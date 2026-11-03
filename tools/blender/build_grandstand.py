"""Build the cream Victorian grandstand from scripted, snap-together pieces.

    python -c "exec(open('tools/blender/build_grandstand.py').read())"

Reads  assets/models/architecture/victorian_grandstand_layout.json
Writes assets/models/architecture/victorian_grandstand.glb      (one mesh per material: few draw calls)
       assets/models/architecture/victorian_grandstand_crowd_areas.json  (where spectators can stand)
       assets/models/architecture/crowd_people.glb               (simple spectator figures to instance)
       assets/models/master/victorian_grandstand.blend           (Blender master)

The FRONT elevation of reference/architecture/victorian-grandstand-sheet.png is the master.
Sizes are realistic, not the sheet's scale bar: 3.5 m storeys, a stand of about 124 m, a clock tower
of about 28 m. The pieces are chunkier and simpler than the sheet, with the signature features
exaggerated: the clock, the ironwork lace and the stepped verandas.

Pieces (Townscaper-style kit, everything on a 3.5 m bay grid):
  veranda tier   floor slab, columns, balustrade, glazed back wall; tiers step back as they rise
  block storey   windowed wall with a shallow balcony and balustrade in front
  ironwork level open gallery with arched iron lace, roundel frieze and roundel balustrade
  clock tower    pilastered shaft, four big clock faces, cornice, balustraded top, urns, cupola, finial
  pavilion       glazed storeys with balconies under a pitched slate roof and roof lantern
  steps          flights from the lawn up to the terrace, with cheek walls, handrails and newels

Blender coordinates while building: x along the front (left to right as seen from the lawn),
y = into the building (front faces -y), z = up. Origin: ground level, middle of the front.
In the .glb (glTF, y up) the front faces +z.
"""
import json, math, os, sys
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
LAYOUT = json.load(open(os.path.join(REPO, "assets/models/architecture/victorian_grandstand_layout.json")))
OUT_DIR = os.path.join(REPO, "assets/models/architecture")
S, P, BAY = LAYOUT["storey"], LAYOUT["podium"], LAYOUT["bay"]
COL = LAYOUT["colours"]

bpy.ops.wm.read_factory_settings(use_empty=True)


exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())


MATS = {k: material("gs_" + k, v, rough={"glass": 0.25, "gilt": 0.4, "roof": 0.75}.get(k, 0.85),
                    metal={"gilt": 0.3}.get(k, 0.0)) for k, v in COL.items()}


K = Kit()
L = max(s.get("x1", 0) for s in LAYOUT["segments"])
K.push(Matrix.Translation((-L / 2, 0, 0)))          # origin at the middle of the front
CROWD = []          # standing areas: x0, x1, y0, y1, z (Blender coords, local to the stand)


def stand_area(x0, x1, y0, y1, z, kind):
    CROWD.append({"x0": round(x0 - L / 2, 2), "x1": round(x1 - L / 2, 2), "y0": round(y0, 2), "y1": round(y1, 2),
                  "z": round(z, 2), "kind": kind})


def podium(x0, x1, depth, doors=True, arcade=False):
    K.box("podium", x0, x1, 0, depth, 0, P)
    K.box("trim", x0 - 0.05, x1 + 0.05, -0.12, depth, P - 0.25, P)            # string course
    K.box("podium", x0 - 0.05, x1 + 0.05, -0.08, depth, 0, 0.35)               # plinth
    n = max(1, round((x1 - x0) / BAY))
    for i in range(n):
        cx = x0 + (x1 - x0) * (i + 0.5) / n
        if arcade:
            K.box("glass", cx - 1.2, cx + 1.2, -0.03, 0.05, 0.35, 1.9)
            K.arc_band("glass", cx, 1.9, 0.0, 1.2, 0, math.pi, -0.03, 0.05, 8)
            K.arc_band("trim", cx, 1.9, 1.2, 1.45, 0, math.pi, -0.15, 0.0, 8)
        elif doors and i % 2 == 0:
            K.door(cx, 0, 0.0, 1.3, 2.2)
        # rear doors and windows
        K.door(cx, depth, 0.0, 1.3, 2.2, d=1) if i % 3 == 0 else K.window(cx, depth, 1.0, 1.2, 1.2, d=1)


