"""Review renders for the clay crowd figures: today's 1C (set 8) beside the clay options (sets 9 and 10).

    python -c "exec(open('tools/blender/crowd_clay_review.py').read())" [samples]

Same people, same places and same colours in every set (colours from seeded dice, not Blender's object
random), under the model-look light of tools/blender/stand_clean_study.py (big soft warm sun, high-key sky
fill, the concept's crowd palette). Writes reference/crowd/clay/<set>_<view>.png for the views:
  lineup   the ten people twice over, facing the camera
  rail     packed behind the running rail, from the track (as the owner's restyled still)
  close    a few people near the rail, close up
  tv       the same crowd from the TV camera's distance
"""
import os, sys, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
OUT = rp("reference/crowd/clay"); os.makedirs(OUT, exist_ok=True)
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SAMPLES = int(ARGS[0]) if ARGS and ARGS[0].isdigit() else 32
SETS = os.environ.get("SETS", "8,9,10").split(",")
VIEWS = os.environ.get("VIEWS", "lineup,rail,close,tv").split(",")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


# ---------------- colours: the model look's crowd (stand_clean_study.py, variant model)
PAL = {
    "clothes": ["#3f4c6e", "#c8a97e", "#d4b25e", "#e6dcc6", "#b45a4c", "#5f8a8c", "#8fa8c4", "#a8866a", "#46546e", "#d8b0a6", "#7d8a72", "#efe6d2", "#a796c0", "#c97a5a"],
    "hats": ["#efe6d2", "#d8c08a", "#c8a97e", "#3a3a40", "#9fb4c8", "#d9a0a8", "#e6dcc6"],
    "skin": ["#efc6a4", "#e2b48e", "#c99572", "#9a6a4a"],
    "accent": ["#e6998b", "#8db58c", "#eccd7c", "#8eb0d6", "#b49fd2", "#f2ece0", "#c0453a"],
    "dark": ["#24262b", "#2f3036", "#3b352f"],
    "tophat": ["#2a2a2e", "#8e9096", "#a3a5aa", "#3a3c44", "#7a7c82", "#2a2b30", "#9a9ca2"],
    "tails": ["#3a3f52", "#8e9096", "#a3a5aa", "#2e3446", "#7a7c82", "#46546e", "#b4b2ac", "#2a2b30"],
}


