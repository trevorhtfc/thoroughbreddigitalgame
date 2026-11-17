"""Goodwood: what the cameras see on the horizon (the long-range scenery study, 17 Nov 2026).

Owner, 17 Nov: "then we need to figure out how we create the more longer range scenery that is iconic with goodwood".

From a few viewpoints round the course, this casts a ray every half degree of compass bearing across the real ground
(reference/goodwood/dem-course-20m.json near to, dem-region-400m.json out to about 60 km, with the earth's curve and
normal refraction) and keeps what can be seen: for every bearing, which ground shows at which angle above or below the
level, how far off it is, and whether it is sea. It draws each view as a panorama, coloured by distance (the nearer
ground greener, the far hills paler and bluer, the sea blue), with the landmarks named, and a map of the region.

Writes  reference/goodwood/horizon-<view>.png       the panoramas
        reference/goodwood/region-map.png           the region: the Downs, the coastal plain, the Solent, the Isle of Wight
        reference/goodwood/horizon-bands.json       per view and bearing, the skyline of each distance band (for building
                                                    the far scenery later)

  python3 tools/course/goodwood/horizon.py
"""
import json, math
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[3]
NEAR = json.loads((REPO / "reference/goodwood/dem-course-20m.json").read_text())
FAR = json.loads((REPO / "reference/goodwood/dem-region-400m.json").read_text())
HN = np.array(NEAR["h_dm"], float) / 10.0
HF = np.array(FAR["h"], float)
LAT0, LON0 = NEAR["lat0"], NEAR["lon0"]
KX, KY = 111320.0 * math.cos(math.radians(LAT0)), 110574.0
R_EFF = 6371000.0 / (1 - 0.13)                     # the earth's radius, with normal refraction

def en(lat, lon): return np.array([(lon - LON0) * KX, (lat - LAT0) * KY])

def bil(H, g, x, y):
    fx, fy = (x - g["x0"]) / g["step"], (y - g["y0"]) / g["step"]
    i = np.clip(np.floor(fx).astype(int), 0, g["nx"] - 2); j = np.clip(np.floor(fy).astype(int), 0, g["ny"] - 2)
    a = np.clip(fx - i, 0, 1); b = np.clip(fy - j, 0, 1)
    return (H[j, i] * (1 - a) + H[j, i + 1] * a) * (1 - b) + (H[j + 1, i] * (1 - a) + H[j + 1, i + 1] * a) * b

def height(x, y):
    """ground (m) at east/north x, y: the 20 m grid where it reaches, eased into the 400 m one at its edges"""
    hf = bil(HF, FAR, x, y)
    nx0, nx1 = NEAR["x0"], NEAR["x0"] + NEAR["step"] * (NEAR["nx"] - 1)
    ny0, ny1 = NEAR["y0"], NEAR["y0"] + NEAR["step"] * (NEAR["ny"] - 1)
    inside = (x > nx0) & (x < nx1) & (y > ny0) & (y < ny1)
    edge = np.minimum.reduce([x - nx0, nx1 - x, y - ny0, ny1 - y])
    w = np.clip(edge / 200.0, 0, 1) * inside
    hn = bil(HN, NEAR, np.clip(x, nx0, nx1), np.clip(y, ny0, ny1))
    return hn * w + hf * (1 - w)

def sea(x, y):
    fx, fy = (x - FAR["x0"]) / FAR["step"], (y - FAR["y0"]) / FAR["step"]
    i = np.clip(np.round(fx).astype(int), 0, FAR["nx"] - 1); j = np.clip(np.round(fy).astype(int), 0, FAR["ny"] - 1)
    return HF[j, i] < 0

# viewpoints: (name, lat, lon, eye height above the ground, what it stands for)
VIEWS = [
    ("stands", 50.89205, -0.74470, 18.0, "the top of the March Stand, looking out over the course (the TV gantry's height)"),
    ("post", 50.89235, -0.74578, 4.0, "the winning post, a camera on the rail"),
    ("loop-top", 50.90190, -0.73760, 6.0, "the top of the loop, a tracking camera"),
    ("east-end", 50.89510, -0.72900, 6.0, "the far end of the straight (the 6f start)"),
]
LANDMARKS = [
    ("The Trundle (St Roche's Hill)", 50.8925, -0.7577), ("Chichester Cathedral", 50.8364, -0.7811),
    ("Chichester Harbour", 50.805, -0.88), ("Bognor Regis", 50.783, -0.676), ("Selsey Bill", 50.723, -0.789),
    ("Isle of Wight: St Boniface Down", 50.603, -1.199), ("Isle of Wight: Culver Down", 50.667, -1.098),
    ("Portsmouth, Spinnaker Tower", 50.7955, -1.1086), ("Portsdown Hill", 50.856, -1.08),
    ("Butser Hill", 50.977, -0.982), ("Kingley Vale / Bow Hill", 50.900, -0.83), ("Levin Down", 50.917, -0.737),
    ("Duncton Down", 50.945, -0.64), ("Halnaker windmill", 50.8746, -0.7158), ("Goodwood House", 50.8768, -0.7348),
    ("Blackdown", 51.058, -0.694), ("Goodwood Aerodrome", 50.8597, -0.7600),
]

