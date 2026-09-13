"""Q4 收缩材料域正式结果、四组合机制对照和论文图件。"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import platform
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
import xlsxwriter
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from data_io import ROOT, read_xlsx, verify_inputs, write_json
from model import solve_radial, reconstruct_profile, kirchhoff, inverse_kirchhoff
from plotting import configure as configure_plotting

THRESHOLD = 0.15
DURATION_S = 72 * 3600.0
MECHANISM_DURATION_S = 168 * 3600.0
FORMAL_GRID = 1024
GRID_RUNS = (256, 512, 1024)
OUTPUT_STEP_S = 60.0
SCAN_STEP_S = 600.0
RADII_CM = np.arange(21, dtype=float) / 10.0
TABLE_POSITIONS_CM = np.arange(4, dtype=float) / 2.0


def provenance():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "scipy": scipy.__version__, "xlsxwriter": xlsxwriter.__version__,
            "input_sha256": {e["path"]: e["sha256"] for e in verify_inputs()}}


def continuous_max(solution, t, points=513, *, return_profile=True):
    """求重构场全域极值；points 仅控制返回剖面的采样密度。"""
    xi = np.linspace(0.0, 1.0, points)
    if t == 0:
        c = np.full(points, 2.55)
        return 2.55, 0.0, xi, c
    model, n = solution.model, solution.model.n
    y = solution.state([float(t)])[:, 0]
    _, water, _, cs, _, _, _, base, a = model.fluxes(t, y)
    potential_profile = reconstruct_profile(
        model.centers, kirchhoff(y[n:2*n], a),
        kirchhoff(cs, a), -model.radius(t)*water[-1]/base[-1])
    # K(C) 严格递增，可先比较每段三次多项式的端点和驻点，再反解 C。
    candidates = spline_candidates(potential_profile)
    values = potential_profile(candidates)
    i = int(np.argmax(values))
    maximum = inverse_kirchhoff(values[i], a, 2*max(2.55, float(y[n:2*n].max()), cs))
    if not return_profile:
        return float(maximum), float(candidates[i]), None, None
    c = solution.sample([float(t)], xi, coordinate="material").moisture[0]
    return float(maximum), float(candidates[i]), xi, c


def spline_candidates(spline):
    roots = spline.derivative().roots(extrapolate=False)
    roots = roots[np.isfinite(roots) & (roots >= spline.x[0]) & (roots <= spline.x[-1])]
    return np.unique(np.r_[spline.x, roots])


def locate_event(solution, scan_step=SCAN_STEP_S, profile_points=257):
    times = np.unique(np.minimum(np.arange(0.0, solution.end_s + scan_step, scan_step), solution.end_s))
    values = np.array([continuous_max(solution, t, profile_points, return_profile=False)[0]
                       for t in times])
    crossing = np.flatnonzero(((values[:-1] - THRESHOLD) >= 0) & ((values[1:] - THRESHOLD) < 0))
    if not len(crossing):
        raise RuntimeError(f"在 {solution.end_s/3600:g} h 内未找到连续域达标事件")
    i = int(crossing[0])

    def threshold_residual(t):
        return continuous_max(solution, t, profile_points, return_profile=False)[0] - THRESHOLD

    event_s = float(brentq(threshold_residual, times[i], times[i + 1], xtol=1e-5, rtol=1e-12))
    max_c, max_xi, profile_xi, profile_c = continuous_max(solution, event_s, 1025)
    return {"event_time_s": event_s, "event_time_h": event_s / 3600.0,
            "bracket_s": [float(times[i]), float(times[i + 1])],
            "scan_times_s": times, "scan_max_moisture": values,
            "event_max_moisture": max_c, "event_max_material_coordinate": max_xi,
            "event_profile_xi": profile_xi, "event_profile_moisture": profile_c}


def table_times(event_s):
    return np.r_[np.arange(6 * 3600.0, event_s, 6 * 3600.0), event_s]


def export_workbook(path, times_s, moisture, surface):
    path.parent.mkdir(parents=True, exist_ok=True)
    with xlsxwriter.Workbook(path) as book:
        book.set_properties({"title": "问题四：收缩药材含水率", "created": datetime(2000, 1, 1)})
        val_fmt = book.add_format({"num_format": "0.0000"})
        head_fmt = book.add_format({"bold": True, "text_wrap": True})
        radius_fmt = book.add_format({"num_format": "0.0", "bold": True})
        sheet = book.add_worksheet("Sheet1")
        sheet.write(0, 0, "时间\\到药材中心的距离", head_fmt)
        sheet.write_row(0, 1, RADII_CM, radius_fmt)
        sheet.write(0, len(RADII_CM) + 1, "药材表面", head_fmt)
        for i, (t, row, s) in enumerate(zip(times_s, np.round(moisture, 4), np.round(surface, 4)), start=1):
            sheet.write_number(i, 0, float(t))
            for j, value in enumerate(row, start=1):
                if np.isfinite(value):
                    sheet.write_number(i, j, float(value), val_fmt)
                else:
                    sheet.write_blank(i, j, None, val_fmt)
            sheet.write_number(i, len(RADII_CM) + 1, float(s), val_fmt)
        sheet.freeze_panes(1, 1)
        sheet.set_column(0, 0, 22)
        sheet.set_column(1, len(RADII_CM) + 1, 12)
        sheet.set_row(0, 32)


def verify_workbook(path, times_s, moisture, surface):
    wb = read_xlsx(path)
    if list(wb) != ["Sheet1"]:
        raise ValueError("Q4 工作簿工作表必须为 Sheet1")
    rows = wb["Sheet1"]["rows"]
    if len(rows) != len(times_s) + 1 or wb["Sheet1"]["errors"] or wb["Sheet1"]["formula_count"]:
        raise ValueError("Q4 工作簿结构错误")
    header = rows[1]
    if not np.allclose([header[j] for j in range(2, 23)], RADII_CM) or header[23] != "药材表面":
        raise ValueError("Q4 工作簿表头错误")
    for i, (t, expected, es) in enumerate(zip(times_s, moisture, surface), start=2):
        row = rows[i]
        if not np.isclose(row[1], float(t), atol=1e-9, rtol=0):
            raise ValueError("Q4 时间轴回读不一致")
        values = np.array([row.get(j, np.nan) for j in range(2, 23)], dtype=float)
        if not np.allclose(values, np.round(expected, 4), equal_nan=True, atol=1e-12, rtol=0):
            raise ValueError("Q4 实半径场回读不一致")
        if not np.isclose(row.get(23, np.nan), round(float(es), 4), atol=1e-12, rtol=0):
            raise ValueError("Q4 表面场回读不一致")
    return {"sheet": "Sheet1", "data_rows": len(times_s), "radial_columns": 21,
            "surface_column": True, "outside_radius_as_nan": True, "all_cells_read_back": True}


def physical_output(solution, times_s):
    field = solution.sample(times_s, RADII_CM / 100.0, coordinate="radius", outside="nan")
    surface = solution.sample(times_s, [1.0], coordinate="material").moisture[:, 0]
    return field.moisture, surface


def plot_figures(figures_dir, event, solution, convergence, mechanism):
    figures_dir.mkdir(parents=True, exist_ok=True)
    configure_plotting(ROOT)
    plt.rcParams.update({"font.sans-serif": ["STHeiti", "PingFang SC", "Hiragino Sans GB", "DejaVu Sans"],
                         "axes.unicode_minus": False})
    # 论文主文使用的左右组合图：左侧展示全域达标事件，右侧展示收缩前后剖面。
    # 两个面板直接由同一正式事件和解对象绘制，避免先栅格化再拼接 PDF 造成字体与线宽不一致。
    fig, (ax_event, ax_profile) = plt.subplots(1, 2, figsize=(11.2, 4.2),
                                                 gridspec_kw={"wspace": 0.30})
    ax_event.plot(event["scan_times_s"] / 3600, event["scan_max_moisture"],
                  color="#2F4B7C", lw=1.8, label="连续域最大含水率")
    ax_event.axhline(THRESHOLD, color="#B2182B", ls="--", lw=1.2,
                     label="阈值 0.15 kg/kg")
    ax_event.axvline(event["event_time_h"], color="#444444", ls=":", lw=1.2,
                     label=f"达标时刻 {event['event_time_h']:.4f} h")
    ax_event.set(xlabel="时间 / h", ylabel="最大含水率 / (kg/kg)")
    ax_event.grid(alpha=.22)
    ax_event.legend(frameon=False, fontsize=8, loc="best")
    ax_event.set_title("(a) 全域达标事件", fontsize=11)

    for t, color in [(max(0.0, event["event_time_s"] - 6 * 3600), "#4C78A8"),
                     (event["event_time_s"], "#D62728")]:
        xi = np.linspace(0, 1, 513)
        c = solution.sample([t], xi, coordinate="material").moisture[0]
        radius = solution.model.radius(t)
        ax_profile.plot(xi * radius * 100, c, color=color, lw=1.8,
                        label=f"{t/3600:.4f} h")
    ax_profile.axhline(THRESHOLD, color="#B2182B", ls="--", lw=1.2,
                       label="阈值 0.15 kg/kg")
    ax_profile.set(xlabel="实际到中心距离 / cm", ylabel="含水率 / (kg/kg)")
    ax_profile.grid(alpha=.22)
    ax_profile.legend(frameon=False, fontsize=8, loc="best")
    ax_profile.set_title("(b) 事件前与达标时刻剖面", fontsize=11)
    fig.savefig(figures_dir / "q4_shrink_event_combined.pdf", format="pdf",
                bbox_inches="tight")
    plt.close(fig)

    # 单面板机制路径图：以基准到正式组合的路径展示各效应贡献。
    effects = mechanism["effects"]
    base = effects["baseline_fixed_appendix3_h"]
    g = effects["geometry_effect_at_appendix3_h"]
    p_eff = effects["property_effect_at_fixed_geometry_h"]
    inter = effects["interaction_effect_h"]
    net = effects["net_change_h"]
    xs = np.arange(5)
    ys = np.array([base, base + g, base + g + p_eff, base + g + p_eff + inter, base + net])
    labels = ["固定域·附录3\n基准", "加入收缩\n几何效应", "再加入附录4\n物性", "加入交互\n效应", "正式组合\n收缩域·附录4"]
    fig, ax = plt.subplots(figsize=(10.5, 4.6), constrained_layout=True)
    ax.plot(xs, ys, color="#2F4B7C", lw=2.2, zorder=2)
    ax.scatter(xs, ys, s=[95, 75, 75, 75, 110], c=["#4C78A8", "#2E8B57", "#C44E52", "#7A5195", "#E45756"], edgecolor="white", linewidth=1.2, zorder=3)
    for i in range(4):
        delta = ys[i+1] - ys[i]
        if abs(delta) < 1e-8:
            continue
        color = "#2E8B57" if delta < 0 else "#C44E52"
        ax.annotate(f"{delta:+.2f}", xy=((xs[i]+xs[i+1])/2, (ys[i]+ys[i+1])/2),
                    xytext=(0, 17 if delta >= 0 else -20), textcoords="offset points",
                    ha="center", color=color, fontsize=9, fontweight="bold",
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0,
                                    connectionstyle="arc3,rad=0.08"))
    for x, y in zip(xs, ys):
        # 低位节点标签上移，避免与横坐标组合名称重叠。
        place_above = (x in [0, 4]) or (y < 35)
        offset = 5 if place_above else -5
        ax.text(x, y + offset, f"{y:.2f}", ha="center",
                va="bottom" if place_above else "top", fontsize=8, color="#222")
    ax.set_xticks(xs, labels)
    ax.set_ylabel("连续达标时刻 / h")
    ax.set_title("Q4 从基准到正式组合的机制路径")
    ax.grid(axis="y", alpha=.2)
    ax.set_xlim(-0.35, 4.35)
    ax.text(0.02, 0.04, "绿色：缩短达标时间    红色：延长达标时间", transform=ax.transAxes, fontsize=8, color="#555")
    fig.savefig(figures_dir / "q4_mechanism_comparison.pdf", format="pdf", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(convergence["grid"], convergence["event_time_h"], "o-", label="连续事件时刻")
    ax.set(xlabel="径向单元数 N", ylabel="达标时刻/h")
    ax.grid(alpha=.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "q4_convergence.pdf", format="pdf")
    plt.close(fig)

    return sorted(p.name for p in figures_dir.glob("q4_*.pdf"))


def mechanism_runs():
    cases = {}
    for shrink in (False, True):
        for appendix in (3, 4):
            label = f"{'shrink' if shrink else 'fixed'}_appendix{appendix}"
            solution = solve_radial(FORMAL_GRID, appendix=appendix, shrink=shrink,
                                    duration_s=DURATION_S if shrink else MECHANISM_DURATION_S,
                                    rtol=2e-7, atol=2e-9,
                                    max_step=300, align_environment=True)
            event = locate_event(solution)
            cases[label] = {"appendix": appendix, "shrink": shrink,
                            "integration_duration_h": solution.end_s/3600,
                            "radius_extrapolated": bool(shrink and solution.end_s > solution.model.radii[-1, 0]),
                            "event_time_h": event["event_time_h"],
                            "event_time_s": event["event_time_s"]}
    base = cases["fixed_appendix3"]["event_time_h"]
    effects = {
        "baseline_fixed_appendix3_h": base,
        "geometry_effect_at_appendix3_h": cases["shrink_appendix3"]["event_time_h"] - base,
        "property_effect_at_fixed_geometry_h": cases["fixed_appendix4"]["event_time_h"] - base,
        "interaction_effect_h": (cases["shrink_appendix4"]["event_time_h"]
                                  - cases["shrink_appendix3"]["event_time_h"]
                                  - cases["fixed_appendix4"]["event_time_h"] + base),
    }
    effects["geometry_order_averaged_h"] = effects["geometry_effect_at_appendix3_h"] + effects["interaction_effect_h"]/2
    effects["property_order_averaged_h"] = effects["property_effect_at_fixed_geometry_h"] + effects["interaction_effect_h"]/2
    effects["net_change_h"] = cases["shrink_appendix4"]["event_time_h"] - base
    return {"cases": cases, "effects": effects}




def run(output_dir, figures_dir):
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    solutions, events = {}, {}
    for n in GRID_RUNS:
        solutions[n] = solve_radial(n, appendix=4, shrink=True, duration_s=DURATION_S,
                                    rtol=2e-7, atol=2e-9, max_step=300, align_environment=True)
        events[n] = locate_event(solutions[n])
        print(f"Q4 N={n} 事件 {events[n]['event_time_h']:.6f} h", flush=True)
    formal, event = solutions[FORMAL_GRID], events[FORMAL_GRID]
    tight = solve_radial(FORMAL_GRID, appendix=4, shrink=True, duration_s=DURATION_S,
                         rtol=5e-9, atol=5e-11, max_step=60, align_environment=True)
    tight_event = locate_event(tight)
    first_t = float(np.ceil(event["event_time_s"] / OUTPUT_STEP_S) * OUTPUT_STEP_S)
    if first_t <= event["event_time_s"] + 1e-7:
        first_t += OUTPUT_STEP_S
    first_c = continuous_max(formal, first_t, 513)[0]
    event["first_strict_time_s"] = first_t
    event["first_strict_time_h"] = first_t / 3600.0
    event["first_strict_max_moisture"] = first_c
    if first_c >= THRESHOLD:
        raise ValueError("后继输出时刻未严格达标")
    times = np.unique(np.r_[np.arange(OUTPUT_STEP_S, first_t + 0.1, OUTPUT_STEP_S), event["event_time_s"]])
    moisture, surface = physical_output(formal, times)
    export_workbook(output_dir / "result4.xlsx", times, moisture, surface)
    table_t = table_times(event["event_time_s"])
    table_field = formal.sample(table_t, TABLE_POSITIONS_CM / 100, coordinate="radius", outside="nan")
    table_surface = formal.sample(table_t, [1.0], coordinate="material").moisture[:, 0]
    with (output_dir / "table6.csv").open("w", encoding="utf-8") as f:
        f.write("时间/h,0 cm,0.5 cm,1 cm,1.5 cm,药材表面\n")
        for h, row, s in zip(table_t / 3600, table_field.moisture, table_surface):
            values = ",".join("" if not np.isfinite(x) else f"{x:.4f}" for x in row)
            f.write(f"{float(h)},{values},{s:.4f}\n")
    states = formal.state(times)
    n = formal.model.n
    balance = 2 * formal.model.weights @ states[n:2*n] + states[-1] - 2.55
    profile_refine = abs(event["event_max_moisture"] - float(np.max(formal.sample(
        [event["event_time_s"]], np.linspace(0, 1, 2049), coordinate="material").moisture)))
    mechanism = mechanism_runs()
    summary = {"scope": "Q4 shrinking radius appendix 4 continuous-domain event",
               "provenance": provenance(),
               "configuration": {"n": FORMAL_GRID, "appendix": 4, "shrink": True, "duration_s": DURATION_S,
                                  "rtol": 2e-7, "atol": 2e-9, "max_step": 300, "threshold": THRESHOLD,
                                  "boundary_extension": "附件1末小时均值", "output_step_s": OUTPUT_STEP_S},
               "event": {k: v for k, v in event.items() if not isinstance(v, np.ndarray)},
               "validation": {"grid": list(GRID_RUNS), "event_time_h": [events[n]["event_time_h"] for n in GRID_RUNS],
                              "difference_s": [events[n]["event_time_s"] - event["event_time_s"] for n in GRID_RUNS],
                              "tight_event_time_h": tight_event["event_time_h"],
                              "tight_difference_s": tight_event["event_time_s"] - event["event_time_s"],
                              "profile_refinement_difference": float(profile_refine), "min_moisture": float(np.nanmin(moisture)),
                              "max_water_balance_residual": float(np.max(abs(balance)))},
               "table6": {"times_h": (table_t / 3600).tolist(),
                          "moisture": [[float(x) if np.isfinite(x) else None for x in row]
                                       for row in np.column_stack([table_field.moisture, table_surface])]},
               "mechanism": mechanism,
               "workbook": verify_workbook(output_dir / "result4.xlsx", times, moisture, surface)}
    np.savez_compressed(output_dir / "fields.npz", times_s=times, radii_cm=RADII_CM, moisture=moisture,
                        surface_moisture=surface, event_scan_times_s=event["scan_times_s"],
                        event_scan_max_moisture=event["scan_max_moisture"], event_profile_xi=event["event_profile_xi"],
                        event_profile_moisture=event["event_profile_moisture"], convergence_grid=np.array(GRID_RUNS),
                        convergence_event_time_h=np.array(summary["validation"]["event_time_h"]))
    summary["figures"] = plot_figures(figures_dir, event, formal,
                                       {"grid": list(GRID_RUNS), "event_time_h": summary["validation"]["event_time_h"]},
                                       mechanism)
    write_json(output_dir / "summary.json", summary)
    print(f"Q4 正式结果完成，事件 {event['event_time_h']:.8f} h，耗时 {time.perf_counter()-start:.1f} s", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/q4")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures/q4")
    args = parser.parse_args()
    run(args.output_dir, args.figures_dir)


if __name__ == "__main__":
    main()
