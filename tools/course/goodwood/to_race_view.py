"""Goodwood for the 3D race view (race-view/final-furlong.html?course=goodwood), phase 2: the track on its real ground.

    python3 tools/course/goodwood/layout.py          (the plan: courses/goodwood-draft.json)
    python3 tools/course/goodwood/to_race_view.py    (this: the race view's files)
    node tools/course/goodwood/calibrate.mjs         (the par times, so the engine's winning times match TARGET below)

Writes, as York's:
    race-view/assets/course/goodwood.json            the layout: each route's rail, bends and heights, the turf, rails, poles,
                                                     and the ground (a grid of the real heights, against the post's)
    race-view/assets/course/goodwood-view.json       the races, the cameras, the TV director
    race-view/assets/course/goodwood-stalls.json     where the stalls stand (Ascot's stall kit)
    race-view/assets/course/goodwood-standards.json  par times and the going
    race-view/assets/course/goodwood-scenery.json    for now only the finish-line kit (the edges, stands and the long views
                                                     come in the next phases)

Goodwood is RIGHT-handed (hand 1, as Ascot and the Rowley Mile: the stands beyond the outer rail, +z), has several routes
(as York) and real slopes: every route carries its own heights (the race engine reads them: runRace takes the start's
route's heights), and the turf, rails, stalls, horses and cameras all stand on the ground grid ("drapeTurf": each route's
turf strip laid on the ground, not a flat outline).
"""
import json, math, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools/course/newmarket"))
import to_race_view as NM          # Newmarket's: the shared light, ground colours, cameras and view file
import importlib.util
_spec = importlib.util.spec_from_file_location("goodwood_layout", HERE / "layout.py")
LY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LY)   # Goodwood's plan: the post, the axes, the ground

OUT = REPO / "race-view/assets/course"
F = 201.168
GAP = 0.4                          # the rails stand this far off the turf's edge (Ascot's)
STALL1, STALL_PITCH, STANDS_BEHIND = 1.625, 1.05, 1.55
MAX_RUNNERS = 22                   # 26 m of track: 22 stalls
GROUND_CELL = 20.0                 # the ground grid's spacing (the heights are a 20 m grid)
BEHIND = 40.0                      # each route's rail carries on this far behind its furthest start

# Rough winning times of a good horse on good ground (from memory, to check against real results: the King George about
# 57-58 s, the Stewards' Cup about 70 s, the Sussex Stakes about 1m37-38s, the Nassau about 2m05s for its 1m1f197y, the
# Gordon about 2m35s for 1m3f218y (the owner's video, 17 Nov: a handicap in 2m35.17s), the Goodwood Cup about 3m28s), at
# our distances. PAR (what the engine is handed) is set by calibrate.mjs so its winning times come out at these.
TARGET = {"5f": 57.5, "6f": 70.0, "7f": 85.0, "1m": 97.5, "9f": 112.0, "9f192y": 124.5, "1m3f": 155.5, "1m4f": 155.5,
          "1m6f": 182.0, "2m": 210.0, "2m4f": 268.0, "2m5f": 283.0}
LABEL = {"9f192y": "1m1f192y", "1m3f": "1m3f218y", "9f": "1m1f"}
PAR_FILE = HERE / "goodwood-par.json"


def r2(v): return round(v, 2)


def route_bits(route, W):
    """a route's rail (world x, z every 'spacing' m from d0 metres to go), its running directions, the horses' left (where
    the track lies: right-handed), the far edge and the turf strip"""
    pts = route["insideRail"]
    n = len(pts)
    tan = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]       # towards fewer metres to go
        dx, dz = a[0] - b[0], a[1] - b[1]
        l = math.hypot(dx, dz) or 1
        tan.append((dx / l, dz / l))
    left = [(tz, -tx) for tx, tz in tan]                        # the horses' left: across the track, away from the rail
    outer = [[p[0] + l[0] * W, p[1] + l[1] * W] for p, l in zip(pts, left)]
    strip = Polygon(pts + outer[::-1]).buffer(0)
    return tan, left, outer, strip


