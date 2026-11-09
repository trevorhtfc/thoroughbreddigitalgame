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
  millennium_stand   the Millennium's form (four wave canopies on masts over a deep block) with Ascot's heritage dress: a terrace from the lawn, a colonnade and covered terrace, balconies, a veranda   113 x 44 m, 50 m
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
    # Ascot's heritage palette, as the finish study (stand_clean_study.py): cream walls, a warmer stone for the base and
    # pilasters, dark green ironwork, gilt finials, a clock face
    "wall": "#ecdcc0", "podium": "#dccaa8", "ironwork": "#4f6b5a", "gilt": "#c8a466", "clock": "#fbf5ea", "clockdark": "#2a2c30",
}
# The flanking stands are Ascot's grand pavilion, built with Ascot's own piece code (stand_pieces.py), so they take
# Ascot's colours for the parts only that code uses (owner, 9 Nov: "quite literally applying the architecture of the
# grand pavilion"): the canopy roof, the cream iron lace and the steps
ASCOT_COL = json.load(open(rp("assets/models/architecture/victorian_grandstand_layout.json")))["colours"]
COL.update({k: ASCOT_COL[k] for k in ("roof", "iron", "steps")})
MATS = {k: material("rm_" + k, v, rough=0.9) for k, v in COL.items()}
K = Kit()
CROWD = []


def area(x0, x1, y0, y1, z):
    CROWD.append([round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z, 2)])


# ------------------------------------------------------------------------------------------ Ascot's pieces
STAND_CAT = json.load(open(rp("assets/models/architecture/stand_modules.json")))
S, P, BAY = STAND_CAT["storey"], STAND_CAT["podium"], STAND_CAT["bay"]


def stand_area(x0, x1, y0, y1, z, kind):
    a = K.M @ Vector((x0, y0, z)); b = K.M @ Vector((x1, y1, z))
    area(min(a.x, b.x), max(a.x, b.x), min(a.y, b.y), max(a.y, b.y), a.z)


