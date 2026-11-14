"""The July Course's site plans, to scale, for reviewing and marking up the layout (11 Nov 2026).

    python3 tools/course/newmarket/draw_july_site_plan.py

Drawn from what the race view actually places (race-view/assets/course/newmarket-july*.json, written by
to_race_view.py), so the plan shows the course as it races today: the buildings, the site pieces with their letters,
every tree, the boards, the boundary walls, the Dyke, the crowd and the cameras. Names come from
courses/newmarket-july-draft.json.

Writes (A3 landscape, PNG and PDF) into reference/newmarket-july/:
  july-site-plan.png / .pdf          the run-in: from the run-out to 3.75f, both sides of the track in detail
  july-site-plan-course.png / .pdf   the whole course: the straight mile, the bend, the leg and the Rowley Mile beside it

Axes as the course files: x along the straight (metres from the post, + up the course; the horses run towards -x),
z across (0 = the inside rail, the track to 34 m, the stands behind the inside rail at z < 0). Drawn with the stand
side at the top and the horses running right to left, as on plan-markup.png.
"""
import json, math, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle, FancyArrowPatch, Circle, Wedge
from matplotlib.collections import PatchCollection, LineCollection

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
def rp(*p): return os.path.join(REPO, *p)

C = json.load(open(rp("race-view/assets/course/newmarket-july.json")))
S = json.load(open(rp("race-view/assets/course/newmarket-july-scenery.json")))
D = json.load(open(rp("courses/newmarket-july-draft.json")))
SITE = json.load(open(rp("courses/newmarket-site.json")))
K = json.load(open(rp("assets/models/architecture/site_props_codes.json")))["codes"]
JS = json.load(open(rp("assets/models/architecture/july_stands.json")))["pieces"]
CODE = {v["piece"]: k for k, v in K.items()}
W = C["trackWidth"]
F = C["furlong"]
COL = dict(grass="#c6d6a0", lawn="#d6e0b0", track="#e3ecbf", rail="#ffffff", ink="#1f2a1c", piece="#ffffff",
           pieceedge="#1f5a38", stand="#efe3c4", standedge="#8a744a", post="#e055c8", grid="#ffffff",
           tree="#5f9a48", treeedge="#3c6a2e", belt="#4f8a3d", scrub="#8cbf62", crowd="#b9793a", wall="#fbfaf4",
           walledge="#8a8170", dyke="#9fb27a", dykecrest="#7f9659", cam="#2d4f8f", other="#d9dccb")
CROWN = {"oak_a": 4.7, "oak_b": 4.7, "oak_c": 4.7, "wide_a": 5.4, "wide_b": 5.3, "poplar_a": 2.3,   # crown radius at scale 1
         "bush_a": 2.4, "bush_b": 2.4}                                                        # (race-view/assets/trees/trees.json)
BOARD = {"green": "#2f6b3e", "cream": "#e9dcb4", "navy": "#27365e", "white": "#ffffff"}
P = lambda pts: np.array([[x, -z] for x, z in pts])

# ---------------------------------------------------------------- names for the buildings
NAMES = []                                    # (name, x, z) at each named building's front middle
for s in D["standSide"]["stands"]:
    x = s["at"][0] if "at" in s else sum(s["x"]) / 2
    NAMES.append((s["name"], x, -s.get("front", 0) if "at" not in s else s["at"][1]))
for s in D["farSide"]["stands"]:
    NAMES.append((s["name"], sum(s["x"]) / 2, W + s["off"]))


def name_for(piece, x, z):
    best, bd = None, 1e9
    for n, nx, nz in NAMES:
        d = math.hypot(nx - x, nz - z)
        if d < bd:
            best, bd = n, d
    return best if bd < 25 else None


def corners(p):
    """A placed piece's footprint corners in world (x, z). Pieces: [model, piece, x, z, turn, stretch, scale];
    turn = degrees anticlockwise from above, 0 = the front facing +z."""
    model, piece, x, z, turn, stretch, scale = p
    if model == "july_stands":
        w, d = JS[piece]["width"] * stretch * scale, JS[piece]["depth"] * scale
        box = (-w / 2, w / 2, -d, 0.0)                          # origin = the middle of the front
    else:
        fp = K[CODE[piece]]["footprint"]
        box = (fp["x0"] * stretch * scale, fp["x1"] * stretch * scale, fp["z0"] * scale, fp["z1"] * scale)
    th = math.radians(turn); c, s = math.cos(th), math.sin(th)
    x0, x1, z0, z1 = box
    return [(x + lx * c + lz * s, z - lx * s + lz * c) for lx, lz in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))]


