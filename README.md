# Thoroughbred — digital game

Home for the Thoroughbred digital games (the quick Thoroughbred Ascot game and the longer career game) and the shared race view they will both use.

## What's where

| Folder | What's in it |
|---|---|
| `assets/models/` | 3D models. `racehorse_neutral.glb` is the horse-and-jockey with colours stripped out, with gallop and walk animations and the silks as a separate part so any owner's colours can be painted on. |
| `assets/silks/` | Owners' silks artwork, one image per set of colours. |
| `assets/portraits/` | Horse head portraits for menus and cards. |
| `godot-prototype/` | The earlier Godot race scene (Godot 4.7). Kept for reference: its cameras, running-order panel and silks recolouring are being carried across to the web version. |
| `race-view/` | The web race view. `index.html` is the single-horse gallop test: one horse with a chosen coat and silks galloping down an Ascot straight. `race-view/assets` holds web-sized copies of the silks, the tint mask and the horse model repackaged for the web, so the originals above stay untouched. |
| `assets/models/tint_masks/` | Masks for the neutral model: coat, points (mane, tail, lower legs) and silks. |

## Adding files

On GitHub, open the folder you want first, then use **Add file → Upload files**, so the new files land inside that folder. Finish with the green **Commit changes** button.
