"""Newmarket's two courses for the 3D race view (race-view/final-furlong.html?course=newmarket or newmarket-july).

    python3 tools/course/newmarket/to_race_view.py

Reads the course files that site_plan.py writes (courses/newmarket-*.json) and the layout modules, and writes the race
view's set of files for each course, as Ascot's:
    race-view/assets/course/<id>.json            the layout: the path the races run along, the turf, rails and poles
    race-view/assets/course/<id>-view.json       the races, the cameras, the TV director, the set pieces
    race-view/assets/course/<id>-stalls.json     where the stalls stand (the course's own, with Ascot's stall kit)
    race-view/assets/course/<id>-standards.json  par times and the going (the race engine's)
    race-view/assets/course/<id>-scenery.json    what the cameras see: the stands and site pieces from Blender, the
                                                 banks, walls, hedges, paving, trees, boards and the crowd
Ascot is one loop with a straight and a chute; each Newmarket course is one path: a straight with a bend at its top
and a long leg beyond (course 'path'). The view draws everything live (nothing baked yet): the scenery is placed from
the same layout data as the Blender stills, kept to what the race cameras see (owner, 8 Nov).
"""
import json, math, random, struct, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import draft_layout as R          # the Rowley Mile
import july_layout as J           # the July Course
import site_plan as SP            # the two courses together (keeps either's trees off the other's track)

REPO = HERE.parents[2]
OUT = REPO / "race-view/assets/course"
F = 201.168
GAP = 0.4                         # the rails stand this far off the turf's edge (Ascot's)
STEP = 5.0                        # the path's sample spacing, metres


def r2(v): return round(v, 2)


