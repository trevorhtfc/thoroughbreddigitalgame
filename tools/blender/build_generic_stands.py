"""Small old grandstands for the generic courses (owner, 19 Nov 2026, 17:39-17:41).

    python3.11 -c "exec(open('tools/blender/build_generic_stands.py').read())"           # build and export
    SHEET=1 python3.11 -c "exec(open('tools/blender/build_generic_stands.py').read())"   # also renders of each piece

Owner: "i would also use more of the smaller grandstand and pavillion types as a lot of these seem quite samey? this is a
small pavillion grandstand type you could model. use some of the chester material." (his white model: an open raked
terrace down to the lawn, slim columns carrying a covered first-floor gallery with a criss-cross fretwork balustrade on
bracketed posts, a long hipped roof with boarded cross gables, a belvedere on the ridge with an open lookout and a copper
cupola, a stair down the left flank behind a solid wall on the rake.) Then three photos of smaller courses' old stands
("good examples of smaller courses with old smaller grandstands"): a long low two-storey stand behind a green-posted
veranda with two slatted gables and a raised pavilion box in the middle, a hipped wing beside it; Ripon's stand, open
standing under a deep balcony with flower boxes and a name band, a big slate roof with a raised clerestory box on top; a
white stand with a curved roof, a glazed upper balcony, a two-tier cupola lantern and brick stair walls on the rake. And:
"the intricate roof forms and tv gantries etc really bring them to life".

The pieces (building axes as every kit piece: x along the front, left to right seen from the track; y into the building,
the front faces -y; z up; origin the middle of the front on the ground). Ends follow the owner's rule: a flank wall on
the terraces' rake, never a tower or end block.
  gen_pavilion_stand       his white model (slate roof, boarded gables, copper cupola)
  gen_pavilion_stand_red   the same in Chester's red tile with black-and-white gables
  gen_pavilion_small       a little one: six bays, one cross gable, a cupola
  gen_veranda_stand        photo 1: veranda, glazed floors, slatted gables, the raised pavilion box, a TV gantry
  gen_veranda_wing         photo 1's hipped wing on green posts
  gen_garden_stand         photo 2 (Ripon): open standing, the flower balcony, the big roof and its clerestory box
  gen_cupola_stand         photo 3: the curved roof, the two-tier cupola lantern, brick stair walls, a TV gantry

Writes assets/models/architecture/generic_stands_kit.glb and .json (sizes, crowd areas), and with SHEET=1
reference/generic/renders/stand-<name>.png.
"""
import json, math, os
REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)
exec(open(rp("tools/blender/kit.py")).read())

COL = {   # Chester's palette (build_chester_stands.py) with the white-model and photo colours added
    "render": "#f4ecdf", "trim": "#f7efe2", "white": "#f5f3ee", "timber": "#4d4642", "tile": "#c47a5f", "tile_dark": "#a9664f",
    "brick": "#c98670", "brick_dark": "#b4735f", "steps": "#e6dccb", "seat": "#cf7f74", "glass": "#585b6f", "iron": "#5b6273",
    "slate": "#8f95a8", "slate_pale": "#b9bcc8", "slate_dark": "#6f7383", "copper": "#c9925e", "door": "#7f9f8c",
    "green": "#5f8a6c", "brown": "#7a5646", "band": "#8a5a44", "flower": "#d9798a", "flower_b": "#e7a0b0", "leaf": "#6f9a5e",
    "shade": "#5d5660", "concrete": "#e6d9c4", "louvre": "#e9e2d4",
}
MATS = {k: material("gs_" + k, v, rough=0.9) for k, v in COL.items()}
K = Kit()
CROWD = []


def area(x0, x1, y0, y1, z):
    CROWD.append([round(x0, 2), round(x1, 2), round(y0, 2), round(y1, 2), round(z, 2)])


# ------------------------------------------------------------------------------------------ helpers
def roof_y(mat, x0, x1, y0, y1, z, pitch, ov=0.6, t=0.3, ridge="trim"):
    """A gabled roof with its ridge along y (the gable faces the track, -y); returns the gable's rise at the wall."""
    xc, hw = (x0 + x1) / 2, (x1 - x0) / 2
    rise = (hw + ov) * math.tan(math.radians(pitch))
    K.prism_y(mat, y0 - ov, y1, [(x0 - ov, z), (xc, z + rise), (x1 + ov, z), (x1 + ov, z + t), (xc, z + rise + t), (x0 - ov, z + t)])
    K.box(ridge, xc - 0.14, xc + 0.14, y0 - ov, y1, z + rise + t - 0.05, z + rise + t + 0.14)
    return rise - ov * math.tan(math.radians(pitch))


