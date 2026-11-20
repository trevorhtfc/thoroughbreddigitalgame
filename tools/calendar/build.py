"""Builds the full-game racing calendar (Thoroughbred, career mode) from:
  big_races.txt          every Group, Listed and heritage race, placed on the 2026 dates
  royal-ascot.js         Royal Ascot's 35 races, as the quick game has them
  the rota below         the everyday meetings, on each course's real days and season
and fills every card to a real-looking shape (maidens, novices, nurseries, handicaps by class, sellers...).
Writes calendar.json (for the game) and the tables for the Sheet (calendar.xlsx).
"""
import json, re, random, datetime as dt, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
from collections import defaultdict, Counter

D = dt.date
SEASON_START = D(2026, 3, 23)          # Monday of week 1 (the Lincoln is Sat 28 March)
TURF_WEEKS = 33                         # week 33 ends Sun 8 November (the November Handicap)
WINTER = [  # the winter all-weather season, as five game turns
    ("Winter 1", "November", D(2026, 11, 9), D(2026, 12, 6)),
    ("Winter 2", "December", D(2026, 12, 7), D(2027, 1, 3)),
    ("Winter 3", "January", D(2027, 1, 4), D(2027, 1, 31)),
    ("Winter 4", "February", D(2027, 2, 1), D(2027, 2, 28)),
    ("Winter 5", "March", D(2027, 3, 1), D(2027, 3, 21)),
]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def week_of(d):
    if d <= SEASON_START + dt.timedelta(days=7 * TURF_WEEKS - 1):
        return (d - SEASON_START).days // 7 + 1
    for i, (name, _, a, b) in enumerate(WINTER):
        if a <= d <= b:
            return 34 + i
    raise ValueError(d)

def week_label(w):
    return f"Week {w}" if w <= TURF_WEEKS else WINTER[w - 34][0]

def phase_of(w):
    if w <= 6: return "Spring"
    if w <= 12: return "Early summer"
    if w <= 22: return "High summer"
    if w <= 30: return "Autumn"
    if w <= 33: return "Back end"
    return "Winter (all-weather)"

# ------------------------------------------------------------------ courses
# level: A premier, B middle, C small. trips: the race distances the course stages (furlongs).
# straight: races up to this trip run on a straight course (0 = none). field: most runners the course takes.
# tier and standin: from the course priority Sheet (17 Nov): where a course races until it is built.
C = {}
def course(name, level, surface, trips, straight, field, tier, standin, region, scenery):
    C[name] = dict(name=name, level=level, surface=surface, trips=trips, straight=straight, field=field,
                   tier=tier, standin=standin, region=region, scenery=scenery)
