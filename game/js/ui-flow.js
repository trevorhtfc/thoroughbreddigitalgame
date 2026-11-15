// =====================================================================================================================
// Thoroughbred: the flow pieces from the owner's phone and iPad review (15 Nov 2026).
// Owner: "the horses in your stable are at the moment super confusing so they need tidying up so it's either collapsible
// or something. Once entered they should be out the way. You should be able to develop at all stages.. see your team
// members at all stages as well.. I also need key pop ups of key headlines at each stage."
//   - horse rows: one tidy line per horse that opens up for its details; entered horses folded away at the foot
//   - your team: a Team button in the bar opens your cards from anywhere
//   - key headlines: the first time a step's place is opened in a game, its key points pop up (the "i" in the sheet's
//     header brings them back)
// Loaded after js/ui.js (it uses UI, render, phase and the screens' pieces from js/ui-parts.js and js/ui-team.js).
// =====================================================================================================================

/* ================= Horse rows: tidy, collapsible, entered horses out of the way ================= */
UI.hx = {};            // which horses are opened up
UI.showEnt = false;    // the entered horses' group, folded away until asked for
// developing is open at every stage until race week (at the races the training is over)
const canDev = h => h.age < 4 && S.step <= 3 && !atAscot();
function hrow(h, race, canAct, opts = {}) {
  const now = ratingAt(h, h.age), here = !!race && S.entries[race.id] === h.id, inRace = race ? clashFor(h, race) : null, runs = runsOf(h);
  const open = !!UI.hx[h.id];
  let verdict = "", act = "", cant = false;
  if (race) {
    const why = whyNot(h, race), c = why ? null : check(h, race);
    if (why || !c.ok) { cant = true; verdict = `<span class="hr-v no">${esc2(why || c.why)}</span>`; }
    else verdict = `<span class="hr-v">${rkChip(c)}<small>${rankText(c)}${c.steps ? ` · −${c.steps * 5} trip` : ""}${c.ground ? ` · ${c.ground > 0 ? "+" : "−"}${Math.abs(c.ground)} going` : ""}${teamNote(c)}</small></span>`;
    if (canAct) act = here ? `<button class="tb-btn ghost sm" data-unpick="${race.id}">Take out</button>`
      : !cant ? `<button class="tb-btn sm" data-pick="${h.id}" data-race="${race.id}">${inRace ? "Move here" : "Enter"}</button>` : "";
    // too young for this race: develop it from right here, then enter it
    if (!act && canDev(h) && h.age < race.ages[0]) act = `<button class="tb-btn ghost sm" data-develop="${h.id}">Develop to ${h.age + 1}YO</button>`;
  }
  const T = S.targets || {}, targets = RACES.filter(r => T[r.id] === h.id);
  const tags = [];
  if (here) tags.push(`<span class="hr-tag here">Your runner here</span>`);
  (race ? (inRace ? [inRace] : []) : runs).forEach(r => tags.push(`<span class="hr-tag in">Entered: ${raceTag(r)}</span>`));
  if (!here && !runs.length) targets.forEach(r => tags.push(`<span class="hr-tag tg" title="Flagged in your race planner">⚑ ${raceTag(r)}</span>`));
  if (opts.train && typeof jobsOn === "function" && teamOn()) jobsOn(h).forEach(j => tags.push(`<span class="hr-tag jb">${JOB_INFO[j.k].name}</span>`));
  const dev = canDev(h) ? `<button class="tb-btn ghost sm" data-develop="${h.id}" title="Develop to ${h.age + 1}: its rating and best trip change, and there's no going back">Develop to ${h.age + 1}YO</button>` : "";
  const today = race && goingKnown() ? CARD.going[race.day] : null;
  return `<article class="hr ${open ? "open" : ""} ${here ? "here" : ""} ${cant ? "cant" : ""}" ${opts.plan ? `data-plandrop="${h.id}"` : ""}>
    <div class="hr-top"><button class="hr-tog" type="button" data-hx="${h.id}" aria-expanded="${open}" aria-label="${esc2(h.name)}: ${open ? "hide" : "show"} details">
      <img class="hr-por" src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt="">
      <span class="hr-id"><b class="hr-nm">${esc2(h.name)}</b>
        <small><i class="hr-sx ${h.sex}">${h.sex === "F" ? "♀" : "♂"}</i>${h.age}YO · ${tripText(tripAt(h, h.age))}${h.style ? `<span class="hr-st"> · ${styleTag(h)}</span>` : ""}</small></span>
      <span class="hr-rt"><b>${now}</b><small>Rating</small></span>
      <span class="hr-chev" aria-hidden="true"></span>
    </button>${!race && dev ? `<button class="hr-dev" type="button" data-develop="${h.id}" title="Develop to ${h.age + 1}: its rating and best trip change, and there's no going back"><b>Develop</b><small>to ${h.age + 1}YO</small></button>` : ""}</div>
    ${verdict || tags.length || act ? `<div class="hr-line">${verdict}<span class="hr-tags">${tags.join("")}</span><span class="hr-acts">${act}</span></div>` : ""}
    ${open ? `<div class="hr-more">
      <div class="hr-facts"><div class="hc2-track">${[2, 3, 4].map(a => `<span class="${a < h.age ? "past" : a === h.age ? "now" : ""} ${a === h.peakAge ? "pk" : ""}">${a}YO</span>`).join("")}</div>
        <em>Projected peak ${h.peakAge}YO</em><span class="hr-by">by ${esc2(h.sire)} out of ${esc2(h.dam)}</span></div>
      <div class="hc2-prof">${profileHTML(h, race)}</div>
      <div class="hk-ground" aria-label="Going it likes">${GROUND_ORDER.map(g => `<span class="${h.grounds.includes(g) ? "on g-" + g : ""} ${g === today ? "today" : ""}">${g}</span>`).join("")}</div>
      ${race ? entryNote(h, race, inRace, here) : ""}
      ${opts.plan ? targetBox(h, race) : ""}
      ${opts.train ? jobStrip(h) : ""}
      <div class="hr-acts2">${race && !act.includes("data-develop") ? dev : ""}<button class="tb-btn ghost sm" data-card="${h.id}">See its card</button></div>
    </div>` : ""}
  </article>`;
}
// The list: colts, then fillies; youngest first, best first; in a race, your runner leads. Horses already entered (in a
// race that rules this one out, or anywhere when there's no race) are folded away at the foot.
function horseRows(list, race, canAct, opts = {}) {
  const taken = h => race ? !!clashFor(h, race) && S.entries[race.id] !== h.id : runsOf(h).length > 0;
  const free = list.filter(h => !taken(h)), rest = list.filter(taken);
  const score = h => { if (!race) return ratingAt(h, h.age); const c = whyNot(h, race) ? null : check(h, race); return c && c.ok ? 1000 + c.day : ratingAt(h, h.age) - 1000; };
  const order = a => a.slice().sort((x, y) => (race ? (S.entries[race.id] === y.id) - (S.entries[race.id] === x.id) || score(y) - score(x) : x.age - y.age || score(y) - score(x)) || x.name.localeCompare(y.name));
  const group = (hs) => {
    if (race) return `<div class="hr-list">${order(hs).map(h => hrow(h, race, canAct, opts)).join("")}</div>`;
    return ["C", "F"].map(sx => { const g = hs.filter(h => h.sex === sx); return g.length ? `<h3 class="hr-h">${sx === "C" ? "♂ Colts" : "♀ Fillies"}<span>${g.length}</span></h3><div class="hr-list">${order(g).map(h => hrow(h, race, canAct, opts)).join("")}</div>` : ""; }).join("");
  };
  const anyOpen = list.some(h => UI.hx[h.id]);
  return `<div class="hr-wrap">
    <div class="hr-tools"><span>${race ? `${free.filter(h => { const c = whyNot(h, race) ? null : check(h, race); return c && c.ok; }).length} of your horses can run in this race` : `Tap a horse for its details${list.some(canDev) ? " and to develop it" : ""}`}</span>${anyOpen ? `<button type="button" class="hr-fold" data-hxall="0">Close all</button>` : ""}</div>
    ${free.length ? group(free) : `<p class="tb-empty">${rest.length ? "Every horse is entered." : "No horses yet."}</p>`}
    ${rest.length ? `<div class="hr-ent ${UI.showEnt ? "on" : ""}"><button type="button" class="hr-entbtn" data-showent="1" aria-expanded="${UI.showEnt}"><b>${race ? "Entered in another race" : "Entered"}</b><span>${rest.length}</span><em>${UI.showEnt ? "Hide" : "Show"}</em></button>
      ${UI.showEnt ? `<div class="hr-list">${order(rest).map(h => hrow(h, race, canAct, opts)).join("")}</div>` : ""}</div>` : ""}
  </div>`;
}

