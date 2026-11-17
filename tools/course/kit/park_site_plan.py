"""The Park's site plan, as a drawing to keep: the whole course and, enlarged, the enclosure (the stands, the lawn, the
festival side), from courses/park-draft.json and a top-down render of the buildings.

    python3.11 tools/blender/park_siteplan_roofs.py      # first, if a stand or the layout has changed
    python3.11 tools/course/kit/park_site_plan.py         # writes reference/park/site-plan.png

Owner, 17 Nov 2026: "Can I have a site plan for the park course please". Turned the racing papers' way: the home
straight along the bottom, the horses running left to right to the post on the right, the stands below it.
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle, Ellipse, Circle, FancyBboxPatch
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
C = json.loads((REPO / "courses/park-draft.json").read_text())
W, F = C["trackWidth"], C["furlong"]
m = -C["hand"]                                     # +1 for the left-handed course: stands at z < 0
T = lambda x, z: (-x, m * z)                       # world (x, z) to the plan: the post on the right, the infield up
NAMES = {"park_tiered_stand": "Tiered stand", "park_balcony_stand": "Balcony stand", "park_arch_stand": "Barrel-roof stand",
         "park_old_pavilion": "Old pavilion", "park_gable_stand": "Pitched-roof stand",
         "park_roof_terrace_stand": "Roof-terrace stand", "park_clock_house": "Clock house", "park_terrace": "Terrace",
         "park_shed": "Shed", "park_glass_box": "Glass box", "park_glass_box_small": "Glass box", "park_victorian": "Victorian pavilion"}
INK, TURF, RAIL, GRASS = "#2c2c30", "#93b866", "#3f5e2c", "#e6ead6"
ROUTE_COL = {"straight": "#2f5d8a", "mile": "#2f7a6a", "round": "#2c2c30", "far": "#6a4c93", "loop": "#a0522d"}


def ribbon(pts):
    """The track between the inside rail (pts, world) and the outer rail W outwards (to the right of the list's order)."""
    p = np.array(pts, float)
    t = np.gradient(p, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    return p, p + np.c_[t[:, 1], -t[:, 0]] * W * m


def draw_track(ax, lw=0.7):
    for name in ("loop", "round", "far", "mile", "straight"):
        p, o = ribbon(C["routes"][name]["insideRail"])
        ax.add_patch(Polygon([T(*v) for v in list(p) + list(o[::-1])], closed=True, fc=TURF, ec="none", zorder=2))
    for name in ("loop", "round", "far", "mile", "straight"):        # the rails over the turf
        p, o = ribbon(C["routes"][name]["insideRail"])
        for q in (p, o):
            ax.plot(*zip(*[T(*v) for v in q]), color=RAIL, lw=lw, zorder=3, solid_capstyle="butt")


def draw_zones(ax, labels=True, fs=8):
    Z = C["zones"]
    for b in Z["belts"]:                                             # tree belts: a band and a scatter of trees
        if "poly" in b:
            ax.add_patch(Polygon([T(*q) for q in b["poly"]], closed=True, fc="#b6cc95", ec="none", zorder=1))
    lk = Z["lake"]
    ax.add_patch(Ellipse(T(*lk["centre"]), 2 * lk["radii"][0], 2 * lk["radii"][1], angle=-8, fc="#b3d1e3", ec="#7aa3bd", lw=0.8, zorder=2))
    if labels:
        ax.text(*T(*lk["centre"]), "lake", ha="center", va="center", fontsize=fs, color="#3d6680", style="italic", zorder=4)
    for e in Z["chuteEnds"]:
        ax.add_patch(Ellipse(T(*e["at"]), 60, 36, fc="#b6cc95", ec="#7f9b62", lw=0.6, zorder=1))

    def rect(zone, fc, ec, label=None, z=1.5, ls="-"):
        (x0, x1), (z0, z1) = zone["x"], zone["z"]
        a, b = T(x0, z0), T(x1, z1)
        ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec=ec, lw=0.8, ls=ls, zorder=z))
        if label and labels:
            ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, label, ha="center", va="center", fontsize=fs, color="#444", zorder=6, clip_on=True)
    rect(Z["festival"], "#f4e1c6", "#c99a63", z=1.5, ls="--")
    rect(Z["standLawn"], "#dfe3c9", "none")
    rect(Z["paddock"], "#d5e5b8", "#7f9b62")
    rect(Z["standPark"], "#ece3f0", "#a68bb4", "car park")


