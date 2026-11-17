"""The Tight Track: the kit-made sharp, turning course, as data and a plan, from a few numbers instead of a map.

The second of the three generic courses (the brief: claude/next-chat-kit-courses.md; the Park first, then the Tight
Track, then the Hill Track). It stands in for the ten sharp, turning courses (the design map's "UK courses" tab):
Catterick, Chester, Kempton, Lingfield (AW), Musselburgh, Ripon, Southwell, Thirsk, Windsor and Wolverhampton. Their
switches (hand, straight course, surface, scenery, floodlights) are read from the stand configurator's data
(courses/kit/stand-config.json, written by stand_config.py), so they live in one place.

Owner, 17 Nov 2026: first a rounded triangle; then "more of a circle ... with a few shoots", "take the Chester loop
with a 6f shoot", "bigger loop"; then a sketch: "maybe something like this? and then we can have a straight and a round
6f? i want this course to capture the vibe of as many courses as we can". So, after the sketch: a rounded square about
1m2f round (1,951 m), the post end bulging round (radii 190 m and 180 m), a sharp home bend (90 m) and a 120 m bend at
the top of the home-end side; a run-in of 260 m (1.3f). The same kit as the Park: a polygon with a rounded corner at
each vertex. The chutes, as sketched: the 6f straight course off the home straight (a switch per course), a chute up off
the home-end side, one along the top; plus a short one past the post end (the 1m1f needs it). With a straight course,
the 5f and 6f are offered round the loop too.
Every start is on a straight or in a chute, never on a bend; the starts pick their own place (the nearest straight
with room, else the chute that joins nearest) so the numbers can change without re-planning by hand.

    python3 tools/course/kit/tight_layout.py            # writes courses/tight-draft.json and reference/tight/plan-draft.png
    python3 tools/course/kit/tight_layout.py chester    # a variant's plan too: reference/tight/plan-chester.png
    python3 tools/course/kit/tight_layout.py all        # every variant's plan

World axes, as York and the Park: metres, y up, origin = the winning post on the inside rail; on the home straight the
horses run towards -x. Left-handed (hand -1): the inside rail (z = 0) on the horses' left, the track to z = -trackWidth,
the stands beyond (z < -trackWidth), the infield +z. A right-handed variant is the same course mirrored (z -> -z).
"""
import json, math, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from park_layout import Shape, F, TRIPS, STEP          # the Park's rounded polygon, furlong, trips and sample step

REPO = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------- the switches: one generic course, many real ones
TIGHT = {
    "hand": -1,              # -1 left-handed, +1 right-handed (mirrored)
    "trackWidth": 24.0,      # a touch narrower than the Park's 26 m
    # the inside rail's polygon (metres; x along the home straight away from the post end, z into the infield) and the
    # radius of the bend at each corner: 0 the post-end bend, 1 the home bend, 2 the home-end top, 3 the far top
    "corners": [[0.0, 0.0], [580.0, 0.0], [580.0, 520.0], [0.0, 520.0]],
    "radii": [190.0, 90.0, 120.0, 180.0],
    "pastPost": 40.0,        # straight track past the winning post before the post-end bend
    # the chutes: straight spurs joining the loop on its tangent ("join": metres before the post where a chute meets
    # the loop; "home": the top of the home straight, its line carried on past the home bend, which is also the straight
    # course where a course has one; "corner:i": the line arriving at corner i's bend carried on past it). Owner, 17 Nov,
    # with a sketch: a rounded square, the 6f straight course off the home straight, a chute up off the home-end side,
    # one along the top; the post end bulging round. The post-end chute is mine: the 1m1f needs it.
    "chutes": [{"name": "home-straight chute", "join": "home"}, {"name": "home-side chute", "join": "corner:2"},
               {"name": "top chute", "join": "corner:3"}, {"name": "post-end chute", "join": "corner:0"}],
    "roundSprints": True,    # with a straight course, the 5f and 6f are also offered round the loop ("a straight and a round 6f")
    # the straight course in furlongs (5 or 6; 0 = none), a switch for the real courses; the generic course has a 6f
    # straight and the round sprints too (owner, 17 Nov: "we can have a straight and a round 6f ... capture the vibe of as
    # many courses as we can")
    "straight": 6.0,
    "minAhead": 60.0,        # a start on a straight needs at least this much straight in front of it
    "maxChute": 330.0,       # the furthest a start may sit up a chute
    "room": 30.0,            # straight track behind the furthest start in a chute
    "runOut": 120.0,         # pulling up after the post (into the post-end bend)
    "surface": "turf",       # or "polytrack", "tapeta" (with floodlights)
    "lights": False,
    "uphill": 0.0,           # flat: none of the ten has a stiff finish
    "scenery": "parkland",
}
VARIANT_KEYS = ("name", "hand", "straight", "surface", "lights", "uphill", "scenery", "note")


