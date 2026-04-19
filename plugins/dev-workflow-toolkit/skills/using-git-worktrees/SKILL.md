---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verification
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```bash
# Check in priority order
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check CLAUDE.md

```bash
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

**If preference specified:** Use it without asking.

### 3. Ask User

If no directory exists and no CLAUDE.md preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/superpowers/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Naming Convention

Branch names and worktree paths follow a strict pattern that enables cross-skill navigation (e.g., `/review <PR#>` locating the correct worktree).

**Branch:** `<type>/<issue>-<slug>`
- `type` is one of: `feature`, `fix`, `docs`, `chore`, `refactor`
- `issue` is the GitHub issue number
- `slug` is a short hyphenated description

**Worktree path:** `.worktrees/<type>/<issue>-<slug>` — mirrors the branch name exactly.

Examples:
- Branch `feature/63-worktree-naming` → `.worktrees/feature/63-worktree-naming`
- Branch `fix/42-broken-auth` → `.worktrees/fix/42-broken-auth`
- Branch `docs/39-token-efficiency` → `.worktrees/docs/39-token-efficiency`

**Why this matters:** `requesting-code-review` navigates PR → issue number → worktree path. It matches `git worktree list` paths using the regex `/<issue>-` (bounded — `/63-` must not match `/630-`). If the worktree path doesn't follow this convention, `/review <PR#>` cannot find it.

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**MUST verify directory is ignored before creating worktree:**

```bash
# Check if directory is ignored (respects local, global, and system gitignore)
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**If NOT ignored:**

Per Jesse's rule "Fix broken things immediately":
1. Add appropriate line to .gitignore
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents to repository.

### For Global Directory (~/.config/superpowers/worktrees)

No .gitignore verification needed - outside project entirely.

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

New branches MUST be created from the repo's default branch (typically `main`) — not from whatever branch is currently checked out. Branching from a feature branch causes add/add merge conflicts when both branches land on `main` (#120).

```bash
# Determine full path
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$BRANCH_NAME"
    ;;
  ~/.config/superpowers/worktrees/*)
    path="~/.config/superpowers/worktrees/$project/$BRANCH_NAME"
    ;;
esac

# Detect the repo's default branch (main or master) and fetch latest from origin
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's|refs/remotes/origin/||')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
git fetch origin "$DEFAULT_BRANCH" --quiet

# Create worktree with new branch, always based on origin/<default-branch>
git worktree add "$path" -b "$BRANCH_NAME" "origin/$DEFAULT_BRANCH"
cd "$path"
```

### 3. Run Project Setup

Before invoking any build or dependency-install command, **isolate the worktree's environment** so it doesn't inherit the parent worktree's state (#160):

```bash
# Python: detach from parent repo's .venv so the worktree creates its own
unset VIRTUAL_ENV

# Container/bind-mount filesystems: avoid hardlink failures with uv
export UV_LINK_MODE=copy
```

Then auto-detect and run appropriate setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ] && command -v uv >/dev/null; then uv sync; fi
if [ -f pyproject.toml ] && ! command -v uv >/dev/null; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

### 4. Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
# Examples - use project-appropriate command
npm test
cargo test
pytest
go test ./...
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 5. Report Location

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Mistakes and Red Flags

- **Skip ignore verification** — worktree contents get tracked. Always `git check-ignore` first.
- **Assume directory location** — follow priority: existing > CLAUDE.md > ask.
- **Proceed with failing tests** — report failures, get explicit permission.
- **Hardcode setup commands** — auto-detect from project files.
- **Skip CLAUDE.md check** — it may specify a preferred directory.
- **Forget CWD verification** — after `cd`, verify with `pwd` and `git branch --show-current`.
- **Lose CWD** — re-verify at start of each task. Recovery: `git worktree list` to find valid paths.
- **Remove active worktree** — never remove a worktree another agent/session is using.

## Integration

**Called by:**
- **brainstorming** (Phase 4) - REQUIRED when design is approved and implementation follows
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete. Use `git worktree remove`.
- **executing-plans** or **subagent-driven-development** - Work happens in this worktree
