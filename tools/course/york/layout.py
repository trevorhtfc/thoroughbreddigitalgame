"""York (the Knavesmire), phase 1: the course plan, as data and a drawing, from the real layout.

Owner, 16 Nov 2026: "we can try build York first. If you start with the course plan and assume a flat track. Then it's a
case of building the track geometry and then the borders / edges / any topography round the course and then the
grandstand and festival architecture."

Source: OpenStreetMap's outline of the racecourse turf (reference/york/osm-york.json: its outer and inner edges, and the
named stands). Unlike Newmarket (drawn from the owner's sketch) the shape here is the real one. What OSM can't give is a
choice, named below so it can be changed in one place: where the winning post stands, the track width the game uses,
the run-out past the post, and where each chute's inside rail meets the round course.

How York races (course guides, 16 Nov 2026):
  - left-handed and U-shaped, flat, with a run-in of nearly five furlongs;
  - 5f and 6f on the straight course (its start in the chute south of the home bend);
  - 7f from a spur (the dog-leg chute south-west of the home bend), racing round the tangent of the bend;
  - a mile and up on the round course; 1m6f from a two-furlong chute at the top of the back straight;
  - since 2005 the top bend closes the U into a circuit: 2 miles starts just before the winning post and goes once round.

Writes  courses/york-draft.json           the layout as data, world metres (axes below)
        reference/york/plan-draft.png     the plan, to check by eye (north up)

  python3 tools/course/york/layout.py

World axes, as Ascot and Newmarket: metres, y up, origin = the winning post on the inside rail, and on the home straight
the horses run towards -x. York is LEFT-handed, so the inside rail (z = 0) is on the horses' LEFT and the track runs to
z = -trackWidth on their right; the stands are beyond the outer rail (z < -trackWidth). The infield is +z.
"""
import json, math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, LineString, Point

REPO = Path(__file__).resolve().parents[3]
F = 201.168                                   # a furlong, metres
OSM = json.loads((REPO / "reference/york/osm-york.json").read_text())

# ---------------------------------------------------------------- the choices (change here)
# The winning post, on the home straight's inside rail, by latitude. Set so the 6f start sits in the straight course's
# chute a few metres in from its end, and checked against the 1m6f start (in its chute), the 1m4f start (near where the
# top bend joins the back straight) and the 2m start (just before the post): see the checks printed by main().
POST_LAT = 53.94078
TRACK_W = 26.0          # the game's track width (OSM's turf measures about 22-30 m along the straight: printed by main())
RUN_OUT = 90.0          # how far the routes carry on past the post: round the top bend, which starts at the line (owner,
                        # 16 Nov: no straight past the winning post; the post is at the very end of the straight, as the plans)
TRIPS = {"5f": 5, "6f": 6, "7f": 7, "1m": 8, "1m1f": 9, "1m2f": 10, "1m4f": 12, "1m6f": 14, "2m": 16}
ROUTE = {"5f": "straight", "6f": "straight", "7f": "chute7f", "1m4f": "far", "1m6f": "far", "2m": "loop"}   # the rest: "round"
STEP = 5.0              # the inside rail sampled every STEP metres

# ---------------------------------------------------------------- map projection (east, north metres about the course)
LAT0, LON0 = 53.937, -1.096
KX, KY = 111320.0 * math.cos(math.radians(LAT0)), 110574.0
def en(ll): return np.array([(ll[1] - LON0) * KX, (ll[0] - LAT0) * KY])
def ring(pts):
    a = np.array([en(p) for p in pts])
    return a[:-1] if np.allclose(a[0], a[-1]) else a

OUTER = ring(OSM["track"]["outer"])
INNER = ring(OSM["track"]["inner"])
def signed_area(a): return 0.5 * np.sum(a[:, 0] * np.roll(a[:, 1], -1) - np.roll(a[:, 0], -1) * a[:, 1])
if signed_area(INNER) < 0: INNER = INNER[::-1]          # anticlockwise: the running direction (left-handed)

