---
name: project-init
description: Scaffold a new project with GitHub templates, CONTRIBUTING.md, and CLAUDE.md skeleton. Use when starting a fresh repo or adding standard project structure.
---

# Project Init

## Overview

Initialize a project with standard scaffolding for Claude Code-driven development.

**Announce at start:** "I'm using the project-init skill to set up project scaffolding."

## What It Creates

1. `.github/ISSUE_TEMPLATE/bug-report.yml` — Bug report template
2. `.github/ISSUE_TEMPLATE/feature-request.yml` — Feature request template
3. `.github/pull_request_template.md` — PR template with checklist
4. `CONTRIBUTING.md` — Contribution workflow guide
5. `CLAUDE.md` (optional) — Project configuration for Claude Code

## Process

1. Check which files already exist — skip any that do (warn user)
2. Ask project name and purpose (for CLAUDE.md and README references)
3. Copy templates from `templates/` directory, adapting project name
4. Optionally generate CLAUDE.md skeleton with project-specific sections
5. Create `docs/plans/` directory for implementation plans
6. Commit scaffolding files

## Templates

Templates are stored in `templates/` relative to this skill. They are generic and work with any project — no language or framework assumptions.

## When to Use

- Starting a fresh repository
- Adding standard structure to an existing repo missing these files
- Triggered by: "init project", "set up repo", "scaffold project", "new project setup"

## Session-Start Hook (Optional)

If the project uses the quality gate, offer to install a session-start hook
that runs structural checks automatically when a Claude Code session begins.

Resolve the quality gate path first:
```bash
QUALITY_GATE="$(cd "${CLAUDE_SKILL_DIR}/../.." && pwd)/scripts/quality-gate.sh"
```

Then create `.claude/settings.json` (or merge into existing), using the resolved absolute path:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/scripts/quality-gate.sh --path ."
          }
        ]
      }
    ]
  }
}
```

Replace `/absolute/path/to/scripts/quality-gate.sh` with the value of `$QUALITY_GATE` resolved above.

> Note: `.claude/settings.json` is a project-level file. If the project
> gitignores `.claude/`, the hook is local-only. Otherwise commit it.

## Post-Install

After installing or upgrading the dev-workflow-toolkit plugin, read
`CHANGELOG.md` in the plugin root. Apply entries marked **ACTION** that
are relevant to the project.

## Key Principles

- **Never overwrite** existing files without asking
- **No language assumptions** — templates work for any stack
- **Minimal scaffolding** — only files that provide immediate value