def stand_rects(ax, fs=8, labels=True):
    for e in C["stands"]["chain"]:
        x0, x1 = e["x"] - e["width"] / 2, e["x"] + e["width"] / 2
        z0 = e["z"]; z1 = z0 - m * e["depth"]
        a, b = T(x0, z0), T(x1, z1)
        ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc="#d8cbb4", ec="#6c6458", lw=0.5, zorder=4))
    for e in C["festival"]["pieces"]:
        x0, x1 = e["x"] - e["width"] / 2, e["x"] + e["width"] / 2
        z0 = e["z"]; z1 = z0 + m * e["depth"]
        a, b = T(x0, z0), T(x1, z1)
        ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc="#d59a85", ec="#6c6458", lw=0.5, zorder=4))


def scale_bar(ax, x, y, L, step, fs=8):
    n = int(L / step)
    for i in range(n):
        ax.add_patch(Rectangle((x + i * step, y), step, L * 0.012, fc=INK if i % 2 == 0 else "white", ec=INK, lw=0.6, zorder=9))
    for i in (0, n):
        ax.text(x + i * step, y - L * 0.02, "%d m" % (i * step) if i else "0", ha="center", va="top", fontsize=fs, color=INK, zorder=9)


def post_and_poles(ax, fs=8, small=False):
    kw = dict(clip_on=True)
    ax.plot([0, 0], [0, -m * W], color="#c0392b", lw=2.2, zorder=7)
    ax.add_patch(Circle((0, 0), 4 if small else 7, fc="#c0392b", ec="white", lw=0.8, zorder=8))
    ax.text(6, 10 if not small else 6, "winning post", fontsize=fs, color="#c0392b", fontweight="bold", zorder=8)
    for f in C["furlongPoles"]:
        x, z = T(*f["at"])
        ax.plot([x, x], [z, z - m * W], color=INK, lw=1.0, zorder=7)
        ax.text(x, z + (6 if small else 9), "%df" % f["furlongs"], ha="center", fontsize=fs - 1, color=INK, zorder=8, **kw)


# ------------------------------------------------------------------ the sheet
fig = plt.figure(figsize=(11.7, 16.5), dpi=200)               # A3 portrait at 200 dpi
fig.patch.set_facecolor("white")
ax = fig.add_axes([0.04, 0.585, 0.92, 0.34])                   # the whole course
az = fig.add_axes([0.04, 0.125, 0.92, 0.45])                   # the enclosure, enlarged
ak = fig.add_axes([0.04, 0.01, 0.92, 0.105]); ak.axis("off")  # the key and title block
fig.text(0.04, 0.975, "THE PARK", fontsize=22, fontweight="bold", color=INK, va="top")
fig.text(0.04, 0.948, "Site plan, draft, 17 Nov 2026. The generic galloping course for 12 Flat courses.", fontsize=11, color=INK, va="top")

# ---- 1: the whole course
for a in (ax, az):
    a.set_facecolor(GRASS); a.set_aspect("equal"); a.set_xticks([]); a.set_yticks([])
    for s in a.spines.values():
        s.set_color("#888")
