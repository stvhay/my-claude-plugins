#!/usr/bin/env python3
"""Quality gate: structural validation for dev-workflow-toolkit projects.

Uses markdown-it-py to parse SPEC.md and SKILL.md files structurally
rather than relying on brittle regex patterns.

Usage:
    quality-gate.py [--check <name>] [--path <project-root>]
    quality-gate.py --help

Checks: inv-numbering, issue-tracking, skill-structure, doc-structure,
        vsa-coverage, cross-links, tool-health, doc-stats
"""

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Any

from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.front_matter import front_matter_plugin

# ── Colors ───────────────────────────────────────────────────────────

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

# ── Reporting ────────────────────────────────────────────────────────


@dataclass
class Results:
    checks: int = 0
    failures: int = 0


def report(results: Results, status: str, check: str, detail: str) -> None:
    results.checks += 1
    if status == "PASS":
        print(f"{GREEN}✓{NC} [{check}] {detail}")
    elif status == "WARN":
        print(f"{YELLOW}!{NC} [{check}] {detail}")
    else:
        print(f"{RED}✗{NC} [{check}] {detail}")
        results.failures += 1


# ── Markdown parsing helpers ─────────────────────────────────────────


def parse_md(path: Path) -> list[Any]:
    """Parse a markdown file into tokens using markdown-it-py."""
    md = MarkdownIt().enable("table")
    front_matter_plugin(md)
    footnote_plugin(md)
    return md.parse(path.read_text(encoding="utf-8"))


def extract_frontmatter(tokens: list[Any]) -> dict[str, str]:
    """Extract YAML frontmatter fields as a flat dict of strings."""
    for token in tokens:
        if token.type == "front_matter":
            result = {}
            for line in token.content.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    val = val.strip().strip('"').strip("'")
                    result[key.strip()] = val
            return result
    return {}


def has_frontmatter(tokens: list[Any]) -> bool:
    return any(t.type == "front_matter" for t in tokens)


def extract_table_first_column_ids(tokens: list[Any], prefix: str) -> list[int]:
    """Extract numbered IDs from the first column of table body rows.

    Looks for cells matching PREFIX-N (e.g. INV-1, FAIL-3) in the first
    td of each table row. Returns the list of numbers in document order.
    """
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    ids: list[int] = []

    i = 0
    while i < len(tokens):
        if tokens[i].type == "tr_open" and i > 0:
            # Find the first td content in this row
            j = i + 1
            while j < len(tokens) and tokens[j].type != "tr_close":
                if tokens[j].type == "inline":
                    # First inline in the row = first column
                    m = pattern.match(tokens[j].content.strip())
                    if m:
                        ids.append(int(m.group(1)))
                    break
                j += 1
        i += 1
    return ids


def extract_list_item_ids(tokens: list[Any], prefix: str) -> list[int]:
    """Extract numbered IDs from list item definitions.

    Matches PREFIX-N at the start of a list item's first text content,
    regardless of formatting (bold, italic, plain). This uses structural
    position (first text in a list item) rather than formatting detection.
    """
    pattern = re.compile(rf"{re.escape(prefix)}-(\d+)")
    ids: list[int] = []

    in_list_item = False
    found_in_item = False
    for token in tokens:
        if token.type == "list_item_open":
            in_list_item = True
            found_in_item = False
        elif token.type == "list_item_close":
            in_list_item = False
        elif in_list_item and not found_in_item and token.type == "inline":
            # Check the first text content in this list item
            if token.children:
                for child in token.children:
                    if child.type == "text" and child.content.strip():
                        m = pattern.match(child.content.strip())
                        if m:
                            ids.append(int(m.group(1)))
                        found_in_item = True
                        break
    return ids


def extract_definition_ids(tokens: list[Any], prefix: str) -> list[int]:
    """Extract definition-site IDs from either table or list format.

    Checks two structural positions:
    1. First column of table body rows (e.g., | INV-1 | description |)
    2. Start of list items (e.g., - **INV-1:** description, - INV-1: description)

    Paragraph text is ignored — those are references, not definitions.
    """
    table_ids = extract_table_first_column_ids(tokens, prefix)
    list_ids = extract_list_item_ids(tokens, prefix)
    return table_ids or list_ids


# ── Checks ───────────────────────────────────────────────────────────


