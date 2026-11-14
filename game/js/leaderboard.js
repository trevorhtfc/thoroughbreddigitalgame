/* The leaderboard (owner, 13-14 Nov 2026): the standings and your position on the home screen.
   Name only, no password: a stable name is typed once (with your colours, js/colours.js) and remembered on this phone
   or computer with an id and a secret the browser makes up, so every game played here is yours and nobody else can
   post under your name. The scores are kept by the game's small server (server/worker.js, a Cloudflare database):
       today's card      one go a day, the first finish counts (rules.js: noteDaily)
       yesterday         the day before's final result
       best ever         every stable's best game of this season, daily or random
   Each season (Royal Ascot, Newmarket) has its own boards. A finished game that can't be sent (no signal, no name
   yet) waits in the browser and goes the next time the game is opened. */
const LB = { view: "today", all: false, data: {}, state: {}, busy: false };
const LB_PLAYER = "tb-player", LB_OUT = "tb-outbox", LB_API = "/api";
const lbOrd = n => n + (n % 10 === 1 && n % 100 !== 11 ? "st" : n % 10 === 2 && n % 100 !== 12 ? "nd" : n % 10 === 3 && n % 100 !== 13 ? "rd" : "th");
const lbHex = n => { const a = new Uint8Array(n); crypto.getRandomValues(a); return [...a].map(x => x.toString(16).padStart(2, "0")).join(""); };
function lbPlayer() {
  let p = null; try { p = JSON.parse(localStorage.getItem(LB_PLAYER) || "null"); } catch (e) {}
  if (!p || !p.id || !p.secret) { p = { id: lbHex(12), secret: lbHex(20), name: "", ok: false }; lbKeep(p); }
  return p;
}
function lbKeep(p) { try { localStorage.setItem(LB_PLAYER, JSON.stringify(p)); } catch (e) {} }
const lbName = () => { const p = lbPlayer(); return p.name || ""; };
// the same rules as the server's (server/worker.js: cleanName), so a name is refused here before it is sent
function lbNameProblem(v) {
  const name = String(v == null ? "" : v).replace(/\s+/g, " ").trim();
  if (name.length < 3) return "A stable name needs at least 3 letters.";
  if (name.length > 20) return "Keep it to 20 letters or fewer.";
  if (!/^[A-Za-z0-9 '&.\-]+$/.test(name) || !/[A-Za-z]/.test(name)) return "Letters, numbers and spaces only.";
  return "";
}
async function lbCall(path, body) {
  try {
    const r = await fetch(LB_API + path, body ? { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : { cache: "no-store" });
    let data = null; try { data = await r.json(); } catch (e) {}
    return { status: r.status, data: data || {} };
  } catch (e) { return { status: 0, data: {} }; }
}
// Register the stable's name (or change it, or send new colours). Gives "" when it's done, or what went wrong:
// "taken", "name" (the server won't have it), "offline" (kept here, and sent the next time the game is opened).
async function lbRegister(name) {
  const p = lbPlayer(); name = String(name == null ? p.name : name).replace(/\s+/g, " ").trim();
  if (lbNameProblem(name)) return "name";
  const r = await lbCall("/player", { id: p.id, secret: p.secret, name, colours: MY ? MY.code : undefined });
  if (r.status === 200 && r.data.ok) { p.name = r.data.name || name; p.ok = true; p.sent = MY ? MY.code : ""; lbKeep(p); lbFlush(); return ""; }
  if (r.status === 409) return "taken";
  if (r.status === 400) return "name";
  if (r.status === 403) return "name";
  p.name = name; p.ok = false; lbKeep(p); return "offline";
}
// A finished game for the board: { season, kind: "daily" | "random", day, seed, prize, wins, title }
function lbSubmit(score) {
  try { const out = lbOutbox(); if (!out.some(x => x.season === score.season && x.kind === score.kind && x.seed === score.seed && x.day === score.day)) { out.push(score); localStorage.setItem(LB_OUT, JSON.stringify(out.slice(-30))); } } catch (e) {}
  return lbFlush();
}
function lbOutbox() { try { const v = JSON.parse(localStorage.getItem(LB_OUT) || "[]"); return Array.isArray(v) ? v : []; } catch (e) { return []; } }
async function lbFlush() {
  if (LB.busy) return; LB.busy = true;
  try {
    const p = lbPlayer();
    if (p.name && (!p.ok || (MY && p.sent !== MY.code))) {            // a name or colours still to send
      const r = await lbCall("/player", { id: p.id, secret: p.secret, name: p.name, colours: MY ? MY.code : undefined });
      if (r.status === 200 && r.data.ok) { p.ok = true; p.sent = MY ? MY.code : ""; lbKeep(p); }
      else if (r.status === 409 || r.status === 400) { p.name = ""; p.ok = false; lbKeep(p); }       // taken meanwhile: ask again
    }
    if (!p.ok) return;
    let sent = false;
    for (const s of lbOutbox()) {
      const r = await lbCall("/score", { id: p.id, secret: p.secret, ...s });
      if (r.status === 0 || r.status >= 500) break;                    // no signal: try again next time
      if (r.status === 403) { p.ok = false; lbKeep(p); break; }
      try { localStorage.setItem(LB_OUT, JSON.stringify(lbOutbox().filter(x => !(x.season === s.season && x.kind === s.kind && x.seed === s.seed && x.day === s.day)))); } catch (e) {}
      sent = true;
    }
    if (sent) { LB.data = {}; lbShow(true); lbResult(); }
  } finally { LB.busy = false; }
}
// ----- the standings -----
async function lbLoad(view, fresh) {
  const k = MEETING.id + "|" + view, had = LB.data[k];
  if (had && !fresh && Date.now() - had.at < 30000) return had;
  LB.state[k] = "loading";
  const r = await lbCall(`/board?season=${encodeURIComponent(MEETING.id)}&view=${view}&top=20&id=${encodeURIComponent(lbPlayer().id)}`);
  if (r.status === 200 && r.data.ok) { LB.data[k] = { ...r.data, at: Date.now() }; LB.state[k] = "ok"; }
  else LB.state[k] = "down";
  return LB.data[k] || null;
}
const lbIcons = new Map();
function lbIcon(code) {
  if (!lbIcons.has(code)) { let src = ""; try { const spec = window.SilksPaint && SilksPaint.decode(code); if (spec) src = SilksPaint.icon(spec, 56).toDataURL("image/png"); } catch (e) {} lbIcons.set(code, src); }
  const src = lbIcons.get(code); return src ? `<img class="silk" src="${src}" alt="">` : `<span class="silk lb-nosilk"></span>`;
}
const LB_VIEWS = [["today", "Today"], ["yesterday", "Yesterday"], ["best", "Best ever"]];
function lbRow(r) { return `<li class="${r.me ? "me" : ""}"><span class="lb-n">${r.rank}</span>${lbIcon(r.colours)}<b>${esc2(r.name)}${r.me ? " <i>you</i>" : ""}</b><span class="lb-p">${money(r.prize)}</span></li>`; }
// The panel on the home screen
function lbPaint() {
  const box = document.getElementById("menuBoard"); if (!box) return;
  const k = MEETING.id + "|" + LB.view, d = LB.data[k], st = LB.state[k], p = lbPlayer();
  const tabs = LB_VIEWS.map(([id, name]) => `<button type="button" class="lb-tab ${LB.view === id ? "on" : ""}" data-lbview="${id}" aria-pressed="${LB.view === id}">${name}</button>`).join("");
  let body;
  if (!d) body = `<p class="lb-note">${st === "down" ? "The leaderboard can't be reached just now." : "Fetching the standings…"}</p>`;
  else {
    const n = LB.all ? 20 : 5, rows = d.rows.slice(0, n), mine = d.me && !rows.some(r => r.me) ? d.me : null;
    const n1 = d.count === 1, stables = `${d.count} stable${n1 ? "" : "s"}`;
    const count = d.count === 0 ? (LB.view === "today" ? "Nobody has finished today's card yet. Be the first." : LB.view === "yesterday" ? "Nobody finished yesterday's card." : "No games on the board yet.")
      : LB.view === "today" ? `${stables} ${n1 ? "has" : "have"} played today's card.` : LB.view === "yesterday" ? `${stables} played yesterday's card.` : `${stables} on the board.`;
    const you = d.me ? `You are <b>${lbOrd(d.me.rank)}</b> of ${stables}.` : p.name && LB.view === "today" ? "Play today's card to join the board." : "";
    body = `${rows.length ? `<ol class="lb-rows">${rows.map(lbRow).join("")}${mine ? `<li class="lb-gap" aria-hidden="true">…</li>${lbRow(mine)}` : ""}</ol>` : ""}
      <p class="lb-note">${d.me ? you : (you ? you + " " : "") + count}${d.rows.length > 5 ? ` <button type="button" class="lb-more" data-lbmore="1">${LB.all ? "Show the top 5" : d.count <= 20 ? "Show all " + d.count : "Show the top 20"}</button>` : ""}</p>`;
  }
  // no stable name yet (colours made before the leaderboard came, or the name was taken meanwhile): ask here
  const join = !p.name && hasColours() ? `<form class="lb-join" id="lbJoin"><label for="lbNameIn">Name your stable to join the leaderboard</label><div><input id="lbNameIn" maxlength="20" autocomplete="off" autocapitalize="words" spellcheck="false" placeholder="Stable name"><button class="mc-change" type="submit">Join</button></div><p class="lb-err" id="lbErr" role="alert"></p></form>` : "";
  box.innerHTML = `<div class="lb-head"><div class="mc-h">Leaderboard <small>${W.gameTitle || ""}</small></div><div class="lb-tabs" role="group" aria-label="Which board">${tabs}</div></div>${body}${join}`;
}
async function lbShow(fresh) {
  if (!document.getElementById("menuBoard")) return;
  lbPaint(); const v = LB.view; await lbLoad(v, fresh); if (LB.view === v) lbPaint();
}
// On the final standings: where this game stands
async function lbResult() {
  const el = document.getElementById("lbLine"); if (!el || typeof S === "undefined" || !S) return;
  const view = isDaily() ? (S.day === ukDay() ? "today" : S.day === ukDay(Date.now() - 864e5) ? "yesterday" : null) : "best"; if (!view) return;
  if (!lbPlayer().name) { el.innerHTML = `Name your stable on the home screen to put this on the leaderboard.`; return; }
  const d = await lbLoad(view, true), el2 = document.getElementById("lbLine"); if (!el2) return;
  if (!d) { el2.textContent = "The leaderboard can't be reached just now. Your result will be sent when it can."; return; }
  if (!d.me) { el2.textContent = ""; return; }
  el2.innerHTML = view === "best" ? `Your best ${MEETING.id === "royal-ascot" ? "week" : "season"} is <b>${lbOrd(d.me.rank)}</b> of ${d.count} on the best-ever board.` : `${view === "today" ? "Today's" : "Yesterday's"} card: you are <b>${lbOrd(d.me.rank)}</b> of ${d.count} stable${d.count === 1 ? "" : "s"}.`;
}
document.addEventListener("click", e => {
  const t = e.target.closest && e.target.closest("[data-lbview],[data-lbmore]"); if (!t) return;
  if (t.dataset.lbview) { LB.view = t.dataset.lbview; LB.all = false; lbShow(); }
  else { LB.all = !LB.all; lbPaint(); }
});
document.addEventListener("submit", async e => {
  if (!e.target || e.target.id !== "lbJoin") return; e.preventDefault();
  const inp = document.getElementById("lbNameIn"), err = document.getElementById("lbErr"), name = inp.value, bad = lbNameProblem(name);
  if (bad) { err.textContent = bad; return; }
  err.textContent = "Checking the name…";
  const r = await lbRegister(name);
  if (r === "taken") { document.getElementById("lbErr").textContent = "That name is taken. Try another."; return; }
  if (r === "name") { document.getElementById("lbErr").textContent = "That name can't be used. Try another."; return; }
  toast(r === "offline" ? "Saved. Your name will be registered when the leaderboard can be reached." : "Your stable is on the leaderboard");
  LB.data = {}; lbShow(true);
});
lbFlush();
