#!/usr/bin/env bash
# Hook: Version bump enforcement.
# Silent when compliant. Errors if source files changed without version bump.
# Checks git diff (staged + unstaged) against HEAD.

set -euo pipefail

PLUGIN_JSON=".claude-plugin/plugin.json"
if [ ! -f "$PLUGIN_JSON" ]; then
    exit 0
fi

CHANGED=$(git diff --name-only HEAD 2>/dev/null || true)
STAGED=$(git diff --cached --name-only 2>/dev/null || true)
ALL_CHANGED=$(printf '%s\n%s' "$CHANGED" "$STAGED" | sort -u | grep -v '^$' || true)

if [ -z "$ALL_CHANGED" ]; then
    exit 0
fi

VERSION_CHANGED=false
if echo "$ALL_CHANGED" | grep -qE '(plugin\.json|pyproject\.toml|package\.json|Cargo\.toml)'; then
    VERSION_CHANGED=true
fi

SOURCE_CHANGED=false
SOURCE_FILES=$(echo "$ALL_CHANGED" | grep -vE '(plugin\.json|pyproject\.toml|package\.json|Cargo\.toml|CHANGELOG\.md|\.md$|\.yml$|\.yaml$)' || true)
if [ -n "$SOURCE_FILES" ]; then
    SOURCE_CHANGED=true
fi

if [ "$SOURCE_CHANGED" = true ] && [ "$VERSION_CHANGED" = false ]; then
    CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['version'])" 2>/dev/null || echo "unknown")
    echo "VERSION_BUMP_REQUIRED: Source files changed but version in $PLUGIN_JSON is unchanged ($CURRENT_VERSION)."
    echo "Run: compute-version.sh <patch|minor|major> --update"
    exit 1
fi
