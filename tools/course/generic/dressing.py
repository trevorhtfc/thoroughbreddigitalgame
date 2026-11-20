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

# Two stand clusters for each kind of course (owner, 19 Nov 17:39: "two grandstand clusters for each course type? a
# bigger (haydock, newcastle etc) and a smaller (pontefract, beverley)"; "use more of the smaller grandstand and pavilion
# types"), clustered round the post (17:39: "the finish lines are towards the ends of any straight.. and the grandstand and
# festival zone is clustered around it"). (piece, set back m), from the post-end bend side up the course. New small stands
# from his model and photos: gen_* (tools/blender/build_generic_stands.py). Crib-sheet numbers for the others: Park 1
# tiered, 2 balcony, 3 roof terrace, 5 pitched roof, 6 old pavilion, 8 tented, 12 clock house, 13 low terraces; York 14
# north stand, 15 south stand, 17 pavilions, 19 clock tower; July 21 old pavilion wing, 23 Victorian house; Rowley 27 ring
# pavilion, 28 little Victorian pavilion (lookout); and Chester's little gabled stands (tattersalls).
CLUSTERS = {
    ("park", "big"): ("Galloping course, the bigger stand side", [("york_stand_north", 0), ("gen_pavilion_stand", 2), ("park_balcony_stand", 0),
                       ("park_clock_house", 8), ("park_gable_stand", 0), ("york_pavilions", 6)]),
    ("park", "small"): ("Country galloping course", [("gen_veranda_stand", 0), ("victorian_pavilion", 6), ("gen_veranda_wing", 2),
                         ("ring_pavilion_small", 6)]),
    ("tight", "big"): ("Market-town course", [("gen_garden_stand", 0), ("park_old_pavilion", 8), ("park_roof_terrace_stand", 0),
                       ("chester_tattersalls", 4)]),
    ("tight", "small"): ("Little country course", [("ring_pavilion_small", 6), ("gen_pavilion_small", 0), ("park_terrace", 3),
                         ("victorian_house", 8)]),
    ("ring", "big"): ("Floodlit stadium", [("park_tent_stand", 0), ("gen_cupola_stand", 0), ("york_stand_south", 0), ("park_terrace", 3)]),
    ("ring", "small"): ("Suburban park", [("gen_veranda_wing", 2), ("park_clock_house", 8), ("gen_pavilion_small", 0),
                        ("little_pavilion", 6)]),
    ("hill", "big"): ("Hill course, the bigger stand side", [("gen_cupola_stand", 0), ("park_tiered_stand", 0), ("york_clock_tower", 8),
                      ("park_balcony_stand", 0), ("old_pavilion_wing", 4)]),
    ("hill", "small"): ("Northern hill course", [("gen_pavilion_stand", 0), ("victorian_pavilion", 6), ("chester_tattersalls", 4)]),
    ("downs", "big"): ("Downland course", [("park_tent_stand", 0), ("gen_pavilion_stand_red", 0), ("park_roof_terrace_stand", 0),
                       ("york_pavilions", 6)]),
    ("downs", "small"): ("Seaside downs", [("gen_pavilion_stand_red", 0), ("park_terrace", 3), ("ring_pavilion", 6)]),
}
# Pieces with no standing terrace of their own (owner, 19 Nov 23:57: "make sure all those grandstands have a proper terrace
# of standing steps built into them"): a terrace module (gen_terrace_<w>) goes in front of each and the building is set
# back behind it. (The little lookout and kiosks are not grandstands: none.)
NEEDS_TERRACE = {"old_pavilion_wing", "park_old_pavilion", "ring_pavilion", "ring_pavilion_small", "victorian_house",
                 "york_clock_tower", "york_pavilions", "park_clock_house"}
TERRACE_WIDTHS = (18, 20, 24, 26, 28, 30, 32)
SOURCES = ["park_stands", "york_stands", "july_stands", "rowley_stands", "chester_stands_kit", "generic_stands_kit"]
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


