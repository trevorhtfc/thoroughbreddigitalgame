import html
OUT = "/home/claude/thoroughbreddigitalgame/reference/web/compare/index.html"
VIEWS = [
  ("tower", "The clock tower, close", "Eye 7 m up on the lawn, 28 m in front of the stand",
   ["New belfry tower, iron lace bay and stair blocks", "Striped awnings and pastel doors along the base", "Skittle crowd on every balcony"],
   ["Balustrades: the race view draws the light version of the stand, so the white balusters along each floor are missing", "Windows and glazing bars read softer and flatter"]),
  ("across", "Across the track", "Eye 14 m up on the far side, 80 m from the stand",
   ["The whole new stand: terraces, canopies, tower, flags", "Soft, warm light and the pale sky", "Beige ground beyond the far rail"],
   ["Mown lanes: crisp in the study, barely visible in the race view", "Stand detail softer at this distance"]),
  ("lawn", "From the lawn", "Eye 3 m up among the crowd by the rail",
   ["Gentlemen in black tops and tails, about half the crowd", "Ascot rail with its broad white board", "Awnings and flags"],
   ["Turf texture: the study's grass has depth; the race view's is smooth", "Balustrades on the upper floors"]),
  ("wing", "The east wing from above", "Eye 30 m up, looking back along the stand",
   ["Grand canopy roof carried along the stand", "Terraces packed with people", "Flags along the roof ridge"],
   ["Mown lanes clear in the study, faint in the race view", "The race view adds the enclosure dressing (tents, judge's box) that the study leaves out"]),
  ("track", "Low across the track", "Eye 3.2 m up on the inside rail",
   ["Stand, crowd and rail all read as in the study"],
   ["The biggest gap: the study's turf has real 3D blades and strong lanes; the race view's looks like a flat green floor", "The horses are in the study shot, not the race view's at this moment"]),
  ("fromstand", "From the stand to the infield", "Eye 16 m up on the stand, looking out",
   ["Clay trees with clustered crowns", "Beige-brown ground beside the track"],
   ["Copper beeches come up more often than in the study", "Turf lanes missing", "The race view shows the infield enclosures the study leaves out"]),
  ("belt", "Down the straight mile", "Eye 6 m up, 690 m east of the winning post",
   ["Clay trees and hedge along the planting belt"],
   ["Lanes: strong in the study, absent in the race view (this stretch is beyond the baked ground)", "No beige ground out here in the race view", "Tree trunks hidden by the hedge"]),
]
GAME = [("stand", "Before the race: the stand"), ("finish", "The finish replay"), ("trees", "The enclosures and trees")]
GAPS = [
  ("Turf", "Crisp mown lanes, visible tufts, real 3D grass blades", "Faint soft lanes, a fine grain close up; reads flat", "Biggest gap",
   "Sharpen the lanes into proper bands (re-bake of the ground, about 12 minutes) and add a few layers of short grass near the camera (a standard trick for games: cheap, gives the turf depth)."),
  ("Stand detail", "Full-detail model: balustrades, glazing bars, sharp shadow lines", "The light version of the stand; light baked into one image for 500 m of building", "Clear gap",
   "Use the full-detail stand for the stretch the cameras see close (about 330 m round the post) with its own sharper light images; phones keep the light one."),
  ("Light and colour", "Soft warm sun, pastel sky, matte clay", "Same light baked in; same colour handling", "Close", "Small tuning only."),
  ("Crowd", "Skittle 1C figures, half in black tops and tails", "The same figures and colours", "Close", "Nothing needed."),
  ("Trees and hedge", "Clay clustered crowns, dark leafy hedge", "Same trees, a touch brighter; copper beeches too frequent", "Close", "Fewer copper beeches; slightly deeper greens."),
  ("Beige ground", "Beige beside the track everywhere", "Only where the ground is baked (the last two furlongs)", "Partly", "Carry it on along the rest of the course."),
]

def img(n, kind, label):
    return f'''<figure class="shot {kind}"><a href="img/{n}-{kind}.jpg" target="_blank" rel="noopener"><img src="img/{n}-{kind}.jpg" alt="{html.escape(label)}" loading="lazy" width="1280" height="720"></a><figcaption><span class="chip {kind}">{label}</span></figcaption></figure>'''

sections = []
for i, (n, title, eye, good, gap) in enumerate(VIEWS, 1):
    sections.append(f'''<section class="view" id="{n}">
  <header class="vh"><h2>{html.escape(title)}</h2><p class="eye">{html.escape(eye)}</p></header>
  <div class="trio">{img(n, "before", "Race view · yesterday")}{img(n, "now", "Race view · now")}{img(n, "study", "Blender study")}</div>
  <div class="notes">
    <div><h3>Came across</h3><ul>{"".join(f"<li>{html.escape(g)}</li>" for g in good)}</ul></div>
    <div><h3 class="miss">Still short of the study</h3><ul>{"".join(f"<li>{html.escape(g)}</li>" for g in gap)}</ul></div>
  </div>
</section>''')
game = "".join(f'''<section class="view duo-v" id="{n}"><header class="vh"><h2>{html.escape(t)}</h2><p class="eye">Game camera</p></header><div class="duo">{img(n, "before", "Race view · yesterday")}{img(n, "now", "Race view · now")}</div></section>''' for n, t in GAME)
rows = "".join(f'''<tr><th scope="row">{a}</th><td>{b}</td><td>{c}</td><td><span class="state s{['Close','Partly','Clear gap','Biggest gap'].index(d)}">{d}</span></td><td>{e}</td></tr>''' for a, b, c, d, e in GAPS)

