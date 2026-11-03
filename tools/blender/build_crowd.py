"""Build the racegoer crowd kit: modular figures, hats, a simple rig and looping actions.

    python -c "exec(open('tools/blender/build_crowd.py').read())" [lineup.png] [samples]

After reference/crowd/crowd-asset-pack.png and reference/crowd/ascot-scene-mood.png: stylised period
racegoers (gents in morning coats and lounge suits, ladies in A-line and fitted dresses) with swappable
hats (top hat, boater, homburg; wide brim, wide brim with flowers, cloche, fascinator).

Writes
  assets/models/architecture/crowd_kit.glb        two rigs (rig_gent, rig_lady), each with its bodies,
                                                  hats and actions; every mesh in three versions: near
                                                  (about 1,300-1,500 triangles for a body), `_far`
                                                  (about 200) and `_tiny` (a silhouette, about 50, no arms)
  assets/models/architecture/crowd_anims.json     the actions sampled per frame as one rigid transform
                                                  per bone, so a renderer can animate thousands of
                                                  people in a vertex shader without skinning
  assets/models/master/crowd_kit.blend            Blender master
  (lineup.png)                                    a review render of the line-up, when asked

How colour works (any engine): every vertex carries `_slot` (which part of the outfit it belongs to) and
`_bone` (which bone moves it). A person's look is a row of colours, one per slot:
  0 skin  1 hair  2 main (jacket or dress)  3 second (trousers or trim)  4 shirt  5 accent (tie,
  waistcoat, belt)  6 dark (shoes, eyes)  7 hat  8 hat band or flowers  9 prop
COLOR_0 holds a default look so the kit also shows sensibly in Blender or Godot as it is.

Bones (index = `_bone`): 0 body (pivot at the feet), 1 head (pivot at the neck), 2 upper arm R,
3 forearm R, 4 upper arm L, 5 forearm L. Every vertex follows exactly one bone (rigid parts).
Figures face -y in Blender (+z in glTF), stand on the origin, metres.
"""
import json, math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector, Quaternion

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)
ARGS = [a for a in sys.argv[1:] if not a.startswith("-")]
OUT_PNG = ARGS[0] if ARGS else None
SAMPLES = int(ARGS[1]) if len(ARGS) > 1 else 24
FPS = 24

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS

SLOTS = ["skin", "hair", "main", "second", "shirt", "accent", "dark", "hat", "band", "prop"]
S = {n: i for i, n in enumerate(SLOTS)}
BONES = ["body", "head", "upper_arm.R", "forearm.R", "upper_arm.L", "forearm.L"]
B = {n: i for i, n in enumerate(BONES)}


