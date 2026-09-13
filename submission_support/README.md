# 2026 CUMCM A 题支撑材料

运行时请将 `problemA/` 放在本目录同级，或设置 `PROBLEM_A_DIR` 指向原始附件目录。

- `code/`：Q1–Q4 求解、独立验证、敏感性分析和公共数值核心代码。
- `results/q1`–`results/q4/`：正式工作簿、CSV、未舍入场数据、结果摘要和验证 JSON。
- `figures/q1`–`figures/q4/`：由正式求解程序生成的数据图 PDF。
- `pyproject.toml`、`uv.lock`：Python 版本和锁定依赖。
- `run.py`：跨平台复现入口；复现输出写入 `reproduced/`，不会覆盖正式结果。

## 运行

```bash
uv sync --frozen
python run.py audit --input-dir /path/to/problemA
python run.py q1          # 长时重算按需执行 q2、q3、q4
```

支撑包没有重复放入赛题附件。运行时请用 `--input-dir` 指向原始 `problemA/`；程序会先检查附件是否完整、版本是否一致，再将附件复制到自己的工作目录，原始文件不会被改动。Q1–Q4 的正式结果已经随包提供；需要重新计算时，新结果会写入 `reproduced/`，并自动与随包结果进行对照。
