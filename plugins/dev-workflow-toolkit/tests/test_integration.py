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
    "sprint": (
        "requesting-code-review|code-simplification|dispatching-parallel-agents"
        "|using-git-worktrees|brainstorming|writing-plans"
        "|executing-plans|finishing-a-development-branch|retrospective"
    ),
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
# GitHub state projection
# ---------------------------------------------------------------------------

# Skills that must project state to GitHub (INV-15)
GITHUB_PROJECTION_SKILLS = {
    "brainstorming": "gh issue comment",
    "writing-plans": "gh issue comment",
    "executing-plans": "gh issue comment",
    "subagent-driven-development": "gh issue comment",
    "verification-before-completion": "gh issue comment",
    "requesting-code-review": "gh pr comment",
    "receiving-code-review": "gh api repos/",
    "sprint": "gh issue comment",
}


class TestGitHubProjection:
    """Skills with projection points must include gh comment commands."""  # Tests INV-15

    @pytest.mark.parametrize(
        "skill,pattern",
        list(GITHUB_PROJECTION_SKILLS.items()),
        ids=list(GITHUB_PROJECTION_SKILLS.keys()),
    )
    def test_skill_projects_to_github(self, skills_dir: Path, skill: str, pattern: str):
        """Skills with projection points must include gh comment commands."""  # Tests INV-15
        skill_file = skills_dir / skill / "SKILL.md"
        assert skill_file.exists(), f"Skill file not found: {skill}"
        text = skill_file.read_text().lower()
        assert pattern in text, (
            f"{skill} must project state to GitHub via '{pattern}'"
        )


# ---------------------------------------------------------------------------
# Epic scope check in brainstorming and finishing
# ---------------------------------------------------------------------------


class TestEpicScopeCheck:
    """Brainstorming and finishing skills must include epic scope checks."""

    def test_brainstorming_epic_scope_step_ordering(self, skills_dir: Path):
        """Epic scope must come after design presentation and before doc impact."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        checklist_match = re.search(r"## Checklist.*?(?=\n## )", text, re.DOTALL)
        assert checklist_match, "brainstorming must have a Checklist section"
        lines = [
            l.strip()
            for l in checklist_match.group().splitlines()
            if re.match(r"\d+\.", l.strip())
        ]
        steps = {
            re.sub(r"^\d+\.\s+\*\*", "", l).split("**")[0]: i
            for i, l in enumerate(lines)
        }
        assert "Evaluate epic scope" in steps, "checklist must have 'Evaluate epic scope' step"
        assert "Present design" in steps, "checklist must have 'Present design' step"
        assert "Identify documentation impact" in steps, "checklist must have 'Identify documentation impact' step"
        assert steps["Present design"] < steps["Evaluate epic scope"], (
            "epic scope must come after design presentation"
        )
        assert steps["Evaluate epic scope"] < steps["Identify documentation impact"], (
            "epic scope must come before documentation impact"
        )

    def test_brainstorming_scope_check_mentions_epic_label(self, skills_dir: Path):
        """Brainstorming scope check must describe how to convert to epic."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        assert "gh issue edit" in text and "epic" in text, (
            "brainstorming scope check must describe epic label conversion via gh issue edit"
        )

    def test_finishing_scope_check_before_pr_creation(self, skills_dir: Path):
        """Scope check must appear before PR creation step."""
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        assert "Step 3b: Scope Check" in text, "finishing must have Step 3b: Scope Check"
        scope_pos = text.index("Step 3b: Scope Check")
        pr_pos = text.index("Step 4: Create Pull Request")
        assert scope_pos < pr_pos, (
            "scope check (Step 3b) must appear before PR creation (Step 4)"
        )

    def test_finishing_scope_check_offers_user_choice(self, skills_dir: Path):
        """Scope check must be a soft gate offering proceed-or-split choice."""
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        start = text.index("### Step 3b")
        end = text.index("### Step 4")
        section = text[start:end]
        assert "soft gate" in section.lower(), "scope check must be described as a soft gate"
        assert "Proceed anyway, or split?" in section, "must offer proceed-or-split choice"
        assert "If user proceeds" in section, "must describe what happens if user proceeds"


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
    "subagent-driven-development": ["gh issue comment"],
    "verification-before-completion": ["gh issue comment"],
    "requesting-code-review": ["gh pr comment", "gh api"],
    "receiving-code-review": ["atomic commit", "fix:"],
    "finishing-a-development-branch": ["gh pr create"],
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

    def test_script_has_no_beads_references(self, plugin_root: Path):
        """Script must not reference beads (bd) — removed in PR #121."""  # Tests FAIL-7
        script = plugin_root / "scripts" / "check-review-documented.sh"
        assert script.exists()
        text = script.read_text()
        assert "beads" not in text.lower(), "Script must not reference beads"
        # Allow "bd" as substring in other words, but not as a standalone command
        import re
        assert not re.search(r'\bbd\b', text), "Script must not invoke bd command"

    def test_script_checks_github(self, plugin_root: Path):
        script = plugin_root / "scripts" / "check-review-documented.sh"
        assert script.exists()
        text = script.read_text()
        assert "gh issue" in text or "gh api" in text, (
            "Script must check GitHub issue for review comments"
        )


