# Changelog

Agent-focused changelog. When a new version of this plugin is installed,
read this file and apply retroactive actions marked with **ACTION**.

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
