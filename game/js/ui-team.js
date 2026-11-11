// =====================================================================================================================
// Thoroughbred: your team's screens (the rules are js/team.js). The draft at the Jockey Club, the team cards, and the
// places where they're used: the National Stud (Elite Mares, Black Type Stud, Stud Master), Tattersalls (Auction
// Insider, Bloodstock Agent), entries (trainer cards on horses, jockeys booked for races).
// =====================================================================================================================
const ROLE_CLS = { Owner: "r-own", Trainer: "r-trn", Jockey: "r-jky" };
const ROLE_BLURB = {
  Owner: "Money and bloodstock: a bigger budget, free mares, cheap nominations, help at the sales.",
  Trainer: "Make a horse better on the day, or move its best trip a step nearer the race.",
  Jockey: "Ride your horses in the races you book them for, each with his own way of winning.",
};
function tcard(c, opts = {}) {
  return `<article class="tcard ${ROLE_CLS[c.role]} t${c.tier} ${opts.cls || ""}">
    <div class="tc-top"><span class="tc-role">${c.role}</span><span class="tc-medal" title="${TIER_NAME[c.tier]}: ${c.tier} point${c.tier === 1 ? "" : "s"}">${TIER_NUM[c.tier]}</span></div>
    <h4 class="tc-title">${c.title}</h4>
    <p class="tc-text">${cardText(c)}</p>
    ${opts.fit ? `<p class="tc-fit">${opts.fit}</p>` : ""}
    <div class="tc-foot"><span>${cardWhen(c)}</span><span>${TIER_NAME[c.tier]}</span></div>
    ${opts.btn || ""}${opts.extra || ""}</article>`;
}
// A word on how a card fits this season's ten races (so the draft is a real choice)
function cardFit(c) {
  if (c.role === "Trainer") {
    const K = TRAINER_KINDS[c.kind];
    if (K.cond === "dist") { const n = RACES.filter(r => K.vals.includes(DISTANCES[r.step])).length; return `${n} of your ${RACES.length} races ${n === 1 ? "is" : "are"} at these trips.`; }
    if (K.cond === "age") { const n = RACES.filter(r => r.ages[0] <= K.vals[0] && r.ages[1] >= K.vals[0]).length; return `${n} of your races ${n === 1 ? "is" : "are"} open to ${K.vals[0]}-year-olds.`; }
  }
  if (c.role === "Jockey" && JOCKEY_KINDS[c.kind].style) return JOCKEY_KINDS[c.kind].style === "front" ? "Best on front-runners and prominent horses." : "Best on midfield and hold-up horses.";
  return "";
}
function teamPips() {
  const p = teamPoints(), roles = new Set(teamCards().map(c => c.role));
  return `<div class="tm-sum"><div class="tm-pips" aria-label="${p} of ${TEAM_POINTS} points">${Array.from({ length: TEAM_POINTS }, (_, k) => `<i class="${k < p ? "on" : ""}"></i>`).join("")}</div>
    <span><b>${p} of ${TEAM_POINTS}</b> points</span>${TEAM_ROLES.map(r => `<span class="tm-role ${ROLE_CLS[r]} ${roles.has(r) ? "got" : ""}">${roles.has(r) ? "✓" : "·"} ${r}</span>`).join("")}</div>`;
}
function draftBody() {
  const T = teamState(), mine = teamCards();
  if (T.done) return `<div class="tb-head"><h1 class="tb-h">YOUR TEAM</h1>
      <p class="tb-lede">Your team for the season. Each card says where it comes into play: the owner's cards at the stud and the sales, the trainer's on your horses at entries, the jockeys in the races you book them for.</p></div>
    ${teamPips()}<div class="tm-hand">${mine.map(c => tcard(c, { fit: cardFit(c) })).join("")}</div>`;
  const offer = T.offer ? `<section class="sect tm-offer" id="tmOffer"><div class="sect-h"><h2 class="tb-h2">${T.offer.role.toUpperCase()} · ${TIER_NAME[T.offer.tier].toUpperCase()}</h2><span>Keep one; the others go back in the deck</span></div>
      <div class="tm-hand">${T.offer.codes.map(code => { const c = teamCard(code); return tcard(c, { fit: cardFit(c), btn: `<button class="tb-btn block" data-keepcard="${code}">Keep</button>` }); }).join("")}</div></section>` : "";
  const decks = `<section class="sect"><div class="sect-h"><h2 class="tb-h2">THE DECKS</h2><span>Gold 3 points · Silver 2 · Bronze 1</span></div>
    <div class="tm-decks">${TEAM_ROLES.map(role => `<div class="tm-row ${ROLE_CLS[role]}"><div class="tm-rl"><b>${role}</b><small>${ROLE_BLURB[role]}</small></div>
      ${[3, 2, 1].map(t => { const why = deckProblem(role, t);
        return `<button class="tdeck ${ROLE_CLS[role]} t${t}" data-deck="${role}:${t}" ${why ? "disabled" : ""}><span class="td-m">${TIER_NUM[t]}</span><b>${TIER_NAME[t]}</b><small>${why || `${t} point${t === 1 ? "" : "s"} · turn over ${TEAM_OFFER}`}</small></button>`; }).join("")}</div>`).join("")}</div></section>`;
  return `<div class="tb-head"><h1 class="tb-h">DRAFT YOUR TEAM</h1>
      <p class="tb-lede">Before the stud opens, pick the people behind your stable. You have ${TEAM_POINTS} points: a Gold card costs 3, Silver 2 and Bronze 1, and you need at least one owner, one trainer and one jockey. Choose a deck, see three of its cards and keep one.</p></div>
    ${teamPips()}${offer}${T.offer ? "" : decks}
    ${mine.length ? `<section class="sect"><div class="sect-h"><h2 class="tb-h2">YOUR TEAM SO FAR</h2></div><div class="tm-hand">${mine.map(c => tcard(c, { fit: cardFit(c) })).join("")}</div></section>` : ""}`;
}

