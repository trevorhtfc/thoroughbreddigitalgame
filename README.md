# Thoroughbred — digital game

Home for the Thoroughbred digital games (the quick Thoroughbred Ascot game and the longer career game) and the shared race view they will both use.

## What's where

| Folder | What's in it |
|---|---|
| `assets/models/` | 3D models. **`racehorse_rigged.glb` is the one to use**: the horse and jockey with the rebuilt gallop, a proper silks layout, a rigged jockey and riding animations. `racehorse_neutral.glb` is the colour-stripped original it was built from; `master/racehorse_master.blend` is the Blender source. |
| `assets/silks/` | Owners' silks artwork, one image per set of colours. |
| `assets/portraits/` | Horse head portraits for menus and cards. |
| `godot-prototype/` | The earlier Godot race scene (Godot 4.7). Kept for reference: its cameras, running-order panel and silks recolouring are being carried across to the web version. |
| `silks/` | Traditional 3D silks: `silks.json` describes each set (body, sleeves, cap) and `textures/` holds them painted for the jacket. |
| `tools/` | Scripts that build the horse and silks; see `tools/README.md`. |
| `race-view/` | The web race view. `index.html` is the single-horse gallop test: one horse with a chosen coat and silks galloping down an Ascot straight, with the jockey's riding building through the race. `race-view/assets` holds web copies of the silks thumbnails and 3D silks, the tint mask and the horse model repackaged for the web, so the originals above stay untouched. |
| `assets/models/tint_masks/` | Masks for the neutral model: coat, points (mane, tail, lower legs) and silks. |

## Adding files

On GitHub, open the folder you want first, then use **Add file → Upload files**, so the new files land inside that folder. Finish with the green **Commit changes** button.
