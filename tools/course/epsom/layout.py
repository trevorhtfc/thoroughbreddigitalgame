"""Epsom, phase 1: the course plan, as data and drawings.

Owner, 18 Nov 2026: "Please can you make a start on Epsom. Don't worry about grandstand yet as we will design those bespoke
but if you can study the tool and build the track itself that would be good." Built the way York and Goodwood were
(claude/york-course-handover.md, claude/goodwood-course-handover.md): the plan, then the track in the race view.

Sources (DRAFT, interpretive)
  - The shape: At The Races' Epsom diagram, traced by trace_diagram.py into reference/epsom/diagram-trace.json. The
    diagram is close to scale (its labelled starts sit within a few per cent of their distances once one scale is
    fitted, printed by main()), but it is a drawing, not a survey: OpenStreetMap's outline should replace it when it
    can be fetched (the workspace couldn't reach openstreetmap.org, and the owner's browser wasn't connected).
  - The heights: not measured. A profile drawn from what the racing press says (below), to be replaced by the real
    ground (AWS Terrain Tiles, as Goodwood) when it can be fetched.

How Epsom races (course guides, 18 Nov 2026):
  - left-handed and U-shaped; the Derby course (1m4f) "starts with a lung-bursting climb before it sweeps left-handed
    and begins a rapid descent through the famous Tattenham Corner" (Great British Racing); "they turn right then left"
    early on (At The Races);
  - three roughly equal half-miles: up a steep hill, down a steep hill on the turn, then the straight on a right-to-left
    camber (Telegraph); the climb is about 150 ft in the first half mile (geegeez), "the height of Nelson's Column";
  - the straight (just under half a mile from Tattenham Corner) is mainly downhill, with a final sharp rise in the
    last furlong or so; it is cambered towards the inside (far) rail;
  - the 5f course is straight and downhill for its first 3.5f, adjoining the round course at the entrance to the
    straight ("the fastest in the world"); 6f and 7f start in chutes off the top of Tattenham Corner.

World axes, as York (left-handed): metres, y up, origin = the winning post on the inside rail; on the home straight the
horses run towards -x. The inside rail (z = 0) is on the horses' LEFT, the track runs to z = -trackWidth on their right,
the stands are beyond (z < -trackWidth, north); the infield (the Hill) is +z.

Writes  courses/epsom-draft.json            the layout as data (routes, rails, bends, heights, starts)
        reference/epsom/plan-draft.png       the plan, north up, beside the traced diagram
        reference/epsom/profiles-draft.png   the ground under every route, post on the right

  python3 tools/course/epsom/layout.py
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import LineString, Point

REPO = Path(__file__).resolve().parents[3]
F = 201.168
YD = 0.9144
TRACE = json.loads((REPO / "reference/epsom/diagram-trace.json").read_text())

# ---------------------------------------------------------------- the choices (change here)
TRACK_W = 26.0          # the game's track width (the diagram draws about 40 m)
RUN_OUT = 100.0         # how far the routes carry on past the post (the diagram's straight runs about 165 m past it)
EASE_M = 130.0          # each route's middle line is averaged over this many metres (twice): it turns the diagram's
                        # hard corner at the foot of Tattenham Corner into a raceable bend (tightest about 130 m radius)
                        # and softens the joins where the 6f and 7f chutes meet the course
STEP = 5.0              # each route's rail sampled every STEP metres
CAMBER = 1.0            # the home straight's fall from the outer (stands') rail to the inside (far) rail, metres
SCALE_FROM = "5f"       # the diagram's scale (metres per pixel) is taken from this start: the straight course is the one
                        # line the easing can't change, and its scale agrees with the Derby start's within 1% (all six
                        # are printed by main(); the chutes come out shorter because the easing cuts their corners)
TRIM_X = {"round": 556}  # the diagram's top arm flicks up beyond the Derby start (a flourish): the trace is cut there and
                        # the line carried on straight instead
EXTEND = 100.0          # each route's line is carried on this far beyond the diagram's end of it (the stalls' room)

TRIPS = {"5f": 5 * F, "6f": 6 * F, "7f": 7 * F, "1m114y": 8 * F + 114 * YD, "1m2f18y": 10 * F + 18 * YD,
         "1m4f10y": 12 * F + 10 * YD}
ROUTE = {"5f": "straight", "6f": "six", "7f": "seven", "1m114y": "round", "1m2f18y": "round", "1m4f10y": "round"}
DIAGRAM = {"5f": "the straight course's far end, beyond where Tattenham Corner joins it",
           "6f": "the top of the outer (left) chute at Tattenham Corner", "7f": "the top of the inner chute at Tattenham Corner",
           "1m114y": "the top arm, by the 'Uphill' mark", "1m2f18y": "the top arm, two-thirds of the way out",
           "1m4f10y": "the top arm's far end (the Derby start)"}

# The ground under the round course (metres against the post, by metres to go): a drawing from the press's words, not a
# survey. Up about 45 m from the Derby start in the first half mile (to about 1m out), level over the top, down about 30 m
# round Tattenham Corner, on down the straight to a dip about a furlong out, then up again to the post.
ROUND_H = [(-120, 0.6), (0, 0.0), (100, -1.2), (200, -2.2), (300, -1.6), (500, 2.0), (700, 7.0), (850, 11.5), (1000, 16.5),
           (1150, 22.5), (1270, 27.5), (1380, 30.0), (1500, 30.2), (1620, 28.8), (1750, 24.5), (1900, 15.0), (2100, 2.0),
           (2300, -9.5), (2450, -15.5), (2600, -18.0)]
# The straight course beyond where the round course joins it: rising back towards the 5f start ("downhill for the first
# three and a half furlongs")
STRAIGHT_FAR_H = [(1006, 14.0), (1150, 16.0)]
CHUTE_RISE = 0.012      # the 6f and 7f chutes keep rising gently back from where they leave the course (1.2%)

# ---------------------------------------------------------------- polylines with arc length
class Line:
    def __init__(self, pts):
        p = np.array(pts, float)
        keep = [0] + [i for i in range(1, len(p)) if np.hypot(*(p[i] - p[i - 1])) > 1e-6]
        p = p[keep]
        seg = np.hypot(*np.diff(p, axis=0).T)
        self.p, self.s = p, np.concatenate([[0], np.cumsum(seg)])
        self.L = self.s[-1]
    def at(self, s):
        s = min(max(s, 0.0), self.L)
        i = min(np.searchsorted(self.s, s, side="right") - 1, len(self.p) - 2)
        k = (s - self.s[i]) / max(1e-9, self.s[i + 1] - self.s[i])
        d = self.p[i + 1] - self.p[i]
        return self.p[i] + d * k, d / (np.hypot(*d) or 1)
    def project(self, q):
        return LineString(self.p).project(Point(q))

def px(p):
    """diagram pixels (y down) to a y-up frame, still in pixels"""
    a = np.array(p, float); a[..., 1] *= -1; return a

def ease(p, k):
    """resample a pixel line every pixel, then a running average over k pixels, twice (ends carried on straight)"""
    L = Line(p); q = np.array([L.at(s)[0] for s in np.arange(0, L.L, 1.0)])
    for _ in range(2):
        pad = np.vstack([q[:1] - (q[1] - q[0]) * np.arange(k // 2, 0, -1)[:, None], q,
                         q[-1:] + (q[-1] - q[-2]) * np.arange(1, k // 2 + 1)[:, None]])
        q = np.stack([np.convolve(pad[:, 0], np.ones(k) / k, mode="valid"), np.convolve(pad[:, 1], np.ones(k) / k, mode="valid")], 1)
    return q

# ---------------------------------------------------------------- the diagram's middle lines, eased; the scale
POST_PX = px(TRACE["post"])
NORTH_PX = px(TRACE["north"]); NORTH_PX /= np.hypot(*NORTH_PX)
EAST_PX = np.array([NORTH_PX[1], -NORTH_PX[0]])           # east: north turned a right angle clockwise

def mid_lines(scale):
    k = int(EASE_M / scale) | 1
    return {name: Line(ease(px([q for q in p if q[0] <= TRIM_X.get(name, 1e9)]), k)) for name, p in TRACE["routes"].items()}

def tick_px(t): return px(np.mean(TRACE["ticks"][t], axis=0))

def fitted_scale():
    """metres per pixel: each start's labelled distance over its traced distance to the post (and their median)"""
    sc = 2.55
    for _ in range(3):                                      # the easing depends a little on the scale
        M = mid_lines(sc)
        each = {t: TRIPS[t] / (M[ROUTE[t]].project(POST_PX) - M[ROUTE[t]].project(tick_px(t))) for t in TRIPS}
        sc = float(np.median(list(each.values())))
    return sc, each

