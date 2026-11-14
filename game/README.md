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

## Two ways to play: today's card and the random game (13 Nov 2026, branch `claude/daily-card`)

Owner, 13 Nov: "having the daily mix or just a play a random game option is best". The cover's buttons (`paintMenu()` in
`js/ui.js`) are now **Play today's card** and **Play a random game**; once a random game is under way, **Random game**
(continue) and **New random game**.

- **Today's card** is one race card a day (the same ten races, going and fields for everyone), changing at midnight UK time (`ukDay()`). Its season number
  is made from the date and the season (`dailySeed(day)` in `js/rules.js`; Royal Ascot and Newmarket each have their own),
  kept above 1,000,000 so it can never be a random game's number (those are 1 to 1,000,000).
- **One go.** A day's card can't be restarted, and the first time it is finished its result is written to
  `tb-<season>-daily-log` (`noteDaily()`) and never overwritten. After that the cover's button shows the result and
  opens the final standings. An unfinished card from an earlier day is put away when today's is started.
- **Two saved games a season**, so starting one never loses the other: the random game in `tb-game-<season>` (as before,
  so players' saves carry over) and the daily card in `tb-game-<season>-daily` (`slotKey()`, `load(mode)`); the one last
  played is in `tb-<season>-mode`. `S.mode` is "daily" or "random", `S.day` the card's day.
- **Two numbers make a game** (`js/rules.js`). The season's number (`S.seed`) is the race card: the ten races, the
  going, the fields. That is what today's card shares. The game's own luck (`S.luck`, drawn afresh for every game and
  every player) is the breeding and buying: the mares a pile turns over, a foal, the Tattersalls catalogue, how far
  each rival will go for a lot, what an unproven stallion is really worth. Owner, 13 Nov: "the mares and foals etc
  shouldn't be pre fixed. it should work fresh for each player". Each roll comes from `luck(key)` (the game's luck plus
  what is being rolled for), not `Math.random`, so within one game a roll can't be taken again by reloading. Still
  left to the moment: how long a rival hesitates before a bid, and the board's moving life.
- The screens call a season by `seasonName()`: "Daily card, Fri 13 Nov" or "Season 123456".
- **Not built yet:** the leaderboard (stable names, scores kept on Cloudflare) and score checking. `noteDaily()` is where a
  finished daily card would be sent from.

## Your colours: every player makes their own (13 Nov 2026, branch `claude/own-colours`)

Owner, 13 Nov: "let's make all new players make their own colours.. and let's also remember their colours? no selection
from the initial suite". The cover no longer offers the 54 ready-made silks to choose from (they are the opposition's).

- **The maker** (`js/colours.js`, `openColours()`): three tabs (Jacket, Sleeves, Cap), each with a colour, a second colour
  and a pattern; a big picture with its description in racing's words; "Surprise me". A player with no colours yet is
  brought to it before their first game (`needColours()` on the cover's play buttons), then carries on into the game.
- **The templates and the palette** are in `race-view/silks-paint.js` (staged to the site's top folder and loaded by both
  the game and the race view): the owner's 25 jackets, 12 sleeves and 10 caps, then the extra patterns (sash, halved,
  inverted chevron, panel, three spots; cuffs; halved, four spots, peak), and twelve colours read from his 54 silks
  graphics (the ten most used, plus green and orange). Its pattern rules are `tools/silks/make_silks.py`'s line for line
  (checked: all 56 patterns give identical masks), so **a pattern changed in one must be changed in the other**.
- **Remembered** in the browser under `tb-colours` (one set for every game and both seasons): `setColours()`, `MY`,
  `hasColours()` in `js/rules.js`. `mySilkN()` is `MINE` (-1) once a player has colours; `silkImg(MINE)` is their picture.
  `SilksPaint.encode()` gives a short text for a set (e.g. `j5.1.4-s6.0.5-c6.4.1`), kept with a finished daily card for
  the leaderboard to show.
- **The menu picture** is drawn in the owner's diagram layout (`SilksPaint.icon()`: the strip on the left the sleeves,
  the half circle at the top the cap, the rest the body), so it sits beside the 54 in the racecards and results.
