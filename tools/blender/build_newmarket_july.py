"""Newmarket's July Course in Blender: a first build of the scene, and stills from the key cameras (8 Nov 2026).

    python -c "exec(open('tools/blender/build_newmarket_july.py').read())"            # build + all stills
    SHOTS=stand,headon SAMPLES=16 python -c "exec(open(...).read())"                 # some stills, fewer samples
    SAVE=1 ...                                                                       # also save build/newmarket_july.blend

Everything comes from the course data (tools/course/newmarket/site_plan.py writes it): courses/newmarket-july-draft.json,
newmarket-draft.json (the Rowley Mile, across the Dyke) and newmarket-site.json. Built in the July Course's own axes
(origin = its winning post on the inside rail; course (x, z) is Blender (x, -z), height up), so a later export lines up
with the course files. The stand side's buildings are the July pieces (july_stands.glb, built by
tools/blender/build_july_stands.py: plain terraces, the old pavilion, the judge's box, the weighing room); the festival
is the site components (site_props.glb), the trees the clay trees, the crowd the skittle figures (on the lawns, along the
far rail and on the stands' own terraces), the boards and the post and poles Ascot's; only the ground, the Dyke and
Newmarket's white hoop rails are made here.

Stills go to reference/newmarket-july/renders/ (Cycles, the finish study's soft warm light and pastel sky).
"""
import os, sys, json, math, random
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix, Euler

REPO = os.path.abspath(os.environ.get("REPO", "."))
sys.path.insert(0, os.path.join(REPO, "tools/course/newmarket"))
import july_layout as J, draft_layout as R, site_plan as SP          # the courses' own geometry and placement
OUT = os.path.join(REPO, os.environ.get("OUT", "reference/newmarket-july/renders"))
SAMPLES = int(os.environ.get("SAMPLES", "24"))
SHOTS = [s for s in os.environ.get("SHOTS", "stand,stand_long,tracking,headon,drone,reverse,reverse_up,overview").split(",") if s]
RES = [int(v) for v in os.environ.get("RES", "1280x720").split("x")]
os.makedirs(OUT, exist_ok=True)

jc = json.load(open(os.path.join(REPO, "courses/newmarket-july-draft.json")))
rc = json.load(open(os.path.join(REPO, "courses/newmarket-draft.json")))
site = json.load(open(os.path.join(REPO, "courses/newmarket-site.json")))
W = J.TRACK_W

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def srgb(h, a=1.0):
    h = h.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (a,)


def flat_material(name, hexc, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = srgb(hexc); b.inputs["Roughness"].default_value = rough
    m.diffuse_color = srgb(hexc)
    return m


def clayify(m, sss=0.12, tooth=0.12, mottle=0.035, colour=None):
    """Matte painted clay, as the Ascot finish study (tools/blender/stand_clean_study.py): no shine, the faintest tooth
    in the surface and unevenness in the colour, measured in metres on the object. In place; colour = a new base hex."""
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None) if nt else None
    if b is None:
        return m
    b.inputs["Roughness"].default_value = 0.92; b.inputs["Metallic"].default_value = 0.0
    b.inputs["Specular IOR Level"].default_value = 0.12
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.09, 0.06, 0.04); b.inputs["Subsurface Scale"].default_value = 0.05
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 9.0; fine.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = tooth; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(fine.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if b.inputs["Base Color"].is_linked:                  # a printed texture (a board): leave its colours alone
        return m
    broad = nt.nodes.new("ShaderNodeTexNoise"); broad.inputs["Scale"].default_value = 0.35; broad.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], broad.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix"); mix.name = "clay_mix"; mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[6].default_value = srgb(colour) if colour else tuple(b.inputs["Base Color"].default_value)
    rmp = nt.nodes.new("ShaderNodeMapRange"); rmp.inputs["To Min"].default_value = 1 - mottle; rmp.inputs["To Max"].default_value = 1 + mottle
    nt.links.new(broad.outputs["Fac"], rmp.inputs["Value"])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"): nt.links.new(rmp.outputs["Result"], comb.inputs[k])
    nt.links.new(comb.outputs["Color"], mix.inputs[7]); nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def soften(ob, width=0.05):
    """Rounded edges: a narrow bevel catches a line of light along every edge (the clay look)."""
    for p in ob.data.polygons: p.use_smooth = True
    bv = ob.modifiers.new("bevel", "BEVEL")
    bv.width = width; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
    bv.use_clamp_overlap = True; bv.harden_normals = True; bv.profile = 0.6
    ob.modifiers.new("weights", "WEIGHTED_NORMAL").keep_sharp = True


def B(x, z, y=0.0):
    """Course axes (x along the straight, z across, y up) to Blender's."""
    return (x, -z, y)


