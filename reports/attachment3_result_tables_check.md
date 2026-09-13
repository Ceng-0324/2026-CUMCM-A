# 附件 3 `result1`–`result4` 核对

核对日期：2026-09-13。核对对象分为赛题原始模板和项目生成的正式结果，原始模板未被修改。

| 文件 | 原始附件尺寸/非空单元格 | 正式结果文件 | 正式结果尺寸/非空单元格 | 结论 |
|---|---:|---|---:|---|
| `problemA/附件/附件3/result1.xlsx` | `A1:F5`；20 | `results/q1/result1.xlsx` | `A1:V1801`；79,244 | 已按 Q1 结果生成，模板本身未填充 |
| `problemA/附件/附件3/result2.xlsx` | `A1:F5`；20 | `results/q2/result2.xlsx` | `A1:V10801`；475,244 | 已按 Q2 结果生成，模板本身未填充 |
| `problemA/附件/附件3/result3.xlsx` | `A1:F5`；10 | `results/q3/result3.xlsx` | `A1:V3450`；75,900 | 已按 Q3 结果生成，模板本身未填充 |
| `problemA/附件/附件3/result4.xlsx` | `A1:F5`；10 | `results/q4/result4.xlsx` | `A1:W3068`；47,391 | 已按 Q4 结果生成，模板本身未填充 |

## 判断

附件 3 的四个 `result*.xlsx` 是题目提供的结果模板，当前仍只有表头和少量示例/占位单元格，并没有被回写。项目遵守“原始附件只读”约定，将正式计算结果分别写入 `results/q1/result1.xlsx` 至 `results/q4/result4.xlsx`。四份正式工作簿由各问程序生成，并已在对应结果报告和输出契约中完成回读核验；提交时应使用 `results/q*/result*.xlsx`，不要替换或修改 `problemA/附件/附件3/` 中的原始模板。
