"""Add "gallop_drive": the gallop with the horse's neck stretched lower and a
deeper head nod, for the horse responding under pressure. Horse bones only;
the jockey stays as the original model has him.

Run headless:  python horse_drive.py -- <in.blend> <out.blend>
"""
import bpy, sys, math
from mathutils import Vector, Quaternion

src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
scene = bpy.context.scene
arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
N, PEAK = 48, 0.12
NECK = {"tripo::Spine_7": 4.0, "tripo::Spine_8": 4.0, "tripo::Head_0": 3.0, "tripo::Head_1": 2.0,
        "tripo::Head_2": -2.0, "tripo::Head_3": -3.0}
NOD = {"tripo::Spine_8": 3.0, "tripo::Head_0": 2.5, "tripo::Head_1": 2.0}


def rot_about(pb, axis, deg):
    rest = pb.bone.matrix_local.to_quaternion()
    return rest.inverted() @ Quaternion(Vector(axis).normalized(), math.radians(deg)) @ rest


gallop = bpy.data.actions["gallop"]
drive = gallop.copy()
drive.name = "gallop_drive"
drive.use_fake_user = True
arm.animation_data.action = drive
for i in range(N + 1):
    scene.frame_set(i)
    w = math.cos(2 * math.pi * (i / N - PEAK))
    for bn in set(NECK) | set(NOD):
        pb = arm.pose.bones[bn]
        pb.rotation_quaternion = pb.rotation_quaternion @ rot_about(pb, (0, 1, 0), NECK.get(bn, 0) + NOD.get(bn, 0) * w)
        pb.keyframe_insert("rotation_quaternion", frame=i)
arm.animation_data.action = gallop
bpy.ops.wm.save_as_mainfile(filepath=out)
print("saved", out)
