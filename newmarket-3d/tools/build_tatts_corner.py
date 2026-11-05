"""The Tattersalls corner of the Newmarket board, built in 3D and painted with the board itself.

    python3 newmarket-3d/tools/make_ground.py        # first: the ground and the tree spots
    python3 -c "exec(open('newmarket-3d/tools/build_tatts_corner.py').read())" [render] [samples]   (SHOT=board|ring|yard for one still)

The idea (owner, 5 Nov: "lean into the map as much as possible ... link the two together"): every building stands on
its painted footprint (newmarket-3d/layout.json, traced from assets/maps/newmarket-map.webp) at the painting's own
proportions, and the painting is projected back onto it. The board is drawn as if seen from the south with heights
drawn straight up the page, so a point (x, y, z) in metres sits on the painting at
    X = (x + 112) * 5,   Y = (48 - y - z) * 5          (pixels of the 2x crop; 0.2 m a pixel)
From the board's angle the 3D corner looks like the painting; move the camera and it has real depth. Faces the
painting can't show (backs, gable ends, the lantern) take flat colours from the painting. The ground is the painting
with its drawn buildings painted out (build/ground.jpg); 3D trees stand on the painted trees (build/trees.json) and
wear them too. Writes build/tatts_corner.glb (for the web) and with "render" Cycles stills in build/renders/.
World: metres, x east, y north, z up.
"""
import os, sys, json, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

REPO = os.path.abspath(".")
ROOT = os.path.join(REPO, "newmarket-3d"); BUILD = os.path.join(ROOT, "build")
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
RENDER = "render" in ARGS
SAMPLES = int(next((a for a in ARGS if a.isdigit()), "48"))
L = json.load(open(os.path.join(ROOT, "layout.json")))
TREES = json.load(open(os.path.join(BUILD, "trees.json")))
CW, CH = 1320, 900                                   # the 2x crop the layout is traced on

bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())
scene = bpy.context.scene
coll = scene.collection
R = random.Random(7)
GLOW = 0.62                                           # how much of the painting shows as painted (the rest is lit)

def W(X, Y):                                          # board pixels -> world metres (on the ground)
    return Vector((0.2 * X - 112.0, 48.0 - 0.2 * Y, 0.0))
def proj_uv(p):                                       # world -> the painting
    X = (p.x + 112.0) * 5.0; Y = (48.0 - p.y - p.z) * 5.0
    return (X / CW, 1.0 - Y / CH)
VIEW = Vector((0, -1, 1)).normalized()               # towards the painting's viewer

