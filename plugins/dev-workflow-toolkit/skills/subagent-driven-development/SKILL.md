---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session
---

# Subagent-Driven Development

Execute plan by dispatching fresh subagents per task, with two-stage review after each: spec compliance first, then code quality. Independent tasks can run in parallel.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality at scale. Independent tasks parallelize; dependent tasks wait.

## When to Use

Use when: you have a plan with mostly independent tasks and want to stay in this session.
If tasks are tightly coupled: break into smaller units or execute serially.
If separate session preferred: use executing-plans.

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

**Worktree auto-detection:** Run `git rev-parse --show-toplevel` and compare with `git worktree list` to determine if you're in a worktree. If the toplevel path appears as a worktree entry (not the main working tree), confirm you're operating in the correct worktree for the plan's issue. Cross-reference the `.issue` file if present. Re-verify worktree path before each subagent dispatch — subagents inherit the working directory but should confirm it.

**Re-verify CWD before each task dispatch** — agents can lose track of their working directory between tasks.

## Step by step

1. **Read plan.** Extract all tasks with full text. Identify independent vs dependent tasks.
2. **Check task sizing.** Each task should fit ~50% of a subagent's context window. If a task looks too large, break it up before dispatching.
3. **Load subsystem context.** For each task, find the nearest SPEC.md to the task's target files. If one exists, prepend its key sections (Purpose, Invariants, Failure Modes) to the task context when dispatching. For cross-cutting tasks: include the full spec for the primary subsystem and only the Public Interface section from adjacent subsystems. If a task needs >2 specs, it crosses too many boundaries — split it before dispatching.
4. **Dispatch task.** Fresh subagent (via Task tool) with full task text and context. For independent tasks, dispatch in parallel. For dependent tasks, wait.
5. **Handle questions.** If the subagent asks questions, answer clearly before letting them proceed.
5b. **Verify quantitative criteria.** If the task specifies numeric targets (line counts, file counts, performance thresholds, size limits), check the implementer's output against them before review. If a target is missed by >10%, dispatch a focused follow-up subagent with the specific gap and the target before moving on. Skip this step if the task has no quantitative criteria.
6. **Spec review.** Dispatch spec compliance reviewer (./spec-reviewer-prompt.md). **Populate the "Known Expected Breakage" field** with any cross-task dependencies — e.g., "Task 2 will update server.py to use the new session API; breakage at old call sites is expected and handled there." This prevents the reviewer from flagging intentional in-flight breakage as a Task N failure. If issues found, dispatch fix subagent, then re-review.
7. **Quality review.** Dispatch code quality reviewer (./code-quality-reviewer-prompt.md). If issues found, dispatch fix subagent, then re-review.
8. **Document review.** After both reviews pass, post a summary to the GitHub issue:
   ```bash
   gh issue comment <N> --body "$(cat <<'REVIEW_EOF'
   ## Spec Review — Task N
   <details><summary>Verdict: PASS — N findings resolved</summary>

   - Finding 1: description + resolution
   - Finding 2: description + resolution
   </details>
   REVIEW_EOF
   )"
   ```
9. **Next task.** Repeat until all tasks complete.
10. **Verify acceptance criteria.** Check the plan's acceptance criteria. Run the tests.
11. **Final review.** Dispatch code reviewer for the entire implementation — catches cross-task integration issues.
12. **Finish.** Use finishing-a-development-branch.

### Parallel dispatch

Independent tasks can be dispatched simultaneously. The per-task review cycle (steps 6-7) runs after each implementer finishes, so reviews can also run in parallel across tasks.

**Guard:** Never parallelize tasks that write to the same files — this is hidden coupling even if tasks aren't marked as dependent.

**Commit ordering is nondeterministic.** When parallel tasks commit to the same branch, commit order depends on agent completion timing — logical ordering may not match commit ordering (e.g., docs referencing new code may commit before the code itself). This is safe when tasks have no file overlap; reviewers should expect the divergence. For strict logical commit ordering, use sequential dispatch.

> For larger efforts, consider using agent teams (Teammate tool) for self-coordinating execution.

## Prompt Templates

- `./implementer-prompt.md` — Dispatch implementer subagent
- `./spec-reviewer-prompt.md` — Dispatch spec compliance reviewer subagent
- `./code-quality-reviewer-prompt.md` — Dispatch code quality reviewer subagent

## Red Flags

- Never start implementation on main/master branch without explicit user consent
- Never skip reviews (spec compliance OR code quality)
- Never proceed with unfixed issues — reviewer found issues means fix then re-review
- Never make subagent read plan file (provide full text instead)
- Never skip scene-setting context (subagent needs to understand where task fits)
- Never accept "close enough" on spec compliance
- Never start code quality review before spec compliance passes
- Never dispatch dependent tasks before their dependencies complete
- Never parallelize tasks that write to the same files (hidden coupling)
- Never let implementer self-review replace actual review (both are needed)
- If subagent asks questions: answer clearly, provide additional context, don't rush into implementation
- If subagent fails: dispatch fresh fix subagent with specific instructions, don't fix manually (context pollution)

## Integration

**Required workflow skills:**
- **using-git-worktrees** — REQUIRED: Set up isolated workspace before starting execution
- **writing-plans** — Creates the plan this skill executes
- **requesting-code-review** — Code review template for reviewer subagents
- **finishing-a-development-branch** — Complete development after all tasks

**Subagents should use:**
- **test-driven-development** — Subagents follow TDD for each task

**Alternative workflows:**
- **executing-plans** — Batch execution in a separate session with human checkpoints
