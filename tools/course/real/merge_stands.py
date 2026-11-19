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
KIT = ["park_stands", "york_stands", "rowley_stands", "july_stands", "stand_modules", "site_props", "newbury_kit", "chester_stands_kit", "sandown_stands_kit", "generic_stands_kit"]


def read_glb(path):
    d = path.read_bytes()
    jl = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    b0 = 20 + jl
    return j, d[b0 + 8:b0 + 8 + struct.unpack("<I", d[b0:b0 + 4])[0]]


def main(cid):
    C = json.loads((REPO / f"tools/course/real/{cid}.json").read_text())
    want = []
    comps = C["stands"].get("composites", {})
    for s in C["stands"]["pieces"]:
        nm = s["piece"] if isinstance(s, dict) else s[0]
        if nm in comps: continue
        if nm not in want: want.append(nm)
    for nm in C["stands"].get("extra", []):          # pieces placed by the course's own edges script (Chester's walls)
        if nm not in want: want.append(nm)
    out = {"asset": {"version": "2.0", "generator": "tools/course/real/merge_stands.py"}, "scene": 0, "scenes": [{"nodes": []}],
           "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": [{"byteLength": 0}]}
    blob = bytearray(); info = {"_about": f"{C['name']}'s stands, picked from the grandstand kit by tools/course/real/merge_stands.py "
                                          "(each piece's info as in its source file: building axes x along the front, y into the "
                                          "building, z up, origin the middle of the front on the ground).",
                                "colours": {}, "pieces": {}, "from": {}}
    found = set()
    for src in KIT:
        j, buf = read_glb(ARCH / f"{src}.glb")
        mp = ARCH / f"{src}.json"
        meta = json.loads(mp.read_text()) if mp.exists() else {"pieces": {}}      # (site_props: no info file; used in composites only)
        for ni in j["scenes"][0]["nodes"]:
            node = j["nodes"][ni]; name = node.get("name")
            if name not in want or name in found: continue     # (composites are built after)
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
    # composites (owner, 19:10: "add a clock tower to one of the balcony stands"): a base piece with parts of others
    # added to the same mesh: {"name": {"base": piece, "add": [{"piece", "above": keep only triangles wholly above this
    # height (m), "scale", "at": [x, y, z] glTF axes: x along the front, y up, z out of the front (into the building -z)]}]}}
    import numpy as np
    srcs = {src: read_glb(ARCH / f"{src}.glb") for src in KIT}
    def mesh_of(piece):
        for src, (j, buf) in srcs.items():
            for n in j["nodes"]:
                if n.get("name") == piece: return src, j, buf, j["meshes"][n["mesh"]]
        raise SystemExit(f"not in the kit: {piece}")
    def clip_x(P, N, I, a, b):
        """The triangles cut to the stretch a <= x <= b: those across a cut are sliced (their corners and normals
        interpolated) and fanned, so long walls and roofs are kept up to the cut (a kinked stand from part of a stand)."""
        P2, N2, I2 = [p_ for p_ in P], [n_ for n_ in N], []
        def cut(poly, keep_side, x0):
            out = []
            for k in range(len(poly)):
                cur, nxt = poly[k], poly[(k + 1) % len(poly)]
                ci, ni = keep_side(cur[0][0]), keep_side(nxt[0][0])
                if ci: out.append(cur)
                if ci != ni:
                    t = (x0 - cur[0][0]) / (nxt[0][0] - cur[0][0])
                    out.append((cur[0] + t * (nxt[0] - cur[0]), cur[1] + t * (nxt[1] - cur[1])))
            return out
        for tri in I:
            xs = P[tri][:, 0]
            if xs.min() >= a - 1e-4 and xs.max() <= b + 1e-4: I2.append(list(tri)); continue
            if xs.max() < a or xs.min() > b: continue
            poly = [(P[k].astype(np.float64), N[k].astype(np.float64)) for k in tri]
            poly = cut(poly, lambda x: x >= a, a)
            if len(poly) >= 3: poly = cut(poly, lambda x: x <= b, b)
            if len(poly) < 3: continue
            ids = []
            for pp, nn in poly:
                P2.append(pp.astype(np.float32)); l = np.linalg.norm(nn) or 1.0; N2.append((nn / l).astype(np.float32)); ids.append(len(P2) - 1)
            for k in range(1, len(ids) - 1): I2.append([ids[0], ids[k], ids[k + 1]])
        return np.array(P2, np.float32), np.array(N2, np.float32), np.array(I2, np.uint32).reshape(-1, 3)
    def arr(j, buf, ai, dt, w):
        a = j["accessors"][ai]; bv = j["bufferViews"][a["bufferView"]]
        o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        n = a["count"] * w
        return np.frombuffer(buf[o:o + n * np.dtype(dt).itemsize], dtype=dt).reshape(-1, w) if w > 1 else np.frombuffer(buf[o:o + n * np.dtype(dt).itemsize], dtype=dt)
    def put(data, comp, typ, target):
        while len(blob) % 4: blob.append(0)
        b = np.ascontiguousarray(data).tobytes(); off = len(blob); blob.extend(b)
        out["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": len(b), "target": target})
        acc = {"bufferView": len(out["bufferViews"]) - 1, "componentType": comp, "count": int(len(data)), "type": typ}
        if typ == "VEC3": acc["min"] = data.min(0).tolist(); acc["max"] = data.max(0).tolist()
        out["accessors"].append(acc); return len(out["accessors"]) - 1
    for cname, spec in C["stands"].get("composites", {}).items():
        prims = []
        # "baseAt" moves the base (Ascot's stand modules have their origin at their left end, not the middle of the front)
        # "baseXRange" keeps only the base's triangles within that stretch of its length (before the move), "mirror"
        # flips it end for end (owner, 22:51, Newbury: a kinked stand from two lengths of one stand; end caps both ends)
        parts = [{"piece": spec["base"], "above": -1e9, "scale": 1.0, "at": spec.get("baseAt", [0, 0, 0]),
                  "xRange": spec.get("baseXRange"), "mirror": spec.get("mirror", False)}] + spec.get("add", [])
        for part in parts:
            src, j, buf, mesh = mesh_of(part["piece"])
            for p in mesh["primitives"]:
                P = arr(j, buf, p["attributes"]["POSITION"], "<f4", 3).astype(np.float32)
                N = arr(j, buf, p["attributes"]["NORMAL"], "<f4", 3).astype(np.float32)
                ia = j["accessors"][p["indices"]]
                I = arr(j, buf, p["indices"], {5123: "<u2", 5125: "<u4"}[ia["componentType"]], 1).astype(np.uint32).reshape(-1, 3)
                keep = (P[I][:, :, 1].min(1) >= part["above"])
                I = I[keep]
                if part.get("xRange"):
                    P, N, I = clip_x(P, N, I, *part["xRange"])
                if part.get("mirror"):
                    P = P.copy(); N = N.copy(); P[:, 0] *= -1; N[:, 0] *= -1; I = I[:, ::-1].copy()
                if not len(I): continue
                used = np.unique(I); remap = -np.ones(len(P), np.int64); remap[used] = np.arange(len(used))
                P2 = P[used] * part["scale"] + np.array(part["at"], np.float32); N2 = N[used]
                I2 = remap[I].astype(np.uint32).ravel()
                m = j["materials"][p["material"]]
                out["materials"].append(m)
                prims.append({"attributes": {"POSITION": put(P2.astype(np.float32), 5126, "VEC3", 34962),
                                             "NORMAL": put(N2.astype(np.float32), 5126, "VEC3", 34962)},
                              "indices": put(I2, 5125, "SCALAR", 34963), "material": len(out["materials"]) - 1})
        out["meshes"].append({"name": cname, "primitives": prims})
        out["nodes"].append({"name": cname, "mesh": len(out["meshes"]) - 1}); out["scenes"][0]["nodes"].append(len(out["nodes"]) - 1)
        bsrc = mesh_of(spec['base'])[0]
        if "info" in spec: base = spec["info"]
        else:
            base = json.loads((ARCH / f"{bsrc}.json").read_text())["pieces"][spec["base"]]
            if spec.get("baseXRange") or spec.get("mirror") or spec.get("baseAt"):
                # the crowd areas follow the cut, the flip and the move; the width is the stretch kept
                a_, b_ = spec.get("baseXRange") or [-base["width"] / 2, base["width"] / 2]
                dx = spec.get("baseAt", [0, 0, 0])[0]; mir = spec.get("mirror", False)
                crowd = []
                for x0, x1, y0, y1, fz in base.get("crowd", []):
                    x0, x1 = max(x0, a_), min(x1, b_)
                    if x1 - x0 < 0.5: continue
                    if mir: x0, x1 = -x1, -x0
                    crowd.append([round(x0 + dx, 2), round(x1 + dx, 2), y0, y1, fz])
                base = dict(base, width=round(b_ - a_, 2), crowd=crowd)
        top = max(float(np.max(out["accessors"][q["attributes"]["POSITION"]]["max"][1])) for q in prims)
        info["pieces"][cname] = dict(base, height=round(top, 2), composite=spec)
        info["from"][cname] = "composite"
        found.add(cname)
    want = [w for w in want if w not in C["stands"].get("composites", {})] + list(C["stands"].get("composites", {}))
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
