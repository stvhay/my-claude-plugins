"""Tests for version bump and changelog validation hooks."""

import json
import subprocess
from pathlib import Path

import pytest

_HOOK_ENV = {"PATH": "/usr/bin:/bin:/usr/local/bin"}


@pytest.fixture
def hooks_dir(plugin_root: Path) -> Path:
    return plugin_root / "hooks"


def _init_git_repo(tmp_path: Path, version: str = "1.0.0") -> None:
    """Create a git repo with plugin.json committed."""
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
    (pj_dir / "plugin.json").write_text(
        json.dumps({"name": "test", "version": version})
    )
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path, capture_output=True, check=True,
    )


def _run_hook(script: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a hook script and return the result."""
    return subprocess.run(
        [str(script)],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**_HOOK_ENV, "HOME": str(cwd)},
    )


class TestCheckVersionBumpScript:
    """Tests for check-version-bump.sh."""

    def test_script_exists_and_executable(self, hooks_dir: Path):
        script = hooks_dir / "check-version-bump.sh"
        assert script.exists(), f"Script not found: {script}"
        assert script.stat().st_mode & 0o111, "Script must be executable"

    def test_silent_when_no_changes(self, hooks_dir: Path, tmp_path: Path):
        """In a clean git repo with no changes, hook should succeed silently."""
        _init_git_repo(tmp_path)
        result = _run_hook(hooks_dir / "check-version-bump.sh", tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_errors_when_source_changed_without_version_bump(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Source file changed but plugin.json version unchanged → error."""
        _init_git_repo(tmp_path)
        # Add a source file and stage it (hook checks staged + unstaged tracked)
        (tmp_path / "main.py").write_text("print('hello')\n")
        subprocess.run(["git", "add", "main.py"], cwd=tmp_path, capture_output=True, check=True)
        result = _run_hook(hooks_dir / "check-version-bump.sh", tmp_path)
        assert result.returncode == 1
        assert "VERSION_BUMP_REQUIRED" in result.stdout

    def test_passes_when_version_bumped_with_source(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Source file changed AND plugin.json changed → pass."""
        _init_git_repo(tmp_path)
        # Modify source and version file
        (tmp_path / "main.py").write_text("print('hello')\n")
        pj = tmp_path / ".claude-plugin" / "plugin.json"
        pj.write_text(json.dumps({"name": "test", "version": "1.1.0"}))
        result = _run_hook(hooks_dir / "check-version-bump.sh", tmp_path)
        assert result.returncode == 0

    def test_passes_when_only_docs_changed(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Only markdown/yaml changed → pass (not source files)."""
        _init_git_repo(tmp_path)
        (tmp_path / "README.md").write_text("# Updated\n")
        result = _run_hook(hooks_dir / "check-version-bump.sh", tmp_path)
        assert result.returncode == 0

    def test_passes_without_plugin_json(self, hooks_dir: Path, tmp_path: Path):
        """No plugin.json → not a plugin project, pass."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        (tmp_path / "main.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        (tmp_path / "main.py").write_text("x = 2\n")
        result = _run_hook(hooks_dir / "check-version-bump.sh", tmp_path)
        assert result.returncode == 0


class TestCheckChangelogScript:
    """Tests for check-changelog.sh."""

    def test_script_exists_and_executable(self, hooks_dir: Path):
        script = hooks_dir / "check-changelog.sh"
        assert script.exists(), f"Script not found: {script}"
        assert script.stat().st_mode & 0o111, "Script must be executable"

    def test_errors_when_version_bumped_without_changelog(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """plugin.json version changed but no changelog entry → error."""
        _init_git_repo(tmp_path)
        # Bump version in plugin.json without adding changelog
        pj = tmp_path / ".claude-plugin" / "plugin.json"
        pj.write_text(json.dumps({"name": "test", "version": "1.1.0"}))
        result = _run_hook(hooks_dir / "check-changelog.sh", tmp_path)
        assert result.returncode == 1
        assert "CHANGELOG_MISSING" in result.stdout

    def test_passes_when_version_bumped_with_changelog(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """plugin.json version changed AND changelog has entry → pass."""
        _init_git_repo(tmp_path)
        pj = tmp_path / ".claude-plugin" / "plugin.json"
        pj.write_text(json.dumps({"name": "test", "version": "1.1.0"}))
        (tmp_path / "CHANGELOG.md").write_text("# Changelog\n\n## v1.1.0\n\n- Feature\n")
        result = _run_hook(hooks_dir / "check-changelog.sh", tmp_path)
        assert result.returncode == 0

    def test_silent_when_no_version_change(self, hooks_dir: Path, tmp_path: Path):
        """No plugin.json change → pass silently."""
        _init_git_repo(tmp_path)
        result = _run_hook(hooks_dir / "check-changelog.sh", tmp_path)
        assert result.returncode == 0

    def test_passes_without_plugin_json(self, hooks_dir: Path, tmp_path: Path):
        """No plugin.json → not a plugin project, pass."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
        result = _run_hook(hooks_dir / "check-changelog.sh", tmp_path)
        assert result.returncode == 0


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
