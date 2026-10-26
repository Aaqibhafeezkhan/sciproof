# SciProof Community Launch & Outreach Playbook

This document contains ready-to-copy launch posts tailored for Reddit, Hacker News, X (Twitter), and academic conference outreach.

---

## 1. Reddit: r/Python

**Post Title:**
> SciProof — A zero-dependency tool to record experiments, verify reproducibility, and stop copy-pasting numbers into LaTeX tables

**Post Body:**
```markdown
Hi r/Python!

Like many of you who work on computational scripts, scientific software, or ML pipelines, I ran into the same painful cycle:
1. Months after running an experiment, a collaborator or reviewer asks: *"Which exact code and dataset produced Table 2, and does it still run?"*
2. An experiment is re-run with a slightly improved dataset, but someone forgets to update a cell in Table 3 of the LaTeX draft, leading to published discrepancies.
3. Floating-point noise across CPU/GPU architectures causes strict `assert a == b` tests to fail.

To solve this without adding heavy cloud servers or complex databases, we built **SciProof**: a local-first, zero-runtime-dependency CLI and Python library.

### What it does:
* **Zero code modifications:** Run `sciproof record -- python train.py` — it automatically detects which inputs Python read, hashes output files with SHA-256, and records environment info into a single `.sciproof.json` manifest.
* **Direct LaTeX Export:** Never re-type numbers from the terminal into your paper again.
  `sciproof export baseline.sciproof.json --format latex -o values.tex --value acc metrics.json "$.accuracy"`
  This generates `\newcommand{\acc}{0.942}` so your paper values can never drift from experimental code.
* **Calibrate tolerances:** Floating-point noise happens. `sciproof calibrate` runs your script repeatedly, isolates variance, and suggests the exact `rtol`/`atol` needed so reviewers get an unambiguous `PASS`.
* **One-command reviewer verification:** Anyone can verify with `sciproof verify baseline.sciproof.json --rerun`.

### Links & Try it:
* **Interactive Google Colab:** [Open in Colab](https://colab.research.google.com/github/hayagrivai-labs/sciproof/blob/main/examples/quickstart.ipynb) (Try it in 2 minutes without installing locally)
* **GitHub:** https://github.com/hayagrivai-labs/sciproof
* **Documentation:** https://hayagrivai-labs.github.io/sciproof/
* **PyPI:** `pip install sciproof` (Python 3.11+)
* **Zenodo DOI:** https://doi.org/10.5281/zenodo.23676138

We would love your feedback and thoughts on what else could make computational reproducibility easier!
```

---

## 2. Reddit: r/MachineLearning

**Post Title:**
> [P] SciProof: Zero-code reproducible experiment tracking, floating-point calibration, and direct LaTeX macro exports for paper drafts

**Post Body:**
```markdown
Hi everyone,

When submitting ML papers to NeurIPS, ICML, or ICLR, meeting the Reproducibility Checklist is essential. Most ML engineers find tools like DVC or MLflow too heavy for lightweight paper experiments, and containers (Docker) don't solve floating-point noise or paper number drift.

We built **SciProof** as a lightweight, zero-dependency reproducibility manifest generator:

1. **Record with 0 changes to your codebase:**
   `sciproof record -- python train.py --epochs 50`
   Automatically captures inputs, outputs, git commit, packages, and hardware.
2. **Prevent Paper Number Drift:**
   `sciproof export baseline.sciproof.json --format latex -o paper_values.tex --value acc out.json "$.test_acc"`
   In your paper: `Our model achieved \acc{} test accuracy.` If your results change, your paper numbers update automatically.
3. **Calibrate Numerical Tolerances:**
   `sciproof calibrate baseline.sciproof.json --runs 5`
   Measures empirical variance and recommends realistic `--tolerance` bounds so floating-point discrepancies across GPUs don't fail reviewer audits.
4. **Artifact Evaluation Ready:** Reviewers verify with `sciproof verify baseline.sciproof.json --rerun`.

* Repo: https://github.com/hayagrivai-labs/sciproof
* 1-Click Colab: https://colab.research.google.com/github/hayagrivai-labs/sciproof/blob/main/examples/quickstart.ipynb
* DOI: 10.5281/zenodo.23676138
```

---

## 3. Hacker News (Show HN)

**Title:**
> Show HN: SciProof – Reproducible scientific experiments and automated LaTeX export

