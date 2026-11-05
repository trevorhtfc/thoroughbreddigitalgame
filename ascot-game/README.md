# Thoroughbred Ascot: the playable game (handover, 5 Nov 2026)

The quick management game: breed and buy a stable, enter one horse per race across ten randomly drawn Royal Ascot races, and win as much prize money as you can. It is complete and playable. Owner: graphic designer, little coding. Explain things plainly, in plain British English.

## Where it lives

- **Play it:** the Claude artifact "Thoroughbred Ascot", https://claude.ai/code/artifact/acc00bb9-1451-423b-a99c-15e5502f01f8 (version 37). It is private to the owner until shared.
- **The files:** this folder (`ascot-game/`) is an exact copy of what the artifact publishes, plus `tools/` for testing. The artifact holds the same 73 files.
- **To carry on in a new chat:** read the artifact (Artifact tool, `action: "read"` with its URL, then `path` for each file you need) or take the files from this folder. Make the change, then republish to the same URL: `index.html` as `file_path`, with any other changed file in `files` (e.g. `{"race.html": "<local path>"}`). Copy the result back into this folder so the two stay in step.

## Files

| File | What it is |
|---|---|
| `index.html` | The whole game (about 2,900 lines): menu, breeding, mares sale, Tattersalls, planner, race week, final standings. |
| `race.html` | The race view, opened in an iframe for each race. It has **its own copy of the race engine** (`simulate`), which must stay identical to the one in `index.html`. |
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
5. **Race week:** the going is hidden until now, then declared. Watch each race (race view) or sim it.
6. **Result:** a final standings animation climbs the title ladder. Titles by prize money: Royal Ascot Champion £1m+, Leading Owner £750k+, Group Race Force £500k+, Royal Ascot Winner £250k+, Paying Guest below. Prize money is a separate pot from the budget; money spent doesn't count.

## The rules come from the board game's code

Breeding and Tattersalls follow the companion app's code in `trevorhtfc/horseracinggame` (owner: "follow the code, not the rule book"): `src/backend/breeding.web.js` (copied as `breedPure`, checked identical over 22,480 foals), `src/pages/Tattersalls.hju2p.js` (lot rules, `lotMatch`, `weightedMare`), `src/backend/tattersalls.web.js` (reserves). Unproven stallions: players see the stud-book stars; the foal is bred from the hidden true rating, one star either way per card. Only the standard-game stallions from the CMS (no expansions).

## Races

- `POOL`: the 35-race 2026 Royal Ascot programme. `drawRaces` takes 2 a day, at least 3 handicaps or conditions races and at least 3 pattern races.
- Bands (the rating needed for each deck: black, red, yellow, blue) and prizes by grade (`GRADE`): Group 1 120/115/110/105, £300k to win; Group 2 110/105/100/95; Group 3 and Listed 105/100/95/90; Handicap and Conditions 100/95/90/85, £60k to win. Handicaps refuse a horse rated over 110 (`HCAP_MAX`).
- A horse's rating in a race: its age rating, −5 per step off its best trip (more than 3 steps: can't run) (`check`).
- AI fields: 6–9 runners (9–11 in handicaps), spread across the decks by race strength (`FIELD_W`), always one black and one blue.
- **The race engine here is the board game's card engine**: each round every horse plays a card from its deck's table (or the pace dice), capped by position (leader 8, second 9, third 10). On top of that, since 5 Nov, **class**: every runner has a chance of an extra square each round, from its rating above the race's lowest band (`classEdge`: (rating − band 4) / 24, up to 1.8). Win rates for your runner: Black just in 22%, 10 above 34%, 20 above 54% (before: about 19–20% whatever the rating). `fieldFor` sets `edge`; both `simulate` copies use it; `watch` passes it to the race view. Checked: the race view and the recorded result agree in 100 of 100 races.
- The new race engine being built in this repo (`race-engine/` on branch `claude/race-engine-js`) is meant to replace this card engine later.

## Save data

`localStorage` key `tb15b` (state `S`, version `v: 5`, migrations in `migrate`). `tbAscotHistory` keeps past weeks, `tbAscotBest` the best. A card is rebuilt from its seed (`makeCard`).

## Code map (`index.html`)

Race engine `simulate` ~1303 · breeding `breedPure` ~1411 · pairing `pairProblem` ~1494 · `drawRaces` ~1578 · `makeCard` ~1619 · `check` ~1655 · `fieldFor`, `classEdge`, `simRace` ~1673–1699 · `newCard` ~1708 · catalogue `newCatalogue` ~1792 · mares sale `drawPile`, `keepOffer` ~1819 · `render` ~1997 · planner `raceChip`, `fitFor`, `plannerView` ~2051–2067 · stud `studView` ~2140 · sale `maresSale`, `saleView` ~2171–2187 · horse cards `profileHTML`, `targetBox`, `groundMeter`, `hcard`, `horseCols` ~2319–2440 · standings `playTally` ~2591 · `watch` ~2625 · auction `RIVALS`, `appeal` ~2650.

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

1. **Going public with a leaderboard.** The owner wants a game anyone can play, with a leaderboard. Recommended, not yet agreed: host the game on a static host (Cloudflare Pages or Netlify, deployed from this repo) and keep the leaderboard in Supabase or Firebase; a weekly challenge (everyone gets the same seed, first go counts) with free play kept separate. Wix was ruled out as a poor fit. The owner needs to make the accounts.
2. The price balance above.
3. Later, as agreed: real horses from real races with their owners' colours; team cards (may help stayers); maybe all races always available; real 2026 prize money; the CMS stud fees for Chaldean and King of Steel looked wrong.

## Testing (`tools/`)

Serve this folder (`python3 -m http.server 8765` inside `ascot-game/`) and run the scripts from `ascot-game/` with Playwright (Python):

- `harness.js`: whole-game strategy simulations using the game's own functions (load into the page; `HARNESS.run(name, n, seed)`).
- `t55.py`: whole games by strategy (prize, wins, top 3).
- `t56.py`: win rates for a Black runner at different ratings.
- `t54.py`: average cost by peak rating, bred against bought.
- `t58.py`: the race view gives the same result as the game (100 races).
- `t46.py` (with `t41.py`'s setup): every horse card the same height at 12 widths.
