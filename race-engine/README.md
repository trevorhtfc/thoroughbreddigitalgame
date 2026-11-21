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
| `check/balance.mjs` | Is the game balanced? Fields like the game's (12–25 runners on the straight, 9–16 round, four rating bands): wins by riding style, where the winner was 3f and 2f out, pace collapses, the best horse's wins, switches. `node check/balance.mjs 300 [keys]`, `COURSE=newmarket`/`july`, `CENTRE=113` for Group-class fields. |

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

**The July Course** (8 Nov 2026, draft): `courses/newmarket-july-draft.json`, `-stalls.json` and `-standards.json`; `straight` up to a mile (the Bunbury Mile), `round` from 1m2f (the bend from the Cesarewitch leg), starts `"5f"` … `"2m"`, fields up to 28. In the checks: `COURSE=july`.

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

Until 15 Nov 2026: tune in the bench first (`tools/race-bench`), then copy the numbers into `settings.json` → `bench` and re-run the comparison; a rule change went into both `racebench.py` and `engine.js`. **From 15 Nov the engine has rules the bench doesn't** (`settings.json` → `balance`, below), so the bench no longer reproduces the engine's races. Its settings file is still kept equal to `bench` (so `compare.mjs` runs), but tuning is now done on the engine itself: `check/balance.mjs` and the Race Lab.

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

## 15 Nov 2026: balance, traffic and pace collapses

The owner: "a very front runner friendly game … horses at the back struggle to get involved. Pace collapses are rare.
Traffic is over the top visually … horses switching 5 or 6 times and seemingly getting physically stuck on others. We
just need to make sure the game is nice and balanced with horses winning in lots of different ways."

