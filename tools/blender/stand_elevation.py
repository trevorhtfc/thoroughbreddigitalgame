"""Front elevation of Ascot's main stand, for marking up by hand (owner, 6 Nov 2026).

    python -c "exec(open('tools/blender/stand_elevation.py').read())"

Renders assets/models/architecture/ascot_main_stand.glb straight on (orthographic, from the track) as a clean
drawing: flat soft shading, outlines, the study's colours, no crowd. Writes raw renders to
reference/architecture/elevation/_raw_*.png; tools/course/annotate_elevation.py adds the grid and labels.
Sheets (course x, east on the left as seen from the track): overview (whole stand), east, centre, west.
"""
import os, json, math
import bpy
from mathutils import Vector

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
OUT = rp("reference/architecture/elevation"); os.makedirs(OUT, exist_ok=True)
COURSE = json.load(open(rp("courses/ascot.json")))
FRONT = COURSE["grandstand"]["frontLine"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=rp("assets/models/architecture/ascot_main_stand.glb"))
parts = [o for o in bpy.data.objects if o not in before]
root = bpy.data.objects.new("stand", None); scene.collection.objects.link(root)
for o in parts:
    if o.parent is None: o.parent = root
root.location = (0, -FRONT, 0)
COL = {"gs_wall": "#ecdcc0", "gs_podium": "#dccaa8", "gs_trim": "#f6eee0", "gs_roof": "#8a8d95", "gs_iron": "#2f4236",
       "gs_glass": "#3a3846", "gs_door": "#3a5545", "gs_gilt": "#c8a466", "gs_steps": "#dccfb3",
       "gs_clock_face": "#fbf5ea", "gs_clock_dark": "#25262a"}
for m in bpy.data.materials:
    base = m.name.split(".")[0]
    if base in COL: m.diffuse_color = lin(COL[base])

# a strip of lawn under it, so the stand stands on something
me = bpy.data.meshes.new("lawn"); me.from_pydata([(-200, -10, -0.02), (500, -10, -0.02), (500, -80, -0.02), (-200, -80, -0.02)], [], [(0, 1, 2, 3)])
lm = bpy.data.materials.new("lawn"); lm.diffuse_color = lin("#b9c99a"); me.materials.append(lm)
scene.collection.objects.link(bpy.data.objects.new("lawn", me))

scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light = "FLAT"; sh.color_type = "MATERIAL"
sh.show_cavity = True; sh.cavity_type = "BOTH"; sh.cavity_ridge_factor = 0.6; sh.cavity_valley_factor = 1.0
sh.show_object_outline = True; sh.object_outline_color = (0.16, 0.15, 0.14)
sh.show_shadows = True; sh.shadow_intensity = 0.22
scene.display.light_direction = (-0.45, 0.55, 0.7)
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.display.render_aa = "16"

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.clip_end = 1000; cam.data.sensor_fit = "HORIZONTAL"
cam.rotation_euler = Vector((0, -1, 0)).to_track_quat("-Z", "Y").to_euler()     # looking at the front, from the track
scene.camera = cam

PXM = {"overview": 12, "east": 32, "centre": 32, "west": 32}
SHEETS = {"overview": (412, -110), "east": (412, 232), "centre": (246, 66), "west": (80, -110)}
ZLO, ZHI = -4.0, 46.0                               # metres of height shown
meta = {}
for name, (xe, xw) in SHEETS.items():
    S = xe - xw
    W = int(round(S * PXM[name])); H = int(round((ZHI - ZLO) * PXM[name]))
    scene.render.resolution_x, scene.render.resolution_y = W, H
    cam.data.ortho_scale = S
    cx, cz = (xe + xw) / 2, (ZHI + ZLO) / 2
    cam.location = (cx, 120.0, cz)
    scene.render.filepath = os.path.join(OUT, f"_raw_{name}.png")
    bpy.ops.render.render(write_still=True)
    meta[name] = {"xEast": xe, "xWest": xw, "zLo": ZLO, "zHi": ZHI, "pxPerMetre": PXM[name], "w": W, "h": H}
    print("rendered", name, W, H, flush=True)
json.dump(meta, open(os.path.join(OUT, "_raw_meta.json"), "w"), indent=1)
