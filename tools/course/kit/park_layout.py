"""The Park: the kit-made galloping course, as data and a plan, from a few numbers instead of a map.

Owner, 16 Nov 2026: "lets start with creating some kit of parts grandstand components and mapping out the course which
best captures the general features of those courses". Then, with the plans of Lingfield, Ayr, Newbury and Haydock:
"make the shape a little more teardrop / angular. add 2 chutes.. one for the straight course and another branch off for
a round mile and maybe an extension of the back straight. amalgamate these kind of shapes to form the park course and
make it a bit more than just an even round course".

The Park stands in for twelve courses (the design map's "UK courses" tab): Ayr, Bath, Chelmsford City, Ffos Las,
Leicester, Lingfield (turf), Newcastle, Nottingham, Redcar, Salisbury, Wetherby and Yarmouth.

The shape: a polygon of four straights with a rounded corner at each vertex (a radius per corner), so it is set by a
few numbers. Going round from the winning post:
  - the home straight (the run-in, about 4.6f), its line carried on past the home bend as the straight course;
  - the home bend: a square corner into the short side of the wide end; that side's line carried on as the round-mile
    chute, coming down into the bend (Newbury's);
  - the far bend onto the back straight, which runs back towards the post, kinked at a gentle angle (Lingfield's
    corner) and closing in on the home straight: the teardrop (Haydock's, Newbury's);
  - the narrow bend at the post end, tighter, turning through 140 degrees into the home straight; the back straight's
    line carried on past it as the long-distance chute.
The post stands where the narrow bend meets the home straight (as York: no straight past the post).

    python3 tools/course/kit/park_layout.py            # writes courses/park-draft.json and reference/park/plan-draft.png
    python3 tools/course/kit/park_layout.py redcar     # a variant's plan too: reference/park/plan-redcar.png

World axes, as York: metres, y up, origin = the winning post on the inside rail; on the home straight the horses run
towards -x. Left-handed (hand -1): the inside rail (z = 0) on the horses' left, the track to z = -trackWidth, the stands
beyond (z < -trackWidth), the infield +z. A right-handed variant is the same course mirrored (z -> -z).
"""
import json, math, sys
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[3]
F = 201.168

# ---------------------------------------------------------------- the switches: one generic course, many real ones
PARK = {
    "hand": -1,              # -1 left-handed, +1 right-handed (mirrored)
    "trackWidth": 26.0,
    # the inside rail's polygon (metres; x along the home straight away from the post, z into the infield) and the
    # radius of the bend at each corner: 0 the narrow bend (post end), 1 the home bend, 2 the far bend, 3 the kink
    "corners": [[-230.0, 0.0], [1150.0, 0.0], [1150.0, 400.0], [330.0, 470.0]],
    "radii": [110.0, 160.0, 160.0, 300.0],
    "straight": 6.0,         # the straight course in furlongs; the courses with none get a 5f stub (the 6f then goes round)
    "mileChute": 400.0,      # the round-mile chute, off the far bend (Newbury's)
    "farChute": 260.0,       # the back straight carried on past the narrow bend: 1m6f
    "runOut": 90.0,
    "room": 30.0,            # straight track behind the furthest start in a chute
    "surface": "turf",       # or "polytrack", "tapeta" (with floodlights)
    "uphill": 0.0,           # metres climbed over the last 3f (0: flat). The race engine's gradient comes later.
    "scenery": "parkland",
}
# the real courses the Park stands in for (the "UK courses" tab: direction, straight course, finish, surface). The
# shape stays the Park's; the dressing (name, scenery, stand mix) is the next step.
VARIANTS = {
    "ayr":         {"name": "Ayr",               "straight": 6, "scenery": "seaside"},
    "bath":        {"name": "Bath",              "straight": 5, "uphill": 6.0, "scenery": "downland"},
    "chelmsford":  {"name": "Chelmsford City",   "straight": 5, "surface": "polytrack", "scenery": "parkland"},
    "ffoslas":     {"name": "Ffos Las",          "straight": 6, "scenery": "parkland"},
    "leicester":   {"name": "Leicester",         "hand": 1, "straight": 7, "uphill": 5.0, "scenery": "town"},
    "lingfield":   {"name": "Lingfield (turf)",  "straight": 7.5, "scenery": "parkland"},
    "newcastle":   {"name": "Newcastle",         "straight": 8, "surface": "tapeta", "uphill": 3.0, "scenery": "parkland"},
    "nottingham":  {"name": "Nottingham",        "straight": 6, "scenery": "town"},
    "redcar":      {"name": "Redcar",            "straight": 8, "scenery": "seaside"},
    "salisbury":   {"name": "Salisbury",         "hand": 1, "straight": 8, "uphill": 6.0, "scenery": "downland"},
    "wetherby":    {"name": "Wetherby",          "straight": 5, "scenery": "northern stone"},
    "yarmouth":    {"name": "Yarmouth",          "straight": 8, "scenery": "seaside"},
}
TRIPS = {"5f": 5, "6f": 6, "7f": 7, "1m": 8, "1m1f": 9, "1m2f": 10, "1m4f": 12, "1m6f": 14, "2m": 16}
STEP = 5.0

