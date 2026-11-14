"""Ascot's site plans, to scale, for sketching layout changes on.

    python3 tools/course/draw_site_plan.py

Writes (A3 landscape, PNG and PDF):
  reference/course/layout/ascot-site-plan.png / .pdf          the home straight and the festival side in detail: every
                                                              site component with its letter, the stand, the trees, the
                                                              low planting, the bunting, the crowd areas, the paths
  reference/course/layout/ascot-site-plan-course.png / .pdf   the whole course: zones, planting belts, trees, the stand

Reads courses/ascot.json, ascot-site-dressing.json, ascot-view.json (paths, loose-tree areas, the festival's planting and
bunting), ascot-planting.json (the belts' trees) and assets/models/architecture/site_props_codes.json (letters and sizes).
The loose trees are placed exactly as the race view places them (final-furlong.html placeTrees: same seeded random).
World axes as courses/ascot.json (x east, z south, metres from the winning post); drawn north up.
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle, FancyArrowPatch, Circle
from matplotlib.collections import PatchCollection
from matplotlib.path import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def rp(*p): return os.path.join(REPO, *p)

C = json.load(open(rp("courses/ascot.json")))
D = json.load(open(rp("courses/ascot-site-dressing.json")))
K = json.load(open(rp("assets/models/architecture/site_props_codes.json")))["codes"]
VIEW = json.load(open(rp("courses/ascot-view.json")))
PLANT = json.load(open(rp("courses/ascot-planting.json")))
FEST = VIEW.get("festival", {"trees": [], "shrubs": [], "bunting": []})
CODE = {v["piece"]: k for k, v in K.items()}
W = C["trackWidth"]
COL = dict(grass="#c6d6a0", infield="#cfdeab", track="#e3ecbf", rail="#ffffff", plant="#3b6a34", carn="#8fc2ea",
           stand="#efe3c4", edge="#8a744a", ink="#1f2a1c", piece="#ffffff", pieceedge="#1f5a38", post="#e055c8",
           path="#dcc79f", grid="#ffffff", tree="#5f9a48", treeedge="#3c6a2e", small="#8cbf62", smalledge="#4f8a3a",
           shrub="#4e7f3a", crowd="#d9a35b", bunting="#d0507a", balloon="#e889a9")
SURF = C["track"]["surface"]
surf_out, holes = Path(SURF[0]), [Path(h) for h in SURF[1:]]
on_track = lambda x, z: surf_out.contains_point((x, z)) and not any(h.contains_point((x, z)) for h in holes)


def dist_rails(x, z):
    best = 1e9
    for line in C["rails"]["lines"]:
        a = np.array(line)
        d = a[1:] - a[:-1]
        L2 = (d ** 2).sum(1); L2[L2 == 0] = 1
        t = np.clip(((x - a[:-1, 0]) * d[:, 0] + (z - a[:-1, 1]) * d[:, 1]) / L2, 0, 1)
        best = min(best, float(np.min(np.hypot(x - a[:-1, 0] - t * d[:, 0], z - a[:-1, 1] - t * d[:, 1]))))
    return best


def loose_trees():
    """final-furlong.html placeTrees(): the same seeded random walk over VIEW.trees areas."""
    s = [11]
    def rnd():
        s[0] = (s[0] * 1664525 + 1013904223) & 0xFFFFFFFF
        return s[0] / 4294967296
    CL = VIEW["clearOf"]; S = CL["stand"]
    pieces = D["pieces"]
    def clear(x, z, track):
        return (S[0] < x < S[2] and S[1] < z < S[3]) or on_track(x, z) or dist_rails(x, z) < track \
            or any(abs(p["x"] - x) < CL["pieces"] and abs(p["z"] - z) < CL["pieces"] for p in pieces)
    spots = []
    for a in VIEW["trees"]:
        x0, x1 = sorted((a["area"][0], a["area"][2])); z0, z1 = sorted((a["area"][1], a["area"][3]))
        z = z0
        while z < z1:
            x = x0 + rnd() * a["spacing"]
            while x < x1:
                if rnd() < a.get("skip", 0):
                    x += a["spacing"] * (0.7 + rnd() * 0.6); continue
                n = a["clump"][0] + int(rnd() * (a["clump"][1] - a["clump"][0] + 1)) if "clump" in a else 1
                for _ in range(n):
                    tx = x + (rnd() - 0.5) * (14 if n > 1 else a["spacing"] * 0.6)
                    tz = z + (rnd() - 0.5) * (10 if n > 1 else a["spacing"] * 0.6)
                    if not clear(tx, tz, a.get("trackClear", CL["track"])):
                        spots.append((tx, tz, a["scale"][0] + rnd() * (a["scale"][1] - a["scale"][0])))
                x += a["spacing"] * (0.7 + rnd() * 0.6)
            z += a["spacing"]
    return spots


LOOSE = loose_trees()
print("loose trees", len(LOOSE))


def piece_corners(p):
    code = CODE.get(p["piece"]); fp = K[code]["footprint"]
    th = math.pi + math.radians(p.get("turn", 0)); c, s = math.cos(th), math.sin(th)
    return code, [(p["x"] + lx * c + lz * s, -(p["z"] - lx * s + lz * c)) for lx, lz in
                  ((fp["x0"], fp["z0"]), (fp["x1"], fp["z0"]), (fp["x1"], fp["z1"]), (fp["x0"], fp["z1"]))]


def base(ax, X0, X1, Z0, Z1, detail):
    ax.set_xlim(X0, X1); ax.set_ylim(-Z1, -Z0); ax.set_aspect("equal"); ax.set_facecolor(COL["grass"])
    P = lambda pts: np.array([[x, -z] for x, z in pts])
    ax.add_patch(MplPoly(P(SURF[0]), closed=True, fc=COL["track"], ec="none", zorder=2))
    for h in SURF[1:]:
        ax.add_patch(MplPoly(P(h), closed=True, fc=COL["infield"], ec="none", zorder=2))
    for line in C["rails"]["lines"]:
        a = P(line); ax.plot(a[:, 0], a[:, 1], color=COL["rail"], lw=1.1 if detail else 0.7, zorder=3)
    for poly in C["zones"]["planting"]["polygons"]:
        ax.add_patch(MplPoly(P(poly), closed=True, fc=COL["plant"], ec="none", zorder=2.7))
    for p in VIEW.get("paths", []):
        (a0, b0), (a1, b1) = p["from"], p["to"]
        ax.plot([a0, a1], [-b0, -b1], color=COL["path"], lw=p["width"] * (0.62 if detail else 0.25), solid_capstyle="butt", zorder=2.8)
    for m in C["grandstand"]["modules"]:
        ax.add_patch(Rectangle((m["xWest"], -m["back"]), m["xEast"] - m["xWest"], m["back"] - m["front"], fc=COL["stand"], ec=COL["edge"], lw=0.6 if detail else 0.3, zorder=4))
    ax.plot([0, 0], [0.5, -W - 0.5], color=COL["post"], lw=3 if detail else 2, zorder=5)


def trees_layer(ax, X0, X1, Z0, Z1, detail):
    inside = lambda x, z, m=20: X0 - m < x < X1 + m and Z0 - m < z < Z1 + m
    big = [Circle((x, -z), 5.6 * s) for x, z, s in LOOSE if inside(x, z)]
    big += [Circle((t[0], -t[1]), 5.6 * t[3]) for t in PLANT["trees"] if inside(t[0], t[1])]
    ax.add_collection(PatchCollection(big, fc=COL["tree"], ec=COL["treeedge"], lw=0.4 if detail else 0.15, alpha=0.9, zorder=6))
    small = [Circle((t[0], -t[1]), 5.6 * t[3]) for t in FEST["trees"] if inside(t[0], t[1])]
    ax.add_collection(PatchCollection(small, fc=COL["small"], ec=COL["smalledge"], lw=0.4 if detail else 0.15, zorder=6.1))
    sh = [Circle((t[0], -t[1]), 2.6 * t[3]) for t in FEST["shrubs"] if inside(t[0], t[1])]
    ax.add_collection(PatchCollection(sh, fc=COL["shrub"], ec="none", zorder=6.05))


# ------------------------------------------------------------------ sheet 1: the home straight and the festival
X0, X1, Z0, Z1 = -210, 730, -245, 140
fig = plt.figure(figsize=(16.54, 11.69))
ax = fig.add_axes([0.035, 0.19, 0.93, 0.71])
base(ax, X0, X1, Z0, Z1, True)
for c in D.get("crowds", []):                     # crowd areas, shaded by how packed they are
    (a0, a1), (b0, b1) = c["x"], c["z"]
    ax.add_patch(Rectangle((a0, -b1), a1 - a0, b1 - b0, fc=COL["crowd"], ec="none", alpha=min(0.55, 0.12 + 0.3 * c["density"]), zorder=2.9))
trees_layer(ax, X0, X1, Z0, Z1, True)
for p in D["pieces"]:
    if CODE.get(p["piece"]) is None:
        continue
    code, corners = piece_corners(p)
    fc = COL["balloon"] if code == "X" else COL["piece"]
    ax.add_patch(MplPoly(corners, closed=True, fc=fc, ec=COL["pieceedge"], lw=0.7, zorder=7))
    small = K[code]["width"] < 4 and K[code]["depth"] < 4
    cx = np.mean([q[0] for q in corners]); cy = np.mean([q[1] for q in corners])
    ax.text(cx, cy, code, ha="center", va="center", fontsize=5.5 if small else 8.5, fontweight="bold", color=COL["pieceedge"], zorder=8)
for r in FEST["bunting"]:                          # bunting: a zig-zag of little pennants
    a = np.array([[x, -z] for x, z in r["pts"]])
    ax.plot(a[:, 0], a[:, 1], color=COL["bunting"], lw=1.0, ls=(0, (1.2, 0.9)), zorder=7.5)
    if r.get("pole", True):
        ax.scatter(a[:, 0], a[:, 1], s=3, color="#7a3a50", zorder=7.6)
tx, tz = C["grandstand"]["towerAt"]
ax.text(tx, -(tz + 24), "Clock tower", ha="center", va="center", fontsize=8, color=COL["ink"], zorder=9)
ax.text(150, -(tz + 9), "Main stand (507 m)", ha="center", va="center", fontsize=10, color=COL["ink"], zorder=9)
ax.text(-3, -(W + 7), "Winning post", ha="right", va="top", fontsize=9, color="#a0308f", fontweight="bold", zorder=9)
for f in C["straightMile"]["furlongPoles"]:
    x = f["at"][0]
    if X0 < x < X1:
        ax.plot([x, x], [0.5, 4.5], color="#c0392b", lw=2, zorder=5)
        ax.text(x, 6, "%df" % f["furlongs"], ha="center", va="bottom", fontsize=8.5, color="#c0392b", fontweight="bold", zorder=9)
for x in (560, 320):
    ax.add_patch(FancyArrowPatch((x, -W / 2), (x - 60, -W / 2), arrowstyle="-|>", mutation_scale=14, color="#5b7a3a", lw=1.4, zorder=5))
ax.text(660, -W / 2, "home straight: horses run this way", ha="center", va="center", fontsize=8.5, color="#3f5a28", zorder=6)
lab = dict(fontsize=8.5, color=COL["ink"], zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#fbf6e8", ec="none", alpha=0.85))
ax.text(404, -16, "Balloon dining pods (X) at 2f", ha="center", va="center", **lab)
ax.annotate("Big pavilions (A, B, C) in a line:\nthe festival's back edge", xy=(250, 52), xytext=(250, 115), ha="center", arrowprops=dict(arrowstyle="-", lw=0.8), **lab)
ax.annotate("Low planting and clumps of\nsmall trees behind the pavilions", xy=(430, 80), xytext=(470, 160), ha="center", arrowprops=dict(arrowstyle="-", lw=0.8), **lab)
ax.annotate("Garden: terrace decks, pergolas,\nkiosks, small trees, beds by the path", xy=(160, 34), xytext=(95, 100), ha="center", arrowprops=dict(arrowstyle="-", lw=0.8), **lab)
ax.annotate("Bunting zig-zags over the path", xy=(560, 24), xytext=(600, 90), ha="center", arrowprops=dict(arrowstyle="-", lw=0.8), **lab)
ax.text(140, 215, "Infield beyond: open lawn with scattered small clumps and low planting only (no tall trees)", ha="center", va="center", **lab)
ax.text(530, -112, "Enclosures east of the stand", ha="center", va="center", **lab)
ax.text(-160, -98, "Past the post", ha="center", va="center", **lab)
for x in range(-200, 731, 25):
    ax.axvline(x, color=COL["grid"], lw=0.9 if x % 100 == 0 else 0.35, alpha=0.6 if x % 100 == 0 else 0.4, zorder=3.5)
for z in range(-225, 141, 25):
    ax.axhline(-z, color=COL["grid"], lw=0.9 if z % 100 == 0 else 0.35, alpha=0.6 if z % 100 == 0 else 0.4, zorder=3.5)
ax.set_xticks(range(-200, 731, 100)); ax.set_xticklabels(["%d m" % x for x in range(-200, 731, 100)], fontsize=8)
ax.set_yticks([-z for z in range(-200, 141, 100)])
ax.set_yticklabels(["%d m %s" % (abs(z), "N" if z < 0 else "S" if z > 0 else "") for z in range(-200, 141, 100)], fontsize=8)
ax.tick_params(length=3, colors="#4f5d4a")
for sp in ax.spines.values(): sp.set_color("#8a744a")
ax.add_patch(FancyArrowPatch((705, 180), (705, 230), arrowstyle="-|>", mutation_scale=18, color=COL["ink"], lw=1.6, zorder=11))
ax.text(705, 234, "N", ha="center", va="bottom", fontsize=12, fontweight="bold", color=COL["ink"], zorder=11)
ax.add_patch(Rectangle((-195, -128), 100, 3.5, fc=COL["ink"], zorder=11))
ax.add_patch(Rectangle((-195, -128), 50, 3.5, fc="#ffffff", ec=COL["ink"], lw=0.6, zorder=11))
ax.text(-145, -134, "0        50       100 m  (grid 25 m)", ha="center", va="top", fontsize=8, color=COL["ink"], zorder=11)
fig.text(0.035, 0.955, "Thoroughbred · Ascot: the home straight and the festival side", fontsize=20, color="#1f5a38", fontweight="bold", family="serif")
fig.text(0.035, 0.912, "Site plan, 11 Nov 2026. To scale, north up, metres from the winning post (on the inside rail). White shapes: the site pieces with their letters; "
         "pink X: balloon dining pods.\nDark green: tall trees (outside the course) and planting belts; light green: small trees; dark dots: low planting; "
         "dashed pink: bunting; orange tint: crowd (darker = more packed).", fontsize=9.5, color="#4f5d4a", wrap=True)
fig.text(0.035, 0.885, "To mark up: write a letter where you want a piece (arrow for which way it faces), cross out any to remove, circle areas to plant or clear.",
         fontsize=9.5, color="#4f5d4a")
keys = sorted(K)
cols = 4; per = math.ceil(len(keys) / cols)
for i, k in enumerate(keys):
    col, row = divmod(i, per)
    fig.text(0.04 + col * 0.235, 0.155 - row * 0.021, "%s   %s  (%g × %g m, %g m high)" % (k, K[k]["name"], K[k]["width"], K[k]["depth"], K[k]["height"]),
             fontsize=9, color=COL["ink"])
fig.text(0.04, 0.177, "Codes", fontsize=11, fontweight="bold", color="#1f5a38")
fig.patch.set_facecolor("#f4ead2")
os.makedirs(rp("reference/course/layout"), exist_ok=True)
fig.savefig(rp("reference/course/layout/ascot-site-plan.png"), dpi=200, facecolor=fig.get_facecolor())
fig.savefig(rp("reference/course/layout/ascot-site-plan.pdf"), facecolor=fig.get_facecolor())
plt.close(fig)

# ------------------------------------------------------------------ sheet 2: the whole course
X0, X1, Z0, Z1 = -560, 1680, -1060, 260
fig = plt.figure(figsize=(16.54, 11.69))
ax = fig.add_axes([0.035, 0.07, 0.93, 0.82])
base(ax, X0, X1, Z0, Z1, False)
trees_layer(ax, X0, X1, Z0, Z1, False)
for p in D["pieces"]:
    if CODE.get(p["piece"]) is None:
        continue
    code, corners = piece_corners(p)
    ax.add_patch(MplPoly(corners, closed=True, fc=COL["balloon"] if code == "X" else COL["piece"], ec=COL["pieceedge"], lw=0.25, zorder=7))
for f in C["roundCourse"]["furlongPoles"]:
    x, z = f["at"] if "at" in f else (None, None)
    if x is not None:
        ax.plot(x, -z, "o", ms=2.5, color="#c0392b", zorder=8)
        ax.text(x, -z + 14, "%sf" % f.get("furlongs", ""), fontsize=7, color="#c0392b", ha="center", zorder=9)
lab2 = dict(fontsize=9, color=COL["ink"], zorder=10, bbox=dict(boxstyle="round,pad=0.3", fc="#fbf6e8", ec="none", alpha=0.85))
ax.text(260, 95, "Festival side (sheet 1)", ha="center", **lab2)
ax.text(330, 420, "Infield: open lawn, small clumps\nand low planting, no tall trees", ha="center", **lab2)
ax.text(150, -120, "Main stand", ha="center", **lab2)
ax.text(1250, -45, "Straight mile", ha="center", **lab2)
ax.text(-3, 20, "Post", ha="right", fontsize=8, color="#a0308f", fontweight="bold", zorder=10)
for x in range(-500, 1681, 100):
    ax.axvline(x, color=COL["grid"], lw=0.5, alpha=0.45, zorder=3.5)
for z in range(-1000, 261, 100):
    ax.axhline(-z, color=COL["grid"], lw=0.5, alpha=0.45, zorder=3.5)
ax.set_xticks(range(-500, 1681, 500)); ax.set_xticklabels(["%d m" % x for x in range(-500, 1681, 500)], fontsize=8)
ax.set_yticks([-z for z in range(-1000, 261, 500)]); ax.set_yticklabels(["%d m %s" % (abs(z), "N" if z < 0 else "S" if z > 0 else "") for z in range(-1000, 261, 500)], fontsize=8)
for sp in ax.spines.values(): sp.set_color("#8a744a")
ax.add_patch(Rectangle((-520, -230), 200, 8, fc=COL["ink"], zorder=11)); ax.add_patch(Rectangle((-520, -230), 100, 8, fc="#fff", ec=COL["ink"], lw=0.6, zorder=11))
ax.text(-420, -245, "0      100     200 m  (grid 100 m)", ha="center", va="top", fontsize=8, zorder=11)
fig.text(0.035, 0.955, "Thoroughbred · Ascot: the whole course", fontsize=20, color="#1f5a38", fontweight="bold", family="serif")
fig.text(0.035, 0.925, "Site plan, 11 Nov 2026. North up. Dark green: planting belts and tall trees (all outside the course); light green: small trees; "
         "white: site pieces; pink: balloon pods. The round course runs clockwise into the home straight.", fontsize=9.5, color="#4f5d4a")
fig.patch.set_facecolor("#f4ead2")
fig.savefig(rp("reference/course/layout/ascot-site-plan-course.png"), dpi=200, facecolor=fig.get_facecolor())
fig.savefig(rp("reference/course/layout/ascot-site-plan-course.pdf"), facecolor=fig.get_facecolor())
print("wrote reference/course/layout/ascot-site-plan(.png/.pdf) and ascot-site-plan-course(.png/.pdf)")
