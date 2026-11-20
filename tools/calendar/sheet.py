"""Writes calendar.xlsx (the tabs of the racing-calendar Sheet) from calendar.json."""
import json, datetime as dt
from pathlib import Path
HERE = Path(__file__).resolve().parent
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

J = json.load(open(HERE / "calendar.json"))
R, FX, CRS = J["races"], J["fixtures"], J["courses"]
D = dt.date.fromisoformat
HEAD = PatternFill("solid", fgColor="EDEBE4")
WRAP = Alignment(wrap_text=True, vertical="top")
TOP = Alignment(vertical="top")
GBP = '£#,##0'
SEX = {"F": "Fillies", "C": "Colts & geldings", "CF": "Colts & fillies", "": ""}
GSHORT = {"Group 1": "G1", "Group 2": "G2", "Group 3": "G3", "Listed": "Listed", "Heritage handicap": "Heritage hcap",
          "Handicap": "Handicap", "Conditions": "Conditions", "Sales race": "Sales race", "Maiden": "Maiden"}

wb = Workbook()

def table(ws, top, headers, rows, widths, wrap_cols=(), money_cols=(), date_cols=()):
    for j, h in enumerate(headers):
        c = ws.cell(row=top, column=j + 1, value=h)
        c.fill = HEAD
        c.font = Font(bold=True)
        c.alignment = WRAP
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = ws.cell(row=top + 1 + i, column=j + 1, value=v)
            h = headers[j]
            c.alignment = WRAP if h in wrap_cols else TOP
            if h in money_cols and isinstance(v, (int, float)):
                c.number_format = GBP
            if h in date_cols:
                c.number_format = "ddd d mmm yyyy"
    for j, w in enumerate(widths):
        ws.column_dimensions[get_column_letter(j + 1)].width = w
    ws.freeze_panes = ws.cell(row=top + 1, column=1)

def wk_label(w):
    return f"Week {w}" if w <= 33 else ["Winter 1 (Nov)", "Winter 2 (Dec)", "Winter 3 (Jan)", "Winter 4 (Feb)", "Winter 5 (Mar)"][w - 34]

# ------------------------------------------------------------------ Season
ws = wb.active
ws.title = "Season"
types = Counter(r["type"] for r in R)
summary = [
    "Thoroughbred, career mode: the racing year (draft, 20 Nov 2026)",
    "33 turf weeks, Monday 23 March to Sunday 8 November 2026, then five winter all-weather turns, November to March.",
    f"{len(FX)} meetings and {len(R):,} races: {types['Group 1']} Group 1s, {types['Group 2']} Group 2s, {types['Group 3']} Group 3s, "
    f"{types['Listed']} Listed races, {types['Heritage handicap']} heritage handicaps, and {len(R) - sum(types[t] for t in ['Group 1','Group 2','Group 3','Listed','Heritage handicap']):,} everyday races.",
    "Every big race is real and on its real 2026 date. The everyday meetings are each course's real season, scaled down to about a third of the real number.",
]
for i, s in enumerate(summary):
    c = ws.cell(row=i + 1, column=1, value=s)
    if i == 0:
        c.font = Font(bold=True, size=13)
