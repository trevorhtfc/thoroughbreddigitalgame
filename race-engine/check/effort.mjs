// When do jockeys start working? For each horse: the distance out where it first pushes (effort 1 or more, after the
// first furlong) and first drives (2 or more), by where it sits in the field 4f out and by the pace as run.
//   node check/effort.mjs [distance key] [races]
import { runRace } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
const [key = "s1m", N = "200"] = process.argv.slice(2);
const r = RACES[key], F = 201.168, rows = {};
for (let s = 0; s < +N; s++) {
  const seed = `eff:${key}:${s}`;
  const { timeline, result } = runRace({ ...r, going: "Good", seed }, randomField(12, seed, data.settings), data);
  const pace = result.pace.run === "strong" ? "even" : result.pace.run;      // slow / even (incl. strong) / fast
  const fr = timeline.frames, n = fr[0].length;
  const k4 = fr.findIndex((f) => Math.max(...f.map((h) => h[0])) >= r.distance - 4 * F);
  const at4 = fr[k4].map((h, i) => [h[0], i]).sort((a, b) => b[0] - a[0]);
  for (let pos = 0; pos < n; pos++) {
    const i = at4[pos][1], where = pos === 0 ? "leader" : pos < 4 ? "close" : pos >= n - 4 ? "back" : "middle";
    const first = (lvl) => { for (const f of fr) { const h = f[i]; if (h[0] > 300 && h[0] < r.distance && h[3] >= lvl) return (r.distance - h[0]) / F; } return 0; };
    const k = `${pace}/${where}`;
    (rows[k] ||= { push: [], drive: [] }).push.push(first(1));
    rows[k].drive.push(first(2));
  }
}
const med = (a) => { const s = [...a].sort((p, q) => p - q); return s[s.length >> 1]; };
const q = (a, f) => { const s = [...a].sort((p, q) => p - q); return s[Math.floor(f * (s.length - 1))]; };
console.log(`${key}: furlongs out when first pushed / first driven (median, with the 10%-90% spread), by place 4f out`);
for (const pace of ["slow", "even", "fast"]) for (const where of ["leader", "close", "middle", "back"]) {
  const R = rows[`${pace}/${where}`]; if (!R) continue;
  console.log(`  ${pace.padEnd(5)} ${where.padEnd(6)} push ${med(R.push).toFixed(1)}f (${q(R.push, .1).toFixed(1)}-${q(R.push, .9).toFixed(1)})   drive ${med(R.drive).toFixed(1)}f (${q(R.drive, .1).toFixed(1)}-${q(R.drive, .9).toFixed(1)})   n=${R.push.length}`);
}
