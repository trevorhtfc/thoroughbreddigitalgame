"""Bake the soft shadows and grounding of a Newmarket course's buildings onto its ground, for the race view.

    COURSE=newmarket python -c "exec(open('tools/blender/bake_newmarket_ground.py').read())"      (or COURSE=newmarket-july)
    env: SAMPLES (32), MPP (metres a pixel, 0.25), PAD (metres round the pieces, 60)

The Newmarket courses are drawn live in the race view: their ground is painted, not lit, so the stands, marquees and
walls cast nothing on the lawns, and nothing sits on its shadow (owner, 9 Nov 2026: the model look, "start applying this
to Newmarket as well"). This builds the course's scenery exactly where the race view puts it (race-view/assets/course/
<course>-scenery.json: pieces, walls and hedges, the finish line) on a plain white ground, lights it with the model look's
light (Ascot's bake, tools/blender/bake_static_world.py LOOK=model: big soft sun, strong lilac-blue sky fill; the
course's own sun direction raised, as <course>-view.json -> light.sunDir), and renders the ground straight down. Divided
by the open ground's light, that is how much light each patch of ground gets: soft shadows, the shade at the foot of every
wall, a faint lilac in the shade. The race view multiplies its ground colours by it (view file -> groundLight).

Writes race-view/assets/course/<course>-ground-light.jpg and adds "groundLight" {map, area} to <course>-view.json
(re-run tools/course/newmarket/to_race_view.py first if the layout changed: it rewrites the view file; this script puts
the groundLight entry back).
Race-view axes: x along the straight, y up, z across (stands +z on the Rowley Mile); Blender = (x, -z, y).
"""
import os, json, math
import numpy as np
import bpy
from mathutils import Vector, Matrix

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)
CID = os.environ.get("COURSE", "newmarket")
SAMPLES = int(os.environ.get("SAMPLES", "32"))
MPP = float(os.environ.get("MPP", "0.25"))
PAD = float(os.environ.get("PAD", "60"))
CDIR = rp("race-view/assets/course")
SC = json.load(open(os.path.join(CDIR, f"{CID}-scenery.json")))
VIEW = json.load(open(os.path.join(CDIR, f"{CID}-view.json")))
LIGHT = VIEW["light"]
ARCH = rp("assets/models/architecture")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def B(x, z, y=0.0): return Vector((x, -z, y))


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


# ---- one grey matte material for everything that casts (colour hardly matters for shadows; a mid grey keeps the
# light bounced onto the ground near walls about right)
caster = bpy.data.materials.new("caster"); caster.use_nodes = True
bs = caster.node_tree.nodes["Principled BSDF"]; bs.inputs["Base Color"].default_value = lin("#d8ccb4"); bs.inputs["Roughness"].default_value = 0.95
ground_mat = bpy.data.materials.new("ground"); ground_mat.use_nodes = True
bg = ground_mat.node_tree.nodes["Principled BSDF"]; bg.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1); bg.inputs["Roughness"].default_value = 1.0
bg.inputs["Specular IOR Level"].default_value = 0.0


