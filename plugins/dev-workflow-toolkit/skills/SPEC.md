# Skills Subsystem

## Purpose

The skills directory provides reusable agent instructions as Markdown documents.
Each skill is a self-contained directory with a SKILL.md frontmatter file that
Claude Code loads automatically based on keyword matching in the `description`
field. Skills encode proven techniques, processes, and domain expertise that
agents apply during specific task types (brainstorming, planning, testing, etc.).

The key design decision: skills are documentation-as-code, version-controlled
alongside the project, and tested via the same TDD methodology they prescribe.

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

**Enforcement classification:**
- **structural** — enforced by test suite, gitignore structure, or directory convention; pattern-matchable
- **reasoning-required** — needs architectural understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not discovered by Claude Code | Missing or malformed YAML frontmatter in SKILL.md | Add `---` fenced frontmatter with `name` and `description` fields |
| FAIL-2 | Wrong skill triggered for a task | Overly broad keywords in `description` field | Narrow the description; use specific trigger phrases |
| FAIL-3 | Skill changes lost after git operations | For project-local skills: missing gitignore entry | Ensure project-local skill directories have appropriate gitignore entries; plugin-distributed skills are unaffected |
| FAIL-4 | Upstream sync clobbers local customizations | Skill marked "identical" in UPSTREAM tracking but has local changes | Maintainer action: update status to "diverged" with notes on what differs in the plugin source repo |
| FAIL-5 | Skill references broken after rename | Cross-references use file paths instead of skill names | Update references to use `/skill-name` form |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Adding a skill derived from upstream | Maintainer: add entry to UPSTREAM-*.md with "identical" status and sync date | INV-4 |
| Modifying a skill that originated from upstream | Maintainer: update status to "diverged" in UPSTREAM-*.md with change notes | INV-4 |
| Referencing another skill from within a SKILL.md | Use skill name in Integration section (e.g., "writing-plans"), never file paths | INV-5 |

## Testing

**Traceability:** INV-1, INV-2: enforced by `tests/validate-frontmatter.sh` (17 tests).
INV-3: structural — plugin distribution eliminates the need for gitignore management.
INV-4: reasoning-required — maintainer-only, verified during plugin releases.
INV-5: reasoning-required — verified during code review.
INV-6: structural — directory convention.

Skills are additionally validated via subagent pressure testing — see `/skill-creator`.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| obra/superpowers | external | N/A — upstream repo, tracked in UPSTREAM-superpowers.md |
| spec template | internal | N/A — inlined in codify-subsystem SKILL.md |
