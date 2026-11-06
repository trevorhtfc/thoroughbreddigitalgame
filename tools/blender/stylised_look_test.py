"""Stylised look test: render stills of the course in a soft, stylised 3D style.

    python -c "exec(open('tools/blender/stylised_look_test.py').read())" <out_dir> [samples]

(Run through exec: started as a plain script, Blender's Python module trips over its own
logging when the script folder is on the path.)

Not part of the game: a quick way to judge a style before building it for real.
- Trees: crowns of merged, rounded clumps with their normals bent outwards from the
  crown's centre, so each crown shades as one soft ball (the stylised look). Lit with
  a light underside and a gradient from dark base to sunlit top.
- Sky: a painted gradient with puffy clouds. Haze fades distance towards blue.
- Turf: soft lanes, no grid. Rails from course_props.glb.
- Horses: racehorse_rigged.glb, coats and silks tinted like the web viewer, with a
  softer finish (gentler normal map, rougher coat, a little sheen).
Blender coordinates: x = direction of running, z = up, y = across (+ = far side).
"""
import sys, math, random, os
import bpy, bmesh
from mathutils import Vector, Matrix

REPO = os.path.abspath(".")
OUT = sys.argv[-2] if len(sys.argv) > 2 and not sys.argv[-1].endswith(".py") else "renders"
for a in sys.argv[1:]:
    pass
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
OUT = ARGS[0] if ARGS else "renders"
SAMPLES = int(ARGS[1]) if len(ARGS) > 1 else 40
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
R = random.Random(4)


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


HAZE = srgb("#c9d6e2")


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def add_haze(m, nodes, links, start=70.0, scale=800.0, amount=0.55):
    """Fade towards the sky's haze with distance from the camera."""
    out = nodes["Material Output"]
    shader = out.inputs["Surface"].links[0].from_socket
    cam = nodes.new("ShaderNodeCameraData")
    sub = nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = start
    div = nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"; div.inputs[1].default_value = scale
    ex = nodes.new("ShaderNodeMath"); ex.operation = "EXPONENT"
    neg = nodes.new("ShaderNodeMath"); neg.operation = "MULTIPLY"; neg.inputs[1].default_value = -1
    one = nodes.new("ShaderNodeMath"); one.operation = "SUBTRACT"; one.inputs[0].default_value = 1
    amt = nodes.new("ShaderNodeMath"); amt.operation = "MULTIPLY"; amt.inputs[1].default_value = amount; amt.use_clamp = True
    links.new(cam.outputs["View Distance"], sub.inputs[0]); links.new(sub.outputs[0], div.inputs[0])
    links.new(div.outputs[0], neg.inputs[0]); links.new(neg.outputs[0], ex.inputs[0])
    links.new(ex.outputs[0], one.inputs[1]); links.new(one.outputs[0], amt.inputs[0])
    em = nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = HAZE; em.inputs["Strength"].default_value = 1.0
    mix = nodes.new("ShaderNodeMixShader")
    links.new(amt.outputs[0], mix.inputs[0]); links.new(shader, mix.inputs[1]); links.new(em.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])


def ramp(nodes, stops):
    r = nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], srgb(stops[0][1])
    el[1].position, el[1].color = stops[-1][0], srgb(stops[-1][1])
    for p, c in stops[1:-1]:
        e = el.new(p); e.color = srgb(c)
    return r


