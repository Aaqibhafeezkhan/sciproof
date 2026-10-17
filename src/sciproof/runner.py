"""Run a command without a shell and collect its output."""

from __future__ import annotations

import subprocess  # noqa: S404
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sciproof.errors import SciProofError
from sciproof.hashing import sha256_bytes


class CommandNotRunnable(SciProofError):
    """The command could not be started (not found, not executable, bad working directory)."""


class CommandTimeout(SciProofError):
    """The command did not finish within the allowed time."""


class CommandInterrupted(SciProofError):
    """The user interrupted the command (Ctrl+C)."""


@dataclass
class ExecResult:
    exit_code: int
    stdout: bytes
    stderr: bytes
    duration_seconds: float


def run_command(argv: list[str], cwd: Path, timeout: float | None) -> ExecResult:
    """Run ``argv`` (never through a shell) in ``cwd`` with the current user's permissions.

    Standard input is closed so that the command can never wait for terminal input.
    """
    started = time.monotonic()
    try:
        completed = subprocess.run(  # noqa: S603
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimeout(f"command did not finish within {timeout} seconds") from exc
    except KeyboardInterrupt as exc:
        raise CommandInterrupted("interrupted by the user") from exc
    except OSError as exc:
        raise CommandNotRunnable(f"cannot start {argv[0]!r}: {exc.strerror or exc}") from exc
    return ExecResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.monotonic() - started,
    )


def summarize_stream(data: bytes, max_bytes: int) -> dict[str, Any]:
    """Describe captured output: hash of everything, text of (at most) the first ``max_bytes``."""
    kept = data[:max_bytes]
    return {
        "sha256": sha256_bytes(data),
        "size": len(data),
        "truncated": len(data) > max_bytes,
        "text": kept.decode("utf-8", errors="replace"),
    }
