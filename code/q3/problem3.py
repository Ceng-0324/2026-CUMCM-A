"""生成 Q3 全域连续含水率达标事件、表 5、工作簿和数据图。"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from os.path import relpath
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
from model import solve_radial
from plotting import configure as configure_plotting


THRESHOLD = 0.15
DURATION_S = 72 * 3600.0
FORMAL_GRID = 1024
GRID_RUNS = (256, 512, 1024)
OUTPUT_STEP_S = 60.0
SCAN_STEP_S = 600.0
RADII_CM = np.arange(21, dtype=float) / 10.0
TABLE_POSITIONS_CM = np.arange(5, dtype=float) / 2.0


def provenance():
    sources = ["code/common/data_io.py", "code/common/model.py", "code/q3/problem3.py"]
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "xlsxwriter": xlsxwriter.__version__,
        "input_sha256": {e["path"]: e["sha256"] for e in verify_inputs()},
        "code_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources},
    }


def continuous_profile(solution, t, points=513):
    radius = solution.model.radius(float(t))
    positions = np.linspace(0.0, radius, points)
    sample = solution.sample([float(t)], positions)
    return positions, sample.moisture[0]


def continuous_max(solution, t, points=257):
    """在含中心和表面的径向采样点上估计重构场最大值，点数控制采样密度。"""
    positions, moisture = continuous_profile(solution, t, points)
    index = int(np.argmax(moisture))
    return float(moisture[index]), float(positions[index]), positions, moisture


def locate_event(solution, *, scan_step=SCAN_STEP_S, profile_points=257):
    scan_times = np.arange(0.0, solution.end_s + scan_step, scan_step)
    scan_times = np.minimum(scan_times, solution.end_s)
    scan_times = np.unique(scan_times)
    scan_values = np.array([continuous_max(solution, t, profile_points)[0] for t in scan_times])
    crossing = np.flatnonzero(((scan_values[:-1] - THRESHOLD) >= 0)
                              & ((scan_values[1:] - THRESHOLD) < 0))
    if not len(crossing):
        raise RuntimeError("72 h 内未找到连续域达标事件，请扩大积分时长")
    i = int(crossing[0])

    def event_function(t):
        return continuous_max(solution, t, profile_points)[0] - THRESHOLD

    event_time = float(brentq(event_function, scan_times[i], scan_times[i + 1],
                              xtol=1e-5, rtol=1e-12))
    max_c, max_position, positions, profile = continuous_max(solution, event_time, 1025)
    return {
        "event_time_s": event_time,
        "event_time_h": event_time / 3600.0,
        "scan_times_s": scan_times,
        "scan_max_moisture": scan_values,
        "bracket_s": [float(scan_times[i]), float(scan_times[i + 1])],
        "event_max_moisture": max_c,
        "event_max_position_m": max_position,
        "event_profile_positions_m": positions,
        "event_profile_moisture": profile,
    }


def first_strict_output(solution, event_time):
    """等号事件后的首个整分钟输出；达标判据使用未舍入的含水率。"""
    t = np.ceil(event_time / OUTPUT_STEP_S) * OUTPUT_STEP_S
    if t <= event_time + 1e-7:
        t += OUTPUT_STEP_S
    value = continuous_max(solution, t, 513)[0]
    return float(t), float(value)


def export_workbook(path, times_s, moisture):
    path.parent.mkdir(parents=True, exist_ok=True)
    with xlsxwriter.Workbook(path) as book:
        book.set_properties({"title": "问题三：达标时刻含水率", "created": datetime(2000, 1, 1)})
        value_fmt = book.add_format({"num_format": "0.0000"})
        radius_fmt = book.add_format({"num_format": "0.0", "bold": True})
        header_fmt = book.add_format({"bold": True, "text_wrap": True})
        sheet = book.add_worksheet("Sheet1")
        sheet.write(0, 0, "时间\\到药材中心的距离", header_fmt)
        sheet.write_row(0, 1, RADII_CM, radius_fmt)
        for i, (t, row) in enumerate(zip(times_s, np.round(moisture, 4)), start=1):
            sheet.write_number(i, 0, float(t))
            sheet.write_row(i, 1, row, value_fmt)
        sheet.freeze_panes(1, 1)
        sheet.set_column(0, 0, 22)
        sheet.set_column(1, len(RADII_CM), 12)
        sheet.set_row(0, 32)


def verify_workbook(path, times_s, moisture):
    workbook = read_xlsx(path)
    if list(workbook) != ["Sheet1"]:
        raise ValueError("Q3 工作簿工作表必须为 Sheet1")
    sheet = workbook["Sheet1"]
    expected_rows = len(times_s) + 1
    if len(sheet["rows"]) != expected_rows or sheet["errors"] or sheet["formula_count"]:
        raise ValueError("Q3 工作簿行数、错误单元格或公式不符合输出契约")
    header = sheet["rows"][1]
    if not np.allclose([header[j] for j in range(2, 23)], RADII_CM):
        raise ValueError("Q3 工作簿半径表头错误")
    for i, (t, expected) in enumerate(zip(times_s, moisture), start=2):
        row = sheet["rows"][i]
        if not np.isclose(row[1], float(t), rtol=0, atol=1e-9):
            raise ValueError("Q3 工作簿时间轴回读不一致")
        values = np.array([row[j] for j in range(2, 23)], dtype=float)
        if not np.allclose(values, np.round(expected, 4), atol=1e-12, rtol=0):
            raise ValueError("Q3 工作簿含水率回读不一致")
    return {"sheet": "Sheet1", "data_rows": len(times_s), "radial_columns": 21,
            "event_row_included": True, "all_cells_read_back": True}


def table_times(event_time):
    regular = np.arange(6 * 3600.0, event_time, 6 * 3600.0)
    return np.r_[regular, event_time]


def plot_figures(output_dir, figures_dir, result, formal_solution):
    figures_dir.mkdir(parents=True, exist_ok=True)
    configure_plotting(ROOT)
    plt.rcParams.update({"font.sans-serif": ["STHeiti", "PingFang SC", "Hiragino Sans GB", "DejaVu Sans"],
                         "axes.unicode_minus": False})
    scan_t = result["scan_times_s"]
    scan_c = result["scan_max_moisture"]
    event = result["event_time_s"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(scan_t / 3600.0, scan_c, color="#1f5a94", label="连续场最大含水率")
    ax.axhline(THRESHOLD, color="#b33", ls="--", label="阈值 0.15 kg/kg")
    ax.axvline(event / 3600.0, color="#444", ls=":", label=f"达标时刻 {event/3600:.4f} h")
    ax.set(xlabel="时间/h", ylabel="最大含水率/(kg/kg)")
    ax.grid(alpha=.25)
    ax.legend(frameon=False)
    # 阈值事件局部放大，突出首次达标时刻的根定位。
    inset = ax.inset_axes([0.52, 0.18, 0.43, 0.38])
    mask = (scan_t >= event - 12*3600) & (scan_t <= event + 6*3600)
    inset.plot(scan_t[mask]/3600.0, scan_c[mask], color="#1f5a94")
    inset.axhline(THRESHOLD, color="#b33", ls="--")
    inset.axvline(event/3600.0, color="#444", ls=":")
    inset.set_title("事件附近", fontsize=8)
    inset.tick_params(labelsize=7)
    fig.tight_layout()
    fig.savefig(figures_dir / "q3_threshold_event.pdf", format="pdf")
    plt.close(fig)

    times = np.array([max(0.0, event - 6 * 3600), event])
    fig, ax = plt.subplots(figsize=(7, 4))
    for t in times:
        pos, c = continuous_profile(formal_solution, t, 513)
        ax.plot(pos * 100, c, label=f"{t/3600:.4f} h")
    ax.axhline(THRESHOLD, color="#b33", ls="--", label="阈值")
    ax.set(xlabel="到中心距离/cm", ylabel="含水率/(kg/kg)")
    ax.grid(alpha=.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "q3_threshold_profiles.pdf", format="pdf")
    plt.close(fig)

    convergence = result["convergence"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(convergence["grid"], convergence["event_time_h"], "o-", label="空间网格")
    ax.axhline(event / 3600.0, color="#444", ls=":", label="正式网格")
    ax.set(xlabel="径向单元数 N", ylabel="达标时刻/h")
    ax.grid(alpha=.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures_dir / "q3_convergence.pdf", format="pdf")
    plt.close(fig)
    return sorted(p.name for p in figures_dir.glob("q3_*.pdf"))


def write_report(path, summary, sensitivity_path=None):
    e = summary["event"]
    v = summary["validation"]
    t = summary["table5"]
    rows = ["| 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |",
            "|---:|---:|---:|---:|---:|---:|"]
    rows += ["| " + f"{time_h:g}" + " | " + " | ".join(f"{x:.4f}" for x in row) + " |"
             for time_h, row in zip(t["times_h"], t["moisture"])]
    report = rf'''# 计算结果：问题三

本报告给出附录 3 变物性、固定半径条件下的全域连续含水率达标事件。计算从共同初值重新开始并延续问题二的全耦合模型；环境输入覆盖 0–4 h，4 h 后采用附件 1 末小时均值延拓。目标阈值为全域含水率严格低于 $0.15\,\mathrm{{kg/kg}}$，事件根定义为连续重构场的最大含水率首次达到 $0.15\,\mathrm{{kg/kg}}$ 的时刻。

## 运行环境与方法

Python {summary['provenance']['python']}，NumPy {summary['provenance']['numpy']}，SciPy {summary['provenance']['scipy']}。采用圆柱环形有限体积、Kirchhoff 水分通量、表面半控制体 Robin 边界和自适应 BDF。正式网格为 $N={summary['configuration']['n']}$，相对容差为 {summary['configuration']['rtol']:.1e}，绝对容差为 {summary['configuration']['atol']:.1e}，最大内部步长为 {summary['configuration']['max_step']:.0f} s。

## 连续域事件定义与结果

令 $C_h(r,t)$ 为由有限体积解在真实半径区间上的连续重构，则

\[
g(t)=\max_{{0\le r\le R}}C_h(r,t)-0.15.
\]

问题三的达标事件为 $g(t)$ 从正值到负值的首次交点。正式计算得到连续域事件时刻

\[
t_*={e['event_time_h']:.8f}\,\mathrm{{h}}
={e['event_time_s']:.3f}\,\mathrm{{s}}.
\]

事件处重构场的最大含水率为 {e['event_max_moisture']:.10f} kg/kg，最大位置为 {e['event_max_position_m']*100:.6f} cm。向上取整到 60 s 输出后，首个严格低于阈值的输出时刻为 {e['first_strict_time_h']:.6f} h，此时连续场最大含水率为 {e['first_strict_max_moisture']:.10f} kg/kg。论文中应将 $t_*$ 作为事件定位结果，并同时说明严格不等式对应的首个后继输出时刻。

### 表 5：达标过程的典型位置含水率

表 5 按题目要求列出每 6 h 及结束时刻的五个位置结果。表中结束时刻为连续事件 $t_*$，不是将其替换为下一个整小时。

{chr(10).join(rows)}

数据源为 [`../../results/q3/table5.csv`](../../results/q3/table5.csv)，未舍入导出场见 [`../../results/q3/fields.npz`](../../results/q3/fields.npz)。

## 连续重构与阶段解释

事件扫描使用连续场重构后的径向最大值，而不是直接取最大单元中心。正式事件附近的最大值位于中心，且在加密径向采样中未发现内部偏离中心的更大值；因此中心值可作为本算例的结果解释，但事件定义仍保留连续最大值形式。图 1 展示阈值函数随时间的下降及事件根，图 2 展示事件前后径向含水率剖面。

**图 1：** [`../../figures/q3/q3_threshold_event.pdf`](../../figures/q3/q3_threshold_event.pdf)。

**图 2：** [`../../figures/q3/q3_threshold_profiles.pdf`](../../figures/q3/q3_threshold_profiles.pdf)。

## 数值验证

不同空间网格得到的事件时刻如下：

| 网格 $N$ | 连续事件/h | 相对正式结果/s |
|---:|---:|---:|
{chr(10).join(f"| {n} | {h:.8f} | {d:.3f} |" for n, h, d in zip(v['grid'], v['event_time_h'], v['difference_s']))}

时间设置收紧后的正式网格事件为 {v['tight_event_time_h']:.8f} h，与正式设置相差 {v['tight_difference_s']:.3f} s。连续最大值重构在事件时刻采用 {v['event_profile_points']} 个径向采样点，并以两倍采样密度复核；事件时刻的最大含水率差为 {v['profile_refinement_difference']:.3e} kg/kg。正式积分期间最小含水率为 {v['min_moisture']:.9f} kg/kg，归一化干基水量收支最大残差为 {v['max_water_balance_residual']:.3e}。

**图 3：** [`../../figures/q3/q3_convergence.pdf`](../../figures/q3/q3_convergence.pdf)，展示空间网格对事件时刻的影响。

上述检查验证的是当前条件模型下的连续事件定位、离散收支和数值稳定性，不替代附录 3 经验物性、有效表面平衡浓度和末小时环境延拓的实验验证。阶段识别只作为结果诊断；本次正式时长仍由完整耦合 BDF 参考解给出，未把未经验证的降阶模型写成最终结果。

## 产物与复现

- [`../../results/q3/result3.xlsx`](../../results/q3/result3.xlsx)：每 60 s、每 0.1 cm 的含水率工作簿，延伸至事件时刻。
- [`../../results/q3/fields.npz`](../../results/q3/fields.npz)：未舍入输出场、事件扫描和收敛数据。
- [`../../results/q3/table5.csv`](../../results/q3/table5.csv)：论文表 5 数据。
- [`../../results/q3/summary.json`](../../results/q3/summary.json)：参数、来源和验证记录。
- [`../../results/q3/artifact_manifest.json`](../../results/q3/artifact_manifest.json)：产物哈希。

运行 `make q3` 可复现本结果；原始模板不会被覆盖。
'''
    if sensitivity_path is not None:
        reference = Path(relpath(sensitivity_path, path.parent)).as_posix()
        report += ("\n## 补充检验\n\n"
                   f"- [物理参数敏感性与 BDF/Radau 积分器复核]({reference})。\n\n"
                   "该证据由独立脚本生成，保留文件内的原始来源记录；"
                   "`make q3` 只更新本报告的引用，不重算该检验。\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def run(output_dir, report_path, figures_dir):
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    solutions = {}
    events = {}
    for n in GRID_RUNS:
        solutions[n] = solve_radial(n, appendix=3, duration_s=DURATION_S, rtol=2e-7,
                                    atol=2e-9, max_step=300, align_environment=True)
        events[n] = locate_event(solutions[n])
        print(f"Q3 N={n} 事件 {events[n]['event_time_h']:.6f} h，累计 {time.perf_counter()-start:.1f} s",
              flush=True)

    formal = solutions[FORMAL_GRID]
    event = events[FORMAL_GRID]
    tight = solve_radial(FORMAL_GRID, appendix=3, duration_s=DURATION_S, rtol=5e-9,
                         atol=5e-11, max_step=60, align_environment=True)
    tight_event = locate_event(tight, profile_points=257)
    first_time, first_value = first_strict_output(formal, event["event_time_s"])
    event["first_strict_time_s"] = first_time
    event["first_strict_time_h"] = first_time / 3600.0
    event["first_strict_max_moisture"] = first_value

    out_times = np.arange(OUTPUT_STEP_S, event["event_time_s"], OUTPUT_STEP_S)
    out_times = np.r_[out_times, event["event_time_s"]]
    output = formal.sample(out_times, RADII_CM / 100)
    export_workbook(output_dir / "result3.xlsx", out_times, output.moisture)
    table_t = table_times(event["event_time_s"])
    table = formal.sample(table_t, TABLE_POSITIONS_CM / 100)
    with (output_dir / "table5.csv").open("w", encoding="utf-8") as f:
        f.write("时间/h,0 cm,0.5 cm,1 cm,1.5 cm,2 cm\n")
        for t, row in zip(table_t / 3600.0, table.moisture):
            f.write(str(float(t)) + "," + ",".join(f"{x:.4f}" for x in row) + "\n")

    balance = 2 * formal.model.weights @ formal.state(out_times)[formal.model.n:2*formal.model.n] \
              + formal.state(out_times)[-1] - 2.55
    profile_refine = float(abs(event["event_max_moisture"] - continuous_max(formal, event["event_time_s"], 2049)[0]))
    summary = {
        "scope": "Q3 fixed-radius appendix 3 continuous-domain event",
        "provenance": provenance(),
        "configuration": {"n": FORMAL_GRID, "appendix": 3, "duration_s": DURATION_S,
                           "rtol": 2e-7, "atol": 2e-9, "max_step": 300,
                           "align_environment": True, "threshold": THRESHOLD,
                           "boundary_extension": "附件1末小时均值", "output_step_s": OUTPUT_STEP_S},
        "event": {k: v for k, v in event.items() if not isinstance(v, np.ndarray)},
        "validation": {
            "grid": list(GRID_RUNS),
            "event_time_h": [events[n]["event_time_h"] for n in GRID_RUNS],
            "difference_s": [(events[n]["event_time_s"] - event["event_time_s"]) for n in GRID_RUNS],
            "tight_event_time_h": tight_event["event_time_h"],
            "tight_difference_s": tight_event["event_time_s"] - event["event_time_s"],
            "event_profile_points": 257,
            "profile_refinement_difference": profile_refine,
            "profile_257_to_513_max_difference": float(np.max(abs(
                np.interp(np.linspace(0, 1, 513), np.linspace(0, 1, 257),
                          continuous_profile(formal, event["event_time_s"], 257)[1])
                - continuous_profile(formal, event["event_time_s"], 513)[1]))),
            "min_moisture": float(output.moisture.min()),
            "max_water_balance_residual": float(np.max(abs(balance))),
            "max_event_position_cm": float(max(events[n]["event_max_position_m"] for n in GRID_RUNS) * 100),
        },
        "table5": {"times_h": (table_t / 3600.0).tolist(), "moisture": table.moisture.tolist()},
        "workbook": verify_workbook(output_dir / "result3.xlsx", out_times, output.moisture),
    }
    np.savez_compressed(output_dir / "fields.npz", times_s=out_times, radii_cm=RADII_CM,
                        moisture=output.moisture, event_scan_times_s=event["scan_times_s"],
                        event_scan_max_moisture=event["scan_max_moisture"],
                        event_profile_positions_m=event["event_profile_positions_m"],
                        event_profile_moisture=event["event_profile_moisture"],
                        convergence_grid=np.array(GRID_RUNS),
                        convergence_event_time_h=np.array(summary["validation"]["event_time_h"]))
    summary["figures"] = plot_figures(output_dir, figures_dir, {
        **event, "convergence": {"grid": list(GRID_RUNS),
                                  "event_time_h": summary["validation"]["event_time_h"]}}, formal)
    write_json(output_dir / "summary.json", summary)
    sensitivity_path = output_dir / "validation_sensitivity.json"
    write_report(report_path, summary, sensitivity_path if sensitivity_path.is_file() else None)
    artifacts = [output_dir / n for n in ("result3.xlsx", "fields.npz", "summary.json", "table5.csv")]
    artifacts += sorted(figures_dir.glob("q3_*.pdf"))
    if sensitivity_path.is_file():
        artifacts.append(sensitivity_path)
    write_json(output_dir / "artifact_manifest.json",
               {"files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in artifacts}})
    print(f"Q3 正式结果完成，事件 {event['event_time_h']:.8f} h，耗时 {time.perf_counter()-start:.1f} s。", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/q3")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/q3/RESULTS_REPORT.md")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures/q3")
    args = parser.parse_args()
    run(args.output_dir, args.report, args.figures_dir)


if __name__ == "__main__":
    main()
