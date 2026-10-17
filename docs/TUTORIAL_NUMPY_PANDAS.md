# Tutorial: recording a NumPy/pandas experiment

This walks through [`examples/numpy_pandas/`](../examples/numpy_pandas): a noisy linear
regression written with NumPy and pandas. Every command and every output below was run for
real (Python 3.13, NumPy 2.5.4, pandas 3.0.6, on one Windows machine). Output is shortened
where marked with `...`.

Reproducibility is **not** correctness: SciProof can show that this script gives the same
numbers again, not that a straight line is the right model for your data. See
[CONCEPTS.md](CONCEPTS.md).

## 0. Setup

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
python -m pip install -e . numpy==2.5.4 pandas==3.0.6
```

The versions are pinned in [`requirements.txt`](../examples/numpy_pandas/requirements.txt) on
purpose (see step 6).

## 1. Make the experiment deterministic *before* you capture it

SciProof records what happened; it cannot make an unseeded program repeatable. In
[`experiment.py`](../examples/numpy_pandas/experiment.py):

* All randomness comes from **one explicit generator**: `rng = np.random.default_rng(seed)`,
  and the seed lives in `params.json` (an input), not hidden in the code.
* Parameters are read from a file, not typed into the command line, so they are hashed.
* Numbers are written with full precision (`float_format="%.17g"`). Rounding to a few
  digits would make a tolerance meaningless and can hide real differences.

## 2. Decide what to declare

SciProof only tracks files you declare:

| Flag | What to pass here | In this example |
| --- | --- | --- |
| `--input` | everything the result depends on: the script, parameter files, data files, a requirements/lock file | `experiment.py`, `params.json`, `requirements.txt` |
| `--output` | files that must be **bit-identical** (text, plots you do not expect to change) | none |
| `--output-numeric` | `.json`/`.csv` results that may differ by floating-point noise | `summary.json`, `data.csv` |

Inputs must be read-only for the command; capture fails if the command modifies one. If your
script reads an undeclared file, changes to it are invisible to SciProof.

## 3. Capture

```console
$ sciproof capture --name regression \
    --input examples/numpy_pandas/experiment.py \
    --input examples/numpy_pandas/params.json \
    --input examples/numpy_pandas/requirements.txt \
    --output-numeric examples/numpy_pandas/out/summary.json \
    --output-numeric examples/numpy_pandas/out/data.csv \
    --rtol 1e-9 --atol 1e-12 \
    -- python examples/numpy_pandas/experiment.py examples/numpy_pandas/params.json examples/numpy_pandas/out
warning: the Git working tree has uncommitted changes, so the commit alone does not identify the code that was run
Evidence written to regression.sciproof.json
  command exit code: 0
  inputs recorded:   3
  outputs recorded:  2
```

The Git warning appears because the tutorial files were not committed yet. Commit first when
you capture real evidence.

### Choosing `--rtol` and `--atol`

Two numbers `a` (recorded) and `b` (rerun) are equivalent if
`|a - b| <= max(rtol * max(|a|, |b|), atol)`.

* `rtol` (relative) handles large values; `atol` (absolute) handles values near zero, where a
  relative tolerance would reject `0.0` versus `1e-17`.
* The tolerance is a **scientific decision**. A starting point is `1e-9` to `1e-12` for
  double-precision results of well-conditioned computations, but an iterative or chaotic
  computation can legitimately need far more. If you can, run the experiment on two different
  machines and use the observed differences to choose; do not just widen the tolerance until
  the check passes.
* The default (`--output` without numeric) is **exact**: any difference fails.

## 4. Verify

Integrity only (nothing is executed):

```console
$ sciproof verify regression.sciproof.json
  [PASS] input examples/numpy_pandas/experiment.py: unchanged (SHA-256 matches)
  ...
  [PASS] output examples/numpy_pandas/out/data.csv: unchanged (SHA-256 matches)
  note: scope: artifact integrity only. The recorded command was NOT executed, ...
RESULT: PASS
```

By re-execution (this *runs the recorded command*, so only do it for manifests you trust):

```console
$ sciproof verify regression.sciproof.json --rerun --yes
  ...
  [PASS] exit code: 0, same as recorded
  [PASS] rerun output examples/numpy_pandas/out/summary.json: numerically equivalent (rtol=1e-09, atol=1e-12)
  [PASS] rerun output examples/numpy_pandas/out/data.csv: numerically equivalent (rtol=1e-09, atol=1e-12)
  ...
RESULT: PASS
```

## 5. Understanding `FAIL` and `INCONCLUSIVE`

* **`INCONCLUSIVE`**: SciProof cannot say anything. Example: a declared input is missing
  (here `params.json` was moved away):

  ```console
  $ sciproof verify regression.sciproof.json
    [INCONCLUSIVE] input examples/numpy_pandas/params.json: not available, so nothing can be said about it (restore the file to verify)
  RESULT: INCONCLUSIVE        # exit status 2
  ```

  Fix: restore the file (or get it from where it was stored). A large dataset that you cannot
  ship will always make verification `INCONCLUSIVE` for people without it; that is the honest
  answer, not a bug.

* **`FAIL`**: something differs. Example: `params.json` was edited after capture
  (`"noise": 0.8` changed to `0.8000001`):

  ```console
  $ sciproof verify regression.sciproof.json
    [FAIL] input examples/numpy_pandas/params.json: modified since capture (SHA-256 differs)
  RESULT: FAIL                # exit status 1
  ```

  Restoring the old value makes verification `PASS` again.

Both statuses use different exit codes (`1` and `2`), so scripts and CI can tell them apart.
Add `--json` for machine-readable output.

## 6. What this does *not* tell you

* **Versions.** SciProof records the Python version and every installed package version, and
  `verify --rerun` reports differences as warnings (`--strict-env` turns them into
  `INCONCLUSIVE`). It does not install anything. NumPy documents that the random streams of
  `Generator` can change between releases, which is why the pinned `requirements.txt` is part
  of the declared inputs.
* **Other machines.** Different CPUs, BLAS/LAPACK builds, or thread counts can change
  floating-point results in the last digits. That is exactly what `--rtol`/`--atol` are for;
  bitwise equality across machines is not promised.
* **Correctness.** A fit that reproduces perfectly can still answer the wrong question.
