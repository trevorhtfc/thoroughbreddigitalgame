"""Trees and hedges for the grandstand finish study, in the clay toy-town style (owner, 7 Nov 2026).

Exec'd by tools/blender/stand_clean_study.py when TREES=1 (after the stand and ground exist). Builds a small kit of
trees with rounded, clustered crowns (the owner's toy-town turf reference): lumpy leafy masses with a fine leaf
tooth, darker underneath and sunlit on top, matte, a touch of light through the edges; tapered trunks with a few
limbs. Species: oak, beech, chestnut, lime, poplar, and a shrub. Places them where the race view does (the planting
belts in courses/ascot-planting.json, the loose tree areas in courses/ascot-view.json -> trees), and dresses the
planting belts' hedge (assets/models/course/planting_belts.glb) as a clipped, leafy clay hedge.
Course axes (x east, z south) -> Blender (x, -z).
"""
import random
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union

_rng = random.Random(42)


def _leaf_mat(name, cols, sss=0.25):
    """Matte leafy clay: per-tree colour from a few greens, darker underneath and sunlit on top, mottled, with
    a fine leaf tooth in the surface."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.9; b.inputs["Specular IOR Level"].default_value = 0.15
    b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.15, 0.3, 0.08); b.inputs["Subsurface Scale"].default_value = 0.2
    tc = N.new("ShaderNodeTexCoord"); oi = N.new("ShaderNodeObjectInfo")
    pick = N.new("ShaderNodeValToRGB"); pick.color_ramp.interpolation = "CONSTANT"
    els = pick.color_ramp.elements
    while len(els) < len(cols): els.new(0.5)
    for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
    L.new(oi.outputs["Random"], pick.inputs[0])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    hz = N.new("ShaderNodeMapRange"); L.new(sep.outputs["Z"], hz.inputs["Value"]); hz.inputs["From Min"].default_value = 2.0; hz.inputs["From Max"].default_value = 11.0
    hz.inputs["To Min"].default_value = 0.62; hz.inputs["To Max"].default_value = 1.12
    mot = N.new("ShaderNodeTexNoise"); mot.inputs["Scale"].default_value = 0.6; mot.inputs["Detail"].default_value = 3
    L.new(tc.outputs["Object"], mot.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); L.new(mot.outputs["Fac"], mr.inputs["Value"]); mr.inputs["To Min"].default_value = 0.88; mr.inputs["To Max"].default_value = 1.1
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(hz.outputs["Result"], mul.inputs[0]); L.new(mr.outputs["Result"], mul.inputs[1])
    comb = N.new("ShaderNodeCombineColor")
    for k in ("Red", "Green", "Blue"): L.new(mul.outputs[0], comb.inputs[k])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
    L.new(pick.outputs[0], mix.inputs[6]); L.new(comb.outputs["Color"], mix.inputs[7]); L.new(mix.outputs[2], b.inputs["Base Color"])
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 7.0; L.new(tc.outputs["Object"], vor.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.45; bp.inputs["Distance"].default_value = 0.08
    L.new(vor.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


LEAF = _leaf_mat("tree_leaf", ["#6f9a4e", "#7da85a", "#628c46", "#8bb265", "#5c8546", "#86ad5c", "#73a052", "#79a456",
                               "#668f4a", "#8ab062", "#5f8946", "#9a6a52"])          # about one copper beech in twelve
LEAF_DARK = _leaf_mat("hedge_leaf", ["#5a8544", "#608a47", "#557f41"], sss=0.2)
BARK = bpy.data.materials.new("bark"); BARK.use_nodes = True
_bb = BARK.node_tree.nodes["Principled BSDF"]; _bb.inputs["Base Color"].default_value = lin("#7a6656"); _bb.inputs["Roughness"].default_value = 0.92


def _blob_cluster(name, centres, coll, seed):
    """One crown: overlapping spheres, each pushed lumpy by a cloud displacement, joined and smoothed."""
    parts = []
    tex = bpy.data.textures.new(name + "_tex", "CLOUDS"); tex.noise_scale = 0.9; tex.noise_depth = 2
    for k, (c, r) in enumerate(centres):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=r, location=c)
        o = bpy.context.object; o.name = f"{name}_b{k}"
        d = o.modifiers.new("lumps", "DISPLACE"); d.texture = tex; d.strength = r * 0.28; d.mid_level = 0.5
        d.texture_coords = "GLOBAL"
        bpy.ops.object.modifier_apply(modifier="lumps")
        parts.append(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts: o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    crown = bpy.context.object; crown.name = name + "_crown"
    for p in crown.data.polygons: p.use_smooth = True
    crown.data.materials.clear(); crown.data.materials.append(LEAF)
    for c in list(crown.users_collection): c.objects.unlink(crown)
    coll.objects.link(crown)
    return crown


def _trunk(name, h, r, limbs, coll):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=r * 0.55, depth=h, matrix=Matrix.Translation((0, 0, h / 2)))
    for (ax, ay, az, L) in limbs:                      # a few limbs reaching up into the crown
        d = Vector((ax, ay, az)).normalized()
        m = Matrix.Translation((0, 0, h * 0.7)) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Translation((0, 0, L / 2))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r * 0.45, radius2=r * 0.2, depth=L, matrix=m)
    me = bpy.data.meshes.new(name + "_trunk"); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(BARK)
    ob = bpy.data.objects.new(name + "_trunk", me); coll.objects.link(ob)
    return ob


def _poplar():
    """A soft lumpy column (not stacked balls): many overlapping lumps hugging a tall narrow core."""
    rr = random.Random(5); out = []
    for k in range(16):
        z = 3.8 + k * 0.68
        t = k / 15.0
        r = 1.35 * (1 - 0.55 * t) + 0.25 * math.sin(t * math.pi)
        a = rr.uniform(0, 2 * math.pi)
        out.append(((math.cos(a) * 0.35, math.sin(a) * 0.35, z), r * rr.uniform(0.85, 1.05)))
    return out


def _species():
    """name -> (crown sphere centres and radii, trunk height, trunk radius)."""
    R = random.Random(7)
    def cluster(n, cx, cz, rx, rz, r0, r1, seed):
        rr = random.Random(seed); out = []
        for k in range(n):
            a = rr.uniform(0, 2 * math.pi); t = rr.uniform(0, 1) ** 0.6
            out.append(((math.cos(a) * rx * t, math.sin(a) * rx * t * 0.9, cz + rr.uniform(-rz, rz) * (1 - 0.4 * t)), rr.uniform(r0, r1)))
        out.append(((0, 0, cz + rz * 0.6), r1 * 1.05))                     # a crowning dome
        return out
    return {
        "oak":      (cluster(11, 0, 7.0, 3.6, 1.8, 1.8, 2.7, 1), 4.2, 0.42),
        "beech":    (cluster(10, 0, 8.0, 2.8, 2.8, 1.7, 2.5, 2), 4.8, 0.38),
        "chestnut": (cluster(9, 0, 7.4, 3.0, 2.2, 2.0, 2.9, 3), 4.0, 0.45),
        "lime":     (cluster(12, 0, 8.6, 2.4, 3.4, 1.5, 2.2, 4), 5.0, 0.34),
        "poplar":   (_poplar(), 3.0, 0.28),
        "shrub":    (cluster(6, 0, 1.5, 1.6, 0.6, 1.0, 1.5, 6), 0.4, 0.2),
    }


def build_tree_kit():
    kit = {}
    for name, (centres, th, tr) in _species().items():
        coll = bpy.data.collections.new("tree_" + name)          # not linked to the scene: drawn only as instances
        _blob_cluster("tree_" + name, centres, coll, hash(name) % 100)
        limbs = [] if name in ("poplar", "shrub") else [(0.6, 0.2, 1), (-0.5, 0.4, 1), (0.1, -0.6, 1)]
        _trunk("tree_" + name, th, tr, [(a, b, c, th * 0.6) for a, b, c in limbs], coll)
        kit[name] = coll
    return kit


def _place(kit, name, x, z, s, turn):
    e = bpy.data.objects.new("t", None); e.instance_type = "COLLECTION"; e.instance_collection = kit[name]
    e.location = (x, -z, 0); e.rotation_euler = (0, 0, math.radians(turn)); e.scale = (s, s, s * _rng.uniform(0.92, 1.1))
    scene.collection.objects.link(e)


def place_trees(kit):
    VIEWJ = json.load(open(rp("courses/ascot-view.json")))
    PLANT = json.load(open(rp("courses/ascot-planting.json")))
    # the old tree names -> this kit's species
    MAP = {"oak_a": "oak", "oak_b": "chestnut", "oak_c": "beech", "wide_a": "oak", "wide_b": "lime", "poplar_a": "poplar",
           "bush_a": "shrub", "bush_b": "shrub"}
    n = 0
    for x, z, t, s, turn in PLANT["trees"]:
        _place(kit, MAP.get(t, "oak"), x, z, s * 1.15, turn); n += 1
    # loose trees, as the race view places them (placeTrees): kept clear of the track, rails and stand
    surf = COURSE["track"]["surface"]
    track = Polygon(surf[0], holes=surf[1:]).buffer(0)
    rails = unary_union([LineString(l) for l in COURSE["rails"]["lines"]])
    CL = VIEWJ["clearOf"]; S = CL["stand"]
    names = ["oak", "chestnut", "beech", "lime", "oak", "poplar"]
    rnd = random.Random(11)
    for a in VIEWJ["trees"]:
        x0, x1 = sorted((a["area"][0], a["area"][2])); z0, z1 = sorted((a["area"][1], a["area"][3]))
        z = z0
        while z < z1:
            x = x0 + rnd.random() * a["spacing"]
            while x < x1:
                if rnd.random() >= a.get("skip", 0):
                    k = a["clump"][0] + int(rnd.random() * (a["clump"][1] - a["clump"][0] + 1)) if "clump" in a else 1
                    for _ in range(k):
                        tx = x + (rnd.random() - 0.5) * (14 if k > 1 else a["spacing"] * 0.6)
                        tz = z + (rnd.random() - 0.5) * (10 if k > 1 else a["spacing"] * 0.6)
                        p = Point(tx, tz)
                        if S[0] < tx < S[2] and S[1] < tz < S[3]: continue
                        if track.contains(p) or rails.distance(p) < CL["track"]: continue
                        sc = a["scale"][0] + rnd.random() * (a["scale"][1] - a["scale"][0])
                        _place(kit, names[int(rnd.random() * len(names))], tx, tz, sc * 1.15, rnd.random() * 360); n += 1
                x += a["spacing"] * (0.7 + rnd.random() * 0.6)
            z += a["spacing"]
    print("trees:", n, flush=True)


def dress_hedge():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=rp("assets/models/course/planting_belts.glb"))
    new = [o for o in bpy.data.objects if o not in before]
    keep = 0
    for o in new:
        if o.type == "MESH" and "hedge" in o.name:
            o.data.materials.clear(); o.data.materials.append(LEAF_DARK)
            for p in o.data.polygons: p.use_smooth = True
            keep += 1
        else:                                       # the boards come as one of each design at the origin: not used here
            o.hide_render = True
    print("hedge pieces:", keep, flush=True)


TREE_KIT = build_tree_kit()
place_trees(TREE_KIT)
dress_hedge()
