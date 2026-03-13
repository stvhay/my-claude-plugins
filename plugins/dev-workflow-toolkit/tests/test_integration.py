"""
Integration tests for dev-workflow-toolkit.

Replaces test-integration.sh: skill loading, dependency resolution,
template paths, reference files, trigger patterns, MCP configuration.
"""

import re
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _skill_dirs(skills_dir: Path) -> list[tuple[str, Path]]:
    """Return (name, path) for each skill directory with a SKILL.md."""
    return sorted(
        (d.name, d) for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()
    )


def _extract_frontmatter_field(skill_file: Path, field: str) -> str | None:
    """Extract a field from YAML frontmatter without a YAML dependency."""
    text = skill_file.read_text()
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None


# ---------------------------------------------------------------------------
# Skill loading
# ---------------------------------------------------------------------------


class TestSkillLoading:
    """Every skill directory must have a loadable SKILL.md with frontmatter."""

    def test_all_skills_loadable(self, skills_dir: Path):
        errors = []
        for name, skill_dir in _skill_dirs(skills_dir):
            skill_file = skill_dir / "SKILL.md"
            text = skill_file.read_text()
            if not text.startswith("---"):
                errors.append(f"{name}: missing frontmatter opening delimiter")
                continue
            fm_name = _extract_frontmatter_field(skill_file, "name")
            if not fm_name:
                errors.append(f"{name}: missing 'name' field in frontmatter")
        assert not errors, "Skills not loadable:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# Dependency resolution
# ---------------------------------------------------------------------------

EXPECTED_DEPS = {
    "brainstorming": "using-git-worktrees|writing-plans|documentation-standards",
    "writing-plans": "executing-plans|subagent-driven-development",
    "executing-plans": (
        "test-driven-development|systematic-debugging"
        "|verification-before-completion|finishing-a-development-branch"
    ),
    "subagent-driven-development": (
        "test-driven-development|systematic-debugging"
        "|verification-before-completion|finishing-a-development-branch"
    ),
    "verification-before-completion": "code-simplification",
    "requesting-code-review": "code-reviewer",
    "finishing-a-development-branch": "documentation-standards",
}


class TestDependencyResolution:
    """Skills that reference other skills must contain the expected references."""

    @pytest.mark.parametrize(
        "skill,expected_pattern",
        list(EXPECTED_DEPS.items()),
        ids=list(EXPECTED_DEPS.keys()),
    )
    def test_dependency_referenced(self, skills_dir: Path, skill: str, expected_pattern: str):
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text()
        assert re.search(expected_pattern, text), (
            f"{skill} does not reference expected dependencies: {expected_pattern}"
        )


# ---------------------------------------------------------------------------
# Template path resolution
# ---------------------------------------------------------------------------


class TestTemplatePaths:
    """project-init skill must reference and ship its templates."""

    def test_skill_references_templates(self, skills_dir: Path):
        skill_file = skills_dir / "project-init" / "SKILL.md"
        assert "templates/" in skill_file.read_text()

    @pytest.mark.parametrize(
        "template",
        [
            "bug-report.yml",
            "feature-request.yml",
            "pull_request_template.md",
            "CONTRIBUTING.md",
        ],
    )
    def test_template_exists(self, skills_dir: Path, template: str):
        path = skills_dir / "project-init" / "templates" / template
        assert path.exists(), f"Missing template: {template}"


# ---------------------------------------------------------------------------
# Template substitution
# ---------------------------------------------------------------------------


class TestTemplateSubstitution:
    """Templates should be static (no substitution markers)."""

    def test_bug_report_is_static(self, skills_dir: Path):
        path = skills_dir / "project-init" / "templates" / "bug-report.yml"
        if path.exists():
            assert "{{" not in path.read_text(), (
                "Bug report template has unexpected substitution markers"
            )

    def test_contributing_is_valid(self, skills_dir: Path):
        path = skills_dir / "project-init" / "templates" / "CONTRIBUTING.md"
        if path.exists():
            assert path.stat().st_size > 0, "CONTRIBUTING template is empty"


# ---------------------------------------------------------------------------
# Reference file resolution
# ---------------------------------------------------------------------------

SKILLS_WITH_REFS = [
    "code-simplification",
    "systematic-debugging",
    "test-driven-development",
    "requesting-code-review",
    "subagent-driven-development",
    "documentation-standards",
]


