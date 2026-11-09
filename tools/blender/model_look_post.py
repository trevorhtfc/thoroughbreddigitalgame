"""The model look's finishing pass (owner's concept stills, 9 Nov 2026), on a still from stand_clean_study.py.

    python3 tools/blender/model_look_post.py <still.png> [out.png] [key=value ...]

Reads the still, its depth (<still>.exr, written by the study with DEPTH=1 or the "model" variant) and its camera
(<still>.json), and adds what makes the concept read as a photograph of a model, all worked out from the depth:
  haze     distant things sink into a pale lilac-cream air, so the picture recedes in soft layers
  focus    a shallow miniature focus: sharp at the subject's distance, blurring smoothly nearer and further,
           the way a macro lens sees a table-top model (a real lens's blur, by depth, not a band)
  grade    high key: a touch more exposure, a soft S-curve, lavender in the shadows, warm cream in the highlights,
           a little less saturation (the sky a little more: the tone mapping greys a pale blue sky)
  glow     the brightest parts bleed a little light, like a soft lens
  sky      the sky painted: cream-peach at the horizon, lilac, soft cornflower, with soft clouds
Every step has a strength (key=value: sky, haze, focus, grade, glow), so they can be tried one at a time. All plain
numbers, ready to carry into the race view's own finishing pass.
"""
import sys, json
import numpy as np
import OpenEXR
from PIL import Image
from scipy.ndimage import gaussian_filter

args = [a for a in sys.argv[1:] if "=" not in a]
opts = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
src = args[0]
out = args[1] if len(args) > 1 else src[:-4] + "_post.png"
K = {"haze": 1.0, "focus": 1.0, "grade": 1.0, "glow": 1.0, "sky": 1.0}
K.update({k: float(v) for k, v in opts.items() if k in K})

img = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
H, W = img.shape[:2]
ex = OpenEXR.File(src[:-4] + ".exr")
z = None
for p in ex.parts:
    for name, ch in p.channels.items():
        if name.endswith("Depth.Z") or name == "Depth.Z" or name.endswith(".Z"):
            z = np.asarray(ch.pixels, dtype=np.float32)
if z is None: raise SystemExit("no depth in the EXR")
if z.ndim == 3: z = z[..., 0]
cam = json.load(open(src[:-4] + ".json"))
sky = z > 5e4
zf = float(opts.get("fd", cam["focusDist"]))       # fd=<metres> to move the focus
px = W / 1600.0                                    # sizes below are for a 1600 px wide still

# ---- sky: painted, as the concept's: cream-peach at the horizon, a lilac band, a soft cornflower blue above, with
# soft fair-weather clouds (warm white tops, faintly lilac undersides). Cycles' sky comes out a pale grey once tone
# mapped; painting it here keeps it a free choice (and is how the race view draws its sky anyway).
if K["sky"] > 0 and sky.any():
    rows = np.where(sky.any(1))[0]
    cols_sky = sky.mean(0) > 0
    # the horizon: the lowest row where the sky shows, taken as the median over the columns that have sky
    low = np.array([np.where(sky[:, x])[0].max() for x in np.where(cols_sky)[0]])
    hy = float(np.median(low)) + 2.0
    yy0 = np.arange(H, dtype=np.float32)[:, None]
    tsky = np.clip((hy - yy0) / H, 0, 1) * np.ones((1, W), np.float32)
    stops = [(0.0, (0.97, 0.89, 0.84)), (0.07, (0.88, 0.86, 0.93)), (0.22, (0.76, 0.8, 0.92)), (0.55, (0.62, 0.71, 0.9))]
    paint = np.zeros((H, W, 3), np.float32)
    for (t0, c0), (t1, c1) in zip(stops[:-1], stops[1:]):
        m = (tsky >= t0) & (tsky <= t1)
        f = ((tsky - t0) / (t1 - t0))[..., None]
        paint[m] = (np.array(c0) * (1 - f) + np.array(c1) * f)[m]
    paint[tsky > stops[-1][0]] = stops[-1][1]
    # clouds: layered noise, stretched sideways, in a band above the horizon
    rng = np.random.default_rng(int(abs(hash(src)) % 1000))
    def noise(sx, sy, oct=5):
        acc = np.zeros((H, W), np.float32); amp = 1.0; tot = 0
        for o in range(oct):
            gh, gw = int(sy * 2 ** o) + 2, int(sx * 2 ** o) + 2
            g = rng.random((gh, gw)).astype(np.float32)
            up = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
            acc += up * amp; tot += amp; amp *= 0.5
        return acc / tot
    n = noise(9, 6)
    band = np.clip((tsky - 0.04) / 0.08, 0, 1) * np.clip((0.6 - tsky) / 0.25, 0, 1)
    cl = np.clip((n - 0.58) / 0.08, 0, 1) * band
    shade = np.clip((n - 0.62) / 0.2, 0, 1)                     # thicker parts: brighter tops
    cloud_col = np.array([0.99, 0.96, 0.95], np.float32) * (0.93 + 0.07 * shade[..., None]) + np.array([-0.04, -0.03, 0.0], np.float32) * (1 - shade[..., None])
    paint = paint * (1 - cl[..., None]) + cloud_col * cl[..., None]
    soft = gaussian_filter(sky.astype(np.float32), 0.8)[..., None]
    img = img * (1 - soft * K["sky"]) + paint * soft * K["sky"]

