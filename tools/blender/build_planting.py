"""Build the planting belts and the far-rail advertising boards from the course file's zones.

    python -c "exec(open('tools/blender/build_planting.py').read())"

Reads  courses/ascot.json                         zones.planting (the belt outline: from `gap` to
                                                  gap + depth metres outside the track), the rails
Writes assets/models/course/planting_belts.glb    `planting_belt`: one dark, dense tree mass (a lumpy
                                                  canopy of overlapping crowns, vertex-coloured from a
                                                  dark base to sunlit tops) in WORLD axes, place at the
                                                  origin; `board_navy`, `board_white`, `board_green`,
                                                  `board_cream`: one Thoroughbred advertising board each
                                                  (6 m long, front faces +z, origin at the middle of its
                                                  foot), sharing one image
       assets/models/course/ad_boards.png         the boards' artwork (four designs, one per row)
       courses/ascot-boards.json                  where each board stands (x, z, turn, design)
       assets/models/master/planting_belts.blend  Blender master

World axes as courses/ascot.json: x east, z south, y up. Like the TV pictures of Ascot's far side: a
tight wall of trees a few metres behind the outer rail, with a line of boards in front of it.
"""
import json, math, os
import numpy as np
import bpy, bmesh
from mathutils import Matrix, Vector
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import Delaunay, cKDTree
import shapely
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union

REPO = os.path.abspath(".")
def rp(*p): return os.path.join(REPO, *p)

C = json.load(open(rp("courses/ascot.json")))
W = C["trackWidth"]
PL = C["zones"]["planting"]
GAP, DEPTH = PL["gap"], PL["depth"]
BOARD_BACK = 3.0          # boards stand this far behind the outer rail's line (the track edge)
BOARD_LEN, BOARD_H, BOARD_FOOT = 6.0, 1.25, 0.3
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- the track, as the layout builder makes it
loop = np.array(C["roundCourse"]["insideRail"]["points"])
P_in = Polygon(loop)
loop_band = P_in.buffer(W, join_style=1, quad_segs=32).difference(P_in)
sp = C["roundMileSpur"]
s0, s1 = np.array(sp["from"]), np.array(sp["to"])
dv = (s1 - s0) / np.linalg.norm(s1 - s0)
nl = np.array([dv[1], -dv[0]])
spur_band = Polygon([s0, s1, s1 + nl * W, s0 + nl * W])
stalls_x = C["straightMile"]["stalls"][0]
past = C["straightMile"]["carriesOnPastPost"]
track = unary_union([loop_band, spur_band.difference(P_in), box(-past, 0, stalls_x + 12, W)]).buffer(0.01).buffer(-0.01)

