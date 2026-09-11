"""Compare linear and shape-preserving radius interpolation for Q4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/common"))
sys.path.insert(0, str(ROOT / "code/q4"))

import model
from model import solve_radial
from problem4 import locate_event


def set_radius_interpolator(kind: str) -> None:
    if kind == "linear":
        model.RadialModel.radius = lambda self, t: (
            float(np.interp(t, self.radii[:, 0], self.radii[:, 1]) * 0.01)
            if self.shrink else self.r0
        )
        return
    if kind != "pchip":
        raise ValueError("插值方法必须为 linear 或 pchip")

    def radius(self, t):
        if not self.shrink:
            return self.r0
        if not hasattr(self, "_pchip_radius"):
            self._pchip_radius = PchipInterpolator(
                self.radii[:, 0], self.radii[:, 1], extrapolate=True
            )
        return float(self._pchip_radius(t) * 0.01)

    model.RadialModel.radius = radius


def run_case(kind: str, n: int) -> dict[str, float | str | int]:
    set_radius_interpolator(kind)
    solution = solve_radial(
        n, appendix=4, shrink=True, duration_s=72 * 3600,
        rtol=2e-7, atol=2e-9, max_step=300, align_environment=True,
    )
    event = locate_event(solution)
    return {"interpolator": kind, "n": n,
            "event_time_h": event["event_time_h"],
            "event_time_s": event["event_time_s"]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/q4/interpolation_sensitivity.json")
    parser.add_argument("--grids", type=int, nargs="+", default=[256, 512])
    args = parser.parse_args()
    rows = []
    for n in args.grids:
        linear = run_case("linear", n)
        pchip = run_case("pchip", n)
        rows.append({"n": n, "linear": linear, "pchip": pchip,
                     "delta_s_pchip_minus_linear": pchip["event_time_s"] - linear["event_time_s"]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"cases": rows}, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
    print(json.dumps({"cases": rows}, ensure_ascii=False))


if __name__ == "__main__":
    main()
