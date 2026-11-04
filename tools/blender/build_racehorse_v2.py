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
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
from PIL import Image

ROOT = os.path.abspath(os.environ.get("REPO", "."))
SRC = os.path.join(ROOT, "assets/models/master/racehorse_master.blend")
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

# Cap: everything of the old cap above the rim goes (the new cap replaces it); below the rim is his neck.
old_cap = zone == "cap"
above_rim = side(C, RIM) > 0
near_head = np.linalg.norm(C - HEAD, axis=1) < 0.075
zone[old_cap & above_rim] = "cap_old"
zone[old_cap & ~above_rim] = "skin"
# his own head faces above the rim at the front (the old peak's underside) would poke through the new peak
zone[(zone == "jockey") & above_rim & face_head & (x > HEAD[0] + 0.012)] = "cap_old"
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
        zone[i] = "skin" if tex_lum(p) > 0.10 else "kit"
    else:
        zone[i] = "kit"

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
hz[mane] = "points"
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


# ------------------------------------------------------------------ 3a. the new cap: a smooth dome with a proper peak
# The dome follows the old cap's shape (rays from the middle of the head to the old surface), then is
# smoothed and set 1.5 mm proud; it reaches 4 mm below the rim so it closes over the head neatly.
capf = [p for p in me.polygons if zone[p.index] == "cap_old"]
cverts = [v.co.copy() for v in me.vertices]
tree = BVHTree.FromPolygons(cverts, [tuple(p.vertices) for p in capf])
capco = np.array([cverts[v][:] for p in capf for v in p.vertices])
H = Vector((float(capco[:, 0].mean()) - 0.004, 0.0, 0.551))
rp, rn = Vector(RIM[0]), Vector(RIM[1])
NPHI, NV, LIP = 56, 18, 0.004
def dome_dir(th, ph):                       # th from straight up; ph 0 = forward (+x), +y = jockey's left
    return Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
def hit(d):
    h = tree.ray_cast(H, d, 0.2)
    return (h[0] - H).length if h[0] is not None else None
grid = np.zeros((NV + 1, NPHI, 3))
thmax = []
for j in range(NPHI):
    ph = 2 * math.pi * j / NPHI
    lo, hi = 0.2, 2.4                          # find the angle where the surface meets the rim (less the lip)
    r_last = 0.05
    for _ in range(26):
        mid = (lo + hi) / 2
        r = hit(dome_dir(mid, ph)) or r_last
        r_last = r
        pt = H + dome_dir(mid, ph) * r
        if (pt - rp).dot(rn) > -LIP: lo = mid
        else: hi = mid
    thmax.append(lo)
thmax = np.convolve(np.r_[thmax[-3:], thmax, thmax[:3]], np.ones(7) / 7, "same")[3:-3]
R = np.zeros((NV + 1, NPHI))
for i in range(NV + 1):
    for j in range(NPHI):
        ph = 2 * math.pi * j / NPHI
        th = thmax[j] * (i / NV) ** 0.9
        R[i, j] = hit(dome_dir(th, ph)) or np.nan
R = np.where(np.isnan(R), np.nanmean(R), R)
R0 = R.copy()
for _ in range(14):                            # iron out the old facets and the lumps of the old flap
    R[1:-1] = 0.5 * R[1:-1] + 0.125 * (np.roll(R, 1, 1)[1:-1] + np.roll(R, -1, 1)[1:-1] + R[:-2] + R[2:])
    R[-1] = 0.5 * R[-1] + 0.25 * (np.roll(R, 1, 1)[-1] + np.roll(R, -1, 1)[-1])
    R = np.maximum(R, R0 * 0.975)                # never sink far inside the old cap (keeps the head covered)
R[0] = R[0].mean()
R += 0.0015
# a touch lower in the crown than the old cap: a skull cap sits close on the head
for i in range(NV + 1):
    for j in range(NPHI):
        th = thmax[j] * (i / NV) ** 0.9
        R[i, j] *= 1.0 - 0.07 * math.cos(min(th, math.pi / 2)) ** 2
cap_bm = bmesh.new()
cap_uvl = cap_bm.loops.layers.uv.new("UVMap")
cap_col = cap_bm.loops.layers.color.new("Color")
CX, CY, CR = ATLAS["cap"][0], ATLAS["cap"][1], ATLAS["cap"][2]
def cap_uv(vv, ph):                            # polar disc: top in the middle, rim round the edge, peak at the bottom
    a = ph                                      # forward at the bottom of the disc, jockey's left to the right
    return (CX + CR * vv * math.sin(a), CY + CR * vv * math.cos(a))
