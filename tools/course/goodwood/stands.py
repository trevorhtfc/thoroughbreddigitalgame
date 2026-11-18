"""Goodwood, phase 4: the stand side, from the owner's mark-up of 18 Nov 2026 (reference/goodwood/stands-markup.jpg; his
boxes and zones in world axes: reference/goodwood/stands-zones.json).

  "Mark up of stand types. Make the stand types longer if needed to proportionally fill the space
   1. Balcony stand facing up the home straight  2. Mast stand  3. Tent stand  4. Victorian stand
   Blue zone are then marquees / festival kit [between the] stands with a small amount of festival stuff around the
   finish line and just beyond the finish to frame the view. It can start as the trees start to drop away."
  "Try and keep the alignment of the stand to the track as per the Google image."

The stands (tools/blender/build_goodwood_stands.py) stand on his boxes, each turned as the real building is (the OSM
footprints: the March Stand +2.1 degrees off the straight, the Sussex Stand -2.3, the long building east -8.3; the
balcony stand square to the straight, west of the post, looking up it). Their fronts (the foot of their steps) keep the
real buildings' set back from the outer rail. Then: an apron in front of each, the rail walk and the rail crowd, the
lawn back to the stands; his three blue zones as festival lawns (marquees, kiosks, flags, picnic tables, a crowd); and
the stand camera moves onto the mast stand.
"""
import json, math, random
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep

REPO = Path(__file__).resolve().parents[3]
ZONES = json.loads((REPO / "reference/goodwood/stands-zones.json").read_text())["world"]
MARK = json.loads((REPO / "reference/goodwood/stand-side-markup.json").read_text())["world"]   # his mark-up of the plan, 18 Nov 12:24
INFO = json.loads((REPO / "assets/models/architecture/goodwood_stands.json").read_text())["pieces"]

# piece, front middle (world x, z), turn (degrees: 180 faces the track from the stand side; the front line's angle
# off the straight taken off it), as his boxes and the real buildings
# and the scale (along the front, then height and depth). Owner, 18 Nov 09:04: "the mast and tent stand are a bit small..
# and the balcony stand a bit tall": the mast stand a bay longer and both 12% bigger; the balcony stand 15% lower (and
# shallower), its length kept.
STANDS = [
    ("goodwood_balcony", (-48.0, 40.0), 83.0, (1.0, 0.85)),      # box 1: west of the post, facing up the straight (east)
    ("goodwood_mast", (48.1, 44.3), 177.9, (1.12, 1.12)),        # box 2: the March Stand's footprint, from the post east
    ("goodwood_tent", (130.0, 45.0), 182.3, (1.12, 1.12)),       # box 3: the Sussex Stand's (the tent stand's body; its wing east)
    ("goodwood_victorian", (296.0, 24.5), 188.8, (1.0, 1.0)),    # box 4: the long building east of it
]
CLEAR = 7.0                                           # the stands keep this clear of the turf (the run-out's outer rail)


def to_w(x, z, turn, u, v):
    a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    return (x + u * ca - v * sa, z - (u * sa + v * ca))


def footprint(piece, x, z, turn, v0=-0.5, v1=None, grow=0.0, scale=(1.0, 1.0)):
    pi = INFO[piece]; X, sc = scale; off = (pi.get("offset", 0.0) or 0.0) * X; hw = pi["width"] / 2 * X
    v1 = pi["depth"] * sc if v1 is None else v1
    return Polygon([to_w(x, z, turn, u, v) for u, v in ((off - hw - grow, v0), (off + hw + grow, v0), (off + hw + grow, v1), (off - hw - grow, v1))])


