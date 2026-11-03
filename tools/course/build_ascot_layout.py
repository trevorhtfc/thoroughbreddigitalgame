"""Build Ascot's full course layout from the inside-rail trace, and draw it top-down.

Reads:
  courses/ascot-trace.json                      inside rail traced from the board (board pixels)
  courses/ascot-grandstand-assembly.json        stand module order
  assets/models/architecture/stand_modules.json module catalogue (bays, depths)
Writes:
  courses/ascot.json                            the course as data, world metres
  reference/course/layout/ascot-layout-topdown.png   clean top-down plan
  reference/course/layout/ascot-layout-on-board.jpg  the trace drawn over the board, for checking
  reference/course/layout/ascot-stand-plan.png       the stand's modules, close up

World axes: metres, origin = the winning post on the inside rail. x = east, z = south (as the
board is drawn: down = south), y = up. Right-handed with y up, same as glTF/three.js/Godot.
Horses run clockwise (right-handed): on the home straight they run towards -x, the inside rail is
on their right (north, -z) and the stands on their left (south, +z).

Run:  python3 tools/course/build_ascot_layout.py      (needs numpy, shapely, matplotlib, pillow)
"""
import json, math, os
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle
from PIL import Image

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def rp(*p): return os.path.join(REPO, *p)

T = json.load(open(rp("courses/ascot-trace.json")))
ASM = json.load(open(rp("courses/ascot-grandstand-assembly.json")))
CAT = json.load(open(rp(ASM["catalogue"])))
F = T["scale"]["metresPerFurlong"]
MPP = F / T["scale"]["pxPerFurlong"]
PX0 = np.array(T["winningPost"]["px"], float)
W = T["trackWidth"]


def to_world(pts):
    return (np.asarray(pts, float) - PX0) * MPP


def to_px(pts):
    return np.asarray(pts, float) / MPP + PX0


# ---------- smoothing and resampling ----------
def catmull_rom(P, closed, n_per=24):
    """Centripetal Catmull-Rom through the points."""
    P = np.asarray(P, float)
    if closed:
        Q = np.vstack([P[-1], P, P[0], P[1]])
    else:
        Q = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        def tj(ti, a, b): return ti + max(np.linalg.norm(b - a), 1e-6) ** 0.5
        t0 = 0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        for t in np.linspace(t1, t2, n_per, endpoint=False):
            A1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            A2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            A3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
            B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
            out.append((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2)
    if not closed:
        out.append(P[-1])
    return np.array(out)


def resample(P, step, closed):
    if closed:
        P = np.vstack([P, P[:1]])
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    L = d[-1]
    s = np.arange(0, L if closed else L + 1e-9, step)
    if not closed and s[-1] < L - 1e-6:
        s = np.r_[s, L]
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], s, L


def smooth(P, passes, closed):
    P = P.copy()
    for _ in range(passes):
        if closed:
            P = (np.roll(P, 1, 0) + 2 * P + np.roll(P, -1, 0)) / 4
        else:
            P[1:-1] = (P[:-2] + 2 * P[1:-1] + P[2:]) / 4
    return P


def left_normals(P, closed):
    d = (np.roll(P, -1, 0) - np.roll(P, 1, 0)) if closed else np.gradient(P, axis=0)
    d /= np.linalg.norm(d, axis=1)[:, None]
    return np.c_[d[:, 1], -d[:, 0]]  # left of travel, seen from above (x east, z south)


def radius_profile(P, closed, span=12):
    n = len(P); r = np.full(n, np.inf)
    for i in range(n):
        a, b, c = P[(i - span) % n], P[i], P[(i + span) % n]
        if not closed and (i - span < 0 or i + span >= n):
            continue
        ab, bc, ca = np.linalg.norm(b - a), np.linalg.norm(c - b), np.linalg.norm(a - c)
        area2 = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        if area2 > 1e-6:
            r[i] = ab * bc * ca / (2 * area2)
    return r


STEP = 1.0
# ---------- the round course loop (inside rail) ----------
loop_raw = to_world(catmull_rom(T["roundCourse"]["points"], closed=True))
loop, s_loop, L_loop = resample(loop_raw, STEP, closed=True)
loop = smooth(loop, 6, True)
loop, s_loop, L_loop = resample(loop, STEP, closed=True)
# start exactly at the post
i0 = int(np.argmin(np.linalg.norm(loop, axis=1)))
loop = np.roll(loop, -i0, 0); loop[0] = [0, 0]
loop, s_loop, L_loop = resample(loop, STEP, closed=True)
n_loop = left_normals(loop, True)
r_loop = radius_profile(loop, True)

