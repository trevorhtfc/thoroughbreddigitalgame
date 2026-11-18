"""Epsom: a picture of the race view's ground (the estimated heights) with the track on it, north up, for checking.

    python3 tools/course/epsom/ground_map.py     (after to_race_view.py)  ->  reference/epsom/ground-draft.png
"""
import json, importlib.util
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("epsom_layout", HERE / "layout.py")
LY = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(LY)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    C = json.loads((REPO / "race-view/assets/course/epsom.json").read_text())
    D = json.loads((REPO / "courses/epsom-draft.json").read_text())
    g = C["ground"]
    H = np.array(g["h"]).reshape(g["nz"], g["nx"])
    def en(x, z):
        """world x, z to east, north metres about the post"""
        p = np.stack([np.asarray(x, float), np.asarray(z, float)], -1)
        q = p[..., :1] * LY.XH + p[..., 1:] * LY.ZH
        return q @ LY.EAST_PX, q @ LY.NORTH_PX
    gx, gz = np.meshgrid(g["x0"] + g["cell"] * np.arange(g["nx"]), g["z0"] + g["cell"] * np.arange(g["nz"]))
    E, N = en(gx, gz)
    fig, ax = plt.subplots(figsize=(13, 9), dpi=130)
    cmap = LinearSegmentedColormap.from_list("downs", ["#5d7f4f", "#86a35f", "#b9c27c", "#e2d9a2", "#f1e6c8"])
    ax.tripcolor(E.ravel(), N.ravel(), H.ravel(), cmap=cmap, shading="gouraud", alpha=0.95)
    cs = ax.tricontour(E.ravel(), N.ravel(), H.ravel(), levels=np.arange(-20, 35, 2.5), colors="#3b3b2b", linewidths=0.35, alpha=0.6)
    cs2 = ax.tricontour(E.ravel(), N.ravel(), H.ravel(), levels=np.arange(-20, 35, 10), colors="#3b3b2b", linewidths=0.8, alpha=0.8)
    ax.clabel(cs2, fmt="%+d m", fontsize=7)
    surf = np.array(C["track"]["surface"][0])
    te, tn = en(surf[:, 0], surf[:, 1])
    ax.fill(te, tn, fc="#4f8a3a", ec="#2e5a22", lw=0.7, alpha=0.9)
    for t, s in D["starts"].items():
        e, n = en(*s["at"])
        ax.plot(e, n, marker="s", ms=6, color="white", mec="#1d1d1d", zorder=5)
        ax.annotate(t, (e, n), xytext=(6, 4), textcoords="offset points", fontsize=8.5, fontweight="bold",
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.5))
    ax.plot(0, 0, marker="o", ms=8, color="#c0392b", mec="white", zorder=6)
    ax.annotate("post", (0, 0), xytext=(-10, 10), textcoords="offset points", fontsize=9, color="#c0392b", fontweight="bold")
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    pts = np.array([p for r in C["routes"].values() for p in r["pathRail"]["points"]])
    pe, pn = en(pts[:, 0], pts[:, 1])
    ax.set_xlim(pe.min() - 250, pe.max() + 250); ax.set_ylim(pn.min() - 250, pn.max() + 250)
    ax.set_title("Epsom: the race view's ground, ESTIMATED (heights from the course guides, not measured), north up\n"
                 "contours every 2.5 m against the post; the track traced from At The Races' diagram", fontsize=10, loc="left")
    fig.tight_layout(); fig.savefig(REPO / "reference/epsom/ground-draft.png", facecolor="white"); plt.close(fig)


if __name__ == "__main__":
    main()
