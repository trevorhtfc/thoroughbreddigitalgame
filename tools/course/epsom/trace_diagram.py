"""Epsom, phase 1, step 1: trace At The Races' course diagram into numbers (reference/epsom/diagram-trace.json).

Why the diagram (18 Nov 2026): the workspace can't reach OpenStreetMap or the height tiles, and the owner's computer and
browser weren't connected, so the first plan is traced from the diagram he sent (At The Races' Epsom flat diagram,
https://www.attheraces.com/images/course-guides/epsomdowns/epsomft.png, 650 x 363 px). The image itself is kept out of
the repo (third-party); only the trace is kept. When OSM and real heights can be fetched, layout.py swaps them in.

What it reads off the picture:
  - the green track, filled and thinned to its middle line (a one-pixel skeleton);
  - each route's middle line as the shortest path along that skeleton from its far end to the end of the straight;
  - the start marks (the pairs of black ticks across the track), the post (the red pin) and the north arrow.

    python3 tools/course/epsom/trace_diagram.py /path/to/epsomft.png
"""
import json, sys, heapq
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.morphology import skeletonize, closing, disk

REPO = Path(__file__).resolve().parents[3]
OUT = REPO / "reference/epsom/diagram-trace.json"

# the start marks: each a pair of black ticks across the track (pixel centres, read from the picture's black blobs)
TICKS = {"5f": [[77.5, 279.0], [77.0, 307.0]], "6f": [[106.0, 104.0], [78.4, 110.6]], "7f": [[147.7, 44.2], [173.7, 55.0]],
         "1m114y": [[303.1, 60.1], [297.9, 87.6]], "1m2f18y": [[414.2, 89.5], [407.0, 116.1]],
         "1m4f10y": [[548.0, 88.2], [556.8, 115.0]]}
# each route: where its middle line begins (beyond its furthest start) and ends (the straight's far end past the post)
ENDS = {"straight": [(40, 293), (535, 293)], "six": [(90, 96), (535, 293)], "seven": [(160, 44), (535, 293)],
        "round": [(582, 77), (535, 293)]}


def main(path):
    im = np.array(Image.open(path).convert("RGB")).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    green = (g > 100) & (r < 140) & (b < 120) & (g > r + 30)
    m = closing(green, disk(4))
    m = ndimage.binary_fill_holes(m)                       # the lettering on the track
    lab, n = ndimage.label(m)
    m = lab == (np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1)
    sk = skeletonize(m)
    half = ndimage.distance_transform_edt(m)
    ys, xs = np.nonzero(sk)
    nodes = {(int(x), int(y)) for x, y in zip(xs, ys)}

    def nearest(q):
        return min(nodes, key=lambda p: (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2)

    def path_between(a, b):                                # Dijkstra along the skeleton's 8-connected pixels
        a, b = nearest(a), nearest(b)
        dist, prev, pq = {a: 0.0}, {}, [(0.0, a)]
        while pq:
            d, p = heapq.heappop(pq)
            if p == b: break
            if d > dist[p]: continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    q = (p[0] + dx, p[1] + dy)
                    if (dx or dy) and q in nodes:
                        nd = d + (1.4142 if dx and dy else 1.0)
                        if nd < dist.get(q, 1e9):
                            dist[q] = nd; prev[q] = p; heapq.heappush(pq, (nd, q))
        out = [b]
        while out[-1] != a: out.append(prev[out[-1]])
        return out[::-1]

    routes = {k: [list(p) for p in path_between(*v)] for k, v in ENDS.items()}
    red = (r > 180) & (g < 80) & (b < 80)
    py, px = np.nonzero(red)
    out = {
        "_about": "Traced by tools/course/epsom/trace_diagram.py from At The Races' Epsom flat course diagram (650 x 363 px; "
                  "the image is not kept in the repo). Pixels, x right, y down. 'routes': each route's middle line in running "
                  "order (a one-pixel skeleton of the green track); 'ticks': the start marks; 'post': the red pin's x and the "
                  "straight's middle y; 'north': the compass arrow's direction (x right, y down); 'halfWidthPx': the drawn "
                  "track's half width.",
        "source": "https://www.attheraces.com/images/course-guides/epsomdowns/epsomft.png",
        "routes": routes, "ticks": TICKS,
        "post": [round(float(px.mean()), 1), 293.0],
        "north": [0.103, 0.995],
        "halfWidthPx": round(float(np.median(half[sk])), 2),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, separators=(",", ":")))
    for k, v in routes.items():
        print(k, len(v), "px points from", v[0], "to", v[-1])


if __name__ == "__main__":
    main(sys.argv[1])
