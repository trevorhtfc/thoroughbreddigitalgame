// =====================================================================================================================
// Thoroughbred: the new race planner and every horse's options (owner, 15 Nov 2026).
// Owner: the game is "too complicated ... the ages / races a bit tricky to get your head around". Designed with him on
// the canvas (claude/simpler-game-handover.md), then: "push this through ... ensure all the ui is coordinated nicely".
//   - a new foal (bred or bought) shows its outlook under the card, then every race on the card it could run, age by
//     age (race at 2, develop to 3, develop to 4): stars for its chance, a trainer's line, a flag; a develop button at
//     the foot of each age, or Decide later
//   - then the race planner: Your string (ringed gold, silver, bronze by how good each horse is at its peak, flagged or
//     still needing a race), and the races, each folding up to one line with its flagged horse
//   - on a computer the planner is a grid: every horse against every race
//   - a horse's card from anywhere in the planner: its outlook, its plan and its options
// A flag is a race target (S.targets: one horse per race; a horse may carry several flags but runs as the rules allow).
// The old planner and the old foal pop-up are kept: ?planner=old (remembered) brings them back, ?planner=new undoes it.
// Loaded after js/ui-flow.js.
// =====================================================================================================================
const PLAN_OLD = (() => {
  try {
    const q = location.search;
    if (/[?&]planner=old/.test(q)) localStorage.setItem("tb-planner", "old");
    if (/[?&]planner=new/.test(q)) localStorage.removeItem("tb-planner");
    return localStorage.getItem("tb-planner") === "old";
  } catch (e) { return false; }
})();
UI.pn = { open: {}, more: {}, fresh: null };

/* ================= What a horse could do: its chance in each race, at each age ================= */
const pnHe = h => h.sex === "F" ? { s: "she", S: "She", o: "her", p: "her", P: "Her" } : { s: "he", S: "He", o: "him", p: "his", P: "His" };
const pnLevel = r => r >= 120 ? "champion" : r >= 110 ? "top-class" : r >= 100 ? "smart" : r >= 90 ? "solid" : "moderate";
const pnTier = r => r >= 120 ? "gold" : r >= 110 ? "silver" : r >= 100 ? "bronze" : "plain";
const pnTierWord = { gold: "Gold", silver: "Silver", bronze: "Bronze", plain: "Plain" };
const pnPeak = h => Math.max(...h.r);
// the kind of horse from its best trips: 5f-6f a sprinter, 7f-1m1f a miler, 1m2f-1m4f middle distance, 1m6f+ a stayer
const pnType = d => { const hi = Math.max(...d); return hi <= 1 ? "sprinter" : hi <= 4 ? "miler" : hi <= 6 ? "middle-distance horse" : "stayer"; };
const pnTypeShort = d => ({ sprinter: "Sprinter", miler: "Miler", "middle-distance horse": "Middle distance", stayer: "Stayer" })[pnType(d)];
const pnAgesFrom = (h, foal) => { const out = [], lo = foal ? 2 : h.age, hi = foal || canDev(h) ? 4 : h.age; for (let a = lo; a <= hi; a++) out.push(a); return out; };
const pnNewmarket = () => !!MEETING.runsPerMeeting;
// a trainer can still do trip work (Plus, a trainer with jobs left, before race week)
const pnCanTrain = () => !isSimple() && typeof trainerCards === "function" && trainerCards().length > 0 && jobsLeft() > 0 && S.step < 4;
// the horse at another age, as the rules see it
function pnAt(h, r, age) {
  if (r.sex && h.sex !== r.sex) return null;
  if (age < r.ages[0] || age > r.ages[1]) return null;
  const c = check(Object.assign({}, h, { age }), r);
  return c && !c.hidden ? c : null;
}
// trip work towards this race's trip: does it bring the horse in?
function pnTripFix(h, r, age) {
  if (!pnCanTrain()) return null;
  const d = tripAt(h, age), lo = Math.min(...d), hi = Math.max(...d), dir = r.step > hi ? 1 : r.step < lo ? -1 : 0; if (!dir) return null;
  const x = Object.assign({}, h, { age }), n = tripSteps(x, dir); if (!n) return null;
  x.d = h.d.map(rr => [...new Set(rr.map(i => Math.max(0, Math.min(DISTANCES.length - 1, i + dir * n))))].sort((a, b) => a - b));
  const c = check(x, r); return c && c.ok ? { c, dir } : null;
}
// one race, one horse, at the ages given: { r, age, c, v } where v is 3, 2 or 1 stars, "t" (a trainer job gets it in) or
// "x" (can't run, c.why says why)
const PN_WIN = { 3: .4, 2: .18, 1: .06, t: .04, x: 0 };
// Stars from where the race-day rating sits: top rated, or up to the race's top class (its first band: 120 in a Group 1,
// 110 in a Group 2, 105 in a Group 3 or Listed race, 100 in a handicap) is Strong. Owner, 15 Nov: a 121 three-year-old at
// his best trip in the Commonwealth Cup, 3rd of 10, "120 is gold rated ... should clearly be a 3* option".
const pnV = (r, day, rank) => rank === 1 || day >= r.bands[0] ? 3 : rank <= 3 ? 2 : 1;
// the trainer whose speciality fits a race (a Miler Specialist in a mile race), for the words
const pnTuneWho = r => { const t = typeof trainerSpecs === "function" && trainerSpecs().find(k => k.spec === "trip" && k.trips.includes(raceTrip(r))); return t ? "your " + t.title : "your trainer"; };
// A tune-up from your trainer (Plus, jobs left, none named for this race yet): the stars it would bring, if more.
// Owner, 15 Nov: the planner didn't recognise his Miler Specialist (+5 tune-ups in mile races)
function pnTune(h, r, c) {
  if (!pnCanTrain() || typeof tuneBoost !== "function" || tuneOf(r)) return null;
  const b = tuneBoost(h, r), day = c.day + b, rk = rankIn(r, day, goingKnown() ? CARD.going[r.day] : null), v = pnV(r, day, rk.rank);
  return v > pnV(r, c.day, c.rank) ? { b, v, rank: rk.rank, of: rk.of, who: pnTuneWho(r) } : null;
}
// how good an option is, counting what a trainer job would make of it (a little below the same thing as it stands)
const pnEff = o => o.v === "t" ? (o.tv || 1) - .6 : o.tune ? Math.max(o.v, o.tune.v - .4) : o.v;
const pnScore = o => o.v === "x" ? -1 : pnEff(o) + (o.c.day || o.c.eff || 0) / 1000;
// What an option is worth for "Best idea": the prize times her share of the race, weighed against every runner in the
// field, not just the best (a softmax of race-day ratings; 4.5 points is about one and a half times as likely). Owner,
// 15 Nov: a 95 filly was sent to a Group 2 as "best idea", and a moderate filly to the Royal Hunt Cup (20th of 23) over
// the fillies' Sandringham (14th of 18): fewer and weaker rivals is the better shout.
function pnChance(r, day) {
  const going = goingKnown() ? CARD.going[r.day] : null, k = 4.5, me = Math.exp((day - 100) / k);
  return me / (me + CARD.races[r.i].opp.reduce((a, x) => a + Math.exp((oppDay(x, going) - 100) / k), 0));
}
const pnValue = o => o.v === "x" ? 0 : o.r.prizes[0] * (o.v === "t" ? pnChance(o.r, o.c.day) * .7
  : o.tune ? Math.max(pnChance(o.r, o.c.day), pnChance(o.r, o.c.day + o.tune.b) * .8) : pnChance(o.r, o.c.day));
