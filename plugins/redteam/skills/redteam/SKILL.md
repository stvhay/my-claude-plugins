---
name: redteam
description: Adversarial analysis with multiple perspectives. Use when red team, attack idea, counterarguments, critique, stress test, devil's advocate, or poke holes in an argument.
---

# RedTeam Skill

Adversarial analysis using parallel agent deployment. Breaks arguments into atomic components, attacks from multiple expert perspectives (engineers, architects, pentesters, interns), synthesizes findings, and produces devastating counter-arguments with steelman representations.

## Workflow Routing

Route to the appropriate workflow based on the request.

| Trigger | Workflow |
|---------|----------|
| Red team analysis (stress-test existing content) | `workflows/ParallelAnalysis.md` |
| Adversarial validation (produce new content via competition) | `workflows/AdversarialValidation.md` |

## Quick Reference

| Workflow | Purpose | Output |
|----------|---------|--------|
| **ParallelAnalysis** | Stress-test existing content | Steelman + Counter-argument (8-points each) |
| **AdversarialValidation** | Produce new content via competition | Synthesized solution from competing proposals |

**The Five-Phase Protocol (ParallelAnalysis):**
1. **Decomposition** - Break into 24 atomic claims
2. **Parallel Analysis** - 32 agents examine strengths AND weaknesses
3. **Synthesis** - Identify convergent insights
4. **Steelman** - Strongest version of the argument
5. **Counter-Argument** - Strongest rebuttal

## Context Files

- `references/Philosophy.md` - Core philosophy, success criteria, agent types
- `references/Integration.md` - Skill integration, output format

## Examples

**Attack an architecture proposal:**
```
User: "red team this microservices migration plan"
--> workflows/ParallelAnalysis.md
--> Returns steelman + devastating counter-argument (8 points each)
```

**Devil's advocate on a business decision:**
```
User: "poke holes in my plan to raise prices 20%"
--> workflows/ParallelAnalysis.md
--> Surfaces the ONE core issue that could collapse the plan
```

**Adversarial validation for content:**
```
User: "battle of bots - which approach is better for this feature?"
--> workflows/AdversarialValidation.md
--> Synthesizes best solution from competing ideas
```

## Integration

**Use BEFORE RedTeam:**
- `research` - Gather context, find precedents

**Use AFTER RedTeam:**
- Consider alternatives or adjustments based on findings
