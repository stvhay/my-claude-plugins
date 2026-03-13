#!/usr/bin/env bash
# Run all plugin test suites.
#
# Discovers plugins/*/tests/run-all.sh and runs each.
# Pass any flags through to the per-plugin runners (which pass them to pytest).
#
# Environment:
#   CI_CAPABILITIES  space-separated list of available resource capabilities
#
# Examples:
#   ./tests/run-all.sh              # run all plugin tests
#   ./tests/run-all.sh -v           # verbose
#   CI_CAPABILITIES="gpu" ./tests/run-all.sh  # with GPU capability

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

found=0
failures=0
passed=()
failed=()

for runner in "$REPO_ROOT"/plugins/*/tests/run-all.sh; do
  [ -f "$runner" ] || continue
  plugin="$(basename "$(dirname "$(dirname "$runner")")")"
  found=$((found + 1))
  echo ""
  echo "=== $plugin ==="
  if "$runner" "$@"; then
    passed+=("$plugin")
  else
    failures=$((failures + 1))
    failed+=("$plugin")
  fi
done

echo ""
echo "=== Summary ==="
echo "Plugins tested: $found"
echo "Passed: ${#passed[@]} (${passed[*]:-none})"
if [ $failures -gt 0 ]; then
  echo "Failed: $failures (${failed[*]})"
  exit 1
else
  echo "Failed: 0"
fi
