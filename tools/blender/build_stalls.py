"""Build the starting stalls kit: one stall bay that repeats, its two front half-gates, the unit end tower,
a closing partition, the stall numbers and the top board's plaque.

    python -c "exec(open('tools/blender/build_stalls.py').read())"

Modelled from reference/stalls/ (the owner's photo of a 14-bay set, and frames of Ascot's own stalls at the
Royal Hunt Cup), in the race view's soft heritage look: Ascot green padding, cream tubular frame, yellow
number boards under a cream top board. Simplified: no straps, catches, springs or stitching, grilles as a
few bars, the tower's lattice as a few diagonals, no tow bar, plain wheels; the rear gates don't open.

Sized to the race view's horses (about 2.9 m long and 0.89 m wide at the view's scale): 1.05 m a stall, 3.2 m
deep, end towers 0.9 m wide (owner, 4 Nov: as many stalls across the straight course as will fit).

Writes assets/models/course/starting_stalls.glb (one node per piece), starting_stalls_kit.json (the sizes and
how the pieces fit, for the viewer and tools/course/place_stalls.py) and assets/models/master/starting_stalls.blend.

Axes. Blender: x along the row of stalls (stall numbers rise with x), the front gates on y = 0 and the
horses face -y (they break out towards -y), z up. glTF (y up): x along the row, the horses break out
towards +z. Every node's origin is on the front line at ground level:
  stall_bay        the bay from x 0 to PITCH, with its partition centred on x 0 (the bay to its right
                   supplies the next partition; the last bay of a unit is closed by stall_partition at x PITCH)
  stall_partition  a lone partition, centred on its origin
  stall_tower      the end tower from x 0 to TOWER (between units and at both ends of the row)
  stall_gate_left  the left half-gate, hinged on its origin (the bay's left post), lying along +x when shut
  stall_gate_right the right half-gate, hinged on its origin (the bay's right post), lying along -x when shut
                   Gates open outwards (forwards): in glTF the left gate turns -90 degrees about y, the right +90.
  stall_num_<n>    the figures for stall n, centred on the middle of the number board
  stall_plaque     the wordmark for the top board, centred on its middle (one per unit)
"""
import json, math, os
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
OUT_DIR = os.path.join(REPO, "assets/models/course")
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())

PITCH, DEPTH, TOWER = 1.05, 3.2, 0.9       # stall width (centre to centre), front to rear gates, tower width
                                           # (1.05 leaves 0.93 m between partitions for horses about 0.89 m wide)
PART = 0.12                                # padded partition thickness
TOP = 3.0                                  # top of the overhead frame (the walkway)
GATE = (0.42, 1.45, 2.05)                  # front gate: bottom, top of the padding, top of the grille
NUM_BOARD = {"z0": 2.52, "z1": 2.92, "w": 0.6, "y": -0.07}   # yellow number board on the front, bay-centred
FASCIA = {"z0": 3.05, "z1": 3.62, "y": -0.11}                # cream top board along the front
MAX_NUMBER = 30

# Lit live in the race view under a strong sun, so the greens and the yellow are set deeper than they read on screen.
COL = {"frame": "#f2efe6", "pad": "#174536", "pad_dark": "#12382c", "tube": "#16402f", "yellow": "#f7bd00",
       "figure": "#23272c", "fascia": "#f6f1e4", "word": "#1f5a38", "tyre": "#2d2f31", "hub": "#d9d6cf",
       "deck": "#a7aca4"}
MATS = {k: material("st_" + k, v, rough={"frame": 0.55, "tyre": 0.9, "hub": 0.5}.get(k, 0.8)) for k, v in COL.items()}

col = bpy.data.collections.new("starting_stalls")
bpy.context.scene.collection.children.link(col)


def rod(K, mat, p0, p1, r, segs=8):
    """A round bar between two points."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    if K.far:
        segs = min(segs, 6)
    m = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    g = bmesh.ops.create_cone(K.bm(mat), cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length, matrix=K.M @ m)
    K._smooth(g["verts"])


def pad(K, mat, x0, x1, y0, y1, z0, z1, roll=0.05):
    """A padded panel: a box with soft rolls along its top and bottom edges, so it doesn't read as a hard slab."""
    xc, r = (x0 + x1) / 2, min(abs(x1 - x0), abs(y1 - y0)) / 2
    i = 0.035                                 # the panel sits 35 mm inside the rolls' faces (not in their plane: no flashing)
    if abs(y1 - y0) >= abs(x1 - x0):
        K.box(mat, x0 + i, x1 - i, y0, y1, z0 + roll, z1 - roll)
    else:
        K.box(mat, x0, x1, y0 + i, y1 - i, z0 + roll, z1 - roll)
    if abs(y1 - y0) >= abs(x1 - x0):          # a panel lying along y (a partition)
        for z in (z0 + roll, z1 - roll):
            rod(K, mat, (xc, y0, z), (xc, y1, z), r, 10)
    else:                                     # along x (a gate or a rear panel)
        yc = (y0 + y1) / 2
        for z in (z0 + roll, z1 - roll):
            rod(K, mat, (x0, yc, z), (x1, yc, z), r, 10)


