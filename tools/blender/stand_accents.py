"""Dress Ascot's main stand for the real-time race view: the clay colours and the pastel accents (owner, 6-7 Nov 2026).

    python -c "exec(open('tools/blender/stand_accents.py').read())"

Run after tools/blender/build_stand_modules.py. Reads ascot_main_stand.glb and ascot_main_stand_far.glb and writes
ascot_main_stand_dressed.glb and ascot_main_stand_far_dressed.glb (same axes and origin), with what the finish study
(tools/blender/stand_clean_study.py, variant "accent") adds at render time, as real geometry and flat materials so
any engine draws it:
  - the stand's own materials in the clay palette (warm cream stone, white paintwork, grey slate, dark green iron,
    dark violet glass);
  - pastel doors along the central stretch, coloured balusters by building (sage on the clock block, powder blue on
    the grand canopies, blush on the small ones);
  - striped canvas awnings over every front door and arched opening in the base, each building its own stripe;
  - flags: on the canopy and pavilion roofs, along the ridge of the roof extensions, along the terraces' back walls.
Materials: gs_* (the stand's), gs_acc_<colour>, gs_canvas, gs_flagpole, gs_finial.
"""
import os, json, math
import bpy, bmesh
from mathutils import Vector

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
COURSE = json.load(open(rp("courses/ascot.json")))
MODS = COURSE["grandstand"]["modules"]
FRONT = COURSE["grandstand"]["frontLine"]


def lin(hexc):
    h = hexc.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1.0,)


CLAY = {"gs_wall": "#ecdcc0", "gs_podium": "#dccaa8", "gs_trim": "#f6eee0", "gs_roof": "#7c7e86", "gs_iron": "#2f4236",
        "gs_glass": "#34323f", "gs_door": "#3a5545", "gs_gilt": "#c8a466", "gs_steps": "#dccfb3",
        "gs_clock_face": "#fbf5ea", "gs_clock_dark": "#25262a"}
PAL = {"sage": "#8db58c", "powder": "#8eb0d6", "blush": "#e6998b", "butter": "#eccd7c", "lilac": "#b49fd2"}


def flat(name, hexc, rough=0.9):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(hexc); b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.15
    m.diffuse_color = lin(hexc)
    return m


def module_at(x):
    for m in MODS:
        if m["xWest"] <= x <= m["xEast"]: return m
    return None


def islands(o):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
    seen, out, M = set(), [], o.matrix_world
    for f in bm.faces:
        if f.index in seen: continue
        stack, comp = [f], []; seen.add(f.index)
        while stack:
            g = stack.pop(); comp.append(g.index)
            for v in g.verts:
                for h in v.link_faces:
                    if h.index not in seen: seen.add(h.index); stack.append(h)
        ps = [M @ v.co for i in comp for v in bm.faces[i].verts]
        out.append((comp, Vector((min(p.x for p in ps), min(p.y for p in ps), min(p.z for p in ps))),
                    Vector((max(p.x for p in ps), max(p.y for p in ps), max(p.z for p in ps)))))
    bm.free()
    return out


def recolour(o, faces, mat):
    names = [sl.material.name for sl in o.material_slots if sl.material]
    if mat.name not in names: o.data.materials.append(mat)
    k = [sl.material.name for sl in o.material_slots].index(mat.name)
    for i in faces: o.data.polygons[i].material_index = k


