"""Build the course furniture in Blender and export it as one glTF.

    python tools/blender/build_course_props.py -- assets/models/course/course_props.glb assets/models/master/course_props.blend

Headless (Blender's Python module, bpy). Everything is in metres, modelled in
Blender's Z-up axes; the glTF export turns that into Y-up, so in the .glb:
x = direction of running, y = up, z = across the course (+ = outside the near rail).

Objects (each its own node in the .glb, origin at ground level):
- rail_module    one capped post plus 3 m of white rail with a green top, for the NEAR side: the
                 rail is at z = 0, the post just outside it (+z). Rotate 180°
                 about y for the far side. Repeat every 3 m along the course.
- winning_post   heritage winning post: green-and-white spiral pole with the red
                 and white roundel facing across the course.
- furlong_1..7   white furlong poles with a bottle-green roundel and the number.

Colours follow the board: bottle green #1f5a38, cream-white rails, roundel red.
"""
import sys, math
import bpy, bmesh

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = argv[0] if argv else "course_props.glb"
BLEND = argv[1] if len(argv) > 1 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, hexcol, rough=0.6):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    h = hexcol.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*lin, 1)
    bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*lin, 1)
    return m


WHITE = mat("rail_white", "#f2efe6", 0.55)
GREEN = mat("bottle_green", "#1f5a38", 0.5)
RED = mat("roundel_red", "#b8322a", 0.5)


def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob


def cylinder(bm, r, h, segs=16, rings=1, origin=(0, 0, 0), axis="z", mat_fn=None, cap=True):
    """Cylinder into bmesh. axis z = upright; axis y = facing across the course."""
    ox, oy, oz = origin
    verts = []
    for j in range(rings + 1):
        row = []
        t = h * j / rings
        for i in range(segs):
            a = 2 * math.pi * i / segs
            c, s = math.cos(a) * r, math.sin(a) * r
            if axis == "z":
                co = (ox + c, oy + s, oz + t)
            elif axis == "y":
                co = (ox + c, oy + t, oz + s)
            else:
                co = (ox + t, oy + c, oz + s)
            row.append(bm.verts.new(co))
        verts.append(row)
    for j in range(rings):
        for i in range(segs):
            f = bm.faces.new([verts[j][i], verts[j][(i + 1) % segs], verts[j + 1][(i + 1) % segs], verts[j + 1][i]])
            if mat_fn:
                f.material_index = mat_fn(i / segs, (j + 0.5) / rings)
    if cap:
        f0 = bm.faces.new(list(reversed(verts[0])))
        f1 = bm.faces.new(verts[-1])
        if mat_fn:
            f0.material_index = mat_fn(0, 0)
            f1.material_index = mat_fn(0, 1)
        for f in (f0, f1):
            f.smooth = False
    return verts


def box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    r = bmesh.ops.create_cube(bm, size=1)
    for v in r["verts"]:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mi
        f.smooth = False


# ---------- Running rail module ----------
# glTF +z (outside the near rail) is Blender -y. White posts with a small pyramid
# cap, a white rounded rail with a bottle-green top, one module = 3 m.
bm = bmesh.new()
box(bm, -0.045, 0.045, -0.165, -0.075, 0.0, 0.93)                  # post, just outside the rail
cap = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.068, radius2=0.0, depth=0.05)
for v in cap["verts"]:
    v.co.rotate(__import__("mathutils").Euler((0, 0, math.pi / 4)))
    v.co += __import__("mathutils").Vector((0, -0.12, 0.955))
for f in {f for v in cap["verts"] for f in v.link_faces}:
    f.smooth = False
cylinder(bm, 0.068, 3.0, segs=14, origin=(0, 0, 0.97), axis="x")   # white rail
cylinder(bm, 0.028, 0.12, segs=8, origin=(0, -0.13, 0.90), axis="y")  # bracket from post to rail
# Green top: a flattened tube sitting on the rail
before = set(bm.verts)
cylinder(bm, 0.072, 3.0, segs=14, origin=(0, 0, 0.0), axis="x", mat_fn=lambda u, v: 1)
for v in set(bm.verts) - before:
    v.co.z = v.co.z * 0.5 + 1.0
for f in bm.faces:
    if all(v not in before for v in f.verts):
        f.material_index = 1
new_obj("rail_module", bm, [WHITE, GREEN])

# ---------- Winning post ----------
bm = bmesh.new()
H = 4.4
turns = 9
cylinder(bm, 0.075, H, segs=24, rings=110, origin=(0, 0, 0),
         mat_fn=lambda u, v: int(((u + v * turns) % 1.0) < 0.5))   # spiral green/white
RZ = H + 0.45
# Roundel faces across the course (its flat faces look along Blender y).
cylinder(bm, 0.58, 0.05, segs=48, origin=(0, -0.025, RZ), axis="y", mat_fn=lambda u, v: 2)
for side in (-1, 1):
    y = 0.026 * side - (0.006 if side < 0 else 0)
    cylinder(bm, 0.40, 0.006, segs=48, origin=(0, y if side > 0 else y - 0.0, RZ), axis="y", mat_fn=lambda u, v: 1)
# Finial on top of the roundel
cylinder(bm, 0.05, 0.12, segs=12, origin=(0, 0, RZ + 0.58), mat_fn=lambda u, v: 0)
new_obj("winning_post", bm, [GREEN, WHITE, RED])


# ---------- Furlong poles ----------
def number_mesh(txt, size, y, flip):
    cu = bpy.data.curves.new("n" + txt, "FONT")
    cu.body = txt
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.extrude = 0.004
    ob = bpy.data.objects.new("tmp", cu)
    scene.collection.objects.link(ob)
    ob.rotation_euler = (math.pi / 2, 0, math.pi if flip else 0)
    ob.location = (0, y, 0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.transform(ob.matrix_world)
    bpy.data.objects.remove(ob)
    return me


for n in range(1, 8):
    bm = bmesh.new()
    PH = 2.7
    cylinder(bm, 0.055, PH, segs=14, origin=(0, 0, 0), mat_fn=lambda u, v: 0)
    DZ = PH + 0.25
    cylinder(bm, 0.34, 0.04, segs=40, origin=(0, -0.02, DZ), axis="y", mat_fn=lambda u, v: 0)   # white rim
    cylinder(bm, 0.29, 0.05, segs=40, origin=(0, -0.025, DZ), axis="y", mat_fn=lambda u, v: 1)  # green face
    for flip, y in ((False, -0.03), (True, 0.03)):
        me = number_mesh(str(n), 0.36, y, flip)
        me.transform(__import__("mathutils").Matrix.Translation((0, 0, DZ)))
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    # Faces added from the number meshes keep material index 0 = white.
    new_obj("furlong_%d" % n, bm, [WHITE, GREEN])

# Lay them out in a row for anyone opening the .blend; the game places them itself.
for i, ob in enumerate(scene.collection.objects):
    ob.location.x += i * 2.0 if ob.name != "rail_module" else 0

if BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
# The game positions each piece from the course file, so export every object at
# the origin.
for ob in scene.collection.objects:
    ob.location = (0, 0, 0)
bpy.ops.export_scene.gltf(filepath=GLB, export_format="GLB", export_yup=True, export_apply=True)
print("exported", GLB, [o.name for o in scene.collection.objects])
