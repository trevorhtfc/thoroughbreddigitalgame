"""Give the jockey's arms their own movement, leaving his head, face and body still.

Run headless:  python rig_arms.py -- <in.blend> <build-mask.png> <out.blend>
(run after pin_jockey.py and repattern_jacket.py)

Adds an upper-arm and forearm bone each side, parented to the horse's back
(Spine_4, which the rest of the jockey rides on). Only the sleeves (found from
the jacket's zone layout) and the gloves are bound to them. Movement fades in
from the shoulder seam, so the join with the body never stretches. The mane
right under the hands follows them a little, so the hair doesn't tear.

Keys three riding actions, one stride long (0.48 s, 48 frames at 100 fps),
moving the arm bones only:
  ride_quiet  hands nearly still
  ride_push   hands and heels: hands push forward along the neck as the
              horse's head goes down, elbows opening, then draw back bending
  ride_drive  the same, bigger
"""
import bpy, sys, math
import numpy as np
from PIL import Image
from mathutils import Vector, Quaternion

src, mask_path, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
scene = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
mesh = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("tripo")][0]
me = mesh.data
N, PEAK = 48, 0.12            # PEAK matches the horse's head nod
BACK = "tripo::Spine_4"

def pts(s):
    return {"shoulder": np.array((0.150, 0.062 * s, 0.535)), "elbow": np.array((0.128, 0.074 * s, 0.488)),
            "wrist": np.array((0.168, 0.050 * s, 0.450)), "hand": np.array((0.190, 0.045 * s, 0.440))}

# ---------- bones ----------
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
for side, s in (("L", 1), ("R", -1)):
    p = pts(s)
    up = eb.new("jockey_arm." + side)
    up.head, up.tail = Vector(p["shoulder"]), Vector(p["elbow"])
    up.parent = eb[BACK]
    fo = eb.new("jockey_forearm." + side)
    fo.head, fo.tail = Vector(p["elbow"]), Vector(p["wrist"])
    fo.parent = up
    fo.use_connect = True
bpy.ops.object.mode_set(mode="OBJECT")

# ---------- which vertices are arms ----------
mask = np.asarray(Image.open(mask_path).convert("RGB")).astype(float) / 255.0
MH = mask.shape[0]
silk_idx = [i for i, m in enumerate(me.materials) if m.name == "silks"][0]
uv = me.uv_layers.active.data
n = len(me.vertices)
sleeve_side = np.zeros(n)            # +1 left sleeve, -1 right sleeve
horse = np.zeros(n, bool)
for p in me.polygons:
    vs = list(p.vertices)
    if p.material_index == silk_idx:
        img_v = 1.0 - sum(uv[l].uv[1] for l in p.loop_indices) / p.loop_total   # texture row from the top
        if 0.52 <= img_v < 0.70:
            sleeve_side[vs] = 1
        elif 0.72 <= img_v < 0.90:
            sleeve_side[vs] = -1
        continue
    u = sum(uv[l].uv[0] for l in p.loop_indices) / p.loop_total
    v = sum(uv[l].uv[1] for l in p.loop_indices) / p.loop_total
    m = mask[int((1 - v) % 1 * MH) % MH, int(u % 1 * MH) % MH]
    if m[0] > 0.5 or m[1] > 0.5:
        horse[vs] = True
silk_v = np.zeros(n, bool)
for p in me.polygons:
    if p.material_index == silk_idx:
        silk_v[list(p.vertices)] = True
co = np.array([v.co[:] for v in me.vertices])
x, y, z = co.T

