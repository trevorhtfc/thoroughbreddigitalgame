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
EXTRA = {"canopy": "#9aa1ab", "canopy_under": "#6d7480", "teal": "#7fa7aa", "paint": "#f4e6d0", "deck": "#dcc4a2", "stone": "#f2e4cc", "tile": "#cf8f73", "screen": "#2f3340",
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
def pavilion_pair():
    """Owner, 16 Nov evening: the pavilion mix was too big, "reduce to 2 stands or make them a bit smaller and cuter".
    Two small buildings side by side from Ascot's kit: an iron-lace pavilion of two levels and a three-storey tall
    block with a room on its roof, a little lane between them. About 31 m in all."""
    nb, gap, D = 4, 3.0, 14.0
    w = nb * BAY
    L = 2 * w + gap
    x = -L / 2
    ironwork({"x0": x, "x1": x + w, "depth": D, "levels": 2, "party": ()})
    K.hip_roof(x - 0.3, x + w + 0.3, -0.5, D + 0.3, P + 2 * S + 0.35, 2.4, 0.4)       # a little hipped roof
    block({"x0": x + w + gap, "x1": x + L, "depth": D, "storeys": 3, "party": (), "roof_room": True})
    return {"width": round(L, 2), "depth": D, "height": round(P + 3 * S + 3.6 + 1.0, 2)}


# ------------------------------------------------------------------------------------------ 3: the two grandstands
def canopy_grandstand(L, tiers, tower=False, link=0.0):
    """York's two big stands (owner, 16 Nov evening, with photos of the Ebor and Knavesmire stands: "this is the
    proportion we want", "this nice step between the 2 stands"): tall and fairly short, as the real ones, in our hand.
    From the lawn back:
      - open standing steps rising from the lawn (the crowd right down to the rail lawn);
      - a raked seating deck over a glazed concourse;
      - balconied tiers stacked one over another, a glazed wall behind;
      - an open band of white frame and cross braces under the roof;
      - the deep canopy, thin at its front edge, tipping up towards the course and reaching out over the deck,
        with a pale teal fascia.
    tiers: balcony tiers (the Ebor stand 4, the Knavesmire stand 2: the step between them). tower: a brick stair tower
    at the left end (the Ebor stand's, as the photo). link: a low glazed link with steps off the left end, filling
    the step between the two stands. Origin: the middle of the front (the foot of the steps) on the ground."""
    h = L / 2
    R, tr, rs = 9, 1.0, 0.34                                     # the standing steps
    yS = R * tr                                                   # their back: the concourse front
    prof = [(0.0, -1.0)]
    for i in range(R):
        prof += [(i * tr, 0.2 + i * rs), ((i + 1) * tr, 0.2 + i * rs)]
        area(-h + 0.3, h - 0.3, i * tr + 0.1, (i + 1) * tr - 0.1, 0.2 + i * rs)
    prof += [(yS, -1.0)]
    K.prism_x("steps", -h, h, prof)
    zd = 0.2 + R * rs + 1.2                                       # the seating deck's front, over the concourse
    yW = yS + 7.0                                                 # the glazed wall behind the balconies
    D = yW + 16.0                                                 # the back of the building
    # the concourse under the deck: glazed, recessed
    K.box("wall", -h, h, yS + 1.2, D, -1.0, zd)
    K.screen(-h, h, yS + 1.15, 0.0, zd - 0.6)
    K.box("trim", -h, h, yS - 0.1, yS + 1.2, zd - 0.45, zd)
    # the raked seating deck: rows from the deck's front edge back to the glazed wall
    rows, dtr, drs = 6, (yW - yS) / 6, 0.42
    prof = [(yS, zd - 0.5)]
    for i in range(rows):
        prof += [(yS + i * dtr, zd + i * drs), (yS + (i + 1) * dtr, zd + i * drs)]
        K.box("seat", -h + 0.4, h - 0.4, yS + (i + 1) * dtr - 0.45, yS + (i + 1) * dtr - 0.12, zd + i * drs, zd + i * drs + 0.42)
        area(-h + 0.4, h - 0.4, yS + i * dtr + 0.05, yS + (i + 1) * dtr - 0.5, zd + i * drs)
    prof += [(yW, zd - 0.5)]
    K.prism_x("concrete", -h, h, prof)
    K.box("glass", -h + 0.2, h - 0.2, yS - 0.02, yS + 0.08, zd, zd + 1.0)              # a glass rail to the deck
    K.box("trim", -h, h, yS - 0.06, yS + 0.12, zd + 1.0, zd + 1.12)
    # the balcony tiers
    zb0 = zd + rows * drs + 2.4
    SB = 3.7
    yB = yW - 2.2                                                 # balcony front
    K.box("wall", -h, h, yW, D, zd, zb0 + tiers * SB)
    for k in range(tiers):
        z = zb0 + k * SB
        K.box("trim", -h, h, yB - 0.15, yW, z - 0.3, z)                         # the slab
        K.box("glass", -h + 0.1, h - 0.1, yB - 0.02, yB + 0.06, z, z + 1.0)     # glass balustrade
        K.box("trim", -h, h, yB - 0.08, yB + 0.12, z + 1.0, z + 1.12)
        K.screen(-h, h, yW - 0.05, z, SB - 0.45)
        area(-h + 0.4, h - 0.4, yB + 0.35, yW - 0.3, z)
    zT = zb0 + tiers * SB                                         # the top of the tiers
    K.box("trim", -h, h, yB - 0.15, D, zT - 0.3, zT)
    # the open band of frame and braces under the roof
    zR = zT + 4.2                                                 # the canopy's back edge (it rises towards the front)
    yF, zF, th = yS - 2.0, zR + 5.0, 0.6                          # its front edge: out over the deck and the top steps
    yU0, zU0, yU1, zU1 = yF + 0.4, zF - 1.3, D + 0.8, zR - 0.6     # its underside, front to back
    under = lambda y: zU0 + (zU1 - zU0) * (y - yU0) / (yU1 - yU0)
    nb = max(2, round(L / 8.0))
    for i in range(nb + 1):
        x = -h + L * i / nb
        K.box("trim", x - 0.32, x + 0.32, yB - 0.6, yB, zd, under(yB) + 0.1)   # the big front frame columns
        K.box("trim", x - 0.25, x + 0.25, D - 0.5, D, zT, zR)
        if i < nb and not K.far:
            xa, xb = x + 0.3, x + L / nb - 0.3
            strut("trim", (xa, yB - 0.3, zT + 0.2), (xb, yB - 0.3, zR + 0.9), r=0.09)
            strut("trim", (xb, yB - 0.3, zT + 0.2), (xa, yB - 0.3, zR + 0.9), r=0.09)
    K.box("trim", -h, h, yB - 0.6, yB, zT + 0.0, zT + 0.35)
    K.box("glass", -h, h, yW + 1.5, yW + 1.6, zT, zR - 0.2)                     # a glazed back to the band
    # the canopy: front edge well out over the deck, tipping up towards the course
    K.prism_x("canopy", -h - 1.2, h + 1.2, [(yF, zF), (D + 0.8, zR + 0.3), (D + 0.8, zR + 0.3 + th), (yF, zF + th)])
    K.prism_x("canopy_under", -h - 1.2, h + 1.2, [(yU0, zU0), (yU1, zU1), (D + 0.8, zR + 0.3), (yF, zF)])
    K.box("teal", -h - 1.25, h + 1.25, yF - 0.25, yF + 0.05, zF - 1.35, zF + th + 0.2)        # the fascia
    for x in (-h - 1.2, h + 1.2):                                                            # the canopy's thin ends
        K.prism_x("teal", x - 0.08, x + 0.08, [(yF, zF + th + 0.2), (D + 0.8, zR + 0.3 + th + 0.1), (D + 0.8, zR + 0.2), (yF, zF + th - 0.1)])
    # the ends: closed side walls up the tiers
    K.box("wall", -h - 0.25, -h, yW, D, zd, zT)
    K.box("wall", h, h + 0.25, yW, D, zd, zT)
    top = zF + th + 0.2
    if tower:                                                     # the brick stair tower at the left end
        tx0, tx1 = -h - 6.5, -h - 0.3
        K.box("brick", tx0, tx1, yS + 2.0, D - 1.0, -1.0, zR + 0.5)
        K.box("trim", tx0 - 0.15, tx1 + 0.15, yS + 1.85, D - 0.85, zR + 0.5, zR + 0.9)
        for k in range(int((zR - 3) // 3.7)):
            K.box("glass", tx0 + 1.8, tx1 - 1.8, yS + 1.95, yS + 2.05, 2.5 + k * 3.7, 4.6 + k * 3.7)
        K.door((tx0 + tx1) / 2, yS + 2.0, 0.0, 1.6, 2.6)
    if link > 0:                                                  # the low link and steps off the left end (the step)
        lx0, lx1 = -h - link, -h
        prof = [(0.0, -1.0)]
        for i in range(R):
            prof += [(i * tr, 0.2 + i * rs), ((i + 1) * tr, 0.2 + i * rs)]
            area(lx0 + 0.3, lx1 - 0.3, i * tr + 0.1, (i + 1) * tr - 0.1, 0.2 + i * rs)
        prof += [(yS, -1.0)]
        K.prism_x("steps", lx0, lx1, prof)
        K.box("wall", lx0, lx1, yS + 1.2, D - 2.0, -1.0, zd + 4.0)
        K.screen(lx0, lx1, yS + 1.15, 0.0, zd + 3.2)
        K.box("trim", lx0 - 0.2, lx1, yS + 0.6, D - 1.8, zd + 4.0, zd + 4.4)
        K.balustrade(lx0, lx1, yS + 0.8, zd + 4.4, h=1.0, mat="trim", spacing=0.3, piers=False)
        area(lx0 + 0.4, lx1 - 0.4, yS + 1.2, D - 2.5, zd + 4.4)
    info = {"width": round(L, 2), "depth": round(D + 0.8, 2), "height": round(top, 2)}
    return info


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
    ("york_pavilions", pavilion_pair),
    # 3: the two grandstands (owner, 16 Nov evening, with photos): the Ebor stand tall with four balconied tiers and a
    # brick stair tower, the Knavesmire stand a step lower with two, a low link between; each under its own deep canopy
    ("york_stand_north", lambda: canopy_grandstand(44.0, 4, tower=True)),
    ("york_stand_south", lambda: canopy_grandstand(46.0, 2, link=7.0)),
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
