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
PAL = json.load(open(os.path.join(ARCH, "crowd_palette.json")))
SUITS, DRESSES, SKIN, HATS_LADY, HATS_GENT = PAL["suits"], PAL["dresses"], PAL["skin"], PAL["hats_lady"], PAL["hats_gent"]


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
        hat = RC.choice(HATS_LADY) if lady else RC.choice(HATS_GENT)
        pick = {"clothes": mat(clothes), "skin": mat(RC.choice(SKIN)), "hat": mat(hat)}
        for i, m in enumerate(list(o.data.materials)):
            o.data.materials[i] = pick[next(k for k in pick if k in m.name)]
        VARIANTS_P.append(o)
for f in figures:
    bpy.data.objects.remove(f, do_unlink=True)
count = 0


def person(x, y, z=0.0, face=None, seated=False):
    global count
    o = RC.choice(VARIANTS_P).copy()           # linked duplicate: shares the mesh
    o.location = (x, y, z)
    o.rotation_euler = (0, 0, (face if face is not None else 0) + RC.uniform(-0.6, 0.6))
    s = RC.uniform(0.94, 1.06); o.scale = (s, s, s * (0.7 if seated else 1.0))
    scene.collection.objects.link(o)
    count += 1
    return o


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

# ---------------- Site components round the stand (courses/ascot-site-dressing-straight.json) ----------------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(ARCH, "site_props.glb"))
LIBP = {o.name.split(".")[0]: o for o in bpy.data.objects if o not in before and o.type == "MESH"}
for o in LIBP.values():
    for m in o.data.materials:
        if m.get("_done"):
            continue
        m["_done"] = True
        key = m.name.replace("sp_", "").split(".")[0]
        if key in ("canvas", "timber", "trim", "wall", "roof", "board", "seat", "stripe"):
            painted(m)
        add_haze(m, m.node_tree.nodes, m.node_tree.links)
    o.hide_render = True; o.hide_viewport = True
DRESS = json.load(open(os.path.join(REPO, "courses/ascot-site-dressing-straight.json")))   # the 124 m stand on the old straight
SPOTS = json.load(open(os.path.join(ARCH, "site_props_spots.json")))["pieces"]
placed = 0
for p in DRESS["pieces"]:
    src = LIBP[p["piece"]]
    o = src.copy()                                  # linked duplicate
    o.hide_render = False; o.hide_viewport = False
    rot = math.pi + math.radians(p.get("turn", 0))  # front (-y in the model) turned to face the course, then the turn
    pos = Vector((STAND_AT.x + p["dx"], STAND_AT.y - p["dz"], 0))
    o.location = pos
    o.rotation_euler = (0, 0, rot)
    scene.collection.objects.link(o)
    placed += 1
    sp = SPOTS.get(p["piece"], {})
    Rz = Matrix.Rotation(rot, 3, "Z")
    for kind, fill in (("seats", 0.62), ("stand", 0.7)):
        for lx, ly, lz in sp.get(kind, []):
            if RC.random() < fill:
                w = pos + Rz @ Vector((lx, ly, 0))
                person(w.x, w.y, lz, face=rot + math.pi, seated=(kind == "seats"))
# Crowds on the lawns and along the far rail.
for c in DRESS.get("crowds", []):
    area = (c["dx"][1] - c["dx"][0]) * (c["dz"][1] - c["dz"][0])
    for i in range(int(area * c["density"])):
        dx, dz = RC.uniform(*c["dx"]), RC.uniform(*c["dz"])
        person(STAND_AT.x + dx, STAND_AT.y - dz)
print("site components:", placed, "placed; people now", count, flush=True)
for o in list(bpy.data.objects):                    # keep trees out of the dressed areas
    if o.name.startswith("tree") and o.type == "EMPTY":
        dx, dz = o.location.x - STAND_AT.x, STAND_AT.y - o.location.y
        if (-110 < dx < 112 and -36 < dz < 24) or (-110 < dx < -20 and -122 < dz < -66):
            bpy.data.objects.remove(o, do_unlink=True)

# ---------------- Finish line, opposite the stand (courses/ascot-home-straight.json) ----------------
COURSE = json.load(open(os.path.join(REPO, "courses/ascot-home-straight.json")))
WP = COURSE["winningPost"]
GS = next(s for s in COURSE["structures"] if s["model"] == "victorian_grandstand")
POST_X = STAND_AT.x + (WP["at"] - GS["x"])          # the winning line, in this scene
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, WP["file"]))
for o in [o for o in bpy.data.objects if o not in before and o.type == "MESH"]:
    o.location = (POST_X, 15.4, 0)                   # far rail line; its front already faces the stand
    for m in o.data.materials:
        key = m.name.replace("fl_", "").split(".")[0]
        if key in ("trim", "board", "timber"):
            painted(m)
        add_haze(m, m.node_tree.nodes, m.node_tree.links)
for o in list(bpy.data.objects):                     # the assembly brings its own rail
    if o.name.startswith("rail_module") and o.location.y > 0 and POST_X + WP["railFrom"] - 3 < o.location.x < POST_X + WP["railTo"]:
        bpy.data.objects.remove(o, do_unlink=True)

# ---------------- Shots ----------------
GSHOTS = {
    "stand_wide": ((2, 11, 11), (22, -55, 9), 22),         # from over the far side of the course: horses, rail crowd, the whole stand
    "stand_tv": ((40, 24, 3.2), (12, -30, 7.5), 30),        # low, with the field passing in front of the stand
    "stand_34": ((-78, 22, 24), (8, -62, 9), 28),           # three-quarter view of the stand, as on the sheet
    "far_side": ((30, -49, 13.5), (-40, 45, 2), 26),        # from the stand's balcony across the course to the far side
    "site_aerial": ((150, 95, 95), (-5, -40, 0), 24),       # high over the course: the stand and everything round it
    "finish": ((2.5, -12, 2.6), (2.5, 20, 2.4), 30),       # down the winning line from the stand side: loop, post and boards
    "finish_wide": ((-30, -30, 14), (6, 16, 2), 30),        # the finish line opposite the stand, with the field
}
if os.environ.get("PREVIEW"):
    scene.render.resolution_percentage = 50
only = os.environ.get("SHOT")
for k, v in GSHOTS.items():
    if not only or only == k:
        shot(k, *v)
