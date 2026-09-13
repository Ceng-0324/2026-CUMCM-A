"""生成 Q1 结果、独立基准与精度证据；保留输入模板，结果写入 results/q1。"""
from __future__ import annotations

import argparse
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import platform
import time
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import numpy as np
import scipy
import xlsxwriter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'common'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_io import NS, ROOT, col_number, read_xlsx, verify_inputs, write_json
from model import solve_radial
from q1_validation import diagnose, difference, heat_reference

TIMES = np.arange(1., 1801.)
RADII = np.arange(21)*.001
TABLE_TIMES = np.array([100, 300, 600, 900, 1200, 1500, 1800])
TABLE_COLUMNS = np.array([0, 5, 10, 15, 20])
GRIDS = [1024, 2048, 4096]
# 控制离散误差的验收阈值，不表示物性模型的置信区间。
LIMITS = dict(spatial_temperature_K=5e-6, spatial_moisture=4e-5,
              temporal_temperature_K=1e-6, temporal_moisture=1e-7,
              independent_heat_K=1e-6)
SOURCES = ['code/common/data_io.py', 'code/common/model.py', 'code/q1/q1_validation.py',
           'code/q1/problem1.py', 'code/q1/plot_q1.py']


def provenance():
    return dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                xlsxwriter=xlsxwriter.__version__,
                input_sha256={e['path']: e['sha256'] for e in verify_inputs()},
                code_sha256={p: sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES})


def rounded(array):
    return np.array([[float(f'{x:.4f}') for x in row] for row in array])


def export_workbook(path, temperature_C, moisture):
    template = read_xlsx(ROOT/'problemA/附件/附件3/result1.xlsx')
    with xlsxwriter.Workbook(path) as workbook:
        workbook.set_properties({'title': '问题一：预热阶段温度与水分浓度',
                                 'created': datetime(2000, 1, 1)})
        values_format = workbook.add_format({'num_format': '0.0000'})
        radius_format = workbook.add_format({'num_format': '0.0', 'bold': True})
        header_format = workbook.add_format({'bold': True, 'text_wrap': True})
        for name, array in [('温度', temperature_C), ('水分浓度', moisture)]:
            sheet = workbook.add_worksheet(name)
            sheet.write(0, 0, template[name]['rows'][1][1], header_format)
            sheet.write_row(0, 1, RADII*100, radius_format)
            for i, (t, row) in enumerate(zip(TIMES, rounded(array)), start=1):
                sheet.write_number(i, 0, int(t))
                sheet.write_row(i, 1, row, values_format)
            sheet.freeze_panes(1, 1)
            sheet.set_column(0, 0, 22)
            sheet.set_column(1, 21, 12)
            sheet.set_row(0, 32)


def verify_workbook(path, temperature_C, moisture):
    sheets = read_xlsx(path)
    if list(sheets) != ['温度', '水分浓度']:
        raise ValueError('Q1 工作表名称或顺序错误')
    for name, expected in [('温度', temperature_C), ('水分浓度', moisture)]:
        sheet = sheets[name]
        if sheet['dimension'] != 'A1:V1801' or len(sheet['rows']) != 1801:
            raise ValueError('Q1 工作簿应为表头 + 1800 行，时间 + 21 个半径列')
        if sheet['errors'] or sheet['formula_count'] or sheet['merges']:
            raise ValueError('Q1 工作簿含错误、公式或合并单元格')
        header = sheet['rows'][1]
        np.testing.assert_allclose([header[j] for j in range(2, 23)], RADII*100, atol=1e-12)
        rows = [sheet['rows'][i] for i in range(2, 1802)]
        if any(set(row) != set(range(1, 23)) for row in rows):
            raise ValueError('Q1 结果存在缺失或多余列')
        np.testing.assert_array_equal([row[1] for row in rows], TIMES)
        np.testing.assert_allclose([[row[j] for j in range(2, 23)] for row in rows],
                                   rounded(expected), rtol=0, atol=1e-12)
    with ZipFile(path) as archive:
        styles = ET.fromstring(archive.read('xl/styles.xml'))
        formats = {x.attrib['numFmtId'] for x in styles.findall('s:numFmts/s:numFmt', NS)
                   if x.attrib['formatCode'] == '0.0000'}
        xfs = styles.findall('s:cellXfs/s:xf', NS)
        for filename in ['xl/worksheets/sheet1.xml', 'xl/worksheets/sheet2.xml']:
            tree = ET.fromstring(archive.read(filename))
            for row in tree.findall('s:sheetData/s:row', NS)[1:]:
                for cell in row:
                    if col_number(cell.attrib['r']) > 1:
                        xf = xfs[int(cell.attrib.get('s', 0))]
                        if xf.attrib['numFmtId'] not in formats:
                            raise ValueError('Q1 结果未使用四位小数显示格式')
    return dict(sheets=list(sheets), data_rows_per_sheet=1800, radial_columns=21,
                numeric_field_cells=75600, dimension='A1:V1801',
                time_unit='s', radius_unit='cm', temperature_unit='°C',
                moisture_unit='kg/kg', decimal_places=4, all_cells_read_back=True)


