# Listing manifests and exporting them

## `sciproof list`: the directory is the ledger

There is no database. A manifest is a file, so a directory of manifests is the history of your
experiments.

```bash
sciproof list                 # the manifests in the current directory, newest first
sciproof list -r results/     # also in subdirectories (hidden directories are skipped)
sciproof list --check         # verify every manifest (integrity only, nothing is executed)
```

```
  candidate.sciproof.json  captured 2026-10-19T05:37:44+00:00  exit 0  in 2  out 1  claims 0  PASS
  baseline.sciproof.json   captured 2026-10-19T05:37:43+00:00  exit 0  in 2  out 1  claims 0  FAIL

summary: 2 manifest(s): 1 PASS, 1 FAIL
```

Each line shows the capture time, the exit code of the recorded run, the number of inputs, outputs
and claims, whether a `.sig` file sits next to it, and the Git commit (with `+dirty` if the tree had
uncommitted changes). A file that is not a valid manifest is listed as `INVALID` with the reason;
it does not stop the listing. Symbolic links are not followed, and at most 1,000 manifests are
read.

With `--check`, the exit status is the worst result: `0` if all `PASS`, `1` if any `FAIL` or is
invalid, `2` if any is `INCONCLUSIVE`. This makes `sciproof list --check` a one-line check of every
recorded experiment in a repository. `--format json` and `--format markdown` are available.

## `sciproof export`: for other tools

```bash
sciproof export baseline.sciproof.json -o baseline.intoto.json
```

writes the manifest as an [in-toto Statement v1](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md):

* `subject`: the output files with their SHA-256 (the files of a directory output are listed as
  `dir/file`; outputs that were absent are left out).
* `predicateType`: `https://hayagrivai-labs.github.io/sciproof/docs/export/#experiment-v1`, a type
  defined by SciProof. It does not claim to be SLSA provenance: SciProof records an experiment, not
  a build.
* `predicate`: the experiment name and capture time, the SHA-256 of the manifest file, the command,
  exit code and duration, the inputs (`materials`) with their hashes, Python, platform, recorded
  environment variables and packages, the Git state, how each output is compared (`exact` or the
  numeric tolerance), and the claims as text.

**The Statement is not signed and is not an attestation by itself.** In-toto Statements are
normally wrapped in a signed envelope (DSSE) by the tool that attests them; that step is left to
such a tool, and `sciproof sign` signs the manifest itself. The Statement keeps the hashes but not
the verdict: run `sciproof verify` on the manifest for that.

```bash
sciproof export baseline.sciproof.json --format openlineage
```

writes the run as two [OpenLineage](https://openlineage.io/) run events, `START` and then
`COMPLETE` (or `FAIL` if the recorded command failed), as a JSON array:

* `run.runId` is a UUID (version 5) derived from the SHA-256 of the manifest, so exporting the
  same manifest again gives the same run; `eventTime` of the end is the capture time and the start
  is that minus the recorded duration (derived, not measured separately).
* `job` is `{namespace: "sciproof", name: <experiment name>}`.
* `inputs` and `outputs` are datasets in the namespace `sciproof-files`, named by their path
  relative to the manifest's directory; a directory is one dataset, and outputs that were absent
  are left out.
* `schemaURL` is the one shown in the OpenLineage specification's own run event example.

This is **lineage only**: which files were read and written, and whether the command succeeded. It
carries no hashes and no verdict, because no standard facet for them was verified; use the in-toto
export or the manifest for that.

An export to RO-Crate (Process Run Crate) is not implemented; see the
[design note](DESIGN_RO_CRATE.md) for the open questions.

## Python

```python
import sciproof

for entry in sciproof.list_manifests("results", recursive=True, check=True):
    print(entry.file, entry.verdict)
statement = sciproof.export_in_toto("baseline.sciproof.json")  # a dict
events = sciproof.export_openlineage("baseline.sciproof.json")  # a list of two dicts
```
