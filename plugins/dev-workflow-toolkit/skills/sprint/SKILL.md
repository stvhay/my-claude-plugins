---
name: sprint
description: "Autonomous development session orchestrator"
disable-model-invocation: true
---

# Sprint

Autonomous development session. Follows the CONTRIBUTING.md workflow with pre-authorized decisions — agent pauses only for substantive technical uncertainty, never for process approvals.

**Announce at start:** "Starting sprint. Reading turnover and checking project state."

## Invocation

`/sprint` accepts an optional risk tolerance argument (default: standard):

```
/sprint              — run 1 sprint at Standard (budget 25)
/sprint supervised   — budget 8, unfamiliar codebase
/sprint cautious     — budget 15, production code
/sprint standard     — budget 25, well-tested codebase (default)
/sprint trusted      — budget 40, high coverage, proven track record
/sprint autonomous   — budget 60, prototypes, low blast radius
```

Parse $ARGUMENTS. If it matches a tolerance level name, use that budget. If absent, default to standard (25).

Each `/sprint` invocation is one session. For multiple sprints, invoke `/sprint` again — each invocation gets fresh context. The turnover doc bridges sessions.

## Risk Budget

Sprint tracks cumulative risk using the `total-risk` tool (`${CLAUDE_PLUGIN_ROOT}/scripts/total-risk`). The tool externalizes risk accounting so the agent classifies tasks but doesn't do the math.

### Session lifecycle

```bash
# Phase 1: initialize
total-risk reset <budget>

# Phase 2: before each issue, preview cost
total-risk check <category> [conditions...]
# → {"advice": "ok|caution|skip", "reason": "...", "adjusted_cost": N}

# Phase 2: after completing each issue, log it
total-risk <category> [conditions...]
# → {"status": "ok|warning|checkpoint", "remaining": N, ...}

# Post the result as a comment on the issue
gh issue comment <N> --body "<formatted risk ledger line>"
```

### Task categories

| Category | Cost | Examples |
|----------|------|---------|
| docs | 1 | README, comments, changelog |
| style | 1 | Formatting, linting fixes |
| tests | 2 | New or extended tests |
| new-feature | 3 | Greenfield with clear spec |
| mechanical-refactor | 3 | Renames, extract-method, move-file |
| ci-infra | 4 | CI config, build scripts |
| structural-refactor | 5 | Changing abstractions, reorganizing modules |
| modify-feature | 5 | Changing existing behavior |
| bug-fix | 7 | Fault localization + correction |
| performance | 7 | Optimization with regression risk |
| security | 8 | Auth, crypto, input validation, secrets |

### Conditions (pass to total-risk)

- `4-plus-files` — task touches 4+ files (×1.5)
- `module:<path>` — module path for same-module auto-detection (×1.3 if repeated)
- `ci-pass` / `ci-fail` — CI result after task (−1 / +3)
- `review-clean` — fresh-context review found no issues (−1)

Context degradation (×1.05 per prior task) is applied automatically by the tool.

### Acting on the budget

- **`advice: ok`** — proceed with the task
- **`advice: caution`** — proceed but this is near the limit; prefer cheaper tasks if available
- **`advice: skip`** — do not start this task; pick a cheaper one or checkpoint
- **`status: checkpoint`** — budget exhausted; proceed to Phase 3 (Wrap Up)
- **`status: warning`** — approaching budget; finish current task, then consider wrapping up

When a task is too expensive for remaining budget, **pick a cheaper task from the plan** rather than stopping immediately. Only checkpoint when no affordable tasks remain or the tool returns `blocked`.

## Session Boundary Model

The seam between sessions is the PR. A session ends with all work filed as PRs, tree clean. The next session begins with independent review of those PRs — fresh context, full rigor. The agent never reviews its own work in the same context that wrote it.

## Phase 1: Orient

### 1a. Read Turnover

Check for turnover docs in `.claude/turnover/`. If the directory exists, read the most recent file (by filename date sort) — this is context from a previous sprint, including the current tier/priority plan.

