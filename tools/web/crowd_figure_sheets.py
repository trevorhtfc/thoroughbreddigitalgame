"""Contact sheets for the crowd figure options (reference/crowd/figures/).

    python3 tools/web/crowd_figure_sheets.py <frames_dir> <out_dir>

frames_dir holds line-<n>.png (race-view/crowd-lineup.html?figures=n, deviceScaleFactor 2), lawn-<n>.png and
wide-<n>.png (race-view/crowd-review.html?crowd=A&palette=summer&figures=n, the lawn and wide pockets,
deviceScaleFactor 2) for n = 0..6, and costs.json (triangles per figure and in the wide view, from the page).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
cost = json.load(open(os.path.join(src, "costs.json")))
F = "/usr/share/fonts/truetype/dejavu/"
cream, green, ink, gold = (244, 234, 210), (31, 90, 56), (79, 93, 74), (184, 149, 74)
NAMES = {0: "Today", 1: "Refined skittle", 2: "Fashion plate", 3: "Painted cut-outs", 4: "Low-poly faceted", 5: "Soft painterly", 6: "Lowry"}
LINES = {
    0: "For reference: today's figures. Cone or column, ball head, hat.",
    1: "Today's language, better form: shoulders, waist, flared dress, trousered legs, crisper hats, a tilt of the head.",
    2: "Tall, slender Edwardian: tail coats and waistcoats, cinched long dresses, very wide hats, tall top hats.",
    3: "Flat painted figures on cards that turn to face the camera. 32 drawn, tinted per person.",
    4: "Flat-shaded planes: arms at the sides, a hand on a hip or a race card, lapels, hair.",
    5: "Rounded, lumpy masses with dabs of hat and colour and a brushed finish. Made for TV distance.",
    6: "Thin, angular, a little hunched, on stick legs. In the summer colours.",
}
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MOOD = os.path.join(ROOT, "reference/crowd/ascot-scene-mood.png")


def font(name, size):
    return ImageFont.truetype(F + name, int(size))


def costline(n):
    c = cost[str(n)]
    if n == 3:
        return "2 triangles per figure (a card)  ·  wide view: %sk crowd triangles (%s on today)" % (round(c["wide"] / 1000), c["vs"])
    return "%d triangles per figure (up to %d; %d far off)  ·  wide view: %sk crowd triangles%s" % (
        c["near"], c["nearMax"], c["far"], round(c["wide"] / 1000), "" if n == 0 else " (%s on today)" % c["vs"])


# ---------------------------------------------------------------- 1. line-up: one row per set
rows = [Image.open(os.path.join(src, "line-%d.png" % n)).convert("RGB") for n in range(7)]
w, h = rows[0].size
k = w / 3000
pad, lab, head = int(30 * k), int(330 * k), int(130 * k)
W, H = lab + w + pad * 2, head + 7 * (h + pad) + pad
sheet = Image.new("RGB", (W, H), cream)
d = ImageDraw.Draw(sheet)
d.text((pad, int(30 * k)), "Crowd figures  ·  six directions, and today's for reference", font=font("DejaVuSerif-Bold.ttf", 56 * k), fill=green)
d.text((pad, int(96 * k)), "Studio line-up: the same twelve outfits, places and light in every row (the race view's sun and sky, summer colours). No faces.",
       font=font("DejaVuSans.ttf", 26 * k), fill=ink)
for n, im in enumerate(rows):
    y = head + pad + n * (h + pad)
    sheet.paste(im, (lab + pad, y))
    d.rectangle([lab + pad - 1, y - 1, lab + pad + w, y + h], outline=gold)
    big = font("DejaVuSerif-Bold.ttf", 110 * k)
    d.text((pad, y + int(10 * k)), str(n), font=big, fill=gold if n == 0 else green)
    d.multiline_text((pad, y + int(150 * k)), NAMES[n].replace(" ", "\n", 1), font=font("DejaVuSans-Bold.ttf", 34 * k), fill=green, spacing=int(4 * k))
    c = cost[str(n)]
    d.text((pad, y + h - int(80 * k)), ("2 tris" if n == 3 else "%d tris" % c["near"]), font=font("DejaVuSans.ttf", 28 * k), fill=ink)
    d.text((pad, y + h - int(44 * k)), "wide: " + ("today" if n == 0 else c["vs"]), font=font("DejaVuSans.ttf", 28 * k), fill=ink)
sheet.save(os.path.join(out, "figures-lineup.png"), optimize=True)
print("line-up", sheet.size)


# ---------------------------------------------------------------- 2 and 3. in the scene: 2 x 4 panels, the mood image last
def grid(kind, crop, title, sub, mood_crop, fname):
    frames = []
    for n in range(7):
        im = Image.open(os.path.join(src, "%s-%d.png" % (kind, n))).convert("RGB")
        frames.append(im.crop(crop) if crop else im)
    pw, ph = frames[0].size
    if pw > 1460:                                           # keep the sheet a sensible size
        s = 1460 / pw
        frames = [f.resize((int(pw * s), int(ph * s)), Image.LANCZOS) for f in frames]
        pw, ph = frames[0].size
    mood = Image.open(MOOD).convert("RGB")
    mood = mood.crop(mood_crop) if mood_crop else mood
    r = max(pw / mood.width, ph / mood.height)
    mood = mood.resize((int(mood.width * r) + 1, int(mood.height * r) + 1), Image.LANCZOS)
    mood = mood.crop(((mood.width - pw) // 2, (mood.height - ph) // 2, (mood.width - pw) // 2 + pw, (mood.height - ph) // 2 + ph))
    q = pw / 1460
    pad, lab, head = int(24 * q), int(92 * q), int(120 * q)
    W, H = 2 * pw + 3 * pad, head + 4 * (ph + lab + pad) + pad
    sheet = Image.new("RGB", (W, H), cream)
    d = ImageDraw.Draw(sheet)
    d.text((pad, int(22 * q)), title, font=font("DejaVuSerif-Bold.ttf", 44 * q), fill=green)
    d.text((pad, int(76 * q)), sub, font=font("DejaVuSans.ttf", 22 * q), fill=ink)
    panels = [(n, frames[n]) for n in range(7)] + [("mood", mood)]
    for i, (n, im) in enumerate(panels):
        c, r_ = i % 2, i // 2
        x, y = pad + c * (pw + pad), head + pad + r_ * (ph + lab + pad)
        if n == "mood":
            d.text((x, y + int(6 * q)), "The target mood", font=font("DejaVuSans-Bold.ttf", 30 * q), fill=gold)
            d.text((x, y + int(48 * q)), "reference/crowd/ascot-scene-mood.png (illustration, for comparison)", font=font("DejaVuSans.ttf", 21 * q), fill=ink)
        else:
            d.text((x, y + int(6 * q)), "%d  %s" % (n, NAMES[n]), font=font("DejaVuSans-Bold.ttf", 30 * q), fill=gold if n == 0 else green)
            d.text((x, y + int(48 * q)), costline(n), font=font("DejaVuSans.ttf", 21 * q), fill=ink)
        sheet.paste(im, (x, y + lab))
    sheet.save(os.path.join(out, fname), optimize=True)
    print(fname, sheet.size)


grid("lawn", (1000, 470, 2560, 1180), "Crowd figures in the scene  ·  the rail and lawn by the winning post",
     "Crowd arrangement A (today's), summer colours; the same people and places in every panel. A crop of the 'lawn' camera at double resolution.",
     (0, 440, 780, 793), "figures-in-scene.png")
grid("wide", None, "Crowd figures at TV distance  ·  the grandstand camera on the winning line",
     "Crowd arrangement A (today's), summer colours; looking up the straight. Triangle counts are the crowd's alone in this view (today: 682k).",
     None, "figures-tv-distance.png")
