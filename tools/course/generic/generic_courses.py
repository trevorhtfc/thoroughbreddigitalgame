"""The generic courses: the stop gap that lets any course be raced until it has its own build (owner, 19 Nov 2026).

Five families from the course sheet's "Generic courses" tab (the Park, the Tight Track, the Ring, the Hill Track, the
Downs), each built both ways round (left- and right-handed) and with a bigger and a smaller stand side (owner,
17:39: 'two grandstand clusters for each course type? a bigger (haydock, newcastle etc) and a smaller (pontefract,
beverley)'), so twenty courses. Each is drawn from a few numbers
(specs.py: corners and radii of the loop, the chutes, the starts) and then goes through the same tools as the tier 2
courses (tools/course/real/: layout.py, merge_stands.py, to_race_view.py, calibrate.mjs), so it gets the same
stalls on level pads, cameras, boards, planting, stands and festival as the real courses.

This script writes, for each course id (gen-park-l-big, gen-park-l-small, gen-park-r-big, ...):
  tools/course/real/<id>.json          the course file (routes as hand-drawn rails, the starts, the dressing)
  reference/<id>/osm-<id>.json         a stand-in for OpenStreetMap's turf (the outline of the generic track)
  reference/<id>/dem-course-20m.json   the ground: flat, or the family's slopes (an uphill finish, the downs)

  python3 tools/course/generic/generic_courses.py [ids...]          (no ids: all ten)
"""
import json, math, re, sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
from geometry import Loop
from specs import FAMILIES, F
import dressing

LAT0, LON0 = 52.4, -1.6                     # a made-up anchor (the files want latitude and longitude)
KX, KY = 111320.0 * math.cos(math.radians(LAT0)), 110574.0
W = 26.0
RUN_OUT = 90.0
ROOM = 30.0                                 # straight track behind the furthest start in a chute


def trip_m(t):
    m = re.fullmatch(r"(?:(\d+)m)?(?:(\d+)f)?(?:(\d+)y)?", t)
    mi, fu, yd = (int(x) if x else 0 for x in m.groups())
    return mi * 8 * F + fu * F + yd * 0.9144