def gable_face(x0, x1, y, z, rise, fill="render", style="boards"):
    """The gable's triangle at y (facing -y), filled: vertical boards (his model), black-and-white work (Chester) or
    slats (photo 1)."""
    xc, hw = (x0 + x1) / 2, (x1 - x0) / 2
    K.prism_y(fill, y, y + 0.25, [(x0, z), (x1, z), (xc, z + rise)])
    if style == "boards" or style == "slats":
        n = max(4, int((x1 - x0) / (0.55 if style == "slats" else 0.9)))
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            h = rise * (1 - abs(x - xc) / hw) - 0.15
            if h > 0.3:
                K.box("trim" if style == "boards" else "louvre", x - (0.07 if style == "boards" else 0.16), x + (0.07 if style == "boards" else 0.16),
                      y - 0.08, y, z + 0.25, z + h)
        K.box("trim", x0, x1, y - 0.1, y, z, z + 0.3)                                   # the tie beam
    else:                                                                             # half-timber
        K.box("timber", x0, x1, y - 0.06, y, z, z + 0.28)
        for i in range(1, 6):
            x = x0 + (x1 - x0) * i / 6
            h = rise * (1 - abs(x - xc) / hw) - 0.2
            if h > 0.4: K.box("timber", x - 0.11, x + 0.11, y - 0.06, y, z, z + h)
    # bargeboards and a finial
    L = math.hypot(hw + 0.6, rise + 0.6 * rise / hw); a = math.atan2(rise, hw)
    for s in (-1, 1):
        m = Matrix.Translation((xc + s * (hw + 0.6) / 2, y - 0.12, z + rise / 2 + 0.12)) @ Matrix.Rotation(s * a, 4, "Y")
        K.boxm("trim", m, L, 0.12, 0.34)
    K.cyl("trim", xc, y - 0.15, z + rise, z + rise + 1.3, 0.1, 0.04, segs=6)
    K.sphere("trim", xc, y - 0.15, z + rise + 0.35, 0.16, sub=1)


def raked(x0, x1, y0, z0, rows, tread, rise, seat=False, mat="steps"):
    for i in range(rows):
        ya, yb = y0 + i * tread, y0 + (i + 1) * tread
        zt = z0 + (i + 1) * rise
        K.box(mat, x0, x1, ya, yb if i < rows - 1 else yb + 0.3, -0.5, zt)
        if seat: K.box("seat", x0 + 0.1, x1 - 0.1, yb - 0.42, yb - 0.08, zt, zt + 0.42)
        area(x0 + 0.2, x1 - 0.2, ya + 0.15, yb - 0.25, zt)
    return y0 + rows * tread, z0 + rows * rise


def rail_on(x, y0, z0, y1, z1, h=0.95, mat="trim", posts=True):
    """A handrail along a rake from (y0, z0) to (y1, z1) at x, with posts."""
    L = math.hypot(y1 - y0, z1 - z0); a = math.atan2(z1 - z0, y1 - y0)
    m = Matrix.Translation((x, (y0 + y1) / 2, (z0 + z1) / 2 + h)) @ Matrix.Rotation(a, 4, "X")
    K.boxm(mat, m, 0.08, L, 0.08)
    m = Matrix.Translation((x, (y0 + y1) / 2, (z0 + z1) / 2 + h * 0.5)) @ Matrix.Rotation(a, 4, "X")
    K.boxm(mat, m, 0.05, L, 0.05)
    if posts:
        n = max(2, int(L / 1.6))
        for i in range(n + 1):
            k = i / n
            K.box(mat, x - 0.05, x + 0.05, y0 + (y1 - y0) * k - 0.05, y0 + (y1 - y0) * k + 0.05, z0 + (z1 - z0) * k, z0 + (z1 - z0) * k + h)


def fret(x0, x1, y, z, h=1.0, panel=1.1, mat="trim"):
    """The criss-cross fretwork balustrade of his model: rails, posts, an X in every panel."""
    K.box(mat, x0, x1, y - 0.09, y + 0.09, z + h - 0.12, z + h)
    K.box(mat, x0, x1, y - 0.07, y + 0.07, z, z + 0.14)
    n = max(1, round((x1 - x0) / panel)); w = (x1 - x0) / n
    for i in range(n + 1):
        x = x0 + i * w
        K.box(mat, x - 0.06, x + 0.06, y - 0.06, y + 0.06, z, z + h)
    if K.far: return
    d = math.hypot(w, h - 0.26); a = math.atan2(h - 0.26, w)
    for i in range(n):
        xc = x0 + (i + 0.5) * w
        for s in (-1, 1):
            m = Matrix.Translation((xc, y, z + h / 2)) @ Matrix.Rotation(s * a, 4, "Y")
            K.boxm(mat, m, d * 0.92, 0.045, 0.06)


def bracket(x, y, z_top, mat="trim", reach=0.9, drop=0.9):
    """A curved bracket either side of a post under the eaves (two short struts)."""
    for s in (-1, 1):
        for k, (a, b) in enumerate(((0.0, 0.5), (0.45, 1.0))):
            xa, xb = x + s * reach * a, x + s * reach * b
            za, zb = z_top - drop * (1 - a) ** 1.6, z_top - drop * (1 - b) ** 1.6 + 0.02
            L = math.hypot(xb - xa, zb - za)
            m = Matrix.Translation(((xa + xb) / 2, y, (za + zb) / 2)) @ Matrix.Rotation(-s * math.atan2(zb - za, abs(xb - xa)), 4, "Y")
            K.boxm(mat, m, L + 0.05, 0.12, 0.12)


def flank(x0, x1, prof, mat="render"):
    K.prism_x(mat, x0, x1, prof)


def lamp(x, y, z):
    K.cyl("iron", x, y, z - 0.6, z, 0.02, segs=4)
    K.cyl("white", x, y, z - 0.95, z - 0.6, 0.06, 0.32, segs=10)


