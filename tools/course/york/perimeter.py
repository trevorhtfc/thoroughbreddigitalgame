"""York, the next phase: the Knavesmire's surroundings (owner, 16 Nov evening, on his aerial view):

  "in terms of perimeter we have some stuff to figure out.. so we have pockets of heavy planting where we can use the
  ascot planting type. we have some landscaped sloping areas as per the light blue with pockets of planting.. i guess
  treat these a bit like the dyke but a bit shallower and with some planting. the light purple zones are tricky as they
  are car parks.. either we show some vehicles.. or we just show some marquees etc?.. could be fun. less crowd but still
  a festival kind of thing? then we have some farmers fields and more landscape in other areas... the key is to use the
  advertising boards, mounds, marquees etc all to try and ensure the camera has its view terminated by something"

His zones are set out against the track itself (metres along a route, metres beyond its outer rail), read off his
mark-up; everything else comes from OpenStreetMap (reference/york/osm-surround.json: woods, fields, houses, roads,
hedges; map data (c) OpenStreetMap contributors, ODbL). World axes as york.json: x along the home straight (the post
at 0, the straight course's far end at about +1220), z +infield; the back straight at about z +400 to +600, the
1m6f spur running out to about x -540; the stands at z < -26.

  belts     green: Ascot's planting type: boards just beyond the outer rail, then a deep belt of trees behind
  banks     light blue: shallow grassy banks (as the Dyke, about half its height), with pockets of trees on them
  fields    pink: the farmers' fields round the chutes (OSM farmland), hedged
  parks     light purple: the car parks, as a lighter festival: marquees, a big top, kiosks, the balloon pods,
            flags and boards, a thinner crowd on trodden ground
  the rest  OSM woods filled with trees; leafy suburbs (garden trees) where OSM has houses; roads with trees along
            them; field hedges; and at the far end of the straight course a mound with boards and trees across the
            head-on camera's view.
"""
import json, math, random
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parents[3]
KX, KY = 111320.0 * math.cos(math.radians(53.937)), 110574.0
DESIGNS = ["green", "cream", "navy", "white"]
KINDS = ("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")


def r2(v): return round(float(v), 2)


class Route:
    """A route's inside rail, its running direction and outward normal (towards the outer rail and beyond), by metres
    to go."""
    def __init__(self, r, W):
        self.p = np.array(r["insideRail"], float); self.d0, self.sp, self.W = r["d0"], r["spacing"], W
        n = len(self.p); t = np.zeros_like(self.p)
        for i in range(n):
            a, b = self.p[max(0, i - 1)], self.p[min(n - 1, i + 1)]
            v = a - b; t[i] = v / (np.hypot(*v) or 1)
        self.t = t; self.n = np.c_[-t[:, 1], t[:, 0]]           # the horses' right: the outer side (left-handed)
        self.d1 = self.d0 + self.sp * (n - 1)

    def at(self, d, off=0.0):
        """the point 'off' metres beyond the outer rail at d metres to go, and the outward normal there"""
        f = (min(max(d, self.d0), self.d1) - self.d0) / self.sp; i = min(int(f), len(self.p) - 2); k = f - i
        p = self.p[i] * (1 - k) + self.p[i + 1] * k; nrm = self.n[i] * (1 - k) + self.n[i + 1] * k
        nrm /= np.hypot(*nrm)
        return p + nrm * (self.W + off), nrm

    def d_at_x(self, x, lo=None, hi=None):
        """metres to go where the inside rail is nearest world x (within lo..hi)"""
        ds = self.d0 + self.sp * np.arange(len(self.p))
        m = np.ones(len(ds), bool)
        if lo is not None: m &= ds >= lo
        if hi is not None: m &= ds <= hi
        i = np.argmin(np.where(m, np.abs(self.p[:, 0] - x), 1e9)); return float(ds[i])


def load_osm():
    D = json.loads((REPO / "reference/york/osm-surround.json").read_text())["items"]
    import sys
    sys.path.insert(0, str(REPO / "tools/course/york"))
    import layout as LY
    out = []
    for t, rings in D:
        rs = []
        for f in rings:
            x = y = 0; pts = []
            for i in range(0, len(f), 2):
                x += f[i]; y += f[i + 1]; pts.append(LY.world(np.array([x, y], float)))
            rs.append(pts)
        out.append((t, rs))
    return out


