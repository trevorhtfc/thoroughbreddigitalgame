// How wide horses run round the first bend (owner, 21 Nov 2026: "The race engine seems too happy to let horses be 5/6
// wide in early turns in the races.. this feels unrealistic"). For each round-course race: at the middle of the first
// bend each horse's distance off the inside rail, in horse-widths (a lane = LANE m), and how many of the field are 4+
// and 5+ wide there.     node check/width.mjs [races per distance] [keys...]     SET='{"EASE":0.05}' to try settings
import { runRace, bendsFor } from "../engine.js";
import { randomField } from "../field.js";
import { data, RACES } from "./data.mjs";
if (process.env.SET) { const o = JSON.parse(process.env.SET); for (const [k, v] of Object.entries(o)) { const sec = ["bench", "rules", "benchDefaults", "balance"].find((s) => data.settings[s] && k in data.settings[s]) || "bench"; data.settings[sec][k] = v; } }
const argv = process.argv.slice(2), N = +(argv[0] || 60);
const KEYS = argv.slice(1).length ? argv.slice(1) : Object.keys(RACES).filter((k) => RACES[k].course !== "straight");
const LANE = 1.15, W = data.course.trackWidth, Z0 = data.settings.rules.RAIL_CLEAR;
for (const key of KEYS) {
  const R = RACES[key], start = data.stalls.starts[R.start];
  const kind = R.course === "straight" ? "straight" : R.course === "roundMile" ? "roundMile" : "round";
  const { bends } = bendsFor(data.course, kind, R.distance, !!start.onStraight);
  if (!bends.length) continue;
  const mid = (bends[0][0] + bends[0][1]) / 2, mid2 = bends[1] ? (bends[1][0] + bends[1][1]) / 2 : null;
  let horses = 0, w4 = 0, w5 = 0, maxSum = 0, w4b = 0, horsesB = 0;
  for (let s = 0; s < N; s++) {
    const n = 10 + (s % 9);
    const { timeline } = runRace({ ...R, going: "Good", seed: key + ":" + s }, randomField(n, key + ":" + s, data.settings), data);
    const at = (dmid) => { const lanes = [];
      for (let i = 0; i < n; i++) { const f = timeline.frames.find((fr) => R.distance - fr[i][0] <= dmid); if (!f) continue;
        const fromRail = f[i][1] + W / 2 - Z0; lanes.push(1 + Math.floor(Math.max(0, fromRail) / LANE)); }
      return lanes; };
    const l1 = at(mid); horses += l1.length; w4 += l1.filter((w) => w >= 4).length; w5 += l1.filter((w) => w >= 5).length; maxSum += Math.max(...l1);
    if (mid2 != null) { const l2 = at(mid2); horsesB += l2.length; w4b += l2.filter((w) => w >= 4).length; }
  }
  console.log(`${key.padEnd(6)} first bend (${Math.round(mid)} m to go): 4+ wide ${(100 * w4 / horses).toFixed(0)}%, 5+ wide ${(100 * w5 / horses).toFixed(0)}%, widest on average ${(maxSum / N).toFixed(1)} wide` + (horsesB ? ` · second bend 4+ wide ${(100 * w4b / horsesB).toFixed(0)}%` : ""));
}
