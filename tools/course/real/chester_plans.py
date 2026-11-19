"""Chester's plans for mark-up (owner, 19 Nov 2026, 13:27: "a full course plan and then a grandstand and festival zone
plan"). Drawn from what the race view places (race-view/assets/course/chester*.json), the stands kit's sizes
(assets/models/architecture/chester_stands.json) and the site components' footprints (site_props_codes.json).

  plan-course.png/.pdf            the whole Roodee: the track, the furlongs to go, the starts, every TV camera with what
                                  it looks at and when the director uses it, the overview shot, the walls, the city edge,
                                  the viaduct, the river, the castle
  plan-stands-festival.png/.pdf   the stand side and the infield: every stand and wall-terrace piece numbered with its
                                  size, the lawns, the crowds, the festival's pieces by kind

z runs DOWN the page (the race view's world seen from above), as stand_plan.py. Grid every 50 m in world metres (x from
the winning post along the home straight; z the stand side minus), so marks can be read back to the model.

  python3 tools/course/real/chester_plans.py      ->  reference/chester/plan-*.png, .pdf
"""
import json, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Wedge, Patch
from matplotlib.lines import Line2D

REPO = Path(__file__).resolve().parents[3]
RV = REPO / "race-view/assets/course"
C = json.loads((RV / "chester.json").read_text())
S = json.loads((RV / "chester-scenery.json").read_text())
V = json.loads((RV / "chester-view.json").read_text())
ST = json.loads((RV / "chester-stalls.json").read_text())
CF = json.loads((REPO / "tools/course/real/chester.json").read_text())
INFO = json.loads((REPO / "assets/models/architecture/chester_stands.json").read_text())["pieces"]
CODES = {c["piece"]: c for c in json.loads((REPO / "assets/models/architecture/site_props_codes.json").read_text())["codes"].values()}
W = C["trackWidth"]; F = 201.168
INK, MUTED, POST, CAM, OVER = "#2b2b2b", "#6b6b6b", "#c0392b", "#1f5f8b", "#8e44ad"
BG = "#eef2e4"

PR = C["routes"]["round"]["pathRail"]; RP = np.array(PR["points"]); CEN = RP.mean(0)


def on(d, off=0.0):
    """a point on route 'round' at d metres to go, 'off' metres across from the inside rail (+ out over the track)"""
    f = (d - PR["d0"]) / PR["spacing"]; i = max(0, min(len(RP) - 2, int(f))); k = f - i
    a, b = RP[i], RP[i + 1]; p = a + (b - a) * k; t = (b - a) / np.linalg.norm(b - a)
    n = np.array([-t[1], t[0]])
    if np.dot(n, CEN - p) > 0: n = -n
    return p + n * off


def lap_len():
    ds = PR["d0"] + PR["spacing"] * np.arange(len(RP)); far = ds > 800
    return float(ds[far][np.argmin(np.hypot(RP[far, 0], RP[far, 1]))])


def stand_fp(gi, x, z, turn, sx=1.0):
    a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    def w(u, v): return (x + u * ca - v * sa, z - (u * sa + v * ca))
    D = gi["depth"]; k = gi.get("kink")
    if k:
        r, (lx, ly) = k["right"], k["leftEnd"]
        L = math.hypot(lx, ly); nx, ny = -ly / L, lx / L
        if ny < 0: nx, ny = -nx, -ny
        return [w(lx, ly), w(0, 0), w(r, 0), w(r, D), w(0, D), w(lx + nx * D, ly + ny * D)]
    o, hw = gi.get("offset", 0.0), gi["width"] / 2 * sx
    return [w(o - hw, 0), w(o + hw, 0), w(o + hw, D), w(o - hw, D)]


def prop_fp(code, x, z, turn, sc=1.0):
    f = code["footprint"]; a = math.radians(turn); ca, sa = math.cos(a), math.sin(a)
    out = []
    for px, pz in ((f["x0"], f["z0"]), (f["x1"], f["z0"]), (f["x1"], f["z1"]), (f["x0"], f["z1"])):
        px, pz = px * sc, pz * sc
        out.append((x + px * ca + pz * sa, z - px * sa + pz * ca))
    return out


