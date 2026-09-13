# 2026 CUMCM A · 药材的烘干问题

Q1–Q4 的正式结果工作簿、数值验证、数据图和方法正文稿已完成，论文工程与全文尚未完成。结果适用范围以各问报告中的模型假设和验证边界为准。

[模型总文档](reports/ANALYSIS_MODELING_REPORT.md) 统一题意、假设与模型口径；[plan.md](plan.md) 管阶段安排，[todo.md](todo.md) 管完成状态。

## Quick Start：论文手先看什么

先用 [四问解法异同概览](reports/methods_comparison.md) 了解整体关系，再按以下顺序进入任一子问题（`X` 对应题号）：

1. **方法概览** `reports/qX/METHOD_OVERVIEW.md`：了解建模对象、算法及其用途。
2. **正文稿** `reports/qX/problemX_algorithm_analysis.md`：获取公式、推导、算法说明和图表插入位置。
3. **结果报告** `reports/qX/RESULTS_REPORT.md`：核对正式数值、验证证据和适用边界。
4. **表格与图件**：从 `results/qX/` 取 CSV/Excel，从 `figures/qX/` 取 PDF；文件用途见各目录 README。
5. **实现追溯**：需要复算或查算法细节时，再读 `code/qX/README.md`。

### 四问入口地图

| 问题 | 方法概览 | 正文稿 | 正式结果 |
|---|---|---|---|
| Q1 预热阶段 | [方法](reports/q1/METHOD_OVERVIEW.md) | [正文](reports/q1/problem1_algorithm_analysis.md) | [结果报告](reports/q1/RESULTS_REPORT.md) |
| Q2 变物性耦合 | [方法](reports/q2/METHOD_OVERVIEW.md) | [正文](reports/q2/problem2_algorithm_analysis.md) | [结果报告](reports/q2/RESULTS_REPORT.md) |
| Q3 连续域达标事件 | [方法](reports/q3/METHOD_OVERVIEW.md) | [正文](reports/q3/problem3_algorithm_analysis.md) | [结果报告](reports/q3/RESULTS_REPORT.md) |
| Q4 收缩与机制分解 | [方法](reports/q4/METHOD_OVERVIEW.md) | [正文](reports/q4/problem4_algorithm_analysis.md) | [结果报告](reports/q4/RESULTS_REPORT.md) |

### 跨问题写作材料

- 总体分析：[论文问题分析撰写稿](reports/论文问题分析.md)；表述与论证建议：[正文独特性提升](reports/uniqueness_enhancement.md)。
- 模型检验：[四问模型检验方法汇总](reports/model_validation_methods.md)，集中整理收敛、守恒、边界残差、连续事件、敏感性和独立基准检验。
- 模型假设：[模型假设与合理性说明](reports/model_assumptions.md)，逐条说明假设、理由、适用边界和可检验依据。
- 数据组稿：[论文数据包](reports/PAPER_DATA_PACKAGE.md)；技术路线、递进关系和方法图的插入建议：[图示报告](reports/DRAWIO_REPORT.md)。
- 参考文献：[四问引用文献指南](reports/references_by_question.md)，按问题查找中文优先文献、引用位置及期刊索引依据。
- 论文工程：[LaTeX 组稿入口](paper/README.md)，正文、图件插入和参考文献初稿集中在 `paper/`。
- 模型评价：[模型评价与推广](reports/model_evaluation.md)，按国赛优秀论文要求汇总优点、数值可靠性、敏感性、局限与推广。

## 目录

`code/`、`reports/`、`results/`、`figures/` 均按 `q1/`–`q4/` 分目录，具体文件用途见对应 README。

| 目录与索引 | 内容 |
|---|---|
| [`problemA/`](problemA/) | 原始 PDF、附件、结果模板与哈希清单，只读 |
| [代码索引](code/README.md) | 公共求解器 `common/` 与各问专属脚本 |
| [报告索引](reports/README.md) | 模型总文档、写作素材与各问报告 |
| [结果索引](results/README.md) | 正式数据；`probes/` 为历史试算，`local/` 为忽略 Git 的临时实验 |
| [图件索引](figures/README.md) | 数据图 PDF、方法图 PDF 与可编辑 `.drawio` 源文件 |
| [`tests/`](tests/) | 输入保护、数值与输出契约测试 |
| [历史归档](archive/selection/README.md) | 选题材料与旧代码，不作为当前事实源 |

## 环境与运行

复现基线为 Python 3.14、uv 0.11.13 和 Make。支持范围及依赖分别见 [pyproject.toml](pyproject.toml) 和 [uv.lock](uv.lock)；本地缓存位于 `.uv-cache/` 与 `.mpl-cache/`。

在仓库根目录运行：

```sh
make setup      # 安装锁定依赖
make check      # 输入校验、单元测试、链接/来源/历史数值回归
make probe      # 重算历史原型与机制试算，更新 results/probes
make q1         # 生成 Q1 工作簿、完整精度数据、验证报告和图件
make q2         # 生成 Q2 前 3 h 工作簿、验证报告和图件
make q3         # 生成 Q3 连续域事件工作簿、验证报告和图件
make q4         # 生成 Q4 收缩条件工作簿、验证报告和图件
make verify     # 执行 check，并在临时目录重算核对已有证据
```

首次安装需要网络；重绘数据图需要可用中文字体，无字体时可直接运行对应脚本并加 `--no-figures`。题面提取命令 `make extract` 另需 Poppler 的 `pdftotext`。更多参数见各问代码 README 和脚本 `--help`。

`make verify` 检查输入、测试、结果来源和历史回归，并临时重算 Q1；Q2–Q4 的正式数值验收见各问结果报告。数值验证不代替模型假设的实验验证。

## Git 约定

- 原始输入与模板保持只读；正式结果写入 `results/qX/`，临时实验写入 `results/local/`。
- 修改计算代码后，更新受影响的结果、报告与来源记录；依赖与忽略规则见锁文件和 `.gitignore`。
- 提交前运行 `make verify` 与 `git diff --check`。GitHub Actions 已配置相同检查，远程执行结果以实际运行记录为准。
- 推送由用户另行授权；完整工程约定见 [AGENTS.md](AGENTS.md)。
