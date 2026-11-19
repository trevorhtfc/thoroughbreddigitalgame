"""Chester's stand side, modelled from the owner's photos (18 Nov 2026), in the kit's soft clay finish.

    python3.11 -c "exec(open('tools/blender/build_chester_stands.py').read())"           # build and export
    SHEET=1 python3.11 -c "exec(open('tools/blender/build_chester_stands.py').read())"   # also a concept render

Owner: 23:07 "The stands and walls are really poor to be honest" (the first pass: kit pieces that weren't Chester, and the
walls as plain coloured boxes); 23:20 "I think make detailed models from the photos". His photos: the drone view down the
home straight (the brick block at the bend, the County Stand, the little gabled stands, the wall beyond); the finish with
the wall behind (deep buttresses with sloping tops, a crowd all along the top, a two-level viewing terrace built against
it); the County Stand from the infield (a long red-tiled hipped roof, black-and-white gables, white balconies); the County
Stand from the walls.

The pieces (building axes as every kit piece: x along the front, left to right seen from the track; y into the building,
the front faces -y; z up; origin the middle of the front on the ground):
  chester_county_stand   the County Stand: a raked terrace of red seats rising to a long two-storey front of white
                         balconies and glazing under one deep red-tiled hipped roof with three black-and-white gables on
                         its front slope, and a taller gabled wing at its left end
  chester_tattersalls    four little covered terraces side by side, each under its own red-tiled gable facing the track
  chester_brick_block    the brick block at the bend: four storeys, white balconies round its track corner, a hipped roof
  chester_wall_bay       8 m of the city wall: red sandstone with coursing, a deep buttress with a sloping top, the coping
                         and the parapet, the walkway on top (the crowd stands there)
  chester_wall_terrace   the viewing terrace built against the wall: a deck on posts with a white balustrade and steps
                         rising behind it to the wall top
  chester_terrace_row    the city behind: a row of three-storey brick terraced houses, pitched roofs, chimneys
  chester_city_block     a five-storey brick block with a parapet (the taller buildings behind the wall)
Stand ends follow the owner's rule: flank walls following the terraces' rake, never towers or end blocks.

Writes assets/models/architecture/chester_stands_kit.glb and .json (sizes, crowd areas), and with SHEET=1
reference/chester/renders/stands-concept.png.
"""
import json, math, os
REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)
exec(open(rp("tools/blender/kit.py")).read())

COL = {
    "render": "#f4ecdf", "trim": "#f7efe2", "timber": "#4d4642", "tile": "#c47a5f", "tile_dark": "#a9664f",
    "brick": "#c98670", "brick_dark": "#b4735f", "stone": "#c58670", "stone_dark": "#b97b66", "stone_lit": "#d3a089",
    "coping": "#e2bba5", "steps": "#e6dccb", "seat": "#cf7f74", "glass": "#3f3a4d", "iron": "#5b6273",
    "concrete": "#e6d9c4", "slate": "#8f95a8", "door": "#7f9f8c", "shade": "#5d5660", "paving": "#d8cdbb",
}
MATS = {k: material("ch_" + k, v, rough=0.9) for k, v in COL.items()}
K = Kit()
CROWD = []


def area(x0, x1, y0, y1, z):
    CROWD.append([round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z, 2)])


# ------------------------------------------------------------------------------------------ helpers
def roof_y(mat, x0, x1, y0, y1, z, pitch, ov=0.7, t=0.3):
    """A gabled roof with its ridge along y (the gable faces the track, -y); returns the rise."""
    xc, hw = (x0 + x1) / 2, (x1 - x0) / 2
    rise = (hw + ov) * math.tan(math.radians(pitch))
    K.prism_y(mat, y0 - ov, y1 + ov, [(x0 - ov, z), (xc, z + rise), (x1 + ov, z), (x1 + ov, z + t), (xc, z + rise + t), (x0 - ov, z + t)])
    K.box("trim", xc - 0.14, xc + 0.14, y0 - ov, y1 + ov, z + rise + t - 0.05, z + rise + t + 0.14)      # ridge capping
    return rise - ov * math.tan(math.radians(pitch))


def gable_end_y(mat, x0, x1, y, z, rise, thick=0.25):
    xc = (x0 + x1) / 2
    K.prism_y(mat, y, y + thick, [(x0, z), (x1, z), (xc, z + rise)])


def bargeboards(x0, x1, y, z, rise, ov=0.7):
    """White bargeboards up the gable's two slopes, just proud of the roof edge."""
    xc, hw = (x0 + x1) / 2, (x1 - x0) / 2
    L = math.hypot(hw + ov, rise + ov * rise / hw)
    a = math.atan2(rise, hw)
    for s in (-1, 1):
        m = Matrix.Translation((xc + s * (hw + ov) / 2, y - 0.04, z + (rise) / 2 + 0.12)) @ Matrix.Rotation(s * a, 4, "Y")
        K.boxm("trim", m, L, 0.12, 0.32)


def half_timber(x0, x1, y, z, rise, studs=5):
    """Black-and-white work on a gable's face at y (facing -y): a tie beam, studs and a king post with braces."""
    xc, hw = (x0 + x1) / 2, (x1 - x0) / 2
    K.box("timber", x0, x1, y - 0.06, y, z, z + 0.28)
    for i in range(1, studs):
        x = x0 + (x1 - x0) * i / studs
        h = rise * (1 - abs(x - xc) / hw) - 0.2
        if h > 0.4:
            K.box("timber", x - 0.11, x + 0.11, y - 0.06, y, z, z + h)
    for s in (-1, 1):                                            # braces from the tie beam up to the king post
        L = math.hypot(hw * 0.45, rise * 0.45)
        m = Matrix.Translation((xc + s * hw * 0.22, y - 0.03, z + rise * 0.24)) @ Matrix.Rotation(s * math.atan2(rise * 0.45, hw * 0.45), 4, "Y")
        K.boxm("timber", m, L, 0.06, 0.2)


def flank_y(mat, x0, x1, profile):
    """A flank wall at a stand's end (owner's rule: following the rake): an x-thick slab with a y-z profile."""
    K.prism_x(mat, x0, x1, profile)


def raked(x0, x1, y0, z0, rows, tread, rise, seat=True, mat="steps"):
    """A raked terrace from y0 (front) back, row by row; each tread with a strip of seats; crowd areas on each."""
    for i in range(rows):
        ya, yb = y0 + i * tread, y0 + (i + 1) * tread
        zt = z0 + (i + 1) * rise
        K.box(mat, x0, x1, ya, yb if i < rows - 1 else yb + 0.3, -0.5, zt)
        if seat:
            K.box("seat", x0 + 0.1, x1 - 0.1, yb - 0.42, yb - 0.08, zt, zt + 0.42)
        area(x0 + 0.2, x1 - 0.2, ya + 0.15, yb - 0.25, zt)
    return y0 + rows * tread, z0 + rows * rise


