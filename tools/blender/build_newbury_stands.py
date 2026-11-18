"""Newbury's four stands, modelled for the course from the owner's old photos (no kit pieces bolted together).

    python3.11 -c "exec(open('tools/blender/build_newbury_stands.py').read())"
    SHEET=1 python3.11 -c "exec(...)"        # also render them: reference/newbury/renders/stands-sheet.jpg

Owner, 18 Nov 2026, 23:06, after an evening of kit pieces mixed together ("Hmm It's a mess"): asked what was wrong,
"too many mismatched pieces, the layout/plan itself, model it properly instead". His old photos of Newbury's stands
(22:37 and 22:52): left to right a modern glass stand; the main grandstand, a long low covered stand over an open
standing terrace with a white rendered box on its roof (a gable with a clock, a flagpole, railings), a brick block at
one end and a pitched-roof block at the other; and the old two-tier stand with a hipped slate roof, open galleries on
columns, a brick end, and a lookout on posts on its ridge. His plan (22:39-22:51): four stands in four boxes, the
second bent in plan towards the bend. He agreed (23:08) this reading:

  newbury_glass_stand   1  the modern glass stand at the bend: a standing terrace, a balcony, two glazed storeys,
                           a flat roof                                                                     44 m
  newbury_kinked_stand  2  the brick block with its hipped roof, a covered stand running from it up the course and
                           another turned 35 degrees towards the bend (his kink)                      50 + 14 + 26 m
  newbury_main_stand    3  the long covered stand: the open terrace under a low canopy on iron columns, an upper
                           stand under a flat roof, the white roof box (gable, clock, flagpole) in the middle, the
                           pitched-roof block at its right-hand end                                         89 m
  newbury_old_stand     4  the old stand: two open galleries over a veranda under a hipped slate roof, a brick end
                           block on the left, the lookout on posts on the ridge near the right-hand end     85 m

One palette for all four (the Rowley Mile's, with the July Course's colours York added): cream render, white paint,
brick, slate, iron. His standing rule (17 Nov): the ends are flank walls on the rake of the terrace, not towers.

Writes assets/models/architecture/newbury_kit.glb and .json (as the other kits: building axes x along the front,
y into the building, front facing -y, z up; origin the middle of the front on the ground; crowd [x0, x1, y0, y1,
floor], or with three more values [.., angle, px, py] for a stretch turned 'angle' degrees about (px, py), the kink).
The course's own pick of them is made by tools/course/real/merge_stands.py newbury (newbury_stands.glb).
"""
import json, math, os

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

# ---- the Rowley Mile build's definitions (kit, palette, Ascot's pieces), without its build loop
_src = open(rp("tools/blender/build_rowley_stands.py")).read()
exec(_src[:_src.index("\nPIECES = [")])
# ---- the July Course's old pavilion and brick block, as written there (the old pavilion under a hipped roof here)
_jsrc = open(rp("tools/blender/build_july_stands.py")).read()
def _july(name):
    a = _jsrc.index("def %s(" % name)
    b = _jsrc.index("\n# ----", a) if "\n# ----" in _jsrc[a:] else len(_jsrc)
    return _jsrc[a:b]
exec(_july("brick_block").split("\n\n\n")[0])
exec(_july("old_pavilion").replace('    rz = gable_x(-half, half, -0.95, D, E, 30, 0.7, roof="slate", wall="paint")',
                                   '    K.hip_roof(-half, half, -0.95, D, E, 3.4, ov=0.7, mat="slate"); rz = E + 3.4'))

EXTRA = {"paint": "#f4e6d0", "deck": "#dcc4a2", "stone": "#f2e4cc", "screen": "#2f3340", "clock_face": "#fbf5ea",
         "clock_dark": "#2a2c30", "flagcloth": "#c9584a", "shade": "#6d7480"}
for k, v in EXTRA.items():
    if k not in MATS:
        COL[k] = v
        MATS[k] = material("nb_" + k, v, rough=0.9)


def turned(fn, angle, px, py):
    """Draw fn() turned 'angle' degrees about (px, py); its crowd areas keep their own axes and carry the turn."""
    n0 = len(CROWD)
    K.push(Matrix.Translation((px, py, 0.0)) @ Matrix.Rotation(math.radians(angle), 4, "Z"))
    fn()
    K.pop()
    for c in CROWD[n0:]:
        c += [angle, px, py]


def terrace(x0, x1, rows, tread=0.9, rise=0.3, z0=0.3):
    """The open standing terrace from the lawn, its rows' crowd."""
    return steps("steps", x0, x1, 0.0, z0, rows, tread, rise)