# ---------- round-mile spur (chute) ----------
spur = to_world(T["roundMileSpur"]["points"])
join_pt = to_world([T["roundMileSpur"]["joinsLoopAt"]])[0]
j = int(np.argmin(np.linalg.norm(loop - join_pt, axis=1)))
spur[-1] = loop[j]
spur_len = np.linalg.norm(spur[1] - spur[0])
togo_join = L_loop - s_loop[j]

# ---------- straight mile ----------
sm = to_world(T["straightMile"]["points"])
stalls_x = sm[0, 0]
past = T["straightMile"]["carriesOnPastPost"]

# ---------- track surfaces ----------
P_in = Polygon(loop)
loop_band = P_in.buffer(W, join_style=1, quad_segs=32).difference(P_in)
d = (spur[1] - spur[0]) / spur_len
nl = np.array([d[1], -d[0]])  # left of travel heading south = east
spur_band = Polygon([spur[0], spur[1], spur[1] + nl * W, spur[0] + nl * W])
straight_band = box(-past, 0, stalls_x + 12, W)
track = unary_union([loop_band, spur_band.difference(P_in), straight_band]).buffer(0.01).buffer(-0.01)

# ---------- zones ----------
Z = T["zones"]
c = Z["carnival"]["ellipsePx"]
ang = np.linspace(0, 2 * math.pi, 120, endpoint=False)
ell = to_world(np.c_[c["centre"][0] + c["rx"] * np.cos(ang), c["centre"][1] + c["ry"] * np.sin(ang)])
carnival = Polygon(ell).intersection(P_in.buffer(-Z["carnival"]["clearOfRail"]))
g = Z["grandstand"]
gzone = box(g["from"], W, g["to"], W + g["depth"])

pl = Z["planting"]
ring = track.buffer(pl["gap"] + pl["depth"], join_style=1).difference(track.buffer(pl["gap"], join_style=1))
bend_c = to_world([[215, 935]])[0]
stop = to_world([pl["westEndStopsAtPx"]])[0]
v = (stop - bend_c) / np.linalg.norm(stop - bend_c)
excl = [P_in.buffer(2),
        Polygon([bend_c, bend_c + v * 600, (pl["nearSideFrom"], bend_c[1] + 600), (pl["nearSideFrom"], 0.5 * W)]),
        box(stalls_x + 25, -500, stalls_x + 500, 500)]
planting = ring.difference(unary_union(excl))

# ---------- the stand ----------
mods = CAT["modules"]; bay = CAT["bay"]
seq = []
for item in ASM["order"]:
    for _ in range(item.get("repeat", 1)):
        seq.append((item["module"], item.get("mirror", False)))
cum = 0; spans = []
for name, mir in seq:
    Lm = mods[name]["bays"] * bay
    spans.append((name, mir, cum, cum + Lm)); cum += Lm
stand_len = cum
anc = ASM["anchor"]
tower_c = next(c0 + mods[n]["towerFromLeft"] for n, m, c0, c1 in spans if n == anc["module"])
front_z = W + ASM["setback"]
placed = []
for name, mir, c0, c1 in spans:
    m = mods[name]
    xe, xw = tower_c - c0, tower_c - c1  # left in elevation = east = +x
    placed.append({"module": name, "mirror": mir, "bays": m["bays"],
                   "xEast": round(xe, 2), "xWest": round(xw, 2),
                   "front": round(front_z, 2), "back": round(front_z + m["depth"], 2)})

# ---------- furlong markers ----------
def at_loop_togo(togo):
    s = (L_loop - togo) % L_loop
    k = int(round(s / STEP)) % len(loop)
    return loop[k], n_loop[k]

