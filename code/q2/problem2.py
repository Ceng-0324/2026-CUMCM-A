"""生成 Q2 变物性耦合结果、工作簿、验证报告和数据图。"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
from data_io import ROOT, read_xlsx, verify_inputs, write_json
from model import kirchhoff, solve_radial
from plotting import configure as configure_plotting

DURATION_S = 10800
TIMES_S = np.arange(1.0, DURATION_S + 1.0)
TABLE_TIMES_S = np.arange(1800.0, DURATION_S + 1.0, 1800.0)
RADII_CM = np.arange(21, dtype=float) / 10.0
TABLE_COLUMNS = np.array([0, 5, 10, 15, 20])
GRIDS = (512, 1024, 2048)


def provenance():
    sources = ["code/common/data_io.py", "code/common/model.py", "code/q2/problem2.py"]
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "xlsxwriter": xlsxwriter.__version__,
            "input_sha256": {e["path"]: e["sha256"] for e in verify_inputs()},
            "code_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in sources}}


def export_workbook(path, temperature_c, moisture):
    path.parent.mkdir(parents=True, exist_ok=True)
    with xlsxwriter.Workbook(path) as book:
        book.set_properties({"title": "问题二：全过程温度与水分浓度", "created": datetime(2000, 1, 1)})
        value_fmt = book.add_format({"num_format": "0.0000"})
        radius_fmt = book.add_format({"num_format": "0.0", "bold": True})
        header_fmt = book.add_format({"bold": True, "text_wrap": True})
        for name, values in (("温度", temperature_c), ("水分浓度", moisture)):
            sheet = book.add_worksheet(name)
            sheet.write(0, 0, "时间\\到药材中心的距离", header_fmt)
            sheet.write_row(0, 1, RADII_CM, radius_fmt)
            for i, (t, row) in enumerate(zip(TIMES_S, np.round(values, 4)), start=1):
                sheet.write_number(i, 0, int(t))
                sheet.write_row(i, 1, row, value_fmt)
            sheet.freeze_panes(1, 1)
            sheet.set_column(0, 0, 22)
            sheet.set_column(1, len(RADII_CM), 12)
            sheet.set_row(0, 32)


def verify_workbook(path, temperature_c, moisture):
    wb = read_xlsx(path)
    if list(wb) != ["温度", "水分浓度"]:
        raise ValueError("Q2 工作簿工作表必须为温度、水分浓度")
    expected = {"温度": temperature_c, "水分浓度": moisture}
    cells = 0
    for name in wb:
        ws = wb[name]
        if ws["dimension"] != "A1:V10801" or len(ws["rows"]) != DURATION_S + 1:
            raise ValueError("Q2 工作簿尺寸应为 10800 行、21 个半径列")
        header = [ws["rows"][1][j] for j in range(2, 23)]
        if not np.allclose(header, RADII_CM):
            raise ValueError("Q2 工作簿半径表头错误")
        for i in range(2, DURATION_S + 2):
            row = ws["rows"][i]
            if row[1] != i - 1 or set(row) != set(range(1, 23)):
                raise ValueError("Q2 工作簿时间轴错误")
            values = np.array([row[j] for j in range(2, 23)], dtype=float)
            if not np.allclose(values, np.round(expected[name][i - 2], 4), atol=1e-12):
                raise ValueError(f"Q2 工作簿{name}逐格回读不一致")
            cells += 21
    return {"dimension": "A1:V10801", "data_rows_per_sheet": DURATION_S,
            "radial_columns": 21, "numeric_field_cells": cells, "all_cells_read_back": True}


def plot_figures(output_dir, figures_dir):
    figures_dir.mkdir(parents=True, exist_ok=True)
    configure_plotting(ROOT)
    data = np.load(output_dir / "fields.npz", allow_pickle=True)
    times, radii, tc, c = data["times_s"], data["radii_cm"], data["temperature_C"], data["moisture"]
    plt.rcParams.update({"font.sans-serif": ["STHeiti", "Arial Unicode MS", "DejaVu Sans"],
                         "axes.unicode_minus": False})
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for i in [1799, 5399, 10799]:
        ax[0].plot(radii, tc[i], label=f"{times[i]/3600:.1f} h")
        ax[1].plot(radii, c[i], label=f"{times[i]/3600:.1f} h")
    ax[0].set(xlabel="到中心距离/cm", ylabel="温度/°C")
    ax[1].set(xlabel="到中心距离/cm", ylabel="含水率/(kg/kg)")
    for a in ax: a.grid(alpha=.25); a.legend(frameon=False)
    fig.tight_layout(); fig.savefig(figures_dir / "q2_profiles.pdf", format="pdf"); plt.close(fig)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    for j, label in [(0, "中心"), (10, "1 cm"), (20, "表面")]:
        ax[0].plot(times / 3600, tc[:, j], label=label)
        ax[1].plot(times / 3600, c[:, j], label=label)
    ax[0].set(xlabel="时间/h", ylabel="温度/°C")
    ax[1].set(xlabel="时间/h", ylabel="含水率/(kg/kg)")
    for a in ax: a.grid(alpha=.25); a.legend(frameon=False)
    fig.tight_layout(); fig.savefig(figures_dir / "q2_history.pdf", format="pdf"); plt.close(fig)
    # 全烘干过程温度与含水率时空热力图
    fig, ax = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    moisture_cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "blue_white_light_red", ["#2166ac", "#f7f7f7", "#EE0000"])
    for a, field, title, label, cmap in [(ax[0], tc, "全烘干温度时空分布", "温度/°C", "viridis"),
                                          (ax[1], c, "全烘干含水率时空分布", "含水率/(kg/kg)", moisture_cmap)]:
        mesh = a.pcolormesh(radii, times/3600, field, shading="auto", cmap=cmap, edgecolors="none", linewidth=0, antialiased=False, rasterized=True)
        a.set(xlabel="到中心距离/cm", ylabel="时间/h", title=title)
        fig.colorbar(mesh, ax=a, pad=0.02, label=label)
    fig.savefig(figures_dir / "q2_spatiotemporal_heatmaps.pdf", format="pdf", bbox_inches="tight"); plt.close(fig)
    conv = data["convergence"].item()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.semilogy(conv["times_h"], conv["moisture_difference"], label="1024→2048 含水率差")
    ax.semilogy(conv["times_h"], conv["temperature_difference"], label="1024→2048 温度差")
    ax.set(xlabel="时间/h", ylabel="最大场差"); ax.grid(alpha=.25); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(figures_dir / "q2_convergence.pdf", format="pdf"); plt.close(fig)
    return sorted(p.name for p in figures_dir.glob("q2_*.pdf"))


def markdown_table(times_h, values):
    lines = ["| 时间/h | 0 cm | 0.5 cm | 1 cm | 1.5 cm | 2 cm |",
             "|---:|---:|---:|---:|---:|---:|"]
    lines += ["| " + f"{t:g}" + " | " + " | ".join(f"{x:.4f}" for x in row) + " |"
              for t, row in zip(times_h, values)]
    return "\n".join(lines)


def write_report(path, summary):
    t, v = summary["tables"], summary["validation"]
    report = rf"""# 计算结果：问题二