course("Ascot", "A", "Turf", [5, 6, 7, 8, 10, 12, 14, 16, 20, 22], 8, 30, "Built", "", "South", "Parkland")
course("Newmarket", "A", "Turf", [5, 6, 7, 8, 9, 10, 12, 14, 16, 18], 10, 30, "Built", "", "East", "Heath")
course("York", "A", "Turf", [5, 6, 7, 8, 9, 10, 12, 14, 16], 6, 22, "Built", "", "North", "Parkland")
course("Goodwood", "A", "Turf", [5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20], 6, 20, "1 (detailed build)", "Ascot", "South", "Downland")
course("Epsom", "A", "Turf", [5, 6, 7, 8.5, 10, 12], 5, 20, "1 (detailed build)", "York", "South", "Downland")
course("Sandown", "A", "Turf", [5, 7, 8, 10, 14, 16], 5, 20, "2", "Ascot", "South", "Parkland")
course("Newbury", "A", "Turf", [5, 6, 7, 8, 9, 10, 11, 12, 13, 16], 8, 24, "2", "York", "South", "Parkland")
course("Doncaster", "A", "Turf", [5, 6, 7, 8, 10, 12, 14, 16, 18], 8, 24, "2", "York", "North", "Parkland")
course("Haydock", "A", "Turf", [5, 6, 7, 8, 10, 12, 14, 16], 6, 20, "2", "York", "North", "Parkland")
course("Chester", "A", "Turf", [5, 6, 7, 8, 10, 11, 12, 13, 16, 18], 0, 14, "2", "York", "North", "Town")
course("Kempton", "B", "All-weather", [5, 6, 7, 8, 10, 11, 12, 16], 0, 14, "3", "Sandown", "South", "Parkland")
course("Wolverhampton", "C", "All-weather", [5, 6, 7, 8.5, 9.5, 12, 14, 16], 0, 13, "3", "Chester", "Midlands", "Town")
course("Newcastle", "B", "All-weather", [5, 6, 7, 8, 10, 12, 16], 8, 14, "3", "Doncaster", "North", "Northern stone")
course("Thirsk", "B", "Turf", [5, 6, 7, 8, 12, 16], 6, 20, "3", "Haydock", "North", "Northern stone")
course("Salisbury", "B", "Turf", [5, 6, 7, 8, 10, 12, 14], 8, 20, "3", "Ascot", "South", "Downland")
course("Ayr", "B", "Turf", [5, 6, 7, 8, 9, 10, 12, 13, 16], 6, 25, "3", "Haydock", "Scotland", "Seaside")
course("Bath", "B", "Turf", [5, 5.5, 8, 10, 11, 13, 14], 0, 16, "4", "Haydock", "South", "Downland")
course("Beverley", "B", "Turf", [5, 7, 8, 10, 12, 16], 5, 20, "4", "Sandown", "North", "Northern stone")
course("Brighton", "C", "Turf", [5, 6, 7, 8, 10, 12], 0, 14, "4", "Epsom", "South", "Seaside")
course("Carlisle", "C", "Turf", [5, 6, 7, 8, 9, 11, 12], 0, 16, "4", "Sandown", "North", "Northern stone")
course("Catterick", "C", "Turf", [5, 6, 7, 12, 14], 5, 16, "4", "Chester", "North", "Northern stone")
course("Chelmsford City", "C", "All-weather", [5, 6, 7, 8, 10, 12, 14, 16], 0, 14, "4", "Wolverhampton", "East", "Parkland")
course("Chepstow", "C", "Turf", [5, 6, 7, 8, 10, 12, 16], 8, 20, "4", "Newbury", "Wales", "Parkland")
course("Ffos Las", "C", "Turf", [5, 6, 8, 10, 12, 14, 16], 6, 16, "4", "Haydock", "Wales", "Parkland")
course("Hamilton", "B", "Turf", [5, 6, 8, 9, 11, 12], 6, 16, "4", "Salisbury", "Scotland", "Northern stone")
course("Leicester", "B", "Turf", [5, 6, 7, 8, 10, 12], 7, 20, "4", "Ascot", "Midlands", "Parkland")
course("Lingfield (turf)", "B", "Turf", [5, 6, 7, 8, 10, 11, 12, 16], 7, 20, "4", "Epsom", "South", "Parkland")
course("Lingfield (AW)", "B", "All-weather", [5, 6, 7, 8, 10, 12, 13, 16], 0, 14, "4", "Wolverhampton", "South", "Parkland")
course("Musselburgh", "B", "Turf", [5, 7, 8, 9, 12, 14, 16], 5, 16, "4", "Thirsk", "Scotland", "Seaside")
course("Nottingham", "B", "Turf", [5, 6, 8, 10, 14, 16], 6, 20, "4", "Haydock", "Midlands", "Parkland")
course("Pontefract", "B", "Turf", [5, 6, 8, 10, 12, 16], 0, 18, "4", "Epsom", "North", "Northern stone")
course("Redcar", "B", "Turf", [5, 6, 7, 8, 9, 10, 11, 14], 8, 22, "4", "Doncaster", "North", "Seaside")
course("Ripon", "B", "Turf", [5, 6, 8, 9, 10, 12, 16], 6, 20, "4", "Thirsk", "North", "Parkland")
course("Southwell", "C", "All-weather", [5, 6, 7, 8, 11, 12, 14, 16], 5, 14, "4", "Thirsk", "Midlands", "Parkland")
course("Wetherby", "C", "Turf", [5, 7, 8, 10, 12, 14], 0, 16, "4", "Haydock", "North", "Northern stone")
course("Windsor", "B", "Turf", [5, 6, 8, 10, 11], 6, 20, "4", "Goodwood", "South", "Town")
course("Yarmouth", "B", "Turf", [5, 6, 7, 8, 10, 11, 12, 14, 16], 8, 20, "4", "Doncaster", "East", "Seaside")

def newmarket_course(d):
    """The July Course from late June to the end of August; the Rowley Mile otherwise."""
    return "July Course" if D(2026, 6, 20) <= d <= D(2026, 8, 31) else "Rowley Mile"

# ------------------------------------------------------------------ big races
GRADE_NAME = {"G1": "Group 1", "G2": "Group 2", "G3": "Group 3", "L": "Listed", "HH": "Heritage handicap",
              "H": "Handicap", "C": "Conditions", "S": "Sales race", "M": "Maiden"}
# prize to the winner by grade, when big_races.txt gives none (two-year-old pattern races a little less)
PRIZE = {"G1": 250000, "G2": 85000, "G3": 45000, "L": 25000, "HH": 45000, "H": 20000, "C": 15000, "S": 75000, "M": 8000}
PRIZE_2YO = {"G1": 200000, "G2": 60000, "G3": 35000, "L": 18000}

def dist_label(f):
    if f == 8.5: return "1m113y"
    if f == 9.5: return "1m1f104y"
    if f == 5.5: return "5½f"
    m, r = divmod(int(f), 8)
    return (f"{m}m" if m else "") + (f"{r}f" if r else "") if f >= 8 else f"{int(f)}f"

def ages_label(a):
    return a

races = []        # every race in the calendar
fixtures = {}     # (date, course) -> fixture

def add_fixture(d, crs, meeting, kind, evening=False):
    key = (d, crs)
    if key in fixtures:
        return fixtures[key]
    fx = dict(date=d, course=crs, meeting=meeting, kind=kind, evening=evening, races=[])
    fixtures[key] = fx
    return fx

