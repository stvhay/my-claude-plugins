# Design Intent — what to preserve across iterations

These are the load-bearing ideas behind the `layer-theme` skill. If a future change would compromise one of these, push back hard.

> In the context of theming third-party HTML apps via userscripts, facing the risk that overconfident analytical reasoning replaces visual verification, we mechanically gate every visual claim on a fresh screenshot + Claude-Vision Read, accepting one extra Read tool call per iteration in exchange for the elimination of "I see it" hallucinations.

## Vision API > analytical reasoning

For any visual claim — alignment, contrast, "looks good now," "I see it" — require a freshly-rendered PNG and a Read of that PNG **in the same turn**. The overconfidence trap is named, mechanically gated (Iron Laws #3 and #4), and cited from Phase 5. **Don't soften.** Analytical reasoning about what a screenshot would show is *not* a substitute for actually loading it. The cost of one extra Read is ~zero; the cost of being wrong is the user typing *"why can't you see this?"* for the third time.

## Generality is a quality metric

Specific selectors are debt; class families and slot patterns are equity. Every site-specific selector — page IDs, `nth-child` indexes, single-element targets — is debt. The Phase 6 generality self-check exists because the original LuCI session converged on a complex solution before refactoring back to principles. **Don't let future iterations slide back.** A theme's quality is measured by how *few* and how *general* its rules are.

## Vendor real CSS, not approximations

Approximated CSS produces approximated bugs. Save upstream's stylesheet under `theme-vendor/` and link to it from your fixtures. Never approximate. (Iron Law #1.)

## Critique before patching

The Phase 3 critique document is the gate between *"user said something looks half-baked"* and writing selectors. Don't bypass. The critique converts symptoms into principles (saturation, weight tier, slot pattern, hover progression) and groups findings under them. Fix lists fall out of the principles, not the symptoms.

## Regression report = signal worth more than the bug

Every user-reported regression runs the 4-branch assessment from `templates/regression-assessment.md`, propagates as durable knowledge, and grows the test rig. Patches without classification waste the signal.

## The named-style catalog is the long-term value

Each finalized theme leaves behind a portable spec under `themes/<name>.md`. After 5–10 themes the catalog becomes a small palette / pattern library that makes new theming work ~50% faster. The catalog is the single most durable artifact this skill produces.
