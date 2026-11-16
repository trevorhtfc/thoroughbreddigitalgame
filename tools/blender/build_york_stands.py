"""Build York's stand-side buildings and its Clock Tower, from the pieces the other courses already have.

    python3 -c "exec(open('tools/blender/build_york_stands.py').read())"
    SHEET=1 python3 -c "exec(open(...).read())"      # also render a catalogue sheet: reference/york/renders/stands-sheet.png

Owner, 16 Nov 2026, left to right as seen from the infield (with his photos of York and the crib sheet,
https://claude.ai/artifact/UcCeg7EhQtww6KRL74xvoZ):
  1. "take old pavilion from the July Course and add two more storeys and fix the width to the York scale"
  2. "mix ironwork profile and tall block profile from the Ascot kit as per the Ascot cover image"
  3. "take the grand canopy of the terrace profile to crank it. add a bit of height variation and add a terrace to the
     front of the grandstand"
  4. "end stand: let's take the Victorian stand from the Rowley Mile.. make it longer than the plan"
  5. "you have some clock tower elements you could combine with the judge's box maybe?" (the festival side's Clock Tower)

The pieces' code is the other courses' own: the Rowley Mile build (which brings Ascot's stand_pieces.py and the grand
pavilion stand), and the July Course's old pavilion and judge's box, read out of build_july_stands.py.

Writes assets/models/architecture/york_stands.glb and .json (as july_stands.json: size, crowd areas per piece; origin the
middle of the front on the ground, front facing -y in Blender, +z in glTF).
"""
import json, math, os, re

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

# ---- the Rowley Mile build's definitions (kit, palette, Ascot's pieces, grand pavilion stand), without its build loop
_src = open(rp("tools/blender/build_rowley_stands.py")).read()
exec(_src[:_src.index("\nPIECES = [")])

# ---- the July Course's old pavilion and judge's box, as written there
_jsrc = open(rp("tools/blender/build_july_stands.py")).read()
def _july(name):
    a = _jsrc.index("def %s(" % name)
    b = _jsrc.index("\n# ----", a)
    return _jsrc[a:b]
ROOF_MAT = "tile"                                 # York's big pavilion: a red-tiled roof (muted terracotta, pastel)
exec(_july("old_pavilion").replace('roof="slate", wall="paint"', 'roof=ROOF_MAT, wall="paint"'))
exec(_july("judges_box"))

# materials the borrowed pieces use that the Rowley palette hasn't got (the July Course's own colours)
EXTRA = {"paint": "#f4e6d0", "deck": "#dcc4a2", "stone": "#f2e4cc", "tile": "#cf8f73", "screen": "#2f3340",
         "clock_face": "#fbf5ea", "clock_dark": "#2a2c30", "pot": "#d08a6c"}
for k, v in EXTRA.items():
    if k not in MATS:
        COL[k] = v
        MATS[k] = material("yk_" + k, v, rough=0.9)


# ------------------------------------------------------------------------------------------ 1: the big pavilion
def big_pavilion(L=52.0):
    """The July Course's old pavilion with two more balconied storeys (four in all), at York's scale, under a red-tiled
    roof, with a cross gable in the middle of the front carrying a clock (the owner's photo of York's tall red-roofed
    stand)."""
    info = old_pavilion(L=L, D=11.0, G=4.2, S=3.6, levels=4, stair=True, fence=False)
    E = 4.2 + 4 * 3.6 - 0.25                                    # the eaves (as old_pavilion works them out)
    # the cross gable: a cream gable end standing forward of the roof, with the clock in it
    gw = 11.0
    rz = gable_y(-gw / 2, gw / 2, -0.95, 5.5, E, 38, 0.6, roof=ROOF_MAT, wall="paint")
    zc = E + (rz - E) * 0.45
    K.disc_y("trim", 0.0, -1.10, -0.92, zc, 1.55, segs=32)
    K.disc_y("clock_dark", 0.0, -1.16, -1.08, zc, 1.40, segs=32)
    K.disc_y("clock_face", 0.0, -1.22, -1.14, zc, 1.25, segs=32)
    for h in range(12):
        a = h * math.pi / 6
        K.boxm("clock_dark", Matrix.Translation((math.sin(a) * 1.0, -1.24, zc + math.cos(a) * 1.0)) @ Matrix.Rotation(-a, 4, "Y"),
               0.08 if h % 3 else 0.13, 0.03, 0.3 if h % 3 else 0.42)
    K.cyl("iron", 0.0, 2.2, rz + 0.3, rz + 3.0, 0.05, segs=4, smooth=False)       # a weathervane
    K.box("gilt", -0.5, 0.5, 2.18, 2.22, rz + 2.4, rz + 2.6)
    info["height"] = round(max(info["height"], rz + 3.0), 2)
    return info


# ------------------------------------------------------------------------------------------ 2: the smaller pavilions
def pavilion_mix():
    """Ascot's ironwork and tall-block profiles mixed, as along the Ascot stand: a four-storey tall block, a run of iron
    lace, and a three-storey tall block with a room on its roof. Mixed heights, no slivers (every length 5 bays or more):
    56 m, about the plan's footprint."""
    runs = [("block", 5, {"storeys": 4}), ("iron", 6, {"levels": 3}), ("block", 5, {"storeys": 3, "roof_room": True})]
    L = sum(n for _, n, _ in runs) * BAY
    x = -L / 2
    for i, (kind, n, kw) in enumerate(runs):
        party = tuple(p for p, ok in (("left", i > 0), ("right", i < len(runs) - 1)) if ok)
        seg = dict({"x0": x, "x1": x + n * BAY, "depth": 20.0, "party": party}, **kw)
        (block if kind == "block" else ironwork)(seg)
        x += n * BAY
    # a flight of steps on the front of the middle block, out onto the lawn
    return {"width": round(L, 2), "depth": 20.0, "height": round(P + 4 * S + 4.0, 2)}


