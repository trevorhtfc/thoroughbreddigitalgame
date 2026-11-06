// One race, printed: node check/one.mjs s1m 12 seed [going]
import { runRace } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
const [key = "s1m", n = "12", seed = "1", going = "Good"] = process.argv.slice(2);
const race = { ...RACES[key], going, seed };
const runners = randomField(+n, seed, data.settings);
const t0 = performance.now();
const { timeline, result } = runRace(race, runners, data);
console.log(`${key} ${n} runners, seed ${seed}: ${(performance.now() - t0).toFixed(0)} ms, ${timeline.frames.length} frames`);
console.log(`winning time ${result.winningTime}s (par ${result.parTime}), pace expected ${result.pace.expected}, run ${result.pace.run}`, JSON.stringify(result.pace.groups));
for (const p of result.placed) console.log(`${String(p.place).padStart(2)}. draw ${String(p.draw).padStart(2)} ${p.style.padEnd(9)} (ridden ${p.ridden.padEnd(9)}) rating ${p.dayRating} form ${p.form.toFixed(1).padStart(5)}  ${p.time.toFixed(2)}s  margin ${p.margin.toFixed(2)}  lost ${p.lostLengths}`);
for (const e of result.events) console.log(`  ${e.t.toFixed(1).padStart(6)}s  ${e.text}`);
const effort = [0, 0, 0, 0]; for (const f of timeline.frames) for (const h of f) effort[h[3]]++;
console.log("effort share 0-3:", effort.map((c) => (c / effort.reduce((a, b) => a + b)).toFixed(3)).join(" "));