# ---------------------------------------------------------------- the stand side and the festival side (owner, 16 Nov)
# Left to right as seen from the infield (x rising, up the straight from the post). Linking three forms, as his photos:
# a glass box, the old pavilion, a glass box (photo 4's composition: glass either side of its old brick building; owner,
# 16 Nov: "model the old element of this image in the middle instead of the pavilion with the two point towers");
# then open terrace to the arch-roofed grandstand (photo 1), and the tiered stand (York's of 1895, owner 16 Nov) with its
# own terrace (owner, 17 Nov: the terrace infill either side of it removed). All on one front line, LAWN metres
# beyond the outer rail.
LAWN = 18.0
# Owner, 17 Nov 11:54, on the scaled elevation of six (tools/blender/park_standside_elevation.py): "good, that's a nice
# mix". The run, left to right as in that drawing: the tiered stand, the balcony stand, the barrel-roof stand, the old
# pavilion, the pitched-roof stand, the roof-terrace stand, abutting (0.4 m for the colonnade stands' cheek newels).
# (Was: glass box, old pavilion, glass box, terrace, barrel-roof stand, tiered stand; the glass boxes stay in the kit.)
CHAIN = [("park_tiered_stand", 0.0), ("park_balcony_stand", 0.4), ("park_arch_stand", 0.4), ("park_old_pavilion", 0.0),
         ("park_gable_stand", 0.0), ("park_roof_terrace_stand", 0.4)]
CHAIN_START = -32.0          # the left end, just past the post (the tiered stand by the line)
# set back from the front line: the old pavilion has no steps in front, so its face would stand 9 m proud of its
# neighbours' (their standing steps are 9 m deep); set back, its face lines up with theirs and a strip of lawn fronts it
SETBACK = {"park_old_pavilion": 9.0}
# the festival side, in the infield opposite the stands (as York's): the clock house facing the course, its steps in
# front, terraces either side, the sheds behind; the rest of the lawn for marquees, kiosks and flags
FESTIVAL = [("park_clock_house", 105.0, 42.0), ("park_terrace", 77.0, 40.0, 26.0), ("park_terrace", 133.0, 40.0, 26.0),
            ("park_shed", 45.0, 78.0), ("park_shed", 172.0, 74.0)]


