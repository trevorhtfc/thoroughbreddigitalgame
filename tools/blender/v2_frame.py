"""V2 style frame (11 Nov 2026): Ascot's stand, crowd and horses as they are modelled, art-directed like the owner's
precedents: real proportions and fine detail, one tight palette (warm ivory and salmon against teal and sage, straw
light), soft worked-out light, and ranks of trees fading into a pale mist.

    python -c "exec(open('tools/blender/v2_frame.py').read())"
    env: SAMPLES (48), RES (1600x900), CAM (hero), OUT (reference/architecture/v2-frames), HAZE (1)

It builds the scene with the finish study's own code (tools/blender/stand_clean_study.py, variant "model": the stand,
its awnings and flags, the crowd, the rails) and then replaces every colour, the ground, the light and the sky, plants
new trees, and puts the runners on the track. Each still is rendered twice: the picture, and how far every point is
from the camera, from which the mist is laid in (the same sum a game's distance haze does).
"""
import os, sys, math, json, random, time
T0 = time.time()
os.environ.setdefault("CROWD", "assets/models/architecture/crowd_set_12.glb")
os.environ["GRASS"] = "0"
_argv = sys.argv; sys.argv = ["v2", "model"]
_src = open("tools/blender/stand_clean_study.py").read()
exec(compile(_src[:_src.index('scene.render.engine = "CYCLES"')], "study", "exec"))
sys.argv = _argv
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

SAMPLES = int(os.environ.get("SAMPLES", "48"))
RES = tuple(int(v) for v in os.environ.get("RES", "1600x900").split("x"))
CAM = os.environ.get("CAM", "hero")
OUTDIR = os.environ.get("OUT", rp("reference/architecture/v2-frames")); os.makedirs(OUTDIR, exist_ok=True)
rnd = random.Random(7)

# ---------------- the palette: five families, nothing outside them
P = {
    "ivory": "#eadfc6", "ivory_deep": "#d8caa9", "white": "#f4eddc",
    "salmon": "#cf8068", "terracotta": "#b0604c", "bark": "#8a5b4e",
    "teal_deep": "#22403d", "teal": "#3f6e68", "teal_soft": "#7ea39b", "slate": "#5d7f79",
    "sage": "#8fb08a", "sage_pale": "#b9c99c", "sage_deep": "#5f8d78",
    "straw": "#dcc98a", "straw_pale": "#e3dab0", "char": "#2b3436",
}
FIRS = ["#4f8273", "#5f9482", "#6fa18a", "#86b08f", "#467565", "#7aa58c"]


