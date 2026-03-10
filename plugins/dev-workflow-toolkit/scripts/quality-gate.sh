#!/usr/bin/env bash
# Quality gate: structural validation for dev-workflow-toolkit projects
# Usage: quality-gate.sh [--check <name>] [--path <project-root>]
#
# Checks: inv-numbering, issue-tracking, skill-structure, doc-structure,
#          vsa-coverage, tool-health
#
# Exit 0 = all pass, exit 1 = failures found

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Defaults
CHECK=""
PROJECT_ROOT=""

usage() {
    echo "quality-gate.sh — structural validation for dev-workflow-toolkit projects"
    echo ""
    echo "Usage: quality-gate.sh [--check <name>] [--path <project-root>]"
    echo ""
    echo "Checks:"
    echo "  inv-numbering    INV-N/FAIL-N sequential numbering in SPEC.md"
    echo "  issue-tracking   GitHub and beads issue linkage"
    echo "  skill-structure  SKILL.md frontmatter and naming"
    echo "  doc-structure    Required tracked docs exist"
    echo "  vsa-coverage     Subsystem SPEC.md coverage"
    echo "  tool-health      Required tools installed and working"
    echo ""
    echo "Options:"
    echo "  --check <name>   Run a specific check only"
    echo "  --path <dir>     Project root (default: git rev-parse --show-toplevel)"
    echo "  --help           Show this help"
}

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --check) CHECK="$2"; shift 2 ;;
        --path) PROJECT_ROOT="$2"; shift 2 ;;
        --help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# Auto-detect project root
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

failures=0
checks=0

report() {
    local status="$1" check="$2" detail="$3"
    checks=$((checks + 1))
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} [$check] $detail"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}!${NC} [$check] $detail"
    else
        echo -e "${RED}✗${NC} [$check] $detail"
        failures=$((failures + 1))
    fi
}

# ── Check: inv-numbering ──────────────────────────────────────────────
check_inv_numbering() {
    local spec_files
    spec_files=$(find "$PROJECT_ROOT/plugins" -name "SPEC.md" -path "*/skills/SPEC.md" 2>/dev/null || true)

    if [ -z "$spec_files" ]; then
        report "WARN" "inv-numbering" "No SPEC.md files found"
        return
    fi

    while IFS= read -r spec; do
        local rel_path="${spec#$PROJECT_ROOT/}"
        local inv_ok=true fail_ok=true

        # Check INV-N numbering
        local inv_ids
        inv_ids=$(grep -oP 'INV-\K\d+' "$spec" 2>/dev/null | sort -n | uniq || true)
        if [ -n "$inv_ids" ]; then
            local expected=1
            while IFS= read -r id; do
                if [ "$id" -ne "$expected" ]; then
                    report "FAIL" "inv-numbering" "$rel_path: INV-$id found, expected INV-$expected"
                    inv_ok=false
                    break
                fi
                expected=$((expected + 1))
            done <<< "$inv_ids"
            if $inv_ok; then
                report "PASS" "inv-numbering" "$rel_path: INV-1 through INV-$((expected - 1)) sequential"
            fi
        fi

        # Check FAIL-N numbering
        local fail_ids
        fail_ids=$(grep -oP 'FAIL-\K\d+' "$spec" 2>/dev/null | sort -n | uniq || true)
        if [ -n "$fail_ids" ]; then
            local expected=1
            while IFS= read -r id; do
                if [ "$id" -ne "$expected" ]; then
                    report "FAIL" "inv-numbering" "$rel_path: FAIL-$id found, expected FAIL-$expected"
                    fail_ok=false
                    break
                fi
                expected=$((expected + 1))
            done <<< "$fail_ids"
            if $fail_ok; then
                report "PASS" "inv-numbering" "$rel_path: FAIL-1 through FAIL-$((expected - 1)) sequential"
            fi
        fi
    done <<< "$spec_files"
}

