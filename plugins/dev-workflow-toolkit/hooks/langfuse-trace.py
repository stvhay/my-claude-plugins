#!/usr/bin/env python3
"""Claude Code hook that ships session traces to Langfuse.

Handles SessionStart, PostToolUse, and SessionEnd events.
Reads transcript JSONL for token usage and model data.
Uses the Langfuse batch ingestion API (no SDK dependencies).

Required environment variables:
  LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY
  LANGFUSE_HOST
  LANGFUSE_SOURCE_PROJECT  (identifies the source codebase)
"""

import json
import os
import sys
import uuid
from base64 import b64encode
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError


def get_env():
    """Read required Langfuse environment variables. Returns None if not configured."""
    host = os.environ.get("LANGFUSE_HOST")
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if not all([host, public_key, secret_key]):
        return None
    return {
        "host": host.rstrip("/"),
        "public_key": public_key,
        "secret_key": secret_key,
        "source_project": os.environ.get("LANGFUSE_SOURCE_PROJECT", "unknown"),
    }


def ingest(env, events):
    """Send a batch of events to the Langfuse ingestion API."""
    url = f"{env['host']}/api/public/ingestion"
    credentials = b64encode(
        f"{env['public_key']}:{env['secret_key']}".encode()
    ).decode()
    body = json.dumps({"batch": events}).encode()
    req = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Basic {credentials}",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except (URLError, TimeoutError) as e:
        print(f"langfuse-trace: ingestion failed: {e}", file=sys.stderr)
        return None


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def evt_id():
    return str(uuid.uuid4())


def read_transcript_assistant_messages(transcript_path):
    """Read all assistant messages from a transcript JSONL file."""
    messages = []
    path = Path(transcript_path)
    if not path.exists():
        return messages
    with open(path) as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "assistant":
                messages.append(obj)
    return messages


def make_generation_event(trace_id, assistant_msg):
    """Create a Langfuse generation-create event from an assistant message."""
    msg = assistant_msg.get("message", {})
    usage = msg.get("usage", {})
    request_id = assistant_msg.get("requestId", evt_id())
    timestamp = assistant_msg.get("timestamp", now_iso())

    # Build usage map for Langfuse
    # Anthropic reports: input_tokens (non-cached), cache_read_input_tokens,
    # cache_creation_input_tokens. Total input = sum of all three.
    # Langfuse supports "input", "output", "inputCached" as usage types.
    # We send total input (all tokens sent) and cache breakdown separately.
    input_tokens = usage.get("input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    cache_create = usage.get("cache_creation_input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    langfuse_usage = {
        "input": input_tokens + cache_read + cache_create,
        "output": output_tokens,
        "inputCached": cache_read,
    }

    # Extract content for input/output
    content_blocks = msg.get("content", [])
    text_output = []
    for block in content_blocks:
        if block.get("type") == "text":
            text_output.append(block.get("text", ""))
        elif block.get("type") == "thinking":
            pass  # skip thinking blocks for now

    return {
        "id": evt_id(),
        "type": "generation-create",
        "timestamp": timestamp,
        "body": {
            "id": request_id,
            "traceId": trace_id,
            "name": f"llm-call",
            "model": msg.get("model", "unknown"),
            "startTime": timestamp,
            "endTime": timestamp,
            "usage": langfuse_usage,
            "output": "\n".join(text_output) if text_output else None,
            "metadata": {
                "stop_reason": msg.get("stop_reason"),
                "service_tier": usage.get("service_tier"),
                "cache_creation_input_tokens": usage.get(
                    "cache_creation_input_tokens", 0
                ),
            },
        },
    }


def make_tool_events(trace_id, assistant_msg, tool_results):
    """Create Langfuse span-create events for tool calls in an assistant message."""
    events = []
    msg = assistant_msg.get("message", {})
    timestamp = assistant_msg.get("timestamp", now_iso())
    content_blocks = msg.get("content", [])

    for block in content_blocks:
        if block.get("type") != "tool_use":
            continue
        tool_id = block.get("id", "")
        tool_name = block.get("name", "unknown")
        tool_input = block.get("input", {})

        # Find matching tool result
        result_content = None
        is_error = False
        for result in tool_results:
            if result.get("tool_use_id") == tool_id:
                result_content = result.get("content", "")
                is_error = result.get("is_error", False)
                break

        events.append(
            {
                "id": evt_id(),
                "type": "span-create",
                "timestamp": timestamp,
                "body": {
                    "id": tool_id,
                    "traceId": trace_id,
                    "name": tool_name,
                    "startTime": timestamp,
                    "endTime": timestamp,
                    "input": tool_input,
                    "output": result_content,
                    "metadata": {"is_error": is_error},
                    "level": "ERROR" if is_error else "DEFAULT",
                },
            }
        )
    return events


def get_tool_results_from_transcript(transcript_path):
    """Read all tool_result blocks from user messages in the transcript."""
    results = []
    path = Path(transcript_path)
    if not path.exists():
        return results
    with open(path) as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "user":
                continue
            content = obj.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    results.append(block)
    return results


# Track which request IDs we've already sent (via a state file)
def get_state_path(session_id):
    return Path(f"/tmp/langfuse-hook-{session_id}.json")


def load_state(session_id):
    path = get_state_path(session_id)
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"sent_request_ids": [], "trace_id": None}


