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
  park_old_pavilion   the old brick building in the middle of photo 4, which the owner chose for the middle of the
                      stand side (16 Nov): an arcade of round-headed openings, a first-floor balcony with an iron
                      lattice railing and a white fretwork valance, a big half-timbered gable with the name board,
                      a white clock turret on the ridge, tall chimneys
  park_tiered_stand   the right-hand stand of York's grandstands of 1895 (owner, 16 Nov): a brick arcade at ground
                      level, two open tiers with slim posts and balustrades wrapping round the ends, a hipped roof,
                      chimneys, and standing steps down to the lawn in front; drawn to his section sketch: tall
  park_balcony_stand  (owner's concept, 17 Nov) steps up to a colonnade of square piers; a balustrade with ball
                      finials before open seating; two covered galleries on bracketed columns; a flat roof behind a
                      bracketed cornice and a rooftop balustrade; a panelled end block with an aedicule and flags
  park_roof_terrace_stand  (his second concept) the same base; one tall covered gallery whose roof is a stepped
                      terrace of seats rising to a parapet at the back, the flank wall following the slope
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
        "shade": "#a9958d", "flag_a": "#e7a3a0", "flag_b": "#9fbad8", "flag_c": "#f1d38f", "flag_d": "#a9cfa6", "lamp": "#fff6dc"}
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
    return {"width": round(L, 2), "depth": round(D + 0.6, 2), "height": round(top_z + (5.0 if flags else 0.0), 2),
            "section": {"stepsTop": round(0.2 + (GS["R"] - 1) * GS["rs"], 2), "stepsBack": YS, "shoulder": round(ZD, 2),
                        "deckBack": round(ZD + (rows - 1) * rs, 2), "deckBackY": round(yW, 2), "springing": round(zs, 2),
                        "crown": round(zs + (bay * 0.3 if roof == "arch" else bay / 2 * 0.9), 2),
                        "raisedCrown": round(zs + 3.2 + (bay * 0.3 if roof == "arch" else bay / 2 * 0.9), 2),
                        "columns": round(yF, 2), "roofFront": round(yR0, 2), "back": round(D, 2), "bay": bay, "bays": nb}}


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


def old_pavilion(nb=5, bay=4.8):
    """The old building in the middle of photo 4 (owner, 16 Nov: "model the old element of this image in the middle
    instead of the pavilion with the two point towers", with a close-up of it and York's stands of 1895 as the type for
    the generic pavilion stand). Red brick, two storeys, nearly square:
      - the ground floor: round-headed windows with cream surrounds, a door in the middle;
      - the first floor: an open arcade of brick round arches on brick piers, cream edges to the arches, a low cream
        balustrade between the piers; behind them, benches rising back under the roof (its crowd); a central stair up
        to it from the lawn;
      - over the arches, a band of cream lattice on a dark ground with the course's name board in the middle;
      - a big, steep hipped slate roof reaching out over the arcade; a cream gable over the middle bay with its date
        board; a clock turret on the ridge (cream, clocks on three faces, a red results panel, a lead ogee cap, a
        gilt cross); tall brick chimneys at the ends.
    Origin: the middle of the front on the ground."""
    L = nb * bay; h = L / 2
    G, D = 4.0, 14.0
    pw = 0.8                                                      # the piers' width
    zs = G + 2.4                                                  # where the arches spring
    r = (bay - pw) / 2
    zc = zs + r                                                   # the arches' crown
    zf = zc + 0.45                                                # the lattice band's foot
    E = zf + 1.3                                                  # the eaves
    K.box("brick_red", -h, h, 0.0, D, -1.0, G)
    K.box("quoin", -h - 0.08, h + 0.08, -0.12, D + 0.05, G - 0.35, G)
    for i in range(nb):                                           # the ground floor's windows
        cx = -h + bay * (i + 0.5)
        if i == nb // 2:
            K.door(cx, 0.0, 0.0, 1.8, 2.7)
            continue
        w2, za = 0.85, 2.3
        K.box("glass", cx - w2, cx + w2, -0.06, 0.02, 0.7, za)
        K.arc_band("glass", cx, za, 0.0, w2, 0.0, math.pi, -0.06, 0.02, 10)
        K.arc_band("quoin", cx, za, w2, w2 + 0.25, 0.0, math.pi, -0.14, 0.0, 10)
        K.box("quoin", cx - w2 - 0.15, cx + w2 + 0.15, -0.18, 0.0, 0.55, 0.7)
    # the first floor: benches rising back from the arcade, a back wall with windows
    yb0, rows, tr, rs = 1.2, 5, 1.0, 0.42
    prof = [(yb0, G - 0.3)]
    for k in range(rows):
        prof += [(yb0 + k * tr, G + k * rs), (yb0 + (k + 1) * tr, G + k * rs)]
        y1 = yb0 + (k + 1) * tr
        K.box("bench", -h + 0.5, h - 0.5, y1 - 0.4, y1 - 0.1, G + k * rs, G + k * rs + 0.42)
        rarea(-h + 0.5, h - 0.5, yb0 + k * tr + 0.05, y1 - 0.45, G + k * rs)
    yW = yb0 + rows * tr
    prof += [(yW, G - 0.3)]
    K.prism_x("concrete", -h + 0.05, h - 0.05, prof)
    rarea(-h + 0.6, h - 0.6, pw + 0.1, yb0 - 0.1, G)
    K.box("brick_red", -h, h, yW, D, G, E)
    for i in range(nb):
        K.window(-h + bay * (i + 0.5), D, G + 1.0, 1.3, 2.0, d=1)
    for x in (-h, h):                                             # the end walls up the first floor
        K.box("brick_red", x - 0.3 if x < 0 else x, x if x < 0 else x + 0.3, pw, yW, G, E)
    # the arcade: piers, arches, the brick over them, cream edges, the balustrade
    for i in range(nb + 1):
        x = -h + bay * i
        K.box("brick_red", x - pw / 2, x + pw / 2, 0.0, pw, G, zs)
        K.box("quoin", x - pw / 2 - 0.08, x + pw / 2 + 0.08, -0.08, pw + 0.05, zs - 0.25, zs)
    n = 10
    for i in range(nb):
        cx = -h + bay * (i + 0.5)
        K.arc_band("quoin", cx, zs, r - 0.02, r + 0.16, 0.0, math.pi, -0.08, 0.0, n)
        K.arc_band("brick_red", cx, zs, r, r + 0.05, 0.0, math.pi, 0.0, pw, n)
        for j in range(n):                                        # the spandrels, as strips up to the band
            a0, a1 = math.pi * j / n, math.pi * (j + 1) / n
            xa, xb = cx + r * math.cos(a0), cx + r * math.cos(a1)
            za, zb = zs + r * math.sin(a0), zs + r * math.sin(a1)
            K.prism_y("brick_red", 0.0, pw, [(xa, za), (xa, zf), (xb, zf), (xb, zb)][::-1] if xb < xa else [(xa, za), (xb, zb), (xb, zf), (xa, zf)])
        if i != nb // 2:
            K.balustrade(cx - r, cx + r, 0.25, G, h=1.0, mat="quoin", spacing=0.3, piers=False)
    # the lattice band and the name board
    K.box("board", -h - 0.1, h + 0.1, -0.12, pw, zf, E)
    if not K.far:
        m_ = int(L / 0.9)
        for j in range(m_):
            xa, xb = -h + L * j / m_, -h + L * (j + 1) / m_
            strut("quoin", (xa, -0.16, zf + 0.1), (xb, -0.16, E - 0.1), r=0.05)
            strut("quoin", (xb, -0.16, zf + 0.1), (xa, -0.16, E - 0.1), r=0.05)
    K.box("quoin", -h - 0.1, h + 0.1, -0.2, pw, zf - 0.1, zf + 0.08)
    K.box("quoin", -h - 0.1, h + 0.1, -0.2, pw, E - 0.08, E + 0.1)
    K.box("quoin", -5.2, 5.2, -0.32, -0.16, zf + 0.12, E - 0.12)                       # the name board
    K.box("board", -4.8, 4.8, -0.36, -0.32, zf + 0.45, zf + 0.85)
    # the roof: steep, hipped, reaching out over the arcade
    K.hip_roof(-h, h, -0.6, D, E + 0.1, 5.6, 0.7, mat="slate")
    gw = bay + 1.4
    rz = gable_y(-gw / 2, gw / 2, -1.3, 4.5, E + 0.1, 52, 0.5, roof="slate", wall="quoin")
    K.box("board", -1.5, 1.5, -1.45, -1.3, E + 0.9, E + 1.6)                           # the date board
    K.box("board_line", -1.2, 1.2, -1.5, -1.45, E + 1.1, E + 1.4)
    # the clock turret on the ridge
    cy, cw = (D - 0.6) / 2, 2.8
    z0 = E + 0.1 + 5.6 - 1.4
    K.box("quoin", -cw / 2, cw / 2, cy - cw / 2, cy + cw / 2, z0, z0 + 3.6)
    K.box("redband", -0.9, 0.9, cy - cw / 2 - 0.08, cy - cw / 2, z0 + 0.3, z0 + 0.9)  # the results panel
    for rot in (0.0, math.pi / 2, -math.pi / 2):
        K.push(Matrix.Translation((0, cy, 0)) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Translation((0, -cw / 2, 0)))
        clock_face(0.0, 0.0, z0 + 2.2, 0.95)
        K.pop()
    K.cornice(-cw / 2, cw / 2, cy - cw / 2, cy + cw / 2, z0 + 3.6, 0.2, 0.3)
    K.sphere("slate", 0.0, cy, z0 + 4.3, cw / 2 + 0.1, 2, 1.0)
    K.cyl("gilt", 0.0, cy, z0 + 5.3, z0 + 7.0, 0.06, 0.05, 6)
    K.box("gilt", -0.45, 0.45, cy - 0.05, cy + 0.05, z0 + 6.3, z0 + 6.42)
    # tall chimneys at the ends
    for x in (-h + 1.2, h - 1.2):
        y = D - 3.5
        K.box("brick_red", x - 0.8, x + 0.8, y - 0.55, y + 0.55, E + 1.0, E + 7.5)
        K.box("brick", x - 0.95, x + 0.95, y - 0.7, y + 0.7, E + 7.5, E + 7.8)
        for dx in (-0.35, 0.35):
            K.cyl("clock_dark", x + dx, y, E + 7.8, E + 8.4, 0.16, 0.13, 6)
    # the central stair from the lawn up to the arcade, brick cheeks
    sw, ns = 3.2, 11
    K.prism_x("steps", -sw / 2, sw / 2, [(-ns * 0.42, -1.0)] + [q for k in range(ns) for q in ((-(ns - k) * 0.42, (k + 1) * G / ns), (-(ns - k - 1) * 0.42, (k + 1) * G / ns))] + [(0.0, -1.0)])
    for s in (-1, 1):
        x = s * (sw / 2 + 0.2)
        K.prism_x("brick_red", x - 0.2, x + 0.2, [(-ns * 0.42 - 0.2, -1.0), (-ns * 0.42 - 0.2, 0.9), (0.0, G + 1.0), (0.0, -1.0)])
    rarea(-h + 0.4, h - 0.4, -ns * 0.42 - 3.0, -0.4, 0.0)       # the lawn in front
    return {"width": round(L + 0.6, 2), "depth": D, "height": round(z0 + 7.0, 2)}


