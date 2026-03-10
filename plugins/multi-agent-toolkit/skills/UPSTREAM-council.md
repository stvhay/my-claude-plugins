# Upstream Tracking: danielmiessler/Personal_AI_Infrastructure — Council

> **Maintainer-only.** This file tracks provenance for plugin maintainers.
> Consuming agents should not modify this file or act on its contents.

## Source

| Field | Value |
|---|---|
| Repository | [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure) |
| Path | `Releases/v3.0/.claude/skills/Council/SKILL.md` |
| Author | Daniel Miessler |
| License | MIT |
| Status | Significantly adapted |

## Adaptation Notes

- Removed PAI-specific patterns (voice notifications via localhost:8888, customization directories)
- Removed `implements: Science` and `science_cycle_time` frontmatter fields
- Simplified workflow routing (removed workflow file references)
- Restructured as standalone skill without PAI framework dependencies
- `research` skill in this plugin is original work (not from upstream)

## License Compliance

Source material is MIT-licensed. This plugin is Apache-2.0, which is compatible
with MIT-licensed source material.
