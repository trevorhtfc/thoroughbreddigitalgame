// =====================================================================================================================
// Thoroughbred career: THE RULES (horses, discovery, the trainer's view, race day, the handicapper, sales, the stud).
// No screen code, no calendar and no clock of its own: a host game owns the year, the races on offer and the turns,
// and calls in here. Two hosts exist: reference/season16.js (the "Thoroughbred Career" prototype, 16 fortnights) and,
// once joined, the career hub (weekly, on the real calendar). See README.md beside this file.
//
// The state these rules need lives in one plain object E (it can be the host's own save object): rs, nid, used, horses,
// mares, young, studs, stars, rep, cash, season, prog, clock, ss, troph, hof, top. TBRULES.init(E, seed) adds whatever
// is missing; TBRULES.use(E) points the rules at it (call it after loading a save).
// The host keeps two numbers up to date: E.prog (0 at the first turf turn of the year, 1 at the last) and E.clock (a
// count of turns that never goes back). Money and reputation change only through cash() and addRep(), which also call
// TBRULES.on.money / on.rep so a host can keep a ledger.
// =====================================================================================================================
(function (root) {
'use strict';
let D = root.TBDATA || null;                      // stallions, mares, name lists, silks: see README (setData to supply your own)
const setData = d => { D = d; };
const CFG = { tpf: 1 };                           // turns per fortnight: 1 for fortnightly turns, 2 for weekly
const ON = { money: null, rep: null };            // host hooks: (amount, why, horse)
const TRIPS = ['5f', '6f', '7f', '1m', '1m2f', '1m4f', '1m6f', '2m+'], TRIPF = [5, 6, 7, 8, 10, 12, 14, 16];
const GOINGS = ['Heavy', 'Softer', 'Good', 'Quicker', 'Quick'];
// Course type: g galloping, s sharp, u undulating; * all-weather
const COURSE = { Ascot: 'g', Newmarket: 'g', York: 'g', Doncaster: 'g', Newbury: 'g', Sandown: 'g', Haydock: 'g', Epsom: 'u', Goodwood: 'u', Chester: 's', Kempton: 's*', Lingfield: 'u',
  Windsor: 's', Brighton: 'u', Bath: 'g', Pontefract: 'u', Ripon: 's', Thirsk: 's', Catterick: 's', Musselburgh: 's', Hamilton: 'u', Carlisle: 'u', Beverley: 'u', Redcar: 'g', Leicester: 'g',
  Nottingham: 'g', Yarmouth: 'g', Salisbury: 'g', Ayr: 'g', Newcastle: 'g*', Wolverhampton: 's*', Southwell: 's*', Chelmsford: 's*' };
const TYPE = { g: 'Galloping', s: 'Sharp', u: 'Undulating' };
Object.assign(COURSE, { 'Chelmsford City': 's*', Chepstow: 'u', 'Ffos Las': 'g', 'Lingfield (turf)': 'u', 'Lingfield (AW)': 's*', Wetherby: 'g' });
const TIERS = [null,
  { n: 'Small Owner', rep: 0, boxes: 4, pad: 1, gal: 2, acc: 0.72, fee: 30000 },
  { n: 'Rising Yard', rep: 40, boxes: 6, pad: 2, gal: 2, acc: 0.78, fee: 75000 },
  { n: 'Established Stable', rep: 180, boxes: 8, pad: 3, gal: 3, acc: 0.84, fee: 125000 },
  { n: 'Leading Owner', rep: 550, boxes: 10, pad: 4, gal: 3, acc: 0.9, fee: 200000 },
  { n: 'Champion Owner', rep: 1500, boxes: 12, pad: 5, gal: 4, acc: 0.95, fee: 200000 }];
// Race classes: label, short chip, reputation for a win, rank (for goals), handicap ceiling
const CLS = {
  S: { l: 'Seller', s: 'Sell', rep: 1, rk: 0 }, MA: { l: 'Auction Maiden', s: 'Mdn', rep: 2, rk: 0 }, M: { l: 'Maiden', s: 'Mdn', rep: 3, rk: 1 }, C6: { l: 'Handicap', s: 'C6', rep: 2, rk: 2, cap: 60 },
  C5: { l: 'Handicap', s: 'C5', rep: 3, rk: 3, cap: 70 }, N: { l: 'Novice', s: 'Nov', rep: 4, rk: 4 }, C4: { l: 'Handicap', s: 'C4', rep: 5, rk: 5, cap: 80 },
  C3: { l: 'Handicap', s: 'C3', rep: 8, rk: 6, cap: 90 }, C: { l: 'Conditions', s: 'Cond', rep: 12, rk: 7 }, C2: { l: 'Handicap', s: 'C2', rep: 14, rk: 8, cap: 105 },
  H: { l: 'Handicap', s: 'Hcap', rep: 20, rk: 9, cap: 105 }, L: { l: 'Listed', s: 'L', rep: 25, rk: 10 }, HH: { l: 'Heritage Handicap', s: 'HH', rep: 35, rk: 11, cap: 110 },
  G3: { l: 'Group 3', s: 'G3', rep: 40, rk: 12 }, G2: { l: 'Group 2', s: 'G2', rep: 60, rk: 13 }, G1: { l: 'Group 1', s: 'G1', rep: 120, rk: 14 } };
const CLASSICS = ['2000 Guineas', '1000 Guineas', 'The Derby', 'The Oaks', 'St Leger'];
const QUIRKS = { battler: 'Loves a battle', slowstart: 'Slow starter', fresh: 'Goes well fresh', bigday: 'Big-day horse', learner: 'Fast learner', needstime: 'Needs time between races', lazyhome: 'Lazy at home' };
const QDESC = { battler: 'Finds extra in a close finish.', slowstart: 'Sometimes misses the break. Schooling can cure it.', fresh: 'Runs best after a break of three fortnights or more.', bigday: 'Raises the game in Group races and heritage handicaps.',
  learner: 'Picks up racecraft and new tracks twice as fast.', needstime: 'Takes longer than most to get over a race.', lazyhome: 'Shows little on the gallops, so work reports undersell this one.', none: 'Straightforward. No quirks.' };
const LAB = { mat: { e: 'Early', n: 'Normal', l: 'Late' }, build: { gal: 'Galloper', agi: 'Agile', ver: 'Versatile' }, style: { F: 'Front-runner', P: 'Prominent', M: 'Midfield', H: 'Hold-up' },
  temp: { calm: 'Laid-back', even: 'Honest', hot: 'Highly strung' }, con: { tough: 'Tough', sound: 'Sound', del: 'Delicate' } };
const GAP = { e: { 2: [15, 8], 3: [6, 2], 4: [1, 0], 5: [2, 2], 6: [5, 5], 7: [9, 9] }, n: { 2: [25, 16], 3: [12, 4], 4: [2, 0], 5: [0, 1], 6: [3, 3], 7: [6, 6] }, l: { 2: [33, 25], 3: [19, 9], 4: [5, 1], 5: [0, 0], 6: [0, 1], 7: [3, 3] } };
const GREEN = [-6, -3, -1, 0];
const COST = { tough: 34, sound: 46, del: 60 }, SD = { calm: 3.5, even: 4.5, hot: 6.2 };
const BUYERS = ['Lord Marlowe', 'Ashcombe Stud', 'Glenveagh Racing', 'Mrs J. Tate', 'Kildare Lodge', 'The Castlebar Syndicate', 'Harcourt Bloodstock', 'Mr R. Fenwick'];

let S = null;                                    // the game being played
const use = g => { S = g; VC.clear(); return g; };
function init(E, seed) {
  const d = { rs: (seed || (Date.now() & 0x7fffffff)) | 0, cash: 0, rep: 0, season: 1, prog: 0, clock: 0, horses: [], mares: [], young: [], studs: [], stars: [], nid: 1, used: {}, troph: {}, hof: [], top: null };
  for (const k in d) if (E[k] === undefined) E[k] = d[k];
  use(E); if (!E.ss) E.ss = newSeasonStats(); if (!E.stars.length) genStars(); return E;
}
const newSeasonStats = () => ({ runs: 0, wins: 0, prize: 0, rep: 0, fees: 0, w2: 0, best: -1, pat: 0, patPl: 0, g1: 0, classic: 0, tier0: tier() });
function cash(x, why, h) { S.cash += x; if (ON.money) ON.money(x, why, h || null); }
function addRep(n, why, h) { if (!n) return; S.rep += n; if (ON.rep) ON.rep(n, why, h || null); }
// ---------------------------------------------------------------- luck (seeded, so a reload can't re-roll a race)
function rnd() { S.rs = (S.rs + 0x6D2B79F5) | 0; let t = S.rs; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }
function mk(seed) { let s = seed | 0; return () => { s = (s + 0x6D2B79F5) | 0; let t = s; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const gauss = (r = rnd) => { let u = 0, v = 0; while (!u) u = r(); v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.283185307 * v); };
const ri = (a, b) => a + Math.floor(rnd() * (b - a + 1)), pick = a => a[Math.floor(rnd() * a.length)], clamp = (x, a, b) => Math.max(a, Math.min(b, x));
function wpick(w) { let t = 0; for (const k in w) t += w[k]; let x = rnd() * t; for (const k in w) { x -= w[k]; if (x <= 0) return k; } return Object.keys(w)[0]; }
const nice = x => x < 10000 ? Math.round(x / 500) * 500 : x < 50000 ? Math.round(x / 1000) * 1000 : x < 200000 ? Math.round(x / 5000) * 5000 : Math.round(x / 10000) * 10000;

// ---------------------------------------------------------------- small rules
function fIdx(f) { for (let i = 0; i < 7; i++) if (f <= TRIPF[i + 1]) return i + (f - TRIPF[i]) / (TRIPF[i + 1] - TRIPF[i]); return 7 + (f - 16) / 4; }
function fLabel(f) { const m = Math.floor(f / 8), r = f - m * 8, fr = r % 1 ? (Math.floor(r) || '') + '½' : r; return (m ? m + 'm' : '') + (r ? fr + 'f' : ''); }
const tripOff = (t, f) => { const i = fIdx(f); return Math.max(0, t - i, i - (t + 1)); };
const tripMod = (t, f) => -Math.min(20, 5 * tripOff(t, f));
const tripLabel = t => TRIPS[t] + '–' + TRIPS[t + 1];
function groundMod(gr, g) { if (g == null) return 0; const d = g < gr[0] ? gr[0] - g : g > gr[1] ? g - gr[1] : 0; return d === 0 ? 5 : d === 1 ? 0 : d === 2 ? -5 : -10; }
const groundLabel = gr => gr[0] === gr[1] ? GOINGS[gr[0]] + ' only' : GOINGS[gr[0]] + ' to ' + GOINGS[gr[1]];
const TRACK = { gal: { g: 2, s: -6, u: -4 }, agi: { g: -2, s: 3, u: 2 }, ver: { g: 0, s: 0, u: 0 } };
function trackMod(b, ty, prof) { const m = TRACK[b][ty]; return m < 0 ? m * (1 - Math.min(2, prof || 0) / 3) : m; }
const ctype = co => COURSE[co][0], isAW = co => COURSE[co].length > 1;
const freshMod = f => f >= 75 ? 0 : -(75 - f) * 0.2;
const PACE = { slow: { F: 3, P: 1.5, M: -1, H: -3 }, even: { F: 0, P: 0, M: 0, H: 0 }, fast: { F: -3, P: -1, M: 1.5, H: 3 } };
const floorOf = r => r.cap - 20;
const tier = () => { let t = 1; for (let i = 2; i <= 5; i++) if (S.rep >= TIERS[i].rep) t = i; return t; };
const T = () => TIERS[tier()];
function ability(h, p) { if (p == null) p = S.prog; const g = GAP[h.mat][Math.min(7, Math.max(2, h.age))]; return h.pot - h.trim - (g[0] + (g[1] - g[0]) * p); }
const estAb = h => ability(h) + (h.k.pe - h.pot) * 0.8;       // what the trainer thinks the horse can run to today
const he = h => h.sex === 'f' ? 'she' : 'he', him = h => h.sex === 'f' ? 'her' : 'him', his = h => h.sex === 'f' ? 'her' : 'his', He = h => h.sex === 'f' ? 'She' : 'He';
function name() { for (let i = 0; i < 60; i++) { const n = pick(D.NA) + ' ' + pick(D.NB); if (!S.used[n]) { S.used[n] = 1; return n; } } return pick(D.NA) + ' ' + pick(D.NB) + ' ' + ri(2, 9); }
const rname = () => pick(D.NA) + ' ' + pick(D.NB);
function randGround() { const w = +wpick({ 1: 25, 2: 45, 3: 30 }); const lo = clamp(Math.round(1.6 + gauss() * 1.2), 0, 5 - w); return [lo, lo + w - 1]; }

// ---------------------------------------------------------------- making a horse
function foal(sire, dam, o = {}) {
  const mean = 47 + 7 * sire.stars + 6.5 * dam.stars;
  let res = gauss() * 9.5; if (rnd() < 0.05) res += 8 + rnd() * 12;
  if (o.res != null) res = o.res;
  const pot = clamp(Math.round(o.pot != null ? o.pot : mean + res), 38, 138);
  const trip = o.trip != null ? o.trip : clamp(Math.round((sire.opt + dam.opt) / 2 + gauss() * 0.9 - 0.5), 0, 6);
  const lean = (a, b) => { const x = rnd(); return x < 0.4 ? a : x < 0.7 ? b : null; };
  const pk = lean(sire.peak, dam.peak), matW = { e: { e: 55, n: 35, l: 10 }, n: { e: 25, n: 50, l: 25 }, l: { e: 10, n: 35, l: 55 } };
  const mat = o.mat || wpick(matW[pk || 'n']);
  const gsrc = lean(sire.gr, dam.gr); let gr = randGround();
  if (gsrc) { const w = Math.min(3, gsrc[1] - gsrc[0] + 1), lo = clamp(gsrc[0] + (rnd() < 0.25 ? ri(-1, 1) : 0), 0, 5 - w); gr = [lo, lo + w - 1]; }
  const build = o.build || (dam.build && rnd() < 0.45 ? dam.build : wpick(trip >= 4 ? { gal: 45, agi: 20, ver: 35 } : trip <= 1 ? { gal: 25, agi: 40, ver: 35 } : { gal: 35, agi: 30, ver: 35 }));
  const quirk = o.quirk !== undefined ? o.quirk : (dam.quirk && rnd() < 0.15 ? dam.quirk : rnd() < 0.36 ? pick(Object.keys(QUIRKS)) : null);
  const z = res / 9.5 + gauss() * 0.8, looks = z > 1.2 ? 3 : z > 0.3 ? 2 : z > -0.7 ? 1 : 0;
  const h = { id: S.nid++, n: o.n || name(), sex: o.sex || (rnd() < 0.5 ? 'c' : 'f'), age: o.age || 1, pot, trim: 0, mat, trip, gr, build, style: pick(['F', 'P', 'M', 'H']),
    temp: o.temp || (dam.temp && rnd() < 0.35 ? dam.temp : wpick({ calm: 30, even: 40, hot: 30 })), con: o.con || (dam.con && rnd() < 0.35 ? dam.con : wpick({ tough: 25, sound: 50, del: 25 })), quirk,
    sire: sire.n, dam: dam.n, ss: sire.stars, ds: dam.stars, cost: o.cost || 0, bred: !!o.bred, looks, res,
    runs: 0, wins: 0, pl: 0, earn: 0, or: null, peak: 0, perfs: [], fresh: 100, craft: 0, prof: { g: 0, s: 0, u: 0 }, inj: 0, last: -9, form: [], hist: [], big: [], g1: 0, grp: 0, entry: null, sr: 0, kv: 0,
    k: { pe: mean + looks * 2.5 - 3, pw: 17, mat: 0, trip: 1, gr: [null, null, null, null, null], gh: sire.gr.slice(), build: 0, style: 0, temp: 0, con: 0, quirk: 0 },
    gs: { mat: null, trip: clamp(Math.round((sire.opt + dam.opt) / 2 - 0.5), 0, 6), build: null, temp: null, con: null } };
  return h;
}
const orStars = or => clamp(Math.round((or - 60) / 11), 1, 5);
const potStar = r => clamp((r - 55) / 14, 0, 5.5);          // rating to stars: 69 = 1, 83 = 2, 97 = 3, 111 = 4, 125 = 5
const potWord = s => s < 1.2 ? 'Modest' : s < 2.1 ? 'Handicapper' : s < 2.9 ? 'Useful' : s < 3.6 ? 'Listed class' : s < 4.3 ? 'Group class' : s < 5 ? 'Top class' : 'Champion';
function evid(h, rate, bias) { const k = h.k; k.pe += (h.pot + (bias || 0) - k.pe) * rate + gauss() * k.pw * 0.07; k.pw = Math.max(3, k.pw * (1 - rate * 0.6)); h.kv++; }
// a guess that is right about as often as your trainer's eye is good
function guess(h, key, opts) { const right = rnd() < T().acc; if (key === 'trip') return right ? h.trip : clamp(h.trip + (rnd() < 0.5 ? -1 : 1), 0, 6); if (right) return h[key]; const o = opts.filter(x => x !== h[key]); return pick(o); }
// the ground guess: the set of goings that fits everything seen so far and is nearest the last guess
function regroundGuess(h) {
  const k = h.k, cands = [];
  for (let w = 1; w <= 3; w++) for (let lo = 0; lo + w - 1 < 5; lo++) { const set = [lo, lo + w - 1]; let ok = true;
    for (let g = 0; g < 5 && ok; g++) if (k.gr[g] != null) { const m = groundMod(set, g); ok = k.gr[g] === 2 ? m === 5 : k.gr[g] === 1 ? m === 0 : m < 0; }
    if (ok) cands.push(set); }
  if (!cands.length) return; const p = k.gh || [2, 3];
  cands.sort((a, b) => Math.abs(a[0] - p[0]) + Math.abs(a[1] - p[1]) - Math.abs(b[0] - p[0]) - Math.abs(b[1] - p[1]));
  k.gh = cands[0]; k.gsure = cands.length === 1;
}

// ---------------------------------------------------------------- three to start: an honest handicapper who pays his way, a sharp two-year-old colt, a slower-burning filly
function starters() {
  const sire = n => D.stallions.find(s => s.n === n), dam = st => pick(D.mares.filter(m => m.stars === st));
  const a = foal(sire('Kodiac'), dam(1), { age: 3, sex: 'c', pot: 73 + ri(0, 3), mat: 'n', trip: 2, con: 'tough', temp: 'even', quirk: null, build: 'ver', cost: 14000 });
  Object.assign(a, { runs: 5, wins: 1, pl: 2, craft: 3, form: [4, 2, 1, 5, 3], gr: [2, 4] }); a.or = Math.round(ability(a)) - 2; a.peak = a.or; a.perfs = [a.or]; a.earn = 6200;
  Object.assign(a.k, { pe: a.pot + 1, pw: 4, mat: 2, trip: 2, build: 2, style: 2, temp: 2, con: 2, quirk: 2, gr: [null, null, 2, 2, null], gh: [2, 4] }); a.gs = { mat: 'n', trip: 2, build: 'ver', temp: 'even', con: 'tough' };
  const damT = (st, lo, hi) => pick(D.mares.filter(m => m.stars === st && m.opt >= lo && m.opt <= hi));
  const b = foal(sire('Havana Grey'), damT(2, 0, 2), { age: 2, sex: 'c', pot: 83 + ri(0, 5), mat: 'e', trip: ri(0, 1), cost: 22000 });
  const c = foal(sire('Study Of Man'), damT(2, 3, 6), { age: 2, sex: 'f', pot: 74 + ri(0, 8), mat: rnd() < 0.5 ? 'n' : 'l', trip: ri(3, 4), cost: 18000 });
  b.gs.trip = clamp(b.trip + ri(0, 1), 0, 6); c.gs.trip = clamp(c.trip + ri(-1, 0), 0, 6);
  return [a, b, c];
}

// ---------------------------------------------------------------- the rivals' best horses, who turn up again and again in the big races
function genStars() {
  const old = S.stars || [], out = [];
  for (const s of old) {
    if (s.ag === 2) out.push(Object.assign({}, s, { ag: 3, base: s.base + 9 + gauss() * 3, t: clamp(s.t + (rnd() < 0.6 ? 1 : 0) + (rnd() < 0.3 ? 1 : 0), 0, 6), fm: [] }));
    else if (s.ag === 3 && rnd() < 0.45) out.push(Object.assign({}, s, { ag: 4, base: s.base + 5 + gauss() * 2, fm: [] }));
    else if (s.ag === 4 && rnd() < 0.35) out.push(Object.assign({}, s, { base: s.base - 1 + gauss(), fm: [] }));
  }
  const band = t => t <= 1 ? 0 : t <= 3 ? 1 : t <= 5 ? 2 : 3, count = (ag, sex, b) => out.filter(s => s.ag === ag && (sex == null || s.sex === sex) && band(s.t) === b).length;
  const mkS = (ag, sex, b) => { const t = [ri(0, 1), ri(2, 3), ri(4, 5), 6][b]; let base = (ag === 2 ? 101 : ag === 3 ? 113 : 120) + gauss() * 3.8; if (rnd() < 0.05) base += 6;
    out.push({ n: rname(), s: Math.floor(rnd() * D.silks.length), sex: sex || (rnd() < 0.35 ? 'f' : 'c'), ag, t, base, g: randGround(), st: pick(['F', 'P', 'M', 'H']), fm: [] }); };
  const want = [[2, 'c', 0, 4], [2, 'c', 1, 4], [2, 'f', 0, 3], [2, 'f', 1, 3], [3, 'c', 0, 3], [3, 'c', 1, 4], [3, 'c', 2, 4], [3, 'c', 3, 2], [3, 'f', 0, 2], [3, 'f', 1, 3], [3, 'f', 2, 3], [4, null, 0, 4], [4, null, 1, 4], [4, null, 2, 5], [4, null, 3, 4]];
  for (const [ag, sex, b, n] of want) for (let i = count(ag, sex, b); i < n; i++) mkS(ag, sex, b);
  // prefer the big stables' colours for the best of them
  for (const s of out) if (s.base > (s.ag === 2 ? 103 : s.ag === 3 ? 115 : 122)) { const big = D.silks.map((x, i) => [x, i]).filter(x => x[0].t === 1); s.s = pick(big)[1]; }
  S.stars = out;
}
const starAb = s => s.base + (s.ag === 2 ? 0.65 : s.ag === 3 ? 0.5 : 0) * S.prog * 15;

// ---------------------------------------------------------------- the opposition: how good a race is, and who is in it
function std(r) {
  const f = S.prog * 15, two = r.a[1] === 2, three = r.a[0] === 3 && r.a[1] === 3, fl = r.sx === 'F' ? -3 : 0;
  switch (r.cls) {
    case 'S': return { mu: two ? 44 + 0.8 * f : 52, sd: 7 };
    case 'MA': return { mu: 50 + 0.8 * f, sd: 7 };
    case 'M': return two ? { mu: 60 + f + fl, sd: 8, tout: 0.15 } : { mu: 68 + 0.3 * f + fl, sd: 8, tout: 0.1 };
    case 'N': return two ? { mu: 74 + 0.8 * f, sd: 6 } : { mu: 74 + 0.2 * f + fl, sd: 7 };
    case 'C': return two ? { mu: 74 + 0.8 * f, sd: 6 } : { mu: (three ? 91 : 96) + fl, sd: 5 };
    case 'L': return two ? { mu: 90 + 0.5 * f + fl, sd: 5 } : { mu: (three ? 98 + 0.2 * f : 101) + fl, sd: 4 };
    case 'G3': return two ? { mu: 96 + 0.5 * f + fl, sd: 4.5 } : { mu: (three ? 103 + 0.2 * f : 106) + fl, sd: 4 };
    case 'G2': return two ? { mu: 100 + 0.5 * f + fl, sd: 4.5 } : { mu: (three ? 107 + 0.2 * f : 110) + fl, sd: 4 };
    default: return two ? { mu: 106 + 0.4 * f + fl, sd: 4.5 } : { mu: (three ? 112 + 0.25 * f : 115) + fl, sd: 4 };
  }
}
const NRUN = { S: [7, 11], MA: [8, 12], M: [8, 13], N: [7, 10], C6: [9, 14], C5: [9, 14], C4: [9, 14], C3: [9, 14], C2: [10, 15], H: [10, 16], HH: [14, 18], C: [6, 9], L: [7, 11], G3: [7, 10], G2: [6, 9], G1: [7, 12] };
function genField(r) {
  const [a, b] = r.nrun || NRUN[r.cls], n = ri(a, b), out = [], hc = r.cap != null, top = r.cls === 'G1' || r.cls === 'G2' || r.cls === 'G3';
  const silk = () => { if (top || r.cls === 'L') { const t = +wpick(r.cls === 'G1' ? { 1: 50, 2: 30, 3: 15, 4: 5 } : { 1: 30, 2: 30, 3: 25, 4: 15 }); const c = D.silks.map((x, i) => [x, i]).filter(x => x[0].t === t); return pick(c)[1]; } return Math.floor(rnd() * D.silks.length); };
  const form = ab => { let s = []; for (let i = 0; i < 3; i++) s.push(rnd() < 0.2 ? 1 : ri(1, 9) % 10); return s.join(''); };
  if (top) { // the season's stars
    const ag = r.a[1] === 2 ? 2 : r.a[0] === 3 && r.a[1] === 3 ? 3 : 0, p = r.cls === 'G1' ? 0.65 : r.cls === 'G2' ? 0.3 : 0.1, max = r.cls === 'G1' ? 5 : 3;
    for (const s of S.stars) { if (out.length >= max) break; if (ag ? s.ag !== ag : (s.ag === 2 || s.ag < r.a[0])) continue; if (r.sx === 'F' && s.sex !== 'f' || r.sx === 'C' && s.sex !== 'c') continue; if (tripOff(s.t, r.f) > 0.5) continue;
      if (rnd() < p) out.push({ n: s.n, s: s.s, ab: Math.round(starAb(s) * 10) / 10, g: s.g, st: s.st, fm: s.fm.slice(-3).join('') || form(), star: 1 }); }
  }
  const sd = hc ? null : std(r);
  while (out.length < n) {
    let ab, or = null;
    if (hc) { const lo = r.cap - 14; or = Math.round(lo + Math.pow(rnd(), 0.8) * 14); ab = or + 0.5 + gauss() * 3.5; }
    else { ab = sd.mu + gauss() * sd.sd; if (sd.tout && rnd() < sd.tout) ab += 10; }
    out.push({ n: rname(), s: silk(), ab: Math.round(ab * 10) / 10, or, g: randGround(), st: pick(['F', 'P', 'M', 'H']), fm: r.cls === 'M' || r.cls === 'MA' ? (rnd() < 0.4 ? '' : '' + ri(2, 9) + (rnd() < 0.5 ? ri(2, 9) : '')) : form() });
  }
  return out;
}
// a host hands over { id, n, co, cls, f, a: [min age, max age], sx: '' | 'F' | 'C', p: prize to the winner in £k, big?, cap?, g, ty, nog? }
// g = the going, 0 Heavy to 4 Quick, null on the all-weather, undefined if not yet known; nrun = [fewest, most] rivals, if the calendar says; ty = 'g' galloping, 's' sharp, 'u' undulating
function prepRace(r) { if (r.cap == null && CLS[r.cls].cap) r.cap = CLS[r.cls].cap; if (r.ty == null) r.ty = COURSE[r.co] ? ctype(r.co) : 'g'; r.field = genField(r); return r; }
function eligible(h, r) {
  if (h.inj > 0 || h.age < r.a[0] || h.age > r.a[1]) return false;
  if (r.sx === 'F' && h.sex !== 'f' || r.sx === 'C' && h.sex === 'f' || r.nog && h.sex === 'g') return false;
  if ((r.cls === 'M' || r.cls === 'MA') && h.wins > 0) return false;
  if (r.cls === 'MA' && h.cost > 30000) return false;
  if (r.cls === 'N' && h.wins > 2) return false;
  if (r.cap != null && (h.or == null || h.or > r.cap)) return false;
  return true;
}
// ---------------------------------------------------------------- the trainer's view of a race (uses only what is known about the horse)
const VC = new Map();
function view(h, r) {
  const key = h.id + '|' + r.id + '|' + h.kv + '|' + h.fresh + '|' + S.clock + '|' + r.g; let v = VC.get(key); if (v) return v;
  const g = r.g, ty = r.ty, hc = r.cap != null, k = h.k, fit = {}; let m = 0;
  if (k.trip >= 1) { const t = tripMod(h.gs.trip, r.f); m += t; fit.trip = t > -1 ? 'y' : t > -5 ? 'm' : 'n'; if (k.trip < 2) fit.tripq = 1; } else fit.trip = 'q';
  if (g === undefined) fit.gr = 'q';
  else if (g === null) fit.gr = 'y';
  else if (k.gr[g] != null) { const t = groundMod(h.gr, g); m += t; fit.gr = t > 0 ? 'y' : t === 0 ? 'm' : 'n'; }
  else if (k.gh) { const t = groundMod(k.gh, g); m += t; fit.gr = t > 0 ? 'y' : t === 0 ? 'm' : 'n'; if (!k.gsure) fit.grq = 1; } else fit.gr = 'q';
  if (k.build >= 1) { const t = trackMod(h.gs.build, ty, h.prof[ty]); m += t; fit.tr = t >= 0 ? 'y' : t > -3 ? 'm' : 'n'; if (k.build < 2) fit.trq = 1; } else fit.tr = 'q';
  m += GREEN[Math.min(3, h.craft)] + freshMod(h.fresh);
  const est = estAb(h) + m, mine = est - (hc ? Math.max(h.or, floorOf(r)) : 0), rv = r.field.map(x => x.ab + (g == null ? 0 : groundMod(x.g, g)) - (hc ? x.or : 0));
  const R = mk(h.id * 7919 + r.id * 31 + h.kv), N = 140; let win = 0, pl = 0;
  for (let i = 0; i < N; i++) { const me = mine + gauss(R) * 4.8; let ahead = 0; for (let j = 0; j < rv.length && ahead < 3; j++) if (rv[j] + gauss(R) * 4.5 > me) ahead++; if (!ahead) win++; if (ahead < 3) pl++; }
  win /= N; pl /= N;
  const unsure = k.pw > 9;
  const lv = win >= 0.4 ? 4 : win >= 0.22 ? 3 : win >= 0.085 ? 2 : pl >= 0.17 ? 1 : 0, label = ['Outclassed', 'Place chance', 'In the mix', 'Big chance', 'Hard to beat'][lv];
  v = { win, pl, fit, label, lv, unsure, ev: (win + pl * 0.2) * r.p, low: hc && h.or < floorOf(r) }; VC.set(key, v); return v;
}
function options(h, races) { return races.filter(r => eligible(h, r)).map(r => ({ r, v: view(h, r) })).sort((a, b) => b.v.win + b.v.pl * 0.05 - a.v.win - a.v.pl * 0.05); }
function picks(h, races) { const o = options(h, races); if (!o.length) return {}; const best = o[0]; let rich = null; for (const x of o) if (x.v.win >= 0.06 && (!rich || x.v.ev > rich.v.ev)) rich = x; if (rich && rich.r.id === best.r.id) rich = null; return { best, rich, n: o.length }; }
// the trainer's own choice for a horse from the races on offer, or null to stay at home
function autoPick(h, races) { if (h.inj > 0 || h.fresh < 75) return null; const p = picks(h, races); return p.best && (p.best.v.lv >= 2 || p.best.v.pl >= 0.24 || h.or == null) ? p.best.r : null; }
const horse = id => S.horses.find(h => h.id === id);

// ---------------------------------------------------------------- the gallops: work, school or an easy week
// type: 'work' (learn about the horse), 'school' (teach it) or 'easy' (freshen it). Returns { text, rev } or null if there was nothing to do. The host counts the gallops.
function gallop(h, type) {
  if (h.inj > 0) return null; const k = h.k; let text = '', rev = [];
  if (type === 'easy') { if (h.fresh >= 100) return null; h.fresh = Math.min(100, h.fresh + 30); text = `An easy fortnight for ${h.n}. ${He(h)} has freshened up nicely.`; }
  else if (type === 'school') {
    if (h.quirk === 'slowstart' && k.quirk === 2) { h.quirk = null; h.cured = 1; text = `Hours in the stalls with ${h.n}. ${He(h)} is jumping out smartly now.`; rev.push(['Quirk', 'Slow starts cured']); }
    else if (h.craft < 3) { h.craft++; text = h.craft >= 3 ? `${h.n} knows ${his(h)} job now. A proper professional.` : `${h.n} is learning. ${He(h)} worked upsides and didn't flinch.`; rev.push(['Racecraft', h.craft >= 3 ? 'Professional' : 'Improving']); }
    else { const ty = h.prof.s <= h.prof.u ? 's' : 'u'; if (h.prof[ty] >= 2) return null; h.prof[ty]++; text = ty === 's' ? `We schooled ${h.n} round tight turns. ${He(h)} is handling them better.` : `We worked ${h.n} up and down the hill. ${He(h)} is better balanced for it.`; rev.push(['Track', ty === 's' ? 'Better on sharp tracks' : 'Better on undulating tracks']); }
    h.fresh = Math.max(0, h.fresh - 3);
  } else {
    evid(h, 0.3, h.quirk === 'lazyhome' ? -9 : 0); h.fresh = Math.max(0, h.fresh - 6); h.worked = 1;
    const s = potStar(k.pe), up = [['mat', ['e', 'n', 'l']], ['build', ['gal', 'agi', 'ver']], ['temp', ['calm', 'even', 'hot']], ['con', ['tough', 'sound', 'del']]];
    let done = false;
    for (const [key, opts] of up) if (k[key] === 0) { h.gs[key] = guess(h, key, opts); k[key] = 1; rev.push([{ mat: 'Maturity', build: 'Build', temp: 'Temperament', con: 'Constitution' }[key], LAB[key][h.gs[key]] + '?']); done = true; break; }
    if (!done && k.trip < 2) { const g = guess(h, 'trip'); if (g === h.gs.trip) k.trip = 2, h.gs.trip = h.trip; else h.gs.trip = g; rev.push(['Trip', tripLabel(h.gs.trip) + (k.trip < 2 ? '?' : '')]); done = true; }
    if (!done) for (const [key] of up) if (k[key] === 1) { h.gs[key] = h[key]; k[key] = 2; rev.push([{ mat: 'Maturity', build: 'Build', temp: 'Temperament', con: 'Constitution' }[key], LAB[key][h[key]]]); break; }
    text = s >= 4.3 ? `${h.n} worked like a very good horse this morning. I don't say that often.` : s >= 3.4 ? `${h.n} went past ${his(h)} lead horse without being asked. There's a real engine in there.` : s >= 2.4 ? `A good, honest piece of work from ${h.n}. ${He(h)} will win races.` : s >= 1.4 ? `${h.n} worked fine. Nothing flashy, but ${he(h)} tries.` : `${h.n} was flat out to stay with ${his(h)} lead horse. Small races for ${him(h)}.`;
  }
  h.kv++; return { text, rev };
}

// ---------------------------------------------------------------- race day
const lbPerL = f => f <= 6 ? 3 : f <= 8 ? 2.5 : f <= 12 ? 2 : 1.6;
const LADDER = [[1, 5, '1/5'], [1, 3, '1/3'], [1, 2, '1/2'], [4, 6, '4/6'], [1, 1, 'Evens'], [6, 4, '6/4'], [2, 1, '2/1'], [5, 2, '5/2'], [3, 1, '3/1'], [4, 1, '4/1'], [5, 1, '5/1'], [6, 1, '6/1'], [8, 1, '8/1'], [10, 1, '10/1'], [12, 1, '12/1'], [16, 1, '16/1'], [20, 1, '20/1'], [25, 1, '25/1'], [33, 1, '33/1'], [50, 1, '50/1'], [100, 1, '100/1']];
function oddsOf(p) { const d = (1 - p) / Math.max(0.004, p) * 0.87; let b = LADDER[0]; for (const o of LADDER) if (Math.abs(Math.log(o[0] / o[1]) - Math.log(Math.max(0.15, d))) < Math.abs(Math.log(b[0] / b[1]) - Math.log(Math.max(0.15, d)))) b = o; return { t: b[2], d: b[0] / b[1] }; }
// mine = your horses in the race. Returns the whole result: the field in finishing order, and for each of yours the prize, the new rating, the debrief and what was learned
function runRace(r, mine) {
  const g = r.g, ty = r.ty, hc = r.cap != null;
  const run = r.field.map(x => ({ n: x.n, s: x.s, st: x.st, or: x.or, fm: x.fm, star: x.star, mean: x.ab + (g == null ? 0 : groundMod(x.g, g)) }));
  const ctx = {};
  for (const h of mine) run.push({ you: 1, hid: h.id, n: h.n, st: h.style, or: hc ? Math.max(h.or, floorOf(r)) : h.or, low: hc && h.or < floorOf(r), fm: h.form.slice(-3).join('') });
  const n = run.length, fr = run.filter(x => x.st === 'F').length / n, pace = fr >= 0.36 ? 'fast' : fr <= 0.13 ? 'slow' : 'even';
  for (const x of run) {
    if (!x.you) { x.mean += PACE[pace][x.st] * 0.6; x.fig = x.mean + gauss() * 4.5; continue; }
    const h = horse(x.hid), m = { trip: tripMod(h.trip, r.f), gr: groundMod(h.gr, g), tr: trackMod(h.build, ty, h.prof[ty]), green: GREEN[Math.min(3, h.craft)], fresh: freshMod(h.fresh), pace: PACE[pace][h.style], temp: 0, q: 0 };
    if (h.temp === 'hot') m.temp = (pace === 'slow' ? -2 : 0) + (n >= 16 ? -2 : 0);
    const c = ctx[h.id] = { m, pre: h.fresh, flags: {} };
    if (h.quirk === 'slowstart' && rnd() < 0.3) { m.q -= 5; c.flags.slow = 1; }
    if (h.quirk === 'fresh' && S.clock - h.last >= 3 * CFG.tpf) { m.q += 3; c.flags.freshq = 1; }
    if (h.quirk === 'bigday' && (r.cls === 'G1' || r.cls === 'G2' || r.cls === 'HH')) { m.q += 3; c.flags.big = 1; }
    x.mean = ability(h) + m.trip + m.gr + m.tr + m.green + m.fresh + m.pace + m.temp + m.q; x.fig = x.mean + gauss() * SD[h.temp];
  }
  for (const x of run) x.sc = x.fig - (hc ? x.or : 0);
  { let tot = 0; for (const x of run) { x.pm = Math.exp(((x.you ? x.mean + gauss() * 3 : x.mean) - (hc ? x.or : 0)) / 4.4); tot += x.pm; } for (const x of run) x.od = oddsOf(x.pm / tot); }
  run.sort((a, b) => b.sc - a.sc);
  for (const x of run) if (x.you && run[0] !== x && horse(x.hid).quirk === 'battler' && run[0].sc - x.sc < 2.5) { x.sc += 2.5; x.fig += 2.5; ctx[x.hid].flags.battle = 1; }
  run.sort((a, b) => b.sc - a.sc);
  run.forEach((x, i) => { x.pos = i + 1; x.btn = Math.min(40, (run[0].sc - x.sc) / lbPerL(r.f)); });
  for (const s of S.stars) { const x = run.find(y => y.star && y.n === s.n); if (x) s.fm.push(x.pos > 9 ? 0 : x.pos); }
  const res = { rid: r.id, big: r.big, n: r.n, co: r.co, cls: r.cls, f: r.f, p: r.p, g, ty, pace, a: r.a, sx: r.sx, cap: r.cap, run: run.map(x => ({ n: x.n, s: x.s, st: x.st, or: x.or, fm: x.fm, you: x.you, hid: x.hid, pos: x.pos, btn: Math.round(x.btn * 100) / 100, od: x.od.t, star: x.star })), mine: [] };
  for (const x of run) if (x.you) res.mine.push(settle(horse(x.hid), r, x, run, ctx[x.hid], res));
  return res;
}
function settle(h, r, x, run, c, res) {
  const g = res.g, ty = res.ty, hc = r.cap != null, pos = x.pos, n = run.length, m = c.m, k = h.k, rev = [], out = { hid: h.id, pos, n, orOld: h.or };
  const share = [1, 0.38, 0.19, 0.09][pos - 1] || 0, prize = Math.round(r.p * 1000 * share), cl = CLS[r.cls];
  const classic = CLASSICS.includes(r.n), rep = Math.round((classic && pos === 1 ? 180 : cl.rep) * ([1, 0.3, 0.15][pos - 1] || 0));
  h.runs++; h.sr++; h.earn += prize; cash(prize, 'prize', h); addRep(rep, 'race', h); if (pos === 1) h.wins++; else if (pos <= 3) h.pl++;
  h.form.push(pos > 9 ? 0 : pos); const ss = S.ss; ss.runs++; ss.prize += prize; ss.rep += rep;
  if (pos === 1) { ss.wins++; if (h.age === 2) ss.w2++; ss.best = Math.max(ss.best, cl.rk); if (cl.rk >= 10 && r.cls !== 'HH') ss.pat++; if (r.cls === 'G1') { ss.g1++; h.g1++; } if (classic) ss.classic++; if (cl.rk >= 12) h.grp++;
    if (r.big && cl.rk >= 9) h.big.push(r.n); if (r.cls === 'G1' || r.cls === 'HH') (S.troph[r.n] = S.troph[r.n] || []).push({ s: S.season, h: h.n }); }
  if (pos <= 3 && cl.rk >= 10) ss.patPl++;
  // the handicapper
  const perf = x.fig; h.perfs.push(Math.round(perf));
  if (h.or == null) { if (pos === 1 || h.runs >= 2) { const av = h.perfs.reduce((a, b) => a + b, 0) / h.perfs.length; h.or = Math.round(av - 1); if (pos === 1) h.or = Math.max(h.or, Math.round(perf - 3)); } }
  else { const d = perf - h.or; let ch = d > 0 ? Math.min(7, Math.round(d * 0.35)) : -Math.min(4, Math.round(-d * 0.33)); if (pos === 1) ch = Math.max(ch, hc ? 3 : 0); h.or += ch; }
  if (h.or != null) { h.or = clamp(h.or, 30, 140); h.peak = Math.max(h.peak, h.or); }
  out.orNew = h.or; out.prize = prize; out.rep = rep;
  // what the run taught us
  if (k.style < 2) { k.style = 2; rev.push(['Style', LAB.style[h.style]]); }
  const off = tripOff(h.trip, r.f), short = fIdx(r.f) < h.trip;
  if (off === 0) { if (k.trip < 2 || h.gs.trip !== h.trip) { rev.push(['Trip', tripLabel(h.trip) + ' confirmed']); } k.trip = 2; h.gs.trip = h.trip; }
  else if (k.trip < 2 || h.gs.trip !== h.trip) { h.gs.trip = h.trip; k.trip = off >= 1.5 ? 2 : Math.max(k.trip, 1); rev.push(['Trip', (short ? 'Wants further: ' : 'Wants shorter: ') + tripLabel(h.trip) + (k.trip < 2 ? '?' : '')]); }
  if (g != null && k.gr[g] == null) { k.gr[g] = m.gr > 0 ? 2 : m.gr === 0 ? 1 : 0; regroundGuess(h); rev.push(['Ground', m.gr > 0 ? 'Acts on ' + GOINGS[g] : m.gr === 0 ? 'Copes with ' + GOINGS[g] : 'Hates ' + GOINGS[g]]); }
  if (k.build < 2 && ty !== 'g') { k.build = 2; h.gs.build = h.build; rev.push(['Build', LAB.build[h.build]]); }
  else if (k.build === 0 && h.runs >= 2) { k.build = 1; h.gs.build = guess(h, 'build', ['gal', 'agi', 'ver']); rev.push(['Build', LAB.build[h.gs.build] + '?']); }
  if (k.con < 2 && h.runs >= 2) { k.con = 2; h.gs.con = h.con; rev.push(['Constitution', LAB.con[h.con]]); }
  if (k.temp < 2 && h.runs >= 3) { k.temp = 2; h.gs.temp = h.temp; rev.push(['Temperament', LAB.temp[h.temp]]); }
  if (k.mat < 2 && h.runs >= 4) { k.mat = 2; h.gs.mat = h.mat; rev.push(['Maturity', LAB.mat[h.mat] + ' developer']); }
  if (k.quirk < 2) { const q = h.quirk, f = c.flags; const show = q && (f.slow || f.freshq || f.big || f.battle || (q === 'needstime' && h.runs >= 1) || (q === 'learner' && h.runs >= 2) || (q === 'lazyhome' && (h.worked || h.runs >= 2)));
    if (show) { k.quirk = 2; rev.push(['Quirk', QUIRKS[q]]); } else if (!q && h.runs >= 4) { k.quirk = 2; rev.push(['Quirk', 'None']); } }
  evid(h, 0.42);
  // wear and tear
  const learn = h.quirk === 'learner' ? 2 : 1; h.craft = Math.min(3, h.craft + learn); const hadProf = h.prof[ty]; h.prof[ty] = Math.min(2, h.prof[ty] + learn);
  h.fresh = Math.max(0, h.fresh - COST[h.con] - (h.quirk === 'needstime' ? 12 : 0) - (g === 0 ? 6 : 0) - (r.f >= 14 ? 4 : 0)); h.last = S.clock;
  const tired = c.pre < 50; if (rnd() < (tired ? 0.2 : h.con === 'del' ? 0.03 : 0.012)) { h.inj = ri(2, 4) * CFG.tpf; if (tired) h.trim += ri(1, 3); out.inj = h.inj; }
  // the trainer's debrief
  const won = pos === 1, mg = won ? (run[1] ? run[1].btn : 9) : x.btn, why = [['trip', m.trip], ['gr', m.gr], ['tr', m.tr], ['green', m.green], ['fresh', m.fresh], ['pace', m.pace], ['q', c.flags.slow ? -5 : 0], ['temp', m.temp]].sort((a, b) => a[1] - b[1])[0];
  let t;
  if (out.inj) t = `${He(h)} came back sore${tired ? ' — I ran ' + him(h) + ' when ' + he(h) + ' needed a rest' : ''}. ${He(h)} will be off for about ${Math.round(h.inj * 2 / CFG.tpf)} weeks.`;
  else if (won) t = c.flags.battle ? `${He(h)} refused to be beaten. Loves a scrap, this one.` : mg >= 3 ? (cl.rk >= 10 ? `That was special. ${He(h)} made good horses look ordinary.` : `Never saw another horse. ${He(h)} is better than this grade.`) : mg < 0.5 ? `Got there on the line. I aged ten years, but ${he(h)} did it.` : `Did it nicely. ${He(h)} keeps finding when you ask.`;
  else if (why[1] <= -3) t = { trip: short ? `Outpaced. ${He(h)} is crying out for further.` : `Didn't get home. We need to drop ${him(h)} back in trip.`, gr: `${He(h)} hated the ground. Put a line through that.`, tr: `${He(h)} never got organised round ${r.co}. The track didn't suit.`,
    green: `Still green. ${He(h)} ran about and only got going late. ${He(h)}'ll know more next time.`, fresh: `${He(h)} ran flat. ${He(h)} needs a break.`, pace: res.pace === 'slow' ? `They crawled, and it turned into a sprint. No use to ${him(h)}.` : `They went too hard up front and ${he(h)} paid for it late.`,
    q: `Missed the break and was always on the back foot.`, temp: `${He(h)} boiled over beforehand and ran ${his(h)} race in the paddock.` }[why[0]];
  else if (pos <= 3) t = mg < 1 ? `Beaten a whisker. ${He(h)}'s day is coming.` : `A solid run. ${He(h)} is knocking on the door.`;
  else t = x.btn > 8 ? `No excuses. ${He(h)} wasn't good enough at this level, so we lower our sights.` : `Ran ${his(h)} race. ${He(h)} is about that good in this company.`;
  if (won && m.gr > 0 && g != null && (g <= 1 || g === 4)) t += ` ${He(h)} loved that ground.`;
  if (!out.inj && !won && m.tr < 0 && why[0] !== 'tr' && hadProf < 2 && ty !== 'g') t += ` ${He(h)} will handle the track better next time.`;
  out.say = t; out.rev = rev; out.won = won;
  h.hist.push({ s: S.season, c: S.clock, n: r.n, co: r.co, cls: r.cls, d: r.f, g, pos, of: n, btn: Math.round(mg * 10) / 10, pr: prize });
  if (h.hist.length > 40) h.hist.shift();
  if (h.or != null && (!S.top || h.peak > S.top.or)) S.top = { n: h.n, or: h.peak, s: S.season };
  return out;
}
// a turn goes by: freshness comes back (30 a fortnight) and injuries heal
function rest() { for (const h of S.horses) { h.fresh = Math.min(100, h.fresh + 30 / CFG.tpf); if (h.inj > 0) h.inj--; } }

// ---------------------------------------------------------------- selling, retiring, the stud, the sales
function valueOf(h) {
  const af = { 1: 1, 2: 1.3, 3: 1, 4: 0.7, 5: 0.45, 6: 0.3, 7: 0.2 }[Math.min(7, h.age)];
  let v = h.or != null ? 2000 * Math.exp((Math.max(h.or, h.peak - 6) - 50) / 11) * af : Math.max(h.cost * (h.runs ? 0.55 : 0.8), 3500);
  if (h.sex === 'f' && h.or >= 88) v *= 1.3; if (h.inj > 0) v *= 0.7;
  return Math.max(1500, nice(v));
}
const studStars = h => h.peak >= 126 ? 5 : h.peak >= 120 ? 4 : h.peak >= 113 ? 3 : h.peak >= 106 ? 2 : 1;
const mareStars = h => Math.max(1, orStars(h.peak || 60), Math.round((h.ss + h.ds) / 2) - 1);
const canStud = h => h.sex === 'f' ? true : h.sex === 'c' && h.grp > 0;
const studFee = h => nice(valueOf(Object.assign({}, h, { age: 3 })) * 0.5);
function fame(h, how) { if (h.wins >= 4 || h.peak >= 95 || h.big.length) S.hof.push({ n: h.n, peak: h.peak, wins: h.wins, runs: h.runs, earn: h.earn, big: h.big.slice(0, 8), how, s: S.season }); }
function sell(hid) { const h = horse(hid), v = valueOf(h); cash(v, 'sale', h); fame(h, 'Sold'); S.horses = S.horses.filter(x => x !== h); return v; }
function retire(hid) {
  const h = horse(hid);
  if (h.sex === 'f') { if (S.mares.length >= T().pad) return null; S.mares.push({ id: h.id, n: h.n, stars: mareStars(h), opt: h.trip, peak: h.mat, gr: h.gr, build: h.build, temp: h.temp, con: h.con, quirk: h.quirk, age: h.age, cover: null, peakOR: h.peak, foals: 0 }); fame(h, 'Broodmare'); }
  else { if (!canStud(h)) return null; const fee = studFee(h); cash(fee, 'stud', h); S.studs.push({ n: h.n, stars: studStars(h), opt: h.trip, peak: h.mat, gr: h.gr, fee: 0, own: 1, until: S.season + 8 }); fame(h, 'Stallion'); }
  S.horses = S.horses.filter(x => x !== h); return true;
}
const yearlingValue = y => nice(guideOf(sireOf(y.sire) || { fee: 10000 }, y.ds, y.looks) * 0.8);
const sireOf = n => D.stallions.find(s => s.n === n) || S.studs.find(s => s.n === n);
function sires() { const cap = T().fee; return S.studs.filter(s => s.until >= S.season).concat(D.stallions.filter(s => s.fee <= cap)); }
function setCover(mid, sn) { const m = S.mares.find(x => x.id === mid), s = sn ? sireOf(sn) : null; if (m.cover) { const o = sireOf(m.cover); cash(o ? o.fee : 0, 'cover'); } m.cover = null; if (s) { if (s.fee > S.cash) return false; cash(-s.fee, 'cover'); m.cover = s.n; } return true; }
const guideOf = (sire, ds, looks) => nice((sire.fee * 0.55 + [0, 3, 8, 20, 45, 90][ds] * 1000) * [0.8, 0.92, 1.08, 1.3][looks == null ? 1 : looks]);
const SALEW = [null, [{ 10000: 55, 30000: 38, 75000: 7 }, { 1: 50, 2: 35, 3: 15 }], [{ 10000: 30, 30000: 45, 75000: 22, 125000: 3 }, { 1: 30, 2: 40, 3: 25, 4: 5 }], [{ 10000: 12, 30000: 35, 75000: 35, 125000: 13, 200000: 5 }, { 1: 15, 2: 30, 3: 35, 4: 15, 5: 5 }],
  [{ 30000: 10, 75000: 30, 125000: 30, 200000: 30 }, { 2: 10, 3: 30, 4: 35, 5: 25 }], [{ 75000: 15, 125000: 35, 200000: 50 }, { 3: 20, 4: 40, 5: 40 }]];
function genSale() {
  const t = tier(), [fw, dw] = SALEW[t], lots = [], noise = [0, 1.1, 0.95, 0.8, 0.65, 0.5][t];
  const whisper = h => { const z = h.res / 10 + gauss() * noise; return z > 0.9 ? 3 : z > 0.2 ? 2 : z > -0.6 ? 1 : 0; };
  for (let i = 0; i < 8; i++) { const fee = +wpick(fw), ds = +wpick(dw), sire = pick(D.stallions.filter(s => s.fee === fee)), dam = pick(D.mares.filter(m => m.stars === ds)); const h = foal(sire, dam);
    const guide = guideOf(sire, dam.stars, h.looks); lots.push({ ty: 'y', h, guide, wh: whisper(h), rmax: guide * Math.exp(gauss() * 0.28) * [0.8, 0.95, 1.1, 1.35][h.looks], by: pick(BUYERS), price: 0, lead: null, done: null }); }
  lots.sort((a, b) => a.guide - b.guide);
  for (let i = 0; i < 2; i++) { // horses in training: you know what you are getting
    const sire = pick(D.stallions.filter(s => s.fee <= 75000)), dam = pick(D.mares.filter(m => m.stars <= 3)), age = ri(2, 4), h = foal(sire, dam, { age, pot: 60 + t * 5 + ri(0, 14), mat: age === 2 ? pick(['e', 'n']) : pick(['e', 'n', 'l']) });
    h.runs = ri(4, 9); h.wins = ri(0, 2); h.pl = ri(1, 3); h.craft = 3; h.or = Math.round(ability(h, 1) + gauss() * 2 - 1); h.peak = h.or; h.perfs = [h.or]; h.form = [ri(1, 6), ri(1, 9), ri(1, 5)]; h.earn = h.wins * 6000 + h.pl * 1500;
    Object.assign(h.k, { pe: h.pot + gauss() * 3, pw: 5, mat: 2, trip: 2, build: 2, style: 2, temp: 2, con: 2, quirk: h.quirk ? 1 : 2 }); h.gs = { mat: h.mat, trip: h.trip, build: h.build, temp: h.temp, con: h.con };
    for (let g = h.gr[0]; g <= h.gr[1]; g++) if (rnd() < 0.7) h.k.gr[g] = 2; regroundGuess(h);
    const guide = valueOf(Object.assign({}, h, { age: age + 1 })); lots.push({ ty: 't', h, guide, rmax: guide * Math.exp(gauss() * 0.22), by: pick(BUYERS), price: 0, lead: null, done: null }); }
  for (let i = 0; i < 2; i++) { const st = +wpick(dw), m0 = pick(D.mares.filter(m => m.stars === st)); const guide = nice([0, 6, 15, 35, 80, 160][st] * 1000 * (0.85 + rnd() * 0.3));
    lots.push({ ty: 'm', m: { id: S.nid++, n: m0.n, stars: m0.stars, opt: m0.opt, peak: m0.peak, gr: m0.gr, age: ri(4, 8), cover: null, foals: 0 }, guide, rmax: guide * Math.exp(gauss() * 0.22), by: pick(BUYERS), price: 0, lead: null, done: null }); }
  return lots;
}
const arriving = () => S.young.filter(y => y.due === S.season + 1);
const boxesFree = () => T().boxes - S.horses.length - arriving().length;
const nextBid = l => nice(l.price ? l.price * 1.08 + 250 : l.guide * 0.4);
function bid(l) {
  if (l.done) return null; const p = nextBid(l); if (p > S.cash) return 'cash';
  if (l.ty === 'm' ? S.mares.length >= T().pad : boxesFree() <= 0) return 'full';
  l.price = p; l.lead = 'you'; const rp = nice(p * 1.08 + 250);
  if (rp <= l.rmax) { l.price = rp; l.lead = 'riv'; return 'raised'; }
  l.done = 'you'; cash(-p, 'purchase');
  if (l.ty === 'm') S.mares.push(l.m); else { l.h.cost = p; S.horses.push(l.h); }
  return 'won';
}
function pass(l) { if (l.done) return; if (!l.lead || l.lead === 'you') { l.price = nice(Math.max(l.guide * 0.4, l.rmax * (0.8 + rnd() * 0.15))); } l.lead = 'riv'; l.done = 'riv'; }
// 1 January: everyone a year older, youngsters due come into training, this winter's coverings become foals, a new crop of rivals
function newYear() {
  for (const h of S.horses) { h.age++; h.fresh = 100; h.inj = 0; h.sr = 0; h.worked = 0; h.kv++; }
  const due = S.young.filter(y => y.due === S.season + 1); for (const y of due) { y.age = 2; S.horses.push(y); } S.young = S.young.filter(y => y.due !== S.season + 1);
  for (const m of S.mares) { m.age++; if (m.cover) { const s = sireOf(m.cover); if (s) { const y = foal(s, m, { bred: 1, cost: Math.round(s.fee * 0.4) }); y.due = S.season + 2; y.age = 0; S.young.push(y); m.foals++; } m.cover = null; } }
  S.mares = S.mares.filter(m => m.age < 16);
  S.season++; genStars(); S.ss = newSeasonStats(); VC.clear(); return due;
}

const R = { CFG, on: ON, setData, get D() { return D; }, TRIPS, GOINGS, COURSE, TYPE, TIERS, CLS, CLASSICS, QUIRKS, QDESC, LAB, GREEN, COST, SD, BUYERS,
  use, init, get S() { return S; }, clearViews: () => VC.clear(), newSeasonStats, cash, addRep, rnd, mk, gauss, ri, pick, clamp, wpick, nice,
  fIdx, fLabel, tripOff, tripMod, tripLabel, groundMod, groundLabel, trackMod, ctype, isAW, freshMod, floorOf, tier, T, ability, estAb, potStar, potWord, orStars,
  foal, evid, starters, genStars, std, genField, prepRace, eligible, view, options, picks, autoPick, horse, gallop, runRace, rest,
  valueOf, studStars, mareStars, canStud, studFee, sell, retire, yearlingValue, sireOf, sires, setCover, guideOf, genSale, arriving, boxesFree, nextBid, bid, pass, newYear };
root.TBRULES = R; if (typeof module !== 'undefined') module.exports = R;
})(typeof window !== 'undefined' ? window : globalThis);
