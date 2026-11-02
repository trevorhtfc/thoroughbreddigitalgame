"""Grandstand look test: the Victorian grandstand with its crowd, beside the horses in the stylised scene.

    python -c "exec(open('tools/blender/grandstand_look_test.py').read())" <out_dir> [samples]
    SHOT=stand_wide python -c ...        # render one shot only

Builds the stylised scene from stylised_look_test.py (without rendering its own shots), then adds
assets/models/architecture/victorian_grandstand.glb on the near side of the track, facing the course,
and fills the lawn, steps and balconies with simple instanced spectators (crowd_people.glb).
Run tools/blender/build_grandstand.py first.
"""
import os, sys, json, math, random

_only = os.environ.get("SHOT")
os.environ["SHOT"] = "__none__"                   # build the scene but skip its own shots
exec(open(os.path.join(os.path.abspath("."), "tools/blender/stylised_look_test.py")).read())
if _only:
    os.environ["SHOT"] = _only
else:
    os.environ.pop("SHOT")

ARCH = os.path.join(REPO, "assets/models/architecture")
STAND_AT = Vector((20.0, -52.0, 0.0))              # middle of the stand's front, at ground level
RC = random.Random(21)

# ---------------- Grandstand ----------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ARCH, "victorian_grandstand.glb"))
stand = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
root = bpy.data.objects.new("grandstand", None)
scene.collection.objects.link(root)
for o in stand:
    o.parent = root
root.location = STAND_AT
root.rotation_euler = (0, 0, math.pi)              # front (-y in the model) turns to face the track (+y)


def painted(mat):
    """Soft, painted variation on the plain stand colours, a touch darker near the ground, then haze."""
    n, l = mat.node_tree.nodes, mat.node_tree.links
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    base = tuple(b.inputs["Base Color"].default_value)
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 3
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    vr = n.new("ShaderNodeMapRange"); vr.inputs["To Min"].default_value = 0.9; vr.inputs["To Max"].default_value = 1.06
    l.new(nz.outputs["Fac"], vr.inputs["Value"])
    sp = n.new("ShaderNodeSeparateXYZ"); l.new(tc.outputs["Object"], sp.inputs[0])
    gr = n.new("ShaderNodeMapRange"); gr.inputs["From Max"].default_value = 3.5; gr.inputs["To Min"].default_value = 0.82
    l.new(sp.outputs["Z"], gr.inputs["Value"])
    m1 = n.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    l.new(vr.outputs[0], m1.inputs[0]); l.new(gr.outputs[0], m1.inputs[1])
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
    mx.inputs[6].default_value = base
    cv = n.new("ShaderNodeCombineColor")
    for k in range(3):
        l.new(m1.outputs[0], cv.inputs[k])
    l.new(cv.outputs[0], mx.inputs[7])
    l.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Specular IOR Level"].default_value = 0.25


for o in stand:
    for m in o.data.materials:
        key = m.name.replace("gs_", "")
        if key in ("wall", "trim", "podium", "steps", "iron"):
            painted(m)
        if key == "clock_face":
            bb = next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
            bb.inputs["Emission Color"].default_value = srgb("#fffaf0"); bb.inputs["Emission Strength"].default_value = 0.35
        add_haze(m, m.node_tree.nodes, m.node_tree.links)

# Clear the trees that would stand inside the grandstand or on its lawn.
for o in list(bpy.data.objects):
    if o.name.startswith("tree") and o.type == "EMPTY":
        x, y = o.location.x, o.location.y
        if -50 < x < 92 and -92 < y < -20:
            bpy.data.objects.remove(o, do_unlink=True)

# Woodland behind the stand, and clumps beyond its ends, so the roofline sits against trees.
for row in range(5):
    x = -120 + RC.uniform(0, 10)
    while x < 170:
        place_tree(x, -98 - row * 16 + RC.uniform(-6, 6), RC.uniform(1.0, 1.5))
        x += RC.uniform(8, 13)
for x0 in (-62, -78, 104, 120):
    for k in range(RC.randint(2, 4)):
        place_tree(x0 + RC.uniform(-8, 8), -60 + RC.uniform(-14, 10), RC.uniform(0.9, 1.25))

