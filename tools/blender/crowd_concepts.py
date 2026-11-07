"""Fresh crowd figure concepts for the clay-finish stand (owner, 6 Nov 2026).

    python -c "exec(open('tools/blender/crowd_concepts.py').read())"

Four concepts, each a set of eight people (gents in top hats, bowlers and boaters, ladies in wide, picture,
feathered and cloche hats), all matte clay, faceless, built from soft rounded forms like the stand:
  A figurine   painted diorama figurines, about four heads tall, arms, tailcoats and skirts
  B peg        turned wooden peg dolls: a rounded column with a ball head, painted clothes, no arms
  C bean       toy-town: a big head on a soft bean body, stubby arms and feet, three heads tall
  D silhouette Edwardian silhouettes: slender, six heads tall, frock coats, bustled skirts, a parasol or two
Writes assets/models/architecture/crowd_concept_<a-d>.glb (one object per person, feet at the origin, facing +y,
materials crowd_clothes / crowd_skin / crowd_hat / crowd_accent / crowd_dark, coloured per person by the views)
and reference/crowd/concepts/lineup.png (labels added by tools/course/label_crowd_lineup.py).
"""
import os, sys, math, random
import bpy, bmesh
from mathutils import Vector, Matrix

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
OUT = rp("reference/crowd/concepts"); os.makedirs(OUT, exist_ok=True)
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
SAMPLES = int(ARGS[0]) if ARGS and ARGS[0].isdigit() else 48

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)

MATS = {}
for n in ("crowd_clothes", "crowd_skin", "crowd_hat", "crowd_accent", "crowd_dark"):
    m = bpy.data.materials.new(n); m.use_nodes = True; MATS[n] = m


class Fig:
    """Collects parts per material, each a closed rounded solid, then one mesh with smooth normals."""
    def __init__(self):
        self.bm = bmesh.new(); self.mi = []
        self.names = list(MATS)

    def _add(self, geom_fn, mat):
        tmp = bmesh.new(); geom_fn(tmp)
        for f in tmp.faces: f.smooth = True
        me = bpy.data.meshes.new("t"); tmp.to_mesh(me); tmp.free()
        start = len(self.bm.faces); self.bm.from_mesh(me); bpy.data.meshes.remove(me)
        self.bm.faces.ensure_lookup_table()
        k = self.names.index(mat)
        for f in self.bm.faces[start:]: f.material_index = k

    def ball(self, mat, x, y, z, rx, ry=None, rz=None, sub=3):
        ry = rx if ry is None else ry; rz = rx if rz is None else rz
        self._add(lambda b: bmesh.ops.create_uvsphere(b, u_segments=24, v_segments=14, radius=1.0,
                  matrix=Matrix.Translation((x, y, z)) @ Matrix.Diagonal((rx, ry, rz, 1))), mat)

    def cone(self, mat, z0, z1, r0, r1, x=0, y=0, sx=1.0, sy=1.0, segs=28, rot=None):
        m = Matrix.Translation((x, y, (z0 + z1) / 2)) @ Matrix.Diagonal((sx, sy, 1, 1))
        if rot is not None: m = Matrix.Translation((x, y, z0)) @ rot @ Matrix.Translation((0, 0, (z1 - z0) / 2)) @ Matrix.Diagonal((sx, sy, 1, 1))
        self._add(lambda b: bmesh.ops.create_cone(b, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=z1 - z0, matrix=m), mat)

    def lathe(self, mat, prof, x=0, y=0, sx=1.0, sy=1.0, segs=32):
        """A turned solid from (radius, z) pairs, bottom to top: a peg doll, a bell skirt, a bowler."""
        def g(b):
            rings = []
            for r, z in prof:
                ring = []
                for i in range(segs):
                    a = 2 * math.pi * i / segs
                    ring.append(b.verts.new((x + r * math.cos(a) * sx, y + r * math.sin(a) * sy, z)))
                rings.append(ring)
            for j in range(len(rings) - 1):
                for i in range(segs):
                    b.faces.new((rings[j][i], rings[j][(i + 1) % segs], rings[j + 1][(i + 1) % segs], rings[j + 1][i]))
            b.faces.new(rings[0][::-1]); b.faces.new(rings[-1])
        self._add(g, mat)

    def limb(self, mat, a, b, r0, r1=None):
        """A capsule-ish limb from point a to b."""
        a, b = Vector(a), Vector(b); d = b - a; L = d.length
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        m = Matrix.Translation(a) @ rot @ Matrix.Translation((0, 0, L / 2))
        self._add(lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r0, radius2=r1 if r1 is not None else r0 * 0.85, depth=L, matrix=m), mat)
        self.ball(mat, *b, r1 if r1 is not None else r0 * 0.85)
        self.ball(mat, *a, r0)

    def to_object(self, name, coll):
        me = bpy.data.meshes.new(name); self.bm.to_mesh(me); self.bm.free()
        for n in self.names: me.materials.append(MATS[n])
        ob = bpy.data.objects.new(name, me); coll.objects.link(ob)
        mod = ob.modifiers.new("ws", "WEIGHTED_NORMAL")
        return ob


