"""Tree workshop (owner, 11 Nov 2026: "I'm just not sure about the trees in general. We seem to just be having big lumps
rather than trees"). The game's leafy crowns are sixteen balls merged into one mass and shaded as one soft ball: a
lump on a stick. Here a tree is built as a tree: a trunk that forks into limbs, and separate masses of foliage carried
on the limbs, with air between them. Each mass keeps the leafy surface he chose (cells pushed out of a rounded form),
the colours grade from dark at the foot of the crown to light at its top ("C and F"), the light and sky are the
workshop's. Several ways of building one, side by side, each as a group near the rail and a line further off.

    python3 -c "exec(open('tools/blender/tree_workshop.py').read())"
    env: SAMPLES (40), RES (960x540), OUT (reference/landscape-workshop/trees), ONLY (e.g. "A,C")
"""
import os, sys, math, random, time, subprocess, json
import bpy, bmesh
from mathutils import Vector, Matrix

T0 = time.time()
REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
SAMPLES = int(os.environ.get("SAMPLES", "40"))
RES = tuple(int(v) for v in os.environ.get("RES", "960x540").split("x"))
OUTDIR = os.environ.get("OUT", rp("reference/landscape-workshop/trees")); os.makedirs(OUTDIR, exist_ok=True)
ONLY = [s for s in os.environ.get("ONLY", "").split(",") if s]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
N_ = lambda nt, kind: nt.nodes.new(kind)


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


def mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.95; b.inputs["Specular IOR Level"].default_value = 0.06
    return m, m.node_tree, b


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