# ---------------- Crowd ----------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ARCH, "crowd_people.glb"))
figures = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
SUITS = ["#23262d", "#2c3240", "#3a3e46", "#4b4f57", "#1f2a3c", "#5d5a55", "#6f6a62"]
DRESSES = ["#e79cb2", "#8ec0e2", "#f1e4c4", "#d6524f", "#6aa86a", "#eac64a", "#fbf8f0", "#8a6cb8", "#ef8a5a", "#3e7fb8"]
SKIN = ["#efc6a4", "#e2b48e", "#c99572", "#9a6a4a", "#6e4a34"]
HATS_LADY = ["#fbf8f0", "#1f1f24", "#e79cb2", "#d8b46a", "#8ec0e2", "#7a2a3a"]


def flat(hexc, rough=0.85):
    m = bpy.data.materials.new("crowd_" + hexc)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(hexc); b.inputs["Roughness"].default_value = rough
    add_haze(m, m.node_tree.nodes, m.node_tree.links)
    return m


_mcache = {}
def mat(hexc):
    if hexc not in _mcache:
        _mcache[hexc] = flat(hexc)
    return _mcache[hexc]


VARIANTS_P = []
for f in figures:
    lady = "lady" in f.name
    for v in range(8):
        o = f.copy(); o.data = f.data.copy()
        clothes = RC.choice(DRESSES if lady else SUITS)
        hat = RC.choice(HATS_LADY) if lady else ("#1c1c20" if RC.random() < 0.8 else "#5a5248")
        pick = {"clothes": mat(clothes), "skin": mat(RC.choice(SKIN)), "hat": mat(hat)}
        for i, m in enumerate(list(o.data.materials)):
            o.data.materials[i] = pick[next(k for k in pick if k in m.name)]
        VARIANTS_P.append(o)
for f in figures:
    bpy.data.objects.remove(f, do_unlink=True)
count = 0


def person(x, y, z=0.0):
    global count
    o = RC.choice(VARIANTS_P).copy()           # linked duplicate: shares the mesh
    o.location = (x, y, z)
    o.rotation_euler = (0, 0, RC.uniform(-0.6, 0.6))
    s = RC.uniform(0.94, 1.06); o.scale = (s, s, s)
    scene.collection.objects.link(o)
    count += 1


X0, X1 = STAND_AT.x - 64, STAND_AT.x + 64
# Packed along the rail, thinning back towards the stand; knots of people on the lawn.
y = -17.0
while y > -50:
    density = 0.95 if y > -19.5 else (0.45 if y > -24 else 0.12)
    x = X0
    while x < X1:
        if RC.random() < density:
            person(x + RC.uniform(-0.2, 0.2), y + RC.uniform(-0.2, 0.2))
        x += 0.62
    y -= 0.7
for g in range(26):                              # groups on the lawn and the promenade
    gx, gy = RC.uniform(X0 + 4, X1 - 4), RC.uniform(-48, -26)
    for k in range(RC.randint(3, 8)):
        person(gx + RC.gauss(0, 1.0), gy + RC.gauss(0, 0.8))

# Balconies, galleries and steps, from the stand's standing areas.
areas = json.load(open(os.path.join(ARCH, "victorian_grandstand_crowd_areas.json")))["areas"]
podium_h = 3.0
for a in areas:
    if a["kind"] == "lawn_front_line":
        continue
    rows = 1 if a["y1"] - a["y0"] < 1.4 else 2
    for r in range(rows):
        ly = a["y0"] + 0.15 + r * 0.75
        x = a["x0"]
        while x < a["x1"]:
            fill = 0.35 if a["kind"] == "steps" else (0.78 if r == 0 else 0.4)
            if RC.random() < fill:
                z = a["z"]
                if a["kind"] == "steps":
                    run = -a["y0"] + 0.3
                    z = podium_h * (ly + run) / run
                wx, wy = STAND_AT.x - (x + RC.uniform(-0.1, 0.1)), STAND_AT.y - ly    # stand is turned 180 degrees
                person(wx, wy, z)
            x += 0.62
print("crowd:", count, "people", flush=True)

# ---------------- Shots ----------------
GSHOTS = {
    "stand_wide": ((2, 42, 11), (22, -55, 9), 22),         # from across the course: horses, rail crowd, the whole stand
    "stand_tv": ((40, 24, 3.2), (12, -30, 7.5), 30),        # low, with the field passing in front of the stand
    "stand_34": ((-78, 22, 24), (8, -62, 9), 28),           # three-quarter view of the stand, as on the sheet
}
if os.environ.get("PREVIEW"):
    scene.render.resolution_percentage = 50
only = os.environ.get("SHOT")
for k, v in GSHOTS.items():
    if not only or only == k:
        shot(k, *v)