# ================================================================ geometry builder
class Mesh:
    """Collects vertices with a slot and a bone each. Parts never share vertices, so each shades softly
    on its own and keeps one colour."""

    def __init__(self, far=False, tiny=False):
        self.v, self.f, self.slot, self.bone = [], [], [], []
        self.far = far or tiny
        self.tiny = tiny

    def _add(self, p, slot, bone):
        self.v.append(Vector(p)); self.slot.append(S[slot]); self.bone.append(B[bone])
        return len(self.v) - 1

    def rings(self, rings, slot, bone, segs, phase=0.0):
        """Stack of ellipses: rings = [(cx, cy, z, rx, ry)] from bottom to top; a ring with rx == 0 is a
        pole. Closed lathe shapes (bodies, hats, heads) are all built from this."""
        idx = []
        for cx, cy, z, rx, ry in rings:
            if rx <= 1e-6:
                idx.append([self._add((cx, cy, z), slot, bone)])
            else:
                idx.append([self._add((cx + rx * math.cos(2 * math.pi * k / segs + phase),
                                       cy + ry * math.sin(2 * math.pi * k / segs + phase), z), slot, bone)
                            for k in range(segs)])
        for a, b in zip(idx[:-1], idx[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                for k in range(segs):
                    self.f.append((a[0], b[k], b[(k + 1) % segs]))
            elif len(b) == 1:
                for k in range(segs):
                    self.f.append((a[k], b[0], a[(k + 1) % segs]))
            else:
                for k in range(segs):
                    self.f.append((a[k], b[k], b[(k + 1) % segs], a[(k + 1) % segs]))

    def lathe(self, profile, slot, bone, segs, c=(0, 0), sx=1.0, sy=1.0, z0=0.0):
        """profile = [(r, z)] bottom to top; c = middle; sx, sy squash the ellipse."""
        self.rings([(c[0], c[1], z0 + z, r * sx, r * sy) for r, z in profile], slot, bone, segs)

    def ellipsoid(self, c, r, slot, bone, segs=12, rows=8):
        rx, ry, rz = r
        prof = [(math.sin(math.pi * i / rows), -math.cos(math.pi * i / rows)) for i in range(rows + 1)]
        self.rings([(c[0], c[1], c[2] + rz * z, rx * s, ry * s) for s, z in prof], slot, bone, segs)

    def tube(self, p0, p1, r0, r1, slot, bone, segs=8, caps=True):
        """A tapered tube from p0 to p1 with rounded ends (an arm, a leg)."""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        q = d.to_track_quat("Z", "Y")
        M = Matrix.Translation(p0) @ q.to_matrix().to_4x4()
        n = 2 if caps else 0
        prof = []
        if caps:
            prof += [(0.0, -r0 * 0.9), (r0 * 0.75, -r0 * 0.6)]
        prof += [(r0, 0.0), (r1, L)]
        if caps:
            prof += [(r1 * 0.75, L + r1 * 0.6), (0.0, L + r1 * 0.9)]
        start = len(self.v)
        self.rings([(0, 0, z, r, r) for r, z in prof], slot, bone, segs)
        for i in range(start, len(self.v)):
            self.v[i] = M @ self.v[i]

    def plate(self, pts, y0, y1, slot, bone):
        """A flat shape in the x-z plane between y0 and y1 (a shirt front, a tie, a programme)."""
        a = [self._add((x, y0, z), slot, bone) for x, z in pts]
        b = [self._add((x, y1, z), slot, bone) for x, z in pts]
        n = len(pts)
        self.f.append(tuple(a)); self.f.append(tuple(reversed(b)))
        for i in range(n):
            self.f.append((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))

    def boxm(self, M, size, slot, bone):
        sx, sy, sz = size
        c = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
        i = [self._add(M @ Vector((x * sx / 2, y * sy / 2, z * sz / 2)), slot, bone) for x, y, z in c]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.f.append(tuple(i[k] for k in f))

    def seg(self, near, far):
        return far if self.far else near


# ================================================================ the two body plans
# Landmarks per body plan: shoulder, elbow and wrist at rest (right side, x < 0: the figure faces -y,
# so its right hand is on -x), the neck pivot and the crown of the head (where hats sit).
PLAN = {
    "gent": dict(shoulder=(-0.205, 0.0, 1.405), elbow=(-0.24, 0.02, 1.125), wrist=(-0.25, -0.03, 0.86),
                 neck=1.49, head_c=1.64, head_r=(0.092, 0.1, 0.117), arm_r=(0.068, 0.058, 0.052), hand=0.05),
    "lady": dict(shoulder=(-0.158, 0.0, 1.315), elbow=(-0.185, 0.02, 1.065), wrist=(-0.19, -0.03, 0.83),
                 neck=1.395, head_c=1.545, head_r=(0.087, 0.094, 0.11), arm_r=(0.055, 0.046, 0.04), hand=0.043),
}
for p in PLAN.values():
    p["crown"] = p["head_c"] + p["head_r"][2] * 0.97


def head(m, plan, hair):
    P = PLAN[plan]
    hc, (rx, ry, rz) = P["head_c"], P["head_r"]
    if not m.far:                                               # the far version's head sits on its collar
        m.tube((0, 0.005, P["neck"] - 0.06), (0, 0.0, hc - 0.05), 0.048 if plan == "gent" else 0.04, 0.045 if plan == "gent" else 0.037,
               "skin", "head", 7, caps=False)
    m.ellipsoid((0, 0, hc), (rx, ry, rz), "skin", "head", m.seg(12, 6), m.seg(8, 3))
    if not m.far:
        m.ellipsoid((0, -ry * 0.98, hc - 0.012), (0.016, 0.02, 0.022), "skin", "head", 6, 4)          # nose
        for sx in (-1, 1):
            m.ellipsoid((sx * rx * 0.38, -ry * 0.9, hc + 0.018), (0.013, 0.008, 0.015), "dark", "head", 6, 4)   # eyes
            m.ellipsoid((sx * rx * 0.97, 0.0, hc + 0.0), (0.016, 0.026, 0.03), "skin", "head", 6, 4)  # ears
    # hair: a cap set back and up, so the face stays clear; ladies also a bun or a bob
    if hair in ("short", "bun", "bob") and not m.far:
        m.ellipsoid((0, 0.022, hc + 0.025), (rx * 1.04, ry * 1.02, rz * 0.93), "hair", "head", m.seg(12, 6), m.seg(7, 3))
    if hair == "bun" and not m.far:
        m.ellipsoid((0, ry * 0.85, hc - 0.03), (0.05, 0.045, 0.05), "hair", "head", m.seg(8, 5), m.seg(6, 3))
    if hair == "bob" and not m.far:
        m.ellipsoid((0, 0.03, hc - 0.03), (rx * 1.12, ry * 1.05, rz * 0.75), "hair", "head", m.seg(12, 6), m.seg(7, 3))


def arms(m, plan, sleeve, cuff, glove=False):
    P = PLAN[plan]
    r0, r1, r2 = P["arm_r"]
    for side, (up, fo) in ((-1, ("upper_arm.R", "forearm.R")), (1, ("upper_arm.L", "forearm.L"))):
        s = Vector((side * -P["shoulder"][0], P["shoulder"][1], P["shoulder"][2]))
        e = Vector((side * -P["elbow"][0], P["elbow"][1], P["elbow"][2]))
        w = Vector((side * -P["wrist"][0], P["wrist"][1], P["wrist"][2]))
        if not m.far:                                           # rounds the top of the sleeve into the shoulder
            m.ellipsoid(s + Vector((side * -0.012, 0, -0.035)), (r0 * 0.98, r0 * 0.98, r0 * 0.95), sleeve, up, 8, 5)
        m.tube(s, e, r0, r1, sleeve, up, m.seg(8, 4), caps=not m.far)
        m.tube(e, w, r1 * 0.98, r2, cuff, fo, m.seg(8, 4), caps=False)
        hand = w + (w - e).normalized() * (P["hand"] * 0.8)
        if not m.far:
            m.ellipsoid(hand, (P["hand"] * 0.75, P["hand"] * 0.62, P["hand"]), "skin" if not glove else "shirt", fo, m.seg(7, 4), m.seg(5, 2))


def gent_body(m, coat="morning"):
    """Trousers, shoes, a jacket (morning coat with a cutaway skirt, or a lounge suit), shirt, tie."""
    sg = m.seg(12, 6)
    for sx in (-1, 1):
        if not m.far:
            m.ellipsoid((sx * 0.095, -0.04, 0.045), (0.052, 0.115, 0.045), "dark", "body", 7, 4)              # shoes
        m.tube((sx * 0.095, 0.0, 0.07), (sx * 0.1, 0.0, 0.84), 0.058, 0.082, "second", "body", m.seg(8, 4), caps=False)
    if not m.far:
        m.rings([(0, 0, 0.74, 0.16, 0.115), (0, 0, 0.86, 0.175, 0.125)], "second", "body", sg)          # seat
    # jacket: chest and shoulders as one smooth stack; the morning coat's skirt reaches to the knee at the back
    hem = 0.5 if coat == "morning" else 0.74
    m.rings([(0, 0.02, hem, 0, 0), (0, 0.02, hem, 0.19, 0.14), (0, 0.01, 0.86, 0.192, 0.14), (0, 0, 1.0, 0.18, 0.13),
             (0, 0, 1.18, 0.198, 0.138), (0, 0, 1.32, 0.215, 0.142), (0, 0, 1.39, 0.205, 0.132),
             (0, 0, 1.44, 0.15, 0.1), (0, 0, 1.47, 0.07, 0.06), (0, 0, 1.47, 0, 0)], "main", "body", sg)
    if coat == "morning":                                       # the cutaway: trousers show at the front
        m.plate([(-0.17, 0.5), (0.17, 0.5), (0.12, 0.84), (-0.12, 0.84)], -0.145, -0.135, "second", "body")
    # the open front: waistcoat or shirt in a V, white collar, tie
    yv = -0.141
    m.plate([(-0.07, 1.44), (0.07, 1.44), (0.0, 1.0)], yv - 0.004, yv + 0.004, "accent" if coat == "morning" else "shirt", "body")
    if not m.far:
        m.plate([(-0.045, 1.45), (0.045, 1.45), (0.0, 1.3)], yv - 0.011, yv - 0.004, "shirt", "body")
        m.plate([(-0.014, 1.43), (0.014, 1.43), (0.018, 1.25), (0.0, 1.22), (-0.018, 1.25)], yv - 0.016, yv - 0.011, "dark" if coat == "morning" else "accent", "body")
    if not m.far:                                               # lapel edges and a pocket square
        for sx in (-1, 1):
            m.plate([(sx * 0.07, 1.44), (sx * 0.1, 1.38), (sx * 0.02, 1.12), (sx * 0.0, 1.1)], yv - 0.002, yv + 0.006, "main", "body")
        m.plate([(0.1, 1.29), (0.15, 1.29), (0.145, 1.255), (0.105, 1.255)], -0.147, -0.139, "shirt", "body")


def lady_body(m, dress="aline"):
    sg = m.seg(14, 6)
    for sx in (-1, 1):
        if not m.far:
            m.ellipsoid((sx * 0.065, -0.03, 0.035), (0.04, 0.09, 0.036), "dark", "body", 7, 4)
        m.tube((sx * 0.065, 0.0, 0.06), (sx * 0.07, 0.0, 0.5), 0.038, 0.05, "skin", "body", m.seg(7, 3), caps=False)
    if dress == "aline":                                        # full skirt to mid-calf
        skirt = [(0, 0.01, 0.4, 0, 0), (0, 0.01, 0.4, 0.29, 0.24), (0, 0.01, 0.45, 0.3, 0.25), (0, 0, 0.7, 0.24, 0.19),
                 (0, 0, 0.9, 0.17, 0.135), (0, 0, 1.0, 0.13, 0.105)]
    else:                                                       # fitted, a little longer
        skirt = [(0, 0.0, 0.36, 0, 0), (0, 0.0, 0.36, 0.17, 0.14), (0, 0.0, 0.4, 0.175, 0.145), (0, 0, 0.7, 0.18, 0.145),
                 (0, 0, 0.88, 0.17, 0.135), (0, 0, 1.0, 0.128, 0.104)]
    bodice = [(0, 0, 1.12, 0.14, 0.11), (0, 0, 1.24, 0.158, 0.118), (0, 0, 1.3, 0.16, 0.112), (0, 0, 1.35, 0.12, 0.085),
              (0, 0, 1.38, 0.055, 0.048), (0, 0, 1.38, 0, 0)]
    m.rings(skirt + bodice, "main", "body", sg)
    m.rings([(0, 0, 0.98, 0.1372, 0.1112), (0, 0, 1.03, 0.1372, 0.1112)], "accent", "body", sg)          # belt: a band only
    m.plate([(-0.065, 1.36), (0.065, 1.36), (0.0, 1.25)], -0.122, -0.112, "second", "body")              # collar
    if dress == "aline" and not m.far:                                                                 # hem band
        m.rings([(0, 0.01, 0.405, 0.292, 0.242), (0, 0.01, 0.455, 0.302, 0.252)], "second", "body", sg)


# ================================================================ hats (sit on the crown; bone = head)
def hat(m, kind, plan):
    z = PLAN[plan]["crown"]
    sg = m.seg(18, 6)
    L = lambda prof, slot, sx=1.0, sy=1.0, c=(0, 0.01): m.lathe(prof, slot, "head", sg, c=c, sx=sx, sy=sy, z0=z)
    if kind == "top":
        L([(0, -0.045), (0.175, -0.045), (0.185, -0.03), (0.172, -0.025), (0.104, -0.03), (0.098, 0.03), (0.104, 0.16), (0.108, 0.17), (0, 0.17)], "hat", sy=0.92)
        L([(0, -0.02), (0.101, -0.02), (0.1012, 0.025), (0, 0.025)], "band", sy=0.92)
    elif kind == "boater":
        L([(0, -0.05), (0.2, -0.05), (0.203, -0.036), (0.112, -0.036), (0.11, 0.035), (0.108, 0.04), (0, 0.04)], "hat", sy=0.94)
        L([(0, -0.034), (0.1128, -0.034), (0.1128, 0.0), (0, 0.0)], "band", sy=0.94)
    elif kind == "homburg":
        L([(0, -0.05), (0.165, -0.05), (0.172, -0.03), (0.11, -0.035), (0.112, 0.03), (0.09, 0.075), (0.0, 0.085)], "hat", sy=0.9)
        L([(0, -0.032), (0.112, -0.032), (0.1125, -0.002), (0, -0.002)], "band", sy=0.9)
    elif kind in ("wide", "flower"):
        L([(0, -0.07), (0.29, -0.08), (0.3, -0.07), (0.29, -0.055), (0.11, -0.04), (0.1, 0.02), (0.07, 0.055), (0, 0.06)], "hat")
        L([(0, -0.048), (0.1035, -0.048), (0.1, -0.012), (0, -0.012)], "band")
        if kind == "flower":
            for a, s_ in ((-0.6, 0.048), (-0.15, 0.04), (-1.05, 0.036)):
                m.ellipsoid((0.11 * math.cos(a - 1.2), 0.01 - 0.11 * math.sin(a + 0.4) * 0.9, z - 0.01), (s_, s_, s_ * 0.8), "band", "head", m.seg(8, 5), m.seg(5, 3))
    elif kind == "cloche":
        L([(0, -0.085), (0.135, -0.085), (0.14, -0.07), (0.12, -0.04), (0.106, 0.0), (0.085, 0.05), (0, 0.065)], "hat", c=(0, 0.015))
        L([(0, -0.05), (0.118, -0.05), (0.112, -0.025), (0, -0.025)], "band", c=(0, 0.015))
    elif kind == "fascinator":
        M = Matrix.Translation((0.06, 0.0, z - 0.02)) @ Matrix.Rotation(0.5, 4, "Y") @ Matrix.Rotation(-0.25, 4, "X")
        start = len(m.v)
        m.lathe([(0, -0.006), (0.085, -0.006), (0.085, 0.006), (0, 0.006)], "hat", "head", m.seg(14, 6))
        m.ellipsoid((0.0, 0.0, 0.018), (0.035, 0.035, 0.022), "band", "head", m.seg(8, 5), m.seg(5, 3))
        if not m.far:
            m.tube((0.02, 0.0, 0.02), (0.07, 0.03, 0.17), 0.012, 0.003, "band", "head", 5)              # a feather
        for i in range(start, len(m.v)):
            m.v[i] = M @ m.v[i]


# ================================================================ tiny versions (for people a long way off)
# Silhouettes only: a figure 150 m away is a few pixels tall, so legs, coat or dress, head and hat as a
# handful of five-sided shapes. No arms: the near and far versions carry the movement.
def tiny_body(m, plan, kind):
    P = PLAN[plan]
    hc = P["head_c"]
    if plan == "gent":
        m.rings([(0, 0, 0.0, 0.14, 0.1), (0, 0, 0.78, 0.17, 0.12)], "second", "body", 5)
        hem = 0.5 if kind == "gent_morning" else 0.74
        m.rings([(0, 0, hem, 0, 0), (0, 0, hem, 0.2, 0.15), (0, 0, 1.3, 0.24, 0.16), (0, 0, 1.43, 0.17, 0.11), (0, 0, 1.47, 0, 0)], "main", "body", 5)
    else:
        m.rings([(0, 0, 0.0, 0.08, 0.06), (0, 0, 0.4, 0.09, 0.07)], "skin", "body", 5)
        skirt = 0.3 if kind != "lady_fitted" else 0.19
        m.rings([(0, 0, 0.4, 0, 0), (0, 0, 0.4, skirt, skirt * 0.82), (0, 0, 1.0, 0.14, 0.11), (0, 0, 1.3, 0.18, 0.12), (0, 0, 1.37, 0, 0)], "main", "body", 5)
    rx, ry, rz = P["head_r"]
    m.ellipsoid((0, 0, hc), (rx, ry, rz), "skin", "head", 5, 3)


def tiny_hat(m, kind, plan):
    z = PLAN[plan]["crown"]
    prof = {"top": [(0, -0.04), (0.18, -0.04), (0.105, -0.02), (0.105, 0.17), (0, 0.17)],
            "boater": [(0, -0.045), (0.2, -0.045), (0.11, -0.03), (0.11, 0.04), (0, 0.04)],
            "homburg": [(0, -0.045), (0.17, -0.045), (0.11, -0.03), (0.09, 0.08), (0, 0.08)],
            "wide": [(0, -0.07), (0.3, -0.075), (0.1, -0.04), (0.08, 0.05), (0, 0.06)],
            "flower": [(0, -0.07), (0.3, -0.075), (0.1, -0.04), (0.08, 0.05), (0, 0.06)],
            "cloche": [(0, -0.085), (0.14, -0.08), (0.1, 0.03), (0, 0.065)],
            "fascinator": [(0, -0.01), (0.08, -0.01), (0.08, 0.02), (0, 0.03)]}[kind]
    m.lathe(prof, "hat" if kind != "flower" else "band", "head", 5, c=(0.03 if kind == "fascinator" else 0, 0.01), z0=z)


# ================================================================ props
def binoculars(m, plan):
    P = PLAN[plan]
    y = -P["head_r"][1] - 0.075
    for sx in (-1, 1):
        m.tube((sx * 0.035, y + 0.04, P["head_c"] + 0.015), (sx * 0.038, y - 0.07, P["head_c"] + 0.015), 0.026, 0.03, "prop", "head", m.seg(8, 5), caps=False)
    m.boxm(Matrix.Translation((0, y - 0.01, P["head_c"] + 0.015)), (0.05, 0.04, 0.03), "prop", "head")


def programme(m, plan):
    P = PLAN[plan]
    w = Vector(P["wrist"])
    h = w + Vector((0.0, -0.06, -0.02))
    M = Matrix.Translation(h) @ Matrix.Rotation(-0.35, 4, "X") @ Matrix.Rotation(0.2, 4, "Z")
    m.boxm(M, (0.15, 0.012, 0.21), "prop", "forearm.R")


# ================================================================ rig and actions
def make_rig(plan):
    P = PLAN[plan]
    arm = bpy.data.armatures.new("rig_" + plan)
    ob = bpy.data.objects.new("rig_" + plan, arm)
    scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones
    body = eb.new("body"); body.head = (0, 0, 0); body.tail = (0, 0, 0.95)
    hd = eb.new("head"); hd.head = (0, 0, P["neck"]); hd.tail = (0, 0, P["crown"]); hd.parent = body
    for side, tag in ((-1, "R"), (1, "L")):
        s = Vector((side * -P["shoulder"][0], *P["shoulder"][1:]))
        e = Vector((side * -P["elbow"][0], *P["elbow"][1:]))
        w = Vector((side * -P["wrist"][0], *P["wrist"][1:]))
        u = eb.new("upper_arm." + tag); u.head = s; u.tail = e; u.parent = body
        f = eb.new("forearm." + tag); f.head = e; f.tail = w; f.parent = u; f.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return ob


def ik(S_, H, a, b, pole):
    """Two-bone IK: elbow position for shoulder S_, hand H, bone lengths a, b, bending towards pole."""
    d = H - S_
    L = min(d.length, a + b - 1e-4)
    u = d.normalized()
    cos_t = (a * a + L * L - b * b) / (2 * a * L)
    t = math.acos(max(-1.0, min(1.0, cos_t)))
    v = (pole - u * pole.dot(u)).normalized()
    E = S_ + (u * math.cos(t) + v * math.sin(t)) * a
    return E, S_ + u * L


def aim(rig, name, direction):
    """Turn a bone (with its parents already posed) so it points along `direction` (armature space)."""
    pb = rig.pose.bones[name]
    pb.rotation_quaternion = Quaternion()
    bpy.context.view_layer.update()
    M = pb.matrix.to_quaternion()
    cur = pb.matrix.col[1].xyz.normalized()
    qw = cur.rotation_difference(direction.normalized())
    pb.rotation_quaternion = M.inverted() @ qw @ M
    bpy.context.view_layer.update()


# Actions, after the sheet: hand targets per key time (seconds), in the figure's own frame (x right of
# centre is +x, front is -y). None = arm at rest. head = (yaw, pitch) degrees; lean = body tilt (deg).
def land(plan):
    P = PLAN[plan]
    hc, cr = P["head_c"], P["crown"]
    k = 1.0 if plan == "gent" else 0.94
    return dict(
        chest=lambda dx=0, dy=0, dz=0: Vector((dx, -0.24 * k + dy, 1.2 * k + dz)),
        face=lambda dx=0, dy=0, dz=0: Vector((dx, -0.17 + dy, hc + dz)),
        up=lambda side, dz=0, dx=0: Vector((side * (0.2 + dx), -0.04, cr + 0.32 + dz)),
        brim=lambda: Vector((-0.07, -0.2, cr - 0.03)),
        hc=hc, cr=cr)


def actions_for(plan):
    Lm = land(plan)
    ch, fa, up = Lm["chest"], Lm["face"], Lm["up"]
    A = {}
    # idle: look about, shift weight; hands clasped in front for the gent, at rest for the lady
    A["idle"] = dict(dur=4.0, keys=[
        (0.0, dict(head=(0, 0), lean=(0, 0))), (1.2, dict(head=(-28, 3), lean=(1.0, 0))),
        (2.2, dict(head=(-20, -2), lean=(0.6, 0))), (3.2, dict(head=(16, 2), lean=(-0.8, 0))), (4.0, dict(head=(0, 0), lean=(0, 0)))])
    # clap: hands meet in front of the chest, about three claps a second
    claps = []
    for i in range(7):
        t = i * 0.3
        claps.append((t, dict(R=ch(-0.07, 0, 0.02), L=ch(0.07, 0, 0.02), head=(0, 4))))
        claps.append((t + 0.15, dict(R=ch(-0.005, -0.02, 0.02), L=ch(0.005, -0.02, 0.02), head=(0, 4))))
    claps.append((2.1, claps[0][1]))
    A["clap"] = dict(dur=2.1, keys=claps)
    # cheer: right arm punched up, shaking; the left at rest
    A["cheer_one"] = dict(dur=1.6, keys=[
        (0.0, dict(R=up(-1, -0.02), head=(-6, -10), lean=(0, -2))), (0.4, dict(R=up(-1, -0.1, 0.05), head=(-6, -12), lean=(0, -2))),
        (0.8, dict(R=up(-1, 0.0, -0.03), head=(-6, -10), lean=(0, -2))), (1.2, dict(R=up(-1, -0.1, 0.05), head=(-6, -12), lean=(0, -2))),
        (1.6, dict(R=up(-1, -0.02), head=(-6, -10), lean=(0, -2)))])
    # cheer with both arms up
    A["cheer_both"] = dict(dur=1.2, keys=[
        (0.0, dict(R=up(-1, 0.0), L=up(1, 0.0), head=(0, -14), lean=(0, -3))),
        (0.3, dict(R=up(-1, -0.12, 0.06), L=up(1, -0.12, 0.06), head=(0, -10), lean=(0, -2))),
        (0.6, dict(R=up(-1, 0.0), L=up(1, 0.0), head=(0, -14), lean=(0, -3))),
        (0.9, dict(R=up(-1, -0.12, 0.06), L=up(1, -0.12, 0.06), head=(0, -10), lean=(0, -2))),
        (1.2, dict(R=up(-1, 0.0), L=up(1, 0.0), head=(0, -14), lean=(0, -3)))])
    # wave: a hand (or programme) raised and waved side to side
    A["wave"] = dict(dur=1.6, keys=[
        (0.0, dict(R=up(-1, -0.12, 0.08), head=(-8, -6))), (0.4, dict(R=up(-1, -0.12, -0.06), head=(-8, -6))),
        (0.8, dict(R=up(-1, -0.12, 0.08), head=(-8, -6))), (1.2, dict(R=up(-1, -0.12, -0.06), head=(-8, -6))),
        (1.6, dict(R=up(-1, -0.12, 0.08), head=(-8, -6)))])
    # binoculars: both hands to the glasses in front of the eyes, following the race slowly
    A["binoculars"] = dict(dur=4.0, keys=[
        (0.0, dict(R=fa(-0.045, -0.1, -0.005), L=fa(0.045, -0.1, -0.005), head=(-14, -2))),
        (2.0, dict(R=fa(-0.045, -0.1, -0.005), L=fa(0.045, -0.1, -0.005), head=(14, -2))),
        (4.0, dict(R=fa(-0.045, -0.1, -0.005), L=fa(0.045, -0.1, -0.005), head=(-14, -2)))])
    # hat tip: hand up to the brim, a nod, and down again
    A["hat_tip"] = dict(dur=3.0, keys=[
        (0.0, dict(head=(0, 0))), (0.6, dict(R=Lm["brim"](), head=(0, 6))), (1.3, dict(R=Lm["brim"](), head=(0, 14))),
        (1.9, dict(R=Lm["brim"](), head=(0, 4))), (2.5, dict(head=(0, 0))), (3.0, dict(head=(0, 0)))])
    return A


def sample_keys(keys, t, name):
    """Smoothly interpolated value of `name` at time t (cosine ease between keys; None = rest)."""
    t = min(max(t, keys[0][0]), keys[-1][0])
    for (t0, k0), (t1, k1) in zip(keys[:-1], keys[1:]):
        if t0 <= t <= t1:
            f = 0.5 - 0.5 * math.cos(math.pi * (t - t0) / max(1e-6, t1 - t0))
            a, b = k0.get(name), k1.get(name)
            if a is None and b is None:
                return None
            if name in ("head", "lean"):
                a = a or (0, 0); b = b or (0, 0)
                return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            return (a, b, f)
    v = keys[-1][1].get(name)
    if v is None or name in ("head", "lean"):
        return v
    return (v, v, 0.0)


C_GL = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))     # Blender (x, y, z) -> glTF (x, z, -y)


