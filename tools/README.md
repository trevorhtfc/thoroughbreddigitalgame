# Tools

Scripts that build the game's horse and silks. Nothing here is tied to the web: the outputs are a standard glTF model, PNG textures and a JSON data file, which Godot, Unity, Unreal or a browser can all use.

## The horse

`assets/models/racehorse_rigged.glb` is the horse to use in any engine. It is built from the colour-stripped `racehorse_neutral.glb` in these steps (run from the repo root), each a headless Blender 4.2 script (run with Blender's Python module, `bpy`):

| Step | Script | What it does |
|---|---|---|
| 1 | `tools/blender/rebuild_gallop.py` | Rebuilds the gallop so the legs follow a real gallop footfall (Muybridge, 1878): left hind, right hind, left fore, right fore, then suspension with the legs gathered. Hooves stay planted while in stance. Adds a head-and-neck nod, lowest as the leading fore takes the weight. |
| 2 | `tools/blender/repattern_jacket.py` | Zones the jockey's silks into body, left sleeve, right sleeve and cap. Cuts clean seams at the armholes and cap rim, folds the stray silk patches on the body mesh into the silks, and lays each zone out in its own band of the texture so nothing mirrors. |
| 3a | `tools/blender/pin_jockey.py` | Binds the whole jockey to the horse's back (Spine_4), so his face, chin and cap don't swing with the horse's head nod. Mane and reins stay with the horse. |
| 3b | `tools/blender/rig_arms.py` | Gives the jockey's arms their own bones (upper arm and forearm each side, on the horse's back) and keys `ride_quiet`, `ride_push` and `ride_drive`: the hands push forward along the neck as the head goes down and draw back with the elbows bending. Only the sleeves and gloves move; the movement fades in from the shoulder seam, and his head, face and body stay still. |
| 3c | `tools/blender/horse_drive.py` | Adds `gallop_drive`: the same stride with the neck stretched lower and a deeper nod, for the horse under pressure. Horse bones only. (`rig_jockey.py`, a fuller jockey rig with body and head movement, is kept for later, for use with a jockey model that is separate from the horse.) |
| 4 | `tools/blender/export_glb.py` | Exports glTF, keeping only the channels each action actually moves. |

The Blender file after step 3 is kept as `assets/models/master/racehorse_master.blend`.

```
python tools/blender/rebuild_gallop.py   -- assets/models/racehorse_neutral.glb step1.blend
python tools/blender/repattern_jacket.py -- step1.blend assets/models/tint_masks/build-mask.png step2.blend
python tools/blender/pin_jockey.py       -- step2.blend assets/models/tint_masks/build-mask.png step2b.blend
python tools/blender/rig_arms.py         -- step2b.blend assets/models/tint_masks/build-mask.png step2c.blend
python tools/blender/horse_drive.py      -- step2c.blend step3.blend
python tools/blender/export_glb.py       -- step3.blend assets/models/racehorse_rigged.glb
```

### Animations in the model

Every clip lasts exactly one stride (0.48 s), so they can be played together and stay in step. Scale playback speed with the horse's speed: at 14.6 m/s (model scaled ×3) the legs match the ground at normal speed.

| Clip | Moves | Use |
|---|---|---|
| `gallop` | horse | normal galloping |
| `gallop_drive` | horse | the same stride with the neck stretched lower and a deeper head nod; blend in as the horse responds to pressure |
| `ride_quiet` | jockey's arms | hands nearly still |
| `ride_push` | jockey's arms | hands and heels: arms pumping with the stride |
| `ride_drive` | jockey's arms | the same, bigger |
| `walk` | horse | walking (original clip) |

Blend the arms by the jockey's effort (0 quiet, 1 push, 2 drive) and `gallop` into `gallop_drive` by a slightly delayed copy of it, so the horse visibly responds a beat after he asks.

### Colouring the horse

The horse's texture is neutral grey. `assets/models/tint_masks/` holds masks for the coat, the points (mane, tail, lower legs) and the silk areas on the body mesh. Multiply each masked area by the chosen colour, keeping the grey texture's light and shade. `tools/web/make_tint_mask.py` packs them into one RGB texture (R coat, G points, B silks); show everything outside the masks (tack) in neutral grey. Its `--build` version, `build-mask.png`, also marks leftover silk patches and is only for the Blender steps.

## Silks

