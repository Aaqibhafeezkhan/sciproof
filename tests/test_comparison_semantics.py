"""Precise semantics of the numeric comparison (see docs/COMPARISON.md), one case per rule."""

from __future__ import annotations

import json
import sys

import pytest

from sciproof.errors import ManifestError
from sciproof.manifest import load_manifest
from sciproof.numeric import NumericFormatError, compare, load_numeric


def _leaves(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return load_numeric(path)


def _json_diff(tmp_path, recorded, found, rtol=0.0, atol=0.0):
    return compare(
        _leaves(tmp_path, "r.json", recorded), _leaves(tmp_path, "f.json", found), rtol, atol
    )


# ---------------------------------------------------------------- scalar rules

EQUIVALENT = [
    ("1", "1", 0, 0),
    ("1", "1.0", 0, 0),  # an integer and a float with the same value are the same number
    ("null", "null", 0, 0),
    ("true", "true", 0, 0),
    ('"a"', '"a"', 0, 0),
    ("NaN", "NaN", 0, 0),
    ("Infinity", "Infinity", 0, 0),
    ("1e-12", "0", 0, 1e-9),  # absolute tolerance rescues values near zero
    ("1000", "1000.0000001", 1e-9, 0),  # relative tolerance scales with magnitude
    ("100.0", "101.0", 0.01, 0),  # exactly on the boundary: <= is accepted
    ("100", "101.0", 0.01, 0),  # one float is enough for the tolerance to apply
    ("9007199254740993", "9007199254740993", 0, 0),
]
DIFFERENT = [
    ("1", "2", 0, 0),
    ("null", "0", 1, 1),  # null is never a number, however large the tolerance
    ("true", "1", 1, 1),  # a boolean is not a number
    ("1", "true", 1, 1),
    ('"1"', "1", 1, 1),  # a string is not a number
    ("NaN", "1", 1, 1),
    ("Infinity", "-Infinity", 1, 1),
    ("Infinity", "1e308", 1, 1),
    ("1", "1.0000001", 1e-9, 0),
    ("100", "101", 0.5, 0.5),  # two JSON integers are compared exactly, tolerance or not
    ("9007199254740993", "9007199254740992", 0, 0),  # integers above 2**53 are exact
    ("1e-12", "0", 0, 0),
    ('"a"', '"b"', 0, 0),
]


@pytest.mark.parametrize(("recorded", "found", "rtol", "atol"), EQUIVALENT)
def test_equivalent_scalars(tmp_path, recorded, found, rtol, atol):
    assert _json_diff(tmp_path, recorded, found, rtol, atol) == []


@pytest.mark.parametrize(("recorded", "found", "rtol", "atol"), DIFFERENT)
def test_different_scalars(tmp_path, recorded, found, rtol, atol):
    assert _json_diff(tmp_path, recorded, found, rtol, atol)


def test_a_large_rtol_makes_everything_equivalent_to_zero(tmp_path):
    """Documented consequence of the rule: with rtol >= 1, |a - 0| <= rtol * |a| always holds."""
    assert _json_diff(tmp_path, "5.0", "0.0", rtol=1.0) == []
    assert _json_diff(tmp_path, "5.0", "-5.0", rtol=1.0)  # opposite signs still differ below 2
    assert _json_diff(tmp_path, "5.0", "-5.0", rtol=2.0) == []


def test_the_comparison_is_symmetric_in_its_arguments(tmp_path):
    a, b = "100.0", "101.0"
    assert (_json_diff(tmp_path, a, b, rtol=0.0099) != []) == (
        _json_diff(tmp_path, b, a, rtol=0.0099) != []
    )


def test_csv_numbers_always_use_the_tolerance_unlike_json_integers(tmp_path):
    """A CSV cell is parsed with float(), so 100 vs 101 is within rtol=0.01 only in CSV."""
    recorded = _leaves(tmp_path, "r.csv", "n\n100\n")
    found = _leaves(tmp_path, "f.csv", "n\n101\n")
    assert compare(recorded, found, 0.01, 0.0) == []
    assert _json_diff(tmp_path, "100", "101", rtol=0.01)


# ---------------------------------------------------------------- structure and locations


def test_missing_and_extra_keys_are_reported(tmp_path):
    assert _json_diff(tmp_path, '{"a": 1, "b": 2}', '{"a": 1}')
    assert _json_diff(tmp_path, '{"a": 1}', '{"a": 1, "b": 2}')


def test_object_key_order_does_not_matter_but_list_order_does(tmp_path):
    assert _json_diff(tmp_path, '{"a": 1, "b": 2}', '{"b": 2, "a": 1}') == []
    assert _json_diff(tmp_path, "[1, 2]", "[2, 1]")


def test_list_length_changes_are_reported(tmp_path):
    assert _json_diff(tmp_path, "[1, 2, 3]", "[1, 2]")


def test_nested_differences_name_their_path(tmp_path):
    messages = _json_diff(tmp_path, '{"m": {"acc": [0.9, 0.8]}}', '{"m": {"acc": [0.9, 0.5]}}')
    assert len(messages) == 1
    assert messages[0].startswith("$.m.acc[1]: recorded 0.8, found 0.5")


def test_an_object_is_not_a_list(tmp_path):
    assert _json_diff(tmp_path, '{"a": 1}', "[1]")


# ---------------------------------------------------------------- CSV


def test_csv_differences_name_the_column(tmp_path):
    recorded = _leaves(tmp_path, "r.csv", "epoch,loss\n1,0.5\n2,0.4\n")
    found = _leaves(tmp_path, "f.csv", "epoch,loss\n1,0.5\n2,0.9\n")
    messages = compare(recorded, found, 1e-9, 0.0)
    assert len(messages) == 1
    assert messages[0].startswith("r2c1 (column 'loss'): recorded 0.4, found 0.9")


def test_a_changed_header_is_reported_as_text(tmp_path):
    recorded = _leaves(tmp_path, "r.csv", "a,b\n1,2\n")
    found = _leaves(tmp_path, "f.csv", "a,c\n1,2\n")
    messages = compare(recorded, found, 0.0, 0.0)
    assert messages == ["r0c1: recorded 'b', found 'c'"]


def test_reordered_csv_columns_are_a_difference(tmp_path):
    recorded = _leaves(tmp_path, "r.csv", "a,b\n1,2\n")
    found = _leaves(tmp_path, "f.csv", "b,a\n2,1\n")
    assert compare(recorded, found, 0.0, 0.0)


def test_csv_row_count_and_width_changes_are_reported(tmp_path):
    recorded = _leaves(tmp_path, "r.csv", "a,b\n1,2\n")
    assert compare(recorded, _leaves(tmp_path, "f.csv", "a,b\n1,2\n3,4\n"), 0.0, 0.0)
    assert compare(recorded, _leaves(tmp_path, "g.csv", "a,b\n1,2,3\n"), 0.0, 0.0)


# ---------------------------------------------------------------- duplicate keys are ambiguous


def test_duplicate_keys_in_a_numeric_json_file_are_refused(tmp_path):
    with pytest.raises(NumericFormatError, match="duplicate object key 'loss'"):
        _leaves(tmp_path, "d.json", '{"loss": 1.0, "loss": 2.0}')


def test_duplicate_keys_are_refused_at_any_depth(tmp_path):
    with pytest.raises(NumericFormatError, match="duplicate object key 'x'"):
        _leaves(tmp_path, "d.json", '{"a": [{"x": 1, "x": 1}]}')


def test_the_same_key_in_different_objects_is_fine(tmp_path):
    assert _leaves(tmp_path, "ok.json", '{"a": {"x": 1}, "b": {"x": 2}}')


def test_capture_refuses_a_numeric_output_with_duplicate_keys(project):
    code = "open('dup.json', 'w').write('{\"v\": 1, \"v\": 2}')"
    with pytest.raises(Exception, match="duplicate object key"):
        project.capture(
            name="dup",
            argv=[sys.executable, "-c", code],
            inputs=["data.json"],
            outputs=[],
            numeric_outputs=["dup.json"],
        )


def test_a_manifest_with_a_repeated_key_is_refused(project):
    project.capture()
    text = project.manifest.read_text()
    assert text.count('"schema_version": "1.0"') == 1
    project.manifest.write_text(
        text.replace('"schema_version": "1.0"', '"schema_version": "1.0", "schema_version": "9.9"')
    )
    with pytest.raises(ManifestError, match="duplicate object key 'schema_version'"):
        load_manifest(project.manifest)


def test_a_manifest_is_still_valid_json_after_the_check(project):
    project.capture()
    json.loads(project.manifest.read_text())
    load_manifest(project.manifest)


# ---------------------------------------------------------------- warning for a huge rtol


def test_capture_warns_about_a_relative_tolerance_of_one_or_more(project):
    result = project.capture(rtol=1.0)
    assert any("rtol=1.0 is 1 or more" in warning for warning in result.warnings)


def test_capture_does_not_warn_about_a_small_relative_tolerance(project):
    result = project.capture(rtol=1e-6)
    assert not any("rtol" in warning for warning in result.warnings)