def dress(cid, fid, hand, size, S, L, C):
    I = info()
    side = -1.0 if hand < 0 else 1.0                  # the stand side's z sign (world); the infield is the other side
    zi = -side
    runin = C["facts"]["run-in m"]
    mix_name, mix = CLUSTERS[(fid, size)]
    big = size == "big"
    # ---- the stands: one cluster round the post, about 40% of it past the post (towards the post-end bend, never into it)
    def terrace_for(piece):
        if piece not in NEEDS_TERRACE: return None
        w = I[piece]["width"]
        return "gen_terrace_%d" % min(TERRACE_WIDTHS, key=lambda t: (abs(t - w), t))
    span = lambda p: max(I[p]["width"], I[terrace_for(p)]["width"] if terrace_for(p) else 0)
    T = sum(span(p) for p, _ in mix) + GAP * (len(mix) - 1)
    x0 = max(-0.4 * T, -(S["post_gap"] - 22.0))
    pieces, x, depth = [], x0, 0.0
    for piece, back in mix:
        g = I[piece]; w = span(piece); off = g.get("offset", 0.0) * (1 if side < 0 else -1)
        cx = x + w / 2                                 # where the piece's body is centred
        tm = terrace_for(piece)
        if tm:                                         # its standing terrace at the front line, the building behind it
            pieces.append([tm, round(cx, 2), 0.0, 0.85])
            back = I[tm]["depth"] - 0.4
        pieces.append([piece, round(cx - off, 2), back, 0.85])
        x += w + GAP; depth = max(depth, g.get("depth", 30) + back)
    chain = (x0, x - GAP)
    zr = side * (W + 0.5)
    zs = lambda m: round(zr + side * m, 1)             # metres beyond the outer rail on the stand side
    zf = lambda m: round(zi * m, 1)                    # metres into the infield from the inside rail
    back_z = FRONT + depth + 18.0
    # ---- festivals: the infield opposite the run-in; the stand side up the course past the stands
    # the infield festival opposite the stands, round the post too
    fx0 = max(chain[0] - 30.0, -(S["post_gap"] - 10.0))
    fx1 = min(chain[1] + (110.0 if big else 50.0), runin - 70.0)
    fd = 100 if big else 70
    fests = [{"name": "infield opposite the stands", "kit": "infield",
              "poly": [[fx0, zf(2)], [fx1, zf(2)], [fx1, zf(fd)], [fx0, zf(fd)]],
              "offTurf": 10.0, "dens": 0.035 if big else 0.025, "ground": "patches", "patch": 3.5, "kitScale": 1.0 if big else 0.8,
              "railCrowd": {"from": 1.5, "to": 7.0, "dens": 0.6 if big else 0.45},
              "balloonRows": {"n": 5, "gap": 10, "every": 130 if big else 170, "in": 6, "start": 45, "end": 30}}]
    sx0, sx1 = chain[1] + 22.0, min(chain[1] + 200.0, runin - 40.0)
    if big and sx1 - sx0 > 80:
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
        "lawnDens": 0.3 if big else 0.22, "lawnFront": {"from": 0.8, "to": 10.0, "dens": 0.55 if big else 0.45},
        "lawnX": [chain[0] - 10, chain[1] + 10],
        "treesClearOfBuildings": 5.0,
        "farBelt": {"from": 175.0, "to": 245.0, "every": 34.0, "scale": [1.9, 2.5], "chance": 0.5},
    }
    if not big or sx1 - sx0 <= 80:                     # (a smaller course, or a short run-in: trees on past the stands)
        perimeter["gapTrees"].append({"note": "past the stands, up the course", "poly": [[chain[1] + 10, zs(30)], [runin + 60, zs(30)],
                                      [runin + 60, zs(back_z + 20)], [chain[1] + 10, zs(back_z + 20)]],
                                      "offTurf": 20, "every": 13, "chance": 0.55, "standMargin": 6.0})
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
        "prelude": {"eye": [[round(-S["post_gap"] - 30), 45, round(zi * 140)], [round(-S["post_gap"] - 2), 42, round(zi * 128)]],
                    "at": [[round((chain[0] + chain[1]) / 2 + 40), 10, round(side * 80)], [round((chain[0] + chain[1]) / 2 + 68), 10, round(side * 82)]], "fov": 50,
                    "note": "the overview, as Newbury's: high over the post-end bend, looking up the course with the stands "
                            "on one side and the festival on the other"},
        "stallsAway": True,
        "lede": f"{S['name']}, {'left' if hand < 0 else 'right'}-handed: one of the five generic courses that every course "
                f"without its own build races on for now ({S['kind']}), with the {'bigger' if big else 'smaller'} of its two stand sides. "
                f"{S['about']} Dressed as a {mix_name.lower()}.",
        "notes": [["Stands in for.", S["standsIn"] + "."],
                  ["The track.", f"About {C['facts']['circuit f']}f round, a {C['facts']['run-in f']}f run-in. Drawn from a "
                                 "few numbers (the corners and bends of the loop, the chutes), so it can be reshaped quickly."],
                  ["The stands.", f"{mix_name}: old small stands and pavilions clustered round the winning post, near the end "
                                  "of the straight, the crowd up to the rail, the festival in the infield opposite."],
                  ["Running slowly?", "Choose Medium or Low under Quality in the race view's bar. Auto steps down by itself."]],
    }
    return {"perimeter": perimeter, "stands": stands, "view": view, "mix": mix_name}
