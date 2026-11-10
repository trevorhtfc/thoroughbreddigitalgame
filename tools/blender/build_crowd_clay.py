"""Clay-model crowd figures: the owner's 1C skittle people smoothed into hand-made clay figures (owner, 9 Nov 2026).

    python -c "exec(open('tools/blender/build_crowd_clay.py').read())"

The owner liked the 1C figures (set 8) but wanted them to read more like a living model: smoother forms, no odd
flat tie, softer arms. Two options, built from the same ten people in the same order with the same five tint
slots as set 8, so either can stand in for it in the race view (crowd-figures.js / final-furlong.html):

  set 9   'Smoothed 1C'  the same people and proportions as 1C, rebuilt from soft rounded solids: rounded
                         shoulders and hem, arms as tapered rolls with round elbows tucked into the shoulder,
                         mitten hands, rounded shoes, a pressed-on pillow of waistcoat in place of the tie,
                         and hats with rounded brim edges.
  set 10  'Plasticine'   the same again, pushed further towards a hand-made clay figure: slightly bigger head,
                         chunkier rolled arms and legs, bigger rounded feet and hands, thicker hat brims, and
                         a faint hand-made unevenness over every surface.

Each set also gets a light version for far off (crowd_set_<n>_far.glb: no arms, fewer sides), like 1B for 1C.

Tint slots (materials):  fig_main coat or dress, fig_skin face/neck/hands, fig_hat hat, fig_trim trousers,
waistcoat, belt and hat band, fig_hair hair and shoes. Faceless. Feet at z 0, front faces +y (-z in the .glb).
"""
import json, math, os, random
import bpy, bmesh
from mathutils import Matrix, Vector, noise

REPO = os.path.abspath(".")
OUT = os.path.join(REPO, "assets/models/architecture")
bpy.ops.wm.read_factory_settings(use_empty=True)
MATS = ["fig_main", "fig_skin", "fig_hat", "fig_trim", "fig_hair"]
BASE = {"fig_main": "#3a3f4a", "fig_skin": "#e2b896", "fig_hat": "#1e1f24", "fig_trim": "#8a8c8f", "fig_hair": "#3a3430"}


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


MAT = {}
for n in MATS:
    m = bpy.data.materials.new(n); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb(BASE[n])
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    MAT[n] = m