本报告覆盖 Q2 前 3 h 的正式输出。模型从共同初值 \(T=301.15\,K,\ C=2.55\,kg/kg\) 重新开始，全程采用附录 3 的变物性公式；Q1 末态未作为 Q2 初态。题面要求的表 3、表 4 为前 3 h 每 0.5 h 的五个位置结果，完整 result2.xlsx 保存 1–10800 s、每秒、每 0.1 cm 的温度和含水率。

## 运行环境与方法

Python {summary["provenance"]["python"]}，NumPy {summary["provenance"]["numpy"]}，SciPy {summary["provenance"]["scipy"]}。输入 7 份文件通过 SHA-256 审计。采用圆柱环形有限体积、Kirchhoff 积分水分通量、表面半控制体 Robin 条件和自适应 BDF；附录 3 中 \(\rho,c_p,k\) 随 \(C\) 变化，\(D\) 同时随 \(T,C\) 变化，因此温度—含水率联合推进。

## 表 3：3 h 内药材温度（°C）

{markdown_table(t["times_h"], t["temperature_C"])}

## 表 4：3 h 内药材水分浓度（kg/kg）

{markdown_table(t["times_h"], t["moisture"])}

## 数值验证

以 \(N=1024\) 为正式网格，并用 \(N=512,2048\) 在表格时刻复核。1024→2048 的最大温度差为 {v["spatial_max_temperature_K"]:.3e} K，最大含水率差为 {v["spatial_max_moisture"]:.3e} kg/kg。紧收敛时间设置（rtol=5×10⁻⁹、atol=5×10⁻¹¹、最大步长 15 s）与正式设置相比，表格时刻最大温度差为 {v["temporal_max_temperature_K"]:.3e} K，最大含水率差为 {v["temporal_max_moisture"]:.3e} kg/kg。

