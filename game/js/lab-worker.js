// The Race Lab's helper: runs races off the page (so the page stays responsive) with the very same race engine the
// game uses (assets/engine/engine.js). The page sends the course data and the settings once ("init"), then batches of
// races ("jobs"); each race comes back as a short summary and one line of figures per runner, in stall order.
import { runRace, raceDayRating, flatSettings } from "../assets/engine/engine.js";

const STYLE_IX = { front: 0, prominent: 1, midfield: 2, holdup: 3 };
let DATA = null, P = null;

onmessage = (e) => {
  const m = e.data || {};
  if (m.type === "init") {
    DATA = m.data; P = flatSettings(DATA.settings);
    postMessage({ type: "inited" });
    return;
  }
  if (m.type === "jobs") {
    const out = m.jobs.map(runOne);
    postMessage({ type: "done", batch: m.batch, out });
  }
};

function runOne(job) {
  try {
    const { result: R } = runRace(job.race, job.runners, DATA, { timeline: false });
    const n = job.runners.length;
    const rows = new Array(n);
    const missed = new Set(R.events.filter((e) => e.kind === "missed the break").map((e) => e.runner));
    for (const p of R.placed) {
      const d = raceDayRating(P, job.runners[p.runner], { ...job.race, going: R.race.going });
      // [place, lengths behind the winner, race-day rating, ground +/-, trip steps off, form on the day,
      //  lengths lost to traffic, style as ridden (0-3), missed the break (0/1), group on the straight]
      rows[p.runner] = [p.place, p.behind, d.rating, d.ground, d.tripSteps, p.form, p.lostLengths, STYLE_IX[p.ridden], missed.has(p.runner) ? 1 : 0, p.group];
    }
    return {
      k: job.k, ok: true,
      paceExp: R.pace.expected, paceRun: R.pace.run, groups: R.pace.groups.length,
      time: R.winningTime, par: R.parTime,
      margin: R.placed[1] ? R.placed[1].margin : 0,
      rows,
    };
  } catch (err) {
    return { k: job.k, ok: false, error: String(err && err.message || err) };
  }
}
