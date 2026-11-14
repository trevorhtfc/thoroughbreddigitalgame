// =====================================================================================================================
// Thoroughbred: the game's rules and state. No screens in here (the screens are js/ui.js), so the long game, a
// leaderboard server or another engine can reuse it. The breeding and Tattersalls rules follow the board game's
// companion app code (trevorhtfc/horseracinggame) exactly, as the Ascot game did; the race itself is run by the race
// engine (assets/engine/engine.js). The meeting (which races, which course, the prizes) is data: js/meetings/*.js.
// =====================================================================================================================
const MEETING = window.MEETINGS[window.MEETING_ID || "royal-ascot"] || window.MEETINGS["royal-ascot"];
window.MEETING = MEETING;
// How the screens name things in this season (Royal Ascot or the Newmarket season): js/meetings/*.js -> words
const W = MEETING.words || {};
// A race day's short label ("Tue" … at Ascot; the month of each Newmarket meeting)
const dayTag = k => (MEETING.dayTag ? MEETING.dayTag[k] : DAYS[k].slice(0, 3));

const engineReady = new Promise(res => { if (window.ENGINE || window.ENGINE_FAILED) res(); else addEventListener("engine-ready", () => res(), { once: true }); });
addEventListener("engine-ready", () => { if (S && S.step === 4 && typeof render === "function") render(); });

