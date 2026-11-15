// Is the game balanced? (owner, 15 Nov 2026: "a very front runner friendly game … horses at the back struggle to get
// involved … pace collapses are rare … horses switching 5 or 6 times and seemingly getting physically stuck")
// Races with fields like the game's (big fields, ratings spread across four bands, every horse at its trip), on every
// course. For each distance: wins by riding style against their share, where the winner was at 3f and 2f out, how often
// the pace collapses, the best and worst horse's wins, and the traffic (switches, changes of side, seconds held up).
//
//   node check/balance.mjs [races per distance] [keys...]        COURSE=newmarket / july for the other courses
//   CENTRE=113 (the field's middle rating, default 100), FIELD=16 (else the game's sizes), SET='{"KICK_STYLE":[...]}'
import { runRace, makeRandom } from "../engine.js";
import { data, RACES, COURSE } from "./data.mjs";
if (process.env.SET) { const o = JSON.parse(process.env.SET); for (const [k, v] of Object.entries(o)) { const sec = ["bench", "rules", "benchDefaults", "balance"].find((s) => data.settings[s] && k in data.settings[s]) || "bench"; data.settings[sec][k] = v; } }
const argv = process.argv.slice(2);
const N = +(argv[0] || 200);
const KEYS = argv.slice(1).length ? argv.slice(1) : Object.keys(RACES);
const CENTRE = +(process.env.CENTRE || 100), FIXED = process.env.FIELD ? +process.env.FIELD : null;
const F = 201.168, H = data.settings.horse;

// A field like the game's: four rating bands 5 apart (the top one 9 wide), most runners in the middle two, one in the
// top band and one in the bottom; random styles, flexibility and temperament as the game rolls them; at its trip.
function gameField(n, seed, distance) {
  const r = makeRandom("bal:" + seed);
  const b0 = CENTRE + 9, bands = [b0, b0 - 5, b0 - 10, b0 - 15], top = [b0 + 8, b0 - 1, b0 - 6, b0 - 11], w = [1, 2, 3, 2];
  const steps = H.TRIP_LADDER_FURLONGS, f = distance / F;
  let at = 0; steps.forEach((s, i) => { if (Math.abs(s - f) < Math.abs(steps[at] - f)) at = i; });
  return Array.from({ length: n }, (_, k) => {
    const d = k === 0 ? 0 : k === 1 ? 3 : r.choice(w);
    const up = r.chance(0.5), lo = Math.max(0, Math.min(steps.length - 2, up ? at : at - 1));
    return {
      name: `No. ${k + 1}`, rating: r.int(bands[d], top[d] + 1),
      style: H.STYLES[r.choice([0.25, 0.25, 0.25, 0.25])], flex: H.FLEX[r.choice([0.3, 0.5, 0.2])],
      temperament: r.chance(0.3) ? "keen" : "calm", trip: [H.TRIP_LADDER[lo], H.TRIP_LADDER[lo + 1]],
    };
  });
}
// the game's field sizes by course and trip (a spread round them)
const sizeFor = (R, r) => FIXED || (R.course === "straight" ? r.int(12, 25) : r.int(9, 17));

