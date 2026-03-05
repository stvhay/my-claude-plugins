#!/usr/bin/env bash
#
# Smoke test for skill-creator toolchain.
#
# Validates that all scripts run without errors using synthetic fixtures.
# No API calls unless --live is passed.
#
# Usage:
#   ./tests/smoke_test.sh          # offline only (no API calls)
#   ./tests/smoke_test.sh --live   # includes trigger eval via claude -p
#
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMPDIR_BASE="${TMPDIR:-/tmp}"
WORK="$(mktemp -d "${TMPDIR_BASE}/skill-creator-smoke.XXXXXX")"
LIVE=false
FAILURES=0

for arg in "$@"; do
    case "$arg" in
        --live) LIVE=true ;;
    esac
done

cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

pass() { printf "  \033[32mPASS\033[0m  %s\n" "$1"; }
fail() { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; FAILURES=$((FAILURES + 1)); }

echo "skill-creator smoke test"
echo "========================"
echo "skill dir: $SKILL_DIR"
echo "work dir:  $WORK"
echo ""

# ── Set up venv with dependencies ────────────────────────────────────
echo "── setup ──"
VENV="$WORK/.venv"
if command -v uv &> /dev/null; then
    uv venv "$VENV" --quiet
    uv pip install --quiet -p "$VENV/bin/python" -r "$SKILL_DIR/requirements.txt"
    PYTHON="$VENV/bin/python"
    pass "uv venv created with dependencies"
else
    PYTHON=python3
    echo "  SKIP  uv not found, using system python (some tests may skip)"
fi
echo ""

# ── 1. quick_validate.py ─────────────────────────────────────────────
echo "── quick_validate ──"
if ! "$PYTHON" -c "import yaml" 2>/dev/null; then
    echo "  SKIP  pyyaml not installed (pip install pyyaml)"
else
    if "$PYTHON" "$SKILL_DIR/scripts/quick_validate.py" "$SKILL_DIR" > /dev/null 2>&1; then
        pass "SKILL.md validates"
    else
        fail "SKILL.md validation failed ($("$PYTHON" "$SKILL_DIR/scripts/quick_validate.py" "$SKILL_DIR" 2>&1))"
    fi
fi

