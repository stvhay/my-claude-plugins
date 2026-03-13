"""Parse plan markdown and create beads issues from ### Task N: headings.

Uses markdown-it-py to properly parse markdown, skipping code fences
and other block-level constructs. Replaces `bd create -f` which uses
h2 headings and doesn't skip code fences.
"""

import argparse
import re
import subprocess
import sys

from markdown_it import MarkdownIt


def parse_tasks(plan_path: str) -> list[dict]:
    """Extract tasks from ### Task N: headings in a plan file."""
    text = open(plan_path).read()
    md = MarkdownIt()
    tokens = md.parse(text)

    tasks = []
    expect_heading_content = False

    for token in tokens:
        if token.type == "heading_open" and token.tag == "h3":
            expect_heading_content = True
            continue

        if expect_heading_content and token.type == "inline":
            expect_heading_content = False
            m = re.match(r"Task\s+(\d+):\s*(.*)", token.content)
            if m:
                tasks.append({
                    "number": int(m.group(1)),
                    "title": m.group(2).strip(),
                    "deps": [],
                })
            continue

        if expect_heading_content:
            expect_heading_content = False

        # Look for **Depends on:** in paragraph content within a task
        if token.type == "inline" and tasks:
            m = re.search(r"\*\*Depends\s+on:\*\*\s*(.*)", token.content)
            if m:
                dep_text = m.group(1)
                if not re.search(r"[Ii]ndependent", dep_text):
                    dep_nums = [int(x) for x in re.findall(r"Task\s+(\d+)", dep_text)]
                    tasks[-1]["deps"] = dep_nums

    return tasks


def run_bd(args: list[str], dry_run: bool) -> str:
    """Run a bd command, returning stdout. In dry-run mode, print and return placeholder."""
    if dry_run:
        print(f"  [dry-run] bd {' '.join(args)}")
        return ""
    result = subprocess.run(["bd", *args], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  error: bd {' '.join(args)}: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Create beads issues from a plan's ### Task N: headings."
    )
    parser.add_argument("plan_file", help="Path to plan markdown file")
    parser.add_argument("--parent", help="Parent beads issue ID")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created")
    args = parser.parse_args()

    tasks = parse_tasks(args.plan_file)

    if not tasks:
        print(f"error: no ### Task N: headings found in {args.plan_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(tasks)} task(s) in {args.plan_file}")

    # Create issues, tracking task-number -> beads-id
    task_to_bead: dict[int, str] = {}

    for task in tasks:
        cmd = ["create", task["title"], "--type", "task", "--silent"]
        if args.parent:
            cmd.extend(["--parent", args.parent])

        if args.dry_run:
            label = f'bd create "{task["title"]}" --type task'
            if args.parent:
                label += f" --parent {args.parent}"
            print(f"  [dry-run] {label}")
            task_to_bead[task["number"]] = f"dry-run-{task['number']}"
        else:
            bead_id = run_bd(cmd, dry_run=False)
            task_to_bead[task["number"]] = bead_id
            print(f"  Task {task['number']}: {task['title']} -> {bead_id}")

    # Wire up dependencies
    for task in tasks:
        if not task["deps"]:
            continue
        task_bead = task_to_bead.get(task["number"], "")
        for dep_num in task["deps"]:
            dep_bead = task_to_bead.get(dep_num)
            if not dep_bead:
                print(
                    f"  warning: Task {task['number']} depends on Task {dep_num} "
                    f"but Task {dep_num} was not found",
                    file=sys.stderr,
                )
                continue
            if args.dry_run:
                print(
                    f"  [dry-run] bd dep add {task_bead} {dep_bead}  "
                    f"(Task {task['number']} blocks-on Task {dep_num})"
                )
            else:
                run_bd(["dep", "add", task_bead, dep_bead], dry_run=False)
                print(
                    f"  dep: Task {task['number']} ({task_bead}) "
                    f"blocks-on Task {dep_num} ({dep_bead})"
                )

    print("Done.")


if __name__ == "__main__":
    main()
