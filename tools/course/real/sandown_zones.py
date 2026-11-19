"""Sandown's festival zones between the run-in and the sprint course, worked out from the race view's rails and written
into tools/course/real/sandown.json (perimeter.festivals 0 and 1). Run after to_race_view.py has written
race-view/assets/course/sandown.json, then run to_race_view.py again.

Owner, 19 Nov 13:28: "build a full festival between the home straight and the sprint course that contextualised the far
side of the round course and the near side of the sprint course". The ground between the two (the go-karts in real life)
is split down its middle: the half along the run-in faces the stands (the infield kit: marquees, big tops, balloon pods
in rows along the rail, a crowd on the rail); the half along the sprint course faces the sprint (little covered stands,
terrace decks, marquees, kiosks, a crowd along its rail).

    python3 tools/course/real/sandown_zones.py
"""
import json, math
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Polygon, Point

REPO = Path(__file__).resolve().parents[3]
C = json.loads((REPO / "race-view/assets/course/sandown.json").read_text())
W = C["trackWidth"]


def rail(rn, d_from, d_to, off):
    r = C["routes"][rn]["pathRail"]; P = r["points"]; out = []
    for d in np.arange(d_from, d_to, 5.0):
        i = int((d - r["d0"]) / r["spacing"]); i = max(1, min(len(P) - 2, i))
        a, b = P[i - 1], P[i + 1]; tx, tz = a[0] - b[0], a[1] - b[1]; l = math.hypot(tx, tz); tx, tz = tx / l, tz / l
        ax, az = tz, -tx                          # right-handed: across the track (the horses' left)
        out.append((P[i][0] + ax * off, P[i][1] + az * off))
    return out


# the run-in's inside rail (from past the post round to the far bend) and the sprint course's near (outer) rail
R = rail("round", -100.0, 1000.0, 0.0)
S = rail("straight", -90.0, 1040.0, W)
hole = Polygon(C["track"]["surface"][1])
# the ground between them: the infield, on the run-in's side of the sprint course (closed off past each end)
Sx = LineString(S)
west = (S[0][0] - 400.0, S[0][1] + 60.0)
between = Polygon(R + [(R[-1][0] + 200.0, R[-1][1] - 200.0)] + S[::-1] + [west, (R[0][0] - 400.0, R[0][1] + 20.0)]).buffer(0).intersection(hole)
if between.geom_type != "Polygon": between = max(between.geoms, key=lambda g: g.area)
# its middle: halfway from each point on the sprint's rail to the nearest point on the run-in's
Rl = LineString(R)
mid = []
for x, z in S[::4]:
    q = Rl.interpolate(Rl.project(Point(x, z)))
    mid.append(((x + q.x) / 2, (z + q.y) / 2))
mid = [(mid[0][0] - 400.0, mid[0][1])] + mid + [(mid[-1][0] + 300.0, mid[-1][1] - 120.0)]
far = [(p[0], p[1] - 600.0) for p in mid[::-1]]
sprint_half = Polygon(mid + far).buffer(0).intersection(between)
run_half = between.difference(sprint_half)
pick = lambda g: max(getattr(g, "geoms", [g]), key=lambda q: q.area)
run_half, sprint_half = pick(run_half), pick(sprint_half)
rp = lambda g: [[round(x, 1), round(z, 1)] for x, z in g.simplify(2.0).exterior.coords[:-1]]

CF = REPO / "tools/course/real/sandown.json"
cf = json.loads(CF.read_text())
fz = cf["perimeter"]["festivals"]
fz[0] = {"name": "the run-in infield: the half along the run-in, facing the stands", "kit": "infield",
         "poly": rp(run_half.buffer(2.0)), "offTurf": 8.0, "dens": 0.05, "kitScale": 1.35,
         "railCrowd": {"from": 1.5, "to": 8.0, "dens": 0.7},
         "balloonRows": {"n": 5, "gap": 10, "every": 110, "in": 7, "start": 40, "end": 60},
         "generated": "tools/course/real/sandown_zones.py"}
side = {"name": "the run-in infield: the half along the sprint course, facing it", "kit": "standside",
        "poly": rp(sprint_half.buffer(2.0)), "offTurf": 8.0, "dens": 0.05, "kitScale": 1.35,
        "railCrowd": {"from": 1.5, "to": 8.0, "dens": 0.7}, "generated": "tools/course/real/sandown_zones.py"}
if len(fz) > 2 and fz[2].get("generated"): fz[2] = side
else: fz.insert(2, side)
CF.write_text(json.dumps(cf, indent=1))
print("between %.0f m2: along the run-in %.0f m2, along the sprint %.0f m2" % (between.area, run_half.area, sprint_half.area))
