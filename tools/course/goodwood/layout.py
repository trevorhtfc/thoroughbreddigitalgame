"""Goodwood, phase 1: the course plan, as data and drawings, from the real layout and the real ground.

Owner, 17 Nov 2026: build Goodwood as a detailed flagship course, the way York was built (claude/york-course-handover.md):
the course plan first, then the track in the race view, the perimeter, the stands. "I would urge a good study of
topography to get this going."

Sources
  - reference/goodwood/osm-goodwood.json: OpenStreetMap's outline of the turf (relation 1197801: one outer ring and two
    holes, the island at the foot of the loop and the infield of the top loop) and the stands. (c) OpenStreetMap
    contributors, ODbL.
  - reference/goodwood/dem-course-20m.json: the ground's height every 20 m (AWS Terrain Tiles, from LIDAR and open DEMs).
  - At The Races' course diagram (exact start distances; uphill and downhill marks), used to check, kept out of the repo.

How Goodwood races (right-handed, clockwise round the top loop):
  - the straight runs along the ridge (the Downs, north of the stands) WSW to the post; 5f and 6f start at its far
    (east) end;
  - beyond it the course drops north off the ridge into a teardrop-shaped loop. Two branches round a narrow island join
    the straight: the "lower bend" (the west branch, about 4f out) and the "top bend" (the east branch, about 5f out).
    Timeform: races up to 1m2f use the lower bend, those over 11f the top bend;
  - the loop is run clockwise: up the diagonal (west) leg, round the top, down the east leg;
  - 7f and 1m start on the east leg and come in by the lower bend; 9f and 9f192y start by the chute's corner and come
    down the diagonal (south-east) and in by the lower bend; 1m3f218y/1m4f start at the chute's far end, go round the
    top and in by the top bend; 1m6f (low on the diagonal) and 2m (foot of the west branch) go up and once round;
  - 2m4f and 2m5f start by the post, run the 'wrong way' east along the straight, bear left up the west branch about 4f
    out, go once round and come in by the top bend.
  With the post 44 m in from the 6f start's end of the straight, every start lands where At The Races' diagram draws it.

World axes, as Ascot (right-handed): metres, y up, origin = the winning post on the inside rail; on the home straight the
horses run towards -x (WSW). The rail is on the horses' right: z = 0, the track runs to z = +trackWidth on their left, the
stands beyond (+z, south). Each route's rail is the edge on the horses' RIGHT in that route's own running direction, so
on the outbound legs of the long races (east along the straight, up the west branch) it is the other edge.

Writes  courses/goodwood-draft.json            the layout as data (routes, rails, bends, heights, starts)
        reference/goodwood/plan-draft.png        the plan on the ground's relief, north up
        reference/goodwood/profiles-draft.png    the ground under every route, post to start

  python3 tools/course/goodwood/layout.py
"""
import json, math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, LineString, Point

REPO = Path(__file__).resolve().parents[3]
F = 201.168                                   # a furlong, metres
YD = 0.9144
OSM = json.loads((REPO / "reference/goodwood/osm-goodwood.json").read_text())
DEM = json.loads((REPO / "reference/goodwood/dem-course-20m.json").read_text())

# ---------------------------------------------------------------- the choices (change here)
TRACK_W = 26.0          # the game's track width (OSM's turf measures about 22-33 m: printed by main())
SIX_IN = 44.0           # the 6f stalls stand this far in from the far (east) end of the straight (the diagram's spacing):
                        # this places the post, in front of the March Stand's west end, ~70 m short of the run-out bend
RUN_OUT = 110.0         # how far the routes carry on past the post (the straight bends away north-west beyond it)
CHUTE_EXTRA = 120.0     # OSM draws the chute off the top left about 130 m long; its line is carried on south-west so the
                        # 9f192y stalls (186 m in) fit with room behind them (interpretive)
SMOOTH = 2              # Chaikin passes on each assembled rail (eases OSM's corners)
EASE = 70.0             # then a running average over this many metres, so the joins between one edge of the turf and
                        # another (where a route changes rail at a junction) become gentle curves, not kinks