def tiered_stand(nb=11, bay=3.6, terrace=False):
    """The tiered grandstand, after York's stands of 1895, the owner's section sketch, and (16 Nov, late) his concept
    image, which this follows: "here is a concept image that you should work from". Then (17 Nov) his drawing set for
    the ends and the terrace only: no added end bay ("remove the two bays of infill to the end"), stairs at both ends
    of both galleries with their triangular flank walls, the side walls solid and panelled at the back, the terrace
    back in. Its levels (eaves 13.2 m) made it "squat": the proportions are the concept build's. From the ground up:
      - an arcade of tall round arches on square piers: plinths, moulded imposts, archivolts and keystones, a deep
        cornice over (the arcade 6.6 m to its top; the openings 2.3 m wide, the arches springing at 4.3 m);
      - on the cornice, a classical balustrade with a pedestal on every pier and a ball finial on each, broken in the
        middle by a pediment with a roundel;
      - the lower gallery: benches on a gentle rake back from the balustrade; slim turned columns with capitals and
        curved brackets on every bay line, carrying a deep floor edge;
      - the upper gallery: the same, taller, its own balustrade with pedestals and finials on the floor edge;
      - a stair rising across the left end of each gallery behind a raking balustrade;
      - the ends as his side elevations: the ground storey closed but for an arch into the loggia; above, open at the
        front over the stairs and solid, panelled, from 5.5 m back;
      - the rear a panel grid with lunettes under the eaves;
      - a big hipped roof on close-set brackets under the eaves, three small louvred cupolas on the ridge.
    The section follows his sketch: the arcade standing forward of the gallery columns, the rakes back to a back
    wall, the thin lines columns, not walls (owner). terrace=True puts his shallow terrace down to the lawn in front;
    his concept has none. Origin: the middle of the arcade's front on the ground."""
    L = nb * bay; h = L / 2
    y0 = 0.0
    TP, rows_t, tr_t, rs_t = 2.0, 6, 1.3, 0.2                     # the terrace: a platform before the arcade, six steps
    if terrace:
        y_ = -TP - rows_t * tr_t
        prof = [(y_, -1.0)]
        for k in range(rows_t):
            prof += [(y_ + k * tr_t, (k + 1) * rs_t), (y_ + (k + 1) * tr_t, (k + 1) * rs_t)]
            rarea(-h - 1.0, h + 1.0, y_ + k * tr_t + 0.1, y_ + (k + 1) * tr_t - 0.1, k * rs_t)
        prof += [(0.0, rows_t * rs_t), (0.0, -1.0)]
        K.prism_x("steps", -h - 1.5, h + 1.5, prof)
        rarea(-h + 0.4, h - 0.4, -TP + 0.2, -0.3, rows_t * rs_t)
    base = rows_t * rs_t if terrace else 0.25                     # the arcade's floor: the terrace's platform
    yA = 0.0                                                      # the arcade's front
    # the proportions of the concept build the owner preferred ("why is it so squat? the last version was better"),
    # lifted onto the terrace's platform: the arcade 6.35 m above it, the galleries 6.4 m and 8.2 m
    # owner, 17 Nov: "make the whole stand about 2m deeper ... extend the building back 2m. And take maybe 1m off the
    # height": the back wall 2 m further back (the rakes a row deeper each), the galleries 0.2 m and 0.8 m lower
    A = base + 6.35                                               # the lower gallery's floor
    yp = yA + 1.6                                                 # the gallery columns
    U = A + 6.2                                                   # the upper gallery's floor
    Eav = U + 7.4                                                 # the eaves
    yB = yp + 14.0                                                # the back wall (owner, 17 Nov: another 2 m deeper)
    yR = yp + 9.0                                                 # the back of the rakes
    yE = yA + 5.5                                                 # the end walls' solid part starts here
    # ---- the arcade
    w2, zi = 1.15, base + 4.05                                    # half an opening; the impost (where the arches spring)
    rec = 0.9                                                     # the openings' depth to the wall behind
    yL = yA + rec + 2.6                                           # the loggia's back wall: the arches open into it
    K.box("shade", -h, h, yL, yB, -1.0, A - 0.8)
    K.box("shade", -h, h, yA + rec, yL, A - 1.05, A - 0.8)        # the loggia's ceiling
    K.box("podium", -h, h, yA + rec, yL, -1.0, base)              # its floor
    for i in range(nb):
        K.box("glass", -h + bay * (i + 0.5) - 0.8, -h + bay * (i + 0.5) + 0.8, yL - 0.06, yL, base, base + 2.85)    # doors at its back
    K.box("podium", -h - 0.2, h + 0.2, yA - 0.25, yA + rec, -1.0, base)               # the step along the front
    for i in range(nb + 1):                                       # the piers
        x = -h + bay * i
        pa, pb = x - (bay / 2 - w2), x + (bay / 2 - w2)
        K.box("quoin", pa, pb, yA, yA + rec, base, zi)
        K.box("podium", pa - 0.12, pb + 0.12, yA - 0.12, yA + rec, base, base + 0.75)  # the plinth
        K.box("podium", pa - 0.15, pb + 0.15, yA - 0.15, yA + rec, zi - 0.35, zi)      # the impost
        K.box("podium", pa - 0.1, pb + 0.1, yA - 0.1, yA + rec, zi - 0.5, zi - 0.35)
    n = 12
    for i in range(nb):
        cx = -h + bay * (i + 0.5)
        K.arc_band("quoin", cx, zi, w2, w2 + 0.05, 0.0, math.pi, yA, yA + rec, n)      # the soffit
        K.arc_band("podium", cx, zi, w2 - 0.02, w2 + 0.32, 0.0, math.pi, yA - 0.12, yA, n)   # the archivolt
        K.box("podium", cx - 0.2, cx + 0.2, yA - 0.2, yA, zi + w2 - 0.05, A - 1.0)      # the keystone
        for j in range(n):                                        # the spandrels up to the cornice
            a0, a1 = math.pi * j / n, math.pi * (j + 1) / n
            xa, xb = cx + (w2 + 0.05) * math.cos(a0), cx + (w2 + 0.05) * math.cos(a1)
            za, zb = zi + (w2 + 0.05) * math.sin(a0), zi + (w2 + 0.05) * math.sin(a1)
            K.prism_y("quoin", yA, yA + rec, [(xb, zb), (xa, za), (xa, A - 1.0), (xb, A - 1.0)])
    K.box("quoin", -h - 0.1, h + 0.1, yA, yA + rec, A - 1.0, A - 0.6)                 # the frieze
    K.box("podium", -h - 0.3, h + 0.3, yA - 0.3, yA + rec, A - 0.6, A - 0.35)         # the cornice, stepped out
    K.box("podium", -h - 0.5, h + 0.5, yA - 0.5, yp + 0.3, A - 0.35, A)
    rarea(-h + 0.4, h - 0.4, yA + rec + 0.3, yp + 2.0, base)                           # people in the loggia
    # ---- balustrades: square balusters, a pedestal on every bay line with a ball finial
    def classic_rail(x0, x1, y, z, ped=True, gap=None):
        K.balustrade(x0, x1, y, z, h=1.1, mat="trim", spacing=0.3, piers=False)
        K.box("trim", x0, x1, y - 0.22, y + 0.22, z + 1.02, z + 1.16)                  # a broad coping
        if ped:
            for i in range(nb + 1):
                x = -h + bay * i
                if gap and gap[0] < x < gap[1]:
                    continue
                K.box("trim", x - 0.3, x + 0.3, y - 0.3, y + 0.3, z, z + 1.3)
                K.box("trim", x - 0.36, x + 0.36, y - 0.36, y + 0.36, z + 1.3, z + 1.42)
                K.sphere("trim", x, y, z + 1.72, 0.26, 2)
    # the pediment over the middle of the arcade, breaking the balustrade
    pw = bay * 1.5
    classic_rail(-h, -pw / 2, yA - 0.05, A, gap=(-pw / 2 - 0.1, pw / 2 + 0.1))
    classic_rail(pw / 2, h, yA - 0.05, A, ped=False)
    for x in (-pw / 2, pw / 2):
        K.box("trim", x - 0.35, x + 0.35, yA - 0.35, yA + 0.3, A, A + 1.45)
        K.sphere("trim", x, yA - 0.02, A + 1.78, 0.28, 2)
    K.box("quoin", -pw / 2, pw / 2, yA - 0.25, yA + 0.3, A, A + 0.9)
    K.prism_y("podium", yA - 0.4, yA + 0.3, [(-pw / 2 - 0.3, A + 0.85), (pw / 2 + 0.3, A + 0.85), (0.0, A + 2.6)][::-1])
    K.prism_y("quoin", yA - 0.32, yA + 0.2, [(-pw / 2 + 0.35, A + 1.0), (pw / 2 - 0.35, A + 1.0), (0.0, A + 2.25)][::-1])
    K.disc_y("podium", 0.0, yA - 0.44, yA - 0.3, A + 1.55, 0.42, 20)
    for i in range(1, nb):                                        # the arcade rail's other pedestals
        x = -h + bay * i
        if x > pw / 2 + 0.1:
            K.box("trim", x - 0.3, x + 0.3, yA - 0.35, yA + 0.25, A, A + 1.3)
            K.box("trim", x - 0.36, x + 0.36, yA - 0.41, yA + 0.31, A + 1.3, A + 1.42)
            K.sphere("trim", x, yA - 0.05, A + 1.72, 0.26, 2)
    for x in (h,):
        K.box("trim", x - 0.3, x + 0.3, yA - 0.35, yA + 0.25, A, A + 1.3)
        K.sphere("trim", x, yA - 0.05, A + 1.72, 0.26, 2)
    # ---- the galleries: rakes, columns with brackets, deep floor edges
    sw = 1.8                                                      # the end stairs' width (below)
    def rake(z0, y0_, rows, rs):
        tr = (yR - y0_) / rows
        prof = [(y0_ - 0.3, z0 - 0.5), (y0_ - 0.3, z0)]
        for j in range(rows):
            ya, yb = y0_ + j * tr, y0_ + (j + 1) * tr
            prof += [(ya, z0 + j * rs), (yb, z0 + j * rs)]
            K.box("bench", -h + sw + 0.6, h - sw - 0.6, yb - 0.42, yb - 0.12, z0 + j * rs, z0 + j * rs + 0.42)
            rarea(-h + sw + 0.6, h - sw - 0.6, ya + 0.05, yb - 0.45, z0 + j * rs)
        prof += [(yR, z0 - 0.5)]
        K.prism_x("concrete", -h, h, prof)
        return z0 + (rows - 1) * rs
    zl = rake(A, yp + 0.8, 9, 0.38)
    rarea(-h + 0.4, h - 0.4, yA + 0.3, yp + 0.5, A)
    zu = rake(U, yp + 0.8, 10, 0.36)
    K.box("shade", -h, h, yp, yR, U - 1.06, U - 1.0)
    K.box("quoin", -h - 0.3, h + 0.3, yp - 0.75, yp + 0.4, U - 1.0, U)                  # the upper floor's deep edge
    K.box("podium", -h - 0.4, h + 0.4, yp - 0.85, yp + 0.4, U - 1.0, U - 0.8)
    classic_rail(-h, h, yp - 0.45, U)
    rarea(-h + 0.4, h - 0.4, yp - 0.2, yp + 0.6, U)
    def column(x, z0, z1, brackets=True):
        r = 0.16
        K.box("trim", x - 0.3, x + 0.3, yp - 0.3, yp + 0.3, z0, z0 + 0.4)              # the base
        K.cyl("trim", x, yp, z0 + 0.4, z1 - 0.55, r + 0.03, r, 10)                     # the shaft, tapering a little
        K.cyl("trim", x, yp, z1 - 0.55, z1 - 0.3, r + 0.03, r + 0.14, 10)              # the capital's bell
        K.box("trim", x - 0.3, x + 0.3, yp - 0.3, yp + 0.3, z1 - 0.3, z1)              # the abacus
        if brackets and not K.far:
            R = 0.95
            for s_ in (-1, 1):
                if abs(x + s_ * R) > h + 0.01:
                    continue
                cxr = x + s_ * (R + r)
                a0, a1 = (math.pi / 2, math.pi) if s_ > 0 else (0.0, math.pi / 2)
                K.arc_band("trim", cxr, z1 - R, R - 0.12, R, a0, a1, yp - 0.07, yp + 0.07, 8)
                K.arc_band("trim", cxr, z1 - R, R * 0.45, R * 0.55, a0, a1, yp - 0.05, yp + 0.05, 6)
    for i in range(nb + 1):
        x = -h + bay * i
        column(x, A, U - 1.0)
        column(x, U, Eav - 0.6)
    K.box("trim", -h - 0.3, h + 0.3, yp - 0.4, yp + 0.4, Eav - 0.6, Eav)              # the eaves beam
    # the end stairs (as the concept): a flight climbing each gallery's end bay from the front to the back, a solid
    # triangular flank wall on its inner side under a raking balustrade, a newel pedestal at its foot. Both galleries
    # at the left; the lower gallery at the right too, as the concept shows.
    sw = 1.8                                                       # the flight's width
    def end_stair(side, z0, ztop):
        xo = side * h                                              # the end
        xi = xo - side * sw                                        # the flight's inner edge
        ya, yb = yp + 0.5, yR - 0.2                                # its foot and head
        nst = max(4, int((ztop - z0) / 0.18))
        prof = [(ya, z0 - 0.05)]
        for k in range(nst):
            y1 = ya + (yb - ya) * (k + 1) / nst
            prof += [(ya + (yb - ya) * k / nst, z0 + (ztop - z0) * (k + 1) / nst), (y1, z0 + (ztop - z0) * (k + 1) / nst)]
        prof += [(yb, z0 - 0.05)]
        K.prism_x("steps", min(xo, xi), max(xo, xi), prof)
        ox0, ox1 = sorted((xo, xo + side * 0.3))                   # the outer cheek, closing under the flight
        K.prism_x("quoin", ox0, ox1, [(ya, z0 - 0.6), (yb, z0 - 0.6), (yb, ztop + 0.1), (ya, z0 + 0.1)])
        fx0, fx1 = sorted((xi, xi - side * 0.3))                   # the flank wall, a triangle under the rail
        K.prism_x("quoin", fx0, fx1, [(ya, z0), (yb, z0), (yb, ztop + 0.9), (ya, z0 + 0.9)])
        K.prism_x("trim", fx0 - 0.08, fx1 + 0.08, [(ya, z0 + 0.9), (yb, ztop + 0.9), (yb, ztop + 1.05), (ya, z0 + 1.05)])
        if not K.far:                                              # the balusters along its top
            k = 12
            for j in range(k):
                f = (j + 0.5) / k
                y = ya + (yb - ya) * f; z = z0 + (ztop - z0) * f + 1.05
                K.box("trim", (fx0 + fx1) / 2 - 0.05, (fx0 + fx1) / 2 + 0.05, y - 0.05, y + 0.05, z, z + 0.85)
            strut("trim", ((fx0 + fx1) / 2, ya, z0 + 1.95), ((fx0 + fx1) / 2, yb, ztop + 1.95), r=0.09)
        xc = (fx0 + fx1) / 2                                       # the newel at the foot
        K.box("trim", xc - 0.3, xc + 0.3, ya - 0.6, ya, z0, z0 + 1.4)
        K.sphere("trim", xc, ya - 0.3, z0 + 1.68, 0.25, 2)
    for side in (-1, 1):                                          # both ends, both stands (the side elevations)
        end_stair(side, A, zl)
        end_stair(side, U, zu)
    # ---- the back wall, in shade within; doors
    K.box("wall", -h, h, yB, yB + 0.4, -1.0, Eav)
    K.box("shade", -h, h, yB - 0.04, yB, A - 0.4, Eav)
    for i in range(nb):
        cx = -h + bay * (i + 0.5)
        K.door(cx, yB - 0.04, zl, 1.2, 2.4)
        K.door(cx, yB - 0.04, zu, 1.2, 2.4)
    K.box("concrete", -h, h, yR, yB, zl - 0.4, zl)
    K.box("concrete", -h, h, yR, yB, zu - 0.4, zu)
    K.box("shade", -h, h, yR, yB, zu - 0.46, zu - 0.4)
    K.box("quoin", -h, h, yR, yB, -1.0, zl - 0.4)
    # ---- the ends (the side elevations): the ground storey closed but for an arch into the loggia; above it, open at
    # the front over the stairs, solid and panelled from yE back
    for side in (-1, 1):
        x0w, x1w = sorted((side * h, side * (h + 0.4)))
        K.box("wall", x0w, x1w, yA, yB + 0.4, -1.0, A - 0.6)
        K.push(Matrix.Translation((side * (h + 0.4), 0, 0)) @ Matrix.Rotation(math.pi / 2 * side, 4, "Z"))
        yy = (yA + rec + 1.3) * side
        K.box("shade", yy - 0.95, yy + 0.95, -0.05, 0.02, base, zi)
        K.arc_band("shade", yy, zi, 0.0, 0.95, 0.0, math.pi, -0.05, 0.02, 10)
        K.arc_band("podium", yy, zi, 0.93, 1.2, 0.0, math.pi, -0.15, 0.0, 10)
        K.pop()
        K.box("wall", x0w, x1w, yE, yB + 0.4, A - 0.6, Eav)
        xf = side * (h + 0.4)                                     # the panel grid on its face
        for y in [yE + (yB + 0.4 - yE) * k / 3 for k in range(4)]:
            K.box("quoin", min(xf, xf + side * 0.15), max(xf, xf + side * 0.15), y - 0.25, y + 0.25, -1.0, Eav - 0.3)
        for z in (A - 0.6, A + 0.2, U - 0.6, U + 0.2, Eav - 0.6):
            K.box("quoin", min(xf, xf + side * 0.15), max(xf, xf + side * 0.15), yE - 0.25, yB + 0.65, z - 0.15, z + 0.15)
        K.box("quoin", min(xf, xf + side * 0.18), max(xf, xf + side * 0.18), yA - 0.2, yE, A - 0.75, A - 0.45)
    # the rear: a panel grid, lunettes under the eaves in the middle bays
    yb_ = yB + 0.4
    for i in range(nb + 1):
        x = -h + bay * i
        K.box("quoin", x - 0.25, x + 0.25, yb_, yb_ + 0.15, -1.0, Eav - 0.3)
    for z in (A - 0.6, U - 0.6, Eav - 0.6):
        K.box("quoin", -h - 0.4, h + 0.4, yb_, yb_ + 0.15, z - 0.15, z + 0.15)
    for i in range(2, nb - 2):
        cx = -h + bay * (i + 0.5)
        K.arc_band("glass", cx, Eav - 2.4, 0.0, 1.0, 0.0, math.pi, yb_ + 0.0, yb_ + 0.06, 10)
        K.arc_band("quoin", cx, Eav - 2.4, 1.0, 1.2, 0.0, math.pi, yb_, yb_ + 0.12, 10)
    # ---- the roof: hipped, a big overhang on close-set brackets; three louvred cupolas on the ridge
    rise = 5.8
    x0r, x1r, y0r, y1r = -h - 0.4, h + 0.4, yp - 1.6, yB + 0.4
    K.box("shade", x0r, x1r, y0r, y1r, Eav - 0.12, Eav - 0.02)
    K.hip_roof(x0r, x1r, y0r, y1r, Eav, rise, 1.4, mat="slate")
    if not K.far:
        k = int((x1r - x0r + 2.8) / 1.0)
        for j in range(k + 1):                                    # the eaves brackets along the front
            x = x0r - 1.4 + (x1r - x0r + 2.8) * j / k
            K.prism_x("trim", x - 0.1, x + 0.1, [(y0r - 1.3, Eav - 0.05), (y0r + 0.3, Eav - 0.05), (y0r + 0.3, Eav - 0.9)])
        for j in range(int((y1r - y0r) / 1.0) + 1):               # and round both ends
            y = y0r + j * 1.0
            K.prism_y("trim", y - 0.1, y + 0.1, [(x1r + 1.3, Eav - 0.05), (x1r - 0.3, Eav - 0.05), (x1r - 0.3, Eav - 0.9)])
            K.prism_y("trim", y - 0.1, y + 0.1, [(x0r - 1.3, Eav - 0.05), (x0r + 0.3, Eav - 0.9), (x0r + 0.3, Eav - 0.05)])
    yc = (y0r + y1r) / 2
    hip = min((y1r - y0r) / 2 + 1.4, (x1r - x0r) / 2 + 1.4)
    for x in (x0r - 1.4 + hip + 1.0, (x0r + x1r) / 2, x1r + 1.4 - hip - 1.0):
        z = Eav + rise
        K.box("trim", x - 0.9, x + 0.9, yc - 0.9, yc + 0.9, z - 0.6, z + 1.2)
        for f in (-0.9, 0.9):                                     # louvres
            for j in range(4):
                K.box("shade", x - 0.7, x + 0.7, yc + f - 0.04, yc + f + 0.04, z - 0.2 + j * 0.32, z - 0.05 + j * 0.32)
        K.box("trim", x - 1.1, x + 1.1, yc - 1.1, yc + 1.1, z + 1.2, z + 1.4)
        K.sphere("slate", x, yc, z + 1.45, 1.0, 2, 0.8)
        K.cyl("trim", x, yc, z + 2.1, z + 2.5, 0.12, 0.08, 6)
        K.sphere("trim", x, yc, z + 2.65, 0.18, 1)
    return {"width": round(L + 3.0 if terrace else L + 0.8, 2), "depth": round(yB + 1.8, 2), "height": round(Eav + rise + 2.85, 2),
            "section": {"platform": round(base, 2), "arches": zi, "lowerStand": A, "upperStand": U, "eaves": Eav,
                        "ridge": round(Eav + rise, 2), "columns": round(yp, 2), "back": round(yB, 2)}}


