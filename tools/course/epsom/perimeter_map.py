"""Epsom: a plan of the scenery (phase 3) for the owner to mark up, north up.

    python3 tools/course/epsom/perimeter_map.py     (after to_race_view.py)  ->  reference/epsom/perimeter-plan.png
"""
import json, math, importlib.util
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("epsom_layout", HERE / "layout.py")
LY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LY)


def main(zoom=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    C = json.loads((REPO / "race-view/assets/course/epsom.json").read_text())
    S = json.loads((REPO / "race-view/assets/course/epsom-scenery.json").read_text())
    def en(x, z):
        p = np.stack([np.asarray(x, float), np.asarray(z, float)], -1)
        q = p[..., :1] * LY.XH + p[..., 1:] * LY.ZH
        return q @ LY.EAST_PX, q @ LY.NORTH_PX
    fig, ax = plt.subplots(figsize=(16, 11), dpi=150 if zoom else 120)
    ax.set_facecolor("#cfdcae")
    for col, lst in S["flats"].items():
        for f in lst:
            P = np.array(f["pts"]); e, n = en(P[:, 0], P[:, 1]); ax.fill(e, n, fc=col, ec="none", zorder=1)
    for c in S.get("canopies", []):
        v = np.array(c["v"]).reshape(-1, 3); e, n = en(v[:, 0], v[:, 2])
        ax.scatter(e, n, s=1.2, c="#557a3c", alpha=0.5, zorder=2, linewidths=0)
    surf = np.array(C["track"]["surface"][0]); e, n = en(surf[:, 0], surf[:, 1])
    ax.fill(e, n, fc="#4f8a3a", ec="#2e5a22", lw=0.6, zorder=3)
    T = np.array([[t[0], t[1], t[3]] for t in S["trees"]]); e, n = en(T[:, 0], T[:, 1])
    ax.scatter(e, n, s=T[:, 2] * 7, c="#2f5a2a", zorder=4, linewidths=0)
    B = np.array([[b[0], b[1]] for b in S["boards"]]); e, n = en(B[:, 0], B[:, 1])
    ax.scatter(e, n, s=2.5, c="#2a5d9f", marker="s", zorder=5, linewidths=0)
    Pp = np.array(S["people"]).reshape(-1, 4); e, n = en(Pp[:, 0], Pp[:, 2])
    ax.scatter(e, n, s=0.4, c="#c0392b", zorder=6, linewidths=0, alpha=0.6)
    EI = json.loads((REPO / "assets/models/architecture/epsom_stands.json").read_text())["pieces"]
    for pc in S["pieces"]:
        if pc[0] == "epsom_stands":
            pi, x, z, t = EI[pc[1]], pc[2], pc[3], math.radians(pc[4])
            hw = pi["width"] / 2; o = pi.get("offset", 0.0)
            if "crowd" in pi and pi["crowd"]:                     # a stand: its origin is the middle of its front foot
                f, d1 = pi.get("front", 0.0), pi["depth"] + pi.get("front", 0.0)
            else:                                                 # a ride: its origin is its middle
                f, d1 = -pi["depth"] / 2, pi["depth"] / 2
            q = np.array([(x + u * math.cos(t) - v * math.sin(t), z - (u * math.sin(t) + v * math.cos(t))) for u, v in ((o - hw, f), (o + hw, f), (o + hw, d1), (o - hw, d1))])
            e, n = en(q[:, 0], q[:, 1]); ax.fill(e, n, fc="#f4efe6", ec="#8a7350", lw=0.8, zorder=8)
            continue
        if pc[0] != "site_props": continue
        e, n = en(pc[2], pc[3]); ax.plot(e, n, marker="o", ms=2.6, color="#f4efe6", mec="#8a7350", mew=0.5, zorder=7)
    for t, s in json.loads((REPO / "courses/epsom-draft.json").read_text())["starts"].items():
        e, n = en(*s["at"]); ax.plot(e, n, "ws", mec="k", ms=5, zorder=8); ax.annotate(t, (e, n), xytext=(4, 4), textcoords="offset points", fontsize=7.5, zorder=8)
    lab = [("the grandstand", 39, -112), ("balcony stand", -85, -95), ("Rowley stand", 190, -90), ("the Hill: rail crowd,\nboards on the rail", 330, 18), ("hospitality frontage", 65, 62),
           ("the Hill's festival,\nFerris wheel, helter skelter", 380, 135), ("Tattenham Corner: crowd,\nroad, huts", 760, 210), ("the climb: groups\nalong the rail", 200, 430),
           ("far side: boards 20 m out,\nbelt of trees, the woods", 150, 640), ("Tattenham Corner\nhouses (garden trees)", 1040, 120),
           ("stand side: boards,\nthin crowd, belt", 650, -80), ("the open Downs (infield)", 400, 300)]
    for txt, x, z in lab:
        e, n = en(x, z); ax.annotate(txt, (e, n), fontsize=8.5, color="#1d1d1d", ha="center", zorder=9,
                                    bbox=dict(fc="white", ec="#888888", alpha=0.85, pad=1.5))
    e, n = en(0, 0); ax.plot(e, n, "o", color="#c0392b", ms=7, mec="white", zorder=9)
    pts = np.array([p for r in C["routes"].values() for p in r["pathRail"]["points"]]); pe, pn = en(pts[:, 0], pts[:, 1])
    if zoom:                                                          # the stand side and the Hill, by the post
        SP = np.array(C["routes"]["straight"]["pathRail"]["points"])
        rz = lambda x: float(np.interp(x, SP[::-1, 0] if SP[0, 0] > SP[-1, 0] else SP[:, 0], SP[::-1, 1] if SP[0, 0] > SP[-1, 0] else SP[:, 1]))
        ride = {pc[1]: (pc[2], pc[3]) for pc in S["pieces"] if pc[0] == "epsom_stands"}
        fw, hs = ride["epsom_ferris_wheel"], ride["epsom_helter_skelter"]
        for txt, x, z in [("Ferris wheel", fw[0], fw[1] + 22), ("helter skelter", hs[0], hs[1] - 16), ("big tents", 216.9, 150), ("rail lawn", -45, -31),
                          ("little stands", -60, 20), ("edge marquees", 250, 26), ("winning post", 0, 12)] + [("%df" % k, 201.17 * k, rz(201.17 * k) - 26 - 16) for k in (1, 2, 3)]:
            e, n = en(x, z); ax.annotate(txt, (e, n), fontsize=9, color="#1d1d1d", ha="center", zorder=9,
                                        bbox=dict(fc="#fffbe8", ec="#a89060", alpha=0.9, pad=1.2))
        cx, cz = [], []
        for x, z in ((-150, -140), (760, -140), (760, 230), (-150, 230)):
            e, n = en(x, z); cx.append(float(e)); cz.append(float(n))
        ax.set_xlim(min(cx), max(cx)); ax.set_ylim(min(cz), max(cz))
        e0, n0 = min(cx) + 30, min(cz) + 25
        ax.plot([e0, e0 + 100], [n0, n0], color="k", lw=3, zorder=10); ax.text(e0 + 50, n0 + 8, "100 m", ha="center", fontsize=9, zorder=10)
    else:
        ax.set_xlim(pe.min() - 260, pe.max() + 260); ax.set_ylim(pn.min() - 260, pn.max() + 230)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Epsom: the scenery, DRAFT for mark-up, north up. Dark green dots trees, blue boards, red people, cream marquees and "
                 "kiosks,\npale green speckle the woods' canopies, beige paths; the real outline and ground (OpenStreetMap, AWS Terrain "
                 "Tiles)", fontsize=10, loc="left")
    fig.tight_layout(); fig.savefig(REPO / ("reference/epsom/perimeter-plan-stands.png" if zoom else "reference/epsom/perimeter-plan.png"), facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    main()
    main(zoom=True)
