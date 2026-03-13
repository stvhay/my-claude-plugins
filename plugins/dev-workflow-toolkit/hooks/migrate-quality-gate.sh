#!/usr/bin/env bash
# Claude Code SessionStart hook: removes stale version-pinned quality-gate.sh
# entries from project .claude/settings.json. These were written by earlier
# versions of project-init and break on plugin version updates.
#
# No-op if settings.json doesn't exist or has no quality-gate entries.
# Idempotent — safe to run every session.

SETTINGS_PATH=".claude/settings.json"

# Nothing to do if settings.json doesn't exist
[ -f "$SETTINGS_PATH" ] || exit 0

python3 - "$SETTINGS_PATH" << 'PYEOF'
import json
import os
import sys

settings_path = sys.argv[1]

# Read existing settings
try:
    with open(settings_path, "r") as f:
        settings = json.load(f)
except (json.JSONDecodeError, IOError):
    sys.exit(0)

hooks = settings.get("hooks")
if not isinstance(hooks, dict):
    sys.exit(0)

session_start = hooks.get("SessionStart")
if not isinstance(session_start, list):
    sys.exit(0)

# Filter out entire hook entries containing quality-gate.sh.
# project-init always wrote single-command entries, so removing the whole
# entry is safe — no other hooks share the same entry.
original_len = len(session_start)
filtered = []
for entry in session_start:
    dominated_by_qg = False
    for hook in entry.get("hooks", []):
        cmd = hook.get("command", "")
        if "quality-gate.sh" in cmd:
            dominated_by_qg = True
            break
    if not dominated_by_qg:
        filtered.append(entry)

if len(filtered) == original_len:
    # Nothing removed
    sys.exit(0)

# Update settings, cleaning up empty containers
if filtered:
    hooks["SessionStart"] = filtered
else:
    del hooks["SessionStart"]

if not hooks:
    del settings["hooks"]

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
PYEOF

exit 0