def tiered_with_terrace():
    """The tiered grandstand with its terrace (owner, 17 Nov: "terrace back in"), set back so the terrace's foot is the
    piece's front line, as the other stands' steps are."""
    K.push(Matrix.Translation((0.0, 9.8, 0.0)))
    info = tiered_stand(terrace=True)
    K.pop()
    info["depth"] = round(info["depth"] + 9.8, 2)
    return info


# ------------------------------------------------------------------------------------------ 2c: the colonnade stands
# Owner, 17 Nov: "two new stands to make in similar vein" (two concept images, white clay renders). Both stand on a wide
# flight of steps up to a colonnade of square piers carrying a flat beam; over it a stone balustrade with pedestals and
# ball finials at the front of open seating rising to a line of bracketed columns; at each end a flank wall following
# the section (owner: "the correct flank wall", not towers), the pediment on the left flank's top; (was: a solid panelled end block at the
# left with a small pediment and roundel on top and a flag; stairs with raking balustrades up the ends; aisles through
# the seating. park_balcony_stand (the first): two covered galleries, a flat roof behind a deep bracketed cornice and a
# rooftop balustrade. park_roof_terrace_stand (the second): one tall covered gallery, its roof a stepped terrace of
# seats rising to a parapet at the back, the ends' flank walls following the slope.
def stone_rail(x0, x1, y, z, peds=(), h=1.1, ball=True):
    """A stone balustrade: square balusters, a broad coping, pedestals at peds (x), each with a ball finial."""
    K.balustrade(x0, x1, y, z, h=h, mat="trim", spacing=0.3, piers=False)
    K.box("trim", x0, x1, y - 0.22, y + 0.22, z + h - 0.08, z + h + 0.06)
    K.box("quoin", x0, x1, y - 0.2, y + 0.2, z, z + 0.14)
    for x in peds:
        K.box("trim", x - 0.32, x + 0.32, y - 0.32, y + 0.32, z, z + h + 0.25)
        K.box("trim", x - 0.38, x + 0.38, y - 0.38, y + 0.38, z + h + 0.25, z + h + 0.37)
        if ball:
            K.cyl("trim", x, y, z + h + 0.37, z + h + 0.55, 0.12, 0.08, 8)
            K.sphere("trim", x, y, z + h + 0.78, 0.26, 2)


