"""Take the carnival path off the turf in the baked ground (owner, 7 Nov: "a strange strip on the home bend of brown").

    python3 tools/course/fix_ground_path.py

The baked ground (race-view/assets/baked/ground.jpg) has the carnival's path running east along z -26..-21 right to the
image's edge at x 700, so it crossed the round course's turf where the home bend comes in. Every pixel of the path band
that lies on the turf (courses' track.surface) is replaced with the turf mirrored across the path's nearer edge (north, or south where the north is off the turf), which
carries the mown lanes across. Reads the untouched image from raw/ground.jpg (kept the first time).
"""
import os, json, shutil
import numpy as np
from PIL import Image
from matplotlib.path import Path

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(REPO, "race-view", "assets", "baked")
raw = os.path.join(D, "raw", "ground.jpg")
os.makedirs(os.path.dirname(raw), exist_ok=True)
if not os.path.exists(raw): shutil.copy2(os.path.join(D, "ground.jpg"), raw)
B = json.load(open(os.path.join(D, "bake.json")))["ground"]["area"]
C = json.load(open(os.path.join(REPO, "race-view", "assets", "course", "ascot.json")))
rings = C["track"]["surface"]
im = np.asarray(Image.open(raw).convert("RGB")).copy()
H, W = im.shape[:2]
sx, sz = W / (B["x1"] - B["x0"]), H / (B["z1"] - B["z0"])
z0, z1 = -28.0, -19.0                                       # the path band, with a margin
r0, r1 = int((z0 - B["z0"]) * sz), int((z1 - B["z0"]) * sz) + 1
c0 = int((600 - B["x0"]) * sx)
R0, R1 = max(0, r0 - (r1 - r0) - 4), min(H, r1 + (r1 - r0) + 4)    # the band and as much again either side
rows, cols = np.mgrid[R0:R1, c0:W]
x = B["x0"] + (cols + 0.5) / sx; z = B["z0"] + (rows + 0.5) / sz
pts = np.stack([x.ravel(), z.ravel()], 1)
turf = Path(rings[0]).contains_points(pts)
for h in rings[1:]: turf &= ~Path(h).contains_points(pts)
turf = turf.reshape(x.shape)
T = lambda r, j: R0 <= r < R1 and turf[r - R0, j] and not (r0 <= r < r1)
n = 0
for r in range(r0, r1):
    north, south = r0 - 1 - (r - r0), r1 + (r1 - 1 - r)        # mirrored about the band's north or south edge
    for j in np.where(turf[r - R0])[0]:
        src = north if T(north, j) else south if T(south, j) else None
        if src is None: continue
        im[r, c0 + j] = im[src, c0 + j]; n += 1
Image.fromarray(im).save(os.path.join(D, "ground.jpg"), quality=92)
print("replaced", n, "pixels of path on the turf")
