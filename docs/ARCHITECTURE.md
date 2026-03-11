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

## Documentation Structure

This document (`docs/ARCHITECTURE.md`) and its companion `docs/DESIGN.md`
form the project-level tracked documentation tier. They are synthesized from
plugin-level `skills/SPEC.md` files and updated when structural decisions
change. SPEC.md files define invariants for the plugin distribution model —
all paths and references assume remote installation, not local clones.
`scripts/quality-gate.sh` validates structural invariants automatically.
See [DESIGN.md](DESIGN.md) for the three-tier documentation model, writing
conventions, and patterns like SPEC.md contracts and upstream provenance.
