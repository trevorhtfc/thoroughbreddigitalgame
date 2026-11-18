"""Tier 2 courses: the basic rules for what stands round the track (the same on every course), until each course gets
its own mark-up.

Owner, 18 Nov 2026 (16:12), on Newbury and Doncaster: "Into both of these a very basic rules of planting - advert
boards tracking cams etc". The rules are the ones York, Goodwood and Epsom settled on:

  outside the course   (where the tracking car runs, 12 m beyond the outer rail on the bends, 5 m on the straight)
      boards           a run of the planting kit's boards on the line 20 m off the turf, all the way round, except in
                       front of the stand side (no boards in front of people: owner, 18 Nov 12:11) and the pull-up
      a belt of trees  25 to 55 m off the turf, close-set: it closes every view from the tracking car and the head-on
      thinner trees    55 to 110 m off, more scattered, so the belt doesn't read as a wall from the high cameras;
                       nothing beyond 110 m (only what the cameras see)
  the infield          (what the tracking car looks across the track at)
      boards           a run along the inside rail, 8 m in, round the far side and the bends; not along the run-in
                       (that side is kept for the festival zone opposite the stands, as Ascot, Goodwood and Epsom)
      a belt of trees  30 to 60 m in from the turf, looser than the outside belt, then a few parkland trees deeper in
  the stand side       the plot along the home straight from 150 m past the post to 450 m up the course, out to 260 m,
                       kept clear for the stands (the next phase: the configurator's plots); for now a rail lawn crowd
                       in front of it, 3 to 15 m off the rail, and a belt of trees behind it (260 to 305 m out)
  the run-in infield   opposite the stands: open lawn, kept clear for the festival zone

Counts are kept near or under Ascot's (about 2,000 trees, 23,000 people).
"""
import math, random
import numpy as np
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep

DESIGNS = ["green", "cream", "navy", "white"]
KINDS = ("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")
PARK = ("oak_a", "oak_b", "wide_a", "wide_b")
BOARD_OFF = 20.0
BOARD_GAP = 6.0
BELT = (25.0, 55.0, 10.5, (1.1, 1.55), 0.88)          # from, to (m off the turf), spacing, scale, chance
OUTER = (55.0, 110.0, 17.0, (1.2, 1.7), 0.5)
IN_BOARD = 8.0
IN_BELT = (30.0, 60.0, 13.0, (1.05, 1.5), 0.6)
IN_PARK = (60.0, 2000.0, 48.0, (1.1, 1.6), 0.45)
STAND_PLOT = (-150.0, 450.0, 260.0)                    # x from, x to (up the course), metres beyond the outer rail
RUNIN_DEPTH = 170.0                                    # the run-in's infield kept open for the festival, m in from the rail
LAWN = (3.0, 15.0, -60.0, 320.0, 0.32)                 # rail lawn crowd: m off the rail from, to; x from, to; density


def r2(v): return round(float(v), 2)
def polys(g): return [q for q in getattr(g, "geoms", [g]) if q.geom_type == "Polygon" and not q.is_empty]


