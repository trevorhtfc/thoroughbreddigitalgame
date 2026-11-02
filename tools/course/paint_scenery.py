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
def turf(size=1024):
    H = W = size
    base = hexrgb("#5f9443")
    v = (np.arange(H)[:, None] + 0.5) / H                      # 0..1 across the track
    lane = np.floor(v * LANES)
    # Soft lanes: alternate lighter/darker with gently blended edges, and a little
    # unevenness along each lane so they read as mown, not ruled.
    phase = np.sin((v * LANES) * math.pi) ** 2                 # 0 at lane edges, 1 mid-lane
    alt = np.where(lane % 2 == 0, 1.0, -1.0)
    edge_soft = 0.55 + 0.45 * phase
    wobble = periodic_noise(H, W, 6, 1) * 0.25
    lane_shade = alt * edge_soft * (1 + wobble) * 0.05         # +/- 5 % brightness
    big = periodic_noise(H, W, 4, 2) * 0.05                    # broad patches
    fine = periodic_noise(H, W, 90, 3) * 0.035                 # grain
    shade = 1 + lane_shade + big + fine
    warm = np.stack([1.03 + big * 0.3, 1.0 + 0 * big, 0.92 - big * 0.2], -1)
    a = base * shade[..., None] * warm
    img = to_img(a)
    light, mid, dark = hexrgb("#7dae55"), hexrgb("#5b8f3f"), hexrgb("#44743a")
    # Brush grain runs with the direction of running (along u).
    strokes(img, 9000, [light, mid, dark], 26, 2, 0.0, 0.12, 60, 4)
    strokes(img, 1800, [hexrgb("#9cc56a"), hexrgb("#b9c978")], 14, 1, 0.0, 0.2, 55, 5)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return img.convert("RGB")


def grass(size=1024):
    base = hexrgb("#5f8f40")
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
def _blur(a, sigma):
    return gaussian_filter(a, sigma, mode="nearest")