def spline(ctrl, per):
    """Catmull-Rom through control tuples (every component), 'per' steps between neighbours: smooth profiles."""
    P = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in range(per):
            t = s / per
            out.append(tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                             for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(tuple(ctrl[-1]))
    return out


class Fig:
    """One figure: closed, smooth-shaded rounded solids through a transform stack, one material per face."""

    def __init__(self, sides):
        self.bm = bmesh.new()
        self.stack = [Matrix.Identity(4)]
        self.n = sides            # sides on the big forms (body, dress, hats); limbs use fewer
        self.sheets = []          # faces of open pressed-on panels (oriented by hand, not by the closed-solid pass)

    def push(self, m): self.stack.append(self.stack[-1] @ m)
    def pop(self): self.stack.pop()
    def V(self, p): return self.bm.verts.new(self.stack[-1] @ Vector(p))

    def F(self, vs, mat):
        f = self.bm.faces.new(vs); f.material_index = MATS.index(mat); f.smooth = True
        return f

    def lathe(self, rings, n, mats, phase=0.0, cap0=True, cap1=True):
        """Rings (z, rx, ry[, cx, cy]) from bottom to top; a ring of radius 0 is a pole (a rounded end).
        mats: one name, or one per band between rings. Ends that aren't poles are closed with a centre fan."""
        rows = []
        for r in rings:
            z, rx, ry = r[0], r[1], r[2]
            cx, cy = (r[3], r[4]) if len(r) > 3 else (0.0, 0.0)
            if rx <= 1e-6:
                rows.append([self.V((cx, cy, z))])
            else:
                rows.append([self.V((cx + rx * math.sin(a), cy + ry * math.cos(a), z))
                             for a in (2 * math.pi * (i + phase) / n for i in range(n))])
        mat = lambda k: mats if isinstance(mats, str) else mats[min(k, len(mats) - 1)]
        for k in range(len(rows) - 1):
            a, b = rows[k], rows[k + 1]
            if len(a) == 1 and len(b) == 1: continue
            for i in range(n):
                j = (i + 1) % n
                if len(a) == 1: self.F((a[0], b[i], b[j]), mat(k))
                elif len(b) == 1: self.F((a[i], a[j], b[0]), mat(k))
                else: self.F((a[i], a[j], b[j], b[i]), mat(k))
        for row, want, z, m in ((rows[0], cap0, rings[0], mat(0)), (rows[-1], cap1, rings[-1], mat(len(rows) - 2))):
            if want and len(row) > 1:
                c = self.V((z[3] if len(z) > 3 else 0.0, z[4] if len(z) > 3 else 0.0, z[0]))
                for i in range(n): self.F((row[i], row[(i + 1) % n], c), m)
        return rows

    def egg(self, c, rx, ry, rz, n, m, mat):
        """An ellipsoid: n around, m rings between the poles."""
        rings = [(c[2] - rz, 0, 0, c[0], c[1])]
        for k in range(1, m + 1):
            t = math.pi * k / (m + 1)
            rings.append((c[2] - rz * math.cos(t), rx * math.sin(t), ry * math.sin(t), c[0], c[1]))
        rings.append((c[2] + rz, 0, 0, c[0], c[1]))
        self.lathe(rings, n, mat)

    def roll(self, p0, p1, r0, r1, n, mat, flat=1.0, ends=2):
        """A rolled sausage of clay from p0 to p1: a tapered tube with round ends (hemispheres of r0 and r1)."""
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        rings = [(-r0, 0, 0)]
        for k in range(1, ends + 1):
            t = -math.pi / 2 * (1 - k / (ends + 1))
            rings.append((r0 * math.sin(t), r0 * math.cos(t) * flat, r0 * math.cos(t)))
        rings.append((0.0, r0 * flat, r0))
        rings.append((L, r1 * flat, r1))
        for k in range(1, ends + 1):
            t = math.pi / 2 * k / (ends + 1)
            rings.append((L + r1 * math.sin(t), r1 * math.cos(t) * flat, r1 * math.cos(t)))
        rings.append((L + r1, 0, 0))
        self.push(Matrix.Translation(p0) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4())
        self.lathe(rings, n, mat, phase=0.5)
        self.pop()

    def ring(self, z, rx, ry, rt, n, mat, m=6, cy=0.0):
        """A rolled ring of clay (a collar) round the z axis: a tube of radius rt on an ellipse rx x ry."""
        rows = []
        for k in range(m):
            a = 2 * math.pi * k / m
            R, h = rt * math.cos(a), rt * math.sin(a)
            rows.append([self.V(((rx + R) * math.sin(b), cy + (ry + R) * math.cos(b), z + h))
                         for b in (2 * math.pi * i / n for i in range(n))])
        for k in range(m):
            a, b = rows[k], rows[(k + 1) % m]
            for i in range(n):
                j = (i + 1) % n
                self.F((a[i], a[j], b[j], b[i]), mat)

    def limb(self, pts, radii, n, mat, ends=2):
        """Shoulder - elbow - hand as overlapping rolls: the round ends make soft joints."""
        for k in range(len(pts) - 1):
            self.roll(pts[k], pts[k + 1], radii[k], radii[k + 1], n, mat, ends=ends)

    def pillow(self, surf, z0, z1, w, mat, thick=0.007, rows=7, cols=6):
        """A pressed-on panel of clay on the front of a body (the waistcoat): a V from a rounded tip at z0 to
        width 2w at z1, following the body (surf(z) -> rx, ry), its middle raised by 'thick', its edges sunk in."""
        grid = []
        for r in range(rows + 1):
            v = r / rows
            z = z0 + (z1 - z0) * v
            half = max(0.004, w * v ** 0.7)          # a short open V with a blunt, rounded tip
            rx, ry = surf(z)
            row = []
            for c in range(cols + 1):
                u = -1 + 2 * c / cols
                x = u * half
                y = ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2))
                lift = thick * (1 - u * u) ** 0.6 * math.sin(min(1.0, v * 3, (1 - v) * 6 + 0.25) * math.pi / 2) - 0.002
                row.append(self.V((x, y + lift, z)))
            grid.append(row)
        for r in range(rows):
            for c in range(cols):
                self.sheets.append(self.F((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]), mat))

    def finish(self, lump=0.0, seed=0):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in set(self.sheets)])
        for f in self.sheets:                 # the panels face forwards
            f.normal_update()
            if f.normal.y < 0: f.normal_flip()
        bm.normal_update()
        if lump:                              # a hand-made unevenness: low, soft bumps along the surface
            o = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
            body = {v for f in bm.faces if MATS[f.material_index] in ("fig_main", "fig_trim") for v in f.verts}
            for v in body:                    # coats, dresses and trousers only: hands, faces and hats stay clean
                v.co += v.normal * lump * noise.noise(v.co * 5.0 + o)
            bm.normal_update()

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    def to_object(self, name, coll):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me); self.bm.free()
        for m in MATS: me.materials.append(MAT[m])
        for p in me.polygons: p.use_smooth = True
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


