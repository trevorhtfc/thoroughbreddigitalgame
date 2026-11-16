"""The Park's stand kit: modules for the kit-made galloping course (the first of the three generic courses).

    python3.11 -c "exec(open('tools/blender/build_park_stands.py').read())"
    SHEET=1 python3.11 -c "exec(...)"       # also render the catalogue: reference/park/renders/kit-sheet-1.jpg to -4.jpg
    ARRANGE=1 python3.11 -c "exec(...)"     # also render the stand side assembled, the festival side opposite

Owner, 16 Nov 2026 (with photos of stands from the Park's courses): "could you look to create a series of stands to go
down the stand side of the generic park racecourse that uses some of the features. i think linking 2 or 3 architectural
forms is correct. the course should also use a similar festival zone to york with a festival zone and clock tower
building. lets start with creating some kit of parts grandstand components."

What each piece takes from his photos:
  park_arch_stand     the row of barrel-vaulted roofs over a white frame and the red band along the concourse (photo 1);
                      a taller middle bay with a clock; flags along the front of the roof (the flagpoles of photo 3).
                      roof="gable" swaps the vaults for photo 3's row of gables.
  park_victorian      brick, two tiers of iron-lace veranda, corner towers with steep slate roofs (photo 2), a gabled
                      name dormer, a clock cupola and chimneys (photo 4's middle building)
  park_glass_box      a modern glazed hospitality stand: glass-railed balconies, a thin flat roof plate reaching out over
                      them, a brick podium and a front of steps (photos 4 and 5); stair="left"/"right": the brick stair
                      tower with its diagonal glazing (photo 4)
  park_stair_tower    that brick stair tower alone, as a link between buildings
  park_terrace        open concrete standing steps with crush barriers (photo 6); stretched to fit
  park_clock_house    the festival side's building (photo 6, the Ripon clock tower): a brick block with cream bands, a
                      shaped gable carrying the clock, the big screen and a green results board on its front
  park_shed           the low brick shed with its tiled roof (photo 6)
  park_floodlight     a floodlight mast (photo 5), for the all-weather courses' evening racing

Every piece is built on one front line and to one shoulder height (the standing steps of York's stands, GS), so any of
them can be chained along a straight as York's were. The kit's own code reuses York's build (which brings the Rowley Mile
and Ascot pieces): its standing steps and shoulder link.

Writes assets/models/architecture/park_stands.glb and .json (as york_stands.json: size and crowd areas per piece;
origin the middle of the front on the ground, front facing -y in Blender, +z in glTF).
"""
import json, math, os

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

# ---- York's build's definitions (which exec the Rowley Mile's and the July Course's), without its build loop
_ysrc = open(rp("tools/blender/build_york_stands.py")).read()
exec(_ysrc[:_ysrc.index("\nPIECES = [")])

PARK = {"redband": "#d9928a", "flat_roof": "#d3d5da", "roof_edge": "#6f7584", "board": "#4f7563", "board_line": "#f3efe4",
        "brick_red": "#cf8a74", "quoin": "#efe1c8", "vault": "#f7f3ec", "vault_under": "#e3dfd8",
        "flag_a": "#e7a3a0", "flag_b": "#9fbad8", "flag_c": "#f1d38f", "flag_d": "#a9cfa6", "lamp": "#fff6dc"}
for k, v in PARK.items():
    COL[k] = v
    MATS[k] = material("pk_" + k, v, rough=0.9)
FLAGS = ["flag_a", "flag_b", "flag_c", "flag_d"]
YS, ZD = GS["yS"], GS["zd"]                      # the shoulder: steps' back and the seating deck's front edge (York's)


def barrier_rows(x0, x1, every=2):
    """Crush barriers along standing steps (GS): a rail on posts every 3 m, on every 'every'-th row."""
    if K.far:
        return
    R, tr, rs = GS["R"], GS["tr"], GS["rs"]
    for i in range(1, R, every):
        y, z = i * tr + 0.15, 0.2 + i * rs
        K.box("iron", x0 + 0.4, x1 - 0.4, y - 0.05, y + 0.05, z + 0.95, z + 1.05)
        n = max(1, int((x1 - x0 - 0.8) / 3.0))
        for j in range(n + 1):
            x = x0 + 0.4 + (x1 - x0 - 0.8) * j / n
            K.box("iron", x - 0.05, x + 0.05, y - 0.05, y + 0.05, z, z + 1.05)


def flag(x, y, z, mat, h=5.0):
    K.cyl("mast", x, y, z, z + h, 0.06, 0.05, 6)
    K.sphere("gilt", x, y, z + h + 0.1, 0.12, 1)
    K.box(mat, x + 0.06, x + 1.9, y - 0.03, y + 0.03, z + h - 1.2, z + h - 0.05)