def recolour(name, cols):
    """A study material's colour (or its list of colours, for the crowd's): whatever way it was built."""
    m = bpy.data.materials.get(name)
    if not m: print("no material", name); return
    nt = m.node_tree
    ramp = next((n for n in nt.nodes if n.type == "VALTORGB"), None)
    if ramp and isinstance(cols, list):
        els = ramp.color_ramp.elements
        while len(els) > len(cols): els.remove(els[-1])
        while len(els) < len(cols): els.new(0.5)
        for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
        return
    mix = next((n for n in nt.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY"), None)
    if mix: mix.inputs[6].default_value = lin(cols)
    else: nt.nodes["Principled BSDF"].inputs["Base Color"].default_value = lin(cols)


for name, col in {
    "s_wall": P["ivory"], "s_podium": P["ivory_deep"], "s_trim": P["white"], "s_steps": P["ivory_deep"],
    "s_roof": P["slate"], "s_iron": P["teal_deep"], "s_glass": "#1f3434", "s_door": P["teal"], "s_gilt": "#c9a868",
    "s_clock": P["white"], "s_clockd": P["char"],
    "a_blush": P["salmon"], "a_lilac": P["terracotta"], "a_butter": P["straw"], "a_sage": P["sage"], "a_powder": P["teal_soft"],
    "a_canvas": P["white"], "a_pole": P["white"], "rail": P["white"],
    # the crowd, in the scene's own colours: ivory, straw, salmon and teal; the morning coats charcoal and grey-teal
    "c_clothes": [P["ivory"], P["straw"], P["salmon"], P["teal"], P["sage"], P["terracotta"], P["white"], P["teal_soft"], P["straw_pale"], P["teal_deep"], "#c9a184", P["sage_pale"]],
    "c_hat": [P["white"], P["straw"], P["ivory"], P["salmon"], P["straw_pale"], P["teal_soft"]],
    "c_accent": [P["salmon"], P["teal"], P["straw"], P["white"], P["terracotta"]],
    "c_skin": ["#e9c2a2", "#dcae8c", "#c4916f", "#96684c"],
    "c_dark": [P["char"], "#3a3432", P["teal_deep"]],
    "c_tophat": [P["char"], "#55605f", "#7d8886", P["teal_deep"], "#333b3c", "#8f9895"],
    "c_tails": [P["char"], "#56615f", "#7f8a88", P["teal_deep"], "#3a4445", "#98a09c", "#2f3a3b"],
}.items():
    recolour(name, col)


# ---------------- the ground: sage turf mown in lanes, a paler lawn, straw beside the rail
def ground_mat(name, a, b=None, band=3.75, fleck=0.05):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = 0.97; bs.inputs["Specular IOR Level"].default_value = 0.08
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
    col = None
    if b:   # lanes along the course: alternate bands across it, soft-edged
        mth = nt.nodes.new("ShaderNodeMath"); mth.operation = "MULTIPLY"; mth.inputs[1].default_value = math.pi / band
        sn = nt.nodes.new("ShaderNodeMath"); sn.operation = "SINE"; mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = -0.25; mr.inputs["From Max"].default_value = 0.25
        nt.links.new(sep.outputs["Y"], mth.inputs[0]); nt.links.new(mth.outputs[0], sn.inputs[0]); nt.links.new(sn.outputs[0], mr.inputs["Value"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[6].default_value = lin(a); mx.inputs[7].default_value = lin(b)
        nt.links.new(mr.outputs["Result"], mx.inputs["Factor"]); col = mx.outputs[2]
    # broad, quiet unevenness and a fine fleck, so no big area is one flat colour
    n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.035; n1.inputs["Detail"].default_value = 3
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 2.2; n2.inputs["Detail"].default_value = 5
    nt.links.new(geo.outputs["Position"], n1.inputs["Vector"]); nt.links.new(geo.outputs["Position"], n2.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"; nt.links.new(n1.outputs["Fac"], add.inputs[0]); nt.links.new(n2.outputs["Fac"], add.inputs[1])
    mr2 = nt.nodes.new("ShaderNodeMapRange"); mr2.inputs["From Min"].default_value = 0.6; mr2.inputs["From Max"].default_value = 1.4
    mr2.inputs["To Min"].default_value = 1 - fleck; mr2.inputs["To Max"].default_value = 1 + fleck
    nt.links.new(add.outputs[0], mr2.inputs["Value"])
    mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1
    if col: nt.links.new(col, mul.inputs[6])
    else: mul.inputs[6].default_value = lin(a)
    cc = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"): nt.links.new(mr2.outputs["Result"], cc.inputs[k])
    nt.links.new(cc.outputs["Color"], mul.inputs[7]); nt.links.new(mul.outputs[2], bs.inputs["Base Color"])
    return no_green_bounce(m, "#b3ab8a")


TURF = ground_mat("v2_turf", "#88a873", "#96b47f")
LAWN = ground_mat("v2_lawn", "#bccb98")
STRAW = ground_mat("v2_straw", "#d9cfa6", fleck=0.035)
for o in list(bpy.data.objects):
    if o.type != "MESH": continue
    names = [s.material.name for s in o.material_slots if s.material]
    if any(n.startswith("turf_") for n in names):
        for i, s in enumerate(o.material_slots):
            if s.material and s.material.name.startswith("turf_track"): o.material_slots[i].material = TURF
            elif s.material and s.material.name.startswith("turf_lawn"): o.material_slots[i].material = LAWN
# a straw walk between the outer rail and the lawn (the track is y 0 .. -W; the stand's front at -FRONT)
plane("walk", -400, 700, -W - 6.5, -W - 0.2, STRAW, 0.02)
plane("far_verge", -400, 700, 0.2, 3.2, STRAW, 0.02)
# blades of grass standing in the turf where the cameras are close (the study's own blades, in this turf's colour)
if os.environ.get("BLADES", "1") != "0":
    grass_blades("v2_blades", -34, 30, -W + 0.1, -0.1, float(os.environ.get("BLADES", "1")) * 110, 0.05, "#9db886", lanes=True, seed=3)


# ---------------- light: a soft straw sun, a pale teal sky that fills the shade
wn, wl = world.node_tree.nodes, world.node_tree.links
for n in list(wn):
    if n.type not in ("BACKGROUND", "OUTPUT_WORLD"): wn.remove(n)
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], ramp.inputs[0])
els = ramp.color_ramp.elements
els[0].position = 0.0; els[0].color = lin("#f6f1cf"); els[1].position = 0.55; els[1].color = lin("#a6d2cb")
mid = els.new(0.12); mid.color = lin("#eaf0d2")
wl.new(ramp.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = float(os.environ.get("SKY", "0.7"))
sun.data.energy = float(os.environ.get("SUNPOW", "8.0")); sun.data.angle = math.radians(8); sun.data.color = (1.0, 0.9, 0.62)
d = Vector((float(v) for v in os.environ.get("SUN", "-0.3,0.85,0.5").split(","))).normalized()
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


# ---------------- trees: every face flat; a salmon trunk, crowns of soft-cornered lumps; tall firs in ranks
def flat_mat(name, cols, per_island=0.0, rough=0.95):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = rough; bs.inputs["Specular IOR Level"].default_value = 0.1
    oi = nt.nodes.new("ShaderNodeObjectInfo")
    if isinstance(cols, list):
        cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"; els = cr.color_ramp.elements
        while len(els) < len(cols): els.new(0.5)
        for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
        nt.links.new(oi.outputs["Random"], cr.inputs[0]); col = cr.outputs[0]
    else:
        rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = lin(cols); col = rgb.outputs[0]
    if per_island:   # each lump of a crown a shade lighter or darker than its neighbours
        geo = nt.nodes.new("ShaderNodeNewGeometry"); mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = 1 - per_island; mr.inputs["To Max"].default_value = 1 + per_island
        nt.links.new(geo.outputs["Random Per Island"], mr.inputs["Value"])
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs["Factor"].default_value = 1
        cc = nt.nodes.new("ShaderNodeCombineColor")
        for k in ("Red", "Green", "Blue"): nt.links.new(mr.outputs["Result"], cc.inputs[k])
        nt.links.new(col, mul.inputs[6]); nt.links.new(cc.outputs["Color"], mul.inputs[7]); col = mul.outputs[2]
    nt.links.new(col, bs.inputs["Base Color"])
    return m


FIR_MAT = flat_mat("v2_fir", FIRS + [P["salmon"]], per_island=0.07)
LEAF_MAT = flat_mat("v2_leaf", ["#86ab86", "#94b58c", "#7aa283", "#a3be90", "#8fb08a", "#c08a6e"], per_island=0.1)
BARK_MAT = flat_mat("v2_bark", P["bark"])


def mesh_from_bm(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    for p in me.polygons: p.use_smooth = False
    return me


def fir_mesh(seed):
    r = random.Random(seed); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.035, radius2=0.02, depth=0.3, matrix=Matrix.Translation((0, 0, 0.15)))
    for f in bm.faces: f.material_index = 1
    tiers = r.choice([6, 7, 8]); z = 0.16
    for i in range(tiers):
        k = i / (tiers - 1); rad = 0.2 * (1 - k) ** 0.8 + 0.035; h = 0.2 - 0.06 * k
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=9, radius1=rad, radius2=rad * 0.18, depth=h,
                                  matrix=Matrix.Translation((r.uniform(-0.006, 0.006), r.uniform(-0.006, 0.006), z + h / 2)) @ Matrix.Rotation(r.uniform(0, 6.28), 4, "Z"))
        z += h * 0.6
    scale = 1 / z
    for v in bm.verts: v.co *= scale
    return mesh_from_bm("fir%d" % seed, bm, [FIR_MAT, BARK_MAT])


def leafy_mesh(seed):
    r = random.Random(seed); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=0.045, radius2=0.03, depth=0.5, matrix=Matrix.Translation((0, 0, 0.25)))
    for f in bm.faces: f.material_index = 1
    lumps = [(0, 0, 0.72, 0.24)] + [(math.cos(a) * 0.22, math.sin(a) * 0.22, 0.52 + r.uniform(0, 0.24), r.uniform(0.14, 0.2)) for a in [i * 6.283 / 6 + r.uniform(-0.3, 0.3) for i in range(6)]]
    for (x, y, z, rad) in lumps:
        g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad, matrix=Matrix.Translation((x, y, z)) @ Matrix.Rotation(r.uniform(0, 6), 4, (r.random(), r.random(), 1)))
        for v in g["verts"]:
            v.co += Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * rad * 0.07
        # the branch that carries it
        a = Vector((0, 0, 0.44)); b = Vector((x * 0.8, y * 0.8, z - rad * 0.5)); dirv = (b - a)
        if dirv.length > 0.05:
            bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=0.018, radius2=0.012, depth=dirv.length,
                                  matrix=Matrix.Translation((a + b) / 2) @ dirv.to_track_quat("Z", "Y").to_matrix().to_4x4())
    for f in bm.faces:
        if f.material_index != 1 and len(f.verts) > 3: f.material_index = 1
    # branches (4-sided faces without caps) are bark; lumps are triangles
    for f in bm.faces: f.material_index = 1 if len(f.verts) != 3 else 0
    return mesh_from_bm("leafy%d" % seed, bm, [LEAF_MAT, BARK_MAT])


