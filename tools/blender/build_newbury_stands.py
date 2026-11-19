"""Newbury's four stands, modelled for the course from the owner's old photos (no kit pieces bolted together).

    python3.11 -c "exec(open('tools/blender/build_newbury_stands.py').read())"
    SHEET=1 python3.11 -c "exec(...)"        # also render them: reference/newbury/renders/stands-sheet.jpg

Owner, 18 Nov 2026, 23:06, after an evening of kit pieces mixed together ("Hmm It's a mess"): asked what was wrong,
"too many mismatched pieces, the layout/plan itself, model it properly instead". His old photos of Newbury's stands
(22:37 and 22:52): left to right a modern glass stand; the main grandstand, a long low covered stand over an open
standing terrace with a white rendered box on its roof (a gable with a clock, a flagpole, railings), a brick block at
one end and a pitched-roof block at the other; and the old two-tier stand with a hipped slate roof, open galleries on
columns, a brick end, and a lookout on posts on its ridge. His plan (22:39-22:51): four stands in four boxes, the
second bent in plan towards the bend. He agreed (23:08) this reading:

  newbury_glass_stand   1  the modern glass stand at the bend: a standing terrace, a balcony, two glazed storeys,
                           a flat roof                                                                     44 m
  newbury_kink_right/left/joint  2  the kinked stand (23:23: "we have a kinked stand from Newmarket? could we not
                           apply that stand to the kink here"): the Rowley Mile's cranked stand, Ascot's grand pavilion
                           behind a lawn terrace on a podium storey, a 49 m run up the course with the TV structure on
                           its roof and a 28 m run the course turns 35 degrees towards the bend; the cream stair drum
                           and a filled wedge where they meet                                         49 + 28 m
  newbury_main_stand    3  the long covered stand: the open terrace under a low canopy on iron columns, an upper
                           stand under a flat roof, the white roof box (gable, clock, flagpole) in the middle, the
                           pitched-roof block at its right-hand end                                         89 m
  newbury_old_stand     4  the old stand: two open galleries over a veranda under a hipped slate roof, a brick end
                           block on the left, the lookout on posts on the ridge near the right-hand end     85 m

One palette for all four (the Rowley Mile's, with the July Course's colours York added): cream render, white paint,
brick, slate, iron. His standing rule (17 Nov): the ends are flank walls on the rake of the terrace, not towers.

Writes assets/models/architecture/newbury_kit.glb and .json (as the other kits: building axes x along the front,
y into the building, front facing -y, z up; origin the middle of the front on the ground; crowd [x0, x1, y0, y1,
floor], or with three more values [.., angle, px, py] for a stretch turned 'angle' degrees about (px, py), the kink).
The course's own pick of them is made by tools/course/real/merge_stands.py newbury (newbury_stands.glb).
"""
import json, math, os

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

# ---- the Rowley Mile build's definitions (kit, palette, Ascot's pieces), without its build loop
_src = open(rp("tools/blender/build_rowley_stands.py")).read()
exec(_src[:_src.index("\nPIECES = [")])
# ---- the July Course's old pavilion and brick block, as written there (the old pavilion under a hipped roof here)
_jsrc = open(rp("tools/blender/build_july_stands.py")).read()
def _july(name):
    a = _jsrc.index("def %s(" % name)
    b = _jsrc.index("\n# ----", a) if "\n# ----" in _jsrc[a:] else len(_jsrc)
    return _jsrc[a:b]
exec(_july("brick_block").split("\n\n\n")[0])
exec(_july("old_pavilion").replace('    rz = gable_x(-half, half, -0.95, D, E, 30, 0.7, roof="slate", wall="paint")',
                                   '    K.hip_roof(-half, half, -0.95, D, E, 3.4, ov=0.7, mat="slate"); rz = E + 3.4'))

EXTRA = {"paint": "#f4e6d0", "deck": "#dcc4a2", "stone": "#f2e4cc", "screen": "#2f3340", "clock_face": "#fbf5ea",
         "clock_dark": "#2a2c30", "flagcloth": "#c9584a", "shade": "#6d7480"}
for k, v in EXTRA.items():
    if k not in MATS:
        COL[k] = v
        MATS[k] = material("nb_" + k, v, rough=0.9)


def turned(fn, angle, px, py):
    """Draw fn() turned 'angle' degrees about (px, py); its crowd areas keep their own axes and carry the turn."""
    n0 = len(CROWD)
    K.push(Matrix.Translation((px, py, 0.0)) @ Matrix.Rotation(math.radians(angle), 4, "Z"))
    fn()
    K.pop()
    for c in CROWD[n0:]:
        c += [angle, px, py]


def lawn_terrace(x0, x1, rows, tread=0.9, rise=0.3, z0=0.3):
    """The open standing terrace from the lawn, its rows' crowd."""
    return steps("steps", x0, x1, 0.0, z0, rows, tread, rise)


def flank(x, side, prof):
    """An end wall on the terrace's rake (his rule), then the building's own end above it."""
    xa, xb = (x - 0.35, x) if side < 0 else (x, x + 0.35)
    K.prism_x("paint", xa, xb, prof)


def iron_columns(x0, x1, y, z0, z1, every=6.0):
    n = max(1, round((x1 - x0) / every))
    for k in range(n + 1):
        x = x0 + 0.3 + (x1 - x0 - 0.6) * k / n
        K.cyl("iron", x, y, z0, z1, 0.11, segs=8)
        K.box("iron", x - 0.35, x + 0.35, y - 0.06, y + 0.06, z1 - 0.5, z1 - 0.35)     # a cross bracket under the beam


def clock(x, y, z, R):
    K.disc_y("trim", x, y + 0.02, y + 0.2, z, R + 0.15, segs=32)
    K.disc_y("clock_dark", x, y - 0.04, y + 0.02, z, R, segs=32)
    K.disc_y("clock_face", x, y - 0.1, y - 0.03, z, R - 0.15, segs=32)
    for h in range(12):
        a = h * math.pi / 6
        K.boxm("clock_dark", Matrix.Translation((x + math.sin(a) * (R - 0.4), y - 0.12, z + math.cos(a) * (R - 0.4))) @ Matrix.Rotation(-a, 4, "Y"),
               0.08 if h % 3 else 0.13, 0.03, 0.3 if h % 3 else 0.42)


def flagpole(x, y, z, h=7.0):
    K.cyl("trim", x, y, z, z + h, 0.09, 0.05, segs=6)
    K.sphere("gilt", x, y, z + h + 0.1, 0.16, sub=1)
    K.box("flagcloth", x + 0.1, x + 2.9, y - 0.03, y + 0.03, z + h - 1.9, z + h - 0.2)


