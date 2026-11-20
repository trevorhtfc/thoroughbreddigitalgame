// =====================================================================================================================
// Thoroughbred, the career hub: the rules behind the prototype's screens (20 Nov 2026). No screen code in here, so it
// runs in Node for testing (game/tools/career_test.js) and can be swapped for the full game's rules later.
//
// A PROTOTYPE'S RULES: enough to make the calendar, the money and the yard move. They follow the design map and borrow
// the cut-down ideas of the "Thoroughbred Career" prototype (one freshness bar, stars for potential, the trainer's
// chance chips, gallops, the five reputation tiers) so the two can be joined. The races themselves are not here: a
// race is settled by one roll (runRace), where the full game would go to the racecard and the 3D race view.
//
// Time: the 33 turf weeks of the calendar (23 March to 8 November), then five winter turns of about a month each.
// Everything about the year is data: js/career/data.js (tools/calendar/calendar.json: 416 meetings, 2,836 races).
// =====================================================================================================================
(function (root) {
"use strict";
const D = root.CAREER_DATA;
const TRIPF = [5, 6, 7, 8, 10, 12, 14, 16], TRIPN = ["5f", "6f", "7f", "1m", "1m2f", "1m4f", "1m6f", "2m+"];
const GOINGS = ["Heavy", "Softer", "Good", "Quicker", "Quick"];
// The reputation ladder (names and points as the Career prototype's): boxes in the yard, paddocks at the stud,
// gallops a week, the dearest stallion you can book, how sharp the trainer's eye is (the width of his estimates)
const TIERS = [null,
  { n: "Small Owner", rep: 0, boxes: 4, pad: 2, gal: 2, fee: 30000, eye: 1 },
  { n: "Rising Yard", rep: 40, boxes: 6, pad: 3, gal: 2, fee: 75000, eye: 0.9 },
  { n: "Established Stable", rep: 180, boxes: 8, pad: 4, gal: 3, fee: 125000, eye: 0.8 },
  { n: "Leading Owner", rep: 550, boxes: 10, pad: 5, gal: 3, fee: 200000, eye: 0.7 },
  { n: "Champion Owner", rep: 1500, boxes: 12, pad: 6, gal: 4, fee: 1e9, eye: 0.6 }];
const COST = { training: 150, mare: 60, young: 30 };           // a week (about £7,800 a year a horse in training, as the Career prototype's £500 a fortnight over its season)
// Everyday prizes to the winner, by class: a little richer than real life so a small yard can live (the calendar's own
// figures are kept where they are higher, and for every big race)
const PURSE = { 6: 5000, 5: 7000, 4: 10000, 3: 16000, 2: 24000, 1: 25000 };
const PLACE = [1, 0.4, 0.2, 0.1];
const REP = { "Group 1": 100, "Group 2": 50, "Group 3": 35, "Listed": 25, "Heritage handicap": 30, "Sales race": 20 };
const REPCLS = { 2: 10, 3: 6, 4: 4, 5: 3, 6: 2 };
const CHIPS = ["Outclassed", "Place chance", "In the mix", "Big chance", "Hard to beat"];

// ---------------------------------------------------------------- the year, from the data
const MEET = D.meetings.map((m, i) => ({ i, date: m[0], course: m[1], name: m[2], kind: m[3], evening: !!m[4], week: m[5], races: [], aw: D.courses[m[1]].surface !== "Turf" }));
const RACES = D.races.map((r, i) => {
  const o = { id: i, m: MEET[r[0]], time: r[1], name: r[2], type: r[3], cls: r[4], band: r[5], ages: r[6], sex: r[7], f: r[8], dist: r[9], straight: !!r[10],
    prize: r[11], lo: r[12], hi: r[13], ratings: r[14], big: !!r[15], note: r[16] };
  if (!o.big || o.type === "Handicap") o.prize = Math.max(o.prize, PURSE[o.cls] || 0);
  o.hcap = o.type === "Handicap" || o.type === "Heritage handicap" || o.type === "Nursery";
  o.top = o.band ? +o.band.split("-")[1] : null;
  o.m.races.push(o); return o;
});
const WEEKS = D.weeks, NW = WEEKS.length;
const MEETS_OF = WEEKS.map((w) => MEET.filter((m) => m.week === w.w));
const weekInfo = (w) => WEEKS[w - 1];
const isWinter = (w) => w > 33;
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
// a calendar date in a later season: the same day of the week, 52 weeks on for each season
function dateOf(iso, season) { const d = new Date(iso + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + 364 * ((season || 1) - 1)); return d; }
const fmtDay = (iso, season) => { const d = dateOf(iso, season); return `${DAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; };
const fmtSpan = (w, season) => { const a = dateOf(weekInfo(w).a, season), b = dateOf(weekInfo(w).b, season);
  return a.getUTCMonth() === b.getUTCMonth() ? `${a.getUTCDate()}–${b.getUTCDate()} ${MONTHS[b.getUTCMonth()]}` : `${a.getUTCDate()} ${MONTHS[a.getUTCMonth()]} – ${b.getUTCDate()} ${MONTHS[b.getUTCMonth()]}`; };
const yearOf = (w, season) => dateOf(weekInfo(w).a, season).getUTCFullYear();
const money = (n) => (n < 0 ? "−£" : "£") + Math.abs(Math.round(n)).toLocaleString("en-GB");

// ---------------------------------------------------------------- luck (seeded, kept in the save)
function rnd(S) { S.seed = (S.seed + 0x6D2B79F5) | 0; let t = Math.imul(S.seed ^ (S.seed >>> 15), 1 | S.seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
const ri = (S, a, b) => a + Math.floor(rnd(S) * (b - a + 1));
const pick = (S, a) => a[Math.floor(rnd(S) * a.length)];
const gauss = (S) => { let u = 0, v = 0; while (!u) u = rnd(S); v = rnd(S); return Math.sqrt(-2 * Math.log(u)) * Math.cos(6.283185 * v); };
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

// ---------------------------------------------------------------- horses
// Hidden: pot (the best it can ever be), mat (early, normal, late), trip (index of the shorter of its two best trips),
// g (the run of goings it likes), temper. Known: est (the trainer's view of pot: centre c, give or take w), and what
// runs and gallops have shown (known.trip, known.ground, known.mat).
const MAT = {
  early: [[2.2, 0.84], [2.8, 0.94], [3.3, 1], [5.5, 1], [7.5, 0.92]],
  normal: [[2.2, 0.72], [2.8, 0.85], [3.5, 0.97], [4, 1], [6, 1], [8, 0.92]],
  late: [[2.2, 0.62], [2.8, 0.75], [3.5, 0.89], [4.3, 0.98], [4.8, 1], [7, 1], [9, 0.93]] };
const yearFrac = (w) => (w <= 33 ? (11 + w) / 52 : [0.87, 0.95, 0.04, 0.12, 0.19][w - 34]);
function frac(h, w) {
  const a = h.age + yearFrac(w), c = MAT[h.mat];
  if (a <= c[0][0]) return c[0][1];
  for (let i = 1; i < c.length; i++) if (a <= c[i][0]) { const [x0, y0] = c[i - 1], [x1, y1] = c[i]; return y0 + (y1 - y0) * (a - x0) / (x1 - x0); }
  return c[c.length - 1][1];
}
const ability = (S, h) => h.pot * frac(h, S.week);
const tripPos = (f) => { for (let i = 1; i < TRIPF.length; i++) if (f <= TRIPF[i]) return i - 1 + (f - TRIPF[i - 1]) / (TRIPF[i] - TRIPF[i - 1]); return TRIPF.length - 1; };
const tripIdx = (f) => Math.round(Math.max(0, tripPos(f)));
function tripAdj(h, f) { const p = tripPos(f); return p < h.trip ? -(h.trip - p) * 5 : p > h.trip + 1 ? -(p - h.trip - 1) * 5 : 0; }
function groundAdj(h, going) { const g = GOINGS.indexOf(going); if (g < 0) return 0; const off = g < h.g[0] ? h.g[0] - g : g > h.g[1] ? g - h.g[1] : 0; return [5, 0, -5, -10, -10][off]; }
const freshAdj = (h) => (h.fresh < 75 ? -(75 - h.fresh) / 4 : 0);
const greenAdj = (h) => (h.runs === 0 ? -6 : h.runs === 1 ? -3 : 0);
const SEXN = { c: "colt", f: "filly", g: "gelding" };
const sexWord = (h) => (h.sex === "f" && h.age >= 5 ? "mare" : h.sex === "c" && h.age >= 5 ? "horse" : SEXN[h.sex]);
function newName(S) {
  for (let k = 0; k < 400; k++) { const n = pick(S, D.nameA) + " " + pick(S, D.nameB); if (!S.names[n] && n.split(" ")[0] !== n.split(" ")[1]) { S.names[n] = 1; return n; } }
  return "Runner " + (S.nextId + 1);
}
const stallion = (name) => D.stallions.find((s) => s.name === name);
function makeHorse(S, o) {
  const sire = stallion(o.sire) || pick(S, D.stallions), damStars = o.damStars || ri(S, 1, 3);
  let pot = o.pot;
  if (pot == null) { pot = 47 + 7 * sire.stars + 6.5 * damStars + gauss(S) * 9.5; if (rnd(S) < 0.05) pot += 12 + rnd(S) * 10; }
  pot = clamp(Math.round(pot), 42, 134);
  const peak = sire.peak === "2YO" ? [0.5, 0.42, 0.08] : sire.peak === "4YO" ? [0.12, 0.48, 0.4] : [0.25, 0.55, 0.2], u = rnd(S);
  const mat = o.mat || (u < peak[0] ? "early" : u < peak[0] + peak[1] ? "normal" : "late");
  const opt = Math.max(0, TRIPN.indexOf(sire.opt)), trip = o.trip != null ? o.trip : clamp(opt - 1 + ri(S, 0, 2) - (rnd(S) < 0.5 ? 1 : 0), 0, 6);
  const gi = sire.ground.map((x) => GOINGS.indexOf(x)).filter((x) => x >= 0), g0 = clamp(Math.min(...gi) + ri(S, -1, 1), 0, 4), g1 = clamp(g0 + ri(S, 0, 2), g0, 4);
  const w = (o.w || 16) * TIERS[tierOf(S)].eye;
  const h = { id: ++S.nextId, name: o.name || newName(S), age: o.age, sex: o.sex || pick(S, ["c", "c", "f", "f", "g"]), colour: pick(S, ["bay", "bay", "bay", "chestnut", "chestnut", "brown", "grey"]),
    sire: sire.name, dam: o.dam || null, damStars, pot, mat, trip, g: o.g || [g0, g1], temper: rnd(S) < 0.3 ? "keen" : "calm", style: pick(S, ["Front-runner", "Prominent", "Midfield", "Hold-up"]),
    est: { c: clamp(Math.round(pot + gauss(S) * w * 0.45), 45, 130), w: Math.round(w) }, known: { trip: {}, ground: {}, mat: false },
    fresh: 100, or: null, runs: 0, wins: 0, places: 0, form: [], figs: [], seen: [], earned: 0, cost: o.cost || 0, kept: 0, entries: {}, out: 0, galloped: false,
    fromSale: !!o.fromSale, homebred: !!o.homebred, aw: 0, joined: [S.season, S.week] };
  return h;
}
// stars for potential, out of five: what a rating is worth
const stars = (r) => clamp((r - 45) / 15, 0.5, 5);
const starsOf = (h) => ({ sure: Math.round(stars(h.est.c - h.est.w) * 2) / 2, maybe: Math.round(stars(h.est.c + h.est.w) * 2) / 2 });
function sharpen(h, k) { h.est.c = Math.round(h.est.c + (h.pot - h.est.c) * k); h.est.w = Math.max(2, Math.round(h.est.w * (1 - k * 0.7))); }
const tierOf = (S) => { let t = 1; for (let i = 2; i <= 5; i++) if (S.rep >= TIERS[i].rep) t = i; return t; };

// ---------------------------------------------------------------- the state
function ledger(S, cat, text, amt, hid) {
  if (!amt) return;
  S.bank += amt; S.ledger.push({ s: S.season, w: S.week, cat, text, amt, hid: hid || 0 });
  if (S.ledger.length > 400) S.ledger.splice(0, S.ledger.length - 400);
  const y = S.year; (amt > 0 ? y.in : y.out)[cat] = ((amt > 0 ? y.in : y.out)[cat] || 0) + Math.abs(amt);
  if (hid) { const h = horse(S, hid); if (h) { if (cat === "Prize money") h.earned += amt; else if (amt < 0) h.kept -= amt; } }
}
function news(S, kind, title, body, go) { S.news.unshift({ s: S.season, w: S.week, kind, title, body, go: go || null, read: false }); if (S.news.length > 80) S.news.length = 80; }
const horse = (S, id) => S.horses.find((h) => h.id === id);
function newGame(seed, stable) {
  const S = { v: 1, seed: seed | 0 || 20261120, season: 1, week: 4, stable: stable || "Your stable", bank: 60000, rep: 0, nextId: 0, names: {},
    horses: [], mares: [], young: [], ledger: [], news: [], trophies: [], going: {}, sale: null, gallops: 0, last: null,
    year: { in: {}, out: {}, runs: 0, wins: 0, places: 0, start: 60000 }, stats: { runs: 0, wins: 0, best: null }, rivals: [], goals: [] };
  S.rivals = D.rivals.map((r) => ({ name: r.name, tier: r.tier, pic: r.pic, pts: Math.round([0, 1500 + rnd(S) * 1500, 620 + rnd(S) * 820, 150 + rnd(S) * 380, 8 + rnd(S) * 110][r.tier]) }));
  // three in training: a steady handicapper, a filly with a mark and more to come, an unraced colt
  const a = makeHorse(S, { age: 4, sex: "g", sire: "Mayson", pot: 73, mat: "normal", trip: 1, g: [2, 4], w: 5, cost: 14000 });
  Object.assign(a, { or: 68, runs: 9, wins: 2, places: 3, form: [3, 1, 5, 2, 0, 4], figs: [70, 66, 71], earned: 21400 }); a.est = { c: 73, w: 3 }; a.known = { trip: { 1: 0, 2: 0, 0: -1 }, ground: { 2: 0, 3: 5 }, mat: true };
  const b = makeHorse(S, { age: 3, sex: "f", sire: "New Bay", pot: 91, mat: "normal", trip: 3, g: [1, 3], w: 12, cost: 26000, fromSale: true });
  Object.assign(b, { or: 72, runs: 2, places: 1, form: [4, 2], figs: [66, 72], earned: 2100 }); b.known.trip[2] = -1;
  const c = makeHorse(S, { age: 3, sex: "c", sire: "Ulysses", pot: 80, mat: "late", trip: 4, g: [0, 2], w: 15, homebred: true, cost: 10000 });
  S.horses.push(a, b, c);
  // the stud: a mare with a foal at foot (to be covered again), a mare about to foal, and a yearling
  const m = D.mares.filter((x) => x.stars <= 2);
  const m1 = pick(S, m), m2 = pick(S, m.filter((x) => x !== m1));
  S.mares.push({ id: ++S.nextId, name: m1.name, stars: 2, age: 8, inFoal: null, cost: 20000 }, { id: ++S.nextId, name: m2.name, stars: 1, age: 11, inFoal: { sire: "Mehmas", season: 1 }, cost: 8000 });
  S.young.push(Object.assign(makeHorse(S, { age: 0, sex: "c", sire: "Havana Grey", damStars: 2, dam: m1.name, homebred: true, cost: 18500 }), { stage: "foal" }));
  S.young.push(Object.assign(makeHorse(S, { age: 1, sex: "f", sire: "Study Of Man", damStars: 1, dam: m2.name, homebred: true, cost: 10000 }), { stage: "yearling" }));
  S.goals = makeGoals(S);
  startWeek(S, true);
  news(S, "note", "Welcome to Newmarket", "Three horses in the yard, two mares at the stud and £60,000 in the bank. The Craven Breeze-Up is on at Tattersalls this week, and you have a box free.", "stables");
  return S;
}
function makeGoals(S) {
  const t = tierOf(S);
  return [{ id: "wins", text: `Win ${t + 1} races this season`, need: t + 1 }, { id: "profit", text: "Finish the season with more in the bank than you started", need: 1 },
    t < 5 ? { id: "tier", text: `Become a ${TIERS[t + 1].n}`, need: TIERS[t + 1].rep } : { id: "g1", text: "Win a Group 1", need: 1 }];
}
function goalState(S, g) {
  if (g.id === "wins") return { have: S.year.wins, need: g.need, done: S.year.wins >= g.need };
  if (g.id === "profit") return { have: S.bank - S.year.start, need: 0, done: S.bank > S.year.start, money: true };
  if (g.id === "tier") return { have: S.rep, need: g.need, done: S.rep >= g.need };
  const n = S.trophies.filter((x) => x.s === S.season && x.type === "Group 1").length; return { have: n, need: 1, done: n >= 1 };
}

// ---------------------------------------------------------------- the going, the sales: set up as a week begins
const GOING_ODDS = { 3: [14, 26, 34, 18, 8], 4: [8, 20, 36, 24, 12], 5: [4, 12, 32, 30, 22], 6: [2, 9, 26, 33, 30], 7: [2, 8, 24, 34, 32], 8: [2, 9, 26, 33, 30],
  9: [5, 13, 32, 30, 20], 10: [10, 20, 34, 24, 12], 11: [18, 28, 32, 16, 6] };
function drawGoing(S, m) {
  if (m.aw) return "Standard";
  const o = GOING_ODDS[+m.date.slice(5, 7)] || GOING_ODDS[4]; let u = rnd(S) * 100;
  for (let i = 0; i < 5; i++) { u -= o[i]; if (u < 0) return GOINGS[i]; } return "Good";
}
// The sales through the year (their usual weeks at Tattersalls)
const SALES = { 4: { name: "The Craven Breeze-Up Sale", lots: [["breeze", 8]], blurb: "Two-year-olds, ready to run. Each has galloped two furlongs against the clock." },
  6: { name: "The Guineas Breeze-Up and Horses in Training Sale", lots: [["breeze", 5], ["hit", 4]], blurb: "Late two-year-olds, and older horses with form and a handicap mark." },
  16: { name: "The July Sale", lots: [["hit", 8]], blurb: "Horses in training: instant runners with form in the book." },
  29: { name: "October Yearling Sale, Book 1", lots: [["yearling", 8, 1]], blurb: "The best-bred yearlings of the year. They race next season." },
  30: { name: "October Yearling Sale, Book 2", lots: [["yearling", 8, 2]], blurb: "Well-bred yearlings at more reachable prices." },
  31: { name: "October Yearling Sale, Books 3 and 4", lots: [["yearling", 10, 3]], blurb: "The bargain books: cheap yearlings, and now and then a good one." },
  32: { name: "The Autumn Horses in Training Sale", lots: [["hit", 10]], blurb: "The big clear-out: horses of every age and rating." },
  34: { name: "The December Sale", lots: [["mare", 6], ["foal", 4]], blurb: "Broodmares and foals: the stud's shopping week." } };
const priceOf = (q) => Math.round(6000 * Math.exp((q - 65) / 14) / 500) * 500;
function makeSale(S, def) {
  const t = tierOf(S), lots = [];
  for (const [kind, n, book] of def.lots) for (let i = 0; i < n; i++) {
    if (kind === "mare") {
      const st = clamp(ri(S, 1, 2) + (rnd(S) < 0.2 + t * 0.12 ? 1 : 0) + (rnd(S) < t * 0.08 ? 1 : 0), 1, 5), p = pick(S, D.mares);
      const name = S.mares.some((x) => x.name === p.name) ? newName(S) : p.name;
      lots.push({ id: lots.length + 1, kind, mare: { name, stars: st, age: ri(S, 4, 11) }, price: Math.round([0, 8000, 20000, 45000, 110000, 260000][st] * (0.8 + rnd(S) * 0.5) / 500) * 500, sold: false, note: `${st}-star mare by ${pick(S, D.stallions).name}` }); continue;
    }
    // which sires: Book 1 the best, Book 3 the cheapest; a better reputation sees better lots everywhere
    let pool = D.stallions.filter((s) => (book === 1 ? s.stars >= 3 : book === 3 ? s.stars <= 3 : kind === "breeze" ? s.stars <= 3 + (t > 2) : true));
    const sire = pick(S, pool), damStars = clamp((book === 1 ? 3 : book === 3 ? 1 : 2) + ri(S, -1, 1) + (rnd(S) < t * 0.1 ? 1 : 0), 1, 5);
    const age = kind === "foal" ? 0 : kind === "yearling" ? 1 : kind === "breeze" ? 2 : pick(S, [3, 3, 4, 4, 5, 6]);
    const h = makeHorse(S, { age, sire: sire.name, damStars, w: kind === "breeze" ? 12 : kind === "hit" ? 6 : 17, fromSale: kind !== "hit" });
    S.nextId--; h.id = 0; delete S.names[h.name];              // only a horse you buy takes an id and keeps its name
    let q = 47 + 7 * sire.stars + 6.5 * damStars, note;
    if (kind === "hit") {
      h.pot = clamp(Math.round(52 + rnd(S) * 30 + (rnd(S) < 0.15 ? 12 : 0) + t * 2), 45, 112); h.est = { c: clamp(Math.round(h.pot + gauss(S) * 3), 45, 115), w: 5 };
      const ab = h.pot * frac(h, S.week); h.runs = ri(S, 3, 14); h.wins = Math.min(h.runs, ri(S, 0, 3)); h.places = ri(S, 0, 4); h.or = Math.round(ab + gauss(S) * 3);
      h.figs = [h.or - 2, h.or + 1]; h.form = Array.from({ length: Math.min(6, h.runs) }, () => pick(S, [1, 2, 3, 4, 5, 6, 0, 0])); h.known.mat = true;
      h.known.trip[h.trip] = 0; h.known.ground[h.g[0]] = 5; q = h.or + (h.age <= 3 ? 6 : h.age >= 6 ? -8 : 0);
      note = `Rated ${h.or}. ${h.wins ? h.wins + (h.wins > 1 ? " wins" : " win") : "A maiden"} from ${h.runs} runs. Best at ${TRIPN[h.trip]}.`;
    } else if (kind === "breeze") {
      const t2 = 23.6 - (h.pot * frac(h, S.week) - 55) / 22 + gauss(S) * 0.18; h.breeze = Math.round(t2 * 100) / 100; q = h.est.c * 0.6 + q * 0.4 + (22.6 - h.breeze) * 5;
      note = `Breezed two furlongs in ${h.breeze.toFixed(2)}s${h.breeze < 23.25 ? ", a fast time" : h.breeze > 23.9 ? ", a slow time" : ""}. ${h.mat === "early" && rnd(S) < 0.7 ? "Looks sharp and ready." : h.mat === "late" && rnd(S) < 0.7 ? "A big frame to fill: one for later." : "A nice mover."}`;
    } else {
      q += gauss(S) * 4 + (h.pot - q) * 0.25;
      note = (kind === "foal" ? "A foal: two years before it races. " : "") + (h.mat === "early" && rnd(S) < 0.6 ? "Compact and forward." : h.mat === "late" && rnd(S) < 0.6 ? "Tall and unfurnished: will take time." : rnd(S) < 0.5 ? "A good walker." : "Well put together.");
    }
    lots.push({ id: lots.length + 1, kind, h, price: Math.max(2500, Math.round(priceOf(q) * (kind === "foal" ? 0.6 : kind === "breeze" ? 1.15 : 1) * (0.85 + rnd(S) * 0.35) / 500) * 500), sold: false, note });
  }
  return { week: S.week, name: def.name, blurb: def.blurb, lots };
}
function startWeek(S, first) {
  S.going = {}; for (const m of MEETS_OF[S.week - 1]) S.going[m.i] = drawGoing(S, m);
  S.gallops = 0; for (const h of S.horses) h.galloped = false;
  S.sale = SALES[S.week] ? makeSale(S, SALES[S.week]) : null;
  if (S.sale && !first) news(S, "sale", S.sale.name, S.sale.blurb + " On at Tattersalls this week.", "tatts");
  const nx = SALES[S.week + 1]; if (nx) news(S, "sale", "Next week: " + nx.name, nx.blurb, "tatts");
}

// ---------------------------------------------------------------- who can run where, and the trainer's view of it
// the standard of a race: the ratings its field is drawn from
function standard(r) {
  if (r.hcap) return { hcap: true, top: r.top };
  if (r.type === "Classified") return { lo: r.top - 12, hi: r.top };
  const m = /(\d+)\D+(\d+)/.exec(r.ratings);
  if (m) return { lo: +m[1], hi: +m[2] };
  const young = r.ages === "2yo", t = { 1: [78, 100], 2: [68, 92], 3: [62, 86], 4: [56, 80], 5: [50, 74], 6: [42, 66] }[r.cls] || [50, 74];
  return { lo: t[0] - (young ? 6 : 0), hi: t[1] - (young ? 6 : 0) };
}
const ageOk = (h, r) => ({ "2yo": h.age === 2, "3yo": h.age === 3, "2yo+": h.age >= 2, "3yo+": h.age >= 3, "4yo+": h.age >= 4 }[r.ages]);
const sexOk = (h, r) => !r.sex || (r.sex === "F" ? h.sex === "f" : r.sex === "C" ? h.sex !== "f" : h.sex !== "g");
// why a horse can't run in a race (null: it can)
function barred(S, h, r) {
  if (!ageOk(h, r)) return "For " + r.ages.replace("yo", "-year-olds");
  if (!sexOk(h, r)) return r.sex === "F" ? "Fillies only" : r.sex === "C" ? "Colts and geldings only" : "No geldings";
  if (r.type === "Maiden" && h.wins) return "Maidens only: has won";
  if (/unraced/.test(r.note) && r.type === "Maiden" && h.runs) return "Unraced horses only";
  if (r.type === "Novice" && h.wins > 2) return "Has won too often for a novice";
  if (/^Restricted/.test(r.name) && h.cost > 40000) return "For cheaper buys only";
  if ((r.hcap || r.type === "Classified") && h.or == null) return "Needs a handicap mark (two runs or a win)";
  if ((r.hcap || r.type === "Classified") && h.or > r.top) return `Rated too high (${h.or}) for a ${r.band}`;
  if (r.type === "Sales race" && !h.fromSale) return "Only for horses bought at the sales";
  if (/All-Weather Championships Finals/.test(r.m.name) && h.aw < 3) return "Needs three all-weather runs over the winter";
  return null;
}
// The trainer's estimate of what the horse runs to today, from what is known (never the hidden numbers)
function trainerEst(S, h) {
  let e = h.est.c * frac(h, S.week);
  if (h.or != null && h.runs >= 3) e = (e + h.or + 1) / 2; else if (h.or != null) e = e * 0.7 + (h.or + 2) * 0.3;
  return e;
}
function view(S, h, r) {
  const st = standard(r), ti = tripIdx(r.f), going = r.m.week === S.week ? S.going[r.m.i] : null, gi = GOINGS.indexOf(going);
  const kg = gi >= 0 ? h.known.ground[gi] : undefined;
  // the trip: known from a run or a gallop at it; else reasoned from the trips that are known (too sharp at 7f means
  // too sharp at 6f; a horse proven at 6f and 7f is a guess at a mile and unlikely at a mile and a half)
  let kt = h.known.trip[ti], tAdj = kt === undefined ? 0 : tripAdj(h, r.f);
  if (kt === undefined) { const K = Object.entries(h.known.trip).map(([i, v]) => [+i, v]), ok = K.filter((x) => x[1] === 0).map((x) => x[0]);
    const sharp = K.filter((x) => x[1] < 0 && x[0] >= ti).map((x) => x[0]), far = K.filter((x) => x[1] > 0 && x[0] <= ti).map((x) => x[0]);
    if (sharp.length) { kt = -1; tAdj = -5 * (Math.min(...sharp) - ti + 1); } else if (far.length) { kt = 1; tAdj = -5 * (ti - Math.max(...far) + 1); }
    else if (ok.length) { const d = Math.min(...ok.map((i) => Math.abs(i - ti))); if (d >= 2) { tAdj = -4 * (d - 1); if (d >= 3) kt = ti < ok[0] ? -1 : 1; } } }
  let e = trainerEst(S, h) + tAdj + (kg === undefined ? 0 : kg) + greenAdj(h) + penalty(h, r) + (r.m.week === S.week ? freshAdj(h) : 0);
  // how far ahead of a winning run the estimate is (set from 20,000 rolls of each kind of race: a handicapper needs
  // about 10 lb in hand of its mark to be odds-on; at level weights, a rating a pound or two above the field's best)
  const margin = st.hcap ? e - Math.max(h.or, st.top - 20) - 10.5 : e - st.hi - 1.5;
  const key = margin >= 0 ? 4 : margin >= -5 ? 3 : margin >= -9.5 ? 2 : margin >= -13.5 ? 1 : 0;
  const tick = (k, bad) => (k === undefined ? "?" : bad ? "no" : "ok");
  return { key, chip: CHIPS[key], trip: tick(kt, kt !== undefined && tAdj < -2), ground: r.m.aw ? "ok" : gi < 0 ? "?" : tick(kg, kg < 0), going, margin,
    fee: entryFee(r), low: st.hcap && h.or < st.top - 20, claim: isClaim(r) ? claimPrice(r) : 0, pen: -penalty(h, r) };
}
// Sellers and claimers: every runner is for sale at the race's set price. A horse too good for the race wins it and
// is very likely bought by another stable. Novices: a past winner carries a penalty (about 6 lb a win).
const isClaim = (r) => r.type === "Claimer" || r.type === "Seller";
const claimPrice = (r) => Math.round(5000 * Math.exp((standard(r).hi - 4 - 60) / 13) / 500) * 500;
const penalty = (h, r) => (r.type === "Novice" ? -6 * Math.min(2, h.wins) : 0);
const entryFee = (r) => Math.max(30, Math.round(r.prize * 0.01 / 10) * 10);
const weekRaces = (w) => MEETS_OF[w - 1].flatMap((m) => m.races);
// the races a horse could run in over the coming weeks, best first
function options(S, h, weeksAhead) {
  const out = [];
  for (let k = 0; k <= (weeksAhead || 0); k++) { const w = S.week + k; if (w > NW) break;
    for (const r of weekRaces(w)) if (!barred(S, h, r)) out.push({ r, v: view(S, h, r) }); }
  // soonest first; within a week the best chance first, with sellers and claimers (where the horse can be lost) last
  return out.sort((a, b) => a.r.m.week - b.r.m.week || (a.v.claim ? 1 : 0) - (b.v.claim ? 1 : 0) || b.v.key - a.v.key || b.r.prize - a.r.prize);
}
function enter(S, hid, rid) {
  const h = horse(S, hid), r = RACES[rid]; if (!h || !r) return "No such race";
  const why = barred(S, h, r); if (why) return why;
  if (h.out) return `${h.name} is on the easy list`;
  if (r.m.week < S.week) return "That race has been run";
  const other = S.horses.find((x) => x !== h && x.entries[r.m.week] === rid); if (other) return `${other.name} already runs for you in this race`;   // (one runner a race, for now)
  if (h.entries[r.m.week] != null) withdraw(S, hid, r.m.week);
  h.entries[r.m.week] = rid; ledger(S, "Entry fees", `${h.name}: ${r.name}, ${r.m.course}`, -entryFee(r), h.id); return null;
}
function withdraw(S, hid, week) {
  const h = horse(S, hid), rid = h && h.entries[week]; if (rid == null) return;
  delete h.entries[week]; ledger(S, "Entry fees", `${h.name} withdrawn: ${RACES[rid].name} (fee back)`, entryFee(RACES[rid]), h.id);
}
// "Trainer's picks": every fresh horse without a race this week goes where it has the best chance
function trainerPicks(S) {
  const made = [];
  for (const h of S.horses) {
    if (h.out || h.fresh < 72 || h.entries[S.week] != null) continue;
    // (never a seller or claimer with a horse worth more than the race's price: it would be bought)
    const o = options(S, h, 0).filter((x) => x.v.fee <= Math.max(300, S.bank * 0.02) && (!x.v.claim || valueOf(S, h) <= x.v.claim * 1.15));
    const best = o.find((x) => !S.horses.some((y) => y !== h && y.entries[S.week] === x.r.id)); if (!best) continue;
    if (best.v.key >= 2 || (best.v.key === 1 && h.or == null)) { if (!enter(S, h.id, best.r.id)) made.push({ h, r: best.r, v: best.v }); }
  }
  return made;
}

// ---------------------------------------------------------------- a race, settled by one roll (the prototype's stand-in for race day)
function runRace(S, h, r) {
  const st = standard(r), n = ri(S, r.lo, r.hi), going = S.going[r.m.i] || "Good";
  const parts = { trip: tripAdj(h, r.f), ground: r.m.aw ? 0 : groundAdj(h, going), fresh: freshAdj(h), green: greenAdj(h) };
  const eff = ability(S, h) + parts.trip + parts.ground + parts.fresh + parts.green + penalty(h, r), markUsed = st.hcap ? Math.max(h.or, st.top - 20) : 0;
  const mine = (st.hcap ? eff - markUsed : eff) + gauss(S) * (h.temper === "keen" ? 6 : 4.5);
  const opp = [];
  for (let i = 1; i < n; i++) opp.push(st.hcap ? gauss(S) * 3.5 + gauss(S) * 5 : st.lo + (st.hi - st.lo) * rnd(S) + gauss(S) * 5);
  opp.sort((a, b) => b - a);
  const pos = 1 + opp.filter((x) => x > mine).length, lbPerLen = r.f <= 6 ? 3 : r.f <= 9 ? 2.2 : 1.6;
  const gap = pos === 1 ? (n > 1 ? (mine - opp[0]) / lbPerLen : 5) : (opp[0] - mine) / lbPerLen;
  const fig = Math.round(st.hcap ? markUsed + mine : mine);
  const prize = pos <= 4 ? Math.round(r.prize * PLACE[pos - 1] / 10) * 10 : 0;
  // the horse
  const orBefore = h.or, learned = [];
  h.runs++; S.year.runs++; S.stats.runs++; if (r.m.aw) h.aw++;
  if (pos === 1) { h.wins++; S.year.wins++; S.stats.wins++; } else if (pos <= 3) { h.places++; S.year.places++; }
  h.form.push(pos > 9 ? 0 : pos); if (h.form.length > 6) h.form.shift();
  h.figs.push(fig); h.fresh = clamp(h.fresh - 40, 5, 100);
  if (h.or == null) { if (h.runs >= 2 || pos === 1) { const f = h.figs.slice().sort((a, b) => b - a); h.or = clamp(Math.round(pos === 1 ? f[0] - 1 : (f[0] + (f[1] != null ? f[1] : f[0])) / 2), 35, 125); learned.push(`A handicap mark: ${h.or}`); } }
  else { const d = fig - h.or; h.or = clamp(h.or + (d > 0 ? Math.round(d * 0.5) + (pos === 1 ? 2 : 0) : pos > 4 ? -1 - (d < -8 ? 1 : 0) : 0), 35, 130); }
  const ti = tripIdx(r.f), gi = GOINGS.indexOf(going);
  if (h.known.trip[ti] === undefined) { h.known.trip[ti] = parts.trip < -2 ? (tripPos(r.f) < h.trip ? -1 : 1) : 0; learned.push(parts.trip < -2 ? (tripPos(r.f) < h.trip ? `${r.dist} is sharper than ideal` : `${r.dist} is further than ideal`) : `${r.dist} suits`); }
  if (gi >= 0 && h.known.ground[gi] === undefined) { h.known.ground[gi] = parts.ground; learned.push(parts.ground > 0 ? `Loves ${going.toLowerCase()} ground` : parts.ground < 0 ? `Not at home on ${going.toLowerCase()} ground` : `Handles ${going.toLowerCase()} ground`); }
  if (!h.known.mat && h.runs >= 2) { h.known.mat = true; learned.push({ early: "An early type: at his best young", normal: "Maturing at the normal rate", late: "A late developer: better with time" }[h.mat].replace("his", h.sex === "f" ? "her" : "his")); }
  sharpen(h, 0.3);
  // money, reputation, the record
  const what = `${r.name}, ${r.m.course}`;
  if (prize) ledger(S, "Prize money", `${h.name}: ${pos === 1 ? "won" : ["", "", "2nd in", "3rd in", "4th in"][pos]} ${pos === 1 ? "the " : "the "}${what}`, prize, h.id);
  const base = REP[r.type] || REPCLS[r.cls] || 2, rep = pos === 1 ? base : pos === 2 ? Math.round(base * 0.4) : pos === 3 ? Math.round(base * 0.2) : 0;
  S.rep += rep;
  if (pos === 1 && (REP[r.type])) S.trophies.unshift({ s: S.season, w: S.week, race: r.name, course: r.m.course, type: r.type, horse: h.name, prize });
  if (!S.stats.best || fig > S.stats.best.fig) S.stats.best = { name: h.name, fig, race: what, s: S.season };
  h.seen.unshift({ s: S.season, w: S.week, date: r.m.date, race: r.name, course: r.m.course, dist: r.dist, type: r.type, cls: r.cls, going, pos, n, fig, prize }); if (h.seen.length > 30) h.seen.length = 30;
  // the trainer's debrief: the biggest thing that happened
  const worst = Object.entries(parts).sort((a, b) => a[1] - b[1])[0];
  let say;
  if (pos === 1) say = gap > 2.5 ? "Won going away. There's more to come." : gap < 0.5 ? "All out, but got there." : "Did it nicely.";
  else if (worst[1] <= -5) say = { trip: tripPos(r.f) < h.trip ? "Outpaced: wants further." : "Emptied late on: didn't get home.", ground: `Never happy on the ${going.toLowerCase()} ground.`, fresh: "Flat. Needed longer after the last run.", green: "Very green. Will know much more next time." }[worst[0]];
  else say = pos <= 3 ? "A solid run. No excuses, a bit more needed." : gap < 4 ? "Not beaten far. A drop in class would help." : "Well held. Needs an easier race.";
  const winner = pos === 1 ? null : rivalWinner(S, r);
  // a seller's winner goes to auction, and any claimer runner can be claimed: a horse worth more than the price usually goes
  let claimed = 0;
  if (isClaim(r) && (r.type === "Claimer" || pos === 1)) { const cp = claimPrice(r), v = valueOf(S, h);
    if (rnd(S) < clamp(0.1 + (v / cp - 0.8) * 0.9, 0.04, 0.95)) { claimed = cp; const to = pick(S, S.rivals.filter((x) => x.tier >= 3)).name;
      for (const w of Object.keys(h.entries)) if (+w !== S.week) withdraw(S, h.id, +w);
      ledger(S, "Horses sold", `${h.name} ${r.type === "Seller" ? "sold at the auction after the seller" : "claimed"} (${to})`, cp, h.id); S.horses.splice(S.horses.indexOf(h), 1);
      say = r.type === "Seller" ? `Sold at the auction afterwards to ${to} for ${money(cp)}.` : `Claimed out of the race by ${to} for ${money(cp)}.`;
      news(S, "sale", `${h.name} has left the yard`, say + " In sellers and claimers every runner is for sale at the set price.", "stables"); } }
  return { hid: h.id, name: h.name, rid: r.id, pos, n, going, prize, fig, gap: Math.abs(gap), orBefore, orAfter: h.or, learned, say, rep, winner, claimed };
}
// who beat you: a rival stable, the big ones more often in the big races
function rivalWinner(S, r) {
  const big = r.type.startsWith("Group") ? 3 : r.type === "Listed" ? 2 : r.cls <= 2 ? 1 : 0;
  const w = S.rivals.map((x) => [x, [[1, 1, 1, 1], [3, 2, 1.5, 1], [6, 3, 1.5, 0.6], [12, 4, 1, 0.3]][big][x.tier - 1]]);
  let u = rnd(S) * w.reduce((a, b) => a + b[1], 0); for (const [x, k] of w) { u -= k; if (u < 0) { x.pts += Math.round((REP[r.type] || REPCLS[r.cls] || 2) * 0.5); return { horse: pick(S, D.nameA) + " " + pick(S, D.nameB), owner: x.name, pic: x.pic }; } }
  return null;
}

// ---------------------------------------------------------------- gallops, buying, selling, the stud
function gallop(S, hid, kind) {
  const h = horse(S, hid); if (!h || h.galloped || h.out) return null;
  if (S.gallops >= TIERS[tierOf(S)].gal) return null;
  S.gallops++; h.galloped = true;
  if (kind === "easy") { h.fresh = clamp(h.fresh + 20, 0, 100); return { h, say: `${h.name} had an easy week on the Heath and looks the better for it.`, learned: [] }; }
  h.fresh = clamp(h.fresh - 5, 0, 100); sharpen(h, 0.3);
  const learned = [], todo = [];
  if (!h.known.mat) todo.push("mat"); if (h.known.trip[h.trip] === undefined || h.known.trip[h.trip + 1] === undefined) todo.push("trip");
  if (Object.keys(h.known.ground).length < 2) todo.push("ground");
  const k = todo.length ? pick(S, todo) : null;
  if (k === "mat") { h.known.mat = true; learned.push({ early: "An early type: forward for the age", normal: "Maturing at the normal rate", late: "A late developer: give time" }[h.mat]); }
  if (k === "trip") { h.known.trip[h.trip] = 0; h.known.trip[h.trip + 1] = 0; learned.push(`Shapes as though ${TRIPN[h.trip]} to ${TRIPN[h.trip + 1]} is the trip`); }
  if (k === "ground") { const g = h.g[0] <= 1 ? h.g[0] : h.g[1]; h.known.ground[g] = 5; learned.push(`Moves like one who wants ${GOINGS[g].toLowerCase()} ground`); }
  const e = trainerEst(S, h), lead = Math.round(e / 5) * 5;
  return { h, say: `${h.name} worked up Warren Hill with a ${lead}-rated lead horse and ${h.pot * frac(h, S.week) > lead + 2 ? "pulled clear" : h.pot * frac(h, S.week) < lead - 2 ? "couldn't go with it" : "finished upsides"}.`, learned };
}
const boxesFree = (S) => TIERS[tierOf(S)].boxes - S.horses.length;
const paddocksFree = (S) => TIERS[tierOf(S)].pad - S.mares.length;
function buy(S, lotId) {
  const lot = S.sale && S.sale.lots.find((l) => l.id === lotId); if (!lot || lot.sold) return "Sold";
  if (lot.price > S.bank) return "Not enough in the bank";
  if (lot.kind === "mare") { if (paddocksFree(S) <= 0) return "No paddock free at the stud"; lot.sold = true; const m = Object.assign({ id: ++S.nextId, inFoal: null, cost: lot.price }, lot.mare); S.mares.push(m);
    ledger(S, "Horses bought", `${m.name}, a ${m.stars}-star mare (${S.sale.name})`, -lot.price); return null; }
  const racing = lot.kind === "breeze" || lot.kind === "hit";
  if (racing && boxesFree(S) <= 0) return "No box free in the yard";
  if (!racing && S.young.length >= TIERS[tierOf(S)].pad * 2 + 2) return "No room at the stud for more youngstock";
  lot.sold = true; const h = lot.h; h.id = ++S.nextId; S.names[h.name] = 1; h.cost = lot.price; h.joined = [S.season, S.week];
  if (racing) S.horses.push(h); else { h.stage = lot.kind; S.young.push(h); }
  ledger(S, "Horses bought", `${h.name}, ${h.age ? h.age + "yo " : ""}${SEXN[h.sex]} by ${h.sire} (${S.sale.name})`, -lot.price, h.id); return null;
}
function valueOf(S, h) {
  const q = h.or != null ? h.or * 0.7 + trainerEst(S, h) * 0.3 : trainerEst(S, h) - 4;
  const age = h.age <= 3 ? 1.25 : h.age === 4 ? 1 : h.age === 5 ? 0.7 : 0.4;
  return Math.max(1500, Math.round(5000 * Math.exp((q - 60) / 13) * age * (h.sex === "f" && h.wins ? 1.3 : 1) / 500) * 500);
}
function sell(S, hid) {
  const i = S.horses.findIndex((h) => h.id === hid), j = S.young.findIndex((h) => h.id === hid);
  if (i < 0 && j < 0) return 0;
  const h = i >= 0 ? S.horses[i] : S.young[j], atSale = S.sale && /Training|July|Yearling|December/.test(S.sale.name);
  const v = i >= 0 ? Math.round(valueOf(S, h) * (atSale ? 1 : 0.8) / 500) * 500 : Math.round(priceOf(47 + 7 * stallion(h.sire).stars + 6.5 * h.damStars) * (h.stage === "foal" ? 0.5 : 0.9) * (atSale ? 1 : 0.8) / 500) * 500;
  for (const w of Object.keys(h.entries || {})) withdraw(S, hid, +w);
  if (i >= 0) S.horses.splice(i, 1); else S.young.splice(j, 1);
  ledger(S, "Horses sold", `${h.name} sold ${atSale ? "at " + S.sale.name : "privately"}`, v); return v;
}
function retireToStud(S, hid) {
  const i = S.horses.findIndex((h) => h.id === hid), h = S.horses[i]; if (!h || h.sex !== "f" || paddocksFree(S) <= 0) return false;
  const best = Math.max(h.or || 0, ...h.figs, 0), st = clamp(Math.round((best - 55) / 14) + (stallion(h.sire).stars >= 4 ? 1 : 0), 1, 5);
  S.horses.splice(i, 1); S.mares.push({ id: h.id, name: h.name, stars: st, age: h.age, inFoal: null, cost: 0, own: true });
  news(S, "stud", `${h.name} retires to the stud`, `She joins your broodmares as a ${st}-star mare.`, "stud"); return true;
}
// the covering season: late winter to the end of May
const coveringOpen = (S) => S.week <= 10 || S.week >= 37;
const stallionsFor = (S) => D.stallions.filter((s) => s.fee <= TIERS[tierOf(S)].fee).sort((a, b) => b.stars - a.stars || b.fee - a.fee);
function cover(S, mid, sireName) {
  const m = S.mares.find((x) => x.id === mid), s = stallion(sireName); if (!m || !s) return "No such mating";
  if (m.inFoal) return "Already in foal"; if (!coveringOpen(S)) return "The covering season is over";
  if (s.fee > TIERS[tierOf(S)].fee) return "His book is closed to you for now"; if (s.fee > S.bank) return "Not enough in the bank";
  m.inFoal = { sire: s.name, season: S.season + (S.week >= 37 ? 2 : 1) };
  ledger(S, "Stud fees", `${m.name} covered by ${s.name}`, -s.fee); return null;
}

// ---------------------------------------------------------------- what needs doing, and moving on a week
function runners(S) { return S.horses.filter((h) => h.entries[S.week] != null).map((h) => ({ h, r: RACES[h.entries[S.week]] })).sort((a, b) => (a.r.m.date + a.r.time).localeCompare(b.r.m.date + b.r.time)); }
function weeklyCost(S) {
  const k = isWinter(S.week) ? (S.week === 38 ? 3 : 4) : 1;
  const rows = [["Training fees", S.horses.length, COST.training], ["Broodmares' keep", S.mares.length, COST.mare], ["Foals and yearlings", S.young.length, COST.young]].filter((r) => r[1]);
  return { weeks: k, rows: rows.map(([t, n, each]) => ({ t, n, each, amt: n * each })), perWeek: rows.reduce((a, r) => a + r[1] * r[2], 0) };
}
function todos(S) {
  const t = [], T = TIERS[tierOf(S)];
  if (S.bank < 0) t.push({ k: "bank", go: "palace", text: "The bank is overdrawn", sub: "Sell a horse or win a race: you can't buy until it's cleared." });
  const idle = S.horses.filter((h) => !h.out && h.fresh >= 72 && h.entries[S.week] == null && options(S, h, 0).some((o) => o.v.key >= 1));
  if (idle.length) t.push({ k: "enter", go: "stables", n: idle.length, text: idle.length === 1 ? `Find a race for ${idle[0].name}` : `${idle.length} horses are ready to run`, sub: "Fresh, with races to suit this week." });
  if (S.sale) { const left = S.sale.lots.filter((l) => !l.sold).length; if (left && !S.saleSeen) t.push({ k: "sale", go: "tatts", n: left, text: S.sale.name, sub: `${left} lots at Tattersalls this week.` }); }
  const gl = T.gal - S.gallops; if (gl > 0 && S.horses.some((h) => !h.galloped && !h.out && h.est.w > 4)) t.push({ k: "gallop", go: "warren", n: gl, text: `${gl} gallop${gl > 1 ? "s" : ""} to use`, sub: "Work a horse on Warren Hill to learn more about it." });
  const empty = S.mares.filter((m) => !m.inFoal); if (empty.length && coveringOpen(S)) t.push({ k: "cover", go: "stud", n: empty.length, text: empty.length === 1 ? `Choose a stallion for ${empty[0].name}` : `${empty.length} mares to cover`, sub: "The covering season closes at the end of May." });
  const wait = S.young.filter((h) => h.stage === "ready"); if (wait.length) t.push({ k: "box", go: "stud", n: wait.length, text: `${wait[0].name} is ready for the yard`, sub: boxesFree(S) > 0 ? "A two-year-old waiting at the stud: move it into a box." : "No box free: sell a horse, or sell the youngster." });
  return t;
}
function moveToYard(S, hid) { const j = S.young.findIndex((h) => h.id === hid); if (j < 0 || boxesFree(S) <= 0) return false; const h = S.young.splice(j, 1)[0]; delete h.stage; S.horses.push(h); return true; }
// Go racing, then on to the next week. Returns the week's report for the screen.
function advance(S) {
  const rep = { season: S.season, week: S.week, results: [], costs: null, bankBefore: S.bank, events: [], tierBefore: tierOf(S), repBefore: S.rep };
  for (const { h, r } of runners(S)) { rep.results.push(runRace(S, h, r)); delete h.entries[S.week]; }
  // the week's keep
  const c = weeklyCost(S); rep.costs = c;
  for (const row of c.rows) ledger(S, row.t, `${row.n} × ${money(row.each)} a week${c.weeks > 1 ? ` × ${c.weeks} weeks` : ""}`, -row.amt * c.weeks);
  for (const h of S.horses) { h.kept += COST.training * c.weeks; h.fresh = clamp(h.fresh + (isWinter(S.week) ? 60 : 12), 0, 100); if (h.out) h.out = Math.max(0, h.out - c.weeks);
    if (h.fresh < 45 && !h.out && rnd(S) < 0.25) { h.out = 4; rep.events.push({ kind: "vet", text: `${h.name} is jarred up after running while tired: four weeks on the easy list.` }); news(S, "vet", `${h.name}: four weeks off`, "Jarred up after running while tired. Horses need a fortnight or so between races.", "stables"); } }
  for (const x of S.rivals) x.pts += Math.round(rnd(S) * [0, 9, 4.5, 2, 0.8][x.tier] * c.weeks);
  // The safety net (the design map's open question; this is the prototype's answer): more than £25,000 overdrawn and the
  // bank sells for you, youngest stock first; with nothing left to sell, a new backer puts in £20,000
  while (S.bank < -25000) {
    const y = S.young[0], m = !y && S.mares.slice().sort((a, b) => a.stars - b.stars)[0], h = !y && !m && S.horses.slice().sort((a, b) => valueOf(S, a) - valueOf(S, b))[0];
    if (y || h) { const x = y || h, v = sell(S, x.id); rep.events.push({ kind: "bank", text: `The bank has sold ${x.name} for ${money(v)} to cover the overdraft.` }); news(S, "bank", `The bank has sold ${x.name}`, `More than £25,000 overdrawn: ${money(v)} raised.`, "palace"); }
    else if (m) { const v = Math.round([0, 8000, 20000, 45000, 110000, 260000][m.stars] * 0.6 / 500) * 500; S.mares.splice(S.mares.indexOf(m), 1); ledger(S, "Horses sold", `${m.name} sold by the bank`, v);
      rep.events.push({ kind: "bank", text: `The bank has sold the mare ${m.name} for ${money(v)} to cover the overdraft.` }); news(S, "bank", `The bank has sold ${m.name}`, `More than £25,000 overdrawn: ${money(v)} raised.`, "palace"); }
    else { ledger(S, "A new backer", "A new backer clears the overdraft and puts in £20,000", 20000 - S.bank); rep.events.push({ kind: "bank", text: "With nothing left to sell, a new backer has cleared the overdraft and put in £20,000. Start again at Tattersalls." });
      news(S, "bank", "A new backer", "The overdraft is cleared and there is £20,000 in the bank. The sales are the place to start again.", "tatts"); }
  }
  // on a week
  const was = S.week;
  if (S.week === NW) { rep.review = seasonReview(S); S.week = 1; S.season++; S.year = { in: {}, out: {}, runs: 0, wins: 0, places: 0, start: S.bank }; S.goals = makeGoals(S); for (const h of S.horses) h.entries = {};
    const sp = 4000 + 4000 * tierOf(S); ledger(S, "Sponsor", `Your sponsor's cheque for the new season (${TIERS[tierOf(S)].n})`, sp); rep.events.push({ kind: "bank", text: `A new season: your sponsor's cheque for ${money(sp)} has arrived.` }); S.year.start = S.bank - sp; }
  else S.week++;
  if (S.week === 36) newYear(S, rep);
  if (S.week === 3) for (const h of S.horses) h.aw = 0;
  // the stud: foals arrive in the spring
  if (S.week <= 8) for (const m of S.mares) if (m.inFoal && m.inFoal.season <= S.season && rnd(S) < 0.3 + S.week * 0.09) {
    const f = Object.assign(makeHorse(S, { age: 0, sire: m.inFoal.sire, damStars: m.stars, dam: m.name, homebred: true, cost: stallion(m.inFoal.sire).fee }), { stage: "foal" }); m.inFoal = null; S.young.push(f);
    rep.events.push({ kind: "foal", text: `${m.name} has foaled a ${SEXN[f.sex]} by ${f.sire}.` }); news(S, "stud", `A ${SEXN[f.sex]} foal for ${m.name}`, `By ${f.sire}. ${coveringOpen(S) ? "She can be covered again this spring." : ""}`, "stud"); }
  S.saleSeen = false; startWeek(S);
  const t = tierOf(S); if (t > rep.tierBefore) { rep.tierUp = t; news(S, "rep", `You are now a ${TIERS[t].n}`, `${TIERS[t].boxes} boxes in the yard, ${TIERS[t].pad} paddocks at the stud, ${TIERS[t].gal} gallops a week, and better stallions and sale lots.`, "palace"); }
  rep.bankAfter = S.bank; rep.repAfter = S.rep; rep.from = was; S.last = rep; return rep;
}
function newYear(S, rep) {
  for (const h of S.horses) h.age++; for (const m of S.mares) m.age++;
  for (const h of S.young) { h.age++; if (h.age >= 2) h.stage = "ready"; else h.stage = "yearling"; }
  for (const h of S.young.filter((x) => x.stage === "ready")) if (boxesFree(S) > 0) { moveToYard(S, h.id); rep.events.push({ kind: "yard", text: `${h.name}, now two, has come into the yard from the stud.` }); }
  rep.events.push({ kind: "year", text: "1 January: every horse is a year older." });
  news(S, "note", "New Year: every horse a year older", "Yearlings are now two-year-olds and can come into training. The turf season starts in late March.", "stables");
}
function seasonReview(S) {
  const sum = (o) => Object.values(o).reduce((a, b) => a + b, 0);
  return { season: S.season, runs: S.year.runs, wins: S.year.wins, places: S.year.places, in: sum(S.year.in), out: sum(S.year.out), prize: S.year.in["Prize money"] || 0,
    goals: S.goals.map((g) => ({ text: g.text, done: goalState(S, g).done })), tier: tierOf(S), trophies: S.trophies.filter((t) => t.s === S.season) };
}
// the owners' table: you among the rival stables
function table(S) { return [...S.rivals.map((r) => ({ name: r.name, pts: r.pts, tier: r.tier, pic: r.pic })), { name: S.stable, pts: S.rep, you: true }].sort((a, b) => b.pts - a.pts); }

root.CAREER = { isClaim, claimPrice, TIERS, TRIPN, TRIPF, GOINGS, CHIPS, COST, SALES, MEET, RACES, WEEKS, NW, MEETS_OF, weekInfo, isWinter, fmtDay, fmtSpan, yearOf, dateOf, money, newGame, tierOf, horse, stallion,
  ability, frac, starsOf, stars, trainerEst, standard, barred, view, options, entryFee, weekRaces, enter, withdraw, trainerPicks, runRace, gallop, boxesFree, paddocksFree, buy, sell, valueOf, retireToStud,
  coveringOpen, stallionsFor, cover, runners, weeklyCost, todos, moveToYard, advance, table, goalState, sexWord, tripIdx, tripAdj, groundAdj, priceOf, rnd };
})(typeof window !== "undefined" ? window : globalThis);
