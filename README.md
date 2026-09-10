# 2026 CUMCM A · 药材的烘干问题

本项目已确定研究 A 题，资料整理与 Git 工程已完成，当前进入正式模型闭合、四问求解准备和论文问题分析交接。

从 [A题思路分析总文档](reports/ANALYSIS_MODELING_REPORT.md) 开始阅读。它统一了题意、数据口径、四问模型、创新设计与试算证据；[计划](plan.md) 记录阶段安排，[待办](todo.md) 记录完成状态。

论文手可直接使用 [论文问题分析撰写稿](reports/论文问题分析.md) 的四个分析小节。该稿按“问题本质—主要难点—处理思路—检验重点”组织，是总文档的写作表达；正式数值结论仍需等待结果验收。计划已细化为 A 题执行流程，现有模型主线和原型继续复用。

## 目录

```text
problemA/              原始 PDF、数据附件、结果模板与 SHA-256 清单
reports/               模型总文档、论文问题分析稿；后续添加结果与验收报告
code/                  A 题输入审计、数学原型、试算入口和工程检查
tests/                 输入保护、积分通量、守恒与解析收敛测试
results/probes/        可复算的小型试算证据，纳入 Git
results/local/         临时提取/探索输出，忽略 Git
archive/selection/     五份历史报告、历史代码和选题证据
.github/workflows/     提交与 PR 的自动检查配置
pyproject.toml         Python 范围、计算依赖
uv.lock                锁定依赖与下载来源
Makefile               环境、检查、试算统一入口
```

当前不创建空论文或图表目录；进入对应阶段再建立 `figures/`、`paper/`。正式结果文件应输出至 `results/` 的专用子目录，禁止覆盖 `problemA/附件/附件3/` 内模板。

## 环境与运行

需要 Python 3.14 和 uv 0.11.13（CI 同版），Make 可用。依赖声明支持 Python 3.12–3.14，当前复现基线为 3.14；`uv.lock` 锁定 NumPy 2.4.4、SciPy 1.17.1。依赖缓存默认放入项目 `.uv-cache/`，不依赖机器上的全局环境。

在仓库根目录运行：

```sh
make setup      # 安装锁定依赖
make check      # 输入校验、单元测试、链接/来源/历史数值回归
make probe      # 重算 10 组可行性和 4 组机制试算，更新 results/probes
make verify     # 执行 check，并在临时目录重算核对已有证据
```

第一次读取/安装依赖需要网络。可用 `make help` 查看命令；`make extract` 另外需要 Poppler 的 `pdftotext`，只将题面文本写到本地忽略目录。纯输入审计无第三方依赖，可直接运行 `python3 code/audit.py`。

试验自定义网格时输出到本地目录，避免覆盖统一证据：

```sh
UV_CACHE_DIR=.uv-cache uv run --frozen python code/probes.py \
  --mode feasibility --grids 16 32 64 --output-dir results/local/coarse
```

`make verify` 校验 7 份原始文件哈希、输入结构、积分通量、离散质量平衡、解析二阶收敛、当前数值与归档原型的一致性。跨平台数值采用明确的小容差比对，不要求运行时间或求解器调用次数逐位相同。该命令验证工程与原型复现，**不代替正式物理模型和连续域精度验收**。

## Git 约定

- 保留 `main` 分支及已有远程配置；本地提交后由用户决定何时推送。
- 原始 PDF/XLSX、有效报告、代码、锁文件和精选 JSON 证据纳入版本控制；系统文件、虚拟环境、缓存、临时输出和凭据忽略。
- 小而完整地提交数据契约、实现、验证及对应文档。修改计算代码后先审查数值影响，再运行 `make probe` 更新来源和结果。
- [历史归档](archive/selection/README.md) 保持内容，旧结论不作为现行契约。原型模型有意改变时，应同步更新报告和回归检查，不能通过放宽容差掩盖差异。
- 提交前运行 `make verify` 与 `git diff --check`。GitHub Actions 已配置相同检查，远程执行结果以实际运行记录为准。

当前未交付正式 result1–4 工作簿、阶段降阶求解器和论文全文；已有四问问题分析素材。方法与验证要求见 [总文档](reports/ANALYSIS_MODELING_REPORT.md)，执行依赖与交付顺序见 [计划](plan.md)。
