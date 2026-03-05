# UX Toolkit

UX design skills for agentic systems and user-facing interfaces.

## Skills

| Skill | Purpose |
|-------|---------|
| **ux-design-agent** | Full UX design process: requirements, user model, modality selection |
| **design-principles** | GUI design standards for dashboards, admin UIs, SaaS products |
| **delegation-oversight** | Human-AI handoff: when the agent should ask vs. act |
| **approval-confirmation** | Approval UI for informed consent in agentic systems |
| **failure-choreography** | Graceful failure with preserved state and human handoff |
| **trust-calibration** | Communicating agent confidence calibrated to evidence |
| **ux-writing** | Interface copy: buttons, labels, errors, notifications |
| **writing-clearly-and-concisely** | Strunk's rules applied to any prose humans read |

## Skill Coordination

`ux-design-agent` orchestrates the others based on modality:

- **GUI** -> `design-principles` -> implementation
- **Agentic** -> `delegation-oversight` -> `approval-confirmation` / `failure-choreography`
- **All modalities** use `trust-calibration`, `ux-writing`, and `writing-clearly-and-concisely` as technique skills

## Install

```
/plugin marketplace add stvhay/my-claude-plugins
```