- **In 3D**: the race view is sent the colours' description (`silkSpec` on your runner) and `race-view/horse-v2.js`
  paints the jockey's texture from it (`SilksPaint.texture(spec, 1024, "v2")`); the board's string of horses
  (`js/life.js`, the v1 layout) and your banner on the road to the races (`flyOwn()` in `src/board.src.js`) take them too.

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

## 7 Nov 2026: the new look and a faster race view in the game (version 7)

**Branch now `claude/race-look-options`** (it sits on top of `claude/thoroughbred-game`; nothing to merge back the other
way). Published as version 7 of the live game.

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

## 7 Nov 2026 (afternoon): the owner's phone playtest

**Branch `claude/playtest-fixes`**, from `main`; merged into `main` for the live site (Cloudflare).

- **Phones**: the game page had no doctype, charset or viewport, so on the live site a phone drew the desktop layout
  shrunk down, in quirks mode (the programme in five tiny columns, the draw's deck over the cards, the toast over the
  stud's footer). `src/index.src.html` now starts with them. The draw's deck has its own space at the foot of the table;
  the toast sits above an open sheet's footer (`--foot-h`, measured in `ui.js`).
- **The board holds still behind a sheet** (programme, stud, sales...): no ticking map underneath (`board.src.js`,
  `life.src.js`).
- **The race view's Look and Stand menus are out of the game** (switching reloaded the view and stuck on the loading
  screen; the game also re-sends the race whenever the view says it's ready). They live on the style review page.
- **The crowd's hats**: far-off figures no longer simplified into black cones.
- **The 2m4f (Gold Cup) starts on the straight course**, 1334 m out, runs past the stand and once round
  (`tools/course/place_stalls.py` `onStraight`; the engine meets no bend until the post; the view's `railAt`).
- **Cameras**: tracking shots frame the horses within about 8 lengths of the leader (less on a phone held upright),
  so a strung-out field no longer pulls them wide on the bends; a new **drone** camera over the turf down the round
  mile's chute (its tracking car was in the hedge) and just past the post (the look-back camera had the field behind
  the carnival's terraces); the grandstand camera only from 600 m out on the round course (before that the carnival
  hides the home bend); a gentle steady zoom out over the last 220 m.
- **Before the off**: a low drone glides along the stand while each runner is announced (number, colours, name, price),
  with Skip; then the racecard. **Commentary**: a line at a time, written from the engine's events and the timeline.
- **Course**: a paler cut strip across the track at the winning line, fainter ones at each furlong of the straight;
  the far (carnival) rail at the finish filled with crowd.
- **Style review page** (`race-view/styles.html`, live at `/styles.html`): every look, stand and tree style side by
  side with pictures (`race-view/assets/styles/`), each opening the real race in that style, plus mix and match. The
  owner picks one of each; then the game is set to those and the others removed.

### 7 Nov (later): the owner's choices and second round of notes

**Branch `claude/playtest-fixes-2`**, merged into `main`.

- **Chosen style:** today's leafy trees and today's stand, with a **fresher light** between the storybook grade and
  the "model maker" look: the grade is now saturate 1.02, sepia .07, hue -5, brightness 1.04, contrast .95 (was 1.15,
  .25, -12, .96, .935), the sun less orange, the sky's horizon less peach (`FRESH` in the race view; `?grade=`,
  `?suncol=`, `?skyh=` try others). The style review page is no longer published (still in the repo).
- **Smooth clay stand**: the baked light maps (stand, site pieces, finish) smoothed island by island and their gutters
  filled (`tools/course/smooth_lightmaps.py`, untouched bakes in `race-view/assets/baked/raw/`): no grain, blotches,
  brick-like banding or flicker.
