"""Sandown's own edges for the race view: the band of bushes along the far side of the sprint course (owner, 19 Nov 13:28:
"emphasise the bushes on the far side of the sprint course"; his Google Maps views show a dark line of bushes along the
golf course side of the sprint strip). Called by to_race_view.py ("edges": {"script": "edges_sandown", ...}).

From the sprint course's inside rail (its far side, the golf course) outwards:
  a clipped hedge in long runs with the odd gap (dressed with leaf tufts in the soft look), then three staggered rows of
  bushes (light crowns only, belt 2), then a loose row of trees for height, so the band reads as a deep green wall behind
  the field from the cameras on the festival side. It stops short of where the sprint crosses the round course in the
  far bend, and the golf course's scattered trees are cleared from in front of and inside it.
"""
import math
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from shapely.prepared import prep

HEDGE = "#5b7f4c"
BUSH_KINDS = ("oak_b", "oak_c", "wide_a", "wide_b")
TREE_KINDS = ("oak_a", "oak_b", "wide_a", "wide_b")


def build(S, LY, course, turf, trees, boards, opts, NM, rnd):
    W = course["trackWidth"]; note = {}
    R = course["routes"]["straight"]["pathRail"]; P = R["points"]; d0, sp = R["d0"], R["spacing"]

    def at(d, off):
        """the point 'off' metres from the sprint's inside rail at d metres to go (+ across the track, - the far side),
        and the running direction"""
        f = (d - d0) / sp; i = max(1, min(len(P) - 2, int(f))); k = f - i
        a, b = P[i], P[i + 1]
        x, z = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        p0, p1 = P[i - 1], P[i + 1]; tx, tz = p0[0] - p1[0], p0[1] - p1[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        ax, az = tz, -tx                                     # right-handed: across the track
        return x + ax * off, z + az * off, tx, tz

    # the round course's own turf: the band stops 14 m short of it (the sprint crosses it in the far bend)
    rr = course["routes"]["round"]["pathRail"]["points"]
    round_turf = LineString(rr).buffer(W + 1.0, single_sided=False)
    stop = prep(round_turf.buffer(14.0))
    d_a, d_b = opts.get("from", -70.0), opts.get("to", 1040.0)

    # clear the golf course's scattered trees from the band and in front of it
    band = Polygon([at(d, -2.0)[:2] for d in np.arange(d_a, d_b, 10.0)] + [at(d, -44.0)[:2] for d in np.arange(d_b, d_a, -10.0)]).buffer(0)
    bp = prep(band); n0 = len(trees)
    trees[:] = [t for t in trees if not bp.contains(Point(t[0], t[1]))]
    note["trees cleared from the band"] = n0 - len(trees)

    # the clipped hedge (his 5f video: big dark hedges behind the far rail, clumps of bushes between): runs of two to five
    # 12 m lengths, then a gap of 5 to 14 m with a clump of bushes in it
    H = opts.get("hedge", {"off": 10.5, "depth": 2.6, "height": 2.1})
    n = 0; d = d_a; left = rnd.randint(2, 5)
    while d < d_b:
        x, z, tx, tz = at(d + 6.0, -H["off"])
        if not stop.contains(Point(x, z)):
            S.box(HEDGE, x, z, 12.2, H["depth"], -0.4, H["height"] + 0.25 * math.sin(d * 0.07), math.atan2(-tz, tx)); n += 1
        d += 12.0; left -= 1
        if left == 0:
            gap = rnd.uniform(5.0, 14.0)
            for k in range(int(gap // 4.5) + 1):
                bx, bz, _, _ = at(d + 2.0 + k * 4.5, -(H["off"] + rnd.uniform(-1.0, 1.5)))
                if not stop.contains(Point(bx, bz)):
                    trees.append([round(bx, 2), round(bz, 2), rnd.choice(BUSH_KINDS), round(rnd.uniform(0.4, 0.55), 2), rnd.randrange(360), 2])
            d += gap; left = rnd.randint(2, 5)
    note["hedge runs"] = n

    # three staggered rows of bushes behind the hedge, then a loose row of trees
    nb = nt = 0
    for row, (off, every, sc) in enumerate(opts.get("bushes", [[14.5, 5.0, [0.42, 0.6]], [19.0, 5.5, [0.48, 0.7]], [23.5, 6.0, [0.52, 0.78]]])):
        for d in np.arange(d_a + row * 2.0, d_b, every):
            if rnd.random() > 0.92: continue
            x, z, _, _ = at(d + rnd.uniform(-1.5, 1.5), -(off + rnd.uniform(-1.4, 1.4)))
            if stop.contains(Point(x, z)) or S.blocked(x, z): continue
            trees.append([round(x, 2), round(z, 2), rnd.choice(BUSH_KINDS), round(rnd.uniform(*sc), 2), rnd.randrange(360), 2]); nb += 1
    for d in np.arange(d_a + 5.0, d_b, opts.get("treeEvery", 16.0)):
        if rnd.random() > 0.7: continue
        x, z, _, _ = at(d + rnd.uniform(-4, 4), -rnd.uniform(29.0, 38.0))
        if stop.contains(Point(x, z)) or S.blocked(x, z): continue
        trees.append([round(x, 2), round(z, 2), rnd.choice(TREE_KINDS), round(rnd.uniform(0.95, 1.4), 2), rnd.randrange(360), 1]); nt += 1
    note["bushes"], note["trees behind them"] = nb, nt

    # chase fences on the jumps course inside the round course (his video, 110-120 s: the field coming at the camera over
    # the top of a fence): birch packed in a frame, a white take-off rail, white wings; 'fences' are metres to go on the
    # round course, each 15 m inside its inside rail
    RR = course["routes"]["round"]["pathRail"]; RP = RR["points"]; nf = 0
    for dd in opts.get("fences", []):
        f = (dd - RR["d0"]) / RR["spacing"]; i = max(1, min(len(RP) - 2, int(f)))
        p0, p1 = RP[i - 1], RP[i + 1]; tx, tz = p0[0] - p1[0], p0[1] - p1[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        ax, az = tz, -tx
        cx, cz = RP[i][0] - ax * 15.0, RP[i][1] - az * 15.0
        yaw = math.atan2(-az, ax)                            # the fence runs across the jumps course (along 'across')
        S.box("#6e5a45", cx, cz, 14.0, 1.6, -0.3, 1.38, yaw)
        S.box("#7d6a52", cx, cz, 14.0, 1.1, 1.38, 1.5, yaw)
        S.box("#f2eee5", cx + tx * 0.95, cz + tz * 0.95, 14.0, 0.25, 0.0, 0.42, yaw)
        for s_ in (-1, 1):
            S.box("#f2eee5", cx + ax * s_ * 7.6, cz + az * s_ * 7.6, 1.4, 2.6, 0.0, 2.0, yaw)
        nf += 1
    note["chase fences"] = nf

    # big boards along the far rail at the sprint's finish, in front of the hedge (his video, 59 s: the boards behind the post)
    fb = opts.get("finishBoards"); nfb = 0
    if fb:
        for dd in np.arange(fb["from"], fb["to"] + 0.1, fb["every"]):
            x, z, tx, tz = at(dd, -fb["off"])
            ax, az = tz, -tx
            boards.append([round(x, 2), round(z, 2), round(math.degrees(math.atan2(ax, az)), 2), ("green", "cream", "navy", "white")[nfb % 4], fb.get("scale", 2.4)]); nfb += 1
    note["finish boards"] = nfb
    return note
