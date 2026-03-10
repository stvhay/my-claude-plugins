"""
Quality gate tests — positive (smoke against real repo) and negative (fixtures).

Replaces test-quality-gate.sh.
"""

import subprocess
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qg(plugin_root: Path) -> str:
    """Path to the quality-gate.sh script."""
    path = plugin_root / "scripts" / "quality-gate.sh"
    assert path.exists() and path.stat().st_mode & 0o111, (
        "quality-gate.sh missing or not executable"
    )
    return str(path)


def run_qg(qg: str, *args: str) -> subprocess.CompletedProcess:
    """Run the quality gate and return the result (doesn't check exit code)."""
    return subprocess.run(
        [qg, *args],
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def fixture_dir(tmp_path: Path, repo_root: Path) -> Path:
    """Create a minimal valid fixture project for negative testing."""
    d = tmp_path / "project"
    skills = d / "plugins" / "test-plugin" / "skills" / "test-skill"
    skills.mkdir(parents=True)
    (d / "docs").mkdir()

    # Initialize git repo (quality-gate uses git rev-parse)
    subprocess.run(["git", "init", "-q", str(d)], check=True)

    # Minimal valid structure
    (d / "README.md").write_text("# Test\n")
    (d / "docs" / "ARCHITECTURE.md").write_text("# Arch\n")
    (d / "docs" / "DESIGN.md").write_text("# Design\n")

    # Valid SPEC.md
    (d / "plugins" / "test-plugin" / "skills" / "SPEC.md").write_text(
        "# Test Plugin Spec\n\n"
        "## Invariants\n\n"
        "| ID | Invariant | Type |\n"
        "|----|-----------|------|\n"
        "| INV-1 | First invariant | structural |\n"
        "| INV-2 | Second invariant | structural |\n\n"
        "## Failure Modes\n\n"
        "| ID | Mode |\n"
        "|----|------|\n"
        "| FAIL-1 | First failure |\n"
        "| FAIL-2 | Second failure |\n\n"
        "## Testing\n\n"
        "INV-1 and INV-2 are tested by the test suite.\n"
        "FAIL-1 is tested via integration tests.\n"
    )

    # Valid SKILL.md
    (skills / "SKILL.md").write_text(
        '---\nname: test-skill\ndescription: "A test skill"\n---\n\n# Test Skill\n\nDoes things.\n'
    )

    return d


# ---------------------------------------------------------------------------
# Smoke tests (against real repo)
# ---------------------------------------------------------------------------


class TestSmokeChecks:
    """Run individual checks against the real repo to verify they pass."""

    def test_script_executable(self, qg: str):
        """quality-gate.sh exists and is executable (verified by fixture)."""

    @pytest.mark.parametrize(
        "check",
        [
            "inv-numbering",
            "skill-structure",
            "doc-structure",
            "vsa-coverage",
            "cross-links",
            "tool-health",
        ],
    )
    def test_individual_check_passes(self, qg: str, repo_root: Path, check: str):
        result = run_qg(qg, "--check", check, "--path", str(repo_root))
        assert result.returncode == 0, f"{check} failed:\n{result.stdout}\n{result.stderr}"

    def test_issue_tracking(self, qg: str, repo_root: Path):
        result = run_qg(qg, "--check", "issue-tracking", "--path", str(repo_root))
        # On main branch, warnings are OK but hard failures are not
        if result.returncode != 0:
            assert "✗" not in result.stdout, (
                f"issue-tracking has unexpected failures:\n{result.stdout}"
            )

    def test_all_checks_together(self, qg: str, repo_root: Path):
        result = run_qg(qg, "--path", str(repo_root))
        assert result.returncode == 0, f"All checks failed:\n{result.stdout}\n{result.stderr}"

    def test_output_contains_check_names(self, qg: str, repo_root: Path):
        result = run_qg(qg, "--path", str(repo_root))
        for name in ("inv-numbering", "skill-structure", "doc-structure"):
            assert name in result.stdout, f"Output missing check name: {name}"

    def test_help_flag(self, qg: str):
        result = run_qg(qg, "--help")
        assert "quality-gate" in result.stdout


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgValidation:
    def test_check_without_value(self, qg: str):
        result = run_qg(qg, "--check")
        assert result.returncode != 0

    def test_unknown_option(self, qg: str):
        result = run_qg(qg, "--bogus")
        assert result.returncode != 0

    def test_unknown_check_name(self, qg: str):
        result = run_qg(qg, "--check", "nonexistent")
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# Fixture: valid project passes
# ---------------------------------------------------------------------------


class TestValidFixture:
    def test_valid_fixture_passes(self, qg: str, fixture_dir: Path):
        result = run_qg(qg, "--path", str(fixture_dir))
        assert result.returncode == 0, f"Valid fixture should pass:\n{result.stdout}"


# ---------------------------------------------------------------------------
# inv-numbering: duplicate INV numbers
# ---------------------------------------------------------------------------


class TestInvNumberingDuplicates:
    def test_duplicate_inv_detected(self, qg: str, fixture_dir: Path):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n## Invariants\n\n"
            "| ID | Invariant |\n|----|-----------|\n"
            "| INV-1 | First invariant |\n"
            "| INV-1 | Duplicate of first invariant |\n"
            "| INV-2 | Second invariant |\n\n"
            "## Failure Modes\n\n"
            "| ID | Mode |\n|----|------|\n"
            "| FAIL-1 | First failure |\n"
        )
        result = run_qg(qg, "--check", "inv-numbering", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "duplicate" in result.stdout.lower()


class TestInvNumberingGap:
    def test_gap_detected(self, qg: str, fixture_dir: Path):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n## Invariants\n\n"
            "| ID | Invariant |\n|----|-----------|\n"
            "| INV-1 | First |\n"
            "| INV-3 | Third (skipped 2) |\n\n"
            "## Failure Modes\n\n"
            "| ID | Mode |\n|----|------|\n"
            "| FAIL-1 | First failure |\n"
        )
        result = run_qg(qg, "--check", "inv-numbering", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "expected INV-2" in result.stdout


class TestFailNumberingDuplicates:
    def test_duplicate_fail_detected(self, qg: str, fixture_dir: Path):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n## Invariants\n\n"
            "| ID | Invariant |\n|----|-----------|\n"
            "| INV-1 | First |\n\n"
            "## Failure Modes\n\n"
            "| ID | Mode |\n|----|------|\n"
            "| FAIL-1 | First |\n"
            "| FAIL-1 | Duplicate first |\n"
            "| FAIL-2 | Second |\n"
        )
        result = run_qg(qg, "--check", "inv-numbering", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "duplicate" in result.stdout.lower()


# ---------------------------------------------------------------------------
# inv-numbering: list formats (bold, plain, italic)
# ---------------------------------------------------------------------------


class TestListFormats:
    @pytest.mark.parametrize(
        "fmt,content",
        [
            (
                "bold",
                "- **INV-1:** First invariant\n- **INV-2:** Second invariant\n\n"
                "## Failure Modes\n\n- **FAIL-1:** First failure\n",
            ),
            (
                "plain",
                "- INV-1: First invariant\n- INV-2: Second invariant\n\n"
                "## Failure Modes\n\n- FAIL-1: First failure\n",
            ),
            (
                "italic",
                "- *INV-1:* First invariant\n- *INV-2:* Second invariant\n\n"
                "## Failure Modes\n\n- *FAIL-1:* First failure\n",
            ),
        ],
        ids=["bold", "plain", "italic"],
    )
    def test_list_format_accepted(self, qg: str, fixture_dir: Path, fmt: str, content: str):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(f"# Spec\n\n## Invariants\n\n{content}")
        result = run_qg(qg, "--check", "inv-numbering", "--path", str(fixture_dir))
        assert result.returncode == 0, f"{fmt} format rejected:\n{result.stdout}"
        assert "INV-1 through INV-2" in result.stdout, f"{fmt} IDs not extracted:\n{result.stdout}"


# ---------------------------------------------------------------------------
# inv-numbering: cross-references don't cause false positives
# ---------------------------------------------------------------------------


class TestCrossReferences:
    def test_no_false_positives(self, qg: str, fixture_dir: Path):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n## Invariants\n\n"
            "| ID | Invariant |\n|----|-----------|\n"
            "| INV-1 | First |\n| INV-2 | Second |\n\n"
            "## Failure Modes\n\n"
            "| ID | Mode |\n|----|------|\n"
            "| FAIL-1 | First |\n\n"
            "## Decision Framework\n\n"
            "| Scenario | Action | Relates to |\n"
            "|----------|--------|------------|\n"
            "| Adding a skill | Check frontmatter | INV-1 |\n"
            "| Naming a skill | Use lowercase | INV-2 |\n\n"
            "## Testing\n\n"
            "INV-1 is tested here. INV-2 is also referenced. INV-1 again.\n"
            "FAIL-1 is covered by tests. See also INV-1 and INV-2.\n"
        )
        result = run_qg(qg, "--check", "inv-numbering", "--path", str(fixture_dir))
        assert result.returncode == 0, f"Cross-references caused false positives:\n{result.stdout}"