def pose_at(rig, plan, spec, t):
    """Pose the rig at time t of an action: arms by IK to the hand targets, then head and body."""
    P = PLAN[plan]
    for pb in rig.pose.bones:
        pb.rotation_quaternion = Quaternion()
    bpy.context.view_layer.update()
    for side, tag in ((-1, "R"), (1, "L")):
        v = sample_keys(spec["keys"], t, tag)
        if v is None:
            continue
        a, b, f = v
        Rw = Vector((side * -P["wrist"][0], *P["wrist"][1:]))
        a = a if a is not None else Rw
        b = b if b is not None else Rw
        H = a.lerp(b, f)
        up, fo = rig.pose.bones["upper_arm." + tag], rig.pose.bones["forearm." + tag]
        S_ = up.head.copy()
        la, lb = (up.tail - up.head).length, (fo.tail - fo.head).length
        pole = Vector((side * 0.6, 0.6, -0.5))                    # elbows out, back and down
        E, Hn = ik(S_, H, la, lb, pole)
        aim(rig, "upper_arm." + tag, E - S_)
        aim(rig, "forearm." + tag, Hn - E)
    hy, hp = sample_keys(spec["keys"], t, "head") or (0, 0)
    rig.pose.bones["head"].rotation_quaternion = Quaternion((0, 1, 0), math.radians(hy)) @ Quaternion((1, 0, 0), math.radians(hp))
    ly, lx = sample_keys(spec["keys"], t, "lean") or (0, 0)
    rig.pose.bones["body"].rotation_quaternion = Quaternion((0, 0, 1), math.radians(ly)) @ Quaternion((1, 0, 0), math.radians(lx))
    bpy.context.view_layer.update()