STEP_DEG = 0.5
def cast(x0, y0, eye):
    """per bearing: the visible ground as a list of (angle above level (deg), distance (m), is-sea), nearest first"""
    z0 = float(height(np.array([x0]), np.array([y0]))[0]) + eye
    dist = np.concatenate([np.arange(30, 1500, 10), np.arange(1500, 8000, 40), np.arange(8000, 62000, 150)])
    bearings = np.arange(0, 360, STEP_DEG)
    out = []
    for b in bearings:
        t = math.radians(b)
        x = x0 + dist * math.sin(t); y = y0 + dist * math.cos(t)
        ok = (x > FAR["x0"]) & (x < FAR["x0"] + FAR["step"] * (FAR["nx"] - 1)) & (y > FAR["y0"]) & (y < FAR["y0"] + FAR["step"] * (FAR["ny"] - 1))
        h = height(x, y); s = sea(x, y); h = np.where(s, 0.0, h)
        ang = np.degrees(np.arctan2(h - z0 - dist ** 2 / (2 * R_EFF), dist))
        ang[~ok] = -90
        best = -90.0; vis = []
        for k in range(len(dist)):
            if ang[k] > best:
                vis.append((ang[k], dist[k], bool(s[k]))); best = ang[k]
        out.append(vis)
    return bearings, out, z0

def band_skylines(vis_all, edges=(0, 600, 2500, 8000, 20000, 70000)):
    """for each distance band, the highest visible angle on each bearing (None where nothing in the band shows)"""
    res = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        res.append([max([a for a, d, s in vis if lo <= d < hi], default=None) for vis in vis_all])
    return res

def colour(d, s):
    if s: return np.array([0.55, 0.70, 0.82]) * (1 - min(d / 60000, 1) * 0.3) + np.array([0.86, 0.88, 0.9]) * min(d / 60000, 1) * 0.3
    near, far = np.array([0.38, 0.55, 0.30]), np.array([0.80, 0.84, 0.90])
    k = min(math.log10(max(d, 100) / 100) / math.log10(600), 1.0)
    return near * (1 - k) + far * k

def panorama(name, lat, lon, eye, what):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x0, y0 = en(lat, lon)
    bearings, vis_all, z0 = cast(x0, y0, eye)
    H, W = 420, len(bearings)
    top, bot = 4.0, -6.0                                          # degrees above / below the level
    img = np.ones((H, W, 3)) * np.array([0.93, 0.91, 0.88])
    rows = lambda a: int(np.clip((top - a) / (top - bot) * (H - 1), 0, H - 1))
    for c, vis in enumerate(vis_all):
        # paint from the far ground to the near, each surface from its angle down to the next nearer one
        prev = H - 1
        seq = sorted(vis, key=lambda v: v[0])                   # by angle: lowest (nearest visible) first
        for k, (a, d, s) in enumerate(seq):
            r = rows(a)
            img[r:prev + 1, c] = colour(d, s)
            prev = r
        # the sky above the skyline: a soft gradient
        img[:prev, c] = np.array([0.93, 0.91, 0.88]) * 0.6 + np.array([0.72, 0.80, 0.90]) * 0.4
    fig, ax = plt.subplots(figsize=(18, 4.6), dpi=110)
    ax.imshow(img, extent=[0, 360, bot, top], aspect="auto", interpolation="bilinear")
    ax.axhline(0, color="#999", lw=0.5, ls=":")
    for lname, la, lo in LANDMARKS:
        p = en(la, lo) - np.array([x0, y0]); dd = float(np.hypot(*p))
        if dd < 150: continue
        b = (math.degrees(math.atan2(p[0], p[1])) + 360) % 360
        k = int(round(b / STEP_DEG)) % len(bearings)
        hh = float(height(np.array([x0 + p[0]]), np.array([y0 + p[1]]))[0])
        a = math.degrees(math.atan2(max(hh, 0) - z0 - dd ** 2 / (2 * R_EFF), dd))
        visible = any(abs(d - dd) < max(400, dd * 0.03) for _, d, _ in vis_all[k]) or a >= max([v[0] for v in vis_all[k]], default=-90) - 0.02
        ax.plot([b, b], [a, a + 0.9], color="#333" if visible else "#aaa", lw=0.6)
        ax.text(b, a + 1.0, f"{lname}\n{dd / 1000:.1f} km" + ("" if visible else " (hidden)"), fontsize=6.5, ha="center",
                va="bottom", color="#222" if visible else "#999", rotation=0)
    for b, lab in [(0, "N"), (45, "NE"), (90, "E"), (135, "SE"), (180, "S"), (225, "SW"), (270, "W"), (315, "NW"), (360, "N")]:
        ax.text(b, bot + 0.2, lab, ha="center", fontsize=8, fontweight="bold")
    ax.set_xticks(np.arange(0, 361, 15)); ax.tick_params(labelsize=7)
    ax.set_ylabel("degrees above level", fontsize=8)
    ax.set_title(f"Goodwood, the view all round from {what} (eye {z0:.0f} m above sea). Heights x1 (true angles); "
                 "colour by distance: green near, paler and bluer far off, blue = sea", fontsize=9, loc="left")
    fig.tight_layout(); fig.savefig(REPO / f"reference/goodwood/horizon-{name}.png", facecolor="white"); plt.close(fig)
    return bearings, vis_all, z0

