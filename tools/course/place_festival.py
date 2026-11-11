"""Ascot's festival side, re-laid (owner, 11 Nov 2026): the inner carnival inside the home straight.

    python3 tools/course/place_festival.py

The owner's brief:
  - hot air balloons (the balloon dining pods, as at the Rowley Mile) round the 2f pole, close to the track;
  - bunting and flags;
  - no tall trees in the middle of the course;
  - the larger pavilions (three-peak marquees, glazed clearspans, big tops) in a near-continuous line form the
    festival's back edge, the visual edge seen from the stands;
  - low planting, and small clusters of smaller trees (his photo of the Royal Ascot enclosures from above).

What it writes
  courses/ascot-site-dressing.json   the carnival groups (names starting "carn" or "fest") replaced; every other group
                                     kept as it is (the far-side enclosure by the post, east of the stand, past the post)
  courses/ascot-view.json            "trees": the loose-tree areas in the infield taken out (tall trees there);
                                     "festival": the festival's own planting and bunting, worked out here so the site plan
                                     and the race view agree: small trees [x, z, tree, scale, turn], low planting
                                     [x, z, bush, scale, turn, squash], bunting runs {pts, h, pole}
  and copies both to race-view/assets/course/.

World axes as courses/ascot.json: x east of the post, z south, the inside rail of the home straight on z 0, the
festival at negative z. turn 0 = the piece faces north, 180 = faces south (towards the track and the stands).
"""
import json, math, os, random, shutil
from matplotlib.path import Path

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rp = lambda *p: os.path.join(REPO, *p)
DRESS_F, VIEW_F = rp("courses/ascot-site-dressing.json"), rp("courses/ascot-view.json")
DRESS, VIEW = json.load(open(DRESS_F)), json.load(open(VIEW_F))
COURSE = json.load(open(rp("courses/ascot.json")))
CODES = json.load(open(rp("assets/models/architecture/site_props_codes.json")))["codes"]
PIECE = {k: v["piece"] for k, v in CODES.items()}
FOOT = {v["piece"]: v["footprint"] for v in CODES.values()}
HEIGHT = {v["piece"]: v["height"] for v in CODES.values()}
CLEAR = 2.0
OURS = ("carn", "fest")

DRESS["pieces"] = [p for p in DRESS["pieces"] if not p.get("group", "").startswith(OURS)]
DRESS["crowds"] = [c for c in DRESS["crowds"] if not c.get("group", "").startswith(OURS)]
DRESS["groups"] = {k: v for k, v in DRESS["groups"].items() if not k.startswith(OURS)}

turf = [Path(r) for r in COURSE["track"]["surface"]]
infield = turf[1]
RAILS = COURSE["rails"]["lines"]


def box(piece, x, z, turn):
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
OBST = [(-70, -26.5, 700, -21.5)]               # the festival path (kept: it is in the ground bake's paths)


def in_field(b, m):
    grown = [(b[0] - m, b[1] - m), (b[2] + m, b[1] - m), (b[0] - m, b[3] + m), (b[2] + m, b[3] + m)]
    return all(infield.contains_point(c) for c in grown)


dropped, out = [], []


def put(letter, x, z, turn, group, margin=4.0, reach=12, zreach=(0,), gap=CLEAR):
    piece = PIECE[letter]
    tries = sorted({(dx, dz) for dx in range(-reach, reach + 1) for dz in zreach}, key=lambda t: (abs(t[0]) + 3 * abs(t[1]), t))
    for dx, dz in tries:
        b = box(piece, x + dx, z + dz, turn)
        if not in_field(b, margin) or any(hit(b, o, 0.5) for o in OBST) or any(hit(b, o, gap) for o in placed):
            continue
        placed.append(b)
        p = {"piece": piece, "x": round(x + dx, 2), "z": round(z + dz, 2), "turn": turn, "group": group}
        DRESS["pieces"].append(p); out.append(p)
        return p
    dropped.append((letter, x, z, group))
    return None


