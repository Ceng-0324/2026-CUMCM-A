# 2026 CUMCM A · 药材的烘干问题

本项目研究 A 题。Q1、Q2、Q3、Q4 均已完成正式结果工作簿、数值验证和数据图；Q4 采用材料坐标、收缩半径与附录 4 整组物性。所有结果均限于各报告明确的径向传递、有效边界和收缩假设。

从 [A题思路分析总文档](reports/ANALYSIS_MODELING_REPORT.md) 开始阅读。它统一了题意、数据口径、四问模型、创新设计与试算证据；[计划](plan.md) 记录阶段安排，[待办](todo.md) 记录完成状态。

四个问题的文件按“代码、报告、结果、图件”分目录保存；每个问题的 `reports/qX/METHOD_OVERVIEW.md` 是论文手的第一入口，先告诉你本问实际用了哪些建模方法和算法，再进入算法分析稿和结果报告。结果、图件和数据按问题目录分别索引。

论文手可直接使用 [论文问题分析撰写稿](reports/论文问题分析.md)。该稿采用“总体主线—四问分析—总体求解路线”的结构，每问突出本质、难点与对策；Q1–Q4 方法与结果均可据各自验收报告入稿。计划已细化为 A 题执行流程。

## Quick Start：论文手先看什么

不需要先通读整个仓库。按下面的顺序即可快速进入任一子问题：

1. **先看方法概览**：打开 `reports/qX/METHOD_OVERVIEW.md`，确认本问的建模对象、核心算法、输出和验证状态。
2. **再看正文稿**：打开 `reports/qX/problemX_algorithm_analysis.md`（Q4 正文稿可在结果报告基础上补写），获取可直接改写进论文的公式、算法流程和段落。
3. **核对结果**：打开 `reports/qX/RESULTS_REPORT.md`，确认正式数值、结果边界和验证结论。
4. **取表格和图件**：表格从 `results/qX/` 的 CSV 获取，图件从 `figures/qX/` 的 PDF 获取；对应目录 README 会说明每个文件的用途。
5. **需要追溯实现时**：最后再看 `code/qX/README.md` 和代码入口，不要把脚本路径、哈希或工作簿回读过程直接写进论文正文。

### 四问入口地图

| 问题 | 先读什么 | 再读什么 | 正式结果 | 当前状态 |
|---|---|---|---|---|
| Q1 预热阶段 | [Q1 方法概览](reports/q1/METHOD_OVERVIEW.md) | [Q1 正文稿](reports/q1/problem1_algorithm_analysis.md) | [Q1 结果报告](reports/q1/RESULTS_REPORT.md) | 条件模型已验证 |
| Q2 变物性耦合 | [Q2 方法概览](reports/q2/METHOD_OVERVIEW.md) | [Q2 正文稿](reports/q2/problem2_algorithm_analysis.md) | [Q2 结果报告](reports/q2/RESULTS_REPORT.md) | 前 3 h 正式结果已验证 |
| Q3 连续域达标事件 | [Q3 方法概览](reports/q3/METHOD_OVERVIEW.md) | [Q3 正文稿](reports/q3/problem3_algorithm_analysis.md) | [Q3 结果报告](reports/q3/RESULTS_REPORT.md) | 固定半径正式结果已验证 |
| Q4 收缩与机制分解 | [Q4 方法概览](reports/q4/METHOD_OVERVIEW.md) | [Q4 正文算法稿](reports/q4/problem4_algorithm_analysis.md) | [Q4 结果报告](reports/q4/RESULTS_REPORT.md) | 正式结果、四组合机制与验证已完成 |

### 文件用途怎么区分

| 文件类型 | 论文手用法 | 不要混淆的内容 |
|---|---|---|
| `METHOD_OVERVIEW.md` | 快速知道“用了什么方法、解决什么难点、是否已验证” | 不是完整推导，也不是最终结果表 |
| `problemX_algorithm_analysis.md` | 获取正文段落、公式、算法步骤和图表插入说明 | 不新增总模型之外的事实 |
| `RESULTS_REPORT.md` | 获取正式数值、验证指标和适用边界 | 不把原型试算当正式结果 |
| `results/qX/` | 读取 CSV、Excel、NPZ、JSON 等可追溯数据 | 不直接从 PDF 图片反抄数值 |
| `figures/qX/` | 选取论文中的数据驱动 PDF 图件 | 不放流程图或概念图；非数据图由 `4drawio` 阶段管理 |
| `code/qX/` | 需要复算、检查参数或理解实现时查阅 | 脚本名和内部实现细节不直接写进正文 |

### 按论文写作任务进入

- 写**总体问题分析**：先读 [A题思路分析总文档](reports/ANALYSIS_MODELING_REPORT.md) 和 [论文问题分析撰写稿](reports/论文问题分析.md)。
- 写**某一问的方法与求解**：按上表先读该问 `METHOD_OVERVIEW.md`，再读对应正文稿。
- 写**某一问的结果分析**：在对应 `RESULTS_REPORT.md` 中找正式数值，再按正文稿的“表格与图件插入说明”放置 CSV/PDF。
- 写**模型评价与限制**：同时核对该问结果报告的验证边界和总文档的假设敏感性预检。
- 写**Q4**：使用方法概览、结果报告、表 6 工作簿和图件补写正文结果段落。

## 目录

