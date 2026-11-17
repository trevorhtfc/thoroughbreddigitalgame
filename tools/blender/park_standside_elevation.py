"""A scaled front elevation of Park stands strung side by side on one front line, with levels and a scale bar.

    STANDS=park_tiered_stand,park_balcony_stand,park_arch_stand,park_old_pavilion,park_gable_stand,park_roof_terrace_stand python3.11 tools/blender/park_standside_elevation.py

Owner, 17 Nov 2026: the barrel-roof stand made two tiers "which we can string them together if need be", then "you had
another stand with a series of pitched roofs.. bring that into the scaled elevation". Orthographic, so true to scale;
writes reference/park/drawings/standside-elevation.jpg (the render PNG is a working file).
"""
import os
REPO = os.path.abspath(os.environ.get("REPO", "."))
for k in ("SHEET", "ARRANGE"):
    os.environ.pop(k, None)
exec(open(os.path.join(REPO, "tools/blender/build_park_stands.py")).read())

NAMES = os.environ.get("STANDS", "park_tiered_stand,park_balcony_stand,park_arch_stand,park_old_pavilion,park_gable_stand,"
                                 "park_roof_terrace_stand").split(",")
LABEL = {"park_balcony_stand": "Balcony stand", "park_arch_stand": "Barrel-roof stand", "park_gable_stand": "Pitched-roof stand",
         "park_roof_terrace_stand": "Roof-terrace stand", "park_tiered_stand": "Tiered stand", "park_old_pavilion": "Old pavilion",
         "park_victorian": "Victorian pavilion"}
OUT = os.path.join(REPO, "reference/park/drawings"); os.makedirs(OUT, exist_ok=True)
W, H = 3200, 640

def span(n):                                       # the piece's full width on the ground (steps' cheeks included)
    return INFO[n]["width"] + (0.7 if n in ("park_balcony_stand", "park_roof_terrace_stand") else 0.0)   # + the cheeks' newels

xs, x = [], 0.0
for n in NAMES:
    w = span(n); xs.append(x + w / 2); x += w
total = x
for n, o in OBJ.items():
    o.location = (99999, 0, 0)
for n, cx in zip(NAMES, xs):
    OBJ[n].location = (cx - total / 2, 0, 0)

scene = bpy.context.scene
world = bpy.data.worlds.new("paper"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.75
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(55), 0, math.radians(-25))
scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "24")); scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.view_settings.view_transform = "AgX"; scene.render.film_transparent = True
scale = total * 1.06; zc = 15.0
cam = bpy.data.objects.new("el", bpy.data.cameras.new("el")); scene.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = scale; cam.data.clip_end = 3000
cam.location = (0, -500, zc); cam.rotation_euler = (Vector((0, 0, zc)) - Vector(cam.location)).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
png = os.path.join(OUT, "standside-elevation.png")
scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"; scene.render.filepath = png
bpy.ops.render.render(write_still=True)

from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
INK = (40, 40, 44)
rgba = Image.open(png).convert("RGBA")
PADR, PADB, PADT = 470, 150, 110
im = Image.new("RGB", (W + PADR, H + PADB + PADT), "white"); im.paste(rgba, (0, PADT), rgba); d = ImageDraw.Draw(im)
k = W / scale
zpx = lambda z: PADT + H / 2 - (z - zc) * k
upx = lambda u: W / 2 + u * k
lv = {}
for n in NAMES:
    s = INFO[n].get("section", {})
    for key, name in (("upperFloor", "upper tiers' floor"), ("springing", "springing / cornice top"),
                      ("crown", "gable ridges" if n == "park_gable_stand" else "vault crowns")):
        if key in s:
            lv[name] = s[key] + (0.6 if n == "park_gable_stand" and key == "crown" else 0.0)
LEVELS = [("ground", 0.0)] + sorted(lv.items(), key=lambda t: t[1])
last = 1e9
for name, z in LEVELS:
    y = zpx(z)
    d.line([(30, y), (W + 10, y)], fill=(160, 160, 170), width=2)
    ty = min(y - 15, last - 32); last = ty
    d.text((W + 20, ty), "+%.2f  %s" % (z, name), fill=INK, font=F)
for n, cx in zip(NAMES, xs):                      # the pieces' names and widths under them, their joints marked
    u0, u1 = cx - total / 2 - span(n) / 2, cx - total / 2 + span(n) / 2
    yb = zpx(0) + 30
    for u in (u0, u1):
        d.line([(upx(u), yb), (upx(u), yb + 40)], fill=INK, width=3)
    d.line([(upx(u0), yb + 20), (upx(u1), yb + 20)], fill=INK, width=2)
    t = "%s, %.1f m" % (LABEL.get(n, n), span(n))
    tw = d.textlength(t, font=F)
    d.rectangle([upx(cx - total / 2) - tw / 2 - 8, yb + 50, upx(cx - total / 2) + tw / 2 + 8, yb + 86], fill="white")
    d.text((upx(cx - total / 2) - tw / 2, yb + 52), t, fill=INK, font=F)
x0, y0 = 60, 70                                    # the scale bar: 0 to 50 m in 10s
for i in range(5):
    d.rectangle([x0 + i * 10 * k, y0, x0 + (i + 1) * 10 * k, y0 + 14], fill=INK if i % 2 == 0 else (255, 255, 255), outline=INK)
for i in (0, 10, 20, 30, 40, 50):
    d.text((x0 + i * k - 8, y0 + 20), "%d" % i if i < 50 else "50 m", fill=INK, font=F)
d.text((x0, 18), "The Park, stand side: front elevation from the course, to scale (%.0f m of stands on one front line)" % total, fill=INK, font=FB)
im.save(os.path.join(OUT, "standside-elevation.jpg"), quality=90)
print("elevation written", total, LEVELS, flush=True)