def raking_rail(x, ya, za, yb, zb, solid=True, xw=0.3):
    """A raking balustrade along y at x, from (ya, za) up to (yb, zb): a solid flank wall under it (the triangle down to
    the lower end's level), balusters, a sloping coping, newels with balls at both ends."""
    x0, x1 = x - xw / 2, x + xw / 2
    if solid:
        K.prism_x("quoin", x0, x1, [(ya, min(za, zb) - 0.6), (yb, min(za, zb) - 0.6), (yb, zb), (ya, za)])
    K.prism_x("trim", x0 - 0.08, x1 + 0.08, [(ya, za + 1.0), (yb, zb + 1.0), (yb, zb + 1.14), (ya, za + 1.14)])
    if not K.far:
        n = max(3, int(math.hypot(yb - ya, zb - za) / 0.32))
        for j in range(n):
            f = (j + 0.5) / n
            y = ya + (yb - ya) * f; z = za + (zb - za) * f
            K.box("trim", x - 0.05, x + 0.05, y - 0.05, y + 0.05, z, z + 1.0)
    for y, z in ((ya, za), (yb, zb)):
        K.box("trim", x - 0.32, x + 0.32, y - 0.32, y + 0.32, z, z + 1.4)
        K.sphere("trim", x, y, z + 1.68, 0.25, 2)


