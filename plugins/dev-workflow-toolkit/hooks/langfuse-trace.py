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
import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# Route SDK/OTel warnings to stderr so the shell wrapper can detect failures
logging.basicConfig(level=logging.WARNING, stream=sys.stderr,
                    format="%(levelname)s: %(message)s", force=True)

from langfuse import Langfuse, propagate_attributes


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
    """Extract text content from assistant message content blocks.

    Falls back to tool call summaries when no text blocks exist.
    """
    texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
    if texts:
        return "\n".join(texts)
    # Fallback: summarize tool_use blocks so the generation has visible output
    tools = []
    for b in content_blocks:
        if b.get("type") == "tool_use":
            name = b.get("name", "unknown")
            inp = b.get("input", {})
            desc = inp.get("description", "") if isinstance(inp, dict) else ""
            tools.append(f"[tool_use: {name}] {desc}".strip())
    return "\n".join(tools) if tools else None


# -- State management (track which requestIds have been shipped) --


def get_state_dir():
    """Get a user-private directory for hook state files."""
    state_dir = Path(tempfile.gettempdir()) / f"langfuse-hook-{os.getuid()}"
    if not state_dir.exists():
        state_dir.mkdir(mode=0o700)
    return state_dir


def get_state_path(session_id):
    return get_state_dir() / f"{session_id}.json"


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


# -- Trace context --


def build_tags(*values):
    """Build a tag list, filtering out empty/falsy values."""
    return [v for v in values if v]


def get_trace_context(session_id):
    """Build trace_id and propagate_attributes kwargs for a session."""
    trace_id = Langfuse.create_trace_id(seed=session_id)
    git_branch = get_git_branch()
    source_project = get_source_project()
    return {
        "trace_id": trace_id,
        "git_branch": git_branch,
        "source_project": source_project,
    }


# -- Shipping observations --