SC_MEDIAN, SC_EACH = fitted_scale()
SC = SC_EACH[SCALE_FROM]
MID_PX = mid_lines(SC)
def extended(p):
    d = p[0] - p[1]; d /= np.hypot(*d)
    return np.vstack([p[0] + d * EXTEND, p])
MID = {k: Line(extended((v.p - POST_PX) * SC)) for k, v in MID_PX.items()}   # metres, a y-up frame, the post's middle line at 0
TICK = {t: (tick_px(t) - POST_PX) * SC for t in TRIPS}

# ---------------------------------------------------------------- the rails: the middle line moved half a track to the left
def rail_of(line):
    pts = []
    for s in np.arange(0, line.L, 1.0):
        p, t = line.at(s)
        pts.append(p + np.array([-t[1], t[0]]) * TRACK_W / 2)  # the horses' left (left-handed: the inside rail)
    return Line(pts)

RAIL = {k: rail_of(v) for k, v in MID.items()}
STR = RAIL["straight"]
_p0, RUN = STR.at(STR.project(np.array([0.0, TRACK_W / 2])))
POST = _p0                                                # the winning post, on the inside rail
XH = -RUN                                                 # world x: against the running direction on the home straight
ZH = np.array([-RUN[1], RUN[0]])                          # world z: the horses' left (the infield)
def world(p):
    q = np.asarray(p) - POST
    return [round(float(q @ XH), 2), round(float(q @ ZH), 2)]
