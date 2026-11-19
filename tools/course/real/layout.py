"""Tier 2 courses, phase 1: the course plan, from one shared tool and a small file per course.

Owner, 17 Nov 2026 (19:36, 19:50): Epsom and Goodwood made in detail; the rest built into one shared framework (each
course's own track, undulations included, a consistent perimeter, a consistent finish zone of stands in plots with a
festival zone opposite). Tier 2: Newbury, Sandown, Chester, Doncaster, Haydock. 18 Nov: "So we've now made all the tier
one courses. We need to start looking at tier 2."

This is York's, Goodwood's and Epsom's layout.py made general: everything that belongs to one course is in
tools/course/real/<id>.json (which edges of OpenStreetMap's turf make each route's rail, where the post is, the starts),
and this script does the rest the same way for every course.

Sources (per course, in reference/<id>/)
  - osm-<id>.json: OpenStreetMap's turf (the leisure=track relation: an outer ring and its holes) and the stands, fetched
    through the owner's built-in browser. (c) OpenStreetMap contributors, ODbL; private reference only.
  - dem-course-20m.json: ground heights every 20 m (AWS Terrain Tiles, terrarium z15).
  - The starts: At The Races' course diagram (the labelled distances).

How a route's rail is made (the course file's "routes"):
  each route is a list of pieces in running order. A piece is a run of one ring's points ("ring": index into the OSM
  rings, "from", "to": point numbers, either way round, wrapping if need be), or {"lead": m} to carry the rail on
  straight before its first point (room behind the furthest start). "offset" moves a piece across towards the inside:
  0 = the edge IS the inside rail; e.g. 30 = the edge is the outer rail and the inside rail is 30 m in from it (where
  OSM's turf includes a jumps course on the inside, as at Newbury). The pieces are joined, then eased (a running average
  over "ease" metres) so the joins become gentle curves.

World axes, as York, Goodwood and Epsom: metres, y up, origin = the winning post on the inside rail; on the home straight
the horses run towards -x; z is the horses' left. Left-handed (hand -1): the inside rail is on their left and the track
runs to z = -trackWidth; right-handed (hand 1): the inside rail on their right, the track to z = +trackWidth.

Writes  courses/<id>-draft.json            the layout as data (routes, rails, bends, heights, starts)
        reference/<id>/plan-draft.png       the plan, north up, beside OSM's turf with its points numbered
        reference/<id>/profiles-draft.png   the ground under every route, post on the right

  python3 tools/course/real/layout.py newbury
"""
import json, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, Polygon

REPO = Path(__file__).resolve().parents[3]
F = 201.168
YD = 0.9144
STEP = 5.0

def trip_m(t):
    """'1m2f6y' -> metres"""
    import re
    m = re.fullmatch(r"(?:(\d+)m)?(?:(\d+)f)?(?:(\d+)y)?", t)
    if not m or not t: raise SystemExit(f"can't read the trip {t!r}")
    mi, fu, yd = (int(x) if x else 0 for x in m.groups())
    return mi * 8 * F + fu * F + yd * YD

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
    def project(self, q, after=0.0):
        """arc length of the nearest point, looking only at s >= after (a route that passes the post twice)"""
        if after <= 0: return LineString(self.p).project(Point(q))
        i = max(0, np.searchsorted(self.s, after) - 1)
        return self.s[i] + LineString(self.p[i:]).project(Point(q))

def left_of(t): return np.array([-t[1], t[0]])
def right_of(t): return np.array([t[1], -t[0]])

def chaikin(p, n):
    p = np.array(p, float)
    for _ in range(n):
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]):
            q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        q.append(p[-1]); p = np.array(q)
    return p

def resample(p, ds):
    L = Line(p); return np.array([L.at(s)[0] for s in np.arange(0, L.L + 1e-6, ds)])