# ---------------------------------------------------------------------------
# Branch check auto-worktree (issue #97)
# ---------------------------------------------------------------------------


class TestBranchCheckAutoWorktree:
    """Branch check must auto-create worktree without asking (issue #97)."""

    def test_no_ask_pattern_in_branch_check(self, skills_dir: Path):
        """Branch check must not ask user if they want a worktree."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        assert "Want me to run" not in text, (
            "branch check must auto-create worktree, not ask"
        )

    def test_auto_create_on_main(self, skills_dir: Path):
        """Branch check must auto-invoke using-git-worktrees on main."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        # Find the 1b. Branch Check section
        section_match = re.search(
            r"### 1b\. Branch Check.*?(?=\n### |\n## )", text, re.DOTALL
        )
        assert section_match, "must have '### 1b. Branch Check' section"
        section = section_match.group()
        assert "using-git-worktrees" in section, (
            "branch check must reference using-git-worktrees"
        )
        assert "If yes" not in section, (
            "branch check must not have conditional 'If yes' for worktree creation"
        )

# ---------------------------------------------------------------------------
# Structured question preference (INV-14)
# ---------------------------------------------------------------------------


class TestStructuredQuestionPreference:
    """SPEC.md must define INV-14 for AskUserQuestion and batching."""  # Tests INV-14

    def test_inv14_structured_question_preference(self, skills_dir: Path):
        """SPEC.md must contain INV-14 requiring AskUserQuestion for structured choices."""
        spec_path = skills_dir / "SPEC.md"
        content = spec_path.read_text()
        assert "INV-14" in content, "SPEC.md missing INV-14"
        inv14_start = content.index("INV-14")
        inv14_section = content[inv14_start:inv14_start + 500]
        assert "AskUserQuestion" in inv14_section, "INV-14 must reference AskUserQuestion"
        assert "batch" in inv14_section.lower(), "INV-14 must reference batching"

    def test_inv14_brainstorming_no_one_question_per_message(self, skills_dir: Path):
        """Brainstorming must NOT contain the old 'Only one question per message' pattern."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        assert "Only one question per message" not in text, (
            "brainstorming must not contain 'Only one question per message' — use batching (INV-14)"
        )

    def test_inv14_brainstorming_references_askuserquestion(self, skills_dir: Path):
        """Brainstorming must reference AskUserQuestion for structured choices."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        assert "AskUserQuestion" in text, (
            "brainstorming must reference AskUserQuestion (INV-14)"
        )

    def test_inv14_brainstorming_has_delegation_pattern(self, skills_dir: Path):
        """Brainstorming must include delegation pattern (approval or information)."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text().lower()
        assert "approval or information" in text, (
            "brainstorming must include delegation pattern 'approval or information' (INV-14)"
        )

    def test_inv14_brainstorming_no_ready_for_implementation(self, skills_dir: Path):
        """Brainstorming must NOT contain 'Ready to set up for implementation?' prompt."""
        text = (skills_dir / "brainstorming" / "SKILL.md").read_text()
        assert "Ready to set up for implementation?" not in text, (
            "brainstorming must not ask 'Ready to set up for implementation?' — proceed directly (INV-14)"
        )

    def test_inv14_finishing_references_askuserquestion(self, skills_dir: Path):
        """finishing-a-development-branch must reference AskUserQuestion for batched decisions."""
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        assert "AskUserQuestion" in text, (
            "finishing-a-development-branch must reference AskUserQuestion (INV-14)"
        )

    def test_inv14_finishing_batches_retrospective(self, skills_dir: Path):
        """finishing-a-development-branch must batch retrospective opt-in with other questions."""
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text().lower()
        assert "batch" in text and "retrospective" in text, (
            "finishing-a-development-branch must batch retrospective opt-in with pre-PR questions (INV-14)"
        )

    def test_inv14_retrospective_references_askuserquestion(self, skills_dir: Path):
        """retrospective must reference AskUserQuestion for wrap-up decisions."""
        text = (skills_dir / "retrospective" / "SKILL.md").read_text()
        assert "AskUserQuestion" in text, (
            "retrospective must reference AskUserQuestion (INV-14)"
        )

    def test_inv14_codify_no_one_question_mandate(self, skills_dir: Path):
        """codify-subsystem must NOT mandate 'one question at a time' in Key Principles."""
        text = (skills_dir / "codify-subsystem" / "SKILL.md").read_text()
        # Extract Key Principles section
        principles_match = re.search(
            r"## Key Principles.*?(?=\n## |\Z)", text, re.DOTALL
        )
        assert principles_match, "codify-subsystem must have a Key Principles section"
        principles = principles_match.group().lower()
        assert "one question at a time" not in principles, (
            "codify-subsystem Key Principles must not mandate 'one question at a time' — use batching (INV-14)"
        )

    def test_inv14_codify_references_adaptive_modality(self, skills_dir: Path):
        """codify-subsystem must reference AskUserQuestion or adaptive modality."""
        text = (skills_dir / "codify-subsystem" / "SKILL.md").read_text()
        has_ask = "AskUserQuestion" in text
        has_adaptive = "adaptive" in text.lower()
        assert has_ask or has_adaptive, (
            "codify-subsystem must reference AskUserQuestion or adaptive modality (INV-14)"
        )

    def test_inv14_project_init_references_askuserquestion(self, skills_dir: Path):
        """project-init must reference AskUserQuestion for batched setup questions."""
        text = (skills_dir / "project-init" / "SKILL.md").read_text()
        assert "AskUserQuestion" in text, (
            "project-init must reference AskUserQuestion (INV-14)"
        )

    def test_inv14_project_init_worktrees_default(self, skills_dir: Path):
        """project-init must establish .worktrees as default worktree location."""
        text = (skills_dir / "project-init" / "SKILL.md").read_text()
        assert ".worktrees" in text, (
            "project-init must establish .worktrees as default worktree location"
        )

    def test_inv14_documentation_standards_references_askuserquestion(self, skills_dir: Path):
        """documentation-standards must reference AskUserQuestion for batched approve/defer decisions."""
        text = (skills_dir / "documentation-standards" / "SKILL.md").read_text()
        assert "AskUserQuestion" in text, (
            "documentation-standards must reference AskUserQuestion (INV-14)"
        )


class TestFinishingGhFlagCompatibility:
    """#158: skill must not use nonexistent gh flags."""

    def test_inv18_no_fail_on_error_flag(self, skills_dir: Path):  # Tests INV-18
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        assert "--fail-on-error" not in text, (
            "SKILL.md must not reference --fail-on-error (not a valid gh pr checks flag); "
            "use exit-code check or --watch --fail-fast instead (#158)"
        )

    def test_ci_check_uses_fail_fast_for_watch(self, skills_dir: Path):
        """When --watch is used, --fail-fast must accompany it so CI failures exit non-zero."""
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        # Both CI check points must be retained
        assert text.count("gh pr checks") >= 2, (
            "SKILL.md must retain both CI verification points (Step 1d + Step 5b)"
        )
        # Any --watch usage must pair with --fail-fast (otherwise checks don't gate)
        import re
        for match in re.finditer(r"gh pr checks[^\n`]*", text):
            snippet = match.group(0)
            if "--watch" in snippet:
                assert "--fail-fast" in snippet, (
                    f"`gh pr checks --watch` must include --fail-fast to error-exit on CI failure; found: {snippet}"
                )


