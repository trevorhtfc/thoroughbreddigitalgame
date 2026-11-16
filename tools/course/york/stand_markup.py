"""York, phase 4 brief: the stand side and the festival side marked up on the plan, against the pieces we already have.

Owner, 16 Nov 2026 (working left to right as seen from the infield, with his photos of York's stands):
  1. Big pavilion: this kind of scale, but made from the old pavilion models.
  2. Smaller, more bitty old pavilions: as Ascot's and the July Course's old pavilions.
  3. Big grandstands x2, including the link between them: not modern in the game, but with their proportions.
  4. The final stand down the end, a lot smaller: the general older stand on the Rowley Mile, furthest from the finish.
  5. Opposite: the festival side, banking up away from the course to the Clock Tower, from the general festival pieces.

    python3 tools/course/york/stand_markup.py      ->  reference/york/stands-markup.png

Drawn in world axes turned so it reads as if standing in the infield looking across at the stands: x along the run-in
(north on the left, the run-in's start on the right), the stands at the top, the infield at the bottom.
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, FancyBboxPatch
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
C = json.loads((REPO / "courses/york-draft.json").read_text())
V = json.loads((REPO / "race-view/assets/course/york.json").read_text())
W = C["trackWidth"]
FOOT = {b["name"]: b["footprint"] for b in C["buildings"]}
P = lambda pts: [[x, -z] for x, z in pts]            # world (x, z) -> drawing (x, up = towards the stands)

INK, MUTED, TURF, GRASS, RAIL = "#2b2b2b", "#6b6b6b", "#86ac5f", "#dfe6c6", "#ffffff"
ZONE = {1: "#c0623a", 2: "#b8954a", 3: "#2f5d8a", 4: "#6a3d9a", 5: "#2f7d4a"}

ZONES = [
    (1, "Big pavilion", ["Melrose Stand"],
     "Old pavilion pieces built up to this scale: the July Course's old\npavilion stacked to 4-5 balconied storeys under one big hipped\nroof (terracotta, muted), Ascot's clock gable in the middle.\nAbout 50 m long, 25-28 m to the ridge. Turned with the top bend."),
    (2, "Smaller old pavilions", ["Gimcrack Stand"],
     "A bitty cluster at mixed heights: the July Course's old pavilion,\nits wing and small pavilion; Ascot's veranda and porch pieces;\nthe Rowley Mile's Victorian pavilion. Lawn terrace in front."),
    (3, "Two big grandstands + link", ["Ebor Stand", "Knavesmire Stand"],
     "York's proportions in our heritage hand: two tall stands (about\n60-70 m each, 5 tiers of balconies) with deep roofs lifted on\nposts, as the Millennium stand at the Rowley Mile; a brick stair\ntower as the link (the Rowley end stand's drum). Standing\nsteps down to the lawn; paved betting ring in front."),
    (4, "Smaller end stand", ["Bustardthorpe Stand"],
     "The Rowley Mile's old stand (the one furthest from the finish):\nterraces under a hipped slate roof, shortened to about 75 m\nand a storey lower. The marquee before it: a three-peak or\nglazed marquee from the festival kit."),
]


def draw():
    fig = plt.figure(figsize=(16, 14), dpi=130)
    ax = fig.add_axes([0.03, 0.30, 0.94, 0.66])
    ax.set_facecolor(GRASS)
    surf = V["track"]["surface"]
    ax.add_patch(MP(P(surf[0]), closed=True, fc=TURF, ec="#4f6f35", lw=0.7))
    for h in surf[1:]: ax.add_patch(MP(P(h), closed=True, fc=GRASS, ec="#4f6f35", lw=0.7))
    for line in V["rails"]["lines"]:
        xs = [p[0] for p in line]; ys = [-p[1] for p in line]
        ax.plot(xs, ys, color=RAIL, lw=1.6)
    # the winning post and the furlong poles
    ax.plot([0, 0], [-2, W + 2], color="#c0392b", lw=2)
    ax.text(0, W + 5, "winning post", color="#c0392b", ha="center", fontsize=8, fontweight="bold")
    for f in V["straightMile"]["furlongPoles"]:
        if f["at"][0] < 300: ax.text(f["at"][0], W + 5, f"{f['furlongs']}f", ha="center", fontsize=7, color=MUTED)
    ax.annotate("", (-210, W / 2), (-120, W / 2), arrowprops=dict(arrowstyle="->", color=INK, lw=1.2))
    ax.text(-165, W / 2 + 4, "running", ha="center", fontsize=7, color=INK)

    # the festival side: from the inside rail up to the Clock Tower, banking up in steps
    fx0, fx1 = -12, 270
    for k, (z0, z1, a) in enumerate([(2, 18, 0.10), (18, 34, 0.17), (34, 50, 0.24), (50, 75, 0.30)]):
        ax.add_patch(MP([[fx0 + 8 * k, -z0], [fx1 - 6 * k, -z0], [fx1 - 6 * k, -z1], [fx0 + 8 * k, -z1]], closed=True,
                        fc=ZONE[5], alpha=a, ec="none"))
        ax.text(fx1 - 6 * k - 4, -(z0 + z1) / 2, f"+{k + 0.5:.1f} m" if k else "rail lawn", ha="right", va="center", fontsize=7, color="#1d4a2c")
    ct = FOOT["Clock Tower"]
    ax.add_patch(MP(P(ct), closed=True, fc="#f3ead2", ec=ZONE[5], lw=1.5))
    cx = sum(p[0] for p in ct) / len(ct); cz = sum(p[1] for p in ct) / len(ct)
    ax.text(cx, -cz - 9, "Clock Tower", ha="center", fontsize=8, fontweight="bold", color="#1d4a2c")
    # schematic rows of white marquees either side of the tower (owner's photo), seating along the rail
    for x0 in (2, 122, 182):
        ax.add_patch(FancyBboxPatch((x0, -46), 50, 7, boxstyle="round,pad=0.5", fc="white", ec="#9aa58a", lw=0.8))
    for x in range(0, 260, 34):
        ax.add_patch(FancyBboxPatch((x, -12), 14, 4, boxstyle="round,pad=0.3", fc="#e9dfc3", ec="#9aa58a", lw=0.6))
    ax.text(-60, -85, "5", fontsize=26, fontweight="bold", color=ZONE[5])
    ax.text(-44, -82, "Festival side: banks up away from the course to the Clock Tower", fontsize=11, fontweight="bold", color=ZONE[5])
    ax.text(-44, -96,
            "Rail crowd and covered/open seating stands along the inside rail (E, F); grassy terraces stepping up behind;\n"
            "long rows of white marquees either side of the tower (A three-peak, B glazed clearspan); a big top (C), terrace decks (G),\n"
            "kiosks (I, K, L), pergolas (M), flags and banners (U, V); bookmakers' boards on the lawn (T). The Clock Tower is new:\n"
            "a tall pavilion with a clock cupola and the big screen (from Ascot's clock gable and the July Course's judge's box).",
            fontsize=8.5, color=INK, va="top")

    # the stands
    for n, title, names, note in ZONES:
        xs, ys = [], []
        for nm in names:
            pts = P(FOOT[nm]); xs += [p[0] for p in pts]; ys += [p[1] for p in pts]
            ax.add_patch(MP(pts, closed=True, fc=ZONE[n], alpha=0.35, ec=ZONE[n], lw=1.4))
        ax.add_patch(FancyBboxPatch((min(xs) - 4, min(ys) - 4), max(xs) - min(xs) + 8, max(ys) - min(ys) + 8,
                                    boxstyle="round,pad=2", fc="none", ec=ZONE[n], lw=1.6, ls=(0, (4, 3))))
        mx = (min(xs) + max(xs)) / 2
        ax.text(mx, max(ys) + 10, str(n), ha="center", fontsize=22, fontweight="bold", color=ZONE[n])
    for nm in ("Knavesmire Marquee", "Weighing Room"):
        ax.add_patch(MP(P(FOOT[nm]), closed=True, fc="#e8dcc0", ec="#8a7350", lw=0.8))
    ax.text(*[sum(c) / len(c) for c in zip(*P(FOOT["Weighing Room"]))], "weighing room\n(parade ring area)", ha="center", va="center", fontsize=6.5, color=MUTED)
    # the lawn and steps in front of the stands
    ax.add_patch(MP([[-60, W + 3], [235, W + 3], [235, W + 20], [-60, W + 20]], closed=True, fc="#c9d9a6", ec="none", alpha=0.7, zorder=0.5))
    ax.text(250, W + 11, "lawn + standing\nsteps, rail crowd", fontsize=7, color=MUTED, va="center")

    # the notes for 1-4, along the top
    for k, (n, title, names, note) in enumerate(ZONES):
        x = -265 + k * 142
        ax.text(x, 205, f"{n}  {title}", fontsize=11, fontweight="bold", color=ZONE[n])
        ax.text(x, 196, f"(OSM: {', '.join(names)})", fontsize=7, color=MUTED)
        ax.text(x, 188, note, fontsize=7.6, color=INK, va="top")
    ax.set_xlim(-270, 305); ax.set_ylim(-125, 215); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("York: the stands and the festival side, marked up against the pieces we have (DRAFT, 16 Nov 2026)\n"
                 "as if standing in the infield looking across at the stands: north on the left; footprints from OpenStreetMap; scale in metres",
                 loc="left", fontsize=12, color=INK)
    ax.plot([190, 290], [120, 120], color=INK, lw=2); ax.text(240, 124, "100 m", ha="center", fontsize=7)

    # the pieces we have, as they look now
    crops = [
        ("reference/newmarket-july/renders/stand.png", (0, 300, 1000, 470), "1, 2: the July Course's old pavilions"),
        ("reference/newmarket/renders/across.png", (220, 170, 1280, 570), "3: the Millennium stand's proportions (Rowley Mile)"),
        ("reference/newmarket/renders/across.png", (0, 300, 300, 480), "4: the Rowley Mile's old stand"),
        ("reference/newmarket/renders/festival.png", (0, 300, 1280, 620), "5: the festival kit"),
    ]
    for i, (f, box, cap) in enumerate(crops):
        a = fig.add_axes([0.03 + i * 0.24, 0.04, 0.225, 0.22])
        im = Image.open(REPO / f).crop(box)
        a.imshow(im); a.set_xticks([]); a.set_yticks([])
        a.set_title(cap, fontsize=9, loc="left", color=INK)
    fig.text(0.03, 0.275, "The pieces we have now (renders from the Newmarket work)", fontsize=10, fontweight="bold", color=INK)
    out = REPO / "reference/york/stands-markup.png"
    fig.savefig(out, facecolor="white"); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    draw()