def parse_big():
    out = []
    for line in open(HERE / "big_races.txt"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        if line == "ROYAL_ASCOT":
            out.extend(royal_ascot())
            continue
        p = line.split("|")
        p += [""] * (11 - len(p))
        date, crs, meeting, name, g, f, dist, ages, sex, prize, note = p[:11]
        f = float(f); f = int(f) if f == int(f) else f
        if name == "Portland Handicap": f = 5.5
        if prize and not prize.isdigit():
            note, prize = (prize + (" " + note if note else "")).strip(), ""
        out.append(dict(date=D.fromisoformat(date), course=crs, meeting=meeting, name=name, g=g, f=f,
                        dist=dist or dist_label(f), ages=ages, sex=sex, prize=int(prize) if prize else None, note=note))
    return out

def royal_ascot():
    src = open(REPO / "game/js/meetings/royal-ascot.js").read()
    days = [D(2026, 6, 16 + i) for i in range(5)]
    names = ["Royal Ascot, Tuesday", "Royal Ascot, Wednesday", "Royal Ascot, Thursday (Gold Cup Day)",
             "Royal Ascot, Friday", "Royal Ascot, Saturday"]
    gmap = {"Group 1": "G1", "Group 2": "G2", "Group 3": "G3", "Listed": "L", "Handicap": "HH", "Conditions": "C"}
    prize = {"queen-anne": 450000, "king-charles": 350000, "st-james": 450000, "prince-of-wales": 600000,
             "gold-cup": 450000, "coronation": 400000, "commonwealth": 400000, "qeii": 450000,
             "royal-hunt-cup": 100000, "wokingham": 100000}
    notes = {"queen-anne": "Opens the royal meeting", "gold-cup": "The great staying race of the year",
             "prince-of-wales": "Royal Ascot's richest race", "st-james": "The Guineas winners meet again",
             "coronation": "The fillies' Guineas winners meet again", "queen-alexandra": "The longest Flat race of the year",
             "royal-hunt-cup": "Straight mile, up to 30 runners", "wokingham": "Six furlongs, up to 30 runners"}
    out = []
    for m in re.finditer(r'\{ id: "([^"]+)", day: (\d), name: "([^"]+)", grade: "([^"]+)", f: (\d+), dist: "([^"]+)", '
                         r'ages: \[(\d), (\d)\], ageLabel: "([^"]+)"(?:, sex: "(\w)")?(, round: true)?', src):
        rid, day, name, grade, f, dist, a0, a1, label, sex, rnd = m.groups()
        a0, a1 = int(a0), int(a1)
        ages = f"{a0}yo" if a0 == a1 else f"{a0}yo+"
        g = gmap[grade]
        pr = prize.get(rid) or {"G1": 350000, "G2": 120000, "G3": 80000, "L": 50000, "HH": 60000, "C": 50000}[g]
        out.append(dict(date=days[int(day)], course="Ascot", meeting=names[int(day)], name=name, g=g, f=int(f), dist=dist,
                        ages=ages, sex=sex or "", prize=pr, note=notes.get(rid, ""), round=bool(rnd)))
    assert len(out) == 35, len(out)
    return out

BIG = parse_big()

def kind_for(crs, meeting, big_on_card):
    m = meeting.lower()
    if any(k in m for k in ["royal ascot", "glorious", "ebor festival", "july festival", "guineas", "derby festival",
                             "st leger", "cambridgeshire", "future champions", "champions day", "dante", "may festival",
                             "craven", "sprint cup", "western meeting", "ayr gold cup", "eclipse", "king george",
                             "lincoln", "finals day", "northumberland", "chester cup", "trials day"]):
        return "Festival"
    if any(r["g"] in ("G1", "G2", "G3") for r in big_on_card):
        return "Premier"
    if C[crs]["surface"] == "All-weather":
        return "All-weather"
    return "Feature"

by_fixture = defaultdict(list)
for r in BIG:
    by_fixture[(r["date"], r["course"])].append(r)
for (d, crs), rs in by_fixture.items():
    meeting = rs[0]["meeting"]
    ev = "Evening" in meeting
    fx = add_fixture(d, crs, meeting, kind_for(crs, meeting, rs), evening=ev)
    fx["big"] = rs

rng = random.Random(20261120)
# ------------------------------------------------------------------ everyday meetings
# Named everyday days at the big courses (real 2026 fixtures where known)
NAMED = [
    ("2026-03-27", "Doncaster", "The Lincoln Meeting, Friday", False),
    ("2026-04-17", "Newbury", "Spring Friday", False),
    ("2026-05-30", "Chester", "Roman Day", False), ("2026-06-12", "Chester", "Friday Evening", True),
    ("2026-06-13", "Chester", "Saturday", False), ("2026-06-27", "Chester", "Saturday", False),
    ("2026-07-10", "Chester", "Friday Evening", True), ("2026-07-25", "Chester", "Saturday", False),
    ("2026-08-22", "Chester", "Ladies Day", False),
    ("2026-06-20", "Newmarket", "Summer Saturday (July Course)", False), ("2026-06-25", "Newmarket", "Thursday (July Course)", False),
    ("2026-07-17", "Newmarket", "Friday Evening (July Course)", True), ("2026-07-18", "Newmarket", "Saturday (July Course)", False),
    ("2026-08-01", "Newmarket", "Summer Saturday (July Course)", False), ("2026-08-06", "Newmarket", "Thursday (July Course)", False),
    ("2026-08-21", "Newmarket", "Friday Evening (July Course)", True), ("2026-08-22", "Newmarket", "Summer Saturday (July Course)", False),
    ("2026-10-21", "Newmarket", "Two-Year-Old Day", False),
    ("2026-06-12", "York", "Summer Friday", False), ("2026-10-09", "York", "Autumn Friday", False),
    ("2026-06-12", "Goodwood", "Friday Night", True), ("2026-06-26", "Goodwood", "Friday Night", True),
    ("2026-10-11", "Goodwood", "Season Finale", False),
    ("2026-07-02", "Epsom", "Thursday Evening", True), ("2026-08-31", "Epsom", "Bank Holiday Monday", False),
    ("2026-06-24", "Sandown", "Wednesday Evening", True), ("2026-08-12", "Sandown", "Wednesday Evening", True),
    ("2026-06-25", "Newbury", "Thursday", False), ("2026-09-18", "Newbury", "Friday", False),
    ("2026-07-18", "Doncaster", "Saturday", False), ("2026-08-14", "Doncaster", "Friday Evening", True),
    ("2026-06-20", "Haydock", "Saturday", False), ("2026-07-17", "Haydock", "Friday Evening", True),
    ("2026-09-03", "Haydock", "Sprint Cup Festival, Thursday", False), ("2026-09-26", "Haydock", "Saturday", False),
    ("2026-08-04", "Brighton", "Brighton Festival, Tuesday", False), ("2026-08-06", "Brighton", "Brighton Festival, Thursday", False),
    ("2026-09-15", "Yarmouth", "The Eastern Festival, Tuesday", False), ("2026-09-17", "Yarmouth", "The Eastern Festival, Thursday", False),
    ("2026-09-17", "Ayr", "The Western Meeting, Thursday", False),
    ("2026-09-10", "Doncaster", "The St Leger Festival, Thursday", False),
]
for d, crs, meeting, ev in NAMED:
    d = D.fromisoformat(d)
    if (d, crs) in fixtures:
        continue
    k = "Festival" if "Festival" in meeting or "Western" in meeting else ("Evening" if ev else "Everyday")
    add_fixture(d, crs, meeting, k, evening=ev)

# The rota: (course, first week, last week, weekdays, how many, evening weekdays)
ROTA = [
    ("Wolverhampton", 1, 33, [0, 1, 4, 5], 9, [0, 4]),
    ("Southwell", 1, 33, [1, 3], 6, []),
    ("Newcastle", 1, 33, [3, 4], 6, [4]),
    ("Kempton", 1, 33, [2], 8, [2]),
    ("Chelmsford City", 1, 33, [3, 5], 3, [3]),
    ("Lingfield (AW)", 1, 8, [2, 5], 2, []),
    ("Lingfield (AW)", 28, 33, [2, 5], 2, []),
    ("Lingfield (turf)", 9, 24, [2, 5], 4, [2]),
    ("Windsor", 4, 23, [0], 9, [0]),
    ("Yarmouth", 5, 29, [1, 2, 3], 6, []),
    ("Brighton", 5, 28, [1, 2, 3], 4, []),
    ("Bath", 4, 29, [2, 4], 6, [4]),
    ("Salisbury", 5, 27, [6, 2, 3], 4, []),
    ("Chepstow", 7, 24, [4, 1], 4, [4]),
    ("Ffos Las", 12, 23, [1, 3], 3, []),
    ("Leicester", 3, 30, [0, 1, 5], 5, [0]),
    ("Nottingham", 2, 32, [1, 2], 6, []),
    ("Musselburgh", 2, 30, [4, 6], 6, []),
    ("Hamilton", 7, 27, [1, 2, 4], 5, [2]),
    ("Ayr", 6, 30, [0, 5], 4, []),
    ("Carlisle", 9, 22, [0, 2, 3], 4, [2]),
    ("Catterick", 3, 30, [1, 2], 6, []),
    ("Thirsk", 3, 26, [5, 1, 4], 6, [4]),
    ("Ripon", 4, 24, [3, 6, 0], 6, [3]),
    ("Redcar", 3, 31, [0, 1, 5], 6, []),
    ("Beverley", 3, 27, [1, 2, 5], 6, []),
    ("Pontefract", 3, 31, [1, 6, 0], 5, []),
    ("Wetherby", 8, 20, [0, 1], 2, []),
    ("Goodwood", 9, 24, [4], 1, [4]),
    ("Doncaster", 8, 30, [3, 5], 1, []),
    ("Haydock", 6, 28, [2, 4, 5], 1, [2]),
    ("Newbury", 4, 30, [3, 6], 1, []),
]
MEETING_NAME = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}

