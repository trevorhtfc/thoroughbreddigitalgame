"""Crowd figure options: five sets of faceless racegoers, for the owner to pick a direction.

    python -c "exec(open('tools/blender/build_crowd_figure_sets.py').read())"

Writes assets/models/architecture/crowd_set_<n>.glb for n = 1, 2, 4, 5, 6, and crowd_sets.json (the
triangles per figure). Set 3, the painted cut-outs, is a texture: tools/web/build_crowd_cutouts.py.

  1 Refined skittle   today's simple language with shoulders, a waist, a flared dress, trousered legs,
                      crisper hats and a little tilt of the head (about 250 triangles)
  2 Fashion plate     tall and slender Edwardian proportions: morning coats with tails and waistcoats,
                      cinched long dresses, very wide hats, tall top hats; smooth (about 400)
  4 Low-poly faceted  a few more planes: arms at the sides, a hand on a hip or holding a race card,
                      lapels, hair, flat-shaded (about 300)
  5 Soft painterly    rounded, lumpy masses with dabs of hat and colour, for TV distance (about 250)
  6 Lowry             thin, angular, slightly hunched figures on stick legs (about 200)

No faces, no hands to speak of, adult proportions. Every figure is one mesh with up to five materials,
which are the tint slots the race view colours per person:
  fig_main   coat or dress           fig_skin   face, neck, hands
  fig_hat    the hat                 fig_trim   trousers, waistcoat, lapels, sash, hat band
  fig_hair   hair (ladies' hair, the odd gent's)
The hat is kept as its own part so the crowd shader can still lift it.

Blender axes while building: x across the figure, y forwards (the front faces +y: in the .glb that is
-z, the way the race view's crowd faces), z up. Feet at z 0.
"""
import json, math, os, random
import bpy
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
OUT = os.path.join(REPO, "assets/models/architecture")
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = ["fig_main", "fig_skin", "fig_hat", "fig_trim", "fig_hair"]
BASE = {"fig_main": "#3a3f4a", "fig_skin": "#e2b896", "fig_hat": "#1e1f24", "fig_trim": "#8a8c8f", "fig_hair": "#5a3e2b"}


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


MAT = {}
for n in MATS:
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb(BASE[n])
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    MAT[n] = m


class Fig:
    """A figure's geometry: verts, and faces with a material and a smooth flag, through a transform stack."""

    def __init__(self, smooth=True):
        self.v, self.f = [], []
        self.stack = [Matrix.Identity(4)]
        self.smooth = smooth

    def push(self, m):
        self.stack.append(self.stack[-1] @ m)

    def pop(self):
        self.stack.pop()

    def vert(self, p):
        self.v.append(self.stack[-1] @ Vector(p))
        return len(self.v) - 1

    def face(self, idx, mat, smooth=None):
        # the rings run clockwise seen from above: reversed here, so every face points outwards
        self.f.append((list(reversed(idx)), MATS.index(mat), self.smooth if smooth is None else smooth))

    def tris(self):
        return sum(len(i) - 2 for i, _, _ in self.f)

    # A lofted tube along z: rings of (z, rx, ry[, cx, cy]); mats per band (one name, or a list).
    # Caps close the ends unless the end ring has no radius. phase turns the ring (half a segment).
    def loft(self, rings, n, mats, cap0=True, cap1=True, phase=0.0, lump=None, smooth=None):
        mats = [mats] * (len(rings) - 1) if isinstance(mats, str) else mats
        R = []
        for k, r in enumerate(rings):
            z, rx, ry = r[0], r[1], r[2]
            cx, cy = (r[3], r[4]) if len(r) > 3 else (0.0, 0.0)
            row = []
            for i in range(n):
                a = 2 * math.pi * (i + phase) / n
                s = 1.0 + (lump(k, i) if lump else 0.0)
                row.append(self.vert((cx + rx * s * math.sin(a), cy + ry * s * math.cos(a), z)))
            R.append(row)
        for k in range(len(R) - 1):
            a, b = R[k], R[k + 1]
            for i in range(n):
                j = (i + 1) % n
                self.face((a[i], a[j], b[j], b[i]), mats[k], smooth)
        if cap0:
            self.face(list(reversed(R[0])), mats[0], smooth)
        if cap1:
            self.face(R[-1], mats[-1], smooth)
        return R

    # A tube from p0 to p1 (radii r0, r1), n sides, flattened by 'flat' across its own x.
    def tube(self, p0, p1, r0, r1, n, mat, flat=1.0, smooth=None, phase=0.5):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        self.push(Matrix.Translation(p0) @ rot)
        self.loft([(0, r0 * flat, r0), (d.length, r1 * flat, r1)], n, mat, phase=phase, smooth=smooth)
        self.pop()

    # A jointed limb through several points (shoulder, elbow, hand): one tube per segment.
    def limb(self, pts, radii, n, mat, smooth=None):
        for k in range(len(pts) - 1):
            self.tube(pts[k], pts[k + 1], radii[k], radii[k + 1], n, mat, smooth=smooth)

    # An ellipsoid (heads, hair, blobs): n around, m rings from bottom to top.
    def blob(self, c, rx, ry, rz, n, m, mat, lump=None, smooth=None, phase=0.0):
        rings = []
        for k in range(1, m + 1):
            t = math.pi * k / (m + 1)
            rings.append((c[2] - rz * math.cos(t), rx * math.sin(t), ry * math.sin(t), c[0], c[1]))
        return self.loft(rings, n, mat, lump=lump, smooth=smooth, phase=phase)

    # A flat-ish card (race card, lapel): a thin box from a centre, size and turn.
    def card(self, c, sx, sy, sz, mat, rot=None, smooth=False):
        self.push(Matrix.Translation(c) @ (rot or Matrix.Identity(4)))
        self.loft([(-sz / 2, sx / 2, sy / 2), (sz / 2, sx / 2, sy / 2)], 4, mat, phase=0.5, smooth=smooth)
        self.pop()

    def to_object(self, name, coll):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.v], [], [list(i) for i, _, _ in self.f])
        for m in MATS:
            me.materials.append(MAT[m])
        for p, (_, mi, sm) in zip(me.polygons, self.f):
            p.material_index = mi
            p.use_smooth = sm
        me.validate()
        me.update()
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


