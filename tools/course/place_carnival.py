"""Places the owner's carnival layout (reference/course/layout/ascot-site-plan-sketch-1.png, read in the
race-graphics handover) into courses/ascot-site-dressing.json.

World axes as courses/ascot.json: x east of the post, z south, the far (inside) rail of the home straight on
z 0, so the inner carnival is at negative z. turn 0 = the piece faces north, 180 = faces south.

Today's pieces stay (owner, 3 Nov); every new piece is checked against them, the far-side path, the track and
the pieces placed before it, and nudged along x (then a little in z) to the nearest free spot. A piece with no
free spot within reach is dropped and listed.

Re-run safely: it first removes the groups it wrote last time (names starting "carn" or "east2").
    python3 tools/course/place_carnival.py
"""
import json, math, os, random
from matplotlib.path import Path

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rp = lambda *p: os.path.join(REPO, *p)
DRESS_F = rp("courses/ascot-site-dressing.json")
DRESS = json.load(open(DRESS_F))
COURSE = json.load(open(rp("courses/ascot.json")))
CODES = json.load(open(rp("assets/models/architecture/site_props_codes.json")))["codes"]
PIECE = {k: v["piece"] for k, v in CODES.items()}
FOOT = {v["piece"]: v["footprint"] for v in CODES.values()}
CLEAR = 2.0                     # metres kept clear between pieces
OURS = ("carn", "east2")

DRESS["pieces"] = [p for p in DRESS["pieces"] if not p.get("group", "").startswith(OURS)]
DRESS["crowds"] = [c for c in DRESS["crowds"] if not c.get("group", "").startswith(OURS)]
DRESS["groups"] = {k: v for k, v in DRESS["groups"].items() if not k.startswith(OURS)}

turf = [Path(r) for r in COURSE["track"]["surface"]]
infield = turf[1]                               # the hole inside the loop


def box(piece, x, z, turn):
    """World axis-aligned box of a piece: the engine turns it by 180 + turn about y (three.js sense)."""
    f = FOOT[piece]
    th = math.pi + math.radians(turn)
    c, s = math.cos(th), math.sin(th)
    xs, zs = [], []
    for lx in (f["x0"], f["x1"]):
        for lz in (f["z0"], f["z1"]):
            xs.append(x + lx * c + lz * s)
            zs.append(z - lx * s + lz * c)
    return min(xs), min(zs), max(xs), max(zs)


def hit(a, b, gap=CLEAR):
    return not (a[2] + gap <= b[0] or b[2] + gap <= a[0] or a[3] + gap <= b[1] or b[3] + gap <= a[1])


placed = [box(p["piece"], p["x"], p["z"], p.get("turn", 0)) for p in DRESS["pieces"]]
OBST = [(-70, -26.5, 700, -21.5),               # the far-side path (keep)
        (400, 69, 640, 75)]                     # the path behind the east enclosures
STAND = (-115, 30, 412, 140)                    # the main stand and its lawn


def on_ground(b, side):
    m = 1.5 if side == "rail" else 4.0          # rail pieces stand close to the far rail
    if side == "rail":
        side = "in"
    corners = [(b[0], b[1]), (b[2], b[1]), (b[0], b[3]), (b[2], b[3])]
    if side == "in":                            # well inside the infield: 4 m off the turf
        grown = [(b[0] - m, b[1] - m), (b[2] + m, b[1] - m), (b[0] - m, b[3] + m), (b[2] + m, b[3] + m)]
        return all(infield.contains_point(c) for c in grown)
    return b[1] > 31 and not any(t.contains_point(c) for t in turf[:1] for c in corners if c[1] < 31)


dropped, out = [], []


