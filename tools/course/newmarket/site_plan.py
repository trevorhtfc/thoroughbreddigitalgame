"""Newmarket: the Rowley Mile and the July Course built together, as one site (owner's sketch, 8 Nov 2026).

The owner's sketch of the two courses (reference/newmarket/owner-sketch-zones.png and owner-sketch-arrows.png): the
Cesarewitch leg comes down to a bend where the two courses part. The Rowley Mile turns into its 1m2f straight; the July
Course turns more sharply into its straight mile, which runs off at about 25 degrees to the Rowley Mile's. The Dyke
lies in the wedge between the two straights; each course's grandstands are on the side away from it, so both sets of
stands look across their own track to the Dyke (his blue arrows: the main stand cameras), with each course's festival
area beside its stands, and the July Course's far-side festival in front of the Dyke.

  python3 tools/course/newmarket/site_plan.py

Builds both courses (draft_layout.py, july_layout.py) so neither puts trees, boards or banks on the other, then writes
        courses/newmarket-site.json             where the July Course sits in the Rowley Mile's axes, the Dyke between them,
                                                the stands, festival areas and main stand cameras of both, in one frame
        reference/newmarket/site-plan-draft.png the two courses together, drawn as the owner's sketch, with it beside them

Site axes = the Rowley Mile's: origin = its winning post on the inside rail; its horses run towards -x; +z is the side
of its stands. North is at the bottom of the plans (+z), as in the owner's sketch.
"""
import json, math
from pathlib import Path
import draft_layout as R
import july_layout as J

REPO = Path(__file__).resolve().parents[3]
S_UP = 150.0          # how far up the Cesarewitch leg (beyond the Rowley Mile's bend) the July Course turns off
MARGIN = 10.0         # trees, boards and banks keep this far off the other course's track
DYKE_HEIGHT = 4.0     # the Dyke's top between the two courses (its faces are the courses' own banks)

C, S = math.cos(math.radians(J.SPLAY)), math.sin(math.radians(J.SPLAY))


def place():
    """The July Course's axes in the site's: a turn by SPLAY and an offset, so the July Course's leg lies on the Rowley
    Mile's leg (the same track), with the July bend S_UP metres further up it."""
    lx, lz = J.course_pt(J.STRAIGHT + J.BEND_LEN)[0]                  # where the July bend starts, on the leg
    sx, sz = R.course_pt(R.STRAIGHT + R.BEND_LEN + S_UP)[0]
    return sx - (C * lx - S * lz), sz - (S * lx + C * lz)


TX, TZ = place()


def j2s(x, z):
    return TX + C * x - S * z, TZ + S * x + C * z


def s2j(x, z):
    x, z = x - TX, z - TZ
    return C * x + S * z, -S * x + C * z


def centreline(course_pt, W, d0, d1, to_site=lambda x, z: (x, z)):
    out = []
    d = d0
    while d <= d1:
        (x, z), (tx, tz) = course_pt(d)
        out.append(to_site(x + tz * W / 2, z - tx * W / 2))
        d += 5.0
    return out


R_TRACK = centreline(R.course_pt, R.TRACK_W, -R.RUN_ON - 40, max(R.TRIPS.values()) * R.F + 60)
J_TRACK = centreline(J.course_pt, J.TRACK_W, -J.RUN_ON - 40, J.STRAIGHT + J.BEND_LEN + 40, j2s)   # its leg is the Rowley Mile's


def near_track(track, W, x, z, margin):
    lim = (W / 2 + margin) ** 2
    return any((px - x) ** 2 + (pz - z) ** 2 < lim for px, pz in track)


def skips(d0, d1, pts_at, track, W):
    """Stretches (metres to go) of a bank whose cross-section touches the other course's track."""
    bad = []
    d = d0
    while d <= d1:
        if any(near_track(track, W, x, z, MARGIN) for x, z in pts_at(d)):
            bad.append(d)
        d += 5.0
    out = []
    for d in bad:
        if out and d - out[-1][1] <= 10: out[-1][1] = d
        else: out.append([d, d])
    return [[a - 20, b + 20] for a, b in out]


