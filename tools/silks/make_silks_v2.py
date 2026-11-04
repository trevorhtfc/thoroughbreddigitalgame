"""Paint racing silks for the v2 jockey (racehorse_v2), in its own texture layout.

    python tools/silks/make_silks_v2.py silks/silks.json [size]

Uses exactly the same pattern rules as make_silks.py (imported, not changed), so a set of silks looks
the same on both jockeys; only the layout differs. Writes:
    silks/textures-v2/<id>.png               (plus catalogue-*.png, one per pattern, and zones.png)
    race-view/assets/silks-3d-v2/<id>.png    the web copy

Layout (matches ATLAS in tools/blender/build_racehorse_v2.py), x across, y down from the top:
    body          x 0-1 (wraps round the torso: .25 chest, .75 back)   y 0.00-0.47  (waist -> collar)
    left sleeve   x 0.04-0.30 (round the arm, 0 outside)               y 0.53-0.96  (shoulder -> cuff)
    right sleeve  x 0.37-0.63                                          y 0.53-0.96
    cap           a disc centred (0.82, 0.745), radius 0.155: crown in the middle, rim round the edge,
                  the peak at the bottom of the disc, the jockey's left to the right.
Every zone is painted on past its own edge (the body and sleeves carry on round, the cap's rim colour
carries on outward), so the gutters between zones hold the right colour and nothing bleeds across
when the texture is seen small (mipmaps).
"""
import json, sys, os, math
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_silks as ms                                    # the pattern rules (read only)

BODY = (0.0, 0.0, 1.0, 0.47)
SLEEVES = {"left": (0.04, 0.53, 0.26, 0.43), "right": (0.37, 0.53, 0.26, 0.43)}
CAP = (0.82, 0.745, 0.155)
SS = 3


def texture(entry, palette, size=1024):
    S = size * SS
    ys, xs = np.mgrid[0:S, 0:S]
    X, Y = (xs + 0.5) / S, (ys + 0.5) / S
    col = lambda n: ms.hexrgb(palette[n])
    b, s, c = entry["body"], entry.get("sleeves", entry["body"]), entry.get("cap", entry["body"])
    z = entry.get("zones")
    img = np.zeros((S, S, 3)); img[:] = col(z["body front"] if z else b["colour"])

    def paint(sel, part, fn, u, v, *extra):
        img[sel] = col(part["colour"])
        m = fn(part.get("pattern"), u[sel], v[sel], *extra)
        idx = np.where(sel)
        if m.any():
            img[idx[0][m], idx[1][m]] = col(part["colour2"])

    # body, carried on 0.03 past the collar
    x0, y0, w, h = BODY
    sel = Y < y0 + h + 0.03
    hh = np.clip((Y - y0) / h, 0, 1)
    if z:
        front = np.abs(((X - 0.25 + 0.5) % 1.0) - 0.5) <= 0.25
        img[sel & front] = col(z["body front"]); img[sel & ~front] = col(z["body back"])
    else:
        paint(sel, b, ms.body_mask, X % 1.0, hh, ms.ASPECT_3D["body"])
    # sleeves, carried on 0.03 round each side (periodic) and past each end
    for name, (x0, y0, w, h) in SLEEVES.items():
        sel = (X > x0 - 0.03) & (X < x0 + w + 0.03) & (Y > y0 - 0.03) & (Y < y0 + h + 0.03)
        u = ((X - x0) / w) % 1.0
        t = np.clip((Y - y0) / h, 0, 1)
        if z:
            img[sel] = col(z["left sleeve" if name == "left" else "right sleeve"])
        else:
            paint(sel, s, ms.sleeve_mask, u, t, ms.ASPECT_3D["sleeve"])
    # cap disc, with the rim colour carried on outward
    cx, cy, R = CAP
    dx, dy = X - cx, Y - cy
    rr = np.hypot(dx, dy) / R
    sel = rr < 1.12
    u = (np.arctan2(dx, dy) / (2 * math.pi) + 0.5) % 1.0     # .5 = the peak, .75 = jockey's left
    v = np.clip(rr, 0, 1)
    if z:
        img[sel] = col(z["cap"])
    else:
        paint(sel, c, ms.cap_mask, u, v)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((size, size), Image.LANCZOS)


def main():
    src = sys.argv[1]
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    root = os.path.dirname(os.path.dirname(HERE))
    data = json.load(open(src))
    pal = data["palette"]
    outs = [os.path.join(root, "silks/textures-v2"), os.path.join(root, "race-view/assets/silks-3d-v2")]
    for o in outs:
        os.makedirs(o, exist_ok=True)
    jobs = list(data["silks"]) + ms.catalogue_entries()     # the owners' silks and one of each pattern
    zt = data["zone_test"]
    jobs.append({"id": "zones", "zones": zt, "body": {"colour": zt["body front"]}})
    for e in jobs:
        im = texture(e, pal, size)
        for o in outs:
            im.save(os.path.join(o, e["id"] + ".png"), optimize=True)
    print("painted", len(jobs), "v2 silks textures at", size)


if __name__ == "__main__":
    main()
