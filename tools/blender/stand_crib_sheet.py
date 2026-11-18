"""The grandstand crib sheet: every grandstand and pavilion in the kit, from all the courses, on two sheets.

    python3.11 tools/blender/stand_crib_sheet.py            # both sheets (about 8 minutes)
    PART=tiles python3.11 ...  /  PART=elevations python3.11 ...

Owner, 17 Nov 2026: "before we implement to the park I want to bring together the kit of part grandstands. Can you
bring in the pavilion stands from the other courses with these grandstands to create a fresh crib sheet."

Reads the exported pieces (assets/models/architecture/*.glb: the Park, York, the July Course, the Rowley Mile, Ascot's
Victorian grandstand), so re-run the builds first if a piece has changed. Writes, in reference/stands/:
  crib-sheet-tiles.jpg       each piece from the front three-quarters, with its course, name, code name and size
  crib-sheet-elevations.jpg  every piece's front elevation at one scale, on a common ground line, with a scale bar
Every piece's front faces -y (the course), x along the front, origin the middle of its front on the ground.
"""
import math, os, bpy
from mathutils import Vector

REPO = os.path.abspath(os.environ.get("REPO", "."))
ARCH = os.path.join(REPO, "assets/models/architecture")
OUT = os.path.join(REPO, "reference/stands"); os.makedirs(OUT, exist_ok=True)
PART = os.environ.get("PART", "both")

# (file, object name or "*" for the whole file, course, display name), grouped in the order they're shown
CAT = [
    ("The Park (kit)", [
        ("park_stands", "park_tiered_stand", "Tiered stand (York 1895)"),
        ("park_stands", "park_balcony_stand", "Balcony stand"),
        ("park_stands", "park_roof_terrace_stand", "Roof-terrace stand"),
        ("park_stands", "park_arch_stand", "Barrel-roof stand"),
        ("park_stands", "park_gable_stand", "Pitched-roof stand"),
        ("park_stands", "park_old_pavilion", "Old pavilion"),
        ("park_stands", "park_victorian", "Victorian pavilion (towers)"),
        ("park_stands", "park_tent_stand", "Tented stand"),
        ("park_stands", "park_mast_stand", "Mast stand"),
        ("park_stands", "park_glass_box", "Glass box"),
        ("park_stands", "park_glass_box_small", "Glass box, small"),
        ("park_stands", "park_clock_house", "Clock house (brick block)"),
        ("park_stands", "park_terrace", "Low terraces"),
    ]),
    ("York", [
        ("york_stands", "york_stand_north", "North stand"),
        ("york_stands", "york_stand_south", "South stand"),
        ("york_stands", "york_big_pavilion", "Big pavilion"),
        ("york_stands", "york_pavilions", "Pavilions"),
        ("york_stands", "york_end_stand", "End stand"),
        ("york_stands", "york_clock_tower", "Clock tower"),
    ]),
    ("Newmarket, July Course", [
        ("july_stands", "old_pavilion", "Old pavilion (July)"),
        ("july_stands", "old_pavilion_wing", "Old pavilion, wing"),
        ("july_stands", "pavilion_small", "Small pavilion"),
        ("july_stands", "victorian_house", "Victorian house"),
    ]),
    ("Newmarket, Rowley Mile", [
        ("rowley_stands", "millennium_stand", "Millennium stand"),
        ("rowley_stands", "victorian_stand", "Victorian stand"),
        ("rowley_stands", "rowley_stand", "Rowley stand"),
        ("rowley_stands", "ring_pavilion", "Ring pavilion"),
        ("rowley_stands", "victorian_pavilion", "Little Victorian pavilion (lookout)"),
    ]),
    ("Epsom", [
        ("epsom_stands", "epsom_grandstand", "Epsom grandstand"),
        ("epsom_stands", "epsom_balcony_stand", "Epsom balcony stand"),
        ("epsom_stands", "epsom_rowley_stand", "Epsom Rowley-style stand"),
    ]),
    ("Ascot", [
        ("victorian_grandstand", "*", "Victorian grandstand"),
        ("ascot_main_stand", "*", "Main stand (modern)"),
    ]),
    ("Ascot, stand modules", [
        ("stand_modules", "module_clock_centre", "Clock centre"),
        ("stand_modules", "module_grand_pavilion", "Grand pavilion"),
        ("stand_modules", "module_pavilion", "Pavilion"),
        ("stand_modules", "module_end_pavilion", "End pavilion"),
        ("stand_modules", "module_terrace_stand", "Terrace stand"),
        ("stand_modules", "module_three_storey_block", "Three-storey block"),
        ("stand_modules", "module_window_block", "Window block"),
        ("stand_modules", "module_ironwork_bay", "Ironwork bay"),
        ("stand_modules", "module_stair_bay", "Stair bay"),
        ("stand_modules", "module_veranda_low", "Low veranda"),
        ("stand_modules", "module_veranda_wing", "Veranda wing"),
        ("stand_modules", "module_veranda_wing_raised", "Veranda wing, raised"),
        ("stand_modules", "module_porch", "Porch"),
        ("stand_modules", "module_link", "Link"),
    ]),
    ("Built for tier 2 (kit pieces combined)", [
        ("doncaster_stands", "park_balcony_stand_clock", "Balcony stand + clock tower (Doncaster)"),
        ("newbury_stands", "park_roof_terrace_stand_postcard", "Roof-terrace stand + postcard roof pieces (Newbury)"),
    ]),
]
# every piece gets a number, shown on both sheets, so a piece can be named without doubt (owner, 18 Nov 21:36)
NUM = {}
for _g, _items in CAT:
    for _f, _n, _l in _items: NUM[(_f, _n)] = len(NUM) + 1

