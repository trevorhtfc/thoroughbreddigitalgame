"""Build the Rowley Mile's stand-side architecture (owner, 8 Nov 2026, with photos in reference/newmarket/).

    python -c "exec(open('tools/blender/build_rowley_stands.py').read())"
    SHEET=1 python -c "exec(open(...).read())"      # also render the pieces in place along the stand side, to check

Writes assets/models/architecture/rowley_stands.glb     one node per piece, each at the origin, ready to place
       assets/models/architecture/rowley_stands.json    per piece: size, crowd areas, colours
       assets/models/master/rowley_stands.blend

The owner's references: the aerial with his marks (aerial-stands-marked.png): 1 = the Millennium Grandstand
(millennium-grandstand.png, grandstand.jpg: a row of white wave canopies on masts over glazed floors and an open seating
terrace, a glazed stair tower at its end, and beside it the lower Rowley stand with a clock cupola and a brick end);
2 = the finish line; 3 = the old stand up the course (old-stand-victorian.png: a long two-tier Victorian grandstand
under a big hipped slate roof with dormers, a lantern and chimneys, a packed standing terrace in front, a white judge's
kiosk by the rail and a small two-storey pavilion beside it). As at the July Course: interpretive, drawn simply, in the
pastel-street precedent's colours and a clay finish ("don't try too hard to make these look like real buildings").

Building coordinates (Blender), as the other kits: x along the front, left to right as seen from the track; y into the
building (the front faces -y); z up; origin the middle of the front, on the ground; walls run 1 m below the ground.

Pieces
  millennium_stand   five wave canopies on masts over three glazed floors and an open terrace; stair tower   168 x 26 m, 30 m
  rowley_stand       glazed base, an open seating terrace under a flat canopy, an upper floor, the clock cupola, a brick end   110 x 18 m, 24 m
  victorian_stand    two tiers under a hipped slate roof with dormers, lantern and chimneys; standing terrace in front; low wing   112 x 22 m, 19 m
  judges_kiosk       the white judge's kiosk with a pyramid cap                                              3 x 3 m, 6 m
  victorian_pavilion a small two-storey pavilion with an open balcony and a hipped roof                       11 x 8 m, 11 m
"""
import json, math, os
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(rp("tools/blender/kit.py")).read())

COL = {   # the pastel-street palette, as the July Course's pieces
    "white": "#f6f2ea", "cream": "#efe3cd", "glass": "#3f3a4d", "trim": "#f7efe2", "seat": "#9dbfa6", "concrete": "#e6d9c4",
    "fascia": "#e8b29b", "mast": "#f3f0ea", "brick": "#dc9c86", "slate": "#8f95a8", "roof": "#b4aaa2", "canvas": "#fbf8f1",
    "door": "#7f9f8c", "green": "#93b89e", "iron": "#5b6273", "bench": "#857f96",
}
MATS = {k: material("rm_" + k, v, rough=0.9) for k, v in COL.items()}
K = Kit()
CROWD = []


def area(x0, x1, y0, y1, z):
    CROWD.append([round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z, 2)])


def win(x, y, z0, w, h):
    K.window(x, y, z0, w, h, panes=False)


def side_window(xf, facing, y, z0, w, h):
    K.push(Matrix.Translation((xf, 0, 0)) @ Matrix.Rotation(math.pi / 2 * facing, 4, "Z"))
    K.window(y * facing, 0, z0, w, h, panes=False)
    K.pop()


def rod(mat, x, ya, za, yb, zb, r=0.04):
    K.prism_x(mat, x - r, x + r, [(ya, za), (yb, zb), (yb, zb + 2 * r), (ya, za + 2 * r)])


def gable_x(x0, x1, y0, y1, z, pitch, ov, roof="slate", wall="cream", trim="trim"):
    t, tn = 0.28, math.tan(math.radians(pitch))
    yc, half = (y0 + y1) / 2, (y1 - y0) / 2
    ez, rz = z - ov * tn, z + half * tn
    K.prism_x(roof, x0 - ov, x1 + ov, [(y0 - ov, ez), (y0 - ov, ez + t), (yc, rz + t), (y1 + ov, ez + t), (y1 + ov, ez), (yc, rz)])
    for xa, xb in ((x0, x0 + 0.25), (x1 - 0.25, x1)):
        K.prism_x(wall, xa, xb, [(y0, z - 0.02), (y1, z - 0.02), (yc, rz - 0.05)])
    K.box(trim, x0 - ov, x1 + ov, yc - 0.13, yc + 0.13, rz + t - 0.04, rz + t + 0.14)
    return rz


