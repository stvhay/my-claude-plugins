# Changelog

## 0.1.0 — 2026-04-27

Initial release. Distilled from the LuCI Material Dark Mode project
(`luci-material-dark-mode/`, sessions 8cc01486 / d3719986 / fa30cf91 /
bcd213ff on 2026-04-26).

- `layer-theme` skill: 6-phase workflow (intent → acquire → study → fixture
  rig → iterate-with-vision → finalize-and-name).
- References: `upstream-acquisition.md`, `design-principles.md`,
  `vision-verification.md`, `existing-themes.md`.
- Reusable Playwright screenshot rig parameterized for any site.
- First named style: `themes/luci-dark-material.md`.
- Plugin renamed from `web-ui-theming` to `web-ui-theming-tampermonkey` on incorporation, reserving the `web-ui-theming-*` namespace for future delivery-target siblings (e.g. Stylus-only, browser-extension).
- Added plugin-level `DESIGN.md` (load-bearing intent extracted from the now-removed `TURNOVER.md`).
- Added `skills/SPEC.md`.
