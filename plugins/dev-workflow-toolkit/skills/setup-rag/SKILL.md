---
name: setup-rag
description: Configure local-rag for project-isolated RAG indexing. Sets up .mcp.json with auto-indexing and per-project vector DB. Use when setting up RAG, enabling RAG, or indexing a repo.
---

# Setup RAG

## Overview

Configure [local-rag](https://github.com/aihaysteve/local-rag) as an MCP server for this project, with project-isolated vector database and index paths.

**Announce at start:** "I'm using the setup-rag skill to configure RAG for this project."

## Process

### 1. Check Prerequisites

Verify local-rag is available:
```bash
which local-rag 2>/dev/null || echo "local-rag not found"
```

If not found, guide installation:
```bash
# Install via pip
pip install local-rag

# Or clone and install
git clone https://github.com/aihaysteve/local-rag.git
cd local-rag && pip install -e .
```

### 2. Determine Project Paths

```bash
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
PROJECT_NAME=$(basename "$PROJECT_ROOT")
RAG_DATA_DIR="$HOME/.local/share/local-rag/$PROJECT_NAME"
```

### 3. Generate or Update .mcp.json

If `.mcp.json` exists, read it and merge. If not, create it.

The MCP server configuration:
```json
{
  "mcpServers": {
    "local-rag": {
      "command": "local-rag",
      "args": ["serve"],
      "env": {
        "LOCAL_RAG_PROJECT": "<project-name>",
        "LOCAL_RAG_DATA_DIR": "<rag-data-dir>",
        "LOCAL_RAG_WATCH": "true",
        "LOCAL_RAG_ROOT": "<project-root>"
      }
    }
  }
}
```

### 4. Add RAG Data to .gitignore

Check if `.local-rag/` is in `.gitignore`. If not, add it (for any in-project data).

### 5. Initial Index (Optional)

Ask user if they want to run initial indexing:
```bash
local-rag index --project <project-name> --root <project-root>
```

## When to Use

- Setting up a new project for RAG-powered search
- Triggered by: "set up RAG", "enable RAG", "index this repo", "configure local-rag"

## Key Principles

- **Project isolation** — each project gets its own vector DB at `~/.local/share/local-rag/<project>/`
- **Never overwrite** — merge into existing `.mcp.json`
- **Gitignore safety** — ensure RAG data directories are ignored
