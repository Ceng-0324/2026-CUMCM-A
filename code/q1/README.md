# Q1 代码

- `problem1.py`：生成 `results/q1/`、`reports/q1/RESULTS_REPORT.md` 和 `figures/q1/`。
- `q1_validation.py`：独立圆柱 Robin 热方程基准及 Q1 诊断。
- `plot_q1.py`：从保存数据生成四张论文图件，其中时空热力图按 11×11 取样矩阵格式输出。
- `q1_physics_audit.py`：湿空气浓度、潜热和 Lewis 传质情景复核；不替换正式基线。

正式入口为项目根目录的 `make q1`。

阅读独立热基准时，先看 `heat_modes` 中的 Robin 特征根、衰减率和径向/轴向模态，再看 `heat_reference` 如何对烘房分段线性温度解析推进。`diagnose` 独立积分表面热流与水分通量，并与状态变化核对收支；它不把求解器自己的累计失水量当作唯一验证。
