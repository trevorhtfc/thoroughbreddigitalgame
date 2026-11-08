"""Build the July Course's stand-side buildings: plain traditional stands, an old-world pavilion, and the old
buildings round the finish (owner, 8 Nov 2026, with reference photos in reference/newmarket-july/).

    python -c "exec(open('tools/blender/build_july_stands.py').read())"
    SHEET=1 python -c "exec(open(...).read())"      # also render a catalogue sheet to check the pieces

Writes assets/models/architecture/july_stands.glb     one node per piece, each at the origin, ready to place
       assets/models/architecture/july_stands.json    per piece: size, and where a crowd can stand (crowd areas)
       assets/models/master/july_stands.blend

Owner: "the grandstands to the July Course can be less ornate structures compared to the Ascot modules ... more
traditional stands" (stands-traditional.png: stepped terraces under a flat dark canopy roof with a deep timber fascia,
plain red-brick end blocks with a few windows, thin steel columns). "The one closest to the finish line can be more of
an old world pavilion" (old-pavilion.png: two storeys, a veranda below and an open balcony above with fretwork
brackets, a gabled roof, a side stair, a white picket fence). "A couple of buildings that should sit around the finish
line" (judges-box-1805.png: a small brick box tower with people on its roof by the post; victorian-house.png: a red
brick house with steep gables and tall chimneys behind a white rail and gate, a bell tent, a small hipped pavilion).

Then (8 Nov, on the first renders): the brick blocks set back, at the stands' back corners, so the terrace and the roof
show their profile at the ends; "don't try too hard to make these look like real buildings"; the pastel-street
precedent for the detail: pastel tones, soft shadows, a smooth clay finish (the scene build gives every piece matte
clay materials and rounded edges; the colours here are already the pastel ones).

Building coordinates (Blender), as the stand kit: x along the front, left to right as seen from the track; y into the
building (the front faces -y); z up. Every piece's origin is the middle of its front, on the ground. Walls run 1 m
below the ground so a piece can sit on a slope. In glTF (y up) the front faces +z.

Pieces
  terrace_grand     the big stand: 16 stepped rows; brick blocks at its back corners, one a tower 80 x 15 m, 21 m high
  terrace_mid       12 rows, a brick block at one back corner                                   62 x 12 m, 15 m
  terrace_small     10 rows, brick blocks at both back corners                                  52 x 10 m, 13.5 m
  terrace_low       a long low stand: 6 rows, open ends with stairs                             70 x 6 m, 8 m
  old_pavilion      the old-world pavilion at the line: a veranda and two balconied stands      40 x 9 m, 16 m
  judges_box        the 1805 judge's box: brick, tall windows, people on the roof               5 x 5 m, 8 m
  victorian_house   the weighing room: red brick, steep gables, chimneys, porch, rail and gate  11 x 11 m, 12.9 m
  bell_tent         a white bell tent                                                           7 m across
  little_pavilion   a small hipped-roof pavilion                                                6 x 6 m
"""
import json, math, os
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(rp("tools/blender/kit.py")).read())

COL = {   # the owner's pastel-street precedent (reference/newmarket-july/precedent-pastel-street.png): soft terracotta
          # instead of hard red brick, cream and sand, dusty violet and slate for the darks; nothing shiny
    "brick": "#d9917a", "stone": "#f2e4cc", "concrete": "#e6d9c4", "bench": "#857f96", "roof": "#8c7873",
    "fascia": "#e2c198", "steel": "#6b7086", "glass": "#3f3a4d", "trim": "#f7efe2", "door": "#7f9f8c",
    "paint": "#f4e6d0", "slate": "#8f95a8", "deck": "#dcc4a2", "canvas": "#f7efe0", "pot": "#d08a6c", "iron": "#5b6273",
}
MATS = {k: material("jc_" + k, v, rough=0.9) for k, v in COL.items()}
K = Kit()
CROWD = []          # crowd areas of the piece being built: [x0, x1, y0, y1, floor]


def area(x0, x1, y0, y1, z):
    CROWD.append([round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z, 2)])


# ------------------------------------------------------------------------------------------ helpers
PANES = False        # plain windows (owner: don't try too hard to make these look like real buildings)


def win(x, y, z0, w, h):
    K.window(x, y, z0, w, h, panes=PANES)


