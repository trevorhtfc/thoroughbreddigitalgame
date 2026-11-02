"""Paint racing silks: 3D jacket textures and 2D racecard icons from one description.

    python make_silks.py <silks.json> <out_dir> [texture_size]

Writes, for every set of silks in silks.json:
    <out_dir>/textures/<id>.png   texture for the 3D jockey (layout below)
    <out_dir>/icons/<id>.png      flat front-view icon, racecard style
plus the same for the pattern catalogue (catalogue-*.png) and the zone test
(zones.png), and <out_dir>/catalogue.json listing them.

Both outputs use the same pattern functions, so the icon and the 3D jacket
always agree.

Texture layout (matches tools/blender/repattern_jacket.py), rows from the top:
    0.00-0.50  body          u: 0 right side seam, .25 chest centre, .5 left side,
                                .75 back centre; v: 0 waist .. 1 collar
    0.52-0.70  left sleeve   u: round the arm (0 outside); v: 0 shoulder .. 1 cuff
    0.72-0.90  right sleeve  same as left
    0.92-1.00  cap           u: round the crown (.5 peak, .75 jockey's left); v: 0 top .. 1 rim

Garment terms used by the patterns: L runs across the body from the jockey's
right side (-1) to his left side (+1), the same on front and back; h runs
from the waist (0) to the collar (1). A sash goes from the left shoulder to
the right hip on the front and carries on across the back.
"""
import json, sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROWS = {"body": (0.00, 0.50), "left": (0.52, 0.70), "right": (0.72, 0.90), "cap": (0.92, 1.00)}
SS = 3

BODY_PATTERNS = ["plain", "hoops", "stripes", "sash", "crossbelts", "chevron", "inverted chevron", "chevrons",
                 "braces", "halved", "quartered", "spots", "large spots", "disc", "star", "diamond",
                 "epaulets", "panel", "seams", "check", "hooped band"]
SLEEVE_PATTERNS = ["plain", "hoops", "stripes", "halved", "chevrons", "armlets", "cuffs", "spots", "diabolo", "seams"]
CAP_PATTERNS = ["plain", "quartered", "halved", "striped", "hooped", "spots", "star", "diamond", "peak"]


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def spots(x, y, r):
    row = np.floor(y)
    xs = x + 0.5 * (row % 2)
    return np.hypot(xs - np.floor(xs) - 0.5, y - row - 0.5) < r


def star(px, py, r):
    ang = np.arctan2(px, py)
    k = (ang % (2 * math.pi / 5)) - math.pi / 5
    inner = 0.42
    edge = r * (inner + (1 - inner) * (np.abs(k) / (math.pi / 5)) ** 1.6)
    return np.hypot(px, py) < np.maximum(edge, r * inner)


# ---------------- masks: True where the second colour goes ----------------
# Physical proportions: how tall one unit of h is compared with one unit of L
# (half the body's width). Round shapes use these so circles stay round on both
# the 3D jacket (crouched jockey, front about as tall as it is wide) and the
# taller racecard icon.
ASPECT_3D = {"body": 1.9, "sleeve": 1.0}
ASPECT_ICON = {"body": 3.6, "sleeve": 3.0}


def body_mask(pattern, u, h, asp=1.9):
    a = (u - 0.25) % 1.0
    a = np.where(a > 0.5, a - 1.0, a)                         # -0.5..0.5, 0 = chest centre
    front = np.abs(a) <= 0.25
    L = np.where(front, a / 0.25, np.sign(a) * (0.5 - np.abs(a)) / 0.25)
    p = pattern or "plain"
    if p == "plain": return np.zeros_like(u, bool)
    if p == "hoops": return (np.floor(h * 8) % 2) == 1
    if p == "hooped band": return (h > 0.42) & (h < 0.62)
    if p == "stripes": return (np.floor(u * 24) % 2) == 1
    if p == "sash": return np.abs(L - (2 * h - 1)) < 0.34
    if p == "crossbelts": return (np.abs(L - (2 * h - 1)) < 0.26) | (np.abs(L + (2 * h - 1)) < 0.26)
    if p == "chevron": return np.abs(h - (0.25 + 0.78 * np.abs(L))) < 0.15
    if p == "inverted chevron": return np.abs(h - (0.95 - 0.7 * np.abs(L))) < 0.15
    if p == "chevrons": return (np.floor((h - 0.6 * np.abs(L)) * 5) % 2) == 1
    if p == "braces": return np.abs(np.abs(L) - 0.5) < 0.12
    if p == "halved": return L > 0
    if p == "quartered": return (L > 0) ^ (h > 0.5)
    Y = (h - 0.5) * asp                                       # height in half-widths, 0 at mid-body
    if p == "spots": return spots(u * 4 * 2.6, (Y + 10) * 2.6, 0.27)
    if p == "large spots": return spots(u * 4 * 1.25, (Y + 10) * 1.25, 0.3)
    if p == "disc": return np.hypot(L, Y) < 0.62
    if p == "star": return star(L, Y, 0.75)
    if p == "diamond": return (np.abs(L) * 1.3 + np.abs(Y)) < 0.85
    if p == "epaulets":                                       # pointed bands hanging from each shoulder
        band = np.abs(np.abs(L) - 0.6)
        return (band < 0.22) & (h > 0.45 + 0.8 * band)
    if p == "panel": return (np.abs(L) < 0.45) & (h > 0.12) & (h < 0.88)
    if p == "seams": return (np.abs(np.abs(L) - 1) < 0.07) | (h > 0.95)
    if p == "check": return ((np.floor(u * 16) + np.floor(h * 6)) % 2) == 1
    raise ValueError("unknown body pattern: %s" % p)


