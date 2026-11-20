"""The generic courses' front page (race-view/generic.html): the ten courses as cards, each with its overview still,
its facts and the real courses it stands in for, linking to the course's own page (race-view/<id>.html, test_page.py).

  python3 tools/course/generic/index_page.py
"""
import html, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RV = REPO / "race-view"
IDS = [f"gen-{f}-{h}-{s}" for f in ("park", "tight", "ring", "hill", "downs") for h in "lr" for s in ("big", "small")] + ["gen-ring-l-us"]


def main():
    SI = json.loads((REPO / "courses/generic/stand-ins.json").read_text())["courses"]
    cards = []
    for cid in IDS:
        C = json.loads((REPO / f"tools/course/real/{cid}.json").read_text())
        f = C["facts"]
        real = [n for n, v in SI.items() if v["generic"] == cid]
        starts = ", ".join(k.replace(" (round)", " round") for k in C["starts"])
        cards.append(f"""    <a class="card" href="{cid}.html">
      <img src="{cid}-card.jpg" alt="{html.escape(C["name"])}, the stands" loading="lazy">
      <div class="body">
        <h2>{html.escape(C['name'])}</h2>
        <p class="mix">{html.escape(C.get('mix', ''))} · {html.escape(f['kind'])}</p>
        <p class="facts">About {f['circuit f']}f round · {f['run-in f']}f run-in · starts {html.escape(starts)}</p>
        <p class="for"><b>Races</b> {html.escape(', '.join(real) or '—')}</p>
      </div>
    </a>""")
    page = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thoroughbred: the generic courses</title>
<style>
  :root {{ --ink: #1f2a22; --muted: #5d6a60; --paper: #f5efe1; --card: #fffaf0; --line: #d9ceb4; --green: #2f5a3a; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--paper); color: var(--ink); font: 15px/1.5 Georgia, "Times New Roman", serif; }}
  header {{ max-width: 1180px; margin: 0 auto; padding: 36px 20px 8px; }}
  .eyebrow {{ font: 600 12px/1 system-ui, sans-serif; letter-spacing: .12em; text-transform: uppercase; color: var(--green); }}
  h1 {{ font-size: 34px; margin: 10px 0 8px; font-weight: 600; }}
  .lede {{ color: var(--muted); max-width: 820px; margin: 0; }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 20px; display: grid; gap: 18px; grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); }}
  .card {{ display: block; background: var(--card); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; color: inherit; text-decoration: none; transition: transform .15s, box-shadow .15s; }}
  .card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(40,30,10,.12); }}
  .card img {{ display: block; width: 100%; aspect-ratio: 16 / 9; object-fit: cover; background: #dfe6d6; }}
  .body {{ padding: 12px 16px 16px; }}
  h2 {{ font-size: 19px; margin: 0 0 2px; font-weight: 600; }}
  .mix {{ margin: 0 0 8px; color: var(--green); font: 600 12px/1.4 system-ui, sans-serif; letter-spacing: .03em; }}
  .facts, .for {{ margin: 4px 0 0; font: 13px/1.45 system-ui, sans-serif; color: var(--muted); }}
  .for b {{ color: var(--ink); font-weight: 600; }}
  footer {{ max-width: 1180px; margin: 0 auto; padding: 8px 20px 40px; color: var(--muted); font: 13px/1.5 system-ui, sans-serif; }}
</style>
</head>
<body>
<header>
  <div class="eyebrow">Thoroughbred · race view · draft</div>
  <h1>The generic courses</h1>
  <p class="lede">Five kinds of course, each built both ways round and with a bigger and a smaller stand side, so every
  course without its own build can be raced for now; and the Ring dressed as an American track (a dirt track round its
  turf course) for the Breeders' Cup turf races. Each has its own track drawn from a few numbers, its own ground (flat, an uphill finish, or the rolling downs),
  old small stands and pavilions clustered round the winning post near the end of the straight, the
  festival opposite them, and the usual belts
  of trees and boards round the edge. Open a course, then pick a race.</p>
</header>
<main>
{chr(10).join(cards)}
</main>
<footer>The tracks, ground and dressing come from tools/course/generic/ (specs.py, dressing.py) on the claude/generic-courses
branch. Which real course races on which generic course: courses/generic/stand-ins.json.</footer>
</body>
</html>
"""
    (RV / "generic.html").write_text(page)
    print("wrote", RV / "generic.html")


if __name__ == "__main__":
    main()