GROUP = {"chester_county_stand": ("stand", "County Stand"), "chester_tattersalls": ("stand", "Tattersalls"),
         "chester_brick_block": ("stand", "Brick block"),
         "chester_wt_steps": ("terrace", "Wall terrace: open steps"), "chester_wt_steps_rail": ("terrace", "Wall terrace: steps with a rail"),
         "chester_wt_stand": ("terrace", "Wall terrace: covered stand"), "chester_wt_stand_lantern": ("terrace", "Wall terrace: covered stand with the lantern"),
         "chester_wt_tower": ("terrace", "Wall terrace: the tower"), "chester_wt_taper": ("terrace", "Wall terrace: the taper back to the wall"),
         "chester_wall_bay": ("wall", None), "chester_terrace_row": ("city", None), "chester_city_block": ("city", None),
         "chester_viaduct_bay": ("viaduct", None), "chester_viaduct_span": ("viaduct", None),
         "chester_grosvenor_bridge": ("bridge", "Grosvenor Bridge"), "chester_castle_range": ("castle", "Castle range"),
         "chester_agricola_tower": ("castle", "Agricola Tower"),
         "chester_pagoda_run": ("festival", None), "chester_big_screen": ("festival", None), "chester_bar_pavilion": ("festival", None),
         "chester_lamp_speaker": ("lamp", None), "chester_sky_spire": ("city", None), "chester_sky_cathedral": ("city", None),
         "chester_sky_town_hall": ("city", None), "chester_sky_roofs": ("city", None), "chester_sky_roofs_b": ("city", None)}
STYLE = {"stand": ("#f4efe6", "#5a4a32", 1.2), "terrace": ("#e8c4ae", "#7a3f2c", 1.0), "wall": ("#b8705a", "#8a4a38", 0.4),
         "city": ("#d8cdc1", "#9a8c7c", 0.4), "viaduct": ("#9c5a45", "#6d3b2c", 0.4), "bridge": ("#cdbfa8", "#7d6d55", 0.8),
         "castle": ("#d2c2a8", "#7d6d55", 0.8), "festival": ("#2f5f9e", "#1f3f6e", 0.6), "lamp": ("#2b2b2b", "#2b2b2b", 0.4)}
PROP = {"marquee_peaks": "#f3f0e6", "marquee_clearspan": "#dfe8ee", "big_top": "#f2d6dc", "pagoda_kiosk": "#f4e2b8",
        "kiosk_awning": "#e9cf9a", "picnic_table": "#b99a6b", "pergola_picnic": "#cdb68d", "terrace_deck": "#c9b08a",
        "stand_open": "#e0d6c6", "stand_covered": "#d6c8b2", "banner_flag": "#c0392b", "flagpole": "#2b2b2b", "balloon_pod": "#e58fa6"}


