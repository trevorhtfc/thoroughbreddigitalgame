"""Epsom, phase 3: the course's surroundings, out to the edge of the ground grid.

Owner, 18 Nov 2026 (09:37): "Yep scenery next", after his 1m4f race video (the views listed in
claude/epsom-course-handover.md) and his Google Maps view. No mark-up yet, so the zones are drawn from the video and
OpenStreetMap (reference/epsom/osm-surround.json; (c) OpenStreetMap contributors, ODbL), for him to mark up:

  the Hill      the infield along the straight: a packed crowd behind the inside rail, a run of boards on the rail in
                front of it (the video's 117-150 s), and opposite the post a hospitality frontage (a long blue-and-white
                deck with white tented roofs behind, 153-160 s); a festival on the Hill behind (marquees, big tops,
                kiosks, flags, balloons, a light crowd)
  Tattenham     inside the loop: a crowd along the inside rail, the tarmac road behind it, portaloo rows, a small marquee
                (57-114 s)
  the climb     the south arm's inside: small groups of people along the rail on the open Downs (9-54 s)
  the far side  outside the whole round course (where the tracking car runs, 12 m out): boards 20 m off the turf (the
                video's run of boards on the far rail), a belt of trees from 25 m (deep woodland behind the Derby start,
                0-6 s; the real woods from OSM as belts and canopies), and beyond the loop the Tattenham Corner houses as
                garden trees
  stand side    east of the stands' plot: boards 20 m off the turf, a thin crowd behind them, a belt of trees, the golf
                course beyond
  the stands    phase 4 (owner, 18 Nov 10:42, his clay model): the grandstand (tools/blender/build_epsom_stands.py) on
                the stand side by the post, its terrace and galleries full, a paved walk and the rail lawn's crowd in
                front, hospitality marquees up the course beside it
  the infield   the open Downs: its paths as worn strips (the muddy crossing path, 33-54 s), nothing tall

The rules (York's and Goodwood's): every camera's view ends on something; boards 20 m off the turf on the tracking
car's side, trees 22 m clear of the turf; only what the cameras see (the woods beyond the belts are canopies, the map's
trees thinned beyond 110 m and gone beyond 300 m), within Ascot's counts (about 2,000 trees and 23,000 people).
"""
import json, math, random, importlib.util
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("epsom_layout", HERE / "layout.py")
LY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LY)
_gs = importlib.util.spec_from_file_location("goodwood_perimeter", REPO / "tools/course/goodwood/perimeter.py")
GW = importlib.util.module_from_spec(_gs); _gs.loader.exec_module(GW)       # its canopy mesh and polygon helpers

DESIGNS = ["green", "cream", "navy", "white"]
KINDS = ("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")
GARDEN = ("oak_b", "wide_a", "wide_b")
BOARD_OFF = 20.0              # the far side's boards, metres off the turf (beyond the tracking car's lane)
BELT = (25.0, 58.0)           # the belt of real trees off the turf
CANOPY_FROM = 50.0
CANOPY_H = (12.0, 16.0)
STANDS_PLOT = Polygon([(-130, -28), (270, -28), (270, -270), (-130, -270)])   # kept clear for phase 4
HILL_D = (-60.0, 690.0)       # the Hill's crowd along the straight's inside rail, metres to go on the round route
TATT_D = (690.0, 1180.0)      # Tattenham Corner's inside crowd
CLIMB_D = (1180.0, 2470.0)    # the climb's inside, small groups along the rail
FRONTAGE_X = (-45.0, 175.0)   # the hospitality frontage opposite the post
HEDGE = "#5b7a43"
PATH = "#cfc7a6"              # worn paths across the Downs
ROAD = "#c4bfb0"
RAIL_BALLAST = "#b8ab95"


def r2(v): return round(float(v), 2)


def osm():
    D = json.loads((REPO / "reference/epsom/osm-surround.json").read_text())
    out = {}
    for k, v in D.items():
        if not isinstance(v, list): continue
        if k == "building":
            out[k] = [(LY.world(np.array([v[i], v[i + 1]], float)), v[i + 2]) for i in range(0, len(v), 3)]
            continue
        L = []
        for f in v:
            x = y = 0; pts = []
            for i in range(0, len(f), 2):
                x += f[i]; y += f[i + 1]; pts.append(LY.world(np.array([x, y], float)))
            L.append(pts)
        out[k] = L
    return out


def polygons(feats):
    return unary_union([Polygon(p).buffer(0) for p in feats if len(p) >= 4])


