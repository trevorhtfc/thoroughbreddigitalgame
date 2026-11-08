"""A quick look at the Rowley Mile's stand-side architecture in place (8 Nov 2026), before the full Rowley Mile scene.

    python -c "exec(open('tools/blender/preview_rowley_stands.py').read())"      (SHOTS=, SAMPLES=, RES=)

Flat ground (the full scene will bring the Dip and the bank): Ascot's turf and lawn, the Ascot rail, the finish-line
assembly on the far rail at the post, the pieces from rowley_stands.glb where draft_layout.STAND_PIECES puts them, a
crowd on their terraces and the lawn, a backdrop of clay trees, the July build's light. Stills go to
reference/newmarket/renders/.
"""
import os, sys, json, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix

REPO = os.path.abspath(os.environ.get("REPO", "."))
sys.path.insert(0, os.path.join(REPO, "tools/course/newmarket"))
import draft_layout as R
OUT = os.path.join(REPO, "reference/newmarket/renders"); os.makedirs(OUT, exist_ok=True)
SAMPLES = int(os.environ.get("SAMPLES", "24"))
SHOTS = [s for s in os.environ.get("SHOTS", "across,across_up,post,track,aerial,plan").split(",") if s]
RES = [int(v) for v in os.environ.get("RES", "1280x720").split("x")]
W = R.TRACK_W
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def srgb(h):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


def flat(name, hexc, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = srgb(hexc); b.inputs["Roughness"].default_value = rough
    return m


def clayify(m, sss=0.12):
    nt = m.node_tree; b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None: return m
    b.inputs["Roughness"].default_value = 0.92; b.inputs["Metallic"].default_value = 0.0; b.inputs["Specular IOR Level"].default_value = 0.12
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.09, 0.06, 0.04); b.inputs["Subsurface Scale"].default_value = 0.05
    tc = nt.nodes.new("ShaderNodeTexCoord"); fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 9.0
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(fine.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def soften(ob, width=0.05):
    for p in ob.data.polygons: p.use_smooth = True
    bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = width; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
    bv.use_clamp_overlap = True; bv.harden_normals = True
    ob.modifiers.new("wn", "WEIGHTED_NORMAL").keep_sharp = True


def B(x, z, y=0.0): return (x, -z, y)


def load(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, path))
    new = [o for o in bpy.data.objects if o not in before]
    mw = {o: o.matrix_world.copy() for o in new}
    for o in new: o.parent = None
    for o in new:
        if o.type == "MESH": o.data.transform(mw[o]); o.matrix_world = Matrix.Identity(4)
    out = {}
    for o in [o for o in new if o.type == "MESH"]:
        o.hide_render = True; o.hide_viewport = True; out[o.name.split(".")[0]] = o
    return out


def place(src, x, z, turn=0.0, scale=1.0, name=None):
    ob = bpy.data.objects.new(name or src.name + "_i", src.data); ob.location = Vector(B(x, z, 0.0))
    ob.rotation_euler = (0, 0, math.radians(turn)); ob.scale = (scale, scale, scale)
    scene.collection.objects.link(ob); return ob


def instances(name, objs, xyz, idx, rot, scl):
    coll = bpy.data.collections.new(name + "_lib")
    for o in sorted(objs, key=lambda o: o.name): coll.objects.link(o)
    me = bpy.data.meshes.new(name); n = len(xyz); me.vertices.add(n); me.vertices.foreach_set("co", np.asarray(xyz, np.float32).ravel())
    for nm, typ, val in (("idx", "INT", idx), ("rot", "FLOAT", rot), ("scl", "FLOAT", scl)):
        a = me.attributes.new(nm, typ, "POINT"); a.data.foreach_set("value", np.asarray(val, np.int32 if typ == "INT" else np.float32))
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nd, ln = ng.nodes, ng.links; gi, go = nd.new("NodeGroupInput"), nd.new("NodeGroupOutput")
    ci = nd.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = coll
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    iop = nd.new("GeometryNodeInstanceOnPoints"); iop.inputs["Pick Instance"].default_value = True
    def named(nm, typ):
        a = nd.new("GeometryNodeInputNamedAttribute"); a.data_type = typ; a.inputs["Name"].default_value = nm; return a.outputs["Attribute"]
    rz = nd.new("ShaderNodeCombineXYZ"); ln.new(named("rot", "FLOAT"), rz.inputs["Z"])
    ln.new(gi.outputs[0], iop.inputs["Points"]); ln.new(ci.outputs[0], iop.inputs["Instance"])
    ln.new(named("idx", "INT"), iop.inputs["Instance Index"]); ln.new(rz.outputs[0], iop.inputs["Rotation"])
    ln.new(named("scl", "FLOAT"), iop.inputs["Scale"]); ln.new(iop.outputs[0], go.inputs[0])
    ob.modifiers.new(name, "NODES").node_group = ng
    return ob


