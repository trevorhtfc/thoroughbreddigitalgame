"""Prepares the home-map base from the owner's clean board (markup/clean-map.jpg, 1448 x 1086):
- mends the right-hand frame where it is missing,
- paints out the place names the buttons replace and the crossed-out upper National Stud label,
- paints out the painted horses the owner circled (the Gallops, Warren Hill, the lone horse bottom left),
  which are replaced by moving ones.
Writes assets/newmarket-board.webp, and a before/after sheet when given a path."""
import cv2, numpy as np, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
im = cv2.imread(str(here / "markup/clean-map.jpg")); out = im.copy()
H, W = im.shape[:2]

# 1. the frame: copy an intact stretch of the right-hand border over the gap, feathered into the grass
src = im[600:890, 1418:W].astype(np.float32); dst_y = 288
alpha = np.clip((np.arange(W - 1418) - 2) / 10, 0, 1)[None, :, None]
region = out[dst_y:dst_y + 290, 1418:W].astype(np.float32)
out[dst_y:dst_y + 290, 1418:W] = (region * (1 - alpha) + src * alpha).astype(np.uint8)

# 2. lettering and 3. horses: dark marks inside each box, filled from what's around them
LABELS = {"warren": (92, 466, 238, 510), "palace": (382, 664, 490, 686), "jockey": (594, 666, 722, 694),
          "tatts": (884, 738, 1008, 762), "stables": (918, 896, 1008, 922), "stud": (1286, 466, 1402, 520),
          "stud-upper": (1210, 197, 1308, 236)}
HORSES = [(130, 210), (215, 183), (262, 146), (267, 218), (430, 110), (503, 88), (513, 145),       # the Gallops
          (25, 370), (78, 382), (137, 400), (235, 432),                                             # Warren Hill
          (135, 785)]                                                                                # bottom left
lum = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
mask = np.zeros((H, W), np.uint8)
def mark(x0, y0, x1, y1, drop, grow):
    sub = lum[y0:y1, x0:x1]; m = (sub < np.median(sub) - drop).astype(np.uint8) * 255
    mask[y0:y1, x0:x1] |= cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=grow)
for (x0, y0, x1, y1) in LABELS.values(): mark(x0, y0, x1, y1, 30, 2)
for (x, y) in HORSES: mark(x - 22, y - 20, x + 22, y + 18, 26, 3)
filled = cv2.inpaint(out, mask, 5, cv2.INPAINT_TELEA)
grain = np.random.default_rng(5).normal(0, 5, out.shape).astype(np.float32)
soft = cv2.GaussianBlur(mask, (0, 0), 1.5).astype(np.float32)[..., None] / 255
out = np.clip(filled.astype(np.float32) + grain * soft, 0, 255).astype(np.uint8)
cv2.imwrite(str(here / "assets/newmarket-board.webp"), out, [cv2.IMWRITE_WEBP_QUALITY, 92])

if len(sys.argv) > 1:
    boxes = list(LABELS.values()) + [(x - 30, y - 26, x + 30, y + 24) for x, y in HORSES] + [(1380, 260, 1448, 600)]
    tiles = []
    for (x0, y0, x1, y1) in boxes:
        x0, y0 = max(0, x0 - 8), max(0, y0 - 8); x1, y1 = min(W, x1 + 8), min(H, y1 + 8)
        t = np.hstack([im[y0:y1, x0:x1], np.full((y1 - y0, 4, 3), 40, np.uint8), out[y0:y1, x0:x1]])
        k = 2 if (y1 - y0) < 200 else 1
        tiles.append(cv2.resize(t, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC))
    # lay out in rows
    rows, row, rw = [], [], 0
    for t in tiles:
        if rw + t.shape[1] > 1400 and row: rows.append(row); row, rw = [], 0
        row.append(t); rw += t.shape[1] + 6
    rows.append(row)
    def hrow(r):
        h = max(t.shape[0] for t in r)
        return np.hstack([np.vstack([t, np.full((h - t.shape[0], t.shape[1], 3), 30, np.uint8)]) for t in sum([[t, np.full((h, 6, 3), 30, np.uint8)] for t in r], [])])
    R = [hrow(r) for r in rows]; Wm = max(r.shape[1] for r in R)
    cv2.imwrite(sys.argv[1], np.vstack([np.hstack([r, np.full((r.shape[0], Wm - r.shape[1], 3), 30, np.uint8)]) for r in R]))
