"""Capture and verify an experiment from Python. Runs in a temporary directory.

python examples/api_usage.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import sciproof

EXPERIMENT = """\
import json, pathlib
data = json.loads(pathlib.Path("data.json").read_text())
pathlib.Path("metrics.json").write_text(json.dumps({"loss": data["x"] / 3, "epochs": 3}))
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "experiment.py").write_text(EXPERIMENT)
        (root / "data.json").write_text('{"x": 1.0}')

        # 1. Record the run. Only the files you declare are tracked.
        result = sciproof.capture_experiment(
            name="demo",
            argv=[sys.executable, "experiment.py"],
            base=root,
            inputs=["data.json", "experiment.py"],
            numeric_outputs=["metrics.json"],
            rtol=1e-6,
        )
        print("captured:", result.manifest_path.name, "exit code", result.exit_code)

        # 2. Integrity only: nothing is executed.
        report = sciproof.verify_manifest(result.manifest_path)
        print("integrity:", report.status.value)

        # 3. Re-execute (arbitrary code!) with a minimal environment, and look at the evidence.
        report = sciproof.verify_manifest(
            result.manifest_path, rerun=True, assume_yes=True, clean_env=True
        )
        print("rerun:", report.status.value)
        print("why:", report.reason)
        for check in report.checks:
            print(f"  [{check.status.value}] {check.subject}")

        # 4. Tamper with an input: the verdict changes and says why.
        (root / "data.json").write_text('{"x": 2.0}')
        report = sciproof.verify_manifest(result.manifest_path)
        print("after tampering:", report.status.value)
        failed = [c for c in report.checks if c.status is sciproof.Status.FAIL]
        print("failed check:", failed[0].subject, failed[0].evidence)

        # The same report as plain data (what `sciproof verify --json` prints).
        print("report schema:", report.to_dict()["schema"])
        return 0 if report.status is sciproof.Status.FAIL else 1  # FAIL is the expected result


if __name__ == "__main__":
    raise SystemExit(main())
