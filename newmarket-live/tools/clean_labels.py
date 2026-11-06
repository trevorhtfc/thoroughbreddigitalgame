"""Paints the six place names out of the board (the buttons replace them): dark lettering inside each box is
masked and filled from the surrounding grass. Writes assets/newmarket-board.webp and a check crop."""
import cv2, numpy as np, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
im = cv2.imread(str(here.parent / "assets/maps/newmarket-map.webp"))
BOXES = {"warren": (72, 383, 200, 428), "palace": (312, 548, 412, 569), "jockey": (488, 544, 603, 570),
         "tatts": (674, 603, 838, 630), "stables": (758, 736, 838, 760), "stud": (1058, 386, 1168, 434)}
mask = np.zeros(im.shape[:2], np.uint8)
lum = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
for k, (x0, y0, x1, y1) in BOXES.items():
    sub = lum[y0:y1, x0:x1]
    m = (sub < np.percentile(sub, 70) - 28).astype(np.uint8) * 255      # the lettering: clearly darker than the ground around it
    mask[y0:y1, x0:x1] = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
out = cv2.inpaint(im, mask, 4, cv2.INPAINT_TELEA)
# a touch of the board's own grain back over the filled letters, so they don't read as smooth patches
noise = np.random.default_rng(3).normal(0, 5, im.shape).astype(np.float32)
soft = cv2.GaussianBlur(mask, (0, 0), 1.2).astype(np.float32)[..., None] / 255
out = np.clip(out.astype(np.float32) + noise * soft, 0, 255).astype(np.uint8)
cv2.imwrite(str(here / "assets/newmarket-board.webp"), out, [cv2.IMWRITE_WEBP_QUALITY, 92])
if len(sys.argv) > 1:
    tiles = []
    for k, (x0, y0, x1, y1) in BOXES.items():
        a = im[y0 - 12:y1 + 12, x0 - 12:x1 + 12]; b = out[y0 - 12:y1 + 12, x0 - 12:x1 + 12]
        t = np.hstack([a, b]); t = cv2.resize(t, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
        tiles.append(cv2.copyMakeBorder(t, 4, 4, 4, 4, cv2.BORDER_CONSTANT, value=(40, 40, 40)))
    W = max(t.shape[1] for t in tiles)
    cv2.imwrite(sys.argv[1], np.vstack([cv2.copyMakeBorder(t, 0, 0, 0, W - t.shape[1], cv2.BORDER_CONSTANT) for t in tiles]))
