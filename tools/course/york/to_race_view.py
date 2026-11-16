"""York for the 3D race view (race-view/final-furlong.html?course=york), phase 2: the track itself.

    python3 tools/course/york/layout.py          (the plan: courses/york-draft.json)
    python3 tools/course/york/to_race_view.py    (this: the race view's files)
    node tools/course/york/calibrate.mjs         (the par times, so the engine's winning times match TARGET below)

Writes, as Ascot's and Newmarket's:
    race-view/assets/course/york.json            the layout: each route's inside rail and bends, the turf, rails, poles
    race-view/assets/course/york-view.json       the races, the cameras, the TV director, the set pieces
    race-view/assets/course/york-stalls.json     where the stalls stand (Ascot's stall kit)
    race-view/assets/course/york-standards.json  par times and the going (the race engine's)
    race-view/assets/course/york-scenery.json    what the cameras see: for now only the finish-line kit (the edges, the
                                                 stands and the festival come in the next phases)

York is the first LEFT-handed course: courses/york.json -> "hand": -1 (the race view puts the track on the horses' right
of the inside rail), and the first with several routes ("routes": the race takes its start's route). Flat (owner,
16 Nov: assume a flat track), so no ground grid.
"""
import json, math, sys
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools/course/newmarket"))
import to_race_view as NM          # Newmarket's: the shared light, ground colours, cameras and view file

OUT = REPO / "race-view/assets/course"
F = 201.168
GAP = 0.4                          # the rails stand this far off the turf's edge (Ascot's)
STALL1, STALL_PITCH, STANDS_BEHIND = 1.625, 1.05, 1.55
MAX_RUNNERS = 22                   # 26 m of track: 22 stalls (York's biggest fields, the Ebor and the sprint handicaps)

# Rough winning times of a good horse on good ground (from memory, to check against real results: the Nunthorpe about
# 57-58 s, the International about 2m09s, the Ebor about 2m58s for its 1m5f188y, the Lonsdale Cup about 3m28s for 2m56y),
# scaled to our distances. PAR (what the engine is handed) is set by calibrate.mjs so its winning times come out at these.
TARGET = {"5f": 58.0, "6f": 70.0, "7f": 83.5, "1m": 97.5, "1m1f": 110.5, "1m2f": 129.5, "1m4f": 152.0, "1m6f": 179.0, "2m": 208.0}
PAR_FILE = HERE / "york-par.json"


def r2(v): return round(v, 2)


def route_bits(route, W):
    """a route's inside rail (world x, z every 'spacing' m from d0 metres to go), its running directions, and its turf strip"""
    pts, sp, d0 = route["insideRail"], route["spacing"], route["d0"]
    n = len(pts)
    tan = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]       # towards fewer metres to go: b(i-1) - a(i+1)
        dx, dz = a[0] - b[0], a[1] - b[1]
        l = math.hypot(dx, dz) or 1
        tan.append((dx / l, dz / l))
    right = [(-tz, tx) for tx, tz in tan]                       # the horses' right (left-handed: the outer side)
    outer = [[p[0] + r[0] * W, p[1] + r[1] * W] for p, r in zip(pts, right)]
    strip = Polygon(pts + outer[::-1]).buffer(0)
    return tan, right, outer, strip


