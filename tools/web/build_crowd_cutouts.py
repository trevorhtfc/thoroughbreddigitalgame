"""Crowd option 3, painted cut-outs: flat illustrated racegoers drawn into a texture atlas.

    python3 tools/web/build_crowd_cutouts.py

Writes race-view/assets/architecture/crowd_cutouts.png and crowd_cutouts.json.

32 figures (16 gents, 16 ladies), each a 1 m x 2 m card standing on the ground, drawn from simple
shapes with a painted finish: light from the upper left, a darker edge round each shape, and brush
strokes. Faceless. The race view tints them per person like the 3D figures, so the atlas holds what
each pixel is rather than its colour:

  left half  (R, G, B, A) = shade, trim weight, hat weight, alpha
  right half (R, G, B, A) = skin weight, hair weight, white weight (shirt fronts, gloves, cards), 1
  the coat or dress (the main colour) takes whatever weight is left; shoes are the main colour drawn nearly black.
(The right half keeps full alpha: browsers may clear the colour of fully transparent pixels.)

Drawn at 4x and averaged down, so the edges between colours are soft.
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = os.path.abspath(".")
OUT = os.path.join(REPO, "race-view/assets/architecture")
CW, CH, SS = 128, 256, 4                 # cell size in the atlas, supersampling
COLS, ROWS = 8, 4
W, H = CW * SS, CH * SS                  # drawing size of one cell
PPM = W / 1.0                            # pixels per metre (the card is 1 m wide, 2 m tall)
MAIN, SKIN, HAT, TRIM, HAIR, WHITE, DARK = range(7)


def P(x, y):
    return (W / 2 + x * PPM, H - 0.02 * PPM - y * PPM)


class Cell:
    def __init__(self, seed):
        self.part = Image.new("L", (W, H), 255)            # 255 = empty
        self.shade = np.zeros((H, W), np.float32)
        self.rnd = random.Random(seed)

    def _apply(self, mask_img, part, light=0.0):
        m = np.asarray(mask_img) > 127
        if not m.any():
            return
        ys, xs = np.nonzero(m)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        gx = (np.arange(W)[None, :] - x0) / max(1, x1 - x0)
        gy = (np.arange(H)[:, None] - y0) / max(1, y1 - y0)
        # lit from the upper left; a soft roll-off to the right and down; a little lift for skin and hats
        s = 0.88 - 0.3 * np.clip(gx, 0, 1) ** 1.4 - 0.08 * gy + light
        self.shade[m] = np.broadcast_to(s, (H, W))[m]
        self.part.paste(part, mask=mask_img)

    def poly(self, pts, part, light=0.0):
        mk = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mk).polygon([P(x, y) for x, y in pts], fill=255)
        self._apply(mk, part, light)

    def ell(self, cx, cy, rx, ry, part, light=0.0, rot=0.0):
        n = 28
        pts = []
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = rx * math.cos(a), ry * math.sin(a)
            c, s = math.cos(rot), math.sin(rot)
            pts.append((cx + x * c - y * s, cy + x * s + y * c))
        self.poly(pts, part, light)

    def limb(self, pts, r0, r1, part, light=0.0):
        """A tapered stroke through points (an arm or a leg)."""
        for k in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[k], pts[k + 1]
            dx, dy = bx - ax, by - ay
            l = math.hypot(dx, dy) or 1
            nx, ny = -dy / l, dx / l
            ra = r0 + (r1 - r0) * k / (len(pts) - 1)
            rb = r0 + (r1 - r0) * (k + 1) / (len(pts) - 1)
            self.poly([(ax + nx * ra, ay + ny * ra), (bx + nx * rb, by + ny * rb), (bx - nx * rb, by - ny * rb), (ax - nx * ra, ay - ny * ra)], part, light)
            self.ell(bx, by, rb, rb, part, light)


def wobble(rnd, pts, a=0.006):
    return [(x + rnd.uniform(-a, a), y + rnd.uniform(-a, a)) for x, y in pts]


def hat(c, kind, hx, hy, s=1.0, tilt=0.0, wide=1.0):
    """Hat on a head whose crown is at (hx, hy)."""
    r = c.rnd
    t = math.tan(tilt)
    if kind == "top":
        c.poly([(hx - 0.1 * s, hy - 0.02), (hx + 0.1 * s, hy - 0.02 + 0.2 * t), (hx + 0.108 * s, hy + 0.2 * s + 0.2 * t), (hx - 0.102 * s, hy + 0.2 * s)], HAT, 0.05)
        c.poly([(hx - 0.1 * s, hy + 0.0), (hx + 0.1 * s, hy + 0.0 + 0.2 * t), (hx + 0.1 * s, hy + 0.035 + 0.2 * t), (hx - 0.1 * s, hy + 0.035)], TRIM)
        c.ell(hx, hy - 0.02, 0.17 * s, 0.028, HAT, 0.05, rot=tilt)
    elif kind == "boater":
        c.poly([(hx - 0.105 * s, hy - 0.02), (hx + 0.105 * s, hy - 0.02), (hx + 0.1 * s, hy + 0.065 * s), (hx - 0.1 * s, hy + 0.065 * s)], HAT, 0.1)
        c.poly([(hx - 0.105 * s, hy - 0.0), (hx + 0.105 * s, hy - 0.0), (hx + 0.105 * s, hy + 0.03), (hx - 0.105 * s, hy + 0.03)], TRIM)
        c.ell(hx, hy - 0.02, 0.175 * s, 0.025, HAT, 0.1, rot=tilt)
    elif kind == "bowler":
        c.ell(hx, hy + 0.02, 0.1 * s, 0.1 * s, HAT, 0.05)
        c.ell(hx, hy - 0.015, 0.14 * s, 0.03, HAT, 0.05, rot=tilt)
    elif kind == "panama":
        c.poly([(hx - 0.1 * s, hy - 0.02), (hx + 0.1 * s, hy - 0.02), (hx + 0.085 * s, hy + 0.09 * s), (hx, hy + 0.075 * s), (hx - 0.085 * s, hy + 0.09 * s)], HAT, 0.1)
        c.poly([(hx - 0.1 * s, hy - 0.01), (hx + 0.1 * s, hy - 0.01), (hx + 0.1 * s, hy + 0.02), (hx - 0.1 * s, hy + 0.02)], TRIM)
        c.poly([(hx - 0.17 * s, hy - 0.04), (hx + 0.17 * s, hy - 0.025), (hx + 0.15 * s, hy - 0.0), (hx - 0.15 * s, hy - 0.01)], HAT, 0.1)
    elif kind == "wide":
        c.ell(hx, hy + 0.03, 0.105 * s, 0.07 * s, HAT, 0.08)
        c.poly([(hx - 0.105 * s, hy - 0.0), (hx + 0.105 * s, hy + 0.0), (hx + 0.105 * s, hy + 0.035), (hx - 0.105 * s, hy + 0.035)], TRIM)
        c.ell(hx, hy - 0.02, 0.3 * s * wide, 0.05, HAT, 0.08, rot=tilt)
        if r.random() < 0.5:
            c.ell(hx + 0.09 * s, hy + 0.035, 0.045, 0.04, TRIM, 0.1)               # a flower
    elif kind == "picture":
        c.ell(hx + 0.01, hy - 0.025, 0.36 * s * wide, 0.06, HAT, 0.08, rot=tilt)
        c.ell(hx + 0.01, hy + 0.02, 0.1 * s, 0.06 * s, HAT, 0.12)
        c.ell(hx - 0.11 * s, hy + 0.02, 0.06, 0.035, TRIM, 0.1, rot=0.4)           # a bow
    elif kind == "cloche":
        c.ell(hx, hy - 0.0, 0.118 * s, 0.11 * s, HAT, 0.06)
        c.poly([(hx - 0.13 * s, hy - 0.06), (hx + 0.13 * s, hy - 0.06), (hx + 0.12 * s, hy - 0.025), (hx - 0.12 * s, hy - 0.025)], HAT, 0.0)
        c.poly([(hx - 0.118 * s, hy - 0.03), (hx + 0.118 * s, hy - 0.03), (hx + 0.115 * s, hy + 0.0), (hx - 0.115 * s, hy + 0.0)], TRIM)
    elif kind == "fascinator":
        c.ell(hx + 0.07, hy - 0.0, 0.07, 0.04, HAT, 0.1, rot=0.5)
        c.limb([(hx + 0.08, hy + 0.02), (hx + 0.13, hy + 0.12), (hx + 0.18, hy + 0.2)], 0.012, 0.004, TRIM, 0.1)
        c.limb([(hx + 0.09, hy + 0.02), (hx + 0.17, hy + 0.08), (hx + 0.24, hy + 0.11)], 0.01, 0.003, TRIM, 0.05)


def gent(c, i):
    r = c.rnd
    tails = r.random() < 0.5
    sh = 0.225 + r.uniform(-0.02, 0.02)
    lean = r.uniform(-0.015, 0.015)
    hem = 0.5 if tails else r.uniform(0.66, 0.74)
    # legs and shoes
    for sx in (-1, 1):
        c.poly(wobble(r, [(sx * 0.02, 0.06), (sx * 0.13, 0.06), (sx * 0.135, 0.9), (sx * 0.0, 0.9)]), TRIM)
        c.ell(sx * 0.085 + 0.015, 0.035, 0.075, 0.035, DARK)
    c.poly([(-0.14, 0.82), (0.14, 0.82), (0.15, 1.0), (-0.15, 1.0)], TRIM)
    # coat: shoulders, waist, hem; tails hang behind the legs (seen at the sides)
    if tails:
        for sx in (-1, 1):
            c.poly(wobble(r, [(sx * 0.07, 1.0), (sx * 0.175, 1.0), (sx * 0.16, hem), (sx * 0.1, hem + 0.04)]), MAIN, -0.08)
    body = [(-sh + lean, 1.43), (-0.17, 1.15), (-0.165, 0.98 if tails else 0.95), (-0.17, 0.98 if tails else hem), (0.17, 0.98 if tails else hem), (0.165, 0.95), (0.17, 1.15), (sh + lean, 1.43), (0.08 + lean, 1.5), (-0.08 + lean, 1.5)]
    c.poly(wobble(r, body), MAIN)
    # shirt front and waistcoat: a V, the waistcoat in the second colour
    c.poly([(-0.07 + lean, 1.49), (0.07 + lean, 1.49), (0.0 + lean, 1.08)], TRIM, 0.05)
    c.poly([(-0.04 + lean, 1.49), (0.04 + lean, 1.49), (0.0 + lean, 1.3)], WHITE, 0.1)
    # arms: hanging, one on the hip, or holding a race card
    pose = r.choice(["down", "down", "card", "hip", "pocket"])
    for sx in (-1, 1):
        p = pose if sx == 1 else "down"
        s0 = (sx * (sh - 0.03) + lean, 1.4)
        if p == "down":
            pts = [s0, (sx * 0.235, 1.12), (sx * 0.225, 0.88)]
        elif p == "hip":
            pts = [s0, (sx * 0.33, 1.15), (sx * 0.17, 0.98)]
        elif p == "pocket":
            pts = [s0, (sx * 0.25, 1.12), (sx * 0.17, 0.93)]
        else:
            pts = [s0, (sx * 0.24, 1.12), (sx * 0.1, 1.18)]
        c.limb(pts, 0.052, 0.042, MAIN, -0.04 if sx > 0 else 0.04)
        if p in ("down", "card"):
            c.ell(pts[-1][0], pts[-1][1] - 0.015, 0.024, 0.03, SKIN, 0.1)
        if p == "card":
            c.poly([(pts[-1][0] - 0.07, pts[-1][1] - 0.02), (pts[-1][0] + 0.04, pts[-1][1] - 0.04), (pts[-1][0] + 0.05, pts[-1][1] + 0.1), (pts[-1][0] - 0.06, pts[-1][1] + 0.11)], WHITE, 0.1)
    # neck, head, a little hair at the back of the neck and the ears
    hx = lean + r.uniform(-0.012, 0.012)
    c.poly([(hx - 0.048, 1.46), (hx + 0.048, 1.46), (hx + 0.042, 1.55), (hx - 0.042, 1.55)], SKIN)
    c.ell(hx, 1.635, 0.09, 0.112, SKIN, 0.1)
    c.ell(hx - 0.086, 1.655, 0.018, 0.05, HAIR)
    c.ell(hx + 0.086, 1.655, 0.018, 0.05, HAIR)
    kind = ["top", "top", "top", "boater", "bowler", "panama"][i % 6] if i < 12 else r.choice(["top", "boater", "panama", "bowler"])
    hat(c, kind, hx, 1.715, s=1.0, tilt=r.uniform(-0.08, 0.08))
    return kind


def lady(c, i):
    r = c.rnd
    style = r.choice(["long", "midi", "midi", "flare", "long"])
    lean = r.uniform(-0.015, 0.015)
    hem = {"long": 0.04, "midi": 0.38, "flare": 0.45}[style]
    if hem > 0.1:
        for sx in (-1, 1):
            c.poly(wobble(r, [(sx * 0.03, 0.05), (sx * 0.08, 0.05), (sx * 0.085, hem + 0.05), (sx * 0.025, hem + 0.05)]), SKIN, -0.05)
            c.ell(sx * 0.06, 0.03, 0.05, 0.03, DARK)
    sk = {"long": 0.28, "midi": 0.25, "flare": 0.3}[style]
    skirt = [(-0.12, 0.98), (-sk - r.uniform(0, 0.03), hem), (sk + r.uniform(0, 0.03), hem), (0.12, 0.98)]
    c.poly(wobble(r, skirt, 0.01), MAIN)
    bod = [(-0.115, 0.96), (-0.15, 1.2), (-0.19 + lean, 1.36), (-0.07 + lean, 1.44), (0.07 + lean, 1.44), (0.19 + lean, 1.36), (0.15, 1.2), (0.115, 0.96)]
    c.poly(wobble(r, bod), MAIN, 0.03)
    c.poly([(-0.125, 0.94), (0.125, 0.94), (0.122, 1.01), (-0.122, 1.01)], TRIM, 0.05)       # sash
    pose = r.choice(["down", "down", "bag", "hip", "clasp"])
    for sx in (-1, 1):
        p = pose if sx == -1 else "down"
        s0 = (sx * 0.17 + lean, 1.34)
        if p == "down":
            pts = [s0, (sx * 0.2, 1.1), (sx * 0.18, 0.9)]
        elif p == "hip":
            pts = [s0, (sx * 0.29, 1.12), (sx * 0.13, 1.0)]
        elif p == "clasp":
            pts = [s0, (sx * 0.2, 1.1), (sx * 0.03, 1.02)]
        else:
            pts = [s0, (sx * 0.19, 1.12), (sx * 0.12, 1.06)]
        c.limb(pts, 0.04, 0.032, MAIN if r.random() < 0.6 else SKIN, -0.04 if sx > 0 else 0.04)
        c.ell(pts[-1][0], pts[-1][1] - 0.01, 0.022, 0.028, WHITE if r.random() < 0.4 else SKIN, 0.1)
        if p == "bag":
            c.poly([(pts[-1][0] - 0.07, pts[-1][1] - 0.13), (pts[-1][0] + 0.06, pts[-1][1] - 0.13), (pts[-1][0] + 0.05, pts[-1][1] - 0.03), (pts[-1][0] - 0.06, pts[-1][1] - 0.03)], TRIM, 0.05)
    hx = lean + r.uniform(-0.015, 0.015)
    c.poly([(hx - 0.038, 1.4), (hx + 0.038, 1.4), (hx + 0.035, 1.5), (hx - 0.035, 1.5)], SKIN)
    hy = 1.575
    hair = r.choice(["bob", "bun", "long", "bob"])
    if hair == "long":
        c.poly(wobble(r, [(hx - 0.1, hy + 0.08), (hx + 0.1, hy + 0.08), (hx + 0.12, 1.42), (hx - 0.12, 1.42)]), HAIR, -0.05)
    elif hair == "bob":
        c.ell(hx, hy, 0.1, 0.1, HAIR, -0.05)
    c.ell(hx, hy, 0.082, 0.105, SKIN, 0.1)
    if hair == "bun":
        c.ell(hx - 0.07, hy, 0.04, 0.05, HAIR)
    elif hair != "long":
        c.ell(hx - 0.075, hy + 0.02, 0.03, 0.06, HAIR)
        c.ell(hx + 0.075, hy + 0.02, 0.03, 0.06, HAIR)
    kind = ["wide", "picture", "fascinator", "cloche", "wide", "boater"][i % 6] if i < 12 else r.choice(["wide", "picture", "fascinator", "wide"])
    hat(c, kind, hx, hy + 0.08, s=0.95, tilt=r.uniform(-0.15, 0.15), wide=r.uniform(0.85, 1.2))
    return kind


def brush(seed):
    """Brush strokes: short, mostly upright dabs, light and dark, as a 0..1 field (0.5 = none)."""
    rnd = random.Random(seed)
    im = Image.new("L", (W, H), 128)
    d = ImageDraw.Draw(im)
    for _ in range(900):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        a = math.pi / 2 + rnd.uniform(-0.6, 0.6) + (0.9 if rnd.random() < 0.3 else 0)
        l = rnd.uniform(18, 60)
        v = int(128 + rnd.choice((-1, 1)) * rnd.uniform(18, 50))
        d.line([(x, y), (x + math.cos(a) * l, y - math.sin(a) * l)], fill=v, width=int(rnd.uniform(6, 14)))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255.0


atlas = np.zeros((CH * ROWS, CW * COLS * 2, 4), np.float32)
info = []
for idx in range(COLS * ROWS):
    is_lady = idx % 2 == 1
    c = Cell(100 + idx)
    kind = lady(c, idx // 2) if is_lady else gent(c, idx // 2)
    part = np.asarray(c.part).astype(np.int16)
    alpha = (part != 255).astype(np.float32)
    # a darker edge round every shape: where the part changes within a few pixels
    pi = Image.fromarray(part.astype(np.uint8))
    edge = (np.asarray(pi.filter(ImageFilter.MaxFilter(7))) != np.asarray(pi.filter(ImageFilter.MinFilter(7)))).astype(np.float32)
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255.0
    shade = c.shade * (1.0 + 0.42 * (brush(idx) - 0.5) * 2 * 0.5) * (1.0 - 0.38 * edge)
    shade = np.where(part == DARK, 0.16, shade)               # shoes: the main colour, nearly black
    shade = np.clip(shade, 0, 1) * alpha
    chans = [shade, (part == TRIM), (part == HAT), alpha, (part == SKIN), (part == HAIR), (part == WHITE), np.ones_like(alpha)]
    chans = [np.asarray(ch, np.float32) for ch in chans]
    # average down 4x
    small = [ch.reshape(CH, SS, CW, SS).mean(axis=(1, 3)) for ch in chans]
    # shade is averaged over covered pixels only (so the edge doesn't go dark), weights stay as coverage
    a_s = small[3]
    small[0] = np.where(a_s > 0, small[0] / np.maximum(a_s, 1e-4), 0)
    for k in (1, 2, 4, 5, 6):
        small[k] = np.where(a_s > 0, small[k] / np.maximum(a_s, 1e-4), 0)
    cx, cy = idx % COLS, idx // COLS
    ys, xs = slice(cy * CH, (cy + 1) * CH), slice(cx * CW, (cx + 1) * CW)
    atlas[ys, xs, :] = np.stack(small[:4], -1)
    atlas[ys, slice(COLS * CW + cx * CW, COLS * CW + (cx + 1) * CW), :] = np.stack(small[4:], -1)
    info.append({"cell": [cx, cy], "lady": is_lady, "hat": kind})

os.makedirs(OUT, exist_ok=True)
Image.fromarray((np.clip(atlas, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(os.path.join(OUT, "crowd_cutouts.png"), optimize=True)
json.dump({"_about": "Painted cut-out racegoers (tools/web/build_crowd_cutouts.py). Atlas: left half shade/trim/hat/alpha, right half skin/hair/white weights (alpha 1); main colour = the rest. Each card is 1 m wide and 2 m tall, its bottom edge on the ground.",
           "cols": COLS, "rows": ROWS, "card": [1.0, 2.0], "figures": info}, open(os.path.join(OUT, "crowd_cutouts.json"), "w"), indent=1)
print("wrote atlas", atlas.shape, sum(1 for f in info if f["lady"]), "ladies")