# ------------------------------------------------------------------ materials
# Every surface has its own colour, from the painting's palette, mottled a little like paint; and, through the "proj"
# UVs, the painting itself. PAINTW (one number for the whole scene) blends between them: 1 = the board, 0 = the model.
# A face the painting can't show carries pv = 0 and always shows its own colour.
PAINT_IMG = bpy.data.images.load(os.path.join(BUILD, "paint.jpg"))
PAINTW = []                                                                  # the mix nodes, set per still
def mixed(name, hexc, glow=0.3, rough=0.9, mottle=0.12, vcol=None, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; Lk = nt.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    if vcol:                                                                 # trees: their own leafy colours, tinted towards the painting's
        va = N.new("ShaderNodeVertexColor"); va.layer_name = vcol
        tn = N.new("ShaderNodeMix"); tn.data_type = "RGBA"; tn.blend_type = "MULTIPLY"; tn.inputs[0].default_value = 1.0
        Lk.new(va.outputs["Color"], tn.inputs[6]); tn.inputs[7].default_value = srgb(tint)
        own = tn.outputs[2]
    else:
        tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 6
        Lk.new(tc.outputs["Object"], nz.inputs["Vector"])
        rp = N.new("ShaderNodeMapRange"); rp.inputs[3].default_value = 1 - mottle; rp.inputs[4].default_value = 1 + mottle
        Lk.new(nz.outputs["Fac"], rp.inputs[0])
        col = N.new("ShaderNodeRGB"); col.outputs[0].default_value = srgb(hexc)
        mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1.0
        Lk.new(col.outputs[0], mul.inputs[6]); Lk.new(rp.outputs[0], mul.inputs[7])
        own = mul.outputs[2]
    uvn = N.new("ShaderNodeUVMap"); uvn.uv_map = "proj"
    tex = N.new("ShaderNodeTexImage"); tex.image = PAINT_IMG; tex.interpolation = "Cubic"; tex.extension = "EXTEND"
    Lk.new(uvn.outputs["UV"], tex.inputs["Vector"])
    pv = N.new("ShaderNodeVertexColor"); pv.layer_name = "pv"
    sep = N.new("ShaderNodeSeparateColor"); Lk.new(pv.outputs["Color"], sep.inputs[0])
    w = N.new("ShaderNodeMath"); w.operation = "MULTIPLY"; w.inputs[1].default_value = 1.0
    Lk.new(sep.outputs["Red"], w.inputs[0]); PAINTW.append(w)
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"
    Lk.new(w.outputs[0], mx.inputs[0]); Lk.new(own, mx.inputs[6]); Lk.new(tex.outputs["Color"], mx.inputs[7])
    Lk.new(mx.outputs[2], b.inputs["Base Color"]); Lk.new(mx.outputs[2], b.inputs["Emission Color"])
    gl = N.new("ShaderNodeMapRange"); Lk.new(w.outputs[0], gl.inputs[0]); gl.inputs[3].default_value = glow; gl.inputs[4].default_value = 0.66
    Lk.new(gl.outputs[0], b.inputs["Emission Strength"])
    m["own"] = hexc
    return m
def painted_material(name, image_path):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = bpy.data.images.load(image_path); tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"]); nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.5; b.inputs["Roughness"].default_value = 1.0
    return m
def flat(name, hexc, rough=0.95):
    m = material(name, hexc, rough); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = srgb(hexc); b.inputs["Emission Strength"].default_value = 0.45
    return m
MATS = {
    "wall": mixed("brick", "#a06446", mottle=0.16), "wall2": mixed("brick_dark", "#8b5539", mottle=0.16),
    "roof": mixed("slate", "#6b6964", mottle=0.1), "trim": mixed("stone", "#e2d4b4", mottle=0.06),
    "door": mixed("door_green", "#35503f"), "glass": mixed("glass_dark", "#2a3034", rough=0.4),
    "lead": mixed("lead_roof", "#a9b0ad", mottle=0.07, rough=0.6), "glaze": mixed("glazing", "#7f949d", rough=0.3),
    "rail": mixed("white_rail", "#efe9da"), "black": mixed("black", "#222020"), "chimney": mixed("chimney", "#8a4e36"),
}
NOPAINT = {"glaze", "black", "rail"}

def finish(k, name, paint=True, paint_above=None):
    """The kit's mesh, with the painting's UVs ("proj") and where the painting can show it ("pv")."""
    ob, tris = kit_to_object(k, name, MATS, coll)
    me = ob.data; names = [m.name for m in me.materials]
    nop = {MATS[k_].name for k_ in NOPAINT}
    bm = bmesh.new(); bm.from_mesh(me)
    uv = bm.loops.layers.uv.new("proj"); pv = bm.loops.layers.float_color.new("pv")
    for f in bm.faces:
        c = f.calc_center_median()
        ok = paint and names[f.material_index] not in nop and f.normal.dot(VIEW) >= 0.12 and (paint_above is None or c.z <= paint_above)
        for lp in f.loops:
            lp[uv].uv = proj_uv(lp.vert.co); lp[pv] = (1.0, 1.0, 1.0, 1.0) if ok else (0.0, 0.0, 0.0, 1.0)
    bm.to_mesh(me); bm.free()
    me.color_attributes.active_color = me.color_attributes["pv"]
    return ob

def beam(k, mat, p0, p1, w, h=None):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L_ = d.length
    if L_ < 1e-4: return
    x = d.normalized(); up = Vector((0, 0, 1)) if abs(x.z) < 0.95 else Vector((0, 1, 0))
    y = up.cross(x).normalized(); z = x.cross(y)
    m = Matrix(((x.x, y.x, z.x, 0), (x.y, y.y, z.y, 0), (x.z, y.z, z.z, 0), (0, 0, 0, 1)))
    k.boxm(mat, Matrix.Translation((p0 + p1) / 2) @ m, L_, w, h or w)

def frustum(k, mat, r0, z0, r1, z1, n=8, rot=math.pi / 8, cap=False):
    bm = k.bm(mat)
    a = [bm.verts.new(k.M @ Vector((r0 * math.cos(rot + 2 * math.pi * i / n), r0 * math.sin(rot + 2 * math.pi * i / n), z0))) for i in range(n)]
    b = [bm.verts.new(k.M @ Vector((r1 * math.cos(rot + 2 * math.pi * i / n), r1 * math.sin(rot + 2 * math.pi * i / n), z1))) for i in range(n)]
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if cap: bm.faces.new(b)
    bm.faces.new(a[::-1])

# ------------------------------------------------------------------ the ground: the board, its drawn buildings painted out
def ground():
    a, b = W(0, CH), W(CW, 0)
    bm = bmesh.new()
    v = [bm.verts.new((a.x, a.y, 0)), bm.verts.new((b.x, a.y, 0)), bm.verts.new((b.x, b.y, 0)), bm.verts.new((a.x, b.y, 0))]
    f = bm.faces.new(v); uv = bm.loops.layers.uv.new("UVMap")
    for loop, (u, w_) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): loop[uv].uv = (u, w_)
    me = bpy.data.meshes.new("ground"); bm.to_mesh(me); bm.free()
    me.materials.append(painted_material("board_ground", os.path.join(BUILD, "ground.jpg")))
    ob = bpy.data.objects.new("ground", me); coll.objects.link(ob)
    g = flat("grass_beyond", "#a8a271", 1.0)
    bpy.ops.mesh.primitive_plane_add(size=1, location=((a.x + b.x) / 2, (a.y + b.y) / 2, -0.03))
    o = bpy.context.object; o.name = "ground_beyond"; o.scale = (900, 900, 1); o.data.materials.append(g)

