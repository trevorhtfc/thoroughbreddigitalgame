"""Build the second-generation racehorse (v2) beside the first, without touching it.

Run headless from the repo root (Blender as a Python module, bpy 5.2):

    python -c "exec(open('tools/blender/build_racehorse_v2.py').read())"

Reads (never writes):
    assets/models/master/racehorse_master.blend    the v1 master: mesh, rig, gallop, walk
    assets/models/tint_masks/build-mask.png        the v1 colour masks (coat, points, silks)

Writes:
    assets/models/master/racehorse_v2.blend        the v2 master
    assets/models/racehorse_v2.glb                 the v2 model, three detail levels, all clips
    assets/models/racehorse_v2_rig.json            what the clips are and how to blend them

What changes from v1 (see the handover, "Horse and jockey v2"):
 1. Clean colour zones. Every face is given one zone: coat, points (mane, tail, lower legs), tack,
    the jockey's skin, his kit (breeches, boots, gloves, goggles), and the silks (body, sleeves,
    cap). Coat, points and skin are carried as vertex colours (R, G, B) on the main material instead
    of a texture mask, so a colour stops exactly where its zone stops: no coat on the jockey's chin,
    no cap colour down his neck, no sleeve colour on his gloves, no jacket flecks on his breeches,
    no grey speckles in the mane.
 2. A new silks layout with room between the zones (body, two sleeves, cap as a disc), painted by
    tools/silks/make_silks_v2.py, so colours can't bleed from one zone into the next.
 3. A new, smooth cap with a proper peak, replacing the blocky one.
 4. The jockey's jacket and breeches smoothed (the crumpled facets ironed out).
 5. A jockey rig: hips, back, neck, head, arms, hands and a whip, with riding clips (quiet, push,
    drive, whip) and small "variety" poses, so each jockey can sit a little differently.
 6. A better gallop: tail swing, a stronger head and neck nod, more weight through the back, and
    variety poses for head carriage.
 7. Three detail levels: close (smoothed, more triangles), race, and far (light).
"""
import bpy, bmesh, sys, os, math, json, struct, io
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
from PIL import Image

ROOT = os.path.abspath(os.environ.get("REPO", "."))
SRC = os.path.join(ROOT, "assets/models/master/racehorse_master.blend")
ORIG = os.path.join(ROOT, "assets/models/source/racehorse_3d_model_Clone1.glb")      # the untouched Tripo model
NEUTRAL = os.path.join(ROOT, "race-view/assets/model/racehorse-3d-model-clone1-basecolor.jpg")   # v1's grey texture
OUT_TEX = os.path.join(ROOT, "assets/models/racehorse_v2_basecolor.jpg")
OUT_SHADE = os.path.join(ROOT, "assets/models/racehorse_v2_silks_shading.png")
MASK = os.path.join(ROOT, "assets/models/tint_masks/build-mask.png")
OUT_BLEND = os.path.join(ROOT, os.environ.get("OUT_BLEND", "assets/models/master/racehorse_v2.blend"))
OUT_GLB = os.path.join(ROOT, os.environ.get("OUT_GLB", "assets/models/racehorse_v2.glb"))
OUT_RIG = os.path.join(ROOT, "assets/models/racehorse_v2_rig.json")
STOP = os.environ.get("STOP", "")          # stop after a stage, for checking: zones, rig, anim
N, CYCLE = 48, 0.48                        # one stride: 48 frames at 100 fps

# Silks atlas (u right, v down from the top of the image; the glTF uv has v down too).
# Each zone has its own island with a gutter round it; make_silks_v2.py paints the same layout.
ATLAS = {
    "body":  (0.0, 0.0, 1.0, 0.47),          # x0, y0, w, h: u wraps right round the torso
    "left":  (0.04, 0.53, 0.26, 0.43),       # left sleeve: u round the arm, v shoulder -> cuff
    "right": (0.37, 0.53, 0.26, 0.43),
    "cap":   (0.82, 0.745, 0.155, 0.0),      # disc: centre x, centre y, radius (in u)
}

bpy.ops.wm.open_mainfile(filepath=SRC)
bpy.context.preferences.filepaths.save_version = 0      # no .blend1 backups
scene = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
src_obj = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("tripo")][0]
for o in list(bpy.data.objects):
    if o.name == "Icosphere":
        bpy.data.objects.remove(o)

# Work on a copy, in the rest pose.
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
obj = src_obj.copy(); obj.data = src_obj.data.copy(); obj.name = "racehorse_v2"
scene.collection.objects.link(obj)
bpy.data.objects.remove(src_obj)
me = obj.data
me.name = "racehorse_v2"
SILK = [i for i, m in enumerate(me.materials) if m.name == "silks"][0]

# ------------------------------------------------------------------ 1. weld and read the v1 zones
mask = np.asarray(Image.open(MASK).convert("RGB")).astype(float) / 255.0
MH = mask.shape[0]
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)       # the mesh came in many small patches
bm.to_mesh(me); bm.free()
if me.has_custom_normals:
    me.normals_split_custom_set([(0, 0, 0)] * len(me.loops))
for p in me.polygons:
    p.use_smooth = True
print("welded:", len(me.vertices), "verts,", len(me.polygons), "faces")


def face_data():
    uv = me.uv_layers["UVMap"].data
    C = np.array([p.center[:] for p in me.polygons])
    MI = np.array([p.material_index for p in me.polygons])
    return uv, C, MI


def mask_votes(p, uv):
    """Sample the v1 mask inside a face (away from its edges, where the gutters are)."""
    us = [uv[l].uv[:] for l in p.loop_indices]
    c = np.mean(us, axis=0)
    pts = [c] + [c + (np.array(a) - c) * 0.5 for a in us]
    r = g = b = 0
    for u, v in pts:
        m = mask[int((1 - v) % 1 * MH) % MH, int(u % 1 * MH) % MH]
        r += m[0] > 0.5; g += m[1] > 0.5 and m[0] <= 0.5; b += m[2] > 0.5 and m[0] <= 0.5 and m[1] <= 0.5
    return r, g, b, len(pts)


def adjacency():
    adj = [[] for _ in me.polygons]
    ef = {}
    for p in me.polygons:
        for ek in p.edge_keys:
            ef.setdefault(ek, []).append(p.index)
    for fs in ef.values():
        for a in fs:
            adj[a] += [b for b in fs if b != a]
    return adj


# ------------------------------------------------------------------ 2. jockey cuts: clean seams
def nrm(v):
    v = np.array(v, float); return v / np.linalg.norm(v)

HEAD = np.array((0.198, 0.0, 0.565))
RIM = ((0.20, 0.0, 0.551), nrm((-0.10, 0.0, 1.0)))           # cap rim, a little lower at the back
def wrist(s):                                                 # cuff seam, square to the forearm
    e, w = np.array((0.128, 0.074 * s, 0.488)), np.array((0.168, 0.050 * s, 0.450))
    return (tuple(w - (w - e) * 0.08), nrm(w - e))
CUTS = [RIM, wrist(1), wrist(-1)]
bm = bmesh.new(); bm.from_mesh(me)
for co_, no_ in CUTS:
    faces = [f for f in bm.faces if np.linalg.norm(np.array(f.calc_center_median()[:]) - np.array(co_)) < 0.09]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co_, plane_no=no_, dist=1e-6)
bm.to_mesh(me); bm.free()

# Every face's place on the original texture, found on the untouched Tripo model (same shape, same place).
blob = open(ORIG, "rb").read()
jl = struct.unpack("<I", blob[12:16])[0]; gj = json.loads(blob[20:20 + jl]); bin0 = 28 + jl
def glb_image(name_part):
    for im in gj["images"]:
        if name_part in (im.get("name") or "") or name_part in (im.get("uri") or ""):
            bv = gj["bufferViews"][im["bufferView"]]
            return Image.open(io.BytesIO(blob[bin0 + bv.get("byteOffset", 0): bin0 + bv.get("byteOffset", 0) + bv["byteLength"]])).convert("RGB")
ORIG_TEX = glb_image("basecolor")
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=ORIG)
imported = [o for o in bpy.data.objects if o not in before]
src = [o for o in imported if o.type == "MESH" and o.name.startswith("tripo")][0]
bpy.context.view_layer.update()
sm = src.data; mw = src.matrix_world
s_co = [mw @ v.co for v in sm.vertices]
s_uv = sm.uv_layers.active.data
s_tri = [tuple(p.vertices) for p in sm.polygons]
s_luv = [[tuple(s_uv[l].uv) for l in p.loop_indices] for p in sm.polygons]
s_tree = BVHTree.FromPolygons(s_co, s_tri)
def bary(P, A, B, Cc):
    v0, v1, v2 = B - A, Cc - A, P - A
    d00, d01, d11, d20, d21 = v0.dot(v0), v0.dot(v1), v1.dot(v1), v2.dot(v0), v2.dot(v1)
    den = d00 * d11 - d01 * d01 or 1e-12
    b1 = (d11 * d20 - d01 * d21) / den; b2 = (d00 * d21 - d01 * d20) / den
    return 1 - b1 - b2, b1, b2