def bracket_column(x, y, z0, z1, xmin=-1e9, xmax=1e9, r=0.17):
    """A turned column with base, bell capital and abacus, and curved brackets either side under the beam."""
    K.box("trim", x - 0.32, x + 0.32, y - 0.32, y + 0.32, z0, z0 + 0.45)
    K.cyl("trim", x, y, z0 + 0.45, z1 - 0.55, r + 0.03, r, 10)
    K.cyl("trim", x, y, z1 - 0.55, z1 - 0.3, r + 0.03, r + 0.14, 10)
    K.box("trim", x - 0.32, x + 0.32, y - 0.32, y + 0.32, z1 - 0.3, z1)
    if K.far:
        return
    R = 0.95
    for s_ in (-1, 1):
        if not (xmin - 0.01 <= x + s_ * (R + r) <= xmax + 0.01):
            continue
        cxr = x + s_ * (R + r)
        a0, a1 = (math.pi / 2, math.pi) if s_ > 0 else (0.0, math.pi / 2)
        K.arc_band("trim", cxr, z1 - R, R - 0.12, R, a0, a1, y - 0.07, y + 0.07, 8)
        K.arc_band("trim", cxr, z1 - R, R * 0.45, R * 0.55, a0, a1, y - 0.05, y + 0.05, 6)


def seating(x0, x1, ya, yb, z0, rows, rise, aisles=()):
    """Raked seating from ya (front, z0) back to yb: the stepped mass, a bench on every row, gaps at the aisles, where
    smaller steps climb at half the rise; its crowd."""
    tr = (yb - ya) / rows
    prof = [(ya, z0 - 0.6), (ya, z0)]
    for j in range(rows):
        prof += [(ya + j * tr, z0 + j * rise), (ya + (j + 1) * tr, z0 + j * rise)]
    prof += [(yb, z0 - 0.6)]
    K.prism_x("steps", x0, x1, prof)
    cuts = sorted([x0] + [a for c in aisles for a in (c - 0.6, c + 0.6)] + [x1])
    segs = [(cuts[i], cuts[i + 1]) for i in range(0, len(cuts), 2)]
    for j in range(rows):
        y1 = ya + (j + 1) * tr; z = z0 + j * rise
        for a, b in segs:
            if b - a > 0.8:
                K.box("seat", a + 0.15, b - 0.15, y1 - 0.42, y1 - 0.12, z, z + 0.42)
                rarea(a + 0.2, b - 0.2, ya + j * tr + 0.05, y1 - 0.45, z)
    for c in aisles:                                               # the aisles' half steps
        for j in range(rows):
            for k_ in (0, 1):
                ys = ya + j * tr + k_ * tr / 2
                K.box("quoin", c - 0.55, c + 0.55, ys, ys + tr / 2, z0 + j * rise - 0.5, z0 + j * rise + (k_ - 0.5) * rise * (1 if j else 0) + (rise / 2 if k_ else 0.0) - (0 if j else rise / 2) * 0)
    return z0 + (rows - 1) * rise, tr