# ---------------- hats (shared shapes, scaled per concept) ----------------
def hat(F, kind, z, s=1.0, tilt=0.0):
    """A hat sitting with its band at height z; s scales it (toy concepts have bigger hats)."""
    if kind == "top":
        F.lathe("crowd_hat", [(0.17 * s, z), (0.17 * s, z + 0.015 * s), (0.095 * s, z + 0.02 * s), (0.1 * s, z + 0.2 * s),
                              (0.096 * s, z + 0.215 * s), (0.0, z + 0.218 * s)])
        F.lathe("crowd_accent", [(0.098 * s, z + 0.022 * s), (0.099 * s, z + 0.05 * s), (0.0, z + 0.051 * s)])
    elif kind == "bowler":
        F.lathe("crowd_hat", [(0.15 * s, z), (0.15 * s, z + 0.02 * s), (0.105 * s, z + 0.03 * s), (0.11 * s, z + 0.08 * s),
                              (0.09 * s, z + 0.13 * s), (0.05 * s, z + 0.152 * s), (0.0, z + 0.156 * s)])
    elif kind == "boater":
        F.lathe("crowd_hat", [(0.19 * s, z), (0.19 * s, z + 0.015 * s), (0.105 * s, z + 0.02 * s), (0.105 * s, z + 0.085 * s), (0.0, z + 0.088 * s)])
        F.lathe("crowd_accent", [(0.107 * s, z + 0.02 * s), (0.107 * s, z + 0.045 * s), (0.0, z + 0.046 * s)])
    elif kind == "wide":
        F.lathe("crowd_hat", [(0.3 * s, z - 0.01 * s), (0.3 * s, z + 0.005 * s), (0.11 * s, z + 0.03 * s), (0.105 * s, z + 0.1 * s), (0.0, z + 0.13 * s)])
        F.lathe("crowd_accent", [(0.112 * s, z + 0.03 * s), (0.11 * s, z + 0.06 * s), (0.0, z + 0.061 * s)])
        F.ball("crowd_accent", 0.1 * s, 0.05 * s, z + 0.06 * s, 0.05 * s)            # a rose on the band
    elif kind == "picture":
        F.lathe("crowd_hat", [(0.34 * s, z + 0.03 * s), (0.34 * s, z + 0.045 * s), (0.12 * s, z + 0.02 * s), (0.11 * s, z + 0.1 * s), (0.0, z + 0.12 * s)],
                sx=1.0, sy=0.9)
        for k in range(3):                                                      # a cluster of blooms
            F.ball("crowd_accent", -0.08 * s + k * 0.07 * s, 0.09 * s, z + 0.09 * s, 0.045 * s)
    elif kind == "feather":
        F.lathe("crowd_hat", [(0.16 * s, z), (0.16 * s, z + 0.015 * s), (0.11 * s, z + 0.025 * s), (0.105 * s, z + 0.09 * s), (0.0, z + 0.11 * s)])
        F.ball("crowd_accent", -0.07 * s, -0.02 * s, z + 0.2 * s, 0.035 * s, 0.025 * s, 0.17 * s)   # an upright plume
    elif kind == "cloche":
        F.lathe("crowd_hat", [(0.14 * s, z - 0.05 * s), (0.14 * s, z - 0.035 * s), (0.125 * s, z), (0.12 * s, z + 0.08 * s),
                              (0.08 * s, z + 0.13 * s), (0.0, z + 0.145 * s)])
        F.lathe("crowd_accent", [(0.127 * s, z - 0.005 * s), (0.124 * s, z + 0.025 * s), (0.0, z + 0.026 * s)])


