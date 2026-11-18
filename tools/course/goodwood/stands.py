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
from shapely.geometry import Polygon, Point, box, LineString
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
    far = zones["orange_far"].difference(turf.buffer(6.0))            # (owner, 18 Nov evening: "move the festival closer to the rail")
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


def angled_adverts(S, turf, boards, trees, x0=60.0, x1=505.0, every=43.0, scale=2.0, angle=22.0, off=9.0, clear_x0=-110.0):
    """The far side of the home straight. Owner, 18 Nov: 12:24 (purple on his plan) "adverts to be at an angle and set
    out evenly"; 12:41 on short runs of small boards: "looks an absolute mess look at how they look on the home straight
    in the video"; 14:32 on plain slate hoardings: "they should be the same as my thoroughbred ones"; 22:26 on single
    boards at 3.2 times: "the advert boards are too big and hidden in the bushes. review the real footage" and "get rid
    of the adverts behind the finish line", "advert boards overlapping again. please spread them out", "closer to the
    rail".
    The footage: long low hoardings close behind the rail, in front of the trees, each about four times as long as it is
    tall, turned a little towards the stands. So at each of his strokes (every 'every' metres from x0 to x1): a hoarding
    of two of our own Thoroughbred boards end to end at 'scale' (each 12 m wide, the panel about 2.2 to 4.7 m up: about
    24 m long), its near end 'off' metres off the turf, turned 'angle' degrees back from the track towards the post,
    faces to the stands. Every other board on the far side from clear_x0 to x1 goes (none behind the finish), and the
    trees on and in front of each hoarding."""
    from shapely.geometry import LineString
    ring = turf.buffer(off, join_style=1).boundary
    north = lambda b: clear_x0 < b[0] < x1 + 25 and b[1] < _north_edge(turf, b[0]) and turf.distance(Point(b[0], b[1])) < 30.0
    kept = [b for b in boards if not north(b)]
    designs = ["green", "navy", "cream", "white"]
    w = 6.0 * scale
    out, feet = [], []
    for k, x in enumerate(np.arange(x0, x1 + 1e-6, every)):
        pts = []
        for xx in (x - 4.0, x + 4.0):
            hit = ring.intersection(LineString([(xx, -300.0), (xx, _north_edge(turf, xx))]))
            cand = [g for g in getattr(hit, "geoms", [hit]) if g.geom_type == "Point"]
            if not cand: break
            pts.append(max(cand, key=lambda g: g.y))                       # the line just north of the turf
        if len(pts) < 2: continue
        rx, rz = pts[1].x - pts[0].x, pts[1].y - pts[0].y
        a = math.atan2(rz, rx) + math.radians(180.0 + angle)               # back from the track, towards the post
        ux, uz = math.cos(a), math.sin(a)
        nx, nz = -uz, ux                                                   # the face: towards the stands and the run-in
        if nz < 0: nx, nz = -nx, -nz
        sx, sz = (pts[0].x + pts[1].x) / 2, (pts[0].y + pts[1].y) / 2
        turn = round(math.degrees(math.atan2(nx, nz)), 2)
        for j in range(2):                                                 # two boards end to end, one design
            cx, cz = sx + ux * (w * (j + 0.5) + 0.2), sz + uz * (w * (j + 0.5) + 0.2)
            out.append([round(cx, 2), round(cz, 2), turn, designs[k % 4], scale])
        e0, e1 = (sx, sz), (sx + ux * 2 * w, sz + uz * 2 * w)
        feet.append(Polygon([(e0[0] - nx * 4, e0[1] - nz * 4), (e1[0] - nx * 4, e1[1] - nz * 4), (e1[0] + nx * 14, e1[1] + nz * 14),
                             (e0[0] + nx * 14, e0[1] + nz * 14)]).buffer(1.5))
    near = unary_union(feet)
    trees = [t for t in trees if not near.contains(Point(t[0], t[1]))]
    kept = [b for b in kept if not near.buffer(6.0).contains(Point(b[0], b[1]))]
    return kept + out, trees, len(out) // 2


def _north_edge(turf, x):
    """the turf's north edge at world x (the smallest z of the turf there), or 0"""
    from shapely.geometry import LineString
    hit = turf.intersection(LineString([(x, -400.0), (x, 400.0)]))
    zs = [c[1] for g in getattr(hit, "geoms", [hit]) for c in getattr(g, "coords", [])]
    return min(zs) if zs else 0.0