ORIG_UV = {}                                    # loop index -> uv on the original texture
for p in me.polygons:
    hit = s_tree.find_nearest(Vector(p.center))
    if hit[2] is None: continue
    fi = hit[2]; A, B, Cc = (s_co[k] for k in s_tri[fi][:3]); ua, ub, uc = (Vector(t) for t in s_luv[fi][:3])
    for l in p.loop_indices:
        w0, w1, w2 = bary(me.vertices[me.loops[l].vertex_index].co, A, B, Cc)
        ORIG_UV[l] = tuple(ua * w0 + ub * w1 + uc * w2)
for o in imported:
    bpy.data.objects.remove(o, do_unlink=True)


uv, C, MI = face_data()
nF = len(me.polygons)
side = lambda P, plane: (P - np.array(plane[0])) @ plane[1]
adj = adjacency()

# v1 silks zones from where each silk face sits in the v1 layout
v1zone = np.full(nF, "", dtype=object)
for p in me.polygons:
    if p.material_index != SILK:
        continue
    r = 1 - np.mean([uv[l].uv[1] for l in p.loop_indices])
    v1zone[p.index] = "body" if r < 0.51 else "left" if r < 0.71 else "right" if r < 0.91 else "cap"

vg = {g.name: g.index for g in obj.vertex_groups}
# The jockey: the same selection pin_jockey.py used to bind him to the horse's back (silks, head, body)
co = np.array([v.co[:] for v in me.vertices])
vx, vy, vz = co.T
horse_v = np.zeros(len(me.vertices), bool); silk_v = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if p.material_index == SILK:
        silk_v[list(p.vertices)] = True; continue
    u_, v_ = np.mean([uv[l].uv[:] for l in p.loop_indices], axis=0)
    m = mask[int((1 - v_) % 1 * MH) % MH, int(u_ % 1 * MH) % MH]
    if m[0] > 0.5 or m[1] > 0.5:
        horse_v[list(p.vertices)] = True
mane_v = ~silk_v & (np.abs(vy) < 0.025) & (((vx > 0.16) & (vz < 0.48)) | ((vx > 0.185) & (np.abs(vz - (0.49 + (vx - 0.2) * 0.55)) < 0.022)))
crest_v = (np.abs(vy) < 0.04) & (vz < 0.49 + (vx - 0.2) * 0.55 + 0.03)
head_v = (np.linalg.norm(co - np.array([0.205, 0.0, 0.555]), axis=1) < 0.075) & (vz > 0.5) & ~crest_v & ~mane_v
body_v = ~horse_v & ~mane_v & (vz > 0.455) & (vx > -0.02) & (vx < 0.25) & (np.abs(vy) < 0.11)
# his body stops at his chest; further forward only his hands (on the reins) are his, not the horse's neck
_hands = np.array([[0.192, 0.045, 0.438], [0.168, 0.050, 0.450], [0.192, -0.045, 0.438], [0.168, -0.050, 0.450]])
_near_hand = np.min(np.linalg.norm(co[:, None, :] - _hands[None], axis=2), axis=1) < 0.035
body_v &= (vx < 0.19) | _near_hand
v_jockey = silk_v | head_v | body_v
v_head = head_v
x, y, z = C.T
lum = None
base = bpy.data.images["racehorse_3d_model_Clone1_basecolor"]
_px = np.array(base.pixels[:]).reshape(base.size[1], base.size[0], 4)[:, :, :3]
BH = _px.shape[0]
def tex_lum(p):
    u, v = np.mean([uv[l].uv[:] for l in p.loop_indices], axis=0)
    c = _px[int(v % 1 * BH) % BH, int(u % 1 * BH) % BH]      # Blender images are stored bottom row first
    return float(c @ np.array([0.2126, 0.7152, 0.0722]))

zone = np.full(nF, "", dtype=object)
face_head = np.zeros(nF, bool)
for p in me.polygons:
    i = p.index
    vs = list(p.vertices)
    if p.material_index == SILK:
        zone[i] = v1zone[i]
    elif v_jockey[vs].mean() > 0.5:
        zone[i] = "jockey"
        face_head[i] = v_head[vs].mean() > 0.5
    else:
        zone[i] = "horse"

# The helmet and face stay exactly as the original model has them (owner, 4 Nov, with his reference picture).
# The helmet: the old cap zone above the rim, plus his own head faces above the rim at the front (the peak's
# underside); recoloured by the cap's silks. Below the rim at the back is the jacket's collar.
old_cap = zone == "cap"
above_rim = side(C, RIM) > 0
near_head = np.linalg.norm(C - HEAD, axis=1) < 0.075
zone[old_cap & ~above_rim] = "collar"
zone[(zone == "jockey") & above_rim & face_head] = "cap"
# Gloves: sleeve beyond the cuff seam, and any silk on his hands
for s, nm in ((1, "left"), (-1, "right")):
    beyond = side(C, wrist(s)) > 0
    zone[(zone == nm) & beyond] = "glove"
    zone[(zone == "body") & beyond & (y * s > 0.0) & (x > 0.16) & (z < 0.47)] = "glove"

# Tidy: each silk zone keeps only its biggest connected piece; stray flecks take their neighbours' zone
def components(sel):
    seen = np.zeros(nF, bool); comps = []
    for i in np.where(sel)[0]:
        if seen[i]: continue
        st = [i]; seen[i] = True; c = []
        while st:
            a = st.pop(); c.append(a)
            for b in adj[a]:
                if sel[b] and not seen[b]: seen[b] = True; st.append(b)
        comps.append(c)
    return sorted(comps, key=len, reverse=True)

for nm in ("body", "left", "right"):
    comps = components(zone == nm)
    print(nm, "pieces", [len(c) for c in comps[:6]])
    for c in comps[1:]:
        for i in c:
            zone[i] = "jockey"                      # back to his kit: breeches, gloves or collar
# His own (non-silk) faces: skin on the face and neck, kit for the rest
for p in me.polygons:
    i = p.index
    if zone[i] != "jockey":
        continue
    if face_head[i]:
        zone[i] = "natural"                         # face, goggles, chin strap: the original painting
    else:
        zone[i] = "kit"

# Round his head, the original painting decides: the helmet is the painted helmet (blue, with its black band
# and peak edge), reached from the crown; jacket colours touching his jacket are the collar; skin and the
# dark of the goggles, strap and hair stay painted. (Faces, not pixels: the dark band is shared, so where a
# face is half helmet and half hair it still looks right, as the helmet's shading map keeps the dark.)
import colorsys
from collections import deque, Counter
OT = np.asarray(ORIG_TEX, np.float32) / 255.0; OH = OT.shape[0]
def orig_at(u, v):
    return OT[int((1 - v % 1) * OH) % OH, int(u % 1 * OH) % OH]
def orig_rgb(p):
    ls = [l for l in p.loop_indices if l in ORIG_UV]
    if not ls: return None
    uvs = np.array([ORIG_UV[l] for l in ls]); c = uvs.mean(0)
    return np.median([orig_at(*c)] + [orig_at(*(0.6 * q + 0.4 * c)) for q in uvs], axis=0)
def paint_class(rgb):
    h, s, v = colorsys.rgb_to_hsv(*rgb); h *= 360
    if v < 0.2 or (v < 0.3 and s < 0.35): return "dark"
    if 185 <= h <= 250 and s > 0.3: return "blue"
    if 20 <= h <= 50 and s > 0.6 and v > 0.5: return "orange"
    if ((h < 20 or h > 340) and s > 0.7) or 260 <= h <= 340: return "pinkred"
    return "skin"
hreg = (np.linalg.norm(C - HEAD, axis=1) < 0.09) & np.isin(zone, ["cap", "natural", "collar", "kit"])
pcls = {}
for i in np.where(hreg)[0]:
    rgb = orig_rgb(me.polygons[int(i)])
    if rgb is not None: pcls[int(i)] = paint_class(rgb)
crown = max((i for i, k in pcls.items() if k == "blue" and above_rim[i]), key=lambda i: C[i, 2])
helmet = {crown: 0}; q = deque([crown])
while q:                                            # blue, and up to two faces of dark beyond it (band, peak edge)
    a = q.popleft()
    for b in adj[a]:
        if b in helmet or b not in pcls or not above_rim[b]: continue
        if pcls[b] == "blue": d = 0
        elif pcls[b] == "dark" and helmet[a] < 2: d = helmet[a] + 1
        else: continue
        helmet[b] = d; q.append(b)
