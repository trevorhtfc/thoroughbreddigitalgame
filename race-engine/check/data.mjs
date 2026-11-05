// Loads the course files and the engine's settings from the repo, for running races in Node.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
export const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const read = (p) => JSON.parse(readFileSync(join(REPO, p), "utf8"));
export const data = {
  course: read("courses/ascot.json"),
  stalls: read("courses/ascot-stalls.json"),
  standards: read("courses/ascot-standards.json"),
  settings: read("race-engine/settings.json"),
};
// The races by the standards file's keys, with the start each uses (courses/ascot-stalls.json).
export const RACES = {
  s5f: { course: "straight", start: "fiveFurlongs" }, s6f: { course: "straight", start: "sixFurlongs" },
  s7f: { course: "straight", start: "sevenFurlongs" }, s1m: { course: "straight", start: "straightMile" },
  r1m: { course: "roundMile", start: "roundMile" }, r1m2f: { course: "round", start: "mileTwo" },
  r1m4f: { course: "round", start: "mileFour" }, r1m6f: { course: "round", start: "mileSix" },
  r2m: { course: "round", start: "twoMiles" }, r2m4f: { course: "round", start: "twoMilesFour" },
  r2m6f: { course: "round", start: "twoMilesSix" },
};
for (const [k, r] of Object.entries(RACES)) r.distance = data.stalls.starts[r.start].distance;