PEOPLE = [("gent", "top"), ("gent", "top"), ("gent", "bowler"), ("gent", "boater"),
          ("lady", "wide"), ("lady", "picture"), ("lady", "feather"), ("lady", "cloche")]


# ---------------- A: figurine ----------------
def figurine(sex, hk, i):
    F = Fig(); rnd = random.Random(i)
    if sex == "gent":
        for sx in (-1, 1):                                                       # legs and shoes
            F.limb("crowd_dark", (sx * 0.075, 0, 0.1), (sx * 0.07, 0, 0.78), 0.075, 0.08)
            F.ball("crowd_dark", sx * 0.075, 0.04, 0.05, 0.075, 0.12, 0.055)
        F.lathe("crowd_clothes", [(0.0, 0.72), (0.17, 0.74), (0.18, 0.95), (0.19, 1.2), (0.17, 1.32), (0.1, 1.38), (0.0, 1.39)], sy=0.75)
        F.cone("crowd_clothes", 0.45, 0.82, 0.05, 0.16, y=-0.07, sx=1.0, sy=0.35)    # tails behind
        F.ball("crowd_accent", 0.0, 0.11, 1.22, 0.045, 0.02, 0.09)                    # cravat
        F.ball("crowd_accent", 0.1, 0.105, 1.2, 0.03)                                 # buttonhole
    else:
        F.lathe("crowd_clothes", [(0.0, 0.03), (0.3, 0.04), (0.29, 0.1), (0.22, 0.55), (0.15, 0.85), (0.14, 1.0),
                                  (0.16, 1.18), (0.15, 1.3), (0.09, 1.37), (0.0, 1.38)], sy=0.85)
        F.lathe("crowd_accent", [(0.0, 0.88), (0.152, 0.88), (0.15, 0.94), (0.0, 0.94)], sy=0.85)   # sash
    for sx in (-1, 1):                                                           # arms close to the body
        F.limb("crowd_clothes", (sx * 0.2, 0.0, 1.27), (sx * 0.24, 0.04, 0.9), 0.055, 0.05)
        F.ball("crowd_skin", sx * 0.24, 0.05, 0.86, 0.05)
    F.limb("crowd_skin", (0, 0, 1.36), (0, 0, 1.44), 0.055)
    F.ball("crowd_skin", 0, 0, 1.56, 0.135, 0.13, 0.15)
    hat(F, hk, 1.63, 1.12)
    return F


# ---------------- B: peg doll ----------------
def peg(sex, hk, i):
    F = Fig()
    if sex == "gent":
        F.lathe("crowd_dark", [(0.0, 0.0), (0.15, 0.0), (0.17, 0.04), (0.165, 0.55), (0.0, 0.55)])
        F.lathe("crowd_clothes", [(0.0, 0.55), (0.168, 0.55), (0.175, 0.95), (0.17, 1.2), (0.14, 1.28), (0.08, 1.31), (0.0, 1.31)])
        F.lathe("crowd_accent", [(0.0, 1.12), (0.172, 1.12), (0.171, 1.17), (0.0, 1.17)])   # collar band
    else:
        F.lathe("crowd_clothes", [(0.0, 0.0), (0.2, 0.0), (0.215, 0.04), (0.2, 0.4), (0.17, 0.8), (0.16, 1.2), (0.13, 1.28), (0.08, 1.31), (0.0, 1.31)])
        F.lathe("crowd_accent", [(0.0, 0.06), (0.212, 0.06), (0.207, 0.16), (0.0, 0.16)])   # hem band
        F.lathe("crowd_accent", [(0.0, 0.92), (0.165, 0.92), (0.164, 0.98), (0.0, 0.98)])
    F.ball("crowd_skin", 0, 0, 1.45, 0.155)
    hat(F, hk, 1.55, 1.2)
    return F


