# ssh-mcp Subsystem

## Purpose

`ssh-mcp` is a runtime-component plugin that ships an MCP server. The server
gives agents per-project bash access on remote hosts via system `ssh`, with
no edits to `~/.ssh/config` and no managed include files. State lives in
`<project>/.ssh-mcp.toml`; the server is stateless across projects and the
agent passes `project` (an absolute path) on every tool call.

The key design decision: `run` synthesizes a temporary `ssh_config` per call
that lists the project's host blocks and then `Include`s the user's global
`~/.ssh/config`, then invokes `ssh -F <tmp>`. First-match precedence in
`ssh_config(5)` means project values win over globals where they conflict;
the user's defaults (e.g. `IdentityAgent`, `ServerAliveInterval`, `Host *`
options) still fill in everything the project didn't specify. This avoids
the long-tail mess of editing or shadowing the user's actual config file.

> **Plugin shape:** This is a runtime-component plugin (no `skills/`
> directory). It ships `.mcp.json` declaring the server the harness
> launches, plus the Python source under `src/ssh_mcp/`. SPEC.md lives
> at the plugin root rather than under `skills/`. See
> `docs/ARCHITECTURE.md#plugin-shape-skills-vs-runtime-component`.

## Core Mechanism

The server is a single FastMCP entry point (`src/ssh_mcp/server.py`)
launched by Claude Code via the plugin's `.mcp.json`:

```
uv --directory ${CLAUDE_PLUGIN_ROOT} run ssh-mcp
```

`run(project, command, host?, cwd?, timeout_seconds?)` resolves the host in
this order: explicit `host=` argument → `default_host` in
`<project>/.ssh-mcp.toml` → the only registered host (if exactly one). It
then synthesizes an ssh_config in a temp file, invokes
`ssh -F <tmp> -o BatchMode=yes -o StrictHostKeyChecking=accept-new`, and
deletes the temp file when the call returns.

`upload` and `download` are thin `scp` wrappers that resolve relative
`remote_path` against the host's registered `directory` (the same convention
`run` uses for `cd`).

**Key files:**
- `src/ssh_mcp/server.py` — FastMCP server + 7 tools
- `src/ssh_mcp/__init__.py` — re-exports `main` and `mcp`
- `.mcp.json` — declares the server for the harness
- `pyproject.toml` — `mcp[cli]` + `tomli-w` dependencies; entry point
- `flake.nix` — dev shell (`uv`, `python313`, `ruff`, `openssh`)
- `<project>/.ssh-mcp.toml` — runtime state, written `0600`, NOT shipped

## Public Interface

| Tool | Contract |
|---|---|
| `add_host(project, name, hostname, directory, user?, port?, identity_file?, options?)` | Registers or updates a host in `<project>/.ssh-mcp.toml`. Idempotent — existing names are updated in place. `name` must match `^[A-Za-z0-9._-]+$`. |
| `remove_host(project, name)` | Removes a host. Clears `default_host` if it pointed there. No-op if absent. |
| `list_hosts(project)` | Returns registered hosts and current `default_host`. |
| `set_default_host(project, name?)` | Sets or clears `default_host`. Pass `name=None` to clear. |
| `run(project, command, host?, cwd?, timeout_seconds?)` | Runs `command` over ssh. `cd`s into the host's `directory` first (or `cwd` if given). Returns `host`, `exit_code`, `stdout`, `stderr`, `timed_out`. |
| `upload(project, local_path, remote_path, host?, recursive?, timeout_seconds?)` | scp local → host. Relative `remote_path` resolves against the host's `directory`. `recursive=True` for trees. |
| `download(project, remote_path, local_path, host?, recursive?, timeout_seconds?)` | scp host → local. Same `remote_path` resolution as `upload`. |

All tools take `project` (an absolute path to the project directory) as the
first argument. The server is stateless across projects.

## Invariants

| ID | Invariant | Enforcement | Why It Matters |
|---|---|---|---|
| INV-1 | `~/.ssh/config` is never read for write and never edited by any tool | reasoning-required | Users own their ssh config; mutating it surprises them and breaks reproducibility |
| INV-2 | All registered host state lives in `<project>/.ssh-mcp.toml`; the server holds no in-memory cross-project state | structural | Per-project isolation; agents pass `project` on every call |
| INV-3 | `run` synthesizes a temp ssh_config that lists project Host blocks BEFORE `Include ~/.ssh/config` so first-match precedence (per `ssh_config(5)`) gives project values priority | reasoning-required | Project hosts must be able to override global defaults; reordering would silently flip precedence |
| INV-4 | The synthesized ssh_config temp file is deleted when the `run` call returns (success, failure, or timeout) | structural | Prevents accumulating tempfiles and avoids leaking host details to other processes |
| INV-5 | `ssh` is invoked with `BatchMode=yes` and `StrictHostKeyChecking=accept-new`; no tool may pass options that re-enable interactive password/passphrase prompts | reasoning-required | The MCP server has no UI for password entry; a prompt would deadlock the agent |
| INV-6 | Host names registered via `add_host` match the regex `^[A-Za-z0-9._-]+$` | structural | Validates via `pydantic` `Field` constraint; prevents shell injection through the synthesized ssh_config and the `ssh <host>` CLI argument |
| INV-7 | The host's `directory` is `shlex.quote`d before interpolation into the remote `cd <dir> && <command>` invocation | structural | Prevents command injection through the directory field in `.ssh-mcp.toml` |
| INV-8 | `<project>/.ssh-mcp.toml` is created with mode `0600` | structural | Host registry may contain identity-file paths and proxy hosts; world-readable defaults would leak that detail |
| INV-9 | `add_host` for an existing name updates in place; `remove_host` for an absent name is a no-op | reasoning-required | Idempotency — agents can replay tool calls without surprising side effects |
| INV-10 | `remove_host` clears `default_host` when it pointed at the removed host | reasoning-required | Otherwise `run` calls without an explicit host would fail with a confusing "default points to unknown host" error |
| INV-11 | Plugin runtime state (`.venv/`, `.ruff_cache/`, `__pycache__/`, `.ssh-mcp.toml`) is gitignored at the plugin root and never committed | structural | `.venv` and caches are per-developer; `.ssh-mcp.toml` is per-project secret host registry |

