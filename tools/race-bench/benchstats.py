# The bench's figures for every distance, as JSON, for race-engine/check/compare.mjs to set beside the engine's.
#   python3 benchstats.py [races per distance] [runners] [out.json] [seed] [distances, e.g. r1m6f,r2m]
# Same figures as distcheck.py (and the same way of working them out), plus wins by style for each pace.
import json, sys, time, warnings, numpy as np
warnings.filterwarnings('ignore')
from racebench import run, PAR_TIME
P = json.load(open('settings.json'))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
out = sys.argv[3] if len(sys.argv) > 3 else 'benchstats.json'
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 8
only = sys.argv[5].split(',') if len(sys.argv) > 5 else list(PAR_TIME)
res = {}
for key in only:
    t0 = time.time()
    Q = dict(P); Q['CHECK_DV'] = P['CHECK_DV_BY_COURSE']['straight' if key[0] == 's' else 'round']
    r = run(Q, key, N=N, n=n, seed=seed)
    raw = r['raw']; Rd = np.asarray(raw['Rday']); pos = np.asarray(raw['pos']); sty = np.asarray(raw['sty']); lvl = np.asarray(raw['lvl']); L = np.asarray(raw['lost'])
    ix = np.arange(N); w = np.argmax(pos == 1, 1)
    best = np.argmax(Rd + np.random.default_rng(0).random(Rd.shape) * 1e-3, 1)
    th = np.array_split(np.arange(n), 3)
    by_pace = {}
    for k, nm in enumerate(['slow', 'even', 'strong', 'fast']):
        m = lvl == k
        if m.sum() < 20: continue
        by_pace[nm] = {s: float((sty[m][np.arange(m.sum()), w[m]] == j).mean() / max((sty[m] == j).mean(), 1e-9)) for j, s in enumerate('FPMH')}
    res[key] = dict(
        races=N, runners=n,
        time=float(r['all']['time']), margin=float(r['all']['margin']),
        best=float((pos[ix, best] == 1).mean()),
        style={s: float((sty[ix, w] == j).mean() / (sty == j).mean()) for j, s in enumerate('FPMH')},
        draw={nm: float(np.isin(w, c).mean() / (len(c) / n)) for nm, c in zip(['low', 'mid', 'high'], th)},
        lose1=float((L >= 1).mean()), lost=float(L.mean()),
        paceMix={nm: float((lvl == k).mean()) for k, nm in enumerate(['slow', 'even', 'strong', 'fast'])},
        byPace=by_pace,
    )
    print(key, round(time.time() - t0), 's', json.dumps({k: v for k, v in res[key].items() if k in ('time', 'best', 'style', 'lose1')}), flush=True)
    json.dump(res, open(out, 'w'), indent=1)
