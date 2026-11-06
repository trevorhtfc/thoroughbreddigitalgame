"""Works out, for every pixel of the board that shows a building (or a tree), where that thing stands: the board
is painted from the south with heights going up the page, so a roof is drawn above its own foot. A horse whose feet
are further up the page (further north) than a building's foot is behind it, and the page hides it there.
Writes assets/occlusion.png: for each pixel, the board y of the foot of whatever is drawn there (16 bits split over
red and green), or 0 for open ground. With a path, also writes a check picture."""
import cv2, numpy as np, sys
from pathlib import Path
from sklearn.cluster import MiniBatchKMeans
here = Path(__file__).resolve().parent.parent
im = cv2.imread(str(here / "assets/newmarket-board.webp")); H, W = im.shape[:2]
lab = cv2.cvtColor(cv2.GaussianBlur(im, (0, 0), 1.0), cv2.COLOR_BGR2LAB).astype(np.float32)
g = lab[..., 0]; mean = cv2.blur(g, (7, 7)); tex = np.sqrt(np.maximum(cv2.blur(g * g, (7, 7)) - mean * mean, 0))
feat = np.dstack([lab[..., 0], lab[..., 1] * 2.0, lab[..., 2] * 2.0, tex * 1.5]).reshape(-1, 4)
km = MiniBatchKMeans(14, random_state=0, batch_size=20000, n_init=3).fit(feat[::7])
lbl = km.predict(feat).reshape(H, W); C = km.cluster_centers_
# things, not ground: dark (trees, walls, doors), or warm and busy (roofs, brick), or very busy; shaded grass is
# greenish and stays ground; pale cool greys (the rotunda's roof) are things too
L, A, Tx = C[:, 0], C[:, 1] / 2, C[:, 3] / 1.5
thing = [k for k in range(14) if (L[k] < 112) or (A[k] >= 126 and L[k] < 160 and Tx[k] > 8) or (L[k] < 150 and Tx[k] > 40)]
print("thing clusters", thing)
obj = np.isin(lbl, thing).astype(np.uint8)
obj[(lab[..., 2] < 138) & (lab[..., 0] > 140)] = 1
# the two ring tracks are ground, however dark they are painted
ring = np.zeros((H, W), np.uint8)
cv2.ellipse(ring, (1312, 878), (74, 40), 0, 0, 360, 1, -1); cv2.ellipse(ring, (1168, 752), (63, 34), 15, 0, 360, 1, -1)
obj[ring > 0] = 0
obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
# fill holes (pale patches of roof, windows) inside each building or tree
inv = (1 - obj).astype(np.uint8); n0, cc0, st0, _ = cv2.connectedComponentsWithStats(inv, 4)
small = np.zeros(n0, bool); small[1:] = st0[1:, cv2.CC_STAT_AREA] < 400; obj[small[cc0]] = 1
n, cc, st, _ = cv2.connectedComponentsWithStats(obj, 8)
keep = np.zeros(n, bool); keep[1:] = st[1:, cv2.CC_STAT_AREA] >= 60          # painted figures and posts don't hide anything
obj = keep[cc].astype(np.uint8)
# road names painted along the roads are lettering, not things: drop what lies wholly inside their boxes
TEXT = [(612, 75, 640, 160), (580, 455, 632, 540), (445, 355, 530, 425), (245, 340, 330, 395), (335, 255, 430, 290), (70, 245, 150, 295),
        (820, 140, 870, 185), (880, 460, 995, 540), (345, 850, 430, 970), (385, 460, 420, 510)]
n, cc, st, _ = cv2.connectedComponentsWithStats(obj, 8)
drop = np.zeros(n, bool)
for i in range(1, n):
    x, y, w, h = st[i, :4]
    drop[i] = any(x >= x0 and y >= y0 and x + w <= x1 and y + h <= y1 for (x0, y0, x1, y1) in TEXT)
obj[drop[cc]] = 0
obj[:12, :] = 0; obj[-12:, :] = 0; obj[:, :12] = 0; obj[:, -12:] = 0          # the frame
# foot of each run, column by column, bridging tiny gaps
base = np.zeros((H, W), np.int32); run = np.zeros(W, np.int32); gap = np.full(W, 99)
for y in range(H - 1, -1, -1):
    o = obj[y] > 0
    start = o & (gap > 5)                                                       # a new thing starts here (its foot)
    run[start] = y; gap[o] = 0; gap[~o] += 1
    base[y][o] = run[o]
enc = np.where(obj > 0, base + 1, 0).astype(np.uint16)
png = np.dstack([np.zeros((H, W), np.uint8), (enc & 255).astype(np.uint8), (enc >> 8).astype(np.uint8)])   # BGR: R = high, G = low
cv2.imwrite(str(here / "assets/occlusion.png"), png)
print("object share", obj.mean().round(3))
if len(sys.argv) > 1:
    vis = im.copy(); vis[obj > 0] = (0.45 * vis[obj > 0] + 0.55 * np.array([60, 60, 230])).astype(np.uint8)
    cv2.imwrite(sys.argv[1], vis)
