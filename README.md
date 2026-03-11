# my-claude-plugins

Personal Claude Code plugin marketplace.

## Usage

```bash
/plugin marketplace add stvhay/my-claude-plugins
/plugin install <plugin-name>@my-claude-plugins
```

## Plugins

| Plugin | Description |
|--------|-------------|
| [skill-creator](plugins/skill-creator/) | TDD-focused skill creator combining Anthropic's eval tooling with test-driven development philosophy |
| [stamp](plugins/stamp/) | STAMP-based systems analysis: safety (STPA), security (STPA-Sec), and incident investigation (CAST) |
| [ux-toolkit](plugins/ux-toolkit/) | UX design skills for agentic systems: design principles, delegation, approval, failure handling, trust calibration, and UX writing |
| [thinking-toolkit](plugins/thinking-toolkit/) | Thinking and reasoning skills: first-principles analysis, divergent ideation, and Heilmeier Catechism research evaluation |
| [writing-toolkit](plugins/writing-toolkit/) | Writing skills: Strunk's rules applied to any prose humans read |
| [multi-agent-toolkit](plugins/multi-agent-toolkit/) | Multi-agent coordination skills: council debates and parallel research |
| [redteam](plugins/redteam/) | Adversarial analysis with parallel agent deployment: stress-test ideas and produce content through competition |
| [dev-workflow-toolkit](plugins/dev-workflow-toolkit/) | Development workflow skills: brainstorming, planning, execution, debugging, testing, code review, project scaffolding, retrospective, and automated quality gates |

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — architectural decisions and system structure
- [Design](docs/DESIGN.md) — design patterns and conventions
- [Writing Conventions](docs/writing-conventions.md) — writing guidance for humans and LLMs
- Each plugin has a `skills/SPEC.md` — subsystem contracts with invariants and failure modes
- `scripts/quality-gate.sh` (in dev-workflow-toolkit) — automated structural validation

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
