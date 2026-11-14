/* Your colours: the maker (owner, 13 Nov 2026).
   Every player makes their own silks: a jacket, sleeves and a cap, each a template with a colour and a second colour
   from the palette (silks-paint.js holds the templates, the palette and the painting). There is no choosing from the
   54 ready-made silks; those are the opposition's. The colours are remembered on this phone or computer
   (rules.js: setColours, the key "tb-colours") for every game and both seasons.
   A player with no colours yet is brought here before their first game (needColours), then carries on. */
let CM = null;   // the maker while it is open: { spec, tab, first, then }
const CM_TABS = [["body", "Jacket", () => SilksPaint.JACKETS], ["sleeves", "Sleeves", () => SilksPaint.SLEEVES], ["cap", "Cap", () => SilksPaint.CAPS]];
const cmCopy = s => JSON.parse(JSON.stringify(s));
// Asked before a game starts: true if the maker had to be opened first (it calls `again` once colours are saved)
function needColours(again) { if (hasColours() || !window.SilksPaint) return false; openColours({ first: true, then: again }); return true; }
function openColours(opts = {}) {
  if (!window.SilksPaint || CM) return;
  CM = { spec: MY ? cmCopy(MY.spec) : SilksPaint.random(), tab: "body", first: !!opts.first || !MY, then: opts.then || null };
  const box = document.createElement("div"); box.className = "cm"; box.id = "cm"; box.setAttribute("role", "dialog"); box.setAttribute("aria-modal", "true"); box.setAttribute("aria-labelledby", "cmTitle");
  box.innerHTML = `<div class="cm-in">
      <header class="cm-head"><div><div class="cm-k">${CM.first ? "Before your first runner" : "Your colours"}</div><h2 class="cm-t" id="cmTitle">${CM.first ? "Make your colours" : "Change your colours"}</h2>
        <p class="cm-lede">The silks your jockeys wear in every race. Choose a jacket, sleeves and a cap, and two colours for each. They are remembered for every game.</p></div>
        ${CM.first ? "" : `<button class="cm-x" id="cmClose" type="button" aria-label="Close without changing">&times;</button>`}</header>
      <div class="cm-main">
        <aside class="cm-show"><div class="cm-big" id="cmBig"></div><p class="cm-say" id="cmSay"></p><button class="tb-btn ghost cm-dice" id="cmDice" type="button">Surprise me</button></aside>
        <section class="cm-pick">
          <div class="cm-tabs" role="tablist">${CM_TABS.map(([id, name]) => `<button role="tab" type="button" class="cm-tab" data-cmtab="${id}">${name}</button>`).join("")}</div>
          <div class="cm-row"><span class="cm-l">Colour</span><div class="cm-cols" id="cmA" role="group" aria-label="Colour"></div></div>
          <div class="cm-row"><span class="cm-l">Second colour <small>for the pattern</small></span><div class="cm-cols" id="cmB" role="group" aria-label="Second colour"></div></div>
          <div class="cm-l cm-lp">Pattern</div>
          <div class="cm-pats" id="cmPats" role="group" aria-label="Pattern"></div>
        </section>
      </div>
      <footer class="cm-foot"><button class="tb-btn" id="cmSave" type="button">${CM.first ? "These are my colours" : "Save my colours"} <span aria-hidden="true">›</span></button></footer>
    </div>`;
  document.body.appendChild(box); CM.box = box;
  box.addEventListener("click", cmClick);
  cmPaint();
  const f = box.querySelector(".cm-tab"); if (f) f.focus({ preventScroll: true });
}
function closeColours() { if (!CM) return; CM.box.remove(); CM = null; }
function cmPaint(only) {
  if (!CM) return;
  const part = CM.spec[CM.tab], list = CM_TABS.find(t => t[0] === CM.tab)[2](), q = s => CM.box.querySelector(s);
  // the big picture and how racing would describe it
  const big = q("#cmBig"); big.textContent = ""; big.appendChild(SilksPaint.icon(CM.spec, 220));
  q("#cmSay").textContent = SilksPaint.describe(CM.spec);
  CM.box.querySelectorAll(".cm-tab").forEach(b => { const on = b.dataset.cmtab === CM.tab; b.classList.toggle("on", on); b.setAttribute("aria-selected", String(on)); });
  const cols = (which) => SilksPaint.PALETTE.map(([name, hex]) => `<button type="button" class="cm-c ${part[which] === hex ? "on" : ""}" data-cmcol="${which}" data-hex="${hex}" style="--c:${hex}" aria-label="${name}" aria-pressed="${part[which] === hex}" title="${name}"></button>`).join("");
  q("#cmA").innerHTML = cols("a"); q("#cmB").innerHTML = cols("b");
  q("#cmB").parentNode.classList.toggle("off", part.p === "plain");   // a plain jacket, sleeve or cap has no second colour to show
  // every pattern for this part, each shown on the whole set as it would look
  const pats = q("#cmPats"); pats.textContent = "";
  list.forEach(([p, name]) => {
    const b = document.createElement("button"); b.type = "button"; b.className = "cm-p" + (part.p === p ? " on" : ""); b.dataset.cmpat = p; b.setAttribute("aria-pressed", String(part.p === p));
    const s = cmCopy(CM.spec); s[CM.tab].p = p; b.appendChild(SilksPaint.icon(s, 66));
    const l = document.createElement("span"); l.textContent = name; b.appendChild(l); pats.appendChild(b);
  });
  if (only !== "keep") { const on = pats.querySelector(".cm-p.on"); if (on && on.scrollIntoView) { try { on.scrollIntoView({ block: "nearest" }); } catch (e) {} } }
}
function cmClick(e) {
  const t = e.target.closest("button"); if (!t || !CM) return;
  const d = t.dataset;
  if (d.cmtab) { CM.tab = d.cmtab; cmPaint(); return; }
  if (d.cmcol) {
    const part = CM.spec[CM.tab], was = part[d.cmcol]; part[d.cmcol] = d.hex;
    // a pattern in the colour it sits on can't be seen: keep the two apart by swapping them over
    if (part.a === part.b && part.p !== "plain") part[d.cmcol === "a" ? "b" : "a"] = was;
    cmPaint("keep"); return;
  }
  if (d.cmpat) { const part = CM.spec[CM.tab]; part.p = d.cmpat; if (part.p !== "plain" && part.a === part.b) part.b = SilksPaint.PALETTE.find(c => c[1] !== part.a)[1]; cmPaint("keep"); return; }
  switch (t.id) {
    case "cmDice": CM.spec = SilksPaint.random(); cmPaint(); break;
    case "cmClose": closeColours(); break;
    case "cmSave": {
      const then = CM.then, first = CM.first;
      if (!setColours(CM.spec)) { toast("Those colours couldn't be saved. Try again."); break; }
      closeColours(); render(); if (menuOpen) paintMenu(true);
      toast(first ? "Your colours are registered" : "Your colours are changed");
      if (then) then();
      break;
    }
  }
}
addEventListener("keydown", e => { if (e.key === "Escape" && CM && !CM.first) closeColours(); });
document.addEventListener("click", e => { const b = e.target.closest && e.target.closest("#menuColours"); if (b) openColours(); });
