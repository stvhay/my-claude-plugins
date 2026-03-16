---
name: code-simplification
description: Use after verification passes to automatically simplify code. Runs as standard pipeline step - applies low-risk changes automatically, flags structural changes for approval, analyzes failures for deeper issues.
---

# Code Simplification

## Overview

Automated refactoring after tests pass. Part of the standard development pipeline.

**Core principle:** Simplification that breaks tests is a signal, not just a failure. Analyze before reverting.

**Announce at start:** "I'm using the code-simplification skill to simplify the code you just verified."

## When to Use

This skill runs automatically after verification-before-completion passes. It operates on whatever code was just built/modified in the current session.

```
develop → verify (tests pass) → simplify → re-verify → complete
```

## Constraints

- No behavior changes (external API unchanged)
- No new features added
- Prefer deletion over modification
- Tests must pass after each change

## Pattern Categories

Simplifications are categorized by risk. Lower risk = more autonomy.

| Category | Risk | Behavior | Summary |
|----------|------|----------|---------|
| Deletion | Low | Auto-apply | One-liner |
| Parser Preference | Low | Auto-apply | One-liner |
| Flattening | Low-Moderate | Auto-apply | One-liner |
| Derivation | Moderate | Auto-apply | One-liner |
| Consolidation | Moderate-High | Auto-apply, atomic commit | Detailed |
| Structural | High | Flag for approval only | Detailed |

### Deletion (Low Risk)

- Dead code (functions/variables never called)
- Unused imports
- Unreachable branches
- Commented-out code

### Parser Preference (Low Risk)

- Replace regex/sed/grep with parser for formats with formal grammars

### Flattening (Low-Moderate Risk)

- Unnecessary wrapper functions/components
- Redundant abstraction layers
- Over-nested conditionals (flatten with early returns)
- Pointless indirection (A calls B which just calls C)

### Derivation (Moderate Risk)

- Stored values that should be computed (derived state)
- Redundant state synchronized manually
- Cached data easily derivable from source of truth

### Consolidation (Moderate-High Risk)

- Semantic duplicates (same intent, different implementation)
- Copy-paste variations with minor differences
- Functions that could be unified with a parameter

### Structural (High Risk - Flag Only)

- Interface changes
- Abstraction redesign
- Architectural simplifications
- Changes affecting multiple modules

## Execution Loop

Process simplifications incrementally, ordered by risk (low first).

```
FOR each simplification opportunity:

  1. APPLY the change

  2. VERIFY (run tests)

  3. IF tests PASS:
     - Keep the change
     - Log summary (one-liner or detailed based on category)
     - If consolidation: commit atomically with detailed message
     - Continue to next

  4. IF tests FAIL:
     - ANALYZE the failure (see @failure-analysis.md):
       • Brittle test? → Flag for test improvement
       • Hidden coupling? → Flag as refactor opportunity
       • Inconsistency revealed? → Attempt expanded fix

     - If deeper issue found AND addressable within scope:
       → Attempt to fix it
       → Re-verify
       → If still fails: revert all, log as BLOCKED, continue

     - If deeper issue exceeds scope (architectural, multi-module):
       → Revert change
       → Log as ESCALATION
       → Continue

     - If no deeper issue identified:
       → Revert change
       → Log as SKIPPED with reason
       → Continue

AFTER all opportunities processed:
  - Commit remaining low-moderate changes (grouped)
  - Run final verification
  - Present summary
```

Before applying each consolidation, verify it doesn't conflict with prior changes.

## Output Format

Present results in this structure:

```
## Simplification Complete

Applied N changes, blocked N, skipped N, N opportunities, N escalations.

### Applied
- [One-liner per low-moderate change]

### Applied (consolidation) [commit: hash]
- **[Title]** (file.ts)
  - Before: [What existed]
  - After: [What it became]
  - Scope: [Files touched, lines changed]
  - Impact: [Call sites affected]
  - Confidence: [High/Medium/Low with reason]

### Blocked
- **[Title]** (file.ts)
  - Attempted: [What was tried]
  - Failure: [What went wrong]
  - Analysis: [Root cause found]
  - Action taken: [Reverted, flagged X]
  - Recommendation: [Next steps]

### Skipped
- [Change]: [Why it was skipped]

### Opportunities (require approval)
- **Structural:** [Description of potential change]

### Escalations
- **[Issue type] in [location]**: [Description and recommended action]
```

**Summary levels:** Low-Moderate changes get one-liners (action + target + location). Consolidation and Blocked items get detailed entries with before/after, scope, impact, and confidence.

## Integration

### Pipeline Position

Runs after verification-before-completion, before completion claim.

```
verify → simplify → re-verify → complete
```

### Entry

Triggered automatically. Scope = files modified in current session.

### Exit

- Final verification must pass
- Summary presented
- Only then: completion claim allowed

### Failure Mode

If final verification fails after all simplifications:
1. Revert to pre-simplification state
2. Report what went wrong
3. Require human intervention

## References

- @patterns-by-language.md - Language-specific pattern refinements
- @failure-analysis.md - How to analyze test failures for deeper issues
