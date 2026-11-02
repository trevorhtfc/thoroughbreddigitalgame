# Tools

Scripts that build the game's horse and silks. Nothing here is tied to the web: the outputs are a standard glTF model, PNG textures and a JSON data file, which Godot, Unity, Unreal or a browser can all use.

## The horse

`assets/models/racehorse_rigged.glb` is the horse to use in any engine. It is built from the colour-stripped `racehorse_neutral.glb` in four steps (run from the repo root), each a headless Blender 4.2 script (run with Blender's Python module, `bpy`):

| Step | Script | What it does |
|---|---|---|
| 1 | `tools/blender/rebuild_gallop.py` | Rebuilds the gallop so the legs follow a real gallop footfall (Muybridge, 1878): left hind, right hind, left fore, right fore, then suspension with the legs gathered. Hooves stay planted on the turf while in stance. |
| 2 | `tools/blender/repattern_jacket.py` | Gives the jockey's silks a proper pattern layout (body, left sleeve, right sleeve, cap), replacing the old projection that mirrored every design. |
| 3 | `tools/blender/rig_jockey.py` | Adds jockey bones (hips, chest, head, arms, forearms), binds his upper body to them and keys the riding actions. |
| 4 | `tools/blender/export_glb.py` | Exports glTF, keeping only the channels each action actually moves. |

The Blender file after step 3 is kept as `assets/models/master/racehorse_master.blend`.

```
python tools/blender/rebuild_gallop.py   -- assets/models/racehorse_neutral.glb step1.blend
python tools/blender/repattern_jacket.py -- step1.blend step2.blend
python tools/blender/rig_jockey.py       -- step2.blend race-view/assets/tint-mask.png step3.blend
python tools/blender/export_glb.py       -- step3.blend assets/models/racehorse_rigged.glb
```

### Animations in the model

Every clip lasts exactly one stride (0.48 s), so they can be played together and stay in step. Scale playback speed with the horse's speed: at 14.6 m/s (model scaled ×3) the legs match the ground at normal speed.

| Clip | Moves | Use |
|---|---|---|
| `gallop` | horse | normal galloping |
| `gallop_drive` | horse | the same stride with the neck stretched lower and a deeper head nod; blend in as the horse responds to pressure |
| `ride_quiet` | jockey | sitting still, hands following the horse's head |
| `ride_push` | jockey | hands and heels: arms pumping, body rocking with the stride |
| `ride_drive` | jockey | all out |
| `walk` | horse | walking (original clip) |

Blend the jockey by effort (0 quiet, 1 push, 2 drive) and the horse by a slightly delayed copy of that effort, so it visibly responds a beat after the jockey asks.

### Colouring the horse

The horse's texture is neutral grey. `assets/models/tint_masks/` holds masks for the coat, the points (mane, tail, lower legs) and the silk areas on the body mesh. Multiply each masked area by the chosen colour, keeping the grey texture's light and shade. `tools/web/make_tint_mask.py` packs them into one RGB texture (R coat, G points, B silks).

## Silks

`silks/silks.json` describes each set of silks the way registered colours are written: body, sleeves and cap, each a colour plus an optional pattern in a second colour. `tools/silks/make_silks.py` paints them into the jacket's texture layout (`silks/textures/`). Your menu artwork in `assets/silks/` is separate and stays as it is.

```
python tools/silks/make_silks.py silks/silks.json silks/textures 1024
```

Patterns available:

- **Body:** plain, hoops, stripes, sash, crossbelts, chevron, inverted chevron, braces, halved, quartered, spots, large spots, disc, star, diamond, epaulets, panel, seams, collar and cuffs
- **Sleeves:** plain, hoops, stripes, chevrons, armlets, cuffs, spots, diabolo
- **Cap:** plain, quartered, striped, hooped, spots, star, peak

## Web

`tools/web/glb_to_web.py` splits a .glb into files the claude.ai artifact host will serve (glTF JSON, the geometry as base64 text, and the images). The race view reassembles them in the browser. Other engines should use the .glb directly.