# ------------------------------------------------------------------------------------------ the ground's height
# Sampled along both courses' paths (inside rail, every 5 m), in the July Course's axes, with their heights.
def path_samples(course_pt, height, d0, d1, to_local=lambda x, z: (x, z)):
    xs, zs, hs = [], [], []
    d = d0
    while d <= d1:
        (x, z), (tx, tz) = course_pt(d)
        for o in (0.0, W / 2, W):                                  # inside rail, middle, outer rail
            lx, lz = to_local(x + tz * o, z - tx * o); xs.append(lx); zs.append(lz); hs.append(height(d))
        d += 5.0
    return np.array(xs), np.array(zs), np.array(hs)


def r_to_local(x, z):
    return SP.s2j(x, z)


jx, jz, jh = path_samples(J.course_pt, J.height, -J.RUN_ON, J.STRAIGHT + J.BEND_LEN + 2600)
rx, rz, rh = path_samples(R.course_pt, R.height, -R.RUN_ON, max(R.TRIPS.values()) * R.F, r_to_local)
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter
from matplotlib.path import Path as MPath
TJ, TR = cKDTree(np.c_[jx, jz]), cKDTree(np.c_[rx, rz])
TJm, TRm = cKDTree(np.c_[jx[1::3], jz[1::3]]), cKDTree(np.c_[rx[1::3], rz[1::3]])      # the middles of the tracks

GX0, GX1, GZ0, GZ1, STEP = -650.0, 1900.0, -420.0, 1120.0, 2.5
gx = np.arange(GX0, GX1 + 0.01, STEP); gz = np.arange(GZ0, GZ1 + 0.01, STEP)
X, Z = np.meshgrid(gx, gz)                                          # rows: z, columns: x
P = np.c_[X.ravel(), Z.ravel()]
dj, ij = TJ.query(P); dr, ir = TR.query(P)
wj, wr = 1.0 / (dj ** 2 + 400.0), 1.0 / (dr ** 2 + 400.0)
H = ((jh[ij] * wj + rh[ir] * wr) / (wj + wr)).reshape(X.shape)

# the July Course's Dyke face (beyond its outer rail, along the straight), set back behind the far-side festival
def bank_h(Bp, off):
    a, b = Bp["crest"]; f, bk, h = Bp["foot"], Bp["back"], Bp["height"]
    u = np.where(off < a, (off - f) / (a - f), np.where(off <= b, 1.0, (bk - off) / (bk - b)))
    u = np.clip(u, 0, 1)
    return np.where((off > f) & (off < bk), h * (0.5 - 0.5 * np.cos(np.pi * u)), 0.0)


dyke = np.zeros_like(H)
for s0, s1 in jc["dykeFace"]["spans"]:
    on = (X >= s0) & (X <= s1)
    off = Z - W
    cols = [J.bank_at(d) for d in gx]
    prof = {k: np.broadcast_to(np.array([c[k] for c in cols]), X.shape) for k in ("foot", "back", "height")}
    c0 = np.broadcast_to(np.array([c["crest"][0] for c in cols]), X.shape); c1 = np.broadcast_to(np.array([c["crest"][1] for c in cols]), X.shape)
    hb = bank_h({"foot": prof["foot"], "back": prof["back"], "height": prof["height"], "crest": [c0, c1]}, off)
    dyke = np.maximum(dyke, np.where(on, hb, 0.0))
# the Rowley Mile's far bank (behind its inside rail, along its straight), in its own axes
SX, SZ = SP.j2s(X, Z)
for s0, s1 in rc["farBank"]["spans"]:
    on = (SX >= max(s0, -R.RUN_ON - 200)) & (SX <= min(s1, R.STRAIGHT))
    dyke = np.maximum(dyke, np.where(on, bank_h(R.BANK, -SZ), 0.0))
# the Dyke's top between the two courses
poly = np.array([SP.s2j(x, z) for x, z in site["dyke"]["top"]])
inside = MPath(poly).contains_points(P).reshape(X.shape)
dyke = np.maximum(dyke, np.where(inside, site["dyke"]["height"], 0.0))
dyke = gaussian_filter(dyke, 1.6)
H = H + dyke

# masks: red = another course's track (the July straight is drawn sharp in the shader), green = lawns and festival
# grounds, blue = the Dyke's rough top
mR = ((TJm.query(P)[0] <= W / 2 + 0.3) | (TRm.query(P)[0] <= R.TRACK_W / 2 + 0.3)).reshape(X.shape)   # on a track
def rect_mask(x0, x1, z0, z1):
    return (X >= x0) & (X <= x1) & (Z >= z0) & (Z <= z1)
lawn = np.zeros_like(H, bool)
for r_ in [J.LAWN, J.FESTIVAL]:
    lawn |= rect_mask(r_["x"][0], r_["x"][1], r_["z"][0], r_["z"][1])
ff = J.far_rect(J.FAR_FESTIVAL); lawn |= rect_mask(ff["x"][0], ff["x"][1], ff["z"][0], ff["z"][1])
fc = J.far_rect(J.FAR_CROWD); lawn |= rect_mask(fc["x"][0], fc["x"][1], fc["z"][0], fc["z"][1])
for s in J.stand_rects():
    lawn |= rect_mask(s["x"][0] - 6, s["x"][1] + 6, s["z"][0] - 6, s["z"][1] + 2)
