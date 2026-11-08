"""Newmarket (the Rowley Mile), phase 1: a DRAFT layout for the owner to check before anything is modelled.

Interpretive, from the owner's references (reference/newmarket/): the plan, the grandstand photo, his notes on the Dip and
his 1m4f video. Not surveyed: every number below is a choice, named, so it can be changed in one place.

Writes  courses/newmarket-draft.json   the layout as data (same axes and running direction as courses/ascot.json)
        reference/newmarket/plan-draft.png   a plan and a height profile, to check by eye

  python3 tools/course/newmarket/draft_layout.py

Axes as Ascot: origin = the winning post on the inside rail; x east, z south, y up. On the straight the horses run
towards -x with the inside rail on their right (z = 0, the far side) and the stands on their left (+z). Right-handed:
coming down the Cesarewitch leg they turn right into the straight.
"""
import json, math
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
F = 201.168                                   # a furlong, metres

# ---------------------------------------------------------------- the choices (change here)
TRACK_W = 36.0          # the Rowley Mile is wide; Ascot's straight is 30
STRAIGHT = 10 * F       # 1m2f from the post to the end of the bend: everything up to 1m2f is run straight (the plan)
LEG_ANGLE = 62.0        # the Cesarewitch leg, degrees up from the straight's line on the plan
BEND_R = 200.0          # the bend's inside-rail radius
RUN_ON = 120.0          # the straight carries on past the post
TRIPS = {"5f": 5, "6f": 6, "7f": 7, "1m": 8, "1m1f": 9, "1m2f": 10, "1m4f": 12, "1m6f": 14, "2m": 16, "2m2f": 18, "2m4f": 20}
# The Dip (owner's notes): downhill from about 2f out (by "the Bushes"), the bottom at the 1f pole, a sharp climb to the
# post. Heights in metres against the post, by metres to go; smooth between. Gentle ridges before it; the leg rises
# a little towards the far starts. Interpretive: big enough to see from the stand and to matter in the run for home.
PROFILE = [(-RUN_ON, 0.6), (0, 0.0), (201, -3.0), (402, 0.6), (520, 1.0), (700, 0.4),
           (900, 1.2), (1150, 0.6), (1400, 1.4), (1700, 0.8), (STRAIGHT, 1.6), (2600, 3.0), (3400, 4.5), (4500, 6.0), (5200, 6.5)]
DYKE = {"offset": 70.0, "height": 9.0, "base": 34.0, "from": -260.0, "to": STRAIGHT + 150.0,
        "note": "Owner, 8 Nov: the Devil's Dyke as a long grassy bank on the far side of the straight from the cameras, a "
                "visual screen (interpretive: the real dyke crosses the heath at an angle). 'offset' metres north of the "
                "inside rail to its crest, 'base' its width at the foot, scrub along the crest."}
STANDS = {"front": TRACK_W + 14.0, "x": [-170.0, 330.0], "height": 26.0,
          "note": "Interpretive and bigger than life (owner): the Millennium Grandstand's row of wave-shaped canopies, "
                  "longer than the real stand, from the stand kit with a new canopy module, smooth clay finish."}


def straight_pt(d):                            # d metres to go on the straight, inside rail
    return (d, 0.0)

# the bend: from the straight's top end, turning (as you go UP the course, against the running) up the plan
TURN = math.radians(LEG_ANGLE)                  # the angle turned through, running (the leg meets the straight at LEG_ANGLE)
CX, CZ = STRAIGHT, -BEND_R                       # the bend's centre (inside the turn: north of the inside rail)
BEND_LEN = BEND_R * math.radians(LEG_ANGLE)


