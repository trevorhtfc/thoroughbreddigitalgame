"""Package the v2 racehorse for the web race view.

    python tools/web/package_racehorse_v2.py <racehorse_v2_web.glb>

The web copy is exported without images (tools/blender/build_racehorse_v2.py writes it beside the full
model): the race view reuses v1's horse textures from race-view/assets/model/ and the v2 silks from
race-view/assets/silks-3d-v2/, so the new horse adds no texture download. gltfpack squeezes the geometry
and the clips (meshopt; positions to 16 bits, UVs kept as exact floats because the textures are set by the viewer, every clip kept at 100 frames a second so the
strides stay exact), then glb_to_web.py splits it into the files the artifact host serves:
race-view/assets/model-v2/racehorse_v2.json and racehorse_v2-geometry.txt.
"""
import os, sys, subprocess, shutil, tempfile

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = sys.argv[1]
packed = os.path.join(tempfile.mkdtemp(), "racehorse_v2_packed.glb")
tool = [shutil.which("gltfpack")] if shutil.which("gltfpack") else ["npx", "--yes", "gltfpack"]
subprocess.run(tool + ["-i", src, "-o", packed, "-c", "-kn", "-km", "-kv", "-af", "100", "-vp", "16", "-vtf", "-vn", "10"], check=True)
print("packed: %.2f MB -> %.2f MB" % (os.path.getsize(src) / 1e6, os.path.getsize(packed) / 1e6))
out = os.path.join(root, "race-view/assets/model-v2")
subprocess.run([sys.executable, os.path.join(root, "tools/web/glb_to_web.py"), packed, out, "racehorse_v2"], check=True)
shutil.copy(os.path.join(root, "assets/models/racehorse_v2_rig.json"), out)
for f in sorted(os.listdir(out)):
    print("  %-28s %7.0f KB" % (f, os.path.getsize(os.path.join(out, f)) / 1024))