def check_inv_numbering(results: Results, project_root: Path) -> None:
    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        report(results, "WARN", "inv-numbering", "No plugins/ directory found")
        return

    spec_files = sorted(plugins_dir.rglob("skills/SPEC.md"))
    if not spec_files:
        report(results, "WARN", "inv-numbering", "No SPEC.md files found")
        return

    for spec in spec_files:
        rel = spec.relative_to(project_root)
        tokens = parse_md(spec)

        for prefix in ("INV", "FAIL"):
            ids = extract_definition_ids(tokens, prefix)
            if not ids:
                continue

            # Check duplicates
            seen: dict[int, int] = {}
            dupes: list[int] = []
            for n in ids:
                seen[n] = seen.get(n, 0) + 1
                if seen[n] == 2:
                    dupes.append(n)

            if dupes:
                dupe_str = ", ".join(f"{prefix}-{d}" for d in dupes)
                report(
                    results,
                    "FAIL",
                    "inv-numbering",
                    f"{rel}: duplicate definitions: {dupe_str}",
                )
                continue

            # Check sequential from 1
            unique = sorted(set(ids))
            ok = True
            for expected, actual in enumerate(unique, start=1):
                if actual != expected:
                    report(
                        results,
                        "FAIL",
                        "inv-numbering",
                        f"{rel}: {prefix}-{actual} found, expected {prefix}-{expected}",
                    )
                    ok = False
                    break

            if ok:
                report(
                    results,
                    "PASS",
                    "inv-numbering",
                    f"{rel}: {prefix}-1 through {prefix}-{len(unique)} sequential, no duplicates",
                )


def check_skill_structure(results: Results, project_root: Path) -> None:
    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        report(results, "WARN", "skill-structure", "No plugins/ directory found")
        return

    skill_files = sorted(plugins_dir.rglob("SKILL.md"))
    if not skill_files:
        report(results, "WARN", "skill-structure", "No SKILL.md files found")
        return

    names_seen: set[str] = set()

    for skill_file in skill_files:
        rel = skill_file.relative_to(project_root)
        dir_name = skill_file.parent.name
        tokens = parse_md(skill_file)

        # Check frontmatter exists
        if not has_frontmatter(tokens):
            report(results, "FAIL", "skill-structure", f"{rel}: missing YAML frontmatter")
            continue

        fm = extract_frontmatter(tokens)

        # Check name
        skill_name = fm.get("name", "")
        if not skill_name:
            report(results, "FAIL", "skill-structure", f"{rel}: missing 'name' in frontmatter")
            continue

        if skill_name != dir_name:
            report(
                results,
                "FAIL",
                "skill-structure",
                f"{rel}: name '{skill_name}' doesn't match directory '{dir_name}'",
            )
            continue

        if not re.match(r"^[a-z][a-z0-9-]*$", skill_name):
            report(
                results,
                "FAIL",
                "skill-structure",
                f"{rel}: name '{skill_name}' not lowercase-hyphenated",
            )
            continue

        if len(skill_name) > 64:
            report(
                results,
                "FAIL",
                "skill-structure",
                f"{rel}: name '{skill_name}' exceeds 64 chars",
            )
            continue

        # Check description
        if "description" not in fm:
            report(
                results,
                "FAIL",
                "skill-structure",
                f"{rel}: missing 'description' in frontmatter",
            )
            continue

        # Check uniqueness
        if skill_name in names_seen:
            report(results, "FAIL", "skill-structure", f"{rel}: duplicate name '{skill_name}'")
            continue
        names_seen.add(skill_name)

        report(results, "PASS", "skill-structure", f"{rel}: valid ({skill_name})")


def check_doc_structure(results: Results, project_root: Path) -> None:
    for doc in ("README.md", "docs/ARCHITECTURE.md", "docs/DESIGN.md"):
        path = project_root / doc
        if path.exists():
            report(results, "PASS", "doc-structure", f"{doc} exists")
        else:
            report(results, "WARN", "doc-structure", f"{doc} missing (recommended)")

    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        return

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        spec = plugin_dir / "skills" / "SPEC.md"
        name = plugin_dir.name
        if spec.exists():
            report(results, "PASS", "doc-structure", f"plugins/{name}/skills/SPEC.md exists")
        else:
            report(results, "FAIL", "doc-structure", f"plugins/{name}/skills/SPEC.md missing")


def check_vsa_coverage(results: Results, project_root: Path) -> None:
    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        return

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        skills_dir = plugin_dir / "skills"
        if not skills_dir.is_dir():
            continue
        name = plugin_dir.name
        if (skills_dir / "SPEC.md").exists():
            report(
                results,
                "PASS",
                "vsa-coverage",
                f"plugins/{name}: skills/SPEC.md covers subsystem",
            )
        else:
            report(results, "FAIL", "vsa-coverage", f"plugins/{name}/skills/ has no SPEC.md")


