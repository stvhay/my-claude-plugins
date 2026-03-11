"""Integration tests for langfuse-trace.sh wrapper.

Tests the bash wrapper's health check, backgrounding, and bootstrap logic.
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

HOOK_SH = str(Path(__file__).parent / "langfuse-trace.sh")
CACHE_DIR = Path.home() / ".cache" / "langfuse-hook"


@pytest.fixture(autouse=True)
def clean_sentinel():
    """Remove sentinel and errors before each test."""
    (CACHE_DIR / "error-flag").unlink(missing_ok=True)
    errors_dir = CACHE_DIR / "errors"
    if errors_dir.exists():
        for f in errors_dir.iterdir():
            f.unlink()
    errors_log = CACHE_DIR / "errors.log"
    errors_log.unlink(missing_ok=True)
    yield
    (CACHE_DIR / "error-flag").unlink(missing_ok=True)
    if errors_dir.exists():
        for f in errors_dir.iterdir():
            f.unlink()
    errors_log.unlink(missing_ok=True)


def run_hook(event_json, env_overrides=None, timeout=5):
    """Run the shell wrapper with a clean env and capture stdout/stderr/exit code."""
    env = {
        "HOME": os.environ["HOME"],
        "PATH": os.environ["PATH"],
        "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
    }
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", HOOK_SH],
        input=event_json,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


class TestHealthCheck:
    """SessionStart health check runs synchronously in bash."""

    def test_missing_env_vars_warns(self):
        result = run_hook(
            '{"hook_event_name":"SessionStart","session_id":"t1"}',

        )
        assert result.returncode == 0
        assert "missing env vars" in result.stdout

    def test_healthy_is_silent(self):
        result = run_hook(
            '{"hook_event_name":"SessionStart","session_id":"t1"}',
            env_overrides={
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost",
            },

        )
        assert result.returncode == 0
        assert result.stdout == ""

    def test_sentinel_reports_errors(self, tmp_path):
        """When error-flag exists, SessionStart reports errors to stdout."""
        cache_dir = tmp_path / ".cache" / "langfuse-hook"
        cache_dir.mkdir(parents=True)
        venv_bin = cache_dir / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        real_python = subprocess.check_output(
            ["which", "python3"], text=True
        ).strip()
        (venv_bin / "python3").symlink_to(real_python)

        errors_dir = cache_dir / "errors"
        errors_dir.mkdir()
        (errors_dir / "20260311_PostToolUse_test.log").write_text(
            "PostToolUse: connection timeout\n"
        )
        (cache_dir / "error-flag").touch()

        result = run_hook(
            '{"hook_event_name":"SessionStart","session_id":"t1"}',
            env_overrides={
                "HOME": str(tmp_path),
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost",
                "LANGFUSE_HOOK_VENV": str(cache_dir / "venv"),
            },

        )
        assert result.returncode == 0
        assert "1 error(s)" in result.stdout
        assert "connection timeout" in result.stdout


class TestBackgrounding:
    """All Langfuse SDK work runs in the background."""

    def test_post_tool_use_returns_instantly(self):
        """PostToolUse should return in <500ms (backgrounded)."""
        start = time.monotonic()
        result = run_hook(
            '{"hook_event_name":"PostToolUse","session_id":"t1",'
            '"tool_name":"Bash","transcript_path":"/dev/null"}',
            env_overrides={
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost",
            },

        )
        elapsed = time.monotonic() - start
        assert result.returncode == 0
        assert elapsed < 0.5, f"Hook took {elapsed:.2f}s — should be <0.5s"

    def test_session_start_returns_instantly(self):
        """SessionStart should return fast (health check is bash, SDK is backgrounded)."""
        start = time.monotonic()
        result = run_hook(
            '{"hook_event_name":"SessionStart","session_id":"t1",'
            '"model":"claude-opus-4-6","source":"startup"}',
            env_overrides={
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost",
            },

        )
        elapsed = time.monotonic() - start
        assert result.returncode == 0
        assert elapsed < 0.5, f"Hook took {elapsed:.2f}s — should be <0.5s"

    def test_non_session_start_no_stdout(self):
        """PostToolUse should produce no stdout (no health check)."""
        result = run_hook(
            '{"hook_event_name":"PostToolUse","session_id":"t1",'
            '"tool_name":"Bash","transcript_path":"/dev/null"}',
            env_overrides={
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost",
            },

        )
        assert result.stdout == ""


class TestSentinelOnSdkError:
    """SDK connection failures touch the sentinel via stderr detection."""

    @pytest.fixture
    def transcript_with_data(self, tmp_path):
        """Create a transcript with a unique request ID to avoid state caching."""
        req_id = f"req-sentinel-{time.monotonic_ns()}"
        path = tmp_path / "transcript.jsonl"
        path.write_text(
            f'{{"type":"assistant","requestId":"{req_id}","message":'
            '{"model":"claude-opus-4-6","usage":{"input_tokens":100,"output_tokens":50},'
            '"content":[{"type":"text","text":"hello"}]}}\n'
        )
        return str(path)

    def test_bad_host_creates_sentinel(self, transcript_with_data):
        """When Langfuse host is unreachable, backgrounded process touches sentinel."""
        # Use unique session to avoid cached state
        session_id = f"sentinel-test-{time.monotonic_ns()}"
        run_hook(
            '{"hook_event_name":"PostToolUse","session_id":"' + session_id + '",'
            f'"tool_name":"Bash","transcript_path":"{transcript_with_data}"' + '}',
            env_overrides={
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost:19999",
            },

        )
        # Background process needs time: SDK retries twice (~3-5s)
        for _ in range(15):
            if (CACHE_DIR / "error-flag").exists():
                break
            time.sleep(1)
        assert (CACHE_DIR / "error-flag").exists(), (
            "Sentinel should be created when SDK cannot connect"
        )
        # errors.log should have the SDK error
        errors_log = CACHE_DIR / "errors.log"
        assert errors_log.exists()
        content = errors_log.read_text()
        assert "Failed to export" in content or "Connection refused" in content


class TestBootstrap:
    """Venv bootstrap behavior."""

    def test_missing_venv_exits_zero(self, tmp_path):
        """When venv doesn't exist, wrapper exits 0 (background bootstrap)."""
        result = run_hook(
            '{"hook_event_name":"SessionStart","session_id":"t1"}',
            env_overrides={
                "LANGFUSE_HOOK_VENV": str(tmp_path / "nonexistent-venv"),
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
                "LANGFUSE_HOST": "http://localhost",
            },

        )
        assert result.returncode == 0