def table_markdown(times, radii_cm, values):
    rows = ['| 时间/s | '+' | '.join(f'{r:g} cm' for r in radii_cm)+' |',
            '| ---: | '+' | '.join(['---:']*len(radii_cm))+' |']
    rows += ['| '+str(int(t))+' | '+' | '.join(f'{v:.4f}' for v in row)+' |'
             for t, row in zip(times, values)]
    return '\n'.join(rows)


def write_report(path, summary, with_figures):
    v, tables = summary['validation'], summary['tables']
    d = v['diagnostics']
    report = f'''# 计算结果：问题一

本报告覆盖一维径向、有效表面平衡浓度和无显式潜热假设下的 Q1 预热计算，包括中心/表面重构、连续场采样、正式工作簿及数值验证。Q2–Q4 的变物性、长期事件和收缩域结果见各问报告。这里的数值收敛不等同于实验验证。

## 运行环境与数据

Python {summary['provenance']['python']}，NumPy {summary['provenance']['numpy']}，SciPy {summary['provenance']['scipy']}，XlsxWriter {summary['provenance']['xlsxwriter']}；依赖锁定于 uv.lock。原始 7 份输入均通过 SHA-256 验证。附件 1 按时间线性插值，本问仅使用 0–1800 s，不使用 4 h 后延拓。

模板从 1 s 开始：两张表各 1800 行，半径 0–2 cm 每 0.1 cm，共 21 个位置；内部使用 s、m、K，导出温度为 °C。t=0 的均匀初值保存在完整精度数据中，不插入模板的时间序列。水分初值与 t=0 表面 Robin 条件不相容，采样接口在 t=0 返回题设初值；t>0 才恢复边界迹并检查 Robin 残差。

## 方法与公共接口

共用 solve_radial 和 RadialSolution.sample。有限体积离散沿用单元中点近似量解释；中心按偶二次式 (9q₀−q₁)/8 恢复。内部斜率由 PCHIP 确定，分段 Hermite 重构在中心强制零梯度、表面强制与通量一致的梯度。温度直接重构，水分在 K(C) 空间重构后反解；表面浓度由非线性半单元通量与 Robin 条件联合求根。

Q1 采用 {GRIDS[-1]} 个均匀径向单元、BDF、rtol=10⁻¹⁰、atol=10⁻¹¹、最大步长 10 s，在附件每个 60 s 插值节点分段积分。输出采样与内部步长分离。采样支持积分区间内任意时间、实际半径或材料坐标，越界默认报错，也可显式返回 NaN。Q3、Q4 在连续重构场上进一步定位达标事件。

## 问题一结果

### 表1：预热阶段温度（°C）

{table_markdown(TABLE_TIMES, np.array(tables['radii_cm']), tables['temperature_C'])}

### 表2：预热阶段含水率（kg/kg）

{table_markdown(TABLE_TIMES, np.array(tables['radii_cm']), tables['moisture'])}

1800 s 时，中心温度为 {tables['temperature_C'][-1][0]:.4f}°C，表面温度为 {tables['temperature_C'][-1][-1]:.4f}°C；中心与表面含水率分别为 {tables['moisture'][-1][0]:.4f}、{tables['moisture'][-1][-1]:.4f} kg/kg。预热后温度仍有径向差异，中心水分变化很小，不能把 1800 s 当成均匀热平衡状态。

## 数值精度与一致性

空间加密覆盖每秒、21 个输出半径，并额外覆盖包含近表层加密点的径向诊断网格。最后一次 {GRIDS[-2]}→{GRIDS[-1]} 加密，在工作簿网格上温度最大变化 {v['spatial_output'][-1]['max_temperature_difference_K']:.3e} K，含水率最大变化 {v['spatial_output'][-1]['max_moisture_difference']:.3e} kg/kg。最敏感位置在刚开始干燥的表层。基于观测收敛阶的 Richardson 后验估计见 summary.json；这不是严格数学误差上界。

时间容差收紧到 rtol=2×10⁻¹¹、atol=2×10⁻¹² 且最大步长降至 5 s 后，温度和含水率最大变化分别为 {v['temporal_output']['max_temperature_difference_K']:.3e} K、{v['temporal_output']['max_moisture_difference']:.3e} kg/kg。四位小数为输出格式，接近舍入分界的末位可能随加密变化；不能据此宣称材料真实值达到四位小数精度。

独立温度基准采用圆柱 Robin 特征展开，并对实际分段线性烘房输入逐段解析推进模态，不调用有限体积右端。工作簿网格上最大温度偏差为 {v['independent_heat_max_error_K']:.3e} K；256→512 模态的截断对照差为 {v['heat_series_truncation_K']:.3e} K。

| 检查 | 结果 |
| --- | ---: |
| 最小输出含水率 | {d['min_sample_moisture']:.9f} kg/kg |
| 离散干质量归一化水量收支残差 | {d['max_discrete_water_balance_residual']:.3e} |
| 独立表面通量时间积分的水量收支残差 | {d['independent_water_balance_residual']:.3e} |
| Q1 常热物性显热收支相对残差 | {d['independent_energy_balance_relative_residual']:.3e} |
| 表面换热 Robin 最大残差 | {d['max_surface_heat_Robin_residual_W_m2']:.3e} W/m² |
| 表面传质 Robin 最大残差 | {d['max_surface_moisture_Robin_residual_m_s']:.3e} m/s |
| 中心温度/含水率梯度 | 0 / 0 |
| 浓度下限保护触发次数 | {d['moisture_floor_evaluations']} |
| 工作簿逐格回读 | 75600 个结果单元格全部一致 |

边界残差验证重构和通量的一致性；离散积分检验求解收支。它们不能单独证明模型对真实药材适用，也不代表重构函数在每个控制体内严格保持体积平均值。实际全场误差由独立温度基准及水分加密对照评估。

## 端部近似及物理限制

另以相同换热条件的有限圆柱热方程特征展开检查中截面：在论文表格时空点，含端面换热与一维径向基准的最大温差为 {v['end_effect']['midplane_max_temperature_change_K']:.3e} K，模态加密变化为 {v['end_effect']['series_refinement_change_K']:.3e} K。这只支持本问预热时段中截面温度的径向近似；不证明端面附近、水分场或后续数十小时过程同样可以忽略端部。

有效平衡浓度与无显式潜热仍是题目数据不足条件下采用的 Q1 基线解释，未通过药材实验识别。复核确认空气浓度与药材干基含水率的分母不同；湿空气换算和潜热耦合情景对传质系数、水活度等额外假设敏感，因此不替换当前工作簿。相关情景与收支见 `results/q1/physics/summary.json`。热收支检验仅对 Q1 的常热物性显热方程成立，不能直接作为后续变物性和收缩模型的能量检验。

## 产物与复现

- [result1.xlsx](../../results/q1/result1.xlsx)：按原模板扩展的正式格式工作簿。
- [fields.npz](../../results/q1/fields.npz)：未舍入的逐秒场、初值、论文表格与剖面/验证图数据。
- [summary.json](../../results/q1/summary.json)：参数、数值表、误差对照、验收目标、来源哈希和完整验证记录。
- [table1.csv](../../results/q1/table1.csv)、[table2.csv](../../results/q1/table2.csv)：供论文手排版的四位小数表格。
- [artifact_manifest.json](../../results/q1/artifact_manifest.json)：生成产物哈希。

运行 make q1 生成结果和图件；make verify 在临时目录重算并比较数值、回读工作簿，原始模板不会被覆盖。Q1 运行入口为 code/q1/problem1.py；仅重算数值可加 --no-figures --output-dir results/local/q1-check --report results/local/q1-check/REPORT.md。
'''
    if with_figures:
        report += '''
## 数据图件

- [径向剖面](../../figures/q1/q1_profiles.pdf)：比较 100、600、1800 s 的温度与含水率梯度，数据来自 fields.npz。
- [位置随时间变化](../../figures/q1/q1_history.pdf)：中心、中间位置和表面的响应差异，数据来自 fields.npz。
- [精度对照](../../figures/q1/q1_convergence.pdf)：时空输出网格加密误差与独立热基准误差，数据来自 summary.json。
- [时空热力图](../../figures/q1/q1_spatiotemporal_heatmaps.pdf)：预热阶段温度与含水率的时间—半径分布，数据来自 fields.npz。

各图按内容使用中文或英文坐标与图例，PDF 为矢量输出，图内不设置总标题。热力图采用 11×11 取样方格，生成环境与文件哈希记录于 artifact_manifest.json。
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding='utf-8')


def run(output_dir, report_path, figures_dir=None):
    for target in [output_dir, report_path, figures_dir]:
        if target is not None and target.resolve().is_relative_to((ROOT/'problemA').resolve()):
            raise ValueError('生成产物禁止写入原始题面/附件目录')
    source = provenance()
    start = time.perf_counter()
    output_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_times = np.array([1, 10, 60, 100, 300, 600, 900, 1200, 1500, 1800])
    diagnostic_radii = np.unique(np.r_[np.linspace(0, .02, 401), .02-np.geomspace(1e-7, 1e-3, 80)])
    spatial, spatial_dense = [], []
    previous = previous_dense = None
    for n in GRIDS:
        solution = solve_radial(n, appendix=2, rtol=1e-10, atol=1e-11, max_step=10,
                                align_environment=True)
        fields = solution.sample(TIMES, RADII)
        dense = solution.sample(diagnostic_times, diagnostic_radii)
        if previous is not None:
            spatial.append(dict(coarse_n=n//2, fine_n=n, **difference(previous, fields)))
            spatial_dense.append(dict(coarse_n=n//2, fine_n=n, **difference(previous_dense, dense)))
        previous, previous_dense = fields, dense
        print(f'Q1 N={n} 完成，t=1800 s 表面 C={fields.moisture[-1,-1]:.9f}', flush=True)
    diagnostics = diagnose(solution, fields)
    # 保存绘图所需剖面后释放细网格解，给时间加密复算留出内存。
    profile = solution.sample(TABLE_TIMES, np.linspace(0, .02, 401))
    configuration = solution.configuration
    room = solution.model.room
    del solution
    tight = solve_radial(GRIDS[-1], appendix=2, rtol=2e-11, atol=2e-12, max_step=5,
                         align_environment=True)
    tight_fields = tight.sample(TIMES, RADII)
    temporal = difference(fields, tight_fields)
    del tight
    reference = heat_reference(room, TIMES, RADII, modes=256)
    reference_fine = heat_reference(room, TIMES, RADII, modes=512)
    heat_error = float(np.max(abs(fields.temperature_K-273.15-reference_fine)))
    end_coarse = heat_reference(room, TABLE_TIMES, RADII[TABLE_COLUMNS], modes=128, axial_modes=128)
    end_fine = heat_reference(room, TABLE_TIMES, RADII[TABLE_COLUMNS], modes=256, axial_modes=256)
    end_radial = heat_reference(room, TABLE_TIMES, RADII[TABLE_COLUMNS], modes=512)
    estimates = {}
    for key in ['max_temperature_difference_K', 'max_moisture_difference']:
        ratio = spatial[-2][key]/spatial[-1][key]
        estimates[key] = dict(observed_order=float(np.log2(ratio)),
                              fine_grid_error_estimate=spatial[-1][key]/(ratio-1))
    tests = [(spatial[-1]['max_temperature_difference_K'], LIMITS['spatial_temperature_K']),
             (spatial[-1]['max_moisture_difference'], LIMITS['spatial_moisture']),
             (spatial_dense[-1]['max_temperature_difference_K'], LIMITS['spatial_temperature_K']),
             (spatial_dense[-1]['max_moisture_difference'], LIMITS['spatial_moisture']),
             (temporal['max_temperature_difference_K'], LIMITS['temporal_temperature_K']),
             (temporal['max_moisture_difference'], LIMITS['temporal_moisture']),
             (heat_error, LIMITS['independent_heat_K'])]
    if any(value > limit for value, limit in tests):
        raise RuntimeError(f'Q1 数值目标未通过：{tests}')
    temp_C = fields.temperature_K-273.15
    tables = dict(times_s=TABLE_TIMES.tolist(), radii_cm=(RADII[TABLE_COLUMNS]*100).tolist(),
                  temperature_C=temp_C[TABLE_TIMES-1][:, TABLE_COLUMNS].tolist(),
                  moisture=fields.moisture[TABLE_TIMES-1][:, TABLE_COLUMNS].tolist())
    export_workbook(output_dir/'result1.xlsx', temp_C, fields.moisture)
    workbook = verify_workbook(output_dir/'result1.xlsx', temp_C, fields.moisture)
    np.savez_compressed(output_dir/'fields.npz', times_s=TIMES, radii_m=RADII,
                        temperature_C=temp_C, moisture=fields.moisture,
                        initial_temperature_C=np.full(21, 28.), initial_moisture=np.full(21, 2.55),
                        profile_times_s=TABLE_TIMES, profile_radii_m=profile.radius_m[0],
                        profile_temperature_C=profile.temperature_K-273.15, profile_moisture=profile.moisture,
                        heat_reference_C=reference_fine)
    for i, name in enumerate(['temperature_C', 'moisture'], start=1):
        with (output_dir/f'table{i}.csv').open('w', encoding='utf-8', newline='') as stream:
            stream.write('时间/s,0 cm,0.5 cm,1 cm,1.5 cm,2 cm\n')
            for t, row in zip(TABLE_TIMES, tables[name]):
                stream.write(str(t)+','+','.join(f'{v:.4f}' for v in row)+'\n')
    summary = dict(scope='Q1 conditional radial model; numerical validation, not experimental validation',
                   provenance=source, configuration=configuration, tables=tables,
                   validation=dict(targets=LIMITS, passed=True, spatial_output=spatial,
                       spatial_dense=spatial_dense, temporal_output=temporal,
                       richardson_estimates=estimates, diagnostics=diagnostics,
                       independent_heat_max_error_K=heat_error,
                       heat_series_truncation_K=float(np.max(abs(reference-reference_fine))),
                       heat_error_by_time_K=np.max(abs(temp_C-reference_fine), axis=1).tolist(),
                       end_effect=dict(midplane_max_temperature_change_K=float(np.max(abs(end_fine-end_radial))),
                           series_refinement_change_K=float(np.max(abs(end_coarse-end_fine))))),
                   workbook=workbook)
    write_json(output_dir/'summary.json', summary)
    plot_info = None
    if figures_dir is not None:
        from plot_q1 import plot
        plot_info = plot(output_dir, figures_dir)
    write_report(report_path, summary, figures_dir is not None)
    artifacts = [output_dir/name for name in ['fields.npz', 'result1.xlsx', 'summary.json',
                                              'table1.csv', 'table2.csv']]
    if figures_dir is not None:
        artifacts += sorted(figures_dir.glob('q1_*.pdf'))
    write_json(output_dir/'artifact_manifest.json', dict(plot=plot_info,
        files={p.name: sha256(p.read_bytes()).hexdigest() for p in artifacts}))
    print(f'Q1 数值与输出验收通过，耗时 {time.perf_counter()-start:.2f} s。', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'results/q1')
    parser.add_argument('--report', type=Path, default=ROOT/'reports/q1/RESULTS_REPORT.md')
    parser.add_argument('--figures-dir', type=Path, default=ROOT/'figures/q1')
    parser.add_argument('--no-figures', action='store_true')
    args = parser.parse_args()
    run(args.output_dir, args.report, None if args.no_figures else args.figures_dir)


if __name__ == '__main__':
    main()
