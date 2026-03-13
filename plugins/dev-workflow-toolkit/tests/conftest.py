import os
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


@pytest.fixture(scope="session")
def plugins_dir(repo_root: Path) -> Path:
    return repo_root / "plugins"


@pytest.fixture(scope="session")
def all_plugin_dirs(plugins_dir: Path) -> list[Path]:
    return sorted(d for d in plugins_dir.iterdir() if d.is_dir())


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "capability(name): mark test as requiring a specific resource capability (e.g., gpu, ollama)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    raw = os.environ.get("CI_CAPABILITIES", "")
    available = set(raw.split()) if raw.strip() else set()
    for item in items:
        for marker in item.iter_markers("capability"):
            required = marker.args[0]
            if required not in available:
                item.add_marker(
                    pytest.mark.skip(reason=f"Requires capability: {required}")
                )