rough = gaussian_filter(inside.astype(float), 3) > 0.5
M = np.stack([gaussian_filter(mR.astype(float), 0.6), gaussian_filter(lawn.astype(float), 0.8), gaussian_filter(rough.astype(float), 2.0)], -1)


def ground_height(x, z):
    """The ground's height at course (x, z), bilinear from the grid."""
    fx = np.clip((np.asarray(x) - GX0) / STEP, 0, len(gx) - 1.001); fz = np.clip((np.asarray(z) - GZ0) / STEP, 0, len(gz) - 1.001)
    i, j = np.floor(fz).astype(int), np.floor(fx).astype(int); u, v = fz - i, fx - j
    return (H[i, j] * (1 - u) * (1 - v) + H[i + 1, j] * u * (1 - v) + H[i, j + 1] * (1 - u) * v + H[i + 1, j + 1] * u * v)


# ------------------------------------------------------------------------------------------ the ground mesh
def build_ground():
    ny, nx = X.shape
    verts = np.c_[X.ravel(), -Z.ravel(), H.ravel()].astype(np.float32)
    ii = np.arange(ny * nx).reshape(ny, nx)
    a, b, c, d = ii[:-1, :-1].ravel(), ii[:-1, 1:].ravel(), ii[1:, 1:].ravel(), ii[1:, :-1].ravel()
    quads = np.c_[a, d, c, b]                                       # winding so normals face up (Blender y = -z)
    me = bpy.data.meshes.new("ground")
    me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel())
    me.loops.add(quads.size); me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4)); me.polygons.foreach_set("loop_total", np.full(len(quads), 4))
    me.update(); me.validate()
    col = me.color_attributes.new("mask", "FLOAT_COLOR", "POINT")
    col.data.foreach_set("color", np.c_[M.reshape(-1, 3), np.ones(ny * nx)].astype(np.float32).ravel())
    me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
    ob = bpy.data.objects.new("ground", me); scene.collection.objects.link(ob)
    ob.data.materials.append(ground_material())
    return ob


def ground_material():
    m = bpy.data.materials.new("ground"); m.use_nodes = True
    nt = m.node_tree; n, l = nt.nodes, nt.links
    bsdf = n["Principled BSDF"]; bsdf.inputs["Roughness"].default_value = 0.95
    tc = n.new("ShaderNodeTexCoord"); sep = n.new("ShaderNodeSeparateXYZ"); l.new(tc.outputs["Object"], sep.inputs[0])
    att = n.new("ShaderNodeVertexColor"); att.layer_name = "mask"
    sm = n.new("ShaderNodeSeparateColor"); l.new(att.outputs["Color"], sm.inputs[0])
    def noise(scale, detail=3, rough=0.55):
        t = n.new("ShaderNodeTexNoise"); t.inputs["Scale"].default_value = scale; t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough; l.new(tc.outputs["Object"], t.inputs["Vector"]); return t.outputs["Fac"]
    def tint(hexc, scale, spread, fine=None):
        r = n.new("ShaderNodeValToRGB"); el = r.color_ramp.elements
        base = srgb(hexc); el[0].position, el[1].position = 0.3, 0.7
        el[0].color = tuple(v * (1 - spread) for v in base[:3]) + (1,); el[1].color = tuple(min(v * (1 + spread), 1) for v in base[:3]) + (1,)
        l.new(noise(scale), r.inputs[0]); out = r.outputs[0]
        if fine:
            r2 = n.new("ShaderNodeValToRGB"); e2 = r2.color_ramp.elements; e2[0].position, e2[1].position = 0.35, 0.65
            e2[0].color = (1 - fine, 1 - fine, 1 - fine, 1); e2[1].color = (1 + fine, 1 + fine, 1 + fine, 1)
            l.new(noise(scale * 30, 4, 0.6), r2.inputs[0]); mm = n.new("ShaderNodeMix"); mm.data_type = "RGBA"; mm.blend_type = "MULTIPLY"
            mm.inputs["Factor"].default_value = 1.0; l.new(out, mm.inputs["A"]); l.new(r2.outputs[0], mm.inputs["B"]); out = mm.outputs["Result"]
        return out
    heath = tint("#b2b47a", 0.006, 0.12, 0.08)     # the open heath: paler, drier and more olive than the course
    lawn = tint("#b4c785", 0.02, 0.07, 0.06)
    scrub = tint("#8f9c5c", 0.01, 0.16, 0.12)
    turf = tint("#6a9c44", 0.01, 0.08, 0.06)      # the racing turf: a deeper, watered green so the track reads
    # mowing bands across the July straight, 9 m wide
    band = n.new("ShaderNodeMath"); band.operation = "SINE"
    mul = n.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = math.pi / 9.0
    l.new(sep.outputs["X"], mul.inputs[0]); l.new(mul.outputs[0], band.inputs[0])
    br = n.new("ShaderNodeMapRange"); br.inputs["From Min"].default_value = -1; br.inputs["To Min"].default_value = 0.88; br.inputs["To Max"].default_value = 1.12
    l.new(band.outputs[0], br.inputs["Value"])
    bandc = n.new("ShaderNodeCombineColor"); [l.new(br.outputs[0], bandc.inputs[k]) for k in range(3)]
    turf2 = n.new("ShaderNodeMix"); turf2.data_type = "RGBA"; turf2.blend_type = "MULTIPLY"; turf2.inputs["Factor"].default_value = 1.0
    l.new(turf, turf2.inputs["A"]); l.new(bandc.outputs[0], turf2.inputs["B"])
    # the July straight and run-out, sharp: -W <= Blender y <= 0 and x >= -RUN_ON (the bend is in the mask)
    def step(inp, edge, above=True):
        mth = n.new("ShaderNodeMath"); mth.operation = "GREATER_THAN" if above else "LESS_THAN"; mth.inputs[1].default_value = edge
        l.new(inp, mth.inputs[0]); return mth.outputs[0]
    def mult(a, b):
        mth = n.new("ShaderNodeMath"); mth.operation = "MULTIPLY"; l.new(a, mth.inputs[0]); l.new(b, mth.inputs[1]); return mth.outputs[0]
    on_straight = mult(mult(step(sep.outputs["Y"], -W), step(sep.outputs["Y"], 0.0, False)), mult(step(sep.outputs["X"], -J.RUN_ON), step(sep.outputs["X"], J.STRAIGHT + 2, False)))
    trk = n.new("ShaderNodeMath"); trk.operation = "MAXIMUM"; l.new(on_straight, trk.inputs[0]); l.new(sm.outputs["Red"], trk.inputs[1])
    def mix(a, b, f):
        mm = n.new("ShaderNodeMix"); mm.data_type = "RGBA"; l.new(f, mm.inputs["Factor"]); l.new(a, mm.inputs["A"]); l.new(b, mm.inputs["B"]); return mm.outputs["Result"]
    c = mix(heath, scrub, sm.outputs["Blue"])
    c = mix(c, lawn, sm.outputs["Green"])
    c = mix(c, turf2.outputs["Result"], trk.outputs[0])
    l.new(c, bsdf.inputs["Base Color"])
    return m


