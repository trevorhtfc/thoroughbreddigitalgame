"""Shared grandstand pieces (veranda tiers, windowed blocks, ironwork, clock tower, pavilion, steps).

Loaded with exec() after tools/blender/kit.py by build_grandstand.py and build_stand_modules.py.
The host script defines: K (a Kit), P (podium height), S (storey), BAY, and stand_area(x0, x1, y0, y1, z, kind).
Blender coordinates: x along the front (left to right as seen from the track), y into the building
(front faces -y), z up.
"""


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
    if seg["roof"] == "none":
        pass                                          # the caller adds its own roof
    elif seg["roof"] == "flat":
        K.box("trim", x0, x1, yt - 0.4, D, zt - 0.6, zt - 0.3)
        K.cornice(x0, x1, yt - 0.1, D, zt - 0.3, 0.2, 0.3)
        K.balustrade(x0, x1, yt + 0.2, zt, 0.9)
    else:
        rf = seg.get("raised_from")
        if rf is not None:
            if rf > x0 + 0.1:
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
    party = seg.get("party", ())          # ends that butt against a neighbour: no end windows there
    for x in (x0, x1):
        K.balustrade(0.15, D - 0.15, x, H + 0.6, axis="y", piers=False)
        if ("left" if x == x0 else "right") in party:
            continue
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
    St = seg.get("storey", S)
    podium(x0, x1, D, doors=False)
    K.door((x0 + x1) / 2, 0, 0, 2.2, 2.6)
    wf = 1.8
    H = P + N * St
    nb = max(1, round((x1 - x0) / BAY))
    K.box("wall", x0, x1, wf, D, P, H)
    for k in range(N):
        z = P + k * St
        K.box("trim", x0, x1, -0.2, wf, z - 0.28, z)
        K.balustrade(x0, x1, 0.1, z)
        for i in range(nb):                                     # big glazed screens
            cx = x0 + (x1 - x0) * (i + 0.5) / nb
            K.window(cx, wf, z + 0.3, BAY - 0.7, St - 0.9)
            K.box("trim", cx - (BAY - 0.7) / 2, cx + (BAY - 0.7) / 2, wf - 0.09, wf, z + St * 0.45, z + St * 0.45 + 0.07)
            K.window(cx, D, z + 0.7, 1.4, 1.9, d=1)
        stand_area(x0 + 0.4, x1 - 0.4, 0.45, wf - 0.2, z, "balcony")
    party = seg.get("party", ())                                # ends that butt against a neighbour
    for x, d in ((x1, 1), (x0, -1)):                            # end windows
        if ("right" if d > 0 else "left") in party:
            continue
        for k in range(N):
            for j in (-1, 0, 1):
                yc = D / 2 + j * 4.5
                K.box("glass", x - 0.03 if d > 0 else x - 0.06, x + 0.06 if d > 0 else x + 0.03, yc - 0.8, yc + 0.8, P + k * St + 0.6, P + k * St + St - 0.8)
                K.box("trim", x - 0.02 if d > 0 else x - 0.18, x + 0.18 if d > 0 else x + 0.02, yc - 0.95, yc + 0.95, P + k * St + 0.45, P + k * St + 0.6)
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



