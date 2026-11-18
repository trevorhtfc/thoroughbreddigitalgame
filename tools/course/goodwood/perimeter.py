"""Goodwood, phase 3: the course's surroundings, out to the edge of the ground grid (the long views beyond it are
farland.py's).

Owner, 17 Nov 2026, on his mark-up of the aerial view (reference/goodwood/perimeter-markup.png, the zones traced in
reference/goodwood/perimeter-zones.json):

  "1 - heavy planting as typical. include advertising boards as typically layed out. 2 is planting that sits down a
  slope.. again with signinge. 3. open grasslands sloping 4. possile small festival area 5. granstands"

  planting  (1, orange) round the outside of the loop and the far end of the straight: the boards 20 m off the turf,
            a belt of trees from 25 to 55 m, and the wood's canopy behind
  slope     (2, blue) the wooded fall north of the straight: the boards 20 m off the turf, the belt and the canopy
            stepping down the hill on the real ground
  grass     (3, magenta) the island and the infield: open sloping grass (the ground's own grass), a few parkland trees
  festival  (4, lilac) in the valley below the straight: a small festival (marquees, a big top, kiosks, a light crowd on
            trodden ground) facing up the slope towards the straight and the stands, a loose line of trees behind it
  stands    (5, green) kept clear for phase 4
  the rest  OpenStreetMap (reference/goodwood/osm-surround.json; (c) OpenStreetMap contributors, ODbL): woods as belts
            and canopies, fields as flats with clipped hedges, roads

The rules (the brief): every camera's view ends on something; boards 20 m off the turf (so beyond any outer rail),
banks from 18 m, trees 22 m clear of the turf (here from 25 m); only what the cameras see: the trees stay in a belt by
the course and the woods beyond it are canopies (one light mesh each: a soft lumpy roof of leaves on the real ground,
from the belt back to the ground grid's edge), so the counts stay within Ascot's.
"""
import json, math, random, importlib.util
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, box
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep
from scipy.spatial import Delaunay

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("goodwood_layout", HERE / "layout.py")
LY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LY)

DESIGNS = ["green", "cream", "navy", "white"]
KINDS = ("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")
BOARD_OFF = 20.0              # the boards' line off the turf (beyond every outer rail: the tracking car's lane is inside it)
BELT = (25.0, 55.0)           # the belt of real trees, metres off the turf
CANOPY_FROM = 46.0            # the canopies start here (under the belt's back half, so the trees hide their front edge)
SLOPE_DEEP = 105.0            # on the slope (zone 2) real trees go this far down, the canopy beyond
CANOPY_H = (13.0, 17.0)       # the canopy's height over the ground, metres (the tree kit's belt trees are about 12-18 m)
HEDGE = "#5b7a43"             # clipped hedges (a green box: the soft look dresses it with leaf tufts)


def r2(v): return round(float(v), 2)


def zones():
    """the owner's zones in world axes (x along the straight, the post at 0; z + towards the stands)"""
    Z = json.loads((REPO / "reference/goodwood/perimeter-zones.json").read_text())["px"]
    M = np.array(json.loads((REPO / "reference/goodwood/markup-fit.json").read_text())["M"])
    out = {}
    for k, pts in Z.items():
        en = np.c_[np.array(pts, float), np.ones(len(pts))] @ M
        out[k] = Polygon([LY.world(e) for e in en]).buffer(0)
    return out


def osm():
    """OpenStreetMap's woods, fields, grass, scrub, roads, built-up land, tracks, buildings and hedges, in world axes"""
    D = json.loads((REPO / "reference/goodwood/osm-surround.json").read_text())
    out = {}
    for k in ("wood", "farm", "grass", "scrub", "road", "built", "track", "building", "hedge"):
        L = []
        for f in D[k]:
            x = y = 0; pts = []
            for i in range(0, len(f), 2):
                x += f[i]; y += f[i + 1]; pts.append(LY.world(np.array([x, y], float)))
            L.append(pts)
        out[k] = L
    return out