def gantry(x, y, z, w=3.2, d=2.4, h=2.3, legs=1.6):
    """A TV camera gantry on a roof: a little railed platform on legs with a hooded box and a camera on a tripod."""
    for dx in (-w / 2 + 0.15, w / 2 - 0.15):
        for dy in (0.15, d - 0.15):
            K.box("iron", x + dx - 0.07, x + dx + 0.07, y + dy - 0.07, y + dy + 0.07, z - 0.5, z + legs)
    K.box("iron", x - w / 2, x + w / 2, y, y + d, z + legs, z + legs + 0.15)
    K.balustrade(x - w / 2 + 0.05, x + w / 2 - 0.05, y + 0.08, z + legs + 0.15, h=0.95, mat="iron", spacing=0.5, piers=False)
    K.box("white", x - w / 2 + 0.3, x + w / 2 - 0.3, y + d * 0.45, y + d - 0.1, z + legs + 0.15, z + legs + h)     # the hut
    K.box("glass", x - w / 2 + 0.5, x + w / 2 - 0.5, y + d * 0.45 - 0.03, y + d * 0.45 + 0.01, z + legs + 1.0, z + legs + h - 0.3)
    K.box("trim", x - w / 2 + 0.1, x + w / 2 - 0.1, y + d * 0.35, y + d, z + legs + h, z + legs + h + 0.18)
    K.cyl("iron", x - 0.5, y + 0.6, z + legs + 0.15, z + legs + 1.3, 0.04, segs=4)                                  # camera on its tripod
    K.box("shade", x - 0.75, x - 0.25, y + 0.35, y + 0.95, z + legs + 1.3, z + legs + 1.65)
    K.cyl("iron", x + w / 2 - 0.3, y + d - 0.3, z + legs + h, z + legs + h + 3.5, 0.03, segs=4)                    # an aerial
    for k in range(3):
        K.box("iron", x + w / 2 - 0.9, x + w / 2 + 0.3, y + d - 0.32, y + d - 0.28, z + legs + h + 2.0 + k * 0.5, z + legs + h + 2.04 + k * 0.5)


def flagpole(x, y, z, h=6.0, col="flower"):
    K.cyl("white", x, y, z, z + h, 0.06, 0.04, segs=6)
    K.sphere("copper", x, y, z + h + 0.1, 0.12, sub=1)
    K.box(col, x + 0.05, x + 1.8, y - 0.02, y + 0.02, z + h - 1.25, z + h - 0.15)


def belvedere(xc, yc, z, w=7.2, d=5.0, roof="slate_pale", cup=True):
    """His model's belvedere: a glazed room on the ridge, an open lookout with a fretwork rail on posts under a pyramid
    roof, a little louvred cupola with a copper cap and a tall finial."""
    x0, x1, y0, y1 = xc - w / 2, xc + w / 2, yc - d / 2, yc + d / 2
    K.box("render", x0, x1, y0, y1, z - 1.0, z + 2.6)
    for i in range(6):
        K.window(x0 + w * (i + 0.5) / 6, y0, z + 0.7, w / 6 - 0.35, 1.4)
    K.cornice(x0, x1, y0, y1, z + 2.6, ov=0.5, h=0.3)
    K.hip_roof(x0 - 0.6, x1 + 0.6, y0 - 0.6, y1 + 0.6, z + 2.9, 0.9, ov=0.3, mat=roof)          # the skirt roof over the room
    zl = z + 3.5
    lw, ld = w * 0.78, d * 0.85
    K.box("trim", xc - lw / 2, xc + lw / 2, yc - ld / 2, yc + ld / 2, zl - 0.25, zl)
    for (a, b, yy) in ((xc - lw / 2, xc + lw / 2, yc - ld / 2 + 0.1), (xc - lw / 2, xc + lw / 2, yc + ld / 2 - 0.1)):
        fret(a, b, yy, zl, h=0.9, panel=0.8)
    for xx in (xc - lw / 2 + 0.1, xc + lw / 2 - 0.1):
        K.balustrade(yc - ld / 2, yc + ld / 2, xx, zl, h=0.9, axis="y", spacing=0.4)
    K.box("render", xc - lw / 2 + 1.0, xc + lw / 2 - 1.0, yc - ld / 2 + 1.0, yc + ld / 2 - 1.0, zl, zl + 2.3)       # the lookout's core
    for xx in (xc - lw / 2 + 0.15, xc, xc + lw / 2 - 0.15):
        for yy in (yc - ld / 2 + 0.15, yc + ld / 2 - 0.15):
            K.cyl("trim", xx, yy, zl, zl + 2.5, 0.09, segs=6)
    K.hip_roof(xc - lw / 2, xc + lw / 2, yc - ld / 2, yc + ld / 2, zl + 2.5, 1.7, ov=0.45, mat=roof)
    top = zl + 4.2
    if cup:
        K.box("white", xc - 0.75, xc + 0.75, yc - 0.75, yc + 0.75, top - 0.4, top + 1.3)
        for s in (-1, 1):
            for k in range(4):
                K.box("trim", xc - 0.6, xc + 0.6, yc + s * 0.78 - 0.03, yc + s * 0.78 + 0.03, top + 0.15 + k * 0.28, top + 0.27 + k * 0.28)
        K.hip_roof(xc - 0.75, xc + 0.75, yc - 0.75, yc + 0.75, top + 1.3, 1.1, ov=0.2, mat="copper")
        K.cyl("copper", xc, yc, top + 2.3, top + 4.0, 0.08, 0.02, segs=6)
        K.sphere("copper", xc, yc, top + 2.75, 0.2, sub=1)
        top += 4.0
    return top