# ------------------------------------------------------------------ veranda wing
def veranda(seg):
    x0, x1, T, D, sb = seg["x0"], seg["x1"], seg["tiers"], seg["depth"], seg["setback"]
    podium(x0, x1, D)
    nb = max(1, round((x1 - x0) / BAY))
    deep = 3.4                                         # depth of each open veranda
    for k in range(T):
        z, yf = P + k * S, k * sb
        top = k == T - 1
        hh = S + (0.6 if top else 0)
        # floor slab: reaches forward over the tier below as a ledge
        K.box("trim", x0, x1, yf - (sb if k else 0) - 0.25, D, z - 0.3, z)
        # interior behind the veranda, with glazed doors
        K.box("wall", x0, x1, yf + deep, D, z, z + hh)
        for i in range(nb):
            cx = x0 + (x1 - x0) * (i + 0.5) / nb
            K.screen(cx - BAY / 2, cx + BAY / 2, yf + deep, z, hh - 0.5)
            K.window(cx, D, z + 0.9, 1.4, 1.6, d=1)
        # columns, a light frieze, front balustrade
        for i in range(nb + 1):
            cx = x0 + (x1 - x0) * i / nb
            K.cyl("trim", cx, yf + 0.35, z, z + hh, 0.15, 0.12)
            K.box("trim", cx - 0.22, cx + 0.22, yf + 0.13, yf + 0.57, z + hh - 0.45, z + hh - 0.2)      # capital
            for sgn in (-1, 1):                                                                        # brackets
                if x0 < cx + sgn * 0.6 < x1:
                    K.arc_band("trim", cx + sgn * 0.75, z + hh - 0.95, 0.62, 0.74,
                               math.pi / 2 if sgn < 0 else 0, math.pi if sgn < 0 else math.pi / 2, yf + 0.3, yf + 0.4, 5)
        K.box("trim", x0, x1, yf + 0.2, yf + 0.5, z + hh - 0.3, z + hh)
        K.balustrade(x0, x1, yf + 0.35, z)
        for x in (x0, x1):
            K.balustrade(yf + 0.35, yf + deep, x, z, axis="y", piers=False)
        stand_area(x0 + 0.4, x1 - 0.4, yf + 0.8, yf + deep - 0.4, z, "veranda")
    zt = P + T * S + 0.6
    yt = (T - 1) * sb
    if seg["roof"] == "flat":
        K.box("trim", x0, x1, yt - 0.4, D, zt - 0.6, zt - 0.3)
        K.cornice(x0, x1, yt - 0.1, D, zt - 0.3, 0.2, 0.3)
        K.balustrade(x0, x1, yt + 0.2, zt, 0.9)
    else:
        rf = seg.get("raised_from")
        if rf:
            K.hip_roof(x0, rf, yt, D, zt - 0.6, 1.5, 0.8)
            K.box("wall", rf, x1, yt + deep, D, zt - 0.6, zt + 0.6)               # clerestory under the raised roof
            for i in range(round((x1 - rf) / BAY)):
                K.cyl("trim", rf + i * BAY, yt + 0.35, zt - 0.6, zt + 0.6, 0.12)
            K.hip_roof(rf, x1, yt, D, zt + 0.6, 1.7, 0.9)
        else:
            K.hip_roof(x0, x1, yt, D, zt - 0.6, 1.6, 0.7)


