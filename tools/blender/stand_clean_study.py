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
from mathutils import Vector

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
plane("ground", -900, 1400, -700, 500, grass, -0.02)
plane("track", -300, 1300, -W, 0, turf, 0.0)
for y in (0.0, -W):
    plane("rail_%d" % int(-y), -300, 1300, y - 0.12, y + 0.12, rail, 1.0)

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
}
for name, (eye, at, fov, focus, fstop) in SHOTS.items():
    if CAMS and f"cam={name}" not in CAMS: continue
    camera(name, eye, at, fov, focus, fstop)