STEP = 5.0              # each route's rail sampled every STEP metres
# "1m3f" is Goodwood's 1m3f218y (owner's video of the race, 17 Nov: the caption reads 1m3f218y), two yards short of
# 1m4f: the diagram's "1m 3f" and "1m 4f" are the two ends of the same start line at the chute's far end.
TRIPS = {"5f": 5 * F, "6f": 6 * F, "7f": 7 * F, "1m": 8 * F, "9f": 9 * F, "9f192y": 9 * F + 192 * YD, "1m3f": 11 * F + 218 * YD,
         "1m4f": 12 * F, "1m6f": 14 * F, "2m": 16 * F, "2m4f": 20 * F, "2m5f": 21 * F}
# The two ways back into the straight (Timeform: "all races up to a mile and a quarter use the lower bend, and those in
# excess of eleven furlongs use the top bend"; "re-entering just above or below the five furlong gate"):
#   lower bend = the west branch, joining the straight about 4f out; top bend = the east branch, about 5f out.
ROUTE = {"5f": "straight", "6f": "straight", "7f": "lower", "1m": "lower", "9f": "diagonal", "9f192y": "diagonal",
         "1m3f": "chute", "1m4f": "chute", "1m6f": "loop", "2m": "loop", "2m4f": "cup", "2m5f": "cup"}
# where At The Races' diagram puts each start (to check the trace against)
DIAGRAM = {"5f": "straight, a furlong in from its far end", "6f": "the far (east) end of the straight",
           "7f": "east leg, low down (just above where the legs meet)", "1m": "east leg, a third of the way down",
           "9f": "where the chute meets the loop, on the loop's side", "9f192y": "where the chute meets the loop",
           "1m3f": "the chute's far end", "1m4f": "the chute's far end",
           "1m6f": "diagonal leg, low down", "2m": "foot of the west branch, by the island",
           "2m4f": "straight, about a furlong east of the post", "2m5f": "straight, by the post"}

# ---------------------------------------------------------------- map projection (east, north metres about the course)
LAT0, LON0 = DEM["lat0"], DEM["lon0"]
KX, KY = 111320.0 * math.cos(math.radians(LAT0)), 110574.0
def en(ll): return np.array([(ll[1] - LON0) * KX, (ll[0] - LAT0) * KY])
def ring(pts):
    a = np.array([en(p) for p in pts])
    return a[:-1] if np.allclose(a[0], a[-1]) else a
OUT = ring(OSM["track"]["outer"])            # outer ring, indices as listed in osm-goodwood.json
ISL = ring(OSM["track"]["inner_bottom"])     # the island between the west and east branches
INF = ring(OSM["track"]["inner_top"])        # the top loop's infield

# ---------------------------------------------------------------- the ground
DH = np.array(DEM["h_dm"], float) / 10.0
def ground(p):
    """height (m above sea level) at east/north p, bilinear on the 20 m grid"""
    fx, fy = (p[0] - DEM["x0"]) / DEM["step"], (p[1] - DEM["y0"]) / DEM["step"]
    i = int(np.clip(math.floor(fx), 0, DEM["nx"] - 2)); j = int(np.clip(math.floor(fy), 0, DEM["ny"] - 2))
    a, b = np.clip(fx - i, 0, 1), np.clip(fy - j, 0, 1)
    return (DH[j, i] * (1 - a) + DH[j, i + 1] * a) * (1 - b) + (DH[j + 1, i] * (1 - a) + DH[j + 1, i + 1] * a) * b

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

def chaikin(p, n):
    p = np.array(p, float)
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        q.append(p[-1]); p = np.array(q)
    return p

# ---------------------------------------------------------------- the rails, in running order (OSM ring indices)
def seq(R, idx): return [R[i] for i in idx]
# Each route's rail is the turf's edge on the horses' right in that route's own running direction.
EAST_LEG = seq(INF, [7, 6, 5, 4, 3, 2, 1])                     # top of the east leg down to the infield's tip (the Y)
                                                               # (OSM's point 8, a small dent, left out)
TOP_BEND = seq(INF, list(range(26, 9, -1)))                    # chute corner, round the top, to the top of the east leg
DIAG_UP = seq(INF, [0, 35, 34, 33, 32, 31, 30, 29, 28, 27])    # the Y up the diagonal (north-west) to the chute corner
DIAG_DOWN = seq(OUT, [24, 23, 22, 21, 20, 19, 18, 17, 16, 15])  # the chute corner down the diagonal (south-east): its
                                                               # south-west edge, into the single track
