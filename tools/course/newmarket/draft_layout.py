"""Newmarket (the Rowley Mile), phase 1: a DRAFT layout for the owner to check before anything is modelled.

Interpretive, from the owner's references (reference/newmarket/): the plan, the grandstand photo, his notes on the Dip and
his 1m4f video. Not surveyed: every number below is a choice, named, so it can be changed in one place.

Writes  courses/newmarket-draft.json   the layout as data (same axes and running direction as courses/ascot.json)
        reference/newmarket/plan-draft.png   a plan, a cross-section and a height profile, to check by eye

  python3 tools/course/newmarket/draft_layout.py

Axes as Ascot: origin = the winning post on the inside rail; x east, z south, y up. On the straight the horses run
towards -x with the inside rail on their right (z = 0, the far side) and the stands on their left (+z). Right-handed:
coming down the Cesarewitch leg they turn right into the straight.
"""
import json, math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
F = 201.168                                   # a furlong, metres

# ---------------------------------------------------------------- the choices (change here)
TRACK_W = 36.0          # the Rowley Mile is wide; Ascot's straight is 30
STRAIGHT = 10 * F       # 1m2f from the post to the end of the bend: everything up to 1m2f is run straight (the plan)
LEG_ANGLE = 62.0        # the Cesarewitch leg, degrees up from the straight's line on the plan
BEND_R = 200.0          # the bend's inside-rail radius
RUN_ON = 120.0          # the straight carries on past the post
TRIPS = {"5f": 5, "6f": 6, "7f": 7, "1m": 8, "1m1f": 9, "1m2f": 10, "1m4f": 12, "1m6f": 14, "2m": 16, "2m2f": 18, "2m4f": 20}
# The Dip (owner's notes): downhill from about 2f out (by "the Bushes"), the bottom at the 1f pole, a sharp climb to the
# post. Heights in metres against the post, by metres to go; smooth between. Gentle ridges before it; the leg rises
# a little towards the far starts. Interpretive: big enough to see from the stand and to matter in the run for home.
PROFILE = [(-RUN_ON, 0.6), (0, 0.0), (201, -3.0), (402, 0.6), (520, 1.0), (700, 0.4),
           (900, 1.2), (1150, 0.6), (1400, 1.4), (1700, 0.8), (STRAIGHT, 1.6), (2600, 3.0), (3400, 4.5), (4500, 6.0), (5200, 6.5)]
# The far bank (owner, 8 Nov, second look): not a tall dyke 70 m back but "a gentler bank on the far side rail the whole
# way round", closer to the track than the real Devil's Dyke. It follows the inside (far) rail from behind the post,
# along the straight, round the bend and up the Cesarewitch leg. Across it, in metres behind the inside rail: flat
# heath to 'foot', a soft rise to the crest ('crest', a rounded top), and down again to 'back'. Height in metres.
BANK = {"foot": 12.0, "crest": [28.0, 34.0], "back": 50.0, "height": 4.0, "from": -260.0, "to": 20 * F + 120.0,
        "note": "Owner, 8 Nov: a gentle grassy bank behind the far rail the whole way round, closer than real life "
                "(the Devil's Dyke, interpretive). Offsets are metres behind the inside rail; it sits on the ground's "
                "own height (the Dip runs through it). Low scrub along the crest; tree tops show beyond it."}
# Advertising boards (owner, 8 Nov: "some advertising boards dotted along the course"): in short runs, not a continuous
# line, and only on the far side from the cameras (the rule at Ascot), on the strip of heath between the far rail and
# the foot of the bank. Each run: metres to go at its middle, and how many 6 m boards. The house designs from Ascot.
BOARD_LEN, BOARDS_BEHIND = 6.0, 3.0
BOARD_RUNS = [(40, 6), (215, 4), (410, 5), (640, 3), (900, 4), (1180, 3), (1470, 4), (1780, 3), (2110, 5),
              (2520, 3), (2950, 4), (3450, 3), (4000, 3), (4500, 4)]
