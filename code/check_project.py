"""检查有效文档、证据来源及迁移回归；可在临时目录重新计算。"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote

from data_io import ROOT, verify_inputs


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def check_links():
    docs = [*ROOT.glob('*.md'), *(ROOT / 'reports').glob('*.md'), ROOT / 'results/README.md']
    count = 0
    for doc in docs:
        content = doc.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            local = unquote(target.split('#', 1)[0].strip('<>'))
            require((doc.parent / local).exists(), f'{doc.relative_to(ROOT)} 链接失效：{target}')
            count += 1
    return count


def compare_numbers(actual, expected, trail='result'):
    """跨平台允许小浮点差异；不要求求解器调用次数和耗时一致。"""
    if isinstance(expected, dict):
        for key, value in expected.items():
            if key in {'elapsed_s', 'rhs_evaluations', 'provenance'}:
                continue
            require(key in actual, f'{trail} 缺少 {key}')
            compare_numbers(actual[key], value, f'{trail}.{key}')
    elif isinstance(expected, list):
        require(len(actual) == len(expected), f'{trail} 长度改变')
        for i, (a, e) in enumerate(zip(actual, expected)):
            compare_numbers(a, e, f'{trail}[{i}]')
    elif isinstance(expected, bool) or expected is None or isinstance(expected, str):
        require(actual == expected, f'{trail} 不一致')
    elif isinstance(expected, (int, float)):
        tolerance = 1e-4 if trail.endswith('hours') else 2e-6
        if trail.endswith('max_error'):
            tolerance = 1e-8
        require(isinstance(actual, (int, float)) and math.isclose(actual, expected, rel_tol=1e-7, abs_tol=tolerance),
                f'{trail} 回归差异：{actual} vs {expected}')


def check_evidence():
    inputs = {e['path']: e['sha256'] for e in verify_inputs()}
    results = {}
    for name in ['feasibility', 'mechanism']:
        data = read(ROOT / f'results/probes/{name}.json')
        source = data['provenance']
        require(source['input_sha256'] == inputs, f'{name} 输入来源不一致')
        require(set(source['code_sha256']) == {'code/data_io.py', 'code/model.py', 'code/probes.py'},
                f'{name} 代码来源记录不完整')
        for path, digest in source['code_sha256'].items():
            require(sha256((ROOT / path).read_bytes()).hexdigest() == digest,
                    f'{name} 代码已变化：{path}；请审查后 make probe 更新证据')
        runs = data['runs'].values() if isinstance(data['runs'], dict) else data['runs']
        for run in runs:
            require(run['success'] and run['drying_event_hours'] is not None, f'{name} 未完成事件计算')
            require(run['min_C'] > 0 and run['drying_event_hours'] > 0, f'{name} 非物理解')
            require(run['max_dry_mass_normalized_balance_residual'] < 2e-6, f'{name} 离散守恒失败')
            require(not run['radius_extrapolated_after_72h'], f'{name} 使用了尚未验收的半径外推')
            require(run['event_uses_max_cell_C_not_certified_continuous_max'], '不得把原型事件标为连续域认证')
        results[name] = data

    # 目录工程化必须保持历史原型的数值含义；后续改模型应有意更新回归契约。
    original = ROOT / 'archive/selection/results/original'
    old_f = read(original / 'A_feasibility_probe.json')
    old_m = read(original / 'A_mechanism_probe.json')
    compare_numbers(results['feasibility']['runs'], old_f['runs'], 'migration.feasibility')
    compare_numbers(results['feasibility']['analytic_checks'], old_f['analytic_checks'], 'migration.analytic')
    compare_numbers(results['mechanism']['runs'], old_m['runs'], 'migration.mechanism')
    compare_numbers(results['mechanism']['effects'], old_m['effects'], 'migration.effects')

    effects = results['mechanism']['effects']
    require(math.isclose(effects['radius_order_averaged_hours'] + effects['properties_order_averaged_hours'],
                         effects['total_change_hours'], abs_tol=1e-10), '机制贡献未加总为净变化')
    report = (ROOT / 'reports/ANALYSIS_MODELING_REPORT.md').read_text(encoding='utf-8')
    # 报告保留六位小数；在小容差内比对表中的数值，允许跨平台末位舍入。
    report_numbers = [float(x) for x in re.findall(r'(?<![\w.])-?\d+\.\d{6}(?!\d)', report)]
    for run in results['mechanism']['runs'].values():
        require(any(abs(x-run['drying_event_hours']) < 2e-6 for x in report_numbers), '报告机制表与结果不一致')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recompute', action='store_true')
    args = parser.parse_args()
    for name in ['README.md', 'AGENTS.md', 'plan.md', 'todo.md', 'uv.lock',
                 'reports/ANALYSIS_MODELING_REPORT.md', 'archive/selection/README.md']:
        require((ROOT / name).is_file(), f'缺少工程文件：{name}')
    link_count = check_links()
    recorded = check_evidence()
    if args.recompute:
        with tempfile.TemporaryDirectory(prefix='cumcm-a-verify-') as tmp:
            subprocess.run([sys.executable, str(ROOT / 'code/probes.py'), '--mode', 'all',
                            '--output-dir', tmp], check=True, cwd=ROOT)
            for name, expected in recorded.items():
                compare_numbers(read(Path(tmp) / f'{name}.json'), expected, f'recompute.{name}')
        print('临时重算通过：14 次原型试算，记录结果未被覆盖。')
    print(f'工程检查通过：{link_count} 处本地文档链接、输入/代码来源和历史数值回归。')


if __name__ == '__main__':
    main()