def dyke_patches(X0, X1):
    """The Dyke: each cross-section row of the bank, shaded where it stands above the ground."""
    out, crest = [], []
    for B in S["banks"]:
        rows = B["rows"]
        xs = [r[0] for r in rows]
        step = np.median(np.diff(sorted(set(xs)))) if len(set(xs)) > 1 else 10
        for r in rows:
            a = np.array(r).reshape(-1, 3)
            x = a[0, 0]
            if not (X0 - 20 < x < X1 + 20):
                continue
            up = a[:, 1] > 0.25
            if not up.any():
                continue
            # contiguous runs above the ground
            idx = np.where(up)[0]
            runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
            for run in runs:
                z0, z1 = a[run[0], 2], a[run[-1], 2]
                out.append(Rectangle((x - step / 2, -z1), step, z1 - z0))
                k = run[np.argmax(a[run, 1])]
                crest.append((x, -a[k, 2], a[k, 1]))
    return out, crest


def rowley_in_july():
    """The Rowley Mile's track outline, turned into the July Course's axes."""
    path = rp("race-view/assets/course/newmarket.json")
    if not os.path.exists(path):
        return None
    R = json.load(open(path))
    r = math.radians(SITE["julyCourse"]["rotate"]); ox, oz = SITE["julyCourse"]["offset"]
    c, s = math.cos(r), math.sin(r)
    def tr(pts):
        out = []
        for sx, sz in pts:
            dx, dz = sx - ox, sz - oz
            out.append((dx * c + dz * s, -dx * s + dz * c))
        return out
    return [tr(poly) for poly in R["track"]["surface"]], R


def north_dir():
    """North in the plan (site: +z is north). Returns a unit vector in plot coordinates."""
    r = math.radians(SITE["julyCourse"]["rotate"])
    x, z = math.sin(r), math.cos(r)                # site (0, 1) in July axes
    v = np.array([x, -z]); return v / np.linalg.norm(v)


def base(ax, X0, X1, Z0, Z1, detail):
    ax.set_xlim(X0, X1); ax.set_ylim(-Z1, -Z0); ax.set_aspect("equal"); ax.set_facecolor(COL["grass"])
    for poly in C["track"]["surface"]:
        ax.add_patch(MplPoly(P(poly), closed=True, fc=COL["track"], ec="none", zorder=2))
    for line in C["rails"]["lines"]:
        a = P(line); ax.plot(a[:, 0], a[:, 1], color=COL["rail"], lw=1.2 if detail else 0.7, zorder=3)
    ax.plot([0, 0], [0.5, -W - 0.5], color=COL["post"], lw=3 if detail else 2, zorder=5)


def dyke_layer(ax, X0, X1, detail):
    pats, crest = dyke_patches(X0, X1)
    ax.add_collection(PatchCollection(pats, fc=COL["dyke"], ec="none", alpha=0.75, zorder=2.4))
    if crest:
        crest.sort()
        a = np.array([(x, y) for x, y, h in crest])
        ax.plot(a[:, 0], a[:, 1], color=COL["dykecrest"], lw=1.6 if detail else 0.8, ls=(0, (6, 3)), zorder=2.5)


def walls_layer(ax, detail):
    segs = []
    for bx in S["boxes"].values():
        for x, z, L, d, y0, y1, yaw in bx:
            if L > 5:                                         # the wall runs (the piers are the little boxes)
                segs.append([(x - L / 2, -z), (x + L / 2, -z)])
    ax.add_collection(LineCollection(segs, colors=COL["walledge"], linewidths=3.2 if detail else 1.2, zorder=6.4))
    ax.add_collection(LineCollection(segs, colors=COL["wall"], linewidths=1.8 if detail else 0.6, zorder=6.5))


