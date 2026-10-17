"""A small deterministic experiment used to demonstrate SciProof.

It estimates pi by Monte Carlo sampling with a fixed seed. The pseudo-random generator is
the standard library's Mersenne Twister, so the result is repeatable on the same Python
version; it is *not* guaranteed to be bitwise identical on every platform (see docs/CONCEPTS.md).

Usage (from the repository root):
    python examples/experiment.py [path/to/params.json] [output-directory]
"""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path


def estimate_pi(seed: int, samples: int, checkpoints: int) -> tuple[float, list[tuple[int, float]]]:
    rng = random.Random(seed)
    inside = 0
    history = []
    step = max(1, samples // checkpoints)
    for i in range(1, samples + 1):
        x, y = rng.random(), rng.random()
        if x * x + y * y <= 1.0:
            inside += 1
        if i % step == 0:
            history.append((i, 4.0 * inside / i))
    return 4.0 * inside / samples, history


def main() -> int:
    params_path = Path(sys.argv[1] if len(sys.argv) > 1 else "examples/params.json")
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "examples/out")
    params = json.loads(params_path.read_text(encoding="utf-8"))

    estimate, history = estimate_pi(params["seed"], params["samples"], params["checkpoints"])

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(
        json.dumps(
            {"seed": params["seed"], "samples": params["samples"], "pi_estimate": estimate},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    with (out_dir / "convergence.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["samples", "pi_estimate"])
        writer.writerows(history)

    print(
        f"pi is approximately {estimate:.6f} ({params['samples']} samples, seed {params['seed']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
