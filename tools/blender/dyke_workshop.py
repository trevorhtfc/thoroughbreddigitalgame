"""Landscape workshop, round 2 (owner, 11 Nov 2026): the ground "less flat", and lower-level foliage and texture in the
surrounding land, tried on the Rowley Mile's far side: the turf, the verge beyond the rail, the Devil's Dyke and the
trees behind it. The course is built from the race view's own files (courses heights, the Dyke's rows, the trees'
places), so anything that works here has a place to go.

    python -c "exec(open('tools/blender/dyke_workshop.py').read())"
    env: SAMPLES (28), RES (960x540), OUT (reference/landscape-workshop/dyke), CAMS (across,track), ONLY (1,2,3)

Three treatments from each camera:
  1  as it is now: flat colours, the Dyke an even grass ramp
  2  tone and texture: graded turf, drifts of tone in the land, the Dyke coloured by its height and roughened so its
     line is no longer ruled; the trees graded and paler with distance
  3  the same with low foliage: long grass and flowers on the verge and the bank, thorn scrub on its face and crest
Race-view axes: x along the straight (the post at 0, running towards -x), y up, z across (the stands +z, the Dyke -z);
Blender = (x, -z, y).
"""
import os, sys, math, json, random, time, subprocess
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

T0 = time.time()
REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
SAMPLES = int(os.environ.get("SAMPLES", "28"))
RES = tuple(int(v) for v in os.environ.get("RES", "960x540").split("x"))
OUTDIR = os.environ.get("OUT", rp("reference/landscape-workshop/dyke")); os.makedirs(OUTDIR, exist_ok=True)
ONLY = [s for s in os.environ.get("ONLY", "1,2,3").split(",") if s]
CDIR = rp("race-view/assets/course")
SC = json.load(open(os.path.join(CDIR, "newmarket-scenery.json")))
VIEW = json.load(open(os.path.join(CDIR, "newmarket-view.json")))
COURSE = json.load(open(os.path.join(CDIR, "newmarket.json")))
W = COURSE["trackWidth"]
X0, X1 = 420.0, 1320.0            # the stretch of the straight that is dressed in detail
rnd = random.Random(5)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
N_ = lambda nt, kind: nt.nodes.new(kind)


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


def B(x, z, y=0.0): return Vector((x, -z, y))


G = COURSE["ground"]; GH = np.array(G["h"], dtype=np.float32).reshape(G["nz"], G["nx"])
def ground_y(x, z):
    fx, fz = (x - G["x0"]) / G["cell"], (z - G["z0"]) / G["cell"]
    i, j = int(min(max(math.floor(fx), 0), G["nx"] - 2)), int(min(max(math.floor(fz), 0), G["nz"] - 2))
    a, b = min(max(fx - i, 0), 1), min(max(fz - j, 0), 1)
    return float((GH[j, i] * (1 - a) + GH[j, i + 1] * a) * (1 - b) + (GH[j + 1, i] * (1 - a) + GH[j + 1, i + 1] * a) * b)


# ---------------- small shader helpers
def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.96; b.inputs["Specular IOR Level"].default_value = 0.08
    return m, m.node_tree, b


def mul(nt, a, b):
    x = N_(nt, "ShaderNodeMix"); x.data_type = "RGBA"; x.blend_type = "MULTIPLY"; x.inputs["Factor"].default_value = 1.0
    for slot, v in ((6, a), (7, b)):
        if isinstance(v, tuple): x.inputs[slot].default_value = v
        else: nt.links.new(v, x.inputs[slot])
    return x.outputs[2]


def mixc(nt, a, b, fac):
    x = N_(nt, "ShaderNodeMix"); x.data_type = "RGBA"
    if isinstance(fac, float): x.inputs["Factor"].default_value = fac
    else: nt.links.new(fac, x.inputs["Factor"])
    for slot, v in ((6, a), (7, b)):
        if isinstance(v, tuple): x.inputs[slot].default_value = v
        else: nt.links.new(v, x.inputs[slot])
    return x.outputs[2]


def rng(nt, sock, lo, hi, f0=0.0, f1=1.0):
    mr = N_(nt, "ShaderNodeMapRange"); mr.inputs["From Min"].default_value = f0; mr.inputs["From Max"].default_value = f1
    mr.inputs["To Min"].default_value = lo; mr.inputs["To Max"].default_value = hi; nt.links.new(sock, mr.inputs["Value"]); return mr.outputs["Result"]


def grey(nt, sock, lo, hi, f0=0.0, f1=1.0):
    cc = N_(nt, "ShaderNodeCombineColor"); r = rng(nt, sock, lo, hi, f0, f1)
    for k in ("Red", "Green", "Blue"): nt.links.new(r, cc.inputs[k])
    return cc.outputs["Color"]