# ------------------------------------------------------------------------------------------ 5: the Clock Tower
def clock_tower():
    """The festival side's Clock Tower (owner: the clock tower elements combined with the judge's box): the July
    Course's brick judge's box, made bigger, as the base, with the big screen on its front; Ascot's belfry clock tower
    standing on it; low wings either side with a balcony on their roofs."""
    S0 = 9.0; h = S0 / 2
    K.box("brick", -h, h, 0.0, S0, -1.0, 8.4)
    K.box("stone", -h - 0.15, h + 0.15, -0.15, S0 + 0.15, 3.4, 3.62)
    K.box("stone", -h - 0.3, h + 0.3, -0.3, S0 + 0.3, 8.35, 8.7)
    K.door(0.0, 0.0, 0.0, 1.4, 2.6)
    for x in (-2.6, 2.6):
        K.window(x, 0.0, 0.9, 1.2, 2.0)
    # the big screen on the front, framed in the brick
    K.box("trim", -3.9, 3.9, -0.42, -0.02, 3.9, 8.1)
    K.box("screen", -3.6, 3.6, -0.48, -0.36, 4.15, 7.85)
    # the belfry clock tower on top (Ascot's)
    tower_belfry({"x": 0.0, "y": (S0 - 6.0) / 2, "width": 6.0, "base_z": 8.7, "top_z": 21.5})
    # low wings, a balcony on each roof
    for sgn in (-1, 1):
        a, b = (h, h + 9.0) if sgn > 0 else (-h - 9.0, -h)
        K.box("brick", a, b, 1.0, S0 - 0.5, -1.0, 4.2)
        K.box("stone", a - 0.1, b + 0.1, 0.9, S0 - 0.4, 4.15, 4.4)
        for x in (a + 2.2, a + 4.5, a + 6.8):
            K.window(x, 1.0, 1.0, 1.1, 1.9)
        K.balustrade(a, b, 1.1, 4.4, h=1.0, mat="iron", spacing=0.3)
        area(a + 0.4, b - 0.4, 1.4, 3.2, 4.4)
    area(-h + 0.4, h - 0.4, 0.4, 2.8, 8.7)
    return {"width": S0 + 18.0, "depth": S0 + 0.3, "height": 26.0}


# ------------------------------------------------------------------------------------------ build and export
PIECES = [
    ("york_big_pavilion", lambda: big_pavilion(52.0)),
    ("york_pavilions", pavilion_mix),
    # 3: the grand canopy over the terrace profile, behind a lawn terrace (the Rowley Mile's grand pavilion stand), in two
    # cranked runs; the second with a stair drum at the crank. Height variation: placed at different scales in the layout.
    ("york_stand_north", lambda: grand_pavilion_stand(18, 14, 1.0, 0.2)),                  # 63 m
    ("york_stand_south", lambda: grand_pavilion_stand(22, 14, 1.0, 0.2, drum=True)),       # 77 m, the drum at its left end
    # 4: the Rowley Mile's Victorian stand, longer than the plan's
    ("york_end_stand", lambda: grand_pavilion_stand(34, 10, 1.0, 0.28, end_pavilion=True, roof="hipped")),   # 119 m + 14 m
    ("york_clock_tower", clock_tower),
]
LIB = bpy.data.collections.new("york_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-18s %6d triangles, %d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "York's stand-side buildings and Clock Tower (tools/blender/build_york_stands.py). Building axes: x along "
                     "the front (left to right from the track), y into the building (front faces -y), z up; origin the "
                     "middle of the front on the ground (offset: how far the whole piece's middle is from it along x). "
                     "crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "york_stands.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "york_stands.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported york_stands.glb", flush=True)

if os.environ.get("SHEET"):                      # catalogue renders, to check the pieces: the smaller pieces, then the stands
    groups = [["york_big_pavilion", "york_pavilions", "york_clock_tower"], ["york_stand_north", "york_stand_south", "york_end_stand"]]
    spans = []
    x = 0.0
    for g in groups:
        x0 = x
        for name in g:
            w = INFO[name]["width"]
            OBJ[name].location = (x + w / 2, 0, 0)
            x += w + 12
        spans.append((x0, x - 12))
        x += 120
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.75, 0.8, 0.88, 1)
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(x / 2, 40, 0))
    bpy.context.object.data.materials.append(material("lawn", "#9fbf6a"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.0; sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 2400, 900
    scene.view_settings.view_transform = "AgX"
    os.makedirs(rp("reference/york/renders"), exist_ok=True)
    for k, (a, b) in enumerate(spans):
        mid, span = (a + b) / 2, b - a
        cam = bpy.data.objects.new("c%d" % k, bpy.data.cameras.new("c%d" % k)); cam.data.lens = 30; scene.collection.objects.link(cam)
        dist = span * 0.95
        frm, to = (mid, -dist, dist * 0.22), (mid, 8, 10)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = rp("reference/york/renders/stands-sheet-%d.png" % (k + 1))
        bpy.ops.render.render(write_still=True)
        print("rendered sheet", k + 1, flush=True)