# ---------------------------------------------------------------- polylines with arc length
class Line:
    def __init__(self, pts, closed=False):
        p = np.array(pts, float)
        if closed: p = np.vstack([p, p[:1]])
        seg = np.hypot(*np.diff(p, axis=0).T)
        self.p, self.s, self.closed = p, np.concatenate([[0], np.cumsum(seg)]), closed
        self.L = self.s[-1]
    def at(self, s):
        if self.closed: s = s % self.L
        s = min(max(s, 0.0), self.L)
        i = min(np.searchsorted(self.s, s, side="right") - 1, len(self.p) - 2)
        k = (s - self.s[i]) / max(1e-9, self.s[i + 1] - self.s[i])
        d = self.p[i + 1] - self.p[i]
        return self.p[i] + d * k, d / (np.hypot(*d) or 1)
    def project(self, q):
        return LineString(self.p).project(Point(q))

LOOP = Line(INNER, closed=True)                       # the inside rail all the way round, in running order

def ll(lat, lon): return en((lat, lon))
# the home straight's inside rail: the inner edge's straight run up the east side, from the home bend to the top bend
HS0, HS1 = ll(53.933008, -1.093063), ll(53.938741, -1.093397)
RUN = (HS1 - HS0) / np.hypot(*(HS1 - HS0))             # running direction up the home straight (about north)
POST = HS0 + RUN * ((POST_LAT - 53.933008) * KY / RUN[1])
S_POST = LOOP.project(POST)

# the chutes' inside rails (OSM's outer edge on each chute's inside, the horses' left)
CHUTE6 = ll(53.929700, -1.092871)                     # the straight course's chute: its end (west edge)
CHUTE7 = [ll(53.928719, -1.097345), ll(53.931029, -1.094614), ll(53.931686, -1.093792)]   # the 7f dog-leg, top to foot
SPUR = [ll(53.945337, -1.100003), ll(53.941413, -1.101070)]                              # the 1m6f chute, top to foot
SPUR_JOIN_LAT = 53.94000                              # where the 1m6f chute's line meets the back straight's inside rail
# York's "1m6f" is really 1m5f188y (2,804 m: the Ebor, the Yorkshire Cup), so its stalls stand right at the top of the OSM
# chute. The game's 1m6f is a full 14 furlongs, so the chute's line is carried on a little past OSM's end (interpretive).
SPUR_EXTRA = 40.0
SPUR[0] = SPUR[0] + (SPUR[0] - SPUR[1]) / np.hypot(*(SPUR[0] - SPUR[1])) * SPUR_EXTRA

# ---------------------------------------------------------------- the routes (each from the post back to beyond its furthest start)
def ring_back(d):
    """inside-rail point d metres before the post on the round course (going back against the running direction)."""
    p, t = LOOP.at(S_POST - d)
    return p
def ring_pts(d0, d1, step=2.0):
    return [ring_back(d) for d in np.arange(d0, d1 + 1e-6, step)]

def d_on_ring(q):
    """metres before the post, round the course, of the inside-rail point nearest q"""
    return (S_POST - LOOP.project(q)) % LOOP.L

HOME = d_on_ring(HS0)                                  # the home straight, post to the home bend (the run-in)
JOIN7 = d_on_ring(ll(53.933008, -1.093063)) + 0.0      # the 7f chute joins the straight at the foot of the home bend
JOINF = d_on_ring(ll(SPUR_JOIN_LAT, -1.101370))        # the 1m6f chute joins the back straight

def runout_pts():
    """past the post: the round course's inside rail into the top bend (no straight run-out). The post stands a little
    under a metre off OSM's inner edge, so that offset is eased out over the first 30 m."""
    off = POST - LOOP.at(S_POST)[0]
    return [ring_back(-k) + off * max(0.0, 1.0 - k / 30.0) for k in np.arange(RUN_OUT, 0, -2.0)]

def route_points(name):
    """inside rail from the end of the run-out, through the post, back to the route's far end: in reverse running order
    (index 0 = past the post), as 2 m steps."""
    out = runout_pts()
    if name == "straight":
        out += [POST - RUN * k for k in np.arange(0, np.dot(POST - CHUTE6, RUN) + 1e-6, 2.0)]
    elif name == "chute7f":
        out += ring_pts(0, JOIN7)
        tail = [ring_back(JOIN7)] + CHUTE7[::-1]
        for a, b in zip(tail[:-1], tail[1:]):
            n = max(1, int(np.hypot(*(b - a)) / 2.0))
            out += [a + (b - a) * (k / n) for k in range(1, n + 1)]
    elif name == "far":
        out += ring_pts(0, JOINF)
        tail = [ring_back(JOINF)] + SPUR[::-1]
        for a, b in zip(tail[:-1], tail[1:]):
            n = max(1, int(np.hypot(*(b - a)) / 2.0))
            out += [a + (b - a) * (k / n) for k in range(1, n + 1)]
    elif name == "round":
        out += ring_pts(0, JOINF)
    elif name == "loop":
        out += ring_pts(0, LOOP.L + 400)
    return out

