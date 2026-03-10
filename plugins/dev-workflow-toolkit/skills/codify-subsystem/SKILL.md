---
name: codify-subsystem
description: Use when a subsystem directory needs a SPEC.md — analyzes code, interviews the developer about invariants and failure modes, and produces a machine-readable specification
---

# Codify Subsystem

## Overview

Create or update a SPEC.md for a subsystem directory. Analyzes the code,
interviews the developer about purpose, invariants, and failure modes,
then produces a specification that agents load when working on that subsystem.

**Announce at start:** "I'm using the codify-subsystem skill to create a specification for [directory]."

## When to Use

- A directory has 3+ source files and no SPEC.md
- A new feature directory is created
- An agent encounters a subsystem it doesn't understand
- After significant refactoring that changes a subsystem's invariants
- During onboarding to document existing subsystems

## Checklist

You MUST complete these steps in order:

1. **Identify target directory** — confirm with user which directory to codify
2. **Analyze code** — read all files, identify patterns, entry points, exports
3. **Draft initial spec** — produce a first draft from code analysis alone
4. **Interview developer** — ask about invariants, failure modes, and testing (one question at a time)
5. **Finalize SPEC.md** — incorporate interview answers into the spec
6. **Update subsystem map** — add entry to CLAUDE.md's Subsystem Map table
7. **Update MANIFEST.md** — create `docs/specs/MANIFEST.md` if missing, then add entry

## The Process

### Step 1: Identify Target

Ask the user which directory to codify, or accept the path they provided.
Confirm the directory exists and list its files.

### Step 1b: Check for Parent SPEC.md

Before drafting, walk up the directory tree from the target to check for an
existing SPEC.md that may already cover this subsystem.

```bash
dir="<target-directory>"
while [ "$dir" != "." ] && [ "$dir" != "/" ]; do
    if [ -f "$dir/SPEC.md" ]; then
        echo "Found SPEC.md at $dir/SPEC.md"
        break
    fi
    dir=$(dirname "$dir")
done
```

If a parent SPEC.md is found, ask: "A SPEC.md already exists at `<path>`. Should
this subsystem get its own SPEC.md, or should it be documented in the parent?"

If the user chooses the parent, update the parent SPEC.md instead and skip to
Step 6 (Update Subsystem Map).

### Step 2: Analyze Code

Read all source files in the directory. Identify:
- Entry points and public API
- Internal data flow
- Dependencies (imports, external calls)
- Existing tests and their coverage
- Patterns and conventions used

### Step 3: Draft Initial Spec

Draft a SPEC.md from what the code analysis reveals using the following template.
Mark sections where you're uncertain with `[NEEDS INPUT]`.

**SPEC.md Template:**

````markdown
# [Subsystem Name]

## Purpose

[One paragraph: what this subsystem does and why it exists. Include the
problem it solves and the key design decision that shaped it.]

## Core Mechanism

[2-3 sentences on the key design decisions that shaped this subsystem — *why*
it works this way, not *what* it does (the code already shows that). Include
the mental model an agent needs to modify this code correctly.]

**Key files:**
- `path/to/entry-point.py` — [role]
- `path/to/core-logic.py` — [role]

## Public Interface

[What other subsystems depend on. Exports, APIs, events, shared types.
An agent modifying this subsystem must not break these contracts.]

| Export | Used By | Contract |
|---|---|---|
| | | |

## Invariants

[Things that must ALWAYS be true. These are the correctness pillars — an agent
that violates any of these has introduced a bug. Each invariant gets an ID for
test traceability.]

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | | structural / reasoning-required | |

**Enforcement classification:**
- **structural** — enforced by type system, API design, or code structure; pattern-matchable and universally respected
- **reasoning-required** — needs architectural understanding; model-tier dependent

Prioritize converting reasoning-required invariants to structural via API design.

## Failure Modes

[Known ways this subsystem breaks and how to fix them. An agent encountering
these symptoms should try the fix before investigating further. Each failure
mode gets an ID for test traceability.]

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | | | |

## Decision Framework

[Situation-keyed recipes for reasoning-required invariants. Converts declarative
rules into procedural guidance for agents that can follow patterns but cannot
infer architectural constraints. One entry per reasoning-required invariant.]

| Situation | Action | Invariant |
|---|---|---|
| | | INV-N |

## Testing

