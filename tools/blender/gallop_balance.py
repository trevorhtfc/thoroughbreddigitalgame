"""Rebalance a gallop clip: the body's rocking put in step with the legs, and every hoof planted on the turf.

Read by tools/blender/build_racehorse_v2.py (exec'd there, after the head, back and tail have been added to a
clip). It needs that script's bpy, arm, obj (the race mesh), scene, N.

Why (owner, 13 Nov: "the horse in full gallop looks a tiny bit like they are going to fall over their fronts"):
 - The body's rocking was out of step with the legs. It dipped its nose furthest (5 degrees) just as the fore
   legs reached out to land, and was nose-down right through the hind legs' push. A real galloper is the other
   way about: the forehand is up while the hind legs push and the fore legs reach, and the nose is down only
   while the fore legs are under the body, carrying it.
 - The fore hooves sank up to 12 cm (at the view's scale) into the ground as they landed, and then stood
   still under the horse for a few frames before sweeping back, so the front end looked to be stumbling.

What this does, frame by frame:
 1. Turns the whole horse about its middle to a new rocking curve (PITCH): up most in the middle of the hind
    legs' push, down most in the middle of the fore legs' stance, level as the fore legs land.
 2. Lets the neck take up part of that, so the head doesn't swing with the body.
 3. Gives each hoof a path: on the ground and travelling back at the ground's speed from touch-down to
    lift-off (STANCE), and the clip's own swing in between, eased into both ends. Each leg's joints are then
    turned by the least that puts the hoof on its path with the sole flat while it is down.
"""
import math
import numpy as np
from mathutils import Matrix, Vector

GB_LEGS = {"FL": "tripo::0_Left_Limb_", "FR": "tripo::0_Right_Limb_", "HL": "tripo::1_Left_Limb_", "HR": "tripo::1_Right_Limb_"}
GB_REF = {"FL": 2, "FR": 8, "HL": 31, "HR": 35}          # a frame where the clip has each hoof squarely down: its sole and "flat" are read here
# For each leg: the new touch-down frame, the hoof's place then (model units ahead of the model's origin) and the
# frames it stays on the ground; then where the clip itself has that leg start and end its sweep back. Each leg
# is re-timed from the clip's own sweep and swing to the new ones, so it keeps its own action.
GB_STANCE = {"HL": (26.5, 0.012, 9.5, 26.5, 36.5), "HR": (31.0, 0.045, 8.5, 32.0, 38.5),
             "FL": (43.5, 0.410, 8.5, 46.0, 54.5), "FR": (49.5, 0.385, 8.0, 52.0, 60.5)}
GB_GROUND = 14.6 * 0.48 / 3.0 / 48                       # the ground's speed under the horse: model units a frame
# how freely each joint gives (shoulder or hip, elbow or stifle, knee or hock, fetlock, hoof)
GB_GIVE = {"F": (1.0, 1.0, 0.2, 0.5, 0.35), "H": (1.0, 1.0, 0.7, 0.5, 0.35)}
GB_PIVOT = Vector((0.02, 0.0, 0.33))                     # the horse's middle
GB_NECK = {"tripo::Spine_7": 0.16, "tripo::Spine_8": 0.16, "tripo::Head_0": 0.10, "tripo::Head_1": 0.06}


def gb_periodic(points):
    """A smooth closed curve through (phase, value) points; phase 0..1."""
    ph = np.array([p for p, _ in points]); val = np.array([v for _, v in points])
    o = np.argsort(ph); ph, val = ph[o], val[o]
    P = np.concatenate([ph - 1, ph, ph + 1]); V = np.concatenate([val, val, val])
    def f(x):
        x = x % 1.0
        k = np.searchsorted(P, x) - 1
        # Catmull-Rom on uneven knots
        p0, p1, p2, p3 = P[k - 1], P[k], P[k + 1], P[k + 2]; v0, v1, v2, v3 = V[k - 1], V[k], V[k + 1], V[k + 2]
        t = (x - p1) / (p2 - p1)
        m1 = (v2 - v0) / (p2 - p0) * (p2 - p1); m2 = (v3 - v1) / (p3 - p1) * (p2 - p1)
        return (2 * t**3 - 3 * t**2 + 1) * v1 + (t**3 - 2 * t**2 + t) * m1 + (-2 * t**3 + 3 * t**2) * v2 + (t**3 - t**2) * m2
    return f


def gb_pitch_curve(level=1.5, swing=2.8):
    """The body's rock, degrees, nose up positive, against the model's rest pose."""
    c = gb_periodic([(0.06, -1.0), (0.30, -0.40), (0.50, 0.40), (0.69, 1.0), (0.88, 0.10)])
    return lambda ph: level + swing * float(c(ph))


def gb_roty(p, deg):
    """Turn about the line through p across the horse; positive lifts whatever is in front of p."""
    return Matrix.Translation(p) @ Matrix.Rotation(math.radians(-deg), 4, "Y") @ Matrix.Translation(-Vector(p))


