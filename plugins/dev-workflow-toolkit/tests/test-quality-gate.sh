#!/usr/bin/env bash
# Test: Validate quality-gate checks (positive and negative cases)
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

assert_fail() {
    local desc="$1"
    shift
    tests=$((tests + 1))
    if "$@" > /dev/null 2>&1; then
        echo -e "${RED}✗${NC} $desc (expected failure, got success)"
        failures=$((failures + 1))
    else
        echo -e "${GREEN}✓${NC} $desc"
    fi
}

assert_output_contains() {
    local desc="$1" pattern="$2"
    shift 2
    tests=$((tests + 1))
    local output
    output=$("$@" 2>&1 || true)
    if echo "$output" | grep -qE "$pattern"; then
        echo -e "${GREEN}✓${NC} $desc"
    else
        echo -e "${RED}✗${NC} $desc (pattern '$pattern' not found)"
        failures=$((failures + 1))
    fi
}

# Create temp directory for fixture-based tests
FIXTURES="$(mktemp -d)"
trap 'rm -rf "$FIXTURES"' EXIT

setup_fixture() {
    local name="$1"
    local dir="$FIXTURES/$name"
    rm -rf "$dir"
    mkdir -p "$dir/plugins/test-plugin/skills/test-skill"
    mkdir -p "$dir/docs"

    # Initialize as git repo (quality-gate uses git rev-parse)
    git -C "$dir" init -q

    # Minimal valid structure
    echo "# Test" > "$dir/README.md"
    echo "# Arch" > "$dir/docs/ARCHITECTURE.md"
    echo "# Design" > "$dir/docs/DESIGN.md"

    # Valid SPEC.md with both definitions and cross-references
    cat > "$dir/plugins/test-plugin/skills/SPEC.md" <<'SPEC'
# Test Plugin Spec

## Invariants

| ID | Invariant | Type |
|----|-----------|------|
| INV-1 | First invariant | structural |
| INV-2 | Second invariant | structural |

## Failure Modes

| ID | Mode |
|----|------|
| FAIL-1 | First failure |
| FAIL-2 | Second failure |

## Testing

INV-1 and INV-2 are tested by the test suite.
FAIL-1 is tested via integration tests.
SPEC

    # Valid SKILL.md
    cat > "$dir/plugins/test-plugin/skills/test-skill/SKILL.md" <<'SKILL'
---
name: test-skill
description: "A test skill"
---

# Test Skill

Does things.
SKILL

    echo "$dir"
}

echo "Testing quality-gate..."
echo ""

# ── Smoke tests ──────────────────────────────────────────────────────

echo "--- Smoke tests (against real repo) ---"

# Script exists and is executable
tests=$((tests + 1))
if [ -x "$QG" ]; then
    echo -e "${GREEN}✓${NC} quality-gate.sh exists and is executable"
else
    echo -e "${RED}✗${NC} quality-gate.sh exists and is executable"
    failures=$((failures + 1))
    echo "Tests: $tests, Failures: $failures"
    exit 1
fi

# Individual checks pass against real repo
assert_pass "inv-numbering check runs" "$QG" --check inv-numbering --path "$REPO_ROOT"
assert_pass "skill-structure check runs" "$QG" --check skill-structure --path "$REPO_ROOT"
assert_pass "doc-structure check runs" "$QG" --check doc-structure --path "$REPO_ROOT"
assert_pass "vsa-coverage check runs" "$QG" --check vsa-coverage --path "$REPO_ROOT"
assert_pass "tool-health check runs" "$QG" --check tool-health --path "$REPO_ROOT"

# issue-tracking: verify it runs and check actual result
tests=$((tests + 1))
if "$QG" --check issue-tracking --path "$REPO_ROOT" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} issue-tracking check passes"
else
    # On main branch, warnings are expected but FAIL reports are not
    it_output=$("$QG" --check issue-tracking --path "$REPO_ROOT" 2>&1 || true)
    if echo "$it_output" | grep -q "✗"; then
        echo -e "${RED}✗${NC} issue-tracking check has unexpected failures"
        failures=$((failures + 1))
    else
        echo -e "${GREEN}✓${NC} issue-tracking check runs (warnings only)"
    fi
fi

# All checks together
assert_pass "all checks run together" "$QG" --path "$REPO_ROOT"

