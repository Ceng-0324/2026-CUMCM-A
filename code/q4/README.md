# Q4 代码

Q4 使用附件 2 的收缩轨迹和附录 4 的整组物性。材料坐标求解、干基水量收支和真实表面采样由 [`common/model.py`](../common/model.py) 提供；本目录的 `problem4.py` 负责重构场极值、阈值定位、实际半径输出及四组合机制对照。

运行 `make q4` 更新正式结果与图件。已有的 `validation_sensitivity.json` 由独立检验脚本生成，重跑正式入口时保留其引用和来源记录。

补充对照由 `q4_sensitivity.py` 检查环境延拓和四组合收敛，`q4_interpolation_sensitivity.py` 检查半径的线性/PCHIP 插值。后者暂时替换半径方法，完成积分及事件定位后恢复，发生异常时也恢复；该脚本按顺序运行，不支持同一进程内并发替换。输出同时记录输入与代码哈希。

输出写入 [`results/q4/`](../../results/q4/)，报告和图件分别写入 [`reports/q4/`](../../reports/q4/) 与 [`figures/q4/`](../../figures/q4/)。
