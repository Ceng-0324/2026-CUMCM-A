"""Formal Q3/Q4 sensitivity runs for boundary extension and Q4 mechanism convergence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/common"))
sys.path.insert(0, str(ROOT / "code/q3"))
sys.path.insert(0, str(ROOT / "code/q4"))

from model import solve_radial
from problem3 import locate_event as locate_q3_event
from problem4 import locate_event as locate_q4_event


def event_q3(n: int, boundary: str) -> float:
    sol = solve_radial(n, appendix=3, boundary=boundary, duration_s=72 * 3600,
                       rtol=2e-7, atol=2e-9, max_step=300, align_environment=True)
    return float(locate_q3_event(sol)["event_time_h"])


def event_q4(n: int, appendix: int, shrink: bool, boundary: str) -> float:
    duration = 72 * 3600 if shrink else 168 * 3600
    sol = solve_radial(n, appendix=appendix, shrink=shrink, boundary=boundary,
                       duration_s=duration, rtol=2e-7, atol=2e-9,
                       max_step=300, align_environment=True)
    return float(locate_q4_event(sol)["event_time_h"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/q4/formal_sensitivity.json")
    parser.add_argument("--grids", type=int, nargs="+", default=[256, 512, 1024])
    args = parser.parse_args()

    q3 = {boundary: {str(n): event_q3(n, boundary)
                     for n in args.grids} for boundary in ("mean", "last")}
    cases = {(shrink, appendix): {str(n): event_q4(n, appendix, shrink, "mean")
                                  for n in args.grids}
             for shrink in (False, True) for appendix in (3, 4)}
    q4_last = {str(n): event_q4(n, 4, True, "last") for n in args.grids}
    payload = {
        "configuration": {"grids": args.grids, "rtol": 2e-7, "atol": 2e-9,
                           "max_step_s": 300, "environment": "mean/last",
                           "q4_default_boundary": "mean"},
        "q3_environment_event_time_h": q3,
        "q4_mechanism_event_time_h": {
            f"{'shrink' if shrink else 'fixed'}_appendix{appendix}": values
            for (shrink, appendix), values in cases.items()
        },
        "q4_shrink_appendix4_last_environment_event_time_h": q4_last,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
