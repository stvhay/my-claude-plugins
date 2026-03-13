"""Tests for capability-based test guards."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def plugin_dir() -> Path:
    return Path(__file__).parent.parent


def run_pytest_with_capabilities(plugin_dir: Path, capabilities: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run pytest in a subprocess with CI_CAPABILITIES set."""
    env = os.environ.copy()
    env["CI_CAPABILITIES"] = capabilities
    args = [
        "uv", "run", "--project", str(plugin_dir),
        "pytest", str(plugin_dir / "tests" / "test_capability_guard.py"),
        "-v", "--no-header", "-rN",
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True, env=env, cwd=plugin_dir)


class TestCapabilityMarkerRegistered:
    """Verify the capability marker is registered and doesn't produce warnings."""

    def test_no_unknown_marker_warning(self, plugin_dir: Path) -> None:
        """Running with capability marker should not produce PytestUnknownMarkWarning."""
        result = run_pytest_with_capabilities(plugin_dir, "", ["-k", "test_marked_gpu", "-W", "error::pytest.PytestUnknownMarkWarning"])
        assert "PytestUnknownMarkWarning" not in result.stdout + result.stderr


class TestCapabilitySkipping:
    """Tests that verify capability-based skipping behavior."""

    @pytest.mark.capability("gpu")
    def test_marked_gpu(self) -> None:
        """This test requires GPU capability. Used by other tests to verify skipping."""
        pass

    @pytest.mark.capability("ollama")
    def test_marked_ollama(self) -> None:
        """This test requires ollama capability. Used by other tests to verify skipping."""
        pass

    def test_unmarked(self) -> None:
        """This test has no capability requirement and should always run."""
        pass

    def test_skips_when_capability_missing(self, plugin_dir: Path) -> None:
        """Tests with capability markers should be skipped when CI_CAPABILITIES lacks that capability."""
        result = run_pytest_with_capabilities(plugin_dir, "", ["-k", "test_marked_gpu", "-v"])
        assert "SKIPPED" in result.stdout or "skipped" in result.stdout.lower()

    def test_runs_when_capability_present(self, plugin_dir: Path) -> None:
        """Tests with capability markers should run when CI_CAPABILITIES includes that capability."""
        result = run_pytest_with_capabilities(plugin_dir, "gpu", ["-k", "test_marked_gpu", "-v"])
        assert "PASSED" in result.stdout

    def test_skip_reason_includes_capability_name(self, plugin_dir: Path) -> None:
        """Skip reason should mention the missing capability."""
        result = run_pytest_with_capabilities(plugin_dir, "", ["-k", "test_marked_gpu", "-v", "-rs"])
        assert "gpu" in result.stdout.lower()

    def test_unmarked_tests_always_run(self, plugin_dir: Path) -> None:
        """Tests without capability markers should run regardless of CI_CAPABILITIES."""
        result = run_pytest_with_capabilities(plugin_dir, "", ["-k", "test_unmarked", "-v"])
        assert "PASSED" in result.stdout

    def test_multiple_capabilities_space_separated(self, plugin_dir: Path) -> None:
        """CI_CAPABILITIES should be space-separated, matching any listed capability."""
        result = run_pytest_with_capabilities(plugin_dir, "gpu ollama", ["-k", "test_marked_gpu or test_marked_ollama", "-v"])
        assert result.stdout.count("PASSED") >= 2

    def test_empty_capabilities_skips_all_marked(self, plugin_dir: Path) -> None:
        """Empty CI_CAPABILITIES should skip all capability-marked tests."""
        result = run_pytest_with_capabilities(plugin_dir, "", ["-k", "test_marked_gpu or test_marked_ollama", "-v"])
        assert "PASSED" not in result.stdout
