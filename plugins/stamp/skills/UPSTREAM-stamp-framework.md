# Upstream Tracking: MIT STAMP Framework

This file tracks source material from the MIT STAMP (Systems-Theoretic Accident Model and Processes) framework.

## Source Material

| Source | Authors | Year | Used By |
|---|---|---|---|
| STPA Handbook | Leveson & Thomas | 2018 | stamp-stpa (primary methodology reference) |
| Engineering a Safer World, Ch. 11 | Leveson | 2011 | stamp-cast (CAST methodology), stamp-base (STAMP foundations) |
| STPA-Sec: Safety and Security Analysis | Young & Leveson | 2014 | stamp-stpa-sec (security extension methodology) |
| A New Accident Model for Engineering Safer Systems | Leveson | 2004 | stamp-base (STAMP theory foundations) |

## Adaptation Notes

The following adaptations differentiate this plugin from the source material:

- **Agentic checkpoints** — STPA and CAST skills include checkpoint prompts where
  the agent pauses to verify analysis completeness before proceeding. Not present
  in source material.
- **Framing conflict handling** — stamp-base detects when the initial routing
  decision was wrong and supports bidirectional handoffs between spokes.
  Source material treats methodologies as standalone.
- **Time pressure guidance** — Skills include guidance for abbreviated analysis
  under time constraints. Source material assumes full analysis.
- **depict notation** — Control structure diagrams use depict notation instead
  of the textbook diagram conventions. Enables text-based rendering in agent
  output.
- **STRIDE integration** — stamp-stpa-sec integrates Microsoft's STRIDE threat
  model for systematic attack vector enumeration. Not part of the original
  STPA-Sec paper.
- **@red path highlighting** — Flawed control paths are annotated with @red
  markers for visual emphasis. Plugin-specific convention.

## License Compliance

All source material is published academic work. The plugin implements original
analysis procedures inspired by the frameworks described in these publications.
No copyrighted text is reproduced. The STPA Handbook is freely available from
MIT Partnership for Systems Approaches to Safety and Security (PSASS).