# ---- load every file once; each piece becomes an empty with its meshes under it
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
PIECES = {}
for fname in sorted({f for _, items in CAT for f, _, _ in items}):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(ARCH, fname + ".glb"))
    new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for grp, items in CAT:
        for f, name, _ in items:
            if f != fname:
                continue
            obs = new if name == "*" else [o for o in new if o.name == name or o.name.startswith(name + ".")]
            assert obs, (fname, name)
            PIECES[(f, name)] = obs
for o in bpy.data.objects:
    if o.type == "MESH":
        o.hide_render = True


def bbox(obs):
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def show(obs):
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = o not in obs


world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 3.6; sun.data.angle = math.radians(3); sun.rotation_euler = (math.radians(52), 0, math.radians(-35))
scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"
bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -0.02)); ground = bpy.context.object
gm = bpy.data.materials.new("ground"); gm.use_nodes = True
gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.70, 0.52, 1)
ground.data.materials.append(gm)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.clip_end = 5000

from PIL import Image, ImageDraw, ImageFont
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
FS = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
FB = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
FT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
INK = (40, 40, 44)
SIZES = {}
for k, obs in PIECES.items():
    lo, hi = bbox(obs)
    SIZES[k] = (hi.x - lo.x, hi.y - lo.y, hi.z, lo, hi)

# ------------------------------------------------------------------ sheet 1: tiles, three-quarter views
if PART in ("both", "tiles"):
    TW, TH, COLS = 760, 470, 5
    scene.render.resolution_x, scene.render.resolution_y = TW, TH
    scene.render.film_transparent = False
    bg.inputs["Color"].default_value = (0.56, 0.70, 0.90, 1); bg.inputs["Strength"].default_value = 1.0
    cam.data.type = "PERSP"; cam.data.lens = 35
    rows = []
    for grp, items in CAT:
        tiles = []
        for f, name, label in items:
            obs = PIECES[(f, name)]; show(obs)
            w, d, h, lo, hi = SIZES[(f, name)]
            c = (lo + hi) / 2
            r = 0.5 * (hi - lo).length
            dirn = Vector((0.62, -0.75, 0.30)).normalized()
            dist = r / math.tan(math.radians(25)) * 1.02
            cam.location = c + dirn * dist
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            path = os.path.join(OUT, "_tile.png"); scene.render.filepath = path
            scene.render.image_settings.file_format = "PNG"
            bpy.ops.render.render(write_still=True)
            im = Image.open(path).convert("RGB")
            tiles.append((im, "%d  %s" % (NUM[(f, name)], label), name if name != "*" else f, (w, d, h)))
            print("tile", grp, label, flush=True)
        rows.append((grp, tiles))
    LH = 74
    nrows = sum(math.ceil(len(t) / COLS) for _, t in rows)
    Wd = COLS * TW + (COLS + 1) * 16
    Hd = 110 + nrows * (TH + LH + 16) + len(rows) * 50
    sheet = Image.new("RGB", (Wd, Hd), "white"); d = ImageDraw.Draw(sheet)
    d.text((16, 20), "Grandstand crib sheet: the kit of parts, from every course (18 Nov 2026)", fill=INK, font=FT)
    d.text((16, 66), "Sizes are width x depth x height in metres (height to the highest point, flags and flagpoles included).",
           fill=(90, 90, 96), font=FS)
    y = 110
    for grp, tiles in rows:
        d.text((16, y + 8), grp, fill=INK, font=FB); y += 50
        for i, (im, label, code, (w, dd, h)) in enumerate(tiles):
            if i and i % COLS == 0:
                y += TH + LH + 16
            x = 16 + (i % COLS) * (TW + 16)
            sheet.paste(im, (x, y))
            d.text((x + 4, y + TH + 8), label, fill=INK, font=F)
            d.text((x + 4, y + TH + 38), "%s   %.0f x %.0f x %.0f m" % (code, w, dd, h), fill=(90, 90, 96), font=FS)
        y += TH + LH + 16
    sheet.save(os.path.join(OUT, "crib-sheet-tiles.jpg"), quality=88)
    os.remove(os.path.join(OUT, "_tile.png"))
    print("tiles written", flush=True)