def obj_from_bm(name, bm, mat=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    if mat:
        me.materials.append(mat)
    return ob


def apply_mods(ob):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    for m in list(ob.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    ob.select_set(False)


# ---------------- World: painted sky ----------------
world = bpy.data.worlds.new("sky"); scene.world = world
world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord")
sep = wn.new("ShaderNodeSeparateXYZ")
wl.new(tc.outputs["Generated"], sep.inputs[0])
sky = ramp(wn, [(0.0, "#e4e6dc"), (0.04, "#b8d4ec"), (0.14, "#6faee6"), (0.45, "#3a86d6")])
wl.new(sep.outputs["Z"], sky.inputs[0])
bg = wn["Background"]
wl.new(sky.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.05

# Sun: warm, high afternoon, from the upper left behind the camera; soft-edged shadows.
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 5.0
sun.data.angle = math.radians(5)
sun.data.color = (1.0, 0.9, 0.76)
sun.rotation_euler = (math.radians(56), 0, math.radians(-118))

# ---------------- Ground ----------------
gm, gn, gl = new_mat("ground")
tco = gn.new("ShaderNodeTexCoord")
sxyz = gn.new("ShaderNodeSeparateXYZ"); gl.new(tco.outputs["Object"], sxyz.inputs[0])
# track mask: |y| < 15
absy = gn.new("ShaderNodeMath"); absy.operation = "ABSOLUTE"; gl.new(sxyz.outputs["Y"], absy.inputs[0])
trk = gn.new("ShaderNodeMath"); trk.operation = "LESS_THAN"; trk.inputs[1].default_value = 15.0; gl.new(absy.outputs[0], trk.inputs[0])
# soft lanes across the track
lanes = gn.new("ShaderNodeMath"); lanes.operation = "MULTIPLY"; lanes.inputs[1].default_value = math.pi * 8 / 30
gl.new(sxyz.outputs["Y"], lanes.inputs[0])
cosn = gn.new("ShaderNodeMath"); cosn.operation = "COSINE"; gl.new(lanes.outputs[0], cosn.inputs[0])
noise = gn.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 0.04; noise.inputs["Detail"].default_value = 3
gl.new(tco.outputs["Object"], noise.inputs["Vector"])
fine = gn.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 1.2; fine.inputs["Detail"].default_value = 2
gl.new(tco.outputs["Object"], fine.inputs["Vector"])
turf_r = ramp(gn, [(0.0, "#2f7a2c"), (0.5, "#4f9a38"), (1.0, "#74b448")])
grass_r = ramp(gn, [(0.0, "#4f8a32"), (0.5, "#76a442"), (1.0, "#b4bc5a")])
# turf value = 0.5 + lanes*0.12 + noise
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
# sandy paths at y = +46 and -44
def band(y0, w):
    d = gn.new("ShaderNodeMath"); d.operation = "SUBTRACT"; d.inputs[1].default_value = y0; gl.new(sxyz.outputs["Y"], d.inputs[0])
    a = gn.new("ShaderNodeMath"); a.operation = "ABSOLUTE"; gl.new(d.outputs[0], a.inputs[0])
    lt = gn.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = w / 2; gl.new(a.outputs[0], lt.inputs[0])
    return lt
pth = gn.new("ShaderNodeMath"); pth.operation = "MAXIMUM"
gl.new(band(46, 5).outputs[0], pth.inputs[0]); gl.new(band(-44, 7).outputs[0], pth.inputs[1])
mixp = gn.new("ShaderNodeMix"); mixp.data_type = "RGBA"; mixp.inputs[7].default_value = srgb("#d8c29a")
gl.new(pth.outputs[0], mixp.inputs[0]); gl.new(mixg.outputs[2], mixp.inputs[6])
# fine grain
grain = gn.new("ShaderNodeMix"); grain.data_type = "RGBA"; grain.blend_type = "OVERLAY"; grain.inputs[0].default_value = 0.18
gl.new(mixp.outputs[2], grain.inputs[6]); gl.new(fine.outputs["Color"], grain.inputs[7])
bsdf = gn["Principled BSDF"]
gl.new(grain.outputs[2], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = 0.95
bsdf.inputs["Specular IOR Level"].default_value = 0.2
add_haze(gm, gn, gl)
bpy.ops.mesh.primitive_plane_add(size=4000, location=(300, 0, 0))
ground = bpy.context.object; ground.data.materials.append(gm)

# ---------------- Trees ----------------
def tree_mat(name, seed):
    m, n, l = new_mat(name)
    tc = n.new("ShaderNodeTexCoord")
    sp = n.new("ShaderNodeSeparateXYZ"); l.new(tc.outputs["Object"], sp.inputs[0])
    mr = n.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 1.5; mr.inputs["From Max"].default_value = 11.5
    l.new(sp.outputs["Z"], mr.inputs["Value"])
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 2
    l.new(tc.outputs["Object"], nz.inputs["Vector"])
    add = n.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.35; add.inputs[2].default_value = -0.17
    l.new(nz.outputs["Fac"], add.inputs[0])
    tot = n.new("ShaderNodeMath"); tot.operation = "ADD"; tot.use_clamp = True
    l.new(mr.outputs[0], tot.inputs[0]); l.new(add.outputs[0], tot.inputs[1])
    rr = random.Random(seed)
    hue = [("#1c4a2a", "#3f8034", "#86bd4a", "#d6e07a"), ("#1d4834", "#367a48", "#74b25c", "#bfe08a"),
           ("#2a4a20", "#56862e", "#a2c048", "#e6dc72")][seed % 3]
    cr = ramp(n, [(0.0, hue[0]), (0.35, hue[1]), (0.75, hue[2]), (1.0, hue[3])])
    l.new(tot.outputs[0], cr.inputs[0])
    b = n["Principled BSDF"]
    l.new(cr.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Specular IOR Level"].default_value = 0.15
    b.inputs["Subsurface Weight"].default_value = 0.2
    b.inputs["Subsurface Radius"].default_value = (0.4, 0.8, 0.25)
    b.inputs["Subsurface Scale"].default_value = 0.4
    add_haze(m, n, l)
    return m


bark_m, bn, bl = new_mat("bark")
bn["Principled BSDF"].inputs["Base Color"].default_value = srgb("#6b5442")
bn["Principled BSDF"].inputs["Roughness"].default_value = 0.9
add_haze(bark_m, bn, bl)
TREE_MATS = [tree_mat("leaves%d" % i, i) for i in range(3)]


def cone(bm, p0, p1, r0, r1, segs=10):
    d = p1 - p0
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=d.length, matrix=m)


def make_tree(name, seed, kind="oak"):
    r = random.Random(seed)
    col = bpy.data.collections.new(name)
    if kind == "poplar":
        C, Rr, stretch = Vector((0, 0, 8.0)), 2.7, 2.4
    elif kind == "wide":
        C, Rr, stretch = Vector((0, 0, 6.2)), 5.4, 0.8
    elif kind == "bush":
        C, Rr, stretch = Vector((0, 0, 1.6)), 2.4, 0.75
    else:
        C, Rr, stretch = Vector((0, 0, 6.4)), 4.6, 0.95
    # Crown: merged rounded clumps.
    bm = bmesh.new()
    n = 16 if kind != "poplar" else 10
    clumps = [(C, Rr * 0.72)]
    for i in range(n):
        if kind == "poplar":
            t = i / (n - 1)
            p = C + Vector((r.uniform(-0.4, 0.4), r.uniform(-0.4, 0.4), (t - 0.5) * Rr * stretch * 1.4))
            rad = Rr * r.uniform(0.5, 0.7) * (1.1 - 0.5 * abs(t - 0.4))
        else:
            a, e = r.uniform(0, 6.28), r.uniform(-0.5, 1.0)
            p = C + Vector((math.cos(a) * math.cos(e) * Rr * 0.62, math.sin(a) * math.cos(e) * Rr * 0.62, math.sin(e) * Rr * 0.5 * stretch))
            rad = Rr * r.uniform(0.3, 0.48)
        clumps.append((p, rad))
    for p, rad in clumps:
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=rad, matrix=Matrix.Translation(p))
    crown = obj_from_bm(name + "_crown", bm, TREE_MATS[seed % 3])
    col.objects.link(crown)
    bpy.context.scene.collection.objects.link(crown)
    rm = crown.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = Rr * 0.05
    sm = crown.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.7; sm.iterations = 4
    # Leafy clumps: cells pushed out from the surface, then a little finer breakup.
    vt = bpy.data.textures.new(name + "_clumps", "VORONOI"); vt.noise_scale = Rr * 0.22; vt.distance_metric = "DISTANCE"
    dv = crown.modifiers.new("clumps", "DISPLACE"); dv.texture = vt; dv.strength = -Rr * 0.16; dv.mid_level = 0.6
    tex = bpy.data.textures.new(name + "_bump", "CLOUDS"); tex.noise_scale = Rr * 0.1
    dp = crown.modifiers.new("lumps", "DISPLACE"); dp.texture = tex; dp.strength = Rr * 0.05; dp.mid_level = 0.5
    dc = crown.modifiers.new("dec", "DECIMATE"); dc.ratio = 0.6
    apply_mods(crown)
    bpy.context.scene.collection.objects.unlink(crown)
    me = crown.data
    for p in me.polygons:
        p.use_smooth = True
    # Bend normals outwards from the crown's centre: each crown shades as one soft ball.
    centre = C - Vector((0, 0, Rr * 0.25))
    nrm = []
    for v in me.vertices:
        s = (v.co - centre); s.z /= max(0.6, stretch); s.normalize()
        k = (v.normal * 0.5 + s * 0.5); k.normalize()
        nrm.append(k)
    me.normals_split_custom_set_from_vertices(nrm)
    if kind == "bush":
        return col
    # Trunk and limbs reaching into the crown.
    bm = bmesh.new()
    base = Vector((0, 0, 0)); top = C - Vector((0, 0, Rr * 0.15))
    cone(bm, base, top, 0.42 if kind != "poplar" else 0.3, 0.2)
    for i in range(4 if kind != "poplar" else 2):
        a = r.uniform(0, 6.28)
        p0 = Vector((0, 0, C.z - Rr * r.uniform(0.35, 0.6)))
        p1 = p0 + Vector((math.cos(a) * Rr * 0.5, math.sin(a) * Rr * 0.5, Rr * 0.55))
        cone(bm, p0, p1, 0.17, 0.06, 6)
    trunk = obj_from_bm(name + "_trunk", bm, bark_m)
    for p in trunk.data.polygons:
        p.use_smooth = True
    col.objects.link(trunk)
    return col


VARIANTS = [make_tree("oak_a", 1), make_tree("oak_b", 2), make_tree("wide_a", 3, "wide"), make_tree("oak_c", 4),
            make_tree("poplar_a", 5, "poplar"), make_tree("wide_b", 6, "wide")]
BUSHES = [make_tree("bush_a", 7, "bush"), make_tree("bush_b", 8, "bush")]


def place_tree(x, y, s=1.0, rot=None, variant=None):
    e = bpy.data.objects.new("tree", None)
    e.instance_type = "COLLECTION"
    e.instance_collection = variant or R.choice(VARIANTS)
    e.location = (x, y, 0)
    e.rotation_euler = (0, 0, rot if rot is not None else R.uniform(0, 6.28))
    e.scale = (s, s, s * R.uniform(0.92, 1.1))
    scene.collection.objects.link(e)


# Near clumps along the far side, then a deep woodland band; a few on the near side.
x = -260
while x < 520:
    if R.random() > 0.3:
        for k in range(R.randint(1, 4)):
            place_tree(x + R.uniform(-9, 9), 72 + R.uniform(-6, 10), R.uniform(0.85, 1.25))
    x += R.uniform(30, 60)
for row in range(6):
    x = -320 + R.uniform(0, 12)
    while x < 620:
        place_tree(x, 112 + row * 18 + R.uniform(-8, 8), R.uniform(1.1, 1.6))
        x += R.uniform(7, 12)
x = -320
while x < 620:                                   # undergrowth along the woodland's edge
    place_tree(x, 104 + R.uniform(-4, 4), R.uniform(0.9, 1.5), variant=R.choice(BUSHES))
    x += R.uniform(9, 18)
x = -260
while x < 520:
    if R.random() > 0.45:
        for k in range(R.randint(1, 3)):
            place_tree(x + R.uniform(-8, 8), -70 - R.uniform(0, 12), R.uniform(0.85, 1.2))
    x += R.uniform(40, 70)

# ---------------- Clouds ----------------
cm, cn, cl = new_mat("cloud")
cb = cn["Principled BSDF"]
cb.inputs["Base Color"].default_value = srgb("#f4f2ec")
cb.inputs["Roughness"].default_value = 1.0
cb.inputs["Subsurface Weight"].default_value = 0.3
cb.inputs["Emission Color"].default_value = srgb("#9fb8d8"); cb.inputs["Emission Strength"].default_value = 0.25
for i in range(22):
    bm = bmesh.new()
    W = R.uniform(110, 240)
    for k in range(R.randint(5, 9)):
        rad = W * R.uniform(0.18, 0.32)
        p = Vector((R.uniform(-W / 2, W / 2), R.uniform(-W * 0.15, W * 0.15), rad * R.uniform(0.1, 0.7)))
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad, matrix=Matrix.Translation(p))
    c = obj_from_bm("cloud", bm, cm)
    scene.collection.objects.link(c)
    rm = c.modifiers.new("r", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = W * 0.04
    sm = c.modifiers.new("s", "SMOOTH"); sm.factor = 1.0; sm.iterations = 8
    apply_mods(c)
    bm = bmesh.new(); bm.from_mesh(c.data)          # flatten the underside
    for v in bm.verts:
        v.co.z = max(v.co.z, -W * 0.03)
    bm.to_mesh(c.data); bm.free()
    for p in c.data.polygons:
        p.use_smooth = True
    c.location = (R.uniform(-1400, 2000), R.uniform(2200, 3400), R.uniform(260, 620))
    c.scale.y = 0.6
    c.visible_shadow = False

# ---------------- Rails ----------------
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "assets/models/course/course_props.glb"))
rail = bpy.data.objects.get("rail_module")
for o in list(bpy.context.selected_objects):
    if o is not rail and o.name.split(".")[0] != "rail_module":
        bpy.data.objects.remove(o, do_unlink=True)
rail.location = (0, 0, 0)
for mat in rail.data.materials:
    add_haze(mat, mat.node_tree.nodes, mat.node_tree.links)
for side in (-1, 1):
    for i in range(260):
        o = rail.copy()
        o.location = (-200 + i * 3 + (3 if side > 0 else 0), side * 15.4, 0)
        o.rotation_euler = (0, 0, math.pi if side > 0 else 0)
        scene.collection.objects.link(o)
bpy.data.objects.remove(rail, do_unlink=True)

# ---------------- Horses ----------------
bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "assets/models/racehorse_rigged.glb"))
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == arm)
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.name.startswith("Icosphere"):
        bpy.data.objects.remove(o, do_unlink=True)
