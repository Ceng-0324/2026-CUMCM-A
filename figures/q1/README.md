# Q1 图件

- `q1_profiles.pdf`：100、600、1800 s 径向温度与含水率剖面。
- `q1_history.pdf`：中心、1 cm 和表面随时间变化。
- `q1_convergence.pdf`：空间加密与独立温度基准误差。
- `q1_spatiotemporal_heatmaps.pdf`：按期刊矩阵热力图形式（11×11 取样方格）展示预热阶段温度场和含水率场的时间—半径分布；温度使用 `viridis`，含水率使用蓝—白—浅红—深红渐变。
- `fig_q1_3d_cylinder_model.pdf`：圆柱几何、径向坐标、真实表面状态与 Robin 环境交换的立体结构示意；对应源文件为 `fig_q1_3d_cylinder_model.drawio`。
- `fig_q1_3d_control_volume.pdf`：环形有限体积控制体、径向界面和热/水分共享通量的立体结构示意；对应源文件为 `fig_q1_3d_control_volume.drawio`。
- `render_q1_3d_figures.py`：上述两张结构示意图的可复现生成脚本（不读取或伪造数值场）。

数据图件来自 `results/q1/fields.npz` 和 `results/q1/summary.json`，生成入口为 `make q1`；立体结构图运行 `MPLCONFIGDIR=.mpl-cache UV_CACHE_DIR=.uv-cache uv run --frozen python figures/q1/render_q1_3d_figures.py` 生成。