`silks/silks.json` describes each set of silks the way registered colours are written: body, sleeves and cap, each a colour plus an optional pattern in a second colour. The 17 sets are read from your menu artwork in `assets/silks/` (left strip = sleeves, top semicircle = cap, the rest = body), with the palette sampled from it. The artwork itself stays as it is for menus.

`tools/silks/make_silks.py` paints every set two ways from the same pattern code, so they always agree:

- `silks/textures/` — the texture the 3D jockey wears
- `silks/icons/` — a flat racecard-style icon

It also paints the pattern catalogue (`catalogue-*`), the five-zone test (`zones`) and writes `silks/catalogue.json` with each set's registered-colours description.

```
python tools/silks/make_silks.py silks/silks.json silks 1024
```

Patterns available:

- **Body:** plain, hoops, hooped band, stripes, sash, crossbelts, chevron, inverted chevron, chevrons, braces, halved, quartered, spots, large spots, three spots, disc, star, diamond, epaulets, panel, seams, check
- **Sleeves:** plain, hoops, stripes, halved, chevrons, armlets, cuffs, spots, diabolo, seams
- **Cap:** plain, quartered, halved, striped, hooped, spots, four spots, star, diamond, peak

To add a set of silks, add one entry to `silks.json` and run the script.

## Web

`tools/web/glb_to_web.py` splits a .glb into files the claude.ai artifact host will serve (glTF JSON, the geometry as base64 text, and the images). The race view reassembles them in the browser. Other engines should use the .glb directly.

## Courses

A course is a data file in `courses/` (see `courses/ascot-home-straight.json`): the centre line, track width and lanes, rails, winning post, furlong poles, paths, tree clumps, woodland strips, the TV cameras and the director's rules (which camera at which point of the race). Positions are in metres: x = direction of running, y = up, z = across the course (+ towards the stands). Any engine builds the course from this file.

| Script | What it does |
|---|---|
| `tools/blender/build_course_props.py` | Builds the course furniture in Blender (running rail module, heritage winning post with the spiral pole and roundel, furlong poles 1–7) and exports `assets/models/course/course_props.glb`, with the source in `assets/models/master/course_props.blend`. |
| `tools/course/paint_scenery.py` | Paints the illustrated textures into `assets/course/textures/`: `turf.png` (soft lanes along the track, no grid), `grass.png`, `path.png` `trees.png` (four painted trees in gouache masses, lit from the upper left, used as upright cut-outs) and `treeline.png` / `treeline_far.png` (continuous painted woodland that tiles left to right, for the tree lines behind the course). |

```
python tools/blender/build_course_props.py -- assets/models/course/course_props.glb assets/models/master/course_props.blend
python tools/course/paint_scenery.py assets/course/textures
python tools/web/glb_to_web.py assets/models/course/course_props.glb race-view/assets/course course-props
```

The illustrated finish (painterly smoothing, soft ink outlines where depth jumps, a warm heritage grade, paper grain and vignette) is a single full-screen pass after the 3D render; `race-view/look-test.html` has the web version. Each engine needs its own copy of that pass, but it is short and self-contained.

## Architecture

The cream Victorian grandstand is rebuilt from scripted, snap-together pieces on a 3.5 m bay grid (veranda tier, windowed storey with balcony, ironwork gallery, clock tower, pavilion, steps), following the FRONT elevation of `reference/architecture/victorian-grandstand-sheet.png` at realistic sizes: 3.5 m storeys, a stand of 124 m and a clock tower of about 30 m to the finial. It is chunkier and simpler than the sheet, with the signature features drawn out but kept believable: a clock on all four faces, bold iron lace (full arches, roundels in the spandrels, a roundel frieze and roundel balustrade) and verandas that step back as they rise.

| File | What it is |
|---|---|
| `assets/models/architecture/victorian_grandstand_layout.json` | The layout as data: each segment's kind, position along the front, storeys or tiers, depth, setback and roof, the steps, and the colours. Change the numbers and re-run the script. |
| `assets/models/architecture/victorian_grandstand.glb` | The stand: about 72,000 triangles in 11 meshes, one per material, so 11 draw calls. Origin at ground level in the middle of the front; the front faces +z (glTF). |
| `assets/models/architecture/victorian_grandstand_crowd_areas.json` | Where spectators can stand: each veranda tier, gallery, balcony and flight of steps, with its floor height. |
| `assets/models/architecture/crowd_people.glb` | Four simple spectator figures (gent in top hat, gent in hat, two ladies in hats), about 150 triangles each, with clothes, skin and hat materials to tint per instance. |
| `assets/models/master/victorian_grandstand.blend` | The Blender master. |