# ------------------------------------------------------------------------------------------------ the stands and the festival
# Owner, 16 Nov (left to right as seen from the infield, so north first; pieces from tools/blender/build_york_stands.py):
# 1 the big pavilion (the July old pavilion, four balconied storeys, red roof, clock gable), turned with the top bend;
# 2 Ascot's tall blocks and iron lace mixed; 3 the grand canopy over the terrace profile in two cranked runs with a lawn
# terrace in front, one a little taller; 4 the Rowley Mile's Victorian stand, longer than the plan; 5 the festival side
# banking up away from the course to the Clock Tower (the judge's box with Ascot's belfry on it).
# Each: piece, x, z (the middle of its front, on the ground; z < 0 the stand side), turn (degrees, 0 = facing +z, the track;
# positive = turned with the top bend), scale.
# Owner, 16 Nov evening, on the aerial view (north to the right): the top bend starts at the winning post (no straight past
# the line), and the stands are set back from the course by a wide lawn (the light green), narrowing round the bend:
#   4 (light orange) the end stand, square to the straight, furthest back;
#   3 (pink) the two grandstands with the kink built in: the south run square to the straight, the north run turned with
#     the bend (as the real Ebor stand, about 13 degrees) so it comes forward towards the line;
#   2 (blue) the pavilions, turned further, from the line into the bend;
#   1 (light blue) the big pavilion, turned furthest, round the bend.
# Placed end to end from the big pavilion southwards (_chain). Set back from the outer rail (z -26.4): about 12 m at the
# big pavilion, 14-20 m at the pavilions, 19 m to 30 m round the Ebor stand, 36 m at the Knavesmire stand (a step back
# and lower, as the owner's photo), 44 m at the end stand.
EBOR_KINK, EBOR_LEFT, EBOR_RIGHT = 24.0, 27.0, 29.0          # as build_york_stands.py's ebor_stand (its json says so too)


def _chain():
    """From the big pavilion (owner: "1 looks good", kept where it was) southwards up the straight, each piece's north
    end a gap from the last one's south end; the gaps are filled by the shoulder links (LINKS). Owner, 16 Nov evening:
    2 smaller (two little stands); 3 in the real proportion, the Ebor stand bent in plan (his sketch), the Knavesmire
    stand "a nice step" back and lower; "join all the stands up at the lower / shoulder levels"."""
    out, links = [("york_big_pavilion", -79.56, -14.83, 30.0, 1.0)], []
    a = math.radians(30.0); end = (-79.56 + 28.0 * math.cos(a), -14.83 - 28.0 * math.sin(a))   # its south end
    def u(turn): t = math.radians(turn); return math.cos(t), -math.sin(t)    # along the front, towards the south (+x)
    # the pavilions, 2 m on
    ux, uz = u(22.0); n0 = (end[0] + 2.0 * ux, end[1] + 2.0 * uz)
    out.append(("york_pavilions", round(n0[0] + ux * 15.5, 2), round(n0[1] + uz * 15.5, 2), 22.0, 1.0))
    end = (n0[0] + ux * 31.0, n0[1] + uz * 31.0)
    # the Ebor stand: its left run (turned with the bend) starts 10 m on; origin at the kink, its right run square
    ux, uz = u(EBOR_KINK); left = (end[0] + 10.0 * ux, end[1] + 10.0 * uz)
    links.append((end, left))
    k = math.radians(EBOR_KINK)
    X, Z = left[0] + EBOR_LEFT * math.cos(k), left[1] - EBOR_LEFT * math.sin(k)
    out.append(("york_stand_north", round(X, 2), round(Z, 2), 0.0, 1.0))
    end = (X + EBOR_RIGHT, Z)
    # the Knavesmire stand, 8 m on and a step (6 m) further back
    zk = Z - 6.0
    links.append((end, (end[0] + 8.0, zk)))
    out.append(("york_stand_south", round(end[0] + 8.0 + 22.0, 2), round(zk, 2), 0.0, 1.0))
    end = (end[0] + 8.0 + 44.0, zk)
    # the end stand, 12 m on
    links.append((end, (end[0] + 12.0, -70.0)))
    out.append(("york_end_stand", round(end[0] + 12.0 + 66.5, 2), -70.0, 0.0, 1.0))
    return out, links
STANDS, LINKS = _chain()
CLOCK_TOWER = ("york_clock_tower", 88.0, 52.0, 180.0, 1.0)
BANK = {"x": [-20.0, 290.0], "z": [9.0, 66.0], "height": 3.5, "fadeX": 45.0, "back": 150.0,
        "note": "the festival side's bank (owner, 16 Nov): rising from the rail lawn to the Clock Tower, then easing back down"}


