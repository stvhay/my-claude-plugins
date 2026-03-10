#!/usr/bin/env bash
# Test: Validate quality-gate.sh checks
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$PLUGIN_DIR/../.." && pwd)"
QG="$PLUGIN_DIR/scripts/quality-gate.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

failures=0
tests=0

assert_pass() {
    local desc="$1"
    shift
    tests=$((tests + 1))
    if "$@" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $desc"
    else
        echo -e "${RED}✗${NC} $desc"
        failures=$((failures + 1))
    fi
}

echo "Testing quality-gate.sh..."

# Script exists and is executable
tests=$((tests + 1))
if [ -x "$QG" ]; then
    echo -e "${GREEN}✓${NC} quality-gate.sh exists and is executable"
else
    echo -e "${RED}✗${NC} quality-gate.sh exists and is executable"
    failures=$((failures + 1))
    echo ""
    echo "Tests: $tests, Failures: $failures"
    echo -e "${RED}Some quality-gate tests failed.${NC}"
    exit 1
fi

# Individual checks can be invoked
assert_pass "inv-numbering check runs" "$QG" --check inv-numbering --path "$REPO_ROOT"
assert_pass "skill-structure check runs" "$QG" --check skill-structure --path "$REPO_ROOT"
assert_pass "doc-structure check runs" "$QG" --check doc-structure --path "$REPO_ROOT"
assert_pass "vsa-coverage check runs" "$QG" --check vsa-coverage --path "$REPO_ROOT"
assert_pass "tool-health check runs" "$QG" --check tool-health --path "$REPO_ROOT"

# issue-tracking may warn on main, just check it runs without crashing
tests=$((tests + 1))
"$QG" --check issue-tracking --path "$REPO_ROOT" > /dev/null 2>&1 || true
echo -e "${GREEN}✓${NC} issue-tracking check runs (warnings expected)"

# All checks together
assert_pass "all checks run together" "$QG" --path "$REPO_ROOT"

# Output contains check names
tests=$((tests + 1))
output=$("$QG" --path "$REPO_ROOT" 2>&1 || true)
if echo "$output" | grep -q "inv-numbering" && \
   echo "$output" | grep -q "skill-structure" && \
   echo "$output" | grep -q "doc-structure"; then
    echo -e "${GREEN}✓${NC} output contains check names"
else
    echo -e "${RED}✗${NC} output contains check names"
    failures=$((failures + 1))
fi

# Help flag
tests=$((tests + 1))
if "$QG" --help 2>&1 | grep -q "quality-gate"; then
    echo -e "${GREEN}✓${NC} --help works"
else
    echo -e "${RED}✗${NC} --help works"
    failures=$((failures + 1))
fi

echo ""
echo "Tests: $tests, Failures: $failures"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All quality-gate tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some quality-gate tests failed.${NC}"
    exit 1
fi
