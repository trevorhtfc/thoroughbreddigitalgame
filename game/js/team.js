// =====================================================================================================================
// Thoroughbred: your team. Owner, trainer and jockey cards, drafted at the Jockey Club before the stud opens (owner,
// 10 Nov: "integrate owner, jockey and trainers into your team, which you draft at the start ... a draft from bronze,
// silver and gold decks of each type, 6 points: gold is 3, silver 2, bronze 1").
//
// The cards are the board game's (the CMS collection TeamCards on the Thoroughbred site, 60 cards), turned into the
// digital game's terms where the board's rules can't work as they are (no other players at the stud, no card hands in
// the race). The trainer cards are the board's almost word for word. Rules only, no screens (those are in js/ui-team.js).
//
// The draft: pick a deck (Owner, Trainer or Jockey; Bronze, Silver or Gold), three of its cards are turned over and you
// keep one, as at the mares sale. Spend exactly 6 points (Gold 3, Silver 2, Bronze 1), with at least one card of each
// kind, as on the board.
// =====================================================================================================================
const TEAM_POINTS = 6, TEAM_OFFER = 3;
const TEAM_ROLES = ["Owner", "Trainer", "Jockey"];
const TIER_NAME = ["", "Bronze", "Silver", "Gold"], TIER_NUM = ["", "I", "II", "III"];

// ---------- the numbers (easy to change after playtesting) ----------
// Owner cards (owner, 10 Nov, second round): each pushes you towards breeding or the sales. No card pays income
// ("too computer sim luck based"); the mares sale turns over 2 mares for everyone.
const POWERHOUSE = [0, 150000, 300000, 450000];          // added to the budget (to be levelled against the others)
const ELITE_SEE = [2, 3, 4, 5];                          // mares turned over at the mares sale: 2 for everyone, more with Elite Mares
const OWNED_STARS = [0, 3, 4, 5], OWNED_DRAW = 3, OWNED_FREE = 2;   // Stallion Owner: three of these stars drawn, keep one, two free nominations
const PEDIGREE_LOOKS = [0, 2, 4, 99];                    // Pedigree Expert: unproven stallions whose true stars you learn
// Sales Scout (owner, 11 Nov: in place of Trade Terms, "refining the books": pick the races you still need horses for,
// the game works out which lots won't be useful, and special lots primed for those races)
const SCOUT_RACES = [0, 2, 3, 4];                        // races you brief him for
const SCOUT_LOTS = [0, 1, 2, 4];                         // his own finds added to the catalogue, each bred for one of them
const AGENT_BAND = [0, 15, 10, 5];                       // Bloodstock Agent: his projection is within this many points either way
const VET_USES = [0, 1, 2, 3], VET_REFUND = [0, 0.8, 0.9, 1];   // Vet's Report: send a yearling back once you've seen it
const PRIVATE_BOOKS = [null, [3], [2, 3], [1, 2, 3]];    // Private Sale: one lot before the ring, at the middle of its guide
const JOCKEY_RIDES = [0, 3, 4, 5];                       // how many of your races he can ride
const JOCKEY_LEVEL = [0, 3, 4, 5];                       // his skill in the race engine (1 to 5); your own yard's is random
// What each jockey card does in the race engine, by tier (race-engine/engine.js: formBest, noFlop, paceTank, lateKick,
// reader). Measured with race-engine/check/team-jockeys.mjs against rating points: see game/README.md, "Your team".
// For a horse 2 below the best in a field of 14, in rating points: Champion II (best of two runs, no stinker) about +2,
// III (best of three) about +3; Tempo Setter about +1.5 / +2.5 / +3.5 and Late Closer about +1.5 / +2.5 / +3.5 when
// the horse is ridden the way they like (+0 otherwise); Race Reader about +1 / +1.5 / +2.5 whatever the style.
const JOCKEY_EDGE = {
  champion: [null, { formBest: 2 }, { noFlop: true, formBest: 2 }, { noFlop: true, formBest: 3 }],
  tempo:    [null, { paceTank: 0.03 }, { paceTank: 0.055 }, { paceTank: 0.08 }],
  closer:   [null, { lateKick: 0.008 }, { lateKick: 0.013 }, { lateKick: 0.019 }],
  reader:   [null, { reader: 0.5, paceTank: 0.02, lateKick: 0.005 }, { reader: 0.75, paceTank: 0.035, lateKick: 0.008 }, { reader: 1, paceTank: 0.05, lateKick: 0.012 }],
};