gallop = bpy.data.actions["gallop"]
arm.animation_data.action = gallop
f0, f1 = gallop.frame_range
mask = bpy.data.images.load(os.path.join(REPO, "race-view/assets/tint-mask.png")); mask.colorspace_settings.name = "Non-Color"
src_coat = next(m for m in body.data.materials if m.name != "silks")
src_silk = next(m for m in body.data.materials if m.name == "silks")

COATS = ["#7a4a2a", "#4a2e1c", "#a3552c", "#2b2523", "#a8a6a0"]
POINTS = ["#1d1714", "#17110d", "#6a3317", "#141110", "#6d6b66"]
SILKS = ["#c8322a", "#2448a8", "#e0b52a", "#1f7a4a", "#7a2a8a", "#e07a2a", "#f0f0f0", "#202838"]


def coat_material(i):
    m = src_coat.copy(); m.name = "coat%d" % i
    n, l = m.node_tree.nodes, m.node_tree.links
    b = next(x for x in n if x.type == "BSDF_PRINCIPLED")
    tex = next(x for x in n if x.type == "TEX_IMAGE" and "basecolor" in x.image.name)
    nm = next((x for x in n if x.type == "NORMAL_MAP"), None)
    if nm: nm.inputs["Strength"].default_value = 0.35       # softer: fewer fine bumps
    mt = n.new("ShaderNodeTexImage"); mt.image = mask
    l.new(tex.inputs["Vector"].links[0].from_socket if tex.inputs["Vector"].links else n.new("ShaderNodeUVMap").outputs[0], mt.inputs["Vector"])
    sp = n.new("ShaderNodeSeparateColor"); l.new(mt.outputs["Color"], sp.inputs[0])
    bw = n.new("ShaderNodeRGBToBW"); l.new(tex.outputs["Color"], bw.inputs[0])
    def tinted(hexc, k, lo):
        mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"; mul.inputs[1].default_value = k; mul.inputs[2].default_value = lo; mul.use_clamp = False
        l.new(bw.outputs[0], mul.inputs[0])
        mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1
        mx.inputs[6].default_value = srgb(hexc)
        l.new(mul.outputs[0], mx.inputs[7])
        return mx.outputs[2]
    coat = tinted(COATS[i % 5], 1.1, 0.4)
    pts = tinted(POINTS[i % 5], 1.0, 0.8)
    silk = tinted(SILKS[i % len(SILKS)], 0.8, 0.45)
    m1 = n.new("ShaderNodeMix"); m1.data_type = "RGBA"; l.new(sp.outputs["Red"], m1.inputs[0]); l.new(bw.outputs[0], m1.inputs[6]); l.new(coat, m1.inputs[7])
    m2 = n.new("ShaderNodeMix"); m2.data_type = "RGBA"; l.new(sp.outputs["Green"], m2.inputs[0]); l.new(m1.outputs[2], m2.inputs[6]); l.new(pts, m2.inputs[7])
    m3 = n.new("ShaderNodeMix"); m3.data_type = "RGBA"; l.new(sp.outputs["Blue"], m3.inputs[0]); l.new(m2.outputs[2], m3.inputs[6]); l.new(silk, m3.inputs[7])
    l.new(m3.outputs[2], b.inputs["Base Color"])
    for s in [s for s in b.inputs["Roughness"].links]:
        l.remove(s)
    b.inputs["Roughness"].default_value = 0.62
    b.inputs["Sheen Weight"].default_value = 0.25                 # soft rim on the coat
    b.inputs["Sheen Tint"].default_value = (1.0, 0.95, 0.85, 1)
    add_haze(m, n, l)
    return m