# ---------------------------------------------------------------------------------------- hats
def hat(F, kind, z, n, s=1.0, tall=1.0, wide=1.0, brim=1.0, lite=False):
    """A hat sitting on a head whose crown is near z. Every edge is rounded (a clay hat has no knife edges).
    brim scales the brim's thickness. Hat in fig_hat, band in fig_trim."""
    H, T = "fig_hat", "fig_trim"
    t = 0.012 * brim                                   # brim thickness
    def brimmed(rb, rc, crown, droop=0.0, ey=0.9, cy=0.0):
        """Underside from the head out to a rounded rim, back over the top to the crown, then the crown's own
        profile (z, r, mat) to its rounded top. droop lowers the rim (summer hats)."""
        e = t * 0.5
        rings = [(-0.02, 0, 0), (-0.016 - t, rc * 0.92, rc * 0.92 * ey),
                 (-0.016 - t - droop * 0.6, (rc + rb) / 2, (rc + rb) / 2 * ey),
                 (-0.016 - t - droop, rb - e, (rb - e) * ey), (-0.016 - e - droop, rb, rb * ey),
                 (-0.016 - droop, rb - e, (rb - e) * ey), (-0.016 + 0.002 - droop * 0.6, (rc + rb) / 2, (rc + rb) / 2 * ey),
                 (-0.013, rc * 1.04, rc * 1.04 * ey)]
        if lite:   # far off: a plain brim (under, rim, top), no rounded edge or mid rings
            rings = [rings[0], rings[1], (-0.016 - t * 0.5 - droop, rb, rb * ey), rings[-1]]
        mats = [H] * (len(rings) - 1)
        if lite and len(crown) > 4:   # the crown's band and its rounded top only
            crown = [crown[0], crown[1], crown[-2], crown[-1]]
        for zc, rr, m in crown:
            rings.append((zc, rr, rr * ey)); mats.append(m)
        F.push(Matrix.Translation((0, cy, 0)))
        F.lathe(rings, n, mats)
        F.pop()
    if kind in ("wide", "picture"):
        n = int(n * (1.25 if lite else 1.5))                               # big brims need more sides to stay round
    F.push(Matrix.Translation((0, 0, z)))
    if kind == "top":
        rb, rc, hc = 0.165 * s * wide, 0.096 * s, 0.19 * s * tall
        brimmed(rb, rc, [(-0.008, rc * 1.0, H), (0.03, rc * 1.0, T), (0.034, rc * 1.005, T), (hc - 0.02, rc * 1.07, H),
                         (hc - 0.004, rc * 1.03, H), (hc, rc * 0.8, H), (hc + 0.002, 0, H)])
    elif kind == "boater":
        rb, rc = 0.17 * s * wide, 0.104 * s
        brimmed(rb, rc, [(-0.008, rc, H), (0.03, rc, T), (0.034, rc, T), (0.05, rc * 0.99, H), (0.06, rc * 0.85, H), (0.062, 0, H)])
    elif kind == "bowler":
        rb, rc = 0.148 * s * wide, 0.1 * s
        brimmed(rb, rc, [(-0.008, rc, H), (0.018, rc, T), (0.022, rc * 1.0, T), (0.06, rc * 0.97, H), (0.095 * tall, rc * 0.78, H),
                         (0.118 * tall, rc * 0.45, H), (0.125 * tall, 0, H)], droop=-0.012)
    elif kind == "trilby":
        rb, rc = 0.16 * s * wide, 0.1 * s
        brimmed(rb, rc, [(-0.008, rc, H), (0.016, rc, T), (0.02, rc, T), (0.065, rc * 0.92, H), (0.095, rc * 0.7, H),
                         (0.105, rc * 0.4, H), (0.108, 0, H)], droop=0.008)
    elif kind == "wide":
        rb, rc = 0.3 * s * wide, 0.104 * s
        brimmed(rb, rc, [(-0.008, rc, H), (0.02, rc, T), (0.024, rc, T), (0.065, rc * 0.88, H), (0.085, rc * 0.55, H),
                         (0.09, 0, H)], droop=0.03)
    elif kind == "picture":
        rb, rc = 0.4 * s * wide, 0.1 * s
        brimmed(rb, rc, [(-0.008, rc, H), (0.018, rc, T), (0.022, rc, T), (0.06, rc * 0.82, H), (0.075, rc * 0.45, H),
                         (0.078, 0, H)], droop=0.022)
    elif kind == "cloche":
        rc = 0.112 * s
        F.lathe([(-0.06, 0, 0), (-0.092, rc * 1.15, rc * 1.12, 0, 0.01), (-0.098, rc * 1.3, rc * 1.27, 0, 0.01),
                 (-0.086, rc * 1.33, rc * 1.3, 0, 0.01), (-0.074, rc * 1.12, rc * 1.09), (-0.05, rc * 1.08, rc * 1.05),
                 (-0.03, rc * 1.08, rc * 1.05), (0.02, rc * 1.0, rc * 0.96), (0.06, rc * 0.78, rc * 0.74), (0.08, rc * 0.4, rc * 0.38),
                 (0.085, 0, 0)], n, [H, H, H, H, T, H, H, H, H, H])
    elif kind == "fascinator":
        F.push(Matrix.Translation((0.06 * s, 0.0, -0.02)) @ Matrix.Rotation(0.45, 4, "Y"))
        F.lathe([(0, 0, 0), (0.002, 0.08 * s, 0.08 * s), (0.012, 0.085 * s, 0.085 * s), (0.024, 0.075 * s, 0.075 * s),
                 (0.03, 0, 0)], max(8, n - 2), H)
        F.pop()
        F.roll((0.08 * s, -0.01, 0.01), (0.15 * s, -0.04, 0.16 * s), 0.012, 0.005, 5, T)
    F.pop()