def seg(pnt, a, b):
    ab = b - a
    t = np.clip(((pnt - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(pnt - (a + t[:, None] * ab), axis=1), t

groups = {}
for side, s in (("L", 1), ("R", -1)):
    p = pts(s)
    up_len = np.linalg.norm(p["elbow"] - p["shoulder"])
    d1, t1 = seg(co, p["shoulder"], p["elbow"])
    d2, t2 = seg(co, p["elbow"], p["wrist"])
    d3, _ = seg(co, p["wrist"], p["hand"])
    sleeve = sleeve_side == s
    glove = ~silk_v & ~horse & (d3 < 0.035) & (y * s > 0.02) & (z < 0.48)
    along = np.where(d1 <= d2, t1 * up_len, up_len + t2 * np.linalg.norm(p["wrist"] - p["elbow"]))
    fade = np.clip(along / (0.4 * up_len), 0, 1)
    fade = fade * fade * (3 - 2 * fade)                       # smooth start at the shoulder seam
    fore_share = np.clip((along - (up_len - 0.012)) / 0.024, 0, 1)
    w_up = np.where(sleeve, fade * (1 - fore_share), 0.0)
    w_fo = np.where(sleeve, fade * fore_share, 0.0)
    w_fo = np.where(glove, 1.0, w_fo)
    w_up = np.where(glove, 0.0, w_up)
    # the mane right under the hands follows a little
    gl = np.where(glove)[0]
    if len(gl):
        from scipy.spatial import cKDTree
        dist, _ = cKDTree(co[gl]).query(co)
        hold = ~silk_v & ~glove & (dist < 0.02) & (z > 0.43)
        w_fo = np.where(hold, np.maximum(w_fo, 0.5 * (1 - dist / 0.02)), w_fo)
    groups[side] = (w_up, w_fo)
    print(side, "sleeve verts", int(sleeve.sum()), "glove verts", int(glove.sum()))

vg = {nm: (mesh.vertex_groups.get(nm) or mesh.vertex_groups.new(name=nm)) for nm in
      ["jockey_arm.L", "jockey_forearm.L", "jockey_arm.R", "jockey_forearm.R"]}
old = [g for g in mesh.vertex_groups if g.name not in vg]
for side in ("L", "R"):
    w_up, w_fo = groups[side]
    for i in np.where((w_up + w_fo) > 0.001)[0].tolist():
        total = float(min(w_up[i] + w_fo[i], 1.0))
        for g in old:                                        # scale the existing weights down to make room
            try:
                g.add([i], g.weight(i) * (1 - total), "REPLACE")
            except RuntimeError:
                pass
        if w_up[i] > 0.001:
            vg["jockey_arm." + side].add([i], float(w_up[i]), "REPLACE")
        if w_fo[i] > 0.001:
            vg["jockey_forearm." + side].add([i], float(w_fo[i]), "REPLACE")

# ---------- riding actions ----------
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"

def rot_about(pb, axis, deg):
    rest = pb.bone.matrix_local.to_quaternion()
    return rest.inverted() @ Quaternion(Vector(axis).normalized(), math.radians(deg)) @ rest

def wave(ph, lag=0.0):
    return math.cos(2 * math.pi * (ph - PEAK - lag))

RIDES = {   # shoulder swing, elbow opening, elbows flaring out as the hands come back (degrees)
    "ride_quiet": dict(arm=3, fore=4, out=1),
    "ride_push":  dict(arm=14, fore=22, out=4),
    "ride_drive": dict(arm=22, fore=34, out=7),
}
for name, a in RIDES.items():
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for i in range(N + 1):
        ph = i / N
        f = 0.5 + 0.5 * wave(ph)               # 1 = hands fully forward
        fe = 0.5 + 0.5 * wave(ph, 0.03)        # elbow follows a touch later
        for side, s in (("L", 1.0), ("R", -1.0)):
            pa = arm.pose.bones["jockey_arm." + side]
            pf = arm.pose.bones["jockey_forearm." + side]
            pa.rotation_quaternion = rot_about(pa, (0, 1, 0), -a["arm"] * (f - 0.5)) @ rot_about(pa, (1, 0, 0), s * a["out"] * (1 - f))
            pf.rotation_quaternion = rot_about(pf, (0, 1, 0), a["fore"] * (fe - 0.5))
            pa.keyframe_insert("rotation_quaternion", frame=i)
            pf.keyframe_insert("rotation_quaternion", frame=i)
arm.animation_data.action = bpy.data.actions["gallop"]
for pb in arm.pose.bones:
    if pb.name.startswith("jockey_"):
        pb.rotation_quaternion = (1, 0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
