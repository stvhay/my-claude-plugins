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
6. `compute-version.sh` + `compute_version.py` — Version management scripts
7. `.github/workflows/release.yml` — Release automation workflow
8. Validation hooks for version bump and changelog enforcement

## Release Infrastructure

After scaffolding the base files, offer to set up release infrastructure:

1. **Detect tech stack** — check for `package.json`, `Cargo.toml`, `pyproject.toml`, `.claude-plugin/plugin.json`
2. **Research conventions** — for the detected stack, research community-standard release practices (npm version, cargo release, Python versioning tools, etc.)
3. **Confirm with user** — present findings and proposed approach
4. **Generate compute-version.sh** — thin Bash wrapper that checks dependencies and delegates to Python
5. **Generate compute_version.py** — Python implementation using stdlib `json` + `tomllib` and `tomli_w` for TOML. Tailored to the project's version file locations.
6. **Generate release.yml** — GitHub Actions workflow: on push to main, create timestamp git tag (`YYYY-MM-DDTHHMMSSZ`), create GitHub Release with changelog content
7. **Register hooks** — add `check-version-bump.sh` and `check-changelog.sh` to the project's Claude Code hook configuration

The release infrastructure is part of the initial commit with passing CI. The generated scripts are project-specific — the skill generates them based on the detected stack, not from templates.

**Always use shell + Python implementation pattern.** Do not ask about implementation choice.

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