# ---------------- materials
# leaves: graded up the whole crown (dark at its foot, light at its top), a little tone from mass to mass and within
m, nt, b = mat("leaf"); LEAF = m
tc = N_(nt, "ShaderNodeTexCoord"); sz = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sz.inputs[0])
rampn = N_(nt, "ShaderNodeValToRGB"); els = rampn.color_ramp.elements
els[0].position = 0.0; els[0].color = lin("#3c6a55"); els[1].position = 1.0; els[1].color = lin("#bccf8c"); e = els.new(0.5); e.color = lin("#709d66")
nt.links.new(sz.outputs["Z"], rampn.inputs[0])
g = N_(nt, "ShaderNodeNewGeometry"); nz = N_(nt, "ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.5; nz.inputs["Detail"].default_value = 2; nt.links.new(g.outputs["Position"], nz.inputs["Vector"])
col = mul(nt, rampn.outputs[0], grey(nt, nz.outputs["Fac"], 0.88, 1.12, 0.3, 0.7))
at = N_(nt, "ShaderNodeAttribute"); at.attribute_name = "tone"; col = mul(nt, col, grey(nt, at.outputs["Fac"], 0.86, 1.14))
nt.links.new(col, b.inputs["Base Color"]); b.inputs["Subsurface Weight"].default_value = 0.12; b.inputs["Subsurface Radius"].default_value = (0.25, 0.4, 0.12)
m, nt, b = mat("bark"); BARK = m; b.inputs["Base Color"].default_value = lin("#6d5f50")
m, nt, b = mat("lawn"); LAWN = m
g = N_(nt, "ShaderNodeNewGeometry"); n1 = N_(nt, "ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = 0.11; n1.inputs["Detail"].default_value = 3; nt.links.new(g.outputs["Position"], n1.inputs["Vector"])
n2 = N_(nt, "ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 1.3; n2.inputs["Detail"].default_value = 2; nt.links.new(g.outputs["Position"], n2.inputs["Vector"])
col = mul(nt, lin("#a6bb88"), grey(nt, n1.outputs["Fac"], 0.74, 1.2, 0.36, 0.64)); col = mul(nt, col, grey(nt, n2.outputs["Fac"], 0.93, 1.07, 0.3, 0.7))
nt.links.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 1.0
m, nt, b = mat("turf"); TURF = m; b.inputs["Base Color"].default_value = lin("#8fad79"); b.inputs["Roughness"].default_value = 1.0
m, nt, b = mat("rail"); RAIL = m; b.inputs["Base Color"].default_value = lin("#f4f2ea")


def link(o, coll=None):
    (coll or scene.collection).objects.link(o); return o


def baked(o):
    """The object's mesh with its modifiers worked out."""
    link(o); dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(o.evaluated_get(dg)); scene.collection.objects.unlink(o); return me


# ---------------- a mass of foliage: a rounded form with leafy cells pushed out of it (as the kit's crowns, but one bough)
def leaf_mass(centre, R, flat, r, cell=0.55):
    bm = bmesh.new()
    for i in range(r.choice((2, 3, 3))):
        off = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-0.5, 0.5))) * R * (0.0 if i == 0 else 0.5)
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=R * (0.82 if i == 0 else r.uniform(0.5, 0.7)), matrix=Matrix.Translation(off))
    me = bpy.data.meshes.new("mass"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("mass", me)
    rm = o.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = max(R * 0.075, 0.1)
    sm = o.modifiers.new("smooth", "SMOOTH"); sm.factor = 0.7; sm.iterations = 3
    vt = bpy.data.textures.new("cells", "VORONOI"); vt.noise_scale = cell; vt.distance_metric = "DISTANCE"
    dv = o.modifiers.new("cells", "DISPLACE"); dv.texture = vt; dv.strength = -min(R * 0.24, 0.5); dv.mid_level = 0.6; dv.texture_coords = "GLOBAL"
    ct = bpy.data.textures.new("lumps", "CLOUDS"); ct.noise_scale = 0.3
    dp = o.modifiers.new("lumps", "DISPLACE"); dp.texture = ct; dp.strength = R * 0.07; dp.mid_level = 0.5
    o.location = Vector((r.uniform(-40, 40), r.uniform(-40, 40), r.uniform(-40, 40)))        # so each mass meets different cells
    out = baked(o); shift = Matrix.Translation(centre) @ Matrix.Diagonal((1, 1, flat, 1)) @ Matrix.Rotation(r.uniform(0, 6.283), 4, "Z")
    out.transform(shift)                                                                       # (baked in local space: the offset above only moved the texture)
    return out


def limb(points, radii):
    cu = bpy.data.curves.new("limb", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 2; cu.use_fill_caps = True
    sp = cu.splines.new("BEZIER"); sp.bezier_points.add(len(points) - 1)
    for bp, p, rad in zip(sp.bezier_points, points, radii):
        bp.co = p; bp.radius = rad; bp.handle_left_type = bp.handle_right_type = "AUTO"
    return baked(bpy.data.objects.new("limb", cu))


def joined(name, meshes, material, tones=None):
    bm = bmesh.new(); lay = bm.verts.layers.float.new("tone") if tones else None
    for i, me in enumerate(meshes):
        n0 = len(bm.verts); bm.from_mesh(me)
        if lay:
            bm.verts.ensure_lookup_table()
            for v in bm.verts[n0:]: v[lay] = tones[i]
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(material); return me


def bend(a, b, lift, k=0.5):
    """A point part-way from a to b, lifted: limbs curve up as they go out."""
    return a.lerp(b, k) + Vector((0, 0, lift))


# ---------------- the trees. Each returns (wood meshes, [(centre, R, flat)]).
def tree_boughs(r, twigs=False, full=False):
    th = r.uniform(3.2, 4.2); top = Vector((r.uniform(-0.3, 0.3), r.uniform(-0.3, 0.3), th)); wood = [limb([Vector((0, 0, -0.3)), Vector((0, 0, th * 0.5)), top], [0.46, 0.36, 0.3])]
    masses = []; n = r.choice((4, 5, 5)); a0 = r.uniform(0, 6.283); K = 1.28 if full else 1.0
    spec = [(a0 + i * 6.283 / n + r.uniform(-0.35, 0.35), r.uniform(24, 62), r.uniform(4.2, 6.2), top, False) for i in range(n)]
    spec.append((r.uniform(0, 6.283), 82, r.uniform(5.6, 7.0), top, True))                                 # the leader
    low = Vector((0, 0, th * r.uniform(0.62, 0.8)))
    for i in range(r.choice((1, 2))): spec.append((a0 + 0.9 + i * 3.1 + r.uniform(-0.4, 0.4), r.uniform(8, 24), r.uniform(3.6, 4.8), low, False))   # a low limb or two
    for a, el, L, root, leader in spec:
        el = math.radians(el); end = root + Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el))) * L
        mid = bend(root, end, 0.5); wood.append(limb([root, mid, end], [0.24, 0.16, 0.08]))
        if twigs:       # the open crown: each limb ends in a spray of small masses on twigs
            for j in range(r.choice((5, 6, 6))):
                dv = Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-0.3, 1.0))).normalized() * r.uniform(1.0, 2.1); tip = end + dv
                wood.append(limb([end, bend(end, tip, 0.15), tip], [0.08, 0.06, 0.04])); masses.append((tip, r.uniform(0.9, 1.4), r.uniform(0.62, 0.8)))
            for sgn in (-1, 1):
                side = mid + Vector((math.cos(a + sgn * 1.2), math.sin(a + sgn * 1.2), 0.25)) * r.uniform(1.3, 2.1)
                wood.append(limb([mid, side], [0.1, 0.05])); masses.append((side, r.uniform(0.85, 1.25), 0.7))
        else:           # boughs: one good mass on each limb, a smaller one on a side branch
            masses.append((end, r.uniform(1.9, 2.5) * (0.9 if leader else 1) * K, r.uniform(0.62, 0.78)))
            if not leader and (full or r.random() < 0.8):
                sgn = r.choice((-1, 1)); side = mid + Vector((math.cos(a + sgn * 1.1), math.sin(a + sgn * 1.1), -0.1)) * r.uniform(1.8, 2.6)
                wood.append(limb([mid, bend(mid, side, 0.2), side], [0.13, 0.09, 0.05])); masses.append((side, r.uniform(1.2, 1.7) * K, 0.68))
    if full: masses.append((top + Vector((0, 0, 2.6)), 2.3, 0.7))                                         # a heart to the crown
    return wood, masses


