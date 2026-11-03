"""Build the finish-line assembly that stands opposite the grandstand.

    python -c "exec(open('tools/blender/build_finish_line.py').read())"

Follows reference/architecture/finish-line-sheet.png (front elevation as the master), at real sizes:
about 30 m of running rail at 1.05 m, box hedges about 1.1 m high with boards standing in them,
the race-time board, the winning post with its red loop on top and a diamond plate, two planters
at its foot, and a bracket clock on a lamp post at the far end.

Writes assets/models/architecture/finish_line.glb and assets/models/master/finish_line.blend.

Origin: the foot of the winning post, on the line of the running rail. The red loop stands upright
across the course, edge-on to the stands, so it lines up with the winning line. Blender: front
(towards the track) faces -y, hedges and boards behind at +y. glTF: front faces +z.
On the far side of the course the assembly needs no turn: its front already faces the stands.
"""
import json, math, os
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
OUT_DIR = os.path.join(REPO, "assets/models/architecture")
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())

TIME = "1:01.47"                    # shown on the race-time board
COL = {"trim": "#f6f1e4", "board": "#f8f4ea", "dark": "#23272c", "digit": "#f3e3b2", "red": "#c42a24",
       "hedge": "#4b7038", "hedge_light": "#628a45", "timber": "#ebe3d1", "leaf": "#5c8048",
       "flower": "#f7f1e6", "flower_pink": "#e2a3b4", "clock_face": "#fbf8ef", "metal": "#d9d6cf"}
MATS = {k: material("fl_" + k, v, rough={"red": 0.45, "digit": 0.5}.get(k, 0.8)) for k, v in COL.items()}
for key, strength in (("digit", 1.6), ("red", 0.0)):
    b = MATS[key].node_tree.nodes["Principled BSDF"]
    if strength:
        b.inputs["Emission Color"].default_value = srgb(COL[key])
        b.inputs["Emission Strength"].default_value = strength

K = Kit()
RAIL_H, HEDGE = 1.05, (1.0, 1.9, 1.1)          # hedge: y from, y to, height


def rod(mat, p0, p1, r, segs=8):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    g = bmesh.ops.create_cone(K.bm(mat), cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length, matrix=K.M @ m)
    K._smooth(g["verts"])


# ---------------------------------------------------------------- running rail (split at the post)
for x0, x1 in ((-15.2, -0.2), (0.2, 14.8)):
    rod("trim", (x0, 0, RAIL_H), (x1, 0, RAIL_H), 0.065, 10)
    n = max(1, round((x1 - x0) / 3.0))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        if abs(x) < 0.3:
            continue
        K.cyl("trim", x, 0, 0, RAIL_H, 0.05, 0.05, 8)
        K.cyl("trim", x, 0, RAIL_H - 0.1, RAIL_H + 0.02, 0.075, 0.075, 8)       # knuckle
for x in (-15.2, 14.8):
    K.sphere("trim", x, 0, RAIL_H, 0.085, 1)


# ---------------------------------------------------------------- box hedges
import random
R = random.Random(7)
HEDGES = [(-13.7, -8.3), (-7.9, -2.6), (-2.3, 2.3), (2.5, 9.4), (9.7, 13.0)]
y0, y1, H = HEDGE
for hx0, hx1 in HEDGES:
    K.box("hedge", hx0 + 0.08, hx1 - 0.08, y0 + 0.08, y1 - 0.08, 0, H - 0.12)
    # leafy lumps over the top and the faces, so it reads as clipped box rather than a block
    L = hx1 - hx0
    for i in range(int(L / 0.32) + 1):
        x = hx0 + 0.16 + i * (L - 0.32) / max(1, int(L / 0.32))
        for y in (y0 + 0.25, (y0 + y1) / 2, y1 - 0.25):
            K.sphere(R.choice(("hedge", "hedge_light")), x + R.uniform(-0.06, 0.06), y, H - 0.14 + R.uniform(-0.03, 0.03),
                     R.uniform(0.2, 0.26), 1, 0.7)
        for z in (0.3, 0.7):
            K.sphere(R.choice(("hedge", "hedge", "hedge_light")), x + R.uniform(-0.06, 0.06), y0 + 0.16, z + R.uniform(-0.05, 0.05),
                     R.uniform(0.2, 0.25), 1, 1.0)


