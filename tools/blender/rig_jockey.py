"""Give the jockey his own bones and riding animations.

Run headless:  python rig_jockey.py -- <in.blend> <tint-mask.png> <out.blend>

The original model's jockey is skinned straight onto the horse's spine, so
he can't move on his own. This adds a small jockey skeleton riding on the
horse's back (hips, chest, head, upper arm and forearm each side), binds
his upper body to it, and keys three riding actions that last one stride
(0.48 s, 48 frames at 100 fps) and contain only jockey bones:

  ride_quiet  sitting still, hands following the horse's head
  ride_push   hands and heels: arms pumping, body rocking with the stride
  ride_drive  all out: bigger pump, lower and more urgent

It also adds "gallop_drive": the gallop with the neck stretched lower and
a deeper head nod, for the horse responding under pressure. Engines blend
ride_* by the jockey's effort and gallop / gallop_drive by the horse's.
"""
import bpy, sys, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix

src, mask_path, out = sys.argv[-3], sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
scene = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
mesh = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("tripo")][0]
me = mesh.data
N, CYCLE = 48, 0.48

# ---------------- bones ----------------
BONES = {   # name: (head, tail, parent)
    "jockey_hips":      ((0.00, 0.0, 0.500), (0.07, 0.0, 0.525), "tripo::Spine_3"),
    "jockey_chest":     ((0.07, 0.0, 0.525), (0.160, 0.0, 0.548), "jockey_hips"),
    "jockey_head":      ((0.170, 0.0, 0.545), (0.205, 0.0, 0.585), "jockey_chest"),
    "jockey_arm.L":     ((0.150, 0.062, 0.535), (0.128, 0.074, 0.488), "jockey_chest"),
    "jockey_forearm.L": ((0.128, 0.074, 0.488), (0.168, 0.050, 0.450), "jockey_arm.L"),
    "jockey_arm.R":     ((0.150, -0.062, 0.535), (0.128, -0.074, 0.488), "jockey_chest"),
    "jockey_forearm.R": ((0.128, -0.074, 0.488), (0.168, -0.050, 0.450), "jockey_arm.R"),
}
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="EDIT")
eb = arm.data.edit_bones
for name, (h, t, parent) in BONES.items():
    b = eb.new(name)
    b.head, b.tail = Vector(h), Vector(t)
    b.parent = eb[parent]
    b.use_connect = False
bpy.ops.object.mode_set(mode="OBJECT")

# ---------------- which vertices are the jockey's upper body ----------------
from PIL import Image
mask = np.asarray(Image.open(mask_path).convert("RGB")).astype(float) / 255.0
MH = mask.shape[0]
silk_idx = [i for i, m in enumerate(me.materials) if m.name == "silks"][0]
uv = me.uv_layers.active.data
horse_vert = np.zeros(len(me.vertices), bool)
silk_vert = np.zeros(len(me.vertices), bool)
for p in me.polygons:
    if p.material_index == silk_idx:
        for v in p.vertices: silk_vert[v] = True
        continue
    u = sum(uv[l].uv[0] for l in p.loop_indices) / p.loop_total
    v = sum(uv[l].uv[1] for l in p.loop_indices) / p.loop_total
    m = mask[int((1 - v) % 1 * MH) % MH, int(u % 1 * MH) % MH]
    if m[0] > 0.5 or m[1] > 0.5:
        for vi in p.vertices: horse_vert[vi] = True

co = np.array([v.co[:] for v in me.vertices])
x, y, z = co.T
# the whole head (face, goggles, cap peak) moves as one piece with the jockey
head = ~horse_vert & (np.linalg.norm(co - np.array([0.205, 0.0, 0.555]), axis=1) < 0.075) & (z > 0.5)
upper = silk_vert | head | (~horse_vert & (z > 0.455) & (x > -0.02) & (x < 0.25) & (np.abs(y) < 0.11))
reins = ~horse_vert & ~upper & (x >= 0.15) & (x < 0.33) & (z > 0.43) & (np.abs(y) < 0.06)
print("jockey upper verts", int(upper.sum()), "rein verts", int(reins.sum()))

def seg_dist(p, a, b):
    a, b = np.array(a), np.array(b)
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)

names = list(BONES)
D = np.stack([seg_dist(co, BONES[n][0], BONES[n][1]) for n in names], 1)
W = 1.0 / np.maximum(D, 0.004) ** 4
# keep arms on arm bones and the body off them, by side
sleeve = silk_vert & (np.abs(y) > 0.045) & (z < 0.535) & (x > 0.08)
hand = ~horse_vert & upper & (z < 0.475) & (x > 0.14) & (np.abs(y) > 0.025)
armish = sleeve | hand
for side, s in (("L", 1), ("R", -1)):
    ai, fi = names.index("jockey_arm." + side), names.index("jockey_forearm." + side)
    wrong_side = (y * s) < 0
    W[wrong_side, ai] = 0; W[wrong_side, fi] = 0
