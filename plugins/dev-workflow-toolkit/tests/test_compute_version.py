"""Tests for compute_version.py — semver computation and version file management."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.compute_version import (
    bump_version,
    check_changelog_has_version,
    check_version_consistency,
    read_version_from_plugin_json,
    read_version_from_pyproject_toml,
    update_version_files,
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
