#!/usr/bin/env bash
# Wrapper for langfuse-trace.py hook.
# Ensures correct Python environment and never blocks Claude Code.

set -euo pipefail

HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"

# Find project root (look for pyproject.toml upward from plugin)
find_project_root() {
    local dir="$HOOK_DIR"
    while [ "$dir" != "/" ]; do
        [ -f "$dir/pyproject.toml" ] && echo "$dir" && return
        dir="$(dirname "$dir")"
    done
    echo ""
}

PROJECT_ROOT="$(find_project_root)"

# Read stdin once (hook input JSON)
INPUT="$(cat)"

run_hook() {
    if [ -n "$PROJECT_ROOT" ] && command -v uv >/dev/null 2>&1; then
        echo "$INPUT" | uv run --project "$PROJECT_ROOT" python3 "$HOOK_DIR/langfuse-trace.py"
    elif [ -n "$VIRTUAL_ENV" ]; then
        echo "$INPUT" | python3 "$HOOK_DIR/langfuse-trace.py"
    else
        # No venv available — try system python (will fail if langfuse not installed)
        echo "$INPUT" | python3 "$HOOK_DIR/langfuse-trace.py"
    fi
}

# Run in background-ish: never block, never fail
run_hook 2>/dev/null || true
