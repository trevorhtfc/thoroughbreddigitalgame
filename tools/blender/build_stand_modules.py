"""Build the grandstand module kit, and assemble Ascot's main stand from it.

    python -c "exec(open('tools/blender/build_stand_modules.py').read())"

Reads  assets/models/architecture/stand_modules.json       the module catalogue (bays, depths, tiers)
       courses/ascot-grandstand-assembly.json               the order Ascot's stand is assembled in
       courses/ascot.json                                   where the stand stands (front line)
Writes assets/models/architecture/stand_modules.glb         one node per module, to snap together in any engine
       assets/models/architecture/ascot_main_stand.glb      Ascot's assembled stand, one mesh per material
       assets/models/architecture/ascot_main_stand_far.glb  the same stand, light distant version for the web
                                                            (fine detail drawn simply; same outline and placing)
       assets/models/architecture/ascot_main_stand_crowd_areas.json
       assets/models/master/stand_modules.blend             Blender master

Where a module butts against a neighbour (a "party" end), its end windows are left off, so no dark
slots show where a taller block stands above a lower one.

Every module is a whole number of 3.5 m bays, sits on the same 3 m podium with 3.5 m storeys and has its
front on the shared front line, so modules butt together end to end. Runs of the same repeatable module
(veranda wings) are built as one run in the assembly, so their roof carries on unbroken.

Building coordinates (Blender): x along the front, left to right as seen from the track; y into the
building (front faces -y); z up.

stand_modules.glb: each module's origin is the LEFT end of its front at ground level; in glTF (y up)
the front faces +z and the module runs along +x. End pavilions are built with their dressed end on the
right; mirror in x for a left-hand end.

ascot_main_stand.glb is already in WORLD axes (courses/ascot.json): x east, y up, z south, origin at
the clock tower on the front line. Place it at (0, 0, grandstand.frontLine) with no turn.
"""
import json, math, os
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)

CAT = json.load(open(rp("assets/models/architecture/stand_modules.json")))
ASM = json.load(open(rp("courses/ascot-grandstand-assembly.json")))
COURSE = json.load(open(rp("courses/ascot.json")))
GS = json.load(open(rp("assets/models/architecture/victorian_grandstand_layout.json")))
S, P, BAY = CAT["storey"], CAT["podium"], CAT["bay"]
COL = GS["colours"]
MODS = CAT["modules"]

bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(rp("tools/blender/kit.py")).read())

MATS = {k: material("gs_" + k, v, rough={"glass": 0.25, "gilt": 0.4, "roof": 0.75}.get(k, 0.85),
                    metal={"gilt": 0.3}.get(k, 0.0)) for k, v in COL.items()}

K = Kit()
CROWD = []


def stand_area(x0, x1, y0, y1, z, kind):
    a = K.M @ Vector((x0, y0, z)); b = K.M @ Vector((x1, y1, z))
    CROWD.append({"x0": round(min(a.x, b.x), 2), "x1": round(max(a.x, b.x), 2),
                  "y0": round(min(a.y, b.y), 2), "y1": round(max(a.y, b.y), 2), "z": round(a.z, 2), "kind": kind})


exec(open(rp("tools/blender/stand_pieces.py")).read())


# ------------------------------------------------------------------ new pieces for the kit
def end_pavilion(x0, x1, D, tiers):
    """Two-tier veranda pavilion with a wraparound balcony on its dressed (right) end, hipped roof and
    a small square cupola. From the end pavilions of the 300 m sheet."""
    veranda({"x0": x0, "x1": x1, "tiers": tiers, "depth": D, "setback": 0.0, "roof": "none"})
    zt = P + tiers * S + 0.6
    xo = x1 + 1.6                                                     # wraparound gallery on the end
    for k in range(tiers):
        z = P + k * S
        hh = S + (0.6 if k == tiers - 1 else 0)
        K.box("trim", x1, xo, -0.25, D, z - 0.3, z)
        n = max(2, round(D / BAY))
        for i in range(n + 1):
            K.cyl("trim", xo - 0.35, D * i / n, z, z + hh, 0.15, 0.12)
        K.box("trim", xo - 0.5, xo - 0.2, 0, D, z + hh - 0.3, z + hh)
        K.balustrade(0.0, D, xo - 0.35, z, axis="y", piers=False)
        stand_area(x1 + 0.2, xo - 0.6, 0.6, D - 0.6, z, "veranda")
    K.box("podium", x1, xo, 0, D, 0, P)
    K.hip_roof(x0, xo, -0.2, D, zt - 0.6, 2.6, 0.8)
    cx, cy, cw = (x0 + xo) / 2, D / 2, 3.2                            # cupola
    zc = zt - 0.6 + 2.6 - 0.4
    K.box("wall", cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zc, zc + 1.7)
    for rot in range(4):
        K.push(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rot * math.pi / 2, 4, "Z") @ Matrix.Translation((-cx, -cy, 0)))
        for j in (-0.8, 0.0, 0.8):
            K.box("glass", cx + j - 0.28, cx + j + 0.28, cy - cw / 2 - 0.05, cy - cw / 2 + 0.05, zc + 0.3, zc + 1.4)
        K.pop()
    K.cornice(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zc + 1.7, 0.25, 0.25)
    K.hip_roof(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zc + 1.95, 1.2, 0.35)
    K.cyl("gilt", cx, cy, zc + 3.1, zc + 3.9, 0.04, 0.01, 6)


