# Product roadmap

Written on 2026-10-18 after the [baseline audit](BASELINE_AUDIT.md) and the
[competitive analysis](COMPETITIVE_ANALYSIS.md). Nothing here is a promise; priorities are
supposed to move when real users say something different.

## The hypothesis, and what the audit did to it

The hypothesis to test was: *SciProof can stand out through explainable, claim-aware verification
of computational experiments.*

* **"Explainable" survives.** No audited project reports, per check, the evidence it used, the
  rule that produced the verdict, and what was not established. This was missing in SciProof too,
  and is now implemented ([Report](REPORT.md)).
* **"Claim-aware" does not survive in the form first imagined.** Linking *scientific claims* to
  evidence is VeriRepro's territory (it starts from a paper's PDF and has a much larger
  machinery). SciProof records no claims and extracts none, and that is deliberate: a claim a
  tool cannot check mechanically is a claim it must not appear to endorse. The honest version is
  "**claim-limited**": every report states exactly what was and was not established.
* **The remaining differentiator is a combination, not a feature:** three-valued verdict with a
  conservative rule, declared numeric tolerances with stated semantics, a confirmed and timed
  rerun, and an explicit "not checked" list, with no runtime dependencies. This is true of the
  audited projects on one date and is **unproven with users**.

## Personas

These are composites to make trade-offs concrete. They are **not** interviewed users.

**1. Maya, PhD student (computational biology).** Her thesis figures come from a few Python
scripts and CSV data. Pain: a year later she cannot show that the data and scripts she archived
still produce the reported numbers; a reviewer asks and she re-runs by hand. Wants: one command
before submission, one command later, a plain answer, nothing to install or host.

**2. Dev, ML engineer on an evaluation team.** Metrics are written to JSON by a script that runs
in CI. Pain: a dependency bump moves a metric in the fourth decimal and nobody knows if that is
noise or a regression; "the diff is in a log somewhere". Wants: a tolerance written down once,
a CI step that returns an exit code, and a message that names the key that moved.

**3. Sam, artifact evaluator.** Receives a code archive with a manifest from a paper's authors.
Pain: running someone's command is risky and "it ran" proves little. Wants: to read exactly what
will run, to run it in a throw-away environment, and a verdict that says what it covers.

## Primary use case

Persona 2 is the sharpest: it needs the tolerance comparison and the exit-code contract, which
are the audited gaps in ReproLedger (no tolerance, no rerun) and DVC (no documented tolerance).
Persona 1 is the most numerous and is served by the same tool with a gentler path. Persona 3
depends on the safe-rerun work below.

> A script writes metrics. Capture it once; in CI, `sciproof verify --rerun --yes --json` fails
> when a declared output leaves its tolerance and says which value moved.

## Existing alternatives and why someone might still choose SciProof

| If you already use | You may not need SciProof, because | You may still choose SciProof because |
| --- | --- | --- |
| DVC | it hashes inputs and outputs and reruns stages | you do not want a pipeline system, and need tolerances and an explicit verdict (DVC documents none for `metrics diff`) |
| ReproLedger | it records evidence bundles and verifies integrity | you need a rerun, numeric tolerances, a third verdict (INCONCLUSIVE) or a timeout |
| MLflow | it tracks runs and artifacts | you want a check, not a tracker or a UI |
| ReproZip / containers | they capture the whole environment | you only need to check results, not rebuild the machine |
| VeriRepro | it reproduces a published paper's claims | you verify your own experiment and want no network, models or Docker |
| `pytest.approx` | it compares numbers in tests | you need the reference values recorded with their provenance |

## Candidate improvements, scored

Scores 1 (poor) to 5 (good); for maintenance burden and compatibility risk, 5 means *low* burden
or risk. "Diff." is verified differentiation against the audited projects.