def perimeter(S, C, turf, grid_box, rnd=None, opts=None):
    """Adds the basic surroundings to the scene S. C: the race view's course (with 'routes'); turf: the turf (shapely,
    world x, z); grid_box: the ground grid (x0, z0, x1, z1). Returns trees, boards, the stand plot and a note."""
    rnd = rnd or random.Random(23)
    opts = opts or {}                                       # the course's own switches (tools/course/real/<id>.json "perimeter")
    W = C["trackWidth"]; hand = C["hand"]
    side = -1.0 if hand < 0 else 1.0                       # the stand side's z sign (beyond the outer rail)
    trees, boards, note = [], [], {}
    gx0, gz0, gx1, gz1 = grid_box
    inside_grid = box(gx0 + 25, gz0 + 25, gx1 - 25, gz1 - 25)
    holes = sorted([Polygon(h) for h in turf.interiors], key=lambda g: -g.area)
    infield = holes[0] if holes else Polygon()
    outside = Polygon(turf.exterior)
    # the stand plot beyond the outer rail along the home straight, and the run-in's infield opposite it
    x0, x1, depth = STAND_PLOT
    zr = side * (W + 0.5)
    plot = box(x0, min(zr, zr + side * depth), x1, max(zr, zr + side * depth)).difference(turf.buffer(0.5))
    home_d = C["routes"][C["defaultRoute"]]["path"]["home"]
    runin = box(-150.0, min(0.0, -side * RUNIN_DEPTH), home_d + 60.0, max(0.0, -side * RUNIN_DEPTH)).intersection(infield)
    keep_out = unary_union([turf.buffer(22.0), plot])
    pk = prep(keep_out)

    def tree(x, z, sc, belt=None, kinds=KINDS):
        t = [r2(x), r2(z), rnd.choice(kinds), r2(sc), rnd.randrange(360)]
        if belt: t.append(belt)
        trees.append(t)

    def fill(poly, spacing, sc, chance, belt=None, kinds=KINDS):
        n = 0
        for g in polys(poly):
            pg = prep(g); a, b, c, d = g.bounds
            for x in np.arange(a, c, spacing):
                for z in np.arange(b, d, spacing):
                    px, pz = x + rnd.uniform(-0.45, 0.45) * spacing, z + rnd.uniform(-0.45, 0.45) * spacing
                    q = Point(px, pz)
                    if pg.contains(q) and not pk.contains(q) and rnd.random() < chance:
                        tree(px, pz, rnd.uniform(*sc), belt=belt, kinds=kinds); n += 1
        return n

    def face_turf(x, z):
        a, _ = nearest_points(turf, Point(x, z)); fx, fz = a.x - x, a.y - z; l = math.hypot(fx, fz) or 1
        return math.degrees(math.atan2(fx / l, fz / l))

    def board_run(line, skip):
        n = 0
        for seg in getattr(line, "geoms", [line]):
            for s in np.arange(3.0, seg.length - 2.0, BOARD_GAP):
                q = seg.interpolate(s)
                if skip(q) or not inside_grid.contains(q): continue
                boards.append([r2(q.x), r2(q.y), r2(face_turf(q.x, q.y)), DESIGNS[len(boards) % 4], 1.4]); n += 1
        return n

    # ---- outside: the boards on the 20 m line, the belt, the thinner trees
    ring = turf.buffer(BOARD_OFF, join_style=1).exterior
    plot_b = plot.buffer(10)
    pull_up = box(-260.0, min(0.0, side * (W + 140)), -40.0, max(0.0, side * (W + 140)))
    note["boards outside"] = board_run(ring, lambda q: plot_b.contains(q) or pull_up.contains(q))
    around = outside.buffer(BELT[1]).difference(outside.buffer(BELT[0])).difference(plot.buffer(12))
    note["belt trees"] = fill(around, BELT[2], BELT[3], BELT[4], belt=1)
    further = outside.buffer(OUTER[1]).difference(outside.buffer(OUTER[0])).difference(plot.buffer(12)).intersection(inside_grid)
    note["outer trees"] = fill(further, OUTER[2], OUTER[3], OUTER[4])

    # behind the stand plot: a belt closing the view across the stands from the start and the infield cameras
    zb0, zb1 = side * (W + depth), side * (W + depth + 45.0)
    back = box(x0 - 60.0, min(zb0, zb1), x1 + 60.0, max(zb0, zb1)).difference(turf.buffer(25.0))
    note["trees behind the stand plot"] = fill(back, 9.0, (1.2, 1.6), 0.9, belt=1)

    # ---- the infield: boards on the inside rail (not along the run-in), a looser belt, parkland trees
    if not infield.is_empty:
        inner = infield.buffer(-IN_BOARD, join_style=1)
        runin_b = runin.buffer(30)
        if opts.get("infieldBoards", True):              # (off where the TV's tracking car runs in the infield: Doncaster)
            for g in polys(inner):
                note["boards infield"] = note.get("boards infield", 0) + board_run(g.exterior, lambda q: runin_b.contains(q))
        belt_in = infield.buffer(-IN_BELT[0]).difference(infield.buffer(-IN_BELT[1])).difference(runin.buffer(20))
        note["infield belt trees"] = fill(belt_in, IN_BELT[2], IN_BELT[3], IN_BELT[4], belt=1)
        deep = infield.buffer(-IN_PARK[0]).difference(runin.buffer(40))
        note["infield parkland trees"] = fill(deep, IN_PARK[2], IN_PARK[3], IN_PARK[4], kinds=PARK)

    # ---- big hoardings along the run-in's inside rail, facing the stands (both his race videos: Newbury's run of
    # bookmakers' boards along the straight, Doncaster's behind the field coming at the head-on camera); always our own
    # Thoroughbred boards, big, few and evenly spaced (Goodwood's lesson)
    rb = opts.get("runInBoards", {"from": 200.0, "to": 800.0, "every": 40.0, "in": 7.0, "scale": 2.4})
    if rb and not infield.is_empty:
        n = 0
        for x in np.arange(rb["from"], min(rb["to"], home_d - 60.0) + 0.1, rb["every"]):
            from shapely.geometry import LineString as _LS
            cut = infield.intersection(_LS([(x, 0.0), (x, -side * 400.0)]))      # the infield's edge across from x
            if cut.is_empty: continue
            zs = [c[1] for g in getattr(cut, "geoms", [cut]) for c in g.coords]
            z0 = min(zs, key=abs); z = z0 - side * rb["in"]
            if infield.contains(Point(x, z)):
                boards.append([r2(x), r2(z), r2(face_turf(x, z)), DESIGNS[n % 4], rb["scale"]]); n += 1
        note["run-in hoardings"] = n

    # ---- the stands: the course's picks from the grandstand kit (tools/course/real/<id>.json "stands"), on one front line
    # 'front' metres back from the outer rail (each piece set back a further 'back' m), facing the track, their crowds in
    st = opts.get("stands")
    if st:
        info, model = opts["standsInfo"], opts["standsModel"]
        zr = side * (W + 0.5)
        lawn_x = [1e9, -1e9]
        aprons = []
        # joined stands share one level (owner, 22:27, Newbury: "3, 4 and 5 need aligning neatly"; each piece had stood
        # at the ground's height under its own origin, so the joined modules stepped): "level": [[piece indices], ...],
        # each group at the middle of the ground's range under its pieces' fronts (the buildings' plinths go 1 m below
        # their floors, so up to 2 m of fall along a run is covered at both ends)
        LEVEL = {}
        for grp in st.get("level", []):
            hs = []
            for i in grp:
                e = st["pieces"][i]
                if isinstance(e, dict):                      # a hand-placed piece: the ground at its origin
                    hs.append(S.G(*e["at"])); continue
                gi = info[e[0]]; gz = zr + side * (st.get("front", 17.0) + e[2])
                hw = gi["width"] / 2; ox = e[1] + gi.get("offset", 0.0)
                hs += [S.G(xx, gz) for xx in np.linspace(ox - hw, ox + hw, 9)]
            lv = (max(hs) + min(hs)) / 2
            for i in grp: LEVEL[i] = lv
            note.setdefault("levels", []).append([grp, r2(lv), r2(max(hs) - min(hs))])
        for ei, e in enumerate(st["pieces"]):
            if isinstance(e, dict):
                # a piece placed by hand (owner's mark-up): 'at' a seed point and 'turn'; with 'toTurf' it is slid along the
                # way it faces until the middle of its front is that far from the turf (the stand at the bend, turned to it)
                piece, dens, turn = e["piece"], e.get("dens", 0.5), e.get("turn", 0.0)
                gi = info[piece]; x, gz = e["at"]
                if "toTurf" in e:
                    fx, fz = math.sin(math.radians(turn)), math.cos(math.radians(turn))
                    for _ in range(400):
                        dd = turf.distance(Point(x, gz))
                        if abs(dd - e["toTurf"]) < 0.3: break
                        step = (dd - e["toTurf"]) * 0.5
                        x, gz = x + fx * step, gz + fz * step
                S.piece(model, piece, x, gz, turn, y=LEVEL.get(ei))
                S.stand_people(gi, x, gz, turn, 1.0, 1.0, dens, g=LEVEL.get(ei))
                S.footprint(gi, x, gz, turn)
                note.setdefault("placed by hand", []).append([piece, r2(x), r2(gz), turn, "turf gap", r2(turf.distance(Polygon(S.nogo[-1])))])
                if st.get("walkUnderHandPlaced"):           # the paved walk and the rail lawn run along these too (Newbury)
                    bx0, _, bx1, _ = Polygon(S.nogo[-1]).bounds
                    lawn_x = [min(lawn_x[0], bx0), max(lawn_x[1], bx1)]
                # clear the ground between it and the turf (owner, 19:15: the tiered stand tucked into the bend, where the
                # bend's belt trees would stand in front of it): no trees there, a paved apron to the rail
                from shapely.affinity import translate as _tr
                fx, fz = math.sin(math.radians(turn)), math.cos(math.radians(turn))
                fp = Polygon(S.nogo[-1])
                ahead = unary_union([fp, _tr(fp, fx * e.get("apron", 14.0), fz * e.get("apron", 14.0))]).convex_hull
                clear = prep(ahead.buffer(6.0)); aprons.append(ahead.buffer(6.0))
                wide = prep(unary_union([fp, _tr(fp, fx * 60.0, fz * 60.0)]).convex_hull.buffer(10.0))
                nb = len(boards); boards[:] = [b for b in boards if not wide.contains(Point(b[0], b[1]))]
                note["boards cleared for the hand-placed stands"] = note.get("boards cleared for the hand-placed stands", 0) + nb - len(boards)
                n0 = len(trees); trees[:] = [t for t in trees if not clear.contains(Point(t[0], t[1]))]
                note["trees cleared for the hand-placed stands"] = note.get("trees cleared for the hand-placed stands", 0) + n0 - len(trees)
                apron = ahead.difference(fp).difference(turf.buffer(0.5))
                for g in polys(apron):
                    S.flat("#e4d8c2", [(r2(a), r2(b)) for a, b in g.exterior.coords[:-1]], 0.03)
                continue
            piece, x, back, dens = e
            gi = info[piece]
            gz = zr + side * (st.get("front", 17.0) + back)             # the stand's foot
            turn = 0.0 if side < 0 else 180.0
            S.piece(model, piece, x, gz, turn, y=LEVEL.get(ei))
            S.stand_people(gi, x, gz, turn, 1.0, 1.0, dens, g=LEVEL.get(ei))
            S.footprint(gi, x + gi.get("offset", 0.0) * (1 if side < 0 else -1), gz, turn)
            ox = x + gi.get("offset", 0.0); hw = gi["width"] / 2
            lawn_x = [min(lawn_x[0], ox - hw), max(lawn_x[1], ox + hw)]
        note["stands"] = len(st["pieces"]); note["stand people"] = (len(S.people) - 0) // 4
        # the paved walk along the stands' feet
        za, zb = zr + side * 1.0, zr + side * (st.get("front", 17.0) - 0.5)
        S.flat("#e4d8c2", [(lawn_x[0], za), (lawn_x[1], za), (lawn_x[1], zb), (lawn_x[0], zb)], 0.03)
        LAWN_X = (lawn_x[0], lawn_x[1])
    else:
        LAWN_X = None

    # ---- rows of trees behind the stands (owner's mark-up, 19:10: a line of trees drawn behind the stand side)
    for row in opts.get("backTrees", []):
        n = 0
        for x in np.arange(row["x"][0], row["x"][1] + 0.1, row.get("every", 10.0)):
            for k, zz in enumerate(row["z"]):
                xx = x + (row.get("every", 10.0) / 2 if k % 2 else 0) + rnd.uniform(-1.5, 1.5)
                if not S.blocked(xx, zz):
                    tree(xx, zz + rnd.uniform(-1.5, 1.5), rnd.uniform(*row.get("scale", (1.25, 1.6))), belt=1); n += 1
        note["trees behind the stands"] = note.get("trees behind the stands", 0) + n

    # ---- trees filling the gaps round the stands (owner, 19:26: "fill the gaps with trees", either side of the stand at the
    # bend): a region given in the course's file, less the turf, the stands, their aprons and the walk
    for gt in opts.get("gapTrees", []):
        g = Polygon(gt["poly"]).difference(turf.buffer(gt.get("offTurf", 12.0)))
        for ap in (aprons if st else []): g = g.difference(ap)
        n = 0
        for gg in polys(g):
            pg = prep(gg); a_, b_, c_, d_ = gg.bounds; sp_ = gt.get("every", 8.0)
            for x in np.arange(a_, c_, sp_):
                for z in np.arange(b_, d_, sp_):
                    px, pz = x + rnd.uniform(-0.4, 0.4) * sp_, z + rnd.uniform(-0.4, 0.4) * sp_
                    if pg.contains(Point(px, pz)) and not S.blocked(px, pz) and rnd.random() < gt.get("chance", 0.9):
                        tree(px, pz, rnd.uniform(*gt.get("scale", (1.2, 1.6))), belt=1); n += 1
        note["gap trees"] = note.get("gap trees", 0) + n

    # ---- festival zones (owner's mark-up, 19:10: one in the infield along the run-in, one on the stand side up the
    # course): the site props kit on trodden ground (marquees, big tops, balloon pods, little stands, kiosks, pergolas,
    # picnic tables, flags), each with its own people, then a crowd through it
    if opts.get("festivals"):
        import json as _json
        from pathlib import Path as _P
        spots = _json.loads((_P(__file__).resolve().parents[3] / "assets/models/architecture/site_props_spots.json").read_text())["pieces"]
        import sys as _sys
        _sys.path.insert(0, str(_P(__file__).resolve().parents[1] / "newmarket"))
        import to_race_view as _NM
        placed = []
        def sp(piece, x, z, turn, people=0.6, sc=1.0):
            S.piece("site_props", piece, x, z, turn, 1.0, sc)
            w, dd = _NM.SP_SIZE[piece]; ca_, sa_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
            hw, hd = w / 2 * sc + 0.5, dd / 2 * sc + 0.5
            S.nogo.append([(x + u * ca_ + v * sa_, z - u * sa_ + v * ca_) for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))])
            for kind in ("seats", "stand"):
                for lx, ly, lz in spots.get(piece, {}).get(kind, []):
                    if rnd.random() < people:
                        lx, ly, lz = lx * sc, ly * sc, lz * sc
                        S.person(x + lx * ca_ - ly * sa_, lz, z - (lx * sa_ + ly * ca_), round(rnd.uniform(-3.14, 3.14), 2))
        KIT = {"infield": [("marquee_peaks", 2.5, 13.0), ("big_top", 0.8, 11.0), ("marquee_clearspan", 1.5, 11.0), ("balloon_pod", 1.2, 4.0),
                           ("stand_open", 1.0, 8.5), ("stand_covered", 0.8, 7.0), ("kiosk_awning", 3.0, 3.5), ("pagoda_kiosk", 2.5, 3.0),
                           ("pergola_picnic", 2.0, 5.0), ("picnic_table", 6.0, 1.5), ("banner_flag", 6.0, 1.0), ("terrace_deck", 1.0, 6.0)],
               "standside": [("marquee_peaks", 3.0, 13.0), ("marquee_clearspan", 2.0, 11.0), ("pergola_picnic", 2.0, 5.0), ("terrace_deck", 1.5, 6.0),
                             ("kiosk_row_arched", 1.2, 6.0), ("pagoda_kiosk", 2.0, 3.0), ("picnic_table", 6.0, 1.5), ("flagpole", 4.0, 1.0),
                             ("planter_long", 4.0, 2.5)],
               # (owner, 22:27, Newbury: "more festival bits and pieces between stands"): small things for the gaps
               "gaps": [("kiosk_awning", 14.0, 3.5), ("pagoda_kiosk", 12.0, 3.0), ("pergola_picnic", 8.0, 5.0),
                        ("picnic_table", 30.0, 1.5), ("flagpole", 16.0, 1.0), ("planter_long", 14.0, 2.5), ("banner_flag", 14.0, 1.0)]}
        for fz_ in opts["festivals"]:
            g = Polygon(fz_["poly"]).buffer(0)
            g = g.difference(turf.buffer(fz_.get("offTurf", 10.0)))
            for b in boards:
                if b[4] > 1.5: g = g.difference(Point(b[0], b[1]).buffer(8.0))
            res = {"pieces": 0, "people": 0}
            raw = Polygon(fz_["poly"]).buffer(0)
            # the crowd on the rail along the zone's track side (owner, 19:26: "add more crowd to the rail")
            rc = fz_.get("railCrowd")
            if rc:
                strip = raw.intersection(turf.buffer(rc.get("to", 7.0))).difference(turf.buffer(rc.get("from", 1.5)))
                a_, b_, c_, d_ = strip.bounds if not strip.is_empty else (0, 0, 0, 0)
                ps = prep(strip); n = 0
                for x, z in S.spots(a_, c_, b_, d_, rc.get("dens", 0.6)):
                    if ps.contains(Point(x, z)) and not S.blocked(x, z):
                        S.person(x, 0.0, z, round(face_turf(x, z) * math.pi / 180.0 + math.pi + rnd.uniform(-0.5, 0.5), 2)); n += 1
                res["rail crowd"] = n
            # balloon pods in rows of five along the track edge (owner, 19:26)
            br = fz_.get("balloonRows")
            if br:
                from shapely.geometry import LineString as _LS
                xa_, _, xb_, _ = g.bounds; nrow = 0
                for xc in np.arange(xa_ + br.get("start", 40.0), xb_ - br.get("end", 40.0) + 0.1, br.get("every", 120.0)):
                    row = []
                    for k in range(br.get("n", 5)):
                        x = xc + (k - (br.get("n", 5) - 1) / 2) * br.get("gap", 10.0)
                        cut = g.intersection(_LS([(x, -2000.0), (x, 2000.0)]))
                        if cut.is_empty: break
                        zs = [c[1] for gm in getattr(cut, "geoms", [cut]) for c in gm.coords]
                        z0 = min(zs, key=lambda zz: turf.distance(Point(x, zz)))
                        z = z0 + (1 if raw.contains(Point(x, z0 + 1)) else -1) * br.get("in", 6.0)
                        if not g.contains(Point(x, z)): break
                        row.append((x, z))
                    if len(row) == br.get("n", 5):
                        for x, z in row:
                            sp("balloon_pod", x, z, rnd.uniform(0, 360), 0.6); placed.append((x, z, 4.0)); res["pieces"] += 1
                        nrow += 1
                res["balloon rows"] = nrow
            for gg in polys(g):
                if gg.area < fz_.get("minArea", 800): continue
                S.flat("#d8d0a2", list(gg.simplify(1.0).exterior.coords)[:-1], 0.028)
                x0_, z0_, x1_, z1_ = gg.bounds; per = gg.area / 10000.0
                def ok(x, z, r):
                    return gg.buffer(-r).contains(Point(x, z)) and all(math.hypot(x - a, z - b) > r + rb + 3 for a, b, rb in placed) and not S.blocked(x, z)
                face_track = 0.0 if side < 0 else 180.0                  # the stand side's props face the track
                for piece, c, r in KIT[fz_.get("kit", "infield")]:
                    if piece == "balloon_pod" and fz_.get("balloonRows"): continue
                    for _ in range(max(1, int(round(c * per)))):
                        for _try in range(300):
                            x, z = rnd.uniform(x0_, x1_), rnd.uniform(z0_, z1_)
                            if ok(x, z, r):
                                sc = rnd.uniform(0.9, 1.2) if piece in ("marquee_peaks", "marquee_clearspan", "big_top") else 1.0
                                if piece in ("big_top", "balloon_pod"): turn = rnd.uniform(0, 360)
                                elif fz_.get("kit") == "standside": turn = face_track + rnd.choice([0, 0, 0, 90, -90])
                                else: turn = (180.0 if side < 0 else 0.0) + rnd.choice([0, 0, 0, 90, -90])   # the infield's face the stands
                                sp(piece, x, z, turn, 0.6, sc); placed.append((x, z, r * sc)); res["pieces"] += 1; break
                for _ in range(int(gg.area * fz_.get("dens", 0.035))):
                    x, z = rnd.uniform(x0_, x1_), rnd.uniform(z0_, z1_)
                    if gg.contains(Point(x, z)) and not S.blocked(x, z):
                        S.person(x, 0.0, z, round(rnd.uniform(-3.14, 3.14), 2)); res["people"] += 1
                res["area m2"] = res.get("area m2", 0) + round(gg.area)
            note.setdefault("festivals", {})[fz_.get("name", "festival")] = res

    # ---- the rail lawn's crowd in front of the stand plot
    p0 = len(S.people)
    a, b, xa, xb, dens = LAWN
    dens = opts.get("lawnDens", dens)
    if LAWN_X: xa, xb = LAWN_X
    if opts.get("lawnX"): xa, xb = opts["lawnX"]              # (Newbury: the lawn runs on past the stands to his area 4)
    if opts.get("lawnDepth"): a, b = opts["lawnDepth"]        # (Newbury: stands set back, the lawn deep in front of them)
    z_a, z_b = side * (W + 0.5 + a), side * (W + 0.5 + b)
    for x, z in S.spots(xa, xb, min(z_a, z_b), max(z_a, z_b), dens):
        if not turf.buffer(2.0).contains(Point(x, z)) and not S.blocked(x, z):
            S.person(x, 0.0, z, round((math.pi if side < 0 else 0.0) + rnd.uniform(-0.5, 0.5), 2))
    note["rail lawn crowd"] = (len(S.people) - p0) // 4
    note["trees"], note["boards"] = len(trees), len(boards)
    return trees, boards, plot, note
