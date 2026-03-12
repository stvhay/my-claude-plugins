#!/usr/bin/env bash
# check-review-documented.sh — Validates review documentation exists
#
# Checks:
# 1. Beads task has review status (via bd)
# 2. GitHub issue has at least one review comment
#
# Usage: check-review-documented.sh [--issue <N>] [--beads-id <ID>]
#
# Exit codes:
#   0 — Both checks pass (or tools unavailable)
#   1 — Review documentation missing
#
# Silent when compliant. Warns about specific gap if either is missing.

set -euo pipefail

ISSUE=""
BEADS_ID=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --issue) ISSUE="$2"; shift 2 ;;
        --beads-id) BEADS_ID="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

WARNINGS=()

# --- Beads check ---
if command -v bd &>/dev/null; then
    if [[ -n "$BEADS_ID" ]]; then
        REVIEW_STATUS=$(bd show "$BEADS_ID" --json 2>/dev/null | jq -r '.notes // ""' 2>/dev/null || echo "")
        if [[ -z "$REVIEW_STATUS" ]] || ! echo "$REVIEW_STATUS" | grep -qi "review"; then
            WARNINGS+=("Beads: task $BEADS_ID has no review status in notes. Update with: bd update $BEADS_ID --notes \"Review: PASS/FAIL, N findings\"")
        fi
    else
        # Try to find beads task from current branch context
        BEADS_TASKS=$(bd list --status=closed --json 2>/dev/null || echo "")
        if [[ -n "$BEADS_TASKS" ]] && [[ "$BEADS_TASKS" != "[]" ]]; then
            HAS_REVIEW=$(echo "$BEADS_TASKS" | jq -r '.[].notes // ""' 2>/dev/null | grep -ci "review" || echo "0")
            if [[ "$HAS_REVIEW" -eq 0 ]]; then
                WARNINGS+=("Beads: no tasks have review status in notes.")
            fi
        fi
    fi
fi

# --- GitHub issue check ---
if command -v gh &>/dev/null; then
    if [[ -n "$ISSUE" ]]; then
        COMMENTS=$(gh issue view "$ISSUE" --json comments --jq '.comments[].body' 2>/dev/null || echo "")
        if [[ -z "$COMMENTS" ]] || ! echo "$COMMENTS" | grep -qi "review\|spec review\|code review"; then
            WARNINGS+=("GitHub: issue #$ISSUE has no review comments. Post a review summary with: gh issue comment $ISSUE --body \"## Spec Review ...\"")
        fi
    fi
fi

# --- Report ---
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo "Review documentation gaps:"
    for w in "${WARNINGS[@]}"; do
        echo "  - $w"
    done
    exit 1
fi

# Silent on success
exit 0
