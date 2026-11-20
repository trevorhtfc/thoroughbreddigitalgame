// =====================================================================================================================
// "Thoroughbred Career", the reference host for the rules (rules.js): a season of 16 fortnights, the big races of each
// fortnight plus four everyday meetings, one screenful of decisions a turn, and a winter of selling, buying and
// covering. It shows the order a host calls the rules in. The screens are in ui.js.
// =====================================================================================================================
(function (root) {
'use strict';
const R = root.TBRULES, D = R.D;
const { CLS, TIERS, rnd, ri, pick, clamp, wpick, gauss, nice, tier, T, ctype, isAW, genField, valueOf, sell, retire, canStud, yearlingValue, horse, guideOf } = R;
const NF = 16;                                   // fortnights in a season
const FN = [['The Lincoln', '23 Mar – 5 Apr'], ['The Craven Meeting', '6 – 19 Apr'], ['The Guineas', '20 Apr – 3 May'], ['Chester and the Dante', '4 – 17 May'],
  ['The Temple Stakes', '18 – 31 May'], ['The Derby', '1 – 14 Jun'], ['Royal Ascot', '15 – 28 Jun'], ['The Eclipse and the July Cup', '29 Jun – 12 Jul'],
  ['The King George', '13 – 26 Jul'], ['Glorious Goodwood', '27 Jul – 9 Aug'], ['The Ebor Festival', '10 – 23 Aug'], ['The Sprint Cup', '24 Aug – 6 Sep'],
  ['The St Leger', '7 – 20 Sep'], ['The Cambridgeshire', '21 Sep – 4 Oct'], ['Champions Day', '5 – 18 Oct'], ['The Futurity', '19 Oct – 8 Nov']];
const ROTA = { a: ['Wolverhampton', 'Southwell', 'Chelmsford', 'Newcastle', 'Kempton'], s: ['Thirsk', 'Catterick', 'Ripon', 'Windsor', 'Musselburgh'], u: ['Brighton', 'Pontefract', 'Beverley', 'Hamilton', 'Carlisle'], g: ['Bath', 'Leicester', 'Nottingham', 'Yarmouth', 'Salisbury', 'Redcar'] };
const FEE = 500, MARE_FEE = 200;
let S = null;
// saves from before the rules were split out (v1) are brought up to date
function migrate(g) {
  if (!g || g.v !== 1) return g;
  g.prog = g.phase === 'winter' ? 1 : g.f / (NF - 1); g.clock = (g.season - 1) * 22 + g.f;
  for (const h of g.horses) h.last = h.last < 0 ? -99 : g.clock - (g.f - h.last);
  if (g.fn) for (const r of g.fn.races) { r.g = g.fn.going[r.co]; r.ty = ctype(r.co); }
  g.v = 2; return g;
}
const use = g => { S = migrate(g); R.use(S); return S; };
function newGame(o) {
  S = { v: 2, stable: o.stable || 'Your Stable', silk: o.silk || { b: '#3d7153', b2: '#e9bc65', p: 'chevron', s: '#3d7153', c: '#e9bc65' }, cash: 60000, f: 0, phase: 'yard', hist: [], gal: 2, seenTier: 1, tips: {} };
  R.init(S, o.seed); S.horses.push(...R.starters()); setGoals(); buildFortnight();
  return S;
}

// ---------------------------------------------------------------- a fortnight's racing
function drawGoing(f) { const w = f <= 2 || f >= 13 ? [8, 27, 35, 22, 8] : f <= 4 || f >= 11 ? [3, 15, 34, 32, 16] : [2, 9, 25, 33, 31]; let x = rnd() * 100; for (let i = 0; i < 5; i++) { x -= w[i]; if (x <= 0) return i; } return 2; }
function buildFortnight() {
  const f = S.f, races = [], base = drawGoing(f), going = {}, used = {};
  const add = o => { o.id = f * 100 + races.length; if (CLS[o.cls].cap) o.cap = o.cap || CLS[o.cls].cap; races.push(o); return o; };
  const big = D.big[f]; let main = null; { const c = {}; for (const b of big) { const w = b.g === 'G1' ? 5 : b.g === 'G2' || b.g === 'HH' ? 2 : 1; c[b.co] = (c[b.co] || 0) + w; } main = Object.keys(c).sort((x, y) => c[y] - c[x])[0] || 'Newmarket'; }
  for (const b of big) add({ n: b.n, co: b.co, cls: b.g === 'M' ? 'M' : b.g, f: b.f, a: b.a.slice(), sx: b.sx, p: b.p, big: 1 });
  // the everyday meetings: one all-weather, one sharp, one undulating, one galloping track
  const ev = ['a', 's', 'u', 'g'].map((k, i) => ROTA[k][(f + i * 2 + S.season) % ROTA[k].length]);
  let ei = 0; const evc = () => ev[(ei++) % 4], alt = (a, b, k) => (f + k) % 2 ? a : b;
  const t2 = f <= 2 ? [5] : f <= 5 ? [5, 6] : f <= 8 ? [6, 7] : f <= 11 ? [6, 7, 8] : [7, 8, 10];
  t2.forEach(t => add({ n: 'Maiden Stakes', co: evc(), cls: 'M', f: t, a: [2, 2], sx: '', p: 8 }));
  t2.slice(0, 2).forEach(t => add({ n: 'Auction Maiden', co: evc(), cls: 'MA', f: t, a: [2, 2], sx: '', p: 5 }));
  if (f >= 3) add({ n: 'Novice Stakes', co: evc(), cls: 'N', f: t2[Math.min(1, t2.length - 1)], a: [2, 2], sx: '', p: 10 });
  if (f >= 9) [['C5', 7], ['C4', 10], ['C3', 15]].forEach(([c, p], i) => add({ n: 'Nursery', co: evc(), cls: c, f: t2[i % t2.length], a: [2, 2], sx: '', p }));
  (f <= 7 ? [alt(6, 7, 0), 8, alt(10, 12, 1)] : [6, 8, 12]).forEach(t => add({ n: f <= 7 ? 'Maiden Stakes' : 'Maiden Stakes', co: evc(), cls: 'M', f: t, a: f <= 7 ? [3, 3] : [3, 7], sx: '', p: 8 }));
  const bands = [[5, 6], [7, 8], [10, 12], [14, 16]];
  [['C6', 5], ['C5', 7], ['C4', 10], ['C3', 15]].forEach(([c, p], ci) => bands.forEach((bd, bi) => add({ n: 'Handicap', co: evc(), cls: c, f: alt(bd[0], bd[1], ci + bi), a: [3, 7], sx: '', p })));
  [0, 1, 2, 3].filter(i => i !== f % 4).forEach(bi => add({ n: 'Handicap', co: main, cls: 'C2', f: alt(bands[bi][0], bands[bi][1], bi), a: [3, 7], sx: '', p: 28 }));
  for (const r of races) { if (going[r.co] === undefined) { const x = rnd(); going[r.co] = isAW(r.co) ? null : clamp(base + (x < 0.15 ? -1 : x > 0.85 ? 1 : 0), 0, 4); } }
  S.fn = { f, base, going, races, main, ev };
  S.prog = f / (NF - 1);
  for (const r of races) { r.g = going[r.co]; r.ty = ctype(r.co); R.prepRace(r); }
  for (const h of S.horses) h.entry = null;
  S.gal = T().gal; R.clearViews();
}
const goingAt = co => S.fn.going[co];
const race = id => S.fn.races.find(r => r.id === id);
const options = h => R.options(h, S.fn.races), picks = h => R.picks(h, S.fn.races);
function enter(hid, rid) { horse(hid).entry = rid == null ? null : rid; }
function autoEnter() { let n = 0; for (const h of S.horses) { if (h.entry != null) continue; const r = R.autoPick(h, S.fn.races); if (r) { h.entry = r.id; n++; } } return n; }
function gallop(hid, type) { if (S.gal <= 0) return null; const r = R.gallop(horse(hid), type); if (r) S.gal--; return r; }

function goRacing() {
  const ids = [...new Set(S.horses.filter(h => h.entry != null).map(h => h.entry))].map(race).sort((a, b) => a.p - b.p);
  const cash0 = S.cash, res = ids.map(r => R.runRace(r, S.horses.filter(h => h.entry === r.id)));
  S.rd = { res, i: 0, cash0, repBefore: S.rep - res.reduce((a, x) => a + x.mine.reduce((b, y) => b + y.rep, 0), 0) }; S.phase = res.length ? 'raceday' : 'summary';
  return res;
}
function endFortnight() {
  const fees = S.horses.length * FEE + S.mares.length * MARE_FEE; R.cash(-fees, 'fees'); S.ss.fees += fees;
  R.rest(); for (const h of S.horses) h.entry = null;
  S.rd = null; S.f++; S.clock++;
  if (S.f >= NF) startWinter(); else { S.phase = 'yard'; buildFortnight(); }
}
function skipToWinter() { while (S.phase !== 'winter') { S.rd = null; endFortnight(); } }
const fortnightFees = () => S.horses.length * FEE + S.mares.length * MARE_FEE;

// ---------------------------------------------------------------- goals for the season
const GOALS = [null,
  [['wins', 3, 'Win 3 races'], ['prize', 30000, 'Win £30,000 in prize money'], ['w2', 1, 'Win a race with a two-year-old']],
  [['wins', 5, 'Win 5 races'], ['best', 6, 'Win a Class 3 handicap or better'], ['prize', 70000, 'Win £70,000 in prize money']],
  [['best', 10, 'Win a Listed race or better'], ['prize', 180000, 'Win £180,000 in prize money'], ['wins', 8, 'Win 8 races']],
  [['best', 13, 'Win a Group 2 or better'], ['prize', 450000, 'Win £450,000 in prize money'], ['pat', 3, 'Win 3 Listed or Group races']],
  [['g1', 1, 'Win a Group 1'], ['classic', 1, 'Win a Classic'], ['prize', 1000000, 'Win £1,000,000 in prize money']]];
const GREW = [null, [10, 3000], [22, 8000], [55, 20000], [130, 50000], [220, 100000]];
function setGoals() { const t = tier(); S.ss = R.newSeasonStats(); S.goals = GOALS[t].map(g => ({ k: g[0], n: g[1], t: g[2], rep: GREW[t][0], cash: GREW[t][1] })); }
const goalDone = g => S.ss[g.k] >= g.n;

// ---------------------------------------------------------------- winter: review, who stays, the sales, the stud
function startWinter() {
  S.phase = 'winter'; S.prog = 1; const done = S.goals.map(goalDone); let rep = 0, cash = 0; S.goals.forEach((g, i) => { if (done[i]) { rep += g.rep; cash += g.cash; } });
  S.rep += rep; S.cash += cash; const best = S.horses.filter(h => h.sr > 0).sort((a, b) => (b.or || 0) - (a.or || 0))[0];
  S.w = { step: 0, plan: {}, yplan: {}, review: Object.assign({}, S.ss, { done, grep: rep, gcash: cash, best: best ? { n: best.n, or: best.or } : null, tier1: tier() }), lots: null };
  S.hist.push({ s: S.season, wins: S.ss.wins, runs: S.ss.runs, prize: S.ss.prize, tier: tier() });
  for (const h of S.horses) { S.w.plan[h.id] = h.age >= 7 ? (canStud(h) && (h.sex === 'c' || S.mares.length < T().pad) ? 'stud' : 'sell') : 'keep'; if (h.k.mat < 2) { h.k.mat = 2; h.gs.mat = h.mat; h.kv++; } }
  for (const y of S.young) S.w.yplan[y.id] = 'keep';
}
function applyStable() {
  for (const h of S.horses.slice()) { const p = S.w.plan[h.id]; if (p === 'sell') sell(h.id); else if (p === 'stud') { if (!retire(h.id)) sell(h.id); } }
  for (const y of S.young.slice()) if (S.w.yplan[y.id] === 'sell') { S.cash += yearlingValue(y); S.young = S.young.filter(x => x !== y); }
  if (!S.horses.length && S.cash < 15000) { S.cash = 15000; S.w.loan = 1; }   // never leave a player with nothing to bid with
  S.w.lots = R.genSale(); S.w.step = 2;
}
function closeSale() { S.w.lots.forEach((l, i) => pass(i)); S.w.step = 3; }
const bid = i => R.bid(S.w.lots[i]), pass = i => R.pass(S.w.lots[i]);
function startSeason() { R.newYear(); S.clock += 6; S.f = 0; S.w = null; S.phase = 'yard'; setGoals(); buildFortnight(); }

const TB = Object.assign({}, R, { NF, FN, FEE, MARE_FEE, use, newGame, goingAt, race, options, picks, enter, autoEnter, gallop, goRacing, endFortnight, skipToWinter, fortnightFees, goalDone,
  applyStable, closeSale, bid, pass, startSeason });
Object.defineProperty(TB, 'S', { get: () => S, enumerable: true });
root.TB = TB; if (typeof module !== 'undefined') module.exports = TB;
})(typeof window !== 'undefined' ? window : globalThis);