# Output contains check names
assert_output_contains "output contains inv-numbering" "inv-numbering" "$QG" --path "$REPO_ROOT"
assert_output_contains "output contains skill-structure" "skill-structure" "$QG" --path "$REPO_ROOT"
assert_output_contains "output contains doc-structure" "doc-structure" "$QG" --path "$REPO_ROOT"

# Help flag
assert_output_contains "--help works" "quality-gate" "$QG" --help

# ── Argument validation ──────────────────────────────────────────────

echo ""
echo "--- Argument validation ---"

assert_fail "--check without value exits non-zero" "$QG" --check
assert_fail "unknown option exits non-zero" "$QG" --bogus
assert_fail "unknown check name exits non-zero" "$QG" --check nonexistent

# ── Fixture: valid project passes ─────────────────────────────────────

echo ""
echo "--- Fixture tests (negative cases) ---"

VALID_DIR=$(setup_fixture "valid")
assert_pass "valid fixture passes all checks" "$QG" --path "$VALID_DIR"

# ── inv-numbering: duplicate INV numbers (table format) ──────────────

DUP_DIR=$(setup_fixture "dup-inv")
cat > "$DUP_DIR/plugins/test-plugin/skills/SPEC.md" <<'SPEC'
# Spec

## Invariants

| ID | Invariant |
|----|-----------|
| INV-1 | First invariant |
| INV-1 | Duplicate of first invariant |
| INV-2 | Second invariant |

## Failure Modes

| ID | Mode |
|----|------|
| FAIL-1 | First failure |
SPEC

assert_fail "duplicate INV numbers detected" "$QG" --check inv-numbering --path "$DUP_DIR"
assert_output_contains "duplicate INV reported" "duplicate" \
    "$QG" --check inv-numbering --path "$DUP_DIR"

# ── inv-numbering: gap in INV numbers ─────────────────────────────────

GAP_DIR=$(setup_fixture "gap-inv")
cat > "$GAP_DIR/plugins/test-plugin/skills/SPEC.md" <<'SPEC'
# Spec

## Invariants

| ID | Invariant |
|----|-----------|
| INV-1 | First |
| INV-3 | Third (skipped 2) |

## Failure Modes

| ID | Mode |
|----|------|
| FAIL-1 | First failure |
SPEC

assert_fail "gap in INV numbers detected" "$QG" --check inv-numbering --path "$GAP_DIR"
assert_output_contains "gap reports expected number" "expected INV-2" \
    "$QG" --check inv-numbering --path "$GAP_DIR"

# ── inv-numbering: duplicate FAIL numbers (table format) ──────────────

DUP_FAIL_DIR=$(setup_fixture "dup-fail")
cat > "$DUP_FAIL_DIR/plugins/test-plugin/skills/SPEC.md" <<'SPEC'
# Spec

## Invariants

| ID | Invariant |
|----|-----------|
| INV-1 | First |

## Failure Modes

| ID | Mode |
|----|------|
| FAIL-1 | First |
| FAIL-1 | Duplicate first |
| FAIL-2 | Second |
SPEC

assert_fail "duplicate FAIL numbers detected" "$QG" --check inv-numbering --path "$DUP_FAIL_DIR"
assert_output_contains "duplicate FAIL reported" "duplicate" \
    "$QG" --check inv-numbering --path "$DUP_FAIL_DIR"

# ── inv-numbering: bold list format works ─────────────────────────────

BOLD_DIR=$(setup_fixture "bold-format")
cat > "$BOLD_DIR/plugins/test-plugin/skills/SPEC.md" <<'SPEC'
# Spec

## Invariants

- **INV-1:** First invariant
- **INV-2:** Second invariant

## Failure Modes

- **FAIL-1:** First failure
SPEC

assert_pass "bold list format accepted" "$QG" --check inv-numbering --path "$BOLD_DIR"

# ── inv-numbering: cross-references don't cause false positives ──────

XREF_DIR=$(setup_fixture "cross-refs")
cat > "$XREF_DIR/plugins/test-plugin/skills/SPEC.md" <<'SPEC'
# Spec

## Invariants

| ID | Invariant |
|----|-----------|
| INV-1 | First |
| INV-2 | Second |

## Failure Modes

| ID | Mode |
|----|------|
| FAIL-1 | First |

## Decision Framework

| Scenario | Action | Relates to |
|----------|--------|------------|
| Adding a skill | Check frontmatter | INV-1 |
| Naming a skill | Use lowercase | INV-2 |

## Testing

