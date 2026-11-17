"""The kit courses' stand configurator: every course without a full build, grouped into the three generic courses
(the Park, the Tight Track, the Hill Track); each family's stand side cut into fixed plots; each course a choice of
crib-sheet module for each plot.

    python3.11 tools/course/kit/stand_config.py            # writes courses/kit/stand-config.json and the plot sheets
    python3.11 tools/course/kit/stand_config.py --import export.json   # keep the page's choices (stand-choices.json)

Owner, 17 Nov 2026: "shall we now build a standard course configurator? ... group all courses we need into the 3
primary types ... a sort of plot diagram for the different stand components for each course ... include all courses
we dont have full builds of for now.. so add newbury, donny etc into the park ... a framework with plots that we can
then assign modules from the crib sheet to each plot for each course". And (13:15): "if the footprints are essentially
fixed in the standard courses".

The plots are fixed footprints on one front line (the kit's: the front at the steps' foot, the back line 31.3 m),
left to right as seen from the course, the first by the winning post. A module sits centred in its plot; what's left
of the plot either side is filled with a low link (terrace infill), so the footprints never move. A plot may be left
empty (lawn). Modules come from the crib sheet (reference/stands/elevations/index.json, written by
tools/blender/stand_crib_sheet.py).

The courses' switches (hand, straight course, uphill finish, surface, scenery) are a first draft from general
knowledge, for checking; the Park's twelve are park_layout.py's VARIANTS. The assignments are my first draft for the
owner to change in the configurator page.
"""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
IDX = json.loads((REPO / "reference/stands/elevations/index.json").read_text())["pieces"]

# ---------------------------------------------------------------- the modules (from the crib sheet)
LONG = 80.0                       # wider than any plot: the flagship courses' own long stands, not offered


def klass(w):
    return "pavilion" if w < 33 else "side" if w < 50 else "main" if w <= LONG else "long"


MODULES = {code: {"label": p["label"], "course": p["course"], "width": p["width"], "height": p["height"],
                  "class": klass(p["width"]), "png": p["png"]} for code, p in IDX.items()}

# ---------------------------------------------------------------- the families and their plots
# plot: id, name, class (what it's sized for), width (the fixed footprint, m). 2 m between plots.
GAP = 2.0
PLOT_W = {"side": 48.0, "main": 78.0, "pavilion": 33.0}
FAMILIES = {
    "park": {"name": "The Park", "kind": "galloping: a big flat left-handed oval, a long straight",
             "plots": [("P1", "by the post", "side"), ("P2", "", "side"), ("P3", "main stand", "main"),
                       ("P4", "centre", "pavilion"), ("P5", "second stand", "main"), ("P6", "", "side"),
                       ("P7", "far end (big courses)", "side")]},
    "tight": {"name": "The Tight Track", "kind": "sharp, turning: a small oval about 1m1f round",
              "plots": [("T1", "by the post", "side"), ("T2", "main stand", "main"), ("T3", "centre", "pavilion"),
                        ("T4", "far end", "side")]},
    "hill": {"name": "The Hill Track", "kind": "stiff: right-handed, a downhill bend, an uphill straight",
             "plots": [("H1", "by the post", "side"), ("H2", "main stand", "main"), ("H3", "centre", "pavilion"),
                       ("H4", "second stand (big courses)", "main"), ("H5", "far end", "side")]},
}

# ---------------------------------------------------------------- the courses
# switches: hand (-1 left, 1 right), straight (furlongs; 0 = none), uphill (m over the last furlongs), surface, scenery,
# lights (floodlit), standIn (raced here until its own full build). plots: module code, None = lawn.
L, R = -1, 1
C = {}


def course(cid, name, fam, hand, straight, scenery, plots, surface="turf", uphill=0.0, lights=False, standIn=False, note=""):
    C[cid] = {"name": name, "family": fam, "hand": hand, "straight": straight, "uphill": uphill, "surface": surface,
              "scenery": scenery, "lights": lights, "standIn": standIn, "note": note,
              "plots": dict(zip([p[0] for p in FAMILIES[fam]["plots"]], plots + [None] * 10))}


