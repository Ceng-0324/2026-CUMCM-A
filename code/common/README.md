# 公共代码

- `data_io.py`：只读 Excel 解析、输入哈希和结构化读取。
- `audit.py`：原始附件审计。
- `model.py`：统一径向热质求解器、Kirchhoff 通量和连续场采样接口。
- `plotting.py`：统一中文字体、可写缓存目录和 PDF 图件配置。
- `probes.py`：历史可行性与机制试算，保留原型事件口径。
- `check_project.py`：文档链接、来源哈希、历史回归和 Q1 产物核验。

从项目根目录使用 `make check`、`make probe`、`make verify`，不要直接把公共模块复制到问题目录。
- `model_validation_sensitivity.py`：Q3/Q4 物理参数敏感性和 BDF/Radau 独立积分器复核（输出到 `results/local/`）。

## 从方程定位代码

`model.py` 内部统一使用 s、m、K，含水率为 kg 水/kg 干物质。状态向量依次存放温度、含水率和累计归一化失水量；物性中的有效密度不作为干骨架密度使用。

| 数学步骤 | 对应函数 | 阅读要点 |
|---|---|---|
| 环形控制体积分 | `radial_geometry`、`divergence` | 坐标为 ξ=r/R，权重为 ∫ξ dξ；`divergence` 返回向外通量散度的负值。 |
| 附录 2–4 物性 | `material_parameters` | 返回 ρ、cp、k、D0(T)、a，完整扩散率为 D0(T)exp(−a/C)。 |
| 非线性水分通量 | `kirchhoff`、`RadialModel.fluxes` | 对浓度因子积分；温度因子保留在界面系数中，导热采用调和平均。 |
| 表面传质边界 | `surface_moisture` | 联立最外半单元扩散与 Robin 条件求真实表面含水率，允许通量变号。 |
| 半离散方程与时间推进 | `RadialModel.rhs`、`solve_radial` | 温度与水分共用状态向量；支持 BDF/Radau，在输入折点分段积分。Q1 常物性时两个场无反馈耦合。 |
| 中心、表面与连续重构 | `reconstruct_profile`、`inverse_kirchhoff`、`RadialSolution.sample` | 中心偶二次外推，内部 PCHIP 斜率，端点施加通量梯度；水分在积分势空间重构后反解。 |
| 材料坐标与实际半径映射 | `RadialModel.radius`、`RadialSolution.sample` | Q4 在固定材料坐标网格求解，用当时 R(t) 转回实际半径；域外输出留空。 |

Q3 的 `continuous_max` 对连续重构场加密采样，Q4 同名函数比较各段三次多项式的节点和驻点；两者实现不同，不能把 Q3 的采样检查说成逐段解析极值检验。事件扫描、Brent 求根及严格达标的后继输出由各问 `problem3.py`、`problem4.py` 负责。