# ---------------------------------------------------------------- boards standing in the hedges
def board(x0, x1, z0, z1, y=1.45, legs=True):
    K.box("board", x0, x1, y - 0.05, y + 0.05, z0, z1)
    for a, b, c, d in ((x0 - 0.07, x1 + 0.07, z1, z1 + 0.08), (x0 - 0.07, x1 + 0.07, z0 - 0.08, z0),
                       (x0 - 0.07, x0, z0, z1), (x1, x1 + 0.07, z0, z1)):
        K.box("trim", a, b, y - 0.08, y + 0.08, c, d)
    n = max(2, round((x1 - x0) / 1.6))
    for i in range(1, n):                                   # frame ribs on the back
        x = x0 + (x1 - x0) * i / n
        K.box("trim", x - 0.04, x + 0.04, y + 0.05, y + 0.12, z0, z1)
    if legs:
        for x in (x0 + 0.3, x1 - 0.3):
            K.box("trim", x - 0.06, x + 0.06, y - 0.06, y + 0.06, 0, z0)


SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
       "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def digits(text, x0, zc, h=0.62, y=1.38):
    """Seven-segment figures on the dark panel, lit."""
    w, t = h * 0.52, h * 0.11
    x = x0
    for ch in text:
        if ch in ":.":
            for dz in ((-0.18, 0.18) if ch == ":" else (-0.5,)):
                K.box("digit", x + 0.02, x + 0.02 + t, y - 0.02, y, zc + dz * h - t / 2, zc + dz * h + t / 2)
            x += t + 0.12
            continue
        segs = {"a": (x + t, x + w - t, zc + h / 2 - t, zc + h / 2), "d": (x + t, x + w - t, zc - h / 2, zc - h / 2 + t),
                "g": (x + t, x + w - t, zc - t / 2, zc + t / 2), "f": (x, x + t, zc + t / 2, zc + h / 2 - t),
                "e": (x, x + t, zc - h / 2 + t, zc - t / 2), "b": (x + w - t, x + w, zc + t / 2, zc + h / 2 - t),
                "c": (x + w - t, x + w, zc - h / 2 + t, zc - t / 2)}
        for s in SEG[ch]:
            a, b, c, d = segs[s]
            K.box("digit", a + 0.008, b - 0.008, y - 0.02, y, c + 0.008, d - 0.008)
        x += w + 0.13


# race-time board: a header band over a dark panel with the time
board(-13.4, -8.6, 1.0, 2.8)
K.box("dark", -13.2, -8.8, 1.36, 1.41, 1.15, 2.2)
K.box("trim", -13.25, -8.75, 1.34, 1.42, 2.2, 2.26)
digits(TIME, -12.85, 1.67, 0.7)
board(-7.6, -2.9, 1.05, 2.55)
board(-2.0, -0.25, 1.0, 2.15, legs=False)
board(0.25, 2.0, 1.0, 2.15, legs=False)
board(2.8, 9.1, 1.05, 2.55)

# ---------------------------------------------------------------- planters at the foot of the post
for px0, px1 in ((-2.05, -0.35), (0.35, 2.05)):
    yc = 0.58
    K.box("timber", px0, px1, yc - 0.25, yc + 0.25, 0, 0.38)
    K.box("trim", px0 - 0.04, px1 + 0.04, yc - 0.29, yc + 0.29, 0.33, 0.38)
    for i in range(int((px1 - px0) / 0.11)):
        x = px0 + 0.08 + i * 0.11
        for y in (yc - 0.12, yc + 0.08):
            K.sphere("leaf", x + R.uniform(-0.03, 0.03), y, 0.42, 0.08, 1)
            K.sphere(R.choice(("flower", "flower", "flower_pink")), x + R.uniform(-0.04, 0.04), y + R.uniform(-0.04, 0.04), 0.5, 0.055, 1)

