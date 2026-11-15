// =====================================================================================================================
// Entries as one step (owner, 15 Nov evening: "The trainer and entries need consolidating .. we also need to see clearly
// what horses need developing for their various entries .. which horses we can train .. once a horse is entered it
// moves down to the entered section at the bottom"). After the sales the string goes straight to the Jockey Club. Each
// race still to fill, in day order, shows the horse for it (your flag first, else the best that could run) and what it
// needs: develop to an age, a job from your trainer (trip work to get it in, a tune-up to lift it), then Enter. Entered
// races fold into the Entered section at the foot. Uses the planner's judgement (js/plan.js: pnOpt, pnFits, pnStars).
// =====================================================================================================================

const enOrder = () => RACES.slice().sort((a, b) => a.day - b.day || a.i - b.i);
// the horses that could run in a race, best first, leaving out any already entered in a race that rules this one out
// (flagged here first, then horses not flagged for another race still to fill, then the best: a horse flagged elsewhere
// is only suggested when nothing else can run, so a "develop to 4" here never quietly wrecks its own flagged race)
const enFlaggedElsewhere = (h, r) => RACES.some(x => x !== r && !S.entries[x.id] && pnFlagged(h, x));
const enFits = r => pnFits(r).filter(x => S.entries[r.id] === x.h.id || !clashFor(x.h, r))
  .map((x, k) => ({ ...x, k, w: pnFlagged(x.h, r) ? 0 : enFlaggedElsewhere(x.h, r) ? 2 : 1 })).sort((a, b) => a.w - b.w || a.k - b.k);
// a trainer with jobs to spend (Plus)
const enTrainerOn = () => typeof teamOn === "function" && teamOn() && !teamSkipped() && trainerCards().length > 0;

// the top of By race and By horse: where you stand, your trainer and where his jobs would help, and the next step
function enState() {
  const order = enOrder(), todo = order.filter(r => !S.entries[r.id]), done = order.filter(r => S.entries[r.id]);
  const items = todo.map(r => ({ r, fits: enFits(r) }));
  // every place a trainer's job would help: the horse shown for each race, and any horse flagged for it
  const jobs = items.flatMap(x => x.fits.filter((f, k) => (k === 0 || pnFlagged(f.h, x.r)) && (f.o.v === "t" || f.o.tune)).map(f => ({ r: x.r, h: f.h, o: f.o })));
  const needDev = items.filter(x => x.fits[0] && x.fits[0].o.age > x.fits[0].h.age).length;
  return { todo, done, items, jobs, needDev };
}
function enTop() {
  const { todo, done, jobs, needDev } = enState(), helps = jobs.length;
  return `<div class="en-steps" aria-label="The steps"><span class="${needDev ? "on" : "ok"}"><b>1</b>Develop</span><i aria-hidden="true">›</i>${enTrainerOn() ? `<span class="${jobsLeft() && helps ? "on" : "ok"}"><b>2</b>Train</span><i aria-hidden="true">›</i>` : ""}<span class="${todo.length ? "on" : "ok"}"><b>${enTrainerOn() ? 3 : 2}</b>Enter</span>${enJockeysOn() ? `<i aria-hidden="true">›</i><span class="${todo.length ? "" : "on"}"><b>${enTrainerOn() ? 4 : 3}</b>Jockeys</span>` : ""}<i aria-hidden="true">›</i><span><b>${3 + (enTrainerOn() ? 1 : 0) + (enJockeysOn() ? 1 : 0)}</b>${esc2(W.where)}</span></div>
    <div class="en-sum"><span class="${todo.length ? "need" : "ok"}"><b>${done.length} of ${RACES.length}</b> entered</span>${needDev ? `<span><b>${needDev}</b> need${needDev === 1 ? "s" : ""} developing</span>` : ""}${enTrainerOn() && helps ? `<span><i class="pn-tr xs" aria-hidden="true"></i><b>${helps}</b> a trainer job would help</span>` : ""}
      <span class="en-btns"><button class="tb-btn ghost sm" id="fill" type="button">Fill empty races</button>${done.length ? `<button class="tb-btn ghost sm" id="clear" type="button">Clear</button>` : ""}</span></div>
    ${enTrainer(jobs)}
    ${enJockeysOn() && done.length ? `<p class="en-next"><b>Last step before the races:</b> book your jockeys. <button class="tb-btn sm" type="button" data-pnv="jockeys">Jockeys ›</button></p>` : ""}`;
}
function enBody() {
  const { todo, done, items } = enState();
  return `${enTop()}
    <section class="en-sec"><h2 class="en-h">To enter <b>${todo.length}</b></h2>
      ${items.length ? items.map(enRace).join("") : `<p class="en-all">Every race has a runner.${enJockeysOn() ? " Book your jockeys, then go racing." : " Go racing!"}</p>`}</section>
    ${done.length ? `<section class="en-sec en-done"><h2 class="en-h">Entered <b>${done.length}</b></h2>${done.map(enIn).join("")}</section>` : ""}`;
}

