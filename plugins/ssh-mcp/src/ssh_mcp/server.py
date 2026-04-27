"""MCP server: per-project bash on remote machines via system ssh.

State lives in `<project>/.ssh-mcp.toml`. `run` synthesizes a temporary
ssh_config that defines the project's hosts and `Include`s the user's
~/.ssh/config (so global rules still apply), then invokes `ssh -F <tmp>`.
~/.ssh/config is never edited.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import tempfile
import tomllib
from pathlib import Path
from typing import Annotated, Any

import tomli_w
from mcp.server.fastmcp import FastMCP
from pydantic import Field

INSTRUCTIONS = """\
Bash on remote machines via system ssh, scoped per project.

State lives in `<project>/.ssh-mcp.toml`. The server is stateless across
projects — every tool takes `project` (an absolute path to the project
directory) as its first argument. Pass the agent's current working
directory, not this MCP server's directory.

Typical flow:
  1. `list_hosts(project)` — see what's already registered for this project
  2. `add_host(project, name, hostname, directory, ...)` — register if missing
  3. `run(project, command)` — execute; host resolves automatically when
     there's a default or only one host
  4. `upload(project, local, remote)` / `download(project, remote, local)` —
     scp single files or (with `recursive=True`) trees. Relative remote
     paths resolve against the host's registered `directory`.

Host resolution in `run` (in order): explicit `host=` arg → `default_host`
in .ssh-mcp.toml → the only registered host (if exactly one). If none of
those apply, `run` raises and you should call `list_hosts` to see options.

Each entry pairs a host with a remote `directory`; `run` does
`cd <directory> && <command>` automatically. Pass `cwd=` to override the
directory for one call only.