def bake_actions(rig, plan):
    A = actions_for(plan)
    rest = {pb.name: pb.bone.matrix_local.copy() for pb in rig.pose.bones}
    out = {}
    rig.animation_data_create()
    for aname, spec in A.items():
        act = bpy.data.actions.new("%s_%s" % (plan, aname))
        act.use_fake_user = True
        rig.animation_data.action = act
        n = int(round(spec["dur"] * FPS))
        frames = []
        for fi in range(n + 1):
            pose_at(rig, plan, spec, fi / FPS)
            if fi < n:                                            # the last frame repeats the first: keep n per loop
                row = []
                for bname in BONES:
                    pb = rig.pose.bones[bname]
                    D = C_GL @ (pb.matrix @ rest[bname].inverted()) @ C_GL.inverted()
                    q = D.to_quaternion(); tr = D.translation
                    row.append([round(q.w, 5), round(q.x, 5), round(q.y, 5), round(q.z, 5), round(tr.x, 5), round(tr.y, 5), round(tr.z, 5)])
                frames.append(row)
            for pb in rig.pose.bones:
                pb.keyframe_insert("rotation_quaternion", frame=fi + 1)
        out[aname] = {"duration": spec["dur"], "frames": frames}
        rig.animation_data.action = None
        track = rig.animation_data.nla_tracks.new(); track.name = act.name
        track.strips.new(act.name, 1, act)
    for pb in rig.pose.bones:
        pb.rotation_quaternion = Quaternion()
    return out