// ---------- the cards ----------
// Owner: 6 kinds × 3 tiers. Trainer: the board's 10 kinds × 3 tiers. Jockey: the board's 4 kinds × 3 tiers.
const OWNER_KINDS = {
  powerhouse: { title: "Powerhouse", leans: "Either", when: "At once", text: t => `${money(POWERHOUSE[t])} more to spend on mares, stud fees and yearlings.` },
  elite: { title: "Elite Mares", leans: "Breeding", when: "The National Stud", text: t => `At the mares sale you see ${ELITE_SEE[t]} mares from the pile instead of 2, and keep the one you want.` },
  stallion: { title: "Stallion Owner", leans: "Breeding", when: "The National Stud", text: t => `Three ${OWNED_STARS[t]}★ stallions are drawn at the stud: keep one as your own, with ${OWNED_FREE} free nominations to him.` },
  pedigree: { title: "Pedigree Expert", leans: "Breeding", when: "The stud and the sales", text: t => `An unproven stallion may be a star better or worse than the stud book says. Your expert tells you the truth about ${t === 3 ? "every one of them" : PEDIGREE_LOOKS[t] + " of them"}.` },
  scout: { title: "Sales Scout", leans: "The sales", when: "Tattersalls", text: t => `Tell him the ${SCOUT_RACES[t]} races you still need a horse for. He marks the lots bred to suit them, greys out the rest, and finds ${SCOUT_LOTS[t] === 1 ? "a bargain" : SCOUT_LOTS[t] + " bargains"} of his own: cheaper lots whose yearlings are good enough for them.` },
  agent: { title: "Bloodstock Agent", leans: "The sales", when: "Tattersalls", text: t => `His projection of every yearling's peak rating, to within ${AGENT_BAND[t]} points either way: the true figure is somewhere in his range.` },
  vet: { title: "Vet's Report", leans: "The sales", when: "Tattersalls", text: t => `When a yearling is knocked down to you and you see what it is, you can send it back: ${["", "once", "twice", "three times"][t]}, ${Math.round(VET_REFUND[t] * 100)}% of the price refunded.` },
  private: { title: "Private Sale", leans: "The sales", when: "Tattersalls", text: t => `Once, buy one lot ${t === 1 ? "from Book 3" : t === 2 ? "from Book 2 or 3" : "from any Book"} before it reaches the ring, at the middle of its guide price, with no rival bidding.` },
};
const JOCKEY_KINDS = {
  champion: { title: "Champion Jockey", style: null, text: t => t === 1 ? "Gets a tune out of his horse: it tends to run to its best." : t === 2 ? "Gets the best out of his horse: it runs to its best, and never a stinker." : "Rides his horse at its very best: usually its best run of the season, never a stinker." },
  tempo: { title: "Tempo Setter", style: "front", text: t => `Judges the pace from the front: a front-runner or prominent horse saves ${["", "a little", "plenty of", "lots of"][t]} energy for the finish.` },
  closer: { title: "Late Closer", style: "back", text: t => `Times his run from behind: a midfield or hold-up horse finishes ${["", "a little", "much", "far"][t]} stronger.` },
  reader: { title: "Race Reader", style: null, text: t => `Reads the race, however the horse runs: ${["", "a little", "a good deal", "plenty"][t]} better judged in front or from behind, finds the gaps and loses less switching.` },
};
// The board's trainer cards (TeamCards, role Trainer). cond: "dist" (only in races at these trips), "age", "line" (by a
// stallion of these sire lines) or "any". mode: "or" (adapt the trip OR the boost, whichever helps more in that race),
// "and" (both), "boost" (Stable Form). horses: how many horses it can go on.
const TRAINER_KINDS = {
  middle: { title: "Middle Distance", cond: "dist", vals: ["1m2f", "1m4f"] },
  staying: { title: "Staying Specialist", cond: "dist", vals: ["1m6f", "2m+"] },
  speed: { title: "Extra Speed", cond: "dist", vals: ["5f", "6f"] },
  miler: { title: "Miler Specialist", cond: "dist", vals: ["7f", "1m", "1m1f"] },
  juvenile: { title: "Juvenile Specialist", cond: "age", vals: [2] },
  burner: { title: "Slow Burner", cond: "age", vals: [4] },
  so: { title: "S|O Line Pedigrees", cond: "line", vals: ["S-Line", "O-Line"] },
  pd: { title: "P|D Line Pedigrees", cond: "line", vals: ["P-Line", "D-Line"] },
  master: { title: "Master Trainer", cond: "any", vals: [] },
  form: { title: "Stable Form", cond: "any", vals: [], boostOnly: true },
};
// On the board a card goes on one horse for three races; here there are ten, so each card reaches more horses
// (TRAINER_HORSES), and Stable Form III is +2 on every horse rather than +3 (it would be worth far more than any other).
const TRAINER_HORSES = [0, 2, 3, 3], FORM_HORSES = [0, 2, 4, 99], FORM_ALL_BOOST = 2;
function trainerSpec(kind, t) {
  const K = TRAINER_KINDS[kind];
  if (K.boostOnly) return { boost: t === 3 ? FORM_ALL_BOOST : 3, shift: 0, mode: "boost", horses: FORM_HORSES[t] };
  if (kind === "master") return { boost: 3, shift: 1, mode: t === 3 ? "and" : "or", horses: TRAINER_HORSES[t] };
  return { boost: t === 3 ? 5 : 3, shift: 1, mode: t === 1 ? "or" : "and", horses: TRAINER_HORSES[t] };
}
function trainerText(kind, t) {
  const K = TRAINER_KINDS[kind], sp = trainerSpec(kind, t);
  if (K.boostOnly) return t === 3 ? `Every horse in your stable runs ${FORM_ALL_BOOST} better.` : `${["", "", "Two", "Three", "Four"][sp.horses]} horses of your choice run 3 better.`;
  const n = ["", "one", "two", "three"][sp.horses] || sp.horses;
  const what = sp.mode === "or" ? `Moves the best trip of ${n} horses a step, or makes them ${sp.boost} better (whichever helps in that race)` : `Moves the best trip of ${n} horses a step and makes them ${sp.boost} better`;
  const when = K.cond === "dist" ? `, in ${K.vals.join(", ").replace(/, ([^,]*)$/, " and $1")} races` : K.cond === "age" ? `, while they're ${K.vals[0]}-year-olds` : K.cond === "line" ? `, if they're by a ${K.vals.join(" or ")} stallion` : ", at any age";
  return what + when + ".";
}
const TEAM_CARDS = [];
for (let t = 1; t <= 3; t++) {
  for (const k of Object.keys(OWNER_KINDS)) TEAM_CARDS.push({ code: `O${t}-${k}`, role: "Owner", tier: t, kind: k, title: OWNER_KINDS[k].title });
  for (const k of Object.keys(TRAINER_KINDS)) TEAM_CARDS.push({ code: `T${t}-${k}`, role: "Trainer", tier: t, kind: k, title: TRAINER_KINDS[k].title });
  for (const k of Object.keys(JOCKEY_KINDS)) TEAM_CARDS.push({ code: `J${t}-${k}`, role: "Jockey", tier: t, kind: k, title: JOCKEY_KINDS[k].title });
}
// (Trade Terms became the Sales Scout on 11 Nov: a team picked before then keeps its card under the new name)
const teamCard = code => TEAM_CARDS.find(c => c.code === String(code).replace(/-trade$/, "-scout"));
function cardText(c) {
  if (c.role === "Owner") return OWNER_KINDS[c.kind].text(c.tier);
  if (c.role === "Jockey") return JOCKEY_KINDS[c.kind].text(c.tier) + ` Rides up to ${JOCKEY_RIDES[c.tier]} of your races.`;
  return trainerText(c.kind, c.tier);
}
const cardWhen = c => c.role === "Owner" ? OWNER_KINDS[c.kind].when : c.role === "Trainer" ? "Entries" : "Race day";
const cardName = c => `${c.title} ${TIER_NUM[c.tier]}`;