def sleeve_mask(pattern, u, t, asp=1.0):
    p = pattern or "plain"
    if p == "plain": return np.zeros_like(u, bool)
    if p == "hoops": return (np.floor(t * 7) % 2) == 1
    if p == "stripes": return (np.floor(u * 8) % 2) == 1
    if p == "halved": return t > 0.5                         # upper arm first colour, lower arm second
    if p == "chevrons": return (np.floor(t * 5 + np.abs(((u + 0.5) % 1.0) - 0.5) * 2.0) % 2) == 1
    if p == "armlets": return (t > 0.45) & (t < 0.6)
    if p == "cuffs": return t > 0.84
    if p == "spots": return spots(u * 6, t * 6 * asp, 0.27)
    if p == "diabolo": return np.abs(((u + 0.5) % 1.0) - 0.5) < (0.12 + 0.2 * np.abs(t - 0.5))
    if p == "seams": return np.abs(((u + 0.25) % 0.5) - 0.25) < 0.03
    raise ValueError("unknown sleeve pattern: %s" % p)


def cap_mask(pattern, u, v):
    p = pattern or "plain"
    if p == "plain": return np.zeros_like(u, bool)
    if p == "quartered": return (np.floor(((u + 0.125) % 1.0) * 4) % 2) == 1
    if p == "halved": return u > 0.5                         # jockey's left half second colour
    if p == "striped": return (np.floor(u * 12) % 2) == 1
    if p == "hooped": return (np.floor(v * 5) % 2) == 1
    if p == "spots": return spots(u * 8, v * 2.2, 0.27)
    if p == "star": return star((u - 0.5) * 3.2, (0.55 - v) * 1.1, 0.42)
    if p == "diamond": return (np.abs(u - 0.5) * 3.2 + np.abs(v - 0.5) * 1.3) < 0.45
    if p == "peak": return (v > 0.85) & (np.abs(u - 0.5) < 0.18)
    raise ValueError("unknown cap pattern: %s" % p)


# ---------------- 3D texture ----------------
def texture(entry, palette, size=1024):
    S = size * SS
    ys, xs = np.mgrid[0:S, 0:S]
    U, V = (xs + 0.5) / S, (ys + 0.5) / S
    img = np.zeros((S, S, 3))
    col = lambda n: hexrgb(palette[n])
    b, s, c = entry["body"], entry.get("sleeves", entry["body"]), entry.get("cap", entry["body"])

    def fill(row, part, fn, *extra):
        r0, r1 = ROWS[row]
        sel = (V >= r0) & (V < r1)
        lv = (V[sel] - r0) / (r1 - r0)
        img[sel] = col(part["colour"])
        m = fn(part.get("pattern"), U[sel], lv, *extra)
        idx = np.where(sel)
        if m.any():
            img[idx[0][m], idx[1][m]] = col(part["colour2"])

    if entry.get("zones"):                                  # zone test: five flat colours
        z = entry["zones"]
        sel = V < 0.51
        front = np.abs(((U - 0.25 + 0.5) % 1.0) - 0.5) <= 0.25
        img[sel & front] = col(z["body front"])
        img[sel & ~front] = col(z["body back"])
        img[(V >= 0.51) & (V < 0.71)] = col(z["left sleeve"])
        img[(V >= 0.71) & (V < 0.91)] = col(z["right sleeve"])
        img[V >= 0.91] = col(z["cap"])
    else:
        fill("body", b, body_mask, ASPECT_3D["body"])
        fill("left", s, sleeve_mask, ASPECT_3D["sleeve"])
        fill("right", s, sleeve_mask, ASPECT_3D["sleeve"])
        fill("cap", c, cap_mask)
        for (a0, a1), part in (((0.50, 0.52), b), ((0.70, 0.72), s), ((0.90, 0.92), s)):
            img[(V >= a0) & (V < a1)] = col(part["colour"])
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


