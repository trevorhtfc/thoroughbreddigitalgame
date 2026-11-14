// =====================================================================================================================
// Thoroughbred: the pieces the game's screens are made of (from the Ascot game, ascot-game/index.html): stallion and
// mare cards, the mares sale, the sale ring and its live auction, the horse cards, the race planner, entries, race
// week, the final standings, the animated horse card (card.html) and the 3D race view (final-furlong.html).
// The shell that places them in sheets over the Newmarket board is js/ui.js.
// =====================================================================================================================
/* ================= Rendering ================= */
const $ = s => document.querySelector(s);
const esc2 = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2400); }
/* ----- Step 1: breed and buy ----- */
function needs() {
  // which race slots still look hard to fill, by age and sex, from the horses you have
  const n = { F: S.stable.filter(h => h.sex === "F").length, C: S.stable.filter(h => h.sex === "C").length };
  return `${S.stable.length} horse${S.stable.length === 1 ? "" : "s"} · ${RACES.length} needed, room for ${STABLE_CAP} · ${n.C} colt${n.C === 1 ? "" : "s"}, ${n.F} fill${n.F === 1 ? "y" : "ies"}`;
}
function stableSection() {
  return `<section class="stable"><div class="sect-h"><h2 class="tb-h2">YOUR STUD FARM</h2><span>${needs()}</span></div>
      ${S.stable.length ? cardGroups(S.stable, null, false) : `<p class="tb-empty">No horses yet. Your first foal will appear here.</p>`}</section>`;
}
// Reference views on the stud and sale steps
function viewTabs(job) {
  const v = S.view === "plan" ? "plan" : "job", planned = RACES.filter(r => (S.targets || {})[r.id] && horse(S.targets[r.id])).length;
  return `<div class="vtabs" role="tablist"><button class="vtab ${v === "job" ? "on" : ""}" id="vjob" role="tab" aria-selected="${v === "job"}">${job}</button><button class="vtab ${v === "plan" ? "on" : ""}" id="vplan" role="tab" aria-selected="${v === "plan"}">Race planner<i>${planned}/${RACES.length}</i></button></div>`;
}
function goingStrip() {
  return `<div class="going"><b>THE GOING</b>${DAYS.map((d, k) => `<span class="gday g-${CARD.going[k]}"><small>${dayTag(k)}</small>${CARD.going[k]}</span>`).join("")}
    <p>Set when the card is dealt, so you can breed and buy for it. A horse that likes the day's going runs better.</p></div>`;
}
function refCard(r) {
  return `<article class="race"><div class="race-top">${gradeBox(r)}
      <div style="min-width:0"><h4 class="race-name">${r.name}</h4>
        <div class="facts"><span><b>${ageOnly(r)}</b></span>${sexTag(r)}<span>1st <b>${money(r.prizes[0])}</b></span>${r.grade === "Handicap" ? `<span>Max rating <b>${HCAP_MAX}</b></span>` : ""}</div>
        ${bandsLine(r)}
      </div><div></div></div></article>`;
}
function refView(job) { return S.view === "plan" ? plannerView() : job(); }
const onJob = () => S.view !== "plan";
/* ===== Race planner: race chips at the top, your horses below; drop a race on a horse to target it ===== */
// the board game's four race-day colours, best to worst: a race's rating bands are shown in them
const KEY_NAMES = ["black", "red", "yellow", "blue"];
function raceChip(r) {
  const g = GRADE[r.grade], tg = (S.targets || {})[r.id], th = tg && horse(tg), sel = S.planSel === r.id;
  return `<button class="pq ${sel ? "sel" : ""} ${th ? "has" : ""}" data-plansel="${r.id}" draggable="true" aria-pressed="${sel}" title="${r.name}${th ? " · target: " + th.name : ""}">
    <span class="pq-t"><b class="g ${g.cls}">${g.short}</b><span>${r.dist}</span><span>${ageOnly(r)}</span><span class="sx-i ${r.sex || "O"}">${r.sex === "C" ? "♂" : r.sex === "F" ? "♀" : "⚥"}</span></span>
    <span class="pq-n">${r.name.replace(/ Stakes$/, "")}</span>
    <span class="pq-b" title="Race-day rating bands, as in the board game: ${r.bands.map((b, k) => `${KEY_NAMES[k]} ${b}+`).join(", ")}">${r.bands.map((b, k) => `<i class="k-${KEY_NAMES[k]}">${b}</i>`).join("")}${r.grade === "Handicap" ? `<em title="Handicap: horses rated ${HCAP_MAX} or less">≤${HCAP_MAX}</em>` : ""}</span>
    ${th ? `<span class="pq-who">★ ${esc2(th.name)}</span>` : ""}</button>`;
}
function fitFor(h, r) {
  if (r.sex && h.sex !== r.sex) return { no: true, t: r.sex === "F" ? "Fillies only" : "Colts only" };
  if (h.age > r.ages[1]) return { t: "Too old now", later: true };
  if (h.age < r.ages[0]) return { t: `Needs to be ${r.ages[0]}YO`, later: true };
  const c = check(h, r);
  if (c.ok) return { ok: true, eff: c.eff, t: `${c.day} now · ${rankText(c)}${c.steps ? `, −${c.steps * 5} trip` : ""}` };
  return { t: c.why || "Can't run now", later: true };
}
function plannerView() {
  const sel = RACES.find(r => r.id === S.planSel);
  return `<section class="planner">
    <div class="pl-grid">${DAYS.map((d, k) => `<div class="pl-day"><h4>${dayTag(k)}</h4>${RACES.filter(r => r.day === k).map(raceChip).join("")}</div>`).join("")}</div>
    <p class="pl-help">${sel ? `<b>${sel.name}</b> selected: the cards show how each horse fits it. Tap <b>+</b> on a horse to target it, or tap the race again to let go.` : "Drag a race onto a horse's Race targets box, or tap a race to see how every horse fits it."}</p>
    ${S.stable.length ? horseCols(S.stable, sel || null, false, { plan: true }, false) : `<p class="tb-empty">No horses yet. Breed or buy some, then plan their races here.</p>`}
  </section>`;
}
function setTarget(raceId, horseId) {
  S.targets = S.targets || {};
  if (horseId) S.targets[raceId] = horseId; else delete S.targets[raceId];
  save(); render();
}
// drag and drop (desktop); tap-to-place works everywhere
document.addEventListener("dragstart", e => { const c = e.target.closest && e.target.closest(".pq"); if (!c) return; e.dataTransfer.setData("text/plain", c.dataset.plansel); e.dataTransfer.effectAllowed = "move"; c.classList.add("drag"); });
document.addEventListener("dragend", e => { document.querySelectorAll(".pq.drag,.over").forEach(x => x.classList.remove("drag", "over")); });
const dropZone = t => t.closest && (t.closest(".hc2[data-plandrop]") || t.closest(".pl-slot"));
document.addEventListener("dragover", e => { const z = dropZone(e.target); if (!z) return; e.preventDefault(); z.classList.add("over"); });
document.addEventListener("dragleave", e => { const z = dropZone(e.target); if (z && !z.contains(e.relatedTarget)) z.classList.remove("over"); });
document.addEventListener("drop", e => {
  const z = dropZone(e.target); if (!z) return; e.preventDefault();
  const r = RACES.find(x => x.id === e.dataTransfer.getData("text/plain")), h = horse(z.dataset.plandrop); if (!r || !h) return;
  const f = fitFor(h, r); if (f.no) { toast(`${h.name} can't run in the ${r.name}: ${f.t.toLowerCase()}`); z.classList.remove("over"); return; }
  setTarget(r.id, h.id); toast(`${h.name} targeted at the ${r.name}${f.ok ? "" : ": it doesn't qualify yet"}`);
});
function breedBody() {
  return `<div class="tb-head"><h1 class="tb-h">BREED</h1>
    <p class="tb-lede" ${onJob() ? "" : "hidden"}>You have ${money(startBudget() + (held("powerhouse") ? POWERHOUSE[held("powerhouse").tier] : 0))} to build a stable for this season's ${RACES.length} races, with room for ${STABLE_CAP - RACES.length} spares. ${handOn() ? `Your stud starts with ${HAND.hi + HAND.mid + HAND.lo} mares dealt to you: ${HAND.hi} Blue-blooded, ${HAND.mid} Useful and ${HAND.lo} Moderate. Breed them, buy one more if you like, or send back any you don't want for half her price.` : `Buy mares at the mares sale (pick a pile, then choose one of the ${offerSize()} turned over; up to ${MARE_CAP}), then breed them.`} Keep some money back for Tattersalls, where the sale is made from the mares nobody bred: the cheapest Book 1 yearling starts at ${money(RESERVES[BOOKS[0].min])}. Tap your money at the top to see where it's gone. Every foal arrives as a 2-year-old, and it's a coin flip whether you get a colt or a filly.</p></div>
    ${viewTabs("The stud")}
    ${refView(studView)}`;
}
function saleBody() {
  return `<div class="tb-head"><h1 class="tb-h">TATTERSALLS</h1>
    <p class="tb-lede" ${onJob() ? "" : "hidden"}>Your last chance to strengthen the stable before the races. The catalogue is made from the mares nobody bred, each lot by a stallion drawn at random.</p></div>
    ${viewTabs("The sale ring")}
    ${refView(saleView)}`;
}
/* Stallion and mare cards, drawn like the board game's cards (html/breeding.html) */
function pips(n, variable) {
  n = Number(n) || 0;
  if (variable && n >= 1 && n <= 5) {
    const c = i => 20 + 40 * (i - 1), x1 = n > 1 ? c(n - 1) - 17 : c(n) - 4, x2 = n < 5 ? c(n + 1) + 17 : c(n) + 4;
    let o = '<svg class="var" viewBox="0 0 200 40">';
    o += `<line x1="${x1}" y1="20" x2="${x2}" y2="20" stroke="#3d7153" stroke-width="2.5" stroke-dasharray="4 4"/>`;
    if (n > 1) o += `<path d="M${x1 - 1} 20 l8 -5 v10z" fill="#3d7153"/>`;
    if (n < 5) o += `<path d="M${x2 + 1} 20 l-8 -5 v10z" fill="#3d7153"/>`;
    for (let i = 1; i <= 5; i++) { if (i === n) continue; o += `<use href="#pip" x="${c(i) - 13}" y="7" width="26" height="26" opacity=".32"/>`; }
    o += `<circle cx="${c(n)}" cy="20" r="18.5" fill="#fffdf7" stroke="#3d7153" stroke-width="2.5"/><use href="#pip" x="${c(n) - 14}" y="6" width="28" height="28"/>`;
    return `<span class="pips" style="color:var(--pip)" role="img" aria-label="${n} star, could be one star either way">${o}</svg></span>`;
  }
  let o = ""; for (let i = 1; i <= 5; i++) o += `<svg class="${i <= n ? "" : "off"}"><use href="#pip"/></svg>`;
  return `<span class="pips" role="img" aria-label="${n} star ability">${o}</span>`;
}
const hcTrip = x => `<div class="hc-trip"><span>${x.minDistance}</span><i>|</i><b>${x.optimumDistance}</b><i>|</i><span>${x.maxDistance}</span></div>`;
function mareCard(name) {
  const m = byName(name), on = S.selMare === name;
  return `<button class="hc m ${on ? "on" : ""}" data-mare="${esc2(name)}" aria-pressed="${on}"><span class="tick">✓</span>
    <div class="hc-top"><span class="hc-l">M</span><span class="hc-n">${esc2(m.name)}</span></div>
    <div class="hc-b"><div class="hc-r">${pips(m.stars)}<span class="hc-pk">Peaks <b>${m.peakAge}</b></span></div>
    ${hcTrip(m)}<div class="hc-meta one"><span><b>${m.sireLine} | ${m.sireCode}</b></span></div><div class="hc-g">${m.groundPreference.join(", ")}</div></div></button>`;
}
function stallionCard(s, m) {
  const prob = m ? pairProblem(s, m) : "", on = S.selStallion === s.name, ln = m && !prob ? lineNote(s, m) : null;
  return `<button class="hc s ${on ? "on" : ""}" data-stallion="${esc2(s.name)}" ${prob ? "disabled" : ""} aria-pressed="${on}"><span class="tick">✓</span>
    <div class="hc-top"><span class="hc-l">S</span><span class="hc-n">${esc2(s.name)}</span></div>
    <div class="hc-b"><div class="hc-r">${knowsTrue(s.name) ? pips(s.trueStars) : pips(s.shownStars, s.unproven)}<span class="hc-fee">${feeFor(s) < s.fee ? `<s>${money(s.fee)}</s> Free` : money(s.fee)}</span></div>
    ${hcTrip(s)}<div class="hc-meta"><span><b>${s.sireLine} | ${s.sireCode}</b></span><span>Peaks <b>${s.peakAge}</b></span></div>
    <div class="hc-g">${s.groundPreference.join(", ")}</div>
    <div class="hc-foot">${s.unproven ? (knowsTrue(s.name) ? `<span class="warn">Your expert: really ${s.trueStars}★</span>` : `<span class="warn">Unproven: one star either way</span>`) : ""}${prob ? `<span class="why">${esc2(prob)}</span>` : ""}${ln ? `<span class="ln ${ln.cls}">${ln.text}</span>` : ""}</div></div></button>`;
}
function studView() {
  if (!handDone()) return `${teamAtStud()}${dealView()}`;
  const m = S.selMare && byName(S.selMare);
  let rows = STALLIONS.map(s => stallion(s.name)).filter(s => (S.trip || "all") === "all" || band(s.optimumDistance) === S.trip);
  rows.sort(S.sort === "stars" ? (a, b) => b.shownStars - a.shownStars || a.fee - b.fee : S.sort === "trip" ? (a, b) => DISTANCES.indexOf(a.optimumDistance) - DISTANCES.indexOf(b.optimumDistance) || a.fee - b.fee : (a, b) => a.fee - b.fee || b.shownStars - a.shownStars);
  if (m) rows = rows.filter(s => !pairProblem(s, m)).concat(rows.filter(s => pairProblem(s, m)));
  const st = S.selStallion && stallion(S.selStallion), ok = st && m && !pairProblem(st, m), fee = st ? feeFor(st) : 0, afford = st && fee <= S.budget, ln = ok ? lineNote(st, m) : null;
  const trips = [["all", "All"], ["sprint", "Sprint 5–6f"], ["mile", "Mile 7f–1m1f"], ["middle", "Middle 1m2f–1m4f"], ["staying", "Staying 1m6f+"]];
  if (!m && !studCount()) return `${teamAtStud()}${maresSale()}<section class="sect"><div class="sect-h"><h2 class="tb-h2">YOUR MARES</h2><span>0 of ${MARE_CAP}</span></div>
    <p class="tb-empty">${handOn() ? `You've sent back every mare you were dealt.${extraLeft() > 0 ? " You can still buy one above." : ""} Tattersalls is next.` : `No mares yet. Buy your first above: pick a pile, then choose one of the ${offerSize()} mares turned over.`}</p></section>`;
  if (!m) return `${teamAtStud()}<section class="sect"><div class="sect-h"><h2 class="tb-h2">YOUR MARES</h2><span>${studCount()} of ${MARE_CAP} in your stud · ${S.usedMares.length} covered · tap a mare to breed her</span></div>
    <div class="grid">${S.hand.map(mareCard).join("") || `<p class="tb-empty">${S.usedMares.length ? (extraLeft() > 0 ? "Every mare has been covered. Buy another below, or head to Tattersalls." : "Every mare has been covered: on to Tattersalls.") : "No mares yet. Buy one below."}</p>`}</div>
    ${handList()}</section>
    ${maresSale()}`;
  return `<section class="sect pick-mare"><div class="sect-h"><h2 class="tb-h2">BREEDING ${esc2(m.name).toUpperCase()}</h2><button class="tb-btn ghost sm" id="changeMare">‹ Choose a different mare</button></div>
    <div class="grid one">${mareCard(m.name)}</div></section>
    <div class="tb-bar sticky-bar"><div class="tb-bar-info ${ok && afford ? "ready" : ""}">${!m ? "Pick a mare." : !st ? `Tap a stallion for ${esc2(m.name)}.` : !ok ? esc2(pairProblem(st, m)) + "." :
      `${esc2(st.name)} × ${esc2(m.name)}. Stud fee ${fee < st.fee ? `<s>${money(st.fee)}</s> free (your own stallion)` : money(st.fee)}${ln ? ` · <span class="line ${ln.cls}">${ln.text}</span>` : ""}${afford ? "" : " · not enough budget"}${stableFull() ? ` · your stable is full (${STABLE_CAP})` : ""}`}</div>
      <div class="tb-bar-btns"><button class="tb-btn" id="breedBtn" ${ok && afford && !S.foal && !stableFull() ? "" : "disabled"}>Breed</button></div></div>
    <section class="sect"><div class="sect-h"><h2 class="tb-h2">STALLIONS</h2>
      <label class="sortby">Sort by <select id="sort"><option value="fee" ${S.sort === "fee" ? "selected" : ""}>Fee</option><option value="stars" ${S.sort === "stars" ? "selected" : ""}>Stars</option><option value="trip" ${S.sort === "trip" ? "selected" : ""}>Trip</option></select></label></div>
    <div class="filters">${trips.map(x => `<button class="tb-chip ${(S.trip || "all") === x[0] ? "on" : ""}" data-trip="${x[0]}">${x[1]}</button>`).join("")}</div>
    <div class="grid">${rows.map(s => stallionCard(s, m)).join("")}</div>
    <p class="hint">Outcross (a different sire line) adds 1–3 to the foal's rating. The same line can take up to 4 off, and the same family up to 7. Unproven stallions may turn out a star better or worse than their stud-book rating.</p></section>`;
}
function offerCard(name) {
  const m = byName(name);
  return `<div class="offer"><div class="hc m">
    <div class="hc-top"><span class="hc-l">M</span><span class="hc-n">${esc2(m.name)}</span></div>
    <div class="hc-b"><div class="hc-r">${pips(m.stars)}<span class="hc-pk">Peaks <b>${m.peakAge}</b></span></div>
    ${hcTrip(m)}<div class="hc-meta one"><span><b>${m.sireLine} | ${m.sireCode}</b></span></div><div class="hc-g">${m.groundPreference.join(", ")}</div></div></div>
    <button class="tb-btn block" data-keep="${esc2(name)}">Keep<span class="kn"> ${esc2(m.name)}</span></button></div>`;
}
// The board's Weatherbys mares decks: a card back (blue, cream edge, the stars it holds) and a stack of them
const PILE_STARS = { hi: "4&amp;5", mid: "3", lo: "1&amp;2" };
const MPIP = '<svg viewBox="0 0 40 40"><g fill="currentColor"><path d="M20 5 L35 20 L20 35 L5 20Z"/><circle cx="20" cy="3.6" r="3.2"/><circle cx="20" cy="36.4" r="3.2"/><circle cx="3.6" cy="20" r="3.2"/><circle cx="36.4" cy="20" r="3.2"/></g><circle cx="20" cy="20" r="4" fill="#2b5e74"/></svg>';
function mareBack(id) {
  return `<span class="mback"><span class="wb">WEATHERBYS</span><span class="mt">MARES</span><span class="ms">${PILE_STARS[id]}<br>Stars</span><span class="mp">${MPIP.repeat(10)}</span></span>`;
}
const mareStack = (id, n) => `<span class="mstack">${n > 1 ? '<span class="mback b2"></span>' : ""}${n > 0 ? '<span class="mback b1"></span>' : ""}${n > 0 ? mareBack(id) : '<span class="mback gone"></span>'}</span>`;
// a mare's card as it's turned over (not a button: she isn't picked for breeding until the hand is in)
const mareFace = (name, cls) => mareCard(name).replace(/^<button class="hc m[^"]*" data-mare="[^"]*" aria-pressed="[^"]*">/, `<div class="hc m ${cls || ""}">`).replace(/<\/button>$/, "</div>");
function dealView() {
  const drawn = mh().hand || [], left = PILES.reduce((a, p) => a + Math.max(0, (HAND[p.id] || 0) - handDrawn(p.id)), 0);
  return `<section class="sect mdeal"><div class="sect-h"><h2 class="tb-h2">DRAW YOUR MARES</h2><span>${drawn.length} of ${HAND.hi + HAND.mid + HAND.lo} drawn</span></div>
    <p class="hint">Your stud starts with two mares from each of the Weatherbys decks. Tap a deck to turn over its top card: she's yours.</p>
    <div class="mdecks">${PILES.map(p => { const k = (HAND[p.id] || 0) - handDrawn(p.id);
      return `<button class="mdeck ${p.id}" data-mdraw="${p.id}" ${k > 0 ? "" : "disabled"} aria-label="Draw from the ${p.name} deck">${mareStack(p.id, Math.min(3, pileLeft(p).length))}
        <b>${p.name}</b><small>${k > 0 ? `${k} to draw` : "Done"}</small></button>`; }).join("")}</div>
    ${drawn.length ? `<div class="grid mdrawn">${drawn.map(n => mareFace(n, n === UI.mareDrew ? "flipin" : "")).join("")}</div>` : ""}
    ${left > 1 ? `<p class="mdeal-all"><button class="tb-btn ghost sm" data-mdraw="all">Draw the rest for me</button></p>` : ""}</section>`;
}
// your hand's mares, each with what you can do besides breeding her: upgrade her (Elite Mares) or send her back
function handList() {
  if (!handOn() || S.offer || !S.hand.length) return "";
  const up = upgradesLeft();
  const row = n => { const m = byName(n), p = pileOf(n), sure = UI.sendBack === n;
    return `<li><span class="mh-n"><b>${esc2(m.name)}</b> ${pips(m.stars)} <small>${p.name}</small></span><span class="mh-b">
      ${canUpgrade(n) ? `<button class="tb-btn ghost sm" data-upmare="${esc2(n)}">Upgrade to ${gradeUp(n).name}</button>` : ""}
      <button class="tb-btn ghost sm ${sure ? "warn" : ""}" data-sendback="${esc2(n)}">${sure ? `Sure? Send her back for ${money(sendBackFor(n))}` : `Send back · ${money(sendBackFor(n))}`}</button></span></li>`; };
  return `<details class="mh" ${UI.handOpen || up > 0 ? "open" : ""}><summary>${up > 0 ? `Upgrade a mare (${up} left), or send one back for half her price` : "Don't want a mare? Send her back for half her price"}</summary>
    <p class="hint">A mare you send back is gone for the season, and half what she'd cost at the mares sale goes into your budget for Tattersalls.${up > 0 ? ` Elite Mares: ${up === 1 ? "one upgrade" : up + " upgrades"} left. Each one turns over ${OFFER_SIZE} mares from the grade above, and you keep one in her place.` : ""}</p>
    <ul class="mh-list">${S.hand.map(row).join("")}</ul></details>`;
}
function maresSale() {
  const full = paidMares() >= MARE_CAP;
  const pile = p => {
    const left = pileLeft(p).length, why = full ? "Stud full" : !left ? "None left" : p.price > S.budget ? "Can't afford" : "";
    return handOn() ? `<button class="mdeck ${p.id}" data-pile="${p.id}" ${why ? "disabled" : ""}>${mareStack(p.id, Math.min(3, left))}
      <b>${p.name}</b><span class="pile-p">${money(p.price)}</span><small>${why || "draw two, keep one"}</small></button>`
    : `<button class="pile ${p.id}" data-pile="${p.id}" ${why ? "disabled" : ""}>
      <span class="pile-k">${p.stars.map(n => n + "★").join("–")}</span><b class="pile-n">${p.name}</b>
      <span class="pile-p">${money(p.price)} a mare</span><span class="pile-l">${why || `${left} left`}</span></button>`;
  };
  if (S.offer) { const p = PILES.find(x => x.id === S.offer.pile), sw = S.offer.swap;
    return `<section class="sect msale" id="offer"><div class="sect-h"><h2 class="tb-h2">${sw ? `UPGRADING ${esc2(sw).toUpperCase()}` : `MARES SALE · ${p.name.toUpperCase()}`}</h2><span>${sw ? "Elite Mares: free" : `Paid ${money(p.price)}`}</span></div>
      <p class="offer-h">${S.offer.mares.length} mare${S.offer.mares.length === 1 ? "" : "s"} turned over from the ${p.stars.map(n => n + "★").join("–")} pile. ${sw ? `Keep one in place of ${esc2(sw)}, who goes back.` : "Keep one; the others go back."}</p>
      <div class="offers flip">${S.offer.mares.map(offerCard).join("")}</div></section>`; }
  if (handOn()) {
    if (extraLeft() <= 0) return "";
    return `<section class="sect msale"><div class="sect-h"><h2 class="tb-h2">ONE MORE MARE</h2><span>You may buy one extra: pay the price, see ${offerSize()} from that pile and keep the one you want</span></div>
    <div class="mdecks">${PILES.map(pile).join("")}</div>
    ${full ? `<p class="hint">Your stud is full at ${MARE_CAP} mares.</p>` : ""}</section>`;
  }
  return `<section class="sect msale"><div class="sect-h"><h2 class="tb-h2">MARES SALE</h2><span>Pay the price, see ${offerSize()} mares from that pile and keep the one you want</span></div>
    <div class="piles">${PILES.map(pile).join("")}</div>
    ${full ? `<p class="hint">Your stud is full at ${MARE_CAP} mares.</p>` : ""}</section>`;
}
function saleView() {
  return `${teamAtSales()}<section class="ring"><div class="ring-in"><div class="ring-k">TATTERSALLS</div><div class="ring-t">The sale ring</div>
    <p>Each lot is a foal by a stallion out of a mare. You see the pedigree, not the foal, until it's knocked down to you. Bring a lot into the ring and bid against rival buyers: when the auctioneer's count runs out, the hammer falls.</p></div></section>
    <div class="books" role="tablist">${BOOKS.map(b => { const n = S.sale.filter(l => l.book === b.n).length;
      const f = S.sale.filter(l => l.book === b.n && l.scout).length;
      return `<button class="book ${S.book === b.n ? "on" : ""}" data-book="${b.n}" role="tab" aria-selected="${S.book === b.n}"><b>${b.name}</b><span>${b.note} · ${n} lot${n === 1 ? "" : "s"}${f ? ` · ${f} scout's find${f === 1 ? "" : "s"}` : ""}</span></button>`; }).join("")}</div>
    ${stableFull() ? `<p class="hint">Your stable is full (${STABLE_CAP} horses), so you can't buy any more.</p>` : ""}
    <div class="lots">${scoutOrder(S.sale.filter(l => l.book === S.book)).map(l => { const s = stallion(l.sire), m = byName(l.dam), line = lineNote(s, m), sc = lotScout(l);
      return `<article class="lot ${sc.cls}"><div class="lot-h"><span class="lot-n">LOT ${l.n}</span><span class="line ${line.cls}">${line.text}</span></div>
        <div class="ped">
          <div class="pc s"><span class="pc-l">S</span><div><b>${esc2(s.name)}</b>${knowsTrue(s.name) ? pips(s.trueStars) : pips(s.shownStars, s.unproven)}<small>${s.optimumDistance} · peaks ${s.peakAge}</small></div></div>
          <div class="pc m"><span class="pc-l">M</span><div><b>${esc2(m.name)}</b>${pips(m.stars)}<small>${m.optimumDistance} · peaks ${m.peakAge}</small></div></div></div>
        ${sc.html}${lotInsight(l)}<div class="lot-foot"><span>Reserve ${money(l.reserve)} · guide ${money(guide(l)[0])}–${money(guide(l)[1])}</span></div>
        <button class="tb-btn block" data-auction="${l.id}" ${openBid(l) <= canBidTo() && !S.foal && !stableFull() ? "" : "disabled"}>${openBid(l) <= canBidTo() ? "Bring into the ring" : "Can't afford the opening bid"}</button>${lotClaim(l)}</article>`; }).join("") || `<p class="tb-empty">Every lot in this Book has been sold.</p>`}</div>`;
}
function stableCard(h, developable) {
  const r = RACES.find(x => S.entries[x.id] === h.id), now = ratingAt(h, h.age), o = outlook(h);
  return `<div class="horse ${r ? "used" : ""}"><div class="row"><b>${esc2(h.name)}</b><span class="rating" title="Rating now">${now}</span></div>
    <div><span class="sex ${h.sex}">${h.sex === "F" ? "♀" : "♂"}</span> ${h.age}yo ${sexWord(h)} · by ${esc2(h.sire)}</div>
    <div>Best ${tripText(tripAt(h, h.age))} · likes ${h.grounds.join(", ")}</div>
    <div>Projected peak ${h.peakAge}YO</div>
    ${developable ? (h.age < 4 ? `<button class="tb-btn ghost sm" data-develop="${h.id}">Develop to ${h.age + 1}YO</button>` : `<small>Fully developed</small>`)
      : `<small>${h.how === "bred" ? "Bred" : "Bought"} for ${money(h.cost)}</small>`}
    ${developable ? `<div class="${r ? "in" : ""}">${r ? "Entered: " + r.name : "Not entered"}</div>` : ""}</div>`;
}
/* ===== The animated horse card (backend/horseCard.web.js), in a frame beside the page ===== */
const VERDICT_KEYS = { "2YO flyer": ["flyer", "bolt"], "2YO ready": ["ready", "bolt"], "Future superstar": ["superstar", "star"], "Classy type": ["classy", "star"],
  "Future star": ["star", "star"], "Future stayer": ["stayer", "stay"], "Speedball": ["speed", "bolt"], "Late bloomer": ["bloomer", "up"], "Improver": ["improver", "up"], "Honest type": ["honest", "shield"] };
const dNames = d => d.map(i => DISTANCES[i]).join(", ");
function cardPayload(h, age) {
  age = age || h.age;
  // The card shows the horse as it is now: no projection, potential badge or future trips (players find out by developing)
  const rating = ratingAt(h, age), distance = dNames(tripAt(h, age)), pj = projected(h, age);
  return { sire: h.sire, dam: h.dam, age, rating, distance, ground: h.grounds.join(", "), drop: 5, projection: pj ? { rating: pj.rating, distance: dNames(pj.trip) } : null, range: [distance],
    outlook: { arrows: "", words: "" }, verdict: null,
    baseCardUrl: "img/base.webp", portraitUrl: `img/p${String(h.portrait || 1).padStart(2, "0")}.webp` };
}
let cardFrame = null, cardQueue = [], cardReady = false;
// lock the page while a card pop-up is open; a tap on the card skips its animation
new MutationObserver(() => document.body.classList.toggle("modal-open", !!document.querySelector(".foal-wrap"))).observe(document.body, { childList: true });
document.addEventListener("click", e => { if (e.target.closest && e.target.closest(".cardbox")) toCard({ type: "skip" }); });
function cardBox() {
  cardReady = false; cardQueue = [];
  return `<div class="cardbox"><iframe id="cardFrame" src="card.html" title="Horse card"></iframe></div>`;
}
function toCard(msg) { if (!cardReady || !cardFrame) { cardQueue.push(msg); return; } cardFrame.contentWindow.postMessage(msg, "*"); }
function wireCard() {
  cardFrame = document.getElementById("cardFrame");
  if (cardFrame) cardFrame.onload = () => { try { cardFrame.contentWindow.postMessage({ type: "hello" }, "*"); } catch (e) {} };
}
addEventListener("message", e => {
  if (!cardFrame || e.source !== cardFrame.contentWindow) return;
  const d = e.data || {};
  if (d.type === "ready" && !cardReady) { cardReady = true; const q = cardQueue; cardQueue = []; q.forEach(toCard); }
  if (d.type === "revealDone" || d.type === "developDone") { const f = cardFrame && cardFrame.closest(".foal"); if (f) f.classList.add("done"); }
});
function renderFoal() {
  let box = $("#foal");
  if (!S.foal) { if (box) box.remove(); return; }
  const F = S.foal, h = F.h;
  if (box && box.dataset.id === h.id) return;          // already showing this foal: leave the card playing
  if (box) box.remove();
  box = document.createElement("div"); box.id = "foal"; box.className = "foal-wrap"; box.dataset.id = h.id; document.body.appendChild(box);
  box.innerHTML = `<div class="foal" role="dialog" aria-label="Your new foal">${cardBox()}
    <div class="fc-in">
      <div class="fc-kicker">${F.how === "bred" ? "Born at the stud" : "Knocked down to you at Tattersalls"}</div>
      <div class="fc-sex ${h.sex}">${h.sex === "F" ? "♀ FILLY" : "♂ COLT"}</div>
      <label class="fc-name"><span>Name</span><input id="foalName" value="${esc2(h.name)}" maxlength="18" autocomplete="off"></label>
      <div class="fc-ped fc-wait">by <b>${esc2(h.sire)}</b> out of <b>${esc2(h.dam)}</b></div>
      <div class="fc-facts fc-wait"><span>Rated <b>${ratingAt(h, 2)}</b> as a 2YO</span><span>Best <b>${tripText(tripAt(h, 2))}</b></span><span>Likes <b>${h.grounds.join(", ")}</b></span><span>Projected peak <b>${h.peakAge}YO</b></span><span>Runs <b>${STYLE_NAME[h.style]}</b>, ${h.temper}</span><span><b>${FLEX_NAME[h.flex]}</b></span></div>
      <div class="fc-btns fc-wait fc-choose">${h.peakAge >= 3 ? `<button class="tb-btn" data-keepdev="${h.peakAge}">Develop to peak (${h.peakAge}YO)</button>` : ""}${h.peakAge === 4 ? `<button class="tb-btn ghost" data-keepdev="3">Develop to 3YO</button>` : ""}<button class="tb-btn ${h.peakAge >= 3 ? "ghost" : ""}" id="keep">${h.peakAge >= 3 ? "Save as a 2YO" : "Save to your stud farm"}</button>${agentButton(F)}</div>
      <p class="fc-small fc-wait">${h.peakAge >= 3 ? `Projected to peak at ${h.peakAge}. Develop now if it won't run as a 2-year-old, or keep it young: you can still develop it later. You only see the new rating once it's done.` : "Projected to peak as a 2-year-old: it's ready to race now."}</p>
      <p class="fc-small fc-wait">${F.how === "bred" ? `Stud fee ${money(F.cost)}. ${esc2(h.dam)} has been covered for this season.` : `Bought for ${money(F.cost)}.`}</p>
    </div></div>`;
  wireCard();
  toCard({ type: "reveal", horse: cardPayload(h, 2) });
  setTimeout(() => { const f = box.querySelector(".foal"); if (f) f.classList.add("done"); }, 9000);
}
// Develop: the card shows the horse now, then plays its develop animation
function showDevelop(h, fromAge) {
  const old = $("#devCard"); if (old) old.remove();
  const box = document.createElement("div"); box.id = "devCard"; box.className = "foal-wrap";
  box.innerHTML = `<div class="foal" role="dialog" aria-label="${esc2(h.name)} develops">${cardBox()}
    <div class="fc-in"><div class="fc-kicker">Developed</div><div class="fc-dev"><b>${esc2(h.name)}</b> is now a ${h.age}-year-old</div>
      <div class="fc-facts fc-wait"><span>Rated <b>${ratingAt(h, fromAge)} → ${ratingAt(h, h.age)}</b></span><span>Best trip <b>${tripText(tripAt(h, h.age))}</b></span></div>
      <div class="fc-btns fc-wait">${h.age < 4 ? `<button class="tb-btn ghost" data-develop="${h.id}">Develop again to ${h.age + 1}YO</button>` : ""}<button class="tb-btn" id="closeDev">Done</button></div></div></div>`;
  document.body.appendChild(box);
  wireCard();
  toCard({ type: "show", horse: cardPayload(h, fromAge), animate: false });
  setTimeout(() => toCard({ type: "develop", horse: cardPayload(h, h.age) }), 700);
  setTimeout(() => { const f = box.querySelector(".foal"); if (f) f.classList.add("done"); }, 8000);
}

/* ----- Step 2: develop and enter ----- */
function gradeBox(r) { const g = GRADE[r.grade]; return `<div class="grade ${g.cls}"><div><b>${g.short}</b>${r.dist}</div></div>`; }
// Who can run: age, and colts / fillies / open
const ageOnly = r => r.ageLabel.replace(/ (colts|fillies).*$/, "");
function sexTag(r) {
  const t = r.sex === "C" ? ["C", "♂", "Colts only"] : r.sex === "F" ? ["F", "♀", r.ages[0] >= 4 ? "Fillies & mares" : "Fillies only"] : ["O", "⚥", "Open"];
  return `<span class="sx ${t[0]}" title="${t[2]}"><i>${t[1]}</i>${t[2]}</span>`;
}
// The field's make-up, as dots, shown on race day only
function fieldDots(i) {
  const r = RACES[i], [lo, hi] = fieldRange(r);
  return `<span class="strength">rated ${lo}–${hi}</span>`;
}
function racesByDay(fn) {
  return DAYS.map((d, k) => `<section class="day"><div class="day-h"><h3>${d}</h3>${goingKnown() ? `<span class="gday g-${CARD.going[k]}">${CARD.going[k]}</span>` : ""}</div>
    <div class="races">${RACES.filter(r => r.day === k).map(fn).join("")}</div></section>`).join("");
}
/* ===== Horse cards ===== */
function whyNot(h, r) {
  if (h.age < r.ages[0]) return `Needs to be ${r.ages[0]}YO for this race`;
  if (h.age > r.ages[1]) return `Too old: ${r.ageLabel} only`;
  if (r.sex && h.sex !== r.sex) return r.sex === "F" ? "Fillies only" : "Colts only";
  return "";
}
// The projected peak: the peak rating rounded to the nearest 5, at the peak-age trip (as the card's potential line)
function projected(h, age) {
  age = age || h.age;
  if (age >= h.peakAge) return null;
  const rating = Math.max(ratingAt(h, age), Math.round(h.r[2] / 5) * 5), trip = h.d[2];
  return rating > ratingAt(h, age) || tripText(trip) !== tripText(tripAt(h, age)) ? { rating, trip } : null;
}
// Bars coloured as on the card: gold 120+, silver 110+, bronze 100+, slate below; the current best trip gets a gold edge and a diamond.
// The dotted line is the projected career path, drawn like the card's potential line.
const tierOf = v => v >= 120 ? "gold" : v >= 110 ? "silver" : v >= 100 ? "bronze" : "basic";
function profileHTML(h, race) {
  const best = tripAt(h, h.age), lo = Math.min(...best), hi = Math.max(...best), base = ratingAt(h, h.age);
  const step = i => i < lo ? lo - i : i > hi ? i - hi : 0;
  const pj = projected(h), top = Math.max(base, pj ? pj.rating : base), floor = top - 45;
  const pLo = pj ? Math.min(...pj.trip) : 0, pHi = pj ? Math.max(...pj.trip) : 0, pstep = i => i < pLo ? pLo - i : i > pHi ? i - pHi : 0;
  const pv = i => pj.rating - 5 * pstep(i), hy = v => 100 - Math.max(8, Math.min(100, (v - floor) / 45 * 100));
  let proj = "";
  if (pj) {
    const pts = DISTANCES.map((d, i) => [i * 10 + 5, hy(pv(i))]);
    let d = `M${pts[0][0]} ${pts[0][1].toFixed(1)}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
      d += ` C${(p1[0] + (p2[0] - p0[0]) / 6).toFixed(1)} ${(p1[1] + (p2[1] - p0[1]) / 6).toFixed(1)} ${(p2[0] - (p3[0] - p1[0]) / 6).toFixed(1)} ${(p2[1] - (p3[1] - p1[1]) / 6).toFixed(1)} ${p2[0]} ${p2[1].toFixed(1)}`;
    }
    proj = `<svg class="hp-proj" viewBox="0 0 90 100" preserveAspectRatio="none" aria-hidden="true"><path class="pf" d="${d} L85 100 L5 100Z"/><path class="pl" d="${d}"/></svg>`;
  }
  return `<div class="hp" role="img" aria-label="Rating by distance: best ${tripText(best)} at ${base}${pj ? `; projected peak at ${tripText(pj.trip)}` : ""}">${proj}${DISTANCES.map((d, i) => {
    const v = base - 5 * step(i), far = step(i) > 3, ht = Math.max(8, Math.round((v - floor) / 45 * 100)), isBest = !step(i);
    return `<div class="hp-c ${isBest ? "best" : ""} ${race && race.step === i ? "here" : ""} ${far ? "far" : ""}" style="--f:${(ht / 100).toFixed(3)}"><span class="hp-v">${far ? "" : v}</span><i class="t-${tierOf(v)}"></i><span class="hp-d">${d}</span></div>`;
  }).join("")}</div>`;
}
function targetBox(h, sel) {
  const T = S.targets || {}, mine = RACES.filter(r => T[r.id] === h.id), f = sel ? fitFor(h, sel) : null;
  const open = S.planOpen === h.id, room = open ? mine.length : sel && !f.no && T[sel.id] !== h.id ? 0 : 1, more = mine.length - room;
  const shown = more > 0 ? mine.slice(0, room) : mine;
  return `<div class="pl-slot ${open ? "open" : ""}" data-plandrop="${h.id}"><span class="pl-lbl">Targets</span>
    ${shown.map(r => `<span class="pl-t ${GRADE[r.grade].cls}" title="${esc2(r.name)}"><span class="pl-tn">${r.name.replace(/ Stakes$/, "")}</span><button data-unplan="${r.id}" aria-label="Remove ${r.name}">×</button></span>`).join("")}${more > 0 ? `<button class="pl-more" data-planmore="${h.id}" title="${esc2(mine.slice(room).map(r => r.name).join(", "))}">+${more}</button>` : open && mine.length > 1 ? `<button class="pl-more" data-planmore="${h.id}">Less</button>` : ""}
    ${sel ? (f.no ? `<span class="pl-fit">${f.t}: can't target</span>` : T[sel.id] === h.id ? "" : `<button class="pl-add ${f.ok ? "" : "later"}" data-plantarget="${h.id}" title="${esc2(f.t)}">+ ${sel.name.replace(/ Stakes$/, "")}${f.ok ? "" : " <small>not yet qualified</small>"}</button>`)
      : (mine.length ? "" : `<span class="pl-empty">drop a race here</span>`)}</div>`;
}
// Preferred ground as a small vertical gauge: Quick at the top, Heavy at the foot
function groundMeter(h, today) {
  const scale = GROUND_ORDER.slice().reverse();
  return `<div class="hc2-gm" title="Preferred ground: ${h.grounds.join(", ")}${today ? ` · race day: ${today}` : ""}" aria-label="Preferred ground: ${h.grounds.join(", ")}">
    <span class="gm-l"><b>Q</b><b>G</b><b>S</b></span>
    <span class="gm-bar">${scale.map(g => `<i class="g-${g} ${h.grounds.includes(g) ? "on" : ""} ${g === today ? "today" : ""}"></i>`).join("")}</span></div>`;
}
// Where else a horse is entered: the race it would have to come out of to run here, and (in the Newmarket season, where
// a horse runs at every meeting it qualifies for) its runs at the other meetings
function entryNote(h, race, inRace, here) {
  let s = inRace && !here ? `<div class="hk-in">Entered in the ${esc2(inRace.name)}${MEETING.runsPerMeeting ? " at this meeting" : ""}</div>` : "";
  if (MEETING.runsPerMeeting) {
    const also = runsOf(h).filter(x => (!race || x.id !== race.id) && (!inRace || x.id !== inRace.id));
    if (also.length) s += `<div class="hk-in">${race ? "Also runs in" : "Runs in"} the ${also.map(x => esc2(x.name)).join(", the ")}</div>`;
  }
  return s;
}
function hcard(h, race, canAct, opts) {
  const now = ratingAt(h, h.age), here = !!race && S.entries[race.id] === h.id, inRace = race ? clashFor(h, race) : runsOf(h)[0];
  let verdict = "", acts = "", cant = false;
  if (race) {
    const why = whyNot(h, race), c = why ? null : check(h, race);
    if (why || !c.ok) { cant = true; verdict = `<div class="hv no"><b>–</b><span>${esc2(why || c.why)}</span></div>`; }
    else verdict = `<div class="hv rk-${rkCls(c)}"><b>${c.day}</b><span>${rankText(c)}${c.steps ? ` · −${c.steps * 5} for the trip` : ""}${c.ground ? ` · ${c.ground > 0 ? "+" : "−"}${Math.abs(c.ground)} for the going` : ""}${teamNote(c)}</span></div>`;
    if (canAct) acts += here ? `<button class="tb-btn ghost" data-unpick="${race.id}">Take out</button>`
      : !cant ? `<button class="tb-btn" data-pick="${h.id}" data-race="${race.id}">${inRace ? "Move here" : "Enter"}</button>` : "";
  }
  if (canAct && h.age < 4 && !atAscot()) acts += `<button class="tb-btn ghost" data-develop="${h.id}">Develop to ${h.age + 1}YO</button>`;
  acts += `<button class="tb-btn ghost" data-card="${h.id}">Card</button>`;
  const today = race && goingKnown() ? CARD.going[race.day] : null;
  return `<article class="hk ${here ? "here" : ""} ${race && cant ? "cant" : ""}">
    <div class="hk-pic"><img class="por" src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt="">${silkImg(mySilkN())}
      <div class="hk-rate"><b>${now}</b><small>Rating</small></div>
      <div class="hk-chips"><span class="${h.sex}"><i>${h.sex === "F" ? "♀" : "♂"}</i>${h.sex === "F" ? "Filly" : "Colt"}</span><span>${h.age}YO</span></div></div>
    <div class="hk-body">
      ${race && (S.targets || {})[race.id] === h.id ? `<div class="hk-plan">★ Your planned runner for this race</div>` : ""}
      <div><h4 class="hk-name">${esc2(h.name)}</h4><div class="hk-ped">by ${esc2(h.sire)} out of ${esc2(h.dam)}</div></div>
      <div class="hk-track">${[2, 3, 4].map(a => `<span class="${a < h.age ? "past" : a === h.age ? "now" : ""}">${a}YO</span>`).join("")}<em>Projected peak ${h.peakAge}YO</em></div>
      ${profileHTML(h, race)}
      <div class="hk-ground" aria-label="Going it likes">${GROUND_ORDER.map(g => `<span class="${h.grounds.includes(g) ? "on g-" + g : ""} ${g === today ? "today" : ""}" ${g === today ? 'title="The going on race day"' : ""}>${g}</span>`).join("")}</div>
      ${verdict}
      ${opts && opts.plan ? targetBox(h, race) : ""}
      ${entryNote(h, race, inRace, here)}
      ${acts ? `<div class="hk-acts">${acts}</div>` : ""}
    </div></article>`;
}
function raceBoard(sel) {
  return `<div class="rb">${DAYS.map((d, k) => `<div class="rb-day"><h3>${d}</h3>${RACES.filter(r => r.day === k).map(r => {
    const h = horse(S.entries[r.id]), c = h && check(h, r), g = GRADE[r.grade];
    return `<button class="rb-r ${r.id === sel.id ? "on" : ""} ${h ? "has" : ""}" data-selrace="${r.id}" aria-pressed="${r.id === sel.id}">
      <span class="t"><span class="g ${g.cls}">${g.short}</span>${r.dist} · ${ageOnly(r)} <span class="sx-i ${r.sex || "O"}" title="${r.sex === "C" ? "Colts only" : r.sex === "F" ? "Fillies only" : "Open to colts and fillies"}">${r.sex === "C" ? "♂" : r.sex === "F" ? "♀" : "⚥"}</span></span><span class="n">${r.name}</span>
      <span class="w">${h ? `${c && c.ok ? `<i class="rk ${rkCls(c)}">${c.day}</i>` : ""}<em>${esc2(h.name)}</em>` : (S.targets || {})[r.id] && horse(S.targets[r.id]) ? `<span class="plan">Planned: ${esc2(horse(S.targets[r.id]).name)}</span>` : "No runner yet"}</span></button>`; }).join("")}</div>`).join("")}</div>`;
}
function showHorseCard(h) {
  const box = document.createElement("div"); box.id = "devCard"; box.className = "foal-wrap";
  box.addEventListener("click", e => { if (e.target === box) { box.remove(); cardFrame = null; } });
  box.innerHTML = `<div class="foal" role="dialog" aria-label="${esc2(h.name)}">${cardBox()}
    <div class="fc-in"><div class="fc-kicker">${h.age}-year-old ${sexWord(h)}</div><div class="fc-dev"><b>${esc2(h.name)}</b></div>
      <div class="fc-ped">by <b>${esc2(h.sire)}</b> out of <b>${esc2(h.dam)}</b></div>
      <div class="fc-facts"><span>Rated <b>${ratingAt(h, h.age)}</b></span><span>Best <b>${tripText(tripAt(h, h.age))}</b></span><span>Likes <b>${h.grounds.join(", ")}</b></span>${h.style ? `<span>Runs <b>${STYLE_NAME[h.style]}</b>, ${h.temper}</span><span><b>${FLEX_NAME[h.flex]}</b></span>` : ""}</div>
      <div class="fc-btns"><button class="tb-btn" id="closeDev">Done</button></div></div></div>`;
  document.body.appendChild(box);
  wireCard();
  toCard({ type: "show", horse: cardPayload(h, h.age), animate: true });
}
// Horses grouped by age (youngest first), best current rating first within each age
/* Compact horse card (after the Wix stables card): about half the screen wide */
function hcardC(h, race, canAct, opts) {
  const now = ratingAt(h, h.age), here = !!race && S.entries[race.id] === h.id, inRace = race ? clashFor(h, race) : runsOf(h)[0];
  let verdict = "", acts = "", cant = false;
  if (race) {
    const why = whyNot(h, race), c = why ? null : check(h, race);
    if (why || !c.ok) { cant = true; verdict = `<div class="hv no"><b>–</b><span>${esc2(why || c.why)}</span></div>`; }
    else verdict = `<div class="hv rk-${rkCls(c)}"><b>${c.day}</b><span>${rankText(c)}${c.steps ? ` · −${c.steps * 5} for the trip` : ""}${c.ground ? ` · ${c.ground > 0 ? "+" : "−"}${Math.abs(c.ground)} for the going` : ""}${teamNote(c)}</span></div>`;
    if (canAct) acts += here ? `<button class="tb-btn ghost" data-unpick="${race.id}">Take out</button>`
      : !cant ? `<button class="tb-btn" data-pick="${h.id}" data-race="${race.id}">${inRace ? "Move here" : "Enter"}</button>` : "";
  }
  if (canAct && h.age < 4 && !atAscot()) acts += `<button class="tb-btn ghost" data-develop="${h.id}">Develop to ${h.age + 1}YO</button>`;
  const today = race && goingKnown() ? CARD.going[race.day] : null, planned = race && (S.targets || {})[race.id] === h.id;
  return `<article class="hc2 ${here ? "here" : ""} ${race && cant ? "cant" : ""}" ${opts && opts.plan ? `data-plandrop="${h.id}"` : ""}>
    <div class="hc2-pic"><img src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt=""></div>
    <div class="hc2-id">
      <div class="hc2-top"><div class="hc2-nm"><h4 class="${h.name.length > 17 ? "lng" : ""}">${esc2(h.name)}</h4><div class="hc2-ped">${esc2(h.sire)} × ${esc2(h.dam)}</div></div><div class="hc2-rate"><b>${now}</b><small>Rating</small></div></div>
      <div class="hc2-bot">
        <div class="hc2-info">
          <div class="hc2-chips"><span class="c-sex ${h.sex}">${h.sex === "F" ? "♀ Filly" : "♂ Colt"}</span><span class="c-trip">${tripText(tripAt(h, h.age))}</span>${h.style ? `<span class="c-style" title="Running style${h.flex ? ": " + FLEX_NAME[h.flex].toLowerCase() : ""}">${styleTag(h)}</span>` : ""}</div>
          <div class="hc2-age"><div class="hc2-track">${[2, 3, 4].map(a => `<span class="${a < h.age ? "past" : a === h.age ? "now" : ""} ${a === h.peakAge ? "pk" : ""}">${a}YO</span>`).join("")}</div><em><span class="lg">Projected </span>peak ${h.peakAge}YO</em></div>
        </div>
        ${groundMeter(h, today)}
      </div>
    </div>
    <div class="hc2-prof">${profileHTML(h, race)}</div>
    <div class="hc2-foot">
      ${planned ? `<div class="hk-plan">★ Your planned runner for this race</div>` : ""}
      ${verdict}
      ${opts && opts.plan ? "" : entryNote(h, race, inRace, here)}
      ${opts && opts.train ? jobStrip(h) : ""}
      ${acts ? `<div class="hc2-acts">${acts}</div>` : ""}
      <div class="hc2-end">${opts && opts.plan ? targetBox(h, race) : "<span></span>"}<button class="hc2-card" data-card="${h.id}">Card</button></div>
    </div></article>`;
}
// Two columns, colts and fillies; youngest first, best first within each age; a race's planned runner leads its age
function horseCols(list, race, canAct, opts, splitEntered) {
  // "Already entered": entered here, or in a race that rules this one out (any other race at Royal Ascot; the same meeting at Newmarket)
  const taken = h => (race ? S.entries[race.id] === h.id || !!clashFor(h, race) : Object.values(S.entries).includes(h.id));
  const rest = splitEntered ? list.filter(taken) : [];
  if (splitEntered) list = list.filter(h => !taken(h));
  const planned = h => race && (S.targets || {})[race.id] === h.id ? 1 : 0;
  const order = a => a.slice().sort((x, y) => x.age - y.age || planned(y) - planned(x) || ratingAt(y, y.age) - ratingAt(x, x.age) || x.name.localeCompare(y.name));
  const col = (hs, sx) => { let lastAge = 0; const items = order(hs.filter(h => h.sex === sx)).map(h => { const sub = h.age !== lastAge ? `<div class="hk-sub">${h.age}-year-old${h.sex === "F" ? " fillies" : " colts"}</div>` : ""; lastAge = h.age; return sub + hcardC(h, race, canAct, opts); }).join("");
    return `<div class="hk-col"><h3 class="hk-age">${sx === "C" ? "♂ Colts" : "♀ Fillies"}<span>${hs.filter(h => h.sex === sx).length}</span></h3>${items || `<p class="tb-empty">None yet.</p>`}</div>`; };
  return `<div class="hk-cols">${col(list, "C")}${col(list, "F")}</div>` +
    (rest.length ? `<div class="hk-group-entered"><h3 class="hk-age">Already entered<span>${rest.length}</span></h3><div class="hk-cols">${col(rest, "C")}${col(rest, "F")}</div></div>` : "");
}
function cardGroups(list, race, canAct, splitEntered, opts) {
  const taken = h => (race ? S.entries[race.id] === h.id || !!clashFor(h, race) : Object.values(S.entries).includes(h.id));
  const rest = splitEntered ? list.filter(taken) : [];
  if (splitEntered) list = list.filter(h => !taken(h));
  const sortAb = a => a.slice().sort((x, y) => ratingAt(y, y.age) - ratingAt(x, x.age) || x.name.localeCompare(y.name));
  return [2, 3, 4].map(a => {
    const planned = h => race && (S.targets || {})[race.id] === h.id ? 1 : 0;
    const hs = list.filter(h => h.age === a).sort((x, y) => planned(y) - planned(x) || ratingAt(y, y.age) - ratingAt(x, x.age) || x.name.localeCompare(y.name));
    return hs.length ? `<h3 class="hk-age">${a}-year-olds<span>${hs.length}</span></h3><div class="hk-grid">${hs.map(h => hcard(h, race, canAct, opts)).join("")}</div>` : "";
  }).join("") + (rest.length ? `<div class="hk-group-entered"><h3 class="hk-age">Already entered<span>${rest.length}</span></h3><div class="hk-grid">${sortAb(rest).map(h => hcard(h, race, canAct, opts)).join("")}</div></div>` : "");
}
function entriesBody(entered) {
  const sel = RACES.find(r => r.id === S.selRace) || RACES.find(r => !S.entries[r.id]) || RACES[0]; S.selRace = sel.id;
  const C = CARD.races[sel.i];
  const score = h => { const c = whyNot(h, sel) ? null : check(h, sel); return c && c.ok ? 1000 + c.day : ratingAt(h, h.age); };
  const hs = S.stable.slice().sort((a, b) => (S.entries[sel.id] === b.id) - (S.entries[sel.id] === a.id) || score(b) - score(a));
  return `<div class="tb-head"><h1 class="tb-h">DEVELOP AND ENTER</h1>
    <p class="tb-lede">Pick a race, then enter a horse. Every horse starts as a 2-year-old: develop it to 3 or 4 to change its rating and best trip, though you only see how once it's done, and there's no going back. ${W.entryRule}; each step from its best trip costs 5 points, and every race has a minimum rating. Each horse shows where its rating sits in the field.</p></div>
    <div class="tb-bar"><div class="tb-bar-info ${entered === RACES.length ? "ready" : ""}">${entered === RACES.length ? `All ${RACES.length} races have a runner.` : `${RACES.length - entered} race${RACES.length - entered === 1 ? "" : "s"} still without a runner. An empty race counts as a loss.`}</div>
    <div class="tb-bar-btns"><button class="tb-btn ghost" id="fill">Fill empty races</button><button class="tb-btn ghost" id="clear">Clear</button></div></div>
    ${teamAtEntries()}
    ${raceBoard(sel)}
    <div class="rsel">${gradeBox(sel)}<div class="rsel-in" style="min-width:0;flex:1 1 auto"><h3>${sel.name}</h3>
      <div class="facts"><span><b>${DAYS[sel.day]}</b></span>${courseName(sel) ? `<span>${courseName(sel)}</span>` : ""}<span><b>${ageOnly(sel)}</b></span>${sexTag(sel)}<span>1st <b>${money(sel.prizes[0])}</b></span>${sel.grade === "Handicap" ? `<span>Max rating <b>${HCAP_MAX}</b></span>` : ""}</div>
      ${bandsLine(sel)}
      ${(() => { const h = horse(S.entries[sel.id]), c = h && check(h, sel); return h ? `<div class="rsel-run">Your runner: ${silkImg(mySilkN())}<b>${esc2(h.name)}</b>${c && c.ok ? rkChip(c) + `<small class="rk-t">${rankText(c)}</small>` : ""}<button class="tb-btn ghost sm" data-unpick="${sel.id}">Take out</button></div>` : `<div class="rsel-run" style="color:var(--tb-muted)">No runner yet: pick one below.</div>`; })()}${jockeyPick(sel)}</div></div>
    ${hs.length ? horseCols(hs, sel, true, null, true) : `<p class="tb-empty">No horses yet.</p>`}`;
}
function entryCard(r) {
  const id = S.entries[r.id], h = id && horse(id), c = h && check(h, r), open = S.open === r.id;
  return `<article class="race ${open ? "open" : ""}" id="race-${r.id}">
    <div class="race-top">${gradeBox(r)}
      <div style="min-width:0"><h4 class="race-name">${r.name}</h4>
        <div class="facts"><span><b>${ageOnly(r)}</b></span>${sexTag(r)}<span>1st <b>${money(r.prizes[0])}</b></span>${r.grade === "Handicap" ? `<span>Max rating <b>${HCAP_MAX}</b></span>` : ""}</div>
        ${bandsLine(r)}
      </div>
      <div class="entry"><button class="slot ${h ? "filled" : ""}" data-open="${r.id}" aria-expanded="${open}">
        ${h ? `${silkImg(mySilkN())}<span class="nm">${esc2(h.name)}</span>${rkChip(c)}` : "Choose a horse ▾"}</button></div>
    </div>${open ? picker(r) : ""}</article>`;
}
function picker(r) {
  const rows = S.stable.map(h => ({ h, c: check(h, r) })).filter(x => !x.c.hidden)
    .sort((a, b) => (b.c.ok ? 1 : 0) - (a.c.ok ? 1 : 0) || (b.c.day || b.c.eff || 0) - (a.c.day || a.c.eff || 0));
  if (!rows.length) return `<div class="picker"><p>None of your horses can run in this race (${r.ageLabel}). Develop a horse to the right age, or breed more.</p></div>`;
  const usedIn = h => clashFor(h, r);
  return `<div class="picker"><p>${r.ageLabel}, ${r.dist}.</p><div class="opts">
    ${rows.map(({ h, c }) => { const u = usedIn(h), sel = S.entries[r.id] === h.id;
      return `<button class="opt ${sel ? "sel" : ""}" data-pick="${h.id}" data-race="${r.id}" ${c.ok ? "" : "disabled"}>
        ${c.ok ? rkChip(c) : `<span class="deck none">Can't run</span>`}
        <span class="who"><b>${esc2(h.name)}</b><small>${h.age}yo ${sexWord(h)} · best ${tripText(tripAt(h, h.age))} · likes ${h.grounds.join("/")}
          ${c.steps ? ` · <span class="note">trip −${c.steps * 5}</span>` : ""}${c.ok ? (c.suits ? ` · <span class="ok">suits the going</span>` : "") : ` · <span class="note">${c.why}</span>`}
          ${u ? ` · <span class="note">entered in the ${u.name}</span>` : ""}${sel ? ` · <span class="ok">entered here</span>` : ""}</small></span>
        <span class="rt">${c.eff != null ? c.eff : "–"}<small>RATED</small></span></button>`; }).join("")}
    ${S.entries[r.id] ? `<button class="tb-btn ghost sm" data-unpick="${r.id}" style="justify-self:start">Take out of this race</button>` : ""}
  </div></div>`;
}
function setEntry(raceId, horseId) {
  const race = RACES.find(x => x.id === raceId);
  RACES.forEach(x => { if (S.entries[x.id] === horseId && (!race || x.id === raceId || clashes(x, race))) delete S.entries[x.id]; });
  if (horseId) S.entries[raceId] = horseId; else delete S.entries[raceId];
  save();
}
function fillEmpty() {
  // a horse is free for a race if it isn't entered in one that rules it out (any other race at Royal Ascot; the same meeting at Newmarket)
  const options = r => S.stable.filter(h => !clashFor(h, r) && check(h, r).ok);
  RACES.filter(r => !S.entries[r.id]).forEach(r => { const t = (S.targets || {})[r.id], ht = t && horse(t); if (ht && !clashFor(ht, r) && check(ht, r).ok) S.entries[r.id] = t; });
  RACES.filter(r => !S.entries[r.id]).sort((a, b) => options(a).length - options(b).length).forEach(r => {
    const best = options(r).sort((a, b) => check(b, r).day - check(a, r).day)[0]; if (best) S.entries[r.id] = best.id;
  });
  save();
  const left = RACES.filter(r => !S.entries[r.id]).length;
  toast(left ? `${left} race${left === 1 ? "" : "s"} still empty: no free horse can run at its current age` : "Every race has a runner");
}

/* ----- Step 3: race week ----- */
function weekBody(done) {
  setTimeout(() => { if (!S.goingShown) { S.goingShown = true; save(); } }, 50);
  return `<div class="tb-head"><h1 class="tb-h">${W.weekHead}</h1>
    <p class="tb-lede">${W.watchHere}, or sim it for the result straight away. Both run the very same race. The pace forecast comes from the runners' racecards: lots of front-runners make a fast race that suits horses held up, and a race with none will be slow and tactical.</p></div>
    <div class="going-dec ${S.goingShown ? "" : "fresh"}"><b>THE GOING IS DECLARED</b><div class="gd-days">${DAYS.map((d, k) => `<div class="gd" style="--d:${k * 260}ms"><small>${dayTag(k)}</small><span class="gday g-${CARD.going[k]}">${CARD.going[k]}</span></div>`).join("")}</div>
      <p>${(() => { const mine = RACES.filter(r => S.entries[r.id]), liked = mine.filter(r => horse(S.entries[r.id]).grounds.includes(CARD.going[r.day])).length; return mine.length ? `${liked} of your ${mine.length} runners like the ground they'll get.` : ""; })()}</p></div>
    ${typeof weekJobs === "function" ? weekJobs() : ""}
    <div class="tb-bar"><div class="tb-bar-info ${done === RACES.length ? "ready" : ""}">${done === RACES.length ? `All ${RACES.length} races run.` : `${done} of ${RACES.length} races run.`}</div>
    <div class="tb-bar-btns"><button class="tb-btn ghost" id="backEntries" ${done ? "disabled" : ""} title="${done ? "Entries are closed once the first race is run" : "Change your runners before the first race"}">Change entries</button></div></div>
    ${racesByDay(weekCard)}`;
}
let simBusy = false;
const PACE_WORD = { slow: "Slow", even: "Even", strong: "Strong", fast: "Fast" };
// What the forecast means for your horse's running style
function paceNote(pace, h) {
  if (!h || !h.style) return "";
  const back = h.style === "holdup" || h.style === "midfield", front = h.style === "front" || h.style === "prominent";
  if ((pace === "fast" || pace === "strong") && back) return `should suit your ${STYLE_NAME[h.style].toLowerCase()} horse`;
  if (pace === "fast" && front) return `tough for your ${STYLE_NAME[h.style].toLowerCase()} horse`;
  if (pace === "slow" && front) return `should suit your ${STYLE_NAME[h.style].toLowerCase()} horse`;
  if (pace === "slow" && h.style === "holdup") return "could leave your hold-up horse too much to do";
  return "";
}
function weekCard(r) {
  const id = S.entries[r.id], h = id && horse(id), c = h && check(h, r), res = S.results[r.id], next = RACES.find(x => !S.results[x.id]);
  let right;
  if (res) {
    const cls = res.pos === 1 ? "win" : res.pos >= 2 && res.pos <= 3 ? "placed" : "lost";
    const how = res.time == null ? (res.pos === 1 ? "" : "Won by " + esc2(res.winner))
      : res.pos === 1 ? `Won by ${lengthsText(res.by)}` : res.pos ? `Beaten ${lengthsText(res.beaten)} by ${esc2(res.winner)}` : `Won by ${esc2(res.winner)}`;
    right = `<div class="res"><div class="prize">${res.pos ? (res.prize ? money(res.prize) : "No prize") : "No runner"}<br>${how}</div>
      <div class="pos ${cls}">${res.pos ? ord(res.pos) : "–"}</div><button class="tb-btn ghost sm" data-watch="${r.i}">Replay</button></div>`;
  } else right = `<div class="res"><button class="tb-btn sm" data-watch="${r.i}" ${next === r && !simBusy ? "" : "disabled"} title="Watch it run in 3D">Watch in 3D</button><button class="tb-btn ghost sm" data-sim="${r.i}" ${next === r && !simBusy ? "" : "disabled"} title="The result straight away: the very same race">Sim</button></div>`;
  const pf = paceFor(r.i), note = pf && paceNote(pf.pace, h);
  const forecast = pf ? `<div class="pacef pf-${pf.pace}"><b>Pace forecast: ${PACE_WORD[pf.pace]}</b><span>${pf.front} front-runner${pf.front === 1 ? "" : "s"} in ${pf.n}${note ? ` · ${note}` : ""}</span></div>` : "";
  const report = res && res.report ? `<details class="rep"><summary>Race report · ${res.time.toFixed(2)}s · ${PACE_WORD[res.pace] || ""} pace</summary><ul>${res.report.map(t => `<li>${esc2(t)}</li>`).join("")}</ul></details>` : "";
  return `<article class="race"><div class="race-top">${gradeBox(r)}
    <div style="min-width:0"><h4 class="race-name">${r.name}</h4>
      <div class="facts">${h && c.ok ? `<span class="mine">${silkImg(mySilkN())}<b>${esc2(h.name)}</b> ${rkChip(c)}<small class="rk-t">${rankText(c)}${h.style ? " · " + styleTag(h) : ""}${bookedFor(r) ? ` · ridden by ${cardName(bookedFor(r))}` : ""}${teamNote(c)}</small></span>` : `<span class="note">No runner</span>`}<span>${CARD.races[r.i].opp.length + (h ? 1 : 0)} runners</span>${fieldDots(r.i)}</div>
      ${res ? "" : forecast}
    </div>${right}</div>${report}</article>`;
}

/* ----- Step 4: result ----- */
// The final standings: race by race, your prize money climbs the ladder of titles
function resultBody(wins, losses, prize) {
  const complete = Object.keys(S.results).length === RACES.length;
  if (complete) { noteWeek(prize, wins); addWeek(prize, wins); noteDaily(prize, wins); }
  const spent = startBudget() - S.budget, T = titleFor(prize), rungs = TITLES.slice().reverse();
  const pct = v => Math.min(100, v / LADDER_TOP * 100);
  const rows = RACES.map((r, k) => { const res = S.results[r.id], h = horse(S.entries[r.id]);
    return `<li class="tr" data-k="${k}"><span class="tr-d">${dayTag(r.day)}</span><span class="tr-p ${res && res.pos === 1 ? "win" : res && res.pos >= 2 && res.pos <= 4 ? "pl" : ""}">${res && res.pos ? ord(res.pos) : "–"}</span>
      <span class="tr-n"><b>${r.name}</b><small>${h ? esc2(h.name) : "No runner"}${bookedFor(r) ? ` · ${cardName(bookedFor(r))}` : ""}</small></span><span class="tr-m">${res && res.prize ? "+" + money(res.prize) : ""}</span></li>`; }).join("")
;
  const hist = pastWeeks().slice().sort((a, b) => b.prize - a.prize), counts = {}; hist.forEach(w => counts[w.title] = (counts[w.title] || 0) + 1);
  const rank = hist.findIndex(w => w.seed === S.seed && w.prize === prize) + 1;
  return `<div class="tb-head"><h1 class="tb-h">FINAL STANDINGS</h1>
      <p class="tb-lede">${seasonName()} · ${wins} win${wins === 1 ? "" : "s"} from ${RACES.length} races · ${S.stable.length} horses · budget spent ${money(spent)} (a separate pot)</p></div>
    <div class="fs">
      <div class="fs-ladder" aria-hidden="true"><div class="fs-track"><div class="fs-fill" id="fsFill"></div>
        ${rungs.slice(1).map(t => `<div class="fs-rung ${t.cls}" id="rung-${t.cls}" style="--at:${pct(t.min)}%"><i></i><span><b>${t.name}</b>${money(t.min)}</span></div>`).join("")}</div></div>
      <div class="fs-main">
        <div class="fs-pot"><span>Prize money</span><b id="fsPot">${money(prize)}</b></div>
        <div class="fs-pop" id="fsPop"></div>
        <ol class="fs-rows" id="fsRows">${rows}</ol>
        <div class="title-won ${T.cls}" id="fsTitle"><span>Your title</span><b>${T.name}</b><small>${T.note} ${(() => { const nx = TITLES.slice().reverse().find(t => t.min > prize); return nx ? `${money(nx.min - prize)} short of ${nx.name}.` : ""; })()}</small></div>
        <p class="lb-line" id="lbLine" aria-live="polite"></p>
        <div class="fs-btns"><button class="tb-btn ghost" id="replayTally">Replay the tally</button><button class="tb-btn" id="copy">Copy result</button></div>
        <pre class="share" id="shareText" hidden>${shareText(wins, losses)}</pre>
      </div>
    </div>
    <section class="rec"><h2 class="tb-h2">${W.playedPlural}</h2>
      <div class="rec-titles">${TITLES.map(t => `<div class="rt ${t.cls} ${counts[t.name] ? "got" : ""}"><b>${counts[t.name] ? "×" + counts[t.name] : "?"}</b><span>${t.name}</span></div>`).join("")}</div>
      ${hist.length ? `<table class="rec-t"><thead><tr><th>#</th><th>Card</th><th>Prize money</th><th>Wins</th><th>Title</th></tr></thead><tbody>${hist.slice(0, 10).map((w, k) =>
        `<tr class="${w.seed === S.seed && w.prize === prize ? "me" : ""}"><td>${k + 1}</td><td>${w.day ? "Daily, " + dayText(w.day) : w.seed}</td><td><b>${money(w.prize)}</b></td><td>${w.wins}/${w.races}</td><td>${w.title}</td></tr>`).join("")}</tbody></table>
      <p class="rec-n">${hist.length} ${MEETING.id === "royal-ascot" ? "week" : "season"}${hist.length === 1 ? "" : "s"} played${rank ? ` · this one ranks <b>${ord(rank)}</b>` : ""}. Collect every title.</p>` : ""}
    </section>`;
}
function resultAfter(prize) {
  if (window.lbResult) lbResult();   // where this game stands on the leaderboard
  if (Object.keys(S.results).length === RACES.length && !S.tallied) { S.tallied = true; save(); playTally(); } else finishTally(prize);
}
let tallyRun = 0;
function setFill(v) { const f = $("#fsFill"); if (!f) return; const p = Math.min(100, v / LADDER_TOP * 100) + "%"; f.style.height = p; f.style.setProperty("--w", p); }
function finishTally(prize) {
  setFill(prize);
  $("#fsPot").textContent = money(prize);
  document.querySelectorAll(".fs-rows .tr").forEach(r => r.classList.add("in"));
  TITLES.forEach(t => { const g = $("#rung-" + t.cls); if (g && prize >= t.min) g.classList.add("hit"); });
  $("#fsTitle").classList.add("in");
}
function playTally() {
  const run = ++tallyRun, rows = [...document.querySelectorAll(".fs-rows .tr")], fill = $("#fsFill"), pot = $("#fsPot"), pop = $("#fsPop");
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { const p = RACES.reduce((a, r) => a + (S.results[r.id] ? S.results[r.id].prize : 0), 0) + teamIncome(); return finishTally(p); }
  let total = 0, k = 0;
  fill.style.transition = "none"; setFill(0); pot.textContent = money(0);
  rows.forEach(r => r.classList.remove("in")); $("#fsTitle").classList.remove("in"); document.querySelectorAll(".fs-rung").forEach(g => g.classList.remove("hit"));
  const step = () => {
    if (run !== tallyRun || !document.body.contains(fill)) return;
    if (k >= rows.length) { setTimeout(() => { if (run === tallyRun) $("#fsTitle").classList.add("in"); }, 300); return; }
    const r = RACES[k], res = r && S.results[r.id], add = r ? (res && res.prize ? res.prize : 0) : teamIncome(), from = total, to = total + add, row = rows[k];
    row.classList.add("in"); row.scrollIntoView({ block: "nearest", behavior: "smooth" });
    if (!add) { k++; return setTimeout(step, 380); }
    row.classList.add("pay");
    const t0 = performance.now(), dur = 700 + Math.min(900, add / 500);
    const tick = now => {
      if (run !== tallyRun) return;
      const e = Math.min(1, (now - t0) / dur), v = from + (to - from) * (1 - Math.pow(1 - e, 3));
      pot.textContent = money(Math.round(v / 1000) * 1000); fill.style.transition = "none"; setFill(v);
      TITLES.forEach(t => { const g = $("#rung-" + t.cls); if (t.min > 0 && g && v >= t.min && !g.classList.contains("hit")) { g.classList.add("hit"); pop.innerHTML = `<b>${t.name}</b>`; pop.className = "fs-pop show " + t.cls; } });
      if (e < 1) requestAnimationFrame(tick); else { total = to; k++; setTimeout(step, 420); }
    };
    requestAnimationFrame(tick);
  };
  setTimeout(step, 500);
}

function shareText(wins, losses) {
  const grid = DAYS.map((d, k) => RACES.filter(r => r.day === k).map(r => { const p = S.results[r.id] ? S.results[r.id].pos : 0; return p === 1 ? "🟩" : p >= 2 && p <= 3 ? "🟨" : "⬜"; }).join("")).join("\n");
  const prize = RACES.reduce((a, r) => a + (S.results[r.id] ? S.results[r.id].prize : 0), 0);
  return `Thoroughbred ${W.gameTitle} · ${seasonName(S, true)}\n${titleFor(prize).name}\n${grid}\nPrize money ${money(prize)} · ${wins}–${losses}`;
}

/* ================= Watching a race: the 3D race view (Final Furlong) ================= */
// The view runs the race engine on exactly the racecards and race it's handed here, so it shows the result Sim gives.
let watching = null;
function watch(i) {
  const race = RACES[i], C = CARD.races[i], box = document.createElement("div");
  if (!window.ENGINE) { toast("The race engine is still loading. Try again in a moment."); return; }
  const field = fieldFor(i);
  box.className = "watch";
  // the race view's diagnostics: the game opened as …#debug (or ?debug=1) opens every race with them showing
  const dbg = location.hash === "#debug" || /[?&]debug=1\b/.test(location.search) ? "&debug=1" : "";
  // (the day's going is on the address too: the race view's weather is chosen from it as the page opens, before the race arrives)
  box.innerHTML = `<iframe src="final-furlong.html?game=1&going=${encodeURIComponent(CARD.going[race.day])}${dbg}${window.__watchQuery || ""}" title="${esc2(race.name)}" allow="fullscreen"></iframe><button class="tb-btn ghost x" id="closeWatch"><span class="lg">Back to the racecard</span><span class="sh">Racecard</span></button>`;
  document.body.appendChild(box); document.body.style.overflow = "hidden";
  document.body.classList.add("watching");      // everything under the race is hidden and the board's loop rests (css/game.css)
  if (window.BOARD) BOARD.Sound.hush(true);     // and its sounds: the race view has its own crowd and horses
  const frame = box.querySelector("iframe");
  watching = { i, box, frame, sent: false };
  watching.timer = setTimeout(() => { if (watching && !watching.sent) {
    const m = document.createElement("div"); m.className = "msg";
    m.innerHTML = `<p style="margin:0 0 12px">The race view didn't load here. You can sim the race instead.</p><button class="tb-btn" id="simInstead">Sim the race</button>`;
    box.appendChild(m); } }, 15000);
  const er = engineRace(i), mkt = marketFor(i);
  // the race's own course (the Newmarket season races on the Rowley Mile and the July Course); at Newmarket the panels
  // name the meeting and the course rather than a day
  watching.payload = { type: "race", course: courseFile(race), race: viewKey(race), going: er.going, seed: er.seed, title: race.name,
    sound: !!(window.BOARD && BOARD.Sound.on),   // the game's Sound setting: the race view's crowd and horses follow it
    kicker: MEETING.courses ? `${DAYS[race.day]} · ${courseName(race)} · Race ${i + 1} of ${RACES.length}` : `${DAYS[race.day]} · Race ${i + 1} of ${RACES.length} · ${race.grade}`,
    // for the view's own racecard and result panels (game mode): the race's conditions and prizes, your colours
    card: { grade: race.grade, dist: race.dist, day: DAYS[race.day], meeting: MEETING.courses ? `${DAYS[race.day]}, ${courseName(race)}` : MEETING.name, prizes: race.prizes, conditions: race.ageLabel, next: i + 1 < RACES.length && !S.results[RACES[i + 1].id] ? RACES[i + 1].name : "", silkImg: mySilks().img },
    // and, for the dock and the racecard: the owner's own graphic silks, the price and the race-day colour card
    runners: field.map((h, k) => ({ ...engineRunner(h), ...(h.mine && MY ? { silk: "own", silkSpec: MY.spec, silk2d: MY.img } : { silk: SILK3D[h.sk], silk2d: SILKS[h.sk].img }), odds: mkt[k].odds, card: mkt[k].card, coat: { body: h.coat[0], points: h.coat[1] }, mine: !!h.mine })) };
}
function closeWatch() {
  if (!watching) return; clearTimeout(watching.timer);
  try { watching.frame.contentWindow.__soundStop && watching.frame.contentWindow.__soundStop(); } catch (e) {}
  if (window.BOARD) BOARD.Sound.hush(false);
  watching.box.remove(); watching = null; document.body.style.overflow = ""; document.body.classList.remove("watching"); render(); }
