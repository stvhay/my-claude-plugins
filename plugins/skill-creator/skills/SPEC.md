# Skills Subsystem — skill-creator

## Purpose

Provides a single skill (`skill-creator`) that combines Anthropic's official
eval tooling with TDD philosophy to create, test, and refine agent skills.
The Iron Law: no skill without a failing test first. TDD RED-GREEN-REFACTOR
maps directly to eval runs — baseline without skill (RED), with-skill run
(GREEN), iterative improvement guided by eval results (REFACTOR).

## Core Mechanism

The skill synthesizes two upstream sources into a seven-step workflow:
capture intent, establish baseline (RED), write minimal skill (GREEN),
evaluate with benchmarks, refactor to close loopholes, iterate, optimize
description. Three skill types (Technique, Pattern, Reference) each have
distinct testing approaches and success criteria.

**Key files:**
- `skill-creator/SKILL.md` — Entry point: unified TDD + eval workflow
- `skill-creator/UPSTREAM.md` — Provenance tracking for both upstream sources
- `skill-creator/scripts/` — 7 eval scripts (run_eval, run_loop, aggregate_benchmark, generate_report, improve_description, package_skill, quick_validate)
- `skill-creator/agents/` — 3 subagent instructions (grader, comparator, analyzer)
- `skill-creator/eval-viewer/` — HTML viewer for eval result review
- `skill-creator/references/` — Upstream snapshots (upstream.md, writing-skills.md, schemas.md)
- `skill-creator/writing-skills-refs/` — Supplementary materials from obra/superpowers

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name: skill-creator` | Claude Code skill router | Stable identifier for invocation |
| YAML frontmatter `description` | Claude Code keyword matcher | Triggers on: create skill, run evals, benchmark, optimize description |
| `/skill-creator` invocation | Users and other skills | Seven-step TDD workflow |
| `scripts/*.py` | SKILL.md workflow steps | Called during eval runs and benchmarking |
| `agents/*.md` | Eval scripts (subagent spawning) | Grading, comparison, analysis instructions |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | SKILL.md has valid YAML frontmatter with `name` and `description` | Structural — `quick_validate.py` checks format | Claude Code cannot discover or load the skill without frontmatter |
| INV-2 | No skill created without failing baseline test first (Iron Law) | Reasoning — SKILL.md explicitly mandates delete-and-restart for violations | Without a baseline, you cannot prove the skill improves anything; untested skills accumulate silently broken process docs |
| INV-3 | Eval results must show improvement over baseline before declaring GREEN | Reasoning — workflow requires with-skill vs baseline comparison via eval viewer | A skill that doesn't measurably improve over no-skill is noise; passing this gate is what makes TDD meaningful |
| INV-4 | Upstream sources tracked in UPSTREAM.md with sync process | Structural — UPSTREAM.md documents commit SHAs, diff commands, and sync steps | Without provenance tracking, upstream syncs clobber local customizations or silently diverge |
| INV-5 | Skills reference each other by name, not file path | Structural — SKILL.md cross-references use `/skill-name` form | Directories may move; names are stable identifiers across sessions |

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill appears to work but doesn't improve eval scores | No baseline run performed — skipped the RED phase | Delete the skill, run baseline first, then rewrite addressing documented failures |
| FAIL-2 | Skill passes evals but fails in real use | Eval cases too narrow or synthetic; don't cover real-world pressure | Add diverse pressure scenarios (3+ pressures); test with realistic tasks |
| FAIL-3 | Upstream sync clobbers local customizations | UPSTREAM.md not checked before syncing; diff steps skipped | Follow sync process in UPSTREAM.md — diff before copying, note divergences |
| FAIL-4 | Skill description doesn't trigger correctly | Description contains workflow summary instead of triggering conditions | Optimize description using step 7; description must contain ONLY "Use when..." conditions |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Creating a new skill | Run baseline eval WITHOUT skill first; document failures | INV-2 |
| Editing an existing skill | Run baseline on current version, then edit, then re-eval | INV-2, INV-3 |
| Skill passes some evals but not others | Refactor to close loopholes; add pressure scenarios | INV-3 |
| Upstream released a new version | Follow UPSTREAM.md sync process; diff before overwriting | INV-4 |
| Skill works but doesn't auto-trigger | Optimize description (step 7); keep "Use when..." format | INV-1 |
| Choosing skill type (Technique/Pattern/Reference) | Match type to content; each has different test approach | INV-2 |

## Testing

Smoke test at `skill-creator/tests/smoke_test.sh` validates structural
requirements. Functional testing uses the eval system itself — the skill's
own TDD methodology is applied to test the skill. Each eval run produces
graded results viewable via `eval-viewer/`.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Anthropic official skill-creator | external | N/A — tracked in UPSTREAM.md (Apache 2.0, commit SHA) |
| obra/superpowers writing-skills | external | N/A — tracked in UPSTREAM.md (MIT, commit SHA) |
| Claude Code eval tooling | external | N/A — built into Claude Code runtime |
