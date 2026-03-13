"""Tests for migrate-quality-gate.sh hook."""

import json
import os
import subprocess
import tempfile

import pytest

HOOK_SCRIPT = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "migrate-quality-gate.sh"
)


def run_migration(project_dir: str) -> subprocess.CompletedProcess:
    """Run the migration script against a project directory."""
    return subprocess.run(
        ["bash", HOOK_SCRIPT],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def project_dir():
    """Create a temporary project directory with .claude/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, ".claude"), exist_ok=True)
        yield tmpdir


def write_settings(project_dir: str, settings: dict) -> str:
    """Write settings.json and return its path."""
    path = os.path.join(project_dir, ".claude", "settings.json")
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    return path


def read_settings(project_dir: str) -> dict:
    """Read settings.json from project directory."""
    path = os.path.join(project_dir, ".claude", "settings.json")
    with open(path) as f:
        return json.load(f)


class TestMigrateQualityGate:
    """Tests for the migration script."""

    def test_removes_stale_quality_gate_entry(self, project_dir):
        """Migration removes version-pinned quality-gate.sh hook entries."""
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "/home/dev/.claude/plugins/cache/my-claude-plugins/dev-workflow-toolkit/1.11.0/scripts/quality-gate.sh --path .",
                            }
                        ]
                    }
                ]
            }
        }
        write_settings(project_dir, settings)
        result = run_migration(project_dir)
        assert result.returncode == 0
        updated = read_settings(project_dir)
        assert "SessionStart" not in updated.get("hooks", {})

    def test_preserves_other_hooks(self, project_dir):
        """Migration preserves non-quality-gate hooks in SessionStart."""
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "/home/dev/.claude/plugins/cache/my-claude-plugins/dev-workflow-toolkit/1.11.0/scripts/quality-gate.sh --path .",
                            }
                        ]
                    },
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo hello",
                            }
                        ]
                    },
                ]
            }
        }
        write_settings(project_dir, settings)
        result = run_migration(project_dir)
        assert result.returncode == 0
        updated = read_settings(project_dir)
        session_start = updated["hooks"]["SessionStart"]
        assert len(session_start) == 1
        assert session_start[0]["hooks"][0]["command"] == "echo hello"

    def test_noop_no_settings_file(self):
        """Migration is a no-op when .claude/settings.json doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_migration(tmpdir)
            assert result.returncode == 0
            assert not os.path.exists(
                os.path.join(tmpdir, ".claude", "settings.json")
            )

    def test_noop_no_quality_gate_entry(self, project_dir):
        """Migration is a no-op when no quality-gate entry exists."""
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {"type": "command", "command": "echo hello"}
                        ]
                    }
                ]
            }
        }
        write_settings(project_dir, settings)
        result = run_migration(project_dir)
        assert result.returncode == 0
        updated = read_settings(project_dir)
        assert len(updated["hooks"]["SessionStart"]) == 1

    def test_cleans_empty_hooks_object(self, project_dir):
        """Migration removes empty hooks object after cleanup."""
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "/home/dev/.claude/plugins/cache/my-claude-plugins/dev-workflow-toolkit/1.11.0/scripts/quality-gate.sh --path .",
                            }
                        ]
                    }
                ]
            },
            "someOtherSetting": True,
        }
        write_settings(project_dir, settings)
        result = run_migration(project_dir)
        assert result.returncode == 0
        updated = read_settings(project_dir)
        assert "hooks" not in updated
        assert updated["someOtherSetting"] is True

    def test_handles_multiple_version_paths(self, project_dir):
        """Migration removes quality-gate entries regardless of version number."""
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "hooks": [
                            {
                                "type": "command",
                                "command": "/home/user/.claude/plugins/cache/my-claude-plugins/dev-workflow-toolkit/2.0.0/scripts/quality-gate.sh --path .",
                            }
                        ]
                    }
                ]
            }
        }
        write_settings(project_dir, settings)
        result = run_migration(project_dir)
        assert result.returncode == 0
        updated = read_settings(project_dir)
        assert "SessionStart" not in updated.get("hooks", {})