// your trainer: his jobs left, and a plain list of where they would help (owner, 15 Nov: "much much clearer who trainers
// can be applied to"): each horse, its race, the job, and its stars before and after
function enTrainer(jobs) {
  if (!enTrainerOn()) return "";
  const rowsAll = jobs.map(({ r, h, o }) => {
    const before = o.v === "t" ? null : o.v, after = o.v === "t" ? o.tv : o.tune.v, dev = o.age > h.age;
    const what = o.v === "t" ? `Trip work, ${o.dir > 0 ? "longer" : "shorter"}: gets ${pnHe(h).o} in` : `Tune-up +${o.tune.b}`;
    const btn = o.v === "t" ? (dev ? `<button class="tb-btn ghost sm" type="button" data-devto="${h.id}:${o.age}">Develop to ${o.age} first</button>` : `<button class="tb-btn sm pn-gold" type="button" data-job="trip" data-h="${h.id}" data-dir="${o.dir}">Do it</button>`)
      : `<button class="tb-btn sm pn-gold" type="button" data-job="tune" data-h="${h.id}" data-race="${r.id}">Do it</button>`;
    return `<li><button class="en-face sm" type="button" data-card="${h.id}">${pnFace(h, "sm")}</button>
      <span class="en-tjw"><b>${esc2(h.name)}</b><small>${raceTag(r)} · ${esc2(dayTag(r.day))}${dev ? ` · develop to ${o.age}` : ""}</small></span>
      <span class="en-tjd">${what}</span>
      <span class="en-tjs">${before ? pnStars(before, "sm") : `<i class="pn-x sm" aria-label="Can't run"></i>`}<span aria-hidden="true">→</span>${pnStars(after, "sm")}</span>${btn}</li>`; });
  // the two that matter most first; the rest fold away so the races stay near the top of a phone
  const rows = rowsAll.slice(0, 2).join("") + (rowsAll.length > 2 ? `</ul><details class="en-tmore"><summary>Show ${rowsAll.length - 2} more</summary><ul class="en-tjobs">${rowsAll.slice(2).join("")}</ul></details><ul class="en-tjobs">` : "");
  return `<section class="en-tr"><div class="en-trh"><i class="pn-trface" aria-hidden="true"></i><div class="en-trt"><b>Your trainer: ${trainerCards().map(c => esc2(cardName(c))).join(" · ")}</b>${jobTokens()}</div></div>
    ${!jobsLeft() ? `<p class="en-trn">All his jobs are spent.</p>` : rows ? `<p class="en-trn"><b>Where a job would help:</b></p><ul class="en-tjobs">${rows}</ul>` : `<p class="en-trn">No race below needs a trip-work or tune-up job right now.</p>`}
    <p class="en-trn sm">Settling a keen horse, ground work and his eye are at <button class="pn-how" type="button" data-gowarren="1">Warren Hill ›</button></p></section>`;
}

const enHead = r => { const g = GRADE[r.grade];
  return `<div class="en-rh"><span class="en-day">${esc2(dayTag(r.day))}</span><span class="pn-rname">${esc2(r.name)}</span><span class="g ${g.cls}">${g.short}</span></div>
    <div class="en-rm">${pnDistNeed(r)}<span class="pn-agel">${esc2(r.ageLabel)}</span><span class="pn-agel">1st ${money(r.prizes[0])}</span></div>`; };

