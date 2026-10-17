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

## Field reference

Every field of a manifest. Array entries are written as `[]`.

| Field | Meaning |
| --- | --- |
| `schema` | Always `sciproof.manifest`. |
| `schema_version` | Format version. Readers accept every `1.x` and reject other major versions. |
| `name` | The experiment name given with `--name` (letters, digits, `.`, `_`, `-`, at most 100 characters). It also names the manifest file. |
| `created_at` | UTC time at which the manifest was written, which is after the command finished. |
| `tool` | Name and version of the SciProof that wrote the manifest. |
| `command.argv` | The exact argument vector of the recorded command. It is never run through a shell. |
| `command.cwd` | Always `.`: the command runs in the directory that contains the manifest. |
| `environment.source` | `command-interpreter` if the command was a Python interpreter that was asked for its own version and packages, otherwise `sciproof-process` (the interpreter running SciProof). |
| `environment.python` | Python version, implementation and byte order. |
| `environment.platform` | Operating system name, release, machine type and platform string. |
| `environment.env_vars` | Values of a fixed allowlist of non-secret environment variables that were set at capture time. |
| `dependencies` | Name and version of every package installed for that interpreter. |
| `git` | Commit, branch and whether the working tree had uncommitted or untracked changes before the run; `null` outside a Git repository. |
| `inputs` | Declared input files. |
| `inputs[].path` | Path relative to the manifest directory, using `/`. |
| `inputs[].sha256` | SHA-256 of the file as it was before and after the run. |
| `inputs[].size` | Size in bytes. |
| `execution.exit_code` | Exit status of the recorded run. A nonzero status is recorded, not hidden. |
| `execution.duration_seconds` | Wall-clock duration of the run. |
| `execution.stdout` | Standard output: SHA-256 and size of the full stream, and the first bytes as text. |
| `execution.stderr` | Standard error, recorded like `stdout`. |
| `outputs` | Declared output files. |
| `outputs[].path` | Path relative to the manifest directory. |
| `outputs[].present` | Whether the file existed after the run. |
| `outputs[].sha256` | SHA-256 of the output, or `null` if it was absent. |
| `outputs[].size` | Size in bytes. |
| `outputs[].compare` | How a rerun is compared with this output: `exact` (hash) or `numeric` (tolerance). |
| `outputs[].compare.mode` | `exact` or `numeric`. |
| `outputs[].compare.rtol` | Relative tolerance of a numeric output. |
| `outputs[].compare.atol` | Absolute tolerance of a numeric output. |
| `outputs[].compare.snapshot` | Path and SHA-256 of the copy of the output in `NAME.sciproof.d/`, which is compared with the rerun. |

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
