"""Pulls each place's lit outline in tight to its buildings (the owner's reference: the light runs along the roof
edges). The buildings come from the board itself: the occlusion pass's 'things' (assets/occlusion.png), without the
greenery, kept where they are big enough to be buildings. For each place:
- 'complex' (Tattersalls, the Stables): the buildings inside the owner's outline, joined to the owner's outline
  pulled in a little, so the light runs along the outer roof edges and straight across the gaps between ranges;
- 'building' (Palace House, the Jockey Club, the National Stud): just the buildings, closed up and filled;
- 'drawn' (Warren Hill, open heath): the owner's line as drawn.
Writes markup/sites-tight.json; with a path, a check picture."""
import cv2, numpy as np, json, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
im = cv2.imread(str(here / "assets/newmarket-board.webp")); H, W = im.shape[:2]
o = cv2.imread(str(here / "assets/occlusion.png")); obj = ((o[..., 1].astype(int) + o[..., 2].astype(int) * 256) > 0).astype(np.uint8)
lab = cv2.cvtColor(cv2.GaussianBlur(im, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(int)
bld = (obj > 0) & ((lab[..., 2] < 143) | (lab[..., 1] > 133))
bld = cv2.morphologyEx(bld.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, cc, st, _ = cv2.connectedComponentsWithStats(bld, 8)
big = np.zeros(n, bool); big[1:] = st[1:, cv2.CC_STAT_AREA] >= 260
bld = big[cc]
sites = {s["id"]: s for s in json.load(open(here / "markup/markup.json"))["sites"]}
MODE = {"tatts": ("complex", 12, 21), "stables": ("complex", 12, 21), "palace": ("building", 0, 13), "jockey": ("building", 0, 11),
        "stud": ("building", 0, 15), "warren": ("drawn", 0, 0)}
out = []
for sid, s in sites.items():
    mode, pull, close = MODE[sid]
    poly = np.array(s["poly"], np.int32)
    area = np.zeros((H, W), np.uint8); cv2.fillPoly(area, [poly], 1)
    if mode == "drawn":
        shape = area
    else:
        near = cv2.dilate(area, np.ones((9, 9), np.uint8))
        # whole buildings that mostly sit inside the owner's outline
        cand = (bld & (near > 0)).astype(np.uint8)
        if mode == "building":                                                      # cut trees away from walls
            cand = cv2.morphologyEx(cand, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        n2, cc2, st2, _ = cv2.connectedComponentsWithStats(cand, 8)
        keep = np.zeros(n2, bool)
        for i in range(1, n2):
            m = cc2 == i
            keep[i] = (area[m] > 0).mean() > 0.5 and st2[i, cv2.CC_STAT_AREA] >= (500 if mode == "building" else 260)
        b = keep[cc2].astype(np.uint8)
        b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
        shape = b
        if mode == "complex":
            shape = shape | cv2.erode(area, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (pull * 2 + 1, pull * 2 + 1)))
        ff = (1 - shape).astype(np.uint8); msk = np.zeros((H + 2, W + 2), np.uint8); cv2.floodFill(ff, msk, (0, 0), 0)
        shape = shape | ff                                                              # fill the yards inside
        shape = cv2.morphologyEx(shape, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
        # smooth the edge without letting it drift off the roofs: blur the shape a little and cut it at the middle
        shape = (cv2.GaussianBlur(shape.astype(np.float32), (0, 0), 2.2) > 0.5).astype(np.uint8)
    cs, _ = cv2.findContours(shape, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    pts = cv2.approxPolyDP(c, 1.4 if mode != "drawn" else 2.0, True).reshape(-1, 2).tolist()
    out.append({"id": sid, "poly": pts, "sharp": mode != "drawn"})
    print(sid, mode, len(pts), int(cv2.contourArea(c)))
json.dump(out, open(here / "markup/sites-tight.json", "w"))
if len(sys.argv) > 1:
    vis = im.copy()
    for s in out: cv2.polylines(vis, [np.array(s["poly"], np.int32)], True, (40, 220, 255), 2, cv2.LINE_AA)
    cv2.imwrite(sys.argv[1], vis)
