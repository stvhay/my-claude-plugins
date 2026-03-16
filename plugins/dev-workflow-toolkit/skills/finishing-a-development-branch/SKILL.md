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

### Step 1c: CI Status Check

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
2. **Recommend release type** — based on changes, recommend patch (bug fix), minor (new feature, backward compatible), or major (breaking change). Present recommendation in Pre-PR Batch (Step 3c) using `AskUserQuestion`.
3. **Write changelog entry after Pre-PR Batch** — once the user confirms the release type in Step 3c, add an `## Unreleased` section in `CHANGELOG.md` with a `<!-- bump: TYPE -->` comment and migration-relevant details. Include `**ACTION**` markers for any changes users need to apply.
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

If auto-detection is ambiguous, include in Pre-PR Batch (Step 3c). Otherwise proceed with detected base.

### Step 3b: Scope Check

Before creating the PR, review the accumulated changes for scope coherence. This is a **soft gate** — warn if scope drift is detected, but let the user proceed.

**Evaluate:**

```bash
# Review commit history for this branch
git log main..HEAD --oneline

# Review overall change footprint
git diff main...HEAD --stat
```

**Evaluate scope using the criteria below.** If drift detected, include in Pre-PR Batch (Step 3c). If clean, auto-proceed.

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

### Step 3c: Pre-PR Batch

After completing all analysis (documentation validation, changelog analysis, base branch detection, scope review), present all pending decisions in a single `AskUserQuestion` call:

Use `AskUserQuestion` with up to 4 questions:
1. **Release type** — present recommendation with rationale, options: Patch / Minor / Major (only if CHANGELOG.md exists)
2. **Scope** — present analysis, options: "Looks clean (Recommended)" / "Split into multiple PRs" (only if scope drift detected, otherwise auto-proceed)
3. **Base branch** — options: "main (Recommended)" / Other (only if auto-detection is ambiguous, otherwise auto-proceed)
4. **Retrospective** — "Run a retrospective after PR?" options: "Yes (Recommended)" / "No"

Skip questions where the answer is unambiguous (clean scope, clear base branch). The agent should fill as many slots as possible with questions that genuinely need user input.

### Step 4: Create Pull Request

**Always create a PR and attach it to the relevant GitHub issue.** Do not ask the user to choose — PRs are the default workflow.

### Step 5: Squash Merge via PR

```bash
# Push branch
git push -u origin <feature-branch>

# Check CONTRIBUTING.md for PR target repo
grep -i "\-R \|pr.*target\|target.*repo" CONTRIBUTING.md 2>/dev/null

# Check for design doc and plan to include in PR body
# Convention: *-design.md (from brainstorming), *-plan.md (from writing-plans)
PLANS_DIR=$(jq -r '.plansDirectory // ".claude/plans"' .claude/settings.json 2>/dev/null || echo ".claude/plans")
ls $PLANS_DIR/*-design.md $PLANS_DIR/*-plan.md 2>/dev/null
```

If a design doc or plan exists, include it in a collapsible block:

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>

<details><summary>Implementation Plan</summary>

<paste plan file contents here, if one exists>

</details>

Closes #<N>
EOF
)"
```

The `Closes #<N>` line links to the GitHub issue so it closes when the PR merges.

### Step 5b: Post-PR CI Verification

<HARD-GATE>
Do NOT proceed to cleanup or merge until CI checks pass on the newly created PR.
</HARD-GATE>

This closes the gap from Step 1c when no PR existed at that point.

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

### Step 6: Cleanup Worktree

Check if in worktree:
```bash
git worktree list | grep $(git branch --show-current)
```

If yes:
```bash
git worktree remove <worktree-path>
```

### Step 7: Retrospective

**After all other steps complete,** invoke the retrospective skill.

The retrospective opt-in is collected in the Pre-PR Batch (Step 3c). If the user opted in, invoke retrospective — skip its entry gate question (already answered). If they declined, skip entirely.

## Quick Reference

**Workflow:**
1. Verify tests → Quality gate → CI check
2. Validate docs → Changelog → Base branch → Scope check
3. **Pre-PR Batch** (release type + scope + base + retrospective opt-in)
4. Push → Squash merge PR → Post-PR CI verify → Cleanup → Retrospective

## Common Mistakes and Red Flags

- **Skipping test verification** — merge broken code. Always verify tests before offering options.
- **Skipping changelog entry** — changes ship without changelog, CI can't determine version bump. Step 2b prompts for release type.
- **Automatic worktree cleanup** — removing worktree when might need it. Only cleanup after PR creation.
- **Never** proceed with failing tests, merge without verifying, delete work without confirmation, or force-push without explicit request.
- **Always** verify tests before creating PR, write changelog entry with bump type if CHANGELOG.md exists, and clean up worktree after PR creation.

## Integration

**Invokes:**
- **documentation-standards** — Validate mode, hard gate after test verification
- **retrospective** — Step 7, non-blocking session analysis after PR creation

**Workflow:** Verify → CI check → Validate → Changelog → Base → Scope → Pre-PR Batch → Push + squash merge PR → Post-PR CI verify → Cleanup → Retrospective

**Called by:**
- **subagent-driven-development** (Step 7) - After all tasks complete
- **executing-plans** (Step 5) - After all batches complete

**Pairs with:**
- **using-git-worktrees** - Cleans up worktree created by that skill