def balcony(x0, x1, y, z, depth=1.4, rail_mat="trim"):
    K.box("render", x0, x1, y - depth, y, z - 0.3, z)
    K.balustrade(x0, x1, y - depth + 0.1, z, h=1.05, mat=rail_mat, spacing=0.3)
    area(x0 + 0.3, x1 - 0.3, y - depth + 0.4, y - 0.2, z)


# ------------------------------------------------------------------------------------------ 1: the County Stand
# Owner, 23:34, his sheet of the kinked grandstand (3D perspective, plan, roof plan, front, rear and side elevations): a long
# covered stand of raked seats under a deep hipped roof on slender bracketed columns, a glazed clerestory along the back
# under the eaves, a tall steep gable with a round window rising from the roof, flights of steps down to the lawn from
# the raised terrace; a four-storey block of glazed balconies at one end under a hipped roof with a little gable; at the
# other end the stand kinks forward round the bend, its roof carrying three steep gables, finished with a flank wall
# following the rake. On his sheet the kink is on the right of the front elevation; here it is at the bend end (next to
# the brick block, past the post, towards the north corner), so the piece is his sheet mirrored: kink on the left seen
# from the track, the four-storey block on the right.
def bracket(x, y, z, d=1.6):
    """A timber bracket under the canopy from a column head forward to the eaves beam."""
    m = Matrix.Translation((x, y - d / 2 + 0.1, z - d * 0.35)) @ Matrix.Rotation(math.radians(-35), 4, "X")
    K.boxm("trim", m, 0.14, d * 1.15, 0.16)


def covered_terrace(x0, x1, rows=14, podium=3.2, tread=0.92, rise=0.38, stairs=(), cols=True):
    """The stand's section between x0 and x1 (front at y = 0): the ground storey, the raked seats, the columns, the
    clerestory and the eaves (the roof is laid over it separately). Returns its cross-section's numbers."""
    K.box("render", x0, x1, 0.0, 1.2, -0.5, podium)
    for x in [x0 + 3.0 + i * 5.0 for i in range(int((x1 - x0 - 3.0) / 5.0))]:
        K.box("shade", x - 1.1, x + 1.1, -0.04, 0.05, 0.0, 2.4)
        K.box("trim", x - 1.3, x + 1.3, -0.08, 0.0, 2.4, 2.65)
    K.box("trim", x0, x1, -0.15, 1.2, podium, podium + 0.2)
    K.balustrade(x0, x1, 0.2, podium + 0.2, h=0.95, mat="trim", spacing=0.32)
    yb, zb = raked(x0, x1, 1.2, podium, rows, tread, rise)
    for x in [x0 + (x1 - x0) * i / 4 for i in range(1, 4)]:                 # gangways
        for i in range(rows):
            K.box("concrete", x - 0.6, x + 0.6, 1.2 + i * tread, 1.2 + (i + 1) * tread, podium, podium + (i + 0.55) * rise)
    E = zb + 4.2
    K.box("render", x0, x1, yb, yb + 7.0, -0.5, E - 2.6)
    K.screen(x0 + 0.3, x1 - 0.3, yb, E - 2.6, 2.3, pane=1.3)
    K.box("render", x0, x1, yb + 0.6, yb + 7.0, E - 0.4, E)
    if cols:
        n = max(2, int(round((x1 - x0) / 5.0)))
        for i in range(n + 1):
            x = x0 + 0.25 + (x1 - x0 - 0.5) * i / n
            K.cyl("trim", x, 1.6, podium + 0.2, E - 0.45, 0.13, segs=8)
            bracket(x, 1.6, E - 0.45)
    K.box("trim", x0, x1, -0.2, 0.25, E - 0.6, E)
    K.box("trim", x0, x1, -0.25, 0.3, E, E + 0.12)
    for xs in stairs:
        steps = 9
        for k in range(steps):
            K.box("concrete", xs - 1.3, xs + 1.3, -0.4 - (steps - k) * 0.45, -0.4 - (steps - k - 1) * 0.45, -0.5, (k + 1) * podium / steps)
        for sx in (xs - 1.4, xs + 1.4):
            K.prism_x("trim", sx - 0.08, sx + 0.08, [(-0.4 - steps * 0.45, 0.0), (-0.4, podium), (-0.4, podium + 1.0), (-0.4 - steps * 0.45, 1.0)])
    return {"rows": rows, "podium": podium, "tread": tread, "rise": rise, "yb": yb, "zb": zb, "E": E, "D": yb + 7.0}


def roof_x(mat, x0, x1, y0, y1, z, rise, hip0=False, hip1=False):
    """A solid roof with its ridge along x, hipped at either end or cut square (where it runs on into the next part)."""
    bm = K.bm(mat)
    h = (y1 - y0) / 2; yc = (y0 + y1) / 2
    v = lambda x, y, zz: bm.verts.new(K.M @ Vector((x, y, zz)))
    b0, b1, b2, b3 = v(x0, y0, z), v(x1, y0, z), v(x1, y1, z), v(x0, y1, z)
    r0, r1 = v(x0 + (h if hip0 else 0.0), yc, z + rise), v(x1 - (h if hip1 else 0.0), yc, z + rise)
    for f in ((b0, b1, r1, r0), (b2, b3, r0, r1), (b3, b0, r0), (b1, b2, r1), (b3, b2, b1, b0)):
        bm.faces.new(f)
    K.box("trim", x0, x1, y0 - 0.05, y0 + 0.15, z - 0.35, z)
    K.box("trim", x0, x1, y1 - 0.15, y1 + 0.05, z - 0.35, z)
    K.box("trim", x0 + (h if hip0 else 0.0), x1 - (h if hip1 else 0.0), yc - 0.12, yc + 0.12, z + rise - 0.05, z + rise + 0.12)


def revolve(mat, px, py, prof, a1, steps=6):
    """Sweeps a closed y-z profile (at x = px) round the vertical axis through (px, py) from 0 to a1 radians: the fan that
    joins the straight stand to its kink without a break (owner, 19 Nov 00:04: "the stand when it kinks shouldnt break")."""
    bm = K.bm(mat)
    rings = []
    for i in range(steps + 1):
        a = a1 * i / steps; c, sn = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(K.M @ Vector((px - (y - py) * sn, py + (y - py) * c, z))) for y, z in prof])
    n = len(prof)
    for i in range(steps):
        A, B = rings[i], rings[i + 1]
        for j in range(n):
            bm.faces.new((A[j], A[(j + 1) % n], B[(j + 1) % n], B[j]))


