# Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

```
Task tool (general-purpose):
  description: "Review spec compliance for Task N"
  prompt: |
    You are reviewing whether an implementation matches its specification.

    ## What Was Requested

    [FULL TEXT of task requirements]

    ## What Implementer Claims They Built

    [From implementer's report]

    ## Known Expected Breakage (cross-task context)

    [From orchestrator. If Task N's scope intentionally breaks downstream call sites
    that a later task will fix, describe them here. Example: "Task 2 will update
    server.py to use the new session API; breakage at session.add_message() call sites
    is expected and handled there, not a Task 1 finding." Leave blank if none.]

    ## CRITICAL: Do Not Trust the Report

    The implementer finished suspiciously quickly. Their report may be incomplete,
    inaccurate, or optimistic. You MUST verify everything independently.

    **DO NOT:**
    - Take their word for what they implemented
    - Trust their claims about completeness
    - Accept their interpretation of requirements

    **DO:**
    - Read the actual code they wrote
    - Compare actual implementation to requirements line by line
    - Check for missing pieces they claimed to implement
    - Look for extra features they didn't mention

    ## Your Job

    Read the implementation code and verify:

    **Missing requirements:**
    - Did they implement everything that was requested?
    - Are there requirements they skipped or missed?
    - Did they claim something works but didn't actually implement it?

    **Extra/unneeded work:**
    - Did they build things that weren't requested?
    - Did they over-engineer or add unnecessary features?
    - Did they add "nice to haves" that weren't in spec?

    **Misunderstandings:**
    - Did they interpret requirements differently than intended?
    - Did they solve the wrong problem?
    - Did they implement the right feature but wrong way?

    **Plan fidelity:**
    - Did the implementer use the approach/libraries specified in the task?
    - If they diverged, did they document it with rationale in their report?
    - Are there undocumented divergences (different tech stack, architecture, or approach than specified)?

    **Verify by reading code, not by trusting report.**

    **Expected breakage exception:** Findings that match "Known Expected Breakage"
    above are NOT issues for this task — flag them as "handled by Task N" instead of
    failing the review. Still report them in a separate line so the orchestrator can
    confirm the downstream task still accounts for them.

    Report:
    - ✅ Spec compliant (if everything matches after code inspection)
    - ❌ Issues found: [list specifically what's missing or extra, with file:line references]
    - ⚠️ Plan divergence: [what was specified vs. what was implemented, whether documented by implementer]
```
