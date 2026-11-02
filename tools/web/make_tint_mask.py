"""Pack the neutral horse's tint masks into one RGB texture for the race view.

    python make_tint_mask.py <tint_masks_dir> <out.png> [size] [--build]

R = coat, G = points (mane, tail, lower legs), B = jockey silk areas on the
body mesh. With --build, B also takes any leftover coloured texels in the
neutral texture (traces of the model's original silks); the Blender steps use
that version to find silk patches. Engines use the plain version and show
everything outside the masks in neutral grey.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

d, out = sys.argv[1], sys.argv[2]
args = [a for a in sys.argv[3:] if not a.startswith("--")]
size = int(args[0]) if args else 1024
build = "--build" in sys.argv
load = lambda f: Image.open(f"{d}/{f}").convert("L")
coat, points, silk = load("coatmask.png"), load("pointsmask.png"), load("silkmask.png")
n = np.asarray(Image.open(f"{d}/neutral_basecolor.png").convert("RGB")).astype(float)
leftover = ((n.max(2) - n.min(2)) > 28).astype(np.uint8) * 255
leftover = Image.fromarray(leftover).filter(ImageFilter.MaxFilter(7))
b = np.maximum(np.asarray(silk), np.asarray(leftover)) if build else np.asarray(silk).copy()
b[np.asarray(coat) > 127] = 0
b[np.asarray(points) > 127] = 0
chans = [coat, points, Image.fromarray(b)]
Image.merge("RGB", [c.resize((size, size), Image.LANCZOS) for c in chans]).save(out, optimize=True)
print("saved", out)
