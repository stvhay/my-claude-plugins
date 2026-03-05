# Research Quick Reference

## Three Research Modes

| Trigger | Mode | Config | Speed |
|---------|------|--------|-------|
| "quick research", "minor research" | Quick | 1 agent | ~10-15s |
| "do research", "research this" | Standard | 2 agents in parallel | ~15-30s |
| "extensive research" | Extensive | 9 agents (3 types x 3 threads each) | ~60-90s |

## Research Agent Types

| Agent Focus | Best For |
|-------------|----------|
| Analytical | Academic depth, detailed analysis, scholarly approach |
| Multi-perspective | Cross-domain connections, breadth |
| Contrarian | Fact-checking, alternative viewpoints |

## Examples

**Example 1: Quick research on a topic**
```
User: "quick research on Texas hot sauce brands"
-> Spawns 1 agent with single query
-> Returns top brands with brief descriptions
-> Completes in ~10-15 seconds
```

**Example 2: Standard research (default)**
```
User: "do research on AI agent frameworks"
-> Spawns 2 agents in parallel
-> Each searches from different perspective
-> Returns synthesized findings with multiple viewpoints (~15-30s)
```

**Example 3: Extensive research**
```
User: "extensive research on the history of cryptography"
-> Spawns 9 agents (3 types x 3 threads each)
-> Each takes a unique angle
-> Returns comprehensive synthesized report (~60-90s)
```