# ── Check: issue-tracking ─────────────────────────────────────────────
check_issue_tracking() {
    local branch
    branch=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "")

    if [ -z "$branch" ] || [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
        report "WARN" "issue-tracking" "On ${branch:-detached HEAD} — issue tracking not applicable"
        return
    fi

    # Check for GitHub issue via PR
    local pr_url
    pr_url=$(gh pr view --json url -q '.url' 2>/dev/null || echo "")
    if [ -n "$pr_url" ]; then
        local pr_body
        pr_body=$(gh pr view --json body -q '.body' 2>/dev/null || echo "")
        if echo "$pr_body" | grep -qiP '(closes|fixes|resolves)\s+#\d+'; then
            report "PASS" "issue-tracking" "PR links to GitHub issue"
        else
            report "WARN" "issue-tracking" "PR exists but no issue linkage found in body"
        fi
    else
        report "WARN" "issue-tracking" "No PR found for branch $branch"
    fi

    # Check beads if available
    if command -v bd > /dev/null 2>&1 && [ -d "$PROJECT_ROOT/.beads" ]; then
        local beads_issues
        beads_issues=$(bd list --status=in_progress --json 2>/dev/null || echo "[]")
        if [ "$beads_issues" != "[]" ] && [ -n "$beads_issues" ]; then
            report "PASS" "issue-tracking" "Beads issues found for in-progress work"
        else
            report "WARN" "issue-tracking" "No in-progress beads issues found"
        fi
    fi
}