function enRace({ r, fits }) {
  const main = fits[0], rest = fits.slice(1);
  return `<article class="en-race ${main ? "" : "none"}" data-enrace="${r.id}">${enHead(r)}
    ${main ? enHorse(main.h, r, main.o) : `<p class="en-none">None of your horses can run here${S.stable.some(h => !h.age || h.age < r.ages[0]) ? " yet" : ""}. An empty race earns nothing.</p>`}
    ${rest.length ? `<details class="en-more"><summary>${rest.length} other${rest.length === 1 ? "" : "s"} could run</summary>${rest.map(x => enHorse(x.h, r, x.o)).join("")}</details>` : ""}
  </article>`;
}

// one horse for one race: where it stands, what it needs, and the buttons to do it
function enHorse(h, r, o) { return enAct(h, r, o, "horse"); }
// head: "horse" (in a race's list: the horse's face and name) or "race" (in a horse's list: the race's name, grade, trip)
function enAct(h, r, o, head) {
  const p = pnHe(h), flagged = pnFlagged(h, r), now = check(h, r), ready = now && now.ok;
  const dev = o.age > h.age, trip = o.v === "t", stars = trip ? o.tv : o.v, at = o.c;
  let say;
  if (trip) say = `Outside ${p.p} best trip (${tripText(tripAt(h, o.age))}). Trip work from your trainer gets ${p.o} in${dev ? ` once developed to ${o.age}` : ""}: ${ord(at.rank)} of ${at.of} on ratings.`;
  else if (dev) say = `Develop to ${o.age}: rated <b>${ratingAt(h, h.age)} → ${ratingAt(h, o.age)}</b>, best ${tripText(tripAt(h, o.age))}. Then rated <b>${at.day}</b> in this race (top class ${r.bands[0]}+), ${ord(at.rank)} of ${at.of}.`;
  else if (ready) say = `Ready as a ${h.age}-year-old: rated <b>${now.day}</b> in this race (top class ${r.bands[0]}+)${now.steps ? `, −${now.steps * 5} for the trip` : ""}, ${ord(now.rank)} of ${now.of}.`;
  else say = esc2(now.why || "Can't run as he is");
  if (o.tune) say += ` A tune-up (+${o.tune.b}) would make ${p.o} ${ord(o.tune.rank)}.`;
  const other = RACES.find(x => x !== r && pnFlagged(h, x) && !S.entries[x.id]);
  const btns = [];
  if (dev) btns.push(trip ? `<button class="tb-btn ghost sm" type="button" data-devto="${h.id}:${o.age}"><i class="pn-up" aria-hidden="true"></i>Develop to ${o.age}</button>`
    : `<button class="tb-btn sm" type="button" data-enterdev="${h.id}:${o.age}:${r.id}"><i class="pn-up" aria-hidden="true"></i>Develop to ${o.age} and enter</button>`);
  if (trip && !dev) btns.push(pnCanTrain() ? `<button class="tb-btn sm pn-gold" type="button" data-job="trip" data-h="${h.id}" data-dir="${o.dir}"><i class="pn-trface" aria-hidden="true"></i>Trip work: ${o.dir > 0 ? "longer" : "shorter"}</button>` : `<span class="pn-ready amber">Needs trip work: no trainer job left</span>`);
  if (o.tune) btns.push(`<button class="tb-btn sm pn-gold" type="button" data-job="tune" data-h="${h.id}" data-race="${r.id}"><i class="pn-trface" aria-hidden="true"></i>Tune-up +${o.tune.b} ${pnStars(o.tune.v, "sm")}</button>`);
  if (!dev && ready) btns.push(`<button class="tb-btn sm en-go" type="button" data-pick="${h.id}" data-race="${r.id}">Enter</button>`);
  const top = head === "race"
    ? `<div class="en-hn"><span class="en-day">${esc2(dayTag(r.day))}</span><b class="en-rn">${esc2(r.name)}</b><span class="g ${GRADE[r.grade].cls}">${GRADE[r.grade].short}</span>${pnDistNeed(r)}${flagged ? `<span class="en-flag">${PN_FLAG}Your flag</span>` : `<span class="en-flag off">Best fit, not flagged</span>`}</div>`
    : `<div class="en-hn"><button type="button" class="pn-nm" data-card="${h.id}">${esc2(h.name)}</button>${flagged ? `<span class="en-flag">${PN_FLAG}Your flag</span>` : ""}</div>`;
  return `<div class="en-h1 ${flagged ? "fl" : ""} ${head === "race" ? "byr" : ""}">
    ${head === "race" ? "" : `<button class="en-face" type="button" data-card="${h.id}" aria-label="Open ${esc2(h.name)}'s card">${pnFace(h)}</button>`}
    <div class="en-hb">${top}
      <div class="en-tags"><span class="en-st v${stars}">${pnStars(stars, "sm")}<b>${["", "Outside", "Good", "Strong"][stars]}</b></span>${dev ? `<span class="en-dev"><i class="pn-up" aria-hidden="true"></i>Needs developing to ${o.age}</span>` : ready ? `<span class="en-rdy">✓ Ready now</span>` : ""}${trip ? `<span class="en-tj"><i class="pn-tr xs" aria-hidden="true"></i>Needs trip work</span>` : o.tune ? `<span class="en-tj"><i class="pn-tr xs" aria-hidden="true"></i>A tune-up lifts ${pnHe(h).o} to ${["", "Outside", "Good", "Strong"][o.tune.v]}</span>` : ""}</div>
      <p class="en-say">${say}</p>
      ${other ? `<p class="en-also">Also flagged for the ${raceTag(other)}: it can only run once.</p>` : ""}
      <div class="en-acts">${btns.join("")}</div></div>
  </div>`;
}