def front_z(letter, front):
    """Centre z for a piece facing the track (turn 180) whose front edge is on z = front."""
    return round(front - FOOT[PIECE[letter]]["z1"], 2)


# ------------------------------------------------------------------ the pieces
# 1. Balloon dining pods round the 2f pole (x 402), close to the track: a staggered line, fronts 8 and 12 m behind the
#    inside rail, with the rail crowd in front of them.
BALLOON_X = [362 + 10.5 * k for k in range(9)]
for k, x in enumerate(BALLOON_X):
    put("X", x, -10.6 if k % 2 == 0 else -14.6, 180, "fest_balloons", margin=1.5, reach=2, gap=1.5)

# 2. The front row: open and covered seating stands, fronts 6 m behind the rail (as before), clear of the balloons
for letter, x in [("E", 125), ("F", 170), ("E", 215), ("F", 255), ("E", 300), ("F", 335), ("E", 475), ("F", 540)]:
    put(letter, x, front_z(letter, -6.0), 180, "fest_front", margin=1.5, reach=10)
# viewing towers along the rail, in the gaps
for x in (-90, 95, 278, 510):          # (none further east: the grandstand camera looks past here to the bend)
    put("H", x, front_z("H", -2.5), 180, "fest_front", margin=1.5, reach=12)
# terrace decks along the rail before the post (as before)
for x in (-95, -73, -51, -30):
    put("G", x, front_z("G", -6.0), 180, "fest_front", margin=1.5, reach=10, zreach=(0, -3, -6))

# 3. Pagoda counters facing the path from the south (as before, none in the balloons' stretch)
for x in (145, 190, 270, 330, 460, 495, 560, 610):
    put("D", x, -18.5, 0, "fest_mid", reach=8)
for x in (-70, -48):
    put("D", x, -33.0, 180, "fest_mid", reach=10, zreach=(0, 3, -3))

# 4. The back edge: the big pavilions in a near-continuous line, fronts on z -42, facing the track. A flagpole stands
#    in each gap. (The far-side enclosure's big top at x 52, kept, takes its place in the line.)
EDGE_FRONT = -42.0
PATTERN = "ACBACABCAB"
x, k = -64.0, 0
edge = []
while x < 650:
    letter = PATTERN[k % len(PATTERN)]
    w = CODES[letter]["width"]
    cx = x + w / 2
    p = put(letter, cx, front_z(letter, EDGE_FRONT), 180, "fest_edge", reach=6, zreach=(0, -2, -4))
    if p:
        b = box(p["piece"], p["x"], p["z"], 180)
        edge.append(b)
        x = b[2] + 6.0
        k += 1
    else:
        x += 8.0                                   # something kept stands here (the far-side big top): step past it
for a, b in zip(edge, edge[1:]):                   # flags in the gaps
    gx = (a[2] + b[0]) / 2
    if b[0] - a[2] < 12:
        put("U", gx, EDGE_FRONT - 1.5, 180, "fest_flags", reach=1, zreach=(0, -1, 1), gap=0.6)

# 5. The garden between the path and the pavilions: terrace decks, pergolas, kiosks and picnic tables, spaced out
rng = random.Random(1111)
GARDEN = [("G", 120), ("M", 160), ("I", 196), ("G", 232), ("L", 262), ("M", 300), ("G", 352), ("I", 390), ("M", 425),
          ("G", 468), ("L", 500), ("M", 536), ("G", 575), ("I", 610), ("M", -20), ("L", 0), ("I", 88)]
for letter, x in GARDEN:
    put(letter, x, -33.0, 180, "fest_garden", reach=10, zreach=(0, -2, 2))
for x in range(110, 640, 28):                      # picnic tables round the garden pieces
    put("N", x + rng.uniform(-6, 6), rng.uniform(-30.5, -38.5), rng.choice((0, 90, 180)), "fest_garden", reach=6, zreach=(0, -2, 2), gap=1.5)
# kiosks and huts along the south side of the path
for x in (115, 232, 290, 352, 452, 528, 588):
    put(rng.choice("IJK"), x, -18.0, 0, "fest_mid", reach=8, gap=1.6)

