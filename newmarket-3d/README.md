# Newmarket in 3D: the Tattersalls corner

A first slice of the Newmarket board (`assets/maps/newmarket-map.webp`) built as a real 3D place, meant to become
the home hub of the full game. The web page opens **exactly on the painted board**, then flies down into the
3D buildings while the painting dissolves into the model, with horses walking round the rings.

Live: https://claude.ai/artifact/FyhpXzbC7Q3fgCbPqdz6Dw

## How it fits the board
The board is painted as if seen from the south, with heights drawn straight up the page. A world point
(x east, y north, z up, metres) lands on the 2x crop of the board (map x 540-1200, y 420-870 → 1320x900) at

    X = (x + 112) * 5        Y = (48 - y - z) * 5

So the page can show the model through *the board's own projection* (an oblique clip matrix), where every
building sits exactly on its painted self. Flying in blends that matrix into a normal perspective camera.

Every surface carries two things: its own colour (brick, slate…) and a UV into the painting (`proj`), plus a
`pv` mask saying whether the painting shows that face well. While on the board the page shows the painting
everywhere; as it flies down the painting fades out and the model's own materials (with procedural brick and
slate courses and a painterly mottle) take over.

## Files
- `layout.json` – the corner traced off the board: ranges (foot line + depth), the rotunda, houses, rings, lorries.
- `tools/make_ground.py` – builds the ground texture: the board with the painted buildings taken out and filled
  with yard sand, plus the painted trees found as `trees.json`. Also writes `paint.jpg` (the crop at 4x).
- `tools/build_tatts_corner.py` – the Blender build (headless `bpy`): buildings from the kit, trees, rails,
  lorries; exports `build/tatts_corner.glb`; `render 24` with `SHOT=board,ring,yard,low` renders stills.
- `web/index.html` – the live page (three.js 0.170). Pack the model with
  `python3 tools/web/glb_to_web.py newmarket-3d/build/tatts_corner.glb newmarket-3d/web/assets/scene tatts_corner`.
  Horses, silks and crowd figures are copies of the race view's assets.

## Known rough edges
- Close up, the ground still carries the painting's little figures and horses as dark smudges.
- During the first second of a flight the land beyond the board shows as a plain green band.
- Only this corner is modelled; the rest of the board would follow the same recipe (trace, build, pack).
