"""A verification report as GitHub-flavoured Markdown, for CI summaries and pull-request comments.

Everything that comes from a manifest or a file (names, messages, values) is untrusted text, so
it is escaped before it is put into a table: no HTML, no table breaks, no links.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sciproof.textutil import safe_text

if TYPE_CHECKING:
    from sciproof.verify import Report

_MARK = {"PASS": ":white_check_mark:", "FAIL": ":x:", "INCONCLUSIVE": ":grey_question:"}
MAX_CELL = 300


def escape(text: object, limit: int = MAX_CELL) -> str:
    """Make ``text`` safe inside a Markdown table cell or list item."""
    cleaned = " ".join(safe_text(str(text), limit).split())
    for char, replacement in (
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
        ("|", "\\|"),
        ("`", "&#96;"),
        ("[", "\\["),
        ("]", "\\]"),
    ):
        cleaned = cleaned.replace(char, replacement)
    return cleaned


def number(value: Any) -> str:
    """A compact, stable text for a number from a difference record; ``-`` if undefined."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return escape(value, 60)


def _numeric_tables(report: Report) -> list[str]:
    lines: list[str] = []
    for check in report.checks:
        evidence = check.evidence or {}
        details = evidence.get("difference_details")
        if evidence.get("kind") != "rerun_output_numeric" or not details:
            continue
        lines += [
            "",
            f"### Numeric differences: {escape(evidence.get('path'))}",
            "",
            f"Tolerance: `rtol={number(evidence.get('rtol'))}`, "
            f"`atol={number(evidence.get('atol'))}` "
            "(a difference passes if it is at most the *allowed* value).",
            "",
            "| Location | Recorded | Found | Abs. diff | Rel. diff | Allowed |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for item in details:
            if item.get("kind") == "summary":
                lines.append(f"| {escape(item.get('message'))} | | | | | |")
                continue
            lines.append(
                f"| {escape(item.get('location') or '-')} | {number(item.get('recorded'))} "
                f"| {number(item.get('found'))} | {number(item.get('abs_diff'))} "
                f"| {number(item.get('rel_diff'))} | {number(item.get('allowed'))} |"
            )
    return lines


def report_markdown(report: Report) -> str:
    status = report.status.value
    lines = [
        f"## SciProof: {_MARK[status]} {status}: {escape(report.name, 100)}",
        "",
        f"> {escape(report.reason, 1000)}",
        "",
        "| Result | Check | Details |",
        "| --- | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            f"| {_MARK[check.status.value]} {check.status.value} | {escape(check.subject)} "
            f"| {escape(check.message)} |"
        )
    lines += _numeric_tables(report)
    if report.warnings:
        lines += ["", "### Warnings", ""]
        lines += [f"- {escape(w, 1000)}" for w in report.warnings]
    lines += ["", "### Not checked", ""]
    lines += [f"- {escape(item, 1000)}" for item in report.not_checked]
    if report.info:
        lines += ["", "### Notes", ""]
        lines += [f"- {escape(n, 1000)}" for n in report.info]
    if report.rerun_outputs_dir:
        lines += [
            "",
            f"Files produced by the rerun were moved to `{escape(report.rerun_outputs_dir)}/`.",
        ]
    lines.append("")
    return "\n".join(lines)
