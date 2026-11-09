// =====================================================================================================================
// The Race Lab (lab.html): test the race engine on any course and distance, going, field and riding tactics, and keep
// every figure. It runs the game's own engine (assets/engine/engine.js) on the game's course files, so what you learn
// here is exactly how races in the game behave. Engine numbers can be tuned for a test without touching the game.
//
// How a test is made: every chosen course & distance × every chosen going × every compared setting (for the starred
// horses) is run the chosen number of times. Race 1 of each combination uses the same seed and the same random
// opponents and draw, race 2 the next, and so on, so two settings are compared on identical races ("paired" races):
// the only difference is the thing being compared. Each race is rebuilt from the test's seed when it's needed again
// (details, watching it in 3D, the spreadsheet), so only the figures are stored.
// =====================================================================================================================
import { runRace, makeRandom, raceDayRating, flatSettings } from "../assets/engine/engine.js";

const COURSE_ID = "ascot";
const SETUP_KEY = "tb-lab-setup-v1", GAME_KEY = "tb-game-royal-ascot";
const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const clone = (o) => JSON.parse(JSON.stringify(o));
const uid = () => Math.random().toString(36).slice(2, 9);
const pct = (x, d = 1) => (Number.isFinite(x) ? (x * 100).toFixed(d) + "%" : "–");
const num = (x, d = 1) => (Number.isFinite(x) ? x.toFixed(d) : "–");
const thou = (n) => n.toLocaleString("en-GB");
const cap = (s) => (s ? s[0].toUpperCase() + s.slice(1) : s);

// ---------------------------------------------------------------------------------------------- the game's pieces
// The 54 silks in the game's order (img/silks/s01.webp … and their 3D versions, as js/rules.js -> SILKS, SILK3D)
const SILK3D = ["aga-khan", "alcohol-free", "amo-2", "ballydoyle-navy", "ballydoyle-orange", "ballydoyle-pink", "ballydoyle-purple", "black-white", "bradsell", "cheveley-park", "circus-maximus", "clipper-logistics", "desert-crown", "doha", "ebts-guard", "flamin-rib", "glen-sheil", "godolphin", "highclere", "judmonte", "king-power", "lake-forest", "liberty-lane", "lord-riddleford", "maroon-classic", "masrshamn", "middleham-park", "mill-reef", "nashwa", "nathaniel", "night-of-thunder", "oppenheimer", "orange-black", "phoenix-of-spain", "pink-white", "pink-white-blue", "poetic-flare", "purple-pink", "qatar", "red-white", "red-white-black", "royal", "sea-the-stars", "shadwell", "silkiewilie", "starlust", "strawbridge", "stradivarius", "swingalong", "wantan-2", "watnan", "white-blue", "wimbledon-hawkeye", "yellow-black-epilite"];
const silkImg = (i) => `img/silks/s${String(i + 1).padStart(2, "0")}.webp`;
const COATS = [["#7a4a2a", "#3a2214"], ["#4a2e1c", "#20140c"], ["#a3552c", "#6a3317"], ["#2b2523", "#141110"], ["#a8a6a0", "#6d6b66"]];
const NAME_A = ["Silver", "Royal", "Golden", "Northern", "Midnight", "Crimson", "Iron", "Highland", "Copper", "Shadow", "Velvet", "Thunder", "Gilded", "Ember", "Frost", "Morning", "Harbour", "Paper", "Quiet", "Wild", "Summer", "Distant", "Lucky", "Scarlet", "Hidden", "Brave", "Salt", "Amber", "Lantern", "Starlit"];
const NAME_B = ["Crown", "Echo", "Harbour", "Comet", "Ridge", "Sonnet", "Banner", "Sovereign", "Quarry", "Falcon", "Meadow", "Tempest", "Rampart", "Cadence", "Arrow", "Monarch", "Reverie", "Gambit", "Vista", "Pilgrim", "Ledger", "Beacon", "Mischief", "Rhapsody", "Charter", "Orchard", "Voyager", "Spire", "Verdict", "Kestrel"];
const STYLES = ["front", "prominent", "midfield", "holdup"];
const STYLE_NAME = { front: "Front-runner", prominent: "Prominent", midfield: "Midfield", holdup: "Hold-up" };
const FLEX = ["set", "adaptable", "versatile"];
const FLEX_NAME = { set: "Set", adaptable: "Adaptable", versatile: "Versatile" };
const INSTR = ["jockey", "front", "prominent", "midfield", "holdup"];
const INSTR_NAME = { jockey: "Leave it to the jockey", front: "Make the running", prominent: "Race prominently", midfield: "Settle midfield", holdup: "Hold up" };
const GOINGS = ["Heavy", "Softer", "Good", "Quicker", "Quick"];
const GOING_SHORT = { Heavy: "Hvy", Softer: "Sft", Good: "Gd", Quicker: "Qkr", Quick: "Qk" };
const PACES = ["slow", "even", "strong", "fast"];
const VARY = [
  ["none", "Nothing: run them as set"], ["tactic", "Every riding instruction (5)"], ["style", "Every running style (4)"],
  ["temper", "Calm and keen (2)"], ["flex", "Every flexibility (3)"], ["jockey", "Every jockey level (5)"], ["rating", "A range of ratings"],
];
const VARY_DIM = { none: "Setting", tactic: "Riding instruction", style: "Running style", temper: "Temperament", flex: "Flexibility", jockey: "Jockey", rating: "Rating" };

// ---------------------------------------------------------------------------------------------- the engine's data
const get = (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(p + " " + r.status); return r.json(); });
let COURSE, STALLS, STANDARDS, BASE, VIEW;
try {
  [COURSE, STALLS, STANDARDS, BASE, VIEW] = await Promise.all([`assets/course/${COURSE_ID}.json`, `assets/course/${COURSE_ID}-stalls.json`,
    `assets/course/${COURSE_ID}-standards.json`, "assets/engine/settings.json", `assets/course/${COURSE_ID}-view.json`].map(get));
} catch (e) {
  document.querySelector("main").innerHTML = `<div class="card empty"><h2>The race engine didn't load</h2><p>${esc(e.message)}</p></div>`;
  throw e;
}
const LADDER = BASE.horse.TRIP_LADDER, LADDER_F = BASE.horse.TRIP_LADDER_FURLONGS, MAX_RUNNERS = STALLS.maxRunners;
const TRIPS = Object.entries(VIEW.races).filter(([, v]) => v && typeof v === "object" && v.course)
  .map(([key, v]) => ({ key, label: v.label, course: v.course, distance: v.distance, start: v.start, straight: v.course === "straight" }));
const TRIP_BY = Object.fromEntries(TRIPS.map((t) => [t.key, t]));
const rungOf = (metres) => { const f = metres / 201.168; let b = 0; LADDER_F.forEach((r, i) => { if (Math.abs(r - f) < Math.abs(LADDER_F[b] - f)) b = i; }); return b; };
const pairLabel = (t) => (t == null || t < 0 ? "Any" : `${LADDER[t]}–${LADDER[t + 1]}`);

// ---------------------------------------------------------------------------------------------- engine numbers
// The numbers worth tuning, in plain words. Each is a path into settings.json; a test keeps its own tuned copy.
const arr = (p, labels, o = {}) => labels.map((l, i) => ({ p, i, l, ...o }));
const TUNE = [
  { sec: "The horse on the day" },
  { t: "Ground", h: "Rating points for the going: on a going it likes, then one, two and three steps away.", f: arr("horse.GROUND_POINTS", ["Likes it", "1 off", "2 off", "3 off"]) },
  { t: "Trip", h: "Points lost for each step outside its two best distances.", f: [{ p: "horse.TRIP_STEP_POINTS", l: "Per step" }] },
  { t: "Everyday form", h: "How far a horse's rating wobbles from race to race (a typical spread, in points).", f: [{ p: "bench.FORM_SD", l: "Spread" }] },
  { t: "A big day", h: "How often a horse runs well above itself, and by how many points.", f: [{ p: "bench.UP_P", l: "Chance", pct: 1 }, { p: "bench.UP_MIN", l: "From" }, { p: "bench.UP_MAX", l: "To" }] },
  { t: "A flop", h: "How often a horse runs well below itself, and by how many points.", f: [{ p: "bench.FLOP_P", l: "Chance", pct: 1 }, { p: "benchDefaults.FLOP_MIN", l: "From" }, { p: "benchDefaults.FLOP_MAX", l: "To" }] },
  { sec: "Pace" },
  { t: "Early pace", h: "How fast the early pace is for each pace level, against par (1 = par).", f: arr("bench.PACE", ["Slow", "Even", "Strong", "Fast"]) },
  { t: "What makes the pace", h: "Share of front-runners for a slow, strong or fast race; or a fast race when front-runners and prominent horses together reach the last figure.", f: [{ p: "rules.PACE_SLOW_FRONT", l: "Slow if at most", pct: 1 }, { p: "rules.PACE_STRONG_FRONT", l: "Strong if over", pct: 1 }, { p: "rules.PACE_FAST_FRONT", l: "Fast if at least", pct: 1 }, { p: "rules.PACE_FAST_ON_PACE", l: "Or on-pace at least", pct: 1 }] },
  { t: "Bends calm the pace", h: "How much of the pace's effect stays on the round course (1 = as much as the straight).", f: [{ p: "bench.PACE_ROUND_SCALE", l: "Share" }] },
  { t: "Run of the race", h: "Rating points for each running style at each pace (all 0 in the game for now).", matrix: true, f: [].concat(...PACES.map((pc, r) => STYLES.map((st, c) => ({ p: "bench.RUN_BOOST", i: [r, c], l: `${cap(pc)} · ${STYLE_NAME[st]}` })))) },
  { sec: "Running styles and the finish" },
  { t: "Final sprint extra", h: "Extra finishing speed by style (front-runner, prominent, midfield, hold-up).", f: arr("bench.BURST_STYLE", ["Front", "Prom.", "Mid.", "Hold-up"]) },
  { t: "When they kick", h: "Where each style's jockey goes for home, as a share of the usual point (lower = later).", f: arr("bench.KICK_STYLE", ["Front", "Prom.", "Mid.", "Hold-up"]) },
  { t: "Judging the line", h: "How near the line a jockey thinks he is when he kicks (lower = goes too soon and can empty).", f: arr("bench.KICK_REACH", ["Front", "Prom.", "Mid.", "Hold-up"]) },
  { t: "Keen horses", h: "Extra energy a keen horse burns when it's held back.", f: [{ p: "bench.KEEN_BURN", l: "Burn" }] },
  { t: "Jockeys read the pace", h: "Chance a jockey reads the likely pace from the racecard and changes position to suit.", f: [{ p: "bench.JOCKEY_READ", l: "Chance", pct: 1 }] },
  { sec: "The start and traffic" },
  { t: "Missing the break", h: "Chance of missing the break: keen horses, calm horses.", f: [{ p: "bench.MISS_P_KEEN", l: "Keen", pct: 1 }, { p: "bench.MISS_P_CALM", l: "Calm", pct: 1 }] },
  { t: "Slipstream", h: "Energy saved tucked in behind another horse (0 = none).", f: [{ p: "bench.DRAFT", l: "Saving", pct: 1 }] },
  { t: "Checked in traffic", h: "How much speed a horse loses when it runs into the back of another: straight, round.", f: [{ p: "bench.CHECK_DV_BY_COURSE", key: "straight", l: "Straight" }, { p: "bench.CHECK_DV_BY_COURSE", key: "round", l: "Round" }] },
  { t: "Switching for a run", h: "What it costs to switch out or in for a run.", f: [{ p: "bench.SWITCH_COST", l: "Cost" }] },
];
const pathParts = (p) => p.split(".");
function fieldValue(settings, f) {
  const [sec, key] = pathParts(f.p); let v = settings[sec][key];
  if (Array.isArray(f.i)) v = v[f.i[0]][f.i[1]]; else if (f.i != null) v = v[f.i];
  if (f.key) v = v[f.key];
  return v;
}
function settingsWith(tune) {
  const s = clone(BASE);
  for (const [p, v] of Object.entries(tune || {})) { const [sec, key] = pathParts(p); if (s[sec] && key in s[sec]) s[sec][key] = clone(v); }
  return s;
}
function hashStr(t) { let h = 2166136261; for (let i = 0; i < t.length; i++) { h ^= t.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36).slice(-6).padStart(6, "0"); }
const settingsTag = (tune) => hashStr(JSON.stringify(settingsWith(tune)));
const GAME_TAG = settingsTag({});
const dataWith = (tune) => ({ course: COURSE, stalls: STALLS, standards: STANDARDS, settings: settingsWith(tune) });

