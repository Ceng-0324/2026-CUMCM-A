"""仅从已保存的 Q1 数据生成中文矢量图。"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'common'))

from data_io import ROOT

# Keep font caches writable in a clean checkout and in CI.
os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'.mpl-cache'))
os.environ.setdefault('XDG_CACHE_HOME', str(ROOT/'.mpl-cache'))
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager
from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter
import matplotlib.pyplot as plt
import numpy as np


def plot(output_dir, figures_dir):
    fonts = {font.name for font in font_manager.fontManager.ttflist}
    candidates = ['Microsoft YaHei', 'SimHei', 'STHeiti', 'Arial Unicode MS',
                  'Noto Sans CJK SC', 'Source Han Sans SC', 'Hiragino Sans GB']
    family = next((name for name in candidates if name in fonts), None)
    if family is None:
        raise RuntimeError('中文图件需要 Noto Sans CJK SC 等中文字体；数值复验可使用 --no-figures')
    # TTC/OTF may contain CFF outlines that cannot be embedded as TrueType.
    # Conservatively use vector Type 3 outlines for those font containers.
    pdf_fonttype = 42 if Path(font_manager.findfont(family)).suffix.lower() == '.ttf' else 3
    plt.rcParams.update({'font.family': [family, 'DejaVu Sans'], 'font.size': 8, 'axes.unicode_minus': False,
                         'mathtext.fontset': 'dejavusans',
                         'pdf.fonttype': pdf_fonttype, 'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.linewidth': 0.6, 'xtick.direction': 'out', 'ytick.direction': 'out',
                         'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
                         'xtick.major.size': 3, 'ytick.major.size': 3})
    figures_dir.mkdir(parents=True, exist_ok=True)
    fields = np.load(output_dir/'fields.npz')
    summary = json.loads((output_dir/'summary.json').read_text(encoding='utf-8'))
    colors = ['#0072B2', '#D55E00', '#009E73']
    styles = ['-', '--', '-.']
    metadata = {'CreationDate': datetime(2000, 1, 1, tzinfo=timezone.utc)}

    def save(fig, name):
        fig.savefig(figures_dir/name, bbox_inches='tight', metadata=metadata)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
    for color, style, i in zip(colors, styles, [0, 2, 6]):
        for ax, key in zip(axes, ['profile_temperature_C', 'profile_moisture']):
            ax.plot(fields['profile_radii_m']*100, fields[key][i], color=color, ls=style,
                    label=f'{int(fields["profile_times_s"][i])} s')
    for ax, label in zip(axes, ['温度 / °C', '干基含水率 / (kg/kg)']):
        ax.set(xlabel='距中心半径 / cm', ylabel=label, xlim=(0, 2))
        ax.legend(frameon=False)
    save(fig, 'q1_profiles.pdf')

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
    for color, style, i, label in zip(colors, styles, [0, 10, 20], ['中心', '半径 1 cm', '表面']):
        for ax, key in zip(axes, ['temperature_C', 'moisture']):
            initial = 28. if key == 'temperature_C' else 2.55
            ax.plot(np.r_[0, fields['times_s']]/60, np.r_[initial, fields[key][:, i]],
                    color=color, ls=style, label=label)
    for ax, label in zip(axes, ['温度 / °C', '干基含水率 / (kg/kg)']):
        ax.set(xlabel='时间 / min', ylabel=label, xlim=(0, 30))
        ax.legend(frameon=False)
    save(fig, 'q1_history.pdf')

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5), layout='constrained')
    convergence = summary['validation']['spatial_output']
    ns = [item['fine_n'] for item in convergence]
    cs = [item['max_moisture_difference'] for item in convergence]
    axes[0].loglog(ns, cs, 'o-', color=colors[0], label='相邻网格最大差')
    axes[0].loglog(ns, [cs[0], cs[0]/4], '--', color=colors[1], label='二阶参考斜率')
    axes[0].set(xlabel='加密后单元数', ylabel='含水率最大差 / (kg/kg)')
    # Plain scientific labels avoid mathdefault selecting a CJK font without U+2212.
    axes[0].xaxis.set_major_locator(FixedLocator(ns))
    axes[0].xaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:.0f}'))
    axes[0].xaxis.set_minor_formatter(NullFormatter())
    axes[0].yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    axes[0].yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:.0e}'))
    axes[0].yaxis.set_minor_formatter(NullFormatter())
    axes[0].legend(frameon=False)
    axes[1].plot(fields['times_s']/60, summary['validation']['heat_error_by_time_K'], color=colors[0])
    axes[1].set(xlabel='时间 / min', ylabel='与独立热基准的最大偏差 / K', xlim=(0, 30))
    axes[1].ticklabel_format(axis='y', style='sci', scilimits=(0, 0))
    save(fig, 'q1_convergence.pdf')

    # 时空热力图：按期刊矩阵热力图样式取样为 11×11 方格，数据仍来自正式场。
    # 时间取 0、3、…、30 min；半径取 0、0.2、…、2.0 cm，首行使用题设初值。
    sample_times_s = np.arange(0.0, 1800.1, 180.0)
    sample_radius_idx = np.arange(0, 21, 2)
    sample_time_idx = (sample_times_s[1:] - 1).astype(int)
    matrices = {
        'temperature_C': np.vstack([fields['initial_temperature_C'][sample_radius_idx],
                                    fields['temperature_C'][sample_time_idx][:, sample_radius_idx]]),
        'moisture': np.vstack([fields['initial_moisture'][sample_radius_idx],
                               fields['moisture'][sample_time_idx][:, sample_radius_idx]]),
    }
    radius_labels = [f'{x:.1f}' for x in np.linspace(0, 2, 11)]
    time_labels = [f'{x:g}' for x in np.arange(0, 31, 3)]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), layout='constrained')
    for ax, key, panel, cbar_label, vmin, vmax in zip(
        axes, ['temperature_C', 'moisture'], ['(a)', '(b)'],
        ['温度 / °C', '干基含水率 / (kg/kg)'], [28.0, 1.5], [37.0, 2.55]):
        cmap = ('viridis' if key == 'temperature_C' else
                matplotlib.colors.LinearSegmentedColormap.from_list(
                    'blue_white_deep_red',
                    ['#2166ac', '#f7f7f7', '#f4a582', '#b2182b']))
        im = ax.imshow(matrices[key], cmap=cmap, vmin=vmin, vmax=vmax,
                       interpolation='nearest', aspect='equal', origin='upper')
        # 与参考文档相同的白色方格边界；仅用于区分取样单元，不表示新网格。
        ax.set_xticks(np.arange(-.5, 11, 1), minor=True)
        ax.set_yticks(np.arange(-.5, 11, 1), minor=True)
        ax.grid(which='minor', color='white', linewidth=0.8)
        ax.tick_params(which='minor', length=0)
        ax.set_xticks(np.arange(11), labels=radius_labels)
        ax.set_yticks(np.arange(11), labels=time_labels)
        ax.tick_params(labelsize=7, width=0.5, length=3)
        ax.set_xlabel('距中心半径 / cm')
        ax.set_ylabel('时间 / min')
        ax.text(-0.10, 1.08, panel, transform=ax.transAxes,
                fontsize=9, fontweight='bold', va='top')
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(cbar_label, fontsize=7)
        cbar.ax.tick_params(labelsize=7, width=0.5, length=3)
        cbar.outline.set_linewidth(0.5)
    save(fig, 'q1_spatiotemporal_heatmaps.pdf')
    return dict(matplotlib=matplotlib.__version__, font_family=family, pdf_fonttype=pdf_fonttype,
                files=['q1_profiles.pdf', 'q1_history.pdf', 'q1_convergence.pdf',
                       'q1_spatiotemporal_heatmaps.pdf'],
                data_sources=['fields.npz', 'summary.json'])
