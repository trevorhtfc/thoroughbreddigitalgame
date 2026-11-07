// =====================================================================================================================
// Thoroughbred Ascot: the game's shell. The Newmarket board (js/board.js) is home and the map of the season: each step
// is a place on it, lit when it's the step to take next, and its screens open as a sheet over the board. Between the
// steps the story moves on: a chapter card, the journey inked across the board to the next place, a procession of horses
// (js/life.js). Race week is at Ascot, reached by film (video/), and each race is watched in the 3D race view.
// The rules and the state are js/rules.js; the screens' pieces are js/ui-parts.js.
// =====================================================================================================================

/* ================= The season, chapter by chapter ================= */
// where you are in the season decides which place is next, what each place offers and what the board says
const CHAPTERS = {
  draw:      { step: 1, place: "jockey", season: "Winter", title: "The Royal Ascot programme", hour: 10.5,
               line: "The Jockey Club has drawn your ten races for Royal Ascot. Go and see what you're aiming at." },
  breed:     { step: 1, place: "stud", season: "Spring", title: "The covering season", hour: 8,
               line: "Buy your mares at the National Stud and send them to the stallions of your choice." },
  sales:     { step: 2, place: "tatts", season: "Autumn", title: "The Yearling Sales", hour: 11,
               line: "The mares nobody bred have sent their yearlings to Tattersalls. Bid for the best of them." },
  gallops:   { step: 3, place: "warren", season: "The next spring", title: "Into training", hour: 7,
               line: "Your string is in the yard as 2-year-olds. Take them up Warren Hill to bring them on." },
  entries:   { step: 3, place: "jockey", season: "May", title: "Entries", hour: 14,
               line: "Enter one horse for each race at the Jockey Club, then load the horseboxes for Ascot." },
  week:      { step: 4, place: "races", season: "June", title: "Royal Ascot", hour: 9,
               line: "Five days, ten races. The horseboxes are loaded." },
  standings: { step: 5, place: "races", season: "June", title: "The final standings", hour: 18, line: "" },
  home:      { step: 5, place: "palace", season: "Summer", title: "Home to Newmarket", hour: 19.2,
               line: "Your title from Royal Ascot hangs in Palace House." },
};
const STEPS = [
  { n: 1, name: "The Stud", place: "stud" }, { n: 2, name: "The Sales", place: "tatts" }, { n: 3, name: "Entries", place: "jockey" },
  { n: 4, name: "Royal Ascot", place: "races" }, { n: 5, name: "The Result", place: "palace" },
];
function phase() {
  if (!S.dealt) return "draw";
  if (S.step === 1) return "breed";
  if (S.step === 2) return "sales";
  // (training on Warren Hill, "gallops", is kept for a later version: owner, 6 Nov; horses are developed at the foal
  // reveal and on the entries screen meanwhile)
  if (S.step === 3) return "entries";
  if (S.step === 4) return "week";
  return S.home ? "home" : "standings";
}
const entered = () => RACES.filter(r => S.entries[r.id]).length;
const racesRun = () => RACES.filter(r => S.results[r.id]).length;
const prizeWon = () => RACES.reduce((a, r) => a + (S.results[r.id] ? S.results[r.id].prize : 0), 0);
const winsNow = () => RACES.filter(r => S.results[r.id] && S.results[r.id].pos === 1).length;
function nextPlace() {
  const ph = phase();
  if (ph === "entries" && entered() === RACES.length) return "races";
  return CHAPTERS[ph].place;
}
const atAscot = () => S.at === "ascot";

/* ================= The places: what each is for, and what it offers now ================= */
const PLACE_ICON = { jockey: "JC", stud: "horse-head", tatts: "gavel", stables: "stable", warren: "horse", palace: "greek-temple", races: "horse" };
function placeStates() {
  const ph = phase(), has = S.stable.length > 0, st = {};
  const after = (k) => ["draw", "breed", "sales", "gallops", "entries", "week", "standings", "home"].indexOf(ph) > ["draw", "breed", "sales", "gallops", "entries", "week", "standings", "home"].indexOf(k);
  st.jockey = "open"; st.palace = "open";
  st.stables = has ? "open" : "locked";
  st.stud = ph === "breed" ? "open" : after("breed") ? "done" : "locked";
  st.tatts = ph === "sales" || ph === "gallops" || ph === "entries" ? (S.sale.length || ph === "sales" ? "open" : "done") : after("entries") ? "done" : "locked";
  st.warren = "locked";                                             // training comes in a later version
  st.races = ph === "gallops" || ph === "entries" || ph === "week" || ph === "standings" ? "open" : ph === "home" ? "done" : "locked";
  st[nextPlace()] = "next";
  return st;
}
// the card each place shows on the board
function cardFor(id) {
  const ph = phase(), st = placeStates()[id], ch = CHAPTERS[ph];
  const c = { state: st, kicker: "", status: st === "next" ? "Your next step" : st === "done" ? "Done" : "", text: "", cta: "", off: st === "locked", note: "" };
  const n = entered(), left = RACES.length - n;
  switch (id) {
    case "jockey":
      c.kicker = "Racing's rule-makers";
      if (ph === "draw") { c.text = "The programme for Royal Ascot is out: ten races over five days, two a day, drawn fresh for this season."; c.cta = "See the programme"; }
      else if (ph === "gallops" || ph === "entries") { c.text = `Make your entries: one horse per race. <b>${n} of ${RACES.length}</b> races have a runner.`; c.cta = "Make entries"; c.off = false; }
      else if (ph === "week" || ph === "standings") { c.text = `The programme, with your results so far: <b>${racesRun()} of ${RACES.length}</b> run.`; c.cta = "The programme"; }
      else { c.text = "Your ten races and the race planner: map out which horse is for which race."; c.cta = "The programme"; }
      break;
    case "stud":
      c.kicker = "Mares, stallions and foals";
      if (st === "locked") { c.status = "Opens once you've seen the programme"; c.text = "Where your stable begins: buy mares at the mares sale and send them to the stallions."; c.cta = "Visit the Stud"; }
      else if (ph === "breed") { c.text = `You have <b>${money(S.budget)}</b> to spend. Buy mares at the mares sale and breed them: <b>${studCount()}</b> mare${studCount() === 1 ? "" : "s"} and <b>${S.stable.filter(h => h.how === "bred").length}</b> foal${S.stable.filter(h => h.how === "bred").length === 1 ? "" : "s"} so far.`; c.cta = "Visit the Stud"; }
      else { c.status = "The covering season is over"; c.text = `Your ${S.usedMares.length} mare${S.usedMares.length === 1 ? "" : "s"} produced ${S.stable.filter(h => h.how === "bred").length} foal${S.stable.filter(h => h.how === "bred").length === 1 ? "" : "s"}.`; c.cta = "Look back"; c.off = false; }
      break;
    case "tatts":
      c.kicker = "The sale ring";
      if (st === "locked") { c.status = "The sales are in the autumn, once you leave the stud"; c.text = "Bid against rival buyers for yearlings out of the mares nobody bred."; c.cta = "Enter the sale ring"; }
      else if (ph === "sales") { c.text = `<b>${S.sale.length}</b> lots in three Books. You see the pedigree, not the yearling, until it's knocked down to you. Budget <b>${money(S.budget)}</b>.`; c.cta = "Enter the sale ring"; }
      else if (st === "open") { c.status = `${S.sale.length} lot${S.sale.length === 1 ? "" : "s"} still to sell`; c.text = "The sale goes on: you can still buy any lots that are left."; c.cta = "Back to the sale ring"; }
      else { c.status = "The sales are over"; c.text = `You bought ${S.stable.filter(h => h.how === "bought").length} yearling${S.stable.filter(h => h.how === "bought").length === 1 ? "" : "s"} here.`; c.cta = ""; }
      break;
    case "stables": {
      const col = S.stable.filter(h => h.sex === "C").length, fil = S.stable.length - col;
      c.kicker = "Your string";
      if (st === "locked") { c.status = "Empty until your first horse arrives"; c.text = "Every horse you breed or buy is kept here, with its card and its race targets."; c.cta = "Visit your yard"; }
      else { c.text = `<b>${S.stable.length}</b> horse${S.stable.length === 1 ? "" : "s"}: ${col} colt${col === 1 ? "" : "s"} and ${fil} fill${fil === 1 ? "y" : "ies"}. Their cards and their race targets.`; c.cta = "Visit your yard"; }
      break; }
    case "warren": {
      const can = S.stable.filter(h => h.age < 4).length;
      c.kicker = "The gallops";
      if (st === "locked") { c.status = "Coming in a later version"; c.text = "Training on the gallops is on its way. For now, develop your 2-year-olds when they arrive or on the Jockey Club's entries screen."; c.cta = ""; }
      else if (st === "done") { c.status = "Training is over for this season"; c.text = "Your string has gone to Ascot."; c.cta = ""; }
      else { c.text = `Develop a horse to 3 or 4 to change its rating and best trip; you only see how once it's done. <b>${can}</b> of your ${S.stable.length} could still develop.`; c.cta = "Go to the gallops"; }
      break; }
    case "palace": {
      const weeks = pastWeeks().length;
      c.kicker = "The National Horseracing Museum";
      if (ph === "home") { const T = titleFor(prizeWon()); c.text = `Your title from Royal Ascot is waiting: <b>${T.name}</b>, with ${money(prizeWon())} in prize money.`; c.cta = "Visit Palace House"; }
      else { c.text = weeks ? `Your trophies and every Royal Ascot you've played: <b>${weeks}</b> so far.` : "Your trophies and racing history, and how the game is played."; c.cta = "Visit Palace House"; }
      break; }
    case "races":
      c.kicker = "Royal Ascot · June";
      if (st === "locked") { c.status = "Royal Ascot is in June, once your string is in training"; c.text = "Five days, ten races, watched at Ascot in 3D."; c.cta = "Go to Royal Ascot"; }
      else if (ph === "gallops" || ph === "entries") {
        c.text = `<b>${n} of ${RACES.length}</b> races have a runner. Once you leave for Ascot your entries are lodged and the going is declared.`;
        c.cta = "Go to Royal Ascot";
        if (left) c.note = `<b>${left} race${left === 1 ? " has" : "s have"} no runner.</b> An empty race earns nothing.`;
      }
      else if (ph === "week") { c.text = `Race week is under way: <b>${racesRun()} of ${RACES.length}</b> run, <b>${money(prizeWon())}</b> won.`; c.cta = "Back to Royal Ascot"; }
      else if (ph === "standings") { c.text = "The final standings are in."; c.cta = "Back to Royal Ascot"; }
      else { c.status = "Royal Ascot is over for this year"; c.text = `You won ${money(prizeWon())} and ${winsNow()} race${winsNow() === 1 ? "" : "s"}.`; c.cta = ""; }
      break;
  }
  if (st === "next" && ch && ch.title) c.kicker = ch.title;   // no time of year on the labels (owner, 7 Nov: it is never winter at Royal Ascot)
  return c;
}

