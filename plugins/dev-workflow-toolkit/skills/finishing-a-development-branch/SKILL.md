---
name: finishing-a-development-branch
description: Use when implementation is complete, all tests pass, and you need to integrate the work - guides completion via version bump, squash merge PR, and cleanup
---

# Finishing a Development Branch

## Overview

Guide completion of development work through a fixed workflow: verify, validate, bump version, squash merge PR, clean up.

**Core principle:** Verify tests → CI check → Validate docs → Version bump → Push + squash merge PR → Clean up.

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
  --issue "$(gh pr view --json body --jq '.body' 2>/dev/null | grep -oE '(Closes|Fixes|Resolves) #[0-9]+' | grep -oE '[0-9]+' | head -1 || echo '')" \
  --beads-id "$(bd list --type=feature --json 2>/dev/null | jq -r '.[0].id // ""' || echo '')"
```

This is a **soft gate** — warnings are included in the PR body but do not block:

- If warnings found: include them in PR body under `**Review documentation gaps:**`
- If no warnings: proceed silently
- If script not found or fails to run: proceed with a note

> **Why soft gate:** Small changes (typo fixes, doc updates) may not have formal review documentation. The warning surfaces the gap for the PR reviewer to evaluate.

### Step 1d: CI Status Check

<HARD-GATE>
Do NOT proceed to documentation validation, PR creation, or merge until CI checks pass.
</HARD-GATE>

Check if a PR already exists for the current branch:

```bash
PR_NUM=$(gh pr view --json number --jq .number 2>/dev/null || echo "")
```

**If no PR exists:** Skip this step with a note: "No PR yet — CI status will be verified after PR creation." Continue to Step 2.

**If PR exists:** Verify all CI checks pass:

```bash
gh pr checks "$PR_NUM" --fail-on-error
```

**If checks pass:** Continue to Step 2.

**If checks fail:**
```
CI checks failing on PR #<N>:

[Show failing checks]

Cannot proceed until CI passes. Fix the failing checks and re-run.
```

Stop. Don't proceed to Step 2.

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

### Step 2b: Changelog and Bump Label

If the project has a `CHANGELOG.md` (created by project-init):

1. **Analyze changes** — review the diff against the base branch
2. **Recommend release type** — based on changes, recommend patch (bug fix), minor (new feature, backward compatible), or major (breaking change). Always present the recommendation with rationale:
   > "This adds a new scaffolding step to project-init — new capability, backward compatible. I'd recommend **minor**. Patch, minor, or major?"
3. **Write changelog entry** — add an `## Unreleased` section in `CHANGELOG.md` with a `<!-- bump: TYPE -->` comment and migration-relevant details. Include `**ACTION**` markers for any changes users need to apply.
4. **Commit changelog** — separate commit for the changelog entry
5. **Note PR label** — remind to apply `bump:TYPE` label when creating PR (or apply via `gh pr create --label bump:TYPE`)

If `CHANGELOG.md` does not exist:
> "No changelog found. Consider running project-init to set up release infrastructure."

This is a **soft warning** — proceed without changelog if the project hasn't adopted the convention.

### Step 3: Determine Base Branch

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Or ask: "This branch split from main - is that correct?"

### Step 3b: Scope Check

Before creating the PR, review the accumulated changes for scope coherence. This is a **soft gate** — warn if scope drift is detected, but let the user proceed.

**Evaluate:**

```bash
# Review commit history for this branch
git log main..HEAD --oneline

# Review overall change footprint
git diff main...HEAD --stat
```

**Ask:**

> Did implementation reveal scope that justifies splitting this into multiple PRs?

**Signs of scope drift:**
- Commits that address unrelated issues or features
- Changes to unrelated subsystems with no connection to the original issue
- Bug fixes for pre-existing issues bundled into a feature branch
- Refactoring that could stand alone as its own PR

**If scope drift detected:**
```
This branch appears to include changes beyond issue #<N>:

- [specific changes that appear unrelated]

Consider splitting these into separate issues/PRs before merging.
Proceed anyway, or split?
```

**If user proceeds:** Continue to Step 4 with a note in the PR body: `**Scope note:** [brief description of bundled changes and why they were kept together]`

**If clean:** Proceed to Step 4.

### Step 3c: Beads Preflight

If beads is configured:

```bash
bd preflight --check
```

If preflight fails, surface the failures and stop. Do not proceed to PR creation with failing preflight.

Post preflight results as a PR comment after PR creation:

```bash
gh pr comment <PR#> --body "## Preflight Results
$(bd preflight --check 2>&1)"
```

### Step 4: Create Pull Request

**Always create a PR and attach it to the relevant GitHub issue.** Do not ask the user to choose — PRs are the default workflow.

### Step 5: Squash Merge via PR

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

### Step 5b: Post-PR CI Verification

<HARD-GATE>
Do NOT proceed to cleanup or merge until CI checks pass on the newly created PR.
</HARD-GATE>

This closes the gap from Step 1d when no PR existed at that point.

```bash
# Wait for CI to start and complete
gh pr checks "$PR_NUM" --watch

# Verify all checks passed
gh pr checks "$PR_NUM" --fail-on-error
```

**If checks pass:** Continue to Step 6.

**If checks fail:**
```
CI checks failing on PR #<N>:

[Show failing checks]

Cannot proceed until CI passes. Fix the failing checks and re-run.
```

Stop. Don't proceed to Step 6.

Then: Cleanup worktree (Step 6)

### Step 6: Cleanup Worktree

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

### Step 7: Beads Sync

**After PR creation**, if a `.beads/` directory exists:

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

## Quick Reference

**Workflow:** Verify tests → Quality gate → Review docs check → CI check → Validate docs → Changelog + label → Determine base → Scope check → Push + squash merge PR → Post-PR CI verify → Cleanup → Beads sync → Retrospective

## Work Tracking

Follow the work-tracking protocol in SPEC.md (INV-14).

**Fallback note:** Use GitHub PR body and comments for tracking completion steps.

## Common Mistakes

**Skipping test verification**
- **Problem:** Merge broken code, create failing PR
- **Fix:** Always verify tests before offering options

**Skipping changelog entry**
- **Problem:** Changes ship without changelog, CI can't determine version bump type
- **Fix:** Step 2b prompts for release type and writes ## Unreleased entry with bump comment

**Automatic worktree cleanup**
- **Problem:** Remove worktree when might need it
- **Fix:** Only cleanup after PR creation

## Red Flags

**Never:**
- Proceed with failing tests
- Merge without verifying tests on result
- Delete work without confirmation
- Force-push without explicit request

**Always:**
- Verify tests before creating PR
- Write changelog entry with bump type if CHANGELOG.md exists before creating PR
- Clean up worktree after PR creation

## Integration

**Invokes:**
- **documentation-standards** — Validate mode, hard gate after test verification
- **retrospective** — Step 8, non-blocking session analysis after PR creation

**Workflow:** Verify → CI check → Validate → Changelog + label → Determine base → Scope check → Push + squash merge PR → Post-PR CI verify → Cleanup → Beads sync → Retrospective

**Called by:**
- **subagent-driven-development** (Step 7) - After all tasks complete
- **executing-plans** (Step 5) - After all batches complete

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
