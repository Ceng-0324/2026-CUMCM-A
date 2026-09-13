"""Q3/Q4 物理参数敏感性与独立时间积分器复核。"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/common"))
sys.path.insert(0, str(ROOT / "code/q3"))
sys.path.insert(0, str(ROOT / "code/q4"))

import model
from model import solve_radial
from problem3 import locate_event as locate_q3_event
from problem4 import locate_event as locate_q4_event


FACTORS = (0.8, 0.9, 1.0, 1.1, 1.2)


def run_event(*, question: str, factor_name: str | None = None,
              factor: float = 1.0, method: str = "BDF", n: int = 512) -> float:
    """在同一网格与积分设置下返回连续域达标时刻。"""
    original_h, original_km = model.RadialModel.h, model.RadialModel.km
    original_parameters = model.material_parameters

    if factor_name == "h":
        model.RadialModel.h = original_h * factor
    elif factor_name == "km":
        model.RadialModel.km = original_km * factor
    elif factor_name == "D_factor":
        def scaled_parameters(c, t, appendix):
            rho, cp, k, base, a = original_parameters(c, t, appendix)
            return rho, cp, k, base * factor, a
        model.material_parameters = scaled_parameters
    elif factor_name is not None:
        raise ValueError(f"未知敏感性参数：{factor_name}")

    try:
        kwargs = dict(n=n, duration_s=72 * 3600, rtol=2e-7, atol=2e-9,
                      max_step=300, align_environment=True, method=method)
        if question == "Q3":
            solution = solve_radial(appendix=3, **kwargs)
            return float(locate_q3_event(solution)["event_time_h"])
        if question == "Q4":
            solution = solve_radial(appendix=4, shrink=True, **kwargs)
            return float(locate_q4_event(solution)["event_time_h"])
        raise ValueError(f"未知问题：{question}")
    finally:
        model.RadialModel.h, model.RadialModel.km = original_h, original_km
        model.material_parameters = original_parameters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/local/model_validation_sensitivity.json")
    parser.add_argument("--grid", type=int, default=512)
    args = parser.parse_args()

    payload: dict[str, object] = {
        "configuration": {"grid": args.grid, "rtol": 2e-7, "atol": 2e-9,
                          "max_step_s": 300, "factors": list(FACTORS)},
        "parameter_sensitivity": {},
        "integrator_cross_check": {},
    }
    for question in ("Q3", "Q4"):
        rows = {}
        for name in ("h", "km", "D_factor"):
            values = []
            for factor in FACTORS:
                event_h = run_event(question=question, factor_name=name,
                                    factor=factor, n=args.grid)
                values.append({"factor": factor, "event_time_h": event_h})
                print(f"{question} {name}={factor:.1f}: {event_h:.8f} h", flush=True)
            baseline = next(row["event_time_h"] for row in values if row["factor"] == 1.0)
            for row in values:
                row["delta_h"] = row["event_time_h"] - baseline
                row["relative_percent"] = 100 * row["delta_h"] / baseline
            rows[name] = values
        payload["parameter_sensitivity"][question] = rows

        bdf = run_event(question=question, method="BDF", n=args.grid)
        radau = run_event(question=question, method="Radau", n=args.grid)
        payload["integrator_cross_check"][question] = {
            "BDF_event_time_h": bdf,
            "Radau_event_time_h": radau,
            "Radau_minus_BDF_s": (radau - bdf) * 3600,
        }
        print(f"{question} BDF={bdf:.8f} h, Radau={radau:.8f} h", flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(f"写入 {args.output}")


if __name__ == "__main__":
    main()
