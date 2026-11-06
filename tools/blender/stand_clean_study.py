"""Grandstand finish study: Ascot's stand executed like the owner's pastel-street precedent (6 Nov 2026).

    python -c "exec(open('tools/blender/stand_clean_study.py').read())" [samples] [variant]

Not about the street's colours: about its execution. Clean forms with every edge rounded so it catches a line
of light, smooth unbroken matte surfaces, deep soft shadows and bounce light, crisp dark detailing (railings,
window frames), a shallow model-like focus, all at high resolution. Ascot keeps its own colours.

variant  clean   bevelled edges, clean matte materials, soft light (the study)
         today   the stand as built (no bevels, today's flat materials), same light, for comparison
Writes reference/architecture/clean-study/<variant>_<camera>.png, from the race view's own camera places
(course axes x east, z south, y up -> Blender x, -y, z).
"""
import os, sys, math, json
import bpy
from mathutils import Vector, Matrix

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SAMPLES = int(ARGS[0]) if ARGS and ARGS[0].isdigit() else 64
VARIANT = next((a for a in ARGS if a in ("clean", "today", "soft", "accent")), "clean")
SOFT = VARIANT in ("soft", "accent")
ACCENT = VARIANT == "accent"
CAMS = [a for a in ARGS if a.startswith("cam=")]
OUT = rp("reference/architecture/clean-study"); os.makedirs(OUT, exist_ok=True)
COURSE = json.load(open(rp("courses/ascot.json")))
FRONT = COURSE["grandstand"]["frontLine"]
W = COURSE["trackWidth"]
RES = (1600, 900) if not os.environ.get("QUICK") else (800, 450)
if os.environ.get("RES"): RES = tuple(int(v) for v in os.environ["RES"].split("x"))
CROWD_GLB = os.environ.get("CROWD", "assets/models/architecture/crowd_people.glb")   # the crowd figures (crowd concepts)
OUT_TAG = os.environ.get("TAG", "")

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