# ---------------- C: bean (toy town) ----------------
def bean(sex, hk, i):
    F = Fig()
    for sx in (-1, 1):
        F.ball("crowd_dark", sx * 0.09, 0.05, 0.05, 0.08, 0.12, 0.06)               # little feet
    if sex == "gent":
        F.lathe("crowd_clothes", [(0.0, 0.07), (0.17, 0.08), (0.24, 0.25), (0.25, 0.5), (0.22, 0.75), (0.14, 0.86), (0.0, 0.88)])
        F.ball("crowd_accent", 0.0, 0.22, 0.68, 0.05, 0.02, 0.06)                     # bow tie
        F.ball("crowd_accent", 0.0, 0.2, 0.45, 0.02, 0.02, 0.02)
    else:
        F.lathe("crowd_clothes", [(0.0, 0.05), (0.3, 0.06), (0.28, 0.25), (0.22, 0.5), (0.2, 0.7), (0.13, 0.86), (0.0, 0.88)])
        F.lathe("crowd_accent", [(0.0, 0.5), (0.222, 0.5), (0.213, 0.56), (0.0, 0.56)])
    for sx in (-1, 1):
        F.limb("crowd_clothes", (sx * 0.2, 0.0, 0.7), (sx * 0.27, 0.05, 0.48), 0.06, 0.055)
        F.ball("crowd_skin", sx * 0.275, 0.06, 0.45, 0.055)
    F.ball("crowd_skin", 0, 0, 1.08, 0.2, 0.19, 0.21)
    hat(F, hk, 1.2, 1.5)
    return F


# ---------------- D: Edwardian silhouette ----------------
def silhouette(sex, hk, i):
    F = Fig()
    if sex == "gent":
        for sx in (-1, 1):
            F.limb("crowd_dark", (sx * 0.06, 0, 0.06), (sx * 0.06, 0, 0.9), 0.05, 0.06)
            F.ball("crowd_dark", sx * 0.06, 0.04, 0.035, 0.05, 0.1, 0.035)
        F.lathe("crowd_clothes", [(0.0, 0.55), (0.12, 0.55), (0.15, 0.8), (0.14, 1.05), (0.17, 1.4), (0.13, 1.5), (0.06, 1.54), (0.0, 1.55)], sy=0.7)
        F.ball("crowd_accent", 0.0, 0.1, 1.38, 0.035, 0.02, 0.08)
        for sx in (-1, 1):
            F.limb("crowd_clothes", (sx * 0.17, 0, 1.45), (sx * 0.19, 0.02, 1.0), 0.045, 0.04)
            F.ball("crowd_skin", sx * 0.19, 0.03, 0.96, 0.04)
        if hk == "bowler":                                                       # a cane
            F.limb("crowd_dark", (0.2, 0.06, 0.96), (0.27, 0.12, 0.02), 0.012, 0.012)
    else:
        prof = [(0.0, 0.0), (0.3, 0.0), (0.3, 0.05), (0.26, 0.3), (0.2, 0.6), (0.13, 0.95), (0.1, 1.05), (0.14, 1.25),
                (0.15, 1.38), (0.11, 1.48), (0.05, 1.54), (0.0, 1.55)]
        F.lathe("crowd_clothes", prof, sy=0.8)
        F.ball("crowd_clothes", 0, -0.17, 0.85, 0.16, 0.14, 0.2)                        # the bustle
        F.lathe("crowd_accent", [(0.0, 1.02), (0.105, 1.02), (0.11, 1.07), (0.0, 1.07)], sy=0.8)
        for sx in (-1, 1):
            F.limb("crowd_clothes", (sx * 0.14, 0, 1.44), (sx * 0.17, 0.05, 1.08), 0.04, 0.035)
            F.ball("crowd_skin", sx * 0.17, 0.06, 1.05, 0.035)
        if hk == "cloche":                                                       # a parasol (one lady in eight)
            F.limb("crowd_dark", (0.17, 0.06, 1.05), (0.22, 0.1, 2.05), 0.012, 0.012)
            F.lathe("crowd_accent", [(0.0, 1.95), (0.42, 1.98), (0.3, 2.08), (0.0, 2.16)], x=0.22, y=0.1)
    F.limb("crowd_skin", (0, 0, 1.53), (0, 0, 1.6), 0.04)
    F.ball("crowd_skin", 0, 0, 1.7, 0.1, 0.1, 0.12)
    hat(F, hk, 1.76, 1.0)
    return F


CONCEPTS = {"a": ("A · Figurine", figurine), "b": ("B · Peg doll", peg), "c": ("C · Toy town", bean), "d": ("D · Edwardian silhouette", silhouette)}


def export(coll, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                              export_animations=False, export_materials="EXPORT")
    print("exported", path, flush=True)