draw_zones(ax, fs=9)
draw_track(ax, lw=0.6)
stand_rects(ax)
post_and_poles(ax, fs=9)
for name, s in C["starts"].items():
    x, z = T(*s["at"]); col = ROUTE_COL[s["route"]]
    r = np.array(s["running"], float); r = np.array([-r[0], m * r[1]])
    across = np.array([-r[1], r[0]])                              # across the track at the start
    a, b = np.array([x, z]), np.array([x, z]) + across * W * (1 if np.dot(across, [0, 1]) < 0 else -1)
    ax.plot([a[0], b[0]], [a[1], b[1]], color=col, lw=2.4, zorder=7)
    off = -across * 18 if np.dot(across, [0, 1]) < 0 else across * 18
    ax.text(x + off[0] * 1.6, z + off[1] * 1.6, name, ha="center", va="center", fontsize=10, fontweight="bold", color=col, zorder=8)
xs = [T(*v)[0] for r in C["routes"].values() for v in r["insideRail"]]
zs = [T(*v)[1] for r in C["routes"].values() for v in r["insideRail"]]
ax.set_xlim(min(xs) - 80, max(xs) + 80); ax.set_ylim(min(zs) - 260, max(zs) + 110)
# the run of the race: arrows on the home straight and the back straight
for (x, z, dx) in ((-500, -m * W / 2, 1), (-300, -m * W / 2, 1)):
    ax.annotate("", xy=(x + 60, z), xytext=(x, z), arrowprops=dict(arrowstyle="-|>", color="white", lw=1.6), zorder=8)
ax.text(min(xs) - 60, max(zs) + 80, "The whole course", fontsize=12, fontweight="bold", color=INK, va="top")
x0 = min(xs) - 40; y0 = min(zs) - 220
scale_bar(ax, x0, y0, 400, 100, fs=9)
ax.text(x0, y0 + 22, "Scale", fontsize=9, color=INK)
# the enclosure's frame on the whole-course panel
R = json.loads((REPO / "reference/park/_siteplan_roofs.json").read_text())
ea, eb = T(R["x"][0], R["z"][0]), T(R["x"][1], R["z"][1])
ax.add_patch(Rectangle((min(ea[0], eb[0]), min(ea[1], eb[1])), abs(eb[0] - ea[0]), abs(eb[1] - ea[1]), fc="none", ec="#c0392b", lw=1.2, ls="--", zorder=9))
ax.text(min(ea[0], eb[0]) + 6, max(ea[1], eb[1]) + 10, "the enclosure, below", fontsize=9, color="#c0392b", zorder=9)

# ---- 2: the enclosure, enlarged, with the buildings' roofs
draw_zones(az, fs=10)
draw_track(az, lw=1.0)
for x in np.arange(R["x"][0] + 4, R["x"][1], 9.0):              # the tree belt behind the stands and the car park
    for zz in (-118.0, -128.0):
        jx = 2.5 * np.sin(x * 1.7 + zz); jz = 2.5 * np.cos(x * 0.9)
        az.add_patch(Circle(T(x + jx, zz + jz), 4.6, fc="#8fb36c", ec="#6f8f4a", lw=0.5, zorder=3))
im = Image.open(REPO / "reference/park/_siteplan_roofs.png")
az.imshow(np.asarray(im), extent=(min(ea[0], eb[0]), max(ea[0], eb[0]), min(ea[1], eb[1]), max(ea[1], eb[1])), origin="upper", zorder=5, interpolation="lanczos")
post_and_poles(az, fs=10, small=True)
az.set_xlim(min(ea[0], eb[0]), max(ea[0], eb[0])); az.set_ylim(min(ea[1], eb[1]), max(ea[1], eb[1]))
for e in C["stands"]["chain"]:                                    # the stands' names below them
    x, z = T(e["x"], e["z"] - m * e["depth"])
    az.text(x, z - 3, NAMES.get(e["piece"], e["piece"]) + "\n%.0f m" % e["width"], ha="center", va="top", fontsize=9, color=INK, zorder=8, clip_on=True)
for e in C["festival"]["pieces"]:
    x, z = T(e["x"], e["z"] + m * e["depth"])
    az.text(x, z + 3, NAMES.get(e["piece"], e["piece"]), ha="center", va="bottom", fontsize=9, color=INK, zorder=8)
