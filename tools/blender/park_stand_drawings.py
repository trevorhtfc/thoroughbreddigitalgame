"""Drawings of a Park stand piece: a front elevation and a cross-section through a bay, with its levels marked.

    PIECE=park_arch_stand python3.11 tools/blender/park_stand_drawings.py

Owner, 17 Nov 2026: "turn our attention to the barrel roof stand ... if you could give me an elevation and a section of
that would be great". Both views are orthographic (true to scale). The section is cut by the camera's near clipping
plane through the middle of a bay (CUT_BAY, counted from the left), looking from the right-hand end, so the course is
on the left. The levels come from the piece's own "section" figures in park_stands.json.

Writes reference/park/drawings/<piece>-drawings.jpg (the two on one sheet; the single renders, -elevation.png and
-section.png, are working files).
"""
import os, sys, math
os.environ.pop("SHEET", None); os.environ.pop("ARRANGE", None)
REPO = os.path.abspath(os.environ.get("REPO", "."))
exec(open(os.path.join(REPO, "tools/blender/build_park_stands.py")).read())

PIECE = os.environ.get("PIECE", "park_arch_stand")
CUT_BAY = int(os.environ.get("CUT_BAY", "1"))
OUT = os.path.join(REPO, "reference/park/drawings")
os.makedirs(OUT, exist_ok=True)
info = INFO[PIECE]; sec = info["section"]
W, H = 2400, 1300

scene = bpy.context.scene
world = bpy.data.worlds.new("paper"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.75
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 3.2; sun.rotation_euler = (math.radians(55), 0, math.radians(-25))
scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "24")); scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.view_settings.view_transform = "AgX"
scene.render.film_transparent = True               # the sky left clear: laid on white paper below
for n, o in OBJ.items():
    o.location = (0, 0, 0) if n == PIECE else (99999, 0, 0)
bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -0.01))
bpy.context.object.data.materials.append(material("paper_ground", "#e4e1da"))


def ortho(name, loc, look, scale, clip_start=0.1):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); scene.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = scale; cam.data.clip_start = clip_start; cam.data.clip_end = 2000
    cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    path = os.path.join(OUT, "%s-%s.png" % (PIECE, name))
    scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"; scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


L, D, Ht = info["width"], info["depth"], info["height"]
zc = Ht * 0.45
s_el = max(L * 1.12, Ht * 1.25 * W / H)
el = ortho("elevation", (0, -300, zc), (0, 0, zc), s_el)
h = L / 2
xcut = -h + sec["bay"] * (CUT_BAY + 0.5)
yc = D * 0.45
s_se = max((D + 8) * 1.25, Ht * 1.25 * W / H)
se = ortho("section", (xcut + 300, yc, zc), (xcut, yc, zc), s_se, clip_start=300.0)

# ---- the marks, drawn over the renders
from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
INK = (40, 40, 44)
LEVELS = [("ground", 0.0), ("top of standing steps", sec["stepsTop"]), ("seating deck, front", sec["shoulder"]),
          ("seating deck, back", sec["deckBack"]), ("vault springing", sec["springing"]), ("vault crown", sec["crown"]),
          ("clock bay crown", sec["raisedCrown"])]
if "upperFloor" in sec:                                   # the two-tier stand (17 Nov)
    LEVELS[4:4] = [("upper tier, front", sec["upperFloor"]), ("upper tier, back", sec["upperBack"])]


def marks(path, scale, centre_u, title, across):
    rgba = Image.open(path).convert("RGBA")
    im = Image.new("RGB", rgba.size, "white"); im.paste(rgba, (0, 0), rgba); d = ImageDraw.Draw(im)
    k = W / scale
    zpx = lambda z: H / 2 - (z - zc) * k
    upx = lambda u: W / 2 + (u - centre_u) * k
    last = 1e9
    for name, z in LEVELS:
        y = zpx(z)
        d.line([(60, y), (W - 440, y)], fill=(150, 150, 160), width=2)
        ty = min(y - 14, last - 30)
        d.text((W - 430, ty), "+%.2f  %s" % (z, name), fill=INK, font=F)
        last = ty
    for j, (u, label) in enumerate(across):                              # marks along the bottom, staggered
        x = upx(u)
        dy = 34 * (j % 2)
        d.line([(x, H - 130), (x, H - 92 + dy)], fill=INK, width=3)
        if label:
            d.text((x + 6, H - 100 + dy), label, fill=INK, font=F)
    x0 = 80; y0 = 60                                                     # the scale bar: 0 to 10 m
    for i in range(5):
        d.rectangle([x0 + i * 2 * k, y0, x0 + (i + 1) * 2 * k, y0 + 12], fill=INK if i % 2 == 0 else (255, 255, 255), outline=INK)
    d.text((x0, y0 + 18), "0", fill=INK, font=F); d.text((x0 + 10 * k - 30, y0 + 18), "10 m", fill=INK, font=F)
    d.text((x0, 10), title, fill=INK, font=FB)
    im.save(path)
    return im


bays = [(-h + sec["bay"] * i, "") for i in range(0, sec["bays"] + 1, 3)]
im1 = marks(el, s_el, 0.0, "Barrel-roof grandstand: front elevation, from the course (%d bays of %.0f m, %.0f m long)" % (sec["bays"], sec["bay"], L),
            [(-h + sec["bay"] * i, "") for i in range(sec["bays"] + 1)])
im2 = marks(se, s_se, yc, "Cross-section through the middle of a bay, the course on the left (cut through a vault's crown)",
            [(0.0, "foot of the steps (0 m)"), (sec["stepsBack"], "concourse front (%.1f m)" % sec["stepsBack"]),
             (sec["columns"], "columns (%.1f m)" % sec["columns"]), (sec["deckBackY"], "back of deck (%.1f m)" % sec["deckBackY"]),
             (sec["back"], "back wall (%.1f m)" % sec["back"])])
sheet = Image.new("RGB", (W, 2 * H + 40), "white")
sheet.paste(im1, (0, 0)); sheet.paste(im2, (0, H + 40))
sheet.save(os.path.join(OUT, "%s-drawings.jpg" % PIECE), quality=90)
print("drawings written", sec, flush=True)