def world_dir(v):
    return [round(float(np.asarray(v) @ XH), 4), round(float(np.asarray(v) @ ZH), 4)]
def en_dir(v):
    """a frame direction as (east, north)"""
    return np.array([np.asarray(v) @ EAST_PX, np.asarray(v) @ NORTH_PX])

# ---------------------------------------------------------------- heights
H_ROUND = PchipInterpolator([d for d, _ in ROUND_H], [h for _, h in ROUND_H], extrapolate=True)

def height(name, d):
    """the ground under the middle of the track, d metres to go on route 'name', against the post"""
    if name == "round" or d <= JOIN_STRAIGHT:
        return float(H_ROUND(d))
    if name == "straight":
        h0 = float(H_ROUND(JOIN_STRAIGHT)); (d1, h1), (d2, h2) = STRAIGHT_FAR_H
        if d <= d1: return h0 + (h1 - h0) * (d - JOIN_STRAIGHT) / (d1 - JOIN_STRAIGHT)
        return h1 + (h2 - h1) * (d - d1) / (d2 - d1)
    m = MERGE[name]
    if d <= m: return float(H_ROUND(d))
    return float(H_ROUND(m)) + CHUTE_RISE * (d - m)

def samples(name):
    """[(rail point, metres to go)] every STEP m, index 0 = the end of the run-out past the post (as York and Goodwood)"""
    L = RAIL[name]; sp = L.project(POST)
    s_end = min(L.L, sp + RUN_OUT)
    return [(L.at(s)[0], round(float(sp - s), 2)) for s in np.arange(s_end, -1e-6, -STEP)]

