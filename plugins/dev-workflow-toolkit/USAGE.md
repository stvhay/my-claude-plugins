# Usage

## Installation

```
/plugin marketplace add stvhay/my-claude-plugins
```

Select `dev-workflow-toolkit`. Also install `writing-toolkit` for full functionality.

## Workflow

Every change follows this process:

1. **File a GitHub issue** — `/project-init` sets up issue templates
2. **Create a branch** — `/using-git-worktrees` for isolation
3. **Brainstorm** — `/brainstorming` explores the problem space
4. **Plan** — `/writing-plans` produces a structured plan
5. **Execute** — `/executing-plans` or `/subagent-driven-development`
6. **Verify** — `/verification-before-completion` (auto-triggered)
7. **Review** — `/requesting-code-review` dispatches a reviewer
8. **Finish** — `/finishing-a-development-branch` (auto-triggered)

## Skill Quick Reference

### Auto-triggered

| Skill | When |
|---|---|
| `/verification-before-completion` | Before any completion claim |
| `/code-simplification` | After verification passes |
| `/finishing-a-development-branch` | When implementation is complete |

### Explicit invocation

| Skill | When |
|---|---|
| `/brainstorming` | Before creative work |
| `/writing-plans` | When you have requirements |
| `/executing-plans` | To execute a plan with checkpoints |
| `/subagent-driven-development` | For parallel multi-agent execution |
| `/dispatching-parallel-agents` | For independent parallel tasks |
| `/requesting-code-review` | Before submitting a PR |
| `/systematic-debugging` | When encountering bugs |
| `/using-git-worktrees` | For isolated workspaces |
| `/codify-subsystem` | To create subsystem specs |
| `/project-init` | To scaffold a new project |
| `/setup-rag` | To configure local-rag indexing |

## Background Reading

See `docs/architecture/` for design rationale:

- `agent-oriented-design.md` — Why agent-oriented workflows
- `context-optimization.md` — Managing context windows
- `spec-rationale.md` — Why subsystem specs matter
- `vsa-foundations.md` — Verified Software Architecture foundations
