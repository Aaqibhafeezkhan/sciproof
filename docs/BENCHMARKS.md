# Benchmarks

Eight verification scenarios, run end to end through the command-line tools in fresh temporary
directories. Reproduce with `python benchmarks/run_benchmarks.py` (SciProof only) or add
`--reproledger PATH` to include [ReproLedger](COMPETITIVE_ANALYSIS.md), which you install
yourself in a separate environment. The script never installs or downloads anything.

## What this does and does not show

* **Measured:** the verdict or exit code each tool gives (does it detect the situation?), and
  wall-clock time of whole command invocations.
* **Not measured:** memory, large files, many runs, other operating systems, report clarity as
  judged by users, setup effort beyond the commands in the script.
* **Bias to keep in mind:** the "expected" outcomes were defined by the SciProof authors from
  SciProof's documented semantics. A tool with a different design (ReproLedger has two verdicts,
  not three) can only be shown as "differs", which is not the same as "wrong".
* **Not compared:** DVC, ReproZip, MLflow, noWorkflow and VeriRepro were not run. Their
  workflows are not equivalent tasks (pipelines, packaging, tracking servers, paper pipelines),
  so no numbers are reported for them. No claim of speed or reliability against them is made.

## Conditions of the recorded run

* 2026-10-18, Windows 11, Python 3.13.1, one machine, nothing else running.
* SciProof 0.1.1 plus the changes in this branch; ReproLedger 0.1.0 installed from its
  repository into a separate virtual environment.
* The experiment reads `data.json`, writes `result.json` (a value that can be nudged through an
  environment variable) and takes about 0.1 s. Times are of the whole CLI invocation, including
  interpreter start-up.

## Scenario results

`Observed` is the verdict derived from the tool's exit code. Exit codes: SciProof 0/1/2/3 =
PASS/FAIL/INCONCLUSIVE/error; ReproLedger 0 = pass, 4 = fail, 3 or 5 = error.

| Scenario | SciProof | ReproLedger |
| --- | --- | --- |
| 1. Unchanged deterministic experiment, integrity check | PASS | PASS |
| 1b. Same, verified by re-execution | PASS | not supported (`replay` only prints a plan) |
| 2. Modified input file | FAIL | FAIL |
| 3. Modified output file | FAIL | FAIL |
| 4. Numeric output within the tolerance (rerun, `eps=1e-9`, `rtol=1e-6`) | PASS | not supported (no rerun, no tolerance) |
| 5. Numeric output outside the tolerance (rerun, `eps=1e-2`) | FAIL | not supported |
| 6. Missing required evidence (an input file deleted) | INCONCLUSIVE | FAIL (only pass/fail exist; a missing file is a failed check) |
| 7a. Truncated manifest | error (exit 3) | error (exit 5) |
| 7b. Manifest with a repeated key | error (exit 3) | not run (its manifest is protected by a sidecar digest, so an edit is not an equivalent test) |
| 7c. Manifest hash edited to a wrong value / manifest edited | FAIL | FAIL |
| 8a. Command fails during capture | evidence written, exit 1 | evidence written, exit 3 (the command's exit code) |
| 8b. Capture exceeds a timeout | exit 3, no evidence written | not supported (`run` has no timeout option) |

SciProof gave the expected outcome in all 12 of its scenarios. ReproLedger ran 7 scenarios and
matched the expectation in 6; in scenario 6 its two-valued design reports FAIL instead of
INCONCLUSIVE. It could not run 4 scenarios (1b, 4, 5, 8b), and scenario 7b was not run.

## Overhead

Median of 7 runs of one cycle in a fresh directory, in seconds:

| Step | Seconds |
| --- | --- |
| The experiment alone | 0.099 |
| `sciproof capture` | 0.618 |
| `sciproof verify` (integrity only) | 0.193 |
| `sciproof verify --rerun --yes` | 0.606 |

Reading the numbers honestly: for a 0.1 s experiment, `capture` adds about half a second. A
direct measurement of its parts on this machine gives about 0.14 s to list the installed
packages in a child interpreter and 0.04 s for `git status`, plus the experiment itself and
start-up. This is a roughly fixed cost, not a measure of scalability, and it grows with the
number of installed packages. Integrity verification costs about one interpreter start-up plus
hashing the declared files. For comparison, a single (not repeated) `reproledger verify` in
scenario 1 took 0.19 s.

## What the benchmark found

* The new report fields (evidence, `basis`, `not checked`) and the refusal of duplicate keys
  (scenario 7b) behave as designed. Before this change a repeated key in a manifest was accepted
  and the last value won (shown with `schema_version` in a probe before the fix; the benchmark
  itself was not run against the old code).
* Nothing here shows SciProof is faster or more reliable than another tool. It shows that on
  these eight situations it detects what it documents, and that the audited alternatives do not
  cover scenarios 1b, 4, 5, 6 (as a distinct verdict) and 8b.
