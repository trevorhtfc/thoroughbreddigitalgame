"""Build the planting belts and the far-rail advertising boards from the course file's zones.

    python -c "exec(open('tools/blender/build_planting.py').read())"

Reads  courses/ascot.json                         zones.planting (the belt outline: from `gap` to
                                                  gap + depth metres outside the track), the rails
Writes assets/models/course/planting_belts.glb    `planting_hedge`: a low, dense hedge (about 3.5 m,
                                                  lumpy, rounded) a few metres behind the far rails,
                                                  in WORLD axes, place at the origin; `board_navy`,
                                                  `board_white`, `board_green`, `board_cream`: one
                                                  Thoroughbred advertising board each (6 m long, front
                                                  faces +z, origin at the middle of its foot)
       assets/models/course/ad_boards.png         the boards' artwork (four designs, one per row)
       courses/ascot-planting.json                where each board stands, and the rows of leafy trees
                                                  (assets/models/trees/trees.glb) that fill the belt
                                                  behind the hedge and stand above it
       assets/models/master/planting_belts.blend  Blender master

World axes as courses/ascot.json: x east, z south, y up. Like the TV pictures of Ascot's far side: boards
just behind the rail, a hedge closing the view at eye level, and real trees standing behind and above it.
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
NEAR_SIDE_Z, NEAR_SIDE_X = 15.0, 400.0   # boards south of this line (the stand side of the straight) and east of x: left out
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


# ---------------------------------------------------------------- 1) the hedge
# A low, dense hedge a few metres behind the boards closes the view at eye level, so nothing behind
# it needs designing; the trees (placed below, drawn from the leafy tree models) stand behind and above it.
HEDGE_AT, HEDGE_W = GAP + 1.8, 3.2          # middle of the hedge, metres from the turf's edge; its width
STEP = 1.5


def lines_in_belt(dist):
    """Lines running dist metres outside the turf, kept only where the planting belt runs."""
    area = track.buffer(dist, join_style=1, quad_segs=24)
    rings = [area.exterior] + list(area.interiors)
    out = []
    for r in rings:
        part = LineString(r.coords).intersection(belts.buffer(0.6))
        for g in (part.geoms if hasattr(part, "geoms") else [part]):
            if g.geom_type == "LineString" and g.length > 12:
                out.append(g)
    return out


def noise1(s, seed):
    """Smooth 1-D value noise in -1..1 (s in samples)."""
    r = np.random.default_rng(seed).uniform(-1, 1, int(s.max()) + 3)
    i = np.floor(s).astype(int); f = s - i; f = f * f * (3 - 2 * f)
    return r[i] * (1 - f) + r[i + 1] * f


PROFILE = [(-1.0, 0.0), (-0.92, 0.55), (-0.62, 0.9), (-0.2, 1.0), (0.2, 1.0), (0.62, 0.9), (0.92, 0.55), (1.0, 0.0)]
hedge_dark, hedge_mid, hedge_top = srgb("#2e4c25"), srgb("#426d33"), srgb("#76a54b")
me = bpy.data.meshes.new("planting_hedge")
bm = bmesh.new()
cl = bm.loops.layers.color.new("Col")
nrm_all = []
hedge_len = 0.0
for li, ln in enumerate(lines_in_belt(HEDGE_AT)):
    n = max(2, int(ln.length / STEP) + 1)
    ss = np.linspace(0, ln.length, n)
    P = np.array([[ln.interpolate(t).x, ln.interpolate(t).y] for t in ss])
    T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
    N = np.c_[-T[:, 1], T[:, 0]]
    probe = shapely.distance(track, shapely.points(P + N * 1.0)) < shapely.distance(track, shapely.points(P - N * 1.0))
    N[probe] *= -1                                        # N points away from the track
    k = ss / STEP
    H = 3.5 + 0.55 * noise1(k / 4.0, 11 + li) + 0.3 * noise1(k / 1.3, 31 + li)
    bulge = 0.35 * noise1(k / 2.0, 51 + li)
    end = np.clip(np.minimum(ss, ln.length - ss) / 6.0, 0, 1)   # round the ends off
    H *= 0.3 + 0.7 * end
    hedge_len += ln.length
    rows = []
    for i in range(n):
        row = []
        for w, hf in PROFILE:
            off = w * HEDGE_W / 2 * (1 + (bulge[i] if w < 0 else 0) * 0.5)
            x, z = P[i] + N[i] * off
            y = H[i] * hf
            v = bm.verts.new((x, -z, y))
            row.append(v)
            # soft rounded shading: out from the hedge's core, leaning up
            nv = np.array([N[i][0] * w, N[i][1] * w, 0.0]) + np.array([0, 0, 0.9 * hf + 0.2])
            nrm_all.append(nv / np.linalg.norm(nv))
        rows.append(row)
    for i in range(n - 1):
        for j in range(len(PROFILE) - 1):
            f = bm.faces.new((rows[i][j], rows[i + 1][j], rows[i + 1][j + 1], rows[i][j + 1]))
            f.smooth = True
    mott = rng.uniform(0.82, 1.12, (n, len(PROFILE)))
    cols = {}                                             # by height in the hedge, mottled
    for i in range(n):
        for j, (w, hf) in enumerate(PROFILE):
            c = hedge_dark * (1 - hf) + (hedge_mid * (1 - hf ** 3) + hedge_top * hf ** 3) * hf
            cols[rows[i][j]] = np.clip(c * mott[i, j], 0, 1)
    for f in bm.faces:
        for lp in f.loops:
            if lp.vert in cols:
                lp[cl] = (*cols[lp.vert], 1.0)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.z < -0.2:
        f.normal_flip()
bm.to_mesh(me); bm.free()
nv = np.array(nrm_all)
me.normals_split_custom_set_from_vertices([(a[0], -a[1], a[2]) for a in nv])      # Blender y = -world z
for a_ in [a_ for a_ in me.color_attributes if a_.name != "Col"]:
    me.color_attributes.remove(a_)
me.color_attributes.active_color = me.color_attributes["Col"]
me.color_attributes.render_color_index = me.color_attributes.active_color_index
mat = bpy.data.materials.new("planting_foliage"); mat.use_nodes = True
nt = mat.node_tree; ca = nt.nodes.new("ShaderNodeVertexColor"); ca.layer_name = "Col"
bsdf = nt.nodes["Principled BSDF"]; nt.links.new(ca.outputs["Color"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 1.0
me.materials.append(mat)
belt_ob = bpy.data.objects.new("planting_hedge", me)
scene.collection.objects.link(belt_ob)
print("hedge: %.0f m, %d triangles" % (hedge_len, sum(len(p.vertices) - 2 for p in me.polygons)), flush=True)

# ---------------------------------------------------------------- 1b) the trees behind the hedge
# Rows of the leafy tree models (assets/models/trees/trees.glb), filling the belt behind the hedge:
# a smaller front row, taller rows behind, now and then a poplar. Placed here, drawn by any engine.
KINDS = ["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"]
trees = []
# (owner, 11 Nov 2026: the belts stay as the tracking cameras' backdrop, "a little lower / less dense in the upper
# canopies": the two back rows a size smaller and further apart, fewer poplars)
for r, (dist, spacing, sc) in enumerate(((GAP + 5.5, 8.5, (1.0, 1.3)), (GAP + 11.5, 10.5, (1.12, 1.4)), (GAP + 18.0, 12.5, (1.18, 1.5)))):
    for ln in lines_in_belt(dist):
        s_ = rng.uniform(0, spacing)
        while s_ < ln.length:
            p = ln.interpolate(s_)
            x, z = p.x + rng.uniform(-1.6, 1.6), p.y + rng.uniform(-1.6, 1.6)
            if belts.contains(Point(x, z)):
                kind = "poplar_a" if rng.random() < 0.05 and r > 0 else KINDS[int(rng.integers(len(KINDS)))]
                trees.append([round(x, 2), round(z, 2), kind, round(float(rng.uniform(*sc)), 2), round(float(rng.uniform(0, 360)), 0)])
            s_ += spacing * rng.uniform(0.75, 1.25)
print("belt trees: %d" % len(trees), flush=True)


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
        d.text((530, TH / 2 + 95), "R A C I N G   ·   C L U B", font=ImageFont.truetype(fsans, 64), fill=acc, anchor="lm")
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
        # (owner, 8 Nov: advertising only on the far side of the cameras) none on the grandstand side of the straight
        # course (south of it, east of the stand), where the straight-course cameras look through them
        if p.y > NEAR_SIDE_Z and p.x > NEAR_SIDE_X:
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
json.dump({"_about": "The planting belts round the far rails, as built by tools/blender/build_planting.py from courses/ascot.json (re-run it rather than editing). World axes as courses/ascot.json (x east, z south). boards: x, z, turn (degrees anticlockwise seen from above; 0 = the board's front faces +z, south), design (node board_<design> in the model). trees: x, z, tree (crown and trunk nodes <tree>_crown, <tree>_crown_far and <tree>_trunk in assets/models/trees/trees.glb), scale, turn. The hedge (node planting_hedge) is in world axes already.",
           "model": "assets/models/course/planting_belts.glb", "trees_model": "assets/models/trees/trees.glb",
           "boardLength": BOARD_LEN, "boardsBehindRail": BOARD_BACK, "hedgeBehindRail": HEDGE_AT,
           "boards": place, "trees": trees}, open(rp("courses/ascot-planting.json"), "w"), separators=(",", ":"))
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
