"""Goodwood, phase 3: the long views (owner, 17 Nov 2026: "then we need to figure out how we create the more longer
range scenery that is iconic with goodwood"; the approach he agreed: the real ground out to about 10 km as a light mesh,
painted with its fields, woods and the town; beyond it a painted panorama of the far distance, the coastal plain, the
sea and the Isle of Wight; the Trundle's masts and Chichester Cathedral's spire standing up in 3D).

From the race view's ground grid (the 20 m heights round the course: to_race_view.py) outwards:

  the far land   a light mesh on the real ground (reference/goodwood/dem-course-20m.json near to, dem-region-400m.json
                 beyond it), its cells 80 m wide for 2 km round the ground grid, then wider and wider out to about 11 km;
                 the earth's curve taken off; painted from OpenStreetMap where it reaches (woods raised as a canopy,
                 fields, grass, villages), a field patchwork and scattered woods beyond it, Chichester as a town, the sea
                 at sea level. Its inner edge meets the ground grid's edge (the grid keeps its real heights out to it).
  the panorama   what shows beyond 9.5 km, cast across the real ground from over the course (horizon.py's method): the
                 ground and the sea as a picture all round, 5 degrees tall, with how hazy each pixel should be; the race
                 view hangs it round the camera, behind everything, and hazes it in the day's own haze colour.
  landmarks      the Trundle's two masts (St Roche's Hill, 0.9 km west of the stands) and Chichester Cathedral (its tower
                 and spire, 6.6 km to the south-south-west), on the far land.

Writes  race-view/assets/course/goodwood-farland.json        the mesh, the landmarks, how to hang the panorama
        race-view/assets/course/goodwood-far-colour.png      the panorama's colours (alpha: where there is ground)
        race-view/assets/course/goodwood-far-haze.png        the panorama's haze (0 clear .. 255 all haze)
        reference/goodwood/renders/far-panorama.png          the panorama, hazed, for checking

  python3 tools/course/goodwood/farland.py      (after to_race_view.py: it reads the ground grid from goodwood.json)
"""
import json, math, importlib.util
from pathlib import Path
import numpy as np
from matplotlib.path import Path as MPath

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OUT = REPO / "race-view/assets/course"


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, HERE / file); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


LY = _load("goodwood_layout", "layout.py")
HZ = _load("goodwood_horizon", "horizon.py")
R_EFF = HZ.R_EFF
NEAR_BAND, NEAR_CELL = 2000.0, 80.0          # 80 m cells for 2 km round the ground grid
OUTER = 10500.0                              # out to this far from the course's middle
PANO_FROM = 9500.0                           # the panorama shows the ground beyond this
PANO_W, PANO_H, PANO_LO, PANO_HI = 8192, 256, -3.0, 2.0     # its size, and the angles (degrees) its rows span
CANOPY = 13.0                                # a wood's canopy over the ground, metres

# colours (sRGB): a soft downland palette, close to the soft look's own (the race view hazes them by distance)
COL = {"down": (0.62, 0.72, 0.47), "farm": (0.76, 0.76, 0.52), "farm2": (0.72, 0.75, 0.50), "grass": (0.60, 0.72, 0.46),
       "wood": (0.30, 0.45, 0.28), "wood2": (0.36, 0.52, 0.32), "town": (0.78, 0.74, 0.66), "sea": (0.63, 0.73, 0.78)}


def world_of_en(e, n):
    q = np.stack([e, n], -1) - LY.POST
    return q @ LY.XH, q @ LY.ZH


def en_of_world(x, z):
    return LY.POST[0] + x * LY.XH[0] + z * LY.ZH[0], LY.POST[1] + x * LY.XH[1] + z * LY.ZH[1]


def axis(lo_in, hi_in, cell0, band, outer_lo, outer_hi):
    """grid lines: every cell0 from lo_in to hi_in (both included), then cell0 for 'band' metres either side, then
    growing by 15% a step to 600 m, out to outer_lo / outer_hi"""
    mid = list(np.arange(lo_in, hi_in, cell0)) + [hi_in]
    def out(start, sign, limit):
        L, x, step = [], start, cell0
        while True:
            x = x + sign * step
            if (x - start) * sign > band: step = min(step * 1.15, 600.0)
            L.append(x)
            if (x - limit) * sign >= 0: break
        return L
    lo = out(lo_in, -1, outer_lo)[::-1]; hi = out(hi_in, +1, outer_hi)
    return np.array(lo + mid + hi)


