# Architecture

> In the context of a personal Claude Code plugin marketplace, facing the need
> for consistent plugin structure and independent evolution, we adopted a
> mono-repo with per-plugin isolation and the Agent Skills standard, accepting
> coupled release mechanics in exchange for cross-plugin consistency.

## Plugin Marketplace Model

The repository is a mono-repo cataloged by `.claude-plugin/marketplace.json`.
Each plugin lives under `plugins/<name>/` with its own `plugin.json` manifest
carrying an independent version number.

Installation is a single command:
`/plugin marketplace add stvhay/my-claude-plugins`

**Trade-offs.** A shared repo simplifies consistency enforcement (linting,
spec templates, CI) but couples release mechanics — a broken CI on one plugin
blocks merges for all. Per-plugin versioning in `plugin.json` mitigates this
at the metadata level; full decoupling would require separate repos.

## Agent Skills Standard

Every skill is defined by a `SKILL.md` file with YAML frontmatter containing
at minimum `name` and `description`. Constraints on `name`:

- Lowercase, hyphenated
- Maximum 64 characters
- Must match the enclosing directory name

The `description` field is the primary trigger mechanism — Claude Code uses
keyword matching against it to decide when to invoke a skill. The standard
is external, maintained at [agentskills.io](https://agentskills.io/specification).

## Skill Composition Patterns

Three composition patterns recur across plugins:

1. **Orchestrator to Specialist.** A hub skill classifies the request and
   delegates to a spoke. Examples: `stamp-base` routes to STPA / STPA-Sec /
   CAST; `ux-design-agent` routes to design-principles / delegation-oversight.

2. **Pipeline.** Skills execute in sequence where the output of one feeds the
   next. The dev-workflow-toolkit pipeline: brainstorming, writing-plans,
   executing-plans, finishing-a-development-branch, retrospective. The
   thinking-toolkit pipeline: ideate/first-principles → heilmeier-catechism
   → brainstorming (evaluative assessment bridging divergent thinking and
   design commitment).

3. **Cross-cutting technique.** Skills that any other skill may invoke for a
   specific concern: trust-calibration, ux-writing,
   writing-clearly-and-concisely.

## Per-Plugin Isolation

Each plugin is self-contained: manifest, skills, readme, and SPEC.md live
together under one directory. Cross-plugin composition happens only by name
reference — no shared code, no imports.

**Consequence.** Any plugin can be extracted to its own repository without
modification. This preserves the option to split the mono-repo later without
a rewrite.

## Context-Aware Session Management

A PreToolUse hook (`scripts/context-gate-hook.sh`) checks context window
utilization against per-skill thresholds defined in
`scripts/context-thresholds.json`. Each gate has a threshold tuned to the
remaining pipeline budget: brainstorming (20%), writing-plans (65%),
subagent-driven-development (40%), executing-plans (20%). The hook emits
advisory warnings — it does not block execution.

> **Known limitation (2026-03):** Claude Code does not yet expose
> `CLAUDE_SKILL` to hooks, so the hook is a placeholder until upstream
> support lands. The infrastructure is in place for when the env var becomes
> available.

Thresholds were calibrated from Langfuse session traces (issue #50): the full
pipeline splits roughly 50/50 between pre-execution and execution phases.

## Quality Gate Automation

`scripts/quality-gate.sh` ships inside dev-workflow-toolkit and runs six
structural checks against any project using the plugin:

1. **inv-numbering** — INV/FAIL identifiers in SPEC.md are sequentially
   numbered with no gaps or duplicates.
2. **issue-tracking** — Branch has a linked GitHub issue.
3. **skill-structure** — Each skill directory contains a SKILL.md with valid
   YAML frontmatter and a `name` matching the directory.
4. **doc-structure** — Required documents (SPEC.md, README.md) exist at their
   canonical paths.
5. **vsa-coverage** — Every plugin's skills directory has a SPEC.md.
6. **tool-health** — Required tools (uv, git) and optional tools (gh, bd) are
   installed and working.

The script is invoked by verification-before-completion (pre-merge gate),
finishing-a-development-branch (pre-PR gate), documentation-standards
(on-demand audit), and as a SessionStart hook registered in the plugin's
`hooks.json` — running automatically on every session for all projects
using the plugin. A companion migration hook removes stale version-pinned
quality gate entries from project-level `.claude/settings.json` written by
earlier versions of project-init.

## Work Tracking

Work tracking uses GitHub issues (persistent across sessions) and Claude Code
task lists (in-session progress). GitHub serves as the external projection
layer — issues and PRs receive comments at key lifecycle points (design
summaries, plan summaries, progress updates, review findings). INV-15 in the
dev-workflow-toolkit SPEC.md enumerates which skills must project and to which
GitHub surface (issue pre-PR, PR post-PR). `check-review-documented.sh`
validates at branch completion that projection actually occurred.

## Release Infrastructure

Each project scaffolded by `project-init` gets generated release tooling:

- **`compute-version.sh` + `compute_version.py`** — Semver computation and
  version file updates. Shell wrapper delegates to Python via `uv run`.
  Reads/writes project-specific version files (plugin.json, pyproject.toml,
  package.json, Cargo.toml). Supports `--ci` mode that reads bump type from
  `<!-- bump: TYPE -->` in CHANGELOG.md and rewrites `## Unreleased` to
  `## vX.Y.Z` after version bump.
- **`release.yml`** — GitHub Actions workflow triggered on push to main.
  Detects plugins with `## Unreleased` sections, runs version bump in `--ci`
  mode, commits, creates timestamp tags, and publishes GitHub Releases.
  Uses a concurrency group to serialize parallel merges.
- **`ci.yml` version-check** — Pre-merge CI job that validates PR labels
  match changelog bump type for changed plugins.
- **Validation hooks** — Claude Code hooks enforce changelog entry presence
  on branches. Silent when compliant, structured error messages when violated.

Version bumping is CI-driven: branches write `## Unreleased` changelog entries
with `<!-- bump: TYPE -->` comments and apply `bump:TYPE` PR labels. CI bumps
the actual version files post-merge on main, eliminating race conditions when
parallel branches modify the same plugin.

Version authority: `plugin.json` (for Claude Code plugins) or the
stack-appropriate manifest. Marketplace.json does not carry version
information — `plugin.json` drives update detection directly.

Trade-off: generated scripts are per-project (not shared library). Each
project owns its release tooling and can customize. Cost is duplication;
benefit is zero coupling between projects.

## Continuous Integration

A repo-root `tests/run-all.sh` discovers each plugin's test runner
(`plugins/*/tests/run-all.sh`) and executes them in sequence. This gives CI
a single entry point while allowing each plugin to own its test configuration.

Tests declare resource requirements via pytest markers:
`@pytest.mark.capability("gpu")`. The `CI_CAPABILITIES` environment variable
(space-separated) declares which resources are available; `conftest.py`
auto-skips tests whose required capabilities are missing. GitHub Actions
runners set `CI_CAPABILITIES=""` — only resource-free tests run in CI.

**Trade-offs.** Capability-based skipping means CI cannot catch regressions in
resource-dependent tests. The alternative — provisioning GPUs or ollama in
CI — has disproportionate cost for a personal plugin repository. Local runs
with `CI_CAPABILITIES="gpu ollama"` cover the gap.

Branch protection (require CI pass, require squash merge) is configured by
`project-init` via `gh api`, enforcing that no code merges without passing
tests.

## Hook-Based Telemetry

The dev-workflow-toolkit plugin registers Claude Code hooks for Langfuse
tracing. A shell wrapper (`hooks/langfuse-trace.sh`) bootstraps a private
Python venv at `~/.cache/langfuse-hook/venv/` and invokes the trace script
on each hook event. State is tracked per-session in a user-private temp
directory. Each hook invocation is a separate process — trace-level attributes
(name, session_id, tags) are set once at SessionStart and applied trace-wide
by the Langfuse server; per-observation OTel context does not persist across
invocations.

**Trade-offs.** A self-bootstrapping venv adds first-run latency (~5s) but
eliminates dependency on the user's project environment. Shipping data on
every PostToolUse adds per-tool overhead but ensures crash resilience — if a
session exits abnormally, most data has already been shipped.

## Environment Hooks

The dev-workflow-toolkit plugin ships a `post-checkout` git hook that runs
`direnv allow` after any checkout event (including `git worktree add`). The
hook only auto-allows if the main worktree's `.envrc` is already approved,
inheriting the user's existing trust decision. A Claude Code `SessionStart`
hook ensures the git hook is installed, self-healing if it was removed or
never set up.

**Trade-offs.** Automating `direnv allow` trades explicit per-directory
approval for worktree reliability. The trust boundary is the main worktree's
existing approval — if the user trusted that `.envrc`, worktrees sharing the
same content inherit that trust.

## Documentation Structure

This document (`docs/ARCHITECTURE.md`) and its companion `docs/DESIGN.md`
form the project-level tracked documentation tier. They are synthesized from
plugin-level `skills/SPEC.md` files and updated when structural decisions
change. SPEC.md files define invariants for the plugin distribution model —
all paths and references assume remote installation, not local clones.
`scripts/quality-gate.sh` validates structural invariants automatically.
See [DESIGN.md](DESIGN.md) for the three-tier documentation model, writing
conventions, and patterns like SPEC.md contracts and upstream provenance.
