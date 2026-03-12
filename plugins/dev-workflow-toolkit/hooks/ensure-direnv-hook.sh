#!/usr/bin/env bash
# Claude Code SessionStart hook: ensures the direnv post-checkout git hook
# is installed. Runs at the start of every session. Silent on success.
#
# To be registered in hooks.json as a SessionStart hook.

# Exit silently if direnv is not available
command -v direnv >/dev/null 2>&1 || exit 0

# Find repo root
repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# Exit silently if no .envrc in repo root
[ -f "$repo_root/.envrc" ] || exit 0

# Find git hooks directory
hooks_path="$(git rev-parse --git-path hooks 2>/dev/null)" || exit 0

# Check if already installed (idempotency marker)
if [ -f "$hooks_path/post-checkout" ]; then
    if grep -q "direnv-worktree-hook-start" "$hooks_path/post-checkout" 2>/dev/null; then
        # Check if the installed path is still valid
        installed_path="$(sed -n '/direnv-worktree-hook-start/,/direnv-worktree-hook-end/p' "$hooks_path/post-checkout" | grep -o '"[^"]*direnv-post-checkout.sh"' | tr -d '"')"
        if [ -x "$installed_path" ]; then
            exit 0  # Already installed and path is valid
        fi
        # Stale path — remove old block and reinstall
        sed -i '/# direnv-worktree-hook-start/,/# direnv-worktree-hook-end/d' "$hooks_path/post-checkout"
    fi
fi

# Resolve the path to direnv-post-checkout.sh relative to this script
script_dir="$(cd "$(dirname "$0")" && pwd)"
post_checkout_script="$script_dir/direnv-post-checkout.sh"

if [ ! -x "$post_checkout_script" ]; then
    echo "ensure-direnv-hook: direnv-post-checkout.sh not found at $post_checkout_script" >&2
    exit 1
fi

# Fail on errors during filesystem mutations
set -e

# Ensure hooks directory exists
mkdir -p "$hooks_path"

# If no post-checkout hook exists, create one with a shebang
if [ ! -f "$hooks_path/post-checkout" ]; then
    printf '#!/bin/sh\n' > "$hooks_path/post-checkout"
fi

# Append the direnv block
cat >> "$hooks_path/post-checkout" <<EOF

# direnv-worktree-hook-start
# Auto-installed by dev-workflow-toolkit plugin.
# Runs direnv allow in new worktrees when main worktree is approved.
"$post_checkout_script"
# direnv-worktree-hook-end
EOF

# Ensure executable
chmod +x "$hooks_path/post-checkout"
