"""Export a manifest as an in-toto Statement (v1), so that other tools can consume the evidence.

The Statement lists the output files as subjects with their SHA-256 and describes the run in a
SciProof-specific predicate. It is **not signed and not an attestation by itself**: in-toto
Statements are normally wrapped in a signed envelope (DSSE) by the tool that attests them, and
that step is deliberately left to such tools. The predicate type is SciProof's own; it does not
claim to be SLSA provenance, because SciProof records an experiment, not a build.

Nothing is executed and only the manifest is read.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sciproof import __version__
from sciproof.claims import claim_text
from sciproof.manifest import load_manifest

STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://hayagrivai-labs.github.io/sciproof/docs/export/#experiment-v1"


def _subjects(items: list[dict[str, Any]], *, only_present: bool) -> list[dict[str, Any]]:
    """One subject per file; the files of a directory are listed as ``dir/file``."""
    result = []
    for item in items:
        if only_present and not item.get("present", True):
            continue
        if item.get("kind") == "directory":
            for entry in item.get("files") or []:
                result.append(
                    {
                        "name": f"{item['path']}/{entry['path']}",
                        "digest": {"sha256": entry["sha256"]},
                    }
                )
        else:
            result.append({"name": item["path"], "digest": {"sha256": item["sha256"]}})
    return result


def to_in_toto(manifest_path: Path | str) -> dict[str, Any]:
    """The manifest as an in-toto Statement v1 (a dict that ``json.dumps`` can write)."""
    manifest_path = Path(manifest_path).resolve()
    manifest = load_manifest(manifest_path)
    environment = manifest["environment"]
    git = manifest.get("git")
    predicate: dict[str, Any] = {
        "experiment": manifest["name"],
        "capturedAt": manifest["created_at"],
        "producer": {
            "name": "sciproof",
            "version": __version__,
            "manifestSchemaVersion": manifest["schema_version"],
        },
        "manifestDigest": {"sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest()},
        "command": list(manifest["command"]["argv"]),
        "execution": {
            "exitCode": manifest["execution"]["exit_code"],
            "durationSeconds": manifest["execution"]["duration_seconds"],
        },
        "materials": _subjects(manifest["inputs"], only_present=False),
        "environment": {
            "python": environment["python"],
            "platform": environment["platform"],
            "variables": environment["env_vars"],
            "packages": [
                {"name": d["name"], "version": d["version"]} for d in manifest["dependencies"]
            ],
            "recordedBy": environment.get("source"),
        },
        "git": git,
        "outputs": [
            {
                "name": o["path"],
                "present": o["present"],
                "compare": {k: v for k, v in o["compare"].items() if k != "snapshot"},
            }
            for o in manifest["outputs"]
        ],
        "claims": [claim_text(c) for c in manifest.get("claims") or []],
        "notes": [
            "unsigned: this Statement is not an attestation until it is signed by the consumer",
            "hashes show integrity relative to the recorded digests, not that a result is correct",
        ],
    }
    return {
        "_type": STATEMENT_TYPE,
        "subject": _subjects(manifest["outputs"], only_present=True),
        "predicateType": PREDICATE_TYPE,
        "predicate": predicate,
    }


def format_in_toto(manifest_path: Path | str) -> str:
    return json.dumps(to_in_toto(manifest_path), indent=2, allow_nan=False) + "\n"
