# Comparing two recorded runs: `sciproof diff`

```bash
sciproof diff baseline.sciproof.json candidate.sciproof.json
```

A metric moved. Was it the command, the inputs, the Git state or the environment? `diff` compares
two manifests and lists what is different. **It executes nothing** and reads only the two
manifests and the snapshot copies of numeric outputs that they reference. Both manifests are
validated like any other.

A difference in the command, an input or the environment is a *possible explanation* of a changed
output, not proof of the cause. The report says so.

## What is compared

| Section | Compared |
| --- | --- |
| `command` | the exact argument vector |
| `environment` | Python version and implementation; platform system, machine and release; the hardware record (CPU count, processor, GPUs) if both manifests have one; the recorded environment variables; every installed package (added, removed, version changed; names are matched case-insensitively) |
| `note` | the free-text note (added, removed or changed) |
| `git` | the commit and whether the working tree had uncommitted changes |
| `inputs` | declared files and directories: added, removed, content changed; for a directory, which files were added, removed or modified |
| `outputs` | the same, plus whether the output was present and how it is compared; numeric outputs are compared **numerically** (below) |
| `execution` | the exit code; whether stdout or stderr differ (informational) |

Not compared: the creation time, the duration, the version of SciProof that wrote the manifest and
the name.

## Numeric outputs

When a numeric output (`--output-numeric`) has a different hash in the two manifests, `diff`
compares the two recorded snapshots with the tolerance of the **old (baseline) manifest** and says
whether the change is

* `numerically equivalent within the baseline tolerance (rtol=..., atol=...)`: noise, by the
  tolerance you declared, or
* `outside the baseline tolerance`: with the first difference and its location; the JSON report
  carries every difference with its recorded and found value, absolute and relative difference and
  the difference the tolerance would have allowed.

If a snapshot is missing or its hash no longer matches its manifest, `diff` says the numeric
comparison is not possible and why; it does not guess. The rules are in
[Numeric comparison](COMPARISON.md).

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | no difference (the two manifests describe the same command, environment, Git state, inputs, outputs and exit code) |
| `1` | at least one difference |
| `3` | a manifest cannot be read or is invalid |

## Output formats

`--format text` (default), `--format json` (or `--json`) and `--format markdown`. The JSON document
has `schema: "sciproof.diff"`, `schema_version: "1.0"`, `identical`, `summary`, `counts` per
section, `changes` (each with `section`, `kind` of `added`/`removed`/`changed`, `subject`, `message`
and structured `evidence`) and `notes`. It names the manifests by file name only, not by path.

Markdown output is meant for CI summaries; everything that comes from a manifest is escaped.

## Python

```python
import sciproof

report = sciproof.diff_manifests("baseline.sciproof.json", "candidate.sciproof.json")
if not report.identical:
    print(report.summary)
    for change in report.changes:
        print(change.section, change.subject, change.message)
```