# ── Check: skill-structure ────────────────────────────────────────────
check_skill_structure() {
    local skill_dirs
    skill_dirs=$(find "$PROJECT_ROOT/plugins" -name "SKILL.md" -not -path "*/node_modules/*" 2>/dev/null || true)

    if [ -z "$skill_dirs" ]; then
        report "WARN" "skill-structure" "No SKILL.md files found"
        return
    fi

    local names_seen=""
    while IFS= read -r skill_file; do
        local rel_path="${skill_file#$PROJECT_ROOT/}"
        local dir_name
        dir_name=$(basename "$(dirname "$skill_file")")

        # Check YAML frontmatter exists
        if ! head -1 "$skill_file" | grep -q '^---$'; then
            report "FAIL" "skill-structure" "$rel_path: missing YAML frontmatter"
            continue
        fi

        # Extract name from frontmatter
        local skill_name
        skill_name=$(sed -n '/^---$/,/^---$/{ /^name:/{ s/^name:[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//; p; } }' "$skill_file")

        if [ -z "$skill_name" ]; then
            report "FAIL" "skill-structure" "$rel_path: missing 'name' in frontmatter"
            continue
        fi

        # Check name matches directory
        if [ "$skill_name" != "$dir_name" ]; then
            report "FAIL" "skill-structure" "$rel_path: name '$skill_name' doesn't match directory '$dir_name'"
            continue
        fi

        # Check lowercase-hyphenated
        if ! echo "$skill_name" | grep -qP '^[a-z][a-z0-9-]*$'; then
            report "FAIL" "skill-structure" "$rel_path: name '$skill_name' not lowercase-hyphenated"
            continue
        fi

        # Check length
        if [ ${#skill_name} -gt 64 ]; then
            report "FAIL" "skill-structure" "$rel_path: name '$skill_name' exceeds 64 chars"
            continue
        fi

        # Check description exists
        local has_desc
        has_desc=$(sed -n '/^---$/,/^---$/{ /^description:/p }' "$skill_file")
        if [ -z "$has_desc" ]; then
            report "FAIL" "skill-structure" "$rel_path: missing 'description' in frontmatter"
            continue
        fi

        # Check uniqueness
        if echo "$names_seen" | grep -q "^${skill_name}$"; then
            report "FAIL" "skill-structure" "$rel_path: duplicate name '$skill_name'"
            continue
        fi
        names_seen="${names_seen}
${skill_name}"

        report "PASS" "skill-structure" "$rel_path: valid ($skill_name)"
    done <<< "$skill_dirs"
}

# ── Check: doc-structure ──────────────────────────────────────────────
check_doc_structure() {
    # Check project-level tracked docs
    for doc in README.md docs/ARCHITECTURE.md docs/DESIGN.md; do
        if [ -f "$PROJECT_ROOT/$doc" ]; then
            report "PASS" "doc-structure" "$doc exists"
        else
            report "WARN" "doc-structure" "$doc missing (recommended)"
        fi
    done

    # Check each plugin has skills/SPEC.md
    for plugin_dir in "$PROJECT_ROOT"/plugins/*/; do
        if [ ! -d "$plugin_dir" ]; then continue; fi
        local plugin_name
        plugin_name=$(basename "$plugin_dir")
        local spec="$plugin_dir/skills/SPEC.md"
        if [ -f "$spec" ]; then
            report "PASS" "doc-structure" "plugins/$plugin_name/skills/SPEC.md exists"
        else
            report "FAIL" "doc-structure" "plugins/$plugin_name/skills/SPEC.md missing"
        fi
    done
}

# ── Check: vsa-coverage ──────────────────────────────────────────────
check_vsa_coverage() {
    for plugin_dir in "$PROJECT_ROOT"/plugins/*/; do
        if [ ! -d "$plugin_dir" ]; then continue; fi
        local plugin_name
        plugin_name=$(basename "$plugin_dir")
        local skills_dir="$plugin_dir/skills"

        if [ ! -d "$skills_dir" ]; then continue; fi

        if [ ! -f "$skills_dir/SPEC.md" ]; then
            report "FAIL" "vsa-coverage" "plugins/$plugin_name/skills/ has no SPEC.md"
            continue
        fi

        report "PASS" "vsa-coverage" "plugins/$plugin_name: skills/SPEC.md covers subsystem"
    done
}

# ── Check: tool-health ────────────────────────────────────────────────
check_tool_health() {
    # git
    if command -v git > /dev/null 2>&1; then
        local git_ver
        git_ver=$(git --version 2>&1 | head -1)
        report "PASS" "tool-health" "git: $git_ver"
    else
        report "FAIL" "tool-health" "git: not installed"
    fi

    # gh
    if command -v gh > /dev/null 2>&1; then
        local gh_ver
        gh_ver=$(gh --version 2>&1 | head -1)
        if gh auth status > /dev/null 2>&1; then
            report "PASS" "tool-health" "gh: $gh_ver (authenticated)"
        else
            report "WARN" "tool-health" "gh: $gh_ver (not authenticated)"
        fi
    else
        report "WARN" "tool-health" "gh: not installed (optional)"
    fi

    # bd (beads)
    if command -v bd > /dev/null 2>&1; then
        local bd_ver
        bd_ver=$(bd --version 2>&1 | head -1 || echo "unknown")
        report "PASS" "tool-health" "bd: $bd_ver"
    else
        report "WARN" "tool-health" "bd: not installed (optional)"
    fi
}

# ── Run checks ────────────────────────────────────────────────────────
echo "quality-gate: running structural checks against $PROJECT_ROOT"
echo ""

if [ -n "$CHECK" ]; then
    case $CHECK in
        inv-numbering) check_inv_numbering ;;
        issue-tracking) check_issue_tracking ;;
        skill-structure) check_skill_structure ;;
        doc-structure) check_doc_structure ;;
        vsa-coverage) check_vsa_coverage ;;
        tool-health) check_tool_health ;;
        *) echo "Unknown check: $CHECK"; usage; exit 1 ;;
    esac
else
    check_inv_numbering
    check_skill_structure
    check_doc_structure
    check_vsa_coverage
    check_tool_health
    check_issue_tracking
fi

echo ""
if [ $failures -eq 0 ]; then
    echo -e "${GREEN}quality-gate: all $checks checks passed${NC}"
    exit 0
else
    echo -e "${RED}quality-gate: $failures of $checks checks failed${NC}"
    exit 1
fi