# ------------------------------------------------------------------ sheet 2: front elevations at one scale
if PART in ("both", "elevations"):
    PXM = 7.0                                           # pixels a metre
    scene.render.film_transparent = True
    bg.inputs["Color"].default_value = (1, 1, 1, 1); bg.inputs["Strength"].default_value = 0.75
    sun.data.energy = 3.2; sun.rotation_euler = (math.radians(55), 0, math.radians(-25))
    ground.hide_render = True
    cam.data.type = "ORTHO"
    HMAX = max(s[2] for s in SIZES.values()) + 2
    ELH = int(HMAX * PXM) + 10
    rows, cur, curw, LIMIT = [], [], 0, 2400
    for grp, items in CAT:
        for f, name, label in items:
            w = SIZES[(f, name)][0]
            slot = max(w * PXM + 8, 230) + 22
            if cur and curw + slot > LIMIT:
                rows.append(cur); cur, curw = [], 0
            cur.append((grp, f, name, label)); curw += slot
    rows.append(cur)
    imgs = {}
    ELDIR = os.path.join(OUT, "elevations"); os.makedirs(ELDIR, exist_ok=True)
    ELIDX = {}
    for row in rows:
        for grp, f, name, label in row:
            obs = PIECES[(f, name)]; show(obs)
            w, d, h, lo, hi = SIZES[(f, name)]
            rw, rh = int(math.ceil(w * PXM)) + 8, ELH
            scene.render.resolution_x, scene.render.resolution_y = rw, rh
            cx = (lo.x + hi.x) / 2
            cam.data.ortho_scale = max(rw, rh) / PXM
            zc = (rh / PXM) / 2 - 0.6                    # the ground 0.6 m above the image's foot
            cam.location = (cx, lo.y - 400, zc); cam.rotation_euler = (math.radians(90), 0, 0)
            cam.data.clip_start = 1.0
            path = os.path.join(OUT, "_el.png"); scene.render.filepath = path
            scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"
            bpy.ops.render.render(write_still=True)
            imgs[(f, name)] = Image.open(path).convert("RGBA").copy()
            # each piece's elevation on its own too (transparent, PXM px a metre, the ground 0.6 m above the foot),
            # for the course configurator (tools/course/kit/stand_config.py)
            code = name if name != "*" else f
            imgs[(f, name)].save(os.path.join(ELDIR, code + ".png"))
            ELIDX[code] = {"file": f, "object": name, "label": label, "course": grp, "width": round(w, 2), "depth": round(d, 2),
                           "height": round(h, 2), "pxm": PXM, "groundPx": round(0.6 * PXM, 2), "png": code + ".png",
                           "xMin": round(lo.x, 2), "xMax": round(hi.x, 2)}
            print("elevation", label, flush=True)
    LAB = 70
    Wd = LIMIT + 60
    Hd = 150 + len(rows) * (ELH + LAB + 30)
    sheet = Image.new("RGB", (Wd, Hd), "white"); d = ImageDraw.Draw(sheet)
    d.text((30, 20), "Grandstand crib sheet: front elevations, all to one scale (from the course)", fill=INK, font=FT)
    x0, y0 = 30, 80                                     # the scale bar, 0 to 50 m
    for i in range(5):
        d.rectangle([x0 + i * 10 * PXM, y0, x0 + (i + 1) * 10 * PXM, y0 + 12], fill=INK if i % 2 == 0 else (255, 255, 255), outline=INK)
    d.text((x0, y0 + 18), "0", fill=INK, font=FS); d.text((x0 + 50 * PXM - 30, y0 + 18), "50 m", fill=INK, font=FS)
    y = 150
    for row in rows:
        gy = y + ELH - int(0.6 * PXM)                    # the ground line
        d.line([(30, gy), (Wd - 30, gy)], fill=(170, 170, 176), width=2)
        for z in (10, 20, 30):                           # faint level lines every 10 m
            d.line([(30, gy - z * PXM), (Wd - 30, gy - z * PXM)], fill=(225, 225, 230), width=1)
            d.text((Wd - 70, gy - z * PXM - 22), "%d m" % z, fill=(150, 150, 156), font=FS)
        x = 30
        for grp, f, name, label in row:
            im = imgs[(f, name)]
            sheet.paste(im, (x, y), im)
            w, dd, h = SIZES[(f, name)][:3]
            d.text((x + 4, gy + 10), "%d  %s" % (NUM[(f, name)], label), fill=INK, font=FS)
            d.text((x + 4, gy + 34), "%s, %.0f m" % (grp.replace("Newmarket, ", ""), w), fill=(110, 110, 116), font=FS)
            x += max(im.width, 230) + 22
        y += ELH + LAB + 30
    sheet.save(os.path.join(OUT, "crib-sheet-elevations.jpg"), quality=88)
    import json as _json
    _json.dump({"_about": "Each kit piece's front elevation, from the course, at pxm pixels a metre; the ground line groundPx "
                          "above the image's foot; xMin/xMax the piece's extent along the front about its own origin.",
                "pieces": ELIDX}, open(os.path.join(ELDIR, "index.json"), "w"), indent=1)
    os.remove(os.path.join(OUT, "_el.png"))
    print("elevations written", flush=True)
