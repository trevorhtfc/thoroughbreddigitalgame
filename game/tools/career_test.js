// Robot careers through the career hub (js/career/core.js) with the rules behind it (js/career/rules/): no errors, the
if (process.env.LUCK) globalThis.ENGINE_LUCK = +process.env.LUCK;
// money holds up, and the trainer's chance chips are honest.   node game/tools/career_test.js [careers] [seasons]
const path = require("path"), dir = path.join(__dirname, "../js/career");
globalThis.window = globalThis;
for (const f of ["data.js", "rules/rules.js", "rules/hub-adapter.js", "core.js"]) require(path.join(dir, f));
const C = globalThis.CAREER, R = globalThis.TBRULES, N = +process.argv[2] || 12, SEASONS = +process.argv[3] || 6;
// the race engine and its courses, as career.html loads them (NOENGINE=1: the rules' own roll instead)
const fs = require("fs"), A = path.join(__dirname, "../../race-view/assets");
async function loadEngine() {
  const { runRace, expectedPace } = await import(path.join(A, "engine/engine.js")), get = (f) => JSON.parse(fs.readFileSync(path.join(A, f), "utf8"));
  const settings = get("engine/settings.json"), courses = {};
  for (const c of ["ascot", "newmarket", "newmarket-july", "york"]) courses[c] = { data: { course: get(`course/${c}.json`), stalls: get(`course/${c}-stalls.json`), standards: get(`course/${c}-standards.json`), settings }, view: get(`course/${c}-view.json`) };
  globalThis.ENGINE = { runRace, expectedPace, courses };
}
(async () => { if (!process.env.NOENGINE) await loadEngine(); const t0 = Date.now(); main(); console.log(`(${process.env.NOENGINE ? "the rules' own roll" : "the race engine"}, ${((Date.now() - t0) / 1000).toFixed(0)} s)`); })();
function main() {
const chip = C.CHIPS.map(() => [0, 0]), tiers = [], banks = [], wr = [0, 0]; let broke = 0, lowest = 1e9, claimed = 0, hurt = 0;
for (let k = 0; k < N; k++) {
  const S = C.newGame(1000 + k * 77), tierAt = [];
  for (let s = 0; s < SEASONS * C.NW; s++) {
    C.use(S);
    // the robot: uses its gallops, bids when there's room and money to spare, covers its mares, takes the trainer's picks
    for (const h of S.horses) { if (h.fresh < 55) C.gallop(S, h.id, "easy"); else if (h.k.pw > 8) C.gallop(S, h.id, "work"); else if (h.craft < 3) C.gallop(S, h.id, "school"); }
    const spare = () => S.cash - 15000;
    if (S.sale) for (const l of S.sale.lots) {
      const racing = l.kind === "breeze" || l.kind === "hit";
      const lim = racing && C.boxesFree(S) > 0 ? Math.min(l.guide * (l.kind === "breeze" ? [0.6, 0.95, 1.3, 1.7][l.wh] : 1), spare() * 0.5)
        : l.kind === "yearling" && S.young.length < 3 && S.cash > 90000 ? Math.min(l.guide * [0.6, 0.95, 1.3, 1.7][l.wh], S.cash * 0.15)
        : l.kind === "mare" && C.paddocksFree(S) > 0 && S.cash > 150000 ? Math.min(l.guide, S.cash * 0.15) : 0;
      let r = null; while (R.nextBid(l) <= lim && (r = C.bid(S, l.id)) === "raised"); if (r !== "won") C.pass(S, l.id); }
    if (C.coveringOpen(S)) for (const m of S.mares) if (!m.inFoal) { const st = R.sires().filter((x) => x.fee < Math.max(0, spare()) * 0.25).sort((a, b) => b.stars - a.stars || a.fee - b.fee)[0]; if (st) C.cover(S, m.id, st.n); }
    for (const h of S.young.filter((x) => x.stage === "ready")) if (!C.moveToYard(S, h.id)) { const worst = S.horses.slice().sort((a, b) => (a.or || 60) - (b.or || 60))[0]; if (worst && worst.age >= 4) { C.sell(S, worst.id); C.moveToYard(S, h.id); } }
    for (const h of S.horses.slice()) if (h.age >= 7 || (h.age >= 4 && h.runs > 8 && (h.or || 0) < 55 && S.horses.length > 2)) { if (!(h.sex === "f" && h.peak >= 85 && C.retire(S, h.id))) C.sell(S, h.id); }
    const picks = C.trainerPicks(S), keys = {}; for (const p of picks) keys[p.h.id] = p.v.key;
    const rep = C.advance(S);
    for (const r of rep.results) { const key = keys[r.hid]; if (key != null) { chip[key][0]++; if (r.pos === 1) chip[key][1]++; } wr[0]++; if (r.pos === 1) wr[1]++; if (r.claimed) claimed++; }
    hurt += S.horses.filter((h) => h.inj > 0).length;
    JSON.parse(JSON.stringify(S));                                // the save must survive
    lowest = Math.min(lowest, S.cash); if (S.cash < -20000) { broke++; break; }
    if (S.week === 1) tierAt.push(C.tierOf(S));
  }
  tiers.push(tierAt); banks.push(S.cash);
  if (k < 3) console.log(`career ${k}: tiers by season ${tierAt.join(" ")} | bank ${C.money(S.cash)} | rep ${S.rep} | ${S.stats.wins}/${S.stats.runs} wins | horses ${S.horses.length} mares ${S.mares.length} young ${S.young.length} studs ${S.studs.length} | best ${S.top && S.top.n + " " + S.top.or} | trophies ${S.trophies.length} | save ${Math.round(JSON.stringify(S).length / 1024)} KB`);
}
console.log("bankrupt:", broke, "of", N, "| lowest bank", C.money(lowest), "| median final bank", C.money(banks.sort((a, b) => a - b)[N >> 1]), "| claimed", claimed, "| horse-weeks injured", hurt);
console.log("win rate", (wr[1] / wr[0] * 100).toFixed(1) + "% of", wr[0], "runs,", (wr[0] / N / SEASONS).toFixed(0), "runs a season");
C.CHIPS.forEach((c, i) => console.log(c.padEnd(14), chip[i][0] ? (chip[i][1] / chip[i][0] * 100).toFixed(0) + "% won" : "-", "of", chip[i][0]));
console.log("avg tier after each season:", Array.from({ length: SEASONS }, (_, i) => (tiers.reduce((a, t) => a + (t[i] || 0), 0) / (tiers.filter((t) => t[i]).length || 1)).toFixed(1)).join(" "));
}
