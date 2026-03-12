
# direnv-worktree-hook-start
# Auto-installed by dev-workflow-toolkit plugin.
# Runs direnv allow in new worktrees when main worktree is approved.
_direnv_hook="$(cat "$(dirname "$0")/.direnv-post-checkout-path" 2>/dev/null)"
[ -x "$_direnv_hook" ] && "$_direnv_hook"
# direnv-worktree-hook-end