# ── 2. utils.py parse_skill_md ───────────────────────────────────────
echo "── parse_skill_md ──"
PARSE_OUT=$(cd "$SKILL_DIR" && "$PYTHON" -c "
from scripts.utils import parse_skill_md
from pathlib import Path
name, desc, content = parse_skill_md(Path('.'))
assert name == 'skill-creator', f'bad name: {name}'
assert desc.startswith('Create new skills'), f'bad desc: {desc[:40]}'
print('ok')
" 2>&1) && pass "parse_skill_md returns correct name and description" \
         || fail "parse_skill_md: $PARSE_OUT"

# ── 3. aggregate_benchmark.py (synthetic fixtures) ───────────────────
echo "── aggregate_benchmark ──"

# Create fixture: workspace layout with grading.json files
BENCH="$WORK/benchmark"
for config in with_skill without_skill; do
    for run in run-1 run-2; do
        dir="$BENCH/eval-1/$config/$run"
        mkdir -p "$dir"
        if [ "$config" = "with_skill" ]; then
            pass_rate=0.85
            passed=5
            failed=1
        else
            pass_rate=0.50
            passed=3
            failed=3
        fi
        cat > "$dir/grading.json" <<GRADE
{
  "summary": {
    "pass_rate": $pass_rate,
    "passed": $passed,
    "failed": $failed,
    "total": 6
  },
  "expectations": [
    {"text": "Agent follows TDD", "passed": true, "evidence": "ran test first"}
  ],
  "user_notes_summary": {}
}
GRADE
    done
done

if "$PYTHON" "$SKILL_DIR/scripts/aggregate_benchmark.py" "$BENCH" \
    --skill-name smoke-test -o "$WORK/benchmark.json" > /dev/null 2>&1; then
    # Verify output files exist and contain expected structure
    if "$PYTHON" -c "
import json, sys
b = json.load(open('$WORK/benchmark.json'))
assert 'run_summary' in b, 'missing run_summary'
assert 'with_skill' in b['run_summary'], 'missing with_skill config'
assert 'without_skill' in b['run_summary'], 'missing without_skill config'
assert 'delta' in b['run_summary'], 'missing delta'
print('ok')
" 2>&1; then
        pass "aggregate_benchmark produces valid benchmark.json"
    else
        fail "aggregate_benchmark output malformed"
    fi
    if [ -f "$WORK/benchmark.md" ]; then
        pass "aggregate_benchmark produces benchmark.md"
    else
        fail "benchmark.md not generated"
    fi
else
    fail "aggregate_benchmark.py exited with error"
fi

# ── 4. generate_review.py --static (synthetic workspace) ─────────────
echo "── generate_review ──"

# Create fixture: workspace with outputs/ directory
WS="$WORK/workspace"
RUN1="$WS/eval-1/with_skill/run-1"
mkdir -p "$RUN1/outputs"
echo "# Test output" > "$RUN1/outputs/result.md"
cat > "$RUN1/eval_metadata.json" <<META
{"eval_id": 1, "prompt": "Create a skill that says hello"}
META
cp "$BENCH/eval-1/with_skill/run-1/grading.json" "$RUN1/grading.json"

REVIEW_HTML="$WORK/review.html"
if "$PYTHON" "$SKILL_DIR/eval-viewer/generate_review.py" "$WS" \
    --static "$REVIEW_HTML" --skill-name smoke-test > /dev/null 2>&1; then
    if [ -f "$REVIEW_HTML" ] && [ "$(wc -c < "$REVIEW_HTML")" -gt 100 ]; then
        pass "generate_review produces static HTML"
    else
        fail "review HTML empty or missing"
    fi
else
    fail "generate_review.py exited with error"
fi

# ── 5. generate_report.py (synthetic run_loop output) ─────────────────
echo "── generate_report ──"

# generate_report expects run_loop.py output format (history array)
cat > "$WORK/loop_output.json" <<'LOOP'
{
  "history": [
    {
      "iteration": 0,
      "description": "Test description v0",
      "results": [
        {"query": "create a skill", "should_trigger": true, "triggered": true, "pass": true},
        {"query": "weather today", "should_trigger": false, "triggered": false, "pass": true}
      ],
      "train_accuracy": 1.0,
      "test_accuracy": null
    }
  ],
  "holdout": 0,
  "best_description": "Test description v0"
}
LOOP
REPORT_HTML="$WORK/report.html"
if "$PYTHON" "$SKILL_DIR/scripts/generate_report.py" "$WORK/loop_output.json" \
    -o "$REPORT_HTML" --skill-name smoke-test > /dev/null 2>&1; then
    if [ -f "$REPORT_HTML" ] && [ "$(wc -c < "$REPORT_HTML")" -gt 100 ]; then
        pass "generate_report produces HTML report"
    else
        fail "report HTML empty or missing"
    fi
else
    fail "generate_report.py exited with error"
fi

# ── 6. Live trigger eval (optional, requires claude CLI) ─────────────
if $LIVE; then
    echo "── run_eval (live) ──"
    if ! command -v claude &> /dev/null; then
        fail "claude CLI not found in PATH"
    else
        # Minimal eval set: one should-trigger, one should-not-trigger
        cat > "$WORK/eval_set.json" <<'EVAL'
[
  {"query": "I want to create a new skill from scratch", "should_trigger": true},
  {"query": "What is the weather today?", "should_trigger": false}
]
EVAL
        if cd "$SKILL_DIR" && "$PYTHON" -m scripts.run_eval \
            --eval-set "$WORK/eval_set.json" \
            --skill-path "$SKILL_DIR" \
            --num-workers 2 \
            --timeout 30 \
            --runs-per-query 1 \
            --verbose 2>&1 | tee "$WORK/eval_output.json" | tail -5; then
            pass "run_eval completed"
        else
            fail "run_eval exited with error"
        fi
    fi
else
    echo "── run_eval (skipped, use --live) ──"
fi

# ── Summary ──────────────────────────────────────────────────────────
echo ""
if [ "$FAILURES" -eq 0 ]; then
    printf "\033[32mAll checks passed.\033[0m\n"
else
    printf "\033[31m%d check(s) failed.\033[0m\n" "$FAILURES"
    exit 1
fi