def principled(name, hexc, rough=0.8, metal=0.0, coat=0.0, sss=0.0, bump=0.0, bump_scale=6.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.35
    if sss:   # a touch of light glowing through the edges, like painted clay or plaster
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.08, 0.05, 0.03)
        b.inputs["Subsurface Scale"].default_value = 0.05
    if bump:  # the faintest plaster tooth, so big walls aren't dead flat
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = bump_scale; n.inputs["Detail"].default_value = 4
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.02
        nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def clay(name, hexc, rough=0.92, sss=0.12, tooth=0.12, mottle=0.035):
    """Matte painted clay: no shine (low specular, no coat), a fine tooth in the surface and the faintest
    unevenness in the colour, measured in metres on the object (not stretched over the whole stand)."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.12
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss
        b.inputs["Subsurface Radius"].default_value = (0.09, 0.06, 0.04)
        b.inputs["Subsurface Scale"].default_value = 0.05
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fine = nt.nodes.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 9.0; fine.inputs["Detail"].default_value = 6; fine.inputs["Roughness"].default_value = 0.65
    broad = nt.nodes.new("ShaderNodeTexNoise"); broad.inputs["Scale"].default_value = 0.35; broad.inputs["Detail"].default_value = 3
    nt.links.new(tc.outputs["Object"], fine.inputs["Vector"]); nt.links.new(tc.outputs["Object"], broad.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = tooth; bp.inputs["Distance"].default_value = 0.01
    nt.links.new(fine.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    c = lin(hexc)
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.inputs[6].default_value = c
    rmp = nt.nodes.new("ShaderNodeMapRange"); rmp.inputs["To Min"].default_value = 1 - mottle; rmp.inputs["To Max"].default_value = 1 + mottle
    nt.links.new(broad.outputs["Fac"], rmp.inputs["Value"])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"): nt.links.new(rmp.outputs["Result"], comb.inputs[k])
    nt.links.new(comb.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def no_green_bounce(m, bounce_hex):
    """The grass looks green to the camera but bounces a warm neutral light onto the stand, so the stone
    doesn't pick up a green cast (the precedent's ground is warm)."""
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]; out = nt.nodes["Material Output"]
    lp = nt.nodes.new("ShaderNodeLightPath"); d = nt.nodes.new("ShaderNodeBsdfDiffuse"); d.inputs["Color"].default_value = lin(bounce_hex)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs["Fac"]); nt.links.new(d.outputs[0], mx.inputs[1]); nt.links.new(b.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def plane(name, x0, x1, y0, y1, mat, z=0.0):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    return ob


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


# ---------------- light: a warm low-ish sun with a soft edge, a painted sky that fills the shade with blue
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (0.78, 0.8, 0.82, 1)
ramp.color_ramp.elements[1].position = 0.55; ramp.color_ramp.elements[1].color = (0.18, 0.4, 0.86, 1)
wl.new(ramp.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 0.55
if SOFT:
    # softer and warmer: a pastel sky (peach at the horizon, dusty blue above) instead of an intense blue one
    ramp.color_ramp.elements[0].color = (1.0, 0.86, 0.74, 1); ramp.color_ramp.elements[1].color = (0.56, 0.7, 0.9, 1)
    ramp.color_ramp.elements[1].position = 0.62
    mid = ramp.color_ramp.elements.new(0.16); mid.color = (0.93, 0.87, 0.85, 1)
    wn["Background"].inputs[1].default_value = 0.8
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object; sun.data.energy = 6.0; sun.data.angle = math.radians(3); sun.data.color = (1.0, 0.86, 0.68)
if SOFT:   # a big soft sun: shadows with feathered edges, warm peach light
    sun.data.energy = 4.6; sun.data.angle = math.radians(14); sun.data.color = (1.0, 0.8, 0.62)
# a raking afternoon sun from the west, a little in front of the stand, so every veranda, cornice and
# balcony throws a long soft shadow along the front (course axes (-1, 0.62, -0.42) -> Blender)
d = Vector((-1.0, 0.32, 0.45)).normalized()
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

grass = principled("grass", "#7d9f52", 0.95); turf = principled("turf", "#8fb75f", 0.95)
if SOFT:
    grass = no_green_bounce(principled("grass", "#86a45c", 0.97), "#9c8f78"); turf = no_green_bounce(principled("turf", "#93b466", 0.97), "#a29680")
rail = principled("rail", "#f4f2ea", 0.5 if not SOFT else 0.92)

# ---------------- the stand: full detail, in world axes, origin at the clock tower on the front line
parts = import_glb(rp("assets/models/architecture/ascot_main_stand.glb"))
root = bpy.data.objects.new("stand", None); scene.collection.objects.link(root)
for o in parts:
    if o.parent is None: o.parent = root
root.location = (0, -FRONT, 0)

if VARIANT in ("clean", "soft", "accent"):
    # Ascot's own palette, cleaned up: warm cream stone, white paintwork, slate, and the ironwork, doors and
    # glass dark so they read as crisp drawn detail against the pale stone (the street's dark railings and windows)
    MAT = {
        "gs_wall": principled("c_wall", "#e9dcc0", 0.72, sss=0.15, bump=0.06, bump_scale=3.0),
        "gs_podium": principled("c_podium", "#d9c9a6", 0.78, sss=0.1, bump=0.08, bump_scale=2.0),
        "gs_trim": principled("c_trim", "#f7f3ea", 0.55, sss=0.2),
        "gs_roof": principled("c_roof", "#5f6b78", 0.6, coat=0.25),
        "gs_iron": principled("c_iron", "#26372f", 0.45, coat=0.4),
        "gs_glass": principled("c_glass", "#1e2a36", 0.08, coat=0.6),
        "gs_door": principled("c_door", "#2f4c3c", 0.45, coat=0.4),
        "gs_gilt": principled("c_gilt", "#c9a560", 0.35, metal=0.8),
        "gs_steps": principled("c_steps", "#d8ccb0", 0.8),
        "gs_clock_face": principled("c_clock", "#fbf8ef", 0.5, sss=0.2),
        "gs_clock_dark": principled("c_clockd", "#1d2024", 0.4),
    }
    if SOFT:
        # the same Ascot colours, warmed a touch, every surface matte clay: nothing shines, nothing reflects
        MAT = {
            "gs_wall": clay("s_wall", "#ecdcc0", 0.93, sss=0.15, tooth=0.14),
            "gs_podium": clay("s_podium", "#dccaa8", 0.95, sss=0.1, tooth=0.18),
            "gs_trim": clay("s_trim", "#f6eee0", 0.9, sss=0.18, tooth=0.1),
            "gs_roof": clay("s_roof", "#7c7e86", 0.95, sss=0.0, tooth=0.15),
            "gs_iron": clay("s_iron", "#2f4236", 0.85, sss=0.0, tooth=0.05, mottle=0.0),
            "gs_glass": clay("s_glass", "#34323f", 0.8, sss=0.0, tooth=0.02, mottle=0.0),
            "gs_door": clay("s_door", "#3a5545", 0.88, sss=0.0, tooth=0.06),
            "gs_gilt": clay("s_gilt", "#c8a466", 0.75, sss=0.0, tooth=0.05),
            "gs_steps": clay("s_steps", "#dccfb3", 0.95, tooth=0.16),
            "gs_clock_face": clay("s_clock", "#fbf5ea", 0.9, sss=0.15, tooth=0.05),
            "gs_clock_dark": clay("s_clockd", "#25262a", 0.85, sss=0.0, tooth=0.0, mottle=0.0),
        }
    for o in parts:
        if o.type != "MESH": continue
        for i, slot in enumerate(o.material_slots):
            base = (slot.material.name if slot.material else "").split(".")[0]
            if base in MAT: o.material_slots[i].material = MAT[base]
        # every edge rounded: a narrow bevel catches a line of light along each sill, cornice and balcony
        bpy.context.view_layer.objects.active = o
        for p in o.data.polygons: p.use_smooth = True
        bv = o.modifiers.new("bevel", "BEVEL")
        bv.width = 0.06; bv.segments = 3; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(40)
        bv.use_clamp_overlap = True; bv.harden_normals = True; bv.profile = 0.6
        o.modifiers.new("weights", "WEIGHTED_NORMAL").keep_sharp = True

# ---------------- accents: a few touches of pastel to bring the stand to life, not overdone
# (variant "accent"): flags on the clock tower and the pavilion roofs, pastel doors along the central stretch,
# coloured balusters picking out the clock block and the pavilions, striped awnings over the central doors.
if ACCENT:
    import bmesh
    bpy.context.view_layer.update()
    PAL = {"sage": "#8db58c", "powder": "#8eb0d6", "blush": "#e6998b", "butter": "#eccd7c", "lilac": "#b49fd2"}
    AM = {k: clay("a_" + k, v, 0.9, sss=0.1, tooth=0.08) for k, v in PAL.items()}
    canvas = clay("a_canvas", "#f7efe0", 0.92, sss=0.15, tooth=0.05)
    pole_mat = clay("a_pole", "#f4eee2", 0.85, sss=0.0, tooth=0.0, mottle=0.0)
    gilt_mat = clay("a_finial", "#c8a466", 0.7, sss=0.0, tooth=0.0, mottle=0.0)

    def by_mat(name):
        return [o for o in parts if o.type == "MESH" and any(sl.material and sl.material.name.startswith(MAT[name].name) for sl in o.material_slots)]

    def islands(o):
        """Each separate piece of a mesh (a baluster, a door), with its world bounding box."""
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        seen, out, M = set(), [], o.matrix_world
        for f in bm.faces:
            if f.index in seen: continue
            stack, comp = [f], []; seen.add(f.index)
            while stack:
                g = stack.pop(); comp.append(g.index)
                for v in g.verts:
                    for h in v.link_faces:
                        if h.index not in seen: seen.add(h.index); stack.append(h)
            ps = [M @ v.co for i in comp for v in bm.faces[i].verts]
            lo = Vector((min(p.x for p in ps), min(p.y for p in ps), min(p.z for p in ps)))
            hi = Vector((max(p.x for p in ps), max(p.y for p in ps), max(p.z for p in ps)))
            out.append((comp, lo, hi))
        bm.free()
        return out

    def recolour(o, faces, mat):
        if mat.name not in [sl.material.name for sl in o.material_slots if sl.material]:
            o.data.materials.append(mat)
        k = [sl.material.name for sl in o.material_slots].index(mat.name)
        for i in faces: o.data.polygons[i].material_index = k

    MODS = COURSE["grandstand"]["modules"]
    def module_at(x):
        for m in MODS:
            if m["xWest"] <= x <= m["xEast"]: return m
        return None

    # doors: the central stretch's doors in pastels, one colour per building; the rest stay dark green
    DOOR_COL = {"clock_centre": "sage", "three_storey_block": "butter", "grand_pavilion": "powder", "ironwork_bay": "blush",
                "pavilion": "lilac", "window_block": "butter", "link": "blush", "end_pavilion": "sage"}
    # each building's stripe colour for its awnings, in turn along the stand (a building = a run of one module)
    STRIPES = ["blush", "sage", "butter", "powder", "lilac"]
    bcol, last, k = {}, None, -1
    for m in sorted(MODS, key=lambda m: -m["xEast"]):
        if m["module"] != last: k += 1; last = m["module"]
        bcol[m["xEast"]] = STRIPES[k % len(STRIPES)]
    def stripe_at(x):
        m = module_at(x)
        return bcol[m["xEast"]] if m else "blush"
    doors_front = []
    for o in by_mat("gs_door"):
        for comp, lo, hi in islands(o):
            x = (lo.x + hi.x) / 2; m = module_at(x)
            if m and -110 < x < 220 and m["module"] in DOOR_COL:
                recolour(o, comp, AM[DOOR_COL[m["module"]]])
            if m and hi.y > -FRONT - 0.6 and hi.z < 4.0 and hi.x - lo.x > 0.6: doors_front.append((lo, hi, stripe_at(x)))
    # the arched openings and windows in the stone base get awnings too
    for o in by_mat("gs_glass"):
        for comp, lo, hi in islands(o):
            x = (lo.x + hi.x) / 2
            if hi.y > -FRONT - 0.6 and hi.z < 3.4 and lo.z > 0.2 and hi.x - lo.x > 0.8 and module_at(x):
                doors_front.append((lo, hi, stripe_at(x)))
    # balusters: the clock block's balustrades in sage, the grand pavilions' in powder blue, the small pavilions' in blush
    BAL = {"clock_centre": "sage", "grand_pavilion": "powder", "pavilion": "blush"}     # by building, wherever it stands
    nb = 0
    for o in by_mat("gs_trim"):
        for comp, lo, hi in islands(o):
            sx, sy, sz = hi.x - lo.x, hi.y - lo.y, hi.z - lo.z
            if max(sx, sy) < 0.13 and 0.55 < sz < 1.1:
                m = module_at((lo.x + hi.x) / 2)
                if m and m["module"] in BAL: recolour(o, comp, AM[BAL[m["module"]]]); nb += 1
    print("accents: %d balusters, %d front doors" % (nb, len(doors_front)), flush=True)

    def add_mesh(name, verts, faces, mats, fmat=None):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
        for m in mats: me.materials.append(m)
        if fmat:
            for p, k in zip(me.polygons, fmat): p.material_index = k
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
        return ob

    def flag(base, h, cols, w=3.4, fh=2.1, phase=0.0):
        """A white pole with a gilt ball, and a cloth flag rippling out to the east (two colours: top/bottom)."""
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=h, location=(base.x, base.y, base.z + h / 2), vertices=10)
        p = bpy.context.object; p.data.materials.append(pole_mat)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(base.x, base.y, base.z + h + 0.1), segments=12, ring_count=8)
        bpy.context.object.data.materials.append(gilt_mat)
        nx, nz = 16, 8
        vs, fs, fm = [], [], []
        for j in range(nz + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / nz
                x = u * w; z = base.z + h - 0.15 - v * fh
                y = 0.32 * math.sin(u * 5.5 + phase) * u + 0.08 * math.sin(v * 3 + u * 4)
                vs.append((base.x + x, base.y + y, z - 0.12 * u * u))
        for j in range(nz):
            for i in range(nx):
                a = j * (nx + 1) + i
                fs.append((a, a + 1, a + nx + 2, a + nx + 1)); fm.append(0 if j < nz / 2 else 1)
        ob = add_mesh("flag", vs, fs, [AM[cols[0]], AM[cols[1]]], fm)
        ob.modifiers.new("thick", "SOLIDIFY").thickness = 0.02

    # the clock tower: the highest point near x 0
    stand_pts = [(o.matrix_world @ v.co) for o in parts if o.type == "MESH" for v in o.data.vertices]
    top = max((p for p in stand_pts if abs(p.x) < 3.0), key=lambda p: p.z)
    # the clock tower keeps the photos' cross; flags fly along the back of the roof terraces instead
    back = {}
    for p in stand_pts:
        kx = round(p.x / 4) * 4
        if p.z > back.get(kx, Vector((0, 0, 0))).z: back[kx] = p
    TFLAG = [("blush", "blush"), ("sage", "sage"), ("butter", "butter"), ("powder", "powder"), ("lilac", "lilac")]
    # flags along the top of the terraces' back walls (owner's markup): one every five bays on the open terraces
    wall_pts = [p for p in stand_pts if p.z < 20.5]
    i = 0
    for x in [x0 + 0.0 for x0 in range(-96, 404)][::1]:
        pass
    xs, x = [], 403.25
    while x > -100:
        m = module_at(x)
        if m and m["module"] == "terrace_stand" and not m.get("roof"):
            xs.append(x)
        x -= 17.5
    for x in xs:
        pts = [p for p in wall_pts if abs(p.x - x) < 2.0]
        if not pts: continue
        b = max(pts, key=lambda p: p.z)
        flag(Vector((x, b.y + 0.4, b.z)), 4.0, TFLAG[i % len(TFLAG)], w=2.4, fh=1.5, phase=i * 0.9); i += 1
    # pavilion roofs: a flag at each ridge (highest roof point of the module)
    roofs = [(o.matrix_world @ v.co) for o in by_mat("gs_roof") for v in o.data.vertices]
    FLAG_COL = [("blush", "blush"), ("powder", "powder"), ("sage", "butter"), ("lilac", "lilac"), ("butter", "blush"), ("powder", "sage")]
    k = 0
    for m in MODS:
        if m["module"] in ("grand_pavilion", "pavilion", "end_pavilion"):
            pts = [p for p in roofs if m["xWest"] + 1 < p.x < m["xEast"] - 1]
            if not pts: continue
            r = max(pts, key=lambda p: p.z)
            flag(Vector(((m["xWest"] + m["xEast"]) / 2, r.y, r.z)), 4.5, FLAG_COL[k % len(FLAG_COL)], phase=k * 1.3)
            k += 1

    # striped awnings over the front doors of the clock block and the grand pavilions next to it
    def awning(lo, hi, col):
        x0, x1 = lo.x - 0.5, hi.x + 0.5; yw = hi.y + 0.02; zt = hi.z + 0.55
        out, drop, n = 1.9, 0.85, max(4, round((x1 - x0) / 0.36))
        vs, fs, fm = [], [], []
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            vs += [(x, yw, zt), (x, yw + out, zt - drop), (x, yw + out, zt - drop - 0.28)]
        for i in range(n):
            a, b = 3 * i, 3 * (i + 1)
            fs += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2)]; fm += [i % 2, i % 2]
        ob = add_mesh("awning", vs, fs, [canvas, AM[col]], fm)
        ob.modifiers.new("thick", "SOLIDIFY").thickness = 0.03
    na = 0
    doors_front.sort(key=lambda d: d[0].x)
    placed = []
    for lo, hi, col in doors_front:
        if any(abs(lo.x - p.x) < 0.3 and abs(hi.x - q.x) < 0.3 for p, q in placed): continue   # one awning per opening
        awning(lo, hi, col); placed.append((lo, hi)); na += 1
    # flags along the ridge of the long roofs (owner's sketch): one every three bays
    nr = 0
    spans = []                                      # the roofed modules joined into continuous stretches
    for m in sorted(MODS, key=lambda m: -m["xEast"]):
        if not m.get("roof"): continue
        if spans and abs(spans[-1][1] - m["xEast"]) < 0.01: spans[-1][1] = m["xWest"]
        else: spans.append([m["xEast"], m["xWest"]])
    for xe, xw in spans:
        pts = [p for p in roofs if xw - 0.5 < p.x < xe + 0.5 and p.z < 26.0]     # the ridge is level along the run
        if not pts: continue
        r = max(pts, key=lambda p: p.z)
        x = xe - 3.5
        while x > xw + 1.0:
            flag(Vector((x, r.y, r.z)), 3.2, TFLAG[nr % len(TFLAG)], w=2.0, fh=1.25, phase=nr * 1.1); nr += 1
            x -= 10.5
    print("accents: %d pavilion flags, %d roof flags, %d awnings" % (k, nr, na), flush=True)

    # ---------------- the crowd: the stand's terraces, galleries and boxes, and the lawn, packed as in the photos
    figs = [o for o in import_glb(CROWD_GLB if os.path.isabs(CROWD_GLB) else rp(CROWD_GLB)) if o.type == "MESH"]
    crowd_coll = bpy.data.collections.new("crowd_figs")
    for o in figs:
        for c in o.users_collection: c.objects.unlink(o)
        crowd_coll.objects.link(o); o.parent = None; o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    pal_clothes = ["#2c3140", "#3a3d44", "#4b4d52", "#2f3a33", "#59544c", "#c9a0a8", "#9fb6c8", "#ddd2b8", "#a8706a", "#88a383", "#d2b874", "#e8e2d6", "#9a88b4", "#cf9476"]
    pal_hats = ["#222226", "#222226", "#2a2a2e", "#efe6d2", "#d8c08a", "#c9a0a8", "#9fb6c8"]
    def palette_mat(name, cols, rough=0.9):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.1
        oi = nt.nodes.new("ShaderNodeObjectInfo"); cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
        els = cr.color_ramp.elements
        while len(els) < len(cols): els.new(0.5)
        for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
        nt.links.new(oi.outputs["Random"], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs["Base Color"])
        return m
    CM = {"crowd_clothes": palette_mat("c_clothes", pal_clothes), "crowd_hat": palette_mat("c_hat", pal_hats),
          "crowd_skin": palette_mat("c_skin", ["#efc6a4", "#e2b48e", "#c99572", "#9a6a4a"]),
          "crowd_accent": palette_mat("c_accent", ["#e6998b", "#8db58c", "#eccd7c", "#8eb0d6", "#b49fd2", "#f2ece0", "#c0453a"]),
          "crowd_dark": palette_mat("c_dark", ["#24262b", "#2f3036", "#3b352f"])}
    for k, v in {"fig_main": "crowd_clothes", "fig_skin": "crowd_skin", "fig_hat": "crowd_hat", "fig_trim": "crowd_accent", "fig_hair": "crowd_dark"}.items():
        CM[k] = CM[v]
    for o in crowd_coll.objects:
        for i, sl in enumerate(o.material_slots):
            base = (sl.material.name if sl.material else "").split(".")[0]
            if base in CM: o.material_slots[i].material = CM[base]
    # more black top hats (owner, 6 Nov 2026): every top hat near-black (the odd grey one), and the top-hat gents
    # picked twice as often, so about two people in five wear one
    tops = [o for o in list(crowd_coll.objects) if "_top" in o.name]
    if tops:
        top_mat = palette_mat("c_tophat", ["#1a1a1e", "#1f1f23", "#222226", "#1c1c20", "#26262a", "#1d1d21", "#55555c"], rough=0.8)
        # ...in black tops and tails (owner): their coats near-black morning coats, the odd grey morning suit
        tails_mat = palette_mat("c_tails", ["#1c1d22", "#202128", "#24262c", "#1e1f24", "#2a2c33", "#22232a", "#5c5e64", "#1b1c21"], rough=0.85)
        for o in tops:
            for i, sl in enumerate(o.material_slots):
                if sl.material is CM.get("fig_hat") or sl.material is CM.get("crowd_hat"):
                    o.material_slots[i].link = "OBJECT"; o.material_slots[i].material = top_mat
                elif sl.material is CM.get("fig_main") or sl.material is CM.get("crowd_clothes"):
                    o.material_slots[i].link = "OBJECT"; o.material_slots[i].material = tails_mat
        for k in range(int(os.environ.get("TOP_EXTRA", "3"))):
            for o in tops:
                d = o.copy(); crowd_coll.objects.link(d)
        print("crowd: %d figures, %d with top hats" % (len(crowd_coll.objects), sum("_top" in o.name for o in crowd_coll.objects)), flush=True)
    import random
    rnd = random.Random(21)
    pts = []
    A = json.load(open(rp("assets/models/architecture/ascot_main_stand_crowd_areas.json")))["areas"]
    for a in A:
        if a["kind"] in ("lawn_front_line", "steps"): continue
        rows = 1 if a["z1"] - a["z0"] < 1.4 else 2
        for r in range(rows):
            lz = a["z0"] + 0.15 + r * 0.75
            x = a["x0"]
            while x < a["x1"]:
                if rnd.random() < (0.85 if a["kind"] == "terrace" else 0.7 if r == 0 else 0.4):
                    pts.append((x + (rnd.random() - 0.5) * 0.2, -(FRONT + lz), a["floor"]))
                x += 0.62
    near = W + COURSE["rails"]["gap"]
    z = near + 1.6
    while z < FRONT - 1.5:
        d = z - near; dens = 0.8 if d < 4 else 0.35 if d < 8 else 0.08
        x = -108.0
        while x < 405:
            if rnd.random() < dens: pts.append((x + (rnd.random() - 0.5) * 0.4, -(z + (rnd.random() - 0.5) * 0.4), 0.0))
            x += 0.62
        z += 0.7
    me = bpy.data.meshes.new("crowd_pts"); me.from_pydata(pts, [], [])
    cp = bpy.data.objects.new("crowd", me); scene.collection.objects.link(cp)
    gn = cp.modifiers.new("crowd", "NODES")
    ng = bpy.data.node_groups.new("crowd_inst", "GeometryNodeTree"); gn.node_group = ng
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = crowd_coll
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    ip = N.new("GeometryNodeInstanceOnPoints"); ip.inputs["Pick Instance"].default_value = True
    ri = N.new("FunctionNodeRandomValue"); ri.data_type = "INT"; ri.inputs["Min"].default_value = 0; ri.inputs["Max"].default_value = len(crowd_coll.objects) - 1
    rr = N.new("FunctionNodeRandomValue"); rr.data_type = "FLOAT_VECTOR"
    rr.inputs["Min"].default_value = (0, 0, -0.5); rr.inputs["Max"].default_value = (0, 0, 0.5)
    rs = N.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"; rs.inputs["Min"].default_value = 0.94; rs.inputs["Max"].default_value = 1.06
    L.new(gi.outputs[0], ip.inputs["Points"]); L.new(ci.outputs[0], ip.inputs["Instance"])
    L.new(ri.outputs[0], ip.inputs["Instance Index"]); L.new(rr.outputs[0], ip.inputs["Rotation"]); L.new(rs.outputs[0], ip.inputs["Scale"])
    L.new(ip.outputs[0], go.inputs[0])
    print("crowd:", len(pts), "people", flush=True)

# ground, track, rails
def turf_mat(name, base, stripe=0.0, stripe_w=10.0, lane_k=0.0, flecks=True, light=False):
    """Racecourse turf (owner, 6 Nov 2026, from his toy-town reference): a fine blade texture, slight colour
    variation over metres, broad soft mowing stripes across the track, and the odd divot and daisy.
    light: the lawns off the track, lighter, even, a finer texture and no stripes."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, Lk = nt.nodes, nt.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.97; b.inputs["Specular IOR Level"].default_value = 0.15
    tc = N.new("ShaderNodeTexCoord")
    def noise(scale, detail=4, rough=0.6, vec=None):
        n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = detail
        n.inputs["Roughness"].default_value = rough; Lk.new(vec or tc.outputs["Object"], n.inputs["Vector"]); return n
    def mix(a, bb, fac, blend="MIX"):
        x = N.new("ShaderNodeMix"); x.data_type = "RGBA"; x.blend_type = blend
        if isinstance(fac, float): x.inputs["Factor"].default_value = fac
        else: Lk.new(fac, x.inputs["Factor"])
        for slot, v in ((6, a), (7, bb)):
            if isinstance(v, tuple): x.inputs[slot].default_value = v
            else: Lk.new(v, x.inputs[slot])
        return x.outputs[2]
    def ramp(inp, stops):
        r = N.new("ShaderNodeValToRGB"); Lk.new(inp, r.inputs[0])
        els = r.color_ramp.elements
        while len(els) < len(stops): els.new(0.5)
        for e, (p, c) in zip(els, stops): e.position = p; e.color = c
        return r.outputs[0]
    sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Object"], sep.inputs[0])
    c0 = lin(base)
    def mul(colin, factor_socket):
        x = N.new("ShaderNodeMix"); x.data_type = "RGBA"; x.blend_type = "MULTIPLY"; x.inputs["Factor"].default_value = 1.0
        if isinstance(colin, tuple): x.inputs[6].default_value = colin
        else: Lk.new(colin, x.inputs[6])
        Lk.new(factor_socket, x.inputs[7]); return x.outputs[2]
    g = lambda v: (v, v, v, 1)
    # each layer darkens or lightens the one below (multiplies), so none washes out the others
    col = mul(c0, ramp(noise(0.08 if not light else 0.12, 3).outputs["Fac"], [(0.3, g(0.86)), (0.7, g(1.1))]))     # patches over metres
    tufts = noise(2.2 if not light else 3.0, 6, 0.7)
    col = mul(col, ramp(tufts.outputs["Fac"], [(0.35, g(0.8)), (0.65, g(1.13))] if not light else [(0.35, g(0.88)), (0.65, g(1.08))]))
    blades = noise(18.0 if not light else 26.0, 8, 0.75)
    col = mul(col, ramp(blades.outputs["Fac"], [(0.3, g(0.78)), (0.7, g(1.15))] if not light else [(0.3, g(0.88)), (0.7, g(1.08))]))
    if stripe:
        # mown lanes along the track (owner: the stripes make lanes): soft-edged bands stripe_w metres wide across y
        sx = N.new("ShaderNodeMath"); sx.operation = "MULTIPLY"; Lk.new(sep.outputs["Y"], sx.inputs[0]); sx.inputs[1].default_value = math.pi / stripe_w
        sn = N.new("ShaderNodeMath"); sn.operation = "SINE"; Lk.new(sx.outputs[0], sn.inputs[0])
        st = N.new("ShaderNodeMapRange"); Lk.new(sn.outputs[0], st.inputs["Value"]); st.inputs["From Min"].default_value = -0.3; st.inputs["From Max"].default_value = 0.3
        col = mul(col, ramp(st.outputs["Result"], [(0.0, (1 - stripe, 1 - stripe * 0.8, 1 - stripe * 1.2, 1)), (1.0, (1 + stripe * 0.8, 1 + stripe * 0.8, 1 + stripe * 0.3, 1))]))
    if flecks:
        # the odd divot (brown) on the track, the odd daisy (white) on the lawns
        vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 1.6 if not light else 2.4; Lk.new(tc.outputs["Object"], vor.inputs["Vector"])
        dots = ramp(vor.outputs["Distance"], [(0.0, (1, 1, 1, 1)), (0.035 if not light else 0.03, (0, 0, 0, 1))])
        keep = N.new("ShaderNodeMath"); keep.operation = "GREATER_THAN"; Lk.new(vor.outputs["Color"], keep.inputs[0]); keep.inputs[1].default_value = 0.72
        fl = N.new("ShaderNodeMath"); fl.operation = "MULTIPLY"; Lk.new(dots, fl.inputs[0]); Lk.new(keep.outputs[0], fl.inputs[1])
        col = mix(col, lin("#efe9d2") if light else lin("#6d5236"), fl.outputs[0])
    Lk.new(col, b.inputs["Base Color"])
    hsum = N.new("ShaderNodeMath"); hsum.operation = "ADD"; Lk.new(blades.outputs["Fac"], hsum.inputs[0]); Lk.new(tufts.outputs["Fac"], hsum.inputs[1])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.6 if not light else 0.4; bp.inputs["Distance"].default_value = 0.04
    Lk.new(hsum.outputs[0], bp.inputs["Height"]); Lk.new(bp.outputs["Normal"], b.inputs["Normal"])
    return no_green_bounce(m, "#a29680" if not light else "#a89c86")

