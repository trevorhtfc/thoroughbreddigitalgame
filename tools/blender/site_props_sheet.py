"""The site components as a lettered reference sheet, and their codes and footprints as data.

    python -c "exec(open('tools/blender/site_props_sheet.py').read())" [samples]

Renders every piece in assets/models/master/site_props.blend laid out as on the crib sheet (small pieces
enlarged for display), then letters each one A, B, C... with its name and true size.

Writes reference/architecture/site-components-codes.png      the lettered sheet, to plan layouts with
       assets/models/architecture/site_props_codes.json     code -> piece, true size, and footprint
                                                            (glTF axes: x across, z front-back, front
                                                            facing +z) for drawing plans
Run tools/course/draw_site_plan.py afterwards for the lettered map.
"""
import json, os, sys, math
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(".")
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SAMPLES = int(ARGS[0]) if ARGS else 24
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "assets/models/master/site_props.blend"))
sc = bpy.context.scene
ROWS = [["marquee_peaks", "marquee_clearspan", "big_top", "pagoda_counter"],
        ["stand_open", "stand_covered", "terrace_deck", "viewing_tower"],
        ["kiosk_awning", "booth_hut", "kiosk_row_arched", "pagoda_kiosk", "pergola_picnic", "picnic_table"],
        ["planter_long", "planter_short", "fence_picket", "fence_cross", "barrier_rail", "signboard", "flagpole", "banner_flag", "signpost"]]
NAMES = {"marquee_peaks": "Three-peak marquee", "marquee_clearspan": "Glazed clearspan marquee", "big_top": "Big top",
         "pagoda_counter": "Pagoda counter", "stand_open": "Open seating stand", "stand_covered": "Covered seating stand",
         "terrace_deck": "Terrace deck, parasols", "viewing_tower": "Viewing tower", "kiosk_awning": "Kiosk with awning",
         "booth_hut": "Booth hut", "kiosk_row_arched": "Arched kiosk row", "pagoda_kiosk": "Pagoda kiosk",
         "pergola_picnic": "Pergola, picnic tables", "picnic_table": "Picnic table", "planter_long": "Long planter",
         "planter_short": "Short planter", "fence_picket": "Picket fence (2.5 m)", "fence_cross": "Cross-rail fence (2.5 m)",
         "barrier_rail": "Barrier rail", "signboard": "Signboard", "flagpole": "Flagpole", "banner_flag": "Banner flag",
         "signpost": "Signpost"}
GAP = [5.0, 5.0, 3.0, 1.6]
SCALE = [1.0, 1.0, 1.5, 1.9]          # display only: small pieces enlarged, as on the sheet

# true sizes and footprints first, at scale 1, before laying out
codes = {}
order = [n for row in ROWS for n in row]
for i, n in enumerate(order):
    o = bpy.data.objects[n]
    o.scale = (1, 1, 1); o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0)
bpy.context.view_layer.update()
for i, n in enumerate(order):
    o = bpy.data.objects[n]
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    xs, ys, zs = [p.x for p in bb], [p.y for p in bb], [p.z for p in bb]
    code = chr(ord("A") + i)
    # glTF axes: x = Blender x; z = -Blender y (the front faces +z)
    codes[code] = {"piece": n, "name": NAMES[n], "width": round(max(xs) - min(xs), 1), "depth": round(max(ys) - min(ys), 1),
                   "height": round(max(zs) - min(zs), 1),
                   "footprint": {"x0": round(min(xs), 2), "x1": round(max(xs), 2), "z0": round(-max(ys), 2), "z1": round(-min(ys), 2)}}

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
        x += w + GAP[r]
    y -= depth / 2 + [12, 14, 20, 0][r]
    if r < 3:
        y -= max(bpy.data.objects[n].dimensions.y * SCALE[r + 1] for n in ROWS[r + 1]) / 2
bpy.context.view_layer.update()
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
cam.data.type = "ORTHO"
cam.data.ortho_scale = 96
cam.location = (0, -160, 60)
look = Vector((0, -22, 0))
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam
W, H = 2400, 1260
sc.render.resolution_x, sc.render.resolution_y = W, H
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, 0))
floor = bpy.context.object
fm = bpy.data.materials.new("floor"); fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.6, 0.55, 1)
floor.data.materials.append(fm)
sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.78, 0.82, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
bpy.ops.object.light_add(type="SUN")
sun = bpy.context.object
sun.data.energy = 3.2; sun.data.angle = math.radians(12)
sun.rotation_euler = (math.radians(42), 0, math.radians(-30))
sc.view_settings.view_transform = "AgX"
tmp = os.path.join(REPO, "reference/architecture/_sheet_render.png")
sc.render.filepath = tmp
bpy.ops.render.render(write_still=True)

# where each piece landed in the picture: badge at its front-bottom, name under it
spots = {}
for code, c in codes.items():
    o = bpy.data.objects[c["piece"]]
    bb = [o.matrix_world @ Vector(p) for p in o.bound_box]
    front = Vector((o.location.x, min(p.y for p in bb), 0.0))
    v = world_to_camera_view(sc, cam, front)
    spots[code] = (v.x * W, (1 - v.y) * H)

im = Image.open(tmp).convert("RGB")
pad_top = 120
pad_bottom = 70
sheet = Image.new("RGB", (W, H + pad_top + pad_bottom), (244, 234, 210))
sheet.paste(im, (0, pad_top))
d = ImageDraw.Draw(sheet)
serif = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
sansb = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
d.text((40, 30), "Thoroughbred · Ascot site components", font=ImageFont.truetype(serif, 44), fill=(31, 90, 56))
d.text((40, 84), "Letter codes for planning layouts. Sizes are true metres: width × depth (front-back) × height. Small pieces on the bottom rows are drawn enlarged.",
       font=ImageFont.truetype(sans, 22), fill=(79, 93, 74))
fb, fs = ImageFont.truetype(sansb, 26), ImageFont.truetype(sans, 17)
last_row = set(ROWS[-1])
k_last = 0
for code, (x, y) in spots.items():
    c = codes[code]
    y = y + pad_top + 26
    if c["piece"] in last_row:                       # the small pieces sit close: stagger their labels
        y += 58 if k_last % 2 else 0
        k_last += 1
    r = 22
    d.ellipse([x - r, y - r, x + r, y + r], fill=(31, 90, 56), outline=(244, 234, 210), width=3)
    d.text((x, y), code, font=fb, fill=(244, 234, 210), anchor="mm")
    lines = [c["name"].replace(" (2.5 m)", ""), "%g × %g × %g m" % (c["width"], c["depth"], c["height"])]
    for k, t in enumerate(lines):
        tw = d.textlength(t, font=fs)
        d.rectangle([x - tw / 2 - 5, y + r + 4 + k * 21, x + tw / 2 + 5, y + r + 24 + k * 21], fill=(244, 234, 210))
        d.text((x, y + r + 14 + k * 21), t, font=fs, fill=(24, 63, 42), anchor="mm")
out = os.path.join(REPO, "reference/architecture/site-components-codes.png")
sheet.save(out, optimize=True)
os.remove(tmp)
json.dump({"_about": "Letter codes for the site components (assets/models/architecture/site_props.glb), as on reference/architecture/site-components-codes.png. Sizes in metres; footprint in the piece's own glTF axes (x across, z front-back, front facing +z), for drawing plans. Built by tools/blender/site_props_sheet.py.",
           "codes": codes}, open(os.path.join(REPO, "assets/models/architecture/site_props_codes.json"), "w"), indent=1)
print("wrote", out, flush=True)