def clock_face(x, y, z, R):
    """A clock on a wall face at y (looking -y)."""
    K.disc_y("trim", x, y - 0.12, y + 0.05, z, R + 0.22, 32)
    K.disc_y("clock_dark", x, y - 0.18, y - 0.1, z, R + 0.06, 32)
    K.disc_y("clock_face", x, y - 0.24, y - 0.16, z, R - 0.08, 32)
    for h in range(12):
        a = h * math.pi / 6
        K.boxm("clock_dark", Matrix.Translation((x + math.sin(a) * (R - 0.3), y - 0.26, z + math.cos(a) * (R - 0.3))) @ Matrix.Rotation(-a, 4, "Y"),
               0.07 if h % 3 else 0.12, 0.03, 0.28 if h % 3 else 0.38)
    for ang, ln, wd in ((math.radians(55), R * 0.5, 0.13), (math.radians(-60), R * 0.8, 0.08)):
        K.boxm("clock_dark", Matrix.Translation((x, y - 0.29, z)) @ Matrix.Rotation(-ang, 4, "Y") @ Matrix.Translation((0, 0, ln / 2 - 0.1)), wd, 0.03, ln)


# ------------------------------------------------------------------------------------------ 1: the arch-roofed grandstand
def arch_stand(nb=9, bay=8.0, roof="arch", flags=True, centre=True):
    """The main public grandstand (photo 1; photo 3's flags). From the lawn back: York's standing steps with crush
    barriers; the concourse under the seating, glazed, with the red band along its front; a raked seating deck; slim
    white columns on every bay line; and the roof: a row of barrel vaults, each running front to back, so the front
    reads as a row of arches (roof="gable": a row of gables, photo 3). The middle bay rises a storey higher with a clock
    in its arch. Origin: the middle of the front on the ground."""
    L = nb * bay; h = L / 2
    standing_steps(-h, h)
    barrier_rows(-h, h)
    rows, tr, rs = 10, 0.85, 0.42
    yW = YS + rows * tr                                           # the back of the seating deck
    D = yW + 6.0                                                  # the rooms behind it
    zs = ZD + rows * rs + 2.6                                     # where the vaults spring
    K.box("wall", -h, h, YS + 1.2, D, -1.0, ZD)                   # the concourse
    K.screen(-h, h, YS + 1.15, 0.0, ZD - 1.3)
    K.box("redband", -h, h, YS - 0.15, YS + 1.2, ZD - 1.25, ZD - 0.3)
    K.box("trim", -h, h, YS - 0.2, YS + 1.2, ZD - 0.3, ZD)
    prof = [(YS, ZD - 0.5)]                                       # the seating deck
    for i in range(rows):
        y1 = YS + (i + 1) * tr
        prof += [(YS + i * tr, ZD + i * rs), (y1, ZD + i * rs)]
        K.box("seat", -h + 0.5, h - 0.5, y1 - 0.4, y1 - 0.1, ZD + i * rs, ZD + i * rs + 0.4)
        rarea(-h + 0.5, h - 0.5, YS + i * tr + 0.05, y1 - 0.45, ZD + i * rs)
    prof += [(yW, ZD - 0.5)]
    K.prism_x("concrete", -h, h, prof)
    K.box("glass", -h + 0.2, h - 0.2, YS - 0.02, YS + 0.06, ZD, ZD + 1.0)            # a glass rail at the deck's front
    K.box("trim", -h, h, YS - 0.06, YS + 0.12, ZD + 1.0, ZD + 1.1)
    K.box("wall", -h, h, yW, D, ZD - 0.5, zs)                     # the back rooms, up to the spring line
    for i in range(nb):
        K.window(-h + bay * (i + 0.5), D, ZD + 1.2, 2.2, 1.6, d=1)
    yF = YS + 0.5                                                 # the frame: columns on each bay line
    for i in range(nb + 1):
        x = -h + bay * i
        K.box("trim", x - 0.22, x + 0.22, yF - 0.22, yF + 0.22, ZD, zs)
        K.box("trim", x - 0.25, x + 0.25, yF, D, zs - 0.4, zs)                        # the valley beam front to back
    K.box("trim", -h, h, yF - 0.3, yF + 0.3, zs - 0.6, zs)                            # the front beam
    for side in (-1, 1):                                          # the end walls
        x = side * h
        K.box("vault", min(x, x + side * 0.3), max(x, x + side * 0.3), YS - 0.2, D, ZD - 0.3, zs)
        for y in (YS + 3.5, YS + 8.0, YS + 12.5):
            side_window(x + side * 0.3, side, y, ZD + 2.0, 1.4, 2.2)
    yR0, yR1 = yF - 1.4, D + 0.6                                  # the roof reaches out over the front of the deck
    top_z = zs
    for i in range(nb):
        cx = -h + bay * (i + 0.5)
        lift = 3.2 if (centre and nb % 2 and i == nb // 2) else 0.0
        z0 = zs + lift
        if lift:                                                  # the raised middle bay: walls up to its spring line
            for x in (cx - bay / 2, cx + bay / 2):
                K.box("vault", x - 0.25, x + 0.25, yF - 0.2, D, zs - 0.4, z0)
            K.box("trim", cx - bay / 2, cx + bay / 2, yF - 0.3, yF + 0.3, z0 - 0.6, z0)
            K.screen(cx - bay / 2 + 0.25, cx + bay / 2 - 0.25, yF + 0.2, zs, lift - 0.6)
        a = bay / 2
        if roof == "gable":
            rise = a * 0.9
            prof = [(cx - a - 0.15, z0 - 0.05), (cx, z0 + rise), (cx + a + 0.15, z0 - 0.05), (cx + a + 0.15, z0 + 0.25), (cx, z0 + rise + 0.32), (cx - a - 0.15, z0 + 0.25)]
            K.prism_y("slate", yR0, yR1, prof)
            K.prism_y("vault", yR0 + 0.2, yR0 + 0.45, [(cx - a, z0), (cx + a, z0), (cx, z0 + rise - 0.1)])   # the gable end
            K.prism_y("trim", yR0 - 0.05, yR0 + 0.2, [(cx - a - 0.2, z0 - 0.1), (cx, z0 + rise + 0.25), (cx + a + 0.2, z0 - 0.1), (cx + a + 0.2, z0 + 0.25), (cx, z0 + rise + 0.6), (cx - a - 0.2, z0 + 0.25)])
            crown = z0 + rise + 0.6
            if lift:
                clock_face(cx, yR0 - 0.06, z0 + rise * 0.42, 1.0)
        else:
            rise = bay * 0.3
            Rr = (a * a + rise * rise) / (2 * rise)
            cz = z0 + rise - Rr
            fz = lambda x, y, cx=cx, Rr=Rr, cz=cz: cz + math.sqrt(max(0.0, Rr * Rr - (x - cx) ** 2))
            sheet_solid("vault", fz, cx - a, cx + a, yR0, yR1, 10 if not K.far else 5, 2, 0.28)
            th0 = math.acos(min(1.0, a / Rr))
            for y0 in (yR0 - 0.3, yR1 - 0.05):                    # the arch's rim at the front and back
                K.arc_band("trim", cx, cz, Rr - 0.02, Rr + 0.3, th0, math.pi - th0, y0, y0 + 0.35, 12)
            if lift:                                              # the clock in the raised arch's front
                K.arc_band("vault_under", cx, cz, 0.0, Rr - 0.05, th0, math.pi - th0, yR0 + 0.3, yR0 + 0.4, 12)
                clock_face(cx, yR0 + 0.28, z0 + rise * 0.45, min(1.0, rise * 0.4))
            crown = z0 + rise + 0.3
        top_z = max(top_z, crown)
    if flags:                                                     # flags along the front of the roof, on the valleys
        for i in range(1, nb):
            x = -h + bay * i
            mid = centre and nb % 2 and i in (nb // 2, nb // 2 + 1)
            flag(x, yF - 0.6, zs + (3.2 if mid else 0.0), FLAGS[i % 4], 4.5)
    return {"width": round(L, 2), "depth": round(D + 0.6, 2), "height": round(top_z + (5.0 if flags else 0.0), 2)}


# ------------------------------------------------------------------------------------------ 2: the Victorian pavilion
def lace_bay(x0, x1, z, S, y=0.32, mat="ironwork"):
    """One bay of iron lace on a veranda (Ascot's ironwork, simpler): an arch under the frieze, a roundel in each
    spandrel, a railing with roundels."""
    w = x1 - x0; cx = (x0 + x1) / 2
    r = w / 2 - 0.12
    spring = z + S - 0.5 - r * 0.55
    K.arc_band(mat, cx, spring, r - 0.12, r, 0.1, math.pi - 0.1, y - 0.05, y + 0.05, 10)
    for s in (-1, 1):
        K.ring_y(mat, cx + s * (w / 2 - 0.4), y, z + S - 0.85, 0.24, 0.04)
    K.box(mat, x0, x1, y - 0.06, y + 0.06, z + S - 0.42, z + S - 0.32)                 # frieze rails
    K.box(mat, x0, x1, y - 0.06, y + 0.06, z + S - 0.12, z + S - 0.04)
    n = max(2, int(w / 0.5))
    for i in range(n):
        K.ring_y(mat, x0 + (i + 0.5) * w / n, y, z + S - 0.23, 0.08, 0.02, 8, 3)
    if z > 0.5:                                                   # the railing (not on the ground)
        K.box(mat, x0, x1, y - 0.07, y + 0.07, z + 0.95, z + 1.05)
        K.box(mat, x0, x1, y - 0.05, y + 0.05, z + 0.1, z + 0.18)
        K.ring_y(mat, cx, y, z + 0.56, 0.3, 0.045)
        for s in (-1, 1):
            K.ring_y(mat, cx + s * w * 0.3, y, z + 0.56, 0.22, 0.04)


def corner_tower(x0, x1, y0, y1, H, rise):
    """A square brick corner tower with cream quoins, a window a storey, a steep slate pyramid roof, iron cresting and
    a finial (photo 2)."""
    K.box("brick_red", x0, x1, y0, y1, -1.0, H)
    for x in (x0, x1):
        for y in (y0, y1):
            K.box("quoin", x - 0.25, x + 0.25, y - 0.25, y + 0.25, 0.0, H)
    for z in (4.0, 7.8):
        K.box("quoin", x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, z - 0.25, z)
        K.window((x0 + x1) / 2, y0, z + 0.6, 1.3, 2.3)
    K.window((x0 + x1) / 2, y0, 1.0, 1.3, 2.3)
    K.box("quoin", x0 - 0.35, x1 + 0.35, y0 - 0.35, y1 + 0.35, H, H + 0.45)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bm = K.bm("slate")
    v = lambda x, y, z: bm.verts.new(K.M @ Vector((x, y, z)))
    o = 0.4
    c = [v(x0 - o, y0 - o, H + 0.45), v(x1 + o, y0 - o, H + 0.45), v(x1 + o, y1 + o, H + 0.45), v(x0 - o, y1 + o, H + 0.45)]
    t = v(cx, cy, H + 0.45 + rise)
    for i in range(4):
        bm.faces.new((c[i], c[(i + 1) % 4], t))
    bm.faces.new(c[::-1])
    K.box("ironwork", cx - 0.6, cx + 0.6, cy - 0.06, cy + 0.06, H + rise - 1.0, H + rise + 0.3)
    K.cyl("ironwork", cx, cy, H + rise, H + rise + 2.2, 0.06, 0.03, 6)
    K.sphere("gilt", cx, cy, H + rise + 1.2, 0.18, 1)


def victorian(nb=9, bay=3.8, towers=True, cupola=True, chimneys=True):
    """The heritage centrepiece (photos 2 and 4): a brick building of three storeys behind two tiers of iron-lace
    veranda (the ground under it a colonnade); cream stone bands; a hipped slate roof with a gabled dormer carrying the
    course's name board, a clock cupola on the ridge and brick chimneys; and at each end a square corner tower with a
    steep slate pyramid roof. Origin: the middle of the front on the ground (the veranda's front)."""
    L = nb * bay; h = L / 2
    G, S1, S2 = 4.0, 3.8, 3.6
    H = G + S1 + S2
    vy, D = 3.4, 14.0
    K.box("brick_red", -h, h, vy, D, -1.0, H)
    for z in (G, G + S1):
        K.box("quoin", -h, h, vy - 0.12, D, z - 0.3, z)
    K.box("quoin", -h - 0.1, h + 0.1, vy - 0.25, D + 0.25, H - 0.1, H + 0.45)          # the cornice
    for i in range(nb):
        cx = -h + bay * (i + 0.5)
        K.door(cx, vy, 0.0, 1.6, 2.8)
        for z in (G, G + S1):
            K.window(cx, vy, z + 0.3, 1.6, 2.7)
        K.window(cx, D, 1.2, 1.2, 1.8, d=1)
        K.window(cx, D, G + 0.8, 1.2, 1.8, d=1)
    # the veranda: floors, posts through both tiers, lace, a lean-to roof over the top tier
    for z in (G, G + S1):
        K.box("trim", -h, h, -0.1, vy, z - 0.3, z)
    for i in range(nb + 1):
        x = -h + bay * i
        K.cyl("ironwork", x, 0.32, 0.0, H, 0.1, 0.1, 8)
        K.box("ironwork", x - 0.2, x + 0.2, 0.12, 0.52, 0.0, 0.35)
    for i in range(nb):
        x0, x1 = -h + bay * i, -h + bay * (i + 1)
        lace_bay(x0, x1, 0.0, G - 0.3)
        lace_bay(x0, x1, G, S1 - 0.3)
        lace_bay(x0, x1, G + S1, S2 - 0.3)
    K.prism_x("slate", -h - 0.2, h + 0.2, [(-0.6, H - 0.3), (vy, H + 0.9), (vy, H + 1.2), (-0.6, H)])
    K.box("trim", -h - 0.2, h + 0.2, -0.7, -0.5, H - 0.55, H)
    rarea(-h + 0.4, h - 0.4, 0.6, vy - 0.3, 0.0)
    rarea(-h + 0.4, h - 0.4, 0.6, vy - 0.3, G)
    rarea(-h + 0.4, h - 0.4, 0.6, vy - 0.3, G + S1)
    # the main roof, the name dormer, the clock cupola, chimneys
    zr = H + 0.45
    K.hip_roof(-h, h, vy, D, zr, 3.6, 0.5, mat="slate")
    dw = 7.0
    rz = gable_y(-dw / 2, dw / 2, vy - 0.4, vy + 3.0, zr - 0.6, 48, 0.4, roof="slate", wall="quoin")
    K.box("board", -2.7, 2.7, vy - 0.55, vy - 0.4, zr + 0.2, zr + 1.5)
    K.box("board_line", -2.5, 2.5, vy - 0.6, vy - 0.55, zr + 0.75, zr + 0.95)
    top = zr + 3.6
    if cupola:
        cy, cw = (vy + D) / 2, 2.8
        zc0 = top - 0.6
        K.box("quoin", -cw / 2, cw / 2, cy - cw / 2, cy + cw / 2, zc0, zc0 + 3.2)
        for f, d in ((cy - cw / 2, 1), (cy + cw / 2, -1)):
            K.push(Matrix.Translation((0, f, 0)) @ Matrix.Rotation(0 if d > 0 else math.pi, 4, "Z"))
            clock_face(0.0, 0.0, zc0 + 1.6, 1.0)
            K.pop()
        K.cornice(-cw / 2, cw / 2, cy - cw / 2, cy + cw / 2, zc0 + 3.2, 0.25, 0.3)
        K.sphere("slate", 0.0, cy, zc0 + 3.9, cw / 2 + 0.1, 2, 0.9)
        K.cyl("gilt", 0.0, cy, zc0 + 4.9, zc0 + 6.4, 0.06, 0.02, 6)
        K.sphere("gilt", 0.0, cy, zc0 + 5.3, 0.16, 1)
        top = zc0 + 6.4
    if chimneys:
        for x in (-h * 0.62, h * 0.62):
            for y in (vy + 2.0, D - 2.0):
                K.box("brick_red", x - 0.7, x + 0.7, y - 0.45, y + 0.45, zr + 1.0, zr + 5.0)
                K.box("quoin", x - 0.85, x + 0.85, y - 0.6, y + 0.6, zr + 5.0, zr + 5.3)
                for dx in (-0.35, 0.35):
                    K.cyl("pot", x + dx, y, zr + 5.3, zr + 6.0, 0.17, 0.14, 6)
    width = L
    if towers:
        T = 6.0
        corner_tower(-h - T, -h, 0.4, D - 1.0, H + 2.4, 6.0)
        corner_tower(h, h + T, 0.4, D - 1.0, H + 2.4, 6.0)
        width = L + 2 * T
        top = max(top, H + 2.4 + 6.0 + 2.2)
    return {"width": round(width, 2), "depth": D, "height": round(top, 2)}


# ------------------------------------------------------------------------------------------ 3: the glass box
def stair_tower(x0, x1, y0, y1, H, up=1):
    """The brick stair tower of photo 4: brick, a cream coping, and the stair's glazing climbing diagonally across its
    front face (up=1: rising to the right)."""
    K.box("brick", x0, x1, y0, y1, -1.0, H)
    K.box("quoin", x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, H, H + 0.35)
    w, run = x1 - x0, 3.2
    n = int((H - 2.0) / run)
    for k in range(n):
        za = 1.0 + k * run
        a, b = (x0 + 0.5, x1 - 0.5) if (k % 2 == 0) == (up > 0) else (x1 - 0.5, x0 + 0.5)
        K.prism_y("glass", y0 - 0.05, y0 + 0.05, [(a, za), (b, za + run - 0.6), (b, za + run + 0.9), (a, za + 1.5)][::1 if b > a else -1])
    K.box("glass", (x0 + x1) / 2 - 0.8, (x0 + x1) / 2 + 0.8, y0 - 0.05, y0 + 0.05, 0.0, 2.6)


def glass_box(L=30.0, storeys=3, stair="right"):
    """A modern hospitality stand (photos 4 and 5): a short front of seating steps; a brick podium with a glazed
    shopfront; storeys of full glazing behind deep balconies with glass rails; and a thin flat roof plate reaching
    out over the top balcony and past the ends. stair: a brick stair tower on that end (photo 4). Origin: the middle
    of the front on the ground."""
    h = L / 2
    T = 5.0 if stair else 0.0
    xa, xb = (-h, h - T) if stair == "right" else (-h + T, h) if stair == "left" else (-h, h)
    P0, St, yb, D = 4.4, 3.7, YS - 3.0, YS + 13.0
    steps("steps", xa, xb, 0.0, 0.2, 6, 1.0, 0.36, seat="seat")
    K.box("brick", xa, xb, 6.0, D, -1.0, P0)                                          # the podium
    K.screen(xa, xb, 6.0 - 0.05, 0.0, P0 - 1.0)
    K.box("trim", xa, xb, yb - 0.2, D, P0 - 0.35, P0)
    top = P0 + storeys * St
    yg = yb + 3.2                                                 # the glazing behind the balconies
    K.box("wall", xa, xb, yg, D, P0, top)
    for k in range(storeys):
        z = P0 + k * St
        K.box("trim", xa, xb, yb - 0.1, yg, z - 0.3, z)
        K.box("glass", xa + 0.15, xb - 0.15, yb - 0.02, yb + 0.06, z, z + 1.1)
        K.box("roof_edge", xa, xb, yb - 0.06, yb + 0.1, z + 1.1, z + 1.16)
        K.screen(xa, xb, yg - 0.05, z, St - 0.4, pane=1.5)
        rarea(xa + 0.4, xb - 0.4, yb + 0.4, yg - 0.3, z)
    for x in (xa, xb):                                            # dark fins at the ends of the balconies
        K.box("roof_edge", x - 0.2, x + 0.2, yb - 0.2, yg, P0 - 0.35, top)
    K.box("flat_roof", xa - 1.5, xb + 1.5, yb - 3.5, D + 0.4, top + 0.6, top + 0.95)  # the roof plate
    K.box("roof_edge", xa - 1.55, xb + 1.55, yb - 3.6, yb - 3.4, top + 0.45, top + 1.0)
    for x in (xa, xb):
        K.box("roof_edge", x - 0.15, x + 0.15, yb - 0.25, yb - 0.05, top, top + 0.6)
    K.box("wall", xa, xb, yg, D, top, top + 0.6)
    if stair:
        sx0, sx1 = (xb, h) if stair == "right" else (-h, xa)
        stair_tower(sx0, sx1, yb, D - 1.0, top + 1.6, up=1 if stair == "right" else -1)
    return {"width": L, "depth": round(D + 0.4, 2), "height": round(top + 1.6, 2)}


def stair_link(L=6.0, H=17.0):
    """The stair tower alone, as a link between two buildings, set back from the front, steps along its foot."""
    h = L / 2
    standing_steps(-h, h)
    stair_tower(-h, h, YS + 1.0, YS + 13.0, H)
    return {"width": L, "depth": YS + 13.0, "height": H + 0.35}


# ------------------------------------------------------------------------------------------ 4: open terrace
def open_terrace(L=20.0):
    """Open concrete standing steps with crush barriers (photo 6), a low wall at the back. Stretched to each gap.
    Origin: the middle of the front on the ground."""
    h = L / 2
    standing_steps(-h, h)
    barrier_rows(-h, h)
    zt = 0.2 + (GS["R"] - 1) * GS["rs"]
    K.box("wall", -h, h, YS, YS + 0.5, -1.0, zt + 1.2)
    K.box("trim", -h, h, YS - 0.05, YS + 0.55, zt + 1.2, zt + 1.35)
    return {"width": L, "depth": YS + 0.5, "height": round(zt + 1.35, 2)}


# ------------------------------------------------------------------------------------------ 5: the festival side
def clock_house():
    """The festival side's clock tower building (photo 6, Ripon): a tall brick block with cream bands, a shaped gable
    rising in the middle of its front carrying the clock, the big screen on its front and a green results board beside
    it, a hipped roof behind the gable. Steps in front for the crowd. Origin: the middle of the front on the ground."""
    W, D, H = 12.4, 10.0, 13.4
    h = W / 2
    y0 = 5.0
    steps("steps", -h - 6.0, h + 6.0, 0.0, 0.15, 5, 1.0, 0.32)
    K.box("brick_red", -h, h, y0, y0 + D, -1.0, H)
    for z in (2.6, 9.6, 12.4):
        K.box("quoin", -h - 0.1, h + 0.1, y0 - 0.12, y0 + D + 0.1, z - 0.4, z)
    K.box("quoin", -h - 0.15, h + 0.15, y0 - 0.2, y0 + D + 0.15, H - 0.1, H + 0.3)
    for x in (-h + 0.3, h - 0.3):                                 # cream pilasters
        K.box("quoin", x - 0.3, x + 0.3, y0 - 0.15, y0 + 0.1, 2.6, H)
    gz = H + 0.3
    gable = [(-4.6, gz), (4.6, gz), (4.6, gz + 0.9), (3.4, gz + 0.9), (3.0, gz + 2.4), (2.0, gz + 3.4), (1.6, gz + 3.4),
             (1.6, gz + 4.0), (-1.6, gz + 4.0), (-1.6, gz + 3.4), (-2.0, gz + 3.4), (-3.0, gz + 2.4), (-3.4, gz + 0.9), (-4.6, gz + 0.9)]
    K.prism_y("brick_red", y0 - 0.1, y0 + 0.6, gable[::-1])
    cap = [(x + (0.15 if x > 0 else -0.15), z + 0.25) for x, z in gable[2:-2]]
    for (xa_, za_), (xb_, zb_) in zip(cap[:-1], cap[1:]):
        strut("quoin", (xa_, y0 + 0.25, za_), (xb_, y0 + 0.25, zb_), r=0.2, segs=4)
    clock_face(0.0, y0 - 0.1, gz + 2.1, 1.0)
    K.hip_roof(-h, h, y0 + 0.6, y0 + D, H + 0.3, 2.6, 0.3, mat="slate")
    # the big screen and the results board
    K.box("board", -1.4, 5.4, y0 - 0.35, y0 - 0.02, 3.0, 8.8)
    K.box("screen", -1.1, 5.1, y0 - 0.42, y0 - 0.3, 3.3, 8.4)
    K.box("board", -5.4, -2.0, y0 - 0.3, y0 - 0.02, 3.0, 8.6)
    for k in range(6):
        z = 3.5 + k * 0.85
        K.box("board_line", -5.1, -2.3, y0 - 0.34, y0 - 0.3, z, z + 0.45)
    for x in (-3.2, 0.0, 3.2):                                    # the top storey's windows above the screen
        K.window(x, y0, 10.0, 1.3, 1.8)
    K.door(-3.7, y0, 0.0, 1.4, 2.3)
    for x in (-0.6, 2.0, 4.6):
        K.window(x, y0, 0.5, 1.4, 1.7)
    for x in (-3.5, 0.0, 3.5):
        for z in (3.6, 10.0):
            K.window(x, y0 + D, z, 1.4, 1.8, d=1)
    return {"width": W + 12.0, "depth": y0 + D, "height": round(gz + 4.0, 2)}


def shed(L=16.0, D=7.0):
    """The low brick shed of photo 6: brick walls, a tiled hipped roof, small windows, a white door."""
    h = L / 2
    K.box("brick_red", -h, h, 0.0, D, -1.0, 3.4)
    K.hip_roof(-h, h, 0.0, D, 3.4, 2.4, 0.5, mat="tile")
    for x in (-h + 2.5, -1.5, 2.5, h - 2.5):
        K.window(x, 0.0, 1.0, 1.3, 1.2)
    K.door(h - 5.0, 0.0, 0.0, 1.6, 2.5)
    return {"width": L, "depth": D, "height": 5.8}


def floodlight(H=34.0):
    """A floodlight mast (photo 5): a tapering pale mast and a head frame of lamps facing the course."""
    K.box("concrete", -0.9, 0.9, -0.9, 0.9, -1.0, 0.6)
    K.cyl("mast", 0.0, 0.0, 0.0, H, 0.45, 0.22, 10)
    K.box("roof_edge", -2.6, 2.6, -0.6, -0.3, H - 0.4, H + 3.2)
    for r in range(3):
        for c in range(4):
            x = -2.0 + c * 1.33; z = H + 0.1 + r * 1.0
            K.box("lamp", x - 0.5, x + 0.5, -0.75, -0.6, z, z + 0.8)
    return {"width": 5.2, "depth": 1.8, "height": H + 3.2}


# ------------------------------------------------------------------------------------------ build and export
PIECES = [
    ("park_arch_stand", lambda: arch_stand(9, 8.0, "arch")),
    ("park_gable_stand", lambda: arch_stand(7, 8.0, "gable")),
    ("park_victorian", victorian),
    ("park_glass_box", lambda: glass_box(30.0, 3, "left")),
    ("park_glass_box_small", lambda: glass_box(22.0, 2, "right")),
    ("park_stair_tower", stair_link),
    ("park_terrace", open_terrace),
    ("park_link", shoulder_link),
    ("park_clock_house", clock_house),
    ("park_shed", shed),
    ("park_floodlight", floodlight),
]
LIB = bpy.data.collections.new("park_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-22s %6d triangles, %3d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "The Park's stand kit (tools/blender/build_park_stands.py). Building axes: x along the front (left to "
                     "right from the track), y into the building (front faces -y), z up; origin the middle of the front on "
                     "the ground. crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "park_stands.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "park_stands.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported park_stands.glb", flush=True)

REN = rp("reference/park/renders")
os.makedirs(REN, exist_ok=True)


def setup_scene(w, hgt, samples=None):
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.56, 0.70, 0.90, 1); bg.inputs["Strength"].default_value = 1.0
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.2; sun.data.angle = math.radians(3)
    sun.rotation_euler = (math.radians(52), 0, math.radians(-35))
    scene.render.engine = "CYCLES"; scene.cycles.samples = samples or int(os.environ.get("SAMPLES", "24"))
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = w, hgt
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "JPEG"; scene.render.image_settings.quality = 90
    return scene


def shoot(scene, name, frm, to, lens=30):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); cam.data.lens = lens; cam.data.clip_end = 5000
    scene.collection.objects.link(cam)
    cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    scene.render.filepath = os.path.join(REN, name + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("rendered", name, flush=True)


def lawn(cx, cy, size, mat="lawn", col="#b2c98a"):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(cx, cy, 0))
    bpy.context.object.data.materials.append(material(mat, col))


