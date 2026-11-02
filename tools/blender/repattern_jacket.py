"""Give the jockey's silks a proper pattern layout (UV map).

Run headless:  python repattern_jacket.py -- <in.blend> <out.blend>

The original model maps the silks by projection, so left and right (and
much of front and back) share the same part of the image: every design
comes out mirrored. This replaces the UVs of the faces using the "silks"
material with a garment layout, one full-width band per part, so each
part can wrap all the way round:

  texture rows (from the top of the image)
    0.00-0.50  body    u: 0 = right side seam, 0.25 = chest centre,
                          0.5 = left side, 0.75 = back centre
                       v: 0 = waist .. 1 = collar/shoulders
    0.52-0.70  left sleeve   u: round the arm, v: shoulder .. cuff
    0.72-0.90  right sleeve  u: round the arm, v: shoulder .. cuff
    0.92-1.00  cap           u: round the crown (0 = peak), v: top .. rim

tools/silks/make_silks.py paints textures in exactly this layout.
"""
import bpy, sys, math
import numpy as np

src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
mesh = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("tripo")][0]
me = mesh.data
silk_idx = [i for i, m in enumerate(me.materials) if m.name == "silks"][0]
uv = me.uv_layers.active.data

ROWS = {"body": (0.00, 0.50), "left": (0.52, 0.70), "right": (0.72, 0.90), "cap": (0.92, 1.00)}

def part_of(c):
    x, y, z = c
    if x > 0.165 and z > 0.553:
        return "cap"
    if abs(y) > 0.045 and z < 0.535 and x > 0.08:
        return "left" if y > 0 else "right"
    return "body"

faces = [p for p in me.polygons if p.material_index == silk_idx]
parts = {k: [] for k in ROWS}
for p in faces:
    parts[part_of(p.center)].append(p)

co = np.array([v.co[:] for v in me.vertices])

def verts_of(polys):
    return sorted({v for p in polys for v in p.vertices})

# --- body: cylinder round the torso's long (x) axis --------------------
bv = co[verts_of(parts["body"])]
X0, X1 = bv[:, 0].min(), 0.175            # waist .. shoulders
ZC = float(np.median(bv[:, 2]))
def body_uv(p):
    x, y, z = p
    a = math.atan2(y, -(z - ZC)) / (2 * math.pi)     # 0 chest, +0.25 left, 0.5 back
    u = (a + 0.25) % 1.0                              # seam on the right side
    v = min(max((x - X0) / (X1 - X0), 0.0), 1.0)
    return u, v

# --- sleeves: cylinder round each arm, top (shoulder) to bottom (cuff) ---
def sleeve_fn(polys):
    sv = co[verts_of(polys)]
    ztop, zbot = sv[:, 2].max(), sv[:, 2].min()
    cx, cy = sv[:, 0].mean(), sv[:, 1].mean()
    side = 1.0 if cy > 0 else -1.0
    def f(p):
        x, y, z = p
        a = math.atan2((x - cx), side * (y - cy) * -1.0) / (2 * math.pi)   # seam on the inside of the arm
        return a % 1.0, min(max((ztop - z) / (ztop - zbot), 0.0), 1.0)
    return f

# --- cap: round the crown, top to rim ------------------------------------
cv = co[verts_of(parts["cap"])]
CX, CZ0, CZ1 = cv[:, 0].mean() - 0.01, cv[:, 2].min(), cv[:, 2].max()
def cap_uv(p):
    x, y, z = p
    phi = math.atan2(y, x - CX) / (2 * math.pi)                # 0 = peak (front)
    return (phi + 0.5) % 1.0, min(max((CZ1 - z) / (CZ1 - CZ0), 0.0), 1.0)

FN = {"body": body_uv, "left": sleeve_fn(parts["left"]), "right": sleeve_fn(parts["right"]), "cap": cap_uv}

for name, polys in parts.items():
    r0, r1 = ROWS[name]
    fn = FN[name]
    for p in polys:
        uvs = [fn(co[me.loops[li].vertex_index]) for li in p.loop_indices]
        us = [u for u, _ in uvs]
        if max(us) - min(us) > 0.5:                      # face straddles the wrap seam
            uvs = [((u + 1.0) if u < 0.5 else u, v) for u, v in uvs]
        for li, (u, v) in zip(p.loop_indices, uvs):
            img_v = r0 + v * (r1 - r0)                   # rows measured from the image top
            uv[li].uv = (u, 1.0 - img_v)                 # Blender UVs start at the bottom

print({k: len(v) for k, v in parts.items()})
bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