jacketish = {i for i, k in pcls.items() if i not in helmet and k in ("blue", "orange", "pinkred")}
collar = set(); seen = set()
for i in jacketish:                                 # a patch of jacket colour joins the collar only if it meets the jacket
    if i in seen: continue
    comp, st = [], [i]; seen.add(i)
    while st:
        a = st.pop(); comp.append(a)
        for b in adj[a]:
            if b in jacketish and b not in seen: seen.add(b); st.append(b)
    if any(zone[b] in ("body", "left", "right") for a in comp for b in adj[a]):
        collar.update(comp)
for i in pcls:
    zone[i] = "cap" if i in helmet else "collar" if i in collar else "natural"
for _ in range(2):                                  # lone faces take their neighbours' zone
    flip = {}
    for i in pcls:
        nb = [zone[b] for b in adj[i] if b in pcls]
        if nb:
            k, n = Counter(nb).most_common(1)[0]
            if k != zone[i] and n >= max(2, len(nb) - 1): flip[i] = k
    for i, k in flip.items(): zone[i] = k
print("head by the painting:", dict(Counter(zone[i] for i in pcls)), "painted classes:", dict(Counter(pcls.values())))

# Horse: coat, points or tack, from the v1 mask sampled inside each face, then tidied by neighbours
hz = np.full(nF, "", dtype=object)
for p in me.polygons:
    if zone[p.index] != "horse":
        continue
    r, g, b, n = mask_votes(p, uv)
    hz[p.index] = "coat" if r >= n / 2 else "points" if g >= n / 2 else "tack"
# The mane: all hair along the crest of the neck is points (v1 left much of it untinted, so dark
# horses showed pale manes). The jockey's face and hands are kept out of it.
mane = np.isin(zone, ["horse", "kit"]) & ~face_head & (np.abs(y) < 0.034) & (x > 0.155) & (x < 0.40) & (z > 0.445 + (x - 0.155) * 0.3)
zone[mane] = "horse"
# ...but only the hair: the band is wider than the mane, and the skin on top of the neck under it is coat. The
# original painting tells them apart (the mane is painted black and grey, the neck bay brown); dark mane on top of
# the neck caught the sun as a pale grey patch.
def paint_coat(rgb):                                 # warm brown, not the mane's black and grey highlights
    h, s_, v = colorsys.rgb_to_hsv(*rgb)
    return v > 0.2 and s_ > 0.35 and (h * 360 < 50 or h * 360 > 345)
_neck = 0
for i in np.where(mane)[0]:
    rgb = orig_rgb(me.polygons[int(i)])
    if rgb is not None and paint_coat(rgb):
        hz[i] = "coat"; mane[i] = False; _neck += 1
    else:
        hz[i] = "points"
print("mane band: hair", int(mane.sum()), "neck under it (coat)", _neck)
# The tail: everything bound to the tail bones
TAIL = {vg["bone_%d" % k] for k in range(34, 41)}
for p in me.polygons:
    if zone[p.index] != "horse":
        continue
    tw = 0.0
    for v in p.vertices:
        tw += sum(g.weight for g in me.vertices[v].groups if g.group in TAIL)
    if tw / len(p.vertices) > 0.6:
        hz[p.index] = "points"
# Untinted patches on the neck, head and quarters were gaps in v1's mask, not tack: the tack that stays
# untinted (saddle, saddle cloth, girth, number cloth) is all round the middle of the horse.
hz[(zone == "horse") & (hz == "tack") & ((x > 0.17) | (x < -0.17)) & ~mane] = "coat"
# His boots (dark, outside the horse's flanks under the saddle) are his kit: no coat colour on them.
for p in me.polygons:
    i = p.index
    if zone[i] == "horse" and -0.03 < x[i] < 0.17 and 0.26 < z[i] < 0.47 and abs(y[i]) > 0.07 and tex_lum(p) < 0.2:
        zone[i] = "kit"
keep = mane.copy()
for _ in range(4):                                   # majority of the neighbours wins, a few times over
    new = hz.copy()
    for i in np.where((zone == "horse") & ~keep)[0]:
        nb = [hz[j] for j in adj[i] if zone[j] == "horse"]
        if len(nb) >= 2:
            vals, cnt = np.unique(nb, return_counts=True)
            if cnt.max() >= len(nb) * 0.66 and vals[cnt.argmax()] != hz[i]:
                new[i] = vals[cnt.argmax()]
    hz = new
for i in np.where(zone == "horse")[0]:
    zone[i] = hz[i]
from collections import Counter
print("zones:", dict(Counter(zone)))

# His chin and throat sit on the mane's crest line, so the mane band above took them. The faces joined to his
# face and above the top of the mane are his again (painted, and on his head bone); the cut further down
# parts them from the mane, so his head can move without dragging a dark web of mane under his chin.
def chin_box(i):
    return zone[i] in ("points", "coat", "tack") and abs(y[i]) < 0.012 and 0.175 < x[i] < 0.245 and z[i] > 0.49 + (x[i] - 0.2) * 0.55 + 0.012
chin = [i for i in range(nF) if chin_box(i) and any(zone[j] == "natural" for j in adj[i])]
q = deque(chin); chin = set(chin)
while q:
    a = q.popleft()
    for b in adj[a]:
        if b not in chin and chin_box(b): chin.add(b); q.append(b)
for i in chin:
    zone[i] = "natural"
print("chin and throat faces back from the mane:", len(chin))
# White flecks in his jacket: a few faces of his own mesh (an armpit, inside an elbow) sit in the silks but
# were never part of them. Small islands of kit with only silks round them join the silks, borrowing the
# silks mapping and fabric creases from their neighbours at each shared corner.
uvd = me.uv_layers["UVMap"].data; col0 = me.color_attributes["Color"]
at_vert = {}
for p in me.polygons:
    if p.material_index == SILK and zone[p.index] in ("body", "left", "right"):
        for l in p.loop_indices:
            at_vert.setdefault((zone[p.index], me.loops[l].vertex_index), (tuple(uvd[l].uv), tuple(col0.data[l].color)))
islands = 0
for comp in components(zone == "kit"):
    if len(comp) > 10: continue
    ring = Counter(zone[b] for a in comp for b in adj[a] if zone[b] != "kit")
    if not ring or sum(ring[k] for k in ("body", "left", "right")) < 0.8 * sum(ring.values()): continue
    k = max(("body", "left", "right"), key=lambda q: ring[q])
    for a in comp:
        p = me.polygons[a]
        got = [at_vert.get((k, me.loops[l].vertex_index)) for l in p.loop_indices]
        known = [g for g in got if g]
        if not known: continue
        mu = tuple(np.mean([g[0] for g in known], axis=0)); mc = tuple(np.mean([g[1] for g in known], axis=0))
        for l, g in zip(p.loop_indices, got):
            uvd[l].uv = g[0] if g else mu; col0.data[l].color = g[1] if g else mc
        p.material_index = SILK; zone[a] = k
    islands += 1
print("kit islands in the silks joined them:", islands)


# ------------------------------------------------------------------ 3. remove the old cap, move faces to their materials
mat_main = me.materials[1 - SILK]; mat_main.name = "racehorse_v2_main"
mat_silk = me.materials[SILK]; mat_silk.name = "racehorse_v2_silks"
MAIN = 1 - SILK
# a plain dark and a plain light spot on the main texture, for faces that leave the silks
def spot(pred):
    best = None
    for p in me.polygons:
        if p.material_index == MAIN and pred(p) and p.area > 2e-5:
            l = tex_lum(p)
            if best is None or abs(l - pred.want) < best[0]:
                best = (abs(l - pred.want), tuple(np.mean([uv[q].uv[:] for q in p.loop_indices], axis=0)))
    return best[1]
class Want:
    def __init__(self, zn, want): self.zn, self.want = zn, want
    def __call__(self, p): return zone[p.index] == self.zn
DARK = spot(Want("kit", 0.05))
LIGHT = spot(Want("kit", 0.92))
for p in me.polygons:
    zn = zone[p.index]
    if zn == "natural":                                   # his face: back to its place on the painting
        p.material_index = MAIN
        for l in p.loop_indices:
            if l in ORIG_UV: uv[l].uv = ORIG_UV[l]
    elif p.material_index == SILK and zn not in ("body", "left", "right", "cap", "collar"):
        p.material_index = MAIN
        target = DARK if zn == "glove" else LIGHT
        for l in p.loop_indices:
            uv[l].uv = target

# vertex colours: main = (coat, points, skin) masks; silks = crease shade (kept from v1)
col = me.color_attributes["Color"]
shade = np.array([c.color[:] for c in col.data])
for p in me.polygons:
    zn = zone[p.index]
    if p.material_index == MAIN:
        m = (1.0 if zn == "coat" else 0.0, 1.0 if zn == "points" else 0.0, 1.0 if zn == "natural" else 0.0, 1.0)
        for l in p.loop_indices:
            col.data[l].color = m

