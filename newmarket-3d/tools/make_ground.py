"""The ground for the 3D Tattersalls corner, made from the board itself.

    python3 newmarket-3d/tools/make_ground.py

Crops the corner from assets/maps/newmarket-map.webp, paints out the drawn buildings and lorries (they become 3D),
keeps the painted lawns, paths, yards and shadows, and finds the painted trees so 3D trees can stand on them.
Writes newmarket-3d/build/ground.jpg (the texture), mask.png (what was painted out, for checking) and trees.json.
"""
import json, math, os
import numpy as np, cv2
from scipy import ndimage
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); REPO = os.path.dirname(ROOT)
L = json.load(open(os.path.join(ROOT, "layout.json")))
OUT = os.path.join(ROOT, "build"); os.makedirs(OUT, exist_ok=True)
x0, y0, x1, y1 = L["crop"]; S = L["scale"]
src = cv2.imread(os.path.join(REPO, "assets/maps/newmarket-map.webp"))
img = cv2.resize(src[y0:y1, x0:x1], ((x1 - x0) * S, (y1 - y0) * S), interpolation=cv2.INTER_LANCZOS4)
H, W = img.shape[:2]
PX_M = 5.0                                    # image pixels per metre

def band(pts, depth):                         # the painted building: from the wall's foot up past its roof
    shapes = []
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay; n = math.hypot(dx, dy); nx, ny = dy / n, -dx / n      # left of travel, on screen
        back = depth * PX_M
        # the footprint, then the painted roof and wall standing up from it (drawn higher up the board)
        foot = Polygon([(ax - nx * 4, ay - ny * 4), (bx - nx * 4, by - ny * 4), (bx + nx * back, by + ny * back), (ax + nx * back, ay + ny * back)])
        shapes.append(unary_union([foot, shift(foot, 0, -34)]).convex_hull.buffer(5))
    return unary_union(shapes)

def shift(poly, dx, dy):
    return Polygon([(x + dx, y + dy) for x, y in poly.exterior.coords])

parts = [band(r["pts"], r["depth"]) for r in L["ranges"]]
rx, ry = L["rotunda"]["at"]; parts.append(Point(rx, ry - 16).buffer(L["rotunda"]["apothem"] * PX_M * 1.17))
for h in L["houses"]:
    hx, hy = h["at"]; parts.append(Point(hx, hy - 14).buffer(max(h["w"], h["d"]) * PX_M * 0.62 + 8))
for lo in L["lorries"]:
    lx, ly = lo["at"]; parts.append(Point(lx, ly).buffer(26))
mask_poly = unary_union(parts)
mask = np.zeros((H, W), np.uint8)
geoms = mask_poly.geoms if hasattr(mask_poly, "geoms") else [mask_poly]
for g in geoms:
    cv2.fillPoly(mask, [np.array(g.exterior.coords, np.int32)], 255)

# The painted trees: dark, saturated green blobs outside the buildings
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
b, g, r = [img[:, :, k].astype(int) for k in range(3)]
tree = ((hsv[:, :, 2] < 120) & (g > r + 4) & (g > b + 8) & (hsv[:, :, 1] > 60)).astype(np.uint8)
tree = cv2.morphologyEx(tree, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
tree = cv2.dilate(tree, np.ones((5, 5), np.uint8))
lab, n = ndimage.label(tree)
trees = []
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    ys, xs = np.nonzero(lab[sl] == i); area = len(xs)
    if area < 90: continue
    cx, cy = xs.mean() + sl[1].start, ys.max() + sl[0].start - 4          # trunk at the foot of the crown
    if mask[int(min(H - 1, cy)), int(cx)]: continue
    w = xs.max() - xs.min() + 1
    if w > 70:                                                            # a clump: split into several trees
        k = int(math.ceil(w / 45))
        for j in range(k):
            trees.append({"x": float(sl[1].start + xs.min() + (j + 0.5) * w / k), "y": float(cy), "r": float(w / k / 2)})
    else:
        trees.append({"x": float(cx), "y": float(cy), "r": float(w / 2)})
json.dump(trees, open(os.path.join(OUT, "trees.json"), "w"))

# Paint the buildings out: fill from the surrounding ground, then soften the patch a little
sample = cv2.dilate(mask, np.ones((21, 21), np.uint8))                 # sample the ground clear of the walls' dark edges
keep = (sample == 0).astype(np.float32)
f = img.astype(np.float32)
def pushpull(img_f, valid):                                               # fill holes from their edges, coarse to fine
    if min(img_f.shape[:2]) < 4 or valid.min() > 0: return img_f
    sm = cv2.resize(img_f * valid[:, :, None], (img_f.shape[1] // 2, img_f.shape[0] // 2), interpolation=cv2.INTER_AREA)
    sv = cv2.resize(valid, (valid.shape[1] // 2, valid.shape[0] // 2), interpolation=cv2.INTER_AREA)
    small = sm / np.maximum(sv, 1e-4)[:, :, None]
    small = pushpull(small, (sv > 0.01).astype(np.float32))
    up = cv2.resize(small, (img_f.shape[1], img_f.shape[0]), interpolation=cv2.INTER_LINEAR)
    return img_f * valid[:, :, None] + up * (1 - valid[:, :, None])
local = cv2.GaussianBlur(pushpull(f, keep), (0, 0), 6)
yard = np.median(f[640:700, 940:990].reshape(-1, 3), axis=0) * 0.93      # the east yard's sand, a shade darker
local = local * 0.3 + yard * 0.7
rng = np.random.default_rng(3)                                            # a painterly grain: fine speckle and soft blotches
tile = cv2.GaussianBlur(rng.normal(0, 9, (H, W, 1)).astype(np.float32), (0, 0), 0.8) + cv2.GaussianBlur(rng.normal(0, 16, (H, W, 1)).astype(np.float32), (0, 0), 6)
tile = np.repeat(tile.reshape(H, W, 1), 3, axis=2) * np.array([0.8, 0.95, 1.1])           # BGR: grain leans warm
fill = np.clip(local + tile, 0, 255)
m3 = (cv2.GaussianBlur(mask, (0, 0), 3) / 255.0)[:, :, None]
clean = (f * (1 - m3) + fill * m3).astype(np.uint8)
big = cv2.resize(clean, (W * 2, H * 2), interpolation=cv2.INTER_CUBIC)
cv2.imwrite(os.path.join(OUT, "ground.jpg"), big, [cv2.IMWRITE_JPEG_QUALITY, 92])
cv2.imwrite(os.path.join(OUT, "mask.png"), mask)
over = img.copy(); over[mask > 0] = (over[mask > 0] * 0.4 + np.array([0, 0, 200]) * 0.6).astype(np.uint8)
for t in trees: cv2.circle(over, (int(t["x"]), int(t["y"])), 4, (255, 255, 0), -1)
cv2.imwrite(os.path.join(OUT, "check.jpg"), over)
print(f"ground {W*2}x{H*2}, {len(trees)} trees, {int(mask.mean()/2.55)}% painted out")
