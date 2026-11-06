"""A plan of the home straight, the stand and the inner carnival zone to sketch layouts on, with every
site component placed today drawn to scale and marked with its letter code.

    python3 tools/course/draw_site_plan.py

Reads  courses/ascot.json, courses/ascot-site-dressing.json, assets/models/architecture/site_props_codes.json
       (codes and footprints, from tools/blender/site_props_sheet.py)
Writes reference/course/layout/ascot-site-plan.png and .pdf (A3 landscape)

World axes as courses/ascot.json (x east, z south, metres from the winning post); drawn north up.
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle, FancyArrowPatch

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def rp(*p): return os.path.join(REPO, *p)

C = json.load(open(rp("courses/ascot.json")))
D = json.load(open(rp("courses/ascot-site-dressing.json")))
K = json.load(open(rp("assets/models/architecture/site_props_codes.json")))["codes"]
VIEW = json.load(open(rp("courses/ascot-view.json")))
CODE = {v["piece"]: k for k, v in K.items()}
W = C["trackWidth"]
X0, X1, Z0, Z1 = -200, 720, -235, 175          # the area drawn (world x, z)
COL = dict(grass="#b9cf93", infield="#c3d79f", track="#dfeab8", rail="#ffffff", plant="#2f5a2c", carn="#8fc2ea",
           gz="#7fd8e6", stand="#efe3c4", edge="#8a744a", ink="#1f2a1c", piece="#ffffff", pieceedge="#1f5a38",
           post="#e055c8", path="#d8c29a", grid="#ffffff")

fig = plt.figure(figsize=(16.54, 11.69))          # A3 landscape
ax = fig.add_axes([0.035, 0.2, 0.93, 0.7])
ax.set_xlim(X0, X1); ax.set_ylim(-Z1, -Z0)       # north up: plot y = -z
ax.set_aspect("equal")
ax.set_facecolor(COL["grass"])
P = lambda pts: np.array([[x, -z] for x, z in pts])

# infield (inside the inside rail) a touch lighter, then the turf
rings = C["track"]["surface"]
for hole in rings[1:]:
    ax.add_patch(MplPoly(P(hole), closed=True, fc=COL["infield"], ec="none", zorder=1))
ax.add_patch(MplPoly(P(rings[0]), closed=True, fc=COL["track"], ec="none", zorder=2))
for hole in rings[1:]:
    ax.add_patch(MplPoly(P(hole), closed=True, fc=COL["infield"], ec="none", zorder=2))
for line in C["rails"]["lines"]:
    a = P(line); ax.plot(a[:, 0], a[:, 1], color=COL["rail"], lw=1.1, zorder=3)
# zones
cz = P(C["zones"]["carnival"]["polygon"])
ax.add_patch(MplPoly(cz, closed=True, fc=COL["carn"], ec="#3f7fbf", lw=1.2, alpha=0.35, zorder=2.5, hatch="//"))
g = C["zones"]["grandstand"]
ax.add_patch(Rectangle((g["from"], -g["farEdge"]), g["to"] - g["from"], g["farEdge"] - g["nearEdge"], fc="none", ec="#2aa5b8", lw=1.2, ls="--", zorder=2.6))
for poly in C["zones"]["planting"]["polygons"]:
    ax.add_patch(MplPoly(P(poly), closed=True, fc=COL["plant"], ec="none", zorder=2.7))
# paths
for p in VIEW.get("paths", []):
    (ax_, az), (bx, bz) = p["from"], p["to"]
    ax.plot([ax_, bx], [-az, -bz], color=COL["path"], lw=p["width"] * 0.62, solid_capstyle="butt", zorder=2.8)
# the stand, module by module
for m in C["grandstand"]["modules"]:
    ax.add_patch(Rectangle((m["xWest"], -m["back"]), m["xEast"] - m["xWest"], m["back"] - m["front"], fc=COL["stand"], ec=COL["edge"], lw=0.6, zorder=4))
tx, tz = C["grandstand"]["towerAt"]
ax.add_patch(Rectangle((tx - 4, -(tz + 10)), 8, 8, fc="#d8c79c", ec=COL["edge"], lw=0.8, zorder=4.1))
ax.text(tx, -(tz + 22), "Clock tower", ha="center", va="center", fontsize=8, color=COL["ink"], zorder=6)
ax.text(150, -(tz + 9), "Main stand (507 m)", ha="center", va="center", fontsize=10, color=COL["ink"], zorder=6)
# winning post and furlong poles
ax.plot([0, 0], [0.5, -W - 0.5], color=COL["post"], lw=3, zorder=5)
ax.text(-3, -(W + 7), "Winning post", ha="right", va="top", fontsize=9, color="#a0308f", fontweight="bold", zorder=6)
for f in C["straightMile"]["furlongPoles"]:
    x = f["at"][0]
    if X0 < x < X1:
        ax.plot([x, x], [0.5, 4.5], color="#c0392b", lw=2, zorder=5)
        ax.text(x, 6, "%df" % f["furlongs"], ha="center", va="bottom", fontsize=8.5, color="#c0392b", zorder=6)
# running direction
for x in (560, 320):
    ax.add_patch(FancyArrowPatch((x, -W / 2), (x - 60, -W / 2), arrowstyle="-|>", mutation_scale=14, color="#5b7a3a", lw=1.4, zorder=5))
ax.text(660, -W / 2, "home straight: horses run this way", ha="center", va="center", fontsize=8.5, color="#3f5a28", zorder=6)

# the site components placed today, to scale, with their letter
for p in D["pieces"]:
    code = CODE.get(p["piece"])
    if code is None:
        continue
    fp = K[code]["footprint"]
    th = math.pi + math.radians(p.get("turn", 0))     # the viewer's turn about y
    c, s = math.cos(th), math.sin(th)
    corners = []
    for lx, lz in ((fp["x0"], fp["z0"]), (fp["x1"], fp["z0"]), (fp["x1"], fp["z1"]), (fp["x0"], fp["z1"])):
        wx = p["x"] + lx * c + lz * s
        wz = p["z"] - lx * s + lz * c
        corners.append((wx, -wz))
    ax.add_patch(MplPoly(corners, closed=True, fc=COL["piece"], ec=COL["pieceedge"], lw=0.7, zorder=7))
    small = K[code]["width"] < 4 and K[code]["depth"] < 4
    cx = np.mean([q[0] for q in corners]); cy = np.mean([q[1] for q in corners])
    ax.text(cx, cy, code, ha="center", va="center", fontsize=6 if small else 9, fontweight="bold", color=COL["pieceedge"], zorder=8)
# zone labels
ax.text(380, -(-95), "INNER CARNIVAL ZONE\n(blue: tents, terraces, bandstands as a backdrop)", ha="center", va="center", fontsize=11, color="#2a5f8f", fontweight="bold", zorder=6)
ax.text(560, -(g["farEdge"] - 12), "Grandstand zone (dashed): crowd, marquees, planting", ha="center", va="center", fontsize=9, color="#1f7f8f", zorder=6)
ax.annotate("Planting belt (hedge + trees,\nboards in front)", xy=(-140, -20), xytext=(-185, -125), fontsize=8.5, color=COL["ink"],
            arrowprops=dict(arrowstyle="-", color=COL["ink"], lw=0.8), zorder=9)
ax.text(465, -(92), "Enclosures east of the stand", ha="center", va="center", fontsize=8.5, color=COL["ink"], zorder=6)
ax.text(45, 62, "Far-side enclosure", ha="center", va="center", fontsize=8.5, color=COL["ink"], zorder=6)

# grid: 25 m light, 100 m stronger and labelled
for x in range(-200, 721, 25):
    ax.axvline(x, color=COL["grid"], lw=0.9 if x % 100 == 0 else 0.35, alpha=0.75 if x % 100 == 0 else 0.5, zorder=3.5)
for z in range(-225, 176, 25):
    ax.axhline(-z, color=COL["grid"], lw=0.9 if z % 100 == 0 else 0.35, alpha=0.75 if z % 100 == 0 else 0.5, zorder=3.5)
ax.set_xticks(range(-200, 721, 100))
ax.set_xticklabels(["%d m" % x for x in range(-200, 721, 100)], fontsize=8)
ax.set_yticks([-z for z in range(-200, 176, 100)])
ax.set_yticklabels(["%d m %s" % (abs(z), "N" if z < 0 else "S" if z > 0 else "") for z in range(-200, 176, 100)], fontsize=8)
ax.tick_params(length=3, colors="#4f5d4a")
for sp in ax.spines.values():
    sp.set_color("#8a744a")
# north arrow and scale bar
ax.add_patch(FancyArrowPatch((700, -(-150)), (700, -(-205)), arrowstyle="-|>", mutation_scale=18, color=COL["ink"], lw=1.6, zorder=9))
ax.text(700, 212, "N", ha="center", va="bottom", fontsize=12, fontweight="bold", color=COL["ink"], zorder=9)
ax.add_patch(Rectangle((-185, -160), 100, 3.5, fc=COL["ink"], zorder=9))
ax.add_patch(Rectangle((-185, -160), 50, 3.5, fc="#ffffff", ec=COL["ink"], lw=0.6, zorder=9))
ax.text(-135, -166, "0         50       100 m  (grid: 25 m)", ha="center", va="top", fontsize=8, color=COL["ink"], zorder=9)

fig.text(0.035, 0.955, "Thoroughbred · Ascot home straight: site plan for sketching", fontsize=20, color="#1f5a38", fontweight="bold", family="serif")
fig.text(0.035, 0.925, "Drawn to scale, north up, metres from the winning post (on the inside rail). White shapes are the site components placed today, "
         "marked with their letter (see the components sheet).", fontsize=10.5, color="#4f5d4a")
fig.text(0.035, 0.906, "To plan: write a component's letter where you want it (an arrow for which way it faces), cross out any to remove, and give any new kind "
         "of piece a new letter (X, Y, Z...) with a quick note or sketch.", fontsize=10.5, color="#4f5d4a")
# legend of codes
keys = sorted(K)
cols = 4
per = math.ceil(len(keys) / cols)
for i, k in enumerate(keys):
    col, row = divmod(i, per)
    fig.text(0.04 + col * 0.235, 0.165 - row * 0.022, "%s   %s  (%g × %g m)" % (k, K[k]["name"], K[k]["width"], K[k]["depth"]),
             fontsize=9.5, color=COL["ink"], family="monospace" if False else None)
fig.text(0.04, 0.188, "Codes", fontsize=11, fontweight="bold", color="#1f5a38")
fig.patch.set_facecolor("#f4ead2")
os.makedirs(rp("reference/course/layout"), exist_ok=True)
fig.savefig(rp("reference/course/layout/ascot-site-plan.png"), dpi=200, facecolor=fig.get_facecolor())
fig.savefig(rp("reference/course/layout/ascot-site-plan.pdf"), facecolor=fig.get_facecolor())
print("wrote reference/course/layout/ascot-site-plan.png and .pdf")