NOTES = {
    1: "Turf season opens with the Lincoln. The first two-year-old race of the year, the Brocklesby (5f).",
    2: "Good Friday: the All-Weather Championships Finals at Newcastle, for horses that qualified over the winter.",
    4: "The Classic trials begin: the Craven Meeting and Greenham Day.",
    5: "Derby and Guineas trials at Epsom and Sandown; the Sandown Mile.",
    6: "The first Classics: the 2000 and 1000 Guineas. Two-year-olds can now run over 6f.",
    7: "Chester's May Festival: Derby and Oaks trials round the tight Roodee.",
    8: "The Dante (York) and the Lockinge (Newbury), the first Group 1 for older horses.",
    9: "Goodwood's May Festival and Haydock's Temple Stakes.",
    11: "The Derby and the Oaks at Epsom. Handicaps open to three-year-olds and older together from June.",
    12: "Two-year-olds can now run over 7f.",
    13: "Royal Ascot: eight Group 1s in five days.",
    14: "The Northumberland Plate. Newmarket switches to the July Course until the end of August.",
    15: "The Eclipse: the Classic generation meets its elders for the first time.",
    16: "The July Festival. Nurseries (two-year-old handicaps) start.",
    18: "The King George at Ascot, the richest race of the year.",
    19: "Glorious Goodwood: the Sussex, the Nassau and the Goodwood Cup.",
    20: "The Shergar Cup and Brighton's festival.",
    22: "The Ebor Festival at York: the International, the Yorkshire Oaks, the Nunthorpe, the Ebor. Two-year-olds now run up to a mile.",
    24: "The Sprint Cup at Haydock.",
    25: "The St Leger, the last Classic, in its 250th year.",
    26: "The Ayr Gold Cup and the Mill Reef.",
    27: "The Cambridgeshire Meeting: the Middle Park and Cheveley Park, two-year-old Group 1s.",
    28: "Sun Chariot Day. Tattersalls October Yearling Sale time.",
    29: "Future Champions: the Dewhurst, the Fillies' Mile and the Cesarewitch.",
    30: "British Champions Day at Ascot: the season's finale for the stars.",
    31: "The Futurity Trophy at Doncaster: next year's Derby horses.",
    32: "Newmarket's Final Meeting. Two-year-olds now run up to 1m2f.",
    33: "The November Handicap: the last big race on turf.",
    34: "Winter on the all-weather: Listed races at Kempton and Lingfield. Horses in training sale.",
    35: "Lingfield's Quebec Stakes; Boxing Day at Wolverhampton. December mares sale.",
    36: "1 January: every horse turns a year older. Two-year-olds are now three. Breeding season.",
    37: "Lingfield's winter features and the Winter Derby.",
    38: "Last winter turn: AW qualifiers close for Finals Day. The turf season is a week away.",
}
weeks = sorted({r["week"] for r in R})
rows = []
for w in weeks:
    rw = [r for r in R if r["week"] == w]
    fw = [f for f in FX if f["week"] == w]
    first = min(D(f["date"]) for f in fw)
    mon = first - dt.timedelta(days=first.weekday())
    if w >= 34:
        mon = [dt.date(2026, 11, 9), dt.date(2026, 12, 7), dt.date(2027, 1, 4), dt.date(2027, 2, 1), dt.date(2027, 3, 1)][w - 34]
    heads = []
    for f in sorted(fw, key=lambda f: f["date"]):
        if f["kind"] in ("Festival", "Premier"):
            m = f["meeting"].split(",")[0].replace(" day 1", "").replace(" day 2", "").replace(" day 3", "")
            label = f"{m} ({f['course']})" if f["course"] not in m else m
            if label not in heads:
                heads.append(label)
    g1 = [r["race"] for r in rw if r["type"] == "Group 1"]
    juv = sorted({r["f"] for r in rw if r["ages"] == "2yo"})
    def fl(f):
        return {5.5: "5½f"}.get(f, f"{int(f)}f" if f < 8 else ("1m" if f == 8 else "1m2f" if f == 10 else f"{f}f"))
    rows.append([wk_label(w), mon, rw[0]["phase"], "; ".join(heads[:5]), ", ".join(g1),
                 sum(r["type"] in ("Group 1", "Group 2", "Group 3", "Listed") for r in rw),
                 sum(r["type"] == "Heritage handicap" for r in rw), len(fw), len(rw),
                 (f"{fl(juv[0])}–{fl(juv[-1])}" if len(juv) > 1 else fl(juv[0])) if juv else "none",
                 NOTES.get(w, "")])
