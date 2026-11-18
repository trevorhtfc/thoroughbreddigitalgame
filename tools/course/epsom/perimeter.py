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
BOARD_W = 5.94 * 1.4          # a board's width at scale 1.4 (5.94 m at scale 1)
BOARD_PITCH = 2.0 * BOARD_W   # (owner, 18 Nov 19:24: "one at a time gap between them": a board, a board's width of gap, a board)
BOARD_OFF = 20.0              # the far side's boards, metres off the turf (beyond the tracking car's lane)
BELT = (25.0, 58.0)           # the belt of real trees off the turf
CANOPY_FROM = 50.0
WOOD_FILL = [(50.0, 150.0, 12.5, (1.2, 1.7)), (150.0, 300.0, 19.0, (1.3, 1.8)), (300.0, 2000.0, 32.0, (1.4, 1.9))]   # (from, to, spacing, scale)
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
# the stand side, left to right from the track: piece, x of its origin, how far its foot is behind the outer rail,
# crowd density on its terraces (owner's mark-up, 18 Nov 11:22)
STANDS = [("epsom_balcony_stand", -85.0, 16.0, 0.85), ("epsom_grandstand", 39.0, 11.0, 1.0), ("epsom_rowley_stand", 183.5, 11.0, 0.85)]   # 19:24: fuller
# the Hill: big lightweight marquees breaking up the rail crowd (metres to go, metres in from the rail), little stands
# along the track edge past the post (owner's purple), big festival tents at his red rings (world x, z)
LITTLE_STANDS = (-80.0, 34.0, 5.8)                                # 19:24: forward to the rail; the two furthest past the post gone (big tops there)
PULL_UP_OPEN = box(-175.0, 0.0, 15.0, 130.0)                     # the Hill past the post: no belt trees (the racecard view looks across it)
RAIL_D = (-60.0, 1180.0)                                          # the thick rail crowd: Tattenham Corner to the post (and past)
BACKDROP = (-40.0, 1170.0, 18.0)                                  # the run of big tents behind the crowd (from, to, front off the rail)
BACKDROP_KIT = ["marquee_peaks", "big_top", "marquee_clearspan", "marquee_peaks", "marquee_clearspan", "big_top"]
SCREENS = [(240.0, 64.0), (560.0, 64.0)]                          # big screens: metres to go, metres in from the rail
# the festival's quarters: name, metres to go from and to, metres in from the rail from and to, kit (piece, per hectare,
# radius), crowd a square metre
FEST_ZONES = [
    ("hospitality village", -40.0, 175.0, 78.0, 170.0,
     [("big_top", 0.9, 11.0), ("marquee_peaks", 3.0, 13.0), ("marquee_clearspan", 2.5, 11.0), ("pergola_picnic", 2.0, 5.0), ("terrace_deck", 1.5, 6.0),
      ("planter_long", 4.0, 2.5), ("picnic_table", 6.0, 1.5), ("flagpole", 4.0, 1.0)], 0.015),
    ("fairground", 175.0, 470.0, 30.0, 170.0,
     [("epsom_carousel", 0.25, 8.5), ("epsom_chair_swing", 0.2, 10.5), ("balloon_pod", 1.0, 4.0), ("kiosk_awning", 3.0, 3.5),
      ("pagoda_kiosk", 3.0, 3.0), ("banner_flag", 6.0, 1.0), ("big_top", 0.8, 11.0), ("picnic_table", 3.0, 1.5)], 0.03),
    ("food court", 470.0, 720.0, 30.0, 170.0,
     [("big_top", 0.6, 11.0), ("pergola_picnic", 2.5, 5.0), ("picnic_table", 9.0, 1.5), ("banner_flag", 5.0, 1.0), ("marquee_clearspan", 1.0, 11.0),
      ("viewing_tower", 0.4, 5.0)], 0.03),
    ("marquee village", 720.0, 1150.0, 30.0, 150.0,
     [("marquee_peaks", 2.5, 13.0), ("marquee_clearspan", 2.0, 11.0), ("big_top", 0.8, 11.0), ("kiosk_row_arched", 1.5, 6.0),
      ("pagoda_kiosk", 2.0, 3.0), ("viewing_tower", 0.3, 5.0), ("banner_flag", 4.0, 1.0)], 0.03),
    # above Tattenham Corner, where the side cameras look across the inside rail (owner: "fill the backgrounds")
    ("top of the corner", 1150.0, 1540.0, 26.0, 120.0,
     [("marquee_clearspan", 2.5, 11.0), ("marquee_peaks", 1.5, 13.0), ("big_top", 0.8, 11.0), ("pagoda_kiosk", 3.0, 3.0),
      ("kiosk_awning", 2.0, 3.5), ("banner_flag", 4.0, 1.0), ("picnic_table", 3.0, 1.5)], 0.025),
]
UPPER_RAIL = (1180.0, 1540.0, 10.0, 0.45)                         # a lighter crowd along the rail above the corner
BIG_TENTS = [(-13.8, 131.4), (53.8, 129.8), (136.0, 128.9), (216.9, 127.8), (310.5, 127.9), (412.6, 133.9), (497.5, 125.0), (614.1, 114.6)]
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

    # ------------------------------------------------------------------ the stands, the walk, the rail lawn
    # (owner's mark-up, 18 Nov 11:22: the balcony stand on the lawn past the post, the grandstand, the Rowley Mile's
    # Victorian stand up the course beside it)
    if put:
        zr = outer_rail_z(turf, GRANDSTAND["x"]) - 0.4
        placed_st = {}
        for piece, x, back, dens in STANDS:
            gi = INFO[piece]
            gz = zr - back                                          # the stand's foot (its front walk or steps' foot)
            put("epsom_stands", piece, x, gz, 0.0)
            S.stand_people(gi, x, gz, 0.0, 1.0, 1.0, dens)
            ox = x + gi.get("offset", 0.0); hw = gi["width"] / 2; f = gi.get("front", 0.0)
            S.nogo.append([(ox - hw, gz - f + 0.5), (ox + hw, gz - f + 0.5), (ox + hw, gz - gi["depth"]), (ox - hw, gz - gi["depth"])])
            placed_st[piece] = [round(ox - hw, 1), round(ox + hw, 1), round(gz - f, 1)]
        S.flat("#e4d8c2", [(-135, zr - 0.6), (275, zr - 0.6), (275, zr - 17.0), (-135, zr - 17.0)], 0.03)
        p0 = len(S.people)
        for x, z in S.spots(-132, 272, zr - 17.0, zr - 1.0, 0.38):    # the rail lawn, facing the track
            if not S.blocked(x, z):
                S.person(x, 0.0, z, round(math.pi + rnd.uniform(-0.5, 0.5), 2))
        note["rail lawn crowd"] = (len(S.people) - p0) // 4
        note["stands"] = placed_st

    # ------------------------------------------------------------------ the Hill and Tattenham Corner: the rail crowd
    # (owner, 18 Nov 12:11: "advert boards as a rule go to track perimeter away from viewing areas ... I would create a
    # denser crowd along the rail from tattenham corner to the finish. Push the kit back at least a little bit. The
    # festival tents can be continued up to the corner where the thick crowd start to create a backdrop. Use big tents")
    Pe, Te, Le, de = rail_frame(R)
    def at_d(dd, off):
        i = int(np.clip(np.searchsorted(de, dd), 0, len(de) - 1)); return Pe[i] + Le[i] * off, math.degrees(math.atan2(-Le[i][0], -Le[i][1]))
    # the little stands along the edge past the post, now just behind the front of the crowd
    nl = 0
    dd = LITTLE_STANDS[0]
    while dd < LITTLE_STANDS[1]:
        piece = "stand_open" if nl % 2 == 0 else "stand_covered"
        w = {"stand_open": 15.62, "stand_covered": 12.31}[piece]
        (lx, lz), turn = at_d(dd + w / 2, LITTLE_STANDS[2])
        sp(piece, lx, lz, turn, 0.95); dd += w + 2.5; nl += 1
    note["little stands"] = nl
    for dd_ in (-128.0, -100.0):                                     # big round tents where the two furthest little stands were
        (tx_, tz_), _ = at_d(dd_, 22.0)
        sp("big_top", tx_, tz_, rnd.uniform(0, 360), 0.5, 1.0, 1.1)
    # Tattenham Corner's road behind the crowd, the huts behind the tents
    road = band(R, RAIL_D[1] - 520, RAIL_D[1] + 60, 17.0, 23.0, W)
    for g in GW.polys(road): S.flat(ROAD, list(g.simplify(0.5).exterior.coords)[:-1], 0.03)
    taken.append(road)
    # the backdrop: big tents in a run right behind the crowd from the post round to Tattenham Corner
    nb_, dd, k = 0, BACKDROP[0], 0
    while dd < BACKDROP[1]:
        piece = BACKDROP_KIT[k % len(BACKDROP_KIT)]
        sc = rnd.uniform(0.95, 1.25)
        w = {"marquee_peaks": 24.75, "big_top": 18.97, "marquee_clearspan": 20.5}[piece] * sc
        off = BACKDROP[2] + (9.5 if piece == "big_top" else 4.8) * sc + (6.0 if dd > RAIL_D[1] - 520 else 0.0)
        (bx, bz), turn = at_d(dd + w / 2, off)
        if not (FRONTAGE_X[0] - 8 < bx < FRONTAGE_X[1] + 8 and bz < 80):
            sp(piece, bx, bz, turn if piece != "big_top" else rnd.uniform(0, 360), 0.5, 1.0, sc); nb_ += 1
            taken.append(Point(bx, bz).buffer(w / 2 + 2))
        dd += w + rnd.uniform(3.0, 9.0); k += 1
    note["backdrop tents"] = nb_
    nh = 0
    for dd in np.arange(RAIL_D[1] - 460, RAIL_D[1] - 40, 90.0):         # portaloo rows behind the backdrop
        (q, turn) = at_d(dd, 62.0)
        i = int(np.clip(np.searchsorted(de, dd), 0, len(de) - 1))
        for kk in range(-3, 4):
            x, z = q + Te[i] * kk * 3.2
            S.piece("site_props", "booth_hut", x, z, turn); nh += 1
        S.nogo.append([tuple(q + Te[i] * 12 + Le[i] * 3), tuple(q - Te[i] * 12 + Le[i] * 3), tuple(q - Te[i] * 12 - Le[i] * 3), tuple(q + Te[i] * 12 - Le[i] * 3)])
    note["huts"] = nh
    # the crowd: thick at the rail, from Tattenham Corner to the post
    rail_band = band(R, *RAIL_D, 2.6, 16.0, W)
    people0 = len(S.people)
    for g in GW.polys(rail_band):
        x0, z0, x1, z1 = g.bounds
        for x, z in S.spots(x0, x1, z0, z1, 0.8):
            q = Point(x, z)
            if not g.contains(q) or S.blocked(x, z): continue
            dz = turf.distance(q)
            if x < 150 and dz > 9.0: continue                          # by the post, in front of the frontage: shallower
            if rnd.random() < (1.0 if dz < 6.5 else 0.8 if dz < 11 else 0.5):   # thinning towards the back
                a_, _ = nearest_points(turf, q)
                S.person(x, 0.0, z, round(math.atan2(-(a_.x - x), -(a_.y - z)) + rnd.uniform(-0.55, 0.55), 2))
    taken.append(rail_band)
    note["rail crowd"] = (len(S.people) - people0) // 4
    p0 = len(S.people)
    up = band(R, UPPER_RAIL[0], UPPER_RAIL[1], 2.6, UPPER_RAIL[2], W)
    for g in GW.polys(up):
        x0, z0, x1, z1 = g.bounds
        for x, z in S.spots(x0, x1, z0, z1, UPPER_RAIL[3]):
            q = Point(x, z)
            if g.contains(q) and not S.blocked(x, z) and rnd.random() < (0.9 if turf.distance(q) < 5 else 0.5):
                a_, _ = nearest_points(turf, q)
                S.person(x, 0.0, z, round(math.atan2(-(a_.x - x), -(a_.y - z)) + rnd.uniform(-0.6, 0.6), 2))
    taken.append(up)
    note["upper rail crowd"] = (len(S.people) - p0) // 4

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

    # ------------------------------------------------------------------ the festival behind the backdrop, in quarters
    # (owner, 12:11: "a bit sort of monotonous.. we need more variety"): a hospitality village behind the frontage, the
    # fairground round the rides, a food court in streets with a big screen, a marquee village inside Tattenham Corner
    rides = []
    for piece, dd, off in RIDES:
        q, turn = at_d(dd, off)
        if put:
            put("epsom_stands", piece, q[0], q[1], turn)
            rides.append((q[0], q[1], INFO[piece]["width"] / 2 + 3.0))
    for x, z in BIG_TENTS:                                          # his red rings: the big festival tents
        sp("big_top", x, z, rnd.uniform(0, 360), 0.5, 1.0, rnd.uniform(1.0, 1.3))
        rides.append((x, z, 13.0))
    note["big tents"] = len(BIG_TENTS)
    for x, z, r in rides[:len(RIDES)]:
        S.nogo.append([(x - r, z - r), (x + r, z - r), (x + r, z + r), (x - r, z + r)])
    back_of = BACKDROP[2] + 30.0
    note["festival"] = {}
    for name, d0, d1, o0, o1, kit, dens in FEST_ZONES:
        zone = band(R, d0, d1, max(o0, back_of if d1 > 175 else o0), o1, W).intersection(infield) \
            .difference(box(FRONTAGE_X[0] - 6, 28.0, FRONTAGE_X[1] + 6, 76.0))
        if zone.is_empty: continue
        if name == "food court":                                    # streets of stalls facing each other
            for off in (back_of + 14.0, back_of + 40.0):
                for dd in np.arange(d0 + 8, d1 - 8, 10.5):
                    for side, o2 in ((1, -3.5), (-1, 3.5)):
                        q, turn = at_d(dd, off + o2)
                        piece = rnd.choice(["kiosk_row_arched", "pagoda_kiosk", "kiosk_awning", "pagoda_counter"])
                        if zone.contains(Point(*q)) and not S.blocked(*q):
                            sp(piece, q[0], q[1], turn if side > 0 else turn + 180.0, 0.6)
                            rides.append((q[0], q[1], 4.0))
        note["festival"][name] = festival(S, zone, sp, rnd, taken, rides, kit, dens)
    if put:
        for dd, off in SCREENS:                                     # big screens, facing the course over the tents
            q, turn = at_d(dd, off)
            put("epsom_stands", "epsom_big_screen", q[0], q[1], turn)
            S.nogo.append([(q[0] - 8, q[1] - 3), (q[0] + 8, q[1] - 3), (q[0] + 8, q[1] + 5), (q[0] - 8, q[1] + 5)])

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
    st_east = band(C["routes"]["straight"], 290, 620, BOARD_OFF - 2.0, BOARD_OFF + 12.0, W, inside=False).difference(STANDS_PLOT)   # (not round the outside of the corner, where the head-on camera stands)
    ring = turf.buffer(BOARD_OFF, join_style=1).boundary
    nb = 0
    for seg in getattr(ring, "geoms", [ring]):
        for s in np.arange(3.0, seg.length - 2.0, BOARD_PITCH):
            q = seg.interpolate(s)
            if infield.buffer(2).contains(q) or STANDS_PLOT.buffer(8).contains(q) or not inside_grid.contains(q): continue
            if q.x < -40 and q.y < 120 and q.y > -60: continue           # the pull-up past the post: open
            if st_east.buffer(5).contains(q): continue                  # no boards in front of people (owner, 12:11)
            boards.append([r2(q.x), r2(q.y), r2(face_turf(q.x, q.y)), DESIGNS[nb % 4], 1.4]); nb += 1
    note["far side boards"] = nb
    woods = polygons(O.get("wood", []) + O.get("scrub", []))
    belt = turf.buffer(BELT[1]).difference(turf.buffer(BELT[0])).difference(infield).difference(STANDS_PLOT.buffer(10)).difference(PULL_UP_OPEN)
    nbelt = fill(belt.intersection(woods.buffer(30)), 7.5, (1.15, 1.6), belt=1)
    nbelt += fill(belt.difference(woods.buffer(30)), 9.5, (1.05, 1.5), belt=1, p=0.85)
    note["belt trees"] = nbelt
    # the woods beyond the belt (owner, 12:11: "a lot of floating trees, weird faceted lumps"): the light canopy meshes
    # read as dark slabs and sheets hovering among the trees from the race cameras' low angles, so the woods are trees
    # throughout: close together near the course, further apart away from it (far off each is a flat picture, cheap)
    canopy_area = woods.intersection(inside_grid).difference(turf.buffer(CANOPY_FROM)).difference(infield).difference(STANDS_PLOT.buffer(12))
    ne = 0
    for lo, hi, gap, sc in WOOD_FILL:
        ring_ = turf.buffer(hi).difference(turf.buffer(lo))
        ne += fill(canopy_area.intersection(ring_), gap, sc, kinds=KINDS)
    note["canopies"] = {"pieces": 0}
    note["wood edge trees"] = ne

    # ------------------------------------------------------------------ stand side east of the stands: a thin crowd
    p0 = len(S.people)
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


