// The engine against the bench: thousands of races at every distance, the same figures as the bench's
// (tools/race-bench/benchstats.py), side by side.
//   node check/compare.mjs [races per distance] [runners] [workers]     (writes check/results/engine.json and compare.md)
import { Worker, isMainThread, parentPort, workerData } from "node:worker_threads";
import { writeFileSync, readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { runRace, makeRandom } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES, REPO } from "./data.mjs";

const PACES = ["slow", "even", "strong", "fast"], STY = { front: "F", prominent: "P", midfield: "M", holdup: "H" };

function racesFor(key, from, to, n) {
  const out = [];
  for (let k = from; k < to; k++) {
    const seed = `${process.env.SEED_TAG || ""}${key}:${k}`;
    const { result } = runRace({ ...RACES[key], going: "Good", seed }, randomField(n, seed, data.settings), data, { timeline: false });
    const tie = makeRandom("tie:" + seed);
    const byDraw = [...result.placed].sort((a, b) => a.draw - b.draw);
    const rd = byDraw.map((p) => p.dayRating + tie.next() * 1e-3);
    const best = rd.indexOf(Math.max(...rd));
    const [w, s] = result.placed;
    out.push({
      time: w.time, margin: (s.time - w.time) * result.parSpeed / data.settings.rules.LENGTH,
      bestWon: result.winner === best, winStyle: STY[w.style], winDraw: w.draw, pace: result.pace.expected,
      styles: byDraw.map((p) => STY[p.style]), lost: byDraw.map((p) => p.lostLengths),
    });
  }
  return out;
}

if (!isMainThread) {
  const { key, from, to, n } = workerData;
  parentPort.postMessage(racesFor(key, from, to, n));
} else {
  const N = +(process.argv[2] || 2000), n = +(process.argv[3] || 12), W = +(process.argv[4] || 2);
  // the bench's numbers in the engine's settings must be the bench's own
  const bench = JSON.parse(readFileSync(join(REPO, "tools/race-bench/settings.json"), "utf8"));
  const mine = data.settings.bench, diff = Object.keys({ ...bench, ...mine }).filter((k) => JSON.stringify(bench[k]) !== JSON.stringify(mine[k]));
  if (diff.length) { console.error("settings.json -> bench differs from tools/race-bench/settings.json:", diff.join(", ")); process.exit(1); }
  const median = (a) => { const s = [...a].sort((p, q) => p - q), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };
  const res = {};
  for (const key of Object.keys(RACES).filter((k) => !process.env.ONLY || process.env.ONLY.split(",").includes(k))) {
    const t0 = Date.now(), chunk = Math.ceil(N / W);
    const parts = await Promise.all(Array.from({ length: W }, (_, w) => new Promise((ok, bad) => {
      const wk = new Worker(new URL(import.meta.url), { workerData: { key, from: w * chunk, to: Math.min(N, (w + 1) * chunk), n } });
      wk.on("message", ok); wk.on("error", bad);
    })));
    const R = parts.flat();
    const share = (f) => R.filter(f).length / R.length;
    const styleShare = (rs, s) => { const all = rs.flatMap((r) => r.styles); return (rs.filter((r) => r.winStyle === s).length / rs.length) / (all.filter((x) => x === s).length / all.length); };
    const third = (d) => (d <= Math.ceil(n / 3) ? "low" : d <= Math.ceil(n / 3) + Math.ceil((n - Math.ceil(n / 3)) / 2) ? "mid" : "high");
    const sizes = { low: 0, mid: 0, high: 0 }; for (let d = 1; d <= n; d++) sizes[third(d)]++;
    const lost = R.flatMap((r) => r.lost);
    res[key] = {
      races: R.length, runners: n,
      time: median(R.map((r) => r.time)), margin: median(R.map((r) => r.margin)), best: share((r) => r.bestWon),
      style: Object.fromEntries("FPMH".split("").map((s) => [s, styleShare(R, s)])),
      draw: Object.fromEntries(["low", "mid", "high"].map((t) => [t, share((r) => third(r.winDraw) === t) / (sizes[t] / n)])),
      lose1: lost.filter((l) => l >= 1).length / lost.length, lost: lost.reduce((a, b) => a + b, 0) / lost.length,
      paceMix: Object.fromEntries(PACES.map((p) => [p, share((r) => r.pace === p)])),
      byPace: Object.fromEntries(PACES.filter((p) => R.filter((r) => r.pace === p).length >= 20).map((p) => { const rs = R.filter((r) => r.pace === p); return [p, Object.fromEntries("FPMH".split("").map((s) => [s, styleShare(rs, s)]))]; })),
    };
    console.log(key, ((Date.now() - t0) / 1000).toFixed(0) + "s", JSON.stringify({ time: res[key].time, best: res[key].best.toFixed(3), style: res[key].style, lose1: res[key].lose1.toFixed(3) }));
    writeFileSync(join(REPO, `race-engine/check/results/${process.env.OUT || "engine"}.json`), JSON.stringify(res, null, 1));
  }
}
