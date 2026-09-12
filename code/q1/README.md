# Q1 代码

- `problem1.py`：生成 `results/q1/`、`reports/q1/RESULTS_REPORT.md` 和 `figures/q1/`。
- `q1_validation.py`：独立圆柱 Robin 热方程基准及 Q1 诊断。
- `plot_q1.py`：从保存数据生成四张论文图件，其中时空热力图按 11×11 取样矩阵格式输出。
- `q1_physics_audit.py`：湿空气浓度、潜热和 Lewis 传质情景复核；不替换正式基线。

正式入口为项目根目录的 `make q1`。
