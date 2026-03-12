---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work by presenting clear options and handling chosen workflow.

**Core principle:** Verify tests → Validate docs → Present options → Execute choice → Clean up.

**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

## The Process

### Step 1: Verify Tests

**Before presenting options, check CONTRIBUTING.md for the project's quality gate:**

```bash
# Check for project-specific quality gate
grep -A5 -i "quality gate\|quality check\|ci check" CONTRIBUTING.md 2>/dev/null
```

If CONTRIBUTING.md specifies a quality gate command, run that. Otherwise fall back to auto-detection:

```bash
# Fallback: run project's test suite
npm test / cargo test / pytest / go test ./...
```

**If tests fail:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Stop. Don't proceed to Step 2.

**If tests pass:** Continue to Step 1b.

### Step 1b: Quality Gate

Run the structural quality gate after tests pass:

```bash
${CLAUDE_SKILL_DIR}/../../scripts/quality-gate.sh --path "$(git rev-parse --show-toplevel)"
```

Quality gate failures in `inv-numbering`, `skill-structure`, and `doc-structure`
must be resolved before proceeding. `tool-health` and `issue-tracking` warnings
can proceed with a note in the PR body.

### Step 1c: Review Documentation Check

Run the check-review-documented validation:

```bash
${CLAUDE_SKILL_DIR}/../../scripts/check-review-documented.sh \
  --issue "$(gh pr view --json body --jq '.body' 2>/dev/null | grep -oP '(?<=Closes #)\d+' || echo '')" \
  --beads-id "$(bd list --type=feature --json 2>/dev/null | jq -r '.[0].id // ""' || echo '')"
```

This is a **soft gate** — warnings are included in the PR body but do not block:

- If warnings found: include them in PR body under `**Review documentation gaps:**`
- If no warnings: proceed silently
- If script not found or fails to run: proceed with a note

> **Why soft gate:** Small changes (typo fixes, doc updates) may not have formal review documentation. The warning surfaces the gap for the PR reviewer to evaluate.

### Step 2: Validate Documentation

<HARD-GATE>
Do NOT proceed to option presentation, PR creation, or merge until documentation validation passes or the developer explicitly defers with a recorded reason.
</HARD-GATE>

Invoke documentation-standards in validate mode. The skill will:

1. Detect the scope of changes on this branch
2. Classify whether documentation updates are needed
3. Read tracked docs and relevant SPEC.md files
4. Compare against the branch's changes
5. If gaps found — present them and block until resolved
6. If no gaps — announce "Documentation gate: passed" and proceed

**If the developer defers documentation:**
- Require a reason
- Record it for the PR body: `**Documentation deferred:** [reason]`
- Proceed to Step 3 (Determine Base Branch)

**If documentation gate passes:** Continue to Step 3.

### Step 3: Determine Base Branch

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Or ask: "This branch split from main - is that correct?"

### Step 4: Create Pull Request

**Always create a PR and attach it to the relevant GitHub issue.** Do not ask the user to choose — PRs are the default workflow.

Skip directly to Option 2 (Push and Create PR) below.

### Step 5: Execute Choice

#### Option 1: Merge Locally (only if user explicitly requests)

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest
git pull

# Merge feature branch
git merge <feature-branch>

# Verify tests on merged result
<test command>

# If tests pass
git branch -d <feature-branch>
```

Then: Cleanup worktree (Step 6)

#### Option 2: Push and Create PR

```bash
# Push branch
git push -u origin <feature-branch>

# Check CONTRIBUTING.md for PR target repo
grep -i "\-R \|pr.*target\|target.*repo" CONTRIBUTING.md 2>/dev/null
# If a -R flag is specified (e.g., -R org/repo), use it with gh pr create

# Gather beads context for PR body
bd list --status=closed --json   # Closed tasks for summary
bd list --status=open --json     # Remaining open tasks
bd list --type=feature --json    # Find feature issue with external-ref

