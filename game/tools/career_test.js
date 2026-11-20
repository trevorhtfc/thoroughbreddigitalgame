// Robot careers through the career hub's rules (js/career/core.js): no errors, the money holds up, and the trainer's
// chance chips are honest.   node game/tools/career_test.js [careers] [seasons]
const fs = require("fs"), path = require("path"), dir = path.join(__dirname, "../js/career");
globalThis.window = globalThis;
eval(fs.readFileSync(path.join(dir, "data.js"), "utf8")); eval(fs.readFileSync(path.join(dir, "core.js"), "utf8"));
const C = globalThis.CAREER, N = +process.argv[2] || 20, SEASONS = +process.argv[3] || 8;
const chip = C.CHIPS.map(() => [0, 0]), tiers = [], banks = [], wr = [0, 0]; let broke = 0, lowest = 1e9;
for (let k = 0; k < N; k++) {
  const S = C.newGame(1000 + k * 77);
  const tierAt = [];
  for (let s = 0; s < SEASONS * C.NW; s++) {
    // the robot: uses its gallops, buys when there's a box and money to spare, covers its mares, takes the trainer's picks
    for (const h of S.horses) if (h.est.w > 4) C.gallop(S, h.id, "work");
    const spare = () => S.bank - 15000;
    if (S.sale) for (const l of S.sale.lots) { if (l.sold) continue; const racing = l.kind === "breeze" || l.kind === "hit";
      if (racing && C.boxesFree(S) > 0 && l.price < spare() * 0.5) C.buy(S, l.id);
      else if (l.kind === "yearling" && S.young.length < 3 && S.bank > 90000 && l.price < S.bank * 0.15) C.buy(S, l.id);
      else if (l.kind === "mare" && C.paddocksFree(S) > 0 && S.bank > 150000 && l.price < S.bank * 0.15) C.buy(S, l.id); }
    if (C.coveringOpen(S)) for (const m of S.mares) if (!m.inFoal) { const st = C.stallionsFor(S).filter((x) => x.fee < Math.max(0, spare()) * 0.25)[0]; if (st) C.cover(S, m.id, st.name); }
    for (const h of S.young.filter((x) => x.stage === "ready")) if (!C.moveToYard(S, h.id)) { const worst = S.horses.slice().sort((a, b) => (a.or || 60) - (b.or || 60))[0]; if (worst && worst.age >= 4) { C.sell(S, worst.id); C.moveToYard(S, h.id); } }
    for (const h of S.horses.slice()) if (h.age >= 7 || (h.age >= 4 && h.runs > 8 && (h.or || 0) < 55 && S.horses.length > 2)) C.sell(S, h.id);
    const picks = C.trainerPicks(S); const keys = {}; for (const p of picks) keys[p.h.id] = p.v.key;
    const rep = C.advance(S);
    for (const r of rep.results) { const key = keys[r.hid]; if (key != null) { chip[key][0]++; if (r.pos === 1) chip[key][1]++; } wr[0]++; if (r.pos === 1) wr[1]++; }
    lowest = Math.min(lowest, S.bank); if (S.bank < -20000) { broke++; break; }
    if (S.week === 1) tierAt.push(C.tierOf(S));
  }
  tiers.push(tierAt); banks.push(S.bank);
  if (k < 3) console.log(`career ${k}: tiers by season ${tierAt.join(" ")} | bank ${C.money(S.bank)} | rep ${S.rep} | ${S.stats.wins}/${S.stats.runs} wins | horses ${S.horses.length} mares ${S.mares.length} young ${S.young.length} | best ${S.stats.best && S.stats.best.name + " " + S.stats.best.fig} | trophies ${S.trophies.length}`);
}
console.log("bankrupt:", broke, "of", N, "| lowest bank", C.money(lowest), "| median final bank", C.money(banks.sort((a, b) => a - b)[N >> 1]));
console.log("win rate", (wr[1] / wr[0] * 100).toFixed(1) + "% of", wr[0], "runs,", (wr[0] / N / SEASONS).toFixed(0), "runs a season");
C.CHIPS.forEach((c, i) => console.log(c.padEnd(14), chip[i][0] ? (chip[i][1] / chip[i][0] * 100).toFixed(0) + "% won" : "-", "of", chip[i][0]));
console.log("avg tier after each season:", Array.from({ length: SEASONS }, (_, i) => (tiers.reduce((a, t) => a + (t[i] || 0), 0) / tiers.filter((t) => t[i]).length).toFixed(1)).join(" "));
