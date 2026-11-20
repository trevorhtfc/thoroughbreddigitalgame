"""Writes game/js/career/data.js: everything the career hub (career.html) reads, as one script.
  - the racing year: tools/calendar/calendar.json (the agreed draft calendar: 416 meetings, 2,836 races)
  - the week-by-week notes: tools/calendar/sheet.py (NOTES)
  - the stallions and mares: js/rules.js (PROFILE_ROWS, the board game's snapshot)
  - the rival stables: assets/newmarket/silks.json (the opposition silks and their tiers 1 to 4)
python3 game/tools/career_data.py"""
import ast, json, re, datetime as dt
from pathlib import Path
game = Path(__file__).resolve().parent.parent
repo = game.parent
J = json.load(open(repo / "tools/calendar/calendar.json"))
D = dt.date.fromisoformat
notes = ast.literal_eval(re.search(r"NOTES = (\{.*?\n\})", (repo / "tools/calendar/sheet.py").read_text(), re.S).group(1))

WINTER = [("Winter 1", "November"), ("Winter 2", "December"), ("Winter 3", "January"), ("Winter 4", "February"), ("Winter 5", "March")]
WSTART = [dt.date(2026, 11, 9), dt.date(2026, 12, 7), dt.date(2027, 1, 4), dt.date(2027, 2, 1), dt.date(2027, 3, 1)]
WEND = [dt.date(2026, 12, 6), dt.date(2027, 1, 3), dt.date(2027, 1, 31), dt.date(2027, 2, 28), dt.date(2027, 3, 21)]
def span(w):
    if w <= 33:
        a = dt.date(2026, 3, 23) + dt.timedelta(days=7 * (w - 1)); return a, a + dt.timedelta(days=6)
    return WSTART[w - 34], WEND[w - 34]
PHASE = lambda w: "Spring" if w <= 6 else "Early summer" if w <= 12 else "High summer" if w <= 22 else "Autumn" if w <= 30 else "Back end" if w <= 33 else "Winter"

fx = J["fixtures"]; idx = {(f["date"], f["course"]): i for i, f in enumerate(fx)}
meetings = [[f["date"], f["course"], f["meeting"], f["kind"], 1 if f["evening"] else 0, f["week"]] for f in fx]
races = []
for r in J["races"]:
    lo, hi = [int(x) for x in r["field"].split("–")]
    races.append([idx[(r["date"], r["course"])], r["time"], r["race"], r["type"], r["cls"], r["band"], r["ages"], r["sex"], r["f"], r["dist"],
                  1 if r["course_type"] == "Straight" else 0, r["prize"], lo, hi, r["ratings"], 1 if r["big"] else 0, r["note"]])
# the week's headline, as a racing fan would call it
TITLE = {1: "The Lincoln", 2: "All-Weather Finals Day", 3: "Spring gets going", 4: "The Craven Meeting", 5: "The Classic trials", 6: "The Guineas",
         7: "Chester's May Festival", 8: "The Dante and the Lockinge", 9: "Goodwood and the Temple Stakes", 10: "The Brigadier Gerard evening", 11: "The Derby",
         12: "The week before Ascot", 13: "Royal Ascot", 14: "The Northumberland Plate", 15: "The Eclipse", 16: "The July Festival", 17: "Super Sprint week",
         18: "The King George", 19: "Glorious Goodwood", 20: "The Shergar Cup", 21: "Hungerford Day", 22: "The Ebor Festival", 23: "The Celebration Mile",
         24: "The Sprint Cup", 25: "The St Leger", 26: "The Ayr Gold Cup", 27: "The Cambridgeshire", 28: "Sun Chariot Day", 29: "Future Champions",
         30: "Champions Day", 31: "The Futurity Trophy", 32: "Newmarket's Final Meeting", 33: "The November Handicap", 34: "Winter on the all-weather",
         35: "Christmas racing", 36: "New Year: everyone a year older", 37: "The Winter Derby", 38: "The last of winter"}
weeks = []
for w in range(1, 39):
    a, b = span(w)
    fw = [f for f in fx if f["week"] == w]
    heads = []
    for f in sorted(fw, key=lambda f: f["date"]):
        if f["kind"] in ("Festival", "Premier"):
            m = re.sub(r",? ?(day \d|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday).*$", "", f["meeting"].split(":")[0]).strip()
            m = m if f["course"].split(" ")[0] in m or "Royal Ascot" in m or "Glorious" in m else f"{m}, {f['course']}"
            if m not in heads: heads.append(m)
    g1 = [r["race"] for r in J["races"] if r["week"] == w and r["type"] == "Group 1"]
    label = f"Week {w}" if w <= 33 else WINTER[w - 34][0]
    weeks.append(dict(w=w, label=label, title=TITLE[w], a=a.isoformat(), b=b.isoformat(), phase=PHASE(w), note=notes.get(w, ""), heads=heads[:4], g1=g1,
                      n=len(fw), winter=w > 33))
courses = {k: dict(level=c["level"], surface=c["surface"], straight=c["straight"], standin=c["standin"], tier=c["tier"], region=c["region"], field=c["field"])
           for k, c in J["courses"].items()}

rules = (game / "js/rules.js").read_text()
rows = json.loads(re.search(r"const PROFILE_ROWS = (\[.*?\]);", rules, re.S).group(1))
retired = set(json.loads(re.search(r"const RETIRED = new Set\((\[.*?\])\)", rules).group(1)))
five = {"Night of Thunder", "No Nay Never"}          # 5 stars in the digital game (owner, 15 Nov)
stallions, mares = [], []
for row in rows:
    name, st, stars, base, opt, mn, mx, peak, ground, vers, fee, line, code, blocked = row.split("|")
    fee = int(re.sub(r"[^\d]", "", fee) or 0)
    rec = dict(name=name, stars=5 if name in five else int(stars), opt=opt, min=mn, max=mx, peak=peak, ground=ground.split("/"), fee=fee)
    if st == "1":
        if name not in retired: stallions.append(rec)
    else: mares.append(rec)
A = json.loads(re.search(r"const NAME_A = (\[.*?\]);", rules).group(1)); B = json.loads(re.search(r"const NAME_B = (\[.*?\]);", rules).group(1))
silks = json.load(open(game / "assets/newmarket/silks.json"))
rivals = [dict(name=s["name"], tier=s["tier"], pic=s["menu"], silk=s["id"]) for s in silks["silks"]]   # silk: its 3D colours in the race view (assets/silks-3d/<id>.png)

out = dict(weeks=weeks, meetings=meetings, races=races, courses=courses, stallions=stallions, mares=mares, rivals=rivals, nameA=A, nameB=B)
text = "// Built by game/tools/career_data.py from tools/calendar/calendar.json, js/rules.js and the silks. Don't edit by hand.\nwindow.CAREER_DATA = " + json.dumps(out, separators=(",", ":"), ensure_ascii=False) + ";\n"
(game / "js/career/data.js").write_text(text)
print("data.js", len(text), len(weeks), "weeks", len(meetings), "meetings", len(races), "races", len(stallions), "stallions", len(mares), "mares", len(rivals), "rivals")
