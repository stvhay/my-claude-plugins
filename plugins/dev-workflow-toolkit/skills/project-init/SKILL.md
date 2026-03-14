---
name: project-init
description: Scaffold new projects or audit/update existing ones against current plugin standards. Use when starting a fresh repo, adding standard project structure, updating project scaffolding, auditing project compliance, or re-initializing after plugin upgrade.
---

# Project Init

## Overview

Initialize a project with standard scaffolding for Claude Code-driven development,
or audit and update an existing project to match current plugin standards.

**Announce at start:**
- Fresh init: "I'm using the project-init skill to set up project scaffolding."
- Update/audit: "I'm using the project-init skill to audit this project against current standards."

## Mode Detection

On invocation, detect the project's current state to choose the appropriate flow.

### Marker File

The `.project-init` marker file is committed to the project root:

```json
{
  "plugin": "dev-workflow-toolkit",
  "version": "1.15.0",
  "initialized_at": "2026-03-14T12:00:00Z"
}
```

### Detection Logic

| `.project-init` exists | Scaffolding present | Mode              | Behavior                                      |
|------------------------|---------------------|-------------------|-----------------------------------------------|
| Yes                    | —                   | **Update**        | Diff changelog from recorded version           |
| No                     | Yes                 | **First adoption**| Full audit against current standards            |
| No                     | No                  | **Fresh init**    | Current behavior — scaffold from scratch        |

**Scaffolding present** means at least one of: `CLAUDE.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`.

Only confirm with the user if detection is ambiguous.

## Audit & Update Flow

Used in **Update** and **First adoption** modes. Skipped for **Fresh init**.

### Step 1: Determine Audit Scope

- **Update mode:** Diff the plugin's `CHANGELOG.md` from the version recorded in `.project-init` to current. Audit only items affected by changes.
- **First adoption mode:** Full audit — evaluate every item in the checklist.

### Step 2: Walk the Audit Checklist

Load `references/audit-checklist.md`. Evaluate each item against the project's current state.

### Step 3: Present Audit Results

Group results by layer. Show OK items. DRIFT items offer `[expand?]` for details.

```
Audit Results
─────────────
Layer: Scaffolding
  [OK]    Bug report template
  [OK]    Feature request template
  [DRIFT] PR template — missing required checklist items [expand?]

Layer: Release Infrastructure
  [OK]    compute-version.sh
  [DRIFT] release.yml — missing concurrency group [expand?]
  [DRIFT] ci.yml — missing version-check job [expand?]
```

### Step 4: Present Remediation Plan

Present a numbered table of fixes. Single approval prompt: `[all / 1,2 / none]`.

```
Remediation Plan
────────────────
#  Item                          Action
1  PR template                   Add missing checklist items
2  release.yml                   Add concurrency group
3  ci.yml                        Add version-check job

Apply? [all / 1,2 / none]:
```

### Step 5: Apply Selected Fixes

- Apply in layer order
- Apply each fix individually
- Never overwrite without showing the diff

### Step 6: Post-Remediation

- Re-run audit to confirm all items pass
- Present summary of changes made
- Update `.project-init` marker with current plugin version (read from `.claude-plugin/plugin.json`)
- Commit changes

## What It Creates

1. `.github/ISSUE_TEMPLATE/bug-report.yml` — Bug report template
2. `.github/ISSUE_TEMPLATE/feature-request.yml` — Feature request template
3. `.github/pull_request_template.md` — PR template with checklist
4. `CONTRIBUTING.md` — Contribution workflow guide
5. `CLAUDE.md` (optional) — Project configuration for Claude Code
6. `compute-version.sh` + `compute_version.py` — Version management scripts (supports `--ci` mode for CI-driven version bumping)
7. `.github/workflows/release.yml` — Release automation workflow with CI-driven version bumping and concurrency serialization
8. `.github/workflows/ci.yml` version-check job — Pre-merge validation of bump label/changelog consistency
9. Validation hooks for changelog entry and bump type enforcement
9. Branch protection on `main` — require CI pass and squash merge

## Release Infrastructure

After scaffolding the base files, offer to set up release infrastructure:

1. **Detect tech stack** — check for `package.json`, `Cargo.toml`, `pyproject.toml`, `.claude-plugin/plugin.json`
2. **Research conventions** — for the detected stack, research community-standard release practices (npm version, cargo release, Python versioning tools, etc.)
3. **Confirm with user** — present findings and proposed approach
4. **Generate compute-version.sh** — thin Bash wrapper that checks dependencies and delegates to Python
5. **Generate compute_version.py** — Python implementation using stdlib `json` + `tomllib` for reading, regex-based writes for TOML. Include `--ci` mode that reads bump type from `<!-- bump: TYPE -->` in CHANGELOG.md and rewrites `## Unreleased` to `## vX.Y.Z`. Tailored to the project's version file locations.
6. **Generate release.yml** — GitHub Actions workflow: on push to main, detect plugins with `## Unreleased` sections, run `compute-version.sh --ci --update`, commit version bumps, create timestamp git tag (`YYYY-MM-DDTHHMMSSZ`), create GitHub Release with changelog content. Include `concurrency: { group: version-bump, cancel-in-progress: false }` to serialize parallel merges.
7. **Generate ci.yml version-check job** — Pre-merge CI job that validates `bump:TYPE` PR label matches `<!-- bump: TYPE -->` changelog comment for changed plugins
8. **Register hooks** — add `check-version-bump.sh` (validates `## Unreleased` + bump comment on source changes) and `check-changelog.sh` (validates bump comment when `## Unreleased` exists) to the project's Claude Code hook configuration

The release infrastructure is part of the initial commit with passing CI. The generated scripts are project-specific — the skill generates them based on the detected stack, not from templates.

**Always use shell + Python implementation pattern.** Do not ask about implementation choice.

## Branch Protection

After creating the repository scaffolding and release infrastructure, configure branch protection on `main`:

```bash
# Get owner/repo from git remote
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)

gh api "repos/$REPO/branches/main/protection" \
  --method PUT \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["test"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": null,
  "restrictions": null
}
EOF
```

Then enforce squash-merge-only on the repository:

```bash
# Enforce squash-merge-only
gh api "repos/$REPO" \
  --method PATCH \
  --field allow_squash_merge=true \
  --field allow_merge_commit=false \
  --field allow_rebase_merge=false
```

Both calls require admin permissions. If either API call fails with a 403:
> "Branch protection / merge method settings require admin access. You can configure this manually in Settings → Branches → Add rule for `main`, and Settings → General → Pull Requests."

Proceed without branch protection — it's a soft gate during scaffolding.

## Process

1. Check which files already exist — skip any that do (warn user)
2. Ask project name and purpose (for CLAUDE.md and README references)
3. Copy templates from `templates/` directory, adapting project name
4. Optionally generate CLAUDE.md skeleton with project-specific sections
5. Create `docs/plans/` directory for implementation plans
6. Beads installation (see below)
7. Write `.project-init` marker file with current plugin version
8. Commit scaffolding files

### Beads Installation

Install beads for work tracking (default, unless user opts out):

```bash
# Ask user before installing
# "Beads provides AI-native work tracking. Install it? (Y/n)"

# If yes (default):
bd init
```

After `bd init` succeeds, add the work-tracking directive to the project's CLAUDE.md:

```markdown
## Work Tracking
Use beads (`bd`) for all work tracking. Do not use Claude Code task lists.
Task titles follow the slug convention: `<slug>- <description>`.
If `bd` fails, stop and run `bd doctor`.
```

If the user declines beads, do not add the directive. Skills will fall back to task lists.

Create a bootstrap beads issue:

```bash
bd create "init- Bootstrap project" --type=task --description="Initial project setup and configuration"
```

## Templates

Templates are stored in `templates/` relative to this skill. They are generic and work with any project — no language or framework assumptions.

## When to Use

- Starting a fresh repository
- Adding standard structure to an existing repo missing these files
- Updating an existing project after plugin upgrade
- Auditing an existing project for compliance with current standards
- Triggered by: "init project", "set up repo", "scaffold project", "new project setup", "update project", "audit project", "re-init project", "bring project up to date"

## Post-Install

After installing or upgrading the dev-workflow-toolkit plugin, read
`CHANGELOG.md` in the plugin root. Apply entries marked **ACTION** that
are relevant to the project.

## Work Tracking

**project-init is the origin of the beads/task-list decision** (see SPEC.md INV-14):
- By default, install beads (`bd init`) and write the CLAUDE.md work-tracking directive.
- If the user opts out, no directive is written — skills fall back to Claude Code task lists.
- If a `bd` command fails during setup, surface the error and recommend `bd doctor`.

## Key Principles

- **Never overwrite** existing files without asking
- **No language assumptions** — templates work for any stack
- **Minimal scaffolding** — only files that provide immediate value