# Soft colour edges between coat and points (lower legs, mane), where the two meet on the horse:
# average the corner masks at each shared vertex, horse faces only.
uv, C, MI = face_data()
col = me.color_attributes["Color"]
cd = np.array([c.color[:] for c in col.data])
acc, cnt = {}, {}
lv = np.array([l.vertex_index for l in me.loops])
for p in me.polygons:
    if zone[p.index] in ("coat", "points"):              # tack doesn't dilute the coat (no pale halo round the reins)
        for l in p.loop_indices:
            k = lv[l]; acc[k] = acc.get(k, 0) + cd[l, :2]; cnt[k] = cnt.get(k, 0) + 1
for p in me.polygons:
    if zone[p.index] in ("coat", "points"):
        for l in p.loop_indices:
            k = lv[l]; a = acc[k] / cnt[k]
            col.data[l].color = (a[0], a[1], 0.0, 1.0)


# ------------------------------------------------------------------ 4. silks layout v2 and a smoother jacket
# Body and sleeves keep v1's unwrap (round the torso, round each arm), moved into their own islands.
uv = me.uv_layers["UVMap"].data
for p in me.polygons:
    zn = zone[p.index]
    if zn not in ("body", "left", "right"):
        continue
    r0, r1 = {"body": (0.0, 0.5), "left": (0.52, 0.70), "right": (0.72, 0.90)}[zn]
    X0, Y0, W, Hh = ATLAS[zn]
    for l in p.loop_indices:
        u_, bv = uv[l].uv
        t = ((1 - bv) - r0) / (r1 - r0)                  # 0 waist/shoulder .. 1 collar/cuff
        uv[l].uv = (X0 + W * u_, 1 - (Y0 + Hh * t))

# Iron the crumpled jacket and breeches: smooth his torso, arms and legs, keeping volume, and leaving
# alone every vertex that touches his face, his hands or the horse (so no seam opens).
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
cloth = {"body", "left", "right", "kit"}
movable = []
for v in bm.verts:
    zs = {zone[f.index] for f in v.link_faces}
    if (zs and zs <= cloth and v.co.z > 0.43 and v.co.x < 0.2 and v.is_manifold and not v.is_boundary
            and all(e.is_manifold for e in v.link_edges)):
        movable.append(v)
for _ in range(2):
    bmesh.ops.smooth_vert(bm, verts=movable, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(me); bm.free()
print("smoothed jockey vertices:", len(movable))


# ------------------------------------------------------------------ 4b. helmet and collar on the silks
# The helmet keeps its own shape; its faces take the cap's disc in the silks layout (crown in the middle, the
# rim round the edge, the peak at the rim's colour). The collar under the back of the helmet takes the top
# of the body's band.
uv = me.uv_layers["UVMap"].data
C = np.array([p.center[:] for p in me.polygons])
capf = [p for p in me.polygons if zone[p.index] == "cap"]
capv = sorted({v for p in capf for v in p.vertices})
cco = np.array([me.vertices[v].co[:] for v in capv])
Hc = np.array([cco[:, 0].mean() - 0.004, 0.0, RIM[0][2] - 0.004])
def sph(P):
    d = np.asarray(P) - Hc
    return np.arctan2(d[..., 1], d[..., 0]), np.arccos(np.clip(d[..., 2] / np.linalg.norm(d, axis=-1), -1, 1))
# the rim: helmet vertices shared with his face or collar, angle from the crown at each bearing round the head
other = {v for p in me.polygons if zone[p.index] in ("natural", "collar", "kit") for v in p.vertices}
rimv = np.array([me.vertices[v].co[:] for v in capv if v in other])
rph, rth = sph(rimv)
bins = np.linspace(-math.pi, math.pi, 37)
med = np.array([np.median(rth[(rph >= bins[k]) & (rph < bins[k + 1])]) if ((rph >= bins[k]) & (rph < bins[k + 1])).any() else np.nan for k in range(36)])
ok = ~np.isnan(med); cen = (bins[:-1] + bins[1:]) / 2
med = np.interp(cen, cen[ok], med[ok], period=2 * math.pi)
def th_rim(ph):
    return np.interp(ph, cen, med, period=2 * math.pi)
CXd, CYd, CRd = ATLAS["cap"][0], ATLAS["cap"][1], ATLAS["cap"][2]
for p in capf:
    p.material_index = SILK
    for l in p.loop_indices:
        P = np.array(me.vertices[me.loops[l].vertex_index].co[:])
        ph, th = sph(P)
        vv = float(min(1.0, th / th_rim(ph)))
        uv[l].uv = (CXd + CRd * vv * math.sin(ph), 1 - (CYd + CRd * vv * math.cos(ph)))
X0b, Y0b, Wb, Hb = ATLAS["body"]
for p in me.polygons:
    if zone[p.index] != "collar":
        continue
    p.material_index = SILK
    us = []
    for l in p.loop_indices:
        P = me.vertices[me.loops[l].vertex_index].co
        a = math.atan2(P.y, -(P.z - 0.51)) / (2 * math.pi)
        us.append((a + 0.25) % 1.0)
    if max(us) - min(us) > 0.5:
        us = [u_ + 1 if u_ < 0.5 else u_ for u_ in us]
    for l, u_ in zip(p.loop_indices, us):
        uv[l].uv = (X0b + Wb * u_, 1 - (Y0b + Hb * 0.985))
print("helmet faces:", len(capf), "collar faces:", int((zone == "collar").sum()))

# ------------------------------------------------------------------ 4c. textures: the face's painting back, and the silks' shading
# (1) The main texture: v1's grey texture, with the face, goggles and chin strap painted back from the original.
from PIL import ImageDraw, ImageFilter
base = Image.open(NEUTRAL).convert("RGB"); S_ = base.size[0]
orig_s = ORIG_TEX.resize(base.size, Image.LANCZOS)
mask = Image.new("L", base.size, 0); dr = ImageDraw.Draw(mask)
for p in me.polygons:
    if zone[p.index] == "natural":
        dr.polygon([(uv[l].uv[0] * S_, (1 - uv[l].uv[1]) * S_) for l in p.loop_indices], fill=255)
mask = mask.filter(ImageFilter.MaxFilter(5))
# where the painting shows the original jacket's or helmet's colours inside his face faces (a fleck of orange
# behind an ear, a stripe at the collar's edge), it is darkened to his hair's colour, so no owner sees them
fo = np.asarray(orig_s, dtype=np.float32) / 255.0
mx, mn = fo.max(2), fo.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r_, g_, b_ = fo[..., 0], fo[..., 1], fo[..., 2]
hue = np.degrees(np.arctan2(np.sqrt(3) * (g_ - b_), 2 * r_ - g_ - b_)) % 360
key = (((hue > 15) & (hue < 50) & (sat > 0.65) & (mx > 0.55)) | ((hue > 260) & (hue < 340) & (sat > 0.35) & (mx > 0.35))
       | ((hue > 185) & (hue < 250) & (sat > 0.45) & (mx > 0.3)) | (((hue < 15) | (hue > 345)) & (sat > 0.72) & (mx > 0.45))) & (np.asarray(mask) > 0)
fo[key] = (0.13, 0.11, 0.10)
print("face texels darkened from jacket or helmet colours:", int(key.sum()))
orig_s = Image.fromarray((fo * 255).astype(np.uint8), "RGB")
Image.composite(orig_s, base, mask).save(OUT_TEX, quality=90)
print("main texture with the face painted back:", OUT_TEX)
fa = np.asarray(orig_s, dtype=np.float32)[np.asarray(mask) > 128] / 255.0
fa = fa[fa @ np.array([0.2126, 0.7152, 0.0722]) > 0.3]       # skin, not goggles or strap
print("face skin, average (horse-v2.js SKIN_REF): #%02x%02x%02x" % tuple(int(round(c * 255)) for c in np.median(fa, axis=0)))

# (2) The silks' shading: one shared grey map in the silks layout, multiplied with any owner's silks. Only the
# helmet is painted on it: the original's light and shade, so the helmet keeps its seams, dark rim band and peak
# edge as in the reference. The jacket and sleeves keep v1's crease shading in their vertex colours (the
# original's texture there is its orange and blue stripes, which would print through every owner's silks).
orig_np = np.asarray(ORIG_TEX, dtype=np.float32) / 255.0
lumw = np.array([0.2126, 0.7152, 0.0722], np.float32)
SH = 1024
shade = np.zeros((SH, SH), np.float32); have = np.zeros((SH, SH), bool); zid = np.full((SH, SH), -1, np.int8)
ZI = {"cap": 2}
def sample(img, U, V):
    h, w = img.shape[:2]
    xs = np.clip((U % 1.0) * w, 0, w - 1).astype(int); ys = np.clip((1 - V % 1.0) * h, 0, h - 1).astype(int)
    return img[ys, xs] @ lumw
for p in me.polygons:
    zn = zone[p.index]
    if zn not in ZI or p.material_index != SILK: continue
    ls = list(p.loop_indices)
    if any(l not in ORIG_UV for l in ls): continue
    img = orig_np
    for k in range(1, len(ls) - 1):
        tri = [ls[0], ls[k], ls[k + 1]]
        D = np.array([(uv[l].uv[0] * SH, (1 - uv[l].uv[1]) * SH) for l in tri])
        Sv = np.array([ORIG_UV[l] for l in tri])
        x0, y0 = np.floor(D.min(0)).astype(int); x1, y1 = np.ceil(D.max(0)).astype(int)
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        px, py = xs.ravel() + 0.5, ys.ravel() + 0.5
        (ax, ay), (bx, by), (cx, cy) = D
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-9: continue
        w0 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
        w1 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -0.02) & (w1 >= -0.02) & (w2 >= -0.02)
        if not inside.any(): continue
        U = w0 * Sv[0, 0] + w1 * Sv[1, 0] + w2 * Sv[2, 0]; V = w0 * Sv[0, 1] + w1 * Sv[1, 1] + w2 * Sv[2, 1]
        X = xs.ravel()[inside] % SH; Y = np.clip(ys.ravel()[inside], 0, SH - 1)
        shade[Y, X] = sample(img, U[inside], V[inside]); have[Y, X] = True; zid[Y, X] = ZI[zn]
