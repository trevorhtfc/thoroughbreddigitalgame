"""Bake Blender's lighting into everything that doesn't move, for the real-time race views.

    python -c "exec(open('tools/blender/bake_static_world.py').read())" [samples]

Sets the scene up exactly as the stylised stills light it (same sun, same painted sky, same grass and
turf colours), places the grandstand, the site components (courses/ascot-site-dressing.json) and the
finish line on the course (courses/ascot-home-straight.json), then lets Cycles work out the soft
light, bounce light and shadows on them once, and stores the result:

  assets/models/baked/static_world.glb   four meshes in course coordinates (glTF: x along the running,
                                          y up, z across, + towards the stands), each with a lightmap UV
  assets/models/baked/*_light.png        light on the stand, site pieces and finish line (light only;
                                          the engine multiplies it by each material's colour)
  assets/models/baked/ground.jpg         the ground's own colour and light together (turf, lanes, grass,
                                          paths and the soft shadows the buildings cast on them)
  assets/models/baked/bake.json          how bright each image is (values were divided by `scale`)

A viewer draws these unlit: colour x light x scale, then the same AgX colour handling as Blender.
"""
import sys, os, json, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from PIL import Image, ImageFilter

REPO = os.path.abspath(".")
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SAMPLES = int(ARGS[0]) if ARGS else 48
OUT = os.path.join(REPO, "assets/models/baked")
os.makedirs(OUT, exist_ok=True)
COURSE = json.load(open(os.path.join(REPO, "courses/ascot-home-straight.json")))
DRESS = json.load(open(os.path.join(REPO, "courses/ascot-site-dressing.json")))
GS = next(s for s in COURSE["structures"] if s["model"] == "victorian_grandstand")
WP = COURSE["winningPost"]
POST = WP["at"]
GX, GY = GS["x"], -GS["z"]                      # Blender y = -course z
RAIL = COURSE["track"]["width"] / 2 + COURSE["rails"]["gap"]
# Ground area to bake: the final furlong and a little either side, both enclosures.
GROUND = {"x0": POST - 420, "x1": POST + 260, "y0": -110.0, "y1": 150.0, "w": 4096, "h": 1536}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


def ramp(nodes, stops):
    r = nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], srgb(stops[0][1])
    el[1].position, el[1].color = stops[-1][0], srgb(stops[-1][1])
    for p, c in stops[1:-1]:
        e = el.new(p); e.color = srgb(c)
    return r


# ---------------- light: as in tools/blender/stylised_look_test.py ----------------
world = bpy.data.worlds.new("sky"); scene.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ")
wl.new(tc.outputs["Generated"], sep.inputs[0])
sky = ramp(wn, [(0.0, "#e4e6dc"), (0.04, "#b8d4ec"), (0.14, "#6faee6"), (0.45, "#3a86d6")])
wl.new(sep.outputs["Z"], sky.inputs[0])
wl.new(sky.outputs[0], wn["Background"].inputs["Color"]); wn["Background"].inputs["Strength"].default_value = 1.05
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 5.0; sun.data.angle = math.radians(5); sun.data.color = (1.0, 0.9, 0.76)
sun.rotation_euler = (math.radians(56), 0, math.radians(-118))