def bends_of(samp):
    """the bends for the race engine: [metres to go at the start, at the end, degrees turned], left turns (towards the
    rail on a left-handed course) positive; samp in index order (past the post first)"""
    pts = np.array([s[0] for s in samp])[::-1]; ds = np.array([s[1] for s in samp])[::-1]   # running order
    run = np.diff(pts, axis=0)
    hd = np.unwrap(np.arctan2(run[:, 1], run[:, 0]))
    per = np.convolve(np.gradient(hd), np.ones(5) / 5, mode="same")
    lim = math.radians(0.35) * STEP / 5.0
    out, i, n = [], 0, len(hd)
    while i < n:
        if abs(per[i]) > lim:
            sgn = np.sign(per[i]); j = i
            while j < n and abs(per[j]) > lim and np.sign(per[j]) == sgn: j += 1
            turn = math.degrees(hd[min(j, n - 1)] - hd[i])      # anticlockwise (left) positive
            if abs(turn) > 4 and ds[min(j, n - 1)] > 0:
                out.append([round(float(ds[i]), 1), round(float(max(ds[min(j, n - 1)], 0.0)), 1), round(turn, 1)])
            i = j + 1
        else:
            i += 1
    return out

def first_meet(a, b="round"):
    """metres to go (on route a) where a's rail first comes within 1 m of b's: where a chute joins"""
    La, Lb = RAIL[a], RAIL[b]; sp = La.project(POST)
    for s in np.arange(0, La.L, 2.0):
        p, _ = La.at(s)
        if np.hypot(*(Lb.at(Lb.project(p))[0] - p)) < 1.0:
            return round(float(sp - s), 1)
    return None

JOIN_STRAIGHT = first_meet("round", "straight")          # where Tattenham Corner meets the straight course
MERGE = {"six": first_meet("six"), "seven": first_meet("seven")}

def min_radius(samp, lo, hi):
    pts = np.array([s[0] for s in samp]); ds = np.array([s[1] for s in samp])
    best = (1e9, None)
    for i in range(2, len(pts) - 2):
        if not (lo <= ds[i] <= hi): continue
        a, b, c = pts[i - 2], pts[i], pts[i + 2]
        ab, bc, ca = np.hypot(*(b - a)), np.hypot(*(c - b)), np.hypot(*(a - c))
        area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2
        if area > 1e-6:
            R = ab * bc * ca / (4 * area)
            if R < best[0]: best = (R, ds[i])
    return round(best[0]), best[1]