class TestReferenceFiles:
    """Skills that mention references/ must have the directory."""

    def test_reference_dirs_exist(self, skills_dir: Path):
        missing = []
        md = MarkdownIt()
        for skill in SKILLS_WITH_REFS:
            skill_file = skills_dir / skill / "SKILL.md"
            if not skill_file.exists():
                continue
            text = skill_file.read_text()
            tokens = md.parse(text)
            # Extract inline code spans containing "references/"
            code_spans: list[str] = []
            for token in tokens:
                if token.children:
                    for child in token.children:
                        if child.type == "code_inline" and "references/" in child.content:
                            code_spans.append(child.content)
            for span in code_spans:
                # Resolve path: if there's a "/" before "references/", it's a cross-skill ref
                ref_idx = span.find("references/")
                prefix = span[:ref_idx]
                ref_file_name = span[ref_idx + len("references/"):]
                if prefix and "/" not in prefix.rstrip("/"):
                    # Cross-skill reference like "other-skill/references/file.md"
                    owner = prefix.rstrip("/")
                else:
                    owner = skill
                ref_path = skills_dir / owner / "references" / ref_file_name
                if not ref_path.exists():
                    missing.append(f"{owner}/references/{ref_file_name}")
            # Also check for bare references/ mention (not in code spans) → own dir
            if "references/" in text and not code_spans:
                refs_dir = skills_dir / skill / "references"
                if not refs_dir.is_dir():
                    missing.append(f"{skill}/references")
        assert not missing, f"Missing reference paths: {missing}"


# ---------------------------------------------------------------------------
# Trigger pattern uniqueness
# ---------------------------------------------------------------------------


class TestTriggerPatterns:
    """Skill descriptions should not have obvious trigger conflicts."""

    def test_no_trigger_conflicts(self, skills_dir: Path):
        seen: dict[str, str] = {}
        conflicts = []
        for name, skill_dir in _skill_dirs(skills_dir):
            desc = _extract_frontmatter_field(skill_dir / "SKILL.md", "description")
            if not desc:
                continue
            # Extract first 6 significant words as trigger fingerprint.
            # Common prefixes like "Use when" are expected across skills;
            # conflicts only matter when the full trigger phrase matches.
            words = desc.lower().split()[:6]
            trigger = " ".join(words)
            if trigger in seen:
                conflicts.append(f"'{trigger}' in both {seen[trigger]} and {name}")
            else:
                seen[trigger] = name
        assert not conflicts, "Trigger pattern conflicts:\n" + "\n".join(conflicts)


# ---------------------------------------------------------------------------
# MCP configuration (setup-rag)
# ---------------------------------------------------------------------------


class TestMcpConfiguration:
    """setup-rag skill must include MCP configuration patterns."""

    @pytest.mark.parametrize(
        "term",
        [
            "ragling init",
            "mcpServers.ragling",
            ".ragling",
            "ragling.json",
        ],
    )
    def test_mcp_config_includes(self, skills_dir: Path, term: str):
        skill_file = skills_dir / "setup-rag" / "SKILL.md"
        assert term in skill_file.read_text(), f"MCP config missing: {term}"

    def test_references_mcp_json(self, skills_dir: Path):
        skill_file = skills_dir / "setup-rag" / "SKILL.md"
        assert ".mcp.json" in skill_file.read_text()


# ---------------------------------------------------------------------------
# Issue auto-creation in entry-point skills
# ---------------------------------------------------------------------------

ENTRY_POINT_SKILLS = {
    "brainstorming": "gh issue list --search",
    "systematic-debugging": "gh issue list --search",
}


class TestEntryPointIssueCreation:
    """Entry-point skills must auto-create issues with duplicate search."""  # Tests INV-7

    @pytest.mark.parametrize(
        "skill,pattern",
        list(ENTRY_POINT_SKILLS.items()),
        ids=list(ENTRY_POINT_SKILLS.keys()),
    )
    def test_entry_point_has_duplicate_search(self, skills_dir: Path, skill: str, pattern: str):
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text()
        assert pattern in text, (
            f"{skill} must contain '{pattern}' for duplicate issue search"
        )

    @pytest.mark.parametrize("skill", list(ENTRY_POINT_SKILLS.keys()))
    def test_entry_point_has_bd_description(self, skills_dir: Path, skill: str):
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text()
        assert "--description" in text, (
            f"{skill} must pass --description to bd create"
        )

    @pytest.mark.parametrize("skill", list(ENTRY_POINT_SKILLS.keys()))
    def test_entry_point_handles_issue_creation_failure(self, skills_dir: Path, skill: str):
        """FAIL-6: Entry-point skills must handle issue creation failure gracefully."""
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text().lower()
        assert any(phrase in text for phrase in [
            "fail", "unavailable", "proceed without", "error",
        ]), (
            f"{skill} must document graceful handling when issue creation fails (FAIL-6)"
        )

# ---------------------------------------------------------------------------
# Epic scope check in brainstorming and finishing
# ---------------------------------------------------------------------------


