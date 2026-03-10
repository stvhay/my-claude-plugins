#!/usr/bin/env bash
# Quality gate: structural validation for dev-workflow-toolkit projects.
#
# Usage: quality-gate.sh [--check <name>] [--path <project-root>]
#
# This script checks dependencies, sets up a Python environment via uv,
# and runs the quality gate checks. Safe to run repeatedly — uv caches
# the virtual environment after first use.
#
# Dependencies: uv, python >=3.13
# Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Dependency checks ────────────────────────────────────────────────

if ! command -v uv > /dev/null 2>&1; then
    echo "Error: uv is required but not installed." >&2
    echo "" >&2
    echo "Install it with:" >&2
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    echo "" >&2
    echo "Or via your package manager (brew install uv, nix, etc.)" >&2
    exit 1
fi

if [ ! -f "$PLUGIN_DIR/pyproject.toml" ]; then
    echo "Error: pyproject.toml not found at $PLUGIN_DIR" >&2
    echo "The quality gate script may not be installed correctly." >&2
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/quality_gate.py" ]; then
    echo "Error: quality_gate.py not found at $SCRIPT_DIR" >&2
    echo "The quality gate script may not be installed correctly." >&2
    exit 1
fi

# ── Run ──────────────────────────────────────────────────────────────

exec uv run --project "$PLUGIN_DIR" python "$SCRIPT_DIR/quality_gate.py" "$@"
