"""Sandown Park's stand side, modelled from the owner's photos (19 Nov 2026), in the kit's soft clay finish.

    python3.11 -c "exec(open('tools/blender/build_sandown_stands.py').read())"           # build and export
    SHEET=1 python3.11 -c "exec(open('tools/blender/build_sandown_stands.py').read())"   # also concept renders

Owner, 19 Nov 10:02: "two main grandstands with a tent like pavillion to the rear", with three photos: the main stand
from the course (a huge crowd on the terraces down to the lawn, two bands of glazed boxes, a very deep flat roof whose
underside is ribbed); the main stand and the Eclipse stand beside it from the hurdles course (the roof slab carries a
row of sloping fins on top; a glazed stair at the main stand's end; the Eclipse a five-storey block of glass-fronted
balconies between glazed end bays, a clock on top under a little glass sawtooth canopy, a tall blank clad wall on its
side towards the main stand, a brick plinth wall); and the parade ring behind, under a row of white peaked tents on
masts along the main stand's rear. His Google Maps views (10:00-10:01) show the stands on the hill on the south side,
the tents' white peaks showing above the main stand's back.

The pieces (building axes as every kit piece: x along the front, left to right seen from the track; y into the building,
the front faces -y; z up; origin the middle of the front on the ground):
  sandown_main_stand     the main (Esher) stand: standing terraces from the lawn up to a glazed concourse, a balcony,
                         two storeys of boxes, the deep cantilevered roof with its ribbed underside and the fins on top,
                         and at the back the row of white peaked tents over a terrace (the "pavilion to the rear")
  sandown_eclipse_stand  the Eclipse stand: a brick plinth, four storeys of balconies with glass fronts, the set-back top
                         floor under a glass sawtooth canopy, the clock, glazed end bays and the blank clad block on its
                         left (towards the main stand)
Stand ends follow the owner's rule: flank walls following the terraces' rake, never towers or end blocks (the Eclipse's
glazed bays are part of its front, the height of the block, not towers).

Writes assets/models/architecture/sandown_stands_kit.glb and .json (sizes, crowd areas), and with SHEET=1
reference/sandown/renders/stands-concept-*.png.
"""
import json, math, os
REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)
exec(open(rp("tools/blender/kit.py")).read())

COL = {
    "render": "#efe6d8", "trim": "#f6f1e8", "concrete": "#e2d7c5", "steps": "#e7ddcc", "glass": "#3f3a4d",
    "soffit": "#8d7f78", "rib": "#efe9df", "fin": "#f3f1ec", "clad": "#c8ccd4", "clad_dark": "#b3b8c3",
    "clad_glass": "#8a9cb2", "brick": "#b9765f", "tent": "#f8f5ef", "mast": "#e9e6e0", "iron": "#5b6273",
    "roof": "#d8d1c5", "lawn_wall": "#cdbfa9", "clock": "#fbf8f1", "clock_hand": "#3b3a44", "door": "#7f9f8c",
    "accent": "#9cc0b4",
}
MATS = {k: material("sd_" + k, v, rough=0.9) for k, v in COL.items()}
K = Kit()
CROWD = []


def area(x0, x1, y0, y1, z):
    CROWD.append([round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z, 2)])