def flank(x, side, prof):
    """An end wall on the terrace's rake (his rule), then the building's own end above it."""
    xa, xb = (x - 0.35, x) if side < 0 else (x, x + 0.35)
    K.prism_x("paint", xa, xb, prof)


def iron_columns(x0, x1, y, z0, z1, every=6.0):
    n = max(1, round((x1 - x0) / every))
    for k in range(n + 1):
        x = x0 + 0.3 + (x1 - x0 - 0.6) * k / n
        K.cyl("iron", x, y, z0, z1, 0.11, segs=8)
        K.box("iron", x - 0.35, x + 0.35, y - 0.06, y + 0.06, z1 - 0.5, z1 - 0.35)     # a cross bracket under the beam


def clock(x, y, z, R):
    K.disc_y("trim", x, y + 0.02, y + 0.2, z, R + 0.15, segs=32)
    K.disc_y("clock_dark", x, y - 0.04, y + 0.02, z, R, segs=32)
    K.disc_y("clock_face", x, y - 0.1, y - 0.03, z, R - 0.15, segs=32)
    for h in range(12):
        a = h * math.pi / 6
        K.boxm("clock_dark", Matrix.Translation((x + math.sin(a) * (R - 0.4), y - 0.12, z + math.cos(a) * (R - 0.4))) @ Matrix.Rotation(-a, 4, "Y"),
               0.08 if h % 3 else 0.13, 0.03, 0.3 if h % 3 else 0.42)


def flagpole(x, y, z, h=7.0):
    K.cyl("trim", x, y, z, z + h, 0.09, 0.05, segs=6)
    K.sphere("gilt", x, y, z + h + 0.1, 0.16, sub=1)
    K.box("flagcloth", x + 0.1, x + 2.9, y - 0.03, y + 0.03, z + h - 1.9, z + h - 0.2)