def load_lib(name):
    """Import a .glb into a hidden collection; return {node name: object}."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ARCH, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    coll = bpy.data.collections.new("lib_" + name)
    for o in new:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o)
    bpy.context.view_layer.update()
    return {o.name.split(".")[0]: o for o in new}


libs = {m: load_lib(m) for m in SC.get("models", [])}
out = bpy.data.collections.new("placed"); scene.collection.children.link(out)


def meshes_under(o):
    stack, res = [o], []
    while stack:
        n = stack.pop(); stack.extend(n.children)
        if n.type == "MESH": res.append(n)
    return res


def place(lib, node, x, z, turn_deg, sx=1.0, s=1.0, y=0.0):
    root = libs.get(lib, {}).get(node)
    if root is None: return 0
    # as the race view: geometry in the node's own world placing, then scaled (sx along, s up and across), turned about
    # the vertical and moved to (x, y, z)
    M = Matrix.Translation(B(x, z, y)) @ Matrix.Rotation(math.radians(turn_deg), 4, "Z") @ Matrix.Diagonal((sx, s, s, 1.0))
    n = 0
    for m in meshes_under(root):
        o = bpy.data.objects.new(m.name + "_p", m.data)
        o.matrix_world = M @ m.matrix_world
        o.data.materials.clear(); o.data.materials.append(caster)
        o.visible_camera = False                     # casts shadows and bounces light, but the camera sees the ground under it
        out.objects.link(o); n += 1
    return n


xs, zs, npc = [], [], 0
for model, piece, x, z, turn, sx, s in SC["pieces"]:
    k = place(model, piece, x, z, turn, sx, s)
    if k: npc += 1; xs.append(x); zs.append(z)
if SC.get("finishLine") and "finish_line" in libs:
    place("finish_line", "finish_line", SC["finishLine"]["at"][0], SC["finishLine"]["at"][1], SC["finishLine"]["turn"])
# walls, hedges and copings: [x, z, length, depth, y from, y to, yaw]
nb = 0
for colour, lst in (SC.get("boxes") or {}).items():
    for x, z, L, D, y0, y1, yaw in lst:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        o = bpy.context.object
        o.scale = (L, D, y1 - y0); o.location = B(x, z, (y0 + y1) / 2); o.rotation_euler = (0, 0, yaw)
        o.data.materials.append(caster); o.visible_camera = False
        for c in list(o.users_collection): c.objects.unlink(o)
        out.objects.link(o); nb += 1
for c in list(bpy.data.collections):
    if c.name.startswith("lib_"): bpy.data.collections.remove(c)
print(f"{CID}: {npc} pieces placed, {nb} walls and hedges", flush=True)

# ---- the area to bake: round the pieces, rounded to whole pixels
x0, x1 = math.floor(min(xs) - PAD), math.ceil(max(xs) + PAD)
z0, z1 = math.floor(min(zs) - PAD), math.ceil(max(zs) + PAD)
wpx, hpx = int(round((x1 - x0) / MPP)), int(round((z1 - z0) / MPP))
x1, z1 = x0 + wpx * MPP, z0 + hpx * MPP
print(f"area x {x0}..{x1}, z {z0}..{z1}: {wpx} x {hpx} px", flush=True)

# ---- the white ground
me = bpy.data.meshes.new("ground")
me.from_pydata([B(x0 - 400, z0 - 400), B(x1 + 400, z0 - 400), B(x1 + 400, z1 + 400), B(x0 - 400, z1 + 400)], [], [(0, 1, 2, 3)])
me.materials.append(ground_mat)
scene.collection.objects.link(bpy.data.objects.new("ground", me))

# ---- the model look's light (as tools/blender/bake_static_world.py LOOK=model)
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); wl.new(tc.outputs["Generated"], sep.inputs[0])
ramp = wn.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
el[0].position, el[0].color = 0.0, (1.0, 0.86, 0.76, 1)
el[1].position, el[1].color = 0.5, (0.42, 0.56, 0.9, 1)
el.new(0.07).color = (0.86, 0.84, 0.95, 1)
wl.new(sep.outputs["Z"], ramp.inputs[0]); wl.new(ramp.outputs[0], wn["Background"].inputs["Color"])
wn["Background"].inputs["Strength"].default_value = 1.15
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 3.4; sun.data.angle = math.radians(24); sun.data.color = (1.0, 0.9, 0.8)
sd = LIGHT.get("sunDir") or VIEW.get("sun")
d = Vector((sd[0], -sd[2], sd[1])).normalized()                    # race-view axes -> Blender
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

# ---- straight down, orthographic, image top = north (race-view z0)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = max(x1 - x0, z1 - z0); cam.data.clip_end = 5000
cam.data.sensor_fit = "AUTO"
cam.location = B((x0 + x1) / 2, (z0 + z1) / 2, 900)
cam.rotation_euler = (0, 0, 0)                                    # looking down -Z, image up = Blender +Y = race-view -z
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = wpx, hpx
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True; scene.cycles.max_bounces = 3
scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0
st = scene.render.image_settings; st.media_type = "MULTI_LAYER_IMAGE"; st.file_format = "OPEN_EXR_MULTILAYER"; st.color_depth = "32"
exr = os.path.join("/tmp", f"{CID}-ground-light.exr")
scene.render.filepath = exr
bpy.ops.render.render(write_still=True)
print("rendered", exr, flush=True)

# ---- light relative to the open ground, per channel (shade comes out faintly lilac), into a jpg
import OpenEXR
from PIL import Image
f = OpenEXR.File(exr)
px = None
for p in f.parts:
    for name, ch in p.channels.items():
        if name.endswith("Combined") or name.endswith("Combined.RGBA") or name.endswith(".Combined"):
            px = np.asarray(ch.pixels, np.float32)
if px is None:
    p = f.parts[0]; px = np.asarray(next(iter(p.channels.values())).pixels, np.float32)
rgb = px[..., :3]
openv = np.percentile(rgb.reshape(-1, 3), 99.0, axis=0)                 # the open, sunlit ground
rel = np.clip(rgb / np.maximum(openv, 1e-6), 0, 1)
Image.fromarray((rel * 255 + 0.5).astype(np.uint8)).save(os.path.join(CDIR, f"{CID}-ground-light.jpg"), quality=90)
print("open ground", openv, "darkest", rel.min(axis=(0, 1)), flush=True)
VIEW["groundLight"] = {"map": f"{CID}-ground-light.jpg", "area": [x0, z0, x1, z1],
                       "note": "the ground's light from the buildings (tools/blender/bake_newmarket_ground.py): ground colour x map, "
                               "inside area [x0, z0, x1, z1] (image top = z0); 1 outside"}
json.dump(VIEW, open(os.path.join(CDIR, f"{CID}-view.json"), "w"), indent=1)
print("wrote", f"{CID}-ground-light.jpg", flush=True)