def variants():
    """the ten real courses, from the stand configurator's data (one source for every course's switches)"""
    cfg = json.loads((REPO / "courses/kit/stand-config.json").read_text())["courses"]
    return {k: {x: v[x] for x in VARIANT_KEYS if x in v} for k, v in cfg.items() if v["family"] == "tight"}


# ---------------------------------------------------------------- the stand side and the festival lawn
LAWN = 18.0                  # the front line, metres beyond the outer rail (as the Park)
CHAIN_START = -32.0          # T1's left end, just past the post (as the Park)
STAND_DEPTH = 31.3           # the kit's back line
# the infield opposite the stands, as the Park's (its pieces, a smaller lawn): the clock house facing the course,
# terraces either side, sheds behind
FESTIVAL = [("park_clock_house", 75.0, 40.0), ("park_terrace", 47.0, 38.0), ("park_terrace", 103.0, 38.0),
            ("park_shed", 25.0, 72.0), ("park_shed", 130.0, 72.0)]


class TightShape:
    """The Park's Shape with the post moved pastPost metres up the home straight from the post-end bend: at(d) is the
    inside rail d metres before the post, back round the circuit."""
    def __init__(self, P):
        self.S = Shape(P["corners"], P["radii"])
        self.pb = P["pastPost"]
        self.C = self.S.C
        self.c = self.S.c
        self.dtin = {i: d - self.pb for i, d in self.S.dtin.items()}   # metres before the post where each bend starts
        self.post = self.S.at(self.pb)
        self.pieces = [(p[0], p[1] - self.pb) + tuple(p[2:]) for p in self.S.pieces]

    def at(self, d):
        return self.S.at(d + self.pb)

    def chute(self, i, length):
        return self.S.chute(i, length)

    def join(self, ch):
        """where a chute meets the loop, in metres before the post"""
        j = ch["join"]
        if j == "home": return self.dtin[1]
        if isinstance(j, str) and j.startswith("corner:"): return self.dtin[int(j[7:])]
        return float(j)

    def spur(self, ch, length, back=0.0):
        """the chute's centre... its inside-rail line: from the join point straight out along the loop's tangent (the
        direction going back round, away from the post), length metres; back metres the other way first (drawing)"""
        dj = self.join(ch)
        a = self.at(dj)
        t = self.at(dj + 0.5) - self.at(dj - 0.5); t = t / np.linalg.norm(t)
        return [a + t * k for k in np.arange(2.0 - back, length + 1e-6, 2.0)]

    def tangent(self, ch):
        dj = self.join(ch)
        t = self.at(dj + 0.5) - self.at(dj - 0.5)
        return t / np.linalg.norm(t)

    def piece_at(self, d):
        dd = (d + self.pb) % self.C - self.pb
        for p in self.pieces:
            if p[1] - 1e-6 <= dd <= p[1] + p[2] + 1e-6:
                return p, dd
        return None, dd


