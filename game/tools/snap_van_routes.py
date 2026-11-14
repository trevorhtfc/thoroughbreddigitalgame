# Keeps the horseboxes on the painted roads (owner, 7 Nov: "vehicles taking strange routes, not sticking to the roads").
# The van routes are built from the hand-placed road lines in src/board.src.js (ROAD), which drift up to ~15 px off the
# painted road in places (onto verges, front gardens, a yard). This finds the painted road surface on the board (its
# light beige), and slides every point of each van route sideways onto the middle of the road, then smooths the result.
# Writes the routes into src/life.src.js between the VAN_ROUTES markers. Run tools/build.py afterwards.
#   python3 tools/snap_van_routes.py [--check out.png]
import re, json, sys
import numpy as np, cv2
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d, median_filter

HERE = __file__.rsplit("/", 2)[0]
src = open(f"{HERE}/src/board.src.js").read()
block = src[src.index("const ROAD = {"):src.index("const rev =")]
ROAD = {m.group(1): json.loads(m.group(2).replace("RB", "[632,294]")) for m in re.finditer(r"(\w+): (\[.*\]),[ \t]*(?://[^\n]*)?\n", block)}
rev = lambda a: a[::-1]
def join(*parts):
    acc = []
    for p in parts: acc = acc + (p[1:] if acc else p)
    return acc
STABLES_LANE = [[722, 721], [659, 722], [636, 726], [616, 734], [598, 736], [583, 733], [531, 743], [496, 758], [468, 787], [448, 800]]
# Only the painted main roads are snapped (each road on its own, its two ends kept where they are so the roads still
# meet); the lane from the stables past the Jockey Club is a faint track along a fence, so it stays as drawn.
SNAP = ["fordham", "oldStn", "nmkt", "kingston", "bury", "highSt", "station", "avenueW"]
# The road west of the town that the board's own list (ROAD) stops short of: the Avenue, from the end of Station Road
# out to the board's left edge.
ROAD["station"] = ROAD["station"][:-1] + [[250, 340]]
ROAD["avenueW"] = [[250, 340], [200, 308], [150, 278], [100, 250], [50, 222], [15, 203], [-20, 184]]
im = np.array(Image.open(f"{HERE}/assets/newmarket/newmarket-board.webp").convert("RGB")).astype(int)
H, W = im.shape[:2]
R, G, B = im[..., 0], im[..., 1], im[..., 2]
road = ((R > 192) & (G > 176) & (B > 130) & (R - B < 80) & (R - B > 12)).astype(np.uint8)
road = cv2.morphologyEx(road, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
road = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
dt = cv2.distanceTransform(road, cv2.DIST_L2, 5)

def resample(pts, step=3.0):
    pts = np.asarray(pts, float); seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); t = np.arange(0, s[-1], step)
    return np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], 1)

def snap(pts, reach=12):
    p = resample(pts); n = len(p)
    d = np.gradient(p, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    off = np.full(n, np.nan); offs = np.arange(-reach, reach + 1, 0.5)
    for i in range(n):
        q = p[i] + nrm[i] * offs[:, None]; x, y = q[:, 0].round().astype(int), q[:, 1].round().astype(int)
        ok = (x >= 2) & (x < W - 2) & (y >= 2) & (y < H - 2)
        if ok.sum() < len(offs) * 0.8: continue                     # off the board's edge: leave as drawn
        v = np.zeros(len(offs)); v[ok] = dt[y[ok], x[ok]]
        if v.max() < 3: continue                                    # no road here (a gap in the paint): leave as drawn
        score = v - 0.22 * np.abs(offs)                             # the middle of the nearest road, not a road further off
        off[i] = offs[score.argmax()]
    idx = np.arange(n); good = ~np.isnan(off)
    off = np.interp(idx, idx[good], off[good]) if good.any() else np.zeros(n)
    off[~good] = off[~good] * 0.0 + np.interp(idx[~good], idx[good], off[good]) if good.any() else 0
    off = gaussian_filter1d(median_filter(off, 9, mode="nearest"), 4, mode="nearest")
    # the ends stay where they were (they run off the board's edge or into a yard)
    taper = np.clip(np.minimum(idx, n - 1 - idx) / 6, 0, 1); off *= taper
    out = p + nrm * off[:, None]
    out = gaussian_filter1d(out, 2, axis=0, mode="nearest")
    out[0], out[-1] = p[0], p[-1]
    return out, np.abs(off).max()

def simplify(pts, tol=0.7):
    c = cv2.approxPolyDP(pts.astype(np.float32).reshape(-1, 1, 2), tol, False).reshape(-1, 2)
    return [[round(float(x), 1), round(float(y), 1)] for x, y in c]

R2 = {}
for k in SNAP:
    q, mx = snap(ROAD[k]); R2[k] = q; print(f"{k}: moved up to {mx:.1f} px")
F = lambda k: [list(map(float, x)) for x in R2[k]]
rv = lambda a: a[::-1]
# One way round (owner, 14 Nov: "some of the vans are still hitting buildings, horses or each other"). Every road has
# one direction, the one the strings already walk it in, so nothing ever meets head on: Old Station Road, Bury Road and
# Newmarket Road lead in to the roundabout; Fordham Road, and the High Street and Station Road out to the Avenue, lead away.
ROUTES = {
    "oldStnFordham": join(rv(F("oldStn")), rv(F("fordham"))),
    "nmktFordham": join(rv(F("nmkt")), rv(F("kingston")), rv(F("fordham"))),
    "buryAvenue": join(rv(F("bury")), F("highSt"), F("station"), F("avenueW")),
    # the lane from the stables meets the road a little above the corner: straight on up Kingston Road, no doubling back
    "toTheRaces": join([list(map(float, x)) for x in STABLES_LANE[:-2]], [q for q in rv(F("kingston")) if q[1] < 745], rv(F("fordham"))),
}
snapped = {k: simplify(np.array(v)) for k, v in ROUTES.items()}
ROUTES0 = {
    "oldStnFordham": join(rev(ROAD["oldStn"]), rev(ROAD["fordham"])),
    "nmktFordham": join(rev(ROAD["nmkt"]), rev(ROAD["kingston"]), rev(ROAD["fordham"])),
    "buryAvenue": join(rev(ROAD["bury"]), ROAD["highSt"], ROAD["station"], ROAD["avenueW"]),
    "toTheRaces": join(STABLES_LANE, rev(ROAD["kingston"]), rev(ROAD["fordham"])),
}
life = f"{HERE}/src/life.src.js"; L = open(life).read()
a, b = "// VAN_ROUTES (made by tools/snap_van_routes.py: do not edit by hand)\n", "// /VAN_ROUTES\n"
body = "const VAN_ROUTES = {\n" + "".join(f"  {k}: {json.dumps(v, separators=(',', ':'))},\n" for k, v in snapped.items()) + "};\n"
if a in L: L = L[:L.index(a) + len(a)] + body + L[L.index(b):]
else: raise SystemExit("markers missing in src/life.src.js")
open(life, "w").write(L)

if "--check" in sys.argv:
    out = sys.argv[sys.argv.index("--check") + 1]
    pic = Image.open(f"{HERE}/assets/newmarket/newmarket-board.webp").convert("RGB"); d = ImageDraw.Draw(pic)
    for k, r in ROUTES0.items(): d.line([tuple(q) for q in r], fill="#ff2020", width=2)
    for k, r in snapped.items(): d.line([tuple(q) for q in r], fill="#1050ff", width=2)
    px = pic.load()
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if road[y, x]: px[x, y] = (255, 255, 0)
    pic.save(out)