# ---- ground: the light lawn with beige beside the track, the track's turf in lanes, the cut strip at the post
def plane(name, x0, x1, z0, z1, mat, y=0.0):
    me = bpy.data.meshes.new(name); me.from_pydata([B(x0, z0, y), B(x1, z0, y), B(x1, z1, y), B(x0, z1, y)], [], [(0, 3, 2, 1)])
    me.materials.append(mat); ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); return ob


def grass_mat(name, hexc, lanes=False, beige=False):
    m = flat(name, hexc, 0.97); nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    col = srgb(hexc); last = None
    def layer(scale, lo, hi, inp=None):
        nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
        L.new(tc.outputs["Object"], nz.inputs["Vector"])
        r = N.new("ShaderNodeMapRange"); L.new(nz.outputs["Fac"], r.inputs["Value"]); r.inputs["From Min"].default_value = 0.3; r.inputs["From Max"].default_value = 0.7
        r.inputs["To Min"].default_value = lo; r.inputs["To Max"].default_value = hi; return r.outputs["Result"]
    f = N.new("ShaderNodeMath"); f.operation = "MULTIPLY"; L.new(layer(0.08, 0.88, 1.1), f.inputs[0]); L.new(layer(2.2, 0.85, 1.1), f.inputs[1])
    g = N.new("ShaderNodeMath"); g.operation = "MULTIPLY"; L.new(f.outputs[0], g.inputs[0]); L.new(layer(18.0, 0.85, 1.1), g.inputs[1]); fac = g.outputs[0]
    if lanes:   # lanes along the straight: Blender y = -course z
        a = N.new("ShaderNodeMath"); a.operation = "MULTIPLY"; L.new(sep.outputs["Y"], a.inputs[0]); a.inputs[1].default_value = math.pi / 3.75
        sn = N.new("ShaderNodeMath"); sn.operation = "SINE"; L.new(a.outputs[0], sn.inputs[0])
        r = N.new("ShaderNodeMapRange"); L.new(sn.outputs[0], r.inputs["Value"]); r.inputs["From Min"].default_value = -0.3; r.inputs["From Max"].default_value = 0.3
        r.inputs["To Min"].default_value = 0.86; r.inputs["To Max"].default_value = 1.13
        h = N.new("ShaderNodeMath"); h.operation = "MULTIPLY"; L.new(fac, h.inputs[0]); L.new(r.outputs["Result"], h.inputs[1]); fac = h.outputs[0]
        # the cut strip at the post: a shade paler
        ax = N.new("ShaderNodeMath"); ax.operation = "ABSOLUTE"; L.new(sep.outputs["X"], ax.inputs[0])
        cs = N.new("ShaderNodeMapRange"); L.new(ax.outputs[0], cs.inputs["Value"]); cs.inputs["From Min"].default_value = 0.45; cs.inputs["From Max"].default_value = 1.1
        cs.inputs["To Min"].default_value = 1.35; cs.inputs["To Max"].default_value = 1.0
        h2 = N.new("ShaderNodeMath"); h2.operation = "MULTIPLY"; L.new(fac, h2.inputs[0]); L.new(cs.outputs["Result"], h2.inputs[1]); fac = h2.outputs[0]
    cc = N.new("ShaderNodeCombineColor"); [L.new(fac, cc.inputs[k]) for k in ("Red", "Green", "Blue")]
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
    if beige:   # beige-brown within ~45 m of the track, the light lawn by 85 m
        ay = N.new("ShaderNodeMath"); ay.operation = "ADD"; L.new(sep.outputs["Y"], ay.inputs[0]); ay.inputs[1].default_value = W / 2
        ab = N.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; L.new(ay.outputs[0], ab.inputs[0])
        mk = N.new("ShaderNodeMapRange"); L.new(ab.outputs[0], mk.inputs["Value"]); mk.inputs["From Min"].default_value = W / 2 + 45; mk.inputs["From Max"].default_value = W / 2 + 85
        mk.inputs["To Min"].default_value = 1.0; mk.inputs["To Max"].default_value = 0.0
        bm = N.new("ShaderNodeMix"); bm.data_type = "RGBA"; L.new(mk.outputs["Result"], bm.inputs["Factor"])
        bm.inputs[6].default_value = col; bm.inputs[7].default_value = srgb("#cdb894"); L.new(bm.outputs[2], mx.inputs[6])
    else:
        mx.inputs[6].default_value = col
    L.new(cc.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    out = N["Material Output"]; lp = N.new("ShaderNodeLightPath"); d = N.new("ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = srgb("#a29680")
    ms = N.new("ShaderNodeMixShader"); L.new(lp.outputs["Is Camera Ray"], ms.inputs["Fac"]); L.new(d.outputs[0], ms.inputs[1]); L.new(b.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], out.inputs["Surface"])
    return m


plane("lawn", -900, 1400, -500, 700, grass_mat("lawn", "#bcc98c", beige=True), -0.02)
plane("track", -R.RUN_ON - 200, 1400, 0, W, grass_mat("turf", "#7fa952", lanes=True), 0.0)

# ---- the Ascot rail on both sides
rail_m = clayify(flat("rail", "#f4f2ec", 0.5), 0)
def rail(z, out):
    bm = bmesh.new(); x0, x1 = -R.RUN_ON - 200, 1400
    prof = [(-0.02, 0.86), (-0.02, 1.12), (0.02, 1.17), (0.10, 1.18), (0.18, 1.15), (0.18, 1.10), (0.07, 1.10), (0.07, 0.86)]
    a = [bm.verts.new(B(x0, z + out * u, w)) for u, w in prof]; b_ = [bm.verts.new(B(x1, z + out * u, w)) for u, w in prof]
    n = len(prof)
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b_[(i + 1) % n], b_[i]))
    x = x0
    while x < x1:
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(B(x, z + out * 0.14, 0.55)) @ Matrix.Diagonal((0.1, 0.1, 1.1, 1)))
        x += 2.4
    me = bpy.data.meshes.new("rail"); bm.to_mesh(me); bm.free(); me.materials.append(rail_m)
    scene.collection.objects.link(bpy.data.objects.new("rail", me))