FIR_MESHES = [fir_mesh(s) for s in range(4)]
LEAFY_MESHES = [leafy_mesh(s) for s in range(4)]
tree_coll = bpy.data.collections.new("v2_trees"); scene.collection.children.link(tree_coll)


def plant(meshes, x, y, h, wide=1.0):
    o = bpy.data.objects.new("t", rnd.choice(meshes)); tree_coll.objects.link(o)
    o.location = (x, y, 0); o.scale = (h * wide, h * wide, h); o.rotation_euler = (0, 0, rnd.uniform(0, 6.28))


n_trees = 0
# ranks of firs behind the stand and beyond both its ends, taller with each rank back
for rank in range(11):
    y = -FRONT - 46 - rank * 13
    x = -520 - rank * 10
    while x < 620 + rank * 10:
        plant(FIR_MESHES, x + rnd.uniform(-3, 3), y + rnd.uniform(-5, 5), rnd.uniform(26, 40) + rank * 1.6, rnd.uniform(0.9, 1.25)); n_trees += 1
        x += rnd.uniform(7, 12)
# beyond the post, closing the end of the straight: firs across the whole picture, with leafy trees in front
for rank in range(12):
    x = -150 - rank * 14
    y = 150
    while y > -FRONT - 60:
        if not (-W - 4 < y < 4 and rank < 3):          # not on the course itself for the first ranks
            plant(FIR_MESHES, x + rnd.uniform(-5, 5), y + rnd.uniform(-3, 3), rnd.uniform(22, 36) + rank * 1.4, rnd.uniform(0.9, 1.25)); n_trees += 1
        y -= rnd.uniform(7, 12)