BOARD_DESIGNS = ["green", "cream", "navy", "white"]
# Tree tops beyond the bank (owner, 8 Nov): clumps and short tree lines on the heath behind it, far enough back that
# from the tracking car only the crowns show over the crest. Seeded, so the same trees every time.
TREES = {"from": 62.0, "to": 150.0, "start": -320.0, "end": 20 * F + 220.0, "spacing": 7.5, "seed": 8,
         "kinds": {"oak_a": 3, "oak_b": 3, "oak_c": 3, "wide_a": 3, "wide_b": 3, "poplar_a": 1}, "scale": [1.0, 1.6]}
# The stand side's buildings (owner, 8 Nov, his aerial marked 1-3 and photos: reference/newmarket/): the Millennium
# Grandstand from about the post up the course, the lower Rowley stand with its clock cupola beyond it, then the old
# Victorian stand up the course (his point 3) with its white judge's kiosk by the rail and a small pavilion. Pieces in
# assets/models/architecture/rowley_stands.glb (tools/blender/build_rowley_stands.py). Each: x from, x to (the main
# block, metres along the straight), front = metres beyond the NEAR rail, the piece; all face the track.
STAND_PIECES = [
    {"name": "Millennium Grandstand", "piece": "millennium_stand", "x": [-8.0, 160.0], "front": 14.0, "note": "five wave canopies; its stair tower at the up-course end"},
    {"name": "Rowley stand", "piece": "rowley_stand", "x": [172.0, 282.0], "front": 16.0, "note": "the clock cupola; a brick end up the course"},
    {"name": "Small pavilion", "piece": "victorian_pavilion", "x": [329.0, 340.0], "front": 34.0},
    {"name": "Judge's kiosk", "piece": "judges_kiosk", "x": [350.0, 353.4], "front": 7.0},
    {"name": "Old stand", "piece": "victorian_stand", "x": [350.0, 446.0], "front": 34.0, "note": "his point 3: two tiers under a hipped slate roof; its low wing up the course"},
]
STANDS = {"front": TRACK_W + 14.0, "x": [-170.0, 330.0], "height": 26.0,
          "note": "Interpretive and bigger than life (owner): the Millennium Grandstand's row of wave-shaped canopies, "
                  "longer than the real stand, from the stand kit with a new canopy module, smooth clay finish."}
# The festival area (owner's sketch of both courses, 8 Nov: yellow beside the stands, up the course from them): stalls,
# bars, umbrellas and picnic lawns from the end of the stands to about 3.5f out, set 10 m back from the near rail to
# leave a lane for the tracking car.
FESTIVAL = {"x": [470.0, 3.5 * F], "z": [TRACK_W + 10, TRACK_W + 60],
            "note": "festival pieces from the end of the stands to 3.5f out (owner's sketch, 8 Nov), 10 m back from the near rail"}
# The compass (owner's sketch, 8 Nov): north is at the BOTTOM of these plans, so +z points north and +x west. (The axes'
# names below are Ascot's; the real compass matters only for the sun.)
COMPASS = "owner's sketch, 8 Nov: north is at the bottom of the plans: +z is north, +x is west"
# Set by site_plan.py, which builds both Newmarket courses together: stretches of the bank to leave out (where the July
# Course runs through), and a test for trees and boards that would stand on the July Course.
BANK_SKIP = []          # [[metres to go from, to], ...]
KEEP = None             # KEEP(x, z) -> False to leave a tree or board out


def straight_pt(d):                            # d metres to go on the straight, inside rail
    return (d, 0.0)

# the bend: from the straight's top end, turning (as you go UP the course, against the running) up the plan
TURN = math.radians(LEG_ANGLE)                  # the angle turned through, running (the leg meets the straight at LEG_ANGLE)
CX, CZ = STRAIGHT, -BEND_R                       # the bend's centre (inside the turn: north of the inside rail)
BEND_LEN = BEND_R * math.radians(LEG_ANGLE)


