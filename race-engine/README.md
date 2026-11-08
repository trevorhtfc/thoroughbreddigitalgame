# Race engine

The engine decides every race; the race view only plays back what it hands over. It's plain JavaScript with no build step and no dependencies, so the race view loads it as it is, the game can later, and Node runs it for checking.

It follows the test bench's rules exactly (`tools/race-bench/racebench.py`), one race at a time instead of thousands at once. Every number is in `settings.json`, none in the code. A race is seeded: the same race card, going and seed always run the same race, in every browser.

## Files

| File | What it is |
|---|---|
| `engine.js` | The rules. `runRace(race, runners, data)` returns `{ timeline, result }`. |
| `settings.json` | Every number. Its `bench` section is a copy of `tools/race-bench/settings.json` and must match it (the comparison checks). |
| `field.js` | Random race cards like the bench's, for checking and for the race view until the game sends real ones. |
| `copy-to-view.mjs` | Copies the engine into `race-view/assets/engine/`. Run it after any change here. |
| `check/test.mjs` | Checks: the same seed replays exactly; the timeline's shape; no two horses in the same space; effort 0–3; the result agrees with the timeline. |
| `check/compare.mjs` | Thousands of races at every distance, the same figures as the bench's (`tools/race-bench/benchstats.py`). |
| `check/table.mjs` | Sets the two side by side in `check/results/compare.md`. |
| `check/one.mjs` | Runs one race and prints the result and events: `node check/one.mjs r1m 14 seed`. |
| `check/effort.mjs` | When jockeys start pushing and driving, by place and pace: `node check/effort.mjs s1m 200`. |

## Using it

```js
import { runRace } from "./engine.js";
const { timeline, result } = runRace(
  { course: "roundMile", distance: 1649.4, start: "roundMile", going: "Good", seed: 42 },
  runners,                                     // in draw order: runners[0] is in stall 1
  { course, stalls, standards, settings }      // courses/ascot.json, ascot-stalls.json, ascot-standards.json, settings.json
);
```

**Newmarket** (8 Nov 2026, draft): hand over `courses/newmarket-draft.json`, `newmarket-stalls.json` and `newmarket-standards.json` instead; the races are `straight` (up to 1m2f) or `round` (1m4f and up, with the one bend), the starts are named by trip (`"5f"` … `"2m4f"`), and fields go up to 30. In the checks: `COURSE=newmarket node check/test.mjs` (and the same for `compare.mjs`, with `OUT=engine-newmarket`).

**The race**: `course` (`straight`, `roundMile` or `round`), `distance` in metres, `start` (a start in `courses/ascot-stalls.json`), `going` (Heavy, Softer, Good, Quicker, Quick), `seed`, and for handicaps `handicap: true`.

**Each runner** (the racecard fields agreed on 4 Nov):

| Field | What it is |
|---|---|
| `rating` | Rating at its age. |
| `style` | `front`, `prominent`, `midfield` or `holdup`. |
| `flex` | `set`, `adaptable` or `versatile`. |
| `temperament` | `calm` or `keen`. |
| `trip` | Its two best distances, e.g. `["7f", "1m"]` (ladder 5f … 2m+). −5 per step outside; it also sets the "speedier" or "stayer" shade. |
| `goings` | The goings it likes, e.g. `["Good", "Quicker"]`: +5, 0, −5 or −10. Leave it out for no preference. |
| `mark` | Its handicap mark (handicaps only). |
| `jockey` | Skill 1–5; left out, it's drawn at random. |
| `instruction` | The trainer's riding instruction (a style), or leave it to the jockey. Past the horse's flexibility it races keenly. |
| `name` | For the result and events. |

**The timeline** is exactly what the race view plays: `{ dt: 0.1, frames }`, one frame every tenth of a second from the off, each runner in draw order as `[distance from the gate line (m), across from the track's middle (m), speed (m/s), effort 0–3, heading (rad)]`. It runs on past the post while the horses pull up, so the view's finish replay has something to show.

**The break**: most horses come out within a length of each other; about 1 in 50 misses the break and loses several lengths, keen horses far more often than calm ones (1 in 18 against 1 in 250). (A slower break for held-up horses, `HOLDUP_SLOW`, was tried and set to 0: it cost them too many wins.)

**Effort** comes from what the jockey is doing, tied to the horse's energy and speed: 0 cruising (even at a strong pace); 1 pushing (making up ground after a check or pushing across to a place, or getting busy as the run for home nears); 2 driving; 3 asking for everything (the tank nearly empty, or a close finish). The jockey feels how much his horse has left against the field and where it would finish if everyone kept going as they can: a tiring horse, or one going nowhere, is ridden first; one travelling well waits. So in a slowly run race the back markers go first and the leaders sit; in a fast one the tiring leaders are coaxed while the closers wait. A well-beaten horse isn't given the whip. Effort never changes the race.

