// =====================================================================================================================
// Thoroughbred: your team's screens (the rules are js/team.js). The draft at the Jockey Club, the team cards, and the
// places where they're used: the National Stud (Elite Mares, Black Type Stud, Stud Master), Tattersalls (Auction
// Insider, Bloodstock Agent), entries (trainer cards on horses, jockeys booked for races).
// =====================================================================================================================
const ROLE_CLS = { Owner: "r-own", Trainer: "r-trn", Jockey: "r-jky" };
const ROLE_BLURB = {
  Owner: "Money and bloodstock: a bigger budget, free mares, cheap nominations, help at the sales.",
  Trainer: "Gets your horses ready at Warren Hill: their trip, temperament and ground, and a tune-up for a big race.",
  Jockey: "Rides in the races you book him for: the Champion anywhere, the others at their trips, styles or going.",
};
// The cards look like the board game's: a cream card in a Gold, Silver or Bronze frame, the board's picture for the role
// and tier (img/team, from the Thoroughbred site's Your Team page), the title in capitals, and chips for the points and
// where it's played (owner, 14 Nov: "we really should be lending the graphics from the board game")
const cardArt = c => `img/team/${c.role[0]}${c.tier}.webp`;
function tcard(c, opts = {}) {
  return `<article class="tcard ${ROLE_CLS[c.role]} t${c.tier} ${opts.cls || ""}">
    <div class="tc-art"><img src="${cardArt(c)}" alt="${c.role} ${TIER_NUM[c.tier]}" loading="lazy"></div>
    <div class="tc-body"><h4 class="tc-title">${c.title}</h4>
    <p class="tc-text">${cardText(c)}</p>
    ${opts.fit ? `<p class="tc-fit">${opts.fit}</p>` : ""}
    <div class="tc-chips"><span class="tc-chip">${c.tier} point${c.tier === 1 ? "" : "s"}</span><span class="tc-chip soft">${cardWhen(c)}</span></div>
    ${opts.btn || ""}${opts.extra || ""}</div></article>`;
}
// A word on how a card fits this season's ten races (so the draft is a real choice)
function cardFit(c) {
  if (c.role === "Owner") return "";   // (owner cards have no trips: this crashed the draft once an owner card was drawn, 14 Nov)
  const trips = c.role === "Trainer" ? TRAINER_KINDS[c.kind].trips : JOCKEY_KINDS[c.kind].trips;
  if (trips) { const n = RACES.filter(r => trips.includes(raceTrip(r))).length; return `${n} of your ${RACES.length} races ${n === 1 ? "is" : "are"} at these trips.`; }
  if (c.role === "Trainer" && c.kind === "juvenile") { const n = RACES.filter(r => r.ages[1] === 2).length; return `${n} of your races ${n === 1 ? "is" : "are"} for 2-year-olds.`; }
  if (c.role === "Jockey" && c.kind === "bigrace") { const n = RACES.filter(r => r.grade.startsWith("Group")).length; return `${n} of your races ${n === 1 ? "is a Group race" : "are Group races"}.`; }
  if (c.role === "Jockey" && JOCKEY_KINDS[c.kind].style) return JOCKEY_KINDS[c.kind].style === "front" ? "Best on front-runners and prominent horses." : "Best on midfield and hold-up horses.";
  return "";
}
function teamPips() {
  const p = teamPoints(), roles = new Set(teamCards().map(c => c.role));
  return `<div class="tm-sum"><div class="tm-pips" aria-label="${p} of ${TEAM_POINTS} points">${Array.from({ length: TEAM_POINTS }, (_, k) => `<i class="${k < p ? "on" : ""}"></i>`).join("")}</div>
    <span><b>${p} of ${TEAM_POINTS}</b> points</span>${TEAM_ROLES.map(r => `<span class="tm-role ${ROLE_CLS[r]} ${roles.has(r) ? "got" : ""}">${roles.has(r) ? "✓" : "·"} ${r}</span>`).join("")}</div>`;
}
// (the card you've just drawn shows big at the top for a couple of minutes, then joins the rest)
const justDrew = () => !!UI.drew && Date.now() - UI.drew < 120000;
function draftBody() {
  const T = teamState(), mine = teamCards();
  if (T.offer) keepTeamCard(T.offer.codes[0]);   // a game saved mid-way through the old draft
  if (T.done) return `<div class="tb-head"><h1 class="tb-h">YOUR TEAM</h1>
      <p class="tb-lede">Your team for the season. Each card says where it comes into play: the owner's cards at the stud and the sales, the trainer's at Warren Hill, the jockeys in the races you book them for.</p></div>
    ${teamPips()}${drawnCard()}<div class="tm-hand">${mine.filter(c => c.code !== T.last || !justDrew()).map(c => tcard(c, { fit: cardFit(c) })).join("")}</div>`;
  const decks = `<section class="sect"><div class="sect-h"><h2 class="tb-h2">THE DECKS</h2><span>Gold 3 points · Silver 2 · Bronze 1</span></div>
    <div class="tm-decks">${TEAM_ROLES.map(role => `<div class="tm-row ${ROLE_CLS[role]}"><div class="tm-rl"><b>${role}s</b><small>${ROLE_BLURB[role]}</small></div>
      ${[3, 2, 1].map(t => { const why = deckProblem(role, t);
        return `<button class="tdeck ${ROLE_CLS[role]} t${t}" data-deck="${role}:${t}" ${why ? "disabled" : ""}><img class="td-art" src="img/team/${role[0]}${t}.webp" alt=""><small>${why || `${t} point${t === 1 ? "" : "s"} · draw`}</small></button>`; }).join("")}</div>`).join("")}</div></section>`;
  return `<div class="tb-head"><h1 class="tb-h">DRAFT YOUR TEAM</h1>
      <p class="tb-lede">Before the stud opens, draw the people behind your stable. You have ${TEAM_POINTS} points: a Gold card costs 3, Silver 2 and Bronze 1, and you need at least one owner, one trainer and one jockey. Tap a deck to draw its top card: it joins your team.</p></div>
    ${teamPips()}${drawnCard()}${decks}
    ${mine.length > (justDrew() ? 1 : 0) ? `<section class="sect"><div class="sect-h"><h2 class="tb-h2">YOUR TEAM SO FAR</h2></div><div class="tm-hand">${mine.filter(c => c.code !== T.last || !justDrew()).map(c => tcard(c, { fit: cardFit(c) })).join("")}</div></section>` : ""}`;
}
// the card you've just drawn, turned over
function drawnCard() {
  const T = teamState(); if (!justDrew() || !T.last) return "";
  const c = teamCard(T.last);
  return `<section class="sect tm-offer" id="tmOffer"><div class="sect-h"><h2 class="tb-h2">YOU DREW</h2><span>${c.role} · ${TIER_NAME[c.tier]}</span></div>
    <div class="tm-hand one">${tcard(c, { fit: cardFit(c) })}</div></section>`;
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
// Entries: your trainer's jobs (done at Warren Hill) and your jockeys, booked race by race
function teamAtEntries() {
  if (!teamOn() || teamSkipped()) return "";
  const tr = trainerCards(), jk = jockeyCards();
  const trRow = c => tcard(c, { cls: "sm", extra: `<p class="tc-do">${jobsAll().length ? `Jobs done: ${jobsAll().map(jobLabel).join(", ")}. ` : ""}${jobsLeft() ? `<b>${jobsLeft()}</b> job${jobsLeft() === 1 ? "" : "s"} left: spend ${jobsLeft() === 1 ? "it" : "them"} at Warren Hill, or keep ${jobsLeft() === 1 ? "it" : "them"} for race week.` : c.kind === "form" && !FORM_JOBS[c.tier] ? "Working on every horse." : "Every job is spent."}</p>${jobsLeft() && !atAscot() ? `<button class="tb-btn ghost sm" data-guide="warren">Go to Warren Hill</button>` : ""}` });
  const jkRow = c => tcard(c, { cls: "sm", extra: `<p class="tc-do">Booked for <b>${ridesOf(c.code).length} of ${JOCKEY_RIDES[c.tier]}</b> rides${ridesOf(c.code).length ? ": " + ridesOf(c.code).map(r => r.name.replace(/ Stakes$/, "")).join(", ") : ". Book him in a race below."}</p>` });
  return `<details class="sect tm-at" ${S.team.openEntries === false ? "" : "open"}><summary class="sect-h"><h2 class="tb-h2">YOUR TRAINER AND JOCKEYS</h2><span>The trainer works at Warren Hill; jockeys are booked race by race</span></summary>
    <div class="tm-hand sm">${tr.map(trRow).join("")}${jk.map(jkRow).join("")}</div></details>`;
}
// a job in a few words: "Settle: Copper Falcon"
function jobLabel(j) {
  const h = horse(j.h), n = h ? h.name : "?";
  if (j.k === "trip") return `${j.dir > 0 ? "longer" : "shorter"} trip for ${esc2(n)}`;
  if (j.k === "ground") return `${esc2(n)} on ${j.add.join(" and ")}`;
  if (j.k === "tune") { const r = raceOf(j.race); return `${esc2(n)} tuned up for the ${r ? esc2(shortRace(r)) : "race"}`; }
  return `${JOB_INFO[j.k].name.toLowerCase()}: ${esc2(n)}`;
}
// ---------- Warren Hill: the trainer's jobs ----------
function jobTokens() {
  const tot = jobsTotal(), used = jobsUsed();
  return `<div class="jb-tokens" aria-label="${tot - used} of ${tot} jobs left">${Array.from({ length: tot }, (_, k) => `<i class="${k < used ? "used" : ""}"></i>`).join("")}<span><b>${Math.max(0, tot - used)}</b> of ${tot} job${tot === 1 ? "" : "s"} left</span></div>`;
}
function trainerPanel() {
  if (!teamOn() || teamSkipped() || !trainerCards().length) return "";
  const tr = trainerCards();
  return `<section class="sect tm-at jb-panel"><div class="sect-h"><h2 class="tb-h2">YOUR TRAINER</h2>${jobTokens()}</div>
    <div class="jb-top"><div class="tm-hand sm">${tr.map(c => tcard(c, { cls: "sm" })).join("")}</div>
      <ul class="jb-how">${Object.values(JOB_INFO).map(x => `<li><b>${x.name}</b> ${x.what}.</li>`).join("")}
        <li class="jb-keep">Jobs you don't spend here can be used in race week, once the going is declared: ground work or a tune-up.</li></ul></div></section>`;
}
// the job strip on a horse's card at Warren Hill
function jobStrip(h) {
  if (!teamOn() || teamSkipped() || !trainerCards().length) return "";
  const btn = (k, o, label, title) => { const why = jobProblem(k, h, o); return why ? "" : `<button class="jb-b" data-job="${k}" data-h="${h.id}" ${o.dir ? `data-dir="${o.dir}"` : ""} ${o.side ? `data-side="${o.side}"` : ""} title="${esc2(title)}">${label}</button>`; };
  const d = tripAt(h, h.age), lo = Math.min(...d), hi = Math.max(...d);
  const shift = dir => { const n = tripSteps(h, dir); if (!n) return ""; const nl = Math.max(0, lo + dir * n), nh = Math.min(DISTANCES.length - 1, hi + dir * n); return `${DISTANCES[nl]}${nh !== nl ? "–" + DISTANCES[nh] : ""}`; };
  const adds = side => groundAdds(h, side).join(" & ");
  // the races it's entered in or targeted at first, then any it can run in now, richest first
  const mine = new Set([...runsOf(h).map(r => r.id), ...RACES.filter(r => (S.targets || {})[r.id] === h.id).map(r => r.id)]);
  const races = RACES.filter(r => !S.results[r.id] && !tuneOf(r) && (mine.has(r.id) || (() => { const c = check(h, r); return c && c.ok; })()))
    .sort((a, b) => mine.has(b.id) - mine.has(a.id) || b.prizes[0] - a.prizes[0]);
  const tune = races.length && !jobProblem("tune", h, { race: races[0].id }) ? `<select class="jb-sel" data-tune="${h.id}"><option value="">Tune-up for…</option>${races.map(r => `<option value="${r.id}">${esc2(shortRace(r))} (+${tuneBoost(h, r)}${tuneFree(r) ? ", free" : ""})</option>`).join("")}</select>` : "";
  const nx = eyed(h) ? nextAge(h) : null;
  const done = jobsOn(h).map(j => `<span class="jb-done">${JOB_INFO[j.k].name}${j.k === "trip" ? `: ${j.dir > 0 ? "longer" : "shorter"}` : j.k === "ground" ? `: ${j.add.join(", ")}` : j.k === "tune" ? `: ${esc2(shortRace(raceOf(j.race) || { name: "" }))}` : ""}${j.free ? " (free)" : ""}${jobUndoable(j.i) ? `<button data-unjob="${j.i}" aria-label="Undo">×</button>` : ""}</span>`).join("");
  const notes = trainerNotes(h).map(t => `<li>${esc2(t)}</li>`).join("");
  const opts = [btn("trip", { dir: -1 }, `Shorter: ${shift(-1)}`, "Trip work: its best trip moves this way for the season"), btn("trip", { dir: 1 }, `Longer: ${shift(1)}`, "Trip work: its best trip moves this way for the season"),
    btn("settle", {}, "Settle", "A keen horse learns to settle"), btn("ground", { side: "soft" }, `Also ${adds("soft")}`, "Ground work: it handles this going too"), btn("ground", { side: "quick" }, `Also ${adds("quick")}`, "Ground work: it handles this going too"),
    btn("eye", {}, eyeFree() ? "" : "Trainer's eye", "See how it will be at the next age before you develop it")].join("") + tune;
  return `<div class="jb-strip">${notes ? `<ul class="jb-notes">${notes}</ul>` : ""}
    ${nx ? `<div class="jb-eye">Trainer's eye: at ${nx.age} it will be rated <b>${nx.rating}</b>, best <b>${tripText(nx.trip)}</b>.</div>` : ""}
    ${done ? `<div class="jb-dones">${done}</div>` : ""}
    ${opts ? `<div class="jb-opts">${opts}</div>` : jobsLeft() ? "" : `<div class="jb-none">No jobs left.</div>`}</div>`;
}
// race week: jobs kept back, now the going is out (ground work, tune-ups) for horses with races still to run
function weekJobs() {
  if (!teamOn() || teamSkipped() || !trainerCards().length || !jobsLeft() || S.step !== 4) return "";
  const rows = RACES.filter(r => !S.results[r.id] && S.entries[r.id]).map(r => { const h = horse(S.entries[r.id]), g = CARD.going[r.day];
    if (!h) return "";
    const side = GROUND_ORDER.indexOf(g) < GROUND_ORDER.indexOf(h.grounds[0]) ? "soft" : "quick", adds = h.grounds.includes(g) ? [] : groundAdds(h, side);
    const gb = adds.length && !jobProblem("ground", h, { side }) ? `<button class="jb-b" data-job="ground" data-h="${h.id}" data-side="${side}">Ground work: also ${adds.join(" & ")}${adds.includes(g) ? " (+5 today)" : ""}</button>` : "";
    const tb = !jobProblem("tune", h, { race: r.id }) ? `<button class="jb-b" data-job="tune" data-h="${h.id}" data-race="${r.id}">Tune-up +${tuneBoost(h, r)}${tuneFree(r) ? " (free)" : ""}</button>` : "";
    return gb || tb ? `<li><span><b>${esc2(shortRace(r))}</b> · ${esc2(h.name)} · ${g}${h.grounds.includes(g) ? " (likes it)" : ""}</span><span class="jb-opts">${gb}${tb}</span></li>` : ""; }).join("");
  return rows ? `<section class="sect tm-at jb-week"><div class="sect-h"><h2 class="tb-h2">YOUR TRAINER IN RACE WEEK</h2>${jobTokens()}</div>
    <p class="tc-do">The going is out. Spend the jobs you kept back on ground work or a tune-up before the race is run.</p><ul class="jb-wk">${rows}</ul></section>` : "";
}
// the jockey line in a race's panel at entries
function jockeyPick(r) {
  if (!teamOn() || teamSkipped()) return "";
  const jk = jockeyCards(); if (!jk.length) return "";
  const cur = bookedFor(r), h = horse(S.entries[r.id]);
  if (!h && !cur) return `<div class="tm-jk"><span>Jockey</span><small>Enter a runner, then book one of your jockeys for it.</small></div>`;
  return `<div class="tm-jk"><span>Jockey</span><select class="tm-sel" data-bookrace="${r.id}"><option value="">Your yard's own jockey</option>${jk.map(c => { const left = ridesLeft(c) + (cur && cur.code === c.code ? 1 : 0);
    return `<option value="${c.code}" ${cur && cur.code === c.code ? "selected" : ""} ${left > 0 ? "" : "disabled"}>${cardName(c)} (${left} ride${left === 1 ? "" : "s"} left)${!jockeySuits(c, h, r) ? (JOCKEY_KINDS[c.kind].style ? " · doesn't suit its style" : " · nothing extra here") : ""}</option>`; }).join("")}</select></div>`;
}
// what the team does for a horse in a race, in words (for the horse cards' verdict line)
function teamNote(c) {
  if (!c) return "";
  const bits = (c.train ? c.train.cards.map(x => x.c && x.c.kind === "form" ? `${x.did} ${cardName(x.c)}` : x.did) : []).concat(c.jock && c.jock.why ? [c.jock.why] : []);
  return bits.length ? " · " + bits.join(", ") : "";
}
