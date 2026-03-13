#!/usr/bin/env bash
# Claude Code SessionStart hook: detects when Claude Code has written memory
# to ~/.claude/projects/<encoded-path>/memory/MEMORY.md and redirects the
# content back to the project root MEMORY.md.
#
# - If the file doesn't exist, exits silently.
# - If the file matches the expected stub SHA, exits silently.
# - If the file differs, appends content to project root MEMORY.md,
#   replants the stub, and prints a message for the agent.
#
# Registered in hooks.json as a SessionStart hook.

set -euo pipefail

# Find project root
project_root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# Derive Claude Code's encoded path: replace / with -
encoded_path="${project_root//\//-}"

# Allow override for testing; default to ~/.claude
claude_home="${CLAUDE_HOME:-$HOME/.claude}"
memory_file="${claude_home}/projects/${encoded_path}/memory/MEMORY.md"

# Exit silently if no memory file exists
[ -f "$memory_file" ] || exit 0

# Generate the expected stub content
stub="# Memory

All project memory is stored in ${project_root}/MEMORY.md. Read that file instead.
"

# Compute SHA1 of stub and actual file
stub_sha="$(printf '%s' "$stub" | sha1sum | cut -d' ' -f1)"
file_sha="$(sha1sum "$memory_file" | cut -d' ' -f1)"

# If SHAs match, stub is intact — exit silently
[ "$stub_sha" != "$file_sha" ] || exit 0

# --- Content differs: redirect ---

project_memory="${project_root}/MEMORY.md"

# Create project MEMORY.md if it doesn't exist
if [ ! -f "$project_memory" ]; then
    printf '# Memory\n' > "$project_memory"
fi

# Append relocated content with timestamp separator
{
    printf '\n## Relocated from ~/.claude/projects (%s)\n\n' "$(date +%Y-%m-%d)"
    cat "$memory_file"
} >> "$project_memory"

# Replant the stub
printf '%s' "$stub" > "$memory_file"

# Notify the agent
echo "memory-redirect: Claude Code wrote to ~/.claude/projects/ memory. Content has been appended to MEMORY.md at the project root. Please review the appended content and organize it into the appropriate sections."
