// Random race cards like the test bench's (tools/race-bench/racebench.py), for checking the engine against the bench
// and for the race view until the game hands it real ones. Every number is in settings.json -> testField.
//
//   import { randomField } from "./field.js";
//   const runners = randomField(12, "seed", settings);
//
// Each horse: a rating, a running style, flexibility and temperament, and a "speedier" or "stayer" type for the race
// (given as shade +1 or -1, as the bench draws it, so it works at every distance, 2m+ included). No going preference,
// so the ground neither helps nor hurts; jockeys of random skill (the engine draws it).
import { makeRandom } from "./engine.js";

export function randomField(n, seed, settings, opts = {}) {
  const F = settings.testField, B = settings.bench, H = settings.horse;
  const rnd = makeRandom("field:" + seed);
  return Array.from({ length: n }, (_, i) => {
    const r = {
      name: `No. ${i + 1}`,
      rating: rnd.int(F.R_LO, F.R_HI),
      style: H.STYLES[rnd.choice(F.MIX)],
      flex: H.FLEX[rnd.choice(B.FLEX_MIX)],
      temperament: rnd.chance(F.KEEN_P) ? "keen" : "calm",
      shade: rnd.chance(0.5) ? 1 : -1,
    };
    if (opts.handicap) r.mark = r.rating + rnd.normal(0, F.H_SD);
    return r;
  });
}
