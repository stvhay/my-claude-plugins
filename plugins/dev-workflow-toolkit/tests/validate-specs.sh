#!/usr/bin/env bash
# Test: Validate SPEC.md files across all plugins
# Checks: existence and line count within 80-350 range

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

MIN_LINES=80
MAX_LINES=350

failures=0
tests=0

echo "Validating SPEC.md files across all plugins..."

for plugin_dir in "$REPO_ROOT"/plugins/*/; do
    plugin_name=$(basename "$plugin_dir")
    spec_file="$plugin_dir/skills/SPEC.md"

    # Check existence
    tests=$((tests + 1))
    if [ ! -f "$spec_file" ]; then
        echo -e "${RED}✗${NC} $plugin_name: Missing skills/SPEC.md"
        failures=$((failures + 1))
        continue
    fi
    echo -e "${GREEN}✓${NC} $plugin_name: SPEC.md exists"

    # Check line count
    tests=$((tests + 1))
    line_count=$(wc -l < "$spec_file")
    if [ "$line_count" -lt "$MIN_LINES" ]; then
        echo -e "${RED}✗${NC} $plugin_name: SPEC.md too short ($line_count lines, min $MIN_LINES)"
        failures=$((failures + 1))
    elif [ "$line_count" -gt "$MAX_LINES" ]; then
        echo -e "${RED}✗${NC} $plugin_name: SPEC.md too long ($line_count lines, max $MAX_LINES)"
        failures=$((failures + 1))
    else
        echo -e "${GREEN}✓${NC} $plugin_name: SPEC.md within range ($line_count lines)"
    fi
done

echo ""
echo "Tests: $tests, Failures: $failures"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All SPEC.md validations passed!${NC}"
    exit 0
else
    echo -e "${RED}Some SPEC.md validations failed.${NC}"
    exit 1
fi
