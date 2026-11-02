"""Zone the jockey's silks and give each zone a clean pattern layout (UV map).

Run headless:  python repattern_jacket.py -- <in.blend> <tint-mask.png> <out.blend>

1. Gathers every silk face: the "silks" material plus the small silk areas
   that sit on the main body mesh (cuffs, hem, cap rim), found with the
   tint mask's blue channel. Those move to the silks material so they take
   the pattern instead of a flat colour.
2. Sorts them into zones: body, left sleeve, right sleeve, cap. Sleeves are
   whatever lies closer to the arm (shoulder > elbow > wrist) than to the
   torso; a neighbour vote then tidies the joins.
3. Unwraps each zone into its own band of the texture:

   rows from the image top
     0.00-0.50  body          u: 0 right side seam, .25 chest centre, .5 left side,
                                 .75 back centre; v: 0 waist .. 1 collar
     0.52-0.70  left sleeve   u: round the arm (0 outside, .5 inside);
                              v: 0 shoulder .. 1 cuff
     0.72-0.90  right sleeve  same as left
     0.92-1.00  cap           u: round the crown (.5 = peak, .75 jockey's left);
                              v: 0 top .. 1 rim

tools/silks/make_silks.py paints textures in exactly this layout.
"""
import bpy, sys, math
import numpy as np
from PIL import Image

src, mask_path, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
mesh = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("tripo")][0]
me = mesh.data
silk_idx = [i for i, m in enumerate(me.materials) if m.name == "silks"][0]
uv = me.uv_layers.active.data
ROWS = {"body": (0.00, 0.50), "left": (0.52, 0.70), "right": (0.72, 0.90), "cap": (0.92, 1.00)}

# ---------- 1. gather silk faces ----------
import bmesh
mask = np.asarray(Image.open(mask_path).convert("RGB")).astype(float) / 255.0
MH = mask.shape[0]

def mask_at(u, v):
    return mask[int((1 - v) % 1 * MH) % MH, int(u % 1 * MH) % MH]

for p in me.polygons:
    if p.material_index == silk_idx:
        continue
    c = p.center
    if not (-0.03 < c.x < 0.27 and c.z > 0.425 and abs(c.y) < 0.12):
        continue
    if c.x > 0.175 and c.z < 0.553 and abs(c.y) < 0.035:      # face and goggles stay as they are
        continue
    # sample the corners, edge midpoints and centre; move the face only if it is almost all silk
    uvs = [tuple(uv[l].uv) for l in p.loop_indices]
    cu = (sum(a for a, _ in uvs) / len(uvs), sum(b for _, b in uvs) / len(uvs))
    pts = uvs + [((uvs[i][0] + uvs[(i + 1) % len(uvs)][0]) / 2, (uvs[i][1] + uvs[(i + 1) % len(uvs)][1]) / 2) for i in range(len(uvs))] + [cu]
    hits = sum(1 for u, v in pts if (lambda m: m[2] > 0.5 and m[0] < 0.5 and m[1] < 0.5)(mask_at(u, v)))
    if hits / len(pts) >= 0.85:
        p.material_index = silk_idx

# ---------- 2. cut clean seams, then sort into zones ----------
def nrm(v):
    v = np.array(v, float)
    return v / np.linalg.norm(v)

# Armholes: the sleeve seam runs round the top of each arm, below the shoulder edge.
ARMHOLE = {1: ((0.148, 0.047, 0.535), nrm((0.15, 1.0, -0.45))),
           -1: ((0.148, -0.047, 0.535), nrm((0.15, -1.0, -0.45)))}
# Cap rim: tilted so the back of the cap sits a little lower than the peak.
RIM = ((0.20, 0.0, 0.552), nrm((-0.08, 0.0, 1.0)))
HEAD = np.array((0.198, 0.0, 0.565))

bm = bmesh.new()
bm.from_mesh(me)
bm.faces.ensure_lookup_table()
for co_, no_ in list(ARMHOLE.values()) + [RIM]:
    faces = [f for f in bm.faces if f.material_index == silk_idx]
    geom = list({v for f in faces for v in f.verts}) + list({e for f in faces for e in f.edges}) + faces
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co_, plane_no=no_, dist=1e-5)
bm.to_mesh(me)
bm.free()
me.update()
uv = me.uv_layers.active.data

n = len(me.polygons)
C = np.array([p.center[:] for p in me.polygons])
x, y, z = C.T
silk = np.array([p.material_index == silk_idx for p in me.polygons])

def seg_d(p, a, b):
    a, b = np.array(a), np.array(b)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)

def arm_points(s):
    return [(0.150, 0.062 * s, 0.535), (0.128, 0.074 * s, 0.488), (0.168, 0.050 * s, 0.450), (0.190, 0.045 * s, 0.440)]

def arm_d(p, s):
    pts = arm_points(s)
    return np.min([seg_d(p, pts[i], pts[i + 1]) for i in range(3)], axis=0)

def side(p, plane):
    return (p - np.array(plane[0])) @ plane[1]

