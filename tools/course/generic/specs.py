"""The five generic courses (owner, 19 Nov 2026: "spend some time building the suite of generic courses ... these will
form a stop gap meaning we can play any course we want"). The families are the course sheet's "Generic courses" tab
(17 Nov): the Park, the Tight Track, the Ring, the Hill Track and the Downs. Each is built both ways round.

Frame (u, v) as geometry.py: u along the home straight away from the post, v into the infield. Corners in running order
after the post; the last corner is the home bend. 'routes': a chute is the straight after a corner carried on backwards
beyond it ('chute': corner index); a route without one is the loop itself. 'starts': trip -> route ('trip' when the key
isn't the distance). 'ground': control points (u, v, metres against the post) for a smooth surface; none = flat.
"""
F = 201.168

FAMILIES = {
    # ------------------------------------------------------------------------------------------------ 1 The Park
    "park": {
        "name": "The Park",
        "kind": "galloping",
        "about": "A big, flat, galloping left- or right-handed oval with a long run-in and a straight mile, the teardrop "
                 "shape the owner settled on for the kit Park (16 Nov: 'a little more teardrop / angular ... 2 chutes').",
        "standsIn": "Newcastle, Redcar, Yarmouth, Salisbury, Chepstow, Ayr, Ffos Las, Nottingham, Leicester, Wetherby, Bath",
        "corners": [[-230, 0], [330, 470], [1150, 400], [1150, 0]],
        "radii": [110, 300, 165, 165],
        "post_gap": 120,
        "routes": {
            "straight": {"chute": 3, "note": "the straight mile"},
            "mile": {"chute": 2, "note": "the round mile, from the chute off the far bend"},
            "round": {"note": "the back straight, the far bend, the home bend; from the home straight once round for 2m+"},
            "chute": {"chute": 1, "note": "the far side carried on past the kink"},
            "far": {"chute": 0, "note": "the back straight carried on past the post-end bend"},
        },
        "starts": {"5f": "straight", "6f": "straight", "7f": "straight", "1m": "straight", "1m (round)": ["mile", "1m"],
                   "1m1f": "round", "1m2f": "chute", "1m4f": "round", "1m6f": "far", "2m": "round", "2m2f": "round"},
        "ground": None,
        "words": {"straight": "The straight mile", "mile": "Up the chute, round the far bend",
                  "round": "Down the back straight, round the far bend", "chute": "From the chute, round the far bend", "far": "From the far chute, round"},
    },
    # ------------------------------------------------------------------------------------------------ 2 The Tight Track
    "tight": {
        "name": "The Tight Track",
        "kind": "sharp oval with a sprint spur",
        "about": "A small, sharp oval of about 1m2f with tight turns, a 3f run-in and a 6f sprint course carried on from "
                 "the home straight.",
        "standsIn": "Catterick, Musselburgh, Southwell, Thirsk, Ripon, Windsor",
        "corners": [[-80, 0], [-80, 215], [840, 250], [840, 0]],
        "radii": [105, 105, 122, 122],
        "post_gap": 110,
        "routes": {
            "straight": {"chute": 3, "note": "the 6f sprint course"},
            "round": {"note": "the back straight, round the home bend; from the home straight once round for 1m3f+"},
            "chute": {"chute": 1, "note": "the back straight carried on past the post-end bend"},
            "long": {"chute": 3, "laps": 1, "note": "from the sprint course, past the post, once round"},
        },
        "starts": {"5f": "straight", "6f": "straight", "6f (round)": ["round", "6f"], "7f": "round", "1m": "round",
                   "1m1f": "chute", "1m2f": "chute", "1m3f": "round", "1m4f": "round", "1m6f": "long", "2m": "long"},
        "ground": None,
        "words": {"straight": "The sprint course", "round": "Down the back straight, round the home bend",
                  "chute": "From the chute, round the far bend", "long": "From the sprint course, once round"},
    },
    # ------------------------------------------------------------------------------------------------ 3 The Ring
    "ring": {
        "name": "The Ring",
        "kind": "very tight, near-circular",
        "about": "A tight stadium oval of about 1m½f with a short run-in (about 1½f): no straight course, the sprints go "
                 "round, chutes for the 6f, 7f and the long trips.",
        "standsIn": "Wolverhampton, Lingfield (all-weather), Kempton, Chelmsford City",
        "corners": [[-288, 0], [-288, 256], [410, 256], [410, 0]],
        "radii": [128, 128, 128, 128],
        "post_gap": 160,
        "routes": {
            "round": {"note": "the loop: the back straight, round the home bend; past the post once for 1m6f"},
            "chute": {"chute": 1, "note": "the back straight carried on past the post-end bend"},
            "top": {"chute": 3, "laps": 1, "note": "from a chute at the top of the home straight, past the post, once round"},
            "long": {"chute": 1, "laps": 1, "note": "from the chute, round, past the post, once more round"},
        },
        "starts": {"5f": "round", "6f": "chute", "7f": "chute", "1m": "round", "1m1f": "round", "1m2f": "top",
                   "1m4f": "top", "1m5f": "round", "2m": "long"},
        "ground": None,
        "words": {"round": "Round the Ring", "chute": "From the chute, round both bends",
                  "top": "From the top chute, once round", "long": "From the chute, twice past the stands"},
    },
    # ------------------------------------------------------------------------------------------------ 4 The Hill Track
    "hill": {
        "name": "The Hill Track",
        "kind": "stiff, uphill finish",
        "about": "A pear-shaped course of about 1m5f, wide at the stands end and narrow at the far end: a tight downhill turn into a 3½f run-in that climbs all the way to the post, "
                 "and a stiff 6f sprint course uphill from start to finish.",
        "standsIn": "Beverley, Carlisle, Hamilton, Pontefract, Bath, Chepstow (undulating)",
        "corners": [[-250, 0], [-120, 520], [880, 260], [1000, 0]],
        "radii": [190, 230, 120, 110],
        "post_gap": 120,
        "routes": {
            "straight": {"chute": 3, "note": "the uphill 6f sprint course"},
            "round": {"note": "the far side, the tight downhill home turn; once round for 1m6f+"},
            "chute": {"chute": 1, "note": "the far side carried on past the top bend"},
        },
        "starts": {"5f": "straight", "6f": "straight", "7f": "round", "1m": "round", "1m1f": "round", "1m2f": "chute",
                   "1m4f": "chute", "1m6f": "round", "2m": "round"},
        "ground": [[0, 0, 0.0], [300, 0, -2.5], [600, 0, -5.5], [880, 0, -8.0], [1000, 120, -7.5], [900, 250, -6.0],
                   [500, 360, -3.0], [150, 450, 0.5], [-120, 470, 2.5], [-250, 250, 2.0], [-150, 60, 0.8],
                   [1200, -20, -9.5], [1400, -20, -10.5], [400, 180, -2.5], [-500, -200, 1.0], [1600, 500, -6.0],
                   [-400, 800, 4.0], [1500, -400, -9.0], [500, -350, -3.0], [400, 800, 1.5]],
        "words": {"straight": "The uphill sprint course", "round": "Along the far side, the downhill turn, up the straight",
                  "chute": "From the chute, round the far side"},
    },
    # ------------------------------------------------------------------------------------------------ 5 The Downs
    "downs": {
        "name": "The Downs",
        "kind": "undulating, downhill turn",
        "about": "A rolling triangle of about 1m4f on the downs: a climb along the back straight, a sweeping downhill turn "
                 "into a 3f run-in that rises again in the last furlong, and a downhill 7f straight course.",
        "standsIn": "Brighton and Lingfield (turf), and the two big downland courses until their own builds are in the game",
        "corners": [[-220, 0], [500, 620], [1400, 0]],
        "radii": [130, 240, 180],
        "post_gap": 110,
        "routes": {
            "straight": {"chute": 2, "note": "the downhill 7f straight course"},
            "chute": {"chute": 1, "note": "the top side carried on past the apex"},
            "round": {"note": "round the downhill turn; once round for 1m6f"},
            "far": {"chute": 0, "note": "the back straight carried on past the post-end bend"},
            "long": {"chute": 2, "laps": 1, "note": "from the straight course, past the post, once round"},
        },
        "starts": {"5f": "straight", "6f": "straight", "7f": "straight", "1m": "chute", "1m1f": "chute", "1m2f": "round",
                   "1m4f": "far", "1m6f": "round", "2m": "long"},
        "ground": [[157, 0, 0.0], [360, 0, -1.6], [560, 0, 0.5], [820, 0, 4.5], [1150, 120, 9.0], [1300, 60, 10.0],
                   [1000, 300, 12.0], [500, 560, 15.0], [150, 300, 8.0], [-100, 100, 3.0], [-220, 0, 1.0],
                   [1500, -10, 11.0], [1800, -10, 13.0], [600, 250, 7.0], [-500, -200, 1.0], [-400, 600, 9.0],
                   [1700, 600, 16.0], [700, -350, -1.0], [1600, -400, 9.0], [500, 900, 15.0]],
        "words": {"straight": "The downhill straight course", "chute": "From the top chute, over the brow and down",
                  "round": "Up the back straight, round the downhill turn", "far": "From the far chute, up and over the downs",
                  "long": "From the straight course, once round"},
    },
}
