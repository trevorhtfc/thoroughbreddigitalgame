# Newmarket, the living map (home hub)

The Newmarket board as the full game's home screen, following the owner's concept art and markups.
It uses the Ascot game's look (green band, green buttons, gold for what's lit or chosen, cream boxes, Jost and
Nunito). The board stays the painting; light, clouds and small 3D horses, people and horseboxes move over it, drawn in
the board's own projection so they sit in the picture at its scale.

Live: https://claude.ai/artifact/NnTToGjuhfCXvDK4fWkeMF

## The places
Each place's lit outline is the owner's own line (`markup/sites-markup.jpg`, `markup/sites-markup-2.jpg`), refined
by `tools/refine_sites.py`: the pen's wobble evened out, and the line settled onto a roof edge only where one lies
within 6 pixels of it (never more). An earlier version that traced the buildings outright ignored the markup in
places and was dropped at the owner's request; `tools/tight_sites.py` is kept only for reference.

## What moves (the owner's route markup, `markup/routes-markup.jpg`)
- **Red, strings** (walk, off the left edge, then round again), kept to the roads where the drawn line crossed houses:
  National Stud → Bury Road → Exeter Road → across the Gallops; Tattersalls → Kingston Road → High Street →
  Station Road → Warren Hill; the stables → past the Jockey Club → the Shied → across Warren Hill.
- **Thin red, circled painted horses**: painted out of the board and replaced by lots working in a line on the
  Gallops and up Warren Hill, and the lone horse bottom left cantering away off the corner.
- **Blue, horseboxes** (three): in from the top of Fordham Road and the bottom of Newmarket Road, out along Bury Road
  and Old Station Road. Everyone keeps to the left, and a horsebox stops while a horse or person is just ahead of it.
- **Pink, low-key**: loose horses wandering the paddocks and the Stud (walk, rest, walk back), one walking off
  the right edge; horses led out of one stable and into another in the stable yard; a horse round the lunge ring;
  led horses round the Tattersalls parade ring; lads walking about the yards.
- **White, clouds**: pen-and-ink engraved clouds after the owner's reference (loose doubled outlines, crescents of
  hatching on each billow's shaded side, a soft scalloped underside), drifting across the top with their shadows.
  `tools/cloud.js` is the same drawing code on its own; `tools/clouds-check.html` lays a few out to compare.

## The day, the weather and the sounds (`atmos.src.js`)
- **A day passes every five minutes** (the clock is in the top bar). It opens at dawn with mist lying on the heath and
  the paddocks; the strings go out and the gallops are busy until late morning (two extra lots each), the afternoon
  is quieter and warmer, dusk turns the board rose and lamps come on in the windows and along the streets, and the
  night (the places' outlines glowing) passes quickly. Horses, lads and horseboxes each keep to their own hours.
- **Chimney smoke** rises and drifts with the wind from the houses and stable ranges, **flags** fly on the Tattersalls
  rotunda and the Jockey Club, and now and then **rooks** rise off Warren Hill and wheel away over the town.
  `tools/atmos.py` finds the chimneys and windows on the board → `assets/atmos.json`.
- **The lean-in**: picking a place tilts the board towards it and eases it into view; closing the card eases it back.
- **Sound** (off until the Sound button is pressed; browsers only allow sound after a click). A quiet breeze and
  birds by day, an owl at night. Each place has its own soundscape while the pointer is over it (or it is chosen):
  Tattersalls (crowd, an auctioneer in the browser's own voice, the gavel, horses led round), Warren Hill (lots
  galloping past, snorts, birds), the Stables (mucking out, buckets, hooves on cobbles, whinnies), the National Stud
  (foals and mares calling, birds), Palace House (a chime and a ticking clock), the Jockey Club (a quiet room, glasses),
  To the Races (a crowd building, a horn, a field going by). All made in the browser; real recordings could replace
  any of them later.
- In the console, `__setHour(19)` jumps to a time of day.

## Behind buildings
`tools/occlusion.py` finds the buildings and trees on the board and, for each of their pixels, where the thing
stands (its foot). It writes `assets/occlusion.png`; the horses', people's and horseboxes' shaders drop any part
of them that something standing further south is painted over, so they pass behind buildings and trees.
Run it again whenever the board image changes.

## Files
- `index.src.html` (page and styles) + `hub.src.js` (the script) + `atmos.src.js` (the day, smoke, lamps, sound). `python3 tools/build.py` makes `index.html`
  (adds the icons, the horse mark and the site outlines from `markup/markup.json`).
- `markup/` – the owner's clean map and markups; `markup/extract.py` lines the markups up with the clean map and
  pulls out the outlines and lines into `markup.json`.
- `tools/refine_sites.py` – the refined outlines → `markup/sites-tight.json` (run after `tools/occlusion.py`).
- `tools/clean_board.py` – makes `assets/newmarket-board.webp` from the clean map: mends the right-hand frame,
  paints out the labels under the buttons and the crossed-out National Stud label, and the circled horses.
- `tools/silhouette.html` – renders the race horse mid-gallop as a silhouette → `tools/horse-mark.png`.
- Open `index.html#routes` to see every route drawn over the board, with all the sites lit.
- In the console, `__probe(x, y)` stands a horse at a board point (to check what hides it).

## Coordinates
Board pixels, 1448 x 1086. A thing at board point (x, y) with height h is drawn at (x, y - h).
