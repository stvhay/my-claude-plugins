# Changelog

Agent-focused changelog. When a new version of this plugin is installed,
read this file and apply retroactive actions marked with **ACTION**.

## Unreleased

<!-- bump: minor -->

- **New tools: `upload` / `download`.** Thin scp wrappers — single file by default, set `recursive=True` for directories. Relative `remote_path` resolves against the host's registered `directory` (mirrors `run`'s cd convention); absolute or `~`-prefixed paths pass through. Existing destination files are silently overwritten (scp default).
- **Per-project configuration.** State now lives in `<project>/.ssh-mcp.toml`; all tools take a `project` argument. The server is stateless across projects.
- **No more edits to `~/.ssh/config`.** `run` synthesizes a temp ssh_config that `Include`s the user's global config, and invokes `ssh -F <tmp>`. The previous "managed include" approach in `~/.config/ssh-mcp/config` is gone.
- **New tool: `set_default_host(project, name?)`.** Sets or clears `default_host`, used by `run` when called without an explicit host. If only one host is registered it's used automatically — `set_default_host` is only needed for multi-host projects.
- **`run` now returns the resolved `host`** alongside `exit_code`/`stdout`/`stderr`/`timed_out`, so callers can confirm which entry was used.
- **ACTION:** if you previously had hosts registered in `~/.config/ssh-mcp/config`, that file and the `Include` line in `~/.ssh/config` are no longer read or written by this server. Re-register hosts via `add_host(project=...)` against the relevant project, or remove the legacy `Include` line by hand.

## v0.1.0

- Initial release
- Tools: `add_host`, `remove_host`, `list_hosts`, `run`
- Each entry pairs a host with a project directory; `run` `cd`s into it by default
- Managed `~/.config/ssh-mcp/config`, added a single `Include` line to `~/.ssh/config`
- Plugin layout: ships `.mcp.json` so Claude Code auto-launches the server via `uv --directory ${CLAUDE_PLUGIN_ROOT} run ssh-mcp`