# ------------------------------------------------------------------------------------------ the white hoop rails
RAIL_MAT = flat_material("rail_white", "#f4f2ec", 0.5)


def rails(course_pt, d0, d1, offset, outward, to_local=lambda x, z: (x, z), spacing=2.5):
    """Newmarket's white plastic rail: a round top rail 1.05 m up, on hoops (up from the ground on the side away from
    the track, curving over to hold the rail). offset: metres from the inside rail; outward: +1 if 'away from the
    track' is towards larger offsets, -1 if towards the inside."""
    bm = bmesh.new()
    pts, tans = [], []
    d = d0
    while d <= d1:
        (x, z), (tx, tz) = course_pt(d)
        p = to_local(x + tz * offset, z - tx * offset)
        if GX0 + 5 < p[0] < GX1 - 5 and GZ0 + 5 < p[1] < GZ1 - 5:
            q = to_local(x + tz * (offset + outward), z - tx * (offset + outward))
            pts.append((p, (q[0] - p[0], q[1] - p[1]), d))
        d += spacing
    if len(pts) < 2: return None
    hs = ground_height(np.array([p[0][0] for p in pts]), np.array([p[0][1] for p in pts]))
    ring, rr = 6, 0.045
    rings = []
    for k, ((px, pz), (ox, oz), d) in enumerate(pts):
        o = Vector((ox, -oz, 0)).normalized(); up = Vector((0, 0, 1))
        c = Vector((px, -pz, hs[k] + 1.05))
        rings.append([bm.verts.new(c + (o * math.cos(t) + up * math.sin(t)) * rr) for t in [2 * math.pi * i / ring for i in range(ring)]])
        # the hoop: up from 0.28 m out, then a quarter circle over to the rail
        hp = [Vector((0.28, 0.0)), Vector((0.28, 0.78))] + [Vector((0.28 * math.cos(a), 0.78 + 0.27 * math.sin(a))) for a in np.linspace(0.25, math.pi / 2, 5)]
        prev = None
        for (u, w) in hp:
            cc = Vector((px, -pz, hs[k])) + o * u + up * w
            sq = [bm.verts.new(cc + Vector(t)) for t in ((0.025, 0.025, 0), (-0.025, 0.025, 0), (-0.025, -0.025, 0), (0.025, -0.025, 0))]
            if prev:
                for i in range(4): bm.faces.new((prev[i], prev[(i + 1) % 4], sq[(i + 1) % 4], sq[i]))
            prev = sq
    for a, b in zip(rings[:-1], rings[1:]):
        if (a[0].co - b[0].co).length > spacing * 3: continue
        for i in range(ring): bm.faces.new((a[i], a[(i + 1) % ring], b[(i + 1) % ring], b[i]))
    me = bpy.data.meshes.new("rail"); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("rail", me); scene.collection.objects.link(ob); me.materials.append(RAIL_MAT)
    return ob