T, B, RT, A, G, OP, V = ("park_tiered_stand", "park_balcony_stand", "park_roof_terrace_stand", "park_arch_stand",
                          "park_gable_stand", "park_old_pavilion", "park_victorian")
TE, M, GB, GS = "park_tent_stand", "park_mast_stand", "park_glass_box", "park_glass_box_small"
# The Park: the twelve, and the flagships-to-be raced here until their own builds (owner: "add newbury, donny etc")
course("park", "The Park (generic)", "park", L, 8, "parkland", [T, B, A, OP, G, RT], note="the approved run of six")
course("ayr", "Ayr", "park", L, 6, "seaside", [T, B, A, OP, G, RT])
course("bath", "Bath", "park", L, 5, "downland", [RT, B, G], uphill=6.0)
course("chelmsford", "Chelmsford City", "park", L, 5, "parkland", [GB, GS, M], surface="polytrack", lights=True)
course("ffoslas", "Ffos Las", "park", L, 6, "parkland", [GS, GB, TE])
course("leicester", "Leicester", "park", R, 7, "town", [V, B, G, OP], uphill=5.0)
course("lingfield", "Lingfield (turf)", "park", L, 7.5, "parkland", [GS, B, TE, OP])
course("newcastle", "Newcastle", "park", L, 8, "parkland", [GB, RT, M, GS], surface="tapeta", uphill=3.0, lights=True)
course("nottingham", "Nottingham", "park", L, 6, "town", [B, GS, G, OP])
course("redcar", "Redcar", "park", L, 8, "seaside", [RT, GS, A])
course("salisbury", "Salisbury", "park", R, 8, "downland", [T, B, G, OP], uphill=6.0)
course("wetherby", "Wetherby", "park", L, 5, "northern stone", [V, B, G])
course("yarmouth", "Yarmouth", "park", L, 8, "seaside", [B, GS, A, OP])
course("doncaster", "Doncaster", "park", L, 8, "parkland", [GB, B, M, GS, A, RT, GB], standIn=True)
course("newbury", "Newbury", "park", L, 8, "parkland", [GB, RT, M, GS, TE, B, GB], standIn=True)
course("haydock", "Haydock", "park", L, 6, "parkland", [T, B, M, OP, A, RT], standIn=True)
# The Tight Track
course("catterick", "Catterick", "tight", L, 5, "northern stone", [B, G, OP])
course("chester", "Chester", "tight", L, 0, "town", [T, A, OP, V])
course("kempton", "Kempton", "tight", R, 0, "parkland", [GB, M, GS], surface="polytrack", lights=True)
course("lingfieldaw", "Lingfield (AW)", "tight", L, 0, "parkland", [GS, TE, GB], surface="polytrack", lights=True)
course("musselburgh", "Musselburgh", "tight", R, 5, "seaside", ["pavilion_small", A, "victorian_house"])
course("ripon", "Ripon", "tight", R, 6, "northern stone", [T, G, OP, RT])
course("southwell", "Southwell", "tight", L, 5, "parkland", [GB, M, GS], surface="tapeta", lights=True)
course("thirsk", "Thirsk", "tight", L, 6, "northern stone", [B, G, OP])
course("windsor", "Windsor", "tight", R, 6, "town", ["old_pavilion", TE, "ring_pavilion"], note="a figure of eight; the kit's oval for now")
course("wolverhampton", "Wolverhampton", "tight", L, 0, "town", [GB, M, GS], surface="tapeta", lights=True)
# The Hill Track (right-handed; the left-handed ones mirrored), and the flagships-to-be raced here until their builds
course("beverley", "Beverley", "hill", R, 5, "northern stone", [T, G, OP], uphill=8.0)
course("brighton", "Brighton", "hill", L, 0, "seaside", [RT, A, GS], note="a horseshoe; cambered")
course("carlisle", "Carlisle", "hill", R, 6, "northern stone", [B, G, OP], uphill=6.0)
course("chepstow", "Chepstow", "hill", L, 8, "downland", [GB, TE, OP])
course("hamilton", "Hamilton", "hill", R, 6, "northern stone", [V, G], uphill=6.0)
course("pontefract", "Pontefract", "hill", L, 0, "northern stone", [B, A, OP], uphill=8.0)
course("epsom", "Epsom", "hill", L, 5, "downland", [GB, M, "york_pavilions", "york_stand_north", RT], standIn=True,
       note="undulating, Tattenham Corner; a flagship next")
