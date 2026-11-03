"""Shared building kit for the scripted architecture (grandstand, site components).

Loaded with exec() by the build scripts (a plain import trips over Blender's logging):
    exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())

Kit collects geometry per material name through a transform stack; kit_to_object() turns one Kit
into a single mesh object with one material slot per material name.
"""
import math
import bpy, bmesh
from mathutils import Matrix, Vector


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple((v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (1.0,)


def material(name, hexc, rough=0.85, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = srgb(hexc)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = srgb(hexc)
    return m



class Kit:
    """Collects geometry per material; every piece is placed through a transform stack."""

    def __init__(self):
        self.bms = {}
        self.stack = [Matrix.Identity(4)]
        # far = True builds the light distant version: the same outline and colours with the fine
        # detail (balusters, glazing bars, small iron roundels, round segments) drawn simply.
        self.far = False

    @property
    def M(self):
        return self.stack[-1]

    def push(self, m):
        self.stack.append(self.M @ m)

    def pop(self):
        self.stack.pop()

    def bm(self, mat):
        if mat not in self.bms:
            self.bms[mat] = bmesh.new()
        return self.bms[mat]

    # ---- primitives ----
    def box(self, mat, x0, x1, y0, y1, z0, z1):
        if x1 < x0: x0, x1 = x1, x0
        if y1 < y0: y0, y1 = y1, y0
        if z1 < z0: z0, z1 = z1, z0
        m = Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1))
        bmesh.ops.create_cube(self.bm(mat), size=1.0, matrix=self.M @ m)

    def boxm(self, mat, matrix, sx, sy, sz):
        bmesh.ops.create_cube(self.bm(mat), size=1.0, matrix=self.M @ matrix @ Matrix.Diagonal((sx, sy, sz, 1)))

    def cyl(self, mat, x, y, z0, z1, r0, r1=None, segs=8, smooth=True):
        if self.far:
            segs = min(segs, 6) if max(r0, r1 or r0) > 0.3 else 4
        m = Matrix.Translation((x, y, (z0 + z1) / 2))
        g = bmesh.ops.create_cone(self.bm(mat), cap_ends=True, segments=segs, radius1=r0,
                                  radius2=r0 if r1 is None else r1, depth=z1 - z0, matrix=self.M @ m)
        if smooth:
            self._smooth(g["verts"])

    def disc_y(self, mat, x, y0, y1, z, r, segs=24):
        """A short cylinder whose axis runs along y (a clock face, a medallion)."""
        m = Matrix.Translation((x, (y0 + y1) / 2, z)) @ Matrix.Rotation(math.pi / 2, 4, "X")
        bmesh.ops.create_cone(self.bm(mat), cap_ends=True, segments=segs, radius1=r, radius2=r,
                              depth=abs(y1 - y0), matrix=self.M @ m)

    def sphere(self, mat, x, y, z, r, sub=2, sz=1.0):
        if self.far:
            sub = 1 if r > 1.0 else 0 if r < 0.15 else 1
        m = Matrix.Translation((x, y, z)) @ Matrix.Diagonal((1, 1, sz, 1))
        g = bmesh.ops.create_icosphere(self.bm(mat), subdivisions=sub, radius=r, matrix=self.M @ m)
        self._smooth(g["verts"])

    def ring_y(self, mat, x, y, z, R, r, segs=12, minor=4):
        """A torus standing upright in the x-z plane (an iron roundel)."""
        if self.far:
            if R < 0.15:
                return                                   # the frieze of little rings reads as a band anyway
            segs, minor = 8, 3
        bm = self.bm(mat)
        rows = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            row = []
            for j in range(minor):
                b = 2 * math.pi * j / minor + math.pi / 4
                rr = R + r * math.cos(b)
                p = Vector((x + rr * math.cos(a), y + r * math.sin(b), z + rr * math.sin(a)))
                row.append(bm.verts.new(self.M @ p))
            rows.append(row)
        fs = []
        for i in range(segs):
            for j in range(minor):
                fs.append(bm.faces.new((rows[i][j], rows[(i + 1) % segs][j], rows[(i + 1) % segs][(j + 1) % minor], rows[i][(j + 1) % minor])))
        for f in fs:
            f.smooth = True

    def arc_band(self, mat, cx, cz, r_in, r_out, a0, a1, y0, y1, n=10):
        """A curved band in the x-z plane between angles a0..a1 (an arch rib)."""
        if self.far:
            n = max(3, n // 2)
        bm = self.bm(mat)
        pts = []
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            c, s = math.cos(a), math.sin(a)
            pts.append([bm.verts.new(self.M @ Vector((cx + r * c, y, cz + r * s))) for r in (r_in, r_out) for y in (y0, y1)])
        # order in each slice: (in,y0) (in,y1) (out,y0) (out,y1)
        for i in range(n):
            a, b = pts[i], pts[i + 1]
            bm.faces.new((a[0], b[0], b[1], a[1]))      # inner soffit
            bm.faces.new((a[2], a[3], b[3], b[2]))      # outer
            bm.faces.new((a[0], a[2], b[2], b[0]))      # front
            bm.faces.new((a[1], b[1], b[3], a[3]))      # back
        bm.faces.new((pts[0][0], pts[0][1], pts[0][3], pts[0][2]))
        bm.faces.new((pts[-1][0], pts[-1][2], pts[-1][3], pts[-1][1]))

    def prism_x(self, mat, x0, x1, profile):
        """Extrude a y-z polygon along x."""
        bm = self.bm(mat)
        a = [bm.verts.new(self.M @ Vector((x0, y, z))) for y, z in profile]
        b = [bm.verts.new(self.M @ Vector((x1, y, z))) for y, z in profile]
        bm.faces.new(a[::-1]); bm.faces.new(b)
        n = len(profile)
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))

    def prism_y(self, mat, y0, y1, profile):
        """Extrude an x-z polygon along y."""
        bm = self.bm(mat)
        a = [bm.verts.new(self.M @ Vector((x, y0, z))) for x, z in profile]
        b = [bm.verts.new(self.M @ Vector((x, y1, z))) for x, z in profile]
        bm.faces.new(a); bm.faces.new(b[::-1])
        n = len(profile)
        for i in range(n):
            bm.faces.new((a[(i + 1) % n], a[i], b[i], b[(i + 1) % n]))

    @staticmethod
    def _smooth(verts):
        for f in {f for v in verts for f in v.link_faces}:
            f.smooth = True

    # ---- pieces ----
    def balustrade(self, x0, x1, y, z, h=1.05, mat="trim", spacing=0.34, axis="x", piers=True):
        """Top rail, bottom rail, square balusters, piers at the ends. Along x, or along y at x=y."""
        L = abs(x1 - x0)
        if L < 0.3:
            return
        lo, hi = min(x0, x1), max(x0, x1)

        def bx(a0, a1, b0, b1, z0, z1, m=mat):
            if axis == "x":
                self.box(m, a0, a1, b0, b1, z0, z1)
            else:
                self.box(m, b0, b1, a0, a1, z0, z1)
        bx(lo, hi, y - 0.1, y + 0.1, z + h - 0.1, z + h)              # handrail
        bx(lo, hi, y - 0.08, y + 0.08, z, z + 0.12)                  # plinth rail
        if self.far:                                                 # balusters read as one thin screen
            bx(lo, hi, y - 0.025, y + 0.025, z + 0.12, z + h - 0.1)
            return
        n = max(1, int(L / spacing))
        for i in range(1, n):
            a = lo + L * i / n
            bx(a - 0.042, a + 0.042, y - 0.042, y + 0.042, z + 0.12, z + h - 0.1)
        if piers:
            for a in (lo, hi):
                bx(a - 0.13, a + 0.13, y - 0.13, y + 0.13, z, z + h + 0.06)

    def window(self, x, y, z0, w, h, d=-1, glass="glass", panes=True):
        """A window on a wall face at y; d = which way the face looks (-1 = front, +1 = back)."""
        def yy(a, b):
            return (y + d * a, y + d * b)
        self.box(glass, x - w / 2, x + w / 2, *yy(-0.02, 0.05), z0, z0 + h)
        if self.far:                                                 # one frame box behind the glass
            self.box("trim", x - w / 2 - 0.12, x + w / 2 + 0.12, *yy(0.01, 0.1), z0 - 0.1, z0 + h + 0.15)
            return
        self.box("trim", x - w / 2 - 0.12, x + w / 2 + 0.12, *yy(0, 0.12), z0 - 0.1, z0)            # sill
        self.box("trim", x - w / 2 - 0.12, x + w / 2 + 0.12, *yy(0, 0.1), z0 + h, z0 + h + 0.15)    # head
        if panes:
            self.box("trim", x - 0.04, x + 0.04, *yy(0, 0.09), z0, z0 + h)                         # mullion
            self.box("trim", x - w / 2, x + w / 2, *yy(0, 0.09), z0 + h * 0.62, z0 + h * 0.62 + 0.07)  # transom

    def screen(self, x0, x1, y, z0, h, pane=1.15):
        """A full-height glazed screen at the back of an open gallery: reads as dark and open."""
        self.box("glass", x0 + 0.2, x1 - 0.2, y - 0.02, y + 0.05, z0, z0 + h)
        if self.far:
            self.box("trim", x0, x1, y - 0.12, y, z0 + h, z0 + h + 0.2)
            return
        n = max(1, round((x1 - x0 - 0.4) / pane))
        for i in range(n + 1):
            x = x0 + 0.2 + (x1 - x0 - 0.4) * i / n
            self.box("trim", x - 0.045, x + 0.045, y - 0.07, y, z0, z0 + h)
        self.box("trim", x0 + 0.2, x1 - 0.2, y - 0.07, y, z0 + h * 0.7, z0 + h * 0.7 + 0.06)
        self.box("trim", x0, x1, y - 0.12, y, z0 + h, z0 + h + 0.2)

    def door(self, x, y, z0, w=1.4, h=2.4, d=-1):
        self.box("door", x - w / 2, x + w / 2, y + d * -0.01, y + d * 0.06, z0, z0 + h)
        if self.far:
            return
        self.box("trim", x - w / 2 - 0.15, x + w / 2 + 0.15, y, y + d * 0.14, z0 + h, z0 + h + 0.25)
        self.box("trim", x - w / 2 - 0.15, x - w / 2, y, y + d * 0.1, z0, z0 + h)
        self.box("trim", x + w / 2, x + w / 2 + 0.15, y, y + d * 0.1, z0, z0 + h)

    def hip_roof(self, x0, x1, y0, y1, z, rise, ov=0.6, mat="roof"):
        bm = self.bm(mat)
        X0, X1, Y0, Y1 = x0 - ov, x1 + ov, y0 - ov, y1 + ov
        h = min((Y1 - Y0) / 2, (X1 - X0) / 2 - 0.01)
        yc = (Y0 + Y1) / 2
        v = lambda x, y, zz: bm.verts.new(self.M @ Vector((x, y, zz)))
        b0, b1, b2, b3 = v(X0, Y0, z), v(X1, Y0, z), v(X1, Y1, z), v(X0, Y1, z)
        r0, r1 = v(X0 + h, yc, z + rise), v(X1 - h, yc, z + rise)
        for f in ((b0, b1, r1, r0), (b2, b3, r0, r1), (b3, b0, r0), (b1, b2, r1), (b3, b2, b1, b0)):
            bm.faces.new(f)
        # fascia board round the eaves and a light ridge capping
        self.box("trim", X0, X1, Y0 - 0.05, Y0 + 0.15, z - 0.35, z)
        self.box("trim", X0, X1, Y1 - 0.15, Y1 + 0.05, z - 0.35, z)
        self.box("trim", X0 - 0.05, X0 + 0.15, Y0, Y1, z - 0.35, z)
        self.box("trim", X1 - 0.15, X1 + 0.05, Y0, Y1, z - 0.35, z)
        if X1 - h > X0 + h + 0.2:
            self.box("trim", X0 + h, X1 - h, yc - 0.12, yc + 0.12, z + rise - 0.05, z + rise + 0.12)

    def gable_roof(self, x0, x1, y0, y1, z, pitch_deg, ov=0.8):
        D = y1 - y0
        rise = (D / 2 + ov) * math.tan(math.radians(pitch_deg))
        yc, t = (y0 + y1) / 2, 0.3
        self.prism_x("roof", x0 - ov, x1 + ov, [
            (y0 - ov, z), (y0 - ov, z + t), (yc, z + rise + t), (y1 + ov, z + t), (y1 + ov, z), (yc, z + rise)])
        # gable walls under the roof at both ends, with bargeboards
        for x in (x0, x1):
            self.prism_x("wall", x - 0.2 if x == x0 else x, x if x == x0 else x + 0.2,
                         [(y0, z - 0.01), (y1, z - 0.01), (yc, z + rise - 0.25 * (D / 2) / (D / 2 + ov))])
        self.box("trim", x0 - ov, x1 + ov, yc - 0.15, yc + 0.15, z + rise + t - 0.05, z + rise + t + 0.15)
        self.box("trim", x0 - ov, x1 + ov, y0 - ov - 0.05, y0 - ov + 0.12, z - 0.35, z + 0.05)
        return rise

    def cornice(self, x0, x1, y0, y1, z, ov=0.35, h=0.45):
        self.box("trim", x0 - ov, x1 + ov, y0 - ov, y1 + ov, z, z + h)


