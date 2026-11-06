# Paper cut-outs of the board's buildings: the painting inside a hand-traced outline, with a cream die-cut edge
import json
from PIL import Image, ImageDraw, ImageFilter
SRC = __import__("os").path.join(__import__("os").path.dirname(__file__), "../../assets/maps/newmarket-map.webp")
OUT = __import__("os").path.join(__import__("os").path.dirname(__file__), "../img/")
S, EDGE = 4, 7          # upscale, die-cut border in output pixels
im = Image.open(SRC).convert("RGB")
CUTS = {
  "tatts": [(767,521),(789,501),(806,499),(812,491),(828,491),(833,499),(856,503),(872,528),(865,545),(863,581),(783,581),(781,546),(767,532)],
  "stud": [(807,425),(904,397),(951,393),(1042,424),(1044,448),(1019,449),(951,421),(906,421),(823,449),(806,447)],
  "stables-back": [(560,700),(583,686),(750,643),(936,690),(938,729),(752,679),(601,722),(601,761),(565,763)],
  "stables-front": [(603,812),(918,743),(941,751),(941,783),(613,837),(603,831)],
}
meta = {}
for name, poly in CUTS.items():
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    pad = 3
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    crop = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * S, (y1 - y0) * S), Image.LANCZOS)
    mask = Image.new("L", crop.size, 0)
    ImageDraw.Draw(mask).polygon([((x - x0) * S, (y - y0) * S) for x, y in poly], fill=255)
    inner = mask.filter(ImageFilter.GaussianBlur(1.2))
    outer = mask.filter(ImageFilter.MaxFilter(EDGE * 2 + 1)).filter(ImageFilter.GaussianBlur(1.5))
    card = Image.new("RGBA", crop.size, (246, 238, 220, 0))
    card.putalpha(outer)                                   # the cream die-cut border
    art = crop.convert("RGBA"); art.putalpha(inner)
    card = Image.alpha_composite(card, art)
    card.save(OUT + f"cut-{name}.png", optimize=True)
    meta[name] = {"x0": x0, "y0": y0, "x1": x1, "y1": y1}
print(json.dumps(meta))
