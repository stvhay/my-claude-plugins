# Skills Subsystem

## Purpose

The redteam skills directory provides adversarial analysis through massive
parallel agent deployment. The single skill — redteam — breaks arguments into
atomic claims, attacks from multiple expert perspectives, and produces both a
steelman (strongest version of the argument) and a counter-argument (strongest
rebuttal).

The key design decision: decompose first, then parallelize. Breaking content
into 24 atomic claims before dispatching 32 agents ensures comprehensive
coverage — no aspect of the argument escapes scrutiny.

## Core Mechanism

Two workflows serve different goals. ParallelAnalysis stress-tests existing
content through the five-phase protocol (decompose, analyze in parallel,
synthesize, steelman, counter-argue). AdversarialValidation produces new content
by having competing agents propose and attack solutions.

**Key files:**
- `redteam/SKILL.md` — Workflow routing and five-phase protocol overview
- `redteam/references/Philosophy.md` — Core philosophy, success criteria, agent types
- `redteam/references/Integration.md` — Skill integration and output format
- `redteam/references/ParallelAnalysis.md` — Stress-test workflow details
- `redteam/references/AdversarialValidation.md` — Competition workflow details

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name: redteam` | Claude Code skill router | Unique, lowercase, matches directory name |
| ParallelAnalysis workflow | Users stress-testing existing content | Produces steelman + counter-argument (8 points each) |
| AdversarialValidation workflow | Users producing content via competition | Produces synthesized solution from competing proposals |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | SKILL.md has valid YAML frontmatter with `name` and `description` | structural | Claude Code cannot discover the skill without frontmatter |
| INV-2 | ParallelAnalysis output includes BOTH steelman AND counter-argument | reasoning-required | Omitting either side produces biased analysis; the value is in the tension between them |
| INV-3 | Content is decomposed into atomic claims before parallel analysis | reasoning-required | Analyzing monolithic arguments misses specific weaknesses; atomic decomposition ensures nothing hides in vague generalities |
| INV-4 | Skill name matches directory name (`redteam`) | structural | Claude Code skill router requires name-directory alignment |

**Enforcement classification:**
- **structural** — enforced by test suite, directory convention, or pattern-matching
- **reasoning-required** — needs architectural understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not triggered | Missing or malformed YAML frontmatter | Add `---` fenced frontmatter with `name` and `description` |
| FAIL-2 | Analysis misses obvious weaknesses | Skipped decomposition phase; analyzed argument as monolith | Decompose into 24 atomic claims first, then dispatch agents |
| FAIL-3 | Output feels one-sided | Counter-argument or steelman missing | Ensure both are present; steelman without counter (or vice versa) is incomplete |
| FAIL-4 | Collaborative debate requested but routed to redteam | Council confused with redteam | Route collaborative-adversarial debate to council skill |
| FAIL-5 | Agents produce shallow criticism | Too few perspectives or superficial decomposition | Verify 32 agents deployed with diverse expert types (engineers, architects, pentesters, interns) |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Stress-test an existing proposal or argument | Use ParallelAnalysis workflow | INV-2, INV-3 |
| Produce new content through competition | Use AdversarialValidation workflow | — |
| Need collaborative debate, not pure attack | Route to council skill instead | — |
| Output has steelman but no counter-argument | Incomplete — re-run or complete Phase 5 | INV-2 |
| Analysis seems to miss obvious flaws | Check decomposition — likely skipped or too coarse | INV-3 |

## Testing

**Traceability:** INV-1, INV-4: structural — enforced by frontmatter validation
and directory convention. INV-2, INV-3: reasoning-required — verified during
code review and subagent pressure testing.

Validate via manual invocation: trigger ParallelAnalysis, verify output contains
both steelman and counter-argument sections. Check that decomposition phase
produces atomic claims before analysis begins.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| Claude Code subagent system | external | N/A — built into Claude Code runtime |
| council skill | external | `plugins/multi-agent-toolkit/skills/SPEC.md` |
| research skill | external | `plugins/multi-agent-toolkit/skills/SPEC.md` |