verts = [[None] * NPHI for _ in range(NV + 1)]
top = cap_bm.verts.new(H + Vector((0, 0, R[0, 0])))
for i in range(1, NV + 1):
    for j in range(NPHI):
        ph = 2 * math.pi * j / NPHI
        th = thmax[j] * (i / NV) ** 0.9
        verts[i][j] = cap_bm.verts.new(H + dome_dir(th, ph) * R[i, j])
def put(face, uvs, shades):
    for l, u_, sh in zip(face.loops, uvs, shades):
        l[cap_uvl].uv = (u_[0], 1 - u_[1]); l[cap_col] = (sh, sh, sh, 1.0)
rimshade = lambda i: 1.0 - 0.12 * max(0.0, (i / NV - 0.75) / 0.25)
for j in range(NPHI):
    j2 = (j + 1) % NPHI
    ph0, ph1 = 2 * math.pi * j / NPHI, 2 * math.pi * (j + 1) / NPHI
    f = cap_bm.faces.new((top, verts[1][j], verts[1][j2]))
    put(f, [cap_uv(0, (ph0 + ph1) / 2), cap_uv(1 / NV, ph0), cap_uv(1 / NV, ph1)], [1, 1, 1])
    for i in range(1, NV):
        f = cap_bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][j2], verts[i][j2]))
        put(f, [cap_uv(i / NV, ph0), cap_uv((i + 1) / NV, ph0), cap_uv((i + 1) / NV, ph1), cap_uv(i / NV, ph1)],
            [rimshade(i), rimshade(i + 1), rimshade(i + 1), rimshade(i)])
# The peak: a short curved brim on the front of the rim, tipped down a little, with a rounded edge
PEAK_HALF = math.radians(56); PEAK_LEN = 0.016; PEAK_T = 0.0016
pk_top, pk_bot = [], []
NP = 25
for k in range(NP):
    ph = -PEAK_HALF + 2 * PEAK_HALF * k / (NP - 1)
    jf = (ph % (2 * math.pi)) / (2 * math.pi) * NPHI
    j0 = int(jf) % NPHI; t = jf - int(jf)
    base = verts[NV][j0].co.lerp(verts[NV][(j0 + 1) % NPHI].co, t)
    out = Vector((math.cos(ph), math.sin(ph), 0.0))
    length = PEAK_LEN * math.cos(ph / PEAK_HALF * math.pi / 2) ** 0.55
    row_t, row_b = [], []
    for s_ in range(4):
        f_ = s_ / 3
        pt = base + out * (length * f_) + Vector((0, 0, -0.006 * f_ ** 1.6 + 0.0005))
        row_t.append(cap_bm.verts.new(pt + Vector((0, 0, PEAK_T / 2))))
        row_b.append(cap_bm.verts.new(pt - Vector((0, 0, PEAK_T / 2))))
    pk_top.append(row_t); pk_bot.append(row_b)
def pk_uv(k, s_):
    ph = -PEAK_HALF + 2 * PEAK_HALF * k / (NP - 1)
    return cap_uv(0.93 + 0.02 * s_ / 3, ph)
for k in range(NP - 1):
    for s_ in range(3):
        f = cap_bm.faces.new((pk_top[k][s_], pk_top[k][s_ + 1], pk_top[k + 1][s_ + 1], pk_top[k + 1][s_]))
        put(f, [pk_uv(k, s_), pk_uv(k, s_ + 1), pk_uv(k + 1, s_ + 1), pk_uv(k + 1, s_)], [1, 1, 1, 1])
        f = cap_bm.faces.new((pk_bot[k][s_], pk_bot[k + 1][s_], pk_bot[k + 1][s_ + 1], pk_bot[k][s_ + 1]))
        put(f, [pk_uv(k, s_), pk_uv(k + 1, s_), pk_uv(k + 1, s_ + 1), pk_uv(k, s_ + 1)], [0.62] * 4)
    f = cap_bm.faces.new((pk_top[k][3], pk_bot[k][3], pk_bot[k + 1][3], pk_top[k + 1][3]))
    put(f, [pk_uv(k, 3)] * 2 + [pk_uv(k + 1, 3)] * 2, [0.85] * 4)
for k in (0, NP - 1):
    for s_ in range(3):
        a, b = (pk_top[k][s_], pk_top[k][s_ + 1], pk_bot[k][s_ + 1], pk_bot[k][s_]), None
        f = cap_bm.faces.new(a if k == NP - 1 else tuple(reversed(a)))
        put(f, [pk_uv(k, s_)] * 4, [0.85] * 4)
