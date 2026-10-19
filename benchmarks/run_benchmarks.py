"""Reproducible benchmark: eight verification scenarios, run end to end through the CLIs.

Usage (from the repository root, with SciProof installed):

    python benchmarks/run_benchmarks.py
    python benchmarks/run_benchmarks.py --json results.json --repeat 7

Every scenario starts in a fresh temporary directory with the same tiny deterministic
experiment (``data.json`` -> ``result.json``), so nothing outside that directory is touched. The
script prints a Markdown table and, with ``--json FILE``, writes the raw measurements. It exits
with 1 if SciProof gives an outcome other than the expected one.

What is measured: the verdict / exit code SciProof gives (accuracy against the expected
outcome) and wall-clock time (median of ``--repeat`` runs). What is not measured: memory,
large inputs, other platforms. Timings are for a ~0.1 s experiment on one machine and show
process start-up overhead, not scalability.
"""

from __future__ import annotations

import argparse
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
    parser.add_argument("--repeat", type=int, default=5, help="repetitions for the overhead table")
    parser.add_argument("--json", metavar="FILE", help="write raw measurements here")
    args = parser.parse_args()

    outcomes = sciproof_scenarios(SciProof())
    print(table(outcomes))
    print()
    print("\n".join(overhead(SciProof(), args.repeat)))
    if args.json:
        Path(args.json).write_text(json.dumps([asdict(o) for o in outcomes], indent=2))
    wrong = [o for o in outcomes if o.correct is False]
    print(f"\n{len(wrong)} unexpected outcome(s)")
    return 1 if wrong else 0


if __name__ == "__main__":
    raise SystemExit(main())
