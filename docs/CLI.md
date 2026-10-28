# Command Line Interface (CLI)

`sciproof` provides commands to record, inspect, verify, calibrate, and compare computational
experiments.

## Global options

* `--version`: Print the SciProof version and exit.
* `-q`, `--quiet`: Suppress decorative banners, progress notes, and headers. Only emit the final
  status summary on `stdout`, routing diagnostics and warnings to `stderr` if a failure occurs.

## Commands

### `verify`

Check that an evidence manifest matches current outputs:

```bash
sciproof verify baseline.sciproof.json
```

With `--quiet` / `-q`, header banners and check lists are omitted, producing minimal output on
`stdout`:

```bash
sciproof verify baseline.sciproof.json -q
# Output:
# RESULT: PASS
```

If verification fails or is inconclusive, failure diagnostics and reasons are written to `stderr`:

```bash
sciproof verify modified.sciproof.json -q
# stdout: RESULT: FAIL
# stderr: [FAIL] output out/result.json: modified since capture (SHA-256 differs)
```

### `record`

Automatically detect read inputs and produced outputs without declaring them:

```bash
sciproof record --name myrun -- python train.py
```

With `-q` / `--quiet`, verbose command recreation hints and declarations are suppressed:

```bash
sciproof record --name myrun -q -- python train.py
# Output:
# Evidence written to myrun.sciproof.json
```

### `calibrate`

Measure output variance over multiple re-runs to suggest tolerances:

```bash
sciproof calibrate baseline.sciproof.json --runs 5 --yes
```

With `-q` / `--quiet`:

```bash
sciproof calibrate baseline.sciproof.json --runs 5 --yes -q
# Output:
# RESULT: STABLE
```

### `diff`

Compare two evidence manifests:

```bash
sciproof diff baseline.sciproof.json updated.sciproof.json
```

With `-q` / `--quiet`:

```bash
sciproof diff baseline.sciproof.json updated.sciproof.json -q
# Output:
# RESULT: IDENTICAL
```

If differences are found, `RESULT: DIFFERENT` is output on `stdout` (exit code `1`) and a summary is
printed to `stderr`.

## Shell completion

SciProof supports tab completion for subcommands and long options via `argcomplete`:

```bash
python -m pip install "sciproof[completion]"
eval "$(register-python-argcomplete sciproof)"
```
