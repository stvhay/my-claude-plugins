---
name: documentation-standards
description: "Validate and draft project documentation updates. Invoked by brainstorming (draft mode) and finishing-a-development-branch (validate mode) to ensure tracked docs reflect architectural and design decisions."
---

# Documentation Standards

## Overview

Ensure project documentation stays current with architectural and design decisions. Operates in two modes depending on the calling skill.

**Reference material:** See `references/project-docs.md` for the documentation structure standard and `references/adr-guide.md` for ADR best practices.

## Mode: Draft (Called by Brainstorming)

After the user approves a design, brainstorming invokes this skill to identify what tracked documentation needs updating.

### Process

1. **Read existing tracked docs:**
   - `README.md` (project root)
   - `docs/ARCHITECTURE.md` (if exists)
   - `docs/DESIGN.md` (if exists)
   - Relevant `SPEC.md` files (walk up from affected directories)

2. **Compare against the approved design:**
   - What architectural decisions were made? Are they in ARCHITECTURE.md?
   - What design patterns or conventions were chosen? Are they in DESIGN.md?
   - Do any subsystem contracts change? Check relevant SPEC.md files.
   - Does the public interface change? Check README.md.

3. **Draft documentation updates:**
   - For each gap, draft the new or updated section
   - Use ADR rigor: context → decision → consequences
   - Use Alexandrian prologue for quick scanning:
     > In the context of [X], facing [Y], we decided [Z] to achieve [W], accepting [Q].
   - If a document doesn't exist yet, draft the initial version

4. **Present to user:**
   - Show which documents need updating and the drafted content
   - User approves, modifies, or defers each update

5. **Include in design doc:**
   - Add approved drafts to the design doc under a "## Documentation Updates" section
   - This section carries forward into the implementation plan as work to be done

### Output

A "Documentation Updates" section added to the design doc listing:
- Which files to update
- The drafted content for each update
- Any deferred updates with reasons

## Mode: Validate (Called by Finishing-a-Development-Branch)

After tests pass, finishing invokes this skill as a **hard gate** to verify tracked docs reflect the completed work.

<HARD-GATE>
Do NOT allow the branch to proceed to option presentation, PR creation, or merge until documentation validation passes or the developer explicitly defers with a recorded reason.
</HARD-GATE>

### Process

1. **Detect scope of changes:**
   ```bash
   # Determine base branch (same pattern as finishing Step 3)
   base=$(git merge-base HEAD main 2>/dev/null && echo main || \
          git merge-base HEAD master 2>/dev/null && echo master)

   # What changed on this branch?
   git diff $(git merge-base HEAD $base)...HEAD --stat
   git diff $(git merge-base HEAD $base)...HEAD --name-only
   ```

2. **Classify the change:**
   - **Skip gate** if changes are limited to: bug fixes with no architectural impact, pure refactors with no behavior change, dependency bumps with no design impact. Announce: "Documentation gate: no documentation-impacting changes detected. Proceeding."
   - **Enforce gate** if changes include: new subsystems or components, modified public interfaces, new patterns or conventions, SPEC.md changes, anything the design doc flagged for documentation updates.

3. **Check tracked docs exist:**
   - If `docs/ARCHITECTURE.md` or `docs/DESIGN.md` don't exist and the changes warrant them, warn and recommend creating them.

4. **Read the design doc** (if one exists in `docs/plans/`):
   - Pull the "Documentation Updates" section drafted during brainstorming
   - Check whether each drafted update was implemented

5. **Read current tracked docs:**
   - `README.md`, `docs/ARCHITECTURE.md`, `docs/DESIGN.md`
   - Relevant `SPEC.md` files for modified subsystems

6. **Evaluate completeness:**
   - Do tracked docs reflect the decisions and changes in this branch?
   - Are there new architectural decisions not in ARCHITECTURE.md?
   - Are there new design patterns not in DESIGN.md?
   - Are modified subsystem behaviors reflected in SPEC.md?
   - Has any SPEC.md grown beyond recommended length? (Flag for decomposition)

7. **If gaps found — block and present:**
   ```
   Documentation gate: gaps found.

   Missing from docs/ARCHITECTURE.md:
   - [description of missing decision]

   Missing from plugins/foo/SPEC.md:
   - [description of missing invariant update]

   Options:
   1. I'll draft the updates now (recommended)
   2. You write the updates manually
   3. Defer documentation — reason required (recorded in PR body)
   ```

8. **If option 3 (defer):**
   - Require a reason
   - Record in PR body as: `**Documentation deferred:** [reason]`
   - Proceed past the gate

9. **If no gaps — pass:**
   ```
   Documentation gate: all tracked docs are current. Proceeding.
   ```

## What Counts as a Gap

| Change Type | Expected Documentation |
|-------------|----------------------|
| New architectural decision | Section in `docs/ARCHITECTURE.md` |
| New design pattern or convention | Section in `docs/DESIGN.md` |
| Modified subsystem behavior | Updated `SPEC.md` (invariants, failure modes, interface) |
| SPEC.md exceeds recommended length | Flag for subsystem decomposition |
| Public interface change | Updated `README.md` |
| New subsystem without SPEC.md | Recommend `/codify-subsystem` |

## What Doesn't Trigger the Gate

- Bug fixes that don't change architecture or design
- Pure refactors that don't alter behavior or contracts
- Dependency bumps with no design impact
- Test-only changes
- Documentation-only changes (already updating docs)

## Integration

**Called by:**
- **brainstorming** — Draft mode, after design approval
- **finishing-a-development-branch** — Validate mode, as hard gate after tests

**References:**
- `references/project-docs.md` — Documentation structure standard
- `references/adr-guide.md` — ADR best practices and templates