# ------------------------------------------------------------------------------------------ the kit models
def load(path, keep=None):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, path))
    new = [o for o in bpy.data.objects if o not in before]
    mw = {o: o.matrix_world.copy() for o in new}
    for o in new:
        o.parent = None
    for o in new:
        if o.type == "MESH":
            o.data.transform(mw[o]); o.matrix_world = Matrix.Identity(4)
    new = [o for o in new if o.type == "MESH"]
    lib = bpy.data.collections.get("kit") or bpy.data.collections.new("kit")
    if lib.name not in scene.collection.children: scene.collection.children.link(lib)
    out = {}
    for o in new:
        for c in o.users_collection: c.objects.unlink(o)
        lib.objects.link(o); o.hide_render = True; o.hide_viewport = True
        out[o.name.split(".")[0]] = o
    return out


def place(src, x, z, turn_deg=0.0, scale=1.0, sx=None, name=None):
    """A linked copy of a kit piece at course (x, z) on the ground, turned (degrees anticlockwise from above; 0 =
    facing course +z, the kit's own front) and scaled."""
    ob = bpy.data.objects.new(name or src.name + "_i", src.data)
    ob.location = Vector(B(x, z, float(ground_height(x, z))))
    ob.rotation_euler = (0, 0, math.radians(turn_deg))
    ob.scale = ((sx if sx is not None else scale), scale, scale)
    scene.collection.objects.link(ob)
    return ob


def instances(name, coll, xyz, idx, rot, scl):
    """Many copies of a collection's children on points (geometry nodes), picked by idx, turned and scaled."""
    me = bpy.data.meshes.new(name); n = len(xyz)
    me.vertices.add(n); me.vertices.foreach_set("co", np.asarray(xyz, np.float32).ravel())
    for nm, typ, val in (("idx", "INT", idx), ("rot", "FLOAT", rot), ("scl", "FLOAT", scl)):
        a = me.attributes.new(nm, typ, "POINT"); a.data.foreach_set("value", np.asarray(val, np.int32 if typ == "INT" else np.float32))
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nd, ln = ng.nodes, ng.links
    gi, go = nd.new("NodeGroupInput"), nd.new("NodeGroupOutput")
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


def collection_of(name, objs):
    c = bpy.data.collections.new(name)
    for o in objs:
        cp = bpy.data.objects.new(o.name + "_c", o.data); cp.matrix_world = Matrix.Identity(4); c.objects.link(cp)
    return c