/* ================= The bar: where you are, your stable, your money ================= */
const UI = { sheet: null, tab: {}, story: null, cineOn: false };
function paintBar() {
  const ph = phase(), stepNow = CHAPTERS[ph].step;
  $("#brandWhere").textContent = atAscot() ? "Royal Ascot" : "Newmarket";
  $("#steps").innerHTML = STEPS.map(s => {
    const cls = s.n < stepNow || (s.n === 5 && ph === "home") ? "done" : s.n === stepNow ? "current" : "";
    return `<button class="st ${cls}" type="button" data-step="${s.n}" ${cls === "current" ? 'aria-current="step"' : ""} title="${s.name}"><b>${s.n}</b><span>${s.name}</span></button>`;
  }).join("");
  const n = S.stable.length;
  $("#tally").innerHTML = S.step <= 3
    ? `<span class="t-silk">${silkImg(mySilkN())}</span><span title="Horses in your stable"><svg viewBox="0 0 512 512">${ICON.stable}</svg><em>${n}</em><i>/${STABLE_CAP}</i></span><span class="t-money" title="Your budget"><svg viewBox="0 0 512 512">${ICON["two-coins"]}</svg><em>${money(S.budget)}</em></span>`
    : `<span class="t-silk">${silkImg(mySilkN())}</span><span title="Wins: ${winsNow()} from ${racesRun()} of ${RACES.length} races run"><svg viewBox="0 0 512 512">${ICON["laurels-trophy"]}</svg><em>${winsNow()}</em><i> win${winsNow() === 1 ? "" : "s"}</i></span><span class="t-money prize" title="Prize money won (a separate pot from your budget)"><svg viewBox="0 0 512 512">${ICON["trophy-cup"]}</svg><em>${money(prizeWon())}</em></span>`;
  fitBar();
}
// if the five steps' names don't fit beside the tally (a narrow window, or the fonts still loading), only the
// current step keeps its name
function fitBar() {
  const st = $("#steps"); if (!st) return;
  st.classList.remove("tight");
  if (st.scrollWidth > st.clientWidth + 1) st.classList.add("tight");
}
addEventListener("resize", () => fitBar());
if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => fitBar());

/* ================= The board: the places' states, the card, the guide ================= */
function paintBoard() {
  if (!window.BOARD) return;
  BOARD.setStates(placeStates());
  BOARD.flyOwn(SILK3D[mySilkN()]);
  paintGuide();
  if (BOARD.chosen && !UI.sheet) BOARD.choose(BOARD.chosen);    // keep the open card's words up to date
}
function paintGuide() {
  const ph = phase(), ch = CHAPTERS[ph], nx = nextPlace(), p = BOARD.placeOf(nx), g = $("#guide");
  const what = {
    draw: "See the programme at the Jockey Club", breed: "Breed your foals at the National Stud", sales: "Buy at the Yearling Sales, Tattersalls",
    gallops: "Bring your string on at Warren Hill", entries: nx === "races" ? "Every race has a runner: off to Royal Ascot" : `Make your entries at the Jockey Club (${entered()} of ${RACES.length})`,
    week: "Race week at Royal Ascot", standings: "The final standings at Ascot", home: "Collect your title at Palace House",
  }[ph];
  g.innerHTML = `<div class="g-step"><b>${ch.step}</b><span>of 5</span></div><div class="g-t"><span class="g-k">${ch.title}</span><b>${what}</b></div>
    <button class="g-go" type="button" data-guide="${nx}" aria-label="Show me ${p ? p.title : ""}">Show me<svg viewBox="0 0 10 16" aria-hidden="true"><path d="M1.6 0 0 1.6 6.4 8 0 14.4 1.6 16l8-8z"/></svg></button>`;
  g.hidden = atAscot() || UI.cineOn;
}
let chapterTimer = 0;
// The chapter's words live on the guide and on the place's card (owner, 6 Nov: too many boxes), so there's no
// separate chapter box any more; the guide is simply brought up to date.
function showChapter() { paintGuide(); }
function hideChapter() { const el = $("#chapter"); if (el.hidden) return; el.classList.remove("in"); el.classList.add("out"); setTimeout(() => { if (el.classList.contains("out")) el.hidden = true; }, 600); }

