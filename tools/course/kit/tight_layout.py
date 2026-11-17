"""The Tight Track: the kit-made sharp, turning course, as data and a plan, from a few numbers instead of a map.

The second of the three generic courses (the brief: claude/next-chat-kit-courses.md; the Park first, then the Tight
Track, then the Hill Track). It stands in for the ten sharp, turning courses (the design map's "UK courses" tab):
Catterick, Chester, Kempton, Lingfield (AW), Musselburgh, Ripon, Southwell, Thirsk, Windsor and Wolverhampton. Their
switches (hand, straight course, surface, scenery, floodlights) are read from the stand configurator's data
(courses/kit/stand-config.json, written by stand_config.py), so they live in one place.

The shape: about 1m1f round (1,747 m, 8.7f) and made of turning: a rounded triangle, so the horses are on a bend for nearly
half the circuit (Chester's, Kempton's and Wolverhampton's character; the Park's long straights are what it isn't).
The same kit as the Park: a polygon with a rounded corner at each vertex (a radius per corner). Going round from the
winning post:
  - a short straight past the post (130 m), then the post-end bend: a long sweeping turn of about 150 degrees;
  - the back straight, running on the diagonal up to the far corner; its line carried on past the post-end bend as the
    7f/1m chute;
  - the far corner (about 100 degrees) and a short side down to the home bend;
  - the home bend: sharp (95 m radius, about 110 degrees) into a short run-in of 336 m (1.7f); the home straight's line
    carried on past the home bend as the straight course (5f or 6f), or a 5f stub where a course has none.

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
    # radius of the bend at each corner: 0 the post-end bend, 1 the home bend, 2 the far corner
    "corners": [[-400.0, 0.0], [600.0, 0.0], [450.0, 450.0]],
    "radii": [100.0, 95.0, 105.0],
    "pastPost": 130.0,       # straight track past the winning post before the post-end bend
    "straight": 5.0,         # the straight course in furlongs (5 or 6); 0 = none (a 5f stub is still laid, for the 5f)
    "room": 30.0,            # straight track behind the furthest start in a chute
    "runOut": 120.0,         # pulling up after the post (on the straight past it, into the post-end bend)
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
FESTIVAL = [("park_clock_house", 95.0, 40.0), ("park_terrace", 67.0, 38.0), ("park_terrace", 123.0, 38.0),
            ("park_shed", 45.0, 72.0), ("park_shed", 150.0, 72.0)]


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

    def piece_at(self, d):
        dd = (d + self.pb) % self.C - self.pb
        for p in self.pieces:
            if p[1] - 1e-6 <= dd <= p[1] + p[2] + 1e-6:
                return p, dd
        return None, dd


def build(P):
    W = P["trackWidth"]
    S = TightShape(P)
    C = S.C
    ring = lambda d0, d1: [S.at(d) for d in np.arange(d0, d1 + 1e-6, 2.0)]
    runout = [S.at(-k) for k in np.arange(P["runOut"], 0, -2.0)]
    d_home, d_far, d_post = S.dtin[1], S.dtin[2], S.dtin[0]       # the home bend, the far corner, the post-end bend
    st_f = P["straight"] if P["straight"] > 0 else 5.0              # no straight course: still a 5f stub
    st_len = st_f * F + P["room"] - d_home
    chute_len = TRIPS["1m"] * F - d_post + P["room"]                 # the 7f/1m chute: the 1m start plus room
    routes = {
        "straight": runout + ring(0, d_home) + S.chute(1, st_len),
        "round": runout + ring(0, C + d_home - 2.0),
        "chute": runout + ring(0, d_post) + S.chute(0, chute_len),
        "lap": runout + ring(0, C + d_post) + S.chute(0, chute_len),
    }
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
    sprint6 = P["straight"] >= 6
    route_of = {"5f": "straight", "6f": "straight" if sprint6 else "round", "7f": "chute", "1m": "chute",
                "1m1f": "round", "1m2f": "round", "1m4f": "lap", "1m6f": "lap", "2m": "lap"}
    starts = {}
    for trip, f in TRIPS.items():
        r = route_of[trip]; dist = f * F
        s = samp[r]; ds = np.array([q[1] for q in s])
        if dist > ds[-1]: raise SystemExit(f"{trip} is beyond the {r} route")
        i = int(np.searchsorted(ds, dist)); p = s[i][0]; run = s[i - 1][0] - s[i][0]
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": world(p), "running": wdir(run / np.hypot(*run)),
                        "onStraight": r == "straight"}
    out_routes = {k: {"d0": round(v[0][1], 1), "spacing": STEP, "insideRail": [world(p) for p, d in v], "bends": bends_of(v)}
                  for k, v in samp.items()}

    def where(trip):
        """where a start lies: in a chute, or on a straight (and how far to the next bend); never on a bend"""
        s = starts[trip]; d = s["distance"]
        if s["route"] == "straight" and d > d_home:
            return "in the straight course, %.0f m up from the home bend" % (d - d_home)
        if s["route"] in ("chute", "lap") and (d % C) > d_post - 1e-6 and (s["route"] == "chute" or d > C):
            return "in the 7f/1m chute, %.0f m up from the post-end bend" % ((d % C) - d_post)
        p, dd = S.piece_at(d)
        lap = " (once round first)" if d > C else ""
        return ("on a straight, %.0f m before the next bend%s" % (dd - p[1], lap)) if p[0] == "edge" else "ON A BEND"

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

    # the perimeter zones (York's and the Park's zone types)
    def band(d0, d1, off0, off1):
        pts, nr = [], []
        for d in np.arange(d0, d1 + 1e-6, 10.0):
            a, b = S.at(d), S.at(d + 1.0); t = (b - a) / np.linalg.norm(b - a)
            o = np.array([t[1], -t[0]])                       # right of the reverse direction: outside the circuit
            pts.append(a + o * (W + off0)); nr.append(a + o * (W + off1))
        return [world(q) for q in pts + nr[::-1]]
    end_st = S.c[1]["tin"] + S.c[1]["u"] * (st_len + 30)
    end_chute = S.c[0]["tin"] + S.c[0]["u"] * (chute_len + 25)
    xb = float(S.c[1]["tin"][0] - X0)                         # the home bend's start, world x
    Z = {
        "festival": {"x": [-10, 210], "z": sorted([m * 14, m * 110]), "note": "the festival lawn: marquees, kiosks, flags, the clock house"},
        "standLawn": {"x": [CHAIN_START - 8, x_end + 10], "z": sorted([m * (-W - LAWN), m * (-W - 1)]), "note": "the lawn and rail walk in front of the stands"},
        "paddock": {"x": [40, 120], "z": sorted([m * (-W - LAWN - STAND_DEPTH - 42), m * (-W - LAWN - STAND_DEPTH - 102)]), "note": "the parade ring and pre-parade ring behind the stands"},
        "standPark": {"x": [x_end + 25, xb + 20], "z": sorted([m * (-W - 25), m * (-W - 85)]), "note": "car park as a light festival strip (York's park()), up to the home bend"},
        "belts": [
            {"note": "from the home bend (clear of the straight course) round the far corner and along the back straight: boards at 20 m, trees from 25 m", "poly": band(d_home + 130, d_post - 40, 20, 60)},
            {"note": "round the post-end bend, between the chute and the stands: a shallow bank with tree pockets", "poly": band(d_post + 110, C - S.pb + 60, 18, 64), "bank": True},
        ],
        "chuteEnds": [{"note": "mound closing the straight course", "at": world(end_st)},
                      {"note": "tree pocket at the top of the 7f/1m chute", "at": world(end_chute)}],
        "lake": {"centre": world(np.array([400.0, 170.0])), "radii": [75, 32], "angle": -35, "note": "an infield pond (parkland dressing)"},
        "fields": "beyond the belts: green-led flats with hedges",
    }
    checks = {
        "circuit (inside rail), m": round(C, 1), "circuit, furlongs": round(C / F, 2),
        "run-in (post to the home bend), m": round(d_home, 1),
        "straight past the post, m": S.pb,
        "bends (degrees, radius, arc m)": [[round(math.degrees(c_["th"])), c_["r"], round(c_["r"] * c_["th"])] for c_ in S.c],
        "share of the circuit on a bend": round(sum(c_["r"] * c_["th"] for c_ in S.c) / C, 2),
        "straight course (incl. stub), m from the home bend": round(st_len, 1), "7f/1m chute, m": round(chute_len, 1),
        "stand plots, m": round(x_end - CHAIN_START, 1),
        "starts": {t: where(t) for t in TRIPS},
    }
    return {
        "id": "tight", "name": P.get("name", "The Tight Track"), "family": "tight",
        "status": "DRAFT, 17 Nov 2026: the kit course plan; not used by the game yet",
        "_about": "Built by tools/course/kit/tight_layout.py from a few numbers (params). Don't edit by hand.",
        "axes": "As York and the Park: origin = winning post on the inside rail; y up; on the home straight the horses run "
                "towards -x. hand -1: inside rail z = 0 on the horses' left, track to z = -trackWidth, stands beyond, "
                "infield +z; hand +1: the same mirrored.",
        "hand": P["hand"], "params": P, "trackWidth": W, "furlong": F, "runOut": P["runOut"], "home": round(d_home, 1),
        "surface": P["surface"], "floodlights": bool(P.get("lights")) or P["surface"] != "turf", "uphill": P["uphill"],
        "scenery": P["scenery"],
        "routes": out_routes, "starts": starts, "checks": checks,
        "routesNote": "straight: 5f (and 6f with the switch) down the straight course; courses without one race the 5f from "
                      "a stub on the same line. chute: 7f and 1m from the back straight carried on past the post-end bend. "
                      "round: the 6f without a 6f straight (the back straight), the 1m1f (just past the post) and the 1m2f "
                      "(the home straight, once round). lap: 1m4f (the short side), 1m6f (the back straight) and 2m (the chute), once round first.",
        "furlongPoles": [{"furlongs": k, "at": world(S.at(k * F))} for k in range(1, 2)],
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
    fig, (ax, az) = plt.subplots(2, 1, figsize=(14, 13.5), dpi=130, gridspec_kw={"height_ratios": [0.56, 0.44]})
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
        st_len = c["checks"]["straight course (incl. stub), m from the home bend"]
        for i, L in ((1, st_len), (0, c["checks"]["7f/1m chute, m"])):
            cc = S.c[i]
            pts = [cc["tin"] - cc["u"] * 40 + cc["u"] * k for k in np.arange(0, L + 41, 4.0)]
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
            ax.plot(*p, marker="s", ms=5.5, color=COL[s["route"]], mec="white", mew=0.6, zorder=6)
            if not zoom:
                off = {"5f": (0, -14), "6f": (0, -14) if s["route"] == "straight" else (0, 9), "7f": (16, 6), "1m": (16, 6),
                       "1m1f": (0, -16), "1m2f": (0, -16)}.get(t, (0, 9))
                ax.annotate(t, p, xytext=off, textcoords="offset points", fontsize=8.5, fontweight="bold", color=COL[s["route"]], ha="center", zorder=6)
        for fp in c["furlongPoles"]:
            ax.plot(*T(*fp["at"]), marker="|", ms=8, color="#333", zorder=6)
        ax.plot(*T(0, 0), marker="o", ms=8, color="#c0392b", mec="white", zorder=7)
        ax.annotate("winning post", T(0, 0), xytext=(-8 * m, 9), textcoords="offset points", ha="right" if m > 0 else "left", fontsize=8.5, color="#c0392b", fontweight="bold", zorder=7)
        for d in (250, 640, 1150, 1540, 1760):
            p, q = S.at(d), S.at(d - 40)
            ax.annotate("", TW(q), TW(p), arrowprops=dict(arrowstyle="->", color="#222", lw=1.2), zorder=6)
        if P["straight"] < 6:                       # the switch: the straight course's 6f, dashed
            sl = c["checks"]["straight course (incl. stub), m from the home bend"] + c["home"]
            a, b = T(sl, -m * W / 2), T(6 * F + 30, -m * W / 2)
            ax.plot([a[0], b[0]], [a[1], b[1]], color="#2f5d8a", ls=(0, (4, 3)), lw=1.2, zorder=5)
            if not zoom:
                ax.annotate("6f straight (switch)", b, xytext=(0, -14), textcoords="offset points", fontsize=7, color="#2f5d8a", ha="center", zorder=5)

    paint(ax, False); paint(az, True)
    xs = [T(*q)[0] for r in c["routes"].values() for q in r["insideRail"]] + [T(*e["at"])[0] for e in c["zones"]["chuteEnds"]]
    zs = [T(*q)[1] for r in c["routes"].values() for q in r["insideRail"]]
    ax.set_xlim(min(xs) - 90, max(xs) + 90); ax.set_ylim(min(zs) - 150, max(zs) + 250)
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
           "Bends: post end %d deg r %d m; home bend %d deg r %d m; far corner %d deg r %d m" % tuple(v for b in (ck["bends (degrees, radius, arc m)"][i] for i in (0, 1, 2)) for v in b[:2]),
           f"Straight course: {P['straight']:g}f" if P["straight"] else "No straight course: a 5f stub on the home straight's line; the 6f goes round",
           "Blue: straight course   green: 7f/1m chute   black: round   brown: once round first",
           f"Stand plots: {ck['stand plots, m']:.0f} m (T1-T4), {c['stands']['lawn']:.0f} m of lawn in front"]
    if P.get("note"): key.append("Note: " + P["note"])
    ax.text(0.01, 0.99, "\n".join(key), transform=ax.transAxes, fontsize=8.5, va="top", color="#222",
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
