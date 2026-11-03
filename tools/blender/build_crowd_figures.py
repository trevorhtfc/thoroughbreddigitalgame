"""Evolved crowd figures: period racegoers with arms, legs, outfits in parts and a range of hats.

    python -c "exec(open('tools/blender/build_crowd_figures.py').read())" [lineup.png] [samples]

After reference/crowd/crowd-asset-pack.png. Still simple and stylised (roughly 500-900 triangles each),
built from swappable parts: body (gent or lady), pose, hat, outfit colours. Each figure keeps one
material per part (jacket, trousers, shirt, accent, dress, skin, hair, shoes, hat, hatband, prop) so an
engine can recolour every person from the palette.

Writes assets/models/architecture/crowd_figures.glb, and renders a line-up beside today's figures
(crowd_people.glb) when given a file name.
"""
import os, sys, math
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
OUT_PNG = ARGS[0] if ARGS else None
SAMPLES = int(ARGS[1]) if len(ARGS) > 1 else 32
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())
PARTS = ["jacket", "trousers", "shirt", "accent", "dress", "skin", "hair", "shoes", "hat", "hatband", "prop"]


def rod(k, mat, p0, p1, r0, r1=None, segs=7):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    g = bmesh.ops.create_cone(k.bm(mat), cap_ends=True, segments=segs, radius1=r0, radius2=r1 or r0, depth=d.length, matrix=k.M @ m)
    k._smooth(g["verts"])


def oval(k, mat, z0, z1, r0, r1, depth=0.72, segs=10):
    """A body section: an upright tapered cylinder, flattened front to back."""
    k.push(Matrix.Diagonal((1, depth, 1, 1)))
    k.cyl(mat, 0, 0, z0, z1, r0, r1, segs)
    k.pop()


# Arm poses for the right arm (+x); the left mirrors. Points are elbow and hand, for a gent's shoulder.
POSES = {
    "down":   ((0.27, 0.02, 1.12), (0.26, -0.02, 0.88)),
    "clasp":  ((0.25, -0.07, 1.12), (0.05, -0.19, 0.98)),
    "raise":  ((0.33, -0.02, 1.62), (0.35, -0.05, 1.9)),
    "binoc":  ((0.22, -0.24, 1.32), (0.07, -0.17, 1.6)),
    "prog":   ((0.27, -0.14, 1.15), (0.15, -0.33, 1.25)),
    "hip":    ((0.40, 0.02, 1.16), (0.21, 0.0, 0.98)),
    "hattip": ((0.32, -0.12, 1.52), (0.1, -0.07, 1.8)),
    "bag":    ((0.27, -0.02, 1.13), (0.25, -0.07, 0.95)),
}


def arms(k, lady, right, left, sleeve):
    sx, sz, s = (0.19, 1.33, 0.9) if lady else (0.235, 1.39, 1.0)
    for side, pose in ((1, right), (-1, left)):
        (ex, ey, ez), (hx, hy, hz) = POSES[pose]
        sh = (side * sx, 0, sz)
        el = (side * ex * s, ey, ez * (0.95 if lady else 1))
        ha = (side * hx * s, hy, hz * (0.95 if lady else 1))
        rod(k, sleeve, sh, el, 0.055 if lady else 0.065, 0.05 if lady else 0.058)
        rod(k, sleeve if not lady else "skin", el, ha, 0.048 if lady else 0.055, 0.04 if lady else 0.048)
        k.sphere("skin", *ha, 0.042 if lady else 0.048, 1)
        if pose == "prog":
            k.boxm("prop", Matrix.Translation(ha) @ Matrix.Rotation(-0.5, 4, "X"), 0.16, 0.012, 0.22)
        if pose == "bag":
            k.box("prop", ha[0] - 0.09, ha[0] + 0.09, ha[1] - 0.04, ha[1] + 0.04, ha[2] - 0.2, ha[2] - 0.05)
            rod(k, "prop", (ha[0] - 0.06, ha[1], ha[2] - 0.05), (ha[0], ha[1], ha[2] + 0.02), 0.008, segs=4)
    if right == "binoc":
        k.box("prop", -0.09, 0.09, -0.27, -0.16, 1.57, 1.65)
        for x in (-0.05, 0.05):
            rod(k, "prop", (x, -0.16, 1.61), (x, -0.3, 1.61), 0.035, segs=8)


