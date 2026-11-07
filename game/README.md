# Thoroughbred Ascot: the whole game (6 Nov 2026)

The quick game, the living Newmarket map and the 3D race view, joined into one game. Owner: graphic designer, little
coding. Explain things plainly, in plain British English.

**Live:** https://claude.ai/artifact/DzPTVLUDZwPXjXp9xix512 (the old Ascot game and the living map stay up as they were).

**Branch:** `claude/thoroughbred-game` (from `claude/ascot-game-engine`). The old pieces (`ascot-game/`, `newmarket-live/`)
are untouched and still work on their own; the race view (`race-view/final-furlong.html`) is shared, with its new
game-mode dress (below).

## How it plays

The Newmarket board is home and the map of the season. Each step is a place on it: the next one is lit gold, with a
"Next" tag, a beacon and the spark running round its outline; places not open yet are greyed (their card says when they
open); places finished with get a tick. A guide in the corner always says what to do next ("Show me" opens that place's
card), and the bar's five steps (The Stud, The Sales, Training, Royal Ascot, The Result) can be clicked to find a place.

| Chapter (`phase()` in `js/ui.js`) | Season | Place | What you do |
|---|---|---|---|
| draw | Winter | The Jockey Club | The ten races are dealt onto the Jockey Club's table |
| breed | Spring | National Stud | The mares sale and the matings (`S.step` 1) |
| sales | Autumn | Tattersalls | The live auction (`S.step` 2; once you leave the stud there's no going back) |
| gallops | (later version) | Warren Hill | Training; not used for now |
| entries | May | The Jockey Club | Entries (`S.step` 3), then To the Races |
| week | June | Royal Ascot | Race week: watch each race in 3D or sim it (`S.step` 4) |
| standings | June | Royal Ascot | The final standings (`S.step` 5) |
| home | Summer | Palace House | Your title, every week you've played, the roll of honour; a new season |

Your Stables (your string and the race planner) and Palace House are open all season; the race planner is also a tab at
the Jockey Club, the Stud and Tattersalls.

**Between the steps the story moves on** (`story()` in `js/ui.js`): the sheet closes, a chapter card comes down
("Autumn · Step 2 of 5 · The Yearling Sales"), the journey is inked across the board along the roads from the place just
finished to the next (`trail()` in `src/board.src.js`, routes in `TRAILS`), a little horse trots along it, and when the 3D
life is running a procession goes by on the roads: the yearlings led from the Stud to Tattersalls, your string in your
colours walking out to Warren Hill, the horseboxes away up Fordham Road. Then the next place's card opens.

**The films** (`film()` in `js/ui.js`, files in `video/`):
- `newmarket-arrive.mp4`: the owner's map clip played backwards, from the treetops down onto the board. Its last frame is
  the board itself, so it is laid exactly over the live board as it lands and fades into it (checked: within half a
  pixel). Played on the first arrival of a visit and on the way home from Ascot.
- `ascot-arrive.mp4`: the owner's race clip with "Royal Ascot" over it (with its own sound when Sound is on).
- `cover.mp4`: the cover's loop (the Ascot game's cover video).
- All four share one grade (`tools/grade_map_clip.py` matched the map clip to the board's colours channel by channel;
  `tools/storybook_grade.py` is the "storybook" grade on the Ascot clips: softer colour, greens towards the board's
  olive, a parchment cast, a little grain, a soft vignette). Every film can be skipped.

