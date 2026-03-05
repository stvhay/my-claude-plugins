#!/usr/bin/env bash
# Test: Validate project-init templates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$PLUGIN_ROOT/skills/project-init/templates"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

failures=0
tests=0

echo "Validating project-init templates..."

# Test 1: Templates directory exists
tests=$((tests + 1))
if [ ! -d "$TEMPLATES_DIR" ]; then
    echo -e "${RED}✗${NC} Templates directory not found at $TEMPLATES_DIR"
    failures=$((failures + 1))
    exit 1
else
    echo -e "${GREEN}✓${NC} Templates directory exists"
fi

# Test 2: Required template files exist
required_templates=(
    "bug-report.yml"
    "feature-request.yml"
    "pull_request_template.md"
    "CONTRIBUTING.md"
)

for template in "${required_templates[@]}"; do
    tests=$((tests + 1))
    if [ ! -f "$TEMPLATES_DIR/$template" ]; then
        echo -e "${RED}✗${NC} Required template missing: $template"
        failures=$((failures + 1))
    else
        echo -e "${GREEN}✓${NC} Template exists: $template"
    fi
done

# Test 3: Validate YAML templates (GitHub issue templates)
for yaml_template in "$TEMPLATES_DIR"/*.yml; do
    if [ -f "$yaml_template" ]; then
        tests=$((tests + 1))
        template_name=$(basename "$yaml_template")

        # Basic YAML structure check (name, description, labels, body)
        if ! grep -q "^name:" "$yaml_template"; then
            echo -e "${RED}✗${NC} $template_name: Missing 'name' field"
            failures=$((failures + 1))
            continue
        fi

        if ! grep -q "^description:" "$yaml_template"; then
            echo -e "${RED}✗${NC} $template_name: Missing 'description' field"
            failures=$((failures + 1))
            continue
        fi

        if ! grep -q "^body:" "$yaml_template"; then
            echo -e "${RED}✗${NC} $template_name: Missing 'body' field"
            failures=$((failures + 1))
            continue
        fi

        echo -e "${GREEN}✓${NC} YAML valid: $template_name"
    fi
done

# Test 4: Validate Markdown templates have content
for md_template in "$TEMPLATES_DIR"/*.md; do
    if [ -f "$md_template" ]; then
        tests=$((tests + 1))
        template_name=$(basename "$md_template")

        # Check file is not empty
        if [ ! -s "$md_template" ]; then
            echo -e "${RED}✗${NC} $template_name: Template is empty"
            failures=$((failures + 1))
            continue
        fi

        # Check for reasonable content (at least 50 characters)
        content_length=$(wc -c < "$md_template")
        if [ "$content_length" -lt 50 ]; then
            echo -e "${RED}✗${NC} $template_name: Template too short (< 50 chars)"
            failures=$((failures + 1))
            continue
        fi

        echo -e "${GREEN}✓${NC} Markdown valid: $template_name"
    fi
done

# Test 5: Path resolution test - verify templates can be referenced from skill
tests=$((tests + 1))
skill_file="$PLUGIN_ROOT/skills/project-init/SKILL.md"
if grep -q "templates/" "$skill_file"; then
    echo -e "${GREEN}✓${NC} Skill correctly references templates/ directory"
else
    echo -e "${RED}✗${NC} Skill doesn't reference templates/ directory"
    failures=$((failures + 1))
fi

echo ""
echo "Tests: $tests, Failures: $failures"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All project-init template validations passed!${NC}"
    exit 0
else
    echo -e "${RED}Some project-init template validations failed.${NC}"
    exit 1
fi