def gable_y(x0, x1, y0, y1, z, pitch, ov, **kw):
    K.push(Matrix.Rotation(math.pi / 2, 4, "Z"))
    rz = gable_x(y0, y1, -x1, -x0, z, pitch, ov, **kw)
    K.pop()
    return rz


def steps(mat, x0, x1, y0, z0, rows, tread, rise, seat=None, base=-1.0, crowd=True):
    """A stepped terrace from y0 back, starting at z0; benches in `seat` on each row; crowd areas on each row."""
    prof = [(y0, base)]
    for i in range(rows):
        prof += [(y0 + i * tread, z0 + i * rise), (y0 + (i + 1) * tread, z0 + i * rise)]
    prof += [(y0 + rows * tread, base)]
    K.prism_x(mat, x0, x1, prof)
    for i in range(rows):
        zi, yb = z0 + i * rise, y0 + (i + 1) * tread
        if seat:
            K.box(seat, x0 + 0.3, x1 - 0.3, yb - 0.4, yb - 0.08, zi, zi + 0.42)
        if crowd:
            area(x0 + 0.3, x1 - 0.3, yb - tread + 0.05, yb - (0.44 if seat else 0.1), zi)
    return y0 + rows * tread, z0 + (rows - 1) * rise


def sheet_solid(mat, fz, x0, x1, y0, y1, nx, ny, t):
    """A thin curved roof: the surface z = fz(x, y) over x0..x1, y0..y1, t thick, closed round its edges."""
    bm = K.bm(mat)
    def grid(dz):
        return [[bm.verts.new(K.M @ Vector((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny, fz(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny) + dz)))
                 for i in range(nx + 1)] for j in range(ny + 1)]
    top, bot = grid(0.0), grid(-t)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i])); f.smooth = True
            g = bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1])); g.smooth = True
    ring = [(j, 0) for j in range(ny)] + [(ny, i) for i in range(nx)] + [(j, nx) for j in range(ny, 0, -1)] + [(0, i) for i in range(nx, 0, -1)]
    for k in range(len(ring)):
        (ja, ia), (jb, ib) = ring[k], ring[(k + 1) % len(ring)]
        bm.faces.new((top[ja][ia], bot[ja][ia], bot[jb][ib], top[jb][ib]))


