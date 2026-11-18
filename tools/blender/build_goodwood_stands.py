"""Goodwood's stands, phase 4, from the kit (the Park's, York's, the Rowley Mile's and Ascot's pieces).

    python3.11 -c "exec(open('tools/blender/build_goodwood_stands.py').read())"
    SHEET=1 python3.11 -c "exec(...)"      # also render reference/goodwood/renders/stands-sheet-1.jpg and -2.jpg

Owner, 18 Nov 2026, on Google's aerial of the stand side (reference/goodwood/stands-markup.jpg): "Mark up of stand types.
Make the stand types longer if needed to proportionally fill the space
  1. Balcony stand facing up the home straight
  2. Mast stand
  3. Tent stand
  4. Victorian stand
Blue zone are then marquees / festival kit ... Try and keep the alignment of the stand to the track as per the Google
image." His boxes, in world axes, are in reference/goodwood/stands-zones.json.

  goodwood_balcony    the Park's balcony stand (colonnade, open seating, two covered galleries, flat roof behind a
                      cornice) lengthened to 16 bays (61 m) to fill his box 1, west of the post, facing up the straight
  goodwood_mast       the Park's mast stand (stepped terrace, two glazed levels, the vaulted flat roof on six masts),
                      11 bays (84 m; owner, 18 Nov 09:04: "a bit small"; also scaled up 12% where it is placed): his
                      box 2, on the March Stand's footprint
  goodwood_tent       the Park's tent stand (seated terrace, glazed hall, deck under three tensile tents, the veranda
                      wing), as built (59 m): his box 3, the Sussex Stand's footprint
  goodwood_victorian  the Rowley Mile's Victorian stand (Ascot's terrace under the long hipped slate roof, dormers,
                      chimneys, cupola) cut to 24 bays (84 m) to fill his box 4, WITHOUT the end pavilion; both ends are
                      flank walls following the rake (owner, 17 Nov: never a block or tower on the end of a stand)

Writes assets/models/architecture/goodwood_stands.glb and .json (as the Park's: building axes x along the front, y into
the building (front faces -y), z up; origin the middle of the front on the ground; offset: how far the piece's middle
is from the origin along x; crowd: [x0, x1, y0, y1, floor] where spectators stand).
"""
import json, math, os

REPO = os.path.abspath(os.environ.get("REPO", "."))
def rp(*p): return os.path.join(REPO, *p)

# ---- the Park's build's definitions (which bring York's, the Rowley Mile's, the July Course's and Ascot's), without
# its build loop
_psrc = open(rp("tools/blender/build_park_stands.py")).read()
exec(_psrc[:_psrc.index("\nPIECES = [")])


def victorian_flanked(bays=24, rows=10, tread=1.0, rise=0.28):
    """The Rowley Mile's Victorian stand (grand_pavilion_stand with the hipped roof), no end pavilion, and a flank
    wall at each end following the section: the lawn terrace's rake, up to the terrace stand's front, then the
    standing terrace's rake on its roof to the back."""
    info = grand_pavilion_stand(bays, rows, tread, rise, end_pavilion=False, roof="hipped")
    L, T, z0 = bays * BAY, rows * tread, 0.25
    h = L / 2
    top = terrace_top(18.0)
    z_front = P + 2.9 + 0.35 + 4.3 + 1.0                      # the roof terrace's first row (as terrace_top counts)
    FL = [(-0.5, 1.3), (T, z0 + (rows - 1) * rise + 1.1), (T + 0.4, P + 1.2), (T + 3.6, z_front + 1.05), (T + 17.6, top + 1.1)]
    for x, side in ((-h, -1), (h, 1)):
        rake_flank(x, side, FL)
    info["section"] = {"lawnTerrace": round(T, 2), "terraceTop": round(top, 2)}
    return info


PIECES = [
    ("goodwood_balcony", lambda: colonnade_stand(16, 3.6, "flat")),
    ("goodwood_mast", lambda: mast_stand(11, 7.6)),                 # (owner, 18 Nov 09:04: "a bit small": a bay longer, and scaled up 12% where placed)
    ("goodwood_tent", tent_stand),
    ("goodwood_victorian", victorian_flanked),
]
LIB = bpy.data.collections.new("goodwood_stands")
bpy.context.scene.collection.children.link(LIB)
OBJ, INFO = {}, {}
for name, fn in PIECES:
    CROWD.clear()
    info = fn()
    ob, tris = kit_to_object(K, name, MATS, LIB)
    info["crowd"] = list(CROWD); info["triangles"] = tris
    OBJ[name], INFO[name] = ob, info
    print("%-20s %6d triangles, %3d crowd areas, %.1f m wide, %.1f m deep, %.1f m high" % (name, tris, len(CROWD), info["width"], info["depth"], info["height"]), flush=True)

out_dir = rp("assets/models/architecture")
json.dump({"_about": "Goodwood's stands (tools/blender/build_goodwood_stands.py). Building axes: x along the front (left to right "
                     "from the track), y into the building (front faces -y), z up; origin the middle of the front on the ground "
                     "(offset: how far the piece's middle is from it along x). crowd: [x0, x1, y0, y1, floor] where spectators stand.",
           "colours": COL, "pieces": INFO}, open(os.path.join(out_dir, "goodwood_stands.json"), "w"), indent=0)
bpy.ops.object.select_all(action="DESELECT")
for o in LIB.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "goodwood_stands.glb"), export_format="GLB", use_selection=True,
                          export_yup=True, export_apply=False, export_animations=False)
print("exported goodwood_stands.glb", flush=True)

REN = rp("reference/goodwood/renders")
if os.environ.get("SHEET"):
    exec(_psrc[_psrc.index("def setup_scene("):_psrc.index('if os.environ.get("SHEET")')])     # the Park's render helpers          # each stand from the front three-quarters, and its end (the flank wall)
    scene = setup_scene(2000, 900)
    lawn(0, 0, 6000)
    x = 0.0
    spans = []
    for name, _ in PIECES:
        w = INFO[name]["width"]
        OBJ[name].location = (x + w / 2 - INFO[name].get("offset", 0.0), 0, 0)
        spans.append((name, x, x + w))
        x += w + 25
    a, b = spans[0][1], spans[-1][2]
    mid = (a + b) / 2
    shoot(scene, "stands-sheet-1", (mid - 40, -(b - a) * 0.62, (b - a) * 0.13), (mid, 10, 10), lens=30)
    for name, a, b in spans:                                       # each stand's left end, three-quarters
        shoot(scene, "stands-end-" + name.split("_")[1], (a - 38, -34, 16), ((a + b) / 2 - 8, 14, 10), lens=28)
