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
   executing-plans, finishing-a-development-branch.

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