// ---------------------------------------------------------------------------------------------- the set-up
function newRunner(o = {}) {
  return { id: uid(), star: false, name: "NEW HORSE", rating: 100, mark: 100, style: "midfield", flex: "adaptable", temperament: "calm", trip: 3, goings: ["Good"], jockey: 0, instruction: "jockey", silk: Math.floor(Math.random() * SILK3D.length), coat: 0, ...o };
}
const DEFAULT = () => ({
  trips: ["mile"], goings: ["Good"], fill: true, size: 14, lo: 95, hi: 106, oppTrip: true, oppGoing: true, draw: "random", handicap: false,
  vary: { kind: "none", from: 95, to: 110, step: 5 }, runs: 200, name: "", notes: "", tune: {},
  field: [newRunner({ star: true, name: "TEST HORSE", rating: 104, silk: 27 })],
  view: null,
});
let U;
try { U = { ...DEFAULT(), ...JSON.parse(localStorage.getItem(SETUP_KEY) || "{}") }; } catch (e) { U = DEFAULT(); }
if (!Array.isArray(U.field)) U.field = DEFAULT().field;
const saveU = () => { try { localStorage.setItem(SETUP_KEY, JSON.stringify(U)); } catch (e) {} };

function variantsOf(v) {
  switch (v.kind) {
    case "tactic": return INSTR.map((x) => ({ label: INSTR_NAME[x], set: { instruction: x } }));
    case "style": return STYLES.map((x) => ({ label: STYLE_NAME[x], set: { style: x } }));
    case "temper": return ["calm", "keen"].map((x) => ({ label: cap(x), set: { temperament: x } }));
    case "flex": return FLEX.map((x) => ({ label: FLEX_NAME[x], set: { flex: x } }));
    case "jockey": return [1, 2, 3, 4, 5].map((j) => ({ label: `Jockey level ${j}`, set: { jockey: j } }));
    case "rating": {
      const a = Math.round(+v.from), b = Math.round(+v.to), s = Math.max(1, Math.round(+v.step) || 1), out = [];
      if (Number.isFinite(a) && Number.isFinite(b)) for (let r = Math.min(a, b); r <= Math.max(a, b) && out.length < 40; r += s) out.push({ label: `Rated ${r}`, set: { rating: r } });
      return out.length ? out : [{ label: "As set", set: {} }];
    }
    default: return [{ label: "As set", set: {} }];
  }
}
function combosOf(st) {
  const out = [], V = variantsOf(st.vary);
  for (const t of TRIPS) if (st.trips.includes(t.key)) for (const g of GOINGS) if (st.goings.includes(g)) V.forEach((_, vi) => out.push({ trip: t.key, going: g, vi }));
  return out;
}
const fieldCount = (st) => (st.fill ? Math.max(st.field.length, Math.min(MAX_RUNNERS, st.size)) : st.field.length);

// A random opponent: the same number of random draws whatever the course, going or setting, so race r has the same
// opposition everywhere in a test.
function randomOpp(rnd, st, step, used, avoidSilk) {
  const S = BASE, F = S.testField;
  const lo = Math.min(+st.lo, +st.hi), hi = Math.max(+st.lo, +st.hi);
  const rating = rnd.int(lo, hi + 1);
  const style = STYLES[rnd.choice(F.MIX)], flex = FLEX[rnd.choice(S.bench.FLEX_MIX)], temperament = rnd.chance(F.KEEN_P) ? "keen" : "calm";
  const up = rnd.chance(0.5), g0 = rnd.int(0, 4), gn = rnd.int(2, 4), markWobble = Math.round(rnd.normal(0, F.H_SD));
  let silk = rnd.int(0, SILK3D.length); if (avoidSilk.has(silk)) silk = (silk + 7) % SILK3D.length;
  const coat = rnd.int(0, COATS.length);
  let name = "";
  for (let t = 0; t < 300; t++) { name = (NAME_A[rnd.int(0, NAME_A.length)] + " " + NAME_B[rnd.int(0, NAME_B.length)]).toUpperCase(); if (!used.has(name)) break; }
  used.add(name);
  const lo2 = Math.max(0, Math.min(LADDER.length - 2, up ? step : step - 1));
  return { id: "opp", src: "opp", star: false, name, rating, mark: rating + markWobble, style, flex, temperament,
    trip: st.oppTrip ? lo2 : -1, goings: st.oppGoing ? GOINGS.slice(g0, g0 + gn) : [], jockey: 0, instruction: "jockey", silk, coat };
}
const engineRunner = (h) => ({
  name: h.name, rating: +h.rating, mark: h.mark === "" || h.mark == null ? +h.rating : +h.mark, style: h.style, flex: h.flex, temperament: h.temperament,
  trip: h.trip >= 0 ? [LADDER[h.trip], LADDER[h.trip + 1]] : undefined,
  goings: h.goings && h.goings.length ? h.goings.slice() : undefined,
  jockey: h.jockey ? +h.jockey : undefined, instruction: h.instruction || "jockey",
});
// Race k of a test, rebuilt from the test's seed: the race, the runners in stall order and what each one is.
function buildJob(T, k) {
  const st = T.setup, C = T._combos || (T._combos = combosOf(st)), V = T._vars || (T._vars = variantsOf(st.vary));
  const ci = Math.floor(k / st.runs), r = k % st.runs, c = C[ci], trip = TRIP_BY[c.trip], vv = V[c.vi];
  const rnd = makeRandom(`lab:${T.seedBase}:${r}`);
  let list = st.field.map((h) => ({ ...h, ...(h.star ? vv.set : {}), src: "field" }));
  if (st.fill) {
    const used = new Set(list.map((h) => h.name)), silks = new Set(list.map((h) => h.silk)), want = Math.min(MAX_RUNNERS, st.size) - list.length;
    for (let j = 0; j < want; j++) list.push(randomOpp(rnd, st, rungOf(trip.distance), used, silks));
  }
  list = list.slice(0, MAX_RUNNERS);
  if (st.draw === "random") for (let i = list.length - 1; i > 0; i--) { const j = Math.floor(rnd.next() * (i + 1)); [list[i], list[j]] = [list[j], list[i]]; }
  return {
    k, ci, r, c, V: vv, trip,
    race: { course: trip.course, distance: trip.distance, start: trip.start, going: c.going, seed: String(T.seedBase * 100000 + r), handicap: !!st.handicap },
    meta: list, runners: list.map(engineRunner),
  };
}

// ---------------------------------------------------------------------------------------------- the records (IndexedDB)
const DB = (() => {
  let p;
  const open = () => p || (p = new Promise((res, rej) => {
    const q = indexedDB.open("tb-race-lab", 1);
    q.onupgradeneeded = () => { const d = q.result; d.createObjectStore("tests", { keyPath: "id" }); d.createObjectStore("meta", { keyPath: "id" }); };
    q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error);
  }));
  const tx = (store, mode, fn) => open().then((d) => new Promise((res, rej) => {
    const t = d.transaction(store, mode), r = fn(t.objectStore(store));
    t.oncomplete = () => res(r && r.result); t.onerror = () => rej(t.error); t.onabort = () => rej(t.error);
  }));
  return {
    put: (s, v) => tx(s, "readwrite", (o) => o.put(v)), get: (s, id) => tx(s, "readonly", (o) => o.get(id)),
    all: (s) => tx(s, "readonly", (o) => o.getAll()), del: (s, id) => tx(s, "readwrite", (o) => o.delete(id)),
  };
})();
const plain = (T) => { const o = {}; for (const [k, v] of Object.entries(T)) if (!k.startsWith("_")) o[k] = v; return o; };
async function saveTest(T) {
  await DB.put("tests", plain(T));
  await DB.put("meta", metaOf(T));
}
function metaOf(T) {
  const { head } = analyse(T);
  return { id: T.id, name: T.name, notes: T.notes, created: T.created, total: T.total, done: head.races, stopped: !!T.stopped, tag: T.tag, tuned: Object.keys(T.tune || {}).length,
    setupText: setupText(T.setup), head: { best: head.bestWin, worst: head.worstWin, starWin: head.starWin, starTop3: head.starTop3, starRuns: head.starRuns, pace: head.pace, size: head.size } };
}
function setupText(st) {
  const t = st.trips.map((k) => TRIP_BY[k] ? TRIP_BY[k].label : k);
  const v = variantsOf(st.vary);
  return `${t.length > 3 ? t.length + " courses & distances" : t.join(", ")} · ${st.goings.join(", ")} · ${st.fill ? `fields of ${Math.min(MAX_RUNNERS, st.size)}` : st.field.length + " runners"}${st.handicap ? " · handicap" : ""}${st.vary.kind !== "none" ? ` · comparing ${v.length} ${VARY_DIM[st.vary.kind].toLowerCase()}s` : ""} · ${st.runs} each`;
}

