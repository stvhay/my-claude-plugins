#!/usr/bin/env bash
# Wrapper for langfuse-trace.py hook.
# Bootstraps a private venv, runs health check synchronously (SessionStart),
# and backgrounds all Langfuse SDK work so hooks never block Claude Code.

set -euo pipefail

CACHE_DIR="$HOME/.cache/langfuse-hook"
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${LANGFUSE_HOOK_VENV:-$CACHE_DIR/venv}"
PYTHON="$VENV_DIR/bin/python3"
LOG="$CACHE_DIR/errors.log"

mkdir -p "$CACHE_DIR"

# Bootstrap venv in background on first run — skip this invocation
if [ ! -x "$PYTHON" ]; then
    (uv venv "$VENV_DIR" && uv pip install --python "$PYTHON" langfuse >>"$CACHE_DIR/bootstrap.log" 2>&1 || echo "Bootstrap failed at $(date)" >>"$CACHE_DIR/bootstrap.log") &
    exit 0
fi

# Read stdin once (hook input JSON)
INPUT="$(cat)"

# SessionStart health check — synchronous so stdout flows to the agent
if echo "$INPUT" | grep -q '"SessionStart"'; then
    SENTINEL="$CACHE_DIR/error-flag"
    if [ -f "$SENTINEL" ]; then
        ERRORS_DIR="$CACHE_DIR/errors"
        COUNT=$(find "$ERRORS_DIR" -type f 2>/dev/null | wc -l)
        LATEST=$(ls -t "$ERRORS_DIR" 2>/dev/null | head -1)
        if [ -n "$LATEST" ]; then
            echo "langfuse-hook: $COUNT error(s). Latest: $(cat "$ERRORS_DIR/$LATEST")"
            echo "Error dir: $ERRORS_DIR"
            echo "Clear with: rm $SENTINEL"
        fi
    fi
    if [ -z "${LANGFUSE_PUBLIC_KEY:-}" ] || [ -z "${LANGFUSE_SECRET_KEY:-}" ] || [ -z "${LANGFUSE_HOST:-}" ]; then
        echo "langfuse-hook: missing env vars. Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST."
    fi
fi

# All Langfuse SDK work runs in background — never blocks Claude Code
# Close inherited stdout/stderr so parent can exit immediately
# Stderr from Python is captured; if non-empty, touch sentinel for next SessionStart
(
    ERRFILE=$(mktemp)
    echo "$INPUT" | "$PYTHON" "$HOOK_DIR/langfuse-trace.py" >/dev/null 2>"$ERRFILE" || true
    if [ -s "$ERRFILE" ]; then
        cat "$ERRFILE" >>"$LOG"
        touch "$CACHE_DIR/error-flag"
    fi
    rm -f "$ERRFILE"
) </dev/null >/dev/null 2>/dev/null &
