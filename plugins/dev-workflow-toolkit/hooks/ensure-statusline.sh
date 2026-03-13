#!/usr/bin/env bash
# Claude Code SessionStart hook: ensures claude-statusline binary is installed
# and configured. Downloads latest release from stvhay/claude-statusline if
# missing or outdated. Silent on success, warnings to stderr on failure.
#
# Registered in hooks.json as a SessionStart hook.

BINARY_DIR="$HOME/.claude/bin"
BINARY_PATH="$BINARY_DIR/claude-statusline"
SETTINGS_PATH="$HOME/.claude/settings.json"
UPDATE_CHECK_FILE="$BINARY_DIR/.statusline-update-check"
UPDATE_INTERVAL=86400  # 24 hours in seconds

# --- Helper functions ---

warn() {
    echo "ensure-statusline: $*" >&2
}

detect_platform() {
    local os arch
    os="$(uname -s | tr '[:upper:]' '[:lower:]')"
    arch="$(uname -m)"

    case "$arch" in
        x86_64)  arch="amd64" ;;
        aarch64) arch="arm64" ;;
        arm64)   arch="arm64" ;;
        *)       warn "unsupported architecture: $arch"; return 1 ;;
    esac

    case "$os" in
        darwin|linux) ;;
        *)            warn "unsupported OS: $os"; return 1 ;;
    esac

    echo "${os}_${arch}"
}

get_latest_version() {
    gh release view --repo stvhay/claude-statusline --json tagName -q .tagName 2>/dev/null
}

get_installed_version() {
    if [ -x "$BINARY_PATH" ]; then
        "$BINARY_PATH" --version 2>/dev/null | head -1
    fi
}

needs_update_check() {
    # Check needed if file doesn't exist or is older than UPDATE_INTERVAL
    if [ ! -f "$UPDATE_CHECK_FILE" ]; then
        return 0
    fi
    local last_check now
    last_check="$(cat "$UPDATE_CHECK_FILE" 2>/dev/null)" || return 0
    now="$(date +%s)"
    [ $((now - last_check)) -ge $UPDATE_INTERVAL ]
}

record_update_check() {
    date +%s > "$UPDATE_CHECK_FILE" 2>/dev/null
}

download_and_install() {
    local platform="$1"
    local tmpdir

    tmpdir="$(mktemp -d)" || { warn "failed to create temp dir"; return 1; }
    # shellcheck disable=SC2064
    trap "rm -rf '$tmpdir'" EXIT

    # Download latest release matching our platform
    if ! gh release download --repo stvhay/claude-statusline \
        --pattern "claude-statusline_*_${platform}.tar.gz" \
        --dir "$tmpdir" 2>/dev/null; then
        warn "failed to download release for $platform"
        return 1
    fi

    # Extract the binary
    local tarball
    tarball="$(ls "$tmpdir"/claude-statusline_*_"${platform}".tar.gz 2>/dev/null | head -1)"
    if [ -z "$tarball" ]; then
        warn "no matching tarball found"
        return 1
    fi

    if ! tar -xzf "$tarball" -C "$tmpdir" 2>/dev/null; then
        warn "failed to extract tarball"
        return 1
    fi

    # Find the binary in extracted files
    local extracted_binary
    extracted_binary="$(find "$tmpdir" -name 'statusline' -type f ! -name '*.tar.gz' | head -1)"
    if [ -z "$extracted_binary" ]; then
        warn "binary not found in tarball"
        return 1
    fi

    mkdir -p "$BINARY_DIR"
    cp "$extracted_binary" "$BINARY_PATH"
    chmod +x "$BINARY_PATH"
}

ensure_settings() {
    # Merge statusLine and UserPromptSubmit hook into settings.json
    python3 - "$SETTINGS_PATH" "$BINARY_PATH" << 'PYEOF'
import json
import os
import sys

settings_path = sys.argv[1]
binary_path = sys.argv[2]
# Use ~ for portability in settings
binary_ref = "~/.claude/bin/claude-statusline"

# Read existing settings
settings = {}
if os.path.isfile(settings_path):
    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)
    except (json.JSONDecodeError, IOError):
        pass

changed = False

# Ensure statusLine setting
desired_status_line = {
    "type": "command",
    "command": binary_ref
}
if settings.get("statusLine") != desired_status_line:
    settings["statusLine"] = desired_status_line
    changed = True

# Ensure UserPromptSubmit hook
hooks = settings.setdefault("hooks", {})
uph_list = hooks.setdefault("UserPromptSubmit", [])

# Check if statusline hook already exists
has_statusline_hook = False
for entry in uph_list:
    for hook in entry.get("hooks", []):
        if "statusline" in hook.get("command", "").lower():
            has_statusline_hook = True
            break
    if has_statusline_hook:
        break

if not has_statusline_hook:
    uph_list.append({
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": binary_ref + " --hook"
            }
        ]
    })
    changed = True

if changed:
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
PYEOF
}

# --- Main ---

# Ensure gh is available
command -v gh >/dev/null 2>&1 || { warn "gh not found, skipping"; exit 0; }

platform="$(detect_platform)" || exit 0

if [ ! -x "$BINARY_PATH" ]; then
    # Binary missing — install
    download_and_install "$platform" || { warn "installation failed"; exit 0; }
    record_update_check
elif needs_update_check; then
    # Check for updates
    latest="$(get_latest_version)" || { record_update_check; exit 0; }
    installed="$(get_installed_version)"

    if [ -n "$latest" ] && [ "$latest" != "$installed" ]; then
        download_and_install "$platform" || { warn "update failed"; exit 0; }
    fi
    record_update_check
fi

# Ensure settings are configured
ensure_settings || { warn "settings configuration failed"; exit 0; }

exit 0
