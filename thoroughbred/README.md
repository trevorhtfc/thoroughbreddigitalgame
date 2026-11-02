# Thoroughbred — 3D race view, step 1: test race

A straight 5-furlong turf course, 8 runners in Thoroughbred silks and coat colours,
a simple race and a camera that follows it.

## Run it
1. Open Godot 4.7 → **Import** → pick `project.godot` in this folder → **Import & Edit**.
2. Wait for the first import to finish (progress bar, about a minute).
3. Press **Play** (▶ top right, or Cmd+B on a Mac).

## Keys
| Key | Does |
|---|---|
| 1 | TV camera (side-on, from the stands side) |
| 2 | Behind the field |
| 3 | Head-on |
| 4 | Follow your horse (gold triangle) |
| 5 | Finish-line camera |
| C | Next camera |
| F | Fast-forward ×3 |
| Space | Pause |
| R | New race (new random field) |

## Settings to play with
Click **TestRace** in the Scene panel; the Inspector shows Race Distance, Field Size,
Lane Width, Horse Scale, Countdown and Field Seed (0 = new field every time).

## What's where
- `scenes/test_race.tscn` — the scene: sky and light, track, camera, on-screen panel
- `scripts/race.gd` — sets up and runs the race, handles keys
- `scripts/runner.gd` — one horse: model, colours, speed and animation
- `scripts/race_camera.gd` — the five camera shots
- `scripts/hud.gd` — running order panel and messages
- `scripts/track.gd` — builds the course from simple shapes
- `scripts/horse_data.gd` — silks, coats and names (copied from the Thoroughbred Ascot web game)
- `shaders/horse_recolour.gdshader` — repaints silks and coat per runner
- `assets/horses/racehorse_gallop.glb` — the horse-and-jockey model (gallop + walk animations)
- `assets/horses/silk_mask.png` — marks which parts of the model are silks / coat
- `tools/bake_mask.py` — rebuilds silk_mask.png if the model changes (not used by Godot)
