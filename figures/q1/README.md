# Q1 图件

- `q1_profiles.pdf`：100、600、1800 s 径向温度与含水率剖面。
- `q1_history.pdf`：中心、1 cm 和表面随时间变化。
- `q1_convergence.pdf`：空间加密与独立温度基准误差。
- `q1_spatiotemporal_heatmaps.pdf`：按期刊矩阵热力图形式（11×11 取样方格）展示预热阶段温度场和含水率场的时间—半径分布；温度使用 `viridis`，含水率使用蓝—白—浅红—深红渐变。

图件数据来自 `results/q1/fields.npz` 和 `results/q1/summary.json`，生成入口为 `make q1`。
