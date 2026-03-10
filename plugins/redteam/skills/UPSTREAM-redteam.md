# Upstream Tracking: danielmiessler/Personal_AI_Infrastructure — RedTeam

> **Maintainer-only.** This file tracks provenance for plugin maintainers.
> Consuming agents should not modify this file or act on its contents.

## Source

| Field | Value |
|---|---|
| Repository | [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure) |
| Path | `Releases/v3.0/.claude/skills/RedTeam/SKILL.md` |
| Author | Daniel Miessler |
| License | MIT |
| Status | Significantly adapted |

## Adaptation Notes

- Removed PAI-specific patterns (voice notifications via localhost:8888, customization directories)
- Removed `SkillSearch()` references and PAI framework integration
- Restructured as standalone skill without PAI framework dependencies
- Reduced from 32 agents to focused adversarial analysis approach

## License Compliance

Source material is MIT-licensed. This plugin is Apache-2.0, which is compatible
with MIT-licensed source material.