# ------------------------------------------------------------------ terrace stand (owner's archive photos, 6 Nov 2026)
def terrace(seg):
    """Ascot's old terraced stand, from the owner's photos: a row of glazed private boxes over the lawn, a standing
    terrace behind a plain parapet, an open gallery on slender columns under a deep plain frieze, and on the flat
    roof a terrace of standing rows stepping up towards the back, packed with people. Long, low and continuous:
    runs of it read as one stand, not a string of buildings."""
    x0, x1, D = seg["x0"], seg["x1"], seg.get("depth", 18.0)
    party = seg.get("party", ())
    podium(x0, x1, D)
    nb = max(1, round((x1 - x0) / BAY))
    # -- the boxes: glazed fronts between plain piers, a ledge and a light dark rail in front
    zb, hb = P, 2.9
    K.box("trim", x0, x1, -0.45, 0.7, zb - 0.28, zb)                                # ledge
    K.box("wall", x0, x1, 0.7, 4.0, zb, zb + hb)
    for i in range(nb):
        cx = x0 + (x1 - x0) * (i + 0.5) / nb
        K.box("glass", cx - BAY / 2 + 0.3, cx + BAY / 2 - 0.3, 0.62, 0.72, zb + 0.35, zb + hb - 0.35)
        if not K.far:
            K.box("trim", cx - 0.04, cx + 0.04, 0.55, 0.66, zb + 0.35, zb + hb - 0.35)
            K.box("trim", cx - BAY / 2 + 0.3, cx + BAY / 2 - 0.3, 0.55, 0.66, zb + 1.6, zb + 1.67)
    for i in range(nb + 1):
        px = x0 + (x1 - x0) * i / nb
        K.box("trim", px - 0.2, px + 0.2, 0.45, 0.75, zb, zb + hb)
    K.box("iron", x0, x1, -0.38, -0.26, zb + 0.95, zb + 1.03)                       # rail
    K.box("iron", x0, x1, -0.36, -0.28, zb + 0.1, zb + 0.16)
    if not K.far:
        n = int((x1 - x0) / 0.32)
        for i in range(n):
            bx = x0 + (i + 0.5) * (x1 - x0) / n
            K.box("iron", bx - 0.018, bx + 0.018, -0.34, -0.3, zb + 0.16, zb + 0.95)
    stand_area(x0 + 0.4, x1 - 0.4, -0.2, 0.4, zb, "balcony")
    # -- the standing terrace: floor, plain parapet, three rows stepping back
    z2 = zb + hb + 0.35
    K.box("trim", x0, x1, -0.5, 8.0, z2 - 0.35, z2)
    K.box("wall", x0, x1, -0.5, -0.2, z2, z2 + 1.0)                                  # parapet
    K.box("trim", x0, x1, -0.6, -0.1, z2 + 1.0, z2 + 1.12)
    rows2 = [(0.0, 1.2, 0.0), (1.2, 2.4, 0.34), (2.4, 3.6, 0.68)]
    for ya, yb, rz in rows2:
        if rz > 0:
            K.box("steps", x0, x1, ya, yb, z2, z2 + rz)
        stand_area(x0 + 0.3, x1 - 0.3, ya + 0.15, yb - 0.15, round(z2 + rz, 2), "terrace")
    # -- the gallery: slender columns, glazed screens at the back, the deep plain frieze above
    zr = z2 + 4.3
    K.box("steps", x0, x1, 3.6, 8.0, z2, z2 + 0.68)
    K.box("wall", x0, x1, 8.0, D, z2, zr)
    for i in range(nb):
        cx = x0 + (x1 - x0) * (i + 0.5) / nb
        K.screen(cx - BAY / 2, cx + BAY / 2, 8.0, z2 + 0.68, zr - z2 - 1.2)
        K.window(cx, D, z2 + 1.0, 1.4, 1.6, d=1)
        K.window(cx, D, zb + 0.6, 1.2, 1.5, d=1)
    for i in range(nb + 1):
        K.cyl("trim", x0 + (x1 - x0) * i / nb, 3.75, z2 + 0.68, zr - 0.6, 0.13, 0.11, 10)
    K.box("wall", x0, x1, 3.35, 4.15, zr - 0.6, zr + 1.0)                            # frieze (the photos' plain band)
    K.box("trim", x0, x1, 3.25, 4.25, zr - 0.7, zr - 0.6)
    K.box("trim", x0, x1, 3.2, D, zr + 0.6, zr + 1.0)                                # roof deck
    K.box("trim", x0, x1, 3.15, 3.5, zr + 1.0, zr + 1.95)                            # low front parapet
    stand_area(x0 + 0.4, x1 - 0.4, 4.4, 7.6, round(z2 + 0.68, 2), "gallery")
    # -- the roof terrace: standing rows stepping up to the back
    zt0, y, k = zr + 1.0, 3.6, 0
    while y + 1.1 <= D - 0.4:
        h = k * 0.34
        if h > 0:
            K.box("steps", x0, x1, y, y + 1.1, zt0, zt0 + h)
        stand_area(x0 + 0.3, x1 - 0.3, y + 0.12, y + 0.98, round(zt0 + h, 2), "terrace")
        y += 1.1; k += 1
    ztop = zt0 + (k - 1) * 0.34
    K.box("wall", x0, x1, D - 0.4, D, 0, ztop + 1.1)                                 # back wall
    K.box("trim", x0, x1, D - 0.5, D + 0.1, ztop + 1.1, ztop + 1.25)
    for x in (x0, x1):                                                               # finished ends: cheek walls
        if ("left" if x == x0 else "right") in party:
            continue
        t = -0.3 if x == x0 else 0.3
        K.prism_x("wall", min(x, x + t), max(x, x + t), [(3.15, zr + 0.6), (3.15, zr + 1.95), (D - 0.4, ztop + 1.25), (D, ztop + 1.25), (D, zr + 0.6)])
        K.box("wall", min(x, x + t), max(x, x + t), -0.5, 8.0, z2, z2 + 1.0)


