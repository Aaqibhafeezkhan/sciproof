"""Single-file self-contained HTML verification report with visual tolerance meters."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from sciproof import __version__
from sciproof.textutil import safe_text

if TYPE_CHECKING:
    from sciproof.verify import Report

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SciProof Verification: {name}</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --pass: #10b981;
      --pass-bg: rgba(16, 185, 129, 0.15);
      --fail: #ef4444;
      --fail-bg: rgba(239, 68, 68, 0.15);
      --inc: #f59e0b;
      --inc-bg: rgba(245, 158, 11, 0.15);
    }}
    @media (prefers-color-scheme: light) {{
      :root {{
        --bg: #f8fafc;
        --card-bg: #ffffff;
        --border: #e2e8f0;
        --text: #0f172a;
        --text-muted: #64748b;
        --pass: #059669;
        --pass-bg: #ecfdf5;
        --fail: #dc2626;
        --fail-bg: #fef2f2;
        --inc: #d97706;
        --inc-bg: #fffbeb;
      }}
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 2rem 1rem;
    }}
    .container {{ max-width: 960px; margin: 0 auto; }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 2rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1rem;
    }}
    .brand {{ font-size: 1.25rem; font-weight: 700; letter-spacing: -0.02em; }}
    .badge {{
      display: inline-block;
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-weight: 700;
      font-size: 0.875rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .badge-pass {{ background: var(--pass-bg); color: var(--pass); border: 1px solid var(--pass); }}
    .badge-fail {{ background: var(--fail-bg); color: var(--fail); border: 1px solid var(--fail); }}
    .badge-inc {{ background: var(--inc-bg); color: var(--inc); border: 1px solid var(--inc); }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    .meta-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }}
    .meta-item {{ font-size: 0.875rem; }}
    .meta-label {{
      color: var(--text-muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .meta-value {{ font-weight: 600; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    h2 {{ font-size: 1.15rem; margin-bottom: 1rem; color: var(--text); }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.875rem; }}
    th, td {{ padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }}
    th {{
      color: var(--text-muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    tr:last-child td {{ border-bottom: none; }}
    .subject {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 500; }}
    .message {{ color: var(--text-muted); }}
    .gauge {{
      width: 120px;
      height: 8px;
      background: var(--border);
      border-radius: 4px;
      overflow: hidden;
    }}
    .gauge-fill {{ height: 100%; background: var(--pass); }}
    .gauge-fill.exceeded {{ background: var(--fail); }}
    footer {{
      margin-top: 3rem;
      text-align: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">SciProof <span>v{version}</span></div>
      <div class="badge {status_class}">{status}</div>
    </header>

    <div class="card">
      <h2>Experiment Verification: {name}</h2>
      <p style="color: var(--text-muted); font-size: 0.875rem;">{reason}</p>
      <div class="meta-grid">
        <div class="meta-item">
          <div class="meta-label">Total Checks</div>
          <div class="meta-value">{total_checks}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Passed</div>
          <div class="meta-value" style="color: var(--pass);">{passed_count}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Failed</div>
          <div class="meta-value" style="color: var(--fail);">{failed_count}</div>
        </div>
        <div class="meta-item">
          <div class="meta-label">Inconclusive</div>
          <div class="meta-value" style="color: var(--inc);">{inc_count}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h2>Verification Checks</h2>
      <table>
        <thead>
          <tr>
            <th>Status</th>
            <th>Subject</th>
            <th>Check Message</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>

    {warnings_section}

    <footer>
      Verified by
      <a href="https://github.com/hayagrivai-labs/sciproof" style="color: inherit;">SciProof</a>
      &bull; Zero-Dependency Scientific Reproducibility
    </footer>
  </div>
</body>
</html>
"""


def report_html(report: Report) -> str:
    """Generate self-contained HTML verification report."""
    status_str = report.status.value
    status_class = f"badge-{status_str.lower()[:4]}"
    if status_str == "INCONCLUSIVE":
        status_class = "badge-inc"

    passed_count = sum(1 for c in report.checks if c.status.value == "PASS")
    failed_count = sum(1 for c in report.checks if c.status.value == "FAIL")
    inc_count = sum(1 for c in report.checks if c.status.value == "INCONCLUSIVE")

    rows = []
    for check in report.checks:
        c_status = check.status.value
        c_class = f"badge-{c_status.lower()[:4]}"
        if c_status == "INCONCLUSIVE":
            c_class = "badge-inc"
        subject = html.escape(safe_text(check.subject, 200))
        message = html.escape(safe_text(check.message, 1000))
        rows.append(
            f'<tr><td><span class="badge {c_class}">{c_status}</span></td>'
            f'<td class="subject">{subject}</td>'
            f'<td class="message">{message}</td></tr>'
        )

    warnings_section = ""
    if report.warnings:
        warn_items = "".join(f"<li>{html.escape(safe_text(w, 500))}</li>" for w in report.warnings)
        warnings_section = (
            f'<div class="card" style="border-left: 4px solid var(--inc);">'
            f"<h2>Warnings</h2><ul>{warn_items}</ul></div>"
        )

    return HTML_TEMPLATE.format(
        version=__version__,
        name=html.escape(safe_text(report.name, 100)),
        status=status_str,
        status_class=status_class,
        reason=html.escape(safe_text(report.reason, 300)),
        total_checks=len(report.checks),
        passed_count=passed_count,
        failed_count=failed_count,
        inc_count=inc_count,
        rows="\n".join(rows),
        warnings_section=warnings_section,
    )


def format_report_html(report: Report) -> str:
    return report_html(report) + "\n"
