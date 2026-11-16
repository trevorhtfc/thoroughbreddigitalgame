// York's par times (16 Nov 2026): the engine's par for each start, set so the median winning time of 12-runner races on
// good ground comes out at the target winning time (to_race_view.py TARGET). Writes tools/course/york/york-par.json;
// then run to_race_view.py again to put the pars in race-view/assets/course/york-standards.json.
//   node tools/course/york/calibrate.mjs [races per start, default 300] [rounds, default 3]
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { runRace } from "../../../race-engine/engine.js";
import { randomField } from "../../../race-engine/field.js";

const here = dirname(fileURLToPath(import.meta.url)), repo = join(here, "..", "..", "..");
const rd = (p) => JSON.parse(readFileSync(join(repo, p), "utf8"));
const COURSE = rd("race-view/assets/course/york.json"), STALLS = rd("race-view/assets/course/york-stalls.json");
const STANDARDS = rd("race-view/assets/course/york-standards.json"), SETTINGS = rd("race-engine/settings.json");
const N = Number(process.argv[2] || 300), ROUNDS = Number(process.argv[3] || 3);
const parFile = join(here, "york-par.json");
const out = existsSync(parFile) ? JSON.parse(readFileSync(parFile, "utf8")) : { _about: "Written by calibrate.mjs: the par (seconds) the race engine uses at York, so its winning times match the targets.", par: {}, measured: {} };

// a race on its start's route, as the race view does it (courses/york.json -> routes)
function courseFor(start) {
  const R = COURSE.routes[start.route];
  return { ...COURSE, path: R.path, pathRail: R.pathRail };
}
for (const [name, st] of Object.entries(STALLS.starts)) {
  const p = STANDARDS.parTimes.find((q) => q.key === st.key);
  let par = out.par[st.key] ?? p.seconds;
  let med = 0;
  for (let k = 0; k < ROUNDS; k++) {
    const standards = { ...STANDARDS, parTimes: STANDARDS.parTimes.map((q) => (q.key === st.key ? { ...q, seconds: par } : q)) };
    const times = [];
    for (let s = 0; s < N; s++) {
      const runners = randomField(12, `york:${name}:${s}`, SETTINGS);
      const { result } = runRace({ course: st.course, distance: st.distance, start: name, going: "Good", seed: `york:${name}:${s}` }, runners,
        { course: courseFor(st), stalls: STALLS, standards, settings: SETTINGS }, { timeline: false });
      times.push(result.winningTime ?? result.finish?.[0]?.time ?? result.placings?.[0]?.time);
    }
    times.sort((a, b) => a - b); med = times[Math.floor(times.length / 2)];
    par = Math.round(par * p.winningTime / med * 100) / 100;
  }
  out.par[st.key] = par; out.measured[st.key] = { "winning time (before the last step)": Math.round(med * 100) / 100, target: p.winningTime };
  console.log(`${name.padEnd(5)} ${st.route.padEnd(9)} median ${med.toFixed(2)} s (target ${p.winningTime}) -> par ${par}`);
}
writeFileSync(parFile, JSON.stringify(out, null, 1));