// ---------- the draft ----------
function teamState() {
  if (!S.team) S.team = { picks: [], offer: null, done: false, choice: {}, used: {}, trains: {}, book: {}, income: 0, incomeLog: [] };
  return S.team;
}
const teamCards = () => (S.team ? S.team.picks.map(teamCard).filter(Boolean) : []);
const teamPoints = () => teamCards().reduce((a, c) => a + c.tier, 0);
const teamOn = () => !!(S.team && S.team.done);
const held = kind => teamOn() ? teamCards().find(c => c.kind === kind && c.role !== "Trainer") : null;
// a race-distance trainer card is only offered if a race on this card is at one of its trips (the board: "take another")
function trainerFits(c) {
  const K = TRAINER_KINDS[c.kind]; if (!K || K.cond !== "dist") return true;
  return RACES.some(r => K.vals.includes(DISTANCES[r.step]));
}
function deckLeft(role, tier) {
  const have = new Set(teamCards().map(c => c.title));
  return TEAM_CARDS.filter(c => c.role === role && c.tier === tier && !have.has(c.title) && (c.role !== "Trainer" || trainerFits(c)));
}
// A deck can be drawn from if its card fits the points left and still leaves a point for each kind you haven't got
function deckProblem(role, tier) {
  const T = teamState(), left = TEAM_POINTS - teamPoints(), roles = new Set(teamCards().map(c => c.role));
  if (T.done) return "Your team is picked";
  if (T.offer) return "Keep a card first";
  if (tier > left) return `Only ${left} point${left === 1 ? "" : "s"} left`;
  const missing = TEAM_ROLES.filter(r => r !== role && !roles.has(r)).length;
  if (left - tier < missing) return `Keep a point for ${TEAM_ROLES.filter(r => r !== role && !roles.has(r)).map(r => "a " + r.toLowerCase()).join(" and ")}`;
  if (!deckLeft(role, tier).length) return "None left";
  return "";
}
function drawDeck(role, tier, rnd) {
  rnd = rnd || Math.random;
  if (deckProblem(role, tier)) return false;
  const left = deckLeft(role, tier).map(c => [rnd(), c]).sort((a, b) => a[0] - b[0]).map(x => x[1].code);
  S.team.offer = { role, tier, codes: left.slice(0, TEAM_OFFER) };
  save(); return true;
}
function keepTeamCard(code) {
  const T = teamState(); if (!T.offer || !T.offer.codes.includes(code)) return;
  T.picks.push(code); T.offer = null;
  if (teamPoints() >= TEAM_POINTS) finishTeam();
  save();
}
function finishTeam() {
  const T = teamState(); if (T.done) return;
  T.done = true;
  const p = held("powerhouse"); if (p) S.budget += POWERHOUSE[p.tier];
  // Stable Form III goes on every horse; the others wait for you to give them to a horse
}
// Older saves (before the team) carry on without one
const teamSkipped = () => !!(S.team && S.team.skipped);