正式解的最小含水率为 {v["min_moisture"]:.9f} kg/kg；归一化干基水量收支残差为 {v["max_water_balance_residual"]:.3e}。表面 Robin 残差最大值为 {v["max_surface_moisture_residual"]:.3e} m/s。上述检查验证的是当前变物性条件模型的离散一致性，不替代物性经验式和有效表面平衡浓度的实验验证。

## 结果解释与边界

3 h 内温度场已明显响应升温边界，而含水率场的变化集中在表层并向中心传播；不能用单一平均值替代径向场。Q2 的完整烘干时长和连续最大含水率事件属于 Q3 的后续计算，本报告不提前给出达标时间。附件 1 的 4 h 后环境延拓也不影响本次 0–3 h 正式表格，延长计算时需单独报告延拓口径。

## 产物与复现

- [result2.xlsx](../../results/q2/result2.xlsx)：两张正式输出工作表。
- [fields.npz](../../results/q2/fields.npz)：未舍入场、表格数据和收敛曲线数据。
- [summary.json](../../results/q2/summary.json)：参数、来源和验证记录。
- [表 3 数据](../../results/q2/table3.csv)、[表 4 数据](../../results/q2/table4.csv)。
- [径向剖面](../../figures/q2/q2_profiles.pdf)、[位置历史](../../figures/q2/q2_history.pdf)、[收敛对照](../../figures/q2/q2_convergence.pdf)。

运行 make q2 可复现本结果；原始模板不会被覆盖。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")