def tree_tiers(r):
    H = r.uniform(12.5, 15.0); wood = [limb([Vector((0, 0, -0.3)), Vector((r.uniform(-0.2, 0.2), 0, H * 0.5)), Vector((0, 0, H))], [0.5, 0.3, 0.07])]
    masses = []; a = r.uniform(0, 6.283); z = r.uniform(3.6, 4.4); k = 0
    while z < H - 1.0:
        f = (z - 3.6) / (H - 3.6); reach = (1 - f) ** 0.8 * r.uniform(4.2, 5.4) + 0.6
        for j in range(2 if f < 0.75 else 1):
            a += 2.4 + r.uniform(-0.4, 0.4); c0 = Vector((0, 0, z)); end = c0 + Vector((math.cos(a), math.sin(a), 0.12)) * reach * r.uniform(0.75, 1.0)
            wood.append(limb([c0, bend(c0, end, -0.15), end], [0.16 * (1 - f) + 0.05, 0.09, 0.04]))
            masses.append((c0.lerp(end, 0.62) + Vector((0, 0, 0.2)), reach * r.uniform(0.52, 0.62), r.uniform(0.26, 0.34)))
        z += r.uniform(1.9, 2.5) * (1 - 0.3 * f); k += 1
    masses.append((Vector((0, 0, H - 0.2)), 1.0, 0.8))
    return wood, masses


def tree_column(r):
    H = r.uniform(15.0, 18.0); wood = [limb([Vector((0, 0, -0.3)), Vector((0, 0, H * 0.5)), Vector((0, 0, H - 1.2))], [0.4, 0.25, 0.06])]
    masses = []; z = 3.6; a = r.uniform(0, 6.283)
    while z < H - 0.6:
        f = (z - 3.6) / (H - 3.6); R = (1.55 - 0.85 * f ** 1.5) * r.uniform(0.9, 1.1); a += 2.4
        c = Vector((math.cos(a), math.sin(a), 0)) * r.uniform(0.15, 0.5) * (1 - 0.6 * f) + Vector((0, 0, z)); masses.append((c, R, r.uniform(1.4, 1.7)))
        z += R * r.uniform(0.95, 1.2)
    return wood, masses