# 6. Flags: banner flags along the rail (in front of everything) and flagpoles along the path
for x in range(105, 640, 24):
    put("V", x + rng.uniform(-4, 4), -2.6, 180, "fest_flags", margin=1.0, reach=4, gap=0.6)
for x in range(-40, 640, 34):
    put("U", x + rng.uniform(-5, 5), -28.6, 180, "fest_flags", reach=5, gap=0.8)

# ------------------------------------------------------------------ planting and small trees
def dist_rails(x, z):
    best = 1e9
    for line in RAILS:
        for (ax, az), (bx, bz) in zip(line, line[1:]):
            dx, dz = bx - ax, bz - az
            L2 = dx * dx + dz * dz or 1
            t = max(0, min(1, ((x - ax) * dx + (z - az) * dz) / L2))
            best = min(best, math.hypot(x - ax - t * dx, z - az - t * dz))
    return best


def free(x, z, r, track=30.0):
    """A plant of radius r at (x, z): in the infield, track metres off every rail, clear of the pieces and the path."""
    if not infield.contains_point((x, z)) or dist_rails(x, z) < track:
        return False
    b = (x - r, z - r, x + r, z + r)
    return not any(hit(b, o, 0.8) for o in placed + OBST)


trees, shrubs, beds = [], [], []
SMALL = ["oak_a", "oak_b", "wide_a", "oak_c"]
BUSH = ["bush_a", "bush_b"]


def bush(x, z, s=None, squash=None):
    s = s or rng.uniform(0.3, 0.42)
    shrubs.append([round(x, 2), round(z, 2), rng.choice(BUSH), round(s, 3), round(rng.uniform(0, 360)), round(squash or rng.uniform(0.62, 0.8), 2)])


def bed(x0, x1, z, rows=2, every=1.55, track=30.0):
    """A low planting bed along x (one or two staggered rows of small rounded shrubs), broken wherever a piece stands."""
    run = []
    x = x0
    while x <= x1:
        for r in range(rows):
            zz = z - r * 1.3
            xx = x + (every / 2 if r else 0) + rng.uniform(-0.25, 0.25)
            if free(xx, zz, 1.0, track):
                bush(xx, zz + rng.uniform(-0.2, 0.2))
                run.append((xx, zz))
        x += every
    if run:
        beds.append((min(p[0] for p in run) - 1, min(p[1] for p in run) - 1, max(p[0] for p in run) + 1, max(p[1] for p in run) + 1))


def cluster(cx, cz, n_trees, s=(0.45, 0.62), n_bush=(2, 5), spread=7.0, track=30.0):
    """A small clump of smaller trees with a few shrubs at their feet."""
    got = 0
    for _ in range(n_trees * 4):
        if got >= n_trees:
            break
        x, z = cx + rng.uniform(-spread, spread), cz + rng.uniform(-spread * 0.7, spread * 0.7)
        if free(x, z, 3.0, track) and all(math.hypot(x - t[0], z - t[1]) > 5.0 for t in trees):
            trees.append([round(x, 2), round(z, 2), rng.choice(SMALL), round(rng.uniform(*s), 3), round(rng.uniform(0, 360))])
            got += 1
    for _ in range(rng.randint(*n_bush) if got else 0):
        x, z = cx + rng.uniform(-spread - 2, spread + 2), cz + rng.uniform(-spread, spread)
        if free(x, z, 1.0, track):
            bush(x, z, rng.uniform(0.34, 0.5))
    return got


# (a) beds along the north edge of the path, broken for the way through to each garden piece
for x0 in range(-50, 640, 26):
    bed(x0 + 2, x0 + 2 + rng.uniform(9, 15), -28.4, rows=1, track=20.0)
# (b) a few single small trees and pairs in the garden, between the pieces (kept low: under the pavilions' ridges)
for x in range(-30, 640, 38):
    cluster(x + rng.uniform(-8, 8), -36.0, rng.choice((1, 1, 2)), s=(0.4, 0.5), n_bush=(1, 3), spread=4.0, track=20.0)
