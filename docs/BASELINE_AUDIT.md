# Baseline audit

State of the code before the changes described in the [changelog](../CHANGELOG.md), audited on
**2026-10-18** at commit `1f3a258` (`main`, version 0.1.1, clean working tree).

## How the baseline was established

| Item | Result |
| --- | --- |
| Environment | Windows 11, Python 3.13.1, NumPy 2.5.4, pytest 9.1.1, ruff 0.17.1, installed with `pip install -e ".[dev]"` |
| `ruff check .` | passed |
| `ruff format --check .` | passed (46 files) |
| `python -m pytest` | **227 passed, 2 skipped** in 77 s |
| `python examples/demo.py` | ran; ended with "success was verified and the modified output was detected" |

The 2 skipped tests need symbolic links, which this Windows account cannot create. They were
**not** run during this audit. The documented CI matrix (Python 3.11, 3.12, 3.13 on Linux,
Windows and macOS) was not run locally either; only Python 3.13 on Windows was.

No test failed before any change was made.

## What the code does (checked against the source)

About 2,000 lines under `src/sciproof/` and 1,600 lines of tests. Runtime dependencies: none
(`dependencies = []`); optional extra `numpy` for `.npy` files.

| Capability | Where | Checked how |
| --- | --- | --- |
| `capture`: run a command once (no shell), hash declared inputs before/after, hash outputs, store exit code and truncated stdout/stderr | `capture.py`, `runner.py` | read; benchmark scenarios 1, 8a |
| JSON manifest, schema `sciproof.manifest` 1.0, strict validation of types, hashes and paths | `manifest.py` | read; `tests/test_manifest.py` |
| SHA-256 integrity of inputs, outputs and numeric snapshots | `verify.py`, `hashing.py` (streaming, 1 MiB chunks) | read; scenarios 2, 3 |
| Opt-in rerun with confirmation, timeout, process-group kill, outputs moved aside afterwards | `verify.py`, `runner.py` | read; scenarios 1b, 4, 5 |
| Numeric comparison of `.json`, `.csv`, `.npy` with `rtol`/`atol` | `numeric.py` | read; probed; rules in [COMPARISON.md](COMPARISON.md) |
| Three verdicts `PASS` / `FAIL` / `INCONCLUSIVE`, exit codes 0/1/2/3 | `verify.py`, `cli.py` | read; scenarios 6, 7 |
| Environment record: Python version and packages of the command's interpreter, platform, allowlisted variables, Git commit and dirty flag | `environment.py`, `gitinfo.py` | read |

## Public surface and compatibility constraints

* **CLI** (`capture`, `verify`, `inspect`) and its exit codes are the documented contract
  (`docs/EXIT_CODES.md`). They were not changed.
* **Manifest** `sciproof.manifest` `1.0`; readers accept major version 1. Not changed.
* **Python API:** the functions exist (`capture.capture`, `verify.verify`, `manifest.load_manifest`)
  and the CLI uses them, but `sciproof/__init__.py` exports only `__version__` and no page
  documents a Python API. Treat it as internal until it is documented.
* **JSON report** printed by `verify --json` had no schema name or version before this change.

## Security-sensitive operations

| Operation | Location | Notes |
| --- | --- | --- |
| Running the recorded command | `runner.py` | `shell=False`, stdin closed, new session/process group, kill of the whole tree on timeout or Ctrl+C. Capture has no default timeout; `verify --rerun` defaults to 3600 s. |
| Running the interpreter probe | `environment.py` | Only if the executable's *name* looks like a Python interpreter; runs a fixed snippet, after confirmation during `verify --rerun`. |
| Running `git` | `gitinfo.py` | Fixed arguments, 15 s timeout, remote URLs never recorded. |
| Reading paths from a manifest | `paths.py`, `manifest.py` | Relative, `/`-separated, no `..`, no absolute paths, resolved and checked to stay inside the manifest directory (symlinks followed first). |
| Moving and restoring files during a rerun | `verify.py` | Originals backed up in a temporary directory; new outputs moved to `.sciproof-rerun-*`. |
| Size limits | `manifest.py`, `numeric.py` | Manifest 16 MiB; numeric file 64 MiB. |
| Loading `.npy` | `numeric.py` | `allow_pickle=False`; object and string arrays refused. |

## Findings

Severity is the auditor's judgement. "Fixed" means a regression test was added and shown to fail
on the old code.

| # | Finding | How verified | Severity | Status |
| --- | --- | --- | --- | --- |
| F1 | A repeated key in a JSON object was accepted and the last value won, in manifests (`schema_version` probe) and in numeric output files (`{"loss": 1.0, "loss": 2.0}` was read as `loss = 2.0`). Parsers disagree, so the evidence was ambiguous, and the discarded value could never be compared. | probe script, then tests | medium | **Fixed**: both refused with an actionable message |
| F2 | CSV differences were reported as `r2c1` with no column name. | probe | low | **Improved**: `r2c1 (column 'loss')` |
| F3 | `rtol >= 1` was accepted silently, although it makes every number equivalent to 0 (and to its negative from 2). | probe, rule derivation | medium | **Warning added** at capture; rule documented. Not rejected, to keep compatibility |
| F4 | The verdict was not explained: no evidence per check in JSON, no statement of why the verdict was chosen, no structured "not checked", no report schema version. | reading `report_to_dict` | medium (explainability) | **Fixed**, additive: [REPORT.md](REPORT.md) |
| F5 | Two JSON integers are compared exactly even with a tolerance, while CSV numbers always use it. Intentional (integers above 2^53), but not documented and surprising. | probe | low | **Documented**, behaviour kept |
| F6 | A rerun passes the **entire parent environment** to the recorded command (`Popen` is called without `env`). A manifest from someone else can therefore read your credentials when you rerun it. `SECURITY.md` said a rerun runs arbitrary code with your permissions but did not mention this. | reading `runner.py` | medium | **Documented** in `SECURITY.md`; no behaviour change (a clean environment would break most real commands). Open question: an opt-in `--clean-env` |
| F7 | `capture` costs about 0.5 s on a 0.1 s experiment, mostly spawning a child interpreter that lists installed packages. | benchmark | low | Measured ([BENCHMARKS.md](BENCHMARKS.md)); not changed |
| F8 | The 2 symlink tests are skipped where symlinks cannot be created, so symlink handling was not exercised on this machine. | pytest output | n/a | Open here; exercised by CI on Linux/macOS |
| F9 | CSV comparison is not header-aware (a reordered column is a difference) and rows are not sorted. | probe | low | Documented as intended |

No defect was found in the path validation, the hash comparison or the aggregation of verdicts.

## Compatibility of the changes

* Text output of `verify` gained a `basis:` line and `not checked:` lines before `RESULT:`. The
  first line, the check lines and the final `RESULT:` line are unchanged. Scripts that grep
  `RESULT:` or use exit codes are unaffected.
* `verify --json` gained fields; no existing field was removed or renamed.
* A manifest or numeric file that contains a repeated key is now rejected. This is intentional;
  files written by SciProof never contain one.
