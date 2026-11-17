"""Top-down render of the Park's buildings (the stand chain and the festival pieces from courses/park-draft.json), for
the site plan's enclosure panel: transparent, with the buildings' shadows, at a known scale.

    python3.11 tools/blender/park_siteplan_roofs.py     # writes reference/park/_siteplan_roofs.png (+ .json: its extent)

Orientation as the plan (the racing papers' way): world x runs right to left (the post on the right), the infield up.
"""
import os, json
for k in ("SHEET", "ARRANGE"):
    os.environ.pop(k, None)
exec(open("tools/blender/build_park_stands.py").read())
LAY = json.load(open(rp("courses/park-draft.json")))
X0, X1, Z0, Z1 = -70.0, 300.0, -140.0, 120.0     # world extent drawn (x along the straight, z: infield +)
PXM = float(os.environ.get("PXM", "11"))
scene = bpy.context.scene
for o in OBJ.values():
    o.location = (99999, 0, 0)
def put(name, x, y, turn=0.0, stretch=None):
    ob = OBJ[name].copy(); scene.collection.objects.link(ob)
    ob.location = (x, y, 0); ob.rotation_euler = (0, 0, math.radians(turn))
    if stretch: ob.scale = (stretch, 1, 1)
for p in LAY["stands"]["chain"]:
    put(p["piece"], p["x"] - INFO[p["piece"]].get("offset", 0.0), -p["z"], 0.0, p.get("stretch"))
for p in LAY["festival"]["pieces"]:
    put(p["piece"], p["x"], -p["z"], 180.0, p.get("stretch"))
world = bpy.data.worlds.new("w"); scene.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
bpy.ops.object.light_add(type="SUN"); sun = bpy.context.object
sun.data.energy = 3.4; sun.data.angle = math.radians(2)
sun.rotation_euler = (math.radians(28), 0, math.radians(-150))     # high sun; short shadows falling away from the course
bpy.ops.mesh.primitive_plane_add(size=2000, location=((X0 + X1) / 2, -(Z0 + Z1) / 2, 0.0))
bpy.context.object.is_shadow_catcher = True
scene.render.engine = "CYCLES"; scene.cycles.samples = int(os.environ.get("SAMPLES", "24")); scene.cycles.use_denoising = True
scene.view_settings.view_transform = "AgX"; scene.render.film_transparent = True
w, h = X1 - X0, Z1 - Z0
scene.render.resolution_x, scene.render.resolution_y = int(w * PXM), int(h * PXM)
cam = bpy.data.objects.new("top", bpy.data.cameras.new("top")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = max(w, h); cam.data.clip_end = 1000
cam.location = ((X0 + X1) / 2, -(Z0 + Z1) / 2, 300.0); cam.rotation_euler = (0, 0, math.pi)   # right = -x, up = +z (world)
scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = rp("reference/park/_siteplan_roofs.png")
bpy.ops.render.render(write_still=True)
json.dump({"x": [X0, X1], "z": [Z0, Z1]}, open(rp("reference/park/_siteplan_roofs.json"), "w"))
print("roofs rendered", flush=True)
