"""Tests for auto-collapsing newly created all-stable directories in record (Closes #124)."""

from __future__ import annotations

import sys

from sciproof import load_manifest, verify_manifest
from sciproof.record import record
from sciproof.verify import Status


def test_record_collapses_newly_created_stable_directory(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / "data.txt").write_text("input data")

    script = """
import pathlib
d = pathlib.Path("shards")
d.mkdir(exist_ok=True)
(d / "part1.bin").write_bytes(b"shard 1 content")
(d / "part2.bin").write_bytes(b"shard 2 content")
"""
    (root / "run.py").write_text(script)

    res = record(name="exp_dir", argv=[sys.executable, "run.py"], base=root)
    assert res.exact == ["shards"]
    assert res.numeric == []
    assert "--output shards" in res.command_line

    manifest = load_manifest(res.capture.manifest_path)
    output_entries = manifest["outputs"]
    assert len(output_entries) == 1
    assert output_entries[0]["path"] == "shards"
    assert output_entries[0]["kind"] == "directory"
    assert len(output_entries[0]["files"]) == 2

    # Verification passes
    assert verify_manifest(res.capture.manifest_path).status is Status.PASS
    assert (
        verify_manifest(res.capture.manifest_path, rerun=True, assume_yes=True).status
        is Status.PASS
    )


def test_record_does_not_collapse_pre_existing_directory(tmp_path):
    root = tmp_path / "project_pre"
    root.mkdir()
    # Directory already exists before run
    (root / "out").mkdir()
    (root / "out" / "initial.txt").write_text("pre-existing")

    script = """
import pathlib
(pathlib.Path("out") / "new1.txt").write_text("content 1")
(pathlib.Path("out") / "new2.txt").write_text("content 2")
"""
    (root / "run.py").write_text(script)

    res = record(name="exp_pre", argv=[sys.executable, "run.py"], base=root)
    # Stays file-by-file because "out" existed before
    assert "out/new1.txt" in res.exact
    assert "out/new2.txt" in res.exact
    assert "out" not in res.exact


def test_record_does_not_collapse_when_noisy_file_present(tmp_path):
    root = tmp_path / "project_noisy"
    root.mkdir()

    script = """
import pathlib, time
d = pathlib.Path("results")
d.mkdir(exist_ok=True)
(d / "stable1.txt").write_text("stable 1")
(d / "stable2.txt").write_text("stable 2")
# Noisy file with time
(d / "noisy.log").write_text(str(time.time_ns()))
"""
    (root / "run.py").write_text(script)

    res = record(name="exp_noisy", argv=[sys.executable, "run.py"], base=root)
    # Stays file-by-file because noisy.log is excluded
    assert "results/stable1.txt" in res.exact
    assert "results/stable2.txt" in res.exact
    assert "results" not in res.exact
    assert any("results/noisy.log" in exc[0] for exc in res.excluded)


def test_record_does_not_collapse_when_numeric_file_present(tmp_path):
    root = tmp_path / "project_num"
    root.mkdir()

    script = """
import pathlib, json
d = pathlib.Path("models")
d.mkdir(exist_ok=True)
(d / "weights.bin").write_bytes(b"binary weights")
(d / "metrics.json").write_text(json.dumps({"loss": 0.05}))
"""
    (root / "run.py").write_text(script)

    res = record(name="exp_num", argv=[sys.executable, "run.py"], base=root)
    # Stays file-by-file because metrics.json is numeric
    assert "models/weights.bin" in res.exact
    assert "models/metrics.json" in res.numeric
    assert "models" not in res.exact