colls = {}
for key, (label, fn) in CONCEPTS.items():
    coll = bpy.data.collections.new("concept_" + key); scene.collection.children.link(coll)
    for i, (sex, hk) in enumerate(PEOPLE):
        F = fn(sex, hk, i)
        ob = F.to_object(f"{key}_{i}_{sex}_{hk}", coll)
    colls[key] = coll
    export(coll, rp(f"assets/models/architecture/crowd_concept_{key}.glb"))
    tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in coll.objects) / len(coll.objects)
    print(f"concept {key}: about {tris:.0f} triangles a person", flush=True)


# ---------------- review renders: a line-up and a packed group per concept, in the study's soft clay light ----------------
CLOTHES = ["#2c3140", "#3a3d44", "#4b4d52", "#2f3a33", "#59544c", "#c9a0a8", "#9fb6c8", "#ddd2b8", "#a8706a", "#88a383",
           "#d2b874", "#e8e2d6", "#9a88b4", "#cf9476"]
HATS = ["#222226", "#2a2a2e", "#efe6d2", "#d8c08a", "#c9a0a8", "#9fb6c8", "#e8dcc0"]
ACCENT = ["#e6998b", "#8db58c", "#eccd7c", "#8eb0d6", "#b49fd2", "#f2ece0", "#c0453a"]
SKIN = ["#efc6a4", "#e2b48e", "#c99572", "#9a6a4a", "#6e4a34"]

def palette(m, cols, rough=0.92, sss=0.0):
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rough; b.inputs["Specular IOR Level"].default_value = 0.1
    if sss:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.05, 0.03, 0.02); b.inputs["Subsurface Scale"].default_value = 0.03
    oi = nt.nodes.new("ShaderNodeObjectInfo"); cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    while len(els) < len(cols): els.new(0.5)
    for i, c in enumerate(cols): els[i].position = i / len(cols); els[i].color = lin(c)
    nt.links.new(oi.outputs["Random"], cr.inputs[0]); nt.links.new(cr.outputs[0], b.inputs["Base Color"])
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40.0
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.08; bp.inputs["Distance"].default_value = 0.005
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])

palette(MATS["crowd_clothes"], CLOTHES); palette(MATS["crowd_hat"], HATS); palette(MATS["crowd_accent"], ACCENT)
palette(MATS["crowd_skin"], SKIN, sss=0.2); palette(MATS["crowd_dark"], ["#24262b", "#2f3036", "#3b352f"])

# soft warm sun and pastel sky (as the stand study's "soft" variant)
world = bpy.data.worlds.new("sky"); scene.world = world; world.use_nodes = True
wn, wl = world.node_tree.nodes, world.node_tree.links
tc = wn.new("ShaderNodeTexCoord"); sep = wn.new("ShaderNodeSeparateXYZ"); ramp = wn.new("ShaderNodeValToRGB")
wl.new(tc.outputs["Generated"], sep.inputs[0]); wl.new(sep.outputs["Z"], ramp.inputs[0])
ramp.color_ramp.elements[0].color = (1.0, 0.86, 0.74, 1); ramp.color_ramp.elements[1].color = (0.56, 0.7, 0.9, 1); ramp.color_ramp.elements[1].position = 0.62
mid = ramp.color_ramp.elements.new(0.16); mid.color = (0.93, 0.87, 0.85, 1)
wl.new(ramp.outputs[0], wn["Background"].inputs[0]); wn["Background"].inputs[1].default_value = 0.8
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 4.6; sun.data.angle = math.radians(14); sun.data.color = (1.0, 0.8, 0.62)
sun.rotation_euler = (-Vector((-1.0, 0.32, 0.45)).normalized()).to_track_quat("-Z", "Y").to_euler()
sun.rotation_euler = Vector((-0.7, 0.6, -0.55)).normalized().to_track_quat("-Z", "Y").to_euler()

grass = bpy.data.materials.new("lawn"); grass.use_nodes = True
gb = grass.node_tree.nodes["Principled BSDF"]; gb.inputs["Base Color"].default_value = lin("#93b466"); gb.inputs["Roughness"].default_value = 0.97
me = bpy.data.meshes.new("ground"); me.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
me.materials.append(grass); scene.collection.objects.link(bpy.data.objects.new("ground", me))
rail_m = bpy.data.materials.new("rail"); rail_m.use_nodes = True; rail_m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = lin("#f4f2ea")