def place(S, P, dist):
    """where a start of dist metres goes: ("edge", None, ahead) on a straight with room in front, else ("chute", k,
    metres up the chute) for the chute k joining nearest behind it. The home-straight chute takes a round start only
    once round (it points the wrong way otherwise)."""
    C = S.C
    p, dd = S.piece_at(dist)
    if p[0] == "edge" and dd - p[1] >= P["minAhead"]:
        return ("edge", None, dd - p[1])
    best = None
    for k, ch in enumerate(P["chutes"]):
        dj = S.join(ch)
        if ch["join"] == "home" and dist < C + dj:
            continue
        up = (dist - dj) % C
        if up <= P["maxChute"] and (best is None or up < best[2]):
            best = ("chute", k, up)
    if best is None:
        raise SystemExit(f"no straight or chute for a start {dist:.0f} m out")
    return best


def build(P):
    W = P["trackWidth"]
    S = TightShape(P)
    C = S.C
    ring = lambda d0, d1: [S.at(d) for d in np.arange(d0, d1 + 1e-6, 2.0)]
    runout = [S.at(-k) for k in np.arange(P["runOut"], 0, -2.0)]
    d_home = S.dtin[1]
    sprint = P["straight"]                                           # 0: no straight course; the sprints go round
    sprint6 = P["straight"] >= 6
    trips = dict(TRIPS)
    if sprint and P.get("roundSprints"):
        trips.update({"5f round": 5, "6f round": 6})

    # every start's place, then each chute laid as long as its furthest start (plus room)
    where_at = {}
    for trip, f in trips.items():
        dist = f * F
        if (trip == "5f" and sprint) or (trip == "6f" and sprint6):
            where_at[trip] = ("chute", 0, dist - d_home)
        else:
            where_at[trip] = place(S, P, dist)
    chute_len = {k: 0.0 for k in range(len(P["chutes"]))}
    chute_len[0] = sprint * F - d_home
    for trip, (kind, i, up) in where_at.items():
        if kind == "chute": chute_len[i] = max(chute_len[i], up)
    chute_len = {i: L + P["room"] for i, L in chute_len.items() if L > 0}
    names = {k: ch["name"] for k, ch in enumerate(P["chutes"])}
    if sprint: names[0] = "straight course"                           # the home-straight chute carried on to 5f or 6f
    J = {k: S.join(ch) for k, ch in enumerate(P["chutes"])}

    # the routes: one per chute and lap count, and the circuit itself
    routes, route_of = {}, {}
    for trip, (kind, i, up) in where_at.items():
        dist = trips[trip] * F
        if kind == "edge":
            r = "round"
        else:
            laps = int((dist - J[i] - up + 1.0) // C)
            r = ("straight" if i == 0 and laps == 0 else P["chutes"][i]["name"].replace(" ", "-").replace("-chute", "")
                 + ("-lap" if laps else ""))
            if r not in routes:
                routes[r] = runout + ring(0, laps * C + J[i]) + S.spur(P["chutes"][i], chute_len[i])
        route_of[trip] = r
    longest = max(trips[t] * F for t, w in where_at.items() if w[0] == "edge")
    routes["round"] = runout + ring(0, longest + P["room"] + 10)
    n_run = len(runout)

    def resample(pts):
        p = np.array(pts); seg = np.hypot(*np.diff(p, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
        d0 = s[n_run]
        out = []
        for t in np.arange(0, s[-1] + 1e-6, STEP):
            i = min(np.searchsorted(s, t, side="right") - 1, len(p) - 2)
            k = (t - s[i]) / max(1e-9, s[i + 1] - s[i])
            out.append((p[i] + (p[i + 1] - p[i]) * k, t - d0))
        return out

    m = -P["hand"]                                    # left-handed: z as built; right-handed: mirrored
    X0, Z0 = S.post
    world = lambda q: [round(float(q[0] - X0), 2), round(float(m * (q[1] - Z0)), 2)]
    wdir = lambda v: [round(float(v[0]), 4), round(float(m * v[1]), 4)]

    def bends_of(samples):
        """the engine's bends on a route: [from, to, degrees] in metres before the post (the Park's method)"""
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
    starts = {}
    for trip, f in trips.items():
        r = route_of[trip]; dist = f * F
        s = samp[r]; ds = np.array([q[1] for q in s])
        if dist > ds[-1]: raise SystemExit(f"{trip} is beyond the {r} route")
        i = int(np.searchsorted(ds, dist)); p = s[i][0]; run = s[i - 1][0] - s[i][0]
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": world(p), "running": wdir(run / np.hypot(*run)),
                        "onStraight": r == "straight"}
    out_routes = {k: {"d0": round(v[0][1], 1), "spacing": STEP, "insideRail": [world(p) for p, d in v], "bends": bends_of(v)}
                  for k, v in samp.items()}

    def where(trip):
        kind, i, up = where_at[trip]
        lap = " (once round first)" if trips[trip] * F > C + (J[i] if kind == "chute" else -S.pb) - 1 else ""
        if kind == "chute":
            return "in the %s, %.0f m up from where it joins%s" % (names[i], up, lap)
        return "on a straight, %.0f m before the next bend%s" % (up, lap)

    # the stands: the configurator's fixed plots (T1-T4) on one front line LAWN metres beyond the outer rail
    cfg = json.loads((REPO / "courses/kit/stand-config.json").read_text())
    plots = []
    zf = -(W + LAWN)
    for pl in cfg["families"]["tight"]["plots"]:
        x0, x1 = CHAIN_START + pl["x0"], CHAIN_START + pl["x1"]
        plots.append({"id": pl["id"], "name": pl["name"], "class": pl["class"], "x": round((x0 + x1) / 2, 2),
                      "x0": round(x0, 2), "x1": round(x1, 2), "z": round(m * zf, 2), "width": pl["width"], "depth": STAND_DEPTH})
    x_end = plots[-1]["x1"]
    cat = json.loads((REPO / "assets/models/architecture/park_stands.json").read_text())["pieces"]
    fest = [{"piece": piece, "x": fx, "z": round(m * fz, 2), "width": cat[piece]["width"], "depth": cat[piece]["depth"]}
            for piece, fx, fz in FESTIVAL]

    # the perimeter zones (York's and the Park's zone types): belts round the outside, broken where a chute leaves
    def band(d0, d1, off0, off1):
        pts, nr = [], []
        for d in np.arange(d0, d1 + 1e-6, 10.0):
            a, b = S.at(d), S.at(d + 1.0); t = (b - a) / np.linalg.norm(b - a)
            o = np.array([t[1], -t[0]])                       # right of the reverse direction: outside the circuit
            pts.append(a + o * (W + off0)); nr.append(a + o * (W + off1))
        return [world(q) for q in pts + nr[::-1]]
    arc = {i: S.c[i]["r"] * S.c[i]["th"] for i in S.dtin}
    end_post = C - S.pb - 5                                                            # the stands' end of the post-end bend
    gaps = sorted([(S.dtin[1] - 10, S.dtin[1] + arc[1] + 30)] +                      # the home bend: straight course, car park
                  [(J[k] - 10, J[k] + 170) for k in chute_len if k != 0])
    belts, d = [], gaps[0][1]
    for g0, g1 in gaps[1:] + [(end_post, end_post)]:
        g0 = min(g0, end_post)
        if g0 - d > 50:
            cut = max(d, min(g0, S.dtin[0]))                                          # trees up to the post-end bend, a bank after
            if cut - d > 50:
                belts.append({"note": "boards at 20 m, trees from 25 m", "poly": band(d, cut, 20, 60)})
            if g0 - cut > 50:
                belts.append({"note": "round the post-end bend to the stands: a shallow bank with tree pockets",
                              "poly": band(cut, g0, 18, 64), "bank": True})
        d = max(d, g1)
    ends = []
    for k, L in chute_len.items():
        q = S.at(J[k]) + S.tangent(P["chutes"][k]) * (L + 28)
        ends.append({"note": ("mound closing the straight course" if k == 0 and sprint else f"tree pocket at the end of the {names[k]}"), "at": world(q)})
    xb = float(S.c[1]["tin"][0] - X0)                         # the home bend's start, world x
    cen = np.mean([S.at(d) for d in np.arange(0, C, 20)], axis=0)
    Z = {
        "festival": {"x": [-20, 170], "z": sorted([m * 14, m * 110]), "note": "the festival lawn: marquees, kiosks, flags, the clock house"},
        "standLawn": {"x": [CHAIN_START - 8, x_end + 10], "z": sorted([m * (-W - LAWN), m * (-W - 1)]), "note": "the lawn and rail walk in front of the stands"},
        "paddock": {"x": [40, 120], "z": sorted([m * (-W - LAWN - STAND_DEPTH - 42), m * (-W - LAWN - STAND_DEPTH - 102)]), "note": "the parade ring and pre-parade ring behind the stands"},
        "standPark": {"x": [x_end + 25, xb + 260], "z": sorted([m * (-W - 25), m * (-W - 85)]), "note": "car park as a light festival strip (York's park()), beside the straight course past the home bend"},
        "belts": belts,
        "chuteEnds": ends,
        "lake": {"centre": world(cen + np.array([40.0, 80.0])), "radii": [80, 40], "angle": -20, "note": "an infield pond (parkland dressing)"},
        "fields": "beyond the belts: green-led flats with hedges",
    }
    checks = {
        "circuit (inside rail), m": round(C, 1), "circuit, furlongs": round(C / F, 2),
        "run-in (post to the home bend), m": round(d_home, 1),
        "straight past the post, m": S.pb,
        "bends (degrees, radius, arc m)": [[round(math.degrees(c_["th"])), c_["r"], round(c_["r"] * c_["th"])] for c_ in S.c],
        "share of the circuit on a bend": round(sum(arc.values()) / C, 2),
        "chutes, m": {names[i]: round(L, 1) for i, L in sorted(chute_len.items())},
        "stand plots, m": round(x_end - CHAIN_START, 1),
        "starts": {t: where(t) for t in trips},
    }
    return {
        "id": "tight", "name": P.get("name", "The Tight Track"), "family": "tight",
        "status": "DRAFT, 17 Nov 2026: the kit course plan (near-circle with chutes); not used by the game yet",
        "_about": "Built by tools/course/kit/tight_layout.py from a few numbers (params). Don't edit by hand.",
        "axes": "As York and the Park: origin = winning post on the inside rail; y up; on the home straight the horses run "
                "towards -x. hand -1: inside rail z = 0 on the horses' left, track to z = -trackWidth, stands beyond, "
                "infield +z; hand +1: the same mirrored.",
        "hand": P["hand"], "params": P, "trackWidth": W, "furlong": F, "runOut": P["runOut"], "home": round(d_home, 1),
        "surface": P["surface"], "floodlights": bool(P.get("lights")) or P["surface"] != "turf", "uphill": P["uphill"],
        "scenery": P["scenery"],
        "routes": out_routes, "starts": starts, "checks": checks,
        "routesNote": "Each start's route: 'round' for a start on a straight of the circuit; 'straight' for the straight "
                      "course (5f, 6f with the switch; a 5f stub where a course has none); otherwise the chute it starts "
                      "in, '-lap' when it goes once round first. Chutes are the line arriving at a bend carried on past it.",
        "chutes": [{"index": k, "name": names[k], "length": round(L, 1), "joinsAt": round(J[k], 1), "joins": world(S.at(J[k])),
                    "end": world(S.at(J[k]) + S.tangent(P["chutes"][k]) * L)} for k, L in sorted(chute_len.items())],
        "furlongPoles": [],
        "stands": {"frontZ": round(m * zf, 2), "lawn": LAWN, "plots": plots,
                   "note": "the configurator's fixed plots; each course's modules are in courses/kit/stand-config.json"},
        "festival": {"pieces": fest},
        "zones": Z,
        "variants": variants(),
        "heights": {"note": "flat; none of the ten has an uphill finish", "h": 0.0},
    }, samp, S


# ---------------------------------------------------------------- the plan (the racing papers' way: turned 180)
NAMES = {"park_clock_house": "clock house", "park_terrace": "terrace", "park_shed": "shed"}
COL = {"straight": "#2f5d8a", "chute": "#1f7a6b", "round": "#2b2b2b", "lap": "#b5651d"}
col = lambda r: COL["straight"] if r == "straight" else COL["round"] if r == "round" else COL["lap"] if r.endswith("-lap") else COL["chute"]


def draw(c, samp, S, outp, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP, Rectangle, Ellipse
    W, m = c["trackWidth"], -c["hand"]
    X0, Z0 = S.post
    # turned as the racing papers: the stands always along the bottom (left-handed: turned 180, the horses run left to
    # right; right-handed: the mirrored world flipped back, so they run right to left)
    T = lambda x, z: (-m * x, m * z)
    TW = lambda q: T(q[0] - X0, m * (q[1] - Z0))   # from the shape's own axes
    fig, (ax, az) = plt.subplots(2, 1, figsize=(14, 13.5), dpi=130, gridspec_kw={"height_ratios": [0.56, 0.44], "hspace": 0.42})
    Zn = c["zones"]
    P = c["params"]

    cen = np.mean([[a - X0, m * (b - Z0)] for a, b in (S.at(d) for d in np.arange(0, S.C, 20))], axis=0)

    def paint(ax, zoom):
        ax.set_facecolor("#e3e8cf")
        def rect(zone, fc, ec="none", alpha=1.0, lw=0.6, label=None, zorder=3):
            (x0, x1), (z0, z1) = zone["x"], zone["z"]
            a, b = T(x0, z0), T(x1, z1)
            ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec=ec, alpha=alpha, lw=lw, zorder=zorder))
            if label:
                ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, label, ha="center", va="center", fontsize=7.5, color="#333", zorder=5)
        for b in Zn["belts"]:
            ax.add_patch(MP([T(*q) for q in b["poly"]], closed=True, fc="#9cc4d6" if b.get("bank") else "#7fa463", alpha=0.8, ec="none", zorder=1))
        def outward(p):
            p = np.array(p, float)
            t = np.gradient(p, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
            return p + np.c_[t[:, 1], -t[:, 0]] * W
        circ = np.array([S.at(d) for d in np.arange(0, S.C, 3.0)])
        outer = outward(np.vstack([circ[-1:], circ, circ[:1]]))[1:-1]
        turf = "#c9b48a" if c["surface"] != "turf" else "#8db55f"
        ax.add_patch(MP([TW(v) for v in outer], closed=True, fc=turf, ec="#4f6f35", lw=0.8, zorder=2))
        ax.add_patch(MP([TW(v) for v in circ], closed=True, fc="#e3e8cf", ec="#4f6f35", lw=0.8, zorder=2))
        for ch in c["chutes"]:
            pts = S.spur(c["params"]["chutes"][ch["index"]], ch["length"], back=40.0)
            o = outward(pts)
            ax.add_patch(MP([TW(v) for v in list(pts) + list(o[::-1])], closed=True, fc=turf, ec="#4f6f35", lw=0.8, zorder=2))
        lk = Zn["lake"]; lx, lz = T(*lk["centre"])
        ax.add_patch(Ellipse((lx, lz), 2 * lk["radii"][0], 2 * lk["radii"][1], angle=-m * lk["angle"], fc="#a9cbe0", ec="#7aa3bd", lw=0.8, zorder=3))
        ax.text(lx, lz, "pond", ha="center", va="center", fontsize=7.5, color="#3d6680", zorder=4)
        rect(Zn["festival"], "#f3d9b8", ec="#c99a63")
        fz = Zn["festival"]; p = T(sum(fz["x"]) / 2, (fz["z"][1] if m > 0 else fz["z"][0]) - m * 10)
        ax.text(*p, "festival lawn", ha="center", va="center", fontsize=7.5, color="#333", zorder=4)
        rect(Zn["standLawn"], "#d8dcc0")
        rect(Zn["paddock"], "#cfe0b0", ec="#7f9b62", label="parade ring" if zoom else None)
        rect(Zn["standPark"], "#e4d4ec", ec="#a68bb4", label="car park as festival strip" if zoom else None)
        for e in Zn["chuteEnds"]:
            ax.add_patch(Ellipse(T(*e["at"]), 60, 36, fc="#b9cf8f", ec="#6f8f4a", lw=0.6, zorder=3))
        # the stand plots (fixed footprints) and the festival pieces
        for pl in c["stands"]["plots"]:
            z0 = pl["z"]; z1 = z0 - m * pl["depth"]
            a, b = T(pl["x0"], z0), T(pl["x1"], z1)
            fc = {"side": "#b9c3cf", "main": "#f2ede3", "pavilion": "#d59a85"}[pl["class"]]
            ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec="#6c6458", lw=0.6, zorder=4))
            if zoom:
                ax.text(*T(pl["x"], z0 - m * pl["depth"] / 2), pl["id"], ha="center", va="center", fontsize=10, fontweight="bold", color="#4a3f33", zorder=6)
                ax.text(*T(pl["x"], z0 - m * (pl["depth"] + 4)), f"{pl['name'] or pl['class']}\n{pl['class']}\n{pl['width']:.0f} m",
                        ha="center", va="top", fontsize=7.5, color="#4a3f33", zorder=6)
        for e in c["festival"]["pieces"]:
            x0, x1 = e["x"] - e["width"] / 2, e["x"] + e["width"] / 2
            z0 = e["z"]; z1 = z0 + m * e["depth"]
            a, b = T(x0, z0), T(x1, z1)
            fc = "#d59a85" if e["piece"] != "park_terrace" else "#d9d0bf"
            ax.add_patch(Rectangle((min(a[0], b[0]), min(a[1], b[1])), abs(b[0] - a[0]), abs(b[1] - a[1]), fc=fc, ec="#6c6458", lw=0.6, zorder=4))
            if zoom:
                ax.text(*T(e["x"], z0 + m * (e["depth"] + 3)), NAMES.get(e["piece"], e["piece"]), ha="center", va="bottom", fontsize=8, color="#4a3f33", zorder=6)
        # starts, post, furlongs, running direction
        for t, s in c["starts"].items():
            p = T(*s["at"])
            ax.plot(*p, marker="s", ms=5.5, color=col(s["route"]), mec="white", mew=0.6, zorder=6)
            if not zoom:
                v = np.array(p) - np.array(T(*cen))           # label outwards from the middle of the course
                v = v / max(1e-9, np.hypot(*v))
                off = (0, -14) if s["route"] == "straight" else (round(16 * v[0]), round(13 * v[1]))
                ax.annotate(t, p, xytext=off, textcoords="offset points", fontsize=8.5, fontweight="bold", color=col(s["route"]), ha="center", va="center", zorder=6)
        for fp in c["furlongPoles"]:
            ax.plot(*T(*fp["at"]), marker="|", ms=8, color="#333", zorder=6)
        ax.plot(*T(0, 0), marker="o", ms=8, color="#c0392b", mec="white", zorder=7)
        ax.annotate("winning post", T(0, 0), xytext=(-8 * m, 9), textcoords="offset points", ha="right" if m > 0 else "left", fontsize=8.5, color="#c0392b", fontweight="bold", zorder=7)
        for d in [S.C * k for k in (0.1, 0.32, 0.52, 0.72, 0.9)]:
            p, q = S.at(d), S.at(d - 40)
            ax.annotate("", TW(q), TW(p), arrowprops=dict(arrowstyle="->", color="#222", lw=1.2), zorder=6)
        if P["straight"] == 5:                      # the switch: the straight course's 6f, dashed
            sl = c["checks"]["chutes, m"]["straight course"] + c["home"]
            a, b = T(sl, -m * W / 2), T(6 * F + 30, -m * W / 2)
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#2f5d8a", ls=(0, (4, 3)), lw=1.2, zorder=5)
            if not zoom:
                ax.annotate("6f straight (switch)", b, xytext=(0, -14), textcoords="offset points", fontsize=7, color="#2f5d8a", ha="center", zorder=5)

    paint(ax, False); paint(az, True)
    xs = [T(*q)[0] for r in c["routes"].values() for q in r["insideRail"]] + [T(*e["at"])[0] for e in c["zones"]["chuteEnds"]]
    zs = [T(*q)[1] for r in c["routes"].values() for q in r["insideRail"]]
    ax.set_xlim(min(xs) - 90, max(xs) + 90); ax.set_ylim(min(zs) - 150, max(zs) + 70)
    az.set_xlim(*sorted([T(c["zones"]["standPark"]["x"][0] + 60, 0)[0], T(c["stands"]["plots"][0]["x0"] - 60, 0)[0]]))
    az.set_ylim(-W - 175, 125)
    for a_ in (ax, az):
        a_.set_aspect("equal"); a_.set_xticks([]); a_.set_yticks([])
        for t_ in a_.texts: t_.set_clip_on(True)
    az.set_title("The stand side and the festival lawn, closer: the configurator's fixed plots T1-T4 (post on the right; horses run left to right)" if m > 0 else
                 "The stand side and the festival lawn, closer: the configurator's fixed plots T1-T4 (right-handed: post on the left; horses run right to left)", fontsize=10, loc="left")
    ck = c["checks"]
    lights = ", floodlit" if c["floodlights"] else ""
    key = [f"{c['name']}: {'left' if c['hand'] < 0 else 'right'}-handed, {c['surface']}{lights}, {c['scenery']}",
           f"Circuit {ck['circuit (inside rail), m']:.0f} m ({ck['circuit, furlongs']:.1f}f), {ck['share of the circuit on a bend'] * 100:.0f}% of it on a bend; run-in {ck['run-in (post to the home bend), m']:.0f} m",
           "Bends: " + "; ".join("%d deg r %d m" % tuple(b[:2]) for b in ck["bends (degrees, radius, arc m)"]) + " (post end, home bend, home-end top, post-end top)",
           "Chutes: " + ", ".join(f"{k} {v:.0f} m" for k, v in ck["chutes, m"].items()),
           f"Straight course: {P['straight']:g}f" if P["straight"] else "No straight course (Chester): the 5f and 6f go round from the 6f chute",
           "Blue: straight course   green: in a chute   black: on a straight of the circuit   brown: once round first",
           f"Stand plots: {ck['stand plots, m']:.0f} m (T1-T4), {c['stands']['lawn']:.0f} m of lawn in front"]
    if P.get("note"): key.append("Note: " + P["note"])
    ax.text(0.0, -0.015, "\n".join(key), transform=ax.transAxes, fontsize=8.5, va="top", color="#222",
            bbox=dict(fc="white", ec="#bbb", alpha=0.92), zorder=8)
    x0, y0 = ax.get_xlim()[0] + 40, ax.get_ylim()[0] + 30
    ax.plot([x0, x0 + 200], [y0, y0], color="#222", lw=2); ax.text(x0 + 100, y0 + 10, "200 m", ha="center", fontsize=7.5)
    ax.set_title(title, fontsize=12, loc="left", color="#222")
    outp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outp, bbox_inches="tight", facecolor="white"); plt.close(fig)


def main():
    c, samp, S = build(dict(TIGHT))
    (REPO / "courses/tight-draft.json").write_text(json.dumps(c, separators=(",", ":")))
    draw(c, samp, S, REPO / "reference/tight/plan-draft.png",
         "The Tight Track (kit sharp, turning course): plan, DRAFT 17 Nov 2026. Turned as the racing papers' plans: stands along the bottom")
    print(json.dumps(c["checks"], indent=1))
    for n, r in c["routes"].items(): print(f"  route {n:9s} bends {r['bends']}")
    V = variants()
    names = list(V) if sys.argv[1:] == ["all"] else sys.argv[1:]
    for v in names:
        P = dict(TIGHT); P.update({k: x for k, x in V[v].items() if k in TIGHT or k in ("name", "note")})
        cv, sv, Sv = build(P)
        draw(cv, sv, Sv, REPO / f"reference/tight/plan-{v}.png", f"The Tight Track as {P['name']}: switches from the stand configurator")
        bad = [t for t, w in cv["checks"]["starts"].items() if "BEND" in w]
        print("variant", v, "OK" if not bad else f"STARTS ON A BEND: {bad}")


if __name__ == "__main__":
    main()
