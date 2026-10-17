"""Noisy linear regression with NumPy and pandas (used by docs/TUTORIAL_NUMPY_PANDAS.md).

Usage (from the repository root):
    python examples/numpy_pandas/experiment.py PARAMS_JSON OUTPUT_DIR
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> int:
    params = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    # One explicit, seeded generator. Never rely on global random state.
    rng = np.random.default_rng(params["seed"])
    x = np.linspace(0.0, 10.0, params["n_points"])
    y = params["slope"] * x + params["intercept"] + rng.normal(0.0, params["noise"], x.size)

    slope, intercept = np.polyfit(x, y, deg=1)
    frame = pd.DataFrame({"x": x, "y": y})
    frame["residual"] = frame["y"] - (slope * frame["x"] + intercept)

    # Write numbers with full precision so that a tolerance, not rounding, decides equivalence.
    frame.to_csv(out_dir / "data.csv", index=False, float_format="%.17g", lineterminator="\n")
    summary = {
        "n_points": int(x.size),
        "slope": float(slope),
        "intercept": float(intercept),
        "residual_std": float(frame["residual"].std()),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"fitted slope={slope:.4f} intercept={intercept:.4f} on {x.size} points")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
