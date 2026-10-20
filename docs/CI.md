# Using SciProof in CI

A manifest committed next to your results lets a CI job re-check them. The job below verifies
**integrity only**: nothing recorded in the manifest is executed.

```yaml
name: evidence
on: [pull_request]

permissions:
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install SciProof
        run: python -m pip install "git+https://github.com/hayagrivai-labs/sciproof.git"
      - name: Verify the evidence
        run: sciproof verify baseline.sciproof.json --json | tee verify.json
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: verify-report
          path: verify.json
```

The job fails when the verdict is `FAIL` (exit code `1`), `INCONCLUSIVE` (`2`) or the manifest
is invalid (`3`); see [Exit codes](EXIT_CODES.md). With `--json` the report on stdout is a single
JSON object with `name`, `result`, `checks`, `warnings` and `notes`.

> Pin the actions you use to a commit SHA if your organisation requires it. The versions above
> only illustrate the shape of the workflow.

## Re-running in CI

`sciproof verify --rerun --yes` **executes the command recorded in the manifest** with the
permissions of the job. Only do this for manifests you trust, for example ones committed by your
own team to a protected branch.

* Do not use `pull_request_target` or any trigger that gives untrusted code a privileged token.
  A manifest from a pull request contains a command chosen by its author.
* Keep `permissions` minimal (`contents: read`) and expose no secrets to the job.
* Add `--strict-env` if a rerun on a different Python version or platform should be reported as
  `INCONCLUSIVE` instead of being attempted.
* Add `--clean-env` so the recorded command receives only a minimal environment. Without it the
  command sees every variable of the job, including any token you exposed. Pass what it
  really needs with `--pass-env NAME`. This does not restrict files or network access.

```yaml
      - name: Re-execute the recorded command (trusted manifests only)
        run: sciproof verify baseline.sciproof.json --rerun --yes --strict-env --clean-env --json
```

## Showing the result in the job summary

`--format markdown` writes the report as Markdown, with a table of the numeric differences, which
GitHub shows on the run page when it is appended to `$GITHUB_STEP_SUMMARY`. The exit code is
unchanged, so the step still fails on `FAIL` or `INCONCLUSIVE` and the summary is written either way.

```yaml
      - name: Verify the recorded experiment
        run: sciproof verify baseline.sciproof.json --format markdown >> "$GITHUB_STEP_SUMMARY"
```

To see what changed between the committed baseline and a fresh capture, use
`sciproof diff baseline.sciproof.json candidate.sciproof.json --format markdown`.

Details: [Security and threat model](../SECURITY.md).
