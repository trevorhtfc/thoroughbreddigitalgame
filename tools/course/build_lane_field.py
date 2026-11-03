"""Soft lanes on the turf that follow the course round the bends: how far each point of the turf is from
its nearest edge, as an image the race view (and the ground bake) turns into gentle mown stripes.

    python3 tools/course/build_lane_field.py

Reads courses/ascot.json (track.surface: the turf's outline and the infield hole). Writes
race-view/assets/course/lanes.png (grey = metres from the turf's edge / maxDist, 0 off the turf) and the
settings to courses/ascot-view.json -> lanes (the race view's copy is updated too).

Why the edge works: the track is 30 m wide everywhere and the stripes repeat every two lanes (7.5 m), so
measuring from the nearer edge gives the same stripes as measuring from the inside rail (owner's rule:
lanes along the running line, never formal lines across it). Where the chute and the straight mile join,
the wider turf simply goes plain in the middle.
"""
import json, os
import numpy as np
import shapely
from shapely.geometry import Polygon
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
rp = lambda *p: os.path.join(REPO, *p)
COURSE = json.load(open(rp("courses/ascot.json")))
RES = 1.0                # metres per pixel; the distance is smooth, so the viewer's filtering does the rest
MAXD = 20.0              # distances stored up to this; beyond it the turf is plain

rings = COURSE["track"]["surface"]
turf = Polygon(rings[0], rings[1:])
edge = turf.boundary


def distance_field(x0, z0, x1, z1, res, size=None):
    """Metres from the turf's edge at each pixel centre (row 0 = z0, the north edge); 0 off the turf.
    size = (w, h) to fix the image size instead of working it out from res."""
    w, h = size or (int(round((x1 - x0) / res)), int(round((z1 - z0) / res)))
    xs = x0 + (np.arange(w) + 0.5) * (x1 - x0) / w
    zs = z0 + (np.arange(h) + 0.5) * (z1 - z0) / h
    X, Z = np.meshgrid(xs, zs)
    pts = shapely.points(X.ravel(), Z.ravel())
    inside = shapely.contains(turf, pts)
    d = np.zeros(X.size)
    d[inside] = shapely.distance(pts[inside], edge)
    return d.reshape(h, w)


def lanes_value(d, lanes=8, width=30.0):
    """The stripe pattern itself, 0..1 (0.5 off the turf): a cosine across the track, one bright and one
    dark band every two lanes."""
    v = 0.5 + 0.5 * np.cos(np.pi * lanes * d / width)
    return np.where(d > 0, v, 0.5)


if __name__ == "__main__":
    a = np.array(rings[0])
    x0, z0 = np.floor(a.min(0)) - 8
    x1, z1 = np.ceil(a.max(0)) + 8
    d = distance_field(x0, z0, x1, z1, RES)
    img = np.clip(d / MAXD, 0, 1)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "L").save(rp("race-view/assets/course/lanes.png"), optimize=True)
    settings = {"_about": "Soft mown lanes along the running line (tools/course/build_lane_field.py). map: grey = metres from "
                          "the turf's edge / maxDist (row 0 = z0, north). Stripes: 0.5 + 0.5 cos(pi * lanes * d / width), "
                          "brightening the turf by +-strength. The ground bake draws the same stripes.",
                "map": "lanes.png", "area": [float(x0), float(z0), float(x1), float(z1)], "maxDist": MAXD,
                "lanes": 8, "width": COURSE["trackWidth"], "strength": 0.14}
    for f in ("courses/ascot-view.json", "race-view/assets/course/ascot-view.json"):
        v = json.load(open(rp(f)))
        v["lanes"] = settings
        json.dump(v, open(rp(f), "w"), indent=1)
    print("lanes.png %dx%d, %.0f%% turf" % (img.shape[1], img.shape[0], 100 * (d > 0).mean()))
