"""Exercise the shell completion protocol through the real CLI entry point."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

import pytest

from sciproof.cli import _build_parser, main


def _complete(tmp_path, line):
    if shutil.which("bash") is None:
        pytest.skip("argcomplete's filename completer needs Bash")
    output = tmp_path / "completions.txt"
    env = {
        **os.environ,
        "_ARGCOMPLETE": "1",
        "_ARGCOMPLETE_STDOUT_FILENAME": str(output),
        "_ARGCOMPLETE_IFS": "\n",
        "COMP_LINE": line,
        "COMP_POINT": str(len(line)),
    }
    result = subprocess.run(
        [sys.executable, "-m", "sciproof"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert not result.stdout
    return {value.rstrip() for value in output.read_text(encoding="utf-8").splitlines()}


def _subcommands():
    parser = _build_parser()
    return next(a.choices for a in parser._actions if isinstance(a, argparse._SubParsersAction))


def test_completion_includes_every_subcommand(tmp_path):
    assert set(_subcommands()) <= _complete(tmp_path, "sciproof ")


@pytest.mark.parametrize("command, parser", _subcommands().items())
def test_completion_includes_every_long_option(tmp_path, command, parser):
    options = {
        option
        for action in parser._actions
        for option in action.option_strings
        if option.startswith("--") and action.help != argparse.SUPPRESS
    }
    assert options <= _complete(tmp_path, f"sciproof {command} --")


def test_completion_filters_prefix_and_completes_choices(tmp_path):
    assert _complete(tmp_path, "sciproof cap") == {"capture"}
    assert _complete(tmp_path, "sciproof verify --format j") == {"json", "junit"}


def test_completion_does_not_execute_a_command_or_write_evidence(tmp_path):
    _complete(tmp_path, "sciproof capture --name trial --input absent --out")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["completions.txt"]


def test_missing_optional_dependency_preserves_normal_cli(monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "argcomplete", None)
    monkeypatch.setenv("_ARGCOMPLETE", "1")
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "sciproof" in capsys.readouterr().out
