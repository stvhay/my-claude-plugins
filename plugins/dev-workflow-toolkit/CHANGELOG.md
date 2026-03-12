# Changelog

Agent-focused changelog. When a new version of this plugin is installed,
read this file and apply retroactive actions marked with **ACTION**.

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