def main():
    C = json.loads((OUT / "goodwood.json").read_text())
    G = C["ground"]; post_h = json.loads((REPO / "courses/goodwood-draft.json").read_text())["postGroundM"]
    gx0, gz0, gc = G["x0"], G["z0"], G["cell"]
    gx1, gz1 = gx0 + gc * (G["nx"] - 1), gz0 + gc * (G["nz"] - 1)
    gh = np.array(G["h"]).reshape(G["nz"], G["nx"])
    cx, cz = (gx0 + gx1) / 2, (gz0 + gz1) / 2
    xs = axis(gx0, gx1, NEAR_CELL, NEAR_BAND, cx - OUTER, cx + OUTER)
    zs = axis(gz0, gz1, NEAR_CELL, NEAR_BAND, cz - OUTER, cz + OUTER)
    X, Z = np.meshgrid(xs, zs)
    E, N = en_of_world(X, Z)
    H = HZ.height(E.ravel(), N.ravel()).reshape(X.shape)
    SEA = HZ.sea(E.ravel(), N.ravel()).reshape(X.shape) & (H <= 1.0)
    H = np.where(SEA, 0.0, H)
    D = np.hypot(X - cx, Z - cz)
    Y = H - post_h - D ** 2 / (2 * R_EFF)
    # on and inside the ground grid's edge: the grid's own heights (inside, a little under it: hidden)
    def grid_h(x, z):
        fx, fz = (x - gx0) / gc, (z - gz0) / gc
        i = np.clip(np.floor(fx).astype(int), 0, G["nx"] - 2); j = np.clip(np.floor(fz).astype(int), 0, G["nz"] - 2)
        a, b = np.clip(fx - i, 0, 1), np.clip(fz - j, 0, 1)
        return (gh[j, i] * (1 - a) + gh[j, i + 1] * a) * (1 - b) + (gh[j + 1, i] * (1 - a) + gh[j + 1, i + 1] * a) * b
    ins = (X >= gx0 - 0.01) & (X <= gx1 + 0.01) & (Z >= gz0 - 0.01) & (Z <= gz1 + 0.01)
    strict = (X > gx0 + 0.01) & (X < gx1 - 0.01) & (Z > gz0 + 0.01) & (Z < gz1 - 0.01)
    Y = np.where(ins, grid_h(X, Z) - np.where(strict, 4.0, 0.0), Y)

    # ---- what covers the ground: OpenStreetMap where it reaches, a patchwork beyond
    O = json.loads((REPO / "reference/goodwood/osm-surround.json").read_text())
    def rings(k):
        out = []
        for f in O[k]:
            x = y = 0; pts = []
            for i in range(0, len(f), 2): x += f[i]; y += f[i + 1]; pts.append((x, y))
            if len(pts) >= 4: out.append(MPath(pts))
        return out
    P = np.c_[E.ravel(), N.ravel()]
    def cover(k, pts=P):
        m = np.zeros(len(pts), bool)
        for path in rings(k): m |= path.contains_points(pts)
        return m
    osm_box = (E.ravel() > -4000) & (E.ravel() < 4300) & (N.ravel() > -3250) & (N.ravel() < 3250)
    # woods as a fraction (five samples round each point), so a canopy's edge slopes rather than steps
    wood = np.zeros(len(P))
    for dx, dy in ((0, 0), (25, 0), (-25, 0), (0, 25), (0, -25)):
        wood += (cover("wood", P + [dx, dy]) | cover("scrub", P + [dx, dy])) / 5.0
    farm, grass, built = cover("farm"), cover("grass"), cover("built")
    rng = np.random.default_rng(7)
    # beyond OpenStreetMap's box: fields in 500 m squares of two tones, a wood in about one square in five
    cell_id = (np.floor(E.ravel() / 520).astype(int) * 7919 + np.floor(N.ravel() / 470).astype(int) * 104729) % 1000
    far_wood = (cell_id % 5 == 0) & ~osm_box
    wood = np.where(osm_box, wood, far_wood.astype(float))
    ch = (E.ravel() - HZ.en(50.8365, -0.7795)[0]) ** 2 + (N.ravel() - HZ.en(50.8365, -0.7795)[1]) ** 2 < 1300 ** 2   # Chichester
    sea = SEA.ravel()
    col = np.zeros((len(P), 3))
    for k in range(len(P)):
        if sea[k]: c = COL["sea"]
        elif ch[k]: c = COL["town"]
        elif built[k]: c = COL["town"]
        elif osm_box[k]: c = COL["farm"] if farm[k] else COL["grass"] if grass[k] else COL["down"]
        else: c = COL["farm"] if cell_id[k] % 3 else COL["farm2"]
        c = np.array(c)
        if wood[k] > 0 and not sea[k]: c = c * (1 - wood[k]) + np.array(COL["wood"] if cell_id[k] % 2 else COL["wood2"]) * wood[k]
        col[k] = c * rng.uniform(0.95, 1.05)
    lift = np.where(sea, 0.0, wood * CANOPY + np.where(ch | built, 6.0, 0.0)).reshape(X.shape)
    lift = np.where(ins, 0.0, lift)                 # (inside the grid: under the ground, the canopies are perimeter.py's)
    Y = Y + lift
    # the cells to draw: all but those inside the ground grid
    nz_, nx_ = X.shape
    tris = []
    for j in range(nz_ - 1):
        for i in range(nx_ - 1):
            xm, zm = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if gx0 < xm < gx1 and gz0 < zm < gz1: continue
            a, b, c_, d = j * nx_ + i, j * nx_ + i + 1, (j + 1) * nx_ + i, (j + 1) * nx_ + i + 1
            tris += [a, c_, b, b, c_, d]
    print(f"far land: {nx_} x {nz_} points, {len(tris) // 3} triangles; out to {xs[0]:.0f}..{xs[-1]:.0f}, {zs[0]:.0f}..{zs[-1]:.0f}")

    # ---- landmarks
    def at(lat, lon):
        e, n = HZ.en(lat, lon); x, z = world_of_en(np.array(e), np.array(n))
        h = float(HZ.height(np.array([e]), np.array([n]))[0]); d = math.hypot(x - cx, z - cz)
        return float(x), float(z), h - post_h - d ** 2 / (2 * R_EFF)
    tr = at(50.8925, -0.7577)
    masts = []
    for dx, dz, hgt in ((-30.0, 8.0, 46.0), (32.0, -10.0, 38.0)):       # the Trundle's two masts, about 40-50 m
        masts.append([round(tr[0] + dx, 1), round(tr[1] + dz, 1), round(tr[2], 1), hgt])
    cath = at(50.8364, -0.7811)
    landmarks = {"masts": masts, "cathedral": [round(cath[0], 1), round(cath[1], 1), round(cath[2], 1)]}
    print("Trundle at", [round(v) for v in tr], " cathedral at", [round(v) for v in cath])

    # ---- the panorama, from over the course's middle at a camera's height
    pe, pn = en_of_world(np.array(450.0), np.array(10.0))           # on the straight, by the stands
    eye = float(HZ.height(np.array([pe]), np.array([pn]))[0]) + 12.0
    pano(pe, pn, eye)

    out = {"_about": "Goodwood's far land (tools/course/goodwood/farland.py): a mesh on the real ground beyond the ground grid "
                     "(rectilinear: x lines xs, z lines zs; y metres against the post, the earth's curve taken off; colours sRGB "
                     "0-255; every cell drawn but those whose middle is inside 'hole', the ground grid), landmarks, and the panorama hung round the camera beyond it.",
           "xs": [round(float(v), 1) for v in xs], "zs": [round(float(v), 1) for v in zs],
           "y": [round(float(v), 1) for v in Y.ravel()],
           "colour": [int(round(min(1, max(0, v)) * 255)) for v in col.ravel()],
           "hole": [gx0, gz0, gx1, gz1],
           "landmarks": landmarks,
           "panorama": {"colour": "goodwood-far-colour.png", "haze": "goodwood-far-haze.png", "lo": PANO_LO, "hi": PANO_HI,
                        "east": [round(float(LY.XH[0]), 5), round(float(LY.ZH[0]), 5)],
                        "north": [round(float(LY.XH[1]), 5), round(float(LY.ZH[1]), 5)],
                        "note": "column 0 = due north, clockwise; rows from hi (top) to lo (bottom) degrees above level"},
           "cameraFar": 14000}
    (OUT / "goodwood-farland.json").write_text(json.dumps(out, separators=(",", ":")))
    print("wrote goodwood-farland.json", round((OUT / "goodwood-farland.json").stat().st_size / 1024), "KB")