def partition(K, x):
    """The padded side wall between two stalls, its tubular posts and the green rails above it."""
    pad(K, "pad", x - PART / 2, x + PART / 2, 0.22, DEPTH - 0.22, 0.38, 1.62, 0.06)
    # posts front and rear (cream), the partition's top tube and the green upper rails
    for y in (0.0, DEPTH):
        K.cyl("frame", x, y, 0.0, TOP, 0.055, 0.055, 10)
        K.cyl("frame", x, y, 0.0, 0.12, 0.08, 0.08, 10)               # foot
    rod(K, "tube", (x, 0.0, 1.95), (x, DEPTH, 1.95), 0.045)
    rod(K, "tube", (x, 0.0, 2.45), (x, DEPTH, 2.45), 0.045)
    rod(K, "frame", (x, 0.0, TOP), (x, DEPTH, TOP), 0.055)
    K.cyl("tube", x, DEPTH / 2, 1.62, TOP, 0.045, 0.045, 8)           # middle stay
    # the hinge knuckles the gates hang on
    for z in (GATE[0] + 0.15, GATE[2] - 0.15):
        K.cyl("frame", x, 0.0, z - 0.06, z + 0.06, 0.075, 0.075, 10)


def overhead(K, x0, x1):
    """The frame over the stalls: front and rear top tubes, the walkway and its handrails, the boards."""
    for y in (0.0, DEPTH):
        rod(K, "frame", (x0, y, TOP), (x1, y, TOP), 0.06)
        rod(K, "frame", (x0, y, TOP + 0.95), (x1, y, TOP + 0.95), 0.04)      # handrail
        rod(K, "frame", (x0, y, TOP + 0.5), (x1, y, TOP + 0.5), 0.03)        # knee rail
    K.box("deck", x0, x1, DEPTH / 2 - 0.4, DEPTH / 2 + 0.4, TOP - 0.04, TOP + 0.02)   # walkway
    for y in (0.0, DEPTH):
        K.cyl("frame", x0, y, TOP, TOP + 0.95, 0.035, 0.035, 8)              # handrail stanchion
    # the cream top board along the front (continuous from bay to bay)
    f = FASCIA
    K.box("fascia", x0, x1, f["y"] - 0.04, f["y"] + 0.04, f["z0"], f["z1"])
    K.box("frame", x0, x1, f["y"] - 0.06, f["y"] + 0.06, f["z1"], f["z1"] + 0.05)     # capping
    K.box("frame", x0, x1, f["y"] - 0.06, f["y"] + 0.06, f["z0"] - 0.05, f["z0"])
    for x in (x0, x1):                                                       # board brackets back to the frame
        K.box("frame", x - 0.02, x + 0.02, f["y"] + 0.04, 0.0, f["z0"] + 0.1, f["z1"] - 0.1)


def bay():
    K = Kit()
    partition(K, 0.0)
    overhead(K, 0.0, PITCH)
    # rear gate: closed, padded below and barred above, across the back
    pad(K, "pad_dark", PART / 2 + 0.02, PITCH - PART / 2 - 0.02, DEPTH - 0.03, DEPTH + 0.03, 0.45, 1.6, 0.05)
    rod(K, "frame", (PART / 2, DEPTH, 2.1), (PITCH - PART / 2, DEPTH, 2.1), 0.035)
    for i in range(1, 4):
        x = PART / 2 + (PITCH - PART) * i / 4
        rod(K, "frame", (x, DEPTH, 1.6), (x, DEPTH, 2.1), 0.022, 6)
    # the yellow number board on the front, bay-centred, hung from the top tube
    nb, xc = NUM_BOARD, PITCH / 2
    K.box("yellow", xc - nb["w"] / 2, xc + nb["w"] / 2, nb["y"] - 0.025, nb["y"] + 0.025, nb["z0"], nb["z1"])
    K.box("frame", xc - nb["w"] / 2 - 0.03, xc + nb["w"] / 2 + 0.03, nb["y"] + 0.025, nb["y"] + 0.06, nb["z0"] - 0.03, nb["z1"] + 0.03)
    for x in (xc - 0.2, xc + 0.2):
        K.box("frame", x - 0.015, x + 0.015, nb["y"], 0.0, nb["z1"], TOP - 0.05)
    # a rail under the board linking the gate posts (the gates' head rail)
    rod(K, "frame", (0, 0.0, 2.3), (PITCH, 0.0, 2.3), 0.035)
    return K


