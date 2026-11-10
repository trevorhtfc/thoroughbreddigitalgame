// How much each jockey card is worth (owner, 10 Nov: the team draft), measured as wins for one horse in otherwise
// identical races (same seed, field and draw), against rating points. node check/team-jockeys.mjs [races per distance]
import { runRace } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
const N = +(process.argv[2] || 120);
const keys = ["s6f", "s1m", "r1m2f", "r1m4f", "r2m"];
function trial(mod, styles) {
  let wins = 0, top3 = 0, runs = 0;
  for (const key of keys) for (let s = 1; s <= N; s++) {
    const seed = key + ":" + s, field = randomField(14, seed, data.settings), k = s % 14;
    const best = Math.max(...field.map(r => r.rating)), me = field[k];
    me.rating = best - 2 + (mod.add || 0); me.style = styles[s % styles.length]; me.flex = "adaptable"; me.temperament = "calm";
    const m = { ...mod }; delete m.add; Object.assign(me, m);
    const res = runRace({ ...RACES[key], going: "Good", seed }, field, data, { timeline: false }).result;
    const pos = res.placed.findIndex(p => p.runner === k) + 1;
    runs++; if (pos === 1) wins++; if (pos <= 3) top3++;
  }
  return `${(100 * wins / runs).toFixed(1).padStart(5)}% win  ${(100 * top3 / runs).toFixed(1).padStart(5)}% top 3`;
}
const ALL = ["front", "prominent", "midfield", "holdup"], FRONT = ["front", "prominent"], BACK = ["midfield", "holdup"];
const sets = [
  [ALL, [["none", {}], ["+1", { add: 1 }], ["+2", { add: 2 }], ["+3", { add: 3 }], ["+5", { add: 5 }], ["jockey 1", { jockey: 1 }], ["jockey 5", { jockey: 5 }],
    ["noFlop", { noFlop: true }], ["formBest 2 noFlop", { formBest: 2, noFlop: true }], ["formBest 3 noFlop", { formBest: 3, noFlop: true }],
    ["reader .5 j3", { reader: .5, jockey: 3 }], ["reader .75 j4", { reader: .75, jockey: 4 }], ["reader 1 j5", { reader: 1, jockey: 5 }]]],
  [FRONT, [["none", {}], ["+2", { add: 2 }], ["+4", { add: 4 }], ["tank .04", { paceTank: .04 }], ["tank .07", { paceTank: .07 }], ["tank .10", { paceTank: .10 }]]],
  [BACK, [["none", {}], ["+2", { add: 2 }], ["+4", { add: 4 }], ["kick .006", { lateKick: .006 }], ["kick .011", { lateKick: .011 }], ["kick .016", { lateKick: .016 }]]],
];
for (const [styles, tests] of sets) {
  console.log(`== ${styles.join("/")} ==`);
  for (const [name, mod] of tests) console.log(name.padEnd(20), trial(mod, styles));
}