# ---------------- ground: the stills' turf, lanes, grass and paths ----------------
def ground_material():
    gm = bpy.data.materials.new("bake_ground"); gm.use_nodes = True
    gn, gl = gm.node_tree.nodes, gm.node_tree.links
    tco = gn.new("ShaderNodeTexCoord")
    sxyz = gn.new("ShaderNodeSeparateXYZ"); gl.new(tco.outputs["Object"], sxyz.inputs[0])
    absy = gn.new("ShaderNodeMath"); absy.operation = "ABSOLUTE"; gl.new(sxyz.outputs["Y"], absy.inputs[0])
    trk = gn.new("ShaderNodeMath"); trk.operation = "LESS_THAN"; trk.inputs[1].default_value = RAIL - 0.4; gl.new(absy.outputs[0], trk.inputs[0])
    lanes = gn.new("ShaderNodeMath"); lanes.operation = "MULTIPLY"; lanes.inputs[1].default_value = math.pi * 8 / 30
    gl.new(sxyz.outputs["Y"], lanes.inputs[0])
    cosn = gn.new("ShaderNodeMath"); cosn.operation = "COSINE"; gl.new(lanes.outputs[0], cosn.inputs[0])
    noise = gn.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 0.04; noise.inputs["Detail"].default_value = 3
    gl.new(tco.outputs["Object"], noise.inputs["Vector"])
    turf_r = ramp(gn, [(0.0, "#2f7a2c"), (0.5, "#4f9a38"), (1.0, "#74b448")])
    grass_r = ramp(gn, [(0.0, "#4f8a32"), (0.5, "#76a442"), (1.0, "#b4bc5a")])
    tv = gn.new("ShaderNodeMath"); tv.operation = "MULTIPLY_ADD"; tv.inputs[1].default_value = 0.13; tv.inputs[2].default_value = 0.5
    gl.new(cosn.outputs[0], tv.inputs[0])
    tv2 = gn.new("ShaderNodeMath"); tv2.operation = "ADD"; gl.new(tv.outputs[0], tv2.inputs[0])
    nb = gn.new("ShaderNodeMath"); nb.operation = "MULTIPLY_ADD"; nb.inputs[1].default_value = 0.5; nb.inputs[2].default_value = -0.25
    gl.new(noise.outputs["Fac"], nb.inputs[0]); gl.new(nb.outputs[0], tv2.inputs[1])
    gl.new(tv2.outputs[0], turf_r.inputs[0])
    gv = gn.new("ShaderNodeMath"); gv.operation = "MULTIPLY_ADD"; gv.inputs[1].default_value = 0.6; gv.inputs[2].default_value = 0.0
    gl.new(noise.outputs["Fac"], gv.inputs[0]); gl.new(gv.outputs[0], grass_r.inputs[0])
    mixg = gn.new("ShaderNodeMix"); mixg.data_type = "RGBA"
    gl.new(trk.outputs[0], mixg.inputs[0]); gl.new(grass_r.outputs[0], mixg.inputs[6]); gl.new(turf_r.outputs[0], mixg.inputs[7])
    pth = None
    for p in COURSE["paths"]:
        y0, w = -p["from"][1], p["width"]
        d = gn.new("ShaderNodeMath"); d.operation = "SUBTRACT"; d.inputs[1].default_value = y0; gl.new(sxyz.outputs["Y"], d.inputs[0])
        a = gn.new("ShaderNodeMath"); a.operation = "ABSOLUTE"; gl.new(d.outputs[0], a.inputs[0])
        lt = gn.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = w / 2; gl.new(a.outputs[0], lt.inputs[0])
        if pth is None:
            pth = lt
        else:
            mx = gn.new("ShaderNodeMath"); mx.operation = "MAXIMUM"; gl.new(pth.outputs[0], mx.inputs[0]); gl.new(lt.outputs[0], mx.inputs[1]); pth = mx
    mixp = gn.new("ShaderNodeMix"); mixp.data_type = "RGBA"; mixp.inputs[7].default_value = srgb("#d8c29a")
    gl.new(pth.outputs[0], mixp.inputs[0]); gl.new(mixg.outputs[2], mixp.inputs[6])
    b = gn["Principled BSDF"]
    gl.new(mixp.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    b.inputs["Specular IOR Level"].default_value = 0.2
    return gm


me = bpy.data.meshes.new("ground")
bm = bmesh.new()
g = GROUND
vs = [bm.verts.new((x, y, 0)) for x, y in ((g["x0"], g["y0"]), (g["x1"], g["y0"]), (g["x1"], g["y1"]), (g["x0"], g["y1"]))]
f = bm.faces.new(vs)
uv = bm.loops.layers.uv.new("lightmap")
for loop in f.loops:
    co = loop.vert.co
    loop[uv].uv = ((co.x - g["x0"]) / (g["x1"] - g["x0"]), (co.y - g["y0"]) / (g["y1"] - g["y0"]))
bm.to_mesh(me); bm.free()
ground = bpy.data.objects.new("ground", me)
scene.collection.objects.link(ground)
me.materials.append(ground_material())


# ---------------- place the static pieces ----------------
def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        if o.name not in scene.collection.objects and not o.users_collection:
            scene.collection.objects.link(o)
        o.select_set(True)
    act = objs[0]
    act.data = act.data.copy()
    bpy.context.view_layer.objects.active = act
    if len(objs) > 1:
        bpy.ops.object.join()
    act = bpy.context.view_layer.objects.active
    act.parent = None
    bpy.ops.object.select_all(action="DESELECT"); act.select_set(True)
    bpy.ops.object.make_single_user(object=True, obdata=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    act.name = act.data.name = name
    return act


arch = os.path.join(REPO, "assets/models/architecture")
stand_parts = import_glb(os.path.join(arch, "victorian_grandstand.glb"))
for o in stand_parts:
    o.parent = None
    o.matrix_world = Matrix.Translation((GX, GY, 0)) @ Matrix.Rotation(math.pi, 4, "Z") @ o.matrix_world
stand = join(stand_parts, "stand")

lib = {o.name.split(".")[0]: o for o in import_glb(os.path.join(arch, "site_props.glb"))}
copies = []
for p in DRESS["pieces"]:
    src = lib[p["piece"]]
    o = src.copy()
    scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation((GX + p["dx"], GY - p["dz"], 0)) @ Matrix.Rotation(math.pi + math.radians(p.get("turn", 0)), 4, "Z")
    copies.append(o)
for o in lib.values():
    bpy.data.objects.remove(o, do_unlink=True)
site = join(copies, "site")

fparts = import_glb(os.path.join(REPO, WP["file"]))
side = -1 if WP["side"] == "far" else 1                       # course z sign
for o in fparts:
    o.parent = None
    rot = Matrix.Identity(4) if WP["side"] == "far" else Matrix.Rotation(math.pi, 4, "Z")
    o.matrix_world = Matrix.Translation((POST, -side * RAIL, 0)) @ rot @ o.matrix_world
finish = join(fparts, "finish")
print("placed: stand %d, site %d, finish %d faces" % (len(stand.data.polygons), len(site.data.polygons), len(finish.data.polygons)), flush=True)


# ---------------- lightmap UVs ----------------
def lightmap_uv(o):
    for l in list(o.data.uv_layers):
        o.data.uv_layers.remove(l)
    o.data.uv_layers.new(name="lightmap")
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, scale_to_bounds=False)
    # Thousands of small islands (balusters, posts, frames): pack them tightly by their boxes so the
    # image is used well; a fixed margin of a few pixels keeps neighbours from bleeding into each other.
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=0.0012, shape_method="AABB")
    bpy.ops.object.mode_set(mode="OBJECT")


