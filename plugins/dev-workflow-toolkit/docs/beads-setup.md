# Beads + Dolt Setup

The dev-workflow-toolkit skills integrate with [beads](https://github.com/steveyegge/beads) for cross-session issue tracking. Beads uses [Dolt](https://github.com/dolthub/dolt) as its database backend.

## Requirements

- **beads** ≥ 0.59.0 (earlier versions have daemon timeout issues)
- **dolt** ≥ 1.83.0

## Installation

### Option A: Nix flake + envrc.d (recommended)

Nix packages for beads and dolt may lag behind releases. Use `.envrc.d/` scripts to install from GitHub releases while keeping other tools in nix.

**flake.nix** — keep project tools here, but NOT beads/dolt:

```nix
{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in {
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system}; in {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [
              python313
              uv
              # Do NOT add beads or dolt here — managed by .envrc.d/
            ];
          };
        });
    };
}
```

**.envrc** — source nix flake and .envrc.d/ scripts:

```bash
if has nix; then use flake; fi

for init_dir in .envrc.d .envrc.local.d; do
  if [[ -d "$init_dir" ]]; then
    for f in "$init_dir"/*; do
      source "$f"
    done
  fi
done
```

**.envrc.d/beads.sh** — install/update beads from GitHub releases:

```bash
_beads_latest_version() {
  curl -fsSL https://api.github.com/repos/steveyegge/beads/releases/latest 2>/dev/null \
    | sed -n 's/.*"tag_name":[[:space:]]*"v\{0,1\}\([^"]*\)".*/\1/p' | head -1
}

_beads_install() {
  local version=$1 os arch asset tmpdir
  case "$(uname -s)" in Linux) os="linux" ;; Darwin) os="darwin" ;; esac
  case "$(uname -m)" in x86_64) arch="amd64" ;; aarch64|arm64) arch="arm64" ;; esac
  asset="beads_${version}_${os}_${arch}.tar.gz"

  echo "beads: installing v${version}..."
  tmpdir=$(mktemp -d)
  curl -fsSL "https://github.com/steveyegge/beads/releases/download/v${version}/${asset}" \
    | tar xz -C "$tmpdir"
  mkdir -p "$HOME/.local/bin"
  mv "$tmpdir/bd" "$HOME/.local/bin/bd"
  ln -sf bd "$HOME/.local/bin/beads"
  rm -rf "$tmpdir"
}

_beads_ensure() {
  local bin="$HOME/.local/bin/bd"
  local stamp="$HOME/.local/share/beads/.update-check"
  mkdir -p "$HOME/.local/share/beads"

  if [[ ! -x "$bin" ]]; then
    local latest=$(_beads_latest_version)
    [[ -n "$latest" ]] && _beads_install "$latest"
  elif [[ ! -f "$stamp" ]] || [[ -n $(find "$stamp" -mtime +1 2>/dev/null) ]]; then
    local current=$("$bin" --version 2>/dev/null | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
    local latest=$(_beads_latest_version)
    if [[ -n "$latest" && "$current" != "$latest" ]]; then
      echo "beads: $current -> $latest"
      _beads_install "$latest"
    fi
    touch "$stamp"
  fi
}

_beads_ensure
PATH_add "$HOME/.local/bin"
```

**.envrc.d/dolt.sh** — same pattern for dolt:

```bash
_dolt_latest_version() {
  curl -fsSL https://api.github.com/repos/dolthub/dolt/releases/latest 2>/dev/null \
    | sed -n 's/.*"tag_name":[[:space:]]*"v\{0,1\}\([^"]*\)".*/\1/p' | head -1
}

_dolt_install() {
  local version=$1 os arch tmpdir
  case "$(uname -s)" in Linux) os="linux" ;; Darwin) os="darwin" ;; esac
  case "$(uname -m)" in x86_64) arch="amd64" ;; aarch64|arm64) arch="arm64" ;; esac

  echo "dolt: installing v${version}..."
  tmpdir=$(mktemp -d)
  curl -fsSL "https://github.com/dolthub/dolt/releases/download/v${version}/dolt-${os}-${arch}.tar.gz" \
    | tar xz -C "$tmpdir"
  mkdir -p "$HOME/.local/bin"
  mv "$tmpdir/dolt-${os}-${arch}/bin/dolt" "$HOME/.local/bin/dolt"
  rm -rf "$tmpdir"
}

_dolt_ensure() {
  local bin="$HOME/.local/bin/dolt"
  local stamp="$HOME/.local/share/dolt/.update-check"
  mkdir -p "$HOME/.local/share/dolt"

  if [[ ! -x "$bin" ]]; then
    local latest=$(_dolt_latest_version)
    [[ -n "$latest" ]] && _dolt_install "$latest"
  elif [[ ! -f "$stamp" ]] || [[ -n $(find "$stamp" -mtime +1 2>/dev/null) ]]; then
    local current=$("$bin" version 2>/dev/null | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)
    local latest=$(_dolt_latest_version)
    if [[ -n "$latest" && "$current" != "$latest" ]]; then
      echo "dolt: $current -> $latest"
      _dolt_install "$latest"
    fi
    touch "$stamp"
  fi
}

_dolt_ensure
PATH_add "$HOME/.local/bin"
```

### Option B: Direct install (no nix)

```bash
# beads
curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash

# dolt
sudo bash -c 'curl -L https://github.com/dolthub/dolt/releases/latest/download/install.sh | bash'
```

## Project Configuration

After installing, initialize beads in your project:

```bash
bd init
```

Then configure GitHub integration:

```bash
bd config set github.org <your-org>
bd config set github.repo <your-repo>
```

## Diagnostics

```bash
bd doctor    # Check installation health, version, sync status
bd version   # Show current version
dolt version # Show dolt version
```

Common issues:
- **Daemon timeout ("took too long to start >5s")**: Upgrade beads to ≥ 0.59.0
- **"database not found"**: Run `bd init --force -p <project>` then reimport from JSONL if available (`bd init --from-jsonl`)
- **Nix version lag**: Use the `.envrc.d/` approach above instead of nix packages
