# Newmarket board: proof of the living hub (5 Nov 2026)

The owner's idea: the board game's Newmarket map as the home page of the full game, a pull-out storybook that comes to life. Places are nodes; clicking one swoops the camera down and the building pops up off the page; between steps the camera lifts off and glides to the next place.

Published as the Claude artifact "Newmarket Board" (https://claude.ai/artifact/Y7Zbrq1sr7jjZr7Ui4PP9E). This folder is what it publishes.

- `index.html`: three.js (0.170 from jsDelivr). The board (`img/board.webp`, the 1200 x 900 map from `assets/maps/`) lies on a wooden table; 10 map pixels = 1 world unit.
- Alive: cloud shadows (noise in the board's shader), strings of horses on the gallops, Warren Hill, Bury Road, Old Station Road and the stable yard, loose horses in the paddocks, two horseboxes, chimney smoke, a passing flock. Horses are drawn in code (`drawHorse`), six frames a stride, walk or canter.
- Places (`NODES`): the National Stud (Breed), Tattersalls, the stables (Develop and enter). Hover lifts the piece a little; a visit raises it on a springy hinge and opens the panel; "Next" folds it away and travels to the next place.
- Pop-up pieces: `img/cut-*.png`, cut from the board's own painting inside hand-traced outlines with a cream die-cut edge (`tools/cutouts.py`; outlines in map pixels).
- Limits: the art is only 1200 x 900, so close-ups are soft (Tattersalls especially). The board's print file would fix that.
