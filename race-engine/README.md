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

**Effort** comes from what the jockey is doing, tied to the horse's energy and speed: 0 cruising; 1 pushing (running well above comfort speed, or getting busy as the run for home nears); 2 driving; 3 asking for everything (the tank nearly empty, or a close finish). The jockey feels how much his horse has left against the field and where it would finish if everyone kept going as they can: a tiring horse, or one going nowhere, is ridden first; one travelling well waits. So in a slowly run race the back markers go first and the leaders sit; in a fast one the tiring leaders are coaxed while the closers wait. A well-beaten horse isn't given the whip. Effort never changes the race.

**The result**: `placed` (place, runner, draw, time, margin to the one in front and lengths behind the winner, both in lengths, plus the race-day rating, form on the day and lengths lost to traffic), `winningTime`, `parTime`, the pace (expected from the racecard, as run, and each group's on the straight course) and `events`: lead changes, short of room, switched, kicked and weakening, each with a time, distance out and a line of text.

## Checking it

```
node check/test.mjs                        # about 40 seconds
node check/compare.mjs 4000 12 2           # engine figures (about 30 minutes on 2 cores)
cd ../tools/race-bench && python3 benchstats.py 4000 12 ../../race-engine/check/results/bench.json
node check/table.mjs                       # the side-by-side table
```

## Changing the rules

Tune in the bench first (`tools/race-bench`), then copy the numbers into `settings.json` → `bench` and re-run the comparison. A rule change goes into both `racebench.py` and `engine.js`.
