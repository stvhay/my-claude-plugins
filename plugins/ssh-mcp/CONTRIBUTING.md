# Contributing

## Setup

```bash
direnv allow      # loads flake.nix dev shell (uv, python313, ruff, openssh)
uv sync           # installs Python deps into .venv
```

If you don't use direnv, run `nix develop` directly, or install `uv` and Python 3.13 yourself.

## Workflow

For non-trivial changes:

1. Brainstorm the design — `/dev-workflow-toolkit:brainstorming`
2. Write a plan — `/dev-workflow-toolkit:writing-plans`
3. Execute — `/dev-workflow-toolkit:executing-plans`
4. Verify by hand against a real ssh host, not just by running tests
5. Self-review — `/dev-workflow-toolkit:requesting-code-review`

For trivial fixes (typos, comment edits) just open a PR.

## Testing locally

There is no test suite yet. Smoke test by:

1. Pick a project directory (e.g. a tempdir).
2. Call `add_host(project=<dir>, name="local", hostname="127.0.0.1", directory="/tmp", user=$USER)` — this writes `<dir>/.ssh-mcp.toml`.
3. Call `run(project=<dir>, command="pwd && whoami")` against a real ssh-able target. Confirm the response shows `/tmp` (the registered directory) and the right user.
4. Call `remove_host(project=<dir>, name="local")` and confirm the entry is gone from `<dir>/.ssh-mcp.toml`.
5. Confirm `~/.ssh/config` is untouched (`git diff` if you keep it in a repo, or compare against a backup) — the server should never modify it.

## Code style

- `ruff format` and `ruff check` — both available in the dev shell
- Keep the server file flat; no premature abstraction