table(ws, 6, ["Week", "Starts", "Phase", "Big meetings", "Group 1s", "Group and Listed races", "Heritage handicaps",
              "Meetings", "Races", "Two-year-old trips", "What's happening"], rows,
      [15, 15, 14, 46, 40, 11, 11, 10, 8, 12, 60], wrap_cols=("Big meetings", "Group 1s", "What's happening"),
      date_cols=("Starts",))

# ------------------------------------------------------------------ Big races
ws = wb.create_sheet("Big races")
big = [r for r in R if r["big"]]
rows = [[wk_label(r["week"]), D(r["date"]), r["course"], r["race"], GSHORT[r["type"]], r["dist"], r["ages"], SEX[r["sex"]],
         r["prize"], r["meeting"], r["note"]] for r in big]
table(ws, 1, ["Week", "Date", "Course", "Race", "Grade", "Distance", "Ages", "Sex", "Prize to winner", "Meeting", "Note"],
      rows, [15, 17, 15, 38, 13, 10, 8, 16, 14, 36, 50], wrap_cols=("Note",), money_cols=("Prize to winner",),
      date_cols=("Date",))

# ------------------------------------------------------------------ Every race
ws = wb.create_sheet("Every race")
rows = [[wk_label(r["week"]), D(r["date"]), r["course"], r["time"], r["race"], GSHORT.get(r["type"], r["type"]),
         r["cls"], r["band"] or None, r["ages"], SEX[r["sex"]] or None, r["dist"], r["course_type"], r["prize"], r["field"],
         r["ratings"], r["meeting"], r["note"] or None, r["id"]] for r in R]
table(ws, 1, ["Week", "Date", "Course", "Time", "Race", "Type", "Class", "Band", "Ages", "Sex", "Distance", "Straight or round",
              "Prize to winner", "Runners", "Ratings in the field", "Meeting", "Note", "Race id"],
      rows, [15, 17, 15, 7, 40, 14, 7, 8, 7, 15, 10, 10, 13, 9, 14, 36, 50, 34], money_cols=("Prize to winner",),
      date_cols=("Date",))

# ------------------------------------------------------------------ Meetings
ws = wb.create_sheet("Meetings")
rows = []
for f in FX:
    rs = [r for r in R if r["date"] == f["date"] and r["course"] == f["course"]]
    c = CRS[f["course"]]
    bigs = [r["race"] for r in rs if r["type"] in ("Group 1", "Group 2", "Group 3", "Listed", "Heritage handicap", "Sales race")]
    rows.append([wk_label(f["week"]), D(f["date"]), f["course"], f["meeting"], f["kind"], c["surface"], len(rs),
                 ", ".join(bigs) or None, rs[0]["track"] if f["course"] == "Newmarket" else None,
                 c["standin"] or None, c["tier"]])
table(ws, 1, ["Week", "Date", "Course", "Meeting", "Kind", "Surface", "Races", "Big races on the card", "Track",
              "Races on until built", "Course build tier"], rows,
      [15, 17, 16, 40, 12, 12, 7, 60, 12, 14, 18], wrap_cols=("Big races on the card",), date_cols=("Date",))

