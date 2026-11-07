"""Smooth the baked light maps of the stand, the site pieces and the finish line into an even clay finish.

    python3 tools/course/smooth_lightmaps.py

Owner, 7 Nov: "the grandstand appears to have some funny texture... some reflection... some flashing bits. It should just
be smooth clay texture, no brick patterns." The Cycles bake (tools/blender/bake_static_world.py) leaves sampling noise in
the light maps: blotches across the walls, stepped bands on the small faces that read as brickwork, and specks that
shimmer as the camera moves.

Each map is a sheet of thousands of islands (one per face or group of faces) with gutters between them. Where the
islands are comes from raw/<name>_mask.png (white = island), rendered from the race view's own geometry by the rig's
uvmask script (each mesh drawn at its texture coordinates). Each island is blurred only with itself: a blur of the
light weighted by the island, divided by the blur of the weights, with the blur's size set by the island's size (a
broad wall gets a broad blur, a thin rail a small one). That keeps its broad shading (darker under a canopy, the sunlit
front) and drops the grain. Islands are done in four interleaved sets so neighbours don't bleed into each other. Then
the gutters are filled outwards from the islands' edges, so a far-off copy of the map (the graphics chip's mipmaps)
doesn't darken the edges.

Reads the untouched bakes from race-view/assets/baked/raw/ (copied there the first time), writes race-view/assets/baked/.
"""
import os, shutil
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, label, find_objects, binary_dilation

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(REPO, "race-view", "assets", "baked")
RAW = os.path.join(D, "raw")
BUCKETS = (1.2, 2.5, 5.0, 10.0)            # blur sizes (pixels); each island takes the one that suits its size

def nconv(a, w, s):
    ww = gaussian_filter(w, s)
    return np.stack([gaussian_filter(a[..., c] * w, s) for c in range(3)], -1) / np.maximum(ww, 1e-6)[..., None]

def smooth(name, k):
    raw = os.path.join(RAW, name)
    if not os.path.exists(raw): shutil.copy2(os.path.join(D, name), raw)
    a = np.asarray(Image.open(raw).convert("RGB"), dtype=np.float32) / 255.0
    m = np.asarray(Image.open(os.path.join(RAW, name.replace("_light.jpg", "_mask.png"))).convert("L").resize(a.shape[1::-1], Image.NEAREST)) > 127
    m = binary_dilation(m, iterations=1)                  # the rasterised islands can miss a pixel at their edges
    lab, n = label(m)
    size = np.zeros(n + 1, np.float32)
    for i, sl in enumerate(find_objects(lab), 1):
        size[i] = min(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start)   # the island's smaller side, in pixels
    want = size * k                                       # blur about a fraction of the island's size
    pick = np.digitize(want, [(BUCKETS[j] + BUCKETS[j + 1]) / 2 for j in range(len(BUCKETS) - 1)])
    pick[0] = -1
    out = a.copy()
    for b, s in enumerate(BUCKETS):
        for c in range(4):                                # four interleaved sets of islands
            ids = np.where((pick == b) & (np.arange(n + 1) % 4 == c))[0]
            if not len(ids): continue
            w = np.isin(lab, ids)
            sm = nconv(a, w.astype(np.float32), s)
            out[w] = sm[w]
    # fill the gutters outwards from the islands
    have = m.astype(np.float32)
    for s in (2, 4, 8, 16, 32):
        fill = nconv(out, have, s); ww = gaussian_filter(have, s)
        new = (have < 0.5) & (ww > 1e-3)
        out[new] = fill[new]; have[new] = 1.0
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(D, name), quality=92)
    print("smoothed", name, n, "islands")

for name in ("stand_light.jpg", "site_light.jpg", "finish_light.jpg"):
    smooth(name, 0.12)
