"""Epsom's grandstand (phase 4), and the two fairground rides for the Hill.

    python3.11 -c "exec(open('tools/blender/build_epsom_stands.py').read())"
    SHEET=1 python3.11 -c "exec(...)"       # also render it: reference/epsom/renders/grandstand-front.jpg, -three-quarter.jpg

Owner, 18 Nov 2026, 10:42, with his white clay model of the stand and old photos of Epsom's Victorian grandstand:
"Here is the Epsom grandstand which we should make which I think we can combine with the Victorian/rowley stand and the
balcony stand maybe to create this kind of big grandstand effect." And for the Hill: "use our festival component to
occupy the hill and maybe we add a ferris wheel and a heater shelter" (a helter skelter, as in his photo of the Hill).

His model, left to right as seen from the track (left = the post end, as the real Queen's Stand; right = up the course,
as the Duchess's Stand):
  the west section  a lower stand: a tall colonnade over the terrace, two open balcony galleries on bracketed columns,
                    a balustraded roof with a cupola (an octagonal lantern, its flared roof and a spire); at its left
                    end a one-gallery wing
  the main block    the tall stand: a colonnade at the terrace top, three open balcony galleries, three glazed storeys
                    each set back behind a balustraded terrace, and on the top a raked roof stand of seats (the old
                    Epsom grandstand's famous roof crowd, his photos), a balustrade round its top and a flag
  the terrace       standing steps the whole length, from a balustraded walk along the front, with stair aisles; the
                    west section's aisles between balustraded cheeks
The pieces come from the kit: the balcony stand's bracketed columns, stone balustrades, raked seating, flank walls and
back block (build_park_stands.py), the Rowley Mile's cupola and lantern manner (build_rowley_stands.py). His model's
right-hand end is a tall block; that is left out by his standing rule (17 Nov: "We want just a flank wall that aligns to
the rake of the terraces"): both ends are flank walls on the rake, the building's own end above.

  epsom_grandstand     146 x 48 m, 53 m to the flag
  epsom_ferris_wheel   an observation wheel: two A-frames, the rim, spokes and sixteen pastel gondolas   34 m
  epsom_helter_skelter the striped tower, its spiral slide, a pointed roof and a flag                        15 m

Writes assets/models/architecture/epsom_stands.glb and .json (as the other kits: size and crowd areas per piece; origin
the middle of the front on the ground, front facing -y in Blender, +z in glTF).
"""
import json, math, os

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

# ---- the Park kit's definitions (which bring York's, the Rowley Mile's and the July Course's), without its build loop
_psrc = open(rp("tools/blender/build_park_stands.py")).read()
exec(_psrc[:_psrc.index("\nPIECES = [")])

EP = {"ride_red": "#e59c95", "ride_white": "#fbf7ef", "ride_blue": "#9fbad8", "ride_yellow": "#f1d38f", "ride_green": "#a9cfa6",
      "ride_steel": "#e9e6ef", "ride_dark": "#6b6f80"}
for k, v in EP.items():
    COL[k] = v
    MATS[k] = material("ep_" + k, v, rough=0.85)

# ---------------------------------------------------------------------------------------------------- the grandstand
X0, XW, XM, X1 = -73.0, -58.0, -23.0, 73.0       # the far left; the wing's end; the main block's left end; the right end
YT = 18.0                                         # the terrace's top (20 rows of 0.9 m)
YC = 19.0                                         # the columns' line, at the terrace's top walk
GD = 5.0                                          # the galleries' depth, to their glazed backs
ZP = 8.3                                          # the walk along the terrace top
Z1, Z2, Z3, Z4 = 12.3, 16.1, 19.9, 23.7           # the main block's gallery floors and its third gallery's roof
Z5, Z6, Z7 = 27.4, 31.1, 34.8                     # the glazed storeys' tops
ZL1, ZL2, ZL3 = 14.6, 18.4, 22.2                  # the west section's gallery floors and roof
YS1, YS2, YS3 = YC + 3.0, YC + 5.5, YC + 8.0      # the glazed storeys' fronts, each set back
S1X, S3X = (-29.0, X1), (-21.0, 50.0)             # the glazed storeys' spans (the first two run on over the west section)
RSX = (-19.0, 46.0)                               # the roof stand
RROWS, RRISE, RTREAD = 12, 0.8, 1.1
YR0 = YS3 + 1.4                                   # the roof stand's front row
YR1 = YR0 + RROWS * RTREAD
YB = YR1 + 1.0                                    # the main block's back line, before its back block
YBW = YC + 14.0                                   # the west section's back line
CUP = (-39.4, YC + 7.5)                           # the cupola