def end_block(x0, x1, y0, y1, ztop, bands):
    """A solid panelled end block: plinth, string courses at bands, pilasters at the corners and the third points, sunk
    panels between, a cornice."""
    K.box("wall", x0, x1, y0, y1, -1.0, ztop)
    K.box("podium", x0 - 0.15, x1 + 0.15, y0 - 0.15, y1 + 0.15, -1.0, 0.8)
    for z in bands:
        K.box("podium", x0 - 0.12, x1 + 0.12, y0 - 0.12, y1 + 0.12, z - 0.18, z + 0.18)
    K.box("podium", x0 - 0.35, x1 + 0.35, y0 - 0.35, y1 + 0.35, ztop - 0.4, ztop)
    zs = [0.8] + list(bands) + [ztop - 0.4]
    for (za, zb) in zip(zs[:-1], zs[1:]):                          # panels on the front and the outer side
        w = x1 - x0
        for k in range(2):
            a, b = x0 + 0.5 + k * (w - 1.0) / 2 + 0.2, x0 + 0.5 + (k + 1) * (w - 1.0) / 2 - 0.2
            K.box("quoin", a, b, y0 - 0.08, y0, za + 0.35, zb - 0.35)
            K.box("wall", a + 0.15, b - 0.15, y0 - 0.1, y0 - 0.08, za + 0.5, zb - 0.5)
    for x in (x0 + 0.2, x1 - 0.2):
        K.box("quoin", x - 0.25, x + 0.25, y0 - 0.25, y0, 0.8, ztop - 0.4)
    d = y1 - y0                                                   # panels down the outer side too, in three
    for (za, zb) in zip(zs[:-1], zs[1:]):
        for k in range(3):
            a, b = y0 + 0.5 + k * (d - 1.0) / 3 + 0.25, y0 + 0.5 + (k + 1) * (d - 1.0) / 3 - 0.25
            K.box("quoin", x0 - 0.08, x0, a, b, za + 0.35, zb - 0.35)
            K.box("wall", x0 - 0.1, x0 - 0.08, a + 0.15, b - 0.15, za + 0.5, zb - 0.5)
    for y in [y0 + 0.5 + k * (d - 1.0) / 3 for k in range(4)]:
        K.box("quoin", x0 - 0.25, x0, y - 0.25, y + 0.25, 0.8, ztop - 0.4)


def aedicule(x, y, z, flagmat="trim"):
    """The little pedimented aedicule on the end block's top: pilasters, a pediment, a roundel, a flagpole and flag."""
    K.box("trim", x - 1.6, x + 1.6, y - 0.6, y + 1.6, z, z + 2.6)
    for s_ in (-1, 1):
        K.box("quoin", x + s_ * 1.45 - 0.2, x + s_ * 1.45 + 0.2, y - 0.75, y - 0.55, z, z + 2.6)
    K.disc_y("quoin", x, y - 0.78, y - 0.6, z + 1.45, 0.62, 20)
    K.disc_y("shade", x, y - 0.82, y - 0.76, z + 1.45, 0.42, 20)
    K.prism_y("podium", y - 0.8, y + 1.7, [(x - 1.95, z + 2.6), (x + 1.95, z + 2.6), (x, z + 3.7)][::-1])
    K.cyl("trim", x, y + 0.5, z + 3.5, z + 8.5, 0.07, 0.05, 6)
    K.sphere("trim", x, y + 0.5, z + 8.6, 0.13, 1)
    K.box(flagmat, x + 0.07, x + 2.4, y + 0.47, y + 0.53, z + 7.0, z + 8.4)


def back_block(x0, x1, y0, depth, ztop, bay, storeys=None):
    """The back module (owner, 17 Nov, with a section sketch: "add a rectilinear module to the back that also creates a
    solid back to the grandstands"): a plain rectangular block behind the stand, the stand's full width, 'depth' deep,
    up to the stand's top, its floors marked. The rear face a grid: pilasters on the bay lines, a band at every floor,
    a window a bay a storey, doors at the ground every third bay; the ends the same; a plinth, a cornice and a low
    parapet."""
    y1 = y0 + depth
    n = storeys or max(2, int(round(ztop / 4.6)))
    fz = [ztop * k / n for k in range(n + 1)]
    K.box("wall", x0, x1, y0, y1, -1.0, ztop)
    K.box("podium", x0 - 0.12, x1 + 0.12, y0, y1 + 0.12, -1.0, 0.8)
    for z in fz[1:-1]:                                            # the floor bands round the rear and the ends
        K.box("podium", x0 - 0.1, x1 + 0.1, y0, y1 + 0.1, z - 0.15, z + 0.15)
    K.box("podium", x0 - 0.35, x1 + 0.35, y0, y1 + 0.35, ztop - 0.35, ztop)            # the cornice
    K.box("trim", x0 - 0.2, x1 + 0.2, y0, y1 + 0.2, ztop, ztop + 0.9)                  # the parapet
    K.box("podium", x0 - 0.3, x1 + 0.3, y0, y1 + 0.3, ztop + 0.9, ztop + 1.05)
    nb = max(1, int(round((x1 - x0) / bay)))
    for i in range(nb + 1):                                       # the grid on the rear face
        x = x0 + (x1 - x0) * i / nb
        K.box("quoin", x - 0.28, x + 0.28, y1, y1 + 0.16, 0.8, ztop - 0.35)
    for i in range(nb):
        cx = x0 + (x1 - x0) * (i + 0.5) / nb
        for k in range(n):
            zb = fz[k] + (0.9 if k == 0 else 0.6)
            if k == 0 and i % 3 == 1:
                K.door(cx, y1, 0.0, 1.6, 2.7, d=1)
            else:
                K.window(cx, y1, zb, 1.2, min(2.2, fz[k + 1] - fz[k] - 1.4), d=1)
    for x, side in ((x0, -1), (x1, 1)):                           # the ends: pilasters and windows
        for y in (y0 + 0.3, y0 + depth / 2, y1 - 0.3):
            K.box("quoin", min(x, x + side * 0.16), max(x, x + side * 0.16), y - 0.28, y + 0.28, 0.8, ztop - 0.35)
        for k in range(n):
            for y in (y0 + depth * 0.27, y0 + depth * 0.73):
                side_window(x + side * 0.02, side, y, fz[k] + (0.9 if k == 0 else 0.6), 1.2, min(2.2, fz[k + 1] - fz[k] - 1.4))
    return y1


def colonnade_base(h, bay, P, Ctop, depth, pier_every=2.0 / 3.0):
    """Steps up to a platform at P, with balustraded cheeks at the ends; a colonnade of square piers (base, shaft, cap)
    carrying a beam to Ctop, a loggia 'depth' deep behind, in shade; returns the pier xs."""
    rows, tr = 7, 1.2
    rs = P / rows
    yS = -rows * tr                                               # the steps' foot (the piece's origin is set by the caller)
    prof = [(yS, -1.0)]
    for k in range(rows):
        prof += [(yS + k * tr, (k + 1) * rs), (yS + (k + 1) * tr, (k + 1) * rs)]
        rarea(-h - 1.5, h + 1.5, yS + k * tr + 0.1, yS + (k + 1) * tr - 0.1, k * rs)
    prof += [(0.0, P), (0.0, -1.0)]
    K.prism_x("steps", -h - 1.8, h + 1.8, prof)
    for xs_ in (-h - 1.8, h + 1.8):                               # the cheeks at both ends of the flight
        raking_rail(xs_, yS + 0.4, 0.2, 0.0, P, solid=True, xw=0.45)
    K.box("podium", -h, h, 0.0, depth + 0.4, -1.0, P)                             # the loggia's floor
    K.box("shade", -h, h, depth, depth + 0.4, P, Ctop - 0.9)                      # its back wall
    pb = bay * pier_every
    n = int(round(2 * h / pb))
    xs = [-h + 2 * h * i / n for i in range(n + 1)]
    for x in xs:
        K.box("quoin", x - 0.38, x + 0.38, 0.0, 0.76, P, Ctop - 0.9)
        K.box("podium", x - 0.5, x + 0.5, -0.12, 0.88, P, P + 0.5)
        K.box("podium", x - 0.48, x + 0.48, -0.1, 0.86, Ctop - 1.2, Ctop - 0.9)
    K.box("quoin", -h - 0.2, h + 0.2, -0.15, depth + 0.4, Ctop - 0.9, Ctop - 0.3)  # the beam
    K.box("podium", -h - 0.4, h + 0.4, -0.4, depth + 0.4, Ctop - 0.3, Ctop)       # its cornice
    K.box("shade", -h, h, 0.0, depth, Ctop - 0.92, Ctop - 0.9)                    # the loggia's ceiling
    rarea(-h + 0.5, h - 0.5, 1.2, depth - 0.4, P)
    return xs


