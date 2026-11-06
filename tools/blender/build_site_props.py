"""Build the site components that dress the ground round the grandstand.

    python -c "exec(open('tools/blender/build_site_props.py').read())"

Follows reference/architecture/site-components-sheet.png, built the same way as the grandstand:
scripted pieces from tools/blender/kit.py, realistic sizes, chunky but not cartoonish.

Writes assets/models/architecture/site_props.glb        one node per piece, named as below
       assets/models/architecture/site_props_spots.json  per piece: seats and standing spots for crowds
       assets/models/master/site_props.blend

Every piece: origin on the ground at the middle of its footprint; its front (open side, counter,
seats' view) faces -y in Blender, +z in glTF. Place them with courses/ascot-site-dressing.json.

Pieces
  marquee_peaks        three-peak tension marquee, open arched front          24 x 8 m
  marquee_clearspan    glazed frame marquee with a gabled roof                  20 x 9 m
  big_top              round striped tent, centre pole, flag, guy ropes          14 m across
  pagoda_counter       pagoda gazebo with a serving counter                     4 x 4 m
  stand_open           open tiered seating stand with rails and side steps      12 x 6 m
  stand_covered        covered seating stand on posts with arched brackets      10 x 5 m
  terrace_deck         raised deck, cross-rail balustrade, parasols, tables     10 x 7 m
  viewing_tower        raised viewing box on braced legs with a stair           4 x 4 m
  kiosk_awning         kiosk with a scalloped awning and fascia board           4 x 2.6 m
  booth_hut            small gabled booth with a hatch                          2.6 x 2.2 m
  kiosk_row_arched     three barrel-roofed kiosks in a row                      9 x 2.6 m
  pagoda_kiosk         small closed pagoda kiosk with a flag                    2.6 x 2.6 m
  pergola_picnic       timber pergola over three picnic tables                  7.5 x 3.6 m
  picnic_table         one picnic table with benches                            1.8 x 1.6 m
  planter_long         planter with flowers                                     1.8 x 0.6 m
  planter_short        planter with flowers                                     1.0 x 0.6 m
  fence_picket         picket fence panel                                       2.5 m
  fence_cross          cross-rail fence panel                                   2.5 m
  barrier_rail         rounded bar on three posts                               3 m
  signboard            board on truss legs                                      3.2 m wide
  flagpole             pole with a flag                                         7 m high
  banner_flag          pole with a hanging banner                               4.4 m high
  signpost             finger post with three arms                              2.7 m high
"""
import json, math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
OUT_DIR = os.path.join(REPO, "assets/models/architecture")
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())

COL = json.load(open(os.path.join(OUT_DIR, "site_props_colours.json")))
MATS = {k: material("sp_" + k, v, rough={"glass": 0.25, "metal": 0.5}.get(k, 0.85), metal={"metal": 0.4}.get(k, 0.0))
        for k, v in COL.items() if not k.startswith("_")}
LIB = bpy.data.collections.new("site_props")
bpy.context.scene.collection.children.link(LIB)
SPOTS = {}
TRIS = {}


# ------------------------------------------------------------------ extra pieces of kit
def rod(k, mat, p0, p1, r, segs=6):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    g = bmesh.ops.create_cone(k.bm(mat), cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length, matrix=k.M @ m)
    k._smooth(g["verts"])


def revolve(k, mats, cx, cy, profile, segs, offset=0.0):
    """Surface of revolution through (radius, z) points; mats alternates per segment (stripes)."""
    if isinstance(mats, str):
        mats = [mats]
    for s in range(segs):
        a0 = offset + 2 * math.pi * s / segs
        a1 = offset + 2 * math.pi * (s + 1) / segs
        bm = k.bm(mats[s % len(mats)])
        for (r0, z0), (r1, z1) in zip(profile[:-1], profile[1:]):
            pts = [(r0, z0, a0), (r0, z0, a1), (r1, z1, a1), (r1, z1, a0)]
            vs, seen = [], set()
            for r, z, a in pts:
                key = (round(r * math.cos(a), 4), round(r * math.sin(a), 4), round(z, 4))
                if key in seen:
                    continue
                seen.add(key)
                vs.append(bm.verts.new(k.M @ Vector((cx + r * math.cos(a), cy + r * math.sin(a), z))))
            if len(vs) >= 3:
                f = bm.faces.new(vs)
                f.smooth = segs > 8


def tent_profile(R, z_eave, h, ov=0.3, n=7, power=1.9):
    """Tension-tent curve: gentle at the eaves, steep at the peak."""
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((R + ov) * (1 - t), z_eave + h * t ** power))
    return pts


def square_tent(k, cx, cy, half, z_eave, h, mat="canvas"):
    revolve(k, mat, cx, cy, [(r * math.sqrt(2), z) for r, z in tent_profile(half, z_eave, h, 0.3)], 4, math.pi / 4)
    k.cyl("trim", cx, cy, z_eave + h - 0.05, z_eave + h + 0.35, 0.07, 0.05, 8)
    k.sphere("trim", cx, cy, z_eave + h + 0.42, 0.11, 1)


def scallops(k, mat, a, b, z, depth=0.32, r=0.26):
    """A valance with scalloped hem hanging below z along the edge a->b."""
    ax, ay = a; bx, by = b
    L = math.hypot(bx - ax, by - ay)
    k.push(Matrix.Translation((ax, ay, 0)) @ Matrix.Rotation(math.atan2(by - ay, bx - ax), 4, "Z"))
    k.box(mat, 0, L, -0.025, 0.025, z - depth, z)
    n = max(1, round(L / (2 * r)))
    for i in range(n):
        k.arc_band(mat, (i + 0.5) * L / n, z - depth, 0.0, L / n / 2, math.pi, 2 * math.pi, -0.025, 0.025, 6)
    k.pop()


