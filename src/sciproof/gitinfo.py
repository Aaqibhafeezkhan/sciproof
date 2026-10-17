"""Best-effort Git metadata. Missing git or a non-repository is not an error."""

from __future__ import annotations

import subprocess  # noqa: S404
from pathlib import Path
from typing import Any

_TIMEOUT_SECONDS = 15


def _git(cwd: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout


def git_info(cwd: Path) -> dict[str, Any] | None:
    """Return ``{"commit", "branch", "dirty"}`` or ``None`` outside of a Git repository.

    Remote URLs are intentionally not recorded because they can contain credentials.
    ``dirty`` is true when there are uncommitted or untracked changes.
    """
    commit = _git(cwd, "rev-parse", "HEAD")
    if commit is None:
        return None
    status = _git(cwd, "status", "--porcelain")
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    return {
        "commit": commit.strip(),
        "branch": branch.strip() if branch else None,
        "dirty": bool(status and status.strip()),
    }
