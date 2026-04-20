# Headless Mode Patterns

Common automation patterns using Claude Code's headless mode (`claude -p`). Each pattern shows the command, the `--allowedTools` restriction, when to prefer the headless run over an interactive session, and the expected behavior.

## Cross-Pattern Guidance

- **Always restrict `--allowedTools`.** Headless mode runs without confirmation prompts; the tool whitelist is your safety boundary. Default to the smallest set that lets the task complete.
- **Treat headless runs as production.** They often execute in CI or shell scripts where there is no human in the loop to catch a mistake.
- **Read first, write second.** Patterns that modify state should start by reading current state and reporting it before acting. This makes failures easier to diagnose and limits blast radius.
- **Scope the prompt.** A focused, single-task prompt is easier to validate than a multi-step pipeline. If you find yourself chaining unrelated steps, split the invocation.

## Pattern 1: CI Failure Triage

Re-run a failing CI workflow, diagnose the failure, fix it, push, and verify the next run passes.

```bash
claude -p "The CI workflow on branch <BRANCH> is failing. Run gh run view --log-failed, diagnose, fix, commit, push, and verify the next run passes." \
  --allowedTools "Bash,Read,Edit,Write"
```

**Pre-requisite:** `gh` must be authenticated (`gh auth status` should succeed). In CI, export `GH_TOKEN`.

**When to use it**

- The branch is known-good (you wrote it; you trust the test suite)
- The failure is likely simple — lint, format, missing import, snapshot drift, flake retry
- You want to reclaim attention for higher-value work while a routine fix runs

**When interactive is better**

- The failure points at a design decision (e.g., a new test reveals a contract change)
- The failure is in security or auth code — you want to inspect before applying any patch
- The build touches infrastructure that other people depend on

**Expected behavior**

The agent runs `gh run view --log-failed`, identifies the failing step, makes a targeted edit, commits with a message that references the failure, pushes, and watches the next run with `gh run watch` until it succeeds. If it cannot find a fix in one or two iterations, it reports the diagnosis instead of guessing.

## Pattern 2: Post-Merge Cleanup

Delete the feature branch, prune the local main worktree, and remove any stale worktree after a PR merges.

```bash
claude -p "Clean up after merging PR #<N>: delete the feature branch locally and remotely, update local main, prune any stale worktree." \
  --allowedTools "Bash,Read"
```

**When to use it**

- You've already verified the merge succeeded on GitHub
- You want a clean local repo without doing the housekeeping manually
- Your worktree convention is consistent (e.g., `.worktrees/<type>/<issue>-<slug>`) so the agent can find the right one to remove

**When interactive is better**

- The feature branch has unmerged commits (you'd lose work)
- The worktree contains uncommitted changes — investigate before pruning
- The merge was a fast-forward or rebase that left local refs in an unusual state

**Expected behavior**

The agent confirms the PR is merged, fetches origin, deletes the local feature branch (`git branch -d`, never `-D`), deletes the remote with `git push origin --delete`, fast-forwards local main, and runs `git worktree remove` followed by `git worktree prune`. It refuses to delete a branch with unmerged commits and reports the situation instead.

## Pattern 3: Release Tagging

Verify the changelog has an unreleased entry with the right bump type and push it to main; CI handles the version bump and tag.

```bash
claude -p "Prepare release for the dev-workflow-toolkit plugin: confirm plugins/dev-workflow-toolkit/CHANGELOG.md has an '## Unreleased <!-- bump: TYPE -->' section with at least one entry, confirm the most recent commit on this branch contains that entry, then push the branch. The release bot will compute the version, move the changelog entry under the new version header, edit plugin.json, and create the tag." \
  --allowedTools "Bash,Read"
```

**When to use it**

- The project uses changelog-driven CI bumping (`## Unreleased <!-- bump: TYPE -->`)
- The release is a routine patch or minor bump from a known-good main
- You want to keep the version-of-record in CI rather than in your local working copy

**When interactive is better**

- A breaking change requires migration notes that need human review
- The release coordinates multiple plugins or repos
- Stakeholders need a heads-up before the tag goes out
- The project does NOT use changelog-driven bumping — manual `plugin.json`/`package.json` edits should stay interactive so you can sanity-check the version number

**Expected behavior**

The agent reads `CHANGELOG.md`, confirms the `## Unreleased` header exists with a `<!-- bump: TYPE -->` comment, confirms at least one bullet has been added since the last release, and pushes. It does NOT edit `plugin.json` or rewrite the changelog header — those are the release bot's responsibility. If the unreleased section is empty or missing the bump comment, it stops and reports.

## Pattern 4: Batch Linting and Formatting

Fix all lint and format errors across the working tree, run the test suite, commit the fixes.

```bash
claude -p "Fix all linting and formatting errors in the current branch, run tests, commit fixes." \
  --allowedTools "Bash,Read,Edit,Write"
```

**When to use it**

- Pre-PR cleanup on a long-running branch with style drift
- A sweep after adopting a new linter rule or formatter version
- Routine tidiness before review

**When interactive is better**

- You're working in unfamiliar code — auto-fixes can mask logic bugs
- The project intentionally tolerates style inconsistency for historical reasons
- A failing test surfaced during the run needs human judgment about whether to fix the test or the code

**Expected behavior**

The agent looks for the project's lint/format commands in `CONTRIBUTING.md` and the standard config files (`pyproject.toml`, `package.json`, `go.mod`); if it can't determine them, it asks. It then applies fixes, runs the test suite, and commits in a single commit titled `chore: apply lint and format fixes`. If tests fail after fixes, it stops and reports — it does not attempt to fix test failures under this prompt.