# (c) behind the pavilion line: a continuous low bed (two rows) with gaps, then clumps of small trees
for x0 in range(-60, 650, 48):
    bed(x0, x0 + rng.uniform(30, 40), -66.0, rows=2)
for x in range(-50, 650, 30):
    cluster(x + rng.uniform(-6, 6), rng.uniform(-74, -88), rng.choice((2, 3, 3, 4)))
# (d) the rest of the infield: scattered small clumps and drifts of low planting, nothing tall (the inside of the home
#     bend 20 m off the rail, as before: the tracking car runs 12 m inside the rail)
for gz in range(-110, -730, -44):
    for gx in range(-150, 735, 44):
        x, z = gx + rng.uniform(-14, 14), gz + rng.uniform(-14, 14)
        if rng.random() < 0.5:
            continue
        track = 20.0 if x > 520 else 30.0
        if rng.random() < 0.3:
            for _ in range(rng.randint(4, 9)):
                if free(x, z, 1.0, track):
                    bush(x, z, rng.uniform(0.34, 0.5))
                x += rng.uniform(1.4, 2.2); z += rng.uniform(-0.8, 0.8)
        else:
            cluster(x, z, rng.choice((2, 3, 3, 4)), s=(0.45, 0.68), track=track)

# ------------------------------------------------------------------ bunting
bunting = []
# zig-zags across the festival path on poles either side of it, 4.2 m up
xs = list(range(100, 640, 13))
ps = [[x, -21.2 if i % 2 == 0 else -26.8] for i, x in enumerate(xs)]
run = []
for x, z in ps:
    b = (x - 0.3, z - 0.3, x + 0.3, z + 0.3)
    if any(hit(b, o, 0.3) for o in placed):
        if len(run) > 1: bunting.append({"pts": run, "h": 4.2, "pole": True})
        run = []
    else:
        run.append([x, z])
if len(run) > 1: bunting.append({"pts": run, "h": 4.2, "pole": True})
# along the front of the rail crowd, 3.6 m up, on poles 6.4 m back from the rail
run = []
for x in range(-20, 650, 15):
    b = (x - 0.3, -6.7, x + 0.3, -6.1)
    if any(hit(b, o, 0.3) for o in placed):
        if len(run) > 1: bunting.append({"pts": run, "h": 3.6, "pole": True})
        run = []
    else:
        run.append([x, -6.4])
if len(run) > 1: bunting.append({"pts": run, "h": 3.6, "pole": True})
# from balloon pod to balloon pod, on the corners of their frames (3.5 m)
pods = [p for p in out if p["piece"] == "balloon_pod"]
pods.sort(key=lambda p: p["x"])
for a, b in zip(pods, pods[1:]):
    bunting.append({"pts": [[a["x"] + 2.1, a["z"] - 2.1], [b["x"] - 2.1, b["z"] - 2.1]], "h": 3.45, "pole": False})

# ------------------------------------------------------------------ crowds (people per square metre)
DRESS["crowds"] += [
    {"note": "far rail in front of the seating stands and balloons, packed", "x": [110, 470], "z": [-5.6, -1.4], "density": 1.6, "group": "fest"},
    {"note": "far rail east of the balloons", "x": [470, 615], "z": [-5.6, -1.4], "density": 1.4, "group": "fest"},
    {"note": "far rail by the terraces before the post", "x": [-100, -20], "z": [-4.8, -1.6], "density": 0.8, "group": "fest"},
    {"note": "far rail at the finish, between the terraces and the seating stands", "x": [-20, 110], "z": [-5.2, -1.4], "density": 1.4, "group": "fest"},
    {"note": "behind the far rail crowd at the finish", "x": [-20, 110], "z": [-13, -5.2], "density": 0.3, "group": "fest"},
    {"note": "round the terraces before the post", "x": [-100, -20], "z": [-20, -5], "density": 0.2, "group": "fest"},
    {"note": "thronging between the seating stands, the balloons and the counters", "x": [110, 615], "z": [-21.0, -6.5], "density": 0.32, "group": "fest"},
    {"note": "along the festival path", "x": [-40, 630], "z": [-26.5, -21.5], "density": 0.45, "group": "fest"},
    {"note": "in the garden in front of the pavilions", "x": [-40, 630], "z": [-41.0, -27.5], "density": 0.3, "group": "fest"},
    {"note": "round the counters by the bend", "x": [-80, -15], "z": [-38, -27], "density": 0.25, "group": "fest"},
]
DRESS["keepClear"] = [[round(b[0] - 0.6, 1), round(b[1] - 0.6, 1), round(b[2] + 0.6, 1), round(b[3] + 0.6, 1)]
                      for b in (box(p["piece"], p["x"], p["z"], p.get("turn", 0)) for p in DRESS["pieces"])]