def terraces(x0, x1, y0, z0, rows, tread, rise, gangways=()):
    """Standing steps from y0 back, row by row, a crowd area on each tread; gangways (x of each) as stepped aisles."""
    for i in range(rows):
        ya, yb = y0 + i * tread, y0 + (i + 1) * tread
        zt = z0 + (i + 1) * rise
        K.box("steps", x0, x1, ya, yb if i < rows - 1 else yb + 0.4, -0.6, zt)
        segs = [x0] + [g for gx in gangways for g in (gx - 0.8, gx + 0.8)] + [x1]
        for a, b in zip(segs[0::2], segs[1::2]):
            if b - a > 1.0: area(a + 0.2, b - 0.2, ya + 0.12, yb - 0.12, zt)
        for gx in gangways:                                          # the aisle's half steps, a shade darker
            K.box("concrete", gx - 0.8, gx + 0.8, ya, yb, zt - 0.01, zt + 0.02)
            K.box("concrete", gx - 0.8, gx + 0.8, ya + tread / 2, yb, zt + 0.02, zt + rise / 2)
    # crush barriers every few rows (the white lines across the crowd in his photos)
    for i in range(3, rows, 4):
        yb, zt = y0 + (i + 1) * tread, z0 + (i + 1) * rise
        K.box("trim", x0 + 0.3, x1 - 0.3, yb - 0.08, yb, zt + 0.95, zt + 1.05)
        for x in [x0 + 1.5 + k * 3.0 for k in range(int((x1 - x0 - 3.0) / 3.0) + 1)]:
            K.box("trim", x - 0.05, x + 0.05, yb - 0.08, yb, zt, zt + 1.0)
    return y0 + rows * tread, z0 + rows * rise


def glass_front(x0, x1, y, z0, h, bay=3.0, mat="glass", mull="trim"):
    """Floor-to-ceiling glazing at y (facing -y) with mullions every 'bay' m and a transom."""
    K.box(mat, x0, x1, y - 0.02, y + 0.06, z0, z0 + h)
    n = max(1, round((x1 - x0) / bay))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        K.box(mull, x - 0.06, x + 0.06, y - 0.1, y, z0, z0 + h)
    K.box(mull, x0, x1, y - 0.1, y, z0 + h - 0.12, z0 + h)


def glass_rail(x0, x1, y, z, h=1.1):
    """A glass balustrade: a dark glass panel, a white top rail and posts."""
    K.box("clad_glass", x0, x1, y - 0.03, y + 0.03, z + 0.1, z + h - 0.08)
    K.box("trim", x0, x1, y - 0.07, y + 0.07, z + h - 0.08, z + h)
    for i in range(int((x1 - x0) / 1.6) + 1):
        x = min(x1, x0 + i * 1.6)
        K.box("trim", x - 0.04, x + 0.04, y - 0.05, y + 0.05, z, z + h)


# ------------------------------------------------------------------------------------------ 1: the main (Esher) stand
def peaked_tent(xc, yc, s, z_eave, peak, mast_top):
    """One white tensile canopy: a square base of side s at z_eave sagging slightly between its corners, drawn up to a
    peak on a mast; four cables from the mast head to the corners."""
    bm = K.bm("tent")
    v = lambda x, y, z: bm.verts.new(K.M @ Vector((x, y, z)))
    h = s / 2
    c = [(xc - h, yc - h), (xc + h, yc - h), (xc + h, yc + h), (xc - h, yc + h)]
    pts = []
    for i in range(4):                                   # each side: corner, then a sagging midpoint (a curved cable edge)
        (ax, ay), (bx, by) = c[i], c[(i + 1) % 4]
        pts.append((ax, ay, z_eave))
        pts.append(((ax + bx) / 2 * 0.88 + xc * 0.12, (ay + by) / 2 * 0.88 + yc * 0.12, z_eave + 0.35))
    ring = [v(*q) for q in pts]
    # a concave curve up the cone: one ring at 62% of the way up, pulled well in
    inner = [v(xc + (x - xc) * 0.32, yc + (y - yc) * 0.32, z_eave + peak * 0.62) for x, y, _ in pts]
    top = v(xc, yc, z_eave + peak)
    n = len(ring)
    for i in range(n):
        bm.faces.new((ring[i], ring[(i + 1) % n], inner[(i + 1) % n], inner[i]))
        bm.faces.new((inner[i], inner[(i + 1) % n], top))
    K.cyl("mast", xc, yc, z_eave - 7.0, mast_top, 0.16, segs=8)
    for (ax, ay) in c:                                    # corner posts down to the terrace
        K.cyl("mast", ax, ay, z_eave - 7.0, z_eave, 0.1, segs=6)
    for (ax, ay) in c:                                    # the cables from the mast head
        L = math.dist((ax, ay, z_eave), (xc, yc, mast_top))
        mid_ = ((ax + xc) / 2, (ay + yc) / 2, (z_eave + mast_top) / 2)
        d = Vector((xc - ax, yc - ay, mast_top - z_eave)).normalized()
        q = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        K.boxm("mast", Matrix.Translation(mid_) @ q, 0.05, 0.05, L)


