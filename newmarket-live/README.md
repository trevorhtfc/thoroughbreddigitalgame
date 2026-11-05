# Newmarket, the living map (home hub)

The Newmarket board as the full game's home screen, following the owner's concept art: each place has a
brass medallion and label; hovering lights up its area, clicking opens a card ("Enter Auction", "Visit Stables"…).
The board stays the painting; small 3D horses and horseboxes move over it, drawn in the board's own projection
so they sit in the picture at its scale.

Live: https://claude.ai/artifact/NnTToGjuhfCXvDK4fWkeMF

## What moves
- The morning string (7, in navy) walks out of the yard, up Kingston Road, down the High Street, out along
  Station Road and onto Warren Hill, then canters up the hill. About three minutes round.
- Lots of three canter up Warren Hill; a string gallops across the Gallops.
- Horses walk round the Tattersalls parade ring, the lunge ring in the east yard and the stable yard.
- Seven horseboxes drive the roads (Newmarket Road, Shied, High Street, Fordham, Bury, Kingston, Old Station,
  the Stud road, Exeter Road), coming and going off the edges.
- Cloud shadows drift over the whole board.

## Files
- `index.src.html` – the page source. `python3 tools/build.py` makes `index.html` (adds icons and the horse mark).
- `tools/clean_labels.py` – paints the six place names out of `assets/maps/newmarket-map.webp` →
  `assets/newmarket-board.webp` (the buttons replace them).
- `tools/silhouette.html` – renders the race horse mid-gallop as a silhouette → `tools/horse-mark.png`
  (the logo and the Warren Hill badge).
- `tools/icons.json` – icon paths from game-icons.net (CC BY 3.0, credited on the page).
- Open `index.html#routes` to see every route, ring and highlight area drawn over the board.

## Coordinates
Everything is in board pixels (1200 x 900). A horse or lorry at board point (x, y) with height h is drawn at
(x, y - h): the board is painted as if seen from the south with heights straight up the page.

## Next
- A higher-resolution master of the board would make it sharper on big screens (this one is 1200 x 900).
- Each card's picture is a crop of the board for now; it is the place for a painted scene of that location.
- The stats in the header are example figures; the full game fills them in.