def side_window(xf, facing, y, z0, w, h):
    """A window on a wall face at x = xf that looks along +x (facing = +1) or -x (-1)."""
    K.push(Matrix.Translation((xf, 0, 0)) @ Matrix.Rotation(math.pi / 2 * facing, 4, "Z"))
    K.window(y * facing, 0, z0, w, h, panes=PANES)
    K.pop()


def gable_x(x0, x1, y0, y1, z, pitch, ov, roof="slate", wall="brick", trim="trim", barge=True, finial=True, ends=(True, True)):
    """A pitched roof with its ridge along x over the walls x0..x1, y0..y1 whose tops are at z; gable walls fill the
    ends. The roof passes through z at the wall line (no gap under the eaves). Returns the ridge height."""
    t, tn = 0.28, math.tan(math.radians(pitch))
    yc, half = (y0 + y1) / 2, (y1 - y0) / 2
    ez, rz = z - ov * tn, z + half * tn
    K.prism_x(roof, x0 - ov, x1 + ov, [(y0 - ov, ez), (y0 - ov, ez + t), (yc, rz + t), (y1 + ov, ez + t), (y1 + ov, ez), (yc, rz)])
    for xa, xb in ((x0, x0 + 0.25), (x1 - 0.25, x1)):
        K.prism_x(wall, xa, xb, [(y0, z - 0.02), (y1, z - 0.02), (yc, rz - 0.05)])
    K.box(trim, x0 - ov, x1 + ov, yc - 0.13, yc + 0.13, rz + t - 0.04, rz + t + 0.14)          # ridge capping
    if barge:                                                                                    # bargeboards
        for xb in [x for x, e in zip((x0 - ov - 0.02, x1 + ov - 0.1), ends) if e]:
            K.prism_x(trim, xb, xb + 0.12, [(y0 - ov, ez - 0.28), (yc, rz - 0.28), (y1 + ov, ez - 0.28),
                                             (y1 + ov, ez + 0.02), (yc, rz + 0.02), (y0 - ov, ez + 0.02)])
    if finial:
        for xf in [x for x, e in zip((x0 - ov + 0.05, x1 + ov - 0.05), ends) if e]:
            K.cyl(trim, xf, yc, rz + t, rz + t + 0.9, 0.08, 0.03, segs=6)
    return rz


def gable_y(x0, x1, y0, y1, z, pitch, ov, **kw):
    """The same with the ridge along y (a gable that faces the front); ends = (front, back)."""
    K.push(Matrix.Rotation(math.pi / 2, 4, "Z"))      # local (u, v) -> world (-v, u)
    rz = gable_x(y0, y1, -x1, -x0, z, pitch, ov, **kw)
    K.pop()
    return rz


def rod(mat, x, ya, za, yb, zb, r=0.04):
    """A thin sloping rail in the y-z plane at x (a handrail up a terrace or a stair)."""
    K.prism_x(mat, x - r, x + r, [(ya, za), (yb, zb), (yb, zb + 2 * r), (ya, za + 2 * r)])