// ---------- the team at work, place by place ----------
const panel = out => out.length ? `<section class="sect tm-at"><div class="sect-h"><h2 class="tb-h2">YOUR OWNER'S CARDS</h2></div><div class="tm-hand sm">${out.join("")}</div></section>` : "";
// Pedigree Expert: ask about an unproven stallion (Gold knows them all)
function expertBit() {
  const c = held("pedigree"); if (!c) return "";
  const known = unprovenStallions().filter(x => knowsTrue(x.name)).map(x => `${esc2(x.name)} <b>${x.trueStars}★</b>`);
  const ask = pedigreeLeft() > 0 ? `<select class="tm-sel" data-ask="1"><option value="">Ask about an unproven stallion (${pedigreeLeft()} left)…</option>${unprovenStallions().filter(x => !knowsTrue(x.name)).map(x => `<option value="${esc2(x.name)}">${esc2(x.name)} · shown ${x.shownStars}★</option>`).join("")}</select>` : "";
  return tcard(c, { cls: "sm", extra: `${known.length ? `<p class="tc-do">Really: ${known.join(", ")}</p>` : ""}${ask}` });
}
function teamAtStud() {
  if (!teamOn() || teamSkipped()) return "";
  const out = [];
  const el = held("elite");
  if (el) out.push(tcard(el, { cls: "sm", extra: `<p class="tc-do">Each draw at the mares sale turns over <b>${offerSize()}</b> mares.</p>` }));
  const so = held("stallion");
  if (so) { const own = ownedStallion();
    out.push(tcard(so, { cls: "sm", extra: own ? `<p class="tc-do">Your stallion: <b>${esc2(own)}</b> · ${ownedFreeLeft()} of ${OWNED_FREE} free nominations left</p>`
      : `<p class="tc-do">Keep one as your own:</p><div class="tm-own">${ownerDraw().map(n => { const x = stallion(n); return `<button class="tb-btn ghost" data-own="${esc2(n)}"><b>${esc2(n)}</b><small>${x.shownStars}★${x.unproven ? " unproven" : ""} · best ${x.optimumDistance} · peaks ${x.peakAge}</small></button>`; }).join("")}</div>` })); }
  const pe = expertBit(); if (pe) out.push(pe);
  return panel(out);
}
function teamAtSales() {
  if (!teamOn() || teamSkipped()) return "";
  const out = [], sc = held("scout"), ag = held("agent"), vt = held("vet"), pv = held("private");
  if (sc) out.push(scoutCard(sc));
  if (ag) out.push(tcard(ag, { cls: "sm", extra: `<p class="tc-do">His projection is on every lot.</p>` }));
  if (vt) out.push(tcard(vt, { cls: "sm", extra: `<p class="tc-do">${vetLeft()} of ${VET_USES[vt.tier]} left: offered when a yearling is knocked down to you.</p>` }));
  if (pv) out.push(tcard(pv, { cls: "sm", extra: `<p class="tc-do">${S.team.used.private ? "Used." : "Look for <b>Private sale</b> on the lots it can buy."}</p>` }));
  const pe = expertBit(); if (pe) out.push(pe);
  return panel(out);
}
// Sales Scout: tick the races you still need a horse for, then brief him (his finds join the Books)
const shortRace = r => r.name.replace(/ Stakes$| Handicap$/, "");
function scoutCard(c) {
  const T = scoutState(), max = SCOUT_RACES[c.tier];
  if (T.briefed) return tcard(c, { cls: "sm wide", extra: `<p class="tc-do">Shopping for: <b>${scoutRaces().map(shortRace).join(", ")}</b>. ${T.found && T.found.length ? `His ${T.found.length === 1 ? "find is" : T.found.length + " finds are"} marked <b>Scout's find</b> in the Books.` : ""} Lots that don't suit them are greyed out.</p>` });
  // a race you already have a runner for (as your horses are now)
  const have = r => S.stable.some(h => { const k = check(h, r); return k.ok; });
  const chips = RACES.map(r => { const on = T.races.includes(r.id), full = !on && T.races.length >= max;
    return `<button class="sc-race ${on ? "on" : ""}" data-scoutrace="${r.id}" ${full ? "disabled" : ""} aria-pressed="${on}"><b>${esc2(shortRace(r))}</b><small>${r.ageLabel || r.ages[0] + "YO"} · ${DISTANCES[r.step]} · ${scoutBar(r)}+ to place${have(r) ? " · you have a runner" : ""}</small></button>`; }).join("");
  return tcard(c, { cls: "sm wide", extra: `<p class="tc-do">Pick up to <b>${max}</b> races you still need a horse for (${T.races.length} picked). The Books show which lots suit them as you pick.</p>
    <div class="sc-races">${chips}</div>
    <button class="tb-btn block" data-scout="go" ${T.races.length ? "" : "disabled"}>Brief your scout${SCOUT_LOTS[c.tier] ? `: he adds ${SCOUT_LOTS[c.tier] === 1 ? "a lot" : SCOUT_LOTS[c.tier] + " lots"} of his own` : ""}</button>` });
}
// what the scout says on a lot: his find, the races it suits, or greyed out
function lotScout(l) {
  if (l.scout) { const r = RACES.find(x => x.id === l.scout); return { cls: "sc-find", html: `<div class="lot-sc find"><b>Scout's find</b> bred for the ${esc2(r ? r.name : "race")}</div>` }; }
  const v = lotSuits(l); if (!v) return { cls: "", html: "" };
  if (!v.list.length) return { cls: "sc-off", html: `<div class="lot-sc off">Not for your races</div>` };
  return { cls: "sc-on", html: `<div class="lot-sc on">Suits ${v.list.map(x => `<b>${esc2(shortRace(x.r))}</b>${x.p >= SCOUT_LIKELY ? "" : " (maybe)"}`).join(", ")}</div>` };
}
// the Books in the scout's order: his finds, then the lots for your races, the rest last
function scoutOrder(list) {
  if (!held("scout") || !scoutRaces().length) return list;
  const w = l => l.scout ? 2 : (lotSuits(l) || { best: 0 }).best;
  return list.slice().sort((a, b) => w(b) - w(a));
}
// a lot as your Bloodstock Agent sees it: his projected peak rating, a range with the truth somewhere in it
function lotInsight(l) {
  const r = agentRange(l); if (!r) return "";
  const mid = (r.lo + r.hi) / 2, cls = mid >= 120 ? "gold" : mid >= 110 ? "silver" : mid >= 100 ? "bronze" : "basic";
  return `<div class="lot-ins ${cls}"><b>Agent</b> projects a peak of <b>${r.lo}–${r.hi}</b></div>`;
}
function lotClaim(l) {
  if (!privateOK(l) || S.foal || stableFull()) return "";
  const p = privatePrice(l), cost = payFor(p);
  return cost <= S.budget ? `<button class="tb-btn ghost block tm-claim" data-claim="${l.id}">Private sale: ${money(p)}, no auction</button>` : "";
}
function claimLot(id) {
  const l = S.sale.find(x => x.id === id); if (!l || !privateOK(l) || S.foal || stableFull()) return;
  const cost = payFor(privatePrice(l)); if (cost > S.budget) return;
  S.team.used.private = true; S.budget -= cost; ledger("yearlings", cost); S.sale = S.sale.filter(x => x !== l);
  breed(l.sire, l.dam, "bought", cost, l); save();
}
function agentButton(F) {
  const v = F && F.how === "bought" && held("vet"); if (!v || vetLeft() <= 0) return "";
  return `<button class="tb-btn ghost" data-agent="1">Send back (vet's report): ${money(Math.round(F.cost * VET_REFUND[v.tier]))} refunded</button>`;
}
function handBack() {
  const F = S.foal, v = held("vet"); if (!F || F.how !== "bought" || !v || vetLeft() <= 0) return;
  const back = Math.round(F.cost * VET_REFUND[v.tier]);
  S.budget += back; ledger("yearlings", -back); S.team.used.vet = (S.team.used.vet || 0) + 1; S.foal = null; save();
  toast(`Sent back on the vet's report: ${money(back)} refunded`);
}
// Entries: your trainer cards on horses, your jockeys booked for races
function teamAtEntries() {
  if (!teamOn() || teamSkipped()) return "";
  const tr = trainerCards(), jk = jockeyCards();
  const trRow = c => { const sp = trainerSpec(c.kind, c.tier), on = trainHorses(c);
    if (sp.horses >= 99) return tcard(c, { cls: "sm", extra: `<p class="tc-do">On every horse in your stable.</p>` });
    const opts = S.stable.filter(h => trainerCanGo(c, h)).sort((a, b) => a.name.localeCompare(b.name));
    const slots = Array.from({ length: sp.horses }, (_, k) => `<select class="tm-sel" data-train="${c.code}" data-slot="${k}"><option value="">${k ? "And another horse…" : "Give to a horse…"}</option>${opts.map(h => `<option value="${h.id}" ${on[k] === h.id ? "selected" : ""}>${esc2(h.name)} · ${h.age}YO · ${tripText(tripAt(h, h.age))}</option>`).join("")}</select>`).join("");
    return tcard(c, { cls: "sm", extra: opts.length ? slots : `<p class="tc-hint">None of your horses can take it.</p>` }); };
  const jkRow = c => tcard(c, { cls: "sm", extra: `<p class="tc-do">Booked for <b>${ridesOf(c.code).length} of ${JOCKEY_RIDES[c.tier]}</b> rides${ridesOf(c.code).length ? ": " + ridesOf(c.code).map(r => r.name.replace(/ Stakes$/, "")).join(", ") : ". Book him in a race below."}</p>` });
  return `<details class="sect tm-at" ${S.team.openEntries === false ? "" : "open"}><summary class="sect-h"><h2 class="tb-h2">YOUR TRAINER AND JOCKEYS</h2><span>Trainer cards go on horses; jockeys are booked race by race</span></summary>
    <div class="tm-hand sm">${tr.map(trRow).join("")}${jk.map(jkRow).join("")}</div></details>`;
}
// the jockey line in a race's panel at entries
function jockeyPick(r) {
  if (!teamOn() || teamSkipped()) return "";
  const jk = jockeyCards(); if (!jk.length) return "";
  const cur = bookedFor(r), h = horse(S.entries[r.id]);
  if (!h && !cur) return `<div class="tm-jk"><span>Jockey</span><small>Enter a runner, then book one of your jockeys for it.</small></div>`;
  return `<div class="tm-jk"><span>Jockey</span><select class="tm-sel" data-bookrace="${r.id}"><option value="">Your yard's own jockey</option>${jk.map(c => { const left = ridesLeft(c) + (cur && cur.code === c.code ? 1 : 0);
    return `<option value="${c.code}" ${cur && cur.code === c.code ? "selected" : ""} ${left > 0 ? "" : "disabled"}>${cardName(c)} (${left} ride${left === 1 ? "" : "s"} left)${h && !jockeySuits(c, h) ? " · doesn't suit its style" : ""}</option>`; }).join("")}</select></div>`;
}
// what the team does for a horse in a race, in words (for the horse cards' verdict line)
function teamNote(c) {
  if (!c || !c.train || !c.train.cards.length) return "";
  return " · " + c.train.cards.map(x => `${x.did} ${cardName(x.c)}`).join(", ");
}
