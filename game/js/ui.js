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
  draw:      { step: 1, place: "jockey", season: "Winter", title: W.programme, hour: 10.5,
               line: W.drawLine },
  team:      { step: 1, place: "jockey", season: "Winter", title: "Your team", hour: 11.5,
               line: "Draft your owner, trainer and jockeys: six points from the Bronze, Silver and Gold decks." },
  breed:     { step: 1, place: "stud", season: "Spring", title: "The covering season", hour: 8,
               line: "Draw your mares at the National Stud and send them to the stallions of your choice." },
  sales:     { step: 2, place: "tatts", season: "Autumn", title: "The Yearling Sales", hour: 11,
               line: "The mares nobody bred have sent their yearlings to Tattersalls. Bid for the best of them." },
  gallops:   { step: 3, place: "warren", season: "The next spring", title: "Into training", hour: 7,
               line: "Your string is in the yard as 2-year-olds. Up Warren Hill, your trainer gets them ready: trip, temperament, ground." },
  entries:   { step: 3, place: "jockey", season: "May", title: "Entries", hour: 9.5,
               line: W.entriesLine },
  week:      { step: 4, place: "races", season: W.when, title: W.weekTitle, hour: 9,
               line: W.weekLine },
  standings: { step: 5, place: "races", season: W.when, title: "The final standings", hour: 10, line: "" },
  home:      { step: 5, place: "palace", season: "Summer", title: "Home to Newmarket", hour: 6.2,
               line: `${W.titleFrom} hangs in Palace House.` },
};
const STEPS = [
  { n: 1, name: "The Stud", place: "stud" }, { n: 2, name: "The Sales", place: "tatts" }, { n: 3, name: "Entries", place: "jockey" },
  { n: 4, name: W.where, place: "races" }, { n: 5, name: "The Result", place: "palace" },
];
function phase() {
  if (!S.dealt) return "draw";
  if (S.step === 1 && !(teamOn() && S.team.gone)) return "team";
  if (S.step === 1) return "breed";
  if (S.step === 2) return "sales";
  // Warren Hill opens with the trainers (owner, 14 Nov): after the sales the string goes up the gallops first, where the
  // trainer's jobs are done and horses developed, then on to entries (a season begun before this had no gallops step)
  if (S.step === 3) return S.galloped ? "entries" : "gallops";
  if (S.step === 4) return "week";
  return S.home ? "home" : "standings";
}
const entered = () => RACES.filter(r => S.entries[r.id]).length;
const racesRun = () => RACES.filter(r => S.results[r.id]).length;
// prize money, with any Stud Master income (it counts with prize money, as on the board)
const prizeWon = () => RACES.reduce((a, r) => a + (S.results[r.id] ? S.results[r.id].prize : 0), 0) + teamIncome();
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
  const ORDER = ["draw", "team", "breed", "sales", "gallops", "entries", "week", "standings", "home"], after = (k) => ORDER.indexOf(ph) > ORDER.indexOf(k);
  st.jockey = "open"; st.palace = "open";
  st.stables = has ? "open" : "locked";
  st.stud = ph === "breed" ? "open" : after("breed") ? "done" : "locked";
  st.tatts = ph === "sales" || ph === "gallops" || ph === "entries" ? (S.sale.length || ph === "sales" ? "open" : "done") : after("entries") ? "done" : "locked";
  st.warren = ph === "gallops" || ph === "entries" ? "open" : after("entries") ? "done" : "locked";
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
      if (ph === "draw") { c.text = W.drawText; c.cta = "See the programme"; }
      else if (ph === "team") { c.text = `Draft your team: an owner, a trainer and jockeys, <b>${teamPoints()} of ${TEAM_POINTS}</b> points picked.`; c.cta = "Draft your team"; }
      else if (ph === "gallops" || ph === "entries") { c.text = `Make your entries: ${W.entryRule.toLowerCase()}. <b>${n} of ${RACES.length}</b> races have a runner.`; c.cta = "Make entries"; c.off = false; }
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
      const jl = typeof jobsLeft === "function" && teamOn() ? jobsLeft() : 0;
      if (st === "locked") { c.status = "Opens after the sales"; c.text = "Your trainer gets the string ready here: trip, temperament, ground and a tune-up for a big race. Horses are developed here too."; c.cta = "Go to the gallops"; }
      else if (st === "done") { c.status = "Training is over for this season"; c.text = `Your string has gone to ${W.venue}.`; c.cta = ""; }
      else { c.text = `${jl ? `Your trainer has <b>${jl}</b> job${jl === 1 ? "" : "s"} to spend. ` : ""}Develop a horse to 3 or 4 to change its rating and best trip. <b>${can}</b> of your ${S.stable.length} could still develop.`; c.cta = "Go to the gallops"; }
      break; }
    case "palace": {
      const weeks = pastWeeks().length;
      c.kicker = "The National Horseracing Museum";
      if (ph === "home") { const T = titleFor(prizeWon()); c.text = `${W.titleFrom} is waiting: <b>${T.name}</b>, with ${money(prizeWon())} in prize money.`; c.cta = "Visit Palace House"; }
      else { c.text = weeks ? `Your trophies and every ${W.playedNoun} you've played: <b>${weeks}</b> so far.` : "Your trophies and racing history, and how the game is played."; c.cta = "Visit Palace House"; }
      break; }
    case "races":
      c.kicker = `${W.where} · ${W.when}`;
      if (st === "locked") { c.status = W.lockedStatus; c.text = W.lockedText; c.cta = W.go; }
      else if (ph === "gallops" || ph === "entries") {
        c.text = `<b>${n} of ${RACES.length}</b> races have a runner. Once you leave for ${W.venue} your entries are lodged and the going is declared.`;
        c.cta = W.go;
        if (left) c.note = `<b>${left} race${left === 1 ? " has" : "s have"} no runner.</b> An empty race earns nothing.`;
      }
      else if (ph === "week") { c.text = `${W.weekRunning}: <b>${racesRun()} of ${RACES.length}</b> run, <b>${money(prizeWon())}</b> won.`; c.cta = W.back; }
      else if (ph === "standings") { c.text = "The final standings are in."; c.cta = W.back; }
      else { c.status = W.over; c.text = `You won ${money(prizeWon())} and ${winsNow()} race${winsNow() === 1 ? "" : "s"}.`; c.cta = ""; }
      break;
  }
  if (st === "next" && ch && ch.title) c.kicker = ch.title;   // no time of year on the labels (owner, 7 Nov: it is never winter at Royal Ascot)
  return c;
}

