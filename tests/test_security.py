"""Security properties: manifests are untrusted, nothing runs without explicit intent."""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from sciproof import cli
from sciproof import verify as verify_module
from sciproof.inspect_manifest import inspect_file
from sciproof.verify import Status, verify


@pytest.fixture
def evil(project):
    """A manifest whose command would create PWNED if it were ever executed."""
    project.capture()
    data = json.loads(project.manifest.read_text())
    data["command"]["argv"] = [sys.executable, "-c", "open('PWNED', 'w').write('x')"]
    project.manifest.write_text(json.dumps(data))
    return project


def _forbid_execution(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("something tried to execute a process")

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    monkeypatch.setattr(verify_module, "interpreter_info", refuse)


def test_inspect_never_executes_anything(evil, monkeypatch, capsys):
    _forbid_execution(monkeypatch)
    assert cli.main(["inspect", str(evil.manifest)]) == cli.EXIT_OK
    text = capsys.readouterr().out
    assert "NOT executed" in text
    assert "open('PWNED'" in text  # the command is shown, not run
    inspect_file(evil.manifest)
    assert not (evil.root / "PWNED").exists()


def test_verify_without_rerun_never_executes_anything(evil, monkeypatch):
    _forbid_execution(monkeypatch)
    report = verify(evil.manifest)
    assert report.status is Status.PASS
    assert not (evil.root / "PWNED").exists()


def test_rerun_without_confirmation_executes_nothing(evil, capsys):
    exit_code = cli.main(["verify", str(evil.manifest), "--rerun"])  # stdin is not a terminal
    assert exit_code == cli.EXIT_ERROR
    assert "refusing to execute" in capsys.readouterr().err
    assert not (evil.root / "PWNED").exists()


def test_declining_the_rerun_executes_nothing_and_does_not_probe_interpreters(evil, monkeypatch):
    _forbid_execution(monkeypatch)
    report = verify(evil.manifest, rerun=True, confirm=lambda prompt: False)
    assert report.status is Status.INCONCLUSIVE
    assert not (evil.root / "PWNED").exists()


def test_confirmed_rerun_is_the_only_way_the_command_runs(evil):
    verify(evil.manifest, rerun=True, assume_yes=True)
    assert (evil.root / "PWNED").exists()


def test_terminal_escape_sequences_in_a_manifest_are_neutralised(project, capsys):
    project.capture()
    data = json.loads(project.manifest.read_text())
    data["command"]["argv"] = ["\x1b[31mred\x1b]0;title\x07", "x\ry"]
    data["execution"]["stdout"]["text"] = "\x1b[2Jscreen cleared\x1b[0m"
    project.manifest.write_text(json.dumps(data))

    cli.main(["inspect", str(project.manifest)])
    inspect_output = capsys.readouterr().out
    assert "\x1b" not in inspect_output
    assert "\x07" not in inspect_output
    assert "\r" not in inspect_output

    prompts = []
    verify(project.manifest, rerun=True, confirm=lambda prompt: prompts.append(prompt) or False)
    assert "\x1b" not in prompts[0]


@pytest.mark.parametrize(
    "bad_path",
    ["../outside.txt", "/etc/passwd", "C:/Windows/win.ini", "a/../../outside.txt"],
)
def test_manifest_with_unsafe_paths_is_rejected_before_any_file_access(project, bad_path, capsys):
    project.capture()
    data = json.loads(project.manifest.read_text())
    data["outputs"][0]["path"] = bad_path
    project.manifest.write_text(json.dumps(data))
    assert cli.main(["verify", str(project.manifest)]) == cli.EXIT_ERROR
    assert "invalid manifest" in capsys.readouterr().err
    assert cli.main(["inspect", str(project.manifest)]) == cli.EXIT_ERROR


def test_symlink_pointing_outside_the_project_is_not_followed(project, tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("outside data")
    project.capture()
    exact = project.root / "out" / "exact.txt"
    exact.unlink()
    try:
        exact.symlink_to(secret)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not available here")

    report = verify(project.manifest)
    assert report.status is Status.FAIL
    assert any("unsafe path" in c.message for c in report.checks)

    runs = project.runs()
    rerun = verify(project.manifest, rerun=True, assume_yes=True)
    assert project.runs() == runs  # no execution when a declared path is unsafe
    assert rerun.status is not Status.PASS