# ---------------- 2D racecard icon ----------------
# Front view: the jockey faces you, so his left is on your right.
BODY = [(0.30, 0.20), (0.42, 0.16), (0.58, 0.16), (0.70, 0.20), (0.70, 0.88), (0.30, 0.88)]
SLEEVE_R = [(0.30, 0.20), (0.18, 0.28), (0.09, 0.80), (0.21, 0.83), (0.30, 0.46)]   # jockey's right, on your left
SLEEVE_L = [(1 - x, y) for x, y in SLEEVE_R]
CAP_C, CAP_R = (0.50, 0.105), 0.085


def _poly_mask(poly, S):
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in poly], fill=255)
    return np.asarray(m) > 127


def icon(entry, palette, size=200):
    S = size * SS
    ys, xs = np.mgrid[0:S, 0:S]
    X, Y = (xs + 0.5) / S, (ys + 0.5) / S
    img = np.zeros((S, S, 4))
    col = lambda n: np.append(hexrgb(palette[n]), 255)
    b, s, c = entry["body"], entry.get("sleeves", entry["body"]), entry.get("cap", entry["body"])
    z = entry.get("zones")

    def paint(sel, part, fn, u, v, *extra):
        img[sel] = col(part["colour"])
        m = fn(part.get("pattern"), u[sel], v[sel], *extra)
        idx = np.where(sel)
        if m.any():
            img[idx[0][m], idx[1][m]] = col(part["colour2"])

    # sleeves: t from shoulder to cuff along the sleeve, u across the front of the arm
    for poly, outer_x, name in ((SLEEVE_R, 0.0, "right sleeve"), (SLEEVE_L, 1.0, "left sleeve")):
        sel = _poly_mask(poly, S)
        sh = np.array(poly[0]); cuff = (np.array(poly[2]) + np.array(poly[3])) / 2
        ax = cuff - sh
        t = np.clip(((X - sh[0]) * ax[0] + (Y - sh[1]) * ax[1]) / (ax @ ax), 0, 1)
        off = np.clip((X - (sh[0] + t * ax[0])) / 0.07, -1, 1)
        outward = -1.0 if outer_x == 0.0 else 1.0
        u = 0.25 - 0.25 * off * outward                       # 0 outer edge .. .5 inner edge
        if z:
            img[sel] = col(z[name])
        else:
            paint(sel, s, sleeve_mask, u, t, ASPECT_ICON["sleeve"])
    # body
    sel = _poly_mask(BODY, S)
    L = (X - 0.5) / 0.2
    h = (0.88 - Y) / (0.88 - 0.16)
    if z:
        img[sel] = col(z["body front"])
    else:
        paint(sel, b, body_mask, 0.25 + 0.25 * np.clip(L, -1, 1), h, ASPECT_ICON["body"])
    # cap: a dome seen from the front, with a short peak
    cx, cy = CAP_C
    dome = (np.hypot(X - cx, (Y - cy) * 1.15) < CAP_R) & (Y < cy + 0.035)
    peak = (np.abs(X - cx) < CAP_R * 0.9) & (Y >= cy + 0.035) & (Y < cy + 0.06) & (np.abs(X - cx) < CAP_R * 0.9 - (Y - cy - 0.035) * 1.2)
    sel = dome | peak
    u = 0.5 + 0.25 * np.clip((X - cx) / CAP_R, -1, 1)
    v = np.clip((Y - (cy - CAP_R / 1.15)) / (CAP_R / 1.15 + 0.035), 0, 1)
    if z:
        img[sel] = col(z["cap"])
    else:
        paint(sel, c, cap_mask, u, v)
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGBA")
    # outline
    a = im.split()[3]
    edge = a.filter(ImageFilter.MaxFilter(SS * 2 + 1))
    outline = Image.new("RGBA", im.size, (40, 40, 44, 255))
    base = Image.new("RGBA", im.size, (0, 0, 0, 0))
    base.paste(outline, mask=edge)
    base.alpha_composite(im)
    seams = ImageDraw.Draw(base)
    for poly in (BODY, SLEEVE_R, SLEEVE_L):
        seams.line([(x * S, y * S) for x, y in poly] + [(poly[0][0] * S, poly[0][1] * S)], fill=(40, 40, 44, 255), width=SS)
    return base.resize((size, size), Image.LANCZOS)


