"""Prepares the home-map base from the owner's clean board (markup/clean-map.jpg, 1448 x 1086):
- mends the right-hand frame where it is missing,
- paints out the place names the buttons replace and the crossed-out upper National Stud label,
- paints out the painted horses the owner circled (the Gallops, Warren Hill, the lone horse bottom left),
  which are replaced by moving ones.
Writes assets/newmarket-board.webp, and a before/after sheet when given a path.

With --game it goes on to paint out every other painted horse (the paddocks, the yards, the hack below Palace House:
owner, 14 Nov: "there shouldn't really be any still horses"), which the game replaces with moving ones (js/life.js),
and writes the game's board, game/assets/newmarket/newmarket-board.webp, leaving the living map's own board as it was.
  python3 newmarket-live/tools/clean_board.py --game [sheet.jpg]"""
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
GAME = "--game" in sys.argv
args = [a for a in sys.argv[1:] if a != "--game"]
if not GAME: cv2.imwrite(str(here / "assets/newmarket-board.webp"), out, [cv2.IMWRITE_WEBP_QUALITY, 92])

# 4. (the game's board only) the still horses. Each is found by its chestnut coat near the point given, with whatever
# dark is joined to it (legs, rider, shadow, a lad at its head); a clean patch of the same ground from close by is
# then laid over it, blended at the edges (Poisson cloning), so the grass or the yard's sand carries on unbroken.
STILL = [(716, 98), (756, 102), (802, 89), (845, 72), (862, 94), (816, 122), (938, 165), (876, 190), (1008, 127),   # the paddocks
         (1237, 174), (1320, 203), (1223, 303), (1010, 437), (1308, 445), (1294, 574), (948, 460), (1079, 399),
         (808, 562), (821, 570), (834, 571), (841, 563), (845, 578), (771, 635), (870, 720),                          # Tattersalls
         (896, 830), (925, 835), (838, 857), (963, 856), (793, 891), (731, 896), (1294, 837),                        # the stable yards
         (240, 703)]                                                                                                 # below Palace House
