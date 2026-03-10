#!/usr/bin/env bash
# Quality gate: thin wrapper that delegates to quality_gate.py via uv.
# Usage: quality-gate.sh [--check <name>] [--path <project-root>]
#
# Requires: uv (https://docs.astral.sh/uv/)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

exec uv run --project "$PLUGIN_DIR" python "$SCRIPT_DIR/quality_gate.py" "$@"
