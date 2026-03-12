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

# Resolve paths to our shipped files
script_dir="$(cd "$(dirname "$0")" && pwd)"
post_checkout_script="$script_dir/direnv-post-checkout.sh"
fragment_file="$script_dir/post-checkout-fragment.sh"

if [ ! -x "$post_checkout_script" ]; then
    echo "ensure-direnv-hook: direnv-post-checkout.sh not found at $post_checkout_script" >&2
    exit 1
fi

if [ ! -f "$fragment_file" ]; then
    echo "ensure-direnv-hook: post-checkout-fragment.sh not found at $fragment_file" >&2
    exit 1
fi

# Fail on errors during filesystem mutations
set -e

# Ensure hooks directory exists
mkdir -p "$hooks_path"

# Always write the path file — handles stale paths automatically
echo "$post_checkout_script" > "$hooks_path/.direnv-post-checkout-path"

# If the hook fragment is already installed, we're done
if [ -f "$hooks_path/post-checkout" ] && grep -q "direnv-worktree-hook-start" "$hooks_path/post-checkout" 2>/dev/null; then
    exit 0
fi

# If no post-checkout hook exists, create one with a shebang
if [ ! -f "$hooks_path/post-checkout" ]; then
    printf '#!/bin/sh\n' > "$hooks_path/post-checkout"
fi

# Append the static hook fragment
cat "$fragment_file" >> "$hooks_path/post-checkout"

# Ensure executable
chmod +x "$hooks_path/post-checkout"