/* ================= The story between the steps ================= */
// The sheet closes, the chapter card comes up, the journey is inked from the place just finished to the next, the
// little horse trots along it (and a procession on the roads, when the 3D life is running), then the next place's card opens.
async function story(from, to, key, { procession, then } = {}) {
  const run = UI.story = {};
  closeSheet({ quiet: true });
  BOARD.choose(null);
  if (CHAPTERS[key]) BOARD.setHour(CHAPTERS[key].hour);
  paintBar(); paintBoard();
  showChapter(key);
  if (procession && window.LIFE) { try { LIFE.procession(procession, { silk: SILK3D[mySilkN()] }); } catch (e) { console.warn(e); } }
  BOARD.Sound.hooves && BOARD.Sound.hooves(3);
  if (from && to && from !== to) await BOARD.trail(from, to);
  if (UI.story !== run) return;
  if (then) { await then(); if (UI.story !== run) return; }
  BOARD.choose(nextPlace());
}

/* ================= Sheets: a place's screens over the board ================= */
const SHEET_TITLE = { jockey: "The Jockey Club", stud: "The National Stud", tatts: "Tattersalls", stables: "Your Stables", warren: "Warren Hill", palace: "Palace House", races: "Royal Ascot" };
function openSheet(id, { tab } = {}) {
  hideChapter();
  if (tab) UI.tab[id] = tab;
  UI.sheet = id;
  BOARD.choose(null); BOARD.covered = true; BOARD.setInPlace(id === "races" ? (atAscot() ? "races" : "races") : id);
  $("#sheetWrap").hidden = false; document.body.classList.add("sheet-open");
  const s = $("#sheet"); s.dataset.place = id; s.classList.remove("in"); void s.offsetWidth; s.classList.add("in");
  $("#shBody").scrollTop = 0;
  paintBar(); paintSheet(true);
  if (id === "jockey" && !S.dealt && !D) startDeal();   // a draw already under way is picked up again by paintSheet
}
function closeSheet({ quiet } = {}) {
  if (!UI.sheet) return;
  const was = UI.sheet; UI.sheet = null;
  clearDeal();
  $("#sheetWrap").hidden = true; document.body.classList.remove("sheet-open");
  BOARD.covered = false; BOARD.setInPlace(null);
  if (!quiet) { paintBoard(); if (!atAscot()) BOARD.choose(was === "races" ? null : was); }
}
const sheetTop = () => { $("#shBody").scrollTop = 0; };
function paintSheet(first) {
  const id = UI.sheet; if (!id) return;
  const body = $("#shBody"), keep = first ? 0 : body.scrollTop, ph = phase(), ch = CHAPTERS[ph];
  const p = BOARD.placeOf(id);
  // the header: a window onto the place on the board (or the course, at Ascot), its medal and title
  $("#shTitle").textContent = id === "races" ? (S.step >= 5 ? "Final standings" : "Royal Ascot") : atAscot() && id === "jockey" ? "Declarations" : SHEET_TITLE[id];
  $("#shKicker").textContent = id === "races" ? `${MEETING.month} ${MEETING.year} · ${S.step >= 5 ? "the week is run" : "race week"}`
    : atAscot() && id === "jockey" ? `${MEETING.name} · change your runners before the first race`
    : (placeStates()[id] === "next" ? `Step ${ch.step} of 5 · ${ch.title}` : cardFor(id).kicker);
  const ic = PLACE_ICON[id];
  $("#shMedal").innerHTML = ic === "JC" ? `<span class="jc">JC</span>` : ic === "horse" ? `<span class="hz"></span>` : `<svg viewBox="0 0 512 512">${ICON[ic]}</svg>`;
  const pic = $("#shPic");
  if (id === "races" || atAscot()) { pic.style.backgroundImage = "url(img/ascot-still.jpg)"; pic.style.backgroundSize = "cover"; pic.style.backgroundPosition = "50% 30%"; }
  else if (p) BOARD.paintPic(pic, [p.pic[0], p.pic[1], Math.max(560, Math.min(1000, (pic.clientWidth || 1200) * 0.72))], 0.7);
  $("#shClose").hidden = atAscot();
  $("#main").innerHTML = SHEETS[id]();
  $("#go").innerHTML = FOOTS[id] ? FOOTS[id]() : "";
  $("#go").hidden = !$("#go").innerHTML.trim();
  if (id === "races" && S.step >= 5) resultAfter(prizeWon());
  if (id === "jockey" && UI.dealing && D) reattachDeal();
  body.scrollTop = keep;
}

