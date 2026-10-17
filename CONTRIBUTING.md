# Contributing

Thanks for helping. SciProof is small on purpose; the most valuable contributions right now
are **real-world feedback** (does it fit how you run experiments?), bug reports with a minimal
manifest, and tests.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Checks (run these before opening a pull request)

```bash
ruff check .
ruff format --check .
python -m pytest
python examples/demo.py
```

CI runs the same on Python 3.11, 3.12 and 3.13 on Linux, Windows and macOS.

## Guidelines

* Python 3.11+, standard library only at runtime. A new dependency needs a strong reason.
* No network access, cloud accounts or telemetry. Everything must work offline.
* Treat manifests as untrusted input. Any new code path that reads a path or string from a
  manifest must validate it (see `paths.py`, `manifest.py`, `textutil.py`) and have a test.
  Never execute anything from `inspect` or plain `verify`.
* Be honest in messages and docs: do not claim more than a check shows (see
  `docs/CONCEPTS.md`).
* Add tests for behaviour changes, including failure cases. Do not weaken a test to make it pass.
* Keep pull requests focused. Explain *why*, not only *what*.

## Licence

By contributing you agree that your contribution is licensed under the MIT licence of this
project. MIT was chosen because it is short, permissive and well understood by universities and
companies, so researchers can use and embed the tool without legal review. If patent grants
become important, relicensing to Apache-2.0 can be discussed with all contributors.

## Conduct

See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security issues: see [SECURITY.md](SECURITY.md).