def put(letter, x, z, turn, group, side="in", reach=24, zreach=(0,), dupe=0):
    piece = PIECE[letter]
    if dupe:                                    # skip if one of these already stands this close
        for p in DRESS["pieces"]:
            if p["piece"] == piece and abs(p["x"] - x) < dupe and abs(p["z"] - z) < dupe:
                return None
    tries = sorted({(dx, dz) for dx in range(-reach, reach + 1) for dz in zreach}, key=lambda t: (abs(t[0]) + 3 * abs(t[1]), t))
    for dx, dz in tries:
        b = box(piece, x + dx, z + dz, turn)
        if not on_ground(b, side) or any(hit(b, o, 0.5) for o in OBST) or hit(b, STAND, 1):
            continue
        if any(hit(b, o) for o in placed):
            continue
        placed.append(b)
        p = {"piece": piece, "x": round(x + dx, 2), "z": round(z + dz, 2), "turn": turn, "group": group}
        DRESS["pieces"].append(p)
        out.append(p)
        return p
    dropped.append((letter, x, z, group))
    return None


def front_z(letter, front):
    """Centre z for a south-facing piece whose front edge is on z = front."""
    return round(front - FOOT[PIECE[letter]]["z1"], 2)


def back_z(letter, front):
    """Centre z for a north-facing piece (turn 0) whose front edge is on z = front."""
    return round(front + FOOT[PIECE[letter]]["z1"], 2)


# ---- inner carnival (north of the far rail) ----
# front row: open (E) and covered (F) seating stands, fronts 6 m behind the far rail, facing the track
for letter, x in sorted([("E", 125), ("E", 215), ("E", 300), ("E", 375), ("E", 455),
                         ("F", 170), ("F", 255), ("F", 335), ("F", 415)], key=lambda t: t[1]):
    put(letter, x, front_z(letter, -6.0), 180, "carn_front", reach=12)
# back row: three-peak marquees (A) and big tops (C) alternating, 30-40 m in, facing the track
for letter, x in sorted([("A", 10), ("A", 165), ("A", 305), ("A", 450), ("A", 600),
                         ("C", 95), ("C", 240), ("C", 385), ("C", 525)], key=lambda t: t[1]):
    put(letter, x, -35.0 if letter == "A" else -39.5, 180, "carn_back", reach=30, zreach=(0, -2, 2, -4))
# pagoda counters (D) between the rows, facing the path
for x in (145, 185, 270, 335, 415, 485, 555, 575, 600):
    put("D", x, -18.5, 0, "carn_mid", reach=14)
for x in (-70, -48, -25):                       # by the bend
    put("D", x, -33.0, 180, "carn_mid", reach=14, zreach=(0, 3, -3))
# terrace decks (G) along the far rail before the post, viewing towers (H) dotted along the far rail
for x in (-95, -73, -51, -30):
    put("G", x, front_z("G", -6.0), 180, "carn_rail", reach=10, zreach=(0, -3, -6))
for x in (-90, 18, 95, 260, 510):
    put("H", x, front_z("H", -2.5), 180, "carn_rail", side="rail", reach=20, dupe=12)

# ---- east of the stand (south of the near rail), facing the track (north) ----
for letter, x in [("H", 415), ("D", 445), ("G", 462), ("D", 480), ("G", 497), ("D", 515), ("F", 535),
                  ("H", 535), ("G", 552), ("D", 568), ("G", 585), ("D", 600), ("G", 617), ("H", 665)]:
    put(letter, x, back_z(letter, 46.0), 0, "east2_front", side="out", reach=14, zreach=(0, 4, 8, -4))
for letter, x in [("A", 425), ("C", 465), ("A", 500), ("C", 520), ("A", 550), ("C", 585), ("A", 615)]:
    put(letter, x, 80.0 if letter == "A" else 86.0, 0, "east2_back", side="out", reach=20, zreach=(0, 3, 6))

# ---- the small pieces and flags, dotted round both areas ----
rng = random.Random(1103)


def dot(letters, x0, x1, bands, group, side, n_per_100):
    """Spread pieces evenly along x (one per slot, jittered), each in a band (z0, z1, turn)."""
    n = max(1, round((x1 - x0) * n_per_100 / 100))
    for k in range(n):
        x = x0 + (k + rng.uniform(0.15, 0.85)) * (x1 - x0) / n
        z0, z1, turn = rng.choice(bands)
        letter = rng.choice(letters)
        put(letter, round(x, 1), round(rng.uniform(z0, z1), 1), turn + rng.choice((0, 0, 15, -15)), group, side, reach=8, zreach=(0, 3, -3))