cap_me = bpy.data.meshes.new("cap_v2"); cap_bm.to_mesh(cap_me); cap_bm.free()
print("new cap:", len(cap_me.polygons), "faces")

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
SKIN = spot(Want("skin", 0.55))
for p in me.polygons:
    zn = zone[p.index]
    if p.material_index == SILK and zn not in ("body", "left", "right", "cap_old"):
        p.material_index = MAIN
        target = SKIN if zn == "skin" else DARK if zn == "glove" else LIGHT
        for l in p.loop_indices:
            uv[l].uv = target

# vertex colours: main = (coat, points, skin) masks; silks = crease shade (kept from v1)
col = me.color_attributes["Color"]
shade = np.array([c.color[:] for c in col.data])
for p in me.polygons:
    zn = zone[p.index]
    if p.material_index == MAIN:
        m = (1.0 if zn == "coat" else 0.0, 1.0 if zn == "points" else 0.0, 1.0 if zn == "skin" else 0.0, 1.0)
        for l in p.loop_indices:
            col.data[l].color = m

bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table()
kill = [bm.faces[i] for i in np.where(zone == "cap_old")[0]]
bmesh.ops.delete(bm, geom=kill, context="FACES")
bm.to_mesh(me); bm.free()
zone = zone[zone != "cap_old"]
print("old cap faces removed:", len(kill))
# anything of his head left above the rim that pokes out through the new cap (goggle strap, old peak) goes
cap_tree = BVHTree.FromPolygons([v.co[:] for v in cap_me.vertices], [tuple(p.vertices) for p in cap_me.polygons])
uv, C, MI = face_data()
poke = []
for p in me.polygons:
    c = Vector(C[p.index])
    if zone[p.index] in ("skin", "kit") and (c - Vector(HEAD)).length < 0.08 and (c - rp).dot(rn) > -0.003:
        d = c - H
        h = cap_tree.ray_cast(H, d.normalized(), d.length)
        if h[0] is not None and (h[0] - H).length < d.length - 0.0003:
            poke.append(p.index)
if poke:
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in poke], context="FACES")
    bm.to_mesh(me); bm.free()
    keepz = np.ones(len(zone), bool); keepz[poke] = False
    zone = zone[keepz]
print("head faces poking through the new cap, removed:", len(poke))
# join the new cap in: silks material, bound to the jockey's back like the rest of his head
cap_obj = bpy.data.objects.new("cap_v2", cap_me); scene.collection.objects.link(cap_obj)
cap_me.materials.append(mat_silk)
for p in cap_me.polygons:
    p.material_index = 0; p.use_smooth = True
g = cap_obj.vertex_groups.new(name="tripo::Spine_4"); g.add(list(range(len(cap_me.vertices))), 1.0, "REPLACE")
n_before = len(me.polygons)
bpy.ops.object.select_all(action="DESELECT")
cap_obj.select_set(True); obj.select_set(True); bpy.context.view_layer.objects.active = obj
bpy.ops.object.join()
zone = np.concatenate([zone, np.array(["cap"] * (len(me.polygons) - n_before), dtype=object)])

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

FACE_ZONE = list(zone)
if STOP == "zones":
    for nm, c in (("body", (0.85, 0.1, 0.1)), ("left", (0.1, 0.7, 0.1)), ("right", (0.95, 0.85, 0.1)), ("skin", (1, 0.75, 0.6)),
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
bmesh.ops.split_edges(bm, edges=cut)
bm.to_mesh(me); bm.free()
print("hand/rein edges cut:", len(cut))

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
jockey_v = np.array([bool(z_ & {"body", "left", "right", "cap", "skin", "glove"}) or
                     (("kit" in z_) and v_ok) for z_, v_ok in zip(vzones, (co[:, 2] > 0.43) & (co[:, 0] > -0.06) & (co[:, 0] < 0.25) & (np.abs(co[:, 1]) < 0.12))])
whip_v = np.array(["whip" in z_ for z_ in vzones])
W = {n: np.zeros(len(co)) for n in J}
W["tripo::Spine_4"] = np.zeros(len(co))
x_, y_, z_ = co.T
headish = np.array([bool(zz & {"cap"}) for zz in vzones]) | (jockey_v & (np.linalg.norm(co - np.array([0.198, 0, 0.553]), axis=1) < 0.05) & (x_ > 0.158))
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
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    export(OUT_GLB, images=True)
    web = os.environ.get("WEB_GLB", "/tmp/racehorse_v2_web.glb")
    export(web, images=False)

finish()
