"""Epsom for the 3D race view (race-view/final-furlong.html?course=epsom), phase 2: the track on its ground.

    python3 tools/course/epsom/layout.py          (the plan: courses/epsom-draft.json)
    python3 tools/course/epsom/to_race_view.py    (this: the race view's files)
    node tools/course/epsom/calibrate.mjs         (the par times, so the engine's winning times match TARGET below)

Writes, as York's and Goodwood's:
    race-view/assets/course/epsom.json            the layout: each route's rail, bends and heights, the turf, rails, poles,
                                                  and the ground (a grid of heights, against the post's)
    race-view/assets/course/epsom-view.json       the races, the cameras, the TV director
    race-view/assets/course/epsom-stalls.json     where the stalls stand (Ascot's stall kit)
    race-view/assets/course/epsom-standards.json  par times and the going
    race-view/assets/course/epsom-scenery.json    for now only the finish-line kit and the furlong poles (the edges, the
                                                  stands and the Hill come in the next phases)

Epsom is LEFT-handed (hand -1, as York: the stands beyond the outer rail, -z) and climbs and falls (as Goodwood: every
route carries its own heights for the race engine, and the turf is laid on the ground grid, "drapeTurf"). The ground grid
is not measured yet: it is grown from the routes' estimated heights (layout.py ROUND_H) with the home straight's camber
(the far, inside rail lower), smoothed out across the infield and round the course.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.interpolate import RBFInterpolator
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools/course/newmarket"))
import to_race_view as NM          # Newmarket's: the shared light, ground colours, cameras and view file
import importlib.util
_spec = importlib.util.spec_from_file_location("epsom_layout", HERE / "layout.py")
LY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LY)   # Epsom's plan: the post, the axes, the heights

OUT = REPO / "race-view/assets/course"
F = 201.168
GAP = 0.4                          # the rails stand this far off the turf's edge (Ascot's)
STALL1, STALL_PITCH, STANDS_BEHIND = 1.625, 1.05, 1.55
MAX_RUNNERS = 20                   # 26 m of track would take 22; the Derby's biggest fields are about 20 (Epsom's limit)
GROUND_CELL = 20.0
MARGIN = 420.0                     # the ground grid reaches this far beyond the routes
EDGE_EASE = 160.0                  # the ground grid eases to one height over its outer 160 m (no far land yet)
BEHIND = 40.0                      # each route's rail carries on this far behind its furthest start

# Rough winning times of a good horse on good ground (from memory, to check against real results: the Epsom Dash about
# 55 s (the fastest 5f anywhere), 6f about 69 s, 7f about 82 s, the 1m114y about 1m43s, the 1m2f18y about 2m08s, the Derby
# about 2m34-35s). PAR (what the engine is handed) is set by calibrate.mjs so its winning times come out at these.
TARGET = {"5f": 55.0, "6f": 69.0, "7f": 82.0, "1m114y": 103.0, "1m2f18y": 128.0, "1m4f10y": 154.5}
LABEL = {"1m114y": "1m114y", "1m2f18y": "1m2f18y", "1m4f10y": "1m4f10y"}
PAR_FILE = HERE / "epsom-par.json"


def r2(v): return round(v, 2)


def route_bits(route, W):
    """a route's inside rail (world x, z), its running directions, the horses' right (left-handed: towards the outer rail),
    the outer edge and the turf strip"""
    pts = route["insideRail"]
    n = len(pts)
    tan = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]       # towards fewer metres to go
        dx, dz = a[0] - b[0], a[1] - b[1]
        l = math.hypot(dx, dz) or 1
        tan.append((dx / l, dz / l))
    right = [(-tz, tx) for tx, tz in tan]
    outer = [[p[0] + r[0] * W, p[1] + r[1] * W] for p, r in zip(pts, right)]
    strip = Polygon(pts + outer[::-1]).buffer(0)
    return tan, right, outer, strip


def ground_grid(C, W):
    """The ground as a grid (metres against the post). From the real ground (the AWS Terrain Tiles, as Goodwood) when the
    plan is OpenStreetMap's; otherwise grown from the routes' estimated heights (dem_free_grid). At the grid's edges it eases
    over EDGE_EASE metres to the edges' typical height, where the race view's flat far ground lies."""
    if LY.SOURCE != "osm":
        return dem_free_grid(C, W)
    pts = np.array([p for r in C["routes"].values() for p in r["insideRail"]])
    x0 = math.floor((pts[:, 0].min() - MARGIN) / GROUND_CELL) * GROUND_CELL
    z0 = math.floor((pts[:, 1].min() - MARGIN) / GROUND_CELL) * GROUND_CELL
    x1, z1 = pts[:, 0].max() + MARGIN, pts[:, 1].max() + MARGIN
    nx, nz = int((x1 - x0) / GROUND_CELL) + 2, int((z1 - z0) / GROUND_CELL) + 2
    gx, gz = np.meshgrid(x0 + GROUND_CELL * np.arange(nx), z0 + GROUND_CELL * np.arange(nz))
    E = LY.POST[None, None, :] + gx[..., None] * LY.XH[None, None, :] + gz[..., None] * LY.ZH[None, None, :]
    hh = np.vectorize(lambda e, n: LY.ground((e, n)))(E[..., 0], E[..., 1]) - LY.POST_GROUND
    p = np.pad(hh, 1, mode="edge")
    hh = sum(p[1 + a:1 + a + nz, 1 + b:1 + b + nx] for a in (-1, 0, 1) for b in (-1, 0, 1)) / 9.0
    edge_h = float(np.median(np.concatenate([hh[0], hh[-1], hh[:, 0], hh[:, -1]])))
    di = np.minimum(np.arange(nx), np.arange(nx)[::-1])[None, :] * GROUND_CELL
    dj = np.minimum(np.arange(nz), np.arange(nz)[::-1])[:, None] * GROUND_CELL
    w = np.clip(np.minimum(di, dj) / EDGE_EASE, 0, 1); w = w * w * (3 - 2 * w)
    hh = hh * w + edge_h * (1 - w)
    return {"x0": x0, "z0": z0, "cell": GROUND_CELL, "nx": nx, "nz": nz, "h": [round(float(v), 2) for v in hh.ravel()],
            "farY": round(edge_h, 2),
            "note": "Epsom's real ground (AWS Terrain Tiles, reference/epsom/dem-course-20m.json), metres against the post's (%.1f m "
                    "above sea level), every 'cell' metres from (x0, z0), row by row along x; eased over its outer %d m to farY, the "
                    "edges' typical height, where the flat far ground lies." % (LY.POST_GROUND, EDGE_EASE)}


def dem_free_grid(C, W):
    """The ground as a grid (metres against the post), grown from the routes' heights: points down the middle of every
    route every 10 m, and across the home straight its camber (the inside rail CAMBER lower than the outer); a smooth
    surface through them (thin-plate spline), held within the routes' own range so it doesn't run away off the course."""
    P, H = [], []
    for name, r in C["routes"].items():
        tan, right, outer, _ = route_bits(r, W)
        hh = r["heights"]["h"]
        for i in range(0, len(r["insideRail"]), 2):
            d = r["d0"] + i * r["spacing"]
            (x, z), (rx, rz) = r["insideRail"][i], right[i]
            on_home = d < LY.JOIN_STRAIGHT and name != "straight" or (name == "straight" and d < LY.JOIN_STRAIGHT + 60)
            c = C["camber"] if on_home else 0.0
            for f, dh in ((0.0, -c / 2), (0.5, 0.0), (1.0, c / 2)):
                P.append((x + rx * W * f, z + rz * W * f)); H.append(hh[i] + dh)
    P, H = np.array(P), np.array(H)
    # thin the points to one per 8 m square (the routes overlap where they share track)
    key = np.round(P / 8.0).astype(int)
    _, first = np.unique(key, axis=0, return_index=True)
    P, H = P[first], H[first]
    pts = np.array([p for r in C["routes"].values() for p in r["insideRail"]])
    x0 = math.floor((pts[:, 0].min() - MARGIN) / GROUND_CELL) * GROUND_CELL
    z0 = math.floor((pts[:, 1].min() - MARGIN) / GROUND_CELL) * GROUND_CELL
    x1, z1 = pts[:, 0].max() + MARGIN, pts[:, 1].max() + MARGIN
    nx, nz = int((x1 - x0) / GROUND_CELL) + 2, int((z1 - z0) / GROUND_CELL) + 2
    gx, gz = np.meshgrid(x0 + GROUND_CELL * np.arange(nx), z0 + GROUND_CELL * np.arange(nz))
    f = RBFInterpolator(P, H, kernel="thin_plate_spline", smoothing=2.0, neighbors=120)
    hh = f(np.stack([gx.ravel(), gz.ravel()], 1)).reshape(nz, nx)
    lo, hi = H.min() - 4.0, H.max() + 4.0
    hh = np.clip(hh, lo, hi)
    # away from the course the ground eases towards a gentle tilt of the whole area (no ridges running off the grid)
    from scipy.ndimage import gaussian_filter, distance_transform_edt
    near = np.zeros_like(hh, bool)
    ij = np.round((P - [x0, z0]) / GROUND_CELL).astype(int)
    near[np.clip(ij[:, 1], 0, nz - 1), np.clip(ij[:, 0], 0, nx - 1)] = True
    dist = distance_transform_edt(~near) * GROUND_CELL
    soft = gaussian_filter(hh, 8)
    w = np.clip((dist - 120.0) / 260.0, 0, 1); w = w * w * (3 - 2 * w)
    hh = hh * (1 - w) + soft * w
    edge_h = float(np.median(np.concatenate([hh[0], hh[-1], hh[:, 0], hh[:, -1]])))
    return {"x0": x0, "z0": z0, "cell": GROUND_CELL, "nx": nx, "nz": nz, "h": [round(float(v), 2) for v in hh.ravel()],
            "farY": round(edge_h, 2),
            "note": "Epsom's ground, ESTIMATED (not measured): grown from the routes' heights (tools/course/epsom/layout.py ROUND_H) "
                    "and the home straight's camber, metres against the post, every 'cell' metres from (x0, z0), row by row along x. "
                    "To be replaced by the real ground (AWS Terrain Tiles) when it can be fetched. farY: the edges' typical height."}


def main():
    C = json.loads((REPO / "courses/epsom-draft.json").read_text())
    W = C["trackWidth"]
    for name, r in C["routes"].items():
        far = max(s["distance"] for s in C["starts"].values() if s["route"] == name) + BEHIND
        n = int((far - r["d0"]) / r["spacing"]) + 1
        r["insideRail"] = r["insideRail"][:n]
        r["heights"] = dict(r["heights"], h=r["heights"]["h"][:n])
        r["bends"] = [b for b in r["bends"] if b[1] < far]
        r["bends"] = [[min(b[0], far), b[1], b[2] if b[0] <= far else round(b[2] * (far - b[1]) / (b[0] - b[1]), 1)] for b in r["bends"]]
    routes_out, strips = {}, []
    for name, r in C["routes"].items():
        tan, right, outer, strip = route_bits(r, W)
        strips.append(strip)
        bends = [list(b) for b in r["bends"]]
        home = min([b[1] for b in bends if b[2] > 0], default=0.0)
        routes_out[name] = {"pathRail": {"d0": r["d0"], "spacing": r["spacing"], "points": r["insideRail"]},
                            "path": {"bends": bends, "home": home,
                                     "note": "For the race engine: bends as [metres to go where it starts, where it ends, degrees turned "
                                             "(+ towards the rail, left; - away from it: the right-hand kinks early in the Derby course "
                                             "and the chutes)]; 'home' = where the home straight starts."},
                            "heights": r["heights"]}
    turf = unary_union(strips).buffer(0.01).buffer(-0.01).simplify(0.15)
    parts = [turf] if turf.geom_type == "Polygon" else sorted(turf.geoms, key=lambda g: -g.area)
    turf = parts[0]
    surface = [[[r2(x), r2(z)] for x, z in turf.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in turf.interiors]
    railed = turf.buffer(GAP, join_style=2, mitre_limit=2.0).simplify(0.1)
    rails = [[[r2(x), r2(z)] for x, z in railed.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in railed.interiors]
    # the furlong poles on the stand-side (outer) rail up the straight, facing the track (as York's)
    poles = [{"furlongs": k, "at": [r2(k * F), r2(-(W + GAP + 0.7))], "turn": 0} for k in range(1, 5)]
    ground = ground_grid(C, W)
    course = {
        "id": "epsom", "name": "Epsom", "status": "draft",
        "_about": "Written by tools/course/epsom/to_race_view.py from courses/epsom-draft.json; don't edit by hand. World axes as "
                  "York's: x along the home straight (the horses run towards -x), y up, the winning post on the inside rail is the "
                  "origin. LEFT-handed (hand -1): the inside rail z 0 on the horses' left, the track to z = -trackWidth on their "
                  "right, the stands beyond (z < -trackWidth), the infield (the Hill) +z. Several routes (each race takes its "
                  "start's route), each with its own ground heights for the race engine; the turf is laid on the ground grid.",
        "axes": C["axes"], "direction": C["direction"], "hand": -1,
        "trackWidth": W, "furlong": F,
        "routes": routes_out, "defaultRoute": "round",
        "path": routes_out["round"]["path"], "pathRail": routes_out["round"]["pathRail"],
        "track": {"surface": surface},
        "rails": {"gap": GAP, "lines": rails, "skip": [[-16.3, 16.7, GAP]]},
        "straightMile": {"length": round(C["routes"]["straight"]["length"], 1), "furlongPoles": poles},
        "winningPost": [0, 0],
        "ground": ground,
        "drapeTurf": True,
    }
    NM.write("epsom.json", course)

    # ---- stalls: each start's stalls across the track from its inside rail, stall 1 on the inside (the infield side)
    asc = json.loads((OUT / "ascot-stalls.json").read_text())
    starts = {}
    keys = {t: "e" + t for t in C["starts"]}
    for t, s in C["starts"].items():
        r = C["routes"][s["route"]]
        pts, sp, d0 = r["insideRail"], r["spacing"], r["d0"]
        f = (s["distance"] - d0) / sp; i = max(1, min(len(pts) - 2, int(f))); k = f - i
        a, b = pts[i], pts[i + 1]
        x, z = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        p0, p1 = pts[i - 1], pts[i + 1]
        tx, tz = p0[0] - p1[0], p0[1] - p1[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        nx, nz = -tz, tx                                          # towards the outer rail: the horses' right
        straight = s["route"] == "straight"
        starts[t] = {
            "label": LABEL.get(t, t) + (" (straight)" if straight else ""), "course": "straight" if straight else "round",
            "route": s["route"], "key": keys[t], "distance": s["distance"], "insideRailAt": [r2(x), r2(z)],
            "runningDirection": [round(tx, 4), round(tz, 4)], "towardsOuterRail": [round(nx, 4), round(nz, 4)],
            "stall1": "inside rail (the infield side)", "onStraight": straight, "comesBack": False,
            "stalls": [{"draw": j + 1, "fromInsideRail": round(STALL1 + STALL_PITCH * j, 3), "across": round(STALL1 + STALL_PITCH * j - W / 2, 3),
                        "at": [r2(x + nx * (STALL1 + STALL_PITCH * j)), r2(z + nz * (STALL1 + STALL_PITCH * j))]} for j in range(MAX_RUNNERS)],
        }
    stalls = {"_about": "Epsom's starting stalls, DRAFT (tools/course/epsom/to_race_view.py), with Ascot's stall kit and gates. "
                        "Distances from the gate line along the route's inside rail; stall 1 on the inside rail.",
              "horseStandsBehind": STANDS_BEHIND, "gates": asc["gates"], "kit": asc["kit"], "maxRunners": MAX_RUNNERS,
              "unitsForField": {k: v for k, v in asc["unitsForField"].items() if int(k) <= MAX_RUNNERS}, "starts": starts}
    NM.write("epsom-stalls.json", stalls, 1)

    # ---- standards
    nm = json.loads((OUT / "newmarket-july-standards.json").read_text())
    par = json.loads(PAR_FILE.read_text())["par"] if PAR_FILE.exists() else {}
    standards = {"_about": "Par (standard) times at Epsom, DRAFT, for the race engine and the race view's dock. 'winningTime' is a "
                           "rough winning time for a good horse on good ground (from memory: check against real results); 'seconds' is "
                           "the par the engine uses, set by tools/course/epsom/calibrate.mjs so its winning times come out at those.",
                 "parTimes": [{"key": keys[t], "course": "straight" if s["route"] == "straight" else "round", "distance": s["distance"],
                               "seconds": par.get(keys[t], round(TARGET[t] * 0.978, 2)), "winningTime": TARGET[t]} for t, s in C["starts"].items()],
                 "going": nm["going"], "pace": nm["pace"]}
    NM.write("epsom-standards.json", standards, 1)

    # ---- the view: as York's (stands on -z): the fixed cameras mirrored
    sw = LY.world_dir(-(LY.EAST_PX * 0.55 + LY.NORTH_PX * 0.84))   # the sun in the west-south-west, mid-afternoon
    l = math.hypot(*sw)
    sun = [r2(sw[0] / l * 105), 49.5, r2(sw[1] / l * 105)]
    cams = NM.cameras(W, +1, [0, 16, W + 15], ([-8, 6.5, 0.8], [0, 6.0, W * 0.65]), -70.0, sun)
    mz = lambda p: [p[0], p[1], r2(-p[2])]
    cams["grandstand"]["at"] = mz(cams["grandstand"]["at"])
    cams["headon"]["at"] = mz(cams["headon"]["at"])
    cams["sideon"]["at"], cams["sideon"]["look"] = mz(cams["sideon"]["at"]), mz(cams["sideon"]["look"])
    cams["sideon"]["fov"] = [46, 46]
    cams["track_straight"]["raise"] = []
    # the racecard view: over the infield by the post, looking across at the stand side and up the straight
    prelude = {"label": "The runners", "seconds": 9, "eye": [[-60, 18, 30], [-45, 17, 28]],
               "at": [[150, 6, -60], [165, 6, -62]], "fov": 46, "list": [7, 0.6], "cardAfter": 3.5}
    postlude = NM.overview_after(prelude)
    # ---- the TV coverage (owner, 18 Nov 12:11: "review the race footage I sent and ... match the camera angles"): his
    # Racing TV Derby, frame by frame (reference/epsom/video-cameras.md): the start from inside the rail looking back across
    # the stalls with the woods behind; up the hill, low cameras just inside the inside rail, long lenses, the field coming
    # at them and passing, the far rail's boards and the woods behind; down to Tattenham Corner, raised head-on cameras on
    # the outside of the bend looking back up it, cut with high side-on ones looking across at the crowd behind the inside
    # rail; up the straight, a high camera on the stand side up the course looking back at the field, the Hill's crowd
    # behind the far rail; the finish from the stand, across at the Hill. Each a fixed camera that pans and zooms with the
    # field; the director cuts between them by metres to go (raceDirector.shots).
    RR = C["routes"]["round"]
    rtan, rright, _, _ = route_bits(RR, W)
    def on_route(d, off, h):
        f = (d - RR["d0"]) / RR["spacing"]; i = max(0, min(len(RR["insideRail"]) - 2, int(f))); k = f - i
        (ax, az), (bx, bz) = RR["insideRail"][i], RR["insideRail"][i + 1]
        x, z = ax + (bx - ax) * k, az + (bz - az) * k
        rx, rz = rright[i]
        return [r2(x + rx * off), r2(h), r2(z + rz * off)]
    def fixed(label, d, off, h, fov, note, frame="field"):
        return {"label": label, "kind": "fixed", "at": on_route(d, off, h), "fov": fov, "frame": frame, "leadRoom": 2, "atD": d, "note": note}
    RAIL = "low just inside the inside rail, a long lens: the field coming at it up the hill and passing, the far rail's boards and the woods behind"
    HEAD = "raised on the outside of the bend, looking back up it: the field coming down at it along the inside rail"
    SIDE = "high on the outside, abreast: across the field at the crowd and the road behind the inside rail"
    TV = {
        "rail_1": fixed("Hill 1", 2200, -4.0, 2.2, [2, 30], RAIL), "rail_2": fixed("Hill 2", 1950, -4.0, 2.2, [2, 30], RAIL),
        "rail_3": fixed("Hill 3", 1720, -4.0, 2.2, [2, 30], RAIL),
        "top": fixed("Top of the hill", 1560, -5.0, 3.0, [2, 34], "low inside the rail at the top of the hill: the field across the track, the long view behind"),
        "headon_1": fixed("Down the hill", 1250, W + 5.0, 9.0, [1.5, 26], HEAD), "side_1": fixed("Down the hill, side", 1260, W + 28.0, 13.0, [3, 34], SIDE),
        "headon_2": fixed("Bend", 1000, W + 6.0, 10.0, [1.5, 26], HEAD), "side_2": fixed("Bend, side", 1010, W + 30.0, 14.0, [3, 34], SIDE),
        "headon_3": fixed("Tattenham Corner", 790, W + 20.0, 22.0, [1.5, 26], HEAD + " (Tattenham Corner: high and well out, so it sees the field over the crowd inside the corner)"),
        "side_3": fixed("Tattenham, side", 760, W + 28.0, 14.0, [3, 34], SIDE + " (Tattenham Corner's crowd)"),
        "straight_high": {"label": "Straight", "kind": "fixed", "at": [175.0, 26.0, -50.0], "fov": [1.5, 30], "frame": "field", "leadRoom": 3,
                          "note": "high on the stand side up the course (the Rowley stand's roof), looking back up the straight: the field "
                                  "coming at it, the far rail and the Hill's crowd behind"},
    }
    cams.update(TV)
    cams["start"]["inside"] = True
    cams["start"]["side"] = 3.0
    cams["start"]["note"] = "inside the inside rail in front of the stalls, looking back across their faces: the woods behind (the video's start)"
    shots = [[2380, 2215, "rail_1"], [2215, 1965, "rail_2"], [1965, 1735, "rail_3"], [1735, 1575, "top"], [1575, 1320, "headon_1"],
             [1320, 1200, "side_1"], [1200, 1060, "headon_2"], [1060, 960, "side_2"], [960, 830, "headon_3"], [830, 690, "side_3"],
             [690, 2 * F + 20, "straight_high"], [2 * F + 20, -1, "grandstand"]]
    shots_straight = [[1100, 690, "track_straight"], [690, 2 * F + 20, "straight_high"], [2 * F + 20, -1, "grandstand"]]
    director = {"tracking": True, "grandstand": 2 * F}
    menu = {"straight": [["track_straight", "Tracking"], ["straight_high", "Straight"], ["grandstand", "Stand"], ["headon", "Head-on"]],
            "round": [["track_loop", "Tracking"], ["straight_high", "Straight"], ["grandstand", "Stand"]]}

    class L:                                                       # what NM.view_file reads of a layout
        TRACK_W = W; RUN_ON = C["runOut"]; STRAIGHT = C["routes"]["straight"]["length"]
    view = NM.view_file("epsom", L, {"name": "Epsom"}, stalls, -1, cams, prelude, postlude, director, menu)
    view["homeStraight"]["centreZ"] = -W / 2
    view["lanesStraight"]["x"][0] = 0.0
    view["treeDetail"]["centre"] = [150, -W / 2]
    view["_about"] = ("The race view's cameras and dressing for Epsom. Written by tools/course/epsom/to_race_view.py; don't edit by hand. "
                      "World axes as epsom.json (left-handed: the stands on -z).")
    view["races"]["_default"] = "1m4f10y"
    view["raceDirector"]["shots"] = shots
    view["raceDirector"]["shotsStraight"] = shots_straight
    view["raceDirector"]["shotsNote"] = ("Epsom (owner, 18 Nov, from his Racing TV Derby): [from, to, camera] by the leader's metres to go; the "
                                         "start camera first (startSequence), the rest as listed; outside every shot, the path's rules")
    for k in stalls["starts"]:
        view["races"][k]["label"] = LABEL.get(k, k)
    # the dock's course map as the racing papers draw Epsom: the straight along the bottom running left to right to the
    # post, the stands below, the Derby course's top arm above
    view["mapTurn"] = 180
    view["ground"]["farY"] = ground["farY"]
    NM.write("epsom-view.json", view, 1)

    # ---- scenery: the finish-line kit on the inside rail at the post, the poles, and the surroundings (phase 3:
    # tools/course/epsom/perimeter.py); the stands come in phase 4
    import random
    S = NM.Scene(17, ground)
    rnd = random.Random(17)
    spots = json.loads((REPO / "assets/models/architecture/site_props_spots.json").read_text())["pieces"]

    def sp(piece, x, z, turn=180.0, people=0.85, sxf=1.0, sc=1.0):
        """a site prop (marquee, kiosk, flag...), kept clear of the crowd, with its own people on its seats and steps"""
        S.piece("site_props", piece, x, z, turn, sxf, sc)
        w, dd = NM.SP_SIZE[piece]
        ca_, sa_ = math.cos(math.radians(turn)), math.sin(math.radians(turn))
        hw, hd = w / 2 * sxf * sc + 0.5, dd / 2 * sc + 0.5
        S.nogo.append([(x + u * ca_ + v * sa_, z - u * sa_ + v * ca_) for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))])
        for kind in ("seats", "stand"):
            for lx, ly, lz in spots.get(piece, {}).get(kind, []):
                if rnd.random() < people:
                    lx, ly, lz = lx * sxf * sc, ly * sc, lz * sc            # (the piece's own scale)
                    S.person(x + lx * ca_ - ly * sa_, lz, z - (lx * sa_ + ly * ca_), NM.face(math.sin(math.radians(turn)), math.cos(math.radians(turn))))
    _ps = importlib.util.spec_from_file_location("epsom_perimeter", HERE / "perimeter.py")
    PM = importlib.util.module_from_spec(_ps); _ps.loader.exec_module(PM)
    grid_box = (ground["x0"], ground["z0"], ground["x0"] + ground["cell"] * (ground["nx"] - 1), ground["z0"] + ground["cell"] * (ground["nz"] - 1))
    def put(model, piece, x, z, turn):
        S.piece(model, piece, x, z, turn)
    trees, boards, canopies, pnote = PM.perimeter(S, course, turf, grid_box, sp, rnd, put)
    scen = NM.scenery_file(S, trees, boards, [], ["epsom_stands", "site_props", "finish_line"], {"at": [0, GAP], "turn": 180}, poles)
    scen["canopies"] = canopies
    scen["_about"] += (" canopies: the woods beyond the belts of trees, each a light mesh (v: x, y above the ground, z; i: triangles), "
                       "drawn as a soft roof of leaves.")
    NM.write("epsom-scenery.json", scen)
    print("   perimeter:", json.dumps(pnote))
    print("  ", len(S.pieces), "pieces,", len(S.people) // 4, "people,", len(trees), "trees,", len(boards), "boards,", len(canopies), "canopies")
    hs = np.array(ground["h"])
    print("turf area %.0f m2, %d rail lines, %d starts; ground %d x %d, %.1f to %.1f m against the post" %
          (turf.area, len(rails), len(starts), ground["nx"], ground["nz"], hs.min(), hs.max()))


if __name__ == "__main__":
    main()