def tree(size=512, seed=0, kind="oak"):
    """A painted tree, lit from the upper left like the scene's sun.

    The canopy is a set of leaf masses (big soft bumps) covered in smaller leaf
    clusters; their combined height gives a surface that is shaded like a painted
    ball of foliage: warm highlights on the lit side, cool dark greens in the
    hollows, a leafy broken edge, then a few dabs of light on top."""
    r = np.random.default_rng(seed)
    S = size
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    cx = S / 2
    if kind == "poplar":
        rx, ry, ccy = S * 0.14, S * 0.36, S * 0.50
    elif kind == "wide":
        rx, ry, ccy = S * 0.38, S * 0.25, S * 0.52
    else:
        rx, ry, ccy = S * 0.32, S * 0.29, S * 0.52
    # Core: one soft ellipsoid so the canopy always holds together
    d2 = ((xx - cx) / (rx * 0.85)) ** 2 + ((yy - ccy) / (ry * 0.85)) ** 2
    height = np.sqrt(np.clip(1 - d2, 0, 1)) * min(rx, ry) * 0.8
    # Leaf masses
    for _ in range(9 if kind != "poplar" else 7):
        ang = r.uniform(0, 2 * math.pi); rad = math.sqrt(r.uniform(0, 0.75))
        x = cx + math.cos(ang) * rad * rx * 0.75; y = ccy + math.sin(ang) * rad * ry * 0.75
        rr = min(rx, ry) * r.uniform(0.4, 0.6)
        d2 = ((xx - x) ** 2 + (yy - y) ** 2) / rr ** 2
        height = np.maximum(height, np.sqrt(np.clip(1 - d2, 0, 1)) * rr)
    # Leaf clusters on the surface
    clusters = np.zeros((S, S))
    for _ in range(260):
        ang = r.uniform(0, 2 * math.pi); rad = math.sqrt(r.uniform(0, 1.05))
        x = cx + math.cos(ang) * rad * rx * 0.95; y = ccy + math.sin(ang) * rad * ry * 0.95
        rr = S * r.uniform(0.016, 0.034)
        d2 = ((xx - x) ** 2 + (yy - y) ** 2) / rr ** 2
        clusters = np.maximum(clusters, np.sqrt(np.clip(1 - d2, 0, 1)) * rr)
    leafy = periodic_noise(S, S, 70, seed + 100)
    mask = ((height > 0.5) | ((clusters > 0.3) & (_blur(height, 6) > 1.0))).astype(float)
    near = _blur(mask, 5) > 0.15
    mask = _blur(mask, 1.6) + leafy * 0.18 * near
    alpha = np.clip((mask - 0.42) * 6, 0, 1)
    h = _blur(height, 3) + clusters * 0.6
    gy, gx = np.gradient(h)
    nz = np.ones_like(h) * 1.6
    n = np.stack([-gx, -gy, nz], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.55, -0.6, 0.58]); L /= np.linalg.norm(L)
    lam = np.clip((n * L).sum(-1), 0, 1)
    # Self-shadow towards the lower right of the canopy, and darker hollows.
    side = np.clip(((xx - cx) / rx * 0.5 + (yy - ccy) / ry * 0.7), -1, 1)
    occl = np.clip(clusters / (S * 0.03), 0, 1)
    shade = lam * 0.75 + 0.25 * occl - 0.28 * np.clip(side, 0, 1) + leafy * 0.06
    shade = np.clip(shade, 0, 1)
    # Painted colour ramp: cool dark -> mid -> warm light -> sunlit
    stops = [(0.0, (30, 52, 38)), (0.35, (52, 84, 44)), (0.62, (88, 122, 54)), (0.82, (132, 156, 70)), (1.0, (188, 190, 104))]
    hue = r.normal(0, 7, 3) * np.array([1.0, 0.6, 0.3])
    col = np.zeros((S, S, 3))
    for (a0, c0), (a1, c1) in zip(stops, stops[1:]):
        t = np.clip((shade - a0) / (a1 - a0), 0, 1)[..., None]
        seg = (shade >= a0) & (shade <= a1)
        col[seg] = (np.array(c0) * (1 - t) + np.array(c1) * t)[seg]
    col += hue
    # Darker rim just inside the silhouette
    inner = _blur(alpha, 4)
    col *= (0.8 + 0.2 * np.clip((inner - 0.5) * 3, 0, 1))[..., None]
    # Trunk and a few branches showing under the canopy
    trunk = np.zeros((S, S))
    tw = S * (0.03 if kind != "wide" else 0.04)
    top = ccy + ry * 0.3
    t = (yy - top) / (S * 0.97 - top)
    w = tw * (0.7 + 0.5 * np.clip(t, 0, 1))
    trunk[(yy > top) & (yy < S * 0.97) & (np.abs(xx - cx) < w)] = 1
    tcol = np.array([92, 70, 50]) * (0.75 + 0.35 * ((xx - cx) < 0))[..., None]
    talpha = trunk * (1 - alpha)
    out = col * alpha[..., None] + tcol * talpha[..., None]
    A = np.clip(alpha + talpha, 0, 1)
    rgb = np.clip(out / np.maximum(A, 1e-3)[..., None], 0, 255)
    img = Image.fromarray(rgb.astype(np.uint8), "RGB")
    img = img.filter(ImageFilter.ModeFilter(3))
    # Dabs of light on the sunlit side (painted highlights)
    d = ImageDraw.Draw(img)
    for _ in range(140):
        x = cx + r.normal(-0.3, 0.45) * rx; y = ccy + r.normal(-0.35, 0.45) * ry
        if 0 <= int(x) < S and 0 <= int(y) < S and alpha[int(y), int(x)] > 0.9 and shade[int(y), int(x)] > 0.6:
            rr = S * r.uniform(0.004, 0.009)
            c = tuple(int(v) for v in np.clip(np.array([176, 186, 96]) + r.normal(0, 10, 3), 0, 255))
            d.ellipse([x - rr, y - rr * 0.7, x + rr, y + rr * 0.7], fill=c)
    arr = np.dstack([np.array(img).astype(float), A * 255])
    # Bleed colour into transparent pixels so mip-mapping doesn't draw dark halos.
    m = A[..., None]
    fill = np.dstack([_blur(arr[..., i] * A, 10) / np.maximum(_blur(A, 10), 1e-3) for i in range(3)])
    arr[..., :3] = arr[..., :3] * m + np.clip(fill, 0, 255) * (1 - m)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


if __name__ == "__main__":
    turf().save(os.path.join(OUT, "turf.png"), optimize=True)
    grass().save(os.path.join(OUT, "grass.png"), optimize=True)
    path().save(os.path.join(OUT, "path.png"), optimize=True)
    kinds = ["oak", "wide", "oak", "poplar"]
    atlas = Image.new("RGBA", (512 * 4, 512), (0, 0, 0, 0))
    for i, k in enumerate(kinds):
        atlas.paste(tree(512, seed=31 + i, kind=k), (512 * i, 0))
    atlas.save(os.path.join(OUT, "trees.png"), optimize=True)
    print("wrote", sorted(os.listdir(OUT)))
