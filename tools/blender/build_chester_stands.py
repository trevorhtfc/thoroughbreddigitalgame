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


def covered_terrace(x0, x1, rows=14, podium=3.2, tread=0.92, rise=0.38, stairs=(), back_glaze=True, gables=()):
    """The main stand's section between x0 and x1 (front at y = 0): the ground storey, the raked seats, the columns,
    the clerestory and the deep hipped roof. Returns (eaves height, depth)."""
    # the ground storey under the terrace: rendered, with doors, behind a short apron
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
    E = zb + 4.2                                                            # the eaves over the front
    # the back: a glazed clerestory under the eaves, rendered below
    K.box("render", x0, x1, yb, yb + 7.0, -0.5, E - 2.6)
    if back_glaze:
        K.screen(x0 + 0.3, x1 - 0.3, yb, E - 2.6, 2.3, pane=1.3)
    K.box("render", x0, x1, yb + 0.6, yb + 7.0, E - 0.4, E)
    # the slender columns along the front, each with a bracket to the eaves beam
    n = max(2, int(round((x1 - x0) / 5.0)))
    for i in range(n + 1):
        x = x0 + 0.25 + (x1 - x0 - 0.5) * i / n
        K.cyl("trim", x, 1.6, podium + 0.2, E - 0.45, 0.13, segs=8)
        bracket(x, 1.6, E - 0.45)
    K.box("trim", x0, x1, -0.2, 0.25, E - 0.6, E)                           # the eaves beam
    K.box("trim", x0, x1, -0.25, 0.3, E, E + 0.12)
    # the front stairs from the terrace down to the lawn
    for xs in stairs:
        steps = 9
        for k in range(steps):
            K.box("concrete", xs - 1.3, xs + 1.3, -0.4 - (steps - k) * 0.45, -0.4 - (steps - k - 1) * 0.45, -0.5, (k + 1) * podium / steps)
        for sx in (xs - 1.4, xs + 1.4):
            K.prism_x("trim", sx - 0.08, sx + 0.08, [(-0.4 - steps * 0.45, 0.0), (-0.4, podium), (-0.4, podium + 1.0), (-0.4 - steps * 0.45, 1.0)])
    return E, yb + 7.0


def county_stand(L=62.0, Lk=26.0, kink=32.0):
    x0, x1 = -L / 2, L / 2
    # ---- the main stand
    E, D = covered_terrace(x0, x1, stairs=[x0 + 8, x0 + 20, 0.0, x1 - 20, x1 - 8])
    K.hip_roof(x0, x1, -0.3, D, E, 7.0, ov=1.2, mat="tile")
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
    # ---- the four-storey block at the right-hand end: glazed balconies, a hipped roof with a little gable
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
    # ---- the kink at the left-hand end: the stand turns forward round the bend
    K.push(Matrix.Translation((x0, 0.0, 0.0)) @ Matrix.Rotation(math.radians(kink), 4, "Z"))
    k0, k1 = -Lk, 0.0
    Ek, Dk = covered_terrace(k0, k1, rows=11, podium=1.0, stairs=[k0 + 7, k0 + 17], back_glaze=False)
    K.hip_roof(k0, k1 - 0.01, -0.3, Dk, Ek, 6.0, ov=1.2, mat="tile")
    for i in range(3):                                                  # three steep gables on its front slope
        cx = k0 + 5.0 + i * 7.5
        rise = roof_y("tile", cx - 3.2, cx + 3.2, 0.0, 6.0, Ek, 60, ov=0.5)
        gable_end_y("render", cx - 3.2, cx + 3.2, 0.0, Ek, rise)
        bargeboards(cx - 3.2, cx + 3.2, 0.0, Ek, rise, ov=0.5)
        K.box("glass", cx - 0.8, cx + 0.8, -0.06, 0.0, Ek + 0.6, Ek + 0.6 + rise * 0.38)
    # its open end: a flank wall following the rake (the owner's rule)
    flank_y("render", k0 - 0.5, k0, [(-0.4, -0.5), (-0.4, 1.6), (Dk - 7.0, Ek - 4.0), (Dk - 7.0, Ek), (Dk, Ek), (Dk, -0.5)])
    K.pop()
    # the joint at the kink: a little pavilion roof over the corner
    K.box("render", x0 - 4.0, x0 + 2.0, 4.0, D, -0.5, E)
    K.hip_roof(x0 - 4.5, x0 + 2.5, 3.5, D, E + 0.2, 6.6, ov=0.8, mat="tile_dark")
    reach = Lk * math.cos(math.radians(kink))
    width = L + 16.0 + reach + 1.0
    return {"width": round(width, 1), "depth": round(D + 1.2, 1), "height": round(E + 2.6 + 10.0, 1), "offset": round((16.0 - reach) / 2, 2),
            "kink": {"length": Lk, "degrees": kink, "at": x0, "forward": round(Lk * math.sin(math.radians(kink)), 1)},
            "note": "main stand x %.0f..%.0f; the four-storey block to %.0f; the kink turns %.0f degrees forward at x %.0f and reaches %.1f m along, %.1f m forward"
                    % (x0, x1, x1 + 16, kink, x0, reach, Lk * math.sin(math.radians(kink)))}


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


