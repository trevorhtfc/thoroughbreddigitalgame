// Stable-building test harness. Runs inside the game page and uses the game's own functions:
// newCard, PILES/pileLeft, STALLIONS/stallion/pairProblem, breed (the real breeding engine),
// newCatalogue + RIVALS/appeal (the real sale and rival buyers), check and simRace (the race engine).
(function () {
  // Rough win chance from the race-day rating against the best of the field (used only to choose entries; from
  // measured engine races: level with the top band about 14%, 10 above about 50%)
  const winChance = (h, r, c) => { const top = Math.max(...CARD.races[r.i].opp.map(o => o.rating)); return 0.85 / (1 + Math.exp(-(c.day - top - 3) / 4)); };

  // Best one-horse-per-race assignment (Hungarian algorithm, maximising total win chance)
  function assign(w) {
    const nH = w.length, nR = w[0] ? w[0].length : 0, n = Math.max(nH, nR); if (!n) return [];
    const max = 1, a = Array.from({ length: n + 1 }, (_, i) => Array.from({ length: n + 1 }, (_, j) =>
      i && j ? (i <= nH && j <= nR ? max - w[i - 1][j - 1] : max) : 0));
    const u = Array(n + 1).fill(0), v = Array(n + 1).fill(0), p = Array(n + 1).fill(0), way = Array(n + 1).fill(0);
    for (let i = 1; i <= n; i++) {
      p[0] = i; let j0 = 0; const minv = Array(n + 1).fill(Infinity), used = Array(n + 1).fill(false);
      do {
        used[j0] = true; const i0 = p[j0]; let delta = Infinity, j1 = 0;
        for (let j = 1; j <= n; j++) if (!used[j]) {
          const cur = a[i0][j] - u[i0] - v[j];
          if (cur < minv[j]) { minv[j] = cur; way[j] = j0; }
          if (minv[j] < delta) { delta = minv[j]; j1 = j; }
        }
        for (let j = 0; j <= n; j++) if (used[j]) { u[p[j]] += delta; v[j] -= delta; } else minv[j] -= delta;
        j0 = j1;
      } while (p[j0] !== 0);
      do { const j1 = way[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
    }
    const res = []; for (let j = 1; j <= n; j++) if (p[j] <= nH && j <= nR) res.push([p[j] - 1, j - 1]);
    return res;
  }

  function bestAt(h, r) {
    let best = { w: 0 };
    for (const age of [2, 3, 4]) {
      const c = check({ ...h, age }, r);
      if (c.ok) { const w = winChance(h, r, c) + c.eff / 1e5; if (w > best.w) best = { w, age, eff: c.eff }; }
    }
    return best;
  }

  async function play(P, seed, budget) {
    localStorage.clear(); newCard(seed); if (budget) S.budget = budget;
    const targets = RACES.slice().sort((a, b) => (P.stayFirst ? (b.f >= 14) - (a.f >= 14) : 0) || b.bands[3] - a.bands[3]), taken = new Set();
    const centre = (a, b) => { const x = DISTANCES.indexOf(a.optimumDistance), y = DISTANCES.indexOf(b.optimumDistance); return Math.min(x, y) * .6 + Math.max(x, y) * .4; };
    const aim = c => { const t = targets.find(r => !taken.has(r.id)); if (!t) return null; return t; };
    const sts = STALLIONS.map(s => stallion(s.name));
    const log = { spentMares: 0, spentFees: 0, spentSale: 0, bred: 0, bought: 0, lotsTried: 0 };
    // 1) Mares sale
    for (const [pid, n] of Object.entries(P.mares || {})) for (let k = 0; k < n; k++) {
      const p = PILES.find(x => x.id === pid), left = pileLeft(p);
      if (studCount() >= MARE_CAP || !left.length || p.price > S.budget) break;
      const m = left[Math.floor(Math.random() * left.length)];
      S.budget -= p.price; log.spentMares += p.price; S.hand.push(m.name);
    }
    // 2) Breed every mare (best mares first)
    const mares = S.hand.map(byName).sort((a, b) => b.stars - a.stars);
    for (const m of mares) {
      if (S.stable.length >= STABLE_CAP) break;
      const room = S.budget - (P.keepForSale || 0);
      const ok = sts.filter(s => !pairProblem(s, m) && s.fee <= Math.min(P.feeCap, room));
      if (!ok.length) continue;
      let s = P.stallion(ok, m);
      if (P.plan) { const t = aim(); if (t) { const top = Math.max(...ok.map(x => x.shownStars)); const near = ok.filter(x => x.shownStars >= top - 1); s = near.sort((a, b) => Math.abs(centre(a, m) - t.step) - Math.abs(centre(b, m) - t.step) || b.shownStars - a.shownStars || a.fee - b.fee)[0]; taken.add(t.id); } }
      breed(s.name, m.name, "bred", s.fee); S.budget -= s.fee; log.spentFees += s.fee; log.bred++;
      S.stable.push(S.foal.h); S.usedMares.push(m.name); S.hand = S.hand.filter(x => x !== m.name); S.foal = null;
    }
    // 3) Tattersalls: ascending auction against the real rival buyers
    S.step = 2; newCatalogue();
    let lots = P.lots(S.sale.slice());
    if (P.plan) { const left = targets.filter(r => !taken.has(r.id)); lots = lots.map(l => { const c = centre(stallion(l.sire), byName(l.dam)); const best = Math.min(9, ...left.map(r => Math.abs(c - r.step))); return { l, sc: l.reserve - best * 40000 }; }).sort((a, b) => b.sc - a.sc).map(x => x.l); }
    for (const l of lots) {
      if (S.stable.length >= STABLE_CAP || log.bought >= P.maxLots) break;
      const limit = Math.min(Math.round(l.reserve * P.bidUpTo / 5000) * 5000, S.budget);
      if (limit < l.reserve) continue;
      log.lotsTried++;
      const ap = appeal(l), top = Math.max(0, ...RIVALS.map(r => Math.random() < r.keen(l) ? l.reserve * ap * r.want(l) * (.7 + Math.random() * .9) : 0));
      let price = l.reserve; if (top >= l.reserve) { while (price <= top) price += incFor(price); }
      if (price <= limit) {
        S.budget -= price; log.spentSale += price; log.bought++;
        breed(l.sire, l.dam, "bought", price, l.id); S.stable.push(S.foal.h); S.foal = null;
      }
    }
    // 4) Develop and enter: each horse's best age for its race, one horse per race, best total chance
    const H = S.stable, w = H.map(h => RACES.map(r => bestAt(h, r).w));
    S.entries = {};
    const ages = {};
    for (const [hi, ri] of assign(w)) if (w[hi][ri] > 0) { const b = bestAt(H[hi], RACES[ri]); ages[H[hi].id] = b.age; S.entries[RACES[ri].id] = H[hi].id; }
    H.forEach(h => { if (ages[h.id]) h.age = ages[h.id]; });
    // 5) Race week: the real race simulation
    const out = { prize: 0, maxPrize: RACES.reduce((t, r) => t + r.prizes[0], 0), seed, horses: H.length, budgetLeft: S.budget, ...log, runners: 0, wins: 0, top3: 0, empty: [], canRunAny: 0 };
    H.forEach(h => { if (RACES.some(r => bestAt(h, r).w > 0)) out.canRunAny++; });
    S.step = 4;
    for (const [i, r] of RACES.entries()) {
      const id = S.entries[r.id];
      if (!id) { out.empty.push((isOpenRace(r) ? "Handicap " : r.grade + " ") + r.ageLabel); (out.emptyNames = out.emptyNames || []).push(r.name); continue; }
      out.runners++;
      const pos = (await simRace(i)).order.indexOf(id) + 1; if (pos === 1) out.wins++; if (pos && pos <= 3) out.top3++;
      const won = pos && pos <= 4 ? r.prizes[pos - 1] : 0; out.prize = (out.prize || 0) + won; (out.byGrade = out.byGrade || {})[r.grade] = ((out.byGrade || {})[r.grade] || 0) + won;
    }
    out.raceNames = RACES.map(r => r.name);
    return out;
  }

  const byStarsThenCheap = (ok) => ok.slice().sort((a, b) => b.shownStars - a.shownStars || a.fee - b.fee)[0];
  const cheapest = (ok) => ok.slice().sort((a, b) => a.fee - b.fee || b.shownStars - a.shownStars)[0];
  const bestFirst = lots => lots.sort((a, b) => b.reserve - a.reserve);
  const cheapFirst = lots => lots.sort((a, b) => a.reserve - b.reserve);
  const STRATS = {
    "Breeder (10 mares, top sires)": { mares: { hi: 4, mid: 3 }, feeCap: 200000, keepForSale: 150000, stallion: byStarsThenCheap, lots: bestFirst, maxLots: 3, bidUpTo: 1.5 },
    "Buyer (family mares, big at sale)": { mares: {}, feeCap: 75000, keepForSale: 0, stallion: byStarsThenCheap, lots: bestFirst, maxLots: 12, bidUpTo: 1.6 },
    "Balanced (6 mares, 7 buys)": { mares: { hi: 3 }, feeCap: 125000, keepForSale: 700000, stallion: byStarsThenCheap, lots: bestFirst, maxLots: 7, bidUpTo: 1.5 },
    "Cheap and wide (lots of cheap horses)": { mares: { lo: 4, mid: 3 }, feeCap: 30000, keepForSale: 0, stallion: byStarsThenCheap, lots: cheapFirst, maxLots: 8, bidUpTo: 1.4 },
    "All-in on quality (few, best)": { mares: { hi: 3 }, feeCap: 200000, keepForSale: 600000, stallion: byStarsThenCheap, lots: bestFirst, maxLots: 4, bidUpTo: 1.8 },
    "Card-aware planner": { plan: true, mares: { hi: 4, mid: 2 }, feeCap: 200000, keepForSale: 400000, stallion: byStarsThenCheap, lots: bestFirst, maxLots: 5, bidUpTo: 1.7 }
  };

  window.HARNESS = { play, STRATS, async run(name, n, start, budget) {
    const P = STRATS[name], res = [];
    for (let k = 0; k < n; k++) res.push(await play(P, (start || 50000) + k, budget));
    return res;
  } };
})();
