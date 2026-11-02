"""Paint traditional racing silks into the 3D jacket's texture layout.

    python make_silks.py <silks.json> <out_dir> [size]

Reads each set of silks (body, sleeves, cap: colour + optional pattern and
second colour) and writes <id>.png, laid out to match the UVs made by
tools/blender/repattern_jacket.py:

  rows from the image top
    0.00-0.50  body          u: 0 right seam, .25 chest, .5 left, .75 back; v: waist..collar
    0.52-0.70  left sleeve   u: round the arm;  v: shoulder..cuff
    0.72-0.90  right sleeve  u: round the arm;  v: shoulder..cuff
    0.92-1.00  cap           u: round the crown (.5 = peak); v: top..rim

Patterns are drawn in garment terms (front/back, jockey's left/right,
waist to collar), so a sash runs from the right shoulder to the left hip
on the front and carries on across the back, as on a real jacket.
"""
import json, sys, os, math
import numpy as np
from PIL import Image

ROWS = {"body": (0.00, 0.50), "left": (0.52, 0.70), "right": (0.72, 0.90), "cap": (0.92, 1.00)}
SS = 3   # supersampling for smooth edges


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def star_mask(px, py, r):
    """Five-point star of outer radius r centred on 0,0 (py up)."""
    ang = np.arctan2(px, py)
    rad = np.hypot(px, py)
    k = (ang % (2 * math.pi / 5)) - math.pi / 5
    inner = 0.42
    # radius of the star outline in that direction, by interpolating tip and notch
    edge = r * (inner + (1 - inner) * (np.abs(k) / (math.pi / 5)) ** 1.6)
    return rad < np.maximum(edge, r * inner)


# ---------- body ----------
def body_mask(pattern, u, v):
    """u, v arrays in the body row. Returns True where the second colour goes."""
    a = (u - 0.25) % 1.0                 # 0 chest centre, .25 left, .5 back, .75 right
    a = np.where(a > 0.5, a - 1.0, a)    # -0.5..0.5
    front = np.abs(a) <= 0.25
    # L: across the panel, +1 at the jockey's left side, -1 at his right (front and back alike)
    L = np.where(front, a / 0.25, np.sign(a) * (0.5 - np.abs(a)) / 0.25)
    h = v                                # 0 waist .. 1 collar
    if pattern in (None, "", "plain"):
        return np.zeros_like(u, bool)
    if pattern == "hoops":
        return (np.floor(h * 9) % 2) == 1
    if pattern == "stripes":
        return (np.floor(u * 28) % 2) == 1
    if pattern == "sash":
        return np.abs(L - (1 - 2 * h)) < 0.34
    if pattern == "crossbelts":
        return (np.abs(L - (1 - 2 * h)) < 0.26) | (np.abs(L + (1 - 2 * h)) < 0.26)
    if pattern == "chevron":               # a V from both shoulders to a point low in the centre
        return np.abs(h - (0.18 + 0.8 * np.abs(L))) < 0.14
    if pattern == "inverted chevron":
        return np.abs(h - (0.95 - 0.7 * np.abs(L))) < 0.14
    if pattern == "braces":
        return np.abs(np.abs(L) - 0.5) < 0.13
    if pattern == "halved":                # jockey's left half in the second colour
        return L > 0
    if pattern == "quartered":
        return (L > 0) ^ (h > 0.5)
    if pattern == "spots":
        return spots(u * 14, h * 4.5, 0.27)
    if pattern == "large spots":
        return spots(u * 8, h * 2.6, 0.3)
    if pattern == "disc":
        return (np.hypot(L * 1.0, (h - 0.5) * 1.6) < 0.62)
    if pattern == "star":
        return star_mask(L, (h - 0.5) * 1.6, 0.75)
    if pattern == "diamond":
        return (np.abs(L) + np.abs(h - 0.5) * 1.8) < 0.7
    if pattern == "epaulets":
        return (h > 0.8) & (np.abs(L) > 0.35)
    if pattern == "panel":
        return (np.abs(L) < 0.45) & (h > 0.12) & (h < 0.88)
    if pattern == "seams":
        return (np.abs(np.abs(L) - 1) < 0.07) | (h > 0.95)
    if pattern == "collar and cuffs":
        return h > 0.92
    raise ValueError("unknown body pattern: %s" % pattern)


