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

    # ---- the walls and the city, from the modelled pieces (owner, 23:20 "make detailed models from the photos"; 00:04 his
    # wall terraces sheet; 00:39 "embed this into the course"): tools/blender/build_chester_stands.py, merged into
    # chester_stands by merge_stands.py ("extra" in the course file's stands). Each wall piece's origin is on the wall's
    # face, its front (the steps) towards the track.
    INFO = json.loads((REPO / "assets/models/architecture/chester_stands.json").read_text())["pieces"]
    MODEL = "chester_stands"
    walls = [W(f["p"]) for f in E if f["kind"] == "wall"]
    walls = [w for w in walls if LineString(w).length > 15 and any(in_clear(x, z) for x, z in w)]
    # the wall along the home straight (Nun's Road): the one with the most length close to the track
    def near_len(w):
        ln = LineString(w); return sum(1.0 for d_ in np.arange(0, ln.length, 1.0) if turf.distance(ln.interpolate(d_)) < 70.0)
    main = max(walls, key=near_len) if walls else None
    mw = opts.get("mainWall", {})
    people0 = len(S.people)

    def frame(line, s0, s1):
        """the middle of the stretch s0..s1 of a wall line, the direction along it, and the normal towards the track"""
        a_ = np.array(line.interpolate(s0).coords[0]); b_ = np.array(line.interpolate(s1).coords[0])
        t = b_ - a_; t /= (np.hypot(*t) or 1); m = (a_ + b_) / 2
        n = np.array([-t[1], t[0]])
        if turf.distance(Point(*(m + n * 6))) > turf.distance(Point(*(m - n * 6))): n = -n
        return m, t, n

    def place(piece, m, n, dens, front=0.0):
        """a piece with its origin at m, its front looking along n; set at the ground of its front (it digs into the bank)"""
        gi = INFO[piece]
        turn = math.degrees(math.atan2(n[0], n[1]))
        fr = m + n * (-gi.get("frontAt", 0.0))
        y = min(S.G(*m), S.G(*fr))
        S.piece(MODEL, piece, m[0], m[1], turn, y=y)
        if gi.get("crowd") and dens > 0:
            S.stand_people(gi, m[0], m[1], turn, 1.0, 1.0, dens, g=y)
        return turn

    n_mod = 0
    if main is not None:
        line = LineString(main)
        if line.coords[0][0] > line.coords[-1][0]: line = LineString(list(line.coords)[::-1])     # run it up the straight
        L = line.length
        # the terraces: from where the stands end, in the owner's order, then plain wall to the end
        start_x = mw.get("terracesFrom", 132.0)
        s0 = next((s_ for s_ in np.arange(0, L, 1.0) if line.interpolate(s_).x >= start_x), L)
        seq = mw.get("sequence", ["chester_wt_tower", "chester_wt_stand", "chester_wt_steps", "chester_wt_steps_rail",
                                  "chester_wt_stand_lantern", "chester_wt_steps", "chester_wt_steps_rail", "chester_wt_taper"])
        s_ = s0
        for piece in seq:
            w = INFO[piece]["width"]
            if s_ + w > L: break
            m, t, n = frame(line, s_, s_ + w)
            place(piece, m, n, opts.get("terraceDens", 1.5)); n_mod += 1
            # keep the lawn crowd and trees out of its steps
            S.nogo.append([tuple(m - t * w / 2), tuple(m + t * w / 2), tuple(m + t * w / 2 + n * (-INFO[piece].get("frontAt", 0.0) + 1)),
                           tuple(m - t * w / 2 + n * (-INFO[piece].get("frontAt", 0.0) + 1))])
            s_ += w
        # plain wall before the terraces (behind the stands) and after them
        bay = INFO["chester_wall_bay"]["width"]
        for a_, b_ in ((0.0, s0), (s_, L)):
            k = a_
            while k + bay <= b_ + 0.01:
                m, t, n = frame(line, k, k + bay)
                place("chester_wall_bay", m, n, opts.get("wallDens", 0.45)); n_mod += 1
                k += bay
    for w in walls:                                                      # the other walls (the castle's)
        if w is main: continue
        line = LineString(w); L = line.length; bay = INFO["chester_wall_bay"]["width"]; k = 0.0
        while k + bay <= L + 0.01:
            m, t, n = frame(line, k, k + bay)
            place("chester_wall_bay", m, n, 0.25); n_mod += 1
            k += bay
    note["wall pieces"] = n_mod
    note["people on the walls and terraces"] = (len(S.people) - people0) // 4

    # ---- the city beyond: the OSM buildings in the cleared area beyond the main wall, as the terraced houses and blocks
    nb = 0
    stand_box = [Polygon(q) for q in S.nogo]
    for f in E:
        if f["kind"] != "b" or "p" not in f: continue
        P = Polygon(W(f["p"])).buffer(0)
        if P.is_empty or P.area < 60: continue
        cx, cz = P.centroid.x, P.centroid.y
        if not in_clear(cx, cz) or infield.contains(Point(cx, cz)) or P.distance(turf) < 4.0: continue
        if any(P.intersects(q) for q in stand_box): continue
        if main is not None:
            ml = LineString(main); a_ = ml.interpolate(ml.project(Point(cx, cz)))
            if turf.distance(Point(cx, cz)) < turf.distance(a_) + 4.0: continue        # only beyond the wall
        mr = P.minimum_rotated_rectangle; xy = np.array(mr.exterior.coords)[:4]
        e0, e1 = xy[1] - xy[0], xy[2] - xy[1]; L0, L1 = np.hypot(*e0), np.hypot(*e1)
        ax = e0 / L0 if L0 >= L1 else e1 / L1; Lm, Dm = max(L0, L1), min(L0, L1)
        c = xy.mean(0)
        n = np.array([-ax[1], ax[0]])
        if turf.distance(Point(*(c + n * 5))) > turf.distance(Point(*(c - n * 5))): n = -n
        tg = f["tags"]; tall = ("building:levels" in tg and float(tg["building:levels"]) >= 5) or ("height" in tg and float(tg["height"]) > 15)
        piece = "chester_city_block" if tall else "chester_terrace_row"
        gi = INFO[piece]
        turn = math.degrees(math.atan2(n[0], n[1]))
        front = c + n * Dm / 2                                         # the piece's origin is the middle of its front
        S.piece(MODEL, piece, front[0], front[1], turn, sx=min(1.5, max(0.5, Lm / gi["width"])), sc=1.0)
        nb += 1
    note["city buildings"] = nb
    # ---- life (owner, 00:39: "build the festival crowd etc and bring it to life"): flags along the wall's walkway over the
    # terraces, balloon pods in rows of five along the infield opposite the stands, banner flags on the rail lawn
    from shapely.geometry import LineString as _LS
    nf = 0
    for pc in S.pieces:
        if pc[1] in ("chester_wt_stand", "chester_wt_stand_lantern", "chester_wt_steps_rail", "chester_wt_tower"):
            x, z, turn = pc[2], pc[3], pc[4]; a = math.radians(turn); fx, fz = math.sin(a), math.cos(a)
            for u in ((-12.0, 12.0) if "stand" in pc[1] else (0.0,)):
                ux, uz = math.cos(a), -math.sin(a)
                px, pz = x + ux * u + fx * -1.2, z + uz * u + fz * -1.2
                S.piece("site_props", "flagpole", px, pz, turn, y=(pc[7] if len(pc) > 7 else S.G(px, pz)) + 9.4); nf += 1
    nb_ = 0
    rows = opts.get("balloonRows", [40.0, 110.0, 180.0])
    for xc in rows:
        cut = infield.intersection(_LS([(xc, -500.0), (xc, 500.0)]))
        if cut.is_empty: continue
        zs = [cc[1] for g in getattr(cut, "geoms", [cut]) for cc in g.coords]
        z0 = min(zs, key=lambda zz: abs(zz))                              # the infield's edge on the home straight side
        for k in range(5):
            x = xc + (k - 2) * 10.0; z = z0 + 14.0
            if infield.buffer(-6).contains(Point(x, z)) and not S.blocked(x, z):
                S.piece("site_props", "balloon_pod", x, z, rnd.uniform(0, 360)); nb_ += 1
                S.nogo.append([(x - 3, z - 3), (x + 3, z - 3), (x + 3, z + 3), (x - 3, z + 3)])
    for x in np.arange(-40.0, 250.0, 22.0):                             # banner flags along the rail lawn
        cut = turf.exterior.intersection(_LS([(x, -60.0), (x, 0.0)]))
        if cut.is_empty: continue
        zs = [cc[1] for g in getattr(cut, "geoms", [cut]) for cc in g.coords]
        z = min(zs) - 4.5
        if not S.blocked(x, z): S.piece("site_props", "banner_flag", x, z, 0.0); nf += 1
    note["flags"], note["balloon pods"] = nf, nb_
    # the County Stand's kink comes forward of its front line: no lawn crowd inside it (its own crowd sits on its rows)
    for pc in S.pieces:
        if pc[1] != "chester_county_stand": continue
        gi = INFO["chester_county_stand"]; k = gi.get("kink")
        if not k: break
        x, z, turn = pc[2], pc[3], pc[4]; a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
        w = lambda u, v: (x + u * ca - v * sa, z - (u * sa + v * ca))
        lx, ly = k["leftEnd"]; D = gi["depth"]
        poly = prep(Polygon([w(lx, ly - 2.0), w(k["at"], -2.0), w(k["at"], D), w(lx - 2.0, ly + D)]).buffer(1.0))
        keep, gone = [], 0
        P_ = S.people
        for i in range(0, len(P_), 4):
            px, py, pz = P_[i], P_[i + 1], P_[i + 2]
            if poly.contains(Point(px, pz)) and py < S.G(px, pz) + 1.5: gone += 1; continue
            keep += P_[i:i + 4]
        S.people[:] = keep
        note["lawn people cleared from the kink"] = gone
    return note
