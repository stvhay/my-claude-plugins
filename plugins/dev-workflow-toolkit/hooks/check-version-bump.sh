#!/usr/bin/env bash
# Hook: Changelog entry enforcement for CI-driven version bumping.
# Silent when compliant. Errors if source files changed without
# ## Unreleased section and <!-- bump: TYPE --> comment in CHANGELOG.md.

set -euo pipefail

PLUGIN_JSON=".claude-plugin/plugin.json"
CHANGELOG="CHANGELOG.md"

if [ ! -f "$PLUGIN_JSON" ]; then
    exit 0
fi

CHANGED=$(git diff --name-only HEAD 2>/dev/null || true)
STAGED=$(git diff --cached --name-only 2>/dev/null || true)
ALL_CHANGED=$(printf '%s\n%s' "$CHANGED" "$STAGED" | sort -u | grep -v '^$' || true)

if [ -z "$ALL_CHANGED" ]; then
    exit 0
fi

# Check if any source files changed (exclude docs, config, version files)
SOURCE_FILES=$(echo "$ALL_CHANGED" | grep -vE '(plugin\.json|pyproject\.toml|package\.json|Cargo\.toml|CHANGELOG\.md|uv\.lock|package-lock\.json|Cargo\.lock|poetry\.lock|\.md$|\.yml$|\.yaml$)' || true)
if [ -z "$SOURCE_FILES" ]; then
    exit 0
fi

# Source files changed — require ## Unreleased with bump comment
if [ ! -f "$CHANGELOG" ]; then
    echo "CHANGELOG_ENTRY_REQUIRED: Source changes detected but no CHANGELOG.md exists."
    echo "Create CHANGELOG.md with an ## Unreleased section and <!-- bump: patch|minor|major --> comment."
    exit 1
fi

if ! grep -q '^## Unreleased' "$CHANGELOG"; then
    echo "CHANGELOG_ENTRY_REQUIRED: Source changes detected but CHANGELOG.md has no ## Unreleased section."
    echo "Add an ## Unreleased section with <!-- bump: patch|minor|major --> comment."
    exit 1
fi

if ! grep -qE '<!--\s*bump:\s*(major|minor|patch)\s*-->' "$CHANGELOG"; then
    echo "BUMP_TYPE_MISSING: ## Unreleased section found but missing <!-- bump: TYPE --> comment."
    echo "Add <!-- bump: patch -->, <!-- bump: minor -->, or <!-- bump: major -->."
    exit 1
fi