def base(ax, X0, X1, Z0, Z1, people=False, props=False, numbers=False, dot=0.3, north=None):
    ax.set_facecolor(BG)
    iv = lambda x, z, m=30: X0 - m <= x <= X1 + m and Z0 - m <= z <= Z1 + m
    for col, fl in S["flats"].items():
        for f in fl: ax.add_patch(MP(np.array(f["pts"]), closed=True, fc=col, ec="none", zorder=1.0))
    surf = C["track"]["surface"]
    ax.add_patch(MP(np.array(surf[0]), closed=True, fc="#9cc184", ec="none", zorder=1.2))
    for h in surf[1:]: ax.add_patch(MP(np.array(h), closed=True, fc="#b7cc94", ec="none", zorder=1.3))
    for ln in C["rails"]["lines"]:
        q = np.array(ln); ax.plot(q[:, 0], q[:, 1], color="white", lw=1.2, zorder=2)
    for t in S["trees"]:
        if iv(t[0], t[1]): ax.add_patch(plt.Circle((t[0], t[1]), 3.4 * t[3], fc="#6f9a55", ec="#4f7a3a", lw=0.3, alpha=0.85, zorder=2.5))
    for b in S["boards"]:
        if not iv(b[0], b[1]): continue
        a = math.radians(b[2]); dx, dz = math.cos(a) * 3.0, -math.sin(a) * 3.0
        ax.plot([b[0] - dx, b[0] + dx], [b[1] - dz, b[1] + dz], color="#3d5a75", lw=1.5, solid_capstyle="butt", zorder=3)
    if people:
        P = np.array(S["people"]).reshape(-1, 4)
        m = (P[:, 0] > X0) & (P[:, 0] < X1) & (P[:, 2] > Z0) & (P[:, 2] < Z1)
        ax.scatter(P[m, 0], P[m, 2], s=dot, c="#a0522d", alpha=0.55, lw=0, zorder=3.2)
    key = []
    for q in S["pieces"]:
        model, piece, x, z, turn, sx = q[:6]
        sc = q[6] if len(q) > 6 else 1.0
        if not iv(x, z, 60): continue
        if model == "chester_stands" and piece in INFO:
            g, name = GROUP.get(piece, ("city", None)); fc, ec, lw = STYLE[g]
            fp = stand_fp(INFO[piece], x, z, turn, sx)
            ax.add_patch(MP(np.array(fp), closed=True, fc=fc, ec=ec, lw=lw, zorder=4 if g in ("stand", "terrace") else 3.5))
            if numbers and name and X0 < x < X1 and Z0 < z < Z1:
                cx, cz = np.mean([p[0] for p in fp]), np.mean([p[1] for p in fp]); n = len(key) + 1
                ax.add_patch(plt.Circle((cx, cz), 5.5, fc=ec, ec="white", lw=0.8, zorder=6))
                ax.text(cx, cz, str(n), ha="center", va="center", fontsize=7.5, color="white", fontweight="bold", zorder=6.1)
                gi = INFO[piece]; key.append(f"{n}  {name}: {gi['width'] * sx:.0f} m wide, {gi['depth']:.0f} m deep, at x {x:.0f}, z {z:.0f}")
        elif model == "site_props" and props and piece in CODES:
            if piece in ("banner_flag", "flagpole"):
                ax.plot(x, z, marker="v" if piece == "banner_flag" else "|", ms=4, color=PROP[piece], zorder=4.5); continue
            fp = prop_fp(CODES[piece], x, z, turn, sc)
            ax.add_patch(MP(np.array(fp), closed=True, fc=PROP.get(piece, "#ddd"), ec="#6b5a45", lw=0.5, zorder=4.2))
    # the post, the furlongs to go round the course, the way they run
    ax.plot(0, 0, marker="o", ms=9, color=POST, mec="white", zorder=7)
    ax.annotate("winning post", (0, 0), xytext=(-8, -12), textcoords="offset points", fontsize=9, color=POST, fontweight="bold", ha="right", zorder=7)
    for k in range(1, int(lap_len() // F) + 1):
        p = on(k * F, -3); lp = on(k * F, -13)
        if not (X0 < lp[0] < X1 and Z0 < lp[1] < Z1): continue
        ax.plot(*p, marker="s", ms=4, color=INK, zorder=7)
        ax.text(*lp, f"{k}f", fontsize=8, color=INK, ha="center", va="center", zorder=7)
    for d in (90, 700, 1150, 1450):
        a, b = on(d + 25, W / 2), on(d - 25, W / 2)
        ax.annotate("", b, a, arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=7)
    for gx in range(int(X0 // 50 * 50), int(X1) + 1, 50):
        ax.axvline(gx, color="#9aa58f", lw=0.4, alpha=0.55, zorder=0.5)
        ax.text(gx, Z0 + 3, f"{gx}", ha="center", va="top", fontsize=6.5, color=MUTED, zorder=8)
    for gz in range(int(Z0 // 50 * 50), int(Z1) + 1, 50):
        ax.axhline(gz, color="#9aa58f", lw=0.4, alpha=0.55, zorder=0.5)
        ax.text(X0 + 3, gz - 2, f"{gz}", fontsize=6.5, color=MUTED, zorder=8)
    nth = json.loads((REPO / "courses/chester-draft.json").read_text())["compass"]["north"]
    L = math.hypot(*nth); nx, nz = nth[0] / L, nth[1] / L
    bx, bz = north or (X0 + 210, Z1 - 45)
    ax.annotate("N", (bx + nx * 32, bz + nz * 32), xytext=(bx, bz), ha="center", va="center", fontsize=12, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.6), zorder=9)
    ax.plot([X0 + 20, X0 + 120], [Z1 - 18, Z1 - 18], color=INK, lw=3, zorder=9); ax.text(X0 + 70, Z1 - 24, "100 m", ha="center", fontsize=8, zorder=9)
    ax.set_xlim(X0, X1); ax.set_ylim(Z1, Z0); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    return key


def label(ax, x, z, s, size=9, col=INK, rot=0, style="normal", weight="bold"):
    ax.text(x, z, s, fontsize=size, color=col, ha="center", va="center", rotation=rot, style=style, fontweight=weight, zorder=10,
            bbox=dict(fc="white", ec="none", alpha=0.7, pad=1.5))


def sheet(title):
    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.01, 0.015, 0.70, 0.93]); pn = fig.add_axes([0.715, 0.015, 0.28, 0.93]); pn.axis("off")
    fig.text(0.01, 0.975, title, fontsize=10.5, color=INK, va="top", wrap=True)
    return fig, ax, pn


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(REPO / f"reference/chester/{name}.{ext}", facecolor="white", dpi=150)
    plt.close(fig); print("wrote", name)


def course_plan():
    X0, X1, Z0, Z1 = -290, 720, -240, 640
    fig, ax, pn = sheet("Chester, the Roodee: the course as built (DRAFT, 19 Nov 2026). Left-handed, about 1,650 m round. Grid every 50 m in race-view "
                        "metres: x along the home straight from the post, z towards the infield.")
    base(ax, X0, X1, Z0, Z1)
    # the starts
    for k, s in ST["starts"].items():
        p = np.array(s["insideRailAt"]); o = np.array(s["towardsOuterRail"])
        ax.plot(*zip(p, p + o * W), color="#1e7b45", lw=2.2, zorder=6)
        lp = p + o * (W + 9); ax.text(*lp, s["label"], fontsize=6.5, color="#1e7b45", ha="center", va="center", zorder=6,
                                       bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.8))
    # the tracking car in the infield
    tc = np.array([on(d, -6) for d in np.arange(-40, lap_len() - 5, 5)])
    ax.plot(tc[:, 0], tc[:, 1], color=CAM, lw=1.1, ls=(0, (4, 3)), zorder=5)
    # the director's fixed cameras: where each one stands and the stretch of track it watches (the shots' metres to go)
    RC = V["raceCameras"]; shots = V["raceDirector"]["shots"]; rows = []; n = 0; seen = {}
    for a, b, cam in shots:
        if cam == "track_inside":
            rows.append(f"      {a:>4}-{max(b, 0):<4} m to go   tracking car (dashed)"); continue
        c = RC[cam]; e = np.array([c["at"][0], c["at"][2]])
        if cam not in seen:
            n += 1; seen[cam] = n
            pa, pb = on(min(a, lap_len()), W / 2), on(max(b, 0), W / 2)
            ax.add_patch(MP(np.array([e, pa, pb]), closed=True, fc=CAM, ec=CAM, alpha=0.07, lw=0.6, zorder=5.5))
            ax.plot(*zip(e, (pa + pb) / 2), color=CAM, lw=0.8, alpha=0.6, zorder=5.6)
            ax.add_patch(plt.Circle(e, 8, fc=CAM, ec="white", lw=1, zorder=8))
            ax.text(*e, str(n), ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=8.1)
        rows.append(f"  {seen[cam]:>2}  {a:>4}-{max(b, 0):<4} m to go   {c['label']}, {c['at'][1]:.0f} m up")
    # the overview: the racecard's shot before the off, and after the race
    pre = V["setPieces"]["prelude"]; e = np.array([pre["eye"][0][0], pre["eye"][0][2]]); t = np.array([pre["at"][0][0], pre["at"][0][2]])
    ang = math.degrees(math.atan2(t[1] - e[1], t[0] - e[0])); r = np.linalg.norm(t - e)
    ax.add_patch(Wedge(e, r, ang - pre["fov"] * 0.89, ang + pre["fov"] * 0.89, fc=OVER, ec=OVER, alpha=0.08, lw=0.8, zorder=5.4))
    ax.add_patch(plt.Circle(e, 8, fc=OVER, ec="white", lw=1, zorder=8)); ax.text(*e, "O", ha="center", va="center", fontsize=8, color="white", fontweight="bold", zorder=8.1)
    # names
    for x, z, s, kw in [(22, -75, "County Stand", {}), (104, -72, "Tattersalls", {}), (-95, -42, "brick block", dict(size=7.5)),
                        (210, -95, "the wall terraces", dict(size=8.5)), (330, -55, "the City Walls (Nun's Road)", dict(size=8, rot=-8)),
                        (-50, -150, "the city edge", dict(size=8.5, col=MUTED)), (-190, 200, "the Roodee Viaduct", dict(rot=-80, size=9)),
                        (140, 230, "THE INFIELD: the festival", dict(size=12, col="#8a6a1c", style="italic")),
                        (560, 330, "River Dee", dict(col="#3c6e86", size=10, style="italic")), (520, 215, "Grosvenor Bridge", dict(size=8)),
                        (520, -130, "Chester Castle", dict(size=8.5)), (330, 30, "the chute", dict(size=8)),
                        (35, 470, "River Dee viaduct", dict(size=8, col=MUTED))]:
        label(ax, x, z, s, **kw)
    legend = ("THE TV DIRECTOR'S CUT (1m2f75y, by the leader's metres to go)\n" + "\n".join(rows) +
              "\n\n   O   the overview: behind the runners card before\n       the off, and after the race (down the home\n       straight from the castle end, 16 m up)\n\n   Each fixed camera's wedge runs to the stretch of\n   track it watches. Numbers in green: the starts.")
    pn.text(0.0, 1.0, legend, fontsize=7.4, family="DejaVu Sans Mono", color=INK, ha="left", va="top", linespacing=1.5, transform=pn.transAxes)
    hand = [Patch(fc="#9cc184", label="turf"), Patch(fc="#b7cc94", label="infield (grass; the festival along the straight)"), Patch(fc="#f4efe6", ec="#5a4a32", label="stands"),
            Patch(fc="#e8c4ae", ec="#7a3f2c", label="wall terraces"), Patch(fc="#b8705a", label="city wall"), Patch(fc="#d8cdc1", label="city buildings"),
            Patch(fc="#9c5a45", label="viaduct"), Patch(fc="#a7c1cb", label="river"), Patch(fc="#6f9a55", label="trees"),
            Line2D([], [], color="#3d5a75", lw=2, label="boards"), Line2D([], [], color="#1e7b45", lw=2, label="starts (stalls)"),
            Line2D([], [], marker="s", color=INK, lw=0, label="furlongs to go"), Patch(fc=CAM, alpha=0.3, label="fixed camera and what it watches")]
    pn.legend(handles=hand, loc="lower left", fontsize=8, frameon=False, ncol=1, title="KEY", title_fontsize=9, alignment="left")
    save(fig, "plan-course")


def zone_plan():
    X0, X1, Z0, Z1 = -160, 460, -150, 500
    fig, ax, pn = sheet("Chester: the grandstand and festival zones as built (DRAFT, 19 Nov 2026). Stands and wall terraces numbered with their sizes; "
                        "every festival piece at its real footprint; grid every 50 m in race-view metres (x from the post along the home straight).")
    key = base(ax, X0, X1, Z0, Z1, people=True, props=True, numbers=True)
    # the infield rail crowd band (perimeter.festival.railCrowd: 11-17 m in from the inside rail)
    band = [0.9, 11.0]                                     # the infield's rail crowd down the straight (edges_chester festival)
    for off in band:
        q = np.array([on(d, -off) for d in np.arange(-40, lap_len() - 5, 5)]); ax.plot(q[:, 0], q[:, 1], color="#a0522d", lw=0.6, ls=":", zorder=3.3)
    for x, z, s, kw in [(22, -100, "COUNTY STAND", {}), (104, -95, "TATTERSALLS", dict(size=8.5)), (-100, -60, "brick block", dict(size=8)),
                        (215, -122, "THE WALL TERRACES", dict(size=9)), (40, -14, "the rail lawn", dict(size=7.5, col="#6b4a2a", style="italic", weight="normal")),
                        (140, 230, "THE INFIELD FESTIVAL", dict(size=13, col="#8a6a1c", style="italic")),
                        (140, 252, "marquees, kiosks, picnic areas and open stands; a crowd along the inside rail (dotted)", dict(size=8, col="#8a6a1c", weight="normal")),
                        (360, -40, "the City Walls (Nun's Road)", dict(size=8, rot=-8))]:
        label(ax, x, z, s, **kw)
    pn.text(0.0, 1.0, "THE STAND SIDE (numbered on the plan)\n" + "\n".join(key), fontsize=7.8, color=INK, va="top", linespacing=1.55, transform=pn.transAxes)
    from collections import Counter
    cnt = Counter(q[1] for q in S["pieces"] if q[0] == "site_props" and X0 < q[2] < X1 and Z0 < q[3] < Z1)
    kc = Counter(q[1] for q in S["pieces"] if q[0] == "chester_stands" and X0 < q[2] < X1 and Z0 < q[3] < Z1)
    hand = [Patch(fc="#2f5f9e", ec="#1f3f6e", label=f"pagoda runs ({kc['chester_pagoda_run']}), the bar ({kc['chester_bar_pavilion']}), the big screen ({kc['chester_big_screen']})")]
    hand += [Patch(fc=PROP[k], ec="#6b5a45", label=f"{CODES[k]['name']} ({cnt[k]})") for k in PROP if k in CODES and cnt.get(k) and k not in ("banner_flag", "flagpole")]
    hand += [Line2D([], [], marker="v", color=PROP["banner_flag"], lw=0, label=f"banner flag ({cnt.get('banner_flag', 0)})"),
             Line2D([], [], marker="|", color=INK, lw=0, label=f"flagpole ({cnt.get('flagpole', 0)})"),
             Line2D([], [], marker="o", color="#a0522d", lw=0, ms=3, label="crowd (one dot a person)")]
    pn.legend(handles=hand, loc="lower left", fontsize=8, frameon=False, title="THE FESTIVAL'S PIECES (how many on this plan)", title_fontsize=9, alignment="left")
    save(fig, "plan-stands-festival")


def stands_closeup():
    X0, X1, Z0, Z1 = -125, 305, -140, 40
    fig = plt.figure(figsize=(16.5, 11.7))
    ax = fig.add_axes([0.01, 0.30, 0.98, 0.64])
    fig.text(0.01, 0.975, "Chester: the grandstand zone, close up (DRAFT, 19 Nov 2026). The stands and the wall terraces numbered with their sizes; "
             "crowds as dots (one a person); the rail lawn's banner flags; grid every 50 m in race-view metres.", fontsize=10.5, color=INK, va="top")
    key = base(ax, X0, X1, Z0, Z1, people=True, props=True, numbers=True, dot=1.6, north=(X1 - 25, Z0 + 45))
    for x, z, s_, kw in [(22, -78, "COUNTY STAND", {}), (104, -60, "TATTERSALLS", dict(size=8.5)), (-90, -48, "brick block", dict(size=8)),
                         (200, -78, "THE WALL TERRACES (on the City Walls)", dict(size=9)), (50, -12, "the rail lawn", dict(size=8, col="#6b4a2a", style="italic", weight="normal")),
                         (150, 28, "the infield festival", dict(size=9, col="#8a6a1c", style="italic"))]:
        label(ax, x, z, s_, **kw)
    pn = fig.add_axes([0.01, 0.01, 0.98, 0.27]); pn.axis("off")
    half = (len(key) + 1) // 2
    pn.text(0.0, 1.0, "THE STAND SIDE\n" + "\n".join(key[:half]), fontsize=9, color=INK, va="top", linespacing=1.6, transform=pn.transAxes)
    pn.text(0.5, 1.0, "\n" + "\n".join(key[half:]), fontsize=9, color=INK, va="top", linespacing=1.6, transform=pn.transAxes)
    save(fig, "plan-stands-closeup")


if __name__ == "__main__":
    course_plan(); zone_plan(); stands_closeup()
