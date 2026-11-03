"""Export the stylised look test's leafy trees for the real-time race views.

    python -c "exec(open('tools/blender/export_trees.py').read())"

Builds the trees exactly as tools/blender/stylised_look_test.py does (crowns of merged leafy clumps),
then makes a lighter copy of each crown, keeps its soft-ball shading (normals bent out from the
crown's centre) and stores the stills' colouring (dark base to sunlit top, with a little mottling)
as vertex colours, so any engine lit by the same sun and sky draws the same trees.

Writes assets/models/trees/trees.glb: for each variant <name>_crown and <name>_trunk
(oak_a, oak_b, oak_c, wide_a, wide_b, poplar_a, bush_a, bush_b), origin at the foot of the trunk, plus
<name>_crown_far: the same crown much lighter (about a fifth of the triangles, same colours and
shading) for trees seen from a long way off, such as the planting belts round the far rails.
"""
import os, sys, math
import bpy
from mathutils import Vector

os.environ["SHOT"] = "__none__"
sys.argv = [sys.argv[0], "/tmp/_trees_unused", "1"]
exec(open(os.path.join(os.path.abspath("."), "tools/blender/stylised_look_test.py")).read())

import mathutils.noise as mnoise   # after the exec: the look test names a node "noise"
OUTDIR = os.path.join(REPO, "assets/models/trees")
os.makedirs(OUTDIR, exist_ok=True)
SHAPE = {"oak": ((0, 0, 6.4), 4.6, 0.95), "wide": ((0, 0, 6.2), 5.4, 0.8), "poplar": ((0, 0, 8.0), 2.7, 2.4), "bush": ((0, 0, 1.6), 2.4, 0.75)}
SEEDS = {"oak_a": 1, "oak_b": 2, "wide_a": 3, "oak_c": 4, "poplar_a": 5, "wide_b": 6, "bush_a": 7, "bush_b": 8}
HUES = [("#1c4a2a", "#3f8034", "#86bd4a", "#d6e07a"), ("#1d4834", "#367a48", "#74b25c", "#bfe08a"),
        ("#2a4a20", "#56862e", "#a2c048", "#e6dc72")]
TARGET_TRIS = {"oak": 1400, "wide": 1400, "poplar": 900, "bush": 500}
FAR_TRIS = {"oak": 220, "wide": 220, "poplar": 150, "bush": 100}


def ramp4(stops, t):
    pos = (0.0, 0.35, 0.75, 1.0)
    cols = [srgb(c)[:3] for c in stops]
    t = min(1.0, max(0.0, t))
    for i in range(3):
        if t <= pos[i + 1]:
            k = (t - pos[i]) / (pos[i + 1] - pos[i])
            return tuple(cols[i][j] + (cols[i + 1][j] - cols[i][j]) * k for j in range(3))
    return cols[-1]


lib = bpy.data.collections.new("web_trees")
scene.collection.children.link(lib)
for name, seed in SEEDS.items():
    kind = name.split("_")[0]
    C, Rr, stretch = SHAPE[kind]
    C = Vector(C)
    col = bpy.data.collections[name]
    crown_src = next(o for o in col.objects if o.name.endswith("_crown"))
    crown_src.name = name + "_source_crown"             # free the plain name for the exported copy
    crown = crown_src.copy(); crown.data = crown_src.data.copy(); crown.name = name + "_crown"
    lib.objects.link(crown)
    ratio = min(1.0, TARGET_TRIS[kind] / max(1, len(crown.data.polygons) * 2))
    dm = crown.modifiers.new("lighter", "DECIMATE"); dm.ratio = ratio
    bpy.context.view_layer.objects.active = crown
    crown.select_set(True)
    bpy.ops.object.modifier_apply(modifier="lighter")
    crown.select_set(False)
    me = crown.data
    for p in me.polygons:
        p.use_smooth = True
    centre = C - Vector((0, 0, Rr * 0.25))
    nrm = []
    for v in me.vertices:                         # soft-ball shading, as in the stills
        s = v.co - centre; s.z /= max(0.6, stretch); s.normalize()
        k = v.normal * 0.5 + s * 0.5; k.normalize()
        nrm.append(k)
    me.normals_split_custom_set_from_vertices(nrm)
    attr = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    hue = HUES[seed % 3]
    for i, v in enumerate(me.vertices):
        n = 0.5 + 0.5 * mnoise.noise(v.co * 0.9)
        t = (v.co.z - 1.5) / 10.0 + n * 0.35 - 0.17
        attr.data[i].color = ramp4(hue, t) + (1.0,)
    me.color_attributes.active_color = attr
    me.materials.clear(); me.materials.append(bpy.data.materials.get("leaves%d" % (seed % 3)))
    # the distant version: decimate the finished crown (colours ride along), then bend its normals the same way
    far = crown.copy(); far.data = me.copy(); far.name = name + "_crown_far"
    lib.objects.link(far)
    dm = far.modifiers.new("far", "DECIMATE"); dm.ratio = min(1.0, FAR_TRIS[kind] / max(1, sum(len(p.vertices) - 2 for p in me.polygons)))
    bpy.context.view_layer.objects.active = far
    far.select_set(True)
    bpy.ops.object.modifier_apply(modifier="far")
    far.select_set(False)
    fn = []
    for v in far.data.vertices:
        sv = v.co - centre; sv.z /= max(0.6, stretch); sv.normalize()
        k = v.normal * 0.4 + sv * 0.6; k.normalize()
        fn.append(k)
    far.data.normals_split_custom_set_from_vertices(fn)
    trunk_src = next((o for o in col.objects if o.name.endswith("_trunk")), None)
    if trunk_src:
        trunk_src.name = name + "_source_trunk"
        trunk = trunk_src.copy(); trunk.data = trunk_src.data.copy(); trunk.name = name + "_trunk"
        lib.objects.link(trunk)
        ta = trunk.data.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        for d in ta.data:
            d.color = srgb("#6b5442")
        trunk.data.color_attributes.active_color = ta
    print("%-9s crown %5d triangles" % (name, sum(len(p.vertices) - 2 for p in me.polygons)), flush=True)

bpy.ops.object.select_all(action="DESELECT")
for o in lib.objects:
    o.select_set(True)
    o.location = (0, 0, 0)
bpy.ops.export_scene.gltf(filepath=os.path.join(OUTDIR, "trees.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_normals=True, export_vertex_color="ACTIVE", export_texcoords=False,
                          export_apply=False, export_animations=False, export_materials="NONE")
print("exported trees.glb", flush=True)
