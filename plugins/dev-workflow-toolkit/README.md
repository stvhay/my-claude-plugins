# dev-workflow-toolkit

Development workflow skills for Claude Code. Replaces [claude-gh-project-template](https://github.com/stvhay/claude-gh-project-template) as a distributable plugin.

## Installation

```
/plugin marketplace add stvhay/my-claude-plugins
```

Select `dev-workflow-toolkit` from the plugin list.

**Prerequisites:** [uv](https://docs.astral.sh/uv/) (for quality gate checks). Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Recommended companion:** Install `writing-toolkit` for the `writing-clearly-and-concisely` skill referenced by several workflow skills.

## Skills (18)[^stat-skill-count]

### Workflow

| Skill | Description |
|---|---|
| `brainstorming` | Ideation and design workflow — explores alternatives before committing |
| `writing-plans` | Create detailed, self-contained implementation plans |
| `executing-plans` | Execute plans with checkpoints between tasks |
| `subagent-driven-development` | Multi-agent plan execution with two-stage review |
| `dispatching-parallel-agents` | Run independent tasks in parallel |
| `project-init` | Scaffold new projects with GitHub templates and CONTRIBUTING.md |
| `setup-rag` | Configure local-rag for project-isolated RAG indexing |

### Quality

| Skill | Description |
|---|---|
| `test-driven-development` | TDD workflow with anti-pattern guidance |
| `systematic-debugging` | Structured debugging with root-cause tracing |
| `code-simplification` | Post-verification code cleanup pipeline |
| `verification-before-completion` | Pre-completion verification gates |
| `documentation-standards` | Validate and draft project documentation updates |

### Code Review

| Skill | Description |
|---|---|
| `requesting-code-review` | Dispatch structured code review |
| `receiving-code-review` | Handle incoming review feedback |

### Project Management

| Skill | Description |
|---|---|
| `using-git-worktrees` | Create isolated workspaces |
| `finishing-a-development-branch` | Branch completion — merge, PR, or cleanup |
| `codify-subsystem` | Encode subsystem knowledge as SPEC.md |
| `retrospective` | Post-completion session analysis and upstream feedback |

## Hooks

The plugin registers hooks via `hooks/hooks.json` for Langfuse tracing:

| Hook Event | What It Ships |
|---|---|
| `SessionStart` | Creates trace with name, session_id (git branch), tags |
| `SessionStart` | Ensures `post-checkout` git hook is installed for direnv worktree initialization |
| `PostToolUse` / `PostToolUseFailure` | LLM generations (model, tokens, cost) + tool observations |
| `SubagentStop` | Parent agent span with nested observations |
| `SessionEnd` | Summary span with totals; cleans up state |

**Setup:** Set `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, and `LANGFUSE_SOURCE_PROJECT` env vars. The hook bootstraps its own venv at `~/.cache/langfuse-hook/venv/` on first run.

## Skill Dependencies

Skills invoke other skills to create workflow orchestration. This prevents circular invocations:

```
brainstorming (entry)
  └─> using-git-worktrees (pre-flight, if on main)
  └─> documentation-standards (draft mode, after design approval)
  └─> ux-design-agent* (optional, for user-facing/agentic designs)
  └─> writing-plans (terminal state)
       └─> executing-plans OR subagent-driven-development
            └─> test-driven-development (during implementation)
            └─> systematic-debugging (when bugs occur)
            └─> verification-before-completion (before completion)
                 └─> quality-gate.sh (structural checks)
                 └─> code-simplification (after verification passes)
            └─> finishing-a-development-branch (after implementation)
                 └─> documentation-standards (validate mode, hard gate)
                 └─> quality-gate.sh (structural checks)
                 └─> retrospective (after PR, non-blocking)

requesting-code-review (parallel workflow)
  └─> code-reviewer agent (separate invocation)

codify-subsystem (standalone)
project-init (standalone)
setup-rag (standalone)
dispatching-parallel-agents (standalone)
```

**\* External dependency:** ux-design-agent is in the ux-toolkit plugin

**Terminal states:** Skills that don't invoke others: `test-driven-development`, `systematic-debugging`, `using-git-worktrees`, `documentation-standards`, `code-simplification`, `retrospective`, `receiving-code-review`

## Testing

Run the test suite:
```bash
cd plugins/dev-workflow-toolkit
./tests/run-all.sh
```

**110 tests**[^stat-test-count] across 4 modules[^stat-suite-count]:
- Structure — frontmatter validation, SPEC.md checks, project-init templates, setup-rag config, cross-plugin validation
- Integration — skill loading, dependency resolution, trigger patterns, reference files
- Quality gate — smoke tests, negative fixtures, doc-stats validation
- Direnv hooks — post-checkout behavior, SessionStart installer, idempotency, trust inheritance

See `tests/README.md` for details.

## Documentation

- `docs/architecture/` — Design rationale and foundations
- `docs/FIRST_RUN.md` — Project memory initialization
- `scripts/quality-gate.sh` — Structural validation (requires uv)

## Attribution

- Skills derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT License)
- `writing-clearly-and-concisely` based on Strunk's *Elements of Style* (1918, public domain) — in `writing-toolkit` plugin

## License

Apache-2.0

[^stat-skill-count]: stat-check: skill-count
[^stat-test-count]: stat-check: total-test-count
[^stat-suite-count]: stat-check: test-suite-count
