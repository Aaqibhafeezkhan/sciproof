# ADR 0002: Directory artifacts

* Status: accepted, 2026-10-19
* Resolves the open questions of issue #5.
* Related: [ADR 0001](0001-explainable-verification.md), [MANIFEST.md](../MANIFEST.md#directories)

## Context

Many experiments write a directory of results, and until now every file had to be declared one by
one. DVC, the most widely used tool in the area, handles directories as a matter of course.
Issue #5 listed four open questions: the schema, symbolic links, size limits, and numeric
comparison inside directories.

## Decisions

### 1. Schema 1.1 with an optional `kind` field, written only when needed

An input or output item gets `"kind": "directory"` plus `files` (a sorted list of
`{path, sha256, size}`); items without `kind` are files, exactly as before. A manifest that
contains no directory keeps `schema_version` `1.0` and has the same format as 0.1.x wrote; one that
does is `1.1`. A `kind` in a `1.0` manifest is rejected.

* **Why not a separate field or a new top-level list:** verification already loops over `inputs`
  and `outputs`; one more attribute on the same items keeps every existing code path and report
  subject (`input X`, `output X`) unchanged.
* **Why bump only when needed:** nobody who does not use directories is affected, and the
  readers' rule ("read every `1.x`") still holds.
* **Cost:** SciProof 0.1.x reads a `1.1` manifest but misreports directories (an input is
  "unavailable", an output "missing"). It fails closed (never `PASS`), and this is stated in the
  docs.

### 2. The file list is stored, and the digest is checked against it

The manifest keeps every file's path, hash and size, not only a tree digest, and a reader
recomputes the digest and total size from the list.

* **Why:** only a list can say *which* files were added, removed or modified, which is the whole
  point for the user; a lone digest would give "differs" and nothing else. The recomputation makes
  the list and the digest impossible to edit independently.
* **Cost:** about 150 bytes per file in the manifest, bounded by decision 4.

### 3. Symbolic links and special files are refused, never followed or skipped

At capture the command fails with a message naming the entry; at verification the directory is
`FAIL` with the same reason.

* **Why not follow:** a link can point outside the project, so a "declared directory" could cover
  files the user never meant to include (and that other people's machines will not have).
* **Why not skip:** a skipped link could be swapped for a real file and the change would go
  unnoticed, which is exactly what the evidence is meant to prevent.
* **Why not record the link target:** it would add a second kind of evidence with its own
  platform differences (Windows) for a case nobody has asked for.
* The same applies to file names with a backslash or that are not valid UTF-8, because they cannot
  be written the same way on every system.

### 4. At most 10,000 files per directory; empty directories are not recorded

The limit keeps the manifest well below its 16 MiB limit and a scan fast; the error says to declare
a smaller directory or the files that matter. An empty directory has no content to compare, so it
is not evidence.

### 5. Exact comparison only

A directory cannot be an `--output-numeric` target, at capture and in a manifest. Numeric
comparison inside directories is a separate design question (which files, which tolerances, how to
pair them) with no demand yet.

### 6. A rerun restores a directory output as it restores a file

Before a rerun the original directory is copied to a temporary backup. Afterwards, if the result
is identical it is left alone; otherwise it is moved to `.sciproof-rerun-*` and the original is
restored. A directory the rerun created from nothing is moved aside too.

## Consequences

* Verification can name changed files, which makes reports more actionable than a digest mismatch.
* There are no ignore patterns. Directories containing caches (`__pycache__`) are noisy; the
  documentation says to declare narrower directories. Ignore patterns can be added later without
  changing the format only if they are recorded in the manifest, so they are deferred until
  someone needs them.
* The rerun backup doubles the disk use of a directory output for the duration of the rerun.