def build():
    ground = build_ground()
    # --- rails: the July Course (inside rail on the stand side, outer rail on the far side) and the Rowley Mile
    jd1 = J.STRAIGHT + J.BEND_LEN + 2600
    rails(J.course_pt, -J.RUN_ON, jd1, 0.0, -1)
    rails(J.course_pt, -J.RUN_ON, jd1, W, +1)
    rails(R.course_pt, -R.RUN_ON, R.STRAIGHT + R.BEND_LEN + 300, 0.0, -1, r_to_local)
    rails(R.course_pt, -R.RUN_ON, R.STRAIGHT + R.BEND_LEN + 300, R.TRACK_W, +1, r_to_local)
    # --- the winning post and furlong poles (on the inside rail: the stand side here)
    props = load("assets/models/course/course_props.glb")
    place(props["winning_post"], 0.0, -0.9)
    for k in range(1, 8):
        place(props["furlong_%d" % k], k * J.F, -0.9)
    # --- boards (far side only), the July Course's and the Rowley Mile's in view
    belts = load("assets/models/course/planting_belts.glb")
    for x, z, turn, design in jc["boards"]["list"]:
        place(belts["board_" + design], x, z, turn)
    for x, z, turn, design in rc["boards"]["list"]:
        lx, lz = r_to_local(x, z)
        if GX0 < lx < GX1 and GZ0 < lz < GZ1:
            place(belts["board_" + design], lx, lz, turn + J.SPLAY)      # the July axes are turned SPLAY from the site's
    # --- trees: clay crowns (four leaf greens) and trunks
    tr = load("assets/models/trees/trees_clay.glb")
    leafs = json.load(open(os.path.join(REPO, "assets/models/trees/trees_clay.json")))
    kinds = sorted(["oak_a", "oak_b", "oak_c", "wide_a", "wide_b", "poplar_a"])   # sorted: Collection Info lists children by name
    LEAF = [leafs["leaf"][i] for i in (0, 1, 3, 6)]
    crowns = []
    for k in kinds:
        for li, hexc in enumerate(LEAF):
            me = tr[k + "_crown"].data.copy(); m = bpy.data.materials.new("leaf_%d" % li); m.use_nodes = True
            nt = m.node_tree; vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Color"
            mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = "RGBA"; mm.blend_type = "MULTIPLY"; mm.inputs["Factor"].default_value = 1.0
            nt.links.new(vc.outputs["Color"], mm.inputs["A"]); mm.inputs["B"].default_value = tuple(v * leafs["shadeMax"] for v in srgb(hexc)[:3]) + (1,)
            nt.links.new(mm.outputs["Result"], nt.nodes["Principled BSDF"].inputs["Base Color"]); nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
            me.materials.clear(); me.materials.append(m)
            o = bpy.data.objects.new("%s_%d" % (k, li), me); crowns.append(o)
    crown_coll = bpy.data.collections.new("crowns")
    for o in crowns: crown_coll.objects.link(o)
    trunk_coll = collection_of("trunks", [tr[k + "_trunk"] for k in kinds])
    bark = flat_material("bark", "#7a6650"); [o.data.materials.__setitem__(0, bark) for o in trunk_coll.objects]
    T = [(t[0], t[1], t[2], t[3], t[4]) for t in jc["trees"]["list"]]
    for t in rc["trees"]["list"]:
        lx, lz = r_to_local(t[0], t[1])
        if GX0 < lx < GX1 and GZ0 < lz < GZ1: T.append((lx, lz, t[2], t[3], t[4]))
    rnd = random.Random(5)
    xs = np.array([t[0] for t in T]); zs = np.array([t[1] for t in T]); hs = ground_height(xs, zs)
    xyz = np.c_[xs, -zs, hs - 0.2]
    ki = np.array([kinds.index(t[2]) for t in T]); li = np.array([rnd.randrange(len(LEAF)) for _ in T])
    rot = np.radians([t[4] for t in T]); scl = np.array([t[3] for t in T])
    instances("tree_crowns", crown_coll, xyz, ki * len(LEAF) + li, rot, scl)
    instances("tree_trunks", trunk_coll, xyz, ki, rot, scl)
    # --- the stand side's buildings (tools/blender/build_july_stands.py): plain terraces, the old pavilion, the judge's box
    # on the line, the weighing room, a bell tent and a little pavilion; each piece's front faces the track (course +z)
    # Owner (8 Nov): the pastel-street precedent's finish: pastel tones, soft shadows, matte clay, rounded edges; each
    # building its own shade of soft terracotta (and the little pavilion powder blue), not overdone
    jsp = load("assets/models/architecture/july_stands.glb")
    jsi = json.load(open(os.path.join(REPO, "assets/models/architecture/july_stands.json")))["pieces"]
    for m in {sl.material for o in jsp.values() for sl in o.material_slots if sl.material}:
        clayify(m, sss=0.0 if m.name.split(".")[0] in ("jc_glass", "jc_steel", "jc_iron", "jc_bench") else 0.12)
    TINT = {"Garden stand": {"jc_brick": "#e6ae98"}, "Weighing room": {"jc_brick": "#d99683"},
            "Judge's box": {"jc_brick": "#df977f"}, "Grandstand": {"jc_brick": "#e09c86"},
            "Premier stand": {"jc_brick": "#ecb497"}, "Paddock stand": {"jc_brick": "#e4a69c"},
            "Members' terrace": {"jc_brick": "#e8ae94"}, "Little pavilion": {"jc_paint": "#c4d4de"}}
    stand_people = []                                                  # (x, z, height, facing) on the stands themselves
    rs = random.Random(21)
    for st in J.STANDS:
        info = jsi[st["piece"]]
        cx = (st["x"][0] + st["x"][1]) / 2
        sx = (st["x"][1] - st["x"][0]) / info["width"] if st["piece"].startswith("terrace") else 1.0
        ob = place(jsp[st["piece"]], cx, -st["front"], 0.0, 1.0, sx=sx, name=st["name"])
        soften(ob)
        for i, sl in enumerate(ob.material_slots):
            hexc = TINT.get(st["name"], {}).get(sl.material.name.split(".")[0] if sl.material else "")
            if hexc:
                m = sl.material.copy(); m.node_tree.nodes["clay_mix"].inputs[6].default_value = srgb(hexc)
                sl.link = "OBJECT"; sl.material = m
        base = ob.location.z
        fill = rs.uniform(0.75, 0.95)
        dens = {"judges_box": 0.8, "old_pavilion": 1.3}.get(st["piece"], 1.8) * fill
        for x0, x1, y0, y1, fz in info["crowd"]:
            n = int((x1 - x0) * sx * (y1 - y0) * dens + rs.random())
            for _ in range(n):
                stand_people.append((cx + rs.uniform(x0, x1) * sx, -st["front"] - rs.uniform(y0, y1), base + fz, 0.0))
    # --- festival pieces
    sp = load("assets/models/architecture/site_props.glb")
    for m in {sl.material for o in sp.values() for sl in o.material_slots if sl.material}:
        clayify(m)
    rnd = random.Random(9)
    kind_piece = {"long marquee": "marquee_clearspan", "three-peak marquee": "marquee_peaks", "pagoda marquee": "pagoda_counter",
                  "white pitched-roof pavilion": "marquee_peaks"}
    size = {k: (abs(o.dimensions.x), abs(o.dimensions.y)) for k, o in sp.items()}
    for p in J.PAVILIONS:                                              # far side: facing the track (course -z)
        piece = kind_piece[p["kind"]]; w, d = size[piece]
        rx0, rx1 = p["x"]; z0, z1 = W + p["off"][0], W + p["off"][1]
        sc = min(max((z1 - z0) / d, 1.0), 1.6)
        nfit = max(1, int(round((rx1 - rx0) / (w * sc))))
        for k in range(nfit):
            cx = rx0 + (k + 0.5) * (rx1 - rx0) / nfit
            place(sp[piece], cx, (z0 + z1) / 2, 180.0, sc, sx=((rx1 - rx0) / nfit) / w)
    for p in J.INFILL:                                                 # marquees and pavilions behind the stands
        if p["kit"] == "site_props":                                  # "fit": stretched along the front to fill its gap
            sxf = p["size"][0] / size[p["piece"]][0] * p.get("scale", 1.0) if p.get("fit") else None
            place(sp[p["piece"]], p["at"][0], p["at"][1], 0.0, p.get("scale", 1.0), sx=sxf)
        else:                                                          # the July pieces' origin is the middle of the front
            soften(place(jsp[p["piece"]], p["at"][0], p["at"][1] + p["size"][1] / 2, 0.0, p.get("scale", 1.0)))
    t0, t1 = J.TIER["x"]; zt = W + sum(J.TIER["off"]) / 2                 # the tiered stand behind the finish
    for k in range(3):
        place(sp["stand_covered"], t0 + (k + 0.5) * (t1 - t0) / 3, zt, 180.0, 1.5)
    for x in np.arange(J.FAR_CROWD["x"][0] + 10, J.FAR_CROWD["x"][1], 34):  # flags and pagodas along the far festival
        place(sp["banner_flag"], x, W + 13.5, 180.0)
    # the stand-side festival (facing the track: course +z, the kit's own front)
    fx0, fx1 = J.FESTIVAL["x"]
    x = fx0 + 6
    while x < fx1 - 8:
        place(sp[rnd.choice(["terrace_deck", "terrace_deck", "kiosk_awning", "pagoda_kiosk"])], x, -16.0, 0.0)
        place(sp[rnd.choice(["kiosk_row_arched", "pergola_picnic", "pagoda_counter", "kiosk_awning"])], x + 4, -32.0, 0.0)
        if rnd.random() < 0.45: place(sp["marquee_peaks"], x + 10, -50.0, 0.0)
        place(sp["banner_flag"], x - 3, -11.5, 0.0)
        for _ in range(3): place(sp["picnic_table"], x + rnd.uniform(-5, 12), rnd.uniform(-44, -22), rnd.uniform(0, 180))
        x += rnd.uniform(22, 30)
    # --- the crowd: the lawns in front of the stands, the far rail, and a sprinkle in both festivals
    cr = load("assets/models/architecture/crowd_set_8.glb")
    figs = sorted(cr)
    SKC = {"clothes": ["#2c3140", "#3a3d44", "#4b4d52", "#2f3a33", "#59544c", "#c9a0a8", "#9fb6c8", "#ddd2b8", "#a8706a", "#88a383", "#d2b874", "#e8e2d6", "#9a88b4", "#cf9476"],
           "hats": ["#222226", "#efe6d2", "#d8c08a", "#c9a0a8", "#9fb6c8"], "skin": ["#efc6a4", "#e2b48e", "#c99572", "#9a6a4a"]}
    variants = []
    rv = random.Random(3)
    for f in figs:
        for v in range(4):
            me = cr[f].data.copy()
            for i, mat in enumerate(me.materials):
                base = mat.name.split(".")[0]
                key = {"fig_main": "clothes", "fig_hat": "hats", "fig_skin": "skin"}.get(base)
                if key:
                    nm = flat_material("%s_%s_%d" % (f, base, v), rv.choice(SKC[key]) if not (f.startswith("gent_00") or f.startswith("gent_01")) or key != "clothes" else "#1e1f24", 0.85)
                    me.materials[i] = nm
            variants.append(bpy.data.objects.new("%s_%d" % (f, v), me))
    crowd_coll = bpy.data.collections.new("crowd")
    for o in variants: crowd_coll.objects.link(o)
    pts, facing = [], []
    def fill(x0, x1, z0, z1, density, face):
        n = int((x1 - x0) * (z1 - z0) * density)
        for _ in range(n): pts.append((rnd.uniform(x0, x1), rnd.uniform(z0, z1))); facing.append(face)
    fill(J.LAWN["x"][0], J.LAWN["x"][1], J.LAWN["z"][0] + 1, J.LAWN["z"][1] - 1, 0.42, 0.0)
    fill(J.FAR_CROWD["x"][0], J.FAR_CROWD["x"][1], W + J.FAR_CROWD["off"][0], W + J.FAR_CROWD["off"][1], 0.38, 180.0)
    fill(J.FESTIVAL["x"][0], J.FESTIVAL["x"][1], -60, -12, 0.035, None)
    ff = J.far_rect(J.FAR_FESTIVAL); fill(ff["x"][0], ff["x"][1], ff["z"][0] + 2, ff["z"][1], 0.035, None)
    blocked = J.stand_rects() + [J.far_rect(p) for p in J.PAVILIONS] + [J.far_rect(J.TIER)]
    keep = [i for i, (x, z) in enumerate(pts) if not any(J.rect_hit(x, z, r, 1.0) for r in blocked)]
    xs = np.array([pts[i][0] for i in keep] + [p[0] for p in stand_people])
    zs = np.array([pts[i][1] for i in keep] + [p[1] for p in stand_people])
    hs = np.r_[ground_height(xs[:len(keep)], zs[:len(keep)]), [p[2] for p in stand_people]]
    xyz = np.c_[xs, -zs, hs]
    faces = [facing[i] for i in keep] + [p[3] for p in stand_people]
    rot = np.radians([(f if f is not None else rnd.uniform(0, 360)) + rnd.uniform(-35, 35) for f in faces])
    idx = np.array([rnd.randrange(len(variants)) for _ in faces])
    instances("crowd", crowd_coll, xyz, idx, rot, np.array([rnd.uniform(0.95, 1.06) for _ in faces]))
    print("built: ground %d verts, %d trees, %d crowd (%d on the stands)" % (len(X.ravel()), len(T), len(faces), len(stand_people)), flush=True)


