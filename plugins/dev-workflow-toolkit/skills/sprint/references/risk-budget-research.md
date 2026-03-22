# Risk Budget for Autonomous Agent Sessions

## Purpose

This document defines a risk accumulation model for autonomous coding sessions. The agent executes a fixed workflow (spec, red test, green implementation, code review, clear-context PR review) for each task. Risk accumulates across tasks in a session because each completed task is an independent opportunity for a defect subtle enough to survive all workflow stages.

When accumulated risk reaches the session's budget ceiling, the agent **stops and checkpoints**: summarize work completed, flag highest-risk items, and hand off for human review before continuing.

## Risk Tolerance Levels

Set per session based on project context. The budget ceiling determines how much work an agent completes before a mandatory checkpoint.

| Level | Name           | Budget | Use When                                                    |
|-------|----------------|--------|-------------------------------------------------------------|
| 1     | **Supervised** | 8      | Unfamiliar codebase, new domain, or unproven agent config   |
| 2     | **Cautious**   | 15     | Production code with established patterns                   |
| 3     | **Standard**   | 25     | Well-tested codebase, strong CI, mature specs               |
| 4     | **Trusted**    | 40     | High test coverage, proven track record on this project     |
| 5     | **Autonomous** | 60     | Prototypes, internal tools, low blast radius                |

## Task Category Risk Costs

Each task the agent completes in a session adds its risk cost to the running total. Costs reflect empirical failure rates from research on agent-authored code, adjusted for the protective effect of the TDD + spec + review pipeline.

### Base costs

| Category                          | Cost | Notes                                                                                  |
|-----------------------------------|------|----------------------------------------------------------------------------------------|
| Documentation / comments          | 1    | Highest agent success rates. Low semantic risk.                                        |
| Style / formatting / linting      | 1    | Mechanical changes. Pipeline catches regressions.                                      |
| Adding or extending tests         | 2    | Low risk, high value. Tests for existing behavior are well-suited to agents.            |
| New isolated feature              | 3    | Greenfield with a clear spec is where agents perform best.                             |
| Refactoring (mechanical)          | 3    | Renames, extract-method, move-file. Tests verify behavior preservation.                |
| Refactoring (structural)          | 5    | Changing abstractions, reorganizing modules. Requires understanding intent.            |
| Modifying existing feature        | 5    | Must understand current behavior to change it safely. Spec anchors help.               |
| Bug fix                           | 7    | Empirically lowest merge rates. Requires precise fault localization.                   |
| Performance optimization          | 7    | Requires system-level understanding. Easy to introduce subtle regressions.             |
| Security-sensitive change         | 8    | 1.5-2x empirical vulnerability rate. Auth, crypto, input validation, secrets.          |
| CI / build / infrastructure       | 4    | Config errors cascade silently. Hard to test locally.                                  |

### Modifiers (applied to the base cost)

| Condition                                         | Effect          | Rationale                                                                  |
|---------------------------------------------------|-----------------|----------------------------------------------------------------------------|
| Task touches 4+ files                             | x1.5            | Cross-cutting changes weaken independence between tasks.                   |
| Sequential tasks in the same module/scope         | x1.3 on second+ | Shared-state dependency — errors in earlier work contaminate later work.   |
| Nth task in session (context degradation)         | x1.05^(N-1)     | Orchestrator context accumulates; judgment degrades.                       |
| CI passes after task completion                   | -1              | Earned confidence. Deterministic check passed.                             |
| Clear-context review finds no issues              | -1              | Independent verification passed. Minimum reduction is 1 (cost floor).     |
| CI fails during task                              | +3              | Error is now embedded. Residual risk even after fix.                       |

## Research Basis

The risk costs in this model are calibrated against empirical findings from recent studies on autonomous coding agent performance. Key findings that shaped the design:

### Agent-authored code produces more defects, concentrated in specific categories

CodeRabbit's State of AI vs. Human Code Generation Report (Dec 2025) analyzed 470 real-world open-source pull requests and found that AI-generated PRs contain 1.7x more issues overall (10.83 per PR vs. 6.45 for human-authored). The defects are not evenly distributed — logic and correctness issues rise 75%, security vulnerabilities rise 1.5-2x, readability problems increase 3x, and performance inefficiencies appear nearly 8x more often. Logic errors are flagged as the highest-stakes category because they look like reasonable code unless you trace execution step by step.

### Task type strongly predicts failure