class Shape:
    """The inside rail as a rounded polygon. Corner i: the bend at vertex i, with its tangent points 'tin' (where the
    bend starts, going round in reverse running order: post, home straight, home bend, ...) and 'tout'."""
    def __init__(self, V, R):
        V = [np.array(v, float) for v in V]
        self.c = []
        n = len(V)
        for i in range(n):
            p, a, b = V[i - 1], V[i], V[(i + 1) % n]
            u = (a - p) / np.linalg.norm(a - p); w = (b - a) / np.linalg.norm(b - a)
            th = math.acos(float(np.clip(u @ w, -1, 1))); t = R[i] * math.tan(th / 2)
            nrm = np.array([-u[1], u[0]])                     # left of the reverse direction: towards the infield
            self.c.append({"V": a, "u": u, "w": w, "th": th, "r": R[i], "tin": a - u * t, "tout": a + w * t,
                           "centre": a - u * t + nrm * R[i]})
        self.post = self.c[0]["tout"].copy()
        # the circuit as pieces in reverse running order from the post: edge to corner 1, bend 1, edge, bend 2, ...
        self.pieces, d = [], 0.0
        self.dtin = {}                                        # metres before the post where each corner's bend starts
        for k in range(1, n + 1):
            i = k % n
            a, b = self.c[k - 1]["tout"], self.c[i]["tin"]
            L = float(np.linalg.norm(b - a)); self.pieces.append(("edge", d, L, a, (b - a) / L)); d += L
            cc = self.c[i]; arc = cc["r"] * cc["th"]
            self.dtin[i] = d
            self.pieces.append(("bend", d, arc, cc)); d += arc
        self.C = d

    def at(self, d):
        """the inside rail d metres before the post, back round the circuit"""
        d %= self.C
        for p in self.pieces:
            if p[1] <= d <= p[1] + p[2] + 1e-9:
                s = d - p[1]
                if p[0] == "edge":
                    return p[3] + p[4] * s
                cc = p[3]; ang = s / cc["r"]
                v = cc["tin"] - cc["centre"]                  # turning left (anticlockwise) about the centre
                ca, sa = math.cos(ang), math.sin(ang)
                return cc["centre"] + np.array([v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca])
        return self.post.copy()

    def chute(self, i, length):
        """straight on past corner i's bend start, along the edge arriving there"""
        cc = self.c[i]
        return [cc["tin"] + cc["u"] * k for k in np.arange(2.0, length + 1e-6, 2.0)]