def save_state(session_id, state):
    path = get_state_path(session_id)
    path.write_text(json.dumps(state))


def handle_session_start(hook_input, env):
    """Create a Langfuse trace for this session."""
    session_id = hook_input.get("session_id", "")
    model = hook_input.get("model", "unknown")
    source = hook_input.get("source", "startup")

    trace_id = session_id  # use session_id as trace_id for simplicity
    git_branch = os.popen("git branch --show-current 2>/dev/null").read().strip()

    events = [
        {
            "id": evt_id(),
            "type": "trace-create",
            "timestamp": now_iso(),
            "body": {
                "id": trace_id,
                "name": f"claude-code-{source}",
                "sessionId": git_branch or "no-branch",
                "tags": [
                    env["source_project"],
                    model,
                    git_branch or "no-branch",
                ],
                "metadata": {
                    "source_project": env["source_project"],
                    "model": model,
                    "git_branch": git_branch,
                    "source": source,
                    "claude_version": hook_input.get("version", ""),
                },
            },
        }
    ]

    result = ingest(env, events)
    if result:
        state = load_state(session_id)
        state["trace_id"] = trace_id
        save_state(session_id, state)


def handle_post_tool_use(hook_input, env):
    """Ship new generations and tool observations since last hook call."""
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    if not transcript_path:
        return

    state = load_state(session_id)
    trace_id = state.get("trace_id") or session_id
    sent_ids = set(state.get("sent_request_ids", []))

    # If trace wasn't created yet (e.g., SessionStart hook didn't fire), create it
    if not state.get("trace_id"):
        git_branch = os.popen("git branch --show-current 2>/dev/null").read().strip()
        trace_event = {
            "id": evt_id(),
            "type": "trace-create",
            "timestamp": now_iso(),
            "body": {
                "id": trace_id,
                "name": "claude-code-session",
                "sessionId": git_branch or "no-branch",
                "tags": [env["source_project"], git_branch or "no-branch"],
                "metadata": {
                    "source_project": env["source_project"],
                    "git_branch": git_branch,
                },
            },
        }
        ingest(env, [trace_event])
        state["trace_id"] = trace_id

    # Read transcript for new assistant messages
    assistant_msgs = read_transcript_assistant_messages(transcript_path)
    tool_results = get_tool_results_from_transcript(transcript_path)
    events = []

    for msg in assistant_msgs:
        request_id = msg.get("requestId")
        if not request_id or request_id in sent_ids:
            continue

        # Generation event (token usage + model)
        events.append(make_generation_event(trace_id, msg))

        # Tool call spans
        events.extend(make_tool_events(trace_id, msg, tool_results))

        sent_ids.add(request_id)

    if events:
        result = ingest(env, events)
        if result:
            state["sent_request_ids"] = list(sent_ids)
            save_state(session_id, state)


