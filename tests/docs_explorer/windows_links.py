from __future__ import annotations

import os
import subprocess
from pathlib import Path


def create_directory_alias(link: Path, target: Path, *, dangling: bool = False) -> str:
    """Create an unprivileged directory alias: junction on Windows, symlink on POSIX."""
    link = Path(link)
    target = Path(target)
    if os.name == "nt":
        target.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            [os.environ["ComSpec"], "/d", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True, text=True, encoding="utf-8", timeout=5, check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr or result.stdout)
        if dangling:
            target.rmdir()
        return "junction"
    if dangling:
        link.symlink_to(target, target_is_directory=True)
    else:
        target.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target, target_is_directory=True)
    return "symlink"


def remove_test_path(path: Path) -> None:
    path = Path(path)
    if not path.exists() and not path.is_symlink():
        return
    try:
        if path.is_dir() and not path.is_symlink():
            path.rmdir()
        else:
            path.unlink()
    except FileNotFoundError:
        pass