DRESS["keepClear"] += [[round(b[0], 1), round(b[1], 1), round(b[2], 1), round(b[3], 1)] for b in beds]
DRESS["keepClear"] += [[round(t[0] - 1.2, 1), round(t[1] - 1.2, 1), round(t[0] + 1.2, 1), round(t[1] + 1.2, 1)] for t in trees if t[1] > -45]
DRESS["groups"].update({
    "fest_balloons": "festival: balloon dining pods round the 2f pole, close to the track (owner, 11 Nov)",
    "fest_front": "festival: seating stands, viewing towers and terrace decks along the inside rail",
    "fest_mid": "festival: pagoda counters and kiosks on the south side of the path",
    "fest_edge": "festival: the big pavilions in a line, its back edge (owner, 11 Nov)",
    "fest_garden": "festival: the garden between the path and the pavilions",
    "fest_flags": "festival: flagpoles and banner flags"})
DRESS["anchor"]["carnival"] = ("11 Nov 2026: the festival side re-laid by tools/course/place_festival.py (groups fest_*): balloons at "
                               "2f, the big pavilions as the back edge, low planting and small trees in the view file's 'festival'.")

# ------------------------------------------------------------------ the view file
INFIELD_AREAS = ("right behind the carnival", "behind those, thinning", "clumps in the infield", "infield inside the bend",
                 "the infield inside the home bend", "along the inside of the home bend")
before = len(VIEW["trees"])
VIEW["trees"] = [a for a in VIEW["trees"] if not any(k in a["note"] for k in INFIELD_AREAS)]
VIEW["festival"] = {
    "_about": ("Owner, 11 Nov 2026: no tall trees in the middle of the course; low planting and small clusters of smaller "
               "trees; bunting. Written by tools/course/place_festival.py. trees: [x, z, tree, scale, turn] (the clay "
               "trees at about half size, 6-9 m); shrubs: [x, z, bush, scale, turn, squash] (low rounded planting about a metre "
               "high); bunting: runs of pennants on a line between points 'h' metres up, on poles unless pole is false."),
    "trees": "@@trees@@", "shrubs": "@@shrubs@@", "bunting": "@@bunting@@"}
json.dump(DRESS, open(DRESS_F, "w"), indent=1)
text = json.dumps(VIEW, indent=1)
for key, items in (("trees", trees), ("shrubs", shrubs), ("bunting", bunting)):   # one line per item keeps the file readable
    text = text.replace('"@@%s@@"' % key, "[\n" + ",\n".join("   " + json.dumps(i, separators=(",", ":")) for i in items) + "\n  ]")
open(VIEW_F, "w").write(text)
VIEW["festival"].update(trees=trees, shrubs=shrubs, bunting=bunting)
for f in ("ascot-site-dressing.json", "ascot-view.json"):
    shutil.copy2(rp("courses", f), rp("race-view/assets/course", f))
by = {}
for p in out:
    by[p["group"]] = by.get(p["group"], 0) + 1
print("placed", len(out), by)
print("dropped", len(dropped), dropped)
print("tree areas %d -> %d; small trees %d, shrubs %d, beds %d, bunting runs %d" % (before, len(VIEW["trees"]), len(trees), len(shrubs), len(beds), len(bunting)))