If no turnover exists, evaluate the issue board and create a plan:

```bash
gh issue list --state open --json number,title,labels --limit 30
```

Organize by priority (labels, milestones). Write the plan into the turnover doc for this session.

If turnover exists but the plan looks stale (referenced issues are closed, priorities shifted), update it from the board.

### 1b. Review and Merge Open PRs

```bash
gh pr list --state open --json number,title,headRefName
```

For each open PR, dispatch **3 parallel review agents** with fresh context for model diversity:

1. **Dispatch reviews** — use `dispatching-parallel-agents` to launch 3 agents (opus, sonnet, haiku), each running `requesting-code-review` on the PR branch. Each agent gets clean context (critical for chained sprints where orchestrator context accumulates).

2. **Synthesize findings:**
   - **Unanimous** (all 3 models flag the same issue) — high confidence, auto-fix
   - **Single-model finding** (only 1 model flags) — fix, but note which model caught it in the commit message
   - **Contradictions** (models disagree on approach) — pause and surface to user

3. Apply fixes, invoke `code-simplification` on the branch
4. Push fixes, merge PR if clean
5. Handle version bumping per CONTRIBUTING.md

After processing all PRs, return to main:
```bash
git checkout main
git pull origin main
```

### 1c. Sync and Verify

Read CONTRIBUTING.md for project-specific build, test, and quality gate commands. Cross-check against the project structure (look for `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`, etc.) to confirm your understanding is correct. If CONTRIBUTING.md and the project structure disagree, pause and surface the discrepancy to the user.

Run the identified commands. If tests fail after merges, diagnose and fix before proceeding.

### 1d. Clean Up

Delete local branches that have been merged:
```bash
git branch --merged main | grep -v '^\*\|main\|master' | xargs -r git branch -d
```

Ensure working tree is clean.

## Phase 2: Work

Follow the CONTRIBUTING.md workflow for each issue. The sprint pre-authorizes decisions so the agent moves through without pausing.

### Issue Selection

Pick from the lowest incomplete tier in the turnover plan. Before starting, preview the risk cost:

```bash
total-risk check <category> [conditions...]
```

If advice is `skip`, pick a cheaper task. Sort available tasks by risk cost descending — do the hardest affordable tasks first while context is freshest.

Announce the choice:
> "Working on #N: <title> (risk: <category>, estimated cost: <N>) — <one-line rationale>"

### Workflow Per Issue

1. **Worktree**: Create via `using-git-worktrees` with branch `<type>/<issue>-<slug>`
2. **Brainstorm**: Invoke `brainstorming` with issue context (delegation: information, not approval)
3. **Plan**: Invoke `writing-plans` if the issue warrants it (skip for small/obvious changes)
4. **Implement**: Invoke `executing-plans` or implement directly. TDD for code changes. Verify for config/infrastructure changes.
5. **Lint**: Auto-detect and run project linter (ruff, eslint, rustfmt, gofmt, etc.)
6. **Verify**: Run project test suite — all tests must pass
7. **Log risk**: `total-risk <category> [conditions...]` — post result as `gh issue comment`
8. **PR**: Invoke `finishing-a-development-branch` to push and create PR
9. **Next issue**: Return to main, pull, check budget, pick next issue from plan, repeat

### Pre-Authorization Table

| Step | Decision | Behavior |
|------|----------|----------|
| Issue selection | Pick from plan | Check risk budget first. Announce choice, don't ask |
| Branch creation | Create feature branch | Authorized |
| brainstorming delegation | "approval or information?" | Answer: information — present design, proceed unless technically uncertain |
| brainstorming approach | Which approach? | Pick recommended approach. Only pause if trade-offs are genuinely unclear |
| writing-plans scope | Plan scope | Write the plan, proceed to execution. Only pause if scope seems too large for one PR |
| executing-plans choices | Implementation decisions | Make them. Commit to decisions. Only pause for design flaws discovered mid-implementation |
| TDD strategy | Test strategy | Detect from project. Write tests first for code. Verify after writing for config/infrastructure |
| Commit messages | Wording | Use imperative mood, explain why. Don't ask for approval |
| PR creation | Title, body, labels | Write them well. Don't ask for review of PR text |
| Lint/format | Fix or ignore | Auto-detect and fix all |
| code-simplification | Structural changes flagged | Apply low-risk changes. For structural changes, create an issue for user approval and move on |
| finishing-a-development-branch | Release type | Recommend based on change analysis. Default patch unless features added |
| Retrospective opt-in | Run retrospective? | Always run (pre-authorized) |

