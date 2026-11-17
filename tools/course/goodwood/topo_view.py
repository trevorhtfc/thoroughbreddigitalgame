"""Goodwood: an oblique view of the real ground with the course on it (heights x2), for the topography study.

  python3 tools/course/goodwood/topo_view.py      -> reference/goodwood/topo-oblique.png
"""
import json, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from shapely.geometry import Polygon, Point
from shapely.prepared import prep

REPO = Path(__file__).resolve().parents[3]
D = json.loads((REPO / "reference/goodwood/dem-course-20m.json").read_text())
O = json.loads((REPO / "reference/goodwood/osm-goodwood.json").read_text())
H = np.array(D["h_dm"], float) / 10
x = D["x0"] + np.arange(D["nx"]) * 20.0; y = D["y0"] + np.arange(D["ny"]) * 20.0
KX = 111320 * math.cos(math.radians(D["lat0"])); KY = 110574
en = lambda a: [((p[1] - D["lon0"]) * KX, (p[0] - D["lat0"]) * KY) for p in a]
turf = prep(Polygon(en(O["track"]["outer"]), [en(O["track"]["inner_bottom"]), en(O["track"]["inner_top"])]).buffer(6))
# a finer grid for the picture (10 m), bilinear from the 20 m one
xf = np.arange(-1300, 1300, 10.0); yf = np.arange(-1150, 1150, 10.0)
X, Y = np.meshgrid(xf, yf)
fx = (X - D["x0"]) / 20; fy = (Y - D["y0"]) / 20
i = np.clip(fx.astype(int), 0, D["nx"] - 2); j = np.clip(fy.astype(int), 0, D["ny"] - 2); a = fx - i; b = fy - j
Z = (H[j, i] * (1 - a) + H[j, i + 1] * a) * (1 - b) + (H[j + 1, i] * (1 - a) + H[j + 1, i + 1] * a) * b
on = np.array([[turf.contains(Point(px, py)) for px, py in zip(rx, ry)] for rx, ry in zip(X, Y)])
base = np.where(on[..., None], np.array([0.30, 0.55, 0.22]), np.array([0.80, 0.80, 0.62]))
ls = LightSource(azdeg=225, altdeg=35)
shade = ls.hillshade(Z, vert_exag=2, dx=10, dy=10)[..., None]
rgb = np.clip(base * (0.55 + 0.6 * shade), 0, 1)
fig = plt.figure(figsize=(15, 9), dpi=120)
ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(X, Y, Z * 2, facecolors=rgb, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
for name, la, lo in [("The Trundle 206 m", 50.8925, -0.7577), ("stands", 50.8919, -0.7452)]:
    px, py = (lo - D["lon0"]) * KX, (la - D["lat0"]) * KY
    fi = int((py + 1150) / 10); fj = int((px + 1300) / 10)
    ax.text(px, py, Z[fi, fj] * 2 + 40, name, fontsize=9, fontweight="bold")
ax.view_init(elev=24, azim=-58)        # from the south-east, looking north-west (as the owner's Google Earth view)
ax.set_box_aspect((2600, 2300, float(Z.max() - Z.min()) * 2), zoom=1.45); ax.set_axis_off()
ax.set_title("Goodwood: the course on the real ground, from the south-east (heights x2). The straight on the ridge; the loop "
             "dropping north off it into the dry valleys; the Trundle to the west", fontsize=10, loc="left")
fig.tight_layout(); fig.savefig(REPO / "reference/goodwood/topo-oblique.png", facecolor="white", bbox_inches="tight")
