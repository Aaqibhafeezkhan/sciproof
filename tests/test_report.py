"""The verification report: evidence per check, the reason and what was not checked."""

from __future__ import annotations

import json
import re

import pytest

from sciproof import cli
from sciproof.verify import (
    REPORT_SCHEMA,
    REPORT_SCHEMA_VERSION,
    Report,
    Status,
    format_report,
    report_to_dict,
    verify,
)

SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _check(report_dict, subject_part):
    matching = [c for c in report_dict["checks"] if subject_part in c["subject"]]
    assert matching, [c["subject"] for c in report_dict["checks"]]
    return matching[0]


# ---------------------------------------------------------------- schema and aggregation


def test_json_report_is_versioned_and_keeps_the_original_keys(project):
    project.capture()
    data = report_to_dict(verify(project.manifest))
    assert data["schema"] == REPORT_SCHEMA == "sciproof.report"
    assert data["schema_version"] == REPORT_SCHEMA_VERSION == "1.0"
    # keys that existed before the schema was introduced must still be there
    assert {"name", "result", "rerun_requested", "checks", "warnings", "notes"} <= set(data)
    assert {"status", "subject", "message"} <= set(data["checks"][0])
    assert data["counts"] == {"PASS": len(data["checks"]), "FAIL": 0, "INCONCLUSIVE": 0}
    json.dumps(data)  # the whole report must be serialisable


def test_a_pass_says_what_it_does_not_cover(project):
    project.capture()
    data = report_to_dict(verify(project.manifest))
    assert data["result"] == "PASS"
    assert data["rerun_executed"] is False
    assert "reproducibility: the recorded command was not executed" in data["not_checked"]
    assert any("scientific validity" in item for item in data["not_checked"])
    assert any("unsigned" in item for item in data["not_checked"])
    assert data["reason"].startswith("PASS because all ")


def test_tampered_output_reports_both_digests(project):
    project.capture()
    (project.root / "out" / "exact.txt").write_text("tampered")
    data = report_to_dict(verify(project.manifest))
    assert data["result"] == "FAIL"
    evidence = _check(data, "output out/exact.txt")["evidence"]
    assert evidence["kind"] == "output_integrity"
    assert evidence["path"] == "out/exact.txt"
    assert SHA256.match(evidence["expected_sha256"])
    assert SHA256.match(evidence["actual_sha256"])
    assert evidence["expected_sha256"] != evidence["actual_sha256"]
    assert "output out/exact.txt" in data["reason"]


def test_missing_input_is_inconclusive_with_no_actual_digest(project):
    project.capture()
    (project.root / "data.json").unlink()
    data = report_to_dict(verify(project.manifest))
    assert data["result"] == "INCONCLUSIVE"
    evidence = _check(data, "input data.json")["evidence"]
    assert SHA256.match(evidence["expected_sha256"])
    assert evidence["actual_sha256"] is None
    assert "never counted as success" in data["reason"]


def test_one_failure_outweighs_inconclusive_checks(project):
    project.capture()
    (project.root / "data.json").unlink()  # INCONCLUSIVE
    (project.root / "out" / "exact.txt").write_text("tampered")  # FAIL
    data = report_to_dict(verify(project.manifest))
    assert data["result"] == "FAIL"
    assert data["counts"]["FAIL"] == 1
    assert data["counts"]["INCONCLUSIVE"] == 1
    assert "one failed check is enough" in data["reason"]


def test_a_report_without_any_check_is_inconclusive():
    report = Report(name="empty", rerun_requested=False)
    assert report.status is Status.INCONCLUSIVE
    assert "no check could be performed" in report.reason


def test_the_reason_lists_only_a_few_subjects():
    report = Report(name="many", rerun_requested=False)
    for index in range(8):
        report.add(Status.FAIL, f"output f{index}", "modified")
    assert report.reason.count("output f") == 5
    assert "and 3 more" in report.reason


# ---------------------------------------------------------------- reruns


def test_rerun_numeric_check_records_tolerance_and_rule(project, monkeypatch):
    project.capture(rtol=1e-6)
    monkeypatch.setenv("SCIPROOF_TEST_EPS", "1e-12")
    data = report_to_dict(verify(project.manifest, rerun=True, assume_yes=True))
    assert data["result"] == "PASS"
    assert data["rerun_executed"] is True
    evidence = _check(data, "rerun output out/result.json")["evidence"]
    assert evidence["kind"] == "rerun_output_numeric"
    assert evidence["rtol"] == 1e-6
    assert evidence["atol"] == 0.0
    assert "max(rtol" in evidence["rule"]
    assert evidence["differences"] == []
    assert "reproducibility: the recorded command was not executed" not in data["not_checked"]
    assert any("one re-execution" in item for item in data["not_checked"])


def test_rerun_outside_tolerance_names_the_location(project, monkeypatch):
    project.capture(rtol=1e-9)
    monkeypatch.setenv("SCIPROOF_TEST_EPS", "1e-3")
    data = report_to_dict(verify(project.manifest, rerun=True, assume_yes=True))
    assert data["result"] == "FAIL"
    evidence = _check(data, "rerun output out/result.json")["evidence"]
    assert len(evidence["differences"]) == 1
    assert evidence["differences"][0].startswith("$.value: recorded 42")


def test_rerun_exit_code_evidence(project, monkeypatch):
    project.capture()
    monkeypatch.setenv("SCIPROOF_TEST_EXIT", "3")
    data = report_to_dict(verify(project.manifest, rerun=True, assume_yes=True))
    assert _check(data, "exit code")["evidence"] == {"kind": "exit_code", "recorded": 0, "rerun": 3}


# ---------------------------------------------------------------- human-readable form


def test_text_report_explains_the_verdict(project):
    project.capture()
    text = format_report(verify(project.manifest))
    lines = text.splitlines()
    assert lines[-1] == "RESULT: PASS"
    assert any(line.startswith("  basis: PASS because") for line in lines)
    assert any(line.startswith("  not checked: scientific validity") for line in lines)


@pytest.mark.parametrize("flag", [[], ["--json"]])
def test_cli_output_carries_the_explanation(project, capsys, flag):
    project.capture()
    assert cli.main(["verify", "exp.sciproof.json", *flag]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "not checked" in out or "not_checked" in out
