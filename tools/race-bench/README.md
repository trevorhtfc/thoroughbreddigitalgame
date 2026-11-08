# Race bench: the race rules, tested in bulk

This is the test bench for the race engine. It runs thousands of races at once, with no graphics, so the rules can be checked and tuned: who wins, from where, by how much, and in what time. The design behind it is in the "Thoroughbred Ascot: race engine brainstorm" doc. The race engine (`race-engine/`) follows the same rules and writes the timelines the race view plays.

It's a sketch for tuning, not the engine itself. The engine is built (`race-engine/`, 5 Nov 2026) and follows these rules exactly: tune here, then copy the numbers into `race-engine/settings.json` → `bench`, and put any rule change into `race-engine/engine.js` too. It's written in Python with numpy so that thousands of races can run together.

## Files

| File | What it is |
|---|---|
| `racebench.py` | The rules: energy and the final sprint, pace from running styles, groups on the straight course, bends, the draw, traffic (no overlapping, gaps, cutting in, switching), form on the day, handicaps. |
| `settings.json` | Every number the rules use. Tune here, not in the code. |
| `distcheck.py` | Runs every race distance and prints the winning time against a rough real Ascot time, how often the best horse wins, the margins, wins by style and draw, and traffic. |
| `topdown.py` | Draws a race from above at a few moments (start, middle, finish), so you can see what happened. |
| `benchstats.py` | Every distance's figures as JSON, for setting beside the race engine's (`race-engine/check/compare.mjs`, `check/table.mjs`). |

## Race distances

Newmarket (Rowley Mile, draft, 8 Nov 2026): `nm5f` … `nm1m2f` on the straight, `nm1m4f` … `nm2m4f` round the one bend, on a 36 m track with the ground's height (the Dip) from `courses/newmarket-draft.json`.

Straight course: `s5f`, `s6f`, `s7f`, `s1m`. Round course: `r1m` (from the chute), `r1m2f`, `r1m4f`, `r1m6f`, `r2m`, `r2m4f`. The round races start where the distance falls on the loop, and meet the loop's real bends (from `courses/ascot.json`); 2m and 2m4f go round more than once.

## Running it

```
pip install numpy matplotlib
python3 distcheck.py s5f,s1m,r1m,r2m          # a quick check of a few distances
python3 distcheck.py r1m '{"GOING":"Softer"}' 500   # one distance, on soft ground, 500 races
```

## The main settings

| Setting | What it does |
|---|---|
| `COMFORT`, `TANK` | The speed a horse can cruise at without tiring (a share of its full speed), and how much energy it has for going faster. The tank is scaled by race length and by the going. |
| `FOLLOW` | How closely each style (front-runner, prominent, midfield, hold-up) goes with the leaders' pace. |
| `PACE` | The leaders' speed for slow, even, strong and fast races (set by the share of front-runners). |
| `BURST`, `BURST_STYLE`, `BURST_DIST_EXP` | The final sprint in the last 220 m: a base burst, extra for midfield and hold-up horses, scaled by (distance / a mile) to the power 1.4, so waiting pays more over further. |
| `DRAFT`, `DRAFT_LEN` | Shelter: less energy spent tucked in behind another horse. Off (0) for now: at 10% it punished front-runners far too much on the straight course, where the packs cover almost everyone but the leader. |
| `SHADE_TOP`, `SHADE_TANK` | A 7f/1m type has a shade more sprint, a 1m/1m1f type a shade more stamina. |
| `FORM_SD`, `UP_P`, `FLOP_P` | Form on the day: an everyday wobble, the odd big day, a rarer flop. |
| `JOCKEY_READ`, `FLEX_MIX` | How often a jockey rides an adaptable horse to suit the expected pace. |
| `CUT_IN`, `CHECK_DV_BY_COURSE` | When a horse may cut across in front of another, and how hard the squeezed horse checks. |
| `KICK_LOOK`, `GAP_AHEAD`, `GAP_BEHIND`, `SWITCH_COST` | Finding gaps, and what switching costs. |
| `FAN_FROM`, `FAN_RATE` | How the field spreads out in the straight. |
| `HANDICAP`, `H_SD` | Handicaps: race-day rating = true rating + (true rating minus the handicap mark). `H_SD` is how far out the handicapper's marks are. |
| `GOING` | Heavy, Softer, Good, Quicker or Quick: speed and how sapping it is. |

