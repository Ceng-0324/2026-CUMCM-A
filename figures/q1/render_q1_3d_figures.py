"""Render Q1 axonometric geometry and finite-volume schematics, without solving."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
from urllib.parse import quote
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
from common.plotting import configure

configure(ROOT)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Ellipse, FancyArrowPatch, Polygon, Rectangle

OUT = ROOT / "figures" / "q1"
INK = "#283D43"
MUTED = "#63777A"
TEAL = "#247F80"
HEAT = "#C23B35"
MASS = "#2266A6"


def label(ax, x, y, text, color=INK, size=11, ha="center", **kwargs):
    return ax.text(x, y, text, color=color, fontsize=size, ha=ha, va="center", zorder=20, **kwargs)


def line(ax, points, color=MUTED, lw=1, style="-", zorder=8):
    points = np.asarray(points)
    ax.plot(points[:, 0], points[:, 1], color=color, lw=lw, linestyle=style, zorder=zorder)


def arrow(ax, start, end, color=INK, both=False, lw=1.5):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="<->" if both else "-|>", mutation_scale=11,
                                lw=lw, color=color, shrinkA=0, shrinkB=0, zorder=15))


def ellipse_points(center, radii, theta):
    return np.asarray(center) + np.column_stack((radii[0] * np.cos(theta), radii[1] * np.sin(theta)))


def tube_side(ax, front, back, radii, color, zorder=2):
    angles = np.linspace(-np.pi / 2, np.pi / 2, 120)
    a = ellipse_points(front, radii, angles)
    b = ellipse_points(back, radii, angles)
    base = np.asarray(to_rgb(color))
    for index in range(len(angles) - 1):
        light = 0.84 + 0.16 * np.sin((angles[index] + np.pi / 2) / 2)
        ax.add_patch(Polygon([a[index], b[index], b[index + 1], a[index + 1]],
                             facecolor=base * light, edgecolor="none", zorder=zorder))
    for theta in (-np.pi / 2, np.pi / 2):
        line(ax, [ellipse_points(front, radii, [theta])[0], ellipse_points(back, radii, [theta])[0]],
             color=TEAL, lw=0.9)


def canvas(height):
    fig, ax = plt.subplots(figsize=(12, height))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, 12), ylim=(0, height), aspect="equal")
    ax.set_axis_off()
    return fig, ax


def export(fig, name, title):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", facecolor="white", metadata={"Title": title})
    svg = BytesIO()
    fig.savefig(svg, format="svg", facecolor="white")
    width, height = fig.get_size_inches() * 96
    mxfile = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(mxfile, "diagram", name=title, id=name)
    model = ET.SubElement(diagram, "mxGraphModel", page="1", pageWidth=str(width), pageHeight=str(height), grid="0")
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    style = "shape=image;aspect=fixed;image=data:image/svg+xml," + quote(svg.getvalue().decode(), safe="") + ";"
    cell = ET.SubElement(root, "mxCell", id="vector-sheet", value="", style=style, vertex="1", parent="1")
    ET.SubElement(cell, "mxGeometry", x="0", y="0", width=str(width), height=str(height), attrib={"as": "geometry"})
    ET.indent(mxfile)
    ET.ElementTree(mxfile).write(OUT / f"{name}.drawio", encoding="utf-8", xml_declaration=True)
    plt.close(fig)
    print(f"Generated {name}.pdf and {name}.drawio")


def physical_model():
    fig, ax = canvas(5.35)
    label(ax, 0.3, 5.03, "(a) 圆柱几何与径向假设", ha="left", size=13, weight="bold")
    label(ax, 6.85, 5.03, "(b) 真实表面与环境交换", ha="left", size=13, weight="bold")
    front, back, radii = (1.55, 2.73), (5.5, 3.19), (0.74, 1.07)
    ax.add_patch(Ellipse(back, 2 * radii[0], 2 * radii[1], facecolor="#ACCAC3", edgecolor=TEAL, lw=0.9, zorder=1))
    tube_side(ax, front, back, radii, "#B7D4CE")
    ax.add_patch(Ellipse(front, 2 * radii[0], 2 * radii[1], facecolor="#F0F6F3", edgecolor=TEAL, lw=1.2, zorder=9))
    for ratio in (0.35, 0.67):
        ax.add_patch(Ellipse(front, 2 * radii[0] * ratio, 2 * radii[1] * ratio, fill=False, edgecolor="#A0BAB5", lw=0.75, zorder=10))
    line(ax, [front, back], style="--", color="#617977", zorder=11)
    radial_end = ellipse_points(front, radii, [1.27])[0]
    arrow(ax, front, radial_end, TEAL)
    label(ax, 1.22, 3.17, "$r$", color=TEAL, size=12)
    line(ax, [radial_end, (1.83, 4.1), (0.7, 4.1)], color=TEAL)
    label(ax, 1.12, 4.33, r"$R=2\,\mathrm{cm}$", size=12)
    ax.plot(*front, marker="o", ms=3.6, color=INK, zorder=16)
    line(ax, [front, (0.5, 2.1), (0.5, 1.55)], zorder=16)
    label(ax, 0.8, 1.33, "$r=0$", size=11)
    label(ax, 3.99, 3.15, r"$T(r,t),\ C(r,t)$", size=13)
    label(ax, 4.0, 2.71, "径向分布，轴向均匀", size=11)
    arrow(ax, (3.23, 4.5), (3.23, 3.82), HEAT, lw=2)
    label(ax, 3.08, 4.73, r"热量流入 $q_R<0$", HEAT, size=10.5)
    arrow(ax, (4.91, 4.0), (4.91, 4.55), MASS, lw=2)
    label(ax, 5.1, 4.77, r"水分流出 $j_R>0$", MASS, size=10.5)
    start, end = (1.55, 1.0), (5.5, 1.46)
    line(ax, [(1.55, 1.6), (1.55, 0.83)], lw=0.8)
    line(ax, [(5.5, 2.05), (5.5, 1.29)], lw=0.8)
    arrow(ax, start, end, both=True, lw=1)
    label(ax, 3.6, 0.84, r"$L=25\,\mathrm{cm}$  （轴向示意压缩）", size=10.5)
    label(ax, 3.15, 0.32, r"中心对称：$T_r(0,t)=C_r(0,t)=0$", size=11)
    ax.add_patch(Rectangle((7.2, 1.45), 1.8, 2.85, facecolor="#EBF3EF", edgecolor="none"))
    line(ax, [(9.0, 1.45), (9.0, 4.3)], color=TEAL, lw=1.8)
    label(ax, 8.1, 4.05, "药材内部", size=11)
    label(ax, 10.65, 4.05, "烘房环境", size=11)
    arrow(ax, (10.87, 3.28), (7.75, 3.28), HEAT, lw=2)
    arrow(ax, (7.75, 2.12), (10.87, 2.12), MASS, lw=2)
    ax.plot(9, 3.28, "o", color=HEAT, ms=5, zorder=18)
    ax.plot(9, 2.12, "o", color=MASS, ms=5, zorder=18)
    label(ax, 8.69, 3.61, "$T_s$", HEAT, size=12)
    label(ax, 10.51, 3.61, r"$T_\infty(t)$", HEAT, size=12)
    label(ax, 8.69, 2.48, "$C_s$", MASS, size=12)
    label(ax, 10.51, 2.48, r"$C_e(t)$", MASS, size=12)
    label(ax, 9.0, 1.21, "真实表面 $r=R$", TEAL, size=11)
    label(ax, 9.36, 0.73, r"$q_R=h[T_s-T_\infty(t)]$", HEAT, size=12)
    label(ax, 9.36, 0.25, r"$j_R=k_m[C_s-C_e(t)]$", MASS, size=12)
    export(fig, "fig_q1_3d_cylinder_model", "问题一圆柱径向模型与 Robin 边界")


def control_volume_model():
    fig, ax = canvas(5.65)
    label(ax, 0.3, 5.31, "(a) 三维环形控制体", ha="left", size=13, weight="bold")
    label(ax, 6.55, 5.31, "(b) 径向局部展开与共享通量", ha="left", size=13, weight="bold")
    front, back = (1.6, 3.25), (4.85, 3.63)
    outer, inner = (0.82, 1.13), (0.53, 0.73)
    ax.add_patch(Ellipse(back, 2 * outer[0], 2 * outer[1], facecolor="#ACCAC3", edgecolor=TEAL, lw=0.9, zorder=1))
    tube_side(ax, front, back, outer, "#A5CDC3")
    ax.add_patch(Ellipse(front, 2 * outer[0], 2 * outer[1], facecolor="#D6E9DF", edgecolor=TEAL, lw=1.1, zorder=9))
    aperture = Ellipse(front, 2 * inner[0], 2 * inner[1], facecolor="#FAFCFB", edgecolor=TEAL, lw=0.85, zorder=10)
    ax.add_patch(aperture)
    theta = np.linspace(-np.pi / 2, np.pi / 2, 100)
    a, b = ellipse_points(front, inner, theta), ellipse_points(back, inner, theta)
    for i in range(len(theta) - 1):
        panel = Polygon([a[i], b[i], b[i + 1], a[i + 1]], facecolor="#D1E1DA", edgecolor="none", zorder=11)
        panel.set_clip_path(aperture)
        ax.add_patch(panel)
    line(ax, [front, back], style="--", lw=0.9, zorder=12)
    ax.plot(*front, "o", color=INK, ms=3, zorder=16)
    r_in = ellipse_points(front, inner, [-0.95])[0]
    r_out = ellipse_points(front, outer, [-0.95])[0]
    arrow(ax, front, r_out, color=INK, lw=1.1)
    ax.plot(r_in[0], r_in[1], "o", color=TEAL, ms=4, zorder=18)
    ax.plot(r_out[0], r_out[1], "o", color=TEAL, ms=4, zorder=18)
    line(ax, [r_in, (0.75, 2.18), (0.75, 1.75)], color=TEAL, zorder=17)
    line(ax, [r_out, (2.64, 2.13), (2.64, 1.75)], color=TEAL, zorder=17)
    label(ax, 0.75, 1.5, r"$r_{i-1/2}$", TEAL, size=12)
    label(ax, 2.64, 1.5, r"$r_{i+1/2}$", TEAL, size=12)
    label(ax, 3.97, 3.48, r"控制体 $\Omega_i$", size=12)
    label(ax, 4.05, 3.02, r"厚度 $\Delta r$，长度 $L$", size=10.5)
    label(ax, 3.1, 4.79, "相邻控制体沿半径嵌套", MUTED, size=10.5)
    label(ax, 3.0, 0.94, r"实际体积：$|\Omega_i|=2\pi L V_i$", size=12)
    label(ax, 3.0, 0.34, r"几何权重：$V_i=(r_{i+1/2}^2-r_{i-1/2}^2)/2$", size=12)
    left, right, center = 8.1, 9.9, 9.0
    ax.add_patch(Rectangle((6.6, 2.25), 5.15, 2.1, facecolor="#F5F7F7", edgecolor="none"))
    ax.add_patch(Rectangle((left, 2.25), right - left, 2.1, facecolor="#DCEDE4", edgecolor="none"))
    for x in (left, right):
        line(ax, [(x, 2.25), (x, 4.5)], TEAL, lw=1.2)
    line(ax, [(center, 2.25), (center, 4.4)], style="--", lw=0.9)
    for x, text in ((7.2, r"$T_{i-1},C_{i-1}$"), (9.0, r"$T_i,C_i$"), (10.8, r"$T_{i+1},C_{i+1}$")):
        ax.plot(x, 3.4, "o", ms=4.5, color=INK, zorder=18)
        label(ax, x, 3.72, text, size=12)
    for x, index in ((left, "i-1/2"), (right, "i+1/2")):
        arrow(ax, (x - 0.42, 4.32), (x + 0.42, 4.32), HEAT, lw=1.8)
        label(ax, x, 4.76, f"$q_{{{index}}}$", HEAT, size=12)
        arrow(ax, (x - 0.42, 2.63), (x + 0.42, 2.63), MASS, lw=1.8)
        label(ax, x, 3.01, f"$j_{{{index}}}$", MASS, size=12)
    for x, text in ((left, r"$r_{i-1/2}$"), (center, "$r_i$"), (right, r"$r_{i+1/2}$")):
        label(ax, x, 1.99, text, size=11)
    arrow(ax, (left, 1.55), (right, 1.55), both=True, lw=1)
    label(ax, center, 1.28, r"$\Delta r$", size=11)
    arrow(ax, (10.55, 1.55), (11.7, 1.55), lw=1)
    label(ax, 11.12, 1.28, "$+r$", size=11)
    label(ax, 9.13, 0.79, "箭头表示通量正方向；同一界面在相邻单元中异号计入", size=10.1)
    label(ax, 9.13, 0.3, r"中心界面 $r_{1/2}=0$，面积加权通量为零", size=11)
    export(fig, "fig_q1_3d_control_volume", "问题一环形有限体积与共享界面通量")


if __name__ == "__main__":
    physical_model()
    control_volume_model()
