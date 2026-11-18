"""Goodwood: a plan of the stand side as built (for the owner to mark up). Reads the race view's files.

    python3 tools/course/goodwood/stand_plan.py      ->  reference/goodwood/renders/stand-side-plan.png
"""
import json, math, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/course/newmarket"))
import to_race_view as NM
A = REPO / "race-view/assets/course"
C = json.loads((A / "goodwood.json").read_text()); S = json.loads((A / "goodwood-scenery.json").read_text())
V = json.loads((A / "goodwood-view.json").read_text())
INFO = json.loads((REPO / "assets/models/architecture/goodwood_stands.json").read_text())["pieces"]
ZW = json.loads((REPO / "reference/goodwood/stands-zones.json").read_text())["world"]

def to_w(x, z, turn, u, v):
    a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    return (x + u * ca - v * sa, z - (u * sa + v * ca))

X0, X1, Z0, Z1 = -160, 690, -120, 235
fig, ax = plt.subplots(figsize=(23.4, 11.4), dpi=110)
ax.set_facecolor("#e7efd9")
for i, ring in enumerate(C["track"]["surface"]):
    p = np.array(ring); ax.fill(p[:, 0], p[:, 1], color="#9cc77f" if i == 0 else "#e7efd9", zorder=1)
for r in C["rails"]["lines"]:
    p = np.array(r); ax.plot(p[:, 0], p[:, 1], color="white", lw=1.6, zorder=2)
for col, L in S["flats"].items():
    for f in L:
        p = np.array(f["pts"])
        if p[:, 0].max() < X0 or p[:, 0].min() > X1 or p[:, 1].max() < Z0 or p[:, 1].min() > Z1: continue
        ax.fill(p[:, 0], p[:, 1], color=col, zorder=2, lw=0)
# the blue zones as he drew them (dashed)
for k, v in ZW.items():
    if k.startswith("festival"):
        p = np.array(v + [v[0]]); ax.plot(p[:, 0], p[:, 1], color="#2b7fb8", lw=1.4, ls="--", zorder=6)
# people (faint), trees, boards
pp = np.array(S["people"]).reshape(-1, 4)
m = (pp[:, 0] > X0) & (pp[:, 0] < X1) & (pp[:, 2] > Z0) & (pp[:, 2] < Z1)
ax.scatter(pp[m, 0], pp[m, 2], s=0.6, color="#8a6f8f", alpha=0.35, lw=0, zorder=3)
t = np.array([[a[0], a[1], a[3]] for a in S["trees"]])
m = (t[:, 0] > X0 - 20) & (t[:, 0] < X1 + 20) & (t[:, 1] > Z0 - 20) & (t[:, 1] < Z1 + 20)
ax.scatter(t[m, 0], t[m, 1], s=(t[m, 2] * 5.5) ** 2, color="#4f7d43", alpha=0.75, lw=0, zorder=4)
for b in S["boards"]:
    x, z, turn = b[0], b[1], math.radians(b[2])
    if not (X0 < x < X1 and Z0 < z < Z1): continue
    ux, uz = math.cos(turn), -math.sin(turn)
    ax.plot([x - ux * 2.6, x + ux * 2.6], [z - uz * 2.6, z + uz * 2.6], color="#c0392b", lw=2.2, zorder=5)
# the pieces: the stands (numbered as his mark-up) and the festival kit
num = {"goodwood_helter_skelter": "HS", "goodwood_balcony": "1  Balcony stand", "goodwood_mast": "2  Mast stand", "goodwood_tent": "3  Tent stand", "goodwood_victorian": "4  Victorian stand"}
kitcol = {"marquee_peaks": "#f4c6c3", "marquee_clearspan": "#f2e3b5", "big_top": "#f7d7a8", "kiosk_row_arched": "#cfe1f2", "kiosk_awning": "#cfe1f2",
          "pagoda_kiosk": "#d9cdf0", "pagoda_counter": "#d9cdf0", "pergola_picnic": "#e8d9c4", "picnic_table": "#b89f7c", "banner_flag": "#6b8fc9",
          "viewing_tower": "#bfbfbf", "balloon_pod": "#f0b8d0", "terrace_deck": "#e0d2b8", "stand_open": "#d6c7a1", "stand_covered": "#c9b98f"}