def gb_soles():
    """Each hoof's sole (a point in its hoof bone's own space) and the hoof bone's angle when flat on the ground."""
    out = {}
    gi = {g.name: g.index for g in obj.vertex_groups}
    for leg, pre in GB_LEGS.items():
        idx = gi[pre + "4"]
        vs = [v.index for v in obj.data.vertices if any(g.group == idx and g.weight > 0.6 for g in v.groups)]
        scene.frame_set(GB_REF[leg])
        dg = bpy.context.evaluated_depsgraph_get(); ev = obj.evaluated_get(dg); me_ = ev.to_mesh()
        co = np.array([(obj.matrix_world @ me_.vertices[i].co)[:] for i in vs]); ev.to_mesh_clear()
        low = co[co[:, 2] <= np.quantile(co[:, 2], 0.2)]
        sole_w = Vector((float(low[:, 0].mean()), float(co[:, 1].mean()), float(co[:, 2].min())))
        M = arm.matrix_world @ arm.pose.bones[pre + "4"].matrix
        d = M.to_3x3() @ Vector((0, 1, 0))
        out[leg] = (M.inverted() @ sole_w, math.atan2(d.z, d.x))
    return out


def gb_solve(Ms, sole_l, target, flat_w, flat_angle, give):
    """Ms: the five leg bones' armature matrices. Turn the joints (in the horse's fore-and-aft plane) by the least
    that brings the sole to target (x, z), and, by flat_w (0..1), the hoof to its flat angle."""
    Ms = [m.copy() for m in Ms]
    Wi = np.diag(give)
    for it in range(30):
        heads = [m.translation.copy() for m in Ms]
        s = Ms[4] @ sole_l
        d = Ms[4].to_3x3() @ Vector((0, 1, 0)); ang = math.atan2(d.z, d.x)
        e = np.array([target[0] - s.x, target[1] - s.z, 0.0])
        # an angle step of +1 about gb_roty lifts the front: the hoof's angle rises by the same
        e[2] = flat_w * ((flat_angle - ang + math.pi) % (2 * math.pi) - math.pi) * 0.04
        if abs(e[0]) + abs(e[1]) < 2e-5 and abs(e[2]) < 2e-5:
            break
        J = np.zeros((3, 5))
        for j in range(5):
            r = s - heads[j]
            J[0, j] = -r.z; J[1, j] = r.x; J[2, j] = flat_w * 0.04      # d(sole)/d(angle), radians
        A = J @ Wi @ J.T + np.eye(3) * 1e-7
        dq = Wi @ J.T @ np.linalg.solve(A, e)
        dq = np.clip(dq, -0.25, 0.25)
        for j in range(5):
            R = gb_roty(heads[j], math.degrees(dq[j]))
            for k in range(j, 5):
                Ms[k] = R @ Ms[k]
            heads = [m.translation.copy() for m in Ms]
    s = Ms[4] @ sole_l
    return Ms, math.hypot(target[0] - s.x, target[1] - s.z)


def gb_clip_time(leg, f, n):
    """Where in the clip a leg takes its pose from, for frame f of the new stride."""
    td, _, dur, td_o, lo_o = GB_STANCE[leg]
    rel = (f - td) % n
    if rel <= dur:
        return td_o + (lo_o - td_o) * rel / dur
    return lo_o + (td_o + n - lo_o) * (rel - dur) / (n - dur)


def gb_paths(at, n):
    """Hoof paths for one stride. at(leg, t) gives the clip's own sole position (x, z) at clip time t."""
    out = {}
    fr = np.arange(n)
    for leg, (td, x_td, dur, td_o, lo_o) in GB_STANCE.items():
        lo = td + dur
        rel = (fr - td) % n                                   # frames since touch-down
        down = rel <= dur
        x_line = x_td - GB_GROUND * rel
        o = np.array([at(leg, gb_clip_time(leg, f, n)) for f in fr])
        e_td = np.array((x_td, 0.0)) - np.array(at(leg, td_o)); e_lo = np.array((x_td - GB_GROUND * dur, 0.0)) - np.array(at(leg, lo_o))
        since_lo = (fr - lo) % n; to_td = (td - fr) % n       # frames into the swing, frames left of it
        ease = lambda d, span: np.where(d < span, 0.5 + 0.5 * np.cos(np.pi * np.clip(d / span, 0, 1)), 0.0)
        x = o[:, 0] + e_lo[0] * ease(since_lo, 7.0) + e_td[0] * ease(to_td, 7.0)
        z = o[:, 1] + e_lo[1] * ease(since_lo, 5.0) + e_td[1] * ease(to_td, 5.0)
        lift = lambda d: 0.014 * np.clip(d / 3.0, 0, 1) ** 1.5
        z = np.maximum(z, np.minimum(lift(since_lo), lift(to_td)))       # clear of the turf, but no leaping off it
        for _ in range(2):                                    # a light smoothing of the swing, the stance kept exact
            x = np.where(down, x_line, (np.roll(x, 1) + 2 * x + np.roll(x, -1)) / 4)
            z = np.where(down, 0.0, (np.roll(z, 1) + 2 * z + np.roll(z, -1)) / 4)
        x = np.where(down, x_line, x); z = np.where(down, 0.0, np.maximum(z, 0.0))
        flat = np.where(down, np.clip(np.minimum(rel, dur - rel) / 2.0, 0.25, 1.0), 0.0)
        out[leg] = (x, z, flat)
    return out


