"""Newmarket's July Course: a DRAFT layout for the owner to check before anything is modelled (8 Nov 2026).

Interpretive, from the owner's references (reference/newmarket-july/): his sketch of the two Newmarket courses (where
each course's stands, festival areas and the Dyke sit, the direction of travel and the main stand camera), the aerial
view, the course's enclosure map, the stands, his notes on the undulations and his video of the Bahrain Trophy. Not
surveyed: every number below is a choice, named, so it can be changed in one place.

Built together with the Rowley Mile by site_plan.py (run that), which places this course beside it, keeps either
course's trees, boards and banks off the other, and writes:
        courses/newmarket-july-draft.json        the layout as data
        courses/newmarket-july-stalls.json       the starting stalls, for the race engine and the race view
        courses/newmarket-july-standards.json    par times, for the race engine
        reference/newmarket-july/plan-draft.png  the run-in close up, two cross-sections and the height profile

Axes, the same rules as Ascot and the Rowley Mile: origin = the winning post on the inside rail; y up. On the straight
the horses run towards -x with the inside rail on their right (z = 0) and the track to their left (z 0 to TRACK_W).
Right-handed: races over a mile come down the Cesarewitch leg and turn right into the July straight (the Bunbury
Mile). Unlike the Rowley Mile, the stands here are on the INSIDE, behind the inside rail (z < 0, the horses' right),
and the far side (z > TRACK_W, the horses' left) faces the Rowley Mile across the Dyke (owner's sketch, 8 Nov).
"""
import json, math, random
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
F = 201.168                                   # a furlong, metres

# ---------------------------------------------------------------- the course (change here)
TRACK_W = 34.0          # wide and galloping, a touch narrower than the Rowley Mile's 36
STRAIGHT = 8 * F        # the Bunbury Mile: everything up to a mile is run straight
SPLAY = 25.0            # owner's sketch: the July straight runs off at about 25 degrees to the Rowley Mile's
LEG_ANGLE = 62.0 + SPLAY   # so the turn off the Cesarewitch leg is the Rowley Mile's 62 degrees plus that: 87
BEND_R = 180.0          # the bend's inside-rail radius
RUN_ON = 300.0          # the run-out: the straight carries on past the post (owner, 8 Nov: extend it)
TRIPS = {"5f": 5, "6f": 6, "7f": 7, "1m": 8, "1m2f": 10, "1m4f": 12, "1m5f": 13, "1m6f": 14, "2m": 16}
# The ground (owner's notes): the first three-quarters of the straight mile roll; after the first two furlongs it runs
# downhill for about a furlong (6f to 5f out); then a steep, sustained climb over the last two furlongs to the line.
# Heights in metres against the post, by metres to go; smooth between. The leg rises towards the far starts.
PROFILE = [(-RUN_ON, 0.8), (-150, 0.5), (0, 0.0), (100, -1.3), (201, -2.4), (300, -3.1), (402, -3.4), (500, -3.0), (603, -2.4),
           (700, -2.7), (805, -2.0), (900, -2.3), (1006, -1.8), (1207, 0.6), (1300, 0.9), (1408, 0.5), (1500, 0.9),
           (STRAIGHT, 0.8), (1900, 1.6), (2400, 3.0), (3000, 4.5), (3600, 6.0)]
COMPASS = "owner's sketch, 8 Nov: in courses/newmarket-site.json north is at the bottom of the plans (+z north, +x west)"

# ---------------------------------------------------------------- the stand side: behind the inside rail (z < 0)
# Owner: "a series of grandstands with crowds in and around", then festival pieces on the stand side towards 3/4f
# (his sketch: the stands from about the post up the course, a smaller festival area beyond them). Each stand: x from,
# x to (metres along the straight, + up the course), depth, height; the fronts STAND_BACK metres behind the inside rail,
# behind a packed lawn. Low heritage stands (red brick ends, timber canopy roofs, a red judge's box on top of one).
STAND_BACK = 16.0
STANDS = [
    {"name": "Garden stand", "x": [-110, -62], "depth": 22, "height": 12},
    {"name": "Grandstand", "x": [-50, 36], "depth": 28, "height": 16, "note": "the winning line in front of it"},
    {"name": "Judge's box stand", "x": [48, 128], "depth": 26, "height": 17, "note": "the red judge's box tower on its roof"},
    {"name": "Premier stand", "x": [140, 240], "depth": 30, "height": 18},
    {"name": "Paddock stand", "x": [252, 330], "depth": 22, "height": 13},
]
LAWN = {"x": [-120, 340], "z": [-(STAND_BACK - 1), -2.0], "note": "the lawns between the stands and the rail, packed, coloured umbrellas"}
FESTIVAL = {"x": [345, 3.5 * F], "z": [-62.0, -10.0],
            "note": "stand-side festival pieces from the end of the stands to 3.5f out: food and drink stalls, bars, umbrellas, "
                    "picnic lawns; 10 m back from the rail, leaving a lane for the tracking car; a few shade trees"}
