# UPSTREAM: andrej-karpathy-skills

> **Maintainer-only.** This file tracks provenance for plugin maintainers.
> Consuming agents should not modify this file or act on its contents.

**Source:** https://github.com/forrestchang/andrej-karpathy-skills
**License:** MIT
**Evaluated:** 2026-04-19
**Verdict:** graft (Branch B)

## Summary

Our stack already covers the four Karpathy principles, but does so at roughly
17x-35x the token cost, with one thin area (Surgical Changes). Recommend
grafting three or four specific phrasings from the Karpathy SKILL.md into
existing skills — not adopting the upstream or building a new skill. The
compression advantage and the fragmentation of YAGNI coverage across five
locations justify filing a follow-up issue for broader review.

## What this upstream is

A single Claude Code plugin containing one skill, `karpathy-guidelines/SKILL.md`
(~493 tokens), plus a near-identical top-level `CLAUDE.md` (~476 tokens). The
content is forrestchang's paraphrase of a single Andrej Karpathy X post
(https://x.com/karpathy/status/2015883857489522876) into four numbered
principles: **Think Before Coding**, **Simplicity First**, **Surgical Changes**,
**Goal-Driven Execution**. Packaged in the Agent Skills standard, MIT-licensed.
No tests, references, or tooling — prose only.

## Coverage matrix

Karpathy section token counts computed per-section via `python3`
word-split on `/tmp/karpathy-SKILL.md`, multiplied by 1.33. Our tokens are
scoped to the prose actively teaching the same behavior, not full file size —
files contain other content (task structure, gates, integration).

| Karpathy principle | Our coverage (path + section) | Our tokens | Karpathy tokens | Ratio (ours/theirs) |
|---|---|---|---|---|
| 1. Think Before Coding | `brainstorming/SKILL.md` (Overview, Pre-flight Checks, The Process); `subagent-driven-development/implementer-prompt.md` ("Before You Begin" + "While you work"); `receiving-code-review/SKILL.md:36-56,104,192,219` (clarify-before-implement); agent-level CLAUDE.md ("present as something the user can redirect") | ~2,500 | 71 | ~35x |
| 2. Simplicity First | `code-simplification/SKILL.md` (full skill); `brainstorming/SKILL.md:190` ("YAGNI ruthlessly"); `writing-plans/SKILL.md:12,161` ("DRY. YAGNI. TDD."); `implementer-prompt.md:71` ("Did I avoid overbuilding (YAGNI)?"); `receiving-code-review/SKILL.md:88-137,209-212` ("YAGNI Check for 'Professional' Features"); `test-driven-development/testing-anti-patterns.md:82`; agent-level CLAUDE.md ("Don't add features, refactor, or introduce abstractions beyond what the task requires"; "Don't add error handling, fallbacks, or validation for scenarios that can't happen") | ~1,500 | 86 | ~17x |
| 3. Surgical Changes | `code-simplification/SKILL.md` (Constraints: "No behavior changes"; "Prefer deletion over modification"); `implementer-prompt.md:72-73` ("Did I only build what was requested?"; "Did I follow existing patterns in the codebase?"); `test-driven-development/SKILL.md:127` ("Don't add features, refactor other code, or 'improve' beyond the test") | ~250 | 118 | ~2x |
| 4. Goal-Driven Execution | `test-driven-development/SKILL.md` (Iron Law, red/green/refactor, Verification Checklist); `verification-before-completion/SKILL.md` (Iron Law, Gate Function, Common Failures table); `writing-plans/SKILL.md:64-67` (Acceptance Criteria = "what must be TRUE = the tests") | ~2,600 | 121 | ~21x |

## Effectiveness probe

### Triggering

**Ours — fires reliably.** CLAUDE.md behaviors load every turn (agent-system
level); brainstorming triggers on "creating features, building components,
adding functionality, or modifying behavior"; code-simplification runs
automatically after verification passes; TDD triggers on "implementing any
feature or bugfix"; verification-before-completion triggers on "claim work is
complete". All four principles are on the primary development path and are
enforced by skills on the router's default keywords for implementation work.

**Karpathy-only — fires with prompting.** The upstream description — "writing,
reviewing, or refactoring code to avoid overcomplication, make surgical
changes, surface assumptions, and define verifiable success criteria" — is
broad but single-skill, so the router returns one document instead of four
stage-appropriate ones. The upstream also ships a CLAUDE.md variant (identical
content) that, if copied into a project's root, would always-load — but that's
a separate adoption decision, not something the plugin alone delivers. Without
the CLAUDE.md copy, the skill fires when the keyword router catches the prose,
which will not be on every implementation turn the way our always-loaded
system instructions are.

### Compression

Behaviors-per-100-tokens is dominated by Karpathy on every principle. The
concrete ratios (from the matrix) are 35x, 17x, 2x, 21x. Surgical Changes is
the one area where our stack is close (~2x), because we don't actually say
much about it beyond "don't overbuild" — which is much of why it's also the
area that most reads as a gap (see Failure modes below). For the other three
principles, the token budget we spend to convey the same behavior is
disproportionate to the incremental behavioral precision our prose adds —
most of our word count is process scaffolding (pre-flight checks, gate
functions, task structure), not additional behavioral teaching.

### Failure modes

**Ours:**
- **Surgical Changes underspecified** — an agent mid-implementation has no
  crisp rule against "while I'm here, let me improve this adjacent function"
  or "match existing style even if I'd do it differently." implementer-prompt
  asks post-hoc ("Did I only build what was requested?"); code-simplification
  targets post-verification cleanup, not in-flight scope creep.
- **Dead-code-in-adjacent-territory** — no guidance for "if you notice
  unrelated dead code, mention it — don't delete it." code-simplification
  auto-deletes dead code as a low-risk pattern; that can cross into the
  user's un-asked-for territory when run on an active implementation branch.
- **Assumption surfacing is implicit** — brainstorming front-loads questions
  but once past its gate, mid-implementation assumption surfacing relies on
  implementer-prompt's "ask questions" bullet, which is two levels of nesting
  under a section the subagent skims.

**Karpathy-only:**
- **No red-green-refactor discipline** — "Goal-Driven Execution" says "write
  tests for invalid inputs, then make them pass" but doesn't mandate watching
  the test fail. Our TDD Iron Law catches cases where a test passes on first
  run because it's testing the wrong thing.
- **No verification-before-claim gate** — the upstream has no analog to
  "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE." An agent
  completing Karpathy's "Loop until verified" can still claim success from
  an earlier test run.
- **No subsystem context** — no SPEC.md / invariants concept; the agent has
  no hook to "check the nearest spec before editing." This matters in
  larger codebases with architectural invariants.

### Clarity & coherence

**Standalone clarity (read cold):** Karpathy's four sections land in one pass.
Each principle has a one-line bold imperative (e.g., "Touch only what you must.
Clean up only your own mess.") followed by 4-6 bullets and a test. An agent
with no context absorbs all four in under 500 tokens.

Our prose lands when co-loaded with the workflow it's embedded in — TDD's
red-green-refactor is crisp inside `test-driven-development/SKILL.md`, but
the "Simplicity First" content is distributed across YAGNI mentions in six
files and has no single canonical statement to quote. Agents read the
locally-relevant section, so this is acceptable operationally, but it's
costly if an agent ever needs the composite view.

**Conflict pressure (same principle, different phrasings):**

Count of concrete pairs that could read as contradictory: **0 direct
contradictions, 2 tonal tensions.**

- Tension 1 — post-hoc vs. in-flight simplification:
  - `code-simplification/SKILL.md:12`: "Core principle: Simplification that
    breaks tests is a signal, not just a failure. Analyze before reverting."
    (invites expanded scope when analysis finds a deeper issue)
  - `test-driven-development/SKILL.md:127`: "Don't add features, refactor
    other code, or 'improve' beyond the test." (forbids scope expansion)

  These do not contradict — one runs post-verification, the other during
  GREEN — but an agent reading both in the same session could read the
  simplification skill as permission to do what TDD forbids. Karpathy's
  "Surgical Changes" resolves the tension with one rule ("Every changed line
  should trace directly to the user's request") applied throughout.

- Tension 2 — when to ask questions:
  - `brainstorming/SKILL.md` HARD-GATE: do not implement without approved
    design (front-loads questions).
  - `implementer-prompt.md:53`: "If you encounter something unexpected or
    unclear, **ask questions**" (permits asking mid-execution).

  Consistent but not unified. Karpathy's "Think Before Coding" states the
  same rule once and applies it everywhere.

### Evidence caveats

Token counts use a word-split × 1.33 approximation; our-side denominators
are scoped to behavior-teaching prose, excluding process scaffolding, so
absolute ratios are directional (order-of-magnitude correct, not precise).
The trace study is N=3 PRs selected for workflow diversity, not a random
sample — the 4:3:4:1 tally is illustrative. The Surgical Changes ~2x
ratio is the softest matrix cell because "teaching Surgical Changes"
bleeds into teaching YAGNI; the qualitative gap (no "match existing
style" rule, no "mention but don't delete unrelated dead code" rule in
our stack) is load-bearing, not the ratio.

## Trace study

### PR #152 — `feat: add sprint skill for autonomous development sessions`

Implementation-heavy, 220 lines of new SKILL.md + tooling. Decision points:

1. **Scope of pre-authorization table.** The sprint SKILL lists a 12-row
   table of decisions the agent makes without asking. With our stack:
   brainstorming's delegation-question pattern (INV-14) fired to justify
   pre-authorizing "approval vs. information." With Karpathy-only: "Think
   Before Coding — State your assumptions explicitly" would have forced the
   table; same outcome, less structure. **Tag: tie.**
2. **Choosing to ship `total-risk` as an external CLI tool (34 tests).**
   Our TDD skill + writing-plans acceptance criteria drove test count and
   coverage. Karpathy-only: "Refactor X → Ensure tests pass before and
   after" would have given goal discipline but no red-green verification;
   the risk of testing-after-implementation is real. **Tag: ours-wins.**
3. **Sprint description bans auto-triggering** (`disable-model-invocation:
   true`). This is a scope-control decision. With our stack: no skill
   addressed this directly; the decision came from the design discussion.
   With Karpathy-only: "No features beyond what was asked" would have
   surfaced the same control. **Tag: miss-both — both stacks are weak on
   skill-metadata-level scope decisions.**

### PR #121 — `Reduce skill attention pressure: remove beads, compress prose, add context-gate hook`

Simplification-heavy; net -1,110 lines across 24 files. Decision points:

1. **Removing INV-14 (beads work tracking) and FAIL-10.** Pure deletion of
   an abstraction that competed with built-in task tools. With our stack:
   `code-simplification`'s "Prefer deletion over modification" +
   `receiving-code-review`'s YAGNI check for "Professional" features both
   applied. With Karpathy-only: "No 'flexibility' or 'configurability' that
   wasn't requested" and "No abstractions for single-use code" nail the
   same conclusion in fewer words. **Tag: karpathy-wins on compression,
   tie on outcome.**
2. **Extracting context-gate-hook.sh to replace inline sections in 5
   skills.** This is a structural change touching 5 files. With our
   stack: `code-simplification`'s "Structural (High Risk — Flag Only)"
   pattern would have required approval; `writing-plans`'s "split by
   subsystem boundary" rule helped. With Karpathy-only: "Surgical Changes"
   would say "Touch only what you must" — but the change deliberately
   touches many files to reduce duplication. Karpathy's guidance would be
   unhelpful here; the consolidation needed the deeper
   code-simplification/SPEC.md machinery. **Tag: ours-wins.**
3. **Deciding to remove beads rather than fix it.** A YAGNI judgment about
   an existing system. Multiple YAGNI mentions fired (brainstorming,
   receiving-code-review, writing-plans). Karpathy-only: one rule would
   have said the same ("If you write 200 lines and it could be 50, rewrite
   it"). **Tag: karpathy-wins on clarity, tie on outcome.**

### PR #111 — `feat: adopt AskUserQuestion batching to reduce round-trips across skills`

Brainstorm→plan→execute cycle; touches 6 skills + SPEC.md + 13 new tests.
Decision points:

1. **Adding INV-15 before modifying any SKILL.md.** Spec-first flow driven
   by our codify-subsystem / writing-plans SPEC-anchored-tests discipline.
   With Karpathy-only: no SPEC.md concept exists; "Goal-Driven Execution"
   would suggest acceptance tests but not the invariant framing. **Tag:
   ours-wins.**
2. **Eliminating "unnecessary" questions in brainstorming** (3 questions
   removed). This is a direct YAGNI judgment on existing prose. With our
   stack: brainstorming's "YAGNI ruthlessly" + receiving-code-review's
   YAGNI patterns. With Karpathy-only: "No features beyond what was asked"
   would have done it. **Tag: karpathy-wins on compression, tie on
   outcome.**
3. **Test authoring strategy: pattern-based structural assertions per
   skill edit** (`test_inv15_brainstorming_no_one_question_per_message`,
   etc.). TDD + writing-plans spec-anchoring drove the test design;
   Karpathy's "Write tests for invalid inputs, then make them pass"
   doesn't capture spec-anchoring. **Tag: ours-wins.**

**Trace tally:** ours-wins 4 / karpathy-wins 3 (all on compression or
clarity, never outcome) / tie 4 / miss-both 1.

## Verdict and rationale

**Verdict: B (graft).** The rule: "Karpathy wins on compression or clarity
for specific phrasings that can be ported with minor edits." All three
conditions hold:

1. **Compression win, not coverage win.** The matrix shows 17x-35x
   compression advantage on three of four principles. On every trace
   outcome, our stack produced the right answer — ours-wins outnumbers
   karpathy-wins 4:3, and every karpathy-wins tag is "compression or
   clarity, not outcome." Adopting the whole upstream would duplicate
   content we already have; ignoring the upstream would leave specific
   high-value phrasings on the table.

2. **One real thin spot: Surgical Changes in-flight.** Ratio is ~2x (we
   have less than half the words on this principle), and the concrete
   failure mode — mid-implementation adjacent improvements, style
   matching, touching unrelated dead code — is not directly addressed
   in any skill description, only implicit under YAGNI. Karpathy has
   four crisp bullets on this.

3. **Graftable phrasings exist.** Not hypothetical: "Every changed line
   should trace directly to the user's request." "Match existing style,
   even if you'd do it differently." "If you notice unrelated dead code,
   mention it — don't delete it." "Remove imports/variables/functions
   that YOUR changes made unused. Don't remove pre-existing dead code
   unless asked." These are 1-2 line insertions, not skill-level
   rewrites, and they close the one gap identified above.

Why not **A (do not adopt)**: compression failure on three principles
(>17x) exceeds the "within 2x" bar.

Why not **C (refactor a skill)**: no single skill shows ≥3x compression
disadvantage paired with zero compensating content — the prose bulk is
justified by process scaffolding, not by behavioral over-teaching.

Why not **D (new compact skill)**: the Surgical Changes gap is solvable
with 4-6 bullets added to existing skills. A new skill would duplicate
YAGNI content and add router surface area; the upstream single-skill
packaging shows this doesn't pay off on compression without CLAUDE.md
always-loading, which we already have at the system level.

## Changes made

Grafts applied on branch `feature/163-evaluate-karpathy` in commit
`99608b3` with refinements in commit `46faf9e`:

- `plugins/dev-workflow-toolkit/skills/code-simplification/SKILL.md`,
  Constraints — added: "Every changed line should trace directly to the
  user's request" and "If you notice unrelated dead code, mention it —
  don't delete it unless asked." Closes the auto-delete-crosses-scope
  failure mode; consolidates the post-hoc vs. in-flight simplification
  tension flagged under Clarity & coherence.
- `plugins/dev-workflow-toolkit/skills/subagent-driven-development/implementer-prompt.md`,
  Self-Review Discipline — existing "Did I follow existing patterns in
  the codebase?" bullet widened to "Did I match existing patterns and
  style in the codebase, even where I'd do it differently?" (absorbs
  the Karpathy anti-ego clause into the existing question). New bullet
  added: "Did I remove only imports/variables/functions that my changes
  made unused, leaving pre-existing dead code in place?" Phrased as
  questions to match the section's voice.
- `plugins/dev-workflow-toolkit/skills/test-driven-development/SKILL.md`,
  GREEN section (:127) — appended to existing sentence: "The test: every
  changed line traces to the user's request." Establishes the canonical
  phrasing that the other two grafts echo.
- `CLAUDE.md` (repo root) — added new `## Surgical Changes` section
  between Workflow and Writing Standards with three bullets: "Every
  changed line should trace directly to the user's request"; "Match
  existing style, even if you'd do it differently"; "If you notice
  unrelated dead code, mention it — don't delete it unless asked."
  Always-loaded at the project level, matching how Simplicity First
  reaches agents via always-loaded system instructions.

CHANGELOG entry: `plugins/dev-workflow-toolkit/CHANGELOG.md` Unreleased
with `<!-- bump: patch -->` — the three plugin-scope grafts only;
project-root CLAUDE.md is out of plugin scope.

## Signals for broader review

Running tally of Approach-B signals:

- **Compression-ratio signal (≥3x):** **hit** on three of four principles
  (17x Simplicity First, 21x Goal-Driven Execution, 35x Think Before
  Coding). See coverage matrix.
- **Fragmentation signal (same guidance in ≥3 places):** **hit** on YAGNI /
  Simplicity First content — appears in `brainstorming/SKILL.md:190`,
  `writing-plans/SKILL.md:12,161`, `implementer-prompt.md:71`,
  `receiving-code-review/SKILL.md:88-137,209-212`, and
  `test-driven-development/testing-anti-patterns.md:82`. Five locations
  for one principle.
- **Conflict signal (≥1 contradictory pair):** **miss** on strict
  contradictions; two tonal tensions logged under Clarity & coherence
  (post-hoc vs. in-flight simplification; front-loaded vs. mid-execution
  questions). Tensions are real but resolvable by the Task 3 grafts, not
  by removing or rewriting either side.

**Result:** 2 distinct signal types landed (compression + fragmentation).

**Recommend follow-up issue.** Scope suggestion for the retrospective to
file: "Audit YAGNI / Simplicity First coverage fragmentation across
dev-workflow-toolkit skills; consolidate to one canonical statement
referenced by the others, to reduce attention pressure and address the
17x compression delta identified in UPSTREAM-karpathy.md."
