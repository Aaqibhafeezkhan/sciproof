"""End-to-end demo: capture, verify, re-execute and detect a modified output.

Run from anywhere:  python examples/demo.py

It works in a temporary directory, so nothing in your checkout is changed. The script exits
with status 0 only if SciProof behaved as documented at every step.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sciproof(workdir: Path, *args: str, expect: int) -> str:
    print(f"\n$ sciproof {' '.join(args)}")
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "sciproof", *args],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=False,
    )
    print(completed.stdout + completed.stderr, end="")
    print(f"(exit status {completed.returncode}, expected {expect})")
    if completed.returncode != expect:
        raise SystemExit(f"unexpected exit status {completed.returncode} for: {args}")
    return completed.stdout


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="sciproof-demo-") as tmp:
        work = Path(tmp)
        (work / "examples").mkdir()
        for name in ("experiment.py", "params.json"):
            shutil.copy(HERE / name, work / "examples" / name)

        print("== 1. Capture: run the experiment once and record evidence ==")
        sciproof(
            work,
            "capture",
            "--name",
            "baseline",
            "--input",
            "examples/experiment.py",
            "--input",
            "examples/params.json",
            "--output",
            "examples/out/results.json",
            "--output-numeric",
            "examples/out/convergence.csv",
            "--rtol",
            "1e-9",
            "--",
            sys.executable,
            "examples/experiment.py",
            expect=0,
        )

        print("\n== 2. Inspect: read the evidence without running anything ==")
        sciproof(work, "inspect", "baseline.sciproof.json", expect=0)

        print("\n== 3. Verify integrity: files still match the evidence ==")
        sciproof(work, "verify", "baseline.sciproof.json", expect=0)

        print("\n== 4. Verify by re-execution (explicit opt-in) ==")
        sciproof(work, "verify", "baseline.sciproof.json", "--rerun", "--yes", expect=0)

        print("\n== 5. Deliberately modify an output: verification must detect it ==")
        results = work / "examples" / "out" / "results.json"
        results.write_text(results.read_text().replace("3.1", "3.2", 1))
        sciproof(work, "verify", "baseline.sciproof.json", expect=1)

    print("\nDemo finished: success was verified and the modified output was detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