def course_days(crs):
    return {d for (d, c) in fixtures if c == crs}

for crs, w0, w1, wds, n, evs in ROTA:
    span = w1 - w0 + 1
    for i in range(n):
        w = w0 + int((i + 0.5) * span / n)
        placed = False
        for shift in range(0, 6):
            for wd in (wds[(i + j) % len(wds)] for j in range(len(wds))):
                for ww in (w + shift, w - shift):
                    if not (w0 <= ww <= w1):
                        continue
                    d = SEASON_START + dt.timedelta(days=7 * (ww - 1) + wd)
                    taken = course_days(crs)
                    if any(abs((d - t).days) < 5 for t in taken):
                        continue
                    ev = wd in evs and D(2026, 4, 20) <= d <= D(2026, 9, 5)
                    k = "Evening" if ev else ("All-weather" if C[crs]["surface"] == "All-weather" else "Everyday")
                    add_fixture(d, crs, MEETING_NAME[wd] + (" Evening" if ev else ""), k, evening=ev)
                    placed = True
                    break
                if placed: break
            if placed: break
        if not placed:
            print("could not place", crs, i, file=sys.stderr)

# Balance the turf weeks: at least 9 meetings and at most 13 (a feature-packed week keeps all its big days)
ROTA_COURSES = [r[0] for r in ROTA]
def active(crs, w):
    return any(c == crs and a <= w <= b for c, a, b, *_ in ROTA)