```text
problemA/              原始 PDF、数据附件、结果模板与 SHA-256 清单（只读）
code/
├── common/            输入审计、统一求解器、采样、试算与工程检查
├── q1/                Q1 正式结果、验证和绘图脚本
├── q2/                Q2 变物性全场脚本
├── q3/                Q3 连续域事件脚本
└── q4/                Q4 收缩与机制脚本
figures/
├── q1/                Q1 中文矢量数据图
├── q2/                Q2 图件
├── q3/                Q3 图件
└── q4/                Q4 图件
reports/
├── ANALYSIS_MODELING_REPORT.md  A 题模型与假设事实源
├── 论文问题分析.md             论文问题分析素材
└── q1/…q4/                     各问题结果报告
results/
├── probes/            可复算的小型试算证据，纳入 Git
├── q1/…q4/            各问题正式结果独立目录
└── local/             临时提取/探索输出，忽略 Git
tests/                 输入保护、采样/输出契约、通量守恒与解析收敛测试
archive/selection/     历史报告、历史代码和选题证据
.github/workflows/     提交与 PR 的自动检查配置
pyproject.toml         Python 范围、计算依赖
uv.lock                锁定依赖与下载来源
Makefile               环境、检查、试算统一入口
```

各层 README 是对应目录的索引：[`code/README.md`](code/README.md)、[`figures/README.md`](figures/README.md)、[`reports/README.md`](reports/README.md)、[`results/README.md`](results/README.md)。每个 Q1–Q4 子目录继续提供本问题的入口、状态和产物约定。

正式结果输出至 `results/` 的专用子目录；Q1 为 [result1.xlsx](results/q1/result1.xlsx)。禁止覆盖 `problemA/附件/附件3/` 内模板。论文工程尚未创建。

## 环境与运行

需要 Python 3.14 和 uv 0.11.13（CI 同版），Make 可用。依赖声明支持 Python 3.12–3.14，当前复现基线为 3.14；锁定 NumPy 2.4.4、SciPy 1.17.1、Matplotlib 3.10.8、XlsxWriter 3.2.9。依赖缓存位于 `.uv-cache/`，字体缓存位于 `.mpl-cache/`，不依赖个人临时环境。

在仓库根目录运行：

```sh
make setup      # 安装锁定依赖
make check      # 输入校验、单元测试、链接/来源/历史数值回归
make probe      # 重算 10 组可行性和 4 组机制试算，更新 results/probes
make q1         # 生成 Q1 工作簿、完整精度数据、验证报告和图件
make q2         # 生成 Q2 前 3 h 工作簿、验证报告和图件
make q3         # 生成 Q3 连续域事件工作簿、验证报告和图件
make verify     # 执行 check，并在临时目录重算核对已有证据
```

第一次安装依赖需要网络。中文图件使用本机微软雅黑、黑体、STHeiti、Noto Sans CJK SC 等字体，优先嵌入 TrueType 字体，其余容器采用矢量字形；无字体环境可加 `--no-figures` 重算数值，CI 的 `make verify` 不重绘图。`make extract` 需要 Poppler 的 `pdftotext`。纯输入审计可直接运行 `python3 code/common/audit.py`。

试验自定义网格时输出到本地目录，避免覆盖统一证据：

```sh
UV_CACHE_DIR=.uv-cache uv run --frozen python code/common/probes.py \
  --mode feasibility --grids 16 32 64 --output-dir results/local/coarse
```

`make verify` 校验 7 份原始文件哈希、输入结构、积分通量、离散质量平衡、解析二阶收敛、当前数值与归档原型的一致性，并临时重算 Q1。跨平台数值采用明确的小容差比对，不要求运行时间或求解器调用次数逐位相同。该命令验证工程复现及 Q1 条件模型的数值结果，**不代替实验验证或 Q3/Q4 连续域事件验收**。

Q1 还核验全部 75600 个工作簿数值及四位小数显示、中心/表面条件、时空加密、实际烘房输入的独立温度解析基准。公共接口示例（在 code 目录可导入 model）：

```python
from model import solve_radial
solution = solve_radial(128, appendix=2, duration_s=1800)
field = solution.sample([100, 1800], [0, 0.01, 0.02])
# field.temperature_K、field.moisture 形状均为 (2, 3)。
# 此示例网格仅演示接口；正式 Q1 由 make q1 执行完整加密与校验。
```

任意时空采样使用 s、m、K；`coordinate="material"` 接收 ξ，`outside="nan"` 显式标记超出当前半径的位置，默认越界报错。Q1 之外的长期事件精度尚待验证。

## Git 约定

- 保留 `main` 分支及已有远程配置；本地提交后由用户决定何时推送。
- 原始 PDF/XLSX、有效报告、代码、锁文件和精选 JSON 证据纳入版本控制；系统文件、虚拟环境、缓存、临时输出和凭据忽略。
- 小而完整地提交数据契约、实现、验证及对应文档。修改计算代码后先审查数值影响，再运行对应的 `make probe` / `make q1` 更新来源和结果。
- [历史归档](archive/selection/README.md) 保持内容，旧结论不作为现行契约。原型模型有意改变时，应同步更新报告和回归检查，不能通过放宽容差掩盖差异。
- 提交前运行 `make verify` 与 `git diff --check`。GitHub Actions 已配置相同检查，远程执行结果以实际运行记录为准。

当前已交付条件模型下的 Q1、Q2、固定半径 Q3 和收缩半径 Q4，并完成表面浓度基准、潜热情景复核及 Q4 四组合机制分析；复核没有足够题面数据支持替换基线。阶段降阶和论文全文尚未完成。方法与验证要求见 [总文档](reports/ANALYSIS_MODELING_REPORT.md)，执行顺序见 [计划](plan.md)。