def build(fid, hand, size):
    S = FAMILIES[fid]
    cid = f"gen-{fid}-{'l' if hand < 0 else 'r'}-{size}"
    L = Loop(S["corners"], S["radii"], post_gap=S["post_gap"])
    # (u, v) -> east, north: left-handed the infield lies to the south of a home straight run westwards
    sv = -1.0 if hand < 0 else 1.0
    en = lambda p: [round(float(p[0]), 2), round(float(sv * p[1]), 2)]
    starts = {}
    for key, r in S["starts"].items():
        rn, t = (r if isinstance(r, list) else [r, key])
        starts[key] = {"route": rn, "trip": t, "d": trip_m(t)}
    routes, rails_uv = {}, {}
    for rn, R in S["routes"].items():
        far = max(s["d"] for s in starts.values() if s["route"] == rn)
        if "chute" in R:
            b = L.back_of(R["chute"]) + R.get("laps", 0) * L.L
            clen = far - b + ROOM
            if clen < ROOM: raise SystemExit(f"{cid} {rn}: the furthest start ({far:.0f} m) isn't in the chute")
            pts = L.route(0, RUN_OUT, chute=R["chute"], chute_len=clen, laps=R.get("laps", 0))
        else:
            pts = L.route(far + ROOM, RUN_OUT)
        rails_uv[rn] = pts
        routes[rn] = {"note": R["note"], "pieces": [{"points": [en(p) for p in pts[::2]]}], "ease": 16}
    # the turf (each route's strip from its inside rail out across the track) -> the outline the layout tool reads
    strips = []
    for pts in rails_uv.values():
        t = np.gradient(pts, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
        # in (u, v) the infield (+v) is on the horses' right going -u, so away from it is their left: (-t_v, t_u)
        out = np.stack([-t[:, 1], t[:, 0]], 1)
        poly = Polygon(np.vstack([pts, (pts + out * W)[::-1]])).buffer(0)
        strips.append(poly)
    turf = unary_union(strips).buffer(1.0).buffer(-0.5)
    turf = max(getattr(turf, "geoms", [turf]), key=lambda g: g.area)
    holes = sorted([Polygon(h) for h in turf.interiors], key=lambda g: -g.area)
    to_ll = lambda e, n: [round(LAT0 + n / KY, 7), round(LON0 + e / KX, 7)]
    ring = lambda coords: {"role": "outer", "way": 0, "p": [to_ll(*en(c)) for c in coords]}
    osm = {"_about": f"Not OpenStreetMap: the outline of {S['name']}'s generic track (tools/course/generic/generic_courses.py), "
                     "in the same form, so the shared layout tool reads it.",
           "relation": 0, "rings": [ring(turf.exterior.coords)] + [dict(ring(h.exterior.coords), role="inner") for h in holes[:1]],
           "extra": [], "stands": []}
    ref = REPO / f"reference/{cid}"; ref.mkdir(parents=True, exist_ok=True)
    (ref / f"osm-{cid}.json").write_text(json.dumps(osm, separators=(",", ":")))
    # the ground
    allp = np.vstack(list(rails_uv.values()))
    e0, e1 = allp[:, 0].min() - 800, allp[:, 0].max() + 800
    n_ = np.array([en(p)[1] for p in allp]); n0, n1 = n_.min() - 800, n_.max() + 800
    step = 20
    x0, y0 = math.floor(e0 / step) * step, math.floor(n0 / step) * step
    nx, ny = int((e1 - x0) / step) + 2, int((n1 - y0) / step) + 2
    gx, gy = np.meshgrid(x0 + step * np.arange(nx), y0 + step * np.arange(ny))
    H = np.zeros_like(gx, float)
    if S.get("ground"):
        from scipy.interpolate import RBFInterpolator
        cp = np.array(S["ground"], float)
        rb = RBFInterpolator(cp[:, :2], cp[:, 2], kernel="thin_plate_spline", smoothing=2.0)
        uv = np.stack([gx.ravel(), (gy * sv).ravel()], 1)
        H = rb(uv).reshape(gx.shape)
        H = np.clip(H, -14, 18)
    dem = {"_about": f"The ground of {S['name']}'s generic track: made up (tools/course/generic/specs.py 'ground'), metres + 60 "
                     "in decimetres; same form as the real courses' AWS Terrain Tiles grids.",
           "lat0": LAT0, "lon0": LON0, "step": step, "x0": int(x0), "y0": int(y0), "nx": nx, "ny": ny,
           "h_dm": [[int(round((60 + v) * 10)) for v in row] for row in H]}
    (ref / "dem-course-20m.json").write_text(json.dumps(dem, separators=(",", ":")))
    # the course file
    hand_w = "left-handed" if hand < 0 else "right-handed"
    post_route = "straight" if "straight" in routes else "round"
    C = {
        "_about": f"{S['name']} ({hand_w}), a generic course: written by tools/course/generic/generic_courses.py from specs.py "
                  "and dressing.py. Don't edit by hand.",
        "name": (f"{S['name']} ({hand_w}, {'bigger' if size == 'big' else 'smaller'} stands)" if size != "us"
                 else "The American Ring (turf course inside a dirt track)"), "family": fid, "size": size, "generic": True,
        "date": "19 Nov 2026", "hand": hand, "trackWidth": W, "runOut": RUN_OUT, "ease": 16,
        "post": {"route": post_route, "x": round(L.post_u, 2), "searchLast": 400,
                 "note": "on the home straight, %d m before the post-end bend" % S["post_gap"]},
        "routesNote": "; ".join(f"{rn}: {R['note']}" for rn, R in S["routes"].items()),
        "routes": routes,
        "starts": {k: dict({"route": s["route"], "expected": S["routes"][s["route"]]["note"]},
                           **({"trip": s["trip"]} if s["trip"] != k else {})) for k, s in starts.items()},
        "numberEvery": 40,
        "facts": {"circuit m": round(L.L), "circuit f": round(L.L / F, 1), "run-in m": round(L.back_of(len(S["corners"]) - 1)),
                  "run-in f": round(L.back_of(len(S["corners"]) - 1) / F, 2), "kind": S["kind"], "standsIn": S["standsIn"]},
    }
    if size == "us":
        # the American Ring (owner, 20 Nov 09:11: "a course with a dirt ring around the outside", with his maps of
        # Churchill Downs and Santa Anita): the turf course inside a dirt oval, as theirs. The dirt runs from the turf's
        # outer rail 24 m out round the loop; the chutes cross it (turf over the dirt, as at Santa Anita); its own outer
        # rail, broken where the chutes cross. World axes: x = u - post, z = v * (infield side).
        from shapely.geometry import Polygon as _P, LineString as _LS
        zi = 1.0 if hand < 0 else -1.0
        loop = _P(L.P)
        all_turf = unary_union(strips).buffer(0.6)
        band = loop.buffer(W + 24.6, join_style=1).difference(loop.buffer(W + 0.6, join_style=1)).difference(all_turf)
        wpt = lambda q: [round(float(q[0] - L.post_u), 2), round(float(q[1] * zi), 2)]
        flats = []
        x0b, _, x1b, _ = band.bounds
        for xa in np.arange(x0b - 1, x1b + 1, 40.0):
            from shapely.geometry import box as _box
            cut = band.intersection(_box(xa, -2000, xa + 40.0, 2000))
            for g in getattr(cut, "geoms", [cut]):
                if g.geom_type == "Polygon" and g.area > 1 and not g.interiors:
                    flats.append({"colour": "#c79c72", "poly": [wpt(q) for q in g.simplify(0.3).exterior.coords[:-1]], "y": 0.05})
        rail = _LS(list(loop.buffer(W + 24.6, join_style=1).exterior.coords)).difference(all_turf.buffer(1.0))
        C["extraRails"] = [[wpt(q) for q in g.coords] for g in getattr(rail, "geoms", [rail]) if g.length > 20]
        C["dirt"] = {"width": 24.0, "flats": flats}
    C.update(dressing.dress(cid, fid, hand, size, S, L, C))
    (REPO / f"tools/course/real/{cid}.json").write_text(json.dumps(C, indent=1))
    print(f"{cid}: circuit {L.L:.0f} m, run-in {C['facts']['run-in m']} m, {len(starts)} starts, routes {list(routes)}")
    return cid


if __name__ == "__main__":
    want = sys.argv[1:]
    for fid in FAMILIES:
        for hand in (-1, 1):
            for size in ("big", "small", "us"):
                if size == "us" and not (fid == "ring" and hand < 0): continue      # the American Ring: left-handed only
                cid = f"gen-{fid}-{'l' if hand < 0 else 'r'}-{size}"
                if not want or cid in want: build(fid, hand, size)