**Enforcement classification:**
- **structural** — enforced by code (regex validators, `shlex.quote`, file mode arguments) or directory convention; pattern-matchable
- **reasoning-required** — needs architectural understanding; verified during code review or smoke testing

## Failure Modes

| ID | Symptom | Cause | Fix |
|---|---|---|---|
| FAIL-1 | `run` raises "no host could be resolved" | No explicit `host=`, no `default_host` in `.ssh-mcp.toml`, and either zero or 2+ registered hosts | Call `list_hosts(project)` to see options; pass `host=` explicitly or call `set_default_host(project, name)` |
| FAIL-2 | `run` returns non-zero exit_code with stderr "Permission denied (publickey)" | Identity file missing, agent not loaded, or wrong `user` registered | Verify the `identity_file` path (it is NOT auto-added to ssh-agent), check `user`, confirm the host accepts the key |
| FAIL-3 | `run` times out with `timed_out=True` | Network unreachable, host down, or remote command blocks waiting for input | Check connectivity (`ping`, plain `ssh`); if the remote command is interactive, redirect stdin |
| FAIL-4 | `run` fails with "Host key verification failed" | TOFU rejected — the host's key changed since first connection | Investigate (could be MITM, could be legit re-key); if legit, remove the offending entry from `~/.ssh/known_hosts` and re-run |
| FAIL-5 | Tool call fails with `ValueError: invalid host name` | Host name contains characters outside `^[A-Za-z0-9._-]+$` (INV-6) | Pick a different `name`; the underlying remote `hostname` can still contain anything ssh accepts |
| FAIL-6 | `add_host` overwrote an entry the user had hand-edited with comments | TOML write libs are not comment-aware (documented in README) | Re-add the comments by hand, or maintain `.ssh-mcp.toml` exclusively via the tools |
| FAIL-7 | Server fails to start: `ModuleNotFoundError: No module named 'mcp'` | `uv sync` was never run in the plugin directory; deps not installed | The harness runs `uv --directory ${CLAUDE_PLUGIN_ROOT} run ssh-mcp` which auto-syncs on first launch; if running by hand, run `uv sync` first |
| FAIL-8 | Server fails to start: `command not found: uv` | `uv` is not installed on PATH | Install per https://astral.sh/uv (curl installer or package manager) |
| FAIL-9 | Server fails to start: `command not found: ssh` | OpenSSH client missing on PATH | Install OpenSSH client (`openssh-client` apt package, `openssh` brew formula, included in `flake.nix` dev shell) |

## Testing

There is no test suite in this plugin. The CONTRIBUTING.md prescribes a
manual smoke test against a real ssh host: register a host, call `run` with
a benign command (`pwd && whoami`), confirm the returned `host` and the
remote `cd` behavior, then `remove_host` and verify the entry is gone from
`.ssh-mcp.toml`. Verify `~/.ssh/config` is byte-unchanged.

**Traceability:**
- INV-1: reasoning-required — verified by reading `server.py` (no `~/.ssh/config` writes anywhere; no `Path.home() / ".ssh" / "config"` writes).
- INV-2: structural — verified by reading `server.py` (no module-level mutable state; all reads/writes go through `<project>/.ssh-mcp.toml`).
- INV-3: reasoning-required — verified by reading `_synthesize_ssh_config` and confirming Host blocks precede the `Include` directive.
- INV-4: structural — `tempfile` cleanup is in a `finally` block in `run`.
- INV-5: structural — the literal flags `-o BatchMode=yes -o StrictHostKeyChecking=accept-new` appear in the `ssh` command construction.
- INV-6: structural — pydantic `Field(pattern=...)` on the `name` parameter.
- INV-7: structural — `shlex.quote(directory)` appears in the remote command construction.
- INV-8: structural — `os.open(..., 0o600)` or `os.fchmod(..., 0o600)` in the TOML write path.
- INV-9, INV-10, INV-11: reasoning-required — verified during code review.

## Dependencies

| Dependency | Type | SPEC.md Path |
|---|---|---|
| Claude Code MCP launcher (`${CLAUDE_PLUGIN_ROOT}`) | external | N/A — built into Claude Code runtime |
| FastMCP (`mcp[cli]`) | external | N/A — pinned in `pyproject.toml` |
| `tomli-w` | external | N/A — pinned in `pyproject.toml` |
| OpenSSH client (`ssh`, `scp`) | external | N/A — system binary |
| `uv` | external | N/A — system binary |
