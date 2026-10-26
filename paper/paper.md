---
title: 'SciProof: Machine-Verifiable Computational Evidence and Reproducibility for Scientific Experiments'
tags:
  - Python
  - reproducibility
  - open science
  - research software
  - provenance
  - artifact evaluation
authors:
  - name: Alok Pandey
    affiliation: 1
affiliations:
 - name: HayagrivAI Labs
   index: 1
date: 27 October 2026
bibliography: paper.bib
---

# Summary

Computational experiments across scientific domains frequently fail independent replication attempts [@baker2016reproducibility; @peng2011reproducible]. Even when research code is made publicly available, small differences in software dependencies, underlying hardware floating-point units, or operating systems can cause re-execution to produce numbers that diverge from the published manuscript [@stodden2018empirical].

`SciProof` is a lightweight, zero-dependency Python tool designed to capture computational experiments and produce verifiable evidence manifests. It records cryptographic SHA-256 digests of all input datasets and generated outputs, stores system execution metadata, and enables automated re-execution checks. To address the reality of floating-point drift across hardware architectures, `SciProof` includes a calibration routine that empirically determines relative and absolute numerical tolerances (`rtol` and `atol`), allowing reviewers and continuous integration pipelines to distinguish acceptable precision variance from broken computations.

# Statement of Need

Academic venues and funding agencies increasingly mandate code and data sharing to combat irreproducibility. However, verifying that code actually reproduces published results remains difficult in practice:

1. **Containers vs. Verification:** Container systems such as Docker encapsulate dependencies, but they treat the executed code as a black box. They do not automatically verify whether output data matches declared numbers within acceptable bounds.
2. **Heavyweight Infrastructure:** Production workflow orchestrators and data versioning tools (e.g., MLflow, DVC) often require remote databases, object storage buckets, or extensive code refactoring, creating friction for individual researchers.
3. **Paper Number Drift:** A frequent failure mode during paper writing occurs when an experiment is re-run, but updated metrics are not propagated into LaTeX tables and figures, leading to inconsistencies in the published text.

`SciProof` addresses these practical hurdles by operating directly on standard Python scripts without requiring modifications to user code. It runs entirely locally, stores evidence in plain JSON manifests, and includes utilities to export verified values directly into LaTeX macros.

# State of the Field

Prior tools have tackled aspects of computational reproducibility from different angles:

* **Syscall Tracers:** ReproZip [@chirigati2016reprozip] uses `ptrace` on Linux to trace file access and bundle software environments into self-contained archives. While powerful for Linux packaging, it is platform-dependent and does not provide numerical tolerance evaluation across repeated runs.
* **Workflow Engines:** Systems like Snakemake and Nextflow manage large-scale computational graphs but focus on scheduling and execution rather than lightweight verification of single-run experimental claims.
* **Cryptographic Attestations:** Frameworks like in-toto [@kupferschmidt2019intoto] focus on software supply-chain integrity. `SciProof` shares these integrity principles and supports in-toto and RO-Crate [@soylu2022ro-crate] export, but tailors its user interface specifically to academic artifact evaluation.

`SciProof` provides a lightweight alternative that works natively across Linux, macOS, and Windows with standard Python installations.

# Software Design and Core Workflow

The typical lifecycle of an experiment verified with `SciProof` involves three steps:

```
[Experiment Command] ---> sciproof record ---> [Manifest (.sciproof.json)]
                                                        |
                                                        v
                                               sciproof calibrate
                                                        |
                                                        v
[Peer Reviewer / CI] <--- sciproof verify <--- [Calibrated Tolerances]
```

### 1. Recording an Experiment
A researcher runs their existing script using the `record` subcommand:

```bash
sciproof record --name benchmark --inputs data.csv -- python train.py
```

`SciProof` executes the command in a child process, computes SHA-256 hashes of the declared inputs and generated outputs, and writes a structured manifest (`benchmark.sciproof.json`) alongside execution metadata (CPU architecture, OS platform, Python version, runtime duration, and exit status).

### 2. Calibrating Numerical Tolerances
Because floating-point calculations can vary between CPU architectures and BLAS implementations, exact bitwise matching of floating-point numbers is often impractical. The `calibrate` command runs the experiment multiple times to measure observed variation in JSON, CSV, or NumPy (`.npy`) outputs:

```bash
sciproof calibrate benchmark.sciproof.json --runs 5
```

It outputs empirical maximum absolute and relative deviations, recommending safe `atol` and `rtol` parameters for verification.

### 3. Reviewer Verification
A reviewer or automated GitHub Actions workflow verifies the experiment with a single command:

```bash
sciproof verify benchmark.sciproof.json --rerun --yes
```

The tool validates file integrity hashes, re-executes the command in a sandboxed directory, compares newly generated outputs against the recorded baseline using the calibrated tolerances, and outputs a concise `PASS` or `FAIL` verdict.

### 4. Preventing Number Drift
To ensure figures and tables in a manuscript match the underlying code, `SciProof` exports verified manifest values into LaTeX definitions:

```bash
sciproof export benchmark.sciproof.json --format latex > numbers.tex
```

This allows authors to write `\newcommand{\accuracy}{94.2}` directly into their LaTeX document source, preventing manual transcription errors.

# Research Impact and Artifact Evaluation

`SciProof` has been structured to streamline the submission workflow for conference Artifact Evaluation committees (such as ACM SIGMOD, OSDI, NeurIPS, and ICML). Authors can include a single `.sciproof.json` manifest and reproduction badge in their code repository, providing evaluators with an unambiguous, automated way to confirm experimental results.

# AI Usage Disclosure

No generative artificial intelligence tools were used in writing this manuscript or developing the software algorithms.

# Availability

`SciProof` is distributed under the MIT license. Source code, documentation, test suites, and Colab quickstart tutorials are publicly hosted on GitHub (`https://github.com/hayagrivai-labs/sciproof`). Releases are published on PyPI (`pip install sciproof`) and archived on Zenodo (DOI: [10.5281/zenodo.23676138](https://doi.org/10.5281/zenodo.23676138)).

# References
