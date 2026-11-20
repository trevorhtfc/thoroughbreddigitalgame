// =====================================================================================================================
// The join between the career hub (weekly turns on the real calendar: js/career/data.js and core.js) and the rules
// (rules.js). Nothing in the hub has to change shape for the rules to work: this file turns the hub's stallions,
// mares, rival owners and races into what the rules expect, and keeps the rules' two clocks in step with the hub's week.
//
// Load order: js/career/data.js, rules/rules.js, rules/hub-adapter.js, then the hub's own core and screens.
// Once, at start-up:        TBJOIN.setup(window.CAREER_DATA)
// New game / loading:       TBRULES.init(S.eng = S.eng || {}, seed)   (or init(S) to keep everything in one object)
// As a week begins:         TBJOIN.startWeek(E, week)
// For any race on offer:    const race = TBJOIN.raceFor(E, hubRace, goingName)   -> hand to TBRULES.eligible / view / runRace
// As a week ends:           TBJOIN.endWeek(E, weeks)                             (weeks = 4 for a month-long winter turn)
// On 1 January:             TBRULES.newYear()
// tools/test-hub-join.js plays whole careers this way on the real 2,836-race calendar.
// =====================================================================================================================
(function (root) {
'use strict';
const R = root.TBRULES;
const TRIP = { '5f': 0, '6f': 1, '7f': 2, '1m': 3, '1m2f': 4, '1m4f': 5, '1m6f': 6, '2m+': 7 }, GO = { Heavy: 0, Softer: 1, Good: 2, Quicker: 3, Quick: 4 };
const AGES = { '2yo': [2, 2], '3yo': [3, 3], '2yo+': [2, 99], '3yo+': [3, 99], '4yo+': [4, 99] };
const TYPES = { 'Group 1': 'G1', 'Group 2': 'G2', 'Group 3': 'G3', 'Listed': 'L', 'Heritage handicap': 'HH', 'Conditions': 'C', 'Sales race': 'C', 'Seller': 'S', 'Claimer': 'S', 'Maiden': 'M', 'Novice': 'N' };
const TURF_WEEKS = 33;

// The hub's data, in the rules' shape. A rival runner's `s` is then an index into CAREER_DATA.rivals (its owner and colours).
function setup(D) {
  const prof = s => { const g = s.ground.map(x => GO[x]).filter(x => x != null); return { n: s.name, stars: s.stars, opt: Math.min(6, TRIP[s.opt] == null ? 3 : TRIP[s.opt]), peak: { '2YO': 'e', '3YO': 'n', '4YO': 'l' }[s.peak] || 'n', gr: g.length ? [Math.min(...g), Math.max(...g)] : [2, 3], fee: s.fee || 0 }; };
  R.setData({ stallions: D.stallions.map(prof), mares: D.mares.map(prof), NA: D.nameA, NB: D.nameB, silks: D.rivals.map(r => ({ t: +r.tier || 3 })) });
  R.CFG.tpf = 2;                                  // weekly turns: two to the fortnight (freshness, injuries and the "goes well fresh" gap all follow)
}
// how far through the turf season a week is (the rules' E.prog): 0 in week 1, 1 in week 33 and through the winter
const progOf = week => week <= TURF_WEEKS ? (week - 1) / (TURF_WEEKS - 1) : 1;
// the rules' class for a hub race. Handicaps, nurseries and classified races go by their class number, with the ceiling taken from the band.
function clsOf(r) { if (TYPES[r.type]) return r.type === 'Maiden' && /^(Restricted|Auction)/.test(r.name) ? 'MA' : TYPES[r.type]; return 'C' + Math.min(6, Math.max(2, r.cls)); }
// The rules' copy of a hub race, with its field of rivals. It is made the first time anyone looks at the race and kept in E.cards
// (so it is in the save), which means the racecard a player studies is the race that is run. goingName: the hub's going for the
// meeting ("Good"), or null/undefined if it has not been declared yet.
function raceFor(E, r, goingName) {
  const cards = E.cards || (E.cards = {}); let c = cards[r.id];
  if (!c || c.s !== E.season) {
    const hc = r.hcap || r.type === 'Classified', keep = E.prog; E.prog = progOf(r.m.week); R.use(E);
    c = cards[r.id] = R.prepRace({ id: r.id, s: E.season, wk: r.m.week, n: r.name, co: r.m.course, cls: clsOf(r), f: r.f, a: AGES[r.ages] || [3, 99], sx: r.sex === 'F' ? 'F' : r.sex === 'C' ? 'C' : '', nog: r.sex === 'CF',
      p: r.prize / 1000, big: !!r.big, cap: hc && r.top ? r.top : undefined, nrun: r.lo ? [Math.max(4, Math.min(18, r.lo) - 1), Math.max(5, Math.min(19, r.hi) - 1)] : undefined });
    E.prog = keep;
  }
  c.g = r.m.aw ? null : goingName == null ? undefined : GO[goingName];
  return c;
}
function startWeek(E, week) { R.use(E); E.prog = progOf(week); for (const id in E.cards || {}) if (E.cards[id].s !== E.season || E.cards[id].wk < week) delete E.cards[id]; }
function endWeek(E, weeks) { R.use(E); for (let i = 0; i < (weeks || 1); i++) R.rest(); E.clock += weeks || 1; }

const J = { setup, progOf, clsOf, raceFor, startWeek, endWeek, TYPES, AGES };
root.TBJOIN = J; if (typeof module !== 'undefined') module.exports = J;
})(typeof window !== 'undefined' ? window : globalThis);
