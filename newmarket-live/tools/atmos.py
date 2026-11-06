"""Finds where the board's atmosphere comes from: chimneys (the tops of houses and stable ranges, for smoke) and
windows (low on the walls, lit at dusk), from the buildings found on the board (the same way tools/refine_sites.py
does). Writes assets/atmos.json; with a path, a check picture (smoke orange, windows yellow)."""
import cv2, numpy as np, json, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
rng = np.random.default_rng(11)
im = cv2.imread(str(here / "assets/newmarket-board.webp")); H, W = im.shape[:2]
o = cv2.imread(str(here / "assets/occlusion.png")); obj = ((o[..., 1].astype(int) + o[..., 2].astype(int) * 256) > 0)
lab = cv2.cvtColor(cv2.GaussianBlur(im, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(int)
bld = (obj & ((lab[..., 2] < 143) | (lab[..., 1] > 133))).astype(np.uint8)
bld = cv2.morphologyEx(bld, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
n, cc, st, cen = cv2.connectedComponentsWithStats(bld, 8)
chimneys, windows = [], []
for i in range(1, n):
    x, y, w, h, a = st[i]
    if a < 650 or w > 720 or h > 300: continue                     # painted lorries are smaller than this
    if x < 330 and y > 600: continue                                     # Warren Hill's tree belts
    ys, xs = np.nonzero(cc[y:y + h, x:x + w] == i); ys += y; xs += x
    solidity = a / float(w * h)
    if solidity < 0.35: continue                                          # ragged blobs are trees
    A, B = lab[ys, xs, 1], lab[ys, xs, 2]
    masonry = ((A > 131) | ((np.abs(A - 128) < 4) & (B < 138))).mean()   # brick, terracotta or slate, not leaves
    if masonry < 0.55: continue
    # smoke: from a few points along the top of the roof
    k = 1 if a < 1500 else (2 if a < 5000 else min(6, 3 + int(w / 200)))
    for j in range(k):
        cx = x + w * (j + 0.5) / k + rng.uniform(-w * 0.1, w * 0.1); col = np.abs(xs - cx) < 2
        if col.any(): chimneys.append([round(float(cx), 1), round(float(ys[col].min()) + 1.5, 1)])
    # windows: low on the walls, spaced along the building
    m = max(1, int(w / 22))
    for j in range(m):
        wx = x + w * (j + 0.5) / m; col = np.abs(xs - wx) < 2
        if not col.any(): continue
        foot = ys[col].max(); top = ys[col].min()
        windows.append([round(float(wx), 1), round(float(foot - (foot - top) * 0.22), 1)])
# the long stable ranges and Tattersalls' ranges are too big and too slate-grey for the search above: placed by hand
chimneys = [c for c in chimneys if np.hypot(c[0] - 785, c[1] - 925) > 18]          # a painted lorry, not a house
chimneys += [[720, 830], [800, 808], [900, 790], [1000, 812], [1100, 830], [760, 965], [880, 945], [1000, 925], [1100, 910],
             [1180, 815], [1290, 800], [1390, 800], [1410, 840], [765, 660], [830, 640], [1120, 672], [1240, 720]]
windows += [[740, 850], [820, 833], [900, 822], [980, 835], [1060, 850], [1120, 855], [800, 985], [900, 970], [1000, 958], [1100, 945],
            [1200, 835], [1300, 825], [1390, 830], [780, 700], [840, 655], [1150, 700], [1250, 745], [1000, 682], [970, 672], [1030, 672]]
rng.shuffle(chimneys)
chimneys = chimneys[:48]                                                  # not every chimney is lit at once
out = {"chimneys": chimneys, "windows": windows, "flags": [[990, 604, 22], [670, 588, 20]]}
json.dump(out, open(here / "assets/atmos.json", "w"))
print("chimneys", len(chimneys), "windows", len(windows))
if len(sys.argv) > 1:
    vis = im.copy()
    for x, y in chimneys: cv2.circle(vis, (int(x), int(y)), 4, (0, 120, 255), -1)
    for x, y in windows: cv2.circle(vis, (int(x), int(y)), 2, (0, 240, 255), -1)
    cv2.imwrite(sys.argv[1], vis)