def region_map(views):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource, LinearSegmentedColormap
    x = FAR["x0"] + np.arange(FAR["nx"]) * FAR["step"]; y = FAR["y0"] + np.arange(FAR["ny"]) * FAR["step"]
    land = np.where(HF < 0, np.nan, HF)
    cmap = LinearSegmentedColormap.from_list("d", ["#8fb27a", "#b8c98c", "#dcd6a0", "#c9b48a", "#a88f6a"])
    ls = LightSource(azdeg=315, altdeg=40)
    rgb = ls.shade(np.nan_to_num(land, nan=0), cmap=cmap, vert_exag=6, blend_mode="soft", vmin=0, vmax=280)
    rgb = rgb[..., :3]; rgb[HF < 0] = [0.68, 0.80, 0.88]
    fig, ax = plt.subplots(figsize=(14, 9.6), dpi=120)
    ax.imshow(rgb, origin="lower", extent=[x[0] / 1000, x[-1] / 1000, y[0] / 1000, y[-1] / 1000], interpolation="bicubic")
    ax.contour(x / 1000, y / 1000, land, levels=[50, 100, 150, 200, 250], colors="#5a4a32", linewidths=0.35, alpha=0.6)
    for lname, la, lo in LANDMARKS:
        p = en(la, lo) / 1000; ax.plot(*p, "o", ms=3, color="#333"); ax.text(p[0] + 0.5, p[1] + 0.3, lname, fontsize=7)
    c = en(50.8955, -0.7380) / 1000
    ax.plot(*c, "s", ms=8, color="#c0392b"); ax.text(c[0] + 0.6, c[1] - 1.4, "GOODWOOD RACECOURSE", fontsize=8.5, fontweight="bold", color="#c0392b")
    for r in [5, 10, 20, 40]:
        t = np.linspace(0, 2 * np.pi, 200); ax.plot(c[0] + r * np.sin(t), c[1] + r * np.cos(t), color="#c0392b", lw=0.4, ls=":")
        ax.text(c[0] + r * 0.71, c[1] + r * 0.71, f"{r} km", fontsize=7, color="#c0392b")
    ax.set_xlabel("km east", fontsize=8); ax.set_ylabel("km north", fontsize=8); ax.tick_params(labelsize=7)
    ax.set_title("Goodwood in its landscape: the South Downs (the racecourse on their southern ridge), the coastal plain, "
                 "Chichester Harbour, the Solent and the Isle of Wight. North up; AWS Terrain Tiles", fontsize=9.5, loc="left")
    fig.tight_layout(); fig.savefig(REPO / "reference/goodwood/region-map.png", facecolor="white"); plt.close(fig)

def main():
    data = {"_about": "Per viewpoint and bearing (every 0.5 deg from north, clockwise), the skyline angle (degrees above level) of the "
                      "visible ground in each distance band, None where none of that band shows. Built by tools/course/goodwood/"
                      "horizon.py from the AWS Terrain Tiles.", "bands_m": [0, 600, 2500, 8000, 20000, 70000], "views": {}}
    for name, lat, lon, eye, what in VIEWS:
        b, vis, z0 = panorama(name, lat, lon, eye, what)
        sea_seen = [round(float(bb), 1) for bb, v in zip(b, vis) if any(s for _, _, s in v)]
        data["views"][name] = {"lat": lat, "lon": lon, "eyeM": round(z0, 1), "what": what,
                               "skylines": [[None if a is None else round(float(a), 3) for a in band] for band in band_skylines(vis)],
                               "seaBearings": [min(sea_seen), max(sea_seen)] if sea_seen else None}
        print(f"{name:9s} eye {z0:5.1f} m; sea seen on bearings {data['views'][name]['seaBearings']}")
    (REPO / "reference/goodwood/horizon-bands.json").write_text(json.dumps(data, separators=(",", ":")))
    region_map(VIEWS)

if __name__ == "__main__":
    main()
