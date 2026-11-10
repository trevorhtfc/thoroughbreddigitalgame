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
function stallionSelect(kind, fits) {
  const list = STALLIONS.map(s => stallion(s.name)).filter(fits).sort((a, b) => b.shownStars - a.shownStars || a.name.localeCompare(b.name));
  return `<select class="tm-sel" data-choose="${kind}"><option value="">Choose a stallion…</option>${list.map(s => `<option value="${esc2(s.name)}">${esc2(s.name)} · ${s.shownStars}★ · ${s.optimumDistance} · ${money(s.fee)}</option>`).join("")}</select>`;
}
function teamAtStud() {
  if (!teamOn() || teamSkipped()) return "";
  const out = [];
  const el = held("elite");
  if (el) { const left = eliteLeft();
    out.push(tcard(el, { cls: "sm", extra: left.length ? `<p class="tc-do"><b>${left.length} free mare${left.length === 1 ? "" : "s"} to choose</b> below the mares sale.</p>` : `<p class="tc-done">Used</p>` })); }
  const bt = held("blacktype");
  if (bt) { const ch = S.team.choice.blacktype, used = S.team.used.blacktype || 0;
    out.push(tcard(bt, { cls: "sm", extra: ch ? `<p class="tc-do"><b>${esc2(ch)}</b>: half price · ${BLACK_TYPE_USES - used} of ${BLACK_TYPE_USES} left</p>` : stallionSelect("blacktype", blackTypeFits) })); }
  const sm = held("studmaster");
  if (sm) { const ch = S.team.choice.studmaster;
    out.push(tcard(sm, { cls: "sm", extra: ch ? `<p class="tc-do">Your secret stallion: <b>${esc2(ch)}</b></p>` : stallionSelect("studmaster", () => true) + `<p class="tc-hint">Choose before you leave the stud, or one is picked for you.</p>` })); }
  return out.length ? `<section class="sect tm-at"><div class="sect-h"><h2 class="tb-h2">YOUR OWNER'S CARDS</h2></div><div class="tm-hand sm">${out.join("")}</div></section>` : "";
}
function eliteMares() {
  const left = eliteLeft(); if (!left.length || S.offer) return "";
  const p = PILES.find(x => x.id === left[0]), ms = pileLeft(p).sort((a, b) => b.stars - a.stars || a.name.localeCompare(b.name));
  return `<section class="sect msale tm-elite"><div class="sect-h"><h2 class="tb-h2">ELITE MARES · FREE</h2><span>Any ${p.name} (${p.stars.map(n => n + "★").join("–")}) mare you like, on top of your ${MARE_CAP}</span></div>
    <div class="offers wide">${ms.map(m => `<div class="offer"><div class="hc m"><div class="hc-top"><span class="hc-l">M</span><span class="hc-n">${esc2(m.name)}</span></div>
      <div class="hc-b"><div class="hc-r">${pips(m.stars)}<span class="hc-pk">Peaks <b>${m.peakAge}</b></span></div>${hcTrip(m)}<div class="hc-meta one"><span><b>${m.sireLine} | ${m.sireCode}</b></span></div><div class="hc-g">${m.groundPreference.join(", ")}</div></div></div>
      <button class="tb-btn block" data-elite="${esc2(m.name)}">Take her free</button></div>`).join("")}</div></section>`;
}
function teamAtSales() {
  if (!teamOn() || teamSkipped()) return "";
  const out = [];
  const ins = held("insider");
  if (ins) out.push(tcard(ins, { cls: "sm", extra: `<p class="tc-do">${ins.tier >= 2 ? "Each lot shows its yearling's class. " : ""}${ins.tier !== 2 ? (S.team.used.insider ? "Reserve buy used." : `<b>Buy at reserve</b> on ${ins.tier === 3 ? "any lot" : "a Book 2 or 3 lot"}.`) : ""}</p>` }));
  const ag = held("agent");
  if (ag) out.push(tcard(ag, { cls: "sm", extra: `<p class="tc-do">${S.team.used.agent ? "Used." : "Ready: offered when a yearling is knocked down to you."}</p>` }));
  const sm = held("studmaster");
  if (sm) out.push(tcard(sm, { cls: "sm", extra: `<p class="tc-do">Your stallion: <b>${esc2(S.team.choice.studmaster || "–")}</b> · stud income <b>${money(teamIncome())}</b> (${S.team.used.studmaster || 0} of ${STUD_MASTER_LOTS} lots)</p>` }));
  return out.length ? `<section class="sect tm-at"><div class="sect-h"><h2 class="tb-h2">YOUR OWNER'S CARDS</h2></div><div class="tm-hand sm">${out.join("")}</div></section>` : "";
}
// a lot as an Auction Insider sees it: the yearling's class and trip at its peak
function lotInsight(l) {
  if (!insiderSees()) return "";
  const f = lotFoal(l); if (!f) return "";
  const peak = f.r[2], cls = peak >= 120 ? "gold" : peak >= 110 ? "silver" : peak >= 100 ? "bronze" : "basic";
  return `<div class="lot-ins ${cls}"><b>Insider</b> peaks about <b>${Math.round(peak / 5) * 5}</b> · ${tripText(f.d[2])} · at ${f.peakAge}YO</div>`;
}
function lotClaim(l) {
  return insiderClaimOK(l) && l.reserve <= S.budget && !S.foal && !stableFull() ? `<button class="tb-btn ghost block tm-claim" data-claim="${l.id}">Insider: buy now at ${money(l.reserve)}</button>` : "";
}
function claimLot(id) {
  const l = S.sale.find(x => x.id === id); if (!l || !insiderClaimOK(l) || l.reserve > S.budget || S.foal || stableFull()) return;
  S.team.used.insider = true; S.budget -= l.reserve; S.sale = S.sale.filter(x => x !== l);
  breed(l.sire, l.dam, "bought", l.reserve, l); save();
}
function agentButton(F) {
  const a = F && F.how === "bought" && agentLeft(); if (!a) return "";
  return `<button class="tb-btn ghost" data-agent="1">Hand back: ${money(Math.round(F.cost * AGENT_REFUND[a.tier]))} (agent)</button>`;
}
function handBack() {
  const F = S.foal, a = agentLeft(); if (!F || F.how !== "bought" || !a) return;
  const back = Math.round(F.cost * AGENT_REFUND[a.tier]);
  S.budget += back; S.team.used.agent = true; S.foal = null; save();
  toast(`Handed back through your Bloodstock Agent: ${money(back)} returned`);
}
// Entries: your trainer cards on horses, your jockeys booked for races
function teamAtEntries() {
  if (!teamOn() || teamSkipped()) return "";
  const tr = trainerCards(), jk = jockeyCards();
  const trRow = c => { const sp = trainerSpec(c.kind, c.tier), on = trainHorses(c);
    if (sp.horses >= 99) return tcard(c, { cls: "sm", extra: `<p class="tc-do">On every horse in your stable.</p>` });
    const opts = S.stable.filter(h => trainerCanGo(c, h)).sort((a, b) => a.name.localeCompare(b.name));
    const slots = Array.from({ length: sp.horses }, (_, k) => `<select class="tm-sel" data-train="${c.code}" data-slot="${k}"><option value="">${k ? "And a second horse…" : "Give to a horse…"}</option>${opts.map(h => `<option value="${h.id}" ${on[k] === h.id ? "selected" : ""}>${esc2(h.name)} · ${h.age}YO · ${tripText(tripAt(h, h.age))}</option>`).join("")}</select>`).join("");
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
