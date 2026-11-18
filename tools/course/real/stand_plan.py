"""A tier 2 course's stand side as built, as a plan for mark-up (Goodwood's stand_plan.py made general).

Owner, 18 Nov 2026 (19:02), on Doncaster: "a plan drawing of the grandstand area". Drawn from what the race view
places (race-view/assets/course/<id>.json and -scenery.json) and the stands' sizes (assets/models/architecture/
<id>_stands.json): the track and its rails, the post and the furlong poles, every stand's footprint with its name and
width, the paved walk, the crowds (dots), the boards and the run-in's hoardings, the trees, the plot kept for the stands
and the run-in's infield kept for the festival; a 50 m grid (numbered: metres up the course from the post, and metres
from the inside rail) so marks can be read back to the model.

  python3 tools/course/real/stand_plan.py <id>     ->  reference/<id>/stand-side-plan.png
"""
import json, math, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP

REPO = Path(__file__).resolve().parents[3]
INK, MUTED, POSTC = "#2b2b2b", "#6b6b6b", "#c0392b"
NAMES = {"ring_pavilion": "Ring pavilion (Rowley Mile)", "york_stand_north": "North stand (York): modern cantilever",
         "york_clock_tower": "Clock tower (York)", "park_roof_terrace_stand": "Roof-terrace stand (Park kit)",
         "victorian_stand": "Victorian stand (Rowley Mile)", "old_pavilion": "Old pavilion (July Course)",
         "park_tiered_stand": "Tiered stand (Park kit), turned to the bend", "park_balcony_stand_clock": "Balcony stand with a clock tower (Park kit)",
         "park_gable_stand": "Pitched-roof stand (Park kit)", "park_balcony_stand": "Balcony stand (Park kit)"}


def footprint(gi, x, z, turn):
    """the piece's outline on the ground (world x, z): building axes u along the front, v into the building"""
    a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    def w(u, v): return (x + u * ca - v * sa, z - (u * sa + v * ca))
    D = gi["depth"]
    k = gi.get("kink")
    if k:          # York's north stand: a right run along the front and a left run turned towards the course
        r, (lx, ly) = k["right"], k["leftEnd"]
        L = math.hypot(lx, ly); nx, ny = -ly / L, lx / L          # into the building from the left run's front
        if ny < 0: nx, ny = -nx, -ny
        return [w(lx, ly), w(0, 0), w(r, 0), w(r, D), w(0, D), w(lx + nx * D, ly + ny * D)]
    o, hw = gi.get("offset", 0.0), gi["width"] / 2
    return [w(o - hw, 0), w(o + hw, 0), w(o + hw, D), w(o - hw, D)]


