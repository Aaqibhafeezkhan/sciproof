"""Shared fixtures: a tiny project with a controllable experiment."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from sciproof.capture import CaptureResult, capture

EXPERIMENT = """\
import json
import os
import pathlib
import sys

data = json.loads(pathlib.Path("data.json").read_text())
eps = float(os.environ.get("SCIPROOF_TEST_EPS", "0"))
pathlib.Path("out").mkdir(exist_ok=True)
pathlib.Path("out/result.json").write_text(
    json.dumps({"value": data["x"] * 2 + eps, "label": "ok"})
)
pathlib.Path("out/exact.txt").write_text("exact-" + os.environ.get("SCIPROOF_TEST_SUFFIX", "a"))
with open("marker.txt", "a") as handle:  # lets tests count how often the command really ran
    handle.write("ran\\n")
print("done")
sys.exit(int(os.environ.get("SCIPROOF_TEST_EXIT", "0")))
"""


@dataclass
class Project:
    root: Path

    @property
    def manifest(self) -> Path:
        return self.root / "exp.sciproof.json"

    def runs(self) -> int:
        marker = self.root / "marker.txt"
        return len(marker.read_text().splitlines()) if marker.exists() else 0

    def capture(self, **overrides) -> CaptureResult:
        options = {
            "name": "exp",
            "argv": [sys.executable, "experiment.py"],
            "base": self.root,
            "inputs": ["data.json", "experiment.py"],
            "outputs": ["out/exact.txt"],
            "numeric_outputs": ["out/result.json"],
            "rtol": 1e-9,
            "atol": 0.0,
        }
        options.update(overrides)
        return capture(**options)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Project:
    for name in ("SCIPROOF_TEST_EPS", "SCIPROOF_TEST_SUFFIX", "SCIPROOF_TEST_EXIT"):
        monkeypatch.delenv(name, raising=False)
    root = tmp_path / "project"
    root.mkdir()
    (root / "experiment.py").write_text(EXPERIMENT)
    (root / "data.json").write_text('{"x": 21}')
    monkeypatch.chdir(root)
    return Project(root)
