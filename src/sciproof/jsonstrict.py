"""Strict JSON parsing helpers.

``json.loads`` silently keeps the *last* value of a repeated object key, and other JSON
parsers keep the first. Evidence that parses differently in different tools is ambiguous, so
SciProof refuses it instead of picking a winner.
"""

from __future__ import annotations

from typing import Any


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """``object_pairs_hook`` for ``json.loads`` that raises ``ValueError`` on a repeated key."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            shown = key if len(key) <= 60 else f"{key[:60]}..."
            raise ValueError(
                f"duplicate object key {shown!r}: parsers disagree about which value wins, so "
                "the content is ambiguous"
            )
        result[key] = value
    return result
