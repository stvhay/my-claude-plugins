"""Integration tests for compute-version.sh shell wrapper."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def script_path(plugin_root: Path) -> Path:
    return plugin_root / "scripts" / "compute-version.sh"


class TestComputeVersionShell:
    """Tests the shell wrapper delegates correctly to Python."""

    def test_script_exists_and_executable(self, script_path: Path):
        assert script_path.exists(), f"Script not found: {script_path}"
        assert script_path.stat().st_mode & 0o111, "Script must be executable"

    def test_prints_next_version(self, script_path: Path, plugin_root: Path):
        """Dry run: prints next version to stdout without modifying files."""
        result = subprocess.run(
            [str(script_path), "patch", "--project-root", str(plugin_root)],
            capture_output=True,
            text=True,
            cwd=plugin_root,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        version = result.stdout.strip()
        assert len(version.split(".")) == 3, f"Not a valid version: {version}"

    def test_invalid_bump_type_errors(self, script_path: Path, plugin_root: Path):
        result = subprocess.run(
            [str(script_path), "invalid", "--project-root", str(plugin_root)],
            capture_output=True,
            text=True,
            cwd=plugin_root,
        )
        assert result.returncode != 0

    def test_update_writes_version_files(self, script_path: Path, tmp_path: Path):
        """--update flag writes new version to plugin.json and pyproject.toml."""
        # Set up version files
        pj_dir = tmp_path / ".claude-plugin"
        pj_dir.mkdir()
        (pj_dir / "plugin.json").write_text(
            json.dumps({"name": "test", "version": "1.0.0"}, indent=2) + "\n"
        )
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "1.0.0"\n'
        )
        # Changelog required for --update
        (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## v1.1.0\n\n- Feat\n")

        result = subprocess.run(
            [str(script_path), "minor", "--update", "--project-root", str(tmp_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert result.stdout.strip() == "1.1.0"

        # Verify files were updated
        pj_data = json.loads((pj_dir / "plugin.json").read_text())
        assert pj_data["version"] == "1.1.0"

        toml_content = (tmp_path / "pyproject.toml").read_text()
        assert '"1.1.0"' in toml_content
