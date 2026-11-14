// The team's jockey-card fields leave every race without them exactly as it was: node check/team-same.mjs <old engine>
import { runRace as runNew } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
const { runRace: runOld } = await import(process.argv[2]);
let same = 0, n = 0;
for (const key of Object.keys(RACES)) for (let s = 1; s <= 40; s++) {
  const race = { ...RACES[key], going: "Good", seed: key + s }, field = randomField(14, key + s, data.settings);
  const a = runOld(race, field, data, { timeline: false }).result, b = runNew(race, field, data, { timeline: false }).result;
  n++; if (JSON.stringify(a) === JSON.stringify(b)) same++;
}
console.log(`${same} of ${n} races identical`);