# ------------------------------------------------------------------ stable ranges, at the painting's proportions
H_EAVES, PITCH = 2.9, 27
def range_segment(k, A, B, depth, first, last, pavilions, seed):
    d = B - A; Lg = d.length; x = d.normalized(); n = Vector((-x.y, x.x, 0))
    ext0 = 0 if first else depth * 0.5; ext1 = 0 if last else depth * 0.5
    k.push(Matrix(((x.x, n.x, 0, A.x), (x.y, n.y, 0, A.y), (0, 0, 1, 0), (0, 0, 0, 1))))
    x0, x1 = -ext0, Lg + ext1
    k.box("wall", x0, x1, 0, depth, 0, H_EAVES)
    k.box("trim", x0 - 0.04, x1 + 0.04, -0.04, depth + 0.04, 0, 0.3)                    # plinth
    pitch = 3.4; nd = int((x1 - x0 - 1.5) // pitch)
    for i in range(nd):                                                          # stable doors: half-doors under a lintel
        cx = x0 + 0.75 + pitch * (i + 0.5)
        if any(abs(cx - t * Lg) < 4.6 for t in pavilions): continue
        k.box("door", cx - 0.55, cx + 0.55, -0.05, 0.02, 0.3, 2.2)
        k.box("trim", cx - 0.68, cx + 0.68, -0.08, 0.0, 2.2, 2.38)
        k.box("trim", cx - 0.55, cx + 0.55, -0.08, -0.04, 1.2, 1.28)
        if i % 2: k.box("glass", cx + 1.15, cx + 1.65, -0.03, 0.02, 1.3, 2.0)
    for i in range(int((x1 - x0) // 7)):
        cx = x0 + 3.5 + 7 * i; k.box("glass", cx - 0.3, cx + 0.3, depth - 0.02, depth + 0.03, 1.4, 2.0)
    k.gable_roof(x0, x1, 0, depth, H_EAVES, PITCH, ov=0.4)
    rise = (depth / 2 + 0.4) * math.tan(math.radians(PITCH))
    rng = random.Random(seed)
    nv = max(1, int(Lg // 24))
    for i in range(1, nv):                                                       # louvred ridge vents
        cx = x0 + (x1 - x0) * i / nv
        if any(abs(cx - p * Lg) < 6 for p in pavilions): continue
        zr = H_EAVES + rise + 0.2
        k.box("trim", cx - 0.55, cx + 0.55, depth / 2 - 0.55, depth / 2 + 0.55, zr - 0.3, zr + 0.6)
        k.hip_roof(cx - 0.55, cx + 0.55, depth / 2 - 0.55, depth / 2 + 0.55, zr + 0.6, 0.45, ov=0.2)
    if rng.random() < 0.6:
        cx = x0 + (x1 - x0) * rng.uniform(0.15, 0.85)
        k.box("chimney", cx - 0.32, cx + 0.32, depth * 0.62, depth * 0.62 + 0.64, H_EAVES + rise * 0.5, H_EAVES + rise + 0.9)
    for t in pavilions:                                                          # the taller gabled gatehouses
        cx = t * Lg; hw = 3.6
        k.box("wall2", cx - hw, cx + hw, -0.5, depth + 0.5, 0, 4.4)
        k.box("glass", cx - 1.2, cx + 1.2, -0.58, -0.45, 0.2, 2.9)                       # the archway through
        k.arc_band("trim", cx, 2.9, 1.2, 1.45, 0, math.pi, -0.62, -0.5, n=10)
        k.box("glass", cx - 0.45, cx + 0.45, -0.58, -0.5, 3.4, 4.1)
        k.push(Matrix.Translation((cx, 0, 0)) @ Matrix.Rotation(math.pi / 2, 4, "Z"))
        r2 = k.gable_roof(-0.5, depth + 0.5, -hw, hw, 4.4, 38, ov=0.35)
        k.pop()
        zc = 4.4 + r2
        k.box("trim", cx - 0.7, cx + 0.7, depth / 2 - 0.7, depth / 2 + 0.7, zc - 0.4, zc + 1.0)
        k.box("glaze", cx - 0.71, cx + 0.71, depth / 2 - 0.3, depth / 2 + 0.3, zc + 0.05, zc + 0.75)
        k.hip_roof(cx - 0.7, cx + 0.7, depth / 2 - 0.7, depth / 2 + 0.7, zc + 1.0, 0.8, ov=0.18, mat="lead")
        k.cyl("black", cx, depth / 2, zc + 1.8, zc + 2.6, 0.04, segs=4)
    k.pop()

def stable_ranges():
    for r in L["ranges"]:
        k = Kit(); P = [W(*p) for p in r["pts"]]
        segs = list(zip(P, P[1:])); total = sum((b - a).length for a, b in segs); run = 0
        for i, (a, b) in enumerate(segs):
            Lg = (b - a).length
            pv = [(t * total - run) / Lg for t in r.get("pavilions", []) if 0.04 < (t * total - run) / Lg < 0.96]
            range_segment(k, a, b, r["depth"], i == 0, i == len(segs) - 1, pv, sum(map(ord, r["id"])) + i)
            run += Lg
        finish(k, "range_" + r["id"])

# ------------------------------------------------------------------ the sale ring
def rotunda():
    rt = L["rotunda"]; c = W(*rt["at"]); ap = rt["apothem"]; Rc = ap / math.cos(math.pi / 8)
    k = Kit(); k.push(Matrix.Translation(c))
    rot = -math.pi / 2 + math.pi / 8
    H1, Z2, Z3, ZL = 10.5, 12.0, 15.6, 16.6                   # wall, the drum's foot and top, the lantern's foot
    frustum(k, "wall", Rc, 0, Rc, H1, rot=rot)                 # the brick drum (an octagonal prism)
    frustum(k, "trim", Rc + 0.25, H1 - 0.7, Rc + 0.25, H1, rot=rot)
    frustum(k, "trim", Rc + 0.12, 0, Rc + 0.12, 0.5, rot=rot)
    frustum(k, "trim", Rc + 0.1, 4.9, Rc + 0.1, 5.15, rot=rot)
    side = 2 * Rc * math.sin(math.pi / 8)
    for i in range(8):
        ang = 2 * math.pi * i / 8 - math.pi / 2
        k.push(Matrix.Rotation(ang + math.pi / 2, 4, "Z") @ Matrix.Translation((0, -ap, 0)))
        for j in (-1, 0, 1):
            x = j * side / 3.2
            if i == 0 and j == 0:                                                # the great doors, facing the paddock
                k.box("door", x - 1.5, x + 1.5, -0.1, 0.05, 0, 3.4)
                k.arc_band("trim", x, 3.4, 1.5, 1.85, 0, math.pi, -0.2, -0.05, n=12)
                continue
            for z0, hgt in ((1.0, 2.7), (6.0, 2.9)):                             # two tiers of arched windows
                k.box("glass", x - 0.5, x + 0.5, -0.08, 0.05, z0, z0 + hgt)
                k.arc_band("trim", x, z0 + hgt, 0.5, 0.7, 0, math.pi, -0.16, -0.04, n=8)
        k.pop()
    frustum(k, "lead", Rc + 1.3, H1, 9.6, Z2, rot=rot)        # the shallow lower roof
    for i in range(8):
        a = rot + 2 * math.pi * i / 8
        beam(k, "trim", ((Rc + 1.3) * math.cos(a), (Rc + 1.3) * math.sin(a), H1 + 0.1), (9.6 * math.cos(a), 9.6 * math.sin(a), Z2 + 0.1), 0.35, 0.25)
    frustum(k, "glaze", 9.4, Z2, 9.4, Z3 - 0.4, rot=rot)      # the glazed clerestory
    frustum(k, "trim", 9.6, Z3 - 0.4, 9.6, Z3, rot=rot)
    for i in range(8):
        a = rot + 2 * math.pi * i / 8
        k.box("trim", 9.4 * math.cos(a) - 0.3, 9.4 * math.cos(a) + 0.3, 9.4 * math.sin(a) - 0.3, 9.4 * math.sin(a) + 0.3, Z2, Z3)
    frustum(k, "lead", 10.3, Z3, 3.8, ZL, rot=rot)            # the upper roof
    for i in range(8):
        a = rot + 2 * math.pi * i / 8
        beam(k, "trim", (10.3 * math.cos(a), 10.3 * math.sin(a), Z3 + 0.08), (3.8 * math.cos(a), 3.8 * math.sin(a), ZL + 0.08), 0.26, 0.2)
    frustum(k, "glaze", 3.5, ZL, 3.5, ZL + 1.5, rot=rot)      # the lantern, its cap and finial
    frustum(k, "trim", 3.7, ZL + 1.5, 3.7, ZL + 1.75, rot=rot)
    for i in range(8):
        a = rot + 2 * math.pi * i / 8
        k.box("trim", 3.5 * math.cos(a) - 0.16, 3.5 * math.cos(a) + 0.16, 3.5 * math.sin(a) - 0.16, 3.5 * math.sin(a) + 0.16, ZL, ZL + 1.6)
    frustum(k, "lead", 3.9, ZL + 1.75, 0.3, ZL + 3.6, rot=rot, cap=True)
    k.cyl("black", 0, 0, ZL + 3.4, ZL + 4.5, 0.1, 0.05, segs=6)
    k.sphere("trim", 0, 0, ZL + 4.55, 0.22, sub=1)
    finish(k, "tattersalls_rotunda", paint_above=Z3)          # the lantern and its roof can't line up with the painting

# ------------------------------------------------------------------ houses by the ring
def houses():
    k = Kit()
    for h in L["houses"]:
        c = W(*h["at"]); a = math.radians(-h["turn"])
        k.push(Matrix.Translation(c) @ Matrix.Rotation(a, 4, "Z"))
        w, d = h["w"], h["d"]
        k.box("wall", -w / 2, w / 2, 0, d, 0, 4.6)
        k.box("trim", -w / 2 - 0.04, w / 2 + 0.04, -0.04, d + 0.04, 2.3, 2.42)
        for xw in (-w / 4, w / 4):
            k.box("glass", xw - 0.4, xw + 0.4, -0.04, 0.02, 2.8, 3.9); k.box("trim", xw - 0.5, xw + 0.5, -0.08, 0.0, 2.7, 2.8)
        k.box("glass", -w / 4 - 0.4, -w / 4 + 0.4, -0.04, 0.02, 0.7, 1.8)
        k.door(w / 6, 0, 0, 1.0, 2.1)
        k.hip_roof(-w / 2, w / 2, 0, d, 4.6, 2.2, ov=0.4)
        k.box("chimney", w / 2 - 1.3, w / 2 - 0.6, d / 2 - 0.35, d / 2 + 0.35, 5.2, 7.6)
        k.pop()
    finish(k, "houses")

# ------------------------------------------------------------------ rails round the paddock and rings
def rails():
    k = Kit()
    for o in L["ovals"]:
        c = W(*o["at"]); rx, ry = o["rx"] * 0.2, o["ry"] * 0.2; t = math.radians(-o["turn"])
        per = math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
        n = max(16, int(per / o["posts"]))
        pts = [Matrix.Rotation(t, 4, "Z") @ Vector((rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n), 0)) + c for i in range(n)]
        for i, p in enumerate(pts):
            if o["id"] == "paddock" and 0.70 < i / n < 0.76: continue
            k.box("rail", p.x - 0.07, p.x + 0.07, p.y - 0.07, p.y + 0.07, 0, 1.2)
            q = pts[(i + 1) % n]
            for z in (0.6, 1.08): beam(k, "rail", (p.x, p.y, z), (q.x, q.y, z), 0.07, 0.11)
    finish(k, "rails", paint=False)

# ------------------------------------------------------------------ horseboxes, where the painted ones stood
def lorries():
    k = Kit()
    for lo in L["lorries"]:
        c = W(*lo["at"]); a = math.radians(-lo["turn"])
        name = "body_" + lo["colour"].strip("#")
        if name not in MATS: MATS[name] = mixed(name, lo["colour"], rough=0.6)
        k.push(Matrix.Translation(c) @ Matrix.Rotation(a, 4, "Z"))
        k.box(name, -3.0, 1.8, -1.1, 1.1, 0.6, 3.0); k.box("trim", -3.05, 1.85, -1.13, 1.13, 2.3, 2.45)
        k.box(name, 1.8, 3.5, -1.0, 1.0, 0.6, 2.4); k.box("glass", 2.6, 3.53, -0.85, 0.85, 1.6, 2.2)
        for x in (-2.0, 2.6):
            for y in (-1.0, 1.0): k.disc_y("black", x, y - 0.14 * (1 if y > 0 else -1), y + 0.14 * (1 if y > 0 else -1), 0.5, 0.5, segs=14)
        k.pop()
    finish(k, "horseboxes")

# ------------------------------------------------------------------ trees on the painted trees, wearing them
def trees():
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "assets/models/trees/trees.glb"))
    lib = {o.name: o for o in bpy.data.objects if o.name.endswith(("_crown", "_trunk"))}
    for o in [o for o in bpy.data.objects if o.name.endswith("_crown_far")]: bpy.data.objects.remove(o)
    variants = ["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]
    trunk_m = mixed("trunk", "#4a3a2a")
    bmA = bmesh.new()
    for i, t in enumerate(TREES):
        p = W(t["x"], t["y"]); s = max(0.45, min(1.2, t["r"] * 0.2 / 4.6)); v = variants[i % len(variants)]
        rz = R.uniform(0, 6.28); sz = s * R.uniform(0.85, 1.0)
        M = Matrix.Translation((p.x, p.y, 0)) @ Matrix.Rotation(rz, 4, "Z") @ Matrix.Diagonal((s, s, sz, 1))
        for part, mi in (("_trunk", 0), ("_crown", 1)):
            src = lib.get(v + part)
            if not src: continue
            tmp = bmesh.new(); tmp.from_mesh(src.data); bmesh.ops.transform(tmp, matrix=M, verts=tmp.verts)
            for f in tmp.faces: f.material_index = mi
            me = bpy.data.meshes.new("t"); tmp.to_mesh(me); tmp.free(); bmA.from_mesh(me); bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new("trees"); uv = bmA.loops.layers.uv.new("proj"); pv = bmA.loops.layers.float_color.new("pv")
    for f in bmA.faces:
        for lp in f.loops: lp[uv].uv = proj_uv(lp.vert.co); lp[pv] = (1.0, 1.0, 1.0, 1.0)   # every crown wears its painted tree
    bmA.to_mesh(me); bmA.free()
    me.materials.append(trunk_m); me.materials.append(mixed("crowns", "#5d6b3c", vcol="Color", tint="#9fa06a"))
    ob = bpy.data.objects.new("trees", me); coll.objects.link(ob)
    for o in lib.values(): bpy.data.objects.remove(o)

def people():
    bpy.ops.import_scene.gltf(filepath=os.path.join(REPO, "assets/models/architecture/crowd_people.glb"))
    figs = [o for o in bpy.data.objects if o.name.startswith("person_")]
    spots = [(470, 300), (500, 312), (520, 296), (600, 280), (612, 292), (300, 600), (330, 590), (560, 580), (575, 572), (640, 600),
             (1010, 600), (990, 640), (1120, 580), (700, 470), (690, 480), (430, 440), (520, 455), (820, 470), (250, 640), (420, 620)]
    for i, (X, Y) in enumerate(spots):
        src = figs[i % len(figs)]; o = bpy.data.objects.new(f"person{i:02d}", src.data); coll.objects.link(o)
        p = W(X, Y); o.location = (p.x + R.uniform(-1, 1), p.y + R.uniform(-1, 1), 0); o.rotation_euler.z = R.uniform(0, 6.28)
        o["still_only"] = True
    for f in figs: bpy.data.objects.remove(f)

ground(); stable_ranges(); rotunda(); houses(); rails(); lorries(); trees()

os.makedirs(BUILD, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=os.path.join(BUILD, "tatts_corner.glb"), export_format="GLB", export_apply=True, export_yup=True,
                          export_image_format="JPEG", export_jpeg_quality=88, export_cameras=False, export_lights=False,
                          export_vertex_color="ACTIVE", export_all_vertex_colors=True, export_texcoords=True)
print("exported", os.path.join(BUILD, "tatts_corner.glb"), flush=True)
if RENDER: people()

# ------------------------------------------------------------------ stills
if RENDER:
    w = bpy.data.worlds.new("sky"); scene.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    lp = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); rp = nt.nodes.new("ShaderNodeValToRGB")
    neg = nt.nodes.new("ShaderNodeVectorMath"); neg.operation = "SCALE"; neg.inputs["Scale"].default_value = -1
    nt.links.new(lp.outputs["Incoming"], neg.inputs[0]); nt.links.new(neg.outputs[0], sep.inputs[0])
    el = rp.color_ramp.elements; el[0].position = 0.0; el[0].color = srgb("#f1e4c6"); el[1].position = 0.45; el[1].color = srgb("#86aed4")
    e2 = el.new(0.12); e2.color = srgb("#dfe3dc")
    nt.links.new(sep.outputs["Z"], rp.inputs[0]); nt.links.new(rp.outputs[0], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.8
    sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.6; sun.angle = math.radians(3.0); sun.color = (1.0, 0.94, 0.84)
    so = bpy.data.objects.new("sun", sun); coll.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-38))
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.render.image_settings.file_format = "JPEG"; scene.render.image_settings.quality = 90
    os.makedirs(os.path.join(BUILD, "renders"), exist_ok=True)
    centre = W(CW / 2, CH / 2)
    SHOTS = {
        # the board's own view: looking north and down at 45 degrees (the painting squashed north-south by 0.71; stretched back after)
        "board": dict(ortho=CW * 0.2, size=(1600, int(1600 * CH / CW * 0.7071)), loc=centre + Vector((0, -300, 300)), look=centre),
        "ring": dict(lens=30, size=(1600, 1000), loc=W(300, 520) + Vector((0, 0, 24)), look=W(560, 200) + Vector((0, 0, 6))),
        "yard": dict(lens=26, size=(1600, 1000), loc=W(150, 800) + Vector((0, 0, 8)), look=W(600, 560) + Vector((0, 0, 2))),
        "low": dict(lens=24, size=(1600, 1000), loc=W(470, 420) + Vector((0, 0, 2.2)), look=W(560, 230) + Vector((0, 0, 9))),
    }
    only = os.environ.get("SHOT")
    for name, s in SHOTS.items():
        if only and name not in only.split(","): continue
        cam = bpy.data.cameras.new(name)
        if "ortho" in s: cam.type = "ORTHO"; cam.ortho_scale = s["ortho"]
        else: cam.lens = s["lens"]
        cam.clip_end = 3000
        co = bpy.data.objects.new(name, cam); coll.objects.link(co); co.location = s["loc"]
        co.rotation_euler = (s["look"] - s["loc"]).to_track_quat("-Z", "Y").to_euler()
        scene.render.resolution_x, scene.render.resolution_y = s["size"]
        for wn in PAINTW: wn.inputs[1].default_value = 1.0 if name == "board" else 0.0
        scene.camera = co; scene.render.filepath = os.path.join(BUILD, "renders", name + ".jpg")
        bpy.ops.render.render(write_still=True); print("rendered", name, flush=True)