def handle_subagent_stop(hook_input, env):
    """Parse a subagent's transcript and ship its generations as nested observations."""
    session_id = hook_input.get("session_id", "")
    agent_id = hook_input.get("agent_id", "")
    agent_type = hook_input.get("agent_type", "unknown")
    agent_transcript = hook_input.get("agent_transcript_path", "")

    if not agent_transcript:
        return

    state = load_state(session_id)
    trace_id = state.get("trace_id") or session_id
    sent_ids = set(state.get("sent_request_ids", []))

    # Create a parent span for this subagent
    agent_span_id = agent_id or evt_id()
    events = [
        {
            "id": evt_id(),
            "type": "span-create",
            "timestamp": now_iso(),
            "body": {
                "id": agent_span_id,
                "traceId": trace_id,
                "name": f"subagent-{agent_type}",
                "startTime": now_iso(),
                "metadata": {
                    "agent_id": agent_id,
                    "agent_type": agent_type,
                },
            },
        }
    ]

    # Parse subagent transcript for its generations
    assistant_msgs = read_transcript_assistant_messages(agent_transcript)
    tool_results = get_tool_results_from_transcript(agent_transcript)

    for msg in assistant_msgs:
        request_id = msg.get("requestId")
        if not request_id or request_id in sent_ids:
            continue

        gen_event = make_generation_event(trace_id, msg)
        # Nest under the subagent span
        gen_event["body"]["parentObservationId"] = agent_span_id
        events.append(gen_event)

        tool_events = make_tool_events(trace_id, msg, tool_results)
        for te in tool_events:
            te["body"]["parentObservationId"] = agent_span_id
        events.extend(tool_events)

        sent_ids.add(request_id)

    if events:
        result = ingest(env, events)
        if result:
            state["sent_request_ids"] = list(sent_ids)
            save_state(session_id, state)


def handle_session_end(hook_input, env):
    """Finalize the trace with summary data."""
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    # Ship any remaining data
    if transcript_path:
        handle_post_tool_use(hook_input, env)

    state = load_state(session_id)
    trace_id = state.get("trace_id") or session_id

    # Update trace with final metadata
    assistant_msgs = []
    if transcript_path:
        assistant_msgs = read_transcript_assistant_messages(transcript_path)

    total_input = sum(
        m.get("message", {}).get("usage", {}).get("input_tokens", 0)
        for m in assistant_msgs
    )
    total_output = sum(
        m.get("message", {}).get("usage", {}).get("output_tokens", 0)
        for m in assistant_msgs
    )
    total_cache_read = sum(
        m.get("message", {}).get("usage", {}).get("cache_read_input_tokens", 0)
        for m in assistant_msgs
    )
    total_cache_create = sum(
        m.get("message", {}).get("usage", {}).get("cache_creation_input_tokens", 0)
        for m in assistant_msgs
    )

    events = [
        {
            "id": evt_id(),
            "type": "trace-create",
            "timestamp": now_iso(),
            "body": {
                "id": trace_id,
                "metadata": {
                    "total_input_tokens": total_input,
                    "total_output_tokens": total_output,
                    "total_cache_read_tokens": total_cache_read,
                    "total_cache_creation_tokens": total_cache_create,
                    "total_api_calls": len(assistant_msgs),
                    "reason": hook_input.get("reason", "unknown"),
                },
            },
        }
    ]
    ingest(env, events)

    # Clean up state file
    state_path = get_state_path(session_id)
    if state_path.exists():
        state_path.unlink()


def main():
    hook_input = json.loads(sys.stdin.read())
    env = get_env()
    if not env:
        sys.exit(0)  # silently skip if not configured

    event = hook_input.get("hook_event_name", "")

    if event == "SessionStart":
        handle_session_start(hook_input, env)
    elif event == "PostToolUse":
        handle_post_tool_use(hook_input, env)
    elif event in ("PostToolUseFailure",):
        handle_post_tool_use(hook_input, env)
    elif event == "SubagentStop":
        handle_subagent_stop(hook_input, env)
    elif event == "SessionEnd":
        handle_session_end(hook_input, env)

    # Always exit 0 — never block Claude Code
    sys.exit(0)


if __name__ == "__main__":
    main()
