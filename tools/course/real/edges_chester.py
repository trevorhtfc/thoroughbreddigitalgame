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
from shapely.ops import unary_union as _uu

REPO = Path(__file__).resolve().parents[3]
TREE_KINDS = ("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")      # perimeter.py's KINDS

STONE, STONE_LIT, COPING = "#c4836b", "#d29a83", "#ddb19a"           # red sandstone, its steps, the coping
BRICKS = ["#c98a72", "#b97862", "#d39b80", "#bf846f", "#e2c7ad"]       # the city's brick and the odd rendered front
ROOFS = ["#8c6e66", "#7e7a86", "#956f62"]


def polys_(g):
    return [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]


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
    far_side = None
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

    def clear_line(line, req, iters=4, ease=15):
        """the wall line rationalised (owner, 19 Nov 13:45, the broken wall at the castle-end bend: "this needs properly
        fixing"): OSM's line pushed out wherever it comes closer to the turf than req(x, z) metres, then smoothed so it
        bends gently; repeated so the smoothing doesn't pull it back in"""
        q = np.array([line.interpolate(u).coords[0] for u in np.arange(0, line.length + 0.01, 2.0)])
        for _ in range(iters):
            for i, p_ in enumerate(q):
                P_ = Point(*p_); d_ = turf.distance(P_); r_ = req(*p_)
                if d_ < r_:
                    near_ = np.array(turf.exterior.interpolate(turf.exterior.project(P_)).coords[0])
                    v_ = p_ - near_; l_ = np.hypot(*v_)
                    if l_ < 1e-6: continue
                    if turf.contains(P_): v_ = -v_
                    q[i] = near_ + v_ / l_ * r_
            k_ = ease
            pad = np.vstack([np.repeat(q[:1], k_, 0), q, np.repeat(q[-1:], k_, 0)])
            q = np.array([pad[i:i + 2 * k_ + 1].mean(0) for i in range(len(q))])
        return LineString(q)

    def wall_nogo(m, t, n, w, d_back):
        S.nogo.append([tuple(m - t * w / 2 + n * 4.0), tuple(m + t * w / 2 + n * 4.0), tuple(m + t * w / 2 - n * d_back), tuple(m - t * w / 2 - n * d_back)])

    n_mod = 0; bays_ = []
    gap = mw.get("gap", 14.0); gap_t = mw.get("gapTerraces", 24.0); t_from = mw.get("terracesFrom", 132.0)
    if main is not None:
        line = LineString(main)
        if line.coords[0][0] > line.coords[-1][0]: line = LineString(list(line.coords)[::-1])     # run it up the straight
        line = clear_line(line, lambda x, z: gap_t if t_from - 30 <= x <= t_from + 160 else gap)
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
        for a_, b_, kind_ in ((0.0, s0, "behind"), (s_, L, "plain")):
            k = a_
            while k + bay <= b_ + 0.01:
                m, t, n = frame(line, k, k + bay)
                place("chester_wall_bay", m, n, opts.get("wallDens", 0.45)); n_mod += 1; wall_nogo(m, t, n, bay, 6.0)
                bays_.append((m, t, n, kind_, "main"))
                k += bay
    for w in walls:                                                      # the other walls (the castle's)
        if w is main: continue
        line = clear_line(LineString(w), lambda x, z: gap); L = line.length; bay = INFO["chester_wall_bay"]["width"]; k = 0.0
        while k + bay <= L + 0.01:
            m, t, n = frame(line, k, k + bay)
            place("chester_wall_bay", m, n, 0.25); n_mod += 1; wall_nogo(m, t, n, bay, 6.0)
            bays_.append((m, t, n, "plain", id(w)))
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
    # ---- the far edges (owner, 19 Nov 08:06: "Yeah fill the edges")
    from shapely.ops import unary_union as _uu
    far = opts.get("far", {})
    # the river: the Dee's water as a flat, clipped to the view; no trees on it
    water = None
    for f in E:
        if f["kind"] == "water" and "parts" in f:
            outer = [Polygon(W(pt["p"])) for pt in f["parts"] if pt["role"] == "outer" and len(pt["p"]) > 3]
            holes = [Polygon(W(pt["p"])) for pt in f["parts"] if pt["role"] == "inner" and len(pt["p"]) > 3]
            if outer:
                water = _uu([g.buffer(0) for g in outer]).difference(_uu([g.buffer(0) for g in holes]) if holes else Polygon())
    if water is not None:
        view = box(*far.get("riverBox", [-420.0, -500.0, 820.0, 820.0]))
        water = water.intersection(view).difference(turf.buffer(8.0))
        for g in polys_(water):
            if g.area > 200:
                S.flat(far.get("waterColour", "#a7c1cb"), [(round(a, 2), round(b, 2)) for a, b in g.simplify(1.5).exterior.coords[:-1]], 0.06)
        pw = prep(water.buffer(3.0))
        n0 = len(trees); trees[:] = [t for t in trees if not pw.contains(Point(t[0], t[1]))]
        note["trees off the river"] = n0 - len(trees)

    def line_of(name_bits, bridge_only=True):
        ws = [W(f["p"]) for f in E if f["kind"] == "rail" and all(b in str(f["tags"]) for b in name_bits)
              and (not bridge_only or f["tags"].get("bridge") == "viaduct")]
        return ws

    # the Roodee Viaduct: brick arches from the north corner down to the river, then the railway's spans over the Dee
    n_v = 0
    ways = [w for w in line_of(["Shrewsbury"]) if LineString(w).length > 300]
    if ways:
        rv = LineString(min(ways, key=lambda w: turf.distance(LineString(w))))
        if rv.coords[0][1] > rv.coords[-1][1]: rv = LineString(list(rv.coords)[::-1])       # from the north corner
        river_ways = [w for w in line_of(["Shrewsbury"]) if 60 < LineString(w).length < 160] + \
                     [w for w in line_of(["Crewe"]) if 60 < LineString(w).length < 160]
        FRONTS = []
        def run(line, piece, step, offset):
            nonlocal n_v
            L = line.length; k = 0.0
            while k + step <= L + 0.01:
                m, t, n = frame(line, k, k + step)
                m = m + n * offset                               # the line is the railway's centre: the face is half a deck out
                # kept clear of the track with room for the trees in front (OSM's railway runs almost on the turf's edge
                # down the far side, and the race view's track is laid a little wider than the real one there)
                fp = Point(*m); sd = -turf.exterior.distance(fp) if turf.contains(fp) else turf.distance(fp)
                if sd < far.get("viaductGap", 14.0): m = m - n * (far.get("viaductGap", 14.0) - sd)
                FRONTS.append((m.copy(), t.copy(), n.copy()))
                gi = INFO[piece]
                turn = math.degrees(math.atan2(n[0], n[1]))
                S.piece(MODEL, piece, m[0], m[1], turn, y=S.G(*m))
                S.nogo.append([tuple(m - t * step / 2), tuple(m + t * step / 2), tuple(m + t * step / 2 - n * gi["depth"]), tuple(m - t * step / 2 - n * gi["depth"])])
                n_v += 1; k += step
        run(rv, "chester_viaduct_bay", INFO["chester_viaduct_bay"]["width"], INFO["chester_viaduct_bay"]["depth"] / 2)
        if river_ways:
            rw = LineString(min(river_ways, key=lambda w: LineString(w).distance(Point(*rv.coords[-1]))))
            if Point(*rw.coords[0]).distance(Point(*rv.coords[-1])) > Point(*rw.coords[-1]).distance(Point(*rv.coords[-1])):
                rw = LineString(list(rw.coords)[::-1])
            run(rw, "chester_viaduct_span", INFO["chester_viaduct_span"]["width"], INFO["chester_viaduct_span"]["depth"] / 2)
        # nothing beyond the viaduct (22:08): its far side cleared of the placeholder trees and boards
        sides = [LineString(list(rv.coords)).buffer(d_, single_sided=True) for d_ in (400.0, -400.0)]
        far_side = min(sides, key=lambda g: g.intersection(turf).area)      # the side away from the course
        far_side = far_side.union(LineString(list(rv.coords)).buffer(8.0))
        pf = prep(far_side)
        n0, b0_ = len(trees), len(boards)
        trees[:] = [t for t in trees if not pf.contains(Point(t[0], t[1]))]
        boards[:] = [b for b in boards if not pf.contains(Point(b[0], b[1]))]
        note["cleared beyond the viaduct"] = [n0 - len(trees), b0_ - len(boards)]
        # the trees planted thick in front of it (owner, 08:36: "The viaduct actually has trees panted pretty dense infront
        # of it"): two staggered rows along its track side, tall enough to hide much of the arches, a gap kept to the rail
        vb = far.get("viaductTrees", {"rows": [[3.5, 1.25, 1.6], [8.5, 1.15, 1.5], [13.0, 1.05, 1.35]], "offTurf": 3.5})
        nt = 0
        for face, t, n in FRONTS:
            for j in range(2):                                           # two trees a row per 12 m bay, staggered
                for ri, (off, s_lo, s_hi) in enumerate(vb["rows"]):
                    q = face + n * (off + rnd.uniform(-1.0, 1.0)) + t * ((j - 0.5) * 6.0 + (1.5 if ri % 2 else -1.5) + rnd.uniform(-1.0, 1.0))
                    if turf.distance(Point(*q)) < vb["offTurf"] or turf.contains(Point(*q)): continue
                    trees.append([round(q[0], 2), round(q[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(s_lo, s_hi), 2), rnd.randrange(360), 1])
                    nt += 1
        note["trees in front of the viaduct"] = nt
    note["viaduct pieces"] = n_v

    # Grosvenor Bridge, on its OSM outline; the castle's range and the Agricola Tower on the castle's
    for f in E:
        nm = f["tags"].get("name", "")
        if nm == "Grosvenor Bridge" and "p" in f:
            P = Polygon(W(f["p"])).buffer(0); mr = P.minimum_rotated_rectangle; xy = np.array(mr.exterior.coords)[:4]
            e0, e1 = xy[1] - xy[0], xy[2] - xy[1]; L0, L1 = np.hypot(*e0), np.hypot(*e1)
            ax = e0 / L0 if L0 >= L1 else e1 / L1; Lm, Dm = max(L0, L1), min(L0, L1)
            c = xy.mean(0); n = np.array([-ax[1], ax[0]])
            if turf.distance(Point(*(c + n * 5))) > turf.distance(Point(*(c - n * 5))): n = -n
            front = c + n * Dm / 2
            gi = INFO["chester_grosvenor_bridge"]
            S.piece(MODEL, "chester_grosvenor_bridge", front[0], front[1], math.degrees(math.atan2(n[0], n[1])),
                    sx=Lm / gi["width"], y=float(np.min([S.G(*q) for q in xy])))
            note["Grosvenor Bridge"] = [round(Lm), round(Dm)]
        if f["kind"] == "historic" and nm == "Chester Castle" and "p" in f:
            P = Polygon(W(f["p"])).buffer(0); c = np.array(P.centroid.coords[0])
            near = np.array(P.exterior.interpolate(P.exterior.project(Point(*np.array(turf.centroid.coords[0])))).coords[0])
            n = c - near; n = -n / (np.hypot(*n) or 1)                    # towards the track
            pos = near - n * 18.0
            S.piece(MODEL, "chester_castle_range", pos[0], pos[1], math.degrees(math.atan2(n[0], n[1])), y=S.G(*pos))
            tw = near - n * 4.0 + np.array([-n[1], n[0]]) * 38.0
            S.piece(MODEL, "chester_agricola_tower", tw[0], tw[1], math.degrees(math.atan2(n[0], n[1])), y=S.G(*tw))
            note["castle"] = True

    # Grosvenor Road at the home turn: the carriageway on the ground (its bridge is the model)
    nr = 0
    for f in E:
        if f["kind"] == "road" and f["tags"].get("name") == "Grosvenor Road" and not f["tags"].get("bridge") and "p" in f:
            g = LineString(W(f["p"])).buffer(far.get("roadHalfWidth", 6.0), cap_style=2).difference(turf.buffer(6.0))
            for gg in polys_(g):
                if gg.area > 50:
                    S.flat("#b9b3ab", [(round(a, 2), round(b, 2)) for a, b in gg.simplify(0.8).exterior.coords[:-1]], 0.05); nr += 1
    note["road pieces"] = nr

    # the houses over the river (Handbridge): terraced rows on the far bank, set back behind its trees, facing the course
    nh = 0
    if water is not None:
        bank_pts = []
        for g in polys_(water):
            ring = g.exterior
            for k in np.arange(0, ring.length, 45.0):
                q = ring.interpolate(k); d = turf.distance(q)
                if far.get("farBankMin", 70.0) < d < far.get("farBankMax", 260.0): bank_pts.append((q.x, q.y))
        for x, z in bank_pts:
            q = np.array([x, z]); a_ = np.array(turf.exterior.interpolate(turf.exterior.project(Point(x, z))).coords[0])
            n = q - a_; n /= (np.hypot(*n) or 1)                         # away from the course
            pos = q + n * far.get("houseBack", 28.0)
            if water.buffer(6.0).contains(Point(*pos)) or (far_side is not None and ways and pf.contains(Point(*pos))): continue
            if any(Polygon(nq).contains(Point(*pos)) for nq in S.nogo[-400:]): continue
            turn = math.degrees(math.atan2(-n[0], -n[1]))
            S.piece(MODEL, "chester_terrace_row", pos[0], pos[1], turn, sx=rnd.uniform(0.8, 1.05), y=S.G(*pos)); nh += 1
            for k in range(3):                                           # a few trees in front, on the bank
                tp = q + n * rnd.uniform(6, 18) + np.array([-n[1], n[0]]) * rnd.uniform(-20, 20)
                if not water.contains(Point(*tp)):
                    trees.append([round(tp[0], 2), round(tp[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(1.1, 1.5), 2), rnd.randrange(360)])
            for k in range(4):                                           # (19 Nov: "embed buildings into scenery") big trees behind and between
                tp = q + n * rnd.uniform(40, 62) + np.array([-n[1], n[0]]) * rnd.uniform(-24, 24)
                if not water.buffer(3.0).contains(Point(*tp)):
                    trees.append([round(tp[0], 2), round(tp[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(1.4, 1.9), 2), rnd.randrange(360), 1])
    note["houses over the river"] = nh

    # ---- the forecourts (owner, 19 Nov 13:44: "the way each stand module meets the track edge is wrong.. they should bleed
    # into the usual kind of forecourt area with crowd right up to the track"; "stand terraces should continue and not
    # just fade to grass"): one paved apron from the outer rail back to the fronts of the stands and the wall terraces,
    # along the whole stand side, packed with a standing crowd that hugs the rail and thins towards the buildings
    fc = opts.get("forecourt")
    if fc:
        from shapely.ops import unary_union as _uu
        def fp_(gi, x, z, turn, sx=1.0):
            a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
            w = lambda u, v: (x + u * ca - v * sa, z - (u * sa + v * ca))
            D = gi["depth"]; k = gi.get("kink")
            if k:
                r, (lx, ly) = k["right"], k["leftEnd"]; L_ = math.hypot(lx, ly); nx_, ny_ = -ly / L_, lx / L_
                if ny_ < 0: nx_, ny_ = -nx_, -ny_
                return Polygon([w(lx, ly), w(0, 0), w(r, 0), w(r, D), w(0, D), w(lx + nx_ * D, ly + ny_ * D)])
            o, hw = gi.get("offset", 0.0), gi["width"] / 2 * sx
            fa = gi.get("frontAt", 0.0)
            return Polygon([w(o - hw, fa), w(o + hw, fa), w(o + hw, D), w(o - hw, D)])
        blds = [fp_(INFO[q[1]], q[2], q[3], q[4], q[5]).buffer(0.4) for q in S.pieces if q[0] == MODEL and q[1] in INFO]
        blds += [Polygon(q).buffer(0) for q in S.nogo]
        gap_r = course["rails"]["gap"]
        x0f, x1f = fc.get("x", [-100.0, 300.0])
        side_box = box(x0f, -200.0, x1f, 40.0)
        apron = Polygon(turf.exterior).buffer(fc.get("depth", 30.0)).difference(Polygon(turf.exterior).buffer(gap_r + 0.3))
        apron = apron.intersection(side_box).difference(_uu(blds)).difference(infield)
        parts_ = [g_ for g_ in polys_(apron) if g_.distance(turf) < gap_r + 1.0 and g_.area > 20]
        nfc = 0
        for g_ in parts_:
            S.flat(fc.get("colour", "#e4d8c2"), [tuple(c_) for c_ in g_.exterior.coords][:-1], y=0.03)
            x0_, z0_, x1_, z1_ = g_.bounds
            for x_ in np.arange(x0_, x1_, 0.55):
                for z_ in np.arange(z0_, z1_, 0.55):
                    px, pz = x_ + rnd.uniform(-0.25, 0.25), z_ + rnd.uniform(-0.25, 0.25); P_ = Point(px, pz)
                    if not g_.contains(P_): continue
                    d_ = turf.distance(P_) - gap_r
                    dens = fc.get("railDens", 0.95) if d_ < fc.get("railBand", 4.0) else fc.get("dens", 0.42)
                    if rnd.random() > dens * 0.3025: continue
                    near_ = turf.exterior.interpolate(turf.exterior.project(P_))
                    S.person(px, 0.0, pz, NM.face(near_.x - px + rnd.uniform(-2, 2), near_.y - pz + rnd.uniform(-2, 2))); nfc += 1
        note["forecourt crowd"] = nfc

    # ---- the infield festival (owner, 19 Nov 13:44 "the festival zone sucks"; 13:50 his race-day photos of the infield):
    # a solid crowd on the infield rail all down the home straight; behind it runs of linked blue-and-white pagodas, the
    # two-storey bar with its crowded roof deck near the post, the long glazed marquees, the big screen at the far end
    # facing the stands, lamp posts with speakers; deeper in, white marquees, kiosks and picnic areas among the crowd;
    # the rest of the infield open grass with a lighter crowd on its rail
    fe = opts.get("festival")
    if fe:
        PRr = course["routes"]["round"]["pathRail"]; RP_ = np.array(PRr["points"]); cen_ = np.array(infield.centroid.coords[0])
        def on_r(d, off):
            f_ = (d - PRr["d0"]) / PRr["spacing"]; i_ = max(0, min(len(RP_) - 2, int(f_))); k_ = f_ - i_
            a_, b_ = RP_[i_], RP_[i_ + 1]; p_ = a_ + (b_ - a_) * k_; t_ = (b_ - a_) / np.linalg.norm(b_ - a_)
            n_ = np.array([-t_[1], t_[0]])
            if np.dot(n_, cen_ - p_) > 0: n_ = -n_
            return p_ - n_ * off, n_, t_                       # off metres in from the inside rail; n_ out across the track
        fz = Polygon(infield.exterior).buffer(-0.8)
        def kit(piece, d, off, dens=1.2):
            p_, n_, t_ = on_r(d, off); gi = INFO[piece]
            turn = math.degrees(math.atan2(n_[0], n_[1]))
            S.piece(MODEL, piece, p_[0], p_[1], turn, y=0.0)
            if gi.get("crowd") and dens > 0: S.stand_people(gi, p_[0], p_[1], turn, 1.0, 1.0, dens, g=0.0)
            hw = gi["width"] / 2 + 0.5; dp = gi["depth"] + 0.5
            S.nogo.append([tuple(p_ - t_ * hw + n_ * 0.5), tuple(p_ + t_ * hw + n_ * 0.5), tuple(p_ + t_ * hw - n_ * dp), tuple(p_ - t_ * hw - n_ * dp)])
        def prop(piece, x, z, turn, sc=1.0):
            S.piece("site_props", piece, x, z, turn, 1.0, sc)
            w_, d_ = NM.SP_SIZE[piece]; ca_, sa_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
            hw, hd = w_ / 2 * sc + 0.8, d_ / 2 * sc + 0.8
            S.nogo.append([(x + u * ca_ + v * sa_, z - u * sa_ + v * ca_) for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))])
        d0e, d1e = fe.get("straight", [-90.0, 420.0])
        np0 = len(S.people)
        kit("chester_bar_pavilion", fe.get("bar", -30.0), 14.0, 1.6)
        for d_ in fe.get("pagodas", list(np.arange(20.0, 330.0, 35.0))): kit("chester_pagoda_run", d_, 13.0, 1.4)
        nt_ = len(S.nogo)
        kit("chester_big_screen", fe.get("screen", 362.0), 20.0, 0)
        for d_ in fe.get("clearspans", [-78.0, 405.0]):
            p_, n_, t_ = on_r(d_, 19.0); prop("marquee_clearspan", p_[0], p_[1], math.degrees(math.atan2(n_[0], n_[1])), 1.15)
        for d_ in np.arange(fe.get("lampsFrom", d0e + 10), d1e, 36.0):
            p_, n_, t_ = on_r(d_, 10.5)
            if not S.blocked(*p_): S.piece(MODEL, "chester_lamp_speaker", p_[0], p_[1], 0.0, y=0.0)
        # the rail crowd: solid on the rail down the straight, thinning back to the pagodas; lighter round the rest
        nr = 0
        for d_ in np.arange(-150.0, 1660.0, 0.6):
            straight_ = d0e <= d_ <= d1e
            lo_, depth_ = (0.9, 11.0) if straight_ else (fe.get("restBand", [9.0, 14.0]))   # (elsewhere behind the tracking car's lane)
            for off in np.arange(lo_, depth_, 0.6):
                dens = (0.95 if off < 5.0 else 0.5) if straight_ else 0.16
                if rnd.random() > dens * 0.36: continue
                p_, n_, t_ = on_r(d_, off + rnd.uniform(-0.25, 0.25)); p_ = p_ + t_ * rnd.uniform(-0.25, 0.25)
                if not fz.contains(Point(*p_)) or S.blocked(*p_): continue
                S.person(p_[0], 0.0, p_[1], NM.face(n_[0] + rnd.uniform(-0.4, 0.4), n_[1] + rnd.uniform(-0.4, 0.4))); nr += 1
        # the second line (his third photo): white peaked marquees in a row behind the pagodas
        for d_ in fe.get("whiteLine", []):
            p_, n_, t_ = on_r(d_, fe.get("whiteOff", 31.0))
            if not S.blocked(*p_): prop("marquee_peaks", p_[0], p_[1], math.degrees(math.atan2(n_[0], n_[1])), 1.05)
        # deeper in: the second line of the enclosure, 30-95 m in from the rail
        zone = Polygon([tuple(on_r(d_, 28.0)[0]) for d_ in np.arange(d0e, d1e, 10.0)] + [tuple(on_r(d_, 95.0)[0]) for d_ in np.arange(d1e, d0e, -10.0)]).buffer(0).intersection(fz)
        x0z, z0z, x1z, z1z = zone.bounds; placed_ = []
        for piece, n_p, r_ in fe.get("deepKit", [["marquee_peaks", 9, 13.0], ["big_top", 2, 11.0], ["pagoda_kiosk", 10, 3.5], ["kiosk_awning", 8, 3.5],
                                                  ["pergola_picnic", 8, 5.0], ["picnic_table", 28, 1.6], ["stand_open", 3, 8.5], ["marquee_clearspan", 2, 11.0]]):
            for _ in range(n_p):
                for _t in range(300):
                    x_, z_ = rnd.uniform(x0z, x1z), rnd.uniform(z0z, z1z)
                    if zone.buffer(-r_).contains(Point(x_, z_)) and not S.blocked(x_, z_) and all(math.hypot(x_ - a_, z_ - b_) > r_ + rb + 3 for a_, b_, rb in placed_):
                        near_ = turf.exterior.interpolate(turf.exterior.project(Point(x_, z_)))
                        tn = math.degrees(math.atan2(near_.x - x_, near_.y - z_)) + rnd.choice([0, 0, 0, 90, -90])
                        prop(piece, x_, z_, tn if piece not in ("big_top",) else rnd.uniform(0, 360), rnd.uniform(0.95, 1.15) if "marquee" in piece else 1.0)
                        placed_.append((x_, z_, r_)); break
        nd = 0
        for _ in range(int(zone.area * fe.get("deepDens", 0.07))):
            x_, z_ = rnd.uniform(x0z, x1z), rnd.uniform(z0z, z1z)
            if zone.contains(Point(x_, z_)) and not S.blocked(x_, z_):
                S.person(x_, 0.0, z_, round(rnd.uniform(-3.14, 3.14), 2)); nd += 1
        rest = fz.difference(zone.buffer(10.0)).difference(Polygon([tuple(on_r(d_, 0.0)[0]) for d_ in np.arange(d0e, d1e, 10.0)] + [tuple(on_r(d_, 30.0)[0]) for d_ in np.arange(d1e, d0e, -10.0)]).buffer(0))
        x0r, z0r, x1r, z1r = rest.bounds
        for _ in range(int(rest.area * fe.get("restDens", 0.004))):        # picnic groups on the open grass
            x_, z_ = rnd.uniform(x0r, x1r), rnd.uniform(z0r, z1r)
            if rest.contains(Point(x_, z_)) and not S.blocked(x_, z_):
                for k_ in range(rnd.randint(2, 6)):
                    S.person(x_ + rnd.uniform(-2, 2), 0.0, z_ + rnd.uniform(-2, 2), round(rnd.uniform(-3.14, 3.14), 2)); nd += 1
        note["festival"] = {"rail crowd": nr, "the rest": nd, "people": (len(S.people) - np0) // 4}

    # ---- the wall embedded (owner, 19 Nov 13:51, his view down the straight from the castle end: the wall a retaining
    # wall with a grass bank at its foot, the road along its top, big trees and the Victorian houses hanging over it):
    # a grassy bank against every plain stretch of wall facing the course, and big trees behind the wall all along it
    vb = opts.get("wallEmbed", {})
    if vb:
        if not hasattr(S, "banks"): S.banks = []
        prof = vb.get("bank", [[0.0, 3.2], [2.0, 2.7], [4.5, 1.6], [7.0, 0.6], [10.0, 0.0]])
        run = []
        def flush():
            if len(run) >= 2: S.banks.append({"rows": run[:]})
            run.clear()
        last = None
        for m, t, n, kind_, wid in bays_:
            if kind_ != "plain" or turf.distance(Point(*(m + n * 11.0))) < course["rails"]["gap"] + 2.0 or S.blocked(*(m + n * 6.0)):
                flush(); last = None; continue
            if last is not None and (last[1] != wid or np.hypot(*(m - last[0])) > 12.0): flush()
            for u in (-0.5, 0.0):
                c_ = m + t * u * INFO["chester_wall_bay"]["width"]
                row = []
                for o, h in prof: q = c_ + n * o; row += [round(q[0], 2), h, round(q[1], 2)]
                run.append(row)
            last = (m, wid)
        flush()
        nt = 0
        for i_, (m, t, n, kind_, wid) in enumerate(bays_):
            if i_ % vb.get("treeEvery", 2): continue
            for back, lo, hi in vb.get("treeRows", [[12.0, 1.45, 1.85], [21.0, 1.3, 1.7]]):
                q = m - n * (back + rnd.uniform(-2.0, 2.0)) + t * rnd.uniform(-3.0, 3.0)
                if S.blocked(*q) or turf.buffer(20.0).contains(Point(*q)) or water.buffer(3.0).contains(Point(*q)): continue
                trees.append([round(q[0], 2), round(q[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(lo, hi), 2), rnd.randrange(360), 1]); nt += 1
        note["wall: banks, trees behind"] = [len(S.banks), nt]

    # ---- the skyline (owner, 19 Nov 13:44 "ensure all vistas are terminated by buildings or trees.. faking some skyline
    # spires etc in the distance above the trees"; 13:47 "use planting and distant architectural forms to frame the
    # vistas"): far pieces placed by hand in world x, z, each turned to face the course; distant tree belts
    cen_c = np.array(infield.centroid.coords[0]) if not infield.is_empty else np.array([150.0, 230.0])
    nsk = 0
    for piece, x_, z_, sc_ in opts.get("skyline", []):
        v_ = cen_c - np.array([x_, z_]); turn = math.degrees(math.atan2(v_[0], v_[1]))
        S.piece(MODEL, piece, x_, z_, turn, sx=sc_, y=S.G(x_, z_)); nsk += 1
        gi = INFO[piece]; a_ = math.radians(turn); ca_, sa_ = math.cos(a_), math.sin(a_)
        w_ = lambda u, v: (x_ + u * ca_ - v * sa_, z_ - (u * sa_ + v * ca_))
        S.nogo.append([w_(-gi["width"] / 2 - 4, -4), w_(gi["width"] / 2 + 4, -4), w_(gi["width"] / 2 + 4, gi["depth"] + 4), w_(-gi["width"] / 2 - 4, gi["depth"] + 4)])
    for pts, rows_, lo, hi in opts.get("farBelts", []):
        ln = LineString(pts)
        for u in np.arange(0.0, ln.length, 11.0):
            q = np.array(ln.interpolate(u).coords[0]); q2 = np.array(ln.interpolate(min(ln.length, u + 1.0)).coords[0])
            t_ = (q2 - q) / (np.hypot(*(q2 - q)) or 1); nrm = np.array([-t_[1], t_[0]])
            for k, off in enumerate(rows_):
                tp = q + nrm * (off + rnd.uniform(-3.0, 3.0)) + t_ * rnd.uniform(-4.0, 4.0)
                if water.buffer(4.0).contains(Point(*tp)) or S.blocked(*tp): continue
                trees.append([round(tp[0], 2), round(tp[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(lo, hi), 2), rnd.randrange(360), 1])
    note["skyline pieces"] = nsk

    # ---- the city fill (owner, 19 Nov 15:39: "you didnt really bother with the city scape"; his aerials of the stand side
    # and of the view down the straight: a dense red-brick city rising behind the walls, terraces and bigger blocks with
    # trees among them). A street grid laid along the main wall behind it: blocks of terraces facing the streets, the odd
    # bigger block, a green square now and then, back-garden trees; detailed terraces near the walls, light ones beyond,
    # the real ground rising away from the course (the flat ground eases back to it past 160 m)
    cf = opts.get("cityFill")
    if cf and bays_:
        mains = [b_ for b_ in bays_ if b_[4] == "main"]
        u_ = mains[-1][0] - mains[0][0]; u_ = u_ / np.hypot(*u_)
        v_ = np.array([-u_[1], u_[0]])
        if np.dot(v_, np.mean([b_[2] for b_ in mains], axis=0)) > 0: v_ = -v_          # v_: away from the course
        o_ = np.mean([b_[0] for b_ in mains], axis=0)
        BL, BD, ST = cf.get("block", [46.0, 32.0, 9.0])
        allb = [(b_[0], b_[2]) for b_ in bays_]
        region = _uu([box(*b_) for b_ in cf.get("boxes", opts.get("clear", []))])
        near_rows, far_rows = ["chester_terrace_row"], ["chester_city_row_a", "chester_city_row_b", "chester_city_row_c"]
        far_blocks = ["chester_city_block_a", "chester_city_block_b"]
        nf_ = {"near": 0, "far": 0, "blocks": 0, "greens": 0, "trees": 0, "out": 0, "turf": 0, "wall": 0, "taken": 0}
        def _fp(q):                                     # a placed piece's footprint (the stands kit's axes)
            gi = INFO.get(q[1]); x_, z_, t_ = q[2], q[3], math.radians(q[4]); sx_ = q[5]
            ca_, sa_ = math.cos(t_), math.sin(t_); w_ = lambda u, v: (x_ + u * ca_ - v * sa_, z_ - (u * sa_ + v * ca_))
            hw = gi["width"] / 2 * sx_; fa = gi.get("frontAt", 0.0)
            return Polygon([w_(-hw, fa), w_(hw, fa), w_(hw, gi["depth"]), w_(-hw, gi["depth"])])
        occ = [_fp(q) for q in S.pieces if q[0] == MODEL and q[1] in INFO]
        occ_u = [prep(_uu(occ).buffer(3.0))]
        def free(c, r):
            sq = Polygon([tuple(c - u_ * r - v_ * r), tuple(c + u_ * r - v_ * r), tuple(c + u_ * r + v_ * r), tuple(c - u_ * r + v_ * r)])
            return not any(o.intersects(sq) for o in occ_u)
        for ia in np.arange(-14, 16):
            for ib in np.arange(0, 14):
                c = o_ + u_ * ia * (BL + ST) + v_ * (ib * (BD + ST) + cf.get("start", 30.0))
                P_ = Point(*c)
                if not region.contains(P_) or infield.contains(P_): nf_["out"] += 1; continue
                dT = turf.distance(P_)
                if dT < cf.get("minFromTurf", 55.0): nf_["turf"] += 1; continue
                q_, n_ = min(allb, key=lambda b_: np.hypot(*(b_[0] - c)))
                if np.dot(c - q_, n_) > -cf.get("behindWall", 16.0): nf_["wall"] += 1; continue   # on the city side of the walls
                if water is not None and water.buffer(10.0).contains(P_): continue
                if not free(c, BL / 3.2): nf_["taken"] += 1; continue
                rr = rnd.random()
                if rr < cf.get("green", 0.12):                                              # a green square: trees
                    for _ in range(rnd.randint(4, 7)):
                        tp = c + u_ * rnd.uniform(-BL / 2, BL / 2) + v_ * rnd.uniform(-BD / 2, BD / 2)
                        trees.append([round(tp[0], 2), round(tp[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(1.3, 1.8), 2), rnd.randrange(360), 1]); nf_["trees"] += 1
                    nf_["greens"] += 1; continue
                near = dT < cf.get("nearBand", 150.0)
                for side in (-1, 1):                                                         # the two long sides, facing out
                    if near and rnd.random() < 0.25: piece = "chester_city_block"
                    elif near: piece = rnd.choice(near_rows)
                    elif rnd.random() < cf.get("blocks", 0.25): piece = rnd.choice(far_blocks)
                    else: piece = rnd.choice(far_rows)
                    gi = INFO[piece]
                    pos = c + v_ * side * (BD / 2)                                           # its front on the street
                    face_ = v_ * side
                    turn = math.degrees(math.atan2(face_[0], face_[1]))
                    sc_ = rnd.uniform(0.92, 1.18) if near else rnd.uniform(*cf.get("farScale", [1.0, 1.35])) * (1.15 if "block" in piece else 1.0)
                    S.piece(MODEL, piece, pos[0], pos[1], turn, sx=min(1.12, BL / gi["width"]), sc=sc_, y=S.G(*pos) - 0.3)
                    nf_["blocks" if "block" in piece else ("near" if near else "far")] += 1
                for _ in range(rnd.randint(1, 3)):                                           # back gardens
                    tp = c + u_ * rnd.uniform(-BL / 2.6, BL / 2.6) + v_ * rnd.uniform(-2.5, 2.5)
                    trees.append([round(tp[0], 2), round(tp[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(1.1, 1.6), 2), rnd.randrange(360), 1]); nf_["trees"] += 1
                hw_, hd_ = BL / 2 + 1, BD / 2 + 8
                occ_u.append(prep(Polygon([tuple(c - u_ * hw_ - v_ * hd_), tuple(c + u_ * hw_ - v_ * hd_), tuple(c + u_ * hw_ + v_ * hd_), tuple(c - u_ * hw_ + v_ * hd_)])))
                S.nogo.append([tuple(c - u_ * hw_ - v_ * hd_), tuple(c + u_ * hw_ - v_ * hd_), tuple(c + u_ * hw_ + v_ * hd_), tuple(c - u_ * hw_ + v_ * hd_)])
        note["city fill"] = nf_

    # ---- tree belts by hand (owner, 19 Nov, the cameras: the home straight's head-on looked past the castle-end wall at an
    # empty horizon): rows of trees along each polyline in opts["belts"], [points, rows (metres to the side), scale lo, hi]
    nbt = 0
    for pts, rows_, lo, hi in opts.get("belts", []):
        ln = LineString(pts)
        for u in np.arange(0.0, ln.length, 9.0):
            q = np.array(ln.interpolate(u).coords[0]); q2 = np.array(ln.interpolate(min(ln.length, u + 1.0)).coords[0])
            t_ = (q2 - q) / (np.hypot(*(q2 - q)) or 1); nrm = np.array([-t_[1], t_[0]])
            for k, off in enumerate(rows_):
                tp = q + nrm * (off + rnd.uniform(-2.0, 2.0)) + t_ * (rnd.uniform(-2.5, 2.5) + (4.5 if k % 2 else 0.0))
                if water.buffer(4.0).contains(Point(*tp)) or turf.buffer(12.0).contains(Point(*tp)) or S.blocked(*tp): continue
                trees.append([round(tp[0], 2), round(tp[1], 2), rnd.choice(TREE_KINDS), round(rnd.uniform(lo, hi), 2), rnd.randrange(360), 1]); nbt += 1
    note["belt trees by hand"] = nbt

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