def rebalance(act, level=1.5, swing=2.8, neck=1.0, report=True):
    arm.animation_data.action = act
    pbs = arm.pose.bones
    soles = gb_soles()
    root = pbs["tripo::Root"]
    rest_q = arm.data.bones["tripo::Root"].matrix_local.to_quaternion()
    chain = {leg: [pbs[pre + str(k)] for k in range(5)] for leg, pre in GB_LEGS.items()}
    # 1. the clip as it is: the body's own rock, and each leg's pose and sole at the clip time it will be taken from
    own = np.zeros(N)
    for f in range(N):
        scene.frame_set(f)
        fwd = (root.matrix.to_quaternion() @ rest_q.inverted()) @ Vector((1, 0, 0))
        own[f] = math.degrees(math.atan2(fwd.z, fwd.x))
    def clip_leg(leg, t):
        t = t % N
        scene.frame_set(int(math.floor(t)), subframe=t - math.floor(t))
        return [b.matrix.copy() for b in chain[leg]]
    def clip_sole(leg, t):
        s = clip_leg(leg, t)[4] @ soles[leg][0]
        return (s.x, s.z)
    paths = gb_paths(clip_sole, N)
    pose = {leg: [clip_leg(leg, gb_clip_time(leg, f, N)) for f in range(N)] for leg in GB_LEGS}
    want = gb_pitch_curve(level, swing)
    worst = 0.0
    log = []
    for f in range(N + 1):
        k = f % N
        scene.frame_set(f)
        turn = want(k / N) - own[k]
        root.matrix = gb_roty(GB_PIVOT, turn) @ root.matrix
        bpy.context.view_layer.update()
        root.keyframe_insert("rotation_quaternion", frame=f); root.keyframe_insert("location", frame=f)
        for bn, share in GB_NECK.items():                     # the neck gives back part of the body's turn
            p_ = pbs[bn]
            p_.matrix = gb_roty(p_.matrix.translation, -turn * share * neck) @ p_.matrix
            bpy.context.view_layer.update()
            p_.keyframe_insert("rotation_quaternion", frame=f)
        row = [f, want(k / N)]
        for leg in GB_LEGS:
            bones = chain[leg]
            # start from the leg as the clip had it against the ground at its own time, hung from where the
            # shoulder or hip now is (not carried round with the body)
            Ms = pose[leg][k]
            shift = Matrix.Translation(bones[0].matrix.translation - Ms[0].translation)
            Ms = [shift @ m for m in Ms]
            x, z, flat = paths[leg]
            Ms, miss = gb_solve(Ms, soles[leg][0], (x[k], z[k]), flat[k], soles[leg][1], GB_GIVE[leg[0]])
            worst = max(worst, miss)
            for b, m in zip(bones, Ms):
                loc = b.location.copy()
                b.matrix = m; bpy.context.view_layer.update()
                b.location = loc
                b.keyframe_insert("rotation_quaternion", frame=f)
            row += [x[k], z[k], miss]
        log.append(row)
    # quaternions kept on one side from key to key, so nothing spins the long way round between frames
    quats = {}
    for fc in gb_fcurves(act):
        if fc.data_path.endswith("rotation_quaternion"):
            quats.setdefault(fc.data_path, {})[fc.array_index] = fc
    for path, fcs in quats.items():
        if len(fcs) < 4 or len({len(fcs[i].keyframe_points) for i in range(4)}) != 1:
            continue
        prev = None
        for k in range(len(fcs[0].keyframe_points)):
            q = [fcs[i].keyframe_points[k].co[1] for i in range(4)]
            if prev is not None and sum(a * b for a, b in zip(q, prev)) < 0:
                q = [-a for a in q]
                for i in range(4):
                    kp = fcs[i].keyframe_points[k]
                    kp.co[1] = q[i]; kp.handle_left[1] = -kp.handle_left[1]; kp.handle_right[1] = -kp.handle_right[1]
            prev = q
        for i in range(4):
            fcs[i].update()
    down = {leg: max(r[4 + 3 * j] for r in log if paths[leg][2][int(r[0]) % N] > 0) for j, leg in enumerate(GB_LEGS)}
    if report:
        print("rebalanced %s: worst hoof miss %.4f in the air, %.5f on the ground (model units)" % (act.name, worst, max(down.values())))
    return {"pitch": [want(k / N) for k in range(N)], "paths": paths, "log": log, "down": down}


def gb_fcurves(act):
    try:
        return list(act.fcurves)
    except Exception:
        out = []
        for layer in act.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out += list(bag.fcurves)
        return out