# ---- haze: from 120 m, up to 38% at 1 km, towards a pale lilac-cream
haze_col = np.array([0.91, 0.885, 0.915], np.float32)
t = np.clip((z - 120.0) / (1000.0 - 120.0), 0, 1); t = t * t * (3 - 2 * t)
h = (0.38 * K["haze"] * t)[..., None]
h[sky] = 0
c = img * (1 - h) + haze_col * h

# ---- miniature focus: thin-lens blur (pixels) = A * |1 - zf / z|, capped
A, CAP = 7.0 * px * K["focus"], 9.0 * px * max(K["focus"], 0.01)
coc = np.clip(A * np.abs(1.0 - zf / np.maximum(z, 0.1)), 0, CAP)
coc[sky] = min(CAP, A)
if K["focus"] > 0:
    radii = sorted(set(round(min(r * px, CAP), 3) for r in (0.0, 1.0, 2.0, 3.5, 5.5, 8.0, 11.0, 16.0)))
    stack = [c if r == 0 else np.stack([gaussian_filter(c[..., k], r / 2.0) for k in range(3)], -1) for r in radii]
    rs = np.array(radii, np.float32)
    i1 = np.clip(np.searchsorted(rs, coc), 1, len(rs) - 1); i0 = i1 - 1
    f = np.clip((coc - rs[i0]) / np.maximum(rs[i1] - rs[i0], 1e-3), 0, 1)[..., None]
    S = np.stack(stack, 0)
    yy, xx = np.mgrid[0:H, 0:W]
    c = S[i0, yy, xx] * (1 - f) + S[i1, yy, xx] * f

# ---- grade (display values, 0-1)
g = K["grade"]
if g > 0:
    l = (c @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    graded = np.clip(c * 1.045, 0, 1)
    graded = graded + 0.12 * (graded * graded * (3 - 2 * graded) - graded)           # soft S-curve
    lg = (graded @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    graded = lg + (graded - lg) * np.where(sky[..., None], 1.0, 0.93)               # a little less saturation; a bluer sky
    graded = graded + (1 - lg) ** 2 * np.array([0.012, 0.004, 0.03], np.float32)     # lavender shadows
    graded = graded * (1 + lg * np.array([0.02, 0.006, -0.025], np.float32))         # warm cream highlights
    c = c + (np.clip(graded, 0, 1) - c) * g

# ---- glow from the brightest parts
if K["glow"] > 0:
    hi = np.clip(c - 0.72, 0, 1)
    glow = np.stack([gaussian_filter(hi[..., k], 14 * px) for k in range(3)], -1)
    c = 1 - (1 - c) * (1 - 0.35 * K["glow"] * glow)

# ---- a faint vignette
yy, xx = np.mgrid[0:H, 0:W]
v = np.sqrt(((xx / W - 0.5) * 1.0) ** 2 + ((yy / H - 0.5) * 0.85) ** 2)
c = c * (1 - 0.06 * np.clip((v - 0.35) / 0.5, 0, 1))[..., None]

Image.fromarray((np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)).save(out)
print("wrote", out)
