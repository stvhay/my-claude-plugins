#!/usr/bin/env python3
"""Claude Code hook that ships session traces to Langfuse.

Handles SessionStart, PostToolUse, PostToolUseFailure, SubagentStop,
and SessionEnd events. Reads transcript JSONL for token usage and model data.

Required environment variables (read automatically by SDK):
  LANGFUSE_PUBLIC_KEY
  LANGFUSE_SECRET_KEY
  LANGFUSE_HOST
Custom:
  LANGFUSE_SOURCE_PROJECT  (identifies the source codebase)
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from base64 import b64encode
from urllib.request import Request, urlopen
from urllib.error import URLError

from langfuse import Langfuse


def is_configured():
    """Check if Langfuse environment variables are set."""
    return all(
        os.environ.get(k)
        for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")
    )


def get_source_project():
    return os.environ.get("LANGFUSE_SOURCE_PROJECT", "unknown")


def get_git_branch():
    try:
        return (
            subprocess.check_output(
                ["git", "branch", "--show-current"],
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            .decode()
            .strip()
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


# -- Transcript parsing --


def read_transcript_messages(transcript_path, msg_type="assistant"):
    """Read messages of a given type from a transcript JSONL file."""
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
            if obj.get("type") == msg_type:
                messages.append(obj)
    return messages


def get_tool_results(transcript_path):
    """Index all tool_result blocks by tool_use_id."""
    results = {}
    for msg in read_transcript_messages(transcript_path, "user"):
        content = msg.get("message", {}).get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                results[block.get("tool_use_id")] = block
    return results


def extract_usage(usage):
    """Extract Langfuse usage_details from Anthropic usage dict."""
    input_tokens = usage.get("input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    cache_create = usage.get("cache_creation_input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    return {
        "input": input_tokens + cache_read + cache_create,
        "output": output_tokens,
        "inputCached": cache_read,
    }


def extract_text_output(content_blocks):
    """Extract text content from assistant message content blocks."""
    texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
    return "\n".join(texts) if texts else None


# -- State management (track which requestIds have been shipped) --


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
    get_state_path(session_id).write_text(json.dumps(state))


# -- Trace-level updates via ingestion (SDK pattern) --


def update_trace(trace_id, **kwargs):
    """Update trace attributes via the ingestion API (upsert).

    Uses raw HTTP to avoid SDK internal API instability.
    SDK handles observations; this handles trace-level metadata.
    """
    host = os.environ["LANGFUSE_HOST"].rstrip("/")
    creds = b64encode(
        f"{os.environ['LANGFUSE_PUBLIC_KEY']}:{os.environ['LANGFUSE_SECRET_KEY']}".encode()
    ).decode()

    # Map python snake_case to API camelCase
    body = {"id": trace_id}
    key_map = {"session_id": "sessionId", "user_id": "userId"}
    for k, v in kwargs.items():
        body[key_map.get(k, k)] = v

    payload = json.dumps({"batch": [{
        "id": Langfuse.create_trace_id(),
        "type": "trace-create",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "body": body,
    }]}).encode()

    req = Request(
        f"{host}/api/public/ingestion",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=5):
            pass
    except (URLError, TimeoutError):
        pass  # non-critical, trace data will still arrive via observations


# -- Hook handlers --


def handle_session_start(client, hook_input):
    """Create a Langfuse trace for this session."""
    session_id = hook_input.get("session_id", "")
    model = hook_input.get("model", "unknown")
    source = hook_input.get("source", "startup")
    git_branch = get_git_branch()
    source_project = get_source_project()
    trace_id = Langfuse.create_trace_id(seed=session_id)

    update_trace(
        trace_id,
        name=f"claude-code-{source}",
        session_id=git_branch or "no-branch",
        tags=[source_project, model, git_branch or "no-branch"],
        metadata={
            "source_project": source_project,
            "model": model,
            "git_branch": git_branch,
            "source": source,
            "claude_version": hook_input.get("version", ""),
        },
    )

    state = load_state(session_id)
    state["trace_id"] = trace_id
    save_state(session_id, state)


def ship_transcript_data(client, trace_id, transcript_path, sent_ids,
                         parent_span_id=None):
    """Ship new generations and tool observations from a transcript.

    Returns the updated set of sent request IDs.
    """
    assistant_msgs = read_transcript_messages(transcript_path, "assistant")
    tool_results = get_tool_results(transcript_path)

    trace_ctx = {"trace_id": trace_id}
    if parent_span_id:
        trace_ctx["parent_span_id"] = parent_span_id

    for msg in assistant_msgs:
        request_id = msg.get("requestId")
        if not request_id or request_id in sent_ids:
            continue

        api_msg = msg.get("message", {})
        usage = api_msg.get("usage", {})
        content_blocks = api_msg.get("content", [])

        # Ship generation
        gen = client.start_observation(
            trace_context=trace_ctx,
            name="llm-call",
            as_type="generation",
            model=api_msg.get("model", "unknown"),
            usage_details=extract_usage(usage),
            output=extract_text_output(content_blocks),
            metadata={
                "request_id": request_id,
                "stop_reason": api_msg.get("stop_reason"),
                "service_tier": usage.get("service_tier"),
                "cache_creation_input_tokens": usage.get(
                    "cache_creation_input_tokens", 0
                ),
            },
        )
        gen.end()

        # Ship tool calls
        for block in content_blocks:
            if block.get("type") != "tool_use":
                continue
            tool_id = block.get("id", "")
            result = tool_results.get(tool_id, {})
            is_error = result.get("is_error", False)

            tool_obs = client.start_observation(
                trace_context=trace_ctx,
                name=block.get("name", "unknown"),
                as_type="tool",
                input=block.get("input"),
                output=result.get("content"),
                level="ERROR" if is_error else "DEFAULT",
                metadata={"tool_use_id": tool_id, "is_error": is_error},
            )
            tool_obs.end()

        sent_ids.add(request_id)

    return sent_ids


def handle_post_tool_use(client, hook_input):
    """Ship new generations and tool observations since last hook call."""
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path:
        return

    state = load_state(session_id)
    trace_id = state.get("trace_id") or Langfuse.create_trace_id(seed=session_id)
    sent_ids = set(state.get("sent_request_ids", []))

    # Ensure trace exists if SessionStart didn't fire
    if not state.get("trace_id"):
        git_branch = get_git_branch()
        source_project = get_source_project()
        update_trace(
            client,
            trace_id,
            name="claude-code-session",
            session_id=git_branch or "no-branch",
            tags=[source_project, git_branch or "no-branch"],
            metadata={"source_project": source_project, "git_branch": git_branch},
        )
        state["trace_id"] = trace_id

    sent_ids = ship_transcript_data(client, trace_id, transcript_path, sent_ids)

    state["sent_request_ids"] = list(sent_ids)
    save_state(session_id, state)


def handle_subagent_stop(client, hook_input):
    """Parse a subagent's transcript and ship nested observations."""
    session_id = hook_input.get("session_id", "")
    agent_id = hook_input.get("agent_id", "")
    agent_type = hook_input.get("agent_type", "unknown")
    agent_transcript = hook_input.get("agent_transcript_path", "")
    if not agent_transcript:
        return

    state = load_state(session_id)
    trace_id = state.get("trace_id") or Langfuse.create_trace_id(seed=session_id)
    sent_ids = set(state.get("sent_request_ids", []))

    # Create parent agent span
    agent_span = client.start_observation(
        trace_context={"trace_id": trace_id},
        name=f"subagent-{agent_type}",
        as_type="agent",
        metadata={"agent_id": agent_id, "agent_type": agent_type},
    )

    # Get the OTEL span ID to use as parent for nested observations
    parent_span_id = format(agent_span._span.context.span_id, "016x")

    sent_ids = ship_transcript_data(
        client, trace_id, agent_transcript, sent_ids,
        parent_span_id=parent_span_id,
    )
    agent_span.end()

    state["sent_request_ids"] = list(sent_ids)
    save_state(session_id, state)


