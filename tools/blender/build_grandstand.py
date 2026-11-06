"""Build the cream Victorian grandstand from scripted, snap-together pieces.

    python -c "exec(open('tools/blender/build_grandstand.py').read())"

Reads  assets/models/architecture/victorian_grandstand_layout.json
Writes assets/models/architecture/victorian_grandstand.glb      (one mesh per material: few draw calls)
       assets/models/architecture/victorian_grandstand_crowd_areas.json  (where spectators can stand)
       assets/models/architecture/crowd_people.glb               (simple spectator figures to instance)
       assets/models/master/victorian_grandstand.blend           (Blender master)

The FRONT elevation of reference/architecture/victorian-grandstand-sheet.png is the master.
Sizes are realistic, not the sheet's scale bar: 3.5 m storeys, a stand of about 124 m, a clock tower
of about 28 m. The pieces are chunkier and simpler than the sheet, with the signature features
exaggerated: the clock, the ironwork lace and the stepped verandas.

Pieces (Townscaper-style kit, everything on a 3.5 m bay grid):
  veranda tier   floor slab, columns, balustrade, glazed back wall; tiers step back as they rise
  block storey   windowed wall with a shallow balcony and balustrade in front
  ironwork level open gallery with arched iron lace, roundel frieze and roundel balustrade
  clock tower    pilastered shaft, four big clock faces, cornice, balustraded top, urns, cupola, finial
  pavilion       glazed storeys with balconies under a pitched slate roof and roof lantern
  steps          flights from the lawn up to the terrace, with cheek walls, handrails and newels

Blender coordinates while building: x along the front (left to right as seen from the lawn),
y = into the building (front faces -y), z = up. Origin: ground level, middle of the front.
In the .glb (glTF, y up) the front faces +z.
"""
import json, math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
LAYOUT = json.load(open(os.path.join(REPO, "assets/models/architecture/victorian_grandstand_layout.json")))
OUT_DIR = os.path.join(REPO, "assets/models/architecture")
S, P, BAY = LAYOUT["storey"], LAYOUT["podium"], LAYOUT["bay"]
COL = LAYOUT["colours"]

bpy.ops.wm.read_factory_settings(use_empty=True)


exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())


MATS = {k: material("gs_" + k, v, rough={"glass": 0.25, "gilt": 0.4, "roof": 0.75}.get(k, 0.85),
                    metal={"gilt": 0.3}.get(k, 0.0)) for k, v in COL.items()}


K = Kit()
L = max(s.get("x1", 0) for s in LAYOUT["segments"])
K.push(Matrix.Translation((-L / 2, 0, 0)))          # origin at the middle of the front
CROWD = []          # standing areas: x0, x1, y0, y1, z (Blender coords, local to the stand)


def stand_area(x0, x1, y0, y1, z, kind):
    CROWD.append({"x0": round(x0 - L / 2, 2), "x1": round(x1 - L / 2, 2), "y0": round(y0, 2), "y1": round(y1, 2),
                  "z": round(z, 2), "kind": kind})


exec(open(os.path.join(REPO, "tools/blender/stand_pieces.py")).read())



BUILD = {"veranda": veranda, "block": block, "iron": ironwork, "tower": tower, "pavilion": pavilion}
for seg in LAYOUT["segments"]:
    BUILD[seg["kind"]](seg)
for st in LAYOUT["steps"]:
    steps(st)
stand_area(0.3, L - 0.3, -0.0, 0.0, 0, "lawn_front_line")     # front line of the stand at ground level
K.pop()

# ------------------------------------------------------------------ assemble: one mesh per material
stand = bpy.data.collections.new("victorian_grandstand")
bpy.context.scene.collection.children.link(stand)
tris = 0
for name, bm in K.bms.items():
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("grandstand_" + name)
    bm.to_mesh(me); bm.free()
    me.materials.append(MATS[name])
    ob = bpy.data.objects.new("grandstand_" + name, me)
    stand.objects.link(ob)
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
print("grandstand: %d meshes, %d triangles, %.1f m long" % (len(K.bms), tris, L), flush=True)

# ------------------------------------------------------------------ crowd figures
crowd = bpy.data.collections.new("crowd_people")
bpy.context.scene.collection.children.link(crowd)
CM = {"clothes": material("crowd_clothes", "#3a3f4a", 0.9), "skin": material("crowd_skin", "#e2b896", 0.7),
      "hat": material("crowd_hat", "#1e1f24", 0.6)}


def person(name, kind):
    k = Kit()
    if kind in ("gent", "gent_tophat"):
        k.cyl("clothes", 0, 0, 0.0, 0.85, 0.13, 0.17, 7)            # legs
        k.cyl("clothes", 0, 0, 0.85, 1.48, 0.2, 0.24, 7)            # coat
        k.sphere("clothes", 0, 0, 1.46, 0.23, 1, 0.45)              # shoulders
    else:
        k.cyl("clothes", 0, 0, 0.0, 1.1, 0.33, 0.17, 8)             # dress
        k.cyl("clothes", 0, 0, 1.1, 1.42, 0.16, 0.2, 7)
        k.sphere("clothes", 0, 0, 1.41, 0.2, 1, 0.45)
    k.cyl("skin", 0, 0, 1.45, 1.56, 0.06, 0.06, 6)
    k.sphere("skin", 0, 0, 1.64, 0.115, 1, 1.1)
    if kind == "gent_tophat":
        k.cyl("hat", 0, 0, 1.72, 1.74, 0.17, 0.17, 10)
        k.cyl("hat", 0, 0, 1.74, 1.93, 0.105, 0.11, 10)
    elif kind == "gent":
        k.cyl("hat", 0, 0, 1.71, 1.73, 0.16, 0.16, 10)
        k.cyl("hat", 0, 0, 1.73, 1.8, 0.11, 0.1, 10)
    else:
        k.cyl("hat", 0, 0, 1.69, 1.71, 0.27, 0.27, 12)
        k.sphere("hat", 0, 0, 1.72, 0.12, 1, 0.7)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for mname, b in k.bms.items():
        idx = list(CM).index(mname)
        tmp = bpy.data.meshes.new("tmp"); b.to_mesh(tmp); b.free()
        bm.from_mesh(tmp)
        for f in bm.faces:
            if f.material_index == 0 and not f.tag:
                f.material_index = idx; f.tag = True
        bpy.data.meshes.remove(tmp)
    bm.to_mesh(me); bm.free()
    for m in CM.values():
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    crowd.objects.link(ob)
    return ob


for i, kind in enumerate(("gent_tophat", "gent", "lady", "lady_b")):
    o = person("person_" + kind, kind if kind != "lady_b" else "lady")
    o.location.x = i * 1.0

# ------------------------------------------------------------------ save
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(REPO, "assets/models/master"), exist_ok=True)
json.dump({"_about": "Where spectators can stand on the Victorian grandstand. Blender coordinates, metres, local to the stand: x along the front, y into the stand (front faces -y), z = floor height. In the .glb (y up) that is x = x, y = z, z = -y.",
           "areas": CROWD}, open(os.path.join(OUT_DIR, "victorian_grandstand_crowd_areas.json"), "w"), indent=1)


def export(coll, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_animations=False)
    print("exported", path, flush=True)


export(stand, os.path.join(OUT_DIR, "victorian_grandstand.glb"))
export(crowd, os.path.join(OUT_DIR, "crowd_people.glb"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets/models/master/victorian_grandstand.blend"), compress=True)
