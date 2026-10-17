from __future__ import annotations

import sys

from sciproof import cli
from sciproof.capture import capture
from sciproof.suggest import suggest_inputs
from sciproof.verify import Status, verify

RUN = """\
import json
import helper

config = json.load(open("config.json"))
open("out.txt", "w").write(str(helper.VALUE + config["k"]))
"""


def _project(root):
    (root / "run.py").write_text(RUN)
    (root / "helper.py").write_text("VALUE = 1\n")
    (root / "config.json").write_text('{"k": 1}')
    return [sys.executable, "run.py"]


def test_reports_undeclared_python_files_and_data(tmp_path):
    argv = _project(tmp_path)
    found = suggest_inputs(argv, tmp_path, ["run.py", "out.txt"])
    assert found.exit_code == 0
    assert found.inside == ["config.json", "helper.py"]
    assert found.outside == []


def test_declared_files_are_not_reported(tmp_path):
    argv = _project(tmp_path)
    found = suggest_inputs(argv, tmp_path, ["run.py", "helper.py", "config.json", "out.txt"])
    assert found.inside == []


def test_environment_is_restored(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "keep-me")
    monkeypatch.delenv("SCIPROOF_AUDIT_LOG", raising=False)
    suggest_inputs(_project(tmp_path), tmp_path, ["run.py"])
    import os

    assert os.environ["PYTHONPATH"] == "keep-me"
    assert "SCIPROOF_AUDIT_LOG" not in os.environ


def test_cli_prints_suggestions(tmp_path, monkeypatch, capsys):
    argv = _project(tmp_path)
    monkeypatch.chdir(tmp_path)
    code = cli.main(["suggest-inputs", "--input", "run.py", "--output", "out.txt", "--", *argv])
    out = capsys.readouterr().out
    assert code == cli.EXIT_OK
    assert "suggest --input helper.py" in out
    assert "suggest --input config.json" in out


def test_undeclared_dependency_is_invisible_to_plain_verify_but_not_to_rerun(tmp_path):
    """Documents the limit of declared inputs, and why 'suggest-inputs' exists."""
    argv = _project(tmp_path)
    result = capture(name="exp", argv=argv, base=tmp_path, inputs=["run.py"], outputs=["out.txt"])
    (tmp_path / "helper.py").write_text("VALUE = 2\n")  # undeclared dependency changes
    assert verify(result.manifest_path).status is Status.PASS  # integrity of declared files only
    rerun = verify(result.manifest_path, rerun=True, assume_yes=True)
    assert rerun.status is Status.FAIL  # the output changed, so the rerun notices