def main():
    # 1. the Rowley Mile's bank stops where the July Course runs through, inside its bend
    R.BANK_SKIP = R.BANK_SKIP + skips(R.BANK["from"], R.BANK["to"], lambda d: [R.behind(d, o) for o in (R.BANK["foot"], sum(R.BANK["crest"]) / 2, R.BANK["back"])],
                                      J_TRACK, J.TRACK_W)        # (on top of the course's own gaps: the far-side festival)
    # 2. the July Course's Dyke face stops where the Rowley Mile comes close
    J.BANK_SKIP = skips(J.BANK["from"], J.BANK["to"], lambda d: [j2s(*J.far(d, o)) for o in (J.bank_at(d)["foot"], sum(J.bank_at(d)["crest"]) / 2, J.bank_at(d)["back"])],
                        R_TRACK, R.TRACK_W)
    # 3. nothing of one course stands on the other's track
    r_keep = R.KEEP or (lambda x, z: True)                     # the course's own rule too (no trees in its festival)
    R.KEEP = lambda x, z: r_keep(x, z) and not near_track(J_TRACK, J.TRACK_W, x, z, MARGIN)
    J.KEEP = lambda x, z: not near_track(R_TRACK, R.TRACK_W, *j2s(x, z), MARGIN)
    rc, jc = R.main(), J.main()

    # 4. the Dyke's top: between the Rowley Mile's bank crest and the July Course's Dyke face, from beyond both posts to
    #    where the two lines meet up the straights
    r_line = [R.behind(d, sum(R.BANK["crest"]) / 2) for d in range(int(R.BANK["from"]), int(rc["farBank"]["spans"][0][1]) + 1, 10)]
    j_span = jc["dykeFace"]["spans"][0]
    j_line = [j2s(*J.far(d, sum(J.bank_at(d)["crest"]) / 2)) for d in range(int(j_span[0]), int(j_span[1]) + 1, 10)]
    end = j_line[-1]
    k = min(range(len(r_line)), key=lambda i: (r_line[i][0] - end[0]) ** 2 + (r_line[i][1] - end[1]) ** 2)
    dyke = [list(map(lambda v: round(v, 1), p)) for p in r_line[:k + 1] + j_line[::-1]]

    # 5. the two courses' stands, festival areas and main stand cameras in the site's axes
    rect = lambda r, f=lambda x, z: (x, z): [list(map(lambda v: round(v, 1), f(x, z))) for x, z in
                                             [(r["x"][0], r["z"][0]), (r["x"][1], r["z"][0]), (r["x"][1], r["z"][1]), (r["x"][0], r["z"][1])]]
    rs = {"x": R.STANDS["x"], "z": [R.STANDS["front"], R.STANDS["front"] + 34]}
    site = {
        "_about": "Newmarket's two courses in one frame (owner's sketch, 8 Nov 2026), built by tools/course/newmarket/site_plan.py. "
                  "Site axes = the Rowley Mile's (courses/newmarket-draft.json). DRAFT.",
        "compass": "north is at the bottom of the plans (+z), as in the owner's sketch",
        "julyCourse": {"rotate": J.SPLAY, "offset": [round(TX, 2), round(TZ, 2)],
                       "note": "a point (x, z) in the July Course's axes is at (offset.x + x cos r - z sin r, offset.z + x sin r + z cos r) "
                               "in the site's, r = rotate degrees. Its leg is the Rowley Mile's leg; its bend starts %d m further up it." % S_UP},
        "dyke": {"top": dyke, "height": DYKE_HEIGHT,
                 "note": "The Dyke between the two courses (orange in the owner's sketch): a raised band of heath, scrub and trees. Its edges "
                         "are the two courses' own banks: the Rowley Mile's far bank and the July Course's Dyke face."},
        "rowley": {"post": [0, 0], "stands": rect(rs), "festival": rect(R.FESTIVAL),
                   "standCamera": {"at": [0, R.STANDS["front"] + 2, 14], "looks": [0, -1], "note": "across the track to the Dyke"}},
        "july": {"post": list(map(lambda v: round(v, 1), j2s(0, 0))),
                 "stands": [rect(r, j2s) for r in J.stand_rects()],
                 "festival": rect(J.FESTIVAL, j2s), "farFestival": rect(J.far_rect(J.FAR_FESTIVAL), j2s),
                 "standCamera": {"at": list(map(lambda v: round(v, 1), j2s(0, -13.5))) + [13], "looks": [round(-S, 3), round(C, 3)],
                                 "note": "across the track to the far-side festival and the Dyke, from the roof of the judge's box"}},
        "bankSkips": {"rowley": R.BANK_SKIP, "july": J.BANK_SKIP},
    }
    (REPO / "courses/newmarket-site.json").write_text(json.dumps(site, indent=1))
    draw(rc, jc, site)
    print("wrote courses/newmarket-site.json and reference/newmarket/site-plan-draft.png; July post at", site["july"]["post"],
          "; Rowley bank skips", R.BANK_SKIP, "; July Dyke-face skips", J.BANK_SKIP)


