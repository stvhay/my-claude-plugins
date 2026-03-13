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

Pipeline skills check context window utilization at load time via
`scripts/context-check`. Each gate has a threshold tuned to the remaining
pipeline budget: brainstorming (20%), writing-plans (65%),
subagent-driven-development (40%), executing-plans (20%). Gates recommend
`/clear` or directed `/compact` — they are advisory, not blocking.

Thresholds were calibrated from Langfuse session traces (issue #50): the full
pipeline splits roughly 50/50 between pre-execution and execution phases.
Above 80%, coding performance degrades, so execution-entry gates are more
aggressive. The agent may use discretion to trigger compaction earlier for
large plans, but not below 30%.

## Quality Gate Automation

`scripts/quality-gate.sh` ships inside dev-workflow-toolkit and runs six
structural checks against any project using the plugin:

1. **inv-numbering** — INV/FAIL identifiers in SPEC.md are sequentially
   numbered with no gaps or duplicates.
2. **issue-tracking** — Branch has a linked GitHub issue and beads tracking.
3. **skill-structure** — Each skill directory contains a SKILL.md with valid
   YAML frontmatter and a `name` matching the directory.
4. **doc-structure** — Required documents (SPEC.md, README.md) exist at their
   canonical paths.
5. **vsa-coverage** — Every plugin's skills directory has a SPEC.md.
6. **tool-health** — Required tools (uv, git) and optional tools (gh, bd) are
   installed and working.

The script is invoked by verification-before-completion (pre-merge gate),
finishing-a-development-branch (pre-PR gate), and documentation-standards
(on-demand audit). This converts several reasoning-required invariants into
structural ones enforced by automation.

## Work Tracking

Beads is the primary work-tracking system. When configured via project-init,
a CLAUDE.md directive activates beads for all skills. GitHub serves as the
external projection layer — issues and PRs receive comments at key lifecycle
points (plan summaries, progress updates, review findings, preflight results).
Granular task tracking stays in beads.

When beads is not installed (user opted out during project-init), skills fall
back to Claude Code task lists and GitHub issues.

Task titles follow a slug convention (`<slug>- <description>`) enabling
a lightweight pipeline status script (`bd-pipeline`) that renders one-line
progress: `<phase> || <slugs> | (N more) --> <next_phase>`.

## Release Infrastructure

Each project scaffolded by `project-init` gets generated release tooling:

- **`compute-version.sh` + `compute_version.py`** — Semver computation and
  version file updates. Shell wrapper delegates to Python via `uv run`.
  Reads/writes project-specific version files (plugin.json, pyproject.toml,
  package.json, Cargo.toml).
- **`release.yml`** — GitHub Actions workflow triggered on push to main.
  Creates lexicographically sortable timestamp git tags (`YYYY-MM-DDTHHMMSSZ`)
  and GitHub Releases with changelog content.
- **Validation hooks** — Claude Code hooks enforce version bump and changelog
  guardrails. Silent when compliant, structured error messages when violated.

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
