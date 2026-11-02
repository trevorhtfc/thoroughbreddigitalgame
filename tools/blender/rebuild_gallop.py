"""Rebuild the racehorse gallop so the legs follow a real gallop footfall.

Run headless:  python rebuild_gallop.py -- <in.glb> <out.blend>
(needs the `bpy` module, Blender 4.2)

Keeps the original body, head and tail motion. Replaces the four legs:
each hoof follows a planned path (planted on the turf while in stance,
lifted and folded while swinging) and the leg bones are solved with IK
to reach it. Footfall order is the transverse gallop seen in Muybridge's
1878 sequence: left hind, right hind, left fore, right fore (right lead),
then a moment of suspension with the legs gathered.

The result is baked into a new "gallop" action at 100 fps (48 frames =
one 0.48 s stride), and "walk" is resampled to the same rate.
"""
import bpy, sys, math
from mathutils import Vector, Quaternion

src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
scene = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
orig_gallop = bpy.data.actions["gallop_Armature"]
orig_walk = bpy.data.actions["walk_Armature"]

ORIG_FPS = 24.0
CYCLE = 0.48                 # seconds per stride
STRIDE = 14.6 / 3.0 * CYCLE  # body travel per stride in model units (14.6 m/s at scale 3)
N = 48                       # samples per stride -> 100 fps
SOLE = 0.008                 # Limb_4 tail height above the sole when planted

# leg: (bone prefix, landing phase 0..1, duty, landing x, swing height)
# Hind stance is kept short enough that the hoof stays within reach at push-off,
# so the leg never locks dead straight.
LEGS = {
    "LH": ("tripo::1_Left_Limb", 0.56, 0.21, 0.04, 0.11),
    "RH": ("tripo::1_Right_Limb", 0.68, 0.21, 0.04, 0.11),
    "LF": ("tripo::0_Left_Limb", 0.94, 0.25, 0.47, 0.17),
    "RF": ("tripo::0_Right_Limb", 0.06, 0.25, 0.47, 0.17),
}

def hoof_target(phase, land_phase, duty, land_x, height, y):
    """Hoof position (armature space, z up) at a point in the stride."""
    ls = duty * STRIDE                       # ground covered while planted
    u = (phase - land_phase) % 1.0
    if u < duty:                             # stance: planted, sliding back relative to the body
        return Vector((land_x - ls * (u / duty), y, SOLE))
    s = (u - duty) / (1.0 - duty)            # swing 0..1
    lift_x = land_x - ls
    hind = land_x < 0.2
    # hind legs come through quickly after push-off; fore legs fold first, then reach
    ease = 0.5 - 0.5 * math.cos(math.pi * (s ** 0.7 if hind else s))
    x = lift_x + (land_x - lift_x) * ease
    # rises fast, folds, then reaches forward and comes down
    z = SOLE + height * math.sin(math.pi * (s ** 0.75)) ** 1.2
    return Vector((x, y, z))

def orig_frame(t):
    f = (t % CYCLE) * ORIG_FPS
    return int(f), f - int(f)

# Lateral (y) position of each hoof: keep it where the original had it on average.
lat = {}
arm.animation_data.action = orig_gallop
for k, (pre, *_rest) in LEGS.items():
    ys = []
    for i in range(12):
        fi, sub = orig_frame(CYCLE * i / 12)
        scene.frame_set(fi, subframe=sub)
        ys.append((arm.pose.bones[pre + "_4"].tail).y)
    lat[k] = sum(ys) / len(ys)

# IK targets
targets = {}
for k, (pre, *_rest) in LEGS.items():
    e = bpy.data.objects.new("ik_" + k, None)
    scene.collection.objects.link(e)
    e.parent = arm
    targets[k] = e
    c = arm.pose.bones[pre + "_4"].constraints.new("IK")
    c.target = e
    c.chain_count = 5          # hip/shoulder joins in, for reach
    c.use_tail = True
    c.use_stretch = False
    c.iterations = 500