def stair_bay(x0, x1, D, party=()):
    """A narrow stair hall between wings, with a broad flight from the lawn in front."""
    block({"x0": x0, "x1": x1, "storeys": 3, "depth": D, "party": party})
    steps({"x": (x0 + x1) / 2, "width": x1 - x0 - 0.9, "run": MODS["stair_bay"]["frontProjection"]})


def grand_pavilion(x0, x1, D, party=()):
    pavilion({"x0": x0, "x1": x1, "storeys": 3, "storey": 4.0, "depth": D, "pitch_deg": 26, "party": party})
    H = P + 3 * 4.0
    rise = (D / 2 + 0.8) * math.tan(math.radians(26))
    for xc in (x0 + (x1 - x0) * 0.25, x0 + (x1 - x0) * 0.75):           # dormer gables to the front
        K.prism_x("wall", xc - 1.6, xc + 1.6, [(-0.2, H), (3.2, H), (3.2, H + 2.6), (1.5, H + 3.4), (-0.2, H + 2.6)])
        K.window(xc, -0.2, H + 0.4, 1.6, 1.9)


VER = {"porch": dict(tiers=1, depth=9.0, setback=0.0, roof="hip"),
       "veranda_low": dict(tiers=3, depth=18.0, setback=2.2, roof="flat"),
       "veranda_wing": dict(tiers=4, depth=20.0, setback=2.2, roof="hip"),
       "link": dict(tiers=3, depth=18.0, setback=1.2, roof="flat")}


def build_module(name, x0, length, party=()):
    """Build one module (or a run of one repeatable module) with its front-left corner at x0.
    party: which ends ('left', 'right') butt against a neighbour, so their end windows are left off."""
    m = MODS[name]; x1 = x0 + length
    if name in VER:
        veranda(dict(VER[name], x0=x0, x1=x1))
    elif name == "veranda_wing_raised":
        veranda(dict(VER["veranda_wing"], x0=x0, x1=x1, raised_from=x0))
    elif name == "end_pavilion":
        end_pavilion(x0, x1 - 1.6, m["depth"], m["tiers"])            # the end gallery fills the last 1.6 m
    elif name == "stair_bay":
        stair_bay(x0, x1, m["depth"], party)
    elif name == "clock_centre":
        block({"x0": x0, "x1": x0 + 21.0, "storeys": 4, "depth": 22.0, "balconies": True, "chimney": x0 + 10.0,
               "party": ("right",) + tuple(p for p in party if p == "left")})
        ironwork({"x0": x0 + 21.0, "x1": x1, "levels": 3, "depth": 20.0})
        tower({"x": x0 + m["towerFromLeft"], "y": 6.0, "width": m["towerWidth"], "base_z": 17.0, "top_z": 24.5})
    elif name == "ironwork_bay":
        ironwork({"x0": x0, "x1": x1, "levels": 3, "depth": m["depth"]})
    elif name == "window_block":
        block({"x0": x0, "x1": x1, "storeys": 4, "depth": m["depth"], "party": party})
    elif name == "three_storey_block":
        block({"x0": x0, "x1": x1, "storeys": 3, "depth": m["depth"], "roof_room": True, "party": party})
    elif name == "pavilion":
        pavilion({"x0": x0, "x1": x1, "storeys": 2, "storey": 4.6, "depth": m["depth"], "pitch_deg": 24, "party": party})
    elif name == "grand_pavilion":
        grand_pavilion(x0, x1, m["depth"], party)
    else:
        raise KeyError(name)


def build_placed(name, x0, length, mirror, party=()):
    if mirror:                                  # mirrored: the module's own left end is on the right
        swap = {"left": "right", "right": "left"}
        K.push(Matrix.Translation((x0 + length, 0, 0)) @ Matrix.Diagonal((-1, 1, 1, 1)))
        build_module(name, 0.0, length, tuple(swap[p] for p in party))
        K.pop()
    else:
        build_module(name, x0, length, party)