def fan(x0, S, a1, roof_rise, ov=1.2):
    """The stand's cross-section swept round the kink."""
    revolve("render", x0, 0.0, [(0.0, -0.5), (1.2, -0.5), (1.2, S["podium"]), (0.0, S["podium"])], a1)
    for i in range(S["rows"]):
        ya, yb2 = 1.2 + i * S["tread"], 1.2 + (i + 1) * S["tread"]
        zt = S["podium"] + (i + 1) * S["rise"]
        revolve("steps", x0, 0.0, [(ya, -0.5), (yb2, -0.5), (yb2, zt), (ya, zt)], a1)
        revolve("seat", x0, 0.0, [(yb2 - 0.42, zt), (yb2 - 0.08, zt), (yb2 - 0.08, zt + 0.42), (yb2 - 0.42, zt + 0.42)], a1)
    yb, E, D = S["yb"], S["E"], S["D"]
    revolve("render", x0, 0.0, [(yb, -0.5), (D, -0.5), (D, E - 2.6), (yb, E - 2.6)], a1)
    revolve("glass", x0, 0.0, [(yb, E - 2.6), (yb + 0.1, E - 2.6), (yb + 0.1, E - 0.4), (yb, E - 0.4)], a1)
    revolve("render", x0, 0.0, [(yb + 0.6, E - 0.4), (D, E - 0.4), (D, E), (yb + 0.6, E)], a1)
    revolve("trim", x0, 0.0, [(-0.2, E - 0.6), (0.25, E - 0.6), (0.25, E), (-0.2, E)], a1)
    Y0, Y1 = -0.3 - ov, D + ov
    revolve("tile", x0, 0.0, [(Y0, E), (Y1, E), ((Y0 + Y1) / 2, E + roof_rise)], a1, steps=8)


def county_stand(L=62.0, Lk=26.0, kink=32.0):
    x0, x1 = -L / 2, L / 2
    RISE, OV = 7.0, 1.2
    # ---- the main stand, its roof cut square at the kink end (it runs on round the bend)
    S = covered_terrace(x0, x1, stairs=[x0 + 8, x0 + 20, 0.0, x1 - 20, x1 - 8])
    E, D = S["E"], S["D"]
    roof_x("tile", x0, x1, -0.3 - OV, D + OV, E, RISE)
    # the tall steep gable rising from the roof right of centre, with its round window and a glazed band under it
    gx0, gx1 = L * 0.18 - 4.5, L * 0.18 + 4.5
    K.box("render", gx0, gx1, 1.0, 7.0, E - 0.2, E + 2.6)
    K.screen(gx0 + 0.4, gx1 - 0.4, 1.0, E + 0.2, 1.8, pane=1.1)
    rise = roof_y("tile", gx0, gx1, 1.0, 8.0, E + 2.6, 62, ov=0.7)
    gable_end_y("render", gx0, gx1, 1.0, E + 2.6, rise)
    bargeboards(gx0, gx1, 1.0, E + 2.6, rise, ov=0.7)
    K.disc_y("trim", (gx0 + gx1) / 2, 0.88, 1.02, E + 2.6 + rise * 0.42, 1.25, segs=28)
    K.disc_y("glass", (gx0 + gx1) / 2, 0.82, 0.9, E + 2.6 + rise * 0.42, 0.95, segs=28)
    K.cyl("iron", (gx0 + gx1) / 2, 4.5, E + 2.6 + rise + 0.2, E + 2.6 + rise + 2.6, 0.06, segs=4, smooth=False)
    # ---- the four-storey block at the right-hand end
    bx0, bx1, bD = x1, x1 + 16.0, D - 1.0
    H = 15.6
    K.box("render", bx0, bx1, -1.0, bD, -0.5, H)
    for i in range(3):
        K.window(bx0 + 3 + i * 5, -1.0, 0.9, 1.6, 2.0)
    for z in (4.4, 8.2, 12.0):
        K.screen(bx0 + 0.6, bx1 - 0.6, -1.0, z, 3.0, pane=1.4)
        balcony(bx0 + 0.3, bx1 - 0.3, -1.0, z, depth=1.4)
    K.hip_roof(bx0, bx1, -1.0, bD, H, 5.2, ov=1.0, mat="tile")
    rise = roof_y("tile", bx0 + 5, bx1 - 5, -0.6, 5.0, H + 0.3, 50, ov=0.4)
    gable_end_y("render", bx0 + 5, bx1 - 5, -0.6, H + 0.3, rise)
    for i in range(3):
        K.box("glass", bx0 + 6.4 + i * 1.1, bx0 + 6.9 + i * 1.1, -0.66, -0.6, H + 0.6, H + 0.6 + rise * 0.45)
    # ---- round the bend without a break: the same cross-section swept through the kink's angle, then the kink
    fan(x0, S, math.radians(kink), RISE, OV)
    K.push(Matrix.Translation((x0, 0.0, 0.0)) @ Matrix.Rotation(math.radians(kink), 4, "Z"))
    k0 = -Lk
    covered_terrace(k0, 0.0, stairs=[k0 + 7, k0 + 17])
    roof_x("tile", k0 - OV, 0.0, -0.3 - OV, D + OV, E, RISE, hip0=True)
    for i in range(3):                                                  # three steep gables on its front slope
        cx = k0 + 5.0 + i * 7.5
        rise = roof_y("tile", cx - 3.2, cx + 3.2, 0.0, 6.0, E, 60, ov=0.5)
        gable_end_y("render", cx - 3.2, cx + 3.2, 0.0, E, rise)
        bargeboards(cx - 3.2, cx + 3.2, 0.0, E, rise, ov=0.5)
        K.box("glass", cx - 0.8, cx + 0.8, -0.06, 0.0, E + 0.6, E + 0.6 + rise * 0.38)
    # its open end: a flank wall following the rake (the owner's rule)
    flank_y("render", k0 - 0.5, k0, [(-0.4, -0.5), (-0.4, S["podium"] + 1.2), (S["yb"], S["zb"] + 1.0), (S["yb"], E), (D, E), (D, -0.5)])
    K.pop()
    # the kink's crowd areas, as small squares along its rotated rows (crowd areas are axis-aligned)
    ca, sa = math.cos(math.radians(kink)), math.sin(math.radians(kink))
    for i in range(S["rows"]):
        y = 1.2 + (i + 0.45) * S["tread"]; z = S["podium"] + (i + 1) * S["rise"]
        for u in [k0 + 1.0 + j * 1.6 for j in range(int((Lk - 2.0) / 1.6))]:
            X, Y = x0 + u * ca - y * sa, u * sa + y * ca
            area(X - 0.55, X + 0.55, Y - 0.3, Y + 0.3, z)
    reach = Lk * ca + D * sa
    width = L + 16.0 + reach + 1.0
    return {"width": round(width, 1), "depth": round(D + 1.2, 1), "height": round(E + 2.6 + 10.0, 1), "offset": round((16.0 - reach) / 2, 2),
            "kink": {"length": Lk, "degrees": kink, "at": x0, "forward": round(Lk * sa, 1),
                     "right": round(x1 + 16.0, 2), "leftEnd": [round(x0 - Lk * ca, 2), round(-Lk * sa, 2)]},
            "note": "main stand x %.0f..%.0f; the four-storey block to %.0f; the stand bends %.0f degrees forward at x %.0f (one "
                    "continuous stand) and runs %.0f m on round the bend" % (x0, x1, x1 + 16, kink, x0, Lk)}