/* ================= The bar: where you are, your stable, your money ================= */
const UI = { sheet: null, tab: {}, story: null, cineOn: false };
function paintBar() {
  const ph = phase(), stepNow = CHAPTERS[ph].step;
  $("#brandWhere").textContent = atAscot() ? W.where : "Newmarket";
  $("#steps").innerHTML = STEPS.map(s => {
    const cls = s.n < stepNow || (s.n === 5 && ph === "home") ? "done" : s.n === stepNow ? "current" : "";
    return `<button class="st ${cls}" type="button" data-step="${s.n}" ${cls === "current" ? 'aria-current="step"' : ""} title="${s.name}"><b>${s.n}</b><span>${s.name}</span></button>`;
  }).join("");
  const n = S.stable.length;
  $("#tally").innerHTML = S.step <= 3
    ? `<span class="t-silk">${silkImg(mySilkN())}</span><span title="Horses in your stable"><svg viewBox="0 0 512 512">${ICON.stable}</svg><em>${n}</em><i>/${STABLE_CAP}</i></span><button type="button" class="t-money" data-accounts="1" title="Your budget: open your accounts"><svg viewBox="0 0 512 512">${ICON["two-coins"]}</svg><em>${money(S.budget)}</em></button>`
    : `<span class="t-silk">${silkImg(mySilkN())}</span><span title="Wins: ${winsNow()} from ${racesRun()} of ${RACES.length} races run"><svg viewBox="0 0 512 512">${ICON["laurels-trophy"]}</svg><em>${winsNow()}</em><i> win${winsNow() === 1 ? "" : "s"}</i></span><span class="t-money prize" title="Prize money won (a separate pot from your budget)"><svg viewBox="0 0 512 512">${ICON["trophy-cup"]}</svg><em>${money(prizeWon())}</em></span>`;
  fitBar(); refreshAccounts();
}
// if the five steps' names don't fit beside the tally (a narrow window, or the fonts still loading), only the
// current step keeps its name
function fitBar() {
  const st = $("#steps"); if (!st) return;
  st.classList.remove("tight");
  if (st.scrollWidth > st.clientWidth + 1) st.classList.add("tight");
}
addEventListener("resize", () => { fitBar(); footRoom(); });
// the message toast sits just above an open sheet's footer, never over its buttons (owner, 7 Nov: on a phone the
// stud's "targeted at the Gold Cup" covered "close the stud and go to the sales")
function footRoom() {
  const f = $("#go"), h = f && !f.hidden && UI.sheet ? f.getBoundingClientRect().height : 0;
  document.documentElement.style.setProperty("--foot-h", Math.round(h) + "px");
}
if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => fitBar());

/* ================= The board: the places' states, the card, the guide ================= */
function paintBoard() {
  if (!window.BOARD) return;
  BOARD.setStates(placeStates());
  BOARD.flyOwn(my3D());
  paintGuide();
  if (BOARD.chosen && !UI.sheet) BOARD.choose(BOARD.chosen);    // keep the open card's words up to date
}
function paintGuide() {
  const ph = phase(), ch = CHAPTERS[ph], nx = nextPlace(), p = BOARD.placeOf(nx), g = $("#guide");
  const what = {
    draw: "See the programme at the Jockey Club", team: "Draft your team at the Jockey Club", breed: "Breed your foals at the National Stud", sales: "Buy at the Yearling Sales, Tattersalls",
    gallops: "Bring your string on at Warren Hill", entries: nx === "races" ? `Every race has a runner: off to ${W.where}` : `Make your entries at the Jockey Club (${entered()} of ${RACES.length})`,
    week: W.weekTitle === "Royal Ascot" ? "Race week at Royal Ascot" : W.weekTitle, standings: W.standingsAt, home: "Collect your title at Palace House",
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
  if (procession && window.LIFE) { try { LIFE.procession(procession, { silk: my3D() }); } catch (e) { console.warn(e); } }
  BOARD.Sound.hooves && BOARD.Sound.hooves(3);
  if (from && to && from !== to) await BOARD.trail(from, to);
  if (UI.story !== run) return;
  if (then) { await then(); if (UI.story !== run) return; }
  BOARD.choose(nextPlace());
}

/* ================= Sheets: a place's screens over the board ================= */
const SHEET_TITLE = { jockey: "The Jockey Club", stud: "The National Stud", tatts: "Tattersalls", stables: "Your Stables", warren: "Warren Hill", palace: "Palace House", races: W.where };
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
  $("#shTitle").textContent = id === "races" ? (S.step >= 5 ? "Final standings" : W.where) : atAscot() && id === "jockey" ? "Declarations" : SHEET_TITLE[id];
  $("#shKicker").textContent = id === "races" ? `${MEETING.month} ${MEETING.year} · ${S.step >= 5 ? W.weekDone : W.weekWord}`
    : atAscot() && id === "jockey" ? `${MEETING.name} · change your runners before the first race`
    : (placeStates()[id] === "next" ? `Step ${ch.step} of 5 · ${ch.title}` : cardFor(id).kicker);
  const ic = PLACE_ICON[id];
  $("#shMedal").innerHTML = ic === "JC" ? `<span class="jc">JC</span>` : ic === "horse" ? `<span class="hz"></span>` : `<svg viewBox="0 0 512 512">${ICON[ic]}</svg>`;
  const pic = $("#shPic");
  if (id === "races" || atAscot()) { pic.style.backgroundImage = `url(${W.still})`; pic.style.backgroundSize = "cover"; pic.style.backgroundPosition = "50% 30%"; }
  else if (p) BOARD.paintPic(pic, [p.pic[0], p.pic[1], Math.max(560, Math.min(1000, (pic.clientWidth || 1200) * 0.72))], 0.7);
  $("#shClose").hidden = atAscot();
  $("#main").innerHTML = SHEETS[id]();
  $("#go").innerHTML = FOOTS[id] ? FOOTS[id]() : "";
  $("#go").hidden = !$("#go").innerHTML.trim();
  footRoom();
  if (id === "races" && S.step >= 5) resultAfter(prizeWon());
  if (id === "jockey" && UI.dealing && D) reattachDeal();
  body.scrollTop = keep;
}