for w in range(1, TURF_WEEKS + 1):
    mon = SEASON_START + dt.timedelta(days=7 * (w - 1))
    wk = [k for k in fixtures if mon <= k[0] < mon + dt.timedelta(days=7)]
    tries = 0
    while len(wk) < 9 and tries < 200:
        tries += 1
        cands = [c for c in ROTA_COURSES if active(c, w) and C[c]["level"] != "A"]
        if w <= 3 or w >= 31:
            cands += ["Wolverhampton", "Kempton", "Newcastle", "Southwell", "Lingfield (AW)"]
        # sorted first, so the seeded luck meets the courses in the same order every run (a bare set's order changes
        # from run to run, which reshuffled the everyday meetings each time: found 20 Nov)
        cands = sorted(sorted(set(cands)), key=lambda c: (sum(1 for k in fixtures if k[1] == c), rng.random()))
        crs = rng.choice(cands[:5])
        wd = rng.choice([0, 1, 2, 3, 4, 5])
        d = mon + dt.timedelta(days=wd)
        if any(abs((d - t).days) < 4 for t in course_days(crs)):
            continue
        k = "All-weather" if C[crs]["surface"] == "All-weather" else "Everyday"
        add_fixture(d, crs, MEETING_NAME[wd], k)
        wk.append((d, crs))
    extra = [k for k in wk if fixtures[k]["kind"] in ("Everyday", "Evening", "All-weather") and not fixtures[k].get("big")
             and k[1] not in ("Chester", "Newmarket", "York", "Goodwood", "Epsom", "Sandown", "Newbury", "Doncaster", "Haydock")]
    rng.shuffle(extra)
    # cut the all-weather first, then the courses with the most meetings, so the small turf courses keep their summers
    extra.sort(key=lambda k: (C[k[1]]["surface"] == "All-weather", sum(1 for x in fixtures if x[1] == k[1])))
    while len(wk) > 13 and extra:
        k = extra.pop()
        del fixtures[k]
        wk.remove(k)

# Winter all-weather: a few everyday meetings in each winter turn
WROTA = [("Wolverhampton", [0, 4, 5], 3), ("Kempton", [2], 2), ("Lingfield (AW)", [2, 5], 2), ("Newcastle", [3, 4], 2),
         ("Southwell", [1, 3], 2), ("Chelmsford City", [3], 1)]
for wi, (wname, month, a, b) in enumerate(WINTER):
    days = (b - a).days + 1
    for crs, wds, n in WROTA:
        if wi == 4 and crs == "Chelmsford City":
            continue
        for i in range(n):
            base = a + dt.timedelta(days=int((i + 0.5) * days / n))
            for off in range(0, 7):
                d = base + dt.timedelta(days=off)
                if d.weekday() in wds and d <= b and not any(abs((d - t).days) < 4 for t in course_days(crs)):
                    if d == D(2026, 12, 25):
                        continue
                    nm = "Boxing Day" if d == D(2026, 12, 26) else MEETING_NAME[d.weekday()] + (" Evening" if d.weekday() in (2, 4) else "")
                    add_fixture(d, crs, nm + " (all-weather)", "All-weather", evening=d.weekday() in (2, 4))
                    break
    # Wolverhampton on Boxing Day
add_fixture(D(2026, 12, 26), "Wolverhampton", "Boxing Day (all-weather)", "All-weather")

# ------------------------------------------------------------------ filling the cards

def juv_trips(w, d=None):
    if d is not None and (d < D(2026, 3, 28) or d >= D(2027, 1, 1)): return []   # none before the Brocklesby; none after 1 Jan
    if w <= 6: return [5]
    if w <= 10: return [5, 6]
    if w <= 18: return [5, 6, 7]
    if w <= 30: return [6, 7, 8]
    if w <= 33: return [6, 7, 8, 10]
    if w <= 35: return [5, 6, 7, 8]
    return []

CLASS_BANDS = {2: ["0-105", "0-100"], 3: ["0-95", "0-90"], 4: ["0-85", "0-80"], 5: ["0-75", "0-70"], 6: ["0-65", "0-60", "0-55"]}
CLASS_PRIZE = {1: 25000, 2: 15000, 3: 8000, 4: 5000, 5: 3600, 6: 2900}
RATINGS = {"G1": "110–125", "G2": "105–118", "G3": "100–112", "L": "95–108", "HH": "88–108", "H": "80–100",
           "C": "85–105", "S": "65–95 (unraced or lightly raced)", "M": "unraced"}
RATINGS_2YO = {"G1": "100–115", "G2": "95–110", "G3": "90–105", "L": "85–100"}

def band_ratings(band):
    top = int(band.split("-")[1])
    return f"{max(top - 25, 40)}–{top}"

def trip_weight(f):
    return {5: 1.0, 5.5: .6, 6: 1.4, 7: 1.2, 8: 1.4, 8.5: 1.0, 9: .6, 9.5: .8, 10: 1.0, 11: .6, 12: .8, 13: .3, 14: .45,
            16: .35, 18: .1, 20: .05, 22: .02}.get(f, .3)

def pick_trip(crs, lo, hi, used):
    opts = [f for f in C[crs]["trips"] if lo <= f <= hi]
    if not opts:
        opts = sorted(C[crs]["trips"], key=lambda f: min(abs(f - lo), abs(f - hi)))[:1]
    ws = [trip_weight(f) / (1 + 2 * used[f]) for f in opts]
    f = rng.choices(opts, ws)[0]
    used[f] += 1
    return f

def hcap_class(level, kind):
    if kind in ("Festival",):
        return rng.choices([2, 3], [0.75, 0.25])[0]
    if level == "A":
        return rng.choices([2, 3, 4], [0.35, 0.4, 0.25])[0]
    if level == "B":
        return rng.choices([3, 4, 5, 6], [0.1, 0.3, 0.4, 0.2])[0]
    return rng.choices([4, 5, 6], [0.15, 0.4, 0.45])[0]

