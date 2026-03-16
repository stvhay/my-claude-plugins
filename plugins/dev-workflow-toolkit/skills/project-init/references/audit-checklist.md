# Project Init Audit Checklist

Machine-readable checklist for auditing an existing project against the
project-init skill's current output. The agent walks each item, evaluates
the project, and proposes fixes for failures.

## Severity Definitions

| Severity | Meaning |
|---|---|
| MISSING | Artifact does not exist at all |
| OUTDATED | Artifact exists but predates a structural change in the skill |
| DRIFT | Artifact exists but has diverged from the expected content |

---

## Scaffolding

### SCAFF-1: Bug report template

- **Layer:** Scaffolding
- **Check:** `.github/ISSUE_TEMPLATE/bug-report.yml` exists
- **Expected:** File present with structured YAML form fields
- **Severity when failing:** MISSING
- **Remediation:** Run project-init to generate the bug report template
- **Since:** v1.0.0

### SCAFF-2: Feature request template

- **Layer:** Scaffolding
- **Check:** `.github/ISSUE_TEMPLATE/feature-request.yml` exists
- **Expected:** File present with structured YAML form fields
- **Severity when failing:** MISSING
- **Remediation:** Run project-init to generate the feature request template
- **Since:** v1.0.0

### SCAFF-3: PR template

- **Layer:** Scaffolding
- **Check:** `.github/pull_request_template.md` exists
- **Expected:** File present with checklist sections
- **Severity when failing:** MISSING
- **Remediation:** Run project-init to generate the PR template
- **Since:** v1.0.0

### SCAFF-4: CONTRIBUTING.md

- **Layer:** Scaffolding
- **Check:** `CONTRIBUTING.md` exists at repo root
- **Expected:** File present with contribution workflow guide
- **Severity when failing:** MISSING
- **Remediation:** Run project-init to generate CONTRIBUTING.md
- **Since:** v1.0.0

### SCAFF-5: Plans directory

- **Layer:** Scaffolding
- **Check:** Plans directory exists (read `plansDirectory` from `.claude/settings.json`, default `~/.claude/plans/`)
- **Expected:** Directory present (may be empty)
- **Severity when failing:** MISSING
- **Remediation:** `PLANS_DIR=$(jq -r '.plansDirectory // "~/.claude/plans"' .claude/settings.json 2>/dev/null || echo ~/.claude/plans) && mkdir -p "$PLANS_DIR"`
- **Since:** v1.0.0 (updated v1.18.0 — configurable path)

---

## CLAUDE.md

### CLAUDE-1: CLAUDE.md exists

- **Layer:** CLAUDE.md
- **Check:** `CLAUDE.md` exists at repo root
- **Expected:** File present with project-specific configuration
- **Severity when failing:** MISSING
- **Remediation:** Run project-init to generate CLAUDE.md skeleton
- **Since:** v1.0.0

### CLAUDE-2: Workflow section

- **Layer:** CLAUDE.md
- **Check:** CLAUDE.md contains a `## Workflow` section
- **Expected:** Section present with numbered workflow steps (issue, develop, TDD, PRs, reference)
- **Severity when failing:** DRIFT
- **Remediation:** Add `## Workflow` section with standard steps
- **Since:** v1.0.0

### CLAUDE-3: No stale beads directive

- **Layer:** CLAUDE.md
- **Check:** CLAUDE.md does NOT contain a beads work-tracking directive (`bd`)
- **Expected:** No `## Work Tracking` section referencing `bd` (removed in v1.17.0)
- **Severity when failing:** OUTDATED
- **Remediation:** Remove `## Work Tracking` section that references beads/`bd`
- **Since:** v1.17.0

### CLAUDE-4: Writing Standards section

- **Layer:** CLAUDE.md
- **Check:** CLAUDE.md contains a `## Writing Standards` section
- **Expected:** Section present with style guidance (structured, no filler, dense)
- **Severity when failing:** DRIFT
- **Remediation:** Add `## Writing Standards` section
- **Since:** v1.0.0

### CLAUDE-5: Contributing section

- **Layer:** CLAUDE.md
- **Check:** CLAUDE.md contains a `## Contributing` section
- **Expected:** Section present referencing CONTRIBUTING.md
- **Severity when failing:** DRIFT
- **Remediation:** Add `## Contributing` section with link to CONTRIBUTING.md
- **Since:** v1.0.0

### CLAUDE-6: Lessons Learned section

- **Layer:** CLAUDE.md
- **Check:** CLAUDE.md contains a `## Lessons Learned` section referencing `finishing-a-development-branch`
- **Expected:** Section present with at least the finishing-a-development-branch documentation gate lesson
- **Severity when failing:** OUTDATED
- **Remediation:** Add `## Lessons Learned` section with finishing-a-development-branch directive
- **Since:** v1.9.0

---

## Release Infrastructure

### REL-1: compute-version.sh

- **Layer:** Release Infrastructure
- **Check:** `compute-version.sh` exists and is executable
- **Expected:** File present with execute permission; thin Bash wrapper delegating to Python
- **Severity when failing:** MISSING
- **Remediation:** Run project-init release infrastructure setup to generate compute-version.sh
- **Since:** v1.9.0