/* ----- the sheets' bodies ----- */
const SHEETS = {
  jockey() {
    if (!S.dealt) return drawBody();
    if (phase() === "team" || UI.tab.jockey === "team") return (phase() === "team" ? "" : jockeyTabs("team")) + draftBody();
    const ph = phase(), canEnter = S.step >= 3 && S.step <= 4 && !racesRun();
    const tab = UI.tab.jockey || (canEnter && (ph === "entries" || ph === "gallops" || atAscot()) ? "entries" : "programme");
    const bar = jockeyTabs(tab);
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
    if (phase() === "team") { const T = teamState();
      return T.done ? `<span class="f-info ready">Your team is picked.</span>${goBtn("teamDone", "To the National Stud")}`
        : `<span class="f-info">${T.offer ? "Keep one of the three cards." : `${teamPoints()} of ${TEAM_POINTS} points picked. Choose a deck.`}</span>`; }
    if (atAscot()) return `<span class="f-info">Change your runners before the first race. The going is declared again when you go back.</span>${goBtn("toWeek", W.backToRacing)}`;
    const ph = phase();
    if (ph === "gallops" || ph === "entries") { const left = RACES.length - entered();
      return `<span class="f-info ${left ? "" : "ready"}">${left ? `${left} race${left === 1 ? "" : "s"} still without a runner.` : `All ${RACES.length} races have a runner.`}</span>${goBtn("toRaces", W.go)}`; }
    return "";
  },
  stud() {
    if (S.step !== 1) return "";
    return S.confirmSale
      ? `<span class="f-info"><b>Close the stud?</b> Once you go to Tattersalls you can't come back to breed.${S.hand.length ? ` Your ${S.hand.length} unused mare${S.hand.length === 1 ? "" : "s"} may turn up in the sale.` : ""}</span>${goBtn("saleNo", "Stay at the stud", { ghost: true })}${goBtn("saleYes", "Go to Tattersalls", { off: S.foal || S.offer })}`
      : `<span class="f-info">${studCount()} mare${studCount() === 1 ? "" : "s"} · ${S.stable.length} horse${S.stable.length === 1 ? "" : "s"} · <button type="button" class="f-acct" data-accounts="1">${money(S.budget)} left</button></span>${goBtn("toSale", handDone() ? "Close the stud and go to the sales" : "Draw your mares first", { off: S.foal || S.offer || !handDone() })}`;  },
  tatts() {
    // never a dead end: with no horse bought or bred you can still leave (and race nothing, or start again)
    if (S.step === 2) return `<span class="f-info">${S.stable.length} horse${S.stable.length === 1 ? "" : "s"} in your string · <button type="button" class="f-acct" data-accounts="1">${money(S.budget)} left</button></span>${goBtn("toEnter", S.stable.length ? "Leave the sales: on to entries" : "Leave the sales without a horse", { off: S.foal })}`;
    return "";
  },
  warren() {
    const ph = phase();
    if (ph === "gallops" || ph === "entries") { const jl = typeof jobsLeft === "function" && teamOn() ? jobsLeft() : 0;
      return `<span class="f-info">${jl ? `${jl} job${jl === 1 ? "" : "s"} left: spend ${jl === 1 ? "it" : "them"} now or keep ${jl === 1 ? "it" : "them"} for race week. ` : ""}The gallops stay open until you leave for ${W.venue}.</span>${ph === "gallops" ? goBtn("doneGallops", "Done on the gallops: on to entries") : ""}`; }
    return "";
  },
  palace() { return phase() !== "home" ? "" : isDaily()
    ? `<span class="f-info">That's ${S.day === ukDay() ? "today's" : "that day's"} card played: it counts once. A new card at midnight, and a random game any time.</span>${goBtn("again", "Play a random game")}`
    : `<span class="f-info">A new season: new races, new mares, the same ${money(START_BUDGET)}.</span>${goBtn("again", "Start a new season")}`; },
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
  return `<div class="tb-head"><p class="tb-lede">${W.lede === "Your ten races at Royal Ascot, two a day over five days" ? W.lede + ": Group races, Listed races and big handicaps." : W.lede} Each needs a minimum rating to run, and handicaps take horses rated ${HCAP_MAX} or less. ${going ? "The going has been declared." : W.goingWhen}</p></div>
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
  return `<div class="rf ${g.cls}"><div class="rf-top"><b>${g.short === "Hcap" ? "HANDICAP" : g.short === "Cond" ? "CONDITIONS" : r.grade.toUpperCase()}</b><span>${r.dist}${courseName(r) ? ` · ${courseName(r).split(" ")[0]}` : ""}</span></div>
    <div class="rf-n ${r.name.length > 24 ? "long" : ""}">${r.name}</div><div class="rf-f"><span>${ageOnly(r)} · ${r.sex === "C" ? "♂ Colts" : r.sex === "F" ? (r.ages[0] >= 4 ? "♀ F&M" : "♀ Fillies") : "⚥ Open"}</span><span>1st ${money(r.prizes[0])}</span></div></div>`;
}
const cardBack = (k, t) => `<div class="dc-back"><span>${k}<b>${t}</b></span></div>`;
function dealCard(face, backHTML, cls) { return `<div class="dc ${cls || ""}"><div class="dc-in">${backHTML}<div class="dc-face">${face}</div></div></div>`; }
function drawBody() {
  return `<div class="deal in-sheet" id="deal"><div class="deal-in">
      <div class="deal-head"><div><div class="deal-k" id="dealKicker">${seasonName()} · the draw</div><h2 class="deal-t" id="dealTitle">Your ten races</h2></div><button class="deal-skip" id="dealSkip" type="button">Skip</button></div>
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
  $("#dealBody").innerHTML = `<div class="dl-grid">${DAYS.map((d, k) => `<div class="dl-day"><h4>${dayTag(k)}</h4>
    ${RACES.filter(r => r.day === k).map(r => dealCard(raceFace(r), cardBack(W.cardBack, "Race"), GRADE[r.grade].cls)).join("")}</div>`).join("")}</div>`;
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
function closeDeal() {
  clearDeal(); D = null; UI.dealing = false; S.dealt = true; teamState(); save();
  // the team is drafted here at the Jockey Club before the stud opens (js/team.js)
  if (!(teamOn() && S.team.gone)) { paintBar(); paintBoard(); paintSheet(true); sheetTop(); return; }
  story("jockey", "stud", "breed");
}
// the Jockey Club's tabs (your team appears once it's picked)
function jockeyTabs(tab) {
  const ph = phase(), canEnter = S.step >= 3 && S.step <= 4 && !racesRun();
  const tabs = [["programme", "The programme"], ["plan", "Race planner"]].concat(canEnter ? [["entries", "Entries"]] : []).concat(teamOn() && !teamSkipped() ? [["team", "Your team"]] : []);
  return `<div class="vtabs" role="tablist">${tabs.map(([k, t]) => `<button class="vtab ${tab === k ? "on" : ""}" data-jtab="${k}" role="tab" aria-selected="${tab === k}">${t}${k === "entries" ? `<i>${entered()}/${RACES.length}</i>` : k === "plan" ? `<i>${RACES.filter(r => (S.targets || {})[r.id] && horse(S.targets[r.id])).length}/${RACES.length}</i>` : k === "team" ? `<i>${teamCards().length}</i>` : ""}</button>`).join("")}</div>`;
}

/* ----- National Stud and Tattersalls: the Ascot game's own screens (js/ui-parts.js), in the sheet ----- */

/* ----- Warren Hill: the gallops ----- */
function gallopsBody() {
  const young = S.stable.filter(h => h.age < 4), grown = S.stable.filter(h => h.age >= 4);
  if (!S.stable.length) return `<p class="tb-empty">No horses in training yet.</p>`;
  return `${trainerPanel()}<div class="tb-head"><p class="tb-lede">Every horse arrives as a 2-year-old. Work one up the hill to develop it to 3 or 4: its rating and best trip change, and you only see how once it's done. There's no going back, and a horse can only run in races for its age. The projected peak is the age it should be at its best.</p></div>
    <div class="gal-sum"><span><b>${young.length}</b> could still develop</span><span><b>${grown.length}</b> fully grown</span><span><b>${S.stable.filter(h => h.age === h.peakAge).length}</b> at their projected peak</span></div>
    ${horseCols(S.stable, null, true, { plan: true, train: true }, false)}`;
}

/* ----- Palace House: your trophies and your history ----- */
const HONOURS_KEY = "tb-" + MEETING.id + "-honours";
function honours() { try { const h = JSON.parse(localStorage.getItem(HONOURS_KEY) || "[]"); return Array.isArray(h) ? h : []; } catch (e) { return []; } }
function noteHonours() {
  try {
    const h = honours(); if (h.some(x => x.seed === S.seed)) return;
    RACES.forEach(r => { const res = S.results[r.id], hs = horse(S.entries[r.id]); if (res && res.pos === 1 && hs) h.push({ seed: S.seed, day: S.day || undefined, horse: hs.name, race: r.name, grade: r.grade, by: res.by, when: Date.now(), silks: mySilkN() }); });
    localStorage.setItem(HONOURS_KEY, JSON.stringify(h.slice(-300)));
  } catch (e) {}
}
function museumBody() {
  const ph = phase(), hist = pastWeeks().slice().sort((a, b) => b.prize - a.prize), counts = {}, best = bestWeek();
  hist.forEach(w => counts[w.title] = (counts[w.title] || 0) + 1);
  const hon = honours().slice().reverse();
  const T = ph === "home" ? titleFor(prizeWon()) : null;
  return `${T ? `<section class="trophy ${T.cls}"><div class="tr-k">${W.where} ${MEETING.year} · ${seasonName(S, true)}</div><div class="tr-t">${T.name}</div>
      <p>${T.note} ${money(prizeWon())} in prize money, ${winsNow()} win${winsNow() === 1 ? "" : "s"} from ${RACES.length} races.</p>
      <div class="tr-cup"><svg viewBox="0 0 512 512">${ICON["laurels-trophy"]}</svg></div></section>` : ""}
    <div class="tb-head"><p class="tb-lede">The National Horseracing Museum keeps every ${W.playedNoun} you've played: the titles you've won, your best ${MEETING.id === "royal-ascot" ? "weeks" : "seasons"} and the horses that won for you.</p></div>
    <section class="rec"><h2 class="tb-h2">YOUR TITLES</h2>
      <div class="rec-titles">${TITLES.map(t => `<div class="rt ${t.cls} ${counts[t.name] ? "got" : ""}"><b>${counts[t.name] ? "×" + counts[t.name] : "?"}</b><span>${t.name}</span><small>${t.min ? money(t.min) + "+" : "under " + money(TITLES[TITLES.length - 2].min)}</small></div>`).join("")}</div>
      ${best ? `<p class="rec-n">Your best ${MEETING.id === "royal-ascot" ? "week" : "season"}: <b>${money(best.prize)}</b> (${seasonName(best, true)}, ${best.wins} win${best.wins === 1 ? "" : "s"}).</p>` : ""}
    </section>
    ${hist.length ? `<section class="rec"><h2 class="tb-h2">${W.playedPlural}</h2><table class="rec-t"><thead><tr><th>#</th><th>Season</th><th>Prize money</th><th>Wins</th><th>Title</th></tr></thead><tbody>${hist.slice(0, 12).map((w, k) =>
        `<tr class="${w.seed === S.seed ? "me" : ""}"><td>${k + 1}</td><td>${w.day ? "Daily, " + dayText(w.day) : w.seed}</td><td><b>${money(w.prize)}</b></td><td>${w.wins}/${w.races}</td><td>${w.title}</td></tr>`).join("")}</tbody></table>
      <p class="rec-n">${hist.length} ${MEETING.id === "royal-ascot" ? "week" : "season"}${hist.length === 1 ? "" : "s"} played. Collect every title.</p></section>` : ""}
    ${hon.length ? `<section class="rec"><h2 class="tb-h2">ROLL OF HONOUR</h2><ul class="honours">${hon.slice(0, 30).map(x => `<li>${silkImg(x.silks || 0)}<b>${esc2(x.horse)}</b><span>${esc2(x.race)}</span><small>${esc2(x.grade)} · ${seasonName(x, true)}</small></li>`).join("")}</ul></section>` : ""}
    <section class="rec how"><h2 class="tb-h2">HOW THE SEASON GOES</h2><ol class="how-list">
      <li><b>The Jockey Club</b>: the ten races for ${W.whereLong} are drawn, and you draft your team: owner, trainer and jockey cards worth six points (Gold 3, Silver 2, Bronze 1).</li>
      <li><b>The National Stud</b>: buy mares (choose one of three each time) and send them to the stallions. A mare can be at most one star above her stallion; outcrosses breed best, the same family worst. Unproven stallions may be a star better or worse than they look.</li>
      <li><b>Tattersalls</b>: the yearlings out of the mares nobody bred are sold in three Books. Bid against five rival buyers; you see the pedigree, not the yearling, until it's yours.</li>
      <li><b>Warren Hill</b>: your trainer's jobs (trip work, settling a keen horse, ground work, a tune-up for a big race) and developing horses to 3 or 4.</li>
      <li><b>The Jockey Club</b>: enter ${W.entryRule.toLowerCase()}. Each step from its best trip costs 5; the going counts ${W.goingCounts} (+5 on a going it likes, down to −10 three steps off).</li>
      <li>${W.howRaces ? W.howRaces : "<b>Royal Ascot</b>: watch each race in 3D or sim it."} Rating, trip, going and pace decide it, and a horse's running style meets the pace of the race. Prize money is its own pot; the money you spent doesn't count against it.</li>
    </ol></section>`;
}