# ------------------------------------------------------------------------------------------ 2: Tattersalls' little gabled stands
def tattersalls(n=4, bay=12.5):
    L = n * bay
    x0 = -L / 2
    for i in range(n):
        a, b = x0 + i * bay, x0 + (i + 1) * bay
        K.box("render", a, b, 0.0, 0.4, -0.5, 1.0)
        K.balustrade(a + 0.2, b - 0.2, 0.15, 1.0, h=0.9, mat="trim", spacing=0.4)
        yb, zb = raked(a + 0.25, b - 0.25, 0.4, 0.3, 9, 0.85, 0.34, seat=False)
        K.box("brick", a, b, yb, yb + 0.6, -0.5, zb + 3.6)              # the back wall
        for x in (a + 0.3, b - 0.3):                                     # posts at the front and halfway back
            for y in (0.6, yb * 0.55):
                K.cyl("trim", x, y, 0.0, zb + 3.2 if y > 1 else 5.6, 0.14, segs=8)
        E = zb + 3.4
        rise = roof_y("tile", a + 0.2, b - 0.2, 0.2, yb + 0.6, max(E, 5.8), 40, ov=0.5)
        gable_end_y("render", a + 0.4, b - 0.4, yb + 0.3, max(E, 5.8), rise - 0.3)
        bargeboards(a + 0.2, b - 0.2, 0.2, max(E, 5.8), rise, ov=0.5)
        K.box("trim", a + 0.2, b - 0.2, -0.3, 0.3, max(E, 5.8) - 0.5, max(E, 5.8))        # fascia beam over the front
    for xa, xb, s in ((x0 - 0.4, x0, 1), (x0 + L, x0 + L + 0.4, 1)):
        flank_y("brick", xa, xb, [(0.0, -0.5), (0.0, 1.0), (yb, zb + 0.9), (yb + 0.6, zb + 3.6), (yb + 0.6, -0.5)])
    return {"width": L + 0.8, "depth": yb + 1.2, "height": round(max(E, 5.8) + rise + 0.5, 2)}


# ------------------------------------------------------------------------------------------ 3: the brick block at the bend
def brick_block(W=26.0, D=18.0, floors=4):
    x0, x1 = -W / 2, W / 2
    H = 1.0 + floors * 3.4
    K.box("brick", x0, x1, 0.0, D, -0.5, H)
    for f in range(floors):
        z = 1.0 + f * 3.4
        K.box("brick_dark", x0 - 0.05, x1 + 0.05, -0.05, D + 0.05, z - 0.15, z + 0.05)            # string course
        if f == 0:
            K.box("shade", x0 + 1.5, x1 - 1.5, -0.05, 0.1, 0.0, 2.8)                             # the ground floor entrance
            K.box("render", x0 + 1.0, x1 - 1.0, -2.2, 0.0, 2.9, 3.2)                              # canopy
            continue
        # white balconies all along the front and round the right-hand corner (the track corner)
        K.screen(x0 + 1.0, x1 - 1.0, 0.0, z, 2.9, pane=1.5)
        balcony(x0 + 0.6, x1 - 0.6, 0.0, z, depth=1.5)
        K.box("render", x1, x1 + 1.5, -1.5, D * 0.6, z - 0.3, z)
        K.balustrade(-1.4, D * 0.6, x1 + 1.4, z, h=1.05, mat="trim", spacing=0.3, axis="y")
    for f in range(1, floors):
        z = 1.0 + f * 3.4
        for i in range(4):
            y = 2.5 + i * (D - 5) / 3
            if y > D * 0.6: K.box("glass", x1 - 0.02, x1 + 0.08, y - 0.7, y + 0.7, z + 0.6, z + 2.4)
    K.hip_roof(x0, x1, 0.0, D, H, 4.6, ov=0.8, mat="tile")
    for cx in (x0 + 4, x1 - 4):                                          # chimneys
        K.box("brick", cx - 0.6, cx + 0.6, D * 0.55, D * 0.55 + 1.2, H, H + 5.6)
        K.box("brick_dark", cx - 0.7, cx + 0.7, D * 0.55 - 0.1, D * 0.55 + 1.3, H + 5.4, H + 5.8)
    return {"width": W + 3.0, "depth": D + 0.8, "height": round(H + 5.8, 2)}


# ------------------------------------------------------------------------------------------ 4: the city wall
WALL_H, WALL_T = 8.0, 2.6
import random as _random
WALL_RND = _random.Random(7)