// an entered race: the runner, its standing, its jockey, and a way to take it out
function enIn(r) {
  const h = horse(S.entries[r.id]), c = h && check(h, r), g = GRADE[r.grade];
  if (!h) return "";
  return `<div class="en-in">
    <span class="en-day">${esc2(dayTag(r.day))}</span>
    <div class="en-inb"><div class="en-inr"><b>${esc2(r.name)}</b><span class="g ${g.cls}">${g.short}</span>${pnDistNeed(r)}</div>
      <div class="en-inh"><button class="en-face sm" type="button" data-card="${h.id}">${pnFace(h, "sm")}</button><button type="button" class="pn-nm" data-card="${h.id}">${esc2(h.name)}</button>
        ${c && c.ok ? `${rkChip(c)}<small class="rk-t">${rankText(c)}${teamNote(c)}</small>` : `<small class="en-warn">${esc2((c && c.why) || "Can't run")}</small>`}</div>
      ${enJockeysOn() ? `<small class="enj-now">${bookedFor(r) ? `Jockey: <b>${esc2(cardName(bookedFor(r)))}</b>` : `No jockey booked yet: <button class="pn-how" type="button" data-pnv="jockeys">Jockeys ›</button>`}</small>` : ""}</div>
    <button class="tb-btn ghost sm" type="button" data-unpick="${r.id}">Take out</button>
  </div>`;
}

// develop a horse to an age and enter it in one go; Warren Hill from entries
document.addEventListener("click", e => {
  const t = e.target.closest && e.target.closest("[data-enterdev],[data-gowarren]"); if (!t) return;
  const d = t.dataset;
  if (d.gowarren) { e.stopPropagation(); closeSheet({ quiet: true }); openSheet("warren"); return; }
  const [hid, a, rid] = d.enterdev.split(":"), h = horse(hid), r = RACES.find(x => x.id === rid); if (!h || !r || !canDev(h)) return;
  e.stopPropagation();
  const from = h.age; while (h.age < +a) develop(hid);
  const T = pnFlags(), lost = RACES.filter(x => T[x.id] === hid && h.age > x.ages[1]); lost.forEach(x => { delete T[x.id]; });
  if (check(h, r).ok) { setEntry(r.id, hid); toast(`${h.name} developed to ${h.age} and entered in the ${r.name}`); }
  else toast(`${h.name} developed to ${h.age}, but can't run in the ${r.name} yet`);
  save(); render(); showDevelop(h, from); BOARD.Sound.hooves && BOARD.Sound.hooves(2);
  if (lost.length) setTimeout(() => toast(`Too old now for the ${lost.map(x => x.name).join(" and ")}: those flags are off`), 1200);
}, true);

