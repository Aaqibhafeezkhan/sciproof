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

Computational experiments across machine learning, bioinformatics, and computational physics are notoriously fragile: subtle changes in dependencies, hardware floating-point semantics, or random seeds frequently prevent peer reviewers and independent researchers from replicating published figures and tables [@baker2016reproducibility; @peng2011reproducible]. 

`SciProof` is a local-first, zero-runtime-dependency Python software package that records computational experiments and produces tamper-evident, machine-verifiable evidence manifests. It provides automated file-level cryptographic integrity (SHA-256), sandbox re-execution with user-declared numerical tolerances (`rtol`/`atol`), policy validation, and automated LaTeX macro exports to prevent paper number drift.

# Statement of Need

Modern reproducibility mandates by major scientific venues (such as *Nature*, *Science*, NeurIPS, and ACM Artifact Evaluation) require researchers to provide verifiable proof that computational code matches published outputs [@stodden2018empirical]. However, existing tools impose heavy operational overhead:
* **Workflow orchestrators and MLOps platforms** (e.g., DVC, MLflow) require remote tracking servers, cloud storage backends, or intrusive codebase refactoring.
* **Containers** (Docker, Singularity) capture execution environments but do not inspect or verify whether intermediate and final numerical metrics remain within acceptable numerical bounds across heterogeneous hardware.
* **Paper Number Drift:** A ubiquitous issue in academic writing occurs when code is updated, but authors forget to manually synchronize values across LaTeX tables, leading to published discrepancies.

`SciProof` addresses these gaps through five design principles:
1. **Zero-Code Instrumentation:** `sciproof record -- python script.py` captures input datasets, output artifacts, package versions, and hardware platform without modifying a single line of user code.
2. **Tolerance Calibration:** Floating-point operations vary across architectures. `sciproof calibrate` measures empirical output variance across multiple runs to automatically suggest realistic relative and absolute tolerances.
3. **Direct LaTeX Macro Export:** `sciproof export --format latex` generates LaTeX `\newcommand` macros directly from verified outputs, ensuring paper values can never drift from experimental reality.
4. **Local-First & Offline:** The entire package has zero external runtime dependencies and requires no cloud servers, databases, or API keys.
5. **Standards Interoperability:** Manifests can be exported as in-toto statements [@kupferschmidt2019intoto] or mapped to RO-Crates [@soylu2022ro-crate] for institutional archival.

# State of the Field

Several existing tools address aspects of computational reproducibility:
* **ReproZip** traces Linux system calls to package binaries and dependencies into a self-contained bundle, but focuses on Linux execution capture rather than multi-platform continuous numerical assertion.
* **Popper** utilizes container workflows to automate execution pipelines, whereas `SciProof` operates directly within standard virtual environments with zero container requirements.
* **DVC (Data Version Control)** provides Git-like tracking for large datasets and pipelines, targeting large-scale MLOps infrastructure rather than lightweight, turnkey artifact evaluation for conference and journal reviewers.

`SciProof` complements this ecosystem by prioritizing developer ergonomics, platform independence (full native Windows, macOS, and Linux support), and automated numerical tolerance auditing.

# Workflow and Key Features

A typical workflow with `SciProof` involves three phases:

```
[Experiment Script] ---> (sciproof record) ---> [Evidence Manifest (.json)]
                                                        |
                                                        v
                                               (sciproof calibrate)
                                                        |
                                                        v
[Reviewer / CI]    <--- (sciproof verify) <--- [Declared Tolerances]
         |
         v
[PASS / FAIL Report] ---> (export --format latex) ---> [Paper Tables & Values]
```

### 1. Zero-Declaration Capture
Running `sciproof record --name baseline -- python run.py` automatically detects which files were read and written, records cryptographic digests, and saves an immutable manifest `baseline.sciproof.json`.

### 2. Automated Calibration
To account for numerical stochasticity:
```bash
sciproof calibrate baseline.sciproof.json --runs 5
```
SciProof executes the command repeatedly, isolates output variance in JSON, CSV, and NumPy arrays, and prints recommended `--tolerance` settings.

### 3. Reviewer Verification
A peer reviewer or CI action verifies the results in one command:
```bash
sciproof verify baseline.sciproof.json --rerun --yes
```
The result produces an unambiguous verdict (`PASS`, `FAIL`, or `INCONCLUSIVE`).

# Research Impact

`SciProof` is designed for immediate integration into scientific research pipelines:
* **Conference Artifact Evaluation:** Serves as a turnkey reproducibility engine for ACM, IEEE, NeurIPS, and ICML artifact evaluation committees.
* **Automated CI Verification:** Enables continuous scientific validation on GitHub Actions, ensuring that ongoing codebase changes do not silently degrade numerical claims.

# AI Usage Disclosure

Generative AI assistance (LLMs) was utilized in drafting documentation and test scenario scaffolding. All algorithmic logic, verification mathematics, cryptographic digest pipelines, and final manuscript content were reviewed, verified, and authored by human contributors.

# Availability & Implementation

`SciProof` is open-source under the MIT license and hosted on GitHub (`https://github.com/hayagrivai-labs/sciproof`). It is published on PyPI (`pip install sciproof`) and archived on Zenodo (DOI: [10.5281/zenodo.23676138](https://doi.org/10.5281/zenodo.23676138)). Complete documentation, tutorial notebooks with Google Colab integration, and an automated GitHub Action are available online.

# References
