"""The game's shared 'storybook' grade, the same sums as the 3D race view's painted finish in game mode
(final-furlong.html, post shader, STORYBOOK): softer saturation, greens leaning to the board's olive, warm highlights,
gently cooled shadows, lifted blacks, a little paper grain and a soft vignette. Used on the Ascot clips so the cover,
the arrival at Ascot and the 3D race share one look with the painted Newmarket board.

python3 storybook_grade.py <frames dir> <out dir> [crop x0 x1]"""
import sys, os, glob
import numpy as np, cv2

def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)

def grade(rgb, paper=None):
    c = rgb.astype(np.float32) / 255.0
    l = (c @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]
    c = l + (c - l) * 0.80                                   # softer saturation (the race view: 0.93; the board is softer still)
    # greens lean towards the board's olive: where green leads, move a little of it into red
    g_lead = np.clip(c[..., 1:2] - np.maximum(c[..., 0:1], c[..., 2:3]), 0, 1)
    c[..., 0:1] += g_lead * 0.28; c[..., 2:3] -= g_lead * 0.10
    c *= np.array([1.035, 1.0, 0.92], np.float32)            # warm highlights
    c = c * (1 - smoothstep(0.05, 0.5, l)) * np.array([0.9, 0.97, 1.04], np.float32) + c * smoothstep(0.05, 0.5, l)
    c = c * 0.94 + np.array([0.04, 0.034, 0.018], np.float32) # lifted blacks, a parchment cast
    if paper is not None: c *= 0.985 + 0.03 * paper[..., None]
    h, w = c.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = np.sqrt(((xx / w - 0.5)) ** 2 + ((yy / h - 0.5) * 0.85) ** 2)
    c *= (1 - 0.16 * smoothstep(0.4, 0.85, v))[..., None]
    return (np.clip(c, 0, 1) * 255 + 0.5).astype(np.uint8)

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    x0, x1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (None, None)
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(5)
    paper = None
    for p in sorted(glob.glob(os.path.join(src, "*.png"))):
        f = cv2.imread(p)[..., ::-1]
        if x0 is not None: f = f[:, x0:x1]
        if paper is None: paper = cv2.GaussianBlur(rng.random(f.shape[:2]).astype(np.float32), (0, 0), 0.8)
        cv2.imwrite(os.path.join(out, os.path.basename(p)), grade(f, paper)[..., ::-1])
    print("graded", out)
