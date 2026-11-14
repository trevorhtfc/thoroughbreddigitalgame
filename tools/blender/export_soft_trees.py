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

The low greenery, in the same foliage (owner, 12 Nov: "all the greenery should be of the same style"):
thicket_a, thicket_b    the understorey of the belts, one under each tree: two dozen of the same clumps standing as a
                        low bank of bushes about 6 high and 9 across (<name>_leaves), over a plain dark mound that
                        stops the eye seeing through at ground level (<name>_core);
tuft_a, tuft_b, tuft_c  three clumps together, about 2 across: the game stands these all over the belt hedge, which
                        becomes its dark heart. Modelled 5 units up (the game sets them 5 lower), so the game's
                        grading by height gives the hedge the green of foliage at that height, not the darkest foot.
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


# ---------------------------------------------------------------- the low greenery
def clumps_mesh(name, cards, centre, lift=0.0):
    """Cards (centre, size, facing) as a mesh like a crown's: uv, a tone each, normals those of a rounded mass."""
    r = random.Random(len(cards) * 31 + 7); verts, faces, uvs, tones, nrm = [], [], [], [], []
    for c, size, n in cards:
        tg = n.cross(Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1)))).normalized(); bt = n.cross(tg)
        i0 = len(verts); h = size * 0.5; verts += [c - tg * h - bt * h, c + tg * h - bt * h, c + tg * h + bt * h, c - tg * h + bt * h]; faces.append((i0, i0 + 1, i0 + 2, i0 + 3))
        tx, ty = r.choice((0, 1)), r.choice((0, 1)); uvs += [(tx * 0.5, ty * 0.5), (tx * 0.5 + 0.5, ty * 0.5), (tx * 0.5 + 0.5, ty * 0.5 + 0.5), (tx * 0.5, ty * 0.5 + 0.5)]
        tones += [r.random()] * 4
        out = Vector((c.x - centre.x, c.y - centre.y, (c.z - centre.z) * 0.5)); out = out.normalized() if out.length > 1e-3 else Vector((0, 0, 1))
        nrm += [(out * 0.55 + Vector((0, 0, 0.4)) + n * 0.2).normalized()] * 4
    me = bpy.data.meshes.new(name + "_src"); me.from_pydata([v + Vector((0, 0, lift)) for v in verts], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for li, loop in enumerate(me.loops): uvl.data[li].uv = uvs[loop.vertex_index]
    at_ = me.attributes.new("tone", "FLOAT", "POINT"); at_.data.foreach_set("value", tones)
    for pl in me.polygons: pl.use_smooth = True
    me.normals_split_custom_set_from_vertices([tuple(v) for v in nrm])
    return card_mesh(name, me, 1.0)


def facing(r, out=None):
    """Which way a clump lies: one in three turned out to whoever looks at the bush, the rest every way."""
    base = Vector((out.x, out.y, 0.3)) if out is not None else Vector((r.uniform(-1, 1), r.uniform(-1, 1), abs(r.uniform(-1, 1)) + 0.3))
    return (base + Vector((r.uniform(-1, 1), r.uniform(-1, 1), r.uniform(-1, 1))) * 0.3).normalized()


def thicket(name, seed):
    """A bank of bushes: six or seven stems of different heights standing together, each a few clumps."""
    r = random.Random(seed * 131 + 5); cards = []
    a0 = r.uniform(0, 6.283); ns = r.choice((6, 7))
    for i in range(ns):
        a = a0 + 6.283 * i / ns + r.uniform(-0.35, 0.35); d = r.uniform(1.2, 3.4) if i else 0.4
        cx, cy = d * math.cos(a), d * math.sin(a); top = r.uniform(3.4, 6.4) * (1.0 - 0.22 * d / 3.4)
        for j in range(r.choice((3, 4, 4))):
            th = r.uniform(0, 6.283); up = r.uniform(0.0, 1.0); rad = r.uniform(0.5, 1.5) * (1.0 - 0.55 * up)
            c = Vector((cx + rad * math.cos(th), cy + rad * math.sin(th), top * (0.5 + 0.42 * up) - 0.4))
            cards.append((c, r.uniform(2.0, 2.7), facing(r, Vector((c.x, c.y, 0)).normalized() if (len(cards) % 3 == 0 and c.length > 0.5) else None)))
    for i in range(7):                                                         # and a skirt of clumps low down all round, so no side is bare
        a = a0 + 6.283 * (i + 0.5) / 7 + r.uniform(-0.2, 0.2); d = r.uniform(3.0, 3.7)
        c = Vector((d * math.cos(a), d * math.sin(a), r.uniform(1.0, 1.9)))
        cards.append((c, r.uniform(2.2, 2.8), facing(r, Vector((c.x, c.y, 0)).normalized())))
    leaves = clumps_mesh(name + "_leaves", cards, Vector((0, 0, 2.6)))
    # the dark heart: a low uneven mound, well inside the clumps
    n = 7; ring0 = [(r.uniform(2.6, 3.1), 6.283 * i / n) for i in range(n)]; ring1 = [(r.uniform(1.7, 2.2), 6.283 * (i + 0.5) / n, r.uniform(1.9, 2.6)) for i in range(n)]
    vs = [Vector((d * math.cos(a), d * math.sin(a), -0.3)) for d, a in ring0] + [Vector((d * math.cos(a), d * math.sin(a), z)) for d, a, z in ring1] + [Vector((r.uniform(-0.6, 0.6), r.uniform(-0.6, 0.6), r.uniform(2.8, 3.3)))]
    fs = []
    for i in range(n): j = (i + 1) % n; fs += [(i, j, n + i), (j, n + j, n + i), (n + i, n + j, 2 * n)]
    core = bpy.data.meshes.new(name + "_core"); core.from_pydata(vs, [], fs)
    cc = core.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for d_, v in zip(cc.data, vs): t = 0.13 + 0.05 * max(v.z, 0) / 3.3; d_.color = (t, t, t, 1.0)
    core.color_attributes.active_color = cc
    for pl in core.polygons: pl.use_smooth = True
    core.normals_split_custom_set_from_vertices([tuple((Vector((v.x, v.y, 0)) * 0.25 + Vector((0, 0, 1))).normalized()) for v in vs])
    return leaves, core


def tuft(name, seed, lift=5.0):
    r = random.Random(seed * 71 + 3); cards = []
    for j in range(3):
        c = Vector((r.uniform(-0.55, 0.55), r.uniform(-0.55, 0.55), r.uniform(0.1, 0.6)))
        cards.append((c, r.uniform(1.5, 2.0), facing(r, Vector((c.x, c.y, 0)).normalized() if j == 0 and c.length > 0.2 else None)))
    return clumps_mesh(name, cards, Vector((0, 0, -1.2)), lift)


low = []
for i, nm in enumerate(("thicket_a", "thicket_b")):
    lv, core = thicket(nm, i); low += [(nm + "_leaves", lv), (nm + "_core", core)]
for i, nm in enumerate(("tuft_a", "tuft_b", "tuft_c")): low.append((nm, tuft(nm, i)))
for nm, me in low:
    me.materials.clear(); o = bpy.data.objects.new(nm, me); scene.collection.objects.link(o); out_objs.append(o)
    me.calc_loop_triangles(); print(nm, len(me.loop_triangles), "triangles", flush=True)

bpy.ops.object.select_all(action="DESELECT")
for o in out_objs: o.select_set(True)
OUTDIR2 = rp("assets/models/trees")
bpy.ops.export_scene.gltf(filepath=os.path.join(OUTDIR2, "trees_soft.glb"), export_format="GLB", use_selection=True, export_yup=True, export_normals=True,
                          export_vertex_color="ACTIVE", export_texcoords=True, export_apply=False, export_animations=False, export_materials="NONE")
shutil.copy(os.path.join(OUTDIR, "fluffy_atlas.png"), rp("race-view/assets/trees/leaf_clumps.png"))
print("exported trees_soft.glb", round(os.path.getsize(os.path.join(OUTDIR2, "trees_soft.glb")) / 1024), "KB", flush=True)
