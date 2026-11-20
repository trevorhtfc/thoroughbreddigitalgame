# The career rules: a kit to put behind the career hub

20 Nov 2026. This folder is the rules of the "Thoroughbred Career" prototype (https://claude.ai/artifact/CsCgEoUnKTgC7TZM1EtZY4), cut free of its own calendar and screens so the career hub (`js/career/core.js`, `ui.js`) can use them. Nothing here is loaded by the hub or the live game yet.

The owner's brief for these rules: "fun, accessible and engaging … enough detail to create proper decisions … enough wanting to find what's next … not over complex, a nightmare to navigate and a UI disaster."

## What is in the folder

| File | What it is |
|---|---|
| `rules.js` | **The rules.** `window.TBRULES`. Horses and what is hidden about them, discovery, the trainer's view of a race, race day, the handicapper, gallops, selling, the stud, the sales, the rivals' star horses. No screens, no calendar, no clock. Runs in Node. |
| `hub-adapter.js` | **The join.** `window.TBJOIN`. Turns the hub's data (`CAREER_DATA`) and its races into what the rules expect, and keeps the rules in step with the hub's week. Already tested against the hub's real calendar. |
| `data.js` | Stallions, mares, names, silks and the big races in the reference game's shape (`window.TBDATA`). Only the reference game and its tests need it: the hub gets its data through `TBJOIN.setup`. |
| `reference/` | The whole "Thoroughbred Career" game as a worked example of a host: `season16.js` (16 fortnights, the order a host calls the rules in), `ui.js` and `style.css` (every screen), `index.html` (built, open it to play), `big-races.txt`. |
| `tools/` | `test-hub-join.js` (robot careers week by week on the hub's calendar, through the adapter), `test-careers.js` (robot careers on the reference game), `test-group-races.js` (how good a horse must be), `test-taps.py` (random taps for crashes), `gen-data.js`, `build.js`. |

## The join in ten steps

1. Load `js/career/data.js`, `js/career/rules/rules.js`, `js/career/rules/hub-adapter.js`, then the hub's core and screens.
2. Once at start-up: `TBJOIN.setup(window.CAREER_DATA)`. This hands the rules the hub's stallions, mares, names and rival owners, and sets weekly turns.
3. Let the rules own the horses. On a new game: `TBRULES.init(S, seed)`, then `S.horses.push(...TBRULES.starters())`. `init` only adds the fields that are missing (listed below), so `S` can stay the hub's save object. After loading a save: `TBRULES.use(S)`. Bump the hub's save key, because the horse records change shape.
4. As each week begins: `TBJOIN.startWeek(S, week)`.
5. For any race the player might look at or enter: `const race = TBJOIN.raceFor(S, hubRace, goingName)`. Pass `race` to `TBRULES.eligible(h, race)`, `TBRULES.view(h, race)` and `TBRULES.runRace(race, [horses])`. Keep the hub's `barred()` for the calendar's own conditions (sales races, the All-Weather Finals, unraced maidens, claims) and ask it first.
6. On "Go racing": for each race with runners, `const result = TBRULES.runRace(race, runners)`. Work out every result first and save, then show them one at a time. A reload then cannot re-roll a race.
7. As the week ends: `TBJOIN.endWeek(S, weeks)` (`weeks` = 4 for a month-long winter turn). Charge fees through `TBRULES.cash(-amount, 'fees')`.
8. Gallops: `TBRULES.gallop(h, 'work' | 'school' | 'easy')`. The hub counts how many are left.
9. Sales and stud: `TBRULES.genSale()`, `nextBid`, `bid`, `pass`, `sell`, `retire`, `sires`, `setCover`.
10. On 1 January: `TBRULES.newYear()`.

`tools/test-hub-join.js` does exactly this in about forty lines. Read it before writing the join.

## What the rules need from a host

**One state object.** These fields, all plain data and safe to save as JSON: `rs` (the luck), `nid`, `used` (names taken), `horses`, `mares`, `young`, `studs` (your own stallions), `stars` (the rivals' best), `rep`, `cash`, `season`, `prog`, `clock`, `ss` (this season's counts), `troph`, `hof`, `top`, and `cards` (made by the adapter). The hub's own fields can sit beside them.

**Two clocks, kept by the host.** `prog` is how far through the turf season it is: 0 at the first turf turn, 1 at the last and through the winter. Horses grow along it and two-year-old races get stronger along it. `clock` is a count of turns that never goes back. `TBJOIN.startWeek` and `endWeek` set both.

**Races.** A race handed to the rules looks like this. `TBJOIN.raceFor` builds it from a hub race:

```js
{ id, n: 'Lincoln Handicap', co: 'Doncaster', cls: 'HH', f: 8, a: [4, 99], sx: '', nog: false,
  p: 75,            // prize to the winner, in thousands
  cap: 105,         // handicaps: the top rating allowed. The bottom weight is cap - 20
  g: 2,             // going: 0 Heavy, 1 Softer, 2 Good, 3 Quicker, 4 Quick; null on the all-weather; undefined if not yet declared
  ty: 'g',          // track: 'g' galloping, 's' sharp, 'u' undulating (filled in from the course name)
  nrun: [9, 15],    // fewest and most rivals (optional)
  field: [...] }    // the rivals, made by TBRULES.prepRace: { n, s (index of the owner in CAREER_DATA.rivals), ab, or, g, st, fm, star }
```

**Money and reputation.** Both change only through `TBRULES.cash(amount, why, horse)` and `TBRULES.addRep(n, why, horse)`. Set `TBRULES.on.money = (amount, why, horse) => …` and `TBRULES.on.rep` to write the hub's ledger and news. `why` is one of `prize`, `sale`, `stud`, `cover`, `purchase`, `fees`, `race`.

## How the hub's races map to classes

| Hub race type | Rules class | Notes |
|---|---|---|
| Group 1, Group 2, Group 3, Listed | `G1` `G2` `G3` `L` | The rivals' star horses turn up in Group races and carry on from year to year. |
| Heritage handicap | `HH` | Ceiling from the band. |
| Handicap, Nursery, Classified | `C2` to `C6` by class number | Ceiling from the band (0-55 up to 0-105). |
| Maiden | `M`, or `MA` when the name starts Restricted or Auction | `MA` bars horses that cost over £30,000. |
| Novice | `N` | Up to two wins. |
| Conditions, Sales race | `C` | |
| Seller, Claimer | `S` | Weak fields on purpose. The hub's claim rule is what keeps good horses out. `autoPick` will choose them gladly, so leave them out of the list for a horse the player would mind losing. |

Sex `F` is fillies only, `C` bars fillies, `CF` (the Classics) bars geldings. The rules accept a gelding (`sex: 'g'`); he cannot go to stud.

## A horse, as the screens read it

The hub's horse record is replaced by this one. Extra hub fields (`entries`, `colour`, `fromSale`, `aw`, `joined`) can be added to it freely.

| What | Rules field | The hub's name today |
|---|---|---|
| Name, age, sex | `n`, `age`, `sex` (`c`, `f`, `g`) | `name`, `age`, `sex` |
| Pedigree | `sire`, `dam`, `ss`, `ds` (stars) | `sire`, `dam`, `damStars` |
| Rating (the handicapper's) | `or`, `peak`; `null` until two runs or a win | `or` |
| Record | `runs`, `wins`, `pl`, `earn`, `form` (last positions), `hist` (races), `big` (big wins) | `runs`, `wins`, `places`, `earned`, `form`, `seen` |
| Freshness, injury | `fresh` 0-100, `inj` (turns out) | `fresh`, `out` |
| Racecraft | `craft` 0 green to 3 professional | from `runs` |
| Trainer's estimate of potential | `k.pe` (centre), `k.pw` (give or take). Stars: `TBRULES.potStar(k.pe - k.pw)` sure, `potStar(k.pe + k.pw)` possible | `est.c`, `est.w` |
| What is known | `k.mat`, `k.trip`, `k.build`, `k.style`, `k.temp`, `k.con`, `k.quirk`: 0 unknown, 1 a guess, 2 sure. The guess itself is in `gs.mat`, `gs.trip`, `gs.build`, `gs.temp`, `gs.con` | `known` |
| Ground known | `k.gr[0..4]` per going: `null` untried, 2 acts on it, 1 copes, 0 hates it. `k.gh` is the best guess at the run of goings it likes | `known.ground` |
| Hidden truth (never show) | `pot`, `mat` (`e` `n` `l`), `trip` (index of the shorter of two best trips), `gr` (`[lo, hi]` goings), `build` (`gal` `agi` `ver`), `style` (`F` `P` `M` `H`), `temp` (`calm` `even` `hot`), `con` (`tough` `sound` `del`), `quirk` | `pot`, `mat`, `trip`, `g`, `temper`, `style` |

Words for all of these are in `TBRULES.LAB`, `QUIRKS` and `QDESC`. `reference/ui.js` has the nine-tile horse sheet (`tiles`, `tileInfo`) that shows them.

## What comes back

**`TBRULES.view(h, race)`** is the trainer's view, from what is known only:

```js
{ lv: 3, label: 'Big chance',          // 0 Outclassed, 1 Place chance, 2 In the mix, 3 Big chance, 4 Hard to beat
  win: 0.27, pl: 0.61, unsure: false,  // unsure: the horse is still an unknown quantity
  fit: { trip: 'y', gr: 'q', tr: 'm', tripq: 1 },   // y suits, m so-so, n against, q untested; ...q = only a guess
  low: false }                         // rated below this handicap's bottom weight
```

**`TBRULES.runRace(race, horses)`** is the whole race:

```js
{ n, co, cls, f, p, g, ty, pace: 'slow' | 'even' | 'fast',
  run: [ { pos, n, s, st, or, fm, od: '5/1', btn: 1.25, you, hid, star } ],   // every runner, in finishing order. btn = lengths behind the winner
  mine: [ { hid, pos, won, prize, rep, orOld, orNew, inj,
            say: 'Outpaced. He is crying out for further.',                  // the trainer's debrief
            rev: [['Trip', 'Wants further: 1m–1m2f?'], ['Ground', 'Acts on Good']] } ] }   // what the run taught you
```

The horse records, the money, the reputation and the trophies are already updated when it returns. `run` is enough to draw a racecard (sort by odds, never by `pos`), play a race and show the result: see `vRaceday` and `playRace` in `reference/ui.js`. When the 3D race view is joined, `run` gives it the finishing order, the margins and each runner's running style.

## The rest of the rules, one line each

| Call | Does |
|---|---|
| `init(E, seed)`, `use(E)` | Make ready a new state; point the rules at a loaded one. |
| `starters()` | The three horses a new owner starts with. |
| `foal(sire, dam, opts)` | A new horse from two parents (records from `TBRULES.D.stallions`, a mare of yours, or `sireOf(name)`). |
| `prepRace(race)` | Fill in a race's ceiling, track type and field. |
| `eligible(h, race)` | Age, sex, maiden, novice and rating rules. |
| `options(h, races)`, `picks(h, races)`, `autoPick(h, races)` | Every race a horse can run in with the trainer's view, best first; the best chance and the best prize; the trainer's own choice or `null`. |
| `gallop(h, kind)` | `work` sharpens the potential estimate and reveals a tile; `school` teaches racecraft, then tracks, and cures slow starters; `easy` adds 30 freshness. Returns `{ text, rev }`. |
| `rest()` | One turn's rest for every horse. `TBJOIN.endWeek` calls it. |
| `ability(h)`, `estAb(h)` | What a horse can run to today (hidden), and what the trainer thinks. |
| `valueOf(h)`, `sell(id)`, `retire(id)`, `canStud(h)`, `studFee(h)` | Selling and retiring. A filly becomes a broodmare; a colt with a Group win becomes your stallion, with a payment. |
| `sires()`, `sireOf(name)`, `setCover(mareId, sireName)` | The stallions your reputation allows, and booking one. |
| `genSale()` | Twelve lots: 8 yearlings (`ty: 'y'`), 2 horses in training (`'t'`), 2 mares (`'m'`). Each has `guide`, the trainer's whisper `wh` 0-3 (yearlings), and a rival bidder. |
| `nextBid(lot)`, `bid(lot)`, `pass(lot)` | Bidding. `bid` returns `won`, `raised` (the rival bid again), `cash` or `full`. |
| `boxesFree()`, `arriving()` | Room in the yard; homebreds due in next season. |
| `newYear()` | Everyone a year older and fresh, youngsters due come into training, this winter's coverings become foals, a new crop of rival stars. |
| `tier()`, `T()` | Reputation tier 1-5 and what it brings (boxes, paddocks, gallops, the trainer's eye, the dearest stallion). |

## Where the two prototypes differ

| | The reference game | The hub | What I'd do |
|---|---|---|---|
| Turns | 16 fortnights | 33 weeks and 5 winter months | **The owner's call.** The rules run either way (`CFG.tpf`). Weekly on the real calendar tested fine. |
| Training fees | £500 a fortnight | £150 a week | Keep the hub's: tested, the yard grows steadily. At £250 a week it does not. |
| Gallops | 2 a fortnight at the start | 2 a week | 1 a week at tiers 1 and 2, or horses are found out twice as fast. |
| Runners in a race | Any number of yours | One | Either. `runRace` takes a list. |
| Sellers and claimers | None | Can lose you the horse | Keep the hub's rule. See the note in the class table. |
| Sales | One winter sale | The real sales through the year | Split `genSale()` by `ty` across the hub's sales. For a breeze-up lot take a yearling lot, set `h.age = 2` and call `TBRULES.evid(h, 0.3)` (it has galloped against the clock). |
| Breeding | Foal races two seasons after covering | Foal, yearling, then in training | `newYear()` makes the foal with `due = season + 2` and brings it in when due. If the hub moves young stock itself, clear `due` and push the horse into `horses` at age 2. |
| Reputation for a win | `TBRULES.CLS[cls].rep` (Group 1 120, Classic 180, Class 5 3) | The hub's `REP` table | Use the rules' (they come through `addRep`). The tier thresholds are the same in both: 40, 180, 550, 1,500. |
| Goals, the owners' table, news, the ledger | Three goals a season | The hub's own | Keep the hub's. Feed them from `on.money`, `on.rep` and the season counts in `S.ss`. |
| Stable name and colours | Has a maker | Not yet | `vSetup` and `silk()` in `reference/ui.js`. |

## Screens worth lifting from `reference/ui.js`

Each is one function that returns HTML from the state, in the game's own colours and type.

- `hcard`: the horse card (stars, freshness, form, the trainer's note, the chosen race with its chance chip).
- `shEntry` and `optRow`: "Where does he run?" with the chance chip and the Trip / Ground / Track ticks.
- `shGallop`: the three gallops, each saying what it will do for this horse.
- `shHorse`, `tiles`, `tileInfo`: the horse sheet, nine tiles that fill in, and a plain sentence for each.
- `vRaceday`, `playRace`: the racecard with odds and a pace forecast, the race (a stand-in for the 3D view), the result, the debrief and "what you learned".
- `vWinter`, `lotCard`, `shSire`: who stays, bidding at the sales, choosing a stallion.
- `note`: the trainer's one-line view of each horse.

## Numbers to hold on to

- The chips are honest. Over thousands of robot runs: Hard to beat wins about 60%, Big chance 27%, In the mix 13%, Place chance 7%, Outclassed 1%. On the hub's calendar: 66%, 26%, 12%, 5%, 0%.
- Open Group 1s, with trip and ground to suit: a horse running to 116 wins about 11%, 120 about 28%, 124 about 49%, 128 about 71%, 132 about 89%.
- Foal potential centres on 47 + 7 × sire stars + 6.5 × dam stars, spread about 9.5, with a 1 in 20 freak.
- On the hub's calendar at £150 a week (16 careers, 8 seasons, a cautious robot): 8 to 12 runs a horse a season, about 20 to 30% winners, £12,000 to £20,000 prize money a horse, tier 2 in season 2, tier 3 about season 5, nobody bankrupt.

Run `node tools/test-hub-join.js 16 8` and `node tools/test-careers.js 30 16` after any change to the rules, and `node tools/test-group-races.js` after touching race standards.

## Traps

- **Never show `pot`, `ability()` or the hidden traits.** Screens use `k`, `gs`, `estAb` and `view`.
- **Keep the luck in the save.** `rs` is the rules' seed. `view()` uses its own fixed luck, so looking at a race never changes what happens in it.
- **A racecard must be the race that is run.** `raceFor` keeps each race's field in `S.cards` for that reason. Do not rebuild a field between showing it and running it.
- **Racecards are sorted by odds, never by finishing order.** The result is already in `run` when the card is shown.
- **Old saves.** `season16.js` shows how a save from before a change is brought up to date (`migrate`).
