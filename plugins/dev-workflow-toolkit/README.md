# dev-workflow-toolkit

Development workflow skills for Claude Code. Replaces [claude-gh-project-template](https://github.com/stvhay/claude-gh-project-template) as a distributable plugin.

## Installation

```
/plugin marketplace add stvhay/my-claude-plugins
```

Select `dev-workflow-toolkit` from the plugin list.

**Recommended companion:** Install `writing-toolkit` for the `writing-clearly-and-concisely` skill referenced by several workflow skills.

## Skills (17)

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

**Terminal states:** Skills that don't invoke others: `receiving-code-review`, `code-simplification`, `retrospective`

## Testing

Run the test suite:
```bash
cd plugins/dev-workflow-toolkit
./tests/run-all.sh
```

**72 tests** validate:
- YAML frontmatter in all SKILL.md files (16 tests)
- Template structure and content (10 tests)
- RAG configuration generation logic (11 tests)
- Skill invocation and dependency resolution (35 tests)
- Template path resolution and substitution
- MCP server configuration patterns

See `tests/README.md` for details.

## Documentation

- `docs/architecture/` — Design rationale and foundations
- `docs/spec-template.md` — Template for subsystem specs
- `docs/FIRST_RUN.md` — Project memory initialization

## Attribution

- Skills derived from [obra/superpowers](https://github.com/obra/superpowers) (MIT License)
- `writing-clearly-and-concisely` based on Strunk's *Elements of Style* (1918, public domain) — in `writing-toolkit` plugin

## License

Apache-2.0