def gate(side):
    """One half-gate. Built hinged at x 0, lying along +x (left) or -x (right)."""
    K = Kit()
    w = (PITCH - PART) / 2 - 0.02 - 0.02            # gap at the hinge and in the middle
    s = 1 if side == "left" else -1
    a, b = 0.03 * s, (0.03 + w) * s                 # leaf spans from a to b along x
    lo, hi = min(a, b), max(a, b)
    g0, g1, g2 = GATE
    pad(K, "pad", lo, hi, -0.035, 0.035, g0, g1, 0.04)
    # the cream tubular frame round the grille
    rod(K, "frame", (lo, 0, g2), (hi, 0, g2), 0.03)
    rod(K, "frame", (lo, 0, g1), (hi, 0, g1), 0.025)
    for x in (lo + 0.02, hi - 0.02):
        rod(K, "frame", (x, 0, g0 + 0.05), (x, 0, g2), 0.03)
    for i in range(1, 4):                            # grille bars
        x = lo + (hi - lo) * i / 4
        rod(K, "frame", (x, 0, g1), (x, 0, g2), 0.016, 6)
    # hinge straps reaching the post
    for z in (g0 + 0.15, g2 - 0.15):
        K.box("frame", min(0, a), max(0, a), -0.02, 0.02, z - 0.03, z + 0.03)
    return K


