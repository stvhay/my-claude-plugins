"""Tests for context-check script."""

import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def script_path(plugin_root: Path) -> Path:
    return plugin_root / "scripts" / "context-check"


@pytest.fixture
def stats_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".claude"
    d.mkdir()
    return d


class TestContextCheck:
    """Tests the context-check shell script."""

    def test_script_exists_and_executable(self, script_path: Path):
        assert script_path.exists(), f"Script not found: {script_path}"
        assert script_path.stat().st_mode & 0o111, "Script must be executable"

    def test_reads_context_percent(self, script_path: Path, stats_dir: Path):
        """Outputs integer percentage when file exists with context_percent."""
        stats_file = stats_dir / ".statusline-stats"
        stats_file.write_text("context_percent=42\ncost_usd=1.23\n")
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
            cwd=stats_dir.parent,  # project root with .claude/ dir
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "42"

    def test_handles_zero_percent(self, script_path: Path, stats_dir: Path):
        stats_file = stats_dir / ".statusline-stats"
        stats_file.write_text("context_percent=0\ncost_usd=0.00\n")
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
            cwd=stats_dir.parent,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "0"

    def test_handles_hundred_percent(self, script_path: Path, stats_dir: Path):
        stats_file = stats_dir / ".statusline-stats"
        stats_file.write_text("context_percent=100\ncost_usd=5.00\n")
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
            cwd=stats_dir.parent,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "100"

    def test_error_when_file_missing(self, script_path: Path, tmp_path: Path):
        """Exit 1 with error to stderr when .statusline-stats doesn't exist."""
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
            cwd=tmp_path,  # no .claude/ dir here
        )
        assert result.returncode == 1
        assert result.stderr.strip()  # must have error message

    def test_error_when_no_context_percent_line(
        self, script_path: Path, stats_dir: Path
    ):
        """Exit 1 when file exists but has no context_percent line."""
        stats_file = stats_dir / ".statusline-stats"
        stats_file.write_text("cost_usd=1.23\n")
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
            cwd=stats_dir.parent,
        )
        assert result.returncode == 1
        assert result.stderr.strip()

    def test_robust_parsing_with_extra_equals(
        self, script_path: Path, stats_dir: Path
    ):
        """Handles values with = signs (defensive, even though ours are ints)."""
        stats_file = stats_dir / ".statusline-stats"
        stats_file.write_text("context_percent=55\nsome_key=foo=bar\n")
        result = subprocess.run(
            [str(script_path)],
            capture_output=True,
            text=True,
            env={"HOME": "/tmp", "PATH": "/usr/bin:/bin"},
            cwd=stats_dir.parent,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "55"
