# ssh-mcp

A small MCP server that gives agents bash access to remote hosts on a **per-project** basis. Each project keeps its own host registry in a single `.ssh-mcp.toml` file at its root. `run` shells out to system `ssh` (with the project's hosts merged on top of `~/.ssh/config`), so all of `ssh_config(5)`, agents, `ProxyJump`, and host-key handling keep working unchanged.

The server **never edits `~/.ssh/config`**. It synthesizes a temporary config file per `run` call and invokes `ssh -F <tmp>`.

## Configuration file: `<project>/.ssh-mcp.toml`

```toml
default_host = "prod"  # optional; used by `run` when host arg is omitted

[hosts.prod]
hostname = "10.0.0.1"
user = "ubuntu"
directory = "/srv/myapp"               # `run` cd's here by default
identity_file = "~/.ssh/prod_key"      # optional
port = 22                              # optional
[hosts.prod.options]                   # optional, free-form ssh_config keys
ProxyJump = "bastion"

[hosts.staging]
hostname = "staging.example.com"
user = "ubuntu"
directory = "/srv/myapp"
```

You can edit this file by hand, or use the tools below. Comments are not preserved across tool-driven writes (TOML write libraries are not comment-aware).

## Tools

All tools take `project` (absolute path to the project directory) as the first argument.

| Tool | Purpose |
|------|---------|
| `add_host(project, name, hostname, directory, user?, port?, identity_file?, options?)` | Register or update a host in `.ssh-mcp.toml`. |
| `remove_host(project, name)` | Remove a host. Clears `default_host` if it pointed there. No-op if absent. |
| `list_hosts(project)` | Return registered hosts and current `default_host`. |
| `set_default_host(project, name?)` | Set or clear `default_host`. Pass `name=None` to clear. |
| `run(project, command, host?, cwd?, timeout_seconds?)` | Run `command` over ssh. Resolves host via: explicit arg → `default_host` → the only registered host. `cd`s into the host's `directory`; `cwd` overrides per call. |
| `upload(project, local_path, remote_path, host?, recursive?, timeout_seconds?)` | scp local → host. Relative `remote_path` resolves against the host's `directory`. `recursive=True` for trees. |
| `download(project, remote_path, local_path, host?, recursive?, timeout_seconds?)` | scp host → local. Relative `remote_path` resolves against the host's `directory`. `recursive=True` for trees. |

## How `run` invokes ssh

1. Read `<project>/.ssh-mcp.toml`
2. Resolve the target host
3. Synthesize an ssh_config in a temp file:
   ```
   Host prod
       HostName 10.0.0.1
       User ubuntu
       ...

   Host staging
       ...

   Include ~/.ssh/config       # if it exists; project hosts win on first-match
   ```
4. `ssh -F <tmp> -o BatchMode=yes -o StrictHostKeyChecking=accept-new <host> -- "cd <dir> && <command>"`
5. Delete the temp file when the call returns

Project hosts are listed before the `Include` so they take precedence per ssh_config(5)'s "first obtained value" rule. The user's global rules (e.g. `Host *` defaults, `IdentityAgent`, `ServerAliveInterval`) still fill in anything the project didn't specify.

## Installation

### As a plugin (via marketplace)

```
/plugin marketplace add stvhay/my-claude-plugins
/plugin install ssh-mcp@my-claude-plugins
```

The plugin's `.mcp.json` makes Claude Code launch the server with `uv --directory ${CLAUDE_PLUGIN_ROOT} run ssh-mcp`.

### Standalone (without the marketplace)

```bash
git clone <this-repo> ssh-mcp
cd ssh-mcp
uv sync
```

Then point any MCP client at the server:

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/ssh-mcp", "run", "ssh-mcp"]
    }
  }
}
```

## Requirements

- `uv` on `PATH`
- `ssh` on `PATH`

## Security defaults

- `BatchMode=yes` — `run` never blocks on a passphrase or password prompt
- `StrictHostKeyChecking=accept-new` — TOFU on first connection, reject changes after
- Host names validated against `^[A-Za-z0-9._-]+$`
- `directory` is `shlex.quote`d before being interpolated into the remote command
- `.ssh-mcp.toml` is written `0600`

## License

Apache 2.0