belts = unary_union([Polygon(p) for p in PL["polygons"]])
belt_list = list(belts.geoms) if belts.geom_type == "MultiPolygon" else [belts]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return np.array([(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c])


# ---------------------------------------------------------------- 1) the tree mass
def resample_ring(coords, step):
    out = []
    for a, b in zip(coords[:-1], coords[1:]):
        a, b = np.array(a), np.array(b)
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out += [a + (b - a) * k / n for k in range(n)]
    return np.array(out)


def canopy(poly):
    # crowns: a jittered scatter of overlapping domes, with now and then a taller one standing proud
    minx, miny, maxx, maxy = poly.bounds
    gx, gy = np.meshgrid(np.arange(minx, maxx, 6.5), np.arange(miny, maxy, 6.5))
    cpts = np.c_[gx.ravel(), gy.ravel()] + rng.uniform(-2.6, 2.6, (gx.size, 2))
    cpts = cpts[shapely.contains_xy(poly.buffer(1.0), cpts[:, 0], cpts[:, 1])]
    nC = len(cpts)
    dtr = shapely.distance(track, shapely.points(cpts))         # how far behind the rail each crown stands
    front = np.clip((dtr - GAP) / DEPTH, 0, 1)
    tall = rng.random(nC) < 0.06
    rad = rng.uniform(4.6, 7.4, nC) * (0.85 + 0.2 * front) * (1 + 0.25 * tall)
    top = rng.uniform(12.5, 17.5, nC) * (0.88 + 0.16 * front) + tall * rng.uniform(3.0, 5.5, nC)
    tint = rng.random(nC)                                   # per-crown colour variety
    ctree = cKDTree(cpts)

    # surface points: the outline at ground, a ring just inside it at canopy height, and a grid inside
    edge = np.vstack([resample_ring(np.array(r.coords), 2.0) for r in [poly.exterior] + list(poly.interiors)])
    inner = poly.buffer(-1.6, join_style=1)
    rings = [inner] if inner.geom_type == "Polygon" else list(inner.geoms)
    lip = np.vstack([resample_ring(np.array(r.coords), 2.2) for p in rings for r in [p.exterior] + list(p.interiors)])
    gx, gy = np.meshgrid(np.arange(minx, maxx, 2.8), np.arange(miny, maxy, 2.8))
    grid = np.c_[gx.ravel(), gy.ravel()] + rng.uniform(-0.9, 0.9, (gx.size, 2))
    grid = grid[shapely.contains_xy(poly.buffer(-3.0), grid[:, 0], grid[:, 1])]
    pts = np.vstack([edge, lip, grid])
    is_edge = np.r_[np.ones(len(edge), bool), np.zeros(len(lip) + len(grid), bool)]

    # height: the highest crown dome over each point
    h = np.zeros(len(pts)); own = np.zeros(len(pts), int); rel = np.zeros(len(pts))
    for i, nb in enumerate(ctree.query_ball_point(pts, 8.0)):
        best = 0.0
        for c in nb:
            dd = np.linalg.norm(pts[i] - cpts[c]) / rad[c]
            if dd < 1.0:
                cap = 0.3 * top[c]
                v = top[c] - cap + cap * math.sqrt(1 - dd * dd)
                if v > best:
                    best, own[i], rel[i] = v, c, 1 - dd
        if best == 0.0 and len(nb):                           # between crowns: the canopy beneath them
            c = min(nb, key=lambda c: np.linalg.norm(pts[i] - cpts[c]))
            best, own[i], rel[i] = top[c] * 0.62, c, 0.0
        h[i] = best
    # where the belt simply stops (an end cut across it, not its rail-side or back edge), let the trees
    # step down over the last 30 m instead of ending in a wall
    caps = []
    for ring in [poly.exterior] + list(poly.interiors):
        c_ = np.array(ring.coords)
        for p0, p1 in zip(c_[:-1], c_[1:]):
            mid = Point((p0 + p1) / 2)
            if GAP + 2.5 < track.distance(mid) < GAP + DEPTH - 2.5:
                caps.append(LineString([p0, p1]))
    if caps:
        dcap = shapely.distance(unary_union(caps), shapely.points(pts))
        f = np.clip(dcap / 30.0, 0, 1)
        h *= 0.35 + 0.65 * f * f * (3 - 2 * f)
    # the face on the rail side leans out a little at mid height, so it reads as foliage, not a cliff
    h[is_edge] = 0.0
    lipm = np.zeros(len(pts), bool); lipm[len(edge):len(edge) + len(lip)] = True
    h[lipm] *= 0.55

    # normals bent out from each crown's middle, so every crown shades as one soft ball (as the trees do)
    cc = np.c_[cpts[own], top[own] - 0.55 * top[own]]
    nrm = np.c_[pts - cc[:, :2], h - cc[:, 2]]
    nrm[:, :2] /= np.maximum(rad[own], 1.0)[:, None]
    nrm[:, 2] = nrm[:, 2] / np.maximum(0.45 * top[own], 1.0) + 0.35
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)

    # triangles inside the belt only
    tri = Delaunay(pts).simplices
    cen = pts[tri].mean(axis=1)
    keep = shapely.contains_xy(poly, cen[:, 0], cen[:, 1])
    e = np.max([np.linalg.norm(pts[tri[:, a]] - pts[tri[:, b]], axis=1) for a, b in ((0, 1), (1, 2), (2, 0))], axis=0)
    tri = tri[keep & (e < 9.0)]

    # colour: dark base, deep green body, lighter sunlit domes; a few crowns warmer or bluer
    dark, body, lit = srgb("#22391a"), srgb("#38592a"), srgb("#6f9447")
    warm, cool = srgb("#6e7a35"), srgb("#2c5040")
    t = np.clip(h / np.maximum(top[own], 1.0), 0, 1)
    col = dark[None] * (1 - t[:, None]) + body[None] * t[:, None]
    w_ = (rel ** 1.5 * 0.9 * t)[:, None]
    col = col * (1 - w_) + lit[None] * w_
    tw = tint[own]
    col = np.where((tw > 0.86)[:, None], col * 0.55 + warm[None] * 0.45 * np.maximum(t, 0.3)[:, None], col)
    col = np.where((tw < 0.12)[:, None], col * 0.6 + cool[None] * 0.4, col)
    col *= rng.uniform(0.9, 1.08, (len(pts), 1))
    return pts, h, tri, col, nrm