# ------------------------------------------------------------------ belfry clock tower (owner's archive photo)
def tower_belfry(seg):
    """The old Ascot clock tower: a tall plain square shaft, the clock high up on every face, a belfry stage of
    round-arched openings above it, a bold cornice, a flat top and a cross."""
    cx, y0, w, zb, zt = seg["x"], seg["y"], seg["width"], seg["base_z"], seg["top_z"]
    hw, cy = w / 2, y0 + w / 2
    zbel = zt - 4.6                                            # belfry stage
    K.box("wall", cx - hw, cx + hw, y0, y0 + w, zb, zbel)
    K.box("trim", cx - hw - 0.12, cx + hw + 0.12, y0 - 0.12, y0 + w + 0.12, zbel - 0.35, zbel)   # string course
    K.box("wall", cx - hw + 0.25, cx + hw - 0.25, y0 + 0.25, y0 + w - 0.25, zbel, zt)
    zc = zbel - 3.2
    R = hw - 1.15
    for rot in range(4):
        K.push(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(rot * math.pi / 2, 4, "Z") @ Matrix.Translation((-cx, -cy, 0)))
        f = y0
        K.disc_y("trim", cx, f - 0.12, f + 0.1, zc, R + 0.22, 32)
        K.disc_y("clock_dark", cx, f - 0.2, f - 0.1, zc, R + 0.06, 32)
        K.disc_y("clock_face", cx, f - 0.26, f - 0.18, zc, R - 0.1, 32)
        for h in range(12):
            a = h * math.pi / 6
            K.boxm("clock_dark", Matrix.Translation((cx + math.sin(a) * (R - 0.38), f - 0.28, zc + math.cos(a) * (R - 0.38))) @ Matrix.Rotation(-a, 4, "Y"),
                   0.1 if h % 3 else 0.17, 0.04, 0.42 if h % 3 else 0.55)
        for ang, ln, wd in ((math.radians(55), R * 0.5, 0.18), (math.radians(-60), R * 0.8, 0.11)):
            K.boxm("clock_dark", Matrix.Translation((cx, f - 0.31, zc)) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Translation((0, 0, ln / 2 - 0.15)), wd, 0.04, ln)
        K.sphere("clock_dark", cx, f - 0.33, zc, 0.1, 1)
        # the belfry arcade: five round-arched openings between piers
        fb = f + 0.25
        n, aw = 5, (w - 0.5 - 6 * 0.35) / 5
        for i in range(n):
            ax = cx - hw + 0.25 + 0.35 + i * (aw + 0.35) + aw / 2
            K.box("glass", ax - aw / 2, ax + aw / 2, fb - 0.04, fb + 0.06, zbel + 0.5, zbel + 2.4)
            K.arc_band("glass", ax, zbel + 2.4, 0.0, aw / 2, 0, math.pi, fb - 0.04, fb + 0.06, 8)
            K.arc_band("trim", ax, zbel + 2.4, aw / 2, aw / 2 + 0.14, 0, math.pi, fb - 0.12, fb, 8)
        K.box("trim", cx - hw + 0.25, cx + hw - 0.25, fb - 0.14, fb, zbel + 0.35, zbel + 0.5)     # sill
        K.pop()
    K.cornice(cx - hw + 0.25, cx + hw - 0.25, y0 + 0.25, y0 + w - 0.25, zt, 0.55, 0.5)
    K.box("trim", cx - hw + 0.1, cx + hw - 0.1, y0 + 0.1, y0 + w - 0.1, zt + 0.5, zt + 0.75)
    K.cyl("trim", cx, cy, zt + 0.75, zt + 1.1, 0.35, 0.25, 8)
    K.cyl("gilt", cx, cy, zt + 1.1, zt + 4.0, 0.06, 0.05, 6)                           # the cross
    K.box("gilt", cx - 0.6, cx + 0.6, cy - 0.05, cy + 0.05, zt + 3.1, zt + 3.22)
    K.sphere("gilt", cx, cy, zt + 4.05, 0.12, 1)