def course_pt(d):
    """Inside-rail point and running direction at d metres to go (d may run past the post, negative)."""
    if d <= STRAIGHT:
        return (d, 0.0), (-1.0, 0.0)
    s = d - STRAIGHT
    if s <= BEND_LEN:                            # round the bend (anticlockwise on the plan as you go up the course)
        a = s / BEND_R
        x = CX + BEND_R * math.sin(a); z = CZ + BEND_R * math.cos(a)
        return (x, z), (-math.cos(a), math.sin(a))
    a = math.radians(LEG_ANGLE)
    ex, ez = CX + BEND_R * math.sin(a), CZ + BEND_R * math.cos(a)
    k = s - BEND_LEN
    ux, uz = math.cos(a), -math.sin(a)           # up the leg (against the running)
    return (ex + ux * k, ez + uz * k), (-ux, -uz)


from scipy.interpolate import PchipInterpolator
_H = PchipInterpolator([p[0] for p in PROFILE], [p[1] for p in PROFILE])   # smooth, no overshoot between the points


def height(d):
    return float(_H(min(max(d, PROFILE[0][0]), PROFILE[-1][0])))


def main():
    longest = max(TRIPS.values()) * F + 60
    pts, step = [], 5.0
    d = -RUN_ON
    while d <= longest:
        (x, z), _ = course_pt(d)
        pts.append([round(x, 2), round(z, 2), round(height(d), 3), round(d, 1)])
        d += step
    starts = {}
    for name, f in TRIPS.items():
        dist = f * F
        (x, z), (tx, tz) = course_pt(dist)
        starts[name] = {"distance": round(dist, 1), "at": [round(x, 2), round(z, 2)], "running": [round(tx, 4), round(tz, 4)],
                        "onStraight": dist <= STRAIGHT + 1e-6}
    poles = [{"furlongs": k, "at": [round(c, 2) for c in course_pt(k * F)[0]]} for k in range(1, 25) if k * F <= longest]
    out = {
        "id": "newmarket", "name": "Newmarket (Rowley Mile), draft", "status": "DRAFT for the owner's check (8 Nov 2026): not used by the game yet",
        "_about": "Built by tools/course/newmarket/draft_layout.py. Interpretive, not surveyed: every number is a named choice in that script.",
        "axes": "As courses/ascot.json: origin = winning post on the inside rail; x east, z south, y up. On the straight horses run towards -x, inside rail z = 0 (far side), stands +z.",
        "direction": "clockwise (right-handed: one bend, from the Cesarewitch leg into the straight)",
        "trackWidth": TRACK_W, "furlong": F,
        "straight": {"length": round(STRAIGHT, 1), "note": "1m2f from the post to the bend: races up to 1m2f are run straight"},
        "bend": {"from": round(STRAIGHT + BEND_LEN, 1), "to": round(STRAIGHT, 1), "radius": BEND_R, "turn": round(math.degrees(TURN), 1),
                 "note": "metres to go where it starts and ends; inside-rail radius; degrees turned"},
        "insideRail": {"spacing": step, "fields": "x, z, height, metres to go", "points": pts},
        "theDip": {"profile": PROFILE, "note": "height (m) against the post by metres to go; the bottom at the 1f pole"},
        "starts": starts, "furlongPoles": poles, "devilsDyke": DYKE, "stands": STANDS,
    }
    (REPO / "courses/newmarket-draft.json").write_text(json.dumps(out, separators=(",", ":")))
    draw(out)
    print("wrote courses/newmarket-draft.json and reference/newmarket/plan-draft.png")