def bank_h(x, z):
    """The festival bank's height at (x, z): 0 on the course and the stand side."""
    (x0, x1), (z0, z1) = BANK["x"], BANK["z"]
    if z <= z0: return 0.0
    sm = lambda t: (lambda u: u * u * (3 - 2 * u))(min(max(t, 0.0), 1.0))
    up = sm((z - z0) / (z1 - z0)) * (1.0 - sm((z - z1) / BANK["back"]))
    side = sm((x - x0) / BANK["fadeX"]) * sm((x1 - x) / BANK["fadeX"])
    return BANK["height"] * up * side


def ground_grid(cell=10.0):
    x0, x1, z0, z1 = -200.0, 460.0, -60.0, 300.0
    nx, nz = int((x1 - x0) / cell) + 1, int((z1 - z0) / cell) + 1
    h = [round(bank_h(x0 + i * cell, z0 + j * cell), 2) for j in range(nz) for i in range(nx)]
    return {"x0": x0, "z0": z0, "cell": cell, "nx": nx, "nz": nz, "h": h,
            "note": "York's ground: flat, but for the festival side's bank rising to the Clock Tower (tools/course/york/to_race_view.py BANK)."}


class OuterRail:
    """The outer (stand-side) rail by metres to go: up the straight, and past the post round the top bend (the round course's
    run-out to its end, then the 2m loop's, which goes on round the bend)."""
    def __init__(self, C, W):
        self.C, self.W = C, W
        self.circuit = C["measured"]["checks"]["the circuit (inside rail), m"]
        self.lines = []
        for name in ("round", "loop"):
            r = C["routes"][name]
            tan, right, outer, strip = route_bits(r, W + GAP)
            self.lines.append((r["d0"], r["spacing"], outer, tan, right))

    def at(self, d):
        """(x, z), the running direction (tx, tz) and the outward normal (away from the track) at d metres to go"""
        if d >= self.lines[0][0]:
            d0, sp, outer, tan, right = self.lines[0]
        else:
            d0, sp, outer, tan, right = self.lines[1]; d = d + self.circuit
        f = (d - d0) / sp; i = max(0, min(len(outer) - 2, int(f))); k = f - i
        p = [outer[i][j] + (outer[i + 1][j] - outer[i][j]) * k for j in (0, 1)]
        t = tan[i]; n = right[i]
        return p, t, n

    def place(self, d, back, extra=0.0):
        """a piece's (x, z, turn) with the middle of its front 'back' metres behind the rail at d, square to it"""
        (x, z), (tx, tz), (nx, nz) = self.at(d)
        turn = math.degrees(math.atan2(tz, -tx)) + extra               # 0 = facing +z on the straight (running towards -x)
        return x + nx * back, z + nz * back, turn

    def strip(self, d0, d1, b0, b1, step=4.0):
        """a band b0..b1 metres behind the rail from d0 to d1 metres to go, as one polygon"""
        a, b = [], []
        d = d0
        while d <= d1 + 1e-6:
            (x, z), _, (nx, nz) = self.at(d)
            a.append((x + nx * b0, z + nz * b0)); b.append((x + nx * b1, z + nz * b1)); d += step
        return a + b[::-1]

    def people(self, S, d0, d1, b0, b1, density, upto=None):
        """racegoers over a band behind the rail, facing the track (upto(d): no further back than this)"""
        for u, v in S.spots(d0, d1, b0, b1, density):
            if upto and v > upto(u): continue
            (x, z), _, (nx, nz) = self.at(u)
            px, pz = x + nx * v, z + nz * v
            if not S.blocked(px, pz):
                S.person(px, 0.0, pz, NM.face(-nx, -nz))