# ------------------------------------------------------------------ windowed blocks
def block(seg):
    x0, x1, N, D = seg["x0"], seg["x1"], seg["storeys"], seg["depth"]
    podium(x0, x1, D)
    wf = 1.6                                     # wall face behind the balconies
    nb = max(1, round((x1 - x0) / BAY))
    H = P + N * S
    K.box("wall", x0, x1, wf, D, P, H)
    for k in range(N):
        z = P + k * S
        K.box("trim", x0, x1, -0.15, wf, z - 0.28, z)                              # balcony slab
        K.balustrade(x0, x1, 0.1, z)
        for i in range(nb):
            for j in (-0.25, 0.25):
                cx = x0 + (x1 - x0) * (i + 0.5 + j) / nb
                K.window(cx, wf, z + 0.35, 1.0, 2.3)
                K.window(cx, D, z + 0.6, 0.9, 1.9, d=1)
        for i in range(nb + 1):
            K.box("trim", x0 + (x1 - x0) * i / nb - 0.12, x0 + (x1 - x0) * i / nb + 0.12, 0.0, 0.24, z, z + S - 0.28)
        stand_area(x0 + 0.4, x1 - 0.4, 0.45, wf - 0.2, z, "balcony")
    K.box("trim", x0, x1, -0.15, wf, H - 0.28, H)
    K.cornice(x0, x1, 0, D, H, 0.3, 0.4)
    K.box("trim", x0 - 0.3, x1 + 0.3, -0.3, D + 0.3, H + 0.4, H + 0.6)
    K.balustrade(x0, x1, 0.15, H + 0.6)
    K.balustrade(x0, x1, D - 0.15, H + 0.6)
    for x in (x0, x1):
        K.balustrade(0.15, D - 0.15, x, H + 0.6, axis="y", piers=False)
        for k in range(N):                                                       # end windows
            K.box("glass", x - 0.05 if x == x0 else x - 0.02, x + 0.02 if x == x0 else x + 0.05, D / 2 - 0.8, D / 2 + 0.8, P + k * S + 0.6, P + k * S + 2.4)
    if seg.get("chimney"):
        c = seg["chimney"]
        K.box("wall", c - 2, c + 2, D / 2 - 1.5, D / 2 + 1.5, H, H + 3.0)
        K.cornice(c - 2, c + 2, D / 2 - 1.5, D / 2 + 1.5, H + 3.0, 0.2, 0.35)
        for i in range(3):
            K.box("glass", c - 1.4 + i * 1.1, c - 0.9 + i * 1.1, D / 2 - 1.55, D / 2 - 1.45, H + 0.8, H + 2.4)
    if seg.get("roof_room"):
        rx0, rx1 = x0 + 1.5, x1 - 1.0
        K.box("wall", rx0, rx1, 3.5, D - 4, H + 0.6, H + 3.6)
        K.hip_roof(rx0, rx1, 3.5, D - 4, H + 3.6, 1.0, 0.5)
        for i in range(3):
            K.window(rx0 + (rx1 - rx0) * (i + 0.5) / 3, 3.5, H + 1.3, 1.3, 1.6)