def cloth(k, mat, x, y, z, w, h, wave=0.12, nx=8, ny=4, taper=0.0, along="x"):
    """A waving flag or banner hanging from its top-left corner at (x, y, z)."""
    bm = k.bm(mat)
    grid = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            u, v = i / nx, j / ny
            ww = w * (1 - taper * v) if along == "z" else w
            if along == "x":                      # flag: flies out sideways from a pole
                p = Vector((x + u * w, y + wave * math.sin(u * math.pi * 2.2) * u, z - v * h))
            else:                                 # banner: hangs down from an arm
                p = Vector((x + u * ww + (w - ww) / 2, y + wave * math.sin(v * math.pi * 1.6) * v, z - v * h))
            row.append(bm.verts.new(k.M @ p))
        grid.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.smooth = True


def seat(k, x, y, z):
    k.box("seat", x - 0.21, x + 0.21, y - 0.2, y + 0.18, z + 0.4, z + 0.46)
    k.box("seat", x - 0.21, x + 0.21, y + 0.14, y + 0.2, z + 0.46, z + 0.86)
    k.box("dark", x - 0.04, x + 0.04, y - 0.05, y + 0.05, z, z + 0.4)


def chair(k, x, y, face):
    k.push(Matrix.Translation((x, y, 0)) @ Matrix.Rotation(face, 4, "Z"))
    k.box("timber", -0.2, 0.2, -0.2, 0.2, 0.42, 0.47)
    k.box("timber", -0.2, 0.2, 0.15, 0.2, 0.47, 0.88)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("timber", sx * 0.17 - 0.025, sx * 0.17 + 0.025, sy * 0.17 - 0.025, sy * 0.17 + 0.025, 0, 0.42)
    k.pop()


def rail_run(k, a, b, z, h=1.0, mat="trim", spacing=0.12, kind="balusters"):
    """A railing between two plan points (any direction), at height z (or sloping if z is a pair)."""
    ax, ay = a; bx, by = b
    z0, z1 = (z, z) if not isinstance(z, tuple) else z
    L = math.hypot(bx - ax, by - ay)
    rod(k, mat, (ax, ay, z0 + h), (bx, by, z1 + h), 0.05)
    rod(k, mat, (ax, ay, z0 + 0.15), (bx, by, z1 + 0.15), 0.035)
    n = max(1, int(L / max(spacing, 0.1)))
    for i in range(1, n):
        t = i / n
        x, y, zz = ax + (bx - ax) * t, ay + (by - ay) * t, z0 + (z1 - z0) * t
        k.box(mat, x - 0.03, x + 0.03, y - 0.03, y + 0.03, zz + 0.15, zz + h)
    for x, y, zz in ((ax, ay, z0), (bx, by, z1)):
        k.box(mat, x - 0.06, x + 0.06, y - 0.06, y + 0.06, zz, zz + h + 0.08)


def x_panel(k, a, b, z, h=1.0, mat="trim"):
    """Cross-rail fence: posts, top and bottom rails, an X in each panel."""
    ax, ay = a; bx, by = b
    L = math.hypot(bx - ax, by - ay)
    n = max(1, round(L / 1.25))
    pts = [(ax + (bx - ax) * i / n, ay + (by - ay) * i / n) for i in range(n + 1)]
    for x, y in pts:
        k.box(mat, x - 0.06, x + 0.06, y - 0.06, y + 0.06, z, z + h + 0.1)
        k.box(mat, x - 0.08, x + 0.08, y - 0.08, y + 0.08, z + h + 0.1, z + h + 0.16)
    rod(k, mat, (ax, ay, z + h), (bx, by, z + h), 0.05, 4)
    rod(k, mat, (ax, ay, z + 0.12), (bx, by, z + 0.12), 0.04, 4)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        rod(k, mat, (x0, y0, z + 0.14), (x1, y1, z + h - 0.04), 0.03, 4)
        rod(k, mat, (x0, y0, z + h - 0.04), (x1, y1, z + 0.14), 0.03, 4)


def flowers(k, x0, x1, y0, y1, z, seed):
    import random
    r = random.Random(seed)
    k.box("leaf", x0, x1, y0, y1, z - 0.05, z + 0.08)
    n = max(3, int((x1 - x0) * (y1 - y0) * 14))
    for i in range(n):
        x, y = r.uniform(x0 + 0.08, x1 - 0.08), r.uniform(y0 + 0.08, y1 - 0.08)
        k.sphere("leaf", x, y, z + r.uniform(0.12, 0.22), r.uniform(0.11, 0.16), 1)
    for i in range(int(n * 0.8)):
        x, y = r.uniform(x0 + 0.06, x1 - 0.06), r.uniform(y0 + 0.06, y1 - 0.06)
        k.sphere(r.choice(("flower", "flower_white", "flower_white")), x, y, z + r.uniform(0.22, 0.34), r.uniform(0.05, 0.08), 1)


def planter(k, x, y, L, W=0.6, H=0.5, seed=1):
    k.box("timber", x - L / 2, x + L / 2, y - W / 2, y + W / 2, 0, H - 0.06)       # the cap is the only top
    k.box("trim", x - L / 2 - 0.04, x + L / 2 + 0.04, y - W / 2 - 0.04, y + W / 2 + 0.04, H - 0.06, H)
    k.box("timber", x - L / 2 - 0.03, x + L / 2 + 0.03, y - W / 2 - 0.03, y + W / 2 + 0.03, 0, 0.08)
    for i in range(1, int(L / 0.3)):                     # board joints
        xx = x - L / 2 + i * 0.3
        k.box("trim", xx - 0.012, xx + 0.012, y - W / 2 - 0.01, y - W / 2, 0.08, H - 0.06)
    flowers(k, x - L / 2 + 0.05, x + L / 2 - 0.05, y - W / 2 + 0.05, y + W / 2 - 0.05, H - 0.05, seed)


def picnic(k, x, y, rot=0.0):
    k.push(Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, "Z"))
    k.box("timber", -0.9, 0.9, -0.36, 0.36, 0.72, 0.77)
    for sy in (-1, 1):
        k.box("timber", -0.9, 0.9, sy * 0.62 - 0.14, sy * 0.62 + 0.14, 0.43, 0.47)
    for sx in (-0.65, 0.65):
        rod(k, "timber", (sx, -0.75, 0), (sx, 0.05, 0.75), 0.04, 4)
        rod(k, "timber", (sx, 0.75, 0), (sx, -0.05, 0.75), 0.04, 4)
        k.box("timber", sx - 0.04, sx + 0.04, -0.78, 0.78, 0.38, 0.43)
    k.pop()


