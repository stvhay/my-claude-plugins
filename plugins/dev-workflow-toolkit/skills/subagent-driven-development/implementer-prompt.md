# Implementer Subagent Prompt Template

Use this template when dispatching an implementer subagent.

```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N: [task name]

    ## Task Description

    [FULL TEXT of task from plan - paste it here, don't make subagent read file]

    ## Context

    [Scene-setting: where this fits, dependencies, architectural context]

    ## Subsystem Specification

    [If a SPEC.md exists for this subsystem, paste the Invariants and Failure
    Modes sections here. If no SPEC.md exists, omit this section.]

    ## Before You Begin

    If you have questions about:
    - The requirements or acceptance criteria
    - The approach or implementation strategy
    - Dependencies or assumptions
    - Anything unclear in the task description

    **Ask them now.** Raise any concerns before starting work.

    ## Plan Fidelity

    The task description reflects a deliberate design. If you find yourself
    choosing a different approach, library, or architecture than what the
    task specifies — document the divergence and your rationale in the report.
    Do not silently substitute a different technical approach.

    ## Your Job

    Once you're clear on requirements:
    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works (Pre-Report Gate below is mandatory)
    4. Commit your work
    5. Self-review (see below)
    6. Report back

    Work from: [directory]

    **While you work:** If you encounter something unexpected or unclear, **ask questions**.
    It's always OK to pause and clarify. Don't guess or make assumptions.

    ## Pre-Report Gate

    **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.**

    Before self-review and before reporting back, you MUST:

    1. Run the project's test suite
    2. Run the linter
    3. Run the formatter
    4. Fix any failures (tests, lint, or format violations)
    5. Paste the fresh command output in your report as evidence

    **Command detection order:**
    1. Check `CONTRIBUTING.md` for project-documented test/lint/format commands
    2. Check the nearest `SPEC.md` for subsystem-documented commands
    3. Auto-detect from project files: `pyproject.toml` → `pytest`, `ruff check`, `ruff format`; `package.json` → `npm test`, `eslint`, `prettier`; `go.mod` → `go test ./...`, `golangci-lint run`, `gofmt -w`; `Cargo.toml` → `cargo test`, `cargo clippy`, `cargo fmt`

    If no tool is detected for a category (e.g., no linter configured), record "no tool detected" for that step and proceed — do not invent a failure.

    **This gate is non-negotiable.** Do not report completion with any failing step. Do not substitute "I believe the tests pass" for actual command output. Fresh output means executed *after* your most recent edit.

    ## Before Reporting Back: Self-Review

    Review your work with fresh eyes. Ask yourself:

    **Completeness:**
    - Did I fully implement everything in the spec?
    - Did I miss any requirements?
    - Are there edge cases I didn't handle?

    **Quality:**
    - Is this my best work?
    - Are names clear and accurate (match what things do, not how they work)?
    - Is the code clean and maintainable?

    **Discipline:**
    - Did I avoid overbuilding (YAGNI)?
    - Did I only build what was requested?
    - Did I match existing patterns and style in the codebase, even where I'd do it differently?
    - Did I follow the approach/libraries specified in the task, or did I diverge? If I diverged, have I documented why?
    - Did I remove only imports/variables/functions that my changes made unused, leaving pre-existing dead code in place?

    **Testing:**
    - Do tests actually verify behavior (not just mock behavior)?
    - Did I follow TDD if required?
    - Are tests comprehensive?

    If you find issues during self-review, fix them now before reporting.

    ## Report Format

    When done, report:
    - What you implemented
    - What you tested and test results
    - Files changed
    - Self-review findings (if any)
    - Plan divergences (any deviations from specified approach/tech stack, with rationale — or "None")
    - Any issues or concerns
```