for (x, y, h) in [(-128, -64, 19), (-137, -82, 23), (-146, -58, 17), (-122, -92, 21), (-131, -44, 15), (-140, 22, 18), (-128, 34, 15), (-150, 12, 22), (-118, 48, 13),
                  (-14, 58, 18), (-60, 46, 16), (-90, 56, 19), (150, 50, 17), (176, 44, 15)]:
    plant(LEAFY_MESHES, x, y, h, rnd.uniform(0.95, 1.2)); n_trees += 1
# the inside of the course: a far rank of firs to close it
for rank in range(5):
    y = 70 + rank * 14; x = -300
    while x < 500:
        plant(FIR_MESHES, x + rnd.uniform(-4, 4), y + rnd.uniform(-4, 4), rnd.uniform(22, 34) + rank * 2, rnd.uniform(0.9, 1.2)); n_trees += 1
        x += rnd.uniform(8, 13)
print("trees:", n_trees, flush=True)


# ---------------- the runners
def runners(spots):
    COATS = [("#a35a40", "#5e3328"), ("#6b4032", "#2a2020"), ("#3d3536", "#232021"), ("#cfcdbe", "#8d8b80"), ("#8e4f36", "#3a2420")]
    SILKS = ["ballydoyle-navy", "alcohol-free", "aga-khan", "ballydoyle-orange", "black-white", "bradsell", "amo-2", "ballydoyle-pink", "ballydoyle-purple"]
    for i, (x, y, phase, ride) in enumerate(spots):
        before = set(bpy.data.objects); acts = set(bpy.data.actions)
        bpy.ops.import_scene.gltf(filepath=rp("assets/models/racehorse_v2.glb"))
        new = [o for o in bpy.data.objects if o not in before]
        mine = {a.name.split(".")[0]: a for a in bpy.data.actions if a not in acts}
        arm = next(o for o in new if o.type == "ARMATURE"); root = next(o for o in new if o.parent is None)
        root.location = (x, y, 0); root.rotation_euler = (0, 0, math.pi); root.scale = (3, 3, 3)
        coat, points = COATS[i % len(COATS)]
        img = bpy.data.images.load(rp("race-view/assets/silks-3d-v2/%s.png" % SILKS[i % len(SILKS)]))
        meshes = [o for o in new if o.type == "MESH"]
        best = max(len(o.data.polygons) for o in meshes)
        groups = {}
        for o in meshes: groups.setdefault(o.name.split(".")[0].rsplit("_", 1)[-1] if o.name.split(".")[0].endswith(("_close", "_far")) else "race", []).append(o)
        show = groups.get("close") or groups.get("race") or meshes
        for o in meshes:
            if o not in show: o.hide_render = True; continue
            for p in o.data.polygons: p.use_smooth = True
            for k, sl in enumerate(o.material_slots):
                nm = sl.material.name if sl.material else ""
                m = bpy.data.materials.new("h%d_%s" % (i, nm)); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
                b.inputs["Roughness"].default_value = 0.72; b.inputs["Specular IOR Level"].default_value = 0.22
                if "silks" in nm:
                    t = nt.nodes.new("ShaderNodeTexImage"); t.image = img; nt.links.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.8
                else:
                    ca = nt.nodes.new("ShaderNodeVertexColor"); sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(ca.outputs["Color"], sp.inputs[0])
                    def z(ch, hexc, prev):
                        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; nt.links.new(sp.outputs[ch], mx.inputs["Factor"])
                        if isinstance(prev, tuple): mx.inputs[6].default_value = prev
                        else: nt.links.new(prev, mx.inputs[6])
                        mx.inputs[7].default_value = lin(hexc); return mx.outputs[2]
                    c = z("Red", coat, lin("#33302e")); c = z("Green", points, c); c = z("Blue", "#d6ab8a", c)
                    nt.links.new(c, b.inputs["Base Color"])
                o.material_slots[k].link = "OBJECT"; o.material_slots[k].material = m
        arm.animation_data_create(); arm.animation_data.action = None
        for nm in ("gallop_v2", ride):
            act = mine.get(nm) or bpy.data.actions.get(nm)
            if not act: print("no clip", nm); continue
            tr = arm.animation_data.nla_tracks.new(); st = tr.strips.new(nm, 1, act); st.frame_start = 1 - phase; st.repeat = 6
    scene.frame_set(1)
    print("runners:", len(spots), flush=True)


