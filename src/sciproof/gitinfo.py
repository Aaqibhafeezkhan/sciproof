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


def _is_sciproof_artifact(path: str) -> bool:
    """Files SciProof itself writes next to the experiment never count as code changes."""
    parts = path.replace("\\", "/").split("/")
    return any(
        part.endswith((".sciproof.json", ".sciproof.json.sig", ".sciproof.d"))
        or part.startswith(".sciproof-rerun-")
        for part in parts
    )


def _is_dirty(status: str | None) -> bool:
    """Whether ``git status --porcelain=v1 -z`` output shows changes outside SciProof's files.

    If the status cannot be read the tree is reported as dirty: "clean" must never be claimed
    without evidence.
    """
    if status is None:
        return True
    entries = status.split("\x00")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if len(entry) < 4:
            continue
        paths = [entry[3:]]
        if entry[0] in "RC":  # renames and copies are followed by the original path
            paths.append(entries[index] if index < len(entries) else "")
            index += 1
        if not all(_is_sciproof_artifact(path) for path in paths if path):
            return True
    return False


def git_info(cwd: Path) -> dict[str, Any] | None:
    """Return ``{"commit", "branch", "dirty"}`` or ``None`` outside of a Git repository.

    Remote URLs are intentionally not recorded because they can contain credentials.
    ``dirty`` is true when there are uncommitted or untracked changes, ignoring the manifests,
    snapshots and rerun directories that SciProof writes itself.
    """
    commit = _git(cwd, "rev-parse", "HEAD")
    if commit is None:
        return None
    status = _git(cwd, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    branch = _git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    return {
        "commit": commit.strip(),
        "branch": branch.strip() if branch else None,
        "dirty": _is_dirty(status),
    }
