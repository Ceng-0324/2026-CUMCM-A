"""运行可行性/机制对照原型；不生成正式 result 工作簿。"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import platform
import sys

import numpy as np
import scipy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_io import ROOT, verify_inputs, write_json
from model import analytic_radial_check, probe_a

ASSUMPTIONS = [
    '1D radial cylinder; no axial/latent heat terms',
    'thermal empirical density only used in heat capacity; not asserted as dry skeleton density',
    'homogeneous contracting dry skeleton, constant material dry-mass weights',
    'bulk Robin mass coefficient assumed inherited for all problems',
    'room concentration used as effective surface-equilibrium concentration',
    'radius linear interpolation; held constant beyond 72h if required',
    'Kirchhoff flux for nonlinear moisture; BDF integration',
    'Only conditional feasibility; no claim of unique official model or four-decimal accuracy',
]


def provenance() -> dict:
    files = verify_inputs()
    code = ['code/common/data_io.py', 'code/common/model.py', 'code/common/probes.py']
    return {
        'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
        'input_sha256': {e['path']: e['sha256'] for e in files},
        'code_sha256': {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in code},
    }


def feasibility(grids: list[int]) -> dict:
    result = {'assumptions': ASSUMPTIONS, 'analytic_checks': [], 'runs': []}
    for n in grids:
        result['analytic_checks'].append(analytic_radial_check(n))
        for appendix, shrink in [(3, False), (4, True)]:
            result['runs'].append(probe_a(n, appendix=appendix, shrink=shrink))
    for appendix, shrink in [(3, False), (4, True)]:
        result['runs'].append(probe_a(max(grids), appendix=appendix, shrink=shrink,
                                     rtol=2e-7, max_step=300))
        result['runs'].append(probe_a(max(grids), appendix=appendix, shrink=shrink,
                                     boundary='last'))
    return result


def mechanism() -> dict:
    runs = {}
    for name, appendix, shrink in [('base', 3, False), ('radius_only', 3, True),
                                   ('properties_only', 4, False), ('both', 4, True)]:
        runs[name] = probe_a(128, appendix=appendix, shrink=shrink,
                            rtol=2e-7, max_step=300, max_hours=200)
    t00, t10, t01, t11 = [runs[k]['drying_event_hours']
                         for k in ['base', 'radius_only', 'properties_only', 'both']]
    if any(t is None for t in [t00, t10, t01, t11]):
        raise RuntimeError('一个机制对照未在规定时间内达到阈值')
    effects = {
        'radius_order_averaged_hours': .5*((t10-t00)+(t11-t01)),
        'properties_order_averaged_hours': .5*((t01-t00)+(t11-t10)),
        'interaction_hours': t11-t10-t01+t00,
        'total_change_hours': t11-t00,
    }
    return {
        'scope': 'Conditional mechanism study, not official answers or physical causal identification',
        'assumptions': ASSUMPTIONS,
        'property_change': 'All rho, cp, k, D formulas change together',
        'radius_only_uses_given_empirical_radius_curve': True,
        'counterfactual_radius_is_prescribed_not_induced_by_simulated_moisture': True,
        'runs': runs, 'effects': effects,
    }


def save(path: Path, result: dict, source: dict) -> None:
    runs = result['runs']
    iterable = runs.values() if isinstance(runs, dict) else runs
    runtimes = [run.pop('elapsed_s') for run in iterable]
    result['provenance'] = source
    write_json(path, result)
    print(f'{path.name}: {len(runtimes)} 次试算，计算耗时合计 {sum(runtimes):.3f} s')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['feasibility', 'mechanism', 'all'], default='all')
    parser.add_argument('--grids', nargs='+', type=int, default=[32, 64, 128])
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'results/probes')
    args = parser.parse_args()
    if args.grids != sorted(set(args.grids)) or min(args.grids) < 4:
        parser.error('grids 必须为递增、无重复且不小于 4 的整数')
    source = provenance()
    if args.mode in ['feasibility', 'all']:
        save(args.output_dir / 'feasibility.json', feasibility(args.grids), source)
    if args.mode in ['mechanism', 'all']:
        save(args.output_dir / 'mechanism.json', mechanism(), source)
    print('历史原型复算完成；最大单元事件与各问正式连续场事件口径不同。')


if __name__ == '__main__':
    main()