A large-scale study of 33,000+ agent-authored pull requests across GitHub (MSR 2026) found that documentation, CI, and build update tasks are merged at the highest rates, while performance optimization and bug-fix contributions show the lowest acceptance. Not-merged PRs tend to involve larger code changes, touch more files, and frequently fail CI checks. This directly informs the cost ordering in the table above.

### Errors cascade — early mistakes compound into later failures

The AgentErrorTaxonomy research (NeurIPS 2025 workshop track) demonstrates that a single root-cause failure can cascade into successive errors, with compounding severity across subsequent steps. Memory and reflection errors are the most common sources of propagation, typically arising in early or mid-trajectory steps. Early detection and correction are critical because once cascades begin, they are difficult to reverse. This finding motivates the accumulation model and the checkpoint mechanism.

### Fault localization is easier than fault correction

The ICSE 2026 trajectory study comparing three code agents on SWE-Bench found that even failed trajectories locate the correct file over 72% of the time on standard benchmarks. However, getting close to the correct fix at the hunk level (within five lines) is a strong predictor of success vs. failure. Agents can generally find where the problem is but struggle to correctly identify what the fix should be — which is why bug fixes carry the highest base cost.

### Fresh-context review helps, with limits

Practitioners report that giving a model a clean context slate for code review does catch its own mistakes. However, the fundamental limitation is that a same-architecture reviewer shares structural blind spots with the author — it infers patterns statistically, not semantically, and will miss the business logic rules that experienced engineers internalize. This is why the pipeline pairs fresh-context review with deterministic checks (tests, linting, CI) and why review findings reduce risk cost but don't eliminate it.

### References

- [State of AI vs. Human Code Generation Report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report) — CodeRabbit, Dec 2025. Empirical analysis of 470 PRs comparing AI and human defect rates by category.
- [Are Bugs and Incidents Inevitable with AI Coding Agents?](https://stackoverflow.blog/2026/01/28/are-bugs-and-incidents-inevitable-with-ai-coding-agents/) — Stack Overflow Blog, Jan 2026. Practitioner-oriented discussion of the CodeRabbit findings with mitigation strategies.
- [Where Do AI Coding Agents Fail? An Empirical Study of Failed Agentic Pull Requests in GitHub](https://arxiv.org/html/2601.15195v1) — Ehsani et al., MSR 2026. Large-scale study of 33k+ agent-authored PRs, task-type merge rates, and rejection patterns.
- [Understanding Code Agent Behaviour: An Empirical Study of Success and Failure Trajectories](https://arxiv.org/abs/2511.00197) — Majgaonkar et al., ICSE 2026. Trajectory analysis of three code agents on SWE-Bench, fault localization findings.
- [Where LLM Agents Fail and How They Can Learn From Failures](https://arxiv.org/pdf/2509.25370) — AgentErrorTaxonomy / AgentDebug. Modular classification of failure modes, error propagation analysis, cascading failure evidence.
- [The 80% Problem in Agentic Coding](https://addyo.substack.com/p/the-80-problem-in-agentic-coding) — Addy Osmani, Jan 2026. Practitioner synthesis on fresh-context review, workflow patterns, and orchestrator mindset.
- [Rethinking Autonomy: Preventing Failures in AI-Driven Software Engineering](https://arxiv.org/html/2508.11824v1) — SAFE-AI Framework, Aug 2025. Autonomous failure rates across models (25-34%), proposed governance framework.
- [Prioritizing Real-Time Failure Detection in AI Agents](https://partnershiponai.org/wp-content/uploads/2025/09/agents-real-time-failure-detection.pdf) — Partnership on AI, Sep 2025. Architectural risk analysis, affordance-based failure prediction, layered detection recommendations.

## How to Use This

1. **At session start**, set the risk tolerance level based on the project context.
2. **After each task**, calculate its adjusted cost (base + modifiers) and add to the running total.
3. **When the total meets or exceeds the budget**, stop and checkpoint:
   - List all tasks completed with their individual risk costs.
   - Flag the highest-cost items for priority human review.
   - Summarize any CI failures or review findings encountered.
   - Wait for human direction: reset and continue, adjust tolerance, or hand off.
4. **Never exceed the budget by more than one task.** Check *before* starting a new task, not after completing it.

## What This Does Not Cover

- **Within-task quality.** The TDD + review pipeline handles that. This model governs session-level accumulation only.
- **Task prioritization.** The agent should front-load high-risk tasks when the budget is fresh, not save them for when headroom is thin.
- **Absolute safety guarantees.** This is a heuristic for managing probabilistic risk, not a formal verification system.
