"""Reproducible benchmark: eight verification scenarios, run end to end through the CLIs.

Usage (from the repository root, with SciProof installed):

    python benchmarks/run_benchmarks.py                     # SciProof only
    python benchmarks/run_benchmarks.py --reproledger PATH  # also ReproLedger, see below

Every scenario starts in a fresh temporary directory with the same tiny deterministic
experiment (``data.json`` -> ``result.json``), so tools are compared on equivalent tasks and
nothing outside that directory is touched. The script prints a Markdown table and, with
``--json FILE``, writes the raw measurements.

``--reproledger PATH`` takes the path to a ``reproledger`` executable that you installed
yourself (for example ``pip install`` of https://github.com/Alqudimi/reproledger in a separate
virtual environment). It is never installed or downloaded by this script.

What is measured: the verdict / exit code each tool gives (accuracy against the expected
outcome) and wall-clock time (median of ``--repeat`` runs). What is not measured: memory,
large inputs, other platforms. Timings are for a ~0.1 s experiment on one machine and show
process start-up overhead, not scalability.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import statistics
import subprocess  # noqa: S404
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

EXPERIMENT = """\
import json, os, pathlib
data = json.loads(pathlib.Path("data.json").read_text())
eps = float(os.environ.get("BENCH_EPS", "0"))
pathlib.Path("result.json").write_text(json.dumps({"value": data["x"] * 2 + eps, "label": "ok"}))
print("done")
"""
SLEEPER = "import time; time.sleep(30)"


@dataclass
class Outcome:
    scenario: str
    tool: str
    expected: str
    observed: str
    exit_code: int | None
    seconds: float
    note: str = ""

    @property
    def correct(self) -> bool | None:
        if self.observed == "unsupported":
            return None
        return self.observed == self.expected


def run(argv: list[str], cwd: Path, env: dict[str, str] | None = None) -> tuple[int, float, str]:
    started = time.perf_counter()
    completed = subprocess.run(  # noqa: S603
        argv,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    return completed.returncode, time.perf_counter() - started, completed.stdout + completed.stderr


def fresh_project() -> Path:
    root = Path(tempfile.mkdtemp(prefix="sciproof-bench-"))
    (root / "experiment.py").write_text(EXPERIMENT)
    (root / "data.json").write_text('{"x": 21}')
    return root


# ------------------------------------------------------------------------------------------
# SciProof adapter
# ------------------------------------------------------------------------------------------

SCIPROOF_VERDICTS = {0: "PASS", 1: "FAIL", 2: "INCONCLUSIVE", 3: "ERROR"}


class SciProof:
    name = "sciproof"

    def __init__(self) -> None:
        self.cmd = [sys.executable, "-m", "sciproof"]

    def capture(self, root: Path, *, rtol: str = "1e-6", extra: list[str] | None = None) -> int:
        code, _, _ = run(
            [
                *self.cmd,
                "capture",
                "--name",
                "exp",
                "--input",
                "data.json",
                "--input",
                "experiment.py",
                "--output-numeric",
                "result.json",
                "--rtol",
                rtol,
                *(extra or []),
                "--",
                sys.executable,
                "experiment.py",
            ],
            root,
        )
        return code

    def verify(self, root: Path, *, rerun: bool = False, env: dict[str, str] | None = None):
        argv = [*self.cmd, "verify", "exp.sciproof.json"]
        if rerun:
            argv += ["--rerun", "--yes"]
        code, seconds, text = run(argv, root, env)
        return SCIPROOF_VERDICTS.get(code, f"exit {code}"), code, seconds, text


# ------------------------------------------------------------------------------------------
# ReproLedger adapter (only integrity and exit status are comparable; see the docs)
# ------------------------------------------------------------------------------------------


class ReproLedger:
    name = "reproledger"

    def __init__(self, executable: str) -> None:
        self.cmd = [executable]

    def capture(self, root: Path) -> tuple[int, str]:
        run([*self.cmd, "init"], root)
        code, _, text = run(
            [
                *self.cmd,
                "run",
                "--input",
                "data.json",
                "--input",
                "experiment.py",
                "--output",
                "result.json",
                "--",
                sys.executable,
                "experiment.py",
            ],
            root,
        )
        run_id = ""
        with contextlib.suppress(ValueError, KeyError):
            run_id = json.loads(text)["run_id"]
        return code, run_id

    def verify(self, root: Path, run_id: str):
        code, seconds, text = run([*self.cmd, "verify", run_id], root)
        verdict = {0: "PASS", 4: "FAIL", 3: "ERROR", 5: "ERROR"}.get(code, f"exit {code}")
        return verdict, code, seconds, text


# ------------------------------------------------------------------------------------------
# scenarios
# ------------------------------------------------------------------------------------------

Scenario = tuple[str, str, Callable]


def sciproof_scenarios(tool: SciProof) -> list[Outcome]:
    results: list[Outcome] = []

    def add(name, expected, verdict, code, seconds, note=""):
        results.append(Outcome(name, tool.name, expected, verdict, code, seconds, note))

    # 1. unchanged
    root = fresh_project()
    tool.capture(root)
    add("1 unchanged experiment", "PASS", *tool.verify(root)[:3])
    # 1b. unchanged, with a rerun
    verdict, code, seconds, _ = tool.verify(root, rerun=True)
    add("1b unchanged, rerun", "PASS", verdict, code, seconds)
    shutil.rmtree(root, ignore_errors=True)

    # 2. modified input
    root = fresh_project()
    tool.capture(root)
    (root / "data.json").write_text('{"x": 22}')
    add("2 modified input", "FAIL", *tool.verify(root)[:3])
    shutil.rmtree(root, ignore_errors=True)

    # 3. modified output
    root = fresh_project()
    tool.capture(root)
    (root / "result.json").write_text('{"value": 999, "label": "ok"}')
    add("3 modified output", "FAIL", *tool.verify(root)[:3])
    shutil.rmtree(root, ignore_errors=True)

    # 4 / 5. numeric output within / outside the declared tolerance (needs a rerun)
    for number, eps, expected in (
        ("4 within tolerance", "1e-9", "PASS"),
        ("5 outside", "1e-2", "FAIL"),
    ):
        root = fresh_project()
        tool.capture(root, rtol="1e-6")
        verdict, code, seconds, _ = tool.verify(root, rerun=True, env={"BENCH_EPS": eps})
        add(f"{number} (eps={eps})", expected, verdict, code, seconds)
        shutil.rmtree(root, ignore_errors=True)

    # 6. missing required evidence
    root = fresh_project()
    tool.capture(root)
    (root / "data.json").unlink()
    add("6 missing required input", "INCONCLUSIVE", *tool.verify(root)[:3])
    shutil.rmtree(root, ignore_errors=True)

    # 7. malformed / tampered manifest
    root = fresh_project()
    tool.capture(root)
    manifest = root / "exp.sciproof.json"
    text = manifest.read_text()
    manifest.write_text(text[: len(text) // 2])
    add("7a truncated manifest", "ERROR", *tool.verify(root)[:3])
    manifest.write_text(text.replace('"exit_code": 0', '"exit_code": 0, "exit_code": 1', 1))
    add("7b manifest with a repeated key", "ERROR", *tool.verify(root)[:3])
    data = json.loads(text)
    data["outputs"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(data, indent=2))
    add("7c manifest hash edited to a wrong value", "FAIL", *tool.verify(root)[:3])
    shutil.rmtree(root, ignore_errors=True)

    # 8. failed / timed-out execution
    root = fresh_project()
    (root / "fail.py").write_text("import sys; sys.exit(3)")
    code, seconds, _ = run(
        [
            *tool.cmd,
            "capture",
            "--name",
            "f",
            "--input",
            "data.json",
            "--",
            sys.executable,
            "fail.py",
        ],
        root,
    )
    add(
        "8a command fails at capture",
        "FAIL",
        "FAIL" if code == 1 else f"exit {code}",
        code,
        seconds,
        "evidence is still written: " + str((root / "f.sciproof.json").exists()),
    )
    (root / "sleep.py").write_text(SLEEPER)
    code, seconds, _ = run(
        [
            *tool.cmd,
            "capture",
            "--name",
            "t",
            "--input",
            "data.json",
            "--timeout",
            "1",
            "--",
            sys.executable,
            "sleep.py",
        ],
        root,
    )
    add(
        "8b capture timeout",
        "ERROR",
        "ERROR" if code == 3 else f"exit {code}",
        code,
        seconds,
        "no evidence written: " + str(not (root / "t.sciproof.json").exists()),
    )
    shutil.rmtree(root, ignore_errors=True)
    return results


def reproledger_scenarios(tool: ReproLedger) -> list[Outcome]:
    results: list[Outcome] = []

    def add(name, expected, verdict, code, seconds, note=""):
        results.append(Outcome(name, tool.name, expected, verdict, code, seconds, note))

    def unsupported(name, expected, why):
        results.append(Outcome(name, tool.name, expected, "unsupported", None, 0.0, why))

    root = fresh_project()
    _, run_id = tool.capture(root)
    add("1 unchanged experiment", "PASS", *tool.verify(root, run_id)[:3])
    unsupported("1b unchanged, rerun", "PASS", "no rerun: 'replay' only prints a plan")
    shutil.rmtree(root, ignore_errors=True)

    root = fresh_project()
    _, run_id = tool.capture(root)
    (root / "data.json").write_text('{"x": 22}')
    add("2 modified input", "FAIL", *tool.verify(root, run_id)[:3])
    shutil.rmtree(root, ignore_errors=True)

    root = fresh_project()
    _, run_id = tool.capture(root)
    (root / "result.json").write_text('{"value": 999, "label": "ok"}')
    add("3 modified output", "FAIL", *tool.verify(root, run_id)[:3])
    shutil.rmtree(root, ignore_errors=True)

    unsupported("4 within tolerance", "PASS", "no numeric tolerance comparison and no rerun")
    unsupported("5 outside", "FAIL", "no numeric tolerance comparison and no rerun")

    root = fresh_project()
    _, run_id = tool.capture(root)
    (root / "data.json").unlink()
    verdict, code, seconds, text = tool.verify(root, run_id)
    add(
        "6 missing required input",
        "INCONCLUSIVE",
        verdict,
        code,
        seconds,
        "only PASS/FAIL exist: a missing file is reported as a failed check",
    )
    shutil.rmtree(root, ignore_errors=True)

    root = fresh_project()
    _, run_id = tool.capture(root)
    manifest = root / ".reproledger" / "runs" / run_id / "manifest.json"
    original = manifest.read_text()
    manifest.write_text(original[: len(original) // 2])
    add("7a truncated manifest", "ERROR", *tool.verify(root, run_id)[:3])
    manifest.write_text(original.replace('"exit_code": 0', '"exit_code": 1', 1))
    add("7c manifest edited (sidecar digest not updated)", "FAIL", *tool.verify(root, run_id)[:3])
    shutil.rmtree(root, ignore_errors=True)

    root = fresh_project()
    (root / "fail.py").write_text("import sys; sys.exit(3)")
    run([*tool.cmd, "init"], root)
    code, seconds, text = run(
        [*tool.cmd, "run", "--input", "data.json", "--", sys.executable, "fail.py"], root
    )
    recorded = '"status": "failed"' in text
    verdict = "FAIL" if code == 3 and recorded else f"exit {code}"
    add(
        "8a command fails at capture",
        "FAIL",
        verdict,
        code,
        seconds,
        f"evidence is still written: {recorded}",
    )
    unsupported("8b capture timeout", "ERROR", "the run command has no timeout option")
    shutil.rmtree(root, ignore_errors=True)
    return results


def table(outcomes: list[Outcome]) -> str:
    lines = [
        "| Scenario | Tool | Expected | Observed | Exit | Seconds | Note |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for o in outcomes:
        mark = "" if o.correct in (True, None) else " **(differs from expected)**"
        lines.append(
            f"| {o.scenario} | {o.tool} | {o.expected} | {o.observed}{mark} | "
            f"{'' if o.exit_code is None else o.exit_code} | {o.seconds:.2f} | {o.note} |"
        )
    return "\n".join(lines)


def overhead(tool: SciProof, repeat: int) -> list[str]:
    """Median wall-clock of the bare experiment vs capture vs verify vs verify --rerun."""
    plain, cap, ver, rer = [], [], [], []
    for _ in range(repeat):
        root = fresh_project()
        plain.append(run([sys.executable, "experiment.py"], root)[1])
        started = time.perf_counter()
        tool.capture(root)
        cap.append(time.perf_counter() - started)
        ver.append(tool.verify(root)[2])
        rer.append(tool.verify(root, rerun=True)[2])
        shutil.rmtree(root, ignore_errors=True)
    med = statistics.median
    return [
        f"median of {repeat} runs on this machine (seconds):",
        f"- bare experiment:          {med(plain):.3f}",
        f"- sciproof capture:         {med(cap):.3f}",
        f"- sciproof verify:          {med(ver):.3f}",
        f"- sciproof verify --rerun:  {med(rer):.3f}",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--reproledger", metavar="PATH", help="path to a reproledger executable")
    parser.add_argument("--repeat", type=int, default=5, help="repetitions for the overhead table")
    parser.add_argument("--json", metavar="FILE", help="write raw measurements here")
    args = parser.parse_args()

    outcomes = sciproof_scenarios(SciProof())
    if args.reproledger:
        outcomes += reproledger_scenarios(ReproLedger(args.reproledger))
    print(table(outcomes))
    print()
    print("\n".join(overhead(SciProof(), args.repeat)))
    if args.json:
        Path(args.json).write_text(json.dumps([asdict(o) for o in outcomes], indent=2))
    # Only SciProof's own outcomes can fail this script. A different design in another tool
    # (for example two verdicts instead of three) is shown in the table, not treated as an error.
    wrong = [o for o in outcomes if o.correct is False and o.tool == "sciproof"]
    other = [o for o in outcomes if o.correct is False and o.tool != "sciproof"]
    print(f"\n{len(wrong)} unexpected SciProof outcome(s); {len(other)} other-tool difference(s)")
    return 1 if wrong else 0


if __name__ == "__main__":
    raise SystemExit(main())