# ---------------------------------------------------------------------------------------- the figure
def clay_figure(var, style):
    """One of the ten 1C people. style 'smooth' keeps 1C's proportions; 'plasticine' pushes them to clay."""
    P = style in ("plasticine", "plump", "plump18")
    # 'plump' (owner, 9 Nov 2026: "marginally plumper ... a bit less pin-like"): the plasticine people a little
    # wider and deeper in the body and limbs, same height and head, so they read stockier, like modelled figures
    W = {"plump": 1.12, "plump18": 1.18}.get(style, 1.0)
    WL = 1 + (W - 1) * 0.6                       # limbs and the skirt's hem: a little less
    far = var.get("_far", False)
    # (plasticine trimmed for the game, 9 Nov 2026: 11 sides on the body, 7 on limbs, fewer rings)
    n = 6 if far else (12 if not P else 10)        # sides on the body and dress
    nl = 4 if far else (8 if not P else 6)         # sides on limbs
    F = Fig(n)
    lady = var["lady"]
    tilt = var.get("tilt", (0.0, 0.0))
    limb_k = 1.22 if P else 1.0                    # chunkier rolled limbs
    head_k = 1.1 if P else 1.0
    per = 1 if far else 2

    if not lady:
        # trousered legs, rolled from the shoe to the hip
        for sx in (-1, 1):
            F.roll((sx * 0.078 * W, 0.0, 0.07), (sx * 0.082 * W, 0.0, 0.82), 0.064 * limb_k * WL, 0.08 * limb_k * W, nl, "fig_trim", ends=1)
            # a rounded shoe, its toe forwards
            F.egg((sx * 0.08 * W, 0.035, 0.04), 0.06 * limb_k * WL, 0.1 * (1.1 if P else 1.0), 0.045, nl, 3 if not far else 2, "fig_hair")
        coat = var.get("coat", 0.72)
        # the coat: the 1C outline, with a hem rolled under and round shoulders running into the collar
        ctrl = [(coat - 0.03, 0.15, 0.108), (coat, 0.178, 0.133), (0.98, 0.166, 0.116), (1.22, 0.19, 0.126),
                (1.36, 0.218, 0.13), (1.43, 0.19, 0.118), (1.48, 0.12, 0.09), (1.505, 0.06, 0.055)]
        if P:   # softer, rounder: a fuller chest, shoulders that slope
            ctrl = [(coat - 0.03, 0.158, 0.118), (coat, 0.188, 0.145), (0.98, 0.178, 0.13), (1.2, 0.198, 0.138),
                    (1.34, 0.212, 0.138), (1.42, 0.18, 0.12), (1.475, 0.115, 0.09), (1.5, 0.06, 0.056)]
        ctrl = [(z, rx * W, ry * W) if z < 1.49 else (z, rx, ry) for z, rx, ry in ctrl]
        body = spline(ctrl, per)
        F.lathe([(coat - 0.04, 0, 0)] + body, n, "fig_main", cap1=True)
        zs = [r[0] for r in body]
        def surf(z):
            for a, b in zip(body, body[1:]):
                if a[0] <= z <= b[0]:
                    t = (z - a[0]) / max(1e-6, b[0] - a[0])
                    return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t
            return body[-1][1], body[-1][2]
        # the waistcoat: a soft pillow of clay pressed into the V of the coat (in place of 1C's flat tie)
        if not far:
            F.pillow(surf, 1.25, 1.43, 0.068 * W, "fig_trim", thick=0.007 if not P else 0.01)
        # a rolled coat collar round the base of the neck: hides the join and softens the shoulders
        if not far: F.ring(1.5 if not P else 1.49, 0.058, 0.05, 0.024 if not P else 0.028, n, "fig_main", m=(5 if P else 6) if not far else 4, cy=-0.004)
        if var["hat"] == "top":                    # morning coat: two soft rolled tails behind, to the knee
            for sx in (-1, 1):
                F.roll((sx * 0.07 * W, -0.085 * W, 0.95), (sx * 0.085 * W, -0.11 * W, 0.52), 0.052 * WL, 0.044 * WL, nl, "fig_main", flat=1.25, ends=1)
        top = 1.5
    else:
        hem = var.get("hem", 0.0)
        ctrl = [(hem, 0.27, 0.235), (hem + 0.015, 0.29, 0.25), (hem + 0.3, 0.255, 0.215), (0.74, 0.165, 0.14),
                (0.94, 0.12, 0.097), (0.985, 0.118, 0.095), (1.03, 0.12, 0.096), (1.2, 0.155, 0.11),
                (1.32, 0.182, 0.112), (1.39, 0.16, 0.1), (1.44, 0.1, 0.075), (1.46, 0.05, 0.045)]
        if P:
            ctrl = [(hem, 0.275, 0.24), (hem + 0.02, 0.3, 0.26), (hem + 0.3, 0.265, 0.225), (0.74, 0.175, 0.15),
                    (0.94, 0.13, 0.105), (0.985, 0.128, 0.103), (1.03, 0.13, 0.104), (1.2, 0.162, 0.118),
                    (1.31, 0.18, 0.118), (1.38, 0.155, 0.104), (1.43, 0.1, 0.078), (1.455, 0.05, 0.046)]
        ctrl = [(z, rx * (WL if z < 0.75 else W), ry * (WL if z < 0.75 else W)) if z < 1.45 else (z, rx, ry) for z, rx, ry in ctrl]
        body = spline(ctrl, per)
        # the belt: the bands between 0.95 and 1.02 in the trim colour (clean, level edges)
        mats = []
        for a, b in zip(body, body[1:]):
            mid = (a[0] + b[0]) / 2
            mats.append("fig_trim" if 0.945 < mid < 1.025 else "fig_main")
        F.lathe([(hem + 0.005, 0, 0)] + body, n, ["fig_main"] + mats, cap1=True)
        if hem > 0:                                # stockinged legs and little shoes below a shorter dress
            for sx in (-1, 1):
                F.roll((sx * 0.07, 0.0, 0.06), (sx * 0.072, 0.0, hem + 0.06), 0.034 * limb_k, 0.042 * limb_k, max(4, nl - 2), "fig_skin", ends=1)
                F.egg((sx * 0.07, 0.03, 0.035), 0.042 * limb_k, 0.075, 0.035, max(4, nl - 2), 2, "fig_hair")
        top = 1.45

    if True:
        # arms: tapered rolls from inside the shoulder to a round elbow and a mitten hand (far off: plain
        # four-sided rolls and a small hand, no cuff, card or bag, so a figure keeps its pose as it changes over)
        k = 0.88 if lady else 1.0
        sh = (0.165 if lady else 0.185, 1.33 if lady else 1.375)
        if P: sh = (sh[0] - 0.018, sh[1] - 0.025)
        sh = (sh[0] * W, sh[1])
        POSE = {   # right side: elbow, hand (as 1C)
            "down": [(0.235, 0.0, 1.1), (0.215, 0.04, 0.88)],
            "hip": [(0.32, -0.03, 1.13), (0.18, 0.03, 0.98)],
            "card": [(0.24, 0.03, 1.1), (0.11, 0.22, 1.15)],
            "clasp": [(0.22, 0.05, 1.09), (0.04, 0.15, 0.98)],
            "bag": [(0.22, 0.08, 1.1), (0.08, 0.18, 1.06)],
        }
        for side, pose in ((1, var.get("arms", ("down", "down"))[0]), (-1, var.get("arms", ("down", "down"))[1])):
            pts = [(side * sh[0], 0.0, sh[1])] + [(side * x * k * (W if x > 0.15 else 1.0), y * W, z * (0.96 if lady else 1.0)) for x, y, z in POSE[pose]]
            if pose == "clasp":
                pts[-1] = (side * 0.04, pts[-1][1], pts[-1][2])
            r = [0.056 * k * limb_k * WL, 0.046 * k * limb_k * WL, 0.04 * k * limb_k * WL]
            F.limb(pts, r, nl, "fig_main", ends=0 if far else (1 if P else 2))
            # the mitten hand, just past the cuff, along the forearm
            e, h = Vector(pts[-2]), Vector(pts[-1])
            hd = (h - e).normalized()
            hc = h + hd * 0.035
            if far:
                F.egg(tuple(h + hd * 0.03), 0.036 * k * limb_k, 0.036 * k * limb_k, 0.04 * k, nl, 1, "fig_skin")
                continue
            # a rolled cuff at the end of the sleeve: the hand comes out of it cleanly (no ragged join)
            F.push(Matrix.Translation(h + hd * 0.008) @ hd.to_track_quat("Z", "Y").to_matrix().to_4x4())
            F.ring(0.0, r[-1] * 0.82, r[-1] * 0.82, r[-1] * 0.42, nl, "fig_main", m=4 if P else 5)
            F.pop()
            F.push(Matrix.Translation(hc) @ hd.to_track_quat("Z", "Y").to_matrix().to_4x4())
            F.egg((0, 0, 0), 0.036 * k * limb_k, 0.032 * k * limb_k, 0.043 * k * (1.1 if P else 1.0), nl, 3 if P else 4, "fig_skin")
            F.pop()
            if pose == "card":                   # a race card, its corners soft
                F.push(Matrix.Translation((hc.x + side * 0.01, hc.y + 0.03, hc.z + 0.07)) @ Matrix.Rotation(-0.5, 4, "X"))
                F.lathe([(-0.07, 0.05, 0.004), (-0.066, 0.052, 0.006), (0.066, 0.052, 0.006), (0.07, 0.05, 0.004)], 4, "fig_trim", phase=0.5)
                F.pop()
            if pose == "bag":                    # a small soft handbag
                F.egg((hc.x, hc.y + 0.03, hc.z - 0.08), 0.085, 0.04, 0.06, nl, 3, "fig_trim")

    # neck and head (the head tilts a little, as 1C)
    F.roll((0, 0, top - 0.05), (0, 0, top + 0.07), 0.046 * (1.12 if P else 1.0), 0.044 * (1.12 if P else 1.0), nl, "fig_skin", ends=1)
    F.push(Matrix.Translation((0, 0, top + 0.035)) @ Matrix.Rotation(tilt[0], 4, "X") @ Matrix.Rotation(tilt[1], 4, "Y"))
    hr = (0.094 if lady else 0.1) * head_k
    F.egg((0, 0.005, 0.1 * head_k), hr, 0.104 * head_k, 0.115 * head_k, n + (1 if P else 0), (5 if P else 6) if not far else 3, "fig_skin")
    if lady:
        F.egg((0, -0.075 * head_k, 0.135 * head_k), 0.07, 0.06, 0.06, nl, 3, "fig_hair")      # hair up in a bun
        F.egg((0, -0.02, 0.15 * head_k), hr * 1.02, 0.1 * head_k, 0.085 * head_k, n, 4, "fig_hair")  # hair over the crown
    hat(F, var["hat"], 0.185 * head_k + (0.012 if P else 0.0), n, s=(0.94 if lady else 1.0) * (1.05 if P else 1.0),
        tall=1.18, wide=var.get("wide", 1.22 if lady else 1.04), brim=1.6 if P else 1.0, lite=far)
    F.pop()
    F.finish(lump=(0.0035 if P and not far else 0.0), seed=var.get("seed", 1))
    return F


