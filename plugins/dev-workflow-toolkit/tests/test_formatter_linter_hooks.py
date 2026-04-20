"""Tests for post-edit-formatter and pre-commit-linter hooks."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import shutil

_HAS_RUFF = shutil.which("ruff") is not None

_HOOK_ENV_BASE = {"PATH": "/usr/bin:/bin:/usr/local/bin"}


@pytest.fixture
def hooks_dir(plugin_root: Path) -> Path:
    return plugin_root / "hooks"


def _run_hook(
    script: Path,
    cwd: Path,
    stdin_json: dict,
    extra_env: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a hook script with JSON stdin; return the result."""
    env = {**_HOOK_ENV_BASE, "HOME": str(cwd)}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(script)],
        cwd=cwd,
        input=json.dumps(stdin_json),
        capture_output=True,
        text=True,
        env=env,
    )


def _init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True, check=True,
    )


class TestPostEditFormatter:
    """Tests for post-edit-formatter.sh."""

    def test_script_exists_and_executable(self, hooks_dir: Path):
        script = hooks_dir / "post-edit-formatter.sh"
        assert script.exists(), f"Script not found: {script}"
        assert script.stat().st_mode & 0o111, "Script must be executable"

    def test_silent_when_no_file_path_in_input(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Hook exits 0 silently if tool_input has no file_path."""
        result = _run_hook(
            hooks_dir / "post-edit-formatter.sh",
            tmp_path,
            {"tool_input": {}},
        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_silent_when_file_does_not_exist(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Hook exits 0 silently if file_path does not exist on disk."""
        result = _run_hook(
            hooks_dir / "post-edit-formatter.sh",
            tmp_path,
            {"tool_input": {"file_path": str(tmp_path / "missing.py")}},
        )
        assert result.returncode == 0

    def test_silent_when_no_project_marker(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Hook exits 0 silently if no project marker is found walking up."""
        f = tmp_path / "orphan.py"
        f.write_text("x=1\n")
        result = _run_hook(
            hooks_dir / "post-edit-formatter.sh",
            tmp_path,
            {"tool_input": {"file_path": str(f)}},
        )
        assert result.returncode == 0

    @pytest.mark.skipif(not _HAS_RUFF, reason="ruff not available")
    def test_formats_python_file_with_ruff(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """pyproject.toml present + ruff on PATH → file gets formatted."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        unformatted = tmp_path / "src.py"
        unformatted.write_text("x  =  1\n")
        result = _run_hook(
            hooks_dir / "post-edit-formatter.sh",
            tmp_path,
            {"tool_input": {"file_path": str(unformatted)}},
            extra_env={"PATH": os.environ["PATH"]},
        )
        assert result.returncode == 0
        assert unformatted.read_text() == "x = 1\n"

    def test_silent_when_formatter_binary_absent(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """pyproject.toml present but ruff/black not on PATH → no-op, exit 0."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        f = tmp_path / "src.py"
        original = "x  =  1\n"
        f.write_text(original)
        result = _run_hook(
            hooks_dir / "post-edit-formatter.sh",
            tmp_path,
            {"tool_input": {"file_path": str(f)}},
        )
        assert result.returncode == 0
        assert f.read_text() == original

    @pytest.mark.skipif(not _HAS_RUFF, reason="ruff not available")
    def test_detects_project_marker_walking_up(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """File in nested subdir → walks up to find pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        subdir = tmp_path / "a" / "b" / "c"
        subdir.mkdir(parents=True)
        f = subdir / "deep.py"
        f.write_text("x=1\n")
        result = _run_hook(
            hooks_dir / "post-edit-formatter.sh",
            tmp_path,
            {"tool_input": {"file_path": str(f)}},
            extra_env={"PATH": os.environ["PATH"]},
        )
        assert result.returncode == 0
        assert f.read_text() == "x = 1\n"


class TestPreCommitLinter:
    """Tests for pre-commit-linter.sh."""

    def test_script_exists_and_executable(self, hooks_dir: Path):
        script = hooks_dir / "pre-commit-linter.sh"
        assert script.exists(), f"Script not found: {script}"
        assert script.stat().st_mode & 0o111, "Script must be executable"

    def test_silent_on_non_commit_bash(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Bash commands that are not 'git commit' → exit 0, no stderr."""
        _init_git_repo(tmp_path)
        result = _run_hook(
            hooks_dir / "pre-commit-linter.sh",
            tmp_path,
            {"tool_input": {"command": "ls -la"}},
        )
        assert result.returncode == 0
        assert result.stderr == ""

    def test_silent_when_no_staged_files(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """git commit with no staged files → exit 0."""
        _init_git_repo(tmp_path)
        result = _run_hook(
            hooks_dir / "pre-commit-linter.sh",
            tmp_path,
            {"tool_input": {"command": "git commit -m 'empty'"}},
        )
        assert result.returncode == 0

    def test_silent_when_no_toolchain_detected(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """git commit in a repo with no lang marker → exit 0."""
        _init_git_repo(tmp_path)
        f = tmp_path / "README.md"
        f.write_text("hi\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        result = _run_hook(
            hooks_dir / "pre-commit-linter.sh",
            tmp_path,
            {"tool_input": {"command": "git commit -m 'add readme'"}},
        )
        assert result.returncode == 0

    @pytest.mark.skipif(not _HAS_RUFF, reason="ruff not available")
    def test_allows_clean_python_commit(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Clean staged Python file → exit 0."""
        _init_git_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
        f = tmp_path / "clean.py"
        f.write_text("x = 1\n")
        subprocess.run(
            ["git", "add", "clean.py", "pyproject.toml"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        result = _run_hook(
            hooks_dir / "pre-commit-linter.sh",
            tmp_path,
            {"tool_input": {"command": "git commit -m 'ok'"}},
            extra_env={"PATH": os.environ["PATH"]},
        )
        assert result.returncode == 0

    @pytest.mark.skipif(not _HAS_RUFF, reason="ruff not available")
    def test_blocks_dirty_python_commit(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Staged Python file with lint error → exit 2, stderr mentions file."""
        _init_git_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text(
            "[project]\nname='x'\n"
            "[tool.ruff.lint]\nselect=['F']\n"
        )
        # F401 = unused import
        f = tmp_path / "dirty.py"
        f.write_text("import os\n")
        subprocess.run(
            ["git", "add", "dirty.py", "pyproject.toml"],
            cwd=tmp_path, capture_output=True, check=True,
        )
        result = _run_hook(
            hooks_dir / "pre-commit-linter.sh",
            tmp_path,
            {"tool_input": {"command": "git commit -m 'bad'"}},
            extra_env={"PATH": os.environ["PATH"]},
        )
        assert result.returncode == 2
        assert "dirty.py" in result.stderr

    def test_word_boundary_on_git_commit(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Commands containing 'gitcommit' (no space) should NOT trigger."""
        _init_git_repo(tmp_path)
        result = _run_hook(
            hooks_dir / "pre-commit-linter.sh",
            tmp_path,
            {"tool_input": {"command": "echo gitcommit"}},
        )
        assert result.returncode == 0
