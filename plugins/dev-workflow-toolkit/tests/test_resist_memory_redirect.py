"""Tests for resist-memory-redirect.sh SessionStart hook."""
import os
import hashlib
import subprocess
import tempfile
import textwrap

import pytest


HOOK_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "resist-memory-redirect.sh"
)


def _generate_stub(project_root: str) -> str:
    """Generate the expected stub content for a given project root."""
    return (
        f"# Memory\n"
        f"\n"
        f"All project memory is stored in {project_root}/MEMORY.md."
        f" Read that file instead.\n"
    )


def _sha1(content: str) -> str:
    return hashlib.sha1(content.encode()).hexdigest()


@pytest.fixture
def env(tmp_path):
    """Set up isolated test environment with fake project and claude dirs."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Initialize a git repo so git rev-parse works
    subprocess.run(["git", "init", str(project_root)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(project_root), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(project_root), capture_output=True, check=True,
    )

    # Encode path the way Claude Code does: replace / with -
    encoded = str(project_root).replace("/", "-")
    claude_memory_dir = tmp_path / "claude_home" / "projects" / encoded / "memory"
    claude_memory_dir.mkdir(parents=True)

    return {
        "project_root": project_root,
        "claude_home": tmp_path / "claude_home",
        "memory_file": claude_memory_dir / "MEMORY.md",
        "project_memory": project_root / "MEMORY.md",
    }


def _run_hook(env_dict) -> subprocess.CompletedProcess:
    """Run the hook script with the test environment."""
    return subprocess.run(
        ["bash", HOOK_SCRIPT],
        cwd=str(env_dict["project_root"]),
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "HOME": str(env_dict["claude_home"].parent),
            "CLAUDE_HOME": str(env_dict["claude_home"]),
        },
    )


class TestStubMatching:
    """When the file matches the stub SHA, hook exits silently."""

    def test_stub_unchanged_exits_silently(self, env):
        stub = _generate_stub(str(env["project_root"]))
        env["memory_file"].write_text(stub)

        result = _run_hook(env)

        assert result.returncode == 0
        assert result.stdout == ""
        assert env["memory_file"].read_text() == stub

    def test_no_claude_projects_dir_exits_silently(self, env):
        # Remove the memory directory entirely
        import shutil
        shutil.rmtree(str(env["memory_file"].parent), ignore_errors=True)

        result = _run_hook(env)

        assert result.returncode == 0
        assert result.stdout == ""


class TestContentRedirect:
    """When file differs from stub, content is appended and stub replanted."""

    def test_new_content_appended_to_project_memory(self, env):
        agent_content = "# Memory\n\n- User prefers dark mode\n- Project uses Python 3.13\n"
        env["memory_file"].write_text(agent_content)
        env["project_memory"].write_text("# Memory\n\n## Existing\n\n- Prior content\n")

        result = _run_hook(env)

        assert result.returncode == 0
        project_content = env["project_memory"].read_text()
        assert "Prior content" in project_content
        assert "User prefers dark mode" in project_content
        assert "Project uses Python 3.13" in project_content
        assert "Relocated from" in project_content

    def test_stub_replanted_after_redirect(self, env):
        env["memory_file"].write_text("# Memory\n\n- Some new fact\n")

        _run_hook(env)

        stub = _generate_stub(str(env["project_root"]))
        assert env["memory_file"].read_text() == stub

    def test_agent_message_printed(self, env):
        env["memory_file"].write_text("# Memory\n\n- Some new fact\n")

        result = _run_hook(env)

        assert "memory-redirect:" in result.stdout
        assert "MEMORY.md" in result.stdout

    def test_project_memory_created_if_missing(self, env):
        env["memory_file"].write_text("# Memory\n\n- Brand new fact\n")
        # project_memory does not exist

        result = _run_hook(env)

        assert result.returncode == 0
        assert env["project_memory"].exists()
        content = env["project_memory"].read_text()
        assert content.startswith("# Memory\n")
        assert "Brand new fact" in content

    def test_idempotent_after_redirect(self, env):
        env["memory_file"].write_text("# Memory\n\n- Fact\n")
        _run_hook(env)

        # Run again — stub should match, silent exit
        result = _run_hook(env)

        assert result.returncode == 0
        assert result.stdout == ""