if SOFT:
    turf = turf_mat("turf_track", "#7fa952", stripe=0.16, stripe_w=3.75)       # the racing surface: richer, eight mown lanes
    grass = turf_mat("turf_lawn", "#bcc98c", light=True)                        # the lawns off the track: lighter, even
plane("ground", -900, 1400, -700, 500, grass, -0.02)
plane("track", -300, 1300, -W, 0, turf, 0.0)


def ascot_rail(y, track_side, x0=-300.0, x1=1300.0):
    """The Ascot running rail (owner's photo): a broad white top rail, a deep flat board facing the track with a
    rounded capping on top, on square white posts every 2.4 m set back behind the board; nothing below."""
    h, board, depth = 1.12, 0.26, 0.09
    t = track_side                                                            # +1: the track is towards +y
    ys = y + t * 0.02                                                         # the board's track face
    prof = [(ys, h - board), (ys, h), (ys - t * 0.04, h + 0.05), (ys - t * 0.12, h + 0.06), (ys - t * 0.2, h + 0.03),
            (ys - t * 0.2, h - 0.02), (ys - t * depth, h - 0.02), (ys - t * depth, h - board)]
    if t < 0: prof = prof[::-1]
    me = bpy.data.meshes.new("rail_top"); verts, faces = [], []
    n = len(prof)
    for xx in (x0, x1):
        verts += [(xx, py, pz) for py, pz in prof]
    faces.append(list(range(n))[::-1]); faces.append(list(range(n, 2 * n)))
    for i in range(n):
        faces.append((i, (i + 1) % n, n + (i + 1) % n, n + i))
    me.from_pydata(verts, [], faces); me.materials.append(rail)
    for p in me.polygons: p.use_smooth = False
    ob = bpy.data.objects.new("rail_top", me); scene.collection.objects.link(ob)
    bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.015; bv.segments = 2; bv.limit_method = "ANGLE"
    # posts: one square post, arrayed along the rail
    pm = bpy.data.meshes.new("rail_post"); bmp = bmesh.new()
    bmesh.ops.create_cube(bmp, size=1.0, matrix=Matrix.Translation((0, ys - t * 0.16, (h - 0.02) / 2)) @ Matrix.Diagonal((0.1, 0.1, h - 0.02, 1)))
    bmp.to_mesh(pm); bmp.free(); pm.materials.append(rail)
    po = bpy.data.objects.new("rail_posts", pm); scene.collection.objects.link(po); po.location.x = x0
    ar = po.modifiers.new("array", "ARRAY"); ar.count = int((x1 - x0) / 2.4); ar.use_relative_offset = False
    ar.use_constant_offset = True; ar.constant_offset_displace = (2.4, 0, 0)
    pb = po.modifiers.new("bevel", "BEVEL"); pb.width = 0.012; pb.segments = 2


