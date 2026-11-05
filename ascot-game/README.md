# Thoroughbred Ascot: the playable game (handover, updated 5 Nov 2026: the race engine and the 3D race view are in)

The quick management game: breed and buy a stable, enter one horse per race across ten randomly drawn Royal Ascot races, and win as much prize money as you can. It is complete and playable. Owner: graphic designer, little coding. Explain things plainly, in plain British English.

## Where it lives

- **Repo:** `trevorhtfc/thoroughbreddigitalgame`, folder `ascot-game/`, on branch **`claude/ascot-game-engine`** (built on `claude/race-engine-js`, with the game folder from `claude/ascot-game-package`).
- **Play it:** the Claude artifact "Thoroughbred Ascot", https://claude.ai/artifact/NLFcFEnobQTvDuma1G5Cf1 (version 39). It is private to the owner until shared.
- **The files:** the artifact publishes this folder's files (`index.html`, `card.html`, `img/`) plus the 3D race view from `race-view/`: `final-furlong.html`, `horse-v2.js` and `assets/` (the race engine, course data, models, baked scenery and the 54 silks in 3D). `tools/` is for testing only.
- **To carry on in a new chat:** take the files from the repo. Change them, then republish to the same URL: `index.html` as `file_path`, with `root` set to `race-view/` and any changed race-view file in `files` (e.g. `{"final-furlong.html": "final-furlong.html"}`). A publish takes at most 255 files and 64 MB, so a full re-upload goes in batches (the scenery, models, engine and course in one; the three silks folders, only the 54 game silks of each, in another). After a change to `race-engine/`, run `node race-engine/copy-to-view.mjs` and republish `assets/engine/`; after a course change, copy `courses/*.json` to `race-view/assets/course/`.

## Files

| File | What it is |
|---|---|
| `index.html` | The whole game (about 2,900 lines): menu, breeding, mares sale, Tattersalls, planner, race week, final standings. |
| `final-furlong.html` (from `race-view/`) | The 3D race view, opened in an iframe for each race with `?game=1`. It asks the game for the race, runs the race engine on the game's racecards and plays it. Opened on its own, it is still the Final Furlong test page. |
| `assets/` (from `race-view/`) | The race engine (`assets/engine/`), course data (`assets/course/`), models, baked scenery and silks. The game loads the engine and course data from here too. |
| `card.html` | The horse card (reveal, develop and show animations), opened in an iframe. |
| `img/intro.mp4`, `img/intro.webp` | The cover video (trimmed, slowed to 80%, looping) and its poster still. |
| `img/tatts.webp` | The Tattersalls sale ring scene behind the live auction. |
| `img/base.webp` | Card artwork base. |
| `img/p01–p12.webp` | Horse head portraits (360×540, the head starts about 16% down). |
| `img/silks/s01–s54.webp` | The owner's 54 silks, in alphabetical order of the source files, CMYK converted with a colour profile. |