def wall_terrace(L=32.0):
    """The viewing terrace built against the wall (the owner's photo of the finish): a deck on posts with a white rail,
    and steps rising behind it to the wall top; the wall behind it."""
    x0, x1 = -L / 2, L / 2
    for i in range(4):
        wall_section(x0 + i * L / 4, x0 + (i + 1) * L / 4, buttress=False)
    D0 = -9.0                                                            # the deck's front edge (in front of the wall)
    K.box("concrete", x0, x1, D0, -3.8, 3.2, 3.55)
    for x in [x0 + 1 + i * (L - 2) / 6 for i in range(7)]:
        K.cyl("concrete", x, D0 + 0.6, -0.5, 3.2, 0.28, segs=8)
    K.box("shade", x0 + 0.4, x1 - 0.4, -3.8, -0.1, -0.5, 3.2)             # the dark space under the steps
    K.balustrade(x0, x1, D0 + 0.12, 3.55, h=1.1, mat="trim", spacing=0.28)
    area(x0 + 0.4, x1 - 0.4, D0 + 0.5, -4.2, 3.55)
    # the steps from the deck up to the walkway
    n = 7
    for i in range(n):
        ya, yb = -3.8 + i * (3.8 / n), -3.8 + (i + 1) * (3.8 / n)
        zt = 3.55 + (i + 1) * (WALL_H - 3.55) / n
        K.box("concrete", x0, x1, ya, yb + 0.05, 3.2, zt)
        area(x0 + 0.4, x1 - 0.4, ya + 0.1, yb - 0.1, zt)
    for xa, xb in ((x0 - 0.5, x0), (x1, x1 + 0.5)):                     # brick flank walls following the rake
        flank_y("brick", xa, xb, [(D0 - 0.2, -0.5), (D0 - 0.2, 4.8), (-3.8, 4.8), (0.0, WALL_H + 1.0), (0.0, -0.5)])
    K.balustrade(D0, -3.8, x0 + 0.1, 3.55, h=1.1, mat="trim", spacing=0.3, axis="y")
    K.balustrade(D0, -3.8, x1 - 0.1, 3.55, h=1.1, mat="trim", spacing=0.3, axis="y")
    return {"width": L + 1.0, "depth": WALL_T + 9.2, "height": WALL_H + 1.1, "frontAt": D0,
            "note": "its origin is on the wall's face; the deck runs 9 m in front of it"}


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
    ("chester_wall_terrace", wall_terrace),
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
    wall_y = 24.0
    xs = x + 16
    dup("chester_wall_terrace", xs, wall_y); xw = xs + 16.5
    for i in range(10):
        dup("chester_wall_bay", xw + 4 + i * 8, wall_y)
    for i in range(22):                                                 # the wall behind the stands
        dup("chester_wall_bay", 4 + i * 8, 40)
    bx = 30.0
    for i in range(6):
        dup("chester_terrace_row", bx + i * 44, 52 + (i % 2) * 6)
    dup("chester_city_block", 120, 46); dup("chester_city_block", 260, 40)
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
    shots = [("stands-concept-1", (40, -150, 55), (110, 20, 6), 30),      # from above the infield, like his drone view
             ("stands-concept-2", (40, -60, 9), (95, 10, 7), 30),         # low from the infield: the County Stand
             ("stands-concept-3", (215, -45, 6), (250, 24, 6), 30),
             ("stands-concept-4", (165, -40, 8), (195, 20, 5), 34)]      # the viewing terrace against the wall       # the wall, its terrace and buttresses
    for nm, frm, to, lens in shots:
        cam = bpy.data.objects.new(nm, bpy.data.cameras.new(nm)); cam.data.lens = lens; scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = rp("reference/chester/renders/%s.png" % nm)
        bpy.ops.render.render(write_still=True)
        print("rendered", nm, flush=True)
