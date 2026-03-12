#!/usr/bin/env bash
# Claude Code SessionStart hook: ensures the direnv post-checkout git hook
# is installed. Runs at the start of every session. Silent on success.
#
# Registered in hooks.json as a SessionStart hook.

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
    grep -q "direnv-worktree-hook-start" "$hooks_path/post-checkout" 2>/dev/null && exit 0
fi

# Resolve the path to direnv-post-checkout.sh relative to this script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
POST_CHECKOUT_SCRIPT="$SCRIPT_DIR/direnv-post-checkout.sh"

if [ ! -x "$POST_CHECKOUT_SCRIPT" ]; then
    echo "ensure-direnv-hook: direnv-post-checkout.sh not found at $POST_CHECKOUT_SCRIPT" >&2
    exit 1
fi

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
"$POST_CHECKOUT_SCRIPT"
# direnv-worktree-hook-end
EOF

# Ensure executable
chmod +x "$hooks_path/post-checkout"
