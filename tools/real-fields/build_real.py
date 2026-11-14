"""Turn the saved Racing Post result CSVs into the game's real-fields file.
Usage: python3 build_real.py <csv dir> <meeting id> <year> <out.js>"""
import csv, json, math, os, re, sys

TITLES = {"Dr", "Sir", "Mrs", "Mr", "Ms", "Bt"}

def person(p):
    p = re.sub(r"\^\S*", "", p).strip()
    toks = [t for t in p.split() if t not in TITLES]
    sir = p.startswith("Sir ")
    mrs = p.startswith("Mrs ")
    if not toks:
        return p
    first = toks[0]
    if "-" in first and len(first) <= 4:          # F-H Graffard
        first = first[0]
    # initials-only first names (A P O'Brien, K R Burke, W J Lee): first initial, then the surname
    rest = toks[1:]
    while rest and len(rest) > 1 and len(rest[0]) <= 2 and rest[0].isupper():
        rest = rest[1:]
    # middle names before a surname (Joseph Patrick O'Brien, Donnacha Aidan O'Brien): keep the last word,
    # or the last two for particles (De Sousa, De La Sayette, Browne McMonagle)
    if len(rest) >= 2:
        keep = 1
        while keep < len(rest) and rest[-keep - 1] in ("De", "La", "Le", "Van", "Von", "Di", "Du", "Al", "El", "bin", "Browne", "Johnson", "Philippart"):
            keep += 1
        rest = rest[-keep:]
    out = f"{first[0]}. {' '.join(rest)}" if rest else first
    return ("Sir " if sir else "Mrs " if mrs else "") + out

def abbrev(s):
    parts = [x.strip() for x in s.split("&")]
    if len(parts) == 2 and len(parts[0].split()) == 1:      # "John & Thady Gosden" -> J. & T. Gosden
        b = person(parts[1]); return f"{parts[0][0]}. & {b}"
    return " & ".join(person(x) for x in parts)

def dec(sp):
    sp = sp.replace("F", "").replace("J", "").replace("C", "").strip()
    if sp.lower().startswith("evens"): return 1.0
    a, b = sp.split("/"); return float(a) / float(b)

def num(x):
    try: return float(x)
    except: return None

def build_race(rows):
    runners = []
    for r in rows:
        runners.append(dict(name=r["horse"].strip(), draw=int(r["draw"]) if r["draw"].isdigit() else 0,
            sp=r["sp"].strip(), dec=dec(r["sp"]), age=int(r["age"]) if r["age"].isdigit() else None,
            orr=num(r["or"]), rpr=num(r["rpr"]), pos=r["pos"].strip(), btn=num(r["total_btn"]),
            jockey=abbrev(r["jockey"]), trainer=abbrev(r["trainer"]), trainerFull=r["trainer"].strip()))
    # the market: the field's chances from the starting prices, with the bookmakers' margin taken out
    p = [1 / (x["dec"] + 1) for x in runners]; tot = sum(p); p = [x / tot for x in p]
    rated = [x["orr"] for x in runners if x["orr"]]
    anchor = sum(rated) / len(rated) if rated else None
    if anchor is None:                      # an unrated field (two-year-olds): the Racing Post ratings set the level
        rp = sorted([x["rpr"] for x in runners if x["rpr"]], reverse=True)
        anchor = sum(rp[:max(1, len(rp) // 2)]) / max(1, len(rp) // 2)
    lg = sum(math.log(x) for x in p) / len(p)
    for x, pi in zip(runners, p):
        mkt = anchor + 7 * (math.log(pi) - lg)          # the game's market: 5lb better is about twice the chance
        base = x["orr"] if x["orr"] else mkt
        perf = x["rpr"] if x["rpr"] is not None else base - 10
        perf = max(perf, base - 10)                      # a bad day costs a little, not everything
        if x["orr"]:
            v = 0.45 * x["orr"] + 0.30 * perf + 0.25 * mkt
        else:
            v = 0.55 * perf + 0.45 * mkt
        x["rating"] = round(v)
    return runners

def main(src, meeting, year, out):
    races = {}
    for f in sorted(os.listdir(src)):
        if not f.endswith(".csv"): continue
        with open(os.path.join(src, f)) as fh:
            rows = list(csv.DictReader(fh))
        rr = build_race(rows)
        races[f[:-4]] = [dict(n=x["name"], j=x["jockey"], t=x["trainer"], tf=x["trainerFull"], sp=x["sp"].replace("J", "F") if x["sp"].endswith("J") else x["sp"],
                              r=x["rating"], d=x["draw"], p=x["pos"], b=x["btn"], a=x["age"]) for x in rr]
    js = ("// Real fields (owner, 14 Nov 2026: \"just get the names jockey silks trainers odds and results to form a decent vibe\n"
          "// on the horses ability\"). Written by tools/real-fields/build_real.py from the Racing Post results; don't edit by hand.\n"
          "// Per race, in finishing order: n name, j jockey and t trainer (shortened, as R. Moore), tf the trainer in full (for\n"
          "// the colours), sp the starting price, r the game rating worked out from the official rating, the Racing Post rating\n"
          "// on the day and the market, d the draw, p the place, b lengths behind the winner, a age.\n"
          f"window.REAL_FIELDS = window.REAL_FIELDS || {{}};\nwindow.REAL_FIELDS[{json.dumps(meeting)}] = {{ year: {year}, races: {{\n")
    js += ",\n".join(f"  {json.dumps(k)}: [\n" + ",\n".join("    " + json.dumps(x, ensure_ascii=False, separators=(",", ":")) for x in v) + "\n  ]" for k, v in races.items())
    js += "\n} };\n"
    open(out, "w").write(js)
    print(len(races), "races,", sum(len(v) for v in races.values()), "runners ->", out)

if __name__ == "__main__":
    main(*sys.argv[1:5])