# ------------------------------------------------------------------------------------------ light, sky and the cameras
def light():
    world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
    wn, wl = world.node_tree.nodes, world.node_tree.links
    tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); wl.new(tc.outputs["Generated"], sep.inputs[0])
    sky = wn.new("ShaderNodeValToRGB"); el = sky.color_ramp.elements
    # the cameras mostly see the bottom 20 degrees of sky, so the blue has to arrive quickly above a warm hazy horizon
    el[0].position, el[0].color = 0.0, (1.0, 0.87, 0.76, 1); el[1].position, el[1].color = 0.42, (0.36, 0.55, 0.86, 1)
    e = el.new(0.02); e.color = (0.84, 0.87, 0.92, 1)
    e = el.new(0.1); e.color = (0.55, 0.7, 0.93, 1)
    wl.new(sep.outputs["Z"], sky.inputs[0]); wl.new(sky.outputs[0], wn["Background"].inputs["Color"])
    wn["Background"].inputs["Strength"].default_value = 1.0
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.6; sun.data.angle = math.radians(14); sun.data.color = (1.0, 0.8, 0.62)
    # an afternoon sun from the west-south-west (the site's north is at the bottom of the plans): behind the stands
    # and up the course, so the far side the cameras look at is lit from the front and the side
    to_sun = Vector((0.62, 0.78, 0.0)).normalized() * math.cos(math.radians(30)) + Vector((0, 0, math.sin(math.radians(30))))
    sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()


