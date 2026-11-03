"""A plan of the whole course to mark camera positions and coverage on (the owner's camera planning sheet).

    python3 tools/course/draw_camera_plan.py

Reads  courses/ascot.json (turf, rails, furlong poles, stand), courses/ascot-planting.json (belt trees),
       courses/ascot-site-dressing.json (site pieces, shown faintly)
Writes reference/course/layout/ascot-camera-plan.pdf (A3 landscape, two pages: the whole course, then the
       home straight and stand enlarged) and the same pages as ascot-camera-plan.png / -straight.png

World axes as courses/ascot.json (x east, z south, metres from the winning post); drawn north up.
Furlong markers are distance to go, as on the course.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Polygon as MplPoly, Rectangle, FancyArrowPatch, Circle

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
rp = lambda *p: os.path.join(REPO, *p)
C = json.load(open(rp("courses/ascot.json")))
PL = json.load(open(rp("courses/ascot-planting.json")))
D = json.load(open(rp("courses/ascot-site-dressing.json")))
W, FRONT = C["trackWidth"], C["grandstand"]["frontLine"]
STAND = (-102.5, FRONT, 405.0, FRONT + 40)          # the stand's footprint, roughly (x0, z0, x1, z1)
COL = dict(paper="#f6f1e2", grass="#c9dba6", infield="#d3e2b3", track="#eef3d6", rail="#ffffff", railedge="#6f8a55",
           tree="#4f7a3f", stand="#efe3c4", standedge="#8a744a", ink="#1f2a1c", soft="#5d6b55", post="#d23aa8",
           pole="#1f5a38", piece="#e9e3d0", grid="#ffffff", key="#ffffff")
P = lambda pts: np.array([[x, -z] for x, z in pts])


def draw(ax, X0, X1, Z0, Z1, labels_big):
    ax.set_xlim(X0, X1); ax.set_ylim(-Z1, -Z0); ax.set_aspect("equal")
    ax.set_facecolor(COL["grass"])
    step = 100
    for gx in range(int(X0 // step) * step, int(X1) + 1, step):
        ax.axvline(gx, color=COL["grid"], lw=0.5, alpha=0.6, zorder=0)
    for gz in range(int(Z0 // step) * step, int(Z1) + 1, step):
        ax.axhline(-gz, color=COL["grid"], lw=0.5, alpha=0.6, zorder=0)
    rings = C["track"]["surface"]
    ax.add_patch(MplPoly(P(rings[1]), closed=True, fc=COL["infield"], ec="none", zorder=1))
    ax.add_patch(MplPoly(P(rings[0]), closed=True, fc=COL["track"], ec=COL["railedge"], lw=0.8, zorder=2))
    ax.add_patch(MplPoly(P(rings[1]), closed=True, fc=COL["infield"], ec=COL["railedge"], lw=0.8, zorder=2))
    for line in C["rails"]["lines"]:
        a = P(line); ax.plot(a[:, 0], a[:, 1], color=COL["rail"], lw=1.4, zorder=3)
    t = np.array([[x, -z] for x, z, *_ in PL["trees"]])
    ax.scatter(t[:, 0], t[:, 1], s=4 if labels_big else 9, c=COL["tree"], lw=0, zorder=2, alpha=0.8)
    for p in D["keepClear"]:
        ax.add_patch(Rectangle((p[0], -p[3]), p[2] - p[0], p[3] - p[1], fc=COL["piece"], ec=COL["soft"], lw=0.3, zorder=2, alpha=0.9))
    x0, z0, x1, z1 = STAND
    ax.add_patch(Rectangle((x0, -z1), x1 - x0, z1 - z0, fc=COL["stand"], ec=COL["standedge"], lw=1.0, zorder=4))
    ax.text((x0 + x1) / 2, -(z0 + z1) / 2, "Main stand (507 m)", ha="center", va="center", fontsize=9 if labels_big else 12, color=COL["ink"], zorder=5)
    ax.add_patch(Rectangle((-6, -(z0 + 18)), 12, 18, fc="#d8c79c", ec=COL["standedge"], lw=0.8, zorder=5))
    ax.text(0, -(z0 + 24), "clock tower", ha="center", va="top", fontsize=7 if labels_big else 9, color=COL["soft"], zorder=5)
    # winning post
    ax.plot([0, 0], [0, -W], color=COL["post"], lw=2.5, zorder=6)
    ax.text(0, 8, "Winning post", ha="center", va="bottom", fontsize=8 if labels_big else 11, color=COL["post"], weight="bold", zorder=6)
    # furlong markers (distance to go) on the round course and the straight mile
    fs = 7 if labels_big else 10
    for f in C["roundCourse"]["furlongPoles"]:
        (x, z), (ox, oz) = f["at"], f.get("outward", (0, 1))
        if not (X0 < x < X1 and Z0 < z < Z1):
            continue
        ix, iz = x - ox * 6, z - oz * 6                                # just inside the inside rail
        ax.plot(x, -z, "o", ms=4, color=COL["pole"], zorder=7)
        ax.text(ix - ox * 6, -(iz - oz * 6), "%df" % f["furlongs"], ha="center", va="center", fontsize=fs, color=COL["pole"], weight="bold", zorder=7)
    for f in C["straightMile"]["furlongPoles"]:
        x, z = f["at"]
        if f["furlongs"] <= 3 or not (X0 < x < X1):
            continue
        ax.plot(x, -z, "o", ms=4, color=COL["pole"], zorder=7)
        ax.text(x, 9, "%df" % f["furlongs"], ha="center", va="center", fontsize=fs, color=COL["pole"], weight="bold", zorder=7)
    for f in C["roundMileSpur"]["furlongPoles"]:
        x, z = f["at"]
        if X0 < x < X1 and Z0 < z < Z1:
            ax.plot(x, -z, "o", ms=4, color=COL["pole"], zorder=7)
            ax.text(x + 14, -z, "%df (chute)" % f["furlongs"], ha="left", va="center", fontsize=fs, color=COL["pole"], zorder=7)
    # where races start
    sx, sz = C["straightMile"]["stalls"]
    if X0 < sx < X1:
        ax.text(sx - 6, -(sz + W / 2), "Straight mile\nstalls (8f)", ha="right", va="center", fontsize=fs, color=COL["ink"], zorder=7)
    cx, cz = C["roundMileSpur"]["from"]
    if X0 < cx < X1 and Z0 < cz < Z1:
        ax.text(cx - 10, -cz, "Round-mile chute\nstart (8.2f)", ha="right", va="center", fontsize=fs, color=COL["ink"], zorder=7)
    # running direction
    for (ax0, az0), (ax1, az1) in [((330, 15), (230, 15)), ((719, -260), (709, -170)), ((360, -650), (430, -720)),
                                   ((40, -345), (90, -400)), ((1300, 15), (1200, 15))]:
        if X0 < ax0 < X1 and Z0 < az0 < Z1:
            ax.add_patch(FancyArrowPatch((ax0, -az0), (ax1, -az1), arrowstyle="-|>", mutation_scale=14, color=COL["soft"], lw=1.6, zorder=6))
    ax.tick_params(labelsize=8, colors=COL["soft"])
    ax.set_xticks(range(int(X0 // 200) * 200, int(X1) + 1, 200)); ax.set_yticks([-v for v in range(int(Z0 // 200) * 200, int(Z1) + 1, 200)])
    ax.set_yticklabels(["%d m %s" % (abs(v), "N" if v < 0 else "S" if v > 0 else "") for v in range(int(Z0 // 200) * 200, int(Z1) + 1, 200)])
    ax.set_xticklabels(["%d m" % v for v in range(int(X0 // 200) * 200, int(X1) + 1, 200)])
    for s in ax.spines.values():
        s.set_color(COL["soft"])


KEY = [("Camera position", "a dot where it stands, with its height (e.g. 'box, 25 m up')"),
       ("Coverage", "an arrow along the track from where it picks the race up to where it hands over"),
       ("Framing", "whole field / leading group / leader, or a TV grab number"),
       ("Grandstand shots", "where the camera is and what it should show of the stand"),
       ("TV grabs", "number each reference image and write its number by the camera")]


def page(pdf, png, title, sub, area, labels_big):
    fig = plt.figure(figsize=(16.54, 11.69), facecolor=COL["paper"])
    fig.text(0.035, 0.955, title, fontsize=20, weight="bold", color=COL["pole"], family="serif")
    fig.text(0.035, 0.93, sub, fontsize=10.5, color=COL["soft"])
    ax = fig.add_axes([0.035, 0.2, 0.93, 0.7])
    draw(ax, *area, labels_big)
    fig.text(0.035, 0.155, "How to mark it up", fontsize=12, weight="bold", color=COL["ink"])
    for i, (k, v) in enumerate(KEY):
        fig.text(0.035, 0.13 - i * 0.02, k + ":", fontsize=9.5, weight="bold", color=COL["ink"])
        fig.text(0.135, 0.13 - i * 0.02, v, fontsize=9.5, color=COL["soft"])
    fig.text(0.55, 0.155, "Cameras (your notes)", fontsize=12, weight="bold", color=COL["ink"])
    for i, name in enumerate(["1  Inside-rail tracking", "2  Grandstand camera box", "3  Side-on at the post", "4  Tight aerial",
                              "5  Grandstand shot", "6  Grandstand shot", "7"]):
        y = 0.13 - i * 0.017
        fig.text(0.55, y, name, fontsize=9.5, color=COL["ink"])
        fig.lines.append(plt.Line2D([0.72, 0.965], [y - 0.003, y - 0.003], transform=fig.transFigure, color=COL["soft"], lw=0.5))
    pdf.savefig(fig, facecolor=COL["paper"])
    fig.savefig(png, dpi=110, facecolor=COL["paper"])
    plt.close(fig)


if __name__ == "__main__":
    out = rp("reference/course/layout")
    with PdfPages(os.path.join(out, "ascot-camera-plan.pdf")) as pdf:
        page(pdf, os.path.join(out, "ascot-camera-plan.png"), "Thoroughbred · Ascot: camera plan",
             "The whole course to scale, north up, 100 m grid, metres from the winning post. Running is clockwise (arrows). "
             "Furlong markers are distance to go. Faint boxes are the site pieces; dark dots the planting belt.",
             (-260, 1680, -1010, 120), True)
        page(pdf, os.path.join(out, "ascot-camera-plan-straight.png"), "Thoroughbred · Ascot: camera plan, home straight",
             "The home straight, the stand and the turn in, enlarged (same grid). Mark the grandstand shots and the finish cameras here.",
             (-300, 760, -260, 150), False)
    print("wrote reference/course/layout/ascot-camera-plan.pdf, .png and -straight.png")