# inner: kiosks, huts, arched rows, pagoda kiosks and pergolas along both sides of the path and round the back row
INNER_BANDS = [(-14.5, -19.5, 0), (-29.0, -31.0, 180), (-46.0, -50.0, 180)]
dot("IIJJKLLM", -60, 620, INNER_BANDS, "carn_dots", "in", 4.2)
dot("UUV", -60, 620, INNER_BANDS, "carn_flags", "in", 3.0)
dot("V", 100, 480, [(-2.2, -2.8, 180)], "carn_flags", "rail", 4.0)     # banner flags along the far rail
# east: the same mix round the enclosures
EAST_BANDS = [(38, 42, 0), (58, 66, 0), (90, 98, 0)]
dot("IJJKLLM", 415, 680, EAST_BANDS, "east2_dots", "out", 4.0)
dot("UUV", 415, 680, EAST_BANDS, "east2_flags", "out", 4.0)

# ---- crowds round the new pieces (the old figures) ----
DRESS["crowds"] += [      # owner, 3 Nov: "it wants to feel like a crowd, not a few folks" (density = people per square metre);
                          # then: nobody further back than the back row; those people moved to the rail
    {"note": "far rail in front of the carnival's seating stands, packed", "x": [110, 470], "z": [-5.6, -1.4], "density": 1.6, "group": "carn"},
    {"note": "far rail on east of the seating stands", "x": [470, 615], "z": [-5.6, -1.4], "density": 1.4, "group": "carn"},
    {"note": "far rail by the terraces before the post", "x": [-100, -20], "z": [-4.8, -1.6], "density": 0.8, "group": "carn"},
    {"note": "round the terraces before the post", "x": [-100, -20], "z": [-20, -5], "density": 0.2, "group": "carn"},
    {"note": "thronging between the seating stands and the counters", "x": [110, 615], "z": [-21.0, -6.5], "density": 0.32, "group": "carn"},
    {"note": "along the carnival path", "x": [-40, 620], "z": [-26.5, -21.5], "density": 0.45, "group": "carn"},
    {"note": "in front of the marquees and big tops", "x": [-20, 615], "z": [-31.0, -26.5], "density": 0.4, "group": "carn"},
    {"note": "round the counters by the bend", "x": [-80, -15], "z": [-38, -27], "density": 0.25, "group": "carn"},
    {"note": "east of the stand, among the new pieces", "x": [415, 670], "z": [36, 60], "density": 0.15, "group": "east2"},
]
# Nobody stands inside a piece: the footprint of every piece (world box, 0.6 m margin) for the viewer to keep
# crowd-area people out of.
DRESS["keepClear"] = [[round(b[0] - 0.6, 1), round(b[1] - 0.6, 1), round(b[2] + 0.6, 1), round(b[3] + 0.6, 1)]
                      for b in (box(p["piece"], p["x"], p["z"], p.get("turn", 0)) for p in DRESS["pieces"])]
DRESS["groups"].update({
    "carn_front": "carnival front row: seating stands 6 m behind the far rail, facing the track (owner's sketch 1)",
    "carn_back": "carnival back row: three-peak marquees and big tops 30-40 m in",
    "carn_mid": "pagoda counters between the carnival rows, and by the bend",
    "carn_rail": "terrace decks and viewing towers along the far rail",
    "carn_dots": "small pieces dotted round the carnival", "carn_flags": "flags dotted round the carnival",
    "east2_front": "east of the stand, front line (owner's sketch 1)", "east2_back": "east of the stand, back row of marquees and big tops",
    "east2_dots": "small pieces dotted east of the stand", "east2_flags": "flags dotted east of the stand"})
DRESS["anchor"]["carnival"] = ("3 Nov 2026: the owner's layout sketch 1 placed by tools/course/place_carnival.py "
                               "(groups carn_* and east2_*); today's earlier pieces kept, new ones nudged clear of them.")

json.dump(DRESS, open(DRESS_F, "w"), indent=1)
by = {}
for p in out:
    by[p["group"]] = by.get(p["group"], 0) + 1
print("placed", len(out), by)
print("dropped", len(dropped), dropped)