# ------------------------------------------------------------------ Race types
ws = wb.create_sheet("Race types")
RT = [
    ["Group 1", "The best horses. Conditions by age and sex only (no rating limit)", "Class 1", "Classics April to September; two-year-old Group 1s September and October",
     "6–14", "£200,000 to £1.1m", "The career's peaks. A Group 1 win makes a stallion or a top broodmare"],
    ["Group 2", "Top horses just below the very best; penalties for earlier Group winners", "Class 1", "All season; many are trials for a Group 1", "6–12", "£60,000–£120,000", "Black type: adds stud value"],
    ["Group 3", "Good horses; penalties for Group winners", "Class 1", "All season", "6–12", "£35,000–£80,000", "Black type"],
    ["Listed", "Useful horses, roughly rated 95+", "Class 1", "All season, winter too", "5–11", "£18,000–£50,000", "The first rung of black type: a big boost for a filly's stud value"],
    ["Heritage handicap", "Rated about 85–108 (0-105 or 0-110)", "Class 2", "March to November, mostly at the festivals", "16–30", "£40,000–£300,000",
     "Big fields, big betting heats. The prize for spotting a horse that is better than its mark"],
    ["Handicap, Class 2", "Rated up to 100 or 105", "0-105 / 0-100", "All season at the big courses", "8–24", "£15,000", "Where good handicappers live"],
    ["Handicap, Class 3", "Rated up to 90 or 95", "0-95 / 0-90", "All season", "8–16", "£8,000", ""],
    ["Handicap, Class 4", "Rated up to 80 or 85", "0-85 / 0-80", "All season", "7–14", "£5,000", ""],
    ["Handicap, Class 5", "Rated up to 70 or 75", "0-75 / 0-70", "All season", "7–14", "£3,600", "Bread and butter for a small yard"],
    ["Handicap, Class 6", "Rated up to 55, 60 or 65", "0-65 / 0-60 / 0-55", "All season, lots on the all-weather", "7–14", "£2,900", "The bottom rung: cheap to run, small prizes"],
    ["Fillies' handicap", "Fillies and mares only, any class", "Classes 2–6", "All season", "7–14", "As its class", "A quieter route for a filly"],
    ["Three-year-old handicap", "Three-year-olds only", "Classes 2–6", "Spring and summer mostly", "7–14", "As its class", "Before June, three-year-olds mostly meet only each other"],
    ["Apprentice / amateur handicap", "Ridden by apprentices (weight allowance) or amateurs", "Classes 4–6", "All season", "7–14", "A little less than its class",
     "A light weight on the horse; a less skilful rider"],
    ["Nursery", "Two-year-old handicap, for two-year-olds with a mark", "Classes 3–6", "From early July (week 16) to November", "7–13", "As its class",
     "Where most two-year-olds end up after three runs"],
    ["Maiden", "Horses that have never won", "Classes 3–5", "Two-year-olds from March; three-year-olds to September; then 3yo+", "5–18", "£3,600–£9,000",
     "First runs. Horses run green: a few pounds below their ability"],
    ["Novice", "Horses that have not won more than twice; past winners carry a penalty", "Classes 3–5", "As maidens", "5–13", "£3,600–£9,000",
     "The main start for a young horse"],
    ["Restricted novice", "Two-year-olds that were cheap as yearlings or are by cheaper stallions", "Class 5", "From May", "5–13", "£4,000",
     "A softer start for a Book 3 or Book 4 buy"],
    ["Conditions stakes", "Weights set by age, sex and past wins, not by rating", "Class 2", "All season at bigger courses", "5–10", "£12,000",
     "For a useful horse not quite good enough for Listed"],
    ["Seller", "The winner is offered for sale at auction straight after the race", "Class 6", "All season at smaller courses", "5–10", "£2,900", "Somewhere to win a race with a weak horse, at the risk of losing it"],
    ["Claimer", "Every runner can be bought (claimed) for the price its owner set", "Classes 5–6", "All season", "5–10", "£2,900–£3,600",
     "Ties into the claiming route for buying horses"],
    ["Classified stakes", "Level weights for horses rated under the cap (0-50 or 0-55)", "Class 6", "All season, mostly all-weather", "5–10", "£2,900", "Weak horses with no weight burden"],
    ["Sales race", "Only for two-year-olds bought at a named yearling sale; often very valuable", "Class 2", "July to October", "12–25", "£75,000–£150,000",
     "Rewards buying at the sales: Super Sprint, Premier Yearling Stakes, October Auction Stakes, Two-Year-Old Trophy"],
    ["All-Weather Championships Finals", "Horses that ran three times on the all-weather in the winter", "Conditions", "Good Friday (week 2)", "8–14", "£75,000–£100,000",
     "A reason to race through the winter"],
    ["Series finals", "Horses that ran in the series' qualifiers (Sprint Series, London Mile)", "Handicap", "August and September", "12–16", "£25,000", "A target for a mid-rated horse"],
]
table(ws, 1, ["Race type", "Who can run", "Class / band", "When in the season", "Runners", "Prize to winner", "In the game"], RT,
      [24, 44, 16, 36, 9, 20, 52], wrap_cols=("Who can run", "When in the season", "In the game", "Class / band"))

