"""Tests for bd-pipeline status script."""

import json
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def script_path(plugin_root: Path) -> Path:
    return plugin_root / "scripts" / "bd-pipeline"


@pytest.fixture
def run_script(script_path: Path):
    """Helper to run bd-pipeline with mock bd output via stdin."""
    def _run(json_input: str, phase: str = "executing", next_phase: str = "finishing") -> str:
        result = subprocess.run(
            [str(script_path), "--phase", phase, "--next", next_phase],
            input=json_input,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip()
    return _run


class TestBdPipeline:
    """bd-pipeline script renders one-line status from beads JSON."""

    def test_script_exists_and_is_executable(self, script_path: Path):
        assert script_path.exists(), "scripts/bd-pipeline must exist"
        import os
        assert os.access(script_path, os.X_OK), "bd-pipeline must be executable"

    def test_single_active_task(self, run_script):
        tasks = json.dumps([
            {"id": "bd-1", "title": "auth- Implement auth module", "status": "in_progress"},
        ])
        result = run_script(tasks)
        assert result == "executing || auth --> finishing"

    def test_multiple_active_tasks(self, run_script):
        tasks = json.dumps([
            {"id": "bd-1", "title": "auth- Implement auth", "status": "in_progress"},
            {"id": "bd-2", "title": "routes- Add API routes", "status": "in_progress"},
        ])
        result = run_script(tasks)
        assert result == "executing || auth | routes --> finishing"

    def test_active_plus_ready_tasks(self, run_script):
        tasks = json.dumps([
            {"id": "bd-1", "title": "auth- Implement auth", "status": "in_progress"},
            {"id": "bd-2", "title": "routes- Add routes", "status": "open"},
            {"id": "bd-3", "title": "tests- Write tests", "status": "open"},
            {"id": "bd-4", "title": "docs- Update docs", "status": "open"},
        ])
        result = run_script(tasks)
        assert result == "executing || auth | (3 more) --> finishing"

    def test_no_active_tasks(self, run_script):
        tasks = json.dumps([
            {"id": "bd-1", "title": "auth- Implement auth", "status": "open"},
        ])
        result = run_script(tasks)
        assert result == "executing || (1 more) --> finishing"

    def test_all_closed(self, run_script):
        tasks = json.dumps([
            {"id": "bd-1", "title": "auth- Implement auth", "status": "closed"},
        ])
        result = run_script(tasks)
        assert result == "executing || (done) --> finishing"

    def test_custom_phases(self, run_script):
        tasks = json.dumps([
            {"id": "bd-1", "title": "design- Write design doc", "status": "in_progress"},
        ])
        result = run_script(tasks, phase="planning", next_phase="executing")
        assert result == "planning || design --> executing"

    def test_slug_extraction_uses_first_hyphen_space(self, run_script):
        """Slug is everything before first '- ' delimiter."""
        tasks = json.dumps([
            {"id": "bd-1", "title": "api- Add re-auth endpoint", "status": "in_progress"},
        ])
        result = run_script(tasks)
        assert result == "executing || api --> finishing"

    def test_empty_input(self, run_script):
        result = run_script("[]")
        assert result == "executing || (done) --> finishing"