# Each leg joint is a hinge in the horse's side-on plane, limited to its natural
# range, so hocks can't fold the wrong way and knees can't bow forwards.
# Ranges are the bend between a bone and the next one down the leg, measured
# side-on in degrees (positive = the lower bone turns anticlockwise seen from
# the horse's right side, i.e. towards the front).
RANGES = {
    "hind": [(-150, -15), (-12, 125), (-75, 110), (-45, 45)],   # stifle, hock, fetlock, pastern
    "fore": [(-60, 60), (-150, 6), (-110, 75), (-45, 45)],      # shoulder/elbow, knee, fetlock, pastern
}
def side_angle(pb):
    h, t = pb.bone.head_local, pb.bone.tail_local
    return math.degrees(math.atan2(t.z - h.z, t.x - h.x))

def posed_angle(pb):
    return math.degrees(math.atan2(pb.tail.z - pb.head.z, pb.tail.x - pb.head.x))

# Thighs and shoulders (the top bone of each leg) may only swing as far as they
# did in the original animation, plus a small margin, so they can't poke up
# through the rump or the withers.
arm.animation_data.action = orig_gallop
for k, (pre, *_rest) in LEGS.items():
    arm.pose.bones[pre + "_4"].constraints[0].influence = 0.0   # measure the original, not the IK
top_range = {}
for k, (pre, *_rest) in LEGS.items():
    pb = arm.pose.bones[pre + "_0"]
    bends = []
    for i in range(24):
        fi, sub = orig_frame(CYCLE * i / 24)
        scene.frame_set(fi, subframe=sub)
        bends.append(((posed_angle(pb) - posed_angle(pb.parent) + 180) % 360) - 180)
    top_range[k] = (min(bends), max(bends))
# Left and right share one range per pair (the original's two sides were caught at
# different moments), with room to swing forward but not up through the body.
for pair, fwd in ((("LH", "RH"), 25), (("LF", "RF"), 25)):
    lo = min(top_range[p][0] for p in pair) - 12
    hi = max(top_range[p][1] for p in pair) + fwd
    for p in pair:
        top_range[p] = (lo, hi)
print("thigh/shoulder ranges", {k: (round(a), round(b)) for k, (a, b) in top_range.items()})
arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.location, pb.rotation_quaternion, pb.scale = (0, 0, 0), (1, 0, 0, 0), (1, 1, 1)
for k, (pre, *_rest) in LEGS.items():
    kind = "hind" if pre.startswith("tripo::1_") else "fore"
    for i in range(5):
        pb = arm.pose.bones[f"{pre}_{i}"]
        m = pb.bone.matrix_local.to_3x3()
        ax, az = m.col[0], m.col[2]
        use_x = abs(ax.y) >= abs(az.y)
        sign = 1.0 if (ax.y if use_x else az.y) > 0 else -1.0
        pb.lock_ik_y = True
        pb.lock_ik_x, pb.lock_ik_z = (not use_x), use_x
        parent = pb.parent if i == 0 else arm.pose.bones[f"{pre}_{i - 1}"]
        rb = ((side_angle(pb) - side_angle(parent) + 180) % 360) - 180
        bmin, bmax = top_range[k] if i == 0 else RANGES[kind][i - 1]
        lo, hi = ((rb - bmax, rb - bmin) if sign > 0 else (bmin - rb, bmax - rb))
        if use_x:
            pb.use_ik_limit_x, pb.ik_min_x, pb.ik_max_x = True, math.radians(lo), math.radians(hi)
        else:
            pb.use_ik_limit_z, pb.ik_min_z, pb.ik_max_z = True, math.radians(lo), math.radians(hi)

def sample(action, t, with_ik):
    arm.animation_data.action = action
    fi, sub = orig_frame(t) if action is orig_gallop else (int(t * ORIG_FPS), t * ORIG_FPS - int(t * ORIG_FPS))
    for k, (pre, land, duty, lx, h) in LEGS.items():
        targets[k].location = hoof_target(t / CYCLE, land, duty, lx, h, lat[k])
        arm.pose.bones[pre + "_4"].constraints[0].influence = 1.0 if with_ik else 0.0
    scene.frame_set(fi, subframe=sub)
    bpy.context.view_layer.update()
    M = {pb.name: pb.matrix.copy() for pb in arm.pose.bones}
    if with_ik:
        for k, (pre, *_rest) in LEGS.items():
            planarize(M, pre)
    pose = {}
    for pb in arm.pose.bones:
        ml = pb.bone.matrix_local
        if pb.parent:
            basis = (ml.inverted() @ pb.parent.bone.matrix_local) @ M[pb.parent.name].inverted() @ M[pb.name]
        else:
            basis = ml.inverted() @ M[pb.name]
        pose[pb.name] = basis.decompose()
    return pose