def stair(k, x0, x1, y_start, y_end, z_top, rails=True):
    """A flight running in y from ground at y_start up to z_top at y_end."""
    n = max(2, int(round(z_top / 0.18)))
    d = (y_end - y_start) / n
    for i in range(n):
        ya = y_start + i * d
        k.box("timber", x0, x1, ya, y_end, i * z_top / n, (i + 1) * z_top / n)
    if rails:
        for x in (x0, x1):
            rail_run(k, (x, y_start), (x, y_end), (0.0, z_top), 0.95, spacing=0.4)


def piece(name, build, spots=None):
    k = Kit()
    build(k)
    ob, t = kit_to_object(k, name, MATS, LIB)
    TRIS[name] = t
    if spots:
        SPOTS[name] = spots
    return ob


# ------------------------------------------------------------------ the pieces
def marquee_peaks(k):
    n, m, H = 3, 8.0, 2.7                 # three 8 m modules
    L = n * m
    x0 = -L / 2
    for i in range(n):
        square_tent(k, x0 + m * (i + 0.5), 0, m / 2, H, 4.6)
    posts = [x0 + i * m / 2 for i in range(2 * n + 1)]
    for x in posts:                                       # front and back posts
        for y in (-m / 2, m / 2):
            k.cyl("trim", x, y, 0, H, 0.1, 0.08, 8)
            k.box("trim", x - 0.16, x + 0.16, y - 0.16, y + 0.16, 0, 0.18)
            k.box("trim", x - 0.14, x + 0.14, y - 0.14, y + 0.14, H - 0.2, H - 0.03)
    for y in (-m / 2, m / 2):                             # eave beams
        k.box("trim", x0, -x0, y - 0.08, y + 0.08, H - 0.25, H)
    for x in (x0, -x0):
        k.box("trim", x - 0.08, x + 0.08, -m / 2, m / 2, H - 0.25, H)
    # walls: back and ends in canvas with arched windows; front open under canvas arches
    k.box("canvas", x0, -x0, m / 2 - 0.03, m / 2 + 0.03, 0, H - 0.25)
    for x in (x0, -x0):
        k.box("canvas", x - 0.03, x + 0.03, -m / 2, m / 2, 0, H - 0.25)
    for xa, xb in zip(posts[:-1], posts[1:]):
        c, r = (xa + xb) / 2, (xb - xa) / 2 - 0.1
        # canvas spandrel between the eave and an arched opening
        arch = [(xa + 0.1 + (xb - xa - 0.2) * t, H - 1.05 + 0.6 * math.sin(math.pi * t)) for t in [j / 10 for j in range(11)]]
        k.prism_y("canvas", -m / 2 - 0.02, -m / 2 + 0.02, [(xa + 0.1, H - 0.2), (xb - 0.1, H - 0.2)] + arch[::-1])
        k.box("glass", c - 0.55, c + 0.55, m / 2 + 0.03, m / 2 + 0.08, 0.9, 1.9)          # 5 cm proud of the canvas
        k.arc_band("glass", c, 1.9, 0, 0.55, 0, math.pi, m / 2 + 0.03, m / 2 + 0.08, 6)
    for (xa, ya), (xb, yb) in (((x0, -m / 2 - 0.35), (-x0, -m / 2 - 0.35)), ((-x0, m / 2 + 0.35), (x0, m / 2 + 0.35)),
                               ((x0 - 0.35, m / 2), (x0 - 0.35, -m / 2)), ((-x0 + 0.35, -m / 2), (-x0 + 0.35, m / 2))):
        scallops(k, "canvas", (xa, ya), (xb, yb), H + 0.03, 0.28, 0.3)


def marquee_clearspan(k):
    L, D, H = 20.0, 9.0, 2.7
    x0, y0 = -L / 2, -D / 2
    bays = 5
    k.box("timber", x0 - 0.1, -x0 + 0.1, y0 - 0.1, -y0 + 0.1, 0, 0.15)                 # floor
    for i in range(bays + 1):
        x = x0 + L * i / bays
        for y in (y0, -y0):
            k.box("trim", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, H)
        rise = (D / 2 + 0.3) * math.tan(math.radians(18))
        rod(k, "trim", (x, y0 - 0.2, H), (x, 0, H + rise - 0.25), 0.09, 4)               # roof frames
        rod(k, "trim", (x, -y0 + 0.2, H), (x, 0, H + rise - 0.25), 0.09, 4)
    for side, y in ((-1, y0), (1, -y0)):
        for i in range(bays):
            xa = x0 + L * i / bays
            k.box("glass", xa + 0.1, xa + L / bays - 0.1, y - 0.03, y + 0.03, 0.15, H - 0.15)
            for j in range(1, 4):                                                            # glazing bars
                xx = xa + L / bays * j / 4
                k.box("trim", xx - 0.035, xx + 0.035, y - 0.06, y + 0.06, 0.15, H - 0.15)
            k.box("trim", xa, xa + L / bays, y - 0.06, y + 0.06, 0.95, 1.02)
            k.box("trim", xa, xa + L / bays, y - 0.06, y + 0.06, H - 0.6, H - 0.54)
        k.box("trim", x0, -x0, y - 0.1, y + 0.1, H - 0.15, H)
    for d in (-1, 1):                                                                       # double doors, front middle
        k.box("trim", d * 0.9 - 0.06, d * 0.9 + 0.06, y0 - 0.1, y0 - 0.035, 0.15, 2.3)     # door frames clear of the glass
    k.box("trim", -0.95, 0.95, y0 - 0.1, y0 - 0.035, 2.3, 2.4)
    k.box("trim", -0.04, 0.04, y0 - 0.1, y0 - 0.035, 0.15, 2.3)
    for x in (x0, -x0):                                                                     # glazed gable ends
        k.box("glass", x - 0.03, x + 0.03, y0 + 0.1, -y0 - 0.1, 0.15, H - 0.15)
        for j in range(1, 6):
            yy = y0 + D * j / 6
            k.box("trim", x - 0.06, x + 0.06, yy - 0.035, yy + 0.035, 0.15, H - 0.15)
        k.box("trim", x - 0.1, x + 0.1, y0, -y0, H - 0.15, H)
    rise = (D / 2 + 0.3) * math.tan(math.radians(18))
    k.prism_x("canvas", x0 - 0.25, -x0 + 0.25, [(y0 - 0.3, H), (0, H + rise), (-y0 + 0.3, H), (-y0 + 0.3, H + 0.1), (0, H + rise + 0.1), (y0 - 0.3, H + 0.1)])
    for x in (x0, -x0):
        k.prism_x("canvas", x - 0.03, x + 0.03, [(y0, H), (-y0, H), (0, H + rise - 0.05)])
    for i in range(1, bays):                                                                # panel seams
        x = x0 + L * i / bays
        k.prism_x("trim", x - 0.06, x + 0.06, [(y0 - 0.3, H + 0.08), (0, H + rise + 0.08), (-y0 + 0.3, H + 0.08), (-y0 + 0.3, H + 0.14), (0, H + rise + 0.14), (y0 - 0.3, H + 0.14)])
    k.box("trim", x0 - 0.25, -x0 + 0.25, -0.1, 0.1, H + rise, H + rise + 0.18)