for k in range(4):                                  # each zone to about 1 on its usual fabric, darker in the creases and bands
    sel = have & (zid == k)
    if sel.any():
        shade[sel] = np.clip(shade[sel] / np.percentile(shade[sel], 80), 0.12, 1.0)
for _ in range(24):                                 # fill the gutters from the nearest painted texel
    if have.all(): break
    acc = np.zeros_like(shade); cnt = np.zeros_like(shade)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        acc += np.roll(np.roll(np.where(have, shade, 0), dy, 0), dx, 1); cnt += np.roll(np.roll(have, dy, 0), dx, 1)
    grow = ~have & (cnt > 0)
    shade[grow] = acc[grow] / cnt[grow]; have |= grow
shade[~have] = 1.0
yy, xx = np.mgrid[0:SH, 0:SH]
shade[np.hypot((xx + 0.5) / SH - CXd, (yy + 0.5) / SH - CYd) > CRd + 0.02] = 1.0   # only the helmet's disc
Image.fromarray((shade * 255).astype(np.uint8), "L").save(OUT_SHADE, optimize=True)
print("silks shading map:", OUT_SHADE)
col = me.color_attributes["Color"]
for p in me.polygons:                               # helmet: plain white (its shade is on the map)
    if p.material_index == SILK and zone[p.index] == "cap":
        for l in p.loop_indices:
            col.data[l].color = (1.0, 1.0, 1.0, 1.0)
    elif p.material_index == SILK and zone[p.index] == "collar":
        for l in p.loop_indices:                    # collar: dark at each corner where the painting has the strap or shadow
            f = 1.0
            if l in ORIG_UV:
                f = float(np.clip(max(orig_at(*ORIG_UV[l])) / 0.35, 0.1, 1.0))
            g = f ** 2.2                                # vertex colours are linear
            col.data[l].color = (g, g, g, 1.0)

FACE_ZONE = list(zone)
if STOP == "zones":
    for nm, c in (("body", (0.85, 0.1, 0.1)), ("left", (0.1, 0.7, 0.1)), ("right", (0.95, 0.85, 0.1)), ("natural", (1, 0.75, 0.6)), ("collar", (0.6, 0.1, 0.4)),
                  ("kit", (0.95, 0.95, 0.95)), ("coat", (0.6, 0.35, 0.2)), ("points", (0.1, 0.08, 0.07)), ("tack", (0.5, 0.5, 0.6)), ("cap", (0.1, 0.3, 1.0)), ("glove", (0.2, 0.2, 0.2))):
        m = bpy.data.materials.new("z_" + nm); m.diffuse_color = c + (1,); me.materials.append(m)
    names = [m.name for m in me.materials]
    for p in me.polygons:
        p.material_index = names.index("z_" + FACE_ZONE[p.index])
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    print("saved zones check", OUT_BLEND); raise SystemExit


# ------------------------------------------------------------------ 5. the jockey's rig
# Bones ride on the horse's back (Spine_4), as v1's jockey did. His legs stay in the irons (on Spine_4);
# his seat, back, head, arms, hands and whip move. v1's two arm bones are replaced.
J = {   # name: (head, tail, parent)
    "jky_hips":   ((0.000, 0.0, 0.495), (0.070, 0.0, 0.522), "tripo::Spine_4"),
    "jky_chest":  ((0.070, 0.0, 0.522), (0.150, 0.0, 0.545), "jky_hips"),
    "jky_head":   ((0.168, 0.0, 0.540), (0.205, 0.0, 0.585), "jky_chest"),
}
ARMP = {}
for sd, s_ in (("L", 1), ("R", -1)):
    S0 = Vector((0.150, 0.062 * s_, 0.535)); E0 = Vector((0.128, 0.074 * s_, 0.488))
    W0 = Vector((0.168, 0.050 * s_, 0.450)); T0 = Vector((0.192, 0.045 * s_, 0.438))
    ARMP[sd] = (S0, E0, W0, T0)
    J["jky_arm." + sd] = (S0[:], E0[:], "jky_chest")
    J["jky_forearm." + sd] = (E0[:], W0[:], "jky_arm." + sd)
    J["jky_hand." + sd] = (W0[:], T0[:], "jky_forearm." + sd)
# the whip: held in his right fist, the shaft down and back across the horse's shoulder
WHIP_GRIP = Vector((0.186, -0.047, 0.441))
WHIP_DIR = Vector((-0.55, -0.22, -0.80)).normalized()
WHIP_LEN = 0.205
J["jky_whip"] = (WHIP_GRIP[:], (WHIP_GRIP + WHIP_DIR * WHIP_LEN)[:], "jky_hand.R")

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
for old in [b for b in eb if b.name.startswith("jockey_")]:
    eb.remove(old)
for name, (h, t, par) in J.items():
    b = eb.new(name); b.head, b.tail = Vector(h), Vector(t); b.parent = eb[par]; b.use_connect = False
    b.roll = 0.0
bpy.ops.object.mode_set(mode="OBJECT")
for a in [a for a in bpy.data.actions if a.name.startswith("ride_")]:
    bpy.data.actions.remove(a)                                  # v1's arm-only riding clips
for g in [g for g in obj.vertex_groups if g.name.startswith("jockey_")]:
    obj.vertex_groups.remove(g)

# The whip itself: a tapered shaft with a small leather flap, bound to the whip bone.
wb = bmesh.new()
wuv = wb.loops.layers.uv.new("UVMap"); wcol = wb.loops.layers.color.new("Color")
side_v = WHIP_DIR.orthogonal().normalized(); side_w = WHIP_DIR.cross(side_v).normalized()
rings = []
for k, (t, r) in enumerate([(-0.012, 0.0028), (0.0, 0.0026), (0.35, 0.0019), (0.75, 0.0013), (0.95, 0.0011)]):
    c = WHIP_GRIP + WHIP_DIR * (WHIP_LEN * t)
    rings.append([wb.verts.new(c + (side_v * math.cos(a) + side_w * math.sin(a)) * r) for a in np.linspace(0, 2 * math.pi, 7)[:-1]])
for k in range(len(rings) - 1):
    for i in range(6):
        wb.faces.new((rings[k][i], rings[k][(i + 1) % 6], rings[k + 1][(i + 1) % 6], rings[k + 1][i]))
cap_a = wb.verts.new(WHIP_GRIP + WHIP_DIR * (WHIP_LEN * -0.016)); cap_b = wb.verts.new(WHIP_GRIP + WHIP_DIR * (WHIP_LEN * 0.95))
for i in range(6):
    wb.faces.new((rings[0][(i + 1) % 6], rings[0][i], cap_a)); wb.faces.new((rings[-1][i], rings[-1][(i + 1) % 6], cap_b))
fl = [WHIP_GRIP + WHIP_DIR * (WHIP_LEN * 0.95) + side_v * a + WHIP_DIR * b for a, b in ((-0.004, 0), (0.004, 0), (0.004, 0.028), (-0.004, 0.028))]
fv = [wb.verts.new(q) for q in fl]
wb.faces.new(fv); wb.faces.new(list(reversed([wb.verts.new(q + side_w * 0.0005) for q in fl])))
for f in wb.faces:
    for l in f.loops:
        l[wuv].uv = DARK; l[wcol] = (0, 0, 0, 1)
whip_me = bpy.data.meshes.new("whip"); wb.to_mesh(whip_me); wb.free()
whip_obj = bpy.data.objects.new("whip", whip_me); scene.collection.objects.link(whip_obj)
whip_me.materials.append(mat_main); whip_me.materials.append(mat_silk)
for p in whip_me.polygons:
    p.material_index = 0; p.use_smooth = True