course("goodwood", "Goodwood", "hill", R, 6, "downland", [B, TE, OP, TE, GS], standIn=True, note="a flagship next")
course("sandown", "Sandown", "hill", R, 5, "parkland", [GB, M, GS, A], uphill=6.0, standIn=True)
FULL = ["Ascot", "Newmarket (Rowley Mile)", "Newmarket (July Course)", "York"]     # their own full builds


def plot_layout(fam):
    """The plots' x extents (m, from the first plot's left edge)."""
    out, x = [], 0.0
    for pid, name, cl in FAMILIES[fam]["plots"]:
        w = PLOT_W[cl]
        out.append({"id": pid, "name": name, "class": cl, "x0": round(x, 2), "x1": round(x + w, 2), "width": w})
        x += w + GAP
    return out


def check():
    problems = []
    for cid, c in C.items():
        for pid, code in c["plots"].items():
            if code is None:
                continue
            if code not in MODULES:
                problems.append("%s %s: no module %s" % (cid, pid, code)); continue
            pw = {p["id"]: p["width"] for p in plot_layout(c["family"])}[pid]
            if MODULES[code]["width"] > pw + 0.01:
                problems.append("%s %s: %s is %.0f m, the plot %.0f m" % (cid, pid, code, MODULES[code]["width"], pw))
    return problems


def data():
    return {"_about": "The kit courses' stand configurator (tools/course/kit/stand_config.py). plots: fixed footprints along "
                      "one front line, left to right from the course, the first by the post; a module sits centred in its "
                      "plot, the rest of the plot a low link. courses[].plots: module code, or null for lawn. Drafts for "
                      "the owner to change.",
            "gap": GAP, "plotWidths": PLOT_W,
            "families": {k: {"name": f["name"], "kind": f["kind"], "plots": plot_layout(k)} for k, f in FAMILIES.items()},
            "modules": MODULES, "courses": C, "fullBuilds": FULL}