# ------------------------------------------------------------------ ironwork bay
def ironwork(seg):
    x0, x1, N, D = seg["x0"], seg["x1"], seg["levels"], seg["depth"]
    podium(x0, x1, D, arcade=True)
    nb = max(1, round((x1 - x0) / BAY))
    deep = 3.4
    H = P + N * S
    for k in range(N):
        z = P + k * S
        K.box("trim", x0, x1, -0.2, D, z - 0.3, z)
        K.box("wall", x0, x1, deep, D, z, z + S)
        for i in range(nb):
            cx = x0 + (x1 - x0) * (i + 0.5) / nb
            K.screen(cx - BAY / 2, cx + BAY / 2, deep, z, S - 0.6)
            K.window(cx, D, z + 0.8, 1.2, 1.7, d=1)
        w = (x1 - x0) / nb
        for i in range(nb + 1):
            cx = x0 + w * i
            K.cyl("iron", cx, 0.3, z, z + S, 0.11, 0.11, 8)
            K.box("iron", cx - 0.2, cx + 0.2, 0.1, 0.5, z, z + 0.3)
        for i in range(nb):
            cx = x0 + w * (i + 0.5)
            # exaggerated lace: a full arch, roundels in the spandrels, a frieze of small roundels
            r = w / 2 - 0.1
            spring = z + S - 0.55 - r * 0.62
            K.arc_band("iron", cx, spring, r - 0.14, r, 0, math.pi, 0.25, 0.35, 12)
            K.arc_band("iron", cx, spring, r - 0.55, r - 0.45, 0.15, math.pi - 0.15, 0.26, 0.34, 10)
            for sgn in (-1, 1):
                K.ring_y("iron", cx + sgn * (w / 2 - 0.42), 0.3, z + S - 0.95, 0.27, 0.045)
            K.ring_y("iron", cx, 0.3, spring + r + 0.02 if spring + r + 0.3 < z + S - 0.45 else z + S - 0.8, 0.2, 0.04)
            K.ring_y("iron", cx, 0.3, z + 0.52, 0.32, 0.05)                                       # balustrade roundels
            for sgn in (-1, 1):
                K.ring_y("iron", cx + sgn * w * 0.3, 0.3, z + 0.52, 0.24, 0.045)
            K.box("iron", cx - w / 2, cx + w / 2, 0.24, 0.36, z + 0.1, z + 0.18)
        K.box("iron", x0, x1, 0.18, 0.42, z + 0.92, z + 1.04)                                      # handrail
        K.box("iron", x0, x1, 0.22, 0.38, z + S - 0.45, z + S - 0.38)                             # frieze rails
        K.box("iron", x0, x1, 0.22, 0.38, z + S - 0.15, z + S - 0.08)
        n = int((x1 - x0) / 0.5)
        for i in range(n):
            K.ring_y("iron", x0 + (i + 0.5) * (x1 - x0) / n, 0.3, z + S - 0.265, 0.1, 0.022, 8, 3)
        stand_area(x0 + 0.4, x1 - 0.4, 0.8, deep - 0.4, z, "ironwork")
    K.box("trim", x0, x1, -0.3, D, H - 0.3, H)
    K.cornice(x0, x1, -0.1, D, H, 0.25, 0.35)
    K.balustrade(x0, x1, 0.1, H + 0.35)


