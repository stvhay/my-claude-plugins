# Skills Subsystem

## Purpose

The multi-agent-toolkit skills directory provides two parallel-agent
coordination patterns: structured debate (council) and information gathering
(research). Both deploy multiple agents simultaneously to compress wall-clock
time while producing richer results than single-agent approaches.

The key design decision: agents run in parallel within rounds/tiers but
sequentially between them. This preserves the ability for later rounds to
respond to earlier findings while maximizing throughput within each round.

## Core Mechanism

Council dispatches specialized debate agents in rounds — parallel within each
round, sequential between rounds so agents can respond to each other's points.
Research dispatches information-gathering agents at configurable scale (1, 2, or
9 parallel agents) with mandatory URL verification before delivery.

**Key files:**
- `council/SKILL.md` — Collaborative-adversarial debate routing (DEBATE or QUICK)
- `council/references/CouncilMembers.md` — Agent roles and perspectives
- `council/references/RoundStructure.md` — Three-round debate structure
- `council/references/OutputFormat.md` — Transcript format templates
- `research/SKILL.md` — Parallel research routing (Quick, Standard, Extensive)
- `research/references/UrlVerificationProtocol.md` — Mandatory URL verification
- `research/references/QuickReference.md` — Mode comparison table

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name: council` | Claude Code skill router | Unique, lowercase, matches directory name |
| YAML frontmatter `name: research` | Claude Code skill router | Unique, lowercase, matches directory name |
| DEBATE workflow | Users needing full 3-round discussion | Produces complete transcript + synthesis |
| QUICK workflow | Users needing fast perspective check | Produces 1-round initial positions |
| Research tiers (Quick/Standard/Extensive) | Users needing information | Produces verified research with source URLs |
| Research output files | Downstream skills | Written to `.claude/research/` |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | Every SKILL.md has valid YAML frontmatter with `name` and `description` | structural | Claude Code cannot discover skills without frontmatter |
| INV-2 | Every URL in research output must be verified before delivery | reasoning-required | Research agents hallucinate URLs; a single broken link is a catastrophic credibility failure |
| INV-3 | Council rounds execute parallel within, sequential between | reasoning-required | Later rounds must respond to earlier points; breaking sequence removes the "debate" from debate |
| INV-4 | Due diligence / background check requests route to osint skill, not research | reasoning-required | Research is for information gathering; due diligence requires osint methodology and different legal/ethical considerations |
| INV-5 | Skills reference each other by name, not file path | structural | Names are stable identifiers; paths may change |

**Enforcement classification:**
- **structural** — enforced by test suite, directory convention, or pattern-matching
- **reasoning-required** — needs architectural understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not triggered | Missing or malformed YAML frontmatter | Add `---` fenced frontmatter with `name` and `description` |
| FAIL-2 | Broken URLs in research output | URL verification skipped | Apply `references/UrlVerificationProtocol.md` to every URL before delivery |
| FAIL-3 | Council debate produces no new insights in later rounds | Rounds run in parallel instead of sequentially | Ensure round N+1 receives round N transcript as input |
| FAIL-4 | Due diligence request handled as casual research | Routing logic missed due-diligence keywords | Check for due diligence, background check, vetting triggers; route to osint |
| FAIL-5 | Research takes too long for simple question | Wrong tier selected | Use Quick (1 agent) for simple questions; Standard is the default |
| FAIL-6 | Council used for pure adversarial attack | Council confused with redteam | Route pure adversarial analysis to redteam skill |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Need multiple perspectives on a decision | Use council DEBATE (3 rounds) | INV-3 |
| Quick sanity check on an idea | Use council QUICK (1 round) | INV-3 |
| Need to gather information on a topic | Use research at appropriate tier | INV-2 |
| Due diligence or background check requested | Route to osint skill, not research | INV-4 |
| Research output contains URLs | Verify every URL before including in output | INV-2 |
| Want to stress-test an idea adversarially | Use redteam skill, not council | INV-5 |

## Testing

**Traceability:** INV-1, INV-5: structural — enforced by frontmatter validation
and directory convention. INV-2, INV-3, INV-4: reasoning-required — verified
during code review and subagent pressure testing.

Validate via manual invocation: trigger council, verify rounds are sequential
with visible transcript. Trigger research, verify all output URLs resolve.
Test due-diligence routing by requesting background checks.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| Claude Code subagent system | external | N/A — built into Claude Code runtime |
| WebSearch, WebFetch tools | external | N/A — built into Claude Code runtime |
| redteam skill | external | `plugins/redteam/skills/SPEC.md` |
| osint skill | external | N/A — separate plugin |
