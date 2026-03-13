"""Tests for compute_version.py — semver computation and version file management."""

import json
from pathlib import Path

import pytest

from scripts.compute_version import (
    bump_version,
    check_changelog_has_version,
    check_version_consistency,
    main,
    parse_changelog_bump_type,
    read_version_from_plugin_json,
    read_version_from_pyproject_toml,
    rewrite_changelog_unreleased,
    update_version_files,
    update_version_files_no_changelog_check,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _setup_plugin_json(root: Path, version: str, **extra: str) -> Path:
    """Create a .claude-plugin/plugin.json with given version."""
    plugin_dir = root / ".claude-plugin"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    data: dict[str, str] = {"name": "test-plugin", "version": version, **extra}
    path = plugin_dir / "plugin.json"
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def _setup_pyproject_toml(root: Path, version: str) -> Path:
    """Create a pyproject.toml with given version."""
    path = root / "pyproject.toml"
    path.write_text(
        f'[project]\nname = "test-plugin"\nversion = "{version}"\n'
        f'requires-python = ">=3.13"\ndependencies = []\n'
    )
    return path


def _setup_version_files(root: Path, version: str, **plugin_json_extra: str) -> None:
    """Create both plugin.json and pyproject.toml with matching version."""
    _setup_plugin_json(root, version, **plugin_json_extra)
    _setup_pyproject_toml(root, version)


def _setup_changelog(root: Path, versions: list[str]) -> Path:
    """Create a CHANGELOG.md with ## vX.Y.Z sections."""
    lines = ["# Changelog\n"]
    for v in versions:
        lines.append(f"\n## v{v}\n\n- Some change\n")
    path = root / "CHANGELOG.md"
    path.write_text("\n".join(lines))
    return path


def _setup_changelog_unreleased(
    root: Path, bump_type: str, *, previous_versions: list[str] | None = None
) -> Path:
    """Create a CHANGELOG.md with ## Unreleased section containing a bump comment."""
    lines = ["# Changelog\n", f"\n## Unreleased\n\n<!-- bump: {bump_type} -->\n\n- Some new feature\n"]
    for v in previous_versions or []:
        lines.append(f"\n## v{v}\n\n- Some change\n")
    path = root / "CHANGELOG.md"
    path.write_text("\n".join(lines))
    return path


# ── bump_version ─────────────────────────────────────────────────────


class TestBumpVersion:
    def test_patch(self) -> None:
        assert bump_version("1.8.1", "patch") == "1.8.2"

    def test_minor(self) -> None:
        assert bump_version("1.8.1", "minor") == "1.9.0"

    def test_major(self) -> None:
        assert bump_version("1.8.1", "major") == "2.0.0"

    def test_from_zero_patch(self) -> None:
        assert bump_version("0.1.0", "patch") == "0.1.1"

    def test_from_zero_minor(self) -> None:
        assert bump_version("0.1.0", "minor") == "0.2.0"

    def test_from_zero_major(self) -> None:
        assert bump_version("0.1.0", "major") == "1.0.0"

    def test_invalid_bump_type(self) -> None:
        with pytest.raises(ValueError, match="bump_type"):
            bump_version("1.0.0", "invalid")

    def test_invalid_version_format(self) -> None:
        with pytest.raises(ValueError, match="version"):
            bump_version("not-a-version", "patch")

    def test_strips_v_prefix(self) -> None:
        assert bump_version("v1.2.3", "patch") == "1.2.4"

    def test_strips_prerelease_patch(self) -> None:
        assert bump_version("1.8.2-0", "patch") == "1.8.3"

    def test_strips_prerelease_minor(self) -> None:
        assert bump_version("1.8.2-0", "minor") == "1.9.0"

    def test_strips_prerelease_major(self) -> None:
        assert bump_version("1.8.2-0", "major") == "2.0.0"


# ── read_version_from_plugin_json ────────────────────────────────────


class TestReadVersionFromPluginJson:
    def test_reads_version(self, tmp_path: Path) -> None:
        _setup_plugin_json(tmp_path, "1.2.3")
        assert read_version_from_plugin_json(tmp_path) == "1.2.3"

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_version_from_plugin_json(tmp_path)


# ── read_version_from_pyproject_toml ─────────────────────────────────


class TestReadVersionFromPyprojectToml:
    def test_reads_version(self, tmp_path: Path) -> None:
        _setup_pyproject_toml(tmp_path, "2.0.0")
        assert read_version_from_pyproject_toml(tmp_path) == "2.0.0"

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            read_version_from_pyproject_toml(tmp_path)


# ── check_version_consistency ────────────────────────────────────────


class TestCheckVersionConsistency:
    def test_passes_when_consistent(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        # Should not raise
        check_version_consistency(tmp_path)

    def test_exits_on_drift(self, tmp_path: Path) -> None:
        _setup_plugin_json(tmp_path, "1.0.0")
        _setup_pyproject_toml(tmp_path, "2.0.0")
        with pytest.raises(SystemExit) as exc_info:
            check_version_consistency(tmp_path)
        assert exc_info.value.code == 1

    def test_single_file_ok(self, tmp_path: Path) -> None:
        _setup_plugin_json(tmp_path, "1.0.0")
        # Only one file — nothing to compare, should not raise
        check_version_consistency(tmp_path)


# ── check_changelog_has_version ──────────────────────────────────────


class TestCheckChangelogHasVersion:
    def test_passes_when_section_exists(self, tmp_path: Path) -> None:
        _setup_changelog(tmp_path, ["1.2.3"])
        check_changelog_has_version(tmp_path, "1.2.3")

    def test_exits_when_section_missing(self, tmp_path: Path) -> None:
        _setup_changelog(tmp_path, ["1.0.0"])
        with pytest.raises(SystemExit) as exc_info:
            check_changelog_has_version(tmp_path, "2.0.0")
        assert exc_info.value.code == 1

    def test_exits_when_changelog_missing(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc_info:
            check_changelog_has_version(tmp_path, "1.0.0")
        assert exc_info.value.code == 1


# ── update_version_files ─────────────────────────────────────────────


class TestUpdateVersionFiles:
    def test_updates_plugin_json(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        _setup_changelog(tmp_path, ["1.1.0"])
        update_version_files(tmp_path, "1.1.0")
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == "1.1.0"

    def test_updates_pyproject_toml(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        _setup_changelog(tmp_path, ["1.1.0"])
        update_version_files(tmp_path, "1.1.0")
        import tomllib

        data = tomllib.loads((tmp_path / "pyproject.toml").read_text())
        assert data["project"]["version"] == "1.1.0"

    def test_preserves_other_plugin_json_fields(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0", license="MIT")
        _setup_changelog(tmp_path, ["1.1.0"])
        update_version_files(tmp_path, "1.1.0")
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["name"] == "test-plugin"
        assert data["license"] == "MIT"

    def test_errors_if_changelog_missing(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        with pytest.raises(SystemExit) as exc_info:
            update_version_files(tmp_path, "1.1.0")
        assert exc_info.value.code == 1
        # Version should NOT have been updated
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == "1.0.0"

    def test_errors_if_versions_inconsistent(self, tmp_path: Path) -> None:
        _setup_plugin_json(tmp_path, "1.0.0")
        _setup_pyproject_toml(tmp_path, "2.0.0")
        _setup_changelog(tmp_path, ["3.0.0"])
        with pytest.raises(SystemExit) as exc_info:
            update_version_files(tmp_path, "3.0.0")
        assert exc_info.value.code == 1
        # Versions should NOT have been updated
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == "1.0.0"


# ── parse_changelog_bump_type ────────────────────────────────────────


class TestParseChangelogBumpType:
    def test_reads_patch(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "patch", previous_versions=["1.0.0"])
        assert parse_changelog_bump_type(tmp_path) == "patch"

    def test_reads_minor(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "minor")
        assert parse_changelog_bump_type(tmp_path) == "minor"

    def test_reads_major(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "major")
        assert parse_changelog_bump_type(tmp_path) == "major"

    def test_exits_no_changelog(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit) as exc_info:
            parse_changelog_bump_type(tmp_path)
        assert exc_info.value.code == 1

    def test_exits_no_unreleased_section(self, tmp_path: Path) -> None:
        _setup_changelog(tmp_path, ["1.0.0"])
        with pytest.raises(SystemExit) as exc_info:
            parse_changelog_bump_type(tmp_path)
        assert exc_info.value.code == 1

    def test_exits_no_bump_comment(self, tmp_path: Path) -> None:
        path = tmp_path / "CHANGELOG.md"
        path.write_text("# Changelog\n\n## Unreleased\n\n- Some change\n")
        with pytest.raises(SystemExit) as exc_info:
            parse_changelog_bump_type(tmp_path)
        assert exc_info.value.code == 1

    def test_exits_invalid_bump_type(self, tmp_path: Path) -> None:
        path = tmp_path / "CHANGELOG.md"
        path.write_text("# Changelog\n\n## Unreleased\n\n<!-- bump: huge -->\n\n- Some change\n")
        with pytest.raises(SystemExit) as exc_info:
            parse_changelog_bump_type(tmp_path)
        assert exc_info.value.code == 1

    def test_whitespace_tolerance(self, tmp_path: Path) -> None:
        path = tmp_path / "CHANGELOG.md"
        path.write_text("# Changelog\n\n## Unreleased\n\n<!--  bump:  minor  -->\n\n- Some change\n")
        assert parse_changelog_bump_type(tmp_path) == "minor"

    def test_bump_comment_only_in_unreleased_section(self, tmp_path: Path) -> None:
        """Bump comment in a versioned section should NOT be found."""
        path = tmp_path / "CHANGELOG.md"
        path.write_text(
            "# Changelog\n\n## Unreleased\n\n- Some change\n\n"
            "## v1.0.0\n\n<!-- bump: patch -->\n\n- Old change\n"
        )
        with pytest.raises(SystemExit) as exc_info:
            parse_changelog_bump_type(tmp_path)
        assert exc_info.value.code == 1


# ── rewrite_changelog_unreleased ─────────────────────────────────────


class TestRewriteChangelogUnreleased:
    def test_replaces_heading(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "minor", previous_versions=["1.0.0"])
        rewrite_changelog_unreleased(tmp_path, "1.1.0")
        content = (tmp_path / "CHANGELOG.md").read_text()
        assert "## v1.1.0" in content
        assert "## Unreleased" not in content

    def test_removes_bump_comment(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "patch")
        rewrite_changelog_unreleased(tmp_path, "1.0.1")
        content = (tmp_path / "CHANGELOG.md").read_text()
        assert "<!-- bump:" not in content

    def test_preserves_content(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "minor", previous_versions=["1.0.0"])
        rewrite_changelog_unreleased(tmp_path, "1.1.0")
        content = (tmp_path / "CHANGELOG.md").read_text()
        assert "- Some new feature" in content
        assert "## v1.0.0" in content
        assert "- Some change" in content

    def test_preserves_previous_versions(self, tmp_path: Path) -> None:
        _setup_changelog_unreleased(tmp_path, "major", previous_versions=["2.0.0", "1.0.0"])
        rewrite_changelog_unreleased(tmp_path, "3.0.0")
        content = (tmp_path / "CHANGELOG.md").read_text()
        assert "## v3.0.0" in content
        assert "## v2.0.0" in content
        assert "## v1.0.0" in content


# ── update_version_files_no_changelog_check ──────────────────────────


class TestUpdateVersionFilesNoChangelogCheck:
    def test_updates_without_changelog(self, tmp_path: Path) -> None:
        """Should update version files without requiring changelog ## vX.Y.Z section."""
        _setup_version_files(tmp_path, "1.0.0")
        # No changelog at all - should still work
        update_version_files_no_changelog_check(tmp_path, "1.1.0")
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == "1.1.0"

    def test_still_checks_consistency(self, tmp_path: Path) -> None:
        _setup_plugin_json(tmp_path, "1.0.0")
        _setup_pyproject_toml(tmp_path, "2.0.0")
        with pytest.raises(SystemExit) as exc_info:
            update_version_files_no_changelog_check(tmp_path, "3.0.0")
        assert exc_info.value.code == 1

    def test_updates_both_files(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        update_version_files_no_changelog_check(tmp_path, "2.0.0")
        import tomllib

        pj = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        pp = tomllib.loads((tmp_path / "pyproject.toml").read_text())
        assert pj["version"] == "2.0.0"
        assert pp["project"]["version"] == "2.0.0"


# ── CLI --ci mode ────────────────────────────────────────────────────


class TestCiMode:
    def test_ci_prints_version(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        _setup_changelog_unreleased(tmp_path, "minor", previous_versions=["1.0.0"])
        main(["--ci", "--project-root", str(tmp_path)])
        assert capsys.readouterr().out.strip() == "1.1.0"

    def test_ci_update_writes_files_and_changelog(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        _setup_changelog_unreleased(tmp_path, "patch", previous_versions=["1.0.0"])
        main(["--ci", "--update", "--project-root", str(tmp_path)])

        # Version files updated
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == "1.0.1"

        # Changelog rewritten
        content = (tmp_path / "CHANGELOG.md").read_text()
        assert "## v1.0.1" in content
        assert "## Unreleased" not in content
        assert "<!-- bump:" not in content

    def test_ci_without_update_does_not_write(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        _setup_changelog_unreleased(tmp_path, "major", previous_versions=["1.0.0"])
        main(["--ci", "--project-root", str(tmp_path)])

        # Version files NOT updated
        data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())
        assert data["version"] == "1.0.0"

        # Changelog NOT rewritten
        content = (tmp_path / "CHANGELOG.md").read_text()
        assert "## Unreleased" in content

    def test_ci_exits_without_changelog(self, tmp_path: Path) -> None:
        _setup_version_files(tmp_path, "1.0.0")
        with pytest.raises(SystemExit) as exc_info:
            main(["--ci", "--project-root", str(tmp_path)])
        assert exc_info.value.code == 1

    def test_ci_and_bump_type_mutually_exclusive(self) -> None:
        """Providing both --ci and a bump_type should error."""
        with pytest.raises(SystemExit):
            main(["--ci", "patch"])
