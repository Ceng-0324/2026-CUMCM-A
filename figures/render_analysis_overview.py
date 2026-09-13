"""Render the analysis roadmap as native DrawIO cells and a vector PDF.

Labels are curated from paper/sections/2_analysis.tex. Shared node and edge
definitions keep both exports aligned; this script does not parse LaTeX.
"""
from __future__ import annotations

from dataclasses import dataclass
import html
from math import hypot
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from common.plotting import configure

configure(ROOT)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

WIDTH, HEIGHT = 800, 710
INK, MUTED = "#283C43", "#607980"
COLORS = [("#ECF4F0", "#337D70"), ("#EDF3FA", "#456F9B"),
          ("#FAF3E3", "#A18039"), ("#F8EEEE", "#A66268")]


@dataclass(frozen=True)
class Node:
    ident: str
    x: float
    y: float
    width: float
    height: float
    title: str
    body: str
    fill: str
    stroke: str


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    points: tuple[tuple[float, float], ...]
    dashed: bool = False


def layout():
    nodes = [
        Node("inputs", 36, 16, 232, 72, "题面与附件", "几何、烘房时序、物性\n收缩轨迹与共同初值", "#EDF3FA", "#456F9B"),
        Node("shared", 310, 16, 472, 72, "统一圆柱径向传递框架", "中心对称与 Robin 边界\n环形有限体积、隐式时间推进与连续场重构", "#ECF4F0", "#337D70"),
    ]
    edges = [Edge("inputs", "shared", ((268, 52), (310, 52)))]
    questions = [
        ("问题一：预热分布", "内外响应尺度不同\n水分扩散仍非线性",
         "附录 2：热质场解耦", "固定半径的一维径向模型\n保留非线性水分扩散",
         "温度与含水率场", "中心与表面差异\n独立复核端部热效应"),
        ("问题二：热质耦合", "温度、含水率与物性\n形成双向反馈",
         "附录 3：联合状态同步推进", "从共同初值独立计算\n通量按温度因子与浓度因子分解",
         "耦合温湿分布", "观测窗内的演化\n变物性通量与守恒"),
        ("问题三：全域达标", "连续场上的首达时间\n缓慢脱水放大时刻误差",
         "连续最大值与事件定位", "粗扫描括区间，再求根\n全域含水率阈值 0.15 kg/kg",
         "固定半径达标时长", "空间、时间与重构\n三类误差分离检验"),
        ("问题四：收缩影响", "时变区域与材料守恒\n几何、物性作用并存",
         "材料坐标与四组合对照", "ξ = r/R(t)，固定计算域\n固定/收缩半径 × 附录 3/4",
         "收缩时长与实际场", "越界留空、表面单列\n几何、物性及交互分解"),
    ]
    ys = (165, 274, 383, 492)
    for index, (y, contents, colors) in enumerate(zip(ys, questions, COLORS), 1):
        fill, stroke = colors
        for kind, x, width, offset in (("question", 36, 192, 0), ("method", 266, 290, 2), ("result", 602, 180, 4)):
            nodes.append(Node(f"q{index}-{kind}", x, y, width, 78,
                              contents[offset], contents[offset + 1], fill, stroke))
        middle = y + 39
        edges.extend([
            Edge("shared", f"q{index}-question", ((546, 88), (546, 111), (16, 111), (16, middle), (36, middle))),
            Edge(f"q{index}-question", f"q{index}-method", ((228, middle), (266, middle))),
            Edge(f"q{index}-method", f"q{index}-result", ((556, middle), (602, middle))),
            Edge(f"q{index}-result", "validation", ((782, middle), (795, middle), (795, 612), (408, 612), (408, 631))),
        ])
    for index, y in enumerate(ys[:-1], 1):
        edges.append(Edge(f"q{index}-method", f"q{index + 1}-method",
                          ((283, y + 78), (283, ys[index])), dashed=index != 2))
    nodes.append(Node("validation", 36, 631, 746, 65, "按各问特点开展检验与比较",
                      "网格与时间收敛 · 守恒与边界残差 · 独立基准 · 环境/半径输入敏感性",
                      "#F1F5F5", "#607980"))
    annotations = [
        (132, 141, "问题与关键难点", 11.6, "center", True),
        (411, 141, "建模与求解思路", 11.6, "center", True),
        (692, 141, "输出与针对性检验", 11.6, "center", True),
        (302, 258, "更换物性，从初值重算", 9.4, "left", False),
        (302, 367, "延长 Q2 演化，增加首达判据", 9.4, "left", False),
        (302, 476, "复用判据，收缩条件下独立重算", 9.4, "left", False),
        (36, 593, "长时环境：4 h 后取末小时均值；阶段诊断仅作机理解释", 10, "left", False),
    ]
    return nodes, edges, annotations