def wall_section(x0, x1, buttress=True, dark=False):
    """The wall from x0 to x1: sandstone with coursing, the coping and parapet, the walkway; a buttress at its middle."""
    K.box("stone_dark" if dark else "stone", x0, x1, 0.0, WALL_T, -1.5, WALL_H)
    rnd = WALL_RND
    for i in range(1, int(WALL_H / 0.62)):                               # the coursing: fine joints, just proud
        z = 0.62 * i
        K.box("stone_dark", x0, x1, -0.02, 0.0, z, z + 0.04)
        x = x0 + rnd.uniform(0, 1.2)                                     # weathered blocks: a few lighter or darker
        while x < x1 - 0.5:
            w = rnd.uniform(0.7, 1.7)
            if rnd.random() < 0.3:
                K.box(rnd.choice(["stone_lit", "stone_dark", "stone_lit"]), x, min(x + w, x1), -0.015, 0.0, z - 0.58, z - 0.02)
            x += w
    K.box("coping", x0, x1, -0.12, 0.55, WALL_H, WALL_H + 0.95)          # the parapet on the track side
    K.box("stone_lit", x0, x1, -0.18, 0.62, WALL_H + 0.95, WALL_H + 1.1)
    K.box("paving", x0, x1, 0.55, WALL_T, WALL_H - 0.1, WALL_H + 0.05)    # the walkway
    K.box("coping", x0, x1, WALL_T - 0.4, WALL_T, WALL_H, WALL_H + 0.6)   # its back kerb
    if buttress:                                                         # deep, with a sloping (weathered) top
        xc = (x0 + x1) / 2
        K.prism_x("stone", xc - 0.85, xc + 0.85, [(0.0, -1.5), (-2.9, -1.5), (-2.7, 5.0), (-2.2, 5.0), (0.0, 7.4)])
        K.prism_x("stone_lit", xc - 0.92, xc + 0.92, [(-2.2, 5.0), (-2.75, 5.0), (-2.75, 5.25), (0.02, 7.7), (0.02, 7.4)])
        for z in [0.62 * i for i in range(1, 8)]:
            K.box("stone_dark", xc - 0.87, xc + 0.87, -2.9 + z * 0.03 - 0.02, -2.9 + z * 0.03, z, z + 0.04)
    area(x0 + 0.3, x1 - 0.3, 0.7, 2.1, WALL_H + 0.05)


def wall_bay(L=8.0):
    wall_section(-L / 2, L / 2)
    return {"width": L, "depth": WALL_T + 2.9, "height": WALL_H + 1.1, "frontAt": 0.0,
            "note": "8 m of the city wall; the buttress in the middle projects 2.9 m in front (towards the track)"}


# ------------------------------------------------------------------------------------------ 4b: the terraces built into the wall
# Owner, 19 Nov 00:04, his reference model sheet (3D perspective, plan at grandstand level, front and side elevations): "i
# have also made better reference models for the terraces built into the walls. make it as close as possible to this".
# Left to right on his front elevation: a tall pier at the end (an arched face, a round window, capped piers with ball
# finials); a covered stand on the steps (a raised deck behind a balustrade of X panels, bracketed columns, a canopy whose
# top is itself a raked terrace up to the wall top); open steps with the wall's blind arches above them; a second covered
# stand with a little lantern kiosk on its roof terrace; then long runs of open steps under the blind arches, their
# front tapering back to the wall at the far end. A low wall of X panels along the foot, X-panel railings along the top,
# handrails up the steps. Scaled to about three-quarters of his sheet so it sits on Chester's real wall: walkway 9.3 m up,
# steps 14 m deep.
WT_D, WT_ROWS, WT_TOP = 14.0, 16, 5.0        # the open steps: depth in front of the wall, rows, height at the wall
WT_WALK = 9.3                                 # the walkway on top of the wall


def x_rail(x0, x1, y, z, h=1.05, panel=2.0, mat="trim", axis="x"):
    """A railing of X panels: top and bottom rails, posts, a saltire in each panel."""
    L = abs(x1 - x0); lo = min(x0, x1)
    if L < 0.5: return
    def bx(a0, a1, b0, b1, z0, z1):
        if axis == "x": K.box(mat, a0, a1, b0, b1, z0, z1)
        else: K.box(mat, b0, b1, a0, a1, z0, z1)
    bx(lo, lo + L, y - 0.08, y + 0.08, z + h - 0.12, z + h)
    bx(lo, lo + L, y - 0.06, y + 0.06, z + 0.08, z + 0.2)
    n = max(1, int(round(L / panel)))
    w = L / n
    d = math.hypot(w - 0.2, h - 0.36); ang = math.atan2(h - 0.36, w - 0.2)
    for i in range(n + 1):
        bx(lo + i * w - 0.07, lo + i * w + 0.07, y - 0.07, y + 0.07, z, z + h + 0.05)
    if K.far: return
    for i in range(n):
        cx = lo + (i + 0.5) * w
        for sgn in (-1, 1):
            if axis == "x":
                m = Matrix.Translation((cx, y, z + h / 2 + 0.04)) @ Matrix.Rotation(sgn * ang, 4, "Y")
            else:
                m = Matrix.Translation((y, cx, z + h / 2 + 0.04)) @ Matrix.Rotation(sgn * ang, 4, "X")
            K.boxm(mat, m, d if axis == "x" else 0.05, 0.05 if axis == "x" else d, 0.05)


def foot_wall(x0, x1, y):
    """The low wall along the foot of the steps: a plinth with a coping and a run of X panels on it."""
    K.box("stone_lit", x0, x1, y - 0.35, y + 0.15, -0.5, 0.55)
    K.box("coping", x0, x1, y - 0.42, y + 0.2, 0.55, 0.7)
    x_rail(x0, x1, y - 0.12, 0.7, h=0.75, panel=1.9)


def steps_run(x0, x1, y_front, y_back, z0, z_top, rows, rails=(), base=-0.5):
    """Plain steps from y_front (z0) back to y_back (z_top); handrails up them at the given x; crowd areas on the treads."""
    tread = (y_back - y_front) / rows; rise = (z_top - z0) / rows
    for i in range(rows):
        ya, yb = y_front + i * tread, y_front + (i + 1) * tread
        zt = z0 + (i + 1) * rise
        K.box("steps", x0, x1, ya, y_back if i == rows - 1 else yb + 0.02, base, zt)
        K.box("concrete", x0, x1, ya - 0.02, ya + 0.04, zt - rise, zt)        # the riser's lighter nosing line
        area(x0 + 0.3, x1 - 0.3, ya + 0.15, yb - 0.15, zt)
    for xr in rails:
        for sx in (xr - 0.75, xr + 0.75):
            L = math.hypot(y_back - y_front, z_top - z0)
            m = Matrix.Translation((sx, (y_front + y_back) / 2, (z0 + z_top) / 2 + 1.0)) @ Matrix.Rotation(-math.atan2(z_top - z0, y_back - y_front), 4, "X")
            K.boxm("trim", m, 0.08, L, 0.08)
            for k in range(0, rows + 1, 3):
                yy = y_front + k * tread; zz = z0 + k * rise
                K.box("trim", sx - 0.05, sx + 0.05, yy - 0.05, yy + 0.05, zz, zz + 1.05)