INV-1 is tested here. INV-2 is also referenced. INV-1 again.
FAIL-1 is covered by tests. See also INV-1 and INV-2.
SPEC

assert_pass "cross-references don't cause false positives" "$QG" --check inv-numbering --path "$XREF_DIR"

# ── skill-structure: missing frontmatter ──────────────────────────────

NO_FM_DIR=$(setup_fixture "no-frontmatter")
cat > "$NO_FM_DIR/plugins/test-plugin/skills/test-skill/SKILL.md" <<'SKILL'
# Test Skill

No frontmatter here.
SKILL

assert_fail "missing frontmatter detected" "$QG" --check skill-structure --path "$NO_FM_DIR"
assert_output_contains "missing frontmatter reported" "missing YAML frontmatter" \
    "$QG" --check skill-structure --path "$NO_FM_DIR"

# ── skill-structure: missing name field ───────────────────────────────

NO_NAME_DIR=$(setup_fixture "no-name")
cat > "$NO_NAME_DIR/plugins/test-plugin/skills/test-skill/SKILL.md" <<'SKILL'
---
description: "A skill without a name"
---

# Test
SKILL

assert_fail "missing name in frontmatter detected" "$QG" --check skill-structure --path "$NO_NAME_DIR"
assert_output_contains "missing name reported" "missing 'name'" \
    "$QG" --check skill-structure --path "$NO_NAME_DIR"

# ── skill-structure: name doesn't match directory ─────────────────────

MISMATCH_DIR=$(setup_fixture "name-mismatch")
cat > "$MISMATCH_DIR/plugins/test-plugin/skills/test-skill/SKILL.md" <<'SKILL'
---
name: wrong-name
description: "Name doesn't match directory"
---

# Wrong Name
SKILL

assert_fail "name/directory mismatch detected" "$QG" --check skill-structure --path "$MISMATCH_DIR"
assert_output_contains "mismatch reported" "doesn't match directory" \
    "$QG" --check skill-structure --path "$MISMATCH_DIR"

# ── skill-structure: missing description ──────────────────────────────

NO_DESC_DIR=$(setup_fixture "no-description")
cat > "$NO_DESC_DIR/plugins/test-plugin/skills/test-skill/SKILL.md" <<'SKILL'
---
name: test-skill
---

# Test
SKILL

assert_fail "missing description detected" "$QG" --check skill-structure --path "$NO_DESC_DIR"
assert_output_contains "missing description reported" "missing 'description'" \
    "$QG" --check skill-structure --path "$NO_DESC_DIR"

# ── skill-structure: uppercase name ───────────────────────────────────

UPPER_DIR=$(setup_fixture "uppercase-name")
mkdir -p "$UPPER_DIR/plugins/test-plugin/skills/TestSkill"
cat > "$UPPER_DIR/plugins/test-plugin/skills/TestSkill/SKILL.md" <<'SKILL'
---
name: TestSkill
description: "Uppercase name"
---

# Test
SKILL

assert_fail "uppercase skill name detected" "$QG" --check skill-structure --path "$UPPER_DIR"
assert_output_contains "uppercase name reported" "not lowercase-hyphenated" \
    "$QG" --check skill-structure --path "$UPPER_DIR"

# ── doc-structure: missing SPEC.md ────────────────────────────────────

NO_SPEC_DIR=$(setup_fixture "no-spec")
rm "$NO_SPEC_DIR/plugins/test-plugin/skills/SPEC.md"

assert_fail "missing SPEC.md detected" "$QG" --check doc-structure --path "$NO_SPEC_DIR"
assert_output_contains "missing SPEC.md reported" "SPEC.md missing" \
    "$QG" --check doc-structure --path "$NO_SPEC_DIR"

# ── vsa-coverage: missing SPEC.md ────────────────────────────────────

NO_VSA_DIR=$(setup_fixture "no-vsa")
rm "$NO_VSA_DIR/plugins/test-plugin/skills/SPEC.md"

assert_fail "vsa-coverage catches missing SPEC.md" "$QG" --check vsa-coverage --path "$NO_VSA_DIR"
assert_output_contains "vsa missing reported" "no SPEC.md" \
    "$QG" --check vsa-coverage --path "$NO_VSA_DIR"

# ── Results ───────────────────────────────────────────────────────────

echo ""
echo "Tests: $tests, Failures: $failures"

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All quality-gate tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some quality-gate tests failed.${NC}"
    exit 1
fi