# ---------------- G: built like a real tree (owner, 11 Nov, with a picture of a tall, fine-leaved tree: "what we really
# want is this but I don't know if this is possible"). A trunk; a score of boughs spiralling up it, long low down and
# short at the top; each bough branching twice more into twigs; and on the twigs thousands of small sprays of leaves,
# each a flat card carrying a cut-out picture of a dozen leaves (how games draw foliage: the card is two triangles, the
# picture does the work). The sprays follow the branches, so the crown has the tree's own ragged shape and the sky
# shows through it. Colours grade up the crown as before.
def leaf_atlas(path):
    from PIL import Image, ImageDraw
    r = random.Random(3); T = 256; im = Image.new("RGBA", (T * 2, T * 2), (150, 170, 120, 0)); dr = ImageDraw.Draw(im)
    def leaf(cx, cy, ang, L, Wd, tone):
        pts = []
        for k in range(13):
            t = k / 12; w = math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t) * Wd; pts.append((t * L, w))
        pts += [(x, -y) for x, y in reversed(pts)]
        ca, sa = math.cos(ang), math.sin(ang); poly = [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]
        g = int(205 * tone); dr.polygon(poly, fill=(int(g * 0.93), g, int(g * 0.86), 255))
        dr.line([(cx, cy), (cx + L * 0.9 * ca, cy + L * 0.9 * sa)], fill=(int(g * 0.8), int(g * 0.86), int(g * 0.72), 255), width=2)
    for ty in range(2):
        for tx in range(2):
            ox, oy = tx * T, ty * T; n = r.choice((9, 10, 12)); bendk = r.uniform(-0.35, 0.35)
            stem = [(ox + T * 0.5 + bendk * T * 0.3 * (k / n) ** 2 * (1 if tx else -1), oy + T * 0.94 - (k / n) * T * 0.8) for k in range(n + 1)]
            dr.line(stem, fill=(120, 112, 92, 255), width=3)
            for k in range(1, n + 1):
                x, y = stem[k]; side = 1 if k % 2 else -1; ang = -math.pi / 2 + side * r.uniform(0.6, 1.25) + r.uniform(-0.15, 0.15)
                if k == n: ang = -math.pi / 2 + r.uniform(-0.3, 0.3)
                leaf(x, y, ang, r.uniform(62, 88) * (1.0 - 0.25 * k / n), r.uniform(17, 24), r.uniform(0.8, 1.12))
    im.save(path); return path


def grow(start, d, L, r0, r1, segs, curl, r, wander=0.16):
    pts, rad = [start.copy()], [r0]; p = start.copy(); dn = d.normalized()
    for i in range(1, segs + 1):
        t = i / segs; dn = (dn + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * wander + Vector((0, 0, curl * t ** 1.5))).normalized()
        p = p + dn * (L / segs); pts.append(p.copy()); rad.append(r0 + (r1 - r0) * t)
    return pts, rad


def along(pts, t):
    x = t * (len(pts) - 1); i = min(int(x), len(pts) - 2); return pts[i].lerp(pts[i + 1], x - i), (pts[i + 1] - pts[i]).normalized()


def side_dir(dn, r, lo=40, hi=65, lift=0.15):
    perp = dn.cross(Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1)))).normalized(); a = math.radians(r.uniform(lo, hi))
    v = dn * math.cos(a) + perp * math.sin(a); v.z = v.z * 0.6 + lift; return v.normalized()