def build(P):
    W = P["trackWidth"]
    S = Shape(P["corners"], P["radii"])
    C = S.C
    ring = lambda d0, d1: [S.at(d) for d in np.arange(d0, d1 + 1e-6, 2.0)]
    runout = [S.at(-k) for k in np.arange(P["runOut"], 0, -2.0)]
    d_home, d_mile, d_far = S.dtin[1], S.dtin[2], S.dtin[0]
    sprint = P["straight"] > 0
    st_len = P["straight"] * F + P["room"] - d_home if sprint else 0.0
    routes = {
        "round": runout + ring(0, d_far),
        "mile": runout + ring(0, d_mile) + S.chute(2, P["mileChute"]),
        "far": runout + ring(0, d_far) + S.chute(0, P["farChute"]),
        "loop": runout + ring(0, C + 3.0 * F),
    }
    if sprint:
        routes["straight"] = runout + ring(0, d_home) + S.chute(1, st_len)
    n_run = len(runout)

    def resample(pts):
        p = np.array(pts); seg = np.hypot(*np.diff(p, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
        d_post = s[n_run]
        out = []
        for t in np.arange(0, s[-1] + 1e-6, STEP):
            i = min(np.searchsorted(s, t, side="right") - 1, len(p) - 2)
            k = (t - s[i]) / max(1e-9, s[i + 1] - s[i])
            out.append((p[i] + (p[i + 1] - p[i]) * k, t - d_post))
        return out

    m = -P["hand"]                                    # left-handed: z as built; right-handed: mirrored
    X0 = S.post[0]
    world = lambda q: [round(float(q[0] - X0), 2), round(float(m * q[1]), 2)]
    wdir = lambda v: [round(float(v[0]), 4), round(float(m * v[1]), 4)]

    def bends_of(samples):
        pts = np.array([s[0] for s in samples]); ds = [s[1] for s in samples]
        run = -np.diff(pts, axis=0)
        hd = np.unwrap(np.arctan2(run[:, 1], run[:, 0]))
        per = np.abs(np.convolve(np.gradient(hd), np.ones(5) / 5, mode="same"))
        lim, out, i, n = math.radians(0.35), [], 0, len(hd)
        while i < n:
            if per[i] > lim:
                j = i
                while j < n and per[j] > lim: j += 1
                turn = -math.degrees(hd[min(j, n - 1)] - hd[i]) * m
                if abs(turn) > 4: out.append([round(float(ds[min(j, n - 1)]), 1), round(float(ds[i]), 1), round(float(-turn), 1)])
                i = j + 1
            else:
                i += 1
        return sorted(out, key=lambda b: -b[0])

    samp = {k: resample(v) for k, v in routes.items()}
    sprint_route = "straight" if sprint else "mile"
    route_of = {"5f": sprint_route, "6f": sprint_route, "7f": "mile", "1m": "mile", "1m6f": "far", "2m": "loop"}
    if P["straight"] < 6: route_of["6f"] = "mile"
    if sprint and P["straight"] >= 7: route_of["7f"] = "straight"
    if sprint and P["straight"] >= 8: route_of["1m"] = "straight"
    starts = {}
    for trip, f in TRIPS.items():
        r = route_of.get(trip, "round"); dist = f * F
        s = samp[r]; ds = np.array([q[1] for q in s])
        if dist > ds[-1]: raise SystemExit(f"{trip} is beyond the {r} route")
        i = int(np.searchsorted(ds, dist)); p = s[i][0]; run = s[i - 1][0] - s[i][0]
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": world(p), "running": wdir(run / np.hypot(*run)),
                        "onStraight": r == "straight"}
    out_routes = {k: {"d0": round(v[0][1], 1), "spacing": STEP, "insideRail": [world(p) for p, d in v], "bends": bends_of(v)}
                  for k, v in samp.items()}
    join = {"straight": d_home, "mile": d_mile, "far": d_far}

    def where(trip):
        """where a start lies: in a chute, on a straight (and how far from the next bend), or on a bend"""
        s = starts[trip]; d = s["distance"]
        if s["route"] in join and d > join[s["route"]]:
            return "in its chute, %.0f m up from where it joins" % (d - join[s["route"]])
        dd = d % C
        for p in S.pieces:
            if p[1] <= dd <= p[1] + p[2]:
                return ("on a straight, %.0f m before the next bend" % (dd - p[1])) if p[0] == "edge" else "ON A BEND"

    # the stands: one front line LAWN metres beyond the outer rail (world z < -W, mirrored for right-handed)
    cat = json.loads((REPO / "assets/models/architecture/park_stands.json").read_text())["pieces"]
    chain, x = [], CHAIN_START
    zf = -(W + LAWN)
    for item in CHAIN:
        piece, gap = item[0], item[1]
        w = item[2] if len(item) > 2 else cat[piece]["width"]
        x += gap
        sb = SETBACK.get(piece, 0.0)
        e = {"piece": piece, "x": round(x + w / 2, 2), "z": round(m * (zf - sb), 2), "width": round(w, 2), "depth": cat[piece]["depth"]}
        if sb: e["setback"] = sb
        if cat[piece].get("offset"): e["originX"] = round(x + w / 2 - cat[piece]["offset"], 2)   # where the piece's own origin goes
        if len(item) > 2: e["stretch"] = round(w / cat[piece]["width"], 4)
        chain.append(e); x += w
    fest = []
    for item in FESTIVAL:
        piece, fx, fz = item[:3]
        w = item[3] if len(item) > 3 else cat[piece]["width"]
        e = {"piece": piece, "x": fx, "z": round(m * fz, 2), "width": w, "depth": cat[piece]["depth"]}
        if len(item) > 3: e["stretch"] = round(w / cat[piece]["width"], 4)
        fest.append(e)

    # the perimeter zones (York's zone types): bands beyond the outer rail along stretches of the circuit (by metres
    # before the post), rectangles in world axes, and something at the end of each chute
    def band(d0, d1, off0, off1):
        pts, nr = [], []
        for d in np.arange(d0, d1 + 1e-6, 10.0):
            a, b = S.at(d), S.at(d + 1.0); t = (b - a) / np.linalg.norm(b - a)
            o = np.array([t[1], -t[0]])                       # right of the reverse direction: outside the circuit
            pts.append(a + o * (W + off0)); nr.append(a + o * (W + off1))
        return [world(q) for q in pts + nr[::-1]]
    end_st = S.c[1]["tin"] + S.c[1]["u"] * (st_len + 30) if sprint else None
    end_mile = S.c[2]["tin"] + S.c[2]["u"] * (P["mileChute"] + 25)
    end_far = S.c[0]["tin"] + S.c[0]["u"] * (P["farChute"] + 25)
    cen = np.mean([S.at(d) for d in np.arange(0, C, 20)], axis=0)
    Z = {
        "festival": {"x": [-10, 240], "z": sorted([m * 14, m * 150]), "note": "the festival lawn: marquees, kiosks, flags, the clock house"},
        "standLawn": {"x": [-40, x + 10], "z": sorted([m * (-W - LAWN), m * (-W - 1)]), "note": "the lawn and rail walk in front of the stands"},
        "paddock": {"x": [40, 130], "z": sorted([m * (-W - 85), m * (-W - 150)]), "note": "the parade ring and pre-parade ring behind the stands"},
        "standPark": {"x": [x + 30, x + 330], "z": sorted([m * (-W - 25), m * (-W - 95)]), "note": "car park as a light festival strip (York's park())"},
        "belts": [
            {"note": "round the wide end, clear of the straight course and the mile chute: boards at 20 m, trees from 25 m", "poly": band(d_home + 150, d_mile - 30, 20, 60)},
            {"note": "the back straight: boards at 20 m, trees from 25 m", "poly": band(d_mile + 130, d_far - 40, 20, 60)},
            {"note": "round the narrow bend, between the far chute and the stands: a shallow bank with tree pockets", "poly": band(d_far + 150, C - 30, 18, 64), "bank": True},
            {"note": "stand side, up the straight beyond the car park", "x": [x + 330, float(S.c[1]["tin"][0] - X0) + 40], "z": sorted([m * (-W - 20), m * (-W - 60)])},
        ],
        "chuteEnds": [{"note": n, "at": world(q)} for n, q in (("mound closing the straight course", end_st), ("tree pocket at the top of the mile chute", end_mile),
                                                               ("tree pocket at the end of the far chute", end_far)) if q is not None],
        "lake": {"centre": world(cen + np.array([170, -10])), "radii": [130, 55], "note": "an infield lake (parkland dressing)"},
        "fields": "beyond the belts: green-led flats with hedges",
    }
    checks = {
        "circuit (inside rail), m": round(C, 1), "circuit, furlongs": round(C / F, 2),
        "run-in (post to the home bend), m": round(d_home, 1),
        "bends (degrees, radius)": [[round(math.degrees(c_["th"])), c_["r"]] for c_ in S.c],
        "stand frontage, m": round(x - CHAIN_START, 1),
        "starts": {t: where(t) for t in TRIPS},
    }
    return {
        "id": "park", "name": P.get("name", "The Park"), "status": "DRAFT, 16 Nov 2026: the kit course plan; not used by the game yet",
        "_about": "Built by tools/course/kit/park_layout.py from a few numbers (params). Don't edit by hand.",
        "axes": "As York: origin = winning post on the inside rail; y up; on the home straight the horses run towards -x. "
                "hand -1: inside rail z = 0 on the horses' left, track to z = -trackWidth, stands beyond, infield +z; "
                "hand +1: the same mirrored.",
        "hand": P["hand"], "params": P, "trackWidth": W, "furlong": F, "runOut": P["runOut"], "home": round(d_home, 1),
        "surface": P["surface"], "floodlights": P["surface"] != "turf", "uphill": P["uphill"], "scenery": P["scenery"],
        "routes": out_routes, "starts": starts, "checks": checks,
        "routesNote": "straight: 5f-6f (7f, 1m with the switch). mile: 7f and 1m from the chute off the far bend. round: 1m1f-1m4f "
                      "from the back straight. far: 1m6f from the back straight carried on past the narrow bend. loop: 2m, from the "
                      "home straight, once round.",
        "furlongPoles": [{"furlongs": k, "at": world(S.at(k * F))} for k in range(1, 5)],
        "stands": {"frontZ": round(m * zf, 2), "lawn": LAWN, "chain": chain},
        "festival": {"pieces": fest},
        "zones": Z,
        "variants": VARIANTS,
        "heights": {"note": "flat for now; 'uphill' sets the finish climb when the engine takes gradients", "h": 0.0},
    }, samp, S


# ---------------------------------------------------------------- the plan (the racing papers' way: turned 180)
NAMES = {"park_glass_box_small": "glass box", "park_victorian": "Victorian pavilion", "park_old_pavilion": "old pavilion", "park_tiered_stand": "tiered stand", "park_glass_box": "glass box",
         "park_terrace": "terrace", "park_arch_stand": "arch-roof grandstand", "park_clock_house": "clock house",
         "park_shed": "shed", "park_stair_tower": "stair tower", "park_gable_stand": "gable grandstand"}


def draw(c, samp, S, outp, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Rectangle, Ellipse
    W, m = c["trackWidth"], -c["hand"]
    X0 = S.post[0]
    T = lambda x, z: (-x, z)                       # turned 180: the home straight along the bottom, run left to right
    TW = lambda q: T(q[0] - X0, m * q[1])          # from the shape's own axes
    fig, (ax, az) = plt.subplots(2, 1, figsize=(16, 18.5), dpi=130, gridspec_kw={"height_ratios": [0.5, 0.5]})
    Zn = c["zones"]
    P = c["params"]

    def paint(ax, zoom):
        ax.set_facecolor("#e3e8cf")
        def rect(zone, fc, ec="none", alpha=1.0, lw=0.6, label=None, zorder=3):
            (x0, x1), (z0, z1) = zone["x"], zone["z"]
            a, b = T(x0, z0), T(x1, z1)
            ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec=ec, alpha=alpha, lw=lw, zorder=zorder))
            if label:
                ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, label, ha="center", va="center", fontsize=7.5, color="#333", zorder=5)
        for b in Zn["belts"]:
            if "poly" in b:
                ax.add_patch(MP([T(*q) for q in b["poly"]], closed=True, fc="#9cc4d6" if b.get("bank") else "#7fa463", alpha=0.8, ec="none", zorder=1))
            else:
                rect(b, "#7fa463", alpha=0.8, zorder=1)
        # the track: the circuit as a ring, then each chute as a strip (outer rail = inside rail moved W outwards)
        def outward(p):
            p = np.array(p, float)
            t = np.gradient(p, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
            return p + np.c_[t[:, 1], -t[:, 0]] * W
        circ = np.array([S.at(d) for d in np.arange(0, S.C, 3.0)])
        outer = outward(np.vstack([circ[-1:], circ, circ[:1]]))[1:-1]
        ax.add_patch(MP([TW(v) for v in outer], closed=True, fc="#8db55f", ec="#4f6f35", lw=0.8, zorder=2))
        ax.add_patch(MP([TW(v) for v in circ], closed=True, fc="#e3e8cf", ec="#4f6f35", lw=0.8, zorder=2))
        chutes = [(2, P["mileChute"]), (0, P["farChute"])]
        if P["straight"] > 0:
            chutes.append((1, P["straight"] * F + P["room"] - c["home"]))
        for i, L in chutes:
            cc = S.c[i]
            pts = [cc["tin"] - cc["u"] * 40 + cc["u"] * k for k in np.arange(0, L + 41, 4.0)]
            o = outward(pts)
            ax.add_patch(MP([TW(v) for v in list(pts) + list(o[::-1])], closed=True, fc="#8db55f", ec="#4f6f35", lw=0.8, zorder=2))
        lk = Zn["lake"]; lx, lz = T(*lk["centre"])
        ax.add_patch(Ellipse((lx, lz), 2 * lk["radii"][0], 2 * lk["radii"][1], angle=-8, fc="#a9cbe0", ec="#7aa3bd", lw=0.8, zorder=3))
        ax.text(lx, lz, "lake", ha="center", va="center", fontsize=7.5, color="#3d6680", zorder=4)
        rect(Zn["festival"], "#f3d9b8", ec="#c99a63")
        fz = Zn["festival"]; p = T(sum(fz["x"]) / 2, (fz["z"][1] if m > 0 else fz["z"][0]) - m * 12)
        ax.text(*p, "festival lawn", ha="center", va="center", fontsize=7.5, color="#333", zorder=4)
        rect(Zn["standLawn"], "#d8dcc0")
        rect(Zn["paddock"], "#cfe0b0", ec="#7f9b62", label="parade ring")
        rect(Zn["standPark"], "#e4d4ec", ec="#a68bb4", label="car park as festival strip")
        for e in Zn["chuteEnds"]:
            ax.add_patch(Ellipse(T(*e["at"]), 60, 36, fc="#b9cf8f", ec="#6f8f4a", lw=0.6, zorder=3))
        # the stands and festival pieces as footprints
        for e in c["stands"]["chain"]:
            x0, x1 = e["x"] - e["width"] / 2, e["x"] + e["width"] / 2
            z0 = e["z"]; z1 = z0 - m * e["depth"]
            a, b = T(x0, z0), T(x1, z1)
            fc = {"park_victorian": "#d59a85", "park_old_pavilion": "#d59a85", "park_tiered_stand": "#d59a85", "park_arch_stand": "#f2ede3", "park_terrace": "#d9d0bf"}.get(e["piece"], "#b9c3cf")
            ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec="#6c6458", lw=0.6, zorder=4))
        for e in c["festival"]["pieces"]:
            x0, x1 = e["x"] - e["width"] / 2, e["x"] + e["width"] / 2
            z0 = e["z"]; z1 = z0 + m * e["depth"]
            a, b = T(x0, z0), T(x1, z1)
            fc = "#d59a85" if e["piece"] != "park_terrace" else "#d9d0bf"
            ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec="#6c6458", lw=0.6, zorder=4))
        if zoom:
            for e in c["stands"]["chain"]:
                p = T(e["x"], e["z"] - m * (e["depth"] + 4))
                ax.text(*p, NAMES.get(e["piece"], e["piece"]), ha="center", va="top", fontsize=8, color="#4a3f33", rotation=0 if e["width"] > 28 else 90, zorder=6)
            for e in c["festival"]["pieces"]:
                p = T(e["x"], e["z"] + m * (e["depth"] + 3))
                ax.text(*p, NAMES.get(e["piece"], e["piece"]), ha="center", va="bottom", fontsize=8, color="#4a3f33", zorder=6)
        # starts, post, furlongs, running direction
        col = {"straight": "#2f5d8a", "mile": "#1f7a6b", "round": "#2b2b2b", "far": "#6a3d9a", "loop": "#b5651d"}
        for t, s in c["starts"].items():
            p = T(*s["at"])
            ax.plot(*p, marker="s", ms=5.5, color=col[s["route"]], mec="white", mew=0.6, zorder=6)
            off = {"straight": (0, -14), "loop": (0, -14), "mile": (18, -3), "far": (16, 4)}.get(s["route"], (0, 8))
            ax.annotate(t, p, xytext=off, textcoords="offset points", fontsize=8.5, fontweight="bold", color=col[s["route"]], ha="center", zorder=6)
        for fp in c["furlongPoles"]:
            ax.plot(*T(*fp["at"]), marker="|", ms=8, color="#333", zorder=6)
        ax.plot(*T(0, 0), marker="o", ms=8, color="#c0392b", mec="white", zorder=7)
        ax.annotate("winning post", T(0, 0), xytext=(6, -18 if not zoom else 8), textcoords="offset points", fontsize=8.5, color="#c0392b", fontweight="bold", zorder=7)
        for d in (400, 1350, 1800, 2400, 2750):
            p, q = S.at(d), S.at(d - 40)
            ax.annotate("", TW(q), TW(p), arrowprops=dict(arrowstyle="->", color="#222", lw=1.2), zorder=6)
        if P["straight"] > 0:                       # the switch: the straight course's other lengths, dashed
            for f in (7, 8):
                if f > P["straight"]:
                    a, b = T(P["straight"] * F + 30, -m * W / 2), T(f * F + 30, -m * W / 2)
                    ax.plot([a[0], b[0]], [a[1], b[1]], color="#2f5d8a", ls=(0, (4, 3)), lw=1.2, zorder=5)
                    ax.annotate(f"{f}f straight (switch)", b, xytext=(0, -14), textcoords="offset points", fontsize=7, color="#2f5d8a", ha="center", zorder=5)

    paint(ax, False); paint(az, True)
    xs = [T(*q)[0] for r in c["routes"].values() for q in r["insideRail"]]
    zs = [q[1] for r in c["routes"].values() for q in r["insideRail"]]
    ax.set_xlim(min(xs) - 120, max(xs) + 130); ax.set_ylim(min(zs) - 250, max(zs) + 150)
    zx = [e["x"] for e in c["stands"]["chain"]]
    az.set_xlim(T(max(zx) + 330, 0)[0], T(min(zx) - 110, 0)[0])
    az.set_ylim(-W - 150, 170) if m > 0 else az.set_ylim(-170, W + 150)
    for a_ in (ax, az):
        a_.set_aspect("equal"); a_.set_xticks([]); a_.set_yticks([])
        for t_ in a_.texts: t_.set_clip_on(True)
    az.set_title("The stand side and the festival lawn, closer (the post on the right; horses run left to right)", fontsize=11, loc="left")
    ck = c["checks"]
    key = [f"{c['name']}: {'left' if c['hand'] < 0 else 'right'}-handed, {c['surface']}, {c['scenery']}",
           f"Circuit {ck['circuit (inside rail), m']:.0f} m ({ck['circuit, furlongs']:.1f}f); run-in {ck['run-in (post to the home bend), m']:.0f} m",
           f"Straight course: {P['straight']:g}f" if P["straight"] else "No straight course: the sprints go round from the mile chute",
           "Blue: straight course   green: round-mile chute   black: back straight",
           "purple: back straight carried on past the narrow bend   brown: 2m once round",
           f"Stands: {ck['stand frontage, m']:.0f} m of frontage, {c['stands']['lawn']:.0f} m of lawn in front"]
    ax.text(0.01, 0.99, "\n".join(key), transform=ax.transAxes, fontsize=8.5, va="top", color="#222",
            bbox=dict(fc="white", ec="#bbb", alpha=0.92), zorder=8)
    x0, y0 = ax.get_xlim()[0] + 40, ax.get_ylim()[0] + 30
    ax.plot([x0, x0 + 200], [y0, y0], color="#222", lw=2); ax.text(x0 + 100, y0 + 10, "200 m", ha="center", fontsize=7.5)
    ax.set_title(title, fontsize=12, loc="left", color="#222")
    outp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outp, bbox_inches="tight", facecolor="white"); plt.close(fig)


def main():
    c, samp, S = build(dict(PARK))
    (REPO / "courses/park-draft.json").write_text(json.dumps(c, separators=(",", ":")))
    draw(c, samp, S, REPO / "reference/park/plan-draft.png",
         "The Park (kit galloping course): plan, DRAFT 16 Nov 2026. Turned as the racing papers' plans: stands along the bottom")
    print(json.dumps(c["checks"], indent=1))
    for n, r in c["routes"].items(): print(f"  route {n:9s} bends {r['bends']}")
    for v in sys.argv[1:]:
        P = dict(PARK); P.update(VARIANTS[v])
        cv, sv, Sv = build(P)
        draw(cv, sv, Sv, REPO / f"reference/park/plan-{v}.png", f"The Park as {P['name']}: switches from the UK courses tab")
        print("variant", v, json.dumps(cv["checks"]["starts"]))


if __name__ == "__main__":
    main()