def clay_mat(name, cols, attr, sss=0.0, rough=0.9):
    """Matte painted clay; the colour picked from cols by the person's own dice (object property attr)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.12
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.05, 0.03, 0.02); b.inputs["Subsurface Scale"].default_value = 0.02
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = attr
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    while len(els) < len(cols): els.new(0.5)
    for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
    nt.links.new(at.outputs["Fac"], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs["Base Color"])
    # the faintest tooth in the surface, measured on the figure
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 60.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.06; bp.inputs["Distance"].default_value = 0.003
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


M = {
    "fig_main": clay_mat("c_clothes", PAL["clothes"], "c_main"), "fig_skin": clay_mat("c_skin", PAL["skin"], "c_skin", sss=0.15),
    "fig_hat": clay_mat("c_hat", PAL["hats"], "c_hat"), "fig_trim": clay_mat("c_trim", PAL["accent"], "c_trim"),
    "fig_hair": clay_mat("c_hair", PAL["dark"], "c_hair"),
}
M_TOP = {"fig_main": clay_mat("c_tails", PAL["tails"], "c_main"), "fig_hat": clay_mat("c_tophat", PAL["tophat"], "c_hat")}


# ---------------- light and sky: the model look
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], ramp.inputs[0])
els = ramp.color_ramp.elements
els[0].position = 0.0; els[0].color = (1.0, 0.86, 0.76, 1)
mid = els.new(0.07); mid.color = (0.86, 0.84, 0.95, 1)
els[-1].position = 0.5; els[-1].color = (0.42, 0.56, 0.9, 1)
wl.new(ramp.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 1.15
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 3.4; sun.data.angle = math.radians(24); sun.data.color = (1.0, 0.9, 0.8)
d = Vector((-1.0, 0.45, 0.95)).normalized()   # from the west, a little in front of the crowd, high
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

def plain(name, hexc, rough=0.95):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexc); b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.1
    return m

def mesh(name, build, mat):
    me = bpy.data.meshes.new(name); bm = bmesh.new(); build(bm); bm.to_mesh(me); bm.free()
    me.materials.append(mat); ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = False
    return ob

# the lawn the crowd stands on (warm, pale), the turf beyond the rail, and Ascot's white rail
mesh("lawn", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1,
     matrix=Matrix.Translation((40, -30, 0)) @ Matrix.Diagonal((140, 30.6, 1, 1))), plain("lawn", "#cdc6ad"))
mesh("turf", lambda bm: bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1,
     matrix=Matrix.Translation((40, 40, -0.005)) @ Matrix.Diagonal((140, 39.4, 1, 1))), plain("turf", "#93b466"))
def rail_geo(bm):
    for x in range(-40, 120, 2):
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, 0.9, 0.5)) @ Matrix.Diagonal((0.08, 0.08, 1.0, 1)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.06, radius2=0.06, depth=160,
                          matrix=Matrix.Translation((40, 0.95, 1.02)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
rl = mesh("rail", rail_geo, plain("rail", "#f4f2ea", 0.9))
for p in rl.data.polygons: p.use_smooth = True


def load_set(sid):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=rp("assets/models/architecture/crowd_set_%s.glb" % sid))
    obs = sorted([o for o in bpy.data.objects if o not in before and o.type == "MESH"], key=lambda o: o.name)
    coll = bpy.data.collections.new("src_" + sid); scene.collection.children.link(coll); coll.hide_render = True
    for o in obs:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o); o.parent = None; o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
        top = "_top" in o.name
        for i, sl in enumerate(o.material_slots):
            base = (sl.material.name if sl.material else "").split(".")[0]
            if base in M:
                o.material_slots[i].material = (M_TOP.get(base) if top else None) or M[base]
    for o in [o for o in bpy.data.objects if o not in before and o.type != "MESH"]:
        bpy.data.objects.remove(o)
    return obs


def person(src, fi, x, y, yaw, s, dice):
    o = src[fi].copy(); scene.collection.objects.link(o)
    o.location = (x, y, 0); o.rotation_euler = (0, 0, yaw); o.scale = (s, s, s)
    for k, v in dice.items(): o[k] = v
    return o


def crowd_spots():
    """The same packed crowd for every set: rows behind the rail, thinning to the back, people turned a little."""
    rnd = random.Random(21); spots = []
    weights = [4, 4, 1, 1, 1, 1, 1, 1, 1, 1]                  # top hats four times as often (as the race view)
    for row in range(9):
        y = -0.15 - row * 0.62
        x = -20.0
        while x < 110:
            x += rnd.uniform(0.5, 0.68)
            if row > 5 and rnd.random() < 0.15 * (row - 5): continue
            fi = rnd.choices(range(10), weights)[0]
            dice = {k: rnd.random() for k in ("c_main", "c_skin", "c_hat", "c_trim", "c_hair")}
            spots.append((fi, x, y + rnd.uniform(-0.18, 0.18), (rnd.random() - 0.5) * 1.0, 0.94 + rnd.random() * 0.12, dice))
    return spots


SPOTS = crowd_spots()
LINE = []
rl_ = random.Random(5)
for k in range(2):
    for fi in range(10):
        LINE.append((fi, {c: rl_.random() for c in ("c_main", "c_skin", "c_hat", "c_trim", "c_hair")}))

scene.render.engine = "CYCLES"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.view_settings.exposure = 0.12
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.clip_end = 3000


def shoot(path, eye, at, lens, res, ortho=None):
    cam.location = eye; cam.rotation_euler = (Vector(at) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho: cam.data.ortho_scale = ortho
    else: cam.data.lens = lens
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path; bpy.ops.render.render(write_still=True); print("rendered", path, flush=True)


for sid in SETS:
    src = load_set(sid)
    if "lineup" in VIEWS:
        shown = []
        for j, (fi, dice) in enumerate(LINE):
            shown.append(person(src, fi, (j - 9.5) * 0.74, -3.0, 0.0, 1.0, dice))
        rl.hide_render = True
        shoot(os.path.join(OUT, "set%s_lineup.png" % sid), (0, 30, 1.25), (0, -3, 1.0), 0, (2000, 400), ortho=15.2)
        rl.hide_render = False
        for o in shown: bpy.data.objects.remove(o)
    shown = [person(src, fi, x, y, yaw, s, dice) for fi, x, y, yaw, s, dice in SPOTS]
    if "rail" in VIEWS:     # along the rail from the track side, as the owner's restyled still
        shoot(os.path.join(OUT, "set%s_rail.png" % sid), (-3.2, 4.6, 2.5), (9.0, -2.2, 1.0), 26, (1600, 1000))
    if "close" in VIEWS:    # close in on the front rows
        shoot(os.path.join(OUT, "set%s_close.png" % sid), (2.2, 3.3, 1.9), (5.2, -1.2, 1.25), 40, (1600, 1000))
    if "tv" in VIEWS:       # the TV camera's distance, across the track
        shoot(os.path.join(OUT, "set%s_tv.png" % sid), (8.0, 34.0, 7.0), (14.0, -2.0, 1.0), 50, (1600, 900))
    for o in shown: bpy.data.objects.remove(o)
print("done", flush=True)