rail(0.0, -1); rail(W, +1)

# ---- the finish-line assembly on the far (inside) rail at the post, facing the stands
fl = load("assets/models/architecture/finish_line.glb")["finish_line"]
for sl in fl.material_slots: clayify(sl.material)
place(fl, 0.0, 0.0, 0.0)
props = load("assets/models/course/course_props.glb")
for k in range(1, 5): place(props["furlong_%d" % k], k * R.F, W + 0.9, 180.0)

# ---- the stand side's buildings
jsp = load("assets/models/architecture/rowley_stands.glb")
info = json.load(open(os.path.join(REPO, "assets/models/architecture/rowley_stands.json")))["pieces"]
for m in {sl.material for o in jsp.values() for sl in o.material_slots if sl.material}:
    clayify(m, 0.0 if m.name.split(".")[0] in ("rm_glass", "rm_iron", "rm_bench") else 0.12)
people, nogo = [], []
rnd = random.Random(4)
from matplotlib.path import Path as MPath
for st in R.STAND_PIECES:
    pi = info[st["piece"]]; off = pi.get("offset", 0.0)
    if "turn" in st:
        ox, oz, turn = st["at"][0], W + st["at"][1], st["turn"]
    else:
        ox, oz, turn = sum(st["x"]) / 2, W + st["front"], 180.0
    ob = place(jsp[st["piece"]], ox, oz, turn, name=st["name"]); soften(ob)
    a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    to_c = lambda u, v: (ox + u * ca - v * sa, oz - (u * sa + v * ca))
    hw = pi["width"] / 2
    nogo.append(MPath(np.array([to_c(u, v) for u, v in ((-hw + off, -8.0), (hw + off, -8.0), (hw + off, pi["depth"] + 2), (-hw + off, pi["depth"] + 2))])))
    for x0, x1, y0, y1, fz in pi["crowd"]:
        for _ in range(int((x1 - x0) * (y1 - y0) * 1.5)):
            people.append(to_c(rnd.uniform(x0, x1), rnd.uniform(y0, y1)) + (fz, turn))
