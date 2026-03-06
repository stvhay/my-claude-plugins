# Upstream Sources

This plugin layers two upstream sources into a unified skill-creator.

## Anthropic Official skill-creator

- **Source:** `~/.claude/plugins/cache/claude-plugins-official/skill-creator/`
- **Snapshot:** `references/upstream.md`
- **Commit:** `205b6e0b30366a969412d9aab7b99bea99d58db1`
- **License:** Apache 2.0 (see `LICENSE.txt`)
- **Copied files:** `agents/`, `assets/`, `eval-viewer/`, `references/`, `scripts/`

## obra/superpowers writing-skills

- **Source:** https://github.com/obra/superpowers
- **Snapshot:** `references/writing-skills.md`
- **Last synced:** `e4a2375cb705ca5800f0833528ce36a3faf9017a` (2026-02-21)
- **License:** MIT
- **Copied files:** `writing-skills-refs/` (persuasion-principles.md, testing-skills-with-subagents.md, graphviz-conventions.dot, render-graphs.js)
- **Dropped:** `anthropic-best-practices.md` (redundant with references/upstream.md)

## How to Sync

### Anthropic skill-creator

1. Check `~/.claude/plugins/cache/claude-plugins-official/skill-creator/` for new version
2. Diff the new SKILL.md against `references/upstream.md`:
   ```bash
   diff references/upstream.md ~/.claude/plugins/cache/claude-plugins-official/skill-creator/<new-version>/skills/skill-creator/SKILL.md
   ```
3. Update `references/upstream.md` with new content
4. Copy updated tooling directories (scripts/, agents/, etc.)
5. Review `SKILL.md` cross-references — section names may have changed
6. Update commit SHA in this file

### obra/superpowers writing-skills

1. Clone upstream:
   ```bash
   git clone --depth 1 https://github.com/obra/superpowers.git /tmp/superpowers
   ```
2. Diff against snapshot:
   ```bash
   diff references/writing-skills.md /tmp/superpowers/skills/writing-skills/SKILL.md
   ```
3. Diff reference files:
   ```bash
   diff -r writing-skills-refs/ /tmp/superpowers/skills/writing-skills/ --exclude=anthropic-best-practices.md --exclude=examples --exclude=SKILL.md
   ```
4. Update snapshots
5. Strip `superpowers:` prefix from any new cross-references
6. Update commit SHA in this file
