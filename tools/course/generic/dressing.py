"""The dressing for the generic courses: the stand mix, the festival zones, the planting and the boards.

Owner, 19 Nov 2026: "apply a few mixes of stand / festivals as per our typical kind of designs. the grandstands can be
more the medium / smaller types now. then use the usual pattern of planting. advert boards etc to perimeters."

The usual pattern (as Doncaster, Newbury and Sandown, tools/course/real/perimeter.py):
  - the stands on one front line along the home straight from just past the post, each a crib-sheet piece of the
    medium or smaller kind (no long stands, no towers or blocks on the ends: every kit piece ends in a flank wall),
    a paved forecourt at their feet with the crowd right up to the rail;
  - the festival in the infield opposite the run-in (marquees, big tops, rows of balloon pods along the rail, a rail
    crowd), and a smaller stand-side festival up the course past the stands;
  - trees behind the stands and round the ends of the stand side; the shared belts round the course;
  - boards 20 m off the track round the outside (not in front of people), along the infield rail, and big hoardings
    along the run-in's inside rail facing the stands.
Ten courses, ten different mixes of stands (two per family), so the courses don't all look alike.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARCH = REPO / "assets/models/architecture"

# (piece, set back m) from just past the post up the course. Crib-sheet numbers: Park 1 tiered, 2 balcony, 3 roof
# terrace, 5 pitched roof, 6 old pavilion, 8 tented, 12 clock house, 13 low terraces; York 15 south
# stand, 17 pavilions, 19 clock tower; July 20 old pavilion, 22 small pavilion, 23 Victorian house; Rowley 27 ring pavilion.
MIXES = {
    "gen-park-l": ("Victorian parkland", [("park_tiered_stand", 0), ("park_balcony_stand", 0), ("park_old_pavilion", 8),
                                          ("park_roof_terrace_stand", 0), ("york_pavilions", 6)]),
    "gen-park-r": ("Northern galloping track", [("york_stand_south", 0), ("park_gable_stand", 0), ("york_clock_tower", 8),
                                                ("park_balcony_stand", 0), ("park_terrace", 3)]),
    "gen-tight-l": ("Country course", [("old_pavilion", 4), ("park_gable_stand", 0), ("park_clock_house", 8),
                                       ("park_roof_terrace_stand", 0)]),
    "gen-tight-r": ("Market-town course", [("park_balcony_stand", 0), ("park_terrace", 3), ("park_old_pavilion", 8),
                                           ("park_roof_terrace_stand", 0), ("victorian_house", 8)]),
    "gen-ring-l": ("Floodlit stadium", [("park_terrace", 3), ("park_tent_stand", 0), ("york_pavilions", 6)]),
    "gen-ring-r": ("Suburban park", [("pavilion_small", 4), ("park_tiered_stand", 0), ("park_terrace", 3)]),
    "gen-hill-l": ("Hilltop course", [("old_pavilion", 4), ("park_tiered_stand", 0), ("park_clock_house", 8),
                                      ("york_stand_south", 0)]),
    "gen-hill-r": ("Northern hill course", [("york_stand_south", 0), ("york_clock_tower", 8), ("park_gable_stand", 0),
                                            ("terrace_mid", 4)]),
    "gen-downs-l": ("Seaside downs", [("park_tent_stand", 0), ("park_old_pavilion", 8), ("park_roof_terrace_stand", 0),
                                      ("ring_pavilion", 6)]),
    "gen-downs-r": ("Downland course", [("park_tent_stand", 0), ("terrace_mid", 4), ("park_gable_stand", 0),
                                        ("victorian_house", 8)]),
}
SOURCES = ["park_stands", "york_stands", "july_stands", "rowley_stands"]
GAP = 4.0              # between neighbouring stands
FRONT = 18.0           # the stands' front line, metres back from the outer rail
W = 26.0
DEFAULT_RACE = {"park": "1m2f", "tight": "1m", "ring": "1m", "hill": "1m2f", "downs": "1m4f"}
FEATURE = {"park": ["6f", "1m", "1m4f", "2m"], "tight": ["5f", "1m", "1m4f"], "ring": ["5f", "1m", "1m4f"],
           "hill": ["5f", "1m", "1m4f"], "downs": ["6f", "1m4f", "2m"]}


def info():
    out = {}
    for src in SOURCES:
        out.update(json.loads((ARCH / f"{src}.json").read_text())["pieces"])
    return out


def dress(cid, fid, hand, S, L, C):
    I = info()
    side = -1.0 if hand < 0 else 1.0                  # the stand side's z sign (world); the infield is the other side
    zi = -side
    runin = C["facts"]["run-in m"]
    mix_name, mix = MIXES[cid]
    # ---- the stands: packed from just past the post up the course
    pieces, x, depth = [], -32.0, 0.0
    for piece, back in mix:
        g = I[piece]; w = g["width"]; off = g.get("offset", 0.0) * (1 if side < 0 else -1)
        cx = x + w / 2                                 # where the piece's body is centred
        pieces.append([piece, round(cx - off, 2), back, 0.85])
        x += w + GAP; depth = max(depth, g.get("depth", 30) + back)
    chain = (-32.0, x - GAP)
    zr = side * (W + 0.5)
    zs = lambda m: round(zr + side * m, 1)             # metres beyond the outer rail on the stand side
    zf = lambda m: round(zi * m, 1)                    # metres into the infield from the inside rail
    back_z = FRONT + depth + 18.0
    # ---- festivals: the infield opposite the run-in; the stand side up the course past the stands
    fx1 = min(runin - 90.0, 560.0)
    fests = [{"name": "run-in infield", "kit": "infield",
              "poly": [[-60, zf(2)], [fx1, zf(2)], [fx1, zf(100)], [-60, zf(100)]],
              "offTurf": 10.0, "dens": 0.035, "ground": "patches", "patch": 3.5,
              "railCrowd": {"from": 1.5, "to": 7.0, "dens": 0.6},
              "balloonRows": {"n": 5, "gap": 10, "every": 130, "in": 6, "start": 50, "end": 30}}]
    sx0, sx1 = chain[1] + 22.0, min(chain[1] + 230.0, runin - 40.0)
    if sx1 - sx0 > 80:
        fests.append({"name": "stand side, up the course", "kit": "standside",
                      "poly": [[sx0, zs(4)], [sx1, zs(4)], [sx1, zs(70)], [sx0, zs(70)]],
                      "offTurf": 4.0, "dens": 0.04, "ground": "patches", "patch": 3.5,
                      "railCrowd": {"from": 1.5, "to": 7.0, "dens": 0.6}})
    # little festival bits in the gaps at the ends of the stands
    perimeter = {
        "festivals": fests,
        "backTrees": [{"x": [chain[0] - 40, max(chain[1], sx1) + 30], "z": [zs(back_z), zs(back_z + 11)], "every": 10.0,
                       "note": "a row of trees behind the stands"}],
        "gapTrees": [{"note": "round the post end of the stand side",
                      "poly": [[-260, zs(14)], [chain[0] - 8, zs(14)], [chain[0] - 8, zs(back_z + 20)], [-260, zs(back_z + 20)]],
                      "offTurf": 14, "every": 8, "chance": 0.85, "standMargin": 6.0}],
        "lawnDens": 0.3, "lawnFront": {"from": 0.8, "to": 10.0, "dens": 0.55},
        "lawnX": [chain[0] - 10, chain[1] + 10],
        "treesClearOfBuildings": 5.0,
        "farBelt": {"from": 175.0, "to": 245.0, "every": 31.0, "scale": [1.8, 2.4], "chance": 0.6},
    }
    if sx1 - sx0 <= 80:                                # (a short run-in: the trees carry on past the stands instead)
        perimeter["gapTrees"].append({"note": "past the stands, up the course", "poly": [[chain[1] + 10, zs(30)], [runin + 60, zs(30)],
                                      [runin + 60, zs(back_z + 20)], [chain[1] + 10, zs(back_z + 20)]],
                                      "offTurf": 20, "every": 9, "chance": 0.8, "standMargin": 6.0})
    stands = {"_about": f"{mix_name}: {', '.join(p for p, _ in mix)} (crib-sheet pieces, medium and smaller), from just past "
                        "the post up the course, on one front line %d m back from the outer rail." % FRONT,
              "front": FRONT, "pieces": pieces}
    words = dict(S.get("words", {}))
    # rough good-ground winning times: the shared galloping-course curve (to_race_view.py), slowed a touch for the sharp
    # and stiff courses, quicker for the downhill sprints
    import numpy as np, re
    F_ = 201.168
    def metres(t):
        m = re.fullmatch(r"(?:(\d+)m)?(?:(\d+)f)?(?:(\d+)y)?", t); a, b, c = (int(v) if v else 0 for v in m.groups())
        return a * 8 * F_ + b * F_ + c * 0.9144
    targets = {}
    for key, r in S["starts"].items():
        rn, t = (r if isinstance(r, list) else [r, key]); d = metres(t)
        fpf = float(np.interp(d / F_, [5, 8, 12, 16, 18], [11.95, 12.35, 12.85, 13.3, 13.5]))
        k = {"park": 1.0, "tight": 1.012, "ring": 1.018, "hill": 1.03}.get(fid, 1.0)
        if fid == "downs": k = 0.985 if rn == "straight" else 1.012
        targets[key] = round(fpf * d / F_ * k, 1)
    view = {
        "defaultRace": DEFAULT_RACE[fid], "feature": FEATURE[fid], "routeWords": words, "targets": targets,
        "prelude": {"eye": [[-150, 45, round(zi * 140)], [-122, 42, round(zi * 128)]],
                    "at": [[60, 10, round(side * 80)], [88, 10, round(side * 82)]], "fov": 50,
                    "note": "the overview, as Newbury's: high over the post-end bend, looking up the course with the stands "
                            "on one side and the festival on the other"},
        "stallsAway": True,
        "lede": f"{S['name']}, {'left' if hand < 0 else 'right'}-handed: one of the five generic courses that every course "
                f"without its own build races on for now ({S['kind']}). {S['about']} Dressed as a {mix_name.lower()}.",
        "notes": [["Stands in for.", S["standsIn"] + "."],
                  ["The track.", f"About {C['facts']['circuit f']}f round, a {C['facts']['run-in f']}f run-in. Drawn from a "
                                 "few numbers (the corners and bends of the loop, the chutes), so it can be reshaped quickly."],
                  ["The stands.", f"{mix_name}: medium and smaller pieces from the grandstand crib sheet on one front line, "
                                  "the crowd up to the rail; the festival in the infield opposite and up the stand side."],
                  ["Running slowly?", "Choose Medium or Low under Quality in the race view's bar. Auto steps down by itself."]],
    }
    return {"perimeter": perimeter, "stands": stands, "view": view, "mix": mix_name}
