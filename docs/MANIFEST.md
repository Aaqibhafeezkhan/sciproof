# Manifest format (schema version 1.0)

A manifest is a UTF-8 JSON file named `<name>.sciproof.json`, written next to the files it
describes (its directory is the *base directory*). All paths inside it are relative to that
directory, use `/` as separator and may not contain `..`, drive letters or absolute roots.

Unknown *minor* versions (`1.x`) are read; an unknown *major* version is rejected.
Manifests are validated strictly when read (see `src/sciproof/manifest.py`), because they are
untrusted input.

```jsonc
{
  "schema": "sciproof.manifest",
  "schema_version": "1.0",
  "name": "baseline",
  "created_at": "2026-10-17T18:47:12+00:00",
  "tool": {"name": "sciproof", "version": "0.1.0"},
  "command": {"argv": ["python", "examples/experiment.py"], "cwd": "."},
  "environment": {
    "source": "command-interpreter",          // or "sciproof-process"
    "python": {"version": "3.13.1", "implementation": "CPython", "byteorder": "little"},
    "platform": {"system": "...", "release": "...", "machine": "...", "platform": "..."},
    "env_vars": {"TZ": "UTC"}                 // allowlisted, non-secret variables only
  },
  "dependencies": [{"name": "pytest", "version": "9.1.1"}],
  "git": {"commit": "...", "branch": "main", "dirty": false},   // or null
  "inputs": [{"path": "examples/params.json", "sha256": "...", "size": 58}],
  "execution": {
    "exit_code": 0,
    "duration_seconds": 0.132,
    "stdout": {"sha256": "...", "size": 56, "truncated": false, "text": "..."},
    "stderr": {"sha256": "...", "size": 0, "truncated": false, "text": ""}
  },
  "outputs": [
    {"path": "examples/out/results.json", "present": true, "sha256": "...", "size": 69,
     "compare": {"mode": "exact"}},
    {"path": "examples/out/convergence.csv", "present": true, "sha256": "...", "size": 89,
     "compare": {"mode": "numeric", "rtol": 1e-09, "atol": 0.0,
                 "snapshot": {"path": "baseline.sciproof.d/1-convergence.csv", "sha256": "..."}}}
  ]
}
```

## Notes

* `command.argv` is the exact argument vector. It is never run through a shell.
* `environment.env_vars` contains only variables from a fixed allowlist
  (`PYTHONHASHSEED`, `TZ`, `LANG`, `LC_ALL`, thread-count variables, `CUDA_VISIBLE_DEVICES`).
  Everything else in the environment, including secrets, is never recorded.
* `git` stores the commit, branch and whether the working tree had uncommitted or untracked
  changes *before* the run. Remote URLs are not stored because they can contain credentials.
* `stdout`/`stderr` keep the SHA-256 and size of the full stream but only the first
  `--max-log-bytes` bytes of text. Review them for secrets before sharing a manifest.
* Numeric outputs have a copy ("snapshot") in `<name>.sciproof.d/`, because a hash cannot be
  compared with a tolerance. The snapshot is itself hash-protected by the manifest. Keep that
  directory together with the manifest.
* A manifest is **not signed**. Anyone who can change both a manifest and the files it lists
  can produce consistent but false evidence. See [SECURITY.md](../SECURITY.md).
