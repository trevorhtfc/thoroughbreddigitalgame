/* The money tumbling out of your budget (owner, 14 Nov 2026: "a more visible tumbling of the budget. The money should
   graphically drop from the budget to put into perspective for the players how much they are spending").

   Every payment is booked by ledger() (js/accounts.js), which calls budgetTumble(). The budget figure you can see (the
   money in the top bar, the auction's "Budget", a sheet footer's "… left": anything marked data-budget) counts down
   to the new figure; the amount drops out of it as a price tag with what share of your budget it was; sovereigns, and
   for a big spend banknotes, tumble out and fall away; and a slice of the budget meter under the top bar's money,
   the size of the spend, breaks off and drops. The more you spend, the more falls. A refund (a mare sent back, a
   vet's report) goes the other way: the figure counts up and the amount rises into it.
   If no budget figure can be seen when you pay (the foal's card or a film is in front of it), the tumble waits until
   one can. With "reduce motion" set, the figure simply changes and the tag shows in place. */
const TB = { queue: [], tick: null, layer: null, busy: false };
const tbStart = () => {
  const pw = typeof held === "function" && held("powerhouse") ? POWERHOUSE[held("powerhouse").tier] : 0;
  return Math.max(1, startBudget() + pw);
};
// share of the starting budget, as a plain figure: "12% of your budget", "under 1% of your budget"
function tbShare(amt) { const p = amt / tbStart() * 100; return p < 1 ? "under 1%" : p < 10 ? (Math.round(p * 10) / 10) + "%" : Math.round(p) + "%"; }
function budgetTumble(amt, before, now) {
  if (!amt) return;
  TB.queue.push({ amt, before, now, at: Date.now() });
  tbRun();
}
const tbStill = () => { try { return matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) { return false; } };
// the budget figure to tumble from: one the player can see right now, nothing in front of it
function tbSource() {
  const els = [...document.querySelectorAll("[data-budget]")];
  // the auction's own figure first (it covers the bar), then the top bar, then a sheet footer
  els.sort((a, b) => (b.closest(".auc") ? 2 : b.closest(".bar") ? 1 : 0) - (a.closest(".auc") ? 2 : a.closest(".bar") ? 1 : 0));
  for (const el of els) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height || r.bottom < 0 || r.top > innerHeight) continue;
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (hit && (hit === el || el.contains(hit) || (hit.closest && hit.closest("[data-accounts]") === el.closest("[data-accounts]") && el.closest("[data-accounts]")))) return el;
  }
  return null;
}
function tbRun() {
  if (TB.busy || !TB.queue.length) return;
  const el = tbSource();
  if (!el) { if (Date.now() - TB.queue[0].at > 60000) TB.queue.shift(); setTimeout(tbRun, 350); return; }
  // payments made together (a foal and its fee, two quick buys) fall as one
  const first = TB.queue[0], same = TB.queue.filter(q => Math.sign(q.amt) === Math.sign(first.amt));
  TB.queue = TB.queue.filter(q => !same.includes(q));
  const amt = same.reduce((a, q) => a + q.amt, 0), before = same[0].before, now = same[same.length - 1].now;
  TB.busy = true; setTimeout(() => { TB.busy = false; tbRun(); }, 650);
  tbCount(before, now);
  tbFall(el, amt);
}
// the budget figures count from the old figure to the new one
function tbCount(from, to) {
  const t0 = performance.now(), dur = tbStill() ? 0 : 1100 + Math.min(900, Math.abs(from - to) / tbStart() * 4000);
  TB.tick = { from, to, t0, dur };
  document.querySelectorAll("[data-budget]").forEach(e => e.classList.add(to < from ? "tb-down" : "tb-up"));
  const step = (t) => {
    const T = TB.tick; if (!T || T.t0 !== t0) return;
    const k = T.dur ? Math.min(1, (t - T.t0) / T.dur) : 1, e = 1 - Math.pow(1 - k, 3), v = Math.round((T.from + (T.to - T.from) * e) / 500) * 500;
    // (the bar is redrawn now and then: whatever is on screen is set every frame)
    document.querySelectorAll("[data-budget]").forEach(x => { x.textContent = money(k >= 1 ? S.budget : v); });
    tbMeter(k >= 1 ? S.budget : v);
    if (k < 1) requestAnimationFrame(step);
    else { TB.tick = null; setTimeout(() => document.querySelectorAll("[data-budget]").forEach(x => x.classList.remove("tb-down", "tb-up")), 500); }
  };
  requestAnimationFrame(step);
}
// the meter under the top bar's money: what's left of your starting budget
function tbMeter(v) { document.querySelectorAll(".t-meter b").forEach(b => { b.style.width = Math.max(0, Math.min(100, v / tbStart() * 100)) + "%"; }); }
function tbLayer() {
  if (!TB.layer || !TB.layer.isConnected) { TB.layer = document.createElement("div"); TB.layer.className = "tb-layer"; TB.layer.setAttribute("aria-hidden", "true"); document.body.appendChild(TB.layer); }
  return TB.layer;
}
function tbFall(el, amt) {
  const r = el.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2, layer = tbLayer(), still = tbStill();
  const spend = amt > 0, frac = Math.min(1, Math.abs(amt) / tbStart());
  // the price tag
  const tag = document.createElement("div"); tag.className = "tb-tag " + (spend ? "out" : "in");
  tag.innerHTML = `<b>${spend ? "−" : "+"}${money(Math.abs(amt))}</b><small>${tbShare(Math.abs(amt))} of your budget</small>`;
  // a bigger spend, a bigger tag (less so on a phone)
  const sc = 1 + Math.min(innerWidth < 600 ? 0.2 : 0.5, frac * 2.2);
  tag.style.setProperty("--s", sc.toFixed(2));
  layer.appendChild(tag);
  const tw = tag.offsetWidth * sc, th = tag.offsetHeight * sc, x0 = Math.max(8, Math.min(innerWidth - tw - 8, cx - tw / 2));
  if (still) { tag.style.transform = `translate(${x0}px,${r.bottom + 6}px)`; setTimeout(() => tag.remove(), 2600); return; }
  // a spend pops out and drops away; a refund rises into the figure
  const parts = [spend ? { el: tag, x: x0, y: r.bottom - th * 0.3, vx: (Math.random() - 0.5) * 0.6, vy: -1.6, g: 0.11, a: 0, va: (Math.random() - 0.5) * 0.16, life: 0, max: 150, tag: true }
    : { el: tag, x: x0, y: r.bottom + 40, vx: 0, vy: -0.75, g: 0.004, a: 0, va: 0, life: 0, max: 95, tag: true }];
  if (spend) {
    // sovereigns, and banknotes for a big spend: the bigger the spend, the more fall
    const coins = Math.round(5 + frac * 70), notes = frac >= 0.04 ? Math.min(10, Math.round(frac * 40)) : 0;
    for (let i = 0; i < Math.min(42, coins) + notes; i++) {
      const note = i >= Math.min(42, coins), p = document.createElement("i"); p.className = note ? "tb-note" : "tb-coin";
      layer.appendChild(p);
      parts.push({ el: p, x: cx + (Math.random() - 0.5) * r.width * 0.8, y: cy + (Math.random() - 0.5) * r.height * 0.5,
        vx: (Math.random() - 0.5) * (note ? 5 : 7), vy: -2 - Math.random() * 4.5, g: note ? 0.16 : 0.32, drag: note ? 0.985 : 0.995,
        a: Math.random() * 360, va: (Math.random() - 0.5) * (note ? 14 : 24), flip: Math.random() * 360, vf: 6 + Math.random() * 14, life: -Math.floor(Math.random() * 10), max: 120 });
    }
    // a slice of the budget meter breaks off: the share of your budget this was
    const m = el.closest(".bar") && document.querySelector(".bar .t-meter");
    if (m) {
      const mr = m.getBoundingClientRect(), w0 = mr.width * Math.min(1, (S.budget + amt) / tbStart()), w1 = mr.width * Math.max(0, S.budget / tbStart());
      const chip = document.createElement("i"); chip.className = "tb-chip"; chip.style.width = Math.max(3, w0 - w1) + "px"; chip.style.height = mr.height + "px";
      layer.appendChild(chip);
      parts.push({ el: chip, x: mr.left + w1, y: mr.top, vx: 0.6 + Math.random(), vy: -0.6, g: 0.22, a: 0, va: 2 + Math.random() * 4, life: 0, max: 110 });
    }
  }
  let last = performance.now();
  const frame = (t) => {
    const k = Math.min(3, (t - last) / 16.7); last = t; let alive = 0;
    for (const p of parts) {
      if (p.done) continue;
      p.life += k; if (p.life < 0) { p.el.style.opacity = 0; alive++; continue; }
      p.vy += p.g * k; if (p.drag) { p.vx *= Math.pow(p.drag, k); p.vy *= Math.pow(p.drag, k); }
      if (p.tag) p.vx *= Math.pow(0.97, k);
      p.x += p.vx * k; p.y += p.vy * k; p.a += p.va * k; if (p.vf) p.flip += p.vf * k;
      const fade = p.tag ? Math.max(0, Math.min(1, (p.max - p.life) / 40)) : Math.max(0, Math.min(1, (p.max - p.life) / 30, (innerHeight + 30 - p.y) / 80));
      p.el.style.opacity = fade.toFixed(3);
      p.el.style.transform = `translate(${p.x.toFixed(1)}px,${p.y.toFixed(1)}px) rotate(${p.a.toFixed(1)}deg)` + (p.vf ? ` rotateY(${p.flip.toFixed(0)}deg)` : "") + (p.tag ? ` scale(${p.el.style.getPropertyValue("--s") || 1})` : "");
      if (p.life >= p.max || p.y > innerHeight + 60 || fade <= 0) { p.done = true; p.el.remove(); } else alive++;
    }
    if (alive) requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}