gw = whip_obj.vertex_groups.new(name="jky_whip"); gw.add(list(range(len(whip_me.vertices))), 1.0, "REPLACE")
n_before = len(me.polygons)
bpy.ops.object.select_all(action="DESELECT")
whip_obj.select_set(True); obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()
FACE_ZONE += ["whip"] * (len(me.polygons) - n_before)
me = obj.data

# His hands were modelled fused to the reins and mane: cut them apart, so a hand can push, or lift the
# whip, without dragging a sheet of rein or mane with it.
fz = np.array(FACE_ZONE, dtype=object)
HORSEZ = {"coat", "points", "tack"}
def hand_seg_d(P, sd):
    S0, E0, W0, T0 = [np.array(q[:]) for q in ARMP[sd]]
    a, b = W0 - (W0 - E0) * 0.5, T0 + (T0 - W0) * 0.8
    ab = b - a; t = np.clip(((P - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(P - (a + t[:, None] * ab), axis=1)
FC = np.array([p.center[:] for p in me.polygons])
arm_face = np.isin(fz, ["left", "right", "glove"])
for sd, sg in (("L", 1), ("R", -1)):
    arm_face |= (fz == "kit") & (hand_seg_d(FC, sd) < 0.03) & (FC[:, 1] * sg > 0.012)
FACE_ARM = arm_face
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
cut = [e for e in bm.edges if len(e.link_faces) >= 2 and
       {("a" if arm_face[f.index] else "x" if fz[f.index] in ("left", "right", "body", "glove") else "h") for f in e.link_faces} >= {"h", "a"}]
# and his head (face, helmet, collar) from the horse's mane and neck, where they were modelled touching
HEADZ = {"natural", "cap", "collar"}
cut2 = [e for e in bm.edges if len(e.link_faces) >= 2 and {fz[f.index] for f in e.link_faces} & HEADZ and {fz[f.index] for f in e.link_faces} & HORSEZ]
bmesh.ops.split_edges(bm, edges=list(set(cut) | set(cut2)))
bm.to_mesh(me); bm.free()
print("hand/rein edges cut:", len(cut), "head/mane edges cut:", len(cut2))

# Weights. Head (cap, face, neck under the cap) on the head bone; sleeves and gloves along each arm;
# the jacket and seat between hips and chest; his legs stay with the horse (Spine_4).
fz = np.array(FACE_ZONE, dtype=object)
co = np.array([v.co[:] for v in me.vertices])
vzones = [set() for _ in me.vertices]
for p in me.polygons:
    for v in p.vertices:
        vzones[v].add(fz[p.index])
vg = {g.name: g for g in obj.vertex_groups}
for name in J:
    if name not in vg:
        vg[name] = obj.vertex_groups.new(name=name)
spine4 = vg["tripo::Spine_4"]
def seg_t(p, a, b):
    ab = b - a; t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1); return t, np.linalg.norm(p - (a + t[:, None] * ab), axis=1)
sm = lambda e0, e1, x: np.clip((x - e0) / (e1 - e0), 0, 1) ** 2 * (3 - 2 * np.clip((x - e0) / (e1 - e0), 0, 1))
jockey_v = np.array([bool(z_ & {"body", "left", "right", "cap", "collar", "natural", "glove"}) or
                     (("kit" in z_) and v_ok) for z_, v_ok in zip(vzones, (co[:, 2] > 0.43) & (co[:, 0] > -0.06) & (co[:, 0] < 0.25) & (np.abs(co[:, 1]) < 0.12))])
whip_v = np.array(["whip" in z_ for z_ in vzones])
W = {n: np.zeros(len(co)) for n in J}
W["tripo::Spine_4"] = np.zeros(len(co))
x_, y_, z_ = co.T
headish = np.array([bool(zz & {"cap", "natural"}) for zz in vzones]) | (jockey_v & (np.linalg.norm(co - np.array([0.198, 0, 0.553]), axis=1) < 0.05) & (x_ > 0.158))
# arms: nearest arm, distance along it
armw = {}
for sd in ("L", "R"):
    S0, E0, W0, T0 = [np.array(q[:]) for q in ARMP[sd]]
    sgn = 1 if sd == "L" else -1
    tu, du = seg_t(co, S0, E0); tf, df = seg_t(co, E0, W0); th, dh = seg_t(co, W0, T0 + (T0 - W0) * 0.6)
    sleeve = np.array([bool(zz & {"left" if sd == "L" else "right"}) for zz in vzones])
    glove = np.array(["glove" in zz for zz in vzones])
    d = np.stack([du, df, dh]); k = d.argmin(0); dmin = d.min(0)
    armface_v = np.zeros(len(co), bool)
    for p in me.polygons:
        if FACE_ARM[p.index]:
            for v in p.vertices: armface_v[v] = True
    on_arm = armface_v & (y_ * sgn > 0.0) & ~headish & ~np.array([z_set <= HORSEZ for z_set in vzones])
    # distance along the arm (shoulder 0 -> fingertips); joints blend over a couple of centimetres either
    # side, so the crease of the elbow and the wrist bend smoothly whichever bone is nearer
    la, lb = np.linalg.norm(E0 - S0), np.linalg.norm(W0 - E0)
    sarm = np.where(k == 0, tu * la, np.where(k == 1, la + tf * lb, la + lb + th * np.linalg.norm(T0 - W0) * 1.6))
    un = lambda v: v / np.linalg.norm(v)
    n_el = un(un(W0 - E0) - un(S0 - E0)); n_wr = un(un(T0 - W0) - un(E0 - W0))    # planes halving each joint's angle
    w_fo_in = sm(-0.014, 0.014, (co - E0) @ n_el); w_ha_in = sm(-0.008, 0.010, (co - W0) @ n_wr)
    w_up = 1 - w_fo_in; w_ha = w_ha_in; w_fo = w_fo_in * (1 - w_ha_in)
    fade = sm(0.0, 0.3 * la, sarm)                    # the top of the sleeve fades into the chest
    armw[sd] = (on_arm, w_up * fade, w_fo, w_ha, (1 - fade) * w_up)
for sd in ("L", "R"):
    on_arm, wu, wf, wh, wc = armw[sd]
    W["jky_arm." + sd][on_arm] = wu[on_arm]; W["jky_forearm." + sd][on_arm] = wf[on_arm]; W["jky_hand." + sd][on_arm] = wh[on_arm]
    W["jky_chest"][on_arm] += wc[on_arm]
any_arm = armw["L"][0] | armw["R"][0]
torso = jockey_v & ~any_arm & ~headish & ~whip_v
legs = sm(0.462, 0.482, z_) * (1 - sm(0.115, 0.14, x_) * (z_ < 0.49))        # thighs and knees stay with the irons
hips_chest = sm(0.03, 0.11, x_)
W["jky_chest"][torso] += (legs * hips_chest)[torso]
W["jky_hips"][torso] += (legs * (1 - hips_chest))[torso]
W["tripo::Spine_4"][torso] += (1 - legs)[torso]
# the collar between chest and head
neckb = sm(0.150, 0.170, x_) * (z_ > 0.52)
W["jky_head"][headish] = 1.0
coll = torso & (neckb > 0)
for n in ("jky_chest", "jky_hips", "tripo::Spine_4"):
    W[n][coll] *= (1 - neckb[coll])
W["jky_head"][coll] += neckb[coll]
W["jky_whip"][whip_v] = 1.0
moved = jockey_v | whip_v
tot = sum(W.values())
print("jockey vertices re-bound:", int(moved.sum()), "unbound:", int((moved & (tot < 1e-6)).sum()))
ids = np.where(moved)[0]
for g in obj.vertex_groups:
    g.remove(ids.tolist())
for n, w in W.items():
    for i in ids:
        if w[i] > 1e-4 and tot[i] > 1e-6:
            vg[n].add([int(i)], float(w[i] / tot[i]), "REPLACE")
    lost = ids[tot[ids] < 1e-6]
spine4.add([int(i) for i in ids[tot[ids] < 1e-6]], 1.0, "REPLACE")

# ------------------------------------------------------------------ 6. riding clips and variety poses
PEAK = 0.12                                            # matches the horse's head nod (lowest)
pb = arm.pose.bones
REST = {n: arm.data.bones[n].matrix_local.copy() for n in J}
def about(p, axis, deg):
    p = Vector(p)
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-p)
def aim(rest, head, d0, d1):
    """Armature-space matrix for a bone whose rest matrix is 'rest', moved to 'head' and turned so its
    rest direction d0 now points along d1."""
    q = Vector(d0).normalized().rotation_difference(Vector(d1).normalized()) @ rest.to_quaternion()
    return Matrix.Translation(Vector(head)) @ q.to_matrix().to_4x4()
def ik(S, a, b, T, pole):
    d = (T - S); L = min(d.length, a + b - 1e-4); u = d.normalized()
    v = (pole - S); v = (v - u * v.dot(u)).normalized()
    ca = (a * a + L * L - b * b) / (2 * a * L); sa = math.sqrt(max(0.0, 1 - ca * ca))
    return S + (u * ca + v * sa) * a, S + u * L
def set_pose(P):
    """P: hips (dx, dz, pitch), chest pitch, head pitch, hand targets L/R (offsets from rest, horse frame),
    elbow out L/R (metres), whip turn (degrees), hand turn R."""
    Dh = Matrix.Translation(Vector((P["hx"], 0, P["hz"]))) @ about(J["jky_hips"][0], (0, 1, 0), P["hp"])
    Dc = Dh @ about(J["jky_chest"][0], (0, 1, 0), P["cp"])
    Dhd = Dc @ about(J["jky_head"][0], (0, 1, 0), P["dp"])
    pb["jky_hips"].matrix = Dh @ REST["jky_hips"]; bpy.context.view_layer.update()
    pb["jky_chest"].matrix = Dc @ REST["jky_chest"]; bpy.context.view_layer.update()
    pb["jky_head"].matrix = Dhd @ REST["jky_head"]; bpy.context.view_layer.update()
    for sd in ("L", "R"):
        S0, E0, W0, T0 = ARMP[sd]
        S = Dc @ S0
        Wt = W0 + Vector(P["w" + sd])
        a, b = (E0 - S0).length, (W0 - E0).length
        pole = Dc @ (E0 + Vector((-0.02, 0.0, 0.0)) + Vector((0, 1 if sd == "L" else -1, 0)) * (0.02 + P["eo" + sd]))
        E, Wr = ik(S, a, b, Wt, pole)
        pb["jky_arm." + sd].matrix = aim(REST["jky_arm." + sd], S, E0 - S0, E - S); bpy.context.view_layer.update()
        pb["jky_forearm." + sd].matrix = aim(REST["jky_forearm." + sd], E, W0 - E0, Wr - E); bpy.context.view_layer.update()
        hd = (T0 - W0)
        hm = aim(REST["jky_hand." + sd], Wr, hd, (Matrix.Rotation(math.radians(P.get("ht" + sd, 0.0)), 3, Vector((0, 1, 0))) @ ((Wr - E).normalized() * 0.3 + hd.normalized())))
        pb["jky_hand." + sd].matrix = hm; bpy.context.view_layer.update()
    # whip: turned about the fist (relative to the hand)
    wr = REST["jky_whip"]; hand = pb["jky_hand.R"].matrix @ REST["jky_hand.R"].inverted()
    pb["jky_whip"].matrix = hand @ about(WHIP_GRIP, (0, 1, 0), P["wh"]) @ about(WHIP_GRIP, (0, 0, 1), P.get("wy", 0.0)) @ wr
    bpy.context.view_layer.update()
BASE = dict(hx=0.0, hz=0.0, hp=0.0, cp=0.0, dp=0.0, wL=(0, 0, 0), wR=(0, 0, 0), eoL=0.0, eoR=0.0, wh=0.0)
JKEYS = list(J)
def key_all(f):
    for n in JKEYS:
        pb[n].keyframe_insert("rotation_quaternion", frame=f)
        pb[n].keyframe_insert("location", frame=f)
def new_action(name):
    a = bpy.data.actions.new(name); a.use_fake_user = True
    arm.animation_data.action = a
    return a
NECK = Vector((0.85, 0.0, -0.45)).normalized()          # along the horse's neck, forward and down
def ride(name, push, pump, lower, head_drop, whip=False):
    new_action(name)
    for f in range(N + 1):
        ph = f / N
        c = math.cos(2 * math.pi * (ph - PEAK))          # 1 when the head is lowest: hands furthest forward
        P = dict(BASE)
        P["hz"] = -lower - 0.0025 * pump * (1 + math.cos(2 * math.pi * (ph - PEAK - 0.08)))
        P["hx"] = 0.003 * pump * c
        P["hp"] = 2.0 * pump * c
        P["cp"] = 4.0 * lower / 0.006 + 5.0 * pump * c     # the back pumps with the push
        P["dp"] = -0.7 * P["cp"] + head_drop              # head kept looking forward
        hand = NECK * (push * c) + Vector((0, 0, -0.004 * pump * (1 - c)))
        P["wL"] = tuple(hand); P["wR"] = tuple(hand)
        P["eoL"] = P["eoR"] = 0.006 * pump * (1 - c)
        if whip:                                          # right hand: up and back, then down onto the quarters
            u = ph
            if u < 0.55:   k = 0.5 - 0.5 * math.cos(math.pi * u / 0.55)            # wind up
            elif u < 0.72: k = 1 - ((u - 0.55) / 0.17) ** 1.5 * 1.35                 # strike, fast
            else:          k = -0.35 * (1 - (u - 0.72) / 0.28) ** 2                  # follow through, back to the reins
            up = Vector((-0.085, -0.050, 0.140))
            down = Vector((-0.070, -0.060, -0.015))
            off = up * max(k, 0) + down * max(-k, 0) * 2.2
            P["wR"] = tuple(off + Vector((-0.010, 0, 0)))
            P["eoR"] = 0.025 * max(k, 0)
            P["wh"] = 100.0 * max(k, 0) - 25.0 * max(-k, 0) * 2.0          # shaft up behind his shoulder, then down onto the quarters
        set_pose(P); key_all(f)
ride("ride_quiet", push=0.004, pump=0.2, lower=0.0, head_drop=0.0)
ride("ride_push", push=0.022, pump=1.0, lower=0.003, head_drop=-2.0)
ride("ride_drive", push=0.036, pump=1.9, lower=0.006, head_drop=-4.0)
ride("ride_whip", push=0.030, pump=1.6, lower=0.006, head_drop=-4.0, whip=True)

def ramp_pose(name, P1, bones):
    """A variety pose as a short ramp from the rest pose (frame 0) to the pose (frame N): engines play it
    additively, held at its end, scaled per jockey (see racehorse_v2_rig.json)."""
    new_action(name)
    for f, P in ((0, dict(BASE)), (N, P1)):
        set_pose(P)
        for n in bones:
            pb[n].keyframe_insert("rotation_quaternion", frame=f); pb[n].keyframe_insert("location", frame=f)
JB = ["jky_hips", "jky_chest", "jky_head"] + [n for n in J if n.startswith(("jky_arm", "jky_forearm", "jky_hand"))]
ramp_pose("jky_crouch_low", dict(BASE, hz=-0.006, cp=6.0, dp=-5.0, hp=2.0), JB)
ramp_pose("jky_crouch_high", dict(BASE, hz=0.006, cp=-6.0, dp=5.0, hp=-2.0), JB)
ramp_pose("jky_elbows_out", dict(BASE, eoL=0.03, eoR=0.03), JB)
ramp_pose("jky_hands_long", dict(BASE, wL=tuple(NECK * 0.02), wR=tuple(NECK * 0.02)), JB)
for pbn in pb:
    pbn.rotation_quaternion = (1, 0, 0, 0); pbn.location = (0, 0, 0)

# ------------------------------------------------------------------ 7. the horse: a better gallop and variety poses
def rot_about(pbn, axis, deg):
    rest = pbn.bone.matrix_local.to_quaternion()
    return rest.inverted() @ Quaternion(Vector(axis).normalized(), math.radians(deg)) @ rest
TAILB = ["bone_%d" % k for k in range(34, 41)]
NECKB = ["tripo::Spine_7", "tripo::Spine_8", "tripo::Head_0", "tripo::Head_1", "tripo::Head_2", "tripo::Head_3"]
BACKB = ["tripo::Spine_0", "tripo::Spine_1", "tripo::Spine_2", "tripo::Spine_3"]
def horse_clip(src, name, nod, neck_low, tail_lift, tail_swing, reach):
    act = bpy.data.actions[src].copy(); act.name = name; act.use_fake_user = True
    arm.animation_data.action = act
    for f in range(N + 1):
        scene.frame_set(f)
        ph = f / N
        c = math.cos(2 * math.pi * (ph - PEAK))
        rots = {}
        for k, bn in enumerate(NECKB):                         # head and neck: a fuller nod, carried a little lower
            w = (0.6, 0.8, 1.0, 1.0, -0.6, -0.9)[k]
            rots[bn] = rots.get(bn, 0) + nod * w * c + neck_low * (0.8, 0.8, 0.6, 0.4, -0.4, -0.6)[k]
        for k, bn in enumerate(BACKB):                         # weight through the back: the loin flexes with the hind legs
            rots[bn] = rots.get(bn, 0) + 1.6 * math.sin(2 * math.pi * (ph - 0.62)) * (0.5 + 0.5 * k / 3)
        for bn, deg in rots.items():
            p_ = arm.pose.bones[bn]
            p_.rotation_quaternion = p_.rotation_quaternion @ rot_about(p_, (0, 1, 0), deg)
            p_.keyframe_insert("rotation_quaternion", frame=f)
        for bn, land in (("tripo::0_Right_Limb_0", 0.06), ("tripo::0_Left_Limb_0", 0.94)):   # fore legs reach further out
            sw = (((ph - land) % 1.0) - 0.25) / 0.75                  # 0..1 through the swing (rebuild_gallop.py's footfall)
            wwin = math.sin(math.pi * min(max((sw - 0.45) / 0.5, 0.0), 1.0)) ** 2 if sw > 0 else 0.0
            if wwin > 0:
                p_ = arm.pose.bones[bn]
                p_.rotation_quaternion = p_.rotation_quaternion @ rot_about(p_, (0, 1, 0), -reach * wwin)
                p_.keyframe_insert("rotation_quaternion", frame=f)
        for k, bn in enumerate(TAILB):                         # tail: carried up off the quarters, swinging behind the stride
            lag = 0.07 * k
            up = tail_lift * (1.0 if k < 2 else 0.35) + tail_swing * (0.4 + 0.25 * k) * math.sin(2 * math.pi * (ph - 0.30 - lag))
            sway = 2.2 * (0.3 + 0.2 * k) * math.sin(2 * math.pi * (ph * 1.0 - 0.1 - lag))
            p_ = arm.pose.bones[bn]
            p_.rotation_quaternion = p_.rotation_quaternion @ rot_about(p_, (0, 1, 0), up) @ rot_about(p_, (0, 0, 1), sway)
            p_.keyframe_insert("rotation_quaternion", frame=f)
    return act
horse_clip("gallop", "gallop_v2", nod=2.2, neck_low=0.0, tail_lift=9.0, tail_swing=4.0, reach=7.0)
horse_clip("gallop_drive", "gallop_v2_drive", nod=3.0, neck_low=2.0, tail_lift=12.0, tail_swing=6.0, reach=9.0)
def horse_ramp(name, degs):
    new_action(name)
    for f, s_ in ((0, 0.0), (N, 1.0)):
        for bn, d in degs.items():
            p_ = arm.pose.bones[bn]
            p_.rotation_quaternion = rot_about(p_, (0, 1, 0), d * s_)
            p_.keyframe_insert("rotation_quaternion", frame=f)
    for bn in degs:
        arm.pose.bones[bn].rotation_quaternion = (1, 0, 0, 0)
horse_ramp("horse_head_high", {"tripo::Spine_7": -4, "tripo::Spine_8": -5, "tripo::Head_0": -4, "tripo::Head_2": 3, "tripo::Head_3": 4})
horse_ramp("horse_head_low", {"tripo::Spine_7": 4, "tripo::Spine_8": 5, "tripo::Head_0": 4, "tripo::Head_2": -3, "tripo::Head_3": -4})
horse_ramp("horse_tail_high", {"bone_34": 14, "bone_35": 6, "bone_36": 3})
for name in ("gallop", "gallop_drive"):                   # v2 has its own; v1's stay in v1
    bpy.data.actions.remove(bpy.data.actions[name])
arm.animation_data.action = bpy.data.actions["gallop_v2"]
scene.frame_set(0)
if STOP == "rig":
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND); print("saved rig check", OUT_BLEND); raise SystemExit

