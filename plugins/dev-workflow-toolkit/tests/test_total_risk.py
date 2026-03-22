"""Tests for the total-risk budget tracking tool."""

import json
import subprocess
from pathlib import Path

import pytest

SCRIPT = (Path(__file__).resolve().parent.parent / "scripts" / "total-risk")


def run_risk(*args, cwd=None):
    """Run total-risk and return parsed JSON."""
    result = subprocess.run(
        ["python3", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return json.loads(result.stdout), result.returncode


@pytest.fixture()
def session(tmp_path):
    """Provide a temp dir with .claude/ for isolated state."""
    (tmp_path / ".claude").mkdir()
    return tmp_path


class TestReset:
    def test_reset_creates_session(self, session):
        out, rc = run_risk("reset", "25", cwd=session)
        assert rc == 0
        assert out["budget"] == 25.0
        assert out["total"] == 0
        assert out["status"] == "ok"

    def test_reset_clears_prior_state(self, session):
        run_risk("reset", "25", cwd=session)
        run_risk("docs", cwd=session)
        out, _ = run_risk("reset", "10", cwd=session)
        assert out["budget"] == 10.0
        assert out["total"] == 0


class TestBaseCosts:
    @pytest.mark.parametrize(
        "category,expected_base",
        [
            ("docs", 1),
            ("style", 1),
            ("tests", 2),
            ("new-feature", 3),
            ("mechanical-refactor", 3),
            ("ci-infra", 4),
            ("structural-refactor", 5),
            ("modify-feature", 5),
            ("bug-fix", 7),
            ("performance", 7),
            ("security", 8),
        ],
    )
    def test_base_cost(self, session, category, expected_base):
        run_risk("reset", "100", cwd=session)
        out, rc = run_risk(category, cwd=session)
        assert rc == 0
        assert out["task"]["base"] == expected_base
        assert out["task"]["category"] == category


class TestModifiers:
    def test_four_plus_files(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("new-feature", "4-plus-files", cwd=session)
        # base 3 × 1.5 = 4.5
        assert out["task"]["adjusted_cost"] == 4.5

    def test_same_module_explicit(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("new-feature", "same-module", cwd=session)
        # base 3 × 1.3 = 3.9
        assert out["task"]["adjusted_cost"] == 3.9

    def test_same_module_auto_detect(self, session):
        run_risk("reset", "100", cwd=session)
        run_risk("docs", "module:src/auth", cwd=session)
        out, _ = run_risk("docs", "module:src/auth", cwd=session)
        assert "same-module" in " ".join(out["task"]["modifiers"])

    def test_ci_pass_discount(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("docs", "ci-pass", cwd=session)
        # base 1 - 1 = floor 1
        assert out["task"]["adjusted_cost"] == 1  # cost floor

    def test_ci_fail_penalty(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("docs", "ci-fail", cwd=session)
        # base 1 + 3 = 4
        assert out["task"]["adjusted_cost"] == 4

    def test_review_clean_discount(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("new-feature", "review-clean", cwd=session)
        # base 3 - 1 = 2
        assert out["task"]["adjusted_cost"] == 2

    def test_cost_floor(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("docs", "ci-pass", "review-clean", cwd=session)
        # base 1 - 1 - 1 = -1 → floor 1
        assert out["task"]["adjusted_cost"] == 1


class TestContextDegradation:
    def test_increases_with_task_count(self, session):
        run_risk("reset", "100", cwd=session)
        run_risk("docs", cwd=session)  # task 1: no degradation
        run_risk("docs", cwd=session)  # task 2: ×1.05
        out, _ = run_risk("docs", cwd=session)  # task 3: ×1.1025
        assert out["task"]["adjusted_cost"] > 1.0
        assert "context(n=2)" in " ".join(out["task"]["modifiers"])

    def test_compounds_over_many_tasks(self, session):
        run_risk("reset", "200", cwd=session)
        costs = []
        for _ in range(10):
            out, _ = run_risk("docs", cwd=session)
            costs.append(out["task"]["adjusted_cost"])
        # Cost should be strictly non-decreasing
        for i in range(1, len(costs)):
            assert costs[i] >= costs[i - 1]


class TestBudgetEnforcement:
    def test_checkpoint_when_exceeded(self, session):
        run_risk("reset", "5", cwd=session)
        out, _ = run_risk("security", cwd=session)  # cost 8 > budget 5
        assert out["status"] == "checkpoint"

    def test_blocked_after_checkpoint(self, session):
        run_risk("reset", "5", cwd=session)
        run_risk("security", cwd=session)  # exceeds budget
        out, rc = run_risk("docs", cwd=session)  # should be blocked
        assert out["action"] == "blocked"
        assert out["status"] == "checkpoint"

    def test_warning_near_budget(self, session):
        run_risk("reset", "10", cwd=session)
        run_risk("security", cwd=session)  # cost 8, remaining 2 < 25% of 10
        out, _ = run_risk("status", cwd=session)
        assert out["status"] == "warning"


class TestStatus:
    def test_no_session(self, session):
        out, rc = run_risk("status", cwd=session)
        assert rc == 1
        assert "error" in out

    def test_shows_task_history(self, session):
        run_risk("reset", "50", cwd=session)
        run_risk("docs", cwd=session)
        run_risk("bug-fix", cwd=session)
        out, _ = run_risk("status", cwd=session)
        assert out["task_count"] == 2
        assert len(out["tasks"]) == 2


class TestCheck:
    def test_preview_without_logging(self, session):
        run_risk("reset", "25", cwd=session)
        out, rc = run_risk("check", "bug-fix", cwd=session)
        assert rc == 0
        assert out["action"] == "check"
        assert out["adjusted_cost"] == 7
        # Verify nothing was logged
        status_out, _ = run_risk("status", cwd=session)
        assert status_out["task_count"] == 0
        assert status_out["total"] == 0

    def test_skip_advice_when_over_budget(self, session):
        run_risk("reset", "5", cwd=session)
        out, _ = run_risk("check", "security", cwd=session)
        assert out["advice"] == "skip"
        assert out["adjusted_cost"] == 8

    def test_skip_advice_when_budget_exhausted(self, session):
        run_risk("reset", "5", cwd=session)
        run_risk("ci-infra", cwd=session)  # cost 4, remaining 1
        run_risk("docs", cwd=session)  # cost 1, remaining 0
        out, _ = run_risk("check", "docs", cwd=session)
        assert out["advice"] == "skip"

    def test_caution_advice_near_budget(self, session):
        run_risk("reset", "10", cwd=session)
        run_risk("bug-fix", cwd=session)  # cost 7, remaining 3
        out, _ = run_risk("check", "tests", cwd=session)
        # cost ~2.1 (with context), remaining_after ~0.9 < 15% of 10
        assert out["advice"] == "caution"

    def test_ok_advice_within_budget(self, session):
        run_risk("reset", "100", cwd=session)
        out, _ = run_risk("check", "docs", cwd=session)
        assert out["advice"] == "ok"


class TestErrors:
    def test_unknown_category(self, session):
        run_risk("reset", "25", cwd=session)
        out, rc = run_risk("banana", cwd=session)
        assert rc == 1
        assert "error" in out

    def test_reset_non_numeric(self, session):
        out, rc = run_risk("reset", "abc", cwd=session)
        assert rc == 1
        assert "error" in out