# ------------------------------------------------------------------------------------------ 1: his pavilion grandstand
def pavilion_stand(n=10, bay=4.4, roof="slate_pale", gables="boards", centre=True, cross=4, small=False):
    L = n * bay; X0, X1 = -L / 2, L / 2
    # the lawn's low rail in front, then the raked terrace up from the lawn
    for i in range(int(L / 2.2) + 1):
        x = X0 + i * 2.2
        K.box("trim", x - 0.07, x + 0.07, -1.25, -1.1, 0.0, 1.05)
    for zr in (0.45, 0.95):
        K.box("trim", X0, X1, -1.24, -1.12, zr, zr + 0.1)
    K.box("render", X0, X1, 0.0, 0.35, -0.5, 0.55)
    rows = 9 if small else 11
    yt, zt = raked(X0 + 0.05, X1 - 0.05, 0.35, 0.3, rows, 0.78, 0.33)
    for k in range(1, 5 if not small else 3):                          # aisles with handrails both sides
        x = X0 + L * k / (5 if not small else 3)
        for dx in (-0.65, 0.65):
            rail_on(x + dx, 0.35, 0.3, yt - 0.4, zt - 0.1)
    # the concourse behind the terrace, under the gallery, glazed at the back
    yb = yt + 5.0
    K.box("render", X0, X1, yt, yb, -0.5, zt)
    K.screen(X0 + 0.3, X1 - 0.3, yt + 2.2, zt, 2.4, pane=1.4)
    K.box("render", X0, X1, yb - 0.4, yb, zt, 7.0)                     # the back wall up to the gallery
    # the gallery floor on slim columns standing on the terrace
    yf = 5.6 if not small else 4.8
    zf = 6.6 if not small else 5.9
    K.box("render", X0, X1, yf, yb, zf - 0.45, zf)
    K.box("trim", X0 - 0.05, X1 + 0.05, yf - 0.05, yf + 0.25, zf - 0.6, zf - 0.3)
    for i in range(n + 1):
        x = X0 + i * bay
        zc = 0.3 + 0.33 * max(0, min(rows, math.ceil((yf + 0.3 - 0.35) / 0.78)))
        K.cyl("trim", x, yf + 0.3, zc, zf - 0.45, 0.17, 0.15, segs=10)
        K.box("trim", x - 0.25, x + 0.25, yf + 0.05, yf + 0.55, zc, zc + 0.35)
        K.box("trim", x - 0.25, x + 0.25, yf + 0.05, yf + 0.55, zf - 0.75, zf - 0.45)
    # the gallery: fretwork balustrade, bracketed posts, glazing behind, lamps
    ye = zf + 3.3
    fret(X0 + 0.2, X1 - 0.2, yf + 0.1, zf, h=1.0)
    area(X0 + 0.5, X1 - 0.5, yf + 0.4, yf + 2.6, zf)
    for i in range(n + 1):
        x = X0 + i * bay
        K.box("trim", x - 0.11, x + 0.11, yf + 0.2, yf + 0.42, zf, ye)
        if 0 < i < n: bracket(x, yf + 0.31, ye - 0.15, reach=0.9, drop=1.0)
        if i < n: lamp(x + bay / 2, yf + 0.6, ye - 0.15)
    K.box("trim", X0 - 0.1, X1 + 0.1, yf + 0.1, yf + 0.5, ye - 0.25, ye + 0.05)        # the eaves beam
    K.screen(X0 + 0.3, X1 - 0.3, yf + 2.9, zf, ye - zf - 0.3, pane=1.2)
    K.box("render", X0, X1, yf + 2.95, yb, zf, ye)                                    # the rooms behind
    for x0e, x1e in ((X0, X0 + 0.3), (X1 - 0.3, X1)):                                 # the gallery's ends: glazed screens
        K.box("render", x0e, x1e, yf + 0.3, yb, zf, ye)
        for k in range(3):
            K.box("glass", x0e - 0.02, x1e + 0.02, yf + 1.0 + k * 1.6, yf + 2.2 + k * 1.6, zf + 1.1, ye - 0.6)
    # the roof: a long hip, cross gables on its front slope
    K.hip_roof(X0, X1, yf, yb, ye, 5.0 if not small else 4.2, ov=0.75, mat=roof)
    gx = []
    if cross >= 2: gx += [(X0 + 1.15 * bay, 2.3 * bay * 0.5), (X1 - 1.15 * bay, 2.3 * bay * 0.5)]
    if cross >= 4: gx += [(X0 + 3.6 * bay, 1.6 * bay * 0.5), (X1 - 3.6 * bay, 1.6 * bay * 0.5)]
    if cross == 1: gx = [(0.0, 1.8 * bay * 0.5)]
    for xc, hw in gx:
        r = roof_y(roof, xc - hw, xc + hw, yf - 0.4, yf + 4.2, ye, 41 if hw > 4 else 44, ov=0.55)
        gable_face(xc - hw, xc + hw, yf - 0.4, ye, r, style=gables)
    top = ye + 3.4
    if centre and not small:
        top = belvedere(0.0, (yf + yb) / 2 + 0.3, ye + 4.4, roof=roof)
    elif small:                                                          # the little one: a cupola on the ridge
        zc = ye + 3.9
        K.box("white", -0.9, 0.9, (yf + yb) / 2 - 0.9, (yf + yb) / 2 + 0.9, zc - 0.8, zc + 1.6)
        for s in (-1, 1):
            for k in range(4):
                K.box("trim", -0.75, 0.75, (yf + yb) / 2 + s * 0.93 - 0.03, (yf + yb) / 2 + s * 0.93 + 0.03, zc + 0.25 + k * 0.3, zc + 0.37 + k * 0.3)
        K.hip_roof(-0.9, 0.9, (yf + yb) / 2 - 0.9, (yf + yb) / 2 + 0.9, zc + 1.6, 1.2, ov=0.25, mat="copper")
        K.cyl("copper", 0, (yf + yb) / 2, zc + 2.6, zc + 4.2, 0.07, 0.02, segs=6)
        top = zc + 4.2
    # the stair down the left flank behind a solid wall on the rake (his model), the right end a flank on the rake
    sx0, sx1 = X0 - 2.3, X0 - 0.35
    steps = 14
    for i in range(steps):
        ya = -0.6 + (yt - 0.6 + 0.6) * i / steps; yb_ = -0.6 + (yt - 0.6 + 0.6) * (i + 1) / steps
        K.box("steps", sx0, sx1, ya, yb_ + 0.2, -0.5, zt * (i + 1) / steps)
    K.box("steps", sx0, sx1, yt - 0.6, yt + 2.0, -0.5, zt)
    flank(X0 - 2.75, X0 - 2.3, [(-0.9, -0.5), (-0.9, 1.1), (yt, zt + 1.1), (yt + 2.2, zt + 1.1), (yt + 2.2, -0.5)])
    for k in range(6):                                                    # boarding on its face
        K.box("trim", X0 - 2.8, X0 - 2.74, 0.4 + k * (yt - 1.0) / 6, 0.5 + k * (yt - 1.0) / 6, 0.2, 0.25 + (k + 0.5) * zt / 6.5)
    rail_on(X0 - 0.5, -0.6, 0.0, yt - 0.6, zt)
    rail_on(X0 - 2.5, -0.6, 1.1, yt, zt + 1.1, h=0.9)
    flank(X0 - 0.35, X0, [(0.0, -0.5), (0.0, 0.85), (yt, zt + 0.95), (yt + 0.2, zf - 0.45), (yb, zf - 0.45), (yb, -0.5)])
    flank(X1, X1 + 0.35, [(0.0, -0.5), (0.0, 0.85), (yt, zt + 0.95), (yt + 0.2, zf - 0.45), (yb, zf - 0.45), (yb, -0.5)])
    rail_on(X1 + 0.18, 0.0, 0.85, yt, zt + 0.95, h=0.9)
    return {"width": round(L + 3.2, 2), "depth": round(yb + 1.3, 2), "height": round(top, 2), "offset": -1.4}