def trees_layer(ax, X0, X1, Z0, Z1, detail):
    inside = lambda x, z, m=30: X0 - m < x < X1 + m and Z0 - m < z < Z1 + m
    big, belt, scrub = [], [], []
    for t in S["trees"]:
        x, z, kind, sc = t[0], t[1], t[2], t[3]
        if not inside(x, z):
            continue
        flag = t[5] if len(t) > 5 else 0
        r = CROWN.get(kind, 4.8) * sc
        (scrub if flag == 2 else belt if flag == 1 else big).append(Circle((x, -z), r * (0.7 if flag == 2 else 1)))
    lw = 0.4 if detail else 0.12
    ax.add_collection(PatchCollection(belt, fc=COL["belt"], ec=COL["treeedge"], lw=lw, alpha=0.88, zorder=6))
    ax.add_collection(PatchCollection(big, fc=COL["tree"], ec=COL["treeedge"], lw=lw, alpha=0.88, zorder=6.05))
    ax.add_collection(PatchCollection(scrub, fc=COL["scrub"], ec="none", alpha=0.8, zorder=5.9))
    return len(big) + len(belt) + len(scrub)


def crowd_layer(ax, X0, X1, Z0, Z1, detail):
    a = np.array(S["people"]).reshape(-1, 4)
    m = (a[:, 0] > X0) & (a[:, 0] < X1) & (a[:, 2] > Z0) & (a[:, 2] < Z1)
    ax.scatter(a[m, 0], -a[m, 2], s=0.25 if detail else 0.05, color=COL["crowd"], alpha=0.55, linewidths=0, zorder=4.2)


def boards_layer(ax, X0, X1, detail):
    for b in S["boards"]:
        x, z, turn, design = b[:4]; L = 3 * (b[4] if len(b) > 4 else 1.0)
        if not (X0 < x < X1):
            continue
        th = math.radians(turn); c, s = math.cos(th), math.sin(th)
        a = [(x - L * c, -(z + L * s)), (x + L * c, -(z - L * s))]
        ax.plot([a[0][0], a[1][0]], [a[0][1], a[1][1]], color=COL["ink"], lw=3.4 if detail else 1.6, solid_capstyle="butt", zorder=7.1)
        ax.plot([a[0][0], a[1][0]], [a[0][1], a[1][1]], color=BOARD.get(design, "#999"), lw=2.2 if detail else 1.0, solid_capstyle="butt", zorder=7.2)


def pieces_layer(ax, X0, X1, detail, letters=True):
    used = set()
    for p in S["pieces"]:
        cs = corners(p)
        cx = np.mean([q[0] for q in cs]); cz = np.mean([q[1] for q in cs])
        if not (X0 - 60 < cx < X1 + 60):
            continue
        poly = P(cs)
        if p[0] == "july_stands":
            ax.add_patch(MplPoly(poly, closed=True, fc=COL["stand"], ec=COL["standedge"], lw=0.8 if detail else 0.3, zorder=7))
        else:
            code = CODE[p[1]]; used.add(code)
            ax.add_patch(MplPoly(poly, closed=True, fc=COL["piece"], ec=COL["pieceedge"], lw=0.6 if detail else 0.25, zorder=7))
            if detail and letters:
                small = K[code]["width"] < 4 and K[code]["depth"] < 4
                ax.text(cx, -cz, code, ha="center", va="center", fontsize=4.5 if small else 7.5, fontweight="bold",
                        color=COL["pieceedge"], zorder=8)
    return used


def grid(ax, X0, X1, Z0, Z1, step, major):
    for x in range(int(math.ceil(X0 / step) * step), int(X1) + 1, step):
        ax.axvline(x, color=COL["grid"], lw=0.9 if x % major == 0 else 0.35, alpha=0.6 if x % major == 0 else 0.4, zorder=3.5)
    for z in range(int(math.ceil(Z0 / step) * step), int(Z1) + 1, step):
        ax.axhline(-z, color=COL["grid"], lw=0.9 if z % major == 0 else 0.35, alpha=0.6 if z % major == 0 else 0.4, zorder=3.5)
    for sp in ax.spines.values(): sp.set_color("#8a744a")
    ax.tick_params(length=3, colors="#4f5d4a")


def north_arrow(ax, x, y, L):
    v = north_dir() * L
    ax.add_patch(FancyArrowPatch((x - v[0] / 2, y - v[1] / 2), (x + v[0] / 2, y + v[1] / 2), arrowstyle="-|>",
                                 mutation_scale=16, color=COL["ink"], lw=1.5, zorder=11))
    ax.text(x + v[0] * 0.75, y + v[1] * 0.75, "N", ha="center", va="center", fontsize=11, fontweight="bold", color=COL["ink"], zorder=11)