def tower():
    """The unit's end tower: a cream lattice frame on tandem wheels, with a ladder up to the walkway."""
    K = Kit()
    x0, x1, H = 0.0, TOWER, TOP + 0.95
    for x in (x0 + 0.06, x1 - 0.06):
        for y in (-0.15, DEPTH + 0.15):
            K.cyl("frame", x, y, 0.35, H, 0.06, 0.06, 10)
            K.sphere("frame", x, y, H + 0.04, 0.075, 1)
    for z in (0.4, 1.7, TOP, H):
        for y in (-0.15, DEPTH + 0.15):
            rod(K, "frame", (x0 + 0.06, y, z), (x1 - 0.06, y, z), 0.045)
        for x in (x0 + 0.06, x1 - 0.06):
            rod(K, "frame", (x, -0.15, z), (x, DEPTH + 0.15, z), 0.045)
    # lattice diagonals on both side faces and on the front and back
    for x in (x0 + 0.06, x1 - 0.06):
        for za, zb in ((0.4, 1.7), (1.7, TOP)):
            rod(K, "frame", (x, -0.15, za), (x, DEPTH / 2, zb), 0.03, 6)
            rod(K, "frame", (x, DEPTH + 0.15, za), (x, DEPTH / 2, zb), 0.03, 6)
    for y in (-0.15, DEPTH + 0.15):
        rod(K, "frame", (x0 + 0.06, y, 1.7), (x1 - 0.06, y, TOP), 0.03, 6)
        rod(K, "frame", (x1 - 0.06, y, 0.4), (x0 + 0.06, y, 1.7), 0.03, 6)
    # ladder rungs up the front, between the front posts
    for i in range(8):
        z = 0.75 + i * (TOP - 0.85) / 7
        rod(K, "frame", (x0 + 0.06, -0.15, z), (x1 - 0.06, -0.15, z), 0.022, 6)
    K.box("deck", x0 + 0.06, x1 - 0.06, -0.15, DEPTH + 0.15, TOP - 0.04, TOP + 0.02)     # platform
    # chassis beam and the tandem wheels
    K.box("pad_dark", x0 + 0.25, x1 - 0.25, -0.1, DEPTH + 0.1, 0.32, 0.45)
    for y in (DEPTH * 0.34, DEPTH * 0.66):
        for x in (x0 + 0.2, x1 - 0.2):
            K.push(Matrix.Translation((x, y, 0.4)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
            K.cyl("tyre", 0, 0, -0.13, 0.13, 0.4, 0.4, 20)
            K.cyl("hub", 0, 0, -0.17, 0.17, 0.22, 0.22, 14)       # 4 cm proud of the tyre
            K.pop()
    # a control box on the platform at one end (the starter's release), as in the photo
    K.box("hub", x0 + 0.2, x1 - 0.2, DEPTH - 0.7, DEPTH - 0.1, TOP + 0.02, TOP + 0.55)
    return K


def lone_partition():
    K = Kit()
    partition(K, 0.0)
    return K


def text_kit(text, mat, size, depth, y):
    """Figures or a wordmark from Blender's own font, standing upright on a board face that looks along -y."""
    K = Kit()
    cu = bpy.data.curves.new("t", type="FONT")
    cu.body, cu.size, cu.extrude = text, size, depth / 2
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.space_character = 1.05
    cu.resolution_u = 3                       # fewer curve steps: the figures are small
    ob = bpy.data.objects.new("t", cu)
    col.objects.link(ob)
    bpy.context.view_layer.update()
    me = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    tmp = bmesh.new(); tmp.from_mesh(me)
    bmesh.ops.transform(tmp, matrix=Matrix.Translation((0, y, 0)) @ Matrix.Rotation(math.pi / 2, 4, "X"), verts=tmp.verts)
    t2 = bpy.data.meshes.new("t2"); tmp.to_mesh(t2); tmp.free()
    K.bm(mat).from_mesh(t2)
    bpy.data.meshes.remove(t2)
    ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
    bpy.data.objects.remove(ob); bpy.data.curves.remove(cu)
    return K


pieces = {}
def save(name, K, clean=True):
    if clean:
        ob, tris = kit_to_object(K, name, MATS, col)
    else:                                     # figures and lettering: Blender's font caps are already clean
        me = bpy.data.meshes.new(name); out = bmesh.new()
        (mat, b), = K.bms.items()
        out.free(); b.to_mesh(me); b.free(); K.bms = {}
        me.materials.append(MATS[mat])
        ob = bpy.data.objects.new(name, me); col.objects.link(ob)
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
    pieces[name] = tris
    return ob


save("stall_bay", bay())
save("stall_partition", lone_partition())
save("stall_tower", tower())
save("stall_gate_left", gate("left"))
save("stall_gate_right", gate("right"))
# figures stand 1 cm proud of the yellow board's face (its face is at y NUM_BOARD.y - 0.025)
fy = NUM_BOARD["y"] - 0.025 - 0.006
for n in range(1, MAX_NUMBER + 1):
    save("stall_num_%d" % n, text_kit(str(n), "figure", 0.3, 0.01, fy), clean=False)
save("stall_plaque", text_kit("THOROUGHBRED", "word", 0.26, 0.012, FASCIA["y"] - 0.04 - 0.007), clean=False)

for n, t in pieces.items():
    if not n.startswith("stall_num_"):
        print("  %-18s %6d triangles" % (n, t), flush=True)
print("  numbers 1-%d       %6d triangles in all" % (MAX_NUMBER, sum(t for n, t in pieces.items() if n.startswith("stall_num_"))), flush=True)

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
for ob in col.objects:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT_DIR, "starting_stalls.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
spec = {
    "_about": "The starting stalls kit (tools/blender/build_stalls.py). Sizes in metres, in the glTF's axes: x along the "
              "row (stall numbers rise with x), y up, the horses break out towards +z. Every node's origin is on the "
              "front line at ground level. A unit is: stall_tower, then its bays one after another (stall_bay from x 0 "
              "to pitch, partition on its left edge), closed by stall_partition at the last bay's right edge, then the "
              "next stall_tower. Gates hang on the bay's posts: stall_gate_left at x partition/2 from the bay's left "
              "edge, stall_gate_right at pitch - partition/2; open = left turns -openDegrees about y, right +openDegrees.",
    "file": "assets/models/course/starting_stalls.glb",
    "pitch": PITCH, "depth": DEPTH, "towerWidth": TOWER, "partition": PART, "height": TOP + 0.95,
    "gateHinge": {"left": PART / 2, "right": PITCH - PART / 2},
    "openDegrees": 100,
    "numberBoard": {"centre": [PITCH / 2, (NUM_BOARD["z0"] + NUM_BOARD["z1"]) / 2, 0.0], "maxNumber": MAX_NUMBER},
    "plaque": {"height": (FASCIA["z0"] + FASCIA["z1"]) / 2},
    "horseStandsAt": {"behindFront": 1.55, "note": "where a horse's middle stands, metres behind the front line (its nose just behind the gates)"},
    "triangles": pieces,
}
json.dump(spec, open(os.path.join(OUT_DIR, "starting_stalls_kit.json"), "w"), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets/models/master/starting_stalls.blend"), compress=True)
print("written assets/models/course/starting_stalls.glb", flush=True)
