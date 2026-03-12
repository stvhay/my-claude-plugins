"""Tests for direnv worktree hook scripts."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def hooks_dir(plugin_root: Path) -> Path:
    return plugin_root / "hooks"


@pytest.fixture(scope="session")
def bash_path() -> str:
    """Absolute path to bash, so we can invoke it even with a stripped PATH."""
    path = shutil.which("bash")
    assert path, "bash must be available"
    return path


# --- direnv-post-checkout.sh tests ---


class TestDirenvPostCheckout:
    """Tests for the post-checkout hook logic."""

    def test_script_exists(self, hooks_dir: Path):
        script = hooks_dir / "direnv-post-checkout.sh"
        assert script.exists(), "direnv-post-checkout.sh must exist"

    def test_script_is_executable(self, hooks_dir: Path):
        script = hooks_dir / "direnv-post-checkout.sh"
        assert os.access(script, os.X_OK), "direnv-post-checkout.sh must be executable"

    def test_exits_cleanly_when_no_direnv(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str
    ):
        """Hook must exit 0 when direnv is not on PATH."""
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        env["PATH"] = str(tmp_path)  # empty PATH — no direnv
        result = subprocess.run(
            [bash_path, str(hooks_dir / "direnv-post-checkout.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    def test_exits_cleanly_when_no_envrc(self, hooks_dir: Path, tmp_path: Path):
        """Hook must exit 0 when no .envrc exists."""
        result = subprocess.run(
            [str(hooks_dir / "direnv-post-checkout.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    def test_has_shebang(self, hooks_dir: Path):
        script = hooks_dir / "direnv-post-checkout.sh"
        first_line = script.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "Script must have a shebang line"

    def test_no_stdout_on_success(self, hooks_dir: Path, tmp_path: Path):
        """Hook must be silent on success (no output to agent)."""
        result = subprocess.run(
            [str(hooks_dir / "direnv-post-checkout.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.stdout == ""
