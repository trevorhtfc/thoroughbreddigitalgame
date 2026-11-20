// How good must a horse be? One horse of a set ability, with trip and ground to suit, in every Listed and Group race.   node test-group-races.js
require('../data.js'); require('../rules.js'); const TB = require('../reference/season16.js');
// how good does a horse have to be? Put one horse of a set ability in every race of a class it qualifies for.
const out = {};
for (let c = 0; c < 12; c++) { TB.newGame({ seed: 99 + c * 13 }); let S = TB.S;
  for (let f = 0; f < 16; f++) { S.f = f; S.phase = 'yard';
    for (const ab of [100, 106, 112, 116, 120, 124, 128, 132]) for (const age of [2, 3, 4]) {
      for (const r0 of S.fn.races) { if (!['G1', 'G2', 'G3', 'L'].includes(r0.cls)) continue; const save = JSON.stringify(S);
        const h = S.horses[0]; Object.assign(h, { age, pot: ab, trim: 0, mat: 'n', craft: 3, fresh: 100, inj: 0, wins: 5, or: null, temp: 'even', quirk: null, build: 'ver', sex: 'c' });
        const g = TB.ability(h); h.pot = ab + (ab - g); const r = TB.race(r0.id);
        if (TB.eligible(h, r)) { h.trip = Math.min(6, Math.max(0, Math.floor(TB.fIdx(r.f)))); const gg = TB.goingAt(r.co); h.gr = gg == null ? [2, 3] : [Math.max(0, gg - 1), Math.min(4, gg)];
          h.entry = r.id; const res = TB.goRacing(); const k = r.cls + (age === 2 ? ' 2yo' : age === 3 && r.a[1] === 3 ? ' 3yo' : ' open') + ' @' + ab; const o = out[k] = out[k] || { n: 0, w: 0 }; o.n++; if (res[0].mine[0].won) o.w++; }
        TB.use(JSON.parse(save)); S = TB.S; }
    }
    S.phase = 'summary'; S.rd = null; TB.endFortnight(); S = TB.S; if (S.phase === 'winter') break; }
}
for (const cls of ['G1 open', 'G1 3yo', 'G1 2yo', 'G2 open', 'G3 open', 'L open', 'L 2yo']) console.log(cls.padEnd(9), [100, 106, 112, 116, 120, 124, 128, 132].map(ab => { const o = out[cls + ' @' + ab]; return ab + ':' + (o ? (100 * o.w / o.n).toFixed(0) + '%' : '-'); }).join('  '));