def pano(x0, y0, z0):
    """cast every column's bearing across the real ground beyond PANO_FROM; paint each pixel with what it sees"""
    from PIL import Image
    dist = np.concatenate([np.arange(PANO_FROM, 20000, 60), np.arange(20000, 62000, 150)])
    b = np.radians((np.arange(PANO_W) + 0.5) / PANO_W * 360.0)
    X = x0 + np.outer(np.sin(b), dist); Y = y0 + np.outer(np.cos(b), dist)
    fx0, fx1 = HZ.FAR["x0"], HZ.FAR["x0"] + HZ.FAR["step"] * (HZ.FAR["nx"] - 1)
    fy0, fy1 = HZ.FAR["y0"], HZ.FAR["y0"] + HZ.FAR["step"] * (HZ.FAR["ny"] - 1)
    ok = (X > fx0) & (X < fx1) & (Y > fy0) & (Y < fy1)
    h = HZ.height(X.ravel(), Y.ravel()).reshape(X.shape); s = HZ.sea(X.ravel(), Y.ravel()).reshape(X.shape) & (h <= 1.0)
    h = np.where(s, 0.0, h)
    ang = np.degrees(np.arctan2(h - z0 - dist[None, :] ** 2 / (2 * R_EFF), dist[None, :]))
    ang[~ok] = -90.0
    cm = np.maximum.accumulate(ang, axis=1)                  # the highest angle reached by each distance
    rows = PANO_HI - (np.arange(PANO_H) + 0.5) / PANO_H * (PANO_HI - PANO_LO)
    rgb = np.zeros((PANO_H, PANO_W, 3)); alpha = np.zeros((PANO_H, PANO_W)); haze = np.zeros((PANO_H, PANO_W))
    rowstep = (PANO_HI - PANO_LO) / PANO_H
    # fields: a patchwork by where the ray lands (squares of about 600 m), two tones and the odd wood
    patch = ((np.floor(X / 640).astype(int) * 7919 + np.floor(Y / 560).astype(int) * 104729) % 1000)
    for c in range(PANO_W):
        k = np.searchsorted(cm[c], rows)                    # the nearest distance whose ground reaches up to the row's angle
        seen = k < len(dist); kk = np.minimum(k, len(dist) - 1)
        top = cm[c, -1]
        cover = np.clip((top - rows) / rowstep + 0.5, 0, 1)  # the skyline's pixel: partly covered
        d = dist[kk]; sea = s[c, kk]; p = patch[c, kk]
        land = np.where((p % 7 == 0)[:, None], np.array(COL["wood2"]), np.where((p % 3 == 0)[:, None], np.array(COL["farm2"]), np.array(COL["farm"])))
        c3 = np.where(sea[:, None], np.array(COL["sea"]), land)
        c3[k == 0] = np.array(COL["farm"])                  # (below the nearest ground it shows: the far land's mesh is there)
        rgb[:, c] = c3; alpha[:, c] = np.where(seen, cover, 0.0)
        haze[:, c] = np.clip(0.7 + 0.24 * (1 - np.exp(-(d - PANO_FROM) / 14000.0)), 0, 0.95)
    # Portsmouth's Spinnaker Tower (170 m), a thin pale needle on the far side of the water
    sx, sy = HZ.en(50.7955, -1.1086); dd = math.hypot(sx - x0, sy - y0); bb = (math.degrees(math.atan2(sx - x0, sy - y0)) + 360) % 360
    a0 = math.degrees(math.atan2(0 - z0 - dd ** 2 / (2 * R_EFF), dd)); a1 = math.degrees(math.atan2(170 - z0 - dd ** 2 / (2 * R_EFF), dd))
    col_ = int(bb / 360 * PANO_W)
    for r in range(PANO_H):
        if a0 <= rows[r] <= a1:
            w = 1.0 if rows[r] < a0 + (a1 - a0) * 0.75 else 0.6
            for cc, f in ((col_, 1.0), (col_ + 1, 0.5 * w)):
                rgb[r, cc] = rgb[r, cc] * (1 - f * alpha[r, cc]) + np.array([0.9, 0.9, 0.92]) * f * max(alpha[r, cc], 0) + np.array([0.9, 0.9, 0.92]) * f * (1 - alpha[r, cc])
                alpha[r, cc] = max(alpha[r, cc], f); haze[r, cc] = 0.75
    img = np.dstack([rgb, alpha])
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGBA").save(OUT / "goodwood-far-colour.png", optimize=True)
    Image.fromarray((haze * 255).astype(np.uint8), "L").save(OUT / "goodwood-far-haze.png", optimize=True)
    # for checking: hazed towards a pale haze, over a pale sky, the middle 360 degrees shown in two strips
    hz = np.array([0.94, 0.92, 0.86])
    show = rgb * (1 - haze[..., None]) + hz * haze[..., None]
    sky = np.ones_like(show) * np.array([0.86, 0.9, 0.94])
    show = show * alpha[..., None] + sky * (1 - alpha[..., None])
    half = PANO_W // 2
    both = np.concatenate([show[:, :half], np.ones((12, half, 3)), show[:, half:]], 0)
    Image.fromarray((np.clip(both, 0, 1) * 255).astype(np.uint8)).resize((half // 2, both.shape[0] * 2)).save(REPO / "reference/goodwood/renders/far-panorama.png")
    print("panorama: eye", round(z0, 1), "m; sea in", round(float(np.mean(s.any(axis=1))) * 100), "% of bearings")
    for f in ("goodwood-far-colour.png", "goodwood-far-haze.png"):
        print("wrote", f, round((OUT / f).stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main()
