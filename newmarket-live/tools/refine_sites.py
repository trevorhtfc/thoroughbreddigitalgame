"""Refines the owner's lit outlines without departing from them (markup/markup.json, traced from the owner's lines):
- evens out the pen's wobble (the line resampled every few pixels and gently averaged along its length);
- where a building's roof edge lies within SNAP pixels of the drawn line, settles the line onto it, easing in and out
  so neighbouring stretches move together; anywhere else the line stays where it was drawn.
Writes markup/sites-tight.json (what the page uses); with a path, a check picture showing the owner's line (pink)
and the refined one (yellow)."""
import cv2, numpy as np, json, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
SNAP, STEP = 6.0, 3.0
EPS = {"warren": 5.5}
im = cv2.imread(str(here / "assets/newmarket-board.webp")); H, W = im.shape[:2]
# buildings: the occlusion pass's things, without the greenery, big enough to be buildings
o = cv2.imread(str(here / "assets/occlusion.png")); obj = ((o[..., 1].astype(int) + o[..., 2].astype(int) * 256) > 0)
lab = cv2.cvtColor(cv2.GaussianBlur(im, (0, 0), 1.5), cv2.COLOR_BGR2LAB).astype(int)
bld = (obj & ((lab[..., 2] < 143) | (lab[..., 1] > 133))).astype(np.uint8)
bld = cv2.morphologyEx(bld, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
n, cc, st, _ = cv2.connectedComponentsWithStats(bld, 8)
big = np.zeros(n, bool); big[1:] = st[1:, cv2.CC_STAT_AREA] >= 400; bld = big[cc].astype(np.uint8)
bld = cv2.morphologyEx(bld, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
edge = bld - cv2.erode(bld, np.ones((3, 3), np.uint8))
# for every pixel, the nearest roof-edge pixel
dist, lbl = cv2.distanceTransformWithLabels((1 - edge).astype(np.uint8), cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
ey, ex = np.nonzero(edge); edge_xy = np.zeros((lbl.max() + 1, 2)); 
# labels are assigned to zero pixels (the edges) in scan order
edge_xy[1:len(ex) + 1] = np.stack([ex, ey], 1)
def resample(poly, step):
    p = np.array(poly + [poly[0]], float); seg = np.hypot(*np.diff(p, axis=0).T); s = np.r_[0, np.cumsum(seg)]
    t = np.arange(0, s[-1], step); return np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)
def smooth_closed(v, sigma):
    k = int(sigma * 3); w = np.exp(-0.5 * (np.arange(-k, k + 1) / sigma) ** 2); w /= w.sum()
    pad = np.concatenate([v[-k:], v, v[:k]]); return np.stack([np.convolve(pad[:, i], w, "valid") for i in range(v.shape[1])], 1)
sites = json.load(open(here / "markup/markup.json"))["sites"]
out = []
for s in sites:
    p = smooth_closed(resample(s["poly"], STEP), 2.0)                              # the drawn line, wobble evened out
    off = np.zeros_like(p); wgt = np.zeros(len(p))
    if s["id"] != "warren":
        for i, (x, y) in enumerate(p):
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < W and 0 <= yi < H and dist[yi, xi] <= SNAP:
                tx, ty = edge_xy[lbl[yi, xi]]; off[i] = (tx - x, ty - y); wgt[i] = 1
        # ease the snapping along the line, so it settles onto a roof and eases off again rather than jumping
        off = smooth_closed(off, 3.0); wgt = smooth_closed(wgt[:, None], 3.0)[:, 0]
        off *= np.clip(wgt * 1.6, 0, 1)[:, None] / np.maximum(wgt, 1e-3)[:, None] * np.minimum(wgt, 1)[:, None]
        mag = np.hypot(off[:, 0], off[:, 1]); off *= np.minimum(1, SNAP / np.maximum(mag, 1e-6))[:, None]
    q = p + off
    # straighten: long straight runs between corners, never more than EPS from the refined line (the owner's call)
    q = cv2.approxPolyDP(q.astype(np.float32).reshape(-1, 1, 2), EPS.get(s["id"], 4.5), True).reshape(-1, 2)
    out.append({"id": s["id"], "poly": [[round(float(a), 1), round(float(b), 1)] for a, b in q], "sharp": True})
    print(s["id"], "points", len(q), "snapped share", round(float((wgt > 0.5).mean()), 2), "largest move", round(float(np.hypot(*off.T).max()), 1))
json.dump(out, open(here / "markup/sites-tight.json", "w"))
if len(sys.argv) > 1:
    vis = im.copy()
    for s in sites: cv2.polylines(vis, [np.array(s["poly"], np.int32)], True, (200, 60, 255), 2, cv2.LINE_AA)
    for s in out: cv2.polylines(vis, [np.round(np.array(s["poly"])).astype(np.int32)], True, (40, 230, 255), 2, cv2.LINE_AA)
    cv2.imwrite(sys.argv[1], vis)
