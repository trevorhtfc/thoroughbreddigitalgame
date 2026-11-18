"""A tier 2 course's test page, race-view/<id>.html (Epsom's page, race-view/epsom.html, made general): a still at the
top, the course's races as a card, the going and field size carried into each race's link.

  python3 tools/course/real/test_page.py <id> <still.jpg> "<caption>"
"""
import json, re, shutil, sys, html
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RV = REPO / "race-view"

def main(cid, still, caption):
    C = json.loads((REPO / f"tools/course/real/{cid}.json").read_text())
    V = C.get("view", {})
    page = (RV / "epsom.html").read_text()
    name = C["name"]
    shutil.copy(still, RV / f"{cid}-hero.jpg")
    hand = "left-handed" if C["hand"] < 0 else "right-handed"
    lede = V.get("lede", f"{name}'s track in 3D, {hand}, on its real outline (OpenStreetMap) and real ground (AWS Terrain Tiles). "
                         "A draft with the basic surroundings every tier 2 course shares: boards round the outside 20 m off the "
                         "track, a belt of trees behind them, boards and a looser belt round the infield, the stand side kept "
                         "clear for its stands (a rail crowd for now) and the run-in's infield kept open for the festival.")
    desc = {"straight": "The straight course", "mile": "The round mile, from the chute", "round": "Round the course",
            "loop": "From the home straight, once round"}
    desc.update(V.get("routeWords", {}))
    feat = set(V.get("feature", []))
    links = []
    for t, s in C["starts"].items():
        rid = re.sub(r"\s*\((\w+)\)", r"-\1", t).strip()
        cls = "race feature" if t in feat else "race"
        links.append(f'      <a class="{cls}" data-race="{html.escape(rid)}" href="final-furlong.html?course={cid}&race={html.escape(rid)}">'
                     f'<b>{html.escape(t.replace(" (round)", ""))}</b><span>{html.escape(s.get("words", desc.get(s["route"], s["route"])))}</span></a>')
    page = page.replace("<title>Epsom Racing</title>", f"<title>{name} Racing</title>")
    page = re.sub(r'<div class="eyebrow">.*?</div>', f'<div class="eyebrow">{name} · race view · draft</div>', page, flags=re.S)
    page = re.sub(r"<h1>.*?</h1>", f"<h1>{name} Racing</h1>", page, flags=re.S)
    page = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{html.escape(lede)}</p>', page, flags=re.S)
    page = re.sub(r'<img src="[^"]+" alt="[^"]*">', f'<img src="{cid}-hero.jpg" alt="{html.escape(caption)}">', page)
    page = re.sub(r"<figcaption>.*?</figcaption>", f"<figcaption>{html.escape(caption)}</figcaption>", page, flags=re.S)
    page = re.sub(r'(<nav class="races" id="races" aria-label="Races">\n).*?(\n    </nav>)', lambda m: m.group(1) + "\n".join(links) + m.group(2), page, flags=re.S)
    notes = V.get("notes", [
        ["The real track.", f"OpenStreetMap's outline of the turf, the starts where At The Races' diagram puts them, and the ground under every route for the race engine."],
        ["The basic rules.", "Boards 20 m off the track round the outside, a belt of trees from 25 m, thinner trees to 110 m; boards and a looser belt round the infield; the stand side and the run-in's infield kept clear for the stands and the festival."],
        ["The cameras.", "The start camera, the tracking car round the course and along the straight, the stand camera for the last two furlongs, the head-on for straight races, and the replay."],
        ["Running slowly?", "Choose Medium or Low under Quality in the race view's bar. Auto steps down by itself."]])
    page = re.sub(r'(<div class="notes">\n).*?(\n    </div>)', lambda m: m.group(1) + "\n".join(
        f"      <p><strong>{html.escape(a)}</strong> {html.escape(b)}</p>" for a, b in notes) + m.group(2), page, flags=re.S)
    page = page.replace("course=epsom", f"course={cid}").replace('"ep-going"', f'"{cid[:2]}-going"').replace('"ep-runners"', f'"{cid[:2]}-runners"')
    assert "epsom" not in page.lower(), [l for l in page.splitlines() if "epsom" in l.lower()]
    (RV / f"{cid}.html").write_text(page)
    print("wrote", RV / f"{cid}.html")

if __name__ == "__main__":
    main(*sys.argv[1:4])