// ---------- owner cards at the National Stud ----------
// how many mares the mares sale turns over (rules.js drawPile)
const offerSize = () => ELITE_SEE[held("elite") ? held("elite").tier : 0];
// Stallion Owner: three stallions of the card's stars drawn (once), one kept
function ownerDraw() {
  const c = held("stallion"); if (!c) return [];
  if (!S.team.choice.draw) {
    const fits = STALLIONS.map(x => stallion(x.name)).filter(x => x.shownStars === OWNED_STARS[c.tier]).map(x => [hashStr(luckOf() + "|owned|" + x.name), x.name]).sort((a, b) => a[0] - b[0]).map(x => x[1]);
    S.team.choice.draw = fits.slice(0, OWNED_DRAW); save();
  }
  return S.team.choice.draw;
}
const ownedStallion = () => held("stallion") && S.team.choice.stallion;
function ownStallion(name) {
  if (!held("stallion") || S.team.choice.stallion || !ownerDraw().includes(name)) return false;
  S.team.choice.stallion = name; save(); return true;
}
const ownedFreeLeft = () => ownedStallion() ? OWNED_FREE - (S.team.used.stallion || 0) : 0;
// the fee you pay for a nomination: nothing to your own stallion while the free ones last
function feeFor(s) { return ownedStallion() === s.name && ownedFreeLeft() > 0 ? 0 : s.fee; }
// Pedigree Expert: the unproven stallions you know the truth about (Gold: all of them)
function knowsTrue(name) {
  const c = held("pedigree"); if (!c) return false;
  return PEDIGREE_LOOKS[c.tier] >= 99 || (S.team.used.revealed || []).includes(name);
}
const pedigreeLeft = () => { const c = held("pedigree"); return c && PEDIGREE_LOOKS[c.tier] < 99 ? PEDIGREE_LOOKS[c.tier] - (S.team.used.revealed || []).length : 0; };
function askExpert(name) {
  const s = stallion(name); if (!s || !s.unproven || knowsTrue(name) || pedigreeLeft() <= 0) return false;
  S.team.used.revealed = (S.team.used.revealed || []).concat(name); save(); return true;
}
const unprovenStallions = () => STALLIONS.map(x => stallion(x.name)).filter(x => x.unproven);
// (no card pays income any more; kept so older screens and saves still add up)
const teamIncome = () => (S.team ? S.team.income || 0 : 0);
function closeSales() {}

