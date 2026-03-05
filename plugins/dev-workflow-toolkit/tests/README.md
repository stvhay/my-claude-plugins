# dev-workflow-toolkit Tests

Test suite for the dev-workflow-toolkit plugin.

## Running Tests

Run all tests:
```bash
./tests/run-all.sh
```

Run individual tests:
```bash
./tests/validate-frontmatter.sh
./tests/test-project-init.sh
./tests/test-setup-rag.sh
```

## Test Coverage

### validate-frontmatter.sh
Validates YAML frontmatter in all SKILL.md files:
- Checks frontmatter delimiters (`---`)
- Verifies required fields (`name`, `description`)
- Ensures name matches directory name
- Validates name format (lowercase, hyphenated, max 64 chars)

**Tests:** 16 skills
**Addresses:** Finding 1 - YAML frontmatter validation

### test-project-init.sh
Validates project-init skill templates:
- Verifies templates directory exists
- Checks required template files present
- Validates YAML structure in GitHub issue templates
- Ensures Markdown templates have content
- Tests path resolution in skill

**Tests:** 10 validations
**Addresses:** Finding 1 - Template generation, Finding 4 - Path resolution

### test-setup-rag.sh
Validates setup-rag skill configuration logic:
- Checks prerequisite detection (local-rag)
- Verifies MCP server configuration structure
- Validates required environment variables
- Ensures .mcp.json reference present
- Tests gitignore safety guidance
- Confirms project isolation concept

**Tests:** 11 validations
**Addresses:** Finding 1 - Configuration generation

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

## Test Philosophy

These tests follow the plugin's own TDD guidance by:
- Testing behavior, not implementation
- Using simple, minimal dependencies (bash only)
- Validating real configuration structures
- Ensuring skills are self-contained and discoverable