# ================================================================ assemble the kit
DEFAULT = {"skin": "#e8bf9c", "hair": "#4a3426", "main": "#2b3550", "second": "#8a8478", "shirt": "#f4f0e6",
           "accent": "#a8323a", "dark": "#1f1a17", "hat": "#e3c48e", "band": "#2b3550", "prop": "#efe3c4"}


def srgb_lin(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c]


MAT = None


def to_object(m, name, rig, look=None):
    global MAT
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in m.v], [], m.f)
    me.validate()
    for p in me.polygons:
        p.use_smooth = True
    a_slot = me.attributes.new("_slot", "FLOAT", "POINT")
    a_bone = me.attributes.new("_bone", "FLOAT", "POINT")
    a_slot.data.foreach_set("value", [float(s) for s in m.slot])
    a_bone.data.foreach_set("value", [float(b) for b in m.bone])
    col = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    lk = dict(DEFAULT, **(look or {}))
    pal = [srgb_lin(lk[s]) + [1.0] for s in SLOTS]
    for i, s in enumerate(m.slot):
        col.data[i].color = pal[s]
    me.color_attributes.active_color = col
    if MAT is None:
        MAT = bpy.data.materials.new("crowd"); MAT.use_nodes = True
        nt = MAT.node_tree; vc = nt.nodes.new("ShaderNodeVertexColor"); vc.layer_name = "Col"
        nt.links.new(vc.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
        nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    me.materials.append(MAT)
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    for bn in BONES:
        ob.vertex_groups.new(name=bn)
    for i, b in enumerate(m.bone):
        ob.vertex_groups[BONES[b]].add([i], 1.0, "REPLACE")
    ob.parent = rig
    mod = ob.modifiers.new("rig", "ARMATURE"); mod.object = rig
    return ob, len(me.loop_triangles) if me.loop_triangles else sum(len(p.vertices) - 2 for p in me.polygons)


BODIES = {
    "gent_morning": ("gent", lambda m: (gent_body(m, "morning"), arms(m, "gent", "main", "main"), head(m, "gent", "short"))),
    "gent_lounge": ("gent", lambda m: (gent_body(m, "lounge"), arms(m, "gent", "main", "main"), head(m, "gent", "short"))),
    "gent_binoculars": ("gent", lambda m: (gent_body(m, "lounge"), arms(m, "gent", "main", "main"), head(m, "gent", "short"), binoculars(m, "gent"))),
    "lady_aline": ("lady", lambda m: (lady_body(m, "aline"), arms(m, "lady", "main", "skin"), head(m, "lady", "bun"))),
    "lady_fitted": ("lady", lambda m: (lady_body(m, "fitted"), arms(m, "lady", "main", "skin", glove=True), head(m, "lady", "bob"))),
    "lady_programme": ("lady", lambda m: (lady_body(m, "aline"), arms(m, "lady", "main", "skin"), head(m, "lady", "bun"), programme(m, "lady"))),
}
HATS = {"gent": ["top", "boater", "homburg"], "lady": ["wide", "flower", "cloche", "fascinator"]}
LOOKS = {  # default looks, for Blender, Godot and the line-up
    "gent_morning": {"main": "#2a2b30", "second": "#8a8478", "accent": "#cbbd98", "hat": "#1d1d21", "band": "#1d1d21"},
    "gent_lounge": {"main": "#5f6b3a", "second": "#cfc6b0", "accent": "#a8323a", "hat": "#e3c48e", "band": "#a8323a"},
    "gent_binoculars": {"main": "#2b3550", "second": "#4a4c52", "accent": "#a8323a", "hair": "#d8d4cc"},
    "lady_aline": {"main": "#d98c8c", "second": "#efe3c4", "accent": "#efe3c4", "hat": "#efe3c4", "band": "#c0394a"},
    "lady_fitted": {"main": "#2b3550", "second": "#efe3c4", "accent": "#efe3c4", "shirt": "#efe3c4", "hat": "#efe3c4", "band": "#2b3550"},
    "lady_programme": {"main": "#8ea06a", "second": "#efe3c4", "accent": "#b2362f", "prop": "#efe3c4", "hat": "#b2362f", "band": "#efe3c4"},
}

rigs = {plan: make_rig(plan) for plan in ("gent", "lady")}
anims = {plan: bake_actions(rigs[plan], plan) for plan in rigs}
report = []
objs = []
for name, (plan, build) in BODIES.items():
    for far in (False, True):
        m = Mesh(far); build(m)
        ob, t = to_object(m, name + ("_far" if far else ""), rigs[plan], LOOKS.get(name))
        objs.append(ob); report.append((ob.name, t))
    m = Mesh(tiny=True); tiny_body(m, plan, name)
    ob, t = to_object(m, name + "_tiny", rigs[plan], LOOKS.get(name))
    objs.append(ob); report.append((ob.name, t))
for plan, kinds in HATS.items():
    for kind in kinds:
        for far in (False, True):
            m = Mesh(far); hat(m, kind, plan)
            look = {"hat": {"top": "#1d1d21", "boater": "#e3c48e", "homburg": "#4a4c52", "wide": "#efe3c4", "flower": "#e6b97a",
                            "cloche": "#c99aa6", "fascinator": "#2b3550"}[kind],
                    "band": {"top": "#1d1d21", "boater": "#2b3550", "homburg": "#1d1d21", "flower": "#c0394a"}.get(kind, "#a8323a")}
            ob, t = to_object(m, "hat_%s_%s%s" % (plan, kind, "_far" if far else ""), rigs[plan], look)
            objs.append(ob); report.append((ob.name, t))
        m = Mesh(tiny=True); tiny_hat(m, kind, plan)
        ob, t = to_object(m, "hat_%s_%s_tiny" % (plan, kind), rigs[plan], look)
        objs.append(ob); report.append((ob.name, t))
print("crowd kit:", ", ".join("%s %d" % r for r in report), flush=True)

# ================================================================ write
os.makedirs(rp("assets/models/architecture"), exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
for o in list(rigs.values()) + objs:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=rp("assets/models/architecture/crowd_kit.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_skins=True, export_animations=True,
                          export_animation_mode="NLA_TRACKS", export_attributes=True, export_vertex_color="ACTIVE",
                          export_materials="EXPORT")
json.dump({"_about": "Crowd actions from tools/blender/build_crowd.py, for animating instanced racegoers in a vertex shader. Per rig, per action: duration (seconds, loops) and frames (%d per second); each frame holds one rigid transform per bone in glTF axes, [qw, qx, qy, qz, tx, ty, tz], to apply to the rest-pose vertices that bone owns (`_bone` attribute): v' = q * v + t. Bones in order: %s." % (FPS, ", ".join(BONES)),
           "fps": FPS, "bones": BONES, "slots": SLOTS,
           "rigs": {plan: {"actions": anims[plan]} for plan in anims},
           "meshes": {"bodies": {n: p for n, (p, _) in BODIES.items()}, "hats": HATS}},
          open(rp("assets/models/architecture/crowd_anims.json"), "w"), separators=(",", ":"))
os.makedirs(rp("assets/models/master"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=rp("assets/models/master/crowd_kit.blend"), compress=True)
print("wrote crowd_kit.glb, crowd_anims.json", flush=True)

# ================================================================ review line-up
if OUT_PNG:
    CAST = [("gent_morning", "top", "idle", 1.2), ("lady_aline", "flower", "clap", 0.15), ("gent_binoculars", "boater", "binoculars", 1.0),
            ("gent_morning", "top", "hat_tip", 1.3), ("lady_fitted", "wide", "cheer_one", 0.4), ("gent_lounge", "boater", "clap", 0.0),
            ("lady_aline", "cloche", "idle", 1.2), ("gent_lounge", "homburg", "cheer_both", 0.3), ("lady_programme", "fascinator", "wave", 0.4),
            ("lady_fitted", "flower", "cheer_both", 0.0), ("gent_lounge", "boater", "cheer_one", 0.4)]
    LUK = [None, {"main": "#efe3c4", "second": "#b2362f", "accent": "#b2362f", "hat": "#e6cf9a", "band": "#c0394a"}, None,
           {"main": "#3a3d44", "second": "#77736c"}, {"main": "#c8693f", "hat": "#efe3c4", "band": "#c8693f"}, {"main": "#2b3550", "second": "#cfc6b0", "band": "#a8323a"},
           {"main": "#9bb4c6", "hat": "#2b3550"}, {"main": "#6a5440", "second": "#5a5348", "hat": "#4a4c52"}, None,
           {"main": "#efe3c4", "accent": "#2b3550", "hat": "#c99aa6", "band": "#d98c8c"}, {"main": "#4f6b3a", "second": "#cfc6b0", "band": "#2b3550"}]
    by_name = {o.name: o for o in objs}
    for o in objs:
        o.hide_render = True
    copies = []
    for i, ((body, hk, act, t), lk) in enumerate(zip(CAST, LUK)):
        plan = BODIES[body][0]
        rig = rigs[plan].copy(); rig.data = rigs[plan].data.copy(); scene.collection.objects.link(rig)
        if rig.animation_data:
            rig.animation_data_clear()
        rig["t"], rig["act"], rig["plan"] = t, act, plan
        x = (i - (len(CAST) - 1) / 2) * 0.72
        rig.location = (x, 0, 0)
        for part in (body, "hat_%s_%s" % (plan, hk)):
            src = by_name[part]
            o = src.copy(); o.data = src.data.copy(); o.hide_render = False
            scene.collection.objects.link(o)
            o.parent = rig; o.modifiers["rig"].object = rig
            if lk:
                lkf = dict(DEFAULT, **LOOKS.get(body, {})); lkf.update(lk)
                pal = [srgb_lin(lkf[s]) + [1.0] for s in SLOTS]
                slots = [0.0] * len(o.data.vertices); o.data.attributes["_slot"].data.foreach_get("value", slots)
                for k, s in enumerate(slots):
                    o.data.color_attributes["Col"].data[k].color = pal[int(s)]
            copies.append(o)
    sc = scene
    for rig in [o for o in sc.objects if o.type == "ARMATURE" and "t" in o.keys()]:
        pose_at(rig, rig["plan"], actions_for(rig["plan"])[rig["act"]], rig["t"])
    for o in list(rigs.values()):
        o.hide_render = True
    sc.render.engine = "CYCLES"; sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.66, 0.72, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object; sun.data.energy = 3.5; sun.data.angle = math.radians(8); sun.data.color = (1.0, 0.93, 0.82)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    bpy.ops.mesh.primitive_plane_add(size=60)
    fl = bpy.context.object
    fm = bpy.data.materials.new("floor"); fm.use_nodes = True
    fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.66, 0.62, 0.55, 1)
    fl.data.materials.append(fm)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 8.4
    cam.location = (0, -12, 2.4)
    cam.rotation_euler = (Vector((0, 0, 0.98)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1800, 560
    sc.view_settings.view_transform = "AgX"
    sc.render.filepath = os.path.abspath(OUT_PNG)
    bpy.ops.render.render(write_still=True)
    print("rendered", OUT_PNG, flush=True)
