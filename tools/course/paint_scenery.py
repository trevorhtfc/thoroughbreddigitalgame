"""Paint the course's illustrated textures: turf with soft lane shading, the grass
beyond the rails, a gravel path and a set of painted trees.

    python tools/course/paint_scenery.py assets/course/textures

Everything is plain PNG, so any engine (web, Godot, Unreal) can use it.

- turf.png      one tile of the racing turf. Across the image (v) = the full
                width of the track; along it (u) = TURF_TILE_M metres of
                running, tiling seamlessly end to end. Soft lighter and darker
                lanes run the length of the track, with brushy grain.
- grass.png     the grass beyond the rails, tiles both ways.
- path.png      sandy gravel, tiles both ways.
- trees.png     an atlas of painted trees (4 across), RGBA, for upright cut-outs.
                Light comes from the upper left, matching the scene's sun.
- treeline.png  a continuous strip of woodland (tiles left to right), RGBA, for the
                tree lines behind the course; treeline_far.png is the same in haze.
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import gaussian_filter

OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/course/textures"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)

LANES = 8   # lanes across the track (must match the course file's "lanes")


def periodic_noise(h, w, scale, seed):
    """Smooth noise that tiles both ways (filtered in frequency space)."""
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal((h, w)))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    k = np.sqrt(fx ** 2 + fy ** 2)
    f *= np.exp(-(k / scale) ** 2)
    n = np.real(np.fft.ifft2(f))
    return (n - n.mean()) / (n.std() + 1e-9)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def strokes(img, n, colours, length, width, angle, angle_jit, alpha, seed, wrap=True):
    """Short painted brush strokes, drawn wrapped so the tile stays seamless."""
    r = np.random.default_rng(seed)
    W, H = img.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y = r.uniform(0, W), r.uniform(0, H)
        a = angle + r.normal(0, angle_jit)
        L = length * r.uniform(0.6, 1.4)
        c = colours[r.integers(len(colours))]
        col = tuple(int(v) for v in np.clip(c + r.normal(0, 6, 3), 0, 255)) + (int(alpha * r.uniform(0.5, 1.0)),)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        for ox in ((-W, 0, W) if wrap else (0,)):
            for oy in ((-H, 0, H) if wrap else (0,)):
                d.line([(x - dx + ox, y - dy + oy), (x + dx + ox, y + dy + oy)], fill=col, width=max(1, int(width * r.uniform(0.7, 1.3))))
    img.alpha_composite(layer)


def to_img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ---------- Turf ----------
def turf(size=2048):
    H = W = size
    base = hexrgb("#54863c")
    v = (np.arange(H)[:, None] + 0.5) / H                      # 0..1 across the track
    lane = np.floor(v * LANES)
    # Soft lanes: alternate lighter/darker with gently blended edges, and a little
    # unevenness along each lane so they read as mown, not ruled.
    # A smooth wave across the track: one light and one dark lane per pair, blended softly.
    wave = np.cos((v * LANES) * math.pi)
    wave = np.sign(wave) * np.abs(wave) ** 0.6
    wobble = periodic_noise(H, W, 6, 1) * 0.2
    lane_shade = wave * (1 + wobble) * 0.055                   # +/- 5.5 % brightness
    big = periodic_noise(H, W, 4, 2) * 0.05                    # broad patches
    fine = periodic_noise(H, W, 90, 3) * 0.035                 # grain
    shade = 1 + lane_shade + big + fine
    warm = np.stack([1.03 + big * 0.3, 1.0 + 0 * big, 0.92 - big * 0.2], -1)
    a = base * shade[..., None] * warm
    img = to_img(a)
    light, mid, dark = hexrgb("#70a04c"), hexrgb("#52843a"), hexrgb("#3e6c34")
    # Brush grain runs with the direction of running (along u).
    strokes(img, 14000, [light, mid, dark], 20, 2, 0.0, 0.10, 50, 4)
    strokes(img, 1800, [hexrgb("#8cb460"), hexrgb("#a6b86a")], 14, 1, 0.0, 0.2, 45, 5)
    img = img.filter(ImageFilter.GaussianBlur(0.45))
    return img.convert("RGB")


def grass(size=1024):
    base = hexrgb("#54823a")
    big = periodic_noise(size, size, 3, 11) * 0.04
    mid = periodic_noise(size, size, 14, 12) * 0.03
    fine = periodic_noise(size, size, 120, 13) * 0.04
    shade = 1 + big + mid + fine
    warm = np.stack([1.0 + big * 0.4, 1.0 + 0 * big, 0.9 + 0 * big], -1)
    img = to_img(base * shade[..., None] * warm)
    strokes(img, 7000, [hexrgb("#78a650"), hexrgb("#55833a"), hexrgb("#8aae5a")], 12, 2, -0.6, 0.6, 45, 14)
    return img.filter(ImageFilter.GaussianBlur(0.7)).convert("RGB")


def path(size=512):
    base = hexrgb("#cdb48a")
    n = 1 + periodic_noise(size, size, 10, 21) * 0.06 + periodic_noise(size, size, 120, 22) * 0.08
    img = to_img(base * n[..., None])
    strokes(img, 2500, [hexrgb("#b89c72"), hexrgb("#e2cfa6"), hexrgb("#a68a62")], 5, 2, 0, 3.0, 90, 23)
    return img.filter(ImageFilter.GaussianBlur(0.5)).convert("RGB")


# ---------- Trees ----------
# Painted like the board's woodland: big masses of deep green, each a dark base with a
# mid-tone and a light side towards the sun (upper left), a little leafy texture and a
# broken edge. Few, large shapes rather than thousands of dots.
def _blur(a, sigma):
    return gaussian_filter(a, sigma, mode="nearest")


GREENS = {
    "shadow": (30, 52, 34), "dark": (42, 72, 40), "mid": (62, 98, 48),
    "light": (98, 132, 62), "high": (148, 168, 88), "bark": (58, 46, 36), "bark_lit": (96, 80, 60),
}


def _blob(d, x, y, rx, ry, col, r, wobble=0.14, pts=30, wrap=0):
    """A slightly irregular painted blob; drawn again at +-wrap so strips tile."""
    k = r.uniform(0, 6.28)
    poly = []
    for i in range(pts):
        t = 2 * math.pi * i / pts
        f = 1 + wobble * (math.sin(3 * t + k) * 0.6 + math.sin(7 * t + 2 * k) * 0.25 + r.uniform(-0.15, 0.15))
        poly.append((x + math.cos(t) * rx * f, y + math.sin(t) * ry * f))
    for ox in ((-wrap, 0, wrap) if wrap else (0,)):
        d.polygon([(px + ox, py) for px, py in poly], fill=col)


def _tint(c, r, haze=0.0, jitter=6, hue=(0, 0, 0)):
    c = np.array(c, float) + np.array(hue) + r.normal(0, jitter, 3)
    c = c * (1 - haze) + np.array([196, 200, 176]) * haze      # distance haze towards the sky
    return tuple(int(v) for v in np.clip(c, 0, 255)) + (255,)


def _crown(d, r, cx, base_y, R, haze=0.0, wrap=0, lobes=9, flat=1.0, poplar=False):
    """One tree crown: centre cx, bottom of crown at base_y, radius R (pixels, y down)."""
    hue = r.normal(0, 5, 3) * np.array([1.0, 0.8, 0.5])
    L = []
    for i in range(lobes):
        if poplar:
            t = i / max(1, lobes - 1)
            L.append((cx + r.uniform(-0.15, 0.15) * R, base_y - R * flat * (0.35 + 1.0 * t), R * r.uniform(0.7, 0.85) * (1.1 - 0.45 * t)))
        else:
            a = r.uniform(-math.pi, 0)                 # upper half spread
            L.append((cx + math.cos(a) * R * 0.55 * r.uniform(0.3, 1.0),
                      base_y - R * flat + math.sin(a) * R * 0.5 * flat * r.uniform(0.2, 1.0), R * r.uniform(0.4, 0.62)))
    if not poplar:
        L.append((cx, base_y - R * 0.55 * flat, R * 0.66))
    L.sort(key=lambda l: -l[1])                    # lower lobes first
    for x, y, rr in L:                             # dark mass with a softly broken edge
        _blob(d, x, y, rr, rr * 0.92, _tint(GREENS["dark"], r, haze, 3, hue), r, wrap=wrap)
        for _ in range(9):
            a = r.uniform(-math.pi * 1.1, 0.1)
            _blob(d, x + math.cos(a) * rr * 0.92, y + math.sin(a) * rr * 0.88, rr * 0.16, rr * 0.14,
                  _tint(GREENS["dark"], r, haze, 3, hue), r, 0.25, 16, wrap)
    for x, y, rr in L:                             # shadowed underside
        _blob(d, x + rr * 0.1, y + rr * 0.4, rr * 0.8, rr * 0.42, _tint(GREENS["shadow"], r, haze, 2, hue), r, wrap=wrap)
    for x, y, rr in sorted(L, key=lambda l: l[1], reverse=True):
        mx, my = x - rr * 0.14, y - rr * 0.18
        _blob(d, mx, my, rr * 0.74, rr * 0.62, _tint(GREENS["mid"], r, haze, 4, hue), r, wrap=wrap)
        for _ in range(22):                        # quiet leafy texture, close in tone
            a, q = r.uniform(0, 6.28), r.uniform(0, 0.75)
            base = GREENS["mid"] if r.random() < 0.7 else GREENS["dark"]
            c = np.array(base) * 0.5 + np.array(GREENS["mid"]) * 0.5
            _blob(d, mx + math.cos(a) * rr * q, my + math.sin(a) * rr * q * 0.8,
                  rr * 0.09, rr * 0.075, _tint(c, r, haze, 4, hue), r, 0.25, 14, wrap)
        _blob(d, x - rr * 0.32, y - rr * 0.36, rr * 0.42, rr * 0.32, _tint(GREENS["light"], r, haze, 4, hue), r, wrap=wrap)
        for _ in range(10):                        # sunlit leaf clusters on the upper left
            a = r.uniform(-math.pi * 0.95, -math.pi * 0.35)
            q = r.uniform(0.35, 0.65)
            c = GREENS["light"] if r.random() < 0.75 else GREENS["high"]
            _blob(d, x - rr * 0.2 + math.cos(a) * rr * q, y - rr * 0.12 + math.sin(a) * rr * q,
                  rr * 0.09, rr * 0.075, _tint(c, r, haze, 5, hue), r, 0.25, 14, wrap)


def _finish(img, size):
    """Scale down for soft edges, then bleed colour under transparent pixels (no dark halos when mip-mapped)."""
    rgb = img.convert("RGB").filter(ImageFilter.GaussianBlur(1.6))     # soft gouache edges between tones
    soft = Image.merge("RGBA", (*rgb.split(), img.split()[3].filter(ImageFilter.GaussianBlur(0.8))))
    out = soft.resize(size, Image.LANCZOS)
    arr = np.array(out).astype(float)
    A = arr[..., 3] / 255
    fill = np.dstack([_blur(arr[..., i] * A, 8) / np.maximum(_blur(A, 8), 1e-3) for i in range(3)])
    m = A[..., None]
    arr[..., :3] = arr[..., :3] * np.where(m > 0, 1, 0) + np.clip(fill, 0, 255) * np.where(m > 0, 0, 1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def tree(size=512, seed=0, kind="oak"):
    """One painted tree for the clumps near the course, standing on the bottom edge."""
    r = np.random.default_rng(seed)
    S = size * 2
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ground = S * 0.985
    R = S * {"oak": 0.36, "wide": 0.40, "poplar": 0.22, "round": 0.33}[kind]
    flat = {"oak": 1.0, "wide": 0.8, "poplar": 2.1, "round": 1.05}[kind]
    crown_base = ground - S * {"oak": 0.30, "wide": 0.30, "poplar": 0.16, "round": 0.26}[kind]
    tw = S * 0.028
    # Trunk and a couple of limbs into the crown, lit on the left.
    cx = S / 2
    d.polygon([(cx - tw * 1.5, ground), (cx + tw * 1.4, ground), (cx + tw * 0.8, crown_base - R * 0.4), (cx - tw * 0.8, crown_base - R * 0.4)], fill=GREENS["bark"] + (255,))
    d.polygon([(cx - tw * 1.5, ground), (cx - tw * 0.2, ground), (cx - tw * 0.1, crown_base - R * 0.4), (cx - tw * 0.8, crown_base - R * 0.4)], fill=GREENS["bark_lit"] + (255,))
    for sx in (-1, 1):
        d.line([(cx, crown_base + R * 0.05), (cx + sx * R * 0.45, crown_base - R * 0.45)], fill=GREENS["bark"] + (255,), width=int(tw * 0.8))
    _crown(d, r, cx, crown_base + R * 0.15 * flat, R, lobes=10 if kind != "poplar" else 8, flat=flat, poplar=kind == "poplar")
    return _finish(img, (size, size))


def treeline(width=4096, height=640, seed=0, haze=0.0):
    """A continuous strip of woodland, tiling left to right: back crowns, front crowns,
    then a shadowy under-storey with a few trunks where it meets the ground."""
    r = np.random.default_rng(seed)
    W, H = width * 2, height * 2
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ground = H * 0.99
    # Under-storey: a dark band the crowns sit on.
    x = 0
    while x < W:
        w = r.uniform(0.04, 0.08) * H
        _blob(d, x, ground - H * 0.14, w * 1.6, H * 0.16, _tint(GREENS["shadow"], r, haze, 4), r, 0.25, 14, W)
        x += w
    d.rectangle([0, ground - H * 0.12, W, H], fill=_tint(GREENS["shadow"], r, haze, 0))
    for row, (hmin, hmax, rmin, rmax, step) in enumerate([(0.70, 0.92, 0.22, 0.30, 0.20), (0.55, 0.78, 0.20, 0.27, 0.17), (0.38, 0.55, 0.16, 0.22, 0.15)]):
        x = r.uniform(0, H * 0.1)
        while x < W:
            R = H * r.uniform(rmin, rmax)
            top = H * r.uniform(hmin, hmax)                       # height of this tree's top
            base = ground - top + R * 1.9
            _crown(d, r, x, base, R, haze + 0.05 * (2 - row), W, lobes=9)
            x += H * step * r.uniform(0.7, 1.3)
    # A few trunks showing under the front crowns.
    for _ in range(int(W / H * 2.2)):
        tx, tw = r.uniform(0, W), H * r.uniform(0.008, 0.014)
        for ox in (-W, 0, W):
            d.polygon([(tx + ox - tw, ground), (tx + ox + tw, ground), (tx + ox + tw * 0.7, ground - H * r.uniform(0.12, 0.2)), (tx + ox - tw * 0.7, ground - H * 0.2)],
                      fill=_tint(GREENS["bark"], r, haze + 0.1, 4))
    return _finish(img, (width, height))


if __name__ == "__main__":
    turf().save(os.path.join(OUT, "turf.png"), optimize=True)
    grass().save(os.path.join(OUT, "grass.png"), optimize=True)
    path().save(os.path.join(OUT, "path.png"), optimize=True)
    kinds = ["oak", "wide", "round", "poplar"]
    atlas = Image.new("RGBA", (512 * 4, 512), (0, 0, 0, 0))
    for i, k in enumerate(kinds):
        atlas.paste(tree(512, seed=31 + i, kind=k), (512 * i, 0))
    atlas.save(os.path.join(OUT, "trees.png"), optimize=True)
    treeline(seed=41).save(os.path.join(OUT, "treeline.png"), optimize=True)
    treeline(seed=42, haze=0.28).save(os.path.join(OUT, "treeline_far.png"), optimize=True)
    print("wrote", sorted(os.listdir(OUT)))