// ---------- owner cards at Tattersalls ----------
// Each lot's yearling is settled when the catalogue is made (seeded), so the agent's projection is of the real yearling
function lotFoal(l) {
  // the same yearling breed() will give (rules.js): this game's foal of the pair, or a scout's find's own
  return breedPure(stallion(l.sire), byName(l.dam), l.fs != null ? seeded(l.fs) : luck("foal|" + l.sire + "|" + l.dam));
}
// what a yearling costs you, and the dearest hammer price your budget covers (Trade Terms used to take a share off)
const payFor = price => price;
const canBidTo = () => S.budget;
// Bloodstock Agent: a range of 2 × band points with the true peak somewhere inside it (the same range every time you look)
function agentRange(l) {
  const c = held("agent"); if (!c) return null;
  const f = lotFoal(l); if (!f) return null;
  const B = AGENT_BAND[c.tier], u = luck("agent|" + l.sire + "|" + l.dam)(), lo = Math.round(f.r[2] - u * 2 * B);
  return { lo, hi: lo + 2 * B };
}
// Vet's Report: yearlings you may still send back
const vetLeft = () => { const c = held("vet"); return c ? VET_USES[c.tier] - (S.team.used.vet || 0) : 0; };
// Sales Scout: the races you brief him for, the lots that suit them, and his own finds
const scoutState = () => { const T = teamState(); T.scout = T.scout || { races: [], briefed: false }; return T.scout; };
const scoutRaces = () => held("scout") ? scoutState().races.map(id => RACES.find(r => r.id === id)).filter(Boolean) : [];
function scoutPick(id) {
  const c = held("scout"), T = c && scoutState(); if (!T || T.briefed || !RACES.some(r => r.id === id)) return false;
  if (T.races.includes(id)) T.races = T.races.filter(x => x !== id);
  else if (T.races.length < SCOUT_RACES[c.tier]) T.races.push(id); else return false;
  save(); return true;
}
// would this yearling (the breeding engine's result) be a real runner in the race at an age it allows? At its rating
// less 5 a step off its best trip it needs to reach the race's third band (one above the minimum: a fair chance of a
// place, not just a run); handicaps only take horses rated up to HCAP_MAX
const scoutBar = race => race.bands[BANDS - 2];
function foalFits(f, race, sex, bar) {
  bar = bar || scoutBar(race);
  if (race.sex && sex && race.sex !== sex) return false;
  for (let age = Math.max(2, race.ages[0]); age <= Math.min(4, race.ages[1]); age++) {
    const r = f.r[age - 2], d = f.d[age - 2], lo = Math.min(...d), hi = Math.max(...d);
    const steps = race.step < lo ? lo - race.step : race.step > hi ? race.step - hi : 0;
    if (steps > 3 || (race.grade === "Handicap" && r > HCAP_MAX)) continue;
    if (r - steps * 5 >= bar) return true;
  }
  return false;
}
// How likely a pedigree is to give a horse for the race: the share of the yearlings it could give (sampled with the
// breeding engine) that could run in it. The scout goes by the pedigree as the catalogue shows it (the stud book's
// stars, or the truth if your Pedigree Expert has told you), not by the yearling itself.
const SCOUT_MEMO = {}, SCOUT_LIKELY = 0.5, SCOUT_MAYBE = 0.25;
function pedigreeChance(sire, dam, race, n) {
  n = n || 48;
  const key = [sire, dam, race.id, n, knowsTrue(sire) ? 1 : 0].join("|"); if (SCOUT_MEMO[key] != null) return SCOUT_MEMO[key];
  const s0 = stallion(sire), s = { ...s0, trueStars: knowsTrue(sire) ? s0.trueStars : s0.shownStars }, m = byName(dam), R = seeded(hashStr(key));
  let ok = 0;
  for (let k = 0; k < n; k++) { const f = breedPure(s, m, R), sex = R() < .5 ? "F" : "C"; if (foalFits(f, race, sex)) ok++; }
  return (SCOUT_MEMO[key] = ok / n);
}
// what the scout says about a lot: the races it suits (likely or possible), or nothing for your races
function lotSuits(l) {
  const rs = scoutRaces(); if (!rs.length) return null;
  const list = rs.map(r => ({ r, p: pedigreeChance(l.sire, l.dam, r) })).filter(x => x.p >= SCOUT_MAYBE).sort((a, b) => b.p - a.p);
  return { list, best: list.length ? list[0].p : 0 };
}
// Brief him: the races are settled, and his finds join the catalogue. Each is a bargain bred for one of your races:
// a Book 2 or 3 pedigree that suits it (from the likeliest), whose yearling is better than its price suggests: good
// enough to win the race if it can be found (its second band), at least a fair chance of a place.
function briefScout() {
  const c = held("scout"), T = c && scoutState(); if (!T || T.briefed || !T.races.length || !S.sale) return false;
  T.briefed = true; T.found = [];
  const rs = scoutRaces(), taken = new Set([...(S.usedMares || []), ...(S.catDams || []), ...S.sale.map(l => l.dam)]);
  for (let k = 0; k < SCOUT_LOTS[c.tier]; k++) {
    const race = rs[k % rs.length], lot = scoutFind(race, taken); if (!lot) continue;
    taken.add(lot.dam); S.catDams = (S.catDams || []).concat(lot.dam);
    S.sale.push(lot); T.found.push(lot.id);
  }
  save(); return true;
}
function scoutFind(race, taken) {
  const want = furlongs(DISTANCES[race.step]), cand = [];
  for (const s of STALLIONS.map(x => stallion(x.name))) for (const m of MARES) {
    if (taken.has(m.name) || !lotMatch(s, m)) continue;
    const stars = s.shownStars + m.stars, book = BOOKS.find(b => stars >= b.min && stars <= b.max); if (!book) continue;
    const a = optF(s), b = optF(m);
    if (Math.abs(Math.min(a, b) * .6 + Math.max(a, b) * .4 - want) > 3) continue;   // nowhere near the trip: not worth sampling
    cand.push({ s, m, book });
  }
  if (!cand.length) return null;
  // a fair sample of the pedigrees near the trip (sampling them all takes too long on a phone)
  const rnd = luck("scout|" + race.id + "|" + taken.size);   // this game's own luck: reloading can't change his finds
  for (let k = cand.length - 1; k > 0; k--) { const j = Math.floor(rnd() * (k + 1)); [cand[k], cand[j]] = [cand[j], cand[k]]; }
  cand.length = Math.min(cand.length, 240);
  cand.forEach(x => x.p = pedigreeChance(x.s.name, x.m.name, race, 16));
  // a bargain: Books 2 and 3 when any of them suit the race at all
  const cheap = cand.filter(x => x.book.n > 1 && x.p > 0), from = cheap.length ? cheap : cand;
  const top = Math.max(...from.map(x => x.p)), pool = from.filter(x => x.p >= top - 0.15);
  const pick = pool[Math.floor(rnd() * pool.length)];
  // his find really is one: its yearling (settled now, like every lot's) is good enough to win the race if one of
  // this pedigree's can be, or at least to place
  let fs = 0;
  const tryFor = (bar, n) => { for (let k = 0; k < n; k++) {
    const f0 = 1 + Math.floor(rnd() * 2e9), R = seeded(f0), f = breedPure(pick.s, pick.m, R), sex = R() < .5 ? "F" : "C";
    if (foalFits(f, race, sex, bar)) { fs = f0; return true; }
  } return false; };
  if (!tryFor(race.bands[1], 300) && !tryFor(scoutBar(race), 200)) tryFor(needFor(race), 100) || (fs = 1 + Math.floor(rnd() * 2e9));
  S.lotN = (S.lotN || 0) + 1;
  return { id: "lot" + S.lotN, n: S.lotN, book: pick.book.n, sire: pick.s.name, dam: pick.m.name, reserve: RESERVES[pick.s.shownStars + pick.m.stars] || 10000, fs, scout: race.id };
}

