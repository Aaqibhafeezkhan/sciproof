"""Structured numeric differences and the Markdown report."""

from __future__ import annotations

import json
import math

import pytest

from sciproof import cli
from sciproof.errors import UsageError
from sciproof.markdown import escape, number, report_markdown
from sciproof.numeric import Difference, compare, compare_detailed, load_numeric
from sciproof.verify import Report, Status, report_to_dict, verify


def _leaves(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return load_numeric(path)


# ---------------------------------------------------------------- structured differences


def test_a_numeric_difference_carries_its_numbers(tmp_path):
    recorded = _leaves(tmp_path, "r.json", '{"loss": 0.5}')
    found = _leaves(tmp_path, "f.json", '{"loss": 0.6}')
    (diff,) = compare_detailed(recorded, found, 1e-3, 0.0)
    assert diff.kind == "number"
    assert diff.location == "$.loss"
    assert (diff.recorded, diff.found) == (0.5, 0.6)
    assert diff.abs_diff == pytest.approx(0.1)
    assert diff.rel_diff == pytest.approx(0.1 / 0.6)
    assert diff.allowed == pytest.approx(1e-3 * 0.6)
    assert diff.abs_diff > diff.allowed  # that is why it is a difference


def test_compare_returns_exactly_the_messages_of_compare_detailed(tmp_path):
    recorded = _leaves(tmp_path, "r.json", '{"a": 1.0, "b": "x", "c": [1, 2]}')
    found = _leaves(tmp_path, "f.json", '{"a": 2.0, "b": "y", "c": [1, 3]}')
    assert compare(recorded, found, 0.0, 0.0) == [
        d.message for d in compare_detailed(recorded, found, 0.0, 0.0)
    ]


def test_text_and_structure_differences_have_no_numbers(tmp_path):
    recorded = _leaves(tmp_path, "r.json", '{"label": "ok", "n": [1, 2]}')
    found = _leaves(tmp_path, "f.json", '{"label": "bad", "n": [1]}')
    by_kind = {d.kind: d for d in compare_detailed(recorded, found, 0.0, 0.0)}
    assert by_kind["value"].abs_diff is None
    assert "structure" in by_kind


def test_integers_are_exact_so_nothing_is_allowed(tmp_path):
    recorded = _leaves(tmp_path, "r.json", "[100]")
    found = _leaves(tmp_path, "f.json", "[101]")
    (diff,) = compare_detailed(recorded, found, 0.5, 0.5)
    assert (diff.abs_diff, diff.allowed) == (1.0, 0.0)


def test_non_finite_values_become_strict_json_strings(tmp_path):
    recorded = _leaves(tmp_path, "r.json", "[1.0, NaN]")
    found = _leaves(tmp_path, "f.json", "[Infinity, 1.0]")
    diffs = compare_detailed(recorded, found, 0.0, 0.0)
    assert [d.found for d in diffs] == ["Infinity", 1.0]
    assert diffs[1].recorded == "NaN"
    assert all(d.abs_diff is None for d in diffs)  # undefined for non-finite values
    json.dumps([d.to_dict() for d in diffs], allow_nan=False)  # strictly valid JSON


def test_a_relative_difference_against_zero_is_defined_only_when_both_are_zero():
    d = Difference("m", "number", "x", 0.0, 0.0, 0.0, 0.0, 0.0)
    assert d.to_dict()["rel_diff"] == 0.0


def test_huge_values_are_shortened_in_the_records(tmp_path):
    big = "9" * 400
    recorded = _leaves(tmp_path, "r.json", f"[{big}]")
    found = _leaves(tmp_path, "f.json", "[1]")
    (diff,) = compare_detailed(recorded, found, 0.0, 0.0)
    assert "characters" in str(diff.recorded)
    assert len(json.dumps(diff.to_dict())) < 1000


def test_csv_differences_name_the_column_in_the_record(tmp_path):
    recorded = _leaves(tmp_path, "r.csv", "epoch,loss\n1,0.5\n")
    found = _leaves(tmp_path, "f.csv", "epoch,loss\n1,0.9\n")
    (diff,) = compare_detailed(recorded, found, 1e-9, 0.0)
    assert diff.location == "r1c1 (column 'loss')"
    assert math.isclose(diff.abs_diff, 0.4)


# ---------------------------------------------------------------- evidence in the report


def test_the_rerun_evidence_lists_the_difference_details(project, monkeypatch):
    project.capture(rtol=1e-9)
    monkeypatch.setenv("SCIPROOF_TEST_EPS", "1e-3")
    data = report_to_dict(verify(project.manifest, rerun=True, assume_yes=True))
    evidence = next(c for c in data["checks"] if c["subject"] == "rerun output out/result.json")[
        "evidence"
    ]
    (detail,) = evidence["difference_details"]
    assert detail["location"] == "$.value"
    assert detail["abs_diff"] == pytest.approx(1e-3)
    assert detail["allowed"] < detail["abs_diff"]
    assert evidence["differences"] == [detail["message"]]
    json.dumps(data, allow_nan=False)


def test_a_rerun_within_tolerance_has_no_details(project, monkeypatch):
    project.capture(rtol=1e-6)
    monkeypatch.setenv("SCIPROOF_TEST_EPS", "1e-12")
    data = report_to_dict(verify(project.manifest, rerun=True, assume_yes=True))
    evidence = next(c for c in data["checks"] if c["subject"] == "rerun output out/result.json")[
        "evidence"
    ]
    assert evidence["difference_details"] == []


# ---------------------------------------------------------------- Markdown


def test_markdown_has_the_verdict_the_reason_and_what_was_not_checked(project):
    project.capture()
    text = verify(project.manifest).to_markdown()
    assert text.startswith("## SciProof: :white_check_mark: PASS: exp\n")
    assert "> PASS because all" in text
    assert "| :white_check_mark: PASS | input data.json | unchanged (SHA-256 matches) |" in text
    assert "### Not checked" in text
    assert "- reproducibility: the recorded command was not executed" in text
    assert "### Numeric differences" not in text


def test_markdown_shows_a_numeric_difference_table(project, monkeypatch):
    project.capture(rtol=1e-9)
    monkeypatch.setenv("SCIPROOF_TEST_EPS", "1e-3")
    text = verify(project.manifest, rerun=True, assume_yes=True).to_markdown()
    assert "## SciProof: :x: FAIL: exp" in text
    assert "### Numeric differences: out/result.json" in text
    assert "| Location | Recorded | Found | Abs. diff | Rel. diff | Allowed |" in text
    row = next(line for line in text.splitlines() if line.startswith("| $.value "))
    cells = [c.strip() for c in row.strip("|").split("|")]
    assert cells[0] == "$.value"
    assert cells[1] == "42" and cells[2] == "42.001"
    assert "0.001" in cells[3]


def test_markdown_escapes_everything_that_comes_from_a_manifest():
    report = Report(name="x|<b>y</b>", rerun_requested=False)
    report.add(Status.FAIL, "input a|b", "<script>alert(1)</script> [link](http://evil) `code`")
    report.warnings.append("a\nb | c")
    text = report_markdown(report)
    assert "<script>" not in text and "<b>" not in text
    assert "&lt;script&gt;" in text
    assert "[link](http://evil)" not in text  # brackets are escaped, so it is not a link
    assert "a\\|b" in text
    assert "a\\nb \\| c" in text  # the line break is shown as \n, never rendered
    for line in text.splitlines():  # no check can break out of its table row
        assert line.count("|") - line.count("\\|") in (0, 4)


def test_escape_and_number_helpers():
    assert escape("a|b\nc") == "a\\|b\\nc"
    assert escape("a  b   c") == "a b c"  # runs of blanks collapse
    assert escape("x" * 1000, limit=10).startswith("xxxxxxxxxx")
    assert number(None) == "-"
    assert number(0.1 + 0.2) == "0.3"
    assert number(True) == "True"
    assert number(12345678.9) == "1.23457e+07"


# ---------------------------------------------------------------- command line


def test_cli_format_markdown_prints_markdown_and_keeps_the_exit_code(project, capsys):
    project.capture()
    (project.root / "out" / "exact.txt").write_text("tampered")
    code = cli.main(["verify", "exp.sciproof.json", "--format", "markdown"])
    out = capsys.readouterr().out
    assert code == cli.EXIT_FAIL
    assert out.startswith("## SciProof: :x: FAIL: exp")


def test_cli_json_flag_is_still_an_alias_and_conflicts_are_refused(project, capsys):
    project.capture()
    assert cli.main(["verify", "exp.sciproof.json", "--json"]) == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["schema"] == "sciproof.report"
    assert cli.main(["verify", "exp.sciproof.json", "--format", "json"]) == cli.EXIT_OK
    assert json.loads(capsys.readouterr().out)["result"] == "PASS"
    assert cli.main(["verify", "exp.sciproof.json", "--json", "--format", "text"]) == cli.EXIT_ERROR
    assert "conflicts" in capsys.readouterr().err
    with pytest.raises(UsageError):
        cli._report_format(type("A", (), {"json": True, "format": "markdown"})())