# ------------------------------------------------------------------ clock tower
def tower(seg):
    cx, y0, w, zb, zt = seg["x"], seg["y"], seg["width"], seg["base_z"], seg["top_z"]
    hw, cy = w / 2, y0 + w / 2
    K.box("wall", cx - hw, cx + hw, y0, y0 + w, P, zt)
    for sx in (-1, 1):                                           # corner pilasters
        for sy in (-1, 1):
            px, py = cx + sx * (hw - 0.35), cy + sy * (hw - 0.35)
            K.box("trim", px - 0.5, px + 0.5, py - 0.5, py + 0.5, zb - 1.0, zt)
    K.box("trim", cx - hw - 0.25, cx + hw + 0.25, y0 - 0.25, y0 + w + 0.25, zb - 0.4, zb)   # base band
    zc = zb + (zt - zb) * 0.52
    R = hw - 1.25                                               # a prominent clock, not a cartoon one
    for rot in range(4):
        K.push(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rot * math.pi / 2, 4, "Z") @ Matrix.Translation((-cx, -cy, 0)))
        f = y0                                                  # this face, before rotation
        K.disc_y("trim", cx, f - 0.12, f + 0.1, zc, R + 0.2, 28)
        K.disc_y("clock_dark", cx, f - 0.2, f - 0.1, zc, R + 0.05, 28)
        K.disc_y("clock_face", cx, f - 0.26, f - 0.18, zc, R - 0.1, 28)
        for h in range(12):
            a = h * math.pi / 6
            K.boxm("clock_dark", Matrix.Translation((cx + math.sin(a) * (R - 0.38), f - 0.28, zc + math.cos(a) * (R - 0.38))) @ Matrix.Rotation(-a, 4, "Y"),
                   0.1 if h % 3 else 0.17, 0.04, 0.42 if h % 3 else 0.55)
        for ang, ln, wd in ((math.radians(55), R * 0.5, 0.18), (math.radians(-60), R * 0.8, 0.11)):
            K.boxm("clock_dark", Matrix.Translation((cx, f - 0.31, zc)) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Translation((0, 0, ln / 2 - 0.15)), wd, 0.04, ln)
        K.sphere("clock_dark", cx, f - 0.33, zc, 0.1, 1)
        # pediment-like hood over the clock
        K.prism_y("trim", f - 0.35, f + 0.1, [(cx - R - 0.5, zc + R + 0.35), (cx + R + 0.5, zc + R + 0.35), (cx, zc + R + 0.7)])
        K.box("glass", cx - 0.35, cx + 0.35, f - 0.04, f + 0.05, zb + 0.2, zb + 1.6)
        K.pop()
    K.cornice(cx - hw, cx + hw, y0, y0 + w, zt, 0.45, 0.55)
    zr = zt + 0.55
    for side in ((cx - hw, cx + hw, y0 + 0.1, "x"), (cx - hw, cx + hw, y0 + w - 0.1, "x"),
                 (y0, y0 + w, cx - hw + 0.1, "y"), (y0, y0 + w, cx + hw - 0.1, "y")):
        K.balustrade(side[0], side[1], side[2], zr, 0.95, axis=side[3], piers=False)
    for sx in (-1, 1):                                           # corner piers with urns
        for sy in (-1, 1):
            px, py = cx + sx * (hw - 0.1), cy + sy * (hw - 0.1)
            K.box("trim", px - 0.26, px + 0.26, py - 0.26, py + 0.26, zr, zr + 1.3)
            K.cyl("trim", px, py, zr + 1.3, zr + 1.5, 0.14, 0.2)
            K.sphere("trim", px, py, zr + 1.68, 0.2, 2, 1.2)
            K.sphere("trim", px, py, zr + 1.92, 0.07, 1)
    cw = w * 0.42                                                # cupola
    K.box("wall", cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zr, zr + 2.2)
    for rot in range(4):
        K.push(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rot * math.pi / 2, 4, "Z") @ Matrix.Translation((-cx, -cy, 0)))
        K.box("glass", cx - 0.45, cx + 0.45, cy - cw / 2 - 0.05, cy - cw / 2 + 0.05, zr + 0.4, zr + 1.6)
        K.arc_band("glass", cx, zr + 1.6, 0, 0.45, 0, math.pi, cy - cw / 2 - 0.05, cy - cw / 2 + 0.05, 6)
        K.pop()
    K.cornice(cx - cw / 2, cx + cw / 2, cy - cw / 2, cy + cw / 2, zr + 2.2, 0.3, 0.35)
    K.sphere("roof", cx, cy, zr + 2.55, cw / 2 + 0.05, 2, 0.7)
    K.cyl("trim", cx, cy, zr + 3.2, zr + 3.55, 0.18, 0.12)
    K.sphere("gilt", cx, cy, zr + 3.75, 0.24, 2)
    K.cyl("gilt", cx, cy, zr + 3.95, zr + 4.7, 0.045, 0.01, 6)


