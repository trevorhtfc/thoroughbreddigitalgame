"""Turns the owner's markups into data: registers each to the clean map, splits the drawing by colour,
and reduces strokes to ordered centre lines (routes) or filled outlines (sites). Writes markup.json."""
import cv2, numpy as np, json
from skimage.morphology import skeletonize
clean = cv2.imread('clean-map.jpg')
def layers(name):
    w = cv2.imread(f'{name}-registered.png')
    d = cv2.absdiff(w, clean).astype(int).sum(axis=2)
    hsv = cv2.cvtColor(w, cv2.COLOR_BGR2HSV); H, S, V = [hsv[..., i].astype(int) for i in range(3)]
    return (d > 90), H, S, V
def comps(mask, minpix=60):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    return [(lab == i) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= minpix]
def ordered_path(mask):
    """Longest path through the skeleton of a stroke, as points in order."""
    sk = skeletonize(mask)
    ys, xs = np.nonzero(sk); pts = set(zip(xs.tolist(), ys.tolist()))
    nb = lambda p: [(p[0] + dx, p[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx or dy) and (p[0] + dx, p[1] + dy) in pts]
    def bfs(s):
        prev = {s: None}; q = [s]; last = s
        for p in q:
            for n in nb(p):
                if n not in prev: prev[n] = p; q.append(n); last = n
        return last, prev
    a, _ = bfs(next(iter(pts))); b, prev = bfs(a)
    path = []; p = b
    while p is not None: path.append(p); p = prev[p]
    return path
def simplify(path, eps=2.0):
    c = np.array(path, np.float32).reshape(-1, 1, 2)
    return [[round(float(x), 1), round(float(y), 1)] for x, y in cv2.approxPolyDP(c, eps, False).reshape(-1, 2)]
def width(mask):
    dt = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2, 3); sk = skeletonize(mask)
    return float(np.median(dt[sk]) * 2)
if __name__ == "__main__":
    out = {"size": [clean.shape[1], clean.shape[0]], "routes": [], "sites": []}
    ann, H, S, V = layers('routes')
    red = ann & (S > 90) & ((H <= 15) | (H >= 170)); blue = ann & (S > 90) & (H >= 100) & (H <= 115)
    pink = ann & (S > 60) & (H >= 135) & (H <= 160); white = ann & (S < 60) & (V > 190)
    for kind, m in [("red", red), ("blue", blue), ("pink", pink), ("white", white)]:
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
        for c in comps(m, 80):
            p = ordered_path(c); wd = width(c)
            out["routes"].append({"colour": kind, "width": round(wd, 1), "pts": simplify(p), "bbox": [int(v) for v in cv2.boundingRect(c.astype(np.uint8))]})
    ann, H, S, V = layers('sites')
    X = np.arange(ann.shape[1])[None, :].repeat(ann.shape[0], 0); Y = np.arange(ann.shape[0])[:, None].repeat(ann.shape[1], 1)
    def outline(m):
        """The drawn loop as a polygon along the middle of the stroke. A closed loop is filled; one with a gap
        is followed end to end and closed."""
        m8 = cv2.morphologyEx(m.astype(np.uint8) * 255, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        ff = 255 - m8; msk = np.zeros((m8.shape[0] + 2, m8.shape[1] + 2), np.uint8); cv2.floodFill(ff, msk, (0, 0), 0)
        if (ff > 0).sum() > 5000:
            filled = cv2.dilate(ff, np.ones((3, 3), np.uint8), iterations=2)          # out to the middle of the stroke
            cs, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); big = max(cs, key=cv2.contourArea)
            return cv2.approxPolyDP(big, 1.2, True).reshape(-1, 2).tolist()
        d = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        n, lab, st, _ = cv2.connectedComponentsWithStats(d.astype(np.uint8), 8)
        i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        p = np.array(ordered_path(lab == i), np.int32).reshape(-1, 1, 2)
        return cv2.approxPolyDP(p, 1.2, True).reshape(-1, 2).tolist()
    base = ann & (S > 40)
    SITES = {"tatts": base & (H >= 115) & (H <= 165) & (X >= 735) & (X < 1110) & (Y >= 560) & (Y < 830),
             "jockey": base & (H >= 110) & (H <= 140) & (X < 770) & (X > 540) & (Y > 540),
             "stables": base & (S > 80) & ((H <= 12) | (H >= 172)) & (Y > 760),
             "palace": base & (S > 80) & (H >= 22) & (H <= 36),
             "stud": base & (S > 80) & (H >= 85) & (H <= 105) & (Y > 360)}
    for k, m in SITES.items():
        poly = outline(m); arr = np.array(poly, np.int32)
        out["sites"].append({"id": k, "bbox": list(cv2.boundingRect(arr)), "area": float(cv2.contourArea(arr)), "poly": poly})
    out["labelX"] = [1227, 185, 66, 77]                    # the crossed-out National Stud label
    json.dump(out, open('markup.json', 'w'))
    for r in out["routes"]: print(r["colour"], r["width"], r["bbox"], len(r["pts"]), r["pts"][0], r["pts"][-1])
    for s in out["sites"]: print(s["id"], s["bbox"], s["area"], len(s["poly"]))
