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


def perimeter(S, C, turf, grid_box, rnd=None):
    """Adds the basic surroundings to the scene S. C: the race view's course (with 'routes'); turf: the turf (shapely,
    world x, z); grid_box: the ground grid (x0, z0, x1, z1). Returns trees, boards, the stand plot and a note."""
    rnd = rnd or random.Random(23)
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
        for g in polys(inner):
            note["boards infield"] = note.get("boards infield", 0) + board_run(g.exterior, lambda q: runin_b.contains(q))
        belt_in = infield.buffer(-IN_BELT[0]).difference(infield.buffer(-IN_BELT[1])).difference(runin.buffer(20))
        note["infield belt trees"] = fill(belt_in, IN_BELT[2], IN_BELT[3], IN_BELT[4], belt=1)
        deep = infield.buffer(-IN_PARK[0]).difference(runin.buffer(40))
        note["infield parkland trees"] = fill(deep, IN_PARK[2], IN_PARK[3], IN_PARK[4], kinds=PARK)

    # ---- the rail lawn's crowd in front of the stand plot (the stands themselves come next)
    p0 = len(S.people)
    a, b, xa, xb, dens = LAWN
    z_a, z_b = side * (W + 0.5 + a), side * (W + 0.5 + b)
    for x, z in S.spots(xa, xb, min(z_a, z_b), max(z_a, z_b), dens):
        if not turf.buffer(2.0).contains(Point(x, z)):
            S.person(x, 0.0, z, round((math.pi if side < 0 else 0.0) + rnd.uniform(-0.5, 0.5), 2))
    note["rail lawn crowd"] = (len(S.people) - p0) // 4
    note["trees"], note["boards"] = len(trees), len(boards)
    return trees, boards, plot, note
