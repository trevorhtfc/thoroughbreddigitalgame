"""Export the soft look's trees for the race view (owner's pick in the tree workshop, 11 Nov 2026: tree 2, "loose
clumps", in its lightest weight; "we rarely see trunks so they could become much more simple... typically you have a
hedge or dyke at low level and then trees behind and above").

    python3 -c "exec(open('tools/blender/export_soft_trees.py').read())"
    python3 tools/web/glb_to_web.py assets/models/trees/trees_soft.glb race-view/assets/trees trees_soft

Writes assets/models/trees/trees_soft.glb with the same names as the leafy kit, so every course's planting picks the
trees up as it stands: <name>_crown (about 180 clumps of foliage, each a flat card carrying a cut-out picture of
leaves; every card is there twice, back to back, so it is seen from both sides and lit the same from both),
<name>_crown_far (about 90 larger clumps, for the belts) and <name>_trunk (a five-sided trunk and its main boughs as
three-sided sticks; no smaller branches). Scaled so an oak's top stands at 11 units, as the leafy kit's does.
Vertex colours: a grey tone per clump on the crowns (the game's shader lays the colours on by height), bark brown on
the wood. The cards' normals are those of a rounded crown, so a tree shades as a whole. The cut-out picture is copied
to race-view/assets/trees/leaf_clumps.png.
"""
import os, shutil
_src = open("tools/blender/tree_workshop.py").read()
os.environ.setdefault("OUT", "/tmp/soft_trees_work")
exec(compile(_src[:_src.index("def plane(")], "tree_workshop", "exec"))

VARIANTS = {"oak_a": (0, "std"), "oak_b": (1, "std"), "oak_c": (2, "std"), "wide_a": (3, "wide"), "wide_b": (4, "wide"), "poplar_a": (5, "tall")}
TOP = {"std": 11.0, "wide": 10.4, "tall": 13.8}
BARKC = lin("#6d5f50")
out_objs = []


def card_mesh(name, src, k):
    """The cards of a crown, scaled, each doubled back to back, with a tone as vertex colour."""
    n = len(src.vertices); co = [v.co * k for v in src.vertices]
    uv = [None] * n; nr = [None] * n; cn = src.corner_normals
    for li, loop in enumerate(src.loops): uv[loop.vertex_index] = tuple(src.uv_layers[0].data[li].uv); nr[loop.vertex_index] = tuple(cn[li].vector)
    tone = [d.value for d in src.attributes["tone"].data]
    faces = [tuple(p.vertices) for p in src.polygons]
    faces += [tuple(n + i for i in reversed(f)) for f in faces]
    me = bpy.data.meshes.new(name); me.from_pydata(co + co, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops): uvl.data[li].uv = uv[loop.vertex_index % n]
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i in range(2 * n): t = 0.3 * (0.8 + 0.4 * tone[i % n]); col.data[i].color = (t, t, t, 1.0)
    me.color_attributes.active_color = col
    for p in me.polygons: p.use_smooth = True
    me.normals_split_custom_set_from_vertices(nr + nr)
    return me


for name, (seed, shape) in VARIANTS.items():
    crown, wood = real_tree(seed, "fluffy_xl", shape); far, _ = real_tree(seed, "fluffy_far", shape)
    k = TOP[shape] / max(v.co.z for v in crown.data.vertices)
    wm = wood.data.copy(); wm.transform(Matrix.Diagonal((k, k, k, 1)))
    wc = wm.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for d in wc.data: d.color = BARKC
    wm.color_attributes.active_color = wc
    for p in wm.polygons: p.use_smooth = True
    for part, me in (("_crown", card_mesh(name + "_crown", crown.data, k)), ("_crown_far", card_mesh(name + "_crown_far", far.data, k)), ("_trunk", wm)):
        me.materials.clear(); o = bpy.data.objects.new(name + part, me); scene.collection.objects.link(o); out_objs.append(o)
        me.calc_loop_triangles(); print(name + part, len(me.loop_triangles), "triangles", flush=True)

bpy.ops.object.select_all(action="DESELECT")
for o in out_objs: o.select_set(True)
OUTDIR2 = rp("assets/models/trees")
bpy.ops.export_scene.gltf(filepath=os.path.join(OUTDIR2, "trees_soft.glb"), export_format="GLB", use_selection=True, export_yup=True, export_normals=True,
                          export_vertex_color="ACTIVE", export_texcoords=True, export_apply=False, export_animations=False, export_materials="NONE")
shutil.copy(os.path.join(OUTDIR, "fluffy_atlas.png"), rp("race-view/assets/trees/leaf_clumps.png"))
print("exported trees_soft.glb", round(os.path.getsize(os.path.join(OUTDIR2, "trees_soft.glb")) / 1024), "KB", flush=True)
