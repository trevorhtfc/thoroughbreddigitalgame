"""Chester's urban edges for the race view (owner, 18 Nov 2026): the city walls with their built-in terraces along the home
straight, the plain walls and the castle's, and the first row of the city beyond them, from OpenStreetMap
(reference/chester/osm-edges.json, (c) OpenStreetMap contributors, ODbL). Called by to_race_view.py when the course file
names it ("edges": {"script": "edges_chester", ...}).

Owner: 21:44 "1/2 the edges bound by roman walls, railway viaducts, and the edge of the city ... focusing on the tv tracking
and key place making views"; 21:5x "its about creating edges for key views"; 22:08 "we deffo dont need anything that sits
to the left of the viaduct"; 22:11 "there are some really cool terraces built into the walls that would be great to
replicate in some fashion"; 22:39 "yep go for it".

Everything is built from the scene's coloured boxes (walls, buttresses, steps, buildings) and its people, so no new model
file is needed:
  - the wall along Nun's Road: a red sandstone wall with a walkway and parapet on top; along the stretch the cameras see
    past the stands, bays between deep buttresses, each bay a flight of terraces stepping up to the walkway, packed with
    people, and a crowd along the top
  - the other walls (the castle's): plain wall
  - the buildings beyond the walls: boxes on their OSM footprints (their minimum rectangles), brick or render, a darker
    roof slab, heights from OSM or about three storeys
  - the outside's placeholder trees and boards cleared where the city stands
"""
import json, math
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.prepared import prep

REPO = Path(__file__).resolve().parents[3]

STONE, STONE_LIT, COPING = "#c4836b", "#d29a83", "#ddb19a"           # red sandstone, its steps, the coping
BRICKS = ["#c98a72", "#b97862", "#d39b80", "#bf846f", "#e2c7ad"]       # the city's brick and the odd rendered front
ROOFS = ["#8c6e66", "#7e7a86", "#956f62"]


