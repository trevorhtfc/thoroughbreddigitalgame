"""Mark up the stand's front elevation renders for sketching (owner, 6 Nov 2026).

    python3 tools/course/annotate_elevation.py

Reads reference/architecture/elevation/_raw_*.png (tools/blender/stand_elevation.py) and courses/ascot.json;
writes ascot-stand-elevation-<sheet>.png and ascot-stand-elevation.pdf in the same folder: a bay grid along
the ground, metres from the winning post, a height scale, the modules named over the top, module joins
as faint dashed lines, and the winning post marked.
"""
import json, os
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(REPO, "reference/architecture/elevation")
META = json.load(open(os.path.join(D, "_raw_meta.json")))
MODS = json.load(open(os.path.join(REPO, "courses/ascot.json")))["grandstand"]["modules"]
BAY = 3.5
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
INK, SOFT, FAINT, ACC = (38, 40, 36), (110, 110, 100), (200, 196, 184), (176, 64, 48)
NAMES = {"terrace_stand": "Terrace stand", "clock_centre": "Clock tower and iron bay", "ironwork_bay": "Iron bay",
         "stair_bay": "Stairs", "grand_pavilion": "Grand canopy", "pavilion": "Canopy", "end_pavilion": "End pavilion",
         "porch": "Porch", "veranda_low": "Low veranda"}
TITLES = {"overview": "The whole stand", "east": "East end (left as seen from the track)", "centre": "Centre",
          "west": "Clock tower and west end, by the winning post"}

# runs of one module are one building on the drawing
runs = []
for m in sorted(MODS, key=lambda m: -m["xEast"]):
    if runs and runs[-1]["module"] == m["module"]:
        runs[-1]["xWest"] = m["xWest"]; runs[-1]["bays"] += m["bays"]
    else:
        runs.append(dict(module=m["module"], xEast=m["xEast"], xWest=m["xWest"], bays=m["bays"]))

pages = []
for sheet, M in META.items():
    raw = Image.open(os.path.join(D, f"_raw_{sheet}.png")).convert("RGBA")
    k = M["pxPerMetre"]; s = k / 32                      # text scale
    L, T, R, B = int(130 * s + 40), int(250 * s + 40), int(60 * s + 20), int(210 * s + 40)
    W, H = raw.width + L + R, raw.height + T + B
    img = Image.new("RGB", (W, H), "white")
    img.paste(raw, (L, T), raw)
    d = ImageDraw.Draw(img)
    f = lambda sz, b=False: ImageFont.truetype(BOLD if b else FONT, max(9, int(sz * s)))
    X = lambda x: L + (M["xEast"] - x) * k                # east on the left
    Z = lambda z: T + (M["zHi"] - z) * k
    g = Z(0)
    # module joins and names
    for r in runs:
        xa, xb = max(r["xWest"], M["xWest"]), min(r["xEast"], M["xEast"])
        if xb <= xa: continue
        pa, pb = X(xb), X(xa)
        for x in (r["xEast"], r["xWest"]):
            if M["xWest"] <= x <= M["xEast"]:
                px = X(x)
                for y in range(int(T - 60 * s), int(g), int(14 * s) + 2):
                    d.line([(px, y), (px, y + 7 * s)], fill=FAINT, width=max(1, int(2 * s)))
        yb = T - 70 * s
        d.line([(pa + 3, yb), (pb - 3, yb)], fill=INK, width=max(1, int(2 * s)))
        for px in (pa + 3, pb - 3):
            d.line([(px, yb - 10 * s), (px, yb + 10 * s)], fill=INK, width=max(1, int(2 * s)))
        label = f"{NAMES.get(r['module'], r['module'])}"
        sub = f"{r['bays']} bay{'s' if r['bays'] != 1 else ''} · {r['bays'] * BAY:.1f} m"
        for txt, ff, dy in ((label, f(22, True), -46), (sub, f(17), -22)):
            tw = d.textlength(txt, font=ff)
            if tw < (pb - pa) - 6:
                d.text(((pa + pb) / 2 - tw / 2, yb + dy * s - 4), txt, fill=INK if dy < -30 else SOFT, font=ff)
            elif dy < -30 and (pb - pa) > 30 * s:              # narrow: the short name, upright
                short = label.split()[0]
                tw = d.textlength(short, font=f(17, True))
                if tw < (pb - pa) - 4:
                    d.text(((pa + pb) / 2 - tw / 2, yb - 30 * s), short, fill=INK, font=f(17, True))
    # ground line, bay ticks, metres from the winning post
    d.line([(L - 20 * s, g), (W - R + 10 * s, g)], fill=INK, width=max(1, int(3 * s)))
    step = 25 if sheet == "overview" else 10
    x = int(M["xWest"] // BAY) * BAY
    while x <= M["xEast"]:
        px = X(x)
        if L <= px <= W - R:
            d.line([(px, g), (px, g + 12 * s)], fill=SOFT, width=1)
        x += BAY
    m = int(M["xWest"] // step) * step
    while m <= M["xEast"]:
        px = X(m)
        if L <= px <= W - R:
            d.line([(px, g), (px, g + 30 * s)], fill=INK, width=max(1, int(2 * s)))
            t = f"{abs(m)} m" + ("" if m == 0 else " E" if m > 0 else " W")
            tw = d.textlength(t, font=f(18))
            d.text((px - tw / 2, g + 36 * s), t, fill=INK, font=f(18))
        m += step
    if M["xWest"] <= 0 <= M["xEast"]:                       # the winning post
        px = X(0)
        d.line([(px, g + 64 * s), (px, Z(M["zHi"] - 2))], fill=ACC, width=max(1, int(2 * s)))
        t = "WINNING POST (clock tower opposite)"
        d.text((px + 8 * s, g + 66 * s), t, fill=ACC, font=f(18, True))
    # height scale
    for z in range(0, int(M["zHi"]) + 1, 5):
        py = Z(z)
        d.line([(L - 28 * s, py), (L - 12 * s, py)], fill=INK, width=max(1, int(2 * s)))
        t = f"{z} m"; tw = d.textlength(t, font=f(16))
        d.text((L - 34 * s - tw, py - 10 * s), t, fill=SOFT, font=f(16))
    d.line([(L - 20 * s, Z(0)), (L - 20 * s, Z(int(M["zHi"]) // 5 * 5))], fill=INK, width=max(1, int(2 * s)))
    # title and notes
    d.text((L, 16 * s + 6), f"Ascot main stand · front elevation · {TITLES[sheet]}", fill=INK, font=f(30, True))
    d.text((L, 56 * s + 8), f"As seen from the track (east on the left). Ticks along the ground every bay (3.5 m), "
           f"numbers in metres from the winning post. Dashed lines: joins between modules. "
           f"Flags, awnings and crowd not shown.", fill=SOFT, font=f(18))
    out = os.path.join(D, f"ascot-stand-elevation-{sheet}.png")
    img.save(out, optimize=True)
    pages.append(img)
    print("wrote", out, img.size)
pages[0].save(os.path.join(D, "ascot-stand-elevation.pdf"), save_all=True, append_images=pages[1:], resolution=150)
print("wrote pdf")
