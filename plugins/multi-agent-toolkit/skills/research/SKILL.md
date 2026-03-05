---
name: research
description: Multi-source parallel research. Use when research, do research, quick research, extensive research, find information, or investigate a topic. For due diligence or background checks, use osint skill instead.
---

# Research Skill

Comprehensive research system using parallel researcher agents across multiple sources.

## MANDATORY: URL Verification

**Every URL must be verified before delivery.** Research agents hallucinate URLs. A single broken link is a catastrophic failure.

See `references/UrlVerificationProtocol.md` for details.

## Workflow Routing

Route to the appropriate workflow based on the request.

**CRITICAL:** For due diligence, company/person background checks, or vetting -> **USE OSINT SKILL INSTEAD**

### Research Modes (Primary Workflows)
- Quick/minor research (1 agent, 1 query) -> `workflows/QuickResearch.md`
- Standard research - DEFAULT (2 agents in parallel) -> `workflows/StandardResearch.md`
- Extensive research (9 agents in parallel) -> `workflows/ExtensiveResearch.md`

## Quick Reference

| Trigger | Mode | Speed |
|---------|------|-------|
| "quick research" | 1 agent | ~10-15s |
| "do research" | 2 agents (default) | ~15-30s |
| "extensive research" | 9 agents | ~60-90s |

See `references/QuickReference.md` for detailed comparison.

## Integration

### Feeds Into
- Council debates (research context first)
- RedTeam analysis (gather precedents)
- Writing and content creation

### Uses
- WebSearch and WebFetch tools
- Parallel Task agents

## File Organization

**Scratch (temporary work artifacts):** `.superpowers/research/scratch/`

**History (permanent):** `.superpowers/research/YYYY-MM-DD-[topic]/`