| Script | What it does |
|---|---|
| `tools/blender/kit.py` | The shared building kit (boxes, columns, arches, roundels, balustrades, windows, roofs) used by both build scripts. |
| `tools/blender/build_grandstand.py` | Builds the stand and the crowd figures from the layout and exports the files above. |
| `tools/blender/grandstand_look_test.py` | Stills of the stand in the stylised scene: on the near side of the track facing the course, with its crowd along the rail, on the lawn, up the steps and on every balcony, and the field galloping past. |

```
python -c "exec(open('tools/blender/build_grandstand.py').read())"
python -c "exec(open('tools/blender/grandstand_look_test.py').read())" renders 32
```

### Site components

The pieces that dress the ground round the stand, from `reference/architecture/site-components-sheet.png`, built the same way. Each is a separate node in `assets/models/architecture/site_props.glb` (about 38,000 triangles for all 23), with its origin on the ground at the middle of its footprint and its front facing +z (glTF): `marquee_peaks`, `marquee_clearspan`, `big_top`, `pagoda_counter`, `stand_open`, `stand_covered`, `terrace_deck`, `viewing_tower`, `kiosk_awning`, `booth_hut`, `kiosk_row_arched`, `pagoda_kiosk`, `pergola_picnic`, `picnic_table`, `planter_long`, `planter_short`, `fence_picket`, `fence_cross`, `barrier_rail`, `signboard`, `flagpole`, `banner_flag`, `signpost`.

| File | What it is |
|---|---|
| `assets/models/architecture/site_props_colours.json` | Canvas, painted timber, the big top's sage stripe, flowers and so on. |
| `assets/models/architecture/site_props_spots.json` | Seats and standing spots on each piece, for crowds. |
| `courses/ascot-site-dressing.json` | Where each piece stands, relative to the middle of the grandstand's front (dx along the running, dz across, turn in degrees), plus crowd areas on the lawns and the far rail. Add, move or remove lines to dress the ground. |
| `courses/ascot-home-straight.json` → `structures` | Where the grandstand stands on the course, pointing to the dressing file. |

| Script | What it does |
|---|---|
| `tools/blender/build_site_props.py` | Builds the 23 pieces and exports the files above, with the master in `assets/models/master/site_props.blend`. |
| `tools/blender/site_props_catalogue.py` | Renders the pieces laid out like the crib sheet, on grey, to compare. |

```
python -c "exec(open('tools/blender/build_site_props.py').read())"
python -c "exec(open('tools/blender/site_props_catalogue.py').read())" site_props_catalogue.png 40
```