def camera(ax, x, z, aim_deg, label, dx=0, dy=0, spread=50, R=18):
    """A camera marker: a dot and a fan for which way it looks (aim in plot degrees)."""
    ax.add_patch(Wedge((x, -z), R, aim_deg - spread / 2, aim_deg + spread / 2, fc=COL["cam"], ec="none", alpha=0.22, zorder=9))
    ax.plot(x, -z, "o", ms=5, color=COL["cam"], mec="white", mew=0.8, zorder=9.5)
    ax.text(x + dx, -z + dy, label, ha="center", va="center", fontsize=7.2, color=COL["cam"], fontweight="bold", zorder=10,
            bbox=dict(boxstyle="round,pad=0.2", fc="#f4f6fb", ec="none", alpha=0.85))


# ================================================================== sheet 1: the run-in
X0, X1, Z0, Z1 = -320, 765, -235, 195
fig = plt.figure(figsize=(16.54, 11.69))
ax = fig.add_axes([0.065, 0.225, 0.91, 0.63]); ax.set_anchor("N")
base(ax, X0, X1, Z0, Z1, True)
L = D["standSide"]["lawn"]
ax.add_patch(Rectangle((L["x"][0], -L["z"][1]), L["x"][1] - L["x"][0], L["z"][1] - L["z"][0], fc=COL["lawn"], ec="none", zorder=2.2))
E = D["standSide"]["enclosure"]
ax.add_patch(Rectangle((E["x"][0], -E["z"][1]), E["x"][1] - E["x"][0], E["z"][1] - E["z"][0], fc=COL["lawn"], ec="#a6955f", lw=0.6, ls="--", zorder=2.3))
dyke_layer(ax, X0, X1, True)
walls_layer(ax, True)
crowd_layer(ax, X0, X1, Z0, Z1, True)
ntrees = trees_layer(ax, X0, X1, Z0, Z1, True)
boards_layer(ax, X0, X1, True)
used = pieces_layer(ax, X0, X1, True)

# zones (dashed outlines)
def zone(x0, x1, z0, z1, colour, label=None, lx=None, lz=None):
    ax.add_patch(Rectangle((x0, -z1), x1 - x0, z1 - z0, fc="none", ec=colour, lw=1.1, ls=(0, (5, 3)), zorder=8.5))
FS = D["standSide"]["festival"]; zone(FS["x"][0], FS["x"][1], FS["z"][0], FS["z"][1], "#c46a2b")
FF = D["farSide"]["festival"]; zone(FF["x"][0], FF["x"][1], W + FF["off"][0], W + FF["off"][1], "#2f7d8c")

# furlong poles, post, finish line, direction
for f in C["straightMile"]["furlongPoles"]:
    x = f["at"][0]
    if X0 < x < X1:
        ax.plot([x, x], [1.5, 5.5], color="#c0392b", lw=2, zorder=5)
        ax.text(x, -W / 2, "%df" % f["furlongs"], ha="center", va="center", fontsize=10, color="#c0392b", fontweight="bold", zorder=9)
ax.text(-2.5, -W / 2, "POST", ha="right", va="center", fontsize=9.5, color="#a0308f", fontweight="bold", zorder=9)
for x in (265, 470):
    ax.add_patch(FancyArrowPatch((x + 70, -W / 2), (x, -W / 2), arrowstyle="-|>", mutation_scale=14, color="#5b7a3a", lw=1.4, zorder=5))
ax.text(300, -W / 2 - 9, "direction of running", ha="center", va="center", fontsize=8, color="#3f5a28", zorder=6)
ax.text(-130, -W / 2, "the run-out (300 m past the post)", ha="center", va="center", fontsize=8, color="#3f5a28", zorder=6)