def pos(nt):
    g = N_(nt, "ShaderNodeNewGeometry"); s = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(g.outputs["Position"], s.inputs[0]); return g.outputs["Position"], s


def noise(nt, vec, scale, detail=3, stretch=None):
    n = N_(nt, "ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
    if stretch:
        mp = N_(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = stretch; nt.links.new(vec, mp.inputs[0]); vec = mp.outputs[0]
    nt.links.new(vec, n.inputs["Vector"]); return n.outputs["Fac"]


def ramp(nt, sock, stops):
    r = N_(nt, "ShaderNodeValToRGB"); nt.links.new(sock, r.inputs[0]); els = r.color_ramp.elements
    while len(els) < len(stops): els.new(0.5)
    for e, (p, c) in zip(els, sorted(stops)): e.position = p; e.color = c if isinstance(c, tuple) else lin(c)
    return r.outputs[0]


def attr(nt, name):
    a = N_(nt, "ShaderNodeAttribute"); a.attribute_name = name; return a.outputs["Fac"]


def warm_bounce(m, hexc="#b3ab8a"):
    """Green to the camera, but it bounces a warm neutral light onto what stands on it."""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; out = nt.nodes["Material Output"]
    lp = N_(nt, "ShaderNodeLightPath"); d = N_(nt, "ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = lin(hexc); mx = N_(nt, "ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"]); nt.links.new(d.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def linear(c): return (c[0], c[1], c[2], 1.0)


# ---------------- materials: as it is now, and the textured ones
GV = VIEW["ground"]; LS = VIEW.get("lanesStraight") or {"lanes": 8, "width": W, "strength": 0.16}
def lanes(nt, s, strength):
    a = N_(nt, "ShaderNodeMath"); a.operation = "MULTIPLY"; a.inputs[1].default_value = math.pi * LS["lanes"] / LS["width"]; nt.links.new(s.outputs["Y"], a.inputs[0])
    c = N_(nt, "ShaderNodeMath"); c.operation = "COSINE"; nt.links.new(a.outputs[0], c.inputs[0])
    return grey(nt, c.outputs[0], 1 - strength, 1 + strength, -0.3, 0.3)

M = {}
m, nt, b = mat("now_lawn"); b.inputs["Base Color"].default_value = linear(GV["outside"]); M["now_lawn"] = warm_bounce(m)
m, nt, b = mat("now_turf"); p, s = pos(nt); nt.links.new(mul(nt, linear(GV["turf"]), lanes(nt, s, LS["strength"])), b.inputs["Base Color"]); M["now_turf"] = warm_bounce(m)
m, nt, b = mat("now_bank"); nt.links.new(ramp(nt, rng(nt, attr(nt, "bank_h"), 0, 1, 0, 5.2), [(h / 5.2, linear(c)) for h, c in GV["bankRamp"]]), b.inputs["Base Color"]); M["now_bank"] = warm_bounce(m)

# soft sage turf, graded: lanes, deeper by the rails, slow drifts along it
m, nt, b = mat("tex_turf"); p, s = pos(nt)
col = mul(nt, lin("#86a872"), lanes(nt, s, 0.075))
ay = N_(nt, "ShaderNodeMath"); ay.operation = "ADD"; ay.inputs[1].default_value = W / 2; nt.links.new(s.outputs["Y"], ay.inputs[0])
ab = N_(nt, "ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(ay.outputs[0], ab.inputs[0])
col = mul(nt, col, grey(nt, ab.outputs[0], 1.06, 0.9, 0.0, W / 2))
col = mul(nt, col, grey(nt, noise(nt, p, 0.012, 2), 0.9, 1.1, 0.3, 0.7)); col = mul(nt, col, grey(nt, noise(nt, p, 2.2, 5), 0.95, 1.05, 0.3, 0.7))
nt.links.new(col, b.inputs["Base Color"]); M["tex_turf"] = warm_bounce(m)

# the land round the course: drifts of sage, olive and straw, broad mown swathes, a fine fleck; a little relief
m, nt, b = mat("tex_lawn"); p, s = pos(nt)
col = mixc(nt, lin("#a3b884"), lin("#c9c68c"), rng(nt, noise(nt, p, 0.006, 3), 0, 1, 0.38, 0.66))
col = mixc(nt, col, lin("#86a274"), rng(nt, noise(nt, p, 0.017, 3), 0, 0.8, 0.48, 0.7))
sw = N_(nt, "ShaderNodeMath"); sw.operation = "MULTIPLY"; sw.inputs[1].default_value = math.pi / 9.0; nt.links.new(s.outputs["Y"], sw.inputs[0])
sn = N_(nt, "ShaderNodeMath"); sn.operation = "SINE"; nt.links.new(sw.outputs[0], sn.inputs[0])
col = mul(nt, col, grey(nt, sn.outputs[0], 0.94, 1.06, -0.3, 0.3))
col = mul(nt, col, grey(nt, noise(nt, p, 1.8, 5), 0.94, 1.06, 0.3, 0.7))
nt.links.new(col, b.inputs["Base Color"])
bp = N_(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.5; nt.links.new(noise(nt, p, 0.05, 3), bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
M["tex_lawn"] = warm_bounce(m)

# the verge between the far rail and the Dyke: rougher, strawier, uncut
m, nt, b = mat("tex_verge"); p, s = pos(nt)
col = mixc(nt, lin("#98aa72"), lin("#cdbf7c"), rng(nt, noise(nt, p, 0.09, 4), 0, 1, 0.4, 0.68))
col = mixc(nt, col, lin("#6f9062"), rng(nt, noise(nt, p, 0.21, 3), 0, 0.8, 0.5, 0.72))
col = mul(nt, col, grey(nt, noise(nt, p, 3.0, 5), 0.9, 1.1, 0.3, 0.7))
nt.links.new(col, b.inputs["Base Color"]); M["tex_verge"] = warm_bounce(m)

# the Dyke: deep at its foot, olive on its face, straw and chalk along the crest; streaked down the slope; rough
m, nt, b = mat("tex_bank"); p, s = pos(nt); h = attr(nt, "bank_h")
col = ramp(nt, rng(nt, h, 0, 1, 0, 5.4), [(0.0, "#8fa878"), (0.16, "#587f5c"), (0.5, "#7a9458"), (0.8, "#b3aa68"), (1.0, "#d6c88a")])
streak = noise(nt, p, 0.5, 4, stretch=(0.22, 1.6, 1.0))
col = mul(nt, col, grey(nt, streak, 0.78, 1.2, 0.3, 0.7))
col = mixc(nt, col, lin("#4f7654"), rng(nt, noise(nt, p, 0.07, 3), 0, 0.7, 0.5, 0.7))                    # darker thickets of growth
chalk = N_(nt, "ShaderNodeMath"); chalk.operation = "MULTIPLY"; nt.links.new(rng(nt, noise(nt, p, 0.16, 2), 0, 1, 0.62, 0.72), chalk.inputs[0]); nt.links.new(rng(nt, h, 0, 1, 2.2, 4.6), chalk.inputs[1])
col = mixc(nt, col, lin("#e6dfc4"), rng(nt, chalk.outputs[0], 0, 0.75))                                      # chalk showing through on the upper face
nt.links.new(col, b.inputs["Base Color"])
bp = N_(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6; bp.inputs["Distance"].default_value = 0.25; nt.links.new(streak, bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
M["tex_bank"] = warm_bounce(m)
m, nt, b = mat("rail"); b.inputs["Base Color"].default_value = lin("#f4f2ea"); M["rail"] = m
m, nt, b = mat("bark"); b.inputs["Base Color"].default_value = lin("#7a6656"); M["bark"] = m


# ---------------- the land, the track, the Dyke, the rails
def grid_mesh(name, xs, zs, yfun, material, attrs=None):
    vs = [B(x, z, yfun(x, z)) for z in zs for x in xs]; nx = len(xs)
    fs = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i) for j in range(len(zs) - 1) for i in range(nx - 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.materials.append(material)
    for p_ in me.polygons: p_.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); return o


land = grid_mesh("land", [G["x0"] + i * G["cell"] for i in range(G["nx"])], [G["z0"] + j * G["cell"] for j in range(G["nz"])], lambda x, z: ground_y(x, z) - 0.03, M["now_lawn"])
xs = [x for x in np.arange(-120.0, 1900.0, 5.0)]
track = grid_mesh("track", xs, [0.0, W / 3, 2 * W / 3, W], lambda x, z: ground_y(x, z) + 0.0, M["now_turf"])
verge = grid_mesh("verge", [x for x in np.arange(X0 - 80, X1 + 80, 4.0)], [-0.6, -3.5, -6.5, -9.5, -12.4], lambda x, z: ground_y(x, z) + 0.01, M["tex_verge"])

rows = np.array(SC["banks"][0]["rows"], dtype=np.float32).reshape(len(SC["banks"][0]["rows"]), -1, 3)
def bank_mesh(name, sel):
    r = rows[sel]; nr, nc = r.shape[:2]
    vs = [B(float(x), float(z), float(y) + ground_y(float(x), float(z))) for (x, y, z) in r.reshape(-1, 3)]
    fs = [(i * nc + j, (i + 1) * nc + j, (i + 1) * nc + j + 1, i * nc + j + 1) for i in range(nr - 1) for j in range(nc - 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.materials.append(M["now_bank"])
    a = me.attributes.new("bank_h", "FLOAT", "POINT"); a.data.foreach_set("value", r[..., 1].reshape(-1).astype(np.float32))
    for p_ in me.polygons: p_.use_smooth = True
    me.validate(); me.update()
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o)
    n = sum(1 for p_ in me.polygons if p_.normal.z < 0)
    if n > len(me.polygons) / 2: me.flip_normals()
    return o


straight = np.where((rows[:, 0, 0] > -300) & (rows[:, 0, 0] < 2000))[0]
near = straight[(rows[straight, 0, 0] >= X0 - 60) & (rows[straight, 0, 0] <= X1 + 60)]
bank_far_a = bank_mesh("bank_a", straight[rows[straight, 0, 0] <= X0 - 60]) if (rows[straight, 0, 0] <= X0 - 60).any() else None
bank_far_b = bank_mesh("bank_b", straight[rows[straight, 0, 0] >= X1 + 60])
bank = bank_mesh("bank", near)
# roughened so its crest and foot are no longer ruled lines (treatments 2 and 3)
sub = bank.modifiers.new("sub", "SUBSURF"); sub.subdivision_type = "SIMPLE"; sub.levels = sub.render_levels = 2
tex = bpy.data.textures.new("lumps", "CLOUDS"); tex.noise_scale = 9.0; tex.noise_depth = 3
dsp = bank.modifiers.new("lumps", "DISPLACE"); dsp.texture = tex; dsp.strength = 1.1; dsp.mid_level = 0.5; dsp.texture_coords = "GLOBAL"
tex2 = bpy.data.textures.new("ripple", "CLOUDS"); tex2.noise_scale = 2.2; tex2.noise_depth = 2
dsp2 = bank.modifiers.new("ripple", "DISPLACE"); dsp2.texture = tex2; dsp2.strength = 0.28; dsp2.mid_level = 0.5; dsp2.texture_coords = "GLOBAL"
BANKS = [o for o in (bank, bank_far_a, bank_far_b) if o]


def bank_at(x, t):
    """A point on the Dyke: x along the course, t 0..1 across it (0 the course side). Returns (x, z, y)."""
    i = int(np.clip(np.searchsorted(rows[:, 0, 0], x), 1, len(rows) - 1)); r0, r1 = rows[i - 1], rows[i]
    k = float(np.clip((x - r0[0, 0]) / max(1e-6, r1[0, 0] - r0[0, 0]), 0, 1)); r = r0 * (1 - k) + r1 * k
    f = t * (r.shape[0] - 1); j = int(min(math.floor(f), r.shape[0] - 2)); a = f - j
    px, py, pz = r[j] * (1 - a) + r[j + 1] * a
    return float(px), float(pz), float(py) + ground_y(float(px), float(pz)), float(py)


# rails: a top board and posts, bay by bay along both rail lines of the straight
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((1.2, 0, 1.06)) @ Matrix.Diagonal((2.42, 0.12, 0.2, 1)))
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.5)) @ Matrix.Diagonal((0.09, 0.09, 1.0, 1)))
rail_me = bpy.data.meshes.new("rail_bay"); bm.to_mesh(rail_me); bm.free(); rail_me.materials.append(M["rail"])
rails = bpy.data.collections.new("rails"); scene.collection.children.link(rails)
for z in (-0.4, W + 0.4):
    for x in np.arange(-100.0, 1700.0, 2.4):
        o = bpy.data.objects.new("r", rail_me); rails.objects.link(o)
        y0, y1 = ground_y(x, z), ground_y(x + 2.4, z)
        o.location = B(x, z, y0); o.rotation_euler = (0, -math.atan2(y1 - y0, 2.4), 0)


# ---------------- trees and bushes: the game's own leafy kit, at the game's own places
def import_glb(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); return [o for o in bpy.data.objects if o not in before]


KIT = {}
for o in [o for o in import_glb(rp("assets/models/trees/trees.glb")) if o.type == "MESH"]:
    Mw = o.matrix_world.copy()
    for c in o.users_collection: c.objects.unlink(o)
    KIT[o.name.split(".")[0]] = (o.data, Mw)


def leaf_material(kind):
    m, nt, b = mat("leaf_" + kind); vc = N_(nt, "ShaderNodeVertexColor")
    if kind == "now":
        nt.links.new(vc.outputs["Color"], b.inputs["Base Color"]); return m
    # graded dark to light up each tree, and paler, cooler and flatter the further back it stands (the owner's C and F)
    tcn = N_(nt, "ShaderNodeTexCoord"); s = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Generated"], s.inputs[0])
    low, mid, top = ("#3c6a55", "#709d66", "#bccf8c") if kind == "tree" else ("#3f6650", "#6e9462", "#b3c284")
    col = ramp(nt, rng(nt, s.outputs["Z"], 0, 1, 0.05, 0.95), [(0.0, low), (0.5, mid), (1.0, top)])
    lum = N_(nt, "ShaderNodeRGBToBW"); nt.links.new(vc.outputs["Color"], lum.inputs[0]); col = mul(nt, col, grey(nt, lum.outputs[0], 0.76, 1.17, 0.05, 0.35))
    oi = N_(nt, "ShaderNodeObjectInfo")
    tint = N_(nt, "ShaderNodeValToRGB"); tint.color_ramp.interpolation = "CONSTANT"; els = tint.color_ramp.elements
    tints = ["#ffffff", "#f2f6e4", "#e6f0e6", "#fff6dc", "#eef2d6", "#f6e0c8", "#ffffff", "#e9f2dc"] + (["#f0c8a8"] if kind == "tree" else ["#f4ecc4", "#e8d8d0"])
    while len(els) < len(tints): els.new(0.5)
    for i, c in enumerate(tints): els[i].position = i / len(tints); els[i].color = lin(c)
    nt.links.new(oi.outputs["Random"], tint.inputs[0]); col = mul(nt, col, tint.outputs[0])
    far = N_(nt, "ShaderNodeSeparateColor"); nt.links.new(oi.outputs["Color"], far.inputs[0])
    k = N_(nt, "ShaderNodeMath"); k.operation = "MULTIPLY"; k.inputs[1].default_value = 0.42; nt.links.new(far.outputs["Red"], k.inputs[0])
    col = mixc(nt, col, lin("#bfd0b4"), k.outputs[0]); nt.links.new(col, b.inputs["Base Color"])
    em = N_(nt, "ShaderNodeEmission"); nt.links.new(col, em.inputs["Color"]); em.inputs["Strength"].default_value = 0.85
    k2 = N_(nt, "ShaderNodeMath"); k2.operation = "MULTIPLY"; k2.inputs[1].default_value = 0.5; nt.links.new(far.outputs["Red"], k2.inputs[0])
    mx = N_(nt, "ShaderNodeMixShader"); nt.links.new(k2.outputs[0], mx.inputs["Fac"]); out = nt.nodes["Material Output"]
    nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


LEAF = {k: leaf_material(k) for k in ("now", "tree", "bush")}
_cache = {}
def kit_mesh(key, material):
    if (key, material.name) not in _cache:
        me = KIT[key][0].copy(); me.materials.clear(); me.materials.append(material)
        for p_ in me.polygons: p_.use_smooth = True
        _cache[(key, material.name)] = me
    return _cache[(key, material.name)]


def collection(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c


TREES = {"now": collection("trees_now"), "graded": collection("trees_graded")}
tree_list = []
for t in SC["trees"]:
    x, z, name, s = t[0], t[1], t[2], t[3]; turn = t[4] if len(t) > 4 else 0; belt = t[5] if len(t) > 5 else 0; dy = t[6] if len(t) > 6 else 0
    if not (X0 - 500 < x < X1 + 700) or name + "_crown" not in KIT: continue
    tree_list.append((x, z, name, s, turn, belt, dy))
print("trees in range:", len(tree_list), flush=True)


def place_trees(camxy):
    for c in TREES.values():
        for o in list(c.objects): bpy.data.objects.remove(o)
    dd = sorted(math.hypot(x - camxy[0], z - camxy[1]) for (x, z, *_r) in tree_list); d0, d1 = dd[len(dd) // 20], dd[-len(dd) // 6]
    for (x, z, name, s, turn, belt, dy) in tree_list:
        T = Matrix.Translation(B(x, z, ground_y(x, z) + dy)) @ Matrix.Rotation(math.radians(turn), 4, "Z") @ Matrix.Scale(s, 4)
        k = max(0.0, min(1.0, (math.hypot(x - camxy[0], z - camxy[1]) - d0) / max(1.0, d1 - d0)))
        for tag, lm in (("now", LEAF["now"]), ("graded", LEAF["tree"])):
            for part, material in (("_crown", lm), ("_trunk", M["bark"])):
                if belt == 2 and part == "_trunk": continue
                key = name + part
                if key not in KIT: continue
                o = bpy.data.objects.new("t", kit_mesh(key, material)); TREES[tag].objects.link(o); o.matrix_world = T @ KIT[key][1]; o.color = (k, k, k, 1)


# ---------------- low foliage (treatment 3)
FOLIAGE = collection("foliage")
def tuft_mesh(name, blades, height, width, lean):
    r = random.Random(len(name) * 7 + blades); bm = bmesh.new()
    for i in range(blades):
        a = r.uniform(0, 6.283); d = r.uniform(0, 0.09); h = height * r.uniform(0.6, 1.1); l = lean * r.uniform(0.4, 1.3); w = width * r.uniform(0.7, 1.2)
        c, s_ = math.cos(a), math.sin(a); base = Vector((c * d, s_ * d, 0)); side = Vector((-s_, c, 0)) * w
        tip = base + Vector((c * l, s_ * l, h)); mid_ = base + Vector((c * l * 0.35, s_ * l * 0.35, h * 0.55))
        v = [bm.verts.new(p) for p in (base - side, base + side, mid_ + side * 0.6, mid_ - side * 0.6, tip)]
        bm.faces.new(v[:4]); bm.faces.new((v[3], v[2], v[4]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me


def blade_material(name, root, tip, tints):
    m, nt, b = mat(name); b.inputs["Subsurface Weight"].default_value = 0.3; b.inputs["Subsurface Radius"].default_value = (0.03, 0.06, 0.015)
    tcn = N_(nt, "ShaderNodeTexCoord"); s = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Generated"], s.inputs[0])
    col = mixc(nt, lin(root), lin(tip), rng(nt, s.outputs["Z"], 0, 1, 0.1, 0.9))
    oi = N_(nt, "ShaderNodeObjectInfo"); t = N_(nt, "ShaderNodeValToRGB"); t.color_ramp.interpolation = "CONSTANT"; els = t.color_ramp.elements
    while len(els) < len(tints): els.new(0.5)
    for i, c in enumerate(tints): els[i].position = i / len(tints); els[i].color = lin(c)
    nt.links.new(oi.outputs["Random"], t.inputs[0]); nt.links.new(mul(nt, col, t.outputs[0]), b.inputs["Base Color"])
    m.use_backface_culling = False
    return m


def scatter(target, inst_objs, density, smin, smax, seed, name):
    """Stand copies of a few small things all over a surface (geometry nodes), keeping the surface itself."""
    pick = bpy.data.collections.new(name + "_kit")
    for o in inst_objs: pick.objects.link(o)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"); ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    Gn, GL = ng.nodes, ng.links
    gi = Gn.new("NodeGroupInput"); go = Gn.new("NodeGroupOutput"); dist = Gn.new("GeometryNodeDistributePointsOnFaces"); dist.inputs["Density"].default_value = density; dist.inputs["Seed"].default_value = seed
    ci = Gn.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = pick; ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    inst = Gn.new("GeometryNodeInstanceOnPoints"); inst.inputs["Pick Instance"].default_value = True
    rr = Gn.new("FunctionNodeRandomValue"); rr.data_type = "FLOAT_VECTOR"; rr.inputs["Min"].default_value = (-0.12, -0.12, 0.0); rr.inputs["Max"].default_value = (0.12, 0.12, 6.283)
    rs = Gn.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"; rs.inputs["Min"].default_value = smin; rs.inputs["Max"].default_value = smax
    join = Gn.new("GeometryNodeJoinGeometry")
    GL.new(gi.outputs[0], dist.inputs["Mesh"]); GL.new(dist.outputs["Points"], inst.inputs["Points"]); GL.new(ci.outputs[0], inst.inputs["Instance"])
    GL.new(rr.outputs[0], inst.inputs["Rotation"]); GL.new(rs.outputs[0], inst.inputs["Scale"])
    GL.new(gi.outputs[0], join.inputs[0]); GL.new(inst.outputs[0], join.inputs[0]); GL.new(join.outputs[0], go.inputs[0])
    md = target.modifiers.new(name, "NODES"); md.node_group = ng; return md


def small(name, me, material):
    me.materials.append(material); o = bpy.data.objects.new(name, me); return o


GRASS_M = blade_material("long_grass", "#6f8a5c", "#c9c890", ["#ffffff", "#f0f4dc", "#fff4d0", "#e4eed8", "#f6e8c4"])
PARSLEY_M = blade_material("parsley", "#7f9a6a", "#f4f0e2", ["#ffffff", "#fbf6e6", "#f4f8ec"])
FLOWER_M = blade_material("flowers", "#7f9a6a", "#e8c85a", ["#ffffff", "#ffe9d8", "#f0b0a0", "#ffffff", "#e6d0f0"])
tufts = [small("tuft_a", tuft_mesh("tuft_a", 9, 0.55, 0.035, 0.22), GRASS_M), small("tuft_b", tuft_mesh("tuft_b", 13, 0.8, 0.04, 0.3), GRASS_M),
         small("tuft_c", tuft_mesh("tuft_c", 7, 0.4, 0.03, 0.16), GRASS_M)]
blooms = [small("bloom_a", tuft_mesh("bloom_a", 6, 0.75, 0.055, 0.12), PARSLEY_M), small("bloom_b", tuft_mesh("bloom_b", 5, 0.45, 0.05, 0.1), FLOWER_M)]
SCATTERS = [scatter(bank, tufts, 1.7, 0.8, 1.7, 3, "bank_grass"), scatter(bank, blooms, 0.16, 0.8, 1.5, 9, "bank_bloom"),
            scatter(verge, tufts, 2.6, 0.7, 1.4, 5, "verge_grass"), scatter(verge, blooms, 0.3, 0.8, 1.4, 11, "verge_bloom")]

# thorn scrub on the Dyke: clumps on its face and along the crest, thinner at its foot; the odd small thorn tree on top
def patch(x, z, f): return 0.5 + 0.5 * math.sin(x * f + 1.3) * math.cos(z * f * 1.7 + x * f * 0.31)
n_bush = 0
x = X0 - 40
while x < X1 + 40:
    x += rnd.uniform(1.2, 4.2)
    t = rnd.choice([rnd.uniform(0.24, 0.4), rnd.uniform(0.38, 0.62), rnd.uniform(0.3, 0.72)])
    px, pz, py, hh = bank_at(x, t)
    if hh < 0.6 or patch(px, pz, 0.021) < 0.42 + 0.25 * rnd.random(): continue
    for k in range(rnd.choice([1, 1, 2, 3])):
        qx, qz, qy, _ = bank_at(x + rnd.uniform(-2.2, 2.2), min(0.95, max(0.05, t + rnd.uniform(-0.05, 0.05))))
        key = rnd.choice(["bush_a_crown", "bush_b_crown"]); s = rnd.uniform(0.55, 1.15)
        o = bpy.data.objects.new("bush", kit_mesh(key, LEAF["bush"])); FOLIAGE.objects.link(o)
        o.matrix_world = Matrix.Translation(B(qx, qz, qy - 0.25)) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Diagonal((s * 1.15, s * 1.15, s * rnd.uniform(0.7, 1.0), 1)) @ KIT[key][1]
        o.color = (0.15, 0.15, 0.15, 1); n_bush += 1
x = X0 - 40
while x < X1 + 40:                      # small wind-bent thorns on the crest, in ones and twos
    x += rnd.uniform(18, 60)
    px, pz, py, hh = bank_at(x, rnd.uniform(0.42, 0.56))
    for part, material in (("_crown", LEAF["bush"]), ("_trunk", M["bark"])):
        key = rnd.choice(["oak_a", "oak_c", "wide_a"]) + part; s = rnd.uniform(0.34, 0.5)
        o = bpy.data.objects.new("thorn", kit_mesh(key, material)); FOLIAGE.objects.link(o)
        o.matrix_world = Matrix.Translation(B(px, pz, py - 0.2)) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Scale(s, 4) @ KIT[key][1]; o.color = (0.2, 0.2, 0.2, 1)
print("scrub:", n_bush, "bushes", flush=True)


# ---------------- a few runners
def runners(spots):
    COATS = [("#7a4a2a", "#1d1714"), ("#a3552c", "#6a3317"), ("#2b2523", "#141110"), ("#a8a6a0", "#6d6b66"), ("#4a2e1c", "#17110d")]
    SILKS = ["ballydoyle-navy", "alcohol-free", "aga-khan", "ballydoyle-orange", "black-white", "bradsell"]
    for i, (x, z, phase, ride) in enumerate(spots):
        before = set(bpy.data.objects); acts = set(bpy.data.actions)
        bpy.ops.import_scene.gltf(filepath=rp("assets/models/racehorse_v2.glb"))
        new = [o for o in bpy.data.objects if o not in before]; mine = {a.name.split(".")[0]: a for a in bpy.data.actions if a not in acts}
        arm = next(o for o in new if o.type == "ARMATURE"); root = next(o for o in new if o.parent is None)
        root.location = B(x, z, ground_y(x, z)); root.rotation_euler = (0, 0, math.pi); root.scale = (3, 3, 3)
        coat, points = COATS[i % len(COATS)]; img = bpy.data.images.load(rp("race-view/assets/silks-3d-v2/%s.png" % SILKS[i % len(SILKS)]))
        for o in [o for o in new if o.type == "MESH"]:
            if "close" in o.name or "far" in o.name: o.hide_render = True; continue
            for k, sl in enumerate(o.material_slots):
                nm = sl.material.name if sl.material else ""; m, nt, b = mat("h%d_%s" % (i, nm)); b.inputs["Roughness"].default_value = 0.72; b.inputs["Specular IOR Level"].default_value = 0.22
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


runners([(800, 9.0, 3, "ride_push"), (803.5, 13.5, 12, "ride_push"), (806, 6.5, 20, "ride_quiet"), (810, 16.0, 7, "ride_quiet"), (813, 11.0, 15, "ride_quiet"), (818, 20.0, 24, "ride_quiet")])

# ---------------- light and sky (as the Ascot workshop), render
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); wr = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], wr.inputs[0]); els = wr.color_ramp.elements
els[0].position = 0.0; els[0].color = lin("#f6f1cf"); els[1].position = 0.55; els[1].color = lin("#a6d2cb"); els.new(0.12).color = lin("#eaf0d2")
wl.new(wr.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 0.75
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object; sun.data.energy = 7.0; sun.data.angle = math.radians(9); sun.data.color = (1.0, 0.92, 0.7)
d = Vector((float(v) for v in os.environ.get("SUN", "0.8,-0.38,0.4").split(","))).normalized()      # low from up the course and a little to the stand side: it rakes along the Dyke and lights the long grass from behind
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
scene.render.engine = "CYCLES"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.max_bounces = 6; scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.render.resolution_x, scene.render.resolution_y = RES
dm, nt, _b = mat("dist")
for n in list(nt.nodes): nt.nodes.remove(n)
out = N_(nt, "ShaderNodeOutputMaterial"); em = N_(nt, "ShaderNodeEmission"); cd = N_(nt, "ShaderNodeCameraData"); mr = N_(nt, "ShaderNodeMapRange")
mr.inputs["From Max"].default_value = 800; nt.links.new(cd.outputs["View Distance"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.sensor_fit = "VERTICAL"; cam.data.clip_end = 8000
HAZE = os.environ.get("HAZEARGS", "90 620 0.5 #efecc6 #b4d4cc").split()
CAMS = {   # race-view axes: eye, look-at, field of view
    "across": ((722, 9, 41), (862, 1.0, -30), 37),      # the stand-side TV camera, looking up the course and across to the Dyke
    "track": ((772, 2.6, 41), (814, 2.6, -6), 38),       # the tracking car on the stand-side rail: the field against the Dyke
}


def treat(k):
    textured = k != "1"
    land.data.materials[0] = M["tex_lawn"] if textured else M["now_lawn"]
    track.data.materials[0] = M["tex_turf"] if textured else M["now_turf"]
    for o in BANKS: o.data.materials[0] = M["tex_bank"] if textured else M["now_bank"]
    verge.hide_render = not textured
    for md in (sub, dsp, dsp2): md.show_render = textured
    for md in SCATTERS: md.show_render = k == "3"
    FOLIAGE.hide_render = k != "3"
    TREES["now"].hide_render = textured; TREES["graded"].hide_render = not textured


def shoot(tag):
    base_path = os.path.join(OUTDIR, tag); scene.render.filepath = base_path + "_raw.png"; scene.render.image_settings.color_depth = "8"
    t = time.time(); bpy.ops.render.render(write_still=True)
    vl = scene.view_layers[0]; keep = (scene.cycles.samples, scene.view_settings.view_transform, scene.view_settings.look, wn["Background"].inputs[1].default_value)
    vl.material_override = dm; scene.cycles.samples = 6; scene.cycles.use_denoising = False; scene.view_settings.view_transform = "Raw"; scene.view_settings.look = "None"
    links = [(l.from_socket, l.to_socket) for l in wl if l.to_socket == wn["Background"].inputs[0]]
    for l in list(wl):
        if l.to_socket == wn["Background"].inputs[0]: wl.remove(l)
    wn["Background"].inputs[0].default_value = (1, 1, 1, 1); wn["Background"].inputs[1].default_value = 1
    scene.render.image_settings.color_depth = "16"; scene.render.filepath = base_path + "_dist.png"; bpy.ops.render.render(write_still=True)
    vl.material_override = None; scene.cycles.samples, scene.view_settings.view_transform, scene.view_settings.look = keep[:3]; scene.cycles.use_denoising = True
    for a_, b_ in links: wl.new(a_, b_)
    wn["Background"].inputs[1].default_value = keep[3]
    subprocess.run([sys.executable, rp("tools/blender/v2_post.py"), base_path] + HAZE, check=False, stdout=subprocess.DEVNULL)
    print("tile", tag, round(time.time() - t), "s", flush=True)


NAMES = {"1": "As it is now", "2": "Tone and texture", "3": "With low foliage"}
labels = {}
for cname in os.environ.get("CAMS", "across,track").split(","):
    eye, at, fov = CAMS[cname]; e, a = B(eye[0], eye[2], eye[1] + ground_y(eye[0], eye[2])), B(at[0], at[2], at[1] + ground_y(at[0], at[2]))
    cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler(); cam.data.angle_y = math.radians(fov)
    place_trees((eye[0], eye[2]))
    for k in ONLY:
        treat(k); shoot("%s_%s" % (cname, k)); labels["%s_%s" % (cname, k)] = NAMES[k]
json.dump(labels, open(os.path.join(OUTDIR, "labels.json"), "w"))
print("TOTAL", round(time.time() - T0), "s", flush=True)
