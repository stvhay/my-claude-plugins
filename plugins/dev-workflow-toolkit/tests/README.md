# dev-workflow-toolkit Tests

pytest-based test suite for the dev-workflow-toolkit plugin.

## Running Tests

```bash
# All tests
./tests/run-all.sh

# Verbose output
./tests/run-all.sh -v

# Filter by name
./tests/run-all.sh -k quality

# Count tests without running
uv run --project plugins/dev-workflow-toolkit pytest --collect-only -q tests/
```

## Test Modules

### test_structure.py
Structural validation replacing validate-frontmatter.sh, validate-specs.sh,
test-project-init.sh, and test-setup-rag.sh:
- Frontmatter validation (all SKILL.md files)
- SPEC.md existence and line count per plugin
- Project-init template structure and content
- Setup-rag skill configuration patterns

### test_integration.py
Integration tests replacing test-integration.sh:
- Skill loading (all skills have valid frontmatter)
- Dependency resolution (cross-skill references)
- Template path resolution
- Reference file directories
- Trigger pattern uniqueness
- MCP configuration patterns

### test_quality_gate.py
Quality gate validation replacing test-quality-gate.sh:
- Smoke tests against real repo (all checks pass)
- Argument validation (--help, unknown flags)
- Fixture-based negative tests (duplicate INV/FAIL, gaps, format variants)
- Skill structure negative cases (missing frontmatter, name mismatches)
- Doc-stats stat-check footnote validation

## Test Philosophy

- Tests use pytest fixtures and parametrize for clarity
- Quality gate tests create temporary git repos as fixtures
- `pytest --collect-only` enables sub-second test counting for doc-stats
