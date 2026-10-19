"""The supported Python API (docs/PYTHON_API.md)."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

import sciproof
from sciproof import cli

ROOT = Path(__file__).resolve().parents[1]


def test_every_name_in_all_exists_and_nothing_else_is_promised():
    for name in sciproof.__all__:
        assert hasattr(sciproof, name), name
    assert sorted(sciproof.__all__) == sorted(set(sciproof.__all__))  # no duplicates


def test_the_api_does_not_shadow_the_modules_with_the_same_names():
    """``sciproof.verify`` and ``sciproof.capture`` stay the modules (the API uses other names)."""
    assert importlib.import_module("sciproof.verify") is sciproof.verify
    assert importlib.import_module("sciproof.capture") is sciproof.capture
    assert callable(sciproof.verify_manifest)
    assert callable(sciproof.capture_experiment)


def test_capture_then_verify_through_the_api(project):
    result = sciproof.capture_experiment(
        name="api",
        argv=[sys.executable, "experiment.py"],
        base=project.root,
        inputs=["data.json", "experiment.py"],
        numeric_outputs=["out/result.json"],
        rtol=1e-9,
    )
    assert isinstance(result, sciproof.CaptureResult)
    assert result.exit_code == 0
    report = sciproof.verify_manifest(result.manifest_path)
    assert isinstance(report, sciproof.Report)
    assert report.status is sciproof.Status.PASS


def test_report_to_dict_matches_the_json_the_cli_prints(project, capsys):
    project.capture()
    cli.main(["verify", "exp.sciproof.json", "--json"])
    printed = json.loads(capsys.readouterr().out)
    assert sciproof.verify_manifest(project.manifest).to_dict() == printed
    assert sciproof.report_to_dict(sciproof.verify_manifest(project.manifest)) == printed


def test_errors_are_the_documented_exception_types(project):
    with pytest.raises(sciproof.ManifestError):
        sciproof.load_manifest(project.root / "missing.sciproof.json")
    project.capture()
    with pytest.raises(sciproof.ConfirmationRequired):
        sciproof.verify_manifest(project.manifest, rerun=True)  # no confirmation, nothing runs
    assert project.runs() == 1  # only the capture ran
    with pytest.raises(sciproof.UsageError):
        sciproof.verify_manifest(project.manifest, timeout=-1)
    for name in ("ManifestError", "ConfirmationRequired", "UsageError", "CaptureError"):
        assert issubclass(getattr(sciproof, name), sciproof.SciProofError)


def test_the_package_is_marked_as_typed():
    assert (Path(sciproof.__file__).parent / "py.typed").is_file()


def test_the_example_runs_and_reports_the_expected_failure():
    completed = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "examples" / "api_usage.py")],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "integrity: PASS" in completed.stdout
    assert "rerun: PASS" in completed.stdout
    assert "after tampering: FAIL" in completed.stdout
