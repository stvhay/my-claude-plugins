#!/usr/bin/env bash
# Context gate hook — warns when context utilization exceeds skill threshold.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
THRESHOLDS="$SCRIPT_DIR/context-thresholds.json"
STATS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/.statusline-stats"

# Only run if stats file and thresholds exist
[[ -f "$STATS_FILE" ]] || exit 0
[[ -f "$THRESHOLDS" ]] || exit 0

# Read context percentage
context_pct=$(grep -oP 'context_pct=\K[0-9]+' "$STATS_FILE" 2>/dev/null || echo "0")

# Check skill name from environment
skill_name="${CLAUDE_SKILL:-}"
[[ -n "$skill_name" ]] || exit 0

# Look up threshold
threshold=$(python3 -c "
import json, sys
with open('$THRESHOLDS') as f:
    thresholds = json.load(f)
print(thresholds.get('$skill_name', 0))
" 2>/dev/null || echo "0")

[[ "$threshold" -gt 0 ]] || exit 0

if [[ "$context_pct" -gt "$threshold" ]]; then
  echo "Context is at ${context_pct}%. For best results with $skill_name, consider compacting or starting fresh."
fi