### When to Pause

Stop and ask the user when encountering:

- **Genuine technical uncertainty** — two valid approaches with real trade-offs you cannot resolve
- **Scope creep** — you discover the issue is much larger than expected
- **Breaking changes** — something that would change the API contract or data model in ways not described in the issue
- **Blocked** — a dependency that prevents progress, or tests failing after repeated fix attempts
- **Toolchain discrepancy** — CONTRIBUTING.md and project structure disagree on build/test commands

### Process Rules

- **One PR per issue** — clean traceability
- **Follow CONTRIBUTING.md** — the sprint optimizes by pre-authorizing decisions, not by skipping steps
- **Duplicate check before filing issues** — `gh issue list --search "<keywords>"` first
- **Check risk budget before each task** — never start a task without `total-risk check`

## Phase 3: Wrap Up

When all planned issues are worked, the budget is exhausted, or the user signals done:

### 3a. Autonomous Retrospective

Invoke `retrospective` automatically. The retrospective analyzes the sprint session and files improvement issues:

- **Project-local**: workflow friction, documentation gaps, tooling issues — filed as issues on the current repo
- **Upstream**: skill improvements, plugin bugs — filed as issues on the plugin source repo with `feedback` label

Pre-authorized: the agent runs the retrospective and files issues without asking. The user reviews them asynchronously.

### 3b. Leave Tree Clean

- All work is in filed PRs with branches pushed
- Working tree is on main, clean (`git status` shows nothing)
- No local-only branches with unpushed work

### 3c. Write Turnover Doc

Create `.claude/turnover/YYYY-MM-DD.md` (append sequence number if file exists for same date):

```bash
mkdir -p .claude/turnover
```

```markdown
# Sprint Turnover — YYYY-MM-DD

## Plan
<current tier/priority plan — what's next, what's blocked, what shifted>

## Completed this session
- #N: <what was done> (risk cost: X)

## Risk Ledger
<full output of `total-risk status` — budget, total, all tasks with costs>

## Open PRs (ready for review/merge next sprint)
- #N: <branch, status, any notes>

## Notes
<anything surprising, blockers, or context the next session needs>
```

Post turnover summary to the most relevant issue:
```bash
gh issue comment <N> --body "Sprint turnover posted. Risk budget: <total>/<budget> used."
```

### 3d. Brief Summary

Report to user:
- Sprint complete
- Issues worked: #X, #Y
- PRs filed: #A, #B
- Risk budget: <used>/<total> (<status>)
- Tests passing: yes/no
- Recommended next: <what to work on next>

## Integration

**Invokes:**
- **requesting-code-review** — Phase 1b, dispatched as 3 parallel subagents (opus, sonnet, haiku)
- **code-simplification** — Phase 1b, after PR review fixes
- **dispatching-parallel-agents** — Phase 1b, for multi-model review dispatch
- **using-git-worktrees** — Phase 2, per-issue workspace isolation
- **brainstorming** — Phase 2, with delegation=information
- **writing-plans** — Phase 2, when issue warrants planning
- **executing-plans** — Phase 2, plan execution
- **finishing-a-development-branch** — Phase 2, PR creation and merge
- **retrospective** — Phase 3a, autonomous session analysis

**Tools:**
- **total-risk** (`${CLAUDE_PLUGIN_ROOT}/scripts/total-risk`) — risk budget tracking

**Called by:**
- Directly via `/sprint` or `/sprint <tolerance-level>`

**Standalone entry point.** Sprint is the highest-level orchestrator in the skill graph.