def ground_grid(C, margin=420.0):
    """the real ground (the 20 m heights, against the post's) over the course and 'margin' metres round it, in world
    axes; at the grid's edges it eases to the edges' typical height, where the race view's flat far ground lies"""
    pts = np.array([p for r in C["routes"].values() for p in r["insideRail"]])
    x0 = math.floor((pts[:, 0].min() - margin) / GROUND_CELL) * GROUND_CELL
    z0 = math.floor((pts[:, 1].min() - margin) / GROUND_CELL) * GROUND_CELL
    x1, z1 = pts[:, 0].max() + margin, pts[:, 1].max() + margin
    nx, nz = int((x1 - x0) / GROUND_CELL) + 2, int((z1 - z0) / GROUND_CELL) + 2
    gx, gz = np.meshgrid(x0 + GROUND_CELL * np.arange(nx), z0 + GROUND_CELL * np.arange(nz))
    E = LY.POST[None, None, :] + gx[..., None] * LY.XH[None, None, :] + gz[..., None] * LY.ZH[None, None, :]
    h0 = C["postGroundM"]
    hh = np.vectorize(lambda e, n: LY.ground((e, n)))(E[..., 0], E[..., 1]) - h0
    # a light smoothing (3 x 3), so the ground under the track agrees with the routes' smoothed heights
    p = np.pad(hh, 1, mode="edge")
    hh = sum(p[1 + a:1 + a + nz, 1 + b:1 + b + nx] for a in (-1, 0, 1) for b in (-1, 0, 1)) / 9.0
    edge_h = float(np.median(np.concatenate([hh[0], hh[-1], hh[:, 0], hh[:, -1]])))
    # (no easing at the edges: the far land (farland.py) carries the real ground on from the grid's edge)
    return {"x0": x0, "z0": z0, "cell": GROUND_CELL, "nx": nx, "nz": nz, "h": [round(float(v), 2) for v in hh.ravel()],
            "farY": round(edge_h, 2),
            "note": "Goodwood's real ground (AWS Terrain Tiles, reference/goodwood/dem-course-20m.json), metres against the post's "
                    "(%.1f m above sea level), every 'cell' metres from (x0, z0), row by row along x; real out to its edges, where "
                    "the far land (goodwood-farland.json) carries on. farY: the edges' typical height." % h0}


