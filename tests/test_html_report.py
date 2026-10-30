"""Tests for HTML verification report generation."""

from __future__ import annotations

from sciproof import cli
from sciproof.html_report import format_report_html, report_html
from sciproof.verify import verify


def test_html_report_pass(project, capsys):
    project.capture()
    report = verify(project.manifest)
    html_content = report_html(report)

    assert "<!DOCTYPE html>" in html_content
    assert "SciProof" in html_content
    assert "PASS" in html_content
    assert "badge-pass" in html_content
    assert "exp" in html_content
    assert "out/exact.txt" in html_content

    # CLI export
    code = cli.main(["verify", str(project.manifest), "--format", "html"])
    assert code == cli.EXIT_OK
    cli_out = capsys.readouterr().out
    assert "<!DOCTYPE html>" in cli_out
    assert "badge-pass" in cli_out


def test_html_report_fail(project, capsys):
    project.capture()
    (project.root / "out" / "exact.txt").write_text("tampered")
    report = verify(project.manifest)
    html_content = format_report_html(report)

    assert "FAIL" in html_content
    assert "badge-fail" in html_content

    code = cli.main(["verify", str(project.manifest), "--format", "html"])
    assert code == cli.EXIT_FAIL
    assert "badge-fail" in capsys.readouterr().out
