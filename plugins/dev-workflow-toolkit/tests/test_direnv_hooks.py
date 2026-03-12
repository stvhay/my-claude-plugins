"""Tests for direnv worktree hook scripts."""

import os
import stat
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


# --- ensure-direnv-hook.sh tests ---


class TestEnsureDirenvHook:
    """Tests for the SessionStart hook that installs the git post-checkout hook."""

    def test_script_exists(self, hooks_dir: Path):
        script = hooks_dir / "ensure-direnv-hook.sh"
        assert script.exists(), "ensure-direnv-hook.sh must exist"

    def test_script_is_executable(self, hooks_dir: Path):
        script = hooks_dir / "ensure-direnv-hook.sh"
        assert os.access(script, os.X_OK), "ensure-direnv-hook.sh must be executable"

    def test_exits_cleanly_when_no_direnv(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str
    ):
        """Hook must exit 0 when direnv is not on PATH."""
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        env["PATH"] = str(tmp_path)  # empty PATH — no direnv
        result = subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    def test_exits_cleanly_when_no_envrc(self, hooks_dir: Path, tmp_path: Path):
        """Hook must exit 0 when no .envrc in repo root."""
        # Init a git repo without .envrc
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        result = subprocess.run(
            [str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    def test_no_stdout_on_success(self, hooks_dir: Path, tmp_path: Path):
        """Hook must be silent on success."""
        result = subprocess.run(
            [str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.stdout == ""

    def test_installs_post_checkout_hook(self, hooks_dir: Path, tmp_path: Path):
        """Hook must install the post-checkout hook in a git repo with .envrc."""
        # Set up a git repo with .envrc
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".envrc").write_text("# test envrc\n")

        result = subprocess.run(
            [str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        hook_file = tmp_path / ".git" / "hooks" / "post-checkout"
        assert hook_file.exists(), "post-checkout hook must be created"
        assert os.access(hook_file, os.X_OK), "post-checkout hook must be executable"
        assert "direnv-worktree-hook-start" in hook_file.read_text()

    def test_idempotent_installation(self, hooks_dir: Path, tmp_path: Path):
        """Running twice must not duplicate the hook block."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # Run twice
        for _ in range(2):
            subprocess.run(
                [str(hooks_dir / "ensure-direnv-hook.sh")],
                capture_output=True,
                text=True,
                cwd=str(tmp_path),
            )

        hook_file = tmp_path / ".git" / "hooks" / "post-checkout"
        content = hook_file.read_text()
        assert content.count("direnv-worktree-hook-start") == 1, \
            "Hook block must appear exactly once"

    def test_preserves_existing_post_checkout(self, hooks_dir: Path, tmp_path: Path):
        """Must append to existing post-checkout hooks, not replace."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # Create existing post-checkout hook
        hook_dir = tmp_path / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        hook_file = hook_dir / "post-checkout"
        hook_file.write_text("#!/bin/sh\necho 'existing hook'\n")
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

        subprocess.run(
            [str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        content = hook_file.read_text()
        assert "existing hook" in content, "Existing hook content must be preserved"
        assert "direnv-worktree-hook-start" in content, "Direnv block must be appended"

    def test_error_when_post_checkout_script_missing(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str
    ):
        """Hook must exit 1 with stderr when direnv-post-checkout.sh is not found."""
        # Set up a git repo with .envrc
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # Create a fake hooks dir with only ensure-direnv-hook.sh (no post-checkout script)
        fake_hooks = tmp_path / "fake-hooks"
        fake_hooks.mkdir()
        fake_script = fake_hooks / "ensure-direnv-hook.sh"
        # Copy the real script but into a directory without direnv-post-checkout.sh
        shutil.copy2(str(hooks_dir / "ensure-direnv-hook.sh"), str(fake_script))

        result = subprocess.run(
            [bash_path, str(fake_script)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 1, "Must exit 1 when post-checkout script is missing"
        assert "direnv-post-checkout.sh not found" in result.stderr

    def test_reinstalls_when_path_is_stale(
        self, hooks_dir: Path, tmp_path: Path
    ):
        """Hook must reinstall if the embedded path to direnv-post-checkout.sh is stale."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # First install
        subprocess.run(
            [str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

        hook_file = tmp_path / ".git" / "hooks" / "post-checkout"
        assert hook_file.exists()

        # Corrupt the installed path to simulate a stale reference
        content = hook_file.read_text()
        content = content.replace(
            str(hooks_dir / "direnv-post-checkout.sh"),
            "/nonexistent/path/direnv-post-checkout.sh",
        )
        hook_file.write_text(content)

        # Run again — should detect stale path and reinstall
        result = subprocess.run(
            [str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        # Verify the block was reinstalled with the correct path
        new_content = hook_file.read_text()
        assert new_content.count("direnv-worktree-hook-start") == 1, \
            "Hook block must appear exactly once after reinstall"
        assert str(hooks_dir / "direnv-post-checkout.sh") in new_content, \
            "Reinstalled block must contain the correct path"

    def test_has_shebang(self, hooks_dir: Path):
        script = hooks_dir / "ensure-direnv-hook.sh"
        first_line = script.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "Script must have a shebang line"