def head(k, lady, hair="short", beard=False, z=1.62):
    r = 0.094 if lady else 0.1
    k.cyl("skin", 0, 0, z - 0.2, z - 0.08, 0.045, 0.05, 8)                 # neck
    k.push(Matrix.Translation((0, 0, z)) @ Matrix.Diagonal((0.92, 0.98, 1.15, 1)))
    k.sphere("skin", 0, 0, 0, r, 2)
    k.pop()
    k.sphere("skin", 0, -r * 0.98, z - 0.01, 0.018, 1)                       # nose
    for sx in (-1, 1):
        k.sphere("skin", sx * r * 0.88, 0.0, z, 0.022, 1)                    # ears
    if hair == "short":
        k.sphere("hair", 0, 0.045, z + 0.03, r * 0.98, 2, 1.0)            # set back and up: the face stays clear
    elif hair == "bun":
        k.sphere("hair", 0, 0.045, z + 0.025, r * 0.98, 2, 1.05)
        k.sphere("hair", 0, 0.1, z - 0.05, 0.055, 1)
    elif hair == "bob":
        k.sphere("hair", 0, 0.05, z, r * 1.02, 2, 1.12)
    if beard:
        k.sphere("hair", 0, -0.06, z - 0.08, 0.07, 1, 0.9)
    return z + r * 1.1                                                        # crown of the head


def hat(k, kind, z):
    if kind == "top":
        k.cyl("hat", 0, 0, z - 0.04, z - 0.02, 0.17, 0.17, 16)
        k.cyl("hat", 0, 0, z - 0.03, z + 0.16, 0.098, 0.106, 16)
        k.cyl("hatband", 0, 0, z - 0.02, z + 0.02, 0.1, 0.1, 16)
    elif kind == "boater":
        k.cyl("hat", 0, 0, z - 0.05, z - 0.035, 0.19, 0.19, 18)
        k.cyl("hat", 0, 0, z - 0.04, z + 0.035, 0.108, 0.108, 18)
        k.cyl("hatband", 0, 0, z - 0.035, z + 0.0, 0.11, 0.11, 18)
    elif kind == "trilby":
        k.cyl("hat", 0, 0, z - 0.05, z - 0.035, 0.16, 0.16, 14)
        k.sphere("hat", 0, 0, z - 0.01, 0.11, 2, 0.75)
        k.cyl("hatband", 0, 0, z - 0.04, z - 0.005, 0.105, 0.105, 14)
    elif kind == "cap":
        k.sphere("hat", 0, 0.01, z - 0.03, 0.115, 2, 0.5)
        k.boxm("hat", Matrix.Translation((0, -0.12, z - 0.05)) @ Matrix.Rotation(0.15, 4, "X"), 0.16, 0.08, 0.015)
    elif kind in ("wide", "flower"):
        k.cyl("hat", 0, 0, z - 0.06, z - 0.045, 0.26, 0.26, 20)
        k.sphere("hat", 0, 0, z - 0.03, 0.1, 2, 0.7)
        k.cyl("hatband", 0, 0, z - 0.05, z - 0.02, 0.102, 0.102, 16)
        if kind == "flower":
            for i, (a, s) in enumerate(((0.3, 0.05), (0.9, 0.04), (-0.2, 0.035))):
                k.sphere("accent", 0.1 * math.cos(a + 1.2), -0.09 * math.sin(a + 1.2), z - 0.02 + i * 0.01, s, 1)
    elif kind == "cloche":
        k.sphere("hat", 0, 0.01, z - 0.04, 0.115, 2, 0.85)
        k.cyl("hat", 0, 0, z - 0.09, z - 0.075, 0.15, 0.15, 16)