def stand_side(S, turf, sp, rnd, NM, side_zone):
    """Puts the stands, their aprons and crowds, the rail lawn and the festival lawns into the scene S; returns the
    stands' footprints (for the planting to keep clear), the far-side festival zone (its trees come out), the stand
    camera's place, and a note of the counts."""
    note, prints = {}, []
    placed = []
    for piece, (x, z), turn, scale in STANDS:
        fp = footprint(piece, x, z, turn, scale=scale)
        gap = fp.distance(turf)
        if gap < CLEAR:                                 # (slide it until it is clear: back along its own depth, or, for the
            a = math.radians(turn)                      # balcony stand end-on to the run-out, south along its front)
            vx, vz = (-math.cos(a), math.sin(a)) if piece == "goodwood_balcony" else (-math.sin(a), -math.cos(a))
            for k in range(60):
                x, z = x + vx * 0.5, z + vz * 0.5
                fp = footprint(piece, x, z, turn, scale=scale)
                if fp.distance(turf) >= CLEAR: break
        placed.append((piece, x, z, turn, scale)); prints.append(fp)
        pi = INFO[piece]; X, sc = scale
        S.piece("goodwood_stands", piece, x, z, turn, X, sc)
        S.nogo.append(list(footprint(piece, x, z, turn, -1.0, scale=scale).exterior.coords)[:-1])
        S.stand_people(pi, x, z, turn, X / sc, sc, 1.45)
        apron = footprint(piece, x, z, turn, -8.0, 0.0, grow=2.0, scale=scale).difference(turf.buffer(2.0))
        if not apron.is_empty: S.flat("#e4d8c2", list(apron.exterior.coords)[:-1], 0.03)
    note["stands"] = [[p, round(x, 1), round(z, 1), t, sc, round(footprint(p, x, z, t, scale=sc).distance(turf), 1)] for p, x, z, t, sc in placed]
    stands_all = unary_union(prints)
    # ---- the rail walk and the crowd: along the stand side's outer rail from the balcony stand to the Victorian stand,
    # thick at the rail, thinner across the lawn back to the stands
    side = box(-60.0, -60.0, 345.0, 120.0).intersection(Polygon([(-60, 120), (-60, 0), (60, 15), (345, -15), (345, 120)]))
    walk = turf.buffer(4.2).difference(turf.buffer(0.2)).intersection(side)
    for g in getattr(walk, "geoms", [walk]):
        if g.area > 20: S.flat("#d9c9a8", list(g.simplify(0.3).exterior.coords)[:-1], 0.025)
    zones = {k: Polygon(v).buffer(0) for k, v in ZONES.items() if k.startswith("festival")}
    # his mark-up of the plan (18 Nov 12:24): the orange festival zones replace the far-side and tent-to-Victorian blue
    # zones and add a big one east of the Victorian stand; the one by the balcony stand stays as it was
    for k in ("orange_far", "orange_tent_victorian", "orange_east"):
        zones[k] = Polygon(MARK[k]).buffer(0)
    fest_side = unary_union([zones["festival_ring"], zones["orange_tent_victorian"], zones["orange_east"]])
    def festival(poly, mix, people, face_turn, rides=()):
        """trodden ground, then the mix (biggest first: piece, radius, how many), then a crowd"""
        g = max([q for q in getattr(poly, "geoms", [poly]) if q.geom_type == "Polygon"], key=lambda q: q.area)
        S.flat("#ddd3a8", list(g.simplify(0.8).exterior.coords)[:-1], 0.028)
        gx0, gz0, gx1, gz1 = g.bounds; put = []; k = 0
        def spot(r):
            for _try in range(200):
                x, z = rnd.uniform(gx0, gx1), rnd.uniform(gz0, gz1)
                if g.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 2.5 for a, b, rb in put):
                    put.append((x, z, r)); return x, z
            return None
        for piece, r in rides:                                    # (the helter skelter: from the stands' kit)
            q = spot(r)
            if q:
                S.piece("goodwood_stands", piece, q[0], q[1], rnd.uniform(0, 360), 1.0, 1.0)
                S.nogo.append([(q[0] - r, q[1] - r), (q[0] + r, q[1] - r), (q[0] + r, q[1] + r), (q[0] - r, q[1] + r)]); k += 1
        for piece, r, c in mix:
            for _ in range(c):
                q = spot(r)
                if not q: continue
                turn = rnd.uniform(0, 360) if piece in ("big_top", "balloon_pod") else face_turn + (0 if piece in ("banner_flag", "stand_open", "stand_covered", "terrace_deck") else rnd.choice([0, 0, 0, 90, -90]))
                sp(piece, q[0], q[1], turn, 0.6); k += 1
        m = 0
        for x, z in S.spots(gx0, gx1, gz0, gz1, people):
            if g.contains(Point(x, z)) and not S.blocked(x, z):
                S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); m += 1
        return {"pieces": k, "people": m, "area m2": round(g.area)}
    # his mix: "the marquees, bigger tents, balloons, little terraces, flags etc.. you can add a helter skelter as well as
    # per epsom": counts scale with each zone's size
    def mix(area, big=True):
        f = area / 1000.0
        L = [("big_top", 11.0, round(f * 0.25) if big else 0), ("marquee_peaks", 13.0, round(f * 0.35)), ("marquee_clearspan", 11.0, round(f * 0.3)),
             ("balloon_pod", 4.0, round(f * 0.3) if big else 0), ("stand_open", 8.5, round(f * 0.12)), ("stand_covered", 7.0, round(f * 0.12)),
             ("terrace_deck", 6.5, round(f * 0.2)), ("kiosk_row_arched", 6.0, round(f * 0.3)), ("pagoda_kiosk", 3.0, round(f * 0.5)),
             ("kiosk_awning", 3.5, round(f * 0.4)), ("pergola_picnic", 5.0, round(f * 0.25)), ("picnic_table", 1.5, round(f * 1.4)),
             ("banner_flag", 1.0, round(f * 1.2))]
        return [(p_, r_, c_) for p_, r_, c_ in L if c_ > 0]
    keep_turf = turf.buffer(14.0)
    ring = zones["festival_ring"].difference(stands_all.buffer(3.0)).difference(keep_turf)
    tv = zones["orange_tent_victorian"].difference(stands_all.buffer(3.0)).difference(keep_turf)
    east = zones["orange_east"].difference(stands_all.buffer(3.0)).difference(keep_turf)
    far = zones["orange_far"].difference(turf.buffer(22.0))           # (behind the boards' line, clear of the tracking car)
    note["festival by the balcony stand"] = festival(ring, mix(ring.area, big=False), 0.09, 180.0)
    note["festival between tent and Victorian stands"] = festival(tv, mix(tv.area), 0.09, 180.0)
    note["festival east of the Victorian stand"] = festival(east, mix(east.area), 0.08, 180.0, rides=[("goodwood_helter_skelter", 6.5)])
    note["festival on the far side"] = festival(far, mix(far.area, big=False), 0.05, 0.0)
    # ---- trees: behind the stands (the stand side's back, as the second pass), none in the festival zones; and his green
    # rings ("some moves of planting"): a clump at each
    fill_trees = []
    def tree(x, z, sc_, belt=1):
        fill_trees.append([round(x, 2), round(z, 2), rnd.choice(("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")), round(sc_, 2), rnd.randrange(360), belt])
    fests = unary_union([fest_side, zones["orange_far"]])
    taken = unary_union([stands_all.buffer(3.0), fests.buffer(2.0), turf.buffer(14.0)])
    side_box = box(-120.0, -10.0, 660.0, 260.0)
    back = side_zone.intersection(side_box).difference(taken).difference(turf.buffer(70.0))
    pb = prep(back); bx0, bz0, bx1, bz1 = back.bounds; nt = 0
    for x in np.arange(bx0, bx1, 10.5):
        for z in np.arange(bz0, bz1, 10.5):
            px, pz = x + rnd.uniform(-3.5, 3.5), z + rnd.uniform(-3.5, 3.5)
            if pb.contains(Point(px, pz)) and rnd.random() < 0.8: tree(px, pz, rnd.uniform(1.15, 1.7)); nt += 1
    ng = 0
    for cx, cz in MARK["green_planting"]:
        for _ in range(6):
            tx, tz = cx + rnd.uniform(-7, 7), cz + rnd.uniform(-7, 7)
            if turf.distance(Point(tx, tz)) > 23.0 and not S.blocked(tx, tz) and not stands_all.buffer(2.0).contains(Point(tx, tz)):
                tree(tx, tz, rnd.uniform(1.3, 1.85)); ng += 1
    note["trees"] = {"behind the stands": nt, "his green rings": ng}
    # ---- the rail and lawn crowd (after the kit, so nobody stands in a marquee)
    lawn = turf.buffer(60.0).difference(turf.buffer(1.2)).intersection(side).difference(stands_all.buffer(1.0)).difference(fest_side)
    pl = prep(lawn); n = 0
    x0, z0, x1, z1 = lawn.bounds
    for x, z in S.spots(x0, x1, z0, z1, 0.9):
        q = Point(x, z)
        if not pl.contains(q) or S.blocked(x, z): continue
        d = turf.distance(q)
        keep = 1.0 if d < 9.0 else 0.45 if d < 16.0 else 0.11
        if rnd.random() > keep: continue
        a, _ = nearest_points(turf, q)
        S.person(x, 0.0, z, NM.face(a.x - x, a.y - z)); n += 1
    note["rail and lawn people"] = n
    # the stand camera: the TV gantry on the front edge of the mast stand's roof, by the winning line (its west end)
    piece, x, z, turn, (X, sc) = placed[1]
    cam = [round(v, 1) for v in to_w(x, z, turn, INFO[piece]["width"] / 2 * X - 2.5, 1.0)]
    return stands_all, fests, [cam[0], round(INFO[piece]["section"]["roofTop"] * sc + 1.6, 1), cam[1]], fill_trees, note