`run` never edits ~/.ssh/config. It synthesizes a temp ssh_config (the
project's Host blocks first, then `Include ~/.ssh/config`) and invokes
`ssh -F <tmp>`, so the user's global ssh rules still fill in anything the
project didn't override. Same project hostname in two different repos =
two fully independent entries.

Hard guarantees on `run`: BatchMode=yes (no interactive prompt will ever
hang the call) and StrictHostKeyChecking=accept-new (TOFU). Host names
must match `[A-Za-z0-9_][A-Za-z0-9._-]*` (no leading dash).

If you call a tool and get an error about an unknown host or no hosts
registered, call `list_hosts(project)` first — don't guess.
"""

mcp = FastMCP("ssh-mcp", instructions=INSTRUCTIONS)

CONFIG_FILENAME = ".ssh-mcp.toml"
# First char must be alphanumeric/underscore so the alias can never be parsed
# as a flag when handed to ssh as argv (e.g. "-foo").
HOST_NAME_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9._\-]*$")

# Descriptions reused across tool argument schemas. Pulled out so each Field
# call stays on one line and identical descriptions don't drift between tools.
_DESC_PROJECT = "Absolute path to the project directory."
_DESC_HOST = "Host alias to target. Omit to use default_host, or the only registered host."
_DESC_RECURSIVE = "Pass -r to scp so directories are copied recursively."
_DESC_REMOTE_PATH = (
    "Path on the host. Relative paths are resolved against the host's registered "
    "directory; absolute or ~-prefixed paths are passed through."
)
_DESC_LOCAL_PATH = (
    "Path on this machine. Pass an absolute path; "
    "paths starting with `-` are rejected (would be parsed as scp flags)."
)
_DESC_TIMEOUT_RUN = "Hard timeout for the entire ssh call, in seconds."
_DESC_TIMEOUT_SCP = "Hard timeout for the entire scp call, in seconds."
_DESC_COMMAND = "Shell command to run. Runs in the remote login shell — quote arguments yourself."
_DESC_CWD = "Override remote working directory for this call. Omit to use the host's directory."


def _validate_host_name(name: str) -> None:
    if not HOST_NAME_RE.match(name):
        raise ValueError(f"invalid host name {name!r}: must match {HOST_NAME_RE.pattern}")


def _validate_ssh_config_value(field: str, value: str) -> None:
    """Reject control characters in fields that get written verbatim into the
    synthesized ssh_config. A literal newline would otherwise let a value smuggle
    in a second directive (e.g. an extra Host block)."""
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in value):
        raise ValueError(f"{field} contains control characters: {value!r}")


def _validate_local_path(path: str) -> None:
    """scp parses leading-dash arguments as flags and modern OpenSSH does not
    support `--` as an end-of-options marker, so we reject these outright."""
    if path.startswith("-"):
        raise ValueError(
            f"local_path must not start with '-' (would be parsed as an scp flag): {path!r}"
        )


def _project_dir(project: str) -> Path:
    p = Path(project).expanduser().resolve()
    if not p.is_dir():
        raise ValueError(f"project {project!r} is not an existing directory")
    return p


def _config_path(project: str) -> Path:
    return _project_dir(project) / CONFIG_FILENAME


def _read_config(project: str) -> dict[str, Any]:
    path = _config_path(project)
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def _write_config(project: str, data: dict[str, Any]) -> None:
    path = _config_path(project)
    # os.open with mode=0o600 creates the file already restricted, avoiding the
    # short window where path.open + chmod would leave it world-readable.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        tomli_w.dump(data, f)


def _synthesize_ssh_config(hosts: dict[str, dict[str, Any]]) -> str:
    """Render an ssh_config: project Host blocks first (so they win on first-match),
    then Include the user's ~/.ssh/config to inherit global rules."""
    lines: list[str] = []
    for name, h in hosts.items():
        lines.append(f"Host {name}")
        lines.append(f"    HostName {h['hostname']}")
        if h.get("user"):
            lines.append(f"    User {h['user']}")
        if h.get("port"):
            lines.append(f"    Port {h['port']}")
        if h.get("identity_file"):
            lines.append(f"    IdentityFile {h['identity_file']}")
        for k, v in (h.get("options") or {}).items():
            lines.append(f"    {k} {v}")
        lines.append("")
    user_config = Path.home() / ".ssh" / "config"
    if user_config.is_file():
        lines.append(f"Include {user_config}")
        lines.append("")
    return "\n".join(lines)


def _common_ssh_opts(config_path: str, timeout_seconds: int) -> list[str]:
    """Flags shared by ssh and scp invocations: the synthesized config + safety defaults.

    ConnectTimeout is clamped to <=30s independently of `timeout_seconds`.
    Establishing a TCP+SSH connection fundamentally takes seconds, not minutes;
    `timeout_seconds` is the budget for the *whole* command (including a long-
    running remote process) and must not be inherited by the connect phase.
    """
    return [
        "-F",
        config_path,
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"ConnectTimeout={min(max(timeout_seconds, 1), 30)}",
    ]


def _invoke(
    hosts: dict[str, dict[str, Any]],
    target_host: str,
    timeout_seconds: int,
    argv_builder,
) -> dict:
    """Synthesize ssh_config to a tempfile, run argv_builder(config_path), return the result."""
    synthesized = _synthesize_ssh_config(hosts)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix="-ssh-mcp.conf", delete=True, encoding="utf-8"
    ) as f:
        f.write(synthesized)
        f.flush()
        argv = argv_builder(f.name)
        try:
            result = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            return {
                "exit_code": None,
                "host": target_host,
                "stdout": e.stdout or "",
                "stderr": e.stderr or "",
                "timed_out": True,
            }
    return {
        "exit_code": result.returncode,
        "host": target_host,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": False,
    }


def _resolve_target_host(config: dict[str, Any], host: str | None) -> str:
    hosts = config.get("hosts", {})
    if host:
        if host not in hosts:
            raise ValueError(f"unknown host {host!r}; not in .ssh-mcp.toml")
        return host
    default = config.get("default_host")
    if default:
        if default not in hosts:
            raise ValueError(f"default_host {default!r} is not registered")
        return default
    if len(hosts) == 1:
        return next(iter(hosts))
    if not hosts:
        raise ValueError("no hosts registered; call add_host first")
    raise ValueError(
        "multiple hosts registered and no default_host set; pass host=... or call set_default_host"
    )