# ---------------------------------------------------------------- the winning post
K.box("trim", -0.25, 0.25, -0.25, 0.25, 0, 0.18)
K.cyl("trim", 0, 0, 0.18, 3.3, 0.11, 0.09, 12)
for z in (0.45, 1.6, 3.2):
    K.cyl("trim", 0, 0, z, z + 0.08, 0.14, 0.14, 12)
K.sphere("trim", 0, 0, 3.42, 0.15, 2)
K.cyl("red", 0, 0, 3.52, 3.98, 0.03, 0.03, 8)
# the red loop: upright, across the course (its plane holds the winning line), edge-on to the stands
K.push(Matrix.Translation((0, 0, 4.3)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
K.ring_y("red", 0, 0, 0, 0.32, 0.05, 20, 6)
K.pop()
# diamond plate on the post, facing the stands
zc = 2.35
K.prism_y("trim", -0.2, -0.13, [(-0.95, zc), (0, zc + 0.56), (0.95, zc), (0, zc - 0.56)])
K.prism_y("board", -0.24, -0.2, [(-0.85, zc), (0, zc + 0.48), (0.85, zc), (0, zc - 0.48)])

# ---------------------------------------------------------------- bracket clock on a lamp post
px, py = 10.4, 0.75
K.box("trim", px - 0.2, px + 0.2, py - 0.2, py + 0.2, 0, 0.25)
K.cyl("trim", px, py, 0.25, 3.35, 0.09, 0.07, 10)
for z in (0.55, 2.9):
    K.cyl("trim", px, py, z, z + 0.08, 0.12, 0.12, 10)
K.sphere("trim", px, py, 3.45, 0.11, 1)
K.cyl("trim", px, py, 3.52, 3.7, 0.025, 0.01, 6)
arm_z, arm_x = 3.05, px + 1.35
K.box("trim", px, arm_x, py - 0.04, py + 0.04, arm_z - 0.05, arm_z + 0.05)
K.push(Matrix.Translation((0, py, 0)))
for cx, cz, r in ((px + 0.35, arm_z - 0.3, 0.25), (px + 0.85, arm_z - 0.22, 0.17), (px + 0.55, arm_z + 0.2, 0.15)):
    K.ring_y("trim", cx, 0, cz, r, 0.025, 12, 4)                                        # scrollwork
K.arc_band("trim", px, arm_z - 0.75, 0.68, 0.74, 0, math.pi / 2, -0.03, 0.03, 8)
K.pop()
cz = 2.45
K.box("trim", arm_x - 0.25 - 0.03, arm_x - 0.25 + 0.03, py - 0.03, py + 0.03, cz + 0.42, arm_z)   # hanger
K.disc_y("trim", arm_x - 0.25, py - 0.13, py + 0.13, cz, 0.44, 24)
for side in (-1, 1):
    f = py + side * 0.13
    K.disc_y("clock_face", arm_x - 0.25, f - 0.015 if side < 0 else f, f if side < 0 else f + 0.015, cz, 0.37, 24)
    for h in range(12):
        a = h * math.pi / 6
        K.boxm("dark", Matrix.Translation((arm_x - 0.25 + math.sin(a) * 0.3, f + side * 0.02, cz + math.cos(a) * 0.3)) @ Matrix.Rotation(-a, 4, "Y"),
               0.025, 0.01, 0.07 if h % 3 else 0.1)
    for ang, ln in ((math.radians(-60), 0.17), (math.radians(60), 0.27)):
        K.boxm("dark", Matrix.Translation((arm_x - 0.25, f + side * 0.025, cz)) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Translation((0, 0, ln / 2 - 0.03)), 0.03, 0.01, ln)
K.sphere("trim", arm_x - 0.25, py, cz + 0.5, 0.06, 1)

# ---------------------------------------------------------------- save
col = bpy.data.collections.new("finish_line")
bpy.context.scene.collection.children.link(col)
ob, tris = kit_to_object(K, "finish_line", MATS, col)
print("finish line: %d triangles, %.1f m long" % (tris, ob.dimensions.x), flush=True)
os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, "finish_line.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets/models/master/finish_line.blend"), compress=True)
