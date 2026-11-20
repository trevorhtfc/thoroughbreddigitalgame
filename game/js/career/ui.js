// =====================================================================================================================
// Thoroughbred, the career hub: the screens (prototype, 20 Nov 2026). The rules are js/career/core.js.
//
// How it is laid out:
//   - The Newmarket board is home. Each place on it is a part of the stable, and a tap goes straight to its screen.
//   - The same screens are on the five-way bar (Map, Calendar, Horses, Money, More), so nothing is ever more than a tap away.
//   - The card on the board ("this week") lists what needs doing, each line a shortcut, and holds the one gold button
//     that moves the week on.
//   - A screen is one of the game's sheets; a choice (which horse, which stallion) slides up over it.
// Everything is drawn from the state by render(); every tap is a data-act handled in ACT below.
// =====================================================================================================================
(() => {
"use strict";
const C = window.CAREER, B = window.BOARD, D = window.CAREER_DATA;
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v == null ? "" : v).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = C.money, T = () => C.TIERS[C.tierOf(S)];
const ico = (n) => `<svg viewBox="0 0 512 512" aria-hidden="true">${window.ICON[n] || ""}</svg>`;
const ARR = `<svg class="arr" viewBox="0 0 10 16" aria-hidden="true"><path d="M1.6 0 0 1.6 6.4 8 0 14.4 1.6 16l8-8z"/></svg>`;
const STAR = `<path d="M10 1.5l2.6 5.4 5.9.8-4.3 4.1 1 5.8L10 14.9 4.8 17.6l1-5.8L1.5 7.7l5.9-.8z"/>`;
const NAVI = { map: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3 3 5.5v15.5l6-2.5 6 2.5 6-2.5V3l-6 2.500L9 3zm0 2.200 6 2.500v11.100l-6-2.500V5.200zM5 6.900l2-.800v11.100l-2 .800V6.900zm14 10.200-2 .800V6.800l2-.800v11.100z"/></svg>`,
  more: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h7v6H4V5zm9 0h7v6h-7V5zM4 13h7v6H4v-6zm9 0h7v6h-7v-6z"/></svg>` };

// ---------------------------------------------------------------- the save (this browser only)
const KEY = "tb-career-hub-1";
function load() { try { const t = localStorage.getItem(KEY); if (t) { const s = JSON.parse(t); if (s && s.v === 1) return s; } } catch (e) {} return null; }
function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
let S = load() || C.newGame((Date.now() % 2147483647) | 0);
const UI = { sheet: null, tab: {}, horse: null, calWeek: S.week, meet: {}, picker: null, dockShut: false, big: "g1", report: null, notes: {}, key: "" };

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
  report: { title: "The Week's Racing", kicker: "", medal: ico("checkered-flag"), pic: [1110, 330, 520] },
};
const NAV = [["map", "Map", NAVI.map], ["jockey", "Calendar", ico("calendar")], ["stables", "Horses", ico("horse-head")], ["palace", "Money", ico("two-coins")], ["more", "More", NAVI.more]];

// ---------------------------------------------------------------- small pieces
const starsHtml = (h) => { const s = C.starsOf(h), a = Math.floor(s.sure + 0.25), b = Math.max(a, Math.ceil(s.maybe - 0.25));
  return `<span class="kstars" title="Potential: gold is sure, pale is possible">${[1, 2, 3, 4, 5].map((i) => `<svg viewBox="0 0 20 20" class="${i <= a ? "s1" : i <= b ? "s2" : "s0"}">${STAR}</svg>`).join("")}</span>`; };
const freshHtml = (h) => `<span class="fresh ${h.fresh < 50 ? "low" : h.fresh < 75 ? "mid" : ""}"><span class="barx"><span style="width:${h.fresh}%"></span></span>${h.out ? `Off ${h.out} wk` : h.fresh >= 90 ? "Fresh" : h.fresh >= 75 ? "Ready" : h.fresh >= 50 ? "A bit flat" : "Tired"}</span>`;
const formHtml = (h) => (h.form.length ? `<span class="form">${h.form.map((p) => (p === 1 ? "<em>1</em>" : p)).join("-")}</span>` : `<span class="form" style="color:#9d978a;font-weight:700">Unraced</span>`);
const who = (h) => `${h.age}yo ${C.sexWord(h)} · by ${esc(h.sire)}`;
const coat = (h) => `<span class="coat ${h.colour}"><span></span></span>`;
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
const tick = (label, v) => `<span class="tk ${v === "ok" ? "ok" : v === "no" ? "no" : "q"}"><i>${v === "ok" ? "✓" : v === "no" ? "✕" : "?"}</i>${label}</span>`;
const chipHtml = (v) => `<span class="ch k${v.key}">${v.chip}</span>`;
const day = (iso) => C.fmtDay(iso, S.season);
const weekName = (w) => C.weekInfo(w).label;
const entriesOpen = (w) => w >= S.week && w <= S.week + 3;
const trackOf = (m) => (m.course === "Newmarket" ? (m.date >= "2026-06-20" && m.date <= "2026-08-31" ? "Newmarket (July Course)" : "Newmarket (Rowley Mile)") : m.course);
function toast(text, bad) { const t = $("toast"); t.textContent = text; t.className = "tb-toast show" + (bad ? " error" : ""); clearTimeout(toast.t); toast.t = setTimeout(() => (t.className = "tb-toast"), 2600); }

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
function act(fn) { const before = S.bank, out = fn(); const d = S.bank - before; save(); render(); if (d) tumble(d); return out; }

// ---------------------------------------------------------------- the bar, the five ways in, the board
function drawBar() {
  const wk = C.weekInfo(S.week), cost = C.weeklyCost(S), t = C.tierOf(S), nx = C.TIERS[t + 1];
  const p = nx ? Math.round((S.rep - C.TIERS[t].rep) / (nx.rep - C.TIERS[t].rep) * 100) : 100;
  $("brandWhere").textContent = S.stable;
  $("stats").innerHTML = `<button class="cs" data-act="open" data-sheet="jockey" type="button" aria-label="The calendar"><b>${wk.label}</b><i>${C.fmtSpan(S.week, S.season)} ${C.yearOf(S.week, S.season)}</i></button>
    <button class="cs bank ${S.bank < 0 ? "kneg" : ""}" data-act="open" data-sheet="palace" data-tab="money" type="button" aria-label="Money"><b>${money(S.bank)}</b><i>${money(cost.perWeek)} a week</i></button>
    <button class="cs krep" data-act="open" data-sheet="palace" data-tab="rep" type="button" aria-label="Reputation"><span class="kring" style="--p:${p}"><span>${t}</span></span><span class="t"><b>${C.TIERS[t].n}</b><i>${nx ? `${S.rep} of ${nx.rep}` : `${S.rep} points`}</i></span></button>`;
}
function badges() {
  const td = C.todos(S), n = (k) => { const x = td.find((q) => q.k === k); return x ? x.n || 1 : 0; }, unread = S.news.filter((x) => !x.read).length;
  return { td, stables: n("enter"), warren: n("gallop"), tatts: n("sale") ? "Sale on" : 0, stud: n("cover") + n("box"), races: C.runners(S).length, money: n("bank") ? "!" : 0, unread };
}
function drawNav() {
  const b = badges(), dot = { stables: b.stables, palace: b.money, more: (b.warren ? 1 : 0) + (b.tatts ? 1 : 0) + (b.stud ? 1 : 0) + (b.unread ? 1 : 0) };
  const on = UI.sheet ? (NAV.some((n) => n[0] === UI.sheet) ? UI.sheet : "more") : "map";
  $("nav").innerHTML = NAV.map(([id, label, svg]) => `<button type="button" data-act="${id === "map" ? "close" : "open"}" data-sheet="${id}" class="${on === id ? "on" : ""}">${svg}<span>${label}</span>${dot[id] ? `<i class="dot">${dot[id]}</i>` : ""}</button>`).join("");
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
  const r = v.getBoundingClientRect(), tags = UI.tags || {}, L = [], R = [];
  for (const id of Object.keys(tags)) { if (!tags[id]) continue; const p = B.placeOf(id), x = p.at[0] * B.scale - v.scrollLeft, y = r.top + p.at[1] * B.scale;
    if (x < 30) L.push({ id, y, p }); else if (x > r.width - 30) R.push({ id, y, p }); }
  const side = (list, cls) => { list.sort((a, b) => a.y - b.y); let last = -99; return list.map((e) => { const y = Math.min(r.bottom - 34, Math.max(r.top + 8, e.y - 15, last + 36)); last = y;
    return `<button type="button" class="edge ${cls}" style="top:${y.toFixed(0)}px" data-act="pan" data-id="${e.id}">${cls === "l" ? "‹ " : ""}${esc(e.p.title)}${cls === "r" ? " ›" : ""}</button>`; }).join(""); };
  box.innerHTML = side(L, "l") + side(R, "r");
}
B.view.addEventListener("scroll", () => { UI.panX = (B.view.scrollLeft + B.view.clientWidth / 2) / B.scale; requestAnimationFrame(drawEdges); }, { passive: true });
addEventListener("resize", () => { dockH = -1; setTimeout(fitBoard, 60); });
// a tap on a place goes straight to its screen (the board's own preview card is not used here)
B.onChoose = (id) => { if (!id) return; B.choose(null); open(id); };
B.cardFor = (id) => ({ title: (PLACE[id] || {}).title || "" });

// ---------------------------------------------------------------- this week: the card on the board
const TDI = { enter: "horse-head", sale: "gavel", gallop: "stopwatch", cover: "horseshoe", box: "stable", bank: "two-coins" };
function goLabel() { const n = C.runners(S).length, nxt = S.week === C.NW ? "The new season" : C.isWinter(S.week + 1) || C.isWinter(S.week) ? "Next month" : "Next week";
  return n ? `Go racing <small>${n} runner${n > 1 ? "s" : ""}</small>` : nxt; }
function drawDock() {
  const wk = C.weekInfo(S.week), b = badges(), run = C.runners(S), rows = [];
  if (run.length) rows.push(`<li><button type="button" data-act="open" data-sheet="races"><span class="ic run">${ico("checkered-flag")}</span><span class="tx"><b>${run.length} runner${run.length > 1 ? "s" : ""} this week</b><span>${run.map((x) => esc(x.h.name) + " at " + x.r.m.course).join(" · ")}</span></span>${ARR}</button></li>`);
  for (const t of b.td) rows.push(`<li><button type="button" data-act="open" data-sheet="${t.go}"${t.go === "palace" ? ' data-tab="money"' : ""}><span class="ic">${ico(TDI[t.k])}</span><span class="tx"><b>${esc(t.text)}</b><span>${esc(t.sub)}</span></span>${ARR}</button></li>`);
  if (b.unread) rows.push(`<li><button type="button" data-act="open" data-sheet="news"><span class="ic quiet">${ico("scroll-unfurled")}</span><span class="tx"><b>${b.unread} new in the post</b><span>${esc(S.news.find((x) => !x.read).title)}</span></span>${ARR}</button></li>`);
  if (!rows.length) rows.push(`<li><button type="button" data-act="open" data-sheet="jockey"><span class="ic quiet">${ico("calendar")}</span><span class="tx"><b>Nothing needs doing</b><span>Look ahead in the calendar, or move on.</span></span>${ARR}</button></li>`);
  const idle = b.td.some((t) => t.k === "enter");
  // on a computer the card is a column beside the board, with room for the week's note and the string at a glance
  const str = S.horses.map((h) => { const rid = h.entries[S.week], r = rid != null ? C.RACES[rid] : null;
    return `<button type="button" data-act="openHorse" data-h="${h.id}">${coat(h)}<span class="tx"><b>${esc(h.name)}</b><span class="${r ? "go" : ""}">${h.out ? `Off for ${h.out} week${h.out > 1 ? "s" : ""}` : r ? `Runs ${day(r.m.date)} · ${esc(r.m.course)} · ${r.dist}` : h.fresh < 72 ? "Resting after a run" : "Ready · no race this week"}</span></span><span class="rtg">${h.or != null ? h.or : "–"}</span></button>`; }).join("");
  $("dock").className = "dock" + (UI.dockShut ? " shut" : "");
  $("dock").innerHTML = `<button class="dock-h" type="button" data-act="dock" aria-expanded="${!UI.dockShut}"><span class="t"><span class="k">${wk.label} · ${C.fmtSpan(S.week, S.season)} · ${wk.phase}</span><b>${esc(wk.title)}</b></span>
      <span class="count">${rows.length}</span><span class="chev">${ARR}</span></button>
    ${wk.note ? `<p class="dock-note">${esc(wk.note)}</p>` : ""}
    <ul class="todo">${rows.slice(0, 5).join("")}</ul>
    <div class="dock-str"><div class="k">Your string · ${S.horses.length} of ${T().boxes} boxes</div>${str || `<p class="dock-note">No horses in training.</p>`}</div>
    <div class="dock-go">${idle ? `<button class="ghostb" type="button" data-act="picks">Trainer's<br>picks</button>` : ""}<button class="gold" type="button" data-act="advance">${goLabel()}${ARR}</button></div>`;
}

// ---------------------------------------------------------------- sheets
function open(id, tab, extra) {
  if (id === "map") return close();
  if (!PLACE[id]) id = "more";
  UI.sheet = id; UI.horse = null; UI.picker = null; if (tab) UI.tab[id] = tab;
  if (id === "jockey" && !extra) UI.calWeek = S.week;
  if (id === "tatts") S.saleSeen = true;
  if (id === "news") setTimeout(() => { S.news.forEach((n) => (n.read = true)); save(); drawNav(); }, 1200);
  Object.assign(UI, extra || {}); render(); $("shBody").scrollTop = 0;
}
function close() { UI.sheet = null; UI.horse = null; UI.picker = null; render(); }
function drawSheet() {
  const id = UI.sheet, wrap = $("sheetWrap");
  document.body.classList.toggle("sheet-open", !!id); B.covered = !!id; B.setInPlace(id && B.placeOf(id) ? id : null);
  if (!id) { wrap.hidden = true; return; }
  const P = PLACE[id], tab = UI.tab[id] || (P.tabs && P.tabs[0][0]);
  wrap.hidden = false;
  $("shKicker").textContent = id === "report" && UI.report ? `${weekName(UI.report.week)} · ${C.fmtSpan(UI.report.week, UI.report.season)}` : P.kicker; $("shTitle").textContent = P.title; $("shMedal").innerHTML = P.medal;
  const pl = B.placeOf(id); B.paintPic($("shPic"), P.pic || (pl && pl.pic) || WHOLE, 0.72);
  $("shCloseT").textContent = id === "report" ? "Close" : "Back to the map";
  const tabs = $("shTabs"); tabs.hidden = !P.tabs || !!UI.horse;
  if (P.tabs) tabs.innerHTML = P.tabs.map(([k, l]) => `<button type="button" data-act="tab" data-tab="${k}" class="${k === tab ? "on" : ""}">${l}</button>`).join("");
  const key = id + "/" + tab + "/" + (UI.horse || "") + "/" + UI.calWeek, body = $("shBody"), keep = key === UI.key ? body.scrollTop : 0; UI.key = key;
  const foot = $("shFoot"); foot.hidden = true; foot.innerHTML = "";
  $("main").innerHTML = SCREEN[id](tab);
  body.scrollTop = keep;
  for (const el of $("main").querySelectorAll("[data-pic]")) { const q = B.placeOf(el.dataset.pic); B.paintPic(el, (q && q.pic) || WHOLE, 0.5); }
  if (UI.scrollTo) { const el = $("main").querySelector(UI.scrollTo); if (el) el.scrollIntoView({ block: "center" }); UI.scrollTo = null; }
}
function footer(html) { const f = $("shFoot"); f.hidden = false; f.innerHTML = html; }
const SCREEN = {};

// ---------------------------------------------------------------- the calendar (the Jockey Club)
function raceRow(r, m) {
  const mine = S.horses.find((h) => h.entries[m.week] === r.id), past = m.week < S.week;
  let a = "";
  if (mine) a = `<span class="kmine"><span>✓ ${esc(mine.name)}</span>${past ? "" : `<button type="button" data-act="withdraw" data-h="${mine.id}" data-w="${m.week}" aria-label="Withdraw ${esc(mine.name)}">×</button>`}</span>`;
  else if (!past && entriesOpen(m.week) && S.horses.some((h) => !C.barred(S, h, r))) a = `<button class="btn sm" type="button" data-act="pickRace" data-r="${r.id}">Enter</button>`;
  return `<div class="krace ${r.big && r.type !== "Handicap" ? "big" : ""}" id="race-${r.id}"><span class="tm">${r.time}</span><div class="krt"><b>${esc(r.name)}</b><div class="ln">${typeChip(r)}<span>${cond(r)}</span></div></div><span class="pz">${money(r.prize)}</span><span class="act">${a}</span></div>`;
}
function meetRow(m) {
  const openIt = !!UI.meet[m.i], can = m.week >= S.week ? S.horses.filter((h) => m.races.some((r) => !C.barred(S, h, r))).length : 0, inn = S.horses.filter((h) => h.entries[m.week] != null && C.RACES[h.entries[m.week]].m === m).length;
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
  return `<div class="wkbar"><button class="nv" type="button" data-act="calWeek" data-w="${w - 1}" ${w <= 1 ? "disabled" : ""} aria-label="The week before"><svg viewBox="0 0 10 16"><path d="M8.4 0 10 1.6 3.6 8 10 14.4 8.4 16l-8-8z"/></svg></button>
      <div class="w"><i>${wk.label} · ${C.fmtSpan(w, S.season)} · ${rel}</i><b>${esc(wk.title)}</b></div>
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
    html += `<button class="wk ${wk.w < S.week ? "past" : wk.w === S.week ? "now" : ""}" type="button" data-act="calWeek" data-w="${wk.w}" data-tab="week" id="wk-${wk.w}"><span class="n"><b>${wk.label}</b><i>${C.fmtSpan(wk.w, S.season)}</i></span>
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
    ${list.map((r) => { const w = r.m.week, d = w - S.week; return `<button class="bigr ${d < 0 ? "past" : ""}" type="button" data-act="goRace" data-r="${r.id}"><span class="d">${day(r.m.date)}<br>${d < 0 ? "Run" : d === 0 ? "This week" : `In ${d} wk`}</span>
      <span class="t"><b>${esc(r.name)}</b><i>${esc(r.m.course)} · ${r.dist} · ${r.ages}${SEXT[r.sex]}</i></span><span class="pz">${money(r.prize)}</span></button>`; }).join("")}`;
}

// ---------------------------------------------------------------- your horses (the stables)
function planLine(h) {
  const rid = h.entries[S.week];
  if (h.out) return `<div class="plan"><div class="p"><b>On the easy list</b>Back in ${h.out} week${h.out > 1 ? "s" : ""}.</div></div>`;
  if (rid != null) { const r = C.RACES[rid], v = C.view(S, h, r);
    return `<div class="plan run"><div class="p"><b>Runs ${day(r.m.date)} at ${esc(r.m.course)}</b>${esc(r.name)} · ${r.dist} · ${money(r.prize)}</div>${chipHtml(v)}<button class="x" type="button" data-act="withdraw" data-h="${h.id}" data-w="${S.week}" aria-label="Withdraw">×</button></div>`; }
  const later = Object.keys(h.entries).map(Number).filter((w) => w > S.week).sort((a, b) => a - b)[0];
  const lt = later ? `Entered ${day(C.RACES[h.entries[later]].m.date)}: ${esc(C.RACES[h.entries[later]].name)}, ${esc(C.RACES[h.entries[later]].m.course)}` : h.fresh < 72 ? "Needs a little longer after the last run." : "Fresh and ready.";
  return `<div class="plan"><div class="p"><b>No race this week</b>${lt}</div><button class="btn sm" type="button" data-act="pickHorse" data-h="${h.id}">Find a race</button></div>`;
}
function horseCard(h, big) {
  return `<div class="hcard" id="h-${h.id}"><button class="top" type="button" data-act="horse" data-h="${h.id}">${coat(h)}<span class="id"><b>${esc(h.name)}</b><i>${who(h)}</i></span>
      <span class="mark"><b>${h.or != null ? h.or : "–"}</b><i>${h.or != null ? "Rating" : "No rating"}</i></span></button>
    <div class="kfacts">${starsHtml(h)}${freshHtml(h)}${formHtml(h)}</div>${planLine(h)}</div>`;
}
SCREEN.stables = () => {
  if (UI.horse) { const h = C.horse(S, UI.horse); if (h) return horseView(h); UI.horse = null; }
  const free = C.boxesFree(S), idle = C.todos(S).some((t) => t.k === "enter");
  return `<div class="sec"><h2>In training</h2><span>${S.horses.length} of ${T().boxes} boxes${free ? ` · ${free} free` : " · full"}</span>${idle ? `<button class="btn sm line r" type="button" data-act="picks">Trainer's picks</button>` : ""}</div>
    ${S.horses.length ? `<div class="rows">${S.horses.map((h) => horseCard(h)).join("")}</div>` : `<div class="empty">The yard is empty. Tattersalls is the place to start.</div>`}
    <p class="knote"><b>Stars</b> are the trainer's view of how good a horse could be: gold is sure, pale is possible. <b>Rating</b> is the handicapper's mark, earned after two runs or a win. Gallops and races sharpen both.</p>
    <div class="sec"><h2>More</h2></div>
    <div class="rows"><button class="btn line" type="button" data-act="open" data-sheet="warren">The gallops · ${T().gal - S.gallops} left this week</button><button class="btn line" type="button" data-act="open" data-sheet="tatts">Buy or sell at Tattersalls</button></div>`;
};
function horseView(h) {
  const e = C.starsOf(h), lo = Math.round((h.est.c - h.est.w) / 5) * 5, hi = Math.round((h.est.c + h.est.w) / 5) * 5;
  const kt = Object.entries(h.known.trip), ok = kt.filter(([, v]) => v === 0).map(([i]) => C.TRIPN[i]), no = kt.filter(([, v]) => v !== 0).map(([i, v]) => C.TRIPN[i] + (v < 0 ? " is too sharp" : " is too far"));
  const kg = Object.entries(h.known.ground), likes = kg.filter(([, v]) => v > 0).map(([i]) => C.GOINGS[i]), fine = kg.filter(([, v]) => v === 0).map(([i]) => C.GOINGS[i]), hates = kg.filter(([, v]) => v < 0).map(([i]) => C.GOINGS[i]);
  const opts = optGroups(h, [4, 2, 2]), val = C.valueOf(S, h);
  const tile = (k, b, s, unk) => `<div class="ktile ${unk ? "unk" : ""}"><i>${k}</i><b>${b}</b>${s ? `<span>${s}</span>` : ""}</div>`;
  return `<button class="back" type="button" data-act="horse" data-h=""><svg viewBox="0 0 10 16"><path d="M8.4 0 10 1.6 3.6 8 10 14.4 8.4 16l-8-8z"/></svg>All your horses</button>
    ${horseCard(h)}
    <div class="tiles">
      ${tile("Potential", starsHtml(h), h.est.w <= 4 ? `About ${h.est.c}: the trainer is sure` : `Somewhere from ${lo} to ${hi}`)}
      ${tile("Best trip", ok.length ? ok.join(", ") + " suits" : "Not known yet", no.join(" · ") || (ok.length ? "" : "A gallop or a run will tell"), !ok.length)}
      ${tile("Ground", likes.length ? "Loves " + likes.join(", ").toLowerCase() : fine.length ? "Handles " + fine.join(", ").toLowerCase() : "Not known yet", hates.length ? "Not on " + hates.join(", ").toLowerCase() : "", !kg.length)}
      ${tile("Type", h.known.mat ? { early: "Early type", normal: "Normal", late: "Late developer" }[h.mat] : "Not known yet", h.known.mat ? { early: "At the best young", normal: "Peaks at three and four", late: "Better with time" }[h.mat] : "", !h.known.mat)}
      ${tile("Record", `${h.runs} run${h.runs === 1 ? "" : "s"}, ${h.wins} win${h.wins === 1 ? "" : "s"}`, `${h.places} placed · ${h.style}`)}
      ${tile("Money", `<span class="${h.earned - h.cost - h.kept >= 0 ? "kpos" : "kneg"}">${money(h.earned - h.cost - h.kept)}</span>`, `Won ${money(h.earned)} · cost ${money(h.cost + h.kept)}`)}
    </div>
    <div class="sec"><h2>Races to suit</h2><span>this week and the next two</span></div>
    ${opts || `<div class="empty">Nothing suitable in the next three weeks. Look further ahead in the calendar.</div>`}
    <div class="sec"><h2>Runs</h2></div>
    ${h.seen.length ? `<table class="kv">${h.seen.slice(0, 8).map((x) => `<tr><td><b>${x.pos === 1 ? "Won" : x.pos + ordinal(x.pos) + " of " + x.n}</b> · ${esc(x.race)}<i>${esc(x.course)} · ${x.dist} · ${x.going} · ran to ${x.fig}</i></td><td>${x.prize ? money(x.prize) : "–"}</td></tr>`).join("")}</table>` : `<div class="empty">${h.runs ? "Earlier runs were before your time with the horse." : "Yet to run."}</div>`}
    <div class="sec"><h2>Decisions</h2></div>
    <div class="rows"><button class="btn bad" type="button" data-act="askSell" data-h="${h.id}">Sell ${esc(h.name)} · about ${money(Math.round(val * 0.8 / 500) * 500)}</button>
    ${h.sex === "f" && h.age >= 3 ? `<button class="btn line" type="button" data-act="retire" data-h="${h.id}" ${C.paddocksFree(S) > 0 ? "" : "disabled"}>Retire her to your stud${C.paddocksFree(S) > 0 ? "" : " (no paddock free)"}</button>` : ""}</div>`;
}
// a horse's options, week by week: the best few of each
function optGroups(h, per) {
  const all = C.options(S, h, 2), out = [];
  for (let w = S.week; w <= S.week + 2 && w <= C.NW; w++) { const list = all.filter((o) => o.r.m.week === w); if (!list.length) continue;
    out.push(`<div class="kday">${w === S.week ? "This week" : w === S.week + 1 ? "Next week" : "In two weeks"} · ${esc(C.weekInfo(w).title)}</div><div class="rows">${list.slice(0, per[w - S.week]).map((o) => optRow(h, o, h.entries[w] === o.r.id)).join("")}</div>`); }
  return out.join("");
}
const ordinal = (n) => (n % 10 === 1 && n !== 11 ? "st" : n % 10 === 2 && n !== 12 ? "nd" : n % 10 === 3 && n !== 13 ? "rd" : "th");
function optRow(h, o, cur) {
  const r = o.r, v = o.v;
  return `<button class="kopt ${cur ? "cur" : ""}" type="button" data-act="enter" data-h="${h.id}" data-r="${r.id}"><span class="t"><b>${esc(r.name)}</b><i>${esc(r.m.course)} · ${day(r.m.date)} · ${r.dist} · ${money(r.prize)}</i>
    <span class="ln">${typeChip(r)}${tick("Trip", v.trip)}${tick(v.going ? v.going : "Ground", v.ground)}</span>${v.claim ? `<i style="color:var(--c-bad)">Every runner is for sale at ${money(v.claim)}</i>` : ""}${v.pen ? `<i>Carries a ${v.pen} lb winner's penalty</i>` : ""}${v.low ? `<i>Out of the handicap: rated below the bottom weight</i>` : ""}</span>
    <span class="r">${chipHtml(v)}<small>${cur ? "Entered ✓" : "Fee " + money(v.fee)}</small></span></button>`;
}

// ---------------------------------------------------------------- the gallops (Warren Hill)
SCREEN.warren = () => {
  const left = T().gal - S.gallops;
  return `<p class="lede"><b>${left} of ${T().gal} gallops left this week.</b> Work a horse to learn more about it: how good it could be, its trip, its ground. Or give a tired one an easy week.</p>
    <div class="rows">${S.horses.map((h) => { const n = UI.notes[h.id];
      return `<div class="hcard"><div class="top" style="cursor:default">${coat(h)}<span class="id"><b>${esc(h.name)}</b><i>${who(h)}</i></span><span class="mark"><b>${h.or != null ? h.or : "–"}</b><i>${h.or != null ? "Rating" : "No rating"}</i></span></div>
        <div class="kfacts">${starsHtml(h)}${freshHtml(h)}<span class="tk">${h.est.w <= 4 ? "Trainer is sure of this one" : h.est.w <= 9 ? "Trainer has a fair idea" : "Still a mystery"}</span></div>
        ${n ? `<div class="plan run"><div class="p"><b>${esc(n.say)}</b>${n.learned.map(esc).join(" · ")}</div></div>` : ""}
        <div class="plan"><div class="p">${h.galloped ? "Has been out this week." : h.out ? "On the easy list." : left ? "" : "No gallops left this week."}</div>
          <button class="btn sm" type="button" data-act="gallop" data-h="${h.id}" data-k="work" ${h.galloped || h.out || !left ? "disabled" : ""}>Work</button>
          <button class="btn sm line" type="button" data-act="gallop" data-h="${h.id}" data-k="easy" ${h.galloped || h.out || !left || h.fresh >= 100 ? "disabled" : ""}>Easy week</button></div></div>`; }).join("")}</div>
    <p class="knote">More gallops a week come with reputation: ${C.TIERS.slice(1).map((t) => `${t.n} ${t.gal}`).join(", ")}.</p>`;
};

// ---------------------------------------------------------------- the sales (Tattersalls)
function lotRow(l) {
  const racing = l.kind === "breeze" || l.kind === "hit";
  let title, sub, why = "";
  if (l.kind === "mare") { title = `${esc(l.mare.name)}, ${l.mare.age}yo broodmare`; sub = esc(l.note); if (C.paddocksFree(S) <= 0) why = "No paddock free"; }
  else { const h = l.h; title = l.kind === "hit" ? `${esc(h.name)}, ${h.age}yo ${C.sexWord(h)}` : `${l.kind === "foal" ? "Foal" : l.kind === "yearling" ? "Yearling" : "Two-year-old"} ${C.sexWord(h)} by ${esc(h.sire)}`;
    sub = `${starsHtml(h)}<br>${esc(l.note)}`; if (racing && C.boxesFree(S) <= 0) why = "No box free in the yard"; }
  if (!why && l.price > S.bank) why = "More than the bank holds";
  return `<div class="klot ${l.sold ? "sold" : ""}"><span class="n">Lot<b>${l.id}</b></span><span class="t"><b>${title}</b><i>${sub}</i></span>
    <span class="buy"><b>${money(l.price)}</b>${l.sold ? `<span class="chip l">Yours</span>` : why ? `<span class="why">${why}</span>` : `<button class="btn sm" type="button" data-act="buy" data-l="${l.id}">Buy</button>`}</span></div>`;
}
SCREEN.tatts = () => {
  const ahead = Object.keys(C.SALES).map(Number).sort((a, b) => a - b);
  const list = ahead.map((w) => { const d = w - S.week; return `<tr><td><b>${esc(C.SALES[w].name)}</b><i>${weekName(w)} · ${C.fmtSpan(w, S.season)} · ${esc(C.SALES[w].blurb)}</i></td><td>${d === 0 ? "On now" : d < 0 ? "Next year" : d === 1 ? "Next week" : `In ${d} weeks`}</td></tr>`; }).join("");
  const sell = S.horses.map((h) => `<tr><td><b>${esc(h.name)}</b><i>${who(h)}${h.or != null ? " · rated " + h.or : ""}</i></td><td><button class="btn sm bad" type="button" data-act="askSell" data-h="${h.id}">Sell · ${money(Math.round(C.valueOf(S, h) * (S.sale ? 1 : 0.8) / 500) * 500)}</button></td></tr>`).join("");
  return `${S.sale ? `<div class="sec"><h2>On this week</h2></div><div class="banner"><i>${weekName(S.week)} · ${S.sale.lots.filter((l) => !l.sold).length} lots</i><b>${esc(S.sale.name)}</b><span>${esc(S.sale.blurb)}</span></div>
      <p class="lede">${money(S.bank)} in the bank · ${C.boxesFree(S)} box${C.boxesFree(S) === 1 ? "" : "es"} free in the yard · ${C.paddocksFree(S)} paddock${C.paddocksFree(S) === 1 ? "" : "s"} free at the stud.</p>
      <div class="rows">${S.sale.lots.map(lotRow).join("")}</div>
      <p class="knote">In the full game this is the live auction, with rival bidders. Here each lot has a price: buy it or leave it.</p>`
    : `<div class="empty"><b>No sale at Tattersalls this week.</b><br>The sales come round through the year: the breeze-ups in spring, the yearlings in October, the mares in December.</div>`}
    <div class="sec"><h2>The sales this year</h2></div><div class="panel"><table class="kv">${list}</table></div>
    <div class="sec"><h2>Sell a horse</h2><span>${S.sale ? "full price in a sale week" : "a private sale, a fifth under its value"}</span></div>
    <div class="panel">${sell ? `<table class="kv">${sell}</table>` : `<div class="empty">No horses in training.</div>`}</div>`;
};

// ---------------------------------------------------------------- the stud (National Stud)
SCREEN.stud = () => {
  const open = C.coveringOpen(S), yr = C.yearOf(S.week, S.season) + (S.week >= 36 ? 0 : 0);
  const mare = (m) => `<div class="hcard"><div class="top" style="cursor:default"><span class="coat bay"><span></span></span><span class="id"><b>${esc(m.name)}</b><i>${m.age}yo broodmare${m.own ? " · raced for you" : ""}</i></span>
      <span class="mark"><b>${m.stars}★</b><i>Quality</i></span></div>
    <div class="plan ${m.inFoal ? "run" : ""}"><div class="p">${m.inFoal ? `<b>In foal to ${esc(m.inFoal.sire)}</b>${m.inFoal.season <= S.season ? "Due this spring." : "Due next spring. The foal races two years after that."}` : `<b>Not in foal</b>${open ? "The covering season is open until the end of May." : "The covering season opens in February."}`}</div>
      ${!m.inFoal && open ? `<button class="btn sm" type="button" data-act="pickSire" data-m="${m.id}">Choose a stallion</button>` : ""}</div></div>`;
  const young = (h) => `<div class="hcard"><div class="top" style="cursor:default">${coat(h)}<span class="id"><b>${esc(h.name)}</b><i>${h.stage === "foal" ? "Foal" : h.stage === "yearling" ? "Yearling" : "Two-year-old"} ${C.sexWord(h)} · by ${esc(h.sire)}${h.dam ? " out of " + esc(h.dam) : ""}</i></span></div>
    <div class="kfacts">${starsHtml(h)}<span class="tk">${h.stage === "foal" ? "Races in two years" : h.stage === "yearling" ? "Comes into training in January" : "Ready for the yard"}</span></div>
    <div class="plan"><div class="p"></div>${h.stage === "ready" ? `<button class="btn sm" type="button" data-act="toYard" data-h="${h.id}" ${C.boxesFree(S) > 0 ? "" : "disabled"}>${C.boxesFree(S) > 0 ? "Move into the yard" : "No box free"}</button>` : ""}
      <button class="btn sm bad" type="button" data-act="askSell" data-h="${h.id}">Sell</button></div></div>`;
  return `<div class="pipe"><div><b>${S.mares.length}</b><i>Mares · ${T().pad} paddocks</i></div><div><b>${S.young.filter((h) => h.stage === "foal").length}</b><i>Foals</i></div><div><b>${S.young.filter((h) => h.stage !== "foal").length}</b><i>Yearlings</i></div></div>
    <p class="lede">Breeding is the cheap way to a star, and the slow one: cover a mare this spring, the foal arrives next spring, and it races as a two-year-old the year after.</p>
    <div class="sec"><h2>Your mares</h2></div><div class="rows">${S.mares.map(mare).join("") || `<div class="empty">No mares. The December Sale is the place to buy one.</div>`}</div>
    <div class="sec"><h2>Foals and yearlings</h2></div><div class="rows">${S.young.map(young).join("") || `<div class="empty">No young stock yet.</div>`}</div>`;
};

// ---------------------------------------------------------------- the owner's office (Palace House): money, reputation, goals
SCREEN.palace = (tab) => (tab === "rep" ? repView() : tab === "goals" ? goalsView() : moneyView());
function moneyView() {
  const c = C.weeklyCost(S), sum = (o) => Object.values(o).reduce((a, b) => a + b, 0), tin = sum(S.year.in), tout = sum(S.year.out), max = Math.max(1, ...Object.values(S.year.in), ...Object.values(S.year.out));
  const runway = c.perWeek ? Math.floor(Math.max(0, S.bank) / c.perWeek) : 99;
  const bars = (o, cls) => Object.entries(o).sort((a, b) => b[1] - a[1]).map(([k, v]) => `<div class="barrow ${cls}"><div class="l"><span>${k}</span><b>${money(v)}</b></div><div class="b"><span style="width:${Math.max(2, v / max * 100)}%"></span></div></div>`).join("") || `<div class="empty">Nothing yet.</div>`;
  const per = S.horses.map((h) => `<tr><td><b>${esc(h.name)}</b><i>Won ${money(h.earned)} · bought for ${money(h.cost)} · keep ${money(h.kept)}</i></td><td class="${h.earned - h.cost - h.kept >= 0 ? "kpos" : "kneg"}">${money(h.earned - h.cost - h.kept)}</td></tr>`).join("");
  const led = S.ledger.slice(-25).reverse().map((l) => `<tr><td>${esc(l.text)}<i>${l.cat} · ${weekName(l.w)}${l.s !== S.season ? ", last season" : ""}</i></td><td class="${l.amt >= 0 ? "kpos" : "kneg"}">${l.amt > 0 ? "+" : ""}${money(l.amt)}</td></tr>`).join("");
  return `<div class="bankbox"><div class="big ${S.bank < 0 ? "kneg" : ""}"><i>In the bank</i><b>${money(S.bank)}</b></div>
      <div class="side">The yard costs <b>${money(c.perWeek)} a week</b>.<br>${S.bank < 0 ? "<b>Overdrawn:</b> sell a horse or win a race before you buy again." : runway > 60 ? "The bank would last more than a year with no winnings." : `With no winnings the bank lasts about <b>${runway} weeks</b>.`}<br>
      ${S.bank !== S.year.start ? `This season: <b>${S.bank - S.year.start >= 0 ? "up" : "down"} ${money(Math.abs(S.bank - S.year.start))}</b>.` : ""}</div></div>
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
  const rung = (i) => { const x = C.TIERS[i]; return `<div class="rung ${i < t ? "done" : i === t ? "here" : "locked"}"><span class="no">${i < t ? "✓" : i}</span><span class="t"><b>${x.n}</b><i>${x.boxes} boxes · ${x.pad} paddocks · ${x.gal} gallops a week · stallions ${x.fee > 1e6 ? "of any fee" : "up to " + money(x.fee)}</i>
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
  return `<div class="sec"><h2>This season's goals</h2></div><div class="panel">${goals}</div>
    <div class="sec"><h2>The trophy cabinet</h2><span>Group, Listed and heritage wins</span></div>
    <div class="panel">${tr ? `<table class="kv">${tr}</table>` : `<div class="empty">Empty for now. Your first big-race winner goes here.</div>`}</div>
    <div class="sec"><h2>The career so far</h2></div>
    <div class="panel"><table class="kv"><tr><td>Season</td><td>${S.season}</td></tr><tr><td>Runs</td><td>${S.stats.runs}</td></tr><tr><td>Winners</td><td>${S.stats.wins}</td></tr>
      <tr><td>Best run<i>${S.stats.best ? esc(S.stats.best.name) + " · " + esc(S.stats.best.race) : "No runners yet"}</i></td><td>${S.stats.best ? S.stats.best.fig : "–"}</td></tr></table></div>`;
}

// ---------------------------------------------------------------- to the races: this week's runners
SCREEN.races = () => {
  const run = C.runners(S);
  footer(`<span class="f-info">${run.length ? "The week's races are run and the week moves on." : "No runners: the week simply moves on."}</span><button class="gold" type="button" data-act="advance">${goLabel()}${ARR}</button>`);
  if (!run.length) return `<div class="empty"><b>No runners this week.</b><br>Enter a horse from its card or from the calendar, or let the trainer choose.</div>
    <div class="rows"><button class="btn" type="button" data-act="picks">Trainer's picks</button><button class="btn line" type="button" data-act="open" data-sheet="jockey">Open the calendar</button></div>`;
  return `<p class="lede">Your runners for <b>${esc(C.weekInfo(S.week).title)}</b>. The going is known for this week's meetings.</p>
    <div class="rows">${run.map(({ h, r }) => { const v = C.view(S, h, r); return `<div class="hcard"><div class="top" style="cursor:default">${coat(h)}<span class="id"><b>${esc(h.name)}</b><i>${day(r.m.date)} · ${r.time} · ${esc(trackOf(r.m))}</i></span>${chipHtml(v)}</div>
      <div class="kfacts">${typeChip(r)}<span class="tk">${esc(r.name)} · ${r.dist} · ${money(r.prize)}</span></div>
      <div class="plan"><div class="p" style="display:flex;flex-wrap:wrap;gap:4px 12px">${tick("Trip", v.trip)}${tick(v.going || "Ground", v.ground)}${freshHtml(h)}</div><button class="x" type="button" data-act="withdraw" data-h="${h.id}" data-w="${S.week}" aria-label="Withdraw">×</button></div></div>`; }).join("")}</div>
    <p class="knote">In the full game this is where race day begins: the racecard, then each race in 3D on its own course. This prototype settles the week's races at once.</p>`;
};

// ---------------------------------------------------------------- the week's report
SCREEN.report = () => {
  const R = UI.report; if (!R) return "";
  const nextW = C.weekInfo(S.week);
  footer(`<span class="f-info">Next: <b>${nextW.label}, ${esc(nextW.title)}</b></span><button class="gold" type="button" data-act="close">On to ${nextW.label}${ARR}</button>`);
  const prize = R.results.reduce((a, r) => a + r.prize, 0), keep = R.costs.perWeek * R.costs.weeks, claimed = R.results.reduce((a, r) => a + (r.claimed || 0), 0);
  const res = R.results.map((r) => { const race = C.RACES[r.rid];
    return `<div class="kres p${r.pos}"><div class="top"><span class="posn"><b>${r.pos}</b><i>of ${r.n}</i></span><span class="t"><b>${esc(r.name)}</b><i>${esc(race.name)} · ${esc(race.m.course)} · ${race.dist} · ${r.going}</i>
        <i>${r.pos === 1 ? `Won by ${lengths(r.gap)}` : `Beaten ${lengths(r.gap)}${r.winner ? ` by ${esc(r.winner.horse)} (${esc(r.winner.owner)})` : ""}`}</i></span><span class="won">${r.prize ? "+" + money(r.prize) : ""}</span></div>
      <div class="say"><q>${esc(r.say)}</q><div class="lrn">${r.learned.map((x) => `<span>${esc(x)}</span>`).join("")}${r.orBefore != null && r.orAfter !== r.orBefore ? `<span>Rating ${r.orBefore} → ${r.orAfter}</span>` : ""}${r.rep ? `<span>+${r.rep} reputation</span>` : ""}</div></div></div>`; }).join("");
  const rv = R.review;
  return `${R.tierUp ? `<div class="banner"><i>Reputation</i><b>You are now a ${C.TIERS[R.tierUp].n}</b><span>${C.TIERS[R.tierUp].boxes} boxes · ${C.TIERS[R.tierUp].pad} paddocks · ${C.TIERS[R.tierUp].gal} gallops a week · better stallions and sale lots</span></div>` : ""}
    ${rv ? `<div class="banner"><i>Season ${rv.season} is over</i><b>${rv.wins} winner${rv.wins === 1 ? "" : "s"} from ${rv.runs} runs</b><span>${money(rv.prize)} in prize money · in ${money(rv.in)}, out ${money(rv.out)} · ${rv.goals.filter((g) => g.done).length} of ${rv.goals.length} goals met</span></div>` : ""}
    <div class="sec"><h2>Your runners</h2></div>
    ${res ? `<div class="rows">${res}</div>` : `<div class="empty">No runners ${C.isWinter(R.week) ? "this month" : "this week"}.</div>`}
    ${R.events.length ? `<div class="sec"><h2>From the yard and the stud</h2></div><div class="panel"><table class="kv">${R.events.map((e) => `<tr><td>${esc(e.text)}</td><td></td></tr>`).join("")}</table></div>` : ""}
    <div class="sec"><h2>The money</h2></div>
    <div class="panel"><table class="kv"><tr><td>Prize money</td><td class="kpos">${prize ? "+" + money(prize) : "–"}</td></tr>${claimed ? `<tr><td>Horses sold out of their races</td><td class="kpos">+${money(claimed)}</td></tr>` : ""}
      <tr><td>The yard's keep${R.costs.weeks > 1 ? `<i>${R.costs.weeks} weeks</i>` : ""}</td><td class="kneg">${money(-keep)}</td></tr><tr class="tot"><td>In the bank</td><td>${money(R.bankAfter)}</td></tr></table></div>
    ${R.results.length ? `<p class="knote">In the full game each of these is a race day watched in 3D. This prototype settles them at once.</p>` : ""}`;
};
const lengths = (x) => (x < 0.15 ? "a nose" : x < 0.3 ? "a short head" : x < 0.45 ? "a head" : x < 0.7 ? "a neck" : x >= 20 ? "a distance" : (() => { const q = Math.round(x * 2) / 2, w = Math.floor(q); return (w ? w : "") + (q - w ? "½" : "") + (q > 1 ? " lengths" : " length"); })());

// ---------------------------------------------------------------- everything in one place, and the post
SCREEN.more = () => {
  const b = badges(), tile = (id, title, sub, dot) => `<button class="gb" type="button" data-act="open" data-sheet="${id}" data-pic="${id}"><b>${title}</b><i>${sub}</i>${dot ? `<span class="dot">${dot}</span>` : ""}</button>`;
  return `<div class="kgrid">
      ${tile("stables", "Your Horses", `${S.horses.length} in training`, b.stables)}
      ${tile("jockey", "The Calendar", esc(C.weekInfo(S.week).title))}
      ${tile("warren", "The Gallops", `${T().gal - S.gallops} left this week`, b.warren)}
      ${tile("tatts", "The Sales", S.sale ? "A sale is on" : "Tattersalls", b.tatts ? "!" : 0)}
      ${tile("stud", "The Stud", `${S.mares.length} mares · ${S.young.length} young`, b.stud)}
      ${tile("palace", "Money and Reputation", `${money(S.bank)} · ${T().n}`, b.money)}
      ${tile("races", "To the Races", `${b.races} runner${b.races === 1 ? "" : "s"} this week`, b.races)}
      ${tile("news", "The Post", `${b.unread} unread`, b.unread)}
    </div>
    <div class="sec"><h2>About this prototype</h2></div>
    <div class="panel"><p style="margin:0 0 8px;font-size:14px;line-height:1.5">This is the full game's home and menus: the map, the calendar, the horses, the money and the ladder. The races themselves are left out, so a week's runners are settled at once.</p>
      <p style="margin:0;font-size:14px;line-height:1.5">The game is saved in this browser.</p></div>
    <div class="rows" style="margin-top:12px"><button class="btn line" type="button" data-act="sound">Sound: ${B.Sound.on ? "on" : "off"}</button><button class="btn bad" type="button" data-act="askNew">Start a new career</button></div>`;
};
SCREEN.news = () => (S.news.length ? S.news.map((n) => `<button class="post ${n.read ? "read" : ""}" type="button" ${n.go ? `data-act="open" data-sheet="${n.go}"` : ""}><span class="u"></span><span class="t"><b>${esc(n.title)}</b><span>${esc(n.body)}</span><i>${weekName(n.w)}${n.s !== S.season ? ", season " + n.s : ""}</i></span></button>`).join("") : `<div class="empty">Nothing in the post.</div>`);

// ---------------------------------------------------------------- choices that slide up over a screen
function drawPicker() {
  let p = UI.picker; const wrap = $("pickerWrap");
  // (a choice about a horse or mare that has since gone is dropped)
  if (p && ((p.hid && !C.horse(S, p.hid) && !S.young.some((x) => x.id === p.hid)) || (p.mid && !S.mares.some((x) => x.id === p.mid)))) p = UI.picker = null;
  wrap.hidden = !p; if (!p) return;
  let head = "", body = "";
  if (p.kind === "race") {
    const r = C.RACES[p.rid], w = r.m.week;
    head = `<i>${day(r.m.date)} · ${esc(trackOf(r.m))}</i><b>${esc(r.name)}</b><span>${cond(r)} · ${money(r.prize)} to the winner${w === S.week ? " · going " + S.going[r.m.i].toLowerCase() : ""}</span>`;
    body = S.horses.map((h) => { const why = h.out ? "On the easy list" : C.barred(S, h, r);
      if (why) return `<button class="kopt" type="button" disabled><span class="t"><b>${esc(h.name)}</b><i>${esc(why)}</i></span></button>`;
      const v = C.view(S, h, r), cur = h.entries[w] === r.id, other = h.entries[w] != null && !cur ? C.RACES[h.entries[w]] : null;
      return `<button class="kopt ${cur ? "cur" : ""}" type="button" data-act="${cur ? "withdraw" : "enter"}" data-h="${h.id}" data-r="${r.id}" data-w="${w}"><span class="t"><b>${esc(h.name)}</b><i>${who(h)}${h.or != null ? " · rated " + h.or : ""}</i>
        <span class="ln">${tick("Trip", v.trip)}${tick(v.going || "Ground", v.ground)}${freshHtml(h)}</span>${other ? `<i>Would switch from the ${esc(other.name)} at ${esc(other.m.course)}</i>` : ""}${v.pen ? `<i>Carries a ${v.pen} lb winner's penalty</i>` : ""}${v.low ? `<i>Out of the handicap: rated below the bottom weight</i>` : ""}</span>
        <span class="r">${chipHtml(v)}<small>${cur ? "Entered: tap to withdraw" : "Fee " + money(v.fee)}</small></span></button>`; }).join("") || `<div class="empty">No horses in training.</div>`;
    if (C.isClaim(r)) body += `<p class="pk-note"><b>${r.type}:</b> every runner is for sale at ${money(C.claimPrice(r))}. A horse worth more than that will very likely be bought.</p>`;
    body += `<p class="pk-note">The chip is the trainer's view from what is known so far. A question mark means nobody knows yet.</p>`;
  } else if (p.kind === "horse") {
    const h = C.horse(S, p.hid), opts = optGroups(h, [6, 4, 4]);
    head = `<i>Find a race</i><b>${esc(h.name)}</b><span>${who(h)}${h.or != null ? " · rated " + h.or : " · no rating yet"} · this week and the next two</span>`;
    body = opts || `<div class="empty">Nothing suitable in the next three weeks.</div>`;
    body += `<p class="pk-note">Best chances first in each week. The whole year is in the calendar.</p>`;
  } else if (p.kind === "sire") {
    const m = S.mares.find((x) => x.id === p.mid), cap = T().fee, all = D.stallions.slice().sort((a, b) => a.fee - b.fee || b.stars - a.stars);
    head = `<i>Choose a stallion</i><b>${esc(m.name)}</b><span>A ${m.stars}-star mare. Better stallions and a better mare make a better foal, but nothing is certain.</span>`;
    body = all.map((s) => { const lock = s.fee > cap, poor = !lock && s.fee > S.bank;
      return `<button class="kopt" type="button" data-act="cover" data-m="${m.id}" data-s="${esc(s.name)}" ${lock || poor ? "disabled" : ""}><span class="t"><b>${esc(s.name)} ${"★".repeat(s.stars)}</b><i>Best at ${s.opt} · peaks at ${s.peak.replace("YO", "")} · ${s.ground.join(", ").toLowerCase()} ground</i>
        ${lock ? `<i>His book opens at ${C.TIERS.slice(1).find((t) => t.fee >= s.fee).n}</i>` : poor ? `<i>More than the bank holds</i>` : ""}</span><span class="r"><b>${money(s.fee)}</b></span></button>`; }).join("");
  } else if (p.kind === "sell") {
    const h = C.horse(S, p.hid) || S.young.find((x) => x.id === p.hid);
    head = `<i>Sell</i><b>${esc(h.name)}</b><span>${h.stage ? "From the stud" : who(h)}</span>`;
    body = `<p class="lede" style="margin:6px 4px 12px">This can't be undone. ${S.sale ? "With a sale on this week you get the full price." : "A private sale brings about a fifth less than a sale week would."}</p>
      <div class="rows"><button class="btn bad" type="button" data-act="sell" data-h="${h.id}">Yes, sell</button><button class="btn line" type="button" data-act="unpick">Keep</button></div>`;
  } else if (p.kind === "new") {
    head = `<i>A new career</i><b>Start again?</b><span>This career is wiped: horses, money and reputation.</span>`;
    body = `<div class="rows" style="margin-top:8px"><button class="btn bad" type="button" data-act="newGame">Yes, start again</button><button class="btn line" type="button" data-act="unpick">Carry on</button></div>`;
  }
  $("picker").innerHTML = `<header class="pk-h"><div class="t">${head}</div><button class="x" type="button" data-act="unpick" aria-label="Close">×</button></header><div class="pk-b">${body}</div>`;
}

// ---------------------------------------------------------------- every tap
const ACT = {
  open: (d) => open(d.sheet, d.tab), close, tab: (d) => { UI.tab[UI.sheet] = d.tab; if (d.tab === "season") UI.scrollTo = "#wk-" + S.week; render(); if (d.tab !== "season") $("shBody").scrollTop = 0; },
  dock: () => { UI.dockShut = !UI.dockShut; drawDock(); fitBoard(); },
  pan: (d) => { B.panTo(d.id); },
  openHorse: (d) => open("stables", null, { horse: +d.h }),
  calWeek: (d) => { UI.calWeek = Math.max(1, Math.min(C.NW, +d.w)); UI.meet = {}; if (d.tab) UI.tab.jockey = d.tab; render(); $("shBody").scrollTop = 0; },
  meet: (d) => { UI.meet[d.m] = !UI.meet[d.m]; render(); },
  big: (d) => { UI.big = d.k; render(); },
  goRace: (d) => { const r = C.RACES[+d.r]; UI.calWeek = r.m.week; UI.meet = { [r.m.i]: true }; UI.tab.jockey = "week"; UI.scrollTo = "#race-" + r.id; render(); },
  horse: (d) => { UI.horse = +d.h || null; render(); $("shBody").scrollTop = 0; },
  pickRace: (d) => { UI.picker = { kind: "race", rid: +d.r }; drawPicker(); },
  pickHorse: (d) => { UI.picker = { kind: "horse", hid: +d.h }; drawPicker(); },
  pickSire: (d) => { UI.picker = { kind: "sire", mid: +d.m }; drawPicker(); },
  askSell: (d) => { UI.picker = { kind: "sell", hid: +d.h }; drawPicker(); },
  askNew: () => { UI.picker = { kind: "new" }; drawPicker(); },
  unpick: () => { UI.picker = null; drawPicker(); },
  enter: (d) => { const h = C.horse(S, +d.h), r = C.RACES[+d.r]; const err = act(() => C.enter(S, +d.h, +d.r)); UI.picker = null; drawPicker(); toast(err || `${h.name} is entered: ${r.name}, ${day(r.m.date)}`, !!err); },
  withdraw: (d) => { act(() => C.withdraw(S, +d.h, +d.w)); UI.picker = null; drawPicker(); toast("Withdrawn. The entry fee is back in the bank."); },
  picks: () => { const made = act(() => C.trainerPicks(S)); toast(made.length ? (made.length === 1 ? `The trainer has entered ${made[0].h.name} at ${made[0].r.m.course}.` : `The trainer has entered ${made.length} horses.`) : "The trainer sees nothing worth running for this week."); },
  gallop: (d) => { const out = act(() => C.gallop(S, +d.h, d.k)); if (out) { UI.notes[+d.h] = out; render(); } },
  buy: (d) => { const err = act(() => C.buy(S, +d.l)); toast(err || "Bought. Welcome to the string.", !!err); },
  sell: (d) => { UI.picker = null; UI.horse = null; const v = act(() => C.sell(S, +d.h)); toast(`Sold for ${money(v)}.`); },
  retire: (d) => { act(() => C.retireToStud(S, +d.h)); UI.horse = null; open("stud"); },
  toYard: (d) => { act(() => C.moveToYard(S, +d.h)); toast("Into the yard."); },
  cover: (d) => { const err = act(() => C.cover(S, +d.m, d.s)); UI.picker = null; drawPicker(); toast(err || `Covered by ${d.s}. The foal is due next spring.`, !!err); },
  advance: () => { const before = S.bank; UI.notes = {}; UI.report = C.advance(S); UI.calWeek = S.week; UI.meet = {}; save(); open("report"); tumble(S.bank - before); if (UI.report.results.some((r) => r.pos === 1)) B.Sound.cheer && B.Sound.cheer(3); },
  sound: () => { B.Sound.set(!B.Sound.on); render(); },
  newGame: () => { S = C.newGame((Date.now() % 2147483647) | 0); Object.assign(UI, { sheet: null, horse: null, picker: null, calWeek: S.week, meet: {}, report: null, notes: {}, tab: {} }); save(); render(); toast("A new career. Good luck."); },
};
document.addEventListener("click", (e) => {
  const el = e.target.closest("[data-act]"); if (!el || el.disabled) { if (e.target.id === "pickerWrap") ACT.unpick(); else if (e.target.id === "sheetWrap") close(); return; }
  const f = ACT[el.dataset.act]; if (f) { e.preventDefault(); f(el.dataset, el); }
});
addEventListener("keydown", (e) => { if (e.key === "Escape") { if (UI.picker) ACT.unpick(); else if (UI.sheet) close(); } });

function render() { drawBar(); drawNav(); drawBoard(); drawDock(); drawSheet(); drawPicker(); fitBoard(); drawEdges(); }
render();
window.CAREER_UI = { get S() { return S; }, UI, open, close, render, ACT };
})();
