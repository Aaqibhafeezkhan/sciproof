from __future__ import annotations

import json
import subprocess
import sys

from sciproof import __version__, cli


def _capture_args(*extra, name="exp", command=None):
    command = command or [sys.executable, "experiment.py"]
    return [
        "capture",
        "--name",
        name,
        "--input",
        "data.json",
        "--input",
        "experiment.py",
        "--output",
        "out/exact.txt",
        "--output-numeric",
        "out/result.json",
        *extra,
        "--",
        *command,
    ]


def test_version(capsys):
    try:
        cli.main(["--version"])
    except SystemExit as exit_info:
        assert exit_info.code == 0
    assert __version__ in capsys.readouterr().out


def test_capture_verify_inspect_round_trip(project, capsys):
    assert cli.main(_capture_args()) == cli.EXIT_OK
    assert "Evidence written to exp.sciproof.json" in capsys.readouterr().out

    assert cli.main(["verify", "exp.sciproof.json"]) == cli.EXIT_OK
    assert "RESULT: PASS" in capsys.readouterr().out

    assert cli.main(["inspect", "exp.sciproof.json"]) == cli.EXIT_OK
    assert "SciProof manifest: exp" in capsys.readouterr().out


def test_verify_exit_codes(project, capsys):
    cli.main(_capture_args())
    capsys.readouterr()

    (project.root / "out" / "exact.txt").write_text("changed")
    assert cli.main(["verify", "exp.sciproof.json"]) == cli.EXIT_FAIL
    assert "RESULT: FAIL" in capsys.readouterr().out

    (project.root / "out" / "exact.txt").write_text("exact-a")
    (project.root / "data.json").unlink()
    assert cli.main(["verify", "exp.sciproof.json"]) == cli.EXIT_INCONCLUSIVE
    assert "RESULT: INCONCLUSIVE" in capsys.readouterr().out


def test_verify_with_rerun_and_yes(project, capsys):
    cli.main(_capture_args())
    capsys.readouterr()
    assert cli.main(["verify", "exp.sciproof.json", "--rerun", "--yes"]) == cli.EXIT_OK
    assert "RESULT: PASS" in capsys.readouterr().out


def test_failing_command_is_recorded_and_reported(project, capsys, monkeypatch):
    monkeypatch.setenv("SCIPROOF_TEST_EXIT", "7")
    assert cli.main(_capture_args()) == cli.EXIT_FAIL
    captured = capsys.readouterr()
    assert "exit code" in captured.out
    assert "failure was recorded" in captured.err
    assert (
        json.loads((project.root / "exp.sciproof.json").read_text())["execution"]["exit_code"] == 7
    )

    assert cli.main(_capture_args("--force", "--allow-nonzero")) == cli.EXIT_OK


def test_capture_without_a_command_is_a_usage_error(project, capsys):
    assert cli.main(["capture", "--name", "x", "--input", "data.json"]) == cli.EXIT_ERROR
    assert "no command given" in capsys.readouterr().err


def test_capture_with_an_unknown_command_is_a_clean_error(project, capsys):
    code = cli.main(_capture_args(command=["no-such-program-sciproof"]))
    assert code == cli.EXIT_ERROR
    assert "cannot start" in capsys.readouterr().err
    assert not (project.root / "exp.sciproof.json").exists()


def test_capture_with_a_missing_input_is_a_clean_error(project, capsys):
    (project.root / "data.json").unlink()
    assert cli.main(_capture_args()) == cli.EXIT_ERROR
    assert "input file not found" in capsys.readouterr().err


def test_missing_and_malformed_manifests_are_clean_errors(project, capsys):
    for command in ("verify", "inspect"):
        assert cli.main([command, "nope.sciproof.json"]) == cli.EXIT_ERROR
        assert "manifest not found" in capsys.readouterr().err

    (project.root / "bad.sciproof.json").write_text("{not json")
    for command in ("verify", "inspect"):
        assert cli.main([command, "bad.sciproof.json"]) == cli.EXIT_ERROR
        assert "not valid JSON" in capsys.readouterr().err


def test_runs_as_a_module(project):
    completed = subprocess.run(
        [sys.executable, "-m", "sciproof", "--version"], capture_output=True, text=True, check=True
    )
    assert __version__ in completed.stdout
