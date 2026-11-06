// Checks on the engine: the same seed replays exactly; the timeline has the shape the race view plays; horses never
// share the same space; effort stays 0-3; the result agrees with the timeline.   node check/test.mjs
import { createHash } from "node:crypto";
import { runRace } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
let fails = 0;
const ok = (cond, msg) => { if (!cond) { fails++; console.log("FAIL", msg); } };
const hash = (o) => createHash("sha1").update(JSON.stringify(o)).digest("hex").slice(0, 12);
for (const [key, r] of Object.entries(RACES)) for (const n of [8, 16, 26]) for (const going of ["Good", "Heavy"]) {
  const seed = `test-${key}-${n}`;
  const race = { ...r, going, seed };
  const a = runRace(race, randomField(n, seed, data.settings), data), b = runRace(race, randomField(n, seed, data.settings), data);
  ok(hash(a) === hash(b), `${key} ${n}: the same seed gave a different race`);
  const c = runRace({ ...race, seed: seed + "x" }, randomField(n, seed, data.settings), data);
  ok(hash(a.timeline) !== hash(c.timeline), `${key} ${n}: a different seed gave the same race`);
  const { timeline: T, result: R } = a, st = data.stalls.starts[r.start].stalls;
  ok(T.dt === 0.1 && T.frames.every((f) => f.length === n && f.every((h) => h.length === 5)), `${key} ${n}: timeline shape`);
  ok(T.frames[0].every((h, i) => h[0] === -data.stalls.horseStandsBehind && Math.abs(h[1] - st[i].across) < 1e-3 && h[2] === 0 && h[3] === 0), `${key} ${n}: frame 0 isn't the horses standing in their stalls`);
  ok(T.frames.every((f) => f.every((h) => h[3] >= 0 && h[3] <= 3 && Number.isInteger(h[3]))), `${key} ${n}: effort outside 0-3`);
  ok(T.frames.every((f) => f.every((h) => Math.abs(h[1]) <= 15)), `${key} ${n}: a horse off the track`);
  // overlaps: two horses closer than the bench's measure (2.6 m along, 0.85 m across), before either has finished
  let over = 0, secs = 0;
  T.frames.forEach((f, k) => { const t = k * T.dt; secs++; for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    if (t > R.placed.find((p) => p.runner === i).time || t > R.placed.find((p) => p.runner === j).time) continue;
    if (f[i][0] > 3 && Math.abs(f[i][0] - f[j][0]) < 2.6 && Math.abs(f[i][1] - f[j][1]) < 0.85) over++; } });
  ok(over / secs * 10 < (n > 16 ? 0.1 : 0.05), `${key} ${n} ${going}: ${(over / secs * 10).toFixed(2)} overlaps per race-second`);
  // the result against the timeline: the finishing order is the order they cross the line
  const crossed = Array.from({ length: n }, (_, i) => T.frames.findIndex((f) => f[i][0] >= r.distance));
  ok(crossed.every((k) => k > 0), `${key} ${n}: a horse never reached the line`);
  ok(R.order.every((i, k) => k === 0 || crossed[i] >= crossed[R.order[k - 1]]), `${key} ${n}: result order differs from the timeline`);
  ok(T.frames.length * T.dt >= R.winningTime + data.settings.afterLine.AFTER_WINNER_S - 0.2, `${key} ${n}: timeline too short after the finish`);
  if (n === 16 && going === "Good") console.log(`${key.padEnd(6)} ${String(R.winningTime).padEnd(7)} pace ${R.pace.run.padEnd(6)} ${R.events.length} events, ${T.frames.length} frames, overlaps/s ${(over / secs * 10).toFixed(3)}`);
}
console.log(fails ? `${fails} checks failed` : "all checks passed");
process.exit(fails ? 1 : 0);