// D shows or hides the race view's diagnostics (frame rate, draw calls, triangles, pixel ratio) while a race is on
addEventListener("keydown", e => {
  if (watching && (e.key === "d" || e.key === "D") && !e.metaKey && !e.ctrlKey && !e.altKey) watching.frame.contentWindow.postMessage({ type: "diag" }, "*");
});
addEventListener("message", e => {
  if (!watching || e.source !== watching.frame.contentWindow) return;
  const d = e.data || {};
  // the race is sent every time the view says it's ready (if the view reloads itself it gets the race again)
  if (d.type === "ready") {
    watching.sent = true; clearTimeout(watching.timer);
    const m = watching.box.querySelector(".msg"); if (m) m.remove();     // it loaded late: the race goes on after all
    watching.frame.contentWindow.postMessage(watching.payload, "*");
  }
  if (d.type === "finished") { const i = watching.i; simAndRecord(i).then(() => { if (typeof raceDone === "function") raceDone(i, true); }).catch(err => toast(String(err.message || err))); }
  if (d.type === "back") closeWatch();
  // the race view's speaker changes the game's own Sound setting (and its button on the top bar)
  if (d.type === "sound" && window.BOARD && BOARD.Sound.on !== !!d.on) {
    BOARD.Sound.set(!!d.on);
    const b = $("#snd"), ic = $("#sndIcon");
    if (b) b.setAttribute("aria-pressed", String(!!d.on)); if (ic && window.ICON) ic.innerHTML = d.on ? ICON.speaker : ICON["speaker-off"];
  }
  if (d.type === "next") { const i = watching.i; closeWatch(); const nx = RACES[i + 1]; if (nx && !S.results[nx.id]) watch(i + 1); }
});