_real = {}
def real_tree(seed):
    if seed in _real: return _real[seed]
    r = random.Random(seed * 977 + 13); H = r.uniform(15.5, 18.5); splines = []; cards = []
    wx, wy = r.uniform(-0.5, 0.5), r.uniform(-0.5, 0.5)
    trunk = [Vector((wx * math.sin(t * 2.6), wy * math.sin(t * 3.4 + 1), H * t - 0.3)) for t in [i / 10 for i in range(11)]]
    splines.append((trunk, [0.44 * (1 - t) ** 0.85 + 0.035 for t in [i / 10 for i in range(11)]]))
    def spray(p, size=None):
        cards.append((p + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-0.7, 0.7))) * 0.24, size or r.uniform(0.6, 1.0)))
    nb = r.choice((17, 19, 21)); a = r.uniform(0, 6.283)
    for i in range(nb):
        f = i / (nb - 1); t = 0.27 + 0.71 * f ** 0.92 + r.uniform(-0.012, 0.012); base, _ = along(trunk, min(t, 0.985)); a += 2.39996 + r.uniform(-0.45, 0.45)
        L = H * 0.34 * (0.5 + 0.5 * math.sin(math.pi * (0.12 + 0.8 * f))) * (1 - 0.5 * f ** 2) * r.uniform(0.7, 1.2) + 0.9
        el = math.radians(r.uniform(6, 26) + 34 * f); d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
        P, R1 = grow(base, d, L, 0.05 + 0.1 * (1 - f), 0.022, 7, r.uniform(0.07, 0.17), r); splines.append((P, R1))
        for j in range(int(L * 1.15) + 2):                                     # boughs divide
            u = r.uniform(0.28, 1.0); q, dn = along(P, u); L2 = L * r.uniform(0.3, 0.5) * (1.15 - 0.5 * u) + 0.5
            S, R2 = grow(q, side_dir(dn, r), L2, 0.04, 0.014, 5, r.uniform(0.05, 0.12), r); splines.append((S, R2))
            for k in range(r.choice((4, 5, 5))):                                # and again, into twigs that carry the leaves
                v = r.uniform(0.25, 1.0); q2, dn2 = along(S, v); L3 = r.uniform(0.7, 1.4)
                Tw, R3 = grow(q2, side_dir(dn2, r, 30, 70, 0.1), L3, 0.016, 0.008, 3, 0.05, r, 0.22); splines.append((Tw, R3))
                for m in range(int(L3 / 0.15)): spray(along(Tw, r.uniform(0.15, 1.0))[0])
            for m in range(int(L2 / 0.32)): spray(along(S, r.uniform(0.45, 1.0))[0])
        spray(P[-1], 1.0)
    for m in range(10): spray(trunk[-1] + Vector((0, 0, r.uniform(-0.6, 0.5))), r.uniform(0.7, 1.0))
    # the wood: one curve, a spline for every branch
    cu = bpy.data.curves.new("wood", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 1.0; cu.bevel_resolution = 1; cu.use_fill_caps = True
    for pts, rad in splines:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for pt, p_, rd in zip(sp.points, pts, rad): pt.co = (p_.x, p_.y, p_.z, 1.0); pt.radius = rd
    wood_me = baked(bpy.data.objects.new("wood", cu)); wood_me.materials.append(BARK)
    for pl in wood_me.polygons: pl.use_smooth = True
    # the leaves: a card for every spray, facing mostly up and out, lit as part of a rounded crown (so the tree shades as
    # a whole, soft, and does not glitter)
    verts, faces, uvs, tones, nrm = [], [], [], [], []
    for c, size in cards:
        n = Vector((r.uniform(-1, 1), r.uniform(-1, 1), abs(r.uniform(-1, 1)) + 0.35)).normalized(); tg = n.cross(Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1)))).normalized(); bt = n.cross(tg)
        i0 = len(verts); h = size * 0.5; verts += [c - tg * h - bt * h, c + tg * h - bt * h, c + tg * h + bt * h, c - tg * h + bt * h]; faces.append((i0, i0 + 1, i0 + 2, i0 + 3))
        tx, ty = r.choice((0, 1)), r.choice((0, 1)); uvs += [(tx * 0.5, ty * 0.5), (tx * 0.5 + 0.5, ty * 0.5), (tx * 0.5 + 0.5, ty * 0.5 + 0.5), (tx * 0.5, ty * 0.5 + 0.5)]
        tone = r.random(); tones += [tone] * 4
        out = Vector((c.x, c.y, (c.z - H * 0.55) * 0.5)); out = out.normalized() if out.length > 1e-3 else Vector((0, 0, 1)); nn = (out * 0.6 + Vector((0, 0, 0.3)) + n * 0.25).normalized(); nrm += [nn] * 4
    me = bpy.data.meshes.new("leaves"); me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops): uvl.data[li].uv = uvs[loop.vertex_index]
    at_ = me.attributes.new("tone", "FLOAT", "POINT"); at_.data.foreach_set("value", tones)
    for pl in me.polygons: pl.use_smooth = True
    me.normals_split_custom_set_from_vertices([tuple(v) for v in nrm]); me.materials.append(CARD)
    print("real tree", seed, "cards", len(cards), "branches", len(splines), "wood tris", len(wood_me.polygons), flush=True)
    _real[seed] = (bpy.data.objects.new("crown", me), bpy.data.objects.new("wood", wood_me)); return _real[seed]


