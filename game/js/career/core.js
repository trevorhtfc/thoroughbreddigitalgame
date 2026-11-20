// =====================================================================================================================
// Thoroughbred, the career hub: what happens between the screens (20 Nov 2026). No screen code in here, so it runs in
// Node for testing (game/tools/career_test.js).
//
// THE RULES ARE NOT IN THIS FILE. The horses, what is hidden about them, the trainer's view, race day, the
// handicapper, gallops, the sales and the stud are js/career/rules/rules.js (window.TBRULES, the "Thoroughbred Career"
// prototype's rules), reached through js/career/rules/hub-adapter.js (window.TBJOIN). Read rules/README.md first.
// This file is the HOST: it owns the year (the real calendar, week by week), which races are on offer, entries and
// their fees, the going, the sales through the year, the stud's seasons, the book of money, the post, the goals and
// the owners' table, and it calls the rules in the order the README sets out.
//
// One state object, S, is both the hub's save and the rules' state (TBRULES.init adds its own fields to it).
// Two counters of years live in it, and they are different: S.season is the rules' (it turns on 1 January, when
// horses age), S.yr is the calendar's racing year (it turns in late March, at week 1, and dates are worked out from it).
// Time: the 33 turf weeks of the calendar (23 March to 8 November), then five winter turns of about a month each.
// =====================================================================================================================
(function (root) {
"use strict";
const D = root.CAREER_DATA, R = root.TBRULES, J = root.TBJOIN;
J.setup(D);                                                      // the hub's stallions, mares, names and rival owners; weekly turns
// Where the two prototypes differ (the table in rules/README.md) the hub's own way is kept until the owner says
// otherwise: weekly turns, these costs, two gallops a week, one runner a race, sellers and claimers that can lose you
// the horse, the real sales through the year, foal-yearling-in training, this reputation table, the hub's goals.
// The hub also gives one more paddock at each tier than the rules' own table (it starts you with two mares).
[2, 3, 4, 5, 6].forEach((p, i) => { R.TIERS[i + 1].pad = p; });
const TIERS = R.TIERS, GOINGS = R.GOINGS, TRIPN = R.TRIPS;
const COST = { training: 150, mare: 60, young: 30 };           // a week
// Prize money is the calendar's own (the real races' figures): the rules were balanced on it, at these costs.
const REP = { "Group 1": 100, "Group 2": 50, "Group 3": 35, "Listed": 25, "Heritage handicap": 30, "Sales race": 20 };
const REPCLS = { 2: 10, 3: 6, 4: 4, 5: 3, 6: 2 };
const CHIPS = ["Outclassed", "Place chance", "In the mix", "Big chance", "Hard to beat"];

// ---------------------------------------------------------------- the year, from the data
const MEET = D.meetings.map((m, i) => ({ i, date: m[0], course: m[1], name: m[2], kind: m[3], evening: !!m[4], week: m[5], races: [], aw: D.courses[m[1]].surface !== "Turf" }));
const RACES = D.races.map((r, i) => {
  const o = { id: i, m: MEET[r[0]], time: r[1], name: r[2], type: r[3], cls: r[4], band: r[5], ages: r[6], sex: r[7], f: r[8], dist: r[9], straight: !!r[10],
    prize: r[11], lo: r[12], hi: r[13], ratings: r[14], big: !!r[15], note: r[16] };
  o.hcap = o.type === "Handicap" || o.type === "Heritage handicap" || o.type === "Nursery";
  o.top = o.band ? +o.band.split("-")[1] : null;
  o.m.races.push(o); return o;
});
const WEEKS = D.weeks, NW = WEEKS.length;
const MEETS_OF = WEEKS.map((w) => MEET.filter((m) => m.week === w.w));
const weekInfo = (w) => WEEKS[w - 1];
const isWinter = (w) => w > 33;
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
// a calendar date in a later racing year: the same day of the week, 52 weeks on for each year
function dateOf(iso, yr) { const d = new Date(iso + "T12:00:00Z"); d.setUTCDate(d.getUTCDate() + 364 * ((yr || 1) - 1)); return d; }
const fmtDay = (iso, yr) => { const d = dateOf(iso, yr); return `${DAYS[d.getUTCDay()]} ${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`; };
const fmtSpan = (w, yr) => { const a = dateOf(weekInfo(w).a, yr), b = dateOf(weekInfo(w).b, yr);
  return a.getUTCMonth() === b.getUTCMonth() ? `${a.getUTCDate()}–${b.getUTCDate()} ${MONTHS[b.getUTCMonth()]}` : `${a.getUTCDate()} ${MONTHS[a.getUTCMonth()]} – ${b.getUTCDate()} ${MONTHS[b.getUTCMonth()]}`; };
const yearOf = (w, yr) => dateOf(weekInfo(w).a, yr).getUTCFullYear();
const money = (n) => (n < 0 ? "−£" : "£") + Math.abs(Math.round(n)).toLocaleString("en-GB");
const ORD = ["", "1st", "2nd", "3rd", "4th"];

// ---------------------------------------------------------------- luck for the hub's own business (the going, the rivals' table); the rules keep their own in S.rs
function rnd(S) { S.seed = (S.seed + 0x6D2B79F5) | 0; let t = Math.imul(S.seed ^ (S.seed >>> 15), 1 | S.seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }
const pick = (S, a) => a[Math.floor(rnd(S) * a.length)];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
// point the rules at this game (they play one game at a time)
const use = (S) => { if (R.S !== S) R.use(S); return S; };
const tierOf = (S) => { use(S); return R.tier(); };
const horse = (S, id) => S.horses.find((h) => h.id === id);
const SEXN = { c: "colt", f: "filly", g: "gelding" };
const sexWord = (h) => (h.sex === "f" && h.age >= 5 ? "mare" : h.sex === "c" && h.age >= 5 ? "horse" : SEXN[h.sex]);

// ---------------------------------------------------------------- the book and the post
// Money moves only through the rules (TBRULES.cash), which call back here so every pound is written in the book.
// When the hub knows better than the rules what a payment is for, it says so in NOTE first.
const MONEY = { prize: "Prize money", sale: "Horses sold", stud: "Stud income", cover: "Stud fees", purchase: "Horses bought", fees: "Training fees", race: "Entry fees" };
let NOTE = null;
R.on.money = (amt, why, h) => {
  const S = R.S; if (!S || !S.ledger || !amt) return;
  const n = NOTE || {}, cat = n.cat || MONEY[why] || "Other", hid = n.hid || (h && h.id) || 0;
  const text = n.text || (why === "prize" ? `${h.n}: prize money` : why === "sale" ? `${h.n} sold` : why === "stud" ? `${h.n} retires to stand as a stallion` : why === "cover" ? (amt < 0 ? "A stud fee" : "A stud fee returned") : why === "purchase" ? "Bought at the sales" : cat);
  S.ledger.push({ s: S.yr, w: S.week, cat, text, amt, hid }); if (S.ledger.length > 400) S.ledger.splice(0, S.ledger.length - 400);
  const y = S.year; (amt > 0 ? y.in : y.out)[cat] = ((amt > 0 ? y.in : y.out)[cat] || 0) + Math.abs(amt);
  if (hid && cat === "Entry fees") { const x = horse(S, hid); if (x) x.kept -= amt; }
};
function pay(S, cat, text, amt, hid) { if (!amt) return; use(S); NOTE = { cat, text, hid: hid || 0 }; try { R.cash(amt, "hub"); } finally { NOTE = null; } }
function noted(note, fn) { NOTE = note; try { return fn(); } finally { NOTE = null; } }
function news(S, kind, title, body, go) { S.news.unshift({ s: S.yr, w: S.week, kind, title, body, go: go || null, read: false }); if (S.news.length > 80) S.news.length = 80; }

// ---------------------------------------------------------------- a new career
// what the hub keeps on a horse beside the rules' own record
const extras = (S, h, o) => Object.assign(h, { entries: {}, colour: pick(S, ["bay", "bay", "bay", "chestnut", "chestnut", "brown", "grey"]), kept: 0, aw: 0, galloped: false, fromSale: false, joined: [S.yr, S.week] }, o || {});
// a homebred at the stud: a foal (age 0) or a yearling (age 1), waiting to come into training at two
function bornTo(S, sireName, m, age) { const s = R.sireOf(sireName), y = R.foal(s, m, { bred: 1, cost: Math.round(s.fee * 0.4) }); y.age = age; y.stage = age ? "yearling" : "foal"; return extras(S, y); }
function newGame(seed, stable) {
  const S = { v: 2, seed: seed | 0 || 20261120, yr: 1, week: 4, stable: stable || "Your stable", cash: 60000, ledger: [], news: [], trophies: [], going: {}, sale: null, gallops: 0, last: null, rd: null,
    year: { in: {}, out: {}, runs: 0, wins: 0, places: 0, start: 60000 }, stats: { runs: 0, wins: 0 }, rivals: [], goals: [] };
  R.init(S, S.seed);
  S.rivals = D.rivals.map((r) => ({ name: r.name, tier: r.tier, pic: r.pic, pts: Math.round([0, 1500 + rnd(S) * 1500, 620 + rnd(S) * 820, 150 + rnd(S) * 380, 8 + rnd(S) * 110][r.tier]) }));
  // the rules' three to start: an honest handicapper with a mark, a sharp two-year-old colt and a slower-burning filly
  const st = R.starters(); st.forEach((h, i) => extras(S, h, { fromSale: i > 0 })); S.horses.push(...st);
  // the hub's stud: a mare to cover this spring with a foal at foot, an older mare about to foal, and a yearling
  const mare = (st, age) => { const m = pick(S, R.D.mares.filter((x) => x.stars === st && !S.mares.some((y) => y.n === x.n))); return { id: S.nid++, n: m.n, stars: m.stars, opt: m.opt, peak: m.peak, gr: m.gr, age, cover: null, foals: 1, inFoal: null }; };
  const m1 = mare(2, 8), m2 = mare(1, 11); m2.inFoal = { sire: "Mehmas", due: 1 }; S.mares.push(m1, m2);
  S.young.push(bornTo(S, "Havana Grey", m1, 0), bornTo(S, "Study Of Man", m2, 1));
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
  if (g.id === "profit") return { have: S.cash - S.year.start, need: 0, done: S.cash > S.year.start, money: true };
  if (g.id === "tier") return { have: S.rep, need: g.need, done: S.rep >= g.need };
  const n = S.trophies.filter((x) => x.s === S.yr && x.type === "Group 1").length; return { have: n, need: 1, done: n >= 1 };
}

// ---------------------------------------------------------------- the going and the sales: set up as a week begins
const GOING_ODDS = { 3: [14, 26, 34, 18, 8], 4: [8, 20, 36, 24, 12], 5: [4, 12, 32, 30, 22], 6: [2, 9, 26, 33, 30], 7: [2, 8, 24, 34, 32], 8: [2, 9, 26, 33, 30],
  9: [5, 13, 32, 30, 20], 10: [10, 20, 34, 24, 12], 11: [18, 28, 32, 16, 6] };
function drawGoing(S, m) {
  if (m.aw) return "Standard";
  const o = GOING_ODDS[+m.date.slice(5, 7)] || GOING_ODDS[4]; let u = rnd(S) * 100;
  for (let i = 0; i < 5; i++) { u -= o[i]; if (u < 0) return GOINGS[i]; } return "Good";
}
// The sales through the year (their usual weeks at Tattersalls). The lots themselves are the rules' (TBRULES.genSale),
// shared out by kind: yearlings in October (the dearest in Book 1), breeze-up two-year-olds in spring (a yearling lot
// a year older that has galloped against the clock), horses in training, and mares and foals in December.
const SALES = { 4: { name: "The Craven Breeze-Up Sale", lots: [["breeze", 8]], blurb: "Two-year-olds, ready to run. Each has galloped two furlongs against the clock." },
  6: { name: "The Guineas Breeze-Up and Horses in Training Sale", lots: [["breeze", 5], ["hit", 4]], blurb: "Late two-year-olds, and older horses with form and a handicap mark." },
  16: { name: "The July Sale", lots: [["hit", 8]], blurb: "Horses in training: instant runners with form in the book." },
  29: { name: "October Yearling Sale, Book 1", lots: [["yearling", 8, 1]], blurb: "The best-bred yearlings of the year. They race next season." },
  30: { name: "October Yearling Sale, Book 2", lots: [["yearling", 8, 2]], blurb: "Well-bred yearlings at more reachable prices." },
  31: { name: "October Yearling Sale, Books 3 and 4", lots: [["yearling", 10, 3]], blurb: "The bargain books: cheap yearlings, and now and then a good one." },
  32: { name: "The Autumn Horses in Training Sale", lots: [["hit", 10]], blurb: "The big clear-out: horses of every age and rating." },
  34: { name: "The December Sale", lots: [["mare", 6], ["foal", 4]], blurb: "Broodmares and foals: the stud's shopping week." } };
// names of lots nobody of yours bought go back in the hat
const freeNames = (S, lots) => { for (const l of lots) if (l.h && l.done !== "you") delete S.used[l.h.n]; };
function makeSale(S, def) {
  use(S); const lots = [], spare = [], taken = new Set(S.mares.map((m) => m.n));
  const batch = (ty, calls) => { const out = []; for (let k = 0; k < calls; k++) for (const l of R.genSale()) (l.ty === ty ? out : spare).push(l); return out; };
  const scale = (l, k) => { l.guide = R.nice(l.guide * k); l.rmax *= k; };
  for (const [kind, n, book] of def.lots) {
    let got = [];
    if (kind === "mare") { for (let k = 0; k < 8 && got.length < n; k++) for (const l of batch("m", 1)) { if (got.length < n && !taken.has(l.m.n)) { taken.add(l.m.n); l.m.inFoal = null; got.push(l); } } }
    else if (kind === "hit") { got = batch("t", Math.ceil(n / 2)).slice(0, n);
      // the rules rate a sale horse as it will be at the season's end: in a spring or summer sale it is rated as it is today
      for (const l of got) { const h = l.h, d = Math.round(R.ability(h, 1) - R.ability(h)); if (S.week < 30 && d) { h.or -= d; h.peak = h.or; h.perfs = [h.or]; const g = R.valueOf(h); l.rmax *= g / l.guide; l.guide = g; } } }
    else { const pool = batch("y", book === 1 || book === 3 ? 3 : book === 2 ? 2 : Math.ceil(n / 8)).sort((a, b) => a.guide - b.guide);
      if (book === 1) got = pool.slice(-n); else if (book === 3) got = pool.slice(0, n); else if (book === 2) got = pool.slice(Math.floor((pool.length - n) / 2)).slice(0, n);
      else { got = pool.slice(); while (got.length > n) got.splice(Math.floor(rnd(S) * got.length), 1); }
      for (const l of got) { const h = l.h;
        if (kind === "breeze") { h.age = 2; R.evid(h, 0.3); scale(l, 1.2); l.secs = Math.round((23.6 - (h.k.pe - 80) / 30 + (rnd(S) - 0.5) * 0.16) * 100) / 100; }
        else if (kind === "foal") { h.age = 0; scale(l, 0.6); } }
      spare.push(...pool.filter((l) => !got.includes(l))); }
    for (const l of got) { l.kind = kind; l.id = lots.length + 1; lots.push(l); }
  }
  freeNames(S, spare);
  return { week: S.week, name: def.name, blurb: def.blurb, lots };
}
function startWeek(S, first) {
  use(S); if (S.sale) freeNames(S, S.sale.lots);
  J.startWeek(S, S.week);
  if (S.week >= 36) S.prog = 0;                                  // after 1 January the horses are a year older and at the start of that year's growing
  S.going = {}; for (const m of MEETS_OF[S.week - 1]) S.going[m.i] = drawGoing(S, m);
  S.gallops = 0; for (const h of S.horses) h.galloped = false;
  S.sale = SALES[S.week] ? makeSale(S, SALES[S.week]) : null; S.saleSeen = false;
  if (S.sale && !first) news(S, "sale", S.sale.name, S.sale.blurb + " On at Tattersalls this week.", "tatts");
  const nx = SALES[S.week + 1]; if (nx) news(S, "sale", "Next week: " + nx.name, nx.blurb, "tatts");
  // an entry made weeks ago may no longer be allowed (a win since, a new rating, a birthday)
  for (const h of S.horses) { const rid = h.entries[S.week]; if (rid == null) continue; const why = whyNot(S, h, RACES[rid]);
    if (why) { withdraw(S, h.id, S.week); news(S, "note", `${h.n} is out of the ${RACES[rid].name}`, `${why}. The entry fee is back in the bank.`, "stables"); } }
}

// ---------------------------------------------------------------- who can run where, and the trainer's view of it
const ageOk = (h, r) => ({ "2yo": h.age === 2, "3yo": h.age === 3, "2yo+": h.age >= 2, "3yo+": h.age >= 3, "4yo+": h.age >= 4 }[r.ages]);
const sexOk = (h, r) => !r.sex || (r.sex === "F" ? h.sex === "f" : r.sex === "C" ? h.sex !== "f" : h.sex !== "g");
const hcapLike = (r) => r.hcap || r.type === "Classified";
// The calendar's conditions, in words (null: none of them stops the horse). The rules have the last word (whyNot).
function barred(S, h, r) {
  if (!ageOk(h, r)) return "For " + r.ages.replace("yo", "-year-olds");
  if (!sexOk(h, r)) return r.sex === "F" ? "Fillies only" : r.sex === "C" ? "Colts and geldings only" : "No geldings";
  if (r.type === "Maiden" && h.wins) return "Maidens only: has won";
  if (/unraced/.test(r.note) && r.type === "Maiden" && h.runs) return "Unraced horses only";
  if (r.type === "Maiden" && /^(Restricted|Auction)/.test(r.name) && h.cost > 30000) return "For cheaper buys only";
  if (r.type === "Novice" && h.wins > 2) return "Has won too often for a novice";
  if (hcapLike(r) && h.or == null) return "Needs a rating (two runs or a win)";
  if (hcapLike(r) && h.or > r.top) return `Rated too high (${h.or}) for a ${r.band}`;
  if (r.type === "Sales race" && !h.fromSale) return "Only for horses bought at the sales";
  if (/All-Weather Championships Finals/.test(r.m.name) && h.aw < 3) return "Needs three all-weather runs over the winter";
  return null;
}
const goingOf = (S, r) => (r.m.week === S.week ? S.going[r.m.i] : null);
// The rules' copy of a calendar race, with its field of rivals. It is made the first time anyone looks and kept in the
// save (S.cards), so the racecard a player studies is the race that is run.
const raceOf = (S, r) => { use(S); return J.raceFor(S, r, r.m.aw ? null : goingOf(S, r)); };
function whyNot(S, h, r) { use(S); if (h.inj > 0) return "On the easy list"; return barred(S, h, r) || (R.eligible(h, raceOf(S, r)) ? null : "Not qualified for this race"); }
// the trainer's view (the rules'), with what the hub adds: the entry fee, the claiming price, the going if it is known
function view(S, h, r) { useLuck(); const v = R.view(h, raceOf(S, r)); return Object.assign({}, v, { key: v.lv, chip: v.label, fee: entryFee(r), claim: isClaim(r) ? claimPrice(r) : 0, going: goingOf(S, r) }); }
// Sellers and claimers: every runner is for sale at the race's set price. A horse too good for the race wins it and
// is very likely bought by another stable.
function standard(r) { if (hcapLike(r)) return { hi: r.top }; const m = /(\d+)\D+(\d+)/.exec(r.ratings); if (m) return { hi: +m[2] }; return { hi: ({ 1: 100, 2: 92, 3: 86, 4: 80, 5: 74, 6: 66 }[r.cls] || 74) - (r.ages === "2yo" ? 6 : 0) }; }
const isClaim = (r) => r.type === "Claimer" || r.type === "Seller";
const claimPrice = (r) => Math.round(5000 * Math.exp((standard(r).hi - 4 - 60) / 13) / 500) * 500;
const entryFee = (r) => Math.max(30, Math.round(r.prize * 0.01 / 10) * 10);
const weekRaces = (w) => MEETS_OF[w - 1].flatMap((m) => m.races);
// the races a horse could run in over the coming weeks: soonest first, and in each week the best chance first, with
// sellers and claimers (where the horse can be lost) last
function options(S, h, weeksAhead) {
  use(S); const out = []; if (h.inj > 0) return out;
  for (let k = 0; k <= (weeksAhead || 0); k++) { const w = S.week + k; if (w > NW) break;
    for (const r of weekRaces(w)) if (!barred(S, h, r) && R.eligible(h, raceOf(S, r))) out.push({ r, v: view(S, h, r) }); }
  const sc = (v) => v.win + v.pl * 0.05;
  return out.sort((a, b) => a.r.m.week - b.r.m.week || (a.v.claim ? 1 : 0) - (b.v.claim ? 1 : 0) || sc(b.v) - sc(a.v) || b.r.prize - a.r.prize);
}
function enter(S, hid, rid) {
  const h = horse(S, hid), r = RACES[rid]; if (!h || !r) return "No such race";
  if (r.m.week < S.week) return "That race has been run";
  const why = whyNot(S, h, r); if (why) return why;
  const other = S.horses.find((x) => x !== h && x.entries[r.m.week] === rid); if (other) return `${other.n} already runs for you in this race`;   // (one runner a race, for now)
  if (h.entries[r.m.week] != null) withdraw(S, hid, r.m.week);
  h.entries[r.m.week] = rid; pay(S, "Entry fees", `${h.n}: ${r.name}, ${r.m.course}`, -entryFee(r), h.id); return null;
}
function withdraw(S, hid, week) {
  const h = horse(S, hid), rid = h && h.entries[week]; if (rid == null) return;
  delete h.entries[week]; pay(S, "Entry fees", `${h.n} withdrawn: ${RACES[rid].name} (fee back)`, entryFee(RACES[rid]), h.id);
}
// "Trainer's picks": every fresh horse without a race this week goes where the trainer would send it (the rules'
// autoPick), from the races the hub allows: never a seller or claimer with a horse worth more than the race's price
function trainerPicks(S) {
  use(S); const made = [];
  for (const h of S.horses) {
    if (h.inj > 0 || h.fresh < 75 || h.entries[S.week] != null) continue;
    const worth = R.valueOf(h), list = weekRaces(S.week).filter((r) => !barred(S, h, r) && entryFee(r) <= Math.max(300, S.cash * 0.02) && !(isClaim(r) && worth > claimPrice(r) * 1.15) && !S.horses.some((y) => y !== h && y.entries[S.week] === r.id));
    useLuck(); const p = R.autoPick(h, list.map((r) => raceOf(S, r))); if (!p) continue;
    const r = RACES[p.id]; if (!enter(S, h.id, r.id)) made.push({ h, r, v: view(S, h, r) });
  }
  return made;
}

// ---------------------------------------------------------------- the race engine: every race as the 3D race view runs it
// When the engine has loaded (window.ENGINE: the race view's own engine and course files, loaded by career.html, and
// by the robot test in Node), it runs each race: the rules hand it every runner's figure on the day, it runs the race
// with its own pace, traffic and luck, and the rules settle on its result. The 3D view is then sent exactly the same
// race (the course, the start, the going, the seed and the runners), so the race watched is the race recorded.
// Without the engine (it failed to load), the rules' own roll decides, as before.
const ENG = () => (root.ENGINE && root.ENGINE.courses && root.ENGINE.runRace ? root.ENGINE : null);
// the race engine has more luck in it than the rules' own roll, so the trainer's chances allow for more (see TBRULES.luck)
const ENGINE_LUCK = +(root.ENGINE_LUCK || 1.35);
const useLuck = () => R.luck(ENG() ? ENGINE_LUCK : 1);
// The course each meeting races on in 3D: its own when it has been built (Ascot, York, Newmarket's Rowley Mile and the
// July Course so far), else its stand-in from the calendar (data.js -> courses -> standin, followed until a built one
// turns up: Goodwood runs at Ascot, Epsom at York, Kempton at Sandown and so on to Ascot), else Ascot.
function engineCourse(m) {
  const E = ENG(); if (!E) return null; const have = (k) => !!E.courses[k];
  let co = m.course;
  for (let i = 0; i < 8 && co; i++) {
    if (co === "Newmarket") { const k = m.date.slice(5) >= "06-20" && m.date.slice(5) <= "08-31" ? "newmarket-july" : "newmarket"; if (have(k)) return k; }
    const k = co.toLowerCase().replace(/[^a-z]+/g, "-"); if (have(k)) return k;
    co = D.courses[co] && D.courses[co].standin;
  }
  return have("ascot") ? "ascot" : Object.keys(E.courses)[0];
}
// the course's start nearest the race's trip (the straight course for a race on the straight, where there is one)
function engineStart(k, r) {
  const V = ENG().courses[k].view.races, want = r.f * 201.168; let best = null, bd = 1e9;
  for (const [key, v] of Object.entries(V)) { if (key.startsWith("_") || key === "long" || key === "mile" && V["1m"]) continue;
    const d = Math.abs(v.distance - want) + ((v.course === "straight") === !!r.straight ? 0 : 60); if (d < bd) { bd = d; best = key; } }
  return best;
}
const STYLE3D = { F: "front", P: "prominent", M: "midfield", H: "holdup" };
const PACE3D = { slow: "slow", even: "even", strong: "fast", fast: "fast" };
// The engine's race for a calendar race, and its decider for the rules. Returns null when the engine can't run it.
function engineFor(S, r, race) {
  const E = ENG(), k = E && engineCourse(r.m); if (!k) return null;
  const C = E.courses[k], key = engineStart(k, r), V = C.view.races[key], H = C.data.settings.horse;
  if (race.field.length + 1 > C.data.stalls.maxRunners) return null;
  const f = V.distance / 201.168; let rung = 0; H.TRIP_LADDER_FURLONGS.forEach((x, i) => { if (Math.abs(x - f) < Math.abs(H.TRIP_LADDER_FURLONGS[rung] - f)) rung = i; });
  const going = r.m.aw ? "Good" : (goingOf(S, r) || "Good"), hc = race.cap != null;
  const spec = { file: k, key, label: V.label, going, handicap: hc, seed: Math.floor(R.rnd() * 2147483647), draw: null, runners: null, events: null };
  return { spec, decide(run) {
    // the draw: stalls in a seeded random order (spec.draw[stall] = the runner's place in `run`)
    const draw = run.map((x, i) => i); for (let i = draw.length - 1; i > 0; i--) { const j = Math.floor(R.rnd() * (i + 1)); [draw[i], draw[j]] = [draw[j], draw[i]]; }
    const card = draw.map((i) => { const x = run[i], o = { name: x.n, rating: Math.round(x.mean * 10) / 10, style: STYLE3D[x.st] || "midfield", flex: "adaptable",
      temperament: x.you && horse(S, x.hid).temp === "hot" ? "keen" : "calm", trip: [H.TRIP_LADDER[rung], H.TRIP_LADDER[rung]] }; if (hc) o.mark = x.or; return o; });
    const { result } = E.runRace({ course: V.course, distance: V.distance, start: V.start, going, seed: spec.seed, handicap: hc }, card, C.data, { timeline: false });
    const out = run.map(() => null); for (const p of result.placed) out[draw[p.runner]] = { pos: p.place, btn: p.behind, form: p.form };
    spec.draw = draw; spec.runners = card; spec.events = result.events.filter((e) => run[draw[e.runner]] && run[draw[e.runner]].you).map((e) => ({ kind: e.kind, toGo: e.toGo, lengths: e.lengths }));
    return { pace: PACE3D[result.pace.run] || "even", out };
  } };
}
// what the 3D race showed about your runner, in the trainer's words (added to his debrief)
function eventWords(h, evs) {
  const He = h.sex === "f" ? "She" : "He", out = [];
  for (const e of evs || []) {
    if (e.kind === "missed the break") out.push(`${He} missed the break.`);
    if (e.kind === "short of room" && e.lengths >= 1) out.push(`${He} was short of room ${e.toGo >= 201 ? Math.round(e.toGo / 201.168) + "f" : "a furlong"} out and lost about ${Math.round(e.lengths)} length${Math.round(e.lengths) === 1 ? "" : "s"}.`);
  }
  return out.join(" ");
}

// ---------------------------------------------------------------- race day
function runners(S) { return S.horses.filter((h) => h.entries[S.week] != null).map((h) => ({ h, r: RACES[h.entries[S.week]] })).sort((a, b) => (a.r.m.date + a.r.time).localeCompare(b.r.m.date + b.r.time)); }
// "Go racing": every race with a runner of yours is run by the rules there and then, and all of it is kept in the save
// (S.rd), so the screens can show the races one at a time and a reload can't run one again. The week has not moved on
// yet: endWeek does that, once the day has been watched.
function goRacing(S) {
  use(S); const run = runners(S), rd = { yr: S.yr, week: S.week, i: 0, cash0: S.cash, rep0: S.rep, res: [] };
  for (const { h, r } of run) {
    delete h.entries[S.week];
    const why = whyNot(S, h, r); if (why) { pay(S, "Entry fees", `${h.n} could not run: ${r.name} (fee back)`, entryFee(r), h.id); continue; }
    const n0 = S.ledger.length, what = `${r.name}, ${r.m.course}`;
    useLuck(); const race = raceOf(S, r), eng = engineFor(S, r, race);
    const res = R.runRace(race, [h], eng ? { decide: eng.decide } : undefined), m = res.mine[0];
    if (eng) { res.view = eng.spec; const w = eventWords(h, eng.spec.events); if (w && !m.inj) m.say += " " + w; }
    for (let i = n0; i < S.ledger.length; i++) if (S.ledger[i].cat === "Prize money") S.ledger[i].text = `${h.n}: ${m.pos === 1 ? "won" : ORD[m.pos] + " in"} the ${what}`;
    // reputation by the hub's own table (the rules have just given theirs: swap it)
    const base = REP[r.type] || REPCLS[r.cls] || 2, rep = m.pos === 1 ? base : m.pos === 2 ? Math.round(base * 0.4) : m.pos === 3 ? Math.round(base * 0.2) : 0;
    S.rep += rep - m.rep; S.ss.rep += rep - m.rep; m.rep = rep;
    S.year.runs++; S.stats.runs++; if (r.m.aw) h.aw++;
    if (m.pos === 1) { S.year.wins++; S.stats.wins++; } else if (m.pos <= 3) S.year.places++;
    if (m.pos === 1 && REP[r.type]) S.trophies.unshift({ s: S.yr, w: S.week, race: r.name, course: r.m.course, type: r.type, horse: h.n, prize: m.prize });
    const hub = res.hub = { rid: r.id, hid: h.id, name: h.n, going: r.m.aw ? "Standard" : goingOf(S, r) }, first = res.run[0];
    if (!first.you) { const o = S.rivals[first.s]; if (o) { o.pts += Math.round(base * 0.5); hub.winner = { horse: first.n, owner: o.name, pic: o.pic }; } }
    if (m.inj) news(S, "vet", `${h.n} is on the easy list`, m.say, "stables");
    // a seller's winner goes to auction, and any claimer runner can be claimed: a horse worth more than the price usually goes
    if (isClaim(r) && (r.type === "Claimer" || m.pos === 1)) { const cp = claimPrice(r), v = R.valueOf(h);
      if (rnd(S) < clamp(0.1 + (v / cp - 0.8) * 0.9, 0.04, 0.95)) { const to = pick(S, S.rivals.filter((x) => x.tier >= 3)).name;
        for (const w of Object.keys(h.entries)) withdraw(S, h.id, +w);
        S.horses = S.horses.filter((x) => x !== h); pay(S, "Horses sold", `${h.n} ${r.type === "Seller" ? "sold at the auction after the seller" : "claimed"} (${to})`, cp);
        hub.claimed = cp; hub.to = to; hub.how = r.type === "Seller" ? `Sold at the auction afterwards to ${to} for ${money(cp)}.` : `Claimed out of the race by ${to} for ${money(cp)}.`;
        news(S, "sale", `${h.n} has left the yard`, hub.how + " In sellers and claimers every runner is for sale at the set price.", "stables"); } }
    rd.res.push(res);
  }
  S.rd = rd.res.length ? rd : null; return S.rd;
}

// ---------------------------------------------------------------- gallops, the sales, selling, the stud
// one gallop a horse a week, from the week's allowance: 'work' (learn about it), 'school' (teach it) or 'easy' (freshen it)
function gallop(S, hid, kind) {
  use(S); const h = horse(S, hid); if (!h || h.galloped || h.inj > 0 || S.gallops >= R.T().gal) return null;
  const out = R.gallop(h, kind); if (!out) return null;
  S.gallops++; h.galloped = true; return { h, text: out.text.replace("An easy fortnight", "An easy week"), rev: out.rev };
}
const boxesFree = (S) => { use(S); return R.boxesFree(); };
const paddocksFree = (S) => { use(S); return R.T().pad - S.mares.length; };
const youngRoom = (S) => { use(S); return R.T().pad * 2 + 2 - S.young.length; };
const lotOf = (S, id) => S.sale && S.sale.lots.find((l) => l.id === id);
const lotName = (l) => (l.m ? l.m.n : l.h.n);
// A bid at the sales (the rules' auction: a rival may bid again). Horses to race need a box; yearlings and foals go
// to the stud until they are two, so they need room there instead.
function bid(S, lotId) {
  use(S); const l = lotOf(S, lotId); if (!l || l.done) return null;
  const toStud = l.kind === "yearling" || l.kind === "foal"; if (toStud && youngRoom(S) <= 0) return "full";
  const yard = S.horses; if (toStud) S.horses = [];              // (so the rules' "is there a box?" does not apply to one bound for the stud)
  let r; try { r = noted({ cat: "Horses bought", text: `${lotName(l)}${l.m ? ", a broodmare" : l.h.age ? `, ${l.h.age}yo ${SEXN[l.h.sex]} by ${l.h.sire}` : `, a foal by ${l.h.sire}`} (${S.sale.name})`, hid: l.h ? l.h.id : 0 }, () => R.bid(l)); }
  finally { if (toStud) { const got = S.horses; S.horses = yard; S.young.push(...got); } }
  if (r === "won" && l.h) { extras(S, l.h, { fromSale: l.kind !== "hit" }); if (toStud) l.h.stage = l.kind; }
  return r;
}
function pass(S, lotId) { use(S); const l = lotOf(S, lotId); if (l) R.pass(l); }
const valueOf = (S, h) => { use(S); return R.valueOf(h); };
const youngValue = (S, y) => { use(S); return R.nice(R.yearlingValue(y) * (y.stage === "foal" ? 0.6 : 1)); };
function sell(S, hid) {
  use(S); const h = horse(S, hid);
  if (h) { for (const w of Object.keys(h.entries)) withdraw(S, hid, +w); return noted({ text: `${h.n} sold` }, () => R.sell(hid)); }
  const j = S.young.findIndex((y) => y.id === hid); if (j < 0) return 0;
  const y = S.young[j], v = youngValue(S, y); S.young.splice(j, 1); pay(S, "Horses sold", `${y.n} sold from the stud`, v); return v;
}
// a filly to your paddocks; a colt who has won a Group race to stand as a stallion (a payment, and free covers for your mares)
function retire(S, hid) {
  use(S); const h = horse(S, hid); if (!h) return false;
  const ent = Object.keys(h.entries); if (!R.retire(hid)) return false;
  for (const w of ent) pay(S, "Entry fees", `${h.n} withdrawn: ${RACES[h.entries[w]].name} (fee back)`, entryFee(RACES[h.entries[w]]));
  if (h.sex === "f") { const m = S.mares[S.mares.length - 1]; m.inFoal = null; news(S, "stud", `${h.n} retires to the stud`, `She joins your broodmares as a ${m.stars}-star mare.`, "stud"); }
  else news(S, "stud", `${h.n} retires to stand as a stallion`, "He covers your own mares free for the next eight seasons.", "stud");
  return true;
}
// the covering season: late winter to the end of May. The foal arrives the next spring, is a yearling the January after and comes into training at two.
const coveringOpen = (S) => S.week <= 10 || S.week >= 37;
function cover(S, mid, sireName) {
  use(S); const m = S.mares.find((x) => x.id === mid), s = R.sireOf(sireName); if (!m || !s) return "No such mating";
  if (m.inFoal) return "Already in foal"; if (!coveringOpen(S)) return "The covering season is over";
  if (!R.sires().includes(s)) return "His book is closed to you for now";
  if (!noted({ cat: "Stud fees", text: `${m.n} covered by ${s.n}` }, () => R.setCover(mid, s.n))) return "Not enough in the bank";
  m.cover = null; m.inFoal = { sire: s.n, due: S.yr + (S.week >= 37 ? 2 : 1) }; return null;   // (kept out of the rules' own new-year foaling: the hub foals its mares in the spring)
}
function moveToYard(S, hid) { use(S); const j = S.young.findIndex((h) => h.id === hid); if (j < 0 || R.boxesFree() <= 0) return false; const h = S.young.splice(j, 1)[0]; delete h.stage; h.fresh = 100; h.joined = [S.yr, S.week]; S.horses.push(h); return true; }

// ---------------------------------------------------------------- what needs doing, and moving on a week
function weeklyCost(S) {
  const k = isWinter(S.week) ? (S.week === 38 ? 3 : 4) : 1;
  const rows = [["Training fees", S.horses.length, COST.training], ["Broodmares' keep", S.mares.length, COST.mare], ["Foals and yearlings", S.young.length, COST.young]].filter((r) => r[1]);
  return { weeks: k, rows: rows.map(([t, n, each]) => ({ t, n, each, amt: n * each })), perWeek: rows.reduce((a, r) => a + r[1] * r[2], 0) };
}
function todos(S) {
  use(S); const t = [], T = R.T();
  if (S.cash < 0) t.push({ k: "bank", go: "palace", text: "The bank is overdrawn", sub: "Sell a horse or win a race: you can't bid until it's cleared." });
  const idle = S.horses.filter((h) => !h.inj && h.fresh >= 75 && h.entries[S.week] == null && options(S, h, 0).some((o) => o.v.lv >= 2 || h.or == null));
  if (idle.length) t.push({ k: "enter", go: "stables", n: idle.length, text: idle.length === 1 ? `Find a race for ${idle[0].n}` : `${idle.length} horses are ready to run`, sub: "Fresh, with races to suit this week." });
  if (S.sale) { const left = S.sale.lots.filter((l) => !l.done).length; if (left && !S.saleSeen) t.push({ k: "sale", go: "tatts", n: left, text: S.sale.name, sub: `${left} lots at Tattersalls this week.` }); }
  const gl = T.gal - S.gallops; if (gl > 0 && S.horses.some((h) => !h.galloped && !h.inj && (h.k.pw > 8 || h.craft < 2))) t.push({ k: "gallop", go: "warren", n: gl, text: `${gl} gallop${gl > 1 ? "s" : ""} to use`, sub: "Work a horse on Warren Hill to learn more about it." });
  const empty = S.mares.filter((m) => !m.inFoal); if (empty.length && coveringOpen(S)) t.push({ k: "cover", go: "stud", n: empty.length, text: empty.length === 1 ? `Choose a stallion for ${empty[0].n}` : `${empty.length} mares to cover`, sub: "The covering season closes at the end of May." });
  const wait = S.young.filter((h) => h.stage === "ready"); if (wait.length) t.push({ k: "box", go: "stud", n: wait.length, text: `${wait[0].n} is ready for the yard`, sub: R.boxesFree() > 0 ? "A two-year-old waiting at the stud: move it into a box." : "No box free: sell a horse, or sell the youngster." });
  return t;
}
// The week ends: the keep is paid, the horses rest, and the calendar moves on. Returns the week's report for the screen.
function endWeek(S) {
  use(S); const rd = S.rd, rep = { yr: S.yr, week: S.week, results: [], costs: null, events: [], tierBefore: R.tier(), cashBefore: rd ? rd.cash0 : S.cash };
  if (rd) for (const x of rd.res) { const m = x.mine[0], me = x.run.find((y) => y.you);
    rep.results.push({ hid: m.hid, name: x.hub.name, rid: x.hub.rid, pos: m.pos, n: x.run.length, going: x.hub.going, prize: m.prize, gap: m.pos === 1 ? (x.run[1] ? x.run[1].btn : 9) : me.btn, orOld: m.orOld, orNew: m.orNew,
      rev: m.rev, say: x.hub.how || m.say, rep: m.rep, winner: x.hub.winner || null, claimed: x.hub.claimed || 0 }); }
  S.rd = null;
  const c = weeklyCost(S); rep.costs = c;
  for (const row of c.rows) pay(S, row.t, `${row.n} × ${money(row.each)} a week${c.weeks > 1 ? ` × ${c.weeks} weeks` : ""}`, -row.amt * c.weeks);
  for (const h of S.horses) h.kept += COST.training * c.weeks;
  J.endWeek(S, c.weeks);                                         // rest: freshness comes back, injuries heal
  for (const x of S.rivals) x.pts += Math.round(rnd(S) * [0, 9, 4.5, 2, 0.8][x.tier] * c.weeks);
  // The safety net (the design map's open question; this is the prototype's answer): more than £25,000 overdrawn and the
  // bank sells for you, youngest stock first; with nothing left to sell, a new backer puts in £20,000
  while (S.cash < -25000) {
    const y = S.young[0], m = !y && S.mares.slice().sort((a, b) => a.stars - b.stars)[0], h = !y && !m && S.horses.slice().sort((a, b) => R.valueOf(a) - R.valueOf(b))[0];
    if (y || h) { const x = y || h, v = sell(S, x.id); rep.events.push({ kind: "bank", text: `The bank has sold ${x.n} for ${money(v)} to cover the overdraft.` }); news(S, "bank", `The bank has sold ${x.n}`, `More than £25,000 overdrawn: ${money(v)} raised.`, "palace"); }
    else if (m) { const v = R.nice([0, 6, 15, 35, 80, 160][m.stars] * 600); S.mares.splice(S.mares.indexOf(m), 1); pay(S, "Horses sold", `${m.n} sold by the bank`, v);
      rep.events.push({ kind: "bank", text: `The bank has sold the mare ${m.n} for ${money(v)} to cover the overdraft.` }); news(S, "bank", `The bank has sold ${m.n}`, `More than £25,000 overdrawn: ${money(v)} raised.`, "palace"); }
    else { pay(S, "A new backer", "A new backer clears the overdraft and puts in £20,000", 20000 - S.cash); rep.events.push({ kind: "bank", text: "With nothing left to sell, a new backer has cleared the overdraft and put in £20,000. Start again at Tattersalls." });
      news(S, "bank", "A new backer", "The overdraft is cleared and there is £20,000 in the bank. The sales are the place to start again.", "tatts"); }
  }
  // on a week
  const was = S.week;
  if (S.week === NW) { rep.review = seasonReview(S); S.week = 1; S.yr++; S.cards = {}; S.year = { in: {}, out: {}, runs: 0, wins: 0, places: 0, start: S.cash }; S.goals = makeGoals(S); for (const h of S.horses) h.entries = {};
    const sp = 4000 + 4000 * R.tier(); pay(S, "Sponsor", `Your sponsor's cheque for the new season (${R.T().n})`, sp); rep.events.push({ kind: "bank", text: `A new season: your sponsor's cheque for ${money(sp)} has arrived.` }); S.year.start = S.cash - sp; }
  else S.week++;
  if (S.week === 36) newYear(S, rep);
  if (S.week === 3) for (const h of S.horses) h.aw = 0;
  // the stud: foals arrive in the spring
  if (S.week <= 8) for (const m of S.mares) if (m.inFoal && m.inFoal.due <= S.yr && rnd(S) < 0.3 + S.week * 0.09) {
    const f = bornTo(S, m.inFoal.sire, m, 0); m.inFoal = null; m.foals = (m.foals || 0) + 1; S.young.push(f);
    rep.events.push({ kind: "foal", text: `${m.n} has foaled a ${SEXN[f.sex]} by ${f.sire}.` }); news(S, "stud", `A ${SEXN[f.sex]} foal for ${m.n}`, `By ${f.sire}. ${coveringOpen(S) ? "She can be covered again this spring." : ""}`, "stud"); }
  startWeek(S);
  const t = R.tier(); if (t > rep.tierBefore) { rep.tierUp = t; news(S, "rep", `You are now a ${TIERS[t].n}`, `${TIERS[t].boxes} boxes in the yard, ${TIERS[t].pad} paddocks at the stud, ${TIERS[t].gal} gallops a week, and better stallions and sale lots.`, "palace"); }
  rep.cashAfter = S.cash; rep.from = was; S.last = rep; return rep;
}
// go racing and move on, in one step (the robot careers use this; the screens show race day in between)
function advance(S) { goRacing(S); return endWeek(S); }
// 1 January: the rules age every horse and bring on a new crop of rival stars; the hub moves its young stock up a year
function newYear(S, rep) {
  const before = S.mares.slice(); R.newYear();
  for (const m of before) if (!S.mares.includes(m)) { rep.events.push({ kind: "stud", text: `${m.n} has been retired from the paddocks at ${m.age}.` }); news(S, "stud", `${m.n} is retired`, `At ${m.age} her breeding days are over. A paddock is free.`, "stud"); }
  for (const y of S.young) { y.age++; y.stage = y.age >= 2 ? "ready" : "yearling"; }
  for (const y of S.young.filter((x) => x.stage === "ready")) if (R.boxesFree() > 0) { moveToYard(S, y.id); rep.events.push({ kind: "yard", text: `${y.n}, now two, has come into the yard from the stud.` }); }
  rep.events.push({ kind: "year", text: "1 January: every horse is a year older." });
  news(S, "note", "New Year: every horse a year older", "Yearlings are now two-year-olds and can come into training. The turf season starts in late March.", "stables");
}
function seasonReview(S) {
  const sum = (o) => Object.values(o).reduce((a, b) => a + b, 0);
  return { season: S.yr, runs: S.year.runs, wins: S.year.wins, places: S.year.places, in: sum(S.year.in), out: sum(S.year.out), prize: S.year.in["Prize money"] || 0,
    goals: S.goals.map((g) => ({ text: g.text, done: goalState(S, g).done })), tier: tierOf(S), trophies: S.trophies.filter((t) => t.s === S.yr) };
}
// the owners' table: you among the rival stables
function table(S) { return [...S.rivals.map((r) => ({ name: r.name, pts: r.pts, tier: r.tier, pic: r.pic })), { name: S.stable, pts: S.rep, you: true }].sort((a, b) => b.pts - a.pts); }

root.CAREER = { use, isClaim, claimPrice, TIERS, TRIPN, GOINGS, CHIPS, COST, SALES, MEET, RACES, WEEKS, NW, MEETS_OF, weekInfo, isWinter, fmtDay, fmtSpan, yearOf, dateOf, money, newGame, tierOf, horse,
  barred, whyNot, raceOf, goingOf, view, options, entryFee, weekRaces, enter, withdraw, trainerPicks, runners, goRacing, endWeek, advance, gallop, boxesFree, paddocksFree, youngRoom, bid, pass, sell, valueOf, youngValue, retire,
  coveringOpen, cover, weeklyCost, todos, moveToYard, table, goalState, sexWord, rnd };
})(typeof window !== "undefined" ? window : globalThis);