def resample(pts, step):
    """an even resampling (step metres) of a polyline given in reverse running order, with metres to go (negative past
    the post): returns [(point, metres to go)]."""
    L = Line(pts)
    d_post = L.project(POST) if True else 0.0
    out = []
    for s in np.arange(0, L.L + 1e-6, step):
        p, _ = L.at(s)
        out.append((p, s - d_post))
    return out

# ---------------------------------------------------------------- world axes
XH, ZH = -RUN, np.array([-RUN[1], RUN[0]])             # x along -running, z to the horses' left (the infield)
def world(p):
    q = np.asarray(p) - POST
    return [round(float(q @ XH), 2), round(float(q @ ZH), 2)]
def world_dir(v):
    return [round(float(np.asarray(v) @ XH), 4), round(float(np.asarray(v) @ ZH), 4)]

def bends_of(samples, threshold=0.06):
    """the bends along a route, for the race engine: [metres to go where it starts, where it ends, degrees turned]
    (left turns positive), from the heading change per 10 m."""
    pts = np.array([s[0] for s in samples]); ds = [s[1] for s in samples]
    run = -np.diff(pts, axis=0)                           # running direction (towards the post)
    hd = np.unwrap(np.arctan2(run[:, 1], run[:, 0]))
    out, i, n = [], 0, len(hd)
    per = np.abs(np.convolve(np.gradient(hd), np.ones(5) / 5, mode="same"))   # radians per sample, smoothed over 25 m
    lim = math.radians(0.35)                                   # sharper than about an 800 m radius counts as a bend
    while i < n:
        if per[i] > lim:
            j = i
            while j < n and per[j] > lim: j += 1
            turn = math.degrees(hd[min(j, n - 1)] - hd[i])
            # running order is reverse of index order: the bend starts at the larger metres-to-go
            if abs(turn) > 4: out.append([round(float(ds[min(j, n - 1)]), 1), round(float(ds[i]), 1), round(float(-turn), 1)])
            i = j + 1
        else:
            i += 1
    return sorted(out, key=lambda b: -b[0])

def width_at(p, t):
    """turf width across the inside rail point p (running direction t): from p to the OSM outer edge on the horses' right"""
    right = np.array([t[1], -t[0]])
    far = Polygon(OUTER).exterior.intersection(LineString([p, p + right * 80]))
    if far.is_empty: return None
    pts = [far] if far.geom_type == "Point" else list(getattr(far, "geoms", []))
    return min(np.hypot(*(np.array(q.coords[0]) - p)) for q in pts)

