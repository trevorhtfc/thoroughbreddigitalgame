"""Goodwood: the ground past the winning post, up to the Trundle (owner, 18 Nov 2026, circling the bare slope beyond
the run-out: "what goes on in this area?"; he agreed all of: a soft patchwork on the slope with no dark hedge blocks,
a few lone trees and a low belt of trees along the road at its foot so the run-out ends on something, and the
Trundle's masts with a thin line of picnickers along its top. No cars, by the course's rule).

  patchwork   the open grass west and north of the run-out, within the ground grid, cut into soft irregular parcels
              (a jittered Voronoi, 130-200 m across), each a flat in one of four pale downland tones; the fields
              perimeter.py paints (OpenStreetMap's farmland) sit on top of them
  lone trees  a few dozen oaks and wide crowns along the parcels' edges, and a few clumps of scrub on the slope
  road belt   two loose rows of trees along the roads at the slope's foot (OpenStreetMap), 8-16 m off the road
  picnickers  small groups along the east side of the Trundle's hill fort (round the masts' summit, beyond the ground
              grid, on the far land's own heights), facing the course
The masts themselves are farland.py's landmarks.
"""
import math, importlib.util
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPoint, box
from shapely.ops import unary_union, voronoi_diagram
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
TONES = ("#b4cf8e", "#cfe0a6", "#dcd99a", "#a8c683")      # downland greens round the ground's own (#cce0ab) and a hay tint
REGION = (-675.0, -700.0, -140.0, 70.0)                     # x0, z0, x1, z1: past the post, west and north of the run-out


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, HERE / file); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def r2(v): return round(float(v), 2)


_FH = {}


def far_height(x, z):
    """the far land's own height at (x, z) (as farland.py: the real ground against the post, the earth's curve off)"""
    import json
    if not _FH:
        FL = _load("goodwood_farland_h", "farland.py")
        G = json.loads((FL.OUT / "goodwood.json").read_text())["ground"]
        _FH.update(FL=FL, post=json.loads((FL.REPO / "courses/goodwood-draft.json").read_text())["postGroundM"],
                   cx=G["x0"] + G["cell"] * (G["nx"] - 1) / 2, cz=G["z0"] + G["cell"] * (G["nz"] - 1) / 2)
    FL = _FH["FL"]
    x, z = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(z, float))
    E, N = FL.en_of_world(x, z)
    return FL.HZ.height(E, N) - _FH["post"] - ((x - _FH["cx"]) ** 2 + (z - _FH["cz"]) ** 2) / (2 * FL.R_EFF)