def gent(k, pose=("down", "down"), hatk="top", waistcoat=True, beard=False, build=1.0):
    k.push(Matrix.Diagonal((build, build, 1, 1)))
    for sx in (-1, 1):
        k.box("shoes", sx * 0.1 - 0.05, sx * 0.1 + 0.05, -0.17, 0.06, 0, 0.07)
        rod(k, "trousers", (sx * 0.1, 0, 0.06), (sx * 0.105, 0, 0.86), 0.068, 0.085)
    oval(k, "trousers", 0.78, 0.9, 0.17, 0.18)                                # seat
    oval(k, "jacket", 0.72, 1.06, 0.205, 0.19)                                # jacket skirt
    oval(k, "jacket", 1.06, 1.38, 0.19, 0.215)                                # chest
    k.push(Matrix.Translation((0, 0, 1.39)) @ Matrix.Diagonal((1.0, 0.62, 0.42, 1)))
    k.sphere("jacket", 0, 0, 0, 0.235, 2)                                     # shoulders
    k.pop()
    # the jacket's open front: waistcoat (or shirt) in a V, white shirt and tie at the top
    k.prism_y("accent" if waistcoat else "shirt", -0.142, -0.13, [(-0.085, 1.41), (0.085, 1.41), (0.02, 1.02), (-0.02, 1.02)])
    k.prism_y("shirt", -0.15, -0.14, [(-0.055, 1.41), (0.055, 1.41), (0, 1.25)])
    k.box("hatband" if not waistcoat else "trousers", -0.016, 0.016, -0.158, -0.148, 1.27, 1.4)   # tie
    arms(k, False, pose[0], pose[1], "jacket")
    k.pop()
    top = head(k, False, "short", beard)
    hat(k, hatk, top - 0.02)


def lady(k, pose=("down", "bag"), hatk="wide", hair="bun", build=1.0):
    k.push(Matrix.Diagonal((build, build, 1, 1)))
    for sx in (-1, 1):
        k.box("shoes", sx * 0.07 - 0.04, sx * 0.07 + 0.04, -0.13, 0.05, 0, 0.06)
        rod(k, "skin", (sx * 0.07, 0, 0.05), (sx * 0.075, 0, 0.5), 0.045, 0.055)
    k.push(Matrix.Diagonal((1, 0.8, 1, 1)))
    k.cyl("dress", 0, 0, 0.4, 1.0, 0.3, 0.13, 16)                              # skirt
    k.pop()
    oval(k, "dress", 0.98, 1.3, 0.125, 0.16, 0.75)                            # bodice
    k.push(Matrix.Translation((0, 0, 1.32)) @ Matrix.Diagonal((1.0, 0.65, 0.42, 1)))
    k.sphere("dress", 0, 0, 0, 0.19, 2)
    k.pop()
    oval(k, "accent", 0.97, 1.02, 0.135, 0.135, 0.76)                         # belt
    k.prism_y("accent", -0.13, -0.115, [(-0.07, 1.36), (0.07, 1.36), (0, 1.24)])  # collar
    arms(k, True, pose[0], pose[1], "dress")
    k.pop()
    top = head(k, True, hair, z=1.56)
    hat(k, hatk, top - 0.03)


# The line-up, after the character row on the reference sheet.
CAST = [
    ("gent_top_grey",     gent, dict(pose=("down", "clasp"), hatk="top"),
     {"jacket": "#3f4148", "trousers": "#8a8478", "accent": "#7a2a2a", "hat": "#1d1d21", "hatband": "#1d1d21"}),
    ("lady_cream_flower", lady, dict(pose=("bag", "down"), hatk="flower", hair="bun"),
     {"dress": "#efe3c4", "accent": "#b2362f", "hat": "#e9d9b4", "hatband": "#b2362f", "prop": "#6b3a26"}),
    ("gent_older_binoc",  gent, dict(pose=("binoc", "binoc"), hatk="boater", beard=True, waistcoat=False, build=1.08),
     {"jacket": "#2b3550", "trousers": "#4a4c52", "accent": "#a8323a", "hat": "#e3c48e", "hatband": "#2b3550", "hair": "#d8d4cc"}),
    ("gent_top_tails",    gent, dict(pose=("hip", "down"), hatk="top"),
     {"jacket": "#26272b", "trousers": "#6e6b66", "accent": "#b9a77a", "hat": "#1d1d21", "hatband": "#1d1d21"}),
    ("lady_navy_wide",    lady, dict(pose=("down", "bag"), hatk="wide", hair="bob"),
     {"dress": "#2b3550", "accent": "#efe3c4", "hat": "#efe3c4", "hatband": "#2b3550", "prop": "#c9b38a"}),
    ("gent_boater_olive", gent, dict(pose=("prog", "down"), hatk="boater"),
     {"jacket": "#6f6a3e", "trousers": "#c9b48a", "accent": "#b2362f", "hat": "#e3c48e", "hatband": "#b2362f", "prop": "#efe3c4"}),
    ("lady_pink_cloche",  lady, dict(pose=("clasp", "clasp"), hatk="wide", hair="bun"),
     {"dress": "#d98c8c", "accent": "#efe3c4", "hat": "#e6b97a", "hatband": "#d98c8c"}),
    ("gent_boater_green", gent, dict(pose=("raise", "down"), hatk="boater", waistcoat=False),
     {"jacket": "#4f6b3a", "trousers": "#cfc6b6", "accent": "#e6b97a", "hat": "#e3c48e", "hatband": "#2b3550"}),
    ("gent_trilby_navy",  gent, dict(pose=("hattip", "down"), hatk="trilby"),
     {"jacket": "#2f3d5c", "trousers": "#2f3d5c", "accent": "#c8693f", "hat": "#4a4c52", "hatband": "#1d1d21"}),
    ("lady_sage_red",     lady, dict(pose=("down", "prog"), hatk="flower", hair="bob"),
     {"dress": "#8ea06a", "accent": "#b2362f", "hat": "#b2362f", "hatband": "#efe3c4", "prop": "#efe3c4"}),
    ("gent_cap_tweed",    gent, dict(pose=("clasp", "clasp"), hatk="cap", build=1.05),
     {"jacket": "#7a6a52", "trousers": "#5a5348", "accent": "#4f6b3a", "hat": "#6b5c46", "hatband": "#6b5c46"}),
]
BASE = {"jacket": "#3a3e46", "trousers": "#4a4c52", "shirt": "#f4f0e6", "accent": "#7a2a2a", "dress": "#c99aa6",
        "skin": "#e8bf9c", "hair": "#4a3426", "shoes": "#1f1a17", "hat": "#1d1d21", "hatband": "#1d1d21", "prop": "#efe3c4"}
