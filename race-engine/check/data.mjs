// Loads the course files and the engine's settings from the repo, for running races in Node.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
export const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const read = (p) => JSON.parse(readFileSync(join(REPO, p), "utf8"));
// COURSE=newmarket (8 Nov, draft): the Rowley Mile instead, with its own races (by its standards keys, nm5f ... nm2m4f)
export const COURSE = process.env.COURSE || "ascot";
// COURSE=july: Newmarket's July Course (draft), its races jc5f ... jc2m
const FILES = COURSE === "newmarket"
  ? ["courses/newmarket-draft.json", "courses/newmarket-stalls.json", "courses/newmarket-standards.json"]
  : COURSE === "july"
  ? ["courses/newmarket-july-draft.json", "courses/newmarket-july-stalls.json", "courses/newmarket-july-standards.json"]
  : ["courses/ascot.json", "courses/ascot-stalls.json", "courses/ascot-standards.json"];
export const data = {
  course: read(FILES[0]),
  stalls: read(FILES[1]),
  standards: read(FILES[2]),
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
if (COURSE === "newmarket" || COURSE === "july") {
  for (const k of Object.keys(RACES)) delete RACES[k];
  for (const [name, st] of Object.entries(data.stalls.starts)) RACES[st.key] = { course: st.course, start: name };
}
for (const [k, r] of Object.entries(RACES)) r.distance = data.stalls.starts[r.start].distance;