class TestEpicScopeCheck:
    """Brainstorming and finishing skills must include epic scope checks."""

    def test_brainstorming_has_epic_scope_step(self, skills_dir: Path):
        """Brainstorming checklist must include epic scope evaluation."""
        skill_file = skills_dir / "brainstorming" / "SKILL.md"
        text = skill_file.read_text()
        assert "Evaluate epic scope" in text, (
            "brainstorming must have 'Evaluate epic scope' checklist step"
        )

    def test_brainstorming_scope_check_mentions_epic_label(self, skills_dir: Path):
        """Brainstorming scope check must describe how to convert to epic."""
        skill_file = skills_dir / "brainstorming" / "SKILL.md"
        text = skill_file.read_text()
        assert "gh issue edit" in text and "epic" in text, (
            "brainstorming scope check must describe epic label conversion via gh issue edit"
        )

    def test_brainstorming_scope_check_in_dot_graph(self, skills_dir: Path):
        """Brainstorming dot graph must include the epic scope check node."""
        skill_file = skills_dir / "brainstorming" / "SKILL.md"
        text = skill_file.read_text()
        assert "Evaluate epic scope" in text and "digraph" in text, (
            "brainstorming dot graph must include 'Evaluate epic scope' node"
        )

    def test_finishing_has_scope_check(self, skills_dir: Path):
        """Finishing skill must include a pre-PR scope check."""
        skill_file = skills_dir / "finishing-a-development-branch" / "SKILL.md"
        text = skill_file.read_text()
        assert "scope" in text.lower() and "git log" in text and "git diff" in text, (
            "finishing must have scope check with git log and git diff analysis"
        )

    def test_finishing_scope_check_is_soft_gate(self, skills_dir: Path):
        """Finishing scope check must be a soft gate, not a hard gate."""
        skill_file = skills_dir / "finishing-a-development-branch" / "SKILL.md"
        text = skill_file.read_text().lower()
        assert "soft" in text, (
            "finishing scope check must be described as a soft gate"
        )


# ---------------------------------------------------------------------------
# Worktree auto-detection
# ---------------------------------------------------------------------------

WORKTREE_CONFIRM_SKILLS = [
    "executing-plans",
    "subagent-driven-development",
]


class TestWorktreeAutoDetection:
    """Skills that operate on repos must auto-detect worktree context."""

    def test_review_has_pr_worktree_resolution(self, skills_dir: Path):
        """INV-8(a): requesting-code-review resolves PR branch to local worktree."""
        skill_file = skills_dir / "requesting-code-review" / "SKILL.md"
        text = skill_file.read_text()
        assert "git worktree list" in text, (
            "requesting-code-review must use git worktree list for PR-to-worktree resolution"
        )
        assert "gh pr view" in text, (
            "requesting-code-review must use gh pr view to resolve PR branch"
        )

    @pytest.mark.parametrize("skill", WORKTREE_CONFIRM_SKILLS)
    def test_execution_skill_confirms_worktree(self, skills_dir: Path, skill: str):
        """INV-8(b): execution skills confirm worktree context."""
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text()
        assert "git rev-parse --show-toplevel" in text, (
            f"{skill} must contain git rev-parse --show-toplevel for worktree confirmation"
        )
        assert "git worktree list" in text, (
            f"{skill} must use git worktree list for robust worktree detection"
        )


# ---------------------------------------------------------------------------
# Review documentation standard
# ---------------------------------------------------------------------------

REVIEW_DOC_SKILLS = {
    "subagent-driven-development": ["bd update", "gh issue comment"],
    "verification-before-completion": ["bd update", "gh issue comment"],
    "requesting-code-review": ["gh pr comment", "gh api"],
    "receiving-code-review": ["atomic commit", "fix:"],
    "finishing-a-development-branch": ["check-review-documented"],
}


class TestReviewDocumentationStandard:
    """Skills must document review findings per INV-9."""

    @pytest.mark.parametrize(
        "skill,patterns",
        list(REVIEW_DOC_SKILLS.items()),
        ids=list(REVIEW_DOC_SKILLS.keys()),
    )
    def test_skill_has_review_documentation_instructions(  # Tests INV-9
        self, skills_dir: Path, skill: str, patterns: list[str]
    ):
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text().lower()
        for pattern in patterns:
            assert pattern.lower() in text, (
                f"{skill} must contain '{pattern}' for review documentation standard (INV-9)"
            )


class TestCheckReviewDocumentedScript:
    """check-review-documented.sh must exist and be executable."""  # Tests FAIL-7

    def test_script_exists(self, plugin_root: Path):
        script = plugin_root / "scripts" / "check-review-documented.sh"
        assert script.exists(), "scripts/check-review-documented.sh must exist"

    def test_script_is_executable(self, plugin_root: Path):
        script = plugin_root / "scripts" / "check-review-documented.sh"
        assert script.exists(), "Script must exist before checking permissions"
        import os

        assert os.access(script, os.X_OK), "check-review-documented.sh must be executable"

    def test_script_checks_beads(self, plugin_root: Path):
        script = plugin_root / "scripts" / "check-review-documented.sh"
        assert script.exists()
        text = script.read_text()
        assert "bd" in text, "Script must check beads (bd) for review status"

    def test_script_checks_github(self, plugin_root: Path):
        script = plugin_root / "scripts" / "check-review-documented.sh"
        assert script.exists()
        text = script.read_text()
        assert "gh issue" in text or "gh api" in text, (
            "Script must check GitHub issue for review comments"
        )