SKINS = ["#efc6a4", "#e2b48e", "#c99572", "#efc6a4", "#9a6a4a", "#e8bf9c", "#e2b48e", "#c99572", "#efc6a4", "#6e4a34", "#e2b48e"]
HAIRS = ["#3a2a20", "#7a4a2a", "#d8d4cc", "#2a2420", "#1f1a17", "#5a3a26", "#a8743a", "#3a2a20", "#4a3426", "#2a2420", "#6a5848"]

col = bpy.data.collections.new("crowd_figures")
bpy.context.scene.collection.children.link(col)
figures, tris = [], []
for i, (name, fn, kw, colours) in enumerate(CAST):
    k = Kit()
    fn(k, **kw)
    c = dict(BASE, skin=SKINS[i], hair=HAIRS[i]); c.update(colours)
    mats = {p: material("%s_%s" % (name, p), c[p], rough=0.75) for p in PARTS}
    ob, t = kit_to_object(k, name, mats, col)
    figures.append(ob); tris.append(t)
print("figures:", len(figures), "triangles each:", tris, flush=True)

os.makedirs(os.path.join(REPO, "assets/models/architecture"), exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
for o in figures:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(REPO, "assets/models/architecture/crowd_figures.glb"), export_format="GLB",
                          use_selection=True, export_yup=True, export_apply=False, export_animations=False)

if OUT_PNG:
    sc = bpy.context.scene
    for i, o in enumerate(figures):
        o.location = (i * 0.78 - len(figures) * 0.39, 0, 0)
    # today's figures at the end, for comparison
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "assets/models/architecture/crowd_people.glb"))
    old = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for j, o in enumerate(old):
        o.parent = None
        o.location = (len(figures) * 0.39 + 0.7 + j * 0.7, 0, 0)
    sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.64, 0.66, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object; sun.data.energy = 3.5; sun.data.angle = math.radians(8); sun.data.color = (1.0, 0.93, 0.82)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    bpy.ops.mesh.primitive_plane_add(size=60)
    fl = bpy.context.object
    fm = material("floor", "#d9d2c3", 0.9); fl.data.materials.append(fm)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 12.6
    cam.location = (0.9, -12, 2.6)
    cam.rotation_euler = (Vector((0.35, 0, 0.95)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.rotation_euler = (Vector((0.9, 0, 0.95)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1800, 520
    sc.view_settings.view_transform = "AgX"
    sc.render.filepath = os.path.abspath(OUT_PNG)
    bpy.ops.render.render(write_still=True)
    print("rendered", OUT_PNG, flush=True)