def course_pt(d):
    """Inside-rail point and running direction at d metres to go (d may run past the post, negative)."""
    if d <= STRAIGHT:
        return (d, 0.0), (-1.0, 0.0)
    s = d - STRAIGHT
    if s <= BEND_LEN:                            # round the bend (anticlockwise on the plan as you go up the course)
        a = s / BEND_R
        x = CX + BEND_R * math.sin(a); z = CZ + BEND_R * math.cos(a)
        return (x, z), (-math.cos(a), math.sin(a))
    a = math.radians(LEG_ANGLE)
    ex, ez = CX + BEND_R * math.sin(a), CZ + BEND_R * math.cos(a)
    k = s - BEND_LEN
    ux, uz = math.cos(a), -math.sin(a)           # up the leg (against the running)
    return (ex + ux * k, ez + uz * k), (-ux, -uz)


from scipy.interpolate import PchipInterpolator
_H = PchipInterpolator([p[0] for p in PROFILE], [p[1] for p in PROFILE])   # smooth, no overshoot between the points


def height(d):
    return float(_H(min(max(d, PROFILE[0][0]), PROFILE[-1][0])))


def behind(d, off):
    """The point 'off' metres behind the inside (far) rail at d metres to go, i.e. to the horses' right."""
    (x, z), (tx, tz) = course_pt(d)
    return x - tz * off, z + tx * off


def bank_h(off):
    """The far bank's height (m, on top of the ground) at 'off' metres behind the inside rail: a soft rise and fall."""
    B = BANK; a, b = B["crest"]
    if off <= B["foot"] or off >= B["back"]:
        return 0.0
    if off < a:
        u = (off - B["foot"]) / (a - B["foot"])
    elif off <= b:
        u = 1.0
    else:
        u = (B["back"] - off) / (B["back"] - b)
    return B["height"] * (0.5 - 0.5 * math.cos(math.pi * u))


def bank_spans():
    """The bank's stretches, metres to go, with BANK_SKIP left out."""
    spans = [[BANK["from"], BANK["to"]]]
    for a, b in sorted(BANK_SKIP):
        out = []
        for s0, s1 in spans:
            if b <= s0 or a >= s1: out.append([s0, s1]); continue
            if a > s0: out.append([s0, a])
            if b < s1: out.append([b, s1])
        spans = out
    return [[round(a, 1), round(b, 1)] for a, b in spans if b - a > 20]


def boards():
    out, k = [], 0
    for mid, count in BOARD_RUNS:
        for j in range(count):
            d = mid + (j - (count - 1) / 2) * BOARD_LEN
            x, z = behind(d, BOARDS_BEHIND)
            _, (tx, tz) = course_pt(d)
            turn = math.degrees(math.atan2(tz, -tx))              # the board's face turned to the track (0 = facing south)
            out.append([round(x, 2), round(z, 2), round(turn, 1), BOARD_DESIGNS[k % len(BOARD_DESIGNS)]])
            k += 1
    return out