- **Trees**: the belts get an understorey (each belt tree's light crown squashed low under it), so no sky between the
  hedge and the crowns.
- **Home bend**: the carnival path no longer runs across the turf in the baked ground (`tools/course/fix_ground_path.py`).
- **Finish camera on a phone held upright**: zoom ranges open up on narrow screens and the grandstand camera keeps just
  the leaders, so the winner is seen crossing the line.
- **Before the off**: one card of the whole field (stall, colours, name, price; your runner picked out) over a still
  aerial from behind the carnival across the track to the stand, with "To the start" (it goes by itself after 7 s plus
  0.6 s a runner). The race view's own races get names and prices too.

## 7 Nov 2026 (evening): the owner's run-through list

**Branch `claude/run-through-fixes`**, from `main`; merged into `main` for the live site.

- **The opening film wobbled.** The map clip (`video/newmarket-arrive.mp4`) had an uneven cadence: every few frames the
  zoom jumped further than the frames either side (measured frame to frame), so the descent juddered. It's now steadied
  (each frame re-warped onto a smoothed camera path, `tools/steady_film.py`, run on the original clip) and
  interpolated to 48 frames a second; its last frame is untouched, so it still lands exactly on the board. In `film()`
  the film's framing now moves only when a new frame of the film is shown (`requestVideoFrameCallback`, with a
  transform), so the picture and its frame move together.
- **The strip at the top on a phone.** On a tall screen the clip's last frame doesn't reach the board's top and bottom
  edges (about 24 px each), and the film covered the top bar, which then appeared as a dark band that "loaded later".
  A film that lands on the board now plays under the top bar (`.cine.under-bar`), the board shows through wherever the
  film doesn't reach (instead of the dark backing), and the drifting clouds along the top fade in after the film
  (`body.filming #wisps`) rather than popping in.
- **Horseboxes off the roads.** The vans' routes came from hand-placed road lines that ran up to ~15 px off the painted
  roads (onto verges, a front garden, the grass by the Stud's lawn), and keeping left pushed them further. Now
  `tools/snap_van_routes.py` finds the painted road surface on the board and slides each main road's line onto its
  middle (writes `VAN_ROUTES` into `src/life.src.js`; run `tools/build.py` after). The lane from the stables past the
  Jockey Club is a faint track and stays as drawn. Bury Road's end now follows the road off the top of the board.
  Vans keep left by 4 px (was 6). Walkers and the strings still use the hand-placed lines.
- **The crowd** in the race view is calmed right down (owner: keep it minimal so the figures draw less attention): no
  hopping on the toes, a barely-there sway, a slow lean in as the leaders pass, and only a few hats lifted, slowly.
- **Coming from the back**: see `race-engine/README.md` (7 Nov): held-up horses wait longer and finish stronger, and
  leaders who kick for home can empty before the post.
- **Prices against the colour cards** (owner: reds shouldn't be 20/1). The card comes from the race-day figure against
  the race's bands (rating, less 5 a step off its trip, plus or minus the going, so the ground does count); the price
  came from the horse's chance in the whole field, so a red in a strong field could be 20/1. `marketFor()` in
  `js/rules.js` now keeps every price inside its card's range (`CARD_ODDS`): black about evens to 4/1 (odds-on only
  for a strong favourite), red 5/1 to 10/1, yellow 11/1 to 20/1, blue 25/1 and longer. The horses on one card are
  spread across its range in the order of their chances.
- **The v2 horse and jockey are now the race view's horse** (owner: the boots matched the horse and the shoulder patch
  was back; "I thought we developed a better horse/jockey model"). The game had still been showing v1, whose colours
  were painted through a texture mask that leaks. v2 (`race-view/horse-v2.js`) has black boots and no leaks;
  `?horse=v1` brings back the old one. `tools/stage.py` now ships `assets/model-v2/` and `assets/silks-3d-v2/`
  (about 5.4 MB more). On Low and Lightest more of the field uses v2's light horse.
- **Trackside boards** stand 0.8 m higher on longer legs, so "Thoroughbred" reads over the rail; the understorey
  behind them (the fill between the hedge and the trees) is no longer one flat green but a mix of dark greens round the
  hedge's own colour.

## The Race Lab (9 Nov 2026): `lab.html`

