# Work Breakdown Structure

**Epic:** #39 — Token efficiency and model choice
**Beads:** my-claude-plugins-0uc
**Date:** 2026-03-13

## Overview

Improve dev-workflow-toolkit token efficiency and model selection through an
OODA-based experimental methodology. All interventions are validated by
experiment before reaching production skills.

## Issues

9 child issues, strictly sequential. Each produces one PR with one
deliverable committed to the tree.

### Phase 1 — Telemetry Fixes

| Issue | Title | Beads | Deliverable | Tree location |
|-------|-------|-------|-------------|---------------|
| #65 | Fix cached token double-counting | .0uc.1 | Code fix to `extract_usage()` — send uncached tokens as `input`, not total | `hooks/langfuse-trace.py` |
| #66 | Add experiment tagging env vars | .0uc.2 | Read `LANGFUSE_EXPERIMENT`, `LANGFUSE_VARIANT`, `LANGFUSE_RUN` from env, emit as trace tags | `hooks/langfuse-trace.py` |

### Phase 2 — Research & Design

| Issue | Title | Beads | Deliverable | Tree location |
|-------|-------|-------|-------------|---------------|
| #67 | Baseline telemetry report | .0uc.3 | Corrected cost analysis, token distribution, cache rates, per-session profiles | `docs/experiments/39-token-efficiency/01-baseline/` |
| #68 | Literature review + value/risk matrix | .0uc.4 | Paper summaries, each intervention scored on value and risk using baseline data | `docs/experiments/39-token-efficiency/02-literature-review/` |

### Phase 3 — Experimentation

| Issue | Title | Beads | Deliverable | Tree location |
|-------|-------|-------|-------------|---------------|
| #69 | Synthetic benchmark design + validation | .0uc.5 | Task definition, validation run, methodology document | `docs/experiments/39-token-efficiency/03-benchmark-design/` + `methodology.md` |
| #70 | Run experiments | .0uc.6 | Per-variant results, comparison tables, `.zip` of each experiment branch | `docs/experiments/39-token-efficiency/04-experiment-runs/` |

### Phase 4 — Synthesis & Delivery

| Issue | Title | Beads | Deliverable | Tree location |
|-------|-------|-------|-------------|---------------|
| #71 | Results write-up | .0uc.7 | Synthesis of findings, recommendations, ACE framework `/ideate` → future work section | `docs/experiments/39-token-efficiency/05-results/` |
| #72 | Validate high-risk interventions | .0uc.8 | Expanded validation against realistic tasks. May be skipped with documented rationale | `docs/experiments/39-token-efficiency/06-validation/` |
| #73 | Deliver validated improvements | .0uc.9 | Apply synthesized improvements to production skills and hooks | `plugins/dev-workflow-toolkit/` |

## Dependency Chain

```
#65 → #66 → #67 → #68 → #69 → #70 → #71 → #72 → #73
```

## Experiment Directory

```
docs/experiments/39-token-efficiency/
├── README.md
├── wbs.md                     ← this file
├── methodology.md             ← written during #69
├── 01-baseline/
│   ├── report.md
│   └── figures/
├── 02-literature-review/
│   ├── report.md
│   └── papers/
├── 03-benchmark-design/
│   ├── report.md
│   └── task/
├── 04-experiment-runs/
│   ├── report.md
│   ├── variants/              ← .zip per experiment branch
│   └── figures/
├── 05-results/
│   ├── report.md
│   └── figures/
└── 06-validation/
    ├── report.md
    └── figures/
```

## Report Format

Each report uses this header:

```markdown
# <Title>

**Epic:** #39
**Issue:** #<N>
**Date:** YYYY-MM-DD
**Depends on:** #<prior issue>
```

## Preliminary Baseline Data

Collected 2026-03-11 to 2026-03-13 across 22 sessions, 4 projects. All
claude-opus-4-6. Costs corrected for the double-counting bug (#65).

| Session | Gens | Cache rate | Avg input/gen | Avg output/gen | Cost |
|---------|------|-----------|---------------|----------------|------|
| ragling feature | 65 | 97.4% | 49K | 126 | $2.18 |
| ragling main | 142 | 97.0% | 88K | 134 | $8.44 |
| mcp worktree | 98 | 96.6% | 53K | 78 | $3.58 |
| mcp feature50 | 392 | 95.6% | 50K | 126 | $14.93 |

Cost breakdown: fresh input 19-29%, cache reads 63-72%, output 5-9%.

## Research Basis

Papers to review in #68:

| Area | Paper | Key claim |
|------|-------|-----------|
| Routing | RouteLLM (ICLR 2025) | 85% cost reduction, 95% quality |
| Routing | BudgetMLAgent (2024) | Cascade: 94% cost savings, better success rate |
| Diversity | DEI (Salesforce 2024) | Heterogeneous committees +25% on SWE-bench |
| Diversity | Agent Scaling via Diversity (2025) | Homogeneous agents have diminishing returns |
| Tokens | Complexity Trap (JetBrains, NeurIPS 2025) | Observation masking halves cost |
| Tokens | Tokenomics (MSR 2026) | 59.4% of tokens go to code review |
| Oracle | Grading Scale Impact (2026) | 0-5 scale gives best human-LLM alignment |
| Oracle | Agent-as-a-Judge (2024) | Agents that execute verification outperform prompt-only judges |