# ---------------------------------------------------------------- the drawing, in the owner's own colours
GREEN, PURPLE, YELLOW, ORANGE, RED, BLUE = "#3fae49", "#4b1fb5", "#f5c518", "#f26a1b", "#e3261f", "#1f5fd6"
HEATH, LEAF, INK = "#eef0e2", "#9db58a", "#2b2b2b"


def draw(rc, jc, site):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Circle, FancyArrowPatch
    from PIL import Image
    plt.rcParams["font.family"] = "Inter"
    fig = plt.figure(figsize=(15, 7.4), dpi=100)
    ax = fig.add_axes([0.035, 0.06, 0.64, 0.82]); ax.set_facecolor(HEATH)
    sk = fig.add_axes([0.69, 0.47, 0.30, 0.42]); sk.axis("off")
    sk.imshow(Image.open(REPO / "reference/newmarket/owner-sketch-zones.png")); sk.set_title("your sketch", fontsize=10, loc="left")
    sk2 = fig.add_axes([0.69, 0.03, 0.30, 0.42]); sk2.axis("off")
    sk2.imshow(Image.open(REPO / "reference/newmarket/owner-sketch-arrows.png"))

    poly = lambda pts, **k: ax.add_patch(Polygon(pts, closed=True, **k))
    poly(site["dyke"]["top"], fc=ORANGE, ec="none", alpha=0.55, zorder=1)
    for t in rc["trees"]["list"]:
        ax.add_patch(Circle((t[0], t[1]), 5 * t[3], fc=LEAF, ec="none", zorder=2))
    for t in jc["trees"]["list"]:
        ax.add_patch(Circle(j2s(t[0], t[1]), 5 * t[3], fc=LEAF, ec="none", zorder=2))
    for s0, s1 in rc["farBank"]["spans"]:
        poly([R.behind(d, R.BANK["foot"]) for d in range(int(s0), int(s1), 5)] + [R.behind(d, R.BANK["back"]) for d in range(int(s1) - 5, int(s0) - 1, -5)], fc=ORANGE, ec="none", alpha=0.85, zorder=3)
    for s0, s1 in jc["dykeFace"]["spans"]:
        poly([j2s(*J.far(d, J.bank_at(d)["foot"])) for d in range(int(s0), int(s1), 5)] + [j2s(*J.far(d, J.bank_at(d)["back"])) for d in range(int(s1) - 5, int(s0) - 1, -5)], fc=ORANGE, ec="none", alpha=0.85, zorder=3)
    # the tracks
    def track(course_pt, W, d0, d1, f=lambda x, z: (x, z)):
        a, b = [], []
        d = d0
        while d <= d1:
            (x, z), (tx, tz) = course_pt(d)
            a.append(f(x, z)); b.append(f(x + tz * W, z - tx * W)); d += 5
        poly(a + b[::-1], fc=GREEN, ec="white", lw=0.8, zorder=5)
    track(R.course_pt, R.TRACK_W, -R.RUN_ON, max(R.TRIPS.values()) * R.F)
    track(J.course_pt, J.TRACK_W, -J.RUN_ON, J.STRAIGHT + J.BEND_LEN + 10, j2s)
    # stands and festival areas
    for r in [site["rowley"]["stands"]] + site["july"]["stands"]:
        poly(r, fc=PURPLE, ec="none", zorder=6)
    for r in [site["rowley"]["festival"], site["july"]["festival"], site["july"]["farFestival"]]:
        poly(r, fc=YELLOW, ec="none", zorder=4, alpha=0.95)
    # the posts
    for p in (site["rowley"]["post"], site["july"]["post"]):
        ax.add_patch(Circle(p, 22, fc="white", ec=RED, lw=2, zorder=8))
    # direction of travel (red) and the main stand cameras (blue)
    def run_arrow(course_pt, W, d0, d1, f=lambda x, z: (x, z)):
        pts = []
        d = d1
        while d >= d0:
            (x, z), (tx, tz) = course_pt(d)
            pts.append(f(x + tz * W / 2, z - tx * W / 2)); d -= 20
        ax.plot(*zip(*pts[:-1]), color=RED, lw=2.2, zorder=7, solid_capstyle="round")
        ax.add_patch(FancyArrowPatch(pts[-4], pts[-1], arrowstyle="-|>", mutation_scale=20, color=RED, lw=2.2, zorder=7))
    run_arrow(R.course_pt, R.TRACK_W, 50, 16 * R.F)
    run_arrow(J.course_pt, J.TRACK_W, 50, J.STRAIGHT + J.BEND_LEN + 300, j2s)
    for key in ("rowley", "july"):
        cam = site[key]["standCamera"]; (x, z), (lx, lz) = cam["at"][:2], cam["looks"]
        sx, sz = x - lx * 330, z - lz * 330
        ax.add_patch(FancyArrowPatch((sx, sz), (x - lx * 40, z - lz * 40), arrowstyle="-|>", mutation_scale=24, color=BLUE, lw=4, zorder=9))
    # labels
    ax.text(1300, R.TRACK_W + 70, "The Rowley Mile", fontsize=11, color="#23752c", ha="center", va="center", zorder=9, fontweight="bold")
    mx, mz = j2s(1150, -95)
    ax.text(mx, mz, "The July Course", fontsize=11, color="#23752c", ha="center", va="center", rotation=-J.SPLAY, rotation_mode="anchor", zorder=9, fontweight="bold")
    dx = sum(p[0] for p in site["dyke"]["top"]) / len(site["dyke"]["top"]); dz = sum(p[1] for p in site["dyke"]["top"]) / len(site["dyke"]["top"])
    ax.text(dx, dz, "the Dyke", fontsize=12, color=INK, ha="center", va="center", zorder=9)
    lab = dict(fontsize=9, color=INK, zorder=9)
    ax.text(-60, R.STANDS["front"] + 80, "Rowley stands", ha="center", **lab)
    ax.text(sum(R.FESTIVAL["x"]) / 2, R.FESTIVAL["z"][1] + 45, "Rowley festival", ha="center", **lab)
    jx, jz = j2s(140, -J.STAND_BACK - 75); ax.text(jx, jz, "July stands", ha="center", **lab)
    jx, jz = j2s(sum(J.FESTIVAL["x"]) / 2, -95); ax.text(jx, jz, "July festival", ha="center", **lab)
    jx, jz = j2s(280, J.TRACK_W + 140); ax.text(jx, jz, "July far-side festival", ha="center", va="center", fontsize=8.5, color=INK, zorder=9, rotation=-J.SPLAY)
    # the compass: north at the bottom, as the sketch
    cx_, cz_ = -500, -1500
    ax.add_patch(Circle((cx_, cz_), 110, fc="white", ec=INK, lw=1.2, zorder=9))
    ax.add_patch(FancyArrowPatch((cx_, cz_ - 60), (cx_, cz_ + 85), arrowstyle="-|>", mutation_scale=16, color=INK, lw=1.6, zorder=10))
    ax.text(cx_ + 30, cz_ - 10, "N", fontsize=13, fontweight="bold", color=INK, zorder=10)
    ax.set_aspect("equal"); ax.invert_yaxis()
    ax.set_xlim(-650, 3250); ax.set_ylim(420, -1900); ax.tick_params(labelsize=7, colors="#888")
    ax.set_title("Newmarket's two courses together (metres; north at the bottom, as your sketch). Purple: stands; yellow: festival areas;\n"
                 "orange: the Dyke; red: the way they run to each finish; blue: each course's main stand camera", fontsize=10.5, loc="left", color=INK)
    fig.savefig(REPO / "reference/newmarket/site-plan-draft.png")


if __name__ == "__main__":
    main()
