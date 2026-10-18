# Releasing to PyPI

A version number can be uploaded to PyPI only once (even if the release is deleted later), so
rehearse on TestPyPI first.

## One-time setup (maintainer)

1. PyPI account with 2FA on pypi.org, and a separate one on test.pypi.org.
2. On each site add a **pending publisher** (Account > Publishing): project `sciproof`, owner
   `hayagrivai-labs`, repository `sciproof`, workflow `publish.yml`, environment `pypi` (PyPI) or
   `testpypi` (TestPyPI).
3. In GitHub: Settings > Environments, create `pypi` and `testpypi`. Add yourself as a required
   reviewer if each release should need an approval.

No API token is created or stored anywhere.

## Each release

1. Update `version` in `pyproject.toml` and `__version__` in `src/sciproof/__init__.py`; CI green.
2. Rehearsal: Actions > Publish > Run workflow (publishes to TestPyPI). Check it in a clean venv:
   `pip install --index-url https://test.pypi.org/simple/ --no-deps sciproof` then
   `sciproof --version`.
3. Create a GitHub release with tag `vX.Y.Z`; publishing the release uploads to PyPI.
4. Check `pipx install sciproof` and `sciproof --version`.

Local check before tagging: `python -m build && twine check dist/*`.
