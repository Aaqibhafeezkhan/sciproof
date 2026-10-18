# Competitive analysis

First written before implementation (October 2026); extended by an audit on **2026-10-18**.

How to read the claims. Every statement carries a label:

* **[V] verified**: checked by reading the project's source code, or by installing and running
  it, on the audit date. The check is named.
* **[D] documented**: stated by the project's README or documentation; not independently
  checked.
* **[A] assumption**: an inference that has not been tested.
* **[U] unverified question**: something the audit could not establish. Absence of a feature
  from a README is **not** treated as absence of the feature; it is listed as [U] unless the
  source was searched.

Pages were partly fetched through a summarising tool, so details should be re-checked against
the source before they are quoted elsewhere. Nothing here copies code, text or branding from
these projects; licences are noted so that anyone reusing an idea can respect them.

## The closest projects

Two projects published in 2026 target the same neighbourhood as SciProof and must be taken
seriously. Neither is a general experiment tracker.

### ReproLedger: closest in scope

[github.com/Alqudimi/reproledger](https://github.com/Alqudimi/reproledger), MIT, v0.1.0,
created and last pushed 2026-08-12, 0 stars at the audit date. Source cloned and read; installed
in a clean virtual environment and run on the benchmark scenarios ([Benchmarks](BENCHMARKS.md)).

* **Purpose [D]:** "a local-first, portable evidence ledger for software, data, and AI runs";
  turns a command into an evidence bundle.
* **Workflow [V]:** `init`, `run --input --output -- cmd`, `list`, `inspect`, `verify`, `diff`,
  `replay`, `export` (read from `cli.py`, run).
* **Evidence format [V]:** a canonical JSON `manifest.json` per run plus a `manifest.sha256`
  sidecar, `stdout.log`/`stderr.log`, and a SQLite index that is not the source of truth.
* **Integrity [V]:** SHA-256 of declared inputs and outputs (directories get a sorted tree
  digest); `verify` re-hashes them and the manifest. Editing a manifest without updating the
  sidecar is detected (benchmark scenario 7c).
* **Execution [V]:** `shell=False`; `replay` only prints a plan and never runs it (`service.py`).
  No `--timeout` option exists: the string `timeout` does not occur in `src/` (searched).
* **Numerical comparison [V]:** none. `toleran|rtol|atol|numeric|isclose|csv|npy` do not occur
  in `src/` (searched). Only exact digest comparison.
* **Verdicts [V]:** a boolean `passed`; exit `0` or `4`. A missing declared file is reported as a
  failed check (benchmark scenario 6). No `INCONCLUSIVE` state.
* **Environment [D/V]:** redacts environment variables whose names look secret (`token`,
  `password`, `api_key`, ...); rejects symlink artifacts by default. Git metadata is listed as a
  *future* feature in the README.
* **Interop [V]:** exports "OpenLineage-style" and explicitly unsigned "in-toto-style" JSON.
* **Tests [V]:** one test file with 8 test functions; the README does not claim a coverage
  figure. About 1,000 lines of Python in `src/`. Runtime dependencies: none (`dependencies = []`).
* **Where SciProof is ahead [V]:** numeric tolerance comparison for JSON/CSV/`.npy`, an opt-in
  confirmed rerun with timeout, a three-valued verdict, environment comparison on rerun, and a
  structured explanation of the verdict ([Report](REPORT.md)).
* **Where ReproLedger is ahead [V]:** a ledger of many runs (`list`, `diff`), directory
  artifacts, canonical-JSON serialisation with a sidecar digest, secret redaction of environment
  variables, OpenLineage/in-toto-style export.

### VeriRepro: same ideas, different problem

[github.com/XiantingWu/VeriRepro](https://github.com/XiantingWu/VeriRepro), Apache-2.0, v0.8.3,
198 stars, last push 2026-10-11. README, `pyproject.toml` and `src/` read; not installed or run.

* **Purpose [D]:** "evidence-grounded reproduction for computational papers": given an arXiv
  paper, DOI or PDF it links paper claims to repository evidence, environment provenance,
  execution and metrics, and writes a report.
* **Verdicts [D]:** `PASS`, `FAIL`, `PARTIAL`; "a successful process exit does not automatically
  become a scientific PASS". This is the same principle SciProof states.
* **Numerical comparison [V]:** absolute and relative tolerances exist in `src/reproagent/`
  (`artifacts.py`, `config.py`).
* **Execution [D]:** Docker execution boundary, which the README itself calls "not a formal
  sandbox proof".
* **Weight [V]:** runtime dependencies `packaging`, `Pillow`, `pypdf`, `PyYAML`, `requests`;
  about 8,000 lines of Python under `src/` (23,000 in the whole repository, including tests and release scripts); optional
  model-assisted analysis (`--no-llm` disables it).
* **Relation to SciProof:** it answers "was this *paper's* result reproduced?", starting from a
  PDF. SciProof answers "do *my recorded files and outputs* still hold?", starting from a
  command. The overlap is the principle (evidence, not exit codes) and tolerance comparison, not
  the product. **[A]** A user who wants claim-level verification of a published paper should use
  VeriRepro; SciProof should not try to extract or grade claims.

## Established tools

### DVC

* **Version [V]:** 3.67.1, Apache-2.0, 15.9k stars (GitHub API).
* **Purpose** ([docs](https://doc.dvc.org/start/data-pipelines/data-pipelines)) [D]: `dvc.yaml`
  stages list command, dependencies, parameters and outputs; `dvc.lock` records hashes (the
  example shows md5) of dependencies and outputs; `dvc repro` skips unchanged stages.
* **Numerical comparison [D]:** `dvc metrics diff`
  ([docs](https://doc.dvc.org/command-reference/metrics/diff)) compares metrics between commits
  and offers `--json`, `--md` and `--precision`; **no tolerance or threshold option is
  documented**, and the page does not say whether a difference changes the exit code ([U]).
* **Weight [V]:** `pyproject.toml` lists 42 runtime dependencies, including
  `iterative-telemetry` and `dvc-studio-client`. **[U]** Whether telemetry is on by default was
  not checked.
* **Overlap (large):** hashes of inputs and outputs for a command. Anyone already using DVC gets
  much of SciProof's integrity checking from it.
* **Difference:** DVC's hashes answer "does this stage need to run again?". SciProof asks "does
  the evidence still hold, and what exactly differs?" and reports an explicit verdict.

### ReproZip

* **Version [V]:** 1.3.2, BSD-3-Clause, last release 2026-01-18.
* **Purpose** ([README](https://github.com/VIDA-NYU/reprozip), [docs](https://docs.reprozip.org/en/1.x/))
  [D]: "tracks operating system calls and creates a package that contains all the binaries,
  files and dependencies required to run a given command"; `reprounzip` rebuilds it
  (directory, chroot, container or VM setups).
* **Limit [D]:** "Packing experiments is only available for Linux distributions."
* **[U]:** whether reproduced outputs are compared with the originals, and whether packs are
  integrity-checked, was not established.
* **Difference:** ReproZip's strength is *packaging the whole environment*. SciProof records and
  compares and never packages or rebuilds an environment.

### MLflow

* **Version [V]:** 3.17.1, Apache-2.0, 28k stars. The repository description now reads "the open
  source AI engineering platform for agents, LLMs, and ML models": the project's centre of
  gravity is production AI observability, not reproducibility checks.
* **Tracking** ([docs](https://mlflow.org/docs/latest/ml/tracking/)) [D]: logs parameters, code
  versions, metrics and output files; local `mlruns` directory without a server.
* **[U]:** artifact hashing, tamper detection and numerical comparison of a rerun were not
  established (a code search through the GitHub API returned no usable result).
* **Difference:** an experiment *management* and observability system with a UI; not described as
  checking whether a rerun matches.

### noWorkflow

* **Version [V]:** 2.1.3, MIT, last push 2026-10-18; Python 3.11+ ([D]).
* **Purpose** ([README](https://github.com/gems-uff/noworkflow)) [D]: captures the provenance of
  a Python script without changing it, using AST analysis, reflection and profiling: module
  dependencies, environment attributes, function activations, file accesses, variable
  dependencies. `now run`, `show`, `diff`, `restore`, `export` (Prolog, PROV, ...).
* **Privacy [D]:** the README warns that a provenance store "records the whole environment of the
  machine (environment variables, user name, hostname)". SciProof records an allowlist only.
* **Numerical comparison [V]:** no tolerance feature found; `isclose` appears only in a test
  corpus (searched). `now diff` compares modules, environment and file accesses [D].
* **[U]:** whether accessed data files are content-hashed.
* **Difference:** fine-grained *how* provenance inside one script (a research instrument) versus
  SciProof's coarse *did the declared evidence hold* verdict.

### Sumatra

* **Purpose** ([docs](https://sumatra.readthedocs.io/en/latest/introduction.html)) [D]:
  tracking computational experiments "like an electronic lab notebook": code version, parameters,
  platform, outcome summary, links to output data.
* **Maintenance [U]:** the docs page does not say; sources disagreed, so no claim is made.
* **Difference [D]:** describes recording and provenance; does not describe hashing artifacts or
  an automatic verdict from re-running.

### RO-Crate (and Workflow Run Crate profiles)

* **Purpose** ([RO-Crate 1.1](https://www.researchobject.org/ro-crate/specification/1.1/introduction.html))
  [D]: a method "for aggregating and describing research data with associated metadata", a JSON-LD
  file using mostly schema.org. The page does not describe verifying files or re-executing.
* **Workflow Run Crate** ([profiles](https://www.researchobject.org/workflow-run-crate/profiles/)):
  profiles for recording workflow executions at increasing granularity.
* **Difference:** a *description standard*, not a verifier. A SciProof manifest could be exported
  as a Process Run Crate (see [RO-Crate design notes](DESIGN_RO_CRATE.md)); that is an
  interoperability feature, not a competing format.

### Tools for the numerical part

`pytest.approx` and `numpy.testing.assert_allclose` compare numbers with tolerances inside a
test suite you write. [A] They do not record where the reference values came from.

## Feature matrix

`yes` / `no` are [V] unless marked. `?` means [U].

| | SciProof 0.1.1 | ReproLedger 0.1.0 | VeriRepro 0.8.3 | DVC 3.x | ReproZip 1.3 | MLflow 3.x | noWorkflow 2.1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Primary user | researcher / CI | developer / CI | paper reproducer | data scientist | researcher (Linux) | ML/AI team | Python researcher |
| Records a command | yes | yes | yes (D) | yes (stages) | yes (traced) | yes (runs) | yes (script) |
| SHA-256 of declared files | yes | yes | ? | md5 default (D) | ? | ? | ? |
| Tamper detection on verify | yes | yes | ? | status/repro (D) | ? | ? | ? |
| Explicit, confirmed rerun | yes | no (plan only) | executes code (D) | `dvc repro` | `reprounzip run` | no | `now restore` (D) |
| Numeric tolerance compare | yes (json/csv/npy) | no | yes | no (D) | ? | ? | no |
| Verdict states | PASS/FAIL/INCONCLUSIVE | pass/fail | PASS/FAIL/PARTIAL (D) | n/a | n/a | n/a | n/a |
| Per-check evidence in JSON | yes | partial | ? | n/a | n/a | n/a | n/a |
| "Not checked" list | yes | no | ? | no | no | no | no |
| Environment capture | allowlisted vars, Python, packages | redacted env | rich (D) | no | whole system | partial | whole env incl. user/host (D) |
| Runtime dependencies | none | none (D) | 5 | 40+ | several | many | 3+ |
| Offline | yes | yes | partly (needs network for papers/LLM) (A) | yes (A) | yes (A) | yes locally (D) | yes (A) |

## Honest overlap assessment

Capturing a command with its hashes and outputs is **not new**. ReproLedger does it with a ledger
and exports; DVC does it inside a pipeline; ReproZip captures far more of the environment;
noWorkflow captures more detail about the script. A project that only "records experiments" would
duplicate these.

## Differentiation: what the evidence supports

The original hypothesis, written before the audit, was a lean offline manifest whose main feature
is an honest verification step. The audit narrows it:

1. **Not unique:** "evidence, not exit codes" is VeriRepro's headline too, and local-first
   integrity manifests exist in ReproLedger. Claiming either as SciProof's differentiator would be
   wrong.
2. **Still open [V]:** no audited project combines (a) a three-valued verdict with a conservative
   aggregation rule, (b) declared numeric tolerances with stated semantics for JSON/CSV/`.npy`,
   (c) an opt-in, confirmed, timed rerun that leaves the tree as it found it, and (d) a report
   that lists what was *not* checked, with zero runtime dependencies. ReproLedger lacks (a)–(c);
   VeriRepro is far heavier and aimed at papers; DVC has no tolerance comparison (D); noWorkflow
   has none (V).
3. **Strength of the claim:** this is a statement about the *audited* projects on one date, not a
   survey of the field, and no real-user evidence exists. It stays a hypothesis; see the
   [Product roadmap](PRODUCT_ROADMAP.md) for how to test it.

## Features SciProof should deliberately avoid duplicating

* Packaging or rebuilding environments (ReproZip, containers, Nix, conda).
* Data and pipeline versioning, remote storage, caching (DVC).
* Experiment dashboards, parameter sweeps, model registries, tracing (MLflow).
* Paper or claim extraction and LLM-assisted grading (VeriRepro).
* Fine-grained intra-script provenance (noWorkflow).
* A new metadata standard (RO-Crate). Prefer export/import to existing standards if users ask.
* Anything cloud-hosted, accounts, blockchain-style "proofs", or AI features.

## Not investigated

Containers and environment managers (Docker, Nix, Guix, conda lock files, Binder), OpenLineage and
in-toto tooling themselves, lakeFS, hosted services, and other 2026 projects not found by the
audit's searches. This is not a complete survey.