**The result**: `placed` (place, runner, draw, time, margin to the one in front and lengths behind the winner, both in lengths, plus the race-day rating, form on the day and lengths lost to traffic), `winningTime`, `parTime`, the pace (expected from the racecard, as run, and each group's on the straight course) and `events`: missed the break, lead changes, short of room, switched, kicked and weakening, each with a time, distance out and a line of text.

## Checking it

```
node check/test.mjs                        # about 40 seconds
node check/compare.mjs 4000 12 2           # engine figures (about 30 minutes on 2 cores)
cd ../tools/race-bench && python3 benchstats.py 4000 12 ../../race-engine/check/results/bench.json
node check/table.mjs                       # the side-by-side table
```

## Changing the rules

Tune in the bench first (`tools/race-bench`), then copy the numbers into `settings.json` → `bench` and re-run the comparison. A rule change goes into both `racebench.py` and `engine.js`.

## 7 Nov 2026: more horses coming from the back

The owner, after watching a handful of races: very little comes from the back. Measured (`check/closers.mjs`, 16
runners): the winner was usually already up with the pace 2 furlongs out (leading at 2f out in 45% of straight-mile
races and 43% at 1m4f; only 0.2 L behind the leader at the 2f pole on the straight mile, median). The cause: every
jockey kicked at the same point (about 3.4f out in a mile) and rationed the horse's energy exactly to the line, so the
held-up horses made their ground between 3.5f and 2f out, and leaders never ran out of petrol.

Two new numbers and one changed (in `bench` and the bench's own settings; the same rule in `racebench.py` and `engine.js`):

| Setting | Front · Prominent · Midfield · Hold-up | What it does |
|---|---|---|
| `KICK_STYLE` | 1 · 1 · 0.88 · 0.76 | Where each style's jockey goes for home, as a share of the usual kick point: held-up horses wait. |
| `KICK_REACH` | 0.8 · 0.87 · 0.96 · 1 | How far off a jockey judges the line when he kicks: a front-runner is set alight as if it were 20% nearer, so it can empty before the post and come back to the field in the last furlong. |
| `BURST_STYLE` | 0 · 0 · 0.008 · 0.016 (was 0.006, 0.018) | The final sprint's extra for midfield and hold-up horses. |

Before → after (`node check/closers.mjs 300 16`, Good ground; before was 200 races):

| | Winner in the back half 2f out | Winner leading 2f out | Winner's lengths behind the leader 2f out (median) | Hold-up wins (share 25%) | Best horse wins |
|---|---|---|---|---|---|
| 6f straight | 24% → 29% | 27% → 27% | 1.2 → 1.4 | 20% → 20% | 34% → 34% |
| Straight mile | 9% → 20% | 45% → 36% | 0.2 → 1.2 | 30% → 29% | 40% → 34% |
| Round mile | 19% → 24% | 25% → 29% | 2.4 → 2.9 | 18% → 17% | 28% → 29% |
| 1m4f | 5% → 11% | 43% → 37% | 0.7 → 1.9 | 19% → 26% | 28% → 29% |
| 2m | 11% → 13% | 36% → 42% | 1.7 → 1.0 | 35% → 29% | 29% → 30% |

Stronger settings were tried (front-runners judging the line 30% nearer, hold-up horses kicking at 0.65–0.8 of the
usual point, a bigger burst): they doubled the effect (straight mile 24% from the back half, 1m4f 17%, winners 2–3 L
down at the 2f pole) but front-runners then won only 0.64–0.88 of their share on the bench (they had been about 1).
This balanced version keeps front-runners at about 0.82–0.99 and lifts midfield horses on the round course (0.5–0.85
before, now about 0.77–1.03). The engine and the bench were compared again afterwards: `check/results/compare.md`.

## 8 Nov 2026: hills (Newmarket's Dip counts)

The owner: "the Dip should count, yes: you need more energy to go up than on the flat, so it uses a little more.
Downhill is not a free pass either, as it needs balance." A course can now carry the height of its ground
(`heights` in the course file: every 5 m along the inside rail, by metres to go). Ascot has none, so its races are
exactly as before. Newmarket's is the draft profile: gentle ridges down the straight, then down into the Dip from the
Bushes (2f out), the bottom at the 1f pole, and a 3.6 m climb to the post.

| Setting | Value | What it does |
|---|---|---|
| `HILL_UP` | 0.5 | Energy for every metre climbed (the tank is about 94 for a mile): the last furlong's climb costs about 2% of it. |
| `HILL_DOWN` | 0.15 | Energy for every metre run downhill (balance): about a third of the climb's. No extra speed downhill. |
| `HILL_SLOW` | 0 | Tried and set to 0: slowing every horse uphill *helped* front-runners (slower speeds cost less energy, and the closers' final sprint was cut back too). |

It is a small cost, but it comes at the worst moment for a horse that has already emptied the tank: a front-runner
that went for home early has nothing left for the climb and comes back to the closers. Measured on the bench
(`tools/race-bench/nmdip.py`, a flat Newmarket against the same races with the Dip): see the table in
`tools/race-bench/README.md`. The par times at Newmarket (`courses/newmarket-standards.json`) are set so that the
winning times, Dip included, come out at rough real Rowley Mile times (`tools/race-bench/nmcalibrate.py`).