fz = C["zones"]["festival"]
az.text(*T(sum(fz["x"]) / 2, 22), "festival lawn: marquees, kiosks, flags", ha="center", fontsize=10, color="#8a5a24", style="italic", zorder=8, clip_on=True)
az.text(*T(sum(C["zones"]["standLawn"]["x"]) / 2, -W - 9), "lawn and rail walk", ha="center", va="center", fontsize=9, color="#555", zorder=8)
pd = C["zones"]["paddock"]
az.text(*T(sum(pd["x"]) / 2, -133), "parade ring (beyond)", ha="center", va="center", fontsize=10, color="#4c6a33", zorder=8, clip_on=True,
        bbox=dict(fc="#d5e5b8", ec="none", pad=1.5))
az.annotate("", xy=T(-40, -m * W / 2), xytext=T(40, -m * W / 2), arrowprops=dict(arrowstyle="-|>", color="white", lw=1.8), zorder=8)
az.text(min(ea[0], eb[0]) + 8, max(ea[1], eb[1]) - 8, "The enclosure: the stands, the lawn and the festival side", fontsize=11, fontweight="bold", color=INK, va="top", zorder=9)
scale_bar(az, -150, -104, 100, 20, fs=9)

# ---- 3: the key and the facts
ak.set_xlim(0, 1); ak.set_ylim(0, 1)
ak.add_patch(FancyBboxPatch((0.0, 0.0), 1.0, 1.0, boxstyle="square,pad=0", fc="white", ec=INK, lw=1.0))
ch = C["checks"]
facts = ["Left-handed, turf, galloping; parkland",
         "Circuit %.0f m (%.1f furlongs); run-in %.0f m" % (float(ch["circuit (inside rail), m"]), float(ch["circuit, furlongs"]), C["home"]),
         "Track %.0f m wide; bends of 110 to 300 m radius" % W,
         "Straight course to 6f; round-mile chute; far chute",
         "Stands: %.0f m of frontage, %.0f m of lawn in front" % (float(ch["stand frontage, m"]), C["stands"]["lawn"]),
         "Stands in for Ayr, Bath, Chelmsford City, Ffos Las, Leicester, Lingfield,",
         "Newcastle, Nottingham, Redcar, Salisbury, Wetherby, Yarmouth"]
for i, t in enumerate(facts):
    ak.text(0.02, 0.9 - i * 0.12, t, fontsize=8.5, color=INK, va="top")
key = [("Track (turf), rails", TURF, RAIL), ("Stands", "#d8cbb4", "#6c6458"), ("Festival buildings", "#d59a85", "#6c6458"),
       ("Festival lawn", "#f4e1c6", "#c99a63"), ("Parade ring", "#d5e5b8", "#7f9b62"), ("Car park", "#ece3f0", "#a68bb4"),
       ("Tree belts", "#b6cc95", "none"), ("Lake", "#b3d1e3", "#7aa3bd")]
for i, (t, fc, ec) in enumerate(key):
    cx, cy = 0.53 + (i // 4) * 0.24, 0.86 - (i % 4) * 0.17
    ak.add_patch(Rectangle((cx, cy - 0.05), 0.025, 0.09, fc=fc, ec=ec, lw=0.8))
    ak.text(cx + 0.035, cy, t, fontsize=8.5, color=INK, va="center")
ak.text(0.53, 0.14, "Starts:", fontsize=8.5, color=INK, va="center", fontweight="bold")
for i, (n, col) in enumerate((("straight", ROUTE_COL["straight"]), ("mile chute", ROUTE_COL["mile"]), ("round", ROUTE_COL["round"]),
                              ("far chute", ROUTE_COL["far"]), ("2m", ROUTE_COL["loop"]))):
    ak.text(0.60 + i * 0.08, 0.14, n, fontsize=8.5, color=col, va="center", fontweight="bold")
fig.savefig(REPO / "reference/park/site-plan.png", dpi=200, facecolor="white")
print("site plan written")
