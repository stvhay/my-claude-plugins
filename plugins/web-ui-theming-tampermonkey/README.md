# web-ui-theming-tampermonkey

Claude Code plugin for layering themes onto existing HTML applications.

Single skill: **`layer-theme`**. Output: a Tampermonkey/Greasemonkey/Stylus
userscript (or plain CSS) that re-tones a site without touching its source.

## What it gives Claude

- A phased workflow that **studies upstream design intent** before writing
  selectors — so the result expresses general UX principles instead of
  whack-a-moling individual components.
- A **screenshot + Claude Vision** verification rig (`scripts/screenshot.py`)
  that reuses real vendored CSS, so visual tests run against production CSS
  without needing the live site.
- A **named-style catalog** (`skills/layer-theme/themes/`) — once a visual
  style is finalized for one site, it can be referenced by name when theming
  another.
- Reference docs covering: source acquisition (including how to ask the user
  to grab assets when the source isn't reachable), the contrast / alignment
  / weight / stacking-context checklist that the LuCI work surfaced as
  load-bearing, vision-verification protocol with cache-busting, and existing
  popular-theme sources (Stylus, userstyles.world) to reverse-engineer.

## Install

This plugin lives in `plugins/web-ui-theming-tampermonkey/`. To install via the
my-claude-plugins marketplace, copy the directory into
`marketplaces/my-claude-plugins/plugins/` and add an entry to that
marketplace's plugin index, then `/plugin install web-ui-theming-tampermonkey@my-claude-plugins`.

## Provenance

Distilled from a single day of work building `dark-mode.user.js` for OpenWrt's
LuCI Material theme (April 2026, 4 sessions, ~4h). See `CHANGELOG.md`.

## License

Apache 2.0.
