"""Label the July Course's top-down render (reference/newmarket-july/renders/plan.png) as a plan for the owner to mark
up: building names, the post, the furlong poles, the direction of running, a scale bar.
    python3 tools/blender/plan_labels.py   ->  reference/newmarket-july/plan-markup.png
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "tools/course/newmarket")
import july_layout as J
X0, X1, Z0, Z1, PX = -200.0, 450.0, -110.0, 150.0, 3000
S = PX / (X1 - X0)
TOP, BOT = 110, 120
im = Image.open("reference/newmarket-july/renders/plan.png").convert("RGB")
W_, H_ = im.size
out = Image.new("RGB", (W_, H_ + TOP + BOT), "#fbf8f1"); out.paste(im, (0, TOP))
d = ImageDraw.Draw(out)
F = lambda n, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), n)
INK, RED = "#2b2a33", "#c0392b"
def P(x, z): return ((x - X0) * S, (z - Z0) * S + TOP)
def tag(x, z, text, size=22, fill="#ffffffe6", ink=INK, bold=True):
    px, py = P(x, z); f = F(size, bold)
    l, t, r, b = d.textbbox((0, 0), text, font=f); w, h = r - l, b - t
    d.rounded_rectangle((px - w / 2 - 8, py - h / 2 - 6, px + w / 2 + 8, py + h / 2 + 8), 8, fill="#ffffff", outline="#b9b2a2")
    d.text((px - w / 2, py - h / 2 - t), text, font=f, fill=ink)
# the stand side's buildings
for s_ in J.STANDS:
    x = sum(s_["x"]) / 2; z = -(s_["front"] + s_["depth"] / 2)
    small = s_["x"][1] - s_["x"][0] < 20
    if s_["name"] == "Judge's box":
        tag(x, -32, "Judge's box", 18)
    elif small:
        tag(x, z - 12 if s_["name"] != "Bell tent" else z + 20, s_["name"], 17)
    else:
        tag(x, z, s_["name"], 21)
tag(-45, -60, "gap marquee + trees", 15, bold=False)
tag(100.5, -58, "gap marquee + trees", 15, bold=False)
tag(177, -58, "gap marquee + trees", 15, bold=False)
tag(245, -58, "gap marquee + trees", 15, bold=False)
tag(300, -48, "marquee row + trees", 15, bold=False)
tag(-120, -48, "marquee row + tree wall", 15, bold=False)
tag(400, -40, "stand-side festival (to 3.5f)", 17)
tag(60, -6, "packed lawns", 15, bold=False)
# the far side
W = J.TRACK_W
tag(2.5, W + 23, "Tiered stand", 18)
tag(300, W + 8, "crowd along the far rail", 15, bold=False)
tag(330, W + 72, "far-side festival: marquees and pavilions among big trees (from 3f to the finish)", 18)
tag(-140, W + 70, "big trees (towards the Dyke and the Rowley Mile)", 16, bold=False)
# the post, furlong poles, direction of running
px, _ = P(0, 0); d.line((px, P(0, -4)[1], px, P(0, W + 4)[1]), fill=RED, width=6)
tag(0, W / 2, "POST", 20, ink=RED)
for f in (1, 2):
    tag(f * J.F, W / 2, "%df" % f, 20)
ax, ay = P(-110, W / 2); bx, _ = P(-190, W / 2)
d.line((ax, ay, bx, ay), fill="white", width=8); d.polygon([(bx - 4, ay), (bx + 26, ay - 16), (bx + 26, ay + 16)], fill="white")
tag(-80, W / 2, "direction of running", 17)
tag(-150, W / 2 + 13, "the run-out", 15, bold=False)
# title, key and scale
d.text((30, 22), "July Course: the run-in, from above (draft, 8 Nov 2026)", font=F(40, True), fill=INK)
d.text((30, 72), "Stand side at the top, far side (towards the Dyke) at the bottom. For marking up.", font=F(24), fill="#5f5b52")
y = H_ + TOP + 30
x0 = 30; d.line((x0, y + 20, x0 + 100 * S, y + 20), fill=INK, width=5)
for k in range(0, 101, 25): d.line((x0 + k * S, y + 10, x0 + k * S, y + 30), fill=INK, width=3)
for k in range(0, 101, 25):
    t_ = "%d m" % k if k == 100 else str(k)
    d.text((x0 + k * S - d.textlength(t_, font=F(20)) / 2 + (12 if k == 100 else 0), y + 38), t_, font=F(20), fill=INK)
d.text((x0 + 100 * S + 50, y + 8), "Camera: the stand camera sits on the judge's box roof, looking across to the far side.  "
       "The head-on camera is further down the run-out (off the plan, left).", font=F(22), fill="#5f5b52")
out.save("reference/newmarket-july/plan-markup.png", optimize=True)
print(out.size)
