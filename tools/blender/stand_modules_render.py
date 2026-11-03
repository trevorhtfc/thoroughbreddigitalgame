"""Review stills of the stand module kit and of Ascot's assembled main stand.

    python -c "exec(open('tools/blender/stand_modules_render.py').read())" [samples]

Run tools/blender/build_stand_modules.py first. Writes to reference/architecture/renders/:
  stand_modules_catalogue.png   every module in a row, labelled by bays
  ascot_stand_wide.png          the whole 500 m stand from across the track
  ascot_stand_34.png            three-quarter view along the front from the east end
  ascot_stand_post.png          the clock tower and the west end, from the far side by the post
Plain stylised lighting (warm sun, blue sky, AgX), no crowd: it is for judging the modules.
"""
import os, sys, math, json
import bpy
from mathutils import Vector

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
SAMPLES = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 48
OUT = rp("reference/architecture/renders"); os.makedirs(OUT, exist_ok=True)
COURSE = json.load(open(rp("courses/ascot.json")))
CAT = json.load(open(rp("assets/models/architecture/stand_modules.json")))
FRONT = COURSE["grandstand"]["frontLine"]
W = COURSE["trackWidth"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def flat(name, hexc, rough=0.9):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = rough
    return m


def plane(name, x0, x1, y0, y1, mat, z=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    return ob


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


# world: Blender x = east, y = north (= -course z), z up. glTF import maps course z (south) to -y.
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
grad = wn.new("ShaderNodeTexGradient"); tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ")
ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[0].color = (0.75, 0.84, 0.92, 1)
ramp.color_ramp.elements[1].position = 0.85; ramp.color_ramp.elements[1].color = (0.28, 0.5, 0.86, 1)
wl.new(ramp.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 1.0
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object; sun.data.energy = 4.5; sun.data.angle = math.radians(5); sun.data.color = (1.0, 0.9, 0.76)
# for review the sun comes from the north-east, high, so the north-facing front is lit
sun.rotation_euler = Vector((-0.55, -0.75, -0.75)).to_track_quat("-Z", "Y").to_euler()

grass, turf, rail = flat("grass", "#7f9f55"), flat("turf", "#93b862"), flat("rail", "#f4f4f0", 0.5)

scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.max_bounces = 4
scene.view_settings.view_transform = "AgX"
scene.render.resolution_x, scene.render.resolution_y = 1600, 900


def camera(name, loc, look, lens):
    cam = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    if cam.name not in scene.collection.objects: scene.collection.objects.link(cam)
    cam.data.lens = lens; cam.data.clip_end = 6000
    cam.location = loc
    d = Vector(look) - Vector(loc); cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True); print("rendered", scene.render.filepath, flush=True)


# ---------------- catalogue ----------------
kit = import_glb(rp("assets/models/architecture/stand_modules.glb"))
g = plane("ground_cat", -20, 900, -60, 60, grass)
xs = [o.location.x for o in kit]
mid = (min(xs) + max(xs) + 30) / 2
camera("stand_modules_catalogue", (mid - 40, -340, 110), (mid - 40, 0, 6), 32)
for o in kit: bpy.data.objects.remove(o)
bpy.data.objects.remove(g)

# ---------------- the assembled stand at Ascot ----------------
stand = import_glb(rp("assets/models/architecture/ascot_main_stand.glb"))
root = bpy.data.objects.new("stand", None); scene.collection.objects.link(root)
for o in stand: o.parent = root
root.location = (0, -FRONT, 0)                               # course z (south) = -Blender y
plane("ground", -900, 1400, -700, 500, grass, -0.02)
plane("track", -300, 1300, -W, 0, turf, 0.0)
for y in (0.0, -W):                                          # rails along the home straight
    plane("rail_%d" % int(-y), -300, 1300, y - 0.12, y + 0.12, rail, 1.0)
plane("post", -0.15, 0.15, 0.2, -0.2, flat("post", "#c0392b"), 2.6)

camera("ascot_stand_wide", (140, 260, 70), (150, -FRONT - 10, 10), 26)
camera("ascot_stand_34", (480, -FRONT + 60, 26), (150, -FRONT - 10, 12), 30)
camera("ascot_stand_post", (-40, 40, 14), (10, -FRONT - 10, 14), 28)