# ------------------------------------------------------------------ pavilion
def pavilion(seg):
    x0, x1, N, D = seg["x0"], seg["x1"], seg["storeys"], seg["depth"]
    S = seg.get("storey", LAYOUT["storey"])
    podium(x0, x1, D, doors=False)
    K.door((x0 + x1) / 2, 0, 0, 2.2, 2.6)
    wf = 1.8
    H = P + N * S
    nb = max(1, round((x1 - x0) / BAY))
    K.box("wall", x0, x1, wf, D, P, H)
    for k in range(N):
        z = P + k * S
        K.box("trim", x0, x1, -0.2, wf, z - 0.28, z)
        K.balustrade(x0, x1, 0.1, z)
        for i in range(nb):                                     # big glazed screens
            cx = x0 + (x1 - x0) * (i + 0.5) / nb
            K.window(cx, wf, z + 0.3, BAY - 0.7, S - 0.9)
            K.box("trim", cx - (BAY - 0.7) / 2, cx + (BAY - 0.7) / 2, wf - 0.09, wf, z + S * 0.45, z + S * 0.45 + 0.07)
            K.window(cx, D, z + 0.7, 1.4, 1.9, d=1)
        stand_area(x0 + 0.4, x1 - 0.4, 0.45, wf - 0.2, z, "balcony")
    for x, d in ((x1, 1), (x0, -1)):                            # end windows
        for k in range(N):
            for j in (-1, 0, 1):
                yc = D / 2 + j * 4.5
                K.box("glass", x - 0.03 if d > 0 else x - 0.06, x + 0.06 if d > 0 else x + 0.03, yc - 0.8, yc + 0.8, P + k * S + 0.6, P + k * S + S - 0.8)
                K.box("trim", x - 0.02 if d > 0 else x - 0.18, x + 0.18 if d > 0 else x + 0.02, yc - 0.95, yc + 0.95, P + k * S + 0.45, P + k * S + 0.6)
    K.box("trim", x0, x1, -0.2, wf, H - 0.28, H)
    rise = K.gable_roof(x0, x1, -0.2, D, H, seg["pitch_deg"])
    lx = x0 + (x1 - x0) * 0.62                                  # roof lantern
    zl = H + rise - 0.6
    K.box("wall", lx - 2.2, lx + 2.2, D / 2 - 1.5, D / 2 + 1.5, zl, zl + 1.8)
    for i in range(6):
        K.box("glass", lx - 2.0 + i * 0.7, lx - 1.6 + i * 0.7, D / 2 - 1.56, D / 2 - 1.48, zl + 0.3, zl + 1.5)
    K.cornice(lx - 2.2, lx + 2.2, D / 2 - 1.5, D / 2 + 1.5, zl + 1.8, 0.25, 0.3)
    K.hip_roof(lx - 2.2, lx + 2.2, D / 2 - 1.5, D / 2 + 1.5, zl + 2.1, 0.6, 0.2)


# ------------------------------------------------------------------ steps
def steps(st):
    cx, w, run = st["x"], st["width"], st["run"]
    n = int(round(P / 0.17))
    tread, rh = run / n, P / n
    for i in range(n):
        K.box("steps", cx - w / 2, cx + w / 2, -run + i * tread, 0, i * rh, (i + 1) * rh)
    for sx in (-1, 1):
        x = cx + sx * (w / 2 + 0.2)
        K.prism_x("podium", x - 0.2, x + 0.2, [(-run - 0.4, 0), (0, 0), (0, P + 0.25), (-run - 0.4, 0.45)])
        # sloping handrail on balusters
        ang = math.atan2(P, run)
        Lr = math.hypot(run, P)
        K.boxm("trim", Matrix.Translation((x, -run / 2 - 0.2, P / 2 + 1.15)) @ Matrix.Rotation(-ang, 4, "X"), 0.26, Lr + 0.3, 0.12)
        for j in range(1, 11):
            t = j / 11
            K.box("trim", x - 0.05, x + 0.05, -run - 0.2 + t * run - 0.05, -run - 0.2 + t * run + 0.05, t * P + 0.4, t * P + 1.1)
        K.box("trim", x - 0.25, x + 0.25, -run - 0.65, -run - 0.15, 0, 1.25)          # newel
        K.sphere("trim", x, -run - 0.4, 1.45, 0.22, 1)
    # landing gap in the balustrade above is left to the terrace: crowds walk up here
    stand_area(cx - w / 2 + 0.3, cx + w / 2 - 0.3, -run + 0.3, -0.3, 0, "steps")


BUILD = {"veranda": veranda, "block": block, "iron": ironwork, "tower": tower, "pavilion": pavilion}
for seg in LAYOUT["segments"]:
    BUILD[seg["kind"]](seg)
for st in LAYOUT["steps"]:
    steps(st)
stand_area(0.3, L - 0.3, -0.0, 0.0, 0, "lawn_front_line")     # front line of the stand at ground level
K.pop()