function pnOpt(h, r, ages) {
  let best = null;
  for (const a of ages) {
    const c = pnAt(h, r, a); if (!c) continue;
    let o;
    if (c.ok) o = { r, age: a, c, v: pnV(r, c.day, c.rank), tune: pnTune(Object.assign({}, h, { age: a }), r, c) };
    else {
      // trip work is only worth a job where it makes a real chance of it (owner, 15 Nov: a miler offered trip work for a
      // 6f race he'd only be an outside chance in)
      const t = pnTripFix(h, r, a), tv = t ? pnV(r, t.c.day, t.c.rank) : 0;
      o = t && tv >= 2 ? { r, age: a, c: t.c, v: "t", tv, dir: t.dir } : { r, age: a, c, v: "x" };
    }
    if (!best || pnScore(o) > pnScore(best)) best = o;
  }
  return best;
}
const pnFlags = () => S.targets || (S.targets = {});
const pnFlagged = (h, r) => pnFlags()[r.id] === h.id;
const pnFlagsOf = h => RACES.filter(r => pnFlagged(h, r));
const pnStars = (v, cls = "") => v === "t" ? `<i class="pn-tr ${cls}" title="A trainer job gets it in" aria-label="A trainer job gets it in"></i>`
  : v === "x" ? `<i class="pn-x ${cls}" aria-label="Can't run"></i>`
  : `<span class="pn-st ${cls}" role="img" aria-label="${v} of 3 stars">${[1, 2, 3].map(i => `<i class="${i <= v ? "on" : ""}"></i>`).join("")}</span>`;
// a small trainer's face beside the stars: a tune-up would lift this
const pnTuneMark = o => `<i class="pn-tr xs" title="A tune-up from ${esc2(o.tune.who)} (+${o.tune.b}): ${o.tune.v} stars" aria-label="A tune-up would make it ${o.tune.v} stars"></i>`;
const PN_FLAG = `<svg class="pn-fl" viewBox="0 0 24 24" aria-hidden="true"><path class="pole" d="M5 21V3.5"/><path class="cloth" d="M5 4h12l-3 4.5 3 4.5H5z"/></svg>`;

/* ================= The outlook: the card's numbers in a few words ================= */
function pnSummary(h) {
  const p = pnHe(h), r = h.r, d = h.d, t2 = pnType(d[0]);
  let s = `A ${pnLevel(r[0])} 2-year-old ${t2}`;
  const ch = (a, b) => b - a >= 3 ? "up" : a - b >= 3 ? "down" : "hold";
  const c3 = ch(r[0], r[1]), c4 = ch(r[1], r[2]), t3 = pnType(d[1]), t4 = pnType(d[2]);
  if (c3 === "up") s += ` who should improve into a ${pnLevel(r[1])} 3-year-old${t3 !== t2 ? ` ${t3} (${tripText(d[1])})` : ""}`;
  else if (c3 === "hold") s += ` who should stay ${pnLevel(r[1])} at 3${t3 !== t2 ? `, a ${t3} by then` : ""}`;
  else s += `, best young: only ${pnLevel(r[1])} at 3`;
  if (c4 === "up") s += `, and improve again at 4 into a ${pnLevel(r[2])} ${t4 !== t3 ? t4 : "horse"}.`;
  else if (c4 === "hold") s += `, and hold ${p.p} form at 4.`;
  else s += `, then go back a little at 4.`;
  // the stayer's boost (rules.js, breedFoal): built into the rating at any age the trip reaches 1m6f or 2m+
  const sb = h.stay ? Math.max(...h.stay) : 0;
  if (sb) s += ` A real stayer: +${sb} built into ${p.p} rating at ${DISTANCES[Math.max(...d[h.stay.indexOf(sb)])]}.`;
  return s;
}
function pnOutlook(h) {
  const r = h.r, ch = (a, b) => b - a >= 3 ? ["up", "Improves"] : a - b >= 3 ? ["down", "Goes back"] : ["hold", "Holds"];
  const disc = a => { const x = r[a - 2], pk = a === h.peakAge;
    return `<div class="pn-od ${pk ? "pk" : ""}"><span class="pn-dia" aria-hidden="true"></span><span class="pn-disc t-${pnTier(x)}">${a}YO</span><span class="pn-pk">${pk ? "Peak" : ""}</span>
      <b>${pnLevel(x).replace(/^./, c => c.toUpperCase())}</b><small>${pnTypeShort(h.d[a - 2])}</small><small class="pn-trip">${tripText(h.d[a - 2])}</small>${h.stay && h.stay[a - 2] ? `<small class="pn-stay" title="Stayer's boost built into the rating">Stayer +${h.stay[a - 2]}</small>` : ""}</div>`; };
  const link = (a, b) => { const [k, w] = ch(r[a - 2], r[b - 2]); return `<div class="pn-ol ${k}"><i aria-hidden="true"></i><span>${w}</span></div>`; };
  return `<section class="pn-out" aria-label="Outlook"><div class="pn-ok">${pnHe(h).P} outlook</div>
    <div class="pn-orow" role="img" aria-label="${esc2(pnSummary(h))}">${disc(2)}${link(2, 3)}${disc(3)}${link(3, 4)}${disc(4)}</div>
    <p class="pn-sum">“${esc2(pnSummary(h))}”</p></section>`;
}

