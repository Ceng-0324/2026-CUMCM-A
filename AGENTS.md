# 项目约定：2026 CUMCM A

本文件只补充项目契约。全局身份与工程规则继续以用户指定的 canonical 文件为准。

## 当前入口与范围

- 已选 A 题。唯一有效的题意/模型设计入口为 [reports/ANALYSIS_MODELING_REPORT.md](reports/ANALYSIS_MODELING_REPORT.md)。
- [plan.md](plan.md) 管阶段安排，[todo.md](todo.md) 管完成状态；不要创建平行的 A 题分析总文档。
- `archive/selection/` 是历史材料，包含过时结论和已经不存在的 B/C 输入路径，不能用作当前运行入口。
- 当前 `code/model.py` 是可行性原型。阶段识别、降阶、连续中心/表面重构、正式输出和论文未完成；工程测试通过不得改写为正式数值验收。

## 数据与代码所有权

- `problemA/` 原始 PDF、Excel 数据和模板只读；`manifest.json` 记录其原始哈希。生成物不得写回输入目录。
- `code/data_io.py` 管只读 Excel 解析和输入校验，`code/audit.py` 管字段/时间轴审计。
- `code/model.py` 管数学原型，`code/probes.py` 管实验组合和结果来源记录，`code/check_project.py` 管工程/证据核验。
- 小型可复算证据写入 `results/probes/`；临时实验写入被忽略的 `results/local/`。正式输出阶段另建输出目录并说明与模板的映射。
- 内部单位采用 s、m、K，导出转换到题目要求的单位。Q2 不拼接 Q1；附录 3/4 的扩散率指数为 −a/C。
- 计算代码改变后必须更新结果来源及报告。不要自动重写原始文件清单来通过输入校验。

## 验证与变更

- 环境入口 `make setup`，常规检查 `make check`，更新试算 `make probe`，最终复验 `make verify`。
- 使用 `uv.lock` 和项目 `.uv-cache/`，避免依赖个人 `/tmp` 环境路径或未声明全局包。
- 改模型需补充相应的物理/数值证据；当前历史回归用于保护工程迁移，模型有意变化时应显式修订其契约。
- 记录的是最大单元阈值事件，不能声称连续域已全部低于阈值；有效热物性密度和守恒干骨架密度必须区分。
- 每次任务保留现有用户修改；不创建无依据完成状态，不以提交或清理为由删除数据。推送由用户另行授权。