W[~armish, names.index("jockey_arm.L")] *= 0.05
W[~armish, names.index("jockey_forearm.L")] *= 0.02
W[~armish, names.index("jockey_arm.R")] *= 0.05
W[~armish, names.index("jockey_forearm.R")] *= 0.02
W[armish, names.index("jockey_hips")] = 0
W = W / W.sum(1, keepdims=True)
# keep only the two strongest bones per vertex for clean deformation
order = np.argsort(-W, 1)
for i in np.where(upper)[0]:
    keep = order[i, :2]
    w = np.zeros(len(names)); w[keep] = W[i, keep]; W[i] = w / w.sum()

groups = {n: mesh.vertex_groups.get(n) or mesh.vertex_groups.new(name=n) for n in names}
old_groups = [g for g in mesh.vertex_groups if g.name not in groups]
up_idx = np.where(upper)[0].tolist()
for g in old_groups:
    g.remove(up_idx)
for j, n in enumerate(names):
    for i in up_idx:
        if W[i, j] > 0.001:
            groups[n].add([i], float(W[i, j]), "REPLACE")
# reins: near the hands they follow the hands, further forward they stay with the horse
for i in np.where(reins)[0].tolist():
    side = "L" if y[i] > 0 else "R"
    f = float(np.clip(1 - (x[i] - 0.17) / 0.09, 0, 1))
    if f <= 0: continue
    for g in old_groups:
        try:
            w = g.weight(i)
            g.add([i], w * (1 - f), "REPLACE")
        except RuntimeError:
            pass
    groups["jockey_forearm." + side].add([int(i)], f, "REPLACE")

# ---------------- riding actions ----------------
for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"

def rot_about(pb, axis, deg):
    """Local rotation that turns this bone about an armature-space axis through its head."""
    rest = pb.bone.matrix_local.to_quaternion()
    q = Quaternion(Vector(axis).normalized(), math.radians(deg))
    return rest.inverted() @ q @ rest

PITCH = (0, 1, 0)      # + leans forward / down
ROLL = (1, 0, 0)

# Effort shapes: amplitudes in degrees. Phase 0 = start of the stride; the horse's head
# goes down and forward over the leading fore's stance, so the push peaks at PEAK.
PEAK = 0.12
RIDES = {
    "ride_quiet": dict(chest=1.5, chest_base=0, head=-1.0, arm=4, fore=3, roll=0.5, hips=0.4),
    "ride_push":  dict(chest=7, chest_base=3, head=-4, arm=20, fore=16, roll=1.5, hips=1.5),
    "ride_drive": dict(chest=11, chest_base=6, head=-6, arm=32, fore=26, roll=3, hips=2.5),
}

def wave(p, lag=0.0):
    return math.cos(2 * math.pi * (p - PEAK - lag))

for name, a in RIDES.items():
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    arm.animation_data.action = act
    for i in range(N + 1):
        p = i / N
        w = wave(p)
        poses = {
            "jockey_hips": rot_about(arm.pose.bones["jockey_hips"], PITCH, a["hips"] * w),
            "jockey_chest": rot_about(arm.pose.bones["jockey_chest"], PITCH, a["chest_base"] + a["chest"] * w)
                            @ rot_about(arm.pose.bones["jockey_chest"], ROLL, a["roll"] * math.sin(2 * math.pi * p)),
            "jockey_head": rot_about(arm.pose.bones["jockey_head"], PITCH, a["head"] * wave(p, 0.05) - a["chest_base"] * 0.8),
        }
        for side in ("L", "R"):
            # arms reach forward (negative pitch) as the horse's head goes down, elbows open with them
            poses["jockey_arm." + side] = rot_about(arm.pose.bones["jockey_arm." + side], PITCH, -a["arm"] * (0.5 + 0.5 * w) + a["chest_base"] * 0.5)
            poses["jockey_forearm." + side] = rot_about(arm.pose.bones["jockey_forearm." + side], PITCH, -a["fore"] * (0.5 + 0.5 * wave(p, 0.04)))
        for bn, q in poses.items():
            pb = arm.pose.bones[bn]
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=i)

# ---------------- horse under pressure ----------------
gallop = bpy.data.actions["gallop"]
drive = gallop.copy()
drive.name = "gallop_drive"
drive.use_fake_user = True
NECK = {"tripo::Spine_7": 4.0, "tripo::Spine_8": 4.0, "tripo::Head_0": 3.0, "tripo::Head_1": 2.0, "tripo::Head_2": -2.0, "tripo::Head_3": -3.0}
NOD = {"tripo::Spine_8": 3.0, "tripo::Head_0": 2.5, "tripo::Head_1": 2.0}
arm.animation_data.action = drive
for i in range(N + 1):
    scene.frame_set(i)
    p = i / N
    for bn in set(NECK) | set(NOD):
        pb = arm.pose.bones[bn]
        base = pb.rotation_quaternion.copy()
        extra = NECK.get(bn, 0) + NOD.get(bn, 0) * wave(p)
        pb.rotation_quaternion = base @ rot_about(pb, PITCH, extra)
        pb.keyframe_insert("rotation_quaternion", frame=i)
arm.animation_data.action = gallop
for pb in arm.pose.bones:
    if pb.name.startswith("jockey_"):
        pb.rotation_quaternion = (1, 0, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
