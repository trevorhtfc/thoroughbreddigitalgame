"""Ascot's tree map: every tree and shrub the race view draws, coloured by what it is there for, with each loose-tree
area outlined, numbered and counted, and the furlong marks of the round course and the straight mile.

    python3 tools/course/draw_tree_map.py

Writes reference/course/layout/ascot-tree-map.png / .pdf (A3 landscape). Shares the tree placement with
tools/course/draw_site_plan.py (the race view's own seeded placement).
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle, Circle
from matplotlib.collections import PatchCollection

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "draw_site_plan.py")).read().split("# ------------------------------------------------------------------ sheet 1")[0]
g = {"__file__": os.path.join(HERE, "draw_site_plan.py")}
exec(src, g)
C, D, VIEW, PLANT, FEST, rp = g["C"], g["D"], g["VIEW"], g["PLANT"], g["FEST"], g["rp"]
LOOSE = g["LOOSE"]

X0, X1, Z0, Z1 = -560, 1700, -1060, 300
fig = plt.figure(figsize=(16.54, 11.69))
ax = fig.add_axes([0.03, 0.06, 0.94, 0.83])
ax.set_xlim(X0, X1); ax.set_ylim(-Z1, -Z0); ax.set_aspect("equal"); ax.set_facecolor("#dfe8c8")
P = lambda pts: np.array([[x, -z] for x, z in pts])
SURF = C["track"]["surface"]
ax.add_patch(MplPoly(P(SURF[0]), closed=True, fc="#f3f1dc", ec="#b7b08a", lw=0.5, zorder=2))
for h in SURF[1:]:
    ax.add_patch(MplPoly(P(h), closed=True, fc="#e6eed2", ec="#b7b08a", lw=0.5, zorder=2))
for m in C["grandstand"]["modules"]:
    ax.add_patch(Rectangle((m["xWest"], -m["back"]), m["xEast"] - m["xWest"], m["back"] - m["front"], fc="#d9c9a0", ec="none", zorder=3))
for p in D["pieces"]:
    if g["CODE"].get(p["piece"]):
        _, corners = g["piece_corners"](p)
        ax.add_patch(MplPoly(corners, closed=True, fc="#ffffff", ec="#9a9a8a", lw=0.2, zorder=3))
ax.plot([0, 0], [0.5, -30.5], color="#e055c8", lw=2, zorder=4)

# the trees, by what they are for
CAT = [("Perimeter planting belts (kept: the tracking cameras' backdrop)", "#2f6a2c", [(t[0], t[1], t[3]) for t in PLANT["trees"]])]
AREA_COL = ["#c0712f", "#8e5bb0", "#2f7fa8", "#b8434e", "#a07d1e", "#4f8a8b", "#7a6a3a"]
groups = []
for k, a in enumerate(VIEW["trees"]):
    x0, x1 = sorted((a["area"][0], a["area"][2])); z0, z1 = sorted((a["area"][1], a["area"][3]))
    pts = [(x, z, s) for x, z, s in LOOSE if x0 - 8 <= x <= x1 + 8 and z0 - 8 <= z <= z1 + 8]
    groups.append((k + 1, a, (x0, x1, z0, z1), pts))
for kind, col, pts in CAT:
    ax.add_collection(PatchCollection([Circle((x, -z), 5.6 * s) for x, z, s in pts], fc=col, ec="none", alpha=0.95, zorder=5))
for n, a, (x0, x1, z0, z1), pts in groups:
    col = AREA_COL[(n - 1) % len(AREA_COL)]
    ax.add_collection(PatchCollection([Circle((x, -z), 5.6 * s) for x, z, s in pts], fc=col, ec="none", alpha=0.75, zorder=5))
    ax.add_patch(Rectangle((x0, -z1), x1 - x0, z1 - z0, fc="none", ec=col, lw=1.4, ls="--", zorder=6))
    ax.text((x0 + x1) / 2, -(z0 + z1) / 2, "%d" % n, ha="center", va="center", fontsize=15, fontweight="bold", color="white", zorder=8,
            bbox=dict(boxstyle="circle,pad=0.3", fc=col, ec="white", lw=1.2))
ax.add_collection(PatchCollection([Circle((t[0], -t[1]), 5.6 * t[3]) for t in FEST["trees"]], fc="#8cc95c", ec="#4f8a3a", lw=0.2, zorder=5.5))
ax.add_collection(PatchCollection([Circle((t[0], -t[1]), 2.6 * t[3]) for t in FEST["shrubs"]], fc="#3e6e30", ec="none", zorder=5.4))

# furlong marks: the straight mile (the 'Xf' along the bottom of the straight) and the round course
for f in C["straightMile"]["furlongPoles"]:
    x, z = f["at"]
    ax.plot([x, x], [-z + 4, -z - 34], color="#c0392b", lw=1.6, zorder=7)
    ax.text(x, -z - 46, "%df" % f["furlongs"], ha="center", va="top", fontsize=10, fontweight="bold", color="#c0392b", zorder=9,
            bbox=dict(boxstyle="round,pad=0.15", fc="#fffaf0", ec="none", alpha=0.85))
ax.text(1450, -16, "straight mile", fontsize=8, color="#7a2a20", style="italic", zorder=9)
for f in C["roundCourse"]["furlongPoles"]:
    x, z = f["at"]
    ax.plot(x, -z, "o", ms=3, color="#7a2a7a", zorder=7)
    ax.text(x + 10, -z + 10, "%dfR" % f["furlongs"], fontsize=7, color="#7a2a7a", zorder=9)
lab = dict(fontsize=8.5, color="#1f2a1c", zorder=10, bbox=dict(boxstyle="round,pad=0.3", fc="#fffaf0", ec="none", alpha=0.9))
ax.text(150, -112, "Main stand", ha="center", **lab)
ax.text(300, 90, "Festival side: small trees and low planting only", ha="center", **lab)
ax.text(330, 420, "Infield: small clumps and low planting, no tall trees", ha="center", **lab)
ax.text(905, -190, "Open ground south of the straight mile,\naround 4f: no belt here (the blank patch)", ha="center", fontsize=9, color="#b8434e", fontweight="bold", zorder=10,
        bbox=dict(boxstyle="round,pad=0.35", fc="#fff3f3", ec="#b8434e", lw=1.2))
ax.add_patch(Rectangle((690, -120), 360, 92, fc="#b8434e", ec="#b8434e", alpha=0.12, lw=1.4, ls=":", zorder=4.5))
for x in range(-500, 1701, 100):
    ax.axvline(x, color="white", lw=0.4, alpha=0.6, zorder=2.5)
for z in range(-1000, 301, 100):
    ax.axhline(-z, color="white", lw=0.4, alpha=0.6, zorder=2.5)
ax.set_xticks(range(-500, 1701, 500)); ax.set_xticklabels(["%d m" % x for x in range(-500, 1701, 500)], fontsize=8)
ax.set_yticks([-z for z in range(-1000, 301, 500)])
ax.set_yticklabels(["%d m %s" % (abs(z), "N" if z < 0 else "S" if z > 0 else "") for z in range(-1000, 301, 500)], fontsize=8)
ax.add_patch(Rectangle((-520, -280), 200, 8, fc="#1f2a1c", zorder=11)); ax.add_patch(Rectangle((-520, -280), 100, 8, fc="#fff", ec="#1f2a1c", lw=0.6, zorder=11))
ax.text(-420, -292, "0      100     200 m", ha="center", va="top", fontsize=8, zorder=11)

fig.text(0.03, 0.955, "Thoroughbred · Ascot: indicative tree map", fontsize=20, color="#1f5a38", fontweight="bold", family="serif")
fig.text(0.03, 0.932, "11 Nov 2026, as the race view places them today. North up. Dark green: the perimeter planting belts (%d trees). "
         "Numbered boxes: the loose backdrop blocks. Light green: the festival's small trees (%d); dark dots: low planting (%d shrubs)."
         % (len(PLANT["trees"]), len(FEST["trees"]), len(FEST["shrubs"])), fontsize=9.5, color="#4f5d4a")
NAMES = {1: "behind the stand", 2: "round the enclosures east of the stand", 3: "behind the enclosure past the post",
         4: "beyond the far turn, west", 5: "south of the straight mile, 3f to 7f out", 6: "north of the straight mile, right of the round mile start",
         7: "outside the home bend, next to block 6"}
items = ["%d  %s (%d)" % (n, NAMES.get(n, a["note"][:40]), len(pts)) for n, a, _, pts in groups]
fig.text(0.03, 0.912, "   ".join(items[:4]), fontsize=8.6, color="#1f2a1c")
fig.text(0.03, 0.896, "   ".join(items[4:]), fontsize=8.6, color="#1f2a1c")
fig.patch.set_facecolor("#f4ead2")
fig.savefig(rp("reference/course/layout/ascot-tree-map.png"), dpi=200, facecolor=fig.get_facecolor())
fig.savefig(rp("reference/course/layout/ascot-tree-map.pdf"), facecolor=fig.get_facecolor())
for n, a, box, pts in groups:
    print(n, len(pts), box, a["note"][:70])