The Newmarket map from the board game is in `assets/maps/newmarket-map.webp` (1200×900, copied from the board game repo's `html/assets/`).

## The game, step by step

`STEP_NAMES = ["Breed", "Tattersalls", "Develop and enter", "Race week", "Result"]`. One way only: you can't go back to breeding once at Tattersalls.

1. **Start:** the menu (cover video, how it works, titles, colour picker). Start deals the ten races as cards. No starting mares (dropped on 1 Nov: a board-game hangover).
2. **Breed:** budget **£1,750,000**. Buy mares at the mares sale: pick a pile (Blue-blooded 4–5★ £50k, Useful 3★ £25k, Moderate 1–2★ £10k), three mares are turned over, keep one (`drawPile`, `keepOffer`). Up to **10 mares**. Pick a mare, then a stallion (fee by the stars players see: 1★ £10k, 2★ £30k, 3★ £75k, 4★ £125k, 5★ £200k). A mare can be at most one star above the stallion's shown stars (`pairProblem`). The foal is final. The stable holds **15 horses**.
3. **Tattersalls:** built on arrival from the mares nobody bred. Three Books by combined stars (Book 1: 7–10, Book 2: 4–6, Book 3: 2–3), 9 lots each. **Each lot draws its own stallion at random** (at most two lots per stallion in a Book), with one sprint and one staying pedigree guaranteed per Book (`newCatalogue`). Reserves by combined stars, £10k to £200k. A live countdown auction against five AI rival buyers (`RIVALS`, `appeal`, `BOOK_HEAT [1.45, 1.15]`). You see the pedigree, not the foal, until it's knocked down to you.
4. **Develop and enter:** foals arrive as 2YOs; develop to 3 or 4 (rating and trip change). Enter one horse per race. The **Race planner** tab shows the ten races as chips across five days; drag a race onto a horse card (or tap) to set a target. Only sex blocks a target: a horse can be targeted for a race it doesn't qualify for yet, since it may develop into it.
5. **Race week:** the going is hidden until now, then declared. Each race shows a **pace forecast** from the runners' running styles (`paceFor`, the engine's `expectedPace`), with a note on whether it suits your horse. Watch it in 3D or sim it: both run the same race. Results show the margin, the winning time and a short race report (the engine's events).
6. **Result:** a final standings animation climbs the title ladder. Titles by prize money: Royal Ascot Champion £1m+, Leading Owner £750k+, Group Race Force £500k+, Royal Ascot Winner £250k+, Paying Guest below. Prize money is a separate pot from the budget; money spent doesn't count.

## The rules come from the board game's code

Breeding and Tattersalls follow the companion app's code in `trevorhtfc/horseracinggame` (owner: "follow the code, not the rule book"): `src/backend/breeding.web.js` (copied as `breedPure`, checked identical over 22,480 foals), `src/pages/Tattersalls.hju2p.js` (lot rules, `lotMatch`, `weightedMare`), `src/backend/tattersalls.web.js` (reserves). Unproven stallions: players see the stud-book stars; the foal is bred from the hidden true rating, one star either way per card. Only the standard-game stallions from the CMS (no expansions).

## Races

- `POOL`: the 35-race 2026 Royal Ascot programme. `drawRaces` takes 2 a day, at least 3 handicaps or conditions races and at least 3 pattern races.
- **No more decks** (owner, 5 Nov: the digital game is its own thing, informed by the board game; "just a simple rating"). Each grade keeps its four rating bands (`GRADE`), used only to draw the opposition and to set the **minimum rating** to run (the lowest band: `needFor`). Prizes as before: Group 1 £300k to win down to Handicap and Conditions £60k. Handicaps still refuse a horse rated over 110 (`HCAP_MAX`); there are **no handicap marks** in this quick game (owner, 5 Nov: handicapping is for the long management game).
- **Race-day rating** (`check`): the age rating, −5 per step off its best trip (more than 3 steps: can't run); in race week the going too, +5 on a going it likes, 0 one off, −5 two, −10 three (`groundPts`, as the engine). Cards show it with **where it ranks in the field** ("2nd of 10 on ratings": gold chip for top-rated, green for 2nd–3rd).
- **The racecard** (`rollRacecard`): every horse has a running style (front-runner, prominent, midfield, hold-up), flexibility (set, adaptable, versatile) and temperament (calm, keen), at random when born or bought (shares as the engine's settings: styles 25% each, flexibility 30/50/20, keen 30%). Shown on the horse cards, the foal reveal and the card dialog. Saves from before get one fixed by the horse's id (save v6).
- AI fields: 6–9 runners (9–11 in handicaps), spread across the bands by race strength (`FIELD_W`). Their racecards come from a separate stream of the seed (`hashStr(seed + race id)`), so everything else on a card is drawn as before; each is bred for the trip (the race is one of its two best distances).
- **The race engine** (`race-engine/engine.js`, loaded as a module from `assets/engine/`): `simRace` runs it in the page (about 50–250 ms a race). `engineRace` gives the race as the view knows it (`courses/ascot-view.json` → `races`, via `viewKey`: the four round-mile races are marked `round: true`; the Queen Alexandra uses the new 2m6f start), the going and the card's seed as a string. `fieldFor` gives the runners in stall order; `engineRunner` the fields the engine reads. `record` keeps place, prize, winner, winning time, margin, lengths beaten, pace as run and the race report.
- **Watch** (`watch`): opens `final-furlong.html?game=1`, waits for its "ready", sends the race key, going, seed and every runner's racecard plus name, 3D silks (`SILK3D`: the 54 menu silks as traditional silks, `silks/silks.json` in the repo, linked by its `menu` field) and coat. The view runs the engine on exactly those, so its result is the game's (checked: same order). It tells the game "finished" at the line and the game records the result. "Back to race week" closes it.
- Balance against the old card engine (30 seeds per strategy, the same harness and strategies): the card-aware planner averages £400k (was £335k) with 2.3 wins (was 1.2); the breeder £311k (was £364k); cheap and wide £79k (was £87k). Ratings matter more than before: a runner level with the top band wins about 14%, 10 above about 50%, 20 above about 74%, 5 below about 5%.

## Save data

`localStorage` key `tb15b` (state `S`, version `v: 6`, migrations in `migrate`; v6 adds the racecard to horses already in a stable). `tbAscotHistory` keeps past weeks, `tbAscotBest` the best. A card is rebuilt from its seed (`makeCard`).

## Code map (`index.html`)

Engine loader (module script) at the top of the scripts · racecard `rollRacecard`, `groundPts`, `lengthsText` · breeding `breedPure` · `drawRaces`, `viewKey` · `makeCard` · `check`, `rankIn`, `bandsLine` · `fieldFor`, `engineRace`, `simRace`, `paceFor`, `record`, `simAndRecord` · `newCard`, `migrate6` · catalogue `newCatalogue` · `render` · planner `fitFor` · horse cards `hcardC` · race week `weekCard`, `paceNote` · `watch` · auction `RIVALS`, `appeal`.

The compact horse card (`hcard`): portrait; name and sire × dam beside the rating box; sex, trip and the 2YO/3YO/4YO track at the foot of the portrait, with a vertical ground gauge (Quick at the top to Heavy at the foot) under the rating; rating-by-distance bars in the card's gold/silver/bronze/basic tiers with the dashed projection line; targets and the Card button. Every card is the same height at every width (checked 320–1440 px).

## Balance as it stands (5 Nov)

Average cost by the horse's peak rating (60 simulated cards; bred = stud fee + the mare's sale price):

| Peak rating | Bred | Bought at Tattersalls |
|---|---|---|
| under 90 | £41k | £34k |
| 90–99 | £85k | £81k |
| 100–109 | £140k | £208k |
| 110–119 | £187k | £314k |
| 120+ | £214k | £438k |

Proposed to the owner, **not yet decided**: raise Blue-blooded mares to about £90–100k and cool Book 1 a little, so buying a top horse is a real option.

## Open items

0. **New, 5 Nov**: a trainer's riding instruction (the engine already takes one) for a pre-race scene; bigger handicap fields (real Royal Ascot handicaps run 16–30, the engine takes 26: check a phone with 20+ horses in 3D); the frogged silks (Doha, Qatar, Royal) are drawn as hoops, to refine in `silks/silks.json`.

1. **Going public with a leaderboard.** The owner wants a game anyone can play, with a leaderboard. Recommended, not yet agreed: host the game on a static host (Cloudflare Pages or Netlify, deployed from this repo) and keep the leaderboard in Supabase or Firebase; a weekly challenge (everyone gets the same seed, first go counts) with free play kept separate. Wix was ruled out as a poor fit. The owner needs to make the accounts.
2. The price balance above.
3. Later, as agreed: real horses from real races with their owners' colours; team cards (may help stayers); maybe all races always available; real 2026 prize money; the CMS stud fees for Chaldean and King of Steel looked wrong.

## Testing (`tools/`)

Serve this folder (`python3 -m http.server 8765` inside `ascot-game/`) and run the scripts from `ascot-game/` with Playwright (Python):

- `harness.js`: whole-game strategy simulations using the game's own functions, races by the engine (load into the page; `await HARNESS.run(name, n, seed)`). Serve the game with the race view's `assets/` beside it, as the artifact has them.
- `t55.py`, `t56.py`: written for the old card engine (they set `CLASS_*`); update before use.
- `t54.py`: average cost by peak rating, bred against bought.
- `t46.py` (with `t41.py`'s setup): every horse card the same height at 12 widths.