def brick_block(bx0, bx1, y0, y1, top, outer=None):
    """A plain brick block at a back corner of a stand: a coping, and rows of plain windows on its front and outer side."""
    K.box("brick", bx0, bx1, y0, y1, -1.0, top)
    K.box("stone", bx0 - 0.15, bx1 + 0.15, y0 - 0.15, y1 + 0.15, top, top + 0.35)
    cx, w = (bx0 + bx1) / 2, bx1 - bx0
    xs = [cx] if w < 5.5 else [cx - w * 0.22, cx + w * 0.22]
    z = 4.3
    while z + 1.7 < top - 0.8:
        for x in xs:
            win(x, y0, z, 1.0, 1.6)
        if outer:
            xf, f = (bx1, 1) if outer > 0 else (bx0, -1)
            n = max(1, int((y1 - y0) // 2.8))
            for k in range(n):
                side_window(xf, f, y0 + (y1 - y0) * (k + 0.5) / n, z, 1.0, 1.6)
        z += 3.2
    for x in xs:
        win(x, y0, 0.9, 1.0, 1.5)


# ------------------------------------------------------------------------------------------ the traditional stands
def terrace_stand(L, rows, H, left=None, right=None, tread=0.8, riser=0.42, z0=1.3, aisle=13.0, cols=10.0, gallery=True):
    """Stepped terrace under a canopy roof that rises to the front: a brick parapet in front, benches on every row, white
    handrails up the aisles, a glazed gallery at the back, slender columns, a deep sand fascia. left/right = None (the
    terrace's open end with a stair), 'block' (a brick block as high as the roof) or 'tower' (taller); the blocks sit at
    the BACK corners, set back behind the terrace, so the stepped terrace and the roof show their profile at the ends
    (owner, 8 Nov)."""
    half = L / 2
    ew = {None: 0.0, "block": 6.0, "tower": 7.0}
    eL, eR = ew[left], ew[right]
    yf = 0.6
    yb = yf + rows * tread
    ztop = z0 + (rows - 1) * riser
    D = yb + 0.5
    yr0 = yf + 1.2                                  # the roof's front edge
    by0, by1 = yb - 3.5, D + 1.0                    # the blocks' front and back
    rx = half + 0.4                                 # the roof runs 0.4 m past the terrace's ends
    def span(y):                                    # the terrace's clear width at depth y (the blocks take the back corners)
        return (-half + (eL + 0.2 if y > by0 and eL else 0.4), half - (eR + 0.2 if y > by0 and eR else 0.4))
    # brick parapet in front, with a stone coping
    K.box("brick", -half, half, 0.0, yf, -1.0, z0 + 1.0)
    K.box("stone", -half - 0.06, half + 0.06, -0.06, yf + 0.06, z0 + 1.0, z0 + 1.15)
    # the terrace: one stepped solid
    prof = [(yf, -1.0)]
    for i in range(rows):
        zi = z0 + i * riser
        prof += [(yf + i * tread, zi), (yf + (i + 1) * tread, zi)]
    prof += [(yb, -1.0)]
    K.prism_x("concrete", -half, half, prof)
    # aisles and benches
    nseg = max(2, round(L / aisle))
    bounds = [-half + L * k / nseg for k in range(nseg + 1)]
    for i in range(rows):
        zi, yback = z0 + i * riser, yf + (i + 1) * tread
        lo, hi = span(yback)
        for k in range(nseg):
            s0 = max(lo, bounds[k] + (0 if k == 0 else 0.7))
            s1 = min(hi, bounds[k + 1] - (0 if k == nseg - 1 else 0.7))
            if s1 - s0 > 1.0:
                K.box("bench", s0, s1, yback - 0.42, yback - 0.08, zi, zi + 0.42)
                area(s0, s1, yback - tread + 0.06, yback - 0.44, zi)
    slope = (ztop - z0) / (yb - yf - 0.6)
    for k in range(1, nseg):
        ax = bounds[k]
        rod("trim", ax, yf + 0.3, z0 + 1.0, yb - 0.3, ztop + 1.0)
        for i in range(0, rows, 3):
            yp = yf + i * tread + 0.4
            K.box("trim", ax - 0.04, ax + 0.04, yp - 0.04, yp + 0.04, z0 + i * riser, z0 + 1.0 + (yp - yf - 0.3) * slope)
    # the back wall, with a plain glazed gallery above the top row
    K.box("brick", -half, half, yb, D, -1.0, H - 1.2)
    if gallery and H - 1.6 - ztop > 1.6:
        g0, g1 = span(yb)
        K.box("glass", g0, g1, yb - 0.04, yb + 0.02, ztop + 0.2, H - 1.75)
        n = max(2, round((g1 - g0) / 4.5))
        for k in range(n + 1):
            x = g0 + (g1 - g0) * k / n
            K.box("trim", x - 0.14, x + 0.14, yb - 0.12, yb, ztop, H - 1.5)
    # the canopy roof: rises to the front, a deep sand fascia proud of its front, slim columns on the terrace
    K.prism_x("roof", -rx, rx, [(yr0 - 0.3, H - 1.5), (yr0 - 0.3, H), (D + 0.4, H - 1.0), (D + 0.4, H - 1.35), (yr0 + 0.5, H - 1.5)])
    K.box("fascia", -rx - 0.05, rx + 0.05, yr0 - 0.37, yr0 - 0.29, H - 1.55, H + 0.04)
    yc = yr0 + 0.35
    zc = z0 + int((yc - yf) // tread) * riser
    n = max(2, round(L / cols))
    for k in range(n + 1):
        x = -half + 0.6 + (L - 1.2) * k / n
        K.box("steel", x - 0.14, x + 0.14, yc - 0.14, yc + 0.14, zc, H - 1.5)
    # ends: a brick block at the back corner, or an open stair up the terrace's end
    for side, kind in ((-1, left), (1, right)):
        if kind:
            top = H + (2.6 if kind == "tower" else 0.5)
            bx0, bx1 = (-half - 0.5, -half + ew[kind]) if side < 0 else (half - ew[kind], half + 0.5)
            brick_block(bx0, bx1, by0, by1, top, outer=side)
        else:
            x = -half if side < 0 else half
            sx0, sx1 = (x - 1.6, x - 0.1) if side < 0 else (x + 0.1, x + 1.6)
            nst = max(4, int(ztop / 0.3))
            for j in range(nst):
                zj = (j + 1) * ztop / nst
                yj = yf + (yb - yf - 1.0) * (j + 1) / nst
                K.box("concrete", sx0, sx1, yj - 0.5, yj, zj - 0.14, zj)
            rxx = sx0 + 0.05 if side < 0 else sx1 - 0.05
            rod("trim", rxx, yf, 1.0, yb - 1.0, ztop + 1.0)
    return {"width": L, "depth": by1 if (left or right) else D + 0.4,
            "height": H + (2.6 if "tower" in (left, right) else 0.5 if (left or right) else 0.0)}


# ------------------------------------------------------------------------------------------ the old-world pavilion
def old_pavilion(L=40.0, D=9.0, G=4.0, S=3.9, levels=2, stair=True, fence=True):
    """Two open balconied stands over a veranda (owner, 8 Nov: "make the pavilion grandstand taller", then "longer"):
    G = ground storey, S = each upper storey, levels = how many balconies."""
    half = L / 2
    nb = round(L / 4.0)
    posts = [-half + 0.3 + (L - 0.6) * k / nb for k in range(nb + 1)]
    def brackets(x, y0, y1, z):
        for s_ in (-1, 1):
            if -half < x + s_ * 0.6 < half:
                K.prism_y("trim", y0, y1, [(x, z), (x + s_ * 0.6, z), (x, z - 0.6)])
    # ground floor: veranda deck, rooms behind with windows and a door, posts with fretwork brackets
    K.box("deck", -half, half, 0.0, 3.0, -1.0, 0.3)
    K.box("deck", -2.0, 2.0, -0.6, 0.0, -1.0, 0.15)
    K.box("paint", -half, half, 3.0, D, -1.0, G - 0.25)
    for k in range(int((L - 3.0) // 3.5) + 1):
        x = -half + 2.0 + k * 3.5
        if abs(x) > 1.6 and x < half - 1.2:
            win(x, 3.0, 0.9, 1.3, 2.1)
    K.door(0.0, 3.0, 0.3, 1.6, 2.6)
    K.box("trim", -half, half, 0.05, 0.33, G - 0.5, G - 0.25)
    for x in posts:
        K.box("trim", x - 0.09, x + 0.09, 0.1, 0.28, 0.3, G - 0.5)
        brackets(x, 0.15, 0.23, G - 0.5)
    area(-half + 0.4, half - 0.4, 0.45, 2.6, 0.3)
    # the balconies: each a slab, a balustrade, posts and brackets, and an open stand of four rows
    E = G + levels * S - 0.25                       # the eaves
    zf = G
    for lv in range(levels):
        top = E if lv == levels - 1 else zf + S - 0.25
        K.box("deck", -half - 0.3, half + 0.3, -0.95, D, zf - 0.25, zf)
        K.balustrade(-half - 0.15, half + 0.15, -0.8, zf, h=1.0, mat="trim", spacing=0.3)
        K.balustrade(-0.8, 3.0, -half - 0.15, zf, h=1.0, mat="trim", spacing=0.3, axis="y")
        K.balustrade(-0.8, 0.6 if (lv == 0 and stair) else 3.0, half + 0.15, zf, h=1.0, mat="trim", spacing=0.3, axis="y")
        for x in posts:
            K.box("trim", x - 0.09, x + 0.09, -0.89, -0.71, zf, top - 0.25)
            brackets(x, -0.84, -0.76, top - 0.25)
        K.box("trim", -half - 0.3, half + 0.3, -0.98, -0.6, top - 0.5, top - 0.25)
        steps = [(0.6, zf + 0.35), (2.1, zf + 0.7), (3.6, zf + 1.05), (5.1, zf + 1.4)]
        prof = [(0.6, zf - 0.01)]
        for y, z in steps:
            prof += [(y, z), (y + 1.5, z)]
        prof += [(6.6, zf - 0.01)]
        K.prism_x("deck", -half + 0.3, half - 0.3, prof)
        area(-half + 0.3, half - 0.3, -0.6, 0.45, zf)
        for y, z in steps:
            K.box("bench", -half + 0.6, half - 0.6, y + 1.0, y + 1.4, z, z + 0.42)
            area(-half + 0.6, half - 0.6, y + 0.1, y + 0.95, z)
        K.box("paint", -half, half, D - 0.4, D, zf, top)
        for k in range(int((L - 6.0) // 4.0) + 1):   # the back of each stand: dark doors to the rooms behind
            K.door(-half + 3.0 + k * 4.0, D - 0.4, zf + 1.4, 1.3, 1.9)
        zf += S
    for xa, xb in ((-half, -half + 0.3), (half - 0.3, half)):
        K.box("paint", xa, xb, 3.0, D, G - 0.25, E)
        K.box("paint", xa, xb, 3.0, D, -1.0, G - 0.25)
    rz = gable_x(-half, half, -0.95, D, E, 30, 0.7, roof="slate", wall="paint")
    # the side stair (right end) up to the first balcony, open treads on stringers with a white handrail
    sx0, sx1 = half + 0.35, half + 1.65
    n = 13 if stair else 0
    for j in range(n):
        zj = G * (j + 1) / n
        yj = D + 1.6 - (D + 1.6 - 1.6) * (j + 1) / n
        K.box("deck", sx0, sx1, yj, yj + 0.85, zj - 0.08, zj)
    for xs in ((sx0, sx1 - 0.08) if stair else ()):
        K.prism_x("trim", xs, xs + 0.08, [(D + 1.6, -0.2), (1.6, G - 0.1), (1.6, G + 0.15), (D + 1.6, 0.05)])
    if stair:
        rod("trim", sx1 - 0.04, D + 1.6, 1.0, 1.6, G + 1.0)
    # the white picket fence in front, with a gap for the gate
    fy = -3.2
    for a, b in (((-half - 2.0, -1.5), (1.5, half + 2.0)) if fence else ()):
        K.box("trim", a, b, fy + 0.04, fy + 0.1, 0.28, 0.38)
        K.box("trim", a, b, fy + 0.04, fy + 0.1, 0.72, 0.82)
        x = a + 0.06
        while x < b:
            K.box("trim", x - 0.035, x + 0.035, fy - 0.03, fy + 0.03, -0.3, 1.0)
            x += 0.15
    return {"width": L + 4.0, "depth": D + 1.6, "height": rz + 1.2}


# ------------------------------------------------------------------------------------------ the 1805 judge's box
def judges_box(S=5.0):
    h = S / 2
    K.box("brick", -h, h, 0.0, S, -1.0, 6.9)
    K.box("stone", -h - 0.12, h + 0.12, -0.12, S + 0.12, 3.0, 3.22)
    K.box("stone", -h - 0.25, h + 0.25, -0.25, S + 0.25, 6.85, 7.15)
    K.door(0.0, 0.0, 0.0, 1.1, 2.3)
    for x in (-1.15, 1.15):
        K.window(x, 0.0, 3.6, 1.2, 2.6)
    for f, xf in ((1, h), (-1, -h)):
        for y in (1.45, 3.55):
            side_window(xf, f, y, 3.6, 1.2, 2.6)
    K.balustrade(-h - 0.1, h + 0.1, -0.1, 7.15, h=1.0, mat="iron", spacing=0.3)
    K.balustrade(-h - 0.1, h + 0.1, S + 0.1, 7.15, h=1.0, mat="iron", spacing=0.3)
    K.balustrade(-0.1, S + 0.1, -h - 0.1, 7.15, h=1.0, mat="iron", spacing=0.3, axis="y")
    K.balustrade(-0.1, S - 1.3, h + 0.1, 7.15, h=1.0, mat="iron", spacing=0.3, axis="y")
    K.cyl("iron", -h + 0.25, S - 0.25, 7.15, 10.2, 0.05, 0.04, segs=6)
    K.box("trim", -h + 0.28, -h + 1.3, S - 0.27, S - 0.23, 9.4, 10.1)               # a small white flag
    # the iron stair up the back corner to the roof
    sx0, sx1 = h + 0.2, h + 1.1
    n = 20
    for j in range(n):
        zj = 7.15 * (j + 1) / n
        yj = S + 5.5 - 6.2 * (j + 1) / n
        K.box("iron", sx0, sx1, yj, yj + 0.32, zj - 0.06, zj)
    rod("iron", sx1, S + 5.5, 1.0, S - 0.7, 8.15, 0.035)
    area(-h + 0.4, h - 0.4, 0.3, 2.6, 7.15)
    return {"width": S + 2.4, "depth": S + 5.5, "height": 10.2}


# ------------------------------------------------------------------------------------------ the Victorian house
def victorian_house():
    K.box("brick", -5.5, 5.5, 0.0, 9.0, -1.0, 6.2)
    K.box("brick", -5.5, -0.8, -1.6, 0.0, -1.0, 6.2)                     # the front wing with its own gable
    K.box("stone", -5.62, 5.62, -0.12, 9.12, 3.0, 3.18)
    rz = gable_x(-5.5, 5.5, 0.0, 9.0, 6.2, 42, 0.5)
    gable_y(-5.5, -0.8, -1.6, 4.4, 6.2, 45, 0.45, ends=(True, False))
    # the bay window under the front gable, with its own little hipped roof
    K.box("brick", -4.4, -1.9, -2.5, -1.6, -1.0, 2.9)
    win(-3.15, -2.5, 0.8, 1.7, 1.7)
    K.hip_roof(-4.4, -1.9, -2.5, -1.6, 2.9, 0.6, ov=0.15, mat="slate")
    win(-3.15, -1.6, 3.7, 1.2, 1.7)
    win(-3.15, -1.6, 6.6, 0.7, 1.0)
    for x in (1.4, 3.8):
        win(x, 0.0, 3.7, 1.0, 1.6)
    win(3.8, 0.0, 0.8, 1.1, 1.8)
    K.door(1.4, 0.0, 0.0, 1.1, 2.3)
    for y in (2.6, 6.4):
        for z in (0.8, 3.7):
            side_window(5.5, 1, y, z, 1.0, 1.6)
            side_window(-5.5, -1, y, z, 1.0, 1.6)
    # the porch: two posts and a little gabled roof
    for x in (0.3, 2.5):
        K.box("trim", x - 0.08, x + 0.08, -1.98, -1.82, 0.0, 2.6)
    gable_y(0.15, 2.65, -2.05, 0.0, 2.6, 40, 0.2, roof="slate", wall="trim", finial=False, ends=(True, False))
    # tall chimney stacks with pots
    for x0, x1 in ((-4.3, -3.3), (3.4, 4.4)):
        K.box("brick", x0, x1, 4.0, 5.0, 6.0, 12.0)
        K.box("stone", x0 - 0.15, x1 + 0.15, 3.85, 5.15, 12.0, 12.25)
        for px in (x0 + 0.27, x1 - 0.27):
            K.cyl("pot", px, 4.5, 12.25, 12.9, 0.16, 0.13, segs=8)
    # the white rail in front, with a five-bar gate
    fy = -5.5
    x = -9.0
    while x <= 9.01:
        if not 2.2 < x < 5.0:
            K.box("trim", x - 0.07, x + 0.07, fy - 0.07, fy + 0.07, -0.3, 1.3)
        x += 2.4
    for a, b in ((-9.0, 2.2), (5.0, 9.0)):
        for z in (0.6, 1.1):
            K.box("trim", a, b, fy + 0.07, fy + 0.15, z - 0.06, z + 0.06)
    for gx in (2.35, 4.85):
        K.box("trim", gx - 0.08, gx + 0.08, fy - 0.08, fy + 0.08, -0.3, 1.35)
    for z in (0.25, 0.47, 0.69, 0.91, 1.13):
        K.box("trim", 2.45, 4.75, fy - 0.03, fy + 0.03, z - 0.04, z + 0.04)
    K.prism_y("trim", fy - 0.03, fy + 0.03, [(2.45, 0.21), (2.65, 0.21), (4.75, 1.13), (4.55, 1.13)])
    return {"width": 18.0, "depth": 14.5, "height": 12.9}


def bell_tent(r=3.5):
    K.cyl("canvas", 0.0, r, -0.2, 0.9, r, segs=24)
    K.cyl("canvas", 0.0, r, 0.9, 5.6, r + 0.12, 0.09, segs=24)
    K.cyl("iron", 0.0, r, 5.5, 6.2, 0.04, segs=6)
    K.box("door", -0.45, 0.45, -0.03, 0.06, 0.0, 1.5)          # the dark door flap
    return {"width": 2 * r, "depth": 2 * r, "height": 6.2}


def little_pavilion(S=6.0):
    h = S / 2
    K.box("paint", -h, h, 0.0, S, -1.0, 3.0)
    K.box("deck", -h - 0.5, h + 0.5, -1.2, 0.0, -1.0, 0.2)
    K.hip_roof(-h, h, 0.0, S, 3.0, 2.2, ov=0.55, mat="slate")
    for x in (-1.6, 1.6):
        win(x, 0.0, 0.9, 1.0, 1.4)
    K.door(0.0, 0.0, 0.2, 1.1, 2.2)
    for y in (1.5, 4.5):
        side_window(h, 1, y, 0.9, 1.0, 1.4)
        side_window(-h, -1, y, 0.9, 1.0, 1.4)
    return {"width": S + 1.0, "depth": S + 1.2, "height": 5.2}


# ------------------------------------------------------------------------------------------ build and export
PIECES = [
    # owner (8 Nov): "all the grandstands a bit taller": a higher front, steeper rows, taller galleries
    ("terrace_grand", lambda: terrace_stand(80.0, 16, 18.5, left="block", right="tower", riser=0.46, z0=1.8)),
    ("terrace_mid", lambda: terrace_stand(62.0, 12, 14.5, right="block", riser=0.46, z0=1.8)),
    ("terrace_small", lambda: terrace_stand(52.0, 10, 13.0, left="block", right="block", riser=0.46, z0=1.8)),
    ("terrace_low", lambda: terrace_stand(70.0, 6, 8.0, z0=1.2, riser=0.46, gallery=False)),
    ("old_pavilion", lambda: old_pavilion(42.0)),                       # owner: cranked round the finish line, this the main stand
    ("old_pavilion_wing", lambda: old_pavilion(28.0, stair=False)),      # and its wing, turned towards the track
    ("pavilion_small", lambda: old_pavilion(46.0, levels=1, stair=False, fence=False)),   # behind the gaps between the stands
    ("judges_box", judges_box),
    ("victorian_house", victorian_house),
    ("bell_tent", bell_tent),
    ("little_pavilion", little_pavilion),
]
LIB = bpy.data.collections.new("july_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD)
    info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-16s %6d triangles, %d crowd areas" % (name, tris, len(CROWD)), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "The July Course's stand-side buildings (tools/blender/build_july_stands.py). Building axes: x along "
                     "the front (left to right from the track), y into the building (front faces -y), z up; origin the "
                     "middle of the front on the ground. crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "july_stands.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "july_stands.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
x = 0.0                                          # laid out in a row in the master file, to look at
for name, _ in PIECES:
    w = INFO[name]["width"]
    OBJ[name].location = (x + w / 2, 0, 0)
    x += w + 6
os.makedirs(rp("assets/models/master"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=rp("assets/models/master/july_stands.blend"), compress=True)
print("exported july_stands.glb", flush=True)

if os.environ.get("SHEET"):                      # a quick catalogue render, to check the pieces
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.8, 0.88, 1)
    bpy.ops.mesh.primitive_plane_add(size=600, location=(x / 2, 40, 0))
    bpy.context.object.data.materials.append(material("lawn", "#9fbf6a"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 2400, 900
    scene.view_settings.view_transform = "AgX"
    views = (("sheet_a", (140, -150, 38), (140, 5, 4), 24), ("sheet_b", (333, -48, 11), (333, 5, 4), 24),
             ("sheet_c", (100, -26, 11), (68, 8, 7), 26), ("sheet_d", (226, -22, 8), (198, 6, 5), 26))
    for nm, frm, to, lens in [v for v in views if v[0] in os.environ.get("VIEWS", "sheet_a,sheet_b,sheet_c,sheet_d")]:
        cam = bpy.data.objects.new(nm, bpy.data.cameras.new(nm)); cam.data.lens = lens; scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = rp("reference/newmarket-july/renders/%s.png" % nm)
        bpy.ops.render.render(write_still=True)
        print("rendered", nm, flush=True)
