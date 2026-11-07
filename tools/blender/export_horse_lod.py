"""A light version of the race horse (v1) for when a horse is small on screen (owner, 7 Nov 2026: make the race view
run smoothly without losing quality).

    python -c "exec(open('tools/blender/export_horse_lod.py').read())"

Reads assets/models/racehorse_rigged.glb, decimates its mesh (horse and rider, both materials) to about RATIO of its
triangles, keeping the skin weights, UVs and the same skeleton, and writes assets/models/racehorse_lod.glb: the light
mesh and the armature only (no animations, no images: the race view binds it to each runner's own skeleton and uses
the runner's own materials). The exporter lists the same 58 joints in a different order, so the race view matches
them by name when it binds the light mesh (horseLod() in race-view/final-furlong.html).
"""
import os, json, struct
import bpy

REPO = os.path.abspath(".")
SRC = os.path.join(REPO, "assets/models/racehorse_rigged.glb")
OUT = os.path.join(REPO, "assets/models/racehorse_lod.glb")
RATIO = float(os.environ.get("RATIO", "0.3"))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for o in meshes:
    n0 = sum(len(p.vertices) - 2 for p in o.data.polygons)
    d = o.modifiers.new("lod", "DECIMATE"); d.decimate_type = "COLLAPSE"; d.ratio = RATIO; d.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = o
    # the decimate must come before the armature modifier to be applied on the rest pose
    while o.modifiers.find("lod") > 0:
        bpy.ops.object.modifier_move_up(modifier="lod")
    bpy.ops.object.modifier_apply(modifier="lod")
    n1 = sum(len(p.vertices) - 2 for p in o.data.polygons)
    print(f"{o.name}: {n0} -> {n1} triangles", flush=True)
    o.name = "horse_lod"
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
bpy.ops.object.select_all(action="DESELECT")
for o in meshes + [arm]: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", use_selection=True, export_animations=False, export_skins=True,
                          export_image_format="NONE", export_materials="EXPORT", export_yup=True)


def joints(path):
    b = open(path, "rb").read(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n])
    return [j["nodes"][i]["name"] for i in j["skins"][0]["joints"]]
same = sorted(joints(SRC)) == sorted(joints(OUT))
print("same joints:", same, len(joints(OUT)), flush=True)
if not same: raise SystemExit("the joints differ: the race view can't share the skeleton")
