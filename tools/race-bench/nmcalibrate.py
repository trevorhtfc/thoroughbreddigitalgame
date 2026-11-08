# Newmarket par times (8 Nov): the engine's par for each distance, set so the bench's median winning time (12 runners,
# good ground, the Dip included) comes out at the target winning time in courses/newmarket-standards.json.
#   python3 nmcalibrate.py [races] [distances]      then: python3 ../course/newmarket/draft_layout.py
# Writes newmarket-par.json, which draft_layout.py reads when it writes courses/newmarket-standards.json.
import json, sys, warnings, numpy as np
warnings.filterwarnings('ignore')
import racebench as rb
P = json.load(open('settings.json'))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
keys = sys.argv[2].split(',') if len(sys.argv) > 2 else [p['key'] for p in rb.NM_STD['parTimes']]
try: out = json.load(open('newmarket-par.json'))
except FileNotFoundError: out = {"_about": "Written by nmcalibrate.py: the par (seconds) the race engine uses at Newmarket, so its winning times match the targets.", "par": {}, "measured": {}}
for key in keys:
    Q = dict(P); Q['CHECK_DV'] = P['CHECK_DV_BY_COURSE'][rb.kind_of(key)]
    r = rb.run(Q, key, N=N, n=12, seed=8)
    t = r['all']['time']; target = rb.REAL_TIME[key]; par = rb.PAR_TIME[key]
    new = round(par * target / t, 2)
    out['par'][key] = new; out['measured'][key] = {"with par": par, "winning time": t, "target": target}
    print(f"{key:7s} par {par:6.2f} -> winning time {t:6.1f} (target {target}) -> new par {new}", flush=True)
    json.dump(out, open('newmarket-par.json', 'w'), indent=1)