def trees(rail):
    """Clumps and short lines of trees on the heath beyond the bank, seeded."""
    import numpy as np
    T = TREES; g = np.random.default_rng(T["seed"])
    kinds = list(T["kinds"]); w = np.array([T["kinds"][k] for k in kinds], float); w /= w.sum()
    rail = np.array(rail)
    keep_off = BANK["back"] + 8.0
    out, grid = [], {}
    def free(x, z):
        gx, gz = int(x // T["spacing"]), int(z // T["spacing"])
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for (px, pz) in grid.get((gx + i, gz + j), []):
                    if (px - x) ** 2 + (pz - z) ** 2 < T["spacing"] ** 2:
                        return False
        return True
    d = T["start"]
    while d < T["end"]:
        d += g.uniform(45, 150)                                  # the gap to the next clump
        line = g.random() < 0.35                                 # a tree line along the heath, or a round clump
        n = int(g.integers(6, 16) if line else g.integers(3, 10))
        depth = g.uniform(T["from"] + 6, T["to"] - 10)
        for _ in range(n):
            dd = d + (g.uniform(-45, 45) if line else g.normal(0, 14))
            off = depth + (g.normal(0, 4) if line else g.normal(0, 10))
            off = min(max(off, T["from"]), T["to"])
            x, z = behind(dd, off)
            if np.min((rail[:, 0] - x) ** 2 + (rail[:, 1] - z) ** 2) < keep_off ** 2 or not free(x, z):
                continue
            grid.setdefault((int(x // T["spacing"]), int(z // T["spacing"])), []).append((x, z))
            out.append([round(x, 2), round(z, 2), str(g.choice(kinds, p=w)), round(float(g.uniform(*T["scale"])), 2), int(g.integers(0, 360))])
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
    poles = [{"furlongs": k, "at": [round(c, 2) for c in course_pt(k * F)[0]]} for k in range(1, 25) if k * F <= longest]
    rail_xz = [course_pt(dd)[0] for dd in range(int(BANK["from"]), int(longest) + 1, 5)]
    keep = KEEP or (lambda x, z: True)
    out = {
        "id": "newmarket", "name": "Newmarket (Rowley Mile), draft", "status": "DRAFT, second version for the owner's check (8 Nov 2026): not used by the game yet",
        "_about": "Built by tools/course/newmarket/draft_layout.py. Interpretive, not surveyed: every number is a named choice in that script.",
        "axes": "As courses/ascot.json: origin = winning post on the inside rail; y up. On the straight horses run towards -x, inside rail z = 0 (far side), stands +z.",
        "compass": COMPASS, "site": "Placed with the July Course in courses/newmarket-site.json (this course's axes are the site's).",
        "direction": "clockwise (right-handed: one bend, from the Cesarewitch leg into the straight)",
        "trackWidth": TRACK_W, "furlong": F,
        "straight": {"length": round(STRAIGHT, 1), "note": "1m2f from the post to the bend: races up to 1m2f are run straight"},
        "bend": {"from": round(STRAIGHT + BEND_LEN, 1), "to": round(STRAIGHT, 1), "radius": BEND_R, "turn": round(math.degrees(TURN), 1),
                 "note": "metres to go where it starts and ends; inside-rail radius; degrees turned"},
        "insideRail": {"spacing": step, "fields": "x, z, height, metres to go", "points": pts},
        "theDip": {"profile": PROFILE, "note": "height (m) against the post by metres to go; the bottom at the 1f pole. Owner, 8 Nov: the Dip counts in the race (see race-engine/README.md, 'Hills')"},
        "path": {"bends": [[round(STRAIGHT + BEND_LEN, 1), round(STRAIGHT, 1), round(math.degrees(TURN), 1)]], "home": round(STRAIGHT, 1),
                 "note": "For the race engine (any course that is one path, not Ascot's loop): each bend as [metres to go where it "
                         "starts, where it ends, degrees turned]; 'home' = metres to go where the home straight starts."},
        "heights": {"from": -RUN_ON, "spacing": step, "h": [p[2] for p in pts],
                    "note": "The ground's height (m, against the post) every 'spacing' metres to go from 'from', along the inside "
                            "rail: what the race engine reads for the Dip (owner, 8 Nov: it counts). Straight lines between points."},
        "starts": starts, "furlongPoles": poles, "stands": STANDS, "standPieces": STAND_PIECES, "festival": FESTIVAL,
        "farBank": {**BANK, "spans": bank_spans(), "profileAcross": [[o, round(bank_h(o), 2)] for o in range(0, int(BANK["back"]) + 3, 2)],
                    "spansNote": "the stretches (metres to go) where the bank stands: it stops where the July Course runs through, inside the bend"},
        "boards": {"length": BOARD_LEN, "behindRail": BOARDS_BEHIND, "runs": BOARD_RUNS,
                   "fields": "x, z, turn (degrees anticlockwise from above; 0 = facing south, as ascot-planting.json), design",
                   "list": [b for b in boards() if keep(b[0], b[1])]},
        "trees": {"fields": "x, z, tree (as ascot-planting.json), scale, turn", "note": "tree tops beyond the far bank (owner, 8 Nov)", "list": [t for t in trees(rail_xz) if keep(t[0], t[1])]},
    }
    (REPO / "courses/newmarket-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    (REPO / "courses/newmarket-stalls.json").write_text(json.dumps(stalls(starts), indent=1))
    (REPO / "courses/newmarket-standards.json").write_text(json.dumps(standards(), indent=1))
    draw(out)
    print("wrote courses/newmarket-draft.json and reference/newmarket/plan-draft.png:",
          len(out["boards"]["list"]), "boards,", len(out["trees"]["list"]), "trees")
    return out


# The starting stalls, laid out as Ascot's (courses/ascot-stalls.json): stall 1 on the inside (far) rail, 1.05 m apart.
MAX_RUNNERS = 30                                  # the Rowley Mile is wide enough for the Cambridgeshire's big fields
STALL1, STALL_PITCH, STANDS_BEHIND = 1.625, 1.05, 1.55
START_KEYS = {"5f": "nm5f", "6f": "nm6f", "7f": "nm7f", "1m": "nm1m", "1m1f": "nm1m1f", "1m2f": "nm1m2f", "1m4f": "nm1m4f",
              "1m6f": "nm1m6f", "2m": "nm2m", "2m2f": "nm2m2f", "2m4f": "nm2m4f"}


def stalls(starts):
    out = {"_about": "Where the starting stalls stand for each start at Newmarket (Rowley Mile), DRAFT. Written by "
                     "tools/course/newmarket/draft_layout.py; don't edit by hand. As courses/ascot-stalls.json: world axes as the "
                     "course file, distances from the gate line along the inside rail; stall 1 on the inside (far) rail.",
           "horseStandsBehind": STANDS_BEHIND, "maxRunners": MAX_RUNNERS, "starts": {}}
    for name, s in starts.items():
        (x, z), (tx, tz) = course_pt(s["distance"]); nx, nz = tz, -tx
        out["starts"][name] = {
            "label": name + (" (straight)" if s["onStraight"] else " (round)"), "course": "straight" if s["onStraight"] else "round",
            "key": START_KEYS[name], "distance": s["distance"], "insideRailAt": s["at"], "runningDirection": s["running"],
            "towardsOuterRail": [round(nx, 4), round(nz, 4)], "stall1": "far side (inside rail)", "onStraight": s["onStraight"],
            "stalls": [{"draw": i + 1, "fromInsideRail": round(STALL1 + STALL_PITCH * i, 3), "across": round(STALL1 + STALL_PITCH * i - TRACK_W / 2, 3),
                        "at": [round(x + nx * (STALL1 + STALL_PITCH * i), 2), round(z + nz * (STALL1 + STALL_PITCH * i), 2)]} for i in range(MAX_RUNNERS)],
        }
    return out


# Par times (seconds) for the race engine. TARGET is the rough winning time of a good horse on good ground at the Rowley
# Mile, Dip included (from memory, to check against real results, as Ascot's). PAR is what the engine is handed: set
# so that with the Dip's cost its winning times come out at the targets (tools/race-bench/nmcalibrate.py measures them).
TARGET = {"nm5f": 58.5, "nm6f": 71.5, "nm7f": 84.5, "nm1m": 97.0, "nm1m1f": 110.0, "nm1m2f": 123.0, "nm1m4f": 150.0,
          "nm1m6f": 177.0, "nm2m": 205.0, "nm2m2f": 233.0, "nm2m4f": 262.0}
PAR = dict(TARGET)
PAR_FILE = REPO / "tools/race-bench/newmarket-par.json"
if PAR_FILE.exists():
    PAR.update(json.loads(PAR_FILE.read_text())["par"])


def standards():
    asc = json.loads((REPO / "courses/ascot-standards.json").read_text())
    par = []
    for name, f in TRIPS.items():
        k = START_KEYS[name]
        par.append({"key": k, "course": "straight" if f * F <= STRAIGHT + 1e-6 else "round", "distance": round(f * F, 1),
                    "seconds": PAR[k], "winningTime": TARGET[k]})
    return {"_about": "Par (standard) times at Newmarket (Rowley Mile), DRAFT, for the race engine and the race view's dock. "
                      "'winningTime' is a rough winning time for a good horse on good ground, the Dip included (from memory: check "
                      "against real results). 'seconds' is the par the engine uses, set so its winning times come out at those "
                      "(the Dip slows them). The going as at Ascot.",
            "parTimes": par, "going": asc["going"], "pace": asc["pace"]}


# ---------------------------------------------------------------------------------------------- the drawing
INK, MUTED, RAIL, HEATH, TURF, BANKC, CREST, STAND, POST = "#2b2b2b", "#777", "#ffffff", "#e6e8cf", "#86ac5f", "#a9b979", "#8a9a5b", "#d9cdb4", "#c0392b"
LEAF = ["#5f7f45", "#6e8d4c", "#557440", "#7a9655"]
BOARD_C = {"green": "#2f5d3a", "cream": "#e9dfc3", "navy": "#24324f", "white": "#f6f6f2"}
# the cameras for the sightlines in the cross-section, as Ascot's, moved out for the wider track and the bigger stand
CAMS = {"tracking car": (TRACK_W + 5.0, 3.0), "stand camera": (STANDS["front"] + 2.0, 14.0), "drone": (TRACK_W / 2 + 20.0, 15.0)}


def draw(c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle, Ellipse
    plt.rcParams["font.family"] = "Inter"
    fig = plt.figure(figsize=(13, 16), dpi=110)
    ax = fig.add_axes([0.05, 0.47, 0.9, 0.49]); xs = fig.add_axes([0.07, 0.23, 0.88, 0.17]); pr = fig.add_axes([0.07, 0.04, 0.88, 0.12])

    # ---- the plan
    ax.set_facecolor(HEATH)
    P = c["insideRail"]["points"]
    def left(d, off):                                        # 'off' metres to the horses' left of the inside rail
        (x, z), (tx, tz) = course_pt(d)
        return x + tz * off, z - tx * off
    ds = [p[3] for p in P]
    for s0, s1 in c["farBank"]["spans"]:
        bd = [s0 + i * 5 for i in range(int((s1 - s0) / 5) + 1)]
        ax.add_patch(Polygon([behind(d, BANK["foot"]) for d in bd] + [behind(d, BANK["back"]) for d in bd[::-1]], closed=True, fc=BANKC, ec="none"))
        ax.plot(*zip(*[behind(d, sum(BANK["crest"]) / 2) for d in bd]), color=CREST, lw=1.0)
    FE = c["festival"]
    ax.add_patch(Rectangle((FE["x"][0], FE["z"][0]), FE["x"][1] - FE["x"][0], FE["z"][1] - FE["z"][0], fc="#f1d9a8", ec="#b49a6a", lw=0.6))
    ax.text(FE["x"][1] + 20, (FE["z"][0] + FE["z"][1]) / 2 + 30, "festival area", ha="left", va="center", fontsize=9, color=INK)
    for t in c["trees"]["list"]:
        ax.add_patch(Ellipse((t[0], t[1]), 9 * t[3], 9 * t[3], fc=LEAF[hash(t[2]) % len(LEAF)], ec="none", alpha=0.9))
    ax.add_patch(Polygon([(p[0], p[1]) for p in P] + [left(d, TRACK_W) for d in ds[::-1]], closed=True, fc=TURF, ec="none"))
    ax.plot([p[0] for p in P], [p[1] for p in P], color=RAIL, lw=1.4); ax.plot(*zip(*[left(d, TRACK_W) for d in ds]), color=RAIL, lw=1.4)
    for mid, count in BOARD_RUNS:                            # each run of boards as one short dark stroke
        a, b = behind(mid - count * BOARD_LEN / 2, BOARDS_BEHIND + 6), behind(mid + count * BOARD_LEN / 2, BOARDS_BEHIND + 6)
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#24324f", lw=3.2, solid_capstyle="butt")
    S = c["stands"]
    ax.add_patch(Rectangle((S["x"][0], S["front"]), S["x"][1] - S["x"][0], 34, fc=STAND, ec="#8d826b", lw=0.8))
    ax.text(S["x"][0], S["front"] + 62, "Stands (bigger and longer than life)", ha="left", va="center", fontsize=9, color=INK)
    ax.plot([0, 0], [0, TRACK_W], color=POST, lw=2.2); ax.text(-20, TRACK_W / 2, "post", ha="right", va="center", fontsize=9, color=POST)
    for name, s in c["starts"].items():
        (x, z), (tx, tz) = course_pt(s["distance"]); nx, nz = tz, -tx
        ax.plot([x, x + nx * TRACK_W], [z, z + nz * TRACK_W], color=INK, lw=1.1)
        lx, lz = x + nx * (TRACK_W + 28), z + nz * (TRACK_W + 28)
        ax.text(lx, lz, name, ha="center", va="center", fontsize=8.5, color=INK)
    for p in c["furlongPoles"]:
        if p["furlongs"] <= 10: ax.plot(p["at"][0], p["at"][1], marker="|", color=INK, ms=7)
    ax.annotate("running", xy=(1350, TRACK_W + 70), xytext=(1700, TRACK_W + 70), arrowprops=dict(arrowstyle="->", color=INK), fontsize=8.5, va="center", color=INK)
    lab = behind(1000, sum(BANK["crest"]) / 2)
    ax.annotate("the far bank, about %d m high, round to where the July Course crosses" % BANK["height"], xy=lab, xytext=(lab[0] - 150, lab[1] - 260),
                arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=9, color=INK, ha="center")
    tl = behind(1600, 100)
    ax.annotate("tree tops beyond the bank", xy=tl, xytext=(tl[0] - 200, tl[1] - 300), arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=9, color=INK, ha="center")
    bl = behind(640, BOARDS_BEHIND + 6)
    ax.annotate("advertising boards in short runs (dark strokes)", xy=bl, xytext=(bl[0] + 120, bl[1] - 420), arrowprops=dict(arrowstyle="-", color=INK, lw=0.7), fontsize=9, color=INK, ha="center")
    ax.set_aspect("equal"); ax.invert_yaxis()
    allx = [p[0] for p in P] + [t[0] for t in c["trees"]["list"]]; allz = [p[1] for p in P] + [t[1] for t in c["trees"]["list"]]
    ax.set_xlim(min(allx) - 60, max(allx) + 140); ax.set_ylim(max(allz) + 150, min(allz) - 60)
    ax.set_title("Newmarket, Rowley Mile: draft layout, third version (interpretive, metres; as your plans: the post on the left, the bend on the right, north at the bottom)", fontsize=11, color=INK, loc="left")
    ax.tick_params(labelsize=7, colors=MUTED)

    # ---- the cross-section, 3f out, looking up the course (the far side on the left, the stands on the right)
    EX = 3.0                                                  # heights drawn three times their real size
    z0, z1 = -165.0, S["front"] + 40
    zz = [z0 + i * 0.5 for i in range(int((z1 - z0) / 0.5) + 1)]
    gh = [bank_h(-z) if z < 0 else 0.0 for z in zz]
    xs.fill_between(zz, [h * EX for h in gh], -3, color=BANKC)
    xs.fill_between([0, TRACK_W], [0, 0], -3, color=TURF)
    xs.plot(zz, [h * EX for h in gh], color=INK, lw=1.0)
    for zr in (0, TRACK_W):
        xs.plot([zr, zr], [0, 1.1 * EX], color="#bbb", lw=1.6)
    xs.add_patch(Rectangle((-BOARDS_BEHIND - 0.15, 0.6 * EX), 0.3, 1.2 * EX, fc=BOARD_C["navy"], ec="none"))
    xs.text(-BOARDS_BEHIND, 2.1 * EX, "board", ha="center", fontsize=8, color=INK)
    import random
    rr = random.Random(3)
    for k in range(9):                                       # a few trees beyond the bank, drawn to scale (x3 in height)
        tz_ = -(TREES["from"] + 4 + k * 10 + rr.uniform(-3, 3)); hgt = rr.uniform(10.5, 13.5) * rr.uniform(1.0, 1.6)
        xs.plot([tz_, tz_], [0, hgt * 0.45 * EX], color="#6b5a45", lw=1.2)
        xs.add_patch(Ellipse((tz_, hgt * 0.68 * EX), 9.5, hgt * 0.62 * EX, fc=LEAF[k % len(LEAF)], ec="none"))
    xs.add_patch(Rectangle((S["front"], 0), 34, S["height"] * EX, fc=STAND, ec="#8d826b", lw=0.8))
    xs.text(S["front"] + 17, S["height"] * EX + 4, "stands", ha="center", fontsize=8.5, color=INK)
    crest = (-sum(BANK["crest"]) / 2, BANK["height"])
    shades = {"tracking car": "#c0392b", "stand camera": "#2a6f97", "drone": "#7b5ea7"}
    for name, (cz, cy) in CAMS.items():
        slope = (cy - crest[1]) / (cz - crest[0])
        zl = z0
        xs.plot([cz, zl], [cy * EX, (crest[1] + slope * (zl - crest[0])) * EX], color=shades[name], lw=1.0, ls="--")
        xs.plot(cz, cy * EX, marker="o", color=shades[name], ms=6)
        xs.text(cz + 3, cy * EX + 3, name, fontsize=8.5, color=shades[name], ha="left")
    xs.text(-9, -2.2, "far rail", fontsize=8, ha="center", color=INK); xs.text(TRACK_W + 4, -2.2, "near rail", fontsize=8, ha="left", color=INK)
    xs.text(TRACK_W / 2, -2.2, "the track (%d m)" % TRACK_W, fontsize=8.5, ha="center", color=INK)
    xs.text(-sum(BANK["crest"]) / 2, BANK["height"] * EX + 3, "bank crest, %d m" % BANK["height"], fontsize=8.5, ha="center", color=INK)
    xs.set_xlim(z0, z1); xs.set_ylim(-3, (S["height"] + 3) * EX)
    xs.set_xlabel("metres across the course (0 = the far rail); heights drawn x%d" % EX, fontsize=9)
    xs.set_yticks([0, 5 * EX, 10 * EX, 15 * EX, 20 * EX, 25 * EX]); xs.set_yticklabels(["0", "5", "10", "15", "20", "25 m"])
    for hz in (8.0, 14.0, 21.0):                             # horses for scale (2.5 m to the jockey's cap)
        xs.add_patch(Rectangle((hz - 0.8, 0), 1.6, 2.5 * EX, fc="#5b3a29", ec="none"))
    xs.text(14.0, 2.5 * EX + 3, "horses", ha="center", fontsize=8, color=INK)
    xs.set_title("Across the course, 3f out, looking up the course: everything below each dashed line is hidden from that camera behind the bank", fontsize=10, loc="left")
    xs.tick_params(labelsize=8)

    # ---- the height profile of the straight
    dd = [d / 1.0 for d in range(-120, int(STRAIGHT) + 1, 5)]
    pr.fill_between([d / F for d in dd], [height(d) for d in dd], -4, color=TURF, alpha=0.6)
    pr.plot([d / F for d in dd], [height(d) for d in dd], color=INK, lw=1.2)
    pr.axvline(0, color=POST, lw=1.2); pr.axvline(1, color="#888", lw=0.8, ls="--"); pr.axvline(2, color="#888", lw=0.8, ls="--")
    pr.text(0.95, 2.2, "the bottom of the Dip, 1f", ha="right", fontsize=8.5); pr.text(2.05, 2.2, "the Bushes, 2f", ha="left", fontsize=8.5)
    pr.set_xlim(-RUN_ON / F, STRAIGHT / F); pr.set_ylim(-4, 3)
    pr.set_xlabel("furlongs to go (the straight)", fontsize=9); pr.set_ylabel("height (m)", fontsize=9)
    pr.set_title("The straight's height profile: down into the Dip from 2f, up to the post (heights exaggerated on this chart only)", fontsize=10, loc="left")
    pr.tick_params(labelsize=8)
    fig.savefig(REPO / "reference/newmarket/plan-draft.png")


if __name__ == "__main__":
    # The two Newmarket courses are built together, so neither puts trees, boards or banks on the other.
    import site_plan
    site_plan.main()
