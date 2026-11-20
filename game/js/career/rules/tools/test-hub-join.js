// Proof that the rules join the career hub: whole careers played week by week on the hub's real calendar (data.js),
// through hub-adapter.js. A cautious robot: the trainer's own picks, one gallop a week, plain buying in the winter.
//   node test-hub-join.js [careers] [seasons] [path to the hub's js/career/data.js]
const path = require('path');
globalThis.window = globalThis;
require(process.argv[4] ? path.resolve(process.argv[4]) : path.join(__dirname, '../../data.js'));
const R = require('../rules.js'), J = require('../hub-adapter.js');
const D = globalThis.CAREER_DATA, N = +process.argv[2] || 12, YEARS = +process.argv[3] || 6, FEE = +process.env.FEE || 150;   // £ a week in training (the hub's figure)
// the hub's own way of reading its data (core.js: MEET, RACES)
const MEET = D.meetings.map((m, i) => ({ i, date: m[0], course: m[1], name: m[2], week: m[5], aw: D.courses[m[1]].surface !== 'Turf' }));
const RACES = D.races.map((r, i) => { const o = { id: i, m: MEET[r[0]], name: r[2], type: r[3], cls: r[4], band: r[5], ages: r[6], sex: r[7], f: r[8], prize: r[11], lo: r[12], hi: r[13], big: !!r[15] };
  o.hcap = o.type === 'Handicap' || o.type === 'Heritage handicap' || o.type === 'Nursery'; o.top = o.band ? +o.band.split('-')[1] : null; return o; });
const NW = D.weeks.length, BYWEEK = Array.from({ length: NW + 1 }, () => []); for (const r of RACES) if (r.type !== 'Sales race' && !/All-Weather Championships Finals/.test(r.m.name)) BYWEEK[r.m.week].push(r);
J.setup(D);
const GN = ['Heavy', 'Softer', 'Good', 'Quicker', 'Quick'], agg = Array.from({ length: YEARS }, () => ({ cash: [], tier: [], runs: 0, wins: 0, prize: 0, horses: 0, top: [] })), lab = [0, 0, 0, 0, 0].map(() => ({ n: 0, w: 0 })), cls = {};
for (let c = 0; c < N; c++) {
  const E = R.init({}, 500 + c * 91); E.cash = 60000; E.horses.push(...R.starters());
  for (let y = 0; y < YEARS; y++) {
    for (let w = 1; w <= NW; w++) {
      J.startWeek(E, w); const winter = D.weeks[w - 1].winter, going = {}, base = (() => { const x = R.rnd() * 100, o = w <= 6 || w >= 27 ? [8, 35, 70, 92] : [2, 11, 36, 69]; return x < o[0] ? 0 : x < o[1] ? 1 : x < o[2] ? 2 : x < o[3] ? 3 : 4; })();
      const races = BYWEEK[w].map(r => { if (going[r.m.i] === undefined) going[r.m.i] = GN[Math.max(0, Math.min(4, base + (R.rnd() < 0.15 ? -1 : R.rnd() > 0.85 ? 1 : 0)))]; return J.raceFor(E, r, going[r.m.i]); });
      let gal = 1; for (const h of E.horses) { if (!gal) break; if (h.fresh < 55) { if (R.gallop(h, 'easy')) gal--; } else if (h.k.pw > 8) { if (R.gallop(h, 'work')) gal--; } }
      const taken = {};
      for (const h of E.horses) { const dear = R.valueOf(h) > 8000, open = races.filter(r => !taken[r.id] && !(dear && r.cls === 'S')), r = R.autoPick(h, open);   /* sellers and claimers can lose you the horse (the hub's rule), so only cheap horses go there */ if (!r) continue; taken[r.id] = 1; const v = R.view(h, r), res = R.runRace(r, [h]), m = res.mine[0];
        agg[y].runs++; lab[v.lv].n++; const k = cls[r.cls] = cls[r.cls] || { n: 0, w: 0 }; k.n++; if (m.won) { agg[y].wins++; lab[v.lv].w++; k.w++; } agg[y].prize += m.prize; }
      const weeks = winter ? 4 : 1; R.cash(-E.horses.length * FEE * weeks, 'fees'); J.endWeek(E, weeks);
    }
    const a = agg[y]; a.cash.push(E.cash); a.tier.push(R.tier()); a.horses += E.horses.length; a.top.push(Math.max(0, ...E.horses.map(h => h.or || 0)));
    // the winter's business, then 1 January
    for (const h of E.horses.slice()) { if (h.age >= 7 || (h.age >= 5 && (h.or || 0) < 60 + R.tier() * 6) || (h.age >= 3 && h.runs >= 5 && (h.or || 0) < 44 + R.tier() * 6)) { if (h.sex === 'f' && h.peak >= 80 && E.mares.length < R.T().pad) R.retire(h.id); else R.sell(h.id); } }
    const lots = R.genSale(); for (const l of lots) { if (l.ty === 'm') { R.pass(l); continue; } const lim = Math.min(l.guide * (l.ty === 'y' ? [0.6, 0.95, 1.3, 1.7][l.wh] : 1), E.cash * 0.6 - 8000); let r = null; while (R.boxesFree() > 0 && R.nextBid(l) <= lim && (r = R.bid(l)) === 'raised'); if (r !== 'won') R.pass(l); }
    for (const m of E.mares) { const s = R.sires().filter(x => x.fee <= E.cash * 0.2).sort((p, q) => q.stars - p.stars || p.fee - q.fee)[0]; if (s) R.setCover(m.id, s.n); }
    R.newYear();
  }
}
const avg = a => a.reduce((x, y) => x + y, 0) / (a.length || 1), med = a => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)];
console.log(`${N} careers of ${YEARS} seasons on the hub's calendar (${RACES.length} races, ${NW} turns), fees £${FEE} a week`);
console.log('season  cash(median)  tier  horses  runs/horse  win%  prize/horse  best rating');
agg.forEach((a, y) => console.log(String(y + 1).padStart(4), String(Math.round(med(a.cash) / 1000) + 'k').padStart(12), avg(a.tier).toFixed(2).padStart(7), (a.horses / N).toFixed(1).padStart(6), (a.runs / a.horses).toFixed(1).padStart(10), (100 * a.wins / a.runs).toFixed(0).padStart(7), ('£' + Math.round(a.prize / a.horses / 100) / 10 + 'k').padStart(11), avg(a.top).toFixed(0).padStart(10)));
console.log('trainer\'s chip -> won:', ['Outclassed', 'Place chance', 'In the mix', 'Big chance', 'Hard to beat'].map((l, i) => `${l} ${(100 * lab[i].w / (lab[i].n || 1)).toFixed(0)}% (${lab[i].n})`).join(' | '));
console.log('runs by class:', Object.keys(cls).sort().map(k => `${k} ${cls[k].n}`).join('  '));