import bmesh


def grass_blades(name, x0, x1, y0, y1, density, height, base_hex, lanes=False, seed=1):
    """Real blades of grass standing up from the turf where the cameras look (owner: the turf should feel 3D,
    the horses running in it, not over a flat floor): a small curved blade scattered by geometry nodes, tilted and
    sized at random, coloured to match the turf beneath (and its lanes)."""
    bm = bmesh.new()
    w, h = 0.014, height
    vs = [bm.verts.new(v) for v in ((-w, 0, 0), (w, 0, 0), (w * 0.6, 0.012, h * 0.55), (-w * 0.6, 0.012, h * 0.55), (0.0, 0.03, h))]
    bm.faces.new((vs[0], vs[1], vs[2], vs[3])); bm.faces.new((vs[3], vs[2], vs[4]))
    bme = bpy.data.meshes.new(name + "_blade"); bm.to_mesh(bme); bm.free()
    m = bpy.data.materials.new(name + "_mat"); m.use_nodes = True; nt = m.node_tree; Nn, Lk = nt.nodes, nt.links
    b = Nn["Principled BSDF"]; b.inputs["Roughness"].default_value = 0.9; b.inputs["Specular IOR Level"].default_value = 0.2
    b.inputs["Subsurface Weight"].default_value = 0.15; b.inputs["Subsurface Radius"].default_value = (0.02, 0.05, 0.01)
    geo = Nn.new("ShaderNodeNewGeometry"); sep = Nn.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs["Position"], sep.inputs[0])
    oi = Nn.new("ShaderNodeObjectInfo")
    rr = Nn.new("ShaderNodeMapRange"); Lk.new(oi.outputs["Random"], rr.inputs["Value"]); rr.inputs["To Min"].default_value = 0.72; rr.inputs["To Max"].default_value = 1.18
    fac = rr.outputs["Result"]
    if lanes:
        sx = Nn.new("ShaderNodeMath"); sx.operation = "MULTIPLY"; Lk.new(sep.outputs["Y"], sx.inputs[0]); sx.inputs[1].default_value = math.pi / 3.75
        sn = Nn.new("ShaderNodeMath"); sn.operation = "SINE"; Lk.new(sx.outputs[0], sn.inputs[0])
        sm = Nn.new("ShaderNodeMapRange"); Lk.new(sn.outputs[0], sm.inputs["Value"]); sm.inputs["From Min"].default_value = -0.3; sm.inputs["From Max"].default_value = 0.3
        sm.inputs["To Min"].default_value = 0.86; sm.inputs["To Max"].default_value = 1.13
        mm = Nn.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; Lk.new(fac, mm.inputs[0]); Lk.new(sm.outputs["Result"], mm.inputs[1]); fac = mm.outputs[0]
    # lighter towards the tip, darker at the root
    tip = Nn.new("ShaderNodeMapRange"); Lk.new(sep.outputs["Z"], tip.inputs["Value"]); tip.inputs["From Max"].default_value = height
    tip.inputs["To Min"].default_value = 0.7; tip.inputs["To Max"].default_value = 1.12
    mm2 = Nn.new("ShaderNodeMath"); mm2.operation = "MULTIPLY"; Lk.new(fac, mm2.inputs[0]); Lk.new(tip.outputs["Result"], mm2.inputs[1])
    mix = Nn.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
    mix.inputs[6].default_value = lin(base_hex)
    comb = Nn.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"): Lk.new(mm2.outputs[0], comb.inputs[k])
    Lk.new(comb.outputs["Color"], mix.inputs[7]); Lk.new(mix.outputs[2], b.inputs["Base Color"])
    bme.materials.append(m)
    blade = bpy.data.objects.new(name + "_blade", bme)
    pm = bpy.data.meshes.new(name); pm.from_pydata([(x0, y0, 0.0), (x1, y0, 0.0), (x1, y1, 0.0), (x0, y1, 0.0)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new(name, pm); scene.collection.objects.link(ob)
    gn = ob.modifiers.new("grass", "NODES"); ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree"); gn.node_group = ng
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    G, GL = ng.nodes, ng.links
    gi = G.new("NodeGroupInput"); go = G.new("NodeGroupOutput")
    dist = G.new("GeometryNodeDistributePointsOnFaces"); dist.inputs["Density"].default_value = density; dist.inputs["Seed"].default_value = seed
    oinfo = G.new("GeometryNodeObjectInfo"); oinfo.inputs["Object"].default_value = blade
    inst = G.new("GeometryNodeInstanceOnPoints")
    rr = G.new("FunctionNodeRandomValue"); rr.data_type = "FLOAT_VECTOR"; rr.inputs["Min"].default_value = (-0.45, -0.45, 0.0); rr.inputs["Max"].default_value = (0.45, 0.45, 6.283)
    rs = G.new("FunctionNodeRandomValue"); rs.data_type = "FLOAT"; rs.inputs["Min"].default_value = 0.55; rs.inputs["Max"].default_value = 1.45
    GL.new(gi.outputs[0], dist.inputs["Mesh"]); GL.new(dist.outputs["Points"], inst.inputs["Points"])
    GL.new(oinfo.outputs["Geometry"], inst.inputs["Instance"]); GL.new(rr.outputs[0], inst.inputs["Rotation"]); GL.new(rs.outputs[0], inst.inputs["Scale"])
    GL.new(inst.outputs[0], go.inputs[0])
    print("grass:", name, int((x1 - x0) * (y1 - y0) * density), "blades", flush=True)


GRASS = float(os.environ.get("GRASS", "1"))
if SOFT and GRASS:
    gx0, gx1 = float(os.environ.get("GRASS_X0", "-40")), float(os.environ.get("GRASS_X1", "140"))
    grass_blades("turf_blades", gx0, gx1, -W + 0.1, -0.1, 320 * GRASS, 0.085, "#7fa952", lanes=True, seed=3)
    grass_blades("lawn_blades", gx0, gx1, -FRONT + 0.5, -W - 0.5, 160 * GRASS, 0.05, "#bcc98c", seed=5)


def horses():
    """A few galloping horses on the track for judging the turf (owner): the v2 racehorse, its gallop at different
    moments, coats from its own colour zones, plain silks, all matte."""
    import random
    rnd = random.Random(4)
    COATS = [("#7a4a2a", "#1d1714"), ("#4a2e1c", "#17110d"), ("#a3552c", "#6a3317"), ("#2b2523", "#141110"), ("#a8a6a0", "#6d6b66")]
    SILKS = ["#2f5a9a", "#e8c54a", "#c0392b", "#6a3fa0", "#2e7d4f", "#e8e2d4", "#d9822b"]
    spots = [(48, -9.5), (51.5, -12.5), (46, -15.0), (55, -17.0), (49.5, -20.5), (58, -11.0), (62.5, -16.0)]
    for i, (x, y) in enumerate(spots):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=rp("assets/models/racehorse_v2.glb"))
        new = [o for o in bpy.data.objects if o not in before]
        arm = next(o for o in new if o.type == "ARMATURE")
        root = next(o for o in new if o.parent is None)
        root.location = (x, y, 0); root.rotation_euler = (0, 0, math.pi); root.scale = (3, 3, 3)
        coat, points = COATS[i % len(COATS)]
        for o in new:
            if o.type != "MESH": continue
            if not o.data.name.startswith("racehorse_v2") or o.data.name.endswith(("_close", "_far")) and o.data.name != "racehorse_v2":
                pass
            if "close" in o.name or "far" in o.name:
                o.hide_render = True; continue
            for k, sl in enumerate(o.material_slots):
                nm = sl.material.name if sl.material else ""
                m = bpy.data.materials.new("h%d_%s" % (i, nm)); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
                b.inputs["Roughness"].default_value = 0.75; b.inputs["Specular IOR Level"].default_value = 0.25
                if "silks" in nm:
                    b.inputs["Base Color"].default_value = lin(SILKS[(i * 3) % len(SILKS)])
                else:
                    # colour zones carried in the vertex colours: R coat, G points, B skin; the rest tack
                    ca = nt.nodes.new("ShaderNodeVertexColor"); sp = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(ca.outputs["Color"], sp.inputs[0])
                    def z(ch, hexc, prev):
                        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; nt.links.new(sp.outputs[ch], mx.inputs["Factor"])
                        if isinstance(prev, tuple): mx.inputs[6].default_value = prev
                        else: nt.links.new(prev, mx.inputs[6])
                        mx.inputs[7].default_value = lin(hexc); return mx.outputs[2]
                    c = z("Red", coat, lin("#3a3633")); c = z("Green", points, c); c = z("Blue", "#d9b08c", c)
                    nt.links.new(c, b.inputs["Base Color"])
                o.material_slots[k].link = "OBJECT"; o.material_slots[k].material = m
        act = bpy.data.actions.get("gallop_v2")
        if act and arm:
            arm.animation_data_create()
            tr = arm.animation_data.nla_tracks.new(); st = tr.strips.new("g", 1, act)
            st.frame_start = 1 - (i * 7) % 40; st.repeat = 4
            arm.animation_data.action = None
    scene.frame_set(1)
    print("horses:", len(spots), flush=True)


if os.environ.get("HORSES"):
    horses()


ascot_rail(0.0, -1)       # the far (inside) rail: the track is to its south (Blender -y)
ascot_rail(-W, +1)        # the near (outer) rail by the lawn and the stand: the track is to its north

scene.render.engine = "CYCLES"
scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.max_bounces = 6
scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast" if SOFT else "AgX - Medium High Contrast"
except Exception: pass
scene.render.resolution_x, scene.render.resolution_y = RES
scene.render.film_transparent = False
scene.view_settings.exposure = -0.25 if not SOFT else 0.12


def course(p):                                       # course axes (x east, z south, y up) -> Blender
    return Vector((p[0], -p[2], p[1]))


def camera(name, eye, at, fov, focus=None, fstop=None):
    cam = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    if cam.name not in scene.collection.objects: scene.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"; cam.data.angle_y = math.radians(fov); cam.data.clip_end = 6000
    e, a = course(eye), course(at)
    cam.location = e; cam.rotation_euler = (a - e).to_track_quat("-Z", "Y").to_euler()
    # a shallow model-like focus on the subject (the street's miniature look), kept gentle
    cam.data.dof.use_dof = fstop is not None and VARIANT in ("clean", "soft", "accent")
    if cam.data.dof.use_dof:
        cam.data.dof.focus_distance = (course(focus or at) - e).length; cam.data.dof.aperture_fstop = fstop
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, f"{OUT_TAG or VARIANT}_{name}.png")
    bpy.ops.render.render(write_still=True); print("rendered", scene.render.filepath, flush=True)