def running_mean(q, k):
    k = max(1, int(k)) | 1
    pad = np.vstack([q[:1] - (q[1] - q[0]) * np.arange(k // 2, 0, -1)[:, None], q,
                     q[-1:] + (q[-1] - q[-2]) * np.arange(1, k // 2 + 1)[:, None]])
    return np.stack([np.convolve(pad[:, 0], np.ones(k) / k, mode="valid"),
                     np.convolve(pad[:, 1], np.ones(k) / k, mode="valid")], 1)

# ---------------------------------------------------------------- the course
class Course:
    def __init__(self, cid):
        self.id = cid
        self.C = json.loads((REPO / f"tools/course/real/{cid}.json").read_text())
        self.OSM = json.loads((REPO / f"reference/{cid}/osm-{cid}.json").read_text())
        self.DEM = json.loads((REPO / f"reference/{cid}/dem-course-20m.json").read_text())
        C, D = self.C, self.DEM
        self.hand = C["hand"]
        self.W = C.get("trackWidth", 26.0)
        self.lat0, self.lon0 = D["lat0"], D["lon0"]
        self.KX, self.KY = 111320.0 * math.cos(math.radians(self.lat0)), 110574.0
        self.rings = [np.array([self.en(q) for q in r["p"]]) for r in self.OSM["rings"]]
        self.DH = np.array(D["h_dm"], float) / 10.0
        for fx in C.get("demFix", []):      # a patch of bad ground data: cells in the box more than 'above' m over the
            x0, y0, x1, y1 = fx["box"]       # box's own median are dropped and filled in from their neighbours
            i0, i1 = int((x0 - D["x0"]) // D["step"]), int((x1 - D["x0"]) // D["step"]) + 1
            j0, j1 = int((y0 - D["y0"]) // D["step"]), int((y1 - D["y0"]) // D["step"]) + 1
            sub = self.DH[j0:j1, i0:i1]; bad = sub > np.median(sub) + fx.get("above", 1.5)
            H = self.DH.copy(); mask = np.zeros_like(H, bool); mask[j0:j1, i0:i1] = bad
            H[mask] = np.median(sub[~bad])
            for _ in range(400):
                A = H.copy(); A[1:-1, 1:-1] = (H[:-2, 1:-1] + H[2:, 1:-1] + H[1:-1, :-2] + H[1:-1, 2:]) / 4
                H[mask] = A[mask]
            self.DH = H
        lv = C.get("levelTurf")              # a flat course whose outer rail runs under banks (Chester: the city walls, the
        if lv:                               # road embankments): the 20 m tiles blur the banks into the turf, so every cell
            outer = Polygon(self.rings[0]).buffer(lv.get("margin", 10.0))   # on the turf (plus a margin) higher than the
            infield = Polygon(self.rings[1])                                # infield's median + 'above' comes down to it
            xs = D["x0"] + np.arange(D["nx"]) * D["step"]; ys = D["y0"] + np.arange(D["ny"]) * D["step"]
            on = np.array([[outer.contains(Point(x, y)) for x in xs] for y in ys])
            inf = np.array([[infield.contains(Point(x, y)) for x in xs] for y in ys])
            base = float(np.median(self.DH[inf])) + lv.get("above", 0.3)
            self.DH = np.where(on & (self.DH > base), base, self.DH)
            fa = lv.get("flatAround")       # the ground rationalised (owner, 19 Nov 13:45, Chester: "you can rationalise the
            if fa:                          # topo a bit from reality"): dead flat at the turf's level within r metres of
                ring0 = Polygon(self.rings[0])   # the turf, easing back to the real ground over the next 'ease' metres
                dist = np.array([[ring0.distance(Point(x, y)) for x in xs] for y in ys])
                k = np.clip((dist - fa["r"]) / fa.get("ease", 100.0), 0.0, 1.0)
                k = k * k * (3 - 2 * k)
                self.DH = base + (self.DH - base) * k
            # OSM features whose height the tiles took for ground (Chester: the Roodee Viaduct's deck read as a bank):
            # brought down to the level of the ground either side of them
            for fx in lv.get("osmFeatures", []):
                E = json.loads((REPO / f"reference/{cid}/{fx['file']}").read_text())["features"]
                for f in E:
                    if f["tags"].get("name") != fx["name"] or "p" not in f: continue
                    g = LineString([tuple(q) for q in f["p"]]).buffer(fx.get("buffer", 14.0))   # (osm-edges: metres already)
                    m = np.array([[g.contains(Point(x, y)) for x in xs] for y in ys])
                    ring = np.array([[g.buffer(30.0).contains(Point(x, y)) for x in xs] for y in ys]) & ~m
                    if m.any() and ring.any():
                        lvl = min(float(np.percentile(self.DH[ring], 30)), base + fx.get("above", 0.5))
                        self.DH = np.where(m & (self.DH > lvl), lvl, self.DH)
        self.RAIL ={name: self.rail(spec) for name, spec in C["routes"].items()}
        post = C["post"]
        L = self.RAIL[post["route"]]
        if "x" in post:      # metres east of the frame's origin, on the post route's home straight
            s = min(np.arange(max(0, L.L - post.get("searchLast", 2500)), L.L, 0.5), key=lambda t: abs(L.at(t)[0][0] - post["x"]))
        else:
            s = L.project(self.en(post["latlon"]), after=max(0, L.L - post.get("searchLast", 2500)))
        self.POST, self.RUN = L.at(s)
        self.XH = -self.RUN                                 # world x: against the running direction on the home straight
        self.ZH = left_of(self.RUN)                          # world z: the horses' left
        self.POST_GROUND = float(self.ground(self.POST + self.across(self.RUN) * self.W / 2))

    def en(self, ll): return np.array([(ll[1] - self.lon0) * self.KX, (ll[0] - self.lat0) * self.KY])
    def across(self, t):
        """from the inside rail across the track: the horses' right on a left-handed course, their left on a right-handed one"""
        return left_of(t) if self.hand > 0 else right_of(t)
    def inward(self, t): return -self.across(t)

    def piece(self, pc):
        r = self.rings[pc["ring"]]; n = len(r) - 1 if np.allclose(r[0], r[-1]) else len(r)
        a, b = pc["from"], pc["to"]
        step = pc.get("dir", 1 if b >= a else -1)
        idx, i = [a], a
        while i != b:
            i = (i + step) % n; idx.append(i)
        return r[idx]

    def rail(self, spec):
        """a route's inside rail: the pieces moved in by their offsets, joined, eased"""
        chunks = []
        for pc in spec["pieces"]:
            if "lead" in pc: continue
            p = resample(self.piece(pc), 2.0)
            off = pc.get("offset", 0.0)
            if isinstance(off, list):        # [a, b, m]: from a to b over the piece's first m metres (m < 0: its last -m)
                a, b, m = off; s = np.arange(len(p)) * 2.0; Lp = s[-1]
                k = np.clip(s / m, 0, 1) if m > 0 else np.clip((s - (Lp + m)) / -m, 0, 1)
                k = 0.5 - 0.5 * np.cos(np.pi * k)
                off = a + (b - a) * k
            if np.any(off):
                t = np.gradient(p, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
                p = p + np.array([self.inward(v) for v in t]) * np.reshape(off, (-1, 1))
                p = running_mean(p, 9)
            chunks.append(p)
        pts = np.vstack(chunks)
        lead = spec["pieces"][0].get("lead", 0) if spec["pieces"] else 0
        tail = spec.get("tail", 0)
        if lead:
            d = pts[0] - pts[min(5, len(pts) - 1)]; d /= np.hypot(*d); pts = np.vstack([pts[0] + d * lead, pts])
        if tail:
            d = pts[-1] - pts[max(-6, -len(pts))]; d /= np.hypot(*d); pts = np.vstack([pts, pts[-1] + d * tail])
        q = resample(chaikin(pts, 2), 2.0)
        q = running_mean(running_mean(q, spec.get("ease", self.C.get("ease", 60)) / 2.0), spec.get("ease", self.C.get("ease", 60)) / 2.0)
        return Line(q)

    def ground(self, p):
        D = self.DEM; DH = self.DH
        fx, fy = (p[0] - D["x0"]) / D["step"], (p[1] - D["y0"]) / D["step"]
        i = int(np.clip(math.floor(fx), 0, D["nx"] - 2)); j = int(np.clip(math.floor(fy), 0, D["ny"] - 2))
        a, b = np.clip(fx - i, 0, 1), np.clip(fy - j, 0, 1)
        return (DH[j, i] * (1 - a) + DH[j, i + 1] * a) * (1 - b) + (DH[j + 1, i] * (1 - a) + DH[j + 1, i + 1] * a) * b

    def world(self, p):
        q = np.asarray(p) - self.POST
        return [round(float(q @ self.XH), 2), round(float(q @ self.ZH), 2)]
    def world_dir(self, v):
        return [round(float(np.asarray(v) @ self.XH), 4), round(float(np.asarray(v) @ self.ZH), 4)]

    def post_s(self, name):
        L = self.RAIL[name]; return L.project(self.POST, after=max(0, L.L - self.C["post"].get("searchLast", 2500)))

    def samples(self, name):
        """[(rail point, metres to go)] every STEP m, index 0 = the end of the run-out past the post"""
        L = self.RAIL[name]; sp = self.post_s(name)
        s_end = min(L.L, sp + self.C.get("runOut", 100.0))
        return [(L.at(s)[0], round(float(sp - s), 2)) for s in np.arange(s_end, -1e-6, -STEP)]

    def dem_heights(self, samp):
        pts = np.array([q[0] for q in samp])
        run = -np.gradient(pts, axis=0); run /= np.linalg.norm(run, axis=1)[:, None]
        h = np.array([self.ground(p + self.across(t) * self.W / 2) for p, t in zip(pts, run)])
        k = 9; h = np.convolve(np.pad(h, k // 2, mode="edge"), np.ones(k) / k, mode="valid")
        return h - self.POST_GROUND

    def bends_of(self, samp):
        """[metres to go at the start, at the end, degrees turned]; turns towards the inside rail positive (left on a
        left-handed course, right on a right-handed one), as York, Goodwood and Epsom"""
        pts = np.array([s[0] for s in samp])[::-1]; ds = np.array([s[1] for s in samp])[::-1]
        run = np.diff(pts, axis=0)
        hd = np.unwrap(np.arctan2(run[:, 1], run[:, 0]))
        per = np.convolve(np.gradient(hd), np.ones(5) / 5, mode="same")
        lim = math.radians(0.35) * STEP / 5.0
        out, i, n = [], 0, len(hd)
        while i < n:
            if abs(per[i]) > lim:
                sgn = np.sign(per[i]); j = i
                while j < n and abs(per[j]) > lim and np.sign(per[j]) == sgn: j += 1
                turn = math.degrees(hd[min(j, n - 1)] - hd[i]) * (-self.hand)   # anticlockwise = left
                if abs(turn) > 4 and ds[min(j, n - 1)] > 0:
                    out.append([round(float(ds[i]), 1), round(float(max(ds[min(j, n - 1)], 0.0)), 1), round(turn, 1)])
                i = j + 1
            else:
                i += 1
        return out

    def min_radius(self, samp, lo, hi):
        pts = np.array([s[0] for s in samp]); ds = np.array([s[1] for s in samp])
        best = (1e9, None)
        for i in range(4, len(pts) - 4):
            if not (lo <= ds[i] <= hi): continue
            a, b, c = pts[i - 4], pts[i], pts[i + 4]
            ab, bc, ca = np.hypot(*(b - a)), np.hypot(*(c - b)), np.hypot(*(a - c))
            area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2
            if area > 1e-6:
                R = ab * bc * ca / (4 * area)
                if R < best[0]: best = (R, ds[i])
        return round(best[0]), best[1]

    def turf_check(self, p):
        """how far (m) a point is inside OSM's turf (negative = outside it)"""
        outer = Polygon(self.rings[0]); holes = [Polygon(r) for r in self.rings[1:]]
        P = Point(p)
        inside = outer.contains(P) and not any(h.contains(P) for h in holes)
        d = min([outer.exterior.distance(P)] + [h.exterior.distance(P) for h in holes])
        return round(d if inside else -d, 1)

# ---------------------------------------------------------------- build
def main(cid):
    c = Course(cid); C = c.C
    routes, starts, profiles = {}, {}, {}
    for name in C["routes"]:
        samp = c.samples(name)
        ds = np.array([s[1] for s in samp])
        h = c.dem_heights(samp)
        profiles[name] = (ds, h)
        routes[name] = {
            "d0": float(ds[0]), "spacing": STEP,
            "insideRail": [c.world(s[0]) for s in samp],
            "bends": c.bends_of(samp),
            "heights": {"from": float(ds[0]), "spacing": STEP, "h": [round(float(v), 2) for v in h],
                        "note": "ground height (m, against the post's) every 'spacing' metres to go from 'from', across the middle "
                                "of the track, smoothed over about 40 m (AWS Terrain Tiles)"},
            "length": float(ds[-1]),
        }
    for trip, st in C["starts"].items():
        r = st["route"]; L = c.RAIL[r]; sp = c.post_s(r); dist = trip_m(st.get("trip", trip))
        if dist > sp: raise SystemExit(f"{trip} ({dist:.0f} m) is beyond the {r} route ({sp:.0f} m)")
        p, t = L.at(sp - dist)
        mid = p + c.across(t) * c.W / 2
        starts[trip] = {"distance": round(dist, 1), "route": r, "at": c.world(p), "running": c.world_dir(t),
                        "onStraight": r == "straight", "groundM": round(float(c.ground(mid)) - c.POST_GROUND, 1),
                        "expected": st.get("expected", ""), "inTurfM": c.turf_check(mid)}
    checks = {"post: ground above sea level, m": round(c.POST_GROUND, 1)}
    for name in C["routes"]:
        samp = c.samples(name)
        checks[f"{name}: length behind the post, m"] = round(c.post_s(name), 1)
        checks[f"{name}: tightest radius, m (at m to go)"] = c.min_radius(samp, 0, 1e5)
        checks[f"{name}: bends"] = routes[name]["bends"]
        ds, h = profiles[name]
        checks[f"{name}: ground every furlong to the post, m"] = [round(float(np.interp(k * F, ds, h)), 1)
                                                                  for k in range(int(ds[-1] // F), -1, -1)]
    STR = c.RAIL[C["post"]["route"]]; sps = c.post_s(C["post"]["route"])
    poles = [{"furlongs": k, "at": c.world(STR.at(sps - k * F)[0])} for k in range(1, 6)]
    north = c.world_dir(np.array([0.0, 1.0]))
    out = {
        "id": cid, "name": C["name"] + ", draft",
        "status": "DRAFT, phase 1 (the course plan), %s: the shape from OpenStreetMap's outline of the turf "
                  "(reference/%s/osm-%s.json, (c) OpenStreetMap contributors, ODbL) and the real ground "
                  "(reference/%s/dem-course-20m.json, AWS Terrain Tiles)." % (C.get("date", ""), cid, cid, cid),
        "postGroundM": round(c.POST_GROUND, 1),
        "_about": "Built by tools/course/real/layout.py from tools/course/real/%s.json. Don't edit by hand." % cid,
        "axes": "As York, Goodwood and Epsom: origin = winning post on the inside rail; y up. On the home straight the horses run "
                "towards -x; z is the horses' left. " + ("LEFT-handed: the inside rail (z = 0) on the horses' left, the track to "
                "z = -trackWidth on their right." if c.hand < 0 else "RIGHT-handed: the inside rail (z = 0) on the horses' right, "
                "the track to z = +trackWidth on their left."),
        "direction": "anticlockwise (left-handed)" if c.hand < 0 else "clockwise (right-handed)", "hand": c.hand,
        "compass": {"north": north, "note": "the direction of north in world x, z"},
        "trackWidth": c.W, "furlong": F, "runOut": C.get("runOut", 100.0), "camber": C.get("camber", 0.0),
        "measured": {"checks": checks},
        "routes": routes,
        "routesNote": "Each route is its inside rail sampled every 'spacing' metres, from d0 (metres to go, negative = the run-out past "
                      "the post) back to its far end; 'bends' for the race engine as [metres to go at the start, at the end, degrees "
                      "turned (positive = towards the inside rail)]; 'heights' the ground along it. " + C.get("routesNote", ""),
        "starts": starts,
        "furlongPoles": poles,
    }
    (REPO / f"courses/{cid}-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    print(json.dumps(checks, indent=1))
    for t, s in starts.items():
        print(f"  {t:8s} {s['route']:9s} {s['distance']:7.1f} m  ground {s['groundM']:6.1f}  in the turf by {s['inTurfM']} m  ({s['expected']})")
    draw(c, out, profiles)
    return out

# ---------------------------------------------------------------- drawings
INK, MUTED, POSTC = "#2b2b2b", "#6b6b6b", "#c0392b"
PAL = ["#1d1d1d", "#2f5d8a", "#b03a8a", "#b5651d", "#3a8a5f", "#8a3a3a", "#5d4a8a"]

def draw(c, out, profiles):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    from shapely.ops import unary_union
    C = c.C; RC = {n: PAL[i % len(PAL)] for i, n in enumerate(C["routes"])}
    ext = np.vstack(c.rings); w, h = np.ptp(ext[:, 0]), np.ptp(ext[:, 1])
    fig, axs = plt.subplots(2, 1, figsize=(16, 16 * (2 * h / w) * 0.62 + 2.5), dpi=120)
    ax = axs[0]
    o = c.rings[0]; ax.fill(o[:, 0], o[:, 1], fc="#d7e6cc", ec="#9cb88a", lw=0.6, zorder=0)
    for r in c.rings[1:]: ax.fill(r[:, 0], r[:, 1], fc="white", ec="#9cb88a", lw=0.6, zorder=0)
    strips = []
    for name in C["routes"]:
        L = c.RAIL[name]; sp = c.post_s(name)
        mid = [L.at(s)[0] + c.across(L.at(s)[1]) * c.W / 2 for s in np.arange(0, min(L.L, sp + C.get("runOut", 100)), 2.0)]
        strips.append(LineString(mid).buffer(c.W / 2, cap_style=2))
    turf = unary_union(strips)
    for g in ([turf] if turf.geom_type == "Polygon" else turf.geoms):
        ax.add_patch(MP(np.array(g.exterior.coords), closed=True, fc="#5f9a48", ec="#2e5a22", lw=0.6, alpha=0.9, zorder=1))
        for hole in g.interiors:
            ax.add_patch(MP(np.array(hole.coords), closed=True, fc="white", ec="#2e5a22", lw=0.6, zorder=1.1))
    for name in C["routes"]:
        L = c.RAIL[name]; sp = c.post_s(name)
        q = np.array([L.at(s)[0] for s in np.arange(0, min(L.L, sp + C.get("runOut", 100)), 4.0)])
        ax.plot(q[:, 0], q[:, 1], color=RC[name], lw=1.0, zorder=2, label=f"{name} ({C['routes'][name].get('note', '')})")
    for b in c.OSM.get("stands", []):
        q = np.array([c.en(x) for x in b["p"]]); ax.fill(q[:, 0], q[:, 1], fc="#f4efe6", ec="#8a7350", lw=0.6, zorder=3)
    for t, s in out["starts"].items():
        L = c.RAIL[s["route"]]; p, tt = L.at(c.post_s(s["route"]) - s["distance"])
        b = p + c.across(tt) * c.W
        ax.plot([p[0], b[0]], [p[1], b[1]], color="white", lw=2.4, solid_capstyle="butt", zorder=4)
        off = C["starts"][t].get("label", [8, 8])
        ax.annotate(t, (p + b) / 2, xytext=off, textcoords="offset points", fontsize=8.5, fontweight="bold", color=RC[s["route"]],
                    bbox=dict(fc="white", ec="none", alpha=0.8, pad=0.5), zorder=5)
    ax.plot(*c.POST, marker="o", ms=8, color=POSTC, mec="white", zorder=6)
    ax.annotate("winning post", c.POST, xytext=(-20, 14), textcoords="offset points", fontsize=9, color=POSTC, fontweight="bold")
    STR = c.RAIL[C["post"]["route"]]; sps = c.post_s(C["post"]["route"])
    for k in range(1, 9):
        if sps - k * F < 0: break
        p = STR.at(sps - k * F)[0]; ax.plot(*p, marker="o", ms=2.5, color=INK, zorder=6)
        ax.annotate(f"{k}f", p, xytext=(-4, 6), textcoords="offset points", fontsize=7, color=MUTED)
    for name in C["routes"]:
        L = c.RAIL[name]; sp = c.post_s(name)
        for dd in C["routes"][name].get("arrows", []):
            p, t = L.at(sp - dd); ax.annotate("", p + t * 70, p, arrowprops=dict(arrowstyle="->", color=RC[name], lw=1.2))
    ax.set_aspect("equal"); ax.autoscale_view(); ax.margins(0.04)
    xl, yl = ax.get_xlim(), ax.get_ylim()
    ax.plot([xl[0] + 30, xl[0] + 230], [yl[0] + 30, yl[0] + 30], color=INK, lw=2); ax.text(xl[0] + 130, yl[0] + 42, "200 m", ha="center", fontsize=7.5)
    ax.annotate("N", (xl[1] - 40, yl[0] + 130), xytext=(xl[1] - 40, yl[0] + 40), ha="center", fontsize=10, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK))
    ax.set_xticks([]); ax.set_yticks([]); ax.legend(loc=C.get("legend", "lower right"), fontsize=7.5, frameon=False)
    ax.set_title(f"{C['name']}: course plan, DRAFT {C.get('date', '')} (north up). "
                 f"{'Left' if c.hand < 0 else 'Right'}-handed. Pale green: OpenStreetMap's turf; dark green: the game's track "
                 f"({c.W:.0f} m) on each route; white bars: the starts", fontsize=10, loc="left", color=INK)
    ax = axs[1]
    for k, r in enumerate(c.rings):
        ax.plot(r[:, 0], r[:, 1], color="#2e5a22" if k == 0 else "#2f5d8a", lw=0.7)
        for i, q in enumerate(r):
            if i % C.get("numberEvery", 1) == 0:
                ax.plot(*q, marker="o", ms=1.6, color="#2e5a22" if k == 0 else "#2f5d8a")
                ax.annotate(str(i), q, xytext=(1.5, 1.5), textcoords="offset points", fontsize=5, color="#2e5a22" if k == 0 else "#2f5d8a")
    for name, L in c.RAIL.items():
        ax.plot(L.p[:, 0], L.p[:, 1], color=RC[name], lw=0.9, alpha=0.8)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("OpenStreetMap's turf: ring 0 (outer, green) and the holes (blue), points numbered; each route's inside rail "
                 "after easing", fontsize=10, loc="left", color=INK)
    fig.tight_layout(); fig.savefig(REPO / f"reference/{c.id}/plan-draft.png", facecolor="white"); plt.close(fig)

    panels = C.get("profilePanels", [[n, [t for t, s in C["starts"].items() if s["route"] == n], n] for n in C["routes"]])
    fig, axs = plt.subplots(len(panels), 1, figsize=(12, 2.9 * len(panels)), dpi=120, squeeze=False)
    for ax, (name, trips, title) in zip(axs[:, 0], panels):
        ds, h = profiles[name]
        dists = [out["starts"][t]["distance"] for t in trips] or [ds[-1]]
        top = max(dists) + 60
        m = (ds <= top) & (ds >= -40)
        ax.fill_between(-ds[m] / F, -100, h[m], color="#cfd9b0")
        ax.plot(-ds[m] / F, h[m], color=RC[name], lw=1.6)
        for t, dd in zip(trips, dists):
            ax.axvline(-dd / F, color=MUTED, lw=0.6, ls=":")
            ax.text(-dd / F, h[m].max() + 0.4, t, ha="center", fontsize=8, fontweight="bold", color=INK)
        ax.axvline(0, color=POSTC, lw=1); ax.text(0.05, h[m].min() - 0.8, "post", color=POSTC, fontsize=8)
        for b in out["routes"][name]["bends"]:
            if b[0] <= top: ax.axvspan(-b[0] / F, -b[1] / F, color="#000000", alpha=0.06)
        lo, hi = h[m].min(), h[m].max(); pad = max(1.5, (hi - lo) * 0.15)
        ax.set_ylim(lo - pad, hi + pad * 1.6); ax.set_xlim(-top / F, 0.3)
        ax.set_ylabel("m against the post", fontsize=8); ax.tick_params(labelsize=7)
        ax.set_title(title, fontsize=9, loc="left")
    axs[-1, 0].set_xlabel("furlongs to go (grey bands: bends). Heights from the AWS Terrain Tiles (real ground), smoothed over about 40 m",
                          fontsize=8)
    fig.tight_layout(); fig.savefig(REPO / f"reference/{c.id}/profiles-draft.png", facecolor="white"); plt.close(fig)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "newbury")
