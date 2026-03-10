"""
Structural validation tests for the dev-workflow-toolkit plugin.

Replaces:
  - validate-frontmatter.sh
  - validate-specs.sh
  - test-project-init.sh
  - test-setup-rag.sh
"""

import json
import re
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_frontmatter(path: Path) -> dict:
    """Return parsed YAML frontmatter from a Markdown file, or raise."""
    text = path.read_text()
    assert text.startswith("---"), f"{path}: file does not start with '---'"
    # Find closing marker (must be on its own line)
    end = text.find("\n---", 3)
    assert end != -1, f"{path}: no closing '---' for frontmatter"
    fm_text = text[3:end].strip()
    return yaml.safe_load(fm_text) or {}


def _skill_dirs(skills_dir: Path) -> list[Path]:
    """Return all immediate subdirectories of skills/ that contain a SKILL.md."""
    return sorted(d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists())


# ---------------------------------------------------------------------------
# validate-frontmatter.sh
# ---------------------------------------------------------------------------


class TestFrontmatterValidation:
    """Validates YAML frontmatter in all SKILL.md files."""

    def _all_skill_mds(self, skills_dir: Path) -> list[Path]:
        return sorted(skills_dir.rglob("SKILL.md"))

    def test_frontmatter_starts_with_dashes(self, skills_dir: Path, skill_mds: list[Path]):
        for skill_md in skill_mds:
            text = skill_md.read_text()
            assert text.startswith("---"), (
                f"{skill_md.relative_to(skills_dir)}: must start with '---'"
            )

    def test_frontmatter_has_name(self, skills_dir: Path, skill_mds: list[Path]):
        for skill_md in skill_mds:
            fm = _parse_frontmatter(skill_md)
            assert "name" in fm, (
                f"{skill_md.relative_to(skills_dir)}: missing 'name' field in frontmatter"
            )

    def test_frontmatter_has_description(self, skills_dir: Path, skill_mds: list[Path]):
        for skill_md in skill_mds:
            fm = _parse_frontmatter(skill_md)
            assert "description" in fm, (
                f"{skill_md.relative_to(skills_dir)}: missing 'description' field in frontmatter"
            )

    def test_name_matches_directory(self, skills_dir: Path, skill_mds: list[Path]):
        for skill_md in skill_mds:
            fm = _parse_frontmatter(skill_md)
            if "name" not in fm:
                continue  # caught by test_frontmatter_has_name
            expected = skill_md.parent.name
            assert fm["name"] == expected, (
                f"{skill_md.relative_to(skills_dir)}: "
                f"name '{fm['name']}' does not match directory '{expected}'"
            )

    def test_name_format(self, skills_dir: Path, skill_mds: list[Path]):
        pattern = re.compile(r"^[a-z0-9-]{1,64}$")
        for skill_md in skill_mds:
            fm = _parse_frontmatter(skill_md)
            if "name" not in fm:
                continue
            name = fm["name"]
            assert pattern.match(name), (
                f"{skill_md.relative_to(skills_dir)}: name '{name}' must match ^[a-z0-9-]{{1,64}}$"
            )


# ---------------------------------------------------------------------------
# validate-specs.sh
# ---------------------------------------------------------------------------

MIN_LINES = 80
MAX_LINES = 350


class TestSpecFiles:
    """Each plugin must have a skills/SPEC.md of appropriate length."""

    def _plugin_dirs(self, repo_root: Path) -> list[Path]:
        plugins_dir = repo_root / "plugins"
        return sorted(d for d in plugins_dir.iterdir() if d.is_dir())

    def test_spec_md_exists(self, repo_root: Path):
        missing = []
        for plugin_dir in self._plugin_dirs(repo_root):
            spec = plugin_dir / "skills" / "SPEC.md"
            if not spec.exists():
                missing.append(str(plugin_dir.relative_to(repo_root)))
        assert not missing, f"Missing skills/SPEC.md in: {missing}"

    def test_spec_md_line_count(self, repo_root: Path):
        violations = []
        for plugin_dir in self._plugin_dirs(repo_root):
            spec = plugin_dir / "skills" / "SPEC.md"
            if not spec.exists():
                continue  # covered by test_spec_md_exists
            lines = len(spec.read_text().splitlines())
            if not (MIN_LINES <= lines <= MAX_LINES):
                violations.append(
                    f"{spec.relative_to(repo_root)}: {lines} lines "
                    f"(expected {MIN_LINES}–{MAX_LINES})"
                )
        assert not violations, "SPEC.md line count out of range:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# test-project-init.sh
# ---------------------------------------------------------------------------

REQUIRED_TEMPLATES = [
    "bug-report.yml",
    "feature-request.yml",
    "pull_request_template.md",
    "CONTRIBUTING.md",
]


