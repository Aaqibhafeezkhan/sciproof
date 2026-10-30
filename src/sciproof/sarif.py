"""SARIF 2.1.0 output for verification reports, for GitHub Code Scanning and security tabs."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from sciproof import __version__
from sciproof.textutil import safe_text

if TYPE_CHECKING:
    from sciproof.verify import Report


SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
)

SARIF_VERSION = "2.1.0"


def report_sarif(report: Report) -> dict[str, Any]:
    """Verification report as a SARIF 2.1.0 dictionary."""

    rules = [
        {
            "id": "SP001",
            "name": "VerificationFailure",
            "shortDescription": {"text": "SciProof check failed."},
            "defaultConfiguration": {"level": "error"},
        },
        {
            "id": "SP002",
            "name": "VerificationInconclusive",
            "shortDescription": {"text": "SciProof check was inconclusive."},
            "defaultConfiguration": {"level": "warning"},
        },
        {
            "id": "SP003",
            "name": "VerificationWarning",
            "shortDescription": {"text": "SciProof verification warning."},
            "defaultConfiguration": {"level": "warning"},
        },
    ]

    results: list[dict[str, Any]] = []

    for check in report.checks:
        if check.status.value == "PASS":
            continue

        level = "error" if check.status.value == "FAIL" else "warning"

        rule_id = "SP001" if check.status.value == "FAIL" else "SP002"

        subject = safe_text(check.subject, 500)

        message = safe_text(check.message, 2000)

        result: dict[str, Any] = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": f"{subject}: {message}"},
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": subject.removeprefix("output ").removeprefix("input "),
                        },
                    }
                }
            ],
        }

        results.append(result)

    for warning in report.warnings:
        warn_text = safe_text(warning, 2000)

        results.append(
            {
                "ruleId": "SP003",
                "level": "warning",
                "message": {"text": warn_text},
            }
        )

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "sciproof",
                        "version": __version__,
                        "informationUri": "https://github.com/hayagrivai-labs/sciproof",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def format_report_sarif(report: Report) -> str:
    """Verification report formatted as SARIF 2.1.0 JSON string."""

    return json.dumps(report_sarif(report), indent=2, allow_nan=False) + "\n"
