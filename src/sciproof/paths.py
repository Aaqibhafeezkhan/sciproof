"""Path handling.

Manifests are untrusted input, so every path read from one is validated before it is used.
Paths in a manifest are always relative, use ``/`` as separator and must stay inside the
directory that contains the manifest (the *base directory*).
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from sciproof.errors import UnsafePathError


def validate_relative_path(value: object, *, allow_dot: bool = False) -> str:
    """Check that ``value`` is a safe relative path string and return it unchanged."""
    if not isinstance(value, str) or not value:
        raise UnsafePathError(f"path must be a non-empty string, got {value!r}")
    if "\x00" in value:
        raise UnsafePathError("path contains a NUL byte")
    if "\\" in value:
        raise UnsafePathError(f"path {value!r} contains a backslash; use '/' as separator")
    if value == ".":
        if allow_dot:
            return value
        raise UnsafePathError("path '.' is not a file")
    if PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute():
        raise UnsafePathError(f"path {value!r} is absolute")
    if PureWindowsPath(value).drive:
        raise UnsafePathError(f"path {value!r} has a drive letter")
    parts = value.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise UnsafePathError(f"path {value!r} contains empty, '.' or '..' components")
    return value


def resolve_inside(base: Path, relative: str) -> Path:
    """Resolve ``relative`` below ``base``, refusing anything that escapes it.

    Symbolic links are followed before the check, so a link that points outside ``base``
    is rejected too.
    """
    validate_relative_path(relative)
    base_resolved = base.resolve()
    candidate = (base_resolved / relative).resolve()
    if not candidate.is_relative_to(base_resolved):
        raise UnsafePathError(f"path {relative!r} resolves outside of {base_resolved}")
    return candidate


def to_manifest_path(base: Path, user_path: str | Path) -> str:
    """Convert a path given on the command line to a safe manifest path (relative to ``base``)."""
    base_resolved = base.resolve()
    raw = Path(user_path)
    candidate = (raw if raw.is_absolute() else base_resolved / raw).resolve()
    if not candidate.is_relative_to(base_resolved):
        raise UnsafePathError(
            f"{str(user_path)!r} is outside of the working directory {base_resolved}"
        )
    relative = candidate.relative_to(base_resolved).as_posix()
    return validate_relative_path(relative)