/* ================= Your team, from anywhere ================= */
function teamStatus(c) {
  try {
    if (c.role === "Trainer") { const t = jobsTotal(); return t ? `${jobsLeft()} of ${t} job${t === 1 ? "" : "s"} left` : "Working on every horse"; }
    if (c.role === "Jockey") { const n = ridesOf(c.code).length; return `Booked for ${n} of ${JOCKEY_RIDES[c.tier]} rides${n ? ": " + ridesOf(c.code).map(shortRace).join(", ") : ""}`; }
    switch (c.kind) {
      case "elite": return handOn() ? `${upgradesLeft()} upgrade${upgradesLeft() === 1 ? "" : "s"} left` : "";
      case "stallion": return ownedStallion() ? `Your stallion: ${ownedStallion()} · ${ownedFreeLeft()} free nomination${ownedFreeLeft() === 1 ? "" : "s"} left` : "Choose your stallion at the National Stud";
      case "pedigree": if (PEDIGREE_LOOKS[c.tier] >= 99) return "Knows every unproven stallion"; return `${pedigreeLeft()} question${pedigreeLeft() === 1 ? "" : "s"} left`;
      case "vet": return `${vetLeft()} report${vetLeft() === 1 ? "" : "s"} left`;
      case "private": return S.team.used.private ? "Used" : "Not used yet";
      case "scout": return scoutState().briefed ? `Briefed for ${scoutRaces().length} race${scoutRaces().length === 1 ? "" : "s"}` : "Brief him at Tattersalls";
    }
  } catch (e) {}
  return "";
}
function openTeamPop() {
  const mine = teamCards();
  const body = !mine.length
    ? `<p class="kp-p">Your team is drafted at the Jockey Club before the stud opens: an owner, a trainer and a jockey, from six points.</p>`
    : TEAM_ROLES.map(role => { const cs = mine.filter(c => c.role === role); return cs.length ? `<h3 class="kp-h ${ROLE_CLS[role]}">${role}${cs.length > 1 ? "s" : ""}</h3>
        <div class="kp-cards">${cs.map(c => { const st = teamOn() ? teamStatus(c) : ""; return tcard(c, { cls: "sm", extra: st ? `<p class="tc-do">${esc2(st)}</p>` : "" }); }).join("")}</div>` : ""; }).join("");
  kpShow(`<div class="kp-k">${teamOn() ? `${teamPoints()} of ${TEAM_POINTS} points` : "Being drafted"}</div><h2 id="kpT">Your team</h2>${body}
    <div class="kp-b"><button class="tb-btn" type="button" data-kpok="1">Close</button></div>`, "wide");
}

