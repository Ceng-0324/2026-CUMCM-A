"""生成紧凑的问题分析总体流程图（DrawIO 源文件与 PDF）。"""
from __future__ import annotations

import html
from dataclasses import dataclass
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

WIDTH, HEIGHT = 700, 445
INK, MUTED = "#283C43", "#607980"
COLORS = [("#ECF4F0", "#337D70"), ("#EDF3FA", "#456F9B"),
          ("#FAF3E3", "#A18039"), ("#F8EEEE", "#A66268")]

@dataclass(frozen=True)
class Node:
    ident: str; x: float; y: float; width: float; height: float
    title: str; body: str; fill: str; stroke: str

@dataclass(frozen=True)
class Edge:
    source: str; target: str; points: tuple[tuple[float, float], ...]; dashed: bool = False


def layout():
    nodes = [
        Node("input", 28, 18, 190, 54, "题面与附件", "几何、环境时序、物性与收缩轨迹", "#EDF3FA", "#456F9B"),
        Node("framework", 244, 18, 428, 54, "统一径向传递框架", "中心对称 + Robin 边界 + 环形有限体积 + 隐式推进", "#ECF4F0", "#337D70"),
    ]
    edges = [Edge("input", "framework", ((218, 45), (244, 45)))]
    questions = [
        ("Q1 预热分布", "固定半径\n热质解耦", "守恒有限体积\n非线性扩散", "温度/含水率\n时空场"),
        ("Q2 变物性耦合", "温度—含水率\n双向反馈", "联合状态隐式\n同步推进", "全过程\n温湿演化"),
        ("Q3 全域达标", "最大含水率\n首达判据", "连续场重构\n事件求根", "达标时刻\n误差检验"),
        ("Q4 收缩影响", "时变半径\n守恒核算", "材料坐标 ξ=r/R(t)\n四组合对照", "收缩时长\n机制分解"),
    ]
    x0, gap, w, h, y = 28, 10, 157, 122, 128
    for i, (title, body, method, result) in enumerate(questions):
        x = x0 + i * (w + gap); fill, stroke = COLORS[i]
        nodes.extend([
            Node(f"q{i+1}", x, y, w, h, title, body, fill, stroke),
            Node(f"m{i+1}", x, y + h + 16, w, 56, "方法", method, fill, stroke),
            Node(f"r{i+1}", x, y + h + 88, w, 50, "输出", result, fill, stroke),
        ])
        edges.extend([
            Edge("framework", f"q{i+1}", ((458, 72), (458, 96), (x + w / 2, 96), (x + w / 2, y))),
            Edge(f"q{i+1}", f"m{i+1}", ((x + w / 2, y + h), (x + w / 2, y + h + 16))),
            Edge(f"m{i+1}", f"r{i+1}", ((x + w / 2, y + h + 72), (x + w / 2, y + h + 88))),
        ])
    nodes.append(Node("check", 28, 398, 644, 38, "统一检验", "网格/时间收敛 · 守恒与边界残差 · 独立基准 · 输入敏感性", "#F1F5F5", "#607980"))
    for i in range(1, 5):
        x = x0 + (i - 1) * (w + gap) + w / 2
        edges.append(Edge(f"r{i}", "check", ((x, y + h + 138), (x, 370), (350, 382), (350, 398)), dashed=True))
    return nodes, edges


def render_pdf(path, nodes, edges):
    fig, ax = plt.subplots(figsize=(WIDTH / 100, HEIGHT / 100))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, WIDTH), ylim=(HEIGHT, 0), aspect="equal"); ax.axis("off")
    for edge in edges:
        xs, ys = zip(*edge.points)
        ax.plot(xs, ys, color=MUTED, lw=0.75, linestyle="--" if edge.dashed else "-", zorder=1)
        px, py = edge.points[-2]; ex, ey = edge.points[-1]
        length = hypot(ex - px, ey - py) or 1
        start = (ex - 5 * (ex - px) / length, ey - 5 * (ey - py) / length)
        ax.add_patch(FancyArrowPatch(start, (ex, ey), arrowstyle="-|>", mutation_scale=7,
                                     color=MUTED, lw=0.75, shrinkA=0, shrinkB=1, zorder=2))
    for node in nodes:
        ax.add_patch(FancyBboxPatch((node.x, node.y), node.width, node.height,
                                    boxstyle="round,pad=0,rounding_size=3",
                                    facecolor=node.fill, edgecolor=node.stroke, linewidth=0.9, zorder=3))
        ax.text(node.x + node.width / 2, node.y + 16, node.title, ha="center", va="center",
                fontsize=9.4, weight="bold", color=node.stroke, zorder=4)
        ax.text(node.x + node.width / 2, node.y + node.height / 2 + 12, node.body,
                ha="center", va="center", fontsize=8.5, linespacing=1.25, color=INK, zorder=4)
    fig.savefig(path, facecolor="white", metadata={"Title": "问题分析总体流程"}); plt.close(fig)


def render_drawio(path, nodes, edges):
    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name="问题分析总体流程", id="analysis-overview")
    model = ET.SubElement(diagram, "mxGraphModel", page="1", pageWidth=str(WIDTH), pageHeight=str(HEIGHT), grid="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0"); ET.SubElement(root, "mxCell", id="1", parent="0")
    for node in nodes:
        value = (f'<div style="font-size:13px;color:{node.stroke};margin-bottom:3px"><b>{html.escape(node.title)}</b></div>'
                 f'<div style="line-height:125%">{html.escape(node.body).replace(chr(10), "<br>")}</div>')
        style = (f"rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor={node.fill};strokeColor={node.stroke};"
                 f"strokeWidth=1.2;fontSize=11;fontFamily=STHeiti;fontColor={INK};align=center;verticalAlign=middle;spacing=4;")
        cell = ET.SubElement(root, "mxCell", id=node.ident, value=value, style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(node.x), y=str(node.y), width=str(node.width), height=str(node.height), attrib={"as": "geometry"})
    for i, edge in enumerate(edges):
        style = f"edgeStyle=none;rounded=0;html=0;endArrow=block;endFill=1;strokeColor={MUTED};strokeWidth=1;dashed={int(edge.dashed)};"
        cell = ET.SubElement(root, "mxCell", id=f"edge-{i}", style=style, edge="1", parent="1", source=edge.source, target=edge.target)
        geo = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as": "geometry"})
        if len(edge.points) > 2:
            arr = ET.SubElement(geo, "Array", attrib={"as": "points"})
            for x, y in edge.points[1:-1]: ET.SubElement(arr, "mxPoint", x=str(x), y=str(y))
    ET.indent(mxfile); ET.ElementTree(mxfile).write(path, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    nodes, edges = layout()
    render_drawio(ROOT / "figures/fig_roadmap.drawio", nodes, edges)
    render_pdf(ROOT / "figures/fig_roadmap.pdf", nodes, edges)
    print(f"Generated compact analysis roadmap: {len(nodes)} nodes, {len(edges)} edges")