/* ----- the sheets' bodies ----- */
const SHEETS = {
  jockey() {
    if (!S.dealt) return drawBody();
    const ph = phase(), canEnter = S.step >= 3 && S.step <= 4 && !racesRun();
    const tab = UI.tab.jockey || (canEnter && (ph === "entries" || ph === "gallops" || atAscot()) ? "entries" : "programme");
    const tabs = [["programme", "The programme"], ["plan", "Race planner"]].concat(canEnter ? [["entries", "Entries"]] : []);
    const bar = `<div class="vtabs" role="tablist">${tabs.map(([k, t]) => `<button class="vtab ${tab === k ? "on" : ""}" data-jtab="${k}" role="tab" aria-selected="${tab === k}">${t}${k === "entries" ? `<i>${entered()}/${RACES.length}</i>` : k === "plan" ? `<i>${RACES.filter(r => (S.targets || {})[r.id] && horse(S.targets[r.id])).length}/${RACES.length}</i>` : ""}</button>`).join("")}</div>`;
    if (tab === "entries" && canEnter) return bar + entriesBody(entered());
    if (tab === "plan") return bar + `<p class="tb-lede sh-lede">Map out which horse is for which race. A target is only a plan: it doesn't enter the horse. Drag a race onto a horse, or tap a race to see how every horse fits it.</p>` + plannerView();
    return bar + programmeBody();
  },
  stud() {
    if (S.step === 1) return breedBody();
    const bred = S.stable.filter(h => h.how === "bred");
    return `<div class="tb-head"><h1 class="tb-h">THE COVERING SEASON IS OVER</h1><p class="tb-lede">Your mares and the foals they produced. Once you went to Tattersalls the stud closed for the season.</p></div>
      ${bred.length ? cardGroups(bred, null, false) : `<p class="tb-empty">You didn't breed any foals this season.</p>`}`;
  },
  tatts() { return saleBody(); },
  stables() {
    const tab = UI.tab.stables || "string";
    const bar = `<div class="vtabs" role="tablist"><button class="vtab ${tab === "string" ? "on" : ""}" data-stab="string" role="tab">Your string<i>${S.stable.length}</i></button><button class="vtab ${tab === "plan" ? "on" : ""}" data-stab="plan" role="tab">Race planner<i>${RACES.filter(r => (S.targets || {})[r.id] && horse(S.targets[r.id])).length}/${RACES.length}</i></button></div>`;
    if (tab === "plan") return bar + plannerView();
    return bar + `<div class="tb-head"><p class="tb-lede">${needs()}. ${S.step <= 2 ? "Every foal arrives as a 2-year-old." : "Develop them on Warren Hill, then enter them at the Jockey Club."}</p></div>
      ${S.stable.length ? horseCols(S.stable, null, false, { plan: false }, false) : `<p class="tb-empty">No horses yet.</p>`}`;
  },
  warren() { return gallopsBody(); },
  palace() { return museumBody(); },
  races() { return S.step >= 5 ? resultBody(winsNow(), racesRun() - winsNow(), prizeWon()) : weekBody(racesRun()); },
};
const goBtn = (id, label, opts = {}) => `<button class="tb-btn ${opts.ghost ? "ghost" : ""}" id="${id}" ${opts.off ? "disabled" : ""}>${label}${opts.ghost ? "" : ' <span aria-hidden="true">›</span>'}</button>`;
const FOOTS = {
  jockey() {
    if (!S.dealt) return "";
    if (atAscot()) return `<span class="f-info">Change your runners before the first race. The going is declared again when you go back.</span>${goBtn("toWeek", "Back to race week")}`;
    const ph = phase();
    if (ph === "gallops" || ph === "entries") { const left = RACES.length - entered();
      return `<span class="f-info ${left ? "" : "ready"}">${left ? `${left} race${left === 1 ? "" : "s"} still without a runner.` : `All ${RACES.length} races have a runner.`}</span>${goBtn("toRaces", "Go to Royal Ascot")}`; }
    return "";
  },
  stud() {
    if (S.step !== 1) return "";
    return S.confirmSale
      ? `<span class="f-info"><b>Close the stud?</b> Once you go to Tattersalls you can't come back to breed.${S.hand.length ? ` Your ${S.hand.length} unused mare${S.hand.length === 1 ? "" : "s"} may turn up in the sale.` : ""}</span>${goBtn("saleNo", "Stay at the stud", { ghost: true })}${goBtn("saleYes", "Go to Tattersalls", { off: S.foal || S.offer })}`
      : `<span class="f-info">${studCount()} mare${studCount() === 1 ? "" : "s"} · ${S.stable.length} horse${S.stable.length === 1 ? "" : "s"} · ${money(S.budget)} left</span>${goBtn("toSale", "Close the stud and go to the sales", { off: S.foal || S.offer })}`;  },
  tatts() {
    // never a dead end: with no horse bought or bred you can still leave (and race nothing, or start again)
    if (S.step === 2) return `<span class="f-info">${S.stable.length} horse${S.stable.length === 1 ? "" : "s"} in your string · ${money(S.budget)} left</span>${goBtn("toEnter", S.stable.length ? "Leave the sales: on to entries" : "Leave the sales without a horse", { off: S.foal })}`;
    return "";
  },
  warren() {
    const ph = phase();
    if (ph === "gallops") return `<span class="f-info">Develop any that need it, or come back later: the gallops stay open until you leave for Ascot.</span>${goBtn("doneGallops", "Done on the gallops: on to entries")}`;
    return "";
  },
  palace() { return phase() === "home" ? `<span class="f-info">A new season: new races, new mares, the same ${money(START_BUDGET)}.</span>${goBtn("again", "Start a new season")}` : ""; },
  races() {
    if (S.step === 4) { const done = racesRun();
      return `<span class="f-info ${done === RACES.length ? "ready" : ""}">${done === RACES.length ? `All ${RACES.length} races run.` : `${done} of ${RACES.length} races run · ${money(prizeWon())} won`}</span>${goBtn("simAll", "Sim the rest", { ghost: true, off: done === RACES.length || simBusy })}${goBtn("toResult", "See the final standings", { off: done < RACES.length })}`; }
    if (S.step >= 5) return `<span class="f-info">Your title goes home with you, to Palace House.</span>${goBtn("goHome", "Home to Newmarket")}`;
    return "";
  },
};