def parse_timestamp(ts_str):
    """Parse an ISO 8601 timestamp string to a datetime object."""
    if not ts_str:
        return None
    try:
        # Handle "2026-03-11T12:43:40.155Z" format
        return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def extract_user_input(content):
    """Extract text from a user message's content (string or content blocks).

    Falls back to tool result summaries when no text blocks exist.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        tool_summaries = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    tool_id = block.get("tool_use_id", "")
                    raw = block.get("content", "")
                    preview = str(raw)[:200] if raw else ""
                    tool_summaries.append(
                        f"[tool_result: {tool_id[:16]}] {preview}"
                    )
        if texts:
            return "\n".join(texts)
        if tool_summaries:
            return "\n".join(tool_summaries)
    return None


def read_all_messages(transcript_path):
    """Read all messages from a transcript JSONL file in order."""
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
            if obj.get("type") in ("user", "assistant"):
                messages.append(obj)
    return messages


def ship_transcript_data(client, trace_id, transcript_path, sent_ids,
                         parent_span_id=None):
    """Ship new generations and tool observations from a transcript.

    Returns the updated set of sent request IDs.
    """
    all_msgs = read_all_messages(transcript_path)
    tool_results = get_tool_results(transcript_path)

    trace_ctx = {"trace_id": trace_id}
    if parent_span_id:
        trace_ctx["parent_span_id"] = parent_span_id

    # Track preceding user message for each assistant message
    last_user_input = None
    last_user_ts = None
    for msg in all_msgs:
        if msg.get("type") == "user":
            user_content = msg.get("message", {}).get("content", "")
            last_user_input = extract_user_input(user_content)
            last_user_ts = parse_timestamp(msg.get("timestamp"))
            continue

        # Assistant message
        request_id = msg.get("requestId")
        if not request_id or request_id in sent_ids:
            continue

        api_msg = msg.get("message", {})
        usage = api_msg.get("usage", {})
        content_blocks = api_msg.get("content", [])
        assistant_ts = parse_timestamp(msg.get("timestamp"))

        # Ship generation with user input, assistant output, and timing
        gen_kwargs = {
            "trace_context": trace_ctx,
            "name": "llm-call",
            "as_type": "generation",
            "model": api_msg.get("model", "unknown"),
            "usage_details": extract_usage(usage),
            "input": last_user_input,
            "output": extract_text_output(content_blocks),
            "metadata": {
                "request_id": request_id,
                "stop_reason": api_msg.get("stop_reason"),
                "service_tier": usage.get("service_tier"),
                "cache_creation_input_tokens": usage.get(
                    "cache_creation_input_tokens", 0
                ),
            },
        }
        # SDK v4 start_observation doesn't expose start_time param.
        # Upstream: https://github.com/langfuse/langfuse/issues/9404
        # Workaround: set _start_time on the underlying OTel span so Langfuse
        # computes real latency (endTime - startTime).
        if last_user_ts:
            gen_kwargs["metadata"]["start_time"] = last_user_ts.isoformat()
        if assistant_ts:
            gen_kwargs["metadata"]["end_time"] = assistant_ts.isoformat()

        gen = client.start_observation(**gen_kwargs)
        if last_user_ts:
            start_ns = int(last_user_ts.timestamp() * 1e9)
            gen._otel_span._start_time = start_ns
        end_ns = int(assistant_ts.timestamp() * 1e9) if assistant_ts else None
        gen.end(end_time=end_ns)

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


# -- Hook handlers --


def handle_session_start(client, hook_input):
    """Create a Langfuse trace for this session."""
    session_id = hook_input.get("session_id", "")
    model = hook_input.get("model", "unknown")
    source = hook_input.get("source", "startup")
    ctx = get_trace_context(session_id)

    with propagate_attributes(
        trace_name=f"claude-code-{source}",
        session_id=ctx["git_branch"] or session_id,
        tags=build_tags(ctx["source_project"], model, ctx["git_branch"],
                        hook_input.get("permission_mode", "")),
        metadata={
            "source_project": ctx["source_project"],
            "model": model,
            "git_branch": ctx["git_branch"],
            "source": source,
            "cwd": hook_input.get("cwd", ""),
            "permission_mode": hook_input.get("permission_mode", ""),
            "claude_version": hook_input.get("version", ""),
        },
    ):
        # Create a root span to establish the trace
        obs = client.start_observation(
            trace_context={"trace_id": ctx["trace_id"]},
            name=f"claude-code-{source}",
            as_type="span",
        )
        obs.end()

    state = load_state(session_id)
    state["trace_id"] = ctx["trace_id"]
    save_state(session_id, state)


def handle_post_tool_use(client, hook_input):
    """Ship new generations and tool observations since last hook call."""
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")
    if not transcript_path:
        return

    state = load_state(session_id)
    ctx = get_trace_context(session_id)
    trace_id = state.get("trace_id") or ctx["trace_id"]
    sent_ids = set(state.get("sent_request_ids", []))

    # Ensure trace exists if SessionStart didn't fire
    if not state.get("trace_id"):
        with propagate_attributes(
            trace_name="claude-code-session",
            session_id=ctx["git_branch"] or session_id,
            tags=build_tags(ctx["source_project"], ctx["git_branch"],
                            hook_input.get("permission_mode", "")),
            metadata={
                "source_project": ctx["source_project"],
                "git_branch": ctx["git_branch"],
                "cwd": hook_input.get("cwd", ""),
                "permission_mode": hook_input.get("permission_mode", ""),
            },
        ):
            obs = client.start_observation(
                trace_context={"trace_id": trace_id},
                name="claude-code-session",
                as_type="span",
            )
            obs.end()
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
    last_message = hook_input.get("last_assistant_message", "")
    agent_span = client.start_observation(
        trace_context={"trace_id": trace_id},
        name=f"subagent-{agent_type}",
        as_type="agent",
        output=last_message or None,
        metadata={
            "agent_id": agent_id,
            "agent_type": agent_type,
            "stop_hook_active": hook_input.get("stop_hook_active", False),
        },
    )

    sent_ids = ship_transcript_data(
        client, trace_id, agent_transcript, sent_ids,
        parent_span_id=agent_span.id,
    )
    agent_span.end()

    state["sent_request_ids"] = list(sent_ids)
    save_state(session_id, state)


def handle_session_end(client, hook_input):
    """Finalize the trace with summary data."""
    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    # Ship any remaining data from main transcript
    if transcript_path:
        handle_post_tool_use(client, hook_input)

    # Re-load state once (handle_post_tool_use already saved it)
    state = load_state(session_id)
    trace_id = state.get("trace_id") or Langfuse.create_trace_id(seed=session_id)

    # Compute totals from main transcript only (subagent transcripts are separate)
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_create": 0}
    if transcript_path:
        for msg in read_transcript_messages(transcript_path, "assistant"):
            usage = msg.get("message", {}).get("usage", {})
            totals["input"] += usage.get("input_tokens", 0)
            totals["output"] += usage.get("output_tokens", 0)
            totals["cache_read"] += usage.get("cache_read_input_tokens", 0)
            totals["cache_create"] += usage.get("cache_creation_input_tokens", 0)

    # Use observation-level metadata (supports int values) instead of
    # propagate_attributes metadata (requires string values per SDK validation)
    total_input = totals["input"] + totals["cache_read"] + totals["cache_create"]
    cache_hit_rate = (totals["cache_read"] / total_input) if total_input > 0 else 0.0

    obs = client.start_observation(
        trace_context={"trace_id": trace_id},
        name="session-summary",
        as_type="span",
        metadata={
            "total_input_tokens": totals["input"],
            "total_output_tokens": totals["output"],
            "total_cache_read_tokens": totals["cache_read"],
            "total_cache_creation_tokens": totals["cache_create"],
            "cache_hit_rate": round(cache_hit_rate, 3),
            "total_api_calls": len(state.get("sent_request_ids", [])),
            "reason": hook_input.get("reason", "unknown"),
            "cwd": hook_input.get("cwd", ""),
            "permission_mode": hook_input.get("permission_mode", ""),
        },
    )
    obs.end()

    # Clean up state file
    state_path = get_state_path(session_id)
    if state_path.exists():
        state_path.unlink()


HOOK_TIMEOUT_SECONDS = 8

# -- Error reporting --
#
# Errors are written to individual files under ~/.cache/langfuse-hook/errors/
# and a sentinel file (error-flag) is touched. On SessionStart the health
# check is a single os.path.exists() on the sentinel — near-zero cost on
# the happy path. The agent sees the message only when the sentinel exists.


def get_cache_dir():
    return Path.home() / ".cache" / "langfuse-hook"


def get_errors_dir():
    d = get_cache_dir() / "errors"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_sentinel_path():
    return get_cache_dir() / "error-flag"


MAX_ERROR_FILES = 50


def record_error(event, session_id, error):
    """Write a per-call error file and touch the sentinel.

    Keeps at most MAX_ERROR_FILES error logs, removing oldest when exceeded.
    """
    session_id = session_id or ""
    errors_dir = get_errors_dir()
    ts = f"{time.strftime('%Y%m%d-%H%M%S')}_{time.monotonic_ns()}"
    filename = f"{ts}_{event}_{session_id[:8]}.log"
    (errors_dir / filename).write_text(f"{event}: {error}\n")
    get_sentinel_path().touch()
    # Rotate: keep only the newest MAX_ERROR_FILES
    try:
        files = sorted(errors_dir.iterdir())
        for old in files[:-MAX_ERROR_FILES]:
            old.unlink(missing_ok=True)
    except OSError:
        pass
    # Also log to stderr (captured by shell wrapper)
    print(f"langfuse-hook error: {error}", file=sys.stderr)


def main():
    # Hard timeout — this runs as a background process but still shouldn't hang
    signal.alarm(HOOK_TIMEOUT_SECONDS)

    hook_input = json.loads(sys.stdin.read())
    event = hook_input.get("hook_event_name", "")
    session_id = hook_input.get("session_id", "")

    if not is_configured():
        sys.exit(0)

    client = Langfuse()

    try:
        if event == "SessionStart":
            handle_session_start(client, hook_input)
        elif event in ("PostToolUse", "PostToolUseFailure"):
            handle_post_tool_use(client, hook_input)
        elif event == "SubagentStop":
            handle_subagent_stop(client, hook_input)
        elif event == "SessionEnd":
            handle_session_end(client, hook_input)
    except Exception as e:
        record_error(event, session_id, e)
    finally:
        client.flush()

    sys.exit(0)


if __name__ == "__main__":
    main()
