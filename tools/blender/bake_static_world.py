"""Bake Blender's lighting into everything that doesn't move, for the real-time race views.

    python -c "exec(open('tools/blender/bake_static_world.py').read())" [samples]

Sets the scene up exactly as the stylised stills light it (same sun, same painted sky, same grass and
turf colours) on the full course (courses/ascot.json, world axes: x east, z south, y up), places the
main stand (its light distant version, assets/models/architecture/ascot_main_stand_far.glb), the site
components (courses/ascot-site-dressing.json) and the finish line, with the planting belts' hedge and
trees standing by to cast their shadows, then lets Cycles work out the soft light, bounce light and shadows once:

  assets/models/baked/static_world.glb   the stand, finish line and ground in world axes, and the site kit:
                                          one mesh per site piece and facing (kit_<piece>_q<0..3>, in the
                                          piece's own axes, as site_props.glb), each with a lightmap UV
  assets/models/baked/*_light.jpg        light on the stand, site kit and finish line (light only;
                                          the engine multiplies it by each material's colour)

The site pieces are not baked where they stand. Each piece type is baked once for each way it faces
(its turn rounded to a quarter turn), standing alone on open grass under the same sun and sky, and the
viewer draws every copy from that one mesh (instancing): the download and memory no longer grow with
the number of copies. Copies keep their soft shadows on the ground, which still bakes with every copy in place.
  assets/models/baked/ground.jpg         the ground's own colour and light together round the home
                                          straight's last 2 furlongs (turf, lanes, grass, paths and the
                                          soft shadows the buildings and trees cast on them)
  assets/models/baked/bake.json          how bright each image is (values were divided by `scale`),
                                          the baked ground's area and the plain grass and turf colours
                                          to carry on beyond it

A viewer draws these unlit: colour x light x scale, then the same AgX colour handling as Blender.
"""
import sys, os, json, math
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from PIL import Image, ImageFilter, ImageDraw

REPO = os.path.abspath(".")
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SAMPLES = int(ARGS[0]) if ARGS else 32
OUT = os.path.join(REPO, "assets/models/baked")
os.makedirs(OUT, exist_ok=True)
COURSE = json.load(open(os.path.join(REPO, "courses/ascot.json")))
VIEW = json.load(open(os.path.join(REPO, "courses/ascot-view.json")))
DRESS = json.load(open(os.path.join(REPO, "courses/ascot-site-dressing.json")))
W = COURSE["trackWidth"]
RAIL_GAP = COURSE["rails"]["gap"]
FRONT = COURSE["grandstand"]["frontLine"]
# Ground area to bake (world x, z): the last 2 furlongs and the post, both sides of the track.
GROUND = {"x0": -260.0, "x1": 700.0, "z0": -150.0, "z1": 140.0, "w": 5120, "h": 1548}
SMOKE = bool(os.environ.get("SMOKE"))          # SMOKE=1: tiny images, 1 sample, to check the script runs end to end
if SMOKE:
    SAMPLES = 1; GROUND.update(w=640, h=194)
    OUT = os.path.join(REPO, "assets/models/baked_smoke"); os.makedirs(OUT, exist_ok=True)
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
def ground_mask():
    """Track (red), paths (green) and the soft lanes (blue: tools/course/build_lane_field.py, the same
    stripes the race view draws on the turf beyond the baked ground) over the ground area."""
    g = GROUND
    sx, sz = g["w"] / (g["x1"] - g["x0"]), g["h"] / (g["z1"] - g["z0"])
    px = lambda x, z: ((x - g["x0"]) * sx, (z - g["z0"]) * sz)       # image row 0 = the north edge (z0)
    im = Image.new("RGB", (g["w"], g["h"]))
    d = ImageDraw.Draw(im)
    rings = COURSE["track"]["surface"]
    d.polygon([px(*p) for p in rings[0]], fill=(255, 0, 0))
    for hole in rings[1:]:
        d.polygon([px(*p) for p in hole], fill=(0, 0, 0))
    for p in VIEW.get("paths", []):
        (ax, az), (bx, bz) = p["from"], p["to"]
        d.line([px(ax, az), px(bx, bz)], fill=(0, 255, 0), width=max(1, int(p["width"] * sz)))
    import importlib.util
    spec = importlib.util.spec_from_file_location("lane_field", os.path.join(REPO, "tools/course/build_lane_field.py"))
    lf = importlib.util.module_from_spec(spec); spec.loader.exec_module(lf)
    L = VIEW["lanes"]
    dist = lf.distance_field(g["x0"], g["z0"], g["x1"], g["z1"], None, (g["w"], g["h"]))   # row 0 = north
    lanes = lf.lanes_value(dist, L["lanes"], L["width"])
    rgb = np.array(im)
    rgb[..., 2] = (lanes * 255 + 0.5).astype(np.uint8)
    im = Image.fromarray(rgb, "RGB")
    path = os.path.join(OUT, "_ground_mask.png")
    im.filter(ImageFilter.GaussianBlur(1.2)).save(path)
    return path