def check_tool_health(results: Results, project_root: Path) -> None:
    # uv
    if shutil.which("uv"):
        try:
            ver = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report(results, "PASS", "tool-health", f"uv: {ver}")
        except subprocess.CalledProcessError:
            report(results, "FAIL", "tool-health", "uv: error running uv --version")
    else:
        report(
            results,
            "FAIL",
            "tool-health",
            "uv: not installed (required — curl -LsSf https://astral.sh/uv/install.sh | sh)",
        )

    # git
    if shutil.which("git"):
        try:
            ver = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report(results, "PASS", "tool-health", f"git: {ver}")
        except subprocess.CalledProcessError:
            report(results, "FAIL", "tool-health", "git: error running git --version")
    else:
        report(results, "FAIL", "tool-health", "git: not installed")

    # gh
    if shutil.which("gh"):
        try:
            ver = subprocess.run(
                ["gh", "--version"], capture_output=True, text=True, check=True
            ).stdout.splitlines()[0]
            auth = subprocess.run(
                ["gh", "auth", "status"], capture_output=True, text=True
            ).returncode
            status = "authenticated" if auth == 0 else "not authenticated"
            report(results, "PASS" if auth == 0 else "WARN", "tool-health", f"gh: {ver} ({status})")
        except subprocess.CalledProcessError:
            report(results, "WARN", "tool-health", "gh: error checking version")
    else:
        report(results, "WARN", "tool-health", "gh: not installed (optional)")

    # jq (required for plansDirectory resolution)
    if shutil.which("jq"):
        try:
            ver = subprocess.run(
                ["jq", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report(results, "PASS", "tool-health", f"jq: {ver}")
        except subprocess.CalledProcessError:
            report(results, "PASS", "tool-health", "jq: installed (version unknown)")
    else:
        report(results, "WARN", "tool-health", "jq: not installed (required for plansDirectory resolution)")

    # bd (beads)
    if shutil.which("bd"):
        try:
            ver = subprocess.run(
                ["bd", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report(results, "PASS", "tool-health", f"bd: {ver}")
        except subprocess.CalledProcessError:
            report(results, "PASS", "tool-health", "bd: installed (version unknown)")
    else:
        report(results, "WARN", "tool-health", "bd: not installed (optional)")


def check_issue_tracking(results: Results, project_root: Path) -> None:
    try:
        branch = subprocess.run(
            ["git", "-C", str(project_root), "branch", "--show-current"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    except FileNotFoundError:
        branch = ""

    if not branch or branch in ("main", "master"):
        msg = f"On {branch or 'detached HEAD'} — issue tracking not applicable"
        report(results, "WARN", "issue-tracking", msg)
        return

    # Check for GitHub issue via PR
    try:
        pr_url = subprocess.run(
            ["gh", "pr", "view", "--json", "url", "-q", ".url"],
            capture_output=True,
            text=True,
            cwd=project_root,
        ).stdout.strip()
    except FileNotFoundError:
        pr_url = ""

    if pr_url:
        try:
            pr_body = subprocess.run(
                ["gh", "pr", "view", "--json", "body", "-q", ".body"],
                capture_output=True,
                text=True,
                cwd=project_root,
            ).stdout.strip()
        except FileNotFoundError:
            pr_body = ""

        if re.search(r"(closes|fixes|resolves)\s+#\d+", pr_body, re.IGNORECASE):
            report(results, "PASS", "issue-tracking", "PR links to GitHub issue")
        else:
            report(
                results,
                "WARN",
                "issue-tracking",
                "PR exists but no issue linkage found in body",
            )
    else:
        report(results, "WARN", "issue-tracking", f"No PR found for branch {branch}")

    # Check beads if available
    if shutil.which("bd") and (project_root / ".beads").is_dir():
        try:
            result = subprocess.run(
                ["bd", "list", "--status=in_progress", "--json"],
                capture_output=True,
                text=True,
                cwd=project_root,
            )
            output = result.stdout.strip()
            if output and output != "[]":
                report(results, "PASS", "issue-tracking", "Beads issues found for in-progress work")
            else:
                report(results, "WARN", "issue-tracking", "No in-progress beads issues found")
        except FileNotFoundError:
            pass


# ── Check: cross-links ───────────────────────────────────────────────


def _extract_dependency_paths(tokens: list[Any]) -> list[str]:
    """Extract file paths from SPEC.md Dependencies table (third column).

    Only examines tables within a ``## Dependencies`` section. Looks for
    code_inline tokens (backtick-wrapped paths) in the third column of
    table body rows.  N/A entries are plain text, not code spans.
    """
    paths: list[str] = []
    in_deps_section = False
    in_tbody = False
    td_index = 0

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Track which section we're in via headings
        if token.type == "heading_open":
            level = token.tag  # "h1", "h2", etc.
            # Look ahead for the heading text
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                heading_text = tokens[i + 1].content.strip()
                if level == "h2" and heading_text == "Dependencies":
                    in_deps_section = True
                elif level in ("h1", "h2"):
                    # Any other h1/h2 ends the Dependencies section
                    in_deps_section = False

        if in_deps_section:
            if token.type == "tbody_open":
                in_tbody = True
            elif token.type == "tbody_close":
                in_tbody = False
            elif token.type == "tr_open":
                td_index = 0
            elif in_tbody and token.type == "td_open":
                td_index += 1
            elif in_tbody and token.type == "inline" and td_index == 3 and token.children:
                for child in token.children:
                    if child.type == "code_inline" and child.content.strip():
                        paths.append(child.content.strip())

        i += 1

    return paths


def check_cross_links(results: Results, project_root: Path) -> None:
    """Validate that paths referenced in SPEC.md Dependencies tables exist."""
    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        report(results, "WARN", "cross-links", "No plugins/ directory found")
        return

    spec_files = sorted(plugins_dir.rglob("skills/SPEC.md"))
    if not spec_files:
        report(results, "WARN", "cross-links", "No SPEC.md files found")
        return

    found_any = False
    for spec in spec_files:
        rel = spec.relative_to(project_root)
        tokens = parse_md(spec)
        dep_paths = _extract_dependency_paths(tokens)

        for dep_path in dep_paths:
            found_any = True
            target = project_root / dep_path
            if target.exists():
                report(results, "PASS", "cross-links", f"{rel}: {dep_path} exists")
            else:
                report(results, "FAIL", "cross-links", f"{rel}: {dep_path} not found")

    if not found_any:
        report(results, "WARN", "cross-links", "No cross-link paths found in Dependencies tables")


# ── Check: doc-stats ─────────────────────────────────────────────────

# Stat check registry: each function takes (project_root, plugin_dir) and
# returns the actual integer value. plugin_dir is the plugin containing the
# markdown file with the footnote, or None for project-level docs.


def _stat_total_test_count(project_root: Path, plugin_dir: Path | None) -> int:
    """Count total tests using pytest --collect-only (sub-second, no execution)."""
    test_dir = (plugin_dir or project_root) / "tests"
    if not test_dir.exists():
        return 0
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "--project",
                str(plugin_dir or project_root),
                "pytest",
                "--collect-only",
                "-q",
                str(test_dir),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Last meaningful line: "N tests collected" or "N test collected"
        for line in reversed(result.stdout.splitlines()):
            m = re.match(r"(\d+) tests? collected", line.strip())
            if m:
                return int(m.group(1))
    except (subprocess.TimeoutExpired, OSError):
        pass
    return 0


def _stat_test_suite_count(project_root: Path, plugin_dir: Path | None) -> int:
    """Count number of test modules (test_*.py files)."""
    test_dir = (plugin_dir or project_root) / "tests"
    if not test_dir.exists():
        return 0
    return len(list(test_dir.glob("test_*.py")))


def _stat_skill_count(project_root: Path, plugin_dir: Path | None) -> int:
    """Count number of SKILL.md files in a plugin."""
    skills_dir = (plugin_dir or project_root) / "skills"
    if not skills_dir.exists():
        return 0
    return len(list(skills_dir.rglob("SKILL.md")))


STAT_CHECKS: dict[str, Callable[[Path, Path | None], int]] = {
    "total-test-count": _stat_total_test_count,
    "test-suite-count": _stat_test_suite_count,
    "skill-count": _stat_skill_count,
}


def _extract_stat_refs(tokens: list[Any]) -> list[tuple[str, int, str]]:
    """Extract stat-check footnote references from parsed tokens.

    Returns list of (label, claimed_number, check_name) tuples.
    """
    # Build footnote label -> check name mapping from footnote definitions
    label_to_check: dict[str, str] = {}
    in_footnote: str | None = None
    for token in tokens:
        if token.type == "footnote_open" and token.meta:
            in_footnote = token.meta.get("label", "")
        elif token.type == "footnote_close":
            in_footnote = None
        elif in_footnote and token.type == "inline":
            m = re.match(r"stat-check:\s*(\S+)", token.content.strip())
            if m:
                label_to_check[in_footnote] = m.group(1)

    if not label_to_check:
        return []

    # Find footnote refs and extract the number from preceding text
    refs: list[tuple[str, int, str]] = []
    for token in tokens:
        if token.type != "inline" or not token.children:
            continue
        for i, child in enumerate(token.children):
            if child.type != "footnote_ref":
                continue
            label = child.meta.get("label", "") if child.meta else ""
            if label not in label_to_check:
                continue
            # Look backward for the nearest number in preceding text children
            number = None
            for j in range(i - 1, -1, -1):
                sib = token.children[j]
                if sib.content:
                    nums = re.findall(r"\d+", sib.content)
                    if nums:
                        number = int(nums[-1])
                        break
            if number is not None:
                refs.append((label, number, label_to_check[label]))

    return refs


def _find_plugin_for_file(filepath: Path, project_root: Path) -> Path | None:
    """Find the plugin directory containing a file, or None."""
    plugins_dir = project_root / "plugins"
    try:
        rel = filepath.relative_to(plugins_dir)
        return plugins_dir / rel.parts[0]
    except (ValueError, IndexError):
        return None


def check_doc_stats(results: Results, project_root: Path) -> None:
    """Validate stat-check footnotes in markdown files."""
    md_files = sorted(project_root.rglob("*.md"))
    # Exclude hidden dirs, node_modules, .venv
    md_files = [
        f
        for f in md_files
        if not any(
            part.startswith(".") or part in ("node_modules", "__pycache__")
            for part in f.relative_to(project_root).parts
        )
    ]

    found_any = False
    for md_file in md_files:
        try:
            tokens = parse_md(md_file)
        except (OSError, UnicodeDecodeError):
            continue

        refs = _extract_stat_refs(tokens)
        if not refs:
            continue

        found_any = True
        rel = md_file.relative_to(project_root)
        plugin_dir = _find_plugin_for_file(md_file, project_root)

        for label, claimed, check_name in refs:
            if check_name not in STAT_CHECKS:
                report(
                    results,
                    "FAIL",
                    "doc-stats",
                    f"{rel}: unknown stat-check '{check_name}' in [^{label}]",
                )
                continue

            actual = STAT_CHECKS[check_name](project_root, plugin_dir)
            if claimed == actual:
                report(results, "PASS", "doc-stats", f"{rel}: [^{label}] {check_name} = {actual}")
            else:
                report(
                    results,
                    "WARN",
                    "doc-stats",
                    f"{rel}: [^{label}] {check_name} claims {claimed}, actual {actual}",
                )

    if not found_any:
        report(results, "WARN", "doc-stats", "No stat-check footnotes found in any markdown files")


# ── Main ─────────────────────────────────────────────────────────────

CHECKS: dict[str, Callable[[Results, Path], None]] = {
    "inv-numbering": check_inv_numbering,
    "issue-tracking": check_issue_tracking,
    "skill-structure": check_skill_structure,
    "doc-structure": check_doc_structure,
    "vsa-coverage": check_vsa_coverage,
    "cross-links": check_cross_links,
    "tool-health": check_tool_health,
    "doc-stats": check_doc_stats,
}

ALL_CHECKS_ORDER: list[str] = [
    "inv-numbering",
    "skill-structure",
    "doc-structure",
    "vsa-coverage",
    "cross-links",
    "doc-stats",
    "tool-health",
    "issue-tracking",
]


def detect_project_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path.cwd()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="quality-gate",
        description="Structural validation for dev-workflow-toolkit projects",
    )
    parser.add_argument("--check", choices=list(CHECKS.keys()), help="Run a specific check only")
    parser.add_argument("--path", type=Path, help="Project root (default: git toplevel)")
    args = parser.parse_args()

    project_root = args.path or detect_project_root()
    project_root = project_root.resolve()

    print(f"quality-gate: running structural checks against {project_root}")
    print()

    results = Results()

    if args.check:
        CHECKS[args.check](results, project_root)
    else:
        for name in ALL_CHECKS_ORDER:
            CHECKS[name](results, project_root)

    print()
    if results.failures == 0:
        print(f"{GREEN}quality-gate: all {results.checks} checks passed{NC}")
        sys.exit(0)
    else:
        print(f"{RED}quality-gate: {results.failures} of {results.checks} checks failed{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