# ------------------------------------------------------------------ 8. detail levels
arm.animation_data.action = None
for pbn in arm.pose.bones:
    pbn.rotation_quaternion = (1, 0, 0, 0); pbn.location = (0, 0, 0)
arm.data.pose_position = "REST"
def lod_copy(name):
    o = obj.copy(); o.data = obj.data.copy(); o.name = name; o.data.name = name
    scene.collection.objects.link(o); return o
def apply_first(o, mod):
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    with bpy.context.temp_override(object=o, active_object=o):
        bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
        bpy.ops.object.modifier_apply(modifier=mod.name)
close = lod_copy("racehorse_v2_close")
m = close.modifiers.new("smooth", "SUBSURF"); m.levels = 1; m.render_levels = 1; m.uv_smooth = "PRESERVE_BOUNDARIES"; m.quality = 3
apply_first(close, m)
m = close.modifiers.new("lighten", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = float(os.environ.get("CLOSE_RATIO", "0.36")); m.use_collapse_triangulate = True
apply_first(close, m)
far = lod_copy("racehorse_v2_far")
m = far.modifiers.new("lighten", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = float(os.environ.get("FAR_RATIO", "0.33")); m.use_collapse_triangulate = True
apply_first(far, m)
mt = obj.modifiers.new("tri", "TRIANGULATE"); apply_first(obj, mt)
# the race level: a little lighter than v1's horse, which it replaces in a full field
m = obj.modifiers.new("lighten", "DECIMATE"); m.decimate_type = "COLLAPSE"; m.ratio = float(os.environ.get("RACE_RATIO", "0.86")); m.use_collapse_triangulate = True
apply_first(obj, m)
arm.data.pose_position = "POSE"
LOD_OBJECTS = [close, obj, far]
tris = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in LOD_OBJECTS}
print("detail levels (triangles):", tris)

# ------------------------------------------------------------------ rig notes for engines
rig = {
    "about": "racehorse_v2: how to play the clips. Every clip is one stride (0.48 s) unless noted; play them together and in step. Scale playback by speed / 14.6 m/s (model scaled x3).",
    "detailLevels": {"racehorse_v2_close": "within about 25 m of the camera (or the horse fills a quarter of the screen)", "racehorse_v2": "the race view", "racehorse_v2_far": "beyond about 80 m"},
    "triangles": tris,
    "horse": {"gallop_v2": "normal galloping", "gallop_v2_drive": "under pressure: neck lower, deeper nod, tail higher; blend in a beat after the jockey asks",
              "walk": "walking / standing in the stalls (from v1)"},
    "jockey": {"ride_quiet": "effort 0: sitting still, hands on the neck", "ride_push": "effort 1: hands and heels, arms pushing with the stride, back pumping",
               "ride_drive": "effort 2: the same, bigger and lower", "ride_whip": "effort 3: drive with the left hand, whip in the right, one stroke a stride"},
    "effort": "timeline effort 0..3. Weights: quiet = max(0, 1 - e); push = max(0, 1 - |e - 1|); drive = max(0, 1 - |e - 2|); whip = max(0, e - 2). The horse: gallop_v2_drive = min(1, e / 2) of a copy of e delayed about 0.4 s.",
    "variety": {
        "additive": "ramp clips: rest at the start, the pose at the end. Play additively, held at the end, weight 0..1, chosen once per runner from its seed.",
        "jky_crouch_low": [0, 1], "jky_crouch_high": [0, 1], "jky_elbows_out": [0, 1], "jky_hands_long": [0, 1],
        "horse_head_high": [0, 1], "horse_head_low": [0, 1], "horse_tail_high": [0, 1],
        "stride": "cadence x0.95..1.05 per horse; the jockey's clips run 0..0.04 s off the horse's stride per jockey",
    },
    "colours": "main material: vertex colour R = coat, G = points (mane, tail, lower legs), B = jockey's skin. Multiply the grey texture's light and shade by the chosen colour inside each. Silks material: the owner's v2 silks texture times the vertex colour (fabric creases).",
}
json.dump(rig, open(OUT_RIG, "w"), indent=1)

# ------------------------------------------------------------------ 9. export
def export(path, images=True):
    bpy.ops.object.select_all(action="DESELECT")
    for o in (arm,) + tuple(LOD_OBJECTS):
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True,
        export_animations=True, export_animation_mode="ACTIONS", export_force_sampling=True,
        export_optimize_animation_size=True, export_optimize_animation_keep_anim_armature=False,
        export_frame_step=1, export_anim_single_armature=True, export_def_bones=False,
        export_skins=True, export_morph=False, export_yup=True,
        export_image_format="AUTO" if images else "NONE",
        export_vertex_color="ACTIVE", export_apply=False)
    print("exported", path, "%.2f MB" % (os.path.getsize(path) / 1e6))


def finish():
    # the silks material shows the five-zone test in the stand-alone model; engines swap in the owner's silks
    zimg = bpy.data.images.load(os.path.join(ROOT, "silks/textures-v2/zones.png"))
    zimg.name = "silks_v2_zones"
    for n in mat_silk.node_tree.nodes:
        if n.type == "TEX_IMAGE":
            n.image = zimg
    zimg.pack()
    bimg = bpy.data.images.load(OUT_TEX)                   # the main texture with the face painted back
    bimg.name = "racehorse_v2_basecolor"
    for n in mat_main.node_tree.nodes:
        if n.type == "TEX_IMAGE" and any(l.to_socket.name == "Base Color" for l in n.outputs[0].links):
            n.image = bimg
    bimg.pack()
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    export(OUT_GLB, images=True)
    web = os.environ.get("WEB_GLB", "/tmp/racehorse_v2_web.glb")
    export(web, images=False)

finish()