const pct = (x, n) => (n ? (100 * x / n).toFixed(0) : "-") + "%";
const med = (a) => { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : NaN; };
const rows = [];
const byPace = {};   // over every distance: wins and runners ridden on the pace (front, prominent) and off it, by the pace as run
for (const key of KEYS) {
  const R = RACES[key];
  if (!R) { console.error("no race", key); continue; }
  const S = { n: 0, styleW: [0, 0, 0, 0], styleN: [0, 0, 0, 0], back3: 0, back2: 0, led2: 0, behind2: [], best: 0, worst: 0, collapse: 0, fastN: 0, fastCollapse: 0,
    frontTop3: 0, paceN: { slow: 0, even: 0, strong: 0, fast: 0 }, halfTop3Home: 0, sw: 0, swHome: [], rev: 0, many: 0, held: 0, horses: 0, maxSw: 0, wFromBack4: 0 };
  for (let s = 0; s < N; s++) {
    const seed = `${COURSE}-${key}-${s}`, rr = makeRandom("size:" + seed), n = Math.min(sizeFor(R, rr), data.stalls.maxRunners);
    const runners = gameField(n, seed, R.distance);
    const going = ["Good", "Good", "Quicker", "Softer", "Quick", "Heavy"][rr.int(0, 6)];
    const { timeline, result } = runRace({ course: R.course, distance: R.distance, start: R.start, going, seed }, runners, data);
    const D = R.distance, fr = timeline.frames;
    const rankAt = (toGo) => {
      const f = fr.find((f) => Math.max(...f.map((h) => h[0])) >= D - toGo) || fr[fr.length - 1];
      const o = f.map((h, i) => [h[0], i]).sort((a, b) => b[0] - a[0]), rank = new Array(n);
      o.forEach(([, i], k) => (rank[i] = k + 1));
      return { rank, lead: o[0][0], f };
    };
    const w = result.placed[0].runner, at3 = rankAt(3 * F), at2 = rankAt(2 * F), at4 = rankAt(4 * F), half = rankAt(D / 2);
    S.n++; S.paceN[result.pace.run]++;
    const st = H.STYLES.indexOf(result.placed[0].ridden); S.styleW[st]++;
    for (const p of result.placed) S.styleN[H.STYLES.indexOf(p.ridden)]++;
    { const B = (byPace[result.pace.run] ||= { races: 0, onW: 0, onN: 0, offW: 0, offN: 0, n: 0 }); B.races++; B.n += n;
      for (const p of result.placed) { const on = p.ridden === "front" || p.ridden === "prominent"; if (on) B.onN++; else B.offN++; if (p.place === 1) { if (on) B.onW++; else B.offW++; } } }
    if (at3.rank[w] > n / 2) S.back3++;
    if (at2.rank[w] > n / 2) S.back2++;
    if (at4.rank[w] > n / 2) S.wFromBack4++;
    if (at2.rank[w] === 1) S.led2++;
    S.behind2.push((at2.lead - at2.f[w][0]) / 2.4);
    const rts = result.placed.map((p) => p.dayRating), top = Math.max(...rts), bot = Math.min(...rts);
    if (result.placed[0].dayRating === top) S.best++;
    if (result.placed[0].dayRating === bot) S.worst++;
    // a pace collapse: none of the first three at halfway, nor any horse ridden from the front or prominent, in the first three home
    const top3 = result.placed.slice(0, 3);
    const halfIn = top3.filter((p) => half.rank[p.runner] <= 3).length;
    S.halfTop3Home += halfIn;
    const onPace = top3.filter((p) => p.ridden === "front" || p.ridden === "prominent").length;
    S.frontTop3 += onPace;
    const collapse = halfIn === 0 && onPace === 0;
    if (collapse) S.collapse++;
    if (result.pace.run === "fast" || result.pace.run === "strong") { S.fastN++; if (collapse) S.fastCollapse++; }
    for (const p of result.placed) {
      S.horses++; S.sw += p.switches; S.rev += p.sideChanges; S.held += p.heldSeconds;
      if (p.switches >= 3) S.many++;
      S.maxSw = Math.max(S.maxSw, p.switches);
    }
  }
  const share = S.styleN.map((x) => x / S.horses), ae = S.styleW.map((x, i) => (x / S.n / share[i]).toFixed(2));
  rows.push([key, S.n, ae.join(" "), pct(S.back3, S.n), pct(S.back2, S.n), pct(S.led2, S.n), med(S.behind2).toFixed(1), pct(S.collapse, S.n), pct(S.fastCollapse, S.fastN),
    (S.halfTop3Home / S.n).toFixed(2), pct(S.best, S.n), pct(S.worst, S.n), (S.sw / S.horses).toFixed(2), (S.rev / S.horses).toFixed(2), pct(S.many, S.horses), S.maxSw, (S.held / S.horses).toFixed(1),
    Object.values(S.paceN).map((v) => (100 * v / S.n).toFixed(0)).join("/")]);
}
const head = ["race", "n", "wins÷share F P M H", "win back½ 3f", "back½ 2f", "led 2f", "L down 2f", "collapse", "in fast/strong", "halfway top3 home", "best", "worst", "switches", "side changes", "3+ sw", "max sw", "held s", "pace s/e/st/f %"];
console.log(`${COURSE}, centre ${CENTRE}${FIXED ? ", field " + FIXED : ""}`);
console.log(head.join(" | "));
for (const r of rows) console.log(r.join(" | "));
console.log("by pace as run (all distances): wins÷share on the pace (front+prominent) / off it (midfield+hold-up)");
for (const k of ["slow", "even", "strong", "fast"]) { const B = byPace[k]; if (!B) continue;
  const on = (B.onW / B.races) / (B.onN / B.n), off = (B.offW / B.races) / (B.offN / B.n);
  console.log(`  ${k.padEnd(6)} ${String(B.races).padStart(4)} races: on ${on.toFixed(2)}  off ${off.toFixed(2)}`); }
