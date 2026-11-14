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
m, nt, b = mat("soft_bank"); p, s = pos(nt); h = attr(nt, "bank_h")
col = ramp(nt, rng(nt, h, 0, 1, 0, 5.4), [(0.0, "#8fa878"), (0.16, "#5f8562"), (0.5, "#7e9860"), (0.8, "#b1ab70"), (1.0, "#d2c68c")])
col = mul(nt, col, grey(nt, noise(nt, p, 0.3, 2, stretch=(0.3, 1.3, 1.0)), 0.92, 1.08, 0.3, 0.7))
col = mixc(nt, col, lin("#557c5a"), rng(nt, noise(nt, p, 0.05, 2), 0, 0.55, 0.5, 0.72))
nt.links.new(col, b.inputs["Base Color"]); M["soft_bank"] = warm_bounce(m)
# ---- one soft surface for all the ground (owner, 11 Nov: "a consistent softer texture"; the tussocks and bushes read
# as clumpy). No separate plants: one even, finely mottled surface on the turf, the land, the verge and the Dyke, only
# its colour changing. (A first try used a strong pale sheen: it washed every colour out to grey. No sheen now.)
# The nap (owner, 11 Nov, with a picture of brushed suede: "a soft flock with some depth, shadow and shape to it rather
# than lumps of round masses"). Suede's light and dark is its pile lying this way and that after a hand has brushed it:
# broad soft clouds with wispy edges, finer clouds inside them, and faint strokes along the brushing.
def nap_field(nt, vec, squeeze=None):
    if squeeze:                                                                                      # on the Dyke's face: smaller clouds, longer along the bank than up it
        mp = N_(nt, "ShaderNodeMapping"); mp.inputs["Scale"].default_value = squeeze; nt.links.new(vec, mp.inputs[0]); vec = mp.outputs[0]
    w = N_(nt, "ShaderNodeTexNoise"); w.inputs["Scale"].default_value = 0.04; w.inputs["Detail"].default_value = 2; nt.links.new(vec, w.inputs["Vector"])
    sb = N_(nt, "ShaderNodeVectorMath"); sb.operation = "SUBTRACT"; sb.inputs[1].default_value = (0.5, 0.5, 0.5); nt.links.new(w.outputs["Color"], sb.inputs[0])
    sc = N_(nt, "ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 14.0; nt.links.new(sb.outputs[0], sc.inputs[0])
    ad = N_(nt, "ShaderNodeVectorMath"); ad.operation = "ADD"; nt.links.new(vec, ad.inputs[0]); nt.links.new(sc.outputs[0], ad.inputs[1]); wv = ad.outputs[0]
    return noise(nt, wv, 0.11, 3), noise(nt, wv, 0.33, 2), noise(nt, wv, 1.4, 2, stretch=(0.25, 1.5, 1.0))


def nap_tone(nt, col, field, nap):
    a, b_, st = field
    col = mul(nt, col, grey(nt, a, 1 - nap, 1 + nap * 0.8, 0.36, 0.64)); col = mul(nt, col, grey(nt, b_, 1 - nap * 0.45, 1 + nap * 0.45, 0.3, 0.7))
    return mul(nt, col, grey(nt, st, 1 - nap * 0.25, 1 + nap * 0.25, 0.3, 0.7))


BANK_STOPS = [(0.0, "#8fa878"), (0.16, "#5f8562"), (0.5, "#7e9860"), (0.8, "#b1ab70"), (1.0, "#d2c68c")]
def flock(name, where, under=1.0, nap=0.0, relief=False):
    m, nt, b = mat(name); p, s = pos(nt); b.inputs["Roughness"].default_value = 1.0; b.inputs["Specular IOR Level"].default_value = 0.0
    if where == "bank":
        col = ramp(nt, rng(nt, attr(nt, "bank_h"), 0, 1, 0, 5.4), BANK_STOPS)
    elif where == "turf":
        col = mul(nt, lin("#86a872"), lanes(nt, s, 0.075))
        ay = N_(nt, "ShaderNodeMath"); ay.operation = "ADD"; ay.inputs[1].default_value = W / 2; nt.links.new(s.outputs["Y"], ay.inputs[0])
        ab = N_(nt, "ShaderNodeMath"); ab.operation = "ABSOLUTE"; nt.links.new(ay.outputs[0], ab.inputs[0]); col = mul(nt, col, grey(nt, ab.outputs[0], 1.06, 0.9, 0.0, W / 2))
    elif where == "verge":
        col = mixc(nt, lin("#98aa72"), lin("#bdb97e"), rng(nt, noise(nt, p, 0.05, 2), 0, 1, 0.4, 0.66))
    else:
        col = mixc(nt, lin("#a3b884"), lin("#c9c68c"), rng(nt, noise(nt, p, 0.006, 3), 0, 1, 0.38, 0.66))
        col = mixc(nt, col, lin("#86a274"), rng(nt, noise(nt, p, 0.017, 3), 0, 0.8, 0.48, 0.7))
        sw = N_(nt, "ShaderNodeMath"); sw.operation = "MULTIPLY"; sw.inputs[1].default_value = math.pi / 9.0; nt.links.new(s.outputs["Y"], sw.inputs[0])
        sn = N_(nt, "ShaderNodeMath"); sn.operation = "SINE"; nt.links.new(sw.outputs[0], sn.inputs[0]); col = mul(nt, col, grey(nt, sn.outputs[0], 0.95, 1.05, -0.3, 0.3))
    col = mul(nt, col, grey(nt, noise(nt, p, 0.02, 2), 0.93, 1.07, 0.3, 0.7))                       # broad, quiet drifts of tone
    k = 0.5 if where == "turf" else 1.0                                                              # the mown turf: the same grain, quieter
    g1 = noise(nt, p, 1.3, 2); g2 = noise(nt, p, 4.5, 2)                                             # the flock: a soft mottle, and a finer grain in it
    col = mul(nt, col, grey(nt, g1, 1 - 0.08 * k, 1 + 0.08 * k, 0.3, 0.7)); col = mul(nt, col, grey(nt, g2, 1 - 0.06 * k, 1 + 0.06 * k, 0.3, 0.7))
    if under != 1.0: col = mul(nt, col, grey(nt, s.outputs["Y"], 1.0, under, 0.3, 6.0))             # deeper under the pile, but not where it thins out to nothing at the turf
    add = N_(nt, "ShaderNodeMath"); add.operation = "ADD"; nt.links.new(g1, add.inputs[0]); nt.links.new(g2, add.inputs[1])
    bp = N_(nt, "ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5 * k; bp.inputs["Distance"].default_value = 0.12; nt.links.new(add.outputs[0], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if nap:
        nk = nap * (0.45 if where == "turf" else 1.0); field = nap_field(nt, p, (0.9, 2.2, 2.2) if where == "bank" else None); col = nap_tone(nt, col, field, nk)
        if relief and where != "turf":                                                             # the light clouds stand a little proud, and catch the light
            b2 = N_(nt, "ShaderNodeBump"); b2.inputs["Strength"].default_value = 0.7; b2.inputs["Distance"].default_value = 0.6
            nt.links.new(field[0], b2.inputs["Height"]); nt.links.new(b2.outputs["Normal"], bp.inputs["Normal"])
            b.inputs["Sheen Roughness"].default_value = 0.5; b.inputs["Sheen Tint"].default_value = lin("#dfe6b8"); nt.links.new(rng(nt, field[0], 0, 0.3, 0.45, 0.7), b.inputs["Sheen Weight"])
    nt.links.new(col, b.inputs["Base Color"])
    return warm_bounce(m)


FLOCK = {w: flock("flock_" + w, w) for w in ("bank", "turf", "verge", "land")}
UNDER = {w: flock("under_" + w, w, 0.8) for w in ("bank", "verge")}                                # the ground under a pile: a little deeper
NAP1 = {w: flock("nap1_" + w, w, nap=0.18) for w in ("bank", "turf", "verge", "land")}
NAP2 = {w: flock("nap2_" + w, w, nap=0.32, relief=True) for w in ("bank", "turf", "verge", "land")}
UNDER2 = {w: flock("under2_" + w, w, 0.8, nap=0.32, relief=True) for w in ("bank", "verge")}
SURF = {"6": FLOCK, "7": FLOCK, "8": FLOCK, "9": FLOCK, "10": NAP1, "11": NAP2, "12": NAP2}
UNDERS = {"7": UNDER, "8": UNDER, "9": UNDER, "12": UNDER2}
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
# The verge meets the turf with no step and no gap, and the flat ground casts no shadows (owner, 11 Nov: a thin dark line
# under the edge of the pile "makes it look like a rug"; it was a 3 cm step between the strips, in a low sun).
verge = grid_mesh("verge", [x for x in np.arange(X0 - 80, X1 + 80, 4.0)], [0.0, -3.5, -6.5, -9.5, -12.4], lambda x, z: ground_y(x, z) + 0.0, M["tex_verge"])
for o_ in (land, track, verge): o_.visible_shadow = False

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
    # The bank's mesh starts at the edge of the turf (a flat apron 12 m wide, then the Dyke). The swells must die away to
    # nothing towards the turf: they were lifting that edge into a lip with a dark side, which with grass on it looked
    # like the edge of a rug (owner, 11 Nov).
    vg = o.vertex_groups.new(name="swell")
    for i_, z_ in enumerate(r[..., 2].reshape(-1)):
        t_ = min(max((-float(z_) - 0.5) / 8.0, 0.0), 1.0); vg.add([i_], t_ * t_ * (3 - 2 * t_), "REPLACE")
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
dsp.vertex_group = "swell"; dsp2.vertex_group = "swell"
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


def scatter(target, inst_objs, density, smin, smax, seed, name, keep=True, slope=False, grow=None):
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
    GL.new(gi.outputs[0], dist.inputs["Mesh"]); GL.new(ci.outputs[0], inst.inputs["Instance"])
    if slope:
        st = Gn.new("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT_VECTOR"; st.domain = "POINT"; st.inputs["Name"].default_value = "gn"
        GL.new(dist.outputs["Points"], st.inputs["Geometry"]); GL.new(dist.outputs["Normal"], st.inputs["Value"]); GL.new(st.outputs[0], inst.inputs["Points"])
    else: GL.new(dist.outputs["Points"], inst.inputs["Points"])
    GL.new(rr.outputs[0], inst.inputs["Rotation"])
    if grow:                                    # (from, to) across the course: the pile grows up out of the turf instead of starting in a line
        ps = Gn.new("GeometryNodeInputPosition"); sp = Gn.new("ShaderNodeSeparateXYZ"); mr = Gn.new("ShaderNodeMapRange"); mr.interpolation_type = "SMOOTHSTEP"
        mr.inputs["From Min"].default_value = grow[0]; mr.inputs["From Max"].default_value = grow[1]; mr.inputs["To Min"].default_value = 0.12; mr.inputs["To Max"].default_value = 1.0
        mu = Gn.new("ShaderNodeMath"); mu.operation = "MULTIPLY"
        GL.new(ps.outputs[0], sp.inputs[0]); GL.new(sp.outputs["Y"], mr.inputs["Value"]); GL.new(mr.outputs["Result"], mu.inputs[0]); GL.new(rs.outputs[0], mu.inputs[1]); GL.new(mu.outputs[0], inst.inputs["Scale"])
    else: GL.new(rs.outputs[0], inst.inputs["Scale"])
    if keep: GL.new(gi.outputs[0], join.inputs[0])
    GL.new(inst.outputs[0], join.inputs[0]); GL.new(join.outputs[0], go.inputs[0])
    md = target.modifiers.new(name, "NODES"); md.node_group = ng; return md


def small(name, me, material):
    me.materials.append(material); o = bpy.data.objects.new(name, me); return o


GRASS_M = blade_material("long_grass", "#6f8a5c", "#c9c890", ["#ffffff", "#f0f4dc", "#fff4d0", "#e4eed8", "#f6e8c4"])
PARSLEY_M = blade_material("parsley", "#7f9a6a", "#f4f0e2", ["#ffffff", "#fbf6e6", "#f4f8ec"])
FLOWER_M = blade_material("flowers", "#7f9a6a", "#e8c85a", ["#ffffff", "#ffe9d8", "#f0b0a0", "#ffffff", "#e6d0f0"])
tufts = [small("tuft_a", tuft_mesh("tuft_a", 9, 0.55, 0.035, 0.22), GRASS_M), small("tuft_b", tuft_mesh("tuft_b", 13, 0.8, 0.04, 0.3), GRASS_M),
         small("tuft_c", tuft_mesh("tuft_c", 7, 0.4, 0.03, 0.16), GRASS_M)]
blooms = [small("bloom_a", tuft_mesh("bloom_a", 6, 0.75, 0.055, 0.12), PARSLEY_M), small("bloom_b", tuft_mesh("bloom_b", 5, 0.45, 0.05, 0.1), FLOWER_M)]
SCATTERS = {"3": [scatter(bank, tufts, 1.7, 0.8, 1.7, 3, "bank_grass"), scatter(bank, blooms, 0.16, 0.8, 1.5, 9, "bank_bloom"),
                  scatter(verge, tufts, 2.6, 0.7, 1.4, 5, "verge_grass"), scatter(verge, blooms, 0.3, 0.8, 1.4, 11, "verge_bloom")]}


def soften(m):
    """Shade it as if it faced straight up, like the ground under it: no bright and dark sides to each blade or lump."""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; up = N_(nt, "ShaderNodeCombineXYZ"); up.inputs["Z"].default_value = 1.0
    nrm = N_(nt, "ShaderNodeNewGeometry"); mixn = N_(nt, "ShaderNodeMix"); mixn.data_type = "VECTOR"; mixn.inputs["Factor"].default_value = 0.8
    nt.links.new(nrm.outputs["Normal"], mixn.inputs[4]); nt.links.new(up.outputs[0], mixn.inputs[5]); nt.links.new(mixn.outputs[1], b.inputs["Normal"])
    b.inputs["Subsurface Weight"].default_value = 0.0
    return m


def tussock_mesh(name, seed):
    r = random.Random(seed); bm = bmesh.new()
    for k in range(r.choice([2, 3, 3])):
        rad = r.uniform(0.3, 0.5); g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=rad, matrix=Matrix.Translation((r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), rad * 0.25)) @ Matrix.Diagonal((1.15, 1.15, 0.7, 1)))
    for v in bm.verts: v.co.z = max(v.co.z, -0.05)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me


def dots_mesh(name, seed, n, height):
    r = random.Random(seed); bm = bmesh.new()
    for k in range(n):
        x, y, z = r.uniform(-0.25, 0.25), r.uniform(-0.25, 0.25), height * r.uniform(0.7, 1.1)
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r.uniform(0.07, 0.11), matrix=Matrix.Translation((x, y, z)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p_ in me.polygons: p_.use_smooth = True
    return me


SOFT_GRASS = soften(blade_material("soft_grass", "#84a070", "#b6bd8a", ["#ffffff", "#f4f6e6", "#fff8e0", "#ecf2e2", "#f8eed6"]))
SOFT_MOUND = soften(blade_material("soft_mound", "#7c9a6c", "#b3bd88", ["#ffffff", "#f2f5e2", "#fff6da", "#e8f0e0", "#f6ead2", "#eef0d0"]))
DOT_W = soften(blade_material("dot_white", "#f4f0e4", "#f8f4ea", ["#ffffff", "#fbf6e8"])); DOT_Y = soften(blade_material("dot_colour", "#e6cc6c", "#ecd47a", ["#ffffff", "#ffe6dc", "#f0c0b0", "#ffffff"]))
soft_tufts = [small("stuft_a", tuft_mesh("stuft_a", 6, 0.34, 0.085, 0.2), SOFT_GRASS), small("stuft_b", tuft_mesh("stuft_b", 8, 0.46, 0.1, 0.28), SOFT_GRASS)]
mounds = [small("mound_%d" % k, tussock_mesh("mound_%d" % k, 30 + k), SOFT_MOUND) for k in range(3)]
dots = [small("dots_w", dots_mesh("dots_w", 5, 5, 0.6), DOT_W), small("dots_y", dots_mesh("dots_y", 6, 4, 0.4), DOT_Y)]
# (broad blades shaded like the ground came out dark and spiky where they shade each other: not used)
# 4: mostly tussocks, with a light scatter of the fine grass between them
SCATTERS["4"] = [scatter(bank, mounds, 0.3, 0.7, 1.5, 3, "bank_mound4"), scatter(bank, tufts, 0.4, 0.8, 1.5, 4, "bank_fine4"), scatter(bank, dots, 0.08, 0.8, 1.4, 9, "bank_dots4"),
                 scatter(verge, mounds, 0.42, 0.6, 1.2, 5, "verge_mound4"), scatter(verge, tufts, 0.6, 0.7, 1.3, 6, "verge_fine4"), scatter(verge, dots, 0.14, 0.8, 1.3, 11, "verge_dots4")]
SCATTERS["5"] = [scatter(bank, mounds, 0.42, 0.7, 1.5, 3, "bank_mound"), scatter(bank, dots, 0.1, 0.8, 1.4, 9, "bank_dots5"),
                 scatter(verge, mounds, 0.6, 0.6, 1.2, 5, "verge_mound"), scatter(verge, dots, 0.18, 0.8, 1.3, 11, "verge_dots5")]

# thorn scrub on the Dyke: clumps on its face and along the crest, thinner at its foot; the odd small thorn tree on top
# ---------------- the soft pile (treatments 7 to 9): one even coat of soft grass over the Dyke and the verge.
# What made the fine grass scratchy was thin blades standing apart, each with a bright and a dark side and a hard little
# shadow. Here the blades are broad and close, cover the ground completely, are lit exactly as the ground under them is
# (each copy is handed the slope it stands on) and cast no shadows; only root-to-tip tone and a little copy-to-copy tone
# are left. It reads as a nap, like the pile of a rug.
PILE = collection("pile")
def pile_mesh(name, blades, radius, height, width, lean, seed):
    r = random.Random(seed); bm = bmesh.new()
    for i in range(blades):
        pa = r.uniform(0, 6.283); d = radius * math.sqrt(r.uniform(0, 1)); a = r.uniform(0, 6.283)
        h = height * r.uniform(0.82, 1.1); l = lean * r.uniform(0.4, 1.2); w = width * r.uniform(0.8, 1.2)
        c, s_ = math.cos(a), math.sin(a); base = Vector((math.cos(pa) * d, math.sin(pa) * d, 0)); side = Vector((-s_, c, 0)) * w
        rows = [(0.0, 1.0), (0.5, 0.95), (0.82, 0.62)]
        vs = [(bm.verts.new(base + Vector((c * l * t * t, s_ * l * t * t, h * t)) - side * k), bm.verts.new(base + Vector((c * l * t * t, s_ * l * t * t, h * t)) + side * k)) for t, k in rows]
        tip = bm.verts.new(base + Vector((c * l, s_ * l, h)))
        for (a0, b0), (a1, b1) in zip(vs, vs[1:]): bm.faces.new((a0, b0, b1, a1))
        bm.faces.new((vs[-1][0], vs[-1][1], tip))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me


def pile_material(name, where, wash, nap=0.0):
    m, nt, b = mat(name); b.inputs["Roughness"].default_value = 1.0; b.inputs["Specular IOR Level"].default_value = 0.0
    oi = N_(nt, "ShaderNodeObjectInfo"); ip = oi.outputs["Location"]                                 # where this copy stands
    if where == "bank":
        ia = N_(nt, "ShaderNodeAttribute"); ia.attribute_type = "INSTANCER"; ia.attribute_name = "bank_h"
        col = ramp(nt, rng(nt, ia.outputs["Fac"], 0, 1, 0, 5.4), BANK_STOPS)
    else:
        col = mixc(nt, lin("#98aa72"), lin("#bdb97e"), rng(nt, noise(nt, ip, 0.05, 2), 0, 1, 0.4, 0.66))
    col = mul(nt, col, grey(nt, noise(nt, ip, 0.02, 2), 0.93, 1.07, 0.3, 0.7))
    if nap: col = nap_tone(nt, col, nap_field(nt, ip, (0.9, 2.2, 2.2) if where == "bank" else None), nap)
    if wash:
        col = mixc(nt, col, lin("#d3c688"), rng(nt, noise(nt, ip, 0.035, 2), 0, 0.6, 0.5, 0.68))        # straw
        col = mixc(nt, col, lin("#5f8562"), rng(nt, noise(nt, ip, 0.05, 2), 0, 0.5, 0.56, 0.72))        # deeper green
        for hexc, sc, off in (("#e6d684", 0.07, 3.1), ("#d9b0aa", 0.055, 7.7), ("#e6e8d2", 0.09, 12.3)):   # buttercup, clover, ox-eye: drifts, not dots
            mp = N_(nt, "ShaderNodeMapping"); mp.inputs["Location"].default_value = (off * 40, off * 23, 0); nt.links.new(ip, mp.inputs[0])
            col = mixc(nt, col, lin(hexc), rng(nt, noise(nt, mp.outputs[0], sc, 2), 0, 0.32, 0.58, 0.74))
    tcn = N_(nt, "ShaderNodeTexCoord"); sz = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Generated"], sz.inputs[0])
    col = mul(nt, col, grey(nt, sz.outputs["Z"], 0.7, 1.04, 0.0, 0.9))                               # deeper at the root, paler at the tip
    col = mixc(nt, col, lin("#dedaa6"), rng(nt, sz.outputs["Z"], 0, 0.1, 0.5, 1.0))
    col = mul(nt, col, grey(nt, oi.outputs["Random"], 0.955, 1.045))
    # lit as the ground is, whichever way the blade faces: one layer answers light arriving on the side we see, the
    # other light arriving on the far side and coming through, both measured against the slope of the ground beneath
    gn = N_(nt, "ShaderNodeAttribute"); gn.attribute_type = "INSTANCER"; gn.attribute_name = "gn"
    neg = N_(nt, "ShaderNodeVectorMath"); neg.operation = "SCALE"; neg.inputs["Scale"].default_value = -1.0; nt.links.new(gn.outputs["Vector"], neg.inputs[0])
    df = N_(nt, "ShaderNodeBsdfDiffuse"); tr = N_(nt, "ShaderNodeBsdfTranslucent"); ad = N_(nt, "ShaderNodeAddShader")
    nt.links.new(col, df.inputs["Color"]); nt.links.new(col, tr.inputs["Color"]); nt.links.new(gn.outputs["Vector"], df.inputs["Normal"]); nt.links.new(neg.outputs[0], tr.inputs["Normal"])
    nt.links.new(df.outputs[0], ad.inputs[0]); nt.links.new(tr.outputs[0], ad.inputs[1]); nt.links.new(ad.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    m.use_backface_culling = False
    return m


def pile(target, where, wash, density, smin, smax, seed, name, lean=0.17, nap=0.0):
    o = target.copy(); o.name = name; PILE.objects.link(o)
    for md in [md for md in o.modifiers if md.type == "NODES"]: o.modifiers.remove(md)
    for md in o.modifiers:
        md.show_render = True
        if md.name == "lumps": md.strength = 0.9
        if md.name == "ripple": md.strength = 0.0
    mat_ = pile_material(name + "_m", where, wash, nap)
    kit = [small("%s_%d" % (name, i), pile_mesh("%s_%d" % (name, i), 40, 0.38, 0.36, 0.042, lean, seed * 10 + i), mat_) for i in range(3)]
    scatter(o, kit, density, smin, smax, seed, name, keep=False, slope=True, grow=(0.3, 6.0))
    o.visible_shadow = False
    return o


PILES = {"7": [pile(bank, "bank", False, 10.0, 0.5, 0.7, 3, "pile_short_bank")],
         "8": [pile(bank, "bank", False, 5.0, 0.95, 1.3, 3, "pile_long_bank", 0.3)],
         "9": [pile(bank, "bank", True, 5.0, 0.95, 1.3, 3, "pile_wash_bank", 0.3)],
         "12": [pile(bank, "bank", False, 10.0, 0.5, 0.7, 3, "pile_nap_bank", nap=0.32)]}


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
    "track": ((772, 2.6, 41), (814, 2.6, -6), 38),
    "close": ((768, 2.3, 9), (840, 1.6, -13), 40),       # a low camera on the course, the field coming towards it: the verge and the Dyke close by       # the tracking car on the stand-side rail: the field against the Dyke
}


def treat(k):
    textured = k != "1"; soft = k in SURF; piled = k in PILES; F = SURF.get(k); U = UNDERS.get(k)
    land.data.materials[0] = F["land"] if soft else M["tex_lawn"] if textured else M["now_lawn"]
    track.data.materials[0] = F["turf"] if soft else M["tex_turf"] if textured else M["now_turf"]
    for o in BANKS: o.data.materials[0] = F["bank"] if soft else M["soft_bank"] if k in ("4", "5") else M["tex_bank"] if textured else M["now_bank"]
    if piled: bank.data.materials[0] = U["bank"]
    verge.data.materials[0] = F["verge"] if soft else M["tex_verge"]      # not darkened under its pile: where the pile thins out towards the rail a darker ground read as a shadow
    verge.hide_render = (not textured) or soft       # with the soft surfaces the bank's own flat apron is the verge
    for md in (sub, dsp, dsp2): md.show_render = textured
    for key, mds in SCATTERS.items():
        for md in mds: md.show_render = key == k
    for key, objs in PILES.items():
        for o in objs: o.hide_render = key != k
    FOLIAGE.hide_render = k not in ("3", "4", "5")
    dsp2.strength = 0.0 if soft else 0.12 if k in ("4", "5") else 0.28          # the soft surfaces: big gentle swells only
    dsp.strength = 0.9 if soft else 1.1
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


NAMES = {"1": "As it is now", "2": "Tone and texture", "3": "With low foliage", "4": "Softer: tussocks with a little fine grass", "5": "Softest: rounded tussocks",
         "6": "Soft flock: texture only", "7": "Short soft pile", "8": "Long soft pile", "9": "Long soft pile, washes of colour",
         "10": "Brushed flock, quiet", "11": "Brushed flock, deeper", "12": "Brushed flock, deeper, with a short pile on the Dyke"}
labels = {}
for cname in os.environ.get("CAMS", "across,track").split(","):
    eye, at, fov = CAMS[cname]; e, a = B(eye[0], eye[2], eye[1] + ground_y(eye[0], eye[2])), B(at[0], at[2], at[1] + ground_y(at[0], at[2]))
    cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler(); cam.data.angle_y = math.radians(fov)
    place_trees((eye[0], eye[2]))
    for k in ONLY:
        treat(k); shoot("%s_%s" % (cname, k)); labels["%s_%s" % (cname, k)] = NAMES[k]
json.dump(labels, open(os.path.join(OUTDIR, "labels.json"), "w"))
print("TOTAL", round(time.time() - T0), "s", flush=True)
