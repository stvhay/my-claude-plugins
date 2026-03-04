# Subsystem Specification Template

> Copy this template into a subsystem directory as `SPEC.md` and fill in each
> section. Use `/codify-subsystem` to create one interactively.

## Target Size

100-400 lines. Under 100 means missing invariants or failure modes. Over 400
means the subsystem should be split.

---

# [Subsystem Name]

## Purpose

[One paragraph: what this subsystem does and why it exists. Include the
problem it solves and the key design decision that shaped it.]

## Core Mechanism

[How it works — the mental model an agent needs to modify this code correctly.
Include key algorithms, data flows, and architectural decisions. Reference
specific files and functions by path.]

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
that violates any of these has introduced a bug.]

| Invariant | Why It Matters |
|---|---|
| | |

## Failure Modes

[Known ways this subsystem breaks and how to fix them. An agent encountering
these symptoms should try the fix before investigating further.]

| Symptom | Cause | Fix |
|---|---|---|
| | | |

## Testing

[How to run tests for this subsystem. Include the exact command, any required
fixtures or environment setup, and the mocking strategy.]

```bash
# Run subsystem tests
[exact command here]
```

## Dependencies

[What this subsystem depends on — other subsystems, external services,
libraries. An agent working here should load these SPEC.md files too if
making changes that cross boundaries.]

| Dependency | Type | SPEC.md Path |
|---|---|---|
| | internal/external | |
