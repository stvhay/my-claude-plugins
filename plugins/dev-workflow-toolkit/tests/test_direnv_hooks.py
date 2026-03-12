"""Tests for direnv worktree hook scripts."""

import os
import shutil
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

    def test_allows_envrc_when_main_approved(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str
    ):
        """Hook calls 'direnv allow' when main worktree .envrc is approved."""
        # Create a real git repo as the main worktree
        main = tmp_path / "main"
        main.mkdir()
        subprocess.run(["git", "init", str(main)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(main), "config", "user.email", "test@test.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(main), "config", "user.name", "Test"],
            capture_output=True,
            check=True,
        )
        (main / ".envrc").write_text("# main envrc\n")

        # Create a worktree
        subprocess.run(
            ["git", "-C", str(main), "commit", "--allow-empty", "-m", "init"],
            capture_output=True,
            check=True,
        )
        wt = tmp_path / "worktree"
        subprocess.run(
            ["git", "-C", str(main), "worktree", "add", str(wt), "-b", "wt"],
            capture_output=True,
            check=True,
        )
        (wt / ".envrc").write_text("# wt envrc\n")

        # Create a mock direnv that logs calls
        log_file = tmp_path / "direnv_calls.log"
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_direnv = mock_bin / "direnv"
        mock_direnv.write_text(
            f"#!/usr/bin/env bash\n"
            f'echo "$@" >> "{log_file}"\n'
            f'if [ "$1" = "status" ]; then\n'
            f'  echo "Found RC allowed true"\n'
            f"fi\n"
        )
        mock_direnv.chmod(0o755)

        # Build PATH with mock bin first, plus git
        git_path = shutil.which("git")
        assert git_path
        git_dir = str(Path(git_path).parent)
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        env["PATH"] = f"{mock_bin}:{git_dir}:/usr/bin:/bin"

        result = subprocess.run(
            [bash_path, str(hooks_dir / "direnv-post-checkout.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(wt),
        )
        assert result.returncode == 0

        # Verify direnv allow was called
        calls = log_file.read_text()
        assert "allow" in calls, f"Expected 'direnv allow' call, got: {calls}"

    def test_no_allow_when_main_not_approved(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str
    ):
        """Hook must NOT call 'direnv allow' when main worktree is not approved."""
        # Create a real git repo as the main worktree
        main = tmp_path / "main"
        main.mkdir()
        subprocess.run(["git", "init", str(main)], capture_output=True, check=True)
        subprocess.run(
            ["git", "-C", str(main), "config", "user.email", "test@test.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(main), "config", "user.name", "Test"],
            capture_output=True,
            check=True,
        )
        (main / ".envrc").write_text("# main envrc\n")

        # Create a worktree
        subprocess.run(
            ["git", "-C", str(main), "commit", "--allow-empty", "-m", "init"],
            capture_output=True,
            check=True,
        )
        wt = tmp_path / "worktree"
        subprocess.run(
            ["git", "-C", str(main), "worktree", "add", str(wt), "-b", "wt"],
            capture_output=True,
            check=True,
        )
        (wt / ".envrc").write_text("# wt envrc\n")

        # Create a mock direnv that reports NOT approved
        log_file = tmp_path / "direnv_calls.log"
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_direnv = mock_bin / "direnv"
        mock_direnv.write_text(
            f"#!/usr/bin/env bash\n"
            f'echo "$@" >> "{log_file}"\n'
            f'if [ "$1" = "status" ]; then\n'
            f'  echo "Found RC allowed false"\n'
            f"fi\n"
        )
        mock_direnv.chmod(0o755)

        # Build PATH with mock bin first, plus git
        git_path = shutil.which("git")
        assert git_path
        git_dir = str(Path(git_path).parent)
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        env["PATH"] = f"{mock_bin}:{git_dir}:/usr/bin:/bin"

        result = subprocess.run(
            [bash_path, str(hooks_dir / "direnv-post-checkout.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(wt),
        )
        assert result.returncode == 0

        # Verify direnv allow was NOT called
        calls = log_file.read_text()
        assert "allow" not in calls, f"'direnv allow' should not be called, got: {calls}"
