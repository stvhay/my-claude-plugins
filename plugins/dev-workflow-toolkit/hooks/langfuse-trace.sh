#!/usr/bin/env bash
# Wrapper for langfuse-trace.py hook.
# Bootstraps a private venv with langfuse SDK and never blocks Claude Code.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${LANGFUSE_HOOK_VENV:-$HOME/.cache/langfuse-hook/venv}"
PYTHON="$VENV_DIR/bin/python3"

mkdir -p "$HOME/.cache/langfuse-hook"

# Bootstrap venv in background on first run — skip this invocation
if [ ! -x "$PYTHON" ]; then
    (uv venv "$VENV_DIR" && uv pip install --python "$PYTHON" langfuse >>"$HOME/.cache/langfuse-hook/bootstrap.log" 2>&1 || echo "Bootstrap failed at $(date)" >>"$HOME/.cache/langfuse-hook/bootstrap.log") &
    exit 0
fi

# Read stdin once (hook input JSON)
INPUT="$(cat)"

# Log errors for debugging but never block Claude Code
LOG="$HOME/.cache/langfuse-hook/errors.log"
echo "$INPUT" | "$PYTHON" "$HOOK_DIR/langfuse-trace.py" 2>>"$LOG" || true
