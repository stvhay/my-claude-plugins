# Changelog

Agent-focused changelog. When a new version of this plugin is installed,
read this file and apply retroactive actions marked with **ACTION**.

## Unreleased <!-- bump: patch -->

### Changed

- Graft karpathy-guidelines phrasings into `code-simplification` (Constraints), `subagent-driven-development/implementer-prompt` (Self-Review Discipline), and `test-driven-development` (GREEN step) to close the Surgical Changes in-flight rule gap. Same rule now echoes in three skill load points: every changed line traces to the user's request; match existing style; don't delete unrelated dead code unless asked. See `skills/UPSTREAM-karpathy.md` for evaluation and rationale.

## v1.18.0


### Added

- **sprint skill:** Autonomous development session orchestrator with three phases — Orient (turnover + multi-model PR review), Work (issue loop with pre-authorized pipeline), Wrap Up (retrospective + turnover). Explicit invocation only (`disable-model-invocation: true`). One session per `/sprint` invocation (fresh context); turnover docs bridge sessions.
- **total-risk tool:** Externalized risk budget tracking for autonomous sessions. Categories with empirically-calibrated base costs, multiplicative modifiers (file count, same-module, context degradation at ×1.05/task), additive modifiers (CI/review results). `check` command for pre-task cost preview with skip/caution/ok advice. 34 tests.
- **Risk tolerance levels:** `/sprint supervised|cautious|standard|trusted|autonomous` sets session budget ceiling (8–60).
- **INV-16:** Sprint PR reviews must dispatch to fresh-context subagents; multi-model review (opus, sonnet, haiku) via dispatching-parallel-agents.
- **INV-17:** Turnover doc format (`.claude/turnover/YYYY-MM-DD.md`, gitignored) for session continuity.
- **FAIL-11/12/13:** Failure modes for review contamination, stale turnover, autonomy drift.
- **ARCHITECTURE.md:** Session Orchestrator as 4th composition pattern, with risk tool.
- **DESIGN.md:** Instruction-Based Autonomy, Externalized Risk Accounting, and Session Continuity sections.

## v1.17.1

### Added

- **INV-15 (GitHub Projection Principle):** Skills that produce design documents, review findings, or status artifacts must post them as comments to the appropriate GitHub surface (issue pre-PR, PR post-PR). Enforced by `TestGitHubProjection` test.
- **FAIL-10:** New failure mode for artifacts produced but not posted to GitHub.
- **brainstorming:** Posts condensed design summary to GitHub issue after design approval (checklist step 9).
- **finishing-a-development-branch:** Re-integrated Step 1c (Review Documentation Check) as soft gate using `check-review-documented.sh`.

### Fixed

- **check-review-documented.sh:** Stripped beads references, simplified to GitHub-only check with expanded keyword matching (review, design, plan, verification).
- **FAIL-7:** Updated to reference expanded keyword matching instead of beads.
- **DESIGN.md:** Fixed stale Step 8 reference (should be Step 7 post-beads removal).
- **README.md:** Updated test count (283 → 288).
- **plansDirectory support:** All skills now resolve `plansDirectory` from `.claude/settings.json` instead of hardcoding `docs/plans/`. Default: `~/.claude/plans`.
- **Quoted `$PLANS_DIR`** in `finishing-a-development-branch` `ls` command to handle paths with spaces.
- **`jq` tool-health check** added to `quality_gate.py` (required for plansDirectory resolution).
- **`.project-init` marker** uses `$TIMESTAMP` placeholder instead of synthetic date.
- **CLAUDE-3 audit check** updated to verify beads directive is absent (v1.17.0 removal).

## v1.17.0


### Removed

- **Beads work tracking:** All `bd` references removed from 12 skills, SPEC.md, and CLAUDE.md. Work tracking now uses GitHub issues (persistent) + Claude Code task lists (in-session). **ACTION:** If your project's CLAUDE.md contains a beads work-tracking directive (`Use beads (bd) for all work tracking...`), remove it — skills no longer reference or expect beads.
- **INV-14** (beads work-tracking protocol) and **INV-16** (beads-aware worktrees) removed from SPEC.md. **FAIL-10** (beads database error) removed.
- Inline context gate sections removed from 5 pipeline skills (replaced by hook).

