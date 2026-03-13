#!/usr/bin/env python3
"""Semver version computation and version file management.

Reads plugin.json and pyproject.toml, computes next semver bump,
and optionally writes updated versions. Enforces changelog presence
and version consistency between files.

Usage:
    compute_version.py <patch|minor|major> [--update] [--project-root <path>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Semver computation ───────────────────────────────────────────────

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-.+)?$")


def bump_version(current: str, bump_type: str) -> str:
    """Compute next semver from current version string.

    Strips v prefix and prerelease suffix. Returns bare MAJOR.MINOR.PATCH.
    """
    if bump_type not in ("patch", "minor", "major"):
        msg = f"bump_type must be patch, minor, or major, got: {bump_type!r}"
        raise ValueError(msg)

    m = _VERSION_RE.match(current.strip())
    if not m:
        msg = f"Invalid version format: {current!r}"
        raise ValueError(msg)

    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # major
        major += 1
        minor = 0
        patch = 0

    return f"{major}.{minor}.{patch}"


# ── Version file readers ─────────────────────────────────────────────


def read_version_from_plugin_json(project_root: Path) -> str:
    """Read version from .claude-plugin/plugin.json."""
    path = project_root / ".claude-plugin" / "plugin.json"
    if not path.exists():
        msg = f"plugin.json not found: {path}"
        raise FileNotFoundError(msg)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["version"]


def read_version_from_pyproject_toml(project_root: Path) -> str:
    """Read version from pyproject.toml using tomllib."""
    path = project_root / "pyproject.toml"
    if not path.exists():
        msg = f"pyproject.toml not found: {path}"
        raise FileNotFoundError(msg)
    import tomllib

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return data["project"]["version"]


# ── Version discovery ────────────────────────────────────────────────


def _discover_versions(project_root: Path) -> dict[str, str]:
    """Find all version files and their versions. Returns {filename: version}."""
    versions: dict[str, str] = {}
    try:
        versions["plugin.json"] = read_version_from_plugin_json(project_root)
    except FileNotFoundError:
        pass
    try:
        versions["pyproject.toml"] = read_version_from_pyproject_toml(project_root)
    except FileNotFoundError:
        pass
    return versions


# ── Consistency checks ───────────────────────────────────────────────


def check_version_consistency(project_root: Path) -> None:
    """Exit with code 1 if version files disagree."""
    versions = _discover_versions(project_root)
    unique = set(versions.values())
    if len(unique) > 1:
        detail = ", ".join(f"{k}={v}" for k, v in sorted(versions.items()))
        print(f"VERSION_DRIFT: {detail}", file=sys.stderr)
        sys.exit(1)


def check_changelog_has_version(project_root: Path, version: str) -> None:
    """Exit with code 1 if CHANGELOG.md lacks a ## vX.Y.Z section."""
    changelog = project_root / "CHANGELOG.md"
    if not changelog.exists():
        print(f"CHANGELOG_MISSING: CHANGELOG.md not found in {project_root}", file=sys.stderr)
        sys.exit(1)

    content = changelog.read_text(encoding="utf-8")
    # Match ## vX.Y.Z (with or without trailing text)
    pattern = re.compile(rf"^## v{re.escape(version)}\b", re.MULTILINE)
    if not pattern.search(content):
        print(
            f"CHANGELOG_MISSING: no '## v{version}' section in CHANGELOG.md",
            file=sys.stderr,
        )
        sys.exit(1)


# ── Version file writers ─────────────────────────────────────────────


def _write_plugin_json(project_root: Path, version: str) -> None:
    """Update version in .claude-plugin/plugin.json, preserving other fields."""
    path = project_root / ".claude-plugin" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_pyproject_toml(project_root: Path, version: str) -> None:
    """Update version in pyproject.toml using TOML parser."""
    import tomllib

    import tomli_w

    path = project_root / "pyproject.toml"
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    data["project"]["version"] = version
    path.write_bytes(tomli_w.dumps(data).encode("utf-8"))


def update_version_files(project_root: Path, new_version: str) -> None:
    """Update all version files after validating consistency and changelog.

    Checks are run first — no files are written if any check fails.
    """
    # Pre-checks: consistency and changelog
    check_version_consistency(project_root)
    check_changelog_has_version(project_root, new_version)

    # Write updates
    versions = _discover_versions(project_root)
    if "plugin.json" in versions:
        _write_plugin_json(project_root, new_version)
    if "pyproject.toml" in versions:
        _write_pyproject_toml(project_root, new_version)


# ── CLI ──────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="compute-version",
        description="Compute next semver and optionally update version files",
    )
    parser.add_argument(
        "bump_type",
        choices=["patch", "minor", "major"],
        help="Semver bump type",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Write updated version to all version files",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: cwd)",
    )
    args = parser.parse_args(argv)

    project_root = args.project_root.resolve()

    # Read current version from whichever file exists
    versions = _discover_versions(project_root)
    if not versions:
        print("ERROR: no version files found (plugin.json or pyproject.toml)", file=sys.stderr)
        sys.exit(1)

    # Check consistency before computing
    check_version_consistency(project_root)

    current = next(iter(versions.values()))
    new_version = bump_version(current, args.bump_type)

    if args.update:
        update_version_files(project_root, new_version)

    # Output new version to stdout
    print(new_version)


if __name__ == "__main__":
    main()