# ---------------------------------------------------------------- build
def main():
    routes, starts, profiles = {}, {}, {}
    for name in ["straight", "six", "seven", "round"]:
        samp = samples(name)
        ds = np.array([s[1] for s in samp])
        h = np.array([height(name, d) for d in ds])
        profiles[name] = (ds, h)
        routes[name] = {
            "d0": float(ds[0]), "spacing": STEP,
            "insideRail": [world(s[0]) for s in samp],
            "bends": bends_of(samp),
            "heights": {"from": float(ds[0]), "spacing": STEP, "h": [round(float(v), 2) for v in h],
                        "note": "ground height (m, against the post's) every 'spacing' metres to go from 'from', across the middle "
                                "of the track: ESTIMATED from the course guides' descriptions, not measured"},
            "length": float(ds[-1]),
        }
    for trip, dist in TRIPS.items():
        r = ROUTE[trip]; L = RAIL[r]; sp = L.project(POST)
        if dist > sp: raise SystemExit(f"{trip} ({dist:.0f} m) is beyond the {r} route ({sp:.0f} m)")
        p, t = L.at(sp - dist)
        mid_p = MID[r].at(MID[r].project(p))[0]
        off = float(np.hypot(*(mid_p - TICK[trip])))
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": world(p), "running": world_dir(t),
                        "onStraight": r == "straight", "groundM": round(height(r, dist), 1),
                        "diagram": DIAGRAM[trip], "fromDiagramMark": round(off, 1)}
    samp_r = samples("round")
    checks = {
        "metres per diagram pixel (used; from the %s)" % SCALE_FROM: round(SC, 3), "median of the starts' scales": round(SC_MEDIAN, 3),
        "each start's own scale (m/px)": {t: round(v, 3) for t, v in SC_EACH.items()},
        "each start's distance from its diagram mark, m": {t: s["fromDiagramMark"] for t, s in starts.items()},
        "Tattenham Corner meets the straight course, m from the post (run-in from there)": JOIN_STRAIGHT,
        "6f chute joins the course, m from the post": MERGE["six"], "7f chute joins the course, m from the post": MERGE["seven"],
        "tightest radius on the round course, m (at m to go)": min_radius(samp_r, 0, 3000),
        "round course: bends": routes["round"]["bends"],
        "round course: climb from the Derby start to the top, m": round(float(H_ROUND(1450) - H_ROUND(TRIPS["1m4f10y"])), 1),
        "round course: fall from the top to the dip, m": round(float(H_ROUND(1450) - H_ROUND(200)), 1),
    }
    north = world_dir(NORTH_PX)
    poles = [{"furlongs": k, "at": world(STR.at(STR.project(POST) - k * F)[0])} for k in range(1, 6)]
    out = {
        "id": "epsom", "name": "Epsom Downs, draft",
        "status": "DRAFT, phase 1 (the course plan), 18 Nov 2026: traced from At The Races' diagram; heights estimated. Swap in "
                  "OpenStreetMap's outline and the real ground when they can be fetched.",
        "_about": "Built by tools/course/epsom/layout.py from reference/epsom/diagram-trace.json (trace_diagram.py). Don't edit by "
                  "hand: change the choices at the top of the script.",
        "axes": "As York: origin = winning post on the inside rail; y up. On the home straight the horses run towards -x. LEFT-handed: "
                "the inside rail (z = 0) is on the horses' left, the track runs to z = -trackWidth on their right; on the home "
                "straight the stands are beyond (z < -trackWidth, north) and the infield (the Hill) is +z.",
        "direction": "anticlockwise (left-handed)", "hand": -1,
        "compass": {"north": north, "note": "the direction of north in world x, z"},
        "trackWidth": TRACK_W, "furlong": F, "runOut": RUN_OUT, "camber": CAMBER,
        "measured": {"checks": checks},
        "routes": routes,
        "routesNote": "Each route is its inside rail sampled every 'spacing' metres, from d0 (metres to go, negative = the run-out past "
                      "the post) back to its far end; 'bends' for the race engine as [metres to go at the start, at the end, degrees "
                      "turned (positive = left, towards the rail)]; 'heights' the ground along it. straight: 5f. six: 6f, from the "
                      "outer chute at the top of Tattenham Corner. seven: 7f, from the inner chute. round: 1m114y, 1m2f18y, 1m4f10y "
                      "(the Derby course).",
        "starts": starts,
        "furlongPoles": poles,
    }
    (REPO / "courses/epsom-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    print(json.dumps(checks, indent=1))
    for t, s in starts.items():
        print(f"  {t:8s} {s['route']:8s} {s['distance']:7.1f} m  {s['fromDiagramMark']:5.1f} m from the mark  ground {s['groundM']:6.1f}")
    for n, r in routes.items():
        print(f"  route {n:8s} {r['length']:7.1f} m  bends {r['bends']}")
    draw(out, profiles)
    return out

# ---------------------------------------------------------------- drawings
INK, MUTED, POSTC = "#2b2b2b", "#6b6b6b", "#c0392b"
ROUTE_C = {"straight": "#2f5d8a", "six": "#b03a8a", "seven": "#b5651d", "round": "#1d1d1d"}

def draw(c, profiles):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    from shapely.ops import unary_union
    from shapely.geometry import Polygon
    # turn the frame so north is up
    rot = np.array([EAST_PX, NORTH_PX])                       # rows: east, north
    def en(p): return (np.asarray(p) @ rot.T) if np.ndim(p) > 1 else rot @ np.asarray(p)
    fig, axs = plt.subplots(1, 2, figsize=(17, 8.5), dpi=130, gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axs[0]
    strips = []
    for name in ["straight", "six", "seven", "round"]:
        L = RAIL[name]; sp = L.project(POST); pts, outer = [], []
        for s in np.arange(0, min(L.L, sp + RUN_OUT), 2.0):
            p, t = L.at(s); pts.append(p); outer.append(p + np.array([t[1], -t[0]]) * TRACK_W)
        strips.append(Polygon(pts + outer[::-1]).buffer(0))
    turf = unary_union(strips)
    for g in ([turf] if turf.geom_type == "Polygon" else turf.geoms):
        ax.add_patch(MP(en(np.array(g.exterior.coords)), closed=True, fc="#5f9a48", ec="#2e5a22", lw=0.6, alpha=0.9))
    for name in ["round", "seven", "six", "straight"]:
        L = RAIL[name]; sp = L.project(POST)
        q = en(np.array([L.at(s)[0] for s in np.arange(0, min(L.L, sp + RUN_OUT), 4.0)]))
        ax.plot(q[:, 0], q[:, 1], color=ROUTE_C[name], lw=1.0)
    for t, s in c["starts"].items():
        L = RAIL[s["route"]]; p, tt = L.at(L.project(POST) - s["distance"])
        a, b = en(p), en(p + np.array([tt[1], -tt[0]]) * TRACK_W)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="white", lw=2.2, solid_capstyle="butt")
        m = en(TICK[t]); ax.plot(*m, marker="x", ms=6, color="#d4a017", mew=1.6)
        off = {"5f": (-6, -16), "6f": (10, -4), "7f": (8, 6), "1m114y": (-20, 10), "1m2f18y": (-10, -18), "1m4f10y": (-30, 12)}[t]
        ax.annotate(t, a, xytext=off, textcoords="offset points", fontsize=9, fontweight="bold", color=ROUTE_C[s["route"]],
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))
    pe = en(POST); ax.plot(*pe, marker="o", ms=8, color=POSTC, mec="white", zorder=6)
    ax.annotate("winning post", pe, xytext=(-30, 14), textcoords="offset points", fontsize=9, color=POSTC, fontweight="bold")
    for k in range(1, 5):
        p = en(STR.at(STR.project(POST) - k * F)[0]); ax.plot(*p, marker="o", ms=2.5, color=INK)
        ax.annotate(f"{k}f", p, xytext=(-4, 6), textcoords="offset points", fontsize=7, color=MUTED)
    L = RAIL["round"]; sp = L.project(POST)
    for dd in [400, 1100, 1600, 2100]:
        p, t = L.at(sp - dd); a = en(p); b = en(p + t * 60)
        ax.annotate("", b, a, arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
    tc = en(L.at(sp - 880)[0]); ax.annotate("Tattenham Corner", tc, xytext=(-110, -4), textcoords="offset points", fontsize=8.5, color=INK, style="italic")
    st = en(POST + np.array([0, -1.0]) * 90 * 0); ax.text(*(en(POST + np.array([-240.0, -70.0]))), "stands (north side)", fontsize=8.5, color=MUTED)
    ax.set_aspect("equal"); ax.autoscale_view(); ax.margins(0.08)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.plot([xl[0] + 40, xl[0] + 240], [yl[0] + 40, yl[0] + 40], color=INK, lw=2); ax.text(xl[0] + 140, yl[0] + 52, "200 m", ha="center", fontsize=7.5)
    ax.annotate("N", (xl[1] - 60, yl[0] + 150), xytext=(xl[1] - 60, yl[0] + 60), ha="center", fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Epsom: course plan, DRAFT 18 Nov 2026 (north up)\nleft-handed; traced from At The Races' diagram, one scale "
                 f"fitted ({SC:.2f} m per pixel); gold x = the diagram's start marks", fontsize=10, loc="left", color=INK)
    # the diagram's own frame, for comparing with the picture he sent (north down, as At The Races draw it)
    ax = axs[1]
    for name, p in TRACE["routes"].items():
        a = np.array(p, float); ax.plot(a[:, 0], -a[:, 1], color="#bbbbbb", lw=5, solid_capstyle="round")
    for name, L in MID_PX.items():
        ax.plot(L.p[:, 0], L.p[:, 1], color=ROUTE_C[name], lw=1.2)
    for t in TRIPS:
        m = tick_px(t); ax.plot(*m, marker="x", ms=7, color="#d4a017", mew=1.8); ax.annotate(t, m, xytext=(4, 6), textcoords="offset points", fontsize=8)
    ax.plot(*POST_PX, marker="o", ms=7, color=POSTC)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("The trace, in the diagram's own frame (north down): grey = the diagram's track thinned to its middle;\n"
                 "colours = each route's middle line after easing", fontsize=10, loc="left", color=INK)
    fig.tight_layout(); fig.savefig(REPO / "reference/epsom/plan-draft.png", facecolor="white"); plt.close(fig)

    # the ground under each route
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), dpi=130)
    panels = [("round", ["1m114y", "1m2f18y", "1m4f10y"], "The Derby course (1m4f10y; 1m114y, 1m2f18y on it): up the hill, round and down Tattenham Corner, the straight"),
              ("seven", ["6f", "7f"], "7f from the inner chute (6f from the outer chute, the same fall): down Tattenham Corner, the straight"),
              ("straight", ["5f"], "5f: the straight course, downhill for three and a half furlongs, then up to the post")]
    for ax, (name, trips, title) in zip(axs, panels):
        ds, h = profiles[name]
        dists = [c["starts"][t]["distance"] for t in trips]
        top = max(dists) + 60
        m = (ds <= top) & (ds >= -40)
        ax.fill_between(-ds[m] / F, -100, h[m], color="#cfd9b0")
        ax.plot(-ds[m] / F, h[m], color=ROUTE_C[name], lw=1.6)
        if name == "seven":
            d6, h6 = profiles["six"]; m6 = (d6 <= c["starts"]["6f"]["distance"] + 60) & (d6 >= -40)
            ax.plot(-d6[m6] / F, h6[m6], color=ROUTE_C["six"], lw=1.0, ls="--")
        for t, dd in zip(trips, dists):
            ax.axvline(-dd / F, color=MUTED, lw=0.6, ls=":")
            ax.text(-dd / F, h[m].max() + 1.5, t, ha="center", fontsize=8, fontweight="bold", color=INK)
        ax.axvline(0, color=POSTC, lw=1); ax.text(0.05, h[m].min() - 2, "post", color=POSTC, fontsize=8)
        for b in c["routes"][name]["bends"]:
            if b[0] <= top: ax.axvspan(-b[0] / F, -b[1] / F, color="#000000", alpha=0.06)
        ax.set_ylim(h[m].min() - 4, h[m].max() + 5); ax.set_xlim(-top / F, 0.3)
        ax.set_ylabel("m against the post", fontsize=8); ax.tick_params(labelsize=7)
        ax.set_title(title, fontsize=9, loc="left")
    axs[-1].set_xlabel("furlongs to go (grey bands: bends). Heights ESTIMATED from the course guides, not measured", fontsize=8)
    fig.tight_layout(); fig.savefig(REPO / "reference/epsom/profiles-draft.png", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    main()