# building names
lab = dict(fontsize=8.2, color=COL["ink"], zorder=10, bbox=dict(boxstyle="round,pad=0.22", fc="#fbf6e8", ec="none", alpha=0.88))
done = set()
for p in S["pieces"]:
    if p[0] != "july_stands":
        continue
    n = name_for(p[1], p[2], p[3])
    cs = corners(p); cx = np.mean([q[0] for q in cs]); cz = np.mean([q[1] for q in cs])
    if n is None:
        n = {"pavilion_small": "pavilion"}.get(p[1], p[1].replace("_", " "))
    if (n, round(cx)) in done:
        continue
    done.add((n, round(cx)))
    fs = 8.6 if p[1] in ("terrace_grand", "old_pavilion") else 7.4
    lead = {"Little pavilion": (-215, 50), "Bell tent": (-215, 36), "Weighing room": (-215, 22),
            "Judge's box": (-60, 55), "Pavilion wing": (-60, 69)}.get(n)
    if lead:
        ax.annotate(n, xy=(cx, -cz), xytext=lead, ha="center", va="center",
                    arrowprops=dict(arrowstyle="-", lw=0.7, color="#5a4a20", shrinkA=0, shrinkB=1), **dict(lab, fontsize=fs))
        continue
    off = {"Far tower": (0, -9), "Old pavilion": (0, -7)}.get(n, (0, 0))
    ax.text(cx + off[0], -cz + off[1], n, ha="center", va="center", **dict(lab, fontsize=fs))
TI = D["farSide"]["tier"]
ax.text(sum(TI["x"]) / 2, -(W + TI["off"][1] + 9), "Tiered stand (3 × F)", ha="center", va="center", **lab)

lab2 = dict(fontsize=8.6, color=COL["ink"], zorder=10, bbox=dict(boxstyle="round,pad=0.3", fc="#fbf6e8", ec="none", alpha=0.9))
ax.text(FS["x"][1] - 4, -FS["z"][0] + 7, "Stand-side festival (to 3.5f)", ha="right", va="bottom", color="#9a4e1c", fontsize=8.6, fontweight="bold", zorder=10,
        bbox=dict(boxstyle="round,pad=0.25", fc="#fbf6e8", ec="none", alpha=0.9))
ax.text(FF["x"][1] - 4, -(W + FF["off"][1]) - 4, "Far-side festival: marquees and pavilions among big trees (3f to past the post)", ha="right", va="top",
        color="#215d68", fontsize=8.6, fontweight="bold", zorder=10, bbox=dict(boxstyle="round,pad=0.25", fc="#fbf6e8", ec="none", alpha=0.9))
ax.text(150, 6.5 * 0 - (-8.5), "packed lawns, coloured umbrellas", ha="center", va="center", fontsize=7.4, color="#5a4a20", zorder=10)
ax.text(140, 80, "White boundary wall, low planting in front", ha="center", va="center", **dict(lab2, fontsize=7.6))
ax.text(140, -(W + 39) - 5.5, "White boundary wall, low planting in front", ha="center", va="top", **dict(lab2, fontsize=7.6))
ax.text(120, 135, "Behind the stands: paddock, parade rings and buildings among trees (barely seen by the cameras)", ha="center", **dict(lab2, fontsize=8))
ax.text(330, -(W + 118), "The Dyke (dashed: its crest), with big trees beyond, towards the Rowley Mile", ha="center", va="center", **dict(lab2, fontsize=8.2))
ax.text(-150, -(W + 18), "crowd round the Garden stand", ha="center", va="center", fontsize=7.4, color="#5a4a20", zorder=10)
ax.annotate("marquees (A) + tree wall", xy=(-118, 38), xytext=(-215, 64), ha="center", va="center",
            arrowprops=dict(arrowstyle="-", lw=0.7, color="#5a4a20", shrinkA=0, shrinkB=1), **dict(lab, fontsize=7.4))

# cameras
cams = D["keyCameras"]
sx, sz = cams["standCamera"]["at"][:2]
camera(ax, sx, sz, -90, "stand camera (on the judge's box)", dx=-58, dy=-11, spread=70, R=26)
rx, rz = cams["reverse"]["at"][:2]
camera(ax, rx, rz, 90, "reverse camera", dx=34, dy=-5, spread=60, R=20)
hx, hz = cams["headOn"]["at"][:2]
camera(ax, hx, hz, 0, "head-on camera", dx=8, dy=-11, spread=2 * cams["headOn"]["halfAngle"], R=40)
ax.plot([X0 + 5, X1 - 5], [-cams["trackingCar"]["lane"]] * 2, color=COL["cam"], lw=0.8, ls=(0, (2, 3)), alpha=0.6, zorder=8.8)
ax.text(-200, -cams["trackingCar"]["lane"] + 2.2, "tracking car lane (stand side, along the rail)", ha="center", va="bottom", fontsize=6.8, color=COL["cam"], zorder=10)