# ---------------------------------------------------------------------------
# skill-structure: negative cases
# ---------------------------------------------------------------------------


class TestSkillStructureNegative:
    def test_missing_frontmatter(self, qg: str, fixture_dir: Path):
        skill = fixture_dir / "plugins" / "test-plugin" / "skills" / "test-skill" / "SKILL.md"
        skill.write_text("# Test Skill\n\nNo frontmatter here.\n")
        result = run_qg(qg, "--check", "skill-structure", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "missing YAML frontmatter" in result.stdout

    def test_missing_name(self, qg: str, fixture_dir: Path):
        skill = fixture_dir / "plugins" / "test-plugin" / "skills" / "test-skill" / "SKILL.md"
        skill.write_text('---\ndescription: "A skill without a name"\n---\n\n# Test\n')
        result = run_qg(qg, "--check", "skill-structure", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "missing 'name'" in result.stdout

    def test_name_directory_mismatch(self, qg: str, fixture_dir: Path):
        skill = fixture_dir / "plugins" / "test-plugin" / "skills" / "test-skill" / "SKILL.md"
        skill.write_text('---\nname: wrong-name\ndescription: "Name mismatch"\n---\n\n# Wrong\n')
        result = run_qg(qg, "--check", "skill-structure", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "doesn't match directory" in result.stdout

    def test_missing_description(self, qg: str, fixture_dir: Path):
        skill = fixture_dir / "plugins" / "test-plugin" / "skills" / "test-skill" / "SKILL.md"
        skill.write_text("---\nname: test-skill\n---\n\n# Test\n")
        result = run_qg(qg, "--check", "skill-structure", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "missing 'description'" in result.stdout

    def test_uppercase_name(self, qg: str, fixture_dir: Path):
        upper_dir = fixture_dir / "plugins" / "test-plugin" / "skills" / "TestSkill"
        upper_dir.mkdir(parents=True, exist_ok=True)
        (upper_dir / "SKILL.md").write_text(
            '---\nname: TestSkill\ndescription: "Uppercase name"\n---\n\n# Test\n'
        )
        result = run_qg(qg, "--check", "skill-structure", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "not lowercase-hyphenated" in result.stdout


# ---------------------------------------------------------------------------
# doc-structure: missing SPEC.md
# ---------------------------------------------------------------------------


class TestDocStructureNegative:
    def test_missing_spec(self, qg: str, fixture_dir: Path):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.unlink()
        result = run_qg(qg, "--check", "doc-structure", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "SPEC.md missing" in result.stdout


# ---------------------------------------------------------------------------
# vsa-coverage: missing SPEC.md
# ---------------------------------------------------------------------------


class TestVsaCoverageNegative:
    def test_missing_spec(self, qg: str, fixture_dir: Path):
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.unlink()
        result = run_qg(qg, "--check", "vsa-coverage", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "no SPEC.md" in result.stdout


# ---------------------------------------------------------------------------
# doc-stats: stat-check footnotes
# ---------------------------------------------------------------------------


class TestDocStats:
    def test_valid_skill_count(self, qg: str, fixture_dir: Path):
        """Valid stat-check footnote with correct count passes."""
        readme = fixture_dir / "plugins" / "test-plugin" / "README.md"
        readme.write_text(
            "# Test Plugin\n\n"
            "## Skills (1)[^stat-skill-count]\n\n"
            "| Skill | Description |\n|---|---|\n"
            "| test-skill | A test skill |\n\n"
            "[^stat-skill-count]: stat-check: skill-count\n"
        )
        result = run_qg(qg, "--check", "doc-stats", "--path", str(fixture_dir))
        assert result.returncode == 0, f"Valid stat-check should pass:\n{result.stdout}"
        assert "skill-count = 1" in result.stdout

    def test_wrong_skill_count(self, qg: str, fixture_dir: Path):
        """Stat-check with wrong count warns but doesn't fail."""
        readme = fixture_dir / "plugins" / "test-plugin" / "README.md"
        readme.write_text(
            "# Test Plugin\n\n"
            "## Skills (5)[^stat-skill-count]\n\n"
            "Wrong count above.\n\n"
            "[^stat-skill-count]: stat-check: skill-count\n"
        )
        result = run_qg(qg, "--check", "doc-stats", "--path", str(fixture_dir))
        assert result.returncode == 0, "Stat mismatch should warn, not fail"
        assert "claims 5, actual 1" in result.stdout

    def test_unknown_check_name(self, qg: str, fixture_dir: Path):
        """Unknown stat-check name fails."""
        readme = fixture_dir / "plugins" / "test-plugin" / "README.md"
        readme.write_text(
            "# Test Plugin\n\n"
            "Has 42 widgets[^stat-widgets]\n\n"
            "[^stat-widgets]: stat-check: widget-count\n"
        )
        result = run_qg(qg, "--check", "doc-stats", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "unknown stat-check" in result.stdout

    def test_no_footnotes_warns(self, qg: str, fixture_dir: Path):
        """No stat-check footnotes produces a warning but passes."""
        # fixture_dir has no stat-check footnotes by default
        result = run_qg(qg, "--check", "doc-stats", "--path", str(fixture_dir))
        assert result.returncode == 0  # warnings don't fail
        assert "No stat-check footnotes" in result.stdout


# ---------------------------------------------------------------------------
# cross-links: SPEC.md dependency path validation
# ---------------------------------------------------------------------------


class TestCrossLinks:
    def test_valid_cross_link(self, qg: str, fixture_dir: Path):
        """Valid cross-link to existing SPEC.md passes."""
        # Create a second plugin to reference
        other = fixture_dir / "plugins" / "other-plugin" / "skills"
        other.mkdir(parents=True)
        (other / "SPEC.md").write_text("# Other Plugin Spec\n")

        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n"
            "## Dependencies\n\n"
            "| Dependency | Type | SPEC.md Path |\n"
            "|---|---|---|\n"
            "| other-plugin | external | `plugins/other-plugin/skills/SPEC.md` |\n"
        )
        result = run_qg(qg, "--check", "cross-links", "--path", str(fixture_dir))
        assert result.returncode == 0, f"Valid cross-link should pass:\n{result.stdout}"
        assert "exists" in result.stdout

    def test_broken_cross_link(self, qg: str, fixture_dir: Path):
        """Broken cross-link to non-existent path fails."""
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n"
            "## Dependencies\n\n"
            "| Dependency | Type | SPEC.md Path |\n"
            "|---|---|---|\n"
            "| missing-plugin | external | `plugins/missing-plugin/skills/SPEC.md` |\n"
        )
        result = run_qg(qg, "--check", "cross-links", "--path", str(fixture_dir))
        assert result.returncode != 0
        assert "not found" in result.stdout

    def test_na_entries_ignored(self, qg: str, fixture_dir: Path):
        """N/A entries (plain text, no backticks) are not validated."""
        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n"
            "## Dependencies\n\n"
            "| Dependency | Type | SPEC.md Path |\n"
            "|---|---|---|\n"
            "| Claude Code runtime | external | N/A — built into Claude Code runtime |\n"
        )
        result = run_qg(qg, "--check", "cross-links", "--path", str(fixture_dir))
        assert result.returncode == 0  # warnings don't fail
        assert "No cross-link paths" in result.stdout

    def test_mixed_valid_and_na(self, qg: str, fixture_dir: Path):
        """Mix of N/A and valid backtick paths works correctly."""
        other = fixture_dir / "plugins" / "other-plugin" / "skills"
        other.mkdir(parents=True, exist_ok=True)
        (other / "SPEC.md").write_text("# Other\n")

        spec = fixture_dir / "plugins" / "test-plugin" / "skills" / "SPEC.md"
        spec.write_text(
            "# Spec\n\n"
            "## Dependencies\n\n"
            "| Dependency | Type | SPEC.md Path |\n"
            "|---|---|---|\n"
            "| Claude Code runtime | external | N/A — built into runtime |\n"
            "| other-plugin | external | `plugins/other-plugin/skills/SPEC.md` |\n"
        )
        result = run_qg(qg, "--check", "cross-links", "--path", str(fixture_dir))
        assert result.returncode == 0, f"Mixed entries should pass:\n{result.stdout}"
        assert "exists" in result.stdout
