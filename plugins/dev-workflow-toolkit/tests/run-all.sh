#!/usr/bin/env bash
# Run all tests for dev-workflow-toolkit plugin
#
# Wraps pytest via uv. Pass any pytest flags as arguments.
# Examples:
#   ./tests/run-all.sh              # run all tests
#   ./tests/run-all.sh -v           # verbose
#   ./tests/run-all.sh -k quality   # filter by name

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

exec uv run --project "$PLUGIN_DIR" pytest "$SCRIPT_DIR" "$@"
