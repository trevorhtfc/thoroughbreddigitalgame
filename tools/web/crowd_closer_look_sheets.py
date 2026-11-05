"""Contact sheets for a closer look at the two favourite crowd figure directions, the refined skittle (1) and
the painted cut-outs (3), with two variations of each and a mix (reference/crowd/figures/closer/).

    python3 tools/web/crowd_closer_look_sheets.py <lineups_dir> <scenes_dir> <out_dir>

lineups_dir: line-<set>-<first>.png from race-view/crowd-lineup.html?figures=<set>&first=<0|6>&count=6
             (1500 x 640 at deviceScaleFactor 2), for sets 1, 7, 8, 3, 9, 10.
scenes_dir:  <view>-<key>.png from race-view/crowd-review.html (crowd A, summer colours; the field at the post),
             for views rail, track, lawn, tv, above, far and keys 1, 1B, 1C, 3, 3B, 3C, mix; and run.log (one JSON
             line per key, with the crowd's triangles in each view).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

lin, scn, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
F = "/usr/share/fonts/truetype/dejavu/"
cream, green, ink, gold = (244, 234, 210), (31, 90, 56), (79, 93, 74), (184, 149, 74)
font = lambda n, s: ImageFont.truetype(F + n, int(s))
SET = {"1": 1, "1B": 7, "1C": 8, "3": 3, "3B": 9, "3C": 10}
NAME = {"1": "1  Refined skittle", "1B": "1B  Skittle, dressed up", "1C": "1C  Skittle with arms",
        "3": "3  Painted cut-outs", "3B": "3B  Cut-outs, clean poster", "3C": "3C  Cut-outs, inked",
        "mix": "Mix  Cut-outs, with 1C on the lawn and rail"}
NOTE = {"1": "As shown before.",
        "1B": "Coat-tails and a waistcoat V for the gents, taller toppers, wider brims, hair up.",
        "1C": "1B with simple arms: at the sides, on a hip, a race card, a bag.",
        "3": "As shown before: soft light, brush strokes, a darker edge.",
        "3B": "The same drawings as a poster: two flat tones per shape, no brush.",
        "3C": "The same drawings with a dark ink outline, like a storybook.",
        "mix": "3D figures where the cameras come close; flat ones in the stand, the boxes and across the track."}
VIEW = {"rail": "At the rail,\neye level", "track": "From the track", "lawn": "The lawn\nby the post",
        "tv": "TV distance:\nthe grandstand\ncamera", "above": "From above\n(a high camera)", "far": "Across the\ntrack: the\nfar side"}
cost = {}
for line in open(os.path.join(scn, "run.log")):
    if line.startswith("{"):
        d = json.loads(line)
        cost[d["key"]] = d["tris"]


def k(v):
    return "%dk" % round(v / 1000) if v else "?"


# ------------------------------------------------------------------ 1. the six close line-ups
rows = []
for key in ["1", "1B", "1C", "3", "3B", "3C"]:
    a, b = (Image.open(os.path.join(lin, "line-%d-%d.png" % (SET[key], h))).convert("RGB") for h in (0, 6))
    w, h = a.size
    row = Image.new("RGB", (w * 2, h))
    row.paste(a, (0, 0)); row.paste(b, (w, 0))
    rows.append((key, row.resize((w, h // 2), Image.LANCZOS)))
w, h = rows[0][1].size
pad, lab, head = 30, 96, 150
sheet = Image.new("RGB", (w + 2 * pad, head + len(rows) * (h + lab + pad) + pad), cream)
d = ImageDraw.Draw(sheet)
d.text((pad, 28), "Crowd figures  ·  a closer look at 1 and 3", font=font("DejaVuSerif-Bold.ttf", 54), fill=green)
d.text((pad, 98), "The same twelve outfits and places in every row (summer colours). 1B and 1C build on 1; 3B and 3C are the same drawings as 3 in other finishes.",
       font=font("DejaVuSans.ttf", 25), fill=ink)
for i, (key, im) in enumerate(rows):
    y = head + pad + i * (h + lab + pad)
    d.text((pad, y), NAME[key], font=font("DejaVuSans-Bold.ttf", 36), fill=green)
    d.text((pad, y + 48), NOTE[key], font=font("DejaVuSans.ttf", 25), fill=ink)
    sheet.paste(im, (pad, y + lab))
    d.rectangle([pad - 1, y + lab - 1, pad + w, y + lab + h], outline=gold)
sheet.save(os.path.join(out, "closer-lineup.png"), optimize=True)
print("closer-lineup", sheet.size)


# ------------------------------------------------------------------ grids of scene views
def grid(rows_, cols_, cell, title, sub, fname, row_label, col_label, cap=None):
    pw, ph = 960, 540
    pad, lab_w, head, col_h = 24, 300, 140, 64
    W, H = lab_w + len(cols_) * (pw + pad) + pad, head + col_h + len(rows_) * (ph + pad) + pad
    sh = Image.new("RGB", (W, H), cream)
    d = ImageDraw.Draw(sh)
    d.text((pad, 24), title, font=font("DejaVuSerif-Bold.ttf", 50), fill=green)
    d.text((pad, 90), sub, font=font("DejaVuSans.ttf", 24), fill=ink)
    for c, cv in enumerate(cols_):
        x = lab_w + c * (pw + pad)
        d.text((x, head + 6), col_label(cv), font=font("DejaVuSans-Bold.ttf", 30), fill=green)
    for r, rv in enumerate(rows_):
        y = head + col_h + r * (ph + pad)
        d.multiline_text((pad, y + 10), row_label(rv), font=font("DejaVuSans-Bold.ttf", 28), fill=green, spacing=6)
        for c, cv in enumerate(cols_):
            x = lab_w + c * (pw + pad)
            p = os.path.join(scn, cell(rv, cv))
            im = Image.open(p).convert("RGB").resize((pw, ph), Image.LANCZOS)
            sh.paste(im, (x, y))
            if cap:
                t = cap(rv, cv)
                if t:
                    tw = d.textlength(t, font=font("DejaVuSans.ttf", 22))
                    d.rectangle([x + pw - tw - 20, y + ph - 38, x + pw, y + ph], fill=(244, 234, 210))
                    d.text((x + pw - tw - 10, y + ph - 33), t, font=font("DejaVuSans.ttf", 22), fill=ink)
    sh.save(os.path.join(out, fname), optimize=True)
    print(fname, sh.size)


views = ["rail", "track", "lawn", "tv", "above", "far"]
wrap = lambda s: s
crowd_cap = lambda v, key: "crowd: %s triangles" % k(cost.get(key, {}).get(v))
grid(views, ["1C", "3", "mix"], lambda v, key: "%s-%s.png" % (v, key),
     "Head to head  ·  1C, 3 and the mix in six camera views",
     "Crowd arrangement A (today's), summer colours, the field coming to the post. The crowd's triangles in each view are in the corner (today's figures: about 680k at TV distance).",
     "head-to-head.png", lambda v: wrap(VIEW[v]), lambda key: {"1C": "1C  Skittle with arms", "3": "3  Painted cut-outs", "mix": "Mix  Cut-outs + 1C near the stand"}[key], crowd_cap)
for fam, keys in (("skittle", ["1", "1B", "1C"]), ("cutouts", ["3", "3B", "3C"])):
    grid(["rail", "lawn", "tv", "above"], keys, lambda v, key: "%s-%s.png" % (v, key),
         "The %s variations  ·  %s" % ("skittle" if fam == "skittle" else "cut-out", ", ".join(keys)),
         "The same people and places in every panel. " + ("1B adds Edwardian touches; 1C adds arms." if fam == "skittle" else "3B is the poster finish; 3C is inked."),
         "variations-%s.png" % fam, lambda v: wrap(VIEW[v]), lambda key: NAME[key], crowd_cap)
