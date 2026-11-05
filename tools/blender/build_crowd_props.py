"""Small crowd props for the crowd review (race-view/crowd-review.html): a parasol, a picnic blanket and a hamper.

    python -c "exec(open('tools/blender/build_crowd_props.py').read())"

Simple and stylised, in the spirit of the old four crowd figures (crowd_people.glb): plain shapes, no
texture, one material per part so the race view can colour every copy from a palette (it multiplies
each part's colour by a per-copy colour, so the materials here are near white).

  parasol_canopy, parasol_pole   origin at the hand (the pole's foot); canopy rim 0.9 m above it, 1.0 m across
  picnic_blanket                 1 x 1 m, 3 cm thick, origin at the middle of its underside (scaled per copy)
  picnic_hamper                  0.46 x 0.30 x 0.26 m wicker box with a lid, origin at its foot

Writes assets/models/architecture/crowd_props.glb, then the web copy in race-view/assets/architecture/
(tools/web/glb_to_web.py, name crowd_props).
"""
import os, sys, math, subprocess
import bpy, bmesh
from mathutils import Matrix, Vector

REPO = os.path.abspath(".")
bpy.ops.wm.read_factory_settings(use_empty=True)
exec(open(os.path.join(REPO, "tools/blender/kit.py")).read())

MATS = {
    "prop_canopy": material("prop_canopy", "#ffffff", 0.8),
    "prop_pole": material("prop_pole", "#ffffff", 0.6),
    "prop_blanket": material("prop_blanket", "#ffffff", 0.95),
    "prop_hamper": material("prop_hamper", "#ffffff", 0.9),
}


def to_object(name, bm, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def parasol():
    # Canopy: eight panels, each gently domed, with a scalloped edge dipping between the ribs.
    bm = bmesh.new()
    ribs, rim, rise, lift = 8, 0.5, 0.26, 0.9
    rings = [(0.0, rise), (0.2, rise * 0.82), (0.36, rise * 0.48), (rim, 0.0)]
    verts = []
    for r, h in rings:
        ring = []
        for k in range(ribs * 2):
            a = k * math.pi / ribs
            between = k % 2 == 1
            rr = r * (0.94 if between and r == rim else 1.0)
            hh = h - (0.045 if between and r == rim else 0.0)
            ring.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), lift + hh)))
        verts.append(ring)
    top = bm.verts.new((0, 0, lift + rise + 0.01))
    n = ribs * 2
    for k in range(n):
        bm.faces.new((top, verts[0][k], verts[0][(k + 1) % n]))
    for i in range(len(verts) - 1):
        for k in range(n):
            a, b = verts[i][k], verts[i][(k + 1) % n]
            c, d = verts[i + 1][(k + 1) % n], verts[i + 1][k]
            bm.faces.new((a, d, c, b))
    bm.normal_update()
    for f in bm.faces:
        if f.normal.z < 0:
            f.normal_flip()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    for f in bm.faces:
        f.smooth = True
    can = to_object("parasol_canopy", bm, "prop_canopy")

    # Pole: a slim shaft with a hooked handle at the hand and a small finial on top.
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.011, radius2=0.011, depth=lift + rise + 0.07,
                          matrix=Matrix.Translation((0, 0, (lift + rise + 0.07) / 2 - 0.03)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.016, radius2=0.004, depth=0.07,
                          matrix=Matrix.Translation((0, 0, lift + rise + 0.07)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.016, radius2=0.016, depth=0.07,
                          matrix=Matrix.Translation((0.025, 0, -0.04)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    pole = to_object("parasol_pole", bm, "prop_pole")
    return can, pole


def blanket():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.015)) @ Matrix.Diagonal((1.0, 1.0, 0.03, 1)))
    bmesh.ops.bevel(bm, geom=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.01], offset=0.06, segments=2, affect="EDGES")
    return to_object("picnic_blanket", bm, "prop_blanket")


def hamper():
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.11)) @ Matrix.Diagonal((0.46, 0.30, 0.22, 1)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 0.235)) @ Matrix.Diagonal((0.48, 0.32, 0.04, 1)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.012, radius2=0.012, depth=0.22,
                          matrix=Matrix.Translation((0, 0, 0.29)) @ Matrix.Rotation(math.pi / 2, 4, "Y"))
    return to_object("picnic_hamper", bm, "prop_hamper")


objs = list(parasol()) + [blanket(), hamper()]
for i, ob in enumerate(objs):
    ob.location.x = i * 1.5          # side by side in the file; the race view reads each one's own geometry
tris = sum(sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in objs)
print("crowd props:", [ob.name for ob in objs], tris, "triangles in all", flush=True)

out_dir = os.path.join(REPO, "assets/models/architecture")
os.makedirs(out_dir, exist_ok=True)
glb = os.path.join(out_dir, "crowd_props.glb")
bpy.ops.object.select_all(action="DESELECT")
for ob in objs:
    ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=glb, export_format="GLB", use_selection=True, export_yup=True,
                          export_apply=False, export_animations=False)
print("exported", glb, flush=True)
subprocess.run([sys.executable if "python" in os.path.basename(sys.executable) else "python3",
                os.path.join(REPO, "tools/web/glb_to_web.py"), glb,
                os.path.join(REPO, "race-view/assets/architecture"), "crowd_props"], check=True)