LOWER = seq(OUT, list(range(14, -1, -1)))                      # single track and west branch (the lower bend), west edge
TOP = seq(ISL, [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 23])  # the east branch (the top bend): round the island's east side
STRAIGHT_N = seq(OUT, [0, 114, 113, 112, 111, 110])            # the straight's north edge (the rail), east to west
RUN_OUT_N = seq(OUT, list(range(109, 98, -1)))                 # past the post, bending north-west
STRAIGHT_FAR = [OUT[60], OUT[59]]                              # the straight's north edge at its far east end (6f chute)
STRAIGHT_S = seq(OUT, [86, 85, 84, 82, 80, 79, 78, 77, 76, 75, 74, 73, 72, 70])  # the south edge, west to east (outbound)
UP_WEST = seq(ISL, [23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12])  # up the west branch (its east edge, the island)
CHUTE_SE = [OUT[25], OUT[24]]                                  # the chute's south-east edge, out towards the loop

d = CHUTE_SE[0] - CHUTE_SE[1]; d /= np.hypot(*d)
CHUTE_FAR = CHUTE_SE[0] + d * CHUTE_EXTRA                      # the chute carried on south-west

HOME_LOWER = EAST_LEG + LOWER + STRAIGHT_N[1:]                 # down the east leg, the lower bend, the straight
HOME_TOP = EAST_LEG + TOP + STRAIGHT_N                         # down the east leg, the top bend, the straight
AROUND = DIAG_UP + TOP_BEND                                    # up the diagonal and round the top
ROUTES_RAW = {
    "straight": STRAIGHT_FAR + STRAIGHT_N,
    "lower": TOP_BEND + HOME_LOWER,                                       # 7f, 1m (from the east leg)
    "diagonal": [CHUTE_FAR] + CHUTE_SE + DIAG_DOWN + LOWER + STRAIGHT_N[1:],  # 9f, 9f192y: down the diagonal, lower bend
    "chute": [CHUTE_FAR] + CHUTE_SE + TOP_BEND + HOME_TOP,                # 1m3f, 1m4f: round the top, top bend
    "loop": UP_WEST + AROUND + HOME_TOP,                                  # 1m6f, 2m: up the west branch, once round
    "cup": STRAIGHT_S + UP_WEST + AROUND + HOME_TOP,                      # 2m4f, 2m5f: east along the straight first
}