# Check for design doc and plan to include in PR body
# Convention: *-design.md (from brainstorming), *-plan.md (from writing-plans)
ls docs/plans/*-design.md docs/plans/*-plan.md 2>/dev/null
```

Build the PR body with beads context. If a design doc or plan exists, include it in a collapsible block:

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Beads
**Epic:** <epic-id>
**Completed:** <list of closed beads task IDs and titles>
**Remaining:** <list of open beads task IDs, or "None">

## Test Plan
- [ ] <verification steps>

<details><summary>Implementation Plan</summary>

<paste plan file contents here, if one exists>

</details>

Closes #<N>
EOF
)"
```

The `Closes #<N>` line comes from the beads feature issue's `external-ref` field. Strip the `gh-` prefix to get the issue number (e.g., `gh-21` → `Closes #21`). This ensures the GitHub issue is closed when the PR merges.

After PR creation, close the beads feature issue:
```bash
bd close <feature-id> --reason "PR #<N> created"
```

> **If the PR is rejected or needs rework:** Reopen the beads feature with `bd reopen <feature-id>` and continue working.

Then: Cleanup worktree (Step 6)

#### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

**Don't cleanup worktree.**

#### Option 4: Discard

**Confirm first:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for exact confirmation.

If confirmed:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Then: Cleanup worktree (Step 6)

### Step 6: Cleanup Worktree

**For Options 1, 2, 4:**

Check if in worktree:
```bash
git worktree list | grep $(git branch --show-current)
```

If yes:
```bash
# Use bd worktree remove if .beads/ exists (handles redirect cleanup)
if [ -d .beads ]; then
  bd worktree remove <worktree-name>
else
  git worktree remove <worktree-path>
fi
```

**For Option 3:** Keep worktree.

### Step 7: Beads Sync

**After executing any option**, if a `.beads/` directory exists:

```bash
# Find the beads feature/epic linked to this branch's GitHub issue
bd list --status=in_progress --json  # Review unclosed work

# Only close beads that belong to THIS branch:
# 1. The feature/epic whose external-ref matches the branch's GH issue (e.g., gh-<N>)
# 2. Tasks that are children of that feature/epic
# Do NOT close unrelated in-progress beads — they may belong to other branches.
# If unsure which beads belong to this branch, ask the user before closing.
bd close <id> --reason "Branch completed"

# Push beads data to remote (if configured)
bd dolt push 2>/dev/null || echo "Beads remote not configured — data persisted locally."
```

Only close beads scoped to the current branch's work. If no Dolt remote is configured, beads data is still persisted in the local database.

### Step 8: Retrospective

**After all other steps complete,** invoke the retrospective skill.

This step is non-blocking — if the user declines, skip it. The retrospective
analyzes the session, categorizes findings as project-local or upstream skill
improvements, and files GitHub issues for upstream items once the user approves.

> **Note:** Step 1 (Verify Tests) and Step 2 (Validate Documentation) run before options are presented. The table below covers Steps 5-7.

## Quick Reference

| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | ✓ | - | - | ✓ |
| 2. Create PR | - | ✓ | ✓ | - |
| 3. Keep as-is | - | - | ✓ | - |
| 4. Discard | - | - | - | ✓ (force) |

## Common Mistakes

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Open-ended questions**
- **Problem:** "What should I do next?" → ambiguous
- **Fix:** Present exactly 4 structured options

**Automatic worktree cleanup**
- **Problem:** Remove worktree when might need it (Option 2, 3)
- **Fix:** Only cleanup for Options 1 and 4

**No confirmation for discard**
- **Problem:** Accidentally delete work
- **Fix:** Require typed "discard" confirmation

## Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Verify tests before offering options
- Present exactly 4 options
- Get typed confirmation for Option 4
- Clean up worktree for Options 1 & 4 only

## Integration

**Invokes:**
- **documentation-standards** — Validate mode, hard gate after test verification
- **retrospective** — Step 8, non-blocking session analysis after PR creation

**Called by:**
- **subagent-driven-development** (Step 7) - After all tasks complete
- **executing-plans** (Step 5) - After all batches complete

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
