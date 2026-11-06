"""Grades the owner's Newmarket map clip (the board tilting up into a landscape) to the colours of the live board,
so the clip and the board cross-fade without a jump in colour. The clip's first frame is the board itself (found by
feature matching: the board is scaled by 0.706 and moved by (129.5, -23.6)), so its colours are matched to the board's
there, channel by channel in Lab, and the same curves are applied to every frame.

python3 grade_map_clip.py <frames dir> <board image> <out dir>"""
import sys, os, glob
import numpy as np, cv2

frames, board_p, out = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
paths = sorted(glob.glob(os.path.join(frames, "*.png")))
f0 = cv2.imread(paths[0])
board = cv2.imread(board_p)
H = np.array([[0.7058, 0.0004, 129.5051], [0.0, 0.7064, -23.6050], [0, 0, 1]])
warped = cv2.warpPerspective(board, H, (f0.shape[1], f0.shape[0]))
mask = cv2.warpPerspective(np.full(board.shape[:2], 255, np.uint8), H, (f0.shape[1], f0.shape[0]))
mask = cv2.erode(mask, np.ones((15, 15), np.uint8)) > 0

def lut_for(src, ref):
    """Histogram matching of one channel (uint8 arrays) -> a 256-entry look-up table."""
    s_hist = np.bincount(src, minlength=256).astype(np.float64); r_hist = np.bincount(ref, minlength=256).astype(np.float64)
    s_cdf = np.cumsum(s_hist) / s_hist.sum(); r_cdf = np.cumsum(r_hist) / r_hist.sum()
    lut = np.interp(s_cdf, r_cdf, np.arange(256))
    # keep it smooth: a light blur of the curve
    k = np.ones(9) / 9; lut = np.convolve(np.pad(lut, 4, mode="edge"), k, mode="valid")
    return np.clip(lut, 0, 255).astype(np.uint8)

a = cv2.cvtColor(f0, cv2.COLOR_BGR2LAB); b = cv2.cvtColor(warped, cv2.COLOR_BGR2LAB)
luts = [lut_for(a[..., c][mask], b[..., c][mask]) for c in range(3)]
np.save(os.path.join(out, "luts.npy"), np.array(luts))
for i, p in enumerate(paths):
    f = cv2.imread(p); lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB)
    for c in range(3): lab[..., c] = luts[c][lab[..., c]]
    g = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    cv2.imwrite(os.path.join(out, os.path.basename(p)), g)
# a side-by-side check of the first frame: graded clip | live board
chk = np.concatenate([cv2.imread(os.path.join(out, os.path.basename(paths[0]))), warped], axis=1)
cv2.imwrite(os.path.join(out, "_check.jpg"), cv2.resize(chk, None, fx=0.5, fy=0.5))
print("graded", len(paths))