m, nt, b = mat("leafcard"); CARD = m
img = bpy.data.images.load(leaf_atlas(os.path.join(OUTDIR, "leaf_atlas.png"))); tex = N_(nt, "ShaderNodeTexImage"); tex.image = img
tc = N_(nt, "ShaderNodeTexCoord"); sz = N_(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sz.inputs[0])
rampn = N_(nt, "ShaderNodeValToRGB"); els = rampn.color_ramp.elements
els[0].position = 0.0; els[0].color = lin("#35604a"); els[1].position = 1.0; els[1].color = lin("#b4cc88"); e = els.new(0.5); e.color = lin("#6a9862")
nt.links.new(sz.outputs["Z"], rampn.inputs[0])
col = mul(nt, rampn.outputs[0], tex.outputs["Color"]); col = mul(nt, col, (1.35, 1.35, 1.35, 1.0))
at = N_(nt, "ShaderNodeAttribute"); at.attribute_name = "tone"; col = mul(nt, col, grey(nt, at.outputs["Fac"], 0.8, 1.2))
nt.links.new(col, b.inputs["Base Color"])
tr = N_(nt, "ShaderNodeBsdfTranslucent"); nt.links.new(col, tr.inputs["Color"]); mx = N_(nt, "ShaderNodeMixShader"); mx.inputs["Fac"].default_value = 0.3
tp = N_(nt, "ShaderNodeBsdfTransparent"); mx2 = N_(nt, "ShaderNodeMixShader"); outn = nt.nodes["Material Output"]
nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2]); nt.links.new(tex.outputs["Alpha"], mx2.inputs["Fac"]); nt.links.new(tp.outputs[0], mx2.inputs[1]); nt.links.new(mx.outputs[0], mx2.inputs[2])
nt.links.new(mx2.outputs[0], outn.inputs["Surface"])

KINDS = {
    "G": ("Built like a real tree: branches, twigs, sprays of leaves", "real"),
    "A": ("As now: one merged crown", "kit"),
    "B": ("Full boughs: big masses of leaf on limbs", "full"),
    "C": ("Open boughs: separate masses, more sky", "open"),
    "D": ("Lacy crown: many small masses on twigs", "lace"),
    "E": ("Tiers: flat layers, like a cedar", "tiers"),
    "F": ("Mixed planting, with tall poplars", "mixed"),
}
BUILD = {"full": lambda r: tree_boughs(r, full=True), "open": lambda r: tree_boughs(r), "lace": lambda r: tree_boughs(r, twigs=True), "tiers": tree_tiers, "col": tree_column}
_made = {}
def build(kind, seed):
    """One tree model (two objects: crown, wood), made once per kind and seed."""
    key = (kind, seed)
    if kind == "real": return real_tree(seed)
    if key in _made: return _made[key]
    r = random.Random(seed * 131 + 7); wood, masses = BUILD[kind](r)
    masses = [(Vector((c.x, c.y, max(c.z, 3.4))), R, fl) for c, R, fl in masses]              # no foliage down at the foot of the trunk
    crown = bpy.data.objects.new("crown", joined("crown", [leaf_mass(c, R, fl, r) for c, R, fl in masses], LEAF, [r.random() for _ in masses]))
    trunk = bpy.data.objects.new("wood", joined("wood", wood, BARK))
    _made[key] = (crown, trunk); return _made[key]


KIT = {}
def kit(name):
    if not KIT:
        before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=rp("assets/models/trees/trees.glb"))
        bpy.context.view_layer.update(); new = [o for o in bpy.data.objects if o not in before]; mats = {o: o.matrix_world.copy() for o in new}
        for o in new:
            for c in list(o.users_collection): c.objects.unlink(o)
            if o.type == "MESH": KIT[o.name] = o; o["mw"] = [list(r) for r in mats[o]]
        for o in KIT.values():
            if "crown" in o.name: o.data.materials.clear(); o.data.materials.append(LEAF)
            else: o.data.materials.clear(); o.data.materials.append(BARK)
    return KIT[name + "_crown"], KIT[name + "_trunk"]


def place(coll, kind, seed, x, y, s, turn):
    if kind == "A":
        crown, trunk = kit(("oak_a", "oak_b", "wide_a", "oak_c", "wide_b")[seed % 5]); base = Matrix.Rotation(math.pi / 2, 4, "X") if crown.rotation_euler.x == 0 and False else Matrix.Identity(4)
        for src in (crown, trunk):
            o = bpy.data.objects.new("t", src.data); coll.objects.link(o); o.matrix_world = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(turn, 4, "Z") @ Matrix.Diagonal((s, s, s, 1)) @ Matrix([list(r) for r in src["mw"]])
        return
    kind = KINDS[kind][1]
    if kind == "mixed": kind = ("full", "lace", "open", "col", "full", "open", "col", "lace", "tiers")[seed % 9]
    for src in build(kind, seed % 3):
        o = bpy.data.objects.new("t", src.data); coll.objects.link(o); o.matrix_world = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(turn, 4, "Z") @ Matrix.Diagonal((s, s, s, 1))


# ---------------- the ground, a rail for scale (1.1 m), light, sky
def plane(name, x0, x1, y0, y1, z, material):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)]); me.materials.append(material)
    return link(bpy.data.objects.new(name, me))
