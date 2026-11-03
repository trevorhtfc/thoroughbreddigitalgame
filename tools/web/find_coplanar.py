"""Find faces that will flash (z-fight): two faces facing the same way, lying in (nearly) the same plane
and overlapping. Far off, the depth buffer can't tell them apart and they flicker between each other.

    python3 tools/web/find_coplanar.py <model.glb> [gap_m=0.025] [min_area_m2=0]

Checks each node of the .glb on its own (every material together), and also flags upward faces lying
within `gap` of the ground (y 0), which fight the baked ground. Prints, per node, each fighting pair with
where it is (node-local metres, glTF axes: y up) and the gap between the two faces.
"""
import json, struct, sys
from collections import defaultdict
import numpy as np
from shapely.geometry import Polygon

GAP = float(sys.argv[2]) if len(sys.argv) > 2 else 0.025
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def load(path):
    b = open(path, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    bin_ = b[20 + jl + 8:]
    def acc(i):
        a = js["accessors"][i]; v = js["bufferViews"][a["bufferView"]]
        n, dt = NC[a["type"]], CT[a["componentType"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        arr = np.frombuffer(bin_, dtype=dt, count=a["count"] * n, offset=off).reshape(-1, n) if not v.get("byteStride") else None
        if arr is None:
            st = v["byteStride"]; arr = np.array([np.frombuffer(bin_, dtype=dt, count=n, offset=off + k * st) for k in range(a["count"])])
        return arr
    out = {}
    for node in js["nodes"]:
        if "mesh" not in node:
            continue
        tris, mats = [], []
        for p in js["meshes"][node["mesh"]]["primitives"]:
            pos = acc(p["attributes"]["POSITION"]).astype(np.float64)
            idx = acc(p["indices"]).reshape(-1, 3) if "indices" in p else np.arange(len(pos)).reshape(-1, 3)
            tris.append(pos[idx])
            mats += [js["materials"][p["material"]]["name"] if "material" in p else "-"] * len(idx)
        out[node.get("name", "?")] = (np.concatenate(tris), np.array(mats))
    return out


def check(name, T, M):
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    n = np.cross(e1, e2)
    area = np.linalg.norm(n, axis=1)
    keep = area > 1e-7
    T, M, n, area = T[keep], M[keep], n[keep] / area[keep, None], area[keep] / 2
    # faces looking down from near the ground are never seen (cameras are above): skip them
    lowdown = (n[:, 1] < -0.9) & (T[:, :, 1].max(1) < 0.3)
    T, M, n, area = T[~lowdown], M[~lowdown], n[~lowdown], area[~lowdown]
    d = np.einsum("ij,ij->i", n, T[:, 0])
    # bucket by rounded normal and plane offset; compare neighbours in offset
    key = defaultdict(list)
    nq = np.round(n * 200).astype(int)
    dq = np.floor(d / GAP).astype(int)
    for i in range(len(T)):
        key[(tuple(nq[i]), dq[i])].append(i)
    hits = []
    seen = set()
    for (nk, dk), ids in key.items():
        cand = ids + key.get((nk, dk + 1), [])
        if len(cand) < 2:
            continue
        nn = np.array(nk) / 200.0; nn /= np.linalg.norm(nn)
        u = np.cross(nn, [0, 1, 0] if abs(nn[1]) < 0.9 else [1, 0, 0]); u /= np.linalg.norm(u)
        v = np.cross(nn, u)
        polys = {i: Polygon([(p @ u, p @ v) for p in T[i]]) for i in cand}
        for a in range(len(cand)):
            for b in range(a + 1, len(cand)):
                i, j = cand[a], cand[b]
                if (i, j) in seen:
                    continue
                seen.add((i, j))
                if abs(d[i] - d[j]) >= GAP:
                    continue
                pi, pj = polys[i], polys[j]
                if not pi.bounds or not pi.intersects(pj):
                    continue
                ov = pi.intersection(pj).area
                if ov > 2e-4:
                    hits.append((ov, abs(d[i] - d[j]), T[i].mean(0), T[j].mean(0), nn, tuple(sorted((M[i], M[j])))))
    # upward faces lying on the ground
    up = (n[:, 1] > 0.99) & (np.abs(T[:, :, 1]).max(1) < GAP) & (area > 2e-4)
    ground = [(area[i], T[i, :, 1].max(), T[i].mean(0)) for i in np.where(up)[0]]
    return hits, ground


if __name__ == "__main__":
    total = 0
    MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    for name, (T, M) in load(sys.argv[1]).items():
        hits, ground = check(name, T, M)
        if not hits and not ground:
            continue
        total += len(hits) + len(ground)
        print(f"{name}: {len(hits)} fighting face pairs, {len(ground)} faces on the ground")
        # group by location so one bad pair of boxes reads as one line
        rep = {}
        for ov, gap, ca, cb, nn, mm in hits:
            k = (tuple(float(v) for v in np.round(nn, 1)), round(float(ca[1]), 2) if abs(nn[1]) > 0.9 else round(float(ca @ nn), 2), mm)
            r = rep.setdefault(k, [0, 0, gap, ca])
            r[0] += 1; r[1] += ov
        for k, (cnt, ov, gap, ca) in sorted(rep.items(), key=lambda t: -t[1][1]):
            if ov < MIN: continue
            print(f"   normal {k[0]} plane {k[1]:7.2f} {k[2][0]}/{k[2][1]}: {cnt:4d} pairs, {ov:7.3f} m2, gap {gap*1000:.0f} mm, e.g. at {np.round(ca, 2).tolist()}")
        if ground:
            print(f"   on the ground: {len(ground)} faces, {sum(g[0] for g in ground):.2f} m2, e.g. at {np.round(ground[0][2], 2).tolist()}")
    print("total", total)