def colonnade_stand(nb=10, bay=3.6, roof="flat"):
    """The two colonnade stands (see above). roof="flat": park_balcony_stand; roof="terrace": park_roof_terrace_stand.
    Origin: the middle of the steps' foot on the ground (the steps 8.4 m deep before the colonnade)."""
    L = nb * bay; h = L / 2
    K.push(Matrix.Translation((0.0, 8.4, 0.0)))
    P, C = 1.4, 5.6                                               # the platform; the colonnade's beam top
    yc = 6.0                                                      # the gallery columns' line, back from the colonnade front
    yB = yc + 9.5                                                 # the back wall
    aisles = [-h + bay * 2.5, 0.0, h - bay * 2.5]
    colonnade_base(h, bay, P, C, 3.2)
    K.box("wall", -h, h, 3.6, yB + 0.4, -1.0, C - 0.3)            # the mass under the seating
    # the front balustrade on the colonnade, pedestals every two and a half bays, a ball on each
    peds = [-h + 0.35, -h + bay * 2.5, -0.0, h - bay * 2.5, h - 0.35]
    stone_rail(-h, h, 0.05, C, peds)
    # the open seating, up to the columns
    zc, tr = seating(-h + 1.9, h - 1.9, 0.8, yc, C, 6, 0.42, aisles)
    zc += 0.42                                                    # the columns stand on the top row's level
    K.box("steps", -h, h, yc, yc + 0.6, C, zc)
    if roof == "flat":
        U, E = zc + 5.4, zc + 5.4 + 5.0                           # the upper gallery's floor; the eaves (the beam's foot)
        z1, _ = seating(-h + 1.9, h - 1.9, yc + 0.6, yB - 1.2, zc, 7, 0.36, aisles)
        z2, _ = seating(-h + 1.9, h - 1.9, yc + 0.6, yB - 1.2, U, 7, 0.32, aisles)
        K.box("quoin", -h - 0.3, h + 0.3, yc - 0.6, yB, U - 1.0, U)                  # the upper floor's edge
        K.box("podium", -h - 0.4, h + 0.4, yc - 0.7, yc - 0.4, U - 1.0, U - 0.8)
        K.box("shade", -h, h, yc, yB, U - 1.05, U - 1.0)
        stone_rail(-h, h, yc - 0.3, U, [-h + bay * i for i in range(0, nb + 1, 2)], h=1.05, ball=False)
        for i in range(nb + 1):
            x = -h + bay * i
            bracket_column(x, yc, zc, U - 1.0, -h, h)
            bracket_column(x, yc, U, E, -h, h)
        # the entablature: a frieze, modillions under a deep cornice, a dentil course; the rooftop balustrade
        K.box("quoin", -h - 0.3, h + 0.3, yc - 0.5, yB + 0.4, E, E + 1.1)
        K.box("podium", -h - 0.4, h + 0.4, yc - 0.62, yB + 0.4, E + 0.12, E + 0.32)
        if not K.far:
            for j in range(int((L + 0.8) / 0.45)):
                x = -h - 0.35 + j * 0.45
                K.box("trim", x - 0.1, x + 0.1, yc - 0.75, yc - 0.5, E + 0.45, E + 0.65)  # dentils
            for j in range(int((L + 1.6) / 1.2) + 1):
                x = -h - 0.7 + j * 1.2
                K.prism_x("trim", x - 0.14, x + 0.14, [(yc - 1.3, E + 1.1), (yc - 0.5, E + 1.1), (yc - 0.5, E + 0.75)])   # modillions
        K.box("podium", -h - 0.8, h + 0.8, yc - 1.4, yB + 0.8, E + 1.1, E + 1.45)
        K.box("trim", -h - 0.5, h + 0.5, yc - 1.0, yB + 0.4, E + 1.45, E + 1.7)
        stone_rail(-h - 0.3, h + 0.3, yc - 0.85, E + 1.7, [-h - 0.3 + (L + 0.6) * i / nb for i in range(nb + 1)])
        K.box("shade", -h, h, yc, yB, E - 0.05, E)                                    # the gallery ceiling
        top, flank = E + 1.7, None
        back_top = E + 1.1
    else:
        E = zc + 7.4                                               # one tall gallery; its roof the terrace
        z1, _ = seating(-h + 1.9, h - 1.9, yc + 0.6, yB - 1.2, zc, 8, 0.4, aisles)
        for i in range(nb + 1):
            bracket_column(-h + bay * i, yc, zc, E, -h, h)
        K.box("quoin", -h - 0.3, h + 0.3, yc - 0.6, yc + 0.6, E, E + 0.9)             # the beam over the columns
        K.box("podium", -h - 0.45, h + 0.45, yc - 0.75, yc + 0.6, E + 0.9, E + 1.15)
        rows, rise = 14, 0.4                                       # the roof terrace: seats rising to the back
        zr0 = E + 1.15
        prof = [(yc - 0.45, E + 0.02), (yc - 0.45, zr0)]           # set just inside the beam's face (no shared plane)
        trr = (yB + 0.4 - yc + 0.6) / rows
        for j in range(rows):
            prof += [(yc - 0.6 + j * trr, zr0 + j * rise), (yc - 0.6 + (j + 1) * trr, zr0 + j * rise)]
        prof += [(yB + 0.4, E + 0.02)]
        K.prism_x("steps", -h + 0.01, h - 0.01, prof)
        K.box("canopy_under", -h, h, yc + 0.6, yB, E - 0.05, E)
        for j in range(rows):
            y1 = yc - 0.6 + (j + 1) * trr; z = zr0 + j * rise
            for a, b in ((-h + 0.4, aisles[0] - 0.6), (aisles[0] + 0.6, aisles[1] - 0.6), (aisles[1] + 0.6, aisles[2] - 0.6), (aisles[2] + 0.6, h - 0.4)):
                K.box("seat", a, b, y1 - 0.38, y1 - 0.1, z, z + 0.4)
                rarea(a + 0.1, b - 0.1, y1 - trr + 0.05, y1 - 0.42, z)
        for c in aisles:                                           # the roof aisles: half steps
            for j in range(rows):
                ys = yc - 0.6 + j * trr
                K.box("quoin", c - 0.55, c + 0.55, ys + trr / 2, ys + trr, zr0 + j * rise - 0.4, zr0 + j * rise + rise / 2)
        zt = zr0 + (rows - 1) * rise                               # the back parapet with pedestals and balls
        K.box("trim", -h - 0.3, h + 0.3, yB + 0.4, yB + 0.9, E, zt + 1.4)
        K.box("podium", -h - 0.4, h + 0.4, yB + 0.3, yB + 1.0, zt + 1.4, zt + 1.62)
        for i in range(0, nb + 1):
            x = -h + bay * i
            K.box("trim", x - 0.32, x + 0.32, yB + 0.33, yB + 0.97, zt + 1.62, zt + 2.3)
            K.sphere("trim", x, yB + 0.65, zt + 2.58, 0.26, 2)
        K.box("trim", -h - 0.2, h + 0.2, yc - 0.55, yc - 0.35, zr0, zr0 + 1.0)        # a low rail at the roof's front edge
        top, back_top = zt + 1.62, zt + 1.4
    # ---- the ends (owner: "the correct flank wall", not towers): at each end, in the plane of the end, a flank wall
    # following the section. Over the open seating, a stair beside the end and a triangular flank under its raking
    # balustrade; from the gallery columns back, a solid panelled flank: flat-topped at the roof on the balcony stand,
    # following the roof terrace's slope on the other; the colonnade's end wall below.
    if roof == "flat":
        fl = [(yc - 0.6, C - 0.3), (yB + 0.4, C - 0.3), (yB + 0.4, E + 1.1), (yc - 0.6, E + 1.1)]
        cope = None
        ftop = lambda y: E + 1.1
    else:
        fl = [(yc - 0.6, C - 0.3), (yB + 0.9, C - 0.3), (yB + 0.9, zt + 1.4), (yc - 0.6, zr0 + 1.0)]
        cope = [(yc - 0.6, zr0 + 1.0), (yB + 0.9, zt + 1.4), (yB + 0.9, zt + 1.62), (yc - 0.6, zr0 + 1.22)]
        ftop = lambda y: zr0 + 1.0 + (zt + 0.4 - zr0) * (y - yc + 0.6) / (yB + 1.5 - yc)
    for side in (-1, 1):
        xo = side * h                                             # the end's plane
        xa, xb = sorted((xo, xo + side * 0.45))
        xf = xo + side * 0.45                                     # the outer face
        K.box("wall", xa, xb, -0.15, yB + (0.45 if roof == "flat" else 0.95), -1.0, C - 0.3)   # the colonnade's end wall, to the back module
        K.box("podium", min(xf, xf + side * 0.12), max(xf, xf + side * 0.12), -0.3, yB + 0.55, -1.0, 0.8)
        K.box("podium", min(xf, xf + side * 0.15), max(xf, xf + side * 0.15), -0.4, yB + 0.55, C - 0.9, C - 0.3)
        raking_rail(xo - side * 0.9, 0.6, C, yc - 0.6, zc, solid=True, xw=0.4)       # the stair's balustrade
        sa, sb = sorted((xo - side * 1.8, xo - side * 1.1))
        K.prism_x("steps", sa, sb, [(0.6, C), (yc - 0.6, zc), (yc - 0.6, C)])
        K.prism_x("wall", xa, xb, [(0.0, C - 0.3), (yc - 0.6, C - 0.3), (yc - 0.6, zc + 1.0), (0.6, C + 1.0)])   # the triangular flank
        K.prism_x("podium", xa - 0.05, xb + 0.05, [(0.0, C + 1.0), (yc - 0.6, zc + 1.0), (yc - 0.6, zc + 1.2), (0.0, C + 1.2)])
        K.prism_x("wall", xa, xb, fl)                             # the solid flank behind the columns
        K.box("wall", xa, xb, yB + 0.3, yB + (0.45 if roof == "flat" else 0.95), C - 0.4, fl[2][1])   # closing on the back module
        if cope:
            K.prism_x("podium", xa - 0.05, xb + 0.05, cope)
        # its panels and pilasters on the outer face, the bands at the floors
        ys = [yc - 0.6 + (yB + 0.4 - yc + 0.6) * k / 3 for k in range(4)]
        bands = [C - 0.3, zc + 2.5] + ([E - 2.5] if roof == "flat" else [])
        for y in ys:
            K.box("quoin", min(xf, xf + side * 0.15), max(xf, xf + side * 0.15), y - 0.25, y + 0.25, C - 0.3, ftop(y) - 0.2)
        for z in bands[1:]:                                       # proud of the pilasters, so no shared faces
            K.box("podium", min(xf, xf + side * 0.2), max(xf, xf + side * 0.2), yc - 0.6, yB + 0.4, z - 0.15, z + 0.15)
        for (ya_, yb_) in zip(ys[:-1], ys[1:]):
            lo = C - 0.3
            for hi in bands[1:] + [min(ftop(ya_), ftop(yb_)) - 0.4]:
                if hi - lo > 1.6:
                    K.box("quoin", min(xf, xf + side * 0.08), max(xf, xf + side * 0.08), ya_ + 0.6, yb_ - 0.6, lo + 0.5, hi - 0.5)
                    K.box("wall", min(xf + side * 0.08, xf + side * 0.1), max(xf + side * 0.08, xf + side * 0.1), ya_ + 0.75, yb_ - 0.75, lo + 0.65, hi - 0.65)
                lo = hi
    # the pediment on the left flank's top (as the concepts), a flag on it and another at the right
    if roof == "flat":
        ax, ay, az = -h + 1.6, yc - 0.3, E + 1.7
    else:
        ax, ay, az = -h + 1.6, yB - 1.6, zt + 1.62
    aedicule(ax, ay, az)
    fx, fz = (h - 0.3, top) if roof == "flat" else (h + 0.2, back_top + 0.2)
    fy = (yc - 0.85) if roof == "flat" else (yB + 0.65)
    K.cyl("trim", fx, fy, fz, fz + 6.5, 0.07, 0.05, 6)
    K.box("trim", fx + 0.07, fx + 2.4, fy - 0.03, fy + 0.03, fz + 5.0, fz + 6.4)
    ztop = az + 8.6
    # the back module: a rectilinear block behind, full width, up to the stand's top (owner's section sketch)
    BD = 7.0
    yb0 = yB + (0.4 if roof == "flat" else 0.9)                   # against the back wall, or just behind the back parapet
    btop = (E + 1.45) if roof == "flat" else (zt + 1.4)
    back_block(-h - 0.45, h + 0.45, yb0, BD, btop, bay)
    K.pop()
    return {"width": round(L + 3.6, 2), "depth": round(8.4 + yb0 + BD + 0.4, 2), "height": round(ztop, 2),
            "section": {"platform": P, "colonnadeTop": C, "columns": round(8.4 + yc, 2), "coveredSeatingFront": round(zc, 2),
                        "eaves": round(E, 2), "back": round(8.4 + yB, 2), "backBlock": [round(8.4 + yb0, 2), round(8.4 + yb0 + BD, 2), round(btop, 2)]},
            }


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
    ("park_old_pavilion", old_pavilion),
    ("park_tiered_stand", tiered_with_terrace),
    ("park_balcony_stand", lambda: colonnade_stand(10, 3.6, "flat")),
    ("park_roof_terrace_stand", lambda: colonnade_stand(10, 3.6, "terrace")),
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
    groups = [["park_glass_box_small", "park_old_pavilion", "park_glass_box"], ["park_arch_stand"],
              ["park_gable_stand", "park_stair_tower", "park_terrace", "park_link"], ["park_clock_house", "park_shed", "park_floodlight"], ["park_old_pavilion"], ["park_tiered_stand"],
              ["park_balcony_stand", "park_roof_terrace_stand"]]
    scene = setup_scene(1800, 900)
    lawn(0, 0, 4000)
    x = 0.0
    spans = []
    for g in groups:
        x0 = x
        for name in g:
            w = INFO[name]["width"]
            OBJ[name].location = (x + w / 2 - INFO[name].get("offset", 0.0), 0, 0)
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
        put(p["piece"], p["x"] - INFO[p["piece"]].get("offset", 0.0), -p["z"], 0.0, p.get("stretch"))
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
    shoot(scene, "park-members-group", (-20, -95, 16), (-5, 50, 9), lens=30)
    tx = [p for p in LAY["stands"]["chain"] if p["piece"] == "park_tiered_stand"][0]["x"]
    shoot(scene, "park-tiered-stand", (tx - 30, -70, 12), (tx, 50, 8), lens=30)
    shoot(scene, "park-festival-from-stands", (60, 70, 26), (90, -110, 6), lens=30)
    shoot(scene, "park-stands-aerial", (-120, -170, 120), (90, 40, 0), lens=32)
