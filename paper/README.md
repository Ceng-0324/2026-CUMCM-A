# 论文工程

本目录是 CUMCM A 题中文 LaTeX 组稿工程，使用 XeLaTeX 编译。

## 入口

- `main.tex`：论文主入口，按“问题重述—问题分析—假设—符号—四问—敏感性—评价—参考文献—附录”组织。
- `sections/`：各章节正文；四问内容来自 `reports/q1/` 至 `reports/q4/` 的方法稿和结果报告。
- `references.tex`：已核验的参考文献初稿，正式编号需随正文引用顺序调整。

## 组稿规则

正式数值只从各问 `RESULTS_REPORT.md` 和 `results/qX/` 读取；图件从 `figures/` 读取。表 1--6 当前在正文中标注了插入位置，排版时应从对应 CSV/工作簿生成三线表并复核单位与小数位。

当前版本是可继续编辑的第一版正文组稿，不代表最终论文已完成。摘要、参考文献编号、表格排版、全文交叉引用和编译验收仍需继续处理。


编译命令：

```bash
xelatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main.tex
```
