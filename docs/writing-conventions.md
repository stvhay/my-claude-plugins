# Writing Conventions

> Standalone writing guidance for both human readers and LLM agents. Skills
> pass this document to `/writing-clearly-and-concisely` as additional context.

## Invocation

When a skill produces written output (design docs, plans, SPEC.md files,
documentation updates), reference this document:

> Apply `/writing-clearly-and-concisely` with additional guidance from
> `docs/writing-conventions.md`

## Design Documents

- **Maximum 500-1000 lines.** If longer, split into linked design docs.
- Dense and scannable. No filler, no padding.

## LLM-Friendly Structure

These conventions help agents parse and act on documents reliably:

- **Consistent headers.** Agents jump to sections by name. Use the same
  header names across documents of the same type.
- **Tables over prose** for structured data — check lists, file mappings,
  invariant tables, dependency lists.
- **Explicit "Key Decisions" blocks.** Agents need to know what's settled
  vs what's open. Mark decisions clearly.
- **No ambiguous references.** Use full file paths or skill names, not
  "the script" or "the file." If a path could be project-relative or
  plugin-relative, say which.
- **Categorization markers.** Use explicit labels agents can act on:
  `project-local` vs `upstream`, `structural` vs `reasoning-required`,
  `high/medium/low` severity.

## Human Readability

- Structured with headers, bullet points, and blockquotes for key statements.
- Alexandrian prologues for quick scanning:
  > In the context of [X], facing [Y], we decided [Z], accepting [Q].
- No filler or padding. Dense, scannable, useful.

## Document-Specific Guidelines

| Document Type | Length | Notes |
|--------------|--------|-------|
| SPEC.md | 80-350 lines | Subsystem contracts; loaded repeatedly by agents |
| SKILL.md | Under 500 lines | Heavy reference in separate files |
| Design docs | 500-1000 lines | Split if longer |
| ARCHITECTURE.md | No hard cap | Keep sections focused |
| DESIGN.md | No hard cap | Keep sections focused |
| Plans | Sized to tasks | Each task fits ~50% of subagent context |