def arch_wall(x0, x1, z0, z1, arch=True, w=4.4, spring=3.4):
    """The wall's face from z0 to z1 over x0..x1, with a blind arch (a recess) in the middle; ashlar piers; the walkway, its
    back kerb and the X-panel railing on top."""
    xc = (x0 + x1) / 2
    K.box("stone_dark", x0, x1, 0.6, WALL_T, -1.5, z1)                   # the recess's back (the wall's core)
    if arch:
        a0, a1 = xc - w / 2, xc + w / 2; zs = z0 + spring; r = w / 2
        prof = [(x0, z0), (a0, z0), (a0, zs)] + [(xc - r * math.cos(t), zs + r * math.sin(t)) for t in [math.pi * k / 12 for k in range(1, 12)]] + \
               [(a1, zs), (a1, z0), (x1, z0), (x1, z1), (x0, z1)]
        K.prism_y("stone", 0.0, 0.6, prof)
        for t in [math.pi * k / 10 for k in range(11)]:                    # the arch's ring of voussoirs
            K.box("stone_lit", xc - (r + 0.3) * math.cos(t) - 0.3, xc - (r + 0.3) * math.cos(t) + 0.3, -0.04, 0.0,
                  zs + (r + 0.3) * math.sin(t) - 0.3, zs + (r + 0.3) * math.sin(t) + 0.3)
        K.box("stone_lit", a0 - 0.35, a0, -0.03, 0.0, z0, zs); K.box("stone_lit", a1, a1 + 0.35, -0.03, 0.0, z0, zs)
    else:
        K.box("stone", x0, x1, 0.0, 0.6, z0, z1)
    for i in range(1, int((z1 - z0) / 0.62)):                             # fine coursing
        z = z0 + 0.62 * i
        if arch and a0 - 0.35 < x0: pass
        K.box("stone_dark", x0, (xc - w / 2 - 0.35) if arch else x1, -0.02, 0.0, z, z + 0.04)
        if arch: K.box("stone_dark", xc + w / 2 + 0.35, x1, -0.02, 0.0, z, z + 0.04)
    K.box("coping", x0, x1, -0.15, 0.7, z1, z1 + 0.35)                    # the string course at the walkway
    K.box("paving", x0, x1, 0.6, WALL_T, z1 - 0.1, z1 + 0.05)
    x_rail(x0, x1, 0.15, z1 + 0.35, h=1.0, panel=2.0)
    area(x0 + 0.3, x1 - 0.3, 0.7, 2.2, z1 + 0.05)


def wt_steps(L=8.0, rail=False):
    x0, x1 = -L / 2, L / 2
    foot_wall(x0, x1, -WT_D)
    steps_run(x0, x1, -WT_D + 0.2, 0.0, 0.0, WT_TOP, WT_ROWS, rails=(0.0,) if rail else ())
    arch_wall(x0, x1, WT_TOP, WT_WALK)
    return {"width": L, "depth": WT_D + WALL_T, "height": WT_WALK + 1.4, "frontAt": -WT_D,
            "note": "origin on the wall's face; the steps run %.0f m in front of it" % WT_D}


def wt_stand(L=32.0, lantern=False):
    """A covered stand on the steps: deck, X-panel balustrade, bracketed columns, a canopy whose top is a raked terrace."""
    x0, x1 = -L / 2, L / 2
    DECK_Y, DECK_Z = -9.0, 2.6                                           # the deck's front edge and level
    CAN_Y, CAN_Z = -9.8, 6.4                                             # the canopy's front edge and underside
    foot_wall(x0 - 0.0, x1, -WT_D)
    # the steps up to the deck (with handrails at the gangways)
    steps_run(x0 + 0.6, x1 - 0.6, -WT_D + 0.2, DECK_Y, 0.0, DECK_Z, 6, rails=(x0 + L * 0.25, x1 - L * 0.25))
    K.box("concrete", x0 + 0.6, x1 - 0.6, DECK_Y, -6.6, -0.5, DECK_Z)    # the deck
    x_rail(x0 + 0.6, x1 - 0.6, DECK_Y + 0.15, DECK_Z, h=1.05, panel=1.8)
    area(x0 + 1.0, x1 - 1.0, DECK_Y + 0.5, -6.9, DECK_Z)
    # the seats under the canopy, rising to the wall
    yb, zb = raked(x0 + 0.6, x1 - 0.6, -6.6, DECK_Z, 6, 1.0, 0.42)
    K.box("shade", x0 + 0.6, x1 - 0.6, -0.6, 0.0, zb, CAN_Z)              # the dark back under the canopy
    # columns with brackets, the canopy and its fascia
    n = int(round(L / 5.4))
    for i in range(n + 1):
        x = x0 + 1.0 + (L - 2.0) * i / n
        K.cyl("trim", x, DECK_Y + 0.6, DECK_Z, CAN_Z, 0.16, segs=8)
        K.box("trim", x - 0.32, x + 0.32, DECK_Y + 0.28, DECK_Y + 0.92, DECK_Z, DECK_Z + 0.35)
        K.box("trim", x - 0.3, x + 0.3, DECK_Y + 0.3, DECK_Y + 0.9, CAN_Z - 0.35, CAN_Z)
        for sgn in (-1, 1):                                              # the brackets either side of each column head
            m = Matrix.Translation((x + sgn * 0.6, DECK_Y + 0.6, CAN_Z - 0.55)) @ Matrix.Rotation(sgn * math.radians(-40), 4, "Y")
            K.boxm("trim", m, 1.3, 0.14, 0.16)
    K.box("render", x0, x1, CAN_Y, 0.0, CAN_Z, CAN_Z + 0.55)
    K.box("trim", x0 - 0.1, x1 + 0.1, CAN_Y - 0.12, CAN_Y + 0.2, CAN_Z - 0.2, CAN_Z + 0.7)
    # the canopy's top: a raked terrace up to the walkway, with X railings at the front and up the gangways
    steps_run(x0 + 0.3, x1 - 0.3, CAN_Y + 0.4, -0.2, CAN_Z + 0.55, WT_WALK, 8, rails=(x0 + L * 0.25, 0.0, x1 - L * 0.25), base=CAN_Z + 0.5)
    x_rail(x0 + 0.3, x1 - 0.3, CAN_Y + 0.25, CAN_Z + 0.55, h=1.05, panel=2.0)
    # flank walls at both ends following the profile (the owner's side elevation): one under the steps and the seats,
    # rising to the wall; one along the side of the canopy's roof terrace; the space between them open
    for xa, xb in ((x0, x0 + 0.6), (x1 - 0.6, x1)):
        flank_y("render", xa, xb, [(-WT_D + 0.2, -0.5), (-WT_D + 0.2, 0.35), (DECK_Y, DECK_Z + 0.25), (-6.6, DECK_Z + 0.25),
                                   (-0.6, zb + 0.35), (0.0, zb + 0.35), (0.0, -0.5)])
        flank_y("render", xa, xb, [(CAN_Y + 0.3, CAN_Z - 0.2), (CAN_Y + 0.3, CAN_Z + 1.0), (-0.2, WT_WALK + 0.6), (0.0, WT_WALK + 0.6), (0.0, CAN_Z - 0.2)])
    # the wall behind: plain above the canopy terrace (no arches show there), the walkway and its railing
    arch_wall(x0, x1, WT_TOP, WT_WALK, arch=False)
    if lantern:                                                          # the little lantern kiosk on the roof terrace
        lx, ly, lz = 0.0, -2.2, WT_WALK + 0.05
        K.box("render", lx - 1.9, lx + 1.9, ly - 1.9, ly + 1.9, lz - 3.5, lz + 0.4)
        K.box("render", lx - 1.6, lx + 1.6, ly - 1.6, ly + 1.6, lz + 0.4, lz + 2.6)
        for sx, sy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            if sy: K.box("glass", lx - 1.1, lx + 1.1, ly + sy * 1.62 - 0.03, ly + sy * 1.62 + 0.03, lz + 0.8, lz + 2.2)
            else: K.box("glass", lx + sx * 1.62 - 0.03, lx + sx * 1.62 + 0.03, ly - 1.1, ly + 1.1, lz + 0.8, lz + 2.2)
        K.box("trim", lx - 2.0, lx + 2.0, ly - 2.0, ly + 2.0, lz + 2.6, lz + 2.85)
        K.cyl("tile_dark", lx, ly, lz + 2.85, lz + 4.4, 2.2, 0.25, segs=4, smooth=False)    # the pointed roof
        K.cyl("trim", lx, ly, lz + 4.4, lz + 5.0, 0.18, 0.12, segs=8)
        K.sphere("trim", lx, ly, lz + 5.25, 0.32)
    return {"width": L, "depth": WT_D + WALL_T, "height": WT_WALK + (5.6 if lantern else 1.4), "frontAt": -WT_D,
            "note": "origin on the wall's face; a covered stand on the steps" + (", the lantern on its roof terrace" if lantern else "")}


