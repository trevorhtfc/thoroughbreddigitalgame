"""Lay the mist into a V2 style frame (tools/blender/v2_frame.py): the picture, and how far each point is from the
camera, give the same distance haze a game draws: nothing is painted by hand.

    python3 tools/blender/v2_post.py <base path without _raw.png> [start m] [depth m] [strength] [haze colour]
"""
import sys
import numpy as np
import cv2

base = sys.argv[1]
start, depth, k = (float(sys.argv[i]) if len(sys.argv) > i else v for i, v in ((2, 40.0), (3, 260.0), (4, 0.9)))
haze = sys.argv[5] if len(sys.argv) > 5 else "#e6e6c4"
img = cv2.imread(base + "_raw.png", cv2.IMREAD_UNCHANGED).astype(np.float32)[..., :3] / 255.0
dist = cv2.imread(base + "_dist.png", cv2.IMREAD_UNCHANGED).astype(np.float32)
dist = dist[..., 0] / (65535.0 if dist.max() > 255 else 255.0) * 800.0
sky = dist > 799.0
hc = np.array([int(haze[i:i + 2], 16) / 255.0 for i in (5, 3, 1)], np.float32)        # BGR
h = k * (1.0 - np.exp(-np.maximum(dist - start, 0.0) / depth))
h[sky] = 0.0
# the sky: the mist's own colour where it meets the land, clearing to a pale teal overhead
rows = np.where(sky.any(axis=1))[0]
if len(rows):
    top = np.array([int(c[i:i + 2], 16) / 255.0 for c in [sys.argv[6] if len(sys.argv) > 6 else "#b9d6cb"] for i in (5, 3, 1)], np.float32)
    t = np.clip((np.arange(img.shape[0]) - rows.min()) / max(1.0, rows.max() - rows.min()), 0, 1) ** 0.8
    grad = top[None, :] * (1 - t[:, None]) + hc[None, :] * t[:, None]
    img[sky] = np.repeat(grad[:, None, :], img.shape[1], axis=1)[sky]
# the mist is drawn a pixel soft, so thin things far off (railings, flag poles) don't sparkle against it
h = cv2.GaussianBlur(h, (0, 0), 0.6)
out = img * (1.0 - h[..., None]) + hc * h[..., None]
cv2.imwrite(base + ".png", np.clip(out * 255.0 + 0.5, 0, 255).astype(np.uint8))
print("wrote", base + ".png")