class TestProjectInit:
    """Validates the project-init skill and its templates."""

    @pytest.fixture
    def templates_dir(self, plugin_root: Path) -> Path:
        return plugin_root / "skills" / "project-init" / "templates"

    @pytest.fixture
    def project_init_skill(self, plugin_root: Path) -> Path:
        return plugin_root / "skills" / "project-init" / "SKILL.md"

    def test_templates_directory_exists(self, templates_dir: Path):
        assert templates_dir.is_dir(), f"Templates directory not found: {templates_dir}"

    @pytest.mark.parametrize("template_name", REQUIRED_TEMPLATES)
    def test_required_template_exists(self, templates_dir: Path, template_name: str):
        path = templates_dir / template_name
        assert path.exists(), f"Required template missing: {template_name}"

    def test_yaml_templates_have_required_fields(self, templates_dir: Path):
        if not templates_dir.is_dir():
            pytest.skip("templates directory missing")
        for yml_file in sorted(templates_dir.glob("*.yml")):
            text = yml_file.read_text()
            for field in ("name:", "description:", "body:"):
                assert field in text, f"{yml_file.name}: missing required field '{field}'"

    def test_markdown_templates_not_empty(self, templates_dir: Path):
        if not templates_dir.is_dir():
            pytest.skip("templates directory missing")
        for md_file in sorted(templates_dir.glob("*.md")):
            text = md_file.read_text()
            assert len(text) >= 50, (
                f"{md_file.name}: markdown template too short ({len(text)} chars, need >=50)"
            )

    def test_skill_references_templates_dir(self, project_init_skill: Path):
        assert project_init_skill.exists(), f"SKILL.md not found: {project_init_skill}"
        text = project_init_skill.read_text()
        assert "templates/" in text, (
            "skills/project-init/SKILL.md does not reference 'templates/' directory"
        )


# ---------------------------------------------------------------------------
# test-setup-rag.sh
# ---------------------------------------------------------------------------


class TestSetupRag:
    """Validates the setup-rag skill."""

    @pytest.fixture
    def skill_file(self, plugin_root: Path) -> Path:
        return plugin_root / "skills" / "setup-rag" / "SKILL.md"

    def test_skill_file_exists(self, skill_file: Path):
        assert skill_file.exists(), f"setup-rag SKILL.md not found: {skill_file}"

    def test_contains_prerequisite_check(self, skill_file: Path):
        if not skill_file.exists():
            pytest.skip("skill file missing")
        assert "which uv" in skill_file.read_text(), (
            "SKILL.md must contain 'which uv' prerequisite check"
        )

    def test_contains_mcp_servers(self, skill_file: Path):
        if not skill_file.exists():
            pytest.skip("skill file missing")
        assert "mcpServers" in skill_file.read_text(), "SKILL.md must reference 'mcpServers'"

    @pytest.mark.parametrize(
        "artifact",
        [
            "ragling init",
            "ragling.json",
            ".ragling",
            "mcpServers.ragling",
        ],
    )
    def test_contains_artifact(self, skill_file: Path, artifact: str):
        if not skill_file.exists():
            pytest.skip("skill file missing")
        assert artifact in skill_file.read_text(), f"SKILL.md must reference artifact '{artifact}'"

    def test_references_mcp_json(self, skill_file: Path):
        if not skill_file.exists():
            pytest.skip("skill file missing")
        assert ".mcp.json" in skill_file.read_text(), "SKILL.md must reference '.mcp.json'"

    def test_contains_gitignore(self, skill_file: Path):
        if not skill_file.exists():
            pytest.skip("skill file missing")
        assert "gitignore" in skill_file.read_text(), "SKILL.md must mention 'gitignore'"

    def test_project_isolation(self, skill_file: Path):
        if not skill_file.exists():
            pytest.skip("skill file missing")
        text = skill_file.read_text()
        assert "project" in text, "SKILL.md must contain 'project'"
        assert "isolation" in text or "isolated" in text, (
            "SKILL.md must contain 'isolation' or 'isolated'"
        )


# ---------------------------------------------------------------------------
# Version consistency
# ---------------------------------------------------------------------------


class TestVersionConsistency:
    """Validates that version numbers are consistent across plugin files."""

    def test_plugin_json_and_pyproject_versions_match(self, plugin_root: Path):
        plugin_json = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
        pyproject = (plugin_root / "pyproject.toml").read_text()
        # Extract version from pyproject.toml
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        assert match, "pyproject.toml missing version field"
        pyproject_version = match.group(1)
        plugin_json_version = plugin_json["version"]
        assert plugin_json_version == pyproject_version, (
            f"plugin.json version ({plugin_json_version}) != "
            f"pyproject.toml version ({pyproject_version})"
        )

    def test_changelog_has_section_for_current_version(self, plugin_root: Path):
        plugin_json = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
        version = plugin_json["version"]
        changelog = (plugin_root / "CHANGELOG.md").read_text()
        heading = f"## v{version}"
        assert heading in changelog, f"CHANGELOG.md missing section '{heading}' for current version"
