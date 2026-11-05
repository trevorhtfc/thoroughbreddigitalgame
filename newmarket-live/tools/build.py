"""Builds index.html from index.src.html: drops in the icon paths (game-icons.net, CC BY 3.0) and the
galloping-horse mark (a silhouette of the 3D race horse, tools/horse-mark.png)."""
import base64, json, re, sys
from pathlib import Path
here = Path(__file__).resolve().parent.parent
icons = json.load(open(here / "tools" / "icons.json"))
src = (here / "index.src.html").read_text()
mark = base64.b64encode((here / "tools" / "horse-mark.png").read_bytes()).decode()
src = src.replace("%%HORSE%%", "data:image/png;base64," + mark)
def icon(m):
    name = m.group(1)
    if name == "two-coins" or name == "coins": name = "two-coins"
    return icons[name]
src = re.sub(r"%%ICON:([a-z-]+)%%", icon, src)
assert "%%" not in src, re.findall(r"%%[^%]+%%", src)
(here / "index.html").write_text(src)
print("index.html", len(src))