class TestFinishingWorktreeCleanupSafe:
    """#149: Step 6 must cd to main worktree before removing the current worktree."""

    def test_cleanup_cds_to_main_worktree_first(self, skills_dir: Path):
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        # Locate Step 6 section
        start = text.index("### Step 6: Cleanup Worktree")
        end = text.index("### Step 7")
        section = text[start:end]
        assert "git worktree list --porcelain" in section, (
            "Step 6 must resolve main worktree via `git worktree list --porcelain`"
        )
        assert 'cd "$MAIN_WORKTREE"' in section or "cd $MAIN_WORKTREE" in section, (
            "Step 6 must cd to main worktree before removing the current one (#149)"
        )
        cd_pos = section.index("MAIN_WORKTREE")
        rm_pos = section.index("git worktree remove")
        assert cd_pos < rm_pos, "cd to main worktree must precede `git worktree remove`"


class TestFinishingSquashMerge:
    """#162 + #156: explicit merge step with worktree + fast-forward handling."""

    def test_step_5c_squash_merge_exists(self, skills_dir: Path):
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        assert "### Step 5c:" in text or "## Step 5c:" in text, (
            "SKILL.md must have an explicit Step 5c for squash merge"
        )
        pos_5b = text.index("Step 5b")
        pos_5c = text.index("Step 5c")
        pos_6 = text.index("Step 6")
        assert pos_5b < pos_5c < pos_6, "Step 5c must appear between 5b and 6"

    def test_inv19_worktree_aware_merge(self, skills_dir: Path):  # Tests INV-19
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        start = text.index("Step 5c")
        end = text.index("Step 6")
        section = text[start:end]
        assert "gh pr merge" in section, "Step 5c must contain explicit `gh pr merge` command"
        assert "git rev-parse --show-toplevel" in section, (
            "Step 5c must detect worktree context via git rev-parse (#162)"
        )
        assert "--delete-branch" in section, (
            "Step 5c must reference --delete-branch to show the conditional path (#162)"
        )
        assert "gh api" in section and "git/refs/heads/" in section, (
            "Step 5c must delete remote branch via gh api when in worktree (#162)"
        )

    def test_inv20_fast_forward_detection(self, skills_dir: Path):  # Tests INV-20
        text = (skills_dir / "finishing-a-development-branch" / "SKILL.md").read_text()
        start = text.index("Step 5c")
        end = text.index("Step 6")
        section = text[start:end]
        assert "git merge-base --is-ancestor" in section, (
            "Step 5c must use `git merge-base --is-ancestor` for fast-forward detection (#156)"
        )
        assert "fast-forward" in section.lower() or "fast forward" in section.lower(), (
            "Step 5c must explain fast-forward detection behavior (#156)"
        )


