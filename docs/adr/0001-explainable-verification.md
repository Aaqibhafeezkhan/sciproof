# ADR 0001: Explainable verification, strict parsing, conservative defaults

* Status: accepted, 2026-10-18
* Context documents: [Baseline audit](../BASELINE_AUDIT.md), [Competitive analysis](../COMPETITIVE_ANALYSIS.md),
  [Product roadmap](../PRODUCT_ROADMAP.md)

## Context

The audit found that a `verify` verdict could not be audited from its output: the JSON report had
no schema name or version, no evidence behind each check, no statement of why the verdict was
chosen, and no machine-readable list of what had not been established (BASELINE_AUDIT F4). It
also found two places where ambiguous input was accepted silently (repeated JSON keys, F1) and
one setting that silently defeats the purpose of a tolerance (`rtol >= 1`, F3).

SciProof's value rests on never claiming more than a check shows, so each of these is a defect
in the product, not a nicety.

## Decisions

### 1. Extend the report additively and version it

`verify --json` now carries `schema: "sciproof.report"` and `schema_version: "1.0"`, per-check
`evidence`, a `reason`, `counts`, `rerun_executed` and `not_checked`. The text report gets a
`basis:` line and `not checked:` lines before the final `RESULT:` line.

* **Why additive:** existing scripts read `result`, `checks[].status|subject|message` and the exit
  code. None of those change. New fields are allowed within `1.x`; removal or redefinition needs
  `2.0`.
* **Why the "not checked" list is part of every report, including `PASS`:** a green result
  invites over-reading. The list says, in the report itself, that the command was not executed
  (unless it was), that scientific validity is not addressed, that undeclared files are out of
  scope and that the unsigned manifest does not authenticate its author.
* **Why `evidence` carries digests and the tolerance rule:** a reader can audit a check without
  re-running anything, and a CI system can show the key that moved.
* **Rejected:** replacing the report with a new format (breaks callers); adding a separate
  `explain` command (the explanation belongs with the verdict, not behind another command).

### 2. Aggregation stays conservative and is stated

`FAIL` if any check failed; otherwise `INCONCLUSIVE` if any check could not be performed or none
was performed; otherwise `PASS`. This is the behaviour that existed; the decision is to document
it as a rule and print the rule that applied (`reason`). A single `FAIL` outweighs
`INCONCLUSIVE` because a contradiction is information even when other checks are impossible.

### 3. Refuse ambiguous JSON instead of picking a value

A repeated key in an object is an error in manifests and in numeric output files
(`jsonstrict.reject_duplicate_keys` as `object_pairs_hook`).

* **Why:** parsers disagree about which value wins, and the discarded value can never be
  compared, so the same bytes could mean different evidence to different readers.
* **Compatibility:** SciProof never writes a repeated key, so valid existing manifests are
  unaffected. A numeric output that a program writes with repeated keys is now rejected at capture
  time, with a message naming the key.
* **Rejected:** keeping the last value and warning (still ambiguous, easy to miss); implementing
  "first wins" (also arbitrary).

### 4. Warn, do not reject, on `rtol >= 1`

The tolerance rule `|a-b| <= max(rtol*max(|a|,|b|), atol)` with `rtol >= 1` makes every number
equivalent to 0, and with `rtol >= 2` equivalent to its negative. `capture` prints a warning.

* **Why not reject:** some existing manifests could use such values, and there are legitimate
  order-of-magnitude comparisons. A warning keeps compatibility and removes the surprise.
* **Revisit if:** user testing shows the warning is ignored.

### 5. Keep the integer rule, document it

Two JSON integers are compared exactly even with a tolerance; CSV numbers always use it. Changing
this would hide differences above 2^53 or change verdicts of existing manifests. It is documented
in [COMPARISON.md](../COMPARISON.md) and pinned by tests.

### 6. Do not describe a subprocess as a sandbox

The audit confirmed the rerun hands the complete parent environment to the command (F6).
`SECURITY.md` now says so. A clean-environment option is planned, not shipped, and even then the
rerun is not isolated.

## Consequences

* Reports are larger (digests and tolerance rule per check). They remain small for the intended
  use of a handful of declared files.
* Anything that parses the text report line by line must tolerate the new `basis:` and
  `not checked:` lines. The `RESULT:` line is still last.
* The evidence kinds (`input_integrity`, `output_integrity`, `snapshot_integrity`,
  `rerun_output_exact`, `rerun_output_numeric`, `exit_code`) are now part of the documented report
  schema and must not be renamed without a version bump.
