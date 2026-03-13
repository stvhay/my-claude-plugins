# Design

> In the context of plugins authored for Claude Code agents, facing the risk of
> undocumented invariants and lost provenance, we established SPEC.md contracts,
> upstream tracking, and a three-tier documentation model, accepting additional
> per-plugin maintenance cost to preserve architectural intent over time.

## SPEC.md as Subsystem Contract

Every plugin's `skills/` directory contains a `SPEC.md` following a shared
template. Each spec is 80-350 lines and defines the subsystem's invariants,
failure modes, and enforcement strategy.

- Invariants use `INV-N` identifiers; failure modes use `FAIL-N`.
- Each invariant is classified as **structural** (enforced by tooling or
  directory layout) or **reasoning-required** (needs architectural judgment).
- A Decision Framework section converts reasoning-required invariants into
  procedural guidance so agents can follow them without deep context.

SPEC.md content assumes the plugin distribution model: all paths are relative
to the plugin root, not to a local repository clone. The spec template is
inlined in the codify-subsystem skill rather than referenced by external path.
MANIFEST.md (indexing a project's subsystem specs) is created on first use
by codify-subsystem, not pre-populated by scaffolding.

## INV/FAIL Numbering Discipline

INV and FAIL identifiers in SPEC.md must be sequentially numbered starting
from 1, with no gaps or duplicates. The quality gate's `inv-numbering` check
enforces this automatically. When invariants are removed, remaining identifiers
are renumbered — stable references across documents use the invariant's prose
description, not its number.

## Upstream Provenance Tracking

When a skill adapts external work, provenance is recorded in `UPSTREAM*.md`
files. Two patterns exist:

1. **Per-subsystem.** `UPSTREAM-<source>.md` at the `skills/` level, used when
   the entire plugin draws from one source.
2. **Per-skill.** `UPSTREAM.md` inside an individual skill directory, used when
   only that skill has external provenance.

Each tracking file records: source, license, adaptation notes, and
(where applicable) sync process. Original work based on external research
receives an UPSTREAM file documenting provenance; purely original work
receives no UPSTREAM file — absence signals original authorship.

UPSTREAM files are maintainer-authored — they record the maintainer's
adaptation decisions and sync status. Consuming agents should not modify
these files or act on their sync instructions.

## Hub-and-Spoke Skill Architecture

Plugins with multiple related skills use a hub-and-spoke topology:

- **stamp:** `stamp-base` (hub) classifies the analysis type and routes to
  STPA, STPA-Sec, or CAST (spokes).
- **ux-toolkit:** `ux-design-agent` (hub) routes to specialist skills for
  design principles and delegation oversight.

The hub classifies; spokes execute. Bidirectional handoffs are permitted —
a spoke may return control to the hub when reclassification is needed.

## Structural vs. Reasoning-Required Invariants

Invariants fall into two categories:

- **Structural.** Enforced by tooling, file layout, or CI. These are
  pattern-matchable and can be validated automatically (e.g., "SKILL.md must
  have YAML frontmatter").
- **Reasoning-required.** Need architectural understanding to verify, checked
  during review (e.g., "description must accurately reflect triggering intent").

The design goal is to convert reasoning-required invariants to structural ones
wherever possible — moving enforcement from human judgment to automation.
`scripts/quality-gate.sh` is the primary mechanism: its six checks
(inv-numbering, issue-tracking, skill-structure, doc-structure, vsa-coverage,
tool-health) automate validation of invariants that were previously
review-dependent.

## Retrospective and Upstream Feedback Loop

The `retrospective` skill runs as Step 8 of finishing-a-development-branch,
after the PR is created. The agent analyzes the development session and
categorizes findings into two buckets:

- **Project-local.** Improvements to this project's workflow, configuration,
  or documentation. Saved to CLAUDE.md or memory at the user's discretion.
- **Upstream.** Improvements to plugin skills that belong in the plugin's
  source repository. Filed as GitHub issues with a `feedback` label.

This closes the learning loop: every development session produces structured
feedback that flows to the correct owner.

## Three-Tier Documentation

Documentation is organized into three tiers by lifecycle:

1. **Ephemeral.** Plans and working notes under `.claude/plans/`.
   Gitignored. Used during development, discarded after merge.
2. **Tracked project docs.** `ARCHITECTURE.md`, `DESIGN.md`, `README.md` at
   the project level. Living documents — decisions are woven into sections,
   not appended as ADRs. Git history preserves the evolution.
3. **Tracked subsystem specs.** `SPEC.md` files inside each plugin's `skills/`
   directory. Define the contract for that plugin's skill set.

## Generated Release Infrastructure

Release tooling (`compute-version.sh`, `release.yml`, validation hooks) is
generated per-project by `project-init`, not shipped as templates in the plugin.
The skill prompt contains the knowledge to produce stack-appropriate scripts.

This follows the principle: **guardrails that can be mechanistically determined
run as hooks, silent when compliant, speaking only on violation.** Version
bump and changelog enforcement are structural invariants (INV-10, INV-11)
enforced by hooks, not reasoning-required checks.

Squash merge is the only merge strategy. Every PR is one commit on main.
