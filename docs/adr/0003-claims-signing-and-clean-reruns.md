# ADR 0003: Claims, signatures and reruns that start clean

* Status: accepted, 2026-10-19
* Related: [ADR 0001](0001-explainable-verification.md), [Claims](../CLAIMS.md),
  [Signing](../SIGNING.md), [Concepts](../CONCEPTS.md)

## Context

The roadmap left three things open: a way to state what an experiment is supposed to show in a
form that can be checked, a way to know who vouches for a manifest, and the question of what a
successful rerun really demonstrates. Working on them turned up a defect in the last one.

## Decisions

### 1. A rerun starts without the old outputs

Before the command runs, the declared outputs are copied to a temporary backup and **deleted**.
Afterwards the usual logic applies: an identical result is left alone, a different one is moved to
`.sciproof-rerun-*` and the original is restored.

* **Why:** with the old files in place, a command that never wrote its output (a bug, a wrong path,
  an early exit) was compared with its own previous result and reported as reproduced. That is a
  false `PASS`, the kind of error the tool exists to prevent. It was reproduced by replacing the
  recorded command with a no-op.
* **Cost:** a command that skips work when its output already exists now does the work again, which
  is what a reproduction should do. A command that deliberately appends to its previous output is
  not reproducible by a clean rerun, and now says so.
* **Rejected:** comparing modification times (unreliable across file systems and copies); only
  warning about stale files (still a `PASS`).

### 2. Claims are mechanical, local and limited

A claim is `output`, `location`, `op`, `value` on a `.json` or `.csv` file, using the location
syntax of the difference reports. Seven operators; `~=` carries its own `rtol`/`atol`.

* **Why not richer expressions:** a claim language grows into a program that needs its own tests,
  security review and documentation. A comparison of one value covers the common case (a metric
  above a bound, a count equal to an expected value) and can be explained in one sentence.
* **Why recorded in the manifest:** it is then covered by the manifest hash and a signature, and
  `diff` can show a changed claim.
* **Judged twice:** on the recorded output, and (only with `--rerun`) on the rerun's output, so a
  claim is evidence about the reproduction too. On the recorded output it is only judged if the file
  still has its recorded hash, otherwise it is `INCONCLUSIVE`: a claim about a modified file says
  nothing about the evidence.
* **A failing claim is recorded, with a warning**, not refused: a failing result is also evidence.
* **Not interpreted:** every report that checks claims says a holding claim shows only that the
  value satisfies the comparison.
* **Rejected:** extracting claims from papers (needs models and cannot be checked mechanically);
  free-form Python expressions (code execution inside a verifier).

### 3. Signatures are a thin wrapper around `ssh-keygen`

`sciproof sign` and `verify --allowed-signers` call OpenSSH; SciProof implements no cryptography.
The trust root is the file the caller names, never the manifest. The signature is a detached
`<manifest>.sig` in a SciProof namespace. A missing signature is `INCONCLUSIVE`, a wrong one
`FAIL`, and a good one changes the "not checked" list from "unsigned" to "honesty of the
experiment is still not established".

* **Why OpenSSH:** it is installed on most developer machines, supports allowed-signers files and
  namespaces, and keeps SciProof free of dependencies and key management (see the
  [design note](../DESIGN_SIGNING.md) for the alternatives).
* **A trap that is handled:** `ssh-keygen -Y sign` keeps an existing `.sig` and exits 0 when it
  cannot ask whether to overwrite it. `sign` moves the old signature aside, so a new one is really
  written, and restores the old one if signing fails.
* **Not provided:** timestamps, revocation, key distribution.

### 4. `list` and `export` stay small

`list` reads the directory; there is no index to corrupt or synchronise. `list --check` is the
batch form of the integrity check, with the worst result as the exit status. `export` writes an
in-toto Statement v1 with a SciProof-defined predicate type, explicitly unsigned. An RO-Crate export
is not implemented because the profile's tool support was not verified (see the design note).

## Consequences

* Manifest schema 1.1 now also covers `claims`; manifests without directories or claims stay at 1.0.
* Reruns are slower by the time to delete and restore the outputs, and need disk space for the backup
  (as before).
* Existing manifests whose commands relied on a leftover output will now report `FAIL`. This is
  recorded in the changelog as a fix.
