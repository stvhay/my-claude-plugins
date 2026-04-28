# Skills Subsystem

## Purpose

The web-ui-theming-tampermonkey skills directory provides one skill: `layer-theme`. It encodes a phased workflow for layering themes onto existing HTML applications you don't own — dark mode, brand re-tone, density adjustments — delivered as a userscript (Tampermonkey/Greasemonkey/Stylus) or a UserStyle.

The key design decision: themes are produced **archaeologically + visually** — read the upstream designer's intent from CSS variables and class names, override at the right tier, and verify with screenshots that respect the underlying UX hierarchy rather than patching individual selectors. Quality is measured by how *few* and *general* the resulting rules are.

## Core Mechanism

A six-phase workflow gated by nine "Iron Laws" that turn visual claims from analytical reasoning into mechanical verification: vendor the upstream CSS, study the design tokens before writing selectors, render every iteration with Playwright, and Read the resulting PNG via Claude Vision before claiming a visual outcome. The named-style catalog (`themes/`) accumulates portable theme specs for reuse on future sites.

**Key files:**
- `layer-theme/SKILL.md` — Iron Laws + 6-phase workflow (intent → acquire → study → fixture rig → iterate-with-vision → finalize-and-name)
- `layer-theme/scripts/screenshot.py` — Playwright harness with V8 syntax pre-check, GM_addStyle polyfill, interactive states
- `layer-theme/scripts/contrast.py` — Element-level WCAG AA contrast check via Playwright
- `layer-theme/references/upstream-acquisition.md` — How to vendor real upstream CSS (3 modes, including how to ask the user for assets)
- `layer-theme/references/design-principles.md` — Generality, tokens, slot patterns, stacking-context traps
- `layer-theme/references/vision-verification.md` — Overconfidence-trap protocol, per-state checklist
- `layer-theme/references/existing-themes.md` — userstyles.world, Greasy Fork, palette ports
- `layer-theme/templates/userscript.user.js` — Two-tier override skeleton with slot patterns
- `layer-theme/templates/fixture.html` — Representative fixture with declared interactive states
- `layer-theme/templates/critique.md` — Phase 3 design-brief
- `layer-theme/templates/theme-spec.md` — Named-style template
- `layer-theme/templates/regression-assessment.md` — 4-branch self-improvement loop
- `layer-theme/themes/` — Catalog of finalized named styles (`luci-dark-material.md` is the first)

## Public Interface

| Export | Used By | Contract |
|---|---|---|
| YAML frontmatter `name: layer-theme` | Claude Code skill router | Unique, lowercase, matches directory name |
| Phase 6 finalize step | The user, on completion | Produces a named theme spec under `themes/<name>.md` |
| `themes/<name>.md` references | Future invocations like "apply the luci-dark-material style to grafana" | Self-contained palette + pattern library, readable by future skill invocations |

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | SKILL.md has valid YAML frontmatter with `name: layer-theme` and a non-empty `description` | structural | Claude Code cannot discover skills without frontmatter |
| INV-2 | Visual claims must be backed by a freshly-rendered screenshot AND a Claude-Vision Read of that PNG in the same turn | reasoning-required | The "overconfidence trap" — analytical reasoning about CSS rules silently misrepresents visual outcomes (Iron Laws #3 + #4) |
| INV-3 | Vendor real upstream CSS into `theme-vendor/`; never approximate | reasoning-required | Approximated CSS produces approximated bugs (Iron Law #1) |
| INV-4 | Phase 3 critique document exists before Phase 4 selectors are written | reasoning-required | A critique converts "this looks half-baked" into principles before tactics; bypassing produces whack-a-mole rules |
| INV-5 | Themes prefer class families and slot patterns over `nth-child` / single-ID selectors | reasoning-required | Specific selectors are debt; generality is a quality metric (Iron Law #9) |

**Enforcement classification:**
- **structural** — enforced by test suite or directory convention
- **reasoning-required** — needs architectural understanding; verified during code review or skill behavior

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | Skill not triggered when user asks for theming work | Missing or malformed YAML frontmatter | Add `---` fenced frontmatter with `name: layer-theme` and a `description` |
| FAIL-2 | "Looks good now" claimed without a fresh PNG read | Iron Law #4 violated; INV-2 unmet | Run `scripts/screenshot.py`, then Read the resulting PNG in the same turn before claiming a visual outcome |
| FAIL-3 | Hover tooltip / dropdown clipped after applying `filter:` to parent | Stacking-context trap (Iron Law #7) | Prefer `color-mix()` on `background-color` over filter-based desaturation |
| FAIL-4 | Theme passes page-level contrast but fails on individual buttons | Background mismatch (Iron Law #8) | Compare each text node's computed color to its actual rendered background, not the page bg |
| FAIL-5 | User reports "I'm still on 0.1.5" when 0.1.6 was just deployed | Browser / userscript-manager / gist CDN cache | Bump version, append `?v=N` to raw URLs, force-update (Iron Law #5) |
| FAIL-6 | Screenshot looks identical to the unstyled fixture | Stray backtick / template-literal syntax error in userscript | Run `scripts/screenshot.py` V8 pre-check before claiming the userscript runs (Iron Law #6) |

## Decision Framework

| Situation | Action | Invariant |
|---|---|---|
| User asks for dark mode / re-theme of an existing third-party site | Use layer-theme | — |
| User references a previously named saved style ("apply the luci-dark-material style to X") | Use layer-theme; read the named spec under `themes/<name>.md` first | — |
| User wants to author a design system inside a codebase they own | Skip — this skill is for sites you don't own | — |
| About to claim "this looks fixed" | Render fresh PNG via `screenshot.py`, Read it before responding | INV-2 |
| About to add a third `nth-child` selector | Stop, write a Phase 3 critique, refactor to class families | INV-4, INV-5 |
| Adding a `filter:` rule to a parent of an interactive element | Switch to `color-mix()` on `background-color` | (Iron Law #7) |

## Testing

**Traceability:** INV-1 — structural — enforced by frontmatter validation in the dev-workflow-toolkit `quality-gate.sh` (`skill-structure` check). INV-2 through INV-5 — reasoning-required — enforced by the skill's Iron Laws and Phase gates; verified during code review and by repeated invocation against real third-party sites.

Validate via manual invocation: trigger `layer-theme` against a real site, walk through the 6 phases, verify each Iron Law gate fires (no visual claim without a PNG read; no selectors before Phase 3 critique; no claim that a JS change "works" without a post-change PNG).

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code skill router | external | N/A — built into Claude Code runtime |
| Read tool (Claude Code) | external | required for INV-2 PNG reads |
| Playwright (Python) | external | runtime dependency, installed per-project |
| Tampermonkey / Greasemonkey / Stylus | external | end-user-installed userscript managers; not consumed by the skill itself |
