import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
        cwd=Path(__file__).parent,
    )
    return Path(result.stdout.strip())


@pytest.fixture(scope="session")
def plugin_root(repo_root: Path) -> Path:
    return repo_root / "plugins" / "dev-workflow-toolkit"


@pytest.fixture(scope="session")
def skills_dir(plugin_root: Path) -> Path:
    return plugin_root / "skills"


@pytest.fixture(scope="session")
def skill_mds(skills_dir: Path) -> list[Path]:
    return sorted(skills_dir.rglob("SKILL.md"))