| Candidate | User value | Diff. | Feasibility | Sci./security validity | Maintenance | Compat. | Adoption | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A. Evidence-backed reports (JSON schema, basis, not-checked) | 5 | 4 | 5 | 5 | 4 | 5 | 4 | **Done** |
| C. Numeric comparison audit (duplicate keys, labels, rtol warning, documented rules) | 4 | 4 | 5 | 5 | 5 | 4 | 4 | **Done** |
| E. Safe reruns: opt-in clean environment, documented limits | 4 | 3 | 4 | 5 | 4 | 5 | 3 | Next |
| G. Documented Python API alongside the CLI | 4 | 2 | 4 | 4 | 3 | 5 | 5 | Next |
| Directory artifacts (issue #5) | 4 | 2 | 3 | 4 | 3 | 4 | 4 | Next |
| B. Verification policy file | 3 | 4 | 3 | 4 | 2 | 4 | 3 | Wait for evidence |
| D. More provenance (resource metadata, config capture) | 3 | 2 | 4 | 3 | 3 | 4 | 3 | Wait for evidence |
| F. Portable evidence bundle | 3 | 3 | 2 | 4 | 2 | 3 | 3 | Wait; see [signing](DESIGN_SIGNING.md) and [RO-Crate](DESIGN_RO_CRATE.md) notes |

Reasoning for the two the audit pushed down: a policy file (B) adds a second configuration
surface before anyone has said that flags are not enough; richer provenance (D) is where
noWorkflow and ReproZip are strong and where SciProof would only be a weaker copy.

## The five highest-priority improvements

1. **Explainable reports.** Done in this change set: evidence per check, a `basis` sentence, a
   `not checked` list, `sciproof.report` schema 1.0.
2. **Trustworthy numeric comparison.** Done: duplicate keys refused, CSV column names in
   messages, a warning for `rtol >= 1`, exact rules published and tested.
3. **Safer reruns.** Open finding F6: a rerun hands the whole parent environment to the recorded
   command. Add an opt-in `--clean-env` (pass only an explicit allowlist) and keep saying plainly
   that nothing is sandboxed.
4. **A documented Python API.** `verify()` and `capture()` already exist. Export and document a
   small, stable surface (`verify_manifest(path) -> report dict`) so it can be used from pytest and
   notebooks. Persona 2 asked for CI first, notebooks second.
5. **Directory artifacts.** ReproLedger already hashes directories as sorted trees; many
   experiments write a directory of files, and `capture` currently refuses them.

## Explicitly excluded from the MVP

* Sandboxing or isolation claims. A subprocess is not a sandbox and will not be described as one.
* Reconstructing environments (containers, lock files): ReproZip, Nix and conda do that.
* A server, database, accounts, telemetry, dashboards, or any hosted component.
* Extracting or grading claims from papers; any model-assisted analysis.
* A new interchange standard. Export to RO-Crate or in-toto may come later if users ask.
* Cryptographic signing in the MVP; manifests are unsigned and every report says so.
* Fine-grained provenance inside a script (noWorkflow's territory).

## Validation plan with real users

The audit cannot show that anyone wants this. Before building items 3 to 5, test the claim.

1. **Recruit five people**: two research students or postdocs who run Python analyses, two ML or
   data engineers with a metric file in CI, one artifact-evaluation volunteer. Source: the
   repository's issues and discussions, and research-software communities. No incentives that
   would bias the answer.
2. **Task (30 minutes each, screen-shared, no coaching):** install from PyPI, capture one of
   their own scripts, change an input, verify, then break a tolerance on purpose. Record time to
   the first `PASS`, every point where they stopped, and which message they could not act on.
3. **Comprehension check:** after the session ask them to explain `INCONCLUSIVE` and what a
   `PASS` does not show. Count correct explanations.
4. **Adoption signal after two weeks:** are they still using it, did they put it in CI, what did
   they use before?
5. **Decision rule, written down in advance:** if fewer than three of the five complete the task
   unaided, or fewer than two say they would keep it over what they use now, treat the
   combination in the hypothesis as unvalidated and change direction (for example an exporter
   that adds tolerance verdicts to an existing tool) rather than adding features.