def main(cid):
    C = json.loads((REPO / f"race-view/assets/course/{cid}.json").read_text())
    S = json.loads((REPO / f"race-view/assets/course/{cid}-scenery.json").read_text())
    CF = json.loads((REPO / f"tools/course/real/{cid}.json").read_text())
    info = json.loads((REPO / f"assets/models/architecture/{cid}_stands.json").read_text())["pieces"] if CF.get("stands") else {}
    W = C["trackWidth"]; side = -1 if C["hand"] < 0 else 1
    X0, X1 = -230, 520
    Z0, Z1 = (-340, 230) if side < 0 else (-230, 340)
    fig, ax = plt.subplots(figsize=(16.5, 11.7), dpi=130)                    # A3 landscape
    ax.set_facecolor("#eef2e4")
    inview = lambda x, z: X0 - 20 <= x <= X1 + 20 and Z0 - 20 <= z <= Z1 + 20
    # the turf and the rails
    surf = C["track"]["surface"]
    ax.add_patch(MP(np.array(surf[0]), closed=True, fc="#9cc184", ec="none", zorder=1))
    for h in surf[1:]: ax.add_patch(MP(np.array(h), closed=True, fc="#eef2e4", ec="none", zorder=1.1))
    for ln in C["rails"]["lines"]:
        q = np.array(ln); ax.plot(q[:, 0], q[:, 1], color="white", lw=1.3, zorder=2)
    # the plot kept for the stands, and the run-in's infield kept for the festival
    zr = side * (W + 0.5)
    ax.add_patch(MP(np.array([(-150, zr), (450, zr), (450, zr + side * 260), (-150, zr + side * 260)]), closed=True, fc="none",
                    ec="#8a7350", lw=1.0, ls=(0, (6, 4)), zorder=1.5))
    ax.text(445, zr + side * 254, "the plot kept for the stands", ha="right", va="bottom" if side > 0 else "top", fontsize=8, color="#8a7350")
    home = C["routes"][C["defaultRoute"]]["path"]["home"]
    ax.add_patch(MP(np.array([(-150, 0), (home + 60, 0), (home + 60, -side * 170), (-150, -side * 170)]), closed=True,
                    fc="#f6e9c9", ec="#c49a3c", lw=1.0, ls=(0, (6, 4)), alpha=0.55, zorder=1.2))
    ax.text(150, -side * 150, "the run-in's infield, kept open for the festival zone", ha="center", fontsize=9, color="#8a6a1c", style="italic", zorder=3)
    # paved walk, trees, boards, people
    for col, fl in S.get("flats", {}).items():
        for f in fl:
            q = np.array(f["pts"]); ax.add_patch(MP(q, closed=True, fc=col, ec="none", zorder=2.2))
    for t in S["trees"]:
        if inview(t[0], t[1]): ax.add_patch(plt.Circle((t[0], t[1]), 3.6 * t[3], fc="#6f9a55", ec="#4f7a3a", lw=0.3, alpha=0.85, zorder=2.5))
    for b in S["boards"]:
        if not inview(b[0], b[1]): continue
        w = 6.0 * b[4] / 1.4 * (1.0 if b[4] <= 1.5 else 1.0)
        a = math.radians(b[2]); dx, dz = math.cos(a) * w / 2, -math.sin(a) * w / 2
        big = b[4] > 1.5
        ax.plot([b[0] - dx, b[0] + dx], [b[1] - dz, b[1] + dz], color="#1f3d5a" if big else "#3d5a75", lw=3.2 if big else 1.6, solid_capstyle="butt", zorder=3)
    P = np.array(S["people"]).reshape(-1, 4)
    m = (P[:, 0] > X0) & (P[:, 0] < X1) & (P[:, 2] > Z0) & (P[:, 2] < Z1)
    ax.scatter(P[m, 0], P[m, 2], s=0.25, c="#a0522d", alpha=0.45, lw=0, zorder=3.2)
    # the stands
    key = []
    for model, piece, x, z, turn, sx, sc in S["pieces"]:
        if piece not in info: continue
        gi = info[piece]; fp = footprint(gi, x, z, turn)
        ax.add_patch(MP(np.array(fp), closed=True, fc="#f4efe6", ec="#5a4a32", lw=1.1, alpha=0.93, zorder=4))
        cx = np.mean([p[0] for p in fp]); cz = np.mean([p[1] for p in fp])
        n = len(key) + 1
        ax.add_patch(plt.Circle((cx, cz), 6.5, fc="#5a4a32", ec="white", lw=0.8, zorder=5))
        ax.text(cx, cz, str(n), ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=6)
        xs = [p[0] for p in fp]
        key.append(f"{n}  {NAMES.get(piece, piece)}: {gi['width']:.0f} m wide, {gi['depth']:.0f} m deep, x {min(xs):.0f} to {max(xs):.0f}")
        ax.plot(x, z, marker="+", color="#5a4a32", ms=6, zorder=5)
    if key:
        kz = side * (W + 0.5 + 95)
        ax.text(-140, kz, "The stands (from past the post up the course)\n" + "\n".join(key), fontsize=8.5, color=INK, va="bottom" if side < 0 else "top",
                linespacing=1.55, zorder=6, bbox=dict(fc="white", ec="#8a7350", lw=0.8, pad=6))
    # the post, furlong poles, direction of running
    ax.plot(0, 0, marker="o", ms=9, color=POSTC, mec="white", zorder=6)
    ax.annotate("winning post", (0, 0), xytext=(-10, 14 * -side), textcoords="offset points", fontsize=9, color=POSTC, fontweight="bold", ha="right", zorder=6)
    for p in S["poles"]:
        x, z = p["at"]; ax.plot(x, z, marker="s", ms=4, color=INK, zorder=6)
        ax.annotate(f"{p['furlongs']}f", (x, z), xytext=(3, 5 * side), textcoords="offset points", fontsize=8, color=INK, zorder=6)
    ax.annotate("", (60, -side * W * 0.5 + 0), (200, -side * W * 0.5), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.4), zorder=6)
    ax.text(130, -side * (W * 0.5) + 6 * -side, "the horses run this way", ha="center", fontsize=8, color=INK, zorder=6)
    # grid, scale, north
    for gx in range(-200, X1 + 1, 50):
        ax.axvline(gx, color="#9aa58f", lw=0.4, alpha=0.6, zorder=0.5)
        ax.text(gx, Z0 + 4, f"{gx}", ha="center", va="top", fontsize=6.5, color=MUTED)
    for gz in range(int(Z0 // 50 * 50), Z1 + 1, 50):
        ax.axhline(gz, color="#9aa58f", lw=0.4, alpha=0.6, zorder=0.5)
        ax.text(X0 + 3, gz - 2, f"{gz}", fontsize=6.5, color=MUTED)
    nth = C.get("compass", {}).get("north")
    if not nth:
        V = json.loads((REPO / f"courses/{cid}-draft.json").read_text()); nth = V["compass"]["north"]
    nx, nz = nth; L = math.hypot(nx, nz); nx, nz = nx / L, nz / L
    bx, bz = X1 - 40, (Z1 - 70 if side < 0 else Z0 + 70)
    ax.annotate("N", (bx + nx * 30, bz + nz * 30), xytext=(bx, bz), ha="center", fontsize=11, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.5), zorder=7)
    sbz = Z1 - 18 if side < 0 else Z0 + 18
    ax.plot([X0 + 20, X0 + 120], [sbz, sbz], color=INK, lw=3, zorder=7); ax.text(X0 + 70, sbz - 5, "100 m", ha="center", fontsize=8, zorder=7)
    # the race view's world (x, z) seen from above with z running DOWN the page (three.js: y up, so +z comes towards a
    # viewer looking down from above): plotting z upwards mirrors the course (owner, 19:05: "have you flipped it?")
    ax.set_xlim(X0, X1); ax.set_ylim(Z1, Z0); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{CF['name']}: the stand side as built, DRAFT {CF.get('date', '')}. Grid every 50 m: metres up the course from the post "
                 f"(along the top) and metres from the inside rail (left; the stand side minus). Stands (cream) with their sizes, crosses at their origins; "
                 f"crowds brown dots; boards blue (thick: the big run-in hoardings); trees green.", fontsize=9.5, loc="left", color=INK, wrap=True)
    fig.tight_layout()
    out = REPO / f"reference/{cid}/stand-side-plan.png"
    fig.savefig(out, facecolor="white"); plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "doncaster")