// ---------------------------------------------------------------------------------------------- the figures
function analyse(T) {
  if (T._an) return T._an;
  const recs = [], races = [];
  for (let k = 0; k < T.total; k++) {
    const res = T.results[k]; if (!res || !res.ok) continue;
    const J = buildJob(T, k), n = J.meta.length, dr = res.rows.map((w) => w[2]);
    const best = Math.max(...dr), worst = Math.min(...dr);
    races.push({ k, J, res });
    J.meta.forEach((h, i) => {
      const w = res.rows[i], rank = 1 + dr.filter((x) => x > dr[i]).length;
      recs.push({ k, trip: J.trip.key, course: J.trip.straight ? "Straight" : "Round", going: J.c.going, v: J.V.label, pace: res.paceRun, n,
        star: !!h.star, src: h.src, horse: h.src === "field" ? h.name : "Random opponents", name: h.name, draw: i + 1,
        rating: +h.rating, mark: J.runners[i].mark, style: h.style, flex: h.flex, temper: h.temperament, jockey: +h.jockey || 0, instr: h.instruction || "jockey",
        tripPair: pairLabel(h.trip), liked: (h.goings || []).join("/"),
        place: w[0], behind: w[1], day: w[2], ground: w[3], steps: w[4], form: w[5], lost: w[6], ridden: STYLES[w[7]], missed: w[8], group: w[9],
        rank, gap: best - dr[i], top: dr[i] === best, bottom: dr[i] === worst });
    });
  }
  const R = races.length, wins = recs.filter((r) => r.place === 1), stars = recs.filter((r) => r.star);
  const head = {
    races: R, size: R ? recs.length / R : 0,
    bestWin: R ? wins.filter((r) => r.top).length / R : NaN,
    worstWin: R ? wins.filter((r) => r.bottom).length / R : NaN,
    pace: Object.fromEntries(PACES.map((p) => [p, R ? races.filter((x) => x.res.paceRun === p).length / R : 0])),
    margin: R ? races.reduce((a, x) => a + x.res.margin, 0) / R : NaN,
    vsPar: R ? races.reduce((a, x) => a + (x.res.time - x.res.par), 0) / R : NaN,
    missed: recs.length ? recs.filter((r) => r.missed).length / recs.length : NaN,
    lost: recs.length ? recs.reduce((a, r) => a + r.lost, 0) / recs.length : NaN,
    starRuns: stars.length, starWin: stars.length ? stars.filter((r) => r.place === 1).length / stars.length : NaN,
    starTop3: stars.length ? stars.filter((r) => r.place <= 3).length / stars.length : NaN,
    starPlace: stars.length ? stars.reduce((a, r) => a + r.place, 0) / stars.length : NaN,
  };
  T._an = { recs, races, head };
  return T._an;
}

// Ways to split the figures
const bucket = (x, edges, labels) => { for (let i = 0; i < edges.length; i++) if (x <= edges[i]) return labels[i]; return labels[labels.length - 1]; };
const DIMS = {
  none: { label: "Everything", get: () => "All" },
  horse: { label: "Horse", get: (r) => r.horse },
  v: { label: "Compared setting", get: (r) => r.v },
  trip: { label: "Course & distance", get: (r) => TRIP_BY[r.trip].label, order: TRIPS.map((t) => t.label) },
  course: { label: "Straight or round", get: (r) => r.course, order: ["Straight", "Round"] },
  going: { label: "Going", get: (r) => r.going, order: GOINGS },
  pace: { label: "Pace as run", get: (r) => cap(r.pace), order: PACES.map(cap) },
  style: { label: "Running style", get: (r) => STYLE_NAME[r.style], order: STYLES.map((s) => STYLE_NAME[s]) },
  ridden: { label: "Ridden as", get: (r) => STYLE_NAME[r.ridden], order: STYLES.map((s) => STYLE_NAME[s]) },
  instr: { label: "Riding instruction", get: (r) => INSTR_NAME[r.instr], order: INSTR.map((s) => INSTR_NAME[s]) },
  temper: { label: "Temperament", get: (r) => cap(r.temper), order: ["Calm", "Keen"] },
  flex: { label: "Flexibility", get: (r) => FLEX_NAME[r.flex], order: FLEX.map((s) => FLEX_NAME[s]) },
  ground: { label: "Ground (points on the day)", get: (r) => (r.ground > 0 ? "+" : "") + r.ground, order: ["+5", "0", "-5", "-10"] },
  steps: { label: "Trip (steps outside its best)", get: (r) => (r.steps === 0 ? "In its best trip" : r.steps === 1 ? "1 step off" : r.steps + " steps off"), order: ["In its best trip", "1 step off", "2 steps off", "3 steps off", "4 steps off"] },
  draw: { label: "Draw (thirds of the field)", get: (r) => (r.draw <= r.n / 3 ? "Low" : r.draw <= (2 * r.n) / 3 ? "Middle" : "High"), order: ["Low", "Middle", "High"] },
  rank: { label: "Rating rank in the field", get: (r) => bucket(r.rank, [1, 2, 3, 6, 10], ["Top rated", "2nd", "3rd", "4th–6th", "7th–10th", "11th+"]), order: ["Top rated", "2nd", "3rd", "4th–6th", "7th–10th", "11th+"] },
  gap: { label: "Points below the top rated", get: (r) => bucket(r.gap, [0, 3, 6, 10, 15], ["0 (top)", "1–3", "4–6", "7–10", "11–15", "16+"]), order: ["0 (top)", "1–3", "4–6", "7–10", "11–15", "16+"] },
  size: { label: "Field size", get: (r) => bucket(r.n, [8, 12, 16, 20], ["2–8", "9–12", "13–16", "17–20", "21–26"]), order: ["2–8", "9–12", "13–16", "17–20", "21–26"] },
  form: { label: "Form on the day", get: (r) => bucket(r.form, [-4, -1, 1, 4], ["Flop (−4 or worse)", "Below (−4 to −1)", "Usual (±1)", "Above (+1 to +4)", "Big day (+4 or more)"]), order: ["Flop (−4 or worse)", "Below (−4 to −1)", "Usual (±1)", "Above (+1 to +4)", "Big day (+4 or more)"] },
  jockey: { label: "Jockey", get: (r) => (r.jockey ? `Level ${r.jockey}` : "Random"), order: ["Random", "Level 1", "Level 2", "Level 3", "Level 4", "Level 5"] },
  missed: { label: "The break", get: (r) => (r.missed ? "Missed the break" : "Broke well"), order: ["Broke well", "Missed the break"] },
};
const METRICS = {
  win: { label: "Win %", of: (a) => a.wins / a.runs, fmt: (x) => pct(x) },
  xfair: { label: "Wins vs fair share (×)", of: (a) => a.wins / a.fair, fmt: (x) => (Number.isFinite(x) ? x.toFixed(2) + "×" : "–") },
  top3: { label: "Top 3 %", of: (a) => a.top3 / a.runs, fmt: (x) => pct(x) },
  place: { label: "Average place", of: (a) => a.place / a.runs, fmt: (x) => num(x, 1) },
  behind: { label: "Average lengths behind", of: (a) => a.behind / a.runs, fmt: (x) => num(x, 1) },
  lost: { label: "Lengths lost to traffic", of: (a) => a.lost / a.runs, fmt: (x) => num(x, 2) },
  runs: { label: "Runs", of: (a) => a.runs, fmt: (x) => thou(x) },
};
const WHO = { all: ["All runners", () => true], star: ["Starred horses", (r) => r.star], field: ["Horses on your list", (r) => r.src === "field"], opp: ["Random opponents", (r) => r.src === "opp"] };
const agg = () => ({ runs: 0, wins: 0, top3: 0, fair: 0, place: 0, behind: 0, lost: 0 });
const add = (a, r) => { a.runs++; a.wins += r.place === 1; a.top3 += r.place <= 3; a.fair += 1 / r.n; a.place += r.place; a.behind += r.behind; a.lost += r.lost; };
function pivot(T, view) {
  const { recs } = analyse(T), keep = WHO[view.who] ? WHO[view.who][1] : WHO.all[1];
  const D1 = DIMS[view.rows] || DIMS.none, D2 = DIMS[view.cols] || DIMS.none;
  const cells = new Map(), rowT = new Map(), colT = new Map(), all = agg();
  for (const r of recs) {
    if (!keep(r)) continue;
    const a = D1.get(r), b = D2.get(r);
    const key = a + "\u0001" + b;
    if (!cells.has(key)) cells.set(key, agg());
    add(cells.get(key), r);
    if (!rowT.has(a)) rowT.set(a, agg()); add(rowT.get(a), r);
    if (!colT.has(b)) colT.set(b, agg()); add(colT.get(b), r);
    add(all, r);
  }
  const vOrder = view.rows === "v" || view.cols === "v" ? T._vars || variantsOf(T.setup.vary) : null;
  const sortBy = (D, keys, key) => {
    const ord = key === "v" && vOrder ? vOrder.map((x) => x.label) : D.order;
    return [...keys].sort((x, y) => (ord ? (ord.indexOf(x) < 0 ? 99 : ord.indexOf(x)) - (ord.indexOf(y) < 0 ? 99 : ord.indexOf(y)) : 0) || String(x).localeCompare(String(y)));
  };
  return { D1, D2, rows: sortBy(D1, rowT.keys(), view.rows), cols: sortBy(D2, colT.keys(), view.cols), cells, rowT, colT, all };
}
// green above a fair share of wins, red below (needs 20 runs or more to colour)
function heat(a) {
  if (!a || a.runs < 20 || !a.fair) return "";
  const x = Math.max(-1.3, Math.min(1.3, Math.log2(Math.max(0.01, a.wins / a.fair)))) / 1.3;
  const c = x > 0 ? [169, 211, 182] : [231, 183, 170], k = Math.abs(x);
  return `background:rgb(${Math.round(255 + (c[0] - 255) * k)},${Math.round(255 + (c[1] - 255) * k)},${Math.round(255 + (c[2] - 255) * k)})`;
}

// ---------------------------------------------------------------------------------------------- the page
let TAB = "setup", CUR = null, RACE_PAGE = 0, RACE_FILTER = "all";
function toast(t) { const d = document.createElement("div"); d.className = "toast"; d.textContent = t; document.body.appendChild(d); setTimeout(() => d.remove(), 2600); }
function showTab(t) {
  TAB = t;
  document.querySelectorAll(".tab").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === t)));
  for (const k of ["setup", "results", "history"]) $("#tab-" + k).hidden = k !== t;
  $("#runbar").hidden = t !== "setup";
  if (t === "setup") renderSetup(); else if (t === "results") renderResults(); else renderHistory();
  scrollTo(0, 0);
}
document.querySelectorAll(".tab").forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));