SILK_FILES = sorted(f for f in os.listdir(os.path.join(REPO, "race-view/assets/silks-3d")) if not f.startswith("catalogue"))
R2 = random.Random(9)
def silk_material(i):
    m = src_silk.copy(); m.name = "silks%d" % i
    t = next(x for x in m.node_tree.nodes if x.type == "TEX_IMAGE")
    t.image = bpy.data.images.load(os.path.join(REPO, "race-view/assets/silks-3d", SILK_FILES[(i * 7 + 3) % len(SILK_FILES)]))
    b = next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Sheen Weight"].default_value = 0.3
    return m
FIELD = [(24, -6.5), (20, 2.0), (17.5, -2.5), (14, 6.0), (12.5, -9.0), (10, 0.5), (7, 4.5), (5, -5.0), (2, 9.0), (0, -1.5)]
horses = []
for i, (hx, hy) in enumerate(FIELD):
    a = arm.copy(); a.animation_data_clear()
    b = body.copy(); b.parent = a
    for md in b.modifiers:
        if md.type == "ARMATURE": md.object = a
    scene.collection.objects.link(a); scene.collection.objects.link(b)
    for slot in b.material_slots:
        is_silk = slot.material and slot.material.name.startswith("silks")
        slot.link = "OBJECT"; slot.material = silk_material(i) if is_silk else coat_material(i)
    a.location = (hx, hy, 0); a.scale = (3, 3, 3) if a.scale.x < 2 else a.scale
    horses.append(a)
# Pose each horse at a different point of its stride.
for i, a in enumerate(horses):
    scene.frame_set(int(f0 + (i * 0.37 % 1.0) * (f1 - f0)))
    for pb in a.pose.bones:
        pb.matrix_basis = arm.pose.bones[pb.name].matrix_basis.copy()
for o in (arm, body):
    o.hide_render = True
scene.frame_set(int(f0))

# ---------------- Render ----------------
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
scene.view_settings.view_transform = "AgX"
try:
    scene.view_settings.look = "AgX - Punchy"
except TypeError:
    pass
scene.view_settings.exposure = 0.35
scene.render.film_transparent = False


def shot(name, loc, look, lens):
    cam = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 5000
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath, flush=True)


SHOTS = {
    "tv": ((4, -38, 4.5), (15, 8, 4.2), 50),
    "front": ((40, -19, 2.3), (14, 6, 4.0), 42),
}
only = os.environ.get("SHOT")
for k, v in SHOTS.items():
    if not only or only == k:
        shot(k, *v)
