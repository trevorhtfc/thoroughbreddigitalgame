# Steadies newmarket-arrive.mp4 (owner, 7 Nov: the opening film wobbled). The clip had an uneven 3:2-style cadence:
# every few frames the zoom jumped further. Run on the ORIGINAL clip (git show da44fa2:game/video/newmarket-arrive.mp4),
# then interpolate to 48 fps:
#   python3 steady_film.py original.mp4 steady.mp4 4
#   ffmpeg -i steady.mp4 -vf "minterpolate=fps=48:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart newmarket-arrive.mp4
# The last frame (the board) is left untouched, so the film still lands exactly on the live board.
# Steady the arrival film: measure the camera move frame to frame (a homography fitted to the map), smooth that path,
# and re-warp each frame onto the smooth path. The last frame (the board itself) is left exactly where it was.
import cv2, numpy as np, sys, subprocess
src, out = sys.argv[1], sys.argv[2]
cap = cv2.VideoCapture(src); F = []
while True:
    ok, f = cap.read()
    if not ok: break
    F.append(f)
N = len(F); G = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in F]
sift = cv2.SIFT_create(4000); fl = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=60))
kd = [sift.detectAndCompute(g, None) for g in G]
def hom(i, j):   # maps frame i -> frame j
    (k1, d1), (k2, d2) = kd[i], kd[j]
    m = [a for a, b in fl.knnMatch(d1, d2, k=2) if a.distance < 0.7 * b.distance]
    A = np.float32([k1[x.queryIdx].pt for x in m]); B = np.float32([k2[x.trainIdx].pt for x in m])
    h, _ = cv2.findHomography(A, B, cv2.RANSAC, 1.5)
    return h
# T[i]: frame i -> last frame
T = [None] * N; T[N - 1] = np.eye(3)
for i in range(N - 2, -1, -1):
    T[i] = T[i + 1] @ hom(i, i + 1); T[i] /= T[i][2, 2]
ref = np.float32([[420, 200], [860, 200], [860, 520], [420, 520]]).reshape(-1, 1, 2)
P = np.array([cv2.perspectiveTransform(ref, np.linalg.inv(T[i])).reshape(-1) for i in range(N)])   # N x 8
from scipy.ndimage import gaussian_filter1d
sig = float(sys.argv[3]) if len(sys.argv) > 3 else 4
Q = gaussian_filter1d(P, sig, axis=0, mode='nearest')
w = np.clip((N - 1 - np.arange(N)) / 10, 0, 1)[:, None]
Q = P + (Q - P) * w
print('largest correction (px):', np.abs(Q - P).max())
h, wd = F[0].shape[:2]
pipe = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{wd}x{h}', '-r', '24', '-i', '-',
                         '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
for i in range(N):
    S = cv2.getPerspectiveTransform(ref.reshape(-1, 2), Q[i].reshape(4, 2).astype(np.float32))
    W = S @ T[i]
    pipe.stdin.write(cv2.warpPerspective(F[i], W, (wd, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).tobytes())
pipe.stdin.close(); pipe.wait()