# ------------------------------------------------------------------ 1) the kit: one node per module
kit_coll = bpy.data.collections.new("stand_modules")
bpy.context.scene.collection.children.link(kit_coll)
x = 0.0
kit_report = []
for name, m in MODS.items():
    Lm = m["bays"] * BAY
    build_module(name, 0.0, Lm)
    ob, tris = kit_to_object(K, "module_" + name, MATS, kit_coll)
    ob.location.x = x
    kit_report.append((name, m["bays"], tris))
    x += Lm + 12.0
CROWD.clear()
print("kit:", ", ".join(f"{n} {b}b {t}t" for n, b, t in kit_report), flush=True)

# ------------------------------------------------------------------ 2) Ascot's stand, assembled
runs = []                                   # merge back-to-back repeats of a repeatable module into one run
for item in ASM["order"]:
    name = item["module"]; n = item.get("repeat", 1); mir = item.get("mirror", False)
    if runs and runs[-1][0] == name and MODS[name].get("repeatable") and not mir and not runs[-1][2]:
        runs[-1][1] += n
    else:
        runs.append([name, n, mir])
def assemble(far, coll_name, mesh_prefix):
    """Assemble Ascot's stand from the runs, in world axes, one mesh per material."""
    global CROWD
    K.far = far
    cum, tower_c = 0.0, None
    for i, (name, n, mir) in enumerate(runs):
        Lm = MODS[name]["bays"] * BAY * n
        if name == ASM["anchor"]["module"]:
            tower_c = cum + MODS[name]["towerFromLeft"]
        party = tuple(p for p, on in (("left", i > 0), ("right", i < len(runs) - 1)) if on)
        build_placed(name, cum, Lm, mir, party)
        cum += Lm
    assert abs(cum - COURSE["grandstand"]["length"]) < 0.01, (cum, COURSE["grandstand"]["length"])
    stand_area(0.3, cum - 0.3, 0.0, 0.0, 0, "lawn_front_line")
    coll = bpy.data.collections.new(coll_name)
    bpy.context.scene.collection.children.link(coll)
    # world axes: rotate 180 degrees about z so the front faces north and the left end (as seen from the
    # track) lies east; then the clock tower's front sits at the origin.
    TO_WORLD = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation((-tower_c, 0, 0))
    tris = 0
    for name, bm in list(K.bms.items()):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
        bmesh.ops.transform(bm, matrix=TO_WORLD, verts=bm.verts)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        me = bpy.data.meshes.new(mesh_prefix + name)
        bm.to_mesh(me); bm.free()
        me.materials.append(MATS[name])
        ob = bpy.data.objects.new(mesh_prefix + name, me)
        coll.objects.link(ob)
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
    K.bms = {}
    K.far = False
    print("%s: %.1f m, tower %.1f m from the east end, %d triangles, %d meshes" % (coll_name, cum, tower_c, tris, len(coll.objects)), flush=True)
    return coll, tower_c


# the light distant version first (its crowd areas are dropped), then the full one
far_coll, _ = assemble(True, "ascot_main_stand_far", "ascot_stand_far_")
CROWD.clear()
stand_coll, tower_c = assemble(False, "ascot_main_stand", "ascot_stand_")

# crowd areas in world axes (x east, y up = floor height, z south), relative to the stand's origin
areas = []
for a in CROWD:
    xs = sorted([-(a["x0"] - tower_c), -(a["x1"] - tower_c)])
    ys = sorted([a["y0"], a["y1"]])          # glTF z = Blender y after the half turn
    areas.append({"x0": round(xs[0], 2), "x1": round(xs[1], 2), "floor": a["z"],
                  "z0": round(ys[0], 2), "z1": round(ys[1], 2), "kind": a["kind"]})
json.dump({"_about": "Where spectators can stand on Ascot's main stand, in world axes relative to the stand's origin (the clock tower on the front line): x east, z south, floor = height above the lawn. Add grandstand.frontLine from courses/ascot.json to z for course positions.",
           "areas": areas}, open(rp("assets/models/architecture/ascot_main_stand_crowd_areas.json"), "w"), indent=1)


# ------------------------------------------------------------------ export
def export(coll, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_animations=False)
    print("exported", path, flush=True)


export(kit_coll, rp("assets/models/architecture/stand_modules.glb"))
export(stand_coll, rp("assets/models/architecture/ascot_main_stand.glb"))
export(far_coll, rp("assets/models/architecture/ascot_main_stand_far.glb"))
os.makedirs(rp("assets/models/master"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=rp("assets/models/master/stand_modules.blend"), compress=True)