for o in (stand, site, finish):
    lightmap_uv(o)
print("lightmap UVs done", flush=True)

# ---------------- bake ----------------
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
scene.cycles.max_bounces = 4
scene.cycles.diffuse_bounces = 3
scene.render.bake.margin = 6
scene.render.bake.margin_type = "EXTEND"


def bake(o, name, w, h, kind):
    img = bpy.data.images.new(name, w, h, float_buffer=True, alpha=True)
    img.generated_color = (0, 0, 0, 0)
    for m in o.data.materials:
        n = m.node_tree.nodes
        t = n.new("ShaderNodeTexImage"); t.image = img
        for x in n:
            x.select = False
        t.select = True; n.active = t
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True)
    bpy.context.view_layer.objects.active = o
    passes = {"DIRECT", "INDIRECT"} | ({"COLOR"} if kind == "colour" else set())
    bpy.ops.object.bake(type="DIFFUSE", pass_filter=passes, margin=6, use_clear=True)
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)                              # free it before the next, larger bake
    px = np.flipud(px.reshape(h, w, 4))                     # top row first; matches glTF's flipped v
    return px


def encode(px, path, scale, jpeg=False, blur=1.0):
    v = np.clip(px[..., :3] / scale, 0, 1)
    v = np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1 / 2.4) - 0.055)   # sRGB
    im = Image.fromarray((v * 255 + 0.5).astype(np.uint8), "RGB")
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))    # smooths the last of the sampling noise
    if jpeg:
        im.save(path, quality=90, optimize=True)
    else:
        im.save(path, optimize=True)


INFO = {"_about": "Baked light for the static world (tools/blender/bake_static_world.py). Each image stores value / scale, sRGB-encoded. Viewer: colour = material colour x light x scale (light maps), or image x scale (ground).",
        "glb": "static_world.glb"}
for o, name, size in ((finish, "finish", 2048), (site, "site", 3072), (stand, "stand", 3072)):
    import time; t0 = time.time()
    px = bake(o, name, size, size, "light")
    lum = px[..., :3].max(axis=2)[px[..., 3] > 0.5]
    scale = float(np.percentile(lum, 99.5)) * 1.05 if lum.size else 1.0
    encode(px, os.path.join(OUT, name + "_light.png"), scale, blur=0)
    INFO[name] = {"mesh": name, "lightMap": name + "_light.png", "scale": round(scale, 4)}
    print("baked %s in %.0fs, scale %.3f" % (name, time.time() - t0, scale), flush=True)

t0 = time.time()
if os.environ.get("KEEP_GROUND") and os.path.exists(os.path.join(OUT, "bake.json")):
    INFO["ground"] = json.load(open(os.path.join(OUT, "bake.json")))["ground"]     # reuse the last ground bake
    px = None
else:
    px = bake(ground, "ground", GROUND["w"], GROUND["h"], "colour")
if px is not None:
    scale = float(np.percentile(px[..., :3].max(axis=2), 99.8)) * 1.05
    encode(px, os.path.join(OUT, "ground.jpg"), scale, jpeg=True, blur=0.6)
    far = px[:, :400, :3].reshape(-1, 3)
    INFO["ground"] = {"mesh": "ground", "map": "ground.jpg", "scale": round(scale, 4),
                      "area": {k: GROUND[k] for k in ("x0", "x1", "y0", "y1")},
                      "outside": [round(float(c), 4) for c in np.median(far, axis=0)]}
    print("baked ground in %.0fs, scale %.3f" % (time.time() - t0, scale), flush=True)

# ---------------- export: meshes with their lightmap UVs ----------------
bpy.ops.object.select_all(action="DESELECT")
for o in (stand, site, finish, ground):
    o.select_set(True)
    for m in o.data.materials:                       # drop the bake image nodes again
        for n in [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"]:
            m.node_tree.nodes.remove(n)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "static_world.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_texcoords=True, export_normals=True, export_apply=False, export_animations=False)
json.dump(INFO, open(os.path.join(OUT, "bake.json"), "w"), indent=1)
print("exported static_world.glb", flush=True)
