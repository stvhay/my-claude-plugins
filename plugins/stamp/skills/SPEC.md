# Skills Subsystem — STAMP Analysis

## Purpose

The stamp plugin provides STAMP-based systems-theoretic analysis through a
hub-and-spoke architecture. The hub (stamp-base) routes to one of three spokes
based on the analysis context: prospective hazard analysis (STPA), security
analysis (STPA-Sec), or retrospective incident investigation (CAST). All skills
share a control-theoretic paradigm that rejects "human error" as root cause and
models accidents as inadequate control rather than component failure.

## Core Mechanism

stamp-base acts as a routing hub using a decision diamond:

> "Has a loss already occurred?" → stamp-cast
> "Is there an adversarial threat?" → stamp-stpa-sec
> Otherwise → stamp-stpa

Spokes support bidirectional handoffs when the framing changes mid-analysis
(e.g., a prospective STPA reveals a security concern → hand off to STPA-Sec).

**Key files:**
- `stamp-base/SKILL.md` — Routing hub with decision diamond and shared foundations
- `stamp-stpa/SKILL.md` — Prospective hazard analysis with agentic checkpoints
- `stamp-stpa-sec/SKILL.md` — Security extension with STRIDE integration
- `stamp-cast/SKILL.md` — Retrospective incident investigation (5-step process)
- `UPSTREAM-stamp-framework.md` — Provenance tracking for MIT STAMP framework

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name` | Claude Code skill router | Must be unique, lowercase, hyphenated |
| Decision diamond routing | stamp-base → spokes | Three-branch: CAST / STPA-Sec / STPA |
| Bidirectional handoffs | Between spokes | Context preserved across methodology switch |
| depict notation diagrams | All control structure outputs | Consistent diagram format across all skills |
| @red path highlighting | All flawed-path annotations | Marks inadequate control in diagrams |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | Every SKILL.md has valid YAML frontmatter (`name` + `description`) | structural | Claude Code cannot discover or load skills without frontmatter |
| INV-2 | stamp-base routes correctly via decision diamond (loss → CAST, adversarial → STPA-Sec, else → STPA) | reasoning-required | Wrong methodology produces misleading results; prospective analysis on a past incident misses systemic causes |
| INV-3 | No analysis produces "human error" or "operator error" as root cause | reasoning-required | STAMP's core premise: accidents result from inadequate control, not individual failure |
| INV-4 | All control structure diagrams use depict notation | reasoning-required | Consistent notation enables diagram reuse and cross-skill comparison |
| INV-5 | CAST never assigns blame to individuals | reasoning-required | Blame-oriented findings prevent systemic learning and violate STAMP theory |
| INV-6 | Skills reference each other by name, not file path | structural | Skill directories may move; names are the stable identifier |

**Enforcement classification:**
- **structural** — enforced by test suite or directory convention; pattern-matchable
- **reasoning-required** — needs domain understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Wrong methodology selected | Ambiguous framing (e.g., near-miss that could be prospective or retrospective) | Re-evaluate decision diamond criteria; clarify whether a loss has occurred |
| FAIL-2 | Incomplete control structure | Missed control layers (e.g., regulatory, organizational) | Walk hierarchy top-down: society → regulator → company → management → operations → equipment |
| FAIL-3 | STPA-Sec misses attack vectors | Trust boundaries not identified in control structure | Explicitly map trust boundaries before enumerating threats; cross-check with STRIDE |
| FAIL-4 | CAST produces blame-oriented findings | Analysis focused on individual actions instead of systemic factors | Reframe every finding as a control deficiency; apply INV-3 and INV-5 |
| FAIL-5 | Handoff between spokes loses context | Framing change triggers methodology switch without preserving prior work | Carry forward control structure and identified hazards/losses into the new spoke |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| New analysis request arrives | Route through stamp-base decision diamond | INV-2 |
| Analysis reveals adversarial dimension mid-STPA | Hand off to stamp-stpa-sec with current control structure | INV-2, FAIL-5 |
| Retrospective analysis tempted to cite "human error" | Reframe as control deficiency; identify what controls were inadequate | INV-3, INV-5 |
| Drawing control structure diagram | Use depict notation with @red for flawed paths | INV-4 |
| One skill needs to invoke another | Reference by skill name (e.g., stamp-cast), never by file path | INV-6 |

## Testing

**Traceability:** INV-1, INV-6: enforced by `tests/validate-frontmatter.sh`.
INV-2, INV-3, INV-4, INV-5: reasoning-required — verified during code review
and through agentic checkpoint prompts embedded in each spoke's SKILL.md.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| MIT STAMP framework | external | N/A — academic framework, tracked in UPSTREAM-stamp-framework.md |
| depict notation | external | N/A — diagram notation convention |