if os.environ.get("SHEET"):          # the catalogue: the stands, then the smaller pieces and the festival side's
    groups = [["park_glass_box_small", "park_victorian", "park_glass_box"], ["park_arch_stand"],
              ["park_gable_stand", "park_stair_tower", "park_terrace", "park_link"], ["park_clock_house", "park_shed", "park_floodlight"]]
    scene = setup_scene(1800, 900)
    lawn(0, 0, 4000)
    x = 0.0
    spans = []
    for g in groups:
        x0 = x
        for name in g:
            w = INFO[name]["width"]
            OBJ[name].location = (x + w / 2, 0, 0)
            x += w + 10
        spans.append((x0, x - 10))
        x += 150
    for k, (a, b) in enumerate(spans):
        mid, span = (a + b) / 2, b - a
        dist = max(span * 0.95, 70)
        shoot(scene, "kit-sheet-%d" % (k + 1), (mid - span * 0.15, -dist, dist * 0.22), (mid, 8, 9), lens=34)

if os.environ.get("ARRANGE"):        # the stand side assembled, the track and the festival side opposite (massing only)
    import random
    LAY = json.load(open(rp("courses/park-draft.json")))
    TW = LAY["trackWidth"]
    scene = setup_scene(2400, 1200)
    for o in OBJ.values():
        o.location = (99999, 0, 0)
    # Blender axes here: x = world x (along the straight; the horses run towards -x), y = -world z (the stands at +y)
    lawn(150, 0, 4000)
    def strip(mat, col, x0, x1, y0, y1, z=0.02):
        bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, z))
        ob = bpy.context.object; ob.scale = (x1 - x0, y1 - y0, 1)
        ob.data.materials.append(material(mat, col))
    strip("turf", "#7aa94f", -300, 900, 0.0, TW)                     # the run-in (world z 0 to -TW)
    for y in (0.0, TW):                                               # the rails
        strip("rail", "#ffffff", -300, 900, y - 0.08, y + 0.08, 1.05)
    strip("lawn_path", "#cfc6b4", -300, 900, TW + 1.0, TW + 4.0, 0.03)   # the walk along the stand-side rail
    # the stands on one front line: copies, so a piece can be used twice
    def put(name, x, y, turn=0.0, stretch=None):
        ob = OBJ[name].copy(); scene.collection.objects.link(ob)
        ob.location = (x, y, 0); ob.rotation_euler = (0, 0, math.radians(turn))
        if stretch: ob.scale = (stretch, 1, 1)
        return ob
    for p in LAY["stands"]["chain"]:
        put(p["piece"], p["x"], -p["z"], 0.0, p.get("stretch"))
    for p in LAY["festival"]["pieces"]:
        put(p["piece"], p["x"], -p["z"], 180.0, p.get("stretch"))
    # a few marquees on the festival lawn (York's festival kit does this in the race view; here only to read the zone)
    MQ = bpy.data.collections.new("mq"); scene.collection.children.link(MQ)
    def marquee(w, d, mat):
        K.box("canvas", -w / 2, w / 2, 0, d, 0, 2.6)
        bm = K.bm(mat); v = lambda x, y, z: bm.verts.new(Vector((x, y, z)))
        c = [v(-w / 2 - 0.3, -0.3, 2.6), v(w / 2 + 0.3, -0.3, 2.6), v(w / 2 + 0.3, d + 0.3, 2.6), v(-w / 2 - 0.3, d + 0.3, 2.6)]
        t = v(0, d / 2, 2.6 + min(w, d) * 0.45)
        for i in range(4): bm.faces.new((c[i], c[(i + 1) % 4], t))
        ob, _ = kit_to_object(K, "marquee", MATS, MQ); return ob
    rq = random.Random(7)
    for k in range(16):
        ob = marquee(rq.choice((8, 10, 12)), rq.choice((8, 10)), rq.choice(FLAGS))
        ob.location = (rq.uniform(-5, 235), -rq.uniform(70, 145), 0); ob.rotation_euler = (0, 0, math.radians(rq.choice((0, 90, 180))))
    rnd = random.Random(4)
    treem = material("tree", "#6f9a52")
    def tree(x, y, s):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=s, location=(x, y, s * 1.3))
        o = bpy.context.object; o.scale = (1, 1, 1.15); o.data.materials.append(treem)
        bpy.ops.object.shade_smooth()
    for x in range(-200, 700, 14):                                    # a belt behind the stands and beyond the festival
        tree(x + rnd.uniform(-4, 4), TW + 95 + rnd.uniform(-8, 8), rnd.uniform(4.5, 7))
        tree(x + rnd.uniform(-4, 4), -200 + rnd.uniform(-10, 10), rnd.uniform(4.5, 7))
    shoot(scene, "park-standside-from-infield", (70, -250, 48), (70, 50, 6), lens=40)
    shoot(scene, "park-standside-rail", (190, -6, 4.5), (-20, 52, 9), lens=26)
    shoot(scene, "park-festival-from-stands", (60, 70, 26), (90, -110, 6), lens=30)
    shoot(scene, "park-stands-aerial", (-120, -170, 120), (90, 40, 0), lens=32)