**Body:**
```markdown
SciProof is an open-source, local-first Python tool to record computational experiments, calibrate floating-point tolerances, and verify reproducibility.

Problem:
Computational experiments are fragile. Months after running code, it's often impossible to tell whether outputs match the original run. Furthermore, in scientific and quantitative work, numbers are frequently copied by hand into LaTeX tables, leading to subtle drift when experiments are re-run.

How SciProof works:
- Zero runtime dependencies (standard library only; optional numpy for .npy).
- Run `sciproof record -- python script.py`. It tracks file I/O, hashes artifacts with SHA-256, and writes an evidence manifest.
- `sciproof calibrate` measures numerical variance over multiple runs and recommends floating-point bounds (rtol/atol).
- `sciproof export --format latex` generates LaTeX macros (`\newcommand{\metric}{0.94}`) directly from verified outputs so paper drafts stay in sync.
- A reviewer or CI checks with `sciproof verify manifest.sciproof.json --rerun`.

GitHub: https://github.com/hayagrivai-labs/sciproof
Docs: https://hayagrivai-labs.github.io/sciproof/
Colab demo: https://colab.research.google.com/github/hayagrivai-labs/sciproof/blob/main/examples/quickstart.ipynb
```

---

## 4. X (Twitter) Viral Launch Thread

**Tweet 1:**
> Stop manually copy-pasting numbers from terminal outputs into LaTeX tables! 🛑
>
> We just released SciProof 0.4.1: a zero-dependency Python tool to record computational experiments, calibrate floating-point noise, and guarantee paper reproducibility.
>
> Here’s how it works in 30 seconds 🧵👇

**Tweet 2:**
> 1/ Zero-code experiment capture ⚡
>
> You don't need to import decorators or rewrite your script.
> Just run:
> `sciproof record -- python train.py`
>
> SciProof automatically tracks inputs, hashes outputs (SHA-256), and records your Python environment into an immutable manifest.

**Tweet 3:**
> 2/ Never let paper numbers drift 📄
>
> Run:
> `sciproof export baseline.sciproof.json --format latex -o values.tex --value acc metrics.json "$.accuracy"`
>
> In your paper:
> `Our model achieves \acc{} accuracy.`
> If your experiment changes, paper numbers update automatically.

**Tweet 4:**
> 3/ Calibrate floating-point noise 🎯
>
> Different GPUs/CPUs produce slight floating-point differences ($10^{-6}$).
>
> Run `sciproof calibrate` — it runs your script repeatedly and suggests the exact relative tolerance (`rtol`) so reviewers get a deterministic PASS.

**Tweet 5:**
> Try it in Google Colab without installing anything:
> 🔗 https://colab.research.google.com/github/hayagrivai-labs/sciproof/blob/main/examples/quickstart.ipynb
>
> ⭐️ Star the repo on GitHub: https://github.com/hayagrivai-labs/sciproof
> 📦 PyPI: `pip install sciproof`
> 🎓 DOI: 10.5281/zenodo.23676138

---

## 5. Email Template for Conference Artifact Evaluation Chairs

**Subject:**
> Turnkey reproducibility verification template for [Conference Name] Artifact Evaluation

**Body:**
```text
Dear Artifact Evaluation Chairs,

As the Artifact Evaluation process for [Conference Name, e.g. NeurIPS / ICML / ACM SIGMOD] approaches, ensuring that reviewers can easily and deterministically verify submitted code artifacts is a common challenge.

We have developed SciProof (https://github.com/hayagrivai-labs/sciproof), an open-source, zero-dependency Python tool (archived on Zenodo: 10.5281/zenodo.23676138) specifically designed for reproducible computational experiments and artifact review.

We have authored an open-source, turnkey Artifact Evaluation Appendix Template:
https://github.com/hayagrivai-labs/sciproof/blob/main/docs/ARTIFACT_EVALUATION_TEMPLATE.md

Authors can include this template in their repository to give reviewers:
1. Single-command offline verification: `sciproof verify manifest.sciproof.json`
2. Sandboxed re-execution with calibrated numerical tolerances: `sciproof verify --rerun`
3. Direct verification of Table/Figure values mapped to paper claims.

We would be delighted if this template proves helpful to authors and reviewers submitting artifacts to [Conference Name].

Best regards,
Alok Pandey
HayagrivAI Labs (https://hayagrivai-labs.github.io/sciproof/)
```
