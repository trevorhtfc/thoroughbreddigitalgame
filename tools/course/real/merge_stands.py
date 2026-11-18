"""A tier 2 course's stands, picked from the grandstand kit (the crib sheet: claude/grandstand-crib-sheet.md) into one model.

Every piece in the kit's GLBs (assets/models/architecture/park_stands, york_stands, rowley_stands, july_stands) is one mesh
node at the scene's root, so the chosen ones are copied straight across (meshes, accessors, buffer views, materials) into
assets/models/architecture/<id>_stands.glb, with their info (width, depth, crowd areas...) in <id>_stands.json. Then the
race view's copy: tools/web/glb_to_web.py --meshopt.

The picks come from tools/course/real/<id>.json "stands" (the piece names; a piece used twice is copied once).

  python3 tools/course/real/merge_stands.py <id>
"""
import json, struct, sys, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
ARCH = REPO / "assets/models/architecture"
KIT = ["park_stands", "york_stands", "rowley_stands", "july_stands"]


def read_glb(path):
    d = path.read_bytes()
    jl = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    b0 = 20 + jl
    return j, d[b0 + 8:b0 + 8 + struct.unpack("<I", d[b0:b0 + 4])[0]]


def main(cid):
    C = json.loads((REPO / f"tools/course/real/{cid}.json").read_text())
    want = []
    for s in C["stands"]["pieces"]:
        if s[0] not in want: want.append(s[0])
    out = {"asset": {"version": "2.0", "generator": "tools/course/real/merge_stands.py"}, "scene": 0, "scenes": [{"nodes": []}],
           "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}]}
    blob = bytearray(); info = {"_about": f"{C['name']}'s stands, picked from the grandstand kit by tools/course/real/merge_stands.py "
                                          "(each piece's info as in its source file: building axes x along the front, y into the "
                                          "building, z up, origin the middle of the front on the ground).",
                                "colours": {}, "pieces": {}, "from": {}}
    found = set()
    for src in KIT:
        j, buf = read_glb(ARCH / f"{src}.glb")
        meta = json.loads((ARCH / f"{src}.json").read_text())
        for ni in j["scenes"][0]["nodes"]:
            node = j["nodes"][ni]; name = node.get("name")
            if name not in want or name in found: continue
            found.add(name)
            mesh = json.loads(json.dumps(j["meshes"][node["mesh"]]))
            mat_map, acc_map = {}, {}
            def acc(ai):
                if ai in acc_map: return acc_map[ai]
                a = dict(j["accessors"][ai]); bv = dict(j["bufferViews"][a["bufferView"]])
                while len(blob) % 4: blob.append(0)
                o = bv.get("byteOffset", 0)
                data = buf[o:o + bv["byteLength"]]
                bv["byteOffset"] = len(blob); bv["buffer"] = 0; blob.extend(data)
                out["bufferViews"].append(bv); a["bufferView"] = len(out["bufferViews"]) - 1
                out["accessors"].append(a); acc_map[ai] = len(out["accessors"]) - 1
                return acc_map[ai]
            for p in mesh["primitives"]:
                p["attributes"] = {k: acc(v) for k, v in p["attributes"].items()}
                if "indices" in p: p["indices"] = acc(p["indices"])
                if "material" in p:
                    m = p["material"]
                    if m not in mat_map:
                        out["materials"].append(j["materials"][m]); mat_map[m] = len(out["materials"]) - 1
                    p["material"] = mat_map[m]
            out["meshes"].append(mesh)
            nn = {k: v for k, v in node.items() if k != "mesh"}; nn["mesh"] = len(out["meshes"]) - 1
            out["nodes"].append(nn); out["scenes"][0]["nodes"].append(len(out["nodes"]) - 1)
            info["pieces"][name] = meta["pieces"][name]; info["from"][name] = src
            for k, v in meta.get("colours", {}).items(): info["colours"].setdefault(k, v)
    missing = [w for w in want if w not in found]
    if missing: raise SystemExit(f"not in the kit: {missing}")
    while len(blob) % 4: blob.append(0)
    out["buffers"][0]["byteLength"] = len(blob)
    js = json.dumps(out, separators=(",", ":")).encode()
    while len(js) % 4: js += b" "
    glb = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(js) + 8 + len(blob)) + struct.pack("<I4s", len(js), b"JSON") + js + \
          struct.pack("<I4s", len(blob), b"BIN\x00") + bytes(blob)
    (ARCH / f"{cid}_stands.glb").write_bytes(glb)
    (ARCH / f"{cid}_stands.json").write_text(json.dumps(info, indent=1))
    print(f"wrote {cid}_stands.glb ({len(glb) / 1e6:.1f} MB): {', '.join(found)}")
    subprocess.run([sys.executable, str(REPO / "tools/web/glb_to_web.py"), str(ARCH / f"{cid}_stands.glb"),
                    str(REPO / "race-view/assets/architecture"), f"{cid}_stands", "--meshopt"], check=True)


if __name__ == "__main__":
    main(sys.argv[1])
