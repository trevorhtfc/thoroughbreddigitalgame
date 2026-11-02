"""Split a .glb into files the claude.ai artifact host will serve.

    python glb_to_web.py <in.glb> <out_dir>

Writes racehorse.json (glTF JSON), racehorse-geometry.txt (the binary
buffer as base64) and each embedded image as a .jpg/.png. The race view
reassembles these into a .glb in memory. Any other engine should use the
original .glb directly.
"""
import sys, json, struct, base64, os, re

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
d = open(src, "rb").read()
jl = struct.unpack("<I", d[12:16])[0]
j = json.loads(d[20:20 + jl])
b0 = 20 + jl
buf = d[b0 + 8:b0 + 8 + struct.unpack("<I", d[b0:b0 + 4])[0]]

img_views = set()
for i, im in enumerate(j.get("images", [])):
    bv = j["bufferViews"][im["bufferView"]]
    o = bv.get("byteOffset", 0)
    ext = "png" if im.get("mimeType") == "image/png" else "jpg"
    name = re.sub(r"[^a-z0-9]+", "-", (im.get("name") or "image-%d" % i).lower()).strip("-") + "." + ext
    open(os.path.join(out, name), "wb").write(buf[o:o + bv["byteLength"]])
    img_views.add(im.pop("bufferView"))
    im.pop("mimeType", None)
    im["uri"] = name

new, remap, views = bytearray(), {}, []
for i, bv in enumerate(j["bufferViews"]):
    if i in img_views:
        continue
    while len(new) % 4:
        new.append(0)
    o = bv.get("byteOffset", 0)
    nb = dict(bv, byteOffset=len(new))
    new += buf[o:o + bv["byteLength"]]
    remap[i] = len(views)
    views.append(nb)
j["bufferViews"] = views
for a in j.get("accessors", []):
    if "bufferView" in a:
        a["bufferView"] = remap[a["bufferView"]]
    if "sparse" in a:
        for k in ("indices", "values"):
            a["sparse"][k]["bufferView"] = remap[a["sparse"][k]["bufferView"]]
j["buffers"] = [{"byteLength": len(new)}]
json.dump(j, open(os.path.join(out, "racehorse.json"), "w"), separators=(",", ":"))
open(os.path.join(out, "racehorse-geometry.txt"), "w").write(base64.b64encode(bytes(new)).decode())
print("images:", [im["uri"] for im in j.get("images", [])])