/* ================= Key headlines: a pop-up for each step ================= */
const TIPS_OFF = "tb-tips-off";
const tipsOff = () => { try { return localStorage.getItem(TIPS_OFF) === "1"; } catch (e) { return false; } };
const plural = (n, w, ws) => `${n} ${n === 1 ? w : (ws || w + "s")}`;
const HEADLINES = {
  team: () => ({ place: "jockey", t: "Draft your team", pts: [
    `You have <b>${TEAM_POINTS} points</b>: a Gold card costs 3, Silver 2 and Bronze 1.`,
    "You need at least one <b>owner</b>, one <b>trainer</b> and one <b>jockey</b>. Tap a deck to turn over its top card.",
    "Owners help at the stud and the sales, trainers at Warren Hill, jockeys in the races you book them for.",
    "The <b>Team</b> button at the top shows your cards at any time."] }),
  breed: () => ({ place: "stud", t: "Breed your foals", pts: [
    `You have <b>${money(S.budget)}</b> to build a stable for ${plural(RACES.length, "race")}: room for ${STABLE_CAP} horses.`,
    handOn() ? `Draw your ${HAND.hi + HAND.mid + HAND.lo} mares from the Weatherbys decks. Then tap a mare, tap a stallion and press <b>Breed</b>.` : `Buy mares at the mares sale, then tap a mare, tap a stallion and press <b>Breed</b>.`,
    "An outcross (a different sire line) adds 1 to 3 to the foal's rating. The same line can take up to 4 off.",
    `Keep money back for Tattersalls: Book 1 lots start at ${money(RESERVES[BOOKS[0].min])}. Once you leave for the sales, the stud is closed.`] }),
  sales: () => ({ place: "tatts", t: "The Yearling Sales", pts: [
    "The lots are yearlings out of the mares nobody bred, each by a stallion drawn at random.",
    "You see the pedigree and whether it's a colt or a filly, but not the yearling itself, until it's knocked down to you.",
    "Bring a lot into the ring and bid against the rival buyers: when the count runs out, the hammer falls.",
    `You have <b>${money(S.budget)}</b> left. This is the last chance to buy before the races.`] }),
  gallops: () => ({ place: "warren", t: "Into training", pts: [
    "Every horse arrives as a 2-year-old. <b>Develop</b> one to 3 or 4 and its rating and best trip change: you only see how once it's done, and there's no going back.",
    "A horse can only run in races for its age, so check the ages on the programme.",
    trainerCards().length && jobsTotal() ? `Your trainer has <b>${plural(jobsLeft(), "job")}</b>: open a horse to give it trip work, settling, ground work or a tune-up.` : "",
    "You can develop horses from <b>Your Stables</b> at any time before race week."].filter(Boolean) }),
  entries: () => ({ place: "jockey", t: "Make your entries", pts: [
    `${W.entryRule}. Pick a race at the top, then enter a horse from the list below it.`,
    "Each horse shows its rating for that race and where that puts it in the field. Each step from its best trip costs 5.",
    jockeyCards().length ? "Book your jockeys for the races they suit. Any rides you leave are booked for you when you go." : "",
    "<b>Fill empty races</b> picks the best free horse for every race still without a runner."].filter(Boolean) }),
  week: () => ({ place: "races", t: W.weekTitle || "Race week", pts: [
    "The going is declared for each day: a horse that likes the ground runs better.",
    "<b>Watch in 3D</b>, or <b>Sim</b> for the result straight away. Both run the very same race.",
    "The pace forecast: lots of front-runners make a fast race that suits horses held up; none makes it slow and tactical.",
    "You can change your entries until the first race is run."] }),
};
function headlineFor(ph) { const f = HEADLINES[ph]; return f ? f() : null; }
// the step's key points, if this sheet is the step's place
function sheetHeadline() { const ph = phase(), H = headlineFor(ph); return H && UI.sheet === H.place && (H.place !== "races" || atAscot()) ? H : null; }
function showHeadline(force) {
  const ph = phase(), H = sheetHeadline(); if (!H) return;
  S.seenTips = S.seenTips || {};
  if (!force && (S.seenTips[ph] || tipsOff())) return;
  S.seenTips[ph] = 1; save();
  const ch = CHAPTERS[ph];
  kpShow(`<div class="kp-k">Step ${ch.step} of 5 · ${esc2(SHEET_TITLE[H.place] || "")}</div><h2 id="kpT">${esc2(H.t)}</h2>
    <ol class="kp-l">${H.pts.map(p => `<li>${p}</li>`).join("")}</ol>
    <div class="kp-b"><button class="tb-btn" type="button" data-kpok="1">Got it <span aria-hidden="true">›</span></button></div>
    <label class="kp-off"><input type="checkbox" data-kpoff="1" ${tipsOff() ? "checked" : ""}><span>Don't pop these up at each step (the <b>i</b> at the top still shows them)</span></label>`);
}
function kpShow(html, cls) {
  kpClose();
  const el = document.createElement("div"); el.id = "kp"; el.className = "kp-wrap";
  el.innerHTML = `<div class="kp ${cls || ""}" role="dialog" aria-modal="true" aria-labelledby="kpT"><button class="kp-x" type="button" data-kpok="1" aria-label="Close">×</button>${html}</div>`;
  el.addEventListener("click", e => { if (e.target === el) kpClose(); });
  document.body.appendChild(el);
  const b = el.querySelector(".kp-b [data-kpok]"); if (b) setTimeout(() => b.focus({ preventScroll: true }), 50);
}
function kpClose() { const el = document.getElementById("kp"); if (el) el.remove(); }
function paintInfo() { const b = document.getElementById("shInfo"); if (b) b.hidden = !sheetHeadline(); }

