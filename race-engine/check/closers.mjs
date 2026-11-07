// Do horses come from the back? (owner, 7 Nov: "very little in horses coming from the back")
// For many races: where the winner (and the placed horses) were at 4f, 3f, 2f and 1f out, and how much the order
// changes in the run for home. node check/closers.mjs [races per distance] [field size] [keys...]
import { runRace } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
if (process.env.SET) { const o = JSON.parse(process.env.SET); Object.assign(data.settings.bench, o); }   // try settings: SET='{"KICK_STYLE":[1,1,.85,.7]}'
const argv = process.argv.slice(2);
const N = +(argv[0] || 300), FIELD = +(argv[1] || 16), KEYS = argv.slice(2).length ? argv.slice(2) : ["s6f", "s1m", "r1m", "r1m4f", "r2m"];
const F = 201.17, MARKS = [4, 3, 2, 1];
const spearman = (a, b) => { const n = a.length; let d = 0; for (let i = 0; i < n; i++) d += (a[i] - b[i]) ** 2; return 1 - 6 * d / (n * (n * n - 1)); };
const out = {};
for (const key of KEYS) {
  const R = RACES[key], S = { best: 0, worst: 0, winFromBackHalf: {}, winRank: {}, placedFromBack: 0, rho2: 0, gainedTop3: 0, style: {}, styleRunners: {}, winLBehind2f: [] };
  for (const m of MARKS) { S.winFromBackHalf[m] = 0; S.winRank[m] = []; }
  for (let s = 0; s < N; s++) {
    const seed = `${key}-${FIELD}-${s}`;
    const runners = randomField(FIELD, seed, data.settings);
    const { timeline, result } = runRace({ ...R, going: "Good", seed }, runners, data);
    const D = R.distance, fr = timeline.frames;
    const finish = new Array(FIELD); for (const p of result.placed) finish[p.draw - 1] = p.place;
    const ranksAt = {};
    for (const m of MARKS) {
      const at = fr.find((f) => Math.max(...f.map((h) => h[0])) >= D - m * F) || fr[fr.length - 1];
      const order = at.map((h, i) => [h[0], i]).sort((a, b) => b[0] - a[0]);
      const rank = new Array(FIELD); order.forEach(([, i], k) => (rank[i] = k + 1));
      ranksAt[m] = { rank, lead: order[0][0], at };
    }
    const w = result.placed[0].draw - 1;
    const rts = result.placed.map((p) => p.dayRating), top = Math.max(...rts), bot = Math.min(...rts);
    if (result.placed[0].dayRating === top) S.best++; if (result.placed[0].dayRating === bot) S.worst++;
    for (const m of MARKS) { const r = ranksAt[m].rank[w]; S.winRank[m].push(r); if (r > FIELD / 2) S.winFromBackHalf[m]++; }
    S.winLBehind2f.push((ranksAt[2].lead - ranksAt[2].at[w][0]) / 2.4);
    for (const p of result.placed.slice(0, 3)) if (ranksAt[2].rank[p.draw - 1] > FIELD / 2) S.placedFromBack++;
    for (const p of result.placed.slice(0, 3)) if (ranksAt[2].rank[p.draw - 1] > 3) S.gainedTop3++;
    S.rho2 += spearman(ranksAt[2].rank, finish);
    const st = result.placed[0].ridden || result.placed[0].style; S.style[st] = (S.style[st] || 0) + 1;
    for (const p of result.placed) { const x = p.ridden || p.style; S.styleRunners[x] = (S.styleRunners[x] || 0) + 1; }
  }
  const med = (a) => { const b = a.slice().sort((x, y) => x - y); return b[b.length >> 1]; };
  const pct = (x) => (100 * x / N).toFixed(0) + "%";
  out[key] = S;
  if (process.env.COMPACT) { const hu = ((S.style.holdup || 0) / N * 100).toFixed(0), md = ((S.style.midfield || 0) / N * 100).toFixed(0), fr = ((S.style.front || 0) / N * 100).toFixed(0);
    console.log(`${key.padEnd(6)} back half 2f ${pct(S.winFromBackHalf[2]).padStart(4)} 1f ${pct(S.winFromBackHalf[1]).padStart(3)} | L behind 2f ${med(S.winLBehind2f).toFixed(1)} | led 2f ${pct(S.winRank[2].filter((r) => r === 1).length).padStart(4)} | rho ${(S.rho2 / N).toFixed(2)} | wins front ${fr} mid ${md} hold ${hu} | best ${pct(S.best)} worst ${pct(S.worst)}`); continue; }
  console.log(`\n${key} (${N} races, ${FIELD} runners)`);
  console.log("  winner in the back half of the field at:", MARKS.map((m) => `${m}f out ${pct(S.winFromBackHalf[m])}`).join(", "));
  console.log("  winner's median place at:", MARKS.map((m) => `${m}f ${med(S.winRank[m])}`).join(", "));
  console.log("  winner's place 2f out, share:", [1, 2, 3, "4-6", "7-10", "11+"].map((b) => { const r = S.winRank[2];
    const c = typeof b === "number" ? r.filter((x) => x === b).length : b === "4-6" ? r.filter((x) => x >= 4 && x <= 6).length : b === "7-10" ? r.filter((x) => x >= 7 && x <= 10).length : r.filter((x) => x >= 11).length; return `${b}: ${pct(c)}`; }).join("  "));
  console.log(`  winner's median lengths behind the leader 2f out: ${med(S.winLBehind2f).toFixed(1)} L`);
  console.log(`  first three home who were outside the first three 2f out: ${(S.gainedTop3 / N).toFixed(2)} a race; from the back half: ${(S.placedFromBack / N).toFixed(2)} a race`);
  console.log(`  top-rated (or joint) wins ${pct(S.best)}; bottom-rated (or joint) wins ${pct(S.worst)}`);
  console.log(`  order 2f out vs finish (1 = unchanged): ${(S.rho2 / N).toFixed(2)}`);
  console.log("  wins by riding style (share of wins / share of runners):", Object.keys(S.styleRunners).map((k) => `${k} ${((S.style[k] || 0) / N * 100).toFixed(0)}% / ${(S.styleRunners[k] / N / FIELD * 100).toFixed(0)}%`).join(", "));
}
