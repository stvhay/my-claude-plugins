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
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

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
    """Extract text content from assistant message content blocks."""
    texts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
    return "\n".join(texts) if texts else None


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
        tags=build_tags(ctx["source_project"], model, ctx["git_branch"]),
        metadata={
            "source_project": ctx["source_project"],
            "model": model,
            "git_branch": ctx["git_branch"],
            "source": source,
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
            tags=build_tags(ctx["source_project"], ctx["git_branch"]),
            metadata={
                "source_project": ctx["source_project"],
                "git_branch": ctx["git_branch"],
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
    agent_span = client.start_observation(
        trace_context={"trace_id": trace_id},
        name=f"subagent-{agent_type}",
        as_type="agent",
        metadata={"agent_id": agent_id, "agent_type": agent_type},
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
    obs = client.start_observation(
        trace_context={"trace_id": trace_id},
        name="session-summary",
        as_type="span",
        metadata={
            "total_input_tokens": totals["input"],
            "total_output_tokens": totals["output"],
            "total_cache_read_tokens": totals["cache_read"],
            "total_cache_creation_tokens": totals["cache_create"],
            "total_api_calls": len(state.get("sent_request_ids", [])),
            "reason": hook_input.get("reason", "unknown"),
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


def record_error(event, session_id, error):
    """Write a per-call error file and touch the sentinel."""
    import time
    errors_dir = get_errors_dir()
    ts = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{ts}_{event}_{session_id[:8]}.log"
    (errors_dir / filename).write_text(f"{event}: {error}\n")
    get_sentinel_path().touch()
    # Also log to stderr (captured by shell wrapper)
    print(f"langfuse-hook error: {error}", file=sys.stderr)


def check_health():
    """Fast health check for SessionStart. Returns a message or None.

    Checks: sentinel exists → env vars set → venv ready.
    """
    cache_dir = get_cache_dir()

    # Fast path: no sentinel, no problems reported
    sentinel = get_sentinel_path()
    has_errors = sentinel.exists()

    # Check env vars (cheap — just dict lookups)
    missing = [
        k for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST")
        if not os.environ.get(k)
    ]
    if missing:
        return (
            f"langfuse-hook: missing env vars: {', '.join(missing)}. "
            "Set these in your shell profile or .env to enable tracing."
        )

    # Check venv
    venv_dir = os.environ.get("LANGFUSE_HOOK_VENV",
                              str(cache_dir / "venv"))
    python = Path(venv_dir) / "bin" / "python3"
    if not python.exists():
        return (
            "langfuse-hook: venv not ready. "
            "It will auto-bootstrap on next hook invocation."
        )

    # Check error sentinel
    if has_errors:
        errors_dir = cache_dir / "errors"
        try:
            error_files = sorted(errors_dir.iterdir())
            count = len(error_files)
            latest = error_files[-1].read_text().strip() if error_files else ""
            return (
                f"langfuse-hook: {count} error(s) logged. "
                f"Latest: {latest}\n"
                f"Error dir: {errors_dir}\n"
                f"Clear with: rm {sentinel}"
            )
        except OSError:
            return f"langfuse-hook: errors detected. Check {cache_dir / 'errors'}/"

    return None


def main():
    # Hard timeout to avoid being killed by Claude Code's hook timeout
    signal.alarm(HOOK_TIMEOUT_SECONDS)

    hook_input = json.loads(sys.stdin.read())
    event = hook_input.get("hook_event_name", "")
    session_id = hook_input.get("session_id", "")

    # On SessionStart, run fast health check (output goes to agent context)
    if event == "SessionStart":
        msg = check_health()
        if msg:
            print(msg)
        if not is_configured():
            sys.exit(0)
    elif not is_configured():
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