/* ----- The Jockey Club: the draw, the programme ----- */
function programmeBody() {
  const going = goingKnown();
  return `<div class="tb-head"><p class="tb-lede">Your ten races at Royal Ascot, two a day over five days: Group races, Listed races and big handicaps. Each needs a minimum rating to run, and handicaps take horses rated ${HCAP_MAX} or less. ${going ? "The going has been declared." : "The going is declared in race week, once your entries are in."}</p></div>
    <div class="prog">${DAYS.map((d, k) => `<section class="prog-day"><h3>${d}${going ? ` <span class="gday g-${CARD.going[k]}">${CARD.going[k]}</span>` : ""}</h3>
      ${RACES.filter(r => r.day === k).map(r => { const res = S.results[r.id], h = horse(S.entries[r.id]), t = (S.targets || {})[r.id] && horse(S.targets[r.id]);
        return `<div class="prog-r">${raceFace(r)}<div class="prog-who">${h ? `${silkImg(mySilkN())}<b>${esc2(h.name)}</b>` : t ? `<span class="plan">Planned: ${esc2(t.name)}</span>` : `<span class="none">No runner yet</span>`}
          ${res ? `<span class="pos ${res.pos === 1 ? "win" : res.pos && res.pos <= 3 ? "placed" : ""}">${res.pos ? ord(res.pos) : "–"}</span>` : ""}</div>
          <div class="prog-need">${bandsLine(r)}</div></div>`; }).join("")}</section>`).join("")}</div>`;
}
// the draw: the ten races dealt onto the Jockey Club's table
let D = null;
const still = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
function raceFace(r) {
  const g = GRADE[r.grade];
  return `<div class="rf ${g.cls}"><div class="rf-top"><b>${g.short === "Hcap" ? "HANDICAP" : g.short === "Cond" ? "CONDITIONS" : r.grade.toUpperCase()}</b><span>${r.dist}</span></div>
    <div class="rf-n ${r.name.length > 24 ? "long" : ""}">${r.name}</div><div class="rf-f"><span>${ageOnly(r)} · ${r.sex === "C" ? "♂ Colts" : r.sex === "F" ? (r.ages[0] >= 4 ? "♀ F&M" : "♀ Fillies") : "⚥ Open"}</span><span>1st ${money(r.prizes[0])}</span></div></div>`;
}
const cardBack = (k, t) => `<div class="dc-back"><span>${k}<b>${t}</b></span></div>`;
function dealCard(face, backHTML, cls) { return `<div class="dc ${cls || ""}"><div class="dc-in">${backHTML}<div class="dc-face">${face}</div></div></div>`; }
function drawBody() {
  return `<div class="deal in-sheet" id="deal"><div class="deal-in">
      <div class="deal-head"><div><div class="deal-k" id="dealKicker">Season ${S.seed} · the draw</div><h2 class="deal-t" id="dealTitle">Your ten races</h2></div><button class="deal-skip" id="dealSkip" type="button">Skip</button></div>
      <div class="deal-body" id="dealBody"></div>
      <div class="deal-foot"><p class="deal-sum" id="dealSum"></p><button class="tb-btn" id="dealNext" type="button" hidden></button></div>
    </div><div class="deal-deck" id="dealDeck" aria-hidden="true"><i></i><i></i><i></i></div></div>`;
}
function startDeal() { UI.dealing = true; D = { phase: 0, timers: [] }; dealRaces(); }
function reattachDeal() { if (D && D.phase >= 2) { dealRaces(true); racesDone(true); } else dealRaces(); }
function dealTimers(fn, ms) { D.timers.push(setTimeout(fn, ms)); }
function clearDeal() { if (D) { D.timers.forEach(clearTimeout); D.timers = []; } }
function flyIn(cards, gap) {
  const deck = $("#dealDeck").getBoundingClientRect(), cx = deck.left + deck.width / 2, cy = deck.top + deck.height / 2;
  cards.forEach((c, i) => {
    const r = c.getBoundingClientRect(), dx = cx - (r.left + r.width / 2), dy = cy - (r.top + r.height / 2);
    if (still()) return;
    c.animate([{ transform: `translate(${dx}px,${dy}px) rotate(${(i % 2 ? 1 : -1) * 9}deg) scale(.55)`, opacity: 0 }, { opacity: 1, offset: .12 }, { transform: "none", opacity: 1 }],
      { duration: 560, delay: i * gap, easing: "cubic-bezier(.2,.8,.3,1)", fill: "backwards" });
  });
}
function dealRaces(instant) {
  if (!$("#dealBody")) return;
  if (!instant) D.phase = 1;
  $("#dealSum").classList.remove("on"); $("#dealNext").hidden = true; $("#dealSkip").hidden = false;
  $("#dealDeck").classList.remove("gone");
  $("#dealBody").innerHTML = `<div class="dl-grid">${DAYS.map((d, k) => `<div class="dl-day"><h4>${d.slice(0, 3)}</h4>
    ${RACES.filter(r => r.day === k).map(r => dealCard(raceFace(r), cardBack("ROYAL ASCOT", "Race"), GRADE[r.grade].cls)).join("")}</div>`).join("")}</div>`;
  const cards = [...$("#dealBody").querySelectorAll(".dc")];
  if (instant || still()) { cards.forEach(c => c.classList.add("up")); if (!instant) racesDone(); return; }
  flyIn(cards, 95);
  BOARD.Sound.chime();
  const t0 = cards.length * 95 + 650;
  cards.forEach((c, i) => dealTimers(() => c.classList.add("up"), t0 + i * 170));
  dealTimers(racesDone, t0 + cards.length * 170 + 500);
}
function racesDone(instant) {
  if (!D || (!instant && D.phase !== 1) || !$("#dealBody")) return; D.phase = 2;
  $("#dealBody").querySelectorAll(".dc").forEach(c => c.classList.add("up"));
  const g1 = RACES.filter(r => r.grade === "Group 1").length, open = RACES.filter(isOpenRace).length, other = RACES.length - g1 - open;
  const top = Math.max(...RACES.map(r => r.prizes[0])), low = Math.min(...RACES.map(r => r.prizes[0]));
  $("#dealSum").innerHTML = `<b>${g1} Group 1${g1 === 1 ? "" : "s"}</b>, ${other} other Group or Listed race${other === 1 ? "" : "s"} and ${open} handicap${open === 1 ? "" : "s"}. Winners' prizes from ${money(low)} to ${money(top)}. You have ${money(START_BUDGET)} to build a stable for them: breed at the National Stud first, then buy at Tattersalls.`;
  $("#dealSum").classList.add("on");
  $("#dealDeck").classList.add("gone"); $("#dealSkip").hidden = true;
  const n = $("#dealNext"); n.hidden = false; n.innerHTML = `To the National Stud <span aria-hidden="true">›</span>`;
}
function skipDeal() { clearDeal(); $("#dealBody").querySelectorAll(".dc").forEach(c => c.getAnimations().forEach(a => a.finish())); if (D && D.phase === 1) racesDone(); }
function closeDeal() { clearDeal(); D = null; UI.dealing = false; S.dealt = true; save(); story("jockey", "stud", "breed"); }

/* ----- National Stud and Tattersalls: the Ascot game's own screens (js/ui-parts.js), in the sheet ----- */

/* ----- Warren Hill: the gallops ----- */
function gallopsBody() {
  const young = S.stable.filter(h => h.age < 4), grown = S.stable.filter(h => h.age >= 4);
  if (!S.stable.length) return `<p class="tb-empty">No horses in training yet.</p>`;
  return `<div class="tb-head"><p class="tb-lede">Every horse arrives as a 2-year-old. Work one up the hill to develop it to 3 or 4: its rating and best trip change, and you only see how once it's done. There's no going back, and a horse can only run in races for its age. The projected peak is the age it should be at its best.</p></div>
    <div class="gal-sum"><span><b>${young.length}</b> could still develop</span><span><b>${grown.length}</b> fully grown</span><span><b>${S.stable.filter(h => h.age === h.peakAge).length}</b> at their projected peak</span></div>
    ${horseCols(S.stable, null, true, { plan: true }, false)}`;
}

/* ----- Palace House: your trophies and your history ----- */
const HONOURS_KEY = "tb-" + MEETING.id + "-honours";
function honours() { try { const h = JSON.parse(localStorage.getItem(HONOURS_KEY) || "[]"); return Array.isArray(h) ? h : []; } catch (e) { return []; } }
function noteHonours() {
  try {
    const h = honours(); if (h.some(x => x.seed === S.seed)) return;
    RACES.forEach(r => { const res = S.results[r.id], hs = horse(S.entries[r.id]); if (res && res.pos === 1 && hs) h.push({ seed: S.seed, horse: hs.name, race: r.name, grade: r.grade, by: res.by, when: Date.now(), silks: mySilkN() }); });
    localStorage.setItem(HONOURS_KEY, JSON.stringify(h.slice(-300)));
  } catch (e) {}
}
function museumBody() {
  const ph = phase(), hist = pastWeeks().slice().sort((a, b) => b.prize - a.prize), counts = {}, best = bestWeek();
  hist.forEach(w => counts[w.title] = (counts[w.title] || 0) + 1);
  const hon = honours().slice().reverse();
  const T = ph === "home" ? titleFor(prizeWon()) : null;
  return `${T ? `<section class="trophy ${T.cls}"><div class="tr-k">Royal Ascot ${MEETING.year} · season ${S.seed}</div><div class="tr-t">${T.name}</div>
      <p>${T.note} ${money(prizeWon())} in prize money, ${winsNow()} win${winsNow() === 1 ? "" : "s"} from ${RACES.length} races.</p>
      <div class="tr-cup"><svg viewBox="0 0 512 512">${ICON["laurels-trophy"]}</svg></div></section>` : ""}
    <div class="tb-head"><p class="tb-lede">The National Horseracing Museum keeps every Royal Ascot you've played: the titles you've won, your best weeks and the horses that won for you.</p></div>
    <section class="rec"><h2 class="tb-h2">YOUR TITLES</h2>
      <div class="rec-titles">${TITLES.map(t => `<div class="rt ${t.cls} ${counts[t.name] ? "got" : ""}"><b>${counts[t.name] ? "×" + counts[t.name] : "?"}</b><span>${t.name}</span><small>${t.min ? money(t.min) + "+" : "under " + money(TITLES[TITLES.length - 2].min)}</small></div>`).join("")}</div>
      ${best ? `<p class="rec-n">Your best week: <b>${money(best.prize)}</b> (season ${best.seed}, ${best.wins} win${best.wins === 1 ? "" : "s"}).</p>` : ""}
    </section>
    ${hist.length ? `<section class="rec"><h2 class="tb-h2">YOUR ROYAL ASCOTS</h2><table class="rec-t"><thead><tr><th>#</th><th>Season</th><th>Prize money</th><th>Wins</th><th>Title</th></tr></thead><tbody>${hist.slice(0, 12).map((w, k) =>
        `<tr class="${w.seed === S.seed ? "me" : ""}"><td>${k + 1}</td><td>${w.seed}</td><td><b>${money(w.prize)}</b></td><td>${w.wins}/${w.races}</td><td>${w.title}</td></tr>`).join("")}</tbody></table>
      <p class="rec-n">${hist.length} week${hist.length === 1 ? "" : "s"} played. Collect every title.</p></section>` : ""}
    ${hon.length ? `<section class="rec"><h2 class="tb-h2">ROLL OF HONOUR</h2><ul class="honours">${hon.slice(0, 30).map(x => `<li>${silkImg(x.silks || 0)}<b>${esc2(x.horse)}</b><span>${esc2(x.race)}</span><small>${esc2(x.grade)} · season ${x.seed}</small></li>`).join("")}</ul></section>` : ""}
    <section class="rec how"><h2 class="tb-h2">HOW THE SEASON GOES</h2><ol class="how-list">
      <li><b>The Jockey Club</b>: the ten races for Royal Ascot are drawn.</li>
      <li><b>The National Stud</b>: buy mares (choose one of three each time) and send them to the stallions. A mare can be at most one star above her stallion; outcrosses breed best, the same family worst. Unproven stallions may be a star better or worse than they look.</li>
      <li><b>Tattersalls</b>: the yearlings out of the mares nobody bred are sold in three Books. Bid against five rival buyers; you see the pedigree, not the yearling, until it's yours.</li>
      <li><b>Warren Hill</b>: develop horses to 3 or 4. Their rating and best trip change; you only see how once it's done.</li>
      <li><b>The Jockey Club</b>: enter one horse per race. Each step from its best trip costs 5; the going counts in race week (+5 on a going it likes, down to −10 three steps off).</li>
      <li><b>Royal Ascot</b>: watch each race in 3D or sim it. Rating, trip, going and pace decide it, and a horse's running style meets the pace of the race. Prize money is its own pot; the money you spent doesn't count against it.</li>
    </ol></section>`;
}

