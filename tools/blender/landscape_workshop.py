"""Landscape workshop (owner, 11 Nov 2026): Ascot as it is (the stand, the crowd and their colours untouched), under
the softer light and the graded sky he liked, with much less mist; then one thing changed at a time: six ways of doing
the trees, six of the turf (the track and the ground round it), a few skies. Same camera throughout.

    python -c "exec(open('tools/blender/landscape_workshop.py').read())"
    env: SAMPLES (28), RES (960x540), OUT (reference/landscape-workshop), ONLY (e.g. "trees:A,trees:C,turf:2"), CAM (west)

Each tile is rendered twice (the picture; how far each point is from the camera) and finished by
tools/blender/v2_post.py, which lays in the distance haze and the sky's gradient.
"""
import os, sys, math, json, random, time, subprocess
T0 = time.time()
os.environ.setdefault("CROWD", "assets/models/architecture/crowd_set_12.glb")
os.environ["GRASS"] = "0"
_argv = sys.argv; sys.argv = ["ws", "model"]
_src = open("tools/blender/stand_clean_study.py").read()
exec(compile(_src[:_src.index('scene.render.engine = "CYCLES"')], "study", "exec"))
sys.argv = _argv
import bpy, bmesh
from mathutils import Vector, Matrix

SAMPLES = int(os.environ.get("SAMPLES", "28"))
RES = tuple(int(v) for v in os.environ.get("RES", "960x540").split("x"))
OUTDIR = os.environ.get("OUT", rp("reference/landscape-workshop")); os.makedirs(OUTDIR, exist_ok=True)
ONLY = [s for s in os.environ.get("ONLY", "").split(",") if s]
rnd = random.Random(11)
N_ = lambda nt, kind: nt.nodes.new(kind)


# ---------------- the softer light and the graded sky (as the misty frames), everything else as the game has it
wn, wl = world.node_tree.nodes, world.node_tree.links
for n in list(wn):
    if n.type not in ("BACKGROUND", "OUTPUT_WORLD"): wn.remove(n)
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], ramp.inputs[0])
els = ramp.color_ramp.elements
els[0].position = 0.0; els[0].color = lin("#f6f1cf"); els[1].position = 0.55; els[1].color = lin("#a6d2cb")
mid = els.new(0.12); mid.color = lin("#eaf0d2")
wl.new(ramp.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = float(os.environ.get("SKY", "0.75"))
sun.data.energy = float(os.environ.get("SUNPOW", "7.0")); sun.data.angle = math.radians(9); sun.data.color = (1.0, 0.92, 0.7)
d = Vector((float(v) for v in os.environ.get("SUN", "-0.25,0.85,0.55").split(","))).normalized()
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

GROUND, TRACK = bpy.data.objects["ground"], bpy.data.objects["track"]
OG_TURF, OG_LAWN = TRACK.data.materials[0], GROUND.data.materials[0]


def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); c.hide_render = True; return c