def polys(g):
    return [] if g is None or g.is_empty else [q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon"]


def canopy_mesh(poly, rnd, spacing, h_rng):
    """a wood's canopy: points over the polygon (its edge every few metres, the inside on a jittered grid),
    triangulated; the edge at the ground, rising steeply to the canopy's height, lumpy on top. Returns flat lists
    (x, y above the ground, z) and the triangles."""
    poly = poly.simplify(2.0)
    if poly.is_empty or poly.area < 600: return None
    pts, edge = [], []
    for ring in [poly.exterior] + list(poly.interiors):
        L = ring.length
        for s in np.arange(0, L, min(6.0, spacing * 0.7)):
            q = ring.interpolate(s); pts.append((q.x, q.y)); edge.append(True)
    inner = poly.buffer(-1.5)
    pin = prep(inner) if not inner.is_empty else None
    x0, z0, x1, z1 = poly.bounds
    for x in np.arange(x0, x1, spacing):
        for z in np.arange(z0, z1, spacing):
            px, pz = x + rnd.uniform(-0.3, 0.3) * spacing, z + rnd.uniform(-0.3, 0.3) * spacing
            if pin and pin.contains(Point(px, pz)): pts.append((px, pz)); edge.append(False)
    if len(pts) < 8: return None
    P = np.array(pts)
    tri = Delaunay(P).simplices
    pp = prep(poly.buffer(0.5))
    def short(t):
        a, b, c = P[t]; return max(np.hypot(*(a - b)), np.hypot(*(b - c)), np.hypot(*(c - a))) < spacing * 2.6
    keep = [t for t in tri if short(t) and pp.contains(Point(P[t].mean(axis=0)))]
    if not keep: return None
    H = rnd.uniform(*h_rng)
    bd = poly.boundary
    ys = []
    for (x, z), e in zip(pts, edge):
        if e: ys.append(H * rnd.uniform(0.28, 0.36)); continue                  # the edge: the leaves hang low
        d = bd.distance(Point(x, z))
        rise = 0.72 + 0.28 * min(1.0, d / 14.0)
        lump = 1.0 + 0.1 * math.sin(x * 0.23 + z * 0.07) * math.sin(z * 0.19 - x * 0.05) + rnd.uniform(-0.16, 0.16)   # the crowns
        ys.append(H * rise * lump)
    v = []
    for (x, z), y in zip(pts, ys): v += [round(x, 1), round(y, 1), round(z, 1)]
    return {"v": v, "i": [int(a) for t in keep for a in t]}


def perimeter(S, turf, grid_box, sp, rnd=None):
    """Adds the surroundings to the scene S (flats, hedges, the festival's pieces and people); returns trees, boards,
    canopies and a short count of what went where. turf: the course's turf (shapely); grid_box: the ground grid's
    rectangle (x0, z0, x1, z1); sp(piece, x, z, turn, people): puts a site prop (with its people)."""
    rnd = rnd or random.Random(17)
    Z, O = zones(), osm()
    trees, boards, canopies, note = [], [], [], {}
    gx0, gz0, gx1, gz1 = grid_box
    inside_grid = box(gx0 + 25, gz0 + 25, gx1 - 25, gz1 - 25)
    stands = Z["stands"].difference(turf.buffer(BOARD_OFF - 2))
    keep_out = unary_union([turf.buffer(22.0), stands])
    pk = prep(keep_out)
    zone_woods = unary_union([Z["planting"], Z["slope"]])

    def tree(x, z, sc, belt=None, kinds=KINDS):
        t = [r2(x), r2(z), rnd.choice(kinds), r2(sc), rnd.randrange(360)]
        if belt: t.append(belt)
        trees.append(t)

    def fill(poly, spacing, sc, belt=None, kinds=KINDS, p=1.0):
        n = 0
        for g in polys(poly):
            pg = prep(g); x0, z0, x1, z1 = g.bounds
            for x in np.arange(x0, x1, spacing):
                for z in np.arange(z0, z1, spacing):
                    px, pz = x + rnd.uniform(-0.45, 0.45) * spacing, z + rnd.uniform(-0.45, 0.45) * spacing
                    if pg.contains(Point(px, pz)) and not pk.contains(Point(px, pz)) and rnd.random() < p:
                        tree(px, pz, rnd.uniform(*sc), belt=belt, kinds=kinds); n += 1
        return n

    # ------------------------------------------------------------------ 1 and 2: the boards, the belts, the canopies
    ring = turf.buffer(BOARD_OFF, join_style=1).boundary
    n_boards = {}
    for zname in ("planting", "slope"):
        line = ring.intersection(Z[zname].buffer(12.0)).difference(stands.buffer(6.0))
        k = 0; n = 0
        for seg in getattr(line, "geoms", [line]):
            if seg.geom_type != "LineString" or seg.length < 12: continue
            for s in np.arange(3.0, seg.length - 2.0, 6.0):
                q = seg.interpolate(s)
                a, _ = nearest_points(turf, q)
                fx, fz = a.x - q.x, a.y - q.y; L = math.hypot(fx, fz) or 1
                boards.append([r2(q.x), r2(q.y), r2(math.degrees(math.atan2(fx / L, fz / L))), DESIGNS[k % 4], 1.4]); k += 1; n += 1
        n_boards[zname] = n
    note["boards"] = n_boards
    band = turf.buffer(BELT[1]).difference(turf.buffer(BELT[0]))
    note["belt trees"] = {
        "planting": fill(Z["planting"].intersection(band), 8.8, (1.15, 1.65), belt=1),
        "slope": fill(Z["slope"].intersection(band), 7.5, (1.0, 1.5), belt=1)
                 # (the slope is in full view from the stands, looked down on: real trees further down it, sparser)
                 + fill(Z["slope"].intersection(turf.buffer(SLOPE_DEEP).difference(turf.buffer(BELT[1]))), 11.5, (1.1, 1.6), belt=1),
    }
    woods = unary_union([Polygon(p).buffer(0) for p in O["wood"] + O["scrub"] if len(p) >= 4])
    other_woods = woods.difference(zone_woods)
    note["belt trees"]["OSM woods"] = fill(other_woods.intersection(band), 8.0, (1.0, 1.5), belt=1)
    # (where the planting zone meets the stands' zone at the straight's east end, and the far end of the straight
    # course: the boards' ring wraps round the end of the turf, and the belt behind it closes the head-on camera's view)
    # the canopies: every wood from the belt back to the ground grid's edge
    festival = Z["festival"]
    canopy_area = unary_union([zone_woods, woods]).intersection(inside_grid) \
        .difference(turf.buffer(CANOPY_FROM)).difference(Z["slope"].intersection(turf.buffer(SLOPE_DEEP - 8))).difference(stands.buffer(10)).difference(festival.buffer(10)).difference(Z["grass"])
    cv = ct = 0
    for g in polys(canopy_area.buffer(4).buffer(-4)):
        near = g.distance(turf) < 160
        m = canopy_mesh(g, rnd, 9.0 if near else 15.0, CANOPY_H)
        if m: canopies.append(m); cv += len(m["v"]) // 3; ct += len(m["i"]) // 3
    note["canopies"] = {"pieces": len(canopies), "points": cv, "triangles": ct}
    # a wood's edge where no belt stands in front of it (within 320 m of the course): a row of real trees just inside
    # it, a little taller than the canopy, so the cameras see trees, not the canopy's side
    ne = 0
    for g in polys(canopy_area.buffer(4).buffer(-4)):
        if g.distance(turf) > 320 or g.area < 600: continue
        for ring_ in [g.buffer(-3.0)]:
            for gg in polys(ring_):
                for ln in [gg.exterior] + list(gg.interiors):
                    for s in np.arange(0, ln.length, 11.5):
                        q = ln.interpolate(s + rnd.uniform(-2, 2))
                        dq = turf.distance(q)
                        if dq < 58 or dq > 330 or pk.contains(q): continue
                        a, _ = nearest_points(turf, q); ux, uz = (a.x - q.x) / dq, (a.y - q.y) / dq
                        if g.contains(Point(q.x + ux * 9, q.y + uz * 9)): continue      # (only the edges that face the course)
                        tree(q.x, q.y, rnd.uniform(1.3, 1.8), belt=1); ne += 1
    note["edge trees"] = ne

    # ------------------------------------------------------------------ 3: open sloping grass, a few parkland trees
    n = 0
    for g in polys(Z["grass"].difference(turf.buffer(30.0))):
        x0, z0, x1, z1 = g.bounds
        for _ in range(int(g.area / 9000)):
            for _try in range(30):
                x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
                if g.contains(Point(x, z)) and not pk.contains(Point(x, z)):
                    for k in range(rnd.choice([1, 1, 2, 3])):
                        tree(x + rnd.uniform(-6, 6) * k, z + rnd.uniform(-6, 6) * k, rnd.uniform(1.2, 1.7), kinds=("oak_a", "oak_b", "wide_a", "wide_b")); n += 1
                    break
    note["parkland trees"] = n

    # ------------------------------------------------------------------ 4: a small festival in the valley
    note["festival"] = festival_area(S, festival.difference(keep_out), sp, rnd, tree)

    # ------------------------------------------------------------------ OSM: fields and hedges, roads (within the grid)
    near_flats = prep(turf.buffer(420.0))
    fields = unary_union([Polygon(p).buffer(0) for p in O["farm"] if len(p) >= 4]).intersection(inside_grid) \
        .difference(keep_out).difference(canopy_area).difference(festival).difference(Z["grass"])
    nh = 0
    for g in polys(fields):
        if g.area < 1500: continue
        S.flat("#ccc993", list(g.simplify(2.0).exterior.coords)[:-1], 0.02)
        # clipped hedges round the fields, in 6 m lengths (each stands level on the ground under its middle)
        if g.distance(turf) > 260: continue
        rr = LineString(list(g.exterior.coords))
        for s in np.arange(0, rr.length - 6, 6.0):
            a, b = rr.interpolate(s), rr.interpolate(s + 6.0)
            mx, mz = (a.x + b.x) / 2, (a.y + b.y) / 2
            if pk.contains(Point(mx, mz)): continue
            S.box(HEDGE, mx, mz, 6.3, 1.5, 0.0, rnd.uniform(1.5, 2.1), math.atan2(-(b.y - a.y), b.x - a.x)); nh += 1
    for p in O["hedge"]:
        ln = LineString(p)
        for s in np.arange(0, ln.length - 6, 6.0):
            a, b = ln.interpolate(s), ln.interpolate(s + 6.0)
            mx, mz = (a.x + b.x) / 2, (a.y + b.y) / 2
            if not inside_grid.contains(Point(mx, mz)) or pk.contains(Point(mx, mz)) or not near_flats.contains(Point(mx, mz)): continue
            S.box(HEDGE, mx, mz, 6.3, 1.5, 0.0, rnd.uniform(1.6, 2.2), math.atan2(-(b.y - a.y), b.x - a.x)); nh += 1
    note["hedge lengths"] = nh
    nr = 0
    for p in O["road"]:
        ln = LineString(p)
        if ln.length < 5: continue
        road = ln.buffer(3.2, cap_style=2).intersection(inside_grid).difference(turf.buffer(3.0)).difference(canopy_area).difference(zone_woods)
        for g in polys(road):
            if g.area > 30: S.flat("#c4bfb0", list(g.exterior.coords)[:-1], 0.025); nr += 1
    note["road pieces"] = nr
    return trees, boards, canopies, note


def festival_area(S, poly, sp, rnd, tree):
    """a small festival on the lilac zone's upper slope: a strip about 130 m deep along its side nearest the straight,
    facing up the slope towards it (+z); trodden ground, marquees, a big top, kiosks, picnic tables, flags and a light
    crowd; a loose line of trees behind it closes the view from the stands"""
    g = max(polys(poly), key=lambda q: q.area)
    x0, z0, x1, z1 = g.bounds
    front = g.intersection(box(x0, z1 - 140.0, x1, z1)).buffer(-6.0)
    front = max(polys(front), key=lambda q: q.area)
    S.flat("#d8d0a2", list(front.simplify(1.0).exterior.coords)[:-1], 0.03)
    fx0, fz0, fx1, fz1 = front.bounds
    placed = []
    def ok(x, z, r):
        return front.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 3 for a, b, rb in placed)
    kit = [("big_top", 1, 11.0), ("marquee_peaks", 3, 13.0), ("marquee_clearspan", 2, 11.0), ("kiosk_row_arched", 3, 6.0),
           ("pagoda_kiosk", 5, 3.0), ("kiosk_awning", 4, 3.5), ("viewing_tower", 1, 5.0), ("pergola_picnic", 2, 5.0),
           ("picnic_table", 12, 1.5), ("banner_flag", 10, 1.0), ("balloon_pod", 3, 4.0)]
    n = 0
    for piece, count, r in kit:
        for _ in range(count):
            for _try in range(120):
                x, z = rnd.uniform(fx0, fx1), rnd.uniform(fz0, fz1)
                if ok(x, z, r):
                    turn = rnd.uniform(0, 360) if piece in ("big_top", "balloon_pod") else 180.0 + rnd.choice([0, 0, 0, 90, -90])
                    sp(piece, x, z, turn, 0.5); placed.append((x, z, r)); n += 1; break
    people = 0
    for _ in range(int(front.area * 0.03)):
        x, z = rnd.uniform(fx0, fx1), rnd.uniform(fz0, fz1)
        if front.contains(Point(x, z)) and not S.blocked(x, z):
            S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); people += 1
    # the trees behind: along the strip's back (north) edge and down its sides
    back = g.intersection(box(x0, z1 - 175.0, x1, z1 - 140.0))
    nt = 0
    for q in polys(back):
        qx0, qz0, qx1, qz1 = q.bounds
        for x in np.arange(qx0, qx1, 8.0):
            for _ in range(2):
                tx, tz = x + rnd.uniform(-3, 3), rnd.uniform(qz0, qz1)
                if q.contains(Point(tx, tz)) and rnd.random() < 0.75:
                    tree(tx, tz, rnd.uniform(1.1, 1.6), belt=1); nt += 1
    return {"pieces": n, "people": people, "trees behind": nt, "area m2": round(front.area)}