/* ================= Films between the places ================= */
// newmarket-arrive.mp4 is the owner's map clip played backwards: from the treetops down onto the board. Its last frame is
// the board itself (the board scaled by 0.706 and moved by (129.5, -23.6) in the 1280 x 720 frame), so the film is laid
// exactly over the live board as it lands, and fades into it.
const CLIP = { w: 1280, h: 720, k: 0.706, x: 129.5, y: -23.6 };
function boardRect() { const r = $("#stage").getBoundingClientRect(); return r; }
function clipRectOnBoard() {
  const b = boardRect(), s = b.width / 1448, f = s / CLIP.k;
  return { left: b.left - CLIP.x * f, top: b.top - CLIP.y * f, width: CLIP.w * f, height: CLIP.h * f, board: b };
}
function coverRect(w, h) {
  const W = innerWidth, H = innerHeight, k = Math.max(W / w, H / h);
  return { left: (W - w * k) / 2, top: (H - h * k) / 2, width: w * k, height: h * k };
}
const lerpRect = (a, b, u) => ({ left: a.left + (b.left - a.left) * u, top: a.top + (b.top - a.top) * u, width: a.width + (b.width - a.width) * u, height: a.height + (b.height - a.height) * u });
// play a film: from one framing to another; resolves when it ends (or is skipped)
function film(src, { from = "cover", to = "cover", caption = "", sound = false, fadeOut = true, fadeIn = true, poster } = {}) {
  return new Promise((done) => {
    const box = $("#cine"), v = $("#cineVid"), cap = $("#cineCap");
    UI.cineOn = true; paintGuide();
    box.hidden = false; box.className = "cine on" + (fadeIn ? " fade-in" : "");
    cap.innerHTML = caption; cap.classList.remove("show");
    v.muted = !(sound && BOARD.Sound.on); v.src = src; if (poster) v.poster = poster;
    let finished = false, raf = 0;
    const rectFor = (k) => k === "board" ? clipRectOnBoard() : coverRect(v.videoWidth || CLIP.w, v.videoHeight || CLIP.h);
    const place = (r) => Object.assign(v.style, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
    const end = () => {
      if (finished) return; finished = true; cancelAnimationFrame(raf);
      const close = () => { box.hidden = true; box.className = "cine"; v.removeAttribute("src"); v.load(); UI.cineOn = false; paintGuide(); done(); };
      if (fadeOut) { box.classList.add("fade-out"); setTimeout(close, 650); } else close();
    };
    const tick = () => {
      if (finished) return;
      const d = v.duration || 4, u = Math.min(1, v.currentTime / d), e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      const a = rectFor(from), b = rectFor(to), r = lerpRect(a, b, e); place(r);
      // landing on (or leaving) the board: clip the film to the board's frame, so the clip's dark edges never show
      if (from === "board" || to === "board") {
        const br = clipRectOnBoard().board, w = to === "board" ? e : 1 - e, ins = (x) => Math.max(0, x * w);
        box.style.setProperty("--clip", `inset(${ins(br.top)}px ${ins(innerWidth - br.right)}px ${ins(innerHeight - br.bottom)}px ${ins(br.left)}px)`);
        box.classList.toggle("landing", to === "board" && u > 0.86);
      }
      if (u > 0.15 && caption) cap.classList.add("show");
      if (u > 0.82 && caption) cap.classList.remove("show");
      raf = requestAnimationFrame(tick);
    };
    $("#cineSkip").onclick = end;
    v.onended = end; v.onerror = end;
    v.onloadedmetadata = () => place(rectFor(from));
    const go = v.play(); if (go && go.catch) go.catch(() => { v.muted = true; v.play().catch(end); });
    raf = requestAnimationFrame(tick);
    setTimeout(() => { if (!finished && v.currentTime === 0) end(); }, 9000);   // never hang on a film that won't play
  });
}
// coming home to the board: the film lands on it, then the board comes alive
async function arriveNewmarket(withFilm = true) {
  S.at = "newmarket"; save();
  document.body.classList.remove("at-ascot"); document.body.classList.add("at-newmarket"); $("#ascot").hidden = true;
  BOARD.setHour(CHAPTERS[phase()].hour); BOARD.holdDay = false;
  paintBar(); paintBoard();
  // the film the first time in a visit, and on the way home from Ascot; otherwise the board simply comes back
  if (withFilm) await film("video/newmarket-arrive.mp4", { from: "cover", to: "board", fadeIn: true });
  UI.arrived = true;
}
// leaving for Ascot: the horseboxes go, the board tilts up into the landscape, then the film of the races
// leaving for Ascot (owner, 6 Nov): the race film leads straight into race week, started in the very tap that sends
// you, so it plays with its sound
async function goToAscot() {
  closeSheet({ quiet: true }); BOARD.choose(null);
  S.step = 4; S.open = null; save();
  if (window.LIFE) { try { LIFE.procession("boxes"); } catch (e) {} }
  await arriveAscot(true);
}
async function arriveAscot(withFilm) {
  S.at = "ascot"; save();
  const there = () => { document.body.classList.remove("at-newmarket"); document.body.classList.add("at-ascot"); $("#ascot").hidden = false; paintBar(); paintGuide(); };
  if (withFilm) {
    const f = film("video/ascot-arrive.mp4", { caption: `<span>${MEETING.month} ${MEETING.year}</span><b>Royal Ascot</b><i>Five days · ten races</i>`, sound: true, fadeIn: true, poster: "img/ascot-still.jpg" });
    setTimeout(there, 550);                                          // once the film has faded up over the board
    await f;
  }
  there();
  openSheet("races");
  BOARD.Sound.horn();
}
async function goHomeFromAscot() {
  closeSheet({ quiet: true });
  S.home = true; save();
  await arriveNewmarket(true);
  story("races", "palace", "home");
}

/* ================= The cover ================= */
let menuOpen = false, newArmed = false;
const hasProgress = () => S.dealt || S.step > 1 || S.stable.length > 0 || S.budget !== START_BUDGET;
function openMenu() {
  menuOpen = true; newArmed = false; const m = $("#menu"); m.hidden = false;
  paintMenu(); const v = $("#menuVid"); try { v && v.play && v.play().catch(() => {}); } catch (e) {}
  const on = m.querySelector(".sw.on"), st = on && on.parentNode; if (st) st.scrollLeft = Math.max(0, on.offsetLeft - (st.clientWidth - on.offsetWidth) / 2);
}
function closeMenu() { menuOpen = false; $("#menu").hidden = true; const v = $("#menuVid"); try { v && v.pause(); } catch (e) {} }
function paintMenu(keepScroll) {
  const strip = $("#menu .swatches"), x = strip ? strip.scrollLeft : 0;
  $("#menuCol").innerHTML = `<div class="mc-big">${silkImg(mySilkN())}</div><div class="mc-h">Your colours</div>
    <div class="swatches" role="group" aria-label="Choose your silks">${SILKS.map((c, k) => `<button class="sw ${k === mySilkN() ? "on" : ""}" data-silks="${k}" aria-label="Silks ${k + 1} of ${SILKS.length}" aria-pressed="${k === mySilkN()}">${silkImg(k)}</button>`).join("")}</div>`;
  if (keepScroll) { const s2 = $("#menu .swatches"); if (s2) s2.scrollLeft = x; }
  const counts = {}; pastWeeks().forEach(w => counts[w.title] = (counts[w.title] || 0) + 1);
  $("#menuTitles").innerHTML = TITLES.map(t => `<li class="${t.cls} ${counts[t.name] ? "got" : ""}"><b data-n="${counts[t.name] ? "✓ ×" + counts[t.name] : ""}">${t.name}</b><span>${t.min ? money(t.min).replace(",000,000", "m").replace(/,000$/, "k") + "+" : "under " + money(TITLES[TITLES.length - 2].min).replace(/,000$/, "k")}</span></li>`).join("");
  const b = bestWeek(); $("#menuBest").innerHTML = b ? `Your best week: <b>${money(b.prize)}</b> · ${titleFor(b.prize).name}` : "";
  const ph = phase(), ch = CHAPTERS[ph];
  $("#menuGo").innerHTML = hasProgress()
    ? `<button class="tb-btn" id="menuContinue">Continue season ${S.seed}<small>Step ${ch.step} of 5 · ${ch.title}</small></button><button class="tb-btn ghost" id="menuNew">${newArmed ? "Tap again to confirm" : "Start a fresh season"}<small>${newArmed ? "This season will be lost" : "New races and mares"}</small></button>`
    : `<button class="tb-btn" id="menuContinue">Start season ${S.seed}<small>Newmarket and ${money(START_BUDGET)} are waiting</small></button><button class="tb-btn ghost" id="menuNew">Draw a different season<small>New races and mares</small></button>`;
}
// a new season from the cover or Palace House: whatever was open goes, and the season starts at Newmarket
function freshSeason() {
  if (A) { clearInterval(A.timer); cancelAnimationFrame(A.raf); A.box.remove(); A = null; document.body.style.overflow = ""; }
  closeSheet({ quiet: true }); clearDeal(); D = null; UI.dealing = false; UI.tab = {}; UI.story = null;
  newCard(); S.at = "newmarket"; save();
}
async function leaveMenu() {
  closeMenu();
  // still at Ascot: back to race week (Declarations reopen as race week; the going is declared again)
  if (atAscot() && !S.home) { if (S.step === 3) S.step = 4; save(); await arriveAscot(false); return; }
  await arriveNewmarket(!UI.arrived);
  const ph = phase();
  showChapter(ph);
  BOARD.choose(nextPlace());
}

/* ================= Drawing everything ================= */
function render() {
  paintBar();
  if (!atAscot()) paintBoard();
  if (UI.sheet) paintSheet();
  renderFoal();
}

/* ================= Clicks ================= */
document.addEventListener("change", e => { if (e.target.id === "sort") { S.sort = e.target.value; save(); render(); } });
document.addEventListener("click", e => {
  const t = e.target.closest("button"); if (!t || t.disabled) return;
  const d = t.dataset;
  if (d.guide) { BOARD.choose(d.guide); return; }
  if (d.step) { const s = STEPS.find(x => x.n === +d.step); if (s && !atAscot()) BOARD.choose(s.n === CHAPTERS[phase()].step ? nextPlace() : s.place); return; }
  if (d.jtab) { UI.tab.jockey = d.jtab; render(); sheetTop(); return; }
  if (d.stab) { UI.tab.stables = d.stab; render(); sheetTop(); return; }
  if (d.tab) { S.tab = d.tab; save(); render(); return; }
  if (d.mare) { if (S.selMare !== d.mare) { S.selMare = d.mare; S.selStallion = null; save(); render(); sheetTop(); } return; }
  if (d.stallion) { S.selStallion = S.selStallion === d.stallion ? null : d.stallion; save(); render(); return; }
  if (d.trip) { S.trip = d.trip; save(); render(); return; }
  if (d.pile) { drawPile(d.pile); save(); render(); BOARD.Sound.whinny(); return; }
  if (d.keep) { keepOffer(d.keep); save(); render(); return; }
  if (d.book) { S.book = +d.book; save(); render(); return; }
  if (d.auction) { openAuction(d.auction); BOARD.setInPlace("tatts-ring"); return; }
  if (d.plansel) { S.planSel = S.planSel === d.plansel ? null : d.plansel; render(); return; }
  if (d.plantarget) { if (S.planSel) { const h = horse(d.plantarget), r = RACES.find(x => x.id === S.planSel); setTarget(S.planSel, d.plantarget); S.planSel = null; render(); toast(`${h.name} targeted at the ${r.name}`); } return; }
  if (d.unplan) { setTarget(d.unplan, null); return; }
  if (d.planmore) { S.planOpen = S.planOpen === d.planmore ? null : d.planmore; render(); return; }
  if (d.selrace) { S.selRace = d.selrace; save(); render(); return; }
  if (d.card) { const h = horse(d.card); if (h) showHorseCard(h); return; }
  if (d.keepdev) {
    const F = S.foal; if (!F) return;
    const id = F.h.id; keepFoal(($("#foalName") || {}).value);
    const h = horse(id); if (!h) { render(); return; }
    while (h.age < +d.keepdev) develop(id);
    render(); showDevelop(h, 2); return;
  }
  if (d.develop) { const h = horse(d.develop); if (!h || S.step > 3 || atAscot()) return;   // training is over once you're at Ascot
    const from = h.age; develop(d.develop); render(); showDevelop(h, from); BOARD.Sound.hooves(2); return; }
  if (d.silks != null) { S.silks = +d.silks; save(); render(); if (menuOpen) paintMenu(true); return; }
  if (d.open) { S.open = S.open === d.open ? null : d.open; render(); return; }
  if (d.pick) { setEntry(d.race, d.pick); S.open = null; render(); const h = horse(d.pick); if (h) toast(`${h.name} entered in the ${RACES.find(r => r.id === d.race).name}`); return; }
  if (d.unpick) { setEntry(d.unpick, null); render(); return; }
  if (d.sim) { if (S.step !== 4 || !atAscot()) return; const i = +d.sim; simBusy = true; render(); simAndRecord(i).then(() => raceDone(i)).catch(err => toast(String(err.message || err))).finally(() => { simBusy = false; render(); }); return; }
  if (d.watch) { if (S.step !== 4 || !atAscot()) return; watch(+d.watch); return; }
  switch (t.id) {
    case "toMenu": openMenu(); break;
    case "snd": { const on = !BOARD.Sound.on; BOARD.Sound.set(on); t.setAttribute("aria-pressed", String(on)); $("#sndIcon").innerHTML = on ? ICON.speaker : ICON["speaker-off"]; break; }
    case "shClose": closeSheet(); break;
    case "breedBtn": { const s = stallion(S.selStallion); if (!s || s.fee > S.budget || stableFull() || pairProblem(s, byName(S.selMare))) break; breed(s.name, S.selMare, "bred", s.fee); save(); render(); BOARD.Sound.whinny(); break; }
    case "keep": keepFoal(($("#foalName") || {}).value); render(); break;
    case "closeDev": { const b = $("#devCard"); if (b) b.remove(); cardFrame = null; break; }
    case "changeMare": S.selMare = null; S.selStallion = null; save(); render(); sheetTop(); break;
    case "vjob": case "vplan": S.view = t.id.slice(1); render(); break;
    case "dealSkip": skipDeal(); break;
    case "dealNext": closeDeal(); break;
    case "toSale": S.confirmSale = true; render(); break;
    case "saleNo": S.confirmSale = false; render(); break;
    case "saleYes": if (S.step !== 1 || S.foal || S.offer) break;
      S.confirmSale = false; S.step = 2; S.book = 1; S.view = "job"; newCatalogue(); save();
      story("stud", "tatts", "sales", { procession: "yearlings" }); break;
    case "toEnter": if (S.step !== 2 || S.foal) break;
      S.step = 3; S.galloped = true; S.view = "job"; save();
      story("tatts", "jockey", "entries", { procession: "gallops" }); break;
    case "doneGallops": S.galloped = true; save(); story("warren", "jockey", "entries"); break;
    case "fill": fillEmpty(); render(); break;
    case "clear": S.entries = {}; save(); render(); break;
    case "toRaces": {
      const left = RACES.length - entered();
      if (left && !t.dataset.sure) { t.dataset.sure = "1"; t.innerHTML = `${left} empty: go anyway <span aria-hidden="true">›</span>`; toast(`${left} race${left === 1 ? " has" : "s have"} no runner. Tap again to go anyway.`); break; }
      S.galloped = true; goToAscot(); break; }
    case "toWeek": S.step = 4; UI.tab.jockey = null; save(); closeSheet({ quiet: true }); openSheet("races"); break;
    case "backEntries": if (racesRun()) break; S.step = 3; save(); closeSheet({ quiet: true }); openSheet("jockey", { tab: "entries" }); break;
    case "simAll": { simBusy = true; render();
      (async () => { for (const r of RACES) if (!S.results[r.id]) { await simAndRecord(r.i); raceDone(r.i, true); } })().catch(err => toast(String(err.message || err))).finally(() => { simBusy = false; render(); });
      break; }
    case "toResult": S.step = 5; save(); noteHonours(); render(); sheetTop(); BOARD.Sound.cheer(5); break;
    case "goHome": goHomeFromAscot(); break;
    case "again": freshSeason(); story("palace", "jockey", "draw"); break;
    case "replayTally": playTally(); break;
    case "copy": {
      const txt = $("#shareText").textContent;
      try { navigator.clipboard.writeText(txt).then(() => toast("Copied"), () => { selectShare(); toast("Selected. Copy it from here."); }); } catch (err) { selectShare(); toast("Selected. Copy it from here."); }
      break;
    }
    case "closeWatch": closeWatch(); break;
    case "menuContinue": leaveMenu(); break;
    case "menuNew": if (hasProgress() && !newArmed) { newArmed = true; paintMenu(true); break; }
      freshSeason(); newArmed = false; render(); paintMenu(true); if (!hasProgress()) toast("A new season is drawn"); break;
    case "aucBid": aucPlace("me"); break;
    case "aucLeave": aucLeave(); break;
    case "autoMinus": if (A) { A.auto = Math.max(openBid(A.l), A.auto - incFor(A.auto - 1)); aucPaint(); } break;
    case "autoPlus": if (A) { A.auto = Math.min(S.budget, A.auto + incFor(A.auto)); aucPaint(); } break;
    case "autoOn": if (A) { A.autoOn = !A.autoOn; aucPaint(); } break;
    case "simInstead": { const i = watching.i; closeWatch(); simAndRecord(i).then(() => raceDone(i)).catch(err => toast(String(err.message || err))).finally(render); break; }
  }
});
// after each race: a word on how your horse got on
function raceDone(i, quiet) {
  const r = RACES[i], res = S.results[r.id]; if (!res || quiet) return;
  if (res.pos === 1) { toast(`You've won the ${r.name}!`); BOARD.Sound.cheer(4); }
  else if (res.pos && res.pos <= 4) toast(`${ord(res.pos)} in the ${r.name}: ${money(res.prize)}`);
}
function selectShare() { const r = document.createRange(); r.selectNodeContents($("#shareText")); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }

addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (document.querySelector(".foal-wrap, .auc, .watch") || menuOpen || UI.cineOn) return;
  if (UI.sheet && !atAscot()) closeSheet();
});

