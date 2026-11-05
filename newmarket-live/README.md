# Newmarket, the living map (home hub)

The Newmarket board as the full game's home screen, following the owner's concept art and markups.
The board stays the painting; light, clouds and small 3D horses, people and horseboxes move over it, drawn in
the board's own projection so they sit in the picture at its scale.

Live: https://claude.ai/artifact/NnTToGjuhfCXvDK4fWkeMF

## The places
Palace House, the Jockey Club, Tattersalls, the Stables and the National Stud each have a lit outline: the owner's
own line from `markup/sites-markup.jpg`. It glows softly all the time, and heats up (a wider halo, a warm wash
over the site, a spark running round the edge) when the pointer is over the site or its button, or it is chosen.
The whole site is clickable. Warren Hill has its button only (no outline was drawn for it).

## What moves (the owner's route markup, `markup/routes-markup.jpg`)
- **Red, strings** (walk, off the left edge, then round again), kept to the roads where the drawn line crossed houses:
  National Stud → Bury Road → Exeter Road → across the Gallops; Tattersalls → Kingston Road → High Street →
  Station Road → Warren Hill; the stables → past the Jockey Club → the Shied → across Warren Hill.
- **Thin red, circled painted horses**: painted out of the board and replaced by lots working in a line on the
  Gallops and up Warren Hill, and the lone horse bottom left cantering away off the corner.
- **Blue, horseboxes**: in from the top of Fordham Road and the bottom of Newmarket Road, out along Bury Road and
  Old Station Road; they keep to the left.
- **Pink, low-key**: loose horses wandering the paddocks and the Stud (walk, rest, walk back), one walking off
  the right edge; horses led out of one stable and into another in the stable yard; a horse round the lunge ring;
  led horses round the Tattersalls parade ring; lads walking about the yards.
- **White, clouds**: hand-drawn clouds drifting across the top, with their shadows on the ground.

## Files
- `index.src.html` (page and styles) + `hub.src.js` (the script). `python3 tools/build.py` makes `index.html`
  (adds the icons, the horse mark and the site outlines from `markup/markup.json`).
- `markup/` – the owner's clean map and markups; `markup/extract.py` lines the markups up with the clean map and
  pulls out the outlines and lines into `markup.json`.
- `tools/clean_board.py` – makes `assets/newmarket-board.webp` from the clean map: mends the right-hand frame,
  paints out the labels under the buttons and the crossed-out National Stud label, and the circled horses.
- `tools/silhouette.html` – renders the race horse mid-gallop as a silhouette → `tools/horse-mark.png`.
- Open `index.html#routes` to see every route drawn over the board, with all the sites lit.

## Coordinates
Board pixels, 1448 x 1086. A thing at board point (x, y) with height h is drawn at (x, y - h).
