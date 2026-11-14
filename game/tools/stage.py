"""Gathers everything the published game needs into one folder, laid out as the game expects (the page at the top,
the race view beside it, the race view's assets under assets/ with the Newmarket board's own in assets/newmarket/).
Only the files the game actually loads are taken (found by playing it through with every request logged), so the
look test's straight is left out (the v2 horse is in: it has been the race view's horse since 7 Nov).

python3 game/tools/stage.py <out dir>      then publish <out dir>/index.html with the rest as its files."""
import re, shutil, sys
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
for f in ["index.html", "card.html", "css/components.css", "css/game.css", "js/meetings/royal-ascot.js", "js/meetings/newmarket.js", "js/rules.js", "js/team.js", "js/accounts.js", "js/board.js", "js/ui-parts.js", "js/ui-team.js", "js/ui.js", "js/colours.js", "js/howto.js", "js/leaderboard.js", "js/life.js"]:
    add(game / f, f)
# the Race Lab (lab.html): test the race engine on any course, distance, going, field and tactics
for f in ["lab.html", "css/lab.css", "js/lab.js", "js/lab-worker.js"]:
    add(game / f, f)
for p in sorted((game / "img").rglob("*")):
    if p.is_file(): add(p, p.relative_to(game))
for p in sorted((game / "video").glob("*.mp4")): add(p, p.relative_to(game))
for p in sorted((game / "assets" / "newmarket").glob("*")): add(p, p.relative_to(game))
for p in sorted((game / "assets" / "board-model").glob("*")): add(p, p.relative_to(game))   # small textures for the board's horses
# the 3D race view and what it loads in the game
add(view / "final-furlong.html", "final-furlong.html")
for f in ["horse-v2.js", "looks.js", "stand-styles.js", "race-sound.js", "uplift.js", "silks-paint.js"]: add(view / f, f)   # uplift.js: the soft look test (only loaded with ?uplift=soft)
for p in sorted((view / "assets" / "sound").glob("*")):        # the crowd and the horses (race-sound.js, 12 Nov)
    if p.suffix in (".mp3", ".json"): add(p, p.relative_to(view))
# (the style review page, race-view/styles.html, was live for the owner's choice on 7 Nov: today's trees and stand, a
# fresher light. It stays in the repo but is no longer published.)
A = view / "assets"
for f in ["silks-catalogue.json", "tint-mask.png"]: add(A / f, "assets/" + f)
for d in ["engine", "model", "model-v2", "trees", "baked"]:   # model-v2: the v2 horse, the race view's horse since 7 Nov (it reuses two of v1's maps)
    for p in sorted((A / d).glob("*")):
        if p.is_file(): add(p, p.relative_to(view))   # leafy and clay trees (the model look uses the clay ones: owner, 9 Nov)
for f in ["ascot.json", "ascot-view.json", "ascot-stalls.json", "ascot-standards.json", "ascot-planting.json", "ascot-site-dressing.json",
          "ad-boards.png", "lanes.png", "course-props.json", "course-props-geometry.txt", "planting_belts.json", "planting_belts-geometry.txt",
          "starting_stalls.json", "starting_stalls-geometry.txt", "starting_stalls_kit.json", "turf_detail.png"]:
    add(A / "course" / f, "assets/course/" + f)
for f in ["ascot_main_stand_crowd_areas.json", "crowd_palette.json", "crowd_people.json", "crowd_people-geometry.txt", "site_props_spots.json",
          "crowd_set_8.json", "crowd_set_8-geometry.txt",
          "crowd_set_12.json", "crowd_set_12-geometry.txt", "crowd_set_12_far.json", "crowd_set_12_far-geometry.txt"]:
    add(A / "architecture" / f, "assets/architecture/" + f)
# Newmarket's two courses in the race view (final-furlong.html?course=newmarket or ?course=newmarket-july; the game doesn't
# race there yet): each course's files (tools/course/newmarket/to_race_view.py) and the Blender pieces it places live
for c in ["newmarket", "newmarket-july"]:
    for f in [f"{c}.json", f"{c}-view.json", f"{c}-stalls.json", f"{c}-standards.json", f"{c}-scenery.json"]:
        add(A / "course" / f, "assets/course/" + f)
    gl = A / "course" / f"{c}-ground-light.jpg"            # the model look's baked ground light (bake_newmarket_ground.py)
    if gl.exists(): add(gl, "assets/course/" + gl.name)
for f in ["rowley_stands", "july_stands", "site_props", "finish_line"]:
    for g in [f + ".json", f + "-geometry.txt"]:
        add(A / "architecture" / g, "assets/architecture/" + g)
# the 3D silks and their icons: every set but the pattern catalogue's test swatches
for d in ["silks-3d", "silks-3d-v2", "silks-icons"]:
    for p in sorted((A / d).glob("*.png")):
        if not p.name.startswith("catalogue-"): add(p, p.relative_to(view))
# Every character outside plain ASCII in the pages, scripts and styles is written as an escape (\u00b7 in scripts,
# \0000b7 in styles, &#xb7; in page text), so the text reads the same however the browser guesses a file's encoding
# (owner, 7 Nov: "4YO+ Â· âš¥" on a Mac: a script read as Windows-1252 instead of UTF-8).
def js_esc(t):
    out = []
    for ch in t:
        o = ord(ch)
        if o < 128: out.append(ch)
        elif o < 0x10000: out.append("\\u%04x" % o)
        else: o -= 0x10000; out.append("\\u%04x\\u%04x" % (0xD800 + (o >> 10), 0xDC00 + (o & 0x3FF)))
    return "".join(out)
css_esc = lambda t: "".join(ch if ord(ch) < 128 else "\\%06x" % ord(ch) for ch in t)
html_esc = lambda t: "".join(ch if ord(ch) < 128 else "&#x%x;" % ord(ch) for ch in t)
def html_safe(t):
    out, pos = [], 0
    for m in re.finditer(r"(<script\b[^>]*>)(.*?)(</script>)|(<style\b[^>]*>)(.*?)(</style>)", t, re.S | re.I):
        out.append(html_esc(t[pos:m.start()]))
        out.append(m.group(1) + js_esc(m.group(2)) + m.group(3) if m.group(1) else m.group(4) + css_esc(m.group(5)) + m.group(6))
        pos = m.end()
    out.append(html_esc(t[pos:]))
    return "".join(out)
SAFE = {".js": js_esc, ".css": css_esc, ".html": html_safe}
for src, dst in take:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix in SAFE:
        dst.write_text(SAFE[src.suffix](src.read_text(encoding="utf-8")), encoding="ascii")
        shutil.copystat(src, dst)
    else:
        shutil.copy2(src, dst)
size = sum(d.stat().st_size for _, d in take)
print(f"{len(take)} files, {size / 1e6:.1f} MB in {out}")