### Added

- **Context-gate hook:** `scripts/context-gate-hook.sh` — PreToolUse hook that reads per-skill thresholds from `scripts/context-thresholds.json` and warns when context utilization is too high. Replaces inline context gate logic in brainstorming, writing-plans, subagent-driven-development, and executing-plans. **Known limitation:** Claude Code does not yet expose `CLAUDE_SKILL` to hooks, so the hook is a placeholder until upstream support lands.
- **Hook-Based Enforcement** section added to `docs/DESIGN.md`.

### Changed

- **Skill prose compression:** 10 skills compressed by removing argumentation sections, redundant red flags, DOT diagrams, and verbose examples. Net reduction: 1,110 lines across 24 files.
- **INV-13** updated to reference context-gate hook instead of inline skill logic.
- **INV-15** renumbered to **INV-14** (AskUserQuestion invariant).
- Test suite updated: 283 tests (down from 316 — beads-specific tests removed).

## v1.16.2


### Added

- **project-init update workflow:** Auto-detects project state (fresh, first adoption, or update) via `.project-init` marker file. In update and first-adoption modes, runs a deep audit across 5 layers (scaffolding, CLAUDE.md, release infrastructure, spec compliance, hooks) using `references/audit-checklist.md`. Presents findings with severity levels and a numbered remediation plan for selective approval.
- `references/audit-checklist.md` — Machine-readable audit checklist with ~25 items across 5 layers, each with `Since` version for changelog-driven scoping

## v1.16.1