def handle_session_end(client, hook_input):
    """Finalize the trace with summary data."""
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    # Ship any remaining data
    if transcript_path:
        handle_post_tool_use(client, hook_input)

    state = load_state(session_id)
    trace_id = state.get("trace_id") or Langfuse.create_trace_id(seed=session_id)

    # Compute totals for trace metadata
    assistant_msgs = []
    if transcript_path:
        assistant_msgs = read_transcript_messages(transcript_path, "assistant")

    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    for msg in assistant_msgs:
        usage = msg.get("message", {}).get("usage", {})
        totals["input"] += usage.get("input_tokens", 0)
        totals["output"] += usage.get("output_tokens", 0)
        totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
        totals["cache_create"] += usage.get("cache_creation_input_tokens", 0)

    update_trace(
        trace_id,
        metadata={
            "total_input_tokens": totals["input"],
            "total_output_tokens": totals["output"],
            "total_cache_read_tokens": totals["cache_read"],
            "total_cache_creation_tokens": totals["cache_create"],
            "total_api_calls": len(assistant_msgs),
            "reason": hook_input.get("reason", "unknown"),
        },
    )

    # Clean up state file
    state_path = get_state_path(session_id)
    if state_path.exists():
        state_path.unlink()


def main():
    hook_input = json.loads(sys.stdin.read())

    if not is_configured():
        sys.exit(0)

    client = Langfuse()
    event = hook_input.get("hook_event_name", "")

    try:
        if event == "SessionStart":
            handle_session_start(client, hook_input)
        elif event in ("PostToolUse", "PostToolUseFailure"):
            handle_post_tool_use(client, hook_input)
        elif event == "SubagentStop":
            handle_subagent_stop(client, hook_input)
        elif event == "SessionEnd":
            handle_session_end(client, hook_input)
    finally:
        client.flush()

    sys.exit(0)


if __name__ == "__main__":
    main()