def rail_frame(route):
    """a route's inside rail: points every 5 m (index order: from the run-out's end, d0 metres to go, outwards), the
    running direction and the horses' left (the infield on a left-handed course)"""
    P = np.array(route["pathRail"]["points"], float); n = len(P)
    T = np.array([P[max(0, i - 1)] - P[min(n - 1, i + 1)] for i in range(n)]); T /= np.linalg.norm(T, axis=1)[:, None]
    left = np.stack([T[:, 1], -T[:, 0]], 1)
    d = route["pathRail"]["d0"] + route["pathRail"]["spacing"] * np.arange(n)
    return P, T, left, d


def band(route, d0, d1, a, b, W, inside=True):
    """the strip from a to b metres off the rail (inside: into the infield; outside: beyond the outer rail), between d0
    and d1 metres to go"""
    P, T, L, d = rail_frame(route)
    m = (d >= d0) & (d <= d1)
    if m.sum() < 2: return Polygon()
    P, L = P[m], L[m]
    if inside: A, B = P + L * a, P + L * b
    else: A, B = P - L * (W + a), P - L * (W + b)
    return Polygon(list(map(tuple, A)) + list(map(tuple, B[::-1]))).buffer(0)


GRANDSTAND = {"piece": "epsom_grandstand", "x": 39.0, "lawn": 8.0,
              "note": "the stand's middle 39 m up the course from the post, so its west section (the Queen's Stand's place) "
                      "is by the post and its main block (the Duchess's) up the course; the terrace's front walk 8 m behind "
                      "the outer rail"}
RIDES = [("epsom_ferris_wheel", 330.0, 62.0), ("epsom_helter_skelter", 395.0, 50.0)]   # metres to go, metres in from the rail


def outer_rail_z(turf, x):
    """the stand-side (outer) edge of the turf at x: the lowest z of the turf there"""
    g = turf.intersection(LineString([(x, -400.0), (x, 400.0)]))
    return min(c[1] for q in getattr(g, "geoms", [g]) for c in q.coords) if not g.is_empty else -26.0


