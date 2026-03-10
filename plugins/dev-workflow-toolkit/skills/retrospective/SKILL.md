---
name: retrospective
description: "Post-completion session analysis and upstream feedback. Invoked by finishing-a-development-branch after PR creation to capture what worked, what didn't, and file improvement issues upstream."
---

# Retrospective

## Overview

Analyze a completed development session, categorize findings, and file
upstream issues for skill workflow improvements. The agent does the analysis
work; the user validates and steers.

**Announce at start:** "I'm running a brief retrospective on this session."

## When This Runs

Invoked as Step 8 of finishing-a-development-branch, after the PR is created
and beads are synced. Non-blocking — if the user declines, skip entirely.

Ask: "Would you like a brief retrospective on this session? (Takes ~2 minutes)"

If no: "Skipping retrospective. Session complete."

## The Process

### Step 1: Analyze Session Context

Review available context from this session:

- **Commits** — `git log --oneline $(git merge-base HEAD main)..HEAD`
- **PR** — `gh pr view --json title,body,additions,deletions` (if created)
- **Plan vs actual** — compare the implementation plan (if one exists in `docs/plans/`) against what was actually built
- **Blockers** — note any workarounds, retries, or skill invocations that failed
- **Skill usage** — which skills were invoked, which worked smoothly, which caused friction

### Step 2: Present Structured Analysis

Present findings organized as:

```
## Session Retrospective

### What Went Well
- [Specific steps/skills that worked as intended]

### Friction Points
- [Where things broke, required workarounds, or took longer than expected]
- [Include root cause if determinable]

### Proposed Improvements

**Project-local** (for this project's CLAUDE.md or memory):
- [Improvement] — [rationale]

**Upstream skill improvements** (file as issues):
- [Skill name]: [improvement] — [rationale]

### Questions
- [Only if agent can't determine root cause of a friction point]
```

### Step 3: User Review

The user confirms, corrects, or adds context to the analysis. Iterate until
the user is satisfied with the findings.

### Step 4: Act on Findings

**For project-local improvements:**
- Present the improvements and let the user decide where to save them
  (CLAUDE.md, memory, or skip)

**For upstream skill improvements:**
- Determine the target repo from the plugin manifest:
  ```bash
  # Walk up from the skill that needs improvement to find plugin.json
  # Parse the repo from marketplace.json or plugin metadata
  # The source repo is typically in marketplace.json's plugin entry
  cat .claude-plugin/marketplace.json 2>/dev/null | grep -o '"repo"[^,]*'
  ```
- If the target repo cannot be determined, ask the user for it
- Draft an issue for each upstream improvement:
  ```
  Title: [skill-name]: [concise improvement description]

  ### Context
  [How the issue was discovered — what session, what task]

  ### Problem
  [What went wrong or could be better]

  ### Suggested Improvement
  [Specific change proposed]

  ### Session Evidence
  [Relevant details from the session]
  ```
- Present the draft to the user for approval
- Once approved, file:
  ```bash
  gh issue create -R <source-repo> \
    --title "<title>" \
    --body "<body>" \
    --label "feedback"
  ```
  If the `feedback` label doesn't exist on the target repo, create it first:
  ```bash
  gh label create "feedback" --description "User feedback from retrospective" \
    -R <source-repo> 2>/dev/null || true
  ```

### Step 5: Complete

Report what was saved/filed and end the session.

## Key Principles

- **Non-blocking** — never gate PR creation or merge
- **Completed staff work** — agent analyzes first, user validates
- **Two buckets** — project-local vs upstream, clearly separated
- **Evidence-based** — cite specific session events, not vague impressions
- **Low friction** — takes ~2 minutes for a typical session

## Integration

**Called by:**
- **finishing-a-development-branch** — Step 8, after Beads Sync

**Does not invoke other skills.** This is a terminal operation.
