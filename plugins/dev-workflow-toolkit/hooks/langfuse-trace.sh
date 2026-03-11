#!/usr/bin/env bash
# Wrapper for langfuse-trace.py hook.
# Bootstraps a private venv with langfuse SDK and never blocks Claude Code.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${LANGFUSE_HOOK_VENV:-$HOME/.cache/langfuse-hook/venv}"
PYTHON="$VENV_DIR/bin/python3"

# Skip entirely if venv not bootstrapped yet — don't block Claude Code.
# Run: python3 -m venv ~/.cache/langfuse-hook/venv && ~/.cache/langfuse-hook/venv/bin/pip install langfuse
if [ ! -x "$PYTHON" ]; then
    exit 0
fi

# Read stdin once (hook input JSON)
INPUT="$(cat)"

# Log errors for debugging but never block Claude Code
mkdir -p "$HOME/.cache/langfuse-hook"
LOG="$HOME/.cache/langfuse-hook/errors.log"
echo "$INPUT" | "$PYTHON" "$HOOK_DIR/langfuse-trace.py" 2>>"$LOG" || true
