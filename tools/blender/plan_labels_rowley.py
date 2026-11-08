"""Label the Rowley Mile stand-side preview from above (reference/newmarket/renders/plan.png) for marking up.
    python3 tools/blender/plan_labels_rowley.py  ->  reference/newmarket/plan-stands-markup.png
"""
import sys, math
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "tools/course/newmarket")
import draft_layout as R
W = R.TRACK_W
CX, CZ, SCALE, PX = 110.0, 75.0, 460.0, 2400
S = PX / SCALE
# turned half round so the stands are at the top, as on the July Course's plan (the horses then run left to right)
im = Image.open("reference/newmarket/renders/plan.png").convert("RGB").rotate(180); w, h = im.size
TOP, BOT = 100, 70
out = Image.new("RGB", (w, h + TOP + BOT), "#fbf8f1"); out.paste(im, (0, TOP)); d = ImageDraw.Draw(out)
F = lambda n, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), n)
INK, RED = "#2b2a33", "#c0392b"
def P(x, z): return (w / 2 - (x - CX) * S, h / 2 - (z - CZ) * S + TOP)
def tag(x, z, text, size=20, ink=INK, bold=True):
    px, py = P(x, z); f = F(size, bold); l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.rounded_rectangle((px - (r - l) / 2 - 8, py - (b - t) / 2 - 6, px + (r - l) / 2 + 8, py + (b - t) / 2 + 8), 8, fill="#ffffff", outline="#b9b2a2")
    d.text((px - (r - l) / 2, py - (b - t) / 2 - t), text, font=f, fill=ink)
for st in R.STAND_PIECES:
    if "turn" in st:
        a = math.radians(st["turn"]); d_ = st["depth"] / 2
        x, z = st["at"][0] - d_ * math.sin(a), W + st["at"][1] - d_ * math.cos(a)
    else: x, z = sum(st["x"]) / 2, W + st["front"] + (18 if st["piece"] == "millennium_stand" else 6)
    if st["piece"] == "judges_kiosk": z -= 4
    tag(x, z, st["name"], 18 if st["piece"] in ("judges_kiosk", "victorian_pavilion") else 21)
x0, _ = P(0, 0); d.line((x0, P(0, -3)[1], x0, P(0, W + 3)[1]), fill=RED, width=6); tag(0, W / 2, "POST", 20, ink=RED)
tag(R.F, W / 2, "1f", 20)
ax, ay = P(-30, W / 2); bx, _ = P(-80, W / 2)
d.line((ax, ay, bx, ay), fill="white", width=8); d.polygon([(bx + 4, ay), (bx - 24, ay - 15), (bx - 24, ay + 15)], fill="white")
tag(-55, W / 2 + 10, "direction of running", 15, bold=False)
tag(0, -6, "finish line (far rail)", 15, bold=False)
tag(120, W + 22, "lawns", 15, bold=False); tag(310, W + 30, "festival", 20)
d.text((24, 20), "Rowley Mile: the stands from above (draft, 8 Nov 2026)", font=F(36, True), fill=INK)
d.text((24, 64), "Stands at the top, the far side (towards the Dyke) at the bottom; the horses run left to right. For marking up.", font=F(22), fill="#5f5b52")
y = h + TOP + 22; d.line((24, y + 12, 24 + 100 * S, y + 12), fill=INK, width=5)
for k in range(0, 101, 25):
    d.line((24 + k * S, y + 4, 24 + k * S, y + 20), fill=INK, width=3)
d.text((24 + 100 * S + 16, y), "100 m", font=F(20), fill=INK)
out.save("reference/newmarket/plan-stands-markup.png", optimize=True); print(out.size)
