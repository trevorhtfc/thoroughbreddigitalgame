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
const POWERHOUSE = [0, 150000, 300000, 450000];          // added to the budget
const ELITE_MARES = [null, ["mid"], ["hi"], ["hi", "hi"]];   // free mares, chosen from the whole pile
const BLACK_TYPE = [0, 3, 4, 5];                         // the stallion's stars (as shown in the stud book)
const BLACK_TYPE_USES = 3;                               // half price for up to this many nominations
const STUD_MASTER = [0, 25000, 50000, 100000];           // paid now, and again for each of his lots a rival buys
const STUD_MASTER_LOTS = 2;                              // ... up to this many lots (three times the first payment in all)
const AGENT_REFUND = [0, 0.8, 0.9, 1];
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
  powerhouse: { title: "Powerhouse", when: "At once", text: t => `${money(POWERHOUSE[t])} more to spend on mares, stud fees and yearlings.` },
  elite: { title: "Elite Mares", when: "The National Stud", text: t => t === 1 ? "One Useful (3★) mare free, picked from the whole pile, on top of your ten." : t === 2 ? "One Blue-blooded (4–5★) mare free, picked from the whole pile, on top of your ten." : "Two Blue-blooded (4–5★) mares free, picked from the whole pile, on top of your ten." },
  blacktype: { title: "Black Type Stud", when: "The National Stud", text: t => `Choose one ${BLACK_TYPE[t]}★ stallion: half price on up to ${BLACK_TYPE_USES} nominations to him.` },
  studmaster: { title: "Stud Master", when: "Before Tattersalls", text: t => `Choose a stallion in secret. ${money(STUD_MASTER[t])} now, and ${money(STUD_MASTER[t])} more in stud income each time a rival buys one of his yearlings (up to ${STUD_MASTER_LOTS} lots). Stud income counts with your prize money.` },
  agent: { title: "Bloodstock Agent", when: "Tattersalls", text: t => `Once: when a yearling is knocked down to you and you see what it is, you may hand it back for ${Math.round(AGENT_REFUND[t] * 100)}% of the price.` },
  insider: { title: "Auction Insider", when: "Tattersalls", text: t => t === 1 ? "Once: buy one lot from Book 2 or 3 at its reserve, without going to auction." : t === 2 ? "See the class of every yearling in the catalogue before you bid." : "See the class of every yearling before you bid, and once, buy any lot at its reserve without going to auction." },
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
const teamCard = code => TEAM_CARDS.find(c => c.code === code);
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
  const sm = held("studmaster"); if (sm) S.budget += STUD_MASTER[sm.tier];   // paid now; the stallion is chosen before Tattersalls
  // Stable Form III goes on every horse; the others wait for you to give them to a horse
}
// Older saves (before the team) carry on without one
const teamSkipped = () => !!(S.team && S.team.skipped);

// ---------- owner cards at the National Stud ----------
const eliteLeft = () => { const c = held("elite"); if (!c) return []; const used = S.team.used.elite || 0; return ELITE_MARES[c.tier].slice(used); };
const mareCap = () => MARE_CAP + (held("elite") ? ELITE_MARES[held("elite").tier].length : 0);
function takeEliteMare(name) {
  const left = eliteLeft(), m = byName(name); if (!left.length || !m) return false;
  const p = PILES.find(x => x.id === left[0]); if (!p.stars.includes(m.stars) || ownMares().has(name)) return false;
  S.hand.push(name); S.team.used.elite = (S.team.used.elite || 0) + 1; save();
  return true;
}
const blackTypeStallion = () => held("blacktype") && S.team.choice.blacktype;
function blackTypeFits(s) { const c = held("blacktype"); return c && s.shownStars === BLACK_TYPE[c.tier]; }
// the fee you pay for a nomination: half to your Black Type stallion while the card's uses last
function feeFor(s) {
  if (blackTypeStallion() === s.name && (S.team.used.blacktype || 0) < BLACK_TYPE_USES) return Math.round(s.fee / 2);
  return s.fee;
}
function chooseStallion(kind, name) {
  if (!held(kind) || S.team.choice[kind]) return false;
  const s = stallion(name); if (!s) return false;
  if (kind === "blacktype" && !blackTypeFits(s)) return false;
  if (kind === "studmaster" && S.step > 2) return false;
  S.team.choice[kind] = name; save(); return true;
}
// Stud Master: a rival bought one of his lots
function studMasterSale(l, rival) {
  const c = held("studmaster"); if (!c || S.team.choice.studmaster !== l.sire) return 0;
  const n = S.team.used.studmaster || 0; if (n >= STUD_MASTER_LOTS) return 0;
  S.team.used.studmaster = n + 1; S.team.income += STUD_MASTER[c.tier];
  S.team.incomeLog.push({ lot: l.n, sire: l.sire, rival, amount: STUD_MASTER[c.tier] });
  return STUD_MASTER[c.tier];
}
// When the sales close (you leave for the races), the lots nobody brought into the ring go through it among the rivals
function closeSales() {
  if (!S.sale || !S.sale.length) return;
  for (const l of S.sale) {
    const ap = appeal(l), top = RIVALS.map(r => ({ r, c: Math.random() < r.keen(l) ? l.reserve * ap * r.want(l) * (.7 + Math.random() * .9) : 0 })).sort((a, b) => b.c - a.c)[0];
    if (top && top.c >= l.reserve) studMasterSale(l, top.r.name);
  }
  S.sale = []; save();
}
const teamIncome = () => (S.team ? S.team.income || 0 : 0);

// ---------- owner cards at Tattersalls ----------
// Each lot's yearling is settled when the catalogue is made (seeded), so an Auction Insider can see its class first
function lotFoal(l) {
  if (l.fs == null) return null;
  return breedPure(stallion(l.sire), byName(l.dam), seeded(l.fs));
}
const insiderSees = () => { const c = held("insider"); return !!c && c.tier >= 2; };
function insiderClaimOK(l) {
  const c = held("insider"); if (!c || c.tier === 2 || S.team.used.insider) return false;
  return c.tier === 3 || l.book >= 2;
}
const agentLeft = () => { const c = held("agent"); return c && !S.team.used.agent ? c : null; };

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