## Where it stands (5 Nov 2026)

- **Winning times** are within about 1–2 seconds of rough real Ascot times at every distance. The real times are approximate, from memory, and should be checked.
- **The best horse on paper** wins about 30% in 10-runner fields, 25% in 12-runner fields and 20–25% in big fields. A horse 5–6 points behind the best wins about 1 in 20.
- **A superstar** 19 points clear wins about 9 races in 10.
- **Traffic:** about 10% of horses lose a length or more on the straight, and about 20% on the round course (the pocket on the rail).
- **To keep tuning:**
    - Midfield horses are a little low on the round course (about 0.7 of their share): they're the ones caught in traffic on the bend.
    - Hold-up horses on the straight course are slightly above their share.

## 8 Nov 2026: Newmarket and the Dip

The owner: the Dip counts. Uphill costs a little more energy than the flat; downhill is no free pass (balance), so it
costs a little too, with no extra speed. The rule is in `racebench.py` and `race-engine/engine.js` alike: every metre
climbed costs `HILL_UP` (0.5) of the tank (about 94 for a mile), every metre run downhill `HILL_DOWN` (0.15). The
last furlong's 3.6 m climb costs about 2% of the tank: small, but it lands when a horse that went for home early has
nothing left. `HILL_SLOW` (slowing every horse uphill) was tried and left at 0: it helped the front-runners, because
slower speeds cost them less energy and it cut the closers' final sprint too.

`nmdip.py` runs the same races twice, on a flat Newmarket and with the Dip (600 races of 14 runners; the mile also
1,500 races of 12):

| Distance | Front-runners win (1 = fair share) | Hold-up horses win | Leader 2f out wins | Winner in the back half 2f out |
|---|---|---|---|---|
| 6f | 1.07 → 0.99 | 0.84 → 0.93 | 28% → 26% | 26% → 28% |
| Mile | 1.07 → 0.97 | 0.93 → 1.03 | 41% → 39% | 19% → 22% |
| Mile, 12 runners | 0.80 → 0.71 | 1.17 → 1.26 | 37% → 34% | 21% → 24% |
| 1m2f | 1.00 → 0.88 | 1.02 → 1.17 | 43% → 39% | 13% → 14% |
| 1m4f | 0.97 → 0.82 | 0.88 → 1.02 | 42% → 37% | 13% → 16% |
| 2m2f | 0.85 → 0.81 | 0.98 → 1.10 | 43% → 40% | 14% → 16% |

About a tenth off the front-runners' wins and a tenth on the hold-up horses', more over middle distances; the best
horse's chances don't change. The winning times barely move (0.1–0.2 s), so the par times at Newmarket are set by
`nmcalibrate.py` to come out at rough real Rowley Mile times. The engine was compared with the bench at four
Newmarket distances (`race-engine/check/results/compare-newmarket.md`, 1,200 races each): every difference is within
chance.

### The July Course (8 Nov 2026, draft: `jc5f` … `jc2m`)

The owner's notes: the Bunbury Mile rolls for its first three-quarters, runs downhill from 6f to 5f out, then climbs
steeply and steadily over the last two furlongs ("tired horses tie up"; jockeys mustn't kick too early). Same rule,
no new numbers: the climb is 3.4 m over 2f, so it catches anyone who went for home early. `nmdip.py`, 800 races of 14
runners:

| Distance | Front-runners win | Hold-up horses win | Leader 2f out wins | Winner in the back half 2f out |
|---|---|---|---|---|
| 6f | 0.89 → 0.73 | 0.86 → 1.01 | 29% → 26% | 24% → 28% |
| Mile | 0.83 → 0.72 | 0.99 → 1.10 | 38% → 35% | 16% → 18% |
| 1m4f | 0.84 → 0.72 | 0.89 → 0.99 | 43% → 40% | 12% → 14% |
| 1m5f | 0.84 → 0.74 | 0.91 → 1.01 | 44% → 40% | 10% → 13% |

A little stronger than the Rowley Mile's Dip over sprint trips, as the owner's notes would have it. The engine matches
the bench on the July Course too (`race-engine/check/results/compare-july.md`: 6f, mile, 1m5f).