# ------------------------------------------------------------------------------------------ 2: photo 1's veranda stand
def veranda_stand(L=50.0):
    X0, X1 = -L / 2, L / 2
    D = 13.0
    # the ground floor: glazed behind a veranda of green posts; a low step at the front
    K.box("concrete", X0, X1, -0.4, D, -0.5, 0.35)
    K.screen(X0 + 0.4, X1 - 0.4, 3.2, 0.35, 2.9, pane=1.6)
    K.box("render", X0, X1, 3.25, D, 0.35, 3.6)
    n = int(L / 4.0)
    for i in range(n + 1):
        x = X0 + 0.3 + (L - 0.6) * i / n
        K.box("green", x - 0.12, x + 0.12, 0.05, 0.3, 0.35, 3.55)
        if 0 < i < n: bracket(x, 0.17, 3.5, mat="green", reach=0.7, drop=0.6)
    K.box("white", X0 - 0.2, X1 + 0.2, -0.15, 3.3, 3.55, 3.95)                        # the veranda roof, a balcony on top
    K.box("trim", X0 - 0.25, X1 + 0.25, -0.2, 0.0, 3.4, 4.0)
    K.balustrade(X0 + 0.1, X1 - 0.1, 0.05, 3.95, h=1.0, mat="white", spacing=0.35)
    area(X0 + 0.5, X1 - 0.5, -0.3, 2.9, 0.35); area(X0 + 0.5, X1 - 0.5, 0.4, 3.0, 3.95)
    # the first floor, glazed, under a deep white fascia
    K.screen(X0 + 0.4, X1 - 0.4, 3.35, 3.95, 2.6, pane=1.3)
    K.box("render", X0, X1, 3.4, D, 3.95, 6.7)
    K.box("white", X0 - 0.3, X1 + 0.3, 2.6, D + 0.3, 6.7, 7.3)
    # the hipped slate roof, two big slatted gables on its front, the raised pavilion box in the middle
    K.hip_roof(X0, X1, 2.9, D, 7.3, 3.2, ov=0.5, mat="slate")
    for xc in (X0 + 10.5, X1 - 10.5):
        r = roof_y("slate", xc - 5.2, xc + 5.2, 2.5, 8.5, 7.3, 38, ov=0.5)
        gable_face(xc - 5.2, xc + 5.2, 2.5, 7.3, r, fill="white", style="slats")
    bx0, bx1 = -6.0, 6.0
    K.box("render", bx0, bx1, 2.4, 10.0, 6.5, 10.6)
    K.box("glass", bx0 + 0.5, bx1 - 0.5, 2.35, 2.45, 8.0, 9.8)
    for k in range(9):
        x = bx0 + 0.5 + (bx1 - bx0 - 1.0) * k / 8
        K.box("white", x - 0.06, x + 0.06, 2.3, 2.45, 8.0, 9.8)
    K.box("white", bx0 - 0.3, bx1 + 0.3, 2.1, 10.3, 10.6, 11.0)
    K.hip_roof(bx0, bx1, 2.4, 10.0, 11.0, 2.3, ov=0.6, mat="slate")
    gantry(bx1 - 2.2, 4.0, 13.0, legs=0.8)                                              # the TV gantry on its roof
    flagpole(bx0 + 1.0, 6.0, 13.0, h=5.0)
    # the ends: flank walls (no tower: the owner's rule)
    for xa, xb in ((X0 - 0.35, X0), (X1, X1 + 0.35)):
        flank(xa, xb, [(-0.4, -0.5), (-0.4, 4.0), (2.6, 4.0), (2.6, 7.3), (D, 7.3), (D, -0.5)])
    return {"width": L + 1.4, "depth": D + 0.8, "height": 17.6}