What was wrong (measured with `check/balance.mjs`, fields like the game's):

- **The pace didn't follow the class of the field.** The pace came from the course's par time alone, so a Group 1 field
  (ratings round 113) cruised at a pace that cost it almost nothing: nobody tired, and the horses in front stayed there.
  In Group-class fields front-runners and prominent horses won 1.3–1.6 times their share on the round course, hold-up
  horses 0.3–0.7, and a fast pace cost the leaders nothing (on the pace 1.00, off it 0.99).
- **A strong pace taxed everyone the same.** Every horse ran at the pace, wherever it was, so the leaders never paid
  more for setting it than the ones tucked in behind.
- **Traffic**: a horse looked for a way out whenever anyone was in front of it (not only a slower one), picked a side at
  random each time, and then the steering pulled it straight back in behind the horse it had just gone round. The average
  horse switched 2–6 times a race, the worst 18–27 times. Horses ran into the backs of others and were checked again and
  again.

What changed (`settings.json` → `balance`, and five `bench` numbers; all in `engine.js`):

| | |
|---|---|
| The pace follows the class | `CLASS_PACE` 1: the field's middle race-day rating sets the pace, as it sets real winning times (Group 1s run faster). A Group 1 now races like any other race. |
| Cover | `DRAFT` 0 → 0.2: a horse tucked in behind another saves a fifth of its effort. Leaders and horses stuck wide pay. |
| A stronger, longer final sprint | `BURST` 0.02 → 0.03 over the last 300 m (was 220), for horses with something left. |
| Midfield nearer the pace | `FOLLOW` midfield 0.6 → 0.75 (they had been almost as far back as the hold-up horses on the round course, without their final sprint). |
| Judging the line | `KICK_REACH` [0.8, 0.87, 0.96, 1] → [0.88, 0.92, 0.97, 1]; on the straight course its own (`KICK_REACH_STRAIGHT` [0.97, 0.96, 0.97, 1]) and the hold-up horses' sprint (`BURST_STYLE_STRAIGHT` [0, 0, 0, 0.013]). |
| Keeping in touch | `TOUCH_M` 24: before the run for home a horse more than 24 m off the leader goes at least the pace, so a long race doesn't string out beyond reach. |
| Traffic | A horse looks for a way out only when it is held up, or in the run for home when the one ahead is going slower than it wants (`SLOW_AHEAD`); before the run for home it sits behind a slower one for 3 s first (`BLOCK_WAIT`). It keeps going the same way (back to the other side only 30% of the time, `SIDE_CHANGE`; on the straight its first switch is to the side with fewer horses), rests 3 s between switches (`SWITCH_REST`), is less keen with each (`SWITCH_TIRE`), holds its new line (`HOLD_LINE_S`; in the run for home for good) and never steers back into a lane that's taken. It eases up behind a slower horse from 1.5 m off its quarters (`TRACK_GAP`, `CLOSE_RATE`) instead of running into it. |

Tried and left out: horses sitting further off a strong pace (`LAG`: it only left them too far back), an extra saving
for an uncontested leader (made no difference), lighter hills at Newmarket (no difference).

Before → after, Ascot, 300 races per distance, fields like the game's (rating centre 100):

| | Before | After |
|---|---|---|
| Wins ÷ share, front / prominent / midfield / hold-up, straight 5f–1m | 1.01–1.20 / 1.00–1.12 / 1.00–1.28 / **0.57–0.87** | 0.81–1.08 / 1.01–1.25 / 0.86–1.22 / 0.81–1.15 |
| The same, round 1m–2m6f | 0.86–1.15 / 1.08–1.36 / **0.63–0.90** / 0.73–1.10 | 0.57–1.11 / 0.97–1.19 / 0.81–1.20 / 0.76–1.35 |
| Winner leading 2f out, round 1m4f–2m6f | 41–51% | 31–40% |
| Winner in the back half 3f out, round 1m4f–2m6f | 18–23% | 26–35% |
| Wins ÷ share on the pace / off it, slow pace | 1.62 / 0.56 | 1.48 / 0.66 |
| … even pace | 1.15 / 0.86 | 1.00 / 1.00 |
| … strong pace | 0.91 / 1.11 | 0.79 / 1.26 |
| … fast pace | 0.78 / 1.40 | 0.74 / 1.48 |
| Group-class fields (centre 113), on / off the pace, even / fast | 1.37 / 0.65, 1.00 / 0.99 | 0.90–1.00 / 1.00–1.09, 0.52–0.80 / 1.38–1.85 |
| Switches a horse a race, straight / round | 1.8–3.4 / 4.3–6.3 | 0.4–0.6 / 1.1–1.5 |
| Horses switching 3 times or more | 27–83% | 3–19% |
| Most switches by one horse | 18–27 | 5–8 |
| Best horse wins | 44–57% | 41–51% |

(The best horse wins this often because the game deals one runner from the top band, often 9 or more points clear.)

Still leaning: at Newmarket (both courses) front-runners win about 0.55–0.8 of their share over a mile and further,
and hold-up horses 1.2–1.65 over 1m–1m2f on the Rowley Mile. The Race Lab can try numbers there.

New in each runner's result (for checking): `switches`, `sideChanges`, `heldSeconds` (time tracking or held behind a
slower horse), `bumpedSeconds` (time pressed against one), `energyAtKick` and `energyLeft` (shares of its tank).

## Not so wide on the first bend (21 Nov 2026)

Owner, playing Beginner Ascot: "The race engine seems too happy to let horses be 5/6 wide in early turns in the races.. this feel unrealistic."

- Before the first bend a horse may only drift across at `EARLY_STEER_MAX` (1.2, was the full `STEER_MAX`), so the field doesn't fan out wide going into it.
- From `TUCK_FROM` (300 m) before a bend, a horse stuck wide with a horse alongside either eases a touch (`TUCK_EASE`, if its rider is holding it up) or pushes on a touch (`TUCK_PUSH`), to drop in behind or get across.
- `check/width.mjs` counts how wide the runners are halfway round the first bend. With 1m and 1m6f at Ascot, 5 wide or more went from 11-12% of runners to 3-5%. The widest horse went from about 5 lanes out to about 4. Other trips are 0-1%.
- Front runners against hold-ups, 400 races a trip: 1.06/0.94 (was 0.96/1.04). That is still within the target band.

Also: Ascot's 2m6f now starts on the straight mile, as the Queen Alexandra does (`tools/course/place_stalls.py`, `ON_STRAIGHT`). The race is 4299.1 m, par 4m 49.0s.