def hat(F, kind, z, n, scale=1.0, tilt=(0.0, 0.0), smooth=None, band=True, tall=1.0, wide=1.0):
    """A hat sitting on a head whose crown is at height z. Hat geometry is fig_hat; bands are fig_trim."""
    s = scale
    F.push(Matrix.Translation((0, 0, z)) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    H, T = "fig_hat", "fig_trim" if band else "fig_hat"
    if kind == "top":                                  # top hat: flat brim, tall straight crown
        rb, rc, hc = 0.165 * s * wide, 0.098 * s, 0.19 * s * tall
        F.loft([(-0.03, rb, rb * 0.9), (-0.012, rb, rb * 0.9), (-0.012, rc, rc * 0.88), (0.02, rc, rc * 0.88),
                (0.045, rc * 1.01, rc * 0.89), (hc, rc * 1.06, rc * 0.93)], n, [H, H, T, T, H], smooth=smooth)
    elif kind == "boater":                             # flat brim, low flat crown, a band
        rb, rc = 0.17 * s * wide, 0.105 * s
        F.loft([(-0.025, rb, rb * 0.92), (-0.012, rb, rb * 0.92), (-0.012, rc, rc * 0.9), (0.025, rc, rc * 0.9),
                (0.05, rc, rc * 0.9), (0.06, rc * 0.98, rc * 0.88)], n, [H, H, T, T, H], smooth=smooth)
    elif kind == "bowler":                             # small curled brim, round crown
        rb, rc = 0.15 * s * wide, 0.1 * s
        F.loft([(-0.005, rb, rb * 0.88), (-0.025, rb * 0.93, rb * 0.82), (-0.02, rc, rc * 0.88), (0.0, rc, rc * 0.88),
                (0.05, rc * 0.98, rc * 0.86), (0.1 * tall, rc * 0.75, rc * 0.66), (0.125 * tall, rc * 0.3, rc * 0.27)],
               n, [H, H, T, H, H, H], smooth=smooth)
    elif kind == "trilby":                             # panama or trilby: snap brim, pinched crown
        rb, rc = 0.165 * s * wide, 0.1 * s
        F.loft([(-0.035, rb, rb * 0.9, 0, 0.015), (-0.02, rb, rb * 0.9, 0, 0.015), (-0.02, rc, rc * 0.88), (0.015, rc, rc * 0.88),
                (0.06, rc * 0.92, rc * 0.82), (0.105, rc * 0.62, rc * 0.62, 0, -0.01)], n, [H, H, T, H, H], smooth=smooth)
    elif kind == "cap":                                # flat cap (Lowry): a flat slab with a peak
        rc = 0.11 * s
        F.loft([(-0.01, rc, rc * 1.05, 0, 0.01), (0.03, rc * 1.08, rc * 1.15, 0, 0.03), (0.06, rc * 0.9, rc, 0, 0.02)], n, H, smooth=smooth)
        F.card((0, 0.11 * s, -0.005), 0.15 * s, 0.07 * s, 0.012, H, smooth=False)
    elif kind == "wide":                               # wide-brimmed summer hat, the brim drooping a little
        rb, rc = 0.3 * s * wide, 0.105 * s
        F.loft([(-0.06, rb, rb * 0.95), (-0.04, rb * 0.97, rb * 0.92), (-0.012, rc * 1.2, rc * 1.15), (-0.01, rc, rc * 0.9),
                (0.03, rc, rc * 0.9), (0.075, rc * 0.85, rc * 0.78), (0.09, rc * 0.4, rc * 0.36)], n, [H, H, H, T, H, H], smooth=smooth)
    elif kind == "picture":                            # a very wide picture hat, worn tipped
        rb, rc = 0.4 * s * wide, 0.1 * s
        F.loft([(-0.035, rb, rb * 0.95), (-0.02, rb * 0.98, rb * 0.93), (0.0, rc * 1.3, rc * 1.2), (0.005, rc, rc * 0.9),
                (0.045, rc, rc * 0.9), (0.08, rc * 0.7, rc * 0.62)], n, [H, H, H, T, H], smooth=smooth)
    elif kind == "cloche":                             # close bell hat with a short down-turned brim
        rc = 0.112 * s
        F.loft([(-0.09, rc * 1.35, rc * 1.3, 0, 0.01), (-0.07, rc * 1.08, rc * 1.05), (0.0, rc * 1.05, rc * 1.02),
                (0.05, rc * 0.85, rc * 0.8), (0.08, rc * 0.35, rc * 0.33)], n, [H, T, H, H], smooth=smooth)
    elif kind == "fascinator":                         # a small disc tipped on one side, a feather up
        F.push(Matrix.Translation((0.06 * s, 0.0, -0.02)) @ Matrix.Rotation(0.45, 4, "Y"))
        F.loft([(0, 0.085 * s, 0.085 * s), (0.025, 0.07 * s, 0.07 * s)], max(5, n - 2), H, smooth=smooth)
        F.pop()
        F.tube((0.07 * s, -0.01, 0.0), (0.16 * s, -0.04, 0.17 * s), 0.012, 0.004, 4, "fig_trim", smooth=False)
    elif kind == "pillbox":
        rc = 0.075 * s
        F.push(Matrix.Translation((0.03, 0.02, -0.01)) @ Matrix.Rotation(-0.25, 4, "X"))
        F.loft([(0, rc, rc), (0.055, rc, rc)], n, H, smooth=smooth)
        F.pop()
    F.pop()


# ---------------------------------------------------------------------------------------- set 1
def set1(var, dressed=False, arms=False):
    """Refined skittle: today's figures with a real outline.
    dressed (sets 7 and 8, '1B' and '1C'): Edwardian touches from set 2: coat-tails, taller top hats, wider
    brims, ladies' hair up under the hat. arms (set 8, '1C'): simple arms and hands, in a few poses."""
    F = Fig(smooth=True)
    lady = var["lady"]
    tilt = var.get("tilt", (0.0, 0.0))
    if not lady:
        for sx in (-1, 1):                                                     # trousered legs
            F.loft([(0.0, 0.06, 0.07, sx * 0.075, 0.01), (0.8, 0.08, 0.085, sx * 0.08, 0)], 5, "fig_trim", cap0=False, cap1=False)
        coat = var.get("coat", 0.72)
        F.loft([(coat, 0.18, 0.135), (0.98, 0.165, 0.115), (1.22, 0.19, 0.125), (1.37, 0.225, 0.13),
                (1.45, 0.16, 0.105), (1.5, 0.065, 0.06)], 8, "fig_main", cap1=False)
        if dressed and var["hat"] == "top":                                    # morning coat: tails behind to the knee
            for sx in (-1, 1):
                F.tube((sx * 0.07, -0.09, 0.98), (sx * 0.085, -0.12, 0.5), 0.055, 0.045, 4, "fig_main")
        if dressed:                                                            # the waistcoat in the V of the coat
            a, b, c = F.vert((-0.07, 0.138, 1.45)), F.vert((0.07, 0.138, 1.45)), F.vert((0.0, 0.14, 1.12))
            F.face([c, b, a], "fig_trim", False)
            F.face([a, b, c], "fig_trim", False)
        top = 1.5
    else:
        hem = var.get("hem", 0.0)
        F.loft([(hem, 0.29, 0.25), (hem + 0.3, 0.255, 0.215), (0.74, 0.165, 0.14), (0.95, 0.118, 0.095), (1.02, 0.118, 0.095),
                (1.2, 0.155, 0.11), (1.33, 0.19, 0.11), (1.45, 0.05, 0.045)], 8,
               ["fig_main", "fig_main", "fig_main", "fig_trim", "fig_main", "fig_main", "fig_main"], cap1=False)
        if hem > 0:
            for sx in (-1, 1):
                F.loft([(0.0, 0.035, 0.04, sx * 0.07, 0), (hem + 0.05, 0.045, 0.05, sx * 0.07, 0)], 4, "fig_skin", cap0=False, cap1=False)
        top = 1.45
    if arms:
        k = 0.88 if lady else 1.0
        sh = (0.185 if lady else 0.205, 1.34 if lady else 1.39)
        POSE = {   # right side (shoulder is fixed): elbow, hand
            "down": [(0.235, 0.0, 1.1), (0.215, 0.04, 0.86)],
            "hip": [(0.33, -0.03, 1.13), (0.17, 0.03, 0.97)],
            "card": [(0.24, 0.03, 1.1), (0.11, 0.24, 1.15)],
            "clasp": [(0.22, 0.05, 1.09), (0.03, 0.14, 0.97)],
            "bag": [(0.22, 0.08, 1.1), (0.08, 0.18, 1.06)],
        }
        for side, pose in ((1, var.get("arms", ("down", "down"))[0]), (-1, var.get("arms", ("down", "down"))[1])):
            pts = [(side * sh[0], 0.0, sh[1])] + [(side * x * k, y, z * (0.96 if lady else 1.0)) for x, y, z in POSE[pose]]
            if pose == "clasp":
                pts[-1] = (side * 0.03, pts[-1][1], pts[-1][2])
            F.limb(pts, [0.05 * k, 0.043 * k, 0.037 * k], 5, "fig_main")
            F.blob(pts[-1], 0.03 * k, 0.032 * k, 0.04 * k, 5, 2, "fig_skin")
            if pose == "card":
                F.card((pts[-1][0] + side * 0.015, pts[-1][1] + 0.025, pts[-1][2] + 0.065), 0.1, 0.008, 0.14, "fig_trim",
                       rot=Matrix.Rotation(-0.5, 4, "X"))
            if pose == "bag":
                F.card((pts[-1][0], pts[-1][1] + 0.03, pts[-1][2] - 0.07), 0.16, 0.05, 0.1, "fig_trim", smooth=False)
    F.loft([(top - 0.04, 0.045, 0.045), (top + 0.08, 0.042, 0.042)], 5, "fig_skin", cap0=False, cap1=False)
    F.push(Matrix.Translation((0, 0, top + 0.035)) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    F.blob((0, 0.005, 0.1), 0.094 if lady else 0.1, 0.104, 0.115, 7, 3, "fig_skin")
    if dressed and lady:
        F.blob((0, -0.07, 0.13), 0.07, 0.06, 0.06, 6, 2, "fig_hair")          # hair up in a bun
    if dressed:
        hat(F, var["hat"], 0.185, 8, scale=0.94 if lady else 1.0, tall=1.18, wide=var.get("wide", 1.22 if lady else 1.04))
    else:
        hat(F, var["hat"], 0.185, 8, scale=0.94 if lady else 1.0)
    F.pop()
    return F


def set7(var):
    return set1(var, dressed=True)


def set8(var):
    return set1(var, dressed=True, arms=True)


# ---------------------------------------------------------------------------------------- set 2
def set2(var):
    """Fashion plate: tall, slender, Edwardian."""
    F = Fig(smooth=True)
    lady = var["lady"]
    tilt = var.get("tilt", (0.0, 0.0))
    if not lady:
        for sx in (-1, 1):                                                     # long slim legs
            F.loft([(0.0, 0.045, 0.075, sx * 0.065, 0.015), (0.06, 0.05, 0.06, sx * 0.065, 0), (0.92, 0.07, 0.075, sx * 0.07, 0)], 5, "fig_trim", cap1=False)
        # the coat: fitted at the waist, cut away in front, with tails behind to the back of the knee
        F.loft([(0.9, 0.155, 0.11, 0, -0.01), (1.06, 0.135, 0.1), (1.3, 0.172, 0.115), (1.45, 0.205, 0.115),
                (1.52, 0.13, 0.09), (1.56, 0.06, 0.055)], 9, "fig_main", cap1=False)
        for sx in (-1, 1):
            F.tube((sx * 0.06, -0.075, 1.02), (sx * 0.075, -0.115, 0.52), 0.05, 0.045, 4, "fig_main", flat=1.0)
        F.card((0, 0.104, 1.2), 0.13, 0.03, 0.24, "fig_trim", smooth=True)    # waistcoat
        for sx in (-1, 1):                                                     # arms down, a little forward
            F.limb([(sx * 0.19, 0, 1.44), (sx * 0.215, 0.02, 1.15), (sx * 0.2, 0.06, 0.92)], [0.05, 0.042, 0.038], 5, "fig_main")
            F.blob((sx * 0.2, 0.065, 0.89), 0.03, 0.03, 0.04, 4, 2, "fig_trim")  # gloves
        top = 1.55
    else:
        F.loft([(0.0, 0.36, 0.38, 0, -0.06), (0.18, 0.31, 0.32, 0, -0.04), (0.55, 0.2, 0.18, 0, -0.01), (0.88, 0.12, 0.095),
                (1.0, 0.092, 0.074), (1.06, 0.095, 0.076), (1.22, 0.14, 0.1), (1.37, 0.165, 0.09), (1.48, 0.05, 0.045)],
               10, ["fig_main", "fig_main", "fig_main", "fig_main", "fig_trim", "fig_main", "fig_main", "fig_main"], cap1=False)
        for sx in (-1, 1):
            F.limb([(sx * 0.155, 0, 1.36), (sx * 0.18, 0.0, 1.1), (sx * 0.13, 0.06, 0.95)], [0.042, 0.034, 0.03], 5, "fig_main")
            F.blob((sx * 0.125, 0.07, 0.93), 0.026, 0.026, 0.035, 4, 2, "fig_trim")
        top = 1.48
    F.loft([(top - 0.04, 0.04, 0.04), (top + 0.07, 0.038, 0.038)], 6, "fig_skin", cap0=False, cap1=False)
    F.push(Matrix.Translation((0, 0, top + 0.045)) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    F.blob((0, 0.008, 0.09), 0.08, 0.09, 0.102, 7, 3, "fig_skin")
    if lady:
        F.blob((0, -0.065, 0.13), 0.07, 0.06, 0.06, 6, 3, "fig_hair")          # hair up in a bun
    hat(F, var["hat"], 0.165, 10, scale=0.9 if lady else 0.95, tall=1.18, wide=var.get("wide", 1.15))
    F.pop()
    return F


# ---------------------------------------------------------------------------------------- set 4
ARMS4 = {   # right-arm points (shoulder, elbow, hand) for a gent; the left mirrors unless given
    "down": [(0.2, 0, 1.38), (0.235, 0.0, 1.1), (0.22, 0.03, 0.86)],
    "hip": [(0.2, 0, 1.38), (0.34, -0.02, 1.15), (0.17, 0.02, 0.98)],
    "card": [(0.2, 0, 1.38), (0.23, 0.02, 1.12), (0.12, 0.25, 1.16)],
    "pocket": [(0.2, 0, 1.38), (0.25, -0.02, 1.13), (0.16, 0.03, 0.92)],
    "bag": [(0.2, 0, 1.38), (0.2, 0.1, 1.12), (0.05, 0.16, 1.08)],
}


def set4(var):
    """Low-poly faceted: flat-shaded planes, arms, lapels, hair."""
    F = Fig(smooth=False)
    lady = var["lady"]
    tilt = var.get("tilt", (0.0, 0.0))
    k = 0.9 if lady else 1.0
    if not lady:
        for sx in (-1, 1):
            F.tube((sx * 0.08, 0.005, 0.0), (sx * 0.085, 0, 0.82), 0.06, 0.075, 4, "fig_trim")
        F.loft([(0.74, 0.18, 0.13), (1.0, 0.165, 0.115), (1.26, 0.2, 0.13), (1.4, 0.22, 0.125), (1.5, 0.07, 0.06)], 6, "fig_main", phase=0.5)
        # lapels: a V of the second colour down the chest
        for sx in (-1, 1):
            F.push(Matrix.Translation((sx * 0.04, 0.122, 1.28)) @ Matrix.Rotation(sx * 0.32, 4, "Y"))
            F.card((0, 0, 0), 0.05, 0.02, 0.24, "fig_trim")
            F.pop()
        top = 1.5
    else:
        F.loft([(0.0, 0.28, 0.24), (0.42, 0.21, 0.17), (0.94, 0.12, 0.095), (1.2, 0.155, 0.11), (1.34, 0.175, 0.1), (1.43, 0.06, 0.05)],
               6, ["fig_main", "fig_main", "fig_main", "fig_main", "fig_main"], phase=0.5)
        F.loft([(0.92, 0.125, 0.1), (1.0, 0.125, 0.1)], 6, "fig_trim", phase=0.5)                 # belt
        top = 1.43
    for side in (1, -1):
        pose = var["arms"][0 if side > 0 else 1]
        pts = [(side * x * k, y, z * (0.96 if lady else 1)) for x, y, z in ARMS4[pose]]
        F.limb(pts, [0.05 * k, 0.045 * k, 0.04 * k], 4, "fig_main")
        F.blob(pts[-1], 0.035 * k, 0.035 * k, 0.04 * k, 4, 2, "fig_skin")
        if pose == "card":
            F.card((pts[-1][0] + side * 0.02, pts[-1][1] + 0.03, pts[-1][2] + 0.06), 0.1, 0.008, 0.14, "fig_trim",
                   rot=Matrix.Rotation(-0.5, 4, "X"))
    F.loft([(top - 0.04, 0.045, 0.045), (top + 0.08, 0.042, 0.042)], 4, "fig_skin", cap0=False, cap1=False, phase=0.5)
    F.push(Matrix.Translation((0, 0, top + 0.06)) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    F.blob((0, 0.005, 0.1), 0.088, 0.098, 0.112, 6, 3, "fig_skin")
    if lady:
        hl = var.get("hair", "bob")
        if hl == "long":
            F.loft([(-0.03, 0.12, 0.08, 0, -0.06), (0.1, 0.1, 0.075, 0, -0.04), (0.2, 0.08, 0.06, 0, -0.02)], 5, "fig_hair", phase=0.5)
        else:
            F.blob((0, -0.03, 0.1), 0.1, 0.09, 0.1, 5, 2, "fig_hair")
    hat(F, var["hat"], 0.185, 7, scale=0.94 if lady else 1.0, smooth=False)
    F.pop()
    return F


# ---------------------------------------------------------------------------------------- set 5
def set5(var):
    """Soft painterly: lumpy rounded masses; the hat and a dab of colour carry the figure."""
    F = Fig(smooth=True)
    lady = var["lady"]
    rnd = random.Random(var["seed"])
    noise = {}
    lump = lambda k, i: noise.setdefault((k, i), rnd.uniform(-0.09, 0.09))
    lean = rnd.uniform(-0.04, 0.04)
    F.push(Matrix.Rotation(lean, 4, "Y"))
    if not lady:
        # a mass from the ground up, sloping shoulders running into the head; the trousers a darker dab below,
        # split into two short lumps at the feet
        for sx in (-1, 1):
            F.blob((sx * 0.07, 0.0, 0.2), 0.085, 0.09, 0.24, 5, 2, "fig_trim", lump=lump)
        F.loft([(0.3, 0.16, 0.12), (0.62, 0.175, 0.13), (0.8, 0.2, 0.15), (1.1, 0.215, 0.155), (1.3, 0.225, 0.15), (1.44, 0.15, 0.115), (1.52, 0.075, 0.07)],
               7, ["fig_trim", "fig_trim", "fig_main", "fig_main", "fig_main", "fig_main"], lump=lump, cap0=False, cap1=False)
        F.blob((0.07 * rnd.choice((-1, 1)), 0.135, 1.27), 0.05, 0.035, 0.06, 6, 3, "fig_trim")    # a dab: buttonhole or tie
        top = 1.52
    else:
        F.loft([(0.0, 0.27, 0.24), (0.38, 0.245, 0.205), (0.82, 0.17, 0.135), (1.12, 0.175, 0.135), (1.3, 0.2, 0.13), (1.42, 0.13, 0.1), (1.48, 0.065, 0.055)],
               7, "fig_main", lump=lambda k, i: 1.4 * lump(k, i), cap1=False)
        F.blob((0.08 * rnd.choice((-1, 1)), 0.12, 1.22), 0.06, 0.04, 0.055, 6, 3, "fig_trim")     # a corsage
        top = 1.48
    F.pop()
    F.push(Matrix.Translation((rnd.uniform(-0.015, 0.015), 0.01, top + 0.06)) @ Matrix.Rotation(rnd.uniform(-0.12, 0.12), 4, "Y"))
    F.blob((0, 0, 0.075), 0.1, 0.105, 0.115, 6, 3, "fig_skin", lump=lambda k, i: rnd.uniform(-0.06, 0.06))
    if lady:
        F.blob((0, -0.045, 0.09), 0.11, 0.08, 0.1, 5, 2, "fig_hair")
    hat(F, var["hat"], 0.16, 8, scale=1.1, wide=var.get("wide", 1.05))
    if var.get("flower"):
        F.blob((0.12, 0.05, 0.2), 0.065, 0.055, 0.045, 6, 2, "fig_trim")    # a flower on the hat
    F.pop()
    return F


# ---------------------------------------------------------------------------------------- set 6
def set6(var):
    """Lowry: thin, angular, a little hunched, on stick legs."""
    F = Fig(smooth=False)
    lady = var["lady"]
    lean = var.get("lean", 0.12)
    rnd = random.Random(var["seed"])
    spread = rnd.uniform(0.05, 0.085)
    # the body leans: a shear forwards (+y) that grows with height
    shear = Matrix.Identity(4)
    shear[1][2] = lean * 0.55
    for sx in (-1, 1):                                                      # stick legs, feet a dark nub
        F.tube((sx * spread, 0.01, 0.03), (sx * 0.05, 0.0, 0.7 if not lady else 0.55), 0.028, 0.035, 4, "fig_trim" if not lady else "fig_skin")
        F.card((sx * spread, 0.03, 0.02), 0.05, 0.11, 0.04, "fig_trim" if not lady else "fig_main")   # shoes
    F.push(shear)
    if not lady:
        F.loft([(0.6, 0.15, 0.11), (1.0, 0.14, 0.105), (1.3, 0.16, 0.11), (1.38, 0.15, 0.1), (1.44, 0.06, 0.05)], 5, "fig_main", phase=0.5)
        top = 1.44
    else:
        F.loft([(0.42, 0.19, 0.15), (0.8, 0.135, 0.1), (0.95, 0.11, 0.085), (1.22, 0.135, 0.095), (1.32, 0.12, 0.09), (1.38, 0.05, 0.045)],
               5, ["fig_main", "fig_main", "fig_main", "fig_trim", "fig_trim"], phase=0.5)        # a shawl over the shoulders
        top = 1.38
    for sx in (-1, 1):                                                      # thin arms hanging, a little forward
        a = rnd.uniform(0.0, 0.07)
        F.tube((sx * 0.13, 0.0, top - 0.06), (sx * 0.155, 0.04 + a, top - 0.62), 0.032, 0.026, 4, "fig_main")
    F.pop()
    F.push(Matrix.Translation((0, lean * 0.55 * (top + 0.05) + 0.04, top + 0.0)) @ Matrix.Rotation(-lean * 2.0, 4, "X"))
    F.blob((0, 0.01, 0.075), 0.078, 0.084, 0.1, 5, 3, "fig_skin", phase=0.5)
    hat(F, var["hat"], 0.15, 6, scale=0.92, smooth=False, band=var.get("band", False), wide=var.get("wide", 0.9))
    F.pop()
    return F


# ---------------------------------------------------------------------------------------- variants
G, L = False, True
SETS = {
    1: (set1, [
        dict(lady=G, hat="top", tilt=(0.06, 0.04)), dict(lady=G, hat="top", tilt=(-0.04, -0.06), coat=0.6),
        dict(lady=G, hat="boater", tilt=(0.0, 0.08)), dict(lady=G, hat="bowler", tilt=(0.08, 0.0)),
        dict(lady=G, hat="trilby", tilt=(0.02, -0.05)),
        dict(lady=L, hat="wide", tilt=(0.06, 0.05)), dict(lady=L, hat="picture", tilt=(-0.03, -0.08), hem=0.3),
        dict(lady=L, hat="fascinator", tilt=(0.0, 0.06)), dict(lady=L, hat="cloche", tilt=(0.08, -0.03), hem=0.28),
        dict(lady=L, hat="boater", tilt=(0.02, 0.07)),
    ]),
    7: (set7, [
        dict(lady=G, hat="top", tilt=(0.06, 0.04)), dict(lady=G, hat="top", tilt=(-0.04, -0.06), coat=0.6),
        dict(lady=G, hat="boater", tilt=(0.0, 0.08)), dict(lady=G, hat="bowler", tilt=(0.08, 0.0)),
        dict(lady=G, hat="trilby", tilt=(0.02, -0.05)),
        dict(lady=L, hat="wide", tilt=(0.06, 0.05)), dict(lady=L, hat="picture", tilt=(-0.03, -0.08), hem=0.3),
        dict(lady=L, hat="fascinator", tilt=(0.0, 0.06)), dict(lady=L, hat="cloche", tilt=(0.08, -0.03), hem=0.28),
        dict(lady=L, hat="boater", tilt=(0.02, 0.07)),
    ]),
    8: (set8, [
        dict(lady=G, hat="top", tilt=(0.06, 0.04), arms=("down", "down")), dict(lady=G, hat="top", tilt=(-0.04, -0.06), coat=0.6, arms=("card", "down")),
        dict(lady=G, hat="boater", tilt=(0.0, 0.08), arms=("hip", "down")), dict(lady=G, hat="bowler", tilt=(0.08, 0.0), arms=("down", "hip")),
        dict(lady=G, hat="trilby", tilt=(0.12, -0.05), arms=("card", "down")),
        dict(lady=L, hat="wide", tilt=(0.06, 0.05), arms=("down", "clasp")), dict(lady=L, hat="picture", tilt=(-0.03, -0.08), hem=0.3, arms=("hip", "down")),
        dict(lady=L, hat="fascinator", tilt=(0.1, 0.06), arms=("card", "down")), dict(lady=L, hat="cloche", tilt=(0.08, -0.03), hem=0.28, arms=("bag", "down")),
        dict(lady=L, hat="boater", tilt=(0.02, 0.07), arms=("down", "down")),
    ]),
    2: (set2, [
        dict(lady=G, hat="top", tilt=(0.04, 0.03)), dict(lady=G, hat="top", tilt=(-0.05, -0.04)),
        dict(lady=G, hat="bowler", tilt=(0.06, 0.0)), dict(lady=G, hat="boater", tilt=(0.0, -0.06)),
        dict(lady=G, hat="top", tilt=(0.02, 0.06)),
        dict(lady=L, hat="picture", tilt=(0.1, 0.08), wide=1.1), dict(lady=L, hat="wide", tilt=(-0.04, -0.1), wide=1.35),
        dict(lady=L, hat="picture", tilt=(0.03, -0.12), wide=0.95), dict(lady=L, hat="cloche", tilt=(0.06, 0.04)),
        dict(lady=L, hat="fascinator", tilt=(0.0, 0.08)),
    ]),
    4: (set4, [
        dict(lady=G, hat="top", arms=("down", "down"), tilt=(0.04, 0.0)), dict(lady=G, hat="top", arms=("card", "down"), tilt=(0.18, 0.0)),
        dict(lady=G, hat="boater", arms=("hip", "down"), tilt=(0.0, 0.08)), dict(lady=G, hat="bowler", arms=("pocket", "pocket")),
        dict(lady=G, hat="trilby", arms=("down", "card"), tilt=(0.12, -0.04)),
        dict(lady=L, hat="wide", arms=("down", "down"), hair="long"), dict(lady=L, hat="picture", arms=("hip", "down"), tilt=(0.0, -0.08)),
        dict(lady=L, hat="fascinator", arms=("card", "down"), tilt=(0.15, 0.0)), dict(lady=L, hat="cloche", arms=("bag", "down"), hair="bob"),
        dict(lady=L, hat="boater", arms=("down", "hip"), hair="long"),
    ]),
    5: (set5, [
        dict(lady=G, hat="top", seed=1), dict(lady=G, hat="top", seed=2), dict(lady=G, hat="boater", seed=3),
        dict(lady=G, hat="bowler", seed=4), dict(lady=G, hat="trilby", seed=5),
        dict(lady=L, hat="wide", seed=6, flower=True), dict(lady=L, hat="picture", seed=7), dict(lady=L, hat="wide", seed=8, wide=1.3),
        dict(lady=L, hat="cloche", seed=9, flower=True), dict(lady=L, hat="boater", seed=10),
    ]),
    6: (set6, [
        dict(lady=G, hat="bowler", seed=1, lean=0.16), dict(lady=G, hat="top", seed=2, lean=0.08), dict(lady=G, hat="cap", seed=3, lean=0.2),
        dict(lady=G, hat="trilby", seed=4, lean=0.12), dict(lady=G, hat="boater", seed=5, lean=0.1, band=True),
        dict(lady=L, hat="wide", seed=6, lean=0.1, band=True), dict(lady=L, hat="cloche", seed=7, lean=0.16),
        dict(lady=L, hat="picture", seed=8, lean=0.08, band=True, wide=0.8), dict(lady=L, hat="pillbox", seed=9, lean=0.14),
        dict(lady=L, hat="fascinator", seed=10, lean=0.12),
    ]),
}

summary = {"_about": "Crowd figure options (tools/blender/build_crowd_figure_sets.py): triangles per figure.", "sets": {}}
ONLY = [int(x) for x in os.environ.get("CROWD_SETS", "").split(",") if x]
for sid, (build, variants) in SETS.items():
    if ONLY and sid not in ONLY:
        continue
    coll = bpy.data.collections.new("crowd_set_%d" % sid)
    bpy.context.scene.collection.children.link(coll)
    counts = {}
    for i, var in enumerate(variants):
        F = build(var)
        name = "%s_%02d_%s" % ("lady" if var["lady"] else "gent", i, var["hat"])
        ob = F.to_object(name, coll)
        ob.location.x = i * 0.9
        counts[name] = F.tris()
    vals = list(counts.values())
    summary["sets"][str(sid)] = {"figures": counts, "mean": round(sum(vals) / len(vals)), "max": max(vals)}
    print("set %d: %d figures, triangles %d..%d (mean %d)" % (sid, len(vals), min(vals), max(vals), sum(vals) / len(vals)), flush=True)
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects:
        o.select_set(True)
        o.location.x = 0
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "crowd_set_%d.glb" % sid), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=False, export_animations=False)
old = json.load(open(os.path.join(OUT, "crowd_sets.json"))) if ONLY and os.path.exists(os.path.join(OUT, "crowd_sets.json")) else {"sets": {}}
old["sets"].update(summary["sets"]); summary["sets"] = old["sets"]
json.dump(summary, open(os.path.join(OUT, "crowd_sets.json"), "w"), indent=1)
print("done", flush=True)