TOP = {(1294, 837): 829, (896, 830): 822, (925, 835): 827}
def still_horses(img):
    f = img.astype(np.float32); b, g, r = f[..., 0], f[..., 1], f[..., 2]
    lum2 = 0.114 * b + 0.587 * g + 0.299 * r
    med = cv2.medianBlur(img, 41).astype(np.float32); medl = 0.114 * med[..., 0] + 0.587 * med[..., 1] + 0.299 * med[..., 2]
    brown = ((r - b > 34) & (r > g + 6) & (lum2 < medl - 22)).astype(np.uint8)
    dark = (lum2 < medl - 16).astype(np.uint8)
    faint = (cv2.GaussianBlur(lum2, (0, 0), 1.2) < medl - 6).astype(np.uint8)                  # the soft shadow on the ground
    n, lab = cv2.connectedComponents(dark, connectivity=8)
    nf, labf = cv2.connectedComponents(faint, connectivity=8)
    total = np.zeros(img.shape[:2], np.uint8); res = f.copy(); boxes = []
    for (x, y) in STILL:
        m = np.zeros_like(total); x0, y0, x1, y1 = x - 13, y - 12, x + 13, y + 12
        seed = np.zeros_like(total); sub = brown[y0:y1, x0:x1]
        nb, labb = cv2.connectedComponents(sub, connectivity=8)                                 # the coat nearest the point given:
        if nb > 1:                                                                              # not the next horse's, nor a brick wall
            yy, xx = np.nonzero(labb); d2 = (xx - 13) ** 2 + (yy - 12) ** 2; k = d2.argmin()
            if d2[k] <= 64: seed[y0:y1, x0:x1] = (labb == labb[yy[k], xx[k]])
        if not seed.any(): seed[y - 5:y + 5, x - 6:x + 6] = dark[y - 5:y + 5, x - 6:x + 6]      # the faded grey horse by the fence
        ids = np.unique(lab[cv2.dilate(seed, np.ones((5, 5), np.uint8)) > 0]); ids = ids[ids > 0]
        m[np.isin(lab, ids)] = 1
        near = cv2.dilate(seed, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 15)))        # never far from the coat itself:
        m &= near                                                                               # a tree's shadow or a doorway may touch it
        if m.sum() < 12: print("nothing found at", (x, y)); continue
        ids = np.unique(labf[m > 0]); ids = ids[ids > 0]; sh = np.isin(labf, ids).astype(np.uint8)
        sh &= cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 7)))
        one = cv2.dilate(m | sh, np.ones((5, 5), np.uint8))
        if (x, y) in TOP: one[:TOP[(x, y)]] = 0                                                 # a horse at a stable door: the wall stays
        total |= one
    # one clean patch per horse (or per huddle of horses): the nearest stretch of the same ground with nothing standing
    # on it, its colour shifted to the ground's own here, laid in with a soft edge
    busy = (lum2 < medl - 26).astype(np.uint8)                      # trees, fences, people, walls: not to be copied
    n2, lab2, stats, _ = cv2.connectedComponentsWithStats(total, connectivity=8)
    for i in range(1, n2):
        x, y, w, h, _a = stats[i]; pad = 6; x0, y0, x1, y1 = x - pad, y - pad, x + w + pad, y + h + pad
        mk = (lab2[y0:y1, x0:x1] == i).astype(np.uint8); on = cv2.dilate(mk, np.ones((5, 5), np.uint8)) > 0
        want = med[y0:y1, x0:x1][on].mean(0); best = None
        for tol in (0.0, 0.006):                                    # a spotless patch of the same ground
            for dy in range(-90, 91, 2):
                for dx in range(-120, 121, 2):
                    sx0, sy0 = x0 + dx, y0 + dy
                    if sx0 < 4 or sy0 < 4 or sx0 + (x1 - x0) > W - 4 or sy0 + (y1 - y0) > H - 4: continue
                    sl = (slice(sy0, sy0 + (y1 - y0)), slice(sx0, sx0 + (x1 - x0)))
                    if total[sl][on].any(): continue
                    bz = busy[sl][on].mean()
                    if bz > tol: continue
                    dm = np.abs(med[sl][on].mean(0) - want).sum()
                    if dm > 30: continue                            # the same ground: grass for grass, sand for sand
                    cost = dm + 0.15 * np.hypot(dx, dy) + 300 * bz
                    if best is None or cost < best[0]: best = (cost, sx0, sy0)
            if best is not None: break
        al = cv2.GaussianBlur(cv2.dilate(mk, np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), 1.6)[..., None]
        if best is None:                                            # hemmed in (a yard full of people, a wall): filled from its edges
            big = (slice(y0 - 8, y1 + 8), slice(x0 - 8, x1 + 8)); mk2 = np.zeros((y1 - y0 + 16, x1 - x0 + 16), np.uint8); mk2[8:-8, 8:-8] = cv2.dilate(mk, np.ones((3, 3), np.uint8))
            fill = cv2.inpaint(np.clip(res[big], 0, 255).astype(np.uint8), mk2 * 255, 4, cv2.INPAINT_TELEA).astype(np.float32)[8:-8, 8:-8]
            patch = fill + np.random.default_rng(int(x) * 7 + int(y)).normal(0, 3.5, fill.shape).astype(np.float32)
        else:
            _c, sx0, sy0 = best; sl = (slice(sy0, sy0 + (y1 - y0)), slice(sx0, sx0 + (x1 - x0)))
            patch = f[sl] - med[sl] + med[y0:y1, x0:x1]
        res[y0:y1, x0:x1] = res[y0:y1, x0:x1] * (1 - al) + patch * al
        boxes.append((x0, y0, x1, y1))
    return np.clip(res, 0, 255).astype(np.uint8), boxes, total
if GAME:
    out, still_boxes, gone = still_horses(out)
    cv2.imwrite(str(here.parent / "game/assets/newmarket/newmarket-board.webp"), out, [cv2.IMWRITE_WEBP_QUALITY, 92])
    # the painted horses also stood in the hide-behind map (assets/occlusion.png, tools/occlusion.py), where they would
    # go on hiding whatever walks behind the place they stood: they come out of the game's copy of it too
    occ = cv2.imread(str(here / "assets/occlusion.png"), cv2.IMREAD_UNCHANGED)
    occ[cv2.dilate(gone, np.ones((5, 5), np.uint8)) > 0] = 0
    cv2.imwrite(str(here.parent / "game/assets/newmarket/occlusion.png"), occ)
sys.argv = [sys.argv[0]] + args

if len(sys.argv) > 1:
    boxes = list(LABELS.values()) + [(x - 30, y - 26, x + 30, y + 24) for x, y in HORSES] + [(1380, 260, 1448, 600)]
    if GAME: boxes = [(x0 - 14, y0 - 12, x1 + 14, y1 + 12) for (x0, y0, x1, y1) in still_boxes]
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
