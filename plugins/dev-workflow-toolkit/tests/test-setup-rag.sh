#!/usr/bin/env bash
# Test: Validate setup-rag skill logic

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_FILE="$PLUGIN_ROOT/skills/setup-rag/SKILL.md"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

failures=0
tests=0

echo "Validating setup-rag skill..."

# Test 1: Skill file exists
tests=$((tests + 1))
if [ ! -f "$SKILL_FILE" ]; then
    echo -e "${RED}✗${NC} Skill file not found at $SKILL_FILE"
    failures=$((failures + 1))
    exit 1
else
    echo -e "${GREEN}✓${NC} Skill file exists"
fi

# Test 2: Skill contains prerequisite check
tests=$((tests + 1))
if grep -q "which uv" "$SKILL_FILE"; then
    echo -e "${GREEN}✓${NC} Contains prerequisite check for uv"
else
    echo -e "${RED}✗${NC} Missing prerequisite check for uv"
    failures=$((failures + 1))
fi

# Test 3: Skill defines MCP server configuration structure
tests=$((tests + 1))
if grep -q "mcpServers" "$SKILL_FILE"; then
    echo -e "${GREEN}✓${NC} Contains MCP server configuration structure"
else
    echo -e "${RED}✗${NC} Missing MCP server configuration structure"
    failures=$((failures + 1))
fi

# Test 4: Skill includes ragling configuration artifacts
required_artifacts=(
    "ragling init"
    "ragling.json"
    ".ragling"
    "mcpServers.ragling"
)

for artifact in "${required_artifacts[@]}"; do
    tests=$((tests + 1))
    if grep -q "$artifact" "$SKILL_FILE"; then
        echo -e "${GREEN}✓${NC} Includes config artifact: $artifact"
    else
        echo -e "${RED}✗${NC} Missing config artifact: $artifact"
        failures=$((failures + 1))
    fi
done

# Test 5: Skill references .mcp.json configuration file
tests=$((tests + 1))
if grep -q ".mcp.json" "$SKILL_FILE"; then
    echo -e "${GREEN}✓${NC} References .mcp.json configuration file"
else
    echo -e "${RED}✗${NC} Missing reference to .mcp.json"
    failures=$((failures + 1))
fi

# Test 6: Skill includes gitignore safety check
tests=$((tests + 1))
if grep -q "gitignore" "$SKILL_FILE"; then
    echo -e "${GREEN}✓${NC} Includes gitignore safety guidance"
else
    echo -e "${RED}✗${NC} Missing gitignore safety guidance"
    failures=$((failures + 1))
fi

# Test 7: Skill mentions project isolation
tests=$((tests + 1))
if grep -q "project" "$SKILL_FILE" && grep -q "isolation\|isolated" "$SKILL_FILE"; then
    echo -e "${GREEN}✓${NC} Mentions project isolation"
else
    echo -e "${RED}✗${NC} Missing project isolation concept"
    failures=$((failures + 1))
fi
echo ""
echo "Tests: $tests, Failures: $failures"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All setup-rag validations passed!${NC}"
    exit 0
else
    echo -e "${RED}Some setup-rag validations failed.${NC}"
    exit 1
fi