const JOCKEYS = ["T. Hale", "M. Quinlan", "S. Ashby", "R. Dunmore", "L. Kerrigan", "J. Fennell", "O. Marsh", "C. Bracken", "D. Lowry", "H. Tolland", "P. Garvey", "E. Rook"];
const TRAINERS = ["A. Whitcombe", "G. Penrose", "F. Calder", "N. Ashworth", "B. Stannard", "K. Moffatt", "W. Harlow", "V. Pryce"];
const COATS = [["#7a4a2a", "#3a2214"], ["#4a2e1c", "#20140c"], ["#a3552c", "#6a3317"], ["#2b2523", "#141110"], ["#a8a6a0", "#6d6b66"]];
/* ================= The racecard: the race engine's fields for every horse ================= */
// Running style, flexibility and temperament (settings.json -> horse; shares as testField.MIX, bench.FLEX_MIX, testField.KEEN_P).
// Every horse gets them at random when it's born or bought, and they never change.
const STYLES = ["front", "prominent", "midfield", "holdup"];
const STYLE_NAME = { front: "Front-runner", prominent: "Prominent", midfield: "Midfield", holdup: "Hold-up" };
const FLEX = ["set", "adaptable", "versatile"];
const FLEX_NAME = { set: "Set in its ways", adaptable: "Adaptable", versatile: "Versatile" };
const STYLE_MIX = [0.25, 0.25, 0.25, 0.25], FLEX_MIX = [0.3, 0.5, 0.2], KEEN_P = 0.3;
function pickW(w, r) { let x = r() * w.reduce((a, b) => a + b, 0), k = 0; while (k < w.length - 1 && x >= w[k]) { x -= w[k]; k++; } return k; }
function rollRacecard(r) { return { style: STYLES[pickW(STYLE_MIX, r)], flex: FLEX[pickW(FLEX_MIX, r)], temper: r() < KEEN_P ? "keen" : "calm" }; }
const styleTag = h => h.style ? `${STYLE_NAME[h.style]}${h.temper === "keen" ? ", keen" : ""}` : "";
// The ground on the day, as the engine counts it: +5 on a going it likes, 0 one step off, -5 two, -10 three
const GROUND_POINTS = [5, 0, -5, -10];
function groundPts(goings, going) {
  if (!goings || !goings.length || !going) return 0;
  const g = GROUND_ORDER.indexOf(going), away = Math.min(...goings.map(x => Math.abs(GROUND_ORDER.indexOf(x) - g)));
  return GROUND_POINTS[Math.min(away, GROUND_POINTS.length - 1)];
}
function hashStr(t) { let h = 2166136261; for (const c of String(t)) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; }
// Winning margins as racing reads them
function lengthsText(x) {
  if (x == null) return "";
  if (x < 0.05) return "a dead heat"; if (x < 0.15) return "a nose"; if (x < 0.25) return "a short head"; if (x < 0.4) return "a head"; if (x < 0.65) return "a neck";
  if (x >= 30) return "a distance";
  const q = Math.round(x * 4) / 4, w = Math.floor(q), f = q - w, fr = f === 0.25 ? "¼" : f === 0.5 ? "½" : f === 0.75 ? "¾" : "";
  return (w ? w + fr : fr) + (q > 1 ? " lengths" : " length");
}
const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pick = a => a[Math.floor(Math.random() * a.length)];
function seeded(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

/* ================= Stallions and mares (snapshot of the CMS, StallionMareProfiles) =================
   name | stallion | stars | base (unproven) stars | optimum | min | max | peak age | ground | versatility | fee | sire line | sire code | blocked stallions */
const PROFILE_ROWS = ["Vadeni|1|2|1|1m4f|1m|1m6f|3YO|Softer/Good/Quicker|3|£10,000|S-Line|CH|","Mostahdaf|1|1|1|1m2f|1m|1m6f|4YO|Good/Quicker/Quick|2|£10,000|S-Line|FR|","Paddington|1|2|3|1m|6f|1m4f|3YO|Softer/Good/Quicker|3|£75,000|O-Line|SY|","Little Big Bear|1|1|2|6f|5f|1m|2YO|Quicker/Quick|2|£30,000|O-Line|NN|","Modern Games|1|3|2|1m|6f|1m2f|3YO|Quicker/Quick|1|£30,000|P-Line|DU|","City of Troy|1|3|4|1m2f|1m|1m4f|3YO|Good/Quicker/Quick|2|£125,000|O-Line|JU|","Baaeed|1|3|4|1m2f|1m|1m6f|4YO|Good/Quicker/Quick|2|£125,000|D-Line|SS|","Auguste Rodin|1|2|3|1m2f|7f|1m4f|3YO|Good/Quicker/Quick|2|£75,000|O-Line|DI|","Ace Impact|1|2|3|1m2f|1m|1m4f|3YO|Softer/Good/Quicker|3|£75,000|S-Line|CR|","Blackbeard|1|1|2|6f|5f|7f|2YO|Good/Quicker|1|£30,000|O-Line|NN|","Chaldean|1|4|3|7f|6f|1m|2YO|Softer/Good|1|£30,000|S-Line|FR|","Native Trail|1|2|1|1m|6f|1m2f|2YO|Quicker/Quick|2|£10,000|D-Line|OD|","King of Steel|1|4|3|1m2f|7f|1m4f|3YO|Softer/Good/Quicker|2|£30,000|P-Line|WB|","Pinatubo|1|1|0|7f|5f|1m|2YO|Softer/Good/Quicker|2|£10,000|O-Line|SH|","Starman|1|2|0|6f|5f|7f|2YO|Good/Quicker/Quick|2|£30,000|P-Line|DA|","Aqualina|0|2|0|2m+|1m6f|2m+|4YO|Quicker/Quick|2||S-Line|KT|","Speed Cop|0|1|0|6f|5f|7f|3YO|Good/Quicker/Quick|2||P-Line|CG|","Her Honour|0|2|0|6f|5f|7f|3YO|Heavy/Softer|1||D-Line|SH|","Perfect Clarity|0|2|0|1m4f|1m2f|1m6f|3YO|Heavy/Softer|2||S-Line|NT|Nathaniel","Topaz Clear|0|2|0|2m+|1m6f|2m+|4YO|Heavy/Softer|1||O-Line|PV|","Turret Rocks|0|2|0|1m|7f|1m2f|3YO|Quicker/Quick|1||D-Line|FR|","Royal Solitaire|0|2|0|1m6f|1m4f|2m+|3YO|Softer/Good|2||D-Line|SH|","Shoshoni Wind|0|2|0|6f|5f|7f|2YO|Good/Quicker/Quick|2||O-Line|SI|","No Lippy|0|2|0|6f|5f|6f|2YO|Good/Quicker/Quick|2||D-Line|OD|","Make Fast|0|2|0|7f|6f|1m|2YO|Softer/Good/Quicker|3||P-Line|MK|","Diamond Bangle|0|2|0|2m+|1m6f|2m+|4YO|Softer/Good|2||S-Line|GA|","Antara|0|2|0|1m|7f|1m2f|4YO|Softer/Good/Quicker|3||O-Line|PL|","Seaduced|0|3|0|1m6f|1m4f|2m+|3YO|Heavy/Softer|3||D-Line|LV|Lope De Vega","Bella Nouf|0|3|0|1m4f|1m2f|1m6f|3YO|Quicker/Quick|2||D-Line|DS|","Aris|0|3|0|1m2f|1m|1m4f|3YO|Softer/Good/Quicker|3||D-Line|DR|","Avon Breeze|0|3|0|5f|5f|6f|2YO|Softer/Good/Quicker|3||O-Line|AB|","Fidaaha|0|3|0|7f|6f|1m|2YO|Quicker/Quick/Good|3||S-Line|NA|","Bright Beacon|0|3|0|2m+|1m6f|2m+|3YO|Good/Quicker/Quick|3||O-Line|MD|","Falls of Lora|0|3|0|1m2f|1m|1m4f|4YO|Quicker/Quick|2||P-Line|SC|","Koora|0|3|0|1m4f|1m2f|1m6f|4YO|Softer/Good/Quicker|3||O-Line|PV|","Emily Bronte|0|3|0|1m|7f|1m2f|3YO|Softer/Good|3||P-Line|MC|","Arcamist|0|3|0|6f|6f|7f|3YO|Good/Quicker/Quick|3||D-Line|AR|","Nimble Thimble|0|4|0|7f|6f|1m|3YO|Quicker/Quick|2||O-Line|MM|","Mondelice|0|4|0|1m6f|1m4f|2m+|4YO|Softer/Good/Quicker|3||S-Line|MJ|","Vasilia|0|4|0|7f|6f|1m|4YO|Softer/Good/Quicker|3||D-Line|DS|","In Clover|0|4|0|1m4f|1m2f|1m6f|4YO|Heavy/Softer|1||O-Line|IC|","Arabian Queen|0|4|0|1m2f|1m|1m2f|3YO|Softer/Good/Quicker|3||P-Line|DU|Dubawi","My Titania|0|4|0|1m|7f|1m2f|3YO|Softer/Good/Quicker|3||D-Line|SS|Sea The Stars","Gale Force|0|4|0|1m6f|1m4f|2m+|4YO|Softer/Good|2||O-Line|SR|","Montare|0|4|0|1m4f|1m2f|1m6f|4YO|Softer/Good/Quicker|3||S-Line|MJ|","Adventure Seeker|0|4|0|5f|5f|6f|2YO|Softer/Good/Quicker|3||O-Line|BE|Little Big Bear","Pure Illusion|0|4|0|6f|5f|7f|3YO|Softer/Good/Quicker|3||D-Line|DH|","Anna Law|0|5|0|5f|5f|6f|3YO|Good/Quicker/Quick|3||D-Line|LW|","Suelita|0|5|0|7f|6f|1m|2YO|Softer/Good|2||P-Line|DA|Chaldean","Cabaret|0|5|0|1m|1m|1m2f|3YO|Softer/Good/Quicker|3||S-Line|GA|","Tarana|0|5|0|1m2f|1m|1m4f|4YO|Good/Quicker|3||D-Line|CC|","Together Forever|0|5|0|1m2f|1m|1m4f|3YO|Good/Quick/Quicker|3||S-Line|GA|City of Troy","Choose Me|0|5|0|7f|6f|1m|3YO|Softer/Good|2||D-Line|CH|","Aghareed|0|5|0|1m4f|1m|1m6f|4YO|Softer/Good/Quicker|3||P-Line|KM|Baaeed","Modern Ideals|0|5|0|1m|7f|1m2f|3YO|Good/Quicker/Quick|2||S-Line|NA|Modern Games","Danedrop|0|5|0|1m6f|1m4f|2m+|3YO|Softer/Good|2||D-Line|DH|","Polished Gem|0|5|0|2m+|1m6f|2m+|4YO|Softer/Good/Quicker|3||D-Line|DH|","Zunera|0|1|0|5f|5f|6f|4YO|Good/Quicker/Quick|2||D-Line|IS|","Loves Secret|0|1|0|1m2f|1m|1m4f|3YO|Heavy/Softer|1||O-Line|PV|","Law of The Range|0|1|0|1m2f|1m|1m4f|4YO|Quicker/Quick|2||O-Line|AL|","Lady Fashion|0|1|0|6f|5f|7f|3YO|Softer/Good/Quicker|3||D-Line|OD|","Za Za Zoom|0|1|0|1m4f|1m2f|1m6f|3YO|Softer/Good/Quicker|3||O-Line|LV|","Go Lovely Rose|0|1|0|7f|6f|1m|4YO|Heavy/Softer|2||O-Line|PV|","Shalwa|0|1|0|1m6f|1m2f|2m+|4YO|Softer/Good/Quicker|3||S-Line|GA|","Lope De Vega|1|4|0|7f|6f|1m4f|4YO|Softer/Good|3|£125,000|O-Line|SH|","Blue Point|1|4|0|6f|5f|7f|3YO|Good/Quicker/Quick|3|£125,000|O-Line|SH|","Kingman|1|5|0|7f|6f|1m|3YO|Quicker/Quick|1|£200,000|D-Line|IS|","New Bay|1|3|0|1m|7f|1m4f|3YO|Softer/Good|2|£75,000|P-Line|DU|","Gleneagles|1|3|0|1m|6f|1m4f|3YO|Softer/Quicker/Good|3|£75,000|S-Line|GA|","Stradivarius|1|3|2|2m+|1m4f|2m+|4YO|Softer/Good/Quicker|3|£30,000|D-Line|SS|","Harry Angel|1|1|0|5f|5f|6f|2YO|Softer/Good|1|£10,000|O-Line|DA|","Bated Breath|1|1|0|6f|5f|7f|4YO|Good/Quicker/Quick|2|£10,000|D-Line|DS|","Kameko|1|2|0|7f|6f|1m2f|3YO|Good/Quicker|2|£30,000|S-Line|KJ|","Justify|1|5|0|1m|1m|1m4f|3YO|Good/Quicker/Quick|2|£200,000|O-Line|SD|","Havana Grey|1|3|0|5f|5f|6f|2YO|Good/Quicker/Quick|2|£75,000|S-Line|HG|","Nathaniel|1|4|0|1m4f|1m2f|2m+|4YO|Softer/Good/Quicker|3|£125,000|S-Line|GA|","Teofilo|1|3|0|1m6f|1m2f|2m+|3YO|Softer/Good/Quicker|2|£75,000|S-Line|GA|","Kodiac|1|2|0|6f|5f|1m|3YO|Good/Quicker/Quick|2|£30,000|D-Line|DH|","Night of Thunder|1|4|0|7f|6f|1m|3YO|Softer/Good/Quicker|3|£125,000|P-Line|DU|","Mehmas|1|4|0|6f|5f|6f|2YO|Good/Quicker/Quick|3|£125,000|O-Line|AC|","No Nay Never|1|4|0|6f|5f|7f|2YO|Good/Quicker|2|£125,000|O-Line|SD|","Camelot|1|3|0|1m4f|1m2f|2m+|4YO|Softer/Good|2|£75,000|S-Line|MJ|","Golden Horn|1|2|0|1m6f|1m4f|2m+|4YO|Softer/Good/Quicker|3|£30,000|D-Line|CC|","Study Of Man|1|2|0|1m2f|1m|1m4f|4YO|Softer/Good|2|£30,000|O-Line|DI|","Showcasing|1|3|0|6f|5f|7f|2YO|Good/Quicker/Quick|3|£75,000|D-Line|OD|","Mayson|1|1|0|6f|5f|7f|2YO|Heavy/Softer|1|£10,000|D-Line|IS|","Too Darn Hot|1|3|0|7f|6f|1m2f|3YO|Softer/Good/Quicker|3|£75,000|P-Line|DU|","Calyx|1|1|0|6f|5f|7f|2YO|Softer/Good/Quicker|3|£10,000|D-Line|KM|","Australia|1|2|0|1m4f|1m2f|2m+|4YO|Good/Quicker|2|£30,000|S-Line|GA|","Dark Angel|1|4|0|6f|5f|6f|3YO|Good/Quicker/Quick|2|£125,000|O-Line|AC|","Wootten Bassett|1|5|0|1m|6f|1m4f|3YO|Good/Quicker/Quick|3|£200,000|P-Line|IF|","Ulysses|1|1|0|1m4f|1m|2m+|3YO|Softer/Good/Quicker|3|£10,000|S-Line|GA|","Ardad|1|1|0|5f|5f|6f|2YO|Softer/Good/Quicker|3|£10,000|D-Line|KO|","Sea The Stars|1|5|0|1m4f|1m2f|1m6f|4YO|Softer/Good/Quicker|3|£200,000|D-Line|CC|","Siyouni|1|5|0|1m|7f|1m4f|3YO|Good/Quick/Quicker|2|£200,000|O-Line|PL|","Dubawi|1|5|0|1m|6f|1m4f|3YO|Good/Quicker/Quick|2|£200,000|P-Line|DM|","Authorised|1|1|0|1m6f|1m4f|2m+|3YO|Softer/Good|2|£10,000|S-Line|MJ|","Southern Belle|0|1|0|5f|5f|6f|2YO|Heavy/Softer|2||D-Line|AQ|","Frankel|1|5|0|1m2f|7f|1m6f|3YO|Good/Quicker/Quick|3|£200,000|S-Line|GA|"];
const PROFILES = PROFILE_ROWS.map(row => {
  const [name, st, stars, base, opt, min, max, peak, ground, vers, fee, line, code, blocked] = row.split("|");
  return { name, isStallion: st === "1", stars: +stars, base: +base, optimumDistance: opt, minDistance: min, maxDistance: max, peakAge: peak,
    groundPreference: ground.split("/"), groundVersatility: +vers, fee: +String(fee).replace(/[^\d]/g, "") || 0,
    sireLine: line, sireCode: code, blocked: blocked ? blocked.split("/") : [] };
});
// Standard-game stallions only (CMS StallionMareProfiles, Expansion = "O | Standard"); the 19 expansion stallions are left out for now
const STANDARD_STALLIONS = new Set(["Paddington", "Little Big Bear", "Modern Games", "City of Troy", "Baaeed", "Auguste Rodin", "Chaldean", "Native Trail", "King of Steel", "Starman", "Lope De Vega", "Kingman", "New Bay", "Stradivarius", "Harry Angel", "Havana Grey", "Nathaniel", "Night of Thunder", "Mehmas", "Camelot", "Golden Horn", "Study Of Man", "Mayson", "Too Darn Hot", "Australia", "Ulysses", "Sea The Stars", "Dubawi", "Authorised", "Frankel"]);
const STALLIONS = PROFILES.filter(p => p.isStallion && STANDARD_STALLIONS.has(p.name)), MARES = PROFILES.filter(p => !p.isStallion);
const byName = n => PROFILES.find(p => p.name === n);

/* ================= The breeding engine (from backend/breeding.web.js, unchanged) ================= */
const DISTANCES = ["5f", "6f", "7f", "1m", "1m1f", "1m2f", "1m4f", "1m6f", "2m+"];
const GROUND_ORDER = ["Heavy", "Softer", "Good", "Quicker", "Quick"];
const SPEED_PULL = 0.6, SPRINT_MAX = 1, SPEED_DOMINANCE = 0.4;
const RATING_TABLE = {
  5: { 2: 53, 3: 54, 4: 55, 5: 56, 6: 58, 7: 59, 8: 60, 9: 61, 10: 63, 11: 65, 12: 67 },
  4: { 2: 48, 3: 50, 4: 51, 5: 53, 6: 54, 7: 54, 8: 56, 9: 57, 10: 59, 11: 62, 12: 64 },
  3: { 2: 45, 3: 46, 4: 47, 5: 49, 6: 49, 7: 50, 8: 51, 9: 52, 10: 54, 11: 57, 12: 60 },
  2: { 2: 42, 3: 42, 4: 44, 5: 45, 6: 46, 7: 46, 8: 47, 9: 48, 10: 49, 11: 51, 12: 54 },
  1: { 2: 39, 3: 39, 4: 40, 5: 40, 6: 40, 7: 41, 8: 42, 9: 42, 10: 43, 11: 45, 12: 48 }
};
const ROLL_VALUES = {
  5: [8, 8, 7, 6, 6, 5, 5, 3, 3, 3, 2], 4: [8, 7, 7, 6, 5, 5, 4, 3, 3, 2, 2], 3: [7, 7, 6, 5, 5, 4, 4, 3, 3, 3, 2],
  2: [7, 7, 6, 5, 5, 4, 4, 3, 3, 2, 1], 1: [7, 6, 5, 5, 5, 4, 4, 3, 3, 2, 1]
};
const ARROW_THRESHOLDS = { three: 12, two: 6, one: 1 };
function starsForRating(r) { r = Number(r) || 0; return r >= 120 ? 4 : r >= 110 ? 3 : r >= 100 ? 2 : 1; }
function sireLineModifier(s, m, rnd) {
  const sL = s.sireLine, mL = m.sireLine, sC = s.sireCode, mC = m.sireCode, pk = a => a[Math.floor(rnd() * a.length)];
  if (sL && mL && sL !== mL) return pk([1, 1, 2, 2, 3]);
  if (sL && mL && sL === mL && sC && mC && sC === mC) return pk([-7, -7, -7, -6, -6, -5, -5, -4, -3, -2]);
  if (sL && mL && sL === mL) return pk([-4, -4, -4, -3, -3, -2, -1, 0]);
  return 0;
}
// stallion.stars here is his real rating this game (an unproven horse's may differ from what's shown)
function breedPure(stallion, mare, rnd) {
  rnd = rnd || Math.random;
  const sStars = stallion.trueStars, mStars = mare.stars;
  const roll2d6 = () => Math.ceil(rnd() * 6) + Math.ceil(rnd() * 6);
  const peakRating = RATING_TABLE[sStars][roll2d6()] + RATING_TABLE[mStars][roll2d6()] + sireLineModifier(stallion, mare, rnd);
  const peakToNum = { "2YO": 2, "3YO": 3, "4YO": 4 };
  const sPeak = peakToNum[stallion.peakAge] || 3, mPeak = peakToNum[mare.peakAge] || 3, avgPeak = (sPeak + mPeak) / 2;
  const foalPeakAge = avgPeak <= 2.3 ? 2 : avgPeak <= 3.3 ? 3 : 4;
  function reverseImprovement(rating, peak) {
    if (!ROLL_VALUES[rating]) return { from3to2: 0, from4to3: 0 };
    const r1 = Math.floor(rnd() * 11), r2 = Math.floor(rnd() * 11);
    if (peak === "3YO") return { from3to2: ROLL_VALUES[rating][r1], from4to3: 0 };
    if (peak === "4YO") return { from4to3: Math.round(ROLL_VALUES[rating][r1] / 2), from3to2: Math.round(ROLL_VALUES[rating][r2] / 2) };
    return { from3to2: 0, from4to3: 0 };
  }
  const iS = reverseImprovement(sStars, stallion.peakAge), iM = reverseImprovement(mStars, mare.peakAge);
  const total3to2 = iS.from3to2 + iM.from3to2, total4to3 = iS.from4to3 + iM.from4to3;
  let rating3 = peakRating, rating2 = peakRating;
  if (foalPeakAge === 3) rating2 = peakRating - total3to2;
  else if (foalPeakAge === 4) { rating3 = peakRating - total4to3; rating2 = rating3 - total3to2; }
  const idx = d => DISTANCES.indexOf(String(d || "").trim()), clamp = (n, a, b) => Math.max(a, Math.min(n, b));
  let sOpt = idx(stallion.optimumDistance), mOpt = idx(mare.optimumDistance);
  if (sOpt < 0 && mOpt < 0) { sOpt = 3; mOpt = 3; } else if (sOpt < 0) sOpt = mOpt; else if (mOpt < 0) mOpt = sOpt;
  const sMin = idx(stallion.minDistance) >= 0 ? idx(stallion.minDistance) : 0, mMin = idx(mare.minDistance) >= 0 ? idx(mare.minDistance) : 0;
  const sMax = idx(stallion.maxDistance) >= 0 ? idx(stallion.maxDistance) : DISTANCES.length - 1, mMax = idx(mare.maxDistance) >= 0 ? idx(mare.maxDistance) : DISTANCES.length - 1;
  const avgMin = Math.min(sMin, mMin), avgMax = Math.max(sMax, mMax);
  const shorter = Math.min(sOpt, mOpt), longer = Math.max(sOpt, mOpt);
  let centre, jitter;
  if (longer <= SPRINT_MAX) { centre = shorter; jitter = rnd() < 0.25 ? 1 : 0; }
  else if (shorter <= SPRINT_MAX && rnd() < SPEED_DOMINANCE) { centre = shorter; jitter = rnd() < 0.3 ? 1 : 0; }
  else { centre = shorter * SPEED_PULL + longer * (1 - SPEED_PULL); jitter = Math.floor(rnd() * 3) - 1; }
  const optimumIndex = clamp(Math.round(centre + jitter), avgMin, avgMax);
  function generateRange(c, lo, hi) {
    c = clamp(c, lo, hi);
    let cand = [c];
    if (rnd() < 0.5 && c + 1 <= hi) cand.push(c + 1); else if (c - 1 >= lo) cand.push(c - 1); else if (c + 1 <= hi) cand.push(c + 1);
    cand = [...new Set(cand)];
    if (cand.length < 2) { const extra = cand[0] > lo ? cand[0] - 1 : cand[0] + 1; if (extra >= lo && extra <= hi && !cand.includes(extra)) cand.push(extra); }
    return cand.sort((a, b) => a - b);
  }
  function reduceRange(base, lo) {
    let r = [...new Set(base.map(i => clamp(i - 1, lo, DISTANCES.length - 1)))];
    if (r.length < 2) { const c = clamp(r[0] + 1, lo, DISTANCES.length - 1); if (!r.includes(c)) r.push(c); }
    return r.sort((a, b) => a - b);
  }
  let d2, d3, d4;
  const peakRange = generateRange(optimumIndex, avgMin, avgMax);
  if (foalPeakAge === 2) { d2 = d3 = d4 = peakRange; }
  else if (foalPeakAge === 3) { d3 = peakRange; d2 = reduceRange(peakRange, avgMin); d4 = peakRange; }
  else { d4 = peakRange; d3 = reduceRange(peakRange, avgMin); d2 = reduceRange(d3, avgMin); if (rnd() < 0.1) d4 = [...new Set(d4.map(i => clamp(i + 1, avgMin, avgMax)))]; }
  const gIdx = tags => tags.map(t => GROUND_ORDER.indexOf(String(t).trim())).filter(i => i >= 0).sort((a, b) => a - b);
  const sG = gIdx(stallion.groundPreference), mG = gIdx(mare.groundPreference), all = [...new Set([...sG, ...mG])].sort((a, b) => a - b);
  let foalGround = [];
  if (all.length) {
    const lo = all[0], hi = all[all.length - 1], mid = (lo + hi) / 2, sV = stallion.groundVersatility, mV = mare.groundVersatility, tv = sV + mV;
    if (tv <= 2) foalGround = [GROUND_ORDER[Number.isInteger(mid) ? mid : (rnd() < 0.5 ? Math.floor(mid) : Math.ceil(mid))]];
    else if (tv <= 4) {
      const base = Math.round(mid), bias = sV <= mV ? sG : mG, cand = [base - 1, base, base + 1].filter(i => i >= 0 && i < GROUND_ORDER.length);
      foalGround = cand.filter(i => bias.includes(i)).map(i => GROUND_ORDER[i]);
      if (foalGround.length < 2) foalGround = cand.slice(0, 2).map(i => GROUND_ORDER[i]);
    } else { const c = Math.round(mid); foalGround = [c - 1, c, c + 1].filter(i => i >= 0 && i < GROUND_ORDER.length).map(i => GROUND_ORDER[i]); }
  }
  return { peakAge: foalPeakAge, r: [rating2, rating3, peakRating], d: [d2, d3, d4], grounds: foalGround };
}
function verdictFor(h) {
  const now = h.r[0], peak = h.r[2], gain = peak - now, peakStars = starsForRating(peak), nowStars = starsForRating(now);
  const avg = a => a.reduce((x, y) => x + y, 0) / a.length, nowIdx = avg(h.d[0]), peakIdx = avg(h.d[2]), stretching = peakIdx > nowIdx;
  if (h.peakAge === 2) return nowStars >= 3 ? ["2YO flyer", "Ready to win now. Make the most of it this season."] : ["2YO ready", "Already at its best, so race it this season."];
  if (peakStars === 4) return gain >= 6 ? ["Future superstar", "Modest now, but heading for the very top."] : ["Classy type", "Smart already, with a little more to come."];
  if (peakStars === 3 && gain >= 8) return ["Future star", "Lots of improvement to come."];
  if (stretching && peakIdx >= 6) return ["Future stayer", "Will want a much longer trip as it matures."];
  if (peakIdx <= 1.5) return ["Speedball", "Built for sprinting."];
  if (gain >= 10) return ["Late bloomer", "Give it time. The best is yet to come."];
  if (gain >= 4) return ["Improver", "Should keep getting better."];
  return ["Honest type", "Consistent. What you see is what you get."];
}
function outlook(h) {
  const left = h.r[2] - h.r[0], arrows = left >= ARROW_THRESHOLDS.three ? 3 : left >= ARROW_THRESHOLDS.two ? 2 : left >= ARROW_THRESHOLDS.one ? 1 : 0;
  return { arrows, words: ["Already at its peak", "A little still to come", "Some improvement to come", "Plenty still to come"][arrows] };
}
// Tattersalls reserve by combined stars (backend/tattersalls.web.js)
const RESERVES = { 2: 10000, 3: 20000, 4: 30000, 5: 50000, 6: 75000, 7: 100000, 8: 125000, 9: 150000, 10: 200000 };
// Breeding rule: a mare can't be more than one star above the stallion's shown rating, and some pairings are blocked
function pairProblem(s, m) {
  if (m.stars > s.shownStars + 1) return `${m.name} is more than one star above him`;
  if (m.blocked.includes(s.name)) return `${m.name} can't be bred with ${s.name}`;
  return "";
}
function lineNote(s, m) {
  if (s.sireLine !== m.sireLine) return { cls: "out", text: "Outcross" };
  if (s.sireCode === m.sireCode) return { cls: "in2", text: "Same family" };
  return { cls: "in1", text: "Same line" };
}


/* ================= The card ================= */
const START_BUDGET = 1250000, MARE_CAP = 10, STABLE_CAP = 15, LOTS_PER_BOOK = 9;
// From the site's Tattersalls page code (src/pages/Tattersalls.hju2p.js)
const TRIP_WEIGHTS = { close: 3, near: 2, mid: 1, far: 0.35, sprinterVsMiddle: 0.1 };
// CMS newStallion = "Yes" (standard set): a mare one star above gets a slightly better chance in their lots
const NEW_STALLIONS = new Set(["Paddington", "Little Big Bear", "Modern Games", "City of Troy", "Baaeed", "Auguste Rodin", "Chaldean", "Native Trail", "King of Steel", "Stradivarius"]);
// Mares sale: three piles by stars; pay to turn over two mares and keep one
// (Blue-blooded raised from £50,000 on 6 Nov 2026, so that buying a top horse at Tattersalls is a real option beside breeding one)
const PILES = [
  { id: "hi", name: "Blue-blooded", stars: [4, 5], price: 95000 },
  { id: "mid", name: "Useful", stars: [3], price: 25000 },
  { id: "lo", name: "Moderate", stars: [1, 2], price: 10000 }
];
// Tattersalls Books by the lot's combined stars (sire's shown rating + dam)
const BOOKS = [
  { n: 1, name: "Book 1", note: "Top pedigrees", min: 7, max: 10 },
  { n: 2, name: "Book 2", note: "The solid middle", min: 4, max: 6 },
  { n: 3, name: "Book 3", note: "Cheap and cheerful", min: 2, max: 3 }
];
// The meeting's days, grades and race programme come from the meeting file
const DAYS = MEETING.days;
const GRADE = MEETING.grades;
const POOL = MEETING.pool;
const N_RACES = MEETING.nRaces, PER_DAY = MEETING.racesPerDay, MIN_HANDICAPS = MEETING.minOpen, MIN_PATTERN = MEETING.minPattern;
// Handicaps are for horses rated 110 or less, on their own rating (not after the trip penalty)
const HCAP_MAX = MEETING.hcapMax;
const isOpenRace = r => r.grade === "Handicap" || r.grade === "Conditions";
// Runners in each kind of race, your horse included (owner, 5 Nov): 2-year-old races 14-26; handicaps 18-26 on the
// straight course, 18-20 round the bend; Group races 10-18 on the straight, 8-14 round the bend; Listed and
// Conditions races 10-16. The round mile (starting in the chute) counts as round the bend.
const FIELD_SIZE = MEETING.fieldSize;
const onStraight = r => (MEETING.courses ? r.f <= courseOf(r).straightUpTo : r.f < MEETING.straightUpTo || (r.f === MEETING.straightUpTo && !r.round));
function fieldSize(r) {
  if (r.ages[1] === 2) return FIELD_SIZE.twoYO;
  if (r.grade === "Handicap") return onStraight(r) ? FIELD_SIZE.hcapStraight : FIELD_SIZE.hcapRound;
  if (r.grade.startsWith("Group")) return onStraight(r) ? FIELD_SIZE.groupStraight : FIELD_SIZE.groupRound;
  return FIELD_SIZE.other;
}
let RACES = [];
// Draw the card's ten races: two a day, a real mix (at least three of each kind), in race-time order
function drawRaces(R) {
  for (let tries = 0; tries < 200; tries++) {
    const pick = [];
    for (let d = 0; d < DAYS.length; d++) {
      const day = POOL.filter(r => r.day === d).slice();
      for (let k = day.length - 1; k > 0; k--) { const j = Math.floor(R.r() * (k + 1)); [day[k], day[j]] = [day[j], day[k]]; }
      pick.push(...day.slice(0, PER_DAY).sort((a, b) => POOL.indexOf(a) - POOL.indexOf(b)));
    }
    const h = pick.filter(isOpenRace).length;
    if (h >= MIN_HANDICAPS && pick.length - h >= MIN_PATTERN) return pick;
  }
  return POOL.filter((r, k) => k % 7 < 2);
}
function setRaces(list) {
  RACES = list.map((r, i) => ({ ...r, i, step: STEP_OF[r.f], bands: GRADE[r.grade].bands, prizes: GRADE[r.grade].prizes }));
}
const STEP_OF = { 5: 0, 6: 1, 7: 2, 8: 3, 9: 4, 10: 5, 12: 6, 13: 6, 14: 7, 16: 8, 18: 8, 20: 8, 22: 8 };   // 13 (1m5f) and 18 (2m2f): Newmarket, as the engine rounds them
// The race in the race engine and the 3D view (courses/ascot-view.json -> races)
// A season may race on more than one course (Newmarket: the Rowley Mile and the July Course): each race's course gives its
// files (assets/course/<file>.json …), how far its straight goes and its races in the view file. Royal Ascot has one.
const courseOf = r => (MEETING.courses ? MEETING.courses[r.course] : { name: MEETING.name, file: MEETING.course, straightUpTo: MEETING.straightUpTo, views: MEETING.viewRaces });
const courseFile = r => courseOf(r).file;
const courseName = r => (MEETING.courses ? courseOf(r).name : "");
const viewKey = r => (MEETING.courses ? courseOf(r).views[r.f] : (r.round && MEETING.viewRaces[r.f + "r"]) || MEETING.viewRaces[r.f]);


// The four rating bands of each race (the board game's decks): the field is drawn across them, and the lowest is the
// rating a horse needs to run at all.
const BANDS = 4;
const needFor = race => race.bands[BANDS - 1];

const NAME_A = ["Silver", "Royal", "Golden", "Northern", "Midnight", "Crimson", "Iron", "Highland", "Copper", "Shadow", "Velvet", "Thunder", "Gilded", "Ember", "Frost", "Morning", "Harbour", "Paper", "Quiet", "Wild", "Summer", "Distant", "Lucky", "Scarlet", "Hidden", "Brave", "Salt", "Amber", "Lantern", "Starlit"];
const NAME_B = ["Crown", "Echo", "Harbour", "Comet", "Ridge", "Sonnet", "Banner", "Sovereign", "Quarry", "Falcon", "Meadow", "Tempest", "Rampart", "Cadence", "Arrow", "Monarch", "Reverie", "Gambit", "Vista", "Pilgrim", "Ledger", "Beacon", "Mischief", "Rhapsody", "Charter", "Orchard", "Voyager", "Spire", "Verdict", "Kestrel"];
const MORE_JOCKEYS = ["A. Prior", "B. Halloran", "N. Severn", "G. Whitlock", "K. Ashdown", "F. Merriman"];
const MORE_TRAINERS = ["S. Ledbury", "M. Corrigan", "P. Hatherley", "J. Tamworth", "R. Elsworth"];
// Racing silks from the board game (img/silks), 54 designs in alphabetical order of the source files; a = jacket colour, b = second colour, for the race view
const SILKS = [{img:"img/silks/s01.webp",a:"#3e9745",b:"#d53f3c"},{img:"img/silks/s02.webp",a:"#604a82",b:"#b7e5f1"},{img:"img/silks/s03.webp",a:"#49266c",b:"#ffffff"},{img:"img/silks/s04.webp",a:"#333f51",b:"#333f51"},{img:"img/silks/s05.webp",a:"#2156a6",b:"#f1a43f"},{img:"img/silks/s06.webp",a:"#eea1c6",b:"#eea1c6"},{img:"img/silks/s07.webp",a:"#49266c",b:"#ffffff"},{img:"img/silks/s08.webp",a:"#1d1d1d",b:"#eff5f5"},{img:"img/silks/s09.webp",a:"#ed2f24",b:"#fffefe"},{img:"img/silks/s10.webp",a:"#ed2f24",b:"#eff5f5"},{img:"img/silks/s11.webp",a:"#333f51",b:"#b8e5f2"},{img:"img/silks/s12.webp",a:"#bebfc0",b:"#bebfc0"},{img:"img/silks/s13.webp",a:"#2156a5",b:"#f1dc47"},{img:"img/silks/s14.webp",a:"#a8a8aa",b:"#9e3a59"},{img:"img/silks/s15.webp",a:"#2356a6",b:"#ee2f24"},{img:"img/silks/s16.webp",a:"#333f51",b:"#b8e5f2"},{img:"img/silks/s17.webp",a:"#e0d5a9",b:"#333f51"},{img:"img/silks/s18.webp",a:"#2156a5",b:"#2156a5"},{img:"img/silks/s19.webp",a:"#b7e4f1",b:"#333f51"},{img:"img/silks/s20.webp",a:"#64c3ab",b:"#eea1c6"},{img:"img/silks/s21.webp",a:"#2055a6",b:"#feffff"},{img:"img/silks/s22.webp",a:"#2156a5",b:"#ffffff"},{img:"img/silks/s23.webp",a:"#f1e93e",b:"#1d1d1d"},{img:"img/silks/s24.webp",a:"#604a82",b:"#64c3ab"},{img:"img/silks/s25.webp",a:"#a04059",b:"#ffffff"},{img:"img/silks/s26.webp",a:"#eff5f5",b:"#1d1d1d"},{img:"img/silks/s27.webp",a:"#b7e4f1",b:"#f0a43f"},{img:"img/silks/s28.webp",a:"#1d1d1d",b:"#f1e93e"},{img:"img/silks/s29.webp",a:"#64c3ab",b:"#ffffff"},{img:"img/silks/s30.webp",a:"#333f51",b:"#f1db47"},{img:"img/silks/s31.webp",a:"#eff5f5",b:"#ed2e23"},{img:"img/silks/s32.webp",a:"#1d1d1d",b:"#ffffff"},{img:"img/silks/s33.webp",a:"#f0a43f",b:"#1d1e1e"},{img:"img/silks/s34.webp",a:"#333f51",b:"#eea1c6"},{img:"img/silks/s35.webp",a:"#eff5f5",b:"#eea1c6"},{img:"img/silks/s36.webp",a:"#eff5f5",b:"#2056a6"},{img:"img/silks/s37.webp",a:"#eff5f5",b:"#49266c"},{img:"img/silks/s38.webp",a:"#49266c",b:"#eea1c6"},{img:"img/silks/s39.webp",a:"#9e3a59",b:"#c98637"},{img:"img/silks/s40.webp",a:"#eff5f5",b:"#ed2e23"},{img:"img/silks/s41.webp",a:"#ed2f24",b:"#eff5f5"},{img:"img/silks/s42.webp",a:"#49266c",b:"#ed2f24"},{img:"img/silks/s43.webp",a:"#f1e93e",b:"#49266c"},{img:"img/silks/s44.webp",a:"#2156a5",b:"#ffffff"},{img:"img/silks/s45.webp",a:"#b7e4f1",b:"#333f51"},{img:"img/silks/s46.webp",a:"#eda1c6",b:"#64c3ab"},{img:"img/silks/s47.webp",a:"#eff5f5",b:"#64c3ab"},{img:"img/silks/s48.webp",a:"#1d1d1d",b:"#f1e93e"},{img:"img/silks/s49.webp",a:"#333f51",b:"#f1dc47"},{img:"img/silks/s50.webp",a:"#e9c665",b:"#2156a6"},{img:"img/silks/s51.webp",a:"#2156a6",b:"#e9c665"},{img:"img/silks/s52.webp",a:"#eff5f5",b:"#2056a6"},{img:"img/silks/s53.webp",a:"#f1e93e",b:"#1d1d1d"},{img:"img/silks/s54.webp",a:"#f1e93e",b:"#1d1d1d"}];
const COLOURS = SILKS;
// The same 54 silks as traditional silks for the 3D jockey (silks/silks.json in the repo, in menu order: s01 first)
const SILK3D = ["aga-khan", "alcohol-free", "amo-2", "ballydoyle-navy", "ballydoyle-orange", "ballydoyle-pink", "ballydoyle-purple", "black-white", "bradsell", "cheveley-park", "circus-maximus", "clipper-logistics", "desert-crown", "doha", "ebts-guard", "flamin-rib", "glen-sheil", "godolphin", "highclere", "judmonte", "king-power", "lake-forest", "liberty-lane", "lord-riddleford", "maroon-classic", "masrshamn", "middleham-park", "mill-reef", "nashwa", "nathaniel", "night-of-thunder", "oppenheimer", "orange-black", "phoenix-of-spain", "pink-white", "pink-white-blue", "poetic-flare", "purple-pink", "qatar", "red-white", "red-white-black", "royal", "sea-the-stars", "shadwell", "silkiewilie", "starlust", "strawbridge", "stradivarius", "swingalong", "wantan-2", "watnan", "white-blue", "wimbledon-hawkeye", "yellow-black-epilite"];
// Your colours (owner, 13 Nov): every player makes their own from the templates and the palette (silks-paint.js, the
// maker in js/colours.js), and they are remembered on this phone or computer for every game and both seasons. The 54
// ready-made silks are the opposition's; a player who has not made colours yet is shown the first of them until they do.
const COLOURS_KEY = "tb-colours", MINE = -1;
let MY = null;   // { spec, code, img (the menu picture, a data: address), a, b }
function setColours(spec, keep) {
  if (!window.SilksPaint || !SilksPaint.valid(spec)) return false;
  const second = [spec.body, spec.sleeves, spec.cap].map(z => z.p !== "plain" && z.b !== spec.body.a ? z.b : z.a).find(c => c !== spec.body.a) || spec.body.a;
  MY = { spec, code: SilksPaint.encode(spec), img: SilksPaint.icon(spec, 280).toDataURL("image/png"), a: spec.body.a, b: second };
  if (keep !== false) { try { localStorage.setItem(COLOURS_KEY, JSON.stringify({ v: 1, spec, when: Date.now() })); } catch (e) {} }
  return true;
}
(() => { try { const v = JSON.parse(localStorage.getItem(COLOURS_KEY) || "null"); if (v && v.spec) setColours(v.spec, false); } catch (e) {} })();
const hasColours = () => !!MY;
const mySilkN = () => MY ? MINE : Math.min(S.silks || 0, SILKS.length - 1);
const mySilks = () => MY || SILKS[mySilkN()];
const silkOf = k => k === MINE ? (MY || SILKS[0]) : SILKS[Math.max(0, Math.min(SILKS.length - 1, k || 0))];
const silkImg = (k, cls) => `<img class="silk ${cls || ""}" src="${silkOf(k).img}" alt="">`;
// what the 3D views are given for your jockey: your own colours to paint, or one of the ready-made silks by name
const my3D = () => MY ? MY.spec : SILK3D[mySilkN()];
const shirt = (a, b) => `<svg class="shirt" viewBox="0 0 40 46" aria-hidden="true"><path d="M12 6l8-3 8 3 9 8-5 6-4-3v26H12V17l-4 3-5-6z" fill="${a}" stroke="rgba(0,0,0,.35)"/><rect x="12" y="20" width="16" height="6" fill="${b}"/></svg>`;

/* ================= Building a card from a seed: the opposition, the going, the mare draw ================= */
function rngFrom(seed) { const r = seeded(seed); return { r, int: (a, b) => a + Math.floor(r() * (b - a + 1)), pick: a => a[Math.floor(r() * a.length)] }; }
function groundsFor(R) { const s = R.int(0, 3), n = R.int(2, 3); return GROUND_ORDER.slice(s, s + n); }
// How the rest of each AI field is spread across the race's four rating bands, top to bottom, by race strength; every field also has one runner in the top band and one in the bottom
let FIELD_W = { open: { Weak: [0.3, 2, 4, 2], Average: [0.6, 3, 4, 1.5], Strong: [1.2, 4, 3, 1] }, pattern: { Weak: [0.5, 2, 3, 3], Average: [1, 2, 3, 2], Strong: [2, 3, 2, 1] } };
function makeCard(seed) {
  const R = rngFrom(seed), used = new Set();
  const nm = () => { for (let k = 0; k < 300; k++) { const n = (R.pick(NAME_A) + " " + R.pick(NAME_B)).toUpperCase(); if (!used.has(n)) { used.add(n); return n; } } return "RUNNER " + used.size; };
  const going = DAYS.map(() => R.pick(MEETING.goings));
  const jockeys = JOCKEYS.concat(MORE_JOCKEYS), trainers = TRAINERS.concat(MORE_TRAINERS);
  setRaces(drawRaces(R));
  const races = RACES.map(race => {
    const open = isOpenRace(race), n = open ? R.int(9, 11) : R.int(6, 9), x = R.r(), strength = x < .3 ? "Weak" : x < .7 ? "Average" : "Strong";
    // handicaps are framed so most of the field is closely matched
    const w = (open ? FIELD_W.open : FIELD_W.pattern)[strength], tot = w.reduce((a, b) => a + b);
    const count = [1, 0, 0, 1];
    for (let k = 2; k < n - 1; k++) { let y = R.r() * tot, d = 0; while (y >= w[d]) { y -= w[d]; d++; } count[d]++; }
    const b = race.bands, top = [b[0] + 8, b[0] - 1, b[1] - 1, b[2] - 1], opp = [];
    count.forEach((c, d) => { for (let k = 0; k < c; k++) {
      const sk = R.int(0, SILKS.length - 1), s = SILKS[sk];
      opp.push({ id: race.id + "-" + opp.length, name: nm(), rating: R.int(b[d], top[d]),
        sk, a: s.a, b: s.b, silks: s.img, grounds: groundsFor(R), coat: R.pick(COATS), jockey: R.pick(jockeys), trainer: R.pick(trainers) });
    } });
    for (let k = opp.length - 1; k > 0; k--) { const j = Math.floor(R.r() * (k + 1)); [opp[k], opp[j]] = [opp[j], opp[k]]; }
    // Field sizes and racecards come from a separate stream of the seed, so the rest of the card is drawn exactly as
    // before. The field is grown (or cut) to a size for its kind of race (FIELD_SIZE), the extra runners drawn across
    // the bands the same way.
    const X = rngFrom(hashStr(seed + ":" + race.id)), [fLo, fHi] = fieldSize(race), want = X.int(fLo, fHi) - 1;
    let nextId = opp.length;
    while (opp.length > want) opp.splice(X.int(0, opp.length - 1), 1);
    while (opp.length < want) {
      let y = X.r() * tot, d = 0; while (d < 3 && y >= w[d]) { y -= w[d]; d++; } count[d]++;
      let name; for (let t = 0; t < 300; t++) { name = (X.pick(NAME_A) + " " + X.pick(NAME_B)).toUpperCase(); if (!used.has(name)) break; }
      used.add(name);
      const sk = X.int(0, SILKS.length - 1), s = SILKS[sk];
      opp.splice(X.int(0, opp.length), 0, { id: race.id + "-" + nextId++, name, rating: X.int(b[d], top[d]),
        sk, a: s.a, b: s.b, silks: s.img, grounds: groundsFor(X), coat: X.pick(COATS), jockey: X.pick(jockeys), trainer: X.pick(trainers) });
    }
    // Each is bred for this trip: the race is one of its two best distances.
    opp.forEach(o => { const up = X.r() < .5, lo = Math.max(0, Math.min(DISTANCES.length - 2, up ? race.step : race.step - 1));
      Object.assign(o, rollRacecard(X.r), { trip: [lo, lo + 1] }); });
    return { opp, strength, count, myStall: (R.int(0, opp.length), X.int(0, opp.length)), pace: R.pick(["fast", "even", "even", "slow"]), seed: R.int(1, 2e9) };
  });
  // Unproven stallions: players see the stud-book stars; this game he is really a star better or worse
  const trueStars = {};
  STALLIONS.forEach(s => { trueStars[s.name] = s.base > 0 ? Math.max(1, Math.min(5, s.base + (R.r() < .5 ? -1 : 1))) : s.stars; });
  const mareOrder = MARES.map(m => m.name);
  for (let k = mareOrder.length - 1; k > 0; k--) { const j = Math.floor(R.r() * (k + 1)); [mareOrder[k], mareOrder[j]] = [mareOrder[j], mareOrder[k]]; }
  return { seed, going, races, trueStars, mareOrder, oppNames: used };
}
// Stud fee goes by the stars players see (the stud-book rating for an unproven stallion)
const FEE_BY_STARS = { 1: 10000, 2: 30000, 3: 75000, 4: 125000, 5: 200000 };
function stallion(name) { const s = byName(name), shown = s.base > 0 ? s.base : s.stars; return { ...s, fee: FEE_BY_STARS[shown] || s.fee, shownStars: shown, trueStars: CARD.trueStars[name], unproven: s.base > 0 }; }

/* ================= Eligibility and the race-day rating ================= */
// The going is declared in race week, after the entries (as on the board)
const goingKnown = () => S.step >= 4;
const tripText = (d) => d.length ? (d.length === 1 ? DISTANCES[d[0]] : DISTANCES[d[0]] + "–" + DISTANCES[d[d.length - 1]]) : "";
const ratingAt = (h, age) => h.r[Math.min(4, age) - 2];
const tripAt = (h, age) => h.d[Math.min(4, age) - 2];
function check(h, race) {
  if (h.age < race.ages[0] || h.age > race.ages[1]) return { hidden: true };
  if (race.sex && h.sex !== race.sex) return { hidden: true };
  if (race.grade === "Handicap" && ratingAt(h, h.age) > HCAP_MAX) return { why: `Rated ${ratingAt(h, h.age)}: too high for a handicap (max ${HCAP_MAX})` };
  const best = tripAt(h, h.age), lo = Math.min(...best), hi = Math.max(...best);
  const steps0 = race.step < lo ? lo - race.step : race.step > hi ? race.step - hi : 0;
  // your trainer (js/team.js): a tune-up for this race, Stable Form (trip work and the rest change the horse itself)
  const train = typeof trainFor === "function" ? trainFor(h, race, steps0) : { boost: 0, shift: 0, cards: [] };
  const steps = Math.max(0, steps0 - train.shift);
  if (steps > 3) return { why: `More than 3 steps from its best trip (${tripText(best)})` };
  const eff = ratingAt(h, h.age) + train.boost - steps * 5;
  if (eff < needFor(race)) return { eff, steps, train, why: `Rated ${eff} here: this race needs ${needFor(race)}+` };
  // Before race week the going isn't known, so the race-day rating is the rating at this trip; then the ground counts too
  // a booked jockey's boost on the day (js/team.js: the Champion everywhere, a specialist where he fits)
  const jock = typeof jockeyBoost === "function" ? jockeyBoost(race, h) : { boost: 0, why: "" };
  const going = goingKnown() ? CARD.going[race.day] : null, ground = groundPts(h.grounds, going), day = eff + ground + jock.boost;
  const rk = rankIn(race, day, going);
  return { eff, steps, ok: true, ground, day, rank: rk.rank, of: rk.of, suits: ground > 0, train, jock };
}
// Where a race-day rating sits among the field's (the opposition race at their best trip)
function oppDay(o, going) { return o.rating + groundPts(o.grounds, going); }
function rankIn(race, day, going) {
  const opp = CARD.races[race.i].opp.map(o => oppDay(o, going));
  return { rank: 1 + opp.filter(v => v > day).length, of: opp.length + 1 };
}
function fieldRange(race) {
  const going = goingKnown() ? CARD.going[race.day] : null, v = CARD.races[race.i].opp.map(o => oppDay(o, going));
  return [Math.min(...v), Math.max(...v)];
}
const rkCls = c => c.rank === 1 ? "r1" : c.rank <= 3 ? "r3" : "rn";
const rankText = c => `${ord(c.rank)} of ${c.of} on ratings`;
const rkChip = c => `<span class="rk ${rkCls(c)}" title="${rankText(c)}">${c.day}</span>`;
function bandsLine(r) { const [lo, hi] = fieldRange(r); return `<div class="bands">Needs <b>${needFor(r)}+</b> · the field is rated ${lo}–${hi}</div>`; }
const money = v => "£" + Math.round(v).toLocaleString("en-GB");
const ord = n => n + (n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th");
const sexWord = h => h.age <= 3 ? (h.sex === "F" ? "filly" : "colt") : (h.sex === "F" ? "mare" : "horse");
const starStr = n => "★".repeat(n) + "☆".repeat(Math.max(0, 5 - n));

/* ================= Running a race ================= */
function horse(id) { return S.stable.find(h => h.id === id); }
// Which of a horse's other entries a race rules out. At Royal Ascot a horse runs once; in the Newmarket season it may run
// at every meeting it qualifies for, once at each (MEETING.runsPerMeeting; owner, 10 Nov: "the same horse can be used
// multiple times if applicable").
const clashes = (x, r) => x.id !== r.id && (!MEETING.runsPerMeeting || x.day === r.day);
const clashFor = (h, r) => RACES.find(x => clashes(x, r) && S.entries[x.id] === h.id);
const runsOf = h => RACES.filter(x => S.entries[x.id] === h.id);
// The field in stall order, as racecards for the race engine (it applies the trip and the ground itself)
function fieldFor(i) {
  const race = RACES[i], C = CARD.races[i], mk = mySilkN(), me0 = mySilks();
  const list = C.opp.map((o, k) => {
    let sk = o.sk;
    if (sk === mk) sk = (mk + 1 + k) % SILKS.length;   // nobody else wears your colours
    if (sk === mk) sk = (sk + 1) % SILKS.length;
    const t = SILKS[sk];
    return { ...o, sk, a: t.a, b: t.b, silks: t.img, trip: o.trip.map(x => DISTANCES[x]), goings: o.grounds };
  });
  const me = S.entries[race.id] && horse(S.entries[race.id]);
  if (me) {
    const c = check(me, race), d = tripAt(me, me.age);
    // the trainer cards' boost and trip move (towards the race), and a booked jockey's skills (js/team.js)
    let lo = Math.min(...d), hi = Math.max(...d);
    const sh = c.ok && c.train ? c.train.shift : 0;
    if (sh && race.step < lo) { const k = Math.min(sh, lo - race.step); lo -= k; hi -= k; }
    else if (sh && race.step > hi) { const k = Math.min(sh, race.step - hi); lo += k; hi += k; }
    const jc = typeof bookedFor === "function" ? bookedFor(race) : null;
    if (c.ok) list.splice(C.myStall, 0, { id: me.id, name: me.name, rating: ratingAt(me, me.age) + (c.train ? c.train.boost : 0) + (c.jock ? c.jock.boost : 0), trip: [DISTANCES[lo], DISTANCES[hi]],
      goings: me.grounds, style: me.style, flex: me.flex, temper: me.temper, sk: mk, a: me0.a, b: me0.b, silks: me0.img,
      coat: me.coat, jockey: jc ? `${jc.title} ${TIER_NUM[jc.tier]}` : "Your jockey", trainer: "Your yard", owner: "You", mine: true,
      edge: typeof jockeyFields === "function" ? jockeyFields(race) : {} });
  }
  return list.map((h, k) => ({ ...h, stall: k + 1 }));
}
// The betting and the race-day colours (for the race view's dock and racecard). Each runner's race-day figure is its
// rating, less 5 a step away from its best trip, plus or minus the going (as check() counts them); its colour card is
// the board game's: black at or above the race's top band, then red, yellow, blue. The market prices the figures
// (a horse 5 better is about twice as likely to win), with a bookmaker's margin, on the usual ladder of odds.
const CARD_KEYS = ["black", "red", "yellow", "blue"];
const CARD_ODDS = { black: [0, 4], red: [5, 10], yellow: [11, 20], blue: [25, 100] };   // each card's price range (to 1)
const ODDS_LADDER = [[1, 3], [2, 5], [1, 2], [4, 7], [8, 13], [4, 6], [8, 11], [4, 5], [10, 11], [1, 1], [6, 5], [5, 4], [11, 8], [6, 4], [13, 8], [7, 4], [15, 8], [2, 1], [9, 4], [5, 2], [11, 4], [3, 1], [10, 3], [7, 2], [4, 1], [9, 2], [5, 1], [11, 2], [6, 1], [13, 2], [7, 1], [15, 2], [8, 1], [17, 2], [9, 1], [10, 1], [11, 1], [12, 1], [14, 1], [16, 1], [18, 1], [20, 1], [25, 1], [33, 1], [40, 1], [50, 1], [66, 1], [100, 1]];
function dayFigure(h, race) {
  const lo = DISTANCES.indexOf(h.trip[0]), hi = DISTANCES.indexOf(h.trip[1]);
  const steps = race.step < lo ? lo - race.step : race.step > hi ? race.step - hi : 0;
  return h.rating - steps * 5 + groundPts(h.goings, CARD.going[race.day]);
}
function marketFor(i) {
  const race = RACES[i], field = fieldFor(i), figs = field.map(h => dayFigure(h, race));
  const w = figs.map(f => Math.exp(f / 7)), tot = w.reduce((a, b) => a + b, 0);
  const raw = w.map(x => 1 / Math.min(0.85, (x / tot) * 1.18) - 1);                 // the price against, before the cards
  const card = figs.map(f => CARD_KEYS[race.bands.findIndex(b => f >= b)] || "blue");
  // (owner, 7 Nov) the price sits in its colour card's range: black about evens to 4/1 (odds-on only for a strong
  // favourite), red 5/1 to 10/1, yellow 11/1 to 20/1, blue 25/1 and longer. The horses on one card are spread across
  // its range in the order of their chances (not all pinned at its end): the best keeps its own price if that falls
  // in the range, the weakest goes to the range's long end if its own price is longer still.
  const want = raw.slice();
  for (const key of CARD_KEYS) {
    const ks = field.map((_, k) => k).filter(k => card[k] === key);
    if (!ks.length) continue;
    const [lo, hi] = CARD_ODDS[key], L = Math.log, mid = Math.exp((L(Math.max(lo, 1)) + L(hi)) / 2);
    const rs = ks.map(k => L(raw[k])), r0 = Math.min(...rs), r1 = Math.max(...rs);
    // the card's best at its own price, kept to the shorter half of the range; its weakest at the long end
    const a = L(Math.min(Math.max(Math.exp(r0), Math.max(lo, 0.3)), ks.length > 1 ? mid : hi)), z = ks.length > 1 ? L(hi) : a;
    ks.forEach((k, j) => { want[k] = Math.exp(r1 > r0 ? a + (z - a) * (rs[j] - r0) / (r1 - r0) : a); });
  }
  return field.map((h, k) => {
    const [lo, hi] = CARD_ODDS[card[k]];
    const [n, d] = ODDS_LADDER.filter(([a, b]) => a / b >= lo - 1e-9 && a / b <= hi + 1e-9)
      .reduce((a, b) => Math.abs(Math.log(b[0] / b[1] / want[k])) < Math.abs(Math.log(a[0] / a[1] / want[k])) ? b : a);
    return { fig: figs[k], odds: n === d ? "Evens" : `${n}/${d}`, card: card[k] };
  });
}
// The race engine's course data for a race (index.html loads every course the season races on)
const engineFor = race => (ENGINE.courses && ENGINE.courses[courseFile(race)]) || { data: ENGINE.data, view: ENGINE.view };
const engineRunner = h => ({ id: h.id, name: h.name, rating: h.rating, trip: h.trip, goings: h.goings, style: h.style, flex: h.flex, temperament: h.temper, ...(h.edge || {}) });
// The race as the engine and the 3D view know it: the same five values in both, so both run the same race
function engineRace(i) {
  const race = RACES[i], v = engineFor(race).view.races[viewKey(race)];
  return { course: v.course, distance: v.distance, start: v.start, going: CARD.going[race.day], seed: String(CARD.races[i].seed) };
}
async function simRace(i) {
  await engineReady;
  if (!window.ENGINE) throw new Error("The race engine didn't load" + (window.ENGINE_FAILED ? ": " + window.ENGINE_FAILED : ""));
  const field = fieldFor(i), { result } = ENGINE.runRace(engineRace(i), field.map(engineRunner), engineFor(RACES[i]).data, { timeline: false });
  return { field, result, order: result.placed.map(p => field[p.runner].id) };
}
// The pace the racecard promises (the jockeys read it the same way before the off)
function paceFor(i) {
  if (!window.ENGINE) return null;
  const field = fieldFor(i), styles = field.map(h => h.style);
  return { pace: ENGINE.expectedPace(ENGINE.data.settings, styles), front: styles.filter(x => x === "front").length, n: styles.length };
}
const REPORT_KINDS = new Set(["missed", "led", "short", "switched", "kicked", "weakening"]);
function record(i, out) {
  const race = RACES[i], myId = S.entries[race.id], order = out.order, pos = myId ? order.indexOf(myId) + 1 : 0, R = out.result;
  const win = R.placed[0], me = pos ? R.placed[pos - 1] : null;
  S.results[race.id] = { pos, runners: order.length, prize: pos >= 1 && pos <= 4 ? race.prizes[pos - 1] : 0, winner: out.field[win.runner].name,
    time: R.winningTime, by: R.placed[1] ? R.placed[1].margin : 0, beaten: me ? me.behind : 0, pace: R.pace.run,
    report: R.events.filter(e => REPORT_KINDS.has(e.kind)).map(e => e.text).slice(0, 12) };
  save();
}
async function simAndRecord(i) { if (S.results[RACES[i].id]) return; const out = await simRace(i); if (!S.results[RACES[i].id]) record(i, out); }

/* ================= State ================= */
let S, CARD;
// Two numbers make a game. The season's number (S.seed) is the race card: the ten races, the going, the fields. That is
// what today's card shares: everyone gets the same races. The game's own luck (S.luck, drawn afresh for every game and
// every player) is the breeding and buying: which mares a pile turns over, the foal a mating gives, the Tattersalls
// catalogue, how far each rival buyer will go, what an unproven stallion is really worth (owner, 13 Nov: "the mares and
// foals etc shouldn't be pre fixed. it should work fresh for each player"). Each roll comes from the game's luck and
// what is being rolled for, never from the clock, so within one game a roll can't be taken again by reloading the page.
// (Games saved before this have no luck of their own and go on using the season's number.)
const luckOf = () => S.luck || S.seed;
const luck = key => seeded(hashStr(luckOf() + "|" + key));
function ownLuck() {
  if (!S.luck) return;
  const r = luck("stallions");
  STALLIONS.forEach(s => { CARD.trueStars[s.name] = s.base > 0 ? Math.max(1, Math.min(5, s.base + (r() < .5 ? -1 : 1))) : s.stars; });
}
// ----- Today's card: one season a day, the same for everyone, changing at midnight UK time -----
const ukDay = t => { const d = t ? new Date(t) : new Date();
  try { const o = {}; new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(d).forEach(x => o[x.type] = x.value); return `${o.year}-${o.month}-${o.day}`; }
  catch (e) { return d.toISOString().slice(0, 10); } };
// random games are numbered 1 to 1,000,000; the daily cards sit above that, each season (Royal Ascot, Newmarket) with its own
const dailySeed = day => 1000001 + hashStr("thoroughbred-daily|" + MEETING.id + "|" + day) % 2000000000;
const dayText = (day, long) => { const [y, m, d] = String(day).split("-").map(Number); return new Date(Date.UTC(y, m - 1, d, 12)).toLocaleDateString("en-GB", { timeZone: "UTC", weekday: long ? "long" : "short", day: "numeric", month: long ? "long" : "short" }); };
const isDaily = () => !!(S && S.mode === "daily");
// what a season is called on the screens: "Daily card, Fri 13 Nov" or "Season 123456"
const seasonName = (x, lower) => { x = x || S; return x.day ? `${lower ? "d" : "D"}aily card, ${dayText(x.day)}` : `${lower ? "s" : "S"}eason ${x.seed}`; };
const seasonDone = () => !!S && Object.keys(S.results).length === RACES.length;
function newCard(seed, day) {
  S = { seed: seed || Math.floor(Math.random() * 1e6) + 1, luck: Math.floor(Math.random() * 2e9) + 1, mode: day ? "daily" : "random", day: day || null, pileN: {}, step: 1, tab: "stud", budget: START_BUDGET, stable: [], hand: [], usedMares: [], deckPos: 0,
    selMare: null, foal: null, sale: [], lotN: 0, entries: {}, results: {}, open: null, silks: S ? S.silks : 0, sort: "fee", offer: null, book: 1, catDams: [], v: 8, dealt: false, tallied: false,
    team: { picks: [], offer: null, done: false, choice: {}, used: {}, trains: {}, book: {}, income: 0, incomeLog: [] } };
  CARD = makeCard(S.seed); ownLuck();
  // No starting mares: every mare is bought at the mares sale, choosing one of three
  S.selMare = null;
  save();
}
// Two saved games a season: the random game, and today's card (so starting one never loses the other)
const slotKey = mode => SAVE_KEY + (mode === "daily" ? "-daily" : "");
function save() { try { localStorage.setItem(slotKey(S.mode), JSON.stringify(S)); localStorage.setItem(MODE_KEY, S.mode === "daily" ? "daily" : "random"); } catch (e) {} }
const lastMode = () => { try { return localStorage.getItem(MODE_KEY) === "daily" ? "daily" : "random"; } catch (e) { return "random"; } };
// the saved daily card, if there is one (read without opening it): { day, done, step }
function dailySave() { try { const v = JSON.parse(localStorage.getItem(slotKey("daily")) || "null"); return v && v.seed && v.day ? v : null; } catch (e) { return null; } }
function load(mode) {
  mode = mode || "random";
  try { const v = JSON.parse(localStorage.getItem(slotKey(mode)) || "null"); if (v && v.seed && Array.isArray(v.stable)) {
    S = v; S.open = null; S.mode = mode === "daily" && S.day ? "daily" : "random"; S.pileN = S.pileN || {}; CARD = makeCard(S.seed); ownLuck(); migrate();
    // left in the middle of an auction: that lot has gone through the ring without you
    if (S.ring) { S.sale = (S.sale || []).filter(x => x.id !== S.ring); S.ring = null; save(); }
    return true; } } catch (e) {}
  return false;
}
// Saves from before the mares sale: only mares you bred from count as yours, and the ring is rebuilt into Books
function migrate() {
  if (S.v === 8) return;
  if (S.v === 7) return migrate8();
  if (S.v === 6) return migrate7();
  if (S.v === 5) return migrate6();
  if (S.v === 4) return migrate5();
  if (S.v !== 2 && S.v !== 3) {
    const bred = new Set(S.stable.filter(h => h.how === "bred").map(h => h.dam));
    S.usedMares = (S.usedMares || []).filter(n => bred.has(n));
  }
  if (S.v !== 3) { S.offer = null; S.book = 1; }
  // v4: Tattersalls became its own step after breeding. Breeding saves stay at the stud (the sale is made on arrival);
  // anything later moves up one step and keeps its catalogue.
  if (S.step >= 2) { S.step += 1; if (!S.sale || !S.sale.length) newCatalogue(); }
  else S.sale = [];
  S.v = 4; migrate5();
}
// v5: ten races drawn per card from the full programme, and a £2m budget
function migrate5() {
  S.budget += START_BUDGET - 1250000;
  const ids = new Set(RACES.map(r => r.id));
  Object.keys(S.entries || {}).forEach(k => { if (!ids.has(k)) delete S.entries[k]; });
  Object.keys(S.results || {}).forEach(k => { if (!ids.has(k)) delete S.results[k]; });
  if (S.step >= 4 && !Object.keys(S.results).length) S.step = 3;
  S.v = 5; migrate6();
}
// v6: the race engine. Horses from before it get their running style, flexibility and temperament now (fixed by their id)
function migrate6() {
  S.stable.forEach(h => { if (!h.style) Object.assign(h, rollRacecard(seeded(hashStr(h.id)))); });
  S.v = 6; migrate7();
}
// v7: your team (js/team.js). A season that hasn't left the Jockey Club yet drafts one; one already under way goes on without
function migrate7() {
  if (!S.team) S.team = S.dealt ? { picks: [], offer: null, done: true, gone: true, skipped: true, choice: {}, used: {}, trains: {}, book: {}, income: 0, incomeLog: [] }
    : { picks: [], offer: null, done: false, choice: {}, used: {}, trains: {}, book: {}, income: 0, incomeLog: [] };
  S.v = 7; migrate8();
}
// v8 (14 Nov): the mares hand. A game already buying mares, or past the stud, keeps the old mares sale
function migrate8() {
  if (S.step > 1 || studCount() > 0 || S.offer || Object.keys(S.pileN || {}).length) S.mh = { legacy: true };
  S.v = 8; save();
}
// Mares in your stud: still to breed from, plus those already used this season
const studCount = () => S.hand.length + S.usedMares.length;
const paidMares = studCount;
const ownMares = () => new Set([...S.usedMares, ...S.hand, ...(S.offer ? S.offer.mares : [])]);
const maresOut = ownMares;
// Breeding comes first, so the piles draw from the whole deck (Tattersalls is made later from what's left)
const pileLeft = p => { const own = ownMares(); return MARES.filter(m => p.stars.includes(m.stars) && !own.has(m.name)); };
const stableFull = () => S.stable.length >= STABLE_CAP;
function drawMare() {
  const out = maresOut();
  while (S.deckPos < CARD.mareOrder.length) { const n = CARD.mareOrder[S.deckPos++]; if (!out.has(n)) { S.hand.push(n); return true; } }
  return false;
}
// ----- Tattersalls lots, following the site's Tattersalls page code -----
// isMatchAllowed: not the same sire line AND code; mare at most 1★ above the stallion's shown rating,
// stallion at most 2★ above the mare; and not a stallion the mare's card excludes
function lotMatch(s, m) {
  if (s.sireLine && s.sireCode && s.sireLine === m.sireLine && s.sireCode === m.sireCode) return false;
  if (m.stars > s.shownStars + 1 || s.shownStars > m.stars + 2) return false;
  return !m.blocked.includes(s.name);
}
// "5f" -> 5, "1m2f" -> 10, "2m+" -> 18
function furlongs(v) {
  const t0 = String(v || "").toLowerCase().replace(/\s/g, ""); if (!t0) return null;
  const mm = t0.match(/(\d+)m/), ff = t0.match(/(\d+)f/); if (!mm && !ff) return null;
  let t = 0; if (mm) t += +mm[1] * 8; if (ff) t += +ff[1]; if (t0.includes("+")) t += 2;
  return (t < 4 || t > 20) ? null : t;
}
function ratingWeight(s, m) {
  const d = s.shownStars - m.stars;
  if (d <= -2) return 0; if (d === -1) return NEW_STALLIONS.has(s.name) ? 9 : 7;
  if (d === 0) return 10; if (d === 1) return 9; if (d === 2) return 8; if (d === 3) return 7; return 6;
}
function tripWeight(s, m) {
  const a = furlongs(s.optimumDistance), b = furlongs(m.optimumDistance); if (a === null || b === null) return 1;
  if (a <= 6 && b >= 10) return TRIP_WEIGHTS.sprinterVsMiddle;
  const gap = Math.abs(a - b);
  return gap <= 1 ? TRIP_WEIGHTS.close : gap <= 2 ? TRIP_WEIGHTS.near : gap <= 4 ? TRIP_WEIGHTS.mid : TRIP_WEIGHTS.far;
}
function weightedMare(list, s, rnd) {
  const w = list.map(m => Math.max(0, ratingWeight(s, m) * tripWeight(s, m))), total = w.reduce((a, b) => a + b, 0);
  if (total <= 0) return list[Math.floor(rnd() * list.length)];
  let r = rnd() * total; for (let i = 0; i < list.length; i++) { r -= w[i]; if (r <= 0) return list[i]; }
  return list[list.length - 1];
}
// The catalogue: each Book has three different stallions (none repeated across Books), each bringing three
// lots with weighted mares (the site's rules). Every Book has a sprint pedigree and a staying pedigree.
const optF = x => furlongs(x.optimumDistance) || 8;
function newCatalogue() {
  const out = new Set(S.usedMares), used = new Set(), lots = [], rnd = luck("catalogue");
  const shuffle = a => { for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(rnd() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; };
  const sires = shuffle(STALLIONS.map(s => stallion(s.name)));
  for (const b of BOOKS) {
    const fits = (s, m) => !out.has(m.name) && !used.has(m.name) && lotMatch(s, m) && s.shownStars + m.stars >= b.min && s.shownStars + m.stars <= b.max;
    // Each lot draws its own stallion at random from those who fit this Book (no more than two lots by one stallion in a Book),
    // so a Book can hold anything from four to nine different sires; one sprint and one staying pedigree are still guaranteed
    const book = [], perSire = {};
    const addLot = (sireTest, mareTest) => {
      const ok = sires.filter(s => (perSire[s.name] || 0) < 2 && sireTest(s) && MARES.some(m => fits(s, m) && mareTest(m)));
      if (!ok.length) return false;
      const s = ok[Math.floor(rnd() * ok.length)];
      let valid = MARES.filter(m => fits(s, m)); const q = valid.filter(mareTest); if (q.length) valid = q;
      const m = weightedMare(valid, s, rnd); used.add(m.name); perSire[s.name] = (perSire[s.name] || 0) + 1;
      book.push({ book: b.n, sire: s.name, dam: m.name, reserve: RESERVES[s.shownStars + m.stars] || 10000 });
      return true;
    };
    addLot(s => optF(s) <= 6, m => optF(m) <= 7);
    addLot(s => optF(s) >= 12, m => optF(m) >= 12);
    for (let tries = 0; book.length < LOTS_PER_BOOK && tries < 40; tries++) addLot(() => true, () => true);
    shuffle(book).forEach(l => lots.push({ id: "lot" + (++S.lotN), n: S.lotN, ...l }));
  }
  S.sale = lots; S.catDams = [...used];
}
// Mares sale: pay the pile's price, two of its mares are turned over, and you keep one
// (owner, 10 Nov: two mares turned over for everyone). Since 14 Nov this is only for the one extra mare: your stud
// starts with a dealt hand (below)
const OFFER_SIZE = 2;
// a pile's mares in this game's order for one draw (tag): each mare has her own place in it
const pileOrder = (p, tag) => pileLeft(p).map(m => [hashStr(luckOf() + "|" + tag + "|" + m.name), m]).sort((a, b) => a[0] - b[0] || (a[1].name < b[1].name ? -1 : 1)).map(x => x[1]);
function drawPile(id) {
  const p = PILES.find(x => x.id === id); if (S.offer || !p || studCount() >= MARE_CAP || p.price > S.budget) return;
  if (handOn() && extraLeft() <= 0) return;
  if (!pileLeft(p).length) return;
  S.pileN = S.pileN || {}; const n = S.pileN[id] = (S.pileN[id] || 0) + 1;
  const left = pileOrder(p, "pile|" + id + "|" + n);
  S.budget -= p.price; if (typeof ledger === "function") ledger("mares", p.price);
  if (handOn()) mh().extra++;
  S.offer = { pile: p.id, mares: left.slice(0, offerSize()).map(m => m.name) };
}
function keepOffer(name) {
  if (!S.offer || !S.offer.mares.includes(name)) return;
  const was = S.offer.swap;
  if (was && S.hand.includes(was)) { S.hand[S.hand.indexOf(was)] = name; mh().up = (mh().up || 0) + 1; }
  else S.hand.push(name);
  S.offer = null;
  const m = byName(name); toast(was ? `${m.name} (${m.stars}★) takes ${was}'s place in your stud` : `${m.name} (${m.stars}★) joins your stud`);
}
// ----- Your mares hand (owner, 14 Nov: "a deal would be better ... 2 of each ... + an opportunity to buy an extra one
// with a choice, at the current price ... cut the budget down to reflect you no longer have to buy mares"). The stud
// opens with a hand dealt from the piles: 2 Blue-blooded, 2 Useful, 2 Moderate (2 of each, as the big races want
// Blue-blooded mares). You may buy one extra mare (pick a pile, see two, keep one), and send back any mare you
// don't want to breed from for half her pile's price, so a player who'd rather shop at Tattersalls can. Games saved
// before the hand (S.mh.legacy) keep buying their mares.
const HAND = { hi: 2, mid: 2, lo: 2 }, EXTRA_MARES = 1, SEND_BACK = 0.5;
const mh = () => (S.mh = S.mh || { dealt: false, extra: 0, up: 0, sent: [] });
const handOn = () => !(S.mh && S.mh.legacy);
const extraLeft = () => handOn() ? EXTRA_MARES - (mh().extra || 0) : 99;
const pileOf = name => { const m = byName(name); return PILES.find(p => p.stars.includes(m.stars)); };
const sendBackFor = name => Math.round(pileOf(name).price * SEND_BACK / 500) * 500;
function dealHand() {
  if (!handOn() || mh().dealt || S.step !== 1) return false;
  const got = [];
  for (const p of PILES) got.push(...pileOrder(p, "hand|" + p.id).slice(0, HAND[p.id] || 0).map(m => m.name));
  S.hand.push(...got); mh().dealt = true; mh().hand = got.slice();
  save(); return true;
}
function sendBack(name) {
  if (!handOn() || S.step !== 1 || !S.hand.includes(name) || (S.offer && S.offer.swap === name) || (S.foal && S.foal.h.dam === name)) return 0;
  const back = sendBackFor(name);
  S.hand = S.hand.filter(n => n !== name); mh().sent.push(name); if (S.selMare === name) S.selMare = null;
  S.budget += back; if (typeof ledger === "function") ledger("mares", -back);
  save(); return back;
}
function newName(rnd) {
  const taken = new Set([...CARD.oppNames, ...S.stable.map(h => h.name)]);
  for (let k = 0; k < 300; k++) { const n = (NAME_A[Math.floor(rnd() * NAME_A.length)] + " " + NAME_B[Math.floor(rnd() * NAME_B.length)]).toUpperCase(); if (!taken.has(n)) return n; }
  return "FOAL " + (S.stable.length + 1);
}
function breed(sireName, damName, how, cost, lotRef) {
  // the foal is this game's foal of this sire and dam, however and whenever it is bred or bought; a Sales Scout's find
  // (js/team.js) carries its own yearling (lot.fs). lotRef is the lot itself or its id
  const lot = lotRef && typeof lotRef === "object" ? lotRef : lotRef && (S.sale || []).find(l => l.id === lotRef), lotId = lot ? lot.id : lotRef;
  const rnd = lot && lot.fs != null ? seeded(lot.fs) : luck("foal|" + sireName + "|" + damName);
  const s = stallion(sireName), m = byName(damName), f = breedPure(s, m, rnd);
  let id = "h" + hashStr(luckOf() + "|foal|" + sireName + "|" + damName).toString(36); while (S.stable.some(x => x.id === id)) id += "x";
  const h = { id, name: newName(rnd), sex: rnd() < .5 ? "F" : "C", sire: s.name, dam: m.name,
    peakAge: f.peakAge, r: f.r, d: f.d, grounds: f.grounds, age: 2, portrait: 1 + Math.floor(rnd() * 12), coat: COATS[Math.floor(rnd() * COATS.length)], how, cost };
  h.verdict = verdictFor(h);
  Object.assign(h, rollRacecard(rnd));
  S.foal = { h, how, cost, lotId, retried: S.foal && S.foal.h && S.foal.how === "bred" && S.foal.h.dam === damName && S.foal.h.sire === sireName ? true : false };
}
function keepFoal(name) {
  const F = S.foal; if (!F) return;
  const nm = name && String(name).trim().toUpperCase();
  if (nm && !S.stable.some(h => h.name === nm) && !CARD.oppNames.has(nm)) F.h.name = nm;
  if (F.how === "bred") {
    S.budget -= F.cost; if (typeof ledger === "function") ledger("fees", F.cost);
    if (S.team && typeof ownedStallion === "function" && ownedStallion() === F.h.sire && F.cost === 0) S.team.used.stallion = (S.team.used.stallion || 0) + 1;   // a free nomination to your own stallion
    S.usedMares.push(F.h.dam); S.hand = S.hand.filter(n => n !== F.h.dam); S.selMare = null; S.selStallion = null;
  }
  S.stable.push(F.h); S.foal = null; save();
  toast(`${F.h.name} is on your stud farm`);
}
function letGo() {
  const F = S.foal; if (!F) return;
  // the mare's season is used up; no stud fee is paid
  S.usedMares.push(F.h.dam); S.hand = S.hand.filter(n => n !== F.h.dam); S.selMare = S.hand[0] || null;
  S.foal = null; save();
}
function develop(id) {
  const h = horse(id); if (!h || h.age >= 4) return;
  h.age += 1;
  RACES.forEach(r => { if (S.entries[r.id] === id && !check(h, r).ok) delete S.entries[r.id]; });
  save();
}

/* ================= The ambition: prize money earns a title ================= */
const TITLES = MEETING.titles;
const titleFor = prize => TITLES.find(t => prize >= t.min);
const BEST_KEY = "tb-" + MEETING.id + "-best", HIST_KEY = "tb-" + MEETING.id + "-history", SAVE_KEY = "tb-game-" + MEETING.id;
const MODE_KEY = "tb-" + MEETING.id + "-mode", DAILY_KEY = "tb-" + MEETING.id + "-daily-log";
// Today's card counts once: the first time a day's card is finished, its result is written here and stays
function dailyLog() { try { const v = JSON.parse(localStorage.getItem(DAILY_KEY) || "{}"); return v && typeof v === "object" ? v : {}; } catch (e) { return {}; } }
function noteDaily(prize, wins) {
  if (!isDaily()) return;
  try { const log = dailyLog(); if (log[S.day]) return;
    log[S.day] = { seed: S.seed, prize, wins, races: RACES.length, title: titleFor(prize).name, silks: mySilkN(), colours: MY ? MY.code : undefined, when: Date.now() };
    const days = Object.keys(log).sort(); days.slice(0, Math.max(0, days.length - 400)).forEach(d => delete log[d]);
    localStorage.setItem(DAILY_KEY, JSON.stringify(log)); } catch (e) {}
  // and it goes on the leaderboard (js/leaderboard.js)
  try { if (window.lbSubmit) lbSubmit({ season: MEETING.id, kind: "daily", day: S.day, seed: S.seed, prize, wins, title: titleFor(prize).name }); } catch (e) {}
}
function pastWeeks() { try { const h = JSON.parse(localStorage.getItem(HIST_KEY) || "[]"); return Array.isArray(h) ? h : []; } catch (e) { return []; } }
function addWeek(prize, wins) {
  try {
    const h = pastWeeks(); if (h.some(w => w.seed === S.seed && w.prize === prize)) return h;
    h.push({ seed: S.seed, day: S.day || undefined, prize, wins, races: RACES.length, title: titleFor(prize).name, when: Date.now() });
    localStorage.setItem(HIST_KEY, JSON.stringify(h.slice(-200)));
    // a finished random game goes on the leaderboard's best-ever board (the daily card is sent by noteDaily)
    try { if (!isDaily() && window.lbSubmit) lbSubmit({ season: MEETING.id, kind: "random", day: "", seed: S.seed, prize, wins, title: titleFor(prize).name }); } catch (e) {}
    return h;
  } catch (e) { return []; }
}
function bestWeek() { try { return JSON.parse(localStorage.getItem(BEST_KEY) || "null"); } catch (e) { return null; } }
function noteWeek(prize, wins) { try { const b = bestWeek(); if (!b || prize > b.prize) localStorage.setItem(BEST_KEY, JSON.stringify({ prize, wins, seed: S.seed, day: S.day || undefined })); } catch (e) {} }
const LADDER_TOP = MEETING.ladderTop;

/* ================= Tattersalls: the rival buyers in the live auction ================= */
// (the auction itself is drawn by js/ui-parts.js; these are its rules)
// "band" is the trip band of a pedigree's best distance (sprint, mile, middle, staying)
function band(d) { const i = DISTANCES.indexOf(d); return i <= 1 ? "sprint" : i <= 4 ? "mile" : i <= 6 ? "middle" : "staying"; }
const tripOf = l => band(stallion(l.sire).optimumDistance);
const RIVALS = [
  { id: "hf", name: "Highfield Bloodstock", seat: [27, 23], c: "#d9b04f", want: l => l.book === 1 ? 1.25 : l.book === 2 ? 1.05 : .55, keen: l => l.book === 1 ? .9 : l.book === 2 ? .6 : .3 },
  { id: "cr", name: "Corrigan Racing", seat: [73, 23], c: "#e0603f", want: l => tripOf(l) === "sprint" ? 1.3 : tripOf(l) === "mile" ? 1.05 : .8, keen: () => .65 },
  { id: "sv", name: "Severn Bloodstock", seat: [9, 47], c: "#6fa3c0", want: l => l.book === 1 ? .8 : 1.02, keen: () => .85 },
  { id: "as", name: "Ashdown Stud", seat: [91, 51], c: "#9b7ccc", want: l => ["middle", "staying"].includes(tripOf(l)) ? 1.25 : .85, keen: () => .6 },
  { id: "mm", name: "Merriman & Co", seat: [23, 87], c: "#5fb07f", want: () => 1, keen: () => .6 }
];
const ME_SEAT = [77, 86];
const round5k = v => Math.max(5000, Math.round(v / 5000) * 5000);
const incFor = p => p < 50000 ? 5000 : p < 200000 ? 10000 : 25000;
// Bidding opens at the reserve (rules TA-9; recordSale refuses anything lower)
const openBid = l => l.reserve;
const guide = l => [l.reserve, round5k(l.reserve * 1.6)];
// How hard the rivals chase the best Books (Book 1 cooled from 1.45, Book 2 from 1.15 on 6 Nov 2026, with the dearer
// Blue-blooded mares: buying a top horse is now a real option beside breeding one)
const BOOK_HEAT = [1.3, 1.1];
function appeal(l, rnd) {
  const s = stallion(l.sire), m = byName(l.dam), ln = lineNote(s, m).cls;
  let a = 1 + (ln === "out" ? .12 : ln === "in2" ? -.15 : 0);
  if (s.unproven) a *= .85 + (rnd || Math.random)() * .4;   // rivals take a punt on unproven sires
  // the best pedigrees draw the deepest pockets: Book 1 is fought over, Book 2 a little
  a *= l.book === 1 ? BOOK_HEAT[0] : l.book === 2 ? BOOK_HEAT[1] : 1;
  return a;
}