# ------------------------------------------------------------------------------------------ 1: the glass stand
def glass_stand(L=44.0):
    h = L / 2
    yt, zt = lawn_terrace(-h, h, 7, 0.9, 0.35)
    yb, zb, Z1, Z1b, Z2 = yt + 1.4, 3.8, 7.6, 11.4, 15.2          # (23:23: "a floor taller": three glazed storeys)
    Z3 = Z2 + 0.5
    D = 18.0
    K.box("podium", -h, h, yt, D, -1.0, zb - 0.3)                           # the ground storey: doors under the balcony
    for k in range(int(L // 6.0)):
        K.door(-h + 3.0 + k * 6.0, yt, zt + 0.3, 1.6, 2.4)
    K.box("trim", -h - 0.2, h + 0.2, yt - 1.2, yb, zb - 0.3, zb)             # the balcony slab and its glass rail
    K.box("glass", -h, h, yt - 1.15, yt - 1.05, zb, zb + 1.1)
    K.box("trim", -h, h, yt - 1.2, yt - 1.0, zb + 1.1, zb + 1.2)
    area(-h + 0.4, h - 0.4, yt - 0.9, yb - 0.2, zb)
    for za, zc in ((zb, Z1), (Z1, Z1b), (Z1b, Z2)):                           # three glazed storeys, white floor bands
        K.box("wall", -h, h, yb + 0.15, D, za, zc)
        K.screen(-h + 0.1, h - 0.1, yb, za, zc - za - 0.35, pane=1.8)
        K.box("trim", -h - 0.1, h + 0.1, yb - 0.2, yb + 0.1, zc - 0.35, zc)
    K.box("trim", -h - 0.6, h + 0.6, yb - 2.2, D + 0.3, Z2, Z3)              # the flat roof, its deep front edge
    K.box("podium", -h - 0.6, h + 0.6, yb - 2.25, yb - 2.0, Z2 - 0.5, Z3)
    for x in (-h, h):                                                         # flank walls: the rake, then the block's end
        flank(x, -1 if x < 0 else 1, [(-0.2, -1.0), (-0.2, 1.1), (yt, zt + 1.3), (yt, Z2), (D, Z2), (D, -1.0)])
    return {"width": L + 1.2, "depth": D + 0.3, "height": Z3}


# ------------------------------------------------------------------------------------------ 2: the kinked stand
RUN = {"rows": 9, "tread": 0.9, "rise": 0.3, "back": 5.0, "eaves": 7.2, "top": 9.6, "block": 8.8}


def covered_run(x0, x1, ends=(True, True)):
    """The covered stand (his photo): the open terrace under a low slate canopy on iron columns along its front, the
    canopy rising to a rendered block behind with doors onto the terrace top; ends flank walls on the rake."""
    r = RUN
    yt, zt = lawn_terrace(x0, x1, r["rows"], r["tread"], r["rise"])
    yb = yt + r["back"]
    K.box("cream", x0, x1, yt, yb, -1.0, r["block"])                          # the block behind
    for k in range(int((x1 - x0 - 2.0) // 4.5) + 1):
        x = x0 + 2.0 + k * 4.5
        if x < x1 - 1.0:
            K.door(x, yt, zt + 0.3, 1.5, 2.4)
            win(x, yt, zt + 3.4, 1.2, 1.4)
    e, t = r["eaves"], r["top"]
    K.prism_x("slate", x0 - 0.3, x1 + 0.3, [(-0.9, e), (-0.9, e + 0.25), (yb + 0.4, t + 0.25), (yb + 0.4, t)])
    K.box("trim", x0 - 0.3, x1 + 0.3, -1.0, -0.8, e - 0.6, e + 0.25)          # the valance along the canopy's edge
    K.box("shade", x0, x1, -0.6, yb, e + 0.02, e + 0.06)
    iron_columns(x0, x1, -0.4, 0.3, e, 5.6)
    for x, side, on in ((x0, -1, ends[0]), (x1, 1, ends[1])):
        if on:
            flank(x, side, [(-0.6, -1.0), (-0.6, 1.2), (yt, zt + 1.3), (yt, r["block"]), (yb, r["block"]), (yb, -1.0)])
    return yb


def hipped_block(x0, x1, y0, y1, top, rise=3.6):
    brick_block(x0, x1, y0, y1, top, outer=None)
    K.hip_roof(x0, x1, y0, y1, top + 0.35, rise, ov=0.5, mat="slate")
    for x in (x0 + (x1 - x0) * 0.3, x0 + (x1 - x0) * 0.7):                     # chimneys
        K.box("brick", x - 0.5, x + 0.5, (y0 + y1) / 2 - 0.5, (y0 + y1) / 2 + 0.5, top + rise - 1.0, top + rise + 1.4)
    return top + rise + 1.4


def gp_run(bays, rows=12, tread=0.9, rise=0.35, lift=4.0, ends=(True, True), tv=None):
    """One run of the kinked stand (owner, 23:23: "we have a kinked stand from Newmarket? could we not apply that stand
    to the kink here"): the Rowley Mile's cranked stand, Ascot's grand pavilion (the terrace profile under the grand
    canopy with its glazed ridge lantern) behind a lawn terrace, here a floor taller (lift: a podium storey of rooms
    under the pavilion, the lawn terrace rising to meet it). Ends: flank walls on the rake, then the pavilion's end
    wall (his rule). tv: x of the TV structure on its roof. Origin: the middle of the lawn terrace's foot."""
    L, h = bays * BAY, bays * BAY / 2
    T, top = steps("steps", -h, h, 0.0, 0.25, rows, tread, rise)
    T += 0.0
    D = 18.0
    K.box("cream", -h, h, T, T + D, -1.0, lift)                                 # the podium storey
    for k in range(int((L - 2.0) // 3.5) + 1):
        x = -h + 1.75 + k * 3.5
        if x < h - 1.0:
            (K.door if k % 3 == 1 else win)(x, T, top + 0.3 if k % 3 == 1 else top + 0.9, 1.4, 2.3 if k % 3 == 1 else 1.4)
    K.box("trim", -h - 0.2, h + 0.2, T - 0.25, T + 0.1, lift - 0.3, lift)
    K.push(Matrix.Translation((-h, T, lift)))
    canopy_terrace({"x0": 0.0, "x1": L, "depth": D, "party": ()}, grand=True)
    K.pop()
    tt = terrace_top(D) + lift
    for x, side, on in ((-h, -1, ends[0]), (h, 1, ends[1])):
        if on:
            flank(x, side, [(-0.3, -1.0), (-0.3, 1.1), (T, top + 1.3), (T, tt + 1.2), (T + D, tt + 1.2), (T + D, -1.0)])
    H = terrace_top(D) + 9.6 + lift
    if tv is not None:
        tv_structure(tv, T + D * 0.55, H - 2.2)
    return {"width": round(L, 2), "depth": round(T + D + 0.5, 2), "height": round(H + (7.5 if tv is not None else 0.0), 2),
            "section": {"terraceBack": round(T, 2), "lift": lift, "pavilionTop": round(tt, 2), "roof": round(H, 2)}}


def tv_structure(cx, cy, z):
    """The TV structure on the roof (his photos: the camera platform on the old stand's roof): a white boarded box on
    the ridge with windows, a railed platform on its roof, two cameras on tripods looking at the course, an aerial."""
    w, d, hgt = 7.0, 4.2, 3.0
    K.box("paint", cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z, z + hgt)
    for x in (cx - 2.2, cx, cx + 2.2):
        win(x, cy - d / 2, z + 0.9, 1.3, 1.3)
    K.box("trim", cx - w / 2 - 0.5, cx + w / 2 + 0.5, cy - d / 2 - 1.2, cy + d / 2 + 0.3, z + hgt, z + hgt + 0.25)
    K.balustrade(cx - w / 2 - 0.4, cx + w / 2 + 0.4, cy - d / 2 - 1.1, z + hgt + 0.25, h=1.0, mat="iron", spacing=0.3)
    zp = z + hgt + 0.25
    for x in (cx - 1.8, cx + 1.8):                                            # the cameras, on tripods
        for a in (0, 2.1, 4.2):
            K.cyl("iron", x + 0.45 * math.sin(a), cy - 1.6 + 0.45 * math.cos(a), zp, zp + 1.3, 0.035, segs=4, smooth=False)
        K.box("clock_dark", x - 0.3, x + 0.3, cy - 2.4, cy - 1.2, zp + 1.3, zp + 1.85)
        K.box("glass", x - 0.18, x + 0.18, cy - 2.55, cy - 2.4, zp + 1.42, zp + 1.72)
    K.cyl("iron", cx + w / 2 - 0.5, cy + 1.0, zp, zp + 6.5, 0.05, segs=4, smooth=False)   # an aerial
    for k in range(3):
        K.box("iron", cx + w / 2 - 1.2, cx + w / 2 + 0.2, cy + 0.98, cy + 1.02, zp + 4.2 + k * 0.8, zp + 4.26 + k * 0.8)


def kink_joint(depth=29.0, angle=35.0, top=17.0):
    """Where the kinked stand's two runs meet (as the Rowley Mile's cranked stand, his Newmarket): the cream stair drum
    on the front corner, and the wedge between the runs' backs filled in to the roof. Origin: the front corner of the
    kink (the right run's front left corner)."""
    k = math.radians(angle)
    for i in range(int(depth)):                                                # the wedge, in 1 m strips
        y = i + 0.5
        xl = -y * math.tan(k) if y < depth * math.cos(k) else -(depth * math.sin(k)) * (depth - y) / (depth - depth * math.cos(k) + 1e-6)
        if xl < -0.3:
            K.box("cream", xl, 0.0, i, i + 1.0, -1.0, top)
    K.box("trim", -depth * math.sin(k), 0.0, depth * math.cos(k) - 0.6, depth, top, top + 0.3)
    stair_drum(-1.4, 2.6, r=3.4, top=top + 3.0)
    return {"width": round(depth * math.sin(k) + 4.0, 2), "depth": depth, "height": top + 4.2,
            "outline": [[0.0, 0.0], [0.0, depth], [round(-depth * math.sin(k), 2), round(depth * math.cos(k), 2)]]}


# ------------------------------------------------------------------------------------------ 3: the main stand
def main_stand(L=89.0, endblock=18.0, extra=3.6):
    """The long covered stand (his photos): the open terrace under a low canopy on iron columns; behind and above it
    an upper stand of seats under a flat roof people stand on; the white roof box in the middle (a front gable with
    the clock, a flagpole); the pitched-roof block at the right-hand end. Origin: the middle of the front."""
    h = L / 2
    x1 = h - endblock
    yt, zt = lawn_terrace(-h, h, 9, 0.9, 0.3)
    # the lower canopy, from the iron columns up to the upper stand's front
    e = 6.3
    K.prism_x("slate", -h - 0.3, x1, [(-0.9, e), (-0.9, e + 0.25), (yt + 0.2, e + 1.25), (yt + 0.2, e + 1.0)])
    K.box("trim", -h - 0.3, x1, -1.0, -0.8, e - 0.55, e + 0.25)
    K.box("shade", -h, x1, -0.6, yt, e + 0.02, e + 0.06)
    iron_columns(-h, x1, -0.4, 0.3, e, 5.8)
    # the upper stand: a balustraded front, six rows of seats, the back wall, a flat roof on slim columns
    zf, yu = e + 1.25 + extra, yt + 0.2                                       # (23:23: a floor taller: a storey of boxes)
    K.box("cream", -h, x1, yt, yt + 7.4, -1.0, zf)                            # the block under it, doors onto the terrace top
    if extra:
        K.box("trim", -h - 0.3, x1, yt - 0.3, yt + 0.2, e + 1.25, e + 1.55)
        K.screen(-h + 0.2, x1 - 0.2, yt - 0.05, e + 1.55, extra - 0.5, pane=1.8)
    for k in range(int((x1 + h - 2.0) // 4.5) + 1):
        x = -h + 2.0 + k * 4.5
        if x < x1 - 1.0:
            K.door(x, yt, zt + 0.3, 1.5, 2.4)
    K.balustrade(-h, x1, yu + 0.1, zf, h=1.0, mat="trim", spacing=0.3)
    yr, zr = steps("steps", -h, x1, yu + 0.5, zf, 6, 0.95, 0.42)
    yback = yr + 0.6
    zroof = zr + 3.4
    K.box("cream", -h, x1, yr, yback, zf, zroof)
    K.box("trim", -h - 0.3, x1, yu - 0.4, yback + 0.3, zroof, zroof + 0.45)  # the flat roof
    K.box("podium", -h - 0.3, x1, yu - 0.45, yu - 0.2, zroof - 0.4, zroof + 0.45)
    iron_columns(-h, x1, yu + 0.2, zf, zroof, 7.2)
    K.balustrade(-h, x1, yu - 0.1, zroof + 0.45, h=1.0, mat="iron", spacing=0.3)
    area(-h + 0.5, -10.0, yu + 0.3, yu + 3.0, zroof + 0.45)                    # people on the roof, either side of the box
    area(10.0, x1 - 1.0, yu + 0.3, yu + 3.0, zroof + 0.45)
    # the roof box: white render, two rows of windows, a front gable with the clock, a flagpole on the ridge
    bx, by0, by1, bz = 8.5, yu + 3.2, yback, zroof + 0.45
    K.box("paint", -bx, bx, by0, by1, bz, bz + 5.2)
    K.box("trim", -bx - 0.3, bx + 0.3, by0 - 0.3, by1 + 0.3, bz + 5.2, bz + 5.55)
    for x in (-6.0, -3.6, 3.6, 6.0):
        win(x, by0, bz + 0.9, 1.1, 1.5)
        win(x, by0, bz + 3.2, 1.1, 1.3)
    K.door(0.0, by0, bz, 1.6, 2.4)
    rz = gable_y(-3.2, 3.2, by0 - 0.4, by1, bz + 5.2, 38, 0.4, roof="slate", wall="paint")
    clock(0.0, by0 - 0.5, bz + 5.2 + (rz - bz - 5.2) * 0.42, 1.2)
    K.balustrade(-bx - 1.5, bx + 1.5, by0 - 1.2, bz, h=1.0, mat="iron", spacing=0.3)
    flagpole(0.0, (by0 + by1) / 2 + 1.0, rz + 0.2)
    # the pitched-roof block at the right-hand end: cream render, three storeys of windows, gable ends
    K.box("cream", x1, h, yt - 0.4, yback + 1.0, -1.0, zroof)
    for z in (zt + 0.6, zt + 4.2, zt + 7.8):
        for x in (x1 + 3.0, x1 + 6.5, h - 6.5, h - 3.0):
            win(x, yt - 0.4, z, 1.2, 1.8)
    K.door((x1 + h) / 2, yt - 0.4, zt + 0.3, 1.8, 2.7)
    grz = gable_x(x1, h, yt - 0.4, yback + 1.0, zroof, 34, 0.6, roof="slate", wall="cream")
    # the left end: a flank wall on the rake, then the stand's end wall
    flank(-h, -1, [(-0.6, -1.0), (-0.6, 1.2), (yt, zt + 1.3), (yt, zf + 1.0), (yr, zroof), (yback, zroof), (yback, -1.0)])
    flank(h, 1, [(-0.6, -1.0), (-0.6, 1.2), (yt - 0.4, zt + 1.3), (yt - 0.4, -1.0)])
    return {"width": L + 0.7, "depth": round(yback + 1.6, 2), "height": round(max(rz + 7.3, grz + 0.5), 2)}


# ------------------------------------------------------------------------------------------ 4: the old stand
def old_stand(L=76.0, endblock=9.0, levels=3):
    """The old stand (his photos): two open galleries over a veranda under a hipped slate roof (the July Course's old
    pavilion, its roof hipped), a brick end block on the left, the lookout on four posts on the ridge near the right.
    Origin: the middle of the whole front."""
    sh = endblock / 2                                       # the pavilion's middle sits this far right of the whole's
    K.push(Matrix.Translation((sh, 0.0, 0.0)))
    info = old_pavilion(L=L, D=11.0, G=4.2, S=3.9, levels=levels, stair=False, fence=False)
    half, D, E = L / 2, 11.0, 4.2 + levels * 3.9 - 0.25
    ridge = E + 3.4
    # the lookout: four posts up from the ridge, a small boarded hut with windows all round, a balcony rail, a hip roof
    cx, cy, s, zp = half - 9.0, D / 2 - 0.5, 2.4, ridge + 1.6
    for dx in (-s + 0.2, s - 0.2):
        for dy in (-s + 0.2, s - 0.2):
            K.box("trim", cx + dx - 0.12, cx + dx + 0.12, cy + dy - 0.12, cy + dy + 0.12, ridge - 1.2, zp)
    K.box("deck", cx - s - 0.5, cx + s + 0.5, cy - s - 0.5, cy + s + 0.5, zp - 0.2, zp)
    K.balustrade(cx - s - 0.4, cx + s + 0.4, cy - s - 0.4, zp, h=0.9, mat="trim", spacing=0.3)
    K.box("paint", cx - s + 0.4, cx + s - 0.4, cy - s + 0.4, cy + s - 0.4, zp, zp + 2.6)
    for x in (cx - 1.0, cx + 1.0):
        win(x, cy - s + 0.4, zp + 0.9, 0.9, 1.2)
    K.hip_roof(cx - s + 0.4, cx + s - 0.4, cy - s + 0.4, cy + s - 0.4, zp + 2.6, 1.6, ov=0.5, mat="slate")
    K.cyl("iron", cx, cy, zp + 4.2, zp + 6.0, 0.05, segs=4, smooth=False)
    K.pop()
    # the brick end block on the left, the same height as the eaves, under its own hipped roof
    bx1 = -L / 2 + sh - 0.2
    bx0 = bx1 - endblock
    hipped_block(bx0, bx1, 1.0, D + 0.4, E, rise=2.8)
    K.door((bx0 + bx1) / 2, 1.0, 0.0, 1.5, 2.5)
    return {"width": L + endblock, "depth": D + 1.6, "height": round(zp + 6.0, 2)}


# ======================================================================================================================
# The owner's own models (19 Nov, 00:11: "I have made models for you to copy for the main stands... model these as close
# as possible to these"): three sheets, each a three-quarter view, a plan, a roof plan and elevations.
# ======================================================================================================================
def post(x, y, z0, z1, r=0.13, brackets=True, mat="trim", axis_x=True):
    """A slender column with a cap and fretwork brackets either side under the beam."""
    K.cyl(mat, x, y, z0, z1, r, segs=8)
    K.box(mat, x - 0.25, x + 0.25, y - 0.25, y + 0.25, z1 - 0.25, z1)
    if brackets:
        for s_ in (-1, 1):
            K.prism_y(mat, y - 0.05, y + 0.05, [(x, z1 - 0.2), (x + s_ * 1.1, z1 - 0.2), (x, z1 - 1.2)])


def posts(x0, x1, y, z0, z1, every, **kw):
    n = max(1, round((x1 - x0) / every))
    for k in range(n + 1):
        post(x0 + 0.3 + (x1 - x0 - 0.6) * k / n, y, z0, z1, **kw)


def pyramid(cx, cy, w, d, z, rise, spire=4.0, lantern=0.0):
    """A pagoda-like hipped roof (sheet 1): a glazed lantern base, flared eaves, a hip roof to a point, a finial spire."""
    if lantern:
        K.box("paint", cx - w / 2 + 0.6, cx + w / 2 - 0.6, cy - d / 2 + 0.6, cy + d / 2 - 0.6, z, z + lantern)
        K.screen(cx - w / 2 + 0.8, cx + w / 2 - 0.8, cy - d / 2 + 0.55, z + 0.3, lantern - 0.6, pane=1.4)
        z += lantern
    K.box("trim", cx - w / 2 - 0.4, cx + w / 2 + 0.4, cy - d / 2 - 0.4, cy + d / 2 + 0.4, z, z + 0.35)
    K.hip_roof(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z + 0.35, rise, ov=0.9, mat="roof")
    top = z + 0.35 + rise
    K.cyl("trim", cx, cy, top - 0.4, top + 0.6, 0.35, 0.2, segs=8)
    if spire:
        K.cyl("trim", cx, cy, top + 0.6, top + 0.6 + spire, 0.09, 0.03, segs=6)
    return top + 0.6 + spire


# ------------------------------------------------------------------------------------------ sheet 1: the pagoda stand
def pagoda_stand():
    """Sheet 1: the big modern grandstand. In front, stepped terraces with stair flights between railed cheeks and a
    long light canopy on columns with Y brackets; then five storeys of continuous glazing, each under a deep projecting
    floor band (the eaves broadest at the top); an attic storey; five pagoda roofs along the top, the middle one with
    the clock dormer, spires on all; on the left (west) a five-storey block with grid windows, a roof terrace, a
    stair tower, a podium in front. Origin: the middle of the front (the terraces' foot)."""
    X0, XM, X1 = -45.0, -25.0, 45.0
    # the terraces in front of the main block: steps with stair flights between railed cheeks, a rail along the front
    yt, zt = steps("steps", XM, X1, 0.0, 0.3, 10, 0.85, 0.32)
    for c in (-9.0, 9.0, 27.0):
        K.box("podium", c - 1.3, c + 1.3, 0.0, yt, -1.0, 0.3)                       # the flight
        for i in range(10):
            K.box("steps", c - 1.1, c + 1.1, i * 0.85, yt, -1.0, 0.3 + i * 0.32 + 0.16)
        for sx in (-1.3, 1.3):
            K.prism_x("podium", c + sx - 0.15, c + sx + 0.15, [(0.0, -1.0), (0.0, 1.0), (yt, zt + 1.0), (yt, -1.0)])
            rod("iron", c + sx, 0.0, 1.9, yt, zt + 1.9, r=0.05)
    K.balustrade(XM, X1, -0.4, 0.3, h=1.0, mat="iron", spacing=0.3)
    # the canopy: a thin light roof on columns with Y brackets, over the back of the terraces
    zc = 6.8
    K.box("trim", XM - 0.5, X1 + 0.5, 2.0, yt + 1.2, zc, zc + 0.3)
    K.box("glass", XM - 0.5, X1 + 0.5, 1.6, 2.0, zc - 0.5, zc + 0.3)
    n = 7
    for k in range(n + 1):
        x = XM + 1.0 + (X1 - XM - 2.0) * k / n
        zb = 0.3 + min(9, int(3.4 / 0.85)) * 0.32
        K.cyl("trim", x, 3.4, zb, zc - 1.0, 0.2, segs=10)
        for s_ in (-1, 1):
            K.prism_y("trim", 3.3, 3.5, [(x, zc - 1.0), (x + s_ * 2.2, zc), (x + s_ * 1.9, zc), (x, zc - 0.6)])
    # the main block: five glazed storeys behind floor bands that project; the top eaves broadest
    yg = yt + 1.0                                         # the glazing line
    D = yg + 16.0
    K.box("paint", XM, X1, yt, D, -1.0, zt + 0.2)
    K.screen(XM + 0.3, X1 - 0.3, yt + 0.6, zt + 0.2, zc - zt - 0.6, pane=2.2)       # the concourse under the canopy
    levels = [(zc + 0.3, 3.6, 2.0), (zc + 4.6, 3.6, 2.6), (zc + 8.9, 3.6, 2.6), (zc + 13.2, 3.4, 3.4)]
    K.box("paint", XM, X1, yg, D, zc + 0.3, zc + 17.0)
    for z0, hgt, proj in levels:
        K.screen(XM + 0.3, X1 - 0.3, yg - 0.05, z0 + 0.25, hgt - 0.35, pane=1.6)
        area(XM + 1.0, X1 - 1.0, yg - proj + 0.4, yg - 0.3, z0 + 0.1) if proj > 2.1 else None
        zb = z0 + hgt
        K.box("trim", XM - 0.5, X1 + 0.5, yg - proj, yg + 0.3, zb - 0.1, zb + 0.6)     # the floor band above it
        K.box("podium", XM - 0.55, X1 + 0.55, yg - proj - 0.05, yg - proj + 0.15, zb - 0.25, zb + 0.6)
        K.balustrade(XM, X1, yg - proj + 0.3, z0 - 0.1 if z0 > zc + 1 else zb, h=1.0, mat="trim", spacing=0.35) if z0 > zc + 1 else None
    ze = zc + 17.0
    K.box("trim", XM - 1.5, X1 + 1.5, yg - 4.6, D + 0.8, ze, ze + 0.7)             # the deep top eaves
    K.box("podium", XM - 1.55, X1 + 1.55, yg - 4.65, yg - 4.4, ze - 0.2, ze + 0.7)
    # the attic storey, set back, with a row of windows, then the five pagoda roofs
    ya0, ya1, za = yg + 2.0, D - 1.0, ze + 0.7
    K.box("paint", XM + 2.0, X1 - 3.0, ya0, ya1, za, za + 3.2)
    for k in range(int((X1 - XM - 6.0) // 3.0)):
        win(XM + 4.0 + k * 3.0, ya0, za + 0.9, 1.9, 1.4)
    K.box("trim", XM + 1.4, X1 - 2.4, ya0 - 0.6, ya1 + 0.6, za + 3.2, za + 3.6)
    zr = za + 3.6
    cy = (ya0 + ya1) / 2
    tops = []
    for cx, w, rise, lan in ((-20.0, 9.0, 4.4, 2.4), (-4.0, 15.0, 6.5, 0.0), (9.5, 17.0, 7.8, 0.0), (22.0, 15.0, 6.5, 0.0), (32.5, 9.0, 4.4, 2.4)):
        tops.append(pyramid(cx, cy, w, ya1 - ya0 - 1.0, zr, rise, spire=4.5 if w > 10 else 0.0, lantern=lan))
    # the clock dormer on the middle pagoda's front slope
    gz = zr + 2.2
    K.box("paint", 7.3, 11.7, ya0 - 1.2, ya0 + 2.0, zr, gz + 1.4)
    rz = gable_y(7.3, 11.7, ya0 - 1.4, ya0 + 2.0, gz + 1.4, 40, 0.3, roof="roof", wall="paint")
    clock(9.5, ya0 - 1.5, gz + 0.9, 1.2)
    # the west block: five storeys of grid windows, a podium in front, a roof terrace, the stair tower, a chimney
    K.box("paint", X0, XM, 2.0, D - 2.0, -1.0, 4.6)                                  # the podium
    for x in (X0 + 3.0, X0 + 7.0, X0 + 11.0, X0 + 15.0):
        win(x, 2.0, 1.0, 2.0, 2.0)
    K.box("trim", X0 - 0.2, XM + 0.2, 1.8, D - 1.8, 4.6, 5.0)
    K.box("paint", X0 + 3.0, XM, 4.0, D - 2.0, 5.0, 19.5)
    for z in (6.0, 9.4, 12.8, 16.2):
        for k in range(5):
            x = X0 + 4.5 + k * 3.4
            K.window(x, 4.0, z, 2.6, 2.6)
    K.box("trim", X0 + 2.8, XM + 0.2, 3.8, D - 1.8, 19.5, 19.9)
    K.balustrade(X0 + 3.0, XM, 4.1, 19.9, h=1.0, mat="iron", spacing=0.3)
    area(X0 + 3.5, XM - 0.5, 4.4, 9.0, 19.9)
    K.box("paint", X0, X0 + 3.0, 6.0, D - 4.0, -1.0, 24.5)                          # the stair tower
    for z in (6.0, 10.0, 14.0, 18.0):
        win(X0 + 1.5, 6.0, z, 1.0, 2.0)
    K.box("paint", XM - 1.0, XM + 3.0, yg + 4.0, D - 3.0, ze, ze + 6.0)              # the shoulder and its chimney
    K.box("paint", XM + 0.2, XM + 2.0, yg + 6.0, yg + 8.0, ze + 6.0, ze + 9.0)
    # flank: the terraces' rake at the right-hand end, then the block's end
    flank(X1, 1, [(-0.6, -1.0), (-0.6, 1.0), (yt, zt + 1.1), (yt, ze), (D, ze), (D, -1.0)])
    return {"width": X1 - X0 + 3.0, "depth": round(D + 0.8, 2), "height": round(max(tops), 2),
            "section": {"terraceBack": round(yt, 2), "canopy": zc, "eaves": ze, "attic": round(za, 2), "pagodas": round(zr, 2)}}


# ------------------------------------------------------------------------------------------ sheet 2: the kinked stand
SB2 = {"rows": 16, "tread": 0.9, "rise": 0.35, "deckY": 6.6, "deck": 7.4, "urows": 8, "utread": 0.95, "urise": 0.45,
       "back": 15.6, "eaves": 14.6}


def tier_section(x0, x1, roof="hip", ends=(False, False)):
    """Sheet 2's section: the lower terrace from the lawn with a rail along its front; slender posts with brackets up
    to the upper deck, which overhangs the back of the lower terrace; the upper tier of seats behind its balustrade;
    posts again to the eaves; the back wall with windows; a long hipped roof ('hip') or a flat roof with a
    balustrade people stand on ('flat', the links beside the middle pavilion)."""
    r = SB2
    yt, zt = steps("steps", x0, x1, 0.0, 0.6, r["rows"], r["tread"], r["rise"])
    K.balustrade(x0, x1, -0.3, 0.6, h=1.0, mat="trim", spacing=0.3)
    K.box("podium", x0, x1, -0.5, 0.0, -1.0, 0.6)
    yd, zd = r["deckY"], r["deck"]
    zrow = 0.6 + int(yd / r["tread"]) * r["rise"]
    posts(x0, x1, yd + 0.3, zrow, zd - 0.4, 5.2)
    K.box("trim", x0, x1, yd - 0.1, r["back"], zd - 0.4, zd)                         # the upper deck
    K.box("trim", x0, x1, yd - 0.2, yd + 0.1, zd - 0.9, zd)
    K.balustrade(x0, x1, yd + 0.2, zd, h=1.0, mat="trim", spacing=0.3)
    area(x0 + 0.3, x1 - 0.3, yd + 0.4, yd + 1.2, zd)
    yu, zu = steps("steps", x0, x1, yd + 1.3, zd, r["urows"], r["utread"], r["urise"])
    yb = r["back"]
    K.box("paint", x0, x1, yb, yb + 0.4, -1.0, r["eaves"])
    for k in range(int((x1 - x0 - 2.0) // 3.0) + 1):
        x = x0 + 1.5 + k * 3.0
        if x < x1 - 1.0:
            win(x, yb, zu + 0.9, 1.6, 1.3)
    e = r["eaves"]
    if roof == "hip":
        posts(x0, x1, yd + 0.3, zd, e - 0.3, 5.2)
        K.box("trim", x0, x1, yd - 0.2, yd + 0.4, e - 0.7, e - 0.3)
        K.hip_roof(x0, x1, yd - 0.5, yb + 1.2, e - 0.3, 4.2, ov=0.9, mat="roof")
    else:
        posts(x0, x1, yd + 0.3, zd, e - 1.8, 5.2)
        K.box("trim", x0 - 0.2, x1 + 0.2, yd - 0.4, yb + 0.6, e - 1.8, e - 1.4)
        K.balustrade(x0, x1, yd - 0.2, e - 1.4, h=1.0, mat="trim", spacing=0.3)
        area(x0 + 0.3, x1 - 0.3, yd + 0.1, yb, e - 1.4)
    for x, side, on in ((x0, -1, ends[0]), (x1, 1, ends[1])):
        if on:
            flank(x, side, [(-0.5, -1.0), (-0.5, 1.4), (yt, zt + 1.3), (yt, zd), (yb + 0.4, e), (yb + 0.4, -1.0)])
    return yt


def tower(x0, x1, y0, y1, H, rise=4.5):
    """Sheet 2's end towers: five storeys of three-light windows on the front and outer side, a cornice, a pyramid
    roof with a finial, a little balcony at the first floor."""
    K.box("paint", x0, x1, y0, y1, -1.0, H)
    for z in (3.4, 7.0, 10.6, 14.2, 17.8):
        if z + 2.0 < H:
            for x in ((x0 + x1) / 2 - 1.2, (x0 + x1) / 2, (x0 + x1) / 2 + 1.2):
                K.window(x, y0, z, 1.0, 2.0)
    K.box("trim", x0 - 0.3, x1 + 0.3, y0 - 0.3, y1 + 0.3, H, H + 0.5)
    K.box("trim", x0 - 1.0, x1 + 1.0, y0 - 1.6, y0, 2.9, 3.2)
    K.balustrade(x0 - 0.9, x1 + 0.9, y0 - 1.4, 3.2, h=1.0, mat="trim", spacing=0.3)
    K.hip_roof(x0, x1, y0, y1, H + 0.5, rise, ov=0.6, mat="roof")
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    K.box("paint", cx - 0.5, cx + 0.5, cy - 0.5, cy + 0.5, H + rise - 0.6, H + rise + 1.4)
    K.cyl("trim", cx, cy, H + rise + 1.4, H + rise + 3.0, 0.1, 0.03, segs=6)
    return H + rise + 3.0


def kinked_stand2(angle=8.0, angle_r=None, l_link=12.3, l_roof=33.6, r_link=16.4, r_roof=44.5, stair=True, towers=True):
    """Sheet 2: the kinked stand. A middle pavilion (two galleries, a front gable with the clock, a flagpole) square to
    the course; from each side a lower link with a flat balustraded roof, then a long run under a hipped roof and a
    square tower at the end; both sides turned 'angle' degrees about the pavilion's front corners so their ends come
    forward towards the course; an open stair up the right-hand end. Origin: the middle of the pavilion's front."""
    hp = 8.2
    # the middle pavilion
    yt = tier_section(-hp, hp, roof="flat")
    yb = SB2["back"]
    K.box("paint", -hp + 0.6, hp - 0.6, 3.0, yb + 0.4, SB2["eaves"] - 1.4, SB2["eaves"] + 4.6)
    for x in (-5.0, -2.0, 2.0, 5.0):
        K.window(x, 3.0, SB2["eaves"] + 0.4, 1.4, 2.2)
    K.balustrade(-hp + 0.6, hp - 0.6, 3.2, SB2["eaves"] - 1.4, h=1.0, mat="trim", spacing=0.3)
    zg = SB2["eaves"] + 4.6
    K.box("trim", -hp + 0.3, hp - 0.3, 2.7, yb + 0.7, zg, zg + 0.4)
    K.hip_roof(-hp + 0.6, hp - 0.6, 3.0, yb + 0.4, zg + 0.4, 4.0, ov=0.7, mat="roof")
    rz = gable_y(-5.2, 5.2, 2.4, 9.0, zg + 0.4, 38, 0.5, roof="roof", wall="paint")
    clock(0.0, 2.2, zg + 0.4 + (rz - zg - 0.4) * 0.42, 1.3)
    for x in (-hp + 0.6, hp - 0.6):
        K.box("paint", x - 0.5, x + 0.5, 2.6, 3.4, -1.0, zg + 0.4)                    # its corner pilasters
    flagpole(0.0, 8.0, rz + 0.2, h=8.0)
    # the right side: a link, a run under its hipped roof, the tower, the stair
    ar = angle if angle_r is None else angle_r
    r1, r2 = r_link, r_link + r_roof
    def right():
        # (00:36: "the towers suck I'd get rid. Make the terrace continue along the link"): one run each side, the
        # two tiers and the hipped roof straight on from the pavilion to a flank wall at the end
        tier_section(0.0, r2 + (0.0 if towers else 9.0), roof="hip", ends=(False, True)) if not towers else None
        if towers:
            tier_section(0.0, r1, roof="flat")
            tier_section(r1, r2, roof="hip", ends=(False, False))
            tower(r2, r2 + 9.0, 0.5, 13.0, 20.5)
    turned(right, -ar, hp, 0.0)
    # the left side: a link, a run, the tower
    l1, l2 = l_link, l_link + l_roof
    def left():
        if towers:
            tier_section(-l1, 0.0, roof="flat")
            tier_section(-l2, -l1, roof="hip", ends=(False, False))
            tower(-l2 - 10.3, -l2, 0.5, 13.0, 20.5)
        else:
            tier_section(-l2 - 10.3, 0.0, roof="hip", ends=(True, False))
    turned(left, angle, -hp, 0.0)
    RE, LE = r2 + (12.3 if stair and towers else 9.0), l2 + 10.3
    k = math.radians(angle)
    def pt(px, ang, x, y):
        a = math.radians(ang); return [round(px + x * math.cos(a) - y * math.sin(a), 2), round(x * math.sin(a) + y * math.cos(a), 2)]
    outline = [pt(-hp, angle, -LE, 0.0), pt(-hp, angle, 0.0, 0.0), pt(hp, -ar, 0.0, 0.0), pt(hp, -ar, RE, 0.0),
               pt(hp, -ar, RE, 16.0), pt(hp, -ar, 0.0, 16.0), pt(-hp, angle, 0.0, 16.0), pt(-hp, angle, -LE, 16.0)]
    xs = [p[0] for p in outline]
    return {"width": round(max(xs) - min(xs), 2), "depth": 16.4, "height": round(rz + 8.2, 2), "offset": round((max(xs) + min(xs)) / 2, 2),
            "outline": outline, "kink": {"angle": angle, "angleRight": ar, "note": "the left side turned 'angle', the right 'angleRight', about the middle pavilion's front corners"}}


# ------------------------------------------------------------------------------------------ sheet 3: the lookout stand
def lookout_stand(XB=-33.5, X0=-25.5, X1=33.5, tiers=2):
    """Sheet 3: the two-tier stand. A lower terrace behind a picket fence, two stair flights up its middle; slender
    posts with brackets to the upper deck; the upper tier of seats behind a balustrade, a band of multi-pane windows
    in the back wall; posts to the eaves of a long hipped roof; at its left a plain end block with its stair inside; on
    the ridge the lookout: an X-braced trestle, a railed deck, a glazed hut under its own hipped roof.
    Origin: the middle of the front."""
    yt, zt = steps("steps", X0, X1, 0.5, 0.4, 11, 0.8, 0.32)
    for c in (-1.6, 1.6):                                                         # the two middle flights
        K.prism_x("trim", c - 0.12, c + 0.12, [(0.5, 0.4), (0.5, 1.4), (yt, zt + 1.4), (yt, zt + 0.4)])
    K.box("trim", X0 - 0.5, X1 + 0.5, -1.0, -0.9, 0.3, 0.42)                        # the picket fence
    K.box("trim", X0 - 0.5, X1 + 0.5, -1.0, -0.9, 0.85, 0.97)
    x = X0 - 0.4
    while x < X1 + 0.5:
        if abs(x) > 1.4:
            K.box("trim", x - 0.04, x + 0.04, -1.0, -0.9, -0.3, 1.1)
        x += 0.18
    zd, yd = zt + 1.6, yt - 1.2
    zrow = 0.4 + int((yd - 0.5) / 0.8) * 0.32
    posts(X0, X1, yd + 0.3, zrow, zd - 0.4, 4.6)
    K.box("trim", X0 - 0.3, X1 + 0.3, yd - 0.1, yd + 11.0, zd - 0.4, zd)
    K.balustrade(X0, X1, yd + 0.2, zd, h=1.0, mat="trim", spacing=0.3)
    area(X0 + 0.3, X1 - 0.3, yd + 0.4, yd + 1.2, zd)
    yu, zu = steps("steps", X0, X1, yd + 1.3, zd, 8, 0.95, 0.42)
    for t_ in range(tiers - 2):                       # (00:36: "add another tier"): a deck over the tier below, posts, seats
        zd2 = zu + 2.6
        posts(X0, X1, yd + 0.3, zd, zd2 - 0.4, 4.6)
        K.box("trim", X0 - 0.3, X1 + 0.3, yd - 0.1, yu + 0.6, zd2 - 0.4, zd2)
        K.balustrade(X0, X1, yd + 0.2, zd2, h=1.0, mat="trim", spacing=0.3)
        area(X0 + 0.3, X1 - 0.3, yd + 0.4, yd + 1.2, zd2)
        K.box("paint", X0, X1, yu + 0.6, yu + 1.0, zd - 0.4, zd2)
        zd = zd2
        yu, zu = steps("steps", X0, X1, yd + 1.3, zd, 8, 0.95, 0.42)
    yb = yu + 0.6
    e = zu + 3.2
    K.box("paint", X0, X1, yb, yb + 0.4, -1.0, e)
    K.screen(X0 + 1.0, X1 - 1.0, yb - 0.02, zu + 0.4, 1.8, pane=1.0)
    posts(X0, X1, yd + 0.3, zd, e - 0.3, 4.6)
    K.box("trim", X0 - 0.3, X1 + 0.3, yd - 0.2, yd + 0.4, e - 0.7, e - 0.3)
    K.hip_roof(X0 - 0.3, X1 + 0.3, yd - 0.6, yb + 1.0, e - 0.3, 4.0, ov=1.0, mat="roof")
    ridge = e - 0.3 + 4.0
    # the end block on the left, with windows, a parapet, and the stair rising inside its front
    K.box("paint", XB, X0, 0.0, yb + 0.4, -1.0, e + 0.6)
    for z in (1.0, 4.6, 8.2):
        if z + 1.6 < e:
            win(XB + 2.4, 0.0, z, 1.0, 1.6)
    K.box("trim", XB - 0.2, X0 + 0.2, -0.2, yb + 0.6, e + 0.6, e + 0.9)
    for k in range(4):                                                            # the stair's windows climbing its front
        win(XB + 4.4 + k * 1.0, 0.0, 1.2 + k * 1.3, 0.8, 1.0)
    flank(X1, 1, [(-0.9, -1.0), (-0.9, 1.4), (yt, zt + 1.4), (yt, zd), (yb + 0.4, e), (yb + 0.4, -1.0)])
    # the lookout on the ridge: an X-braced trestle, a railed deck, a glazed hut, its hipped roof
    cx, cy = 2.0, (yd + yb) / 2
    w, d, zt0, zt1 = 11.0, 6.0, ridge - 1.2, ridge + 2.0
    for dx in (-w / 2 + 0.8, -w / 6, w / 6, w / 2 - 0.8):
        for dy in (-d / 2 + 0.5, d / 2 - 0.5):
            K.box("trim", cx + dx - 0.15, cx + dx + 0.15, cy + dy - 0.15, cy + dy + 0.15, zt0, zt1)
    for a, b in ((-w / 2 + 0.8, -w / 6), (-w / 6, w / 6), (w / 6, w / 2 - 0.8)):
        for dy in (-d / 2 + 0.5,):
            for s_ in (1, -1):
                L = math.hypot(b - a, zt1 - zt0); ang = math.atan2(zt1 - zt0, b - a) * s_
                K.boxm("trim", Matrix.Translation((cx + (a + b) / 2, cy + dy, (zt0 + zt1) / 2)) @ Matrix.Rotation(-ang, 4, "Y"), L, 0.14, 0.14)
    K.box("deck", cx - w / 2 - 1.2, cx + w / 2 + 1.2, cy - d / 2 - 1.2, cy + d / 2 + 1.2, zt1, zt1 + 0.3)
    K.balustrade(cx - w / 2 - 1.1, cx + w / 2 + 1.1, cy - d / 2 - 1.1, zt1 + 0.3, h=1.0, mat="trim", spacing=0.3)
    K.balustrade(cy - d / 2 - 1.1, cy + d / 2 + 1.1, cx - w / 2 - 1.1, zt1 + 0.3, h=1.0, mat="trim", spacing=0.3, axis="y")
    K.balustrade(cy - d / 2 - 1.1, cy + d / 2 + 1.1, cx + w / 2 + 1.1, zt1 + 0.3, h=1.0, mat="trim", spacing=0.3, axis="y")
    zh = zt1 + 0.3
    K.box("paint", cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, zh, zh + 0.9)
    K.screen(cx - w / 2 + 0.2, cx + w / 2 - 0.2, cy - d / 2 - 0.02, zh + 0.9, 1.6, pane=1.2)
    K.box("paint", cx - w / 2, cx + w / 2, cy - d / 2 + 0.3, cy + d / 2, zh + 0.9, zh + 2.5)
    K.box("trim", cx - w / 2 - 0.3, cx + w / 2 + 0.3, cy - d / 2 - 0.3, cy + d / 2 + 0.3, zh + 2.5, zh + 2.8)
    K.hip_roof(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, zh + 2.8, 2.6, ov=0.8, mat="roof")
    top = zh + 2.8 + 2.6
    K.cyl("trim", cx, cy, top - 0.3, top + 1.4, 0.12, 0.04, segs=6)
    return {"width": X1 - XB + 1.0, "depth": round(yb + 1.4, 2), "height": round(top + 1.4, 2),
            "section": {"terraceTop": round(zt, 2), "deck": round(zd, 2), "eaves": round(e, 2), "ridge": round(ridge, 2)}}



PIECES = [
    ("newbury_glass_stand", glass_stand),
    # 19 Nov 00:11, the owner's own models of the main stands, as close as can be:
    ("newbury_pagoda_stand", pagoda_stand),      # sheet 1: the modern stand, glazed storeys under deep bands, five pagoda roofs
    # sheet 2: the kinked stand, towers at both ends, the clock pavilion at the kink; in his plan's box 2 (00:21: "the kinked
    # stand is number 2 still from this plan"): the right side straight up the course, the left turned 35 towards the bend
    ("newbury_kinked_stand2", lambda: kinked_stand2(35.0, 0.0, 5.0, 12.0, 8.0, 30.6, stair=False, towers=False)),
    ("newbury_lookout_stand", lambda: lookout_stand(-42.5, -34.5, 42.5, tiers=3)),   # 00:36: box 3, another tier    # sheet 3: the two-tier stand with the lookout on its ridge
]
LIB = bpy.data.collections.new("newbury_kit")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = [list(c) for c in CROWD]; info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-22s %6d triangles, %3d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "Newbury's four stands (tools/blender/build_newbury_stands.py), modelled from the owner's old photos. "
                     "Building axes: x along the front (left to right from the track), y into the building (front faces "
                     "-y), z up; origin the middle of the front on the ground (the kinked stand: the middle of its brick "
                     "block's front). crowd: [x0, x1, y0, y1, floor], or [.., angle, px, py] for a stretch turned 'angle' "
                     "degrees about (px, py). outline: the footprint when it is not a rectangle.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "newbury_kit.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "newbury_kit.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported newbury_kit.glb", flush=True)

if os.environ.get("SHEET"):
    REN = rp("reference/newbury/renders"); os.makedirs(REN, exist_ok=True)
    x = 0.0
    for name, _ in PIECES:
        w = INFO[name]["width"]
        OBJ[name].location = (x + w / 2 - INFO[name].get("offset", 0.0), 0, 0)
        x += w + 14
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.82, 0.9, 1)
    bpy.ops.mesh.primitive_plane_add(size=3000, location=(x / 2, 40, 0))
    bpy.context.object.data.materials.append(material("lawn", "#a9c48a"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 4.0; sun.data.angle = math.radians(3); sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "16")); scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.render.image_settings.file_format = "JPEG"; scene.render.image_settings.quality = 90

    def shoot(fname, frm, to, lens, w=2400, hgt=900):
        scene.render.resolution_x, scene.render.resolution_y = w, hgt
        cam = bpy.data.objects.new(fname, bpy.data.cameras.new(fname)); cam.data.lens = lens; cam.data.clip_end = 5000
        scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (Vector(to) - Vector(frm)).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam; scene.render.filepath = os.path.join(REN, fname + ".jpg")
        bpy.ops.render.render(write_still=True)
        print("rendered", fname, flush=True)
    mid = (x - 14) / 2
    shoot("stands-sheet", (mid, -(x - 14) * 0.62, 40), (mid, 10, 6), 30)
    xs = 0.0
    for name, _ in PIECES:
        w = INFO[name]["width"]
        c = xs + w / 2
        shoot("stand-" + name.replace("newbury_", ""), (c + w * 0.55, -w * 0.9, w * 0.32), (c, 6, 7), 32, 1600, 900)
        xs += w + 14
