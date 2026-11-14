// =====================================================================================================================
// Thoroughbred: your team. Owner, trainer and jockey cards, drafted at the Jockey Club before the stud opens (owner,
// 10 Nov: "integrate owner, jockey and trainers into your team, which you draft at the start ... a draft from bronze,
// silver and gold decks of each type, 6 points: gold is 3, silver 2, bronze 1").
//
// The cards are the board game's (the CMS collection TeamCards on the Thoroughbred site, 60 cards), turned into the
// digital game's terms where the board's rules can't work as they are (no other players at the stud, no card hands in
// the race). The trainer cards are the board's almost word for word. Rules only, no screens (those are in js/ui-team.js).
//
// The draft: pick a deck (Owner, Trainer or Jockey; Bronze, Silver or Gold) and its top card is yours (14 Nov; it
// used to turn three over to keep one). Spend exactly 6 points (Gold 3, Silver 2, Bronze 1), with at least one card of each
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
// Trainer cards (owner, 14 Nov: "throw those trainers in"; the brainstorm of 11 Nov, "yard jobs at Warren Hill"): each
// trainer gives you jobs to spend on your horses at Warren Hill, between the sales and entries; any left over can be
// spent in race week, once the going is declared (ground work or a tune-up only). The card's speciality makes some jobs
// stronger. Stable Form is the one with no jobs to place: a flat boost on every horse.
// (first test games, 14 Nov: 2 / 3 / 4 jobs made a trainer worth +55k to +120k a week, well above the owner and jockey
// cards, so one fewer)
const TRAINER_JOBS = [0, 1, 2, 3];                        // jobs a trainer gives you, by tier
// The Juvenile Specialist's first tune-up in a 2-year-old race is free (every horse is a 2-year-old at Warren Hill, so a
// free settle for 2-year-olds, tried first, was a free settle for anyone)
const TUNE_UP = 3, TUNE_SPECIAL = 5, TUNE_MASTER = 4;    // a tune-up: this much better in the race you name (a specialist's; the Master's anywhere)
const FORM_BOOST = [0, 1, 2, 2], FORM_JOBS = [0, 0, 0, 1];   // Stable Form: every horse this much better; Gold has 2 jobs too
// Jockey cards (owner, 14 Nov: "boosts to riding styles and boosts to distances ... champion jockey is just an all over
// boost"): booked race by race at entries. A rating boost on the day where his speciality fits, or (the two style
// jockeys) a riding skill in the race engine worth about the same when the horse runs his way.
const JOCKEY_RIDES = [0, 3, 4, 5];                       // how many of your races he can ride
const JOCKEY_LEVEL = [0, 3, 4, 5];                       // his skill in the race engine (1 to 5); your own yard's is random
const CHAMPION_BOOST = [0, 2, 3, 4];                     // Champion Jockey: in every race he rides
const SPECIAL_BOOST = [0, 3, 4, 6];                      // trip, big-race and going specialists: where they shine
const PARTNER_BOOST = 1;
const MUD_EXTRA = 2;                                     // the Mud Lark: this much more than the other specialists (the going is a gamble)                                 // a trainer and jockey of the same trip, in races at that trip
// The style jockeys in the race engine (race-engine/engine.js: paceTank, lateKick), measured with
// race-engine/check/team-jockeys.mjs: about +2 / +3.3 / +4.7 rating points when the horse runs his way, +0 otherwise.
const JOCKEY_EDGE = {
  tempo:  [null, { paceTank: 0.04 }, { paceTank: 0.07 }, { paceTank: 0.10 }],
  closer: [null, { lateKick: 0.011 }, { lateKick: 0.016 }, { lateKick: 0.022 }],
};