def draw(c):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle
    ink, rail, grass, turf, dyke, stand = "#2b2b2b", "#ffffff", "#dfe6c8", "#7fa65a", "#9aa86b", "#d9cdb4"
    fig = plt.figure(figsize=(13, 10.5), dpi=110)
    ax = fig.add_axes([0.04, 0.33, 0.92, 0.62]); pr = fig.add_axes([0.07, 0.06, 0.88, 0.2])
    ax.set_facecolor(grass)
    P = c["insideRail"]["points"]
    def outer(i):
        (x, z), (tx, tz) = course_pt(P[i][3])
        nx, nz = tz, -tx                                     # to the horses' left (towards the stands on the straight)
        return x + nx * TRACK_W, z + nz * TRACK_W
    inner = [(p[0], p[1]) for p in P]; out = [outer(i) for i in range(len(P))]
    ax.add_patch(Polygon(inner + out[::-1], closed=True, fc=turf, ec="none"))
    ax.plot(*zip(*inner), color=rail, lw=1.4); ax.plot(*zip(*out), color=rail, lw=1.4)
    D = c["devilsDyke"]
    ax.add_patch(Rectangle((D["from"], -D["offset"] - D["base"] / 2), D["to"] - D["from"], D["base"], fc=dyke, ec="#6f7a45", lw=0.8))
    ax.text((D["from"] + D["to"]) / 2, -D["offset"] + 4, "The Devil's Dyke (a bank, about %d m high: the screen behind the far rail)" % D["height"], ha="center", va="center", fontsize=9, color=ink)
    S = c["stands"]
    ax.add_patch(Rectangle((S["x"][0], S["front"]), S["x"][1] - S["x"][0], 34, fc=stand, ec="#8d826b", lw=0.8))
    ax.text(S["x"][1] + 30, S["front"] + 17, "Stands (bigger and longer than life)", ha="left", va="center", fontsize=9, color=ink)
    ax.plot([0, 0], [0, TRACK_W], color="#c0392b", lw=2.2); ax.text(-20, TRACK_W / 2, "post", ha="right", va="center", fontsize=9, color="#c0392b")
    for name, s in c["starts"].items():
        (x, z), (tx, tz) = course_pt(s["distance"]); nx, nz = tz, -tx
        ax.plot([x, x + nx * TRACK_W], [z, z + nz * TRACK_W], color=ink, lw=1.1)
        lx, lz = x - nx * 26, z - nz * 26
        ax.text(lx, lz, name, ha="center", va="center", fontsize=8.5, color=ink, rotation=0)
    for p in c["furlongPoles"]:
        if p["furlongs"] <= 10: ax.plot(p["at"][0], p["at"][1], marker="|", color=ink, ms=7)
    ax.annotate("running", xy=(1350, TRACK_W + 22), xytext=(1700, TRACK_W + 22), arrowprops=dict(arrowstyle="->", color=ink), fontsize=8.5, va="center", color=ink)
    ax.set_aspect("equal"); ax.invert_yaxis()
    xs = [p[0] for p in P] + [D["from"]]; zs = [p[1] for p in P]
    ax.set_xlim(min(xs) - 200, max(xs) + 120); ax.set_ylim(max(zs) + 140, min(zs) - 80)
    ax.set_title("Newmarket, Rowley Mile: draft layout for checking (interpretive, metres; north up, as your plan: the post on the left, the bend on the right)", fontsize=11, color=ink, loc="left")
    ax.tick_params(labelsize=7, colors="#777")
    dd = [d / 1.0 for d in range(-120, int(STRAIGHT) + 1, 5)]
    pr.fill_between([d / F for d in dd], [height(d) for d in dd], -4, color=turf, alpha=0.6)
    pr.plot([d / F for d in dd], [height(d) for d in dd], color=ink, lw=1.2)
    pr.axvline(0, color="#c0392b", lw=1.2); pr.axvline(1, color="#888", lw=0.8, ls="--"); pr.axvline(2, color="#888", lw=0.8, ls="--")
    pr.text(0.95, 2.2, "the bottom of the Dip, 1f", ha="right", fontsize=8.5); pr.text(2.05, 2.2, "the Bushes, 2f", ha="left", fontsize=8.5)
    pr.set_xlim(-RUN_ON / F, STRAIGHT / F); pr.set_ylim(-4, 3)
    pr.set_xlabel("furlongs to go (the straight)", fontsize=9); pr.set_ylabel("height (m)", fontsize=9)
    pr.set_title("The straight's height profile: down into the Dip from 2f, up to the post (heights exaggerated on this chart only)", fontsize=10, loc="left")
    pr.tick_params(labelsize=8)
    fig.savefig(REPO / "reference/newmarket/plan-draft.png")


if __name__ == "__main__":
    main()