plane("lawn", -900, 900, -200, 1500, 0.0, LAWN); plane("turf", -900, 900, -60, -16, 0.01, TURF)
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, -16, 1.06)) @ Matrix.Diagonal((400, 0.12, 0.2, 1)))
for i in range(-80, 81): bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((i * 2.4, -16, 0.5)) @ Matrix.Diagonal((0.09, 0.09, 1.0, 1)))
me = bpy.data.meshes.new("rail"); bm.to_mesh(me); bm.free(); me.materials.append(RAIL); link(bpy.data.objects.new("rail", me))

world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True; wn, wl = world.node_tree.nodes, world.node_tree.links
tcw = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); wr = wn.new("ShaderNodeValToRGB"); wl.new(tcw.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], wr.inputs[0])
els = wr.color_ramp.elements; els[0].position = 0.0; els[0].color = lin("#f6f1cf"); els[1].position = 0.55; els[1].color = lin("#a6d2cb"); mid = els.new(0.12); mid.color = lin("#eaf0d2")
wl.new(wr.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 0.75
sun_d = bpy.data.lights.new("sun", "SUN"); sun_d.energy = 7.0; sun_d.angle = math.radians(9); sun_d.color = (1.0, 0.92, 0.7); sun = link(bpy.data.objects.new("sun", sun_d))
d = Vector((-0.55, -0.6, 0.55)).normalized(); sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

scene.cycles.transparent_max_bounces = 24
scene.render.engine = "CYCLES"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.max_bounces = 6; scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.render.resolution_x, scene.render.resolution_y = RES
dm, nt, _b = mat("dist")
for n in list(nt.nodes): nt.nodes.remove(n)
out = N_(nt, "ShaderNodeOutputMaterial"); em = N_(nt, "ShaderNodeEmission"); cd = N_(nt, "ShaderNodeCameraData"); mr = N_(nt, "ShaderNodeMapRange")
mr.inputs["From Max"].default_value = 800; nt.links.new(cd.outputs["View Distance"], mr.inputs["Value"]); nt.links.new(mr.outputs["Result"], em.inputs["Color"]); nt.links.new(em.outputs[0], out.inputs["Surface"])
cam = link(bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))); scene.camera = cam; cam.data.sensor_fit = "VERTICAL"; cam.data.clip_end = 8000
e, a = Vector((3, -37, 2.0)), Vector((1, 0, 7.2)); cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler(); cam.data.angle_y = math.radians(38)
HAZE = os.environ.get("HAZEARGS", "70 520 0.6 #efecc6 #b4d4cc").split()


def shoot(tag):
    base_path = os.path.join(OUTDIR, tag); scene.render.filepath = base_path + "_raw.png"; scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = True; scene.render.image_settings.color_mode = "RGBA"          # its own outline, leaf by leaf: the sky goes in behind afterwards
    t = time.time(); bpy.ops.render.render(write_still=True)
    scene.render.film_transparent = False; scene.render.image_settings.color_mode = "RGB"
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


# the same planting for every kind: a group by the rail, with gaps; and a line further off
r0 = random.Random(5)
NEAR = [(-21, 2, 1.05), (-9, 7, 0.9), (4, 1, 1.12), (17, 6, 0.95), (29, 3, 1.0)]
FAR = [(-150 + i * 13 + r0.uniform(-3, 3), 95 + r0.uniform(-8, 14), r0.uniform(0.85, 1.2)) for i in range(26) if r0.random() < 0.78]
if os.environ.get("PORTRAIT"):
    NEAR, FAR = [(0, 0, 1.0)], []
    e, a = Vector((2, -30, 2.0)), Vector((0, 0, 8.6)); cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler(); cam.data.angle_y = math.radians(40)
labels = {}
for k, (label, _) in KINDS.items():
    if ONLY and k not in ONLY: continue
    coll = bpy.data.collections.new("trees_" + k); scene.collection.children.link(coll); rk = random.Random(11)
    for i, (x, y, s) in enumerate(NEAR + FAR): place(coll, k, i + int(os.environ.get("SEED", "0")), x, y, s, rk.uniform(0, 6.283))
    shoot(("portrait_" if os.environ.get("PORTRAIT") else "tree_") + k); labels["tree_" + k] = label
    coll.hide_render = True
json.dump(labels, open(os.path.join(OUTDIR, "labels.json"), "w"))
print("TOTAL", round(time.time() - T0), "s", flush=True)