# course x, then Blender y (the track is y 0 .. -W, the stand side at -W); phase in frames; how the jockey rides
runners([(-7, -16.0, 3, "ride_drive"), (-3.4, -19.6, 12, "ride_drive"), (-1.2, -13.6, 20, "ride_push"), (3.4, -21.8, 7, "ride_push"),
         (6.0, -17.2, 15, "ride_push"), (10.2, -23.6, 24, "ride_quiet"), (13.0, -19.4, 9, "ride_push")])

# ---------------- render
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.max_bounces = 6; scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.view_settings.exposure = float(os.environ.get("EXPOSURE", "0.0"))
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.film_transparent = False

# the distance pass: every surface glows by how much mist lies between it and the camera
dm = bpy.data.materials.new("v2_dist"); dm.use_nodes = True; nt = dm.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial"); em = nt.nodes.new("ShaderNodeEmission"); cd = nt.nodes.new("ShaderNodeCameraData")
mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0; mr.inputs["From Max"].default_value = 800
nt.links.new(cd.outputs["View Distance"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])


def course(p): return Vector((p[0], -p[2], p[1]))


SHOTS = {      # course axes: eye, look-at, field of view
    "hero": ((-17, 1.9, 9), (7.6, 8.6, 40.5), 50),        # low on the track just past the post: the field coming at the camera, the tower behind
    "wide": ((78, 15, -36), (-30, 15, 50), 36),         # over the inside of the course: the stand, the firs and the mist
    "rail": ((-36, 2.0, 23.5), (4, 6.5, 37), 46),          # along the outer rail and the crowd
}


