# my-claude-plugins

## Purpose

Personal Claude Code plugin marketplace. Plugins are developed here and
distributed via the Claude Code plugin system.

## Repository Structure

```
docs/
  ARCHITECTURE.md          # Architectural decisions and system structure
  DESIGN.md                # Design patterns and conventions
plugins/
  plugin-name/
    .claude-plugin/
      plugin.json          # Plugin manifest
    skills/
      SPEC.md              # Subsystem spec (VSA — agents walk up to find it)
      UPSTREAM-*.md        # Upstream provenance tracking
      skill-name/
        SKILL.md           # Skill definition (Agent Skills standard)
        references/        # Optional supporting docs
    README.md
```

## Plugin Format

Each plugin follows the [Claude Code plugin format](https://code.claude.com/docs/en/plugins):

- **`.claude-plugin/plugin.json`** — Plugin manifest with name, description, version
- **`skills/<name>/SKILL.md`** — Skills following the [Agent Skills standard](https://agentskills.io/specification)
- SKILL.md requires YAML frontmatter with at least `name` and `description`
- The `name` field must be lowercase, hyphenated, max 64 chars, and match the directory name

## Marketplace

`.claude-plugin/marketplace.json` at the repo root defines the plugin catalog.
Add each new plugin to the `plugins` array when it's ready for distribution.

Install via: `/plugin marketplace add stvhay/my-claude-plugins`

## Local Working Files

Plans and other working documents go under `.claude/` which is fully gitignored:

- **`.claude/plans/`** — Implementation plans (paste into PR body, not committed)

## Work Tracking

Use beads (`bd`) for all work tracking. Do not use Claude Code task lists.
Task titles follow the slug convention: `<slug>- <description>`.
If `bd` fails, stop and run `bd doctor`.

## Workflow

1. **Create GitHub issue** — All work starts with an issue
2. **Develop plugin** — Install dev-workflow-toolkit plugin for brainstorming, planning, and TDD workflows
3. **Follow TDD** — Write tests first
4. **Always create PRs** — Never commit directly to main
5. **Reference issue in PR** — Link back to the originating issue

## Writing Standards

- Structured with headers, bullet points, and blockquotes for key statements.
- No filler or padding. Dense, scannable, useful.

## Lessons Learned

- **Always use `finishing-a-development-branch` before creating PRs.** Its documentation gate (Step 2) validates README.md, ARCHITECTURE.md, and DESIGN.md against the changes. Skipping it leads to stale docs that must be patched post-merge (see heilmeier-catechism PR #42).

## Contributing

All changes go through pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md).
