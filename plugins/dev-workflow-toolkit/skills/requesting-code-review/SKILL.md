---
name: requesting-code-review
description: Canonical review flow for this repo — review a PR by number and post findings to GitHub. Use when completing tasks, implementing major features, before merging to verify work meets requirements, or to review a specific PR. Prefer over the built-in /review command, which does not post to GitHub.
---

# Requesting Code Review

Dispatch code-reviewer subagent to catch issues before they cascade, **and always post the review to GitHub** when a PR exists.

**Core principle:** Review early, review often — and always post findings to the PR surface so the record is visible to collaborators (INV-15 GitHub Projection).

> **This skill vs. built-in `/review`:** The Claude Code built-in `/review <PR#>` command produces an in-chat review but does NOT post to GitHub. When a PR review needs to be recorded on GitHub, use this skill (or explicitly call `gh pr review`/`gh pr comment` after `/review`). The two skills have overlapping purposes but only this one closes the loop on GitHub.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

### Worktree Auto-Detection

Before running review, locate the correct worktree:

1. Run `git rev-parse --show-toplevel` to get the current repo root
2. Run `git worktree list` — if the current toplevel appears as a worktree entry (not the main working tree), you're already in a worktree — proceed
3. If a PR number was provided as argument:
   a. Run `gh pr view <N> --json body,headRefName` to get the PR body and branch name
   b. Extract the issue number from the PR body — match `(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#(\d+)` (case-insensitive). GitHub accepts all these variants.
   c. Run `git worktree list` and match worktree paths using the regex `/<issue>-` where `<issue>` is bounded by `/` before and `-` after (e.g., `/63-` for issue #63 — must not substring-match `/630-` or `/6-`)
   d. If a matching worktree is found, operate on that worktree's directory
   e. If no issue link found in PR body, fall back to matching by branch name (existing behavior)
   f. If no worktree found by either method, warn: "No local worktree found for PR #N (issue #M). Reviewing from current directory."
4. If no PR number and not in a worktree, proceed from current directory

**1. Detect context:**

Determine if a PR exists for the current branch and whether you are the author:

```bash
# Get PR number and author in a single API call.
# NOTE: If this fails, check gh auth status before assuming no PR exists.
# See "Error handling" below — silent fallback masks auth/network failures.
PR_JSON=$(gh pr view --json number,author 2>/dev/null) || PR_JSON=""

if [ -n "$PR_JSON" ]; then
  PR_NUMBER=$(echo "$PR_JSON" | jq -r '.number')
  PR_AUTHOR=$(echo "$PR_JSON" | jq -r '.author.login')
  CURRENT_USER=$(gh api user --jq '.login')
  IS_AUTHOR=$( [ "$PR_AUTHOR" = "$CURRENT_USER" ] && echo "true" || echo "false" )
else
  PR_NUMBER=""
  IS_AUTHOR=""
fi
```

If no PR exists, the review runs locally only (existing behavior).

**Error handling:** If `gh pr view` fails for reasons other than "no PR" (auth failure, network error, rate limit), the agent must surface the error rather than silently falling back to local-only review. Check `gh auth status` and retry before assuming no PR exists. A silent fallback means the agent skips posting to the PR — the user won't know the review happened.

**2. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**3. Dispatch code-reviewer subagent:**

Use Task tool with code-reviewer type, fill template at `code-reviewer.md`

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_REFERENCE}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary
- `{PR_NUMBER}` - PR number (empty for local-only review)
- `{IS_AUTHOR}` - `true` if current user authored the PR, `false` otherwise

**4. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Review Documentation (Post-PR)

When a PR exists (`PR_NUMBER` is set), the code-reviewer subagent posts findings as PR comments:

- **Line-level comments** where applicable: `gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/pulls/{PR_NUMBER}/comments` with `path`, `line`, and `body`
- **General findings** as top-level PR comment: `gh pr comment {PR_NUMBER} --body "<findings>"`
- **Summary:** Post a structured review summary:
  ```bash
  gh pr comment $PR_NUMBER --body "$(cat <<'REVIEW_EOF'
  ## Code Review Summary
  **Verdict:** PASS/NEEDS_WORK
  - Critical: N | Important: N | Minor: N

  <details><summary>Findings</summary>

  1. [severity] description — file:line
  2. [severity] description — file:line
  </details>
  REVIEW_EOF
  )"
  ```

When no PR exists, findings are reported locally only (existing behavior unchanged).

## Example: Local Review (no PR)

```
[Just completed Task 2: Add PR-aware review flow]

You: Let me request code review before proceeding.

PR_NUMBER=""  # No PR exists yet
BASE_SHA=447c459
HEAD_SHA=9a0d42a

[Dispatch code-reviewer subagent]:
  WHAT_WAS_IMPLEMENTED: PR-aware review flow with authorship detection
  PLAN_REFERENCE: Task 2 from ~/.claude/plans/optimize-pr-review.md
  BASE_SHA: 447c459
  HEAD_SHA: 9a0d42a
  DESCRIPTION: Added context detection, PR commenting, and authorship-based action branching
  PR_NUMBER: ""
  IS_AUTHOR: ""

[Subagent returns]:
  Strengths: Clean decision matrix, backwards-compatible design
  Issues:
    Important: Redundant API calls in detection script
    Minor: Examples lack concrete placeholder values
  Assessment: Ready to proceed with fixes

You: [Fix redundant API calls, continue to Task 3]
```

## Example: PR Review (self-authored)

```
[PR #5 is open, you are the author]

PR_NUMBER=5, IS_AUTHOR=true

[Dispatch code-reviewer subagent]
[Subagent posts structured comment on PR #5]
[Clean review: comment signals LGTM — no --approve attempted]
[Issues found: comment lists them — no --request-changes attempted]
```

## Example: PR Review (external)

```
[PR #12 from a contributor, you are not the author]

PR_NUMBER=12, IS_AUTHOR=false

[Dispatch code-reviewer subagent]
[Subagent posts structured comment on PR #12]
[Clean review: gh pr review 12 --approve]
[Issues found: gh pr review 12 --request-changes]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

## Work Tracking

GitHub PR comments serve as the review record.

See template at: requesting-code-review/code-reviewer.md