PADDOCK = {"x": [-100, 330], "z": [-170.0, -60.0], "note": "behind the stands: the parade rings and buildings among trees (barely seen)"}
# ---------------------------------------------------------------- the far side: beyond the outer rail (z > TRACK_W)
# Owner: "a series of marquees etc nestled in the trees with crowd in front, and a tier structure behind the finish";
# then (8 Nov, on the second draft) the far-side festival runs from about 3f out to the finish, opposite the stands, with
# nice big trees, and the Dyke moved back to make room. Distances on this side are metres beyond the OUTER rail ('off').
FAR_FESTIVAL = {"x": [-60, 610], "off": [12.0, 92.0], "note": "marquees and pavilions among big trees, from 3f out to just past the post"}
FAR_CROWD = {"x": [-50, 600], "off": [4.0, 12.0], "note": "the crowd in front of them, along the far rail"}
TIER = {"name": "Tiered stand", "x": [-25, 30], "off": [14.0, 32.0], "height": 9,
        "note": "behind the finish as the stand camera sees it: open tiers facing the track, opposite the line"}
PAVILIONS = [
    {"name": "Pavilion 1", "x": [42, 94], "off": [16, 34], "height": 8, "kind": "long marquee"},
    {"name": "Pavilion 2", "x": [108, 132], "off": [16, 30], "height": 7, "kind": "pagoda marquee"},
    {"name": "Pavilion 3", "x": [146, 200], "off": [17, 35], "height": 8, "kind": "three-peak marquee"},
    {"name": "Pavilion 4", "x": [216, 252], "off": [16, 30], "height": 7, "kind": "white pitched-roof pavilion"},
    {"name": "Pavilion 5", "x": [266, 290], "off": [16, 30], "height": 7, "kind": "pagoda marquee"},
    {"name": "Pavilion 6", "x": [304, 360], "off": [16, 34], "height": 8, "kind": "long marquee"},
    {"name": "Pavilion 7", "x": [376, 412], "off": [16, 30], "height": 7, "kind": "white pitched-roof pavilion"},
    {"name": "Pavilion 8", "x": [428, 452], "off": [16, 30], "height": 7, "kind": "pagoda marquee"},
    {"name": "Pavilion 9", "x": [468, 524], "off": [17, 35], "height": 8, "kind": "three-peak marquee"},
    {"name": "Pavilion 10", "x": [540, 576], "off": [16, 30], "height": 7, "kind": "white pitched-roof pavilion"},
    {"name": "Pavilion 11", "x": [70, 130], "off": [52, 72], "height": 8, "kind": "long marquee"},
    {"name": "Pavilion 12", "x": [236, 296], "off": [52, 72], "height": 8, "kind": "long marquee"},
    {"name": "Pavilion 13", "x": [404, 454], "off": [52, 70], "height": 7, "kind": "white pitched-roof pavilion"},
]
# The Dyke's face behind the far side (owner: "the dyke should be on the far rail" opposite the grandstands; his sketch:
# between the two courses, behind the far-side festival). Behind the festival it stands back; up the straight it comes in
# to the Rowley Mile's distance. Metres beyond the outer rail: foot, crest, back; height. Between the two courses the
# Dyke's top is drawn in courses/newmarket-site.json.
BANK_NEAR = {"foot": 96.0, "crest": [108.0, 116.0], "back": 132.0, "height": 4.5, "upTo": 640.0}
BANK_FAR = {"foot": 12.0, "crest": [28.0, 34.0], "back": 50.0, "height": 4.0, "from": 860.0}
BANK = {"from": -380.0, "to": 5.5 * F}       # his sketch: the Dyke runs from beyond the post to about 5f out
BANK_SKIP = []          # set by site_plan.py: stretches (metres to go) where the Rowley Mile is too close
KEEP = None             # set by site_plan.py: KEEP(x, z) -> False to leave a tree or board out
# Advertising boards: far side only. A long sponsor run along the far rail at the finish (in front of the crowd), then
# short runs dotted up the straight. Each run: metres to go at its middle, how many 6 m boards.
BOARD_LEN, BOARDS_BEYOND = 6.0, 2.5
BOARD_RUNS = [(30, 18), (300, 5), (520, 4), (800, 5), (1050, 3), (1300, 4)]
BOARD_DESIGNS = ["green", "cream", "navy", "white"]
# Trees: "a much leafier" course, but only where the cameras look (owner, 8 Nov: lose the trees behind the grandstand,
# be selective for the key views). The far side is what every camera looks at: big trees among the festival there. On
# the stand side the cameras look away, so trees stay only where the head-on long lens (beyond the line, looking up the
# straight) or the drone ahead of the leaders sees them: in HEAD_ON's view cone, and never behind the stands.
TREE_KINDS = {"oak_a": 3, "oak_b": 3, "oak_c": 3, "wide_a": 3, "wide_b": 3, "poplar_a": 1}
TREE_SPACING, TREE_SEED, TREE_SCALE = 7.5, 11, [1.0, 1.7]
BIG_TREES = [1.5, 2.3]                    # the far-side festival's trees (crowns about 15 to 24 m high)
HEAD_ON = {"at": [-RUN_ON + 40, TRACK_W / 2, 4.0], "halfAngle": 16.0,
           "note": "the head-on long lens beyond the line, in the middle of the run-out, looking up the straight"}
KEY_CAMERAS = {
    "standCamera": {"at": [0, -(STAND_BACK + 2), 12], "looks": "across the track to the far side"},
    "trackingCar": {"lane": -5.0, "height": 3.0, "looks": "across the track to the far side, from the stand side"},
    "headOn": HEAD_ON,
    "drone": {"across": -3.0, "height": 15.0, "looks": "back up the straight at the field, from over the stand side"},
}


