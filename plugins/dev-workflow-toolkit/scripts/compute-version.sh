#!/usr/bin/env bash
# Compute next semver version for this project.
#
# Usage: compute-version.sh <patch|minor|major> [--update] [--project-root <path>]
#
# Without --update: prints next version to stdout.
# With --update: writes version to plugin.json + pyproject.toml.
#   Errors if CHANGELOG.md missing section for target version.
#   Errors if version files are inconsistent.
#
# Dependencies: uv, python >=3.13

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Dependency checks ────────────────────────────────────────────────

if ! command -v uv > /dev/null 2>&1; then
    echo "Error: uv is required but not installed." >&2
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# ── Run ──────────────────────────────────────────────────────────────

exec uv run --project "$PLUGIN_DIR" python "$SCRIPT_DIR/compute_version.py" "$@"