def wt_tower():
    """The tall pier at the left-hand end: an arched face with a round window above, capped piers with ball finials, an X
    railing between them, a little balcony; the steps run past its foot."""
    W, y0, y1, H = 7.0, -6.0, WALL_T, WT_WALK + 4.2
    x0, x1 = -W / 2, W / 2
    foot_wall(x0, x1, -WT_D)
    steps_run(x0, x1, -WT_D + 0.2, y0, 0.0, 2.2, 5)
    K.box("stone", x0, x1, y0, y1, -0.5, H)
    for i in range(1, int(H / 0.62)):
        K.box("stone_dark", x0 - 0.02, x1 + 0.02, y0 - 0.02, y0, 0.62 * i, 0.62 * i + 0.04)
    # the arched face: a tall recessed arch with a round window over it
    K.prism_y("stone_dark", y0 - 0.02, y0 + 0.02, [(-1.6, 2.2), (1.6, 2.2), (1.6, 8.0)] + [(1.6 * math.cos(t), 8.0 + 1.6 * math.sin(t)) for t in [math.pi * k / 10 for k in range(1, 10)]] + [(-1.6, 8.0)])
    K.disc_y("stone_lit", 0.0, y0 - 0.08, y0, 11.3, 1.2, segs=24)
    K.disc_y("glass", 0.0, y0 - 0.12, y0 - 0.06, 11.3, 0.85, segs=24)
    for z in (WT_WALK, H - 0.5):                                         # string course and cornice
        K.box("coping", x0 - 0.25, x1 + 0.25, y0 - 0.25, y1 + 0.25, z, z + 0.45)
    for cx in (x0 + 0.8, x1 - 0.8):                                      # the capped piers with ball finials
        K.box("stone_lit", cx - 0.8, cx + 0.8, y0 - 0.3, y0 + 1.3, H - 0.05, H + 1.4)
        K.box("coping", cx - 0.95, cx + 0.95, y0 - 0.45, y0 + 1.45, H + 1.4, H + 1.7)
        K.sphere("trim", cx, y0 + 0.5, H + 2.15, 0.45)
    x_rail(x0 + 1.6, x1 - 1.6, y0 + 0.5, H - 0.05, h=1.1, panel=1.9)
    K.box("render", x0 + 0.6, x1 - 0.6, y0 - 1.4, y0, 4.6, 4.9)          # the little balcony
    K.balustrade(x0 + 0.6, x1 - 0.6, y0 - 1.3, 4.9, h=1.0, mat="trim", spacing=0.28)
    area(x0 + 0.9, x1 - 0.9, y0 - 1.2, y0 - 0.2, 4.9)
    return {"width": W, "depth": WT_D + WALL_T, "height": round(H + 2.6, 2), "frontAt": -WT_D,
            "note": "origin on the wall's face; the end pier of the wall terraces (from the owner's sheet)"}


def wt_taper(L=16.0, d_end=3.0):
    """The far end of the open steps: their front tapers back to the wall (the owner's plan)."""
    x0, x1 = -L / 2, L / 2
    n = 8
    for i in range(n):
        a, b = x0 + i * L / n, x0 + (i + 1) * L / n
        d = WT_D + (d_end - WT_D) * (i + 0.5) / n
        rows = max(3, int(round(WT_ROWS * d / WT_D)))
        steps_run(a, b, -d + 0.2, 0.0, max(0.0, WT_TOP - WT_TOP * d / WT_D * 1.0) * 0.0, WT_TOP, rows)
        foot_wall(a, b, -d)
    for i in range(2):
        arch_wall(x0 + i * L / 2, x0 + (i + 1) * L / 2, WT_TOP, WT_WALK)
    flank_y("render", x1, x1 + 0.6, [(-d_end, -0.5), (-d_end, 0.9), (0.0, WT_TOP + 0.9), (0.0, -0.5)])
    return {"width": L + 0.6, "depth": WT_D + WALL_T, "height": WT_WALK + 1.4, "frontAt": -WT_D,
            "note": "origin on the wall's face; the steps' front tapers from %.0f m to %.0f m" % (WT_D, d_end)}