@mcp.tool()
def add_host(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
    name: Annotated[
        str, Field(description="Alias for the host. Must match [A-Za-z0-9_][A-Za-z0-9._-]*.")
    ],
    hostname: Annotated[
        str, Field(description="Real DNS name or IP address of the remote machine.")
    ],
    directory: Annotated[
        str, Field(description="Remote project directory; `run` cd's here by default.")
    ],
    user: Annotated[
        str | None, Field(description="Remote username. Omit to inherit from ~/.ssh/config.")
    ] = None,
    port: Annotated[int | None, Field(description="Non-default SSH port. Omit for 22.")] = None,
    identity_file: Annotated[
        str | None,
        Field(description="Path to a private key file. Tilde expansion happens at ssh time."),
    ] = None,
    options: Annotated[
        dict[str, str] | None,
        Field(description='Extra ssh_config keys, e.g. {"ProxyJump": "bastion"}.'),
    ] = None,
) -> dict:
    """Register or update an SSH host for a project.

    Writes to <project>/.ssh-mcp.toml. Calling with an existing `name` updates
    the entry in place. Comments in the file are not preserved across writes.
    """
    _validate_host_name(name)
    if not directory.strip():
        raise ValueError("directory must be a non-empty path")
    _validate_ssh_config_value("hostname", hostname)
    if user is not None:
        _validate_ssh_config_value("user", user)
    if identity_file is not None:
        _validate_ssh_config_value("identity_file", identity_file)
    for k, v in (options or {}).items():
        _validate_ssh_config_value(f"options[{k!r}] key", k)
        _validate_ssh_config_value(f"options[{k!r}] value", v)

    config = _read_config(project)
    hosts = config.setdefault("hosts", {})
    entry: dict[str, Any] = {"hostname": hostname, "directory": directory}
    if user is not None:
        entry["user"] = user
    if port is not None:
        entry["port"] = port
    if identity_file is not None:
        entry["identity_file"] = identity_file
    if options:
        entry["options"] = options
    hosts[name] = entry
    _write_config(project, config)
    return {"project": str(_project_dir(project)), "name": name, **entry}


@mcp.tool()
def remove_host(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
    name: Annotated[str, Field(description="Alias of the host to remove.")],
) -> dict:
    """Remove a host from <project>/.ssh-mcp.toml. No-op if absent.

    Also clears `default_host` if it pointed at the removed entry.
    """
    _validate_host_name(name)
    config = _read_config(project)
    hosts = config.get("hosts", {})
    removed = name in hosts
    if removed:
        del hosts[name]
        if config.get("default_host") == name:
            config.pop("default_host", None)
        _write_config(project, config)
    return {"project": str(_project_dir(project)), "name": name, "removed": removed}


@mcp.tool()
def list_hosts(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
) -> dict:
    """Return the project's registered hosts and current default_host.

    Call this first when you don't know what's registered — `add_host` and
    `run` will fail loudly if you guess wrong.
    """
    config = _read_config(project)
    return {
        "project": str(_project_dir(project)),
        "config_file": str(_config_path(project)),
        "default_host": config.get("default_host"),
        "hosts": config.get("hosts", {}),
    }


@mcp.tool()
def set_default_host(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
    name: Annotated[
        str | None,
        Field(description="Host alias to set as default. Pass null/None to clear."),
    ] = None,
) -> dict:
    """Set or clear the project's default host.

    `run` uses the default when called without an explicit `host`. If only
    one host is registered, that host is used automatically — you only need
    to call this for multi-host projects.
    """
    config = _read_config(project)
    if name is None:
        config.pop("default_host", None)
    else:
        _validate_host_name(name)
        if name not in config.get("hosts", {}):
            raise ValueError(f"unknown host {name!r}; register it first via add_host")
        config["default_host"] = name
    _write_config(project, config)
    return {"project": str(_project_dir(project)), "default_host": config.get("default_host")}