def main_stand():
    width = 168.0
    x0, x1 = -width / 2, width / 2
    rows, tread, rise = 16, 0.8, 0.29
    gang = [x0 + 12 + i * 24 for i in range(int((width - 24) / 24) + 1)]
    yb, zb = terraces(x0 + 0.4, x1 - 0.4, 0.0, 0.0, rows, tread, rise, gang)          # 12.8 m deep, 4.6 m up
    K.box("lawn_wall", x0, x1, -0.6, 0.0, -0.6, 0.45)                                # the low wall at the lawn
    # the concourse floor: tall glazing between square columns
    F1 = zb                                                        # 4.64
    y_front = yb + 0.6
    K.box("concrete", x0, x1, yb, y_front + 1.0, -0.6, F1)
    glass_front(x0 + 0.6, x1 - 0.6, y_front + 1.0, F1, 4.4, bay=3.0)
    for x in [x0 + 0.6 + k * 6.0 for k in range(int((width - 1.2) / 6.0) + 1)]:
        K.box("render", x - 0.35, x + 0.35, y_front + 0.5, y_front + 1.0, F1, F1 + 4.4)
    # balcony level: a slab projecting 2 m with a white rail; the boxes' glazing behind
    F2 = F1 + 4.8
    K.box("render", x0, x1, y_front - 1.2, y_front + 1.8, F2 - 0.45, F2)
    K.balustrade(x0 + 0.5, x1 - 0.5, y_front - 1.05, F2, h=1.05, mat="trim", spacing=0.4, piers=False)
    area(x0 + 1.0, x1 - 1.0, y_front - 0.9, y_front + 1.4, F2)
    glass_front(x0 + 0.6, x1 - 0.6, y_front + 1.8, F2, 3.9, bay=2.4)
    for x in [x0 + 0.6 + k * 6.0 for k in range(int((width - 1.2) / 6.0) + 1)]:   # the box partitions out on the balcony
        K.box("render", x - 0.12, x + 0.12, y_front - 0.6, y_front + 1.8, F2, F2 + 1.2)
    # the upper boxes: a second balcony band, a little shallower
    F3 = F2 + 4.2
    K.box("render", x0, x1, y_front + 0.2, y_front + 2.6, F3 - 0.45, F3)
    K.balustrade(x0 + 0.5, x1 - 0.5, y_front + 0.35, F3, h=1.05, mat="trim", spacing=0.4, piers=False)
    area(x0 + 1.0, x1 - 1.0, y_front + 0.5, y_front + 2.2, F3)
    glass_front(x0 + 0.6, x1 - 0.6, y_front + 2.6, F3, 3.6, bay=2.4)
    for x in [x0 + 0.6 + k * 6.0 for k in range(int((width - 1.2) / 6.0) + 1)]:
        K.box("render", x - 0.12, x + 0.12, y_front + 0.4, y_front + 2.6, F3, F3 + 1.2)
    top = F3 + 3.9                                                  # 17.5
    # the body behind, its rear and the stair at the right-hand end (glass, the height of the boxes)
    D = 44.0
    K.box("render", x0, x1, y_front + 2.6, D, -0.6, top)
    K.box("render", x0, x1, y_front + 1.0, y_front + 2.6, -0.6, F2 - 0.45)
    for z in (F1 + 0.6, F2 + 0.6, F3 + 0.6):                          # windows down the back (the parade ring side)
        for x in [x0 + 4 + k * 4.0 for k in range(int((width - 8) / 4.0) + 1)]:
            K.box("glass", x - 1.4, x + 1.4, D - 0.02, D + 0.05, z, z + 2.2)
    K.box("clad_glass", x1 - 9.0, x1 - 0.6, y_front + 1.0, y_front + 1.4, F1, top)    # the glazed stair at the right end
    for z in [F1 + 1.6 * k for k in range(1, 8)]:
        K.box("trim", x1 - 9.0, x1 - 0.6, y_front + 0.9, y_front + 1.0, z, z + 0.1)
    # the roof: a deep flat slab cantilevered out over the terraces, its fascia thick, its underside ribbed (dark
    # panels between white ribs, as his first photo)
    R0, R1 = top + 0.8, top + 2.4
    y_edge = 2.2                                                    # the roof's front edge, over the terraces' fourth row
    K.box("roof", x0 - 0.5, x1 + 0.5, y_edge, D + 1.0, R0 + 0.35, R1)
    K.box("trim", x0 - 0.5, x1 + 0.5, y_edge - 0.25, y_edge + 0.15, R0, R1 + 0.15)          # the fascia
    K.box("soffit", x0 - 0.4, x1 + 0.4, y_edge + 0.1, y_front + 2.6, R0 + 0.3, R0 + 0.36)
    for x in [x0 + 1.5 + k * 3.0 for k in range(int((width - 3.0) / 3.0) + 1)]:
        K.box("rib", x - 0.22, x + 0.22, y_edge + 0.1, y_front + 2.6, R0, R0 + 0.32)
    K.box("render", x0, x1, y_front + 2.6, D, top, R0 + 0.36)                                 # the roof's upstand
    # the fins on top: tapering plates rising from the front edge to the back (his second photo), one every 9 m
    for x in [x0 + 4.5 + k * 9.0 for k in range(int((width - 9.0) / 9.0) + 1)]:
        K.prism_x("fin", x - 0.18, x + 0.18, [(y_edge + 0.6, R1), (y_edge + 1.4, R1 + 0.6), (D - 6.0, R1 + 4.2), (D - 2.0, R1 + 4.2), (D - 2.0, R1)])
        K.box("iron", x - 0.06, x + 0.06, y_edge + 1.0, D - 2.0, R1 + 0.05, R1 + 0.15)
    K.box("trim", x0 - 0.5, x1 + 0.5, D - 2.2, D - 1.8, R1, R1 + 4.3)                          # the rail along the fins' backs
    # the flank walls at both ends, following the terraces' rake up to the roof (owner's rule)
    for xa, xb in ((x0 - 0.6, x0), (x1, x1 + 0.6)):
        K.prism_x("render", xa, xb, [(-0.6, -0.6), (-0.6, 1.1), (yb, zb + 1.1), (y_front + 1.0, zb + 1.1),
                                      (y_front + 1.0, R1), (D + 1.0, R1), (D + 1.0, -0.6)])
    # the tents at the back (the parade ring side): a terrace on the stand's rear at the first floor with a row of white
    # peaked canopies on masts over it, their peaks just above the roof
    TZ = F2 + 0.4
    K.box("concrete", -76.0, 76.0, D, D + 12.0, TZ - 0.5, TZ)
    K.balustrade(-76.0, 76.0, D + 11.9, TZ, h=1.05, mat="trim", spacing=0.45, piers=False)
    area(-74.0, 74.0, D + 1.0, D + 11.0, TZ)
    K.box("concrete", -76.0, 76.0, D, D + 12.0, -0.6, 0.3)
    for x in [-70.0 + k * 10.0 for k in range(15)]:
        peaked_tent(x, D + 6.0, 9.6, TZ + 7.0, 6.2, TZ + 7.0 + 8.4)
    for x in [-76.0 + k * 7.6 for k in range(21)]:                   # the colonnade under the terrace
        K.box("render", x - 0.3, x + 0.3, D + 11.4, D + 12.0, 0.3, TZ - 0.5)
    glass_front(-76.0, 76.0, D + 0.05, 0.3, TZ - 0.8, bay=4.0)
    return {"width": round(width + 1.2, 1), "depth": round(D + 12.0, 1), "height": round(R1 + 4.3, 1),
            "frontAt": 0.0, "note": "front at y = 0 (the lawn wall); roof edge at y %.1f, %.1f m up" % (y_edge, R1)}