class TestRequestingCodeReviewPosting:
    """#116 + #142: code-reviewer template must mandate posting to GitHub."""

    def test_reviewer_template_mandates_github_posting(self, skills_dir: Path):
        """Code-reviewer.md must have a MANDATORY-level instruction to post when PR_NUMBER is set."""
        text = (skills_dir / "requesting-code-review" / "code-reviewer.md").read_text()
        assert "MANDATORY" in text, (
            "code-reviewer.md must mark posting as MANDATORY (#116)"
        )
        task_list_end = text.find("## What Was Implemented")
        task_list_text = text[:task_list_end]
        assert "post" in task_list_text.lower() and "PR_NUMBER" in task_list_text, (
            "code-reviewer.md task list must include posting to PR (#116)"
        )

    def test_skill_description_prefers_over_builtin_review(self, skills_dir: Path):
        """Skill description must position itself as the canonical posting flow vs. built-in /review."""
        text = (skills_dir / "requesting-code-review" / "SKILL.md").read_text()
        fm_end = text.find("\n---", 3)
        fm = text[:fm_end]
        assert "GitHub" in fm or "github" in fm.lower(), (
            "requesting-code-review description must reference GitHub posting to distinguish it from built-in /review (#142)"
        )

    def test_skill_body_disambiguates_from_builtin_review(self, skills_dir: Path):
        """SKILL.md must explicitly contrast itself with built-in /review."""
        text = (skills_dir / "requesting-code-review" / "SKILL.md").read_text()
        assert "/review" in text, (
            "SKILL.md must reference the built-in /review command to disambiguate (#142)"
        )


