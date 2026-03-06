#!/usr/bin/env bash
# Test: Validate YAML frontmatter in all SKILL.md files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$PLUGIN_ROOT/skills"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

failures=0
tests=0

echo "Validating YAML frontmatter in SKILL.md files..."

# Find all SKILL.md files
while IFS= read -r -d '' skill_file; do
    tests=$((tests + 1))
    skill_name=$(basename "$(dirname "$skill_file")")

    # Check if file starts with frontmatter delimiter
    if ! head -n 1 "$skill_file" | grep -q "^---$"; then
        echo -e "${RED}✗${NC} $skill_name: Missing frontmatter opening delimiter"
        failures=$((failures + 1))
        continue
    fi

    # Extract frontmatter (between first two --- markers)
    frontmatter=$(awk '/^---$/{n++; next} n==1' "$skill_file")

    # Check for required fields
    if ! echo "$frontmatter" | grep -q "^name:"; then
        echo -e "${RED}✗${NC} $skill_name: Missing 'name' field in frontmatter"
        failures=$((failures + 1))
        continue
    fi

    if ! echo "$frontmatter" | grep -q "^description:"; then
        echo -e "${RED}✗${NC} $skill_name: Missing 'description' field in frontmatter"
        failures=$((failures + 1))
        continue
    fi

    # Extract name from frontmatter
    frontmatter_name=$(echo "$frontmatter" | grep "^name:" | sed 's/^name: *//' | tr -d '"' | tr -d "'")

    # Verify name matches directory name
    if [ "$frontmatter_name" != "$skill_name" ]; then
        echo -e "${RED}✗${NC} $skill_name: Name in frontmatter '$frontmatter_name' doesn't match directory name"
        failures=$((failures + 1))
        continue
    fi

    # Verify name format (lowercase, hyphenated, max 64 chars)
    if ! echo "$frontmatter_name" | grep -qE "^[a-z0-9-]{1,64}$"; then
        echo -e "${RED}✗${NC} $skill_name: Name must be lowercase, hyphenated, max 64 chars"
        failures=$((failures + 1))
        continue
    fi

    echo -e "${GREEN}✓${NC} $skill_name"

done < <(find "$SKILLS_DIR" -name "SKILL.md" -type f -print0)

echo ""
echo "Tests: $tests, Failures: $failures"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All frontmatter validations passed!${NC}"
    exit 0
else
    echo -e "${RED}Some frontmatter validations failed.${NC}"
    exit 1
fi
