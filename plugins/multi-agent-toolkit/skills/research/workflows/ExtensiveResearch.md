# Extensive Research Workflow

**Mode:** 9 agents (3 types x 3 threads each) | **Timeout:** 5 minutes

## CRITICAL: URL Verification Required

**BEFORE delivering any research results with URLs:**
1. Verify EVERY URL using WebFetch or curl
2. Confirm the content matches what you're citing
3. NEVER include unverified URLs - research agents HALLUCINATE URLs
4. A single broken link is a CATASTROPHIC FAILURE

See `references/UrlVerificationProtocol.md` for full protocol.

## When to Use

- User says "extensive research" or "do extensive research"
- Deep-dive analysis needed
- Comprehensive multi-domain coverage required
- High-stakes decisions requiring thorough research

## Workflow

### Step 0: Generate Creative Research Angles

Think deeply about the research topic:
- Explore multiple unusual perspectives and domains
- Question assumptions about what's relevant
- Make unexpected connections across fields
- Consider edge cases, controversies, emerging trends

Generate 3 unique angles per agent type (9 total queries).

### Step 1: Launch All Research Agents in Parallel

**SINGLE message launching 9 Task calls (3 types x 3 threads each):**

```
// Analytical - 3 threads (academic, analytical, scholarly)
Task({ subagent_type: "general-purpose", description: "[topic] angle 1", prompt: "Search for: [angle 1]. Return findings." })
Task({ subagent_type: "general-purpose", description: "[topic] angle 2", prompt: "Search for: [angle 2]. Return findings." })
Task({ subagent_type: "general-purpose", description: "[topic] angle 3", prompt: "Search for: [angle 3]. Return findings." })

// Multi-perspective - 3 threads (cross-domain connections)
Task({ subagent_type: "general-purpose", description: "[topic] angle 4", prompt: "Search for: [angle 4]. Return findings." })
Task({ subagent_type: "general-purpose", description: "[topic] angle 5", prompt: "Search for: [angle 5]. Return findings." })
Task({ subagent_type: "general-purpose", description: "[topic] angle 6", prompt: "Search for: [angle 6]. Return findings." })

// Contrarian - 3 threads (fact-based, alternative views)
Task({ subagent_type: "general-purpose", description: "[topic] angle 7", prompt: "Search for: [angle 7]. Return findings." })
Task({ subagent_type: "general-purpose", description: "[topic] angle 8", prompt: "Search for: [angle 8]. Return findings." })
Task({ subagent_type: "general-purpose", description: "[topic] angle 9", prompt: "Search for: [angle 9]. Return findings." })
```

**Each agent:**
- Gets ONE focused angle
- Does 1-2 searches max
- Returns as soon as it has findings

### Step 2: Collect Results (5 MINUTE TIMEOUT)

- Agents run in parallel
- Most return within 30-90 seconds
- **HARD TIMEOUT: 5 minutes** - proceed with whatever has returned
- Note non-responsive agents

### Step 3: Comprehensive Synthesis

**Synthesis requirements:**
- Identify themes across all 9 research angles
- Cross-validate findings from multiple sources
- Highlight unique insights from each approach
- Note where sources agree (high confidence)
- Flag conflicts or gaps

**Report structure:**
```markdown
## Executive Summary
[2-3 sentence overview]

## Key Findings
### [Theme 1]
- Finding (confirmed by: multiple agents)
- Finding (source: specific agent)

### [Theme 2]
...

## Unique Insights by Approach
- **Analytical**: [depth findings]
- **Multi-perspective**: [cross-domain connections]
- **Contrarian**: [alternative viewpoints]

## Conflicts & Uncertainties
[Note disagreements]
```

### Step 4: VERIFY ALL URLs (MANDATORY)

**Before delivering results, verify EVERY URL:**

```bash
# For each URL returned by agents:
curl -s -o /dev/null -w "%{http_code}" -L "URL"
# Must return 200

# Then verify content:
WebFetch(url, "Confirm article exists and summarize main point")
# Must return actual content, not error
```

**If URL fails verification:**
- Remove it from results
- Find alternative source via WebSearch
- Verify the replacement URL
- NEVER include unverified URLs

**Extensive mode generates MANY URLs - allocate time for verification.**

### Step 5: Return Results

```markdown
## Extensive Research: [topic]

### Executive Summary
[2-3 sentence overview]

### Key Findings
[Comprehensive findings by theme]

### Unique Insights
- **From depth analysis**: [key insight]
- **From breadth analysis**: [key insight]
- **From contrarian analysis**: [key insight]

### Sources (Verified)
- [URL 1]
- [URL 2]
- ...

### Confidence Assessment
[Overall confidence level with rationale]

### Research Metrics
- Total agents: 9
- Approaches: analytical, multi-perspective, contrarian
- Coverage: [assessment]
```

## Speed Target

~60-90 seconds for results (parallel execution)
