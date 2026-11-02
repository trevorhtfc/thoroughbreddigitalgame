"""Pin the whole jockey to the horse's back, so he rides as one piece.

Run headless:  python pin_jockey.py -- <in.blend> <build-mask.png> <out.blend>

In the original model parts of the jockey (face, chin, cap) are bound to the
horse's neck and head bones, so they swing whenever the horse's head nods.
This binds every jockey vertex fully to the back bone the rest of him
follows (Spine_4). The mane and reins are left with the horse.
"""
import bpy, sys
import numpy as np
from PIL import Image

src, mask_path, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
mesh = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("tripo")][0]
me = mesh.data
BACK = "tripo::Spine_4"

mask = np.asarray(Image.open(mask_path).convert("RGB")).astype(float) / 255.0
MH = mask.shape[0]
silk_idx = [i for i, m in enumerate(me.materials) if m.name == "silks"][0]
uv = me.uv_layers.active.data
horse = np.zeros(len(me.vertices), bool)
silk = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if p.material_index == silk_idx:
        for v in p.vertices:
            silk[v] = True
        continue
    u = sum(uv[l].uv[0] for l in p.loop_indices) / p.loop_total
    v = sum(uv[l].uv[1] for l in p.loop_indices) / p.loop_total
    m = mask[int((1 - v) % 1 * MH) % MH, int(u % 1 * MH) % MH]
    if m[0] > 0.5 or m[1] > 0.5:
        for vi in p.vertices:
            horse[vi] = True

co = np.array([v.co[:] for v in me.vertices])
x, y, z = co.T
mane = ~silk & (np.abs(y) < 0.025) & (((x > 0.16) & (z < 0.48)) |
                                     ((x > 0.185) & (np.abs(z - (0.49 + (x - 0.2) * 0.55)) < 0.022)))
crest = (np.abs(y) < 0.04) & (z < 0.49 + (x - 0.2) * 0.55 + 0.03)      # the neck and mane just below the head
head = (np.linalg.norm(co - np.array([0.205, 0.0, 0.555]), axis=1) < 0.075) & (z > 0.5) & ~crest & ~mane
body = ~horse & ~mane & (z > 0.455) & (x > -0.02) & (x < 0.25) & (np.abs(y) < 0.11)
jockey = silk | head | body

back = mesh.vertex_groups[BACK]
others = [g for g in mesh.vertex_groups if g.name != BACK]
idx = np.where(jockey)[0].tolist()
for g in others:
    g.remove(idx)
back.add(idx, 1.0, "REPLACE")
print("jockey verts pinned", len(idx))
bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
