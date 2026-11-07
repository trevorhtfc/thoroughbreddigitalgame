"""The finish study's clay trees for the real-time race view (owner, 7 Nov 2026: "yeah nice").

    python -c "exec(open('tools/blender/export_clay_trees.py').read())"

Builds the study's tree kit (tools/blender/study_trees.py: rounded, clustered crowns of lumpy leafy masses on
tapered trunks with a few limbs) at web weight and writes assets/models/trees/trees_clay.glb with the node names
the race view already places (oak_a ... bush_b, each _crown, _crown_far and _trunk; the study's map from those
names to its species: oak_a oak, oak_b chestnut, oak_c beech, wide_a a second oak, wide_b lime, poplar_a poplar,
bush_a and bush_b shrubs). The study's 1.15 size is built in.

Crowns carry their shading as vertex colours (grey: darker underneath, sunlit on top, a soft mottle, divided by
SHADE_MAX so it fits 0..1); the race view gives each tree its leaf colour per copy (one of the study's twelve
greens, the odd copper beech) and multiplies SHADE_MAX back in. Normals are bent a little over half way out from the crown's
centre, so each crown reads as one soft mass. Near crowns: each lump an ico sphere of 642 points; far: 162.
Trunks: the study's bark colour as a flat vertex colour.
"""
import os, math, json, random
import bpy, bmesh
from mathutils import Vector, Matrix, noise

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
# the study's species (crown lumps, trunk height and radius) without building its full-weight kit
src = open(rp("tools/blender/study_trees.py")).read()
ns = {"bpy": bpy, "bmesh": bmesh, "math": math, "Vector": Vector, "Matrix": Matrix, "lin": lin, "random": random, "json": json, "rp": rp, "scene": scene}
ns["BARK"] = bpy.data.materials.new("bark_study")
exec(src[src.index("def _trunk"):src.index("def build_tree_kit")], ns)
SPECIES = ns["_species"]()
SCALE = 1.15
SHADE_MAX = 1.12
BARK = "#7a6656"


def crown(name, centres, subdiv, seed):
    """The study's crown: overlapping lumps, each pushed lumpy by cloud noise, as one mesh."""
    bm = bmesh.new()
    for k, (c, r) in enumerate(centres):
        g = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r, matrix=Matrix.Translation(c))
        for v in g["verts"]:
            n = (v.co - Vector(c)).normalized()
            d = noise.noise(v.co * 0.9 + Vector((seed * 7.1, k * 3.3, 0)), noise_basis="BLENDER")       # -1..1
            v.co += n * r * 0.28 * d * 0.5
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.transform(Matrix.Diagonal((SCALE, SCALE, SCALE, 1)))
    ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob)
    # shading (study's leaf material: height 2..11 m -> 0.62..1.12, times a soft mottle 0.88..1.1)
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    for i, v in enumerate(me.vertices):
        z = v.co.z / SCALE
        h = 0.62 + 0.5 * min(max((z - 2.0) / 9.0, 0), 1)
        mt = 0.88 + 0.22 * (0.5 + 0.5 * noise.noise(v.co * 0.6, noise_basis="PERLIN_ORIGINAL"))
        s = min(h * mt / SHADE_MAX, 1.0)
        col.data[i].color = (s, s, s, 1.0)
    me.color_attributes.active_color = col
    # normals bent half way out from the crown's centre
    cen = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
    me.calc_loop_triangles() if hasattr(me, "calc_loop_triangles") else None
    ns_ = []
    for l in me.loops:
        v = me.vertices[l.vertex_index]
        ns_.append((v.normal * 0.45 + (v.co - cen).normalized() * 0.55).normalized())
    me.normals_split_custom_set(ns_)
    return ob


def trunk(name, th, tr, limbs):
    ob = ns["_trunk"](name, th, tr, limbs, scene.collection)
    me = ob.data; me.materials.clear()
    me.transform(Matrix.Diagonal((SCALE, SCALE, SCALE, 1)))
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    c = lin(BARK)
    for d in col.data: d.color = c
    me.color_attributes.active_color = col
    ob.name = name
    return ob


NAMES = {"oak_a": ("oak", 1), "oak_b": ("chestnut", 2), "oak_c": ("beech", 3), "wide_a": ("oak", 11),
         "wide_b": ("lime", 4), "poplar_a": ("poplar", 5), "bush_a": ("shrub", 6), "bush_b": ("shrub", 16)}
leaf = bpy.data.materials.new("leaf"); bark = bpy.data.materials.new("bark")
objs = []
for name, (sp, seed) in NAMES.items():
    centres, th, tr = SPECIES[sp]
    if seed > 10:                                            # the second oak / shrub: the lumps turned and jostled
        rr = random.Random(seed)
        a = rr.uniform(0, 2 * math.pi); R = Matrix.Rotation(a, 3, "Z")
        centres = [(tuple(R @ Vector(c) + Vector((rr.uniform(-0.4, 0.4), rr.uniform(-0.4, 0.4), rr.uniform(-0.3, 0.3)))), r * rr.uniform(0.92, 1.08)) for c, r in centres]
    for suffix, sub in (("_crown", 3), ("_crown_far", 2)):
        o = crown(name + suffix, centres, sub, seed); o.data.materials.append(leaf); objs.append(o)
    if sp != "shrub":
        limbs = [] if sp == "poplar" else [(0.6, 0.2, 1), (-0.5, 0.4, 1), (0.1, -0.6, 1)]
        o = trunk(name + "_trunk", th, tr, [(a, b, c, th * 0.6) for a, b, c in limbs]); o.data.materials.append(bark); objs.append(o)
    print(name, sp, "crown", len(objs[-2 if sp != "shrub" else -1].data.vertices), flush=True)

bpy.ops.object.select_all(action="DESELECT")
for o in objs: o.select_set(True)
out = rp("assets/models/trees/trees_clay.glb")
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                          export_vertex_color="ACTIVE", export_normals=True, export_animations=False)
json.dump({"_about": "Clay trees for the race view (tools/blender/export_clay_trees.py). Crown vertex colours are shading / shadeMax; multiply by shadeMax and the leaf colour per copy.",
           "shadeMax": SHADE_MAX,
           "leaf": ["#6f9a4e", "#7da85a", "#628c46", "#8bb265", "#5c8546", "#86ad5c", "#73a052", "#79a456", "#668f4a", "#8ab062", "#5f8946", "#9a6a52"],
           "hedge": ["#5a8544", "#608a47", "#557f41"]},
          open(rp("assets/models/trees/trees_clay.json"), "w"), indent=1)
print("exported", out, flush=True)
