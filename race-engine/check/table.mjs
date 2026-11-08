// The engine's figures beside the bench's: reads check/results/bench.json and engine.json, writes compare.md.
//   node check/table.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { REPO } from "./data.mjs";
const dir = join(REPO, "race-engine/check/results");
// TAG=newmarket: bench-newmarket.json and engine-newmarket.json, written to compare-newmarket.md
const TAG = process.env.TAG ? "-" + process.env.TAG : "";
const B = JSON.parse(readFileSync(join(dir, `bench${TAG}.json`), "utf8")), E = JSON.parse(readFileSync(join(dir, `engine${TAG}.json`), "utf8"));
const NAMES = { s5f: "5f", s6f: "6f", s7f: "7f", s1m: "Straight mile", r1m: "Round mile", r1m2f: "1m2f", r1m4f: "1m4f", r1m6f: "1m6f", r2m: "2m", r2m4f: "2m4f", r2m6f: "2m6f",
  nm5f: "Newmarket 5f", nm6f: "Newmarket 6f", nm7f: "Newmarket 7f", nm1m: "Newmarket mile", nm1m1f: "Newmarket 1m1f", nm1m2f: "Newmarket 1m2f", nm1m4f: "Newmarket 1m4f", nm1m6f: "Newmarket 1m6f", nm2m: "Newmarket 2m", nm2m2f: "Newmarket 2m2f", nm2m4f: "Newmarket 2m4f" };
const keys = Object.keys(NAMES).filter((k) => B[k] && E[k]);
const f2 = (v) => v.toFixed(2), pc = (v) => (v * 100).toFixed(0) + "%";
const pair = (b, e, f) => `${f(b)} / ${f(e)}`;
// how far apart two shares can be by chance alone (2.5 standard errors of the difference)
const noise = (p, N) => 2.5 * Math.sqrt(2 * p * (1 - p) / N);
const flags = [];
const check = (what, key, b, e, lim) => { if (Math.abs(b - e) > lim) flags.push(`${NAMES[key]} ${what}: bench ${b.toFixed(3)}, engine ${e.toFixed(3)} (chance alone: up to ${lim.toFixed(3)})`); };
const lines = [];
lines.push(`# Race engine against the test bench`, ``, `${B[keys[0]].races.toLocaleString()} bench races and ${E[keys[0]].races.toLocaleString()} engine races at each distance, ${E[keys[0]].runners} runners, Good ground, random fields like the bench's. Each cell: bench / engine.`, ``);
lines.push(`| Distance | Winning time (s) | Best horse wins | Winning margin (L) | Traffic: lose 1 L+ | Wins by style F · P · M · H | Wins by draw low · mid · high |`, `|---|---|---|---|---|---|---|`);
for (const k of keys) {
  const b = B[k], e = E[k], N = Math.min(b.races, e.races);
  lines.push(`| ${NAMES[k]} | ${pair(b.time, e.time, (v) => v.toFixed(1))} | ${pair(b.best, e.best, pc)} | ${pair(b.margin, e.margin, f2)} | ${pair(b.lose1, e.lose1, pc)} | ${"FPMH".split("").map((s) => f2(b.style[s])).join(" · ")} / ${"FPMH".split("").map((s) => f2(e.style[s])).join(" · ")} | ${["low", "mid", "high"].map((s) => f2(b.draw[s])).join(" · ")} / ${["low", "mid", "high"].map((s) => f2(e.draw[s])).join(" · ")} |`);
  check("winning time", k, b.time, e.time, 0.3);
  check("best horse wins", k, b.best, e.best, noise(b.best, N));
  check("winning margin", k, b.margin, e.margin, 0.15);   // the median margin moves by up to 0.1 L between two runs of 4,000 races, bench or engine
  check("traffic", k, b.lose1, e.lose1, noise(b.lose1, N * b.runners / 4));
  for (const s of "FPMH") check(`wins by ${s}`, k, b.style[s], e.style[s], noise(0.25 * b.style[s], N) / 0.25);
  for (const s of ["low", "mid", "high"]) check(`wins by ${s} draw`, k, b.draw[s], e.draw[s], noise(b.draw[s] / 3, N) * 3);
}
// pace: how often each pace comes up, and wins by style at each pace, straight and round courses pooled
lines.push(``, `**The pace** (straight course and round course pooled; wins against a fair share of 1.00):`, ``, `| | Races at this pace | Front-runners win | Prominent win | Midfield win | Hold-up win |`, `|---|---|---|---|---|---|`);
const straightKey = (k) => k[0] === "s" || ["nm5f", "nm6f", "nm7f", "nm1m", "nm1m1f", "nm1m2f"].includes(k);   // Newmarket's straight is 1m2f
for (const [label, ks] of [["Straight", keys.filter(straightKey)], ["Round", keys.filter((k) => !straightKey(k))]]) for (const p of ["slow", "even", "strong", "fast"]) {
  const pool = (X, s) => { let w = 0, v = 0; for (const k of ks) if (X[k].byPace[p]) { const m = X[k].paceMix[p]; w += m; v += m * X[k].byPace[p][s]; } return w ? v / w : NaN; };
  const mix = (X) => ks.reduce((a, k) => a + X[k].paceMix[p], 0) / ks.length;
  lines.push(`| ${label}, ${p} | ${pair(mix(B), mix(E), pc)} | ${"FPMH".split("").map((s) => pair(pool(B, s), pool(E, s), f2)).join(" | ")} |`);
}
lines.push(``, flags.length ? `**Differences larger than chance would explain** (${flags.length}):` : `**Every difference is within what chance alone would give** at these numbers of races (2.5 standard errors; times within 0.3 s; median margins within 0.15 L, since the bench's own median margin moved by up to 0.07 L between two runs of 4,000 races).`);
for (const f of flags) lines.push(`- ${f}`);
writeFileSync(join(dir, `compare${TAG}.md`), lines.join("\n") + "\n");
console.log(lines.join("\n"));
