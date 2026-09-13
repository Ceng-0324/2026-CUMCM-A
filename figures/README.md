# 图件索引

| 目录 | 内容 | 状态 |
|---|---|---|
| [`q1/`](q1/) | Q1 径向剖面、位置历史、精度对照 PDF，以及圆柱边界与环形控制体立体结构图 | 已完成 |
| [`q2/`](q2/) | Q2 数据图 | 已完成 |
| [`q3/`](q3/) | Q3 事件与误差图 | 已完成 |
| [`q4/`](q4/) | Q4 收缩和机制图 | 已完成 |

| 根目录 | `fig_roadmap.pdf`（按 `paper/sections/2_analysis.tex` 重构的问题分析总体流程）、`fig_question_progression.pdf`（四问递进关系） | 已完成 |

数据型图件由对应问题的生成脚本产生；非数据方法图保留 `.drawio` 源文件和 PDF，由 `reports/DRAWIO_REPORT.md` 说明依据与插入位置。

总体流程图复现：`MPLCONFIGDIR=.mpl-cache UV_CACHE_DIR=.uv-cache uv run --frozen python figures/render_analysis_overview.py`。