# ------------------------------------------------------------------------------------------ 5: the city behind
def terrace_row(L=40.0, D=9.0, floors=3):
    x0, x1 = -L / 2, L / 2
    H = floors * 3.1
    n = int(L / 5.0)
    for i in range(n):
        a, b = x0 + i * L / n, x0 + (i + 1) * L / n
        K.box("brick" if i % 3 else "brick_dark", a, b, 0.0, D, -0.5, H)
        for f in range(floors):
            K.window((a + b) / 2 - 0.9, 0.0, 0.9 + f * 3.1, 1.0, 1.6, panes=False)
            if f: K.window((a + b) / 2 + 1.0, 0.0, 0.9 + f * 3.1, 1.0, 1.6, panes=False)
            else: K.door((a + b) / 2 + 1.0, 0.0, 0.0, 1.0, 2.2)
        K.box("brick_dark", b - 0.35, b + 0.35, D * 0.5 - 0.4, D * 0.5 + 0.4, H, H + 4.6)            # chimney stack
    K.prism_x("slate", x0 - 0.3, x1 + 0.3, [(-0.4, H), (D * 0.5, H + 3.6), (D + 0.4, H), (D + 0.4, H + 0.25), (D * 0.5, H + 3.85), (-0.4, H + 0.25)])
    return {"width": L, "depth": D, "height": round(H + 4.6, 2)}


def city_block(W=30.0, D=16.0, floors=5):
    x0, x1 = -W / 2, W / 2
    H = floors * 3.3 + 0.6
    K.box("brick", x0, x1, 0.0, D, -0.5, H)
    for f in range(floors):
        for i in range(int(W / 2.6)):
            K.window(x0 + 1.5 + i * 2.6, 0.0, 0.8 + f * 3.3, 1.2, 1.8, panes=False)
    K.box("stone_lit", x0 - 0.15, x1 + 0.15, -0.15, D + 0.15, H, H + 0.9)
    K.box("slate", x0 + 3, x1 - 3, 3, D - 3, H, H + 2.2)                  # a plant room on the roof
    return {"width": W, "depth": D, "height": round(H + 2.2, 2)}


# ------------------------------------------------------------------------------------------ build and export
PIECES = [
    ("chester_county_stand", county_stand),
    ("chester_tattersalls", tattersalls),
    ("chester_brick_block", brick_block),
    ("chester_wall_bay", wall_bay),
    ("chester_wt_steps", wt_steps),
    ("chester_wt_steps_rail", lambda: wt_steps(rail=True)),
    ("chester_wt_stand", wt_stand),
    ("chester_wt_stand_lantern", lambda: wt_stand(lantern=True)),
    ("chester_wt_tower", wt_tower),
    ("chester_wt_taper", wt_taper),
    ("chester_terrace_row", terrace_row),
    ("chester_city_block", city_block),
]
LIB = bpy.data.collections.new("chester_stands_kit")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-22s %6d triangles, %d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "Chester's stand side, modelled from the owner's photos (tools/blender/build_chester_stands.py). Building "
                     "axes: x along the front (left to right from the track), y into the building (front faces -y), z up; "
                     "origin the middle of the front on the ground. crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "chester_stands_kit.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "chester_stands_kit.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported chester_stands_kit.glb", flush=True)

if os.environ.get("SHEET"):
    # a concept vignette of the home straight as the owner's drone photo has it: the brick block, the County Stand, the
    # little stands, then the wall with its terrace and bays; the terraced houses and a block behind the wall
    def dup(name, x, y, rz=0.0):
        o = OBJ[name].copy(); o.data = OBJ[name].data; LIB.objects.link(o)
        o.location = (x, y, 0); o.rotation_euler = (0, 0, math.radians(rz)); o.hide_render = False; return o
    for o in list(LIB.objects): o.hide_render = True
    x = 0.0
    dup("chester_brick_block", x - 10, 18, -30); x += 16 + 22 + 31
    dup("chester_county_stand", x, 0); x += 31 + 16 + 3 + 25
    dup("chester_tattersalls", x, 2); x += 25 + 4
    # the wall terraces, as the owner's front elevation: the end pier, a stand, two bays of steps, the stand with the
    # lantern, eleven bays of steps (handrails every other), the tapering end; the wall's face 16 m back
    wy = 16.0
    seq = [("chester_wt_tower", 7.0), ("chester_wt_stand", 32.0), ("chester_wt_steps", 8.0), ("chester_wt_steps_rail", 8.0),
           ("chester_wt_stand_lantern", 32.0)] + [("chester_wt_steps_rail" if i % 2 else "chester_wt_steps", 8.0) for i in range(11)] + [("chester_wt_taper", 16.0)]
    xw = x + 6
    WT_X0 = xw
    for name, w in seq:
        dup(name, xw + w / 2, wy); xw += w
    for i in range(22):                                                 # the plain wall behind the stands
        dup("chester_wall_bay", 4 + i * 8, 40)
    bx = 30.0
    for i in range(9):
        dup("chester_terrace_row", bx + i * 44, 52 + (i % 2) * 6)
    dup("chester_city_block", 120, 46); dup("chester_city_block", 300, 34); dup("chester_city_block", 380, 36)
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.84, 0.9, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(150, 0, -0.02))
    bpy.context.object.data.materials.append(material("lawn", "#a8c47a"))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(160, -18, 0.0)); tr = bpy.context.object
    tr.scale = (420, 22, 1); tr.data.materials.append(material("turf", "#8fbb63"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 3.6; sun.data.angle = math.radians(6); sun.rotation_euler = (math.radians(48), 0, math.radians(-35))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "24")); scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = int(os.environ.get("RX", "2400")), int(os.environ.get("RY", "1100"))
    scene.view_settings.view_transform = "AgX"
    os.makedirs(rp("reference/chester/renders"), exist_ok=True)
    shots = [("stands-concept-1", (60, -150, 60), (100, 20, 6), 30),          # the whole stand side from above the infield
             ("stands-concept-2", (55, -70, 10), (75, 10, 9), 26),            # the County Stand
             ("stands-concept-5", (-30, -55, 14), (30, 5, 8), 30),           # round the kink
             ("stands-concept-3", (WT_X0 + 70, -110, 16), (WT_X0 + 70, 10, 6), 26),   # the wall terraces, square on (his front elevation)
             ("stands-concept-4", (WT_X0 + 10, -40, 9), (WT_X0 + 30, 10, 6), 28)]    # the end pier and the first stand
    for nm, frm, to, lens in shots:
        cam = bpy.data.objects.new(nm, bpy.data.cameras.new(nm)); cam.data.lens = lens; scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = rp("reference/chester/renders/%s.png" % nm)
        bpy.ops.render.render(write_still=True)
        print("rendered", nm, flush=True)