def render_pdf(path, nodes, edges, annotations):
    fig, ax = plt.subplots(figsize=(WIDTH / 100, HEIGHT / 100))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, WIDTH), ylim=(HEIGHT, 0), aspect="equal")
    ax.axis("off")
    for edge in edges:
        xs, ys = zip(*edge.points)
        ax.plot(xs, ys, color=MUTED, lw=0.85, linestyle="--" if edge.dashed else "-", zorder=1)
        px, py = edge.points[-2]
        ex, ey = edge.points[-1]
        length = hypot(ex - px, ey - py)
        head_start = (ex - 5 * (ex - px) / length, ey - 5 * (ey - py) / length)
        ax.add_patch(FancyArrowPatch(head_start, edge.points[-1], arrowstyle="-|>",
                                    mutation_scale=8, color=MUTED, lw=0.85,
                                    shrinkA=0, shrinkB=1, zorder=2))
    for node in nodes:
        ax.add_patch(FancyBboxPatch((node.x, node.y), node.width, node.height,
                                   boxstyle="round,pad=0,rounding_size=3",
                                   facecolor=node.fill, edgecolor=node.stroke, linewidth=1, zorder=3))
        ax.text(node.x + node.width / 2, node.y + 17, node.title,
                ha="center", va="center", fontsize=11.2, weight="bold", color=node.stroke, zorder=4)
        ax.text(node.x + node.width / 2, node.y + node.height / 2 + 13, node.body,
                ha="center", va="center", fontsize=10.1, linespacing=1.35, color=INK, zorder=4)
    for x, y, text, size, align, bold in annotations:
        ax.text(x, y, text, fontsize=size, ha=align, va="center", color=MUTED,
                weight="bold" if bold else "normal", zorder=4)
    fig.savefig(path, facecolor="white", metadata={"Title": "问题分析总体流程：统一模型与逐问扩展"})
    plt.close(fig)


def render_drawio(path, nodes, edges, annotations):
    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="问题分析总体流程", id="analysis-overview")
    model = ET.SubElement(diagram, "mxGraphModel", page="1", pageWidth=str(WIDTH), pageHeight=str(HEIGHT), grid="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    by_id = {node.ident: node for node in nodes}
    for node in nodes:
        title = f'<div style="font-size:15.56px;color:{node.stroke};margin-bottom:5px"><b>{html.escape(node.title)}</b></div>'
        body = '<div style="line-height:135%">' + html.escape(node.body).replace("\n", "<br>") + "</div>"
        style = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={node.fill};"
                 f"strokeColor={node.stroke};strokeWidth=1.4;fontSize=14.03;fontFamily=STHeiti;"
                 f"fontColor={INK};align=center;verticalAlign=middle;spacing=5;")
        cell = ET.SubElement(root, "mxCell", id=node.ident, value=title + body, style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(node.x), y=str(node.y), width=str(node.width), height=str(node.height), attrib={"as": "geometry"})
    for index, edge in enumerate(edges):
        source, target = by_id[edge.source], by_id[edge.target]
        sx, sy = edge.points[0]
        tx, ty = edge.points[-1]
        style = (f"edgeStyle=none;rounded=0;html=0;endArrow=block;endFill=1;strokeColor={MUTED};"
                 f"strokeWidth=1.2;dashed={int(edge.dashed)};"
                 f"exitX={(sx - source.x) / source.width};exitY={(sy - source.y) / source.height};exitPerimeter=0;"
                 f"entryX={(tx - target.x) / target.width};entryY={(ty - target.y) / target.height};entryPerimeter=0;")
        cell = ET.SubElement(root, "mxCell", id=f"edge-{index}", style=style, edge="1", parent="1", source=edge.source, target=edge.target)
        geo = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        if len(edge.points) > 2:
            points = ET.SubElement(geo, "Array", attrib={"as": "points"})
            for x, y in edge.points[1:-1]:
                ET.SubElement(points, "mxPoint", x=str(x), y=str(y))
    for index, (x, y, text, size, align, bold) in enumerate(annotations):
        width = WIDTH - x - 24 if align == "left" else 2 * min(130, x, WIDTH - x)
        style = (f"text;html=0;whiteSpace=wrap;align={align};verticalAlign=middle;"
                 f"fontFamily=STHeiti;fontColor={MUTED};fontSize={size * 100 / 72};fontStyle={int(bold)};")
        cell = ET.SubElement(root, "mxCell", id=f"annotation-{index}", value=text, style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x if align == "left" else x - width / 2),
                      y=str(y - 12), width=str(width), height="24", attrib={"as": "geometry"})
    ET.indent(mxfile)
    ET.ElementTree(mxfile).write(path, encoding="utf-8", xml_declaration=True)


def main():
    nodes, edges, annotations = layout()
    render_drawio(ROOT / "figures/fig_roadmap.drawio", nodes, edges, annotations)
    render_pdf(ROOT / "figures/fig_roadmap.pdf", nodes, edges, annotations)
    print(f"Generated fig_roadmap: {len(nodes)} editable nodes, {len(edges)} connected edges, one-page PDF.")


if __name__ == "__main__":
    main()