# the lawn between the stands and the rail
for _ in range(int(560 * 34 * 0.3)):                                  # the lawns in front of the stands, down to the rail
    x, z = rnd.uniform(-60, 500), rnd.uniform(W + 2, W + 36)
    if not any(q.contains_point((x, z)) for q in nogo):
        people.append((x, z, 0.0, 180.0))
cr = load("assets/models/architecture/crowd_set_8.glb")
SKC = {"clothes": ["#2c3140", "#3a3d44", "#4b4d52", "#2f3a33", "#59544c", "#c9a0a8", "#9fb6c8", "#ddd2b8", "#a8706a", "#88a383", "#d2b874", "#e8e2d6", "#9a88b4", "#cf9476"],
       "hats": ["#222226", "#efe6d2", "#d8c08a", "#c9a0a8", "#9fb6c8"], "skin": ["#efc6a4", "#e2b48e", "#c99572", "#9a6a4a"]}
var = []; rv = random.Random(3)
for f in sorted(cr):
    for v in range(4):
        me = cr[f].data.copy()
        for i, mat in enumerate(me.materials):
            key = {"fig_main": "clothes", "fig_hat": "hats", "fig_skin": "skin"}.get(mat.name.split(".")[0])
            if key: me.materials[i] = flat("%s_%s_%d" % (f, key, v), rv.choice(SKC[key]), 0.85)
        var.append(bpy.data.objects.new("%s_%d" % (f, v), me))
instances("crowd", var, [B(x, z, h) for x, z, h, _ in people], [rnd.randrange(len(var)) for _ in people],
          [math.radians(t + rnd.uniform(-30, 30)) for *_, t in people], [rnd.uniform(0.95, 1.06) for _ in people])

