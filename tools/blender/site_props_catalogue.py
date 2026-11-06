"""Render the site components laid out like the crib sheet, on grey, to compare with
reference/architecture/site-components-sheet.png.

    python -c "exec(open('tools/blender/site_props_catalogue.py').read())" <out.png> [samples]
    QUICK=1 python -c ...     # fast Workbench preview
"""
import os, sys, math
import bpy
from mathutils import Vector

ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
OUT = ARGS[0] if ARGS else "site_props_catalogue.png"
SAMPLES = int(ARGS[1]) if len(ARGS) > 1 else 48
bpy.ops.wm.open_mainfile(filepath="assets/models/master/site_props.blend")
sc = bpy.context.scene
ROWS = [["marquee_peaks", "marquee_clearspan", "big_top", "pagoda_counter"],
        ["stand_open", "stand_covered", "terrace_deck", "viewing_tower"],
        ["kiosk_awning", "booth_hut", "kiosk_row_arched", "pagoda_kiosk", "pergola_picnic", "picnic_table"],
        ["planter_long", "planter_short", "fence_picket", "fence_cross", "barrier_rail", "signboard", "flagpole", "banner_flag", "signpost"]]
GAP = [5.0, 5.0, 3.0, 1.6]
SCALE = [1.0, 1.0, 1.5, 1.9]          # display only: small pieces enlarged, as on the sheet
y = 0.0
for r, row in enumerate(ROWS):
    objs = [bpy.data.objects[n] for n in row]
    for o in objs:
        o.scale = (SCALE[r],) * 3
    bpy.context.view_layer.update()
    widths = [o.dimensions.x for o in objs]
    total = sum(widths) + GAP[r] * (len(objs) - 1)
    x = -total / 2
    depth = max(o.dimensions.y for o in objs)
    for o, w in zip(objs, widths):
        o.location = (x + w / 2, y, 0)
        o.rotation_euler = (0, 0, 0)
        x += w + GAP[r]
    y -= depth / 2 + [12, 14, 20, 0][r]
    if r < 3:
        y -= max(bpy.data.objects[n].dimensions.y * SCALE[r + 1] for n in ROWS[r + 1]) / 2
# Rows further back are bigger: shrink the gap illusion with a high orthographic camera.
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 90
cam.location = (0, -160, 60)
look = Vector((0, -20, 0))
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1774, 887
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.2, 0.21, 1)
floor.data.materials.append(fm)
if os.environ.get("QUICK"):
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = True
    sc.display.shading.show_cavity = True
else:
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.22, 0.22, 0.23, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.2
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 3.2; sun.data.angle = math.radians(12)
    sun.rotation_euler = (math.radians(42), 0, math.radians(-30))
    sc.view_settings.view_transform = "AgX"
sc.render.filepath = os.path.abspath(OUT)
bpy.ops.render.render(write_still=True)
print("rendered", OUT, flush=True)