grid(ax, X0, X1, Z0, Z1, 25, 100)
ax.set_xticks(range(-300, 701, 100)); ax.set_xticklabels(["%d m" % x for x in range(-300, 701, 100)], fontsize=8)
zt = [-200, -150, -100, -50, 0, 34, 100, 150]
ax.set_yticks([-z for z in zt])
ax.set_yticklabels(["%d m" % abs(z) + (" stand side" if z < 0 else " far side" if z > W else "") if z not in (0, W) else
                    ("inside rail" if z == 0 else "outer rail") for z in zt], fontsize=7.5)
north_arrow(ax, 735, 170, 34)
ax.add_patch(Rectangle((-305, -180), 100, 3.5, fc=COL["ink"], zorder=11))
ax.add_patch(Rectangle((-305, -180), 50, 3.5, fc="#ffffff", ec=COL["ink"], lw=0.6, zorder=11))
ax.text(-255, -186, "0        50       100 m  (grid 25 m)", ha="center", va="top", fontsize=8, color=COL["ink"], zorder=11)

fig.text(0.035, 0.955, "Thoroughbred · Newmarket July Course: the run-in", fontsize=20, color="#1f5a38", fontweight="bold", family="serif")
fig.text(0.035, 0.918, "Site plan, 11 Nov 2026, as the race view draws it today. To scale, metres from the winning post along the straight and from the inside rail across it. "
         "Stand side at the top; the horses run right to left.\nCream: the stands and buildings; white with a letter: site pieces (codes below); green circles: trees "
         "(darker = the planting belts along the walls); brown dots: the crowd; little bars: advertising boards in their colours;\n"
         "double white line: the boundary walls; olive band: the Dyke; dashed outlines: the two festival areas; blue: the main cameras.",
         fontsize=9, color="#4f5d4a", va="top")
fig.text(0.035, 0.875, "To mark up: write a letter where you want a piece (an arrow for which way it faces), cross out any to remove, circle areas to plant or clear.",
         fontsize=9, color="#4f5d4a", va="top")
keys = sorted(used)
cols = 4; per = max(1, math.ceil(len(keys) / cols))
fig.text(0.04, 0.265, "Codes (site pieces on this plan)", fontsize=11, fontweight="bold", color="#1f5a38")
for i, k in enumerate(keys):
    col, row = divmod(i, per)
    fig.text(0.04 + col * 0.235, 0.24 - row * 0.022, "%s   %s  (%g × %g m)" % (k, K[k]["name"], K[k]["width"], K[k]["depth"]),
             fontsize=9, color=COL["ink"])
fig.text(0.04, 0.155, "Main stands: Grandstand, Premier stand, Paddock stand, each %.0f m long, front 16 m behind the inside rail. Old pavilion %.0f m, "
         "centred on the post, with its wing cranked 30° down the run-out." % (JS["terrace_grand"]["width"] * 0.97, JS["old_pavilion"]["width"]),
         fontsize=9, color="#4f5d4a")
fig.text(0.04, 0.133, "Not shown: the trees and boards further up the straight and round the bend (see the whole-course sheet).", fontsize=9, color="#4f5d4a")
fig.patch.set_facecolor("#f4ead2")
out = rp("reference/newmarket-july")
fig.savefig(os.path.join(out, "july-site-plan.png"), dpi=200, facecolor=fig.get_facecolor())
fig.savefig(os.path.join(out, "july-site-plan.pdf"), facecolor=fig.get_facecolor())
plt.close(fig)
print("run-in sheet: trees", ntrees, "pieces", len(S["pieces"]), "codes", "".join(keys))

# ================================================================== sheet 2: the whole course
X0, X1, Z0, Z1 = -420, 2160, -560, 1120
fig = plt.figure(figsize=(16.54, 11.69))
ax = fig.add_axes([0.075, 0.06, 0.9, 0.83])
ax.set_xlim(X0, X1); ax.set_ylim(-Z1, -Z0); ax.set_aspect("equal"); ax.set_facecolor(COL["grass"])
rw = rowley_in_july()
if rw:
    polys, R = rw
    for poly in polys:
        ax.add_patch(MplPoly(P(poly), closed=True, fc=COL["other"], ec="#b6b9a5", lw=0.5, zorder=1.8))
