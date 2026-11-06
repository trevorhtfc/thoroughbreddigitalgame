"""Places the banner avenue: flags in racing silks along the road north of the National Stud, leading off the board
towards To the Races. Banners stand on the road's north verge, at least SPACE apart, skipping the drive into the
paddocks and anywhere a tree or building standing in front (further south) would cover them.
Writes assets/banners.json (road, and each banner's foot point); with a path, a check picture."""
import cv2, numpy as np, json, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
ROAD = [(850, 446), (900, 425), (970, 402), (1080, 372), (1150, 357), (1220, 345), (1320, 321), (1420, 287), (1452, 276)]
SPACE, OFF, POLE, FLAG_W = 45, 9, 40, 26
o = cv2.imread(str(here / "assets/occlusion.png")); foot = (o[..., 1].astype(int) + o[..., 2].astype(int) * 256) - 1
p = np.array(ROAD, float); seg = np.hypot(*np.diff(p, axis=0).T); s = np.r_[0, np.cumsum(seg)]
def at(d):
    x, y = np.interp(d, s, p[:, 0]), np.interp(d, s, p[:, 1]); i = min(len(seg) - 1, np.searchsorted(s, d) - 1)
    t = (p[i + 1] - p[i]) / seg[i]; n = np.array([t[1], -t[0]]) * (1 if t[0] > 0 else -1)        # the side up the page
    if n[1] > 0: n = -n
    return np.array([x, y]) + n * OFF
banners, last = [], -1e9
for d in np.arange(55, s[-1], 2.0):
    q = at(d)
    if q[0] > 1318: break                                                  # the sign stands at the end of the road
    if 1035 < q[0] < 1090: continue                                        # the drive into the paddocks
    if np.hypot(*(q - (banners[-1] if banners else np.array([-1e9, 0])))) < SPACE: continue
    x0, x1, y0, y1 = int(q[0]) - 2, int(q[0]) + FLAG_W + 2, int(q[1]) - POLE - 4, int(q[1])
    box = foot[y0:y1, x0:x1]
    if ((box > q[1] + 2).mean()) > 0.04: continue                          # something in front would cover it
    banners.append(q)
out = {"road": ROAD, "banners": [[round(float(a), 1), round(float(b), 1)] for a, b in banners], "pole": POLE, "flag": FLAG_W}
json.dump(out, open(here / "assets/banners.json", "w"))
print(len(banners), out["banners"])
if len(sys.argv) > 1:
    im = cv2.imread(str(here / "assets/newmarket-board.webp"))
    cv2.polylines(im, [np.array(ROAD, np.int32)], False, (255, 80, 40), 1)
    for x, y in banners: cv2.line(im, (int(x), int(y)), (int(x), int(y) - POLE), (255, 255, 255), 2); cv2.rectangle(im, (int(x), int(y) - POLE + 2), (int(x) + FLAG_W, int(y) - POLE + 18), (40, 40, 220), -1)
    cv2.imwrite(sys.argv[1], cv2.resize(im[220:480, 820:1448], None, fx=2, fy=2))