**Race week** is at Ascot (the board is put away; the sheet sits over a still of the race clip). "Watch in 3D" opens the
race view; "Sim" gives the same result straight away. Entries can still be changed before the first race (the Jockey
Club's entries in an Ascot sheet: "Declarations").

## One look

`css/game.css` on top of the house style (`css/components.css`, the Ascot game's styles). Taken from the board: its
parchment (with a whisper of paper grain), bottle and sage greens, gold for what's lit, chosen or next, ink for the trails,
Crimson Pro (an engraved serif, like the board's own lettering) for titles, Jost in spaced capitals for labels, Nunito
for reading. A place's screens open as a cream sheet over the dimmed board, headed by a window onto that place on the
board, its medal and its name. The cover, the films, the sheets, the race view's panels and its finish all use the same
colours and type.

## The race view's glow-up (game mode only; `race-view/final-furlong.html`)

The race itself (the engine, the timeline, the cameras, the models) is unchanged.
- **The storybook finish**: the clips' grade as a CSS filter on the 3D picture (`saturate(1.15) sepia(.25) hue-rotate(-12deg)
  brightness(.96) contrast(.935)`, fitted in the browser to `storybook_grade.py`), and a soft vignette. Costs almost
  nothing (the browser does it as the picture goes on screen). Controls → Finish: Storybook or Plain 3D (remembered).
  On its own the page is unchanged; `?finish=story` shows the storybook finish there too.
- **The racecard** before the off (race, day, grade, trip, conditions, going, runners, prize; your runner, stall and
  running style) and **the result** after the line (the first four with their silks and margins, your horse's place and
  prize, Watch the replay / Back to the racecard / Next race). In the game the show ends on the set piece after the race,
  with the result up, instead of going round again.
- **Panels in the game's dress** (Crimson Pro, gold hairlines); the controls start tucked away for a clean TV picture
  (the Controls button brings them back); the v1/v2 horse switch is hidden.
- **The course by name**: the view reads `assets/course/<course>.json`, `-view.json`, `-stalls.json`, `-standards.json`
  for the course the game names (its meeting's), `?course=` on its own, Ascot by default.

## Built for more meetings and courses

- **A meeting is data**: `js/meetings/royal-ascot.js` (its course, days, races a day, the race pool with grades, distances,
  ages and sexes, the grades' rating bands and prizes, field sizes, the goings to draw from, which race in the course's
  view file each trip uses, the titles). Another meeting is another file of the same shape; set `window.MEETING_ID`
  before `js/rules.js` loads to play it. The saves are kept per meeting (`tb-game-<meeting>`, `tb-<meeting>-history` …).
- **The rules have no screens in them**: `js/rules.js` (breeding, the mares sale, the Tattersalls catalogue and the rival
  buyers, the card drawn from a seed, eligibility and race-day ratings, fields for the race engine, race running and
  results, save and load). Checked identical to the Ascot game's for ten seeds (cards and foals). The long game or
  another engine can take it as it is.
- **The opposition is random** and drawn in one place (`makeCard` → each race's `opp`, `fieldFor`): real horses from real
  races can be slotted in there later.
- **Still Ascot-specific**: the race view's scenery (the stand, the dressing, the bake) is Ascot's and is loaded by name in
  `final-furlong.html`; a new course needs its scenery listed in its view file, its course files built by
  `tools/course/`, and its stand assembled from the stand kit.

## Prices (owner, 6 Nov: apply the proposed change)

Blue-blooded mares £50,000 → **£95,000**; the rivals' heat for Book 1 1.45 → **1.3**, Book 2 1.15 → **1.1** (`PILES`,
`BOOK_HEAT` in `js/rules.js`). Average cost by peak rating (60 cards, `tools/cost-by-rating.js`):

| Peak rating | Bred, before → now | Bought, before → now |
|---|---|---|
| 100–109 | £140k → £151k | £207k → £192k |
| 110–119 | £186k → £217k | £307k → £281k |
| 120+ | £213k → £256k | £418k → £367k |

Strategy harness (30 seeded seasons each, `tools/harness.js`), average prize money, before → now: Breeder £239k → £210k;
Buyer £25k → £50k; Balanced £148k → £141k; Cheap and wide £39k → £55k; All-in on quality £165k → £183k; Card-aware planner
£259k → £294k. Breeding is still the cheaper way to a top horse, but buying is now a real option.

## Owner's polish round (6 Nov, after a full play on phone and Mac)

- **The map is calm.** It always fills the window (full bleed) and never pulls back past its edges. Picking a place
  glides it a little towards it with the slightest zoom (`cameraFor()`, `ZOOM` in `src/board.src.js`); moving on eases
  back to the whole board, glides towards the next place and gives it a gentle pulse. No tilt. Only the next place
  moves (its glow and ring, slowly); the others sit still. The inked footsteps and the little horse are gone.
- **One box at a time.** No separate chapter box (its words are on the guide and on the place's card); the guide
  steps aside while a card is open; cards and sheets fade in rather than grow.
- **No training step for now.** Warren Hill shows "Coming in a later version" (`CHAPTERS.gallops` and the gallops
  sheet are kept for then). After Tattersalls you go straight to entries at the Jockey Club; 2-year-olds are developed
  at the foal reveal or on the entries screen. The bar's step 3 is "Entries".
- **The race film leads into race day.** "Go to Royal Ascot" plays the Ascot film at once (in the same tap, so it has
  its sound), straight into race week. The film of the board leaving is gone.
- **The race view's dock** (game mode): every runner in the owner's own graphic silks (`img/silks`), with its price
  and its race-day colour card as a band along the foot of its chip (black, red, yellow, blue, as in the board game;
  `marketFor()` in `js/rules.js`: the figure is rating, less 5 a step off its trip, plus or minus the going; a horse 5
  better is about twice as likely; a bookmaker's margin; the usual ladder of odds). Your price and card on the
  racecard too. The racecard sits above the controls when they're showing.
- **Lighter on a Mac:** a fourth quality level, Lightest, that Auto can drop to, and Auto judges every 1.25 s.
- **Phones ("lite", set in the page's head on touch screens):** no blurred glows; the board at 30 frames a second and
  off under a sheet; the foal card without its SVG filters; the board's horses on 512-pixel textures.
- Still to do: the crowd and the race graphics (owner wants another pass), the race view's smoothness on the owner's Mac.

## Checked by a second pair of eyes (6 Nov)

An independent read of the shell found no runtime errors and eight flow bugs, all fixed and re-tested:
- a fresh season from the cover now closes whatever was open (it used to leave race week open on the new season);
- leaving the page while changing entries at Ascot brings you back to race week, not to Newmarket;
- no developing horses once you're at Ascot;
- an auction win is yours (and saved) the moment the hammer falls; leave the page mid-auction and that lot has gone
  through the ring without you;
- the draw can't run twice; the stud's confirm is off while a mare or foal is waiting;
- you can always leave Tattersalls, even with no horse (no dead end);
- the race view's "didn't load" note goes if the view turns up late.

## Files

| File | What it is |
|---|---|
| `index.html` | The page (built from `src/index.src.html`). |
| `js/meetings/royal-ascot.js` | The meeting, as data. |
| `js/rules.js` | The rules and the state (no screens). |
| `js/board.js` | The Newmarket board (built from `src/board.src.js`: places, cards, states, trails, the day, mist, smoke, lamps, clouds, banners with your own colours on the last one, the sounds). `window.BOARD`. |
| `js/life.js` | The 3D life on the board (built from `src/life.src.js`; three.js). `window.LIFE.procession(kind)`. `?nolife=1` leaves it out. |
| `js/ui-parts.js` | The screens' pieces, from the Ascot game: stallion and mare cards, mares sale, sale ring and live auction, horse cards, planner, entries, race week, final standings, the animated horse card, the race view's frame. |
| `js/ui.js` | The shell: chapters, place states and cards, the guide, sheets, the story, films, the cover, clicks, start-up. |
| `css/components.css`, `css/game.css` | The house style and components; the game's look and the shell. |
| `card.html` | The animated horse card (from the Ascot game). |
| `img/` | Portraits, silks, card base, the sale ring, the cover still, the Ascot still. |
| `video/` | The four films. |
| `assets/newmarket/` | The board and what the board needs (occlusion, chimneys and windows, banners, silks for the banners). |
| `src/` | Sources for the built files, plus `sites.json` (the places' outlines), `icons.json` (game-icons.net, CC BY 3.0) and the horse mark. |
| `tools/build.py` | Builds `index.html`, `js/board.js` and `js/life.js` from `src/`. Run after changing anything in `src/`. |
| `tools/stage.py` | Gathers everything the published game needs (250 files, about 35 MB) into one folder, escaping non-ASCII characters. |
| `tools/grade_map_clip.py`, `tools/storybook_grade.py` | The films' grades. |
| `tools/harness.js`, `tools/cost-by-rating.js` | Balance checks (load into the page). |

## Publishing

`python3 game/tools/stage.py <dir>`, then publish `<dir>/index.html` as the artifact with every other file in the folder
as its `files` (one publish takes 255 files and 64 MB; this is 241 files and 35 MB). To update, republish to the same URL.

## Checking

Serve the staged folder (`python3 -m http.server`) and play it in a browser. On a machine without a graphics chip, add
`?nolife=1` (the 3D life on the board is very slow in software rendering, though fine on a real graphics chip). In the
console: `__setHour(19)` sets the time of day on the board; `LIFE.__advance(10)` moves a procession on 10 seconds.

## 7 Nov 2026: the new look and a faster race view in the game (version 6)

**Branch now `claude/race-look-options`** (it sits on top of `claude/thoroughbred-game`; nothing to merge back the other
way). Published as version 6 of the live game.

- **The race view carries the finish study's look**: the dressed terraced stand (pastel doors and balusters, striped
  awnings, flags), the skittle crowd with about half the gents in black tops and tails, crisp mown lanes, beige ground
  beside the track, the Ascot rail, soft warm light. The leafy trees stay (owner preferred them to the clay ones).
- **The finish camera holds on the winning line** once the winner is past the post, so the placings are seen crossing.
- **No time of year** on the labels (the chapters' seasons are no longer shown).
- **Garbled text fixed at the source**: the published scripts carry no charset, so a Mac read "·" and "⚥" as
  "Â·" and "âš¥". `tools/stage.py` now writes every non-ASCII character as an escape.
- **Faster on every machine** (details: `claude/race-view-performance.md`): the storybook grade is drawn in the shaders
  instead of a CSS filter (same colours); while a race plays the game hides everything under it and the board's loop
  rests (`body.watching`); ground and sky painted once; no multisampling on Low and Lightest; Auto remembers its level
  per browser and drops under 40 fps; a light horse for horses small on screen; shaders compiled before the off.
- **Diagnostics**: press **D** during a race (or open the game as `…#debug`): frame rate, draw calls, triangles,
  pixel ratio, picture size, edges, shadows, script time by part, memory, the graphics chip's name.
- `tools/stage.py` now gathers 250 files, 35 MB (adds `looks.js`, `stand-styles.js`, the skittle crowd, the turf grain
  and the light horse; leaves out the clay trees).