# The same ten people, in the same order, as set 8 (1C): five gents, five ladies, each a different hat.
G, L = False, True
PEOPLE = [
    dict(lady=G, hat="top", tilt=(0.06, 0.04), arms=("down", "down"), seed=1),
    dict(lady=G, hat="top", tilt=(-0.04, -0.06), coat=0.6, arms=("card", "down"), seed=2),
    dict(lady=G, hat="boater", tilt=(0.0, 0.08), arms=("hip", "down"), seed=3),
    dict(lady=G, hat="bowler", tilt=(0.08, 0.0), arms=("down", "hip"), seed=4),
    dict(lady=G, hat="trilby", tilt=(0.12, -0.05), arms=("card", "down"), seed=5),
    dict(lady=L, hat="wide", tilt=(0.06, 0.05), arms=("down", "clasp"), seed=6),
    dict(lady=L, hat="picture", tilt=(-0.03, -0.08), hem=0.3, arms=("hip", "down"), seed=7),
    dict(lady=L, hat="fascinator", tilt=(0.1, 0.06), arms=("card", "down"), seed=8),
    dict(lady=L, hat="cloche", tilt=(0.08, -0.03), hem=0.28, arms=("bag", "down"), seed=9),
    dict(lady=L, hat="boater", tilt=(0.02, 0.07), arms=("down", "down"), seed=10),
]
SETS = {9: "smooth", 10: "plasticine", 11: "plump", 12: "plump18"}