round_poles = []
for f in range(1, int(L_loop // F) + 1):
    p, n = at_loop_togo(f * F)
    round_poles.append({"furlongs": f, "at": [round(p[0], 2), round(p[1], 2)], "outward": [round(n[0], 3), round(n[1], 3)]})
spur_poles = []
for f in range(1, 12):
    togo = f * F
    if togo <= togo_join:
        continue
    back = togo - togo_join
    if back > spur_len + 1:
        break
    p = spur[1] - d * back
    spur_poles.append({"furlongs": f, "at": [round(p[0], 2), round(p[1], 2)]})
straight_poles = [{"furlongs": f, "at": [round(f * F, 2), 0.0]} for f in range(1, 9)]

# check against the board's round-course markers
checks = []
for k, pxy in T["boardMarkers"]["round"].items():
    f = int(k); w = to_world([pxy])[0]
    if f * F <= togo_join:
        p, _ = at_loop_togo(f * F)
    else:
        p = spur[1] - d * (f * F - togo_join)
    checks.append((f, float(w[1]), float(p[1])))

# bends
def bend_report():
    out = []; inb = False
    for i in range(len(loop)):
        b = r_loop[i] < 400
        if b and not inb: st = i; inb = True
        if (not b or i == len(loop) - 1) and inb:
            inb = False
            if i - st > 20:
                rr = r_loop[st:i]
                out.append({"from": round(float(L_loop - s_loop[st]), 1), "to": round(float(L_loop - s_loop[i - 1]), 1),
                            "minInsideRadius": round(float(rr.min()), 1), "turnsDegrees": None})
    return out
bends = bend_report()

# ---------- write course data ----------
def r2(P): return [[round(float(a), 2), round(float(b), 2)] for a, b in P]
SAMPLE = 5
course = {
    "id": "ascot",
    "name": "Ascot",
    "_about": "Built by tools/course/build_ascot_layout.py from courses/ascot-trace.json. Do not edit by hand; edit the trace or the assembly and re-run.",
    "units": "metres",
    "axes": "World plan: origin = winning post on the inside rail; x = east, z = south, y = up (right-handed, as glTF). Running is clockwise (right-handed): on the home straight horses run towards -x; inside rail on their right (-z), stands on their left (+z).",
    "direction": "clockwise",
    "trackWidth": W,
    "furlong": F,
    "winningPost": {"at": [0, 0], "line": "across the track along x = 0, from the inside rail (z 0) to the outer rail (z %g)" % W},
    "roundCourse": {
        "length": round(float(L_loop), 1),
        "insideRail": {"spacing": SAMPLE, "note": "Closed loop in running order from the post; distance to go at sample k = length - k*spacing.",
                       "points": r2(loop[::int(SAMPLE / STEP)])},
        "outerRailOffset": W,
        "furlongPoles": round_poles,
        "bends": bends
    },
    "roundMileSpur": {
        "from": r2([spur[0]])[0], "to": r2([spur[1]])[0],
        "length": round(float(spur_len), 1),
        "distanceToGoAtJoin": round(float(togo_join), 1),
        "startDistance": round(float(togo_join + spur_len), 1),
        "outerSide": "east",
        "furlongPoles": spur_poles
    },
    "straightMile": {
        "stalls": [round(float(stalls_x), 2), 0], "length": round(float(stalls_x), 1),
        "insideRail": "z = 0 (far side), from x %g to the post" % round(float(stalls_x), 1),
        "outerRail": "z = %g" % W,
        "carriesOnPastPost": past,
        "furlongPoles": straight_poles
    },
    "zones": {
        "carnival": {"polygon": r2(np.array(carnival.exterior.coords)[::2])},
        "grandstand": {"from": g["from"], "to": g["to"], "nearEdge": W, "farEdge": W + g["depth"]},
        "planting": {"gap": pl["gap"], "depth": pl["depth"],
                     "polygons": [r2(np.array(p.simplify(1.5).exterior.coords)) for p in
                                  (planting.geoms if planting.geom_type == "MultiPolygon" else [planting]) if p.area > 200]}
    },
    "grandstand": {
        "assembly": "courses/ascot-grandstand-assembly.json",
        "length": stand_len, "bays": int(stand_len / bay),
        "towerAt": [0, round(front_z, 2)],
        "frontLine": round(front_z, 2),
        "modules": placed
    }
}
json.dump(course, open(rp("courses/ascot.json"), "w"), indent=1)

# ---------- drawing ----------
os.makedirs(rp("reference/course/layout"), exist_ok=True)
COL = dict(bg="#a9c47f", inner="#b9d18f", track="#cfe3a2", rail="#ffffff", plant="#2f5a2c",
           carn="#7fb6e6", gz="#7fd8e6", stand="#efe3c4", stand2="#e0d0a8", edge="#6b5a3a",
           finish="#e055c8", ink="#1f2a1c", pole="#c0392b")


def add_poly(ax, geom, **kw):
    gs = geom.geoms if hasattr(geom, "geoms") else [geom]
    for p in gs:
        if p.is_empty: continue
        ax.add_patch(MplPoly(np.array(p.exterior.coords), closed=True, **kw))
        for hole in p.interiors:
            ax.add_patch(MplPoly(np.array(hole.coords), closed=True, fc=COL["inner"], ec="none", zorder=kw.get("zorder", 1) + 0.01))


def draw_base(ax, labels=True, stand_detail=False):
    for p in (track.geoms if hasattr(track, "geoms") else [track]):
        ax.add_patch(MplPoly(np.array(p.exterior.coords), closed=True, fc=COL["track"], ec="none", zorder=1.5))
    ax.add_patch(MplPoly(np.array(P_in.exterior.coords), closed=True, fc=COL["inner"], ec="none", zorder=1.6))
    add_poly(ax, planting, fc=COL["plant"], ec="none", zorder=2)
    add_poly(ax, carnival, fc=COL["carn"], ec="#3f7fbf", lw=0.8, alpha=0.55, zorder=2)
    add_poly(ax, gzone, fc=COL["gz"], ec="#2aa5b8", lw=0.8, alpha=0.35, zorder=2)
    for geom in [track]:
        for p in (geom.geoms if hasattr(geom, "geoms") else [geom]):
            ax.plot(*np.array(p.exterior.coords).T, color=COL["rail"], lw=1.1, zorder=4)
            for h in p.interiors:
                ax.plot(*np.array(h.coords).T, color=COL["rail"], lw=1.6, zorder=4)
    # finish line
    ax.plot([0, 0], [0, W], color=COL["finish"], lw=3, zorder=6, solid_capstyle="butt")
    # stand
    for i, m in enumerate(placed):
        x0, x1 = m["xWest"], m["xEast"]
        ax.add_patch(Rectangle((x0, m["front"]), x1 - x0, m["back"] - m["front"],
                               fc=COL["stand"] if i % 2 else COL["stand2"], ec=COL["edge"], lw=0.4, zorder=5))
        if m["module"] == "stair_bay":
            ax.add_patch(Rectangle((x0, m["front"] - 6), x1 - x0, 6, fc="#d3c6a6", ec=COL["edge"], lw=0.3, zorder=5))
    ax.plot(0, front_z + 6, marker="o", ms=5 if not stand_detail else 9, mfc="#a8915a", mec=COL["ink"], zorder=7)


def poles(ax, size=7):
    for p in straight_poles:
        x = p["at"][0]
        ax.plot([x, x], [-4, -12], color=COL["pole"], lw=1.4, zorder=6)
        ax.text(x, -16, f"{p['furlongs']}f", ha="center", va="bottom", fontsize=size, color=COL["ink"], zorder=8,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    for p in round_poles:
        if p["furlongs"] <= 3: continue
        if p["furlongs"] * F > togo_join and p["furlongs"] < 8: continue  # the chute carries these
        x, z = p["at"]; n = p["outward"]
        ax.plot([x - n[0] * 4, x - n[0] * 12], [z - n[1] * 4, z - n[1] * 12], color=COL["pole"], lw=1.4, zorder=6)
        f = p["furlongs"]; lab = f"{f // 8}m{f % 8}f" if f >= 8 and f % 8 else (f"{f // 8}m" if f % 8 == 0 else f"{f}f")
        ax.text(x - n[0] * 28, z - n[1] * 28, lab, ha="center", va="center", fontsize=size, color=COL["ink"], zorder=8,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    for p in spur_poles:
        x, z = p["at"]
        ax.plot([x - 4, x - 12], [z, z], color=COL["pole"], lw=1.4, zorder=6)
        ax.text(x - 30, z, f"{p['furlongs']}f", ha="center", va="center", fontsize=size, color=COL["ink"], zorder=8,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))


# 1) clean top-down plan
xmin, zmin, xmax, zmax = unary_union([track, gzone]).buffer(70).bounds
fig = plt.figure(figsize=(18, 18 * (zmax - zmin) / (xmax - xmin) + 1.2), dpi=110)
ax = fig.add_axes([0.02, 0.02, 0.96, 0.9])
ax.set_facecolor(COL["bg"]); ax.set_aspect("equal"); ax.set_xlim(xmin, xmax); ax.set_ylim(zmax, zmin)
ax.set_xticks([]); ax.set_yticks([])
draw_base(ax); poles(ax)
# direction arrows
for s_ in np.linspace(0.08, 0.92, 9):
    k = int(s_ * len(loop)); p = loop[k] + n_loop[k] * W / 2; q = loop[k + 12] + n_loop[k + 12] * W / 2
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="-|>", color="#4b6b2f", lw=1.2), zorder=7)
for x in (1300, 1000):
    ax.annotate("", xy=(x - 60, W / 2), xytext=(x, W / 2), arrowprops=dict(arrowstyle="-|>", color="#4b6b2f", lw=1.2), zorder=7)
txt = dict(fontsize=10, color=COL["ink"], zorder=9)
ax.text(np.mean([carnival.bounds[0], carnival.bounds[2]]), carnival.centroid.y, "Inner crowd & carnival", ha="center", va="center", **txt)
ax.text(700, W + g["depth"] - 18, "Grandstand zone: crowd, marquees, planting", ha="center", **txt)
ax.text(tower_c - stand_len / 2 + 0, front_z + 40, "", **txt)
ax.text(0, front_z + 52, f"Main stand {stand_len:.0f} m ({stand_len / F:.2f}f), {int(stand_len / bay)} bays\nclock tower faces the post",
        ha="center", va="top", fontsize=9, color=COL["ink"], zorder=9)
ax.text(-8, W + 10, "Winning post", ha="right", va="center", fontsize=9, color=COL["finish"], zorder=9, fontweight="bold")
ax.text(stalls_x + 8, W / 2, "Straight mile\nstalls", ha="left", va="center", fontsize=9, color=COL["ink"], zorder=9)
ax.text(spur[0][0] + 40, spur[0][1] + 12, "Round mile\nstart", ha="left", va="top", fontsize=9, color=COL["ink"], zorder=9)
# scale bar and north
sx, sz = xmin + 60, zmin + 60
ax.add_patch(Rectangle((sx, sz), F, 8, fc=COL["ink"], zorder=9))
ax.text(sx + F / 2, sz + 14, "1 furlong (201 m)", ha="center", va="top", fontsize=9, zorder=9)
ax.annotate("N", xy=(xmax - 60, zmin + 40), xytext=(xmax - 60, zmin + 130), ha="center", fontsize=12,
            arrowprops=dict(arrowstyle="-|>", color=COL["ink"], lw=1.5), zorder=9)
min_r = min(b["minInsideRadius"] for b in bends) if bends else 0
fig.suptitle("Ascot - top-down layout from the inside-rail trace (clockwise, track 30 m wide)", fontsize=15, x=0.02, ha="left", y=0.985)
fig.text(0.02, 0.945,
         f"Round course {L_loop:.0f} m ({L_loop / F:.2f}f) round the inside rail. Straight mile {stalls_x:.0f} m. "
         f"Round-mile chute start {togo_join + spur_len:.0f} m ({(togo_join + spur_len) / F:.2f}f) out. "
         "Red ticks: furlong poles, measured along the inside rail. Dark green: planting belt.",
         fontsize=10, ha="left")
fig.savefig(rp("reference/course/layout/ascot-layout-topdown.png"))
plt.close(fig)

# 2) trace over the board
board = Image.open(rp(T["image"]))
bw = T["imageWidth"]; bh = board.size[1] * bw / board.size[0]
fig = plt.figure(figsize=(16, 16 * bh / bw), dpi=90)
ax = fig.add_axes([0, 0, 1, 1]); ax.imshow(board, extent=[0, bw, bh, 0], alpha=0.75); ax.set_axis_off()
for geom in [track]:
    for p in (geom.geoms if hasattr(geom, "geoms") else [geom]):
        ax.fill(*to_px(np.array(p.exterior.coords)).T, fc="#fff6", ec="none")
ax.plot(*to_px(np.vstack([loop, loop[:1]])).T, color="#ffea00", lw=2.2, label="inside rail (traced)")
ax.plot(*to_px(np.array(spur)).T, color="#ffea00", lw=2.2)
ax.plot(*to_px(np.vstack([loop + n_loop * W, (loop + n_loop * W)[:1]])).T, color="#ff8c00", lw=1.2, label="outer rail, 30 m")
for p in round_poles + spur_poles:
    q = to_px([p["at"]])[0]; ax.plot(*q, "o", ms=6, mfc="#ff2d2d", mec="white")
    ax.text(q[0] - 14, q[1], str(p["furlongs"]), color="white", fontsize=9, ha="right", va="center", fontweight="bold")
for f, (bx, by) in T["boardMarkers"]["round"].items():
    ax.plot(bx, by, "s", ms=7, mfc="none", mec="#00e5ff", mew=2)
for i, m in enumerate(placed):
    q0 = to_px([[m["xWest"], m["front"]]])[0]; q1 = to_px([[m["xEast"], m["back"]]])[0]
    ax.add_patch(Rectangle(q0, q1[0] - q0[0], q1[1] - q0[1], fc="#f2e6c8", ec="#5a4a2a", lw=0.5))
ax.legend(loc="lower left", fontsize=11)
fig.savefig(rp("reference/course/layout/ascot-layout-on-board.jpg"), pil_kwargs={"quality": 85})
plt.close(fig)

# 3) stand close-up
x_lo, x_hi = min(m["xWest"] for m in placed) - 20, max(m["xEast"] for m in placed) + 20
fig = plt.figure(figsize=(20, 4.6), dpi=110)
ax = fig.add_axes([0.01, 0.06, 0.98, 0.78])
ax.set_facecolor(COL["bg"]); ax.set_aspect("equal"); ax.set_xlim(x_hi, x_lo); ax.set_ylim(front_z + 40, -12)
ax.set_xticks([]); ax.set_yticks([])
draw_base(ax, stand_detail=True)
for i, m in enumerate(placed):
    xm = (m["xWest"] + m["xEast"]) / 2
    lab = {"stair_bay": "steps", "veranda_wing_raised": "veranda\nraised", "veranda_wing": "veranda", "end_pavilion": "end\npav.",
           "three_storey_block": "3-storey", "grand_pavilion": "grand\npavilion", "window_block": "window\nblock",
           "ironwork_bay": "iron", "clock_centre": "CLOCK CENTRE", "veranda_low": "low", "porch": "porch"}.get(m["module"], m["module"])
    if m["module"] == "stair_bay": continue
    ax.text(xm, (m["front"] + m["back"]) / 2, lab, ha="center", va="center", fontsize=6.5, rotation=0, color=COL["ink"], zorder=9)
    ax.text(xm, m["back"] + 3, str(m["bays"]), ha="center", va="top", fontsize=6, color="#555", zorder=9)
for x in range(0, int(x_hi), 50):
    ax.text(x, -9, f"{x} m", ha="center", fontsize=7, zorder=9)
ax.text(0, W + 2, "post", ha="center", va="top", fontsize=8, color=COL["finish"], zorder=9, fontweight="bold")
fig.suptitle(f"Main stand: {len(placed)} modules, {int(stand_len / bay)} bays of 3.5 m = {stand_len:.1f} m; "
             f"{tower_c:.0f} m east of the clock tower, {stand_len - tower_c:.0f} m west. Viewed from above, east on the left as seen from the track; "
             "small figures = bays per module.", fontsize=10, x=0.01, ha="left", y=0.97)
fig.savefig(rp("reference/course/layout/ascot-stand-plan.png"))
plt.close(fig)

print(f"loop {L_loop:.1f} m = {L_loop / F:.2f}f; spur {spur_len:.1f} m; join at {togo_join:.1f} m to go; chute start {togo_join + spur_len:.1f} m = {(togo_join + spur_len) / F:.2f}f")
print(f"straight mile {stalls_x:.1f} m = {stalls_x / F:.2f}f")
print("bends:", bends)
print("board marker check (furlong, board z, traced z):", [(f, round(a), round(b)) for f, a, b in checks])
print(f"stand {stand_len} m, {len(placed)} modules, east {tower_c} m / west {stand_len - tower_c} m of tower; front z {front_z}")