class TestSubagentDrivenDevelopmentContext:
    """#159, #153, #122: spec reviewer context + parallel ordering + quantitative checks."""

    def test_spec_reviewer_has_expected_breakage_field(self, skills_dir: Path):
        """Spec reviewer template must accept cross-task dependency context (#159)."""
        text = (skills_dir / "subagent-driven-development" / "spec-reviewer-prompt.md").read_text()
        assert "Known Expected Breakage" in text, (
            "spec-reviewer-prompt.md must have an Expected Breakage field so orchestrator can pass cross-task context (#159)"
        )
        assert "handled by Task" in text or "handled there" in text, (
            "spec-reviewer-prompt.md must instruct reviewer how to mark cross-task findings (#159)"
        )

    def test_sdd_skill_instructs_populating_breakage_field(self, skills_dir: Path):
        """SKILL.md Step 6 must instruct the orchestrator to populate the Expected Breakage field."""
        text = (skills_dir / "subagent-driven-development" / "SKILL.md").read_text()
        assert "Known Expected Breakage" in text or "Expected Breakage" in text, (
            "SKILL.md must instruct orchestrator to populate the Expected Breakage field (#159)"
        )

    def test_sdd_parallel_commit_ordering_note(self, skills_dir: Path):
        """SKILL.md parallel dispatch section must warn about nondeterministic commit ordering (#153)."""
        text = (skills_dir / "subagent-driven-development" / "SKILL.md").read_text()
        start = text.index("Parallel dispatch")
        section = text[start:start + 1500]
        assert "nondeterministic" in section.lower() or "order" in section.lower(), (
            "Parallel dispatch section must discuss commit ordering nondeterminism (#153)"
        )
        assert "commit" in section.lower(), (
            "Parallel dispatch section must reference commit ordering specifically (#153)"
        )

    def test_sdd_has_quantitative_criteria_step(self, skills_dir: Path):
        """SKILL.md must have a step to verify quantitative task criteria before review (#122)."""
        text = (skills_dir / "subagent-driven-development" / "SKILL.md").read_text()
        assert "quantitative" in text.lower(), (
            "SKILL.md must reference quantitative criteria check (#122)"
        )
        quant_pos = text.lower().index("quantitative")
        spec_review_pos = text.index("Spec review.")
        assert quant_pos < spec_review_pos, (
            "Quantitative criteria check must appear before Spec review step (#122)"
        )


class TestUsingGitWorktreesIsolation:
    """#160 + #120: worktree creation must branch from default branch and isolate env."""

    def test_worktree_branches_from_default_branch(self, skills_dir: Path):
        """SKILL.md must branch from origin/<default-branch>, not current branch (#120)."""
        text = (skills_dir / "using-git-worktrees" / "SKILL.md").read_text()
        assert "symbolic-ref" in text or "DEFAULT_BRANCH" in text, (
            "SKILL.md must detect the repo's default branch explicitly (#120)"
        )
        assert "origin/$DEFAULT_BRANCH" in text or "origin/main" in text, (
            "SKILL.md must create worktree branch based on origin/<default-branch> (#120)"
        )

    def test_worktree_unsets_virtual_env(self, skills_dir: Path):
        """SKILL.md must unset VIRTUAL_ENV before setup to avoid parent .venv bleedthrough (#160)."""
        text = (skills_dir / "using-git-worktrees" / "SKILL.md").read_text()
        assert "unset VIRTUAL_ENV" in text, (
            "SKILL.md must unset VIRTUAL_ENV in setup phase to isolate worktree's Python env (#160)"
        )

    def test_worktree_sets_uv_link_mode_copy(self, skills_dir: Path):
        """SKILL.md must set UV_LINK_MODE=copy to avoid hardlink failures in container envs (#160)."""
        text = (skills_dir / "using-git-worktrees" / "SKILL.md").read_text()
        assert "UV_LINK_MODE=copy" in text, (
            "SKILL.md must export UV_LINK_MODE=copy for bind-mount/container environments (#160)"
        )