def trip_name(f):
    if f <= 6: return "Sprint "
    if f <= 9.5: return ""
    if f <= 12: return "Middle-Distance "
    return "Staying "

def make(fx, typ, name, cls, band, ages, sex, f, prize, field, ratings, note=""):
    return dict(type=typ, name=name, cls=cls, band=band, ages=ages, sex=sex, f=f, prize=prize, field=field,
                ratings=ratings, note=note)

def field_range(fx, typ, f, cls):
    cap = C[fx["course"]]["field"]
    if fx["course"] == "Newmarket" and newmarket_course(fx["date"]) == "July Course":
        cap = 20
    if typ in ("Heritage handicap",):
        lo, hi = 16, 30
    elif typ == "Handicap" and fx["kind"] == "Festival":
        lo, hi = 14, 24
    elif typ == "Handicap":
        lo, hi = (8, 16) if cls <= 3 else (7, 14)
    elif typ in ("Group 1",):
        lo, hi = 6, 14
    elif typ in ("Group 2", "Group 3"):
        lo, hi = 6, 12
    elif typ == "Listed":
        lo, hi = 5, 11
    elif typ in ("Novice", "Maiden"):
        lo, hi = (8, 18) if fx["course"] == "Newmarket" else (5, 13)
    elif typ == "Nursery":
        lo, hi = 7, 13
    elif typ in ("Seller", "Claimer", "Classified"):
        lo, hi = 5, 10
    elif typ == "Sales race":
        lo, hi = 12, 25
    else:
        lo, hi = 5, 10
    if C[fx["course"]]["surface"] == "All-weather":
        hi = min(hi, cap)
    hi = min(hi, cap)
    lo = min(lo, hi - 2)
    return f"{lo}–{hi}"

