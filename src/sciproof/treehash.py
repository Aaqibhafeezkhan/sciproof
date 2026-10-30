"""Directories as evidence: a sorted list of the regular files below a directory, and one digest.

A directory is described by every regular file inside it, as ``(relative path, SHA-256, size)``,

sorted by the UTF-8 bytes of the path. The *tree digest* is the SHA-256 of the lines

    <file sha256>  <size>  <relative path>\\n

in that order (two spaces between the fields, paths separated by ``/``). Empty directories are

not recorded, because they contain no file whose content could be compared.

Symbolic links, devices, sockets and other special files are **refused** instead of followed or

skipped: following them can leave the directory, and skipping them would let a change go

unnoticed. File names that cannot mean the same thing on every system (a backslash, a control

character, a Windows reserved name such as ``aux.txt``, a trailing dot or space, a name that is

not valid UTF-8) are refused as well, by the same rules as any path in a manifest. A tree is

limited to ``MAX_TREE_FILES`` files so that a manifest stays small and a scan stays quick.

"""

from __future__ import annotations

import concurrent.futures
import hashlib
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sciproof.errors import SciProofError, UnsafePathError
from sciproof.hashing import sha256_file
from sciproof.paths import validate_relative_path

MAX_TREE_FILES = 10_000

MAX_NAMES_IN_DETAIL = 10


class TreeError(SciProofError):
    """A directory cannot be described as evidence (symlink, special file, too many files, ...)."""


@dataclass(frozen=True)
class FileEntry:
    path: str  # relative to the directory, '/'-separated

    sha256: str

    size: int

    def to_dict(self) -> dict[str, Any]:

        return {"path": self.path, "sha256": self.sha256, "size": self.size}


def _sort_key(path: str) -> bytes:

    return path.encode("utf-8")


def scan_tree(root: Path, *, limit: int = MAX_TREE_FILES) -> list[FileEntry]:
    """Hash every regular file below ``root`` (sorted). Raises ``TreeError`` for anything else.

    ``root`` must already have been checked to lie inside the project (``paths.resolve_inside``).

    Links inside the tree are never followed.

    """

    stack: list[tuple[Path, str]] = [(root, "")]

    files_to_hash: list[tuple[Path, str]] = []

    while stack:
        directory, prefix = stack.pop()

        try:
            with os.scandir(directory) as iterator:
                children = sorted(iterator, key=lambda entry: entry.name)

        except OSError as exc:
            raise TreeError(
                f"cannot read directory {prefix or '.'}: {exc.strerror or exc}"
            ) from exc

        for child in children:
            relative = f"{prefix}{child.name}"

            try:
                # the same rules as every path in a manifest, so that what is scanned can be written

                validate_relative_path(relative)

            except UnsafePathError as exc:
                raise TreeError(f"cannot record {relative!r}: {exc}") from None

            try:
                child.name.encode("utf-8")

            except UnicodeEncodeError:
                raise TreeError(f"unsupported file name {relative!r}: not valid UTF-8") from None

            if child.is_symlink():
                raise TreeError(
                    f"{relative!r} is a symbolic link; links inside a declared directory are not "
                    "supported (declare the real files instead)"
                )

            if child.is_dir(follow_symlinks=False):
                stack.append((Path(child.path), f"{relative}/"))

            elif child.is_file(follow_symlinks=False):
                if len(files_to_hash) >= limit:
                    raise TreeError(
                        f"the directory has more than {limit} files; declare a smaller "
                        "directory or the individual files that matter"
                    )

                files_to_hash.append((Path(child.path), relative))

            else:
                raise TreeError(f"{relative!r} is not a regular file or directory")

    if not files_to_hash:
        return []

    def _hash_worker(item: tuple[Path, str]) -> FileEntry:

        p, rel = item

        try:
            digest, size = sha256_file(p)

        except OSError as exc:
            raise TreeError(f"cannot read {rel!r}: {exc.strerror or exc}") from exc

        return FileEntry(rel, digest, size)

    if len(files_to_hash) >= 16:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
            entries = list(pool.map(_hash_worker, files_to_hash))

    else:
        entries = [_hash_worker(item) for item in files_to_hash]

    return sorted(entries, key=lambda entry: _sort_key(entry.path))


def _fields(entry: FileEntry | Mapping[str, Any]) -> tuple[str, str, int]:

    if isinstance(entry, FileEntry):
        return entry.path, entry.sha256, entry.size

    return entry["path"], entry["sha256"], entry["size"]


def tree_digest(entries: Iterable[FileEntry | Mapping[str, Any]]) -> str:
    """The tree digest of ``entries`` (in any order; it sorts them)."""

    ordered = sorted((_fields(e) for e in entries), key=lambda fields: _sort_key(fields[0]))

    digest = hashlib.sha256()

    for path, sha256, size in ordered:
        digest.update(f"{sha256}  {size}  {path}\n".encode())

    return digest.hexdigest()


def tree_size(entries: Iterable[FileEntry | Mapping[str, Any]]) -> int:

    return sum(_fields(e)[2] for e in entries)


def tree_record(entries: list[FileEntry]) -> dict[str, Any]:
    """The manifest fields that describe a directory: ``sha256``, ``size`` and ``files``."""

    return {
        "sha256": tree_digest(entries),
        "size": tree_size(entries),
        "files": [entry.to_dict() for entry in entries],
    }


@dataclass(frozen=True)
class TreeDiff:
    added: list[str]

    removed: list[str]

    modified: list[str]

    @property
    def empty(self) -> bool:

        return not (self.added or self.removed or self.modified)

    def to_dict(self) -> dict[str, Any]:
        """Counts and (at most ``MAX_NAMES_IN_DETAIL``) names per kind, for the JSON report."""

        result: dict[str, Any] = {}

        for kind, names in (
            ("added", self.added),
            ("removed", self.removed),
            ("modified", self.modified),
        ):
            result[kind] = names[:MAX_NAMES_IN_DETAIL]

            result[f"{kind}_count"] = len(names)

        return result

    def describe(self, shown: int = 3) -> str:
        """One line for people: ``1 modified (a.csv), 2 removed (b, c), ...``."""

        parts = []

        for kind, names in (
            ("modified", self.modified),
            ("removed", self.removed),
            ("added", self.added),
        ):
            if names:
                listed = ", ".join(names[:shown])

                more = f", and {len(names) - shown} more" if len(names) > shown else ""

                parts.append(f"{len(names)} {kind} ({listed}{more})")

        return "; ".join(parts) or "no difference"


def diff_trees(
    expected: Iterable[Mapping[str, Any]], actual: Iterable[FileEntry | Mapping[str, Any]]
) -> TreeDiff:
    """Compare a recorded file list with the current one."""

    recorded = {e["path"]: e["sha256"] for e in expected}

    current = {fields[0]: fields[1] for fields in (_fields(e) for e in actual)}

    return TreeDiff(
        added=sorted(set(current) - set(recorded), key=_sort_key),
        removed=sorted(set(recorded) - set(current), key=_sort_key),
        modified=sorted(
            (p for p in set(recorded) & set(current) if recorded[p] != current[p]), key=_sort_key
        ),
    )