// --- set up
const chip = (on, act, v, text, sm = "") => `<button class="chip" aria-pressed="${on}" data-act="${act}" data-v="${esc(v)}">${text}${sm ? `<small>${sm}</small>` : ""}</button>`;
const radio = (k, opts) => `<span class="radio">${opts.map(([v, t]) => `<button data-act="set" data-k="${k}" data-v="${v}" aria-pressed="${String(U[k]) === String(v)}">${t}</button>`).join("")}</span>`;
const opt = (list, cur, name = (x) => x) => list.map((x) => `<option value="${esc(x)}"${String(x) === String(cur) ? " selected" : ""}>${esc(name(x))}</option>`).join("");
function renderSetup() {
  const straight = TRIPS.filter((t) => t.straight), round = TRIPS.filter((t) => !t.straight);
  const vs = variantsOf(U.vary), tuned = Object.keys(U.tune || {}).length;
  $("#tab-setup").innerHTML = `
  <div class="grid2">
    <div class="card">
      <h2>Courses and distances</h2><p class="lede">Every one you pick is tested. Ascot, as in the game.</p>
      <div class="chip-h">Straight course</div><div class="chips">${straight.map((t) => chip(U.trips.includes(t.key), "trip", t.key, esc(t.label))).join("")}</div>
      <div class="chip-h">Round course</div><div class="chips">${round.map((t) => chip(U.trips.includes(t.key), "trip", t.key, esc(t.label))).join("")}</div>
      <div class="row" style="margin-top:10px"><button class="btn ghost sm" data-act="trips" data-v="all">All</button><button class="btn ghost sm" data-act="trips" data-v="straight">Straight</button><button class="btn ghost sm" data-act="trips" data-v="round">Round</button><button class="btn ghost sm" data-act="trips" data-v="none">None</button></div>
    </div>
    <div class="card">
      <h2>Going</h2><p class="lede">Every going you pick is tested.</p>
      <div class="chips">${GOINGS.map((g) => chip(U.goings.includes(g), "going", g, g)).join("")}</div>
      <div class="row" style="margin-top:10px"><button class="btn ghost sm" data-act="goings" data-v="all">All</button><button class="btn ghost sm" data-act="goings" data-v="Good">Good only</button></div>
      <div class="chip-h" style="margin-top:16px">Race type</div>
      ${radio("handicap", [["false", "Level (ratings)"], ["true", "Handicap (marks)"]])}
      <p class="small muted" style="margin:6px 0 0">In a handicap a horse races off 100 + (its rating on the day − its mark).</p>
    </div>
  </div>

  <div class="card">
    <div class="row sp"><div><h2>The field</h2><p class="lede" style="margin-bottom:0">Star the horses you're testing: their figures are picked out, the comparison below applies to them, and the first star is "your runner" in 3D.</p></div></div>
    <div class="row" style="margin:12px 0">
      <label class="row" style="gap:6px"><input type="checkbox" data-k="fill" ${U.fill ? "checked" : ""}> Fill the field with random opponents to</label>
      <input type="number" min="2" max="${MAX_RUNNERS}" data-k="size" value="${U.size}" ${U.fill ? "" : "disabled"}> runners,
      <span>rated</span><input type="number" data-k="lo" value="${U.lo}" ${U.fill ? "" : "disabled"}><span>to</span><input type="number" data-k="hi" value="${U.hi}" ${U.fill ? "" : "disabled"}>
    </div>
    <div class="row small" style="margin:-4px 0 10px;gap:14px">
      <label class="row" style="gap:6px"><input type="checkbox" data-k="oppTrip" ${U.oppTrip ? "checked" : ""} ${U.fill ? "" : "disabled"}> Opponents bred for the trip</label>
      <label class="row" style="gap:6px"><input type="checkbox" data-k="oppGoing" ${U.oppGoing ? "checked" : ""} ${U.fill ? "" : "disabled"}> Opponents have going likes</label>
      <span class="row" style="gap:6px">Draw ${radio("draw", [["random", "Random each race"], ["listed", "As listed"]])}</span>
    </div>
    <div class="scroll"><table class="field"><thead><tr><th></th><th></th><th>Name</th><th>Rating</th>${U.handicap ? "<th>Mark</th>" : ""}<th>Running style</th><th>Flexibility</th><th>Temper</th><th>Best trip</th><th>Likes the going</th><th>Jockey</th><th>Riding instruction</th><th></th></tr></thead>
    <tbody>${U.field.map(fieldRow).join("") || `<tr><td colspan="13" class="muted" style="padding:14px">No horses listed${U.fill ? ": the field will be all random opponents." : "."}</td></tr>`}</tbody></table></div>
    <div class="row" style="margin-top:10px">
      <button class="btn ghost sm" data-act="addHorse">+ Add a horse</button>
      <button class="btn ghost sm" data-act="addRandom">+ Add 4 random horses</button>
      <button class="btn ghost sm" data-act="stable">+ Horses from my game</button>
      <button class="btn ghost sm" data-act="clearField">Clear the list</button>
      <span class="small muted" style="margin-left:auto">${fieldCount(U)} runners a race (most ${MAX_RUNNERS})</span>
    </div>
  </div>

  <div class="card">
    <h2>Compare</h2><p class="lede">Try every starred horse a number of ways, on the very same races, to see what difference one thing makes.</p>
    <div class="row">
      <select data-k="varyKind">${VARY.map(([k, t]) => `<option value="${k}"${U.vary.kind === k ? " selected" : ""}>${t}</option>`).join("")}</select>
      ${U.vary.kind === "rating" ? `<span>from</span><input type="number" data-k="varyFrom" value="${U.vary.from}"><span>to</span><input type="number" data-k="varyTo" value="${U.vary.to}"><span>in steps of</span><input type="number" min="1" data-k="varyStep" value="${U.vary.step}">` : ""}
    </div>
    ${U.vary.kind !== "none" ? `<p class="small muted" style="margin:8px 0 0">${vs.map((v) => esc(v.label)).join(" · ")}</p>` : ""}
    ${U.vary.kind !== "none" && !U.field.some((h) => h.star) ? `<p class="note">Star at least one horse: the comparison is made on the starred horses.</p>` : ""}
  </div>

  <div class="card">
    <details class="tune" ${tuned ? "open" : ""}><summary><h2 style="display:inline">Engine numbers</h2>${tuned ? `<span class="pill gold">${tuned} tuned</span>` : `<span class="pill green">The game's own</span>`}</summary>
      <p class="lede" style="margin-top:8px">Change any of these for your tests only: the game itself is untouched. Each test keeps the numbers it ran with, and races watched in 3D use them too. A changed number is shown in gold with the game's value beneath.</p>
      ${TUNE.map(tuneRow).join("")}
      <div class="row" style="margin-top:14px"><button class="btn ghost sm" data-act="resetTune" ${tuned ? "" : "disabled"}>Back to the game's numbers</button></div>
    </details>
  </div>

  <div class="card">
    <h2>The test</h2>
    <div class="row" style="margin-top:8px;align-items:flex-end">
      <label class="f">Races for each combination<select data-k="runs">${opt([1, 10, 25, 50, 100, 200, 500, 1000, 2000], U.runs)}</select></label>
      <label class="f" style="flex:1;min-width:200px">Name (optional)<input type="text" data-k="name" value="${esc(U.name)}" placeholder="${esc(autoName(U))}"></label>
    </div>
    <label class="f" style="margin-top:10px">Notes (what you're checking, what you changed)<textarea data-k="notes">${esc(U.notes)}</textarea></label>
  </div>`;
  updateSum();
}
function fieldRow(h) {
  const L = LADDER.slice(0, -1).map((_, i) => i);
  return `<tr class="${h.star ? "starred" : ""}" data-row="${h.id}">
    <td><button class="star" data-act="star" data-id="${h.id}" aria-pressed="${!!h.star}" title="Star: a horse you're testing">★</button></td>
    <td><button class="silkbtn" data-act="silk" data-id="${h.id}" title="Change colours"><img src="${silkImg(h.silk)}" alt=""></button></td>
    <td><input class="nm" type="text" data-f="name" data-id="${h.id}" value="${esc(h.name)}"></td>
    <td><input type="number" data-f="rating" data-id="${h.id}" value="${h.rating}"></td>
    ${U.handicap ? `<td><input type="number" data-f="mark" data-id="${h.id}" value="${h.mark}"></td>` : ""}
    <td><select data-f="style" data-id="${h.id}">${opt(STYLES, h.style, (x) => STYLE_NAME[x])}</select></td>
    <td><select data-f="flex" data-id="${h.id}">${opt(FLEX, h.flex, (x) => FLEX_NAME[x])}</select></td>
    <td><select data-f="temperament" data-id="${h.id}">${opt(["calm", "keen"], h.temperament, cap)}</select></td>
    <td><select data-f="trip" data-id="${h.id}"><option value="-1"${h.trip < 0 ? " selected" : ""}>Any</option>${opt(L, h.trip, pairLabel)}</select></td>
    <td><span class="goingset">${GOINGS.map((g) => `<button data-act="rgo" data-id="${h.id}" data-v="${g}" aria-pressed="${(h.goings || []).includes(g)}" title="${g}">${GOING_SHORT[g]}</button>`).join("")}</span></td>
    <td><select data-f="jockey" data-id="${h.id}">${opt([0, 1, 2, 3, 4, 5], h.jockey, (x) => (x ? "Level " + x : "Random"))}</select></td>
    <td><select data-f="instruction" data-id="${h.id}">${opt(INSTR, h.instruction, (x) => INSTR_NAME[x])}</select></td>
    <td><button class="ic" data-act="dup" data-id="${h.id}" title="Copy">⧉</button><button class="ic" data-act="del" data-id="${h.id}" title="Remove">✕</button></td></tr>`;
}
function tuneRow(row) {
  if (row.sec) return `<div class="tune-sec">${row.sec}</div>`;
  const S = settingsWith(U.tune);
  const inp = (f) => {
    const v = fieldValue(S, f), g = fieldValue(BASE, f), ch = JSON.stringify(v) !== JSON.stringify(g), sc = f.pct ? 100 : 1;
    const show = (x) => +(x * sc).toFixed(f.pct ? 2 : 4);
    return `<label>${esc(f.l)}${f.pct ? " %" : ""}<input type="number" step="any" class="${ch ? "changed" : ""}" data-tune='${esc(JSON.stringify(f))}' value="${show(v)}">${ch ? `<span class="was">game: ${show(g)}</span>` : ""}</label>`;
  };
  if (row.matrix) {
    return `<div class="tune-row"><div class="tl"><b>${row.t}</b><span>${row.h}</span></div><div class="matrix"><span></span>${STYLES.map((s) => `<span>${STYLE_NAME[s]}</span>`).join("")}
      ${PACES.map((p, r) => `<span>${cap(p)}</span>${row.f.slice(r * 4, r * 4 + 4).map((f) => inp({ ...f, l: "" })).join("")}`).join("")}</div></div>`;
  }
  return `<div class="tune-row"><div class="tl"><b>${row.t}</b><span>${row.h}</span></div><div class="tune-parts">${row.f.map(inp).join("")}</div></div>`;
}
const autoName = (st) => {
  const t = st.trips.map((k) => (TRIP_BY[k] ? TRIP_BY[k].label : k));
  return `${t.length > 2 ? t.length + " trips" : t.join(" & ") || "No trip"}, ${st.goings.length > 2 ? st.goings.length + " goings" : st.goings.join(" & ")}${st.vary.kind !== "none" ? ", by " + VARY_DIM[st.vary.kind].toLowerCase() : ""}`;
};
const WORKERS = Math.max(1, Math.min(6, (navigator.hardwareConcurrency || 2) - 1));
function updateSum() {
  const C = combosOf(U), n = C.length * U.runs, per = fieldCount(U);
  const secs = (n * 0.045 * Math.max(0.6, per / 14)) / WORKERS;
  const nT = U.trips.length, nG = U.goings.length, nV = variantsOf(U.vary).length;
  const ok = n > 0 && per >= 2;
  $("#runSum").innerHTML = ok
    ? `<b>${thou(n)} races</b> · ${nT} course${nT === 1 ? "" : "s"} × ${nG} going${nG === 1 ? "" : "s"}${nV > 1 ? ` × ${nV} settings` : ""} × ${U.runs} · about ${secs < 60 ? Math.max(1, Math.round(secs)) + " s" : Math.round(secs / 60) + " min"}${Object.keys(U.tune).length ? ` · <span class="pill gold">tuned numbers</span>` : ""}`
    : per < 2 ? "A race needs at least 2 runners: add horses or fill the field." : "Pick at least one course & distance and one going.";
  $("#runAll").disabled = !ok || n > 100000; $("#runOne").disabled = !ok;
  if (n > 100000) $("#runSum").innerHTML += ` · <span class="pill red">too many: 100,000 at most</span>`;
}
const byId = (id) => U.field.find((h) => h.id === id);
$("#tab-setup").addEventListener("click", (e) => {
  const b = e.target.closest("[data-act]"); if (!b) return;
  const a = b.dataset.act, v = b.dataset.v, h = b.dataset.id ? byId(b.dataset.id) : null;
  const tog = (list, x) => (list.includes(x) ? list.filter((y) => y !== x) : list.concat(x));
  switch (a) {
    case "trip": U.trips = tog(U.trips, v); break;
    case "trips": U.trips = v === "all" ? TRIPS.map((t) => t.key) : v === "none" ? [] : TRIPS.filter((t) => t.straight === (v === "straight")).map((t) => t.key); break;
    case "going": U.goings = tog(U.goings, v); break;
    case "goings": U.goings = v === "all" ? GOINGS.slice() : [v]; break;
    case "set": U[b.dataset.k] = v === "true" ? true : v === "false" ? false : v; break;
    case "star": h.star = !h.star; break;
    case "silk": h.silk = (h.silk + (e.shiftKey ? SILK3D.length - 1 : 1)) % SILK3D.length; break;
    case "rgo": h.goings = tog(h.goings || [], v).sort((x, y) => GOINGS.indexOf(x) - GOINGS.indexOf(y)); break;
    case "dup": U.field.splice(U.field.indexOf(h) + 1, 0, { ...clone(h), id: uid(), name: h.name + " II" }); break;
    case "del": U.field = U.field.filter((x) => x !== h); break;
    case "addHorse": if (U.field.length < MAX_RUNNERS) U.field.push(newRunner({ name: `HORSE ${U.field.length + 1}` })); break;
    case "addRandom": {
      const rnd = makeRandom("add:" + Math.random()), used = new Set(U.field.map((x) => x.name)), silks = new Set(U.field.map((x) => x.silk));
      for (let j = 0; j < 4 && U.field.length < MAX_RUNNERS; j++) { const o = randomOpp(rnd, { ...U, oppTrip: true, oppGoing: true }, rungOf((TRIP_BY[U.trips[0]] || TRIPS[3]).distance), used, silks); U.field.push({ ...o, id: uid(), src: undefined }); }
      break;
    }
    case "stable": addFromGame(); break;
    case "clearField": if (!U.field.length || confirm("Remove every horse from the list?")) U.field = []; break;
    case "resetTune": U.tune = {}; break;
    default: return;
  }
  saveU(); renderSetup();
});
$("#tab-setup").addEventListener("change", onInput);
$("#tab-setup").addEventListener("input", (e) => { if (e.target.matches("input[type=text], textarea")) onInput(e); });
function onInput(e) {
  const t = e.target;
  if (t.dataset.tune) { setTune(JSON.parse(t.dataset.tune), t.value); saveU(); renderSetup(); return; }
  if (t.dataset.f) {
    const h = byId(t.dataset.id); if (!h) return;
    const f = t.dataset.f;
    h[f] = ["rating", "mark", "trip", "jockey"].includes(f) ? +t.value : f === "name" ? t.value.toUpperCase() : t.value;
    if (f === "name") t.value = h.name;
    saveU(); updateSum(); return;
  }
  const k = t.dataset.k; if (!k) return;
  if (k === "varyKind") { U.vary.kind = t.value; saveU(); renderSetup(); return; }
  if (k === "varyFrom" || k === "varyTo" || k === "varyStep") { U.vary[k.slice(4).toLowerCase()] = +t.value; saveU(); if (e.type === "change") renderSetup(); return; }
  if (t.type === "checkbox") { U[k] = t.checked; saveU(); renderSetup(); return; }
  U[k] = t.type === "number" || k === "runs" ? +t.value : t.value;
  if (k === "size") U.size = Math.max(2, Math.min(MAX_RUNNERS, U.size));
  saveU();
  if (k === "size" || k === "runs") renderSetup(); else updateSum();
}
function setTune(f, raw) {
  let x = +raw; if (!Number.isFinite(x)) return;
  if (f.pct) x /= 100;
  const S = settingsWith(U.tune), [sec, key] = pathParts(f.p);
  let v = clone(S[sec][key]);
  if (Array.isArray(f.i)) v[f.i[0]][f.i[1]] = x; else if (f.i != null) v[f.i] = x; else if (f.key) v[f.key] = x; else v = x;
  if (JSON.stringify(v) === JSON.stringify(BASE[sec][key])) delete U.tune[f.p]; else U.tune[f.p] = v;
}
function addFromGame() {
  let S; try { S = JSON.parse(localStorage.getItem(GAME_KEY) || "null"); } catch (e) { S = null; }
  const stable = S && Array.isArray(S.stable) ? S.stable.filter((h) => h && Array.isArray(h.r)) : [];
  if (!stable.length) { toast("No horses in your game on this device yet."); return; }
  let added = 0;
  for (const h of stable) {
    if (U.field.length >= MAX_RUNNERS) break;
    const a = Math.min(4, Math.max(2, h.age || 3)) - 2, d = Array.isArray(h.d && h.d[a]) ? h.d[a] : [];
    U.field.push(newRunner({ star: true, name: String(h.name || "HORSE").toUpperCase(), rating: h.r[a], mark: h.r[a],
      style: STYLES.includes(h.style) ? h.style : "midfield", flex: FLEX.includes(h.flex) ? h.flex : "adaptable", temperament: h.temper === "keen" ? "keen" : "calm",
      trip: d.length ? Math.min(LADDER.length - 2, Math.min(...d)) : -1, goings: Array.isArray(h.grounds) ? h.grounds.filter((g) => GOINGS.includes(g)) : [],
      silk: Math.min(SILK3D.length - 1, S.silks || 0) }));
    added++;
  }
  toast(`${added} horse${added === 1 ? "" : "s"} added from your game, at today's age.`);
}

// --- running a test
function makeWorker(data) {
  // a helper running in the background; if the browser can't start one, the races run here on the page instead
  return new Promise((res) => {
    let w;
    const fallback = () => {
      const d = { ...data }, fake = { onmessage: null, terminate() { this.dead = true; }, postMessage(m) {
        if (m.type !== "jobs") return;
        setTimeout(() => { if (fake.dead) return; const out = m.jobs.map((j) => runHere(j, d)); fake.onmessage && fake.onmessage({ data: { type: "done", batch: m.batch, out } }); }, 0);
      } };
      res(fake);
    };
    try { w = new Worker(new URL("./lab-worker.js", import.meta.url), { type: "module" }); } catch (e) { return fallback(); }
    const t = setTimeout(() => { w.terminate(); fallback(); }, 8000);
    w.onerror = () => { clearTimeout(t); w.terminate(); fallback(); };
    w.onmessage = (e) => { if (e.data && e.data.type === "inited") { clearTimeout(t); w.onerror = null; res(w); } };
    w.postMessage({ type: "init", data });
  });
}
const STYLE_IX = { front: 0, prominent: 1, midfield: 2, holdup: 3 };
function runHere(job, data) {
  try {
    const P = flatSettings(data.settings), { result: R } = runRace(job.race, job.runners, data, { timeline: false });
    const missed = new Set(R.events.filter((e) => e.kind === "missed the break").map((e) => e.runner)), rows = [];
    for (const p of R.placed) {
      const d = raceDayRating(P, job.runners[p.runner], { ...job.race, going: R.race.going });
      rows[p.runner] = [p.place, p.behind, d.rating, d.ground, d.tripSteps, p.form, p.lostLengths, STYLE_IX[p.ridden], missed.has(p.runner) ? 1 : 0, p.group];
    }
    return { k: job.k, ok: true, paceExp: R.pace.expected, paceRun: R.pace.run, groups: R.pace.groups.length, time: R.winningTime, par: R.parTime, margin: R.placed[1] ? R.placed[1].margin : 0, rows };
  } catch (err) { return { k: job.k, ok: false, error: String(err.message || err) }; }
}
let RUN = null;
async function runTest() {
  const st = clone(U); delete st.tune; delete st.name; delete st.notes; delete st.view;
  const C = combosOf(st), total = C.length * st.runs;
  if (!total) return;
  const T = { id: uid() + Date.now().toString(36), name: U.name.trim() || autoName(U), notes: U.notes, created: Date.now(), seedBase: 1 + Math.floor(Math.random() * 89999),
    setup: st, tune: clone(U.tune), tag: settingsTag(U.tune), total, results: new Array(total).fill(null) };
  const data = { course: COURSE, stalls: STALLS, standards: STANDARDS, settings: settingsWith(T.tune) };
  const box = document.createElement("div"); box.className = "prog";
  box.innerHTML = `<div class="prog-box"><div class="k">Race Lab</div><h2 style="margin:4px 0 0">${esc(T.name)}</h2><div class="bar"><i id="pbar"></i></div><div class="row sp small"><span id="ptext">Starting…</span><span id="peta"></span></div><div class="row" style="margin-top:14px"><button class="btn ghost" id="pstop">Stop and keep what's run</button></div></div>`;
  document.body.appendChild(box);
  $("#pstop").onclick = () => { RUN.stop = true; $("#pstop").disabled = true; $("#ptext").textContent = "Stopping…"; };
  const ws = await Promise.all(Array.from({ length: Math.min(WORKERS, Math.ceil(total / 20)) }, () => makeWorker(data)));
  const CHUNK = 20, t0 = performance.now();
  let next = 0, done = 0, failed = 0, firstError = "";
  await new Promise((resolve) => {
    let busy = 0;
    const feed = (w) => {
      if (RUN.stop || next >= total) { if (busy === 0) resolve(); return; }
      const ks = []; for (let j = 0; j < CHUNK && next < total; j++) ks.push(next++);
      busy++;
      w.postMessage({ type: "jobs", batch: ks[0], jobs: ks.map((k) => { const J = buildJob(T, k); return { k, race: J.race, runners: J.runners }; }) });
    };
    for (const w of ws) {
      w.onmessage = (e) => {
        const m = e.data; if (!m || m.type !== "done") return;
        busy--;
        for (const o of m.out) { T.results[o.k] = o; done++; if (!o.ok) { failed++; firstError = firstError || o.error; } }
        const el = (performance.now() - t0) / 1000, left = done ? (el / done) * (total - done) : 0;
        $("#pbar").style.width = (100 * done) / total + "%";
        $("#ptext").textContent = `${thou(done)} of ${thou(total)} races`;
        $("#peta").textContent = done < total ? `about ${left < 60 ? Math.ceil(left) + " s" : Math.ceil(left / 60) + " min"} to go` : "";
        feed(w);
        if (busy === 0 && (RUN.stop || next >= total)) resolve();
      };
      feed(w);
    }
  });
  ws.forEach((w) => w.terminate());
  box.remove();
  T.stopped = done < total;
  if (failed) toast(`${failed} race${failed === 1 ? "" : "s"} couldn't be run: ${firstError}`);
  if (!done) return;
  CUR = T; RACE_PAGE = 0; RACE_FILTER = "all";
  try { await saveTest(T); } catch (e) { toast("Couldn't keep this test in the browser's storage: " + e.message); }
  showTab("results");
}
$("#runAll").onclick = () => {
  if (RUN) return;
  RUN = { stop: false };
  runTest().catch((e) => { document.querySelectorAll(".prog").forEach((x) => x.remove()); toast("The test stopped: " + (e.message || e)); }).finally(() => { RUN = null; });
};
$("#runOne").onclick = () => {
  // one race of the first combination, a new seed each time, straight into the 3D view
  const st = clone(U); delete st.tune; st.runs = 1;
  const T = { id: "one", name: "One race", setup: st, tune: clone(U.tune), seedBase: 1 + Math.floor(Math.random() * 89999), total: 1, results: [] };
  const C = combosOf(st); if (!C.length) return;
  T._combos = [C[0]];
  watch(T, 0);
};

// --- results
function tile(big, label, sub = "") { return `<div class="tile"><b>${big}</b><span>${label}</span>${sub ? `<em>${sub}</em>` : ""}</div>`; }
function defaultView(T) {
  const stars = T.setup.field.some((h) => h.star), vary = T.setup.vary.kind !== "none";
  if (stars) return { who: "star", rows: vary ? "v" : "horse", cols: T.setup.trips.length > 1 ? "trip" : T.setup.goings.length > 1 ? "going" : "none", metric: "win" };
  return { who: "all", rows: "pace", cols: "ridden", metric: "xfair" };
}
const PRESETS = [
  ["Your starred horses", (T) => ({ who: "star", rows: T.setup.vary.kind !== "none" ? "v" : "horse", cols: "trip", metric: "win" })],
  ["Starred: going × distance", () => ({ who: "star", rows: "trip", cols: "going", metric: "win" })],
  ["Pace and running style", () => ({ who: "all", rows: "pace", cols: "ridden", metric: "xfair" })],
  ["Style by course & distance", () => ({ who: "all", rows: "trip", cols: "ridden", metric: "xfair" })],
  ["Ground", () => ({ who: "all", rows: "ground", cols: "none", metric: "xfair" })],
  ["Trip fit", () => ({ who: "all", rows: "steps", cols: "course", metric: "xfair" })],
  ["Draw", () => ({ who: "all", rows: "draw", cols: "trip", metric: "xfair" })],
  ["Rating rank", () => ({ who: "all", rows: "rank", cols: "course", metric: "win" })],
  ["Temperament and pace", () => ({ who: "all", rows: "temper", cols: "pace", metric: "xfair" })],
  ["Form on the day", () => ({ who: "all", rows: "form", cols: "none", metric: "win" })],
];
function renderResults() {
  const box = $("#tab-results");
  if (!CUR) { box.innerHTML = `<div class="card empty"><h2>No test open</h2><p>Run a test from Set up, or open one from your Records.</p><button class="btn" id="goSetup">Set up a test</button></div>`; $("#goSetup").onclick = () => showTab("setup"); return; }
  const T = CUR, { head, races } = analyse(T);
  if (!T._view) T._view = defaultView(T);
  const V = T._view, tuned = Object.keys(T.tune || {}).length, hasStars = T.setup.field.some((h) => h.star);
  const P = pivot(T, V);
  const cellHTML = (a) => (a ? `${METRICS[V.metric].fmt(METRICS[V.metric].of(a))}${V.metric !== "runs" ? `<small>${thou(a.runs)} runs</small>` : ""}` : "");
  const pace = PACES.map((p) => `${cap(p)} ${pct(head.pace[p], 0)}`).join(" · ");
  box.innerHTML = `
  <div class="card">
    <div class="row sp" style="align-items:flex-start">
      <div style="flex:1;min-width:240px"><div class="k">${new Date(T.created).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })} · ${thou(head.races)} races${T.stopped ? " (stopped early)" : ""}</div>
        <input type="text" id="tName" value="${esc(T.name)}" style="font-family:var(--serif);font-size:24px;font-weight:700;border:0;background:transparent;padding:2px 0;width:100%">
        <div class="small muted">${esc(setupText(T.setup))} · ${tuned ? `<span class="pill gold">${tuned} engine number${tuned === 1 ? "" : "s"} tuned</span>` : `<span class="pill green">the game's numbers</span>`} <span class="muted">rules version ${T.tag}${T.tag === GAME_TAG ? "" : tuned ? "" : " (the game's numbers have changed since)"}</span></div>
      </div>
      <div class="row">
        <button class="btn sm" data-act="csv">Spreadsheet (every runner)</button>
        <button class="btn ghost sm" data-act="copy">Copy summary</button>
        <button class="btn ghost sm" data-act="again">Set up again</button>
      </div>
    </div>
    <textarea id="tNotes" placeholder="Notes" style="margin-top:10px">${esc(T.notes || "")}</textarea>
    ${tuned ? `<p class="small muted" style="margin:6px 0 0">Tuned: ${esc(tuneText(T.tune))}</p>` : ""}
    <div class="tiles">
      ${hasStars ? tile(pct(head.starWin), "Starred horses win", `${pct(head.starTop3)} top 3 · average place ${num(head.starPlace, 1)}`) : ""}
      ${tile(pct(head.bestWin), "Top-rated horse wins", "On the day's rating. Aim about 30–35%")}
      ${tile(pct(head.worstWin), "Lowest-rated wins", "Aim about 1 in 20 when things suit")}
      ${tile(num(head.size, 1), "Runners a race")}
      ${tile(num(head.margin, 2) + " L", "Average winning margin")}
      ${tile((head.vsPar >= 0 ? "+" : "") + num(head.vsPar, 1) + " s", "Winning time against par")}
      ${tile(pct(head.missed, 1), "Missed the break", `${num(head.lost, 2)} L lost to traffic a runner`)}
      ${tile(pct(head.pace.fast + head.pace.strong, 0), "Strong or fast pace", pace)}
    </div>
  </div>

  <div class="card">
    <h2>Break it down</h2><p class="lede">Pick who to look at, what goes down the side and across the top, and the figure. Colour shows wins against a fair share (each runner's 1 in the field size): green more, red fewer.</p>
    <div class="presets">${PRESETS.map(([t], i) => `<button class="btn ghost sm" data-act="preset" data-v="${i}">${t}</button>`).join("")}</div>
    <div class="row">
      <label class="f">Who<select data-view="who">${Object.entries(WHO).map(([k, [t]]) => `<option value="${k}"${V.who === k ? " selected" : ""}>${t}</option>`).join("")}</select></label>
      <label class="f">Down the side<select data-view="rows">${dimOpts(V.rows, T)}</select></label>
      <label class="f">Across the top<select data-view="cols">${dimOpts(V.cols, T)}</select></label>
      <label class="f">Figure<select data-view="metric">${Object.entries(METRICS).map(([k, m]) => `<option value="${k}"${V.metric === k ? " selected" : ""}>${m.label}</option>`).join("")}</select></label>
      <span style="margin-left:auto" class="row"><button class="btn ghost sm" data-act="copyTable">Copy table</button><button class="btn ghost sm" data-act="csvTable">Table as spreadsheet</button></span>
    </div>
    <div class="scroll" style="margin-top:10px"><table class="pivot"><thead><tr><th>${esc(P.D1.label)}</th>${P.cols.map((c) => `<th class="c">${esc(c)}</th>`).join("")}${P.cols.length > 1 ? `<th class="c">All</th>` : ""}</tr></thead>
      <tbody>${P.rows.map((r) => `<tr><td class="rl">${esc(r)}</td>${P.cols.map((c) => { const a = P.cells.get(r + "\u0001" + c); return `<td class="c" style="${heat(a)}">${cellHTML(a)}</td>`; }).join("")}${P.cols.length > 1 ? `<td class="c" style="${heat(P.rowT.get(r))}">${cellHTML(P.rowT.get(r))}</td>` : ""}</tr>`).join("")}
      ${P.rows.length > 1 ? `<tr class="tot"><td>All</td>${P.cols.map((c) => `<td class="c">${cellHTML(P.colT.get(c))}</td>`).join("")}${P.cols.length > 1 ? `<td class="c">${cellHTML(P.all)}</td>` : ""}</tr>` : ""}</tbody></table></div>
    ${P.D2 !== DIMS.none ? `<p class="small muted" style="margin:6px 0 0">Across the top: ${esc(P.D2.label)}.</p>` : ""}
    <div class="legend"><i></i> fewer wins than a fair share · more (coloured from 20 runs)</div>
  </div>

  <div class="card">
    <div class="row sp"><div><h2>The races</h2><p class="lede" style="margin-bottom:0">Open any race for its full result and what happened, or watch it in 3D: it's run again from its seed, so it's the same race.</p></div>
      <label class="f">Show<select id="rFilter">${opt(["all", "starWon", "starPlaced", "starLost", "upset"], RACE_FILTER, (x) => ({ all: "Every race", starWon: "A starred horse won", starPlaced: "A starred horse placed 2nd–3rd", starLost: "Starred horses out of the first 3", upset: "Won by one of the three lowest rated" })[x])}</select></label></div>
    ${raceTable(T, races)}
  </div>`;
  box.querySelectorAll("[data-view]").forEach((s) => (s.onchange = () => { V[s.dataset.view] = s.value; renderResults(); }));
  $("#rFilter").onchange = (e) => { RACE_FILTER = e.target.value; RACE_PAGE = 0; renderResults(); };
  $("#tName").onchange = (e) => { T.name = e.target.value.trim() || T.name; DB.put("meta", metaOf(T)); DB.put("tests", plain(T)); };
  $("#tNotes").onchange = (e) => { T.notes = e.target.value; DB.put("meta", metaOf(T)); DB.put("tests", plain(T)); };
}
function dimOpts(cur, T) {
  return Object.entries(DIMS).filter(([k]) => k !== "v" || T.setup.vary.kind !== "none")
    .map(([k, d]) => `<option value="${k}"${cur === k ? " selected" : ""}>${k === "v" ? VARY_DIM[T.setup.vary.kind] + " (compared)" : d.label}</option>`).join("");
}
function tuneText(tune) {
  return Object.entries(tune).map(([p, v]) => `${p.split(".")[1]} ${JSON.stringify(v)} (game ${JSON.stringify(BASE[p.split(".")[0]][p.split(".")[1]])})`).join("; ");
}
function raceTable(T, races) {
  const starOf = (x) => x.J.meta.map((h, i) => (h.star ? x.res.rows[i][0] : 0)).filter(Boolean);
  const keep = {
    all: () => true, starWon: (x) => starOf(x).includes(1), starPlaced: (x) => starOf(x).some((p) => p === 2 || p === 3),
    starLost: (x) => starOf(x).length && starOf(x).every((p) => p > 3),
    upset: (x) => { const w = x.res.rows.findIndex((r) => r[0] === 1), dr = x.res.rows.map((r) => r[2]); return dr.filter((d) => d < dr[w]).length <= 2 && dr.length > 3; },
  }[RACE_FILTER] || (() => true);
  const list = races.filter(keep), per = 25, pages = Math.max(1, Math.ceil(list.length / per));
  RACE_PAGE = Math.min(RACE_PAGE, pages - 1);
  const show = list.slice(RACE_PAGE * per, RACE_PAGE * per + per), vary = T.setup.vary.kind !== "none";
  if (!list.length) return `<p class="muted" style="margin-top:12px">No races to show.</p>`;
  return `<div class="scroll" style="margin-top:10px"><table class="races"><thead><tr><th></th><th>No.</th><th>Course & distance</th><th>Going</th>${vary ? `<th>${VARY_DIM[T.setup.vary.kind]}</th>` : ""}<th>Pace</th><th class="c">Runners</th><th>Winner</th><th>Starred</th><th class="c">Won by</th><th class="c">vs par</th></tr></thead><tbody>
    ${show.map((x) => {
      const w = x.res.rows.findIndex((r) => r[0] === 1), h = x.J.meta[w], st = x.J.meta.map((m, i) => (m.star ? `${esc(m.name)} ${ord(x.res.rows[i][0])}` : "")).filter(Boolean).join(", ");
      return `<tr><td><button class="btn sm" data-act="watch" data-k="${x.k}">Watch</button> <button class="btn ghost sm" data-act="race" data-k="${x.k}">Details</button></td><td class="n">${x.k + 1}</td><td>${esc(x.J.trip.label)}</td><td>${x.J.c.going}</td>${vary ? `<td>${esc(x.J.V.label)}</td>` : ""}<td>${cap(x.res.paceRun)}${x.res.paceExp !== x.res.paceRun ? ` <span class="muted small">(card: ${x.res.paceExp})</span>` : ""}</td><td class="n c">${x.J.meta.length}</td>
        <td class="${h.star ? "mine" : ""}">${esc(h.name)} <span class="muted small">${x.res.rows[w][2]} · ${STYLE_NAME[h.style]}</span></td><td>${st || "–"}</td><td class="n c">${num(x.res.margin, 2)} L</td><td class="n c">${(x.res.time - x.res.par >= 0 ? "+" : "") + num(x.res.time - x.res.par, 1)} s</td></tr>`;
    }).join("")}</tbody></table></div>
    ${pages > 1 ? `<div class="row" style="margin-top:10px"><button class="btn ghost sm" data-act="page" data-v="-1" ${RACE_PAGE ? "" : "disabled"}>← Earlier</button><span class="small muted">Page ${RACE_PAGE + 1} of ${pages} · ${thou(list.length)} races</span><button class="btn ghost sm" data-act="page" data-v="1" ${RACE_PAGE < pages - 1 ? "" : "disabled"}>Later →</button></div>` : ""}`;
}
const ord = (n) => n + (n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th");
$("#tab-results").addEventListener("click", (e) => {
  const b = e.target.closest("[data-act]"); if (!b || !CUR) return;
  const T = CUR;
  switch (b.dataset.act) {
    case "preset": T._view = PRESETS[+b.dataset.v][1](T); if (!T.setup.field.some((h) => h.star) && T._view.who === "star") T._view.who = "all"; if (T._view.rows === "v" && T.setup.vary.kind === "none") T._view.rows = "horse"; renderResults(); break;
    case "csv": download(`${fileName(T.name)}.csv`, csvOf(T)); break;
    case "csvTable": download(`${fileName(T.name)} - table.csv`, tableCsv(T)); break;
    case "copy": copy(summaryText(T)); break;
    case "copyTable": copy(tableText(T)); break;
    case "again": U = { ...U, ...clone(T.setup), tune: clone(T.tune || {}), name: "", notes: T.notes || "" }; saveU(); showTab("setup"); toast("This test's set-up is loaded: change what you like and run it again."); break;
    case "page": RACE_PAGE += +b.dataset.v; renderResults(); break;
    case "race": openRace(T, +b.dataset.k); break;
    case "watch": watch(T, +b.dataset.k); break;
  }
});
function openRace(T, k) {
  const J = buildJob(T, k), { result: R } = runRace(J.race, J.runners, dataWith(T.tune), { timeline: false });
  const P = flatSettings(settingsWith(T.tune));
  const d = document.createElement("div"); d.className = "drawer";
  d.innerHTML = `<div class="drawer-in"><div class="row sp"><div class="k">${esc(T.name)} · race ${k + 1}</div><button class="btn ghost sm" data-x>Close</button></div>
    <h2 style="margin:6px 0 2px">${esc(J.trip.label)} · ${J.race.going}${J.V.label !== "As set" ? ` · ${esc(J.V.label)}` : ""}</h2>
    <p class="small muted" style="margin:0 0 10px">${J.meta.length} runners · pace on the card ${R.pace.expected}, as run ${R.pace.run}${R.pace.groups.length > 1 ? ` · ${R.pace.groups.length} groups (${R.pace.groups.map((g) => g.pace).join(", ")})` : ""} · won in ${R.winningTime.toFixed(2)} s (par ${R.parTime.toFixed(2)}) · seed ${J.race.seed}</p>
    <div class="scroll"><table><thead><tr><th>Pl.</th><th>Stall</th><th>Horse</th><th class="c">Rating</th><th class="c">On the day</th><th class="c">Ground</th><th class="c">Trip</th><th class="c">Form</th><th>Style → ridden</th><th class="c">Behind</th><th class="c">Traffic</th></tr></thead><tbody>
    ${R.placed.map((p) => { const h = J.meta[p.runner], dd = raceDayRating(P, J.runners[p.runner], { ...J.race, going: R.race.going });
      return `<tr class="${h.star ? "starred" : ""}"><td>${ord(p.place)}</td><td class="c">${p.draw}</td><td class="${h.star ? "mine" : ""}"><img class="silk" src="${silkImg(h.silk)}" alt="" style="display:inline-block;width:20px;height:20px;vertical-align:middle;margin-right:6px">${esc(h.name)}${h.temperament === "keen" ? ` <span class="muted small">keen</span>` : ""}</td>
        <td class="c">${h.rating}</td><td class="c">${p.dayRating}</td><td class="c">${dd.ground > 0 ? "+" : ""}${dd.ground}</td><td class="c">${dd.tripSteps ? "−" + dd.tripSteps : "✓"}</td><td class="c">${p.form > 0 ? "+" : ""}${p.form.toFixed(1)}</td>
        <td>${STYLE_NAME[p.style]}${p.ridden !== p.style ? " → " + STYLE_NAME[p.ridden] : ""}</td><td class="c">${p.place === 1 ? "–" : p.behind.toFixed(2) + " L"}</td><td class="c">${p.lostLengths ? p.lostLengths.toFixed(1) + " L" : ""}</td></tr>`; }).join("")}
    </tbody></table></div>
    <h3 style="margin:16px 0 4px;font-size:18px">What happened</h3>
    <ul class="events">${R.events.map((e) => `<li><span class="muted">${e.t.toFixed(1)} s</span> ${esc(e.text)}</li>`).join("") || "<li class='muted'>Nothing of note.</li>"}</ul>
    <div class="row" style="margin-top:14px"><button class="btn" data-w>Watch it in 3D</button></div></div>`;
  document.body.appendChild(d);
  d.onclick = (e) => { if (e.target === d || e.target.closest("[data-x]")) d.remove(); if (e.target.closest("[data-w]")) { d.remove(); watch(T, k); } };
}

// --- watching a race in 3D (the game's race view, handed this race exactly as the game hands it one)
const ODDS_LADDER = [[1, 3], [2, 5], [1, 2], [4, 7], [4, 6], [4, 5], [10, 11], [1, 1], [6, 5], [5, 4], [11, 8], [6, 4], [7, 4], [2, 1], [9, 4], [5, 2], [11, 4], [3, 1], [7, 2], [4, 1], [9, 2], [5, 1], [11, 2], [6, 1], [13, 2], [7, 1], [8, 1], [9, 1], [10, 1], [11, 1], [12, 1], [14, 1], [16, 1], [20, 1], [25, 1], [33, 1], [40, 1], [50, 1], [66, 1], [100, 1]];
let WATCH = null;
function watch(T, k) {
  const J = buildJob(T, k), S = settingsWith(T.tune), P = flatSettings(S);
  const dr = J.runners.map((r) => raceDayRating(P, r, J.race).rating), w = dr.map((x) => Math.exp(x / 7)), tot = w.reduce((a, b) => a + b, 0);
  const runners = J.meta.map((h, i) => {
    const want = 1 / Math.min(0.85, (w[i] / tot) * 1.18) - 1;
    const [n, d] = ODDS_LADDER.reduce((a, b) => (Math.abs(Math.log(b[0] / b[1] / want)) < Math.abs(Math.log(a[0] / a[1] / want)) ? b : a));
    const o = n / d, coat = COATS[h.coat || 0] || COATS[0];
    return { ...J.runners[i], silk: SILK3D[h.silk], silk2d: silkImg(h.silk), odds: n === d ? "Evens" : `${n}/${d}`,
      card: o <= 4 ? "black" : o <= 10 ? "red" : o <= 20 ? "yellow" : "blue", coat: { body: coat[0], points: coat[1] }, mine: !!h.star };
  });
  const box = document.createElement("div"); box.className = "watch";
  box.innerHTML = `<iframe src="final-furlong.html?game=1" title="Race Lab race" allow="fullscreen"></iframe><button class="btn ghost x" style="background:rgba(255,255,255,.9)">Back to the lab</button>`;
  document.body.appendChild(box); document.body.style.overflow = "hidden";
  WATCH = { box, frame: box.querySelector("iframe"), payload: {
    type: "race", course: COURSE_ID, race: J.trip.key, going: J.race.going, seed: J.race.seed, handicap: J.race.handicap,
    settings: Object.keys(T.tune || {}).length ? S : undefined,
    title: J.trip.label, kicker: `Race Lab · ${T.name}${T.total > 1 ? ` · race ${k + 1}` : ""}`,
    card: { dist: J.trip.label, meeting: "Race Lab", conditions: [J.race.handicap ? "Handicap" : "", J.V.label !== "As set" ? J.V.label : ""].filter(Boolean).join(" · "), next: "" },
    runners,
  } };
  window.__labWatch = WATCH.payload;      // checking aid: what the 3D view is handed
  box.querySelector(".x").onclick = closeWatch;
}
function closeWatch() { if (!WATCH) return; WATCH.box.remove(); WATCH = null; document.body.style.overflow = ""; }
addEventListener("message", (e) => {
  if (!WATCH || e.source !== WATCH.frame.contentWindow) return;
  const d = e.data || {};
  if (d.type === "ready") WATCH.frame.contentWindow.postMessage(WATCH.payload, "*");
  if (d.type === "back" || d.type === "next") closeWatch();
});
addEventListener("keydown", (e) => { if (e.key === "Escape") { if (WATCH) closeWatch(); else { const d = $(".drawer"); if (d) d.remove(); } } });

// --- spreadsheets and summaries
const fileName = (t) => t.replace(/[^\w\- &]+/g, "").trim().slice(0, 60) || "race-lab";
const csvCell = (v) => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
const csvRows = (rows) => rows.map((r) => r.map(csvCell).join(",")).join("\r\n");
function download(name, text) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob(["﻿" + text], { type: "text/csv;charset=utf-8" }));
  a.download = name; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}
async function copy(t) { try { await navigator.clipboard.writeText(t); toast("Copied: paste it wherever you like."); } catch (e) { download("race-lab-summary.txt", t); } }
const CSV_HEAD = ["test", "date", "rules", "race", "course_distance", "course", "distance_m", "going", "handicap", "compared", "runners", "seed", "pace_on_card", "pace_as_run", "groups",
  "winning_time_s", "par_time_s", "horse", "starred", "random_opponent", "stall", "rating", "mark", "running_style", "ridden_as", "flexibility", "temperament", "best_trip", "goings_liked",
  "jockey", "instruction", "ground_pts", "trip_steps_off", "race_day_rating", "form_on_day", "rating_rank", "pts_below_top", "place", "won", "top3", "lengths_behind", "lengths_lost_traffic", "missed_break"];
function csvLines(T) {
  const { recs } = analyse(T), date = new Date(T.created).toISOString().slice(0, 16).replace("T", " ");
  return recs.map((r) => {
    const res = T.results[r.k], J = TRIP_BY[r.trip];
    return [T.name, date, T.tag, r.k + 1, J.label, J.straight ? "straight" : J.course === "roundMile" ? "round mile" : "round", J.distance, r.going, T.setup.handicap ? "yes" : "no", r.v, r.n, T.seedBase * 100000 + (r.k % T.setup.runs),
      res.paceExp, res.paceRun, res.groups, res.time, res.par, r.name, r.star ? "yes" : "", r.src === "opp" ? "yes" : "", r.draw, r.rating, T.setup.handicap ? r.mark : "", r.style, r.ridden, r.flex, r.temper,
      r.tripPair, r.liked, r.jockey || "random", r.instr, r.ground, r.steps, r.day, +r.form.toFixed(2), r.rank, r.gap, r.place, r.place === 1 ? 1 : 0, r.place <= 3 ? 1 : 0, r.behind, r.lost, r.missed];
  });
}
const csvOf = (T) => csvRows([CSV_HEAD, ...csvLines(T)]);
function tableData(T) {
  const V = T._view || defaultView(T), P = pivot(T, V), M = METRICS[V.metric], f = (a) => (a ? M.fmt(M.of(a)) : "");
  const head = [P.D1.label + (P.D2 !== DIMS.none ? ` / ${P.D2.label}` : ""), ...P.cols, ...(P.cols.length > 1 ? ["All"] : [])];
  const rows = P.rows.map((r) => [r, ...P.cols.map((c) => f(P.cells.get(r + "\u0001" + c))), ...(P.cols.length > 1 ? [f(P.rowT.get(r))] : [])]);
  if (P.rows.length > 1) rows.push(["All", ...P.cols.map((c) => f(P.colT.get(c))), ...(P.cols.length > 1 ? [f(P.all)] : [])]);
  return { V, M, head, rows };
}
const tableCsv = (T) => csvRows([tableData(T).head, ...tableData(T).rows]);
function tableText(T) {
  const { V, M, head, rows } = tableData(T), all = [head, ...rows], w = head.map((_, i) => Math.max(...all.map((r) => String(r[i]).length)));
  return `${T.name}: ${M.label}, ${WHO[V.who][0].toLowerCase()}\n` + all.map((r) => r.map((c, i) => String(c).padEnd(w[i])).join("  ")).join("\n");
}
function summaryText(T) {
  const { head } = analyse(T), st = T.setup, star = st.field.filter((h) => h.star);
  return [
    `Race Lab test: ${T.name} (${new Date(T.created).toLocaleString("en-GB")})`,
    `Set-up: ${setupText(st)}; draw ${st.draw === "random" ? "random" : "as listed"}${st.fill ? `; random opponents rated ${st.lo}-${st.hi}` : ""}`,
    star.length ? `Starred: ${star.map((h) => `${h.name} (${h.rating}, ${STYLE_NAME[h.style]}, ${h.flex}, ${h.temperament}, best ${pairLabel(h.trip)}, likes ${(h.goings || []).join("/") || "any"}, ${INSTR_NAME[h.instruction]})`).join("; ")}` : "",
    `Engine numbers: ${Object.keys(T.tune || {}).length ? tuneText(T.tune) : "the game's own"} (rules ${T.tag})`,
    T.notes ? `Notes: ${T.notes}` : "",
    `Races ${head.races}; top-rated wins ${pct(head.bestWin)}; lowest-rated wins ${pct(head.worstWin)}; average margin ${num(head.margin, 2)} L; pace ${PACES.map((p) => `${p} ${pct(head.pace[p], 0)}`).join(", ")}; missed the break ${pct(head.missed)}`,
    star.length ? `Starred horses: win ${pct(head.starWin)}, top 3 ${pct(head.starTop3)}, average place ${num(head.starPlace, 1)}` : "",
    "", tableText(T),
  ].filter((x) => x !== "").join("\n");
}

// --- records
let PICK = new Set();
async function renderHistory() {
  const box = $("#tab-history");
  let metas = [];
  try { metas = (await DB.all("meta")).sort((a, b) => b.created - a.created); } catch (e) { box.innerHTML = `<div class="card empty"><h2>This browser won't keep records</h2><p>${esc(e.message)}</p></div>`; return; }
  if (!metas.length) { box.innerHTML = `<div class="card empty"><h2>No tests yet</h2><p>Every test you run is kept here, on this device, with all its figures.</p><button class="btn" id="goSetup2">Set up a test</button></div>`; $("#goSetup2").onclick = () => showTab("setup"); return; }
  PICK = new Set([...PICK].filter((id) => metas.some((m) => m.id === id)));
  const picked = metas.filter((m) => PICK.has(m.id));
  box.innerHTML = `
  <div class="card">
    <div class="row sp"><div><h2>Records</h2><p class="lede" style="margin-bottom:0">Every test you've run, kept in this browser on this device. Tick two or more to set them side by side; export them to keep them safe or open them in Excel or Numbers.</p></div>
      <div class="row"><button class="btn sm" data-act="csvAll">Spreadsheet of every test</button></div></div>
    <div class="scroll" style="margin-top:12px"><table class="hist"><thead><tr><th></th><th>Test</th><th>Date</th><th class="c">Races</th><th class="c">Top-rated wins</th><th class="c">Lowest wins</th><th class="c">Starred win</th><th>Numbers</th><th></th></tr></thead><tbody>
    ${metas.map((m) => `<tr><td><input type="checkbox" data-pick="${m.id}" ${PICK.has(m.id) ? "checked" : ""}></td>
      <td style="white-space:normal;min-width:240px"><span class="nm">${esc(m.name)}</span>${m.stopped ? ` <span class="pill red">stopped early</span>` : ""}<div class="small muted">${esc(m.setupText)}</div>${m.notes ? `<div class="small" style="margin-top:2px">${esc(m.notes)}</div>` : ""}</td>
      <td class="small">${new Date(m.created).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</td><td class="c">${thou(m.done)}</td>
      <td class="c">${pct(m.head.best)}</td><td class="c">${pct(m.head.worst)}</td><td class="c">${m.head.starRuns ? pct(m.head.starWin) : "–"}</td>
      <td>${m.tuned ? `<span class="pill gold">${m.tuned} tuned</span>` : m.tag === GAME_TAG ? `<span class="pill green">game's</span>` : `<span class="pill">older game's</span>`}</td>
      <td><button class="btn sm" data-act="open" data-id="${m.id}">Open</button> <button class="btn ghost sm" data-act="csv1" data-id="${m.id}">Spreadsheet</button> <button class="btn danger sm" data-act="del" data-id="${m.id}">Delete</button></td></tr>`).join("")}
    </tbody></table></div>
  </div>
  ${picked.length >= 2 ? compareHTML(picked) : picked.length === 1 ? `<p class="small muted">Tick one more to compare.</p>` : ""}`;
}
function compareHTML(ms) {
  const row = (label, f) => `<tr><td class="rl">${label}</td>${ms.map((m) => `<td class="c">${f(m)}</td>`).join("")}</tr>`;
  return `<div class="card"><h2>Side by side</h2><div class="scroll" style="margin-top:10px"><table class="pivot"><thead><tr><th></th>${ms.map((m) => `<th class="c" style="white-space:normal;min-width:120px">${esc(m.name)}</th>`).join("")}</tr></thead><tbody>
    ${row("Races", (m) => thou(m.done))}${row("Runners a race", (m) => num(m.head.size, 1))}${row("Top-rated wins", (m) => pct(m.head.best))}${row("Lowest-rated wins", (m) => pct(m.head.worst))}
    ${row("Starred horses win", (m) => (m.head.starRuns ? pct(m.head.starWin) : "–"))}${row("Starred top 3", (m) => (m.head.starRuns ? pct(m.head.starTop3) : "–"))}
    ${PACES.map((p) => row(`${cap(p)} pace`, (m) => pct(m.head.pace[p], 0))).join("")}
    ${row("Engine numbers", (m) => (m.tuned ? `${m.tuned} tuned` : "game's"))}${row("Rules", (m) => m.tag)}</tbody></table></div></div>`;
}
$("#tab-history").addEventListener("change", (e) => { const id = e.target.dataset.pick; if (!id) return; if (e.target.checked) PICK.add(id); else PICK.delete(id); renderHistory(); });
$("#tab-history").addEventListener("click", async (e) => {
  const b = e.target.closest("[data-act]"); if (!b) return;
  const id = b.dataset.id;
  const load = async () => { const T = await DB.get("tests", id); if (!T) throw new Error("not found"); return T; };
  try {
    switch (b.dataset.act) {
      case "open": CUR = await load(); RACE_PAGE = 0; RACE_FILTER = "all"; showTab("results"); break;
      case "csv1": { const T = await load(); download(`${fileName(T.name)}.csv`, csvOf(T)); break; }
      case "del": { const m = (await DB.get("meta", id)) || {}; if (!confirm(`Delete "${m.name}" and all its figures? This can't be undone.`)) break; await DB.del("tests", id); await DB.del("meta", id); if (CUR && CUR.id === id) CUR = null; PICK.delete(id); renderHistory(); break; }
      case "csvAll": {
        const metas = await DB.all("meta"); let lines = [];
        for (const m of metas) { const T = await DB.get("tests", m.id); if (T) lines = lines.concat(csvLines(T)); }
        download("Race Lab - every test.csv", csvRows([CSV_HEAD, ...lines])); break;
      }
    }
  } catch (err) { toast("Couldn't do that: " + err.message); }
});

// ---------------------------------------------------------------------------------------------- start
showTab("setup");