A bench for testing and fine-tuning the race engine, linked from the foot of the cover ("Race Lab · test the race
engine") and at `/lab.html`. It runs the game's own engine (`assets/engine/engine.js`) on the game's Ascot course files.

- **Set up**: any mix of the 11 Ascot courses and distances and the 5 goings; level races or handicaps (marks); a list of
  horses with every racecard field (rating, mark, running style, flexibility, temperament, best trip, goings it likes,
  jockey level, riding instruction, colours), filled up with random opponents to a field size and rating range if wanted;
  random draw or as listed. "Horses from my game" brings in the stable from the saved game on that device.
- **Compare**: the starred horses run every riding instruction, running style, temperament, flexibility, jockey level or a
  range of ratings. Race r of every combination uses the same seed, opponents and draw, so settings are compared on
  identical races.
- **Engine numbers**: about 20 of `settings.json`'s numbers in plain words (ground, trip, form, pace levels and what makes
  them, run-of-the-race boost, final sprint, kick point, missing the break, slipstream, traffic). Tuned for the lab only;
  each test keeps its numbers and a short "rules version" code (a fingerprint of the settings it ran with).
- **Results**: headline figures (top-rated wins, lowest-rated wins, pace mix, margins, time against par, missed breaks,
  traffic), a break-down table (any two of 20 ways to split: horse, compared setting, course & distance, going, pace,
  style, ridden as, ground points, trip steps, draw third, rating rank, form on the day …; win %, wins against a fair share,
  top 3 %, average place, lengths behind, traffic), and every race with its full result and events or **Watch in 3D**.
- **Records**: every test kept in the browser (IndexedDB `tb-race-lab`), side-by-side comparison, and spreadsheets (CSV,
  one row per runner per race with every figure; or of every test at once). "Copy summary" gives a text summary to paste.