/* ---------- the other ways to work at entries (owner, 15 Nov night: "the race planner ... becomes an all singing all
   dancing location for everything ... by horse, by race, by grid ... which jockeys can help who (maybe that can be a last
   step thing before the races) ... clean clear and obvious") ---------- */
const enJockeysOn = () => typeof jockeyCards === "function" && teamOn() && !teamSkipped() && jockeyCards().length > 0;

// By horse: each horse with its races: entered, flagged (with what it needs and the buttons), or its best fit
function enByHorse() {
  const hs = S.stable.slice().sort((a, b) => pnPeak(b) - pnPeak(a));
  return `<div class="enh">${hs.map(h => {
    const t = pnTier(pnPeak(h)), ins = enOrder().filter(r => S.entries[r.id] === h.id);
    const fl = enOrder().filter(r => !S.entries[r.id] && pnFlagged(h, r)).map(r => ({ r, o: pnOpt(h, r, pnAgesFrom(h)) })).filter(x => x.o && x.o.v !== "x");
    let rows = ins.map(r => { const c = check(h, r);
      return `<div class="enh-in"><span class="en-day">${esc2(dayTag(r.day))}</span><b class="en-rn">${esc2(r.name)}</b><span class="g ${GRADE[r.grade].cls}">${GRADE[r.grade].short}</span>${pnDistNeed(r)}<span class="en-rdy">✓ Entered</span>${c && c.ok ? `<small class="rk-t">${rankText(c)}</small>` : ""}<button class="tb-btn ghost sm" type="button" data-unpick="${r.id}">Take out</button></div>`; }).join("");
    rows += fl.map(x => enAct(h, x.r, x.o, "race")).join("");
    if (!ins.length && !fl.length) {
      const free = enOrder().filter(r => !S.entries[r.id]).map(r => pnOpt(h, r, pnAgesFrom(h))).filter(o => o && o.v !== "x");
      rows = free.length ? enAct(h, free.reduce((m, o) => pnValue(o) > pnValue(m) ? o : m).r, free.reduce((m, o) => pnValue(o) > pnValue(m) ? o : m), "race")
        : `<p class="en-none">${ins.length ? "" : "No race left that this horse could run in."}</p>`;
    }
    return `<article class="enh-h"><div class="enh-top"><button class="en-face" type="button" data-card="${h.id}">${pnFace(h)}</button>
        <div class="enh-id"><div class="ph-n"><button type="button" class="pn-nm" data-card="${h.id}">${esc2(h.name)}</button><span class="pn-tiertag t-${t}">${pnTierWord[t]}</span></div>
          <div class="ph-f">${h.age}-year-old ${h.sex === "F" ? "filly" : "colt"} · rated ${ratingAt(h, h.age)} · best ${tripText(tripAt(h, h.age))} · peaks at ${pnPeak(h)}</div></div>
        <button class="tb-btn ghost sm" type="button" data-card="${h.id}">Card and options</button></div>
      <div class="enh-rows">${rows}</div></article>`; }).join("")}</div>`;
}