# ---- a backdrop of clay trees behind the stands and across the heath beyond the far rail
tr = load("assets/models/trees/trees_clay.glb"); leafs = json.load(open(os.path.join(REPO, "assets/models/trees/trees_clay.json")))
kinds = sorted(["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]); LEAF = [leafs["leaf"][i] for i in (0, 1, 3, 6)]
crowns = []
for k in kinds:
    for li, hx in enumerate(LEAF):
        me = tr[k + "_crown"].data.copy(); m = bpy.data.materials.new("leaf_%s_%d" % (k, li)); m.use_nodes = True; nt = m.node_tree
        vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Color"; mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = "RGBA"; mm.blend_type = "MULTIPLY"
        mm.inputs["Factor"].default_value = 1.0; nt.links.new(vc.outputs["Color"], mm.inputs["A"]); mm.inputs["B"].default_value = tuple(v * leafs["shadeMax"] for v in srgb(hx)[:3]) + (1,)
        nt.links.new(mm.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Base Color"]); me.materials.clear(); me.materials.append(m)
        crowns.append(bpy.data.objects.new("%s_%d" % (k, li), me))
trunks = [bpy.data.objects.new(k + "_t", tr[k + "_trunk"].data) for k in kinds]
bark = flat("bark", "#7a6650"); [o.data.materials.__setitem__(0, bark) for o in trunks]
T = []
for x in np.arange(-130, 520, 11):                                    # behind the stands, clear of their backs
    back = 112.0 if x < 105 else 78.0
    T.append((x + rnd.uniform(-3, 3), W + rnd.uniform(back, back + 16), rnd.randrange(5), rnd.uniform(1.9, 2.5)))
for x in np.arange(-200, 900, 16):                                    # across the heath beyond the far rail
    T.append((x + rnd.uniform(-5, 5), -rnd.uniform(70, 140), rnd.randrange(5), rnd.uniform(1.4, 2.2)))
instances("crowns", crowns, [B(x, z, -0.2) for x, z, *_ in T], [k * 4 + rnd.randrange(4) for _, _, k, _ in T],
          [rnd.uniform(0, 6.28) for _ in T], [s for *_, s in T])
instances("trunks", trunks, [B(x, z, -0.2) for x, z, *_ in T], [k for _, _, k, _ in T], [0.0] * len(T), [s for *_, s in T])

# ---- light: the July Course's pastel sky and warm sun
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sp = wn.new("ShaderNodeSeparateXYZ"); wl.new(tc.outputs["Generated"], sp.inputs[0])
sky = wn.new("ShaderNodeValToRGB"); el = sky.color_ramp.elements
el[0].position, el[0].color = 0.0, (1.0, 0.87, 0.76, 1); el[1].position, el[1].color = 0.42, (0.36, 0.55, 0.86, 1)
e = el.new(0.02); e.color = (0.84, 0.87, 0.92, 1); e = el.new(0.1); e.color = (0.55, 0.7, 0.93, 1)
wl.new(sp.outputs["Z"], sky.inputs[0]); wl.new(sky.outputs[0], wn["Background"].inputs["Color"])
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 4.6; sun.data.angle = math.radians(14); sun.data.color = (1.0, 0.8, 0.62)
to_sun = Vector((0.55, -0.8, 0.0)).normalized() * math.cos(math.radians(32)) + Vector((0, 0, math.sin(math.radians(32))))
sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()

CAMS = {   # course (x, z, height) from and to, lens
    "across": ((30.0, -3.0, 6.0), (30.0, 95.0, 20.0), 20),            # from the far rail, at the Millennium
    "across_up": ((165.0, -3.0, 6.0), (160.0, 90.0, 12.0), 22),      # at the old stand
    "post": ((70.0, 8.0, 8.0), (-60.0, 52.0, 12.0), 24),             # from the track before the line, at the end stand
    "track": ((-40.0, 10.0, 9.0), (150.0, 75.0, 16.0), 28),          # up the straight from just past the post
    "aerial": ((60.0, -190.0, 160.0), (60.0, 60.0, 0.0), 26),        # high over the far side
    "plan": ((65.0, 60.0, 500.0), (65.0, 60.0001, 0.0), 0),          # straight down (orthographic), to mark up
}
scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
scene.cycles.max_bounces = 4
scene.render.resolution_x, scene.render.resolution_y = RES
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.view_settings.exposure = 0.12
import time
for s in SHOTS:
    (fx, fz, fy), (tx, tz, ty), lens = CAMS[s]
    cam = bpy.data.objects.new(s, bpy.data.cameras.new(s)); cam.data.lens = lens or 50; cam.data.clip_end = 5000
    if s == "plan":
        cam.data.type = "ORTHO"; cam.data.ortho_scale = 400.0
        scene.render.resolution_x, scene.render.resolution_y = 2400, 1200
    else:
        scene.render.resolution_x, scene.render.resolution_y = RES
    scene.collection.objects.link(cam)
    frm, to = Vector(B(fx, fz, fy)), Vector(B(tx, tz, ty)); cam.location = frm
    cam.rotation_euler = (to - frm).to_track_quat("-Z", "Y").to_euler(); scene.camera = cam
    scene.render.filepath = os.path.join(OUT, s + ".png"); t0 = time.time()
    bpy.ops.render.render(write_still=True); print("rendered", s, round(time.time() - t0), "s", flush=True)
