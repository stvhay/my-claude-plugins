#!/usr/bin/env bash
# check-review-documented.sh — Validates review/design documentation exists in GitHub issue
#
# Checks GitHub issue comments for review, design, plan, or verification keywords.
#
# Usage: check-review-documented.sh --issue <N>
#
# Exit codes:
#   0 — Documentation found (or gh unavailable / no issue)
#   1 — No documentation comments found
#
# Silent when compliant. Warns about specific gap if missing.

set -euo pipefail

ISSUE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --issue) ISSUE="$2"; shift 2 ;;
        *) echo "Unknown arg: $1" >&2; exit 1 ;;
    esac
done

# Skip if no issue or gh not available
[[ -n "$ISSUE" ]] || exit 0
command -v gh &>/dev/null || exit 0

COMMENTS=$(gh issue view "$ISSUE" --json comments --jq '.comments[].body' 2>/dev/null || echo "")

if [[ -z "$COMMENTS" ]] || ! echo "$COMMENTS" | grep -qiE "review|design|plan|verification"; then
    echo "Review documentation gaps:"
    echo "  - GitHub: issue #$ISSUE has no review/design/plan/verification comments."
    echo "  - Post artifacts during development via: gh issue comment $ISSUE --body \"## Design Summary ...\""
    exit 1
fi

# Silent on success
exit 0