def veranda_wing(L=34.0):
    X0, X1 = -L / 2, L / 2
    D = 11.0
    K.box("concrete", X0, X1, -0.4, D, -0.5, 0.35)
    K.screen(X0 + 0.4, X1 - 0.4, 3.0, 0.35, 4.2, pane=1.5)
    K.box("render", X0, X1, 3.05, D, 0.35, 5.0)
    K.box("white", X0 + 0.2, X1 - 0.2, 2.9, 3.15, 2.5, 2.85)
    K.box("white", X0 + 0.2, X1 - 0.2, 1.2, 3.15, 2.85, 3.0)                                  # a light canopy at mid height
    n = int(L / 4.25)
    for i in range(n + 1):
        x = X0 + 0.3 + (L - 0.6) * i / n
        K.box("green", x - 0.12, x + 0.12, 0.05, 0.3, 0.35, 4.95)
        if 0 < i < n: bracket(x, 0.17, 4.9, mat="green", reach=0.7, drop=0.6)
    area(X0 + 0.5, X1 - 0.5, -0.3, 2.7, 0.35)
    K.box("white", X0 - 0.2, X1 + 0.2, -0.3, D + 0.2, 4.95, 5.5)
    K.hip_roof(X0, X1, -0.1, D, 5.5, 3.6, ov=0.6, mat="slate")
    for xa, xb in ((X0 - 0.3, X0), (X1, X1 + 0.3)):
        flank(xa, xb, [(-0.4, -0.5), (-0.4, 5.0), (D, 5.0), (D, -0.5)])
    for x in (X0 + 8, X1 - 8):                                                            # roof vents
        K.box("slate_dark", x - 0.6, x + 0.6, D * 0.45, D * 0.55, 7.6, 9.4)
        K.hip_roof(x - 0.6, x + 0.6, D * 0.45, D * 0.55, 9.4, 0.5, ov=0.2, mat="slate")
    return {"width": L + 1.2, "depth": D + 0.8, "height": 10.0}


# ------------------------------------------------------------------------------------------ 3: photo 2 (Ripon)
def garden_stand(L=58.0):
    X0, X1 = -L / 2, L / 2
    D = 15.0
    # open standing under the balcony: a few low steps, dark posts, the dark back
    yt, zt = raked(X0 + 0.1, X1 - 0.1, 0.8, 0.15, 7, 0.9, 0.22)
    K.box("brick_dark", X0, X1, 0.0, 0.8, -0.5, 0.5)
    K.box("shade", X0, X1, yt, D, -0.5, 4.4)
    for i in range(10):
        x = X0 + 0.4 + (L - 0.8) * i / 9
        zc = 0.15 + 0.22 * 2
        K.box("brown", x - 0.18, x + 0.18, 2.2, 2.55, zc, 4.6)
    # the balcony: deck, the name band, flower boxes along the rail
    K.box("brown", X0, X1, 1.0, D, 4.45, 4.95)
    K.box("band", X0 - 0.2, X1 + 0.2, 0.9, 1.15, 4.3, 5.6)                                # the fascia band (no name)
    K.box("trim", X0 - 0.2, X1 + 0.2, 0.85, 1.2, 5.6, 5.75)
    K.balustrade(X0 + 0.1, X1 - 0.1, 1.05, 5.75, h=0.85, mat="brown", spacing=0.4)
    import random as _r
    R = _r.Random(5)
    for i in range(int(L / 0.9)):
        x = X0 + 0.5 + i * 0.9
        K.box("leaf", x - 0.42, x + 0.42, 0.7, 1.05, 5.75, 6.05)
        for k in range(3):
            K.sphere("flower" if R.random() < 0.6 else "flower_b", x + R.uniform(-0.35, 0.35), 0.82, 6.12 + R.uniform(0, 0.1), 0.16, sub=0)
    area(X0 + 0.5, X1 - 0.5, 1.5, 4.0, 5.75)
    # the first floor: glazed behind the balcony, posts up to the eaves
    K.screen(X0 + 0.3, X1 - 0.3, 4.2, 5.75, 2.7, pane=1.4)
    K.box("brick", X0, X1, 4.25, D, 5.75, 8.6)
    for i in range(10):
        x = X0 + 0.4 + (L - 0.8) * i / 9
        K.box("brown", x - 0.12, x + 0.12, 1.25, 1.5, 5.75, 8.5)
    # the big roof: a steep lower slope all round, a raised clerestory box with its own hipped roof on top
    K.hip_roof(X0, X1, 0.9, D, 8.5, 4.2, ov=0.7, mat="slate_dark")
    cx0, cx1, cy0, cy1 = -17.0, 17.0, 5.0, 10.5
    K.box("brown", cx0, cx1, cy0, cy1, 10.2, 13.6)
    for k in range(16):
        x = cx0 + 0.9 + (cx1 - cx0 - 1.8) * k / 15
        K.box("glass", x - 0.75, x + 0.75, cy0 - 0.05, cy0 + 0.02, 11.4, 12.9)
    K.box("trim", cx0 - 0.15, cx1 + 0.15, cy0 - 0.2, cy1 + 0.2, 13.6, 13.85)
    K.hip_roof(cx0, cx1, cy0, cy1, 13.85, 1.9, ov=0.7, mat="slate_dark")
    gantry(cx1 - 3.5, cy0 + 0.6, 15.2, legs=0.7)
    for x in (X0 + 5.0, X1 - 5.0):                                                      # chimneys
        K.box("brick", x - 0.6, x + 0.6, D - 3.0, D - 1.8, 9.0, 14.4)
        K.box("brick_dark", x - 0.7, x + 0.7, D - 3.1, D - 1.7, 14.2, 14.6)
    # flank walls in brick on the low steps' rake
    for xa, xb in ((X0 - 0.4, X0), (X1, X1 + 0.4)):
        flank(xa, xb, [(0.0, -0.5), (0.0, 1.0), (yt, zt + 1.0), (yt, 8.6), (D, 8.6), (D, -0.5)], mat="brick")
    return {"width": L + 2.2, "depth": D + 1.4, "height": 19.6}


