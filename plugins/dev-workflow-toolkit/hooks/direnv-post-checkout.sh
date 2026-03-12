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
[ "$PWD" != "$main_worktree" ] || exit 0

# Check if main worktree's .envrc is approved by direnv
main_approved="$(cd "$main_worktree" && direnv status 2>/dev/null | grep 'Found RC allowed' | head -1)"
case "$main_approved" in
    *"true"*) ;;
    *) exit 0 ;;  # Main worktree not approved — don't auto-allow
esac

# Inherit the trust: allow this worktree's .envrc
direnv allow >/dev/null 2>&1
