"""Builds the game from game/src/: index.html (the page, with the icons and the horse mark dropped in), js/board.js
(the Newmarket board, with the places' outlines) and js/life.js (the 3D life on the board).
Icons: game-icons.net (CC BY 3.0), copied into src/icons.json from the @iconify-json/game-icons package.

python3 game/tools/build.py"""
import base64, json, re
from pathlib import Path
here = Path(__file__).resolve().parent.parent
src = here / "src"
icons = json.load(open(src / "icons.json"))
def icon(m):
    name = m.group(1)
    if name not in icons: raise SystemExit(f"no icon {name}")
    return icons[name]
mark = "data:image/png;base64," + base64.b64encode((src / "horse-mark.png").read_bytes()).decode()
sites = json.dumps(json.load(open(src / "sites.json")), separators=(",", ":"))

page = (src / "index.src.html").read_text()
page = page.replace("%%HORSE%%", mark)
page = page.replace("%%ICONSET%%", ", ".join(f'"{k}": `{v}`' for k, v in icons.items()))
page = re.sub(r"%%ICON:([a-z-]+)%%", icon, page)
board = (src / "board.src.js").read_text().replace("%%SITES%%", sites)
board = re.sub(r"%%ICON:([a-z-]+)%%", icon, board)
life = (src / "life.src.js").read_text()
for name, text in [("index.html", page), ("js/board.js", board), ("js/life.js", life)]:
    left = re.findall(r"%%[A-Z]+[^%]*%%", text)
    assert not left, (name, left[:3])
    (here / name).write_text(text)
    print(name, len(text))