def run(output_dir, report_path, figures_dir):
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    sols = {}
    for n in GRIDS:
        sols[n] = solve_radial(n, appendix=3, duration_s=DURATION_S, rtol=2e-7,
                               atol=2e-9, max_step=60, align_environment=True)
        print(f"Q2 N={n} 完成，耗时累计 {time.perf_counter()-start:.2f} s", flush=True)
    solution = sols[1024]
    fields = solution.sample(TIMES_S, RADII_CM / 100)
    diag_times = TABLE_TIMES_S
    coarse = sols[512].sample(diag_times, RADII_CM / 100)
    fine = sols[2048].sample(diag_times, RADII_CM / 100)
    base = solution.sample(diag_times, RADII_CM / 100)
    tight = solve_radial(1024, appendix=3, duration_s=DURATION_S, rtol=5e-9,
                         atol=5e-11, max_step=15, align_environment=True)
    tight_base = tight.sample(diag_times, RADII_CM / 100)
    spatial_t = float(np.max(abs(fine.temperature_K - base.temperature_K)))
    spatial_c = float(np.max(abs(fine.moisture - base.moisture)))
    temporal_t = float(np.max(abs(tight_base.temperature_K - base.temperature_K)))
    temporal_c = float(np.max(abs(tight_base.moisture - base.moisture)))
    n, model = solution.model.n, solution.model
    balance = 2 * model.weights @ solution.y[n:2*n] + solution.y[-1] - 2.55
    residuals = []
    for t in diag_times:
        y = solution.state([t])[:, 0]
        *_, cs, _, _, _, base_d, a = model.fluxes(t, y)
        c = np.maximum(y[n:2*n], 1e-10); dr = model.radius(t) / n
        ca = model.environment(t)[1]
        residuals.append(abs(base_d[-1] * (kirchhoff(c[-1], a) - kirchhoff(cs, a))
                             - .5 * dr * model.km * (cs - ca)))
    tables = {"times_h": (diag_times / 3600).tolist(),
              "temperature_C": (base.temperature_K - 273.15)[:, TABLE_COLUMNS].tolist(),
              "moisture": base.moisture[:, TABLE_COLUMNS].tolist()}
    summary = {"scope": "Q2 first 3 h formal output; appendix 3 from common initial state",
               "provenance": provenance(), "configuration": solution.configuration, "tables": tables,
               "validation": {"grids": list(GRIDS), "spatial_max_temperature_K": spatial_t,
                              "spatial_max_moisture": spatial_c,
                              "temporal_max_temperature_K": temporal_t,
                              "temporal_max_moisture": temporal_c,
                              "min_moisture": float(fields.moisture.min()),
                              "max_water_balance_residual": float(np.max(abs(balance))),
                              "max_surface_moisture_residual": float(max(residuals)),
                              "nfev": {str(n): int(s.segments[-1].nfev) for n, s in sols.items()}}}
    conv = {"times_h": (diag_times / 3600).tolist(),
            "temperature_difference": np.max(abs(fine.temperature_K - base.temperature_K), axis=1).tolist(),
            "moisture_difference": np.max(abs(fine.moisture - base.moisture), axis=1).tolist()}
    np.savez_compressed(output_dir / "fields.npz", times_s=TIMES_S, radii_cm=RADII_CM,
                        temperature_C=fields.temperature_K - 273.15, moisture=fields.moisture,
                        convergence=conv)
    export_workbook(output_dir / "result2.xlsx", fields.temperature_K - 273.15, fields.moisture)
    summary["workbook"] = verify_workbook(output_dir / "result2.xlsx",
                                           fields.temperature_K - 273.15, fields.moisture)
    for i, key in enumerate(("temperature_C", "moisture"), start=3):
        with (output_dir / f"table{i}.csv").open("w", encoding="utf-8") as f:
            f.write("时间/h,0 cm,0.5 cm,1 cm,1.5 cm,2 cm\n")
            for t, row in zip(tables["times_h"], tables[key]):
                f.write(str(t) + "," + ",".join(f"{x:.4f}" for x in row) + "\n")
    summary["figures"] = plot_figures(output_dir, figures_dir)
    write_json(output_dir / "summary.json", summary)
    write_report(report_path, summary)
    artifacts = [output_dir / n for n in
                 ("result2.xlsx", "fields.npz", "summary.json", "table3.csv", "table4.csv")]
    artifacts += sorted(figures_dir.glob("q2_*.pdf"))
    write_json(output_dir / "artifact_manifest.json",
               {"files": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                          for p in artifacts}})
    print(f"Q2 正式结果与验证完成，耗时 {time.perf_counter()-start:.2f} s。", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results/q2")
    parser.add_argument("--report", type=Path, default=ROOT / "reports/q2/RESULTS_REPORT.md")
    parser.add_argument("--figures-dir", type=Path, default=ROOT / "figures/q2")
    args = parser.parse_args()
    run(args.output_dir, args.report, args.figures_dir)


if __name__ == "__main__":
    main()
