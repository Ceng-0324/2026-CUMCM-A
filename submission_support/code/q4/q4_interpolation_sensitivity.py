"""Q4 半径轨迹的分段线性与保形插值对照。"""
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
from data_io import verify_inputs, write_json
from model import solve_radial
from problem4 import locate_event


def run_case(kind: str, n: int) -> dict[str, float | str | int]:
    if kind not in ("linear", "pchip"):
        raise ValueError("插值方法必须为 linear 或 pchip")

    def radius(self, t):
        if not self.shrink:
            return self.r0
        if kind == "linear":
            return float(np.interp(t, self.radii[:, 0], self.radii[:, 1]) * 0.01)
        if not hasattr(self, "_pchip_radius"):
            self._pchip_radius = PchipInterpolator(
                self.radii[:, 0], self.radii[:, 1], extrapolate=True
            )
        return float(self._pchip_radius(t) * 0.01)

    original_radius = model.RadialModel.radius
    try:
        model.RadialModel.radius = radius
        solution = solve_radial(
            n, appendix=4, shrink=True, duration_s=72 * 3600,
            rtol=2e-7, atol=2e-9, max_step=300, align_environment=True,
        )
        event = locate_event(solution)
    finally:
        # 事件重构也会读取半径；直到定位结束才恢复，失败时同样恢复。
        model.RadialModel.radius = original_radius
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
    payload = {
        "cases": rows,
        "provenance": {
            "input_sha256": {entry["path"]: entry["sha256"] for entry in verify_inputs()},
        },
    }
    write_json(args.output, payload)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
