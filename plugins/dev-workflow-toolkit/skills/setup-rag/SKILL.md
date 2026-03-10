---
name: setup-rag
description: Configure ragling for project-isolated RAG indexing. Sets up .mcp.json with auto-indexing and per-project vector DB. Use when setting up RAG, enabling RAG, or indexing a repo.
---

# Setup RAG

## Overview

Configure [ragling](https://github.com/aihaysteve/local-rag) as an MCP server for this project. Ragling provides privacy-first local RAG with per-project vector databases, automatic indexing on serve, and live file watching.

**Announce at start:** "I'm using the setup-rag skill to configure RAG for this project."

## Process

### 1. Check Prerequisites

Verify each prerequisite. If any are missing, report what's needed and **stop** — do not attempt installation.

```bash
# Check uv (https://docs.astral.sh/uv/getting-started/installation/)
which uv 2>/dev/null || echo "MISSING: uv — see https://docs.astral.sh/uv/getting-started/installation/"

# Check ollama (https://ollama.com/download)
which ollama 2>/dev/null || echo "MISSING: ollama — see https://ollama.com/download"

# Check ollama is running
ollama list 2>/dev/null || echo "MISSING: ollama is not running — start with: ollama serve"

# Check bge-m3 model
ollama list 2>/dev/null | grep -q bge-m3 || echo "MISSING: bge-m3 model — pull with: ollama pull bge-m3"
```

If anything is missing, report all missing prerequisites together with install links, then stop.

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

Run init from the project root. This generates `ragling.json` and updates `.mcp.json`.

```bash
cd "$PROJECT_ROOT" && uv run --directory .ragling ragling init
```

`ragling init` produces:
- **`ragling.json`** — watch configuration mapping the project name to `.` (the project directory)
- **`.mcp.json`** — merges a `ragling` entry into `mcpServers`, preserving any existing MCP server configurations. Only the `mcpServers.ragling` key is written; other entries are left untouched.

### 4. Update .gitignore

Ensure these entries are in `.gitignore` — the clone is reproducible and config contains absolute paths:

```
.ragling/
ragling.json
```

**Do not gitignore `.mcp.json`** — it may contain other MCP server configurations the user wants to track. The ragling entry will contain absolute paths, so the user can decide whether to gitignore `.mcp.json` themselves.

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

## Troubleshooting

- **`rag_search` tool not available** — restart Claude Code after setup so the MCP server starts. Check `.mcp.json` has a `mcpServers.ragling` entry.
- **`ragling init` fails** — ensure `uv` can resolve dependencies: run `uv run --directory .ragling ragling --help` to test. If the `.ragling/` clone is corrupt, delete it and re-run step 2.
- **Ollama connection errors** — verify `ollama serve` is running and `ollama list` shows `bge-m3`. Ragling needs ollama for embeddings.
- **Search returns stale results** — the file watcher has a 2-second debounce. For large batch changes, wait a few seconds and retry. If indexing seems stuck, restart the Claude Code session to trigger a fresh startup sync.
- **Cleanup** — to remove ragling from a project, delete `.ragling/`, `ragling.json`, and the `mcpServers.ragling` entry from `.mcp.json`. Remove the `.gitignore` entries.

## When to Use

- Setting up a new project for RAG-powered search
- Triggered by: "set up RAG", "enable RAG", "index this repo", "configure local-rag", "configure ragling"

## Key Principles

- **Project isolation** — ragling cloned per-project in `.ragling/`, vector DB isolated per group
- **Check, don't install** — report missing prerequisites with install links, don't run them
- **Merge, not overwrite** — `ragling init` merges into existing `.mcp.json`, preserving other MCP server entries
- **Gitignore safety** — `.ragling/` and `ragling.json` are always gitignored
