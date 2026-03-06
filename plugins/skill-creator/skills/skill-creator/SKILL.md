---
name: skill-creator
description: "Use when users want to create a skill from scratch, update or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy."
---

# Skill Creator

## Overview

**Skill creation IS Test-Driven Development applied to process documentation.**

Write test cases (pressure scenarios), watch them fail (baseline behavior), write the skill, watch tests pass (agents comply), refactor (close loopholes). This skill combines Anthropic's eval tooling with TDD methodology.

**Two upstream references power this skill:**
- `references/upstream.md` — Anthropic's official skill-creator: eval workflows, benchmarking, description optimization, tooling scripts
- `references/writing-skills.md` — TDD methodology: the Iron Law, RED-GREEN-REFACTOR for documentation, CSO guidance, rationalization bulletproofing

Read each when directed below. This document synthesizes both into a unified workflow.

## The Iron Law

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

This applies to NEW skills AND EDITS to existing skills.

Write skill before testing? Delete it. Start over. No exceptions:
- Not for "simple additions"
- Not for "just adding a section"
- Not for "documentation updates"
- Don't keep untested changes as "reference"
- Delete means delete

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (use CLAUDE.md)
- Mechanical constraints enforceable with automation

**Skill types:**
- **Technique** — Concrete method with steps (condition-based-waiting, root-cause-tracing)
- **Pattern** — Way of thinking about problems (flatten-with-flags, test-invariants)
- **Reference** — API docs, syntax guides, tool documentation

## The Process

### 1. Capture Intent

Start by understanding what the skill should do. Read `references/upstream.md` § "Creating a skill" for the complete interview and research workflow. Key questions:
1. What should this skill enable Claude to do?
2. When should this skill trigger?
3. What's the expected output format?
4. What test cases will verify it works?

### 2. RED — Establish Baseline (Watch It Fail)

**Before writing any skill content**, run test scenarios WITHOUT the skill.

This is the TDD "write failing test first" step. You must see what agents naturally do before writing the skill.

**For discipline-enforcing skills** (TDD, verification requirements):
- Create pressure scenarios combining 3+ pressures (time + sunk cost + exhaustion)
- Run scenarios WITHOUT skill present
- Document exact choices and rationalizations verbatim
- Identify patterns in failures

**For technique/reference skills:**
- Run representative tasks WITHOUT skill
- Note where agents struggle, produce wrong output, or miss steps
- Document specific gaps and errors

**Detailed pressure testing methodology:** Read `writing-skills-refs/testing-skills-with-subagents.md`

**Using the eval system for baselines:** Read `references/upstream.md` § "Running and evaluating test cases" — the "baseline run" in the eval system IS the RED phase. When you spawn subagent runs, always include a `without_skill` baseline. This is not optional housekeeping — it's the failing test.

### 3. GREEN — Write Minimal Skill

Write skill addressing the specific failures you documented. Don't add content for hypothetical cases.

**Structure guidance:** Read `references/writing-skills.md` § "SKILL.md Structure" for frontmatter rules and document organization.

**CSO (Claude Search Optimization):** Read `references/writing-skills.md` § "Claude Search Optimization" for description best practices.

> **The description trap:** Testing revealed that when a description summarizes the skill's workflow, Claude follows the description instead of reading the full skill. Descriptions must contain ONLY triggering conditions, never workflow summaries.

Run same scenarios WITH skill. Agent should now comply / produce correct output.

### 4. Evaluate with Benchmarks

Read `references/upstream.md` § "Running and evaluating test cases" for the complete eval workflow:
- Spawn with-skill and baseline runs in parallel
- Draft quantitative assertions while runs execute
- Grade results, aggregate benchmarks
- Launch the eval viewer for human review

**The eval loop IS the TDD verify-GREEN step.** The viewer lets you and the user inspect whether the skill actually fixed the baseline failures.

### 5. REFACTOR — Close Loopholes

Read eval feedback. For each test case where the skill didn't help:
- Identify new rationalizations or failure modes
- Add explicit counters in the skill
- Build rationalization table (for discipline skills)
- Add red flags list

**Detailed rationalization bulletproofing:** Read `references/writing-skills.md` § "Bulletproofing Skills Against Rationalization"

**Psychology behind bulletproofing:** Read `writing-skills-refs/persuasion-principles.md` for research on authority, commitment, and scarcity principles (Cialdini, 2021; Meincke et al., 2025).