# ---------------------------------------------------------------- the plot sheets (one a family)
def sheets():
    from PIL import Image, ImageDraw, ImageFont
    F = lambda s, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), s)
    INK, MUTE = (40, 40, 44), (115, 115, 122)
    PX = 5.0                                                  # pixels a metre
    LEFT, TOP = 440, 230
    COLS = {"side": (226, 236, 246), "main": (246, 232, 214), "pavilion": (232, 242, 222)}
    cache = {}

    def mod_img(code):
        if code not in cache:
            im = Image.open(REPO / "reference/stands/elevations" / MODULES[code]["png"]).convert("RGBA")
            s = PX / IDX[code]["pxm"]
            cache[code] = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        return cache[code]
    out = REPO / "reference/kit"; out.mkdir(parents=True, exist_ok=True)
    for fam, f in FAMILIES.items():
        plots = plot_layout(fam)
        span = plots[-1]["x1"]
        rows = [(cid, c) for cid, c in C.items() if c["family"] == fam]
        RH = int(42 * PX) + 70
        W = int(LEFT + span * PX + 60); H = TOP + len(rows) * RH + 80
        im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
        d.text((30, 24), "%s: stand plots and each course's modules" % f["name"], fill=INK, font=F(34, True))
        d.text((30, 72), f["kind"] + ". Plots are fixed footprints on one front line, seen from the course, the first by "
               "the post. Draft for you to change.", fill=MUTE, font=F(19))
        # the plot diagram
        for p in plots:
            a, b = LEFT + p["x0"] * PX, LEFT + p["x1"] * PX
            d.rectangle([a, 120, b, 190], fill=COLS[p["class"]], outline=(150, 150, 160))
            d.text((a + 8, 126), p["id"] + "  " + p["class"], fill=INK, font=F(20, True))
            d.text((a + 8, 154), "%.0f m%s" % (p["width"], ("  " + p["name"]) if p["name"] else ""), fill=MUTE, font=F(16))
        d.text((30, 140), "The plots", fill=INK, font=F(22, True))
        x0 = LEFT; y0 = 205                                   # scale bar 0-50 m
        for i in range(5):
            d.rectangle([x0 + i * 10 * PX, y0, x0 + (i + 1) * 10 * PX, y0 + 8], fill=INK if i % 2 == 0 else "white", outline=INK)
        d.text((x0 + 50 * PX + 8, y0 - 6), "50 m", fill=MUTE, font=F(16))
        y = TOP
        for cid, c in rows:
            gy = y + RH - 44                                  # the ground line
            d.line([(LEFT - 10, gy), (LEFT + span * PX + 10, gy)], fill=(170, 170, 176), width=2)
            for p in plots:                                   # the plots' faint footprints
                a, b = LEFT + p["x0"] * PX, LEFT + p["x1"] * PX
                d.rectangle([a, gy, b, gy + 8], fill=COLS[p["class"]])
                code = c["plots"].get(p["id"])
                if not code:
                    d.text((a + 6, gy + 12), p["id"] + " lawn", fill=(170, 170, 176), font=F(14))
                    continue
                mi = mod_img(code)
                mw = MODULES[code]["width"] * PX
                cx = (a + b) / 2
                for sa, sb in ((a, cx - mw / 2), (cx + mw / 2, b)):  # the link either side
                    if sb - sa > 2:
                        d.rectangle([sa, gy - 3.5 * PX, sb, gy], fill=(222, 214, 196), outline=(196, 188, 170))
                im.paste(mi, (int(cx - mi.width / 2), int(gy - mi.height + IDX[code]["groundPx"] * PX / IDX[code]["pxm"])), mi)
                d.text((a + 6, gy + 12), p["id"] + " " + MODULES[code]["label"], fill=INK, font=F(14))
            sw = ["left-handed" if c["hand"] < 0 else "right-handed",
                  ("%gf straight" % c["straight"]) if c["straight"] else "no straight course",
                  c["surface"] if c["surface"] != "turf" else "turf", c["scenery"]]
            if c["uphill"]: sw.append("uphill %g m" % c["uphill"])
            if c["lights"]: sw.append("floodlit")
            d.text((30, y + 30), c["name"], fill=INK, font=F(24, True))
            d.text((30, y + 64), ", ".join(sw[:3]), fill=MUTE, font=F(16))
            d.text((30, y + 86), ", ".join(sw[3:]), fill=MUTE, font=F(16))
            if c["standIn"]:
                d.text((30, y + 110), "raced here until its own full build", fill=(170, 90, 50), font=F(16))
            if c["note"]:
                d.text((30, y + 132), c["note"], fill=MUTE, font=F(15))
            y += RH
        im.save(out / ("configurator-%s.jpg" % fam), quality=88)
        print("sheet", fam, im.size)


if __name__ == "__main__":
    CH = REPO / "courses/kit/stand-choices.json"             # the owner's choices from the page, kept over the drafts
    if "--import" in sys.argv:
        got = json.loads(Path(sys.argv[sys.argv.index("--import") + 1]).read_text())
        CH.parent.mkdir(parents=True, exist_ok=True)
        CH.write_text(json.dumps({"_about": "The owner's choices from the configurator page; they override the drafts in "
                                            "stand_config.py.", "plots": got.get("plots", {})}, indent=1))
    if CH.exists():
        for cid, plots in json.loads(CH.read_text()).get("plots", {}).items():
            if cid in C:
                C[cid]["plots"].update(plots)
    probs = check()
    for p in probs:
        print("CHECK:", p)
    (REPO / "courses/kit").mkdir(parents=True, exist_ok=True)
    (REPO / "courses/kit/stand-config.json").write_text(json.dumps(data(), indent=1))
    print("wrote courses/kit/stand-config.json: %d courses" % len(C))
    sheets()