def perimeter(S, C, W, sp, rnd=None):
    """Adds the surroundings to the scene S (pieces, flats, people); returns (trees, boards, banks)."""
    rnd = rnd or random.Random(33)
    R = {k: Route(v, W) for k, v in C["routes"].items()}
    trees, boards, banks = [], [], []
    # the course and its rails, kept clear (with a margin); the stand side and the festival infield too
    strips = []
    for r in R.values():
        o = [tuple(r.at(r.d0 + r.sp * i)[0]) for i in range(len(r.p))]
        strips.append(Polygon([tuple(p) for p in r.p] + o[::-1]).buffer(0))
    turf = unary_union(strips)
    keep_out = unary_union([turf.buffer(22.0),     # (the tracking car's lane, 5-12 m out, kept clear of trees)
                             Polygon([(-140, -26), (330, -26), (330, -190), (-140, -190)]),
                            Polygon([(-20, 0), (300, 0), (300, 90), (-20, 90)])])
    taken = [keep_out]

    def free(x, z, pad=0.0):
        return not any(g.distance(Point(x, z)) <= pad if pad else g.contains(Point(x, z)) for g in taken)

    def tree(x, z, sc, belt=None, dy=0.0, kinds=KINDS):
        t = [r2(x), r2(z), rnd.choice(kinds), r2(sc), rnd.randrange(360)]
        if belt or dy: t.append(belt or 0)
        if dy: t.append(r2(dy))
        trees.append(t)

    # ------------------------------------------------------------------ green: Ascot's planting along the outer rail
    # (the tracking car runs 5 m beyond the outer rail on the straight and 12 m on the round course, looking in across
    # the track: so the boards stand 20 m out, behind its lane, and the trees and banks start further back still)
    BOARD_OFF = 20.0
    def belt(route, da, db, depth=(25.0, 48.0), boards_on=True, spacing=7.0, scale=(1.1, 1.6)):
        r = R[route]; lo, hi = sorted((da, db)); d = lo; k = rnd.randrange(4)
        while d <= hi:
            (bx, bz), nrm = r.at(d, BOARD_OFF)
            if boards_on:
                # facing the track: back along the normal; turn = atan2(fx, fz)
                boards.append([r2(bx), r2(bz), r2(math.degrees(math.atan2(-nrm[0], -nrm[1]))), DESIGNS[k % 4], 1.4]); k += 1
            d += 6.0
        d = lo
        while d <= hi:
            for _ in range(2):
                off = rnd.uniform(*depth)
                (x, z), _n = r.at(d + rnd.uniform(-3, 3), off)
                if free(x, z):
                    tree(x, z, rnd.uniform(*scale), belt=1)
            d += spacing
        taken.append(LineString([tuple(r.at(d_, BOARD_OFF)[0]) for d_ in np.arange(lo, hi, 5.0)]).buffer(4.0))

    rf = R["far"]
    d_x = lambda x, lo=None, hi=None: rf.d_at_x(x, lo, hi)
    # the back straight runs from the spur (x about -540, the far end) to the home bend (x about +1000)
    dB0, dB1 = d_x(1000.0, 1500, 2500), d_x(-540.0, 1500, 2900)
    belt("far", d_x(776, 1500, 2600), d_x(1000, 1500, 2600), depth=(25, 60))                  # G1: by Knavesmire Wood
    belt("far", d_x(-60, 1500, 2900), d_x(222, 1500, 2900), depth=(25, 44))                   # G2: between the banks
    rs = R["straight"]
    belt("straight", rs.d_at_x(1222), rs.d_at_x(898), depth=(25, 46))                         # G3: the straight course
    r7 = R["chute7f"]
    belt("chute7f", r7.d1 - 5, r7.d1 - 220, depth=(25, 40))                                  # G4: along the 7f chute

    # ------------------------------------------------------------------ light blue: shallow banks with pockets of trees
    def bank(route, da, db, a, b, h, pockets, step=5.0):
        r = R[route]; lo, hi = sorted((da, db)); L = hi - lo
        rows, n_across = [], 15
        ease = lambda u: (lambda s: s * s * (3 - 2 * s))(min(max(u, 0.0), 1.0))
        heights = {}
        for d in np.arange(lo, hi + 1e-6, step):
            end = ease((d - lo) / 45.0) * ease((hi - d) / 45.0)
            row = []
            for j in range(n_across):
                u = j / (n_across - 1); off = a + (b - a) * u
                hh = h * end * math.sin(math.pi * u) ** 0.8 * (1 + 0.12 * math.sin(d * 0.031 + j))
                (x, z), _ = r.at(d, off); row += [r2(x), r2(max(hh, 0.0) if 0 < j < n_across - 1 else -0.05), r2(z)]
            rows.append(row)
        banks.append({"rows": rows})
        bh = lambda d, off: h * ease((d - lo) / 45.0) * ease((hi - d) / 45.0) * math.sin(math.pi * min(max((off - a) / (b - a), 0), 1)) ** 0.8
        # the pockets of planting on the bank (orange on his mark-up): clumps of five to nine trees on its far half
        for f in pockets:
            dc = lo + L * f + rnd.uniform(-8, 8); oc = a + (b - a) * rnd.uniform(0.5, 0.72)
            for _ in range(rnd.randint(5, 9)):
                dd, oo = dc + rnd.uniform(-11, 11), oc + rnd.uniform(-6, 6)
                (x, z), _ = r.at(dd, oo)
                tree(x, z, rnd.uniform(1.0, 1.55), belt=1, dy=max(0.0, bh(dd, oo) - 0.3))
        poly = Polygon([tuple(r.at(d, a)[0]) for d in np.arange(lo, hi, 10)] + [tuple(r.at(d, b)[0]) for d in np.arange(hi, lo, -10)]).buffer(0)
        taken.append(poly)
        return poly

    bank("far", d_x(222, 1500, 2900), d_x(776, 1500, 2600), 18.0, 60.0, 3.2,
         [0.08, 0.2, 0.3, 0.42, 0.55, 0.67, 0.8, 0.92])                                       # LB1: the back straight
    bank("far", d_x(-60, 1500, 2900), rf.d1 - 2, 18.0, 64.0, 3.0,
         [0.1, 0.22, 0.34, 0.45, 0.56, 0.7, 0.82, 0.93])                                       # LB2: along the spur
    # past the spur's top the bank and its planting carry on a little, so the 1m6f's stalls camera looks into trees
    tx, tz = rf.t[-1]                                         # the running direction at the top (back past it: -t)
    for k in range(40):
        (x, z), _ = rf.at(rf.d1, rnd.uniform(18, 70)); back = rnd.uniform(-20, 60)
        tree(x - tx * back, z - tz * back, rnd.uniform(1.1, 1.6), belt=1)

    # ------------------------------------------------------------------ OSM: woods, fields, houses, roads, hedges
    osm = load_osm()
    box = Polygon([(-760, -520), (1500, -520), (1500, 1150), (-760, 1150)])
    def poly_of(rs):
        try:
            p = Polygon(rs[0]).buffer(0)
            return p.intersection(box) if p.is_valid else None
        except Exception:
            return None
    def fill(poly, spacing, sc, belt_=None, kinds=KINDS, cap=None):
        if poly is None or poly.is_empty: return
        x0, z0, x1, z1 = poly.bounds; n = 0
        for x in np.arange(x0, x1, spacing):
            for z in np.arange(z0, z1, spacing):
                px, pz = x + rnd.uniform(-0.4, 0.4) * spacing, z + rnd.uniform(-0.4, 0.4) * spacing
                if poly.contains(Point(px, pz)) and free(px, pz):
                    tree(px, pz, rnd.uniform(*sc), belt=belt_, kinds=kinds); n += 1
                    if cap and n >= cap: return
    fields = []
    for t, rs in osm:
        kind = t.get("n") or t.get("l") or t.get("a") or t.get("s")
        if t.get("h") or t.get("b") or t.get("r") or kind == "tree_row" or kind == "track": continue
        p = poly_of(rs)
        if p is None or p.is_empty: continue
        p = p.difference(keep_out)
        if p.is_empty: continue
        if kind in ("wood", "scrub"):
            near = p.distance(turf) < 400
            fill(p, (11.0 if near else 16.0) if kind == "wood" else 20.0, (1.0, 1.6) if kind == "wood" else (0.6, 1.0), belt_=1 if near else None)
            taken.append(p)
        elif kind in ("farmland", "meadow"):
            fields.append((kind, p))
        elif kind == "residential":
            x0_, z0_, x1_, z1_ = p.bounds                                          # leafy suburbs: clumps of garden trees
            for x in np.arange(x0_, x1_, 48.0):
                for z in np.arange(z0_, z1_, 48.0):
                    cx_, cz_ = x + rnd.uniform(-15, 15), z + rnd.uniform(-15, 15)
                    if not p.contains(Point(cx_, cz_)): continue
                    for _ in range(rnd.randint(3, 6)):
                        tx_, tz_ = cx_ + rnd.uniform(-8, 8), cz_ + rnd.uniform(-8, 8)
                        if free(tx_, tz_): tree(tx_, tz_, rnd.uniform(0.9, 1.4))
        elif kind == "allotments":
            for g in getattr(p, "geoms", [p]):
                if g.area > 300: S.flat("#bfc88c", list(g.exterior.coords)[:-1], 0.02)
            fill(p, 34.0, (0.5, 0.8))
    for kind, p in fields:                                                        # the fields and their hedges
        for g in getattr(p, "geoms", [p]):
            if g.area < 800: continue
            S.flat("#c6c78e" if kind == "farmland" else "#b4c98a", list(g.exterior.coords)[:-1], 0.02)
            ring = LineString(list(g.exterior.coords))
            for s in np.arange(0, ring.length, 5.0):
                q = ring.interpolate(s)
                if free(q.x, q.y) and rnd.random() < 0.8:
                    tree(q.x, q.y, rnd.uniform(0.45, 0.65), kinds=("oak_a", "oak_b", "wide_a", "wide_b"))
                if rnd.random() < 0.03:
                    tree(q.x + rnd.uniform(-2, 2), q.y + rnd.uniform(-2, 2), rnd.uniform(1.2, 1.6))
    for t, rs in osm:                                                             # roads and hedges
        if t.get("b") == "hedge" or t.get("n") == "tree_row":
            for r_ in rs:
                ln = LineString(r_)
                for s in np.arange(0, ln.length, 3.5 if t.get("b") else 9.0):
                    q = ln.interpolate(s)
                    if box.contains(q) and free(q.x, q.y):
                        tree(q.x, q.y, rnd.uniform(0.45, 0.65) if t.get("b") else rnd.uniform(1.1, 1.5))
        h = t.get("h")
        if h in ("trunk", "primary", "secondary", "tertiary", "unclassified"):
            w = {"trunk": 14.0, "primary": 9.0, "secondary": 8.0}.get(h, 6.5)
            for r_ in rs:
                ln = LineString(r_)
                if ln.length < 5: continue
                road = ln.buffer(w / 2, cap_style=2).difference(keep_out)
                for g in getattr(road, "geoms", [road]):
                    if g.area > 20 and box.intersects(g): S.flat("#b9b4a6", list(g.exterior.coords)[:-1], 0.025)
                if h in ("primary", "trunk", "unclassified"):
                    for s in np.arange(0, ln.length, 16.0):
                        q = ln.interpolate(s); q2 = ln.interpolate(min(s + 1, ln.length))
                        dx, dz = q2.x - q.x, q2.y - q.y; L_ = math.hypot(dx, dz) or 1
                        for side in (-1, 1):
                            x, z = q.x - dz / L_ * side * (w / 2 + 5), q.y + dx / L_ * side * (w / 2 + 5)
                            if box.contains(Point(x, z)) and free(x, z) and rnd.random() < 0.8:
                                tree(x, z, rnd.uniform(1.0, 1.5))

    # ------------------------------------------------------------------ light purple: the car parks, as a lighter festival
    CARS = ["#c9c9c4", "#ecebe5", "#5d6066", "#3f4d66", "#8c4a46", "#6d86a3", "#2f3134", "#cbbf9f", "#c9c9c4", "#ecebe5"]
    def park(poly, seed_pieces, balloons=0, face=(0.0, 1.0), strip=55.0):
        """a car park on race day: a festival strip along the side facing the course (marquees, a big top, kiosks,
        flags, a thinner crowd on trodden ground), and rows of parked cars on the grass behind it"""
        poly = poly.difference(turf.buffer(14.0))
        g = max(getattr(poly, "geoms", [poly]), key=lambda q: q.area)
        front = g.intersection(turf.buffer(14.0 + strip))
        front = max(getattr(front, "geoms", [front]), key=lambda q: q.area)
        S.flat("#d6cfa2", list(front.exterior.coords)[:-1], 0.03)                 # trodden ground
        x0, z0, x1, z1 = front.bounds
        placed = []
        def ok(x, z, r):
            return front.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 3 for a, b, rb in placed)
        fx, fz = face; turn = math.degrees(math.atan2(fx, fz)) % 360
        for piece, count, r in seed_pieces:
            for _ in range(count):
                for _try in range(80):
                    x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
                    if ok(x, z, r):
                        sp(piece, x, z, turn + rnd.choice([0, 0, 0, 90, 180]) if piece not in ("big_top", "balloon_pod") else rnd.uniform(0, 360), people=0.5)
                        placed.append((x, z, r)); break
        for _ in range(balloons):
            for _try in range(80):
                x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
                if ok(x, z, 4.0):
                    sp("balloon_pod", x, z, rnd.uniform(0, 360), people=0.3); placed.append((x, z, 4.0)); break
        for _ in range(int(front.area * 0.06)):                                    # a thinner crowd
            x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
            if front.contains(Point(x, z)) and not S.blocked(x, z):
                S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2))
        # the cars: rows across the face, in pairs nose to nose with an aisle between, a few spaces empty
        back = g.difference(turf.buffer(14.0 + strip + 6.0)).buffer(-3.0)
        ux, uz = -fz, fx                                                           # along a row
        yaw = math.atan2(-fz, fx)                                                  # a car's length along the face
        cx, cz = back.centroid.x, back.centroid.y
        R_ = math.hypot(back.bounds[2] - back.bounds[0], back.bounds[3] - back.bounds[1])
        n = 0
        for k in range(-int(R_ / 6), int(R_ / 6) + 1):
            off = k * 6.2 + (3.5 if k % 2 else 0.0)                                 # pairs of rows, 7 m aisles
            for j in np.arange(-R_, R_, 2.7):
                x, z = cx + fx * off + ux * j, cz + fz * off + uz * j
                if rnd.random() < 0.16 or not back.contains(Point(x, z)): continue
                c = rnd.choice(CARS)
                S.box(c, x, z, 4.3, 1.8, 0.25, 0.95, yaw)
                S.box("#4a5260", x - fx * 0.25, z - fz * 0.25, 2.3, 1.56, 0.95, 1.42, yaw)
                n += 1
        taken.append(g)
        return g, n
    kit = [("big_top", 1, 11.0), ("marquee_peaks", 3, 13.0), ("marquee_clearspan", 2, 11.0), ("kiosk_row_arched", 3, 6.0),
           ("pagoda_kiosk", 5, 3.0), ("kiosk_awning", 4, 3.5), ("viewing_tower", 1, 5.0), ("picnic_table", 10, 1.5),
           ("pergola_picnic", 2, 5.0), ("banner_flag", 8, 1.0)]
    lp1, n1 = park(Polygon([(428, -45), (893, -45), (893, -120), (760, -230), (428, -230)]), kit, face=(0.0, 1.0))
    lp2, n2 = park(Polygon([(-262, 0), (-262, 320), (-420, 300), (-560, -40), (-330, -70)]), kit, balloons=4, face=(1.0, 0.0))
    print("   car parks:", n1, "and", n2, "cars")
    # boards along the car parks' fronts, facing the course
    for g, (fx, fz) in ((lp1, (0.0, 1.0)), (lp2, (0.8, 0.6))):
        ring = LineString(list(g.exterior.coords)); k = 0
        for s in np.arange(0, ring.length, 7.0):
            q = ring.interpolate(s)
            if turf.distance(q) < 40 and rnd.random() < 0.9:
                boards.append([r2(q.x), r2(q.y), r2(math.degrees(math.atan2(fx, fz))), DESIGNS[k % 4], 1.4]); k += 1

    # ------------------------------------------------------------------ the far end of the straight course: closed off
    # (the head-on camera's long lens looks straight up the course to it): a long grassy mound across the end, boards on
    # its face and a belt of trees along its top and behind
    rows = []
    for zz in np.arange(-90, 110, 5.0):
        row = []
        for j in range(13):
            u = j / 12; x = 1250 + 40 * u
            hh = 4.0 * math.sin(math.pi * u) ** 0.8 * (1 + 0.1 * math.sin(zz * 0.05 + j))
            row += [r2(x), r2(hh if 0 < j < 12 else -0.05), r2(zz)]
        rows.append(row)
    banks.append({"rows": rows})
    for zz in np.arange(-80, 100, 6.0):
        boards.append([1246.0, r2(zz), -90.0, DESIGNS[int(zz) // 6 % 4], 1.4])
    for _ in range(70):
        zz = rnd.uniform(-90, 110); x = rnd.uniform(1262, 1320)
        if not turf.buffer(22).contains(Point(x, zz)): tree(x, zz, rnd.uniform(1.1, 1.6), belt=1, dy=max(0.0, 4.0 * math.sin(math.pi * min(max((x - 1250) / 40, 0), 1)) ** 0.8 - 0.3))
    return trees, boards, banks