exec(open(rp("tools/blender/stand_pieces.py")).read())


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
def millennium_stand(n=4, bay=28.0, D=42.0):
    """The Millennium Grandstand's form and proportion (four wave canopies on masts over a deep block) dressed with the
    Royal Ascot stand's old-school details (owner, 8 Nov: "something about it is still not convincing. The steps should
    come down to ground. The raised platform isn't helping... take the form and proportion of the new stand but
    integrate some of the Royal Ascot old school vibe into it, so it feels more heritage"):
    a standing terrace that steps up from the lawn; cream walls with pilasters at the bay lines and deep cornices;
    balconies with balustrades; a veranda on dark green iron columns; the canopies on dark green masts with gilt
    finials. Then (on the second look): a colonnade of straight piers with a covered terrace behind, in place of the
    arches; no ring beam along the canopies' front; no clock tower; deeper, the canopies reaching further out."""
    L = n * bay; h = L / 2
    rows, tread, rise = 26, 1.0, 0.2         # owner: a much shallower rake, so the terrace comes much further forward
    yf = rows * tread + 0.4                                           # the building's face, behind the terrace
    # the terrace: from the lawn straight up to the arcade, a low balustrade along its foot, benches on the rows
    K.box("wall", -h, h, -0.35, 0.0, -1.0, 1.0)                                  # a plain low wall at its foot
    K.box("trim", -h - 0.05, h + 0.05, -0.42, 0.07, 1.0, 1.12)
    yb, zt = steps("concrete", -h, h, 0.0, 0.3, rows, tread, rise)                   # plain standing steps
    K.box("concrete", -h, h, yb, yf + 0.5, -1.0, zt)
    z1 = zt + 0.05                                                     # the gallery floor, level with the top row
    # a colonnade of plain square piers carrying an entablature (owner, 8 Nov: straight piers rather than arches),
    # with a deep covered terrace behind it, level with the top row
    span, pier = bay / 4, 1.2
    zc = z1 + 5.2
    K.box("glass", -h, h, yf + 7.6, yf + 7.8, z1, zc)
    K.box("concrete", -h, h, yf, yf + 7.8, z1 - 0.4, z1)
    for k in range(n * 4 + 1):
        x = -h + k * span
        K.box("wall", x - pier / 2, x + pier / 2, yf, yf + pier, z1, zc)            # plain square piers
    area(-h + 0.6, h - 0.6, yf + 1.4, yf + 7.2, z1)
    K.box("wall", -h, h, yf, yf + 2.4, zc, zc + 1.0)
    # three upper floors (owner, 8 Nov: "a bit low... add extra height by another terrace", "strip out some of the
    # extra detail"): each a balcony with a plain solid parapet in front of tall windows in cream walls
    z = zc + 1.5
    for lv in range(3):
        H = 4.6
        K.box("wall", -h, h, yf + 2.4, D, z, z + H)
        for k in range(int(L // 3.5)):
            win(-h + 1.75 + k * 3.5, yf + 2.4, z + 0.6, 1.5, 2.8)
        K.box("podium", -h - 0.2, h + 0.2, yf - 0.2, yf + 2.6, z - 0.35, z)                 # the balcony slab
        K.box("wall", -h - 0.2, h + 0.2, yf - 0.2, yf + 0.05, z, z + 1.05)                  # its parapet
        K.box("trim", -h - 0.25, h + 0.25, yf - 0.28, yf + 0.12, z + 1.05, z + 1.17)
        area(-h + 0.4, h - 0.4, yf + 0.4, yf + 2.2, z)
        z += H
    K.box("wall", -h, h, yf + 2.4, D, z, z + 1.4)
    K.cornice(-h, h, yf + 2.0, D, z + 1.4, ov=0.6, h=0.6)
    deck = z + 2.0
    # pilasters at the bay lines, full height, and the ends in cream with windows and cornices
    for j in range(n + 1):
        x = -h + bay * j
        K.box("podium", x - 0.9, x + 0.9, yf - 0.35, yf + 0.1, z1, zc + 1.0)
        K.box("podium", x - 0.9, x + 0.9, yf + 2.0, yf + 2.45, zc + 1.0, deck - 0.6)
    for x, f in ((-h, -1), (h, 1)):
        K.box("wall", x - 0.5 * f - 0.5, x - 0.5 * f + 0.5, yf, D + 0.5, -1.0, deck)
        for zz in (z1 + 1.0, zc + 2.2, zc + 6.8):
            for y in (yf + 6.0, yf + 11.0, D - 4.0):
                side_window(x + 0.5 * f, f, y, zz, 1.4, 2.4)
    # the wave canopies: vaults across the bays springing from the cornice, rising towards the front
    def fz(x, y, xc):
        t = min(max((x - (xc - bay / 2)) / bay, 0.0), 1.0)
        rise_ = 1.5 * (D + 2 - y) / (D + 2 - yf + 9)                     # a gentle lift to the front: springing
        return deck - 0.3 + rise_ + 6.5 * math.sin(math.pi * t) ** 0.75     # straight off the top cornice
    y0c = yf - 11.0                                                   # the canopies reach well out over the terrace
    for k in range(n):
        xc = -h + bay * (k + 0.5)
        sheet_solid("canvas", lambda x, y, xc=xc: fz(x, y, xc), xc - bay / 2 + 0.35, xc + bay / 2 - 0.35, y0c, D + 2.0, 18, 10, 0.25)
    # the frame: ribs along the troughs, a ring beam along the front, dark green masts with gilt finials and stays
    for j in range(n + 1):
        x = -h + bay * j
        p0, p1 = (y0c, fz(x, y0c, x + bay / 2)), (D + 2.0, fz(x, D + 2.0, x + bay / 2))     # along the trough
        K.prism_x("trim", x - 0.45, x + 0.45, [(p0[0], p0[1] - 0.9), (p1[0], p1[1] - 0.9), (p1[0], p1[1] + 0.35), (p0[0], p0[1] + 0.35)])
        mz, my = deck + 17.0, yf + (D - yf) * 0.45
        K.cyl("ironwork", x, my, deck - 2.0, mz, 0.45, 0.3, segs=10)
        K.sphere("gilt", x, my, mz + 0.35, 0.55, sub=1)
        for s_ in (-1, 1):
            for f_ in (0.22, 0.42):
                for ye in (y0c, D + 2.0):
                    xe = x + s_ * bay * f_
                    if not (-h <= xe <= h):
                        continue
                    xc = -h + bay * (math.floor((xe + h) / bay) + 0.5)
                    v = Vector((xe - x, ye - my, fz(xe, ye, xc) + 0.2 - mz)); m = v.length
                    rot = Vector((0, 0, 1)).rotation_difference(v.normalized()).to_matrix().to_4x4()
                    K.push(Matrix.Translation((x, my, mz)) @ rot)
                    K.cyl("ironwork", 0, 0, 0, m, 0.06, segs=4, smooth=False)
                    K.pop()
    return {"width": L + 1.0, "depth": D + 2.0, "height": deck + 17.6}


# ------------------------------------------------------------------------------------------ 1b: the Rowley stand
def rowley_stand(L=110.0, cupola=True, brick=True, rows=26, tread=1.0, rise=0.2):
    """The Rowley stand, from the owner's photo (rowley-stand-photo.jpg) and notes (8 Nov): slim profiles, projecting
    roofs, and a terrace down to the ground that runs on from the Millennium's (the same shallow rake): a low
    canopy on slim posts over the back of the terrace, glazed boxes and a balcony of seats above, a thin roof projecting
    well out over them, the clock cupola, a brick end."""
    h = L / 2
    eb = 12.0 if brick else 0.0
    x0, x1 = -h, h - eb
    yb, zt = steps("concrete", -h, h, 0.0, 0.25, rows, tread, rise)            # the terrace, from the lawn
    D = yb + 11.0
    # behind the terrace top: a glazed concourse under the low canopy, the cream block behind everything
    K.box("glass", x0, x1, yb, yb + 0.2, zt, zt + 3.4)
    K.box("cream", x0, x1, yb + 0.2, D, -1.0, zt + 9.0)
    # the low canopy: a thin white slab on slim posts over the back of the terrace
    yc0 = yb - 9.0
    K.box("white", x0 - 0.3, x1, yc0, yb + 0.2, zt + 3.4, zt + 3.7)
    n = max(2, round((x1 - x0) / 8.0))
    for k in range(n + 1):
        x = x0 + 0.4 + (x1 - x0 - 0.8) * k / n
        zb = 0.25 + int((yc0 + 0.4) / tread) * rise
        K.box("iron", x - 0.09, x + 0.09, yc0 + 0.3, yc0 + 0.48, zb, zt + 3.4)
    # above it: a balcony of green seats stepping back to glazed boxes, a thin roof projecting well out
    yb2, zt2 = steps("concrete", x0, x1, yb - 3.0, zt + 3.7, 5, 0.9, 0.34, seat="seat")
    K.box("white", x0, x1, yb - 3.12, yb - 3.0, zt + 3.7, zt + 4.7)
    K.box("glass", x0, x1, yb2, yb2 + 0.2, zt2 + 0.3, zt + 9.0)
    K.box("white", x0 - 0.3, x1, yb - 8.0, D + 0.3, zt + 9.0, zt + 9.3)              # the upper roof
    K.box("white", x0 - 0.3, x1, yb - 8.1, yb - 7.9, zt + 8.75, zt + 9.35)           # its slim front edge
    for k in range(int((x1 - x0) // 4)):                                             # windows in the block's top
        win(x0 + 2.0 + k * 4.0, yb2 + 0.2, zt + 9.6, 2.2, 1.4)
    K.box("cream", x0, x1, yb2 + 0.2, D, zt + 9.3, zt + 11.6)
    K.box("white", x0 - 0.2, x1 + 0.2, yb2, D + 0.2, zt + 11.6, zt + 11.9)
    top = zt + 11.9
    if cupola:
        cx = x0 + (x1 - x0) * 0.62; cy = (yb2 + D) / 2
        K.box("cream", cx - 1.8, cx + 1.8, cy - 1.8, cy + 1.8, top, top + 3.0)
        K.disc_y("trim", cx, cy - 1.88, cy - 1.8, top + 1.6, 1.0, segs=20)
        K.cyl("white", cx, cy, top + 3.0, top + 5.4, 1.45, segs=12)
        K.cyl("slate", cx, cy, top + 5.4, top + 7.0, 1.6, 0.15, segs=12)
        K.cyl("iron", cx, cy, top + 7.0, top + 8.8, 0.05, segs=4, smooth=False)
        K.box("gilt", cx - 0.6, cx + 0.6, cy - 0.02, cy + 0.02, top + 8.1, top + 8.4)
    if brick:
        K.box("brick", h - eb, h, yb - 4.0, D + 1.0, -1.0, top + 1.5)
        K.box("trim", h - eb - 0.15, h + 0.15, yb - 4.15, D + 1.15, top + 1.5, top + 1.85)
        for z in (zt + 0.6, zt + 4.4, zt + 8.0):
            for x in (h - 9.0, h - 3.0):
                win(x, yb - 4.0, z, 1.6, 1.8)
    return {"width": L, "depth": D + 1.0, "height": top + 8.8}


# ------------------------------------------------------------------------------------------ 3: the old Victorian stand
def victorian_stand(L=128.0, rows=24, tread=1.0, rise=0.28):
    """The old stand (owner's photos old-stand-victorian.png, old-stand-photo-2.jpg; 8 Nov: "a bit bigger... again bring
    the terraces to ground", a shallow rake): a long open stand of seats rising from the lawn under a big slate roof on
    slim posts, rooms behind, gablet dormers and chimneys, and an end pavilion with a clock turret."""
    h = L / 2
    yb, zt = steps("concrete", -h, h, 0.0, 0.3, rows, tread, rise, seat="bench")
    D = yb + 7.0
    K.box("cream", -h, h, yb, D, -1.0, zt + 4.2)                                      # the rooms behind
    for k in range(int(L // 4.0)):
        win(-h + 2.0 + k * 4.0, yb, zt + 1.0, 1.4, 2.0)
    for k in range(int(L // 6.0) + 1):                                                # slim posts along the front
        x = -h + k * L / int(L // 6.0)
        K.box("trim", x - 0.12, x + 0.12, -1.3, -1.06, -0.5, 7.2)
    K.box("trim", -h - 0.3, h + 0.3, -1.6, -0.9, 6.9, 7.3)
    K.hip_roof(-h, h, -1.5, D, 7.3, 6.0, ov=0.6, mat="slate")
    tn = 6.0 / ((D + 1.5) / 2 + 0.6)
    for k in range(7):                                                                # gablet dormers on the front slope
        x = -h + L * (k + 0.5) / 7
        z0 = 7.3 + 3.5 * tn
        K.box("cream", x - 1.4, x + 1.4, 2.0, 4.6, z0 - 1.2, z0 + 0.9)
        gable_y(x - 1.4, x + 1.4, 2.0, 4.6, z0 + 0.9, 42, 0.25)
        win(x, 2.0, z0 - 0.7, 1.1, 1.2)
    rz = 7.3 + 6.0
    for x in (-h * 0.6, -h * 0.15, h * 0.3):
        K.box("brick", x - 0.6, x + 0.6, (D - 1.5) / 2 - 0.4, (D - 1.5) / 2 + 0.8, rz - 2.5, rz + 1.6)
        K.box("trim", x - 0.72, x + 0.72, (D - 1.5) / 2 - 0.52, (D - 1.5) / 2 + 0.92, rz + 1.6, rz + 1.8)
    # the end pavilion (right as seen from the track), two storeys under its own roof, with a clock turret
    px0, px1 = h, h + 16.0
    K.box("cream", px0, px1, -1.0, D, -1.0, 10.5)
    for z in (1.0, 5.5):
        for x in (px0 + 3.0, px0 + 8.0, px0 + 13.0):
            win(x, -1.0, z, 1.6, 2.4)
    K.hip_roof(px0, px1, -1.0, D, 10.5, 5.0, ov=0.5, mat="slate")
    tc, tyc = (px0 + px1) / 2, 4.0
    K.box("cream", tc - 1.6, tc + 1.6, tyc - 1.6, tyc + 1.6, 12.0, 16.6)
    K.disc_y("trim", tc, tyc - 1.68, tyc - 1.6, 15.0, 0.9, segs=20)
    K.hip_roof(tc - 1.6, tc + 1.6, tyc - 1.6, tyc + 1.6, 16.6, 1.6, ov=0.25, mat="slate")
    K.cyl("iron", tc, tyc, 18.2, 20.6, 0.05, segs=4, smooth=False)
    K.box("gilt", tc - 0.5, tc + 0.5, tyc - 0.02, tyc + 0.02, 19.9, 20.2)
    K.box("brick", px1 - 3.0, px1 - 1.8, D - 4.0, D - 2.8, 12.0, 17.5)
    return {"width": L + 16.0, "depth": D, "height": 20.6, "offset": 8.0}


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


# ------------------------------------------------------------------------------------------ 9 Nov: grand pavilions
def ascot_end_pavilion(x0, x1, D, tiers):
    """Ascot's end pavilion (as build_stand_modules.end_pavilion): a two-tier veranda pavilion with a wraparound
    balcony on its dressed (right) end, a hipped roof and a small square cupola."""
    veranda({"x0": x0, "x1": x1, "tiers": tiers, "depth": D, "setback": 0.0, "roof": "none"})
    zt = P + tiers * S + 0.6
    xo = x1 + 1.6
    for k in range(tiers):
        z = P + k * S
        hh = S + (0.6 if k == tiers - 1 else 0)
        K.box("trim", x1, xo, -0.25, D, z - 0.3, z)
        n = max(2, round(D / BAY))
        for i in range(n + 1):
            K.cyl("trim", xo - 0.35, D * i / n, z, z + hh, 0.15, 0.12)
        K.box("trim", xo - 0.5, xo - 0.2, 0, D, z + hh - 0.3, z + hh)
        K.balustrade(0.0, D, xo - 0.35, z, axis="y", piers=False)
        stand_area(x1 + 0.2, xo - 0.6, 0.6, D - 0.6, z, "veranda")
    K.box("podium", x1, xo, 0, D, 0, P)
    K.hip_roof(x0, xo, -0.2, D, zt - 0.6, 2.6, 0.8)
    cx, cy, cw = (x0 + xo) / 2, D / 2, 3.2
    zc = zt - 0.6 + 2.6 - 0.4
    K.box("wall", cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zc, zc + 1.7)
    for rot in range(4):
        K.push(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rot * math.pi / 2, 4, "Z") @ Matrix.Translation((-cx, -cy, 0)))
        for j in (-0.8, 0.0, 0.8):
            K.box("glass", cx + j - 0.28, cx + j + 0.28, cy - cw / 2 - 0.05, cy - cw / 2 + 0.05, zc + 0.3, zc + 1.4)
        K.pop()
    K.cornice(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zc + 1.7, 0.25, 0.25)
    K.hip_roof(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zc + 1.95, 1.2, 0.35)
    K.cyl("gilt", cx, cy, zc + 3.1, zc + 3.9, 0.04, 0.01, 6)


def grand_pavilion_stand(bays, rows, tread, rise, end_pavilion=False):
    """The flanking stands (owner, 9 Nov): Ascot's grand pavilion, quite literally (the terrace profile under the
    grand canopy with its glazed ridge lantern), behind a lower tier of terrace that rises from the lawn at the Rowley
    Mile's shallow rake to just under the boxes' ledge (the podium). Origin: the middle of the lawn terrace's foot.
    end_pavilion: Ascot's end pavilion on the right as seen from the track (the old stand's clock-turret end)."""
    L, T, z0 = bays * BAY, rows * tread, 0.25
    h = L / 2
    prof = [(0.0, -1.0)]                                                           # the lawn terrace, foot at y = 0
    for i in range(rows):
        prof += [(i * tread, z0 + i * rise), ((i + 1) * tread, z0 + i * rise)]
        area(-h + 0.3, h - 0.3, i * tread + 0.1, (i + 1) * tread - 0.1, z0 + i * rise)
    prof += [(T, -1.0)]
    K.prism_x("steps", -h, h, prof)
    for xa, xb in ((-h - 0.3, -h), (h, h + 0.3)):                                  # low cheek walls at its ends
        K.box("podium", xa, xb, 0.0, T, -1.0, z0 + rows * rise + 0.6)
    K.push(Matrix.Translation((-h, T, 0.0)))
    t = canopy_terrace({"x0": 0.0, "x1": L, "depth": 18.0, "party": ()}, grand=True)
    if end_pavilion:
        ascot_end_pavilion(L, L + 4 * BAY - 1.6, 16.0, 2)
    K.pop()
    width = L + (4 * BAY if end_pavilion else 0.0)
    info = {"width": width, "depth": T + 19.0, "height": round(terrace_top(18.0) + 9.6, 2)}
    if end_pavilion:
        info["offset"] = 2 * BAY
    return info


PIECES = [
    ("millennium_stand", millennium_stand),
    # 9 Nov: the flanking stands become Ascot's grand pavilion behind a lawn terrace (same names, so the layout, the
    # previews and the race view pick them up); rowley_stand is the full-length version, kept for reference
    ("rowley_stand", lambda: grand_pavilion_stand(31, 14, 1.0, 0.2)),
    # owner's sketch (8 Nov): the pavilion stand cranks round by the winning line: a wing in line with the Millennium,
    # then an end stand at right angles to the track, past the post, looking back up the course
    ("rowley_wing", lambda: grand_pavilion_stand(12, 14, 1.0, 0.2)),                  # 42 m
    ("rowley_end", lambda: grand_pavilion_stand(24, 14, 1.0, 0.2)),                   # 84 m
    ("victorian_stand", lambda: grand_pavilion_stand(37, 10, 1.0, 0.28, end_pavilion=True)),   # 129.5 m + 14 m
    ("judges_kiosk", judges_kiosk),
    ("victorian_pavilion", victorian_pavilion),
]
LIB = bpy.data.collections.new("rowley_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
MIRROR = {"millennium_stand", "rowley_stand", "rowley_wing", "rowley_end"}    # built with the tower / brick end on the right, then mirrored so they
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
