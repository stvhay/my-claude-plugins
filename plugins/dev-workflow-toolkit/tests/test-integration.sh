#!/usr/bin/env bash
# Integration tests for dev-workflow-toolkit

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$PLUGIN_ROOT/skills"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

tests_run=0
tests_failed=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
    tests_run=$((tests_run + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    tests_run=$((tests_run + 1))
    tests_failed=$((tests_failed + 1))
}

echo "Running integration tests..."

# Test 1: Skill invocation - verify all skills can be loaded
echo "Validating skill invocation structure..."
for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    skill_file="$skill_dir/SKILL.md"

    # Skip non-skill directories
    if [ "$skill_name" = "SPEC.md" ] || [ "$skill_name" = "UPSTREAM-superpowers.md" ]; then
        continue
    fi

    if [ -f "$skill_file" ]; then
        # Check that skill has both frontmatter markers
        if grep -q "^---$" "$skill_file" && \
           sed -n '/^---$/,/^---$/p' "$skill_file" | grep -q "^name:"; then
            pass "Skill loadable: $skill_name"
        else
            fail "Skill not loadable (missing frontmatter): $skill_name"
        fi
    else
        fail "Missing SKILL.md: $skill_name"
    fi
done

# Test 2: Cross-skill dependency resolution
echo ""
echo "Validating skill dependency resolution..."

# Define expected dependencies from README
declare -A dependencies=(
    ["brainstorming"]="using-git-worktrees|writing-plans|documentation-standards"
    ["writing-plans"]="executing-plans|subagent-driven-development"
    ["executing-plans"]="test-driven-development|systematic-debugging|verification-before-completion|finishing-a-development-branch"
    ["subagent-driven-development"]="test-driven-development|systematic-debugging|verification-before-completion|finishing-a-development-branch"
    ["verification-before-completion"]="code-simplification"
    ["requesting-code-review"]="code-reviewer"
    ["finishing-a-development-branch"]="documentation-standards"
)

for skill in "${!dependencies[@]}"; do
    skill_file="$SKILLS_DIR/$skill/SKILL.md"
    if [ -f "$skill_file" ]; then
        # Check if skill references its expected dependencies
        expected="${dependencies[$skill]}"
        if grep -qE "$expected" "$skill_file"; then
            pass "Dependency resolution: $skill → ${dependencies[$skill]}"
        else
            fail "Missing dependency reference in $skill"
        fi
    fi
done

# Test 3: Template path resolution
echo ""
echo "Validating template path resolution..."

# Test project-init templates
project_init_skill="$SKILLS_DIR/project-init/SKILL.md"
templates_dir="$SKILLS_DIR/project-init/templates"

if [ -f "$project_init_skill" ]; then
    # Verify skill references templates/ directory
    if grep -q "templates/" "$project_init_skill"; then
        pass "Skill references templates/ directory"
    else
        fail "project-init doesn't reference templates/ directory"
    fi

    # Verify all referenced templates exist
    for template in bug-report.yml feature-request.yml pull_request_template.md CONTRIBUTING.md; do
        if [ -f "$templates_dir/$template" ]; then
            pass "Template exists: $template"
        else
            fail "Missing template: $template"
        fi
    done
fi

# Test 4: Template substitution logic
echo ""
echo "Validating template substitution patterns..."

# Check that templates have substitution markers
bug_report="$templates_dir/bug-report.yml"
contributing="$templates_dir/CONTRIBUTING.md"

if [ -f "$bug_report" ]; then
    # YAML templates should be static (no substitution)
    if ! grep -q "{{" "$bug_report"; then
        pass "Bug report template is static (no substitution needed)"
    else
        fail "Bug report template has unexpected substitution markers"
    fi
fi

if [ -f "$contributing" ]; then
    # CONTRIBUTING should be static or have minimal substitution
    # Check it's valid markdown
    if [ -s "$contributing" ]; then
        pass "CONTRIBUTING template is valid"
    else
        fail "CONTRIBUTING template is empty"
    fi
fi

# Test 5: Reference file resolution
echo ""
echo "Validating reference file paths..."

# Skills with references/ directories
skills_with_refs=("code-simplification" "systematic-debugging" "test-driven-development"
                  "requesting-code-review" "subagent-driven-development" "documentation-standards")

for skill in "${skills_with_refs[@]}"; do
    skill_file="$SKILLS_DIR/$skill/SKILL.md"
    refs_dir="$SKILLS_DIR/$skill/references"

    if [ -f "$skill_file" ]; then
        # If skill mentions references, directory should exist
        if grep -q "references/" "$skill_file"; then
            if [ -d "$refs_dir" ]; then
                pass "Reference directory exists: $skill/references"
            else
                fail "Missing reference directory: $skill/references"
            fi
        fi
    fi
done

# Test 6: Skill trigger pattern uniqueness
echo ""
echo "Validating skill trigger patterns for conflicts..."

# Extract all descriptions and check for overly broad patterns
duplicates=0
declare -A seen_triggers

while IFS= read -r line; do
    # Extract key trigger words (lowercase, first 3 significant words)
    trigger=$(echo "$line" | sed 's/description: //' | tr '[:upper:]' '[:lower:]' | awk '{print $1,$2,$3}')

    if [ -n "${seen_triggers[$trigger]:-}" ]; then
        fail "Potential trigger conflict: '$trigger' appears multiple times"
        duplicates=$((duplicates + 1))
    else
        seen_triggers[$trigger]=1
    fi
done < <(grep "^description:" "$SKILLS_DIR"/*/SKILL.md 2>/dev/null || true)

if [ $duplicates -eq 0 ]; then
    pass "No obvious trigger pattern conflicts detected"
fi

# Test 7: MCP configuration generation (setup-rag)
echo ""
echo "Validating MCP configuration patterns..."

setup_rag_skill="$SKILLS_DIR/setup-rag/SKILL.md"

if [ -f "$setup_rag_skill" ]; then
    # Check for ragling configuration artifacts
    required_terms=("ragling init" "mcpServers.ragling" ".ragling" "ragling.json")

    for term in "${required_terms[@]}"; do
        if grep -q "$term" "$setup_rag_skill"; then
            pass "MCP config includes: $term"
        else
            fail "MCP config missing: $term"
        fi
    done

    # Check for .mcp.json reference
    if grep -q ".mcp.json" "$setup_rag_skill"; then
        pass "Skill references .mcp.json configuration"
    else
        fail "Skill missing .mcp.json reference"
    fi
fi

# Summary
echo ""
echo "Tests: $tests_run, Failures: $tests_failed"

if [ $tests_failed -eq 0 ]; then
    echo -e "${GREEN}All integration tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$tests_failed integration test(s) failed${NC}"
    exit 1
fi
