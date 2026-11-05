# Race bench: the race rules, tested in bulk

This is the test bench for the race engine. It runs thousands of races at once, with no graphics, so the rules can be checked and tuned: who wins, from where, by how much, and in what time. The design behind it is in the "Thoroughbred Ascot: race engine brainstorm" doc. The real engine (later) will follow the same rules and write a timeline for the race view.

It's a sketch for tuning, not the engine itself. It's written in Python with numpy so that thousands of races can run together.

## Files

| File | What it is |
|---|---|
| `racebench.py` | The rules: energy and the final sprint, pace from running styles, groups on the straight course, bends, the draw, traffic (no overlapping, gaps, cutting in, switching), form on the day, handicaps. |
| `settings.json` | Every number the rules use. Tune here, not in the code. |
| `distcheck.py` | Runs every race distance and prints the winning time against a rough real Ascot time, how often the best horse wins, the margins, wins by style and draw, and traffic. |
| `topdown.py` | Draws a race from above at a few moments (start, middle, finish), so you can see what happened. |

## Race distances

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
| `BURST`, `BURST_STYLE`, `BURST_DIST_EXP` | The final sprint in the last 220 m: a base burst, extra for midfield and hold-up horses, scaled up with distance (waiting pays more over further). |
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
    - On the round course from 1m2f to 1m6f, front-runners and prominent horses still win more than real Ascot suggests.
    - Hold-up horses on the straight course are slightly above their share.
