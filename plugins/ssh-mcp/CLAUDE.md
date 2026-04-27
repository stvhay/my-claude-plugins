# ssh-mcp

A small MCP server that gives agents bash access on remote hosts via system `ssh`. Ships as a Claude Code **plugin** vendored under a marketplace's `plugins/` directory.

## What it does

Seven tools, exposed over MCP stdio. All take `project` (absolute path) as the first arg:

- `add_host(project, name, hostname, directory, ...)` — register or update a host in `<project>/.ssh-mcp.toml`
- `remove_host(project, name)` — deregister; clears `default_host` if it pointed there
- `list_hosts(project)` — registered hosts and the current `default_host`
- `set_default_host(project, name?)` — set or clear `default_host`
- `run(project, command, host?, cwd?)` — `cd <directory> && <command>` over ssh
- `upload(project, local_path, remote_path, recursive?)` — scp local → host
- `download(project, remote_path, local_path, recursive?)` — scp host → local

## Invariants

- **Per-project state.** All host registrations live in `<project>/.ssh-mcp.toml`. The MCP server is stateless across projects; the agent passes `project` on every call.
- **`~/.ssh/config` is never edited.** `run` synthesizes a temp ssh_config (project hosts first, then `Include ~/.ssh/config`) and invokes `ssh -F <tmp>`. The user's global rules still apply for anything not overridden.
- **First-match precedence.** Project Host blocks come before the Include in the synthesized config, so project values win where they conflict with global defaults.
- **Each entry pairs a host with a project directory.** `run` does `cd <dir> && <command>` by default; pass `cwd` to override per call. `upload`/`download` resolve relative `remote_path` against the same directory; absolute or `~`-prefixed paths pass through.
- **Idempotent.** `add_host` for an existing name updates in place; `remove_host` for an absent name is a no-op.
- **Fail fast on auth.** `ssh` is invoked with `BatchMode=yes` — never blocks on a passphrase or password prompt.
- **Comments not preserved across writes.** TOML libs aren't comment-aware. If you maintain `.ssh-mcp.toml` by hand with comments, don't mix in tool-driven writes.

## Layout

```
.claude-plugin/plugin.json   # plugin manifest
.mcp.json                    # auto-launches server via ${CLAUDE_PLUGIN_ROOT}
src/ssh_mcp/server.py        # FastMCP server + 5 tools
pyproject.toml               # mcp[cli] + tomli-w
flake.nix                    # uv + python313 + ruff + openssh
.envrc / .envrc.d            # direnv loads the flake
README.md                    # public-facing
CHANGELOG.md                 # agent-readable
```

## Running it

When installed as a plugin, Claude Code reads `.mcp.json` and runs:

```
uv --directory ${CLAUDE_PLUGIN_ROOT} run ssh-mcp
```

For local development:

```bash
direnv allow      # loads flake (uv, python313, ruff, openssh)
uv sync
uv run ssh-mcp    # speaks MCP over stdio
```

## Working on this project

- `/dev-workflow-toolkit:brainstorming` before designing new tool surface
- `/dev-workflow-toolkit:writing-plans` for any change touching ssh_config synthesis or the TOML schema — those are the load-bearing pieces
- Smoke test: register two hosts in a tempdir, set a default, verify `_synthesize_ssh_config` round-trips through `ssh -G -F`
