# 公共代码

- `data_io.py`：只读 Excel 解析、输入哈希和结构化读取。
- `audit.py`：原始附件审计。
- `model.py`：统一径向热质求解器、Kirchhoff 通量和连续场采样接口。
- `plotting.py`：统一中文字体、可写缓存目录和 PDF 图件配置。
- `probes.py`：历史可行性与机制试算，保留原型事件口径。
- `check_project.py`：文档链接、来源哈希、历史回归和 Q1 产物核验。

从项目根目录使用 `make check`、`make probe`、`make verify`，不要直接把公共模块复制到问题目录。
- `model_validation_sensitivity.py`：Q3/Q4 物理参数敏感性和 BDF/Radau 独立积分器复核（输出到 `results/local/`）。
