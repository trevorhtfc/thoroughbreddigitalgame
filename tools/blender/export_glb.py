"""Export the master horse .blend to glTF binary with all actions.

Run headless:  python export_glb.py -- <in.blend> <out.glb>
"""
import bpy, sys

src, out = sys.argv[-2], sys.argv[-1]
bpy.ops.wm.open_mainfile(filepath=src)
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_force_sampling=True,
    export_optimize_animation_size=True,
    export_optimize_animation_keep_anim_armature=False,
    export_frame_step=1,
    export_anim_single_armature=True,
    export_def_bones=False,
    export_skins=True,
    export_morph=False,
    export_yup=True,
    export_image_format="AUTO",
    export_vertex_color="ACTIVE",
    export_apply=False,
)
print("exported", out)