# ---------------- descriptions ----------------
def describe(entry):
    """Registered-colours style description, e.g. 'Emerald green, pink sash, white sleeves, pink cap'."""
    b, s, c = entry["body"], entry.get("sleeves", entry["body"]), entry.get("cap", entry["body"])
    def two(part): return "%s and %s" % (part["colour"], part["colour2"])
    def body_phrase(p):
        pat = p.get("pattern") or "plain"
        if pat == "plain": return p["colour"].capitalize()
        if pat in ("hoops", "stripes", "halved", "quartered", "check", "chevrons"):
            return ("%s %s" % (two(p), {"check": "check"}.get(pat, pat))).capitalize()
        if pat == "large spots": return "%s, large %s spots" % (p["colour"].capitalize(), p["colour2"])
        return "%s, %s %s" % (p["colour"].capitalize(), p["colour2"], pat)
    def sleeve_phrase(p):
        pat = p.get("pattern") or "plain"
        if pat == "plain": return "%s sleeves" % p["colour"]
        if pat in ("hoops", "stripes", "halved", "chevrons", "diabolo", "seams", "spots"):
            word = {"hoops": "hooped", "stripes": "striped", "chevrons": "chevrons on", "spots": "spotted"}.get(pat, pat)
            return "%s %s sleeves" % (two(p), word) if pat not in ("chevrons",) else "%s sleeves, %s chevrons" % (p["colour"], p["colour2"])
        return "%s sleeves, %s %s" % (p["colour"], p["colour2"], pat)
    def cap_phrase(p):
        pat = p.get("pattern") or "plain"
        if pat == "plain": return "%s cap" % p["colour"]
        if pat in ("quartered", "halved", "striped", "hooped"): return "%s %s cap" % (two(p), pat)
        if pat == "spots": return "%s cap, %s spots" % (p["colour"], p["colour2"])
        return "%s cap, %s %s" % (p["colour"], p["colour2"], pat)
    parts = [body_phrase(b)]
    plain_same = lambda p: (p.get("pattern") or "plain") == "plain" and p["colour"] == b["colour"]
    if not plain_same(s): parts.append(sleeve_phrase(s))
    if not plain_same(c): parts.append(cap_phrase(c))
    return ", ".join(parts)


def catalogue_entries():
    """One demo entry per pattern, in two neutral demo colours."""
    out = []
    base, second = "dark blue", "gold"
    for p in BODY_PATTERNS:
        out.append({"id": "catalogue-body-" + p.replace(" ", "-"), "name": p.capitalize(), "zone": "body", "pattern": p,
                    "body": {"colour": base, "pattern": p, "colour2": second}, "sleeves": {"colour": base}, "cap": {"colour": base}})
    for p in SLEEVE_PATTERNS:
        out.append({"id": "catalogue-sleeves-" + p.replace(" ", "-"), "name": p.capitalize(), "zone": "sleeves", "pattern": p,
                    "body": {"colour": base}, "sleeves": {"colour": base, "pattern": p, "colour2": second}, "cap": {"colour": base}})
    for p in CAP_PATTERNS:
        out.append({"id": "catalogue-cap-" + p.replace(" ", "-"), "name": p.capitalize(), "zone": "cap", "pattern": p,
                    "body": {"colour": base}, "sleeves": {"colour": base}, "cap": {"colour": base, "pattern": p, "colour2": second}})
    return out


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    data = json.load(open(src))
    pal = data["palette"]
    os.makedirs(out_dir + "/textures", exist_ok=True)
    os.makedirs(out_dir + "/icons", exist_ok=True)
    listing = {"silks": [], "catalogue": [], "zones": None}
    for e in data["silks"]:
        texture(e, pal, size).save(f"{out_dir}/textures/{e['id']}.png", optimize=True)
        icon(e, pal).save(f"{out_dir}/icons/{e['id']}.png", optimize=True)
        listing["silks"].append({"id": e["id"], "name": e["name"], "description": describe(e),
                                 "colour": pal[e["body"]["colour"]]})
    for e in catalogue_entries():
        texture(e, pal, size // 2).save(f"{out_dir}/textures/{e['id']}.png", optimize=True)
        icon(e, pal).save(f"{out_dir}/icons/{e['id']}.png", optimize=True)
        listing["catalogue"].append({"id": e["id"], "name": e["name"], "zone": e["zone"], "pattern": e["pattern"],
                                     "colour": pal[e["body"]["colour"]]})
    z = data["zone_test"]
    ze = {"id": "zones", "zones": z, "body": {"colour": z["body front"]}}
    texture(ze, pal, size // 2).save(f"{out_dir}/textures/zones.png", optimize=True)
    icon(ze, pal).save(f"{out_dir}/icons/zones.png", optimize=True)
    listing["zones"] = {"id": "zones", "legend": z, "colours": {k: pal[v] for k, v in z.items()}}
    json.dump(listing, open(f"{out_dir}/catalogue.json", "w"), indent=1)
    print("painted", len(listing["silks"]), "silks,", len(listing["catalogue"]), "catalogue patterns and the zone test")


if __name__ == "__main__":
    main()
