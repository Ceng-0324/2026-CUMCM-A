"""生成 Q1 结果、独立基准与精度证据；保留输入模板，结果写入 results/q1。"""
from __future__ import annotations

import argparse
from datetime import datetime
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
def provenance():
    return dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                xlsxwriter=xlsxwriter.__version__,
                input_sha256={e['path']: e['sha256'] for e in verify_inputs()})


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






def run(output_dir, figures_dir=None):
    for target in [output_dir, figures_dir]:
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
    print(f'Q1 数值与输出验收通过，耗时 {time.perf_counter()-start:.2f} s。', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'results/q1')
    parser.add_argument('--figures-dir', type=Path, default=ROOT/'figures/q1')
    args = parser.parse_args()
    run(args.output_dir, args.figures_dir)


if __name__ == '__main__':
    main()
