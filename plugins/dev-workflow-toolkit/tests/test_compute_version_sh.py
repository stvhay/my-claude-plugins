"""Integration tests for compute-version.sh shell wrapper."""

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