scene.render.engine = "CYCLES"; scene.cycles.samples = SAMPLES; scene.cycles.use_denoising = True; scene.cycles.device = "CPU"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Base Contrast"
except Exception: pass
scene.view_settings.exposure = 0.12

cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.clip_end = 2000

def shoot(path, eye, at, lens, res, dof=None):
    cam.location = eye; cam.rotation_euler = (Vector(at) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.dof.use_dof = dof is not None
    if dof: cam.data.dof.focus_distance = (Vector(at) - Vector(eye)).length; cam.data.dof.aperture_fstop = dof
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path; bpy.ops.render.render(write_still=True); print("rendered", path, flush=True)

refs = {}
def load_ref(key, path, mapping):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path)
    obs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    coll = bpy.data.collections.new("ref_" + key); scene.collection.children.link(coll)
    for o in obs:
        for c in list(o.users_collection): c.objects.unlink(o)
        coll.objects.link(o); o.parent = None; o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
        for i, sl in enumerate(o.material_slots):
            base = (sl.material.name if sl.material else "").split(".")[0]
            for k, v in mapping.items():
                if base.startswith(k): o.material_slots[i].material = MATS[v]
    return coll
refs["now"] = load_ref("now", rp("assets/models/architecture/crowd_people.glb"), {"crowd_clothes": "crowd_clothes", "crowd_skin": "crowd_skin", "crowd_hat": "crowd_hat"})
SK = os.environ.get("SKITTLE")
if SK and os.path.exists(SK):
    refs["skittle"] = load_ref("skittle", SK, {"fig_main": "crowd_clothes", "fig_skin": "crowd_skin", "fig_hat": "crowd_hat", "fig_trim": "crowd_accent", "fig_hair": "crowd_dark"})

ALL = dict(colls); ALL.update(refs)
for c in ALL.values(): c.hide_render = True

for key, coll in ALL.items():
    src = [o for o in coll.objects]                                # copies are drawn; the source collection stays hidden
    shown = []
    # line-up: each person twice (two colourways), in a row, facing the camera
    for k in range(2):
        for j, o in enumerate(src[:8] if key in colls else src):
            d = o.copy(); scene.collection.objects.link(d); shown.append(d)
            n = len(src[:8]) if key in colls else len(src)
            d.location = ((j + k * n - (2 * n - 1) / 2) * 0.82, 0, 0); d.rotation_euler = (0, 0, 0)
    w = 2 * (len(src[:8]) if key in colls else len(src)) * 0.82
    shoot(os.path.join(OUT, f"lineup_{key}.png"), (0, (w + 1.2) * 85 / 36, 1.6), (0, 0, 1.0), 85, (1800, 420))
    for d in shown: bpy.data.objects.remove(d)
    if os.environ.get("LINEUP_ONLY"):
        continue
    # a packed group behind a rail, from the track side, a little above (a close race camera)
    rnd = random.Random(7); shown = []
    for row in range(8):
        for col in range(26):
            if rnd.random() < 0.12: continue
            o = src[rnd.randrange(len(src))]; d = o.copy(); scene.collection.objects.link(d); shown.append(d)
            d.location = (col * 0.62 - 8 + rnd.uniform(-0.12, 0.12), -row * 0.7 - rnd.uniform(0, 0.25), 0)
            d.rotation_euler = (0, 0, rnd.uniform(-0.35, 0.35)); s = rnd.uniform(0.95, 1.05); d.scale = (s, s, s)
    rail = bpy.data.objects.new("rail", bpy.data.meshes.new("rail")); scene.collection.objects.link(rail)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((0, 0.9, 1.05)) @ Matrix.Diagonal((30, 0.1, 0.1, 1)))
    for x in range(-14, 15, 2): bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, 0.9, 0.55)) @ Matrix.Diagonal((0.1, 0.1, 1.1, 1)))
    bm.to_mesh(rail.data); bm.free(); rail.data.materials.append(rail_m); shown.append(rail)
    shoot(os.path.join(OUT, f"group_{key}.png"), (2.0, 13.0, 4.2), (0.0, -2.0, 1.0), 50, (1400, 700), dof=4.0)
    for d in shown: bpy.data.objects.remove(d)