// ---------- the cards ----------
// Owner: 6 kinds × 3 tiers. Trainer: the board's 10 kinds × 3 tiers. Jockey: the board's 4 kinds × 3 tiers.
const OWNER_KINDS = {
  powerhouse: { title: "Powerhouse", leans: "Either", when: "At once", text: t => `${money(POWERHOUSE[t])} more to spend on mares, stud fees and yearlings.` },
  elite: { title: "Elite Mares", leans: "Breeding", when: "The National Stud", text: t => typeof handOn === "function" && !handOn() ? `At the mares sale you see ${ELITE_SEE[t]} mares from the pile instead of 2, and keep the one you want.`
    : `Upgrade ${ELITE_UP[t] === 1 ? "one of your mares" : ELITE_UP[t] + " of your mares"} a grade, Moderate to Useful or Useful to Blue-blooded: two from the grade above are turned over and you keep one.` },
  stallion: { title: "Stallion Owner", leans: "Breeding", when: "The National Stud", text: t => `Three ${OWNED_STARS[t]}★ stallions are drawn at the stud: keep one as your own, with ${OWNED_FREE} free nominations to him.` },
  pedigree: { title: "Pedigree Expert", leans: "Breeding", when: "The stud and the sales", text: t => `An unproven stallion may be a star better or worse than the stud book says. Your expert tells you the truth about ${t === 3 ? "every one of them" : PEDIGREE_LOOKS[t] + " of them"}.` },
  scout: { title: "Sales Scout", leans: "The sales", when: "Tattersalls", text: t => `Tell him the ${SCOUT_RACES[t]} races you still need a horse for. He marks the lots bred to suit them, greys out the rest, and finds ${SCOUT_LOTS[t] === 1 ? "a bargain" : SCOUT_LOTS[t] + " bargains"} of his own: cheaper lots whose yearlings are good enough for them.` },
  agent: { title: "Bloodstock Agent", leans: "The sales", when: "Tattersalls", text: t => `His projection of every yearling's peak rating, to within ${AGENT_BAND[t]} points either way: the true figure is somewhere in his range.` },
  vet: { title: "Vet's Report", leans: "The sales", when: "Tattersalls", text: t => `When a yearling is knocked down to you and you see what it is, you can send it back: ${["", "once", "twice", "three times"][t]}, ${Math.round(VET_REFUND[t] * 100)}% of the price refunded.` },
  private: { title: "Private Sale", leans: "The sales", when: "Tattersalls", text: t => `Once, buy one lot ${t === 1 ? "from Book 3" : t === 2 ? "from Book 2 or 3" : "from any Book"} before it reaches the ring, at the middle of its guide price, with no rival bidding.` },
};
// The trips the specialists cover (the board's trainer cards' trips; the jockeys share them, so the two can pair up)
const TRIPS = { speed: ["5f", "6f"], miler: ["7f", "1m", "1m1f"], middle: ["1m2f", "1m4f"], staying: ["1m6f", "2m+"] };
const tripWords = v => v.join(", ").replace(/, ([^,]*)$/, " and $1");
const raceTrip = race => DISTANCES[race.step];
const JOCKEY_KINDS = {
  champion: { title: "Champion Jockey", text: t => `The best in the weighing room: every horse he rides runs ${CHAMPION_BOOST[t]} better, whatever the race.` },
  tempo: { title: "Tempo Setter", style: "front", text: t => `Judges the pace from the front: a front-runner or prominent horse saves ${["", "a little", "plenty of", "lots of"][t]} energy for the finish.` },
  closer: { title: "Late Closer", style: "back", text: t => `Times his run from behind: a midfield or hold-up horse finishes ${["", "a little", "much", "far"][t]} stronger.` },
  speed: { title: "Sprint Jockey", trips: TRIPS.speed, text: t => `Quick out of the stalls and sharp in a finish: ${SPECIAL_BOOST[t]} better in ${tripWords(TRIPS.speed)} races.` },
  miler: { title: "Mile Jockey", trips: TRIPS.miler, text: t => `At home over a mile: ${SPECIAL_BOOST[t]} better in ${tripWords(TRIPS.miler)} races.` },
  staying: { title: "Staying Jockey", trips: TRIPS.middle.concat(TRIPS.staying), text: t => `Patient and strong in a long finish: ${SPECIAL_BOOST[t]} better in races of 1m2f and further.` },
  bigrace: { title: "Big-Race Jockey", text: t => `Never better than on the big day: ${SPECIAL_BOOST[t]} better in Group races, nothing extra in the others.` },
  mudlark: { title: "Mud Lark", text: t => `Loves it when the rain comes: ${SPECIAL_BOOST[t] + MUD_EXTRA} better on Softer or Heavy going. You book him before the going is declared.` },
};
// The board's trainer cards (TeamCards, role Trainer), now specialities: every trainer can do every job, the
// speciality makes some of them stronger (owner, 11 Nov brainstorm, "yard jobs").
const TRAINER_KINDS = {
  speed: { title: "Extra Speed", spec: "trip", trips: TRIPS.speed },
  miler: { title: "Miler Specialist", spec: "trip", trips: TRIPS.miler },
  middle: { title: "Middle Distance", spec: "trip", trips: TRIPS.middle },
  staying: { title: "Staying Specialist", spec: "trip", trips: TRIPS.staying },
  juvenile: { title: "Juvenile Specialist", spec: "juvenile" },
  burner: { title: "Slow Burner", spec: "burner" },
  so: { title: "S|O Line Pedigrees", spec: "line", lines: ["S-Line", "O-Line"] },
  pd: { title: "P|D Line Pedigrees", spec: "line", lines: ["P-Line", "D-Line"] },
  master: { title: "Master Trainer", spec: "master" },
  form: { title: "Stable Form", spec: "form" },
};
const jobsOfCard = c => c.kind === "form" ? FORM_JOBS[c.tier] : TRAINER_JOBS[c.tier];
function trainerText(kind, t) {
  const K = TRAINER_KINDS[kind], n = jobsOfCard({ kind, tier: t }), jobs = `${n === 1 ? "One job" : n + " jobs"} at Warren Hill`;
  if (K.spec === "form") return `Every horse in your stable runs ${FORM_BOOST[t]} better on the day${n ? `, and ${n === 1 ? "one job" : n + " jobs"} at Warren Hill` : ". No jobs to place"}.`;
  if (K.spec === "trip") return `${jobs}. In ${tripWords(K.trips)} races his tune-ups are +${TUNE_SPECIAL}, and trip work towards those trips moves two steps.`;
  if (K.spec === "juvenile") return `${jobs}. His tune-ups are +${TUNE_SPECIAL} in 2-year-old races, and the first of them is free.`;
  if (K.spec === "burner") return `${jobs}. His eye is free: you see every horse's next age before you develop it. Tune-ups are +${TUNE_SPECIAL} for 4-year-olds.`;
  if (K.spec === "line") return `${jobs}. On horses by ${K.lines.join(" or ")} stallions every job counts double.`;
  return `${jobs}. The all-rounder: his tune-ups are +${TUNE_MASTER} in any race.`;
}
// What a trainer's jobs are (the same for every trainer)
const JOB_INFO = {
  trip: { name: "Trip work", what: "Moves its best trip a step longer or shorter, for the season" },
  settle: { name: "Settle", what: "A keen horse learns to settle: it stops fighting for its head" },
  ground: { name: "Ground work", what: "It handles one more going, next to those it likes" },
  tune: { name: "Tune-up", what: `Brings it to a peak for one race you name: +${TUNE_UP} there` },
  eye: { name: "Trainer's eye", what: "Shows how it will be at the next age before you develop it" },
};
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
  if (c.role === "Jockey") return JOCKEY_KINDS[c.kind].text(c.tier) + ` Rides ${JOCKEY_RIDES[c.tier]} of your races.`;
  return trainerText(c.kind, c.tier);
}
const cardWhen = c => c.role === "Owner" ? OWNER_KINDS[c.kind].when : c.role === "Trainer" ? (c.kind === "form" && !FORM_JOBS[c.tier] ? "Race day" : "Warren Hill") : "Race day";
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
// A trip jockey is only offered if a race on this card is at one of his trips, a Big-Race Jockey if there's a Group race
// (the board: "take another"). Trainers are never wasted: every one can do every job.
function cardFits(c) {
  if (c.role !== "Jockey") return true;
  const K = JOCKEY_KINDS[c.kind];
  if (K.trips) return RACES.some(r => K.trips.includes(raceTrip(r)));
  if (c.kind === "bigrace") return RACES.some(r => r.grade.startsWith("Group"));
  return true;
}
function deckLeft(role, tier) {
  const have = new Set(teamCards().map(c => c.title));
  return TEAM_CARDS.filter(c => c.role === role && c.tier === tier && !have.has(c.title) && cardFits(c));
}
// A deck can be drawn from if its card fits the points left and still leaves a point for each kind you haven't got
function deckProblem(role, tier) {
  const T = teamState(), left = TEAM_POINTS - teamPoints(), roles = new Set(teamCards().map(c => c.role));
  if (T.done) return "Your team is picked";
  if (tier > left) return `Only ${left} point${left === 1 ? "" : "s"} left`;
  const missing = TEAM_ROLES.filter(r => r !== role && !roles.has(r)).length;
  if (left - tier < missing) return `Keep a point for ${TEAM_ROLES.filter(r => r !== role && !roles.has(r)).map(r => "a " + r.toLowerCase()).join(" and ")}`;
  if (!deckLeft(role, tier).length) return "None left";
  return "";
}
// Pick and go (owner, 14 Nov: "we don't get a choice on which cards we pick once we draw. It's a simple pick and go"):
// the deck's top card is yours. The order is this game's luck, so a reload doesn't change it
function drawDeck(role, tier, rnd) {
  if (deckProblem(role, tier)) return false;
  const T = teamState(); rnd = rnd || luck("team|" + role + "|" + tier + "|" + T.picks.length);
  const left = deckLeft(role, tier).map(c => [rnd(), c]).sort((a, b) => a[0] - b[0]).map(x => x[1].code);
  T.picks.push(left[0]); T.last = left[0]; T.offer = null;
  if (teamPoints() >= TEAM_POINTS) finishTeam();
  save(); return left[0];
}
// (games saved part-way through the old draft, with three cards turned over: the first is kept)
function keepTeamCard(code) {
  const T = teamState(); if (!T.offer || !T.offer.codes.includes(code)) return;
  T.picks.push(code); T.last = code; T.offer = null;
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
// (games saved before the mares hand: Elite Mares turns more over. Since 14 Nov it upgrades mares in your hand instead)
const offerSize = () => typeof handOn === "function" && handOn() ? OFFER_SIZE : ELITE_SEE[held("elite") ? held("elite").tier : 0];
// Elite Mares with the dealt hand (owner, 14 Nov: "Elite mares would change to be able to upgrade your hand"): each
// upgrade swaps a Moderate or Useful mare you haven't bred for one of two from the grade above
const ELITE_UP = [0, 1, 2, 4];                     // (Gold 4: with 3 it was hardly better than Silver, 14 Nov tests)
const upgradesLeft = () => handOn() && held("elite") ? ELITE_UP[held("elite").tier] - (mh().up || 0) : 0;
const gradeUp = name => { const k = PILES.indexOf(pileOf(name)); return k > 0 ? PILES[k - 1] : null; };
const canUpgrade = name => upgradesLeft() > 0 && S.step === 1 && !S.offer && !S.foal && S.hand.includes(name) && !!gradeUp(name) && pileLeft(gradeUp(name)).length > 0;
function upgradeMare(name) {
  if (!canUpgrade(name)) return false;
  const p = gradeUp(name), n = (mh().up || 0) + 1;
  S.offer = { pile: p.id, swap: name, mares: pileOrder(p, "up|" + n + "|" + name).slice(0, OFFER_SIZE).map(m => m.name) };
  save(); return true;
}
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

// ---------- trainer cards: jobs at Warren Hill ----------
// S.team.jobs = [{ k: "trip" | "settle" | "ground" | "tune" | "eye", h: horse id, dir?, race?, free?, week?, was? }].
// Trip work, Settle and Ground work change the horse itself (what it was is kept in `was`, so a job can be undone
// while you're still at Warren Hill or entries); a tune-up is counted on the day (trainFor); the eye only shows.
const trainerCards = () => teamOn() ? teamCards().filter(c => c.role === "Trainer") : [];
const trainerSpecs = () => trainerCards().map(c => ({ c, ...TRAINER_KINDS[c.kind] }));
const jobsAll = () => (S.team && S.team.jobs) || [];
const jobsTotal = () => trainerCards().reduce((a, c) => a + jobsOfCard(c), 0);
const jobsUsed = () => jobsAll().filter(j => !j.free).length;
const jobsLeft = () => Math.max(0, jobsTotal() - jobsUsed());
const lineOf = h => { const s = byName(h.sire); return s ? s.sireLine : ""; };
// does a speciality make jobs on this horse count double (the sire-line cards)?
const lineDouble = h => trainerSpecs().some(t => t.spec === "line" && t.lines.includes(lineOf(h)));
const raceWeek = () => S.step >= 4;
const raceOf = id => RACES.find(r => r.id === id);
// how far trip work would move this horse's best trip in that direction (two steps when a specialist's trips lie that way
// or a sire-line card covers it; never past the ends of the scale)
function tripSteps(h, dir) {
  const d = tripAt(h, h.age), lo = Math.min(...d), hi = Math.max(...d);
  let n = lineDouble(h) ? 2 : 1;
  for (const t of trainerSpecs()) if (t.spec === "trip") {
    const tl = DISTANCES.indexOf(t.trips[0]), th = DISTANCES.indexOf(t.trips[t.trips.length - 1]);
    if ((dir > 0 && tl > hi) || (dir < 0 && th < lo)) n = Math.max(n, Math.min(2, dir > 0 ? tl - hi : lo - th));
  }
  return dir > 0 ? Math.min(n, DISTANCES.length - 1 - hi) : Math.min(n, lo);
}
// the goings ground work would add on that side ("soft" or "quick")
function groundAdds(h, side) {
  const g = h.grounds.map(x => GROUND_ORDER.indexOf(x)).filter(i => i >= 0), lo = Math.min(...g), hi = Math.max(...g), n = lineDouble(h) ? 2 : 1, out = [];
  for (let k = 1; k <= n; k++) { const i = side === "soft" ? lo - k : hi + k; if (i >= 0 && i < GROUND_ORDER.length) out.push(GROUND_ORDER[i]); }
  return out;
}
// a tune-up's boost in this race: +5 when a speciality fits (trip, 2-year-old race, a 4-year-old, the sire line)
function tuneBoost(h, race) {
  let b = trainerSpecs().some(t => t.spec === "master") ? TUNE_MASTER : TUNE_UP;
  for (const t of trainerSpecs()) {
    if (t.spec === "trip" && t.trips.includes(raceTrip(race))) b = TUNE_SPECIAL;
    if (t.spec === "juvenile" && race.ages[1] === 2) b = TUNE_SPECIAL;
    if (t.spec === "burner" && h.age === 4) b = TUNE_SPECIAL;
  }
  if (lineDouble(h)) b = TUNE_SPECIAL;
  return b;
}
const tuneFree = race => !!race && race.ages[1] === 2 && trainerSpecs().some(t => t.spec === "juvenile") && !jobsAll().some(j => j.k === "tune" && j.free);
const eyeFree = () => trainerSpecs().some(t => t.spec === "burner");
const tuneOf = race => jobsAll().find(j => j.k === "tune" && j.race === race.id);
const eyed = h => eyeFree() || jobsAll().some(j => j.k === "eye" && j.h === h.id && j.age === h.age);
// why a job can't be done now ("" if it can)
function jobProblem(k, h, o = {}) {
  if (!teamOn() || !trainerCards().length) return "You have no trainer";
  if (!h) return "No horse";
  const free = (k === "eye" && eyeFree()) || (k === "tune" && tuneFree(raceOf(o.race)));
  if (!free && jobsLeft() <= 0) return "No jobs left";
  if (raceWeek() && k !== "ground" && k !== "tune") return "In race week only ground work and tune-ups";
  if (k === "trip") { if (!tripSteps(h, o.dir)) return o.dir > 0 ? "Can't go any longer" : "Can't go any shorter"; }
  if (k === "settle") { if (h.temper !== "keen") return "Already settled"; }
  if (k === "ground") { if (!groundAdds(h, o.side).length) return "Already handles every going that way"; }
  if (k === "tune") {
    const r = raceOf(o.race); if (!r) return "Choose a race";
    if (S.results[r.id]) return "Already run";
    if (tuneOf(r)) return "That race already has a tune-up";
  }
  if (k === "eye") { if (h.age >= 4) return "Fully grown"; if (eyed(h)) return "Already seen"; }
  return "";
}
function doJob(k, h, o = {}) {
  if (jobProblem(k, h, o)) return false;
  const T = teamState(); T.jobs = T.jobs || [];
  const j = { k, h: h.id, free: (k === "eye" && eyeFree()) || (k === "tune" && tuneFree(raceOf(o.race))) || undefined, week: raceWeek() || undefined, was: { d: h.d.map(x => x.slice()), grounds: h.grounds.slice(), temper: h.temper } };
  if (k === "trip") { const n = tripSteps(h, o.dir); j.dir = o.dir; j.n = n; h.d = h.d.map(r => [...new Set(r.map(i => Math.max(0, Math.min(DISTANCES.length - 1, i + o.dir * n))))].sort((a, b) => a - b)); }
  if (k === "settle") h.temper = "calm";
  if (k === "ground") { j.side = o.side; j.add = groundAdds(h, o.side); h.grounds = GROUND_ORDER.filter(g => h.grounds.includes(g) || j.add.includes(g)); }
  if (k === "tune") j.race = o.race;
  if (k === "eye") j.age = h.age;
  if (k !== "trip" && k !== "settle" && k !== "ground") delete j.was;
  T.jobs.push(j); save(); return true;
}
// undo: the last job on that horse, before race week (a race-week job stands)
function jobUndoable(i) {
  const j = jobsAll()[i]; if (!j || j.week || raceWeek()) return false;
  return !jobsAll().slice(i + 1).some(x => x.h === j.h && x.was);
}
function undoJob(i) {
  if (!jobUndoable(i)) return false;
  const j = jobsAll()[i], h = horse(j.h);
  if (h && j.was) { h.d = j.was.d; h.grounds = j.was.grounds; h.temper = j.was.temper; }
  S.team.jobs.splice(i, 1); save(); return true;
}
const jobsOn = h => jobsAll().map((j, i) => ({ ...j, i })).filter(j => j.h === h.id);
// what a horse would be at its next age (the trainer's eye)
const nextAge = h => h.age < 4 ? { age: h.age + 1, rating: ratingAt(h, h.age + 1), trip: tripAt(h, h.age + 1) } : null;
// the trainer's notes on a horse: what's worth doing
function trainerNotes(h) {
  const out = [];
  if (h.temper === "keen") out.push("Keen: fights for his head early. Settle him and he's a different horse.");
  const runs = runsOf(h).length ? runsOf(h) : RACES.filter(r => (S.targets || {})[r.id] === h.id);
  for (const r of runs) { const d = tripAt(h, h.age), lo = Math.min(...d), hi = Math.max(...d);
    if (r.step < lo) out.push(`Best at ${tripText(d)}, but the ${r.name} is ${raceTrip(r)}: trip work would bring it nearer.`);
    else if (r.step > hi) out.push(`Best at ${tripText(d)}, but the ${r.name} is ${raceTrip(r)}: stretch him out.`); }
  if (h.grounds.length === 1) out.push(`Only likes ${h.grounds[0]} ground: a gamble on the weather.`);
  if (h.age < h.peakAge && h.age < 4) out.push(`Bred to peak at ${h.peakAge}: there may be more to come.`);
  return out.slice(0, 2);
}
// What a horse's trainer does for it in a race: a tune-up for this race, Stable Form on every horse
function trainFor(h, race) {
  const out = { boost: 0, shift: 0, cards: [] };
  for (const c of trainerCards()) if (c.kind === "form") { out.boost += FORM_BOOST[c.tier]; out.cards.push({ c, did: `+${FORM_BOOST[c.tier]}` }); }
  const t = race && tuneOf(race);
  if (t && t.h === h.id) { const b = tuneBoost(h, race); out.boost += b; out.cards.push({ c: trainerCards()[0], did: `+${b} tune-up` }); }
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
// the jockey's riding skills for the race engine (the two style jockeys)
function jockeyFields(race) {
  const c = bookedFor(race); if (!c) return {};
  return { jockey: JOCKEY_LEVEL[c.tier], ...((JOCKEY_EDGE[c.kind] || [])[c.tier] || {}) };
}
// his boost on the day: the Champion's everywhere, a specialist's where he fits; a trainer and jockey of the same trips
// add one more in races at those trips. The going counts once it's declared (before that, the Mud Lark is a hope).
function jockeyBoost(race, h) {
  const c = bookedFor(race); if (!c) return { boost: 0, why: "" };
  const K = JOCKEY_KINDS[c.kind], trip = raceTrip(race), going = goingKnown() ? CARD.going[race.day] : null;
  let b = 0;
  if (c.kind === "champion") b = CHAMPION_BOOST[c.tier];
  else if (K.trips && K.trips.includes(trip)) b = SPECIAL_BOOST[c.tier];
  else if (c.kind === "bigrace" && race.grade.startsWith("Group")) b = SPECIAL_BOOST[c.tier];
  else if (c.kind === "mudlark" && going && (going === "Softer" || going === "Heavy")) b = SPECIAL_BOOST[c.tier] + MUD_EXTRA;
  if (K.trips && K.trips.includes(trip) && trainerSpecs().some(t => t.spec === "trip" && t.trips.includes(trip))) b += PARTNER_BOOST;
  return { boost: b, why: b ? `+${b} ${cardName(c)}` : "" };
}
// does his specialism suit this horse and race? (style jockeys: the running style; trip jockeys: the race's trip)
function jockeySuits(c, h, race) {
  const K = JOCKEY_KINDS[c.kind];
  if (K.trips) return !race || K.trips.includes(raceTrip(race));
  if (c.kind === "bigrace") return !race || race.grade.startsWith("Group");
  const st = K.style; if (!st || !h || !h.style) return true;
  return st === "front" ? h.style === "front" || h.style === "prominent" : h.style === "midfield" || h.style === "holdup";
}
