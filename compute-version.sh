#!/usr/bin/env bash
# Thin wrapper for compute_version.py.
# Checks dependencies and delegates to the Python implementation.
#
# Usage:
#   ./compute-version.sh <patch|minor|major> [--update] [--project-root <path>]
#   ./compute-version.sh --ci [--update] [--project-root <path>]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/plugins/dev-workflow-toolkit/scripts/compute_version.py"

# Check dependencies
if ! command -v uv &>/dev/null; then
    echo "ERROR: uv is required but not found. Install from https://docs.astral.sh/uv/" >&2
    exit 1
fi

if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: compute_version.py not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

exec uv run --project "$SCRIPT_DIR/plugins/dev-workflow-toolkit" \
    python "$PYTHON_SCRIPT" "$@"