CAMS = {   # course (x, z, height) from and to, lens mm
    "stand": ((0.0, -13.5, 13.0), (-20.0, 80.0, 2.0), 26),                     # on the roof of the judge's box
    "stand_long": ((0.0, -13.5, 13.0), (420.0, 40.0, 1.0), 70),
    "tracking": ((420.0, -5.0, 3.2), (360.0, 60.0, 3.0), 32),
    "headon": ((-240.0, W / 2, 4.0), (700.0, W / 2, 1.5), 85),
    "drone": ((150.0, -3.0, 15.0), (620.0, 30.0, 0.0), 30),
    "overview": ((300.0, 700.0, 300.0), (260.0, 0.0, 0.0), 30),
    "reverse": ((25.0, W + 3.0, 5.0), (-8.0, -25.0, 7.0), 24),                  # from the far rail back at the line
    "reverse_up": ((150.0, W + 3.0, 5.0), (130.0, -25.0, 8.0), 24),             # the same, at the stands up the course
}


def camera(name):
    (fx, fz, fy), (tx, tz, ty), lens = CAMS[name]
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.clip_end = 6000
    ob = bpy.data.objects.new(name, cam); scene.collection.objects.link(ob)
    frm = Vector(B(fx, fz, float(ground_height(fx, fz)) + fy)); to = Vector(B(tx, tz, float(ground_height(tx, tz)) + ty))
    ob.location = frm; ob.rotation_euler = (to - frm).to_track_quat("-Z", "Y").to_euler()
    return ob


def render():
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True; scene.cycles.max_bounces = 4
    scene.render.resolution_x, scene.render.resolution_y = RES; scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    try: scene.view_settings.look = "AgX - Base Contrast"
    except Exception: pass
    scene.view_settings.exposure = 0.12
    import time
    for s in SHOTS:
        t0 = time.time()
        scene.camera = camera(s)
        scene.render.filepath = os.path.join(OUT, s + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", s, round(time.time() - t0), "s", flush=True)


build()
light()
if os.environ.get("SAVE"):
    os.makedirs(os.path.join(REPO, "build"), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "build/newmarket_july.blend"))
render()
