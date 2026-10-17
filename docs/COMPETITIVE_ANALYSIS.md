# Competitive analysis

Written before implementation, in October 2026. Statements are limited to what the cited
pages say. Where a page did not answer a question, that is stated instead of guessed.
Pages were fetched through a summarising tool, so details should be re-checked against the
source before they are quoted elsewhere.

## Tools looked at

### ReproZip

* **Purpose** ([docs](https://docs.reprozip.org/en/1.x/)): "tracks operating system calls and
  creates a bundle that contains all the binaries, files, and dependencies required to run a
  given command" (a `.rpz` file). `reprounzip` rebuilds the experiment from it, from plain
  extraction up to a full virtual machine.
* **Limits stated in the docs:** packing only works for experiments that ran on Linux
  (unpacking is not restricted to Linux).
* **Not answered by the page:** whether reproduced outputs are compared with the originals.
* **Overlap with SciProof:** both start from "a command" and aim at rerunning it.
* **Difference:** ReproZip's strength is *packaging the whole environment*. SciProof records
  and compares, but never packages or rebuilds an environment.

### Sumatra

* **Purpose** ([docs](https://sumatra.readthedocs.io/en/latest/introduction.html)): tracking
  computational experiments, "like an electronic lab notebook"; records code version (or
  repository URL and revision), parameters, platform (architecture, OS, processors), a reason
  and outcome summary, and links to output data. Recording is meant to be automatic.
* **Maintenance:** the docs page does not say. A search result showed the PyPI page describing
  it as beta code and an ecosystem mirror listing the latest release as over eight years old,
  but the sources disagreed, so no claim is made here. Check the project before relying on it.
* **Overlap:** run records with code, platform and outputs.
* **Difference (from the page):** it describes recording and provenance; it does not describe
  hashing artifacts or an automatic verdict from re-running.

### MLflow Tracking

* **Purpose** ([docs](https://mlflow.org/docs/latest/ml/tracking/)): logs "parameters, code
  versions, metrics, and output files"; stores runs and artifacts such as models and images;
  without server configuration it logs to a local `mlruns` directory.
* **Not answered by the page:** environment/git capture details, verification of
  reproducibility, artifact hashing.
* **Overlap:** local run records with artifacts.
* **Difference:** MLflow is a experiment *management* system centred on ML workflows,
  parameters and metrics, with a UI. It is not described as checking whether a rerun matches.

### DVC (pipelines)

* **Purpose** ([docs](https://doc.dvc.org/start/data-pipelines/data-pipelines)): `dvc.yaml`
  stages list command, dependencies, parameters and outputs. `dvc.lock` records hashes (the
  example shows md5, "in most cases") of dependencies and outputs plus parameter values;
  `dvc repro` uses it to skip unchanged stages and reuse cached results.
* **Not mentioned on the page:** numerical tolerance comparison; recording of Python/OS
  environment (it only recommends a virtualenv).
* **Overlap (large):** content hashes of inputs and outputs for a command.
* **Difference:** DVC is a pipeline and data-versioning system whose hashes answer "does this
  stage need to be rerun?". SciProof's question is "does the evidence still hold and can I
  re-check it?", with an explicit verdict and tolerances. Anyone already using DVC gets much of
  SciProof's integrity checking from it.

### RO-Crate (and Workflow Run Crate profiles)

* **Purpose** ([RO-Crate 1.1](https://www.researchobject.org/ro-crate/specification/1.1/introduction.html)):
  a method "for aggregating and describing research data with associated metadata", a JSON-LD
  file (`ro-crate-metadata.json`) using mostly schema.org, describing data, contextual
  entities (people, software, equipment) and provenance. The page does not describe verifying
  files or re-executing anything.
* **Workflow Run Crate** ([profiles](https://www.researchobject.org/workflow-run-crate/profiles/)):
  profiles for recording the provenance of workflow executions at increasing granularity
  (Process Run, Workflow Run, Provenance Run), per a search result summary.
* **Overlap:** describing a run and its inputs/outputs in a portable, standard format.
* **Difference:** RO-Crate is a *description standard*, not a verifier. A SciProof manifest
  could in future be exported as a Process Run Crate (see "Differentiation"), which would be
  an interoperability feature rather than a competing format.

### Tools for the numerical part (not researched in depth)

`pytest.approx` ([docs](https://docs.pytest.org/en/stable/reference/reference.html#pytest-approx))
and `numpy.testing.assert_allclose`
([docs](https://numpy.org/doc/stable/reference/generated/numpy.testing.assert_allclose.html))
compare numbers with tolerances inside tests. These links come from general knowledge and
were not fetched for this document. They solve the comparison *inside* a test suite you
write; they do not record where the reference values came from.

### Not investigated

Container- and environment-based approaches (Docker, Nix, Guix, conda lock files, Binder),
other provenance tools (noWorkflow and similar), and hosted services. They are listed so that
no one reads this document as a complete survey.

## Honest overlap assessment

Capturing a command with its environment, hashes and outputs is **not new**. DVC already
hashes dependencies and outputs; Sumatra and MLflow record runs; ReproZip captures far more of
the environment; RO-Crate standardises description. A project that only "records experiments"
would duplicate these.

## Differentiation hypothesis (unproven)

A narrow gap that these documents leave open, and that SciProof's MVP targets:

> A **single-file, dependency-free, offline evidence manifest** for one command, whose main
> feature is an honest **verification step**: a three-valued verdict (`PASS` / `FAIL` /
> `INCONCLUSIVE`), exact hashes by default, **explicit per-output numerical tolerances**, and
> a deliberate separation between "files are intact" and "the computation reproduced".

Why this might be useful: it can be added to an existing script or CI job without adopting a
pipeline system, a server or a container workflow, and the verdict is machine-readable (exit
codes) so a reviewer or CI job can re-check a result.

Why it might not be: researchers may already be satisfied with DVC plus a lock file, or with
containers. **This is a hypothesis and must be tested with real users before any claim of
usefulness or uniqueness is made.**

## Features SciProof should deliberately avoid duplicating

* Packaging or rebuilding environments (ReproZip, containers, Nix, conda).
* Data and pipeline versioning, remote storage, caching (DVC).
* Experiment dashboards, parameter sweeps, model registries (MLflow).
* A new metadata standard (RO-Crate). Prefer export/import to existing standards later, if
  users ask for it.
* Anything cloud-hosted, accounts, blockchain-style "proofs", or AI features.