def trundle(S, turf, keep_out, avoid, O, rnd, NM, masts):
    """S: the scene; keep_out: nothing goes here (the turf and its margin, the loop car's lane); avoid: woods and the
    owner's zones (already planted); O: OpenStreetMap in world axes (perimeter.osm()); masts: farland's [[x, z, y, h]].
    Returns the trees added and a short note."""
    trees, note = [], {}
    x0, z0, x1, z1 = REGION
    area = box(*REGION).difference(keep_out).difference(avoid)
    woods = unary_union([Polygon(p).buffer(0) for p in O["wood"] + O["scrub"] if len(p) >= 4])
    area = area.difference(woods.buffer(6.0))
    pa = prep(area)

    # ---- the patchwork: jittered Voronoi parcels over the region
    seeds = []
    for x in np.arange(x0 - 160, x1 + 160, 165.0):
        for z in np.arange(z0 - 160, z1 + 160, 150.0):
            seeds.append((x + rnd.uniform(-55, 55), z + rnd.uniform(-50, 50)))
    cells = voronoi_diagram(MultiPoint(seeds), envelope=box(x0 - 400, z0 - 400, x1 + 400, z1 + 400))
    edges, nflat = [], 0
    for i, c in enumerate(getattr(cells, "geoms", [cells])):
        g = c.intersection(area)
        for q in [g] if g.geom_type == "Polygon" else [p for p in getattr(g, "geoms", []) if p.geom_type == "Polygon"]:
            if q.area < 900: continue
            S.flat(TONES[(i * 7 + int(rnd.random() * 2)) % len(TONES)], list(q.simplify(3.0).exterior.coords)[:-1], 0.018)
            nflat += 1
        edges.append(c.boundary.intersection(area.buffer(-8.0)))
    note["parcels"] = nflat

    def tree(x, z, sc, kind=None, belt=None):
        t = [r2(x), r2(z), kind or rnd.choice(("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")), r2(sc), rnd.randrange(360)]
        if belt: t.append(belt)
        trees.append(t)

    # ---- lone trees along the parcels' edges, a few clumps of scrub
    lines = [l for e in edges if not e.is_empty for l in (getattr(e, "geoms", [e])) if l.geom_type == "LineString" and l.length > 30]
    nl = 0
    for l in lines:
        for s in np.arange(rnd.uniform(10, 60), l.length, rnd.uniform(70, 120)):
            if rnd.random() < 0.45:
                q = l.interpolate(s)
                if pa.contains(q): tree(q.x + rnd.uniform(-3, 3), q.y + rnd.uniform(-3, 3), rnd.uniform(1.3, 1.9), rnd.choice(("oak_a", "oak_b", "wide_a", "wide_b"))); nl += 1
    note["lone trees"] = nl
    ns = 0
    for _ in range(9):
        cx, cz = rnd.uniform(x0, -380), rnd.uniform(-420, -60)
        for _ in range(rnd.randint(3, 6)):
            px, pz = cx + rnd.uniform(-9, 9), cz + rnd.uniform(-7, 7)
            if pa.contains(Point(px, pz)): tree(px, pz, rnd.uniform(0.7, 1.1), belt=2); ns += 1
    note["scrub"] = ns

    # ---- the road belt at the slope's foot: two loose rows either side, 8-16 m off
    nb = 0
    foot = box(x0, -420.0, x1, z1)                               # the roads round the run-out's end and along its west
    for p in O["road"]:
        ln = LineString(p).intersection(foot)
        for l in [ln] if ln.geom_type == "LineString" else [g for g in getattr(ln, "geoms", []) if g.geom_type == "LineString"]:
            if l.length < 20: continue
            for s in np.arange(0, l.length, 9.0):
                a, b = l.interpolate(max(0, s - 1)), l.interpolate(min(l.length, s + 1))
                tx, tz = b.x - a.x, b.y - a.y; n = math.hypot(tx, tz) or 1; nx_, nz_ = -tz / n, tx / n
                for side in (-1, 1):
                    if rnd.random() > 0.72: continue
                    off = rnd.uniform(8.0, 16.0) * side
                    q = l.interpolate(s); px, pz = q.x + nx_ * off + rnd.uniform(-3, 3), q.y + nz_ * off + rnd.uniform(-3, 3)
                    if pa.contains(Point(px, pz)): tree(px, pz, rnd.uniform(1.2, 1.7), belt=1); nb += 1
    note["road belt"] = nb

    # ---- the hill fort's rampart: a slightly deeper green ring round the summit (about 110 m out)
    sx, sz = np.mean([m[0] for m in masts]), np.mean([m[1] for m in masts])
    for k in range(40):
        a0, a1 = 2 * math.pi * k / 40, 2 * math.pi * (k + 1) / 40
        quad = [(sx + r * math.cos(a), sz + r * math.sin(a)) for r, a in ((100, a0), (100, a1), (113, a1), (113, a0))]
        if all(x0 < qx < x1 and z0 < qz < z1 for qx, qz in quad): S.flat("#9fbd7c", quad, 0.022)
    # ---- picnickers along the east side of the hill fort, facing the course
    sx, sz = np.mean([m[0] for m in masts]), np.mean([m[1] for m in masts])
    toward = math.atan2(0.0 - sz, 0.0 - sx)                     # from the summit towards the post
    groups, people = 0, 0
    for k in range(170):
        a = toward + rnd.uniform(-1.05, 1.05)
        r = rnd.uniform(105, 135)
        gx, gz = sx + r * math.cos(a), sz + r * math.sin(a)
        for _ in range(rnd.randint(2, 5)):
            px, pz = gx + rnd.uniform(-2.5, 2.5), gz + rnd.uniform(-2.5, 2.5)
            y = None if px > x0 else float(far_height(px, pz)[0])      # (the ground grid's own heights where it reaches)
            S.person(px, 0.0, pz, NM.face(-px, -pz), g=y); people += 1
        groups += 1
    note["picnickers"] = people
    return trees, note
