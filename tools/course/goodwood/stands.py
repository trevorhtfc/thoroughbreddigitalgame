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
STANDS = [
    ("goodwood_balcony", (-48.0, 40.0), 83.0),        # box 1: west of the post, facing up the straight (east)
    ("goodwood_mast", (39.0, 44.0), 177.9),           # box 2: the March Stand's footprint
    ("goodwood_tent", (131.95, 45.0), 182.3),         # box 3: the Sussex Stand's (the tent stand's body; its wing east)
    ("goodwood_victorian", (296.0, 24.5), 188.8),     # box 4: the long building east of it
]
CLEAR = 7.0                                           # the stands keep this clear of the turf (the run-out's outer rail)


def to_w(x, z, turn, u, v):
    a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    return (x + u * ca - v * sa, z - (u * sa + v * ca))


def footprint(piece, x, z, turn, v0=-0.5, v1=None, grow=0.0):
    pi = INFO[piece]; off = pi.get("offset", 0.0) or 0.0; hw = pi["width"] / 2
    v1 = pi["depth"] if v1 is None else v1
    return Polygon([to_w(x, z, turn, u, v) for u, v in ((off - hw - grow, v0), (off + hw + grow, v0), (off + hw + grow, v1), (off - hw - grow, v1))])


def stand_side(S, turf, sp, rnd, NM):
    """Puts the stands, their aprons and crowds, the rail lawn and the festival lawns into the scene S; returns the
    stands' footprints (for the planting to keep clear), the far-side festival zone (its trees come out), the stand
    camera's place, and a note of the counts."""
    note, prints = {}, []
    placed = []
    for piece, (x, z), turn in STANDS:
        fp = footprint(piece, x, z, turn)
        gap = fp.distance(turf)
        if gap < CLEAR:                                 # (slide it until it is clear: back along its own depth, or, for the
            a = math.radians(turn)                      # balcony stand end-on to the run-out, south along its front)
            vx, vz = (-math.cos(a), math.sin(a)) if piece == "goodwood_balcony" else (-math.sin(a), -math.cos(a))
            for k in range(60):
                x, z = x + vx * 0.5, z + vz * 0.5
                fp = footprint(piece, x, z, turn)
                if fp.distance(turf) >= CLEAR: break
        placed.append((piece, x, z, turn)); prints.append(fp)
        pi = INFO[piece]
        S.piece("goodwood_stands", piece, x, z, turn, 1.0, 1.0)
        S.nogo.append(list(footprint(piece, x, z, turn, -1.0).exterior.coords)[:-1])
        S.stand_people(pi, x, z, turn, 1.0, 1.0, 1.45)
        apron = footprint(piece, x, z, turn, -8.0, 0.0, grow=2.0).difference(turf.buffer(2.0))
        if not apron.is_empty: S.flat("#e4d8c2", list(apron.exterior.coords)[:-1], 0.03)
    note["stands"] = [[p, round(x, 1), round(z, 1), t, round(footprint(p, x, z, t).distance(turf), 1)] for p, x, z, t in placed]
    stands_all = unary_union(prints)
    # ---- the rail walk and the crowd: along the stand side's outer rail from the balcony stand to the Victorian stand,
    # thick at the rail, thinner across the lawn back to the stands
    side = box(-60.0, -60.0, 345.0, 120.0).intersection(Polygon([(-60, 120), (-60, 0), (60, 15), (345, -15), (345, 120)]))
    walk = turf.buffer(4.2).difference(turf.buffer(0.2)).intersection(side)
    for g in getattr(walk, "geoms", [walk]):
        if g.area > 20: S.flat("#d9c9a8", list(g.simplify(0.3).exterior.coords)[:-1], 0.025)
    zones = {k: Polygon(v).buffer(0) for k, v in ZONES.items() if k.startswith("festival")}
    fest_side = unary_union([zones["festival_ring"], zones["festival_east"]])
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
    # the stand camera: the TV gantry on the front edge of the mast stand's roof, by the winning line (its west end)
    piece, x, z, turn = placed[1]
    cam = [round(v, 1) for v in to_w(x, z, turn, INFO[piece]["width"] / 2 - 2.5, 4.0)]
    return stands_all, far, [cam[0], round(INFO[piece]["section"]["roofTop"] + 1.6, 1), cam[1]], note
