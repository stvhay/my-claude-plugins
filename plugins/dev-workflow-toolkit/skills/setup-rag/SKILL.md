---
name: setup-rag
description: Configure local-rag for project-isolated RAG indexing. Sets up .mcp.json with auto-indexing and per-project vector DB. Use when setting up RAG, enabling RAG, or indexing a repo.
---

# Setup RAG

## Overview

Configure [ragling](https://github.com/aihaysteve/local-rag) as an MCP server for this project. Ragling provides privacy-first local RAG with per-project vector databases, automatic indexing on serve, and live file watching.

**Announce at start:** "I'm using the setup-rag skill to configure RAG for this project."

## Process

### 1. Check Prerequisites

Verify each prerequisite. If any are missing, report what's needed and **stop** — do not attempt installation.

```bash
# Check uv
which uv 2>/dev/null || echo "MISSING: uv — install with: brew install uv"

# Check ollama
which ollama 2>/dev/null || echo "MISSING: ollama — install with: brew install ollama"

# Check ollama is running
ollama list 2>/dev/null || echo "MISSING: ollama is not running — start with: ollama serve"

# Check bge-m3 model
ollama list 2>/dev/null | grep -q bge-m3 || echo "MISSING: bge-m3 model — pull with: ollama pull bge-m3"
```

If anything is missing, report all missing prerequisites together with install commands, then stop.

### 2. Clone or Update Ragling

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

if [ -d "$PROJECT_ROOT/.ragling" ]; then
    # Update existing clone
    git -C "$PROJECT_ROOT/.ragling" pull
else
    # Fresh clone
    git clone https://github.com/aihaysteve/local-rag.git "$PROJECT_ROOT/.ragling"
fi
```

### 3. Initialize Ragling

Run init from the project root. This generates `ragling.json` (with watch pointing at the project directory) and `.mcp.json` (with the MCP server configuration using absolute paths).

```bash
cd "$PROJECT_ROOT" && uv run --directory .ragling ragling init
```

### 4. Update .gitignore

Ensure these entries are in `.gitignore` — all contain absolute paths or reproducible state:

```
.ragling/
ragling.json
```

**Do not gitignore `.mcp.json`** — it may contain other MCP server configurations the user wants to track. Instead, note that `ragling init` adds ragling-specific entries with absolute paths. The user can decide whether to gitignore `.mcp.json` themselves.

### 5. Verify Setup

```bash
# Check ragling.json exists and has watch config
cat "$PROJECT_ROOT/ragling.json"

# Check .mcp.json exists and has ragling server
cat "$PROJECT_ROOT/.mcp.json"
```

Confirm:
- `ragling.json` has a `watch` key mapping a name to the project directory
- `.mcp.json` has a `mcpServers.ragling` entry with `command: "uv"` and args pointing to `.ragling`

Report success:

> RAG configured. Restart your Claude Code session to start the MCP server.
> On startup, ragling will automatically index the project and watch for changes.

## How It Works (for reference)

When the MCP server starts (`ragling serve`):
1. Leader election occurs (supports multiple MCP instances)
2. Leader runs startup sync — discovers and indexes all watch directories
3. Watchdog file watcher starts with 2-second debounce for ongoing changes
4. `rag_search` tool becomes available in Claude

No manual indexing or hooks needed — serve handles everything.

## When to Use

- Setting up a new project for RAG-powered search
- Triggered by: "set up RAG", "enable RAG", "index this repo", "configure local-rag", "configure ragling"

## Key Principles

- **Project isolation** — ragling cloned per-project in `.ragling/`, vector DB isolated per group
- **Check, don't install** — report missing prerequisites with install commands, don't run them
- **Never overwrite** — if `.mcp.json` exists, `ragling init` merges into it
- **Gitignore safety** — `.ragling/` and `ragling.json` are always gitignored