# ---------------------------------------------------------------- the path
TURN = math.radians(LEG_ANGLE)
CX, CZ = STRAIGHT, -BEND_R
BEND_LEN = BEND_R * TURN


def course_pt(d):
    """Inside-rail point and running direction at d metres to go (d may run past the post, negative)."""
    if d <= STRAIGHT:
        return (d, 0.0), (-1.0, 0.0)
    s = d - STRAIGHT
    if s <= BEND_LEN:
        a = s / BEND_R
        return (CX + BEND_R * math.sin(a), CZ + BEND_R * math.cos(a)), (-math.cos(a), math.sin(a))
    ex, ez = CX + BEND_R * math.sin(TURN), CZ + BEND_R * math.cos(TURN)
    k = s - BEND_LEN
    ux, uz = math.cos(TURN), -math.sin(TURN)
    return (ex + ux * k, ez + uz * k), (-ux, -uz)


def inside(d, off):
    """'off' metres behind the inside rail at d metres to go (the horses' right: the stand side on the straight)."""
    (x, z), (tx, tz) = course_pt(d)
    return x - tz * off, z + tx * off


def far(d, off):
    """'off' metres beyond the outer rail at d metres to go (the horses' left: the far side, towards the Rowley Mile)."""
    (x, z), (tx, tz) = course_pt(d)
    k = TRACK_W + off
    return x + tz * k, z - tx * k


from scipy.interpolate import PchipInterpolator
_H = PchipInterpolator([p[0] for p in PROFILE], [p[1] for p in PROFILE])


def height(d):
    return float(_H(min(max(d, PROFILE[0][0]), PROFILE[-1][0])))


def bank_at(d):
    """The Dyke face's cross-profile at d metres to go: set back behind the far-side festival, closer beyond."""
    if d <= BANK_NEAR["upTo"]:
        return dict(BANK_NEAR)
    if d >= BANK_FAR["from"]:
        return dict(BANK_FAR)
    u = (d - BANK_NEAR["upTo"]) / (BANK_FAR["from"] - BANK_NEAR["upTo"]); u = 0.5 - 0.5 * math.cos(math.pi * u)
    m = lambda a, b: a + (b - a) * u
    return {"foot": m(BANK_NEAR["foot"], BANK_FAR["foot"]), "crest": [m(BANK_NEAR["crest"][0], BANK_FAR["crest"][0]), m(BANK_NEAR["crest"][1], BANK_FAR["crest"][1])],
            "back": m(BANK_NEAR["back"], BANK_FAR["back"]), "height": m(BANK_NEAR["height"], BANK_FAR["height"])}


def bank_h(B, off):
    a, b = B["crest"]
    if off <= B["foot"] or off >= B["back"]:
        return 0.0
    u = (off - B["foot"]) / (a - B["foot"]) if off < a else 1.0 if off <= b else (B["back"] - off) / (B["back"] - b)
    return B["height"] * (0.5 - 0.5 * math.cos(math.pi * u))


def bank_spans():
    spans = [[BANK["from"], BANK["to"]]]
    for a, b in sorted(BANK_SKIP):
        out = []
        for s0, s1 in spans:
            if b <= s0 or a >= s1: out.append([s0, s1]); continue
            if a > s0: out.append([s0, a])
            if b < s1: out.append([b, s1])
        spans = out
    return [[round(a, 1), round(b, 1)] for a, b in spans if b - a > 20]


# ---------------------------------------------------------------- the dressing, placed
def far_rect(r):
    """A far-side piece as an x-z rectangle in course axes (on the straight)."""
    return {"x": r["x"], "z": [TRACK_W + r["off"][0], TRACK_W + r["off"][1]]}


def stand_rects():
    return [{"x": s["x"], "z": [-(STAND_BACK + s["depth"]), -STAND_BACK]} for s in STANDS]


def boards():
    out, k = [], 0
    for mid, count in BOARD_RUNS:
        for j in range(count):
            d = mid + (j - (count - 1) / 2) * BOARD_LEN
            x, z = far(d, BOARDS_BEYOND)
            _, (tx, tz) = course_pt(d)
            # the face turned to the track: towards the horses' right from the far side (0 = facing +z)
            out.append([round(x, 2), round(z, 2), round(math.degrees(math.atan2(-tz, tx)), 1), BOARD_DESIGNS[k % 4]])
            k += 1
    return out


def rect_hit(x, z, r, pad=0.0):
    return r["x"][0] - pad <= x <= r["x"][1] + pad and r["z"][0] - pad <= z <= r["z"][1] + pad


def in_head_on(x, z):
    hx, hz = HEAD_ON["at"][0], HEAD_ON["at"][1]
    return x > hx and abs(z - hz) <= math.tan(math.radians(HEAD_ON["halfAngle"])) * (x - hx)