def main():
    C = json.loads((REPO / "courses/goodwood-draft.json").read_text())
    W = C["trackWidth"]
    # each route only as far back as its furthest start and a little behind it (the stalls' room): the cup route's rail
    # beyond the 2m5f start, round the run-out's far edge, would otherwise lay a stub of turf there
    for name, r in C["routes"].items():
        far = max(s["distance"] for s in C["starts"].values() if s["route"] == name) + BEHIND
        n = int((far - r["d0"]) / r["spacing"]) + 1
        r["insideRail"] = r["insideRail"][:n]
        r["heights"] = dict(r["heights"], h=r["heights"]["h"][:n])
        r["bends"] = [b for b in r["bends"] if b[1] < far]
        r["bends"] = [[min(b[0], far), b[1], b[2] if b[0] <= far else round(b[2] * (far - b[1]) / (b[0] - b[1]), 1)] for b in r["bends"]]
    routes_out, strips = {}, []
    for name, r in C["routes"].items():
        tan, left, outer, strip = route_bits(r, W)
        strips.append(strip)
        bends = [list(b) for b in r["bends"]]
        home = min([b[1] for b in bends if b[2] > 0], default=0.0)
        routes_out[name] = {"pathRail": {"d0": r["d0"], "spacing": r["spacing"], "points": r["insideRail"]},
                            "path": {"bends": bends, "home": home,
                                     "note": "For the race engine: bends as [metres to go where it starts, where it ends, degrees turned "
                                             "(+ towards the rail, - away from it: the left turn into the loop on the 2m4f and 2m5f)]; "
                                             "'home' = where the home straight starts."},
                            "heights": r["heights"]}
    turf = unary_union(strips).buffer(0.01).buffer(-0.01).simplify(0.15)
    parts = [turf] if turf.geom_type == "Polygon" else sorted(turf.geoms, key=lambda g: -g.area)
    turf = parts[0]
    surface = [[[r2(x), r2(z)] for x, z in turf.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in turf.interiors]
    railed = turf.buffer(GAP, join_style=2, mitre_limit=2.0).simplify(0.1)
    rails = [[[r2(x), r2(z)] for x, z in railed.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in railed.interiors]
    # the furlong poles on the stand-side (outer) rail up the straight, facing the track
    st = C["routes"]["straight"]; tan, left, outer, _ = route_bits(st, W + GAP + 0.7)
    def at_d(d):
        i = int(round((d - st["d0"]) / st["spacing"])); i = max(0, min(len(outer) - 1, i)); return outer[i], tan[i]
    poles = []
    for k in range(1, 7):
        (x, z), (tx, tz) = at_d(k * F)
        poles.append({"furlongs": k, "at": [r2(x), r2(z)], "turn": r2(180 + math.degrees(math.atan2(tz, -tx)))})
    ground = ground_grid(C)
    course = {
        "id": "goodwood", "name": "Goodwood", "status": "draft",
        "_about": "Written by tools/course/goodwood/to_race_view.py from courses/goodwood-draft.json; don't edit by hand. World axes "
                  "as Ascot's: x along the home straight (the horses run towards -x), y up, the winning post on the inside rail is the "
                  "origin. RIGHT-handed (hand 1): each route's rail z 0 on the horses' right, the track on their left, the stands "
                  "beyond the outer rail (+z) on the home straight. Several routes (each race takes its start's route), each with its "
                  "own ground heights for the race engine; the ground grid is the real ground under everything.",
        "axes": C["axes"], "direction": C["direction"], "hand": 1,
        "trackWidth": W, "furlong": F,
        "routes": routes_out, "defaultRoute": "lower",
        "path": routes_out["lower"]["path"], "pathRail": routes_out["lower"]["pathRail"],
        "track": {"surface": surface},
        "rails": {"gap": GAP, "lines": rails, "skip": [[-16.7, 16.3, -GAP]]},
        "straightMile": {"length": round(C["routes"]["straight"]["length"], 1), "furlongPoles": poles},
        "winningPost": [0, 0],
        "ground": ground,
        "drapeTurf": True,
    }
    NM.write("goodwood.json", course)

    # ---- stalls: each start's stalls across the track from its rail, stall 1 on the rail
    asc = json.loads((OUT / "ascot-stalls.json").read_text())
    starts = {}
    keys = {t: "g" + t for t in C["starts"]}
    for t, s in C["starts"].items():
        r = C["routes"][s["route"]]
        pts, sp, d0 = r["insideRail"], r["spacing"], r["d0"]
        f = (s["distance"] - d0) / sp; i = max(1, min(len(pts) - 2, int(f))); k = f - i
        a, b = pts[i], pts[i + 1]
        x, z = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        p0, p1 = pts[i - 1], pts[i + 1]
        tx, tz = p0[0] - p1[0], p0[1] - p1[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        nx, nz = tz, -tx                                          # across the track: the horses' left
        straight = s["route"] == "straight"
        starts[t] = {
            "label": LABEL.get(t, t) + (" (straight)" if straight else ""), "course": "straight" if straight else "round",
            "route": s["route"], "key": keys[t], "distance": s["distance"], "insideRailAt": [r2(x), r2(z)],
            "runningDirection": [round(tx, 4), round(tz, 4)], "towardsOuterRail": [round(nx, 4), round(nz, 4)],
            "stall1": "the rail (the horses' right)", "onStraight": straight,
            # the 2m4f and 2m5f start by the post and finish there: the stalls are towed away after the off
            "comesBack": s["route"] == "cup",
            "stalls": [{"draw": j + 1, "fromInsideRail": round(STALL1 + STALL_PITCH * j, 3), "across": round(STALL1 + STALL_PITCH * j - W / 2, 3),
                        "at": [r2(x + nx * (STALL1 + STALL_PITCH * j)), r2(z + nz * (STALL1 + STALL_PITCH * j))]} for j in range(MAX_RUNNERS)],
        }
    stalls = {"_about": "Goodwood's starting stalls, DRAFT (tools/course/goodwood/to_race_view.py), with Ascot's stall kit and gates. "
                        "Distances from the gate line along the route's rail; stall 1 on the rail.",
              "horseStandsBehind": STANDS_BEHIND, "gates": asc["gates"], "kit": asc["kit"], "maxRunners": MAX_RUNNERS,
              "unitsForField": {k: v for k, v in asc["unitsForField"].items() if int(k) <= MAX_RUNNERS}, "starts": starts}
    NM.write("goodwood-stalls.json", stalls, 1)

    # ---- standards: par times (calibrate.mjs) and the going and pace bands (as York's)
    nm = json.loads((OUT / "newmarket-july-standards.json").read_text())
    par = json.loads(PAR_FILE.read_text())["par"] if PAR_FILE.exists() else {}
    standards = {"_about": "Par (standard) times at Goodwood, DRAFT, for the race engine and the race view's dock. 'winningTime' is a "
                           "rough winning time for a good horse on good ground (from memory: check against real results); 'seconds' is "
                           "the par the engine uses, set by tools/course/goodwood/calibrate.mjs so its winning times come out at those.",
                 "parTimes": [{"key": keys[t], "course": "straight" if s["route"] == "straight" else "round", "distance": s["distance"],
                               "seconds": par.get(keys[t], round(TARGET[t] * 0.978, 2)), "winningTime": TARGET[t]} for t, s in C["starts"].items()],
                 "going": nm["going"], "pace": nm["pace"]}
    NM.write("goodwood-standards.json", standards, 1)

    # ---- the view: cameras as the Rowley Mile's (stands beyond the outer rail, +z)
    sun = [-90, 49.5, 55.0]                                      # the afternoon sun from the south-west, behind the stands
    cams = NM.cameras(W, +1, [0, 16, W + 15], ([-8, 6.5, -0.8], [0, 6.0, W * 0.65]), -55.0, sun)
    cams["sideon"]["fov"] = [46, 46]
    cams["track_straight"]["raise"] = []
    # the racecard view: over the infield by the post, looking across at the stands and up the straight
    prelude = {"label": "The runners", "seconds": 9, "eye": [[-50, 16, -24], [-38, 15, -22]],
               "at": [[150, 4, 60], [165, 4, 62]], "fov": 46, "list": [7, 0.6], "cardAfter": 3.5}
    postlude = NM.overview_after(prelude)
    director = {"tracking": True, "grandstand": 2 * F}
    menu = {"straight": [["track_straight", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]],
            "round": [["track_loop", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]]}

    class L:                                                       # what NM.view_file reads of a layout
        TRACK_W = W; RUN_ON = C["runOut"]; STRAIGHT = C["routes"]["straight"]["length"]
    view = NM.view_file("goodwood", L, {"name": "Goodwood"}, stalls, 1, cams, prelude, postlude, director, menu)
    view["lanesStraight"]["x"][0] = 0.0                                # the mown lanes stop at the line: the run-out bends away
    view["treeDetail"]["centre"] = [150, W / 2]
    view["_about"] = ("The race view's cameras and dressing for Goodwood. Written by tools/course/goodwood/to_race_view.py; don't edit by "
                      "hand. World axes as goodwood.json (right-handed: the stands on +z).")
    view["races"]["_default"] = "1m"
    for k, st in stalls["starts"].items():
        view["races"][k]["label"] = LABEL.get(k, k)
    # the dock's course map reads as the racing papers' plan as it is: the straight along the bottom, the post on the left,
    # the stands below, the loop above on the right
    view["mapTurn"] = 0
    view["ground"]["farY"] = ground["farY"]
    view["farLand"] = "goodwood-farland.json"            # the long views (tools/course/goodwood/farland.py)
    NM.write("goodwood-view.json", view, 1)

    # ---- scenery: the finish-line kit on the rail at the post, and the perimeter (phase 3: tools/course/goodwood/
    # perimeter.py); the stands come in phase 4
    import random
    S = NM.Scene(17, ground)
    rnd = random.Random(17)
    spots = json.loads((REPO / "assets/models/architecture/site_props_spots.json").read_text())["pieces"]

    def sp(piece, x, z, turn=180.0, people=0.85, sxf=1.0, sc=1.0):
        """a site prop (marquee, kiosk, flag...), kept clear of the crowd, with its own people on its seats and steps"""
        S.piece("site_props", piece, x, z, turn, sxf, sc)
        w, d = NM.SP_SIZE[piece]
        S.nogo.append([(x - w / 2 * sxf * sc - 0.5, z - d / 2 * sc - 0.5), (x + w / 2 * sxf * sc + 0.5, z - d / 2 * sc - 0.5),
                       (x + w / 2 * sxf * sc + 0.5, z + d / 2 * sc + 0.5), (x - w / 2 * sxf * sc - 0.5, z + d / 2 * sc + 0.5)])
        ca_, sa_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        for kind in ("seats", "stand"):
            for lx, ly, lz in spots.get(piece, {}).get(kind, []):
                if rnd.random() < people:
                    S.person(x + lx * ca_ - ly * sa_, lz, z - (lx * sa_ + ly * ca_), NM.face(0, 1))
    # phase 4: the stands, the rail lawn and the festival lawns, from the owner's mark-up (tools/course/goodwood/stands.py)
    _ss = importlib.util.spec_from_file_location("goodwood_stands", HERE / "stands.py")
    ST = importlib.util.module_from_spec(_ss); _ss.loader.exec_module(ST)
    _ps = importlib.util.spec_from_file_location("goodwood_perimeter", HERE / "perimeter.py")
    PM = importlib.util.module_from_spec(_ps); _ps.loader.exec_module(PM)
    stands_all, far_fest, stand_cam, side_trees, note4 = ST.stand_side(S, turf, sp, rnd, NM, PM.zones()["stands"])
    grid_box = (ground["x0"], ground["z0"], ground["x0"] + ground["cell"] * (ground["nx"] - 1), ground["z0"] + ground["cell"] * (ground["nz"] - 1))
    trees, boards, canopies, note = PM.perimeter(S, turf, grid_box, sp, rnd)
    # (owner, 18 Nov: the far side's festival "can start as the trees start to drop away": no trees in it; nothing in the stands)
    from shapely.geometry import Point
    clear = far_fest.buffer(4.0).union(stands_all.buffer(3.0))
    trees = [t for t in trees if not clear.contains(Point(t[0], t[1]))]
    boards = [b for b in boards if not stands_all.buffer(2.0).contains(Point(b[0], b[1]))]
    trees += side_trees
    boards, trees, n_angled = ST.angled_adverts(S, turf, boards, trees)
    note4["far-side hoardings"] = n_angled
    scen = NM.scenery_file(S, trees, boards, [], ["goodwood_stands", "site_props", "finish_line"], {"at": [0, -GAP], "turn": 0}, poles)
    scen["canopies"] = canopies
    scen["_about"] += (" canopies: the woods beyond the belts of trees, each a light mesh (v: x, y above the ground, z; i: triangles), "
                       "drawn as a soft roof of leaves.")
    NM.write("goodwood-scenery.json", scen)
    print("   perimeter:", json.dumps(note))
    print("   stand side:", json.dumps(note4))
    view = json.loads((OUT / "goodwood-view.json").read_text())        # the stand camera, on the mast stand's balcony
    view["raceCameras"]["grandstand"]["at"] = stand_cam
    NM.write("goodwood-view.json", view, 1)
    print("  ", len(S.pieces), "pieces,", len(S.people) // 4, "people,", len(trees), "trees,", len(boards), "boards,",
          sum(len(v) for v in S.boxes.values()), "hedge lengths,", len(canopies), "canopies")
    print("turf area %.0f m2, %d rail lines, %d starts; ground %d x %d, %.0f to %.0f m against the post" %
          (turf.area, len(rails), len(starts), ground["nx"], ground["nz"], min(ground["h"]), max(ground["h"])))


if __name__ == "__main__":
    main()