# ------------------------------------------------------------------------------------------ 1: the Millennium Grandstand
def millennium_stand(n=5, bay=32.0, D=26.0):
    """Interpretive and bigger than life: five wave canopies (the real stand has four)."""
    L = n * bay; h = L / 2
    # ground floor: dark glazing between cream piers, a cream band over it
    K.box("glass", -h, h, 0.6, D, -1.0, 4.4)
    for k in range(int(L // 8) + 1):
        x = -h + k * L / int(L // 8)
        K.box("cream", x - 0.45, x + 0.45, 0.2, 0.8, -1.0, 4.4)
    K.box("cream", -h - 0.2, h + 0.2, -0.4, D, 4.4, 5.0)
    # the open terrace: green seats stepping up, a white balustrade along its front
    yb, zt = steps("concrete", -h, h, 0.0, 5.3, 8, 1.05, 0.38, seat="seat")
    K.box("white", -h, h, -0.12, 0.05, 5.0, 6.2)
    K.box("glass", -h + 0.5, h - 0.5, yb - 0.05, yb + 0.05, zt + 0.4, 11.0)                 # the bars behind it
    # the boxes: a white slab over the terrace with the pink sponsor fascia, glazed floors with balconies above
    K.box("white", -h, h, 1.6, D, 11.0, 11.7)
    for k in range(n):
        x = -h + bay * (k + 0.5)
        K.box("fascia", x - bay * 0.38, x + bay * 0.38, 1.45, 1.6, 11.0, 12.6)
    K.box("white", -h, h, 1.55, 1.75, 12.6, 12.85)
    K.box("glass", -h, h, 3.4, D, 11.7, 15.6)
    K.box("white", -h, h, 1.6, 3.4, 11.7, 11.95)
    K.balustrade(-h, h, 1.75, 11.95, h=1.0, mat="white", spacing=0.6, piers=False)
    K.box("white", -h, h, 1.6, D, 15.6, 16.3)
    K.box("glass", -h, h, 5.0, D, 16.3, 19.8)
    K.balustrade(-h, h, 1.8, 16.3, h=1.0, mat="white", spacing=0.6, piers=False)
    K.box("white", -h, h, 1.6, D + 0.5, 19.8, 20.5)
    for x in (-h, h):                                                     # cream end walls
        K.box("cream", x - 0.4, x + 0.4, 0.0, D + 0.5, -1.0, 20.5)
    # the wave canopies: each a vault across its bay, rising towards the front and cantilevered over the balconies
    def fz(x, y, xc):
        t = (x - (xc - bay / 2)) / bay
        rise = 2.6 * (D + 3 - y) / (D + 9)
        return 21.2 + rise + 5.0 * math.sin(math.pi * t) ** 0.8
    for k in range(n):
        xc = -h + bay * (k + 0.5)
        sheet_solid("canvas", lambda x, y, xc=xc: fz(x, y, xc), xc - bay / 2 + 0.3, xc + bay / 2 - 0.3, -6.0, D + 3.0, 16, 8, 0.22)
    # masts between the canopies with stays out to the canopies' front edges
    for k in range(n + 1):
        x = -h + bay * k
        K.cyl("mast", x, D * 0.45, 20.5, 31.5, 0.32, 0.22, segs=10)
        K.sphere("mast", x, D * 0.45, 31.6, 0.35, sub=1)
        for s_ in (-1, 1):
            xe = x + s_ * bay * 0.32
            if -h < xe < h:
                v = Vector((xe - x, -6.0 - D * 0.45, fz(xe, -6.0, x + s_ * bay / 2) - 31.0)); m = v.length
                rot = Vector((0, 0, 1)).rotation_difference(v.normalized()).to_matrix().to_4x4()
                K.push(Matrix.Translation((x, D * 0.45, 31.0)) @ rot)
                K.cyl("mast", 0, 0, 0, m, 0.05, segs=4, smooth=False)
                K.pop()
    # the glazed stair tower at the right-hand end, with pale green bands
    tx0, tx1 = h + 0.4, h + 9.0
    K.box("glass", tx0, tx1, 2.0, D - 2.0, -1.0, 24.0)
    for z in range(2, 24, 3):
        K.box("green", tx0 - 0.08, tx1 + 0.08, 1.92, D - 1.92, z, z + 0.45)
    for xx in (tx0, tx1):
        K.box("white", xx - 0.3, xx + 0.3, 1.7, D - 1.7, -1.0, 24.6)
    K.box("white", tx0 - 0.3, tx1 + 0.3, 1.7, D - 1.7, 24.0, 24.7)
    return {"width": L + 18.8, "depth": D + 3.0, "height": 31.9, "offset": (tx1 + 0.3 - h) / 2}


# ------------------------------------------------------------------------------------------ 1b: the Rowley stand
def rowley_stand(L=110.0, D=18.0):
    h = L / 2
    K.box("glass", -h, h, 0.6, D, -1.0, 4.0)
    for k in range(int(L // 7) + 1):
        x = -h + k * L / int(L // 7)
        K.box("cream", x - 0.4, x + 0.4, 0.2, 0.8, -1.0, 4.0)
    K.box("cream", -h, h, -0.3, D, 4.0, 4.6)
    yb, zt = steps("concrete", -h, h - 12.0, 0.0, 4.9, 9, 0.95, 0.36, seat="seat")
    K.box("white", -h, h - 12.0, -0.12, 0.05, 4.6, 5.8)
    K.box("glass", -h + 0.5, h - 12.5, yb - 0.05, yb + 0.05, zt + 0.4, 10.4)
    K.box("cream", -h, h - 12.0, yb, D, 4.6, 10.4)
    K.box("white", -h - 0.3, h - 12.0, -1.2, D, 10.4, 11.1)                              # the flat canopy
    K.box("white", -h - 0.3, h - 12.0, -1.3, -1.0, 9.9, 11.2)
    for k in range(int((L - 12) // 9) + 1):                                              # slim columns under it
        x = -h + 1.0 + k * (L - 14.0) / int((L - 12) // 9)
        K.box("iron", x - 0.12, x + 0.12, -0.8, -0.56, 4.6, 10.4)
    K.box("cream", -h, h - 12.0, 5.0, D, 11.1, 14.3)                                      # the top floor, set back
    for k in range(int((L - 14) // 4)):
        win(-h + 2.5 + k * 4.0, 5.0, 11.9, 2.2, 1.6)
    K.box("white", -h - 0.2, h - 11.8, 4.7, D + 0.2, 14.3, 14.8)
    # the clock cupola on the roof
    cx = -h + (L - 12) * 0.62
    K.box("cream", cx - 1.8, cx + 1.8, 9.0, 12.6, 14.8, 18.0)
    K.disc_y("trim", cx, 8.92, 9.0, 16.4, 1.0, segs=20)
    K.cyl("white", cx, 10.8, 18.0, 20.6, 1.45, segs=12)
    K.cyl("slate", cx, 10.8, 20.6, 22.3, 1.6, 0.15, segs=12)
    K.cyl("iron", cx, 10.8, 22.3, 24.2, 0.05, segs=4, smooth=False)
    K.box("iron", cx - 0.6, cx + 0.6, 10.78, 10.82, 23.5, 23.8)
    # the brick block at the right-hand end
    K.box("brick", h - 12.0, h, -0.4, D + 1.0, -1.0, 16.0)
    K.box("trim", h - 12.15, h + 0.15, -0.55, D + 1.15, 16.0, 16.35)
    for z in (1.0, 5.0, 9.0, 12.6):
        for x in (h - 9.0, h - 3.0):
            win(x, -0.4, z, 1.6, 1.8)
    return {"width": L, "depth": D + 1.0, "height": 24.2}


# ------------------------------------------------------------------------------------------ 3: the old Victorian stand
def victorian_stand(L=96.0, D=16.0):
    h = L / 2
    # the standing terrace in front, packed in the photo
    steps("concrete", -h, h, -6.5, 0.35, 5, 1.2, 0.3)
    # the ground floor: cream rooms with plain windows, an upper deck of seats under the roof
    K.box("cream", -h, h, 0.0, D, -1.0, 4.8)
    for k in range(int(L // 4.0)):
        win(-h + 2.0 + k * 4.0, 0.0, 1.0, 1.6, 2.2)
    K.box("trim", -h - 0.2, h + 0.2, -0.3, D, 4.8, 5.3)
    yb, zt = steps("concrete", -h + 0.3, h - 0.3, 0.3, 5.6, 7, 1.15, 0.42, seat="bench")
    K.balustrade(-h, h, 0.2, 5.3, h=1.0, mat="trim", spacing=0.32)
    K.box("cream", -h, h, D - 0.5, D, 5.3, 11.4)
    for x in (-h, h):
        K.box("cream", x - 0.3, x + 0.3, 0.0, D, 5.3, 11.4)
    for k in range(int(L // 6.0) + 1):                                    # slender posts carrying the roof
        x = -h + k * L / int(L // 6.0)
        K.box("trim", x - 0.13, x + 0.13, 0.05, 0.31, 5.3, 11.2)
    K.box("trim", -h - 0.2, h + 0.2, -0.05, 0.4, 11.0, 11.4)
    # the big hipped slate roof, with gablet dormers, a lantern and flag, chimneys
    K.hip_roof(-h, h, 0.0, D, 11.4, 5.2, ov=0.9, mat="slate")
    tn = 5.2 / (D / 2 + 0.9)
    for k in range(5):
        x = -h + L * (k + 0.5) / 5
        z0 = 11.4 + 2.0 * tn
        K.box("cream", x - 1.5, x + 1.5, 1.2, 4.0, z0 - 1.2, z0 + 1.0)
        gable_y(x - 1.5, x + 1.5, 1.2, 4.0, z0 + 1.0, 42, 0.25)
        win(x, 1.2, z0 - 0.7, 1.2, 1.3)
    rz = 11.4 + 5.2
    K.box("cream", -2.2, 2.2, D / 2 - 2.2, D / 2 + 2.2, rz - 1.0, rz + 2.0)
    K.hip_roof(-2.2, 2.2, D / 2 - 2.2, D / 2 + 2.2, rz + 2.0, 1.8, ov=0.3, mat="slate")
    K.cyl("iron", 0.0, D / 2, rz + 3.6, rz + 7.0, 0.05, segs=4, smooth=False)
    K.box("fascia", 0.05, 1.3, D / 2 - 0.03, D / 2 + 0.03, rz + 6.0, rz + 6.8)
    for x in (-h * 0.62, h * 0.62, -h * 0.2, h * 0.2):
        K.box("brick", x - 0.6, x + 0.6, D / 2 - 0.4, D / 2 + 0.8, rz - 2.0, rz + 1.8)
        K.box("trim", x - 0.72, x + 0.72, D / 2 - 0.52, D / 2 + 0.92, rz + 1.8, rz + 2.0)
    # the low wing at the left-hand end, gable to the front
    wx0, wx1 = -h - 15.0, -h - 0.2
    K.box("cream", wx0, wx1, 1.5, D, -1.0, 6.5)
    for k in range(3):
        win(wx0 + 2.5 + k * 5.0, 1.5, 1.2, 1.6, 2.2)
    gable_x(wx0, wx1, 1.5, D, 6.5, 32, 0.5)
    gable_y(wx0 + 3.0, wx0 + 10.0, -1.0, 1.5, 6.5, 40, 0.3)
    K.box("cream", wx0 + 3.0, wx0 + 10.0, -1.0, 1.5, -1.0, 6.5)
    return {"width": L + 15.0, "depth": D, "height": rz + 7.0, "offset": -7.5}


def judges_kiosk(S=2.6):
    h = S / 2
    K.box("concrete", -h - 0.4, h + 0.4, -0.4, S + 0.4, -0.5, 0.3)
    K.box("white", -h, h, 0.0, S, 0.3, 3.6)
    win(0.0, 0.0, 1.6, 1.4, 1.4)
    for f, xf in ((1, h), (-1, -h)):
        side_window(xf, f, S / 2, 1.6, 1.2, 1.4)
    K.hip_roof(-h, h, 0.0, S, 3.6, 1.9, ov=0.3, mat="white")
    K.sphere("white", 0.0, S / 2, 5.75, 0.18, sub=1)
    return {"width": S + 0.8, "depth": S + 0.8, "height": 6.0}


def victorian_pavilion(Lx=10.0, D=8.0):
    h = Lx / 2
    K.box("cream", -h, h, 0.0, D, -1.0, 4.0)
    for x in (-3.0, 3.0):
        win(x, 0.0, 1.0, 1.4, 2.0)
    K.door(0.0, 0.0, 0.0, 1.3, 2.5)
    K.box("trim", -h - 0.4, h + 0.4, -1.2, D, 4.0, 4.3)
    K.balustrade(-h - 0.3, h + 0.3, -1.05, 4.3, h=1.0, mat="trim", spacing=0.3)
    for x in (-h - 0.2, -h / 2, 0.0, h / 2, h + 0.2):
        K.box("trim", x - 0.1, x + 0.1, -1.15, -0.95, 4.3, 7.4)
    K.box("cream", -h, h, 1.0, D, 4.3, 7.4)
    for x in (-2.5, 2.5):
        win(x, 1.0, 5.0, 1.4, 1.8)
    K.hip_roof(-h - 0.4, h + 0.4, -1.2, D, 7.4, 2.8, ov=0.5, mat="slate")
    return {"width": Lx + 1.0, "depth": D + 1.2, "height": 10.5}


PIECES = [
    ("millennium_stand", millennium_stand),
    ("rowley_stand", rowley_stand),
    ("victorian_stand", victorian_stand),
    ("judges_kiosk", judges_kiosk),
    ("victorian_pavilion", victorian_pavilion),
]
LIB = bpy.data.collections.new("rowley_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
MIRROR = {"millennium_stand", "rowley_stand"}    # built with the tower / brick end on the right, then mirrored so they
                                                 # stand at the up-course end (the left as seen from the track)
for name, fn in PIECES:
    CROWD.clear()
    if name in MIRROR: K.push(Matrix.Diagonal((-1, 1, 1, 1)))
    info = fn()
    if name in MIRROR:
        K.pop()
        CROWD[:] = [[-c[1], -c[0], c[2], c[3], c[4]] for c in CROWD]
        if "offset" in info: info["offset"] = -info["offset"]
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-18s %6d triangles, %d crowd areas" % (name, tris, len(CROWD)), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "The Rowley Mile's stand-side buildings (tools/blender/build_rowley_stands.py). Building axes: x along "
                     "the front (left to right from the track), y into the building (front faces -y), z up; origin the "
                     "middle of the main block's front on the ground (offset: how far the whole piece's middle is from "
                     "it along x). crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "rowley_stands.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "rowley_stands.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
os.makedirs(rp("assets/models/master"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=rp("assets/models/master/rowley_stands.blend"), compress=True)
print("exported rowley_stands.glb", flush=True)
