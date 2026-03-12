"""Tests for version bump and changelog validation hooks."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def hooks_dir(plugin_root: Path) -> Path:
    return plugin_root / "hooks"


class TestCheckVersionBumpScript:
    """Tests for check-version-bump.sh."""

    def test_script_exists_and_executable(self, hooks_dir: Path):
        script = hooks_dir / "check-version-bump.sh"
        assert script.exists(), f"Script not found: {script}"
        assert script.stat().st_mode & 0o111, "Script must be executable"

    def test_silent_when_no_changes(self, hooks_dir: Path, tmp_path: Path):
        """In a clean git repo with no changes, hook should succeed silently."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        pj_dir = tmp_path / ".claude-plugin"
        pj_dir.mkdir()
        (pj_dir / "plugin.json").write_text(json.dumps({"name": "t", "version": "1.0.0"}))
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path, capture_output=True, check=True,
        )

        script = hooks_dir / "check-version-bump.sh"
        result = subprocess.run(
            [str(script)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            env={"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(tmp_path)},
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""


class TestCheckChangelogScript:
    """Tests for check-changelog.sh."""

    def test_script_exists_and_executable(self, hooks_dir: Path):
        script = hooks_dir / "check-changelog.sh"
        assert script.exists(), f"Script not found: {script}"
        assert script.stat().st_mode & 0o111, "Script must be executable"


class TestHooksJsonRegistration:
    """Verify hooks are registered in hooks.json."""

    def test_stop_hooks_registered(self, hooks_dir: Path):
        hooks_json = json.loads((hooks_dir / "hooks.json").read_text())
        assert "Stop" in hooks_json["hooks"], "Stop event not in hooks.json"
        stop_hooks = hooks_json["hooks"]["Stop"]
        commands = []
        for entry in stop_hooks:
            for hook in entry.get("hooks", []):
                commands.append(hook.get("command", ""))
        assert any("check-version-bump" in c for c in commands), (
            "check-version-bump.sh not registered in Stop hooks"
        )
        assert any("check-changelog" in c for c in commands), (
            "check-changelog.sh not registered in Stop hooks"
        )
