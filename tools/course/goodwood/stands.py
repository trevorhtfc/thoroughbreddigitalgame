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
    fest_side = unary_union([zones["festival_ring"], zones["festival_east"]])
    # ---- the festival lawns (his blue zones): between the stands, and a little on the far side round the finish
    kit = [("marquee_peaks", 13.0), ("marquee_clearspan", 11.0), ("kiosk_row_arched", 6.0), ("pagoda_kiosk", 3.0),
           ("kiosk_awning", 3.5), ("pergola_picnic", 5.0), ("picnic_table", 1.5), ("banner_flag", 1.0), ("pagoda_counter", 3.5)]
    def festival(poly, counts, people, face_turn):
        g = max([q for q in getattr(poly, "geoms", [poly]) if q.geom_type == "Polygon"], key=lambda q: q.area)
        S.flat("#ddd3a8", list(g.simplify(0.8).exterior.coords)[:-1], 0.028)
        gx0, gz0, gx1, gz1 = g.bounds; put = []; k = 0
        for (piece, r), c in zip(kit, counts):
            for _ in range(c):
                for _try in range(150):
                    x, z = rnd.uniform(gx0, gx1), rnd.uniform(gz0, gz1)
                    if g.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 2.5 for a, b, rb in put):
                        sp(piece, x, z, face_turn + rnd.choice([0, 0, 0, 90, -90]) if piece != "banner_flag" else face_turn, 0.6)
                        put.append((x, z, r)); k += 1; break
        m = 0
        for x, z in S.spots(gx0, gx1, gz0, gz1, people):
            if g.contains(Point(x, z)) and not S.blocked(x, z):
                S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); m += 1
        return {"pieces": k, "people": m, "area m2": round(g.area)}
    keep_turf = turf.buffer(14.0)
    ring = zones["festival_ring"].difference(stands_all.buffer(3.0)).difference(keep_turf)
    east = zones["festival_east"].difference(stands_all.buffer(3.0)).difference(keep_turf)
    far = zones["festival_far"].difference(turf.buffer(24.0))         # (behind the boards' line, clear of the tracking car)
    note["festival by the balcony stand"] = festival(ring, [1, 1, 1, 2, 2, 1, 6, 4, 1], 0.09, 180.0)
    note["festival between tent and Victorian stands"] = festival(east, [2, 2, 2, 3, 3, 2, 10, 6, 1], 0.09, 180.0)
    note["festival on the far side"] = festival(far, [1, 1, 1, 2, 2, 1, 6, 5, 0], 0.05, 0.0)
    # ---- every gap (owner, 18 Nov 09:04: "in fill all gaps with festival and trees including big bits up from the
    # Victorian stand as that gable end flank wall needs a bit of embedding"): the rest of the stand side, from the
    # balcony stand to where the planting begins east of the Victorian stand. Near the course (14 to 70 m off the turf):
    # festival kit and a crowd; further back and behind the stands: trees. Against the Victorian stand's east end, a
    # clump of big trees round its flank wall, and the big festival lawn beyond it.
    fill_trees = []
    def tree(x, z, sc_, belt=1):
        fill_trees.append([round(x, 2), round(z, 2), rnd.choice(("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")), round(sc_, 2), rnd.randrange(360), belt])
    taken = unary_union([stands_all.buffer(3.0), fest_side.buffer(2.0), zones["festival_far"], turf.buffer(14.0)])
    side_box = box(-120.0, -10.0, 660.0, 260.0)
    gaps = side_zone.intersection(side_box).difference(taken)
    near = gaps.intersection(turf.buffer(70.0))
    back = gaps.difference(turf.buffer(70.0)).difference(turf.buffer(25.0).buffer(0))
    big = [("big_top", 11.0), ("marquee_peaks", 13.0), ("marquee_clearspan", 11.0), ("viewing_tower", 5.0), ("kiosk_row_arched", 6.0),
           ("pagoda_kiosk", 3.0), ("kiosk_awning", 3.5), ("pergola_picnic", 5.0), ("picnic_table", 1.5), ("banner_flag", 1.0),
           ("balloon_pod", 4.0), ("terrace_deck", 6.5)]
    put, k, m = [], 0, 0
    for g in sorted([q for q in getattr(near, "geoms", [near]) if q.geom_type == "Polygon" and q.area > 150], key=lambda q: -q.area):
        gx0, gz0, gx1, gz1 = g.bounds; east = gx0 > 330          # (on the lawn's own grass: no trodden ground)          # (east of the Victorian stand: the big festival lawn)
        per = g.area / (900.0 if east else 1400.0)
        for piece, r in big:
            if piece in ("big_top", "viewing_tower", "balloon_pod") and not east: continue
            n = {"picnic_table": 4, "banner_flag": 3, "pagoda_kiosk": 2}.get(piece, 1) * per / 6
            for _ in range(int(n) + (1 if rnd.random() < n % 1 else 0)):
                for _try in range(80):
                    x, z = rnd.uniform(gx0, gx1), rnd.uniform(gz0, gz1)
                    if g.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 2.5 for a, b, rb in put):
                        sp(piece, x, z, rnd.uniform(0, 360) if piece in ("big_top", "balloon_pod") else 180.0 + rnd.choice([0, 0, 90, -90]), 0.6)
                        put.append((x, z, r)); k += 1; break
        for x, z in S.spots(gx0, gx1, gz0, gz1, 0.07):
            if g.contains(Point(x, z)) and not S.blocked(x, z):
                S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); m += 1
    pb = prep(back); bx0, bz0, bx1, bz1 = back.bounds; nt = 0
    for x in np.arange(bx0, bx1, 10.5):
        for z in np.arange(bz0, bz1, 10.5):
            px, pz = x + rnd.uniform(-3.5, 3.5), z + rnd.uniform(-3.5, 3.5)
            if pb.contains(Point(px, pz)) and rnd.random() < 0.8: tree(px, pz, rnd.uniform(1.15, 1.7)); nt += 1
    # the Victorian stand's east end: big trees round the flank wall, from the lawn's back to well behind the stand
    piece, x, z, turn, (X, sc) = placed[3]
    hw = INFO[piece]["width"] / 2 * X
    nv = 0
    for _ in range(60):
        u, v = -hw - rnd.uniform(3.0, 26.0), rnd.uniform(4.0, INFO[piece]["depth"] * sc + 22.0)      # (u < 0: its east end)
        tx, tz = to_w(x, z, turn, u, v)
        if turf.distance(Point(tx, tz)) > 25.0 and not S.blocked(tx, tz):
            tree(tx, tz, rnd.uniform(1.4, 1.95)); nv += 1
    note["gaps filled"] = {"festival pieces": k, "people": m, "trees": nt, "trees at the Victorian stand's end": nv}
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
    cam = [round(v, 1) for v in to_w(x, z, turn, INFO[piece]["width"] / 2 * X - 2.5, 4.0 * sc)]
    return stands_all, far, [cam[0], round(INFO[piece]["section"]["roofTop"] * sc + 1.6, 1), cam[1]], fill_trees, note