base(ax, X0, X1, Z0, Z1, False)
dyke_layer(ax, X0, X1, False)
walls_layer(ax, False)
crowd_layer(ax, X0, X1, Z0, Z1, False)
trees_layer(ax, X0, X1, Z0, Z1, False)
boards_layer(ax, X0, X1, False)
pieces_layer(ax, X0, X1, False)
for f in C["straightMile"]["furlongPoles"]:
    x = f["at"][0]
    ax.plot([x, x], [2, 14], color="#c0392b", lw=1.4, zorder=5)
    ax.text(x, 22, "%df" % f["furlongs"], ha="center", va="bottom", fontsize=7.5, color="#c0392b", fontweight="bold", zorder=9)
for k, s in D["starts"].items():
    x, z = s["at"]
    if not s.get("onStraight"):
        ax.plot(x + W / 2, -z, "s", ms=3.5, color="#2d4f8f", zorder=9)
        ax.text(x + W + 14, -z, k + " start", ha="left", va="center", fontsize=7.2, color="#2d4f8f", zorder=9, clip_on=True)
ax.text(-6, 20, "July post", ha="right", fontsize=8, color="#a0308f", fontweight="bold", zorder=10)
lab3 = dict(fontsize=9, color=COL["ink"], zorder=10, bbox=dict(boxstyle="round,pad=0.3", fc="#fbf6e8", ec="none", alpha=0.88))
ax.text(200, 215, "Run-in (sheet 1): stands, festival areas", ha="center", **lab3)
ax.text(1000, 95, "The straight mile (the Bunbury Mile): races up to a mile start here", ha="center", **lab3)
ax.annotate("The Cesarewitch leg, shared with the Rowley Mile:\nraces over a mile come down it and turn right.\nOff the sheet: the 1m4f, 1m5f, 1m6f and 2m starts",
            xy=(1838, 548), xytext=(1420, 500), ha="center", va="center", arrowprops=dict(arrowstyle="-|>", lw=1.0, color=COL["ink"]), **lab3)
ax.text(1540, 330, "Belt of trees across the top\nof the straight (closes the view)", ha="center", va="center", **lab3)
if rw:
    rx, rz = -157.2, 1000.2                               # the Rowley Mile's winning post in these axes
    ax.plot(rx, -rz, "o", ms=5, color="#a0308f", zorder=9)
    ax.text(rx + 20, -rz + 30, "Rowley Mile post", ha="left", fontsize=8, color="#a0308f", fontweight="bold", zorder=10)
    ax.text(780, -760, "The Rowley Mile (grey): its straight, beyond the Dyke, at 25° to the July straight", ha="center", va="center", **dict(lab3, fontsize=8.5))
grid(ax, X0, X1, Z0, Z1, 100, 500)
ax.set_xticks(range(0, 2001, 500)); ax.set_xticklabels(["%d m" % x for x in range(0, 2001, 500)], fontsize=8)
zt = [-500, 0, 500, 1000]
ax.set_yticks([-z for z in zt]); ax.set_yticklabels(["%d m %s" % (abs(z), "stand side" if z < 0 else "far side" if z > 0 else "(inside rail)") for z in zt], fontsize=8)
north_arrow(ax, 2060, -950, 110)
ax.add_patch(Rectangle((-380, -1060), 200, 9, fc=COL["ink"], zorder=11))
ax.add_patch(Rectangle((-380, -1060), 100, 9, fc="#fff", ec=COL["ink"], lw=0.6, zorder=11))
ax.text(-280, -1075, "0      100     200 m  (grid 100 m)", ha="center", va="top", fontsize=8, zorder=11)
fig.text(0.04, 0.955, "Thoroughbred · Newmarket July Course: the whole course", fontsize=20, color="#1f5a38", fontweight="bold", family="serif")
fig.text(0.04, 0.925, "Site plan, 11 Nov 2026, as the race view draws it today. Stand side at the top of the straight; the horses run right to left. "
         "Green: trees; olive: the Dyke; cream: stands; white: site pieces; blue squares: the round-course starts; grey: the Rowley Mile.",
         fontsize=9, color="#4f5d4a")
fig.patch.set_facecolor("#f4ead2")
fig.savefig(os.path.join(out, "july-site-plan-course.png"), dpi=200, facecolor=fig.get_facecolor())
fig.savefig(os.path.join(out, "july-site-plan-course.pdf"), facecolor=fig.get_facecolor())
plt.close(fig)
print("wrote reference/newmarket-july/july-site-plan(.png/.pdf) and july-site-plan-course(.png/.pdf)")