/* ================= Starting up ================= */
document.body.insertAdjacentHTML("afterbegin", `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="pip" viewBox="0 0 40 40"><g fill="currentColor"><path d="M20 5 L35 20 L20 35 L5 20Z"/><circle cx="20" cy="3.6" r="3.2"/><circle cx="20" cy="36.4" r="3.2"/><circle cx="3.6" cy="20" r="3.2"/><circle cx="36.4" cy="20" r="3.2"/></g><circle cx="20" cy="20" r="4" fill="#fffdf7"/></symbol></svg>`);
function boot() {
  if (!load()) { newCard(); S.at = "newmarket"; save(); }
  BOARD.cardFor = cardFor;
  BOARD.onEnter = (id) => {
    const st = placeStates()[id];
    if (st === "locked") { toast(cardFor(id).status || "Not open yet"); return; }
    if (id === "races") {
      const ph = phase();
      if (ph === "week" || ph === "standings") { arriveAscot(false); return; }
      if (ph === "gallops" || ph === "entries") {
        const left = RACES.length - entered();
        if (left && !BOARD._sure) { BOARD._sure = true; $("#cardCta").textContent = `${left} empty: go anyway`; return; }
        BOARD._sure = false; S.galloped = true; goToAscot(); return;
      }
      return;
    }
    if (id === "warren" && phase() === "gallops") { /* the first visit counts as having been to the gallops */ }
    openSheet(id);
  };
  BOARD.onChoose = (id) => { BOARD._sure = false; document.body.classList.toggle("card-open", !!id); };
  render();
  openMenu();
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
