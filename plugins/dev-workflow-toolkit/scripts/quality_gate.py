#!/usr/bin/env python3
"""Quality gate: structural validation for dev-workflow-toolkit projects.

Uses markdown-it-py to parse SPEC.md and SKILL.md files structurally
rather than relying on brittle regex patterns.

Usage:
    quality-gate.py [--check <name>] [--path <project-root>]
    quality-gate.py --help

Checks: inv-numbering, issue-tracking, skill-structure, doc-structure,
        vsa-coverage, tool-health
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.front_matter import front_matter_plugin

# ── Colors ───────────────────────────────────────────────────────────

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
NC = "\033[0m"

# ── Reporting ────────────────────────────────────────────────────────

failures = 0
checks = 0


def report(status: str, check: str, detail: str) -> None:
    global failures, checks
    checks += 1
    if status == "PASS":
        print(f"{GREEN}✓{NC} [{check}] {detail}")
    elif status == "WARN":
        print(f"{YELLOW}!{NC} [{check}] {detail}")
    else:
        print(f"{RED}✗{NC} [{check}] {detail}")
        failures += 1


# ── Markdown parsing helpers ─────────────────────────────────────────


def parse_md(path: Path) -> list:
    """Parse a markdown file into tokens using markdown-it-py."""
    md = MarkdownIt().enable("table")
    front_matter_plugin(md)
    return md.parse(path.read_text(encoding="utf-8"))


def extract_frontmatter(tokens: list) -> dict[str, str]:
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


def has_frontmatter(tokens: list) -> bool:
    return any(t.type == "front_matter" for t in tokens)


def extract_table_first_column_ids(tokens: list, prefix: str) -> list[int]:
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


def extract_list_item_ids(tokens: list, prefix: str) -> list[int]:
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


def extract_definition_ids(tokens: list, prefix: str) -> list[int]:
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


def check_inv_numbering(project_root: Path) -> None:
    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        report("WARN", "inv-numbering", "No plugins/ directory found")
        return

    spec_files = sorted(plugins_dir.rglob("skills/SPEC.md"))
    if not spec_files:
        report("WARN", "inv-numbering", "No SPEC.md files found")
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
                report("FAIL", "inv-numbering", f"{rel}: duplicate definitions: {dupe_str}")
                continue

            # Check sequential from 1
            unique = sorted(set(ids))
            ok = True
            for expected, actual in enumerate(unique, start=1):
                if actual != expected:
                    report(
                        "FAIL",
                        "inv-numbering",
                        f"{rel}: {prefix}-{actual} found, expected {prefix}-{expected}",
                    )
                    ok = False
                    break

            if ok:
                report(
                    "PASS",
                    "inv-numbering",
                    f"{rel}: {prefix}-1 through {prefix}-{len(unique)} sequential, no duplicates",
                )


def check_skill_structure(project_root: Path) -> None:
    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        report("WARN", "skill-structure", "No plugins/ directory found")
        return

    skill_files = sorted(plugins_dir.rglob("SKILL.md"))
    if not skill_files:
        report("WARN", "skill-structure", "No SKILL.md files found")
        return

    names_seen: set[str] = set()

    for skill_file in skill_files:
        rel = skill_file.relative_to(project_root)
        dir_name = skill_file.parent.name
        tokens = parse_md(skill_file)

        # Check frontmatter exists
        if not has_frontmatter(tokens):
            report("FAIL", "skill-structure", f"{rel}: missing YAML frontmatter")
            continue

        fm = extract_frontmatter(tokens)

        # Check name
        skill_name = fm.get("name", "")
        if not skill_name:
            report("FAIL", "skill-structure", f"{rel}: missing 'name' in frontmatter")
            continue

        if skill_name != dir_name:
            report(
                "FAIL",
                "skill-structure",
                f"{rel}: name '{skill_name}' doesn't match directory '{dir_name}'",
            )
            continue

        if not re.match(r"^[a-z][a-z0-9-]*$", skill_name):
            report(
                "FAIL",
                "skill-structure",
                f"{rel}: name '{skill_name}' not lowercase-hyphenated",
            )
            continue

        if len(skill_name) > 64:
            report("FAIL", "skill-structure", f"{rel}: name '{skill_name}' exceeds 64 chars")
            continue

        # Check description
        if "description" not in fm:
            report("FAIL", "skill-structure", f"{rel}: missing 'description' in frontmatter")
            continue

        # Check uniqueness
        if skill_name in names_seen:
            report("FAIL", "skill-structure", f"{rel}: duplicate name '{skill_name}'")
            continue
        names_seen.add(skill_name)

        report("PASS", "skill-structure", f"{rel}: valid ({skill_name})")


def check_doc_structure(project_root: Path) -> None:
    for doc in ("README.md", "docs/ARCHITECTURE.md", "docs/DESIGN.md"):
        path = project_root / doc
        if path.exists():
            report("PASS", "doc-structure", f"{doc} exists")
        else:
            report("WARN", "doc-structure", f"{doc} missing (recommended)")

    plugins_dir = project_root / "plugins"
    if not plugins_dir.exists():
        return

    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        spec = plugin_dir / "skills" / "SPEC.md"
        name = plugin_dir.name
        if spec.exists():
            report("PASS", "doc-structure", f"plugins/{name}/skills/SPEC.md exists")
        else:
            report("FAIL", "doc-structure", f"plugins/{name}/skills/SPEC.md missing")


def check_vsa_coverage(project_root: Path) -> None:
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
            report("PASS", "vsa-coverage", f"plugins/{name}: skills/SPEC.md covers subsystem")
        else:
            report("FAIL", "vsa-coverage", f"plugins/{name}/skills/ has no SPEC.md")


def check_tool_health(project_root: Path) -> None:
    # uv
    if shutil.which("uv"):
        try:
            ver = subprocess.run(
                ["uv", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report("PASS", "tool-health", f"uv: {ver}")
        except subprocess.CalledProcessError:
            report("FAIL", "tool-health", "uv: error running uv --version")
    else:
        report("FAIL", "tool-health", "uv: not installed (required — curl -LsSf https://astral.sh/uv/install.sh | sh)")

    # git
    if shutil.which("git"):
        try:
            ver = subprocess.run(
                ["git", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report("PASS", "tool-health", f"git: {ver}")
        except subprocess.CalledProcessError:
            report("FAIL", "tool-health", "git: error running git --version")
    else:
        report("FAIL", "tool-health", "git: not installed")

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
            report("PASS" if auth == 0 else "WARN", "tool-health", f"gh: {ver} ({status})")
        except subprocess.CalledProcessError:
            report("WARN", "tool-health", "gh: error checking version")
    else:
        report("WARN", "tool-health", "gh: not installed (optional)")

    # bd (beads)
    if shutil.which("bd"):
        try:
            ver = subprocess.run(
                ["bd", "--version"], capture_output=True, text=True, check=True
            ).stdout.strip()
            report("PASS", "tool-health", f"bd: {ver}")
        except subprocess.CalledProcessError:
            report("PASS", "tool-health", "bd: installed (version unknown)")
    else:
        report("WARN", "tool-health", "bd: not installed (optional)")


def check_issue_tracking(project_root: Path) -> None:
    try:
        branch = subprocess.run(
            ["git", "-C", str(project_root), "branch", "--show-current"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    except FileNotFoundError:
        branch = ""

    if not branch or branch in ("main", "master"):
        report("WARN", "issue-tracking", f"On {branch or 'detached HEAD'} — issue tracking not applicable")
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
            report("PASS", "issue-tracking", "PR links to GitHub issue")
        else:
            report("WARN", "issue-tracking", "PR exists but no issue linkage found in body")
    else:
        report("WARN", "issue-tracking", f"No PR found for branch {branch}")

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
                report("PASS", "issue-tracking", "Beads issues found for in-progress work")
            else:
                report("WARN", "issue-tracking", "No in-progress beads issues found")
        except FileNotFoundError:
            pass


# ── Main ─────────────────────────────────────────────────────────────

CHECKS = {
    "inv-numbering": check_inv_numbering,
    "issue-tracking": check_issue_tracking,
    "skill-structure": check_skill_structure,
    "doc-structure": check_doc_structure,
    "vsa-coverage": check_vsa_coverage,
    "tool-health": check_tool_health,
}

ALL_CHECKS_ORDER = [
    "inv-numbering",
    "skill-structure",
    "doc-structure",
    "vsa-coverage",
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
    global failures, checks

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

    if args.check:
        CHECKS[args.check](project_root)
    else:
        for name in ALL_CHECKS_ORDER:
            CHECKS[name](project_root)

    print()
    if failures == 0:
        print(f"{GREEN}quality-gate: all {checks} checks passed{NC}")
        sys.exit(0)
    else:
        print(f"{RED}quality-gate: {failures} of {checks} checks failed{NC}")
        sys.exit(1)


if __name__ == "__main__":
    main()
