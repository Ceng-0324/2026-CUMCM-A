# Q1–Q4 引用文献指南

本指南为论文手提供与当前四问解法对应的文献、引用网址和正文使用位置。模型与实现口径以 [模型总文档](ANALYSIS_MODELING_REPORT.md) 及 [四问解法异同概览](methods_comparison.md) 为准。

检索与核验日期：2026-09-12。按近十年要求，本轮收录范围取 **2017 年至核验日**，共整理 **17 篇期刊论文，中文 4 篇、英文 13 篇**，分为 **10 篇优先引用、7 篇方法补充**；另有 2 篇仅核实书目的候选，见第 8 节。中文文献覆盖药材干燥背景、连续介质热质模型、收缩域计算与收缩规律；具体数值方法同时保留贴合的英文来源。

本文是针对当前解法的精选清单。期刊声誉是选文依据之一，最终引用仍须对应文章实际讨论的方法；索引数据库负责收录检索，不是论文的出版机构。

## 1. 论文手快速选用

下表的“论文网址”可直接打开原始来源；R01–R17 是本文检索编号，按问题归类而非按编号排列，正式参考文献编号按正文首次引用顺序重排。同一篇文献在不同问题中复用时，只著录一次。

| 使用位置 | 优先引用与论文网址 | 补充阅读 | 支持的论点 |
|---|---|---|---|
| Q1 预热阶段 | [R15 中文热质数值模型综述](https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2020010245)、[R01 中文药材干燥综述](https://xb.njucm.edu.cn/article/doi/10.14148/j.issn.1672-0482.2021.0786)、[R13 Kirchhoff 与非线性边界](https://doi.org/10.1007/s11431-022-2389-8) | [R02 浓度依赖扩散](https://doi.org/10.37394/232012.2021.16.9)、[R03 有限体积实例](https://doi.org/10.3390/agriculture10110507) | 连续介质场模型选型；积分变换思路及其作用范围 |
| Q2 变物性耦合 | 先读 [R15 中文热质数值模型综述](https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2020010245)，状态依赖建模见 [R12 热质耦合与状态依赖扩散](https://doi.org/10.1016/j.jfoodeng.2018.02.006)，复用 R13 | [R04 变系数有限体积](https://doi.org/10.3390/en14123405)、[R05 扩散率识别](https://doi.org/10.1515/cppm-2016-0074)、[R06 积分变换算法](https://doi.org/10.3390/computation12110218) | 联合热质建模；物性依赖；变换后仍需处理的非线性 |
| Q3 全域达标时间 | [R07 PDE 阈值时间误差](https://doi.org/10.1007/s10543-023-00947-1)、[R08 ODE 首次阈值时间](https://doi.org/10.1007/s10543-020-00825-0) | 公共实现见 R11 | 把达标时刻作为独立计算目标，并单独检查其数值误差 |
| Q4 收缩域与机制比较 | [R16 中文动网格热质研究](https://www.j-csam.org/jcsam/article/abstract/2022s234)、[R09 干燥收缩综述](https://doi.org/10.1111/1541-4337.12375)、[R14 固相收缩与热质守恒](https://doi.org/10.1111/jfpe.12614) | [R17 中文收缩动力学实验](https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2022070147)、[R10 ALE 干燥实例](https://doi.org/10.3390/en16114461)，复用 R07 | 收缩域热质建模；固相运动与守恒；几何变化及其假设 |
| 四问公共数值实现 | [R11 SciPy 论文](https://doi.org/10.1038/s41592-019-0686-2) | 见第 7 节官方接口文档 | 数值积分、求根和插值的软件实现来源 |

**先按论点选择中文来源：** 药材背景用 R01，Q1/Q2 的连续介质与热质建模用 R15，Q4 的收缩域问题用 R16；需要讨论收缩规律受工况影响时，再补 R17。R15 和 R16 分别来自《食品工业科技》和《农业机械学报》，不只用于背景介绍。

优先引用池为 **R01、R15、R16、R07、R08、R09、R11、R12、R13、R14**，不要求全部著录。可先以 **R01、R15、R16、R13、R07、R11** 构成 3 篇中文、3 篇英文的简要组合，再按实际论证补充状态依赖物性、固相守恒及收缩综述。R02、R03、R04、R05、R06、R10、R17 为补充。Q3 的首次阈值时间及其误差是专门的数值分析问题，本轮仍以 R07/R08 最贴合；一般干燥曲线拟合文章不能替代相应的算法依据。R13 支持积分变换的一般思路，浓度扩散形式仍以自身推导和 R02 为补充。

核验标记含义：**原文方法已核验**表示已查阅期刊提供的全文中相关章节；**摘要已核验**表示核对到摘要，来源在条目中注明，未据此声称读过全文。全文入口的访问权限可能随期刊政策变化。

### 1.1 期刊与索引核查

下面区分“期刊官网明确列出的索引”“期刊公布的单篇 EI 检索记录”和“Elsevier 官方接口返回的 Scopus 期刊来源记录”。期刊层面的来源记录不等于每篇论文均被收录；本轮未逐条获取文章的 Scopus EID，也未核对所有历史覆盖年份。未独立核实的 SCIE、EI 或中文核心身份不作推断。

| 期刊与对应文献 | 选择理由 | 本轮可核实的索引信息与来源 |
|---|---|---|
| **食品工业科技**，R15/R17 | 国内食品工程专业中文期刊，R15 直接综述热质模型，R17 提供收缩实验与拟合实例 | [期刊官网](https://www.spgykj.com/)明确标注 **北大核心、CSTPCD、EI、Scopus** 等；这里采用官网当前声明，未取得 R15/R17 单篇 EI 检索记录，不追认其发表年度的收录状态 |
| **农业机械学报**，R16 | 国内农业工程专业中文期刊，研究对象与收缩域热质传递直接对应 | [学报简介](https://www.j-csam.org/jcsam/site/menu/20101116171652001)列出中文核心、**EI、Scopus**；[2022 年增刊 EI 结果](https://www.j-csam.org/jcsam/site/menut/20230316163816001)第 23 条列出 R16 的题名、DOI、页码及 **Compendex 检索号 20231013692730** |
| **Journal of Food Engineering**，R12 | 食品工程领域主流专业期刊；Elsevier 出版，直接覆盖干燥热质模型 | [Elsevier 期刊记录](https://api.elsevier.com/content/serial/title/issn/02608774?httpAccept=application/json)返回 [Scopus 来源 20586](https://www.scopus.com/source/sourceInfo.url?sourceId=20586) |
| **Science China Technological Sciences**，R13 | 《中国科学》技术科学英文刊；Science China Press 与 Springer 合作出版 | [期刊官网](https://link.springer.com/journal/11431)明确列有 **SCIE、Scopus、EI Compendex、CSCD** |
| **BIT Numerical Mathematics**，R07/R08 | 数值分析领域专业期刊；阈值时间论文与本题算法目标直接对应 | [期刊官网](https://link.springer.com/journal/10543)明确列有 **SCIE、Scopus、Mathematical Reviews、zbMATH** |
| **Comprehensive Reviews in Food Science and Food Safety**，R09 | 食品科学领域重要综述期刊；IFT/Wiley 平台，适合收缩机理与研究背景 | [Elsevier 期刊记录](https://api.elsevier.com/content/serial/title/issn/15414337?httpAccept=application/json)返回 [Scopus 来源 4900152301](https://www.scopus.com/source/sourceInfo.url?sourceId=4900152301) |
| **Journal of Food Process Engineering**，R14 | 食品加工工程专业期刊；Wiley 出版，包含固相守恒与收缩耦合模型 | [Elsevier 期刊记录](https://api.elsevier.com/content/serial/title/issn/01458876?httpAccept=application/json)返回 [Scopus 来源 20589](https://www.scopus.com/source/sourceInfo.url?sourceId=20589) |
| **Nature Methods**，R11 | Nature Portfolio 方法学期刊；本条引用的是 SciPy 软件论文 | [期刊介绍](https://www.nature.com/nmeth/journal-information)与 [Elsevier 期刊记录](https://api.elsevier.com/content/serial/title/issn/15487091?httpAccept=application/json)已核实；后者返回 [Scopus 来源 21100778827](https://www.scopus.com/source/sourceInfo.url?sourceId=21100778827) |
| **南京中医药大学学报**，R01 | 中文药材干燥背景，与题目对象直接相关 | 已核实期刊原文；本轮未取得可独立核对的对应年度核心目录，不标注“北大核心/CSCD” |

**SCIE/Scopus 收录、期刊分区、单篇论文质量是不同信息。** 本指南不填未经指定年份核实的影响因子、JCR 分区或中科院分区；Crossref 的 DOI 登记与 OpenAlex 的检索记录，也不作为 SCI/EI 收录证明。

## 2. Q1：预热阶段的场模型与非线性扩散

当前 Q1 的热物性为常数，温度与含水率在数学上解耦，但水分扩散率仍随含水率变化。引用重点对应 [Q1 正文稿](q1/problem1_algorithm_analysis.md) 的模型选择、径向有限体积和积分通量，不应把 Q1 写成温湿双向耦合。

### R15 中文优先：热风干燥的连续介质模型与热质传递

**著录：** 刘格含, 王鹏, 吴小华, 等. 农产品热风干燥传热传质数值模拟研究进展[J]. 食品工业科技, 2020, 41(22): 342–350, 357. DOI: 10.13386/j.issn1002-0306.2020010245.

- **网址：** [期刊页面与摘要](https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2020010245)；[期刊 PDF 全文](https://www.spgykj.com/cn/article/pdf/preview/10.13386/j.issn1002-0306.2020010245.pdf)。
- **分类与优先级：** 中文热质数值模型综述；优先引用；Q1/Q2 主用，四问模型背景共用。
- **贴合之处：** 区分干燥动力学、连续介质假设与孔道网络三类模型。第 2 节介绍宏观多孔介质连续模型，其中第 2.1 节列出局部含湿量的扩散方程；第 2.3–2.4 节讨论热质耦合机制。比仅讨论干燥工艺的综述更适合解释本题为什么需要计算内部场。
- **正文位置：** Q1 第 1 节模型选型；Q2 模型建立前说明联合热质场的研究背景。可写：“热风干燥研究中，连续介质模型通过传递方程描述物料内部温度与水分的变化[R15]。结合本题要求输出不同半径处的状态，本文采用径向分布参数模型。”
- **方法差异：** 综述包含毛细流、蒸发冷凝和 Luikov 等模型，本题没有全部采用。Q1 两场解耦，Q2 的耦合来自题定物性反馈；不能因此将本题称为完整 Luikov 模型或引入未实现的潜热项。该文也不是本题 Kirchhoff 通量、BDF 或事件求根的算法出处。
- **核验：** 原刊摘要、卷期目录和 PDF 第 343–345 页的相关内容已核验，重点为第 1 节末的模型局限及第 2 节的连续介质方程。页码为 **342–350, 357**，不是连续的 342–357；期刊索引证据见第 1.1 节。

### R01 中文优先：药材干燥的模型分类与选型

**著录：** 巨浩羽, 赵士豪, 赵海燕, 等. 中草药干燥加工现状及发展趋势[J]. 南京中医药大学学报, 2021, 37(5): 786–796. DOI: 10.14148/j.issn.1672-0482.2021.0786.

- **网址：** [期刊页面与摘要](https://xb.njucm.edu.cn/article/doi/10.14148/j.issn.1672-0482.2021.0786)；[期刊 PDF 全文](https://xb.njucm.edu.cn/cn/article/pdf/preview/10.14148/j.issn.1672-0482.2021.0786.pdf)。
- **分类与优先级：** 中文综述；优先引用；Q1 主用，Q2/Q4 背景复用。
- **贴合之处：** 原文第 2 节区分理论、半理论与经验干燥模型，说明理论模型可描述内部温度、水分的时空分布，并讨论物性参数和收缩假设对精度的影响。
- **正文位置：** Q1 第 1 节说明为何求解径向场；或全文模型建立前介绍干燥模型类别。可写：“为描述药材内部温度与水分的空间差异，本文采用基于传递方程的分布参数模型。此类模型可表征干燥过程中内部状态的时空演化[R01]。”
- **适用范围：** 支持模型类别与选型理由；题目给定的物性系数、Robin 参数和本项目的计算精度仍由题面及数值验证说明。
- **核验：** 原文方法已核验，重点为第 2 节。页码按官方 PDF 实际 11 页、页眉 786–796 著录；网页末页字段及 PDF 首页推荐引文存在不一致，使用时勿直接照抄错误字段。

### R13 优先：Kirchhoff 变换与 Robin 边界的非线性

**著录：** ZHANG L M, KONG H, ZHENG H. Numerical manifold method for steady-state nonlinear heat conduction using Kirchhoff transformation[J]. Science China Technological Sciences, 2024, 67(4): 992–1006. DOI: 10.1007/s11431-022-2389-8.

- **网址：** [出版社页面与摘要](https://link.springer.com/article/10.1007/s11431-022-2389-8)；[DOI 入口](https://doi.org/10.1007/s11431-022-2389-8)。
- **分类与优先级：** 非线性扩散变换与边界处理；优先引用；Q1/Q2 主用。论文为英文，不计入中文篇数。
- **贴合之处：** 原文以 Kirchhoff 变换处理温度依赖导热系数，并明确指出：内部方程经过变换后，Robin 与辐射边界仍可保持非线性。这与本题“积分通量处理内部非线性、表面条件另行求解”的算法组织相契合。
- **正文位置：** Q1 第 3.1–3.2 节或 Q2 第 3.2–3.3 节的衔接。可写：“Kirchhoff 变换能够简化状态依赖的扩散算子，但 Robin 边界的非线性仍需单独处理[R13]。本题据此区分内部积分通量与表面状态方程，后者通过标量求根闭合。”
- **方法差异：** 原文为稳态导热与数值流形法，本题为瞬态水分积分通量、有限体积和 BDF。两者对应的是变换与边界处理的思想，原文不直接给出本题浓度通量格式，也不意味着 Q1 的常系数热方程需要 Kirchhoff 变换。
- **核验：** 出版社摘要与 Crossref 书目信息已核验。在线发表为 2023 年，卷期为 2024 年，按卷期年份著录；索引来源见第 1.1 节。

### R02 方法补充：Kirchhoff 变换与浓度依赖扩散

**著录：** GAMA R M S, GAMA R P S. The Kirchhoff transformation and the Fick’s second law with concentration-dependent diffusion coefficient[J]. WSEAS Transactions on Heat and Mass Transfer, 2021, 16: 59–67. DOI: 10.37394/232012.2021.16.9.

- **网址：** [DOI 入口](https://doi.org/10.37394/232012.2021.16.9)；[期刊 PDF 全文](https://wseas.com/journals/hmt/2021/a185113-006%282021%29.pdf)。
- **分类与优先级：** 非线性扩散方法；补充引用；Q1–Q4 共用。保留原因是浓度积分形式直接相关，不作为主流期刊优先组合的一部分。
- **贴合之处：** 第 2 节定义扩散系数关于浓度的积分变量，将 $D(C)\nabla C$ 写成势变量的梯度；与本项目利用 $K(C)=\int_0^C\exp(-a/s)\,\mathrm ds$ 构造水分积分通量直接对应。
- **正文位置：** Q1 第 3.1 节引入 $K(C)$ 前；Q2 第 3.2 节沿用时可再次引用。可写：“针对浓度依赖的非线性扩散，Kirchhoff 变换可将扩散系数与浓度梯度的乘积表示为积分势的梯度[R02]。据此，本文将含水率因子纳入界面积分通量。”
- **方法差异：** 原文采用分段常数扩散率与半隐式有限差分；本项目采用给定的指数函数、环形有限体积和 BDF。Q2–Q4 仅对浓度因子积分，温度因子仍参与耦合求解。原文讨论的扩散率正下界条件也不能直接用于 $C\to0$ 时的本题指数扩散率。
- **核验：** 原文方法已核验，重点为第 2–3 节。出版日期为 2021-07-08；其他论文参考文献中出现的“2001”是误写。

### R03 补充：扩散型干燥模型的有限体积实现

**著录：** SILVA E G, GOMEZ R S, GOMES J P, et al. Convective and Microwave Assisted Drying of Wet Porous Materials with Prolate Spheroidal Shape: A Finite-Volume Approach[J]. Agriculture, 2020, 10(11): 507. DOI: 10.3390/agriculture10110507.

- **网址：** [DOI 与期刊入口](https://doi.org/10.3390/agriculture10110507)；[期刊 PDF 全文](https://mdpi-res.com/d_attachment/agriculture/agriculture-10-00507/article_deploy/agriculture-10-00507.pdf)。
- **分类与优先级：** 干燥数值模型；补充引用；Q1 主用，Q2 可复用。
- **贴合之处：** 以内部扩散和表面对流描述热量、水分传递，采用有限体积离散并输出内部场分布，适合支撑“传递方程、表面交换、有限体积”这一建模路线。
- **正文位置：** Q1 第 3 节介绍有限体积离散时，作为同类干燥计算的应用实例。
- **方法差异：** 原文研究长旋转椭球体，包含微波体热源；本题使用一维径向圆柱模型，无微波热源。其文献作用是方法实例，不是本题几何、源项或精度结论的依据。
- **核验：** 原文方法已核验，重点为第 2 节。

## 3. Q2：变物性热质耦合与数值处理

当前 Q2 从题目原始初值出发，以 $\rho(C),c_p(C),k(C),D(T,C)$ 建立双向反馈，采用联合状态的隐式 BDF 推进。引用位置对应 [Q2 正文稿](q2/problem2_algorithm_analysis.md) 的第 2–4 节。

中文入口优先复用 **R15**：支持从整体干燥曲线进入内部热质场建模。需要进一步说明扩散率的状态依赖时，用 R12/R05；需要解释积分通量与边界非线性时，用 R13/R02。这些来源分别支持不同论点，不应把中文综述中的一般耦合模型直接写成附录 3 的具体物性关系。

### R12 优先：食品干燥中的热质耦合与状态依赖扩散

**著录：** ONWUDE D I, HASHIM N, ABDAN K, et al. Modelling of coupled heat and mass transfer for combined infrared and hot-air drying of sweet potato[J]. Journal of Food Engineering, 2018, 228: 12–24. DOI: 10.1016/j.jfoodeng.2018.02.006.

- **网址：** [DOI 与出版社入口](https://doi.org/10.1016/j.jfoodeng.2018.02.006)；[Crossref 书目信息](https://api.crossref.org/works/10.1016/j.jfoodeng.2018.02.006)；[OpenAlex 摘要索引记录](https://api.openalex.org/works/https://doi.org/10.1016/j.jfoodeng.2018.02.006?select=title,doi,abstract_inverted_index)。
- **分类与优先级：** 热质耦合建模；优先引用；Q2 主用，Q4 可作背景。
- **贴合之处：** 摘要说明模型联合预测温度与水分分布，考虑温度和收缩相关的扩散率，并在二维轴对称几何上数值求解。适合支撑状态相关物性和热质场联合建模的选择。
- **正文位置：** Q2 第 2.3 节“物性反馈机制”。可写：“已有食品干燥模型通过联合求解热质传递过程，并考虑扩散率对温度及收缩状态的依赖，描述内部温度与水分分布[R12]。本问采用附录 3 给定的物性关系，建立温度与含水率之间的反馈。”
- **方法差异：** 原文为红外与热风联合干燥，使用 COMSOL，并含红外能量输入；本题没有相应红外体热源。该文支持耦合建模方向，不替代本题物性系数，也不作为本题有限体积或 BDF 的方法出处。
- **核验：** Crossref 书目、Elsevier 文章元数据及 OpenAlex 收录摘要已交叉核对；尚未核验全文。Scopus 期刊来源见第 1.1 节。

### R04 方法补充：变系数、对流边界与有限体积热质求解

**著录：** MELO J C S, DELGADO J M P Q, SILVA W P, et al. Non-Equilibrium Thermodynamics-Based Convective Drying Model Applied to Oblate Spheroidal Porous Bodies: A Finite-Volume Analysis[J]. Energies, 2021, 14(12): 3405. DOI: 10.3390/en14123405.

- **网址：** [DOI 与期刊入口](https://doi.org/10.3390/en14123405)；[期刊 PDF 全文](https://mdpi-res.com/d_attachment/energies/energies-14-03405/article_deploy/energies-14-03405.pdf)。
- **分类与优先级：** 热质耦合建模与空间离散；补充引用。需要具体展开有限体积应用实例时使用。
- **贴合之处：** 原文同时求解温度与水分传递，考虑传递系数变化及表面对流条件，并使用有限体积法。与 Q2 的变系数、表面交换和联合热质计算框架相关。
- **正文位置：** Q2 第 2.3 节解释状态反馈，或第 3.1 节说明空间离散。可写：“变系数与表面交换条件会共同影响内部温度和水分的演化，相关干燥研究已采用有限体积框架对热质传递进行联合计算[R04]。”
- **方法差异：** 原文为非平衡热力学模型，区分液态与蒸汽传输，采用 Gauss–Seidel 求解；本题使用给定的有效扩散关系与 BDF。引用其建模框架时，应保留这一区别。
- **核验：** 原文方法已核验，重点为数学模型与 Numerical Solution 部分。

### R05 方法补充：扩散率的温度和含水率依赖

**著录：** HERMASSI I, AZZOUZ S, HASSINI L, et al. Moisture Diffusivity of Seedless Grape undergoing convective drying[J]. Chemical Product and Process Modeling, 2017, 12(1): 20160074. DOI: 10.1515/cppm-2016-0074.

- **网址：** [DOI 与出版社入口](https://doi.org/10.1515/cppm-2016-0074)；[出版方提交的书目信息与摘要](https://api.crossref.org/works/10.1515/cppm-2016-0074)。
- **分类与优先级：** 状态依赖扩散率与收缩传质；补充引用；Q2 主用，Q4 可复用。
- **贴合之处：** 摘要报告通过干燥实验和数值模型识别有效水分扩散率，讨论其温度和水分依赖；数值模型还包含固相守恒与收缩速度引起的液相传输。
- **正文位置：** Q2 第 2.1 节引入 $D(T,C)$，或第 2.3 节解释“升温改变扩散速率，脱水又改变传递条件”。可写：“干燥介质的有效水分扩散率可以同时依赖温度与含水状态[R05]，因此本问按附录 3 在时间推进中更新 $D(T,C)$。”
- **适用范围：** 文献支持状态依赖这一建模方向；原文对象为葡萄，其拟合系数、含水率基准及函数形式不直接移植到药材模型。本文 $\exp(-a/C)$ 的具体形式来自题目附录。
- **核验：** Crossref 书目信息与摘要已核验。正式出版于 2017 年；DOI 和文章号中的“2016”不代表引用年份。

### R06 补充：Kirchhoff 变换之后仍需处理的非线性

**著录：** RAMOS J I. Finite Difference Methods Based on the Kirchhoff Transformation and Time Linearization for the Numerical Solution of Nonlinear Reaction–Diffusion Equations[J]. Computation, 2024, 12(11): 218. DOI: 10.3390/computation12110218.

- **网址：** [DOI 与期刊入口](https://doi.org/10.3390/computation12110218)；[期刊 PDF 全文](https://mdpi-res.com/d_attachment/computation/computation-12-00218/article_deploy/computation-12-00218.pdf)。
- **分类与优先级：** 非线性扩散算法；补充引用；Q1–Q4 均可参考。
- **贴合之处：** 第 2 节展示积分势如何改变扩散算子的表达，同时保留储存项、源项或变量反演中的非线性；第 2.5 节讨论边界条件处理。
- **正文位置：** Q2 第 3.2 节说明积分通量的作用范围。可写：“积分变量简化了扩散通量的表达，但变换后的模型仍可能含有其他非线性项[R06]。本问保留温度因子及变物性反馈，在联合时间积分中求解。”
- **方法差异：** 原文研究有限差分与时间线性化方案；本项目正式结果采用有限体积与 BDF，未采用该文的时间线性化格式，也未采用另行设计的 Picard 迭代。
- **核验：** 原文方法已核验，重点为第 2 节。

## 4. Q3：从场变量计算转向首次达标时间

当前 Q3 求解 $M(t)=\max_r C_h(r,t)$ 首次达到阈值的时间。空间上重构并采样加密，时间上先扫描括区间，再以连续时间输出和 Brent 法求根。下面两篇比一般干燥曲线拟合论文更贴近 [Q3 正文稿](q3/problem3_algorithm_analysis.md) 的核心目标。

### R07 核心推荐：演化 PDE 的阈值到达时间误差

**著录：** CHAUDHRY J H, ESTEP D, GIANNINI T, et al. Error estimation for the time to a threshold value in evolutionary partial differential equations[J]. BIT Numerical Mathematics, 2023, 63(1): 12. DOI: 10.1007/s10543-023-00947-1.

- **网址：** [出版社页面与摘要](https://link.springer.com/article/10.1007/s10543-023-00947-1)；[DOI 入口](https://doi.org/10.1007/s10543-023-00947-1)。全文权限以出版社页面为准。
- **分类与优先级：** PDE 事件时间与误差分析；优先引用；Q3 主用，Q4 事件复用。
- **贴合之处：** 研究演化 PDE 解的某个泛函首次达到阈值的时刻，并针对这一目标量构造误差估计；包含热方程例子。它直接说明“场解误差”和“阈值时间误差”是相关但不同的评价对象。
- **正文位置：** Q3 第 2 节定义全域事件，或第 10 节解释为何检查达标时间收敛。可写：“对于演化 PDE，首次达到阈值的时间本身是需要单独评价的数值目标量[R07]。因此，本文除检查温度与含水率场外，还比较网格加密及积分容差变化引起的达标时刻偏移。”
- **方法差异：** 原文使用 Taylor 展开与伴随后验估计；本项目用网格、时间容差与重构检验提供数值证据。空间最大值泛函在极大点切换时可能不可微，原文的具体误差理论不能未经条件核查直接套用。
- **核验：** 出版社摘要与 Crossref 书目信息已核验，未核验付费全文中的全部定理条件。

### R08 优先：首次阈值时间、求根与误差传播

**著录：** CHAUDHRY J H, ESTEP D, STEVENS Z, et al. Error estimation and uncertainty quantification for first time to a threshold value[J]. BIT Numerical Mathematics, 2021, 61(1): 275–307. DOI: 10.1007/s10543-020-00825-0.

- **网址：** [出版社页面与摘要](https://link.springer.com/article/10.1007/s10543-020-00825-0)；[DOI 入口](https://doi.org/10.1007/s10543-020-00825-0)。全文权限以出版社页面为准。
- **分类与优先级：** ODE 事件求解与误差；优先引用；Q3/Q4 共用。篇幅有限时，可与 R07 按正文论点择一。
- **贴合之处：** 研究 ODE 解首次达到阈值的时间，分别从 Taylor 线性化与求根角度推导误差表示。有限体积空间离散后，本题进入 ODE 时间积分阶段，因此这一视角与事件后处理相关。
- **正文位置：** Q3 第 6 节“事件扫描与根求解”。用于说明：求根容差只约束给定数值轨迹上的根定位，整体事件精度还取决于轨迹本身。
- **方法差异：** 原文还研究伴随估计与不确定性量化；本题当前未开展这些计算。正文用它支持事件时间的误差意识即可，具体 Brent 实现见 R11 和官方接口文档。
- **核验：** 出版社摘要与 Crossref 书目信息已核验。在线发表为 2020 年，卷期出版为 2021 年，本指南按卷期年份著录。

## 5. Q4：收缩区域上的热质传递

当前 Q4 的 $R(t)$ 由附件给定。在均匀径向收缩假设下，材料坐标 $\xi=r/R(t)$ 将区域固定，并保留内部 $1/R(t)^2$ 尺度及边界的半径依赖。引用对应 [Q4 正文稿](q4/problem4_algorithm_analysis.md) 第 1–3 节；具体坐标推导和四组合分解由本项目自身给出。

### R16 中文优先：动网格上的收缩与热质传递

**著录：** 吴孟秋, 雷登文, 朱广飞, 等. 基于动网格的白萝卜热风干燥热质传递研究[J]. 农业机械学报, 2022, 53(S2): 293–302. DOI: 10.6041/j.issn.1000-1298.2022.S2.034.

- **网址：** [期刊页面与中英文摘要](https://www.j-csam.org/jcsam/article/abstract/2022s234)；[DOI 入口](https://doi.org/10.6041/j.issn.1000-1298.2022.S2.034)；[期刊公布的单篇 EI 检索记录，第 23 条](https://www.j-csam.org/jcsam/site/menut/20230316163816001)。
- **分类与优先级：** 中文收缩域热质耦合研究；优先引用；Q4 主用。刊于 **增刊 S2**，引用时保留增刊标记。
- **贴合之处：** 基于实验选择收缩模型，再通过动网格将收缩方程与热质传递方程联立，比较考虑和忽略收缩时的内部温度、水分预测。摘要明确讨论收缩引起的水分迁移路径变化，直接对应 Q4 的时变空间区域及其传递效应。
- **正文位置：** Q4 第 1 节提出收缩域问题，随后转入材料坐标推导。可写：“已有研究将收缩方程与热质传递方程通过动网格技术耦合，并比较收缩对内部温度和水分分布的影响[R16]。本题的半径历程由附件给定，在均匀径向收缩假设下，可进一步利用材料坐标将计算区域固定。”
- **方法差异：** 原文采用实验识别的 Hatamipour 收缩模型与动网格，本题采用规定的 $R(t)$、材料坐标、有限体积和 BDF。原文讨论水分蒸发耗热，本题没有显式潜热项；其“缩短迁移路径”的机制可供比较，具体温升、提速及实验误差不能直接移用于本题，也不能把本题写成采用了动网格。
- **核验：** 原刊中英文摘要及“引用本文”书目已核验，未取得可读全文。期刊公布的 EI 记录核对到题名、作者、293–302 页与相同 DOI，数据库标为 **Compendex**，检索号 **20231013692730**；这比仅引用期刊收录声明更具体。

### R09 优先：收缩机理与模型假设综述

**著录：** MAHIUDDIN M, KHAN M I H, KUMAR C, et al. Shrinkage of Food Materials During Drying: Current Status and Challenges[J]. Comprehensive Reviews in Food Science and Food Safety, 2018, 17(5): 1113–1126. DOI: 10.1111/1541-4337.12375.

- **网址：** [DOI 与出版社入口](https://doi.org/10.1111/1541-4337.12375)；[出版方提交的书目信息与摘要](https://api.crossref.org/works/10.1111/1541-4337.12375)。
- **分类与优先级：** 干燥收缩综述；优先引用。
- **贴合之处：** 综述材料性质、微结构、力学性质和干燥条件对收缩的影响，讨论经验收缩模型与物理模型的区别，适合解释为何 Q4 需要重新处理几何及其假设。
- **正文位置：** Q4 第 1 节提出时变域问题，或第 5 节讨论均匀收缩假设。可写：“干燥收缩受材料结构与过程条件共同影响，收缩模型的选择会影响热质传递描述[R09]。结合题目已给出的半径历程，本文采用规定几何演化的模型。”
- **适用范围：** 本文的半径函数来自附件，均匀径向收缩是建模假设；这篇综述提供研究背景，不构成这两项条件已经获得实验验证的依据。
- **核验：** Crossref 书目信息与摘要已核验。

### R14 优先：固相守恒、收缩速度与热质耦合

**著录：** AZZOUZ S, HERMASSI I, CHOUIKH R, et al. The convective drying of grape seeds: Effect of shrinkage on heat and mass transfer[J]. Journal of Food Process Engineering, 2018, 41(1): e12614. DOI: 10.1111/jfpe.12614.

- **网址：** [DOI 与出版社入口](https://doi.org/10.1111/jfpe.12614)；[出版方提交的书目信息与摘要](https://api.crossref.org/works/10.1111/jfpe.12614)。
- **分类与优先级：** 收缩与守恒耦合模型；优先引用；Q4 主用。
- **贴合之处：** 摘要明确描述固相守恒、液态水对流扩散和能量方程，并以脱水引起的固相收缩速度联系这些方程。相比仅修改半径或拟合干燥曲线的文章，它更接近本题材料运动、干骨架守恒和热质传递之间的关系。
- **正文位置：** Q4 第 1–2 节，从收缩假设进入材料速度与固定域推导之前。可写：“含收缩的干燥模型可通过固相运动联系质量守恒与热质传递方程[R14]。本题结合给定半径历程和均匀收缩假设，取材料速度 $v_r=(\dot R/R)r$，再将方程转换至固定材料区间。”
- **方法差异：** 原文对象及收缩建模条件与本题不同。本题的 $R(t)$、材料速度公式及坐标变换由题目数据和自身假设推导，不能称为直接采用该文全部方程；干骨架密度与有效热物性密度仍须区分。
- **核验：** Crossref 书目信息与出版方摘要已核验。在线发表为 2017 年，卷期为 2018 年；英文题名按登记原文保留。Scopus 期刊来源见第 1.1 节。

### R10 方法补充：考虑收缩的耦合干燥模型与固定几何对照

**著录：** TULY S S, JOARDDER M U H, WELSH Z G, et al. Mathematical Modelling of Heat and Mass Transfer during Jackfruit Drying Considering Shrinkage[J]. Energies, 2023, 16(11): 4461. DOI: 10.3390/en16114461.

- **网址：** [DOI 与期刊入口](https://doi.org/10.3390/en16114461)；[期刊 PDF 全文](https://mdpi-res.com/d_attachment/energies/energies-16-04461/article_deploy/energies-16-04461.pdf)。
- **分类与优先级：** 收缩域热质耦合与数值仿真；补充引用。需要展示 ALE 的具体干燥应用实例时使用。
- **贴合之处：** 建立包含收缩的热质传递模型，并比较考虑与忽略收缩的预测；第 3.4 节使用 ALE 框架处理区域运动。这与 Q4“传递方程的计算区域也随时间变化”的数学本质直接相关。
- **正文位置：** Q4 第 1 节介绍收缩域建模，随后转入本题材料坐标推导。可写：“已有干燥研究将收缩引起的区域变化纳入热质传递模型，并利用 ALE 框架追踪区域运动[R10]。本题半径历程已知，且采用均匀径向收缩假设，因此可通过材料坐标映射在固定区间内求解。”
- **方法差异：** 原文采用 COMSOL 有限元和 ALE，收缩与材料模型联动；本题使用给定 $R(t)$、固定材料网格上的有限体积与 BDF。原文不提供本题 $\xi$ 变换下的全部方程，也不保证收缩必然缩短干燥时间。
- **核验：** 原文方法已核验，重点为第 3 节，特别是第 3.4 节；已核对有无收缩的模型比较。

### R17 中文补充：收缩规律对干燥工况的依赖

**著录：** 韩琭丛, 金听祥, 张振亚, 等. 火龙果热泵干燥特性及收缩动力学模型分析[J]. 食品工业科技, 2023, 44(10): 242–248. DOI: 10.13386/j.issn1002-0306.2022070147.

- **网址：** [期刊页面与摘要](https://www.spgykj.com/article/doi/10.13386/j.issn1002-0306.2022070147)；[DOI 入口](https://doi.org/10.13386/j.issn1002-0306.2022070147)。
- **分类与优先级：** 中文收缩实验与经验模型；补充引用；Q4 假设讨论使用。
- **贴合之处：** 研究干燥温度、切片厚度和相对湿度对干燥速率与体积比的影响，并比较模型对收缩规律的描述。可用于说明收缩历程通常与材料和干燥条件有关，给定半径轨迹的适用范围应明确。
- **正文位置：** Q4 模型评价或假设讨论。可写：“干燥温度、物料厚度及空气湿度均可能影响材料的收缩规律[R17]，因此本文基于附件半径轨迹得到的结果，适用于该轨迹所代表的条件。”
- **方法差异：** 原文为火龙果热泵干燥实验及经验拟合，不提供本题耦合 PDE、材料速度或坐标变换的推导。本题不采用其 Quadratic 拟合参数，也不能据此断言药材具有相同收缩规律。
- **核验：** 原刊摘要与网页书目字段已核验，未核验全文。正式卷期为 2023 年；DOI 中的“202207”不能当作出版年份。

## 6. 四问公共数值实现

### R11 优先：SciPy 科学计算软件论文

**著录：** VIRTANEN P, GOMMERS R, OLIPHANT T E, et al. SciPy 1.0: fundamental algorithms for scientific computing in Python[J]. Nature Methods, 2020, 17(3): 261–272. DOI: 10.1038/s41592-019-0686-2.

- **网址：** [DOI 与期刊入口](https://doi.org/10.1038/s41592-019-0686-2)；[出版方提交的书目信息与摘要](https://api.crossref.org/works/10.1038/s41592-019-0686-2)。
- **分类与优先级：** 软件实现引用；优先引用；四问共用。
- **贴合之处：** 本项目依赖 SciPy 实现刚性 ODE 积分、标量求根和插值，适合在公共数值算法或软件环境说明处统一引用。
- **正文位置：** 首次说明 BDF、Brent 与插值实现时引用一次。可写：“数值计算基于 SciPy 科学计算库实现[R11]；时间推进采用隐式 BDF，表面状态及事件时刻由括区间求根获得。”
- **适用范围：** 此文是软件引用；BDF、Brent、PCHIP 都有更早的算法来源，不能将 2020 年写成这些算法的提出年份。Q1 采用统一数值接口也不改变两个场数学解耦的性质。
- **核验：** Crossref 书目信息与摘要已核验；下列官方接口文档已另行核对。

## 7. 实现查阅与引用边界

### 7.1 官方接口资料，单列为非论文来源

这些链接用于核对实现细节，不计入上述 17 篇近十年期刊论文。网址指向 SciPy 当前在线文档，项目实际依赖版本以 [uv.lock](../uv.lock) 为准。

| 方法 | 官方网址 | 适合核对的内容 |
|---|---|---|
| BDF | [SciPy BDF](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.BDF.html) | 隐式多步、自动变阶、误差容差、稀疏 Jacobian 结构 |
| Brent 求根 | [SciPy brentq](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brentq.html) | 连续性与异号括区间要求、求根容差的含义 |
| PCHIP | [SciPy PchipInterpolator](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.PchipInterpolator.html) | 保形三次插值与导数接口；本项目边界重构还有自身约束 |

### 7.2 由本项目推导和验证的内容

| 内容 | 正文中应使用的依据 |
|---|---|
| 题目物性、初边值及环境外推 | 题面附录、附件与模型假设；其他材料的文献系数不能替代它们 |
| Q1 圆柱解析基准、真实中心与表面恢复 | 本项目推导、独立热场基准和采样验证；R03 只提供同类数值应用背景 |
| Kirchhoff 通量与 BDF 的具体组合 | 优先用 R13 说明变换和边界非线性，R02/R06 补充具体积分思路，R11 支持软件实现；组合方案及其精度由本项目验证 |
| Q3 连续域最大值与阈值定位 | 本项目空间采样加密、时间容差和事件检查；R07/R08 支持将事件时间作为独立目标量 |
| Q4 材料速度与坐标导数抵消、几何尺度 | 均匀收缩假设下的坐标推导；R14 支持固相运动与守恒的联系，R16/R10 为动网格或 ALE 应用实例，均不直接给出本题离散方案 |
| Q4 重构场的全域极值 | 分段三次多项式端点与驻点比较；极值针对重构场，PDE 精度仍依赖网格与时间验证 |
| Q4 四组合机制分解 | 固定/收缩 × 附录 3/4 的正式对照与代数分解；本次不以机器学习 SHAP 文献替代其依据 |
| 连续阈值时刻与严格达标的 60 s 输出时刻 | 本项目事件定义与题目输出约定，两个时间应分别报告 |

当前正式解未采用阶段降阶、额外 Picard 求解器、伴随后验误差估计或 COMSOL/ALE 移动网格。文献中的这些方法可在相关工作或展望中讨论，不能写成本文已执行的算法。其他论文的实验吻合结果也不构成本题正式数值的实验验证。

上述文献按“实际论点”放到对应句末即可，无须在每个公式后堆叠引用。现代应用论文适合支持方法选择；本题参数代入、坐标推导、机制分解和最终数值应保留本项目自身的证据链。

## 8. 主流期刊候选：书目已核实，内容待核验

下面两篇来自传热领域主流期刊，适合后续通过学校数据库取得原文。本轮已用 Crossref 核对书目，并找到研究机构 DORA 的存储记录；出版页面访问受限，DORA 全文下载连接失败，尚未成功取得摘要或全文。因此不计入前述 17 篇，也不提供可直接放入正文的引用论断。

| 候选与完整书目 | 论文网址 | 期刊来源核查 | 待核验方向 |
|---|---|---|---|
| C01：DEFRAEYE T, RADU A. Convective drying of fruit: A deeper look at the air-material interface by conjugate modeling[J]. International Journal of Heat and Mass Transfer, 2017, 108: 1610–1622. | [DOI](https://doi.org/10.1016/j.ijheatmasstransfer.2017.01.002)；[DORA 存储记录](https://www.dora.lib4ri.ch/empa/item/empa:13545) | [Elsevier 期刊记录](https://api.elsevier.com/content/serial/title/issn/00179310?httpAccept=application/json)返回 [Scopus 来源 20448](https://www.scopus.com/source/sourceInfo.url?sourceId=20448) | Q1/Q2 内部传递与空气侧界面条件的关系 |
| C02：DEFRAEYE T, RADU A. Insights in convective drying of fruit by coupled modeling of fruit drying, deformation, quality evolution and convective exchange with the airflow[J]. Applied Thermal Engineering, 2018, 129: 1026–1038. | [DOI](https://doi.org/10.1016/j.applthermaleng.2017.10.082)；[DORA 存储记录](https://www.dora.lib4ri.ch/empa/item/empa:15412) | [Elsevier 期刊记录](https://api.elsevier.com/content/serial/title/issn/13594311?httpAccept=application/json)返回 [Scopus 来源 13688](https://www.scopus.com/source/sourceInfo.url?sourceId=13688) | Q4 干燥与变形的耦合方式，以及是否适用于给定半径历程 |
