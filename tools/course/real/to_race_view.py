"""Tier 2 courses for the 3D race view (race-view/final-furlong.html?course=<id>), phases 2 and 3 at their basic level:
the track on its real ground, the stalls, the cameras, and the basic rules for boards and planting (perimeter.py).

    python3 tools/course/real/layout.py <id>          (the plan: courses/<id>-draft.json)
    python3 tools/course/real/to_race_view.py <id>    (this: the race view's files)
    node tools/course/real/calibrate.mjs <id>         (the par times), then this again

Epsom's to_race_view.py made general (it reads the course's own settings from tools/course/real/<id>.json, "view").
Writes race-view/assets/course/<id>.json, -view, -stalls, -standards, -scenery, as York, Goodwood and Epsom.

Cameras (the basic set, York's): the start camera; the tracking car 12 m beyond the outer rail round the course and 5 m
along the straight; the stand camera on the stand side by the post for the last 2 furlongs; the head-on long lens
beyond the line for straight races; the side-on replay. Each course's own TV cameras come with its race video.
"""
import json, math, re, sys, random, importlib.util
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.prepared import prep

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools/course/newmarket"))
import to_race_view as NM          # Newmarket's: the shared light, ground colours, cameras and view file
sys.path.insert(0, str(HERE))
import layout as LYM
import perimeter as PM

OUT = REPO / "race-view/assets/course"
F = 201.168
GAP = 0.4
STALL1, STALL_PITCH, STANDS_BEHIND = 1.625, 1.05, 1.55
MAX_RUNNERS = 22
GROUND_CELL = 20.0
MARGIN = 420.0
EDGE_EASE = 160.0
BEHIND = 40.0


def r2(v): return round(v, 2)
def race_id(t): return re.sub(r"\s*\((\w+)\)", r"-\1", t).strip()


def route_bits(route, W, hand):
    pts = route["insideRail"]; n = len(pts); tan = []
    for i in range(n):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dz = a[0] - b[0], a[1] - b[1]; l = math.hypot(dx, dz) or 1
        tan.append((dx / l, dz / l))
    # across the track from the inside rail: the horses' right on a left-handed course (-z on the home straight)
    across = [(-tz, tx) if hand < 0 else (tz, -tx) for tx, tz in tan]
    outer = [[p[0] + r[0] * W, p[1] + r[1] * W] for p, r in zip(pts, across)]
    mid = [[p[0] + r[0] * W / 2, p[1] + r[1] * W / 2] for p, r in zip(pts, across)]
    from shapely.geometry import LineString
    strip = LineString(mid).buffer(W / 2, cap_style=2)
    return tan, across, outer, strip


def ground_grid(LY, C, W, name):
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
            "note": "%s's real ground (AWS Terrain Tiles), metres against the post's (%.1f m above sea level), every 'cell' metres "
                    "from (x0, z0), row by row along x; eased over its outer %d m to farY, where the flat far ground lies." %
                    (name, LY.POST_GROUND, EDGE_EASE)}