# ------------------------------------------------------------------------------------------ 2: the Eclipse stand
def eclipse_stand():
    core = 48.0                                                     # the balconied middle
    bay = 8.0                                                       # the glazed end bays
    side = 16.0                                                     # the blank clad block on the left
    xb0, xb1 = -core / 2, core / 2
    xl0 = xb0 - bay - side
    width = core + 2 * bay + side
    D = 22.0
    # the brick plinth and the lawn steps up to it
    rows, tread, rise = 6, 0.9, 0.32
    yb, zb = terraces(xb0 - bay, xb1 + bay, 0.0, 0.0, rows, tread, rise, gangways=(0.0,))
    K.box("brick", xl0, xb1 + bay, yb, yb + 1.0, -0.6, zb + 1.2)
    K.box("trim", xl0, xb1 + bay, yb - 0.1, yb + 1.0, zb + 1.2, zb + 1.35)
    P = zb + 1.35                                                   # the first balcony floor
    y0 = yb + 1.0
    floors = [P + 3.6 * i for i in range(4)]
    for z in floors:
        K.box("clad", xb0, xb1, y0 - 2.0, y0 + 0.4, z - 0.4, z)                 # the balcony slab
        glass_rail(xb0 + 0.3, xb1 - 0.3, y0 - 1.9, z)
        area(xb0 + 0.6, xb1 - 0.6, y0 - 1.6, y0 + 0.1, z)
        glass_front(xb0, xb1, y0 + 0.5, z, 3.2, bay=3.0)
    top = floors[-1] + 3.6
    K.box("clad", xb0, xb1, y0 + 0.5, D, -0.6, top)
    # the set-back top floor under a glass sawtooth canopy, the clock on the parapet in the middle
    K.box("clad", xb0, xb1, y0 - 0.6, y0 + 0.5, top - 0.4, top)
    glass_front(xb0 + 0.5, xb1 - 0.5, y0 + 3.0, top, 2.8, bay=3.0)
    K.box("clad", xb0, xb1, y0 + 3.0, D, top, top + 3.0)
    for k in range(10):                                             # the sawtooth: glass ridges running front to back
        xa = xb0 + 1.0 + k * (core - 2.0) / 10; xc_ = xa + (core - 2.0) / 20; xe = xa + (core - 2.0) / 10
        K.prism_y("clad_glass", y0 - 0.2, y0 + 3.2, [(xa, top + 2.9), (xc_, top + 3.9), (xe, top + 2.9)])
        K.box("trim", xc_ - 0.05, xc_ + 0.05, y0 - 0.2, y0 + 3.2, top + 3.85, top + 3.95)
    K.box("clad", -4.0, 4.0, y0 + 3.2, y0 + 5.0, top + 3.0, top + 8.0)          # the clock's panel above the canopy
    K.disc_y("clock", 0.0, y0 + 3.1, y0 + 3.2, top + 5.6, 1.8, segs=32)
    K.box("clock_hand", -0.08, 0.08, y0 + 3.0, y0 + 3.1, top + 5.6, top + 6.9)
    K.box("clock_hand", -0.08, 1.0, y0 + 3.0, y0 + 3.1, top + 5.5, top + 5.7)
    K.box("clad_dark", xb0 + 2.0, xb1 - 2.0, D - 8.0, D - 1.0, top + 3.0, top + 5.0)   # plant on the roof
    H = top + 3.0
    # the glazed end bays, the full height of the block, a little proud of the balconies
    for xa, xc in ((xb0 - bay, xb0), (xb1, xb1 + bay)):
        K.box("clad", xa, xc, y0 - 2.2, D, -0.6, H + 0.6)
        glass_front(xa + 0.6, xc - 0.6, y0 - 2.2, P - 1.0, H - P + 1.2, bay=1.2, mat="clad_glass")
    # the blank clad block on the left (towards the main stand), taller, a few small windows and a doorway at its foot
    K.box("clad_dark", xl0, xb0 - bay, y0 - 1.25, D + 4.0, -0.6, H + 2.0)
    for z in (P + 2.0, P + 9.0, P + 16.0):
        for x in (xl0 + 4.0, xl0 + 8.0, xl0 + 12.0):
            K.box("glass", x - 0.5, x + 0.5, y0 - 1.3, y0 - 1.2, z, z + 0.7)
    K.door(xl0 + side / 2, y0 - 1.25, 0.2, w=2.4, h=2.6)
    # flank walls at the steps' ends (owner's rule)
    for xa, xb_ in ((xb0 - bay - 0.5, xb0 - bay), (xb1 + bay, xb1 + bay + 0.5)):
        K.prism_x("brick", xa, xb_, [(-0.6, -0.6), (-0.6, 0.9), (yb, zb + 0.9), (yb + 1.0, zb + 0.9), (yb + 1.0, -0.6)])
    return {"width": round(width + 1.0, 1), "depth": round(D + 4.0, 1), "height": round(H + 2.0, 1), "frontAt": 0.0,
            "offset": round((xl0 + xb1 + bay) / 2, 2), "note": "the clad block on the left; 'offset' is the middle of the whole"}


