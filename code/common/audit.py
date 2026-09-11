"""审计 A 题输入，默认只读取；--output 保存派生审计结果。"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
import statistics

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_io import ROOT, input_rows, read_xlsx, verify_inputs, write_json


def audit_inputs(root: Path = ROOT) -> dict:
    files = verify_inputs(root)
    workbooks = {}
    for entry in files:
        if not entry['path'].endswith('.xlsx'):
            continue
        sheets = read_xlsx(root / entry['path'])
        workbooks[entry['path']] = {
            name: {'dimension': sheet['dimension'], 'rows': len(sheet['rows']),
                   'formula_count': sheet['formula_count'], 'errors': sheet['errors']}
            for name, sheet in sheets.items()
        }
        if any(sheet['errors'] for sheet in sheets.values()):
            raise ValueError(f"Excel 错误单元格：{entry['path']}")
    # Explicit columns and time grids catch mislabeled or transposed workbooks.
    room = input_rows('附件1.xlsx', root)
    radii = input_rows('附件2.xlsx', root)
    for name, rows, count, columns, step in [
        ('附件1', room, 241, 3, 60), ('附件2', radii, 145, 2, 1800)
    ]:
        if len(rows) != count:
            raise ValueError(f'{name} 数据行数应为 {count}')
        for i, row in enumerate(rows):
            if set(row) != set(range(1, columns + 1)):
                raise ValueError(f'{name} 第 {i + 2} 行字段缺失或多余')
            if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in row.values()):
                raise ValueError(f'{name} 第 {i + 2} 行存在非数值/非有限值')
            if row[1] != i * step:
                raise ValueError(f'{name} 时间轴错误：第 {i + 2} 行')
    if min(row[2] for row in radii) <= 0:
        raise ValueError('药材半径必须为正')
    tail = [r for r in room if r[1] >= 10800]
    return {
        'scope': 'A 题输入结构和原始字节校验，不是物理模型验收',
        'files_verified': len(files), 'workbooks': workbooks,
        'room': {'rows': len(room), 'first': room[0], 'last': room[-1],
                 'tail_mean_temperature_C': statistics.fmean(r[2] for r in tail),
                 'tail_mean_concentration': statistics.fmean(r[3] for r in tail)},
        'radius': {'rows': len(radii), 'first': radii[0], 'last': radii[-1],
                   'increases': sum(b[2] > a[2] for a, b in zip(radii, radii[1:]))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='审计 JSON 路径，不修改原始附件')
    args = parser.parse_args()
    result = audit_inputs()
    if args.output:
        write_json(args.output, result)
    print(f"A 题审计通过：{result['files_verified']} 份原始文件，"
          f"烘房 {result['room']['rows']} 点，半径 {result['radius']['rows']} 点")


if __name__ == '__main__':
    main()