def big_top(k):
    R, H, top = 7.0, 2.6, 9.0
    segs = 24
    revolve(k, ["canvas", "stripe"], 0, 0, [(R, 0.0), (R, H)], segs)
    revolve(k, ["canvas", "stripe"], 0, 0, tent_profile(R, H, top - H, 0.35, 8, 1.7), segs)
    for s in range(segs):
        a0, a1 = 2 * math.pi * s / segs, 2 * math.pi * (s + 1) / segs
        rr = R + 0.35
        scallops(k, "canvas" if s % 2 else "stripe", (rr * math.cos(a0), rr * math.sin(a0)), (rr * math.cos(a1), rr * math.sin(a1)), H + 0.02, 0.38, 0.25)
    # entrance: dark doorway with tied-back curtains, facing -y
    k.box("dark", -1.1, 1.1, -R - 0.05, -R + 0.2, 0, 2.3)
    for sx in (-1, 1):
        k.prism_y("canvas", -R - 0.12, -R - 0.05, [(sx * 1.1, 0), (sx * 1.45, 0), (sx * 1.35, 2.35), (sx * 0.85, 2.35), (sx * 1.05, 1.1)])
    k.cyl("trim", 0, 0, top - 0.2, top + 2.0, 0.1, 0.07, 8)
    k.sphere("trim", 0, 0, top + 2.05, 0.12, 1)
    cloth(k, "flag", 0.08, 0, top + 1.95, 1.3, 0.75, 0.12)
    for i in range(8):                                                                       # guy ropes
        a = math.pi / 8 + i * math.pi / 4
        rod(k, "trim", (R * 0.9 * math.cos(a), R * 0.9 * math.sin(a), H + 1.2), ((R + 3.2) * math.cos(a), (R + 3.2) * math.sin(a), 0), 0.02, 4)
        k.box("timber", (R + 3.2) * math.cos(a) - 0.06, (R + 3.2) * math.cos(a) + 0.06, (R + 3.2) * math.sin(a) - 0.06, (R + 3.2) * math.sin(a) + 0.06, 0, 0.3)