**Traceability:** Test names encode the spec item ID (`test_invN_description`,
`test_failN_description`). Items verified by other means should be noted here
(e.g., "INV-1, INV-5: enforced by `tsc --noEmit`", "FAIL-2: operational —
not unit-testable"). See CLAUDE.md Testing Convention.

## Dependencies

[What this subsystem depends on — other subsystems, external services,
libraries. An agent working here should load these SPEC.md files too if
making changes that cross boundaries.]

| Dependency | Type | SPEC.md Path |
|---|---|---|
| | internal/external | |
````

Present the draft to the developer.

### Step 4: Interview Developer

Ask about each `[NEEDS INPUT]` section plus these critical areas, one question
at a time:

**Invariants:** "What must ALWAYS be true about this subsystem? What rules, if
broken, would cause bugs?" (Examples: "order of operations matters", "this
value is never null after init", "these two fields must stay in sync")

**Failure modes:** "What are the known ways this breaks? What symptoms have you
seen, and what caused them?"

**Testing:** "How do you verify this subsystem works? What's the exact command?
Any special setup needed?"

**Test mapping:** "Are there existing tests for this subsystem? If so, which
tests verify which invariants or failure modes?" (This informs the inline
`# Tests INV-N` comments to add on test function declaration lines.)

**Enforcement:** "Which invariants are enforced structurally (type system, API
design, code structure) vs require architectural reasoning to follow?" (This
populates the Enforcement column: `structural` or `reasoning-required`.)

**Decision framework:** "For reasoning-required invariants, what's the
situation-action recipe an agent should follow?" (e.g., "Need DB writes? →
Submit IndexJob to queue." Populates the Decision Framework table.)

**Non-runtime verification:** "Are any spec items verified by non-runtime means
(e.g., type checker, code review, operational monitoring)?" (These get recorded
in the Testing section so verification gaps aren't rediscovered every session.)

**Purpose:** "Anything about *why* this subsystem exists that isn't obvious from
the code?" (Sometimes the code shows *what* but not *why* — design decisions,
alternatives considered, constraints from external systems.)

### Step 5: Finalize SPEC.md

Incorporate all answers. Write the final SPEC.md to the target directory.

**Inline test comments:** For each spec item (INV-N, FAIL-N) that has a
corresponding test, add a `# Tests INV-N` or `# Tests FAIL-N` inline comment
on the test function's declaration line. Use the naming convention
`test_invN_description` for invariant tests and `test_failN_description` for
failure mode tests. Flag any spec items that lack corresponding tests — these
need tests written. For items verified by non-runtime means (type checker,
code review, operational monitoring) or items with no coverage yet, record
them in the SPEC.md's Testing section rather than just flagging ephemerally.

**Existing non-conforming tests:** If the subsystem already has tests that
cover spec items but use different naming, add the inline comment to those
tests as-is (e.g., `def test_checkout_rejects_expired():  # Tests FAIL-2`).
Note the current name and the recommended rename. Do not require renaming
before the spec ships — the inline comment documents what exists, and renaming
can happen incrementally.

**Size check:** If the spec exceeds 400 lines, suggest splitting the subsystem
or summarizing verbose sections.

### Step 6: Update Subsystem Map

Add an entry to the `### Subsystem Map` table in `CLAUDE.md`:

```markdown
| [Subsystem Name] | [path/to/directory] | [One-line purpose] |
```

### Step 7: Update Manifest

If `docs/specs/MANIFEST.md` does not exist, create it:

```markdown
# Subsystem Specifications

## Index

| Subsystem | SPEC.md Path | Summary |
|-----------|-------------|---------|
```

Then add an entry to the `## Index` table:

```markdown
| [Subsystem Name] | [path/to/SPEC.md] | [One-line summary] |
```

If the spec covers cross-cutting concerns, add a `## Cross-Cutting Concerns`
section (or append to it if it exists).

## Key Principles

- **One question at a time** — don't overwhelm the developer
- **Code analysis first** — draft from code before asking questions
- **Invariants are the most important section** — push for specifics
- **80-350 lines** — under 80 means missing detail, over 350 means split
- **Machine-readable format** — consistent sections, tables for structured data
- **Commit the SPEC.md** — specs are load-bearing artifacts, version-controlled

## Integration

**Related skills:**
- **brainstorming** — may recommend codify-subsystem when subsystem boundaries are identified
- **writing-plans** — loads SPEC.md into task context
- **subagent-driven-development** — prepends SPEC.md context when dispatching implementer subagents
- **executing-plans** — loads nearest SPEC.md before executing each task
- **verification-before-completion** — checks SPEC.md invariants after verification
