# Quick Research Workflow

**Mode:** Single agent, 1 query | **Timeout:** 30 seconds

## When to Use

- User says "quick research" or "minor research"
- Simple, straightforward queries
- Time-sensitive requests
- Just need a fast answer

## Workflow

### Step 1: Launch Single Agent

**ONE Task call with a single focused query:**

```
Task({
  subagent_type: "general-purpose",
  description: "[topic] quick lookup",
  prompt: "Do ONE web search for: [query]. Return the key findings immediately. Keep it brief and factual."
})
```

**Prompt requirements:**
- Single, well-crafted query
- Instruct to return immediately after first search
- No multi-query exploration

### Step 2: Return Results

Report findings using this format:

```markdown
## Quick Research: [topic]

**Key Findings:**
[Main points from the search]

**Sources:**
- [Verified URL 1]
- [Verified URL 2]

**Confidence:** [High/Medium/Low based on source quality]

**Need more depth?** Run "do research on [topic]" for standard mode.
```

## Speed Target

~10-15 seconds for results