def dress(src, dst, far):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=src)
    parts = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in parts:                                             # bake every transform in: stand axes, glTF import's
        o.select_set(True)                                     # y-up turn included (front faces +y, origin the tower)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for m in bpy.data.materials:
        base = m.name.split(".")[0]
        if base in CLAY: flat(m.name, CLAY[base], 0.6 if base in ("gs_glass",) else 0.9)
    AM = {k: flat("gs_acc_" + k, v) for k, v in PAL.items()}
    canvas = flat("gs_canvas", "#f7efe0"); pole = flat("gs_flagpole", "#f4eee2"); finial = flat("gs_finial", "#c8a466", 0.6)
    by_mat = lambda name: [o for o in parts if any(sl.material and sl.material.name.split(".")[0] == name for sl in o.material_slots)]

    # in these axes the stand's front is the line y = 0, facing +y (towards the track); x as courses/ascot.json
    STRIPES = ["blush", "sage", "butter", "powder", "lilac"]
    bcol, last, k = {}, None, -1
    for m in sorted(MODS, key=lambda m: -m["xEast"]):
        if m["module"] != last: k += 1; last = m["module"]
        bcol[m["xEast"]] = STRIPES[k % len(STRIPES)]
    stripe_at = lambda x: bcol[module_at(x)["xEast"]] if module_at(x) else "blush"
    DOOR_COL = {"clock_centre": "sage", "three_storey_block": "butter", "grand_pavilion": "powder", "ironwork_bay": "blush",
                "pavilion": "lilac", "window_block": "butter", "link": "blush", "end_pavilion": "sage", "stair_bay": "butter"}
    front_y = lambda lo, hi: hi.y > -0.6           # faces the track (front at y = 0, the track at +y)
    openings = []
    for o in by_mat("gs_door"):
        for comp, lo, hi in islands(o):
            x = (lo.x + hi.x) / 2; m = module_at(x)
            if m and -110 < x < 220 and m["module"] in DOOR_COL:
                recolour(o, comp, AM[DOOR_COL[m["module"]]])
            if m and front_y(lo, hi) and hi.z < 4.0 and hi.x - lo.x > 0.6: openings.append((lo, hi, stripe_at(x)))
    for o in by_mat("gs_glass"):
        for comp, lo, hi in islands(o):
            x = (lo.x + hi.x) / 2
            if front_y(lo, hi) and hi.z < 3.4 and lo.z > 0.2 and hi.x - lo.x > 0.8 and module_at(x):
                openings.append((lo, hi, stripe_at(x)))
    BAL = {"clock_centre": "sage", "grand_pavilion": "powder", "pavilion": "blush"}
    nb = 0
    for o in by_mat("gs_trim"):
        for comp, lo, hi in islands(o):
            sx, sy, sz = hi.x - lo.x, hi.y - lo.y, hi.z - lo.z
            m = module_at((lo.x + hi.x) / 2)
            if not m or m["module"] not in BAL: continue
            if (max(sx, sy) < 0.13 and 0.55 < sz < 1.1) or (far and 0.6 < sz < 1.0 and min(sx, sy) < 0.08 and max(sx, sy) > 1.0):
                recolour(o, comp, AM[BAL[m["module"]]]); nb += 1

    new = []
    def add_mesh(name, verts, faces, mats, fmat=None, thick=0.0):
        me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
        for mm in mats: me.materials.append(mm)
        if fmat:
            for p, kk in zip(me.polygons, fmat): p.material_index = kk
        ob = bpy.data.objects.new(name, me); scene.collection.objects.link(ob); new.append(ob)
        if thick:
            ob.modifiers.new("thick", "SOLIDIFY").thickness = thick
        return ob

    def flag(base, h, cols, w=3.4, fh=2.1, phase=0.0):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=h, location=(base.x, base.y, base.z + h / 2), vertices=8)
        p = bpy.context.object; p.data.materials.append(pole); new.append(p)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.16, location=(base.x, base.y, base.z + h + 0.1), segments=10, ring_count=6)
        f = bpy.context.object; f.data.materials.append(finial); new.append(f)
        nx, nz = (10, 4) if far else (16, 8)
        vs, fs, fm = [], [], []
        for j in range(nz + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / nz
                vs.append((base.x + u * w, base.y + 0.32 * math.sin(u * 5.5 + phase) * u + 0.08 * math.sin(v * 3 + u * 4),
                           base.z + h - 0.15 - v * fh - 0.12 * u * u))
        for j in range(nz):
            for i in range(nx):
                a = j * (nx + 1) + i
                fs.append((a, a + 1, a + nx + 2, a + nx + 1)); fm.append(0 if j < nz / 2 else 1)
        add_mesh("flag", vs, fs, [AM[cols[0]], AM[cols[1]]], fm, 0.02)

    pts = [(o.matrix_world @ v.co) for o in parts for v in o.data.vertices]
    roofs = [(o.matrix_world @ v.co) for o in by_mat("gs_roof") for v in o.data.vertices]
    TFLAG = [("blush", "blush"), ("sage", "sage"), ("butter", "butter"), ("powder", "powder"), ("lilac", "lilac")]
    nf = 0
    # along the open terraces' back walls, one every five bays
    wall = [p for p in pts if p.z < 20.5]
    x = max(m["xEast"] for m in MODS) - 1.75
    while x > min(m["xWest"] for m in MODS):
        m = module_at(x)
        if m and m["module"] == "terrace_stand" and not m.get("roof"):
            near = [p for p in wall if abs(p.x - x) < 2.0]
            if near:
                b = max(near, key=lambda p: p.z)
                flag(Vector((x, b.y + 0.4, b.z)), 4.0, TFLAG[nf % 5], w=2.4, fh=1.5, phase=nf * 0.9); nf += 1
        x -= 17.5
    # canopy and pavilion roofs
    FLAG_COL = [("blush", "blush"), ("powder", "powder"), ("sage", "butter"), ("lilac", "lilac"), ("butter", "blush"), ("powder", "sage")]
    kk = 0
    for m in MODS:
        if m["module"] in ("grand_pavilion", "pavilion", "end_pavilion"):
            near = [p for p in roofs if m["xWest"] + 1 < p.x < m["xEast"] - 1]
            if near:
                r = max(near, key=lambda p: p.z)
                flag(Vector(((m["xWest"] + m["xEast"]) / 2, r.y, r.z)), 4.5, FLAG_COL[kk % 6], phase=kk * 1.3); kk += 1
    # along the ridges of the roof extensions, every three bays
    spans = []
    for m in sorted(MODS, key=lambda m: -m["xEast"]):
        if not m.get("roof"): continue
        if spans and abs(spans[-1][1] - m["xEast"]) < 0.01: spans[-1][1] = m["xWest"]
        else: spans.append([m["xEast"], m["xWest"]])
    nr = 0
    for xe, xw in spans:
        near = [p for p in roofs if xw - 0.5 < p.x < xe + 0.5 and p.z < 26.0]
        if not near: continue
        r = max(near, key=lambda p: p.z)
        x = xe - 3.5
        while x > xw + 1.0:
            flag(Vector((x, r.y, r.z)), 3.2, TFLAG[nr % 5], w=2.0, fh=1.25, phase=nr * 1.1); nr += 1
            x -= 10.5
    # striped awnings over the openings in the base, one per opening
    def awning(lo, hi, col):
        x0, x1 = lo.x - 0.5, hi.x + 0.5; yw = hi.y + 0.02; zt = hi.z + 0.55
        out, drop, n = 1.9, 0.85, max(4, round((x1 - x0) / 0.36))
        vs, fs, fm = [], [], []
        for i in range(n + 1):
            xx = x0 + (x1 - x0) * i / n
            vs += [(xx, yw, zt), (xx, yw + out, zt - drop), (xx, yw + out, zt - drop - 0.28)]
        for i in range(n):
            a, b = 3 * i, 3 * (i + 1)
            fs += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2)]; fm += [i % 2, i % 2]
        add_mesh("awning", vs, fs, [canvas, AM[col]], fm, 0.03)
    openings.sort(key=lambda d: d[0].x)
    placed = []
    for lo, hi, col in openings:
        if any(abs(lo.x - p.x) < 0.3 and abs(hi.x - q.x) < 0.3 for p, q in placed): continue
        awning(lo, hi, col); placed.append((lo, hi))
    print(f"{os.path.basename(dst)}: {nb} balusters/screens recoloured, {len(placed)} awnings, {nf + kk + nr} flags", flush=True)

    bpy.ops.object.select_all(action="DESELECT")
    for o in parts + new: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
                              export_animations=False)
    print("exported", dst, flush=True)


ARCH = rp("assets/models/architecture")
dress(os.path.join(ARCH, "ascot_main_stand_far.glb"), os.path.join(ARCH, "ascot_main_stand_far_dressed.glb"), far=True)
dress(os.path.join(ARCH, "ascot_main_stand.glb"), os.path.join(ARCH, "ascot_main_stand_dressed.glb"), far=False)
