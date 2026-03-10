# Skills Subsystem

## Purpose

The writing-toolkit skills directory provides prose quality tools grounded in
established style references. The single skill — writing-clearly-and-concisely —
applies Strunk's *The Elements of Style* (1918) to any human-facing prose.

The key design decision: the reference text (~12k tokens) is loaded on demand,
not by default. Two usage modes (direct read vs. subagent dispatch) let the
skill operate under different context budgets.

## Core Mechanism

The skill routes to one of two modes based on available context. In direct mode,
the agent reads `references/elements-of-style.md` and applies rules inline. In
subagent mode, the agent drafts prose then dispatches a copyediting subagent
with the draft and reference file.

**Key files:**
- `writing-clearly-and-concisely/SKILL.md` — Skill definition with rule summary and mode routing
- `writing-clearly-and-concisely/references/elements-of-style.md` — Full Strunk reference (~12k tokens)

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name: writing-clearly-and-concisely` | Claude Code skill router | Unique, lowercase, matches directory name |
| Direct mode | Agents with sufficient context budget | Reads reference file, applies rules inline |
| Subagent mode | Agents under context pressure | Dispatches copyediting subagent with draft + reference |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | SKILL.md has valid YAML frontmatter with `name` and `description` | structural | Claude Code cannot discover the skill without frontmatter |
| INV-2 | `references/elements-of-style.md` must be loaded before applying Strunk's rules | reasoning-required | Applying rules from memory leads to inaccurate or incomplete editing; the reference is the source of truth |
| INV-3 | Skill name matches directory name (`writing-clearly-and-concisely`) | structural | Claude Code skill router requires name-directory alignment |

**Enforcement classification:**
- **structural** — enforced by test suite, directory convention, or pattern-matching
- **reasoning-required** — needs architectural understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not triggered | Missing or malformed YAML frontmatter | Add `---` fenced frontmatter with `name` and `description` |
| FAIL-2 | Editing quality inconsistent with Strunk | Reference file not loaded; rules applied from memory | Ensure reference file is read before editing |
| FAIL-3 | Context budget blown | Direct mode used when context is tight | Switch to subagent mode — draft first, dispatch copyeditor |
| FAIL-4 | Subagent returns unchanged prose | Subagent not given reference file | Pass both draft and `references/elements-of-style.md` to subagent |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Writing prose for humans with sufficient context | Direct mode: read reference, apply rules inline | INV-2 |
| Writing prose for humans under context pressure | Subagent mode: draft, dispatch copyeditor with reference | INV-2 |
| Editing existing prose | Load reference, then apply rules to existing text | INV-2 |
| Not writing prose (code, config, data) | Do not invoke this skill | — |

## Upstream Provenance

The reference file reproduces Strunk's 1918 public domain text faithfully.
The SKILL.md wrapper is original work. See `UPSTREAM-strunk.md` for full
provenance tracking, license compliance, and modification notes.

## Testing

**Traceability:** INV-1, INV-3: structural — enforced by frontmatter validation
and directory convention. INV-2: reasoning-required — verified during code
review and by checking subagent dispatch includes reference file.

Validate via manual invocation: trigger skill, verify reference file is loaded,
check edited prose against Strunk's rules.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| Claude Code subagent system | external | N/A — built into Claude Code runtime |
