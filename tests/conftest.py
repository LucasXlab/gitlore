import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args} failed: {result.stderr}")
    return result.stdout


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "dev@example.com")
    _git(repo, "config", "user.name", "Dev One")

    # file a.py touched many times -> high churn
    (repo / "a.py").write_text("def f():\n    return 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init a")

    for i in range(5):
        prev = (repo / "a.py").read_text()
        (repo / "a.py").write_text(prev + f"\n# change {i}\n")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", f"update a {i}")

    # file b.py touched once -> low churn
    (repo / "b.py").write_text(
        "def g(x):\n    if x > 0:\n        return x\n    else:\n        return 0\n"
    )
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "add b")

    return repo
