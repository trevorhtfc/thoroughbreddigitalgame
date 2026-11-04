"""Place the starting stalls for each of Ascot's starts and write courses/ascot-stalls.json.

    python3 tools/course/place_stalls.py

Reads courses/ascot.json (the layout) and assets/models/course/starting_stalls_kit.json (the stalls' sizes,
from tools/blender/build_stalls.py). Writes where every stall stands for every start, so the race engine
and the race view read the same thing. Re-run after changing the layout or the kit.

The draw (Ascot's convention, checked against the 2025-26 Royal Ascot draw tables):
  straight course: stall 1 on the far side (the inside rail, z 0, away from the stands), high numbers on the
                   stands' side
  round course:    stall 1 against the inside rail, on the horses' right (Ascot is right-handed)
Both come to the same rule on this layout: stall 1 is the stall nearest the inside rail, numbers rising
towards the outer rail.

How a set of stalls is made up: units of up to UNIT bays, each with an end tower either side (a tower
between neighbouring units), the first tower RAIL_GAP metres off the inside rail. Stall n stands in the
same place whatever the field size; a field of N uses ceil(N / UNIT) units, the last one holding the rest.
"""
import json, math, os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
C = json.load(open(os.path.join(REPO, "courses/ascot.json")))
KIT = json.load(open(os.path.join(REPO, "assets/models/course/starting_stalls_kit.json")))
P, T = KIT["pitch"], KIT["towerWidth"]
W = C["trackWidth"]
UNIT = 5                  # bays in a unit
RAIL_GAP = 1.0            # inside rail to the first tower
FAR_GAP = 0.8             # the least room left between the last tower and the outer rail


def loop_at(d):
    """Point on the round course's inside rail with d metres still to run, and the running direction."""
    rc = C["roundCourse"]
    pts, sp = rc["insideRail"]["points"], rc["insideRail"]["spacing"]
    n = len(pts); L = n * sp
    s = (-d) % L
    f = s / sp; i = int(f) % n; j = (i + 1) % n; k = f - int(f)
    tan = []
    for a in (i, j):
        (px, pz), (qx, qz) = pts[(a - 1) % n], pts[(a + 1) % n]
        l = math.hypot(qx - px, qz - pz); tan.append(((qx - px) / l, (qz - pz) / l))
    tx = tan[0][0] + (tan[1][0] - tan[0][0]) * k; tz = tan[0][1] + (tan[1][1] - tan[0][1]) * k
    l = math.hypot(tx, tz)
    return (pts[i][0] + (pts[j][0] - pts[i][0]) * k, pts[i][1] + (pts[j][1] - pts[i][1]) * k), (tx / l, tz / l)


def across(n):
    """Metres from the inside rail to the middle of stall n (1-based)."""
    u, j = divmod(n - 1, UNIT)
    return RAIL_GAP + T + u * (UNIT * P + T) + j * P + P / 2


def units_for(field):
    """The units a field of this size needs: [first stall, last stall] each."""
    return [[a, min(a + UNIT - 1, field)] for a in range(1, field + 1, UNIT)]


MAX = 0
while True:                                    # the most stalls that fit across the track
    n = MAX + 1
    u = (n - 1) // UNIT
    right = RAIL_GAP + T + u * (UNIT * P + T) + ((n - 1) % UNIT + 1) * P + T
    if right > W - FAR_GAP:
        break
    MAX = n