# ------------------------------------------------------------------ Routes
ws = wb.create_sheet("Routes")
RO = [
    ["Classic miler (colt)", "2yo: novice (June/July) → Coventry, July Stakes or Vintage → Dewhurst or Futurity Trophy",
     "3yo: Craven or Greenham → 2000 Guineas → St James's Palace → Sussex → Queen Elizabeth II", "Craven Stakes, 16 Apr"],
    ["Classic filly (miler)", "2yo: novice → Albany or Duchess of Cambridge → Sweet Solera or Prestige → Rockfel or Fillies' Mile",
     "3yo: Nell Gwyn or Fred Darling → 1000 Guineas → Coronation → Falmouth or Nassau → Sun Chariot", "Nell Gwyn Stakes, 14 Apr"],
    ["Derby colt", "2yo: maiden over 7f or 1m (August) → Royal Lodge or Futurity Trophy",
     "3yo: Classic Trial, Chester Vase, Dante, Derby Trial, Dee or Cocked Hat → the Derby → King George → International → Champion Stakes", "Derby, 6 Jun"],
    ["Oaks filly", "2yo: novice over 7f or 1m → May Hill or Fillies' Mile",
     "3yo: Musidora, Cheshire Oaks, Oaks Trial, Pretty Polly or Height of Fashion → the Oaks → Yorkshire Oaks → Champions Fillies' and Mares'", "Oaks, 5 Jun"],
    ["St Leger horse", "A late developer that stays",
     "3yo: King Edward VII or Queen's Vase → Bahrain Trophy, Gordon, Great Voltigeur or March Stakes → St Leger", "St Leger, 12 Sep"],
    ["Stayer (Cup horse)", "4yo+",
     "Sagaro → Henry II or Yorkshire Cup → Gold Cup → Goodwood Cup → Lonsdale Cup → Doncaster Cup → Champions Long Distance Cup", "Gold Cup, 18 Jun"],
    ["Sprinter", "3yo+",
     "Palace House, Abernant or Pavilion → Temple, Duke of York or Sandy Lane → King Charles III, Commonwealth Cup or QEII Jubilee → July Cup → King George Stakes or Nunthorpe → Sprint Cup → Champions Sprint", "July Cup, 11 Jul"],
    ["Older middle-distance horse", "4yo+",
     "Earl of Sefton, Gordon Richards or Huxley → Brigadier Gerard → Prince of Wales's → Eclipse → King George or International → Champion Stakes", "Eclipse, 4 Jul"],
    ["Older miler", "4yo+", "Sandown Mile → Lockinge → Queen Anne → Summer Mile or Sussex → Celebration Mile or Joel → Queen Elizabeth II", "Lockinge, 16 May"],
    ["Early two-year-old sprinter", "An early type, 5f",
     "Novice (April/May) → National or Marygate → Norfolk, Windsor Castle or Queen Mary → Molecomb → Flying Childers or Cornwallis → Middle Park or Cheveley Park", "Norfolk Stakes, 20 Jun"],
    ["Sprint handicapper", "3yo+ with a mark around 85–105",
     "Three runs for a mark → Class 4/3 sprints → Wokingham → Stewards' Cup → Portland → Ayr Gold Cup", "Stewards' Cup, 1 Aug"],
    ["Mile handicapper", "4yo+ with a mark around 85–105",
     "Lincoln → Victoria Cup → Royal Hunt Cup → Bunbury Cup → Golden Mile → Cambridgeshire → Balmoral", "Lincoln, 28 Mar"],
    ["Staying handicapper", "4yo+ that stays 2m",
     "Chester Cup → Ascot Stakes → Northumberland Plate → Goodwood Handicap → Ebor → Cesarewitch → November Handicap", "Ebor, 22 Aug"],
    ["Three-year-old handicapper", "A 3yo rated 80–100",
     "London Gold Cup or Silver Bowl → Britannia, King George V or Golden Gates → July Festival 3yo handicaps → Melrose → Old Rowley Cup", "Britannia, 18 Jun"],
    ["Cheap buy (Book 3 or 4)", "A 2yo that cost little",
     "Restricted novice → Super Sprint → Premier Yearling Stakes or October Auction Stakes → Two-Year-Old Trophy", "Super Sprint, 18 Jul"],
    ["Winter all-weather horse", "Any age",
     "Three all-weather runs between November and March → a Finals race on Good Friday (Easter Classic, Mile, Sprint, Marathon...)", "Finals Day, 3 Apr"],
]
table(ws, 1, ["Route", "Who", "The path", "Signature race"], RO, [26, 36, 90, 24], wrap_cols=("Who", "The path"))

