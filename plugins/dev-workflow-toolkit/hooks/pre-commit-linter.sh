#!/usr/bin/env bash
# Hook: PreToolUse on Bash. Block `git commit` if staged files fail project lint.
# Exit 0 to allow, exit 2 to block (Claude Code PreToolUse protocol).

set -uo pipefail

INPUT=$(cat)
CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

# Word-boundary match for 'git commit'. Matches `git commit`, `git commit -m foo`,
# but NOT `gitcommit`, `echo "git-commit"`, or `notgit commit`.
if ! printf '%s' "$CMD" | grep -qE '(^|[^[:alnum:]_-])git[[:space:]]+commit([^[:alnum:]_-]|$)'; then
    exit 0
fi

git rev-parse --show-toplevel >/dev/null 2>&1 || exit 0
REPO_ROOT=$(git rev-parse --show-toplevel)

STAGED=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null || true)
[ -z "$STAGED" ] && exit 0

FAILED=0
STDERR_BUF=""

# Python: ruff (preferred) or flake8.
PY_FILES=$(printf '%s\n' "$STAGED" | grep -E '\.py$' || true)
if [ -n "$PY_FILES" ] && [ -f "$REPO_ROOT/pyproject.toml" ]; then
    if command -v ruff >/dev/null 2>&1; then
        if ! OUT=$(printf '%s\n' "$PY_FILES" | (cd "$REPO_ROOT" && xargs ruff check 2>&1)); then
            FAILED=1
            STDERR_BUF="${STDERR_BUF}${OUT}"$'\n'
        fi
    elif command -v flake8 >/dev/null 2>&1; then
        if ! OUT=$(printf '%s\n' "$PY_FILES" | (cd "$REPO_ROOT" && xargs flake8 2>&1)); then
            FAILED=1
            STDERR_BUF="${STDERR_BUF}${OUT}"$'\n'
        fi
    fi
fi

# JS/TS: eslint (requires package.json AND an eslint config).
JS_FILES=$(printf '%s\n' "$STAGED" | grep -E '\.(js|jsx|ts|tsx|mjs|cjs)$' || true)
if [ -n "$JS_FILES" ] && [ -f "$REPO_ROOT/package.json" ]; then
    if [ -f "$REPO_ROOT/.eslintrc.js" ] || [ -f "$REPO_ROOT/.eslintrc.json" ] || \
       [ -f "$REPO_ROOT/.eslintrc.yaml" ] || [ -f "$REPO_ROOT/.eslintrc.yml" ] || \
       [ -f "$REPO_ROOT/eslint.config.js" ] || [ -f "$REPO_ROOT/eslint.config.mjs" ]; then
        if command -v eslint >/dev/null 2>&1; then
            if ! OUT=$(printf '%s\n' "$JS_FILES" | (cd "$REPO_ROOT" && xargs eslint 2>&1)); then
                FAILED=1
                STDERR_BUF="${STDERR_BUF}${OUT}"$'\n'
            fi
        fi
    fi
fi

# Go: golangci-lint (preferred) or gofmt -l (any output = fail).
GO_FILES=$(printf '%s\n' "$STAGED" | grep -E '\.go$' || true)
if [ -n "$GO_FILES" ] && [ -f "$REPO_ROOT/go.mod" ]; then
    if command -v golangci-lint >/dev/null 2>&1; then
        if ! OUT=$(cd "$REPO_ROOT" && golangci-lint run 2>&1); then
            FAILED=1
            STDERR_BUF="${STDERR_BUF}${OUT}"$'\n'
        fi
    elif command -v gofmt >/dev/null 2>&1; then
        OUT=$(printf '%s\n' "$GO_FILES" | (cd "$REPO_ROOT" && xargs gofmt -l 2>&1))
        if [ -n "$OUT" ]; then
            FAILED=1
            STDERR_BUF="${STDERR_BUF}gofmt: files need formatting:"$'\n'"${OUT}"$'\n'
        fi
    fi
fi

# Rust: cargo clippy (project-wide; clippy doesn't reliably accept file paths).
RS_FILES=$(printf '%s\n' "$STAGED" | grep -E '\.rs$' || true)
if [ -n "$RS_FILES" ] && [ -f "$REPO_ROOT/Cargo.toml" ]; then
    if command -v cargo >/dev/null 2>&1; then
        if ! OUT=$(cd "$REPO_ROOT" && cargo clippy --quiet 2>&1); then
            FAILED=1
            STDERR_BUF="${STDERR_BUF}${OUT}"$'\n'
        fi
    fi
fi

if [ "$FAILED" -eq 1 ]; then
    printf 'Pre-commit lint failed:\n%s' "$STDERR_BUF" >&2
    exit 2
fi

exit 0
