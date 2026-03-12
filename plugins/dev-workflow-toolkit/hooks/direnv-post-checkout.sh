#!/usr/bin/env bash
# Git post-checkout hook logic for direnv worktree initialization.
# Auto-allows .envrc in new worktrees when the main worktree's .envrc
# is already approved. Inherits trust, never grants new trust.
#
# Called by the git post-checkout hook (installed by ensure-direnv-hook.sh).

# Exit silently if direnv is not available
command -v direnv >/dev/null 2>&1 || exit 0

# Exit silently if no .envrc in this checkout
[ -f .envrc ] || exit 0

# Get main worktree path (first line of git worktree list)
main_worktree="$(git worktree list --porcelain 2>/dev/null | head -1 | sed 's/^worktree //')"
[ -n "$main_worktree" ] || exit 0

# If we ARE the main worktree, nothing to do — user manages their own approval
[ "$(pwd -P)" != "$main_worktree" ] || exit 0

# Check if main worktree's .envrc is approved by direnv.
# Uses 'direnv exec' as a programmatic check — exits 0 only when allowed.
direnv exec "$main_worktree" true 2>/dev/null || exit 0

# Inherit the trust: allow this worktree's .envrc
direnv allow >/dev/null 2>&1
