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
def _blur(a, sigma):
    return gaussian_filter(a, sigma, mode="nearest")


def tree(size=512, seed=0, kind="oak"):
    """A painted tree, lit from the upper left like the scene's sun.

    The canopy is a few overlapping leaf masses in 3D. Thousands of small leaf
    dabs are scattered over their surfaces, each shaded by how much it faces the
    sun and how deep it sits in the crown, then painted back to front. Branches
    show through the gaps. Drawn at twice the size and scaled down so the dabs
    read as foliage rather than blobs."""
    r = np.random.default_rng(seed)
    S2 = size * 2
    img = Image.new("RGBA", (S2, S2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    U = S2 / 2                      # 1 unit = half the image
    cx = S2 / 2
    def px(x, y):                   # canopy space (x right, y up) -> pixels
        return cx + x * U, S2 * 0.96 - y * U
    # Shape of the crown per kind: list of lobes (x, y, z, rx, ry, rz)
    if kind == "poplar":
        base = [(0, 1.0, 0, 0.24, 0.62, 0.24)]
        n_lobes, spread, lobe_r = 9, (0.16, 0.55, 0.12), (0.12, 0.22)
        trunk_top, trunk_w = 0.55, 0.045
    elif kind == "wide":
        base = [(0, 0.88, 0, 0.62, 0.34, 0.50)]
        n_lobes, spread, lobe_r = 14, (0.70, 0.30, 0.40), (0.16, 0.30)
        trunk_top, trunk_w = 0.60, 0.075
    else:
        base = [(0, 0.90, 0, 0.48, 0.40, 0.44)]
        n_lobes, spread, lobe_r = 13, (0.55, 0.40, 0.35), (0.15, 0.30)
        trunk_top, trunk_w = 0.60, 0.065
    lobes = list(base)
    bx, by, bz = base[0][:3]
    for _ in range(n_lobes):
        rr = r.uniform(*lobe_r)
        lobes.append((bx + r.uniform(-1, 1) * spread[0], by + r.uniform(-0.8, 1) * spread[1], bz + r.uniform(-1, 1) * spread[2],
                      rr * r.uniform(0.9, 1.2), rr * r.uniform(0.8, 1.0), rr))
    top = max(l[1] + l[4] for l in lobes)
    if top > 1.9:                    # keep inside the frame
        k = 1.9 / top
        lobes = [(x, (y - 0.5) * k + 0.5, z, a * k, b * k, c * k) for (x, y, z, a, b, c) in lobes]
    # --- Trunk and branches ---
    bark_dark, bark_light = np.array([70, 54, 40]), np.array([122, 98, 72])
    def limb(x0, y0, x1, y1, w0, w1):
        n = 12
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            xa, ya = x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0
            xb, yb = x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1
            wa, wb = w0 + (w1 - w0) * t0, w0 + (w1 - w0) * t1
            pa, pb = px(xa, ya), px(xb, yb)
            poly = [(pa[0] - wa * U, pa[1]), (pa[0] + wa * U, pa[1]), (pb[0] + wb * U, pb[1]), (pb[0] - wb * U, pb[1])]
            d.polygon(poly, fill=tuple(int(v) for v in bark_dark) + (255,))
            lit = [(pa[0] - wa * U, pa[1]), (pa[0] - wa * U * 0.1, pa[1]), (pb[0] - wb * U * 0.1, pb[1]), (pb[0] - wb * U, pb[1])]
            d.polygon(lit, fill=tuple(int(v) for v in bark_light) + (255,))
    limb(0, 0, 0.0, 0.08, trunk_w * 1.35, trunk_w)          # root flare
    limb(0, 0.08, 0.02, trunk_top, trunk_w, trunk_w * 0.7)
    for _ in range(5 if kind != "poplar" else 3):
        ang = r.uniform(-0.9, 0.9)
        L = r.uniform(0.25, 0.45)
        y0 = trunk_top * r.uniform(0.7, 1.0)
        limb(0.02, y0, 0.02 + math.sin(ang) * L, y0 + math.cos(ang) * L, trunk_w * 0.45, trunk_w * 0.12)
    # --- Leaf dabs ---
    Lsun = np.array([-0.55, 0.62, 0.56]); Lsun /= np.linalg.norm(Lsun)
    pts = []
    n_dabs = 9000 if kind != "poplar" else 5000
    vols = np.array([l[3] * l[4] * l[5] for l in lobes]); vols /= vols.sum()
    for _ in range(n_dabs):
        li = r.choice(len(lobes), p=vols)
        x, y, z, a, b, c = lobes[li]
        v = r.normal(size=3); v /= np.linalg.norm(v)
        depth = r.uniform(0.80, 1.08) ** 0.5
        P = np.array([x + v[0] * a * depth, y + v[1] * b * depth, z + v[2] * c * depth])
        # Hide dabs buried inside another lobe
        buried = False
        for (x2, y2, z2, a2, b2, c2) in lobes:
            q = ((P[0] - x2) / a2) ** 2 + ((P[1] - y2) / b2) ** 2 + ((P[2] - z2) / c2) ** 2
            if q < 0.6:
                buried = True; break
        if buried:
            continue
        N = np.array([v[0] / a, v[1] / b, v[2] / c]); N /= np.linalg.norm(N)
        pts.append((P, N, depth))
    pts.sort(key=lambda t: t[0][2])
    stops = [(0.0, (26, 44, 34)), (0.3, (44, 72, 40)), (0.55, (76, 106, 50)), (0.78, (122, 146, 66)), (1.0, (182, 186, 102))]
    def ramp(t):
        for (a0, c0), (a1, c1) in zip(stops, stops[1:]):
            if t <= a1:
                k = (t - a0) / (a1 - a0)
                return np.array(c0) * (1 - k) + np.array(c1) * k
        return np.array(stops[-1][1])
    hue = r.normal(0, 6, 3) * np.array([1.0, 0.7, 0.4])
    ylo = min(l[1] - l[4] for l in lobes); yhi = max(l[1] + l[4] for l in lobes)
    for P, N, depth in pts:
        lam = max(0.0, float(N @ Lsun))
        under = np.clip((P[1] - ylo) / (yhi - ylo), 0, 1)          # 0 at the bottom of the crown
        shade = 0.05 + 0.78 * lam ** 1.2 + 0.20 * under + r.normal(0, 0.06)
        col = np.clip(ramp(np.clip(shade, 0, 1)) + hue + r.normal(0, 5, 3), 0, 255)
        X, Y = px(P[0], P[1])
        rad = U * r.uniform(0.016, 0.030)
        ang = r.uniform(0, math.pi)
        e = [(X + math.cos(t) * rad * (1.0 if i % 2 == 0 else 0.62) * math.cos(ang) - math.sin(t) * rad * 0.62 * math.sin(ang),
              Y + math.cos(t) * rad * math.sin(ang) + math.sin(t) * rad * 0.62 * math.cos(ang)) for i, t in enumerate(np.linspace(0, 2 * math.pi, 10, endpoint=False))]
        d.polygon(e, fill=tuple(int(v) for v in col) + (255,))
    # Scale down for smooth edges, then bleed colour under transparent pixels (no dark halos when mip-mapped).
    out = img.resize((size, size), Image.LANCZOS)
    arr = np.array(out).astype(float)
    A = arr[..., 3] / 255
    fill = np.dstack([_blur(arr[..., i] * A, 8) / np.maximum(_blur(A, 8), 1e-3) for i in range(3)])
    m = A[..., None]
    arr[..., :3] = arr[..., :3] * np.where(m > 0, 1, 0) + np.clip(fill, 0, 255) * np.where(m > 0, 0, 1)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


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
