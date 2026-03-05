# my-claude-plugins

## Purpose

Personal Claude Code plugin marketplace. Plugins are developed here and
distributed via the Claude Code plugin system.

## Repository Structure

```
plugins/
  plugin-name/
    .claude-plugin/
      plugin.json          # Plugin manifest
    skills/
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

<!-- Add project-specific lessons as they arise. -->

## Contributing

All changes go through pull requests. See [CONTRIBUTING.md](CONTRIBUTING.md).
