from __future__ import annotations

import shutil
import subprocess

import pytest

from sciproof.gitinfo import _is_dirty, git_info

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
NUL = chr(0)  # git status -z separates entries with NUL


def _git(root, *args):
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=root,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    (tmp_path / "code.py").write_text("print(1)")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


@needs_git
def test_clean_tree_is_not_dirty(repo):
    assert git_info(repo)["dirty"] is False


@needs_git
def test_sciproof_files_do_not_make_the_tree_dirty(repo):
    (repo / "exp.sciproof.json").write_text("{}")
    (repo / "exp.sciproof.d").mkdir()
    (repo / "exp.sciproof.d" / "0-out.csv").write_text("1")
    rerun = repo / ".sciproof-rerun-20260101T000000Z" / "out"
    rerun.mkdir(parents=True)
    (rerun / "r.txt").write_text("x")
    assert git_info(repo)["dirty"] is False


@needs_git
def test_other_changes_still_make_the_tree_dirty(repo):
    (repo / "exp.sciproof.json").write_text("{}")
    (repo / "notes.txt").write_text("untracked")
    assert git_info(repo)["dirty"] is True


@needs_git
def test_modified_tracked_file_makes_the_tree_dirty(repo):
    (repo / "code.py").write_text("print(2)")
    assert git_info(repo)["dirty"] is True


@needs_git
def test_file_names_with_spaces_and_unicode_are_handled(repo):
    (repo / ("odd name " + chr(233) + " file.txt")).write_text("x")
    assert git_info(repo)["dirty"] is True


def test_unreadable_status_is_reported_as_dirty():
    assert _is_dirty(None) is True
    assert _is_dirty("") is False
    assert _is_dirty(f"?? a.sciproof.json{NUL}") is False
    assert _is_dirty(f"?? a.sciproof.json{NUL}?? other.txt{NUL}") is True


def test_a_rename_is_checked_with_both_paths():
    assert _is_dirty(f"R  new.txt{NUL}old.txt{NUL}") is True
    assert _is_dirty(f"R  new.sciproof.json{NUL}old.sciproof.json{NUL}") is False
