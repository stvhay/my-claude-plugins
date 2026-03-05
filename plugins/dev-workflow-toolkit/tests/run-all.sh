#!/usr/bin/env bash
# Run all tests for dev-workflow-toolkit plugin

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running dev-workflow-toolkit test suite...${NC}"
echo ""

total_failures=0

# Run each test script
for test_script in "$SCRIPT_DIR"/*.sh; do
    # Skip this runner script
    if [ "$(basename "$test_script")" = "run-all.sh" ]; then
        continue
    fi

    if [ -x "$test_script" ]; then
        echo "----------------------------------------"
        if ! "$test_script"; then
            total_failures=$((total_failures + 1))
        fi
        echo ""
    fi
done

echo "========================================"
if [ $total_failures -eq 0 ]; then
    echo -e "${GREEN}✓ All test suites passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $total_failures test suite(s) failed${NC}"
    exit 1
fi
