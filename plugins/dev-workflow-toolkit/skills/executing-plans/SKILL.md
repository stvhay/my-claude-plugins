---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for review. Verify acceptance criteria at the end.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## Context Gate

Before starting, check context utilization:

```bash
context_pct=$(bash "$(dirname "$CLAUDE_SKILL_DIR")/../scripts/context-check" 2>/dev/null) || true
```

- If the script errors, warn the user: "Context awareness unavailable — `.claude/.statusline-stats` not found."
- If `context_pct` is above **20%**, recommend:
  > Context is at N%. For best results, start fresh: `/clear`

## Worktree Guard

**Before starting, verify you are NOT on main/master:**

```bash
branch=$(git branch --show-current)
if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  echo "ERROR: On $branch — must be in a worktree/feature branch."
  echo "Run /using-git-worktrees first."
  exit 1
fi
echo "Verified: on branch $branch in $(pwd)"
```

**If CWD is invalid** (e.g., worktree was removed): Navigate back to the project root or worktree path before proceeding. Run `git worktree list` to find valid worktree paths.

**Worktree auto-detection:** Run `git rev-parse --show-toplevel` and compare with `git worktree list` to determine if you're in a worktree. If the toplevel path appears as a worktree entry (not the main working tree), confirm you're operating in the correct worktree for the plan's issue. Cross-reference the `.issue` file if present.

**Re-verify CWD at the start of each batch** — agents can lose track of their working directory between batches.

## Work Tracking

**When CLAUDE.md contains a beads work-tracking directive:**
- Use `bd` for all work tracking. Do not use Claude Code task lists (TaskCreate/TaskUpdate).
- Task titles follow the slug convention: `<slug>- <description>`.
- If a `bd` command fails, **stop the workflow** and recommend `bd doctor`. Beads is critical infrastructure.
- Display pipeline status after each batch: `bd list --type=task --json | bd-pipeline --phase executing --next finishing`

**When no beads directive in CLAUDE.md (fallback):**
- Use Claude Code task lists (TaskCreate/TaskUpdate) for in-session progress tracking.
- Plan file is the source of truth.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically — identify questions or concerns
3. Note acceptance criteria from plan header
4. If concerns: Raise them before starting
5. If clear: Run `bd ready --json` to see available beads tasks. If no beads tasks exist, run `bd create -f <plan-file>` to create them. If `bd` is unavailable, proceed without beads tracking.

### Step 2: Execute Batch
**Default: First 3 tasks**

Run `bd ready --json` to find unblocked tasks. For each task in the batch:
1. Claim it: `bd update <id> --claim`
2. Load nearest SPEC.md for the task's target files (if one exists). Review its Invariants before starting — these are constraints you must not violate. If the task crosses subsystems, load the primary spec in full and only the Public Interface section from adjacent specs.
3. Follow each step exactly (plan has bite-sized steps)
4. Run verifications as specified
5. Complete it: `bd close <id> --reason "Implemented"`

After closing completed tasks in a batch, update the parent feature issue:

```bash
# Count progress
total=$(bd list --type=task --json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
closed=$(bd list --type=task --status=closed --json | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")
bd update <feature-id> --append-notes "Batch complete: $closed/$total tasks done"

# GitHub projection: post progress
gh issue comment <N> --body "Progress: $closed/$total tasks complete"
```

**Pipeline status:** After each batch, display pipeline status:

```bash
bd list --type=task --json | bd-pipeline --phase executing --next finishing
```

### Step 3: Report
When batch complete:
- Show what was implemented
- Show verification output
- Say: "Ready for feedback."

### Step 4: Continue
Based on feedback:
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Verify Acceptance Criteria
After all tasks complete:
- Check each acceptance criterion from the plan header
- Run the tests that verify each condition
- Report: which criteria pass, which fail

### Step 6: Complete Development
After acceptance criteria verified:
- **REQUIRED SUB-SKILL:** Use finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## Agent Teams

For larger efforts or autonomous execution, this skill can be run by a **teammate** rather than in a manual session:

1. Controller spawns teammate using Task tool with `team_name`
2. Teammate loads and executes the plan
3. Teammate reports progress via messages
4. Controller reviews and unblocks as needed

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Step 1 (Review) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking after seeing implementation results

**Don't force through blockers** — stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Verify acceptance criteria after all tasks complete
- Between batches: just report and wait
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **using-git-worktrees** - REQUIRED: Set up isolated workspace before starting execution
- **writing-plans** - Creates the plan this skill executes
- **finishing-a-development-branch** - Complete development after all tasks

**Alternative workflows:**
- **subagent-driven-development** - Same-session execution with fresh subagents, parallel dispatch, two-stage review