def planarize(M, pre):
    """Keep a leg in one upright plane from hip to hoof: the joints between are
    moved sideways onto the straight line between the two, and each bone is
    re-aimed with the smallest turn, so hocks and knees never bulge outwards."""
    names = [f"{pre}_{i}" for i in range(5)]
    lens = [arm.pose.bones[n].bone.length for n in names]
    P = [M[names[0]].translation.copy()] + [M[n] @ Vector((0, lens[i], 0)) for i, n in enumerate(names)]
    total = sum(lens)
    y0, y5 = P[0].y, P[5].y
    cur = P[0].copy()
    acc = 0.0
    for i, n in enumerate(names):
        acc += lens[i]
        want = P[i + 1].copy()
        want.y = y0 + (y5 - y0) * acc / total
        d = (want - cur).normalized()
        rot3 = M[n].to_3x3()
        bone_dir = (rot3 @ Vector((0, 1, 0))).normalized()
        rot3 = bone_dir.rotation_difference(d).to_matrix() @ rot3
        m4 = rot3.to_4x4()
        m4.translation = cur
        M[n] = m4
        cur = cur + d * lens[i]

gallop_frames = [sample(orig_gallop, CYCLE * i / N, True) for i in range(N + 1)]
walk_len = (orig_walk.frame_range[1] - orig_walk.frame_range[0]) / ORIG_FPS
walk_n = int(round(walk_len * 50))          # sample walk at 50 fps, key every 2 frames at 100 fps
walk_frames = [sample(orig_walk, walk_len * i / walk_n, False) for i in range(walk_n + 1)]

# Drop the IK rig and write clean keyframed actions.
for k, (pre, *_rest) in LEGS.items():
    pb = arm.pose.bones[pre + "_4"]
    pb.constraints.remove(pb.constraints[0])
    bpy.data.objects.remove(targets[k])

def write_action(name, frames, step):
    act = bpy.data.actions.new(name)
    arm.animation_data.action = act
    for i, pose in enumerate(frames):
        f = i * step
        for pb in arm.pose.bones:
            loc, rot, scl = pose[pb.name]
            pb.location, pb.rotation_quaternion, pb.scale = loc, rot, scl
            pb.keyframe_insert("location", frame=f)
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.keyframe_insert("scale", frame=f)
    return act

for pb in arm.pose.bones:
    pb.rotation_mode = "QUATERNION"
gallop = write_action("gallop", gallop_frames, 1)

# Head and neck nod: once per stride, lowest as the leading fore takes the weight,
# rising through the hind stance and suspension. The poll counter-rotates a little
# so the face stays near vertical.
NOD_PEAK = 0.20
NOD = {"tripo::Spine_7": 0.20, "tripo::Spine_8": 0.30, "tripo::Head_0": 0.20, "tripo::Head_1": 0.15,
       "tripo::Head_2": 0.10, "tripo::Head_5": -0.25}
NOD_DEG = 14.0
def rot_about(pb, axis, deg):
    rest = pb.bone.matrix_local.to_quaternion()
    q = Quaternion(Vector(axis).normalized(), math.radians(deg))
    return rest.inverted() @ q @ rest
arm.animation_data.action = gallop
for i in range(N + 1):
    scene.frame_set(i)
    w = math.cos(2 * math.pi * (i / N - NOD_PEAK))
    for bn, share in NOD.items():
        pb = arm.pose.bones[bn]
        pb.rotation_quaternion = pb.rotation_quaternion @ rot_about(pb, (0, 1, 0), NOD_DEG * share * w)
        pb.keyframe_insert("rotation_quaternion", frame=i)
walk = write_action("walk", walk_frames, 2)
gallop.use_fake_user = walk.use_fake_user = True
bpy.data.actions.remove(orig_gallop)
bpy.data.actions.remove(orig_walk)
arm.animation_data.action = gallop
scene.render.fps = 100
scene.frame_start, scene.frame_end = 0, N
bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
