// What a trainer could change, measured as for the jockey cards (owner, 11 Nov: trainers brainstorm).
// One horse, 2 below the best in a field of 14, same seeds/fields/draws; win % against rating points.
import { runRace } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
const N = +(process.argv[2] || 120);
const keys = ["s6f", "s1m", "r1m2f", "r1m4f", "r2m"];
function trial(mod, keysUse = keys) {
  let wins = 0, top3 = 0, runs = 0;
  for (const key of keysUse) for (let s = 1; s <= N; s++) {
    const seed = key + ":" + s, field = randomField(14, seed, data.settings), k = s % 14;
    const best = Math.max(...field.map(r => r.rating)), me = field[k];
    me.rating = best - 2 + (mod.add || 0); me.style = mod.style || ["front", "prominent", "midfield", "holdup"][s % 4]; me.flex = "adaptable"; me.temperament = "calm";
    const m = { ...mod }; delete m.add; delete m.style; Object.assign(me, m);
    const res = runRace({ ...RACES[key], going: "Good", seed }, field, data, { timeline: false }).result;
    const pos = res.placed.findIndex(p => p.runner === k) + 1;
    runs++; if (pos === 1) wins++; if (pos <= 3) top3++;
  }
  return `${(100 * wins / runs).toFixed(1).padStart(5)}% win  ${(100 * top3 / runs).toFixed(1).padStart(5)}% top 3`;
}
const out = (n, m, k) => console.log(n.padEnd(34), trial(m, k));
console.log("== rating scale =="); for (const a of [0, 1, 2, 3, 5]) out("+" + a, { add: a });
console.log("== temperament / flexibility =="); out("calm adaptable", {}); out("keen", { temperament: "keen" }); out("set", { flex: "set" }); out("versatile", { flex: "versatile" }); out("keen + set", { temperament: "keen", flex: "set" });
console.log("== riding orders by trip (a midfield horse, adaptable) ==");
for (const key of keys) { console.log(" " + key); for (const ins of ["jockey", "front", "prominent", "midfield", "holdup"]) out("  orders " + ins, { style: "midfield", instruction: ins }, [key]); }
