# Q4 报告

- [METHOD_OVERVIEW.md](METHOD_OVERVIEW.md)：Q4 建模、坐标变换、守恒和机制分析方法速览。
- [RESULTS_REPORT.md](RESULTS_REPORT.md)：收缩条件下附录 4 正式结果、表 6、数值验证和四组合机制分解。
- [半径插值对照](../../results/q4/interpolation_sensitivity.json)：256、512 单元下比较分段线性与 PCHIP，文件记录该独立试验的输入和代码来源。

Q4 采用材料坐标固定计算域，输出时映射回实际半径；当前结果仍受均匀径向收缩、干骨架无损失、有效表面平衡浓度和环境延拓假设约束。

对应代码、结果和图件分别位于 [`code/q4/`](../../code/q4/)、[`results/q4/`](../../results/q4/) 和 [`figures/q4/`](../../figures/q4/)。