# ---------------------------------------------------------------- build
def main():
    routes, starts = {}, {}
    for name in ["straight", "chute7f", "round", "far", "loop"]:
        samp = resample(route_points(name), STEP)
        routes[name] = {"samples": samp}
    for trip, f in TRIPS.items():
        r = ROUTE.get(trip, "round"); dist = f * F
        samp = routes[r]["samples"]
        ds = np.array([s[1] for s in samp])
        if dist > ds[-1]:
            raise SystemExit(f"{trip} ({dist:.0f} m) is beyond the {r} route ({ds[-1]:.0f} m)")
        i = int(np.searchsorted(ds, dist)); p = samp[i][0]
        run = samp[i - 1][0] - samp[i][0]
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": world(p), "running": world_dir(run / np.hypot(*run)),
                        "onStraight": r == "straight", "ll": [round(float(LAT0 + p[1] / KY), 6), round(float(LON0 + p[0] / KX), 6)]}

    # checks against the course guides
    loopL = LOOP.L
    def nearest_ll(name, trip): return starts[trip]["ll"]
    chute6_room = np.dot(POST - CHUTE6, RUN) - TRIPS["6f"] * F
    spur_len = np.hypot(*(SPUR[0] - SPUR[1])) + np.hypot(*(SPUR[1] - ring_back(JOINF)))
    checks = {k: round(float(v), 1) for k, v in {
        "run-in (post to the home bend), m": round(HOME, 1),
        "6f start, metres in from the chute's end": round(chute6_room, 1),
        "7f start, metres in from the chute's top": round(sum(np.hypot(*(b - a)) for a, b in zip(CHUTE7[:-1], CHUTE7[1:])) + np.hypot(*(CHUTE7[-1] - ring_back(JOIN7))) + JOIN7 - TRIPS["7f"] * F, 1),
        "1m4f start, metres up the chute from where it joins": round(TRIPS["1m4f"] * F - JOINF, 1),
        "1m6f start, metres in from the chute's top": round(JOINF + spur_len - TRIPS["1m6f"] * F, 1),
        "the circuit (inside rail), m": round(loopL, 1),
        "2m start, metres before the post": round(TRIPS["2m"] * F - loopL, 1),
    }.items()}
    # turf widths along the run-in (OSM)
    widths = []
    for d in np.arange(0, HOME, 50):
        p, t = LOOP.at(S_POST - d)
        w = width_at(p, t)
        if w: widths.append(round(float(w), 1))

    out_routes = {}
    for name, r in routes.items():
        samp = r["samples"]
        out_routes[name] = {
            "d0": round(samp[0][1], 1), "spacing": STEP,
            "insideRail": [world(p) for p, d in samp],
            "bends": bends_of(samp),
        }
    stands = [{"name": b["name"], "footprint": [world(en(q)) for q in b["p"]]} for b in OSM["buildings"]]
    poles = [{"furlongs": k, "at": world(ring_back(k * F))} for k in range(1, 6)]
    north = world_dir(np.array([0.0, 1.0]))
    out = {
        "id": "york", "name": "York (the Knavesmire), draft", "status": "DRAFT, phase 1 (the course plan), 16 Nov 2026: not used by the game or the race view yet",
        "_about": "Built by tools/course/york/layout.py from OpenStreetMap's outline of the course (reference/york/osm-york.json; "
                  "map data (c) OpenStreetMap contributors, ODbL). Don't edit by hand: change the choices at the top of the script.",
        "axes": "Origin = winning post on the inside rail; y up. On the home straight the horses run towards -x. LEFT-handed: the "
                "inside rail (z = 0) on the horses' left, the track to z = -trackWidth on their right, the stands beyond the outer "
                "rail (z < -trackWidth); the infield is +z.",
        "direction": "anticlockwise (left-handed)", "hand": -1,
        "compass": {"north": north, "note": "the direction of north in world x, z"},
        "trackWidth": TRACK_W, "furlong": F, "runOut": RUN_OUT,
        "measured": {"turfWidthAlongRunIn": widths, "checks": checks},
        "routes": out_routes,
        "routesNote": "Each route is its inside rail sampled every 'spacing' metres, from d0 (metres to go, negative = the run-out past "
                      "the post) back beyond its furthest start; 'bends' for the race engine as [metres to go at the start, at the end, "
                      "degrees turned (positive = left)]. straight: 5f and 6f. chute7f: the dog-leg. round: a mile to 1m2f. far: 1m4f and 1m6f "
                      "from the chute at the top of the back straight. loop: 2m, from just before the post, once round.",
        "home": round(float(HOME), 1),
        "heights": {"note": "flat (owner, 16 Nov: assume a flat track)", "h": 0.0},
        "starts": starts,
        "furlongPoles": poles,
        "osm": {"outer": [world(p) for p in OUTER], "inner": [world(p) for p in INNER],
                "note": "the real turf's outer and inner edges, in world axes, for drawing and for the next phase (edges and borders)"},
        "buildings": stands,
    }
    (REPO / "courses/york-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    draw(out, checks, widths)
    print(json.dumps(checks, indent=1))
    print("run-in turf widths (m):", widths)
    for t, s in starts.items(): print(f"  {t:5s} {s['route']:9s} {s['distance']:7.1f} m  at {s['at']}  {s['ll']}")
    for n, r in out_routes.items(): print(f"  route {n:9s} bends {r['bends']}")
    return out

# ---------------------------------------------------------------- the drawing (north up, east right)
INK, MUTED, TURF, GRASS, POSTC, STANDC = "#2b2b2b", "#777777", "#86ac5f", "#e6ead2", "#c0392b", "#cdb79a"
ROUTE_C = {"straight": "#2f5d8a", "chute7f": "#8a5a2f", "round": "#2b2b2b", "far": "#6a3d9a", "loop": "#b5651d"}

def draw(c, checks, widths):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    fig, ax = plt.subplots(figsize=(11, 14), dpi=150)
    ax.set_facecolor(GRASS)
    ax.add_patch(MP(OUTER, closed=True, fc=TURF, ec="#4f6f35", lw=0.8))
    ax.add_patch(MP(INNER, closed=True, fc=GRASS, ec="#4f6f35", lw=0.8))
    for b in OSM["buildings"]:
        pts = np.array([en(q) for q in b["p"]])
        ax.add_patch(MP(pts, closed=True, fc=STANDC, ec="#8a7350", lw=0.6))
        cx, cy = pts.mean(axis=0)
        ax.text(cx + 14, cy, b["name"], fontsize=6.5, color=INK, va="center")
    for name in ["round", "far", "chute7f", "straight", "loop"]:
        pts = np.array([s[0] for s in resample(route_points(name), STEP)])
        ax.plot(pts[:, 0], pts[:, 1], color=ROUTE_C[name], lw=1.1 if name != "loop" else 0.8,
                ls="-" if name != "loop" else (0, (4, 3)), alpha=0.9)
    for t, s in c["starts"].items():
        p = en(s["ll"])
        ax.plot(*p, marker="s", ms=5, color=ROUTE_C[s["route"]], mec="white", mew=0.6)
        ax.annotate(t, p, xytext=(-26, 6), textcoords="offset points", fontsize=8, fontweight="bold", color=ROUTE_C[s["route"]])
    for k in range(1, 6):
        p = ring_back(k * F); ax.plot(*p, marker="|", ms=8, color=INK)
        ax.annotate(f"{k}f", p, xytext=(-18, -3), textcoords="offset points", fontsize=6.5, color=MUTED)
    ax.plot(*POST, marker="o", ms=7, color=POSTC, mec="white")
    ax.annotate("winning post", POST, xytext=(-70, 4), textcoords="offset points", fontsize=8, color=POSTC, fontweight="bold")
    # running direction arrows
    for d in [400, 1400, 2200, 3050]:
        p = ring_back(d); q = ring_back(d - 40)
        ax.annotate("", q, p, arrowprops=dict(arrowstyle="->", color=INK, lw=1.0))
    ax.set_aspect("equal"); ax.set_xlim(OUTER[:, 0].min() - 120, OUTER[:, 0].max() + 260); ax.set_ylim(OUTER[:, 1].min() - 80, OUTER[:, 1].max() + 80)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("York (the Knavesmire): course plan, DRAFT 16 Nov 2026\nleft-handed; real turf outline from OpenStreetMap; north up",
                 fontsize=11, color=INK, loc="left")
    key = ["Routes (inside rail):", "  straight course: 5f, 6f", "  7f dog-leg chute", "  round course: 1m to 1m2f",
           "  chute at the top of the back straight: 1m4f, 1m6f", "  2m: from just before the post, once round (dashed)", "",
           f"Run-in: {checks['run-in (post to the home bend), m']:.0f} m ({checks['run-in (post to the home bend), m'] / F:.1f}f)",
           f"Circuit: {checks['the circuit (inside rail), m']:.0f} m ({checks['the circuit (inside rail), m'] / F:.1f}f)",
           f"Turf width on the run-in: {min(widths):.0f}-{max(widths):.0f} m (game: {TRACK_W:.0f} m)",
           "", "Map data (c) OpenStreetMap contributors"]
    ax.text(0.33, 0.975, "\n".join(key), transform=ax.transAxes, fontsize=8, color=INK, va="top",
            bbox=dict(fc="white", ec="#bbbbbb", alpha=0.9))
    # scale bar
    x0, y0 = OUTER[:, 0].max() + 40, OUTER[:, 1].min() - 40
    ax.plot([x0, x0 + 200], [y0, y0], color=INK, lw=2); ax.text(x0 + 100, y0 + 12, "200 m", ha="center", fontsize=7)
    ax.annotate("N", (x0 + 200, y0 + 120), xytext=(x0 + 200, y0 + 60), ha="center", fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK))
    outp = REPO / "reference/york/plan-draft.png"
    outp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outp, bbox_inches="tight", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    main()
