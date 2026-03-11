# Skills Subsystem

## Purpose

The thinking-toolkit skills directory provides three complementary cognitive
tools: divergent exploration (ideate), convergent analysis (first-principles),
and evaluative assessment (heilmeier-catechism). Together they cover the
"thinking before designing" phase of any project, producing structured artifacts
that feed into downstream design and planning skills.

The key design decision: ideate generates breadth (many ideas, minimal
structure), first-principles generates depth (few approaches, maximal rigor),
and heilmeier-catechism evaluates ambition (structured assessment of feasibility
and impact). They are independent entry points, never auto-chained.

## Core Mechanism

Each skill is a standalone SKILL.md with YAML frontmatter. Claude Code
discovers and loads skills by keyword matching against the `description` field.
All skills produce dated Markdown files as output artifacts.

**Key files:**
- `ideate/SKILL.md` — Divergent exploration, 4-step session (explore, generate, connect, capture)
- `first-principles/SKILL.md` — Convergent Socratic analysis, 6-phase process
- `heilmeier-catechism/SKILL.md` — Evaluative assessment, 6-phase H1→H2→Enablers pipeline

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name: ideate` | Claude Code skill router | Unique, lowercase, matches directory name |
| YAML frontmatter `name: first-principles` | Claude Code skill router | Unique, lowercase, matches directory name |
| YAML frontmatter `name: heilmeier-catechism` | Claude Code skill router | Unique, lowercase, matches directory name |
| Idea files `YYYY-MM-DD-{slug}-idea-{status}.md` | Downstream design/brainstorming skills | Status is raw, refined, or actionable |
| First-principles output `YYYY-MM-DD-{topic}-first-principles.md` | Downstream design/brainstorming skills | Contains problem, assumptions, fundamentals, approaches |
| Initiative briefs `YYYY-MM-DD-{slug}-initiative-brief.md` | Downstream brainstorming skill | Contains full catechism analysis with go/no-go recommendation |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | Every SKILL.md has valid YAML frontmatter with `name` and `description` | structural | Claude Code cannot discover skills without frontmatter |
| INV-2 | Idea files follow naming convention `YYYY-MM-DD-{slug}-idea-{status}.md` where status is raw/refined/actionable | reasoning-required | Downstream skills and humans rely on filename to determine idea maturity |
| INV-3 | First-principles Phase 3 classifies every assumption as Fundamental or Convention | reasoning-required | Skipping classification leads to rebuilding on unexamined assumptions |
| INV-4 | Phase 5 produces 2-3 radically different approaches, not incremental improvements | reasoning-required | Incremental approaches defeat the purpose; the whole method exists to escape convention |
| INV-5 | Skills reference each other by name, not file path | structural | Names are stable identifiers; paths may change |
| INV-6 | Heilmeier H1 must be stated without jargon and be quantitatively evaluable | reasoning-required | Vague H1 makes the entire pipeline unfalsifiable |
| INV-7 | H2 research must reference actual sources (papers, data, products), not speculation | reasoning-required | Unsourced H2 leads to uninformed enabler identification |
| INV-8 | Enablers must be classified as Critical, Accelerator, or Wild Card | reasoning-required | Unclassified enablers prevent prioritization and risk assessment |
| INV-9 | Initiative brief must include kill criteria (conditions for stopping) | reasoning-required | Without kill criteria, failing initiatives persist indefinitely |

**Enforcement classification:**
- **structural** — enforced by test suite, directory convention, or pattern-matching
- **reasoning-required** — needs architectural understanding; verified during code review

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not triggered | Missing or malformed YAML frontmatter | Add `---` fenced frontmatter with `name` and `description` |
| FAIL-2 | Idea files unrecognizable by downstream tools | Wrong naming convention or missing status | Follow `YYYY-MM-DD-{slug}-idea-{status}.md` exactly |
| FAIL-3 | First-principles analysis produces incremental solutions | Skipped Phase 3 assumption classification or kept conventions | Re-run Phase 3; strip all conventions before Phase 5 |
| FAIL-4 | Analysis stalls at Phase 2 | Problem not clearly defined in Phase 1 | Return to Phase 1; stay until problem is crystal clear |
| FAIL-5 | Ideation session produces design decisions | Scope creep into brainstorming territory | Ideate captures ideas only; hand off to design skill explicitly |
| FAIL-6 | H1 accepted despite being vague | Insufficient pushback during Phase 1 | Return to Phase 1; apply validation criteria until quantifiable |
| FAIL-7 | H2 analysis is speculation without sources | Skipped web research or relied on model knowledge | Require web search; cite actual papers, data, products |
| FAIL-8 | Phase 5 stress testing skipped | Assumed initiative is "obviously" feasible | Always run at minimum gap waterfall and go/no-go matrix |
| FAIL-9 | Catechism treated as one-pass checklist | No iteration between phases | Revisit earlier phases when later phases reveal gaps |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| Problem space is fuzzy, multiple directions exist | Use ideate for divergent exploration | INV-2 |
| Conventional solution feels wrong or cargo-cult | Use first-principles for convergent analysis | INV-3, INV-4 |
| Assumption seems obviously true | Question it hardest; classify as Fundamental or Convention | INV-3 |
| Phase 5 produces only one approach | Generate more; must produce 2-3 radically different options | INV-4 |
| User wants to design after ideation | Hand off manually to brainstorming skill; do not auto-chain | INV-5 |
| Ambitious idea needs structured evaluation | Use heilmeier-catechism for evaluative assessment | INV-6, INV-7 |
| Enabler maturity unclear | Assess TRL/AD2 using assessment-frameworks reference | INV-8 |
| Initiative brief lacks stopping conditions | Add kill criteria before finalizing | INV-9 |

## Testing

**Traceability:** INV-1, INV-5: structural — enforced by frontmatter validation
and directory convention. INV-2, INV-3, INV-4: reasoning-required — verified
during code review and subagent pressure testing. INV-6, INV-7, INV-8, INV-9:
reasoning-required — verified during code review. FAIL-8 partially structural:
can verify Phase 5 section exists in output.

Validate via manual invocation: trigger each skill, verify output format matches
contract, check that first-principles produces assumption classification and
multiple radical approaches.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| Downstream design/brainstorming skills | external | Consumers of idea and analysis artifacts |
| heilmeier-catechism references | internal | 5 reference docs in heilmeier-catechism/references/ |