page = f'''<title>Race View vs Study</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Source+Sans+3:wght@400;600&display=swap">
<style>
/* Layout: a racecard-like run of camera positions, each a row of three frames (yesterday, now, target), notes beneath; a gap table at the top. */
:root {{
  --bg: #f3f4f1; --panel: #ffffff; --ink: #1d2420; --soft: #5b655f; --rule: #d9ddd6;
  --green: #1f5a3a; --before: #8a8f8a; --now: #1f6b45; --study: #3b5f86; --warn: #a5582c; --chip-ink: #ffffff;
  --display: "Barlow Condensed", "Arial Narrow", sans-serif; --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #151916; --panel: #1d221f; --ink: #e7ebe6; --soft: #a3aca5; --rule: #323a35;
  --green: #7fc29b; --before: #9aa09a; --now: #6fc596; --study: #8fb3dc; --warn: #e39a6b; --chip-ink: #151916; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #151916; --panel: #1d221f; --ink: #e7ebe6; --soft: #a3aca5; --rule: #323a35;
  --green: #7fc29b; --before: #9aa09a; --now: #6fc596; --study: #8fb3dc; --warn: #e39a6b; --chip-ink: #151916; color-scheme: dark }}
body {{ background: var(--bg); color: var(--ink); font: 400 16px/1.55 var(--body); }}
.wrap {{ max-width: 1440px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 32px 64px; display: grid; gap: 40px; }}
h1, h2, h3, .chip, th, .state {{ font-family: var(--display); }}
h1 {{ font-size: clamp(2.2rem, 5vw, 3.4rem); font-weight: 700; line-height: 1; margin: 0; letter-spacing: .01em; text-wrap: balance; }}
.intro {{ display: grid; gap: 14px; max-width: 70ch; }}
.intro p {{ margin: 0; color: var(--soft); }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px 18px; }}
.chip {{ display: inline-block; font-size: .95rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; padding: 2px 8px; border-radius: 3px; color: var(--chip-ink); }}
.chip.before {{ background: var(--before); }} .chip.now {{ background: var(--now); }} .chip.study {{ background: var(--study); }}
.verdict {{ background: var(--panel); border: 1px solid var(--rule); border-radius: 6px; padding: 20px; display: grid; gap: 12px; }}
.verdict h2 {{ margin: 0; font-size: 1.7rem; }}
.verdict p {{ margin: 0; max-width: 75ch; }}
.tablewrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; min-width: 760px; font-size: .95rem; }}
th, td {{ text-align: left; vertical-align: top; padding: 10px 12px; border-top: 1px solid var(--rule); }}
thead th {{ font-size: .9rem; letter-spacing: .08em; text-transform: uppercase; color: var(--soft); font-weight: 600; border-top: 0; }}
tbody th {{ font-size: 1.15rem; font-weight: 600; white-space: nowrap; }}
.state {{ font-weight: 600; letter-spacing: .05em; text-transform: uppercase; font-size: .9rem; white-space: nowrap; padding: 1px 7px; border-radius: 3px; border: 1.5px solid currentColor; }}
.s0 {{ color: var(--now); }} .s1 {{ color: var(--study); }} .s2 {{ color: var(--warn); }} .s3 {{ color: var(--warn); background: color-mix(in srgb, var(--warn) 14%, transparent); }}
.view {{ display: grid; gap: 14px; padding-top: 28px; border-top: 2px solid var(--ink); }}
.vh {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 16px; }}
.vh h2 {{ margin: 0; font-size: 1.9rem; font-weight: 700; }}
.eye {{ margin: 0; color: var(--soft); font-size: .95rem; }}
.trio {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }}
.duo {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; max-width: 1100px; }}
.shot {{ margin: 0; display: grid; gap: 6px; }}
.shot img {{ display: block; width: 100%; height: auto; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 3px; background: var(--rule); }}
.shot a:focus-visible {{ outline: 3px solid var(--green); outline-offset: 2px; }}
.notes {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 24px; max-width: 1100px; }}
.notes h3 {{ margin: 0 0 4px; font-size: 1.1rem; letter-spacing: .06em; text-transform: uppercase; color: var(--now); }}
.notes h3.miss {{ color: var(--warn); }}
.notes ul {{ margin: 0; padding-left: 1.1em; display: grid; gap: 3px; }}
.part {{ font-size: 1.1rem; letter-spacing: .1em; text-transform: uppercase; color: var(--soft); margin: 0; font-family: var(--display); font-weight: 600; }}
@media (max-width: 760px) {{ .trio, .duo, .notes {{ grid-template-columns: 1fr; }} }}
</style>
<div class="wrap">
  <div class="intro">
    <h1>Race view against the study</h1>
    <p>Each camera below is shot three ways from exactly the same spot: the race view as it was yesterday, the race view now, and the Blender study we built today, which is the target. Click any frame to open it full size.</p>
    <div class="legend"><span class="chip before">Race view · yesterday</span><span class="chip now">Race view · now</span><span class="chip study">Blender study</span></div>
  </div>
  <div class="verdict">
    <h2>Where it stands</h2>
    <p>The stand, the crowd, the light and the trees have come across well: side by side, the race view now looks like the study in shape, colour and mood. The turf has not. In the study the track has crisp mown lanes and real depth; in the race view it is still a smooth green floor with faint stripes. The stand is also softer than the study's, because the race view draws its lighter version without the balustrades.</p>
    <div class="tablewrap"><table>
      <thead><tr><th>Part</th><th>Blender study</th><th>Race view now</th><th>Match</th><th>To close the gap</th></tr></thead>
      <tbody>{rows}</tbody>
    </table></div>
  </div>
  <p class="part">The study's cameras</p>
  {"".join(sections)}
  <p class="part">Game cameras (no study render)</p>
  {game}
</div>
'''
open(OUT, "w").write(page)
print("ok", len(page))
