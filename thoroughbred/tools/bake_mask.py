# Bakes a recolour mask for the racehorse GLB.
# R = silk colour A (orange hoops), G = silk colour B (blue/red hoops + cap), B = horse body (coat + points), A = unused (255)
import json, struct, sys, numpy as np
from PIL import Image, ImageFilter
import matplotlib.colors as mc
glb, out, dbg = sys.argv[1], sys.argv[2], sys.argv[3]
RES = 2048
f = open(glb, 'rb').read()
clen = struct.unpack('<I', f[12:16])[0]; j = json.loads(f[20:20+clen]); bo = 20+clen+8
def acc(i):
    a = j['accessors'][i]; bv = j['bufferViews'][a['bufferView']]
    n = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    dt = {5126:np.float32,5123:np.uint16,5121:np.uint8,5125:np.uint32}[a['componentType']]
    return np.frombuffer(f, dtype=dt, count=a['count']*n, offset=bo+bv.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'], n)
p = j['meshes'][0]['primitives'][0]
pos = acc(p['attributes']['POSITION']).astype(np.float64)
uv = acc(p['attributes']['TEXCOORD_0']).astype(np.float64) * RES
tri = acc(p['indices']).reshape(-1, 3)
img = j['images'][j['textures'][j['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']]
bv = j['bufferViews'][img['bufferView']]
import io
base = Image.open(io.BytesIO(f[bo+bv.get('byteOffset',0): bo+bv.get('byteOffset',0)+bv['byteLength']])).convert('RGB').resize((RES, RES))
col = np.asarray(base).astype(np.float64) / 255

P = np.full((RES, RES, 3), np.nan)
for t in tri:
    a, b, c = uv[t]
    x0, x1 = int(max(0, np.floor(min(a[0], b[0], c[0])))), int(min(RES-1, np.ceil(max(a[0], b[0], c[0]))))
    y0, y1 = int(max(0, np.floor(min(a[1], b[1], c[1])))), int(min(RES-1, np.ceil(max(a[1], b[1], c[1]))))
    xs, ys = np.meshgrid(np.arange(x0, x1+1) + .5, np.arange(y0, y1+1) + .5)
    d = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
    if abs(d) < 1e-12: continue
    l1 = ((b[1]-c[1])*(xs-c[0]) + (c[0]-b[0])*(ys-c[1])) / d
    l2 = ((c[1]-a[1])*(xs-c[0]) + (a[0]-c[0])*(ys-c[1])) / d
    l3 = 1 - l1 - l2
    e = -0.6 / max(1, np.sqrt(abs(d)))  # small tolerance so seams are covered
    m = (l1 >= e) & (l2 >= e) & (l3 >= e)
    if not m.any(): continue
    q = l1[m, None]*pos[t[0]] + l2[m, None]*pos[t[1]] + l3[m, None]*pos[t[2]]
    P[ys[m].astype(int), xs[m].astype(int)] = q

X, Y, Z = P[..., 0], P[..., 1], P[..., 2]
valid = ~np.isnan(X)
hsv = mc.rgb_to_hsv(col); H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
with np.errstate(invalid='ignore'):
    upper = valid & (Y > 0.425) & (X > -0.01) & (X < 0.285)          # jockey torso / arms / head
    legs = valid & (Y > 0.15) & (Y <= 0.425) & (X > 0.0) & (X < 0.23) & (np.abs(Z) > 0.075)  # jockey legs, boots
    jockey = upper | legs
    orange = (H > 0.025) & (H < 0.13) & (S > 0.45) & (V > 0.5)
    blue = (H > 0.5) & (H < 0.75) & (S > 0.3) & (V > 0.15)
    red = ((H > 0.92) | (H <= 0.025)) & (S > 0.5) & (V > 0.35)
    silkA = upper & orange
    silkB = upper & (blue | red)
    horse = valid & ~jockey
    tack = (((S < 0.2) & (V > 0.55))                      # white saddle cloth
            | ((H > 0.5) & (H < 0.75) & (S > 0.3))        # blue girth
            | ((S > 0.6) & (V > 0.62)))                    # bright orange reins
    body = horse & ~tack                                   # whole coat: body, mane, tail, legs, hooves
    coat = body & (H < 0.12) & (S > 0.25) & (V > 0.16)     # brown hair (reference brightness only)
    points = body & (V < 0.2) & ~coat                      # dark hair (reference brightness only)
mask = np.zeros((RES, RES, 4), np.uint8)
mask[..., 0] = silkA * 255; mask[..., 1] = silkB * 255; mask[..., 2] = body * 255; mask[..., 3] = 255
# reference luminance (linear) per class, so the shader can keep the folds and shading
lin = np.where(col <= 0.04045, col/12.92, ((col+0.055)/1.055)**2.4)
L = lin @ np.array([0.2126, 0.7152, 0.0722])
for n, m in [('silkA', silkA), ('silkB', silkB), ('coat', coat), ('points', points)]:
    print(n, int(m.sum()), 'ref_lum %.4f' % np.median(L[m]))
im = Image.fromarray(mask, 'RGBA')
# soften edges slightly so recolour boundaries don't alias
im = Image.merge('RGBA', [ch.filter(ImageFilter.GaussianBlur(0.7)) for ch in im.split()])
im.save(out)
d = np.zeros((RES, RES, 3)); d[valid] = 0.25
d[silkA] = [1, 0, 1]; d[silkB] = [0, 1, 1]; d[body] = [0.2, 0.8, 0.2]; d[points] = [1, 1, 0]; d[jockey & ~(silkA | silkB)] = [1, 1, 1]
Image.fromarray((d*255).astype(np.uint8)).resize((1024, 1024)).save(dbg)
