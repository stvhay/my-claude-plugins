# stamp

STAMP-based systems analysis: safety (STPA), security (STPA-Sec), and incident investigation (CAST).

## Installation

```bash
# From marketplace
/plugin marketplace add stvhay/my-claude-plugins
/plugin install stamp@my-claude-plugins
```

## Skills

| Skill | Purpose |
|-------|---------|
| stamp-base | STAMP foundations and routing hub — directs to the right analysis method |
| stamp-stpa | Prospective hazard analysis using Systems-Theoretic Process Analysis |
| stamp-cast | Retrospective incident analysis using Causal Analysis based on STAMP |
| stamp-stpa-sec | Security threat modeling extending STPA with adversarial scenarios |

## Architecture

Hub-and-spoke pattern with bidirectional handoffs:

- **stamp-base** routes to the appropriate analysis skill based on context
- **stamp-stpa** and **stamp-cast** handle prospective and retrospective analysis
- **stamp-stpa-sec** extends STPA with security/adversarial scenarios
- Skills cross-reference each other by name for seamless handoffs

## License

Apache 2.0