def pagoda_counter(k):
    h, H = 2.0, 2.6
    square_tent(k, 0, 0, h, H, 2.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.cyl("trim", sx * h, sy * h, 0, H, 0.07, 0.07, 8)
    k.box("timber", -h, h, h - 0.05, h, 0, H - 0.25)                                         # back wall
    k.box("timber", -h, h, -h - 0.05, -h + 0.05, 0, 1.05)                                    # counter front
    k.box("trim", -h - 0.05, h + 0.05, -h - 0.15, -h + 0.2, 1.05, 1.12)
    k.box("timber", h - 0.05, h + 0.05, -h, h, 0, 1.05)                                      # side counter
    k.box("trim", h - 0.1, h + 0.15, -h, h, 1.05, 1.12)
    k.box("canvas", -h - 0.05, -h + 0.05, -h, h, 0, H - 0.25)                                # closed side
    for i in range(1, 8):
        x = -h + i * 0.5
        k.box("trim", x - 0.015, x + 0.015, -h - 0.07, -h, 0.1, 1.0)
    for (xa, ya), (xb, yb) in (((-h - 0.3, -h - 0.3), (h + 0.3, -h - 0.3)), ((h + 0.3, -h - 0.3), (h + 0.3, h + 0.3)),
                               ((h + 0.3, h + 0.3), (-h - 0.3, h + 0.3)), ((-h - 0.3, h + 0.3), (-h - 0.3, -h - 0.3))):
        scallops(k, "canvas", (xa, ya), (xb, yb), H + 0.02, 0.25, 0.22)


def stand_open(k):
    W, rows, rise, tread, z0 = 12.0, 6, 0.42, 0.85, 0.6
    seats, y0 = [], -rows * tread / 2
    D = rows * tread
    for i in range(rows):
        z = z0 + i * rise
        y = y0 + i * tread
        k.box("timber", -W / 2, W / 2, y, -y0 - 0.1, z - 0.12, z)                    # up to the back panel
        if i:
            k.box("timber", -W / 2, W / 2, y - 0.02, y + 0.02, z - rise, z - 0.12)   # riser, under the tread
        n = int(W / 0.55)
        for j in range(n):
            x = -W / 2 + (j + 0.5) * W / n
            seat(k, x, y + tread * 0.45, z)
            seats.append([round(x, 2), round(y + tread * 0.45, 2), round(z + 0.05, 2)])
    zt = z0 + (rows - 1) * rise
    for x in (-W / 2, W / 2):                                       # side cheeks, stepped
        prof = [(y0, 0), (-y0, 0), (-y0, zt)]
        for i in range(rows - 1, -1, -1):
            prof += [(y0 + i * tread, z0 + i * rise), (y0 + i * tread, z0 + (i - 1) * rise if i else z0)]
        prof = prof[:-1] + [(y0, z0)]
        k.prism_x("timber", x - 0.08, x + 0.08, prof)
        rail_run(k, (x, y0), (x, -y0), (z0, zt), 1.0, spacing=0.4)
    k.box("timber", -W / 2, W / 2, y0 - 0.05, y0 + 0.05, 0, z0 - 0.15)                             # front skirt
    for i in range(1, 12):
        x = -W / 2 + i * W / 12
        k.box("trim", x - 0.02, x + 0.02, y0 - 0.08, y0 - 0.05, 0.05, z0 - 0.05)
    rail_run(k, (-W / 2, y0 - 0.1), (W / 2, y0 - 0.1), z0, 1.0, spacing=0.14)                     # front rail
    rail_run(k, (-W / 2, -y0), (W / 2, -y0), zt, 1.2, spacing=0.3)                                 # back rail
    k.box("timber", -W / 2, W / 2, -y0 - 0.1, -y0, 0, zt)                                          # back panel
    for x in (-W / 2 - 1.0, W / 2 + 1.0):                                                          # side stairs
        stair(k, x - 0.75 if x < 0 else x - 0.75, x + 0.75, y0 - 0.4, -y0, zt)
    return {"seats": seats}


def stand_covered(k):
    W, rows, rise, tread, z0 = 10.0, 4, 0.36, 0.85, 0.7
    seats, y0 = [], -rows * tread / 2 - 0.3
    D = rows * tread + 0.6
    for i in range(rows):
        z, y = z0 + i * rise, y0 + 0.3 + i * tread
        k.box("timber", -W / 2, W / 2, y, -y0 - 0.1, z - 0.12, z)
        n = int(W / 0.55)
        for j in range(n):
            x = -W / 2 + (j + 0.5) * W / n
            seat(k, x, y + tread * 0.45, z)
            seats.append([round(x, 2), round(y + tread * 0.45, 2), round(z + 0.05, 2)])
    k.box("timber", -W / 2, W / 2, y0, y0 + 0.3, 0, z0)
    k.box("timber", -W / 2 + 0.03, W / 2 - 0.03, y0 + 0.3, -y0 - 0.1, 0, z0 - 0.12)
    k.box("timber", -W / 2, W / 2, -y0 - 0.1, -y0, 0, 3.7)                                         # back wall
    rail_run(k, (-W / 2, y0 + 0.1), (W / 2, y0 + 0.1), z0, 0.95, spacing=0.14)
    for x in (-W / 2, W / 2):
        rail_run(k, (x, y0 + 0.1), (x, -y0), z0, 0.95, spacing=0.3)
    Hp = 3.8
    posts = [-W / 2 + i * W / 5 for i in range(6)]
    for x in posts:
        for y in (y0 + 0.1, -y0 - 0.1):
            k.cyl("trim", x, y, 0, Hp - 0.03, 0.09, 0.08, 8)
    for xa, xb in zip(posts[:-1], posts[1:]):                                                     # arched brackets
        c, r = (xa + xb) / 2, (xb - xa) / 2
        k.arc_band("trim", c, Hp - 1.0, r - 0.1, r, 0.25, math.pi - 0.25, y0 + 0.05, y0 + 0.15, 10)
        for sgn in (-1, 1):
            k.arc_band("trim", c + sgn * (r - 0.55), Hp - 0.55, 0.45, 0.53, math.pi / 2 if sgn > 0 else 0, math.pi if sgn > 0 else math.pi / 2, y0 + 0.06, y0 + 0.14, 5)
    k.box("trim", -W / 2 - 0.1, W / 2 + 0.1, y0, y0 + 0.2, Hp - 0.3, Hp)
    k.box("trim", -W / 2 - 0.1, W / 2 + 0.1, -y0 - 0.2, -y0 + 0.05, Hp - 0.3, Hp)               # 5 cm proud of the back wall
    k.hip_roof(-W / 2, W / 2, y0 + 0.1, -y0 - 0.1, Hp, 1.2, 0.5)
    stair(k, -W / 2 - 1.7, -W / 2 - 0.2, y0 - 1.6, y0 + 0.3, z0)
    return {"seats": seats}


def terrace_deck(k):
    W, D, h = 10.0, 7.0, 0.7
    k.box("timber", -W / 2, W / 2, -D / 2, D / 2, 0, h)
    # edging stops 3 cm under the deck top: sharing the top face made the deck flash (owner, 3 Nov)
    k.box("trim", -W / 2 - 0.05, W / 2 + 0.05, -D / 2 - 0.05, D / 2 + 0.05, h - 0.11, h - 0.03)
    for i in range(1, 20):
        x = -W / 2 + i * W / 20
        k.box("trim", x - 0.015, x + 0.015, -D / 2 - 0.07, -D / 2, 0.06, h - 0.1)
    for (a, b) in (((-W / 2, -D / 2), (-1.2, -D / 2)), ((1.2, -D / 2), (W / 2, -D / 2)), ((W / 2, -D / 2), (W / 2, D / 2)),
                   ((W / 2, D / 2), (-W / 2, D / 2)), ((-W / 2, D / 2), (-W / 2, -D / 2))):
        x_panel(k, a, b, h, 0.95)
    stair(k, -1.2, 1.2, -D / 2 - 1.3, -D / 2, h, rails=True)
    spots = []
    for i, (x, y) in enumerate(((-3.0, -0.6), (0.4, 0.9), (3.2, -0.4))):
        k.cyl("metal", x, y, h, h + 2.5, 0.04, 0.04, 6)
        revolve(k, "canvas", x, y, [(1.5, h + 2.15), (0.75, h + 2.5), (0.0, h + 2.65)], 8)
        k.cyl("trim", x, y, h, h + 0.74, 0.5, 0.5, 12)                       # round table
        k.cyl("dark", x, y, h, h + 0.7, 0.08, 0.08, 6)
        for c in range(4):
            a = c * math.pi / 2 + 0.4
            chair(k, x + 0.85 * math.cos(a), y + 0.85 * math.sin(a), a + math.pi / 2)
        spots += [[round(x + 1.3 * math.cos(c * 1.6 + 1), 2), round(y + 1.3 * math.sin(c * 1.6 + 1), 2), h] for c in range(3)]
    for x in (-W / 2 + 1.3, W / 2 - 1.3):
        planter(k, x, -D / 2 - 0.55, 2.2, 0.6, 0.5, int(x * 10))
    return {"stand": spots}


def viewing_tower(k):
    h, zp, H = 2.0, 3.2, 6.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("trim", sx * h - 0.11, sx * h + 0.11, sy * h - 0.11, sy * h + 0.11, 0, H)
    for (a, b) in (((-h, -h), (h, -h)), ((h, -h), (h, h)), ((h, h), (-h, h)), ((-h, h), (-h, -h))):
        rod(k, "trim", (a[0], a[1], 0.3), (b[0], b[1], zp - 0.4), 0.06, 4)
        rod(k, "trim", (a[0], a[1], zp - 0.4), (b[0], b[1], 0.3), 0.06, 4)
        k.box("trim", min(a[0], b[0]) - 0.08, max(a[0], b[0]) + 0.08, min(a[1], b[1]) - 0.08, max(a[1], b[1]) + 0.08, zp - 0.45, zp - 0.3)
    k.box("timber", -h - 0.25, h + 0.25, -h - 0.25, h + 0.25, zp - 0.25, zp)
    for (a, b) in (((-h - 0.2, -h - 0.2), (h + 0.2, -h - 0.2)), ((h + 0.2, -h - 0.2), (h + 0.2, 0.6)),
                   ((h + 0.2, h + 0.2), (-h - 0.2, h + 0.2)), ((-h - 0.2, h + 0.2), (-h - 0.2, -h - 0.2))):
        rail_run(k, a, b, zp, 1.05, spacing=0.14)
    k.box("timber", -h, h, h - 0.06, h, zp, H - 0.3)                                     # back wall with windows
    for x in (-1.0, 1.0):
        k.box("glass", x - 0.6, x + 0.6, h - 0.1, h - 0.06, zp + 1.2, zp + 2.3)
    k.box("trim", -h - 0.15, h + 0.15, -h - 0.15, h + 0.15, H - 0.3, H)
    k.hip_roof(-h - 0.1, h + 0.1, -h - 0.1, h + 0.1, H, 1.3, 0.45)
    # stair up the right side, arriving at the gap in the rail
    for i in range(int(zp / 0.19)):
        n = int(zp / 0.19)
        y = h + 3.6 - (i + 1) * 3.6 / n
        k.box("timber", h + 0.25, h + 1.25, y, y + 3.6 / n + 0.05, (i + 1) * zp / n - 0.06, (i + 1) * zp / n)
    rod(k, "timber", (h + 0.75, h + 3.6, 0), (h + 0.75, 0.6, zp), 0.12, 4)
    rail_run(k, (h + 1.25, h + 3.6), (h + 1.25, 0.6), (0.0, zp), 0.95, spacing=0.35)
    k.box("trim", h + 1.15, h + 1.35, h + 3.5, h + 3.7, 0, 1.0)
    return {"stand": [[x, y, zp] for x in (-1.2, 0, 1.2) for y in (-1.4, -0.5)]}


def kiosk_body(k, x0, x1, D, H, hatch=True):
    k.box("timber", x0, x1, -D / 2, D / 2, 0, H)
    k.box("trim", x0 - 0.05, x1 + 0.05, -D / 2 - 0.05, D / 2 + 0.05, 0, 0.12)
    for x in (x0, x1):
        k.box("trim", x - 0.06, x + 0.06, -D / 2 - 0.06, -D / 2 + 0.06, 0, H)
    for i in range(1, int((x1 - x0) / 0.3)):
        x = x0 + i * 0.3
        k.box("trim", x - 0.012, x + 0.012, -D / 2 - 0.02, -D / 2, 0.12, 0.95 if hatch else H - 0.1)
    if hatch:
        w = (x1 - x0) - 0.9
        c = (x0 + x1) / 2
        k.box("dark", c - w / 2, c + w / 2, -D / 2 - 0.05, -D / 2 + 0.12, 1.05, 2.05)   # 5 cm proud: 2 cm flashed far off
        k.box("trim", c - w / 2 - 0.1, c + w / 2 + 0.1, -D / 2 - 0.3, -D / 2 + 0.05, 0.98, 1.06)   # counter
        k.box("trim", c - w / 2 - 0.08, c + w / 2 + 0.08, -D / 2 - 0.05, -D / 2, 2.05, 2.15)


def kiosk_awning(k):
    L, D, H = 4.0, 2.6, 2.7
    kiosk_body(k, -L / 2, L / 2, D, H)
    k.box("trim", -L / 2 - 0.15, L / 2 + 0.15, -D / 2 - 0.15, D / 2 + 0.15, H, H + 0.15)
    k.box("board", -L / 2 - 0.3, L / 2 + 0.3, -D / 2 - 0.12, -D / 2 + 0.05, H + 0.15, H + 0.75)       # fascia board
    k.box("trim", -L / 2 - 0.35, L / 2 + 0.35, -D / 2 - 0.16, -D / 2 + 0.08, H + 0.75, H + 0.82)
    k.prism_x("canvas", -L / 2 - 0.1, L / 2 + 0.1, [(-D / 2, H - 0.05), (-D / 2 - 1.1, H - 0.55), (-D / 2 - 1.1, H - 0.5), (-D / 2, H)])
    scallops(k, "canvas", (-L / 2 - 0.1, -D / 2 - 1.1), (L / 2 + 0.1, -D / 2 - 1.1), H - 0.5, 0.18, 0.18)
    for x in (-L / 2 - 0.1, L / 2 + 0.1):
        k.prism_x("canvas", x - 0.02, x + 0.02, [(-D / 2, H), (-D / 2, H - 0.5), (-D / 2 - 1.1, H - 0.55)])


def booth_hut(k):
    L, D, H = 2.6, 2.2, 2.3
    kiosk_body(k, -L / 2, L / 2, D, H)
    rise = (D / 2 + 0.35) * math.tan(math.radians(32))
    k.prism_y("roof", -D / 2 - 0.35, D / 2 + 0.35, [(-L / 2 - 0.3, H), (0, H + rise), (L / 2 + 0.3, H), (L / 2 + 0.3, H + 0.1), (0, H + rise + 0.1), (-L / 2 - 0.3, H + 0.1)])
    for y in (-D / 2, D / 2):
        k.prism_y("timber", y - 0.02, y + 0.02, [(-L / 2, H), (L / 2, H), (0, H + rise - 0.05)])
    k.prism_y("trim", -D / 2 - 0.4, -D / 2 - 0.3, [(-L / 2 - 0.35, H - 0.05), (0, H + rise + 0.08), (L / 2 + 0.35, H - 0.05), (L / 2 + 0.2, H - 0.05), (0, H + rise - 0.08), (-L / 2 - 0.2, H - 0.05)])


def kiosk_row_arched(k):
    n, w, D, H = 3, 3.0, 2.6, 2.5
    L = n * w
    for i in range(n):
        x0 = -L / 2 + i * w
        kiosk_body(k, x0, x0 + w, D, H)
        c, r = x0 + w / 2, w / 2 + 0.1
        prof = [(c + (r + 0.12) * math.cos(a), H + 0.25 + (r + 0.12) * math.sin(a) * 0.55) for a in [math.pi * j / 10 for j in range(11)]]
        prof += [(c + r * math.cos(a), H + 0.25 + r * math.sin(a) * 0.55) for a in [math.pi * (10 - j) / 10 for j in range(11)]]
        k.prism_y("roof", -D / 2 - 0.25, D / 2 + 0.25, prof)
        half = [(c + r * math.cos(math.pi * j / 10), H + 0.25 + r * math.sin(math.pi * j / 10) * 0.55) for j in range(11)]
        k.prism_y("timber", -D / 2 - 0.05, D / 2 + 0.05, [(x0, H - 0.01), (x0 + w, H - 0.01)] + half)
        k.box("trim", x0, x0 + w, -D / 2 - 0.1, -D / 2 + 0.05, H, H + 0.25)
    k.box("trim", -L / 2 - 0.1, L / 2 + 0.1, -D / 2 - 0.1, D / 2 + 0.1, 0, 0.14)


def pagoda_kiosk(k):
    h, H = 1.3, 2.4
    kiosk_body(k, -h, h, 2 * h, H)
    k.box("timber", -h, h, -h, h, 0, H)
    square_tent(k, 0, 0, h + 0.1, H, 2.0)
    for (xa, ya), (xb, yb) in (((-h - 0.4, -h - 0.4), (h + 0.4, -h - 0.4)), ((h + 0.4, -h - 0.4), (h + 0.4, h + 0.4)),
                               ((h + 0.4, h + 0.4), (-h - 0.4, h + 0.4)), ((-h - 0.4, h + 0.4), (-h - 0.4, -h - 0.4))):
        scallops(k, "canvas", (xa, ya), (xb, yb), H + 0.02, 0.22, 0.2)
    k.cyl("trim", 0, 0, H + 2.4, H + 3.6, 0.035, 0.03, 6)
    cloth(k, "flag", 0.03, 0, H + 3.55, 0.8, 0.45, 0.07)


def pergola_picnic(k):
    L, D, H = 7.5, 3.6, 2.6
    for x in (-L / 2 + 0.3, 0, L / 2 - 0.3):
        for y in (-D / 2, D / 2):
            k.box("timber", x - 0.1, x + 0.1, y - 0.1, y + 0.1, 0, H)
            for sgn in (-1, 1):                                                         # knee braces
                if abs(x + sgn * 0.55) < L / 2:
                    rod(k, "timber", (x, y, H - 0.7), (x + sgn * 0.55, y, H - 0.12), 0.04, 4)
    for y in (-D / 2, D / 2):
        k.box("timber", -L / 2 - 0.3, L / 2 + 0.3, y - 0.1, y + 0.1, H - 0.1, H + 0.15)
    for i in range(16):                                                                 # rafters
        x = -L / 2 - 0.1 + i * (L + 0.2) / 15
        k.box("timber", x - 0.05, x + 0.05, -D / 2 - 0.45, D / 2 + 0.45, H + 0.15, H + 0.35)
    for j in range(7):                                                                  # top slats
        y = -D / 2 + j * D / 6
        k.box("timber", -L / 2 - 0.2, L / 2 + 0.2, y - 0.03, y + 0.03, H + 0.35, H + 0.42)
    for x in (-2.5, 0, 2.5):
        picnic(k, x, 0, 0)
    return {"seats": [[x + dx, y, 0.03] for x in (-2.5, 0, 2.5) for y in (-0.62, 0.62) for dx in (-0.45, 0.45)]}


def picnic_table(k):
    picnic(k, 0, 0, 0)
    return {"seats": [[dx, y, 0.03] for y in (-0.62, 0.62) for dx in (-0.45, 0.45)]}


def planter_long(k):
    planter(k, 0, 0, 1.8, 0.6, 0.5, 3)


def planter_short(k):
    planter(k, 0, 0, 1.0, 0.6, 0.5, 4)


def fence_picket(k):
    L, H = 2.5, 1.0
    for x in (-L / 2, L / 2):
        k.box("trim", x - 0.06, x + 0.06, -0.06, 0.06, 0, H + 0.1)
        k.sphere("trim", x, 0, H + 0.17, 0.07, 1)
    for z in (0.25, 0.7):
        k.box("trim", -L / 2, L / 2, 0.03, 0.08, z, z + 0.07)
    n = int(L / 0.15)
    for i in range(1, n):
        x = -L / 2 + i * L / n
        k.prism_y("trim", -0.015, 0.015, [(x - 0.04, 0.08), (x + 0.04, 0.08), (x + 0.04, H - 0.08), (x, H), (x - 0.04, H - 0.08)])


def fence_cross(k):
    x_panel(k, (-1.25, 0), (1.25, 0), 0.0, 1.0)


def barrier_rail(k):
    L, H = 3.0, 1.0
    for x in (-L / 2, 0, L / 2):
        k.cyl("trim", x, 0, 0, H, 0.06, 0.06, 8)
    rod(k, "trim", (-L / 2, 0, H), (L / 2, 0, H), 0.07, 10)
    for x in (-L / 2, L / 2):
        k.sphere("trim", x, 0, H, 0.07, 1)


def signboard(k):
    W, z0, z1 = 3.2, 1.0, 2.9
    k.box("board", -W / 2 + 0.3, W / 2 - 0.3, -0.04, 0.04, z0, z1)
    for z in (z0 - 0.06, z1):
        k.box("trim", -W / 2 + 0.25, W / 2 - 0.25, -0.07, 0.07, z, z + 0.08)
    for x in (-W / 2 + 0.15, W / 2 - 0.15):                                             # square truss legs
        for dx in (-0.12, 0.12):
            for dy in (-0.12, 0.12):
                k.box("metal", x + dx - 0.025, x + dx + 0.025, dy - 0.025, dy + 0.025, 0, z1 + 0.25)
        for i in range(11):
            za, zb = i * (z1 + 0.25) / 11, (i + 1) * (z1 + 0.25) / 11
            for dy in (-0.12, 0.12):
                rod(k, "metal", (x - 0.12, dy, za), (x + 0.12, dy, zb), 0.012, 4)
            for dx in (-0.12, 0.12):
                rod(k, "metal", (x + dx, -0.12, zb), (x + dx, 0.12, za), 0.012, 4)
        k.box("metal", x - 0.3, x + 0.3, -0.3, 0.3, 0, 0.05)
        k.box("metal", x - 0.16, x + 0.16, -0.16, 0.16, z1 + 0.25, z1 + 0.3)
    k.box("trim", -W / 2 + 0.15, W / 2 - 0.15, -0.05, 0.05, z1 + 0.15, z1 + 0.25)


def flagpole(k):
    k.box("trim", -0.25, 0.25, -0.25, 0.25, 0, 0.2)
    k.cyl("trim", 0, 0, 0.2, 7.0, 0.07, 0.045, 8)
    k.sphere("trim", 0, 0, 7.06, 0.09, 1)
    cloth(k, "flag", 0.05, 0, 6.9, 1.6, 1.0, 0.16)


def banner_flag(k):
    k.box("trim", -0.2, 0.2, -0.2, 0.2, 0, 0.15)
    k.cyl("trim", 0, 0, 0.15, 4.4, 0.05, 0.04, 8)
    k.sphere("trim", 0, 0, 4.45, 0.07, 1)
    k.box("trim", 0, 0.85, -0.025, 0.025, 4.05, 4.1)
    cloth(k, "flag", 0.08, 0, 4.03, 0.72, 2.3, 0.06, 4, 8, taper=0.0, along="z")
    k.prism_y("flag", -0.01, 0.01, [(0.08, 1.73), (0.8, 1.73), (0.44, 1.35)])


def signpost(k):
    k.box("trim", -0.06, 0.06, -0.06, 0.06, 0, 2.6)
    k.cyl("trim", 0, 0, 2.6, 2.66, 0.1, 0.1, 8)
    k.sphere("trim", 0, 0, 2.74, 0.08, 1)
    for z, d, ln in ((2.3, 1, 0.95), (2.0, -1, 0.95), (1.7, 1, 0.8)):
        x0, x1 = (0.06, 0.06 + ln) if d > 0 else (-0.06, -0.06 - ln)
        tip = x1 + d * 0.18
        k.prism_y("board", -0.03, 0.03, [(x0, z - 0.1), (x1, z - 0.1), (tip, z), (x1, z + 0.1), (x0, z + 0.1)] if d > 0 else
                  [(x0, z + 0.1), (x1, z + 0.1), (tip, z), (x1, z - 0.1), (x0, z - 0.1)])


PIECES = [("marquee_peaks", marquee_peaks), ("marquee_clearspan", marquee_clearspan), ("big_top", big_top),
          ("pagoda_counter", pagoda_counter), ("stand_open", stand_open), ("stand_covered", stand_covered),
          ("terrace_deck", terrace_deck), ("viewing_tower", viewing_tower), ("kiosk_awning", kiosk_awning),
          ("booth_hut", booth_hut), ("kiosk_row_arched", kiosk_row_arched), ("pagoda_kiosk", pagoda_kiosk),
          ("pergola_picnic", pergola_picnic), ("picnic_table", picnic_table), ("planter_long", planter_long),
          ("planter_short", planter_short), ("fence_picket", fence_picket), ("fence_cross", fence_cross),
          ("barrier_rail", barrier_rail), ("signboard", signboard), ("flagpole", flagpole),
          ("banner_flag", banner_flag), ("signpost", signpost)]
OBJ = {}
for name, fn in PIECES:
    spots = {}
    def build(k, fn=fn):
        spots.update(fn(k) or {})
    OBJ[name] = piece(name, build, None)
    if spots:
        SPOTS[name] = spots
    print("%-18s %6d triangles" % (name, TRIS[name]), flush=True)
print("site props: %d pieces, %d triangles in all" % (len(PIECES), sum(TRIS.values())), flush=True)

# Lay the library out in rows (only for looking at it in Blender; positions don't matter to engines).
x = 0.0
for name, _ in PIECES:
    ob = OBJ[name]
    w = ob.dimensions.x
    ob.location = (x + w / 2, 0, 0)
    x += w + 2

json.dump({"_about": "Crowd spots on the site components, local to each piece (Blender coordinates, metres; front faces -y). 'seats': where a seated figure goes; 'stand': standing spots on raised floors.",
           "pieces": SPOTS}, open(os.path.join(OUT_DIR, "site_props_spots.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
loc = {o.name: o.location.copy() for o in LIB.objects}
for o in LIB.objects:
    o.location = (0, 0, 0)                    # each piece at the origin in the .glb, ready to place
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, "site_props.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
for o in LIB.objects:
    o.location = loc[o.name]
os.makedirs(os.path.join(REPO, "assets/models/master"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets/models/master/site_props.blend"), compress=True)
print("exported site_props.glb", flush=True)