def runout_festival(S, turf, rail, trees, sp, rnd, NM, avoid, d_from=-430.0, d_to=-95.0):
    """Festival kit all along the run-out, in amongst its trees (owner, 18 Nov 23:31, of the run-out past the post: "we
    should add festival tents all along this run out element of the track in amongst the trees"). Both sides of it,
    16-30 m off the turf, faces to the track: marquees, kiosks, little open stands, pergolas, balloons and flags in a
    loose run, each on its own patch of trodden ground with a few people round it. The trees standing where a piece
    goes come out (3 m round it); the rest stay, so the kit sits among them.
    rail: [(d, x, z)] the straight route's rail, d metres to go (negative past the post). avoid: nothing goes here."""
    from shapely.affinity import rotate as _rot
    pts = [(x, z) for d, x, z in rail if d_from <= d <= d_to]
    corridor = LineString(pts).buffer(75.0)
    ok = corridor.difference(turf.buffer(14.0)).difference(avoid)
    cycle = [("marquee_peaks", 2), ("kiosk_awning", 1), ("pagoda_kiosk", 1), ("marquee_clearspan", 2), ("banner_flag", 0),
             ("stand_open", 2), ("pergola_picnic", 1), ("balloon_pod", 1), ("kiosk_row_arched", 1), ("banner_flag", 0)]
    placed, clear, k, people, new_trees = [], [], 0, 0, []
    for off in (19.0, 27.0):
        line = turf.buffer(off).exterior.intersection(corridor)
        for l in [g for g in getattr(line, "geoms", [line]) if g.geom_type == "LineString"]:
            s = rnd.uniform(0, 14)
            while s < l.length:
                piece, crowd = cycle[k % len(cycle)]
                w, dd = NM.SP_SIZE[piece]
                q = l.interpolate(s); a = l.interpolate(max(0.0, s - 2)); b = l.interpolate(min(l.length, s + 2))
                tx, tz = b.x - a.x, b.y - a.y; n = math.hypot(tx, tz) or 1.0
                # the front faces the turf: whichever normal points at it
                nx_, nz_ = -tz / n, tx / n
                if turf.distance(Point(q.x + nx_ * 3, q.y + nz_ * 3)) > turf.distance(Point(q.x - nx_ * 3, q.y - nz_ * 3)): nx_, nz_ = -nx_, -nz_
                cx, cz = q.x - nx_ * dd / 2, q.y - nz_ * dd / 2            # (its front on the line, its body behind)
                turn = math.degrees(math.atan2(nx_, nz_))
                fp = _rot(box(cx - w / 2, cz - dd / 2, cx + w / 2, cz + dd / 2), -turn, origin=(cx, cz))
                if ok.contains(fp) and all(fp.distance(p) > 5.0 for p in placed):
                    sp(piece, cx, cz, turn, 0.6)
                    placed.append(fp); clear.append(fp.buffer(3.0)); k += 1
                    S.flat("#ddd3a8", list(fp.buffer(3.5, join_style=2).exterior.coords)[:-1], 0.028)
                    for _ in range(crowd * 4):
                        px, pz = q.x + nx_ * rnd.uniform(2, 7) + tx / n * rnd.uniform(-w / 2, w / 2), q.y + nz_ * rnd.uniform(2, 7) + tz / n * rnd.uniform(-w / 2, w / 2)
                        if not S.blocked(px, pz) and turf.distance(Point(px, pz)) > 4.0:
                            S.person(px, 0.0, pz, NM.face(nx_, nz_)); people += 1
                    # a tree or two in the gap beyond it and behind it, so the run is among trees on both sides
                    for _ in range(2):
                        along = (w / 2 + rnd.uniform(3.0, 7.0)) * rnd.choice((-1, 1)); back = rnd.uniform(2.0, dd + 12.0)
                        px, pz = q.x + tx / n * along - nx_ * back, q.y + tz / n * along - nz_ * back
                        if ok.contains(Point(px, pz)): new_trees.append([round(px, 2), round(pz, 2), rnd.choice(("oak_a", "oak_b", "wide_a", "wide_b")), round(rnd.uniform(1.2, 1.7), 2), rnd.randrange(360), 1])
                    s += w / 2 + rnd.uniform(6, 13)
                else:
                    s += 6.0
    cu = unary_union(clear) if clear else None
    kept = [t for t in trees if cu is None or not cu.contains(Point(t[0], t[1]))]
    added = [t for t in new_trees if cu is None or not cu.contains(Point(t[0], t[1]))]
    return kept + added, {"pieces": len(placed), "people": people, "trees taken out": len(trees) - len(kept), "trees added among them": len(added)}