def shoot(name):
    eye, at, fov = SHOTS[name]
    cam = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    if cam.name not in scene.collection.objects: scene.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"; cam.data.angle_y = math.radians(fov); cam.data.clip_end = 6000
    e, a = course(eye), course(at)
    cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler(); scene.camera = cam
    base = os.path.join(OUTDIR, "%s%s" % (os.environ.get("TAG", "v2_"), name))
    scene.render.filepath = base + "_raw.png"
    t = time.time(); bpy.ops.render.render(write_still=True); print("rendered", name, round(time.time() - t), "s", flush=True)
    if os.environ.get("HAZE", "1") != "0":
        vl = scene.view_layers[0]; keep = (scene.cycles.samples, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, wn["Background"].inputs[1].default_value)
        vl.material_override = dm; scene.cycles.samples = 6; scene.cycles.use_denoising = False
        scene.view_settings.view_transform = "Raw"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0
        links = [(l.from_socket, l.to_socket) for l in wl if l.to_socket == wn["Background"].inputs[0]]
        for l in list(wl):
            if l.to_socket == wn["Background"].inputs[0]: wl.remove(l)
        wn["Background"].inputs[0].default_value = (1, 1, 1, 1); wn["Background"].inputs[1].default_value = 1
        scene.render.image_settings.color_depth = "16"; scene.render.filepath = base + "_dist.png"
        bpy.ops.render.render(write_still=True)
        vl.material_override = None; scene.cycles.samples, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure = keep[:4]
        scene.cycles.use_denoising = True; scene.render.image_settings.color_depth = "8"
        for a_, b_ in links: wl.new(a_, b_)
        wn["Background"].inputs[1].default_value = keep[4]
    print("done", name, flush=True)


for name in CAM.split(","):
    shoot(name)
print("TOTAL", round(time.time() - T0), "s", flush=True)