### 6. Iterate

Improve the skill, rerun all test cases into a new iteration directory. Read `references/upstream.md` § "Improving the skill" for guidance on:
- Generalizing from feedback (don't overfit to test cases)
- Keeping the prompt lean
- Explaining the why
- Looking for repeated work across test cases

**Keep going until:**
- User says they're happy
- Feedback is all empty
- No meaningful progress being made

### 7. Optimize Description

After the skill content is stable, optimize the description for triggering accuracy. Read `references/upstream.md` § "Description Optimization" for the full loop:
- Generate trigger eval queries (should-trigger and should-not-trigger)
- Review with user via HTML template
- Run optimization loop
- Apply best description

## TDD ↔ Eval Loop Mapping

This is the core synthesis — how TDD phases map to the eval system:

| TDD Phase | Eval System Equivalent | What You Do |
|-----------|----------------------|-------------|
| **RED** (write failing test) | Baseline run (`without_skill/`) | Spawn subagent on task without skill, document failures |
| **Verify RED** (watch it fail) | Review baseline outputs | Confirm agent produces wrong/incomplete output |
| **GREEN** (write minimal code) | Write SKILL.md | Address specific baseline failures, nothing more |
| **Verify GREEN** (watch it pass) | With-skill run + eval viewer | Spawn subagent with skill, review via `generate_review.py` |
| **REFACTOR** (improve) | Iteration loop | Read feedback, close loopholes, rerun into `iteration-N+1/` |
| **Stay GREEN** (regression) | Benchmark comparison | `aggregate_benchmark.py` confirms no regressions |

**The upstream iteration loop IS the TDD refactor cycle.** Each iteration is a RED-GREEN-REFACTOR pass. The eval viewer is your test runner. The benchmark is your test report.

## Skill Structure & CSO Quick Reference

**Frontmatter (YAML):**
- Only `name` and `description` fields (max 1024 chars total)
- `name`: letters, numbers, hyphens only (max 64 chars)
- `description`: starts with "Use when...", third person, triggering conditions ONLY

**Progressive disclosure:**
- Keep SKILL.md under 500 lines
- Put heavy reference in separate files
- One level deep (SKILL.md → reference, never reference → reference)

**Full guidance:** Read `references/writing-skills.md` § "SKILL.md Structure" and `references/upstream.md` § "Skill Writing Guide"

## Testing Different Skill Types

| Skill Type | Test Approach | Success Criteria |
|------------|--------------|------------------|
| **Discipline** (TDD, verification) | Pressure scenarios, 3+ pressures | Agent follows rule under maximum pressure |
| **Technique** (how-to guides) | Application + edge case scenarios | Agent applies technique correctly |
| **Pattern** (mental models) | Recognition + counter-example scenarios | Agent knows when/how to apply |
| **Reference** (docs/APIs) | Retrieval + application scenarios | Agent finds and uses info correctly |

**Full testing methodology:** Read `writing-skills-refs/testing-skills-with-subagents.md`

## Flowcharts

Use flowcharts ONLY for non-obvious decision points, not for linear instructions or reference material. See `writing-skills-refs/graphviz-conventions.dot` for style rules. Use `writing-skills-refs/render-graphs.js` to render to SVG.

## Tooling Reference

All scripts live in `scripts/` and are documented in `references/upstream.md`:
- `run_eval.py` — Run evaluation queries
- `run_loop.py` — Description optimization loop
- `aggregate_benchmark.py` — Aggregate benchmark results
- `generate_report.py` — Generate reports
- `improve_description.py` — Improve skill descriptions
- `package_skill.py` — Package skill as .skill file
- `quick_validate.py` — Quick validation

Subagent instructions in `agents/`:
- `grader.md` — Evaluate assertions against outputs
- `comparator.md` — Blind A/B comparison
- `analyzer.md` — Analyze benchmark results

Schemas in `references/schemas.md`.

## Common Rationalizations for Skipping Testing

| Excuse | Reality |
|--------|---------|
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. Test it. |
| "It's just a reference" | References can have gaps. Test retrieval. |
| "Testing is overkill" | Untested skills have issues. Always. |
| "I'll test if problems emerge" | Problems = agents can't use skill. Test BEFORE deploying. |
| "Too tedious to test" | Less tedious than debugging bad skill in production. |
| "Academic review is enough" | Reading ≠ using. Test application scenarios. |

**All of these mean: Test before deploying. No exceptions.**