zone = np.full(n, -1)
zone[silk] = 0
cap = silk & (side(C, RIM) > 0) & (np.linalg.norm(C - HEAD, axis=1) < 0.068) & (x > 0.14)
for s_, k in ((1, 1), (-1, 2)):
    sl = silk & ~cap & (side(C, ARMHOLE[s_]) > 0) & (arm_d(C, s_) < 0.032)
    sl |= silk & ~cap & (x > 0.15) & (z < 0.48) & (y * s_ > 0.03)        # cuffs at the hands
    zone[sl] = k
zone[cap] = 3

# Tidy stragglers away from the cut seams: neighbours found by welded position,
# since the mesh is stored in many small separate patches.
key = lambda v: tuple(np.round(v, 5))
vkey = [key(v.co[:]) for v in me.vertices]
edge_faces = {}
for p in me.polygons:
    ks = [vkey[v] for v in p.vertices]
    for i in range(len(ks)):
        e = tuple(sorted((ks[i], ks[(i + 1) % len(ks)])))
        edge_faces.setdefault(e, []).append(p.index)
adj = [[] for _ in range(n)]
for fs in edge_faces.values():
    for a in fs:
        adj[a] += [b for b in fs if b != a]
near_cut = np.zeros(n, bool)
for plane in list(ARMHOLE.values()) + [RIM]:
    near_cut |= np.abs(side(C, plane)) < 0.004
for _ in range(3):
    new = zone.copy()
    for i in np.where(silk & ~near_cut)[0]:
        nb = [zone[j] for j in adj[i] if silk[j]]
        if len(nb) >= 2:
            vals, cnt = np.unique(nb, return_counts=True)
            if cnt.max() > len(nb) / 2:
                new[i] = vals[cnt.argmax()]
    zone = new
NAMES = {0: "body", 1: "left", 2: "right", 3: "cap"}
print("silk faces", int(silk.sum()), {NAMES[k]: int((zone == k).sum()) for k in NAMES})

# ---------- 3. unwrap ----------
co = np.array([v.co[:] for v in me.vertices])
bodyv = co[sorted({v for i in np.where(zone == 0)[0] for v in me.polygons[int(i)].vertices})]
X0, X1 = float(bodyv[:, 0].min()), 0.175

# Centre line of the torso, from the middle of measured cross-sections, so the
# wrap-round stays smooth (an axis outside the body would smear the pattern).
AXIS_X = [0.00, 0.06, 0.11, 0.15, 0.18]
AXIS_Z = [0.499, 0.510, 0.519, 0.510, 0.495]
def torso_zc(px):
    return float(np.interp(px, AXIS_X, AXIS_Z))

def body_uv(p):
    px, py, pz = p
    a = math.atan2(py, -(pz - torso_zc(px))) / (2 * math.pi)   # 0 chest, .25 left, .5 back
    return (a + 0.25) % 1.0, min(max((px - X0) / (X1 - X0), 0.0), 1.0)

def sleeve_fn(s):
    pts = [np.array(q) for q in arm_points(s)]
    lens = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(3)]
    total = sum(lens)
    def f(p):
        p = np.array(p)
        best = None
        acc = 0.0
        for i in range(3):
            a, b = pts[i], pts[i + 1]
            ab = b - a
            t = float(np.clip((p - a) @ ab / (ab @ ab), 0, 1))
            d = np.linalg.norm(p - (a + t * ab))
            if best is None or d < best[0]:
                best = (d, acc + t * lens[i], ab / np.linalg.norm(ab), a + t * ab)
            acc += lens[i]
        _, along, axis, foot = best
        out_ref = np.array([0.0, s, 0.0])
        out_ref = out_ref - axis * (out_ref @ axis)
        out_ref /= np.linalg.norm(out_ref)
        side = np.cross(axis, out_ref)
        r = p - foot
        ang = math.atan2(r @ side, r @ out_ref) / (2 * math.pi)  # 0 outside of the arm
        return ang % 1.0, min(max(along / total, 0.0), 1.0)
    return f

capv = co[sorted({v for i in np.where(zone == 3)[0] for v in me.polygons[int(i)].vertices})]
CX, CZ0, CZ1 = float(capv[:, 0].mean()) - 0.01, float(capv[:, 2].min()), float(capv[:, 2].max())

def cap_uv(p):
    px, py, pz = p
    phi = math.atan2(py, px - CX) / (2 * math.pi)            # 0 = peak (front)
    return (phi + 0.5) % 1.0, min(max((CZ1 - pz) / (CZ1 - CZ0), 0.0), 1.0)

FN = {"body": body_uv, "left": sleeve_fn(1), "right": sleeve_fn(-1), "cap": cap_uv}
for k, name in NAMES.items():
    r0, r1 = ROWS[name]
    fn = FN[name]
    for i in np.where(zone == k)[0]:
        p = me.polygons[int(i)]
        uvs = [fn(co[me.loops[li].vertex_index]) for li in p.loop_indices]
        us = [u for u, _ in uvs]
        if max(us) - min(us) > 0.5:                      # face straddles the wrap seam
            uvs = [((u + 1.0) if u < 0.5 else u, v) for u, v in uvs]
        for li, (u, v) in zip(p.loop_indices, uvs):
            uv[li].uv = (u, 1.0 - (r0 + v * (r1 - r0)))

bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