def lin(hexc):
    """A hex colour as the view's linear [r, g, b] (as its ground colours)."""
    c = [int(hexc.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [round(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4, 4) for v in c]


def glb_sizes(path):
    """Each node's footprint (x and z extents, glTF axes) in a .glb, from its accessors' bounds."""
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    g = json.loads(b[20:20 + n])
    out = {}
    for nd in g["nodes"]:
        if "mesh" not in nd: continue
        lo, hi = [1e9] * 3, [-1e9] * 3
        for p in g["meshes"][nd["mesh"]]["primitives"]:
            a = g["accessors"][p["attributes"]["POSITION"]]
            lo = [min(x, y) for x, y in zip(lo, a["min"])]; hi = [max(x, y) for x, y in zip(hi, a["max"])]
        out[nd["name"]] = (hi[0] - lo[0], hi[2] - lo[2])
    return out


SP_SIZE = glb_sizes(REPO / "assets/models/architecture/site_props.glb")


def path_course(L, course, cid, name, stalls):
    """The layout file: the course's own path, heights and bends (for the race engine), plus the rail line sampled
    every 5 m from the end of the run-on to beyond the furthest start, the turf, the rails and the poles."""
    W = L.TRACK_W
    dmax = max(s["distance"] for s in stalls["starts"].values()) + 80
    ds = [-L.RUN_ON + k * STEP for k in range(int((dmax + L.RUN_ON) / STEP) + 1)]
    pts = [L.course_pt(d) for d in ds]
    off = lambda p, w: [r2(p[0][0] + p[1][1] * w), r2(p[0][1] - p[1][0] * w)]
    inside, outer = [off(p, 0) for p in pts], [off(p, W) for p in pts]
    return {
        "id": cid, "name": name, "status": "draft",
        "_about": "Written by tools/course/newmarket/to_race_view.py from courses/%s-draft.json (Rowley Mile: newmarket); don't edit by hand. World axes as "
                  "Ascot's: x along the straight (the horses run towards -x), z across (inside rail z 0, the track to z = trackWidth), "
                  "y up; the winning post on the inside rail is the origin. One path: 'path' and 'heights' for the race engine; "
                  "pathRail is the inside rail sampled every 'spacing' metres from d0 metres to go (d0 < 0: the run-on past the post)." % cid,
        "axes": course.get("axes"), "direction": course.get("direction"),
        "trackWidth": W, "furlong": F, "path": course["path"], "heights": course["heights"],
        "pathRail": {"d0": ds[0], "spacing": STEP, "points": inside},
        "track": {"surface": [inside + outer[::-1]]},
        "rails": {"gap": GAP, "lines": [[off(p, -GAP) for p in pts], [off(p, W + GAP) for p in pts]]},
        "winningPost": [0, 0],
        "ground": GROUND.get(cid),
    }


# The ground's height over the whole site (owner, 9 Nov: model the Dip): the course's own height profile (heights, along
# the path) carried out sideways, each point taking the height at its nearest point on the track's centre line, easing
# to 0 over the outer 'fade' metres of the grid so it meets the flat far ground. The race view and this script read
# the same grid (bilinear between its points), so the turf, rails, horses, buildings, trees and crowd all agree.
GROUND = {}                        # course id -> {"x0", "z0", "cell", "nx", "nz", "h"}


def ground_grid(L, course, cell=20.0, margin=900.0, fade=350.0):
    import numpy as np
    H = course["heights"]; hs = np.array(H["h"], float); d0, sp = H["from"], H["spacing"]
    ds = np.arange(d0, d0 + sp * (len(hs) - 1) + 1e-6, 5.0)
    W = L.TRACK_W
    cen = []
    for d in ds:
        (x, z), (tx, tz) = L.course_pt(d)
        cen.append((x + tz * W / 2, z - tx * W / 2))
    cen = np.array(cen); hd = np.interp(ds, d0 + sp * np.arange(len(hs)), hs)
    x0, z0 = math.floor((cen[:, 0].min() - margin) / cell) * cell, math.floor((cen[:, 1].min() - margin) / cell) * cell
    x1, z1 = cen[:, 0].max() + margin, cen[:, 1].max() + margin
    nx, nz = int((x1 - x0) / cell) + 2, int((z1 - z0) / cell) + 2
    gx, gz = np.meshgrid(x0 + cell * np.arange(nx), z0 + cell * np.arange(nz))
    P = np.stack([gx.ravel(), gz.ravel()], 1); best = np.full(len(P), 1e18); hh = np.zeros(len(P))
    for k in range(0, len(cen), 200):                                  # nearest centre-line point, in chunks
        c = cen[k:k + 200]; dd = ((P[:, None, :] - c[None, :, :]) ** 2).sum(2)
        j = dd.argmin(1); m = dd[np.arange(len(P)), j]; take = m < best
        best[take] = m[take]; hh[take] = hd[k:k + 200][j[take]]
    edge = np.minimum.reduce([gx.ravel() - x0, x0 + cell * (nx - 1) - gx.ravel(), gz.ravel() - z0, z0 + cell * (nz - 1) - gz.ravel()])
    w = np.clip(edge / fade, 0, 1); w = w * w * (3 - 2 * w)
    hh = hh * w
    return {"x0": x0, "z0": z0, "cell": cell, "nx": nx, "nz": nz, "h": [round(float(v), 2) for v in hh],
            "note": "The ground's height (m) every 'cell' metres from (x0, z0), row by row along x: the course's height profile "
                    "carried out sideways from the track's centre line, easing to 0 at the grid's edges. Bilinear between points."}


def ground_at(g, x, z):
    if not g: return 0.0
    fx, fz = (x - g["x0"]) / g["cell"], (z - g["z0"]) / g["cell"]
    i = min(max(int(math.floor(fx)), 0), g["nx"] - 2); j = min(max(int(math.floor(fz)), 0), g["nz"] - 2)
    a = min(max(fx - i, 0.0), 1.0); b = min(max(fz - j, 0.0), 1.0); h = g["h"]; n = g["nx"]
    return (h[j * n + i] * (1 - a) + h[j * n + i + 1] * a) * (1 - b) + (h[(j + 1) * n + i] * (1 - a) + h[(j + 1) * n + i + 1] * a) * b


def bank_rows(L, spans, profile, side, step=10.0):
    """A grassy bank as rows of points across it (x, z, y), every 'step' metres to go along the spans. profile(d) ->
    [[offset beyond the rail, height], ...] (the same count every row); side -1 behind the inside rail, +1 beyond the outer."""
    rows = []
    for d0, d1 in spans:
        d = d0
        while d <= d1 + 1e-6:
            (x, z), (tx, tz) = L.course_pt(d)
            row = []
            for o, h in profile(d):
                w = -o if side < 0 else L.TRACK_W + o
                row += [r2(x + tz * w), r2(h), r2(z - tx * w)]
            rows.append(row)
            d += step
    return rows


def face(dx, dz):
    """The turn (radians about y) that has a crowd figure (facing -z unturned) look along (dx, dz)."""
    return round(math.atan2(-dx, -dz), 2)


class Scene:
    def __init__(s, seed, ground=None):
        s.rnd = random.Random(seed); s.ground = ground
        s.pieces, s.people, s.boxes, s.flats, s.nogo = [], [], {}, {}, []

    def G(s, x, z):
        return ground_at(s.ground, x, z)

    def piece(s, model, piece, x, z, turn=0.0, sx=1.0, sc=1.0):
        s.pieces.append([model, piece, r2(x), r2(z), r2(turn), r2(sx), r2(sc)])

    def box(s, colour, x, z, length, depth, y0, y1, yaw=0.0):
        s.boxes.setdefault(colour, []).append([r2(x), r2(z), r2(length), r2(depth), r2(y0), r2(y1), round(yaw, 3)])

    def flat(s, colour, pts, y=0.02):
        s.flats.setdefault(colour, []).append({"y": y, "pts": [[r2(a), r2(b)] for a, b in pts]})

    def person(s, x, y, z, f, g=None):
        """y above the ground: the ground's own height at (x, z) is added, or g (the height a building stands at)."""
        s.people += [r2(x), r2(y + (s.G(x, z) if g is None else g)), r2(z), f]

    def stand_people(s, info, ox, oz, turn, sx=1.0, sc=1.0, dens=1.6):
        """Spectators in a piece's crowd areas ([x0, x1, y0, y1, floor] in the piece's axes), facing its front."""
        a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
        f = face(math.sin(a), math.cos(a))
        g = s.G(ox, oz)                                                # the building stands at its origin's height
        for x0, x1, y0, y1, fz in info["crowd"]:
            for u, v in s.spots(x0 * sx * sc, x1 * sx * sc, y0 * sc, y1 * sc, dens):
                s.person(ox + u * ca - v * sa, fz * sc, oz - (u * sa + v * ca), f, g)

    def footprint(s, info, ox, oz, turn, sx=1.0, sc=1.0, pad=0.5):
        a = math.radians(turn); ca, sa = math.cos(a), math.sin(a); hw = info["width"] / 2 * sx * sc
        s.nogo.append([(ox + u * ca - v * sa, oz - (u * sa + v * ca)) for u, v in ((-hw, -pad), (hw, -pad), (hw, info["depth"] * sc), (-hw, info["depth"] * sc))])

    def blocked(s, x, z):
        for q in s.nogo:
            inside = False
            for i in range(len(q)):
                (xi, zi), (xj, zj) = q[i], q[i - 1]
                if (zi > z) != (zj > z) and x < (xj - xi) * (z - zi) / (zj - zi) + xi: inside = not inside
            if inside: return True
        return False

    def spots(s, x0, x1, z0, z1, density):
        """Points spread over a rectangle at 'density' a square metre, one in each cell of a grid, jittered: never two
        people in one place (owner, 9 Nov late: overlapping figures flickered against each other)."""
        if density <= 0: return []
        c = 1.0 / math.sqrt(density); nx, nz = max(1, int((x1 - x0) / c)), max(1, int((z1 - z0) / c))
        cx, cz = (x1 - x0) / nx, (z1 - z0) / nz
        return [(x0 + (i + 0.5 + s.rnd.uniform(-0.32, 0.32)) * cx, z0 + (j + 0.5 + s.rnd.uniform(-0.32, 0.32)) * cz)
                for i in range(nx) for j in range(nz)]

    def fill(s, x0, x1, z0, z1, density, f=None):
        for x, z in s.spots(x0, x1, z0, z1, density):
            if not s.blocked(x, z):
                s.person(x, 0.0, z, f if f is not None else round(s.rnd.uniform(-3.14, 3.14), 2))


def boundary_wall(S, x0, x1, z, panel=3.0):
    """The white boundary wall (2.2 m, piers every 3 m, a coping), as the July Course's Blender build."""
    S.box("#f3ede2", (x0 + x1) / 2, z, x1 - x0, 0.3, -0.6, 2.2)
    S.box("#f3ede2", (x0 + x1) / 2, z, x1 - x0, 0.42, 2.2, 2.32)
    x = x0
    while x <= x1 + 1e-6:
        S.box("#f3ede2", x, z, 0.5, 0.5, -0.6, 2.45); S.box("#f3ede2", x, z, 0.62, 0.62, 2.45, 2.58)
        x += panel


# ------------------------------------------------------------------------------------------------ the Rowley Mile
def rowley_scenery(course):
    W = R.TRACK_W
    S = Scene(4, GROUND.get("newmarket"))
    info = json.load(open(REPO / "assets/models/architecture/rowley_stands.json"))["pieces"]
    aprons = []
    for st in R.STAND_PIECES:                       # the stand side's buildings (draft_layout.STAND_PIECES)
        pi = info[st["piece"]]; o = pi.get("offset", 0.0)
        if "turn" in st: ox, oz, turn = st["at"][0], W + st["at"][1], st["turn"]
        else: ox, oz, turn = sum(st["x"]) / 2, W + st["front"], 180.0
        S.piece("rowley_stands", st["piece"], ox, oz, turn)
        a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
        to_c = (lambda ox, oz, ca, sa: lambda u, v: (ox + u * ca - v * sa, oz - (u * sa + v * ca)))(ox, oz, ca, sa)
        hw = pi["width"] / 2
        S.nogo.append([to_c(u, v) for u, v in ((-hw + o, -0.5), (hw + o, -0.5), (hw + o, pi["depth"] + 2), (-hw + o, pi["depth"] + 2))])
        if st["piece"] != "judges_kiosk":
            aprons.append((to_c, -hw + o - 3.0, hw + o + 3.0, -10.0 if st["piece"] != "victorian_pavilion" else -5.0, pi["depth"] + 3.0))
        S.stand_people(pi, ox, oz, turn, dens=1.5)
    # the paddock behind the Millennium (owner, 9 Nov evening): the parade ring, pavilions and stables, on paving
    pa = R.PADDOCK_APRON
    S.flat("#e4d8c2", [(pa["x"][0], pa["z"][0]), (pa["x"][1], pa["z"][0]), (pa["x"][1], pa["z"][1]), (pa["x"][0], pa["z"][1])], 0.028)
    for pk in R.PADDOCK:
        pi = info[pk["piece"]]; ox, oz, turn = pk["at"][0], pk["at"][1], pk["turn"]
        S.piece("rowley_stands", pk["piece"], ox, oz, turn)
        a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
        to_c = (lambda ox, oz, ca, sa: lambda u, v: (ox + u * ca - v * sa, oz - (u * sa + v * ca)))(ox, oz, ca, sa)
        hw = pi["width"] / 2
        S.nogo.append([to_c(u, v) for u, v in ((-hw, -0.5), (hw, -0.5), (hw, pi["depth"] + 1), (-hw, pi["depth"] + 1))])
    S.fill(pa["x"][0], pa["x"][1], pa["z"][0] + 2, pa["z"][1] - 2, 0.02)
    # the flat green up the course on the stand side, in strips of subtle shades (owner, 9 Nov evening)
    gx0, gx1 = R.GRASS_STRIPS["x"]
    for z0, z1, col in R.grass_strips():
        S.flat(col, [(gx0, z0), (gx1, z0), (gx1, z1), (gx0, z1)], 0.012)
    # the ground tied together (owner, 8 Nov): a paved apron round every stand, a gravel walk along the rail, low clipped
    # hedges along the aprons' fronts with gaps to walk through, and small trees in the gaps
    small = []
    for k, (to_c, u0, u1, v0, v1) in enumerate(aprons):
        S.flat("#e4d8c2", [to_c(u0, v0), to_c(u1, v0), to_c(u1, v1), to_c(u0, v1)], 0.03 + k * 0.004)
        u = u0
        while u < u1 - 2.0:
            seg = min(9.0, u1 - u)
            c0, c1 = to_c(u, v0 - 0.6), to_c(u + seg - 3.0, v0 - 0.6)
            S.box("#5f8350", (c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2, math.hypot(c1[0] - c0[0], c1[1] - c0[1]), 1.0, 0.0, 1.0,
                  math.atan2(-(c1[1] - c0[1]), c1[0] - c0[0]))
            small.append(to_c(u + seg - 1.5, v0 - 0.6))
            u += seg
    S.flat("#d9c9a8", [(-R.RUN_ON - 100, W + 0.6), (900, W + 0.6), (900, W + 4.6), (-R.RUN_ON - 100, W + 4.6)], 0.025)
    # the stand-side festival up the course: pavilions in loose rows facing the track, flags, a crowd through it
    rnd = S.rnd
    spots = json.load(open(REPO / "assets/models/architecture/site_props_spots.json"))["pieces"]
    for piece, px, pz, turn in R.festival_pieces(rnd):                 # every festival zone (owner's markups, 8 and 9 Nov)
        S.piece("site_props", piece, px, pz, turn)
        ca_, sa_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        for kind in ("seats", "stand"):                                # people in the seats and on the decks (9 Nov late)
            for lx, ly, lz in spots.get(piece, {}).get(kind, []):
                if rnd.random() < 0.85:
                    S.person(px + lx * ca_ - ly * sa_, lz, pz - (lx * sa_ + ly * ca_), face(0, -1) if turn == 180.0 else face(0, 1), S.G(px, pz))
        if piece != "banner_flag":
            w, d = SP_SIZE[piece]
            S.nogo.append([(px - w / 2 - 1, pz - d / 2 - 1), (px + w / 2 + 1, pz - d / 2 - 1), (px + w / 2 + 1, pz + d / 2 + 1), (px - w / 2 - 1, pz + d / 2 + 1)])
    for fz in R.FESTIVAL_ZONES:
        S.fill(fz["x"][0], fz["x"][1], fz["z"][0] + 2, fz["z"][1] - 2, R.FESTIVAL_DENSITY[fz["side"]])
    # the lawns in front of the stands, down to the rail walk: packed along the rail, thinner on the lawns behind
    for rc in R.RAIL_CROWD:                                         # packed right up against the rail (owner, 9 Nov late)
        S.fill(rc["x"][0], rc["x"][1], rc["z"][0], rc["z"][1], rc["density"], face(0, -1) if rc["face"] == 180.0 else face(0, 1))
    for z0, z1, dn in R.LAWN_CROWD["bands"]:                       # back to the stands, densest by the rail
        S.fill(-60, 290, z0, z1, dn, face(0, -1))
    # trees: the course's own (tops beyond the far bank), small ones in the hedge gaps, a backdrop behind the stands
    # (a 7th field on a tree: metres up or down from the ground: the heath's trees beyond the Dyke stand sunk, so from the
    # stands only their tops show over it; the scrub sits up on the Dyke's crest. Owner, 9 Nov late.)
    SINK = -4.0
    trees = [list(t) + [0, SINK] for t in course["trees"]["list"]]
    # (no small trees in the hedge gaps: owner, 9 Nov, no trees in front of the stands)
    x = -130.0
    while x < 760:
        if rnd.random() < 0.3:                                    # a thin, broken line (owner, 9 Nov late)
            x += 13; continue
        back = 228.0 if x < 105 else (125.0 if x < 290 else 108.0)   # behind the paddock there (9 Nov)
        trees.append([r2(x + rnd.uniform(-3, 3)), r2(W + rnd.uniform(back, back + 16)), rnd.choice(["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]), r2(rnd.uniform(1.9, 2.5)), rnd.randrange(360)])
        x += 13
    # Owner (8 Nov): no gaps where the cameras look. The stand camera and the side-on replay look across to the far side:
    # a belt of tree tops all along beyond the bank, thick opposite the stands. The head-on long lens looks up the
    # straight: a belt of trees across its top, round the bend, and a backdrop beyond the stand-side festival.
    grid = {}
    def clear(x, z, m=12.0):
        return not SP.near_track(SP.R_TRACK, R.TRACK_W, x, z, m) and not SP.near_track(SP.J_TRACK, J.TRACK_W, x, z, m)
    def scatter(x0, x1, z0, z1, tries, spacing, scale, kinds=("oak_a", "oak_b", "oak_c", "wide_a", "wide_b", "poplar_a"), margin=12.0, dy=0.0):
        for _ in range(tries):
            x, z = rnd.uniform(x0, x1), rnd.uniform(z0, z1)
            gx, gz = int(x // 10), int(z // 10)
            if any((px - x) ** 2 + (pz - z) ** 2 < spacing ** 2 for i in (-1, 0, 1) for j in (-1, 0, 1) for px, pz in grid.get((gx + i, gz + j), [])):
                continue
            if not clear(x, z, margin) or R.in_festival(x, z, 6.0): continue
            grid.setdefault((gx, gz), []).append((x, z))
            trees.append([r2(x), r2(z), rnd.choice(kinds), r2(rnd.uniform(*scale)), rnd.randrange(360), 1, dy])
    # (from just behind the bank's crest, so the stand camera's long lens, looking down across the track, sees their tops
    # rising over it: owner, "a gentle bank with tree tops beyond")
    # (owner, 9 Nov late: "lose some density of trees... sporadic behind the dyke and pretty thin lines elsewhere")
    scatter(-260, 900, -140, -70, 70, 26.0, [1.5, 2.3], dy=SINK)    # tree tops beyond the Dyke, opposite the stands: sporadic
    scatter(900, 2000, -140, -70, 40, 30.0, [1.4, 2.2], dy=SINK)    # and on up the straight, sparser still
    # (the crest's scrub is a band of its own: see the banks below)
    scatter(2060, 2600, -320, 280, 260, 15.0, [1.8, 2.5], margin=45.0)   # across the top of the straight, round the bend
                                                                 # (well back from the leg: the tracking car and the start camera)
    scatter(700, 2060, W + 70, W + 170, 130, 18.0, [1.6, 2.4])   # beyond the stand-side festival, up the straight
    scatter(-420, -160, -200, W + 200, 110, 15.0, [1.6, 2.4])   # beyond the run-on, behind the head-on camera's back
    for tx, tz, sc_ in R.belt_trees(rnd):                         # the owner's belts as thin broken lines (9 Nov late)
        if clear(tx, tz, 20.0):
            trees.append([r2(tx), r2(tz), rnd.choice(["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]), r2(sc_), rnd.randrange(360), 1])
    # the far bank (owner, 8 Nov: a gentle grassy bank behind the far rail the whole way round)
    fb = course["farBank"]
    prof = [[o, h] for o, h in fb["profileAcross"]] + [[fb["back"] + 30, 0.0]]
    # opposite the stands the Dyke steps back behind the far-side festival (owner, 9 Nov evening): offsets grow by
    # bank_shift(d), the ground flat in front of it
    banks = [{"rows": bank_rows(R, fb["spans"], lambda d: [[0.0, 0.0]] + [[o + R.bank_shift(d), h] for o, h in prof[1:]], -1)}]
    # the scrub along the Dyke's crest (owner, 9 Nov late: the bushes were heavy in places with odd gaps between): one
    # continuous, softly lumpy band of low scrub, its height rising and falling along the course, in its own darker greens
    c0, c1 = fb["crest"][0] - 1.0, fb["crest"][1] + 1.0
    def scrub(d):
        lump = 1.15 + 0.35 * math.sin(d * 0.21) + 0.25 * math.sin(d * 0.077 + 1.3) + 0.18 * math.sin(d * 0.53 + 0.4)
        out = []
        for k in range(9):
            t = k / 8; o = c0 + (c1 - c0) * t
            cap = math.sin(math.pi * t) ** 0.6                         # a rounded top across the band
            out.append([o + R.bank_shift(d), round(R.bank_h(o) + (lump * cap if 0 < k < 8 else -0.05), 2)])
        return out
    sp = [[max(a_, -250.0), min(b_, 2050.0)] for a_, b_ in fb["spans"] if b_ > -250 and a_ < 2050]
    banks.append({"rows": bank_rows(R, sp, scrub, -1, step=2.5), "ramp": [[h, lin(c)] for h, c in
                  ((0.0, "#62804a"), (4.0, "#55753f"), (5.6, "#4c6b39"), (6.8, "#5b7a42"))], "mottle": 0.14})
    return S, trees, banks


# ------------------------------------------------------------------------------------------------ the July Course
STAND_CAM_JULY = [0.0, 13.5, -13.5]          # on the judge's box roof (july_layout.KEY_CAMERAS)


boards_extra = []


def july_scenery(course):
    W = J.TRACK_W
    S = Scene(9, GROUND.get("newmarket-july"))
    rnd = S.rnd
    info = json.load(open(REPO / "assets/models/architecture/july_stands.json"))["pieces"]
    PAD = {"old_pavilion": 3.6, "old_pavilion_wing": 3.6, "victorian_house": 6.0, "judges_box": 1.0}
    DENS = {"judges_box": 0.8, "old_pavilion": 1.3, "old_pavilion_wing": 1.3, "pavilion_small": 0.9}

    def put(piece, ox, oz, turn, sx=1.0, sc=1.0, pad=0.5):
        S.piece("july_stands", piece, ox, oz, turn, sx * sc, sc)          # (the stretch along the front is absolute)
        S.footprint(info[piece], ox, oz, turn, sx, sc, pad)
        S.stand_people(info[piece], ox, oz, turn, sx, sc, DENS.get(piece, 1.8) * rnd.uniform(0.75, 0.95))
    for st in J.STANDS:                                       # the stand side, facing the track
        pi = info[st["piece"]]
        if "turn" in st: put(st["piece"], st["at"][0], st["at"][1], st["turn"], pad=PAD.get(st["piece"], 0.5))
        else:
            sx = (st["x"][1] - st["x"][0]) / pi["width"] if st["piece"].startswith("terrace") else 1.0
            put(st["piece"], sum(st["x"]) / 2, -st["front"], 0.0, sx, pad=PAD.get(st["piece"], 0.5))
    for st in J.FAR_STANDS:                                   # the far side, turned to face the track
        pi = info[st["piece"]]
        sx = (st["x"][1] - st["x"][0]) / pi["width"] if st["piece"].startswith("terrace") else 1.0
        put(st["piece"], sum(st["x"]) / 2, W + st["off"], 180.0, sx, st.get("scale", 1.0))
    kind_piece = {"long marquee": "marquee_clearspan", "three-peak marquee": "marquee_peaks", "pagoda marquee": "pagoda_counter",
                  "white pitched-roof pavilion": "marquee_peaks"}
    rects = []
    for p in J.PAVILIONS:                                     # far side: marquees and pavilions among the trees
        piece = kind_piece[p["kind"]]; w, d = SP_SIZE[piece]
        rx0, rx1 = p["x"]; z0, z1 = W + p["off"][0], W + p["off"][1]
        sc = min(max((z1 - z0) / d, 1.0), 1.6)
        n = max(1, int(round((rx1 - rx0) / (w * sc))))
        for k in range(n):
            S.piece("site_props", piece, rx0 + (k + 0.5) * (rx1 - rx0) / n, (z0 + z1) / 2, 180.0, ((rx1 - rx0) / n) / w, sc)
        rects.append((rx0, rx1, z0, z1))
    for p in J.INFILL:                                        # behind the stands: smaller pavilions and marquees
        if p["kit"] == "site_props":
            sc = p.get("scale", 1.0)
            sxf = p["size"][0] / SP_SIZE[p["piece"]][0] * sc if p.get("fit") else sc
            S.piece("site_props", p["piece"], p["at"][0], p["at"][1], 0.0, sxf, sc)
        else:
            put(p["piece"], p["at"][0], p["at"][1] + p["size"][1] / 2, 0.0, sc=p.get("scale", 1.0))
    for bd in J.BOUNDARY:                                     # the white boundary walls, both sides
        boundary_wall(S, bd["x"][0], bd["x"][1], bd["z"])
    t0, t1 = J.TIER["x"]; zt = W + sum(J.TIER["off"]) / 2       # the tiered stand behind the finish
    for k in range(3):
        S.piece("site_props", "stand_covered", t0 + (k + 0.5) * (t1 - t0) / 3, zt, 180.0, 1.5, 1.5)
    rects.append((t0, t1, W + J.TIER["off"][0], W + J.TIER["off"][1]))
    x = J.FAR_CROWD["x"][0] + 10
    while x < J.FAR_CROWD["x"][1]:
        S.piece("site_props", "banner_flag", x, W + 13.5, 180.0); x += 34
    fx0, fx1 = J.FESTIVAL["x"]; x = fx0 + 6                 # the stand-side festival, facing the track
    while x < fx1 - 8:
        row = [(rnd.choice(["terrace_deck", "terrace_deck", "kiosk_awning", "pagoda_kiosk"]), x, -16.0),
               (rnd.choice(["kiosk_row_arched", "pergola_picnic", "pagoda_counter", "kiosk_awning"]), x + 4, -32.0)]
        if rnd.random() < 0.45: row.append(("marquee_peaks", x + 10, -50.0))
        for pc, px, pz in row:
            S.piece("site_props", pc, px, pz, 0.0)
            w, d = SP_SIZE[pc]; rects.append((px - w / 2, px + w / 2, pz - d / 2, pz + d / 2))
        S.piece("site_props", "banner_flag", x - 3, -11.5, 0.0)
        for _ in range(3): S.piece("site_props", "picnic_table", x + rnd.uniform(-5, 12), rnd.uniform(-44, -22), rnd.uniform(0, 180))
        x += rnd.uniform(22, 30)
    for x0, x1, z0, z1 in rects:
        S.nogo.append([(x0 - 1, z0 - 1), (x1 + 1, z0 - 1), (x1 + 1, z1 + 1), (x0 - 1, z1 + 1)])
    for p in J.INFILL:
        x0, z0 = p["at"][0] - p["size"][0] / 2, p["at"][1] - p["size"][1] / 2
        S.nogo.append([(x0, z0), (x0 + p["size"][0], z0), (x0 + p["size"][0], z0 + p["size"][1]), (x0, z0 + p["size"][1])])
    # the crowd: the lawns in front of the stands, the old pavilion's enclosure, the far rail, round the Garden stand, the festivals
    S.fill(J.LAWN["x"][0], J.LAWN["x"][1], J.LAWN["z"][0] + 1, J.LAWN["z"][1] - 1, 0.42, face(0, 1))
    S.fill(J.ENCLOSURE["x"][0], J.ENCLOSURE["x"][1], J.ENCLOSURE["z"][0], J.ENCLOSURE["z"][1], 0.3, face(0, 1))
    S.fill(J.FAR_CROWD["x"][0], J.FAR_CROWD["x"][1], W + J.FAR_CROWD["off"][0], W + J.FAR_CROWD["off"][1], 0.38, face(0, -1))
    fr = J.FAR_RUNOUT_CROWD; S.fill(fr["x"][0], fr["x"][1], W + fr["off"][0], W + fr["off"][1], 0.3, face(0, -1))
    S.fill(J.FESTIVAL["x"][0], J.FESTIVAL["x"][1], J.FESTIVAL["crowd"][0], J.FESTIVAL["crowd"][1], 0.2)
    ff = J.far_rect(J.FAR_FESTIVAL); S.fill(ff["x"][0], ff["x"][1], ff["z"][0] + 2, ff["z"][1], 0.035)
    # nobody standing in front of the stand camera on the judge's box roof
    P, keep = S.people, []
    for i in range(0, len(P), 4):
        if not (abs(P[i] - STAND_CAM_JULY[0]) < 6 and abs(P[i + 2] - STAND_CAM_JULY[2]) < 6 and P[i + 1] > 3):
            keep += P[i:i + 4]
    S.people = keep
    trees = [list(t) for t in course["trees"]["list"]]
    for t in trees:                                           # the belt across the top of the straight: woodland, not trunks
        if t[0] > J.END_TREES["x"][0] - 20: t.append(1)          # (the head-on's long lens looks straight at it)
    # the stand side up the straight, past the festival (the drone looks across it): low planting a few metres behind the
    # inside rail, boards dotted along the rail, and a loose belt of trees behind
    x = J.FESTIVAL["x"][1] + 14                                # (low planting, as in front of the boundary walls)
    while x < J.STRAIGHT - 40:
        trees.append([r2(x), r2(-7.5 - rnd.uniform(0, 1.5)), rnd.choice(["oak_a", "oak_b", "wide_a", "wide_b"]), r2(rnd.uniform(0.45, 0.65)), rnd.randrange(360)])
        x += rnd.uniform(2.8, 3.8)
    k = 0
    for mid, count in ((880, 5), (1080, 4), (1290, 5), (1500, 4)):
        for j in range(count):
            boards_extra.append([r2(mid + (j - (count - 1) / 2) * J.BOARD_LEN), -J.BOARDS_BEYOND, 0.0, J.BOARD_DESIGNS[k % 4]]); k += 1
    grid = {}
    for _ in range(420):
        x, z = rnd.uniform(J.FESTIVAL["x"][1] + 10, J.STRAIGHT - 40), rnd.uniform(-46, -11)
        gx, gz = int(x // 10), int(z // 10)
        if any((px - x) ** 2 + (pz - z) ** 2 < 8.5 ** 2 for i in (-1, 0, 1) for j in (-1, 0, 1) for px, pz in grid.get((gx + i, gz + j), [])): continue
        grid.setdefault((gx, gz), []).append((x, z))
        trees.append([r2(x), r2(z), rnd.choice(["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]), r2(rnd.uniform(1.3, 2.0)), rnd.randrange(360), 1])
    # the Dyke's face beyond the far side (its profile changes along the course: set back behind the far festival)
    def prof(d):
        B = J.bank_at(d); a = B["foot"] - 4; b = B["back"] + 24
        return [[a + (b - a) * k / 24, J.bank_h(B, a + (b - a) * k / 24)] for k in range(25)]
    banks = [{"rows": bank_rows(J, course["dykeFace"]["spans"], prof, +1)}]
    return S, trees, banks


# ------------------------------------------------------------------------------------------------ cameras and races
def view_file(cid, L, course, stalls, stands_side, cams, prelude, postlude, director=None):
    W = L.TRACK_W
    races = {"_about": "The races the view can show, one for every start in %s-stalls.json. course: 'straight' (no bend) or 'round' "
                       "(down the leg and round the bend into the straight); distance in metres; start: the key in the stalls file." % cid}
    for k, st in stalls["starts"].items():
        races[k] = {"label": k, "course": st["course"], "distance": st["distance"], "start": k}
    races["_default"] = "1m" if "1m" in stalls["starts"] else next(iter(stalls["starts"]))
    out = {
        "_about": "The race view's cameras and dressing for %s. Written by tools/course/newmarket/to_race_view.py; don't edit by hand "
                  "(change the script). World axes as %s.json." % (course["name"], cid),
        "homeStraight": {"runTowards": [-1, 0], "centreZ": W / 2, "standSide": stands_side},
        "scenery": "%s-scenery.json" % cid,
        "ground": {"outside": [0.5194, 0.5856, 0.2693], "turf": [0.199, 0.3713, 0.0748], "bank": [0.44, 0.53, 0.22],
                   "bankRamp": [[h, lin(c)] for h, c in ((0.0, "#bcc98c"), (0.7, "#9fb676"), (1.7, "#6f8a4a"), (3.2, "#7d8c50"),
                                                          (4.3, "#a39a60"), (5.2, "#b5a66c"))],
                   "bankMottle": 0.08,
                   "note": "Ascot's lawn and turf colours (the bake's), so the two courses read as one game"},
        "lanesStraight": {"x": [-L.RUN_ON, L.STRAIGHT], "width": W, "lanes": round(W / 3.75), "strength": 0.12,
                          "note": "soft mown lanes along the straight, 3.75 m wide, as Ascot's"},
        "treeDetail": {"centre": [150, W / 2], "nearRadius": 420},
        "sun": cams.pop("_sun"),
        "races": races,
        "raceCameras": cams,
        "cameraMenu": {"straight": [["drone_straight", "Drone"], ["track_straight", "Tracking"], ["headon", "Head-on"], ["grandstand", "Stand"]],
                       "round": [["track_loop", "Tracking"], ["drone_straight", "Drone"], ["headon", "Head-on"], ["grandstand", "Stand"]]},
        "raceDirector": {
            "schedule": "On the Rowley Mile (owner, 9 Nov late) path.tracking is set: the tracking car down the course (on the leg "
                        "and round the bend, then along the straight), cutting to the drone for flicks.length metres every "
                        "flicks.every metres run (not in the first flicks.from), the drone from path.drone3f metres out, the stand "
                        "camera from path.grandstand (down the Dip) to the line; no head-on.",
            "_about": "One path (owner, 8 Nov: tracking car, head-on, the stand camera, the drone). Round races: the tracking car "
                      "down the leg and round the bend until path.drone metres into the straight; then the drone along the stand "
                      "side; the head-on long lens from beyond the line for the stretch path.headon ([from, to] metres to go, only "
                      "when the race is longer than path.headonMin); the stand camera from path.grandstand to the line and beyond. "
                      "After the finish: the side-on replay, slowed to replaySpeed, from replayFrom metres before the line to replayTo after it.",
            "path": dict({"drone": 120, "headon": [1000, 600], "headonMin": 1150, "grandstand": 600}, **(director or {})),
            "straight": {"grandstand": 600, "camera": "drone_straight"},
            "afterFinish": 4, "replayFrom": 30, "replayTo": 14, "replaySpeed": 0.3},
        "setPieces": {"_about": "Before the off and after the race: eye and at go from the first to the second over 'seconds'.",
                      "prelude": prelude, "postlude": postlude},
        "startSequence": {"standSeconds": 3.0, "holdAfterOff": 4.0, "passAt": 8, "hideAfter": 350},
    }
    return out


def cameras(W, side, stand_cam, sideon, headon_x, sun, drone=(20, 15)):
    """side +1: the stands beyond the outer rail (the Rowley Mile); -1: behind the inside rail (the July Course)."""
    stand_z = W + 20 if side > 0 else -20                     # the drone's lane, over the stand side
    return {
        "_sun": sun,
        "track_straight": {"label": "Tracking", "kind": "track", "course": "straight", "side": 5, "height": 3.0, "fov": [8, 50],
                           "railSide": "outer" if side > 0 else "inside", "ahead": [6, 12, 20, 30, 45, 65, 90],
                           "raise": [[-200, 720, 9]], "frame": "field", "leadRoom": 2,
                           "note": "the car along the stand-side rail, up over the lawns and the festival (raise: x from, x to, height)"},
        "track_loop": {"label": "Tracking", "kind": "track", "course": "round", "side": 12, "height": 3.2, "fov": [6, 45],
                       "ahead": [6, 12, 20, 30, 45, 65, 90], "railSide": "outer" if side > 0 else "inside", "frame": "field", "leadRoom": 2,
                       "note": "the car down the leg and round the bend, on the stand side of the track (the outside of the bend at the "
                               "Rowley Mile, the inside on the July Course)"},
        "drone_straight": {"label": "Drone", "kind": "drone", "across": side * drone[0], "height": drone[1], "ahead": [24, 36, 52, 72, 96, 125],
                           "fov": [10, 55], "frame": "all", "leadRoom": 4,
                           "note": "ahead of the leaders, looking back at the whole field (Ascot's straight-course drone): over the stand side at "
                                   "the Rowley Mile; over the inside half of the track on the July Course, so its picture is the track and the "
                                   "far side, not the empty lawns up the straight behind the inside rail"},
        "headon": {"label": "Head-on", "kind": "fixed", "at": [headon_x, 5.0, W / 2], "fov": [0.6, 24], "frame": "leaders", "window": 28, "leadRoom": 3,
                   "note": "the long lens beyond the line, in the middle of the run-out, looking straight up the course: the field "
                           "coming at it, the groups spread across the track"},
        "grandstand": {"label": "Stand", "kind": "fixed", "at": stand_cam, "fov": [1.5, 24 if side > 0 else 42], "frame": "field", "leadRoom": 3,
                       "closeIn": [260, 60, 18], "widen": [220, 0, 1.2],
                       "note": "the stand camera on the winning line: picks the field up down the straight, closes in on the leaders, "
                               "pans round until they cross the line square on to it (Ascot's grandstand camera)"},
        "sideon": {"label": "Side-on replay", "kind": "fixed", "at": sideon[0], "look": sideon[1], "fov": [26, 26],
                   "note": "square on to the winning line from the stand side: the finish again in slow motion"},
        "start": {"label": "Start", "kind": "start", "ahead": [24, 32, 42], "side": 1.3, "height": 2.3, "fov": [12, 46], "leadRoom": 2,
                  "note": "low on the outer side in front of the stalls, looking back across their faces (Ascot's)"},
        "drone": {"label": "Drone", "kind": "drone", "across": -8, "height": 7, "ahead": [8, 14, 22, 32, 45, 60], "fov": [8, 40],
                  "frame": "field", "leadRoom": 2},
    }


def stalls_file(src, name):
    """The course's stalls, with Ascot's stall kit and gates; fields up to the kit's 26."""
    asc = json.load(open(OUT / "ascot-stalls.json"))
    s = json.load(open(REPO / "courses" / src))
    n = min(s["maxRunners"], asc["maxRunners"])
    return {"_about": "%s's starting stalls (courses/%s, tools/course/newmarket/) with Ascot's stall kit and gates. Written by "
                      "tools/course/newmarket/to_race_view.py." % (name, src),
            "horseStandsBehind": s["horseStandsBehind"], "gates": asc["gates"], "kit": asc["kit"], "maxRunners": n,
            "unitsForField": {k: v for k, v in asc["unitsForField"].items() if int(k) <= n}, "starts": s["starts"]}


def scenery_file(S, trees, boards, banks, models, finish, poles):
    return {"_about": "What the race cameras see, placed from the layout data (tools/course/newmarket/to_race_view.py). pieces: "
                      "[model, piece, x, z, turn (degrees, anticlockwise from above; 0 = the piece's front facing +z), stretch along "
                      "its front, scale]; boxes: {colour: [[x, z, length, depth, y from, y to, yaw]]}; flats: paving and gravel; "
                      "banks: rows of points across a grassy bank [x, y, z, ...] (y above the ground); trees [x, z, tree, scale, turn, 1 if in a belt (an understorey under its crown), 2 for scrub (a light crown only), metres up or down from the ground]; boards [x, z, turn, "
                      "design]; people: [x, y, z, facing] flattened.",
            "models": models, "finishLine": finish, "poles": poles, "pieces": S.pieces, "boxes": S.boxes, "flats": S.flats,
            "banks": banks, "trees": trees, "boards": boards, "people": S.people}


def write(name, data, indent=None):
    (OUT / name).write_text(json.dumps(data, indent=indent, separators=None if indent else (",", ":")))
    print("wrote", name, round((OUT / name).stat().st_size / 1024), "KB")


def main():
    for cid, L, src, name, side in (("newmarket", R, "newmarket", "Newmarket · Rowley Mile", +1),
                                     ("newmarket-july", J, "newmarket-july", "Newmarket · July Course", -1)):
        course = json.load(open(REPO / f"courses/{src}-draft.json"))
        GROUND[cid] = ground_grid(L, course)
        stalls = stalls_file(f"{src}-stalls.json", name)
        W = L.TRACK_W
        c = path_course(L, course, cid, name, stalls)
        # the finish-line assembly on the far rail at the line, facing the stands; it brings its own 30 m of rail
        if side > 0: finish = {"at": [0, -GAP], "turn": 0}; c["rails"]["skip"] = [[-16.7, 16.3, -GAP]]
        else: finish = {"at": [0, W + GAP], "turn": 180}; c["rails"]["skip"] = [[-16.3, 16.7, W + GAP]]
        # the furlong poles on the stand-side rail (as the Blender stills), facing the track
        poles = [{"furlongs": k, "at": [r2(k * F), r2(W + GAP + 0.7) if side > 0 else r2(-GAP - 0.7)], "turn": 180 if side > 0 else 0} for k in range(1, 8)]
        c["straightMile"] = {"length": L.STRAIGHT, "furlongPoles": poles}
        if side > 0:
            S, trees, banks = rowley_scenery(course)
            # the side-on replay (owner, 9 Nov late): from the festival side at the line, looking back across at the stands
            cams = cameras(W, side, [0, 14, W + 28], ([-6, 9.0, -13], [0, 6.0, W * 0.6]), -L.RUN_ON + 12, [-110, 49.5, -35.2])
            cams["sideon"]["fov"] = [44, 44]
            # the director (owner, 9 Nov late): mainly the tracking car, flicks to the drone early on, the drone from 3f, the
            # stand camera down the Dip to the line
            director = {"tracking": True, "drone3f": round(3 * F), "grandstand": 330, "flicks": {"from": 260, "every": 520, "length": 110}}
            # the racecard / overview (owner, 9 Nov, with a photo from the stands): high at the cranked stand's rail end,
            # looking up the course, the Millennium's canopies on the right, a slow drift
            prelude = {"label": "The runners", "seconds": 9, "eye": [[-40, 14, W + 31], [-30, 13, W + 28]], "at": [[480, 2, W * 0.1], [490, 2, W * 0.2]], "fov": 42, "list": [7, 0.6], "cardAfter": 3.5}
            postlude = {"label": "After the race", "seconds": 8, "eye": [[20, 3, W - 8], [60, 45, -60]], "at": [[0, 8, W + 60], [-10, 6, W + 70]], "fov": 42}
            models = ["rowley_stands", "site_props", "finish_line"]
        else:
            S, trees, banks = july_scenery(course)
            director = None
            # the stand camera on the front of the judge's box roof (its own spectators kept clear: see july_scenery)
            cams = cameras(W, side, STAND_CAM_JULY, ([0, 4.5, -9], [0, 1.4, W * 0.58]), -L.RUN_ON + 40, [-110, 49.5, 35.2], drone=(10, 13))
            prelude = {"label": "The runners", "seconds": 9, "eye": [[200, 62, W + 190], [90, 58, W + 190]], "at": [[100, 8, -40], [20, 8, -40]], "fov": 40, "list": [7, 0.6]}
            postlude = {"label": "After the race", "seconds": 8, "eye": [[20, 3, 8], [60, 45, W + 60]], "at": [[0, 8, -40], [-10, 6, -50]], "fov": 42}
            models = ["july_stands", "site_props", "finish_line"]
        boards = [list(b) for b in course["boards"]["list"]] + (boards_extra if side < 0 else [])
        write(f"{cid}.json", c)
        write(f"{cid}-stalls.json", stalls, 1)
        (OUT / f"{cid}-standards.json").write_text((REPO / f"courses/{src}-standards.json").read_text()); print("wrote", f"{cid}-standards.json")
        write(f"{cid}-view.json", view_file(cid, L, course, stalls, side, cams, prelude, postlude, director), 1)
        write(f"{cid}-scenery.json", scenery_file(S, trees, boards, banks, models, finish, poles))
        print("  ", len(S.pieces), "pieces,", len(S.people) // 4, "people,", len(trees), "trees,", len(boards), "boards")


if __name__ == "__main__":
    main()