# ------------------------------------------------------------------------------------------ 4: photo 3, the cupola stand
def cupola_stand(L=50.0):
    X0, X1 = -L / 2, L / 2
    D = 16.0
    # the terrace up from the lawn, the glazed ground floor behind under a canopy
    yt, zt = raked(X0 + 0.1, X1 - 0.1, 0.3, 0.2, 8, 0.8, 0.34)
    for k in (1, 2, 3):
        x = X0 + L * k / 4
        for dx in (-0.6, 0.6): rail_on(x + dx, 0.3, 0.2, yt - 0.3, zt - 0.1)
    K.box("render", X0, X1, yt, D, -0.5, zt)
    K.screen(X0 + 0.5, X1 - 0.5, yt + 1.6, zt, 2.6, pane=1.2)
    K.box("green", X0 + 0.5, X1 - 0.5, yt + 1.5, yt + 1.6, zt + 2.6, zt + 2.75)
    K.box("white", X0, X1, yt - 0.3, yt + 1.7, zt + 2.8, zt + 3.1)                     # the canopy
    K.box("render", X0, X1, yt + 1.6, D, zt, zt + 3.2)
    # the upper balcony, glazed, set back under the curved roof
    zb = zt + 3.1
    K.balustrade(X0 + 0.2, X1 - 0.2, yt - 0.15, zb, h=1.0, mat="white", spacing=0.32)
    area(X0 + 0.5, X1 - 0.5, yt + 0.2, yt + 2.2, zb)
    K.screen(X0 + 0.4, X1 - 0.4, yt + 2.6, zb, 2.9, pane=1.1)
    K.box("render", X0, X1, yt + 2.65, D, zb, zb + 3.0)
    for i in range(9):
        x = X0 + 0.4 + (L - 0.8) * i / 8
        K.box("green", x - 0.11, x + 0.11, yt - 0.05, yt + 0.2, zb, zb + 3.3)
    # the curved roof (photo 3): a bullnose sweeping up from the eaves over the balcony and on up the long slope
    zr = zb + 3.3
    ya, yz = yt - 0.9, D + 0.6
    top_pts, bot_pts = [], []
    for k in range(17):
        t = k / 16
        y = ya + (yz - ya) * t
        z = zr + 5.2 * math.sin(math.pi / 2 * t) ** 0.55
        top_pts.append((y, z + 0.3)); bot_pts.append((y, z))
    K.prism_x("slate_pale", X0 - 0.5, X1 + 0.5, top_pts + bot_pts[::-1])
    K.box("white", X0 - 0.55, X1 + 0.55, ya - 0.15, ya + 0.15, zr - 0.35, zr + 0.25)        # the fascia under the sweep
    for xa, xb in ((X0 - 0.3, X0), (X1, X1 + 0.3)):                                     # the roof's ends closed in
        K.prism_x("render", xa, xb, [(yt + 2.6, zb)] + [(y, z - 0.05) for y, z in bot_pts if y >= yt + 2.6] + [(yz - 0.6, zb)])
    zr_top = zr + 5.2
    # the two-tier cupola lantern on the ridge
    yc = D * 0.55
    zc = zr + 4.6
    K.box("render", -2.4, 2.4, yc - 2.4, yc + 2.4, zc - 1.0, zc + 2.6)
    for s in (-2.4, 2.4):
        for k in range(3):
            K.window(-1.4 + k * 1.4, yc - 2.4, zc + 0.5, 0.8, 1.5)
    K.cornice(-2.4, 2.4, yc - 2.4, yc + 2.4, zc + 2.6, ov=0.4, h=0.3)
    K.hip_roof(-2.6, 2.6, yc - 2.6, yc + 2.6, zc + 2.9, 1.2, ov=0.3, mat="slate")
    K.box("white", -1.3, 1.3, yc - 1.3, yc + 1.3, zc + 3.6, zc + 5.6)
    for s in (-1, 1):
        for k in range(5):
            K.box("trim", -1.1, 1.1, yc + s * 1.33 - 0.03, yc + s * 1.33 + 0.03, zc + 3.85 + k * 0.32, zc + 3.97 + k * 0.32)
    K.cornice(-1.3, 1.3, yc - 1.3, yc + 1.3, zc + 5.6, ov=0.25, h=0.2)
    K.hip_roof(-1.4, 1.4, yc - 1.4, yc + 1.4, zc + 5.8, 1.6, ov=0.2, mat="slate")
    K.cyl("copper", 0, yc, zc + 7.3, zc + 9.6, 0.09, 0.02, segs=6)
    K.sphere("copper", 0, yc, zc + 7.8, 0.22, sub=1)
    # the TV gantry on the roof's slope, flags at the ends
    gantry(X1 - 8.0, D * 0.5, zr + 4.6, legs=1.2)
    for x in (X0 + 3.0, X1 - 3.0): flagpole(x, D - 1.0, zr + 5.2, h=5.0, col="green" if x < 0 else "flower")
    # brick stair walls on the rake at both ends, with steps up them (photo 3)
    for side in (-1, 1):
        xa = X0 - 2.2 if side < 0 else X1 + 0.4
        xw0, xw1 = (X0 - 2.7, X0 - 2.2) if side < 0 else (X1 + 2.2, X1 + 2.7)
        for i in range(10):
            ya, yb_ = 0.0 + yt * i / 10, yt * (i + 1) / 10
            K.box("steps", xa, xa + 1.8, ya, yb_ + 0.2, -0.5, zb * (i + 1) / 10)
        flank(xw0, xw1, [(-0.4, -0.5), (-0.4, 1.2), (yt, zb + 1.2), (D, zb + 1.2), (D, -0.5)], mat="brick")
        K.box("brick_dark", xw0 - 0.08, xw1 + 0.08, D - 0.3, D, zb + 1.2, zb + 1.5)
        flank(X0 - 0.2 if side < 0 else X1, X0 if side < 0 else X1 + 0.2,
              [(0.0, -0.5), (0.0, 0.9), (yt, zt + 0.9), (yt + 0.2, zb), (yt - 0.2, zb + 1.0), (yt + 2.6, zr), (D, zr + 4.0), (D, -0.5)])
    return {"width": L + 5.6, "depth": D + 1.2, "height": round(zc + 9.6, 2)}