def drop_hidden_faces(bm, gap=0.025):
    """Remove faces that would flash (z-fight): a face lying in (nearly) the same plane as other faces that
    face the same way and cover it completely. A covered face goes when what covers it is the same material
    (at the same depth or in front of it), or any material at least 1 mm in front of it. Faces of different
    materials sharing a plane exactly are left alone (which should show is a modelling decision) and
    reported; tools/web/find_coplanar.py lists anything left. Returns (removed, ambiguous)."""
    try:
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
    except ImportError:
        print("drop_hidden_faces: shapely missing (pip install shapely); faces left as they are", flush=True)
        return 0, 0
    from collections import defaultdict
    bm.normal_update()
    groups = defaultdict(list)
    for f in bm.faces:
        if f.calc_area() < 1e-7:
            continue
        n = f.normal
        d = n.dot(f.verts[0].co)
        groups[(round(n.x * 200), round(n.y * 200), round(n.z * 200), math.floor(d / gap))].append((d, f))
    kill, ambiguous = set(), 0
    for key, items in groups.items():
        cand = items + groups.get(key[:3] + (key[3] + 1,), [])
        if len(cand) < 2:
            continue
        n = Vector(key[:3]).normalized()
        u = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized()
        v = n.cross(u)
        poly = {}
        for d, f in cand:
            p = Polygon([(c.co.dot(u), c.co.dot(v)) for c in f.verts])
            poly[f] = p if p.is_valid else p.buffer(0)
        for d, f in sorted(items, key=lambda t: t[0]):            # back first
            if f in kill:
                continue
            A = poly[f]
            cover, other_mat = [], []
            for d2, g in cand:
                if g is f or g in kill or not A.intersects(poly[g]):
                    continue
                if g.material_index == f.material_index and d2 >= d - 1e-6:
                    cover.append(poly[g])
                elif d2 > d + 0.001:
                    cover.append(poly[g])
                elif abs(d2 - d) <= 0.001 and A.intersection(poly[g]).area > 1e-3:
                    other_mat.append(g)
            if cover and A.difference(unary_union(cover)).area < 1e-4 * max(1.0, A.area):
                kill.add(f)
            elif other_mat:
                ambiguous += 1
    # Same material, exactly the same plane, overlapping only in part (two floor slabs meeting with an
    # overlap): cut the overlap out of the smaller face so each spot of the plane is drawn once.
    from shapely import constrained_delaunay_triangles
    planes = defaultdict(list)
    for f in bm.faces:
        if f in kill or f.calc_area() < 1e-7:
            continue
        nk = (round(f.normal.x * 200), round(f.normal.y * 200), round(f.normal.z * 200))
        planes[nk + (f.material_index, round(f.normal.dot(f.verts[0].co) / 0.001))].append(f)
    for key, fs in planes.items():
        if len(fs) < 2:
            continue
        n = Vector(key[:3]).normalized()
        u = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized()
        v = n.cross(u)
        d0 = key[4] * 0.001
        poly = {}
        for f in fs:
            p = Polygon([(c.co.dot(u), c.co.dot(v)) for c in f.verts])
            poly[f] = p if p.is_valid else p.buffer(0)
        acc = None
        for f in sorted(fs, key=lambda f: -poly[f].area):             # the biggest face stays whole
            A = poly[f]
            if acc is not None and A.intersects(acc) and A.intersection(acc).area > 1e-4:
                rest = A.difference(acc)
                kill.add(f)
                if rest.area > 1e-4:
                    for tri in getattr(constrained_delaunay_triangles(rest.buffer(0)), "geoms", []):
                        pts = list(tri.exterior.coords)[:3]
                        vs = [bm.verts.new(u * x + v * y + n * d0) for x, y in pts]
                        try:
                            g = bm.faces.new(vs)
                        except ValueError:
                            continue
                        g.material_index, g.smooth = f.material_index, f.smooth
                        g.normal_update()
                        if g.normal.dot(n) < 0:
                            g.normal_flip()
            acc = A if acc is None else acc.union(A)
    for f in kill:
        bm.faces.remove(f)
    return len(kill), ambiguous


def kit_to_object(k, name, mats, collection):
    """One mesh object with a material slot per material used; returns (object, triangles)."""
    me = bpy.data.meshes.new(name)
    out = bmesh.new()
    names = [n for n in k.bms]
    for idx, n in enumerate(names):
        b = k.bms[n]
        tmp = bpy.data.meshes.new("tmp"); b.to_mesh(tmp); b.free()
        start = len(out.faces)
        out.from_mesh(tmp)
        out.faces.ensure_lookup_table()
        for f in out.faces[start:]:
            f.material_index = idx
        bpy.data.meshes.remove(tmp)
    k.bms = {}
    bmesh.ops.remove_doubles(out, verts=out.verts, dist=0.0005)
    bmesh.ops.recalc_face_normals(out, faces=out.faces)
    gone, amb = drop_hidden_faces(out)
    if gone or amb:
        print("  %s: %d hidden coplanar faces removed%s" % (name, gone, ", %d faces share a plane with another material" % amb if amb else ""), flush=True)
    out.to_mesh(me); out.free()
    for n in names:
        me.materials.append(mats[n])
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    return ob, sum(len(p.vertices) - 2 for p in me.polygons)
