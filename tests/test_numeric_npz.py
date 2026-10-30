"""Tests for NumPy .npz multi-array archive comparison."""

from __future__ import annotations

import pytest

from sciproof.numeric import NumericFormatError, compare, load_numeric

np = pytest.importorskip("numpy")


def _save_npz(path, **arrays):
    np.savez(path, **arrays)
    return load_numeric(path)


def test_equal_npz_archives_are_equivalent(tmp_path):
    w = np.arange(12, dtype=float).reshape(3, 4)
    b = np.array([1.0, 2.0, 3.0])
    a = _save_npz(tmp_path / "a.npz", weights=w, biases=b)
    b_leaves = _save_npz(tmp_path / "b.npz", weights=w, biases=b)
    assert compare(a, b_leaves, rtol=0.0, atol=0.0) == []


def test_npz_tolerance_and_difference_reporting(tmp_path):
    w1 = np.array([1.0, 1000.0])
    w2 = np.array([1.0, 1000.0000001])
    b = np.zeros(2)

    a = _save_npz(tmp_path / "a.npz", weights=w1, biases=b)
    b_leaves = _save_npz(tmp_path / "b.npz", weights=w2, biases=b)

    # Within 1e-6 tolerance
    assert compare(a, b_leaves, rtol=1e-6, atol=0.0) == []

    # Strict tolerance catches it
    diffs = compare(a, b_leaves, rtol=1e-12, atol=0.0)
    assert len(diffs) == 1
    assert "weights.data[1]" in diffs[0]


def test_npz_missing_array_reported_as_structural(tmp_path):
    a = _save_npz(tmp_path / "a.npz", x=np.ones(3), y=np.zeros(3))
    b = _save_npz(tmp_path / "b.npz", x=np.ones(3))
    diffs = compare(a, b, rtol=0.0, atol=0.0)
    assert any("structure differs" in d for d in diffs)


def test_npz_shape_mismatch_reported(tmp_path):
    a = _save_npz(tmp_path / "a.npz", x=np.zeros((2, 3)))
    b = _save_npz(tmp_path / "b.npz", x=np.zeros((3, 2)))
    diffs = compare(a, b, rtol=0.0, atol=0.0)
    assert any("x.shape" in d for d in diffs)


def test_corrupt_npz_file_handled(tmp_path):
    bad = tmp_path / "bad.npz"
    bad.write_bytes(b"PK\x03\x04corrupted zip archive")
    with pytest.raises(NumericFormatError):
        load_numeric(bad)