def festival(S, poly, sp, rnd, taken, placed, kit, dens):
    """a quarter of the Hill's festival: its kit (piece, per hectare, radius) on trodden ground, mostly facing the
    straight, with a crowd through it at dens a square metre"""
    out = {"pieces": 0, "people": 0, "area m2": 0}
    for g in GW.polys(poly):
        if g.area < 1500: continue
        S.flat("#d8d0a2", list(g.simplify(1.0).exterior.coords)[:-1], 0.028)
        x0, z0, x1, z1 = g.bounds
        def ok(x, z, r):
            return g.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 3 for a, b, rb in placed) and not S.blocked(x, z)
        per = g.area / 10000.0
        for piece, c, r in kit:
            for _ in range(max(1, int(round(c * per)))):
                for _try in range(300):
                    x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
                    if ok(x, z, r):
                        sc = rnd.uniform(0.9, 1.2) if piece in ("marquee_peaks", "marquee_clearspan", "big_top") else 1.0
                        turn = rnd.uniform(0, 360) if piece in ("big_top", "balloon_pod") else 180.0 + rnd.choice([0, 0, 0, 90, -90, 180])
                        if piece.startswith("epsom_"):
                            S.piece("epsom_stands", piece, x, z, turn)
                            S.nogo.append([(x - r, z - r), (x + r, z - r), (x + r, z + r), (x - r, z + r)])
                        else:
                            sp(piece, x, z, turn, 0.5, 1.0, sc)
                        placed.append((x, z, r * sc)); out["pieces"] += 1; break
        for _ in range(int(g.area * dens)):
            x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
            if g.contains(Point(x, z)) and not S.blocked(x, z):
                S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); out["people"] += 1
        taken.append(g); out["area m2"] += round(g.area)
    return out
