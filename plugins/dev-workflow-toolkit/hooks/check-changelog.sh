#!/usr/bin/env bash
# Hook: Bump comment enforcement for CI-driven version bumping.
# Silent when compliant. Errors if ## Unreleased exists without
# a <!-- bump: TYPE --> comment.

set -euo pipefail

PLUGIN_JSON=".claude-plugin/plugin.json"
CHANGELOG="CHANGELOG.md"

if [ ! -f "$PLUGIN_JSON" ]; then
    exit 0
fi

if [ ! -f "$CHANGELOG" ]; then
    exit 0
fi

# Only validate if there's an ## Unreleased section
if ! grep -q '^## Unreleased' "$CHANGELOG"; then
    exit 0
fi

# ## Unreleased exists — require bump comment
if ! grep -qE '<!--\s*bump:\s*(major|minor|patch)\s*-->' "$CHANGELOG"; then
    echo "BUMP_TYPE_MISSING: ## Unreleased section found but missing <!-- bump: TYPE --> comment."
    echo "Add <!-- bump: patch -->, <!-- bump: minor -->, or <!-- bump: major -->."
    exit 1
fi