def ground_material():
    gm = bpy.data.materials.new("bake_ground"); gm.use_nodes = True
    gn, gl = gm.node_tree.nodes, gm.node_tree.links
    tco = gn.new("ShaderNodeTexCoord")
    sxyz = gn.new("ShaderNodeSeparateXYZ"); gl.new(tco.outputs["Object"], sxyz.inputs[0])
    mask = gn.new("ShaderNodeTexImage"); mask.image = bpy.data.images.load(ground_mask()); mask.image.colorspace_settings.name = "Non-Color"
    mask.interpolation = "Linear"; mask.extension = "EXTEND"
    uvn = gn.new("ShaderNodeUVMap"); uvn.uv_map = "lightmap"; gl.new(uvn.outputs["UV"], mask.inputs["Vector"])
    msep = gn.new("ShaderNodeSeparateColor"); gl.new(mask.outputs["Color"], msep.inputs[0])
    # soft lanes along the running line, round the bends too: the mask's blue channel holds
    # 0.5 + 0.5 cos(pi * 8 * d / 30), d = metres from the turf's edge; back to -1..1 here
    cosn = gn.new("ShaderNodeMath"); cosn.operation = "MULTIPLY_ADD"; cosn.inputs[1].default_value = 2.0; cosn.inputs[2].default_value = -1.0
    gl.new(msep.outputs[2], cosn.inputs[0])
    noise = gn.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 0.04; noise.inputs["Detail"].default_value = 3
    gl.new(tco.outputs["Object"], noise.inputs["Vector"])
    turf_r = ramp(gn, [(0.0, "#2f7a2c"), (0.5, "#4f9a38"), (1.0, "#74b448")])
    grass_r = ramp(gn, [(0.0, "#4f8a32"), (0.5, "#76a442"), (1.0, "#b4bc5a")])
    tv = gn.new("ShaderNodeMath"); tv.operation = "MULTIPLY_ADD"; tv.inputs[1].default_value = 0.17; tv.inputs[2].default_value = 0.5
    gl.new(cosn.outputs[0], tv.inputs[0])
    tv2 = gn.new("ShaderNodeMath"); tv2.operation = "ADD"; gl.new(tv.outputs[0], tv2.inputs[0])
    nb = gn.new("ShaderNodeMath"); nb.operation = "MULTIPLY_ADD"; nb.inputs[1].default_value = 0.5; nb.inputs[2].default_value = -0.25
    gl.new(noise.outputs["Fac"], nb.inputs[0]); gl.new(nb.outputs[0], tv2.inputs[1])
    gl.new(tv2.outputs[0], turf_r.inputs[0])
    gv = gn.new("ShaderNodeMath"); gv.operation = "MULTIPLY_ADD"; gv.inputs[1].default_value = 0.6; gv.inputs[2].default_value = 0.0
    gl.new(noise.outputs["Fac"], gv.inputs[0]); gl.new(gv.outputs[0], grass_r.inputs[0])
    mixg = gn.new("ShaderNodeMix"); mixg.data_type = "RGBA"
    gl.new(msep.outputs[0], mixg.inputs[0]); gl.new(grass_r.outputs[0], mixg.inputs[6]); gl.new(turf_r.outputs[0], mixg.inputs[7])
    mixp = gn.new("ShaderNodeMix"); mixp.data_type = "RGBA"; mixp.inputs[7].default_value = srgb("#d8c29a")
    gl.new(msep.outputs[1], mixp.inputs[0]); gl.new(mixg.outputs[2], mixp.inputs[6])
    b = gn["Principled BSDF"]
    gl.new(mixp.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    b.inputs["Specular IOR Level"].default_value = 0.2
    return gm


me = bpy.data.meshes.new("ground")
bm = bmesh.new()
g = GROUND
y0, y1 = -g["z1"], -g["z0"]                                    # Blender y = -world z
vs = [bm.verts.new((x, y, 0)) for x, y in ((g["x0"], y0), (g["x1"], y0), (g["x1"], y1), (g["x0"], y1))]
f = bm.faces.new(vs)
uv = bm.loops.layers.uv.new("lightmap")
for loop in f.loops:
    co = loop.vert.co
    # v = 0 at the south edge (image bottom), 1 at the north edge (image top): the mask's row 0 is north
    loop[uv].uv = ((co.x - g["x0"]) / (g["x1"] - g["x0"]), (co.y - y0) / (y1 - y0))
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
stand_parts = import_glb(os.path.join(arch, "ascot_main_stand_far.glb"))
for o in stand_parts:                                          # built in world axes: origin at the clock tower
    o.parent = None
    o.matrix_world = Matrix.Translation((0, -FRONT, 0)) @ o.matrix_world
stand = join(stand_parts, "stand")

lib = {o.name.split(".")[0]: o for o in import_glb(os.path.join(arch, "site_props.glb"))}
for o in lib.values():
    o.parent = None
quarter = lambda turn: int(round(turn / 90.0)) % 4
# every copy in place, only to cast its shadow on the ground (and on its neighbours' ground)
copies = []
for p in DRESS["pieces"]:
    o = lib[p["piece"]].copy()
    scene.collection.objects.link(o)
    o.matrix_world = Matrix.Translation((p["x"], -p["z"], 0)) @ Matrix.Rotation(math.pi + math.radians(p.get("turn", 0)), 4, "Z")
    copies.append(o)
site_shadow = join(copies, "site_shadow")
# the kit: one copy of each piece for each quarter turn it is used at, in a row on open grass far from the course
VARIANTS = sorted({(p["piece"], quarter(p.get("turn", 0))) for p in DRESS["pieces"]})
STUDIO = (4000.0, 4000.0, 70.0)                                # Blender x, y of the first spot; spacing
studio_at = {}
vcopies = []
for i, (piece, q) in enumerate(VARIANTS):
    o = lib[piece].copy(); o.data = lib[piece].data.copy()
    scene.collection.objects.link(o)
    M = Matrix.Translation((STUDIO[0] + (i % 8) * STUDIO[2], STUDIO[1] + (i // 8) * STUDIO[2], 0)) @ Matrix.Rotation(math.pi + q * math.pi / 2, 4, "Z")
    o.matrix_world = M
    studio_at[i] = M
    a = o.data.attributes.new("variant", "INT", "FACE")
    a.data.foreach_set("value", [i] * len(o.data.polygons))
    vcopies.append(o)
for o in lib.values():
    bpy.data.objects.remove(o, do_unlink=True)
site = join(vcopies, "site_kit")
# open grass under the studio row, for the bounce light and the shadow at each piece's foot
sme = bpy.data.meshes.new("studio_ground")
sbm = bmesh.new()
sx1, sy1 = STUDIO[0] + 8 * STUDIO[2], STUDIO[1] + (len(VARIANTS) // 8 + 1) * STUDIO[2]
sbm.faces.new([sbm.verts.new(c) for c in ((STUDIO[0] - 200, STUDIO[1] - 200, 0), (sx1 + 200, STUDIO[1] - 200, 0), (sx1 + 200, sy1 + 200, 0), (STUDIO[0] - 200, sy1 + 200, 0))])
sbm.to_mesh(sme); sbm.free()
sgm = bpy.data.materials.new("studio_grass"); sgm.use_nodes = True
sgm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb("#76a442")
sgm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
sme.materials.append(sgm)
scene.collection.objects.link(bpy.data.objects.new("studio_ground", sme))
print("site kit: %d pieces x facings for %d copies" % (len(VARIANTS), len(DRESS["pieces"])), flush=True)

# the finish line stands on the far (inside) rail, its post on the rail line and red loop on the winning line,
# facing the stands (it was modelled for the far side: front facing the track)
fparts = import_glb(os.path.join(arch, "finish_line.glb"))
for o in fparts:
    o.parent = None
    o.matrix_world = Matrix.Translation((0, RAIL_GAP, 0)) @ o.matrix_world
finish = join(fparts, "finish")

# the planting belts' hedge and the trees behind it only cast their shadows on the ground here; the
# viewer lights them live. Only the trees over the baked ground are brought in.
for o in import_glb(os.path.join(REPO, "assets/models/course/planting_belts.glb")):
    if o.name.split(".")[0] != "planting_hedge":
        bpy.data.objects.remove(o, do_unlink=True)
PLANT = json.load(open(os.path.join(REPO, "courses/ascot-planting.json")))
tlib = {o.name.split(".")[0]: o for o in import_glb(os.path.join(REPO, "assets/models/trees/trees.glb"))}
for o in tlib.values():
    o.parent = None
for x, z, tree, sc, turn in PLANT["trees"]:
    if not (GROUND["x0"] - 30 < x < GROUND["x1"] + 30 and GROUND["z0"] - 30 < z < GROUND["z1"] + 30):
        continue
    for part in ("_crown", "_trunk"):
        src = tlib.get(tree + part)
        if src:
            o = src.copy(); scene.collection.objects.link(o)
            o.matrix_world = Matrix.Translation((x, -z, 0)) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Diagonal((sc, sc, sc, 1))
for o in tlib.values():
    bpy.data.objects.remove(o, do_unlink=True)


# ---------------- lightmap UVs ----------------
def lightmap_uv(o, margin=0.0012):
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
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=margin, shape_method="AABB")
    bpy.ops.object.mode_set(mode="OBJECT")


for o, margin in ((stand, 0.0012), (site, 0.0012), (finish, 0.0012)):   # bigger margins collapse the islands (thousands of them)
    lightmap_uv(o, margin)
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


INFO = {"_about": "Baked light for the static world (tools/blender/bake_static_world.py), world axes as courses/ascot.json. Each image stores value / scale, sRGB-encoded. Viewer: colour = material colour x light x scale (light maps), or image x scale (ground; its area is in world x, z, image top = north). 'outside' and 'turf' are the plain grass and turf colours (linear) to carry on beyond the baked ground.",
        "glb": "static_world.glb"}
for o, name, size in ((finish, "finish", 2048), (site, "site", 2048), (stand, "stand", 3072)):
    import time; t0 = time.time()
    px = bake(o, name, size // 8 if SMOKE else size, size // 8 if SMOKE else size, "light")
    lum = px[..., :3].max(axis=2)[px[..., 3] > 0.5]
    scale = float(np.percentile(lum, 99.5)) * 1.05 if lum.size else 1.0
    encode(px, os.path.join(OUT, name + "_light.jpg"), scale, jpeg=True, blur=0)
    INFO[name] = {"mesh": o.name, "lightMap": name + "_light.jpg", "scale": round(scale, 4)}
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
    m = (np.array(Image.open(os.path.join(OUT, "_ground_mask.png")).resize((GROUND["w"], GROUND["h"]))))
    # px is top row first = north; the mask's row 0 is north as well
    turf = px[..., :3][m[..., 0] > 200]
    grass = px[..., :3][(m[..., 0] < 20) & (m[..., 1] < 20)]
    INFO["ground"] = {"mesh": "ground", "map": "ground.jpg", "scale": round(scale, 4),
                      "area": {k: GROUND[k] for k in ("x0", "x1", "z0", "z1")},
                      "outside": [round(float(c), 4) for c in np.median(grass[::50], axis=0)],
                      "turf": [round(float(c), 4) for c in np.median(turf[::20], axis=0)]}
    print("baked ground in %.0fs, scale %.3f" % (time.time() - t0, scale), flush=True)

# ---------------- the site kit back into one mesh per piece and facing, in the piece's own axes ----------------
kit_objs = []
vals = np.empty(len(site.data.polygons), dtype=np.int32)
site.data.attributes["variant"].data.foreach_get("value", vals)
for i, (piece, q) in enumerate(VARIANTS):
    me = site.data.copy()
    bm = bmesh.new(); bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f, v in zip(bm.faces, vals) if v != i], context="FACES")
    bmesh.ops.transform(bm, matrix=studio_at[i].inverted(), verts=bm.verts)
    bm.to_mesh(me); bm.free()
    me.attributes.remove(me.attributes["variant"])
    nm = "kit_%s_q%d" % (piece, q)
    ob = bpy.data.objects.new(nm, me); me.name = nm
    scene.collection.objects.link(ob)
    # drop material slots this piece doesn't use, so the viewer gets no empty parts
    used = {p.material_index for p in me.polygons}
    for k in sorted(range(len(me.materials)), reverse=True):
        if k not in used:
            me.materials.pop(index=k)                     # shifts the faces' material indices down
    kit_objs.append(ob)
INFO["site"]["mesh"] = None
INFO["site"]["kit"] = {"%s_q%d" % v: "kit_%s_q%d" % v for v in VARIANTS}
INFO["site"]["note"] = ("Instanced: one mesh per piece and quarter turn, in the piece's own axes. Place each copy in "
                        "courses/ascot-site-dressing.json with kit_<piece>_q<round(turn/90) mod 4> at (x, 0, z), turned "
                        "180 + turn degrees about y, as site_props.glb.")

# ---------------- export: meshes with their lightmap UVs ----------------
bpy.ops.object.select_all(action="DESELECT")
for o in (stand, finish, ground, *kit_objs):
    o.select_set(True)
    for m in o.data.materials:                       # drop the bake image nodes again
        for n in [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"]:
            m.node_tree.nodes.remove(n)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "static_world.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_texcoords=True, export_normals=True, export_apply=False, export_animations=False)
json.dump(INFO, open(os.path.join(OUT, "bake.json"), "w"), indent=1)
os.remove(os.path.join(OUT, "_ground_mask.png"))
print("exported static_world.glb", flush=True)
