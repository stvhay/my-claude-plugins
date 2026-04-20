#!/usr/bin/env bash
# Hook: Auto-format the file touched by Edit/Write.
# Silent on success, on no-toolchain-detected, and on missing formatter binary.
# Never blocks — formatter failures surface via the tool's stderr but return 0.

set -uo pipefail

INPUT=$(cat)
FILE_PATH=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0
[ ! -f "$FILE_PATH" ] && exit 0

# Walk up from the file's directory to find the nearest project marker.
DIR=$(cd "$(dirname "$FILE_PATH")" 2>/dev/null && pwd -P) || exit 0
MARKER=""
while [ "$DIR" != "/" ] && [ -n "$DIR" ]; do
    for M in pyproject.toml package.json go.mod Cargo.toml rustfmt.toml; do
        if [ -f "$DIR/$M" ]; then
            MARKER="$M"
            break 2
        fi
    done
    DIR=$(dirname "$DIR")
done

[ -z "$MARKER" ] && exit 0

# Dispatch to formatter based on marker + file extension.
case "$MARKER" in
    pyproject.toml)
        if [[ "$FILE_PATH" == *.py ]]; then
            if command -v ruff >/dev/null 2>&1; then
                ruff format "$FILE_PATH" >/dev/null 2>&1 || true
            elif command -v black >/dev/null 2>&1; then
                black --quiet "$FILE_PATH" 2>/dev/null || true
            fi
        fi
        ;;
    package.json)
        if [[ "$FILE_PATH" =~ \.(js|jsx|ts|tsx|json|css|scss|html|md|yml|yaml)$ ]]; then
            if command -v prettier >/dev/null 2>&1; then
                prettier --write "$FILE_PATH" >/dev/null 2>&1 || true
            fi
        fi
        ;;
    go.mod)
        if [[ "$FILE_PATH" == *.go ]]; then
            if command -v gofmt >/dev/null 2>&1; then
                gofmt -w "$FILE_PATH" 2>/dev/null || true
            fi
        fi
        ;;
    Cargo.toml|rustfmt.toml)
        if [[ "$FILE_PATH" == *.rs ]]; then
            if command -v rustfmt >/dev/null 2>&1; then
                rustfmt "$FILE_PATH" 2>/dev/null || true
            fi
        fi
        ;;
esac

exit 0