// what a jockey would add to a runner in a race (as autoBook works it out: his boost, or his riding skill when it suits)
function enJockLift(c, r, h) {
  const T = teamState(); T.book = T.book || {}; const was = T.book[r.id]; T.book[r.id] = c.code;
  const b = jockeyBoost(r, h).boost + (JOCKEY_KINDS[c.kind].style && jockeySuits(c, h, r) ? 3 : 0);
  if (was) T.book[r.id] = was; else delete T.book[r.id];
  return b;
}
// Jockeys: the last step before the races. Your jockeys and their rides, then every runner with who would help it most
function enJockeys() {
  if (!enJockeysOn()) return `<p class="en-all">You have no jockey cards: your yard's own jockeys ride every runner.</p>`;
  const jk = jockeyCards(), runs = enOrder().filter(r => S.entries[r.id] && horse(S.entries[r.id]));
  const cards = jk.map(c => `<div class="enj-c"><b>${esc2(cardName(c))}</b><small>${esc2(JOCKEY_KINDS[c.kind].text(c.tier))}</small><span class="enj-r ${ridesLeft(c) ? "" : "out"}">${ridesOf(c.code).length} of ${JOCKEY_RIDES[c.tier]} rides booked</span></div>`).join("");
  const row = r => {
    const h = horse(S.entries[r.id]), cur = bookedFor(r), lifts = jk.map(c => ({ c, b: enJockLift(c, r, h) })), best = Math.max(0, ...lifts.map(x => x.b));
    const chips = lifts.map(({ c, b }) => { const on = cur && cur.code === c.code, can = on || ridesLeft(c) > 0;
      return `<button class="enj-k ${on ? "on" : ""} ${b && b === best ? "best" : ""}" type="button" data-jbook="${r.id}:${on ? "" : c.code}" ${can ? "" : "disabled"} title="${on ? "Booked: tap to take him off" : can ? "Book him" : "No rides left"}">${esc2(cardName(c))}<b>${b ? "+" + b : "+0"}</b>${on ? " ✓" : ""}</button>`; }).join("");
    return `<div class="enj-row"><div class="enj-w"><span class="en-day">${esc2(dayTag(r.day))}</span><b class="en-rn">${esc2(r.name)}</b><span class="g ${GRADE[r.grade].cls}">${GRADE[r.grade].short}</span>${pnDistNeed(r)}
        <span class="enj-h">${pnFace(h, "sm")}<b>${esc2(h.name)}</b><small>${STYLE_NAME[h.style] || ""}</small></span></div>
      <div class="enj-ks">${chips}</div><small class="enj-now">${cur ? `Booked: <b>${esc2(cardName(cur))}</b>` : best ? `Best: <b>${esc2(cardName(lifts.find(x => x.b === best).c))}</b> (+${best})` : "None of your jockeys adds anything here"}</small></div>`; };
  return `<div class="enj"><p class="en-trn">Each jockey card rides a few of your runners. The number is what he adds to the horse's rating in that race (the best is gold). Any runner without one of your jockeys gets your yard's own.</p>
    <div class="enj-cs">${cards}</div>
    <p class="tm-auto"><button class="tb-btn sm" type="button" data-autobook="1">Book my jockeys</button><small>Puts each jockey where he's worth the most. Change any of them below.</small></p>
    ${runs.length ? runs.map(row).join("") : `<p class="en-none">Enter your runners first: then book a jockey for each.</p>`}</div>`;
}
document.addEventListener("click", e => {
  const t = e.target.closest && e.target.closest("[data-jbook]"); if (!t) return;
  e.stopPropagation(); const [rid, code] = t.dataset.jbook.split(":");
  if (!bookJockey(rid, code || null)) toast("He has no rides left"); render();
}, true);

// the next step, at the foot of every planner view at entries (owner, 15 Nov night: "you need a next step button at the
// bottom of the races to progress"): book your jockeys (Plus), then go racing
function enNext(view) {
  if (atAscot()) return `<div class="en-nextbar"><span>Change your runners before the first race.</span>${goBtn("toWeek", W.backToRacing)}</div>`;
  const left = RACES.length - entered();
  const say = left ? `<b>${left} race${left === 1 ? " has" : "s have"} no runner yet.</b> An empty race earns nothing.` : `<b>All ${RACES.length} races have a runner.</b>`;
  if (enJockeysOn() && view !== "jockeys" && !left)
    return `<div class="en-nextbar"><span>${say} Next: book your jockeys.</span><button class="tb-btn" type="button" data-pnv="jockeys">Book your jockeys <span aria-hidden="true">›</span></button></div>`;
  return `<div class="en-nextbar ${left ? "" : "ready"}"><span>${say}${left ? " Enter them above, or go anyway." : " Next step:"}</span>${goBtn("toRaces", W.go)}</div>`;
}