def perimeter(S, C, turf, grid_box, sp, rnd=None, put=None):
    """Adds the surroundings to the scene S; returns trees, boards, canopies and a note of what went where. C: the race
    view's course (epsom.json); turf: its turf (shapely); grid_box: the ground grid (x0, z0, x1, z1); sp(piece, x, z, turn,
    people): a site prop with its people."""
    rnd = rnd or random.Random(23)
    W = C["trackWidth"]; R = C["routes"]["round"]
    O = osm()
    trees, boards, canopies, note = [], [], [], {}
    gx0, gz0, gx1, gz1 = grid_box
    inside_grid = box(gx0 + 25, gz0 + 25, gx1 - 25, gz1 - 25)
    # the infield: inside the round course's rail from the Derby start to the post, closed by a line back to the start
    P, T, L, d = rail_frame(R)
    k0, k1 = np.searchsorted(d, 0.0), np.searchsorted(d, 2440.0)
    infield = Polygon(list(map(tuple, P[k0:k1]))).buffer(0).difference(turf.buffer(0.5))
    infield = max(GW.polys(infield), key=lambda g: g.area)
    keep_out = unary_union([turf.buffer(22.0), STANDS_PLOT])
    pk = prep(keep_out)
    taken = []                                                   # what's already been used (crowds, festival), no trees there
    INFO = json.loads((REPO / "assets/models/architecture/epsom_stands.json").read_text())["pieces"]

    def tree(x, z, sc, belt=None, kinds=KINDS):
        t = [r2(x), r2(z), rnd.choice(kinds), r2(sc), rnd.randrange(360)]
        if belt: t.append(belt)
        trees.append(t)

    def free(x, z):
        q = Point(x, z)
        return not pk.contains(q) and not any(g.contains(q) for g in taken)

    def fill(poly, spacing, sc, belt=None, kinds=KINDS, p=1.0):
        n = 0
        for g in GW.polys(poly):
            pg = prep(g); x0, z0, x1, z1 = g.bounds
            for x in np.arange(x0, x1, spacing):
                for z in np.arange(z0, z1, spacing):
                    px, pz = x + rnd.uniform(-0.45, 0.45) * spacing, z + rnd.uniform(-0.45, 0.45) * spacing
                    if pg.contains(Point(px, pz)) and free(px, pz) and rnd.random() < p:
                        tree(px, pz, rnd.uniform(*sc), belt=belt, kinds=kinds); n += 1
        return n

    def face_turf(x, z):
        a, _ = nearest_points(turf, Point(x, z)); fx, fz = a.x - x, a.y - z; l = math.hypot(fx, fz) or 1
        return math.degrees(math.atan2(fx / l, fz / l))

    # ------------------------------------------------------------------ the grandstand, its walk, the rail lawn
    if put:
        gi = INFO[GRANDSTAND["piece"]]
        gx = GRANDSTAND["x"]
        zr = outer_rail_z(turf, gx) - 0.4
        gz = zr - GRANDSTAND["lawn"] + gi["front"]               # the terrace's foot (the walk runs 3 m before it)
        put("epsom_stands", GRANDSTAND["piece"], gx, gz, 0.0)
        S.stand_people(gi, gx, gz, 0.0, 1.0, 1.0, 1.0)
        hw = gi["width"] / 2
        S.nogo.append([(gx - hw, gz - gi["front"] + 0.5), (gx + hw, gz - gi["front"] + 0.5), (gx + hw, gz - gi["depth"]), (gx - hw, gz - gi["depth"])])
        S.flat("#e4d8c2", [(-70, zr - 0.6), (275, zr - 0.6), (275, gz - gi["front"]), (-70, gz - gi["front"])], 0.03)
        p0 = len(S.people)
        for x, z in S.spots(-68, 272, gz - gi["front"] + 0.6, zr - 1.0, 0.75):     # the rail lawn, facing the track
            if not S.blocked(x, z):
                S.person(x, 0.0, z, round(math.pi + rnd.uniform(-0.5, 0.5), 2))
        note["rail lawn crowd"] = (len(S.people) - p0) // 4
        # up the course beside the stand: hospitality marquees facing the track, a lawn with people between them
        xm0 = gx + hw + 12.0
        nm = 0
        for x in np.arange(xm0, 262.0, 26.0):
            sp("marquee_clearspan", x, gz - 16.0, 0.0, 0.6); nm += 1
            if nm % 2: sp("pagoda_kiosk", x + 13.0, gz - 6.0, 0.0, 0.6)
        p0 = len(S.people)
        for x, z in S.spots(xm0 - 8, 268, gz - 34.0, gz + 1.0, 0.18):
            if not S.blocked(x, z): S.person(x, 0.0, z, round(math.pi + rnd.uniform(-0.9, 0.9), 2))
        note["grandstand"] = {"at": [gx, round(gz, 2)], "marquees": nm, "lawn crowd": (len(S.people) - p0) // 4}

    # ------------------------------------------------------------------ the Hill: the rail crowd, boards on the rail
    hill_rail = band(R, *HILL_D, 2.6, 26.0, W)
    frontage = box(FRONTAGE_X[0], 30.0, FRONTAGE_X[1], 120.0)
    people0 = len(S.people)
    for g in GW.polys(hill_rail):
        x0, z0, x1, z1 = g.bounds
        for x, z in S.spots(x0, x1, z0, z1, 0.62):
            q = Point(x, z)
            if not g.contains(q): continue
            dz = infield.exterior.distance(q) if infield.contains(q) else 0.0
            if rnd.random() < (1.0 if dz < 10 else 0.7 if dz < 18 else 0.45):   # thinning towards the back
                S.person(x, 0.0, z, round(math.atan2(0, 1) + rnd.uniform(-0.6, 0.6), 2))
    taken.append(hill_rail)
    # boards fixed along the inside rail in front of the crowd, facing the track (the video's run of boards)
    Ph, Th, Lh, dh = rail_frame(R)
    kk = 0
    for i in range(len(dh)):
        if HILL_D[0] + 10 <= dh[i] <= HILL_D[1] - 20 and i % 1 == 0 and int(dh[i]) % 5 == 0:
            x, z = Ph[i] + Lh[i] * 1.4
            boards.append([r2(x), r2(z), r2(math.degrees(math.atan2(-Lh[i][0], -Lh[i][1]))), DESIGNS[(kk // 3) % 4], 0.8]); kk += 1
    note["hill rail boards"] = kk
    note["hill rail crowd"] = (len(S.people) - people0) // 4

    # ------------------------------------------------------------------ the hospitality frontage opposite the post
    n = 0
    x = FRONTAGE_X[0] + 8
    while x < FRONTAGE_X[1] - 8:
        piece = "stand_covered" if (n % 3) != 1 else "terrace_deck"
        w = 12.5 if piece == "stand_covered" else 10.5
        sp(piece, x + w / 2, 36.0, 180.0, 0.9); x += w + 1.0; n += 1
    taken.append(box(FRONTAGE_X[0], 30.0, FRONTAGE_X[1], 46.0))
    for k, x in enumerate(np.arange(FRONTAGE_X[0] + 14, FRONTAGE_X[1] - 10, 27.0)):
        sp("marquee_peaks", x, 58.0 + (k % 2) * 4, 180.0, 0.6); n += 1
    taken.append(box(FRONTAGE_X[0], 46.0, FRONTAGE_X[1], 72.0))
    S.flat("#e4d8c2", [(FRONTAGE_X[0] - 4, 30), (FRONTAGE_X[1] + 4, 30), (FRONTAGE_X[1] + 4, 74), (FRONTAGE_X[0] - 4, 74)], 0.03)
    note["frontage pieces"] = n

    # ------------------------------------------------------------------ the festival on the Hill behind
    # (owner, 18 Nov, his photo of the Hill on Derby day: packed with stalls, marquees and rides from the rail back; no
    # cars: the festival kit, a Ferris wheel and a helter skelter)
    fest = band(R, 175.0, 660.0, 30.0, 165.0, W).union(band(R, -40.0, 175.0, 78.0, 165.0, W)).intersection(infield) \
        .difference(box(FRONTAGE_X[0] - 6, 28.0, FRONTAGE_X[1] + 6, 76.0))
    rides = []
    Pr, Tr, Lr, dr = rail_frame(R)
    for piece, dd, off in RIDES:
        i = int(np.searchsorted(dr, dd)); q = Pr[i] + Lr[i] * off
        turn = math.degrees(math.atan2(-Lr[i][0], -Lr[i][1]))
        if put:
            put("epsom_stands", piece, q[0], q[1], turn)
            rides.append((q[0], q[1], INFO[piece]["width"] / 2 + 3.0))
    note["festival"] = festival(S, fest, sp, rnd, taken, rides)

    # ------------------------------------------------------------------ Tattenham Corner's inside: crowd, road, huts
    tatt = band(R, *TATT_D, 2.6, 15.0, W)
    p0 = len(S.people)
    for g in GW.polys(tatt):
        x0, z0, x1, z1 = g.bounds
        for x, z in S.spots(x0, x1, z0, z1, 0.42):
            if g.contains(Point(x, z)) and rnd.random() < 0.9:
                a, _ = nearest_points(turf, Point(x, z))
                S.person(x, 0.0, z, round(math.atan2(-(a.x - x), -(a.y - z)) + rnd.uniform(-0.5, 0.5), 2))
    taken.append(tatt)
    road = band(R, TATT_D[0] - 40, TATT_D[1] + 60, 16.0, 22.0, W)
    for g in GW.polys(road): S.flat(ROAD, list(g.simplify(0.5).exterior.coords)[:-1], 0.03)
    taken.append(road)
    nh = 0
    Pt, Tt, Lt, dt = rail_frame(R)
    for dd in np.arange(TATT_D[0] + 60, TATT_D[1] - 30, 70.0):
        i = int(np.searchsorted(dt, dd)); q = Pt[i] + Lt[i] * 30.0
        turn = math.degrees(math.atan2(-Lt[i][0], -Lt[i][1]))
        for k in range(-3, 4):
            x, z = q + Tt[i] * k * 3.2
            S.piece("site_props", "booth_hut", x, z, turn); nh += 1
        if rnd.random() < 0.5:
            q2 = Pt[i] + Lt[i] * 46.0; sp("marquee_clearspan", q2[0], q2[1], turn, 0.4); nh += 1
        taken.append(Point(*q).buffer(16))
    note["tattenham crowd"] = (len(S.people) - p0) // 4
    note["tattenham huts and marquees"] = nh

    # ------------------------------------------------------------------ the climb's inside: small groups on the Downs
    p0 = len(S.people)
    Pc, Tc, Lc, dc = rail_frame(R)
    for i in range(0, len(dc), 6):
        if not (CLIMB_D[0] <= dc[i] <= CLIMB_D[1]) or rnd.random() > 0.45: continue
        q = Pc[i] + Lc[i] * rnd.uniform(3.0, 7.0)
        for _ in range(rnd.randint(2, 9)):
            x, z = q + Tc[i] * rnd.uniform(-4, 4) + Lc[i] * rnd.uniform(-1.2, 3.0)
            S.person(x, 0.0, z, round(math.atan2(Lc[i][0], Lc[i][1]) + rnd.uniform(-0.8, 0.8), 2))
    note["climb groups' people"] = (len(S.people) - p0) // 4

    # ------------------------------------------------------------------ the far side: boards, belts, the woods
    ring = turf.buffer(BOARD_OFF, join_style=1).boundary
    nb = 0
    for seg in getattr(ring, "geoms", [ring]):
        for s in np.arange(3.0, seg.length - 2.0, 6.0):
            q = seg.interpolate(s)
            if infield.buffer(2).contains(q) or STANDS_PLOT.buffer(8).contains(q) or not inside_grid.contains(q): continue
            if q.x < -40 and q.y < 120 and q.y > -60: continue           # the pull-up past the post: open
            boards.append([r2(q.x), r2(q.y), r2(face_turf(q.x, q.y)), DESIGNS[nb % 4], 1.4]); nb += 1
    note["far side boards"] = nb
    woods = polygons(O.get("wood", []) + O.get("scrub", []))
    belt = turf.buffer(BELT[1]).difference(turf.buffer(BELT[0])).difference(infield).difference(STANDS_PLOT.buffer(10))
    nbelt = fill(belt.intersection(woods.buffer(30)), 7.5, (1.15, 1.6), belt=1)
    nbelt += fill(belt.difference(woods.buffer(30)), 9.5, (1.05, 1.5), belt=1, p=0.85)
    note["belt trees"] = nbelt
    canopy_area = woods.intersection(inside_grid).difference(turf.buffer(CANOPY_FROM)).difference(infield).difference(STANDS_PLOT.buffer(12))
    cv = ct = 0
    for g in GW.polys(canopy_area.buffer(4).buffer(-4)):
        near = g.distance(turf) < 160
        m = GW.canopy_mesh(g, rnd, 9.0 if near else 15.0, CANOPY_H)
        if m: canopies.append(m); cv += len(m["v"]) // 3; ct += len(m["i"]) // 3
    note["canopies"] = {"pieces": len(canopies), "points": cv, "triangles": ct}
    ne = 0
    for g in GW.polys(canopy_area.buffer(4).buffer(-4)):
        if g.distance(turf) > 320 or g.area < 600: continue
        for gg in GW.polys(g.buffer(-3.0)):
            for ln in [gg.exterior] + list(gg.interiors):
                for s in np.arange(0, ln.length, 9.0):
                    q = ln.interpolate(s + rnd.uniform(-2, 2)); dq = turf.distance(q)
                    if dq < 60 or dq > 330 or not free(q.x, q.y): continue
                    a, _ = nearest_points(turf, q); ux, uz = (a.x - q.x) / dq, (a.y - q.y) / dq
                    if g.contains(Point(q.x + ux * 9, q.y + uz * 9)): continue
                    tree(q.x, q.y, rnd.uniform(1.3, 1.8), belt=1); ne += 1
    note["wood edge trees"] = ne

    # ------------------------------------------------------------------ stand side east of the stands: a thin crowd
    p0 = len(S.people)
    st_east = band(C["routes"]["straight"], 290, 1060, BOARD_OFF + 2.5, BOARD_OFF + 12.0, W, inside=False).difference(STANDS_PLOT)
    for g in GW.polys(st_east):
        x0, z0, x1, z1 = g.bounds
        for x, z in S.spots(x0, x1, z0, z1, 0.12):
            if g.contains(Point(x, z)): S.person(x, 0.0, z, round(math.pi + rnd.uniform(-0.6, 0.6), 2))
    taken.append(st_east)
    note["stand side crowd"] = (len(S.people) - p0) // 4

    # ------------------------------------------------------------------ houses (Tattenham Corner, Langley Vale) as garden trees
    filler0 = len(trees)
    nhs = 0
    for (x, z), rad in O.get("building", []):
        q = Point(x, z); dq = turf.distance(q)
        if dq < 40 or dq > 300 or not free(x, z) or not inside_grid.contains(q): continue
        if dq > 110 and rnd.random() > 0.25: continue
        for _ in range(rnd.choice([1, 1, 2])):
            tx, tz = x + rnd.uniform(-8, 8), z + rnd.uniform(-8, 8)
            if free(tx, tz): tree(tx, tz, rnd.uniform(0.9, 1.35) * (1.15 if dq > 110 else 1.0), kinds=GARDEN); nhs += 1
    note["garden trees"] = nhs
    # tree rows and the golf courses' edges, near the course
    for p in O.get("treerow", []):
        ln = LineString(p)
        for s in np.arange(0, ln.length, 9.0):
            q = ln.interpolate(s)
            if 25 < turf.distance(q) < 300 and free(q.x, q.y): tree(q.x, q.y, rnd.uniform(1.0, 1.5))
    golf = polygons(O.get("golf", [])).intersection(inside_grid).difference(keep_out)
    for g in GW.polys(golf):
        if g.area < 4000 or g.distance(turf) > 300: continue
        for ln in [g.exterior]:
            for s in np.arange(0, ln.length, 22.0):
                q = ln.interpolate(s + rnd.uniform(-5, 5))
                if free(q.x, q.y) and rnd.random() < 0.55: tree(q.x, q.y, rnd.uniform(1.0, 1.45))
    note["map trees (houses, rows, golf)"] = len(trees) - filler0

    # ------------------------------------------------------------------ flats: paths, roads, the railway, golf greens
    npth = 0
    for p in O.get("path", []):
        ln = LineString(p)
        if ln.length < 8: continue
        g = ln.buffer(1.6, cap_style=2).intersection(inside_grid).difference(turf.buffer(1.0)).difference(STANDS_PLOT)
        for q in GW.polys(g):
            if q.area > 8: S.flat(PATH, list(q.simplify(0.4).exterior.coords)[:-1], 0.02); npth += 1
    nr = 0
    for p in O.get("road", []):
        ln = LineString(p)
        if ln.length < 5 or ln.distance(turf) > 300: continue
        g = ln.buffer(3.2, cap_style=2).intersection(inside_grid).difference(turf.buffer(3.0)).difference(canopy_area)
        for q in GW.polys(g):
            if q.area > 30: S.flat(ROAD, list(q.simplify(0.5).exterior.coords)[:-1], 0.025); nr += 1
    for p in O.get("rail", []):
        g = LineString(p).buffer(4.5, cap_style=2).intersection(inside_grid).difference(turf.buffer(3.0))
        for q in GW.polys(g):
            if q.area > 30: S.flat(RAIL_BALLAST, list(q.simplify(0.5).exterior.coords)[:-1], 0.026); nr += 1
    for g in GW.polys(golf):
        if g.area > 4000 and g.distance(turf) < 420: S.flat("#a9c47f", list(g.simplify(2.0).exterior.coords)[:-1], 0.012)
    note["paths"], note["road and rail pieces"] = npth, nr
    note["people"] = len(S.people) // 4
    return trees, boards, canopies, note


def festival(S, poly, sp, rnd, taken, rides=()):
    """the Hill's festival: marquees, big tops, kiosks, flags, balloon pods and picnic tables on trodden ground, facing
    the straight, with a light crowd through it"""
    g = max(GW.polys(poly), key=lambda q: q.area)
    S.flat("#d8d0a2", list(g.simplify(1.0).exterior.coords)[:-1], 0.028)
    x0, z0, x1, z1 = g.bounds
    placed = list(rides)
    for x, z, r in rides:
        S.nogo.append([(x - r, z - r), (x + r, z - r), (x + r, z + r), (x - r, z + r)])
    def ok(x, z, r):
        return g.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 3 for a, b, rb in placed)
    per = g.area / 10000.0                                          # pieces per hectare, as his photo's Hill
    kit = [("big_top", 0.5, 11.0), ("marquee_peaks", 2.6, 13.0), ("marquee_clearspan", 1.8, 11.0), ("kiosk_row_arched", 2.4, 6.0),
           ("pagoda_kiosk", 5.0, 3.0), ("kiosk_awning", 4.0, 3.5), ("viewing_tower", 0.3, 5.0), ("pergola_picnic", 1.2, 5.0),
           ("picnic_table", 5.0, 1.5), ("banner_flag", 5.0, 1.0), ("balloon_pod", 0.6, 4.0)]
    kit = [(p, max(1, int(round(c * per))), r) for p, c, r in kit]
    n = 0
    for piece, count, r in kit:
        for _ in range(count):
            for _try in range(400):
                x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
                if ok(x, z, r):
                    turn = rnd.uniform(0, 360) if piece in ("big_top", "balloon_pod") else 180.0 + rnd.choice([0, 0, 0, 90, -90])
                    sp(piece, x, z, turn, 0.5); placed.append((x, z, r)); n += 1; break
    people = 0
    for _ in range(int(g.area * 0.045)):
        x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
        if g.contains(Point(x, z)) and not S.blocked(x, z):
            S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); people += 1
    taken.append(g)
    return {"pieces": n, "people": people, "area m2": round(g.area)}