def build(name):
    pts = chaikin(ROUTES_RAW[name] + RUN_OUT_N, SMOOTH)
    L0 = Line(pts)
    q = np.array([L0.at(s)[0] for s in np.arange(0, L0.L + 1e-6, 2.0)])
    k = int(EASE / 2.0) | 1
    pad = np.vstack([q[:1] - (q[1] - q[0]) * np.arange(k // 2, 0, -1)[:, None], q, q[-1:] + (q[-1] - q[-2]) * np.arange(1, k // 2 + 1)[:, None]])
    q = np.stack([np.convolve(pad[:, 0], np.ones(k) / k, mode="valid"), np.convolve(pad[:, 1], np.ones(k) / k, mode="valid")], 1)
    return Line(q)

# ---------------------------------------------------------------- the post
STR = build("straight")
far_end = STR.p[0]
S_POST_STR = SIX_IN + 6 * F            # metres from the far end along the straight's rail
POST, _ = STR.at(S_POST_STR)
RUN = -STR.at(S_POST_STR)[1] * -1      # running direction at the post (towards the post's far side)
RUN = STR.at(S_POST_STR)[1]
XH = -RUN                              # world x: against the running direction on the home straight
ZH = np.array([-RUN[1], RUN[0]])       # world z: to the horses' left (the stands)
def world(p):
    q = np.asarray(p) - POST
    return [round(float(q @ XH), 2), round(float(q @ ZH), 2)]
def world_dir(v):
    return [round(float(np.asarray(v) @ XH), 4), round(float(np.asarray(v) @ ZH), 4)]

def samples(line):
    """[(point, metres to go)] every STEP metres, from the far start to the end of the run-out (reverse running order:
    index 0 = past the post, as York)"""
    s_post = line.project(POST)
    out = []
    for s in np.arange(line.L, -1e-6, -STEP):
        p, _ = line.at(s)
        out.append((p, round(float(s_post - s), 2)))
    return out[::-1][::-1] if False else out[::-1]

def bends_of(samp):
    """the bends along a route for the race engine: [metres to go at the start, at the end, degrees turned], turns
    towards the rail (right, the course's hand) positive, from the heading change; samp in running order"""
    pts = np.array([s[0] for s in samp]); ds = np.array([s[1] for s in samp])
    run = np.diff(pts, axis=0)
    hd = np.unwrap(np.arctan2(run[:, 1], run[:, 0]))
    per = np.convolve(np.gradient(hd), np.ones(5) / 5, mode="same")     # radians per sample, smoothed over 25 m
    lim = math.radians(0.35) * STEP / 5.0                               # sharper than about an 800 m radius
    out, i, n = [], 0, len(hd)
    while i < n:
        if abs(per[i]) > lim:
            sgn = np.sign(per[i]); j = i
            while j < n and abs(per[j]) > lim and np.sign(per[j]) == sgn: j += 1
            turn = -math.degrees(hd[min(j, n - 1)] - hd[i])             # clockwise (right) turns positive
            # bends past the post (the run-out) are left out: the race is over by then (as York)
            if abs(turn) > 4 and ds[min(j, n - 1)] > 0: out.append([round(float(ds[i]), 1), round(float(max(ds[min(j, n - 1)], 0.0)), 1), round(turn, 1)])
            i = j + 1
        else:
            i += 1
    return out

def heights_of(samp):
    """the ground under the middle of the track every STEP metres (against the post), smoothed over about 40 m"""
    pts = np.array([s[0] for s in samp])
    run = np.gradient(pts, axis=0); run /= np.linalg.norm(run, axis=1)[:, None]
    left = np.stack([-run[:, 1], run[:, 0]], 1)
    h = np.array([ground(p + l * TRACK_W / 2) for p, l in zip(pts, left)])
    k = 9; h = np.convolve(np.pad(h, k // 2, mode="edge"), np.ones(k) / k, mode="valid")
    return h

def width_at(p, t):
    """turf width across the rail point p (running direction t), to the other side of OSM's turf on the horses' left"""
    left = np.array([-t[1], t[0]])
    poly = Polygon(OUT, [ISL, INF])
    seg = LineString([p + left * 0.5, p + left * 90])
    inter = seg.intersection(poly)
    if inter.is_empty: return None
    g = inter if inter.geom_type == "LineString" else max(inter.geoms, key=lambda q: -q.distance(Point(p)))
    return round(float(g.length + 0.5), 1) if g.geom_type == "LineString" else None

def where(name, s):
    """which part of the course a rail position is on (for the checks against the diagram)"""
    p, _ = LINES[name].at(s)
    parts = {"straight": LineString(STRAIGHT_N + [OUT[59], OUT[60]]), "run-out": LineString(RUN_OUT_N),
             "west branch / single track": LineString(LOWER + UP_WEST), "east leg": LineString(EAST_LEG),
             "top of the loop": LineString(TOP_BEND), "diagonal leg": LineString(DIAG_UP), "chute": LineString([CHUTE_FAR] + CHUTE_SE),
             "straight (south edge)": LineString(STRAIGHT_S), "east branch": LineString(TOP)}
    best = min(parts, key=lambda k: parts[k].distance(Point(p)))
    return best

LINES = {k: build(k) for k in ROUTES_RAW}

# ---------------------------------------------------------------- build
def main():
    out_routes, starts, profiles = {}, {}, {}
    for name, line in LINES.items():
        samp = samples(line)                        # running order: far start ... post ... run-out end
        ds = np.array([s[1] for s in samp])
        h = heights_of(samp)
        i_post = int(np.argmin(np.abs(ds)))
        h0 = ground(POST + ZH * 0 + np.array([-RUN[1], RUN[0]]) * TRACK_W / 2)
        rel = h - h0
        profiles[name] = (ds, h)
        rev = slice(None, None, -1)                 # stored as York: index 0 = past the post
        out_routes[name] = {
            "d0": round(float(ds[-1]), 1), "spacing": STEP,
            "insideRail": [world(s[0]) for s in samp][rev],
            "bends": bends_of(samp),
            "heights": {"from": round(float(ds[-1]), 1), "spacing": STEP, "h": [round(float(v), 2) for v in rel[rev]],
                        "note": "ground height (m, against the post's) every 'spacing' metres to go from 'from', across the "
                                "middle of the track, smoothed over about 40 m (AWS Terrain Tiles)"},
            "length": round(float(ds[0]), 1),
        }
    for trip, dist in TRIPS.items():
        r = ROUTE[trip]; line = LINES[r]; s_post = line.project(POST)
        if dist > s_post: raise SystemExit(f"{trip} ({dist:.0f} m) is beyond the {r} route ({s_post:.0f} m)")
        p, t = line.at(s_post - dist)
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": world(p), "running": world_dir(t),
                        "onStraight": r == "straight", "comesBack": r in ("loop", "long"),
                        "groundM": round(float(ground(p + np.array([-t[1], t[0]]) * TRACK_W / 2)), 1),
                        "ll": [round(float(LAT0 + p[1] / KY), 6), round(float(LON0 + p[0] / KX), 6)],
                        "on": where(r, s_post - dist), "diagram": DIAGRAM[trip]}
    # checks
    def along(name, q): return LINES[name].project(POST) - LINES[name].project(q)
    checks = {
        "post: metres west (-) or east (+) of the March Stand's west end": round(float((POST - en([50.89201, -0.745866])) @ XH), 1),
        "post: metres short of where the straight's rail starts bending away (run-out)": round(float(LINES["lower"].project(OUT[108]) - LINES["lower"].project(POST)), 1),
        "lower bend joins the straight (west branch's rail meets it), m from the post": round(float(along("lower", OUT[0])), 1),
        "top bend joins the straight (island's south tip), m from the post": round(float(along("chute", ISL[23])), 1),
        "the 5f gate (1006 m): between those two, as 'just above or below the five furlong gate'": None,
        "run-in from the end of the top bend (east branch), m": round(float(along("chute", ISL[0])), 1),
        "round the loop (up the diagonal, round the top, down the east leg), m": round(float(along("loop", INF[0]) - along("loop", INF[1])), 1) if False else round(float(LINES["loop"].project(INF[1] + 0.0) - 0), 1),
        "chute: OSM's length (its end to the corner), m": round(float(np.hypot(*(CHUTE_SE[0] - CHUTE_SE[1])) + np.hypot(*(CHUTE_SE[1] - INF[26]))), 1),
    }
    checks.pop("the 5f gate (1006 m): between those two, as 'just above or below the five furlong gate'")
    checks.pop("round the loop (up the diagonal, round the top, down the east leg), m")
    for t in ["7f", "1m"]:
        checks[f"{t}: metres up the east leg from the Y"] = round(float(LINES["lower"].project(INF[1]) - (LINES["lower"].project(POST) - TRIPS[t])), 1)
    checks["9f: metres from the chute corner down the diagonal (- = up the chute)"] = round(float((LINES["diagonal"].project(POST) - TRIPS["9f"]) - LINES["diagonal"].project(OUT[24])), 1)
    checks["9f192y: metres up the chute from its corner"] = round(float(LINES["diagonal"].project(OUT[24]) - (LINES["diagonal"].project(POST) - TRIPS["9f192y"])), 1)
    checks["1m4f: metres in from OSM's end of the chute (- = beyond it)"] = round(float((LINES["chute"].project(POST) - TRIPS["1m4f"]) - LINES["chute"].project(CHUTE_SE[0])), 1)
    checks["1m6f: metres up the diagonal from the Y"] = round(float((LINES["loop"].project(POST) - TRIPS["1m6f"]) - LINES["loop"].project(INF[0])), 1)
    checks["2m: metres up the west branch from the island's tip"] = round(float((LINES["loop"].project(POST) - TRIPS["2m"]) - LINES["loop"].project(ISL[23])), 1)
    for t in ["2m4f", "2m5f"]:
        p, _ = LINES["cup"].at(LINES["cup"].project(POST) - TRIPS[t])
        checks[f"{t}: metres east (+) of the post"] = round(float((p - POST) @ XH), 1)
    widths = []
    for k in np.arange(20, 1200, 50):
        p, t = STR.at(S_POST_STR - k)
        w = width_at(p, -t * -1 if False else t)
        if w: widths.append(w)
    out_routes_ordered = {k: out_routes[k] for k in ["straight", "lower", "diagonal", "chute", "loop", "cup"]}
    gpost = float(ground(POST + np.array([-RUN[1], RUN[0]]) * TRACK_W / 2))
    rnd = LINES["chute"]; sp = rnd.project(POST)
    poles = [{"furlongs": k, "at": world(rnd.at(sp - k * F)[0])} for k in range(1, 7)]
    north = world_dir(np.array([0.0, 1.0]))
    out = {
        "id": "goodwood", "name": "Goodwood, draft",
        "status": "DRAFT, phase 1 (the course plan), 17 Nov 2026: not used by the game or the race view yet",
        "_about": "Built by tools/course/goodwood/layout.py from OpenStreetMap's outline of the course (reference/goodwood/"
                  "osm-goodwood.json; map data (c) OpenStreetMap contributors, ODbL) and the ground's heights (reference/goodwood/"
                  "dem-course-20m.json, AWS Terrain Tiles). Don't edit by hand: change the choices at the top of the script.",
        "axes": "As Ascot: origin = winning post on the inside rail; y up. On the home straight the horses run towards -x. "
                "RIGHT-handed: each route's rail (z = 0) is on the horses' right in that route's running direction, the track "
                "runs to z = +trackWidth on their left; on the home straight the stands are beyond (z > trackWidth, south).",
        "direction": "clockwise (right-handed)", "hand": 1,
        "compass": {"north": north, "note": "the direction of north in world x, z"},
        "trackWidth": TRACK_W, "furlong": F, "runOut": RUN_OUT,
        "postGroundM": round(gpost, 1),
        "measured": {"turfWidthStraight": widths, "checks": checks},
        "routes": out_routes_ordered,
        "routesNote": "Each route is its rail sampled every 'spacing' metres, from d0 (metres to go, negative = the run-out past "
                      "the post) back to its far end; 'bends' for the race engine as [metres to go at the start, at the end, "
                      "degrees turned (positive = right, towards the rail)]; 'heights' the ground along it. straight: 5f, 6f. "
                      "lower: 7f, 1m, down the east leg and into the straight by the lower bend (the west branch). diagonal: 9f, "
                      "9f192y, from the chute's corner down the diagonal and the lower bend. chute: 1m3f, 1m4f, round the top "
                      "of the loop, down the east leg, the top bend (the east branch). loop: 1m6f, 2m, up the west branch, once "
                      "round, the top bend. cup: 2m4f, 2m5f, east along the straight from by the post first.",
        "starts": starts,
        "furlongPoles": poles,
        "osm": {"outer": [world(p) for p in OUT], "island": [world(p) for p in ISL], "infield": [world(p) for p in INF],
                "note": "the real turf's outer edge and its two holes, in world axes, for drawing and the next phases"},
        "buildings": [{"name": b["name"], "footprint": [world(en(q)) for q in b["p"]]} for b in OSM["buildings"]],
    }
    (REPO / "courses/goodwood-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    print(json.dumps(checks, indent=1))
    print("straight turf widths (m):", widths)
    print(f"post: {POST.round(1)} en, ground {gpost:.1f} m")
    for t, s in starts.items():
        print(f"  {t:6s} {s['route']:8s} {s['distance']:7.1f} m  on {s['on']:28s} ground {s['groundM']:6.1f}   diagram: {s['diagram']}")
    for n, r in out_routes.items():
        print(f"  route {n:8s} {r['length']:7.1f} m  bends {r['bends']}")
    draw(out, profiles)
    return out

# ---------------------------------------------------------------- drawings
INK, MUTED, POSTC = "#2b2b2b", "#6b6b6b", "#c0392b"
ROUTE_C = {"straight": "#2f5d8a", "lower": "#1d1d1d", "diagonal": "#b03a8a", "chute": "#6a3d9a", "loop": "#b5651d", "cup": "#1a8a6a"}

def signed(a): return 0.5 * np.sum(a[:, 0] * np.roll(a[:, 1], -1) - np.roll(a[:, 0], -1) * a[:, 1])

def draw(c, profiles):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    from matplotlib.colors import LightSource, LinearSegmentedColormap
    x = DEM["x0"] + np.arange(DEM["nx"]) * DEM["step"]; y = DEM["y0"] + np.arange(DEM["ny"]) * DEM["step"]
    cmap = LinearSegmentedColormap.from_list("downs", ["#5d7f4f", "#86a35f", "#b9c27c", "#e2d9a2", "#f1e6c8"])
    ls = LightSource(azdeg=315, altdeg=40)
    rgb = ls.shade(DH, cmap=cmap, vert_exag=2.5, blend_mode="soft", vmin=70, vmax=210)
    fig, ax = plt.subplots(figsize=(13, 11), dpi=140)
    ax.imshow(rgb, origin="lower", extent=[x[0] - 10, x[-1] + 10, y[0] - 10, y[-1] + 10], alpha=0.9, interpolation="bicubic")
    cs = ax.contour(x, y, DH, levels=np.arange(70, 210, 5), colors="#3b3b2b", linewidths=0.3, alpha=0.45)
    cs2 = ax.contour(x, y, DH, levels=np.arange(70, 210, 10), colors="#3b3b2b", linewidths=0.7, alpha=0.7)
    ax.clabel(cs2, fmt="%d m", fontsize=6.5)
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    rings = [OUT, ISL[::-1] if signed(ISL) * signed(OUT) > 0 else ISL, INF[::-1] if signed(INF) * signed(OUT) > 0 else INF]
    verts = np.vstack([np.vstack([r, r[:1]]) for r in rings])
    codes = np.concatenate([[MPath.MOVETO] + [MPath.LINETO] * (len(r) - 1) + [MPath.CLOSEPOLY] for r in rings])
    ax.add_patch(PathPatch(MPath(verts, codes), fc="#4f8a3a", ec="#2e5a22", lw=0.7, alpha=0.85))
    for b in OSM["buildings"]:
        pts = np.array([en(q) for q in b["p"]]); ax.add_patch(MP(pts, closed=True, fc="#f4efe6", ec="#8a7350", lw=0.6))
    ax.text(-215, -345, "stands", fontsize=8, color=INK, ha="center")
    for name in ["cup", "loop", "chute", "diagonal", "lower", "straight"]:
        p = LINES[name].p
        ax.plot(p[:, 0], p[:, 1], color=ROUTE_C[name], lw=1.1, ls="-" if name in ("lower", "straight", "chute", "diagonal") else (0, (4, 2)), alpha=0.95)
    for t, s in c["starts"].items():
        p = en(s["ll"][::-1][::-1] and [s["ll"][0], s["ll"][1]])
        ax.plot(*p, marker="s", ms=6, color=ROUTE_C[s["route"]], mec="white", mew=0.8, zorder=5)
        off = {"5f": (-8, 8), "6f": (4, 8), "7f": (8, -2), "1m": (8, 0), "9f": (6, 6), "9f192y": (-46, 8), "1m3f": (-30, -12),
               "1m4f": (-36, 6), "1m6f": (-40, -4), "2m": (-26, 6), "2m4f": (-4, 8), "2m5f": (-40, 6)}[t]
        ax.annotate(t, p, xytext=off, textcoords="offset points", fontsize=8.5, fontweight="bold", color=ROUTE_C[s["route"]],
                    bbox=dict(fc="white", ec="none", alpha=0.7, pad=0.6))
    ax.plot(*POST, marker="o", ms=8, color=POSTC, mec="white", zorder=6)
    ax.annotate("winning post", POST, xytext=(-80, -16), textcoords="offset points", fontsize=8.5, color=POSTC, fontweight="bold")
    rnd = LINES["chute"]; sp = rnd.project(POST)
    for k in range(1, 8):
        p, _ = rnd.at(sp - k * F); ax.plot(*p, marker="o", ms=2.5, color=INK)
        ax.annotate(f"{k}f", p, xytext=(3, -9), textcoords="offset points", fontsize=6.5, color=MUTED)
    for dd in [500, 1150, 1500, 1900, 2200]:
        p, t = rnd.at(sp - dd); ax.annotate("", p + t * 45, p, arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
    ax.set_aspect("equal"); ax.set_xlim(-750, 1100); ax.set_ylim(-520, 980); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Goodwood: course plan on the real ground, DRAFT 17 Nov 2026\nright-handed; turf outline from OpenStreetMap; "
                 "heights from the AWS Terrain Tiles (contours every 5 m); north up", fontsize=10.5, color=INK, loc="left")
    key = ["Routes (the rail on the horses' right):", "  straight course: 5f, 6f",
           "  7f, 1m: down the east leg, the lower bend", "  9f, 9f192y: down the diagonal, the lower bend",
           "  1m3f, 1m4f: from the chute, round the top, the top bend", "  1m6f, 2m: up the west branch, once round (dashed)",
           "  2m4f, 2m5f: east along the straight first (dashed)", "",
           "Lower bend: the west branch (into the straight ~4f out)", "Top bend: the east branch (~5f out)", "",
           f"Post: {c['postGroundM']:.0f} m above sea level", "Map data (c) OpenStreetMap contributors"]
    ax.text(0.015, 0.985, "\n".join(key), transform=ax.transAxes, fontsize=8, color=INK, va="top",
            bbox=dict(fc="white", ec="#bbbbbb", alpha=0.9))
    x0, y0 = 850, -480
    ax.plot([x0, x0 + 200], [y0, y0], color=INK, lw=2); ax.text(x0 + 100, y0 + 12, "200 m", ha="center", fontsize=7)
    ax.annotate("N", (x0 + 220, y0 + 110), xytext=(x0 + 220, y0 + 40), ha="center", fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK))
    fig.savefig(REPO / "reference/goodwood/plan-draft.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

    # the ground under each route: post on the right, as the racing papers draw a race left to right
    fig, axs = plt.subplots(5, 1, figsize=(12, 14), dpi=130)
    panels = [("straight", ["5f", "6f"], "Straight course (5f, 6f): the far end to the post"),
              ("lower", ["7f", "1m"], "7f, 1m: down the east leg, the lower bend (west branch), the straight"),
              ("diagonal", ["9f", "9f192y"], "9f, 9f192y: from the chute's corner down the diagonal, the lower bend"),
              ("chute", ["1m3f", "1m4f"], "1m3f, 1m4f: from the chute, round the top, down the east leg, the top bend (east branch)"),
              ("cup", ["1m6f", "2m", "2m4f", "2m5f"], "2m4f, 2m5f (and 1m6f, 2m on the same line): east along the straight, up the west branch, round, the top bend")]
    for ax, (name, trips, title) in zip(axs, panels):
        ds, h = profiles[name]
        dists = [c["starts"][t]["distance"] for t in trips]
        top = max(dists) + 60
        m = (ds <= top) & (ds >= -40)
        ax.fill_between(-ds[m] / F, h[m] - 2, 60, color="#cfd9b0")
        ax.plot(-ds[m] / F, h[m], color=ROUTE_C[name], lw=1.6)
        for t, dd in zip(trips, dists):
            ax.axvline(-dd / F, color=MUTED, lw=0.6, ls=":")
            ax.text(-dd / F, h[m].max() + 1.2, t, ha="center", fontsize=8, fontweight="bold", color=INK)
        ax.axvline(0, color=POSTC, lw=1); ax.text(0.05, h[m].min() - 1.5, "post", color=POSTC, fontsize=8)
        for b in c["routes"][name]["bends"]:
            if b[0] <= top: ax.axvspan(-b[0] / F, -b[1] / F, color="#000000", alpha=0.06)
        ax.set_ylim(h[m].min() - 3, h[m].max() + 4); ax.set_xlim(-top / F, 0.3)
        ax.set_ylabel("m above sea", fontsize=8); ax.tick_params(labelsize=7)
        ax.set_title(title, fontsize=9, loc="left")
    axs[-1].set_xlabel("furlongs to go (grey bands: bends)", fontsize=8)
    fig.tight_layout(); fig.savefig(REPO / "reference/goodwood/profiles-draft.png", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    main()
