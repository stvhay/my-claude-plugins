#!/usr/bin/env bash
# Hook: Changelog enforcement.
# Silent when compliant. Errors if version bumped without changelog section.

set -euo pipefail

PLUGIN_JSON=".claude-plugin/plugin.json"
CHANGELOG="CHANGELOG.md"

if [ ! -f "$PLUGIN_JSON" ]; then
    exit 0
fi

CHANGED=$(git diff --name-only HEAD 2>/dev/null || true)
STAGED=$(git diff --cached --name-only 2>/dev/null || true)
ALL_CHANGED=$(printf '%s\n%s' "$CHANGED" "$STAGED" | sort -u | grep -v '^$' || true)

if ! echo "$ALL_CHANGED" | grep -q 'plugin\.json'; then
    exit 0
fi

if ! VERSION=$(python3 -c "import json; print(json.load(open('$PLUGIN_JSON'))['version'])"); then
    echo "ERROR: Failed to read version from $PLUGIN_JSON. Ensure python3 is available and $PLUGIN_JSON contains a 'version' field." >&2
    exit 1
fi

if [ -z "$VERSION" ]; then
    echo "ERROR: Version field is empty in $PLUGIN_JSON." >&2
    exit 1
fi

if [ ! -f "$CHANGELOG" ]; then
    echo "CHANGELOG_MISSING: Version $VERSION found in $PLUGIN_JSON but no CHANGELOG.md exists." >&2
    echo "Create CHANGELOG.md with a ## v$VERSION section." >&2
    exit 1
fi

if ! grep -qF "## v$VERSION" "$CHANGELOG"; then
    echo "CHANGELOG_MISSING: Version $VERSION found in $PLUGIN_JSON but CHANGELOG.md has no section for ## v$VERSION." >&2
    echo "Write a changelog entry for v$VERSION before proceeding." >&2
    exit 1
fi
