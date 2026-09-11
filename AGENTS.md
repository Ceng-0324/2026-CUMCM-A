# 项目约定：2026 CUMCM A

本文件只补充项目契约。全局身份与工程规则继续以用户指定的 canonical 文件为准。

## 当前入口与范围

- 已选 A 题。唯一有效的题意/模型设计入口为 [reports/ANALYSIS_MODELING_REPORT.md](reports/ANALYSIS_MODELING_REPORT.md)。
- [plan.md](plan.md) 管阶段安排，[todo.md](todo.md) 管完成状态；不要创建平行的 A 题分析总文档。
- [论文问题分析撰写稿](reports/论文问题分析.md) 是总文档派生的四问写作素材；只同步论文表述，不独立定义模型或验证结论。模型改变时先更新总文档，再同步该稿。
- `archive/selection/` 是历史材料，包含过时结论和已经不存在的 B/C 输入路径，不能用作当前运行入口。
- `code/common/model.py` 已提供共用求解器与连续中心/表面采样。Q1–Q4 正式结果与连续域事件已完成，Q4 收缩、工作簿、四组合机制和图件见 [Q4 RESULTS_REPORT](reports/q4/RESULTS_REPORT.md)；阶段降阶仍未实现。
- 论文手可提前撰写不依赖结果的问题分析，完整论文阶段仍须等待正式结果；Markdown 素材交接不代表排版引擎已确定或论文工程已建立。

## 数据与代码所有权

- `problemA/` 原始 PDF、Excel 数据和模板只读；`manifest.json` 记录其原始哈希。生成物不得写回输入目录。
- `code/common/data_io.py` 管只读 Excel 解析和输入校验，`code/common/audit.py` 管字段/时间轴审计。
- `code/common/model.py` 管统一数值核心与采样，`code/common/probes.py` 保留历史单元事件试算口径；`code/q1/problem1.py` 管 Q1 输出，`code/q1/q1_validation.py` 管独立基准，`code/q1/plot_q1.py` 从保存数据绘图，`code/common/check_project.py` 管证据核验。
- 小型可复算证据写入 `results/probes/`；Q1 正式结果位于 `results/q1/`，图件位于 `figures/`；临时实验写入被忽略的 `results/local/`。后续各问使用独立输出目录并说明与模板的映射。
- 内部单位采用 s、m、K，导出转换到题目要求的单位。Q2 不拼接 Q1；附录 3/4 的扩散率指数为 −a/C。
- 计算代码改变后必须更新结果来源及报告。不要自动重写原始文件清单来通过输入校验。

## 验证与变更

- 环境入口 `make setup`，常规检查 `make check`，更新原型 `make probe`，生成 Q1 `make q1`，最终复验 `make verify`（包含 Q1 临时重算）。
- 使用 `uv.lock` 和项目 `.uv-cache/`，避免依赖个人 `/tmp` 环境路径或未声明全局包。
- 改模型需补充相应的物理/数值证据；当前历史回归用于保护工程迁移，模型有意变化时应显式修订其契约。
- 历史 probes 仍记录最大单元事件，不能声称 Q3/Q4 连续域已达标；有效热物性密度与守恒干骨架密度必须区分。Q1 采样已重构中心与真实表面，不能把旧 probe 的 center_T_C 当作同一接口。
- 每次任务保留现有用户修改；不创建无依据完成状态，不以提交或清理为由删除数据。推送由用户另行授权。