# ---------- sleeves ----------
def sleeve_mask(pattern, u, t):
    """u round the arm, t from shoulder (0) to cuff (1)."""
    if pattern in (None, "", "plain"):
        return np.zeros_like(u, bool)
    if pattern == "hoops":
        return (np.floor(t * 7) % 2) == 1
    if pattern == "stripes":
        return (np.floor(u * 10) % 2) == 1
    if pattern == "chevrons":
        return (np.floor(t * 5 + np.abs(((u + 0.5) % 1.0) - 0.5) * 2.0) % 2) == 1
    if pattern == "armlets":
        return (t > 0.45) & (t < 0.6)
    if pattern == "cuffs":
        return t > 0.84
    if pattern == "spots":
        return spots(u * 6, t * 6, 0.27)
    if pattern == "diabolo":
        return np.abs(((u + 0.5) % 1.0) - 0.5) < (0.12 + 0.2 * np.abs(t - 0.5))
    raise ValueError("unknown sleeve pattern: %s" % pattern)


# ---------- cap ----------
def cap_mask(pattern, u, v):
    """u round the crown (0.5 = peak at the front), v from the top (0) to the rim (1)."""
    if pattern in (None, "", "plain"):
        return np.zeros_like(u, bool)
    if pattern == "quartered":
        return (np.floor(((u + 0.125) % 1.0) * 4) % 2) == 1
    if pattern == "striped":
        return (np.floor(u * 12) % 2) == 1
    if pattern == "hooped":
        return (np.floor(v * 5) % 2) == 1
    if pattern == "spots":
        return spots(u * 8, v * 2.2, 0.27)
    if pattern == "star":                  # one star on the front of the cap
        du = (u - 0.5) * 3.2
        return star_mask(du, (0.55 - v) * 1.1, 0.42)
    if pattern == "peak":                  # contrasting peak (lowest band at the front)
        return (v > 0.85) & (np.abs(u - 0.5) < 0.18)
    raise ValueError("unknown cap pattern: %s" % pattern)


def spots(x, y, r):
    """Staggered grid of round spots in pattern units."""
    row = np.floor(y)
    xs = x + 0.5 * (row % 2)
    fx, fy = xs - np.floor(xs) - 0.5, y - row - 0.5
    return np.hypot(fx, fy) < r


def paint(entry, palette, size):
    S = size * SS
    img = np.zeros((S, S, 3))
    ys, xs = np.mgrid[0:S, 0:S]
    U = (xs + 0.5) / S
    V = (ys + 0.5) / S
    col = lambda name: hexrgb(palette[name])

    def fill(row, colour, mask_fn, pattern, colour2):
        r0, r1 = ROWS[row]
        sel = (V >= r0) & (V < r1)
        lv = (V[sel] - r0) / (r1 - r0)
        img[sel] = col(colour)
        if pattern:
            m = mask_fn(pattern, U[sel], lv)
            idx = np.where(sel)
            img[idx[0][m], idx[1][m]] = col(colour2)

    b, s, c = entry["body"], entry.get("sleeves", entry["body"]), entry.get("cap", entry["body"])
    # body row: v 0 waist at the top of the row .. 1 collar at the bottom
    fill("body", b["colour"], body_mask, b.get("pattern"), b.get("colour2"))
    fill("left", s["colour"], sleeve_mask, s.get("pattern"), s.get("colour2"))
    fill("right", s["colour"], sleeve_mask, s.get("pattern"), s.get("colour2"))
    fill("cap", c["colour"], cap_mask, c.get("pattern"), c.get("colour2"))
    # fill the gaps between rows with the body colour so filtering at row edges stays clean
    for (a0, a1), name in (((0.50, 0.52), "body"), ((0.70, 0.72), "sleeves"), ((0.90, 0.92), "sleeves")):
        sel = (V >= a0) & (V < a1)
        img[sel] = col((b if name == "body" else s)["colour"])
    out = Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)
    return out


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 1024
    data = json.load(open(src))
    os.makedirs(out_dir, exist_ok=True)
    for e in data["silks"]:
        paint(e, data["palette"], size).save(os.path.join(out_dir, e["id"] + ".png"), optimize=True)
        print("painted", e["id"])


if __name__ == "__main__":
    main()
