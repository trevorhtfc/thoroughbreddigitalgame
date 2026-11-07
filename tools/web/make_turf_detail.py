"""The fine grain laid live over the race view's ground (owner, 7 Nov 2026: the turf should have texture and
feel 3D, as the finish study's turf; the bake's 19 cm pixels are too coarse for it).

    python3 tools/web/make_turf_detail.py

Writes race-view/assets/course/turf_detail.png: a tileable grey image, 512 px for a 2 m square, mean 0.5,
which the page multiplies into the ground (1 + k (v - 0.5)). Two layers, as the study's turf material: tufts
(clumps about 0.25-0.6 m across) and blades (streaks a few centimetres long, a little longer along x, the
running direction down the home straight). Made from filtered random noise, so it tiles without seams; the
mipmaps average it away to a flat 0.5 in the distance, so it never shimmers far off.
"""
import os
import numpy as np
from PIL import Image

N, TILE = 512, 2.0
rng = np.random.default_rng(7)
f = np.fft.fftfreq(N, d=TILE / N)                      # cycles per metre
fx, fy = np.meshgrid(f, f)


def band(lo, hi, stretch=1.0):
    """Noise with features between 1/hi and 1/lo metres (stretch > 1: longer along x)."""
    r = np.hypot(fx * stretch, fy)
    w = np.exp(-((np.log(np.maximum(r, 1e-6)) - np.log(np.sqrt(lo * hi))) ** 2) / (2 * (np.log(hi / lo) / 2.5) ** 2))
    w[0, 0] = 0
    n = np.fft.ifft2(np.fft.fft2(rng.standard_normal((N, N))) * w).real
    return n / n.std()


tufts = band(1.6, 4.0)
blades = band(12.0, 40.0, stretch=2.2)
fine = band(40.0, 110.0, stretch=1.6)
v = 0.5 * np.tanh(0.55 * tufts) + 0.38 * np.tanh(0.7 * blades) + 0.22 * np.tanh(0.7 * fine)
v = v / (np.abs(v).max() + 1e-9) * 0.5 + 0.5
v += 0.5 - v.mean()
out = os.path.join(os.path.dirname(__file__), "..", "..", "race-view/assets/course/turf_detail.png")
Image.fromarray(np.clip(v * 255 + 0.5, 0, 255).astype(np.uint8), "L").save(out, optimize=True)
print("wrote", os.path.abspath(out), "mean %.3f sd %.3f" % (v.mean(), v.std()))
