# DrawIO 图示生成报告

## 图示清单

| 文件 | 类型 | 依据 | 论文用途 | 状态 |
|---|---|---|---|---|
| [`figures/fig_roadmap.drawio`](../figures/fig_roadmap.drawio) / [`fig_roadmap.pdf`](../figures/fig_roadmap.pdf) | 总体技术路线 | `reports/ANALYSIS_MODELING_REPORT.md` | 绪论或问题重述后概括统一模型与验证闭环 | 已生成 |
| [`figures/fig_question_progression.drawio`](../figures/fig_question_progression.drawio) / [`fig_question_progression.pdf`](../figures/fig_question_progression.pdf) | 四问递进关系 | `reports/methods_comparison.md` | 问题分析总述，说明四问递进 | 已生成 |
| [`figures/q2/fig_q2_coupling.drawio`](../figures/q2/fig_q2_coupling.drawio) / [`fig_q2_coupling.pdf`](../figures/q2/fig_q2_coupling.pdf) | Q2 模型结构图 | `reports/q2/METHOD_OVERVIEW.md` | Q2 模型建立小节，压缩双向反馈文字 | 已生成 |
| [`figures/q4/fig_q4_material_event.drawio`](../figures/q4/fig_q4_material_event.drawio) / [`fig_q4_material_event.pdf`](../figures/q4/fig_q4_material_event.pdf) | Q4 流程图 | `reports/q4/problem4_algorithm_analysis.md` | Q4 算法小节，展示坐标变换和事件定位 | 已生成 |
| [`figures/q1/fig_q1_3d_cylinder_model.drawio`](../figures/q1/fig_q1_3d_cylinder_model.drawio) / [`fig_q1_3d_cylinder_model.pdf`](../figures/q1/fig_q1_3d_cylinder_model.pdf) | Q1 三维几何与边界示意 | `paper/sections/5_problem1.tex`、`reports/ANALYSIS_MODELING_REPORT.md` | Q1 一维径向模型小节，说明圆柱、径向坐标、真实表面与 Robin 交换 | 已生成 |
| [`figures/q1/fig_q1_3d_control_volume.drawio`](../figures/q1/fig_q1_3d_control_volume.drawio) / [`fig_q1_3d_control_volume.pdf`](../figures/q1/fig_q1_3d_control_volume.pdf) | Q1 三维环形控制体与界面通量 | `paper/sections/5_problem1.tex`、`reports/ANALYSIS_MODELING_REPORT.md` | Q1 有限体积离散小节，说明 $r_{i\pm1/2}$、$V_i$ 及共享通量守恒 | 已生成 |

## 未生成图示

未单独绘制 Q1、Q3 流程图：两者分别是统一求解骨架的基线实例和 Q2 模型上的阈值后处理，独立成图会重复技术路线或递进关系图。曲线、剖面和收敛图仍由 `3coding-visual` 负责。

## 导出与自检

本机未安装 DrawIO CLI；`.drawio` 源文件可直接用 diagrams.net 编辑。浏览器无头打印异常退出，故已有方法图采用临时 ReportLab 脚本导出。Q1 两张立体结构图由 [`figures/q1/render_q1_3d_figures.py`](../figures/q1/render_q1_3d_figures.py) 生成 PDF，并将同一 SVG 矢量页嵌入 `.drawio` 源文件，避免源图与导出图分叉。已用 `pdfinfo` 检查新增 PDF 为单页且非空，并用 XML 解析确认 `.drawio` 源文件结构完整；同时将 PDF 转 PNG 做了标签、箭头和重叠检查。

## 给论文阶段的嵌入建议

- `fig_roadmap.pdf`：放“问题重述/总体思路”之后，可压缩共同框架的重复过渡语；PDE、边界、物性公式和误差分析必须保留。
- `fig_question_progression.pdf`：放“四问关系”小节，可压缩递进过渡句；独立初值、时间延拓和收缩边界仍需说明。
- `q2/fig_q2_coupling.pdf`：放 Q2 模型建立处，可压缩反馈关系文字；经验物性公式、边界和验证不能由图替代。
- `q4/fig_q4_material_event.pdf`：放 Q4 算法处，可压缩步骤描述；固定域 PDE、`1/R^2`/`1/R` 缩放、极值判据和后继检查必须保留。
- `q1/fig_q1_3d_cylinder_model.pdf`：放 Q1“一维径向模型”之后，说明几何、中心对称和表面 Robin 条件；不要将其描述为温度或含水率结果图。
- `q1/fig_q1_3d_control_volume.pdf`：放 Q1“圆柱环形有限体积离散”开头，说明控制体边界、几何权重和共享界面通量；半离散守恒式仍需在正文保留。
