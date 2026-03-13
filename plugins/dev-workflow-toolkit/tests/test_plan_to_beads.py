"""Tests for plan_to_beads.py markdown parser."""

import tempfile
from pathlib import Path

from scripts.plan_to_beads import parse_tasks


class TestParseTasks:
    """Test task extraction from plan markdown."""

    def _write_plan(self, content: str) -> str:
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False)
        f.write(content)
        f.close()
        return f.name

    def test_basic_tasks(self):
        path = self._write_plan(
            "# Plan\n\n"
            "### Task 1: Setup\n\n"
            "Some content.\n\n"
            "**Depends on:** Independent\n\n"
            "### Task 2: Build\n\n"
            "More content.\n\n"
            "**Depends on:** Task 1\n\n"
        )
        tasks = parse_tasks(path)
        assert len(tasks) == 2
        assert tasks[0]["number"] == 1
        assert tasks[0]["title"] == "Setup"
        assert tasks[0]["deps"] == []
        assert tasks[1]["number"] == 2
        assert tasks[1]["title"] == "Build"
        assert tasks[1]["deps"] == [1]

    def test_multiple_deps(self):
        path = self._write_plan(
            "### Task 1: A\n\n**Depends on:** Independent\n\n"
            "### Task 2: B\n\n**Depends on:** Independent\n\n"
            "### Task 3: C\n\n**Depends on:** Task 1, Task 2\n\n"
        )
        tasks = parse_tasks(path)
        assert tasks[2]["deps"] == [1, 2]

    def test_skips_h3_inside_code_fence(self):
        path = self._write_plan(
            "### Task 1: Real task\n\n"
            "**Depends on:** Independent\n\n"
            "```markdown\n"
            "### Task 99: Fake task inside code fence\n"
            "```\n\n"
            "### Task 2: Another real task\n\n"
            "**Depends on:** Task 1\n\n"
        )
        tasks = parse_tasks(path)
        assert len(tasks) == 2
        assert tasks[0]["title"] == "Real task"
        assert tasks[1]["title"] == "Another real task"

    def test_skips_h2_inside_code_fence(self):
        """Ensure h2 headings in code fences don't interfere."""
        path = self._write_plan(
            "### Task 1: Real\n\n"
            "**Depends on:** Independent\n\n"
            "```markdown\n"
            "## Installation\n\n"
            "## Architecture\n\n"
            "## License\n"
            "```\n\n"
            "### Task 2: Also real\n\n"
            "**Depends on:** Task 1\n\n"
        )
        tasks = parse_tasks(path)
        assert len(tasks) == 2

    def test_skips_h3_inside_quadruple_backtick_fence(self):
        """Plans use ```` fences to embed markdown with ``` fences."""
        path = self._write_plan(
            "### Task 1: Real\n\n"
            "**Depends on:** Independent\n\n"
            "````markdown\n"
            "### Task 99: Fake\n\n"
            "```python\n"
            "x = 1\n"
            "```\n"
            "````\n\n"
            "### Task 2: Also real\n\n"
            "**Depends on:** Task 1\n\n"
        )
        tasks = parse_tasks(path)
        assert len(tasks) == 2
        assert tasks[0]["title"] == "Real"
        assert tasks[1]["title"] == "Also real"

    def test_no_tasks(self):
        path = self._write_plan("# Plan\n\nJust text, no tasks.\n")
        tasks = parse_tasks(path)
        assert tasks == []

    def test_non_task_h3_ignored(self):
        path = self._write_plan(
            "### Overview\n\nNot a task.\n\n"
            "### Task 1: Real\n\n**Depends on:** Independent\n\n"
        )
        tasks = parse_tasks(path)
        assert len(tasks) == 1
        assert tasks[0]["title"] == "Real"

    def test_real_plan_file(self):
        """Smoke test against an actual plan file if available."""
        plan = Path(__file__).parents[2] / "docs/plans/2026-03-13-quality-gate-path-fix-plan.md"
        if not plan.exists():
            return
        tasks = parse_tasks(str(plan))
        assert len(tasks) == 3
        assert tasks[0]["title"] == "Add quality gate to hooks.json and remove from project-init"
        assert tasks[1]["deps"] == [1]
        assert tasks[2]["deps"] == [2]

    def test_plan_with_many_fenced_h2s(self):
        """Smoke test against plan with 40+ embedded h2 headings in code fences."""
        plan = (
            Path(__file__).parents[2]
            / "docs/plans/2026-03-10-documentation-standards-plan.md"
        )
        if not plan.exists():
            return
        tasks = parse_tasks(str(plan))
        assert len(tasks) == 5
        # Should NOT pick up ## What Is an ADR?, ## Templates, etc.
        titles = [t["title"] for t in tasks]
        assert "What Is an ADR?" not in titles
        assert "Templates" not in titles