def gallery(x0, x1, zf, znext, bay, rows=3, rail=True):
    """An open balcony gallery from x0 to x1: its floor slab at zf with a moulded edge, a balustrade along the front,
    bracketed columns to the slab above (at znext), rows of seats stepping back to a glazed back, a shaded ceiling."""
    K.box("quoin", x0 - 0.3, x1 + 0.3, YC - 0.6, YC + GD + 0.1, zf - 0.5, zf)
    K.box("podium", x0 - 0.42, x1 + 0.42, YC - 0.72, YC - 0.45, zf - 0.5, zf - 0.28)
    if rail:
        n = max(1, round((x1 - x0) / bay))
        stone_rail(x0, x1, YC - 0.3, zf, [x0 + (x1 - x0) * i / n for i in range(n + 1)], h=1.05, ball=False)
        rarea(x0 + 0.4, x1 - 0.4, YC - 0.05, YC + 0.5, zf)
    seating(x0 + 0.4, x1 - 0.4, YC + 0.6, YC + GD - 0.3, zf, rows, 0.32)
    n = max(1, round((x1 - x0) / bay))
    for i in range(n + 1):
        bracket_column(x0 + (x1 - x0) * i / n, YC, zf, znext - 0.5, x0, x1)
    K.box("shade", x0, x1, YC + 0.3, YC + GD, znext - 0.56, znext - 0.5)
    K.screen(x0 + 0.2, x1 - 0.2, YC + GD, zf, znext - 0.6 - zf)


