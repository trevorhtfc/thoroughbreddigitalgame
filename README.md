# Thoroughbred — digital game

Home for the Thoroughbred digital games (the quick Thoroughbred Ascot game and the longer career game) and the shared race view they will both use.

## What's where

| Folder | What's in it |
|---|---|
| `assets/models/` | 3D models. **`racehorse_rigged.glb` is the one to use**: the horse and jockey with the rebuilt gallop with head nod, a proper silks layout and a horse-under-pressure clip; the jockey rides still in the saddle with only his arms moving (quiet, push, drive). `racehorse_neutral.glb` is the colour-stripped original it was built from; `master/racehorse_master.blend` is the Blender source. |
| `assets/silks/` | Owners' silks artwork, one image per set of colours. |
| `assets/portraits/` | Horse head portraits for menus and cards. |
| `godot-prototype/` | The earlier Godot race scene (Godot 4.7). Kept for reference: its cameras, running-order panel and silks recolouring are being carried across to the web version. |
| `silks/` | Traditional silks: `silks.json` describes each set (body, sleeves, cap); `textures/` holds them painted for the 3D jacket and `icons/` as racecard icons, plus the pattern catalogue. |
| `tools/` | Scripts that build the horse and silks; see `tools/README.md`. |
| `race-view/` | The web race view. `index.html` is the single-horse gallop test: one horse with a chosen coat and silks galloping down an Ascot straight, with the jockey's riding building through the race. `silks.html` is the Silks Workbench: your artwork beside the traditional silks on a 3D jockey, the pattern catalogue and the zone test. `race-view/assets` holds web copies of the silks thumbnails and 3D silks, the tint mask and the horse model repackaged for the web, so the originals above stay untouched. |
| `assets/models/tint_masks/` | Masks for the neutral model: coat, points (mane, tail, lower legs) and silks. |

## How we build: web first, ready for Godot or Unreal

The race view is built for the web first, so anyone can play from a link and the game can sit beside a leaderboard. Everything is built so it can move to Godot or Unreal later without being redone. Only the thin web viewer would be rewritten. Every chat working here follows these rules:

1. **3D models are made in Blender** (scripted, headless), with the `.blend` master kept in `assets/models/master/` and the export as standard `.glb`. Never build a model only in web code.
2. **Courses are data.** Each course is a file describing its centre line (straights, bends, rises and falls), the running rail, where the stalls, posts, stands and crowd sit, and where each TV camera is placed. The viewer builds the course from that file; the scenery pieces themselves come from Blender.
3. **The race is worked out separately from the pictures.** The race sim produces a timeline (every horse's distance and lane at every moment, and the result); the 3D view only plays it back. Any engine can replay the same timeline, and results can be checked without any 3D.
4. **Looks are data too.** Silks (`silks/silks.json`), coat colours and the camera rules (which shot at which point of the race) live in data files, not in viewer code.
5. **Colouring rules are simple and written down** (multiply masks, see `tools/README.md`), so each engine's shader is a small rewrite.
6. **Engine-specific code stays in its own folder** (`race-view/` for the web) and holds no game rules.

## Adding files

On GitHub, open the folder you want first, then use **Add file → Upload files**, so the new files land inside that folder. Finish with the green **Commit changes** button.