// Private Sale: one lot before the ring, at the middle of its guide
const privatePrice = l => round5k((guide(l)[0] + guide(l)[1]) / 2);
function privateOK(l) { const c = held("private"); return !!c && !S.team.used.private && PRIVATE_BOOKS[c.tier].includes(l.book); }

// ---------- trainer cards ----------
// S.team.trains[code] = [horse ids]; Stable Form III is on every horse
const trainerCards = () => teamOn() ? teamCards().filter(c => c.role === "Trainer") : [];
function trainHorses(c) { const sp = trainerSpec(c.kind, c.tier); return sp.horses >= 99 ? S.stable.map(h => h.id) : (S.team.trains[c.code] || []); }
// can this card go on this horse at all? (sire line cards only on that line's horses)
function trainerCanGo(c, h) {
  const K = TRAINER_KINDS[c.kind];
  if (K.cond === "line") { const s = byName(h.sire); return !!s && K.vals.includes(s.sireLine); }
  return true;
}
function giveTrainer(code, horseId) {
  const c = teamCard(code), h = horse(horseId); if (!c || c.role !== "Trainer" || !h || !trainerCanGo(c, h)) return false;
  const sp = trainerSpec(c.kind, c.tier); if (sp.horses >= 99) return false;
  let list = (S.team.trains[code] || []).filter(id => id !== horseId);
  if (list.length >= sp.horses) list = list.slice(list.length - sp.horses + 1);
  list.push(horseId); S.team.trains[code] = list; save(); return true;
}
function takeTrainer(code, horseId) { S.team.trains[code] = (S.team.trains[code] || []).filter(id => id !== horseId); save(); }
// What a horse's trainer cards do in a race: its race-day boost and how far its best trip moves (towards the race)
function trainFor(h, race, baseSteps) {
  const out = { boost: 0, shift: 0, cards: [] };
  for (const c of trainerCards()) {
    if (!trainHorses(c).includes(h.id)) continue;
    const K = TRAINER_KINDS[c.kind], sp = trainerSpec(c.kind, c.tier);
    if (K.cond === "dist" && !(race && K.vals.includes(DISTANCES[race.step]))) continue;
    if (K.cond === "age" && !K.vals.includes(h.age)) continue;
    if (K.cond === "line" && !trainerCanGo(c, h)) continue;
    const steps = Math.max(0, (baseSteps || 0) - out.shift);
    if (sp.mode === "boost") { out.boost += sp.boost; out.cards.push({ c, did: `+${sp.boost}` }); }
    else if (sp.mode === "and") { out.boost += sp.boost; out.shift += sp.shift; out.cards.push({ c, did: steps ? `+${sp.boost}, a step nearer the trip` : `+${sp.boost}` }); }
    else if (steps) { out.shift += sp.shift; out.cards.push({ c, did: "a step nearer the trip" }); }   // "or": the trip, when that's worth more
    else { out.boost += sp.boost; out.cards.push({ c, did: `+${sp.boost}` }); }
  }
  return out;
}

