"""Contact sheets for the landscape workshop: python3 tools/blender/workshop_sheet.py <dir> (writes trees.jpg, turf.jpg)."""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont
d = sys.argv[1]; L = json.load(open(os.path.join(d, "labels.json")))
def font(sz):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()
# skies: the same tile (original trees, soft sage turf) finished with different gradients; the haze takes the horizon's colour
SKIES = {"1": ("Straw to pale teal", "#efecc6", "#b4d4cc"), "2": ("Straw to clear blue", "#f1ebc8", "#7fb3d8"),
         "3": ("Peach to soft blue", "#f6dcc0", "#8fb4da"), "4": ("Cream to deep teal", "#f0eed2", "#5f9fa3")}
src = os.path.join(d, "trees_A")
if os.path.exists(src + "_raw.png"):
    import shutil, subprocess
    L["sky"] = {}
    for k, (name, lo, hi) in SKIES.items():
        for suf in ("_raw.png", "_dist.png"): shutil.copy(src + suf, os.path.join(d, "sky_" + k + suf))
        subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2_post.py"), os.path.join(d, "sky_" + k), "70", "520", "0.6", lo, hi], stdout=subprocess.DEVNULL)
        L["sky"][k] = name
for group, cols in (("trees", 2), ("turf", 2), ("sky", 2)):
    keys = [k for k in L[group] if os.path.exists(os.path.join(d, f"{group}_{k}.png"))]
    if not keys: continue
    ims = [Image.open(os.path.join(d, f"{group}_{k}.png")).convert("RGB") for k in keys]
    W, H = ims[0].size; gap = max(6, W // 120); rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W + (cols + 1) * gap, rows * H + (rows + 1) * gap), (244, 238, 224))
    f = font(max(14, W // 34))
    for i, (k, im) in enumerate(zip(keys, ims)):
        x, y = gap + (i % cols) * (W + gap), gap + (i // cols) * (H + gap)
        sheet.paste(im, (x, y)); dr = ImageDraw.Draw(sheet)
        text = f"{k}  {L[group][k]}"; tw = dr.textlength(text, font=f); pad = f.size // 2
        dr.rectangle((x, y, x + tw + pad * 2, y + f.size + pad * 1.4), fill=(38, 53, 43))
        dr.text((x + pad, y + pad * 0.55), text, font=f, fill=(244, 238, 224))
    sheet.save(os.path.join(d, group + ".jpg"), quality=90); print(group, sheet.size)
