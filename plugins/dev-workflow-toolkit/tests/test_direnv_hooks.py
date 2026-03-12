"""Tests for direnv worktree hook scripts."""

import json
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

        # Create a mock direnv that logs calls.
        # 'exec <dir> true' exits 0 (approved); 'allow' is logged.
        log_file = tmp_path / "direnv_calls.log"
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_direnv = mock_bin / "direnv"
        mock_direnv.write_text(
            f'#!/usr/bin/env bash\n'
            f'echo "$@" >> "{log_file}"\n'
            f'if [ "$1" = "exec" ]; then\n'
            f'  shift 2  # skip dir\n'
            f'  exec "$@"\n'
            f'fi\n'
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
        calls = log_file.read_text().splitlines()
        assert any(line.strip() == "allow" for line in calls), \
            f"Expected 'direnv allow' call, got: {calls}"

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

        # Create a mock direnv where 'exec' exits 1 (not approved)
        log_file = tmp_path / "direnv_calls.log"
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_direnv = mock_bin / "direnv"
        mock_direnv.write_text(
            f'#!/usr/bin/env bash\n'
            f'echo "$@" >> "{log_file}"\n'
            f'if [ "$1" = "exec" ]; then\n'
            f'  exit 1\n'
            f'fi\n'
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
        calls = log_file.read_text().splitlines()
        assert not any(line.strip() == "allow" for line in calls), \
            f"'direnv allow' should not be called, got: {calls}"


# --- ensure-direnv-hook.sh tests ---


class TestEnsureDirenvHook:
    """Tests for the SessionStart hook that installs the git post-checkout hook."""

    @pytest.fixture()
    def env_with_mock_direnv(self, tmp_path: Path) -> dict:
        """Provide an env dict with a mock direnv on PATH.

        The ensure-direnv-hook.sh script exits early if ``command -v direnv``
        fails (line 8).  In CI, direnv is not installed, so the script silently
        exits 0 and the tests that expect filesystem mutations fail.  This
        fixture creates a no-op ``direnv`` stub so the guard passes.
        """
        mock_bin = tmp_path / "mock-bin"
        mock_bin.mkdir(exist_ok=True)
        mock_direnv = mock_bin / "direnv"
        mock_direnv.write_text("#!/bin/sh\nexit 0\n")
        mock_direnv.chmod(0o755)

        git_path = shutil.which("git")
        assert git_path, "git must be available"
        git_dir = str(Path(git_path).parent)
        # Build PATH from mock-bin + git's directory only; avoid hardcoded paths
        path_dirs = [str(mock_bin), git_dir]
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_dirs = []
        for d in path_dirs:
            if d not in seen:
                seen.add(d)
                unique_dirs.append(d)
        env = {k: v for k, v in os.environ.items() if k != "PATH"}
        env["PATH"] = ":".join(unique_dirs)
        return env

    def test_script_exists(self, hooks_dir: Path):
        script = hooks_dir / "ensure-direnv-hook.sh"
        assert script.exists(), "ensure-direnv-hook.sh must exist"

    def test_script_is_executable(self, hooks_dir: Path):
        script = hooks_dir / "ensure-direnv-hook.sh"
        assert os.access(script, os.X_OK), "ensure-direnv-hook.sh must be executable"

    def test_fragment_exists(self, hooks_dir: Path):
        fragment = hooks_dir / "post-checkout-fragment.sh"
        assert fragment.exists(), "post-checkout-fragment.sh must exist"

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

    def test_exits_cleanly_when_no_envrc(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Hook must exit 0 when no .envrc in repo root."""
        # Init a git repo without .envrc
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
        result = subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

    def test_no_stdout_on_success(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Hook must be silent on success."""
        result = subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )
        assert result.stdout == ""

    def test_installs_post_checkout_hook(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Hook must install the post-checkout hook in a git repo with .envrc."""
        # Set up a git repo with .envrc
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
        (tmp_path / ".envrc").write_text("# test envrc\n")

        result = subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        hook_file = tmp_path / ".git" / "hooks" / "post-checkout"
        assert hook_file.exists(), "post-checkout hook must be created"
        assert os.access(hook_file, os.X_OK), "post-checkout hook must be executable"
        assert "direnv-worktree-hook-start" in hook_file.read_text()

    def test_writes_path_file(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Hook must write the path to direnv-post-checkout.sh in a path file."""
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
        (tmp_path / ".envrc").write_text("# test envrc\n")

        subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )

        path_file = tmp_path / ".git" / "hooks" / ".direnv-post-checkout-path"
        assert path_file.exists(), "Path file must be created"
        stored_path = path_file.read_text().strip()
        assert stored_path.endswith("direnv-post-checkout.sh")
        assert os.path.isfile(stored_path), "Stored path must point to an existing file"

    def test_idempotent_installation(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Running twice must not duplicate the hook block."""
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # Run twice
        for _ in range(2):
            subprocess.run(
                [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
                capture_output=True,
                text=True,
                env=env_with_mock_direnv,
                cwd=str(tmp_path),
            )

        hook_file = tmp_path / ".git" / "hooks" / "post-checkout"
        content = hook_file.read_text()
        assert content.count("direnv-worktree-hook-start") == 1, \
            "Hook block must appear exactly once"

    def test_preserves_existing_post_checkout(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Must append to existing post-checkout hooks, not replace."""
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # Create existing post-checkout hook
        hook_dir = tmp_path / ".git" / "hooks"
        hook_dir.mkdir(parents=True, exist_ok=True)
        hook_file = hook_dir / "post-checkout"
        hook_file.write_text("#!/bin/sh\necho 'existing hook'\n")
        hook_file.chmod(hook_file.stat().st_mode | stat.S_IEXEC)

        subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )

        content = hook_file.read_text()
        assert "existing hook" in content, "Existing hook content must be preserved"
        assert "direnv-worktree-hook-start" in content, "Direnv block must be appended"

    def test_error_when_post_checkout_script_missing(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Hook must exit 1 with stderr when direnv-post-checkout.sh is not found."""
        # Set up a git repo with .envrc
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
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
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )
        assert result.returncode == 1, "Must exit 1 when post-checkout script is missing"
        assert "direnv-post-checkout.sh not found" in result.stderr

    def test_updates_path_file_when_stale(
        self, hooks_dir: Path, tmp_path: Path, bash_path: str,
        env_with_mock_direnv: dict,
    ):
        """Hook must update the path file even when the hook block is already installed."""
        subprocess.run(
            ["git", "init"], cwd=str(tmp_path), capture_output=True,
            env=env_with_mock_direnv,
        )
        (tmp_path / ".envrc").write_text("# test envrc\n")

        # First install
        subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )

        path_file = tmp_path / ".git" / "hooks" / ".direnv-post-checkout-path"
        assert path_file.exists()

        # Corrupt the path file to simulate a stale reference
        path_file.write_text("/nonexistent/path/direnv-post-checkout.sh\n")

        # Run again — should update the path file
        result = subprocess.run(
            [bash_path, str(hooks_dir / "ensure-direnv-hook.sh")],
            capture_output=True,
            text=True,
            env=env_with_mock_direnv,
            cwd=str(tmp_path),
        )
        assert result.returncode == 0

        # Verify the path file was updated
        stored_path = path_file.read_text().strip()
        assert stored_path.endswith("direnv-post-checkout.sh")
        assert os.path.isfile(stored_path), "Path file must be updated with valid path"

        # Hook block should still appear exactly once
        hook_file = tmp_path / ".git" / "hooks" / "post-checkout"
        assert hook_file.read_text().count("direnv-worktree-hook-start") == 1

    def test_has_shebang(self, hooks_dir: Path):
        script = hooks_dir / "ensure-direnv-hook.sh"
        first_line = script.read_text().splitlines()[0]
        assert first_line.startswith("#!/"), "Script must have a shebang line"


class TestHooksJsonRegistration:
    """Tests that hooks.json registers the direnv SessionStart hook."""

    def test_hooks_json_has_direnv_session_start(self, hooks_dir: Path):
        hooks_json = json.loads((hooks_dir / "hooks.json").read_text())
        session_start_hooks = hooks_json["hooks"]["SessionStart"]
        commands = []
        for entry in session_start_hooks:
            for hook in entry["hooks"]:
                commands.append(hook["command"])
        assert any("ensure-direnv-hook" in cmd for cmd in commands), \
            "hooks.json must register ensure-direnv-hook.sh as a SessionStart hook"