# ---------------- where the trees stand (the same places for every kind): the wooded end of the straight,
# parkland on the inside of the course, a belt behind the lawns. Blender axes: x east, y north (the track is y 0 .. -W).
SPECIES = ["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]
SPOTS = []
def spot(x, y, s, sp=None): SPOTS.append((x, y, s, sp or (("poplar_a" if rnd.random() < 0.12 else rnd.choice(SPECIES))), rnd.uniform(0, 6.28)))
for row in range(3):                                   # the belt closing the end of the straight
    y = 100
    while y > -120:
        spot(-216 - row * 15 + rnd.uniform(-4, 4), y + rnd.uniform(-3, 3), rnd.uniform(1.3, 1.85)); y -= rnd.uniform(9, 14)
for row in range(2):                                   # behind the lawn beyond the stand's west end
    x = -112
    while x > -214:
        spot(x + rnd.uniform(-3, 3), -40 - row * 17 + rnd.uniform(-3, 3), rnd.uniform(1.1, 1.6)); x -= rnd.uniform(11, 15)
x = -36                                                # the back of the parkland inside the course
while x > -214:
    spot(x + rnd.uniform(-3, 3), 52 + rnd.uniform(-8, 10), rnd.uniform(1.5, 1.95)); x -= rnd.uniform(11, 16)
for (x, y, s) in [(-52, 12, 1.3), (-60, 22, 1.6), (-70, 10, 1.15), (-88, 16, 1.5), (-96, 30, 1.7), (-110, 9, 1.2), (-124, 20, 1.5), (-136, 10, 1.3),
                  (-150, 26, 1.7), (-168, 12, 1.4), (-182, 22, 1.6), (-200, 10, 1.3), (-44, 30, 1.5), (-116, 36, 1.6), (-162, 38, 1.5)]:
    spot(x, y, s)
for (x, y, s) in [(-78, 34, 1.9), (-142, 40, 2.0), (-205, -46, 1.8), (-190, 36, 1.9)]: spot(x, y, s, "poplar_a")
print("tree places:", len(SPOTS), flush=True)


def load_kit(path, tag):
    obs = [o for o in import_glb(rp(path)) if o.type == "MESH"]
    kit = {}
    for o in obs:
        M = o.matrix_world.copy()
        for c in o.users_collection: c.objects.unlink(o)
        kit[o.name.split(".")[0]] = (o.data, M)
    return kit


KIT_LEAFY = load_kit("assets/models/trees/trees.glb", "leafy")
KIT_CLAY = load_kit("assets/models/trees/trees_clay.glb", "clay")


def vcol_name(me):
    return me.color_attributes[0].name if len(me.color_attributes) else ""


def base(m, rough=0.92, spec=0.1):
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = spec; return b


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; return m, m.node_tree


def pick_ramp(nt, cols, src=None):
    oi = N_(nt, "ShaderNodeObjectInfo"); cr = N_(nt, "ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"; els = cr.color_ramp.elements
    while len(els) < len(cols): els.new(0.5)
    for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
    nt.links.new(src or oi.outputs["Random"], cr.inputs[0]); return cr.outputs[0]


def mul(nt, a, b):
    x = N_(nt, "ShaderNodeMix"); x.data_type = "RGBA"; x.blend_type = "MULTIPLY"; x.inputs["Factor"].default_value = 1.0
    for slot, v in ((6, a), (7, b)):
        if isinstance(v, tuple): x.inputs[slot].default_value = v
        else: nt.links.new(v, x.inputs[slot])
    return x.outputs[2]


def grey(nt, sock, lo, hi, f0=0.0, f1=1.0):
    mr = N_(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = f0; mr.inputs["From Max"].default_value = f1
    mr.inputs["To Min"].default_value = lo; mr.inputs["To Max"].default_value = hi; nt.links.new(sock, mr.inputs["Value"])
    cc = N_(nt, "ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"): nt.links.new(mr.outputs["Result"], cc.inputs[k])
    return cc.outputs["Color"]


def height(nt):
    t = N_(nt, "ShaderNodeTexCoord"); s = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(t.outputs["Object"], s.inputs[0]); return s.outputs["Z"], t


BARK_M, _nt = mat("ws_bark"); base(BARK_M).inputs["Base Color"].default_value = lin("#7a6656")
GREENS = ["#6f9a4e", "#7da85a", "#628c46", "#8bb265", "#5c8546", "#86ad5c", "#73a052", "#79a456", "#668f4a", "#8ab062", "#5f8946", "#9a6a52"]
SOFT_GREENS = ["#7fa46c", "#8bb078", "#74996a", "#96b880", "#6c9264", "#88ac74", "#a8765c"]


def tree_material(kind, me):
    m, nt = mat("ws_tree_" + kind); b = base(m)
    vc = N_(nt, "ShaderNodeVertexColor"); vc.layer_name = vcol_name(me)
    if kind == "A":       # the game's leafy trees, as painted
        nt.links.new(vc.outputs["Color"], b.inputs["Base Color"])
    elif kind == "B":     # the clay trees: their own shading, a leaf green for each tree
        nt.links.new(mul(nt, pick_ramp(nt, GREENS), mul(nt, vc.outputs["Color"], (1.12, 1.12, 1.12, 1))), b.inputs["Base Color"])
    elif kind == "C":     # leafy, graded: deep and cool at the skirt, warm and light at the crown; a tint for each tree
        z, _ = height(nt); r = N_(nt, "ShaderNodeValToRGB"); mr = N_(nt, "ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 2.0; mr.inputs["From Max"].default_value = 11.5; nt.links.new(z, mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], r.inputs[0])
        e = r.color_ramp.elements; e[0].position = 0.0; e[0].color = lin("#3f6b58"); e[1].position = 1.0; e[1].color = lin("#bfd08a"); e.new(0.5).color = lin("#739f66")
        lum = N_(nt, "ShaderNodeRGBToBW"); nt.links.new(vc.outputs["Color"], lum.inputs[0])
        col = mul(nt, r.outputs[0], grey(nt, lum.outputs[0], 0.72, 1.2, 0.05, 0.35))
        col = mul(nt, col, pick_ramp(nt, ["#ffffff", "#f2f6e4", "#e6f0e6", "#fff6dc", "#eef2d6", "#f6e0c8", "#ffffff", "#e9f2dc", "#f0c8a8"]))
        nt.links.new(col, b.inputs["Base Color"])
    elif kind == "D":     # flocked, like model-railway foliage: a fine two-tone speckle, a soft tooth, a velvet edge
        _, t = height(nt); vor = N_(nt, "ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 9.0; nt.links.new(t.outputs["Object"], vor.inputs["Vector"])
        z, _ = height(nt)
        col = mul(nt, pick_ramp(nt, SOFT_GREENS), grey(nt, vor.outputs["Color"], 0.72, 1.22))
        col = mul(nt, col, grey(nt, z, 0.7, 1.12, 2.0, 11.0)); col = mul(nt, col, mul(nt, vc.outputs["Color"], (1.12, 1.12, 1.12, 1)))
        nt.links.new(col, b.inputs["Base Color"])
        bp = N_(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.7; bp.inputs["Distance"].default_value = 0.12
        nt.links.new(vor.outputs["Distance"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Sheen Roughness"].default_value = 0.5
        b.inputs["Subsurface Weight"].default_value = 0.2; b.inputs["Subsurface Radius"].default_value = (0.2, 0.35, 0.1); b.inputs["Subsurface Scale"].default_value = 0.2
    elif kind == "E":     # faceted: flat planes of one green, lit and shaded
        nt.links.new(pick_ramp(nt, SOFT_GREENS), b.inputs["Base Color"])
    elif kind == "F":     # layered: each tree one flat tone, paler and cooler the further back it stands (set per tree)
        oi = N_(nt, "ShaderNodeObjectInfo"); r = N_(nt, "ShaderNodeValToRGB"); nt.links.new(oi.outputs["Color"], r.inputs[0])   # the tree's own colour carries its depth
        e = r.color_ramp.elements; e[0].position = 0.0; e[0].color = lin("#3f6f52"); e[1].position = 1.0; e[1].color = lin("#b9cfb0"); e.new(0.5).color = lin("#7ea27a")
        z, _ = height(nt)
        col = mul(nt, r.outputs[0], grey(nt, z, 0.9, 1.08, 2.0, 11.0))
        em = N_(nt, "ShaderNodeEmission"); nt.links.new(col, em.inputs["Color"]); em.inputs["Strength"].default_value = 0.85
        nt.links.new(col, b.inputs["Base Color"])
        mx = N_(nt, "ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.6
        out = nt.nodes["Material Output"]; nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


TREE_KINDS = {
    "A": ("Original leafy trees", KIT_LEAFY, "_crown", True),
    "B": ("Clay trees", KIT_CLAY, "_crown", True),
    "C": ("Leafy, graded dark to light", KIT_LEAFY, "_crown", True),
    "D": ("Flocked, like model foliage", KIT_CLAY, "_crown", True),
    "E": ("Faceted", KIT_CLAY, "_crown_far", False),
    "F": ("Layered flat tones", KIT_LEAFY, "_crown", True),
}
TREE_COLL = {}
CAMPOS = None      # set with the camera (for the layered kind)


def build_trees(kind):
    label, kit, part, smooth = TREE_KINDS[kind]
    c = coll("trees_" + kind); TREE_COLL[kind] = c
    mats = {}
    for (x, y, s, sp, turn) in SPOTS:
        T = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(turn, 4, "Z") @ Matrix.Scale(s, 4)
        for suffix in (part, "_trunk"):
            key = sp + suffix
            if key not in kit: key = sp + suffix.replace("_far", "")
            if key not in kit: continue
            me, M0 = kit[key]
            if (kind, key) not in mats:
                me2 = me.copy()
                for p in me2.polygons: p.use_smooth = smooth or suffix == "_trunk"
                me2.materials.clear(); me2.materials.append(BARK_M if suffix == "_trunk" else tree_material(kind, me2)); mats[(kind, key)] = me2
            o = bpy.data.objects.new("t", mats[(kind, key)]); c.objects.link(o); o.matrix_world = T @ M0
            if kind == "F":      # depth as the object's colour: 0 near the camera, 1 far
                k = max(0.0, min(1.0, ((Vector((x, y, 0)) - CAMPOS).length - 40) / 230)); o.color = (k, k, k, 1)
    return c


# ---------------- turf
def geo_xyz(nt):
    g = N_(nt, "ShaderNodeNewGeometry"); s = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(g.outputs["Position"], s.inputs[0]); return g, s


def bands(nt, sock, width, soft=0.25):
    a = N_(nt, "ShaderNodeMath"); a.operation = "MULTIPLY"; a.inputs[1].default_value = math.pi / width; nt.links.new(sock, a.inputs[0])
    sn = N_(nt, "ShaderNodeMath"); sn.operation = "SINE"; nt.links.new(a.outputs[0], sn.inputs[0])
    mr = N_(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = -soft; mr.inputs["From Max"].default_value = soft; nt.links.new(sn.outputs[0], mr.inputs["Value"])
    return mr.outputs["Result"]


def mixc(nt, a, b, fac):
    x = N_(nt, "ShaderNodeMix"); x.data_type = "RGBA"
    if isinstance(fac, float): x.inputs["Factor"].default_value = fac
    else: nt.links.new(fac, x.inputs["Factor"])
    for slot, v in ((6, a), (7, b)):
        if isinstance(v, tuple): x.inputs[slot].default_value = v
        else: nt.links.new(v, x.inputs[slot])
    return x.outputs[2]


def noise(nt, vec, scale, detail=3):
    n = N_(nt, "ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail; nt.links.new(vec, n.inputs["Vector"]); return n.outputs["Fac"]


def soft_turf(name, a, b, lane=3.75, fleck=0.05, cross=None, gradient=False, flock=False):
    m, nt = mat(name); bs = base(m, 0.97, 0.08); g, s = geo_xyz(nt)
    col = mixc(nt, lin(a), lin(b), bands(nt, s.outputs["Y"], lane)) if lane else lin(a)
    if cross:   # mown both ways: a second set of bands across the track
        col = mul(nt, col, grey(nt, bands(nt, s.outputs["X"], cross), 0.955, 1.045))
    if gradient:
        # deeper by the rails, a shade paler up the middle where it is ridden; and long slow drifts of tone along it
        ay = N_(nt, "ShaderNodeMath"); ay.operation = "ADD"; ay.inputs[1].default_value = W / 2; nt.links.new(s.outputs["Y"], ay.inputs[0])
        ab = N_(nt, "ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(ay.outputs[0], ab.inputs[0])
        col = mul(nt, col, grey(nt, ab.outputs[0], 1.07, 0.9, 0.0, W / 2))
        col = mul(nt, col, grey(nt, noise(nt, g.outputs["Position"], 0.012, 2), 0.9, 1.1, 0.3, 0.7))
    if flock:
        vor = N_(nt, "ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 14.0; nt.links.new(g.outputs["Position"], vor.inputs["Vector"])
        col = mul(nt, col, grey(nt, vor.outputs["Color"], 0.86, 1.12))
        bp = N_(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; bp.inputs["Distance"].default_value = 0.03
        nt.links.new(vor.outputs["Distance"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], bs.inputs["Normal"])
        bs.inputs["Sheen Weight"].default_value = 0.8; bs.inputs["Sheen Roughness"].default_value = 0.4
    n1 = noise(nt, g.outputs["Position"], 0.035, 3); n2 = noise(nt, g.outputs["Position"], 2.2, 5)
    add = N_(nt, "ShaderNodeMath"); add.operation = "ADD"; nt.links.new(n1, add.inputs[0]); nt.links.new(n2, add.inputs[1])
    col = mul(nt, col, grey(nt, add.outputs[0], 1 - fleck, 1 + fleck, 0.6, 1.4))
    nt.links.new(col, bs.inputs["Base Color"])
    return no_green_bounce(m, "#b3ab8a")


def soft_lawn(name, far, near=None, meadow=False):
    """The ground round the track: 'near' beside the rails, easing to 'far' further off."""
    m, nt = mat(name); bs = base(m, 0.97, 0.08); g, s = geo_xyz(nt)
    col = lin(far)
    if near:
        ay = N_(nt, "ShaderNodeMath"); ay.operation = "ADD"; ay.inputs[1].default_value = W / 2; nt.links.new(s.outputs["Y"], ay.inputs[0])
        ab = N_(nt, "ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(ay.outputs[0], ab.inputs[0])
        mr = N_(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = W / 2 + 4; mr.inputs["From Max"].default_value = W / 2 + 40; nt.links.new(ab.outputs[0], mr.inputs["Value"])
        col = mixc(nt, lin(near), lin(far), mr.outputs["Result"])
    if meadow:   # longer grass: drifts of straw and deeper green, and flecks of flower
        col = mixc(nt, col, lin("#cfc68c"), grey(nt, noise(nt, g.outputs["Position"], 0.05, 4), 0.0, 0.7, 0.45, 0.75))
        col = mixc(nt, col, lin("#7f9f6a"), grey(nt, noise(nt, g.outputs["Position"], 0.11, 3), 0.0, 0.5, 0.5, 0.8))
        vor = N_(nt, "ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.4; nt.links.new(g.outputs["Position"], vor.inputs["Vector"])
        dot = N_(nt, "ShaderNodeMath"); dot.operation = "LESS_THAN"; dot.inputs[1].default_value = 0.05; nt.links.new(vor.outputs["Distance"], dot.inputs[0])
        col = mixc(nt, col, pick_ramp(nt, ["#f4efe0", "#ead27a", "#f4efe0", "#d9a0b4"], vor.outputs["Color"]), dot.outputs[0])
    n1 = noise(nt, g.outputs["Position"], 0.03, 3); n2 = noise(nt, g.outputs["Position"], 2.6, 5)
    add = N_(nt, "ShaderNodeMath"); add.operation = "ADD"; nt.links.new(n1, add.inputs[0]); nt.links.new(n2, add.inputs[1])
    col = mul(nt, col, grey(nt, add.outputs[0], 0.955, 1.045, 0.6, 1.4))
    nt.links.new(col, bs.inputs["Base Color"])
    return no_green_bounce(m, "#b3ab8a")


BLADES = coll("blades")
_before = set(bpy.data.objects)
grass_blades("ws_blades", -112, -28, -W + 0.1, -0.1, 115, 0.05, "#9db886", lanes=True, seed=3)
grass_blades("ws_meadow", -130, -28, 0.6, 30, 26, 0.16, "#b3bd84", lanes=False, seed=5)
for o in [o for o in bpy.data.objects if o not in _before and o.name in ("ws_blades", "ws_meadow")]:
    for c in o.users_collection: c.objects.unlink(o)
    BLADES.objects.link(o)

TURFS = {
    "1": ("Original turf", OG_TURF, OG_LAWN, False),
    "2": ("Soft sage, mown in lanes", soft_turf("t2", "#88a873", "#96b47f"), soft_lawn("l2", "#bccb98", "#d9cfa6"), False),
    "3": ("Soft sage, graded", soft_turf("t3", "#88a873", "#93b17c", gradient=True), soft_lawn("l3", "#b3c592", "#d3cc9e"), False),
    "4": ("Mown both ways", soft_turf("t4", "#88a873", "#96b47f", cross=11.0), soft_lawn("l4", "#bccb98", "#d9cfa6"), False),
    "5": ("Flocked velvet", soft_turf("t5", "#86a772", "#90b07a", flock=True, fleck=0.03), soft_lawn("l5", "#b8c896", "#d6cda4"), False),
    "6": ("Standing grass, meadow beyond the rail", soft_turf("t6", "#88a873", "#96b47f"), soft_lawn("l6", "#b6c592", "#cfc9a0", meadow=True), True),
}


def set_turf(k):
    _, t, l, blades = TURFS[k]
    TRACK.data.materials[0] = t; GROUND.data.materials[0] = l; BLADES.hide_render = not blades


# ---------------- a few runners, for scale
def runners(spots):
    COATS = [("#7a4a2a", "#1d1714"), ("#a3552c", "#6a3317"), ("#2b2523", "#141110"), ("#a8a6a0", "#6d6b66"), ("#4a2e1c", "#17110d")]
    SILKS = ["ballydoyle-navy", "alcohol-free", "aga-khan", "ballydoyle-orange", "black-white"]
    for i, (x, y, phase, ride) in enumerate(spots):
        before = set(bpy.data.objects); acts = set(bpy.data.actions)
        bpy.ops.import_scene.gltf(filepath=rp("assets/models/racehorse_v2.glb"))
        new = [o for o in bpy.data.objects if o not in before]
        mine = {a.name.split(".")[0]: a for a in bpy.data.actions if a not in acts}
        arm = next(o for o in new if o.type == "ARMATURE"); root = next(o for o in new if o.parent is None)
        root.location = (x, y, 0); root.rotation_euler = (0, 0, math.pi); root.scale = (3, 3, 3)
        coat, points = COATS[i % len(COATS)]
        img = bpy.data.images.load(rp("race-view/assets/silks-3d-v2/%s.png" % SILKS[i % len(SILKS)]))
        for o in [o for o in new if o.type == "MESH"]:
            if "close" in o.name or "far" in o.name: o.hide_render = True; continue
            for k, sl in enumerate(o.material_slots):
                nm = sl.material.name if sl.material else ""
                m, nt = mat("h%d_%s" % (i, nm)); b = base(m, 0.72, 0.22)
                if "silks" in nm:
                    t = N_(nt, "ShaderNodeTexImage"); t.image = img; nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
                else:
                    ca = N_(nt, "ShaderNodeVertexColor"); sp = N_(nt, "ShaderNodeSeparateColor"); nt.links.new(ca.outputs["Color"], sp.inputs[0])
                    c = mixc(nt, lin("#33302e"), lin(coat), sp.outputs["Red"]); c = mixc(nt, c, lin(points), sp.outputs["Green"]); c = mixc(nt, c, lin("#d6ab8a"), sp.outputs["Blue"])
                    nt.links.new(c, b.inputs["Base Color"])
                o.material_slots[k].link = "OBJECT"; o.material_slots[k].material = m
        arm.animation_data_create(); arm.animation_data.action = None
        for nm in ("gallop_v2", ride):
            act = mine.get(nm) or bpy.data.actions.get(nm)
            if act: tr = arm.animation_data.nla_tracks.new(); st = tr.strips.new(nm, 1, act); st.frame_start = 1 - phase; st.repeat = 6
    scene.frame_set(1)


runners([(-66, -12.0, 3, "ride_push"), (-62, -17.5, 12, "ride_push"), (-59.5, -8.6, 20, "ride_quiet"), (-55, -20.0, 7, "ride_quiet"), (-52, -14.0, 15, "ride_quiet")])

# ---------------- render
scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.max_bounces = 6; scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.view_settings.exposure = float(os.environ.get("EXPOSURE", "0.0"))
scene.render.resolution_x, scene.render.resolution_y = RES

dm, nt = mat("ws_dist")
for n in list(nt.nodes): nt.nodes.remove(n)
out = N_(nt, "ShaderNodeOutputMaterial"); em = N_(nt, "ShaderNodeEmission"); cd = N_(nt, "ShaderNodeCameraData"); mr = N_(nt, "ShaderNodeMapRange")
mr.inputs["From Max"].default_value = 800; nt.links.new(cd.outputs["View Distance"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])

CAMS = {   # course axes (x east, y up, z south): eye, look-at, field of view
    "west": ((-22, 7.5, 21), (-140, 6.5, 5), 46),
}
eye, at, fov = CAMS[os.environ.get("CAM", "west")]
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
cam.data.sensor_fit = "VERTICAL"; cam.data.angle_y = math.radians(fov); cam.data.clip_end = 6000
e, a = Vector((eye[0], -eye[2], eye[1])), Vector((at[0], -at[2], at[1]))
cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler(); scene.camera = cam
CAMPOS = Vector((e.x, e.y, 0))
HAZE = os.environ.get("HAZEARGS", "70 520 0.6 #efecc6 #b4d4cc").split()


def shoot(tag):
    base_path = os.path.join(OUTDIR, tag)
    scene.render.filepath = base_path + "_raw.png"; scene.render.image_settings.color_depth = "8"
    t = time.time(); bpy.ops.render.render(write_still=True)
    vl = scene.view_layers[0]; keep = (scene.cycles.samples, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, wn["Background"].inputs[1].default_value)
    vl.material_override = dm; scene.cycles.samples = 6; scene.cycles.use_denoising = False
    scene.view_settings.view_transform = "Raw"; scene.view_settings.look = "None"; scene.view_settings.exposure = 0
    links = [(l.from_socket, l.to_socket) for l in wl if l.to_socket == wn["Background"].inputs[0]]
    for l in list(wl):
        if l.to_socket == wn["Background"].inputs[0]: wl.remove(l)
    wn["Background"].inputs[0].default_value = (1, 1, 1, 1); wn["Background"].inputs[1].default_value = 1
    scene.render.image_settings.color_depth = "16"; scene.render.filepath = base_path + "_dist.png"
    bpy.ops.render.render(write_still=True)
    vl.material_override = None; scene.cycles.samples, scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure = keep[:4]
    scene.cycles.use_denoising = True
    for a_, b_ in links: wl.new(a_, b_)
    wn["Background"].inputs[1].default_value = keep[4]
    subprocess.run([sys.executable, rp("tools/blender/v2_post.py"), base_path] + HAZE, check=False, stdout=subprocess.DEVNULL)
    print("tile", tag, round(time.time() - t), "s", flush=True)


want = lambda k: not ONLY or k in ONLY
for kind in TREE_KINDS:
    if want("trees:" + kind) or (kind == "A" and any(o.startswith("turf:") for o in ONLY)) or not ONLY: build_trees(kind)
# the trees, one kind at a time, on the soft sage turf
set_turf("2")
for kind in TREE_KINDS:
    if not want("trees:" + kind): continue
    for k, c in TREE_COLL.items(): c.hide_render = k != kind
    shoot("trees_" + kind)
# the turf, one kind at a time, with the original trees
for k, c in TREE_COLL.items(): c.hide_render = k != "A"
for k in TURFS:
    if not want("turf:" + k): continue
    set_turf(k); shoot("turf_" + k)
json.dump({"trees": {k: v[0] for k, v in TREE_KINDS.items()}, "turf": {k: v[0] for k, v in TURFS.items()}}, open(os.path.join(OUTDIR, "labels.json"), "w"))
print("TOTAL", round(time.time() - T0), "s", flush=True)