def filler(fx, used, have):
    """One everyday race for this card, chosen to give a real-looking mix."""
    crs, d = fx["course"], fx["date"]
    w = week_of(d)
    lvl = C[crs]["level"]
    kind = fx["kind"]
    winter = w > TURF_WEEKS
    after_new_year = d >= D(2027, 1, 1)
    jt = juv_trips(w, d)
    small = lvl in ("B", "C")
    # weights for each kind of race, by phase
    W = Counter()
    if jt:
        juv = 0.4 if w <= 4 else 0.6 if w <= 10 else 1.0
        if winter: juv = 0.45
        W["2yo novice"] += 1.2 * juv
        W["2yo maiden"] += 0.6 * juv
        W["2yo fillies novice"] += (0.5 if w >= 8 else 0.1) * juv
        if w >= 8 and small: W["2yo restricted novice"] += 0.5 * juv
        if 16 <= w and small: W["2yo seller"] += 0.25
        if w >= 16: W["nursery"] += 1.0 if not winter else 0.6
        if lvl == "A" and w >= 8: W["2yo conditions"] += 0.35
    three = "3yo" if not after_new_year else "3yo"
    if w <= 27 or after_new_year:
        W["3yo maiden"] += 1.1 if w <= 20 else 0.5
        W["3yo novice"] += 0.7 if w <= 20 else 0.3
        W["3yo fillies novice"] += 0.4 if w <= 20 else 0.15
    if w >= 18 and not after_new_year:
        W["3yo+ maiden"] += 0.4
    W["3yo hcap"] += 1.4 if (w <= 22 or after_new_year) else 0.6
    if w <= 10 or after_new_year:
        W["4yo+ hcap"] += 2.6
    else:
        W["3yo+ hcap"] += 3.2
    W["fillies hcap"] += 0.6
    if small:
        W["apprentice hcap"] += 0.5
        W["claimer"] += 0.35
        if lvl == "C" or C[crs]["surface"] == "All-weather":
            W["classified"] += 0.45
            W["seller"] += 0.25
        W["amateur hcap"] += 0.08
    if lvl == "A" or kind in ("Festival", "Premier"):
        W["conditions"] += 0.4
        W["apprentice hcap"] += 0.15
    # no more than one of each youngster kind, and at most two maidens/novices on a 6/7 race card
    cap = {"3yo+ hcap": 4, "4yo+ hcap": 4, "3yo hcap": 2}
    for k in list(W):
        if have[k] >= cap.get(k, 1):
            W[k] = 0
    if have["maidnov"] >= 3:
        for k in list(W):
            if "maiden" in k or "novice" in k: W[k] = 0
    if have["juv"] >= (2 if lvl == "A" or w >= 13 else 1):
        for k in list(W):
            if k.startswith("2yo") or k == "nursery": W[k] = 0
    k = rng.choices(list(W), [W[x] for x in W])[0]
    have[k] += 1
    if "maiden" in k or "novice" in k: have["maidnov"] += 1
    if k.startswith("2yo") or k == "nursery": have["juv"] += 1
    a = "3yo" if not after_new_year else "3yo"
    lvl_cls = {"A": 3, "B": 4, "C": 5}[lvl]
    if k.startswith("2yo"):
        f = pick_trip(crs, min(jt), max(jt), used)
        sex = "F" if "fillies" in k else ""
        if k == "2yo seller":
            return make(fx, "Seller", "Two-Year-Old Selling Stakes", 6, "", "2yo", "", f, 2900, field_range(fx, "Seller", f, 6),
                        "45–65", "The winner is offered for sale at auction after the race")
        if k == "2yo conditions":
            return make(fx, "Conditions", "Two-Year-Old Conditions Stakes", 2, "", "2yo", "", f, 12000,
                        field_range(fx, "Conditions", f, 2), "75–95", "For a good young horse with a run or two")
        if k == "2yo restricted novice":
            return make(fx, "Novice", "Restricted Novice Stakes", 5, "", "2yo", "", f, 4000, field_range(fx, "Novice", f, 5),
                        "unrated", "Only for two-year-olds bought cheaply (Books 3 and 4) or by cheaper stallions")
        typ = "Maiden" if "maiden" in k else "Novice"
        nm = ("Two-Year-Old Fillies' Novice Stakes" if sex else "Two-Year-Old Maiden Stakes" if typ == "Maiden" else "Two-Year-Old Novice Stakes")
        cls = 2 if lvl == "A" and fx["kind"] == "Festival" else lvl_cls
        return make(fx, typ, nm, cls, "", "2yo", sex, f, CLASS_PRIZE[cls] if cls > 2 else 9000, field_range(fx, typ, f, cls),
                    "unrated", "First runs: horses run green" if w <= 12 else "")
    if k == "nursery":
        cls = hcap_class(lvl, kind)
        cls = max(cls, 3)
        band = rng.choice(CLASS_BANDS[cls])
        f = pick_trip(crs, min(jt), max(jt) if w < 30 else 8, used)
        return make(fx, "Nursery", "Nursery Handicap", cls, band, "2yo", "", f, CLASS_PRIZE[cls], field_range(fx, "Nursery", f, cls),
                    band_ratings(band), "A handicap for two-year-olds with a mark")
    if k in ("3yo maiden", "3yo novice", "3yo fillies novice", "3yo+ maiden"):
        lo, hi = (7, 12) if w <= 12 else (6, 14)
        f = pick_trip(crs, lo, hi, used)
        sex = "F" if "fillies" in k else ""
        typ = "Maiden" if "maiden" in k else "Novice"
        ages = "3yo+" if k == "3yo+ maiden" else "3yo"
        nm = {"3yo maiden": "Three-Year-Old Maiden Stakes", "3yo novice": "Three-Year-Old Novice Stakes",
              "3yo fillies novice": "Three-Year-Old Fillies' Novice Stakes", "3yo+ maiden": "Maiden Stakes"}[k]
        cls = lvl_cls if lvl != "A" else rng.choice([3, 4])
        return make(fx, typ, nm, cls, "", ages, sex, f, CLASS_PRIZE[cls], field_range(fx, typ, f, cls), "unrated", "")
    if k in ("3yo hcap", "4yo+ hcap", "3yo+ hcap", "fillies hcap", "apprentice hcap", "amateur hcap"):
        cls = hcap_class(lvl, kind)
        if k in ("apprentice hcap", "amateur hcap"):
            cls = max(cls, 4 if lvl == "A" else 5)
        band = rng.choice(CLASS_BANDS[cls])
        f = pick_trip(crs, 5, 22, used)
        ages = {"3yo hcap": "3yo", "4yo+ hcap": "4yo+"}.get(k, "4yo+" if (w <= 10 or after_new_year) else "3yo+")
        sex = "F" if k == "fillies hcap" else ""
        pre = {"3yo hcap": "Three-Year-Old ", "fillies hcap": "Fillies' ", "apprentice hcap": "Apprentice ",
               "amateur hcap": "Amateur Riders' "}.get(k, "")
        nm = pre + trip_name(f) + "Handicap"
        note = {"apprentice hcap": "Ridden by apprentices: their weight allowance helps", "amateur hcap": "Ridden by amateurs"}.get(k, "")
        pz = CLASS_PRIZE[cls] * (0.85 if k in ("apprentice hcap", "amateur hcap") else 1)
        return make(fx, "Handicap", nm.replace("  ", " "), cls, band, ages, sex, f, int(round(pz, -2)),
                    field_range(fx, "Handicap", f, cls), band_ratings(band), note)
    if k == "claimer":
        f = pick_trip(crs, 5, 12, used)
        cls = 5 if lvl != "C" else 6
        return make(fx, "Claimer", "Claiming Stakes", cls, "", ("4yo+" if (w <= 10 or after_new_year) else "3yo+"), "", f, CLASS_PRIZE[cls],
                    field_range(fx, "Claimer", f, cls), "50–72", "Any runner can be bought (claimed) for its set price")
    if k == "seller":
        f = pick_trip(crs, 5, 12, used)
        return make(fx, "Seller", "Selling Stakes", 6, "", ("4yo+" if (w <= 10 or after_new_year) else "3yo+"), "", f, 2900,
                    field_range(fx, "Seller", f, 6), "40–62", "The winner is offered for sale at auction after the race")
    if k == "classified":
        f = pick_trip(crs, 5, 12, used)
        band = rng.choice(["0-55", "0-50"])
        return make(fx, "Classified", "Classified Stakes", 6, band, ("4yo+" if (w <= 10 or after_new_year) else "3yo+"), "", f, 2900,
                    field_range(fx, "Classified", f, 6), band_ratings(band), "Level weights for horses rated under the cap")
    if k == "conditions":
        f = pick_trip(crs, 5, 16, used)
        return make(fx, "Conditions", "Conditions Stakes", 2, "", ("4yo+" if (w <= 10 or after_new_year) else "3yo+"), "", f, 12000,
                    field_range(fx, "Conditions", f, 2), "85–105", "For useful horses not quite up to Listed class")
    raise ValueError(k)