def colonnade(x0, x1, ztop, bay):
    """The colonnade along the terrace top: bracketed columns from the walk to the first gallery's slab, a shaded
    concourse behind them with doors into the stand."""
    n = max(1, round((x1 - x0) / bay))
    for i in range(n + 1):
        bracket_column(x0 + (x1 - x0) * i / n, YC, ZP, ztop - 0.5, x0, x1)
    K.box("shade", x0, x1, YC + 4.0, YC + 4.3, ZP, ztop - 0.5)
    K.box("shade", x0, x1, YC + 0.3, YC + 4.0, ztop - 0.56, ztop - 0.5)
    for k in range(int((x1 - x0) // 6.0)):
        K.door(x0 + 3.0 + k * 6.0, YC + 4.0, ZP, 1.6, 2.6)
    rarea(x0 + 0.5, x1 - 0.5, YT + 0.2, YC + 3.6, ZP)


def roof_slab(x0, x1, ya, yb, z, rail_y, peds_every=None, ball=True):
    """A flat roof (a terrace people stand on): the slab, a cornice along its front, a stone balustrade."""
    K.box("quoin", x0 - 0.3, x1 + 0.3, ya, yb, z - 0.5, z)
    K.box("podium", x0 - 0.45, x1 + 0.45, ya - 0.15, ya + 0.3, z - 0.75, z - 0.45)
    n = max(1, round((x1 - x0) / (peds_every or 7.2)))
    stone_rail(x0, x1, rail_y, z, [x0 + (x1 - x0) * i / n for i in range(n + 1)], h=1.05, ball=ball)


def storey(x0, x1, yf, zb, zt, bay=3.6):
    """A glazed storey: a full-height window wall with white mullions on its front, the block behind it."""
    K.box("wall", x0, x1, yf + 0.12, YB, zb, zt - 0.5)
    K.screen(x0 + 0.1, x1 - 0.1, yf, zb, zt - 0.6 - zb, pane=bay / 2)
    for i in range(int(round((x1 - x0) / bay)) + 1):                  # white piers between the windows
        x = x0 + (x1 - x0) * i / int(round((x1 - x0) / bay))
        K.box("trim", x - 0.22, x + 0.22, yf - 0.16, yf + 0.1, zb, zt - 0.5)


def cupola(cx, cy, z0):
    """The west section's cupola (his model): a square base with pilasters, windows and a balustrade; an octagonal
    lantern with louvred openings and columns at its corners; a flared octagonal roof, a ball and a spire."""
    b = 4.6
    K.box("wall", cx - b, cx + b, cy - b, cy + b, z0, z0 + 3.4)
    K.box("podium", cx - b - 0.2, cx + b + 0.2, cy - b - 0.2, cy + b + 0.2, z0 + 3.4, z0 + 3.8)
    for s in (-1, 1):
        for t in (-1, 1):
            K.box("quoin", cx + s * b - 0.35, cx + s * b + 0.35, cy + t * b - 0.35, cy + t * b + 0.35, z0, z0 + 3.4)
    for x in (cx - 2.4, cx, cx + 2.4):
        K.window(x, cy - b, z0 + 0.8, 1.1, 1.8, panes=False)
    K.balustrade(cx - b, cx + b, cy - b + 0.2, z0 + 3.8, h=0.9, mat="trim", spacing=0.3)
    zl, R = z0 + 3.8, 2.9
    K.cyl("wall", cx, cy, zl, zl + 4.2, R, segs=8, smooth=False)
    for i in range(8):                                                # louvres in each face, a column at each corner
        a = math.pi / 8 + i * math.pi / 4
        K.push(Matrix.Translation((cx, cy, 0)) @ Matrix.Rotation(a - math.pi / 2, 4, "Z"))
        K.box("shade", -0.7, 0.7, -R * math.cos(math.pi / 8) - 0.06, -R * math.cos(math.pi / 8) + 0.2, zl + 0.7, zl + 3.4)
        if not K.far:
            for j in range(5):
                z = zl + 0.95 + j * 0.5
                K.box("trim", -0.7, 0.7, -R * math.cos(math.pi / 8) - 0.14, -R * math.cos(math.pi / 8) - 0.04, z, z + 0.12)
        K.pop()
        ca = a + math.pi / 8
        K.cyl("trim", cx + (R + 0.1) * math.cos(ca), cy + (R + 0.1) * math.sin(ca), zl, zl + 4.2, 0.2, segs=8)
    K.cyl("podium", cx, cy, zl + 4.2, zl + 4.6, R + 0.5, segs=8, smooth=False)
    K.cyl("slate", cx, cy, zl + 4.6, zl + 5.4, R + 0.7, R + 0.1, segs=8, smooth=False)        # the flared roof
    K.cyl("slate", cx, cy, zl + 5.4, zl + 9.0, R + 0.1, 0.25, segs=8, smooth=False)
    K.sphere("gilt", cx, cy, zl + 9.3, 0.4, sub=1)
    K.cyl("trim", cx, cy, zl + 9.6, zl + 16.0, 0.09, 0.03, segs=6)
    return zl + 16.0


def epsom_grandstand():
    # ---- the front: a walk along a stone balustrade, the standing terrace the whole length, aisles
    K.box("steps", X0 - 0.4, X1 + 0.4, -3.0, 0.0, -1.0, 0.15)
    n = int(round((X1 - X0) / 4.0))
    stone_rail(X0, X1, -2.7, 0.15, [X0 + (X1 - X0) * i / n for i in range(n + 1)], h=1.0)
    rarea(X0 + 0.5, X1 - 0.5, -2.3, -0.3, 0.15)
    aisles = [-63.0, -48.5, -36.0, 0.0, 30.0, 57.0]
    zt, _ = plain_terrace(X0, X1, 0.0, YT, 0.3, 20, 0.4, aisles)
    for c in aisles[:3]:                                              # the west section's aisles between balustraded cheeks
        for s in (-1, 1):
            raking_rail(c + s * 0.95, 0.4, 0.3, YT - 0.2, zt, solid=True, xw=0.35)
    K.box("podium", X0, X1, YT, YC + 4.3, -1.0, ZP)                   # the walk along the terrace top
    # ---- the west section: a tall colonnade, two galleries (one at the wing), a balustraded roof, the cupola
    colonnade(X0, XM, ZL1, 3.6)
    gallery(X0, XM, ZL1, ZL2, 3.6)
    gallery(XW, XM, ZL2, ZL3, 3.6)
    K.box("wall", X0, XM, YC + GD + 0.1, YBW, ZP, ZL2 - 0.5)
    K.box("wall", XW, XM, YC + GD + 0.1, YBW, ZL2 - 0.5, ZL3 - 0.5)
    roof_slab(X0, XW, YC - 0.6, YBW, ZL2, YC - 0.3)
    roof_slab(XW, XM, YC - 0.6, YBW, ZL3, YC - 0.3)
    rarea(X0 + 0.5, XW - 0.5, YC, YC + 3.0, ZL2)
    rarea(XW + 0.5, CUP[0] - 6.0, YC, YC + 3.0, ZL3)
    rarea(CUP[0] + 6.0, XM - 7.0, YC, YC + 3.0, ZL3)
    top_cupola = cupola(CUP[0], CUP[1], ZL3)
    back_block(X0, XW, YBW, 4.0, ZL2, 3.6)
    back_block(XW, XM, YBW, 4.0, ZL3, 3.6)
    K.box("wall", XW - 0.4, XW, YC - 0.6, YBW, ZL2, ZL3 + 0.4)        # the step up from the wing: the gallery's end wall
    # ---- the main block: the colonnade, three galleries, three glazed storeys set back, the roof stand
    colonnade(XM, X1, Z1, 4.0)
    gallery(XM, X1, Z1, Z2, 4.0)
    gallery(XM, X1, Z2, Z3, 4.0)
    gallery(XM, X1, Z3, Z4, 4.0)
    K.box("wall", XM, X1, YC + GD + 0.1, YB, ZP, Z4 - 0.5)
    roof_slab(S1X[0], X1, YC - 0.6, YS1 + 0.1, Z4, YC - 0.3)          # the third gallery's roof, a terrace before the glass
    rarea(XM + 0.5, X1 - 0.5, YC, YS1 - 0.4, Z4)
    K.box("wall", S1X[0], XM, YS1, YB, ZL3, Z4 - 0.5)                 # where the glazed storeys run on over the west roof
    storey(S1X[0], S1X[1], YS1, Z4, Z5)
    roof_slab(S1X[0], S1X[1], YS1 - 0.4, YS2 + 0.1, Z5, YS1 - 0.1)
    rarea(S1X[0] + 0.5, S1X[1] - 0.5, YS1 + 0.2, YS2 - 0.4, Z5)
    storey(S1X[0], S1X[1], YS2, Z5, Z6)
    roof_slab(S1X[0], S1X[1], YS2 - 0.4, YB, Z6, YS2 - 0.1)
    rarea(S1X[0] + 0.5, S1X[1] - 0.5, YS2 + 0.2, YS3 - 0.4, Z6)
    rarea(S3X[1] + 0.8, S1X[1] - 0.5, YS3, YB - 1.0, Z6)              # the roof terrace right of the top storey
    storey(S3X[0], S3X[1], YS3, Z6, Z7)
    roof_slab(S3X[0], S3X[1], YS3 - 0.4, YB, Z7, YS3 - 0.1)
    for x, s in ((S3X[0], -1), (S3X[1], 1)):
        K.box("wall", min(x, x + s * 0.4), max(x, x + s * 0.4), YS3, YB, Z6, Z7 - 0.5)
    rarea(RSX[0] + 0.5, RSX[1] - 0.5, YS3 + 0.2, YR0 - 0.2, Z7)
    # the roof stand: seats rising to the back, two stairs, flank walls on the rake, a balustrade round its top, a flag
    zr, _ = seating(RSX[0], RSX[1], YR0, YR1, Z7, RROWS, RRISE, aisles=[4.8, 29.0])
    K.box("wall", RSX[0], RSX[1], YR1, YB, Z7, zr + 0.3)
    K.box("quoin", RSX[0] - 0.3, RSX[1] + 0.3, YR1 - 0.2, YB + 0.3, zr + 0.3, zr + 0.7)
    n = int(round((RSX[1] - RSX[0]) / 5.0))
    stone_rail(RSX[0], RSX[1], YR1 + 0.3, zr + 0.7, [RSX[0] + (RSX[1] - RSX[0]) * i / n for i in range(n + 1)], h=1.05)
    rarea(RSX[0] + 0.5, RSX[1] - 0.5, YR1 + 0.5, YB, zr + 0.7)
    for x, s in ((RSX[0], -1), (RSX[1], 1)):
        rake_flank(x, s, [(YR0 - 0.2, Z7 + 1.1), (YR1, zr + 1.4), (YB + 0.3, zr + 1.4)])
    fx = (RSX[0] + RSX[1]) / 2
    K.cyl("trim", fx, YB - 0.4, zr + 0.7, zr + 10.5, 0.1, 0.06, 6)
    K.sphere("gilt", fx, YB - 0.4, zr + 10.6, 0.16, 1)
    K.box("canvas", fx + 0.1, fx + 3.2, YB - 0.43, YB - 0.37, zr + 8.6, zr + 10.4)
    back_block(XM, X1, YB, 5.0, Z6, 4.0)
    # ---- the ends (his rule): flank walls up the terrace's rake to the top walk, then the building's own end walls
    for x, s, ztop in ((X0, -1, ZL2 + 1.1), (X1, 1, Z6 + 1.1)):
        rake_flank(x, s, [(-3.0, 1.2), (0.0, 1.3), (YT, ZP + 1.1), (YC - 0.6, ZP + 1.1)])
        xa, xb = sorted((x, x + s * 0.45))
        yend = YBW if s < 0 else YB
        K.box("wall", xa, xb, YC - 0.6, yend, -1.0, ztop)
        K.box("podium", xa - 0.05, xb + 0.05, YC - 0.75, yend, ztop - 0.25, ztop + 0.05)
        floors = (ZL1, ZL2) if s < 0 else (Z1, Z2, Z3, Z4, Z5, Z6)
        for z in floors:
            K.box("podium", xa - 0.06, xb + 0.06, YC - 0.75, yend, z - 0.5, z - 0.3)
        xf = x + s * 0.46
        for z in [ZP + 1.0] + [f + 1.0 for f in floors[:-1]]:
            for y in (YC + 7.0, (YC + yend) / 2 + 3.0, yend - 3.0):
                side_window(xf, s, y, z, 1.4, 2.0)
    K.box("wall", XM - 0.2, XM + 0.2, YC - 0.6, YBW, ZL3, Z4 - 0.5)   # the party wall where the main block rises
    return {"width": round(X1 - X0 + 0.9, 2), "depth": round(YB + 5.0 + 3.0, 2), "height": round(max(top_cupola, zr + 10.6), 2),
            "front": -3.0, "section": {"terraceTop": YT, "columns": YC, "walk": ZP, "galleries": [Z1, Z2, Z3, Z4],
            "storeys": [Z5, Z6, Z7], "west": [ZL1, ZL2, ZL3], "roofStand": [round(YR0, 2), round(YR1, 2), round(zr, 2)],
            "spans": {"west": [X0, XM], "wing": [X0, XW], "main": [XM, X1], "glazed": [S1X, S3X], "roofStand": RSX}}}


# ---------------------------------------------------------------------------------------------------- the rides
def ferris_wheel(R=14.5, n=16):
    """An observation wheel in the wheel's own plane x-z (it faces -y, the course): two A-frames, the hub, a double rim
    with ties, spokes, n gondolas hanging from the rim in pastel colours, a ticket booth at its foot."""
    hz = R + 3.2                                                       # the hub's height
    w = 2.4                                                            # half the wheel's thickness
    for s in (-1, 1):                                                  # the A-frames
        y = s * (w + 0.6)
        for dx in (-1, 1):
            strut("ride_steel", (dx * R * 0.55, y * 1.8, 0.0), (0.0, y, hz), r=0.32, segs=8)
        strut("ride_steel", (-R * 0.3, y * 1.4, hz * 0.45), (R * 0.3, y * 1.4, hz * 0.45), r=0.14, segs=6)
    K.push(Matrix.Translation((0.0, 0.0, hz)) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    K.cyl("ride_dark", 0.0, 0.0, -w - 1.2, w + 1.2, 0.55, segs=12)    # the axle
    K.cyl("ride_white", 0.0, 0.0, -w, w, 1.4, segs=16)                # the hub
    K.pop()
    m = 48
    rim = lambda a, y, r=R: (r * math.cos(a), y, hz + r * math.sin(a))
    for y in (-w, w):
        for i in range(m):
            a0, a1 = 2 * math.pi * i / m, 2 * math.pi * (i + 1) / m
            strut("ride_white", rim(a0, y), rim(a1, y), r=0.22, segs=6)
            strut("ride_white", rim(a0, y, R - 1.2), rim(a1, y, R - 1.2), r=0.1, segs=4)
        for i in range(n):
            a = 2 * math.pi * i / n
            strut("ride_white", (0.0, y * 0.5, hz), rim(a, y), r=0.08, segs=4)                   # spokes
            strut("ride_white", (0.0, y * 0.5, hz), rim(a + math.pi / n, y, R - 1.2), r=0.06, segs=4)
    for i in range(n):
        a = 2 * math.pi * i / n
        strut("ride_white", rim(a, -w), rim(a, w), r=0.12, segs=4)                                  # ties across the rim
    cols = ["ride_red", "ride_blue", "ride_yellow", "ride_green"]
    for i in range(n):                                                 # the gondolas, hanging below the rim
        a = 2 * math.pi * i / n + math.pi / n
        x, _, z = rim(a, 0.0)
        strut("ride_steel", (x, 0.0, z), (x, 0.0, z - 1.0), r=0.06, segs=4)
        K.box(cols[i % 4], x - 1.0, x + 1.0, -1.1, 1.1, z - 3.0, z - 1.6)
        K.box("ride_white", x - 1.05, x + 1.05, -1.15, 1.15, z - 3.1, z - 3.0)
        K.box("glass", x - 0.9, x + 0.9, -1.12, 1.12, z - 1.6, z - 1.15)
        K.box(cols[i % 4], x - 1.15, x + 1.15, -1.25, 1.25, z - 1.15, z - 0.95)
    K.box("ride_white", -5.0, 5.0, -3.0, 3.0, -0.5, 0.5)               # the platform and the booth
    K.box("ride_red", -6.5, -3.5, -5.5, -3.0, 0.0, 2.6)
    K.box("ride_white", -6.8, -3.2, -5.8, -2.7, 2.6, 2.9)
    return {"width": round(2 * R + 4.0, 2), "depth": 12.0, "height": round(hz + R + 1.0, 2)}


def helter_skelter(H=12.0, R0=2.6, R1=1.8, turns=3.0):
    """The striped tower (bands of pastel and white), a pointed roof with a flag, its spiral slide winding round from
    the top to a run-out at the foot, a little stair hut at the door."""
    nb = 8
    for k in range(nb):                                                # the tower, in bands
        z0, z1 = H * k / nb, H * (k + 1) / nb
        r0, r1 = R0 + (R1 - R0) * k / nb, R0 + (R1 - R0) * (k + 1) / nb
        K.cyl("ride_red" if k % 2 == 0 else "ride_white", 0.0, 0.0, max(z0, -0.5) if k else -0.5, z1, r0, r1, segs=16)
    K.cyl("ride_white", 0.0, 0.0, H, H + 1.3, R1 + 0.4, segs=16)        # the gallery at the top
    for i in range(12):
        a = 2 * math.pi * i / 12
        K.cyl("ride_white", (R1 + 0.3) * math.cos(a), (R1 + 0.3) * math.sin(a), H + 1.3, H + 2.5, 0.07, segs=4)
    K.cyl("ride_red", 0.0, 0.0, H + 2.5, H + 2.7, R1 + 0.6, segs=16)
    for k in range(4):                                                 # the pointed roof, striped
        K.cyl("ride_white" if k % 2 else "ride_red", 0.0, 0.0, H + 2.7 + k * 0.7, H + 3.4 + k * 0.7,
              (R1 + 0.6) * (1 - k / 4), (R1 + 0.6) * (1 - (k + 1) / 4) + 0.02, segs=16)
    K.cyl("trim", 0.0, 0.0, H + 5.5, H + 7.5, 0.05, segs=4)
    K.box("ride_yellow", 0.06, 1.3, -0.02, 0.02, H + 6.6, H + 7.4)
    # the slide: a sloping trough winding down outside the tower, from the top gallery to a run-out
    bm = K.bm("ride_yellow")
    N = int(turns * 40)
    def ring(i):
        t = i / N
        a = -math.pi / 2 + 2 * math.pi * turns * t
        z = (H + 0.9) * (1 - t) + 0.5 * t
        r = R0 + (R1 - R0) * (z / H) + 0.2
        c, s = math.cos(a), math.sin(a)
        return [bm.verts.new(K.M @ Vector(((r + d) * c, (r + d) * s, z + h))) for d, h in ((0.0, 0.5), (0.0, 0.0), (1.4, 0.0), (1.4, 0.5))]
    rings = [ring(i) for i in range(N + 1)]
    for i in range(N):
        a, b = rings[i], rings[i + 1]
        for j in range(3):
            bm.faces.new((a[j], b[j], b[j + 1], a[j + 1]))
    for i in range(0, N + 1, 5):                                       # brackets from the tower to the slide
        t = i / N; a = -math.pi / 2 + 2 * math.pi * turns * t; z = (H + 0.9) * (1 - t) + 0.5 * t
        r = R0 + (R1 - R0) * (z / H)
        strut("ride_white", (r * math.cos(a), r * math.sin(a), z - 0.6), ((r + 1.5) * math.cos(a), (r + 1.5) * math.sin(a), z), r=0.06, segs=4)
    K.box("ride_yellow", -0.7, 0.7, -R0 - 5.0, -R0 - 1.6, 0.0, 0.45)   # the run-out mat at the foot
    K.box("ride_blue", R0 - 0.2, R0 + 2.4, -1.4, 1.4, 0.0, 2.4)        # the pay hut at the door
    K.hip_roof(R0 - 0.2, R0 + 2.4, -1.4, 1.4, 2.4, 0.9, ov=0.2, mat="ride_white")
    return {"width": round(2 * (R0 + 1.8) + 2.0, 2), "depth": round(2 * (R0 + 1.8) + 3.4, 2), "height": round(H + 7.5, 2)}


PIECES = [
    ("epsom_grandstand", epsom_grandstand),
    ("epsom_ferris_wheel", ferris_wheel),
    ("epsom_helter_skelter", helter_skelter),
]
LIB = bpy.data.collections.new("epsom_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-22s %7d triangles, %4d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "Epsom's grandstand and the Hill's rides (tools/blender/build_epsom_stands.py). Building axes: x along "
                     "the front (left to right from the track), y into the building (front faces -y), z up; origin the "
                     "middle of the front on the ground (the terrace's foot; the front walk runs 3 m before it). crowd: "
                     "[x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "epsom_stands.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "epsom_stands.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported epsom_stands.glb", flush=True)

if os.environ.get("SHEET"):
    REN = rp("reference/epsom/renders")
    os.makedirs(REN, exist_ok=True)
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.80, 0.82, 0.90, 1); bg.inputs["Strength"].default_value = 1.0
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.0; sun.data.angle = math.radians(4)
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = 1920, 820
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "JPEG"; scene.render.image_settings.quality = 90
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, 0))
    bpy.context.object.data.materials.append(material("lawn", "#b2c98a"))
    OBJ["epsom_ferris_wheel"].location = (130, -30, 0)
    OBJ["epsom_helter_skelter"].location = (108, -40, 0)

    def shoot(name, frm, to, lens):
        cam = bpy.data.objects.new(name, bpy.data.cameras.new(name)); cam.data.lens = lens; cam.data.clip_end = 5000
        scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam; scene.render.filepath = os.path.join(REN, name + ".jpg")
        bpy.ops.render.render(write_still=True)
        print("rendered", name, flush=True)
    shoot("grandstand-front", (0, -230, 24), (0, 20, 22), 48)
    shoot("grandstand-three-quarter", (-150, -150, 60), (10, 20, 18), 38)