# ------------------------------------------------------------------ Patterns
ws = wb.create_sheet("Patterns")
PA = [
    ["Ages", "Every horse turns a year older on 1 January. A two-year-old's season runs from the Brocklesby (28 Mar) to December; from January it races as a three-year-old."],
    ["Two-year-old trips", "March–April 5f only. May 5f–6f. June–July up to 7f. August–October 6f–1m. Late October–November up to 1m2f. Early types win in spring; big, late types wait for 7f and a mile in the autumn."],
    ["Nurseries", "Two-year-old handicaps from early July (week 16). A two-year-old gets a mark after three runs, or after a win."],
    ["Three-year-olds", "Until the end of May most handicaps are for 4yo+ or for 3yo only. From June, handicaps are 3yo+ and three-year-olds get the weight-for-age allowance, which shrinks through the summer."],
    ["The Classics", "2000 Guineas, 1000 Guineas, Oaks, Derby and St Leger: three-year-olds only, and closed to geldings. Gelding a colt rules him out of them."],
    ["Fillies", "Most Group levels have a fillies' race beside the open one (Coronation beside St James's Palace, Nassau beside the Eclipse...). Fillies may run in open races too, with a weight allowance."],
    ["Handicap marks", "Given after three runs or a win; up after a win, down after poor runs. Handicaps are for horses rated 110 or less; above that it is Listed and Group races only."],
    ["Class ladder", "Maiden or novice → Class 6/5 handicaps → Class 4/3 → Class 2 and heritage handicaps → Listed → Group 3 → Group 2 → Group 1."],
    ["Black type", "Winning or placing in a Listed or Group race goes in the horse's stud record: worth far more on a filly or a colt with a pedigree."],
    ["Trials", "Most big races have trials 3–6 weeks before them, at set meetings (see Routes). Running in a trial is how real yards plan a season."],
    ["Festivals", "Newmarket (Craven, Guineas, July, Cambridgeshire, Future Champions), Chester May, York (Dante, Ebor), Epsom Derby, Royal Ascot, Glorious Goodwood, Doncaster St Leger, Haydock Sprint Cup, Ayr Western, Champions Day."],
    ["Going by month", "March–April often soft. May–August mostly good to quick. September–October good, turning softer. November soft. The all-weather rides the same all year."],
    ["The two surfaces", "Turf from late March to early November; all-weather (Kempton, Lingfield, Wolverhampton, Newcastle, Southwell, Chelmsford) all year, and alone in winter."],
    ["Prize split", "About 50% to the winner, 25% to second, 12.5% third, 6% fourth, a little to fifth and sixth in bigger races."],
    ["Card shapes", "Festival day: 7 races, mostly Group, Listed and heritage handicaps, with Class 2 handicaps and a two-year-old race to fill. Feature day: 7 races round one or two Listed or Group 3 races. Everyday: 7 races (6 in the evening): one or two maidens or novices, a two-year-old race, three or four handicaps at the course's level, sometimes a seller, claimer, apprentice or classified race. All-weather: 6–7 races, mostly Class 5–6 handicaps."],
    ["Course levels", "A (premier, ten courses): everyday handicaps Class 2–4. B (middle): Class 3–6, mostly 4–5. C (small, and most all-weather): Class 4–6, with sellers and claimers."],
    ["Big courses not built yet", "Each meeting names the course it races on until that course is built (the course priority Sheet's stand-ins). Newmarket uses the July Course from late June to the end of August."],
]
table(ws, 1, ["Pattern", "How it works"], PA, [24, 130], wrap_cols=("How it works",))