sm, sp = C["straightMile"], C["roundMileSpur"]
fx, fz = sp["from"]; tx, tz = sp["to"]; l = math.hypot(tx - fx, tz - fz)
TWO_MILES = 3218.7
starts = {
    "straightMile": {"label": "Straight mile (8f)", "course": "straight", "distance": sm["length"],
                     "rail": sm["stalls"], "run": (-1.0, 0.0), "where": "the straight mile's stalls at the top of the straight course"},
    "roundMile": {"label": "Round mile (8.2f)", "course": "roundMile", "distance": sp["startDistance"],
                  "rail": sp["from"], "run": ((tx - fx) / l, (tz - fz) / l), "where": "the start of the chute (round-mile spur) at the top of the right-hand straight"},
    "twoMiles": {"label": "2 miles", "course": "round", "distance": TWO_MILES,
                 "rail": None, "run": None, "where": "on the home straight, %.0f m before the post: the field passes the stand twice" % (TWO_MILES - C["roundCourse"]["length"])},
}
p, r = loop_at(TWO_MILES)
starts["twoMiles"]["rail"], starts["twoMiles"]["run"] = [round(p[0], 2), round(p[1], 2)], r

out = {
    "_about": "Where the starting stalls stand for each start at Ascot. Written by tools/course/place_stalls.py from "
              "courses/ascot.json and the stalls kit; don't edit by hand. World axes as courses/ascot.json (x east, "
              "z south, y up). For the race engine and the race view alike.",
    "draw": {
        "rule": "Stall 1 is the stall nearest the inside rail; numbers rise towards the outer rail. A horse's stall number is its draw.",
        "straight": "Straight course: stall 1 on the far side (the inside rail, away from the stands); high numbers on the stands' side.",
        "round": "Round course: stall 1 against the inside rail, on the horses' right (Ascot is right-handed).",
    },
    "theOff": "The race starts when the gates open: race time 0, distance 0. Distances run are measured from the gate line "
              "(the front of the stalls) along the inside rail. Anything before that is the race view's own pre-roll.",
    "atTheOff": "Each horse stands in its stall with its middle horseStandsBehind metres behind the gate line (its nose at "
                "the gates), at its stall's distance from the inside rail.",
    "horseStandsBehind": KIT["horseStandsAt"]["behindFront"],
    "gates": {"swingSeconds": 0.22, "openDegrees": KIT["openDegrees"],
              "note": "Both half-gates of every stall spring open together at the off and swing out through openDegrees in swingSeconds."},
    "kit": {"file": KIT["file"], "sizes": "assets/models/course/starting_stalls_kit.json", "unitBays": UNIT,
            "railGap": RAIL_GAP, "pitch": P, "towerWidth": T, "depth": KIT["depth"]},
    "maxRunners": MAX,
    "unitsForField": {str(n): units_for(n) for n in range(1, MAX + 1)},
    "starts": {},
}
for key, s in starts.items():
    (x0, z0), (rx, rz) = s["rail"], s["run"]
    ox, oz = rz, -rx                           # across the track towards the outer rail (horses' left)
    stalls = []
    for n in range(1, MAX + 1):
        a = across(n)
        stalls.append({"draw": n, "fromInsideRail": round(a, 3), "across": round(a - W / 2, 3),
                       "at": [round(x0 + ox * a, 2), round(z0 + oz * a, 2)]})
    out["starts"][key] = {
        "label": s["label"], "course": s["course"], "distance": round(s["distance"], 1), "where": s["where"],
        "insideRailAt": [round(x0, 2), round(z0, 2)],
        "runningDirection": [round(rx, 5), round(rz, 5)],
        "towardsOuterRail": [round(ox, 5), round(oz, 5)],
        "stall1": "far side (inside rail)" if s["course"] == "straight" else "inside rail, on the horses' right",
        "stalls": stalls,
        "_stalls": "at = the middle of the stall on the gate line (world x, z); fromInsideRail = metres from the inside "
                   "rail; across = metres from the middle of the track (+ towards the outer rail), as the race view's v",
    }
path = os.path.join(REPO, "courses/ascot-stalls.json")
json.dump(out, open(path, "w"), indent=1)
print("wrote %s: up to %d runners; units of %d" % (os.path.relpath(path, REPO), MAX, UNIT))
for k, s in out["starts"].items():
    print("  %-13s %7.1f m  rail at %s  stall 1 at %s, stall %d at %s" % (k, s["distance"], s["insideRailAt"], s["stalls"][0]["at"], MAX, s["stalls"][-1]["at"]))