### Added
- **INV-16:** New SPEC.md invariant requiring beads-aware worktree operations — skills must detect `.beads/` and use `bd worktree create`/`bd worktree remove` instead of raw `git worktree` (#113)
- **FAIL-10:** Failure mode documenting orphaned Dolt server from plain `git worktree add`
- Structural tests enforcing INV-16 in `TestBeadsWorktreeInvariant`

## v1.16.0

### Added
- **INV-15:** New SPEC.md invariant requiring `AskUserQuestion` for structured choices and batching of independent questions
- **brainstorming:** Delegation pattern ("approval or information?"), question batching, eliminated unnecessary questions (epic scope auto-ask, "ready for implementation?")
- **finishing-a-development-branch:** Pre-PR Batch combining release type, scope check, base branch, and retrospective opt-in into single `AskUserQuestion` call
- **codify-subsystem:** Adaptive modality for interview — structured confirmations for high-confidence, batched free-text for open-ended, dependency-grouped batches
- **project-init:** Batched setup questions, `.worktrees/` default directory creation
- **documentation-standards:** Batched per-document approval decisions
- **retrospective:** Batched wrap-up decisions (analysis review + local improvements + upstream approval)

### Changed
- **ACTION:** Skills now use `AskUserQuestion` for structured choices. If you have custom skills that follow the "one question at a time" pattern, consider updating them per INV-15.

## v1.15.0

### Added

- `resist-memory-redirect.sh` SessionStart hook — detects when Claude Code writes memory to `~/.claude/projects/` and redirects content to project root `MEMORY.md`

## v1.14.0

### Fixed
- Brainstorming auto-creates worktree when on main/master instead of asking (#97)
- Release workflow blocked by branch protection — use GitHub App token + ruleset bypass for version bump push (#104)

### Changed
- **Version bumping is now CI-driven.** Branches write `## Unreleased` changelog
  entries with `<!-- bump: TYPE -->` comments instead of bumping version files
  directly. CI validates PR label consistency pre-merge and bumps versions
  post-merge with concurrency serialization.
- `check-version-bump.sh` validates `## Unreleased` + bump comment instead of
  version file changes
- `check-changelog.sh` validates bump comment in `## Unreleased` instead of
  `## vX.Y.Z` section
- `compute-version.sh` gains `--ci` mode for CI-driven execution
- `finishing-a-development-branch` Step 2b writes changelog + applies label
  (no longer runs `compute-version.sh --update`)
- `release.yml` performs version bump post-merge with concurrency group
- `ci.yml` gains `version-check` job for pre-merge label/changelog validation

**ACTION:** PR labels `bump:patch`, `bump:minor`, `bump:major` are now required
on PRs with source changes. The version bump happens automatically at merge time.

## v1.13.4

- **fix:** Replace `bd create -f` with `plan-to-beads.sh` for plan-to-beads conversion (#92)
- `bd create -f` uses h2 headings as task boundaries and doesn't skip code fences, producing spurious tasks from embedded file content
- New script uses `markdown-it-py` to parse `### Task N:` headings with proper code fence handling
- **fix:** Add plan fidelity guidance to implementer and spec reviewer prompt templates (#61)
  - Implementer subagents must document divergences from plan's specified approach/tech stack
  - Spec reviewer checks for undocumented plan divergences and flags them as findings
  - New "Plan Divergences" field in implementer report format

## v1.13.3

- **fix:** Move quality gate SessionStart hook from project `settings.json` to plugin `hooks.json`, using `${CLAUDE_PLUGIN_ROOT}` for version-independent path resolution (#83)
- **feat:** Add `migrate-quality-gate.sh` hook that removes stale version-pinned quality gate entries from project `.claude/settings.json`
- **ACTION:** If your project has a quality gate entry in `.claude/settings.json`, it will be automatically removed on next session start. The quality gate now runs via the plugin hook for all projects.

## v1.13.2

### Fixed
- Complete beads integration across all work-tracking skills (#78)
  - All 11 work-tracking skills now document beads-primary and task-list-fallback paths
  - Task title slug convention (`<slug>- <description>`) for pipeline status display
  - GitHub projection at key lifecycle points (plan summaries, batch progress, review findings)
  - `bd` failure treated as workflow blocker with `bd doctor` recommendation
  - project-init installs beads by default and writes CLAUDE.md work-tracking directive
  - SPEC.md INV-7 expanded to cover all work-tracking skills

### Added
- `bd-pipeline` script for one-line pipeline status from beads task JSON

## v1.13.1

Remove unnecessary `from __future__ import annotations` from all Python scripts
and tests. The project requires Python 3.13+ (`pyproject.toml`), making these
imports no-ops. Also moves `Callable` import in `quality_gate.py` from
`TYPE_CHECKING`-only to a regular import, fixing a latent runtime error that
was masked by the `__future__` import.

## v1.13.0

### Added
- **brainstorming:** New checklist step 7 "Evaluate epic scope" — after design
  approval, checks whether the work spans multiple distinct issues that should
  be an epic with child issues. Soft gate: recommends restructuring but lets the
  user proceed.
- **finishing-a-development-branch:** New Step 3b "Scope Check" — before PR
  creation, reviews accumulated changes for scope drift. Warns when commits go
  beyond the originating issue. Soft gate.

Both checks enforce the squash-merge convention: one PR = one commit = one issue.

## v1.12.3

Fix: brainstorming skill's "Evaluating UX Design Need" section had competing
recommend/skip lists that let agents bypass UX design for agentic interaction
work. Simplified to default-on: always use ux-design-agent unless the change
doesn't alter user experience or agent interaction patterns.

## v1.12.2

Fix: `extract_usage()` in `langfuse-trace.py` included cached tokens in the
`input` field, causing Langfuse to double-charge them (~9x cost inflation).
Now passes Anthropic's non-overlapping token fields through directly using
Langfuse canonical field names (`cache_read_input_tokens`,
`cache_creation_input_tokens`), ensuring costs match default model pricing.

## v1.12.1

Fix: `ensure-statusline.sh` looked for binary named `claude-statusline` in
the release tarball, but the actual binary is named `statusline`. Hook failed
on fresh installs.

## v1.12.0

### Added
- `scripts/context-check` — POSIX shell script that reads context window
  utilization from `.claude/.statusline-stats`
- Context Gate directives in brainstorming (>20%), writing-plans (>65%),
  subagent-driven-development (>40%), and executing-plans (>20%)
- `hooks/ensure-statusline.sh` — SessionStart hook that installs/updates
  the `claude-statusline` binary from `stvhay/claude-statusline` GitHub
  releases. Configures statusLine and UserPromptSubmit hook in
  `~/.claude/settings.json`. Checks for updates daily.
- INV-13: context gate invariant in SPEC.md
- FAIL-9: missing statusline-stats failure mode in SPEC.md

### Changed
- ARCHITECTURE.md: new "Context-Aware Session Management" section

## v1.11.0

### CI integration and capability-based test guards

Added CI infrastructure for the plugin ecosystem (#51).

- **Capability markers:** Tests declare resource requirements with
  `@pytest.mark.capability("gpu")`. `conftest.py` reads `CI_CAPABILITIES` env var
  and auto-skips tests when required resources aren't available.
- **Discovery runner:** Repo-root `tests/run-all.sh` discovers and runs all
  `plugins/*/tests/run-all.sh` — single CI entry point.
- **CI workflow:** `ci.yml` switched from direct pytest to the discovery runner.
- **CI hard gate:** `finishing-a-development-branch` Step 1d enforces `gh pr checks`
  before PR creation (INV-12).
- **Branch protection:** `project-init` now configures branch protection on `main`
  via `gh api` (require CI pass, require squash merge).
- **Test fix:** `test_reference_dirs_exist` now resolves cross-skill reference paths
  correctly.

**ACTION:** If you use `finishing-a-development-branch`, note the new Step 1d
(CI status check) between review docs check and documentation validation.

## v1.10.1

### Prefer parsers for formats with formal grammars

Added guidance so agents use stdlib/third-party parsers instead of regex/sed/grep
for any format with a formal grammar (#62).

- Reference doc: `requesting-code-review/references/structured-format-parsing.md`
- Code reviewer checklist item for formal grammar format handling
- Inline rules in test-driven-development (GREEN section) and code-simplification
  (new Parser Preference pattern category)

## v1.10.0

### Worktree naming convention and review navigation

Codified the worktree naming convention in `using-git-worktrees`: branches
and worktree paths follow `<type>/<issue>-<slug>` pattern. Updated
`requesting-code-review` to navigate PR → issue number → worktree path,
enabling `/review <PR#>` to automatically find the correct worktree.

SPEC.md INV-8 tightened to define the naming contract both skills rely on.

## v1.9.0

### Merge strategy & release pipeline

Squash merge is now the only merge strategy in finishing-a-development-branch.
Version bump workflow integrated: agent recommends release type, writes
changelog, runs `compute-version.sh --update`.

**New scripts:**
- `compute-version.sh` / `compute_version.py` — semver computation and
  version file updates for `plugin.json` + `pyproject.toml`

**New hooks:**
- `check-version-bump.sh` — errors if source files changed without version bump
- `check-changelog.sh` — errors if version bumped without changelog section

**Skill updates:**
- `finishing-a-development-branch` — squash merge only, version bump step
  (Step 2b), missing release infrastructure warning
- `project-init` — release infrastructure scaffolding (compute-version.sh,
  release.yml, validation hooks)
- `writing-plans` — scope detection warning before plan creation

**New SPEC.md invariants:**
- INV-10: Version bump enforcement (structural, hook-enforced)
- INV-11: Changelog enforcement (structural, hook-enforced)
- FAIL-8: Version drift between version files

**ACTION:** Marketplace cleanup — `version` fields removed from
marketplace.json plugin entries and `metadata.version`. Plugin.json is
now the sole version authority. If you have scripts that read version
from marketplace.json, update them to read from plugin.json instead.

**ACTION:** Run `compute-version.sh` for version bumps instead of
manually editing plugin.json + pyproject.toml.

## v1.8.2-0

### Review documentation standard

Add `check-review-documented.sh` validation script and INV-9 review
documentation standard. Five skills updated with review documentation
instructions. Consolidate INV-8a/8b into INV-8.

## v1.8.1

Fix: adapt Langfuse hook to SDK v4 `start_observation()` API. The
`start_time`/`end_time` parameters were removed in Langfuse Python SDK
v4.0.0. Timestamps are now stored in observation metadata and `end_time`
is passed as epoch nanoseconds to `.end()`.

## v1.8.0

### Langfuse tracing: full data capture

Generations now include user prompts as input (previously only assistant
output was shipped). Timestamps from transcript JSONL are used for
`start_time`/`end_time` on generation observations, giving real LLM
latency in Langfuse. Session metadata now includes `cwd`,
`permission_mode`, and `cache_hit_rate`. Subagent spans capture
`last_assistant_message` as output.

## v1.7.1

Fix: use `setsid` to create a new process session so the background
Langfuse process survives SessionEnd process group kill.

## v1.7.0

### Async hook execution and error reporting

All Langfuse SDK work now runs fully backgrounded — hooks never block
Claude Code. Sentinel-based error reporting writes per-call error files
and touches `~/.cache/langfuse-hook/error-flag`; the SessionStart health
check is a single file-exists test with zero cost on the happy path.
SDK delivery failures (silent by default) are detected via stderr
capture with `logging.basicConfig(force=True)`.

## v1.6.6

Use uv instead of python3 -m venv for bootstrap. Faster and avoids
the python3-venv package dependency on Debian/Ubuntu.

## v1.6.5

Fix: log bootstrap failures instead of failing silently.

## v1.6.4

Fix: auto-bootstrap venv in background on first run. Skips current
invocation but venv is ready for the next hook call.

## v1.6.3

Fix: add 8-second SIGALRM timeout to Python hook to prevent Claude Code
hook cancellation on SessionEnd.

## v1.6.2

Fix: hook no longer auto-bootstraps venv during SessionStart. Prevents
blocking Claude Code if pip install hangs on slow networks.

## v1.6.1

Fix: removed explicit hooks manifest reference that caused duplicate
hooks error. The `hooks/hooks.json` file is auto-loaded by convention.

## v1.6.0

### Langfuse tracing hooks

Claude Code hooks now ship session traces to a self-hosted Langfuse instance.
Captures LLM generations (model, token usage with cache breakdown, cost),
tool observations, and subagent spans. The hook bootstraps its own private
venv at `~/.cache/langfuse-hook/venv/` — no dependency on the user's project.

**ACTION:** Set env vars `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
`LANGFUSE_HOST`, and `LANGFUSE_SOURCE_PROJECT` to enable tracing. Create
custom model definitions in Langfuse for Claude 4.x models for cost tracking.

## v1.5.0

### New check: cross-links

The quality gate now validates that file paths referenced in SPEC.md
Dependencies tables actually exist. Paths must be in backticks in the
third column (`SPEC.md Path`); N/A entries are ignored.

### Session-start hook support

The project-init skill now offers to install a Claude Code SessionStart
hook that runs the quality gate automatically at the start of each session.
Configuration goes in `.claude/settings.json`.

### CHANGELOG reading mechanism

SPEC.md and project-init now reference `CHANGELOG.md` for upgrade guidance.
Agents should check the changelog when directed by these documents.

## v1.4.0

### Quality gate rewritten in Python

The quality gate (`scripts/quality-gate.sh`) now uses `markdown-it-py` for
AST-based structural validation instead of brittle regex patterns. This adds
a `uv` dependency.

**ACTION:** Ensure `uv` is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### New check: doc-stats

The quality gate now validates numeric statistics in markdown files via
**stat-check footnotes**. Any number followed by a footnote like
`[^stat-test-count]` whose body is `stat-check: total-test-count` will be
validated against the actual count.

**ACTION:** Review README.md and SPEC.md files for numeric claims (test counts,
skill counts, component counts). Add stat-check footnotes to prevent staleness.
See the documentation-standards skill for the full convention.

Available checks: `total-test-count`, `test-suite-count`, `skill-count`.

### New skill: retrospective

Post-completion session analysis. Automatically invoked after PR creation by
finishing-a-development-branch.

### Simplified quality gate invocation

Skills now reference the quality gate script relative to their own location
(`<plugin-root>/scripts/quality-gate.sh`) instead of searching the plugin
cache. The shell wrapper checks dependencies and gives clear error messages.

**ACTION:** If you have custom scripts referencing the quality gate, update
paths to use the plugin-root-relative pattern.