# ------------------------------------------------------------------------------------------ build and export
PIECES = [
    ("gen_pavilion_stand", lambda: pavilion_stand()),
    ("gen_pavilion_stand_red", lambda: pavilion_stand(roof="tile", gables="timber")),
    ("gen_pavilion_small", lambda: pavilion_stand(n=6, bay=4.2, cross=1, small=True)),
    ("gen_veranda_stand", veranda_stand),
    ("gen_veranda_wing", veranda_wing),
    ("gen_garden_stand", garden_stand),
    ("gen_cupola_stand", cupola_stand),
]
LIB = bpy.data.collections.new("generic_stands_kit")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
only = os.environ.get("ONLY")
for name, fn in PIECES:
    if only and name not in only.split(","): continue
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-24s %6d triangles, %d crowd areas, %.1f m wide, %.1f m high" % (name, tris, len(CROWD), info["width"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
if not only:
    json.dump({"_about": "Small old grandstands for the generic courses (tools/blender/build_generic_stands.py). Building axes: x along "
                         "the front (left to right from the track), y into the building (front faces -y), z up; origin the middle of "
                         "the front on the ground. crowd: [x0, x1, y0, y1, floor] where spectators stand.",
               "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "generic_stands_kit.json"), "w"), indent=0)
    bpy.ops.object.select_all(action="DESELECT")
    for o in LIB.objects: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "generic_stands_kit.glb"), export_format="GLB", use_selection=True,
                              export_yup=True, export_apply=False, export_animations=False)
    print("exported generic_stands_kit.glb", flush=True)

if os.environ.get("SHEET"):
    for o in list(bpy.data.objects):
        if o.name in ("Cube", "Light", "Camera"): bpy.data.objects.remove(o)
    scene = bpy.context.scene
    world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.78, 0.82, 0.9, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -0.02))
    bpy.context.object.data.materials.append(material("lawn", "#a8c47a"))
    bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
    sun.data.energy = 3.4; sun.data.angle = math.radians(8); sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "20")); scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = int(os.environ.get("RX", "1400")), int(os.environ.get("RY", "800"))
    scene.view_settings.view_transform = "AgX"
    os.makedirs(rp("reference/generic/renders"), exist_ok=True)
    for name, ob in OBJ.items():
        for o in LIB.objects: o.hide_render = o is not ob
        w, h = INFO[name]["width"], INFO[name]["height"]
        dist = max(w * 1.12, h * 2.4)
        frm = Vector((-0.42 * dist, -0.95 * dist, h * 0.42)); to = Vector((w * 0.04, 4.0, h * 0.36))
        cam = bpy.data.objects.new("c_" + name, bpy.data.cameras.new("c_" + name)); cam.data.lens = 38
        scene.collection.objects.link(cam)
        cam.location = frm; cam.rotation_euler = (to - frm).to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
        scene.render.filepath = rp("reference/generic/renders/stand-%s.png" % name)
        bpy.ops.render.render(write_still=True)
        print("rendered", name, flush=True)