# ------------------------------------------------------------------------------------------ build and export
PIECES = [("sandown_main_stand", main_stand), ("sandown_eclipse_stand", eclipse_stand)]
LIB = bpy.data.collections.new("sandown_stands_kit")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-22s %6d triangles, %d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "Sandown Park's stands, modelled from the owner's photos (tools/blender/build_sandown_stands.py). Building "
                     "axes: x along the front (left to right from the track), y into the building (front faces -y), z up; "
                     "origin the middle of the front on the ground. crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "sandown_stands_kit.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "sandown_stands_kit.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported sandown_stands_kit.glb", flush=True)

if os.environ.get("SHEET"):
    def dup(name, x, y, rz=0.0):
        o = OBJ[name].copy(); o.data = OBJ[name].data; LIB.objects.link(o)
        o.location = (x, y, 0); o.rotation_euler = (0, 0, math.radians(rz)); o.hide_render = False; return o
    for o in list(LIB.objects): o.hide_render = True
    dup("sandown_main_stand", 0, 0)
    ei = INFO["sandown_eclipse_stand"]
    dup("sandown_eclipse_stand", 84.6 + 2.0 + ei["width"] / 2 - ei["offset"], 6.0)
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.84, 0.9, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.02))
    bpy.context.object.data.materials.append(material("lawn", "#a8c47a"))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(40, -30, 0.0)); tr = bpy.context.object
    tr.scale = (420, 26, 1); tr.data.materials.append(material("turf", "#8fbb63"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 3.6; sun.data.angle = math.radians(6); sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = int(os.environ.get("RX", "1800")), int(os.environ.get("RY", "820"))
    scene.view_settings.view_transform = "AgX"
    os.makedirs(rp("reference/sandown/renders"), exist_ok=True)
    shots = [("stands-concept-1", (20, -170, 34), (40, 20, 10), 32),           # both stands from the infield
             ("stands-concept-2", (-40, -60, 8), (-10, 10, 12), 24),            # the main stand from the lawn, as his first photo
             ("stands-concept-3", (40, -75, 6), (95, 10, 13), 28),              # the main stand's end and the Eclipse (his second)
             ("stands-concept-4", (-30, 120, 22), (0, 40, 14), 30)]             # the tents at the back, from the parade ring side
    for nm, frm, to, lens in shots:
        cam = bpy.data.objects.new(nm, bpy.data.cameras.new(nm)); cam.data.lens = lens; scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = rp("reference/sandown/renders/%s.png" % nm)
        bpy.ops.render.render(write_still=True)
        print("rendered", nm, flush=True)
