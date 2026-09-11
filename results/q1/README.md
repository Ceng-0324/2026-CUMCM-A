# Q1 结果索引

- [`result1.xlsx`](result1.xlsx)：按模板扩展的两张工作表。
- `fields.npz`：未舍入逐秒场及论文/绘图数据。
- `summary.json`：参数、误差、诊断和来源哈希。
- `table1.csv`、`table2.csv`：论文表格数据。
- `artifact_manifest.json`：正式结果与图件哈希。
- [`physics/`](physics/)：湿空气、潜热和传质边界的物理复核情景，不替代正式基线。

运行 `make q1` 重新生成正式结果；原始模板位于 `problemA/附件/附件3/`，不会被覆盖。
