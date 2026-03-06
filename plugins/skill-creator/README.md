# skill-creator

TDD-focused skill creator combining Anthropic's eval tooling with test-driven development philosophy.

## Installation

```bash
# From marketplace
/plugin marketplace add stvhay/my-claude-plugins
/plugin install skill-creator@my-claude-plugins
```

## What This Plugin Does

Layers TDD methodology onto Anthropic's official skill-creator:

- **Iron Law:** No skill without a failing test first
- **RED-GREEN-REFACTOR** applied to documentation
- **Eval tooling:** Benchmarking, description optimization, blind comparison
- **Rationalization bulletproofing:** Pressure testing for discipline-enforcing skills

## Architecture

Three-file layer:
- `SKILL.md` — Entrypoint: TDD philosophy + traffic director
- `references/upstream.md` — Snapshot of Anthropic's official skill-creator
- `references/writing-skills.md` — Snapshot of obra/superpowers writing-skills

## Upstream Sources

See `skills/skill-creator/UPSTREAM.md` for provenance tracking and sync instructions.

## License

Apache 2.0 (all components — Anthropic upstream is Apache 2.0; obra/superpowers MIT content is forward-compatible)
