#!/usr/bin/env bash
# Wrapper for langfuse-trace.py hook.
# Ensures correct Python environment and never blocks Claude Code.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HOOK_DIR/../../.." && pwd)"
PYTHON="$REPO_ROOT/.venv/bin/python3"

# Read stdin once (hook input JSON)
INPUT="$(cat)"

# Log errors for debugging but never block Claude Code
LOG="/tmp/langfuse-hook-$(id -u)-errors.log"
echo "$INPUT" | "$PYTHON" "$HOOK_DIR/langfuse-trace.py" 2>>"$LOG" || true
