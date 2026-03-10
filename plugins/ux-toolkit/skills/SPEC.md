# Skills Subsystem

## Purpose

The ux-toolkit skills directory provides UX design expertise for agentic systems.
Skills cover the full spectrum from visual GUI design to agentic interaction
patterns — approval flows, failure handling, trust communication, and delegation
boundaries. The orchestrator skill (ux-design-agent) performs requirements
archaeology, user modeling, and modality selection before routing to specialists.

> Key design decision: ux-design-agent always completes discovery before handing
> off. GUI work routes to design-principles; agentic work routes to
> delegation-oversight. trust-calibration and ux-writing are cross-cutting
> technique skills available to all others.

## Core Mechanism

The ux-design-agent orchestrator runs three phases — requirements archaeology,
user modeling, modality selection — then delegates to the appropriate specialist.
Routing is modality-driven: GUI contexts invoke design-principles (which enforces
direction selection before any design work); agentic contexts invoke
delegation-oversight (checkpoint design, escalation triggers, autonomy gradients).

Two technique skills cut across all specialists:
- **trust-calibration** — five-level confidence communication framework
- **ux-writing** — interface copy with tone adaptation by user state

**Key files:**
- `ux-design-agent/SKILL.md` — Orchestrator entry point (three-phase discovery + routing)
- `design-principles/SKILL.md` — GUI design (9 personality directions, 4px grid, Phosphor Icons)
- `delegation-oversight/SKILL.md` — Agentic interaction patterns
- `approval-confirmation/SKILL.md` — Pre-action preview and stakes communication
- `failure-choreography/SKILL.md` — Graceful failure with state preservation
- `trust-calibration/SKILL.md` — Five-level confidence framework
- `ux-writing/SKILL.md` — Tone-adaptive interface copy

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name` | Claude Code skill router | Must be unique, lowercase, hyphenated |
| YAML frontmatter `description` | Claude Code keyword matcher | Must contain trigger keywords |
| `/ux-design-agent` invocation | Users starting UX work | Entry point; runs discovery then routes |
| Cross-skill references | Skills referencing each other | Use skill name, not file path |
| Orchestrator routing | ux-design-agent → specialists | GUI → design-principles, Agentic → delegation-oversight |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | Every skill directory contains exactly one `SKILL.md` with valid YAML frontmatter (`name` + `description`) | structural | Claude Code cannot discover or load skills without frontmatter |
| INV-2 | design-principles requires direction selection before any design work begins | reasoning-required | Without a chosen direction, design output lacks visual coherence and personality consistency |
| INV-3 | ux-design-agent completes all three phases (requirements archaeology, user modeling, modality selection) before handing off to a specialist | reasoning-required | Skipping phases produces designs mismatched to users or context |
| INV-4 | trust-calibration uses exactly five defined confidence levels, never ad-hoc language | reasoning-required | Ad-hoc confidence wording erodes user trust — consistent levels build calibrated expectations |
| INV-5 | failure-choreography preserves state and provides recovery options on every failure path | reasoning-required | Failures without state preservation force users to start over; failures without recovery options strand users |
| INV-6 | Skills reference each other by name, not file path | structural | Skill directories may move; names are the stable identifier |

**Enforcement classification:**
- **structural** — enforced by test suite or directory convention; pattern-matchable
- **reasoning-required** — needs architectural understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Design output lacks visual coherence | design-principles invoked without direction selection (INV-2 violated) | Ensure direction selection step completes before any layout or component work |
| FAIL-2 | Agentic system asks user too often or acts without needed confirmation | Autonomy gradients miscalibrated in delegation-oversight | Review checkpoint triggers; adjust escalation thresholds per stakes level |
| FAIL-3 | Users rubber-stamp approval dialogs without reading them | approval-confirmation fails to communicate stakes and consequences | Add consequence visualization; differentiate high-stakes from routine approvals |
| FAIL-4 | Agent confidence feels unreliable to users | Ad-hoc confidence language instead of trust-calibration's five levels (INV-4 violated) | Route all confidence communication through trust-calibration skill |
| FAIL-5 | Interface copy tone inconsistent across features | ux-writing skill not invoked by specialist skills | Add ux-writing to specialist skill integration sections |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Starting any UX design task | Enter through ux-design-agent; complete all three discovery phases before specialist handoff | INV-3 |
| GUI design context identified | Route to design-principles; require direction selection first | INV-2 |
| Agentic interaction context identified | Route to delegation-oversight for checkpoint and escalation design | INV-3 |
| Communicating confidence or uncertainty | Use trust-calibration's five-level framework, not free-form language | INV-4 |
| Handling a failure or error state | Invoke failure-choreography; ensure state preservation and recovery options | INV-5 |
| Writing any user-facing text | Invoke ux-writing for tone adaptation by user state | INV-6 |

## Testing

**Traceability:** INV-1, INV-6: structural — enforced by frontmatter validation
tests and cross-reference checks. INV-2, INV-3, INV-4, INV-5: reasoning-required
— verified during code review by checking that orchestrator phases complete and
specialist preconditions are met.

Skills are validated by reviewing orchestrator routing logic against the modality
decision framework and confirming technique skills are referenced in specialist
integration sections.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| brainstorming (dev-workflow-toolkit) | external | `plugins/dev-workflow-toolkit/skills/SPEC.md` |
| Phosphor Icons | external | N/A — icon library used by design-principles |