def angled_adverts(S, turf, boards, trees, x0=60.0, x1=505.0, every=43.0, scale=3.2, angle=50.0):
    """The far side of the home straight. Owner, 18 Nov 12:24 (purple on his plan): "adverts to be at an angle and set
    out evenly"; 12:41, on short runs of small boards: "looks an absolute mess look at how they look on the home
    straight in the video" (a few big hoardings, well apart, in front of the trees); 14:32, on plain slate hoardings:
    "they should be the same as my thoroughbred ones". So: at each of his strokes, set out evenly (every 'every' metres
    from x0 to x1), one of the course's own Thoroughbred advertising boards (the planting kit's board_green / cream /
    navy / white, as round every other course) made big ('scale' times its 6 m: about 19 m wide, the panel about 3.3 to
    7.5 m up), its near end on the 20 m line and running back at 'angle' degrees to the track, towards the post, its
    face to the stands and the run-in. The small boards on that stretch go, and the trees where the big ones stand."""
    from shapely.geometry import LineString
    ring = turf.buffer(20.0, join_style=1).boundary
    north = lambda b: x0 - 15 < b[0] < x1 + 15 and turf.distance(Point(b[0], b[1])) < 24.0 and b[1] < _north_edge(turf, b[0])
    kept = [b for b in boards if not north(b)]
    designs = ["green", "navy", "cream", "white"]
    length = 6.0 * scale
    out, feet = [], []
    for x in np.arange(x0, x1 + 1e-6, every):
        pts = []
        for xx in (x - 4.0, x + 4.0):
            hit = ring.intersection(LineString([(xx, -300.0), (xx, _north_edge(turf, xx))]))
            cand = [g for g in getattr(hit, "geoms", [hit]) if g.geom_type == "Point"]
            if not cand: break
            pts.append(max(cand, key=lambda g: g.y))                       # the 20 m line just north of the turf
        if len(pts) < 2: continue
        rx, rz = pts[1].x - pts[0].x, pts[1].y - pts[0].y
        a = math.atan2(rz, rx) + math.radians(180.0 + angle)               # back from the track, towards the post
        ux, uz = math.cos(a), math.sin(a)
        nx, nz = -uz, ux                                                   # the face: towards the stands and the run-in
        if nz < 0: nx, nz = -nx, -nz
        sx, sz = (pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2
        cx, cz = sx + ux * (length / 2 + 1.0), sz + uz * (length / 2 + 1.0)
        out.append([round(cx, 2), round(cz, 2), round(math.degrees(math.atan2(nx, nz)), 2), designs[len(out) % 4], scale])
        e0, e1 = (cx - ux * length / 2, cz - uz * length / 2), (cx + ux * length / 2, cz + uz * length / 2)
        # (clear the trees on it and in front of its face, out to the 20 m line, so the whole board reads)
        feet.append(Polygon([(e0[0] - nx * 4, e0[1] - nz * 4), (e1[0] - nx * 4, e1[1] - nz * 4), (e1[0] + nx * 22, e1[1] + nz * 22),
                             (e0[0] + nx * 22, e0[1] + nz * 22)]).buffer(1.0))
    near = unary_union(feet)
    trees = [t for t in trees if not near.contains(Point(t[0], t[1]))]
    return kept + out, trees, len(out)


def _north_edge(turf, x):
    """the turf's north edge at world x (the smallest z of the turf there), or 0"""
    from shapely.geometry import LineString
    hit = turf.intersection(LineString([(x, -400.0), (x, 400.0)]))
    zs = [c[1] for g in getattr(hit, "geoms", [hit]) for c in getattr(g, "coords", [])]
    return min(zs) if zs else 0.0