def trees():
    """Big trees among the far-side festival, more past the post and behind the Dyke's face; on the stand side only
    what the head-on and the drone see (none behind the stands)."""
    g = random.Random(TREE_SEED)
    kinds = list(TREE_KINDS); weights = [TREE_KINDS[k] for k in kinds]
    out, grid = [], {}
    blocked = stand_rects() + [far_rect(p) for p in PAVILIONS] + [far_rect(TIER), LAWN, far_rect(FAR_CROWD)]
    def ok(x, z, sp):
        gx, gz = int(x // TREE_SPACING), int(z // TREE_SPACING)
        for i in (-2, -1, 0, 1, 2):
            for j in (-2, -1, 0, 1, 2):
                for (px, pz, ps) in grid.get((gx + i, gz + j), []):
                    if (px - x) ** 2 + (pz - z) ** 2 < max(sp, ps) ** 2:
                        return False
        return True
    def on_track(x, z):
        if -RUN_ON - 60 < x < STRAIGHT and -8.0 < z < TRACK_W + 8.0:            # the straight and the run-out
            return True
        if x >= STRAIGHT - 60:                                                  # round the bend and up the leg
            for d in range(int(STRAIGHT - 60), int(16 * F) + 60, 15):
                (ix, iz), (tx, tz) = course_pt(d)
                mx, mz = ix + tz * TRACK_W / 2, iz - tx * TRACK_W / 2
                if (mx - x) ** 2 + (mz - z) ** 2 < (TRACK_W / 2 + 10) ** 2:
                    return True
        return False
    def put(x, z, sp=TREE_SPACING, scale=TREE_SCALE):
        if any(rect_hit(x, z, r, 4.0) for r in blocked) or on_track(x, z) or not ok(x, z, sp):
            return
        if z < 0 and (x < STANDS[-1]["x"][1] + 15 or not in_head_on(x, z)):  # the stand side: only what the head-on sees
            return
        grid.setdefault((int(x // TREE_SPACING), int(z // TREE_SPACING)), []).append((x, z, sp))
        out.append([round(x, 2), round(z, 2), g.choices(kinds, weights)[0], round(g.uniform(*scale), 2), g.randrange(360)])
    def belt(x0, x1, z0, z1, n, sp=TREE_SPACING, scale=TREE_SCALE):
        for _ in range(n):
            put(g.uniform(x0, x1), g.uniform(z0, z1), sp, scale)
    # the far side (z > TRACK_W): big trees among the festival's marquees, more past the post, then behind the Dyke's face
    belt(FAR_FESTIVAL["x"][0], FAR_FESTIVAL["x"][1], TRACK_W + 14, TRACK_W + 94, 260, 13.0, BIG_TREES)
    belt(-RUN_ON - 80, FAR_FESTIVAL["x"][0], TRACK_W + 10, TRACK_W + 100, 90, 10.0, [1.2, 2.0])
    for d in range(int(BANK["from"]), int(STRAIGHT), 8):
        B = bank_at(d)
        if g.random() < (0.85 if d < 650 else 0.45):
            put(*far(d + g.uniform(-4, 4), B["back"] + g.uniform(10, 110 if d < 650 else 80)))
    # the stand side (z < 0): a few shade trees in the festival, then only a thin, open backdrop behind it and on up the
    # straight (owner, 8 Nov: "thin out the whole backdrop to the back of the stand side"); the head-on keeps them
    belt(345, 3.5 * F, -58, -18, 22, 16.0)
    belt(345, 3.5 * F + 80, -130, -70, 70, 22.0)
    belt(3.5 * F + 80, STRAIGHT - 60, -120, -45, 45, 28.0)
    return out


def main():
    longest = max(TRIPS.values()) * F + 60
    pts, step = [], 5.0
    d = -RUN_ON
    while d <= longest:
        (x, z), _ = course_pt(d)
        pts.append([round(x, 2), round(z, 2), round(height(d), 3), round(d, 1)])
        d += step
    starts = {}
    for name, f in TRIPS.items():
        dist = f * F
        (x, z), (tx, tz) = course_pt(dist)
        starts[name] = {"distance": round(dist, 1), "at": [round(x, 2), round(z, 2)], "running": [round(tx, 4), round(tz, 4)],
                        "onStraight": dist <= STRAIGHT + 1e-6}
    poles = [{"furlongs": k, "at": [round(c, 2) for c in course_pt(k * F)[0]]} for k in range(1, 17) if k * F <= longest]
    keep = KEEP or (lambda x, z: True)
    spans = bank_spans()
    out = {
        "id": "newmarket-july", "name": "Newmarket (July Course), draft", "status": "DRAFT, second version (after the owner's sketch), 8 Nov 2026: not used by the game yet",
        "_about": "Built by tools/course/newmarket/site_plan.py with july_layout.py. Interpretive, not surveyed: every number is a named choice in july_layout.py.",
        "axes": "Origin = winning post on the inside rail; y up. On the straight horses run towards -x, inside rail z = 0 on their right, the track to z = trackWidth on their left. The stands are behind the inside rail (z < 0); the far side (z > trackWidth) faces the Rowley Mile across the Dyke.",
        "compass": COMPASS, "site": "Placed beside the Rowley Mile in courses/newmarket-site.json (rotation and offset into the Rowley Mile's axes).",
        "direction": "clockwise (right-handed: one bend, from the Cesarewitch leg into the July straight)",
        "trackWidth": TRACK_W, "furlong": F,
        "straight": {"length": round(STRAIGHT, 1), "note": "the Bunbury Mile: races up to a mile are run straight"},
        "bend": {"from": round(STRAIGHT + BEND_LEN, 1), "to": round(STRAIGHT, 1), "radius": BEND_R, "turn": LEG_ANGLE},
        "path": {"bends": [[round(STRAIGHT + BEND_LEN, 1), round(STRAIGHT, 1), LEG_ANGLE]], "home": round(STRAIGHT, 1),
                 "note": "For the race engine: each bend as [metres to go where it starts, where it ends, degrees turned]; 'home' = where the home straight starts."},
        "heights": {"from": -RUN_ON, "spacing": step, "h": [p[2] for p in pts],
                    "note": "The ground's height (m, against the post) every 'spacing' metres to go from 'from', along the inside rail: what the race engine reads (owner, 8 Nov: the dips and the climb count)."},
        "insideRail": {"spacing": step, "fields": "x, z, height, metres to go", "points": pts},
        "profile": {"points": PROFILE, "note": "the owner's notes: rolling for the first three-quarters of the straight, downhill 6f to 5f out, a steep sustained climb over the last 2f"},
        "starts": starts, "furlongPoles": poles, "keyCameras": KEY_CAMERAS,
        "standSide": {"side": "behind the inside rail (z < 0)", "standBack": STAND_BACK, "stands": STANDS, "lawn": LAWN, "festival": FESTIVAL, "paddock": PADDOCK},
        "farSide": {"side": "beyond the outer rail: 'off' = metres beyond it", "festival": FAR_FESTIVAL, "crowd": FAR_CROWD, "tier": TIER, "pavilions": PAVILIONS},
        "dykeFace": {"near": BANK_NEAR, "far": BANK_FAR, "spans": spans,
                     "line": [[d] + [round(v, 2) for v in far(d, sum(bank_at(d)["crest"]) / 2)] + [round(bank_at(d)["height"], 2)]
                              for s0, s1 in spans for d in range(int(s0), int(s1) + 1, 10)],
                     "note": "Owner, 8 Nov: the Dyke on the far side, opposite the grandstands; set back behind the far-side festival near the finish. Offsets beyond the outer rail. 'line': metres to go, the crest's x and z, its height."},
        "boards": {"length": BOARD_LEN, "beyondOuterRail": BOARDS_BEYOND, "runs": BOARD_RUNS,
                   "fields": "x, z, turn (degrees anticlockwise from above; 0 = facing +z), design", "list": [b for b in boards() if keep(b[0], b[1])]},
        "trees": {"fields": "x, z, tree (as ascot-planting.json), scale, turn", "list": [t for t in trees() if keep(t[0], t[1])]},
    }
    (REPO / "courses/newmarket-july-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    (REPO / "courses/newmarket-july-stalls.json").write_text(json.dumps(stalls(starts), indent=1))
    (REPO / "courses/newmarket-july-standards.json").write_text(json.dumps(standards(), indent=1))
    draw(out)
    print("wrote courses/newmarket-july-draft.json, -stalls.json, -standards.json and reference/newmarket-july/plan-draft.png:",
          len(out["boards"]["list"]), "boards,", len(out["trees"]["list"]), "trees")
    return out


# ---------------------------------------------------------------- stalls and par times
MAX_RUNNERS = 28
STALL1, STALL_PITCH, STANDS_BEHIND = 1.625, 1.05, 1.55
START_KEYS = {"5f": "jc5f", "6f": "jc6f", "7f": "jc7f", "1m": "jc1m", "1m2f": "jc1m2f", "1m4f": "jc1m4f", "1m5f": "jc1m5f", "1m6f": "jc1m6f", "2m": "jc2m"}


def stalls(starts):
    out = {"_about": "Where the starting stalls stand for each start on Newmarket's July Course, DRAFT. Written by "
                     "tools/course/newmarket/site_plan.py; don't edit by hand. As courses/ascot-stalls.json: distances from the "
                     "gate line along the inside rail; stall 1 on the inside rail (here the stand side).",
           "horseStandsBehind": STANDS_BEHIND, "maxRunners": MAX_RUNNERS, "starts": {}}
    for name, s in starts.items():
        (x, z), (tx, tz) = course_pt(s["distance"]); nx, nz = tz, -tx
        out["starts"][name] = {
            "label": name + (" (straight)" if s["onStraight"] else " (round)"), "course": "straight" if s["onStraight"] else "round",
            "key": START_KEYS[name], "distance": s["distance"], "insideRailAt": s["at"], "runningDirection": s["running"],
            "towardsOuterRail": [round(nx, 4), round(nz, 4)], "stall1": "inside rail (the stand side)", "onStraight": s["onStraight"],
            "stalls": [{"draw": i + 1, "fromInsideRail": round(STALL1 + STALL_PITCH * i, 3), "across": round(STALL1 + STALL_PITCH * i - TRACK_W / 2, 3),
                        "at": [round(x + nx * (STALL1 + STALL_PITCH * i), 2), round(z + nz * (STALL1 + STALL_PITCH * i), 2)]} for i in range(MAX_RUNNERS)],
        }
    return out


# Rough winning times of a good horse on good ground, the climb included (from memory: the July Cup about 1m10.5s, the
# Falmouth about 1m38s, the Princess of Wales's about 2m30s; to check against real results). PAR is what the engine is
# handed, set by tools/race-bench/nmcalibrate.py so its winning times come out at these.
TARGET = {"jc5f": 58.5, "jc6f": 70.8, "jc7f": 84.3, "jc1m": 97.8, "jc1m2f": 124.0, "jc1m4f": 150.5, "jc1m5f": 163.5, "jc1m6f": 177.0, "jc2m": 205.0}
PAR = dict(TARGET)
PAR_FILE = REPO / "tools/race-bench/newmarket-par.json"
if PAR_FILE.exists():
    PAR.update({k: v for k, v in json.loads(PAR_FILE.read_text())["par"].items() if k in TARGET})


def standards():
    asc = json.loads((REPO / "courses/ascot-standards.json").read_text())
    par = [{"key": START_KEYS[n], "course": "straight" if f * F <= STRAIGHT + 1e-6 else "round", "distance": round(f * F, 1),
            "seconds": PAR[START_KEYS[n]], "winningTime": TARGET[START_KEYS[n]]} for n, f in TRIPS.items()]
    return {"_about": "Par (standard) times on Newmarket's July Course, DRAFT, for the race engine and the race view's dock. "
                      "'winningTime' is a rough winning time for a good horse on good ground, the climb included (from memory: check "
                      "against real results). 'seconds' is the par the engine uses, set so its winning times come out at those. "
                      "The going as at Ascot.",
            "parTimes": par, "going": asc["going"], "pace": asc["pace"]}


# ---------------------------------------------------------------- the drawing (the run-in; the whole site is site_plan.py's)
INK, MUTED, RAIL, HEATH, TURF, BANKC, CREST = "#2b2b2b", "#777", "#ffffff", "#e3e7cc", "#86ac5f", "#a9b979", "#8a9a5b"
STAND, LAWNC, FEST, PAV, TIERC, CROWD, POST = "#cdb79a", "#c9d9a6", "#f1d9a8", "#f7f4ec", "#d8c3a0", "#c98b7a", "#c0392b"
LEAF = ["#5f7f45", "#6e8d4c", "#557440", "#7a9655"]
BOARD_C = {"green": "#2f5d3a", "cream": "#e9dfc3", "navy": "#24324f", "white": "#f6f6f2"}
# the cross-sections are drawn from the far (outer) rail: 0 there, the track 0 to TRACK_W, the stands beyond
CAMS = {"tracking car": (TRACK_W + 5.0, 3.0), "stand camera": (TRACK_W + STAND_BACK + 2.0, 12.0), "drone": (TRACK_W / 2 + 20.0, 15.0)}


def draw(c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle, Ellipse
    plt.rcParams["font.family"] = "Inter"
    W_IN = 14.0
    zx, zz_ = (-440.0, 5.2 * F), (-210.0, TRACK_W + 185.0)
    hZ = W_IN * 0.9 * (zz_[1] - zz_[0]) / (zx[1] - zx[0])
    hX, hP, gap, top, bottom = 2.6, 1.9, 0.75, 0.55, 0.6
    H_IN = top + hZ + gap + hX + gap + hP + bottom
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=100)
    yy = [H_IN - top]
    def band(h):
        yy[0] -= h; r = (yy[0] / H_IN, h / H_IN); yy[0] -= gap; return r
    yZ, fZ = band(hZ); Z = fig.add_axes([0.05, yZ, 0.9, fZ])
    yX, fX = band(hX); X1 = fig.add_axes([0.06, yX, 0.43, fX]); X2 = fig.add_axes([0.54, yX, 0.43, fX])
    yP, fP = band(hP); PR = fig.add_axes([0.06, yP, 0.9, fP])
    P = c["insideRail"]["points"]; ds = [p[3] for p in P]

    # ---- the run-in close up (as the site plan, turned so the July straight runs across the page)
    Z.set_facecolor(HEATH)
    for s0, s1 in c["dykeFace"]["spans"]:
        bd = [s0 + i * 5 for i in range(int((s1 - s0) / 5) + 1)]
        Z.add_patch(Polygon([far(d, bank_at(d)["foot"]) for d in bd] + [far(d, bank_at(d)["back"]) for d in bd[::-1]], closed=True, fc=BANKC, ec="none"))
        Z.plot(*zip(*[far(d, sum(bank_at(d)["crest"]) / 2) for d in bd]), color=CREST, lw=1.0)
    rr = lambda r, **k: Z.add_patch(Rectangle((r["x"][0], r["z"][0]), r["x"][1] - r["x"][0], r["z"][1] - r["z"][0], **k))
    rr(far_rect(FAR_FESTIVAL), fc=FEST, ec="none", alpha=0.75)
    rr(LAWN, fc=LAWNC, ec="none"); rr(FESTIVAL, fc=FEST, ec="none"); rr(far_rect(FAR_CROWD), fc=CROWD, ec="none")
    rr({"x": PADDOCK["x"], "z": PADDOCK["z"]}, fc="#dfe6c8", ec="none")
    for t in c["trees"]["list"]:
        Z.add_patch(Ellipse((t[0], t[1]), 9 * t[3], 9 * t[3], fc=LEAF[hash(t[2]) % 4], ec="none", alpha=0.92))
    Z.add_patch(Polygon([(p[0], p[1]) for p in P] + [far(d, 0) for d in ds[::-1]], closed=True, fc=TURF, ec="none"))
    Z.plot([p[0] for p in P], [p[1] for p in P], color=RAIL, lw=1.4); Z.plot(*zip(*[far(d, 0) for d in ds]), color=RAIL, lw=1.4)
    for r in stand_rects(): rr(r, fc=STAND, ec="#8d826b", lw=0.8)
    for p in PAVILIONS: rr(far_rect(p), fc=PAV, ec="#8d826b", lw=0.8)
    rr(far_rect(TIER), fc=TIERC, ec="#8d826b", lw=0.8, hatch="---")
    for b in c["boards"]["list"]:
        Z.plot([b[0] - 3, b[0] + 3], [b[1], b[1]], color=BOARD_C[b[3]] if b[3] != "white" else "#9aa3b5", lw=2.6, solid_capstyle="butt")
    Z.plot([0, 0], [0, TRACK_W], color=POST, lw=2.4)
    for p in c["furlongPoles"]:
        if p["furlongs"] <= 4:
            Z.text(p["at"][0], TRACK_W / 2, "%df" % p["furlongs"], ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    Z.text(-8, TRACK_W / 2, "post", ha="right", va="center", fontsize=9, color=POST, rotation=90)
    lab = dict(fontsize=8.5, color=INK, ha="center", va="center")
    for s, r in zip(STANDS, stand_rects()):
        Z.text(sum(r["x"]) / 2, sum(r["z"]) / 2, s["name"].replace(" ", "\n", 1), **lab)
    Z.text(-118, -8, "packed lawns, umbrellas", fontsize=7.5, color=INK, ha="left", va="center")
    Z.text(sum(FESTIVAL["x"]) / 2 + 20, sum(FESTIVAL["z"]) / 2, "stand-side festival to 3.5f out", **lab)
    Z.text(115, -150, "parade rings and paddock (no trees: never on camera)", **lab)
    hx, hz = HEAD_ON["at"][0], HEAD_ON["at"][1]; ta = math.tan(math.radians(HEAD_ON["halfAngle"]))
    for sg in (-1, 1):
        Z.plot([hx, zx[1]], [hz, hz + sg * ta * (zx[1] - hx)], color="#2a6f97", lw=0.9, ls="--")
    Z.plot(hx, hz, marker="o", color="#2a6f97", ms=6)
    Z.text(hx - 8, hz - 30, "head-on camera:\nstand-side trees kept\nonly inside its view", fontsize=8, color="#2a6f97", ha="right", va="center")
    t_ = far_rect(TIER); Z.text(sum(t_["x"]) / 2, sum(t_["z"]) / 2, "tiered\nstand", **lab)
    Z.annotate("far-side festival from 3f out to the finish: marquees and pavilions among big trees, a crowd along the rail", xy=(330, TRACK_W + 80), xytext=(-430, TRACK_W + 160),
               arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=8.5, color=INK, ha="left")
    Z.annotate("the Dyke's face, set back behind the festival", xy=(560, TRACK_W + 112), xytext=(640, TRACK_W + 160), arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=8.5, color=INK, ha="left")
    Z.annotate("coming in to 30 m\nbeyond the far rail", xy=(940, TRACK_W + 31), xytext=(880, TRACK_W + 110), arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=8.5, color=INK, ha="left")
    Z.annotate("a long sponsor board along the far rail", xy=(-20, TRACK_W + 2.5), xytext=(-430, TRACK_W + 45), arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=8.5, color=INK, ha="left")
    Z.set_aspect("equal"); Z.set_xlim(*zx); Z.set_ylim(zz_[1], zz_[0]); Z.tick_params(labelsize=7, colors=MUTED)
    Z.text(-RUN_ON / 2 - 20, TRACK_W / 2, "the run-out", ha="center", va="center", fontsize=9, color="white", fontweight="bold")
    Z.set_title("July Course, the run-in close up (turned so the straight runs across the page; the post on the left, the run-out beyond it). Stands and festival above;\nthe far-side festival and the Dyke below, towards the Rowley Mile", fontsize=10, loc="left", color=INK)

    # ---- two cross-sections, from the far rail (left) to the stands (right)
    EX = 3.0
    def section(ax, d, title, near):
        B = bank_at(d)
        u0, u1 = -150.0, TRACK_W + STAND_BACK + 60
        uu = [u0 + i * 0.5 for i in range(int((u1 - u0) / 0.5) + 1)]
        gh = [bank_h(B, -u) if u < 0 else 0.0 for u in uu]
        ax.fill_between(uu, [h * EX for h in gh], -3, color=BANKC); ax.plot(uu, [h * EX for h in gh], color=INK, lw=1.0)
        ax.fill_between([0, TRACK_W], [0, 0], -3, color=TURF)
        for ur in (0, TRACK_W): ax.plot([ur, ur], [0, 1.1 * EX], color="#bbb", lw=1.6)
        r = random.Random(int(d) + 3)
        def tree(u, h):
            ax.plot([u, u], [0, h * 0.45 * EX], color="#6b5a45", lw=1.1)
            ax.add_patch(Ellipse((u, h * 0.68 * EX), 9.0, h * 0.62 * EX, fc=LEAF[r.randrange(4)], ec="none"))
        for ut in [-(B["back"] + 8 + k * 11 + r.uniform(-3, 3)) for k in range(8)]:
            if ut > u0 + 4: tree(ut, r.uniform(11, 14) * r.uniform(1.0, 1.6))
        if FAR_FESTIVAL["x"][0] <= d <= FAR_FESTIVAL["x"][1]:      # the far-side festival: big trees, a crowd at the rail
            for k in range(5): tree(-40 - k * 11 + r.uniform(-2, 2), r.uniform(10, 13) * r.uniform(BIG_TREES[0], BIG_TREES[1]) * 0.8)
            ax.add_patch(Rectangle((-FAR_CROWD["off"][1], 0), FAR_CROWD["off"][1] - FAR_CROWD["off"][0], 1.8 * EX, fc=CROWD, ec="none"))
            ax.add_patch(Rectangle((-BOARDS_BEYOND - 0.2, 0.5 * EX), 0.4, 1.0 * EX, fc=BOARD_C["navy"], ec="none"))
        if not near and FAR_FESTIVAL["x"][0] <= d <= FAR_FESTIVAL["x"][1]:
            ax.add_patch(Rectangle((-34, 0), 18, 8 * EX, fc=PAV, ec="#8d826b", lw=0.8)); ax.text(-25, 8 * EX + 3, "marquee", ha="center", fontsize=8)
        if near:
            ax.add_patch(Rectangle((-TIER["off"][1], 0), TIER["off"][1] - TIER["off"][0], TIER["height"] * EX, fc=TIERC, ec="#8d826b", lw=0.8))
            ax.text(-sum(TIER["off"]) / 2, TIER["height"] * EX + 3, "tiered stand", ha="center", fontsize=8)
            ax.add_patch(Rectangle((-FAR_CROWD["off"][1], 0), FAR_CROWD["off"][1] - FAR_CROWD["off"][0], 1.8 * EX, fc=CROWD, ec="none"))
            ax.add_patch(Rectangle((TRACK_W + 2, 0), STAND_BACK - 3, 1.8 * EX, fc=CROWD, ec="none"))
            s = STANDS[1]
            ax.add_patch(Rectangle((TRACK_W + STAND_BACK, 0), s["depth"], s["height"] * EX, fc=STAND, ec="#8d826b", lw=0.8))
            ax.text(TRACK_W + STAND_BACK + s["depth"] / 2, s["height"] * EX + 3, "stands", ha="center", fontsize=8)
        else:
            for k in range(5):
                ax.add_patch(Rectangle((TRACK_W + 12 + k * 9, 0), 5, 3.2 * EX, fc=FEST, ec="#b49a6a", lw=0.6))
            tree(TRACK_W + 30, 12); ax.text(TRACK_W + 36, 6.2 * EX, "festival pieces", ha="center", fontsize=8)
        crest = (-sum(B["crest"]) / 2, B["height"])
        shades = {"tracking car": "#c0392b", "stand camera": "#2a6f97", "drone": "#7b5ea7"}
        for name, (cu, cy) in CAMS.items():
            if name == "stand camera" and not near: continue
            slope = (cy - crest[1]) / (cu - crest[0])
            ax.plot([cu, u0], [cy * EX, (crest[1] + slope * (u0 - crest[0])) * EX], color=shades[name], lw=1.0, ls="--")
            ax.plot(cu, cy * EX, marker="o", color=shades[name], ms=5); ax.text(cu + 2, cy * EX + 3, name, fontsize=8, color=shades[name])
        ax.text(crest[0], crest[1] * EX + 3, "Dyke %.1f m" % B["height"], ha="center", fontsize=8)
        ax.set_xlim(u0, u1); ax.set_ylim(-3, 24 * EX)
        ax.set_yticks([0, 5 * EX, 10 * EX, 15 * EX, 20 * EX]); ax.set_yticklabels(["0", "5", "10", "15", "20 m"])
        ax.set_xlabel("metres across (0 = the far rail, the stands to the right); heights x%d" % EX, fontsize=8.5); ax.tick_params(labelsize=7.5)
        ax.set_title(title, fontsize=9.5, loc="left")
    section(X1, 0.0, "Across at the finish: below each dashed line is hidden", True)
    section(X2, 3 * F, "Across at 3f out", False)

    # ---- the height profile
    dd = list(range(int(-RUN_ON), int(STRAIGHT) + 1, 5))
    PR.fill_between([d / F for d in dd], [height(d) for d in dd], -5, color=TURF, alpha=0.6); PR.plot([d / F for d in dd], [height(d) for d in dd], color=INK, lw=1.2)
    PR.axvline(0, color=POST, lw=1.2)
    for f_, t_ in [(2, "the climb starts, 2f"), (5, "down 6f to 5f")]:
        PR.axvline(f_, color="#888", lw=0.8, ls="--"); PR.text(f_ + 0.05, 1.8, t_, fontsize=8.5)
    PR.set_xlim(-RUN_ON / F, STRAIGHT / F); PR.set_ylim(-5, 3)
    PR.set_xlabel("furlongs to go (the straight)", fontsize=9); PR.set_ylabel("height (m)", fontsize=9)
    PR.set_title("The straight's height profile: rolling, downhill from 6f to 5f out, then a long climb over the last 2f (heights exaggerated on this chart only)", fontsize=10, loc="left")
    PR.tick_params(labelsize=8)
    fig.savefig(REPO / "reference/newmarket-july/plan-draft.png")


if __name__ == "__main__":
    import site_plan
    site_plan.main()
