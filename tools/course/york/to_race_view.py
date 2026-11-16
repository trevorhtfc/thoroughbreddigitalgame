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


def main():
    C = json.loads((REPO / "courses/york-draft.json").read_text())
    W = C["trackWidth"]
    routes_out, strips = {}, []
    for name, r in C["routes"].items():
        tan, right, outer, strip = route_bits(r, W)
        strips.append(strip)
        bends = [[b[0], b[1], abs(b[2])] for b in r["bends"]]
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
    cams = NM.cameras(W, +1, [0, 14, W + 28], ([-8, 6.5, 0.8], [0, 6.0, W * 0.65]), -C["runOut"] + 12, sun)
    mz = lambda p: [p[0], p[1], r2(-p[2])]
    cams["grandstand"]["at"] = mz(cams["grandstand"]["at"])
    cams["headon"]["at"] = mz(cams["headon"]["at"])
    cams["sideon"]["at"], cams["sideon"]["look"] = mz(cams["sideon"]["at"]), mz(cams["sideon"]["look"])
    cams["sideon"]["fov"] = [46, 46]
    cams["track_straight"]["raise"] = []
    prelude = {"label": "The runners", "seconds": 9, "eye": [[-40, 14, -(W + 31)], [-30, 13, -(W + 28)]],
               "at": [[480, 2, -W * 0.1], [490, 2, -W * 0.2]], "fov": 42, "list": [7, 0.6], "cardAfter": 3.5}
    postlude = NM.overview_after(prelude)
    director = {"tracking": True, "grandstand": 2 * F}
    menu = {"straight": [["track_straight", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]],
            "round": [["track_loop", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]]}

    class L:                                                       # what NM.view_file reads of a layout
        TRACK_W = W; RUN_ON = C["runOut"]; STRAIGHT = C["home"]
    view = NM.view_file("york", L, {"name": "York"}, stalls, -1, cams, prelude, postlude, director, menu)
    view["homeStraight"]["centreZ"] = -W / 2
    view["treeDetail"]["centre"] = [150, -W / 2]
    view["_about"] = ("The race view's cameras and dressing for York. Written by tools/course/york/to_race_view.py; don't edit by hand. "
                      "World axes as york.json (left-handed: the stands on -z).")
    view["races"]["_default"] = "1m2f"
    NM.write("york-view.json", view, 1)

    # ---- scenery: the finish-line kit on the inside (infield) rail at the line, facing the stands across the track; the
    # rest comes in the next phases (edges and borders, then the stands and the festival)
    scen = NM.scenery_file(type("S", (), {"pieces": [], "boxes": {}, "flats": {}, "people": []}), [], [], [], ["finish_line"],
                           {"at": [0, GAP], "turn": 180}, poles)
    NM.write("york-scenery.json", scen)
    print("turf area %.0f m2, %d rail lines, %d starts" % (turf.area, len(rails), len(starts)))


if __name__ == "__main__":
    main()