### REL-2: compute_version.py with --ci mode

- **Layer:** Release Infrastructure
- **Check:** `compute_version.py` exists with `--ci` mode support
- **Expected:** Python script with `--ci` flag that reads bump type from `<!-- bump: TYPE -->` and rewrites `## Unreleased` to versioned header
- **Severity when failing:** OUTDATED
- **Remediation:** Regenerate compute_version.py with `--ci` mode support
- **Since:** v1.9.0 (`--ci` since v1.14.0)

### REL-3: release.yml workflow

- **Layer:** Release Infrastructure
- **Check:** `.github/workflows/release.yml` exists with concurrency group and CI-driven version bumping
- **Expected:** Workflow with `concurrency: { group: version-bump, cancel-in-progress: false }` and CI-driven `compute-version.sh --ci --update` invocation
- **Severity when failing:** OUTDATED
- **Remediation:** Update release.yml to add concurrency group and CI-driven version bumping
- **Since:** v1.9.0 (concurrency + CI-driven since v1.14.0)

### REL-4: CI version-check job

- **Layer:** Release Infrastructure
- **Check:** `.github/workflows/ci.yml` contains a version-check job
- **Expected:** Pre-merge job validating `bump:TYPE` PR label matches `<!-- bump: TYPE -->` changelog comment
- **Severity when failing:** MISSING
- **Remediation:** Add version-check job to ci.yml workflow
- **Since:** v1.14.0

### REL-5: CHANGELOG.md with bump comment

- **Layer:** Release Infrastructure
- **Check:** `CHANGELOG.md` exists with `<!-- bump: TYPE -->` convention
- **Expected:** Changelog present; unreleased changes use `## Unreleased` header with `<!-- bump: patch|minor|major -->` comment
- **Severity when failing:** MISSING
- **Remediation:** Create CHANGELOG.md with `## Unreleased` section and bump comment
- **Since:** v1.5.0 (bump comment convention since v1.14.0)

---

## Spec Compliance

### SPEC-1: SPEC.md exists

- **Layer:** Spec Compliance
- **Check:** Each subsystem directory contains a `SPEC.md`
- **Expected:** SPEC.md present with Purpose, Invariants, Failure Modes, and Testing sections
- **Severity when failing:** MISSING
- **Remediation:** Run `codify-subsystem` to generate SPEC.md for each subsystem
- **Since:** v1.4.0

### SPEC-2: INV/FAIL sequential numbering

- **Layer:** Spec Compliance
- **Check:** Invariant IDs (INV-N) and Failure Mode IDs (FAIL-N) are sequentially numbered without gaps
- **Expected:** INV-1, INV-2, ... with no gaps; FAIL-1, FAIL-2, ... with no gaps
- **Severity when failing:** DRIFT
- **Remediation:** Renumber invariants and failure modes to eliminate gaps
- **Since:** v1.4.0

### SPEC-3: Cross-links resolve

- **Layer:** Spec Compliance
- **Check:** Cross-references between SPEC.md files and skill references resolve to existing files
- **Expected:** All referenced paths and skill names point to existing artifacts
- **Severity when failing:** DRIFT
- **Remediation:** Update or remove broken cross-references
- **Since:** v1.5.0

---

## Hooks

### HOOK-1: check-version-bump hook

- **Layer:** Hooks
- **Check:** `check-version-bump.sh` registered as a Claude Code hook
- **Expected:** Hook validates `## Unreleased` section and `<!-- bump: TYPE -->` comment on source changes
- **Severity when failing:** OUTDATED
- **Remediation:** Register check-version-bump.sh in Claude Code hook configuration
- **Since:** v1.9.0 (updated v1.14.0)

### HOOK-2: check-changelog hook

- **Layer:** Hooks
- **Check:** `check-changelog.sh` registered as a Claude Code hook
- **Expected:** Hook validates bump comment presence when `## Unreleased` section exists
- **Severity when failing:** OUTDATED
- **Remediation:** Register check-changelog.sh in Claude Code hook configuration
- **Since:** v1.9.0 (updated v1.14.0)

### HOOK-3: Quality gate SessionStart hook

- **Layer:** Hooks
- **Check:** Quality gate hook configured at plugin level (not stale project-level settings.json)
- **Expected:** Plugin-level hook triggers at SessionStart; no orphaned project-level quality gate in `.claude/settings.json`
- **Severity when failing:** OUTDATED
- **Remediation:** Remove stale quality gate from project settings.json; verify plugin-level hook is active
- **Since:** v1.5.0 (migrated v1.13.3)

### HOOK-4: Branch protection configured

- **Layer:** Hooks
- **Check:** `main` branch has protection rules requiring CI pass and squash merge
- **Expected:** Required status checks enabled; merge commits and rebase merges disabled
- **Severity when failing:** MISSING
- **Remediation:** Configure branch protection via `gh api` (see project-init SKILL.md Branch Protection section)
- **Since:** v1.11.0