# ------------------------------------------------------------------------------------------ 1: the glass stand
def glass_stand(L=44.0):
    h = L / 2
    yt, zt = terrace(-h, h, 7, 0.9, 0.35)
    yb, zb, Z1, Z2, Z3 = yt + 1.4, 3.8, 7.6, 11.4, 11.9
    D = 18.0
    K.box("podium", -h, h, yt, D, -1.0, zb - 0.3)                           # the ground storey: doors under the balcony
    for k in range(int(L // 6.0)):
        K.door(-h + 3.0 + k * 6.0, yt, zt + 0.3, 1.6, 2.4)
    K.box("trim", -h - 0.2, h + 0.2, yt - 1.2, yb, zb - 0.3, zb)             # the balcony slab and its glass rail
    K.box("glass", -h, h, yt - 1.15, yt - 1.05, zb, zb + 1.1)
    K.box("trim", -h, h, yt - 1.2, yt - 1.0, zb + 1.1, zb + 1.2)
    area(-h + 0.4, h - 0.4, yt - 0.9, yb - 0.2, zb)
    for za, zc in ((zb, Z1), (Z1, Z2)):                                       # two glazed storeys, white floor bands
        K.box("wall", -h, h, yb + 0.15, D, za, zc)
        K.screen(-h + 0.1, h - 0.1, yb, za, zc - za - 0.35, pane=1.8)
        K.box("trim", -h - 0.1, h + 0.1, yb - 0.2, yb + 0.1, zc - 0.35, zc)
    K.box("trim", -h - 0.6, h + 0.6, yb - 2.2, D + 0.3, Z2, Z3)              # the flat roof, its deep front edge
    K.box("podium", -h - 0.6, h + 0.6, yb - 2.25, yb - 2.0, Z2 - 0.5, Z3)
    for x in (-h, h):                                                         # flank walls: the rake, then the block's end
        flank(x, -1 if x < 0 else 1, [(-0.2, -1.0), (-0.2, 1.1), (yt, zt + 1.3), (yt, Z2), (D, Z2), (D, -1.0)])
    return {"width": L + 1.2, "depth": D + 0.3, "height": Z3}


# ------------------------------------------------------------------------------------------ 2: the kinked stand
RUN = {"rows": 9, "tread": 0.9, "rise": 0.3, "back": 5.0, "eaves": 7.2, "top": 9.6, "block": 8.8}


def covered_run(x0, x1, ends=(True, True)):
    """The covered stand (his photo): the open terrace under a low slate canopy on iron columns along its front, the
    canopy rising to a rendered block behind with doors onto the terrace top; ends flank walls on the rake."""
    r = RUN
    yt, zt = terrace(x0, x1, r["rows"], r["tread"], r["rise"])
    yb = yt + r["back"]
    K.box("cream", x0, x1, yt, yb, -1.0, r["block"])                          # the block behind
    for k in range(int((x1 - x0 - 2.0) // 4.5) + 1):
        x = x0 + 2.0 + k * 4.5
        if x < x1 - 1.0:
            K.door(x, yt, zt + 0.3, 1.5, 2.4)
            win(x, yt, zt + 3.4, 1.2, 1.4)
    e, t = r["eaves"], r["top"]
    K.prism_x("slate", x0 - 0.3, x1 + 0.3, [(-0.9, e), (-0.9, e + 0.25), (yb + 0.4, t + 0.25), (yb + 0.4, t)])
    K.box("trim", x0 - 0.3, x1 + 0.3, -1.0, -0.8, e - 0.6, e + 0.25)          # the valance along the canopy's edge
    K.box("shade", x0, x1, -0.6, yb, e + 0.02, e + 0.06)
    iron_columns(x0, x1, -0.4, 0.3, e, 5.6)
    for x, side, on in ((x0, -1, ends[0]), (x1, 1, ends[1])):
        if on:
            flank(x, side, [(-0.6, -1.0), (-0.6, 1.2), (yt, zt + 1.3), (yt, r["block"]), (yb, r["block"]), (yb, -1.0)])
    return yb


def hipped_block(x0, x1, y0, y1, top, rise=3.6):
    brick_block(x0, x1, y0, y1, top, outer=None)
    K.hip_roof(x0, x1, y0, y1, top + 0.35, rise, ov=0.5, mat="slate")
    for x in (x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.7):                     # chimneys
        K.box("brick", x - 0.5, x + 0.5, (y0 + y1) / 2 - 0.5, (y0 + y1) / 2 + 0.5, top + rise - 1.0, top + rise + 1.4)
    return top + rise + 1.4


def kinked_stand(right=50.0, block=14.0, left=26.0, kink=35.0):
    """His second stand, bent in plan: the brick block (hipped roof, chimneys) at the bend; the covered stand from its
    right side up the course; the same stand from its left side turned 'kink' degrees towards the course about the
    block's front left corner. Origin: the middle of the block's front, on the ground."""
    hb = block / 2
    yb = covered_run(hb, hb + right, ends=(False, True))
    turned(lambda: covered_run(-left, 0.0, ends=(True, False)), kink, -hb, 0.0)
    top = hipped_block(-hb, hb, -0.6, yb + 1.0, 12.4)
    for x in (-hb + 2.5, hb - 2.5):                                           # the block's ground floor doors
        K.door(x, -0.6, 0.0, 1.5, 2.5)
    k = math.radians(kink)
    lx, ly = -hb - left * math.cos(k), -left * math.sin(k)
    bx, by = -hb - left * math.cos(k) - yb * math.sin(k), -left * math.sin(k) + yb * math.cos(k)
    outline = [[lx, ly], [-hb, -0.6], [hb + right, -0.6], [hb + right, yb], [-hb, yb + 1.0], [-hb - yb * math.sin(k), yb * math.cos(k)], [bx, by]]
    return {"width": round(block + right + left * math.cos(k), 2), "depth": round(yb + 1.0, 2), "height": round(top, 2),
            "offset": round((hb + right + lx) / 2, 2),
            "outline": [[round(a, 2), round(b, 2)] for a, b in outline],
            "kink": {"angle": kink, "left": left, "right": right, "block": block,
                     "note": "origin = the middle of the brick block's front; the right run along +x, the left run turned "
                             "'angle' degrees about the block's front left corner (its far end towards the course)"}}


# ------------------------------------------------------------------------------------------ 3: the main stand
def main_stand(L=89.0, endblock=18.0):
    """The long covered stand (his photos): the open terrace under a low canopy on iron columns; behind and above it
    an upper stand of seats under a flat roof people stand on; the white roof box in the middle (a front gable with
    the clock, a flagpole); the pitched-roof block at the right-hand end. Origin: the middle of the front."""
    h = L / 2
    x1 = h - endblock
    yt, zt = terrace(-h, h, 9, 0.9, 0.3)
    # the lower canopy, from the iron columns up to the upper stand's front
    e = 6.3
    K.prism_x("slate", -h - 0.3, x1, [(-0.9, e), (-0.9, e + 0.25), (yt + 0.2, e + 1.25), (yt + 0.2, e + 1.0)])
    K.box("trim", -h - 0.3, x1, -1.0, -0.8, e - 0.55, e + 0.25)
    K.box("shade", -h, x1, -0.6, yt, e + 0.02, e + 0.06)
    iron_columns(-h, x1, -0.4, 0.3, e, 5.8)
    # the upper stand: a balustraded front, six rows of seats, the back wall, a flat roof on slim columns
    zf, yu = e + 1.25, yt + 0.2
    K.box("cream", -h, x1, yt, yt + 7.4, -1.0, zf)                            # the block under it, doors onto the terrace top
    for k in range(int((x1 + h - 2.0) // 4.5) + 1):
        x = -h + 2.0 + k * 4.5
        if x < x1 - 1.0:
            K.door(x, yt, zt + 0.3, 1.5, 2.4)
    K.balustrade(-h, x1, yu + 0.1, zf, h=1.0, mat="trim", spacing=0.3)
    yr, zr = steps("steps", -h, x1, yu + 0.5, zf, 6, 0.95, 0.42)
    yback = yr + 0.6
    zroof = zr + 3.4
    K.box("cream", -h, x1, yr, yback, zf, zroof)
    K.box("trim", -h - 0.3, x1, yu - 0.4, yback + 0.3, zroof, zroof + 0.45)  # the flat roof
    K.box("podium", -h - 0.3, x1, yu - 0.45, yu - 0.2, zroof - 0.4, zroof + 0.45)
    iron_columns(-h, x1, yu + 0.2, zf, zroof, 7.2)
    K.balustrade(-h, x1, yu - 0.1, zroof + 0.45, h=1.0, mat="iron", spacing=0.3)
    area(-h + 0.5, -10.0, yu + 0.3, yu + 3.0, zroof + 0.45)                    # people on the roof, either side of the box
    area(10.0, x1 - 1.0, yu + 0.3, yu + 3.0, zroof + 0.45)
    # the roof box: white render, two rows of windows, a front gable with the clock, a flagpole on the ridge
    bx, by0, by1, bz = 8.5, yu + 3.2, yback, zroof + 0.45
    K.box("paint", -bx, bx, by0, by1, bz, bz + 5.2)
    K.box("trim", -bx - 0.3, bx + 0.3, by0 - 0.3, by1 + 0.3, bz + 5.2, bz + 5.55)
    for x in (-6.0, -3.6, 3.6, 6.0):
        win(x, by0, bz + 0.9, 1.1, 1.5)
        win(x, by0, bz + 3.2, 1.1, 1.3)
    K.door(0.0, by0, bz, 1.6, 2.4)
    rz = gable_y(-3.2, 3.2, by0 - 0.4, by1, bz + 5.2, 38, 0.4, roof="slate", wall="paint")
    clock(0.0, by0 - 0.5, bz + 5.2 + (rz - bz - 5.2) * 0.42, 1.2)
    K.balustrade(-bx - 1.5, bx + 1.5, by0 - 1.2, bz, h=1.0, mat="iron", spacing=0.3)
    flagpole(0.0, (by0 + by1) / 2 + 1.0, rz + 0.2)
    # the pitched-roof block at the right-hand end: cream render, three storeys of windows, gable ends
    K.box("cream", x1, h, yt - 0.4, yback + 1.0, -1.0, zroof)
    for z in (zt + 0.6, zt + 4.2, zt + 7.8):
        for x in (x1 + 3.0, x1 + 6.5, h - 6.5, h - 3.0):
            win(x, yt - 0.4, z, 1.2, 1.8)
    K.door((x1 + h) / 2, yt - 0.4, zt + 0.3, 1.8, 2.7)
    grz = gable_x(x1, h, yt - 0.4, yback + 1.0, zroof, 34, 0.6, roof="slate", wall="cream")
    # the left end: a flank wall on the rake, then the stand's end wall
    flank(-h, -1, [(-0.6, -1.0), (-0.6, 1.2), (yt, zt + 1.3), (yt, zf + 1.0), (yr, zroof), (yback, zroof), (yback, -1.0)])
    flank(h, 1, [(-0.6, -1.0), (-0.6, 1.2), (yt - 0.4, zt + 1.3), (yt - 0.4, -1.0)])
    return {"width": L + 0.7, "depth": round(yback + 1.6, 2), "height": round(max(rz + 7.3, grz + 0.5), 2)}


# ------------------------------------------------------------------------------------------ 4: the old stand
def old_stand(L=76.0, endblock=9.0):
    """The old stand (his photos): two open galleries over a veranda under a hipped slate roof (the July Course's old
    pavilion, its roof hipped), a brick end block on the left, the lookout on four posts on the ridge near the right.
    Origin: the middle of the whole front."""
    sh = endblock / 2                                       # the pavilion's middle sits this far right of the whole's
    K.push(Matrix.Translation((sh, 0.0, 0.0)))
    info = old_pavilion(L=L, D=11.0, G=4.2, S=3.9, levels=2, stair=False, fence=False)
    half, D, E = L / 2, 11.0, 4.2 + 2 * 3.9 - 0.25
    ridge = E + 3.4
    # the lookout: four posts up from the ridge, a small boarded hut with windows all round, a balcony rail, a hip roof
    cx, cy, s, zp = half - 9.0, D / 2 - 0.5, 2.4, ridge + 1.6
    for dx in (-s + 0.2, s - 0.2):
        for dy in (-s + 0.2, s - 0.2):
            K.box("trim", cx + dx - 0.12, cx + dx + 0.12, cy + dy - 0.12, cy + dy + 0.12, ridge - 1.2, zp)
    K.box("deck", cx - s - 0.5, cx + s + 0.5, cy - s - 0.5, cy + s + 0.5, zp - 0.2, zp)
    K.balustrade(cx - s - 0.4, cx + s + 0.4, cy - s - 0.4, zp, h=0.9, mat="trim", spacing=0.3)
    K.box("paint", cx - s + 0.4, cx + s - 0.4, cy - s + 0.4, cy + s - 0.4, zp, zp + 2.6)
    for x in (cx - 1.0, cx + 1.0):
        win(x, cy - s + 0.4, zp + 0.9, 0.9, 1.2)
    K.hip_roof(cx - s + 0.4, cx + s - 0.4, cy - s + 0.4, cy + s - 0.4, zp + 2.6, 1.6, ov=0.5, mat="slate")
    K.cyl("iron", cx, cy, zp + 4.2, zp + 6.0, 0.05, segs=4, smooth=False)
    K.pop()
    # the brick end block on the left, the same height as the eaves, under its own hipped roof
    bx1 = -L / 2 + sh - 0.2
    bx0 = bx1 - endblock
    hipped_block(bx0, bx1, 1.0, D + 0.4, E, rise=2.8)
    K.door((bx0 + bx1) / 2, 1.0, 0.0, 1.5, 2.5)
    return {"width": L + endblock, "depth": D + 1.6, "height": round(zp + 6.0, 2)}


PIECES = [
    ("newbury_glass_stand", glass_stand),
    ("newbury_kinked_stand", kinked_stand),
    ("newbury_main_stand", main_stand),
    ("newbury_old_stand", old_stand),
]
LIB = bpy.data.collections.new("newbury_kit")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = [list(c) for c in CROWD]; info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-22s %6d triangles, %3d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "Newbury's four stands (tools/blender/build_newbury_stands.py), modelled from the owner's old photos. "
                     "Building axes: x along the front (left to right from the track), y into the building (front faces "
                     "-y), z up; origin the middle of the front on the ground (the kinked stand: the middle of its brick "
                     "block's front). crowd: [x0, x1, y0, y1, floor], or [.., angle, px, py] for a stretch turned 'angle' "
                     "degrees about (px, py). outline: the footprint when it is not a rectangle.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "newbury_kit.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "newbury_kit.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported newbury_kit.glb", flush=True)

if os.environ.get("SHEET"):
    REN = rp("reference/newbury/renders"); os.makedirs(REN, exist_ok=True)
    x = 0.0
    for name, _ in PIECES:
        w = INFO[name]["width"]
        OBJ[name].location = (x + w / 2 - INFO[name].get("offset", 0.0), 0, 0)
        x += w + 14
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.82, 0.9, 1)
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(x / 2, 40, 0))
    bpy.context.object.data.materials.append(material("lawn", "#a9c48a"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.0; sun.data.angle = math.radians(3); sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "JPEG"; scene.render.image_settings.quality = 90

    def shoot(fname, frm, to, lens, w=2400, hgt=900):
        scene.render.resolution_x, scene.render.resolution_y = w, hgt
        cam = bpy.data.objects.new(fname, bpy.data.cameras.new(fname)); cam.data.lens = lens; cam.data.clip_end = 5000
        scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam; scene.render.filepath = os.path.join(REN, fname + ".jpg")
        bpy.ops.render.render(write_still=True)
        print("rendered", fname, flush=True)
    mid = (x - 14) / 2
    shoot("stands-sheet", (mid, -(x - 14) * 0.62, 40), (mid, 10, 6), 30)
    xs = 0.0
    for name, _ in PIECES:
        w = INFO[name]["width"]
        c = xs + w / 2
        shoot("stand-" + name.replace("newbury_", ""), (c + w * 0.55, -w * 0.9, w * 0.32), (c, 6, 7), 32, 1600, 900)
        xs += w + 14