me = bpy.data.meshes.new("planting_belt")
bm = bmesh.new()
cl = bm.loops.layers.color.new("Col")
ntri = 0
all_n = []
for poly in belt_list:
    pts, h, tri, col, nrm = canopy(poly)
    all_n.append(nrm)
    vs = [bm.verts.new((p[0], -p[1], hh)) for p, hh in zip(pts, h)]      # Blender y = -world z
    vid = {v: i for i, v in enumerate(vs)}
    for a, b, c in tri:
        try:
            f = bm.faces.new((vs[a], vs[b], vs[c]))
        except ValueError:
            continue
        f.smooth = True
        for lp in f.loops:
            lp[cl] = (*np.clip(col[vid[lp.vert]], 0, 1), 1.0)
        ntri += 1
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:                                         # every face looks up and outwards
    if f.normal.z < -0.2:
        f.normal_flip()
bm.to_mesh(me); bm.free()
nv = np.vstack(all_n)
me.normals_split_custom_set_from_vertices([(n[0], -n[1], n[2]) for n in nv])   # Blender y = -world z
for a in [a for a in me.color_attributes if a.name != "Col"]:
    me.color_attributes.remove(a)
me.color_attributes.active_color = me.color_attributes["Col"]
me.color_attributes.render_color_index = me.color_attributes.active_color_index
mat = bpy.data.materials.new("planting_foliage"); mat.use_nodes = True
nt = mat.node_tree; ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Col"
bsdf = nt.nodes["Principled BSDF"]; nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 1.0
me.materials.append(mat)
belt_ob = bpy.data.objects.new("planting_belt", me)
scene.collection.objects.link(belt_ob)
print("planting belt: %d triangles over %.0f m2" % (ntri, belts.area), flush=True)


# ---------------------------------------------------------------- 2) the boards' artwork
DESIGNS = [  # (name, ground, ink, accent)
    ("navy", "#1d2b45", "#f1e8d0", "#b8954a"),
    ("white", "#f3f1ea", "#1f5a38", "#1d2b45"),
    ("green", "#1f5a38", "#f4ead2", "#c9a85a"),
    ("cream", "#f4ead2", "#1d2b45", "#1f5a38"),
]
TW, TH = 2048, 428                                         # one row per design, 6 : 1.25
img = Image.new("RGB", (TW, TH * 4))
fontp = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
fsans = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
for r, (name, bg, ink, acc) in enumerate(DESIGNS):
    tile = Image.new("RGB", (TW, TH), bg)
    d = ImageDraw.Draw(tile)
    d.rectangle([14, 14, TW - 15, TH - 15], outline=acc, width=6)
    if r % 2 == 0:                                         # wordmark with the letters spaced out
        word = "THOROUGHBRED"; sp_ = 30
        for size in range(200, 60, -6):                    # the largest that fits inside the border
            f = ImageFont.truetype(fontp, size)
            ws = [d.textlength(ch, font=f) for ch in word]
            if sum(ws) + sp_ * (len(word) - 1) < TW - 260:
                break
        x = (TW - (sum(ws) + sp_ * (len(word) - 1))) / 2
        for ch, w_ in zip(word, ws):
            d.text((x, TH / 2), ch, font=f, fill=ink, anchor="lm"); x += w_ + sp_
    else:                                                  # roundel and a smaller line
        cx, cy, R = 300, TH // 2, 140
        d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=ink, width=12)
        d.ellipse([cx - R + 26, cy - R + 26, cx + R - 26, cy + R - 26], outline=acc, width=5)
        d.text((cx, cy + 6), "T", font=ImageFont.truetype(fontp, 170), fill=ink, anchor="mm")
        d.text((520, TH / 2 - 40), "THOROUGHBRED", font=ImageFont.truetype(fontp, 128), fill=ink, anchor="lm")
        d.text((530, TH / 2 + 95), "R A C I N G   ·   A S C O T", font=ImageFont.truetype(fsans, 64), fill=acc, anchor="lm")
    img.paste(tile, (0, r * TH))
os.makedirs(rp("assets/models/course"), exist_ok=True)
art_path = rp("assets/models/course/ad_boards.png")
img.save(art_path, optimize=True)

bimg = bpy.data.images.load(art_path)
bmat = bpy.data.materials.new("ad_board"); bmat.use_nodes = True
tn = bmat.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = bimg
bb = bmat.node_tree.nodes["Principled BSDF"]
bmat.node_tree.links.new(tn.outputs["Color"], bb.inputs["Base Color"]); bb.inputs["Roughness"].default_value = 0.7
fmat = bpy.data.materials.new("ad_board_frame"); fmat.use_nodes = True
fmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*srgb("#2a2f33"), 1)
fmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6


