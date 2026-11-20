"""Builds the career hub (prototype): game/career.html from game/src/career.src.html (the icons and the horse mark
dropped in, as tools/build.py does for the game's own page) and game/js/career/data.js (tools/career_data.py).
The hub loads the game's own board (js/board.js, js/life.js: run tools/build.py first if their sources changed).

python3 game/tools/build_career.py"""
import base64, json, re, runpy
from pathlib import Path
here = Path(__file__).resolve().parent.parent
src = here / "src"
runpy.run_path(str(here / "tools" / "career_data.py"))
icons = json.load(open(src / "icons.json"))
def icon(m):
    if m.group(1) not in icons: raise SystemExit(f"no icon {m.group(1)}")
    return icons[m.group(1)]
page = (src / "career.src.html").read_text()
page = page.replace("%%HORSE%%", "data:image/png;base64," + base64.b64encode((src / "horse-mark.png").read_bytes()).decode())
# only the icons the hub's screens use (js/career/ui.js: ico("...") and the to-do icons)
ui = (here / "js" / "career" / "ui.js").read_text()
used = sorted(set(re.findall(r'ico\("([a-z-]+)"\)', ui)) | set(re.findall(r'[a-z]+: "([a-z-]+)"', re.search(r"const TDI = \{(.*?)\}", ui).group(1))))
for k in used:
    if k not in icons: raise SystemExit(f"no icon {k}")
page = page.replace("%%ICONSET%%", ", ".join(f'"{k}": `{icons[k]}`' for k in used))
page = re.sub(r"%%ICON:([a-z-]+)%%", icon, page)
assert not re.findall(r"%%[A-Z]+[^%]*%%", page)
(here / "career.html").write_text(page)
print("career.html", len(page))
