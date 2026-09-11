# 计算结果

- `probes/feasibility.json`：32/64/128 网格、紧容差与环境延拓共 10 次原型试算，另含解析基准。
- `probes/mechanism.json`：几何与整组物性四组合试算及作用分解。
- [q1/result1.xlsx](q1/result1.xlsx)：Q1 正式格式输出，两张工作表均为 1–1800 s、21 个半径位置，四位小数。
- `q1/fields.npz`：未舍入的逐秒场、初值、论文表格与剖面/独立温度基准数据；`q1/summary.json` 保存参数、误差、验收及来源。
- [q1/table1.csv](q1/table1.csv)、[q1/table2.csv](q1/table2.csv)：Q1 论文表格；`q1/artifact_manifest.json` 记录结果及三张 PDF 的哈希。
- [q2/result2.xlsx](q2/result2.xlsx)：Q2 前 3 h 逐秒、21 个半径位置的正式输出。`q2/fields.npz`、`q2/summary.json`、`q2/table3.csv`、`q2/table4.csv` 保存未舍入场、验证和论文表格。
- [q3/result3.xlsx](q3/result3.xlsx)：Q3 固定半径条件下每 60 s、每 0.1 cm 的含水率输出，延伸至连续域达标事件；`q3/summary.json`、`q3/table5.csv` 保存事件定位、验证和论文表格。
- [q4/result4.xlsx](q4/result4.xlsx)：Q4 收缩半径条件下每 60 s、每 0.1 cm 的实际半径含水率与真实表面列；`q4/summary.json`、`q4/table6.csv` 保存事件定位、四组合机制和验证记录。
- [q4/result4.xlsx](q4/result4.xlsx)：Q4 收缩半径条件下每 60 s、每 0.1 cm 的实际半径含水率与真实表面列；`q4/summary.json`、`q4/table6.csv` 保存事件定位、四组合机制和验证记录。
- `local/`：临时实验、题面文本提取等本机产物，Git 忽略。

运行 `make probe` 更新原型证据，`make q1` 生成 Q1 结果、报告及图件；运行 `make verify` 在临时目录重算原型及 Q1 并比较，不覆盖这些文件。JSON 包含输入/计算代码哈希、环境版本和假设。运行耗时只打印到终端，避免每次复算造成无意义版本差异。

`probes/` 仍是可行性原型，不能替代正式结果。Q1–Q3 已完成条件径向模型下的数值验证，Q4 已完成收缩半径条件下的连续域事件、工作簿和机制对照。输入目录中的同名文件是原始模板。模型口径与待办见 [总文档](../reports/ANALYSIS_MODELING_REPORT.md)。