`tools/blender/grandstand_look_test.py` places the pieces from the dressing file and renders two more shots: `far_side` (from the stand's balcony across the course) and `site_aerial`.

### Finish line

`tools/blender/build_finish_line.py` builds the finish-line assembly from `reference/architecture/finish-line-sheet.png` into `assets/models/architecture/finish_line.glb` (about 14,000 triangles): 30 m of running rail at 1.05 m, box hedges with boards standing in them, the lit race-time board, the winning post with its red loop and diamond plate, two planters, and a bracket clock on a lamp post. Its origin is the foot of the post on the rail line; the red loop stands across the course, on the winning line. `courses/ascot-home-straight.json` → `winningPost` puts it on the far side, opposite the grandstand (`side: "far"`), and says how much of the course rail it replaces (`railFrom`, `railTo`). The grandstand is placed so its clock tower is directly opposite the post.

`tools/blender/build_stalls.py` builds the starting stalls kit from the photos in `reference/stalls/` into `assets/models/course/starting_stalls.glb` (run headless with `python -c "exec(open('tools/blender/build_stalls.py').read())"`, a few seconds): one stall bay that repeats (padded partition, cream tubular frame, walkway, yellow number board, cream top board, closed rear gate), a closing partition, the unit end tower on tandem wheels, a left and a right front half-gate (each hinged on its own origin, so it can swing open), the figures 1–30 and a "Thoroughbred" plaque, each a separate node. Sizes and how the pieces fit together are in `starting_stalls_kit.json` beside it. Package for the web with `tools/web/glb_to_web.py ... --meshopt` and copy the kit file to `race-view/assets/course/`.

`tools/course/place_stalls.py` writes `courses/ascot-stalls.json`: for each start (straight mile, round mile, 2 miles) where the inside rail is, which way the horses run, and where every stall stands (world x, z and metres from the inside rail), with Ascot's draw convention (stall 1 nearest the inside rail: the far side on the straight course). The race engine and the race view both read it; copy it to `race-view/assets/course/` after re-running.

## In the web race view

`race-view/look-test.html` builds the same world from the same files: the grandstand, the site components from the dressing file, the finish line opposite, and the crowd. Static pieces are merged into one mesh per material (about 40 draw calls for all the architecture). The crowd is instanced, one draw call per figure part, tinted from `crowd_palette.json`, and thinned by the quality setting (all on High, half on Medium, a quarter on Low). The diagnostics panel has switches for Buildings and Crowd. Web copies of the models and data are in `race-view/assets/architecture/` (made with `tools/web/glb_to_web.py`).

## Baked lighting and the Final Furlong test

`race-view/final-furlong.html` is a small test of how close a web page can get to the Blender stills: only the last furlong, with
- Blender's lighting baked into everything that doesn't move (`tools/blender/bake_static_world.py`): Cycles works out the stills' soft sun, sky light, bounce and shadows on the grandstand, site pieces, finish line and ground once, and stores them as light maps (`assets/models/baked/`). The page draws that scenery unlit (material colour × baked light), so it costs nothing to light.
- the stills' leafy trees (`tools/blender/export_trees.py` → `assets/models/trees/trees.glb`), instanced, with their soft-ball shading and colouring
- the stills' colour handling (AgX), painted sky, puffy clouds and haze, and the same sun on the horses, jockeys and crowd

```
python -c "exec(open('tools/blender/bake_static_world.py').read())" 48      # about 25 minutes; KEEP_GROUND=1 skips the ground
python -c "exec(open('tools/blender/export_trees.py').read())"
python tools/web/glb_to_web.py assets/models/baked/static_world.glb race-view/assets/baked static_world
python tools/web/glb_to_web.py assets/models/trees/trees.glb race-view/assets/trees trees
```
Re-run the bake whenever the stand, the site pieces, their places or the finish line change.


## The horse and jockey, v2 (quality test, Nov 2026)

A second horse and jockey built beside the first. **v1 is untouched** (tag `horse-v1-backup`): `racehorse_rigged.glb`, `racehorse_neutral.glb`, the v1 master and the v1 scripts above are exactly as they were, and Final Furlong still uses v1 unless the page is opened with `?horse=v2`.

| File | What it is |
|---|---|
| `tools/blender/build_racehorse_v2.py` | Builds v2 from the v1 master (read only) in one go, headless, about 40 seconds. Also reads the original Tripo model, `assets/models/source/racehorse_3d_model_Clone1.glb` (the owner's file, read only), for the jockey's painted face and the helmet's light and shade. |
| `assets/models/racehorse_v2_basecolor.jpg` | v2's colour texture: v1's grey texture with the jockey's face, goggles and strap painted back from the original (web copy `race-view/assets/model-v2/racehorse_v2-basecolor.jpg`). |
| `assets/models/racehorse_v2_silks_shading.png` | One grey map in the silks layout, multiplied with every owner's silks: the original helmet's seams, rim band and peak edge (white everywhere else). |
| `assets/models/racehorse_v2.glb` | The v2 model for any engine: three detail levels sharing one rig, every clip, textures embedded (silks show the five-zone test). |
| `assets/models/master/racehorse_v2.blend` | The v2 master. |
| `assets/models/racehorse_v2_rig.json` | What each clip is and how to blend them by speed and effort; the variety ranges; the colouring rule. |
| `tools/silks/make_silks_v2.py` | Paints the silks in the v2 layout (`silks/textures-v2/`, web copy `race-view/assets/silks-3d-v2/`), using the same pattern rules as `make_silks.py` (imported, unchanged). |
| `tools/web/package_racehorse_v2.py` | Squeezes the web copy (meshopt) into `race-view/assets/model-v2/`. |
| `race-view/horse-v2.js` | The web viewer's v2 horse: colouring, detail levels, the riding and the variety. |
| `race-view/horse-studio.html` | Close-up checking page: v1 and v2 side by side (`?compare=1`), any silks, coat, effort and view. |

```
python -c "exec(open('tools/blender/build_racehorse_v2.py').read())"          # WEB_GLB=<path> for the web copy (default /tmp)
python tools/silks/make_silks_v2.py silks/silks.json 1024
python tools/web/package_racehorse_v2.py /tmp/racehorse_v2_web.glb
```

**What v2 changes**
- **Colour zones as vertex colours.** Every face belongs to one zone. On the main material the vertex colour is the mask: R coat, G points (mane, tail, lower legs), B the jockey's face (kept as painted, times his skin tone); everything else (tack, breeches, boots, gloves, goggles) keeps the neutral texture. Colours stop exactly at the zone edges, so nothing leaks: no coat on the jockey's face, no cap colour down his neck, no sleeve colour on his gloves or the mane, no jacket flecks on his breeches, no pale patches in the mane. No tint-mask texture is needed.
- **Silks layout v2.** Body (wrapping right round the torso, so the back is its own pattern), two sleeves and the cap as a disc, each with a gutter painted in its own colour, so zones can't bleed into each other at a distance.
- **The original helmet and face** (owner, 4 Nov, after the first try's new cap looked "like an old military hat"): the helmet keeps the original model's shape, its seams, dark rim band and peak edge, recoloured with the owner's cap (patterns map onto it as a disc from the crown, so quarters, stars and stripes sit right). The face, goggles, chin strap and hair are the original painting, shifted to one of seven skin tones per jockey. Round the head the original painting decides each face's zone (helmet blue, jacket colours, skin, dark). His chin and throat, which the mane band used to take (a dark "beard" under his chin once his head moved), are his again and on his head bone.
- **The jacket and breeches ironed** (the crumpled facets smoothed), the boots taken out of the coat colour.
- **A jockey rig** on the horse's back: hips, chest, head, arms, forearms, hands and a whip. His legs stay in the irons. His hands are cut free of the reins and mane so they can move without dragging them.
- **Riding clips** (one stride each, played with the gallop): `ride_quiet` (effort 0), `ride_push` (1: hands and heels, back pumping), `ride_drive` (2: bigger, lower), `ride_whip` (3: driving with the left hand, one stroke a stride with the right). Blend by the timeline's effort.
- **Gallop v2**: `gallop_v2` and `gallop_v2_drive` add a tail carried up off the quarters that swings behind the stride, a fuller head and neck nod, and the loin flexing with the hind legs.
- **Variety** (cosmetic per runner, from its seed): additive ramp clips `jky_crouch_low`, `jky_crouch_high`, `jky_elbows_out`, `jky_hands_long`, `horse_head_high`, `horse_head_low`, `horse_tail_high`, played held at their end with a weight 0..1; plus a stride rhythm of ±4.5% and the jockey's timing up to 0.04 s off the stride.
- **Detail levels**: `racehorse_v2_close` (smoothed, about 45k triangles), `racehorse_v2` (race, about 18.7k: lighter than v1's 19.3k), `racehorse_v2_far` (about 7.2k). The race view picks by size on screen and allows only a few close at once.

## Horse movement and silks templates (13 Nov 2026)

- `tools/blender/gallop_balance.py` is read by `build_racehorse_v2.py`. It puts the body's rocking in step with the legs (forehand up while the hind legs push, level as the fore legs land) and plants every hoof on the turf at the ground's speed, re-timing each leg from the clip's own sweep and swing. The numbers to tune are at its top (`GB_STANCE`, `gb_pitch_curve`).
- The riding clips are made after the gallop, because the jockey gives against the saddle's movement: tall in his irons at effort 0, down low when pushing, lowest when driving. `ride_whip` is two strides long (a stroke, then a push). New "moments" (`jky_look_left`, `jky_look_right`, `jky_stand`) are faded in and out by the viewer (`race-view/horse-v2.js`).
- Section 4a of the build irons the jacket and breeches join, cuts the sleeve joins clean, and lays the silks out afresh from the jockey's shape (body round the line of his back; each sleeve along the cloth itself).
- `tools/silks/make_silks.py` now holds the owner's base templates (`TEMPLATES`: 25 jackets, 12 sleeves, 10 caps, numbered as on `reference/silks/templates-*.png`) and writes `silks/templates.json`. Review sheets of every template on the 3D jockey are in `reference/silks/templates/`.