// the sheet opens: its step's headline the first time, and the "i" in the header
const _openSheet = openSheet;
openSheet = function (id, o) { _openSheet(id, o); paintInfo(); setTimeout(() => { if (UI.sheet === id && !document.querySelector(".foal-wrap, .tm-reveal, .auc")) showHeadline(); }, 450); };
// the draft's key points come up as the draw's cards are put away
const _closeDeal = closeDeal;
closeDeal = function () { _closeDeal(); setTimeout(() => { if (UI.sheet === "jockey" && phase() === "team") showHeadline(); }, 450); };
const _paintSheet = paintSheet;
paintSheet = function (first) { _paintSheet(first); paintInfo(); };

document.addEventListener("click", e => {
  const t = e.target.closest && e.target.closest("button, input[data-kpoff]"); if (!t) return;
  const d = t.dataset;
  if (d.kpoff) { try { localStorage.setItem(TIPS_OFF, t.checked ? "1" : "0"); } catch (err) {} return; }
  if (d.kpok) { kpClose(); return; }
  if (d.teampop) { openTeamPop(); return; }
  if (d.stables) { if (atAscot()) return; if (UI.sheet !== "stables") { closeSheet({ quiet: true }); UI.tab.stables = "string"; openSheet("stables"); } return; }
  if (d.hx) { UI.hx[d.hx] = !UI.hx[d.hx]; render(); return; }
  if (d.hxall) { UI.hx = {}; render(); return; }
  if (d.showent) { UI.showEnt = !UI.showEnt; render(); return; }
  if (t.id === "shInfo") { showHeadline(true); return; }
  if (t.id === "unStallion") { S.selStallion = null; save(); render(); return; }
});
addEventListener("keydown", e => { if (e.key === "Escape" && document.getElementById("kp")) kpClose(); });
const canDevAny = () => S.stable.some(canDev);