Files: `lab.html`, `css/lab.css`, `js/lab.js` (the page), `js/lab-worker.js` (runs the races in the background, several at
once). Races are rebuilt from the test's seed when needed, so only the figures are stored. The race view takes two new
optional fields from whoever opens it: `handicap` and `settings` (the lab's tuned numbers), so a lab race watched in 3D is
exactly the race tested (checked: the view's order matched the lab's for level and handicap races, tuned and not).

## Two seasons: Royal Ascot or Newmarket (10 Nov 2026)

The cover now offers two seasons (owner, 10 Nov). Both are 10 races and share everything before the racing (the draw,
the National Stud, Tattersalls, entries at the Jockey Club, the 3D race view):

| | Royal Ascot (`js/meetings/royal-ascot.js`) | Newmarket (`js/meetings/newmarket.js`) |
|---|---|---|
| Races | 2 a day over 5 days, from the Royal Ascot programme | 2 at each of 5 meetings: Craven (Apr), Guineas (May), July Festival (Jul), Cambridgeshire (Sep), Future Champions (Oct), from the 36-race Newmarket list |
| Courses | Ascot | Rowley Mile and July Course (each race names its course) |
| Runs per horse | Once | Once per meeting, at every meeting it qualifies for (`runsPerMeeting: 1`) |
| Going | One per day | One per meeting |
| Titles | Royal Ascot Champion … Paying Guest | Newmarket Champion, Leading Owner, Classic Force, Newmarket Winner, Heath Walker |
| To the races | The Ascot film | No film: the racecourse is on the board; race days sit over a Rowley Mile still (`img/newmarket-still.jpg`) |

- **Choosing**: the switch at the top of the cover; the choice is remembered (`localStorage` `tb-season`) and
  `?season=newmarket` or `?season=royal-ascot` opens one. Switching reloads the page into the other season.
- **Each season is its own game**: its own save (`tb-game-<id>`), history, best week/season, roll of honour and titles,
  so the leaderboard (still to come, with Firebase) will be one table per season.
- **The words** each season uses on screen are in its meeting file (`words`); the rules read courses per race
  (`courseOf`, `courseFile`, `viewKey`, `onStraight` in `js/rules.js`) and the clash rule (`clashes`, `clashFor`). The page
  loads the engine data for every course the season races on (`ENGINE.courses`).
- **Checked**: Royal Ascot plays exactly as before (same cards, results and wording); Newmarket seasons played through by
  the strategy harness and in the browser (a horse runs at up to every meeting, never twice at one; the 3D view's result
  matches the sim on the Rowley Mile).
- `js/meetings/newmarket-season.js` is the 8 Nov draft (all 36 races over the whole season), kept for the long game.
- The Race Lab now tests all three courses (Ascot, Rowley Mile, July Course).

## Your team: owner, trainer and jockey cards (10 Nov 2026, first go, branch `claude/team-draft`)

Owner, 10 Nov: "integrate owner, jockey and trainers into your team, which you draft at the start ... a draft from
bronze, silver, gold decks of each type, 6 points (gold is 3, bronze is 1); they have different skills that give you
advantages." The cards are the board game's 60 (the Thoroughbred site's CMS collection `TeamCards`), turned into the
digital game's terms where the board's rules can't work as they are.

**The draft** (at the Jockey Club, straight after the ten races are dealt; `phase()` "team"): pick a deck (Owner,
Trainer or Jockey; Gold, Silver or Bronze), three of its cards are turned over and you keep one, as at the mares sale.
Exactly 6 points (Gold 3, Silver 2, Bronze 1), at least one card of each kind (the board's rule). A deck is greyed out
when it would leave too few points for a kind you haven't got. Race-distance trainer cards only turn up if one of the
ten races is at their trips (the board's "take another card"). Then "To the National Stud".

| Kind | Bronze | Silver | Gold | Where it works |
|---|---|---|---|---|
| Powerhouse | +£150k budget | +£300k | +£450k | at once |
| Elite Mares | see 3 mares a draw at the mares sale (everyone else 2) | 4 | 5 | the stud |
| Stallion Owner | three 3★ stallions drawn, keep one: 2 free nominations | 4★ | 5★ | the stud |
| Pedigree Expert | the true stars of 2 unproven stallions you ask about | 4 | all | the stud and the sales |
| Sales Scout (was Trade Terms) | brief him for 2 of your races: lots marked by how well they suit them, the rest greyed; 1 bargain of his own (Book 2 or 3, its yearling good enough to win one of them if possible) | 3 races, 2 bargains | 4 races, 4 bargains | Tattersalls |
| Bloodstock Agent | each lot's projected peak, a 30-point range with the truth inside | 20 points | 10 points | Tattersalls |
| Vet's Report | send a yearling back once you've seen it: once, 80% back | twice, 90% | three times, 100% | Tattersalls |
| Private Sale | one Book 3 lot before the ring, at the middle of its guide | Books 2–3 | any Book | Tattersalls |
| Trainer (8 specialists) | the board's cards: a step on the trip or +3 (whichever helps that race), 2 horses | a step and +3, 3 horses | a step and +5, 3 horses | entries; only in races at their trips / ages / sire lines |
| Master Trainer | a step or +3, 2 horses, any race | a step or +3, 3 horses | a step and +3, 3 horses | entries |
| Stable Form | +3 on 2 horses | +3 on 4 horses | +2 on every horse | entries |
| Champion Jockey | best of two runs on the day | best of two, never a stinker | best of three, never a stinker | the races he's booked for: 3 / 4 / 5 |
| Tempo Setter | more energy left when ridden in front or prominent | more | more | 3 / 4 / 5 races |
| Late Closer | stronger finish when ridden midfield or held up | stronger | stronger | 3 / 4 / 5 races |
| Race Reader | a better-judged ride whatever the style, finds gaps | better | better | 3 / 4 / 5 races |

Where the digital game differs from the board, and why:
- **Trainer cards reach more horses** (2 / 3 / 3, Stable Form 2 / 4 / all) because the board's one horse for three
  races becomes ten races here, where a horse runs once (at Ascot). Stable Form III is +2 on every horse, not +3: at +3
  it was worth about twice any other card (see below).
- **Owner cards, second round (owner, 10 Nov)**: each pushes you to breeding or the sales, and none pays income ("too
  computer sim luck based"): Stud Master and Auction Insider are gone. The mares sale turns over 2 mares for everyone.
  Each lot's yearling is settled (seeded) when the catalogue is made (`fs` on the lot), so the agent's projection is of
  the real yearling.
- **Jockey cards** become riding skills in the race engine (new optional runner fields in `race-engine/engine.js`:
  `formBest`, `noFlop`, `paceTank`, `lateKick`, `reader`; a runner without them races exactly as before, checked
  440 of 440 races identical, `race-engine/check/team-same.mjs`). A booked jockey also has skill 3 / 4 / 5 (the
  engine's 1–5; your yard's own jockey is random, as before). What each is worth, measured against rating points
  (`race-engine/check/team-jockeys.mjs`, a horse 2 below the best in 14, 500 races each): +1 rating ≈ 15→19% wins,
  +3 ≈ 27%, +5 ≈ 41%; Champion II ≈ +2, III ≈ +3; Tempo Setter ≈ +1.5 / +2.5 / +3.5 for a front-runner or prominent
  horse; Late Closer ≈ +1.5 / +2.5 / +3.5 for a midfield or hold-up horse; Race Reader ≈ +1 / +1.5 / +2.5 for any.
  Jockey skill alone (1 to 5) barely matters (14.6% → 16.4%), so the skills carry the cards.

Files: `js/team.js` (rules, numbers at the top), `js/ui-team.js` (the draft and the cards at each place), styles at
the end of `css/game.css`. Save version 7 (`migrate7`: a season already past the draw goes on without a team).
`tools/team-harness.js`: whole seasons with a team, played as a sensible player would use the cards (load
`harness.html`-style: the rules, team.js, ui-team.js and the engine, without the board).

### What the team is worth (team harness, 10 Nov)

Whole Royal Ascot weeks with the real breeding, sale, rival buyers and race engine, cards used as a sensible player
would (`tools/team-harness.js`). Prize money per week against the same seasons with no team; ± is the standard error.

**Full six-point teams** (20 seasons each). Planner (the best of the old strategies) averages £310k without a team:

| Team | Planner | Breeder | Buyer |
|---|---|---|---|
| Stud Master III, Stable Form II, Champion I | **+£238k** | +£206k | +£115k |
| Auction Insider III, Stable Form II, Race Reader I | +£215k | +£170k | **+£168k** |
| Elite Mares II, Black Type I, Master Trainer II, Champion I | +£190k | +£129k | +£46k |
| Powerhouse I, Stable Form III, Champion II | +£173k | +£76k | +£39k |
| Powerhouse II, Stable Form II, Champion II (all silver) | +£174k | +£82k | +£51k |
| Two jockeys (Powerhouse II, Stable Form I, Champion II, Late Closer I) | +£170k | +£59k | +£43k |
| All bronze (six Bronze cards) | +£167k | +£122k | +£65k |
| Powerhouse III, Stable Form II, Champion I | +£165k | +£87k | +£43k |
| Powerhouse I, Stable Form I, Champion III, Race Reader I | +£162k | +£87k | +£37k |
| Elite Mares III, Master Trainer II, Tempo Setter I | +£151k | +£132k | +£29k |
| Bloodstock Agent I, Miler Specialist III, Tempo Setter II | +£124k | +£54k | +£14k |
| Auction Insider II, Miler Specialist II, Late Closer II | +£115k | +£83k | +£128k |

**Single cards** on the Planner (12 seasons each, about ±£10–35k): Auction Insider III +£155k, Stud Master III +£146k,
Tempo Setter II/III +£93k, Stable Form II/III +£83k, Black Type III +£79k, Race Reader III +£79k, Master Trainer III
+£77k, Champion III +£74k; most trainer specialists +£20–95k depending on how many races suit them; Powerhouse only
+£13k / +£31k / +£29k; Staying Specialist +£8–25k; Bloodstock Agent about −£5k (handing a yearling back rarely pays).

### Owner cards, second round, and the starting budget (10 Nov)

Single owner cards on the Planner and Breeder strategies (12 seasons each, ± about £20–50k, so rough), and the same
seasons with no card, at three starting budgets. The simulated players now put spare money into bidding harder.

| Starting budget | No team (Planner) | Gold Powerhouse | Gold Stallion Owner |
|---|---|---|---|
| £1.0m | £146k, about 6 horses | +£153k | +£85–104k |
| £1.25m | £224k, 7–8 horses | +£86–97k | +£48–53k |
| £1.5m | £276k, 8–9 horses | +£31–57k (Bronze +£15k, Silver +£36k) | +£7–26k (Silver +£43k) |
| £1.75m (now) | £308k, 10–12 horses | +£8–63k | about nothing |

At £1.5m: Private Sale III +£35k, Bloodstock Agent III +£26k, Elite Mares III +£13k, Pedigree Expert III +£10k (about
+£130k for a breeder at £1.75m, where it steers him to stallions better than their stars), Trade Terms III and Vet's
Report III about nothing. Money only matters when it is short: at £1.75m any card that gives or saves money adds little.

### Owner cards at £1.25m, the Sales Scout and your accounts (11 Nov)

Owner, 11 Nov: keep the budget and the prize money as separate pots, but make the money tighter so every decision is
weighed up; the other auction card should be about "refining the books" (the races you still need horses for, what
won't be useful, special lots primed for your races); keep the Vet's Report as cash back for a dud; track where the
money goes, with thresholds.

- **Starting budget £1.25m** (`START_BUDGET`, was £1.75m): about 7–11 horses instead of 10–12.
- **Sales Scout** replaces Trade Terms (`O{t}-trade` in an old save reads as the scout). Brief him for 2 / 3 / 4 races
  (the race chips say which you already have a runner for). Each lot then shows the races it suits: the share of the
  yearlings its pedigree could give (sampled with the breeding engine, by the stars the catalogue shows) that would
  reach the race's third band (a fair chance of a place) at an age the race allows; 50%+ "Suits", 25–50% "(maybe)",
  none "Not for your races" (greyed). The Books put his finds first, then the best-suited lots. Briefing him adds 1 /
  2 / 4 **bargains**: Book 2 or 3 pedigrees that suit one of the races, whose yearling (seeded, like every lot) is good
  enough to win it (its second band) if one can be found, else to place.
- **Your accounts** (`js/accounts.js`): the money in the top bar or the footer opens what has gone on mares, stud fees
  and yearlings (and come back from the vet), and a list of what the rest still buys: 5★ / 4★ / 3★ nominations, a
  Blue-blooded or Useful mare, the cheapest lot in each Book. A payment that takes you under one of those says so
  ("Down to £50,000: a 3★ nomination, a Blue-blooded mare and a Book 1 yearling are out of reach now"); at the sales
  only the Books count.

Single owner cards at £1.25m, 40 seasons for each of four strategies (160 per card, about ±£7–13k), against the same
seasons with no card (Planner £219k, Breeder £170k, Balanced £171k, Buyer £57k):

| Card | Bronze | Silver | Gold | Who it helps most |
|---|---|---|---|---|
| Stallion Owner | +£40k | +£45k | +£72k | breeders (Gold +£115k) |
| Powerhouse | +£35k | +£49k | +£67k | the Planner (Gold +£122k) |
| Sales Scout | +£6k | +£37k | +£45k | buyers (Gold +£128k) |
| Private Sale | −£6k | +£2k | +£39k | buyers (Gold +£64k) |
| Pedigree Expert | +£35k | +£37k | +£36k | breeders (+£120k at every tier) |
| Bloodstock Agent | +£24k | +£24k | +£22k | buyers (+£60–70k) |
| Elite Mares | +£5k | +£13k | +£10k | breeders (+£30–50k) |
| Vet's Report | −£2k | −£3k | −£3k | nobody |

The Vet's Report sends back about one yearling per use (only those with next to no chance in any race), but the
money comes back when the best lots have gone, so there is nothing better to spend it on: it needs another shape
(see the handover notes). Pedigree Expert is the same at every tier and Bloodstock Agent hardly better on Gold: both
want their tiers spreading. Private Sale I and II and Elite Mares I are weak.

## The race view's sound: the crowd and the horses (12 Nov 2026)

Owner: "add commentary or at least crowd effects"; crowd effects first, spoken commentary later (the text commentary
is already there). `race-view/race-sound.js` plays it; `race-view/assets/sound/sounds.json` holds the files and every
level; `tools/sound/make_race_sounds.py` made the files from scratch (no recordings, so nothing to license: the
crowd's chatter and shouts are hundreds of eSpeak voices at once, the roar is built from vowel shapes, the applause from
hand claps, the hooves are four-beat gallops with the horses' breathing). Any file can be swapped for a real recording
(same name; for a loop keep half a second of the loop either side and give its length in `sounds.json`).

- **The crowd** chatters before the off and hushes a little while they load; cheers as they jump; builds from about
  5½f out; roars them home (louder when the first two are within 2½ lengths); holds the roar at the line, then settles
  and applauds. A long race lifts the crowd as it passes the stands. Heard fully when the camera is near the crowd,
  quieter and muffled from a distant start.
- **The horses**: the stalls clang open; the field's gallop is as loud as the shot looks close (a long lens on far
  horses sounds near, as on TV), panned to their side, quicker or slower with them, slowed right down in the replay.
- **On and off**: the speaker on the race view's plate. In the game it follows the game's Sound button (and changing it
  in the race changes the game's). The board's own sounds rest while a race is on (`BOARD.Sound.hush`), and the race
  view borrows the game's sound (`BOARD.Sound.ctx()`), so phones that only allow sound after a tap still play it; if a
  browser holds it back, the speaker pulses and the first tap lets it out. On the race view's own page: remembered.
- Checking aid: `window.__sound()` gives what it's doing (excitement, how near the crowd and horses are, each level).

### 13 Nov 2026: the owner's recordings

Owner, after hearing the made sounds: "you can't hear the crowd; the gates are a pop rather than a crash". He sent
recordings (`tools/sound/sources/`, with a note on their licences); `tools/sound/mix_real_sounds.py` cuts and mixes
them. **The off:** the Cheltenham roar, timed so its "they're off" comes just as the stalls crash open (the real latches
and doors from a stalls recording on a heavy clang of steel doors), at full strength wherever the start is. **The crowd**
waits (real crowds, softened and distant), stirs (Aintree) and roars (the Japan Cup with the Grand National finish), then
surges at the line into applause. **The gallop** is the recording doubled up into a field, under the crowd now. **The
course commentary** comes over the loudspeakers from across the course, calm then the finish: a made voice (eSpeak, the
only one available) through horn speakers and echo, so the rise and fall comes through but not the words; a real
commentary recording can replace it (see the script). A whole-race listening preview can be rendered offline the same
way the race view mixes it.

### 13 Nov 2026 (later): the sound in sections

Owner: the off as one sound (his recipe: the stalls opening, 1–2.5 s of the stalls recording, laid into the Cheltenham
roar, "and they're off" brought out); then "a flexible looping middle section … from the off till the 3f stage or so:
a slightly more muted crowd, galloping and background PA announcer"; then "the finish sound effect where the crowd get
much more animated as does the background PA, leading to the cheer as they cross the line". So: `middle.mp3` (a loop)
fades in just after the off; `finish.mp3` (one sound, 51 s) is started so its line (37 s in) comes as the leader
crosses it, about 3f out, the middle fading out under it; it is kept in step with the race clock (a slow computer draws
the race slower than real time). The crowd waiting comes back after the race; a long race passing the stands lifts the
crowd; the gallop loop adds the horses up close and in the replay. The excitement-driven crowd layers and the separate
commentary loops are gone.

### 13 Nov 2026 (evening): the real commentators

Owner: "the commentary isn't great [the made voice]. Some of these clips have crowd and commentary which I'm happy for
you to overlay to get the sound." The made voice is gone: the middle is now the Cheltenham commentator after the roar
and the Aintree clip with its announcer, muted, with the gallop; the finish brings in the Grand National finish (crowd
and commentary) from about 3f out, opening up and rising to the line over the Japan Cup's roar. Each clip's voices are
brought forward a little out of its crowd (`lift_voice` in `tools/sound/mix_real_sounds.py`).

### 14 Nov 2026: the three finishes lined up

Owner gave where each crowd's horses cross the line: the Grand National finish at 22 s, Aintree at 21 s, the Japan Cup at
38 s. The finish now lays all three so their lines land on ours (`LINES` in `tools/sound/mix_real_sounds.py`), their own
build-ups making the crescendo (about 8 dB over the last 20 s, the Japan Cup's surge right on the line), the Grand
National's cheering and commentary carrying on after it into applause. The middle uses Aintree only before its finish
builds, then the Japan Cup crowd early in its race as a breather between the commentators.

Owner, 14 Nov: "I can't really hear any PA announcer … the applause is too prominent, it doesn't sound like a big crowd".
The commentators are now brought forward harder (`TALK_LIFT_DB` 11) and the middle's talk sits above the gallop and the
crowd (the only clearly spoken commentary in the clips is the Cheltenham commentator's few seconds after the roar, and
Aintree's announcer); the applause is some 1,400 pairs of hands, mostly far off down the stands, and much quieter.
