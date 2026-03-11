#!/usr/bin/env bash
# Wrapper for langfuse-trace.py hook.
# Bootstraps a private venv with langfuse SDK and never blocks Claude Code.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${LANGFUSE_HOOK_VENV:-$HOME/.cache/langfuse-hook/venv}"
PYTHON="$VENV_DIR/bin/python3"

# Bootstrap venv on first run
if [ ! -x "$PYTHON" ]; then
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --quiet langfuse >/dev/null 2>&1
fi

# Read stdin once (hook input JSON)
INPUT="$(cat)"

# Log errors for debugging but never block Claude Code
LOG="$HOME/.cache/langfuse-hook/errors.log"
echo "$INPUT" | "$PYTHON" "$HOOK_DIR/langfuse-trace.py" 2>>"$LOG" || true