def main(cid):
    LY = LYM.Course(cid)
    CF = LY.C; V = CF.get("view", {})
    C = json.loads((REPO / f"courses/{cid}-draft.json").read_text())
    W = C["trackWidth"]; hand = C["hand"]; name = CF["name"]
    C["starts"] = {race_id(t): dict(s, label=t) for t, s in C["starts"].items()}
    for rn, r in C["routes"].items():
        far = max([s["distance"] for s in C["starts"].values() if s["route"] == rn] + [r["d0"] + 200]) + BEHIND
        n = int((far - r["d0"]) / r["spacing"]) + 1
        r["insideRail"] = r["insideRail"][:n]
        r["heights"] = dict(r["heights"], h=r["heights"]["h"][:n])
        r["bends"] = [b for b in r["bends"] if b[1] < far]
        r["bends"] = [[min(b[0], far), b[1], b[2] if b[0] <= far else round(b[2] * (far - b[1]) / (b[0] - b[1]), 1)] for b in r["bends"]]
    routes_out, strips = {}, []
    for rn, r in C["routes"].items():
        tan, across, outer, strip = route_bits(r, W, hand)
        strips.append(strip)
        bends = [list(b) for b in r["bends"]]
        home = min([b[1] for b in bends if b[2] > 0], default=0.0)
        routes_out[rn] = {"pathRail": {"d0": r["d0"], "spacing": r["spacing"], "points": r["insideRail"]},
                          "path": {"bends": bends, "home": home,
                                   "note": "For the race engine: bends as [metres to go where it starts, where it ends, degrees turned "
                                           "(+ towards the rail; - away from it)]; 'home' = where the home straight starts."},
                          "heights": r["heights"]}
    turf = unary_union(strips).buffer(0.01).buffer(-0.01).simplify(0.15)
    parts = [turf] if turf.geom_type == "Polygon" else sorted(turf.geoms, key=lambda g: -g.area)
    turf = parts[0]
    surface = [[[r2(x), r2(z)] for x, z in turf.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in turf.interiors]
    railed = turf.buffer(GAP, join_style=2, mitre_limit=2.0).simplify(0.1)
    rails = [[[r2(x), r2(z)] for x, z in railed.exterior.coords]] + [[[r2(x), r2(z)] for x, z in h.coords] for h in railed.interiors]
    for ln in CF.get("extraRails", []):      # (the American Ring: the dirt track's outer rail)
        rails.append([[r2(x), r2(z)] for x, z in ln])
    sz = -1 if hand < 0 else 1                              # the stand side's z sign
    poles = [{"furlongs": k, "at": [r2(k * F), r2(sz * (W + GAP + 0.7))], "turn": 0} for k in range(1, 5)]
    if V.get("polesOnRoute"):            # a run-in that bends within 4f (Sandown): the poles on the route's outer rail
        RR = C["routes"][V["polesOnRoute"]]; _, acr, _, _ = route_bits(RR, W, hand); poles = []
        for k in range(1, 5):
            f = (k * F - RR["d0"]) / RR["spacing"]; i = int(f); kk = f - i
            (ax_, az_), (bx_, bz_) = RR["insideRail"][i], RR["insideRail"][i + 1]
            px, pz = ax_ + (bx_ - ax_) * kk, az_ + (bz_ - az_) * kk
            tx, tz = ax_ - bx_, az_ - bz_; l = math.hypot(tx, tz) or 1; tx, tz = tx / l, tz / l
            o = W + GAP + 0.7
            poles.append({"furlongs": k, "at": [r2(px + acr[i][0] * o), r2(pz + acr[i][1] * o)],
                          "turn": round(math.degrees(math.atan2(tz, -tx)), 1)})
    ground = ground_grid(LY, C, W, name)
    default_route = V.get("defaultRoute", "round")
    # a course with no straight course (Chester): the 'straight' cameras and the furlong poles use the home straight
    STRAIGHT_LEN = C["routes"]["straight"]["length"] if "straight" in C["routes"] else max(routes_out[default_route]["path"]["home"], 2 * F)
    course = {
        "id": cid, "name": name, "status": "draft",
        "_about": "Written by tools/course/real/to_race_view.py from courses/%s-draft.json; don't edit by hand. World axes as "
                  "York's: x along the home straight (the horses run towards -x), y up, the winning post on the inside rail is the "
                  "origin. Several routes (each race takes its start's route), each with its own ground heights for the race "
                  "engine; the turf is laid on the ground grid." % cid,
        "axes": C["axes"], "direction": C["direction"], "hand": hand,
        "trackWidth": W, "furlong": F,
        "routes": routes_out, "defaultRoute": default_route,
        "path": routes_out[default_route]["path"], "pathRail": routes_out[default_route]["pathRail"],
        "track": {"surface": surface},
        "rails": {"gap": GAP, "lines": rails, "skip": [[-16.3, 16.7, GAP]]},
        "straightMile": {"length": round(STRAIGHT_LEN, 1), "furlongPoles": poles},
        "winningPost": [0, 0],
        "extraPosts": [{"route": rn, "at": routes_out[rn]["pathRail"]["points"][int(-routes_out[rn]["pathRail"]["d0"] / routes_out[rn]["pathRail"]["spacing"])],
                        "across": [r2(v) for v in route_bits(C["routes"][rn], W, hand)[1][int(-routes_out[rn]["pathRail"]["d0"] / routes_out[rn]["pathRail"]["spacing"])]]}
                       for rn in CF["routes"] if CF["routes"][rn].get("post")],
        "ground": ground,
        "drapeTurf": True,
    }

    # ---- stalls: each start's stalls across the track from its inside rail, stall 1 on the inside
    asc = json.loads((OUT / "ascot-stalls.json").read_text())
    starts = {}
    pre = cid[0]
    keys = {t: pre + re.sub(r"[^0-9a-z]", "", t) for t in C["starts"]}
    for t, s in C["starts"].items():
        r = C["routes"][s["route"]]
        pts, sp, d0 = r["insideRail"], r["spacing"], r["d0"]
        f = (s["distance"] - d0) / sp; i = max(1, min(len(pts) - 2, int(f))); k = f - i
        a, b = pts[i], pts[i + 1]
        x, z = a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k
        p0, p1 = pts[i - 1], pts[i + 1]
        tx, tz = p0[0] - p1[0], p0[1] - p1[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        nx, nz = (-tz, tx) if hand < 0 else (tz, -tx)
        straight = s["route"] == "straight"
        starts[t] = {
            "label": s["label"],
            "course": "straight" if straight else "round",
            "route": s["route"], "key": keys[t], "distance": s["distance"], "insideRailAt": [r2(x), r2(z)],
            "runningDirection": [round(tx, 4), round(tz, 4)], "towardsOuterRail": [round(nx, 4), round(nz, 4)],
            "stall1": "inside rail", "onStraight": straight, "comesBack": bool(V.get("stallsAway", False)),
            "stalls": [{"draw": j + 1, "fromInsideRail": round(STALL1 + STALL_PITCH * j, 3), "across": round(STALL1 + STALL_PITCH * j - W / 2, 3),
                        "at": [r2(x + nx * (STALL1 + STALL_PITCH * j)), r2(z + nz * (STALL1 + STALL_PITCH * j))]} for j in range(MAX_RUNNERS)],
        }
    stalls = {"_about": "%s's starting stalls, DRAFT (tools/course/real/to_race_view.py), with Ascot's stall kit and gates. Distances "
                        "from the gate line along the route's inside rail; stall 1 on the inside rail." % name,
              "horseStandsBehind": STANDS_BEHIND, "gates": asc["gates"], "kit": asc["kit"], "maxRunners": MAX_RUNNERS,
              "unitsForField": {k: v for k, v in asc["unitsForField"].items() if int(k) <= MAX_RUNNERS}, "starts": starts}
    NM.write(f"{cid}-stalls.json", stalls, 1)
    pad = NM.level_stall_pads(ground, starts, W)          # a level pad under every start's stalls (the rule for every course)
    print("   stall pads: the ground moved by up to %.2f m" % pad)
    NM.write(f"{cid}.json", course)

    # ---- standards: rough winning times (a good horse, good ground) until the calibration sets the pars
    nm = json.loads((OUT / "newmarket-july-standards.json").read_text())
    par_file = HERE / f"{cid}-par.json"
    par = json.loads(par_file.read_text())["par"] if par_file.exists() else {}
    def target(s):
        d = s["distance"]; tgt = V.get("targets", {}).get(s["label"])
        if tgt: return tgt
        # a galloping course's typical good-ground winning times: about 12.0 s a furlong over 5f, 12.4 at a mile, 12.9
        # at a mile and a half, 13.3 at two miles (to check against real results)
        fpf = np.interp(d / F, [5, 8, 12, 16, 18], [11.95, 12.35, 12.85, 13.3, 13.5])
        return round(fpf * d / F, 1)
    standards = {"_about": "Par (standard) times at %s, DRAFT. 'winningTime' is a rough winning time for a good horse on good ground "
                           "(a galloping course's typical times: to check against real results); 'seconds' is the par the engine "
                           "uses, set by tools/course/real/calibrate.mjs so its winning times come out at those." % name,
                 "parTimes": [{"key": keys[t], "course": "straight" if s["route"] == "straight" else "round", "distance": s["distance"],
                               "seconds": par.get(keys[t], round(target(s) * 0.978, 2)), "winningTime": target(s)} for t, s in C["starts"].items()],
                 "going": nm["going"], "pace": nm["pace"]}
    NM.write(f"{cid}-standards.json", standards, 1)

    # ---- the view: as York's and Epsom's (left-handed: the stands on -z, the fixed cameras mirrored)
    sw = LY.world_dir(-(np.array([1.0, 0.0]) * 0.55 + np.array([0.0, 1.0]) * 0.84))   # the sun west-south-west, mid-afternoon
    l = math.hypot(*sw)
    sun = [r2(sw[0] / l * 105), 49.5, r2(sw[1] / l * 105)]
    cams = NM.cameras(W, +1, [0, 16, W + 15], ([-8, 6.5, 0.8], [0, 6.0, W * 0.65]), -70.0, sun)
    if hand < 0:
        mz = lambda p: [p[0], p[1], r2(-p[2])]
        cams["grandstand"]["at"] = mz(cams["grandstand"]["at"])
        cams["headon"]["at"] = mz(cams["headon"]["at"])
        cams["sideon"]["at"], cams["sideon"]["look"] = mz(cams["sideon"]["at"]), mz(cams["sideon"]["look"])
    cams["sideon"]["fov"] = [46, 46]
    cams["track_straight"]["raise"] = []
    zs = -1 if hand < 0 else 1
    prelude = {"label": "The runners", "seconds": 9, "eye": [[-60, 18, -zs * 30], [-45, 17, -zs * 28]],
               "at": [[150, 6, zs * 60], [165, 6, zs * 62]], "fov": 46, "list": [7, 0.6], "cardAfter": 3.5}
    if V.get("prelude"):                     # a course's own racecard / overview shot (Chester: down the straight from the castle end)
        prelude.update({k: v for k, v in V["prelude"].items() if k != "note"})
    postlude = NM.overview_after(prelude)
    director = {"tracking": True, "grandstand": 2 * F}
    menu = {"straight": [["track_straight", "Tracking"], ["grandstand", "Stand"], ["headon", "Head-on"], ["drone_straight", "Drone"]],
            "round": [["track_loop", "Tracking"], ["grandstand", "Stand"], ["drone_straight", "Drone"]]}

    # ---- the course's own TV coverage (tools/course/real/<id>.json "view.tv", from its race video): fixed cameras placed
    # by route, metres to go and metres across from the inside rail (+ across the track and beyond the outer rail, - into
    # the infield), copies of the tracking cars with changes (e.g. the car in the infield), and the director's shots
    TVC = V.get("tv", {})
    def on_route(rn, d, off, h):
        RR = C["routes"][rn]; _, acr, _, _ = route_bits(RR, W, hand)
        f = (d - RR["d0"]) / RR["spacing"]; i = max(0, min(len(RR["insideRail"]) - 2, int(f))); k = f - i
        (ax, az), (bx, bz) = RR["insideRail"][i], RR["insideRail"][i + 1]
        return [r2(ax + (bx - ax) * k + acr[i][0] * off), r2(h), r2(az + (bz - az) * k + acr[i][1] * off)]
    for cn, cs in TVC.get("cams", {}).items():
        if "copy" in cs:
            cams[cn] = dict(cams[cs["copy"]], **{k: v for k, v in cs.items() if k != "copy"})
        else:
            cams[cn] = {"label": cs["label"], "kind": "fixed", "at": on_route(cs.get("route", default_route), cs["d"], cs["off"], cs["h"]),
                        "fov": cs["fov"], "frame": "field", "leadRoom": cs.get("leadRoom", 2), "atD": cs["d"], "note": cs.get("note", "")}
            for kk in ("frame", "window"):
                if kk in cs: cams[cn][kk] = cs[kk]
            if "look" in cs:                  # [d, off, h]: a fixed look point (the side-on replay)
                cams[cn]["look"] = on_route(cs.get("route", default_route), *cs["look"])
    for cn, cs in TVC.get("set", {}).items():     # changes to the standard cameras (Newbury 19 Nov: the stand camera onto
        cams[cn] = dict(cams[cn], **cs)             # the set-back stand)
    if TVC.get("startInside"):
        cams["start"]["inside"] = True; cams["start"]["side"] = 3.0

    class L:
        TRACK_W = W; RUN_ON = C["runOut"]; STRAIGHT = STRAIGHT_LEN
    view = NM.view_file(cid, L, {"name": name}, stalls, -1 if hand < 0 else 1, cams, prelude, postlude, director, menu)
    view["homeStraight"]["centreZ"] = zs * W / 2
    view["lanesStraight"]["x"][0] = 0.0
    view["treeDetail"]["centre"] = [150, zs * W / 2]
    view["_about"] = ("The race view's cameras and dressing for %s. Written by tools/course/real/to_race_view.py; don't edit by hand. "
                      "World axes as %s.json." % (name, cid))
    view["races"]["_default"] = V.get("defaultRace", next(iter(stalls["starts"])))
    for k in stalls["starts"]:
        view["races"][k]["label"] = C["starts"][k]["label"]
        sw_ = TVC.get("routeCams", {}).get(C["starts"][k]["route"])
        if sw_: view["races"][k]["cameraSwap"] = sw_
    view["mapTurn"] = V.get("mapTurn", 0)
    if TVC.get("shots"):
        view["raceDirector"]["shots"] = TVC["shots"]
        view["raceDirector"]["shotsNote"] = TVC.get("note", "") + " [from, to, camera] by the leader's metres to go; outside every shot, the path's rules"
    if TVC.get("shotsStraight"): view["raceDirector"]["shotsStraight"] = TVC["shotsStraight"]
    if TVC.get("menu"): view["cameraMenu"] = TVC["menu"]
    view["ground"]["farY"] = ground["farY"]
    NM.write(f"{cid}-view.json", view, 1)

    # ---- scenery: the finish-line kit, the poles, and the basic surroundings (perimeter.py)
    S = NM.Scene(17, ground)
    grid_box = (ground["x0"], ground["z0"], ground["x0"] + ground["cell"] * (ground["nx"] - 1), ground["z0"] + ground["cell"] * (ground["nz"] - 1))
    popts = dict(CF.get("perimeter", {}))
    models = ["site_props", "finish_line"]
    if CF.get("stands"):
        popts["stands"] = CF["stands"]; popts["standsModel"] = f"{cid}_stands"
        popts["standsInfo"] = json.loads((REPO / f"assets/models/architecture/{cid}_stands.json").read_text())["pieces"]
        models.append(f"{cid}_stands")
    trees, boards, plot, pnote = PM.perimeter(S, course, turf, grid_box, random.Random(23), popts)
    if CF.get("edges"):                     # a course's own edges script (Chester: the city walls and the city beyond)
        ed = importlib.import_module(CF["edges"]["script"])
        pnote["edges"] = ed.build(S, LY, course, turf, trees, boards, CF["edges"], NM, random.Random(29))
    ca_ = TVC.get("clearAround")                # festival pieces and people cleared round the TV's fixed cameras (Chester)
    if ca_:
        # each camera's foreground: a corridor from the camera to the stretch of track it watches (its 'atD' and the
        # 'ahead' metres beyond, along its route), plus a circle round it
        from shapely.geometry import LineString as _LS, Point as _Pt
        zones = []
        for k in ca_["cams"]:
            cs = TVC["cams"].get(k); cm = cams.get(k)
            if not cs or not cm or "at" not in cm: continue
            a = (cm["at"][0], cm["at"][2]); zones.append(_Pt(*a).buffer(ca_.get("radius", 35.0)))
            for dd in np.arange(cs["d"], cs["d"] + ca_.get("ahead", 350.0), 25.0):
                q = on_route(cs.get("route", default_route), dd, W / 2, 0.0)
                zones.append(_LS([a, (q[0], q[2])]).buffer(ca_.get("width", 12.0)))
        bzones = []                          # and the boards beyond the outer rail behind the field, for the cameras named in 'boards'
        for k in ca_.get("boards", []):
            cs = TVC["cams"].get(k); cm = cams.get(k)
            if not cs or not cm or "at" not in cm: continue
            a = (cm["at"][0], cm["at"][2])
            for dd in np.arange(cs["d"], cs["d"] + ca_.get("boardsAhead", 0.0), 10.0):
                q0 = on_route(cs.get("route", default_route), dd, W, 0.0); q1 = on_route(cs.get("route", default_route), dd, W + 40.0, 0.0)
                bzones.append(_LS([a, (q0[0], q0[2]), (q1[0], q1[2])]).convex_hull.buffer(3.0))
        bzone = prep(unary_union(bzones)) if bzones else None
        nb = len(boards); boards[:] = [b_ for b_ in boards if not (bzone is not None and bzone.contains(_Pt(b_[0], b_[1])))]
        pnote["boards cleared round the cameras"] = nb - len(boards)
        tzones = []                          # and the trees in front of the cameras that look out over a tree belt (Chester's viaduct)
        for k in ca_.get("trees", []):
            cs = TVC["cams"].get(k); cm = cams.get(k)
            if not cs or not cm or "at" not in cm: continue
            a = (cm["at"][0], cm["at"][2]); tzones.append(_Pt(*a).buffer(12.0))
            for dd in np.arange(cs["d"] - 60.0, cs["d"] + 61.0, 10.0):
                q = on_route(cs.get("route", default_route), dd, W, 0.0)
                tzones.append(_LS([a, (q[0], q[2])]).buffer(5.0))
        if tzones:
            tz = prep(unary_union(tzones)); nt = len(trees)
            trees[:] = [t_ for t_ in trees if not tz.contains(_Pt(t_[0], t_[1]))]
            pnote["trees cleared round the cameras"] = nt - len(trees)
        zone = prep(unary_union(zones)) if zones else None
        near = lambda x, z: zone is not None and zone.contains(_Pt(x, z))
        n0 = len(S.pieces); S.pieces[:] = [q for q in S.pieces if not (q[0] == "site_props" and near(q[2], q[3]))]
        P_, keep = S.people, []
        for i in range(0, len(P_), 4):
            if near(P_[i], P_[i + 2]) and P_[i + 1] < S.G(P_[i], P_[i + 2]) + 1.5: continue
            keep += P_[i:i + 4]
        gone = (len(P_) - len(keep)) // 4; S.people[:] = keep
        pnote["cleared round the cameras"] = [n0 - len(S.pieces), gone]
    for ep in course["extraPosts"]:          # the finish-line kit at a route's own post, as at the main post
        (ax_, az_), (cx_, cz_) = ep["at"], ep["across"]
        RR = C["routes"][ep["route"]]; i0 = int(-RR["d0"] / RR["spacing"])
        tx, tz = RR["insideRail"][i0][0] - RR["insideRail"][i0 + 1][0], RR["insideRail"][i0][1] - RR["insideRail"][i0 + 1][1]
        l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        S.pieces.append(["finish_line", "finish_line", r2(ax_ - cx_ * GAP), r2(az_ - cz_ * GAP),
                         round(math.degrees(math.atan2(tz, -tx)) + (180 if hand < 0 else 0), 1), 1, 1])
    scen = NM.scenery_file(S, trees, boards, getattr(S, "banks", []), models, {"at": [0, -zs * GAP], "turn": 180 if hand < 0 else 0}, poles)
    scen["_about"] += " Basic surroundings from tools/course/real/perimeter.py (the shared rules until the course's own mark-up)."
    NM.write(f"{cid}-scenery.json", scen)
    print("   perimeter:", json.dumps(pnote))
    hs = np.array(ground["h"])
    print("turf area %.0f m2, %d rail lines, %d starts; ground %d x %d, %.1f to %.1f m against the post" %
          (turf.area, len(rails), len(starts), ground["nx"], ground["nz"], hs.min(), hs.max()))


if __name__ == "__main__":
    main(sys.argv[1])