def build(S, LY, course, turf, trees, boards, opts, NM, rnd):
    """Adds the edges to the scene S and clears the placeholder trees and boards where the city stands. LY: the layout's
    Course (OSM's metres to the race view's world: LY.world). Returns a note."""
    E = json.loads((REPO / "reference/chester/osm-edges.json").read_text())["features"]
    W = lambda pts: np.array([LY.world(q) for q in pts], float)
    note = {}
    infield = Polygon(course["track"]["surface"][1]) if len(course["track"]["surface"]) > 1 else Polygon()
    turf_b = turf.buffer(3.0)

    # ---- clear the placeholder belt and boards where the city is (the course file's "clear": world boxes)
    clear = [box(*b) for b in opts.get("clear", [])]
    def in_clear(x, z):
        p = Point(x, z)
        return any(c.contains(p) for c in clear) and not infield.contains(p)
    n0, b0 = len(trees), len(boards)
    trees[:] = [t for t in trees if not in_clear(t[0], t[1])]
    boards[:] = [b for b in boards if not in_clear(b[0], b[1])]
    note["trees cleared"], note["boards cleared"] = n0 - len(trees), b0 - len(boards)

    # ---- the walls
    walls = [W(f["p"]) for f in E if f["kind"] == "wall"]
    main_w = opts.get("mainWall", {})
    terr = main_w.get("terraces", [80.0, 290.0])        # the stretch with the built-in terraces (x up the straight)
    bay = main_w.get("bay", 8.0); top_h = main_w.get("height", 6.5)
    people = 0; n_bays = 0; n_terr = 0

    def toward_track(p, t):
        n = np.array([-t[1], t[0]])
        a, b = Point(*(p + n * 5)), Point(*(p - n * 5))
        return n if turf.distance(a) < turf.distance(b) else -n

    def yaw(t): return math.atan2(-t[1], t[0])

    keep = [w for w in walls if LineString(w).length > 15 and any(in_clear(x, z) for x, z in w)]
    for w in keep:
        line = LineString(w)
        if line.length < 15: continue
        L = line.length
        for s in np.arange(bay / 2, L - bay / 2 + 1e-6, bay):
            p0 = np.array(line.interpolate(s - bay / 2).coords[0]); p1 = np.array(line.interpolate(s + bay / 2).coords[0])
            p = (p0 + p1) / 2; t = p1 - p0; t /= (np.hypot(*t) or 1)
            if turf_b.contains(Point(*p)): continue
            n = toward_track(p, t)
            g = S.G(*(p + n * 2.0))                      # the ground at the wall's foot, track side
            gt = S.G(*p)
            top = max(g, gt) + top_h                      # the walkway's level
            # the wall (2.6 m thick), the walkway paving on it, the parapet on the track side
            S.box(STONE, p[0], p[1], bay + 0.05, 2.6, g - gt - 1.0, top - gt, yaw(t))
            q = p + n * 1.1
            S.box(COPING, q[0], q[1], bay + 0.05, 0.45, top - S.G(*q), top + 0.95 - S.G(*q), yaw(t))
            n_bays += 1
            # a few people walking the walls everywhere
            for k in range(2):
                if rnd.random() < 0.55:
                    u = rnd.uniform(-bay / 2, bay / 2); v = rnd.uniform(-0.6, 0.6)
                    x, z = p + t * u + n * v
                    S.person(x, 0.0, z, NM.face(*n) + rnd.uniform(-0.6, 0.6), top); people += 1
            on_terr = terr[0] <= p[0] <= terr[1] and abs(p[1]) < 140
            if not on_terr: continue
            n_terr += 1
            # the buttress at the bay's end: deep at the foot, its upper part half as deep (a stepped slope)
            for frac, h_to, depth in ((0.5, top - 2.2, 6.2), (0.5, top - 0.4, 3.0)):
                c = p + t * (bay / 2 - 0.7) + n * (1.3 + depth / 2)
                S.box(STONE, c[0], c[1], 1.4, depth, g - S.G(*c) - 0.5, h_to - S.G(*c), yaw(t))
            # the terraces between the buttresses: four steps up to the walkway, each 1.3 m deep
            nsteps = 4; rise = (top - 0.4 - g) / (nsteps + 0.3); width = bay - 1.4
            mid = p - t * 0.7
            for k in range(nsteps):
                depth = (nsteps - k) * 1.3
                c = mid + n * (1.3 + depth / 2)
                y1 = g + (k + 1) * rise
                S.box(STONE_LIT, c[0], c[1], width, depth, g - S.G(*c) - 0.5, y1 - S.G(*c), yaw(t))
                # the people on this step's tread, in a packed row (two where the tread is deep enough)
                tread = mid + n * (1.3 + depth - 0.65)
                for u in np.arange(-width / 2 + 0.35, width / 2 - 0.3, 0.62):
                    for row in (0.0,):
                        if rnd.random() < opts.get("terraceDens", 0.85):
                            x, z = tread + t * (u + rnd.uniform(-0.12, 0.12)) + n * (row + rnd.uniform(-0.15, 0.15))
                            S.person(x, 0.0, z, NM.face(*n) + rnd.uniform(-0.35, 0.35), y1); people += 1
            # the walkway on top above the terraces: packed
            for u in np.arange(-bay / 2 + 0.4, bay / 2, 0.6):
                for v in (-0.2, 0.5):
                    if rnd.random() < 0.7:
                        x, z = p + t * u + n * (v + rnd.uniform(-0.1, 0.1))
                        S.person(x, 0.0, z, NM.face(*n) + rnd.uniform(-0.4, 0.4), top); people += 1
    note["wall bays"], note["terrace bays"], note["people on the walls"] = n_bays, n_terr, people

    # ---- the city beyond: the OSM buildings in the cleared area, beyond the main wall from the track
    nb = 0
    main = max(keep, key=lambda w: LineString(w).length) if keep else None
    stand_box = [Polygon(q) for q in S.nogo]
    for f in E:
        if f["kind"] != "b" or "p" not in f: continue
        P = Polygon(W(f["p"])).buffer(0)
        if P.is_empty or P.area < 30: continue
        cx, cz = P.centroid.x, P.centroid.y
        if not in_clear(cx, cz) or infield.contains(Point(cx, cz)) or P.distance(turf) < 4.0: continue
        if any(P.intersects(q) for q in stand_box): continue
        if main is not None and opts.get("beyondWallOnly", True):
            # beyond the wall: further from the track than the wall's nearest point
            ml = LineString(main); a = ml.interpolate(ml.project(Point(cx, cz)))
            if turf.distance(Point(cx, cz)) < turf.distance(a) + 2.0 and ml.distance(Point(cx, cz)) < 400: continue
        tg = f["tags"]
        h = float(tg["height"]) if "height" in tg else (float(tg["building:levels"]) * 3.2 + 1.5 if "building:levels" in tg else rnd.choice([9.5, 11.0, 12.5]))
        mr = P.minimum_rotated_rectangle
        xy = np.array(mr.exterior.coords)[:4]
        e0, e1 = xy[1] - xy[0], xy[2] - xy[1]
        L0, L1 = np.hypot(*e0), np.hypot(*e1)
        ax = e0 / L0 if L0 >= L1 else e1 / L1
        c = xy.mean(0); g = S.G(*c)
        col = rnd.choice(BRICKS)
        S.box(col, c[0], c[1], max(L0, L1), min(L0, L1), -1.0, h, math.atan2(-ax[1], ax[0]))
        S.box(rnd.choice(ROOFS), c[0], c[1], max(L0, L1) - 0.6, min(L0, L1) - 0.6, h, h + 0.7, math.atan2(-ax[1], ax[0]))
        nb += 1
    note["city buildings"] = nb
    return note
