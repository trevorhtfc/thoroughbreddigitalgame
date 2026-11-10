# Newmarket's Dip in the race (owner, 8 Nov): how much the climb changes who wins (the Rowley Mile's 'nm' races and the
# July Course's 'jc' races).
#   python3 nmdip.py [races] [runners] [distances] ['{"HILL_UP": 2.5, ...}']
# Each distance is run twice with the same horses: on a flat Newmarket (the heights all 0) and with the Dip. Figures:
# winning time and the last 2f; how often the leader 2f out wins; the winner in the back half 2f out; wins by style
# (front-runner, prominent, midfield, hold-up; 1 = its fair share); the best horse on paper.
import json, sys, warnings, numpy as np
warnings.filterwarnings('ignore')
import racebench as rb
P = json.load(open('settings.json'))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600
n = int(sys.argv[2]) if len(sys.argv) > 2 else 14
keys = sys.argv[3].split(',') if len(sys.argv) > 3 else ['nm6f', 'nm1m', 'nm1m2f', 'nm1m4f', 'nm2m']
over = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
def figures(Q, key, flat):
    C = rb.course_of(key); H = C['heights']
    if flat: C['heights'] = dict(H, h=[0.0] * len(H['h']))
    try: r = rb.run(Q, key, N=N, n=n, seed=11)
    finally: C['heights'] = H
    raw = r['raw']; pos = np.asarray(raw['pos']); sty = np.asarray(raw['sty']); Rd = np.asarray(raw['Rday']); r2 = np.asarray(raw['rank2f'])
    fin = np.asarray(raw['fin']); t2 = np.asarray(raw['t2f']); ix = np.arange(N); w = np.argmax(pos == 1, 1)
    best = np.argmax(Rd + np.random.default_rng(0).random(Rd.shape) * 1e-3, 1)
    lead2 = np.argmin(np.where(np.isnan(r2), 99, r2), 1)
    return dict(time=float(np.median(fin[ix, w])), last2f=float(np.median(fin[ix, w] - t2)),
                leader2f_wins=float((lead2 == w).mean()), back_half=float((r2[ix, w] >= n / 2).mean()),
                style={s: round(float((sty[ix, w] == j).mean() / (sty == j).mean()), 2) for j, s in enumerate('FPMH')},
                # horses at the top of their trip (a shade more sprint, a shade less tank) against those at the bottom of it
                speedier=round(float((np.asarray(raw['shade'])[ix, w] == 1).mean() / (np.asarray(raw['shade']) == 1).mean()), 2),
                best=float((pos[ix, best] == 1).mean()))
Q = dict(P); Q.update(over)
print(f"{N} races of {n} runners; settings {json.dumps({k: Q.get(k, 0) for k in ('HILL_UP', 'HILL_DOWN', 'HILL_SLOW')})}")
for key in keys:
    Qk = dict(Q); Qk['CHECK_DV'] = P['CHECK_DV_BY_COURSE'][rb.kind_of(key)]
    a, b = figures(Qk, key, True), figures(Qk, key, False)
    for nm, f in (('flat', a), ('Dip', b)):
        print(f"{key:7s} {nm:4s} time {f['time']:6.1f}  last 2f {f['last2f']:5.2f}  leader 2f out wins {f['leader2f_wins']*100:4.0f}%  "
              f"winner in back half 2f out {f['back_half']*100:4.0f}%  styles {f['style']}  top-of-trip types {f['speedier']}  best wins {f['best']*100:3.0f}%", flush=True)
