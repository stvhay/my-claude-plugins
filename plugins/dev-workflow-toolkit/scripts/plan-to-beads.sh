#!/usr/bin/env bash
# plan-to-beads.sh — Wrapper that runs plan_to_beads.py via uv.
#
# Usage: plan-to-beads.sh <plan-file> [--parent <beads-id>] [--dry-run]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

exec uv run --project "$PLUGIN_DIR" python3 "$SCRIPT_DIR/plan_to_beads.py" "$@"
