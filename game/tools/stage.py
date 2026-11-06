"""Gathers everything the published game needs into one folder, laid out as the game expects (the page at the top,
the race view beside it, the race view's assets under assets/ with the Newmarket board's own in assets/newmarket/).
Only the files the game actually loads are taken (found by playing it through with every request logged), so the
horse v2 test files and the look test's straight are left out.

python3 game/tools/stage.py <out dir>      then publish <out dir>/index.html with the rest as its files."""
import shutil, sys
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent
game, view = repo / "game", repo / "race-view"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
silks = [p.stem for p in (game / "img" / "silks").glob("s*.webp")]
take = []
def add(src, dst):
    src = Path(src)
    if not src.exists(): raise SystemExit(f"missing {src}")
    take.append((src, out / dst))
# the game
for f in ["index.html", "card.html", "css/components.css", "css/game.css", "js/meetings/royal-ascot.js", "js/rules.js", "js/board.js", "js/ui-parts.js", "js/ui.js", "js/life.js"]:
    add(game / f, f)
for p in sorted((game / "img").rglob("*")):
    if p.is_file(): add(p, p.relative_to(game))
for p in sorted((game / "video").glob("*.mp4")): add(p, p.relative_to(game))
for p in sorted((game / "assets" / "newmarket").glob("*")): add(p, p.relative_to(game))
for p in sorted((game / "assets" / "board-model").glob("*")): add(p, p.relative_to(game))   # small textures for the board's horses
# the 3D race view and what it loads in the game
add(view / "final-furlong.html", "final-furlong.html")
add(view / "horse-v2.js", "horse-v2.js")
A = view / "assets"
for f in ["silks-catalogue.json", "tint-mask.png"]: add(A / f, "assets/" + f)
for d in ["engine", "model", "trees", "baked"]:
    for p in sorted((A / d).glob("*")):
        if p.is_file(): add(p, p.relative_to(view))
for f in ["ascot.json", "ascot-view.json", "ascot-stalls.json", "ascot-standards.json", "ascot-planting.json", "ascot-site-dressing.json",
          "ad-boards.png", "lanes.png", "course-props.json", "course-props-geometry.txt", "planting_belts.json", "planting_belts-geometry.txt",
          "starting_stalls.json", "starting_stalls-geometry.txt", "starting_stalls_kit.json"]:
    add(A / "course" / f, "assets/course/" + f)
for f in ["ascot_main_stand_crowd_areas.json", "crowd_palette.json", "crowd_people.json", "crowd_people-geometry.txt", "site_props_spots.json"]:
    add(A / "architecture" / f, "assets/architecture/" + f)
# the 3D silks and their icons: every set but the pattern catalogue's test swatches
for d in ["silks-3d", "silks-icons"]:
    for p in sorted((A / d).glob("*.png")):
        if not p.name.startswith("catalogue-"): add(p, p.relative_to(view))
for src, dst in take:
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst)
size = sum(d.stat().st_size for _, d in take)
print(f"{len(take)} files, {size / 1e6:.1f} MB in {out}")
