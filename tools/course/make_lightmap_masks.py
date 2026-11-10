"""Draw where the light maps' islands are, for tools/course/smooth_lightmaps.py (white = island, black = gutter).

    python3 tools/course/make_lightmap_masks.py

After a re-bake (tools/blender/bake_static_world.py) the light-map layout is new, so the masks must be drawn again from
the baked geometry: every triangle of each mesh drawn at its light-map coordinates, at the map's own size.
  stand  -> stand_mask.png  (the "stand" mesh)        finish -> finish_mask.png (the "finish" mesh)
  site   -> site_mask.png   (every kit_* mesh: the site pieces share one map)
Reads assets/models/baked/static_world.glb and bake.json; writes race-view/assets/baked/raw/<name>_mask.png.
(Replaces the checking rig's uvmask script, which was never in the repo.)
"""
import os, json, struct
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_erosion, label

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(REPO, "assets", "models", "baked")
RAW = os.path.join(REPO, "race-view", "assets", "baked", "raw")
os.makedirs(RAW, exist_ok=True)
B = json.load(open(os.path.join(SRC, "bake.json")))

# ---- read the .glb (JSON chunk + binary chunk) without any 3D library
raw = open(os.path.join(SRC, B["glb"]), "rb").read()
jlen = struct.unpack_from("<I", raw, 12)[0]
G = json.loads(raw[20:20 + jlen])
bin0 = 20 + jlen + 8
BIN = raw[bin0:bin0 + struct.unpack_from("<I", raw, 20 + jlen)[0]]
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def accessor(i):
    a = G["accessors"][i]; bv = G["bufferViews"][a["bufferView"]]
    n, dt = NC[a["type"]], np.dtype(CT[a["componentType"]])
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    stride = bv.get("byteStride", 0) or n * dt.itemsize
    if stride == n * dt.itemsize:
        arr = np.frombuffer(BIN, dt, a["count"] * n, off).reshape(a["count"], n)
    else:
        rows = [np.frombuffer(BIN, dt, n, off + k * stride) for k in range(a["count"])]
        arr = np.stack(rows)
    if a.get("normalized") and dt != np.float32:
        arr = arr.astype(np.float32) / np.iinfo(dt).max
    return arr


def mesh_tris(name_ok):
    """Every light-map triangle (in 0..1 coordinates) of the meshes whose node name passes name_ok."""
    out = []
    for node in G["nodes"]:
        if "mesh" not in node or not name_ok(node.get("name", "")): continue
        for prim in G["meshes"][node["mesh"]]["primitives"]:
            at = prim["attributes"]
            uvk = "TEXCOORD_0" if "TEXCOORD_0" in at else None
            if not uvk: continue
            uv = accessor(at[uvk]).astype(np.float64)
            idx = accessor(prim["indices"]).reshape(-1) if "indices" in prim else np.arange(len(uv))
            out.append(uv[idx.reshape(-1, 3)])
    return np.concatenate(out) if out else np.zeros((0, 3, 2))


def draw(tris, size, path, light):
    im = Image.new("L", (size, size), 0); d = ImageDraw.Draw(im)
    for t in tris:
        d.polygon([(u * size, v * size) for u, v in t], fill=255)       # glTF UVs: v down from the image top
    # Drawn polygons take in every pixel their edges touch, a pixel wider than the bake filled (its gutters are black):
    # shrink by a pixel, so the smoother (which grows the mask by one again) fills those edges from the island.
    full = np.asarray(im) > 127
    m = binary_erosion(full, iterations=1)
    lab, n = label(full)                                  # islands too thin to survive the shrink are kept as drawn
    left = np.bincount(lab[m], minlength=n + 1)
    lit = np.asarray(Image.open(os.path.join(SRC, light)).convert("RGB")).max(-1) > 2    # (their black edge pixels left out)
    m |= full & (left[lab] == 0) & lit
    im = Image.fromarray((m * 255).astype(np.uint8))
    im.save(path)
    print("wrote", path, len(tris), "triangles", flush=True)


def size_of(img):
    return Image.open(os.path.join(SRC, img)).size[0]


for key, ok in (("stand", lambda n: n == B["stand"]["mesh"]), ("finish", lambda n: n == B["finish"]["mesh"]), ("site", lambda n: n.startswith("kit_"))):
    draw(mesh_tris(ok), size_of(B[key]["lightMap"]), os.path.join(RAW, key + "_mask.png"), B[key]["lightMap"])
