// =====================================================================================================================
// Thoroughbred, the career hub: the screens (prototype, 20 Nov 2026). The host is js/career/core.js (window.CAREER);
// the rules behind it are js/career/rules/rules.js (window.TBRULES). The horse sheet, the entry and gallop choices,
// the sale ring, the stallion list and race day are the "Thoroughbred Career" prototype's screens
// (js/career/rules/reference/ui.js), redrawn in the hub's look.
//
// How it is laid out:
//   - The Newmarket board is home. Each place on it is a part of the stable, and a tap goes straight to its screen.
//   - The same screens are on the five-way bar (Map, Calendar, Horses, Money, More), so nothing is ever more than a tap away.
//   - The card on the board ("this week") lists what needs doing, each line a shortcut, and holds the one gold button
//     that moves the week on. With runners, that button goes to race day: the racecard, the race, the result, one race
//     at a time; then the week in full.
//   - A screen is one of the game's sheets; a choice (which horse, which stallion, which gallop) slides up over it.
// Everything is drawn from the state by render(); every tap is a data-act handled in ACT below.
// NEVER show a horse's hidden numbers (pot, ability(), mat, trip, gr, build, temp, con): screens read h.k, h.gs and view().
// =====================================================================================================================
(() => {
"use strict";
const C = window.CAREER, B = window.BOARD, D = window.CAREER_DATA, R = window.TBRULES, LAB = R.LAB;
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = C.money, T = () => C.TIERS[C.tierOf(S)];
const ico = (n) => `<svg viewBox="0 0 512 512" aria-hidden="true">${window.ICON[n] || ""}</svg>`;
const ARR = `<svg class="arr" viewBox="0 0 10 16" aria-hidden="true"><path d="M1.6 0 0 1.6 6.4 8 0 14.4 1.6 16l8-8z"/></svg>`;
const BACK = `<svg viewBox="0 0 10 16"><path d="M8.4 0 10 1.6 3.6 8 10 14.4 8.4 16l-8-8z"/></svg>`;
const STAR = `<path d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L10 14.9 4.8 17.6l1-5.8L1.5 7.7l5.9-.8z"/>`;
const NAVI = { map: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3 3 5.5v15.5l6-2.5 6 2.5 6-2.5V3l-6 2.500L9 3zm0 2.200 6 2.500v11.100l-6-2.500V5.200zM5 6.900l2-.800v11.100l-2 .800V6.900zm14 10.200-2 .800V6.800l2-.800v11.100z"/></svg>`,
  more: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h7v6H4V5zm9 0h7v6h-7V5zM4 13h7v6H4v-6zm9 0h7v6h-7v-6z"/></svg>` };

// ---------------------------------------------------------------- the save (this browser only)
const KEY = "tb-career-hub-2";
function load() { try { const t = localStorage.getItem(KEY); if (t) { const s = JSON.parse(t); if (s && s.v === 2 && s.horses && s.cards) return C.use(s); } } catch (e) {} return null; }
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
let S = load() || C.newGame((Date.now() % 2147483647) | 0);
const UI = { sheet: null, tab: {}, horse: null, lot: null, tile: "trip", calWeek: S.week, meet: {}, picker: null, dockShut: false, big: "g1", report: null, rd: null, after: null, key: "" };

// ---------------------------------------------------------------- the places and the five ways in
const WHOLE = [724, 560, 1448];
const PLACE = {
  jockey: { title: "The Racing Calendar", kicker: "The Jockey Club", medal: `<span class="jc">JC</span>`, tabs: [["week", "This week"], ["season", "The season"], ["big", "Big races"]] },
  stables: { title: "Your Horses", kicker: "Your stables", medal: ico("stable") },
  warren: { title: "The Gallops", kicker: "Warren Hill", medal: `<span class="hz"></span>` },
  tatts: { title: "The Sales", kicker: "Tattersalls", medal: ico("gavel") },
  stud: { title: "The Stud", kicker: "National Stud", medal: ico("horse-head") },
  palace: { title: "The Owner's Office", kicker: "Palace House", medal: ico("greek-temple"), tabs: [["money", "Money"], ["rep", "Reputation"], ["goals", "Goals and trophies"]] },
  races: { title: "This Week's Runners", kicker: "To the races", medal: `<span class="hz"></span>` },
  more: { title: "Newmarket", kicker: "Everything in one place", medal: `<span class="hz"></span>`, pic: WHOLE },
  news: { title: "The Post", kicker: "News from the yard", medal: ico("scroll-unfurled"), pic: WHOLE },
  raceday: { title: "Race day", kicker: "", medal: ico("checkered-flag"), pic: [1110, 330, 520] },
  report: { title: "The Week's Racing", kicker: "", medal: ico("checkered-flag"), pic: [1110, 330, 520] },
};
const NAV = [["map", "Map", NAVI.map], ["jockey", "Calendar", ico("calendar")], ["stables", "Horses", ico("horse-head")], ["palace", "Money", ico("two-coins")], ["more", "More", NAVI.more]];

// ---------------------------------------------------------------- small pieces
const he = (h) => (h.sex === "f" ? "she" : "he"), him = (h) => (h.sex === "f" ? "her" : "him"), his = (h) => (h.sex === "f" ? "her" : "his"), He = (h) => (h.sex === "f" ? "She" : "He");
const ordinal = (n) => (n % 10 === 1 && n !== 11 ? "st" : n % 10 === 2 && n !== 12 ? "nd" : n % 10 === 3 && n !== 13 ? "rd" : "th");
const hash = (s) => { let x = 7; for (let i = 0; i < s.length; i++) x = (x * 31 + s.charCodeAt(i)) | 0; return x >>> 0; };
const starTxt = (n) => "★".repeat(n) + "☆".repeat(5 - n);
// potential, from the trainer's estimate only: gold is what he is sure of, pale what the horse might be
const potOf = (h) => ({ lo: R.potStar(h.k.pe - h.k.pw), hi: R.potStar(h.k.pe + h.k.pw) });
const starsHtml = (h, big) => { const p = potOf(h), a = Math.min(5, Math.floor(p.lo + 0.25)), b = Math.min(5, Math.max(a, Math.ceil(p.hi - 0.25)));
  return `<span class="kstars${big ? " big" : ""}" title="Potential: gold is sure, pale is possible">${[1, 2, 3, 4, 5].map((i) => `<svg viewBox="0 0 20 20" class="${i <= a ? "s1" : i <= b ? "s2" : "s0"}">${STAR}</svg>`).join("")}</span>`; };
const pword = (h) => { const p = potOf(h), a = R.potWord(p.lo), b = R.potWord(p.hi); return a === b ? a : p.hi - p.lo > 2.6 ? "Could be anything" : a + " to " + b.toLowerCase(); };
const freshHtml = (h) => `<span class="fresh ${h.fresh < 50 ? "low" : h.fresh < 75 ? "mid" : ""}"><span class="barx"><span style="width:${h.fresh}%"></span></span>${h.inj > 0 ? `Off ${h.inj} wk` : h.fresh >= 90 ? "Fresh" : h.fresh >= 75 ? "Ready" : h.fresh >= 50 ? "A bit flat" : "Tired"}</span>`;
const formHtml = (h) => (h.form.length ? `<span class="form">${h.form.slice(-6).map((p) => (p === 1 ? "<em>1</em>" : p)).join("-")}</span>` : `<span class="form" style="color:#9d978a;font-weight:700">Unraced</span>`);
const who = (h) => `${h.age}yo ${C.sexWord(h)} · by ${esc(h.sire)}`;
const coat = (h) => `<span class="coat ${h.colour || "bay"}"><span></span></span>`;
const rated = (h) => `<span class="mark"><b>${h.or != null ? h.or : "–"}</b><i>${h.or != null ? "Rating" : "No rating"}</i></span>`;
function typeChip(r) {
  const t = r.type;
  if (t === "Group 1") return `<span class="chip g1">Group 1</span>`;
  if (t === "Group 2" || t === "Group 3") return `<span class="chip g2">${t}</span>`;
  if (t === "Listed") return `<span class="chip l">Listed</span>`;
  if (t === "Heritage handicap") return `<span class="chip hh">Heritage handicap</span>`;
  if (t === "Handicap" || t === "Nursery") return `<span class="chip h">${t === "Nursery" ? "Nursery" : "Handicap"} ${r.band} · Class ${r.cls}</span>`;
  if (t === "Seller" || t === "Claimer") return `<span class="chip s">${t} · Class ${r.cls}</span>`;
  if (t === "Sales race") return `<span class="chip s">Sales race</span>`;
  if (t === "Classified") return `<span class="chip h">Classified ${r.band}</span>`;
  return `<span class="chip m">${t} · Class ${r.cls}</span>`;
}
const SEXT = { F: " fillies", C: " colts & geldings", CF: " colts & fillies", "": "" };
const cond = (r) => `${r.dist} · ${r.ages}${SEXT[r.sex]} · ${r.lo}–${r.hi} runners`;
const kindChip = (m) => (m.kind === "Festival" ? `<span class="chip fest">Festival</span>` : m.kind === "Premier" ? `<span class="chip prem">Premier</span>` : m.kind === "Feature" ? `<span class="chip prem">Feature race</span>` : "")
  + (m.evening ? `<span class="chip eve">Evening</span>` : "") + (m.aw ? `<span class="chip aw">All-weather</span>` : "");
// the trainer's chance chip, and how the trip, the ground and the track fit (✓ suits, ~ so-so, ✕ against, ? untested;
// an outlined mark is only a guess)
const chipHtml = (v) => `<span class="ch k${v.lv}">${v.label}${v.unsure ? " ?" : ""}</span>`;
const tick = (label, f, guess) => `<span class="tk ${{ y: "ok", m: "so", n: "no", q: "q" }[f]}${guess ? " gs" : ""}"><i>${{ y: "✓", m: "~", n: "✕", q: "?" }[f]}</i>${label}</span>`;
const fitRow = (v) => tick("Trip", v.fit.trip, v.fit.tripq) + tick(v.going && v.going !== "Standard" ? v.going : "Ground", v.fit.gr, v.fit.grq) + tick("Track", v.fit.tr, v.fit.trq);
const revs = (r) => (r && r.length ? `<div class="revs">${r.map((x, i) => `<span class="rev" style="animation-delay:${i * 0.15}s"><i>${esc(x[0])}</i>${esc(x[1])}</span>`).join("")}</div>` : "");
// colours: a rival's are the owner's own artwork; yours are a stand-in until the stable has colours of its own
const slk = (x, h) => (x.you ? `<span class="slk me" style="height:${h}px;width:${Math.round(h * 0.76)}px" aria-hidden="true"></span>` : `<img class="slk" style="height:${h}px;width:${Math.round(h * 0.76)}px" src="img/silks/${(D.rivals[x.s] || D.rivals[0]).pic}.webp" alt="">`);
const ownerOf = (x) => (x.you ? S.stable : (D.rivals[x.s] || {}).name || "");
const day = (iso) => C.fmtDay(iso, S.yr);
const weekName = (w) => C.weekInfo(w).label;
const entriesOpen = (w) => w >= S.week && w <= S.week + 3;
const trackOf = (m) => (m.course === "Newmarket" ? (m.date >= "2026-06-20" && m.date <= "2026-08-31" ? "Newmarket (July Course)" : "Newmarket (Rowley Mile)") : m.course);
const lengths = (x) => (x < 0.08 ? "a nose" : x < 0.15 ? "a short head" : x < 0.3 ? "a head" : x < 0.6 ? "a neck" : x >= 20 ? "a distance" : (() => { const q = Math.round(x * 2) / 2, w = Math.floor(q); return (w ? w : "") + (q - w ? "½" : "") + (q > 1 ? " lengths" : " length"); })());
function toast(text, bad) { const t = $("toast"); t.textContent = text; t.className = "tb-toast show" + (bad ? " error" : ""); clearTimeout(toast.t); toast.t = setTimeout(() => (t.className = "tb-toast"), 2600); }
// the trainer's one line on a horse
function note(h) {
  if (h.inj > 0) return `On the easy list. Back in ${h.inj} week${h.inj > 1 ? "s" : ""}.`;
  if (h.fresh < 50) return `${He(h)} needs a rest. Run ${him(h)} now and we risk an injury.`;
  if (h.fresh < 75) return `A bit flat after ${his(h)} last run. Another week off would do ${him(h)} good.`;
  if (h.runs === 0) { if (h.age === 2 && h.k.mat >= 1 && h.gs.mat === "l") return `Backward. ${He(h)} will be a different horse next year, so expect little yet.`; return h.k.pw > 12 ? `Ready to run. We won't know what we have until ${he(h)} sees a racecourse.` : `Ready to run, and the work says ${he(h)} can win.`; }
  if (h.or == null) return `One more run and the handicapper gives ${him(h)} a rating.`;
  const d = R.estAb(h) - h.or; if (d >= 5) return `I think ${he(h)} is ahead of ${his(h)} rating. Strike while we can.`;
  if (d <= -5) return `The handicapper has ${him(h)} in his grip. Easier races, or wait for ${his(h)} ground.`;
  if (h.form[h.form.length - 1] === 1) return "In great heart since winning.";
  if (h.age <= 3 && h.k.mat === 2 && h.gs.mat !== "e") return `Still growing up. ${He(h)} improves with every week.`;
  return ["Working well and ready to go.", "Eating up and bouncing.", "Same as ever. Honest as the day."][h.id % 3];
}

// ---------------------------------------------------------------- money you can see leaving and arriving
function tumble(amt) {
  const el = document.querySelector(".cs.bank"); if (!el || !amt) return;
  const r = el.getBoundingClientRect(), L = $("tumble"), tag = document.createElement("div");
  tag.className = "ktag " + (amt < 0 ? "out" : "in"); tag.textContent = (amt > 0 ? "+" : "") + money(amt);
  tag.style.top = r.bottom + 4 + "px"; tag.style.right = Math.max(6, innerWidth - r.right) + "px"; L.appendChild(tag); setTimeout(() => tag.remove(), 2300);
  if (amt < 0) for (let i = 0, n = Math.min(26, 3 + Math.round(Math.sqrt(-amt) / 9)); i < n; i++) { const c = document.createElement("i"); c.className = "coin";
    c.style.left = r.left + r.width * (0.2 + Math.random() * 0.6) + "px"; c.style.top = r.bottom - 6 + "px"; c.style.setProperty("--x", (Math.random() * 120 - 60).toFixed(0) + "px");
    c.style.setProperty("--y", (180 + Math.random() * 240).toFixed(0) + "px"); c.style.setProperty("--d", (0.8 + Math.random() * 0.8).toFixed(2) + "s"); c.style.animationDelay = (i * 0.03).toFixed(2) + "s"; L.appendChild(c); setTimeout(() => c.remove(), 2200); }
  el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
}
// do something to the game, show the money moving, save, redraw
function act(fn) { const before = S.cash, out = fn(); const d = S.cash - before; save(); render(); if (d) tumble(d); return out; }
// On race day the results are already in the save, so the bank and the reputation shown are held back to the races
// that have been watched: the bar must not give a result away.
function seen() {
  const rd = S.rd; if (!rd) return { cash: S.cash, rep: S.rep };
  let cash = rd.cash0, rep = rd.rep0;
  rd.res.forEach((x, i) => { if (i < rd.i || (i === rd.i && UI.rd && UI.rd.stage === "result")) { cash += x.mine[0].prize + (x.hub.claimed || 0); rep += x.mine[0].rep; } });
  return { cash, rep };
}
const tierFor = (rep) => { let t = 1; for (let i = 2; i <= 5; i++) if (rep >= C.TIERS[i].rep) t = i; return t; };

// ---------------------------------------------------------------- the bar, the five ways in, the board
function drawBar() {
  const wk = C.weekInfo(S.week), cost = C.weeklyCost(S), now = seen(), t = tierFor(now.rep), nx = C.TIERS[t + 1];
  const p = nx ? Math.round((now.rep - C.TIERS[t].rep) / (nx.rep - C.TIERS[t].rep) * 100) : 100;
  $("brandWhere").textContent = S.stable;
  $("stats").innerHTML = `<button class="cs" data-act="open" data-sheet="jockey" type="button" aria-label="The calendar"><b>${wk.label}</b><i>${C.fmtSpan(S.week, S.yr)} ${C.yearOf(S.week, S.yr)}</i></button>
    <button class="cs bank ${now.cash < 0 ? "kneg" : ""}" data-act="open" data-sheet="palace" data-tab="money" type="button" aria-label="Money"><b>${money(now.cash)}</b><i>${money(cost.perWeek)} a week</i></button>
    <button class="cs krep" data-act="open" data-sheet="palace" data-tab="rep" type="button" aria-label="Reputation"><span class="kring" style="--p:${p}"><span>${t}</span></span><span class="t"><b>${C.TIERS[t].n}</b><i>${nx ? `${now.rep} of ${nx.rep}` : `${now.rep} points`}</i></span></button>`;
}
function badges() {
  const td = C.todos(S), n = (k) => { const x = td.find((q) => q.k === k); return x ? x.n || 1 : 0; }, unread = S.news.filter((x) => !x.read).length;
  return { td, stables: n("enter"), warren: n("gallop"), tatts: n("sale") ? "Sale on" : 0, stud: n("cover") + n("box"), races: C.runners(S).length, money: n("bank") ? "!" : 0, unread };
}
function drawNav() {
  const b = badges(), dot = { stables: b.stables, palace: b.money, more: (b.warren ? 1 : 0) + (b.tatts ? 1 : 0) + (b.stud ? 1 : 0) + (b.unread ? 1 : 0) };
  const on = UI.sheet ? (NAV.some((n) => n[0] === UI.sheet) ? UI.sheet : "more") : "map";
  $("nav").innerHTML = NAV.map(([id, label, svg]) => `<button type="button" data-act="${id === "map" ? "close" : "open"}" data-sheet="${id}" class="${on === id ? "on" : ""}">${svg}<span>${label}</span>${dot[id] && !S.rd ? `<i class="dot">${dot[id]}</i>` : ""}</button>`).join("");
}
function drawBoard() {
  const b = badges(), tag = { stables: b.stables && `${b.stables} ready to run`, warren: b.warren && `${b.warren} gallop${b.warren > 1 ? "s" : ""}`, tatts: b.tatts && "Sale on", stud: b.stud && `${b.stud} to do`, races: b.races && `${b.races} runner${b.races > 1 ? "s" : ""}` };
  const st = {}; for (const id of ["warren", "palace", "jockey", "tatts", "stables", "stud", "races"]) st[id] = tag[id] ? "next" : "open";
  B.states = st; B.setStates(st); UI.tags = tag;
  for (const id of Object.keys(tag)) { const el = id === "races" ? $("races") : B.stage.querySelector(`.loc[data-id="${id}"]`), nt = el && el.querySelector(".nexttag"); if (nt && tag[id]) nt.textContent = tag[id]; }
}
// On a phone the board fills the space between the bar and this week's card (so the card never hides a place) and
// slides sideways. A place off the side that needs something gets a pointer at the edge: a tap slides the board to it.
let dockH = -1;
function fitBoard() {
  const phone = matchMedia("(max-width: 860px)").matches, h = phone ? (UI.sheet ? dockH : $("dock").offsetHeight) : -2;
  if (h === dockH) return; dockH = h;
  document.documentElement.style.setProperty("--dock-h", h + "px"); B.fit(); centre(); drawEdges();
}
function centre() { if (B.view.classList.contains("pan")) B.view.scrollLeft = (UI.panX || 800) * B.scale - B.view.clientWidth / 2; }
function drawEdges() {
  const box = $("edges"), v = B.view; if (!v.classList.contains("pan") || UI.sheet) { box.innerHTML = ""; return; }
  const r = v.getBoundingClientRect(), tags = UI.tags || {}, L = [], Rr = [];
  for (const id of Object.keys(tags)) { if (!tags[id]) continue; const p = B.placeOf(id), x = p.at[0] * B.scale - v.scrollLeft, y = r.top + p.at[1] * B.scale;
    if (x < 30) L.push({ id, y, p }); else if (x > r.width - 30) Rr.push({ id, y, p }); }
  const side = (list, cls) => { list.sort((a, b) => a.y - b.y); let last = -99; return list.map((e) => { const y = Math.min(r.bottom - 34, Math.max(r.top + 8, e.y - 15, last + 36)); last = y;
    return `<button type="button" class="edge ${cls}" style="top:${y.toFixed(0)}px" data-act="pan" data-id="${e.id}">${cls === "l" ? "‹ " : ""}${esc(e.p.title)}${cls === "r" ? " ›" : ""}</button>`; }).join(""); };
  box.innerHTML = side(L, "l") + side(Rr, "r");
}
B.view.addEventListener("scroll", () => { UI.panX = (B.view.scrollLeft + B.view.clientWidth / 2) / B.scale; requestAnimationFrame(drawEdges); }, { passive: true });
addEventListener("resize", () => { dockH = -1; setTimeout(fitBoard, 60); });
// a tap on a place goes straight to its screen (the board's own preview card is not used here)
B.onChoose = (id) => { if (!id) return; B.choose(null); open(id); };
B.cardFor = (id) => ({ title: (PLACE[id] || {}).title || "" });

// ---------------------------------------------------------------- this week: the card on the board
const TDI = { enter: "horse-head", sale: "gavel", gallop: "stopwatch", cover: "horseshoe", box: "stable", bank: "two-coins" };
function goLabel() { const n = C.runners(S).length, nxt = S.week === C.NW ? "The new season" : C.isWinter(S.week + 1) || C.isWinter(S.week) ? "Next month" : "Next week";
  return S.rd ? "Back to the races" : n ? `Go racing <small>${n} runner${n > 1 ? "s" : ""}</small>` : nxt; }
function drawDock() {
  const wk = C.weekInfo(S.week), b = badges(), run = C.runners(S), rows = [];
  if (S.rd) rows.push(`<li><button type="button" data-act="open" data-sheet="raceday"><span class="ic run">${ico("checkered-flag")}</span><span class="tx"><b>At the races</b><span>Race ${S.rd.i + 1} of ${S.rd.res.length}</span></span>${ARR}</button></li>`);
  else {
    if (run.length) rows.push(`<li><button type="button" data-act="open" data-sheet="races"><span class="ic run">${ico("checkered-flag")}</span><span class="tx"><b>${run.length} runner${run.length > 1 ? "s" : ""} this week</b><span>${run.map((x) => esc(x.h.n) + " at " + x.r.m.course).join(" · ")}</span></span>${ARR}</button></li>`);
    for (const t of b.td) rows.push(`<li><button type="button" data-act="open" data-sheet="${t.go}"${t.go === "palace" ? ' data-tab="money"' : ""}><span class="ic">${ico(TDI[t.k])}</span><span class="tx"><b>${esc(t.text)}</b><span>${esc(t.sub)}</span></span>${ARR}</button></li>`);
    if (b.unread) rows.push(`<li><button type="button" data-act="open" data-sheet="news"><span class="ic quiet">${ico("scroll-unfurled")}</span><span class="tx"><b>${b.unread} new in the post</b><span>${esc(S.news.find((x) => !x.read).title)}</span></span>${ARR}</button></li>`);
    if (!rows.length) rows.push(`<li><button type="button" data-act="open" data-sheet="jockey"><span class="ic quiet">${ico("calendar")}</span><span class="tx"><b>Nothing needs doing</b><span>Look ahead in the calendar, or move on.</span></span>${ARR}</button></li>`);
  }
  const idle = !S.rd && b.td.some((t) => t.k === "enter");
  // on a computer the card is a column beside the board, with room for the week's note and the string at a glance
  const str = S.rd ? "" : S.horses.map((h) => { const rid = h.entries[S.week], r = rid != null ? C.RACES[rid] : null;
    return `<button type="button" data-act="openHorse" data-h="${h.id}">${coat(h)}<span class="tx"><b>${esc(h.n)}</b><span class="${r ? "go" : ""}">${h.inj > 0 ? `Off for ${h.inj} week${h.inj > 1 ? "s" : ""}` : r ? `Runs ${day(r.m.date)} · ${esc(r.m.course)} · ${r.dist}` : h.fresh < 75 ? "Resting after a run" : "Ready · no race this week"}</span></span><span class="rtg">${h.or != null ? h.or : "–"}</span></button>`; }).join("");
  $("dock").className = "dock" + (UI.dockShut ? " shut" : "");
  $("dock").innerHTML = `<button class="dock-h" type="button" data-act="dock" aria-expanded="${!UI.dockShut}"><span class="t"><span class="k">${wk.label} · ${C.fmtSpan(S.week, S.yr)} · ${wk.phase}</span><b>${esc(wk.title)}</b></span>
      <span class="count">${rows.length}</span><span class="chev">${ARR}</span></button>
    ${wk.note ? `<p class="dock-note">${esc(wk.note)}</p>` : ""}
    <ul class="todo">${rows.slice(0, 5).join("")}</ul>
    <div class="dock-str">${S.rd ? "" : `<div class="k">Your string · ${S.horses.length} of ${T().boxes} boxes</div>${str || `<p class="dock-note">No horses in training.</p>`}`}</div>
    <div class="dock-go">${idle ? `<button class="ghostb" type="button" data-act="picks">Trainer's<br>picks</button>` : ""}<button class="gold" type="button" data-act="advance">${goLabel()}${ARR}</button></div>`;
}

// ---------------------------------------------------------------- sheets
function open(id, tab, extra) {
  if (S.rd) id = "raceday";                                      // race day is watched through before anything else
  if (id === "map") return close();
  if (!PLACE[id]) id = "more";
  UI.sheet = id; UI.horse = null; UI.lot = null; UI.picker = null; UI.tile = "trip"; if (tab) UI.tab[id] = tab;
  if (id === "raceday" && !UI.rd) UI.rd = { stage: "card" };
  if (id === "jockey" && !extra) UI.calWeek = S.week;
  if (id === "tatts") S.saleSeen = true;
  if (id === "news") setTimeout(() => { S.news.forEach((n) => (n.read = true)); save(); drawNav(); }, 1200);
  Object.assign(UI, extra || {}); render(); $("shBody").scrollTop = 0;
}
function close() { if (S.rd) return open("raceday"); UI.sheet = null; UI.horse = null; UI.lot = null; UI.picker = null; render(); }
function drawSheet() {
  const id = UI.sheet, wrap = $("sheetWrap");
  document.body.classList.toggle("sheet-open", !!id); B.covered = !!id; B.setInPlace(id && B.placeOf(id) ? id : null);
  if (!id) { wrap.hidden = true; return; }
  const P = PLACE[id], tab = UI.tab[id] || (P.tabs && P.tabs[0][0]);
  wrap.hidden = false;
  let kicker = P.kicker, title = P.title;
  if (id === "report" && UI.report) kicker = `${weekName(UI.report.week)} · ${C.fmtSpan(UI.report.week, UI.report.yr)}`;
  if (id === "raceday" && S.rd) { const x = S.rd.res[S.rd.i], r = C.RACES[x.hub.rid]; kicker = `Race ${S.rd.i + 1} of ${S.rd.res.length} · ${day(r.m.date)} · ${trackOf(r.m)}`; title = r.name; }
  $("shKicker").textContent = kicker; $("shTitle").textContent = title; $("shMedal").innerHTML = P.medal;
  const pl = B.placeOf(id); B.paintPic($("shPic"), P.pic || (pl && pl.pic) || WHOLE, 0.72);
  $("shCloseT").textContent = id === "report" ? "Close" : "Back to the map"; $("shCloseT").parentNode.hidden = id === "raceday";
  const tabs = $("shTabs"); tabs.hidden = !P.tabs || !!UI.horse;
  if (P.tabs) tabs.innerHTML = P.tabs.map(([k, l]) => `<button type="button" data-act="tab" data-tab="${k}" class="${k === tab ? "on" : ""}">${l}</button>`).join("");
  const key = [id, tab, UI.horse, UI.lot, UI.calWeek, S.rd ? S.rd.i + (UI.rd || {}).stage : ""].join("/"), body = $("shBody"), keep = key === UI.key ? body.scrollTop : 0; UI.key = key;
  const foot = $("shFoot"); foot.hidden = true; foot.innerHTML = "";
  $("main").innerHTML = SCREEN[id](tab);
  body.scrollTop = keep;
  for (const el of $("main").querySelectorAll("[data-pic]")) { const q = B.placeOf(el.dataset.pic); B.paintPic(el, (q && q.pic) || WHOLE, 0.5); }
  if (UI.scrollTo) { const el = $("main").querySelector(UI.scrollTo); if (el) el.scrollIntoView({ block: "center" }); UI.scrollTo = null; }
  if (UI.after) { const f = UI.after; UI.after = null; f(); }
}
function footer(html) { const f = $("shFoot"); f.hidden = false; f.innerHTML = html; }
const SCREEN = {};

// ---------------------------------------------------------------- the calendar (the Jockey Club)
function raceRow(r, m) {
  const mine = S.horses.find((h) => h.entries[m.week] === r.id), past = m.week < S.week, canSee = !past && entriesOpen(m.week);
  let a = "";
  if (mine) a = `<span class="kmine"><span>✓ ${esc(mine.n)}</span>${past ? "" : `<button type="button" data-act="withdraw" data-h="${mine.id}" data-w="${m.week}" aria-label="Withdraw ${esc(mine.n)}">×</button>`}</span>`;
  else if (canSee) a = `<button class="btn sm ${S.horses.some((h) => !h.inj && !C.barred(S, h, r)) ? "" : "line"}" type="button" data-act="pickRace" data-r="${r.id}">${S.horses.some((h) => !h.inj && !C.barred(S, h, r)) ? "Enter" : "Field"}</button>`;
  return `<div class="krace ${r.big && r.type !== "Handicap" ? "big" : ""}" id="race-${r.id}"><span class="tm">${r.time}</span><div class="krt"><b>${esc(r.name)}</b><div class="ln">${typeChip(r)}<span>${cond(r)}</span></div></div><span class="pz">${money(r.prize)}</span><span class="act">${a}</span></div>`;
}
function meetRow(m) {
  const openIt = !!UI.meet[m.i], can = m.week >= S.week ? S.horses.filter((h) => !h.inj && m.races.some((r) => !C.barred(S, h, r))).length : 0, inn = S.horses.filter((h) => h.entries[m.week] != null && C.RACES[h.entries[m.week]].m === m).length;
  const big = m.races.filter((r) => r.big && r.type !== "Handicap" && r.type !== "Conditions").map((r) => r.name);
  const going = m.week === S.week ? `<span class="chip kgoing">${S.going[m.i]}</span>` : "";
  return `<div class="meet ${openIt ? "open" : ""} ${m.kind === "Festival" ? "fest" : ""}" id="meet-${m.i}"><button type="button" data-act="meet" data-m="${m.i}" aria-expanded="${openIt}">
      <div class="mt"><b>${esc(trackOf(m))}</b><i>${esc(m.name)}${big.length ? " · " + esc(big.slice(0, 3).join(", ")) : ""}</i><div class="cps">${kindChip(m)}${going}<span class="chip">${m.races.length} races</span></div></div>
      ${inn ? `<span class="can in">${inn} entered</span>` : can && entriesOpen(m.week) ? `<span class="can">${can} can run</span>` : ""}<svg class="chv" viewBox="0 0 10 16" aria-hidden="true"><path d="M1.6 0 0 1.6 6.4 8 0 14.4 1.6 16l8-8z"/></svg></button>
    ${openIt ? `<div class="kraces">${m.races.map((r) => raceRow(r, m)).join("")}</div>` : ""}</div>`;
}
SCREEN.jockey = (tab) => {
  if (tab === "season") return seasonView();
  if (tab === "big") return bigView();
  const w = UI.calWeek, wk = C.weekInfo(w), ms = C.MEETS_OF[w - 1], days = {};
  for (const m of ms) (days[m.date] = days[m.date] || []).push(m);
  const rel = w === S.week ? "This week" : w < S.week ? "Already run" : w === S.week + 1 ? "Next week" : `In ${w - S.week} weeks`;
  return `<div class="wkbar"><button class="nv" type="button" data-act="calWeek" data-w="${w - 1}" ${w <= 1 ? "disabled" : ""} aria-label="The week before">${BACK}</button>
      <div class="w"><i>${wk.label} · ${C.fmtSpan(w, S.yr)} · ${rel}</i><b>${esc(wk.title)}</b></div>
      ${w !== S.week ? `<button class="btn sm line now" type="button" data-act="calWeek" data-w="${S.week}">Today</button>` : ""}
      <button class="nv" type="button" data-act="calWeek" data-w="${w + 1}" ${w >= C.NW ? "disabled" : ""} aria-label="The week after"><svg viewBox="0 0 10 16"><path d="M1.6 0 0 1.6 6.4 8 0 14.4 1.6 16l8-8z"/></svg></button></div>
    ${wk.note ? `<p class="lede">${esc(wk.note)}</p>` : ""}
    ${w > S.week + 3 ? `<p class="knote">Entries open three weeks before a race. You can look as far ahead as you like.</p>` : ""}
    ${Object.keys(days).sort().map((d) => `<div class="kday">${day(d)}</div>${days[d].map(meetRow).join("")}`).join("")}`;
};
function seasonView() {
  let html = `<p class="lede">The racing year: <b>33 weeks on the turf</b> from the Lincoln to the November Handicap, then winter on the all-weather. Tap a week to see its meetings.</p>`, phase = "";
  for (const wk of C.WEEKS) {
    if (wk.phase !== phase) { phase = wk.phase; html += `<div class="phase">${phase}</div>`; }
    const mine = S.horses.filter((h) => h.entries[wk.w] != null).length;
    html += `<button class="wk ${wk.w < S.week ? "past" : wk.w === S.week ? "now" : ""}" type="button" data-act="calWeek" data-w="${wk.w}" data-tab="week" id="wk-${wk.w}"><span class="n"><b>${wk.label}</b><i>${C.fmtSpan(wk.w, S.yr)}</i></span>
      <span class="t"><b>${esc(wk.title)}</b>${wk.g1.length ? `<i>${esc(wk.g1.join(" · "))}</i>` : ""}<span>${wk.n} meetings${wk.winter ? " over the month" : ""}</span></span>
      ${mine ? `<span class="kmine">${mine} entered</span>` : ""}${wk.w === S.week ? `<span class="ktag">Now</span>` : ""}</button>`;
  }
  return html;
}
const BIGF = [["g1", "Group 1", (r) => r.type === "Group 1"], ["g23", "Group 2 and 3", (r) => r.type === "Group 2" || r.type === "Group 3"], ["l", "Listed", (r) => r.type === "Listed"], ["hh", "Heritage handicaps", (r) => r.type === "Heritage handicap"], ["s", "Sales races", (r) => r.type === "Sales race"]];
function bigView() {
  const f = BIGF.find((x) => x[0] === UI.big) || BIGF[0], list = C.RACES.filter(f[2]);
  return `<div class="kfilters">${BIGF.map(([k, l]) => `<button type="button" data-act="big" data-k="${k}" class="${k === f[0] ? "on" : ""}">${l}</button>`).join("")}</div>
    <p class="lede">${list.length} races through the year. Tap one to see its meeting.</p>
    ${list.map((r) => { const w = r.m.week, d = w - S.week, won = S.trophies.some((t) => t.race === r.name); return `<button class="bigr ${d < 0 ? "past" : ""}" type="button" data-act="goRace" data-r="${r.id}"><span class="d">${day(r.m.date)}<br>${d < 0 ? "Run" : d === 0 ? "This week" : `In ${d} wk`}</span>
      <span class="t"><b>${esc(r.name)}${won ? ` <span class="ktg">Won</span>` : ""}</b><i>${esc(r.m.course)} · ${r.dist} · ${r.ages}${SEXT[r.sex]}</i></span><span class="pz">${money(r.prize)}</span></button>`; }).join("")}`;
}

// ---------------------------------------------------------------- your horses (the stables)
function planLine(h) {
  const rid = h.entries[S.week];
  if (h.inj > 0) return `<div class="plan"><div class="p"><b>On the easy list</b>Back in ${h.inj} week${h.inj > 1 ? "s" : ""}.</div></div>`;
  if (rid != null) { const r = C.RACES[rid], v = C.view(S, h, r);
    return `<div class="plan run"><div class="p"><b>Runs ${day(r.m.date)} at ${esc(r.m.course)}</b>${esc(r.name)} · ${r.dist} · ${money(r.prize)}</div>${chipHtml(v)}<button class="x" type="button" data-act="withdraw" data-h="${h.id}" data-w="${S.week}" aria-label="Withdraw">×</button></div>`; }
  const later = Object.keys(h.entries).map(Number).filter((w) => w > S.week).sort((a, b) => a - b)[0];
  const lt = later ? `Entered ${day(C.RACES[h.entries[later]].m.date)}: ${esc(C.RACES[h.entries[later]].name)}, ${esc(C.RACES[h.entries[later]].m.course)}` : h.fresh < 75 ? "Resting. Freshness comes back week by week." : "Fresh and ready.";
  return `<div class="plan"><div class="p"><b>No race this week</b>${lt}</div><button class="btn sm" type="button" data-act="pickHorse" data-h="${h.id}">Find a race</button></div>`;
}
function horseCard(h) {
  return `<div class="hcard" id="h-${h.id}"><button class="top" type="button" data-act="horse" data-h="${h.id}">${coat(h)}<span class="id"><b>${esc(h.n)}</b><i>${who(h)}</i></span>${rated(h)}</button>
    <div class="kfacts">${starsHtml(h)}<span class="tk">${pword(h)}</span>${freshHtml(h)}${formHtml(h)}</div><p class="say">“${note(h)}”</p>${planLine(h)}</div>`;
}
SCREEN.stables = () => {
  if (UI.horse) { const h = C.horse(S, UI.horse); if (h) return horseView(h, "mine"); UI.horse = null; }
  const free = C.boxesFree(S), idle = C.todos(S).some((t) => t.k === "enter");
  return `<div class="sec"><h2>In training</h2><span>${S.horses.length} of ${T().boxes} boxes${free > 0 ? ` · ${free} free` : " · full"}</span>${idle ? `<button class="btn sm line r" type="button" data-act="picks">Trainer's picks</button>` : ""}</div>
    ${S.horses.length ? `<div class="rows">${S.horses.map(horseCard).join("")}</div>` : `<div class="empty">The yard is empty. Tattersalls is the place to start.</div>`}
    <p class="knote"><b>Stars</b> are the trainer's view of how good a horse could be: gold is sure, pale is possible. <b>Rating</b> is the handicapper's number, earned after two runs or a win. Tap a horse to see everything known about it.</p>
    <div class="sec"><h2>More</h2></div>
    <div class="rows"><button class="btn line" type="button" data-act="open" data-sheet="warren">The gallops · ${T().gal - S.gallops} left this week</button><button class="btn line" type="button" data-act="open" data-sheet="tatts">Buy or sell at Tattersalls</button></div>`;
};
// The horse sheet: nine tiles that fill in as gallops and races teach you, and a plain sentence for each.
const CRAFT = ["Green", "Learning", "Nearly there", "Professional"];
function tiles(h) {
  const k = h.k, g = h.gs, q = (lv, txt) => (lv === 0 ? "?" : txt + (lv === 1 ? "?" : ""));
  const pips = `<span class="gp">${["H", "S", "G", "Qr", "Qk"].map((l, i) => { const kn = k.gr[i], gu = k.gh ? (R.groundMod(k.gh, i) > 0 ? 2 : R.groundMod(k.gh, i) === 0 ? 1 : 0) : null; return `<u class="${kn != null ? "g" + kn : gu != null ? "h" + gu : ""}">${l}</u>`; }).join("")}</span>`;
  const t = [["mat", "Maturity", q(k.mat, LAB.mat[g.mat]), k.mat], ["trip", "Best trip", q(k.trip, R.tripLabel(g.trip)), k.trip], ["gr", "Ground", pips, k.gsure ? 2 : 1],
    ["build", "Build", q(k.build, LAB.build[g.build]), k.build], ["style", "Style", q(k.style, LAB.style[h.style]), k.style], ["temp", "Temperament", q(k.temp, LAB.temp[g.temp]), k.temp],
    ["con", "Constitution", q(k.con, LAB.con[g.con]), k.con], ["quirk", "Quirk", k.quirk === 2 ? (h.quirk ? R.QUIRKS[h.quirk] : "None") : "?", k.quirk === 2 ? 2 : 0], ["craft", "Racecraft", CRAFT[Math.min(3, h.craft)], 2]];
  return `<div class="t9s">${t.map((x) => `<button class="t9 k${x[3]}${UI.tile === x[0] ? " on" : ""}" type="button" data-act="tile" data-k="${x[0]}"><i>${x[1]}</i><b>${x[2]}</b></button>`).join("")}</div>`;
}
function tileInfo(h, key) {
  const k = h.k, g = h.gs, H = He(h), unk = "Not known yet. Gallops give a first idea; racing settles it.";
  switch (key) {
    case "mat": return k.mat ? { e: `${H} is forward. At ${his(h)} best at two and three.`, n: "A normal developer. Peaks at three and four.", l: `${H} needs time. Best at four and five, so go gently early on.` }[g.mat] + (k.mat < 2 ? " That is your trainer's guess." : "") : unk;
    case "trip": return `${H} is ${k.trip < 2 ? "bred for" : "best over"} ${R.tripLabel(g.trip)}. Each step away from that costs about 5 lb.` + (k.trip < 2 ? " A run over the trip will confirm it." : "");
    case "gr": return "Heavy, Softer, Good, Quicker, Quick. Solid green means proven on it (worth 5 lb), amber means copes, red means hates it. Outlines are guesses from the pedigree. Each going must be raced on to be sure.";
    case "build": return k.build ? { gal: `A long-striding galloper. Best on big galloping tracks. Sharp and undulating tracks cost ${him(h)} lengths until ${he(h)} learns them.`, agi: `Nimble and balanced. At ${his(h)} best on sharp and undulating tracks.`, ver: "Handles any track." }[g.build] + (k.build < 2 ? " That is a guess from how " + he(h) + " moves." : "") : "Not known yet. A run on a sharp or undulating track will tell you.";
    case "style": return k.style ? { F: "Likes to lead. Suited by a slow pace, when nobody takes " + him(h) + " on.", P: "Races just behind the leaders. Rarely caught out by the pace.", M: "Sits in midfield. Slightly suited by a strong pace.", H: "Held up at the back. Needs a strong pace to run at." }[h.style] : "You will see it the first time " + he(h) + " runs.";
    case "temp": return k.temp ? { calm: "Laid-back. Runs to the same level almost every time.", even: "Honest. Usually runs " + his(h) + " race.", hot: "Highly strung. Brilliant one day, flat the next, and dislikes slow paces and big fields." }[g.temp] + (k.temp < 2 ? " A first impression only." : "") : unk;
    case "con": return k.con ? { tough: "Tough. Ready to run again after a week off.", sound: "Sound. A fortnight between races suits " + him(h) + ".", del: "Delicate. Needs three weeks to get over a race." }[g.con] + (k.con < 2 ? " A first impression only." : "") : unk;
    case "quirk": return k.quirk === 2 ? R.QDESC[h.quirk || "none"].replace("three fortnights", "six weeks") : "Quirks only show on the racecourse. Some horses have none.";
    default: return ["Green. First time out a horse gives away about 6 lb through inexperience.", "Learning. Still gives away a few pounds.", "Nearly there.", "A professional. Nothing lost to inexperience."][Math.min(3, h.craft)] + " Every run teaches. Schooling on the gallops helps too.";
  }
}
// kind: "mine" (in training), "young" (at the stud) or "lot" (in the sale ring)
function horseView(h, kind, lot) {
  const mine = kind === "mine", stage = h.age < 2 ? (h.age === 1 ? "Yearling" : "Foal") + " " + (h.sex === "f" ? "filly" : "colt") : `${h.age}yo ${C.sexWord(h)}`;
  let b = `<button class="back" type="button" data-act="horse" data-h="">${BACK}${mine ? "All your horses" : kind === "lot" ? "Back to the sale" : "Back to the stud"}</button>
    <div class="hcard"><div class="top" style="cursor:default">${coat(h)}<span class="id"><b>${esc(h.n)}</b><i>${stage}${h.bred ? " · homebred" : ""} · by ${esc(h.sire)} (${starTxt(h.ss)}) out of ${esc(h.dam)} (${starTxt(h.ds)})</i></span>${h.age >= 2 ? rated(h) : ""}</div>
      ${mine ? `<div class="kfacts">${freshHtml(h)}${formHtml(h)}</div><p class="say">“${note(h)}”</p>${planLine(h)}` : ""}</div>
    ${h.runs ? `<div class="big3"><div><b>${h.or == null ? "–" : h.or}</b><i>Rating</i></div><div><b>${h.runs}·${h.wins}·${h.pl}</b><i>Runs·wins·places</i></div><div><b>${money(h.earn)}</b><i>Prize money</i></div></div>` : ""}
    <div class="panel pot"><div><i>Potential</i>${starsHtml(h, true)}</div><b>${pword(h)}</b><p>Your trainer's estimate. The pale stars are what ${he(h)} might be. Gallops and runs sharpen it.</p></div>
    ${tiles(h)}<p class="explain">${tileInfo(h, UI.tile)}</p>`;
  if (h.big.length) b += `<div class="sec"><h2>Big wins</h2></div><div class="panel">${h.big.map(esc).join(", ")}</div>`;
  if (kind === "lot" && lot) b += `<div class="sec"><h2>In the ring</h2></div>${lotCard(lot, true)}`;
  if (mine) { const opts = optGroups(h, [4, 2, 2]); b += `<div class="sec"><h2>Races to suit</h2><span>this week and the next two</span></div>${opts || `<div class="empty">${h.inj > 0 ? "Nothing until " + he(h) + " is sound again." : "Nothing suitable in the next three weeks. Look further ahead in the calendar."}</div>`}`; }
  if (h.age >= 2) b += `<div class="sec"><h2>Races</h2></div>${h.hist.length ? `<div class="panel"><table class="kv">${h.hist.slice(-8).reverse().map((x) => `<tr><td><b>${x.pos === 1 ? "Won" : x.pos + ordinal(x.pos) + " of " + x.of}</b> · ${esc(x.n)}<i>${esc(x.co)} · ${R.fLabel(x.d)} · ${x.g == null ? "All-weather" : R.GOINGS[x.g]} · ${x.pos === 1 ? "won by " : "beaten "}${lengths(x.btn)}</i></td><td>${x.pr ? money(x.pr) : "–"}</td></tr>`).join("")}</table></div>` : `<div class="empty">${h.runs ? "Earlier runs were before your time with the horse." : "Yet to run."}</div>`}`;
  if (mine) { const v = C.valueOf(S, h), stud = R.canStud(h);
    b += `<div class="sec"><h2>Money</h2></div><div class="panel"><table class="kv"><tr><td>Won</td><td class="kpos">${money(h.earn)}</td></tr><tr><td>Bought for</td><td>${money(h.cost)}</td></tr><tr><td>Keep and entry fees with you</td><td>${money(h.kept)}</td></tr></table></div>
    <div class="sec"><h2>Decisions</h2></div><div class="rows"><button class="btn bad" type="button" data-act="askSell" data-h="${h.id}">Sell ${esc(h.n)} · ${money(v)}</button>
    ${h.sex === "f" && h.age >= 3 ? `<button class="btn line" type="button" data-act="retire" data-h="${h.id}" ${C.paddocksFree(S) > 0 ? "" : "disabled"}>Retire her to your stud${C.paddocksFree(S) > 0 ? "" : " (no paddock free)"}</button>` : ""}
    ${h.sex === "c" && stud ? `<button class="btn line" type="button" data-act="retire" data-h="${h.id}">Retire him to stand as a stallion · +${money(R.studFee(h))}</button>` : ""}</div>`; }
  if (kind === "young") b += `<div class="rows" style="margin-top:14px">${h.stage === "ready" ? `<button class="btn" type="button" data-act="toYard" data-h="${h.id}" ${C.boxesFree(S) > 0 ? "" : "disabled"}>${C.boxesFree(S) > 0 ? "Move into the yard" : "No box free"}</button>` : ""}<button class="btn bad" type="button" data-act="askSell" data-h="${h.id}">Sell · ${money(C.youngValue(S, h))}</button></div>`;
  return b;
}
// a horse's options, week by week: the best few of each, with the trainer's chance and how trip, ground and track fit
function optGroups(h, per) {
  const all = C.options(S, h, 2), out = [];
  for (let w = S.week; w <= S.week + 2 && w <= C.NW; w++) { const list = all.filter((o) => o.r.m.week === w); if (!list.length) continue;
    const best = list[0].v.claim ? null : list[0]; let rich = null; for (const x of list) if (!x.v.claim && x.v.win >= 0.06 && (!rich || x.v.ev > rich.v.ev)) rich = x; if (rich === best) rich = null;
    const show = list.slice(0, per[w - S.week]); if (rich && !show.includes(rich)) show.push(rich); const cur = list.find((o) => h.entries[w] === o.r.id); if (cur && !show.includes(cur)) show.unshift(cur);
    out.push(`<div class="kday">${w === S.week ? "This week" : w === S.week + 1 ? "Next week" : "In two weeks"} · ${esc(C.weekInfo(w).title)}${list.length > show.length ? ` · ${list.length} open to ${him(h)}` : ""}</div><div class="rows">${show.map((o) => optRow(h, o, h.entries[w] === o.r.id, o === best ? "Best chance" : o === rich ? "Big prize" : "")).join("")}</div>`); }
  return out.join("");
}
function optRow(h, o, cur, tag) {
  const r = o.r, v = o.v;
  return `<button class="kopt ${cur ? "cur" : ""}" type="button" data-act="enter" data-h="${h.id}" data-r="${r.id}"><span class="t"><b>${esc(r.name)}${tag ? ` <span class="ktg">${tag}</span>` : ""}</b><i>${esc(r.m.course)} · ${day(r.m.date)} · ${r.dist} · ${money(r.prize)}</i>
    <span class="ln">${typeChip(r)}${fitRow(v)}</span>${v.claim ? `<i style="color:var(--c-bad)">Every runner is for sale at ${money(v.claim)}</i>` : ""}${v.low ? `<i>Rated below this race: ${he(h)} would carry more than ${his(h)} rating deserves</i>` : ""}</span>
    <span class="r">${chipHtml(v)}<small>${cur ? "Entered ✓" : "Fee " + money(v.fee)}</small></span></button>`;
}

// ---------------------------------------------------------------- the gallops (Warren Hill)
SCREEN.warren = () => {
  const left = T().gal - S.gallops;
  return `<p class="lede"><b>${left} of ${T().gal} gallops left this week.</b> Work a horse to learn about it, school it to teach it the job, or give a tired one an easy week. Racing teaches most of all.</p>
    <div class="rows">${S.horses.map((h) => `<div class="hcard"><button class="top" type="button" data-act="openHorse" data-h="${h.id}">${coat(h)}<span class="id"><b>${esc(h.n)}</b><i>${who(h)}</i></span>${rated(h)}</button>
        <div class="kfacts">${starsHtml(h)}<span class="tk">${pword(h)}</span>${freshHtml(h)}<span class="tk">${CRAFT[Math.min(3, h.craft)]}</span></div>
        <div class="plan"><div class="p">${h.galloped ? "Has been out this week." : h.inj > 0 ? "On the easy list." : left > 0 ? (h.k.pw > 8 ? "Still something of a mystery." : h.craft < 3 ? "Has more to learn about racing." : "The trainer knows this one well.") : "No gallops left this week."}</div>
          <button class="btn sm" type="button" data-act="pickGallop" data-h="${h.id}" ${h.galloped || h.inj > 0 || left <= 0 ? "disabled" : ""}>Gallops</button></div></div>`).join("") || `<div class="empty">No horses in training.</div>`}</div>
    <p class="knote">More gallops a week come with reputation: ${C.TIERS.slice(1).map((t) => `${t.n} ${t.gal}`).join(", ")}. Each horse can go out once a week.</p>`;
};

// ---------------------------------------------------------------- the sales (Tattersalls): the ring, with a rival bidder on every lot
const LOOKS = ["Small and backward", "Plain, but a good walker", "Athletic, with a lovely action", "A real eyecatcher"], WH = ["Not for me.", "Fine. Nothing special.", "I like this one.", "I love this one. Don't lose it."];
const mareLine = (m) => `${starTxt(m.stars)} · ${R.tripLabel(Math.min(6, m.opt))} · ${R.groundLabel(m.gr)}`;
const KINDW = { yearling: "Yearling", breeze: "Two-year-old", foal: "Foal" };
function lotCard(l, bare) {
  const nb = R.nextBid(l), toStud = l.kind === "yearling" || l.kind === "foal"; let top, mid, say = "";
  if (l.m) { const m = l.m; top = `<span class="id"><b>${esc(m.n)}</b><i>Broodmare, ${m.age}yo</i></span>`; mid = `<span class="tk">${mareLine(m)}</span>`; }
  else { const h = l.h, sire = R.sireOf(h.sire);
    top = `<span class="id"><b>${esc(h.n)}</b><i>${l.kind === "hit" ? `${h.age}yo ${C.sexWord(h)} in training, rated ${h.or}` : `${KINDW[l.kind]} ${h.sex === "f" ? "filly" : "colt"}`} · by ${esc(h.sire)} (${starTxt(h.ss)}) out of a ${starTxt(h.ds)} mare</i></span>`;
    if (l.kind === "hit") { mid = `${starsHtml(h)}<span class="tk">${h.runs} runs, ${h.wins} win${h.wins === 1 ? "" : "s"} · best at ${R.tripLabel(h.trip)} · ${LAB.con[h.con]}, ${LAB.temp[h.temp].toLowerCase()}</span>`; say = "You know what you're getting. Ready to run."; }
    else { mid = `${starsHtml(h)}<span class="tk">${LOOKS[h.looks]} · bred for ${R.tripLabel(h.gs.trip)}${sire ? " · sire's stock like " + R.groundLabel(sire.gr).toLowerCase() : ""}${l.secs ? ` · breezed two furlongs in ${l.secs.toFixed(2)}s` : ""}</span>`; say = WH[l.wh]; } }
  let actn;
  if (l.done === "you") actn = `<div class="plan run"><div class="p"><b>Yours for ${money(l.price)}.</b>${l.m ? "She is in your paddocks." : toStud ? "At the stud until two." : "In the yard."}</div></div>`;
  else if (l.done) actn = `<div class="plan"><div class="p">Sold to ${esc(l.by)} for ${money(l.price)}.</div></div>`;
  else { const full = l.m ? C.paddocksFree(S) <= 0 : toStud ? C.youngRoom(S) <= 0 : C.boxesFree(S) <= 0, poor = nb > S.cash;
    actn = `<div class="plan"><div class="p">${l.lead === "riv" ? `<b>${esc(l.by)} bids ${money(l.price)}.</b>` : ""}${full ? (l.m ? "No paddock free." : toStud ? "No room at the stud." : "No box free in the yard.") : poor ? "More than the bank holds." : l.lead ? "" : "No bid yet."}</div>
      <button class="btn sm" type="button" data-act="bid" data-l="${l.id}" ${full || poor ? "disabled" : ""}>Bid ${money(nb)}</button><button class="btn sm line" type="button" data-act="passLot" data-l="${l.id}">${l.lead ? "Let it go" : "Pass"}</button></div>`; }
  if (bare) return `<div class="hcard">${actn}</div>`;
  return `<div class="hcard ${l.done && l.done !== "you" ? "gone" : ""}"><${l.h ? `button type="button" data-act="lot" data-l="${l.id}"` : "div"} class="top"><span class="lotn">Lot<b>${l.id}</b></span>${top}<span class="mark"><b>${money(l.guide).replace(",000", "k")}</b><i>Guide</i></span></${l.h ? "button" : "div"}>
    <div class="kfacts">${mid}</div>${say ? `<p class="say">“${say}”</p>` : ""}${actn}</div>`;
}
SCREEN.tatts = () => {
  if (UI.lot) { const l = S.sale && S.sale.lots.find((x) => x.id === UI.lot); if (l && l.h) return horseView(l.h, "lot", l); UI.lot = null; }
  const ahead = Object.keys(C.SALES).map(Number).sort((a, b) => a - b);
  const list = ahead.map((w) => { const d = w - S.week; return `<tr><td><b>${esc(C.SALES[w].name)}</b><i>${weekName(w)} · ${C.fmtSpan(w, S.yr)} · ${esc(C.SALES[w].blurb)}</i></td><td>${d === 0 ? "On now" : d < 0 ? "Next year" : d === 1 ? "Next week" : `In ${d} weeks`}</td></tr>`; }).join("");
  const sell = S.horses.map((h) => `<tr><td><b>${esc(h.n)}</b><i>${who(h)}${h.or != null ? " · rated " + h.or : ""}</i></td><td><button class="btn sm bad" type="button" data-act="askSell" data-h="${h.id}">Sell · ${money(C.valueOf(S, h))}</button></td></tr>`).join("");
  const bf = C.boxesFree(S), pf = C.paddocksFree(S);
  return `${S.sale ? `<div class="banner"><i>${weekName(S.week)} · ${S.sale.lots.filter((l) => !l.done).length} lots to come</i><b>${esc(S.sale.name)}</b><span>${esc(S.sale.blurb)}</span></div>
      <p class="lede"><b>${money(S.cash)}</b> to spend · <b>${Math.max(0, bf)}</b> box${bf === 1 ? "" : "es"} free · <b>${pf}</b> paddock${pf === 1 ? "" : "s"} free. You know the pedigree, the look of them and what your trainer whispers. Another buyer wants every lot: bid until one of you stops.</p>
      <div class="rows">${S.sale.lots.map((l) => lotCard(l)).join("")}</div>`
    : `<div class="empty"><b>No sale at Tattersalls this week.</b><br>The sales come round through the year: the breeze-ups in spring, the yearlings in October, the mares in December.</div>`}
    <div class="sec"><h2>The sales this year</h2></div><div class="panel"><table class="kv">${list}</table></div>
    <div class="sec"><h2>Sell a horse</h2></div>
    <div class="panel">${sell ? `<table class="kv">${sell}</table>` : `<div class="empty">No horses in training.</div>`}</div>`;
};

// ---------------------------------------------------------------- the stud (National Stud)
SCREEN.stud = () => {
  if (UI.horse) { const y = S.young.find((x) => x.id === UI.horse); if (y) return horseView(y, "young"); UI.horse = null; }
  const openS = C.coveringOpen(S);
  const mare = (m) => `<div class="hcard"><div class="top" style="cursor:default"><span class="coat bay"><span></span></span><span class="id"><b>${esc(m.n)}</b><i>${m.age}yo broodmare${m.peakOR ? " · raced for you to " + m.peakOR : ""}</i></span>
      <span class="mark"><b>${m.stars}★</b><i>Class</i></span></div>
    <div class="kfacts"><span class="tk">${R.tripLabel(Math.min(6, m.opt))} · ${R.groundLabel(m.gr)}</span></div>
    <div class="plan ${m.inFoal ? "run" : ""}"><div class="p">${m.inFoal ? `<b>In foal to ${esc(m.inFoal.sire)}</b>${m.inFoal.due <= S.yr ? "Due this spring." : "Due next spring. The foal races two years after that."}` : `<b>Not in foal</b>${openS ? "The covering season is open until the end of May." : "The covering season opens in February."}`}</div>
      ${!m.inFoal && openS ? `<button class="btn sm" type="button" data-act="pickSire" data-m="${m.id}">Choose a stallion</button>` : ""}</div></div>`;
  const young = (h) => `<div class="hcard"><button class="top" type="button" data-act="horse" data-h="${h.id}">${coat(h)}<span class="id"><b>${esc(h.n)}</b><i>${h.stage === "foal" ? "Foal" : h.stage === "yearling" ? "Yearling" : "Two-year-old"} ${h.sex === "f" ? "filly" : "colt"} · by ${esc(h.sire)} out of ${esc(h.dam)}</i></span></button>
    <div class="kfacts">${starsHtml(h)}<span class="tk">${h.stage === "foal" ? "Too early to say much" : LOOKS[h.looks]}</span><span class="tk">${h.stage === "foal" ? "Races in two years" : h.stage === "yearling" ? "Comes into training in January" : "Ready for the yard"}</span></div>
    ${h.stage === "ready" ? `<div class="plan"><div class="p"></div><button class="btn sm" type="button" data-act="toYard" data-h="${h.id}" ${C.boxesFree(S) > 0 ? "" : "disabled"}>${C.boxesFree(S) > 0 ? "Move into the yard" : "No box free"}</button></div>` : ""}</div>`;
  const st = S.studs.filter((s) => s.until >= S.season);
  return `<div class="pipe"><div><b>${S.mares.length}</b><i>Mares · ${T().pad} paddocks</i></div><div><b>${S.young.filter((h) => h.stage === "foal").length}</b><i>Foals</i></div><div><b>${S.young.filter((h) => h.stage !== "foal").length}</b><i>Yearlings</i></div></div>
    <p class="lede">Breeding is the cheap way to a star, and the slow one: cover a mare this spring, the foal arrives next spring, and it races as a two-year-old the year after. The foal takes after both parents in class, trip, ground and build.</p>
    <div class="sec"><h2>Your mares</h2></div><div class="rows">${S.mares.map(mare).join("") || `<div class="empty">No mares. Retire a filly to stud, or buy a mare at the December Sale.</div>`}</div>
    <div class="sec"><h2>Foals and yearlings</h2></div><div class="rows">${S.young.map(young).join("") || `<div class="empty">No young stock yet.</div>`}</div>
    ${st.length ? `<div class="sec"><h2>Your stallions</h2></div><div class="panel"><table class="kv">${st.map((s) => `<tr><td><b>${esc(s.n)}</b><i>${starTxt(s.stars)} · ${R.tripLabel(s.opt)} · free to your mares</i></td><td></td></tr>`).join("")}</table></div>` : ""}`;
};

// ---------------------------------------------------------------- the owner's office (Palace House): money, reputation, goals
SCREEN.palace = (tab) => (tab === "rep" ? repView() : tab === "goals" ? goalsView() : moneyView());
function moneyView() {
  const c = C.weeklyCost(S), sum = (o) => Object.values(o).reduce((a, b) => a + b, 0), tin = sum(S.year.in), tout = sum(S.year.out), max = Math.max(1, ...Object.values(S.year.in), ...Object.values(S.year.out));
  const runway = c.perWeek ? Math.floor(Math.max(0, S.cash) / c.perWeek) : 99;
  const bars = (o, cls) => Object.entries(o).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<div class="barrow ${cls}"><div class="l"><span>${k}</span><b>${money(v)}</b></div><div class="b"><span style="width:${Math.max(2, v / max * 100)}%"></span></div></div>`).join("") || `<div class="empty">Nothing yet.</div>`;
  const net = (h) => h.earn - h.cost - h.kept;
  const per = S.horses.map((h) => `<tr><td><b>${esc(h.n)}</b><i>Won ${money(h.earn)} · bought for ${money(h.cost)} · keep ${money(h.kept)}</i></td><td class="${net(h) >= 0 ? "kpos" : "kneg"}">${money(net(h))}</td></tr>`).join("");
  const led = S.ledger.slice(-25).reverse().map((l) => `<tr><td>${esc(l.text)}<i>${l.cat} · ${weekName(l.w)}${l.s !== S.yr ? ", last season" : ""}</i></td><td class="${l.amt >= 0 ? "kpos" : "kneg"}">${l.amt > 0 ? "+" : ""}${money(l.amt)}</td></tr>`).join("");
  return `<div class="bankbox"><div class="big ${S.cash < 0 ? "kneg" : ""}"><i>In the bank</i><b>${money(S.cash)}</b></div>
      <div class="side">The yard costs <b>${money(c.perWeek)} a week</b>.<br>${S.cash < 0 ? "<b>Overdrawn:</b> sell a horse or win a race before you bid again." : runway > 60 ? "The bank would last more than a year with no winnings." : `With no winnings the bank lasts about <b>${runway} weeks</b>.`}<br>
      ${S.cash !== S.year.start ? `This season: <b>${S.cash - S.year.start >= 0 ? "up" : "down"} ${money(Math.abs(S.cash - S.year.start))}</b>.` : ""}</div></div>
    <div class="sec"><h2>What the yard costs each week</h2></div>
    <div class="panel"><table class="kv">${c.rows.map((r) => `<tr><td>${r.t}<i>${r.n} at ${money(r.each)} a week</i></td><td>${money(r.amt)}</td></tr>`).join("")}<tr class="tot"><td>Each week</td><td>${money(c.perWeek)}</td></tr></table></div>
    <div class="sec"><h2>This season</h2><span>in ${money(tin)} · out ${money(tout)}</span></div>
    <div class="bars"><div class="panel"><b>Money in</b>${bars(S.year.in, "")}</div><div class="panel"><b>Money out</b>${bars(S.year.out, "out")}</div></div>
    <div class="sec"><h2>Horse by horse</h2><span>what each has won, less what it has cost</span></div>
    <div class="panel">${per ? `<table class="kv">${per}</table>` : `<div class="empty">No horses in training.</div>`}</div>
    <div class="sec"><h2>The book</h2><span>the last 25 entries</span></div>
    <div class="panel">${led ? `<table class="kv">${led}</table>` : `<div class="empty">Nothing in the book yet.</div>`}</div>`;
}
function repView() {
  const t = C.tierOf(S), nx = C.TIERS[t + 1], tb = C.table(S), me = tb.findIndex((x) => x.you);
  const rung = (i) => { const x = C.TIERS[i]; return `<div class="rung ${i < t ? "done" : i === t ? "here" : "locked"}"><span class="no">${i < t ? "✓" : i}</span><span class="t"><b>${x.n}</b><i>${x.boxes} boxes · ${x.pad} paddocks · ${x.gal} gallops a week · stallions up to ${money(x.fee)} · a sharper trainer's eye</i>
      ${i === t && nx ? `<div class="kprog"><span style="width:${Math.round((S.rep - x.rep) / (nx.rep - x.rep) * 100)}%"></span></div>` : ""}</span><span class="pts">${i === t ? S.rep + " pts" : x.rep + " pts"}</span></div>`; };
  const show = new Set([0, 1, 2, me - 2, me - 1, me, me + 1, me + 2].filter((i) => i >= 0 && i < tb.length)); let last = -1, rows = "";
  tb.forEach((x, i) => { if (!show.has(i)) return; if (i - last > 1) rows += `<tr class="gapr"><td colspan="3">⋯</td></tr>`; last = i;
    rows += `<tr class="${x.you ? "you" : ""}"><td>${i + 1}</td><td>${x.pic ? `<img src="img/silks/${x.pic}.webp" alt="">` : ""}${esc(x.name)}${x.you ? " (you)" : ""}</td><td>${x.pts.toLocaleString("en-GB")}</td></tr>`; });
  const above = tb[me - 1];
  return `<p class="lede">Reputation comes from <b>winning and placing</b>, and the bigger the race the more it's worth: a Class 5 handicap 3 points, a Listed race 25, a Group 1 100. ${nx ? `<b>${nx.rep - S.rep} more</b> makes you a ${nx.n}.` : "You are at the top of the ladder."}</p>
    <div class="sec"><h2>The ladder</h2></div><div class="ladder">${[1, 2, 3, 4, 5].map(rung).join("")}</div>
    <div class="sec"><h2>The owners' table</h2><span>${me + 1}${ordinal(me + 1)} of ${tb.length}${above ? ` · next to catch: ${esc(above.name)}` : ""}</span></div>
    <div class="panel"><table class="tbl">${rows}</table></div>`;
}
function goalsView() {
  const goals = S.goals.map((g) => { const st = C.goalState(S, g); return `<div class="goal ${st.done ? "done" : ""}"><span class="bx">${st.done ? "✓" : ""}</span><span class="t">${esc(g.text)}<i>${st.money ? (st.have >= 0 ? "Up " : "Down ") + money(Math.abs(st.have)) + " so far" : `${Math.min(st.have, st.need)} of ${st.need}`}</i></span></div>`; }).join("");
  const tr = S.trophies.map((x) => `<tr><td><b>${esc(x.race)}</b><i>${esc(x.horse)} · ${esc(x.course)} · season ${x.s}</i></td><td>${money(x.prize)}</td></tr>`).join("");
  const hof = S.hof.slice().sort((a, b) => b.peak - a.peak).slice(0, 10).map((x) => `<tr><td><b>${esc(x.n)}</b><i>${x.wins} wins from ${x.runs} · ${money(x.earn)} · ${x.how}${x.big.length ? " · " + x.big.slice(0, 3).map(esc).join(", ") : ""}</i></td><td>${x.peak || "–"}</td></tr>`).join("");
  return `<div class="sec"><h2>This season's goals</h2></div><div class="panel">${goals}</div>
    <div class="sec"><h2>The trophy cabinet</h2><span>Group, Listed and heritage wins</span></div>
    <div class="panel">${tr ? `<table class="kv">${tr}</table>` : `<div class="empty">Empty for now. Your first big-race winner goes here.</div>`}</div>
    <div class="sec"><h2>The career so far</h2></div>
    <div class="panel"><table class="kv"><tr><td>Season</td><td>${S.yr}</td></tr><tr><td>Runs</td><td>${S.stats.runs}</td></tr><tr><td>Winners</td><td>${S.stats.wins}</td></tr>
      <tr><td>Best horse you've trained<i>${S.top ? esc(S.top.n) + ". Frankel was 140." : "No rated horse yet"}</i></td><td>${S.top ? S.top.or : "–"}</td></tr></table></div>
    ${hof ? `<div class="sec"><h2>Hall of fame</h2><span>the good ones who have moved on</span></div><div class="panel"><table class="kv">${hof}</table></div>` : ""}`;
}

// ---------------------------------------------------------------- to the races: this week's runners
SCREEN.races = () => {
  const run = C.runners(S);
  footer(`<span class="f-info">${run.length ? "Race day: each race in turn, then the week moves on." : "No runners: the week simply moves on."}</span><button class="gold" type="button" data-act="advance">${goLabel()}${ARR}</button>`);
  if (!run.length) return `<div class="empty"><b>No runners this week.</b><br>Enter a horse from its card or from the calendar, or let the trainer choose.</div>
    <div class="rows"><button class="btn" type="button" data-act="picks">Trainer's picks</button><button class="btn line" type="button" data-act="open" data-sheet="jockey">Open the calendar</button></div>`;
  return `<p class="lede">Your runners for <b>${esc(C.weekInfo(S.week).title)}</b>. The going is known for this week's meetings.</p>
    <div class="rows">${run.map(({ h, r }) => { const v = C.view(S, h, r); return `<div class="hcard"><button class="top" type="button" data-act="pickRace" data-r="${r.id}">${coat(h)}<span class="id"><b>${esc(h.n)}</b><i>${day(r.m.date)} · ${r.time} · ${esc(trackOf(r.m))}</i></span>${chipHtml(v)}</button>
      <div class="kfacts">${typeChip(r)}<span class="tk">${esc(r.name)} · ${r.dist} · ${money(r.prize)}</span></div>
      <div class="plan"><div class="p" style="display:flex;flex-wrap:wrap;gap:4px 12px">${fitRow(v)}${freshHtml(h)}</div><button class="x" type="button" data-act="withdraw" data-h="${h.id}" data-w="${S.week}" aria-label="Withdraw">×</button></div></div>`; }).join("")}</div>
    <p class="knote">Tap a runner to see the field it meets.</p>`;
};

// ---------------------------------------------------------------- race day: the racecard, the race, the result, one race at a time
const PACE = { fast: "Plenty of front-runners, so expect a strong pace. That suits horses held up.", slow: "No obvious leader, so expect a slow pace. That suits horses ridden near the front.", even: "An even pace looks likely. No excuses for anyone." };
const oddsCls = (t) => { const p = t === "Evens" ? 1 : ((a) => a[0] / a[1])(t.split("/").map(Number)); return p <= 4 ? "" : p <= 10 ? "o2" : p < 25 ? "o3" : "o4"; };
SCREEN.raceday = () => {
  const rd = S.rd; if (!rd) return "";
  const X = rd.res[rd.i], r = C.RACES[X.hub.rid], u = UI.rd = UI.rd || { stage: "card" }, n = rd.res.length, last = rd.i === n - 1, m = X.mine[0];
  const head = `<div class="kfacts rdh">${typeChip(r)}<span class="tk">${r.dist} · ${r.m.aw ? "All-weather" : X.hub.going} · ${R.TYPE[X.ty]} track · ${r.ages}${SEXT[r.sex]} · ${money(r.prize)} to the winner</span></div>`;
  if (u.stage === "card") {
    // (sorted by the betting, never by the finishing order: the result is already in the save)
    const dec = (t) => (t === "Evens" ? 1 : ((a) => a[0] / a[1])(t.split("/").map(Number))), list = X.run.slice().sort((a, b) => dec(a.od) - dec(b.od) || hash(a.n) - hash(b.n));
    footer(`<button class="ghostb" type="button" data-act="rdResult">Just the result</button><button class="gold" type="button" data-act="rdWatch">Watch the race${ARR}</button>`);
    return `${head}<p class="explain"><b>Pace forecast.</b> ${PACE[X.pace]}</p>
      <div class="panel rc">${list.map((x) => `<div class="rcl${x.you ? " me" : ""}">${slk(x, 30)}<span class="t"><b>${esc(x.n)}${x.you ? ` <span class="ktg">Yours</span>` : x.star ? ` <span class="ktg">Star</span>` : ""}</b><span>${esc(ownerOf(x))} · ${x.fm ? "form " + String(x.fm).split("").join("-") : "unraced"} · ${LAB.style[x.st]}${x.or != null && X.cap != null ? " · rated " + x.or : ""}</span></span><span class="odds ${oddsCls(x.od)}">${x.od}</span></div>`).join("")}</div>`;
  }
  if (u.stage === "run") {
    UI.after = () => playRace(X);
    footer(`<button class="ghostb" style="flex:1" type="button" data-act="rdResult">Skip to the result</button>`);
    return `${head}<div class="rv"><div class="hd"><span id="rvDist">${R.fLabel(X.f)} to run</span><span>${r.m.aw ? "All-weather" : X.hub.going}</span></div><div class="turf go" id="rvTurf"></div><p class="call" id="rvCall">They're going down to the start.</p></div>
      <p class="pk-note" style="text-align:center">A stand-in for the 3D race view.</p>`;
  }
  const top = X.run.slice(0, 4), extra = X.run.filter((x) => x.you && x.pos > 4);
  footer(`${last ? "" : `<button class="ghostb" type="button" data-act="rdAll">Skip the rest</button>`}<button class="gold" type="button" data-act="rdNext">${last ? "The week in full" : "Next race"}${ARR}</button>`);
  return `${head}<div class="panel rc">${top.concat(extra).map((x) => `<div class="rcl${x.you ? " me" : ""}"><span class="posb p${x.pos}">${x.pos}${ordinal(x.pos)}</span>${slk(x, 26)}<span class="t"><b>${esc(x.n)}</b><span>${esc(ownerOf(x))} · ${x.pos === 1 ? "winner" : lengths(x.btn) + " behind"} · ${x.od}</span></span></div>`).join("")}</div>
    <div class="res1${m.won ? " win" : ""}"><span class="posb big p${m.pos}">${m.pos}${ordinal(m.pos)}</span><span class="t"><b>${esc(X.hub.name)}${m.won ? " wins!" : ""}</b><span>${m.prize ? money(m.prize) + " prize money" : "No prize money"}${m.rep ? " · +" + m.rep + " reputation" : ""}</span></span>
      ${m.orNew != null ? `<span class="mark"><b>${m.orNew}</b><i>${m.orOld == null ? "First rating" : m.orNew > m.orOld ? "Up " + (m.orNew - m.orOld) : m.orNew < m.orOld ? "Down " + (m.orOld - m.orNew) : "Rating"}</i></span>` : ""}</div>
    <p class="quote">“${esc(m.say)}”</p>${X.hub.how ? `<p class="knote">${esc(X.hub.how)} In sellers and claimers every runner is for sale at the set price.</p>` : ""}
    ${m.rev.length ? `<div class="sec"><h2>What you learned</h2></div>${revs(m.rev)}` : ""}`;
};
// the race, drawn from its result: each runner's running style sets where it races early, and its beaten distance where it finishes
function playRace(X) {
  const turf = $("rvTurf"), call = $("rvCall"), dist = $("rvDist"); if (!turf) return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { UI.rd.stage = "result"; reveal(); return; }
  const run = X.run, n = run.length, lh = n <= 10 ? 26 : n <= 14 ? 22 : 19, W = turf.clientWidth, order = run.map((x, i) => i).sort((a, b) => hash(run[a].n) % 997 - hash(run[b].n) % 997);
  let rs = hash(X.n) + X.rid; const rr = () => { rs = (rs * 1664525 + 1013904223) | 0; return (rs >>> 0) / 4294967296; };
  const E = { F: [0, 1.2], P: [1.6, 3.2], M: [3.6, 5.6], H: [6, 8.5] }, d = run.map((x) => ({ e: E[x.st][0] + rr() * (E[x.st][1] - E[x.st][0]), g: Math.min(x.btn, 15), a: { F: 0.40, P: 0.45, M: 0.52, H: 0.6 }[x.st] + rr() * 0.07, w: rr() * 6.28 }));
  const gap = (i, t) => { const q = d[i]; let s = (t - q.a) / (1 - q.a); s = s < 0 ? 0 : s > 1 ? 1 : s * s * (3 - 2 * s); return q.e * (1 - s) + q.g * s + 0.3 * Math.sin(q.w + t * 10) * (1 - t); };
  const gaps = (t) => { const g = run.map((x, i) => gap(i, t)), mn = Math.min(...g); return g.map((x) => x - mn); };
  turf.style.height = n * lh + 6 + "px";
  turf.innerHTML = order.map((ri) => `<div class="lane${run[ri].you ? " me" : ""}" style="height:${lh}px"><div class="runner" data-i="${ri}">${run[ri].you ? `<span class="nm">${esc(run[ri].n)}</span>` : ""}${slk(run[ri], lh - 3)}</div></div>`).join("") + `<div class="rpost" id="rvPost"></div>`;
  const els = [...turf.querySelectorAll(".runner")], post = $("rvPost"), X0 = W * 0.72, ppl = (X0 - 24) / 13, DUR = 9000 + (X.f > 10 ? 2000 : 0) + (X.f > 14 ? 1500 : 0);
  const me = run.findIndex((x) => x.you), nameAt = (t, k) => { const g = gaps(t); return run.map((x, i) => [g[i], x]).sort((a, b) => a[0] - b[0])[k][1].n; }, rankAt = (t) => { const g = gaps(t); return g.filter((x) => x < g[me]).length + 1; };
  const where = (t) => { const r = rankAt(t); return r === 1 ? "leads" : r <= Math.max(2, n * 0.3) ? "is up with the pace" : r <= n * 0.65 ? "sits in midfield" : "is held up at the back"; };
  const mn = run[me].n, r85 = rankAt(0.86), fin = run[me].pos;
  const calls = [[0.02, `They're off in the ${X.n}!`], [0.2, `${nameAt(0.2, 0)} leads from ${nameAt(0.2, 1)}. ${mn} ${where(0.2)}.`], [0.5, `Halfway. ${nameAt(0.5, 0)} still in front. ${mn} ${where(0.5)}.`],
    [0.74, rankAt(0.74) > rankAt(0.5) + 1 ? `${mn} is coming under pressure.` : rankAt(0.74) < rankAt(0.5) ? `${mn} is making ground!` : `They're racing now. ${mn} ${where(0.74)}.`],
    [0.88, fin === 1 ? (r85 === 1 ? `${mn} has gone for home!` : `Here comes ${mn}! Flying down the outside!`) : fin <= 3 ? `${mn} is right there with every chance!` : `${nameAt(0.88, 0)} and ${nameAt(0.88, 1)} have it between them.`],
    [1, fin === 1 ? `${mn} wins${run[1] && run[1].btn > 2.5 ? " easily" : run[1] && run[1].btn < 0.4 ? " in a photo" : ""}!` : `${run[0].n} wins. ${mn} is ${fin}${ordinal(fin)}.`]];
  let ci = 0, t0 = 0; const token = UI.rd.token = Math.random();
  function frame(now) {
    if (!UI.rd || UI.rd.token !== token || UI.rd.stage !== "run" || !document.body.contains(turf)) return;
    if (!t0) t0 = now; const t = (now - t0) / DUR, tt = Math.min(1, t), g = gaps(tt), over = t > 1 ? (t - 1) * DUR / 1000 * 150 : 0;
    for (const el of els) { const i = +el.dataset.i; el.style.transform = `translateX(${Math.max(-30, X0 - g[i] * ppl + over - (lh - 3))}px)`; }
    post.style.transform = `translateX(${X0 + (1 - tt) * W * 2.4}px)`;
    while (ci < calls.length && tt >= calls[ci][0]) { call.textContent = calls[ci][1]; ci++; }
    dist.textContent = tt >= 1 ? "Finish" : R.fLabel(Math.max(0.5, Math.round(X.f * (1 - tt) * 2) / 2)) + " to run";
    if (t >= 1) turf.classList.remove("go");
    if (t < 1.22) requestAnimationFrame(frame); else setTimeout(() => { if (UI.rd && UI.rd.token === token && UI.rd.stage === "run") { UI.rd.stage = "result"; reveal(); } }, 500);
  }
  requestAnimationFrame(frame);
}
// a result comes up: the bar catches up with it, and a winner gets a cheer
function reveal() { const X = S.rd.res[S.rd.i], m = X.mine[0]; render(); $("shBody").scrollTop = 0; tumble(m.prize + (X.hub.claimed || 0)); if (m.won && B.Sound.cheer) B.Sound.cheer(3); }
function finishWeek() { const before = S.cash; UI.rd = null; UI.report = C.endWeek(S); UI.calWeek = S.week; UI.meet = {}; save(); UI.sheet = null; open("report"); tumble(S.cash - before); }

// ---------------------------------------------------------------- the week in full
SCREEN.report = () => {
  const Rp = UI.report; if (!Rp) return "";
  const nextW = C.weekInfo(S.week);
  footer(`<span class="f-info">Next: <b>${nextW.label}, ${esc(nextW.title)}</b></span><button class="gold" type="button" data-act="close">On to ${nextW.label}${ARR}</button>`);
  const prize = Rp.results.reduce((a, r) => a + r.prize, 0), keep = Rp.costs.perWeek * Rp.costs.weeks, claimed = Rp.results.reduce((a, r) => a + (r.claimed || 0), 0), wins = Rp.results.filter((r) => r.pos === 1).length;
  const res = Rp.results.map((r) => { const race = C.RACES[r.rid];
    return `<div class="kres p${r.pos}"><div class="top"><span class="posn"><b>${r.pos}</b><i>of ${r.n}</i></span><span class="t"><b>${esc(r.name)}</b><i>${esc(race.name)} · ${esc(race.m.course)} · ${race.dist} · ${r.going}</i>
        <i>${r.pos === 1 ? `Won by ${lengths(r.gap)}` : `Beaten ${lengths(r.gap)}${r.winner ? ` by ${esc(r.winner.horse)} (${esc(r.winner.owner)})` : ""}`}</i></span><span class="won">${r.prize ? "+" + money(r.prize) : ""}</span></div>
      <div class="say"><q>${esc(r.say)}</q><div class="lrn">${r.rev.map((x) => `<span>${esc(x[0])}: ${esc(x[1])}</span>`).join("")}${r.orOld != null && r.orNew !== r.orOld ? `<span>Rating ${r.orOld} → ${r.orNew}</span>` : r.orOld == null && r.orNew != null ? `<span>First rating: ${r.orNew}</span>` : ""}${r.rep ? `<span>+${r.rep} reputation</span>` : ""}</div></div></div>`; }).join("");
  const rv = Rp.review, n = Rp.results.length;
  return `${Rp.tierUp ? `<div class="banner"><i>Your reputation has grown</i><b>You are now a ${C.TIERS[Rp.tierUp].n}</b><span>${C.TIERS[Rp.tierUp].boxes} boxes · ${C.TIERS[Rp.tierUp].pad} paddocks · ${C.TIERS[Rp.tierUp].gal} gallops a week · better stallions and sale lots · a sharper trainer's eye</span></div>` : ""}
    ${rv ? `<div class="banner"><i>Season ${rv.season} is over</i><b>${rv.wins} winner${rv.wins === 1 ? "" : "s"} from ${rv.runs} runs</b><span>${money(rv.prize)} in prize money · in ${money(rv.in)}, out ${money(rv.out)} · ${rv.goals.filter((g) => g.done).length} of ${rv.goals.length} goals met</span></div>` : ""}
    <div class="sec"><h2>${!n ? "A quiet " + (C.isWinter(Rp.week) ? "month" : "week") : wins ? (wins === 1 ? "A winner" : wins + " winners") : Rp.results.some((r) => r.pos <= 3) ? "In the frame" : "No luck this time"}</h2>${n ? `<span>${n} runner${n > 1 ? "s" : ""}</span>` : ""}</div>
    ${res ? `<div class="rows">${res}</div>` : `<div class="empty">The horses stayed at home and freshened up.</div>`}
    ${Rp.events.length ? `<div class="sec"><h2>From the yard and the stud</h2></div><div class="panel"><table class="kv">${Rp.events.map((e) => `<tr><td>${esc(e.text)}</td><td></td></tr>`).join("")}</table></div>` : ""}
    <div class="sec"><h2>The money</h2></div>
    <div class="panel"><table class="kv"><tr><td>Prize money</td><td class="kpos">${prize ? "+" + money(prize) : "–"}</td></tr>${claimed ? `<tr><td>Horses sold out of their races</td><td class="kpos">+${money(claimed)}</td></tr>` : ""}
      <tr><td>The yard's keep${Rp.costs.weeks > 1 ? `<i>${Rp.costs.weeks} weeks</i>` : ""}</td><td class="kneg">${money(-keep)}</td></tr><tr class="tot"><td>In the bank</td><td>${money(Rp.cashAfter)}</td></tr></table></div>`;
};

// ---------------------------------------------------------------- everything in one place, and the post
SCREEN.more = () => {
  const b = badges(), tile = (id, title, sub, dot) => `<button class="gb" type="button" data-act="open" data-sheet="${id}" data-pic="${id}"><b>${title}</b><i>${sub}</i>${dot ? `<span class="dot">${dot}</span>` : ""}</button>`;
  return `<div class="kgrid">
      ${tile("stables", "Your Horses", `${S.horses.length} in training`, b.stables)}
      ${tile("jockey", "The Calendar", esc(C.weekInfo(S.week).title))}
      ${tile("warren", "The Gallops", `${T().gal - S.gallops} left this week`, b.warren)}
      ${tile("tatts", "The Sales", S.sale ? "A sale is on" : "Tattersalls", b.tatts ? "!" : 0)}
      ${tile("stud", "The Stud", `${S.mares.length} mares · ${S.young.length} young`, b.stud)}
      ${tile("palace", "Money and Reputation", `${money(S.cash)} · ${T().n}`, b.money)}
      ${tile("races", "To the Races", `${b.races} runner${b.races === 1 ? "" : "s"} this week`, b.races)}
      ${tile("news", "The Post", `${b.unread} unread`, b.unread)}
    </div>
    <div class="sec"><h2>How it works</h2></div>
    <div class="panel"><ul class="howto"><li><b>Rating.</b> The handicapper's number for what a horse has shown on the track. It comes after two runs or a win, and moves after every run.</li>
      <li><b>Handicaps.</b> Every horse carries weight to match its rating, so a horse that is better than its rating has the edge. Young, improving horses often are.</li>
      <li><b>Maidens</b> are for horses yet to win. <b>Listed and Group races</b> are level weights: the best horse usually wins.</li>
      <li><b>Potential stars.</b> Gold is what your trainer is sure of. Pale gold is what the horse might be.</li>
      <li><b>Freshness.</b> Racing takes it, rest restores it. Below the green a horse runs flat, and in the red it can get hurt.</li>
      <li><b>Trip, ground and track.</b> The wrong one costs lengths. You find out by trying.</li></ul></div>
    <div class="sec"><h2>About this prototype</h2></div>
    <div class="panel"><p style="margin:0;font-size:14px;line-height:1.5">The full game's home, menus and rules. The race you watch is a stand-in for the 3D race view. The game is saved in this browser.</p></div>
    <div class="rows" style="margin-top:12px"><button class="btn line" type="button" data-act="sound">Sound: ${B.Sound.on ? "on" : "off"}</button><button class="btn bad" type="button" data-act="askNew">Start a new career</button></div>`;
};
SCREEN.news = () => (S.news.length ? S.news.map((n) => `<button class="post ${n.read ? "read" : ""}" type="button" ${n.go ? `data-act="open" data-sheet="${n.go}"` : ""}><span class="u"></span><span class="t"><b>${esc(n.title)}</b><span>${esc(n.body)}</span><i>${weekName(n.w)}${n.s !== S.yr ? ", season " + n.s : ""}</i></span></button>`).join("") : `<div class="empty">Nothing in the post.</div>`);

// ---------------------------------------------------------------- choices that slide up over a screen
function drawPicker() {
  let p = UI.picker; const wrap = $("pickerWrap");
  // (a choice about a horse or mare that has since gone is dropped)
  if (p && ((p.hid && !C.horse(S, p.hid) && !S.young.some((x) => x.id === p.hid)) || (p.mid && !S.mares.some((x) => x.id === p.mid)))) p = UI.picker = null;
  wrap.hidden = !p; if (!p) return;
  let head = "", body = "";
  if (p.kind === "race") {
    const r = C.RACES[p.rid], w = r.m.week, race = C.raceOf(S, r), hc = race.cap != null;
    head = `<i>${day(r.m.date)} · ${esc(trackOf(r.m))}</i><b>${esc(r.name)}</b><span>${cond(r)} · ${money(r.prize)} to the winner${w === S.week ? " · going " + S.going[r.m.i].toLowerCase() : ""} · ${R.TYPE[race.ty].toLowerCase()} track${hc ? ` · rated ${R.floorOf(race)} to ${race.cap}` : ""}</span>`;
    body = `<div class="kday">Your horses</div>` + (S.horses.map((h) => { const why = C.whyNot(S, h, r);
      if (why) return `<button class="kopt" type="button" disabled><span class="t"><b>${esc(h.n)}</b><i>${esc(why)}</i></span></button>`;
      const v = C.view(S, h, r), cur = h.entries[w] === r.id, other = h.entries[w] != null && !cur ? C.RACES[h.entries[w]] : null;
      return `<button class="kopt ${cur ? "cur" : ""}" type="button" data-act="${cur ? "withdraw" : "enter"}" data-h="${h.id}" data-r="${r.id}" data-w="${w}"><span class="t"><b>${esc(h.n)}</b><i>${who(h)}${h.or != null ? " · rated " + h.or : ""}</i>
        <span class="ln">${fitRow(v)}${freshHtml(h)}</span>${other ? `<i>Would switch from the ${esc(other.name)} at ${esc(other.m.course)}</i>` : ""}${v.low ? `<i>Rated below this race</i>` : ""}</span>
        <span class="r">${chipHtml(v)}<small>${cur ? "Entered: tap to withdraw" : "Fee " + money(v.fee)}</small></span></button>`; }).join("") || `<div class="empty">No horses in training.</div>`);
    if (C.isClaim(r)) body += `<p class="pk-note"><b>${r.type}:</b> every runner is for sale at ${money(C.claimPrice(r))}. A horse worth more than that will very likely be bought.</p>`;
    const fld = race.field.slice().sort((a, b) => (b.ab - (hc ? b.or : 0)) - (a.ab - (hc ? a.or : 0)) + ((hash(a.n) % 7) - (hash(b.n) % 7)) * 0.9);
    body += `<div class="kday">The opposition · ${fld.length} runners</div><div class="panel rc">${fld.map((x) => `<div class="rcl">${slk(x, 26)}<span class="t"><b>${esc(x.n)}${x.star ? ` <span class="ktg">Star</span>` : ""}</b><span>${esc(ownerOf(x))} · ${x.fm ? "form " + String(x.fm).split("").join("-") : "unraced"} · ${LAB.style[x.st]}</span></span>${hc ? `<span class="mark"><b>${x.or}</b><i>Rating</i></span>` : ""}</div>`).join("")}</div>
      <p class="pk-note">The chip is your trainer's view of the chance, from what you know so far. A ? means untested; an outlined mark is a guess.</p>`;
  } else if (p.kind === "horse") {
    const h = C.horse(S, p.hid), opts = optGroups(h, [6, 4, 4]);
    head = `<i>Fresh ${Math.round(h.fresh)} · ${h.or == null ? "no rating yet" : "rated " + h.or}</i><b>Where does ${esc(h.n)} run?</b><span>The chip is your trainer's view of the chance, from what you know so far. A ? means untested.</span>`;
    body = opts || `<div class="empty">${h.inj > 0 ? "On the easy list." : "Nothing suitable in the next three weeks."}</div>`;
    body += `<p class="pk-note">Best chances first in each week. The whole year is in the calendar.</p>`;
  } else if (p.kind === "gallop") {
    const h = C.horse(S, p.hid), k = h.k, left = T().gal - S.gallops; let sch, schOk = true;
    if (h.quirk === "slowstart" && k.quirk === 2) sch = `Stalls practice, to cure ${his(h)} slow starts.`;
    else if (h.craft < 3) sch = `Teach ${him(h)} the job. A green horse gives away lengths, and this takes some of that off.`;
    else if (Math.min(h.prof.s, h.prof.u) < 2) sch = h.prof.s <= h.prof.u ? `Practice round tight turns, so sharp tracks cost ${him(h)} less.` : `Work up and down the hill, so undulating tracks cost ${him(h)} less.`;
    else { sch = `${He(h)} knows ${his(h)} job. Nothing left to teach.`; schOk = false; }
    const o = (a, t, d, ok) => `<button class="kopt" type="button" data-act="gallop" data-h="${h.id}" data-k="${a}" ${ok ? "" : "disabled"}><span class="t"><b>${t}</b><i>${d}</i></span></button>`;
    head = `<i>${left} gallop${left === 1 ? "" : "s"} left this week</i><b>${esc(h.n)} on the gallops</b><span>${who(h)}</span>`;
    body = o("work", "Work", `A serious gallop. Sharpens your idea of ${his(h)} potential and usually tells you something new. Takes a little freshness.`, true)
      + o("school", "School", sch, schOk) + o("easy", "Easy week", h.fresh >= 100 ? `${He(h)} is as fresh as can be.` : `Puts 30 back on ${his(h)} freshness, on top of the usual rest.`, h.fresh < 100);
  } else if (p.kind === "msg") {
    head = `<i>${esc(p.k)}</i><b>${esc(p.title)}</b>`;
    body = `<p class="quote">“${esc(p.say)}”</p>${revs(p.rev)}<div class="rows" style="margin-top:14px"><button class="btn" type="button" data-act="unpick">Carry on</button></div>`;
  } else if (p.kind === "sire") {
    const m = S.mares.find((x) => x.id === p.mid), mine = R.sires(), cap = T().fee, all = mine.concat(R.D.stallions.filter((s) => !mine.includes(s)))
      .sort((a, b) => (a.fee > cap) - (b.fee > cap) || (a.fee > S.cash) - (b.fee > S.cash) || (b.own || 0) - (a.own || 0) || b.stars - a.stars || a.fee - b.fee);
    head = `<i>Choose a stallion</i><b>${esc(m.n)}</b><span>She is ${mareLine(m)}. Stars are class. A sire also passes on his trip, his ground and when his stock mature.</span>`;
    body = all.map((s) => { const lock = !mine.includes(s), poor = !lock && s.fee > S.cash;
      return `<button class="kopt" type="button" data-act="cover" data-m="${m.id}" data-s="${esc(s.n)}" ${lock || poor ? "disabled" : ""}><span class="t"><b>${esc(s.n)} <span class="gold5">${"★".repeat(s.stars)}</span></b><i>${R.tripLabel(s.opt)} · ${R.groundLabel(s.gr)} · stock mature ${{ e: "early", n: "at three", l: "late" }[s.peak]}</i>
        ${lock ? `<i>His book opens at ${(C.TIERS.slice(1).find((t) => t.fee >= s.fee) || C.TIERS[5]).n}</i>` : poor ? `<i>More than the bank holds</i>` : ""}</span><span class="r"><b>${s.own ? "Yours, free" : money(s.fee)}</b></span></button>`; }).join("");
  } else if (p.kind === "sell") {
    const h = C.horse(S, p.hid) || S.young.find((x) => x.id === p.hid), v = h.stage ? C.youngValue(S, h) : C.valueOf(S, h);
    head = `<i>Sell</i><b>${esc(h.n)}</b><span>${h.stage ? "From the stud" : who(h)}</span>`;
    body = `<p class="lede" style="margin:6px 4px 12px">This can't be undone. ${h.stage ? "" : "Any entries are withdrawn and their fees returned."}</p>
      <div class="rows"><button class="btn bad" type="button" data-act="sell" data-h="${h.id}">Yes, sell for ${money(v)}</button><button class="btn line" type="button" data-act="unpick">Keep</button></div>`;
  } else if (p.kind === "new") {
    head = `<i>A new career</i><b>Start again?</b><span>This career is wiped: horses, money and reputation.</span>`;
    body = `<div class="rows" style="margin-top:8px"><button class="btn bad" type="button" data-act="newGame">Yes, start again</button><button class="btn line" type="button" data-act="unpick">Carry on</button></div>`;
  }
  $("picker").innerHTML = `<header class="pk-h"><div class="t">${head}</div><button class="x" type="button" data-act="unpick" aria-label="Close">×</button></header><div class="pk-b">${body}</div>`;
}

// ---------------------------------------------------------------- every tap
const BIDS = { cash: "You can't afford the next bid.", full: "No room for this one." };
const ACT = {
  open: (d) => open(d.sheet, d.tab), close, tab: (d) => { UI.tab[UI.sheet] = d.tab; if (d.tab === "season") UI.scrollTo = "#wk-" + S.week; render(); if (d.tab !== "season") $("shBody").scrollTop = 0; },
  dock: () => { UI.dockShut = !UI.dockShut; drawDock(); fitBoard(); },
  pan: (d) => { B.panTo(d.id); },
  openHorse: (d) => open("stables", null, { horse: +d.h }),
  calWeek: (d) => { UI.calWeek = Math.max(1, Math.min(C.NW, +d.w)); UI.meet = {}; if (d.tab) UI.tab.jockey = d.tab; render(); $("shBody").scrollTop = 0; },
  meet: (d) => { UI.meet[d.m] = !UI.meet[d.m]; render(); },
  big: (d) => { UI.big = d.k; render(); },
  goRace: (d) => { const r = C.RACES[+d.r]; UI.calWeek = r.m.week; UI.meet = { [r.m.i]: true }; UI.tab.jockey = "week"; UI.scrollTo = "#race-" + r.id; render(); },
  horse: (d) => { UI.horse = +d.h || null; UI.lot = null; UI.tile = "trip"; render(); $("shBody").scrollTop = 0; },
  lot: (d) => { UI.lot = +d.l; UI.tile = "trip"; render(); $("shBody").scrollTop = 0; },
  tile: (d) => { UI.tile = d.k; render(); },
  pickRace: (d) => { UI.picker = { kind: "race", rid: +d.r }; save(); drawPicker(); },
  pickHorse: (d) => { UI.picker = { kind: "horse", hid: +d.h }; save(); drawPicker(); },
  pickGallop: (d) => { UI.picker = { kind: "gallop", hid: +d.h }; drawPicker(); },
  pickSire: (d) => { UI.picker = { kind: "sire", mid: +d.m }; drawPicker(); },
  askSell: (d) => { UI.picker = { kind: "sell", hid: +d.h }; drawPicker(); },
  askNew: () => { UI.picker = { kind: "new" }; drawPicker(); },
  unpick: () => { UI.picker = null; drawPicker(); },
  enter: (d) => { const h = C.horse(S, +d.h), r = C.RACES[+d.r]; const err = act(() => C.enter(S, +d.h, +d.r)); UI.picker = null; drawPicker(); toast(err || `${h.n} is entered: ${r.name}, ${day(r.m.date)}`, !!err); },
  withdraw: (d) => { act(() => C.withdraw(S, +d.h, +d.w)); UI.picker = null; drawPicker(); toast("Withdrawn. The entry fee is back in the bank."); },
  picks: () => { const made = act(() => C.trainerPicks(S)); toast(made.length ? (made.length === 1 ? `The trainer has entered ${made[0].h.n} at ${made[0].r.m.course}.` : `The trainer has entered ${made.length} horses.`) : "The trainer sees nothing worth running for this week."); },
  gallop: (d) => { const h = C.horse(S, +d.h), out = C.gallop(S, +d.h, d.k); if (!out) { UI.picker = null; render(); return; } UI.picker = { kind: "msg", k: "From the gallops", title: h.n, say: out.text, rev: out.rev }; save(); render(); },
  bid: (d) => { const l = S.sale.lots.find((x) => x.id === +d.l), r = act(() => C.bid(S, +d.l)), name = l.m ? l.m.n : l.h.n;
    if (r === "won") { toast(`Sold! ${name} is yours.`); if (B.Sound.gavel) B.Sound.gavel(); } else if (r === "raised") toast(`${l.by} bids ${money(l.price)}.`); else if (BIDS[r]) toast(BIDS[r], true); },
  passLot: (d) => { const l = S.sale.lots.find((x) => x.id === +d.l); act(() => C.pass(S, +d.l)); toast(`Sold to ${l.by} for ${money(l.price)}.`); },
  sell: (d) => { UI.picker = null; UI.horse = null; const v = act(() => C.sell(S, +d.h)); toast(`Sold for ${money(v)}.`); },
  retire: (d) => { const h = C.horse(S, +d.h), ok = act(() => C.retire(S, +d.h)); if (!ok) { toast("That can't be done just now.", true); return; } UI.horse = null; toast(`${h.n} has gone to stud.`); open("stud"); },
  toYard: (d) => { const ok = act(() => C.moveToYard(S, +d.h)); UI.horse = null; render(); toast(ok ? "Into the yard." : "No box free.", !ok); },
  cover: (d) => { const err = act(() => C.cover(S, +d.m, d.s)); UI.picker = null; drawPicker(); toast(err || `Covered by ${d.s}. The foal is due next spring.`, !!err); },
  // the gold button: with runners it goes to race day (every race is settled and saved first); with none the week moves on
  advance: () => { if (S.rd) return open("raceday"); const rd = C.goRacing(S); save(); if (rd) { UI.rd = { stage: "card" }; open("raceday"); } else finishWeek(); },
  rdWatch: () => { UI.rd.stage = "run"; render(); $("shBody").scrollTop = 0; if (B.Sound.hooves) B.Sound.hooves(4); },
  rdResult: () => { UI.rd.stage = "result"; reveal(); },
  rdNext: () => { const rd = S.rd; if (rd.i < rd.res.length - 1) { rd.i++; UI.rd = { stage: "card" }; save(); render(); $("shBody").scrollTop = 0; } else finishWeek(); },
  rdAll: () => finishWeek(),
  sound: () => { B.Sound.set(!B.Sound.on); render(); },
  newGame: () => { S = C.newGame((Date.now() % 2147483647) | 0); Object.assign(UI, { sheet: null, horse: null, lot: null, picker: null, calWeek: S.week, meet: {}, report: null, rd: null, tab: {} }); save(); render(); toast("A new career. Good luck."); },
};
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-act]"); if (!el || el.disabled) { if (e.target.id === "pickerWrap") ACT.unpick(); else if (e.target.id === "sheetWrap") close(); return; }
  const f = ACT[el.dataset.act]; if (f) { e.preventDefault(); f(el.dataset, el); }
});
addEventListener("keydown", (e) => { if (e.key === "Escape") { if (UI.picker) ACT.unpick(); else if (UI.sheet) close(); } });

function render() { C.use(S); drawBar(); drawNav(); drawBoard(); drawDock(); drawSheet(); drawPicker(); fitBoard(); drawEdges(); }
if (S.rd) { UI.rd = { stage: "card" }; UI.sheet = "raceday"; }           // a reload in the middle of race day picks it up at the same race
render();
window.CAREER_UI = { get S() { return S; }, UI, open, close, render, ACT };
})();