def board(name, row):
    """6 m panel on two back legs; the front (glTF +z, Blender -y) carries one row of the artwork."""
    mb = bmesh.new()
    uvl = mb.loops.layers.uv.new("UVMap")
    L, H, z0, t = BOARD_LEN, BOARD_H, BOARD_FOOT, 0.06
    bmesh.ops.create_cube(mb, size=1, matrix=Matrix.Translation((0, t / 2, z0 + H / 2)) @ Matrix.Diagonal((L, t, H, 1)))
    for lx in (-L / 2 + 0.5, L / 2 - 0.5):                 # legs and a strut behind
        bmesh.ops.create_cube(mb, size=1, matrix=Matrix.Translation((lx, t + 0.05, (z0 + H) / 2)) @ Matrix.Diagonal((0.08, 0.08, z0 + H, 1)))
        bmesh.ops.create_cube(mb, size=1, matrix=Matrix.Translation((lx, t + 0.45, z0 + H * 0.35)) @ Matrix.Rotation(math.radians(-38), 4, "X") @ Matrix.Diagonal((0.06, 0.06, H * 0.95, 1)))
    v0, v1 = 1 - (row + 1) / 4, 1 - row / 4
    for f in mb.faces:
        front = f.normal.y < -0.9 and f.calc_center_median().y < 0.01
        f.material_index = 0 if front else 1
        for lp in f.loops:
            co = lp.vert.co
            if front:
                lp[uvl].uv = ((co.x + L / 2) / L, v0 + (co.z - z0) / H * (v1 - v0))
            else:
                lp[uvl].uv = (0.02, v0 + 0.02 * (v1 - v0))   # edge and back take the border colour
    m = bpy.data.meshes.new(name); mb.to_mesh(m); mb.free()
    m.materials.append(bmat); m.materials.append(fmat)
    o = bpy.data.objects.new(name, m); scene.collection.objects.link(o)
    o.location.x = 10.0 * row                             # laid out side by side in the master file
    return o


board_obs = [board("board_" + d[0], i) for i, d in enumerate(DESIGNS)]

# ---------------------------------------------------------------- 3) where the boards go
line = track.buffer(BOARD_BACK, join_style=1, quad_segs=24)
rings = [line.exterior] + list(line.interiors)
near_belt = belts.buffer(GAP - BOARD_BACK + 2.0)
place = []
k = 0
for ring in rings:
    ls = LineString(ring.coords)
    n = int(ls.length // (BOARD_LEN + 0.25))
    for i in range(n):
        s = (i + 0.5) * ls.length / n
        p = ls.interpolate(s); a = ls.interpolate(s - 1.0); b = ls.interpolate(s + 1.0)
        if not near_belt.contains(p):
            continue
        tx, tz = b.x - a.x, b.y - a.y
        tl = math.hypot(tx, tz); tx, tz = tx / tl, tz / tl
        nx, nz = -tz, tx                                   # one of the two normals; face it at the track
        if track.distance(Point(p.x + nx * 1.0, p.y + nz * 1.0)) > track.distance(Point(p.x - nx * 1.0, p.y - nz * 1.0)):
            nx, nz = -nx, -nz
        # the board's front faces +z at turn 0; turn is anticlockwise seen from above (about +y)
        turn = math.degrees(math.atan2(nx, nz))
        place.append([round(p.x, 2), round(p.y, 2), round(turn, 1), DESIGNS[k % 4][0]])
        k += 1
json.dump({"_about": "Thoroughbred advertising boards along the far rails, in front of the planting belts. Built by tools/blender/build_planting.py from courses/ascot.json; re-run it rather than editing. Each line: x, z (world axes as courses/ascot.json), turn (degrees anticlockwise seen from above; 0 = the board's front faces +z, south), design (node board_<design> in assets/models/course/planting_belts.glb).",
           "model": "assets/models/course/planting_belts.glb", "length": BOARD_LEN, "behindRail": BOARD_BACK,
           "boards": place}, open(rp("courses/ascot-boards.json"), "w"), indent=0)
print("boards: %d along %.0f m" % (len(place), len(place) * (BOARD_LEN + 0.25)), flush=True)

# ---------------------------------------------------------------- export
bpy.ops.object.select_all(action="DESELECT")
for o in [belt_ob] + board_obs:
    o.select_set(True)
locs = [o.location.copy() for o in board_obs]
for o in board_obs:
    o.location = (0, 0, 0)                                 # each board's own origin at the foot of its middle
bpy.ops.export_scene.gltf(filepath=rp("assets/models/course/planting_belts.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False, export_vertex_color="ACTIVE")
for o, l in zip(board_obs, locs):
    o.location = l
os.makedirs(rp("assets/models/master"), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=rp("assets/models/master/planting_belts.blend"), compress=True)
print("exported planting_belts.glb", flush=True)