/* ================= Films between the places ================= */
// newmarket-arrive.mp4 is the owner's map clip played backwards: from the treetops down onto the board. Its last frame is
// the board itself (the board scaled by 0.706 and moved by (129.5, -23.6) in the 1280 x 720 frame), so the film is laid
// exactly over the live board as it lands, and fades into it.
const CLIP = { w: 1280, h: 720, k: 0.706, x: 129.5, y: -23.6 };
function boardRect() { const r = $("#stage").getBoundingClientRect(); return r; }
// rects are measured inside the film's box (which sits under the top bar when the film lands on the board)
function boxRect() { return $("#cine").getBoundingClientRect(); }
function clipRectOnBoard() {
  const o = boxRect(), b = boardRect(), s = b.width / 1448, f = s / CLIP.k;
  return { left: b.left - o.left - CLIP.x * f, top: b.top - o.top - CLIP.y * f, width: CLIP.w * f, height: CLIP.h * f,
    board: { left: b.left - o.left, top: b.top - o.top, right: b.right - o.left, bottom: b.bottom - o.top }, box: o };
}
function coverRect(w, h) {
  const o = boxRect(), W = o.width, H = o.height, k = Math.max(W / w, H / h);
  return { left: (W - w * k) / 2, top: (H - h * k) / 2, width: w * k, height: h * k };
}
const lerpRect = (a, b, u) => ({ left: a.left + (b.left - a.left) * u, top: a.top + (b.top - a.top) * u, width: a.width + (b.width - a.width) * u, height: a.height + (b.height - a.height) * u });
// play a film: from one framing to another; resolves when it ends (or is skipped)
// (owner, 7 Nov: the landing wobbled) The film itself is steadied and runs at 48 frames a second; its framing is now
// moved only when a new frame of the film is shown (requestVideoFrameCallback), with a transform, so the picture and its
// frame always move together instead of the frame gliding between the film's own steps.
function film(src, { from = "cover", to = "cover", caption = "", sound = false, fadeOut = true, fadeIn = true, poster } = {}) {
  return new Promise((done) => {
    const box = $("#cine"), v = $("#cineVid"), cap = $("#cineCap");
    const onBoard = from === "board" || to === "board";
    UI.cineOn = true; paintGuide();
    document.body.classList.toggle("filming", onBoard);
    box.hidden = false; box.className = "cine on" + (fadeIn ? " fade-in" : "") + (onBoard ? " under-bar" : "");
    cap.innerHTML = caption; cap.classList.remove("show");
    v.muted = !(sound && BOARD.Sound.on); v.src = src; if (poster) v.poster = poster;
    let finished = false, raf = 0, vfc = 0;
    const rectFor = (k) => k === "board" ? clipRectOnBoard() : coverRect(v.videoWidth || CLIP.w, v.videoHeight || CLIP.h);
    const W0 = CLIP.w, H0 = CLIP.h;
    Object.assign(v.style, { left: "0px", top: "0px", width: W0 + "px", height: H0 + "px", transformOrigin: "0 0" });
    const place = (r) => { v.style.transform = `translate3d(${r.left}px,${r.top}px,0) scale(${r.width / W0},${r.height / H0})`; };
    const end = () => {
      if (finished) return; finished = true; cancelAnimationFrame(raf); if (vfc && v.cancelVideoFrameCallback) v.cancelVideoFrameCallback(vfc);
      const close = () => { box.hidden = true; box.className = "cine"; v.removeAttribute("src"); v.load(); v.style.transform = ""; UI.cineOn = false; document.body.classList.remove("filming"); paintGuide(); done(); };
      if (fadeOut) { box.classList.add("fade-out"); document.body.classList.remove("filming"); setTimeout(close, 650); } else close();
    };
    const frame = (t) => {
      if (finished) return;
      const d = v.duration || 4, u = Math.min(1, t / d), e = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      const a = rectFor(from), b = rectFor(to), r = lerpRect(a, b, e); place(r);
      // landing on (or leaving) the board: clip the film to the board's frame, so the clip's dark edges never show
      if (onBoard) {
        const br = clipRectOnBoard(), bd = br.board, w = to === "board" ? e : 1 - e, ins = (x) => Math.max(0, x * w);
        box.style.setProperty("--clip", `inset(${ins(bd.top)}px ${ins(br.box.width - bd.right)}px ${ins(br.box.height - bd.bottom)}px ${ins(bd.left)}px)`);
        // the clip's last frame doesn't quite reach the board's top and bottom edges on a tall screen: let the board
        // show through there instead of the dark backing (owner, 7 Nov: a strip at the top on a phone)
        const gap = r.top > 0.5 || r.top + r.height < br.box.height - 0.5 || r.left > 0.5 || r.left + r.width < br.box.width - 0.5;
        box.classList.toggle("landing", to === "board" && (u > 0.86 || gap));
      }
      if (u > 0.15 && caption) cap.classList.add("show");
      if (u > 0.82 && caption) cap.classList.remove("show");
    };
    if (v.requestVideoFrameCallback) {
      const onFrame = (now, meta) => { frame(meta.mediaTime); vfc = v.requestVideoFrameCallback(onFrame); };
      vfc = v.requestVideoFrameCallback(onFrame);
    } else {
      const tick = () => { if (finished) return; frame(v.currentTime); raf = requestAnimationFrame(tick); };
      raf = requestAnimationFrame(tick);
    }
    $("#cineSkip").onclick = end;
    v.onended = end; v.onerror = end;
    v.onloadedmetadata = () => frame(0);
    const go = v.play(); if (go && go.catch) go.catch(() => { v.muted = true; v.play().catch(end); });
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
  // (the races' backdrop is the season's own still: Ascot's, or the Rowley Mile's for the Newmarket season)
  const there = () => { document.body.classList.remove("at-newmarket"); document.body.classList.add("at-ascot"); $("#ascot").hidden = false; $("#ascot").style.backgroundImage = `url(${W.still})`; paintBar(); paintGuide(); };
  // the Newmarket season has no film to the races: the racecourse is on the board, so the races simply open
  if (withFilm && W.film) {
    const f = film(W.film, { caption: `<span>${MEETING.month} ${MEETING.year}</span><b>${W.where}</b><i>Five days · ten races</i>`, sound: true, fadeIn: true, poster: W.still });
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
  await arriveNewmarket(!!W.film);           // home from Ascot by film; the Newmarket season never left
  story("races", "palace", "home");
}

/* ================= The cover ================= */
let menuOpen = false, newArmed = false;
const hasProgress = () => S.dealt || S.step > 1 || S.stable.length > 0 || S.budget !== startBudget();
function openMenu() {
  menuOpen = true; newArmed = false; const m = $("#menu"); m.hidden = false;
  paintMenu(); const v = $("#menuVid"); try { if (v && v.play && !v.dataset.still) v.play().catch(() => {}); } catch (e) {}
  const on = m.querySelector(".sw.on"), st = on && on.parentNode; if (st) st.scrollLeft = Math.max(0, on.offsetLeft - (st.clientWidth - on.offsetWidth) / 2);
}
function closeMenu() { menuOpen = false; $("#menu").hidden = true; const v = $("#menuVid"); try { v && v.pause(); } catch (e) {} }
function paintMenu(keepScroll) {
  const strip = $("#menu .swatches"), x = strip ? strip.scrollLeft : 0;
  // the Newmarket season's cover is a still of the Rowley Mile instead of the Ascot film
  const vid = $("#menuVid");
  if (W.coverPicture && vid && !vid.dataset.still) {
    vid.dataset.still = "1"; try { vid.pause(); } catch (e) {}
    vid.removeAttribute("autoplay"); vid.querySelectorAll("source").forEach(s => s.remove()); vid.poster = W.coverPicture; vid.load();
  }
  // the season on show (Royal Ascot or Newmarket), its words, and the switch between them
  document.querySelectorAll("#menu [data-season]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.season === MEETING.id)));
  if (W.coverKicker) $("#menuKick").textContent = W.coverKicker;
  $("#menuWord").textContent = W.gameTitle || "Ascot";
  if (W.coverLede) $("#menuLede").innerHTML = W.coverLede;
  if (W.coverRaces) $("#menuRaces").innerHTML = `<b>${W.coverRaces[0]}</b><span>${W.coverRaces[1]}</span>`;
  // your colours: made by you (js/colours.js), not chosen from the ready-made silks
  $("#menuCol").innerHTML = hasColours()
    ? `<div class="mc-big">${silkImg(MINE)}</div><div class="mc-h">Your colours</div><div class="mc-own"><span>${esc2(SilksPaint.describe(MY.spec))}</span><button class="mc-change" id="menuColours" type="button">Change your colours</button></div>`
    : `<div class="mc-big mc-none" aria-hidden="true"><span>?</span></div><div class="mc-h">Your colours</div><div class="mc-own"><span>Every owner races in their own colours. Make yours before your first runner.</span><button class="mc-change" id="menuColours" type="button">Make your colours</button></div>`;
  if (keepScroll) { const s2 = $("#menu .swatches"); if (s2) s2.scrollLeft = x; }
  const counts = {}; pastWeeks().forEach(w => counts[w.title] = (counts[w.title] || 0) + 1);
  $("#menuTitles").innerHTML = TITLES.map(t => `<li class="${t.cls} ${counts[t.name] ? "got" : ""}"><b data-n="${counts[t.name] ? "✓ ×" + counts[t.name] : ""}">${t.name}</b><span>${t.min ? money(t.min).replace(",000,000", "m").replace(/,000$/, "k") + "+" : "under " + money(TITLES[TITLES.length - 2].min).replace(/,000$/, "k")}</span></li>`).join("");
  const b = bestWeek(); $("#menuBest").innerHTML = b ? `Your best ${W.bestWord}: <b>${money(b.prize)}</b> · ${titleFor(b.prize).name}` : "";
  if (window.lbShow) lbShow();   // the leaderboard panel: the standings and your position
  // Two ways to play (owner, 13 Nov): today's card, the same season for everyone and played once, or a random game
  const today = ukDay(), done = dailyDone(today), ds = dailySave(), dsToday = ds && ds.day === today ? ds : null;
  const stepOf = x => { const k = Math.min(5, x.step || 1); return `Step ${k} of 5`; };
  const rnd = isDaily() ? randomSave() : (hasProgress() ? S : null);
  const daily = done
    ? `<button class="tb-btn" id="menuDaily">Today's card: ${money(done.prize)}<small>${done.title} · played ${dayText(today)} · a new card at midnight</small></button>`
    : dsToday && (dsToday.dealt || dsToday.step > 1)
      ? `<button class="tb-btn" id="menuDaily">Continue today's card<small>${dayText(today, true)} · ${stepOf(dsToday)}</small></button>`
      : `<button class="tb-btn" id="menuDaily">Play today's card<small>${dayText(today, true)} · the same races for everyone · one go</small></button>`;
  const random = rnd
    ? `<button class="tb-btn ghost" id="menuRandom">Random game<small>Continue · ${stepOf(rnd).toLowerCase()}</small></button><button class="tb-btn ghost" id="menuNew">${newArmed ? "Tap again to confirm" : "New random game"}<small>${newArmed ? "Season " + rnd.seed + " will be lost" : "New races and mares"}</small></button>`
    : `<button class="tb-btn ghost" id="menuRandom">Play a random game<small>Any time, as often as you like</small></button>`;
  $("#menuGo").innerHTML = daily + random;
}
// the saved random game, if it has been started (read without opening it)
function randomSave() { try { const v = JSON.parse(localStorage.getItem(slotKey("random")) || "null"); return v && v.seed && (v.dealt || v.step > 1 || (v.stable || []).length || v.budget !== START_BUDGET) ? v : null; } catch (e) { return null; } }
// a new season from the cover or Palace House: whatever was open goes, and the season starts at Newmarket
function clearTable() {
  if (A) { clearInterval(A.timer); cancelAnimationFrame(A.raf); A.box.remove(); A = null; document.body.style.overflow = ""; }
  closeSheet({ quiet: true }); clearDeal(); D = null; UI.dealing = false; UI.tab = {}; UI.story = null;
}
function freshSeason(day) {
  clearTable();
  newCard(day ? dailySeed(day) : 0, day); S.at = "newmarket"; save();
}
// From the cover: open today's card (started now if it hasn't been; a finished one opens on its result; an unfinished
// card from an earlier day is put away), or the random game. The game not being played stays saved as it was.
function playDaily() {
  const today = ukDay(), ds = dailySave(), silks = S.silks;
  if (isDaily() && S.day === today) return;
  clearTable();
  if (ds && ds.day === today && load("daily")) { save(); return; }
  newCard(dailySeed(today), today); S.silks = silks; S.at = "newmarket"; save();
}
function playRandom() {
  if (!isDaily()) return;
  const silks = S.silks; clearTable();
  if (!load("random")) { newCard(); S.silks = silks; S.at = "newmarket"; }
  save();
}
// Switching season: each is its own game (rules, save, history), so the page opens afresh on the other one's cover
document.addEventListener("click", e => {
  const b = e.target.closest && e.target.closest("#menu [data-season]"); if (!b || b.dataset.season === MEETING.id) return;
  try { localStorage.setItem("tb-season", b.dataset.season); } catch (err) {}
  location.href = location.pathname + "?season=" + b.dataset.season;
});
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
document.addEventListener("change", e => {
  const t = e.target, d = t.dataset || {};
  if (t.id === "sort") { S.sort = t.value; save(); render(); return; }
  // your team (js/team.js): a stallion for an owner's card, a trainer card on a horse, a jockey booked for a race
  if (d.ask) { if (t.value && askExpert(t.value)) { const x = stallion(t.value); toast(`Your expert: ${x.name} is really a ${x.trueStars}★ stallion`); } render(); return; }
  if (d.tune) { const h = horse(d.tune), r = raceOf(t.value); if (h && r && doJob("tune", h, { race: r.id })) toast(`${h.name} is tuned up for the ${r.name}: +${tuneBoost(h, r)} there`); render(); return; }
  if (d.bookrace) { if (!bookJockey(d.bookrace, t.value)) toast("He has no rides left"); render(); return; }
});
document.addEventListener("click", e => {
  const t = e.target.closest("button"); if (!t || t.disabled) return;
  const d = t.dataset;
  if (d.guide) { BOARD.choose(d.guide); return; }
  if (d.step) { const s = STEPS.find(x => x.n === +d.step); if (s && !atAscot()) BOARD.choose(s.n === CHAPTERS[phase()].step ? nextPlace() : s.place); return; }
  if (d.jtab) { UI.tab.jockey = d.jtab; render(); sheetTop(); return; }
  if (d.deck) { const [role, tier] = d.deck.split(":"), code = drawDeck(role, +tier); if (code) { UI.drew = Date.now(); render(); sheetTop(); BOARD.Sound.chime && BOARD.Sound.chime(); toast(`${cardName(teamCard(code))} joins your team`); } return; }
  if (d.keepcard) { const c = teamCard(d.keepcard); keepTeamCard(d.keepcard); toast(`${cardName(c)} joins your team`); render(); sheetTop(); return; }
  if (d.own) { if (ownStallion(d.own)) toast(`${d.own} is your own stallion: ${OWNED_FREE} free nominations`); render(); return; }
  if (d.claim) { claimLot(d.claim); render(); return; }
  if (d.accounts) { toggleAccounts(); return; }
  if (d.job) { const h = horse(d.h), k = d.job, o = { dir: d.dir ? +d.dir : undefined, side: d.side, race: d.race };
    if (h && doJob(k, h, o)) { const j = jobsAll()[jobsAll().length - 1];
      toast(k === "trip" ? `${h.name}: best trip now ${tripText(tripAt(h, h.age))}` : k === "settle" ? `${h.name} has learned to settle` : k === "ground" ? `${h.name} now handles ${j.add.join(" and ")} too` : k === "tune" ? `${h.name} is tuned up: +${tuneBoost(h, raceOf(o.race))} in the ${raceOf(o.race).name}` : `Your trainer has looked ${h.name} over`); }
    render(); return; }
  if (d.unjob) { if (undoJob(+d.unjob)) toast("Job undone"); render(); return; }
  if (d.scoutrace) { scoutPick(d.scoutrace); render(); return; }
  if (d.scout) { if (briefScout()) { const n = (S.team.scout.found || []).length; toast(n ? `Your scout has found ${n === 1 ? "a lot" : n + " lots"} for your races` : "Your scout has your races"); } render(); return; }
  if (d.agent) { handBack(); render(); return; }
  if (d.stab) { UI.tab.stables = d.stab; render(); sheetTop(); return; }
  if (d.tab) { S.tab = d.tab; save(); render(); return; }
  if (d.mare) { if (S.selMare !== d.mare) { S.selMare = d.mare; S.selStallion = null; save(); render(); sheetTop(); } return; }
  if (d.stallion) { S.selStallion = S.selStallion === d.stallion ? null : d.stallion; save(); render(); return; }
  if (d.trip) { S.trip = d.trip; save(); render(); return; }
  if (d.pile) { drawPile(d.pile); save(); render(); BOARD.Sound.whinny(); return; }
  if (d.mdraw) { const n = d.mdraw === "all" ? (dealHand(), null) : drawHandMare(d.mdraw); UI.mareDrew = n;
    if (n) { const m = byName(n); toast(`${m.name} (${m.stars}★) joins your stud`); }
    if (handDone()) setTimeout(() => toast("Your mares are in. Tap one to send her to a stallion"), n ? 1600 : 0);
    render(); BOARD.Sound.whinny && BOARD.Sound.whinny();
    const f = document.querySelector(".hc.flipin"); if (f) f.scrollIntoView({ block: "center", behavior: "smooth" }); return; }
  if (d.keep) { keepOffer(d.keep); save(); render(); return; }
  if (d.upmare) { UI.sendBack = null; if (upgradeMare(d.upmare)) { render(); const o = document.getElementById("offer"); if (o) o.scrollIntoView({ block: "start", behavior: "smooth" }); } return; }
  if (d.sendback) { if (UI.sendBack !== d.sendback) { UI.sendBack = d.sendback; UI.handOpen = true; render(); return; }
    UI.sendBack = null; const back = sendBack(d.sendback); if (back) toast(`${d.sendback} goes back: ${money(back)} for Tattersalls`); render(); return; }
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
    case "breedBtn": { const s = stallion(S.selStallion); if (!s || feeFor(s) > S.budget || stableFull() || pairProblem(s, byName(S.selMare))) break; breed(s.name, S.selMare, "bred", feeFor(s)); save(); render(); BOARD.Sound.whinny(); break; }
    case "keep": keepFoal(($("#foalName") || {}).value); render(); break;
    case "closeDev": { const b = $("#devCard"); if (b) b.remove(); cardFrame = null; break; }
    case "changeMare": S.selMare = null; S.selStallion = null; save(); render(); sheetTop(); break;
    case "vjob": case "vplan": S.view = t.id.slice(1); render(); break;
    case "dealSkip": skipDeal(); break;
    case "dealNext": closeDeal(); break;
    case "teamDone": if (teamOn()) { S.team.gone = true; UI.tab.jockey = null; save(); story("jockey", "stud", "breed"); } break;
    case "toSale": S.confirmSale = true; render(); break;
    case "saleNo": S.confirmSale = false; render(); break;
    case "saleYes": if (S.step !== 1 || S.foal || S.offer) break;
      // a Stud Master who hasn't chosen gets a stallion picked for him
      S.confirmSale = false; S.step = 2; S.book = 1; S.view = "job"; newCatalogue(); save();
      story("stud", "tatts", "sales", { procession: "yearlings" }); break;
    case "toEnter": if (S.step !== 2 || S.foal) break;
      S.step = 3; S.galloped = false; S.view = "job"; save();
      story("tatts", "warren", "gallops", { procession: "gallops" }); break;
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
    case "again":
      // after the daily card, the random game: the one in progress if there is one, a new one if not
      if (isDaily()) { playRandom(); if (hasProgress() && !S.home) { render(); leaveMenu(); break; } }
      freshSeason(); story("palace", "jockey", "draw"); break;
    case "replayTally": playTally(); break;
    case "copy": {
      const txt = $("#shareText").textContent;
      try { navigator.clipboard.writeText(txt).then(() => toast("Copied"), () => { selectShare(); toast("Selected. Copy it from here."); }); } catch (err) { selectShare(); toast("Selected. Copy it from here."); }
      break;
    }
    case "closeWatch": closeWatch(); break;
    case "menuContinue": if (needColours(() => leaveMenu())) break; leaveMenu(); break;
    case "menuDaily": if (needColours(() => $("#menuDaily").click())) break; playDaily(); newArmed = false; render(); leaveMenu(); break;
    case "menuRandom": if (needColours(() => $("#menuRandom").click())) break; playRandom(); newArmed = false; render(); leaveMenu(); break;
    case "menuNew": if (!newArmed) { newArmed = true; paintMenu(true); break; }
      playRandom(); freshSeason(); newArmed = false; render(); paintMenu(true); toast("A new random season is drawn"); break;
    case "aucBid": aucPlace("me"); break;
    case "aucLeave": aucLeave(); break;
    case "autoMinus": if (A) { A.auto = Math.max(openBid(A.l), A.auto - incFor(A.auto - 1)); aucPaint(); } break;
    case "autoPlus": if (A) { A.auto = Math.min(canBidTo(), A.auto + incFor(A.auto)); aucPaint(); } break;
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
  // open on the game last played; a daily card from an earlier day comes back only if it was finished (its result)
  const dsv = lastMode() === "daily" ? dailySave() : null;
  if (!(dsv && (dsv.day === ukDay() || Object.keys(dsv.results || {}).length === RACES.length) && load("daily")) && !load("random")) { newCard(); S.at = "newmarket"; save(); }
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
