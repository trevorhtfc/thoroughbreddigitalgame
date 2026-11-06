// Average cost of a horse by its peak rating, bred against bought (load into the game page, then COST.run(60)).
// Bred = the mare's price at the mares sale + the stud fee; bought = one bid more than the keenest rival at Tattersalls.
// (From ascot-game/tools/t54.py; the mares' prices now come from PILES, so a price change shows up here.)
window.COST = { run(cards = 60) {
  const band = r => r < 90 ? "<90" : r < 100 ? "90-99" : r < 110 ? "100-109" : r < 120 ? "110-119" : "120+";
  const pileP = st => PILES.find(p => p.stars.includes(st)).price, B = {};
  const add = (src, r, c) => { const k = band(r); B[k] = B[k] || { bred: [], bought: [] }; B[k][src].push(c); };
  for (let c = 0; c < cards; c++) { newCard(5000 + c);
    const sts = STALLIONS.map(s => stallion(s.name));
    for (const m of MARES) for (const s of sts) { if (pairProblem(s, m)) continue; const f = breedPure(s, m); add("bred", Math.max(...f.r), s.fee + pileP(m.stars)); }
    S.step = 2; S.lotN = 0; newCatalogue();
    for (const l of S.sale) { const ap = appeal(l), top = Math.max(0, ...RIVALS.map(r => Math.random() < r.keen(l) ? l.reserve * ap * r.want(l) * (.7 + Math.random() * .9) : 0));
      let price = l.reserve; if (top >= l.reserve) { while (price <= top) price += incFor(price); }
      const f = breedPure(stallion(l.sire), byName(l.dam)); add("bought", Math.max(...f.r), price); } }
  const out = {}, av = a => a.length ? Math.round(a.reduce((x, y) => x + y, 0) / a.length / 1000) : null;
  for (const k of ["<90", "90-99", "100-109", "110-119", "120+"]) { const b = B[k]; if (b) out[k] = { bred: av(b.bred), bought: av(b.bought), nBred: b.bred.length, nBought: b.bought.length }; }
  return out;
} };