/* ================= Tattersalls: live auction against rival buyers ================= */
// Rival buyers (invented). want = how much they'll stretch for this kind of lot; keen = chance they take an interest at all.
let A = null;   // the auction in progress
function openAuction(id) {
  const l = S.sale.find(x => x.id === id); if (!l || A || S.step < 2 || S.step > 3 || S.foal || stableFull()) return;
  // who is interested in this lot and how far each will go is this game's own luck (fixed once the game is dealt, so
  // leaving the page and coming back can't change it); how long they hesitate before each bid is left to chance
  const rnd = luck("ring|" + l.sire + "|" + l.dam), ap = appeal(l, rnd);
  const rivals = RIVALS.map(r => ({ ...r, ceil: rnd() < r.keen(l) ? l.reserve * ap * r.want(l) * (.7 + rnd() * .9) : 0, wait: null }));
  A = { rnd, l, price: null, leader: null, start: performance.now(), last: performance.now(), rivals, log: [], call: -1, done: false, auto: 0, autoOn: false, ang: Math.random() * 6.28 };
  A.auto = Math.min(S.budget, round5k(guide(l)[0]));
  S.ring = l.id; save();   // the lot is in the ring: leave the page now and it has gone when you come back (no going back)
  const box = document.createElement("div"); box.className = "auc"; box.id = "auc"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", `Tattersalls, lot ${l.n}`);
  box.innerHTML = aucHTML(); document.body.appendChild(box); document.body.style.overflow = "hidden";
  A.box = box; aucPaint(); A.timer = setInterval(aucTick, 100); A.raf = requestAnimationFrame(aucWalk);
}
function aucHTML() {
  const l = A.l, s = stallion(l.sire), m = byName(l.dam), ln = lineNote(s, m), b = BOOKS.find(x => x.n === l.book);
  const seat = r => `<div class="seat" id="seat-${r.id}" style="left:${r.seat[0]}%;top:${r.seat[1]}%;--c:${r.c}"><span class="seat-bub"></span><span class="seat-dot"></span><span class="seat-tag">${esc2(r.name.split(" ")[0])}</span></div>`;
  return `<div class="auc-scene"><div class="auc-img" role="img" aria-label="The Tattersalls sale ring from above"></div>
      <div class="auc-board" aria-hidden="true"><div class="ab-l">LOT ${l.n} · BOOK ${l.book}</div><div class="ab-p" id="abP">—</div><div class="ab-w" id="abW">OPENING</div></div>
      <div class="auc-lot" id="aucLot" aria-hidden="true">LOT ${l.n}</div>
      <svg class="auc-clock" id="aucClock" viewBox="0 0 100 100" aria-hidden="true"><circle class="track" cx="50" cy="50" r="44"/><circle class="arc" id="abArc" cx="50" cy="50" r="44" stroke-dasharray="276.5" stroke-dashoffset="276.5"/></svg>
      <div class="auc-call" id="aucCall" aria-live="assertive"></div>
      ${A.rivals.map(seat).join("")}
      <div class="seat me" id="seat-me" style="left:${ME_SEAT[0]}%;top:${ME_SEAT[1]}%"><span class="seat-bub"></span>${silkImg(mySilkN())}<span class="tri"></span></div>
    </div>
    <div class="auc-panel">
      <div class="auc-top"><h2 class="auc-h">Lot ${l.n}</h2><div class="auc-k">TATTERSALLS · ${b.name.toUpperCase()}</div></div>
      <div class="auc-ped">
        <div class="pc s"><span class="pc-l">S</span><div><b>${esc2(s.name)}</b>${knowsTrue(s.name) ? pips(s.trueStars) : pips(s.shownStars, s.unproven)}<small>${s.optimumDistance} · peaks ${s.peakAge}</small></div></div>
        <div class="pc m"><span class="pc-l">M</span><div><b>${esc2(m.name)}</b>${pips(m.stars)}<small>${m.optimumDistance} · peaks ${m.peakAge}</small></div></div></div>
      <div class="auc-facts"><span><span class="line ${ln.cls}">${ln.text}</span></span><span>Reserve <b>${money(l.reserve)}</b></span><span>Guide <b>${money(guide(l)[0])}–${money(guide(l)[1])}</b></span><span>Budget <b>${money(S.budget)}</b></span></div>
      <div class="auc-now" aria-live="polite"><div class="lbl" id="aucLbl">Opening bid</div><div class="big" id="aucBig">${money(openBid(l))}</div><div class="who" id="aucWho">No bids yet</div></div>
      <button class="tb-btn block auc-bid" id="aucBid">Bid</button>
      <div class="auc-auto"><span>Bid for me up to</span><button class="tb-square" id="autoMinus" aria-label="Lower my limit">−</button><span class="amt" id="autoAmt"></span><button class="tb-square" id="autoPlus" aria-label="Raise my limit">+</button><button class="tb-chip" id="autoOn" aria-pressed="false">Off</button></div>
      <ul class="auc-log" id="aucLog"></ul>
      <button class="tb-btn ghost block auc-x" id="aucLeave">Leave the ring</button>
    </div>`;
}
const aucNext = () => A.price == null ? openBid(A.l) : A.price + incFor(A.price);
const aucTimes = () => A.price == null ? [3.6, 5.6, 7.2] : [2.4, 3.9, 5.4];
const aucEl = id => A && A.box.querySelector("#" + id);
function aucWalk(t) {
  if (!A) return;
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches, el = aucEl("aucLot");
  if (!still && !A.done) A.ang += .0035;
  if (el) { el.style.left = (49.5 + 19 * Math.cos(A.ang)) + "%"; el.style.top = (51.5 + 13.5 * Math.sin(A.ang)) + "%"; }
  A.raf = requestAnimationFrame(aucWalk);
}
function rivalWait(r, nx) {
  const q = nx / r.ceil, x = Math.random();
  return Math.min(5.0, q < .7 ? .5 + x * 1.1 : q < .9 ? 1.1 + x * 1.9 : 2.1 + x * 2.9);   // nearer their limit, the longer they hesitate
}
function aucTick() {
  if (!A || A.done) return;
  const e = (performance.now() - A.last) / 1000, nx = aucNext();
  let who = null;
  for (const r of A.rivals) {
    if (r.id === A.leader || r.ceil < nx) { r.wait = null; continue; }
    if (r.wait == null) r.wait = rivalWait(r, nx);
    if (e >= r.wait && (!who || r.wait < who.wait)) who = r;
  }
  if (who) return aucPlace(who.id);
  if (A.autoOn && A.leader !== "me" && nx <= A.auto && nx <= canBidTo() && e >= .7) return aucPlace("me");
  const T = aucTimes(), call = e >= T[2] ? 3 : e >= T[1] ? 2 : e >= T[0] ? 1 : 0;
  if (call !== A.call) { A.call = call; if (call === 3) return aucHammer(); aucCall(call); }
  const arc = aucEl("abArc"); if (arc) arc.setAttribute("stroke-dashoffset", (276.5 * (1 - Math.min(1, e / T[2]))).toFixed(1));
  aucEl("aucClock").classList.toggle("hot", call >= 2);
}
function aucCall(k) {
  const txt = A.price == null ? ["", `Who'll start me at the reserve, ${money(openBid(A.l))}?`, "Anyone at all?", ""][k] : ["", "Going once…", "Going twice…", ""][k];
  const c = aucEl("aucCall"); c.className = "auc-call"; c.textContent = txt; void c.offsetWidth; if (txt) c.classList.add("pop");
}
function aucPlace(id) {
  if (!A || A.done) return;
  const nx = aucNext();
  if (id === "me" && (nx > canBidTo() || A.leader === "me")) return;
  A.price = nx; A.leader = id; A.last = performance.now(); A.call = -1; A.rivals.forEach(r => r.wait = null);
  const name = id === "me" ? "You" : A.rivals.find(r => r.id === id).name;
  A.log.unshift(`${money(nx)} · ${name}`); A.log = A.log.slice(0, 6);
  const seat = aucEl("seat-" + id);
  if (seat) { seat.querySelector(".seat-bub").textContent = money(nx); seat.classList.remove("pop"); void seat.offsetWidth; seat.classList.add("pop"); clearTimeout(seat._h); seat._h = setTimeout(() => seat.classList.remove("pop"), 1400); }
  const p = aucEl("abP"); p.classList.remove("flash"); void p.offsetWidth; p.classList.add("flash");
  aucCall(0); aucPaint();
}
function aucPaint() {
  if (!A) return;
  const nx = aucNext(), me = A.leader === "me", lead = A.leader && !me ? A.rivals.find(r => r.id === A.leader) : null;
  aucEl("abP").textContent = A.price == null ? money(openBid(A.l)).replace("£", "£ ") : money(A.price);
  aucEl("abW").textContent = A.done ? (A.leader ? "SOLD" : "NOT SOLD") : me ? "BID: YOUR SEAT" : lead ? "BID: " + lead.name.toUpperCase() : "OPENING";
  aucEl("aucLbl").textContent = A.price == null ? "Opening bid" : "Current bid";
  aucEl("aucBig").textContent = money(A.price == null ? openBid(A.l) : A.price);
  const who = aucEl("aucWho");
  who.className = "who " + (me ? "me" : lead ? "them" : "");
  who.textContent = me ? "You're the top bidder" : lead ? `${lead.name} has it` : "No bids yet";
  const bid = aucEl("aucBid"), can = !A.done && !me && nx <= canBidTo();
  bid.disabled = !can; bid.textContent = A.done ? "Hammer down" : me ? "You hold the bid" : nx > canBidTo() ? `Can't go to ${money(nx)}` : `Bid ${money(nx)}`;
  aucEl("autoAmt").textContent = money(A.auto);
  const on = aucEl("autoOn"); on.textContent = A.autoOn ? "On" : "Off"; on.classList.toggle("on", A.autoOn); on.setAttribute("aria-pressed", A.autoOn);
  aucEl("aucLeave").disabled = !A.done && me;
  aucEl("aucLeave").textContent = A.done ? "Back to the catalogue" : "Leave the ring";
  aucEl("aucLog").innerHTML = A.log.map(x => `<li>${esc2(x)}</li>`).join("");
  A.rivals.forEach(r => { const s = aucEl("seat-" + r.id); if (s) s.classList.toggle("out", A.done || (r.id !== A.leader && r.ceil < nx)); });
}
function aucHammer() {
  A.done = true; clearInterval(A.timer);
  const l = A.l, c = aucEl("aucCall"), arc = aucEl("abArc"); arc.setAttribute("stroke-dashoffset", 0);
  let msg;
  if (!A.leader) {
    // Unsold: once the ring moves on there's no going back (TA-9)
    msg = "Unsold"; S.sale = S.sale.filter(x => x !== l);
    A.outcome = { kind: "passed", text: `No one bid the reserve on lot ${l.n}. It leaves the ring unsold.` };
  } else if (A.leader === "me") {
    // yours the moment the hammer falls (and saved), not when the ring is left
    msg = "SOLD!"; A.outcome = { kind: "won" };
    const cost = payFor(A.price);   // less your Trade Terms (js/team.js)
    S.budget -= cost; if (typeof ledger === "function") ledger("yearlings", cost); S.sale = S.sale.filter(x => x !== l);
    breed(l.sire, l.dam, "bought", cost, l);
  } else {
    const r = A.rivals.find(x => x.id === A.leader);
    msg = "Sold"; S.sale = S.sale.filter(x => x !== l);
    A.outcome = { kind: "lost", text: `Lot ${l.n} sold to ${r.name} for ${money(A.price)}.` };
  }
  S.ring = null;
  c.className = "auc-call sold"; c.textContent = msg; void c.offsetWidth; c.classList.add("pop");
  if (window.BOARD) BOARD.Sound.gavel();
  A.log.unshift(A.outcome.kind === "won" ? `Knocked down to you at ${money(A.price)}` : A.outcome.text); aucPaint(); save();
  if (A.outcome.kind === "won") setTimeout(aucClose, 1700);
}
function aucLeave() {
  // walking out: the rivals settle it between themselves
  if (!A || A.done) return aucClose();
  if (A.leader === "me") return;
  for (let k = 0; k < 200; k++) {
    const nx = aucNext(), keen = A.rivals.filter(r => r.id !== A.leader && r.ceil >= nx);
    if (!keen.length) break;
    const r = keen[Math.floor(A.rnd() * keen.length)];
    A.price = nx; A.leader = r.id;
  }
  aucHammer(); aucClose();
}
function aucClose() {
  if (!A) return;
  clearInterval(A.timer); cancelAnimationFrame(A.raf);
  const { outcome } = A;
  A.box.remove(); A = null; document.body.style.overflow = "";
  if (window.BOARD) BOARD.setInPlace("tatts");
  if (outcome && outcome.kind !== "won") toast(outcome.text);
  if (!outcome) { S.ring = null; }
  save(); render();
}


