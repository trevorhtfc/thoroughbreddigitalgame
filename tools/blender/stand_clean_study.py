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
VARIANT = next((a for a in ARGS if a in ("clean", "today", "soft")), "clean")
SOFT = VARIANT == "soft"
CAMS = [a for a in ARGS if a.startswith("cam=")]
OUT = rp("reference/architecture/clean-study"); os.makedirs(OUT, exist_ok=True)
COURSE = json.load(open(rp("courses/ascot.json")))
FRONT = COURSE["grandstand"]["frontLine"]
W = COURSE["trackWidth"]
RES = (1600, 900) if not os.environ.get("QUICK") else (800, 450)

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

if VARIANT in ("clean", "soft"):
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
    cam.data.dof.use_dof = fstop is not None and VARIANT in ("clean", "soft")
    if cam.data.dof.use_dof:
        cam.data.dof.focus_distance = (course(focus or at) - e).length; cam.data.dof.aperture_fstop = fstop
    scene.camera = cam
    scene.render.filepath = os.path.join(OUT, f"{VARIANT}_{name}.png")
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