GTYPE = {"G1": "Group 1", "G2": "Group 2", "G3": "Group 3", "L": "Listed", "HH": "Heritage handicap", "H": "Handicap",
         "C": "Conditions", "S": "Sales race", "M": "Maiden"}

def big_race(fx, r):
    juv = r["ages"].startswith("2yo") and r["ages"] != "2yo+"
    g = r["g"]
    prize = r["prize"] or (PRIZE_2YO.get(g) if juv else None) or PRIZE[g]
    cls = 1 if g in ("G1", "G2", "G3", "L") else (2 if g in ("HH", "H", "C", "S") else 4)
    band = {"HH": "0-105", "H": "0-100"}.get(g, "")
    if g == "H" and prize < 15000: band, cls = "0-90", 3
    ratings = (RATINGS_2YO.get(g) if juv else None) or RATINGS[g]
    if juv and g in ("C", "M", "S"):
        ratings = "unraced or lightly raced"
    typ = GTYPE[g]
    return dict(type=typ, name=r["name"], cls=cls, band=band, ages=r["ages"], sex=r["sex"], f=r["f"], prize=prize,
                field=field_range(fx, typ, r["f"], cls), ratings=ratings, note=r.get("note", ""), big=True,
                round=r.get("round", False))

for key in sorted(fixtures):
    fx = fixtures[key]
    big = fx.get("big", [])
    w = week_of(fx["date"])
    if fx["kind"] == "Festival":
        n = 7
    elif fx["evening"]:
        n = 6
    elif fx["kind"] == "All-weather":
        n = 7
    else:
        n = 7
    n = max(n, len(big))
    used, have = Counter(), Counter()
    card = [big_race(fx, r) for r in big]
    for r in card:
        used[r["f"]] += 1
        if r["ages"] == "2yo": have["juv"] += 1
    while len(card) < n:
        card.append(filler(fx, used, have))
    # order: youngsters and maidens early, the feature in the middle of the card, handicaps late (as real cards run)
    def order(r):
        if r.get("big") and r["type"] in ("Group 1",): return 4.5
        if r.get("big") and r["type"].startswith("Group"): return 3.5
        if r.get("big"): return 3.8
        return {"Novice": 1, "Maiden": 1.5, "Seller": 2, "Claimer": 2.5, "Nursery": 2.8, "Conditions": 3, "Classified": 6,
                "Handicap": 5}.get(r["type"], 5) + (0.4 if "Apprentice" in r["name"] or "Amateur" in r["name"] else 0)
    card.sort(key=order)
    if fx["course"] == "Ascot" and fx["kind"] == "Festival" and fx["date"].month == 6:
        card = [big_race(fx, r) for r in big]   # Royal Ascot keeps the real race order
    start = (17, 30) if fx["evening"] else ((13, 50) if fx["date"].weekday() == 5 else (13, 30))
    if fx["course"] == "Ascot" and fx["date"].month == 6 and 16 <= fx["date"].day <= 20:
        start = (14, 30)
    for i, r in enumerate(card):
        mins = start[0] * 60 + start[1] + 35 * i
        r["time"] = f"{mins // 60 % 12 or 12}:{mins % 60:02d}pm"
        r["no"] = i + 1
    fx["races"] = card

# ------------------------------------------------------------------ flatten
ALL = []
for key in sorted(fixtures):
    fx = fixtures[key]
    d, crs = fx["date"], fx["course"]
    w = week_of(d)
    track = newmarket_course(d) if crs == "Newmarket" else crs
    for r in fx["races"]:
        f = r["f"]
        st = C[crs]["straight"]
        if crs == "Newmarket" and track == "July Course": st = 8
        if r.get("round"): sor = "Round"
        elif st and f <= st: sor = "Straight"
        else: sor = "Round"
        slug = re.sub(r"[^a-z0-9]+", "-", f"{d.isoformat()} {crs} {r['no']}".lower()).strip("-")
        ALL.append(dict(week=w, week_label=week_label(w), date=d.isoformat(), day=DAYS[d.weekday()], course=crs, track=track,
                        meeting=fx["meeting"], kind=fx["kind"], no=r["no"], time=r["time"], race=r["name"], type=r["type"],
                        cls=r["cls"], band=r["band"], ages=r["ages"], sex=r["sex"], dist=r.get("dist") or dist_label(f), f=f,
                        course_type=sor, prize=r["prize"], field=r["field"], ratings=r["ratings"], big=bool(r.get("big")),
                        note=r.get("note", ""), id=slug, phase=phase_of(w)))
# keep the big races' own distance labels
lab = {(r["date"].isoformat(), r["course"], r["name"]): r["dist"] for r in BIG}
for r in ALL:
    if r["big"]:
        r["dist"] = lab.get((r["date"], r["course"], r["race"]), r["dist"])

OUT = HERE / (sys.argv[1] if len(sys.argv) > 1 else "calendar.new.json")   # calendar.json is the agreed draft (the Sheet): only replace it on purpose
json.dump(dict(fixtures=[dict(date=fx["date"].isoformat(), course=fx["course"], meeting=fx["meeting"], kind=fx["kind"],
                               evening=fx["evening"], week=week_of(fx["date"])) for _, fx in sorted(fixtures.items())],
               races=ALL, courses=C), open(OUT, "w"), separators=(",", ":"), default=str)

cnt = Counter(r["type"] for r in ALL)
print(len(fixtures), "meetings", len(ALL), "races")
print(cnt.most_common())
wk = Counter(week_of(fx["date"]) for fx in fixtures.values())
print(sorted(wk.items()))
