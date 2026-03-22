# Skills Subsystem

## Purpose

The skills directory provides reusable agent instructions as Markdown documents.
Each skill is a self-contained directory with a SKILL.md frontmatter file that
Claude Code loads automatically based on keyword matching in the `description`
field. Skills encode proven techniques, processes, and domain expertise that
agents apply during specific task types (brainstorming, planning, testing, etc.).

The key design decision: skills are documentation-as-code, version-controlled
alongside the project, and tested via the same TDD methodology they prescribe.

> **Upgrade guidance:** When reviewing plugin updates, check `CHANGELOG.md`
> in the plugin root for entries marked **ACTION** that may need project-level changes.

## Core Mechanism

Skills are discovered via YAML frontmatter in `*/SKILL.md` within a plugin's
`skills/` directory. When installed as a plugin, skills live under
`~/.claude/plugins/cache/<repo>/<plugin>/<version>/skills/`. The discovery
mechanism is the same regardless of installation method.
The `name` field maps to `/skill-name` invocation; the `description` field
drives automatic keyword-based triggering. Loading is one-directional: Claude
Code reads a skill's directory, and the skill references other skills by name,
never by path.

**Key files:**
- `UPSTREAM-superpowers.md` — Tracks provenance and sync status for skills
  originating from [obra/superpowers](https://github.com/obra/superpowers)
- `*/SKILL.md` — Entry point for each skill (YAML frontmatter + Markdown body)

## Composition

Skills compose into a development workflow graph. The primary flow is:

> brainstorming → writing-plans → executing-plans / subagent-driven-development → finishing-a-development-branch

**During execution,** quality skills are invoked as needed:
- test-driven-development, systematic-debugging, code-simplification,
  verification-before-completion

**Cross-cutting concerns:**
- documentation-standards is invoked by brainstorming (draft standards) and
  finishing-a-development-branch (validate standards compliance)
- dispatching-parallel-agents, using-git-worktrees support execution at scale
- requesting-code-review, receiving-code-review bracket the PR lifecycle

**Standalone entry points:** project-init, setup-rag, codify-subsystem

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name` | Claude Code skill router | Must be unique, lowercase, hyphenated |
| YAML frontmatter `description` | Claude Code keyword matcher | Must contain trigger keywords |
| `/skill-name` invocation | Users and other skills | Must be stable across sessions |
| Cross-skill references | Skills referencing each other | Use skill name, not file path |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | Every skill directory contains exactly one `SKILL.md` with valid YAML frontmatter (`name` + `description`) | structural | Claude Code cannot discover or load skills without frontmatter |
| INV-2 | Skill names are unique across all `SKILL.md` files | structural | Duplicate names cause routing ambiguity |
| INV-3 | Plugin-distributed skills require no gitignore configuration; project-local skills (if any) must have appropriate gitignore entries | structural | Plugin cache is outside the project repo; only project-local skills need gitignore management |
| INV-4 | Upstream provenance tracking (`UPSTREAM-*.md`) is maintainer-only; consuming agents must not modify these files | reasoning-required | UPSTREAM files in the plugin cache are read-only from the consuming project's perspective |
| INV-5 | Skills that reference other skills use the skill name (not file path) in their Integration section | reasoning-required | Skill directories may move; names are the stable identifier |
| INV-6 | Support files (prompts, templates, examples) live inside the skill's own directory | structural | Skills must be self-contained — an agent loads one directory |
| INV-7 | Entry-point skills (brainstorming, systematic-debugging) auto-create GitHub issues with duplicate search via `gh issue list --search` | reasoning-required | Prevents duplicate issues and provides tracking context |
| INV-8 | Worktree naming and navigation: (a) Worktree paths mirror branch names: `.worktrees/<type>/<issue>-<slug>` where `type` is `feature`/`fix`/`docs`/`chore`/`refactor`, `issue` is the GitHub issue number, and `slug` is a short description. (b) Skills invocable by PR number (`requesting-code-review`) resolve PR → issue number (from GitHub closing keywords in body, regex `(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#(\d+)`) → match `git worktree list` paths with bounded regex `/<issue>-`. (c) Skills executing within a worktree confirm context via `git rev-parse --show-toplevel` + `git worktree list` and cross-reference the `.issue` file | reasoning-required | Enables `/review <PR#>` to locate the correct worktree automatically; ensures execution stays in the correct worktree |
| INV-9 | Review documentation exists in GitHub issue (comment with review summary) for completed tasks | reasoning-required | Ensures review findings are traceable and visible to collaborators |
| INV-10 | Source changes in a plugin directory require an `## Unreleased` section in that plugin's `CHANGELOG.md` with a `<!-- bump: TYPE -->` HTML comment | structural | Prevents unversioned changes from shipping to users; hook-enforced via `check-version-bump.sh` |
| INV-11 | PRs with changelog bump type require a matching `bump:TYPE` PR label; CI validates consistency before merge | structural | Ensures bump intent is visible on the PR and consistent with changelog; CI-enforced via pre-merge workflow |
| INV-12 | CI status checks must pass before PR creation in `finishing-a-development-branch` | structural | Prevents merging code that fails automated tests; enforced by `gh pr checks` hard gate |
| INV-13 | Pipeline skills declare their context threshold in `scripts/context-thresholds.json`; the `context-gate-hook.sh` PreToolUse hook enforces automatically. Skills must not contain inline context gate sections. **Known limitation (2026-03):** Claude Code does not yet expose `CLAUDE_SKILL` to hooks, so the hook is a placeholder until upstream support lands | structural | Prevents context exhaustion during long pipelines; hook-based enforcement removes attention burden from skills |
| INV-14 | Skills MUST use `AskUserQuestion` for decisions with enumerable options when the agent can propose good options with confidence. When 2+ independent questions exist in sequence, they MUST be batched into a single call (max 4). Open-ended questions that are independent SHOULD be presented together in a single free-text message. Agent chooses modality (structured vs free-text) based on confidence in proposed options | reasoning-required | Reduces round-trips and token waste; each round-trip re-sends full conversation context |
| INV-15 | Skills that produce design documents, review findings, or status artifacts MUST post them as comments to the appropriate GitHub surface: issue (pre-PR) or PR (post-PR). Projection skills are enumerated in `GITHUB_PROJECTION_SKILLS` in test_integration.py | structural | Ensures work artifacts are visible to collaborators and traceable in GitHub; prevents silent local-only results that disappear with the session |
| INV-16 | Sprint PR reviews MUST dispatch to subagents for fresh context; the orchestrator context must not be used for review. Multi-model review (opus, sonnet, haiku) runs in parallel via `dispatching-parallel-agents` | reasoning-required | Prevents context contamination in chained sprints where the orchestrator accumulates prior sprint work; model diversity catches different categories of issues |
| INV-17 | Sprint turnover docs follow the format `.claude/turnover/YYYY-MM-DD.md` (gitignored) with sections: Plan, Completed this session, Risk Ledger, Open PRs, Notes. Each sprint session must write a turnover doc in Phase 3 | reasoning-required | Enables session continuity — the next sprint reads the most recent turnover to orient without re-evaluating the entire issue board |

**Enforcement classification:**
- **structural** — enforced by test suite, gitignore structure, or directory convention; pattern-matchable
- **reasoning-required** — needs architectural understanding; verified during code review

## Work Tracking

Work tracking uses GitHub issues (persistent across sessions) and Claude Code
task lists (in-session progress). GitHub issues and PRs receive comments at key
lifecycle points (plan summaries, progress updates, review findings).

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not discovered by Claude Code | Missing or malformed YAML frontmatter in SKILL.md | Add `---` fenced frontmatter with `name` and `description` fields |
| FAIL-2 | Wrong skill triggered for a task | Overly broad keywords in `description` field | Narrow the description; use specific trigger phrases |
| FAIL-3 | Skill changes lost after git operations | For project-local skills: missing gitignore entry | Ensure project-local skill directories have appropriate gitignore entries; plugin-distributed skills are unaffected |
| FAIL-4 | Upstream sync clobbers local customizations | Skill marked "identical" in UPSTREAM tracking but has local changes | Maintainer action: update status to "diverged" with notes on what differs in the plugin source repo |
| FAIL-5 | Skill references broken after rename | Cross-references use file paths instead of skill names | Update references to use `/skill-name` form |
| FAIL-6 | Silent issue creation skipped | Entry-point skill fails to create issue (network error, auth failure) without informing the user | Surface the error, proceed without issue tracking, warn user that the work is untracked |
| FAIL-7 | Review documentation missing at branch completion | `finishing-a-development-branch` runs `check-review-documented.sh` but no review, design, plan, or verification comments found in GitHub issue | Post artifacts during development via `gh issue comment` (design summaries, review findings, plan summaries) |
| FAIL-8 | `check-version-bump.sh` errors with CHANGELOG_ENTRY_REQUIRED or BUMP_TYPE_MISSING | Source files changed without `## Unreleased` section or without `<!-- bump: TYPE -->` comment | Add `## Unreleased` section with `<!-- bump: patch -->` (or minor/major) comment to CHANGELOG.md |
| FAIL-9 | Context gate warns "context awareness unavailable" | `.claude/.statusline-stats` not found (statusline not configured or not running) | Ensure claude-statusline is configured for the project; `context-check` script exits with error, agent warns user and proceeds |
| FAIL-10 | Design, review, or status artifact produced but not posted to GitHub | Skill runs locally without `gh issue comment` or `gh pr comment` | Add projection command to skill; add skill to `GITHUB_PROJECTION_SKILLS` test dict (INV-15) |
| FAIL-11 | PR merged with issues that multi-model review would have caught | Sprint reviews run with single model or in contaminated orchestrator context | Ensure Phase 1b dispatches 3 parallel subagents (opus, sonnet, haiku) with fresh context per review |
| FAIL-12 | Sprint starts with stale turnover plan | Turnover doc references closed issues or shifted priorities | Phase 1a must validate turnover against current issue board; update plan if stale |
| FAIL-13 | Sprint autonomy drift — agent pauses for pre-authorized decisions | Pre-authorization table not followed; agent treats sprint like interactive session | Review pre-authorization table; only pause for items in "When to Pause" section |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Adding a skill derived from upstream | Maintainer: add entry to UPSTREAM-*.md with "identical" status and sync date | INV-4 |
| Modifying a skill that originated from upstream | Maintainer: update status to "diverged" in UPSTREAM-*.md with change notes | INV-4 |
| Referencing another skill from within a SKILL.md | Use skill name in Integration section (e.g., "writing-plans"), never file paths | INV-5 |
| Question has enumerable answers and agent can propose good options | Use `AskUserQuestion` with recommendation as first option | INV-14 |
| Question is open-ended or agent lacks confidence in options | Use free-text in a single message | INV-14 |
| Multiple independent questions pending | Batch into single `AskUserQuestion` (max 4) or single free-text message | INV-14 |
| Starting a design-heavy workflow | Ask delegation question: "Design for approval or information?" | INV-14 |
| CLAUDE.md has workflow defaults for a recurring question | Pre-answer the question without prompting | INV-14 |
| Running autonomous sprint session | Follow pre-authorization table; pause only for genuine uncertainty, scope creep, breaking changes, or blockers | INV-16, INV-17 |
| Reviewing PR during sprint Phase 1b | Dispatch 3 fresh-context subagents (opus/sonnet/haiku), synthesize findings | INV-16 |

## Testing

**Traceability:** INV-1, INV-2: enforced by `tests/validate-frontmatter.sh`.
INV-3: structural — plugin distribution eliminates the need for gitignore management.
INV-4: reasoning-required — maintainer-only, verified during plugin releases.
INV-5: reasoning-required — verified during code review.
INV-6: structural — directory convention.

INV-10, INV-11: INV-10 enforced by Claude Code hook (`check-version-bump.sh`) at session Stop events. INV-11 enforced by CI pre-merge workflow (`ci.yml` version-check job). Both validated by `test_version_hooks.py`.
INV-12: enforced by `finishing-a-development-branch` skill prompt (Step 1d hard gate using `gh pr checks`).
INV-14: reasoning-required — verified by `test_inv14_structured_question_preference` and during code review of SKILL.md updates.
INV-15: structural — enforced by `TestGitHubProjection` in `test_integration.py`; `GITHUB_PROJECTION_SKILLS` dict enumerates all projection-required skills.
INV-16: reasoning-required — verified by `test_sprint_dependency_resolution` (SKILL.md references dispatching-parallel-agents) and during code review.
INV-17: reasoning-required — verified during code review of SKILL.md turnover section.

Skills are additionally validated via subagent pressure testing — see `/skill-creator`.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| obra/superpowers | external | N/A — upstream repo, tracked in UPSTREAM-superpowers.md |
| spec template | internal | N/A — inlined in codify-subsystem SKILL.md |