seen = set()
for model, piece, x, z, turn, sx, sc in S["pieces"]:
    if model == "goodwood_stands":
        pi = INFO[piece]; off = (pi.get("offset", 0.0) or 0.0) * sx; hw = pi["width"] / 2 * sx; d = pi["depth"] * sc
        q = [to_w(x, z, turn, u, v) for u, v in ((off - hw, 0), (off + hw, 0), (off + hw, d), (off - hw, d))]
        ax.add_patch(MP(q, closed=True, fc="#f3efe6", ec="#333", lw=1.6, zorder=7))
        f0, f1 = np.array(q[0]), np.array(q[1]); ax.plot(*np.array([f0, f1]).T, color="#b03a2e", lw=3, zorder=8)   # the front
        c = np.mean(q, axis=0)
        ax.text(c[0], c[1], num[piece] + ("" if piece.endswith("skelter") else "\n%.0f m long" % (pi["width"] * sx)), ha="center", va="center", fontsize=11 if not piece.endswith("skelter") else 7, fontweight="bold", zorder=9)
    elif model == "site_props":
        if not (X0 < x < X1 and Z0 < z < Z1): continue
        w, d = NM.SP_SIZE[piece]; w *= sx * sc; d *= sc
        q = [to_w(x, z, turn, u, v) for u, v in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
        ax.add_patch(MP(q, closed=True, fc=kitcol.get(piece, "#ddd"), ec="#7a6a5a", lw=0.6, zorder=6))
        seen.add(piece)
# the post, the stand camera, labels
ax.plot([0, 0], [-8, 28], color="#c0392b", lw=3, zorder=8); ax.text(0, -12, "winning post", color="#c0392b", ha="center", fontsize=10, zorder=9)
cam = V["raceCameras"]["grandstand"]["at"]
ax.plot(cam[0], cam[2], marker="v", ms=12, color="#1f4e79", zorder=10); ax.text(cam[0] + 5, cam[2] + 7, "stand camera", color="#1f4e79", fontsize=9, zorder=10)
ax.annotate("", xy=(-140, -95), xytext=(-140, -60), arrowprops=dict(arrowstyle="-|>", color="k", lw=1.5))
ax.text(-140, -100, "N", ha="center", fontsize=13, fontweight="bold")
ax.plot([560, 660], [222, 222], color="k", lw=3); ax.text(610, 216, "100 m", ha="center", fontsize=10)
for x in range(-100, 701, 100):
    ax.plot([x, x], [Z1, Z1 - 4], color="#777", lw=0.8); ax.text(x, Z1 - 7, "%d m" % x, ha="center", fontsize=8, color="#777")
ax.text(430, -40, "the straight (horses run right to left)", ha="center", fontsize=11, color="#2f5a24", style="italic")
leg = [("#f3efe6", "stand (red line: its front)"), ("#f4c6c3", "marquee"), ("#f7d7a8", "big top"), ("#cfe1f2", "kiosks"),
       ("#d9cdf0", "pagoda kiosk / counter"), ("#e8d9c4", "pergola"), ("#b89f7c", "picnic table"), ("#6b8fc9", "flag"),
       ("#bfbfbf", "viewing tower"), ("#f0b8d0", "balloon"), ("#d6c7a1", "little stands / terraces"), ("#4f7d43", "tree"), ("#c0392b", "advertising board"),
       ("#8a6f8f", "crowd (dots)"), ("#ddd3a8", "trodden festival ground"), ("#e4d8c2", "stand apron / rail walk")]
for i, (c, lab) in enumerate(leg):
    yy = 122 + i * 6.6
    ax.add_patch(MP([(-150, yy - 2.4), (-141, yy - 2.4), (-141, yy + 2.4), (-150, yy + 2.4)], closed=True, fc=c, ec="#555", lw=0.5, zorder=11))
    ax.text(-137, yy, lab, va="center", fontsize=8.5, zorder=11)
ax.plot([-150, -141], [122 + 16 * 6.6] * 2, color="#2b7fb8", ls="--", lw=1.4); ax.text(-137, 122 + 16 * 6.6, "your blue zones (18 Nov, 00:15)", va="center", fontsize=8.5)
ax.set_xlim(X0, X1); ax.set_ylim(Z1, Z0); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Goodwood: the stand side as built (18 Nov, third pass: your plan mark-up of 12:24), to mark up. Plan, north up, the course along the top. "
             "Metres from the winning post along the straight.", fontsize=12, loc="left")
fig.savefig(REPO / "reference/goodwood/renders/stand-side-plan-2.png", facecolor="white", bbox_inches="tight")
print("ok", sorted(seen))