# the race view's own camera places (stand-styles comparison): course axes
SHOTS = {
    "tower": ((-12, 7, 22), (2, 15, 50), 55, (0, 12, 46), 2.0),
    "across": ((40, 14, -30), (-20, 10, 50), 42, (0, 10, 46), 4.0),
    "lawn": ((60, 3, 26), (0, 12, 48), 50, (40, 8, 46), 2.8),
    "wing": ((230, 30, -45), (120, 9, 52), 40, (150, 9, 46), 5.6),
    # across the track from the inside, low, at the rail and the lawn crowd (owner's turf reference)
    "track": ((70, 3.2, -4), (40, 1.2, 34), 38, (48, 1.0, 28), 4.0),
    # low and close with the horses in the grass
    "horses": ((72, 1.1, 7), (50, 1.4, 14), 34, (53, 1.0, 13), 2.8),
    # checking aid: the turf close up, and the track and lawn from above
    "turfclose": ((50, 4, 12), (46, 0, 18), 45, (46, 0, 18), None),
    "turfhigh": ((80, 60, 10), (40, 0, 30), 40, (40, 0, 30), None),
    # close along the near rail
    "rail": ((95, 1.7, 27.3), (55, 1.0, 31), 40, (85, 1.1, 30), 2.2),
}
for name, (eye, at, fov, focus, fstop) in SHOTS.items():
    if CAMS and f"cam={name}" not in CAMS: continue
    camera(name, eye, at, fov, focus, fstop)