# ------------------------------------------------------------------ Courses
ws = wb.create_sheet("Courses")
rows = []
for name, c in sorted(CRS.items(), key=lambda kv: ({"A": 0, "B": 1, "C": 2}[kv[1]["level"]], kv[0])):
    fs = sorted(D(f["date"]) for f in FX if f["course"] == name)
    rs = [r for r in R if r["course"] == name]
    turf = [d for d in fs if d <= dt.date(2026, 11, 8)]
    season = f"{turf[0]:%d %b} – {turf[-1]:%d %b}" if turf else "winter only"
    rows.append([name, {"A": "A (premier)", "B": "B (middle)", "C": "C (small)"}[c["level"]], c["surface"], season, len(fs),
                 sum(r["type"] in ("Group 1", "Group 2", "Group 3", "Listed", "Heritage handicap") for r in rs),
                 c["region"], c["scenery"], c["tier"], c["standin"] or "itself"])
table(ws, 1, ["Course", "Level", "Surface", "Turf season", "Meetings", "Big races", "Region", "Scenery kit", "Build tier",
              "Races on until built"], rows, [18, 13, 12, 18, 10, 10, 10, 15, 18, 16])
n = len(rows) + 3
ws.cell(row=n, column=1, value="Real 2026 aside: Chelmsford City lost its licence and some Haydock meetings moved after track damage. The game keeps both as normal courses.")

# ------------------------------------------------------------------ Abroad
ws = wb.create_sheet("Abroad (later)")
AB = [
    ["Dubai World Cup night", "Meydan, Dubai", "Late March (before the turf season)", "Dirt and turf Group 1s", "An idea for later: travelling a horse"],
    ["Irish 2000 and 1000 Guineas", "The Curragh", "Late May", "Group 1, 3yo, 1m", "Second chance after Newmarket"],
    ["Prix du Jockey Club (French Derby)", "Chantilly", "Early June", "Group 1, 3yo, 1m2½f", ""],
    ["Irish Derby", "The Curragh", "Late June", "Group 1, 3yo, 1m4f", "The usual next step after Epsom"],
    ["Irish Oaks", "The Curragh", "Mid-July", "Group 1, 3yo fillies, 1m4f", ""],
    ["Irish Champions Festival", "Leopardstown and the Curragh", "12–13 September 2026", "Irish Champion Stakes, Matron, Irish St Leger, Moyglare, National Stakes, Flying Five", ""],
    ["Prix de l'Arc de Triomphe", "ParisLongchamp", "First Sunday in October", "Group 1, 3yo+, 1m4f", "Europe's championship"],
    ["Breeders' Cup", "USA", "6–7 November 2026", "Turf, Mile, Filly & Mare Turf, Juvenile Turf...", ""],
    ["Japan Cup / Hong Kong International", "Tokyo / Sha Tin", "Late November / mid-December", "Group 1s", "Winter targets for a top horse"],
]
table(ws, 1, ["Meeting", "Where", "When", "Races", "Note"], AB, [34, 26, 26, 50, 36], wrap_cols=("Races", "Note"))

wb.save(HERE / "calendar.xlsx")
print("saved", [s.title for s in wb.worksheets], len(R))