/* ================= A horse's options: age by age ================= */
// mode "foal": a new foal not yet in your string (its flags wait on S.foal.flags); "horse": a horse in your string
function pnFoalFlags() { const F = S.foal; if (!F) return []; F.flags = F.flags || []; return F.flags; }
function pnRowComment(h, o, isBest) {
  const p = pnHe(h);
  if (o.v === "x") return o.c && o.c.why ? `${o.c.why.replace(/\.$/, "")}.` : `Can't run here.`;
  const where = `${ord(o.c.rank)} of ${o.c.of} on ratings`, big = o.r.grade === "Group 1";
  if (o.v === "t") return `Outside ${p.p} best trip. Trip work from your trainer would get ${p.o} in: ${where}.`;
  const tune = o.tune ? ` A tune-up from ${o.tune.who} (+${o.tune.b}) would make ${p.o} ${ord(o.tune.rank)} of ${o.tune.of}${o.tune.v === 3 ? ": a strong chance" : ""}.` : "";
  const top = o.c.rank === 1 ? "should be top rated" : `is top class for this race (${where})`;
  if (o.v === 3) return isBest ? `${big ? "The big one. " : ""}${p.S} ${top}: go for it.` : `${p.S} ${top}${big ? "" : ", for a smaller prize"}.`;
  if (o.v === 2) return `A real chance: ${where}.${tune}`;
  return `An outside chance: ${where}.${tune}`;
}
// why a horse can't run, in a few words
function pnWhy(o) {
  const w = (o.c && o.c.why) || "";
  if (/too high for a handicap/.test(w)) return "too good for a handicap";
  if (/steps from its best trip/.test(w)) return "the wrong trip";
  const m = w.match(/Rated (\d+) here: this race needs (\d+)/); if (m) return `rated ${m[1]}, needs ${m[2]}+`;
  return w ? w.toLowerCase() : "can't run";
}
function pnMeta(r) { return `${esc2(dayTag(r.day))} · ${r.dist} · ${esc2(r.ageLabel)} · ${money(r.prizes[0])}`; }
function pnPaths(h, mode) {
  const foal = mode === "foal", p = pnHe(h), ages = pnAgesFrom(h, foal);
  const flags = new Set(foal ? pnFoalFlags() : pnFlagsOf(h).map(r => r.id));
  const byAge = ages.map(a => ({ a, rows: RACES.map(r => pnOpt(h, r, [a])).filter(Boolean).sort((x, y) => pnScore(y) - pnScore(x) || y.r.prizes[0] - x.r.prizes[0]) }));
  const all = byAge.flatMap(x => x.rows).filter(o => o.v !== "x"), best = all.length ? all.reduce((m, o) => pnValue(o) > pnValue(m) ? o : m) : null;
  const ageSub = a => { const x = h.r[a - 2], now = foal ? a === 2 : a === h.age, ty = pnTypeShort(h.d[a - 2]).toLowerCase();
    const lead = now ? "Now" : a === h.peakAge ? `${p.P} peak` : x < h.r[a - 3] - 2 ? "Past " + p.p + " best" : "Holds " + p.p + " form";
    return `${lead} · a ${pnLevel(x)} ${ty === "middle distance" ? "middle-distance horse" : ty}${h.stay && h.stay[a - 2] ? ` · stayer's boost +${h.stay[a - 2]} built in` : ""}`; };
  const devBtn = a => foal
    ? (a === 2 ? `<button class="tb-btn ghost sm" type="button" data-fkeep="1">Keep ${p.o} a 2-year-old</button>` : `<button class="tb-btn ${best && best.age === a ? "" : "ghost"} sm" type="button" data-keepdev="${a}">Develop to ${a}</button>`)
    : (a === h.age ? "" : `<button class="tb-btn ${best && best.age === a ? "" : "ghost"} sm" type="button" data-devto="${h.id}:${a}">Develop to ${a}${pnNewmarket() ? " for the season" : ""}</button>`);
  const row = o => {
    const on = flags.has(o.r.id), isBest = best && o === best, g = GRADE[o.r.grade];
    const other = !foal ? null : horse(pnFlags()[o.r.id]);
    return `<div class="pn-row v${o.v} ${on ? "on" : ""}">
      <div class="pn-v">${pnStars(o.v)}${o.v === "t" ? pnStars(o.tv, "sm") : ""}${o.tune ? pnTuneMark(o) : ""}<span>${o.v === "x" ? "Can't run" : o.v === "t" ? "Trainer job" : ["", "Outside", "Good", "Strong"][o.v]}</span></div>
      <div class="pn-rt"><div class="pn-rn"><b>${esc2(o.r.name)}</b><span class="g ${g.cls}">${g.short}</span>${isBest ? `<em class="pn-best">Best idea</em>` : ""}</div>
        <div class="pn-meta">${pnMeta(o.r)}</div><p class="pn-say">${esc2(pnRowComment(h, o, isBest))}</p>
        ${other && o.v !== "x" ? `<p class="pn-note">Flagged now: ${esc2(other.name)}. Your flag would take its place.</p>` : ""}</div>
      ${o.v === "x" ? "" : `<button class="pn-flag ${on ? "on" : ""}" type="button" ${foal ? `data-ffl="${o.r.id}"` : `data-pflag="${o.r.id}:${h.id}"`} aria-pressed="${on}" aria-label="${on ? "Remove the flag" : "Flag this race"}">${PN_FLAG}<span>${on ? "Flagged" : "Flag"}</span></button>`}
    </div>`; };
  const stages = byAge.map(({ a, rows }, i) => { const isBest = best && best.age === a;
    return `<li class="pn-stage ${isBest ? "best" : ""}"><div class="pn-node" aria-hidden="true">${a}</div>
      <div class="pn-sbody"><div class="pn-sh"><h4>${foal ? (a === 2 ? "Race as a 2-year-old" : `Develop to ${a}`) : a === h.age ? `As ${p.s} is: ${a} years old` : `Develop to ${a}`}</h4>${isBest ? `<em class="pn-bestp">Best path</em>` : ""}</div>
        <p class="pn-ssub">${ageSub(a)}</p>
        ${rows.filter(o => o.v !== "x").map(row).join("") || `<p class="pn-none">No race on your card ${p.s} could run at ${a}.</p>`}
        ${rows.some(o => o.v === "x") ? `<p class="pn-cant"><b>Not for ${p.o} at ${a}:</b> ${rows.filter(o => o.v === "x").map(o => `${esc2(shortRace(o.r))} <span>(${esc2(pnWhy(o))})</span>`).join(", ")}</p>` : ""}
        ${devBtn(a) ? `<div class="pn-sfoot">${devBtn(a)}</div>` : ""}</div></li>`; }).join("");
  const nf = flags.size;
  return `<section class="pn-opts" id="pnOpts" data-h="${h.id}" data-mode="${mode}">
    <div class="pn-oh"><h3>${p.P} options</h3><p>Every race on your card ${p.s} could run, at each age. <b>Flag the ones you like</b>: they show in your race planner.</p></div>
    <div class="pn-tp"><i class="pn-trface" aria-hidden="true"></i><span><b>Not sure where to start?</b> Your trainer flags ${p.p} strongest chances for you.</span>
      <button class="tb-btn sm pn-gold" type="button" ${foal ? `data-fpicks="1"` : `data-hpicks="${h.id}"`}>${PN_FLAG} Flag the trainer's picks</button></div>
    ${pnKey()}
    <ol class="pn-route">${stages}</ol>
    <div class="pn-ofoot">${PN_FLAG}<span><b>${nf ? `${nf} race${nf === 1 ? "" : "s"} flagged` : "Nothing flagged yet"}</b>${foal ? ` · Not sure yet? Save ${p.o} as a 2-year-old: ${p.p} flags go to your planner and you can develop ${p.o} any time before entries.` : ""}</span></div>
  </section>`;
}
function pnKey() {
  return `<div class="pn-key"><span>${pnStars(3)} Strong</span><span>${pnStars(2)} Good</span><span>${pnStars(1)} Outside</span>
    ${pnCanTrain() || (!isSimple() && typeof trainerCards === "function" && trainerCards().length) ? `<span>${pnStars("t")} Trainer job</span>` : ""}<span>${pnStars("x")} Can't run</span><span>${PN_FLAG} Your flag</span></div>`;
}

/* ================= Flags: yours, and the trainer's picks ================= */
function pnSetFlag(raceId, horseId) {
  const T = pnFlags();
  if (T[raceId] === horseId) delete T[raceId]; else T[raceId] = horseId;
  save();
}
// a horse's own picks: its best race, and every other 3-star race at the same age that no stronger horse of yours holds
function pnPicksFor(h, foal) {
  const ages = pnAgesFrom(h, foal), opts = RACES.map(r => pnOpt(h, r, ages)).filter(o => o && o.v !== "x");
  if (!opts.length) return [];
  const best = opts.reduce((m, o) => pnValue(o) > pnValue(m) ? o : m);
  const picks = [best].concat(RACES.map(r => r === best.r ? null : pnOpt(h, r, [best.age])).filter(o => o && o.v === 3));
  return picks.filter(o => { const hid = pnFlags()[o.r.id], other = hid && hid !== h.id && horse(hid);
    if (!other) return true; const oo = pnOpt(other, o.r, pnAgesFrom(other)); return !oo || pnScore(oo) < pnScore(o); });
}
// every race: the best horse for it, each horse once at Ascot (it runs once), once a meeting and at one age at Newmarket.
// Races you've flagged yourself stay as they are.
function pnPicksAll() {
  const T = pnFlags(), used = {}, ageOf = {}, meet = {};
  RACES.forEach(r => { const h = horse(T[r.id]); if (!h) { delete T[r.id]; return; } used[h.id] = (used[h.id] || 0) + 1; (meet[h.id] = meet[h.id] || new Set()).add(r.day); });
  const cand = [];
  S.stable.forEach(h => RACES.forEach(r => { if (T[r.id]) return; pnAgesFrom(h).forEach(a => { const o = pnOpt(h, r, [a]); if (o && o.v !== "x") cand.push({ h, o }); }); }));
  cand.sort((x, y) => pnValue(y.o) - pnValue(x.o));
  let n = 0;
  for (const { h, o } of cand) {
    if (T[o.r.id]) continue;
    if (pnNewmarket()) { if (meet[h.id] && meet[h.id].has(o.r.day)) continue; if (ageOf[h.id] && ageOf[h.id] !== o.age) continue; }
    else if (used[h.id]) continue;
    T[o.r.id] = h.id; used[h.id] = (used[h.id] || 0) + 1; ageOf[h.id] = o.age; (meet[h.id] = meet[h.id] || new Set()).add(o.r.day); n++;
  }
  save(); return n;
}

/* ================= The race planner ================= */
// a race's trip in bold and the rating it takes to run (owner, 15 Nov: "distance need bolding ... showing the ratings required?")
const pnDistNeed = r => `<b class="pn-dist">${r.dist}</b><span class="pn-need" title="${r.grade === "Handicap" ? `Rated ${needFor(r)} to ${HCAP_MAX} to run` : `Rated ${needFor(r)}+ to run`}">${r.grade === "Handicap" ? `${needFor(r)}–${HCAP_MAX}` : `${needFor(r)}+`}</span>`;
const pnWide = () => innerWidth >= 1000;
function pnGroups() {
  if (pnNewmarket()) return DAYS.map((d, k) => ({ t: d, sub: "", races: RACES.filter(r => r.day === k) })).filter(g => g.races.length);
  const g = [
    { t: "2-year-old races", sub: "Run them as they are: no developing.", f: r => r.ages[1] === 2 },
    { t: "3-year-old races", sub: "Develop a horse to 3 to run here.", f: r => r.ages[0] === 3 && r.ages[1] === 3 },
    { t: "3 and up", sub: "Run a horse at 3 or 4. Handicaps are for horses rated 110 or less.", f: r => r.ages[0] === 3 && r.ages[1] > 3 },
    { t: "4 and up", sub: "Develop a horse to 4 to run here.", f: r => r.ages[0] >= 4 },
  ];
  return g.map(x => ({ ...x, races: RACES.filter(x.f) })).filter(x => x.races.length);
}
// the horses that could run in a race, best first (flagged first)
function pnFits(r) {
  return S.stable.map(h => ({ h, o: pnOpt(h, r, pnAgesFrom(h)) })).filter(x => x.o && x.o.v !== "x")
    .sort((a, b) => (pnFlagged(b.h, r) - pnFlagged(a.h, r)) || pnScore(b.o) - pnScore(a.o));
}
// where else a horse could go: a flag elsewhere first, else its next best race
function pnAlso(h, r) {
  const fl = pnFlagsOf(h).filter(x => x !== r);
  // Newmarket: one age all season, once a meeting
  if (pnNewmarket() && fl.length && pnFlagged(h, r)) {
    const all = fl.concat([r]), ages = new Set(all.map(x => { const o = pnOpt(h, x, pnAgesFrom(h)); return o ? o.age : h.age; }));
    if (fl.some(x => x.day === r.day)) return `<span class="pn-also amber">Also flagged at this meeting: ${fl.filter(x => x.day === r.day).map(x => esc2(shortRace(x))).join(", ")}. It runs once a meeting</span>`;
    if (ages.size > 1) return `<span class="pn-also amber">Flagged at ${[...ages].sort().join(" and ")}: it races at one age all season</span>`;
    return `<span class="pn-also">${fl.length + 1} runs this season: ${all.sort((x, y) => x.day - y.day).map(x => esc2(shortRace(x))).join(", ")}</span>`;
  }
  if (fl.length) return `<span class="pn-also amber">Also flagged: ${fl.map(raceTag).join(", ")}</span>`;
  const others = RACES.filter(x => x !== r).map(x => pnOpt(h, x, pnAgesFrom(h))).filter(o => o && o.v !== "x");
  if (!others.length) return "";
  const b = others.reduce((m, o) => pnScore(o) > pnScore(m) ? o : m);
  return `<span class="pn-also">Also fits: ${raceTag(b.r)} ${pnStars(b.v, "sm")}</span>`;
}
function pnLine(h, r, o) {
  const on = pnFlagged(h, r), p = pnHe(h);
  let act;
  if (o.v === "t") act = (pnCanTrain() ? `<button class="tb-btn sm pn-gold" type="button" data-ptrip="${h.id}:${o.dir}"><i class="pn-trface" aria-hidden="true"></i>Trainer: trip work</button>` : `<span class="pn-ready amber">Needs trip work from your trainer</span>`)
    + (o.age > h.age && canDev(h) ? ` <button class="tb-btn ghost sm" type="button" data-devto="${h.id}:${o.age}">Develop to ${o.age}</button>` : "");
  else if (o.age > h.age) act = canDev(h) ? `<button class="tb-btn ghost sm pn-dev" type="button" data-devto="${h.id}:${o.age}"><i class="pn-up" aria-hidden="true"></i>Develop to ${o.age}${pnNewmarket() ? " for the season" : ""}</button>` : `<span class="pn-ready">Too young now</span>`;
  else act = `<span class="pn-ready">✓ Ready as a ${o.age}-year-old</span>`;
  return `<div class="pn-line ${on ? "on" : ""}">
    <button class="pn-face t-${pnTier(pnPeak(h))}" type="button" data-card="${h.id}" aria-label="Open ${esc2(h.name)}'s card"><img src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt=""></button>
    <div class="pn-lt"><div class="pn-lname"><button type="button" class="pn-nm" data-card="${h.id}">${esc2(h.name)}</button>${pnStars(o.v)}${o.v === "t" ? pnStars(o.tv, "sm") : ""}${o.tune ? pnTuneMark(o) : ""}</div>${o.tune ? `<div class="pn-tunenote">A tune-up from ${esc2(o.tune.who)} (+${o.tune.b}) makes ${p.o} ${ord(o.tune.rank)} of ${o.tune.of}</div>` : ""}
      <div class="pn-act">${act}</div>${pnAlso(h, r)}</div>
    <button class="pn-flag ${on ? "on" : ""}" type="button" data-pflag="${r.id}:${h.id}" aria-pressed="${on}" aria-label="${on ? `Remove ${esc2(h.name)}'s flag` : `Flag ${esc2(h.name)} for the ${esc2(r.name)}`}">${PN_FLAG}<span>${on ? "Flagged" : "Flag"}</span></button>
  </div>`;
}
function pnRace(r) {
  const fits = pnFits(r), T = pnFlags(), fh = horse(T[r.id]), open = !!UI.pn.open[r.id], g = GRADE[r.grade];
  const fo = fh && pnOpt(fh, r, pnAgesFrom(fh));
  const dot = fh ? (fo && fo.v === 3 ? "strong" : "ok") : "open";
  const sum = fh ? `<span class="pn-sum1">${PN_FLAG}<b>${esc2(fh.name)}</b>${fo ? pnStars(fo.v, "sm") : ""}</span>`
    : fits.length ? `<span class="pn-sum1 amber">No flag yet · ${fits.length} could run</span>` : `<span class="pn-sum1 none">Nobody yet</span>`;
  const shown = UI.pn.more[r.id] ? fits : fits.slice(0, 2), rest = fits.length - shown.length;
  const empty = `<p class="pn-empty">Nobody can run here yet. It's for ${esc2(r.ageLabel)} over ${r.dist}, rated ${needFor(r)}+${r.grade === "Handicap" ? ` and no more than ${HCAP_MAX}` : ""}.</p>`;
  return `<article class="pn-race ${open ? "open" : ""}" data-race="${r.id}">
    <button class="pn-rh" type="button" data-ropen="${r.id}" aria-expanded="${open}">
      <span class="pn-r1"><i class="pn-dot ${dot}" aria-hidden="true"></i><span class="pn-rname">${esc2(r.name)}</span><span class="g ${g.cls}">${g.short}</span><span class="pn-rinfo">${pnDistNeed(r)}${pnNewmarket() ? `<span class="pn-agel">${esc2(r.ageLabel)}</span>` : ""}</span><i class="pn-chev" aria-hidden="true"></i></span>
      ${open ? "" : sum}
    </button>
    ${open ? `<div class="pn-rbody">${fits.length ? shown.map(x => pnLine(x.h, r, x.o)).join("") : empty}
      ${rest > 0 ? `<button class="pn-more" type="button" data-rmore="${r.id}">+ ${rest} more that could run</button>` : UI.pn.more[r.id] && fits.length > 2 ? `<button class="pn-more" type="button" data-rmore="${r.id}">Show fewer</button>` : ""}</div>` : ""}
  </article>`;
}
// Your string: every horse, ringed by how good it is at its peak, flagged or still needing a race
const pnStringOpen = () => { try { return localStorage.getItem("tb-string") !== "closed"; } catch (e) { return true; } };
function pnStatus(h) {
  const fl = pnFlagsOf(h);
  if (fl.length) return pnNewmarket() ? { k: "ok", t: `${fl.length} run${fl.length === 1 ? "" : "s"}` } : fl.length === 1 ? { k: "ok", t: shortRace(fl[0]) } : { k: "two", t: `${fl.length} races` };
  return RACES.some(r => { const o = pnOpt(h, r, pnAgesFrom(h)); return o && o.v !== "x"; }) ? { k: "need", t: "Needs a race" } : { k: "none", t: "Fits nothing" };
}
function pnString() {
  const hs = S.stable.slice().sort((a, b) => pnPeak(b) - pnPeak(a)), st = hs.map(h => ({ h, s: pnStatus(h) }));
  const n = k => st.filter(x => x.s.k === k || (k === "ok" && x.s.k === "two")).length;
  const pills = `<div class="pn-pills"><span class="ok">${n("ok")} flagged</span>${n("need") ? `<span class="need">${n("need")} need${n("need") === 1 ? "s" : ""} a race</span>` : ""}${n("none") ? `<span class="none">${n("none")} fit${n("none") === 1 ? "s" : ""} nothing</span>` : ""}</div>`;
  const open = pnStringOpen();
  const head = `<button class="pn-sh2" type="button" data-pstring="1" aria-expanded="${open}"><span>Your string · ${hs.length}</span><em>${open ? "Hide" : "Show"}</em><i class="pn-chev ${open ? "up" : ""}" aria-hidden="true"></i></button>`;
  if (!open) return `<section class="pn-string closed">${head}<div class="pn-dots" role="img" aria-label="Filled: flagged. Dashed: needs a race.">${st.map(({ h, s }) => `<i class="t-${pnTier(pnPeak(h))} ${s.k}" title="${esc2(h.name)}"></i>`).join("")}</div>${pills}</section>`;
  return `<section class="pn-string">${head}
    <div class="pn-faces">${st.map(({ h, s }) => `<button class="pn-hf ${s.k}" type="button" data-card="${h.id}">
        <span class="pn-ring t-${pnTier(pnPeak(h))}"><img src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt="">${s.k === "ok" || s.k === "two" ? `<i class="pn-badge">${PN_FLAG}</i>` : s.k === "need" ? `<i class="pn-badge q">?</i>` : ""}</span>
        <b>${esc2(h.name)}</b><small class="${s.k}">${esc2(s.t)}</small></button>`).join("")}</div>
    <div class="pn-ringkey"><span><i class="t-gold"></i>Gold: champion</span><span><i class="t-silver"></i>Silver: top-class</span><span><i class="t-bronze"></i>Bronze: smart</span><span><i class="t-plain"></i>Plain: solid</span></div>
    ${pills}</section>`;
}
// The computer's grid: every horse against every race
function pnGrid() {
  const hs = S.stable.slice().sort((a, b) => pnPeak(b) - pnPeak(a)), T = pnFlags(), n = hs.length;
  const cols = `grid-template-columns:minmax(260px,350px) repeat(${n},56px)`;
  const head = `<div class="pg-row pg-head" style="${cols}"><span></span>${hs.map(h => `<button class="pg-h" type="button" data-card="${h.id}"><span class="pn-ring sm t-${pnTier(pnPeak(h))}"><img src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt=""></span><b>${esc2(h.name)}</b><small>${h.age}YO</small></button>`).join("")}</div>`;
  const rows = pnGroups().map(g => `<div class="pg-g"><b>${esc2(g.t)}</b>${g.sub ? `<span>${esc2(g.sub)}</span>` : ""}</div>` + g.races.map(r => {
    const fh = horse(T[r.id]), fo = fh && pnOpt(fh, r, pnAgesFrom(fh)), gr = GRADE[r.grade];
    return `<div class="pg-row" data-prow="${r.id}" style="${cols}"><div class="pg-r"><i class="pn-dot ${fh ? (fo && fo.v === 3 ? "strong" : "ok") : "open"}" aria-hidden="true"></i><span class="pn-rname">${esc2(r.name)}</span><span class="g ${gr.cls}">${gr.short}</span>${pnDistNeed(r)}</div>
      ${hs.map(h => { const o = pnOpt(h, r, pnAgesFrom(h)), on = T[r.id] === h.id;
        if (!o || o.v === "x") return `<span class="pg-c no" aria-hidden="true"><i></i></span>`;
        return `<button class="pg-c v${o.v} ${on ? "on" : ""}" type="button" data-pflag="${r.id}:${h.id}" aria-pressed="${on}" title="${esc2(h.name)} · ${esc2(r.name)}${o.age > h.age ? ` · develop to ${o.age}` : ""}">${pnStars(o.v, "sm")}${o.tune ? pnTuneMark(o) : ""}${o.age > h.age ? `<small>${o.age}</small>` : ""}${on ? PN_FLAG : ""}</button>`; }).join("")}</div>`; }).join("")).join("");
  const foot = `<div class="pg-row pg-foot" style="${cols}"><span>${pnNewmarket() ? "Runs this season" : "Flags (each horse runs once)"}</span>${hs.map(h => { const s = pnStatus(h); return `<span class="pg-f ${s.k}">${s.k === "ok" || s.k === "two" ? (pnNewmarket() ? s.t : s.k === "two" ? s.t : "⚑") : s.k === "need" ? "?" : "–"}</span>`; }).join("")}</div>`;
  return `<div class="pg"><div class="pg-in">${head}${rows}${foot}</div></div>
    <p class="pn-hint">Tap a square to flag that horse for that race. A small number means the age it would race at: develop it to that age at Warren Hill or from its card. Tap a horse for its card.</p>`;
}
// the planner's key points, the first time it opens in a season (the same pop-up as each step's, js/ui-flow.js)
function pnPlanTips(force) {
  S.seenTips = S.seenTips || {};
  if (!force && (S.seenTips.plan || tipsOff())) return;
  S.seenTips.plan = 1; save();
  kpShow(`<div class="kp-k">Your race planner</div><h2 id="kpT">Which horse for which race</h2>
    <ol class="kp-l">
      <li><b>Your string</b> at the top: gold, silver and bronze rings show how good each horse will be at its best. A <b>?</b> means it still needs a race.</li>
      <li>Each race shows the horse you've <b>flagged</b> for it. Tap a race to see everyone who could run, with stars for their chance.</li>
      <li><b>Develop to 3</b> means it would race as a 3-year-old: do it here, from its card, or at Warren Hill.</li>
      <li>Stuck? <b>Flag the trainer's picks</b> fills every race for you. Flags are only a plan: you enter your runners at entries.</li>
    </ol>
    <div class="kp-b"><button class="tb-btn" type="button" data-kpok="1">Got it <span aria-hidden="true">›</span></button></div>`);
}
/* ================= Three ways to look at the plan (owner, 15 Nov evening) =================
   Grid (the default: every horse against every race; a list of races on a phone), By race (day by day, who is flagged
   for each race, like the old planner) and By horse (your string, each horse with its flagged races) */
// At entries the planner also takes your entries (owner, 15 Nov evening: "training and entries should just be put into
// the main race planner"): an Enter view comes first and is the default then (js/entries.js)
const pnCanEnter = () => !ENTRIES_OLD && S.step >= 3 && S.step <= 4 && !racesRun();
const PN_VIEWS_PLAN = [["grid", "Grid"], ["race", "By race"], ["horse", "By horse"]];
const pnViews = () => pnCanEnter() ? [["enter", "Enter"]].concat(PN_VIEWS_PLAN) : PN_VIEWS_PLAN;
const pnViewKey = () => pnCanEnter() ? "tb-pnview-e" : "tb-pnview";
const pnView = () => { const vs = pnViews(), def = vs[0][0]; try { const v = localStorage.getItem(pnViewKey()); return vs.some(x => x[0] === v) ? v : def; } catch (e) { return def; } };
const pnViewBar = () => { const v = pnView();
  return `<div class="pn-views" role="tablist" aria-label="Planner view">${pnViews().map(([k, w]) => `<button type="button" role="tab" class="${v === k ? "on" : ""}" aria-selected="${v === k}" data-pview="${k}">${w}</button>`).join("")}</div>`; };
const pnFace = (h, cls = "") => `<span class="pn-ring ${cls} t-${pnTier(pnPeak(h))}"><img src="img/p${String(h.portrait || 1).padStart(2, "0")}.webp" alt=""></span>`;
// By race: one column a day (a meeting at Newmarket), each race a tile with the horse flagged for it
function pnByRace() {
  const T = pnFlags(), days = DAYS.map((d, k) => ({ t: d, races: RACES.filter(r => r.day === k) })).filter(g => g.races.length);
  const tile = r => {
    const g = GRADE[r.grade], eh = horse(S.entries[r.id]), fh = eh || horse(T[r.id]), fo = fh && pnOpt(fh, r, pnAgesFrom(fh)), n = fh ? 0 : pnFits(r).length;
    return `<div class="pr-t ${fh ? "on" : n ? "need" : "none"}">
      <div class="pr-h"><span class="pn-rname">${esc2(r.name)}</span><span class="g ${g.cls}">${g.short}</span></div>
      <div class="pr-m">${pnDistNeed(r)}<span class="pn-agel">${esc2(r.ageLabel)}</span><span class="pn-agel">${money(r.prizes[0])}</span></div>
      ${fh ? `<button class="pr-who" type="button" data-card="${fh.id}">${pnFace(fh, "sm")}<span class="pr-wn"><b>${esc2(fh.name)}</b><small>${fo ? pnStars(fo.v === "t" ? fo.tv : fo.v, "sm") : ""}${eh ? `<span class="pr-in">✓ Entered</span>` : fo ? (fo.age > fh.age ? `Develop to ${fo.age}` : `Runs at ${fo.age}`) : ""}</small></span></button>`
        : `<button class="pr-open" type="button" data-pgo="${r.id}">${n ? `No flag yet · ${n} could run <b>Choose ›</b>` : "Nobody can run here yet"}</button>`}
    </div>`;
  };
  return `<div class="pr">${days.map(g => `<div class="pr-d"><h4>${esc2(g.t)}</h4>${g.races.map(tile).join("")}</div>`).join("")}</div>`;
}
// By horse: your string, best first, each with the races it is flagged for (or its best fit)
function pnByHorse() {
  const hs = S.stable.slice().sort((a, b) => pnPeak(b) - pnPeak(a));
  return `<div class="ph">${hs.map(h => {
    const t = pnTier(pnPeak(h)), s = pnStatus(h), fl = pnFlagsOf(h).sort((a, b) => a.day - b.day || a.i - b.i);
    const chips = fl.map(r => { const o = pnOpt(h, r, pnAgesFrom(h));
      return `<span class="ph-r">${PN_FLAG}<b>${esc2(shortRace(r))}</b><span class="g ${GRADE[r.grade].cls}">${GRADE[r.grade].short}</span><small>${esc2(dayTag(r.day))} · <b>${r.dist}</b>${o && o.age > h.age ? ` · develop to ${o.age}` : ""}</small>${o ? pnStars(o.v === "t" ? o.tv : o.v, "sm") : ""}</span>`; }).join("");
    let alt = "";
    if (!fl.length) { const others = RACES.map(r => pnOpt(h, r, pnAgesFrom(h))).filter(o => o && o.v !== "x");
      if (others.length) { const b = others.reduce((m, o) => pnValue(o) > pnValue(m) ? o : m); alt = `<span class="ph-best">Best fit: <b>${raceTag(b.r)}</b> ${pnStars(b.v === "t" ? b.tv : b.v, "sm")}</span>`; } }
    return `<div class="ph-h ${s.k}"><button class="ph-face" type="button" data-card="${h.id}" aria-label="Open ${esc2(h.name)}'s card">${pnFace(h)}</button>
      <div class="ph-b"><div class="ph-n"><button type="button" class="pn-nm" data-card="${h.id}">${esc2(h.name)}</button><span class="pn-tiertag t-${t}">${pnTierWord[t]}</span></div>
        <div class="ph-f">${h.age}-year-old ${h.sex === "F" ? "filly" : "colt"} · rated ${ratingAt(h, h.age)} · best ${tripText(tripAt(h, h.age))} · peaks at ${pnPeak(h)}</div>
        <div class="ph-rs">${chips || `<span class="ph-need ${s.k}">${s.k === "none" ? "Fits nothing on this card" : "Needs a race"}</span>${alt}`}</div></div>
      <button class="tb-btn ghost sm ph-go" type="button" data-card="${h.id}">Options</button></div>`; }).join("")}</div>`;
}
function pnPlanner() {
  if (S.stable.length && !(S.seenTips && S.seenTips.plan)) setTimeout(() => { if (document.querySelector(".pn") && !document.querySelector(".foal-wrap")) pnPlanTips(); }, 500);
  if (!S.stable.length) return `<section class="pn"><p class="tb-empty">No horses yet. Every horse you breed or buy drops in here, with the races it could run.</p></section>`;
  const T = pnFlags(), flagged = RACES.filter(r => horse(T[r.id])).length;
  const fresh = UI.pn.fresh && (UI.sheet === "stud" || UI.sheet === "tatts") && horse(UI.pn.fresh);
  let banner = "";
  if (fresh) { const fl = pnFlagsOf(fresh);
    banner = `<div class="pn-fresh"><img src="img/p${String(fresh.portrait || 1).padStart(2, "0")}.webp" alt=""><span><b>${esc2(fresh.name)} is in your planner.</b> ${fl.length ? `Flagged for ${fl.map(r => esc2(r.name)).join(" and ")}.` : `Nothing flagged yet: find ${pnHe(fresh).o} below, or let your trainer pick.`}</span></div>`; }
  const nmRules = pnNewmarket() ? `<div class="pn-info"><span><b>Newmarket:</b> a horse stays one age all season and can run once at each meeting. Developing it moves it up an age for every meeting.</span></div>` : "";
  const view = pnView();
  if (view === "enter") return `<section class="pn pn-enter">${banner}${nmRules}${pnViewBar()}${enBody()}</section>`;
  return `<section class="pn">${banner}${view === "horse" ? "" : pnString()}${nmRules}${pnViewBar()}
    <div class="pn-tools"><button class="tb-btn sm pn-gold" type="button" data-ppicks="1">${PN_FLAG} Flag the trainer's picks</button><span><b>${flagged} of ${RACES.length}</b> races flagged</span><button class="pn-how" type="button" data-ptips="1">How this works</button></div>
    ${pnKey()}
    ${view === "race" ? pnByRace() : view === "horse" ? pnByHorse() : pnWide() ? pnGrid() : `<div class="pn-all"><span>Tap a race to open it</span><button type="button" data-pall="1">Open all</button><button type="button" data-pall="0">Close all</button></div>
      ${pnGroups().map(g => `<div class="pn-g"><h4>${esc2(g.t)}</h4>${g.sub ? `<p>${esc2(g.sub)}</p>` : ""}</div>${g.races.map(pnRace).join("")}`).join("")}`}
  </section>`;
}

/* ================= A horse's card from the planner ================= */
// fromAge: just developed from that age (owner, 15 Nov: "developing the horse shouldn't remove the options list"), so the
// card plays its develop animation and the options stay open under it, from the new age on
// opts.before: the card as it was before a trainer's job, opts.job: that job (the card plays its "trained" stamp)
function pnHorseCard(h, fromAge, opts = {}) {
  const dev = fromAge != null && fromAge < h.age, tr = opts.before && opts.job;
  const old = $("#devCard"); if (old) old.remove();
  const box = document.createElement("div"); box.id = "devCard"; box.className = "foal-wrap";
  box.addEventListener("click", e => { if (e.target === box) { box.remove(); cardFrame = null; } });
  const p = pnHe(h), t = pnTier(pnPeak(h));
  box.innerHTML = `<div class="foal pn-hc" role="dialog" aria-label="${esc2(h.name)}">${cardBox()}
    <div class="fc-in"><div class="pn-hctop"><span class="pn-tiertag t-${t}">${pnTierWord[t]} · ${pnLevel(pnPeak(h))}</span><button class="tb-btn ghost sm" type="button" data-pclose="1">${pnCanEnter() ? "Back to entries" : "Back to the planner"}</button></div>
      ${tr ? `<div class="pn-devd tr"><i class="pn-trface" aria-hidden="true"></i><span>${pnJobWords(h, opts.job)}</span></div>` : ""}
      ${dev ? `<div class="pn-devd">Developed to ${h.age}: rated <b>${ratingAt(h, fromAge)} → ${ratingAt(h, h.age)}</b>, best <b>${tripText(tripAt(h, h.age))}</b></div>` : ""}
      <div class="fc-kicker">${h.age}-year-old ${h.sex === "F" ? "filly" : "colt"}</div><div class="fc-dev"><b>${esc2(h.name)}</b></div>
      <div class="fc-ped">by <b>${esc2(h.sire)}</b> out of <b>${esc2(h.dam)}</b></div>
      <div class="fc-facts"><span>Rated <b>${ratingAt(h, h.age)}</b></span><span>Best <b>${tripText(tripAt(h, h.age))}</b></span><span>Likes <b>${h.grounds.join(", ")}</b></span>${h.style ? `<span>Runs <b>${STYLE_NAME[h.style]}</b>, ${h.temper}</span>` : ""}</div>
      ${pnOutlook(h)}
      <div id="pnHcOpts">${pnPaths(h, "horse")}</div>
      <div class="pn-bar" id="pnCardBar">${pnCardBar(h)}</div></div></div>`;
  document.body.appendChild(box);
  wireCard();
  if (tr) { toCard({ type: "show", horse: opts.before, animate: false }); setTimeout(() => toCard({ type: "trained", horse: cardPayload(h) }), 650); }
  else if (dev) { toCard({ type: "show", horse: cardPayload(h, fromAge), animate: false }); setTimeout(() => toCard({ type: "develop", horse: cardPayload(h, h.age) }), 700); }
  else toCard({ type: "show", horse: cardPayload(h, h.age), animate: true });
}
// a trainer's job done: the horse's card with the job stamped on it, and its options
const showTrained = (h, before, job) => pnHorseCard(h, null, { before, job });
function pnJobWords(h, j) {
  const who = typeof trainerCards === "function" && trainerCards()[0] ? cardName(trainerCards()[0]) : "Your trainer";
  if (j.k === "trip") return `<b>${esc2(who)}:</b> trip work. Best trip now <b>${tripText(tripAt(h, h.age))}</b>.`;
  if (j.k === "tune") { const r = raceOf(j.race); return `<b>${esc2(who)}:</b> tuned up, <b>+${r ? tuneBoost(h, r) : 0}</b> in the ${r ? esc2(r.name) : "race"}.`; }
  if (j.k === "ground") return `<b>${esc2(who)}:</b> ground work. Now handles <b>${esc2(h.grounds.join(", "))}</b>.`;
  if (j.k === "settle") return `<b>${esc2(who)}:</b> learned to settle. Calm now.`;
  if (j.k === "eye") return `<b>${esc2(who)}</b> has had a good look at ${pnHe(h).o}.`;
  return `<b>${esc2(who)}</b> has worked on ${pnHe(h).o}.`;
}
function pnRefreshCard() {
  const o = $("#pnHcOpts"), f = $("#pnOpts"); if (!o || !f) return;
  const h = horse(f.dataset.h); if (h) { o.innerHTML = pnPaths(h, "horse"); const b = $("#pnCardBar"); if (b) b.innerHTML = pnCardBar(h); }
}
function pnRefreshFoal() {
  if (!S.foal) return; const o = $("#pnFoalOpts"), b = $("#pnFoalBar");
  if (o) o.innerHTML = pnPaths(S.foal.h, "foal"); if (b) b.innerHTML = pnFoalBar(S.foal.h);
}

/* ================= The new foal: its outlook and its options under the card ================= */
function pnFoal() {
  let box = $("#foal");
  if (!S.foal) { if (box) box.remove(); return; }
  const F = S.foal, h = F.h, p = pnHe(h);
  if (box && box.dataset.id === h.id) return;          // already showing this foal: leave the card playing
  if (box) box.remove();
  box = document.createElement("div"); box.id = "foal"; box.className = "foal-wrap"; box.dataset.id = h.id; document.body.appendChild(box);
  box.innerHTML = `<div class="foal pn-foal" role="dialog" aria-label="Your new ${h.sex === "F" ? "filly" : "colt"}">${cardBox()}
    <div class="fc-in">
      <div class="fc-kicker">${F.how === "bred" ? "Born at the stud" : "Knocked down to you at Tattersalls"}</div>
      <div class="fc-sex ${h.sex}">${h.sex === "F" ? "♀ FILLY" : "♂ COLT"}</div>
      <label class="fc-name"><span>Name</span><input id="foalName" value="${esc2(h.name)}" maxlength="18" autocomplete="off"></label>
      <div class="fc-ped fc-wait">by <b>${esc2(h.sire)}</b> out of <b>${esc2(h.dam)}</b></div>
      <div class="fc-facts fc-wait"><span>Rated <b>${ratingAt(h, 2)}</b> as a 2YO</span><span>Best <b>${tripText(tripAt(h, 2))}</b></span><span>Likes <b>${h.grounds.join(", ")}</b></span><span>Runs <b>${STYLE_NAME[h.style]}</b>, ${h.temper}</span></div>
      <div class="fc-wait">${pnOutlook(h)}</div>
      <div class="fc-wait fc-choose" id="pnFoalOpts">${pnPaths(h, "foal")}</div>
      <div class="pn-bar fc-wait fc-choose" id="pnFoalBar">${pnFoalBar(h)}</div>
      ${agentButton(F) ? `<div class="fc-btns fc-wait fc-choose">${agentButton(F)}</div>` : ""}
      <p class="fc-small fc-wait">${F.how === "bred" ? `Stud fee ${money(F.cost)}. ${esc2(h.dam)} has been covered for this season.` : `Bought for ${money(F.cost)}.`}</p>
    </div></div>`;
  wireCard();
  toCard({ type: "reveal", horse: cardPayload(h, 2) });
  setTimeout(() => { const f = box.querySelector(".foal"); if (f) f.classList.add("done"); }, 9000);
}

// the foal's buttons, kept in reach at the foot of the screen: save it as it is, or develop it to its best age
function pnFoalBar(h) {
  const p = pnHe(h), ages = [2, 3, 4], all = ages.flatMap(a => RACES.map(r => pnOpt(h, r, [a])).filter(o => o && o.v !== "x"));
  const best = all.length ? all.reduce((m, o) => pnValue(o) > pnValue(m) ? o : m) : null, n = pnFoalFlags().length;
  const dev = best && best.age > 2 ? `<button class="tb-btn" type="button" data-keepdev="${best.age}">Develop to ${best.age}<small>the best path</small></button>` : "";
  return `<span class="pn-barinfo">${PN_FLAG}<b>${n ? `${n} flagged` : "No flags yet"}</b></span>
    <button class="tb-btn ${dev ? "ghost" : ""}" id="keep" type="button">${dev ? `Decide later<small>save as a 2-year-old</small>` : `Save ${p.o}<small>as a 2-year-old</small>`}</button>${dev}`;
}
// the horse card's buttons, in reach too
function pnCardBar(h) {
  const n = pnFlagsOf(h).length;
  return `<span class="pn-barinfo">${PN_FLAG}<b>${n ? `${n} flagged` : "No flags yet"}</b></span><button class="tb-btn" type="button" data-pclose="1">${pnCanEnter() ? "Back to entries" : "Back to the planner"}</button>`;
}

/* ================= Wiring it in ================= */
if (!PLAN_OLD) {
  plannerView = pnPlanner;
  renderFoal = pnFoal;
  showHorseCard = pnHorseCard;
  showDevelop = pnHorseCard;     // (h, fromAge): the card with its options, not the old "Developed" pop-up
  // keeping a foal: its flags become race targets, and the planner opens with it at the top
  const _keepFoal = keepFoal;
  keepFoal = function (name) {
    const F = S.foal; if (!F) return _keepFoal(name);
    const id = F.h.id, fl = (F.flags || []).slice();
    _keepFoal(name);
    if (!horse(id)) return;
    fl.forEach(rid => { pnFlags()[rid] = id; });
    UI.pn.fresh = id; UI.pn.open = {}; UI.pn.more = {};
    const show = fl.length ? fl : RACES.filter(r => { const o = pnOpt(horse(id), r, pnAgesFrom(horse(id))); return o && o.v !== "x"; }).map(r => r.id).slice(0, 2);
    show.forEach(rid => { UI.pn.open[rid] = true; });
    if (S.step <= 2) S.view = "plan";
    save();
  };
  // the planner's way back: to the stud, or to the sale ring
  // (with mares still to breed, or lots still to buy, going back is the likely next step, so it's the main button)
  const back = (orig, label, more) => function () {
    const f = orig.apply(this, arguments);
    if (!(S.view === "plan" && !S.foal && S.step <= 2)) return f;
    const m = more(), main = !!m;
    return `<button class="tb-btn ${main ? "" : "ghost"}" type="button" data-pview="job">${label}${m ? `<small>${m}</small>` : ""}</button>` + (main ? f.replace(/class="tb-btn\s*"/g, 'class="tb-btn ghost"') : f);
  };
  FOOTS.stud = back(FOOTS.stud, "Back to the stud", () => { const n = typeof handDone === "function" && !handDone() ? 1 : S.hand.length; return n ? (handDone() ? `${n} mare${n === 1 ? "" : "s"} to breed` : "draw your mares") : ""; });
  FOOTS.tatts = back(FOOTS.tatts, "Back to the sale ring", () => S.sale && S.sale.length && S.stable.length < STABLE_CAP ? `${S.sale.length} lots left` : "");
  // the key points of each step, as the new screens have them (js/ui-flow.js HEADLINES)
  const hl = HEADLINES;
  const _breed = hl.breed, _sales = hl.sales, _gallops = hl.gallops, _entries = hl.entries;
  hl.breed = () => { const H = _breed(); H.pts.splice(2, 0, "Each foal shows <b>its outlook and every race it could run</b>. Flag the ones you like: your race planner opens next, then <b>Back to the stud</b> for the next mare."); return H; };
  hl.sales = () => { const H = _sales(); H.pts.splice(3, 0, "A yearling you buy shows its outlook and races just like a foal, then goes into your race planner."); return H; };
  hl.gallops = () => { const H = _gallops(); H.pts[0] = "Every horse arrives as a 2-year-old. A race for 3-year-olds needs it <b>developed to 3</b>: your race planner says which do (<b>Develop to 3</b>), and there's no going back."; return H; };
  hl.entries = () => { const H = _entries(); H.pts[H.pts.length - 1] = "<b>Fill empty races</b> enters your flagged horses from the race planner first, then the best free horse for every race still without a runner."; return H; };
  // a new size of screen may want the other planner (the grid on a computer, the list on a phone)
  let pnWas = pnWide();
  addEventListener("resize", () => { const w = pnWide(); if (w !== pnWas) { pnWas = w; if (document.querySelector(".pn")) render(); } });
}
document.addEventListener("click", e => {
  if (PLAN_OLD) return;
  const t = e.target.closest && e.target.closest("button"); if (!t) return;
  const d = t.dataset;
  if (d.ropen) { UI.pn.open[d.ropen] = !UI.pn.open[d.ropen]; render(); return; }
  if (d.rmore) { UI.pn.more[d.rmore] = !UI.pn.more[d.rmore]; render(); return; }
  if (d.pall) { RACES.forEach(r => { UI.pn.open[r.id] = d.pall === "1"; }); render(); return; }
  if (d.pview) { try { localStorage.setItem(pnViewKey(), d.pview); } catch (err) {} render(); return; }
  if (d.pgo) { try { localStorage.setItem(pnViewKey(), "grid"); } catch (err) {} UI.pn.open[d.pgo] = true; render();
    const el = document.querySelector(`[data-prow="${d.pgo}"], .pn-race[data-race="${d.pgo}"]`);
    if (el) { el.scrollIntoView({ block: "center", behavior: "smooth" }); el.classList.add("pn-hl"); setTimeout(() => el.classList.remove("pn-hl"), 2200); } return; }
  if (d.pstring) { try { localStorage.setItem("tb-string", pnStringOpen() ? "closed" : "open"); } catch (err) {} render(); return; }
  if (d.ptips) { pnPlanTips(true); return; }
  if (d.pclose) { const b = $("#devCard"); if (b) b.remove(); cardFrame = null; return; }
  if (d.pview) { S.view = d.pview; UI.pn.fresh = null; save(); render(); sheetTop(); return; }
  if (d.pflag) { const [rid, hid] = d.pflag.split(":"), h = horse(hid), r = RACES.find(x => x.id === rid); if (!h || !r) return;
    const was = horse(pnFlags()[rid]); pnSetFlag(rid, hid);
    toast(pnFlagged(h, r) ? `${h.name} flagged for the ${r.name}${was && was !== h ? ` (in place of ${was.name})` : ""}` : `Flag taken off the ${r.name}`);
    render(); pnRefreshCard(); return; }
  if (d.ffl) { const fl = pnFoalFlags(), i = fl.indexOf(d.ffl); if (i >= 0) fl.splice(i, 1); else fl.push(d.ffl); save();
    pnRefreshFoal(); return; }
  if (d.fpicks) { if (!S.foal) return; const h = S.foal.h, picks = pnPicksFor(h, true); S.foal.flags = picks.map(o => o.r.id); save();
    pnRefreshFoal();
    toast(picks.length ? `Your trainer's picks: ${picks.map(o => shortRace(o.r)).join(", ")}` : `Your trainer can't find a race for ${pnHe(h).o} yet`); return; }
  if (d.hpicks) { const h = horse(d.hpicks); if (!h) return; const picks = pnPicksFor(h, false); picks.forEach(o => { pnFlags()[o.r.id] = h.id; }); save();
    toast(picks.length ? `Your trainer's picks: ${picks.map(o => shortRace(o.r)).join(", ")}` : `Your trainer can't find a race for ${pnHe(h).o} yet`); render(); pnRefreshCard(); return; }
  if (d.ppicks) { const n = pnPicksAll(); toast(n ? `Your trainer flagged ${n} more race${n === 1 ? "" : "s"}` : "Every race your horses can run is flagged already"); render(); return; }
  if (d.fkeep) { const b = document.getElementById("keep"); if (b) b.click(); return; }
  if (d.devto) { const [hid, a] = d.devto.split(":"), h = horse(hid); if (!h || !canDev(h)) return;
    const from = h.age; while (h.age < +a) develop(hid);
    const T = pnFlags(), lost = RACES.filter(r => T[r.id] === hid && h.age > r.ages[1]);
    lost.forEach(r => { delete T[r.id]; }); save();
    render(); showDevelop(h, from); BOARD.Sound.hooves && BOARD.Sound.hooves(2);
    if (lost.length) setTimeout(() => toast(`Too old now for the ${lost.map(r => r.name).join(" and ")}: those flags are off`), 900);
    return; }
  if (d.ptrip) { const [hid, dir] = d.ptrip.split(":"), h = horse(hid); if (!h) return;
    if (doJob("trip", h, { dir: +dir })) toast(`${h.name}: best trip now ${tripText(tripAt(h, h.age))}`); else toast(jobProblem("trip", h, { dir: +dir }) || "Not possible now");
    render(); pnRefreshCard(); return; }
}, true);
// a card pop-up closed in the middle of its animation: its last message has nowhere to go
if (!PLAN_OLD) { const _toCard = toCard; toCard = function (m) { try { _toCard(m); } catch (e) {} }; }