@mcp.tool()
def run(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
    command: Annotated[str, Field(description=_DESC_COMMAND)],
    host: Annotated[str | None, Field(description=_DESC_HOST)] = None,
    cwd: Annotated[str | None, Field(description=_DESC_CWD)] = None,
    timeout_seconds: Annotated[int, Field(description=_DESC_TIMEOUT_RUN, ge=1, le=3600)] = 60,
) -> dict:
    """Execute a shell command on a project host via ssh.

    Host resolution: explicit `host` arg → `default_host` in .ssh-mcp.toml →
    the only registered host (if exactly one). Raises if none of those apply.

    By default `cd`s into the host's registered `directory`; `cwd` overrides
    for one call. Returns {exit_code, host, stdout, stderr, timed_out}.
    """
    config = _read_config(project)
    hosts = config.get("hosts", {})
    target_host = _resolve_target_host(config, host)
    entry = hosts[target_host]
    target_dir = cwd if cwd is not None else entry.get("directory")
    remote_command = f"cd {shlex.quote(target_dir)} && {command}" if target_dir else command
    return _invoke(
        hosts,
        target_host,
        timeout_seconds,
        lambda cp: [
            "ssh",
            *_common_ssh_opts(cp, timeout_seconds),
            target_host,
            "--",
            remote_command,
        ],
    )


def _resolve_remote_path(entry: dict[str, Any], remote_path: str) -> str:
    """Absolute remote paths are passed through; relative ones are joined onto the
    host's registered directory (mirrors `run`'s cd-into-directory convention)."""
    if remote_path.startswith(("/", "~")):
        return remote_path
    base = entry.get("directory")
    if not base:
        return remote_path
    return f"{base.rstrip('/')}/{remote_path}"


@mcp.tool()
def upload(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
    local_path: Annotated[str, Field(description=_DESC_LOCAL_PATH)],
    remote_path: Annotated[str, Field(description=_DESC_REMOTE_PATH)],
    host: Annotated[str | None, Field(description=_DESC_HOST)] = None,
    recursive: Annotated[bool, Field(description=_DESC_RECURSIVE)] = False,
    timeout_seconds: Annotated[int, Field(description=_DESC_TIMEOUT_SCP, ge=1, le=3600)] = 300,
) -> dict:
    """Copy `local_path` from this machine to `remote_path` on the host via scp.

    Existing files at the destination are silently overwritten (scp's default).
    Returns {exit_code, host, stdout, stderr, timed_out}.
    """
    _validate_local_path(local_path)
    config = _read_config(project)
    hosts = config.get("hosts", {})
    target_host = _resolve_target_host(config, host)
    resolved_remote = _resolve_remote_path(hosts[target_host], remote_path)
    return _invoke(
        hosts,
        target_host,
        timeout_seconds,
        lambda cp: [
            "scp",
            *_common_ssh_opts(cp, timeout_seconds),
            *(["-r"] if recursive else []),
            local_path,
            f"{target_host}:{resolved_remote}",
        ],
    )


@mcp.tool()
def download(
    project: Annotated[str, Field(description=_DESC_PROJECT)],
    remote_path: Annotated[str, Field(description=_DESC_REMOTE_PATH)],
    local_path: Annotated[str, Field(description=_DESC_LOCAL_PATH)],
    host: Annotated[str | None, Field(description=_DESC_HOST)] = None,
    recursive: Annotated[bool, Field(description=_DESC_RECURSIVE)] = False,
    timeout_seconds: Annotated[int, Field(description=_DESC_TIMEOUT_SCP, ge=1, le=3600)] = 300,
) -> dict:
    """Copy `remote_path` from the host to `local_path` on this machine via scp.

    Existing files at the destination are silently overwritten (scp's default).
    Returns {exit_code, host, stdout, stderr, timed_out}.
    """
    _validate_local_path(local_path)
    config = _read_config(project)
    hosts = config.get("hosts", {})
    target_host = _resolve_target_host(config, host)
    resolved_remote = _resolve_remote_path(hosts[target_host], remote_path)
    return _invoke(
        hosts,
        target_host,
        timeout_seconds,
        lambda cp: [
            "scp",
            *_common_ssh_opts(cp, timeout_seconds),
            *(["-r"] if recursive else []),
            f"{target_host}:{resolved_remote}",
            local_path,
        ],
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
