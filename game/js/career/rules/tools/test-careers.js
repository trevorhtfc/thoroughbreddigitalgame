// Robot careers on the reference game (16 fortnights): the trainer's picks, cautious buying.   node test-careers.js [careers] [seasons]
require('../data.js'); require('../rules.js'); const TB = require('../reference/season16.js');
const N = +process.argv[2] || 40, YEARS = +process.argv[3] || 16;
const agg = Array.from({ length: YEARS }, () => ({ cash: [], tier: [], wins: [], runs: [], prize: [], top: [], n: [], g1: 0, classic: 0, bust: 0 }));
let frankel = 0, firstG1 = [], tierAt = [[], [], [], [], [], []], wr = { n: 0, w: 0 }, lab = [0, 0, 0, 0, 0].map(() => ({ n: 0, w: 0, p: 0 }));
for (let c = 0; c < N; c++) {
  TB.newGame({ seed: 1000 + c * 77 }); let S = TB.S, g1Season = null, reached = {};
  for (let y = 0; y < YEARS; y++) {
    while (S.phase !== 'winter') {
      for (const h of S.horses) { if (S.gal <= 0) break; if (h.fresh < 60 && h.fresh < 100) TB.gallop(h.id, 'easy'); else if (h.k.pw > 8 || h.craft < 2) TB.gallop(h.id, h.craft < 2 && h.runs > 0 ? 'school' : 'work'); }
      TB.autoEnter();
      for (const h of S.horses) if (h.entry != null) { const v = TB.view(h, TB.race(h.entry)); lab[v.lv].n++; h._lv = v.lv; }
      const res = TB.goRacing();
      for (const r of res) for (const m of r.mine) { wr.n++; const h = TB.horse(m.hid); if (m.won) { wr.w++; if (h) lab[h._lv].w++; } if (m.pos <= 3 && h) lab[h._lv].p++; }
      TB.endFortnight(); S = TB.S;
    }
    const a = agg[y]; a.cash.push(S.cash); a.tier.push(TB.tier()); a.wins.push(S.w.review.wins); a.runs.push(S.w.review.runs); a.prize.push(S.w.review.prize); a.n.push(S.horses.length);
    a.top.push(Math.max(0, ...S.horses.map(h => h.or || 0))); a.g1 += S.w.review.g1; a.classic += S.w.review.classic; if (S.cash < 0) a.bust++;
    if (S.w.review.g1 && g1Season == null) g1Season = y + 1; const t = TB.tier(); if (!reached[t]) { reached[t] = 1; tierAt[t].push(y + 1); }
    // winter
    for (const h of S.horses) { const v = TB.estAb(h); S.w.plan[h.id] = h.age >= 7 ? (TB.canStud(h) && (h.sex === 'c' || S.mares.length < TB.T().pad) ? 'stud' : 'sell') : (h.age >= 5 && (h.or || 0) < 60 + TB.tier() * 6) || (h.age >= 3 && h.runs >= 5 && (h.or || 0) < 44 + TB.tier() * 6) || (h.age >= 4 && h.sr <= 2) ? 'sell' : (h.sex === 'f' && h.age >= 4 && h.peak >= 80 && S.mares.length < TB.T().pad) ? 'stud' : (h.sex === 'c' && h.age >= 4 && h.g1 > 0) ? 'stud' : 'keep'; }
    { let free = TB.T().boxes - S.horses.filter(h => S.w.plan[h.id] === 'keep').length; for (const y of TB.arriving()) { if (free > 0) free--; else S.w.yplan[y.id] = 'sell'; } }
    TB.applyStable();
    S.w.lots.forEach((l, i) => { if (l.ty === 'm') { if (S.mares.length < TB.T().pad && l.guide < S.cash * 0.15) { let r; while ((r = TB.bid(i)) === 'raised' && TB.nextBid(l) < l.guide * 1.1) ; if (r === 'raised') TB.pass(i); } else TB.pass(i); return; }
      const lim = Math.min(l.guide * (l.ty === 'y' ? [0.6, 0.95, 1.3, 1.7][l.wh] : 1), S.cash * 0.6 - 8000); let r = null;
      while (TB.boxesFree() > 0 && TB.nextBid(l) <= lim && (r = TB.bid(i)) === 'raised') ; if (r !== 'won') TB.pass(i); });
    TB.closeSale();
    for (const m of S.mares) { const ss = TB.sires().filter(s => s.fee <= S.cash * 0.2).sort((a, b) => b.stars - a.stars || a.fee - b.fee); if (ss[0]) TB.setCover(m.id, ss[0].n); }
    TB.startSeason(); S = TB.S;
  }
  if (S.top && S.top.or >= 130) frankel++; if (g1Season) firstG1.push(g1Season);
}
const avg = a => a.length ? (a.reduce((x, y) => x + y, 0) / a.length) : 0, med = a => a.slice().sort((x, y) => x - y)[Math.floor(a.length / 2)];
console.log('yr  cash(med)   tier  horses  runs  wins  prize(avg)  topOR  G1/career classic bust');
agg.forEach((a, y) => console.log(String(y + 1).padStart(2), String(Math.round(med(a.cash) / 1000) + 'k').padStart(9), avg(a.tier).toFixed(2).padStart(6), avg(a.n).toFixed(1).padStart(6), avg(a.runs).toFixed(0).padStart(6), avg(a.wins).toFixed(1).padStart(5), String(Math.round(avg(a.prize) / 1000) + 'k').padStart(9), avg(a.top).toFixed(0).padStart(7), (a.g1 / N).toFixed(2).padStart(8), (a.classic / N).toFixed(2).padStart(6), a.bust));
console.log('win rate', (wr.w / wr.n).toFixed(3), 'runs', wr.n, '| careers with a 130+ horse:', frankel, '/', N, '| first G1 season avg', avg(firstG1).toFixed(1), 'in', firstG1.length, 'careers');
console.log('tier reached at season (avg, n):', [2, 3, 4, 5].map(t => t + ': ' + avg(tierAt[t]).toFixed(1) + ' (' + tierAt[t].length + ')').join('  '));
console.log('trainer label -> actual win%, place%:', ['Outclassed', 'Place chance', 'In the mix', 'Big chance', 'Hard to beat'].map((l, i) => l + ' ' + (100 * lab[i].w / (lab[i].n || 1)).toFixed(0) + '/' + (100 * lab[i].p / (lab[i].n || 1)).toFixed(0) + ' (n' + lab[i].n + ')').join(' | '));
