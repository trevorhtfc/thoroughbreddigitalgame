// Team test harness (10 Nov 2026): plays whole seasons with a team of owner, trainer and jockey cards (js/team.js), as
// a sensible player would use them, to see how much each card is worth and whether the team changes the best way to
// play. Runs inside the game page (load after the game's scripts), using the game's own rules, sale and race engine,
// like tools/harness.js. Math.random is seeded per season so the same season can be replayed with a different team.
//
//   await TEAMH.play(strategyName, seed, ["O3-powerhouse", "T2-miler", "J1-closer"])  -> { prize, wins, ... }
(function () {
  const winChance = (h, r, c) => { const top = Math.max(...CARD.races[r.i].opp.map(o => o.rating)); return 0.85 / (1 + Math.exp(-(c.day - top - 3) / 4)); };
  function assign(w) {
    const nH = w.length, nR = w[0] ? w[0].length : 0, n = Math.max(nH, nR); if (!n) return [];
    const a = Array.from({ length: n + 1 }, (_, i) => Array.from({ length: n + 1 }, (_, j) => i && j ? (i <= nH && j <= nR ? 1 - w[i - 1][j - 1] : 1) : 0));
    const u = Array(n + 1).fill(0), v = Array(n + 1).fill(0), p = Array(n + 1).fill(0), way = Array(n + 1).fill(0);
    for (let i = 1; i <= n; i++) {
      p[0] = i; let j0 = 0; const minv = Array(n + 1).fill(Infinity), used = Array(n + 1).fill(false);
      do {
        used[j0] = true; const i0 = p[j0]; let delta = Infinity, j1 = 0;
        for (let j = 1; j <= n; j++) if (!used[j]) { const cur = a[i0][j] - u[i0] - v[j]; if (cur < minv[j]) { minv[j] = cur; way[j] = j0; } if (minv[j] < delta) { delta = minv[j]; j1 = j; } }
        for (let j = 0; j <= n; j++) if (used[j]) { u[p[j]] += delta; v[j] -= delta; } else minv[j] -= delta;
        j0 = j1;
      } while (p[j0] !== 0);
      do { const j1 = way[j0]; p[j0] = p[j1]; j0 = j1; } while (j0);
    }
    const res = []; for (let j = 1; j <= n; j++) if (p[j] <= nH && j <= nR) res.push([p[j] - 1, j - 1]);
    return res;
  }
  // expected prize from a horse in a race at its best age (prize-weighted, so the planner goes for the big races)
  function bestAt(h, r) {
    let best = { w: 0 };
    for (const age of [2, 3, 4]) {
      const c = check({ ...h, age }, r);
      if (c.ok) { const p = winChance(h, r, c), w = p * r.prizes[0] / 300000 + c.eff / 1e6; if (w > best.w) best = { w, age, p }; }
    }
    return best;
  }
  const centre = (a, b) => { const x = DISTANCES.indexOf(a.optimumDistance), y = DISTANCES.indexOf(b.optimumDistance); return Math.min(x, y) * .6 + Math.max(x, y) * .4; };
  const byStarsThenCheap = ok => ok.slice().sort((a, b) => b.shownStars - a.shownStars || feeFor(a) - feeFor(b))[0];
  const STRATS = {
    "Breeder": { mares: { hi: 4, mid: 3 }, feeCap: 200000, keepForSale: 150000, lots: 3, bidUpTo: 1.5 },
    "Buyer": { mares: {}, feeCap: 75000, keepForSale: 0, lots: 12, bidUpTo: 1.6 },
    "Balanced": { mares: { hi: 3 }, feeCap: 125000, keepForSale: 700000, lots: 7, bidUpTo: 1.5 },
    "Planner": { plan: true, mares: { hi: 4, mid: 2 }, feeCap: 200000, keepForSale: 400000, lots: 5, bidUpTo: 1.7 },
  };
  const realRandom = Math.random;

  async function play(name, seed, team) {
    const P = STRATS[name];
    localStorage.clear(); Math.random = seeded(seed * 7919 + 13);
    newCard(seed);
    S.dealt = true;
    // the team, picked straight (the points rule is the draft's business; single cards can be tested on their own)
    S.team.picks = (team || []).slice(); finishTeam(); S.team.gone = true;
    const targets = RACES.slice().sort((a, b) => b.prizes[0] - a.prizes[0]), taken = new Set();
    const aim = () => targets.find(r => !taken.has(r.id));
    const log = { spent: 0, bred: 0, bought: 0, handedBack: 0, claimed: 0, studIncome: 0 };
    // owner's cards at the stud: the Stud Master's stallion (in secret, before the sale: a sire with plenty of mares
    // he can be matched with is likelier to have lots), the Black Type stallion (the best of the right stars for the races)
    if (held("studmaster")) { const c = STALLIONS.map(s => stallion(s.name)).sort((a, b) => MARES.filter(m => lotMatch(b, m)).length - MARES.filter(m => lotMatch(a, m)).length); chooseStallion("studmaster", c[Math.floor(Math.random() * 4)].name); }
    if (held("blacktype")) { const fits = STALLIONS.map(s => stallion(s.name)).filter(blackTypeFits); chooseStallion("blacktype", fits[Math.floor(Math.random() * fits.length)].name); }
    // 1) the mares: Elite Mares first (the best of the pile for the biggest races), then the strategy's piles
    while (eliteLeft().length) {
      const p = PILES.find(x => x.id === eliteLeft()[0]), t = aim(), list = pileLeft(p);
      const m = list.sort((a, b) => b.stars - a.stars || (t ? Math.abs(DISTANCES.indexOf(a.optimumDistance) - t.step) - Math.abs(DISTANCES.indexOf(b.optimumDistance) - t.step) : 0))[0];
      if (!m || !takeEliteMare(m.name)) break;
    }
    for (const [pid, n] of Object.entries(P.mares)) for (let k = 0; k < n; k++) {
      const p = PILES.find(x => x.id === pid), left = pileLeft(p);
      if (paidMares() >= MARE_CAP || !left.length || p.price > S.budget) break;
      const m = left[Math.floor(Math.random() * left.length)]; S.budget -= p.price; log.spent += p.price; S.hand.push(m.name);
    }
    // 2) breed (best mares first); the Black Type stallion when he's among the best she can have
    const sts = STALLIONS.map(s => stallion(s.name));
    for (const m of S.hand.map(byName).sort((a, b) => b.stars - a.stars)) {
      if (S.stable.length >= STABLE_CAP) break;
      const room = S.budget - P.keepForSale, ok = sts.filter(s => !pairProblem(s, m) && feeFor(s) <= Math.min(P.feeCap, room));
      if (!ok.length) continue;
      let s = byStarsThenCheap(ok);
      const bt = blackTypeStallion() && ok.find(x => x.name === blackTypeStallion() && feeFor(x) < x.fee);
      if (bt && bt.shownStars >= s.shownStars - 1) s = bt;
      else if (P.plan) { const t = aim(); if (t) { const top = Math.max(...ok.map(x => x.shownStars)); s = ok.filter(x => x.shownStars >= top - 1).sort((a, b) => Math.abs(centre(a, m) - t.step) - Math.abs(centre(b, m) - t.step) || b.shownStars - a.shownStars || feeFor(a) - feeFor(b))[0]; } }
      if (P.plan) { const t = aim(); if (t) taken.add(t.id); }
      const fee = feeFor(s); breed(s.name, m.name, "bred", fee); log.spent += fee; log.bred++;
      const F = S.foal; S.foal = F; keepFoal();
    }
    // 3) Tattersalls: the real rival buyers; an Auction Insider sees the yearlings and buys one at its reserve
    S.step = 2; newCatalogue();
    if (!held("studmaster") || !S.team.choice.studmaster) {}
    const peakOf = l => { const f = lotFoal(l); return f ? f.r[2] : 0; };
    const sees = insiderSees();
    let lots = S.sale.slice().sort((a, b) => sees ? peakOf(b) - peakOf(a) : b.reserve - a.reserve);
    if (P.plan && !sees) { const left = targets.filter(r => !taken.has(r.id)); lots = lots.map(l => { const c = centre(stallion(l.sire), byName(l.dam)); const best = Math.min(9, ...left.map(r => Math.abs(c - r.step))); return { l, sc: l.reserve - best * 40000 }; }).sort((a, b) => b.sc - a.sc).map(x => x.l); }
    // the reserve buy: the best lot it may take
    const claimable = lots.filter(l => insiderClaimOK(l) && l.reserve <= S.budget);
    if (claimable.length && S.stable.length < STABLE_CAP) {
      const l = claimable.sort((a, b) => (sees ? peakOf(b) - peakOf(a) : b.reserve - a.reserve))[0];
      claimLot(l.id); keepFoal(); log.claimed++; log.bought++; log.spent += l.reserve; lots = lots.filter(x => x !== l);
    }
    // the budget doesn't count at the end, so a sensible player spends it all: after the strategy's own lots, the best
    // of the rest while the money and the stable's room last
    let tried = 0;
    for (const l of lots) {
      if (S.stable.length >= STABLE_CAP) break;
      if (tried >= P.lots && S.budget < l.reserve * 1.2) continue;
      if (!S.sale.includes(l)) continue;
      if (sees && peakOf(l) < 100) continue;                       // an insider doesn't bid on the poor ones
      const limit = Math.min(Math.round(l.reserve * P.bidUpTo * (sees ? 1.25 : 1) / 5000) * 5000, S.budget);
      if (limit < l.reserve) continue;
      tried++;
      const ap = appeal(l), bids = RIVALS.map(r => ({ r, c: Math.random() < r.keen(l) ? l.reserve * ap * r.want(l) * (.7 + Math.random() * .9) : 0 })).sort((a, b) => b.c - a.c), top = bids[0].c;
      let price = l.reserve; if (top >= l.reserve) { while (price <= top) price += incFor(price); }
      S.sale = S.sale.filter(x => x !== l);
      if (price <= limit) {
        S.budget -= price; breed(l.sire, l.dam, "bought", price, l); log.bought++; log.spent += price;
        // a Bloodstock Agent hands back a yearling that won't make the grade
        if (agentLeft() && S.foal.h.r[2] < 100) { handBack(); log.handedBack++; log.bought--; continue; }
        keepFoal();
      } else if (top >= l.reserve) studMasterSale(l, bids[0].r.name);
    }
    closeSales();
    log.studIncome = teamIncome();
    // 4) entries: each horse at its best age for its race (with its trainer cards), then the trainer cards placed
    // where they add most, then entries again
    const H = S.stable;
    const enter = () => {
      const w = H.map(h => RACES.map(r => bestAt(h, r).w)), ages = {};
      S.entries = {};
      for (const [hi, ri] of assign(w)) if (w[hi][ri] > 0) { const b = bestAt(H[hi], RACES[ri]); ages[H[hi].id] = b.age; S.entries[RACES[ri].id] = H[hi].id; }
      H.forEach(h => { if (ages[h.id]) h.age = ages[h.id]; });
    };
    enter();
    for (const c of trainerCards()) {
      const sp = trainerSpec(c.kind, c.tier); if (sp.horses >= 99) continue;
      for (let k = 0; k < sp.horses; k++) {
        let best = null;
        for (const r of RACES) {
          const h = horse(S.entries[r.id]); if (!h || !trainerCanGo(c, h) || trainHorses(c).includes(h.id)) continue;
          const before = bestAt(h, r).w; giveTrainer(c.code, h.id); const after = bestAt(h, r).w; takeTrainer(c.code, h.id);
          // a horse that can't run anywhere yet might be made to with the card
          if (!best || after - before > best.gain) best = { h, gain: after - before };
        }
        for (const h of H) if (!Object.values(S.entries).includes(h.id) && trainerCanGo(c, h) && !trainHorses(c).includes(h.id)) {
          for (const r of RACES) if (!S.entries[r.id]) { giveTrainer(c.code, h.id); const g = bestAt(h, r).w; takeTrainer(c.code, h.id); if (!best || g > best.gain) best = { h, gain: g }; }
        }
        if (best && best.gain > 0) { const list = S.team.trains[c.code] || []; list.push(best.h.id); S.team.trains[c.code] = list; }
      }
    }
    enter();
    // jockeys: booked where the prize is biggest and his way of riding suits the horse
    for (const c of jockeyCards()) {
      const opts = RACES.filter(r => S.entries[r.id] && !bookedFor(r) && jockeySuits(c, horse(S.entries[r.id])))
        .map(r => ({ r, v: bestAt(horse(S.entries[r.id]), r).p * r.prizes[0] })).sort((a, b) => b.v - a.v);
      for (const o of opts.slice(0, JOCKEY_RIDES[c.tier])) bookJockey(o.r.id, c.code);
    }
    // 5) race week: the real race engine
    const out = { strat: name, seed, team: (team || []).join(" "), prize: 0, horses: H.length, budgetLeft: S.budget, wins: 0, runners: 0, ...log };
    S.step = 4;
    for (const [i, r] of RACES.entries()) {
      const id = S.entries[r.id]; if (!id) continue;
      out.runners++;
      const pos = (await simRace(i)).order.indexOf(id) + 1; if (pos === 1) out.wins++;
      out.prize += pos && pos <= 4 ? r.prizes[pos - 1] : 0;
    }
    out.racePrize = out.prize; out.prize += teamIncome();
    Math.random = realRandom;
    return out;
  }
  window.TEAMH = { play, STRATS };
})();