def york_scenery(W, ground, C):
    import random
    S = NM.Scene(16, ground)
    rnd = random.Random(16)
    info = json.loads((REPO / "assets/models/architecture/york_stands.json").read_text())["pieces"]
    spots = json.loads((REPO / "assets/models/architecture/site_props_spots.json").read_text())["pieces"]
    sizes = NM.SP_SIZE

    def to_w(x, z, turn, u, v):
        a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
        return (x + u * ca - v * sa, z - (u * sa + v * ca))

    def rects(piece, sx=1.0):
        """the piece's plan as rectangles in its own axes (u along the front, v back from it): two for the bent Ebor stand"""
        pi = info[piece]
        if "kink" in pi:
            k = math.radians(pi["kink"]["angle"]); ck, sk = math.cos(k), math.sin(k)
            rot = lambda q: [(a * ck - b * sk, a * sk + b * ck) for a, b in q]
            return [("R", 0.0, pi["kink"]["right"]), ("L", -pi["kink"]["left"], 0.0, rot)]
        hw = pi["width"] / 2 * sx
        return [("R", -hw, hw)]

    def plan_quads(piece, x, z, turn, v0, v1, sx=1.0, grow=0.0):
        out = []
        for r in rects(piece, sx):
            u0, u1 = r[1] - grow, r[2] + grow
            q = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            if r[0] == "L":
                q = r[3](q)
            out.append([to_w(x, z, turn, a, b) for a, b in q])
        return out

    def put(piece, x, z, turn, sc=1.0, dens=1.5, pad=1.0, sx=1.0):
        pi = info[piece]
        S.piece("york_stands", piece, x, z, turn, sx * sc, sc)
        S.nogo.extend(plan_quads(piece, x, z, turn, -pad, pi["depth"] * sc, sx * sc))
        S.stand_people(pi, x, z, turn, sx, sc, dens)
    # the stands, a paved apron in front of each, and the lawn back from the rail packed with racegoers
    rail = OuterRail(C, W)
    for piece, x, z, turn, sc in STANDS:
        put(piece, x, z, turn, sc, dens=1.45)
        for q in plan_quads(piece, x, z, turn, -9.0, 1.0, sc, grow=3.0):
            S.flat("#e4d8c2", q, 0.03)
    # the shoulder links between them: the standing steps carried on, a glazed link up to the shoulder, a roof terrace
    for (ax, az), (bx, bz) in LINKS:
        L = math.hypot(bx - ax, bz - az)
        if L < 3.0: continue
        turn = math.degrees(math.atan2(-(bz - az), bx - ax))
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        put("york_link", mx, mz, turn, 1.0, dens=1.2, sx=(L + 1.0) / info["york_link"]["width"])
        for q in plan_quads("york_link", mx, mz, turn, -9.0, 1.0, (L + 1.0) / info["york_link"]["width"]):
            S.flat("#e4d8c2", q, 0.03)
    S.flat("#d9c9a8", rail.strip(-130, 300, 0.2, 4.2), 0.025)                    # the rail walk, round the bend too
    rail.people(S, -128, 300, 1.2, 9.1, 0.95)                                    # the rail crowd, facing the track
    rail.people(S, -128, 300, 9.1, 15.6, 0.45)
    def front(d):                                      # roughly how far back the stand fronts are (the set back), by metres to go
        pts = [(-130, 11), (-60, 12), (-40, 14), (-15, 18), (9, 30), (38, 30), (46, 36), (90, 36), (102, 44), (300, 44)]
        for (a, fa), (b, fb) in zip(pts[:-1], pts[1:]):
            if d <= b: return fa + (fb - fa) * (d - a) / (b - a)
        return 46
    rail.people(S, -128, 300, 15.6, 47.0, 0.16, lambda d: front(d) - 1.0)        # the lawn back to the stands (the set back)
    # the Clock Tower on top of the festival bank, facing the course, and its people
    piece, x, z, turn, sc = CLOCK_TOWER
    put(piece, x, z, turn, sc, dens=1.2, pad=3.0)
    # the festival side: the rail lawn's crowd; covered and open seating along it; terrace decks, kiosks and pergolas up
    # the bank; long rows of white marquees either side of the tower; a big top; flags along the front
    S.fill(-4, 290, 1.4, 7.5, 0.8, NM.face(0, -1))
    def sp(piece, x, z, turn=180.0, sxf=1.0, sc=1.0, people=0.85):
        S.piece("site_props", piece, x, z, turn, sxf, sc)
        w, d = sizes[piece]
        S.nogo.append([(x - w / 2 * sxf * sc - 0.5, z - d / 2 * sc - 0.5), (x + w / 2 * sxf * sc + 0.5, z - d / 2 * sc - 0.5),
                       (x + w / 2 * sxf * sc + 0.5, z + d / 2 * sc + 0.5), (x - w / 2 * sxf * sc - 0.5, z + d / 2 * sc + 0.5)])
        ca_, sa_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        for kind in ("seats", "stand"):
            for lx, ly, lz in spots.get(piece, {}).get(kind, []):
                if rnd.random() < people:
                    S.person(x + lx * ca_ - ly * sa_, lz, z - (lx * sa_ + ly * ca_), NM.face(0, -1))
    x = -6.0
    while x < 285:                                                             # seating along the rail lawn
        sp(rnd.choice(["stand_covered", "stand_open", "stand_covered"]), x, 12.0); x += rnd.uniform(26, 34)
    x = 0.0
    while x < 282:                                                             # flags at the front
        sp("banner_flag", x, 9.0, people=0); x += 30.0
    x = 4.0
    while x < 280:                                                             # the lower bank: decks, kiosks, pergolas
        if not 66 < x < 112:
            sp(rnd.choice(["terrace_deck", "kiosk_awning", "pergola_picnic", "pagoda_kiosk", "kiosk_row_arched", "terrace_deck"]),
               x + rnd.uniform(-2, 2), 24.0 + rnd.uniform(-2, 2))
        x += rnd.uniform(14, 19)
    for x0, x1 in ((-8.0, 66.0), (114.0, 282.0)):                               # the white marquees either side of the tower
        x = x0
        while x < x1 - 10:
            piece = "marquee_peaks" if (int(x) // 25) % 3 else "marquee_clearspan"
            w = sizes[piece][0]
            sp(piece, x + w / 2, 40.0, people=0); x += w + 3.0
    sp("big_top", 210.0, 64.0, people=0)
    sp("big_top", -4.0, 62.0, people=0)
    for x in (40.0, 140.0, 255.0):
        sp("viewing_tower", x, 56.0)
    S.fill(-15, 290, 15.0, 70.0, 0.32)                                         # racegoers all over the bank
    # trees: a belt behind the stands, and the infield's trees beyond the festival
    trees = []
    kinds = ("oak_a", "oak_b", "oak_c", "wide_a", "wide_b")
    x = -160.0
    while x < 380:
        trees.append([NM.r2(x), NM.r2(-132 - rnd.uniform(0, 30)), rnd.choice(kinds), NM.r2(rnd.uniform(1.1, 1.5)), rnd.randrange(360), 1])
        x += rnd.uniform(9, 14)
    for _ in range(140):
        tx, tz = rnd.uniform(-60, 360), rnd.uniform(95, 260)
        if not S.blocked(tx, tz):
            trees.append([NM.r2(tx), NM.r2(tz), rnd.choice(kinds), NM.r2(rnd.uniform(1.0, 1.5)), rnd.randrange(360)])
    return S, trees


def main():
    C = json.loads((REPO / "courses/york-draft.json").read_text())
    W = C["trackWidth"]
    routes_out, strips = {}, []
    for name, r in C["routes"].items():
        tan, right, outer, strip = route_bits(r, W)
        strips.append(strip)
        # the race engine's bends: the top bend past the post (the run-out) is left out; it starts at the line
        bends = [[b[0], b[1], abs(b[2])] for b in r["bends"] if b[0] > 25.0]
        home = min([b[1] for b in bends], default=0.0)
        routes_out[name] = {"pathRail": {"d0": r["d0"], "spacing": r["spacing"], "points": r["insideRail"]},
                            "path": {"bends": bends, "home": home,
                                     "note": "For the race engine: bends as [metres to go where it starts, where it ends, degrees turned]; "
                                             "'home' = where the home straight starts."}}
    turf = unary_union(strips).buffer(0.01).buffer(-0.01).simplify(0.15)
    if turf.geom_type != "Polygon":
        turf = max(turf.geoms, key=lambda g: g.area)
    surface = [[[r2(x), r2(z)] for x, z in turf.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in turf.interiors]
    railed = turf.buffer(GAP, join_style=2, mitre_limit=2.0).simplify(0.1)
    rails = [[[r2(x), r2(z)] for x, z in railed.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in railed.interiors]
    # the furlong poles on the stand-side (outer) rail up the run-in, facing the track (as the July Course's, whose stands
    # are also on -z); the round course's 5f pole is in the home bend: left out
    poles = [{"furlongs": k, "at": [r2(k * F), r2(-(W + GAP + 0.7))], "turn": 0} for k in range(1, 5)]
    course = {
        "id": "york", "name": "York", "status": "draft",
        "_about": "Written by tools/course/york/to_race_view.py from courses/york-draft.json; don't edit by hand. World axes as Ascot's: "
                  "x along the home straight (the horses run towards -x), y up, the winning post on the inside rail is the origin. "
                  "LEFT-handed (hand -1): the inside rail z 0 on the horses' left, the track to z = -trackWidth on their right, the "
                  "stands beyond (z < -trackWidth), the infield +z. Several routes: each race takes its start's route (stalls file "
                  "-> starts -> route): its inside rail every 'spacing' metres from d0 metres to go, and its bends.",
        "axes": C["axes"], "direction": C["direction"], "hand": -1,
        "trackWidth": W, "furlong": F,
        "routes": routes_out, "defaultRoute": "round",
        "path": routes_out["round"]["path"], "pathRail": routes_out["round"]["pathRail"],
        "track": {"surface": surface},
        "rails": {"gap": GAP, "lines": rails, "skip": [[-16.3, 16.7, GAP]]},
        "straightMile": {"length": C["home"], "furlongPoles": poles},
        "winningPost": [0, 0],
        "ground": ground_grid(),
    }
    NM.write("york.json", course)

    # ---- stalls: each start's stalls across the track from its inside rail, stall 1 on the inside (the infield side)
    asc = json.loads((OUT / "ascot-stalls.json").read_text())
    starts = {}
    keys = {t: "y" + t for t in C["starts"]}
    for t, s in C["starts"].items():
        r = C["routes"][s["route"]]
        pts, sp, d0 = r["insideRail"], r["spacing"], r["d0"]
        i = int(round((s["distance"] - d0) / sp)); i = max(1, min(len(pts) - 2, i))
        k = (s["distance"] - d0) / sp - i
        a, b = pts[i], pts[min(len(pts) - 1, i + 1)]
        x, z = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        p0, p1 = pts[i - 1], pts[i + 1]
        tx, tz = p0[0] - p1[0], p0[1] - p1[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        nx, nz = -tz, tx                                          # towards the outer rail: the horses' right
        straight = s["route"] == "straight"
        starts[t] = {
            "label": t + (" (straight)" if straight else " (round)"), "course": "straight" if straight else "round",
            "route": s["route"], "key": keys[t], "distance": s["distance"], "insideRailAt": [r2(x), r2(z)],
            "runningDirection": [round(tx, 4), round(tz, 4)], "towardsOuterRail": [round(nx, 4), round(nz, 4)],
            "stall1": "inside rail (the infield side)", "onStraight": straight,
            # the 2m starts on the run-in and passes its own start again: the stalls are towed away after the off
            "comesBack": s["route"] == "loop",
            "stalls": [{"draw": j + 1, "fromInsideRail": round(STALL1 + STALL_PITCH * j, 3), "across": round(STALL1 + STALL_PITCH * j - W / 2, 3),
                        "at": [r2(x + nx * (STALL1 + STALL_PITCH * j)), r2(z + nz * (STALL1 + STALL_PITCH * j))]} for j in range(MAX_RUNNERS)],
        }
    stalls = {"_about": "York's starting stalls, DRAFT (tools/course/york/to_race_view.py), with Ascot's stall kit and gates. Distances "
                        "from the gate line along the route's inside rail; stall 1 on the inside rail.",
              "horseStandsBehind": STANDS_BEHIND, "gates": asc["gates"], "kit": asc["kit"], "maxRunners": MAX_RUNNERS,
              "unitsForField": {k: v for k, v in asc["unitsForField"].items() if int(k) <= MAX_RUNNERS}, "starts": starts}
    NM.write("york-stalls.json", stalls, 1)

    # ---- standards: par times (calibrate.mjs) and Ascot's going and pace bands
    nm = json.loads((OUT / "newmarket-july-standards.json").read_text())
    par = json.loads(PAR_FILE.read_text())["par"] if PAR_FILE.exists() else {}
    standards = {"_about": "Par (standard) times at York, DRAFT, for the race engine and the race view's dock. 'winningTime' is a rough "
                           "winning time for a good horse on good ground (from memory: check against real results); 'seconds' is the par "
                           "the engine uses, set by tools/course/york/calibrate.mjs so its winning times come out at those.",
                 "parTimes": [{"key": keys[t], "course": "straight" if s["route"] == "straight" else "round", "distance": s["distance"],
                               "seconds": par.get(keys[t], round(TARGET[t] * 0.978, 2)), "winningTime": TARGET[t]} for t, s in C["starts"].items()],
                 "going": nm["going"], "pace": nm["pace"]}
    NM.write("york-standards.json", standards, 1)

    # ---- the view: cameras as the Rowley Mile's (stands beyond the outer rail); the camera settings that are relative to the
    # track (the tracking car's side, the drone's 'across') turn round with the course's hand in the view; the fixed ones
    # (world positions) are mirrored here: York's stands are on -z
    sun = [-110, 49.5, 35.2]
    cams = NM.cameras(W, +1, [0, 16, W + 15], ([-8, 6.5, 0.8], [0, 6.0, W * 0.65]), -70.0, sun)
    mz = lambda p: [p[0], p[1], r2(-p[2])]
    cams["grandstand"]["at"] = mz(cams["grandstand"]["at"])
    cams["headon"]["at"] = mz(cams["headon"]["at"])
    cams["sideon"]["at"], cams["sideon"]["look"] = mz(cams["sideon"]["at"]), mz(cams["sideon"]["look"])
    cams["sideon"]["fov"] = [46, 46]
    cams["track_straight"]["raise"] = []
    # the racecard view: over the infield's rail lawn by the post, looking across at the stands and up the run-in
    prelude = {"label": "The runners", "seconds": 9, "eye": [[-60, 16, 26], [-45, 15, 24]],
               "at": [[150, 6, -60], [165, 6, -62]], "fov": 46, "list": [7, 0.6], "cardAfter": 3.5}
    postlude = NM.overview_after(prelude)
    director = {"tracking": True, "grandstand": 2 * F}
    menu = {"straight": [["track_straight", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]],
            "round": [["track_loop", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]]}

    class L:                                                       # what NM.view_file reads of a layout
        TRACK_W = W; RUN_ON = C["runOut"]; STRAIGHT = C["home"]
    view = NM.view_file("york", L, {"name": "York"}, stalls, -1, cams, prelude, postlude, director, menu)
    view["homeStraight"]["centreZ"] = -W / 2
    view["lanesStraight"]["x"][0] = 0.0                                # the mown lanes stop at the line: the bend starts there
    view["treeDetail"]["centre"] = [150, -W / 2]
    view["_about"] = ("The race view's cameras and dressing for York. Written by tools/course/york/to_race_view.py; don't edit by hand. "
                      "World axes as york.json (left-handed: the stands on -z).")
    view["races"]["_default"] = "1m2f"
    NM.write("york-view.json", view, 1)

    # ---- scenery: the stands, the Clock Tower and the festival side (phase 4), and the finish-line kit on the inside rail
    S, trees = york_scenery(W, course["ground"], C)
    scen = NM.scenery_file(S, trees, [], [], ["york_stands", "site_props", "finish_line"], {"at": [0, GAP], "turn": 180}, poles)
    NM.write("york-scenery.json", scen)
    print("  ", len(S.pieces), "pieces,", len(S.people) // 4, "people,", len(trees), "trees")
    print("turf area %.0f m2, %d rail lines, %d starts" % (turf.area, len(rails), len(starts)))


if __name__ == "__main__":
    main()