# ------------------------------------------------------------------ assemble: one mesh per material
stand = bpy.data.collections.new("victorian_grandstand")
bpy.context.scene.collection.children.link(stand)
tris = 0
for name, bm in K.bms.items():
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("grandstand_" + name)
    bm.to_mesh(me); bm.free()
    me.materials.append(MATS[name])
    ob = bpy.data.objects.new("grandstand_" + name, me)
    stand.objects.link(ob)
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
print("grandstand: %d meshes, %d triangles, %.1f m long" % (len(K.bms), tris, L), flush=True)

# ------------------------------------------------------------------ crowd figures
crowd = bpy.data.collections.new("crowd_people")
bpy.context.scene.collection.children.link(crowd)
CM = {"clothes": material("crowd_clothes", "#3a3f4a", 0.9), "skin": material("crowd_skin", "#e2b896", 0.7),
      "hat": material("crowd_hat", "#1e1f24", 0.6)}


def person(name, kind):
    k = Kit()
    if kind in ("gent", "gent_tophat"):
        k.cyl("clothes", 0, 0, 0.0, 0.85, 0.13, 0.17, 7)            # legs
        k.cyl("clothes", 0, 0, 0.85, 1.48, 0.2, 0.24, 7)            # coat
        k.sphere("clothes", 0, 0, 1.46, 0.23, 1, 0.45)              # shoulders
    else:
        k.cyl("clothes", 0, 0, 0.0, 1.1, 0.33, 0.17, 8)             # dress
        k.cyl("clothes", 0, 0, 1.1, 1.42, 0.16, 0.2, 7)
        k.sphere("clothes", 0, 0, 1.41, 0.2, 1, 0.45)
    k.cyl("skin", 0, 0, 1.45, 1.56, 0.06, 0.06, 6)
    k.sphere("skin", 0, 0, 1.64, 0.115, 1, 1.1)
    if kind == "gent_tophat":
        k.cyl("hat", 0, 0, 1.72, 1.74, 0.17, 0.17, 10)
        k.cyl("hat", 0, 0, 1.74, 1.93, 0.105, 0.11, 10)
    elif kind == "gent":
        k.cyl("hat", 0, 0, 1.71, 1.73, 0.16, 0.16, 10)
        k.cyl("hat", 0, 0, 1.73, 1.8, 0.11, 0.1, 10)
    else:
        k.cyl("hat", 0, 0, 1.69, 1.71, 0.27, 0.27, 12)
        k.sphere("hat", 0, 0, 1.72, 0.12, 1, 0.7)
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for mname, b in k.bms.items():
        idx = list(CM).index(mname)
        tmp = bpy.data.meshes.new("tmp"); b.to_mesh(tmp); b.free()
        bm.from_mesh(tmp)
        for f in bm.faces:
            if f.material_index == 0 and not f.tag:
                f.material_index = idx; f.tag = True
        bpy.data.meshes.remove(tmp)
    bm.to_mesh(me); bm.free()
    for m in CM.values():
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    crowd.objects.link(ob)
    return ob


for i, kind in enumerate(("gent_tophat", "gent", "lady", "lady_b")):
    o = person("person_" + kind, kind if kind != "lady_b" else "lady")
    o.location.x = i * 1.0

# ------------------------------------------------------------------ save
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(REPO, "assets/models/master"), exist_ok=True)
json.dump({"_about": "Where spectators can stand on the Victorian grandstand. Blender coordinates, metres, local to the stand: x along the front, y into the stand (front faces -y), z = floor height. In the .glb (y up) that is x = x, y = z, z = -y.",
           "areas": CROWD}, open(os.path.join(OUT_DIR, "victorian_grandstand_crowd_areas.json"), "w"), indent=1)


def export(coll, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in coll.objects:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=False, export_animations=False)
    print("exported", path, flush=True)


export(stand, os.path.join(OUT_DIR, "victorian_grandstand.glb"))
export(crowd, os.path.join(OUT_DIR, "crowd_people.glb"))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(REPO, "assets/models/master/victorian_grandstand.blend"), compress=True)