// ---------- jockey cards ----------
const jockeyCards = () => teamOn() ? teamCards().filter(c => c.role === "Jockey") : [];
const ridesOf = code => RACES.filter(r => (S.team.book || {})[r.id] === code);
const ridesLeft = c => JOCKEY_RIDES[c.tier] - ridesOf(c.code).length;
function bookJockey(raceId, code) {
  const T = teamState(); T.book = T.book || {};
  if (!code) { delete T.book[raceId]; save(); return true; }
  const c = teamCard(code); if (!c || c.role !== "Jockey") return false;
  if (T.book[raceId] !== code && ridesLeft(c) <= 0) return false;
  T.book[raceId] = code; save(); return true;
}
const bookedFor = race => teamOn() && S.team.book && S.team.book[race.id] ? teamCard(S.team.book[race.id]) : null;
// the jockey's fields for the race engine
function jockeyFields(race) {
  const c = bookedFor(race); if (!c) return {};
  return { jockey: JOCKEY_LEVEL[c.tier], ...JOCKEY_EDGE[c.kind][c.tier] };
}
// does his specialism suit this horse's running style?
function jockeySuits(c, h) {
  const st = JOCKEY_KINDS[c.kind].style; if (!st || !h || !h.style) return true;
  return st === "front" ? h.style === "front" || h.style === "prominent" : h.style === "midfield" || h.style === "holdup";
}