summary_path = os.path.join(OUT, "crowd_sets.json")
summary = json.load(open(summary_path)) if os.path.exists(summary_path) else {"sets": {}}
ONLY = [int(x) for x in os.environ.get("CROWD_SETS", "").split(",") if x]
for sid, style in SETS.items():
    if ONLY and sid not in ONLY:
        continue
    for far in (False, True):
        tag = "%d%s" % (sid, "_far" if far else "")
        coll = bpy.data.collections.new("crowd_set_" + tag)
        bpy.context.scene.collection.children.link(coll)
        counts = {}
        for i, var in enumerate(PEOPLE):
            F = clay_figure(dict(var, _far=far), style)
            name = "%s_%02d_%s" % ("lady" if var["lady"] else "gent", i, var["hat"])
            counts[name] = F.tris()
            F.to_object(name, coll)
        vals = list(counts.values())
        summary["sets"][tag] = {"style": style + (" (far)" if far else ""), "figures": counts, "mean": round(sum(vals) / len(vals)), "max": max(vals)}
        print("set %s (%s): triangles %d..%d (mean %d)" % (tag, style, min(vals), max(vals), sum(vals) / len(vals)), flush=True)
        bpy.ops.object.select_all(action="DESELECT")
        for o in coll.objects: o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "crowd_set_%s.glb" % tag), export_format="GLB", use_selection=True,
                                  export_yup=True, export_apply=False, export_animations=False)
        for o in list(coll.objects):              # free the names for the next set (no '.001' in the .glb)
            me = o.data; bpy.data.objects.remove(o); bpy.data.meshes.remove(me)
summary["_about"] = "Crowd figure options: triangles per figure (build_crowd_figure_sets.py; 9 and 10 from build_crowd_clay.py)."
json.dump(summary, open(summary_path, "w"), indent=1)
print("done", flush=True)
