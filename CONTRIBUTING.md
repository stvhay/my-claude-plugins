# Contributing

## Adding a Plugin

1. **File a GitHub issue** describing the plugin's purpose
2. **Create a branch** for the new plugin
3. **Scaffold the plugin directory:**

```
plugins/my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── SPEC.md
│   └── my-skill/
│       └── SKILL.md
└── README.md
```

4. **Write `plugin.json`:**

```json
{
  "name": "my-plugin",
  "description": "What this plugin does",
  "version": "1.0.0",
  "author": { "name": "stvhay" },
  "license": "MIT"
}
```

5. **Write `SKILL.md`** with required frontmatter:

```yaml
---
name: my-skill
description: What this skill does and when to use it.
---
```

6. **Register in marketplace** — Add the plugin to `.claude-plugin/marketplace.json`
7. **Open a PR** linking to the issue

## Modifying a Plugin

1. File an issue or reference an existing one
2. Branch, make changes, open a PR
3. Bump the version in `plugin.json`

## Standards

- Plugin names: lowercase, hyphenated
- Skill `name` field must match its directory name
- Every PR links to an issue
- Every plugin must have a `skills/SPEC.md` following the [spec template](plugins/dev-workflow-toolkit/docs/spec-template.md)
- Plugins derived from external sources must include `UPSTREAM-*.md` provenance tracking
- Structural changes must be reflected in [ARCHITECTURE.md](docs/ARCHITECTURE.md) or [DESIGN.md](docs/DESIGN.md)
