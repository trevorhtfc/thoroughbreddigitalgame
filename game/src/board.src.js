// =====================================================================================================================
// The Newmarket board: the game's home and its map (from newmarket-live/, the living map).
// The board stays the painting; light, clouds, smoke, banners and the lit places are drawn over it here (plain canvas
// and SVG, no 3D library), and js/life.js adds the 3D horses, people and horseboxes when three.js is available.
// The game (js/ui.js) drives it through window.BOARD: which places are open, done, locked or next; the card each place
// shows; the inked trail from one step to the next; the time of day; the sounds.
// Board pixels throughout: 1448 x 1086. A thing at board point (x, y) with height h is drawn at (x, y - h).
// =====================================================================================================================
(() => {
const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
// phones and tablets ("lite"): the board runs at 30 frames a second, stops altogether under a sheet, and doesn't lean
const LITE = document.documentElement.classList.contains("lite");
const MW = 1448, MH = 1086;
const svgNS = "http://www.w3.org/2000/svg";
const $id = (id) => document.getElementById(id);
const BASE = "assets/newmarket/";

// ---------------------------------------------------------------- the places
// Each lit outline is the owner's own line (markup/sites-markup*.jpg), refined onto the roof edges (tools/refine_sites.py).
const SITES = %%SITES%%;
const ICONS = { gavel: `%%ICON:gavel%%`, temple: `%%ICON:greek-temple%%`, stable: `%%ICON:stable%%`, head: `%%ICON:horse-head%%` };
// at: where the medal and label stand; pic: [x, y, width] of the board shown in the place's card and sheet header
const PLACES = [
  { id: "warren", name: "Warren Hill<br>Gallops", at: [165, 487], icon: "horse", title: "Warren Hill", pic: [170, 410, 360] },
  { id: "palace", name: "Palace House", at: [436, 676], icon: "temple", title: "Palace House", pic: [440, 615, 240] },
  { id: "jockey", name: "The Jockey Club", at: [660, 682], icon: "jc", title: "The Jockey Club", pic: [662, 640, 230] },
  { id: "tatts", name: "Tattersalls", at: [946, 750], icon: "gavel", title: "Tattersalls", pic: [915, 690, 420] },
  { id: "stables", name: "Your Stables", at: [963, 909], icon: "stable", title: "Your Stables", pic: [930, 880, 500] },
  { id: "stud", name: "National Stud", at: [1344, 493], icon: "head", title: "National Stud", pic: [1170, 500, 440] },
];
// To the Races stands on the board just above the banner avenue, upright like the places' signs
const RACES_AT = [1290, 232];
const RACES = { id: "races", title: "To the Races", at: RACES_AT, pic: [1110, 330, 520] };
const placeOf = (id) => (id === "races" ? RACES : PLACES.find((q) => q.id === id));
const stage = $id("stage"), glow = $id("glow"), card = $id("card");
const smoothPath = (pts) => {                                      // a closed curve through the outline's points
  const n = pts.length, p = (i) => pts[(i + n) % n];
  let d = `M${p(0)[0]},${p(0)[1]}`;
  for (let i = 0; i < n; i++) {
    const a = p(i - 1), b = p(i), c = p(i + 1), e = p(i + 2);
    d += `C${(b[0] + (c[0] - a[0]) / 6).toFixed(1)},${(b[1] + (c[1] - a[1]) / 6).toFixed(1)} ${(c[0] - (e[0] - b[0]) / 6).toFixed(1)},${(c[1] - (e[1] - b[1]) / 6).toFixed(1)} ${c[0]},${c[1]}`;
  }
  return d + "Z";
};
const openPath = (pts) => {                                        // an open curve through a route's points
  const n = pts.length, p = (i) => pts[Math.max(0, Math.min(n - 1, i))];
  let d = `M${p(0)[0]},${p(0)[1]}`;
  for (let i = 0; i < n - 1; i++) {
    const a = p(i - 1), b = p(i), c = p(i + 1), e = p(i + 2);
    d += `C${(b[0] + (c[0] - a[0]) / 6).toFixed(1)},${(b[1] + (c[1] - a[1]) / 6).toFixed(1)} ${(c[0] - (e[0] - b[0]) / 6).toFixed(1)},${(c[1] - (e[1] - b[1]) / 6).toFixed(1)} ${c[0]},${c[1]}`;
  }
  return d;
};
for (const p of PLACES) {
  const site = SITES.find((s) => s.id === p.id);
  if (site) {
    const d = site.sharp ? "M" + site.poly.map((q) => q.join(",")).join("L") + "Z" : smoothPath(site.poly);
    const g = document.createElementNS(svgNS, "g"); g.setAttribute("class", "site"); g.id = "site-" + p.id;
    g.innerHTML = `<path class="wash" d="${d}"/><path class="halo" d="${d}"/><path class="rim" d="${d}"/><path class="line" d="${d}"/><path class="spark" d="${d}" pathLength="548"/><path class="hit" d="${d}"/>`;
    g.addEventListener("pointerenter", () => hover(p.id, true)); g.addEventListener("pointerleave", () => hover(p.id, false));
    g.addEventListener("click", () => choose(p.id));
    glow.appendChild(g);
  }
  const b = document.createElement("button");
  b.className = "loc"; b.type = "button"; b.dataset.id = p.id; b.style.left = p.at[0] + "px"; b.style.top = (p.at[1] - 16) + "px";
  const icon = p.icon === "jc" ? `<span class="jc">JC</span>` : p.icon === "horse" ? `<span class="hz"></span>` : `<svg viewBox="0 0 512 512">${ICONS[p.icon]}</svg>`;
  b.innerHTML = `<span class="medal">${icon}<i class="done-tick" aria-hidden="true"></i></span><span class="pill">${p.name}</span><span class="nexttag" aria-hidden="true">Next</span><span class="ripple"></span><span class="beacon"></span>`;
  b.setAttribute("aria-label", p.title);
  b.addEventListener("mouseenter", () => hover(p.id, true)); b.addEventListener("mouseleave", () => hover(p.id, false));
  b.addEventListener("focus", () => hover(p.id, true)); b.addEventListener("blur", () => hover(p.id, false));
  b.addEventListener("click", () => choose(p.id));
  stage.appendChild(b);
}
let chosen = null, hovered = null;
const siteEl = (id) => $id("site-" + id);
const locEl = (id) => (id === "races" ? $id("races") : stage.querySelector(`.loc[data-id="${id}"]`));
function hover(id, on) {
  hovered = on ? id : (hovered === id ? null : hovered); placeSound();
  if (id === chosen) return;
  siteEl(id)?.classList.toggle("hot", on);
  locEl(id)?.classList.toggle("lit", on);
}
// The card for the chosen place. Its words come from the game (BOARD.cardFor), so they follow the step you're on.
function choose(id) {
  if (id && API.blocked) return;
  chosen = id;
  for (const p of [...PLACES, RACES]) {
    siteEl(p.id)?.classList.toggle("hot", p.id === id);
    locEl(p.id)?.classList.toggle("on", p.id === id);
  }
  leanTo(id); placeSound();
  if (!id) { card.hidden = true; API.onChoose && API.onChoose(null); return; }
  const p = placeOf(id), c = (API.cardFor && API.cardFor(id)) || { title: p.title, text: "" };
  $id("cardKicker").textContent = c.kicker || "";
  $id("cardKicker").hidden = !c.kicker;
  $id("cardTitle").textContent = c.title || p.title;
  $id("cardText").innerHTML = c.text || "";
  $id("cardStatus").className = "status " + (c.state || "");
  $id("cardStatus").textContent = c.status || "";
  $id("cardStatus").hidden = !c.status;
  const go = $id("cardGo");
  go.hidden = !c.cta; go.disabled = !!c.off;
  $id("cardCta").textContent = c.cta || "";
  $id("cardNote").innerHTML = c.note || "";
  $id("cardNote").hidden = !c.note;
  paintPic($id("cardPic"), p.pic);
  card.dataset.place = id;
  card.hidden = false;
  API.onChoose && API.onChoose(id);
}
// a window onto the board: the place as it is painted, used in the cards and the sheets' headers
function paintPic(el, pic, at = 0.5) {
  const w = el.clientWidth || 296, h = el.clientHeight || 170, k = w / pic[2];
  el.style.backgroundImage = `url(${BASE}newmarket-board.webp)`;
  el.style.backgroundSize = `${MW * k}px ${MH * k}px`;
  el.style.backgroundPosition = `${-(pic[0] * k - w * at)}px ${-(pic[1] * k - h / 2)}px`;
}
$id("races").addEventListener("click", () => choose(chosen === "races" ? null : "races"));
$id("cardClose").addEventListener("click", () => choose(null));
$id("cardGo").addEventListener("click", () => { const id = chosen; if (id && API.onEnter) API.onEnter(id); });
addEventListener("keydown", (e) => { if (e.key === "Escape" && !API.blocked && !API.covered) choose(null); });

// ---------------------------------------------------------------- what each place is doing in the game
// open, next (the step to take now: lit, beckoning, with a Next tag), done (a tick), locked (greyed, still clickable
// for its card, which says when it opens)
const STATES = ["st-open", "st-next", "st-done", "st-locked"];
function setStates(map) {
  for (const p of [...PLACES, RACES]) {
    const st = "st-" + (map[p.id] || "open");
    for (const el of [locEl(p.id), siteEl(p.id)]) if (el) { el.classList.remove(...STATES); el.classList.add(st); }
  }
  API.states = map;
}

// ---------------------------------------------------------------- fit the board to the window
const view = $id("view"), holder = $id("holder");
let scale = 1;
const fitHooks = [];
function fit() {
  const W = view.clientWidth, H = view.clientHeight;
  const portrait = W / H < 1.05;
  scale = portrait ? H / MH : Math.max(W / MW, H / MH);            // full bleed: the board always fills the window
  view.classList.toggle("pan", portrait);
  holder.style.width = MW * scale + "px"; holder.style.height = MH * scale + "px";
  holder.style.position = portrait ? "" : "absolute"; holder.style.margin = portrait ? "" : "0";
  holder.style.left = portrait ? "" : ((W - MW * scale) / 2).toFixed(1) + "px"; holder.style.top = portrait ? "" : ((H - MH * scale) / 2).toFixed(1) + "px";
  stage.style.transform = `scale(${scale})`;
  if (portrait && !API.panTo) view.scrollLeft = 990 * scale - W / 2;           // start on Tattersalls and the stables
  fitHooks.forEach((f) => f(scale));
  if (chosen) choose(chosen);
}
addEventListener("resize", fit);
// on a phone held upright the board is wider than the screen: slide it so a place is in view
function panTo(id) {
  const p = placeOf(id); if (!p || !view.classList.contains("pan")) return;
  const x = p.at[0] * scale - view.clientWidth / 2;
  view.scrollTo({ left: x, behavior: REDUCED ? "auto" : "smooth" });
}

// ---------------------------------------------------------------- the roads (the owner's route markup, kept to the roads)
const RB = [632, 294];                                             // the roundabout at the top of the High Street
const ROAD = {
  fordham: [[630, -14], [630, 60], [630, 140], [629, 210], [630, 262], RB],
  bury: [RB, [660, 280], [700, 250], [740, 222], [780, 198], [820, 172], [860, 152], [895, 132], [930, 108], [960, 84], [990, 58], [1016, 32], [1040, 6], [1052, -14]],
  oldStn: [RB, [662, 300], [699, 315], [740, 345], [775, 385], [820, 425], [878, 470], [930, 497], [988, 525], [1060, 568], [1148, 615], [1193, 632], [1234, 648], [1300, 676], [1370, 706], [1410, 722], [1466, 744]],
  kingston: [RB, [630, 340], [629, 380], [626, 420], [618, 460], [605, 495], [590, 530], [573, 556], [557, 590], [528, 630], [505, 675], [490, 708], [478, 740], [465, 775], [448, 800]],
  nmkt: [[448, 800], [441, 836], [424, 864], [408, 899], [390, 921], [349, 947], [300, 995], [281, 1011], [240, 1030], [187, 1044], [140, 1058], [96, 1072]],
  exeter: [[629, 236], [600, 236], [560, 238], [520, 242], [483, 250], [440, 262], [400, 272], [350, 282], [300, 290]],
  highSt: [RB, [612, 312], [580, 330], [545, 350], [510, 370], [475, 390], [440, 408], [400, 425]],
  station: [[400, 425], [370, 412], [332, 397], [290, 374], [250, 352]],
  shied: [[448, 800], [431, 794], [403, 780], [376, 752], [345, 708], [338, 690], [339, 672], [333, 629], [322, 607]],
  avenue: [[850, 446], [900, 425], [970, 402], [1080, 372], [1150, 357], [1220, 345], [1320, 321], [1420, 287], [1452, 276]],
};
const rev = (a) => a.slice().reverse();
const join = (...parts) => parts.reduce((acc, p) => acc.concat(acc.length ? p.slice(1) : p), []);
// points every `step` pixels along a polyline (street lamps)
function along(pts, step, from = 0) {
  const out = []; let need = from;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, ay] = pts[i], [bx, by] = pts[i + 1], L = Math.hypot(bx - ax, by - ay);
    while (need <= L) { const u = need / L; out.push([ax + (bx - ax) * u, ay + (by - ay) * u]); need += step; }
    need -= L;
  }
  return out;
}

// ---------------------------------------------------------------- the journeys between the steps, inked on the board
// From the place just finished to the next, along the roads. The ink draws itself, a little horse trots along it, and it
// stays faintly on the board while the next place waits.
const STUD_GATE = [[1344, 470], [1318, 548], [1270, 600], [1234, 648], [1193, 632], [1148, 615]];
// into Tattersalls by the lane off Old Station Road, past the yard on the rotunda's west side
const TATTS_GATE = [[988, 525], [960, 568], [935, 605], [905, 640], [903, 690], [946, 722]];
const STABLES_GATE = [[963, 880], [900, 858], [820, 838], [760, 790], [722, 721]];
const JC_GATE = [[660, 652], [626, 606], [590, 588], [573, 556]];
const PALACE_GATE = [[505, 675], [470, 662], [436, 650]];
const WARREN_GATE = [[322, 607], [304, 597], [241, 574], [191, 532], [165, 462]];
const TRAILS = {
  "jockey>stud": join(JC_GATE, rev(ROAD.kingston.slice(0, 8)), ROAD.oldStn.slice(1, 11), rev(STUD_GATE)),
  "stud>tatts": join(STUD_GATE, [[1148, 615], [1060, 568], [988, 525]], TATTS_GATE),
  "tatts>stables": [[946, 724], [905, 752], [880, 790], [900, 830], [945, 860], [963, 880]],
  "stables>warren": join(STABLES_GATE, [[722, 721], [659, 722], [636, 726], [616, 734], [598, 736], [583, 733], [531, 743], [496, 758], [468, 787], [448, 800]], ROAD.shied.slice(1), WARREN_GATE.slice(1)),
  "warren>jockey": join(rev(WARREN_GATE), rev(ROAD.shied), [[448, 800], [468, 787], [496, 758], [531, 743], [583, 733], [598, 736], [616, 734], [636, 726], [659, 722], [660, 690]]),
  "jockey>races": join(JC_GATE, rev(ROAD.kingston.slice(0, 8)), ROAD.oldStn.slice(1, 6), [[820, 425], [850, 446]], ROAD.avenue.slice(1, 7), [[1270, 333], [1290, 262]]),
  "races>palace": join([[1290, 262], [1270, 333]], rev(ROAD.avenue.slice(1, 7)), [[850, 446], [820, 425]], rev(ROAD.oldStn.slice(1, 6)), ROAD.kingston.slice(1, 11), PALACE_GATE.slice(1)),
  "stables>jockey": join(STABLES_GATE, [[722, 721], [690, 712], [660, 690]]),
  "tatts>warren": join(rev(TATTS_GATE), [[930, 497], [878, 470], [820, 425], [775, 385], [740, 345], [699, 315], [662, 300]], ROAD.highSt, ROAD.station.slice(1), [[215, 348], [190, 400], [165, 462]]),
  "palace>jockey": [[436, 650], [470, 662], [505, 675], [528, 630], [557, 590], [573, 556], [590, 588], [626, 606], [660, 652]],
};
const medalAt = (id) => { const p = placeOf(id); return id === "races" ? [p.at[0], p.at[1] + 30] : [p.at[0], p.at[1] - 30]; };
function routeFor(from, to) {
  const key = from + ">" + to, back = to + ">" + from;
  if (TRAILS[key]) return TRAILS[key];
  if (TRAILS[back]) return rev(TRAILS[back]);
  return [medalAt(from), medalAt(to)];
}
// The camera. The board always fills the window: it never pulls back past its edges. Picking a place glides the board
// a little towards it with the slightest zoom; moving on to the next place eases back to the whole board, glides in
// towards the next one and gives it a gentle pulse. (A transform on #lean, from its top left corner, clamped so the
// board's edge never shows. On a phone held upright the board slides sideways instead, with no zoom.)
let travelNow = null;
const ZOOM = 1.035;
function cameraFor(id) {
  const p = id && placeOf(id);
  if (!p || view.classList.contains("pan")) return "translate(0px, 0px) scale(1)";
  const W = view.clientWidth, H = view.clientHeight, bw = MW * scale, bh = MH * scale, hx = (W - bw) / 2, hy = (H - bh) / 2;
  const cardOpen = innerWidth > 760, tx = cardOpen ? 380 + (W - 380) / 2 : W / 2, ty = H * 0.5;
  const P = [p.at[0] * scale, p.at[1] * scale];
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  // half way between a gentle zoom about the middle and putting the place on the target, never letting the edge in
  const want = (tgt, h0, pp, size) => 0.5 * (tgt - h0 - ZOOM * pp) + 0.5 * (size / 2) * (1 - ZOOM);
  let x = want(tx, hx, P[0], bw), y = want(ty, hy, P[1], bh);
  x = clamp(x, W - hx - ZOOM * bw, -hx); y = clamp(y, H - hy - ZOOM * bh, -hy);
  return `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) scale(${ZOOM})`;
}
const CAM_REST = "translate(0px, 0px) scale(1)";
function clearTrail() { travelNow = null; }
function pulseAt(id) {
  for (const el of [locEl(id), siteEl(id)]) { if (!el) continue; el.classList.remove("pulse"); void el.getBoundingClientRect(); el.classList.add("pulse"); setTimeout(() => el.classList.remove("pulse"), 2600); }
}
function trail(from, to, { ms = 1600 } = {}) {
  const p = placeOf(to), run = travelNow = {};
  const wait = (t) => new Promise((r) => setTimeout(r, t));
  if (!p) return Promise.resolve();
  if (REDUCED || view.classList.contains("pan")) { panTo(to); pulseAt(to); return wait(REDUCED ? 500 : 900); }
  return (async () => {
    const half = Math.round(ms / 2);
    lean.style.transformOrigin = "0 0";
    lean.style.transition = `transform ${half}ms cubic-bezier(.45,0,.4,1)`;
    lean.style.transform = CAM_REST;                                         // back to the whole board
    await wait(half * 0.8); if (travelNow !== run) return;
    lean.style.transition = `transform ${half + 200}ms cubic-bezier(.3,0,.25,1)`;
    lean.style.transform = cameraFor(to);                                    // and gently towards the next place
    await wait(half * 0.6); if (travelNow !== run) return;
    pulseAt(to);
    await wait(half * 0.6);
  })();
}

// ---------------------------------------------------------------- the sky: cloud shadows over the board, wisps drifting along the top
const clouds = document.getElementById("clouds"), cx2 = clouds.getContext("2d");
const wisps = document.getElementById("wisps"), wx2 = wisps.getContext("2d");
const Q = 4;                                                       // both are drawn at a quarter size and stretched
const PUFFS = Array.from({ length: 5 }, (_, i) => ({ x: (i * 0.27 % 1) * 1800 - 180, y: 150 + (i * 0.61 % 1) * 850, r: 190 + (i * 0.37 % 1) * 200 }));
// Engraved clouds, after the owner's reference (a pen-and-ink engraving): white billows drawn back to front; outlines
// put down as two or three loose, slightly wandering strokes with gaps; dark crescents of close curved hatching in
// each billow's shaded side; a few flicks just outside the edge; an uneven, softly flattened underside with loose
// horizontal strokes. Drawn once each at three times the size, then slid across the top of the board.
const INK = "rgba(34,30,26,", PAPER = "#fffefa";
function cloudSprite(seed, w, h) {
  let s0 = (seed * 7919 + 104729) % 2147483647; const rnd = () => ((s0 = (s0 * 16807) % 2147483647) / 2147483647);
  const K = 3, pad = 10, c = document.createElement("canvas"); c.width = Math.round((w + pad * 2) * K); c.height = Math.round((h + pad * 2) * K);
  const g = c.getContext("2d"); g.scale(K, K); g.translate(pad, pad); g.lineCap = "round"; g.lineJoin = "round";
  const base = h - 7;
  // the cloud's height along its length: one or two heaps on a long low tail
  const heaps = [{ u: 0.4 + rnd() * 0.3, s: 0.13 + rnd() * 0.06, a: 1 }];
  if (rnd() < 0.8) heaps.push({ u: heaps[0].u + (rnd() < 0.5 ? -1 : 1) * (0.18 + rnd() * 0.1), s: 0.09 + rnd() * 0.05, a: 0.55 + rnd() * 0.25 });
  const tail = 0.3 + rnd() * 0.08;
  const prof = (u) => Math.max(tail * (1 - Math.pow(Math.abs(u - 0.5) * 2, 3) * 0.55), ...heaps.map((k) => k.a * Math.exp(-((u - k.u) ** 2) / (2 * k.s * k.s))));
  const P = [];
  const row = (layer, from, to, hgtK, rK, step, keep = () => true, rMin = 3) => {
    let u = from;
    while (u < to) {
      const hgt = prof(u) * h * hgtK * (0.9 + rnd() * 0.2), r = Math.max(rMin, hgt * rK * (0.75 + rnd() * 0.5));
      const yy = layer === 3 ? base - r * (0.62 + rnd() * 0.18) : base - hgt + r;
      if (keep(u)) P.push({ x: u * w, y: yy, r: layer === 3 ? r * (0.9 + 0.5 * prof(u)) : r, layer, shade: rnd() < 0.35 ? 1.6 : 0.7 + rnd() * 0.5 });
      u += (r * step * (0.85 + rnd() * 0.5)) / w;
    }
  };
  row(1, 0.03, 0.97, 0.98, 0.3, 1.05, () => true, h * 0.09);                   // the tops: lumpy, medium billows
  row(2, 0.08, 0.92, 0.66, 0.34, 1.25, (u) => prof(u) > 0.42, h * 0.1);         // nearer billows in the heaps
  row(2, 0.1, 0.9, 0.4, 0.42, 1.4, (u) => prof(u) > 0.55, h * 0.1);
  P.sort((a, b) => a.layer - b.layer || a.y - b.y);
  // the body behind the billows, down to the underside, so the lower edges of the billows don't show
  const tops = P.filter((p) => p.layer === 1).sort((a, b) => a.x - b.x);
  const body = new Path2D(); body.moveTo(tops[0].x, base); for (const p of tops) body.lineTo(p.x, p.y + p.r * 0.2); body.lineTo(tops[tops.length - 1].x, base); body.closePath();
  const drawn = [];
  const behind = (x, y) => g.isPointInPath(body, x * K + pad * K, y * K + pad * K) || drawn.some((q) => (x - q.x) ** 2 + (y - q.y) ** 2 < q.r * q.r);
  // a loose stroke along part of a circle: a few passes, each wandering a little, with its own start and end
  const sketch = (p, a0, a1, passes, alpha, width, keep) => {
    for (let k = 0; k < passes; k++) {
      const off = (rnd() - 0.4) * 0.9, wob = rnd() * 6.28, s = a0 + (rnd() - 0.5) * 0.15, e = a1 + (rnd() - 0.5) * 0.15;
      g.strokeStyle = INK + (alpha * (k ? 0.6 : 1)).toFixed(2) + ")"; g.lineWidth = width * (k ? 0.7 : 1);
      g.beginPath(); let on = false;
      for (let a = s; a <= e; a += 0.03) {
        const rr = p.r + off + Math.sin(a * 5 + wob) * 0.35, x = p.x + rr * Math.cos(a), y = p.y + rr * Math.sin(a);
        if (keep && !keep(x, y, a)) { on = false; continue; }
        if (rnd() < 0.012) { on = false; continue; }                           // the pen lifts now and then
        on ? g.lineTo(x, y) : g.moveTo(x, y); on = true;
      }
      g.stroke();
    }
  };
  const bottom = base;
  g.save(); g.beginPath(); g.rect(-pad, -pad, w + pad * 2, bottom + pad); g.clip();
  g.fillStyle = PAPER; g.fill(body);
  for (const p of P) {
    g.fillStyle = PAPER; g.beginPath(); g.arc(p.x, p.y, p.r, 0, 6.283); g.fill();
    // hatching: a crescent of close curved lines on the lower right, dark at the rim and thinning inwards
    g.save(); g.beginPath(); g.arc(p.x, p.y, p.r, 0, 6.283); g.clip();
    const n = p.layer === 3 ? 0 : Math.max(5, Math.round(p.r / 0.75 * p.shade)), aim = 0.45 + (rnd() - 0.5) * 0.6, deep = Math.min(0.75, 0.4 * p.shade);
    for (let j = 0; j < n; j++) {
      const t = j / n, rr = p.r * (0.99 - t * deep), span = (1 - t * 0.8) * (1.0 + rnd() * 0.4);
      const q = { x: p.x - p.r * 0.45 * t, y: p.y - p.r * 0.3 * t, r: rr };
      sketch(q, aim - span * 0.95, aim + span * 0.7, 1, 0.95 - t * 0.3, 0.4);
    }
    g.restore();
    // outline: against the sky all round; over the billows behind, only the upper left
    sketch(p, 0, 6.3, 2, 0.95, 0.55 + Math.min(0.2, p.r / 80), (x, y, a) => !behind(x, y) || (p.layer < 3 && ((a % 6.283) > Math.PI * 1.0) && ((a % 6.283) < Math.PI * 1.62)));
    // a couple of flicks just outside the edge, on the upper left of the bigger billows
    if (p.layer < 3 && p.r > 7 && rnd() < 0.7) { const a = Math.PI * (1.05 + rnd() * 0.5); sketch({ x: p.x, y: p.y, r: p.r + 2 + rnd() * 1.5 }, a, a + 0.25 + rnd() * 0.3, 1, 0.75, 0.45, (x, y) => !behind(x, y)); }
    drawn.push(p);
  }
  g.restore();
  // the underside: a soft scalloped edge in loose strokes, and wavy horizontal strokes beneath
  const xa = tops[0].x - tops[0].r * 0.6, xb = tops[tops.length - 1].x + tops[tops.length - 1].r * 0.6;
  const scal = []; for (let x = xa; x < xb;) { const L = h * (0.22 + rnd() * 0.22); scal.push([x, Math.min(xb, x + L), 1.2 + rnd() * 2.2]); x += L; }
  g.fillStyle = PAPER; g.beginPath(); g.moveTo(xa, base - 1);
  for (const [a, b, d] of scal) g.quadraticCurveTo((a + b) / 2, base + d * 2, b, base - 0.4);
  g.lineTo(xb, base - 6); g.lineTo(xa, base - 6); g.closePath(); g.fill();
  for (let pass = 0; pass < 2; pass++) {
    g.strokeStyle = INK + (pass ? 0.5 : 0.9) + ")"; g.lineWidth = pass ? 0.4 : 0.6;
    for (const [a, b, d] of scal) { if (rnd() < 0.12) continue; const o = pass ? 0.8 + rnd() * 0.8 : 0;
      g.beginPath(); g.moveTo(a + 1, base - 0.4 + o); g.quadraticCurveTo((a + b) / 2, base + d * 2 + o, b - 0.5, base - 0.4 + o); g.stroke(); }
  }
  for (let j = 0; j < 9; j++) {
    const a = xa + (xb - xa) * rnd() * 0.85, b = Math.min(xb, a + (xb - xa) * (0.05 + rnd() * 0.14)), y = base + 3.2 + rnd() * 3;
    g.strokeStyle = INK + (0.4 + rnd() * 0.35).toFixed(2) + ")"; g.lineWidth = 0.42;
    g.beginPath(); g.moveTo(a, y); for (let x = a; x <= b; x += 2) g.lineTo(x, y + Math.sin(x * 0.4 + j) * 0.35); g.stroke();
  }
  // hatching just above the underside, under the heaps
  for (let j = 0; j < 14; j++) {
    const a = xa + (xb - xa) * (0.15 + rnd() * 0.7), b = a + h * (0.15 + rnd() * 0.3), y = base - 1.5 - rnd() * 3.5;
    g.strokeStyle = INK + (0.35 + rnd() * 0.3).toFixed(2) + ")"; g.lineWidth = 0.4;
    g.beginPath(); g.moveTo(a, y); g.quadraticCurveTo((a + b) / 2, y + 1.2, b, y); g.stroke();
  }
  c.dw = w + pad * 2; c.dh = h + pad * 2;
  return c;
}
const BANKS = [
  { x: 30, y: 10, sprite: cloudSprite(3, 430, 104), speed: 6.5 }, { x: 610, y: 28, sprite: cloudSprite(7, 270, 70), speed: 9 },
  { x: 930, y: 8, sprite: cloudSprite(11, 470, 116), speed: 5.5 },
];
function drawSky(dt) {
  cx2.clearRect(0, 0, clouds.width, clouds.height); wx2.clearRect(0, 0, wisps.width, wisps.height);
  for (const c of PUFFS) {
    if (!REDUCED) { c.x += 6 * dt; c.y -= 1.6 * dt; }
    if (c.x - c.r > MW) { c.x = -c.r; c.y = 180 + Math.random() * 800; }
    for (const [ox, oy, f] of [[0, 0, 1], [c.r * .45, -c.r * .12, .7], [-c.r * .4, c.r * .1, .65]]) {
      const x = (c.x + ox) / Q, y = (c.y + oy) / Q, r = c.r * f / Q, g = cx2.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, "rgba(70,80,60,.15)"); g.addColorStop(1, "rgba(70,80,60,0)");
      cx2.fillStyle = g; cx2.beginPath(); cx2.ellipse(x, y, r * 1.3, r * .75, 0, 0, 6.283); cx2.fill();
    }
  }
  for (const b of BANKS) {
    const w = b.sprite.dw, h = b.sprite.dh;
    if (!REDUCED) b.x += b.speed * dt;
    if (b.x > MW + 20) b.x = -w - 20;
    wx2.drawImage(b.sprite, b.x * 2, b.y * 2, w * 2, h * 2);
    // its shadow on the ground, below and to the right
    const sx = (b.x + w * 0.5 + 70) / Q, sy = (b.y + h * 0.6 + 150) / Q, r = w * 0.42 / Q, sg = cx2.createRadialGradient(sx, sy, 0, sx, sy, r);
    sg.addColorStop(0, "rgba(60,70,50,.13)"); sg.addColorStop(1, "rgba(60,70,50,0)");
    cx2.fillStyle = sg; cx2.beginPath(); cx2.ellipse(sx, sy, r, r * 0.45, 0, 0, 6.283); cx2.fill();
  }
}

// ================================================================ the day, the weather and the sounds of the place
// ---------------------------------------------------------------- the day: one passes every five minutes
// Most of the cycle is daylight (5:30 to 21:30); the night goes by quickly. The board opens in the early morning,
// when the mist is lying on the heath and the strings are going out.
const DAY = 300;
let dayT = 0.04;
const hourAt = (t) => (t < 0.86 ? 5.5 + (t / 0.86) * 16 : 21.5 + ((t - 0.86) / 0.14) * 8) % 24;
const hourNow = () => hourAt(dayT);
const inHours = ([a, b]) => { const h = hourNow(); return h >= a && h < b; };
// the light through the day: [hour, the colour the board is multiplied by, warm light, lamps, mist, smoke]
const LIGHT = [
  [0, [70, 78, 128], 0, 1, 0.15, 0.5], [4.8, [70, 78, 128], 0, 1, 0.3, 0.5], [5.6, [168, 160, 196], 0.12, 0.7, 1, 0.9],
  [6.6, [236, 222, 210], 0.14, 0.1, 1, 1], [8, [255, 255, 255], 0.05, 0, 0.45, 0.8], [9.5, [255, 255, 255], 0, 0, 0, 0.55],
  [15, [255, 255, 255], 0.1, 0, 0, 0.5], [17.8, [255, 228, 196], 0.24, 0, 0, 0.7], [19.4, [214, 168, 162], 0.18, 0.45, 0.1, 0.9],
  [20.6, [110, 110, 160], 0.06, 0.95, 0.15, 0.8], [21.5, [70, 78, 128], 0, 1, 0.15, 0.6], [24, [70, 78, 128], 0, 1, 0.15, 0.5],
];
function lightAt(h) {
  let i = 0; while (i < LIGHT.length - 2 && LIGHT[i + 1][0] <= h) i++;
  const a = LIGHT[i], b = LIGHT[i + 1], u = (h - a[0]) / (b[0] - a[0] || 1), mix = (x, y) => x + (y - x) * u;
  return { rgb: a[1].map((v, k) => Math.round(mix(v, b[1][k]))), warm: mix(a[2], b[2]), lamps: mix(a[3], b[3]), mist: mix(a[4], b[4]), smoke: mix(a[5], b[5]) };
}
const shade = document.getElementById("shade"), warm = document.getElementById("warm");
const clockTime = document.getElementById("clockTime"), clockIcon = document.getElementById("clockIcon");
const DAYICON = { sunrise: `%%ICON:sunrise%%`, sun: `%%ICON:sun%%`, sunset: `%%ICON:sunset%%`, moon: `%%ICON:moon%%` };
let L = lightAt(hourNow()), lastIcon = "";
function stepDay(dt) {
  if (!REDUCED) dayT = (dayT + dt / DAY) % 1;
  const h = hourNow(); L = lightAt(h);
  const night = L.rgb[0] < 250;
  shade.hidden = !night; if (night) shade.style.background = `rgb(${L.rgb.join(",")})`;
  warm.style.opacity = L.warm.toFixed(3);
  wisps.style.filter = `brightness(${(0.45 + 0.55 * L.rgb[0] / 255).toFixed(3)})`;
  const hh = Math.floor(h), mm = Math.floor((h - hh) * 60 / 5) * 5;
  clockTime.textContent = `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
  const icon = h >= 5 && h < 7.5 ? "sunrise" : h >= 7.5 && h < 18 ? "sun" : h >= 18 && h < 21 ? "sunset" : "moon";
  if (icon !== lastIcon) { clockIcon.innerHTML = DAYICON[icon]; lastIcon = icon; }
}

// ---------------------------------------------------------------- mist lying on the heath and the paddocks at dawn
const mistC = document.getElementById("mist"), mx = mistC.getContext("2d");
const MIST = [];
const rngA = (() => { let s = 4242; return () => ((s = (s * 16807) % 2147483647) / 2147483647); })();
for (const [x0, y0, x1, y1, n] of [[0, 230, 400, 650, 26], [0, 80, 560, 250, 22], [660, 60, 1448, 560, 30], [560, 980, 1448, 1086, 12], [0, 650, 300, 1086, 12]])
  for (let i = 0; i < n; i++) MIST.push({ x: x0 + rngA() * (x1 - x0), y: y0 + rngA() * (y1 - y0), r: 50 + rngA() * 70, v: 2 + rngA() * 3, x0, x1 });
let mistShown = -1;
function drawMist(dt) {
  const k = L.mist;
  if (k < 0.02) { if (mistShown !== 0) { mx.clearRect(0, 0, mistC.width, mistC.height); mistShown = 0; } return; }
  mistShown = k; mx.clearRect(0, 0, mistC.width, mistC.height);
  for (const m of MIST) {
    if (!REDUCED) { m.x += m.v * dt; if (m.x - m.r > m.x1) m.x = m.x0 - m.r; }
    const x = m.x / Q, y = m.y / Q, r = m.r / Q, g = mx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(246,244,236,${(0.32 * k).toFixed(3)})`); g.addColorStop(1, "rgba(246,244,236,0)");
    mx.fillStyle = g; mx.beginPath(); mx.ellipse(x, y, r * 1.6, r * 0.55, 0, 0, 6.283); mx.fill();
  }
}

// ---------------------------------------------------------------- lamps: windows and the street lamps, lit at dusk
// (assets/atmos.json: tools/atmos.py found the windows on the board)
const lampC = document.getElementById("lamps"), lx = lampC.getContext("2d");
let LAMPS = [];
function setLamps(atmos) {
  const street = [];
  for (const r of [ROAD.highSt, ROAD.kingston, ROAD.oldStn.slice(0, 9), ROAD.bury.slice(0, 6), ROAD.exeter, ROAD.fordham.slice(2)])
    for (const [x, y] of along(r, 64, 30)) street.push({ x: x + 7, y: y - 5, r: 13, street: true });
  LAMPS = [...atmos.windows.filter(() => rngA() < 0.75).map(([x, y]) => ({ x, y, r: 9 })), ...street]
    .map((l) => ({ ...l, on: 0.05 + rngA() * 0.4, ph: rngA() * 6.28 }));
}
let lampsShown = -1;
function drawLamps(t) {
  const k = L.lamps;
  if (k < 0.02) { if (lampsShown !== 0) { lx.clearRect(0, 0, lampC.width, lampC.height); lampsShown = 0; } return; }
  lampsShown = k; lx.clearRect(0, 0, lampC.width, lampC.height);
  const s = lampC.width / MW;
  for (const l of LAMPS) {
    const lit = Math.min(1, Math.max(0, (k - l.on) * 3));          // each lamp comes on at its own moment
    if (lit <= 0) continue;
    const fl = 0.88 + 0.12 * Math.sin(t * 7 + l.ph) * Math.sin(t * 3.1 + l.ph * 2), a = lit * fl;
    const x = l.x * s, y = l.y * s, r = l.r * s, g = lx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, `rgba(255,214,140,${(0.95 * a).toFixed(3)})`); g.addColorStop(0.25, `rgba(255,170,80,${(0.5 * a).toFixed(3)})`); g.addColorStop(1, "rgba(255,140,50,0)");
    lx.fillStyle = g; lx.beginPath(); lx.arc(x, y, r, 0, 6.283); lx.fill();
  }
}

// ---------------------------------------------------------------- chimney smoke, rooks and flags (one canvas over the board)
const fxC = document.getElementById("smoke"), fx = fxC.getContext("2d");
const puff = (() => { const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
  const r = g.createRadialGradient(32, 32, 0, 32, 32, 32); r.addColorStop(0, "rgba(150,152,160,1)"); r.addColorStop(0.45, "rgba(172,174,182,.7)"); r.addColorStop(1, "rgba(195,196,202,0)");
  g.fillStyle = r; g.fillRect(0, 0, 64, 64); return c; })();
let CHIMNEYS = [], FLAGS = [];
const PUFFS2 = [];
const WIND = 3.2;                                                    // the same way the clouds drift
function stepSmoke(dt) {
  for (const c of CHIMNEYS) {
    c.next -= dt * (0.4 + 0.6 * L.smoke);
    if (c.next <= 0) { c.next = 0.32 + rngA() * 0.3; PUFFS2.push({ x: c.x + (rngA() - 0.5), y: c.y, age: 0, life: 6.5 + rngA() * 3, vx: WIND * (0.5 + rngA() * 0.6), vy: -(11 + rngA() * 4), a: c.a }); }
  }
  for (let i = PUFFS2.length - 1; i >= 0; i--) {
    const p = PUFFS2[i]; p.age += dt; if (p.age > p.life) { PUFFS2.splice(i, 1); continue; }
    p.x += p.vx * dt; p.y += p.vy * dt; p.vy *= 1 - 0.22 * dt; p.vx += 1.1 * dt;
  }
}
// rooks: now and then a flock rises off Warren Hill, wheels and heads away over the town
const ROOKS = Array.from({ length: 11 }, (_, i) => ({ ox: (rngA() - 0.5) * 70, oy: (rngA() - 0.5) * 34, ph: rngA() * 6.28, sp: 0.6 + rngA() * 0.8 }));
let flock = { t: -12, dur: 30 };
function flockAt(s) { return { x: 120 + s * 1000 + Math.sin(s * 9) * 60, y: 420 - s * 470 + Math.cos(s * 7) * 50 }; }
function drawFx(t, dt) {
  const s = fxC.width / MW;
  fx.clearRect(0, 0, fxC.width, fxC.height);
  // smoke
  for (const p of PUFFS2) {
    const u = p.age / p.life, a = Math.min(1, 1.0 * p.a * Math.min(1, p.age / 0.4) * Math.pow(1 - u, 1.4)), r = (2.6 + u * 17) * s;
    fx.globalAlpha = a; fx.drawImage(puff, p.x * s - r, p.y * s - r, r * 2, r * 2);
  }
  fx.globalAlpha = 1;
  // flags on the rotunda and the Jockey Club
  for (const f of FLAGS) {
    const x = f.x * s, y = f.y * s, L2 = f.len * s;
    fx.strokeStyle = "#3a3026"; fx.lineWidth = 1.5 * s; fx.beginPath(); fx.moveTo(x, y); fx.lineTo(x, y - L2); fx.stroke();
    fx.fillStyle = f.col; fx.beginPath();
    const N = 10, fl = 15 * s, fh = 7 * s;
    for (let i = 0; i <= N; i++) { const u = i / N; fx.lineTo(x + u * fl, y - L2 + Math.sin(u * 3.2 - t * 6 + f.ph) * 2 * s * u + u * fh * 0.15); }
    for (let i = N; i >= 0; i--) { const u = i / N; fx.lineTo(x + u * fl, y - L2 + fh * (1 - u * 0.75) + Math.sin(u * 3.2 - t * 6 + f.ph) * 2 * s * u); }
    fx.closePath(); fx.fill();
  }
  // rooks, by day
  if (!REDUCED) flock.t += dt;
  const day = inHours([6, 19.5]);
  if (flock.t > flock.dur) flock = { t: -(25 + rngA() * 30), dur: 26 + rngA() * 8 };
  if (flock.t > 0 && day) {
    const c = flockAt(flock.t / flock.dur);
    fx.strokeStyle = "#26221d"; fx.lineWidth = 1.3 * s; fx.lineCap = "round";
    for (const b of ROOKS) {
      const sw = Math.sin(t * 0.7 * b.sp + b.ph), x = (c.x + b.ox + sw * 14) * s, y = (c.y + b.oy + Math.cos(t * 0.9 * b.sp + b.ph) * 8) * s;
      const w = 4.2 * s, flap = Math.sin(t * 11 * b.sp + b.ph) * 2.6 * s;
      fx.beginPath(); fx.moveTo(x - w, y - flap); fx.quadraticCurveTo(x - w * 0.4, y - flap * 0.2 - 0.6 * s, x, y); fx.quadraticCurveTo(x + w * 0.4, y - flap * 0.2 - 0.6 * s, x + w, y - flap); fx.stroke();
    }
    if (Sound.on && flock.t < dt * 1.5) Sound.caws();
  }
  // all of it takes the light of the hour
  if (L.rgb[0] < 250) { fx.globalCompositeOperation = "source-atop"; fx.fillStyle = `rgba(${L.rgb.join(",")},0.75)`; fx.fillRect(0, 0, fxC.width, fxC.height); fx.globalCompositeOperation = "source-over"; }
}
fetch(BASE + "atmos.json").then((r) => r.json()).then((a) => {
  CHIMNEYS = a.chimneys.map(([x, y]) => ({ x, y, next: rngA() * 3, a: 0.6 + rngA() * 0.4 }));
  FLAGS = a.flags.map(([x, y, len], i) => ({ x, y, len, col: i ? "#3d7153" : "#9c3d33", ph: i * 1.7 }));
  setLamps(a);
  for (let i = 0; i < 40; i++) stepSmoke(0.25);                   // the fires were lit before the page opened
}).catch(() => {});

// ---------------------------------------------------------------- leaning in towards the place you pick
const lean = $id("lean");
function leanTo(id) {
  const p = id && placeOf(id);
  if (p && !API.covered) panTo(id);                                // a phone slides the board to the place
  lean.style.transformOrigin = "0 0";
  if (API.covered) return;
  lean.style.transform = p && !REDUCED ? cameraFor(id) : CAM_REST;
}

// ---------------------------------------------------------------- sounds: each place has its own, heard while the pointer is over it
// Everything is made in the browser (no recordings); the auctioneer is the browser's own speaking voice.
const Sound = (() => {
  let ac = null, out = null, noiseBuf = null, bed = null, scene = null, sceneId = null;
  const S = { on: false };
  const now = () => ac.currentTime;
  function init() {
    ac = new (window.AudioContext || window.webkitAudioContext)();
    const comp = ac.createDynamicsCompressor(); comp.threshold.value = -18; comp.ratio.value = 3; comp.connect(ac.destination);
    out = ac.createGain(); out.gain.value = 0.8; out.connect(comp);
    noiseBuf = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate); const d = noiseBuf.getChannelData(0);
    let b = 0; for (let i = 0; i < d.length; i++) { const w = Math.random() * 2 - 1; b = 0.97 * b + 0.03 * w; d[i] = w * 0.6 + b * 2.2; }
  }
  const gainAt = (dest, v = 1) => { const g = ac.createGain(); g.gain.value = v; g.connect(dest); return g; };
  const panAt = (dest, p = 0) => { if (!ac.createStereoPanner) return dest; const n = ac.createStereoPanner(); n.pan.value = p; n.connect(dest); return n; };
  const noise = (dest, t, dur) => { const s = ac.createBufferSource(); s.buffer = noiseBuf; s.loop = true; s.connect(dest); s.start(t, Math.random() * 1.5); if (dur) s.stop(t + dur); return s; };
  const filt = (dest, type, f, q = 1) => { const n = ac.createBiquadFilter(); n.type = type; n.frequency.value = f; n.Q.value = q; n.connect(dest); return n; };
  const env = (g, t, a, peak, d, hold = 0) => { peak = Math.max(peak, 0.0002); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + a); g.gain.setValueAtTime(peak, t + a + hold); g.gain.exponentialRampToValueAtTime(0.0001, t + a + hold + d); };
  const tone = (dest, t, type, f, a, peak, d, f2) => { const o = ac.createOscillator(); o.type = type; o.frequency.setValueAtTime(f, t); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t + a + d); const g = gainAt(dest, 0); env(g, t, a, peak, d); o.connect(g); o.start(t); o.stop(t + a + d + 0.05); return o; };
  // the sounds
  const thud = (dest, t, v = 0.5, p = 0) => { const d = panAt(dest, p); tone(d, t, "sine", 95 + Math.random() * 20, 0.004, v, 0.09, 55); const g = gainAt(d, 0); env(g, t, 0.002, v * 0.5, 0.06); noise(filt(g, "lowpass", 600), t, 0.1); };
  const clip = (dest, t, v = 0.3, p = 0) => { const g = gainAt(panAt(dest, p), 0); env(g, t, 0.001, v, 0.05); noise(filt(g, "bandpass", 1800 + Math.random() * 900, 4), t, 0.08); };
  const gallop = (dest, t, dur, horses = 3, dir = 1) => {
    for (let hI = 0; hI < horses; hI++) {
      const off = hI * 0.17 + Math.random() * 0.05, stride = 0.42 + Math.random() * 0.03;
      for (let s = 0; s < dur / stride; s++) {
        const u = s * stride / dur, vol = Math.sin(Math.PI * u) ** 1.5 * 0.45, pan = dir * (u * 1.6 - 0.8);
        for (const b of [0, 0.065, 0.13, 0.2]) thud(dest, t + off + s * stride + b, vol * (0.7 + Math.random() * 0.3), pan);
      }
    }
  };
  const whinny = (dest, t, base = 640, dur = 1.25, v = 0.16) => {
    const o = ac.createOscillator(); o.type = "sawtooth";
    o.frequency.setValueAtTime(base * 1.2, t); o.frequency.linearRampToValueAtTime(base * 1.55, t + dur * 0.18); o.frequency.exponentialRampToValueAtTime(base * 0.62, t + dur);
    const vib = ac.createOscillator(); vib.frequency.value = 17; const vg = ac.createGain(); vg.gain.value = base * 0.09; vib.connect(vg); vg.connect(o.frequency);
    const trem = ac.createOscillator(); trem.frequency.value = 21; const tg = ac.createGain(); tg.gain.value = 0.35;
    const g = gainAt(filt(filt(dest, "bandpass", base * 2.2, 0.9), "lowpass", 3200), 0); env(g, t, 0.06, v, dur * 0.85, 0.05);
    const am = gainAt(g, 0.65); trem.connect(tg); tg.connect(am.gain); o.connect(am);
    [o, vib, trem].forEach((n) => { n.start(t); n.stop(t + dur + 0.2); });
    const br = gainAt(dest, 0); env(br, t + dur * 0.7, 0.05, v * 0.4, 0.35); noise(filt(br, "bandpass", 900, 0.8), t + dur * 0.7, 0.45);
  };
  const snort = (dest, t) => { const g = gainAt(dest, 0); env(g, t, 0.01, 0.25, 0.25); noise(filt(g, "lowpass", 900), t, 0.3); };
  const scrape = (dest, t) => {
    const g = gainAt(dest, 0); env(g, t, 0.05, 0.22, 0.32); const f = filt(g, "bandpass", 1600, 2.5); f.frequency.setValueAtTime(1500, t); f.frequency.linearRampToValueAtTime(3200, t + 0.35); noise(f, t, 0.45);
    const g2 = gainAt(dest, 0); env(g2, t + 0.55, 0.01, 0.3, 0.18); noise(filt(g2, "lowpass", 700), t + 0.55, 0.25);
  };
  const clank = (dest, t, v = 0.12) => { for (const [f, d] of [[523, 0.9], [1290, 0.6], [2010, 0.45], [2950, 0.3]]) tone(dest, t, "sine", f * (0.98 + Math.random() * 0.04), 0.002, v, d); clip(dest, t, 0.25); };
  const bell = (dest, t, f, v = 0.2) => { for (const [k, d, a] of [[0.5, 4, 0.6], [1, 3.2, 1], [1.2, 2.2, 0.5], [1.5, 2, 0.45], [2, 1.6, 0.35], [2.76, 1.1, 0.25], [3.05, 0.9, 0.2]]) tone(dest, t, "sine", f * k, 0.004, v * a, d); };
  const ping = (dest, t) => { tone(dest, t, "sine", 2400 + Math.random() * 600, 0.002, 0.06, 0.5); tone(dest, t, "sine", 3700 + Math.random() * 500, 0.002, 0.03, 0.3); };
  const tick = (dest, t) => clip(dest, t, 0.07, 0);
  const gavel = (dest, t) => { tone(dest, t, "sine", 150, 0.002, 0.6, 0.18, 90); const g = gainAt(dest, 0); env(g, t, 0.001, 0.5, 0.05); noise(filt(g, "bandpass", 1200, 1.5), t, 0.08); };
  const chirp = (dest, t, p = 0) => { const d = panAt(dest, p); const n = 2 + Math.floor(Math.random() * 4), f = 2800 + Math.random() * 1600;
    for (let i = 0; i < n; i++) tone(d, t + i * (0.09 + Math.random() * 0.05), "sine", f * (0.9 + Math.random() * 0.3), 0.01, 0.035, 0.07, f * (1.1 + Math.random() * 0.4)); };
  const caw = (dest, t, p = 0) => { const d = filt(panAt(dest, p), "bandpass", 1000, 1.4); tone(d, t, "sawtooth", 420 + Math.random() * 60, 0.02, 0.05, 0.22, 330); };
  const owl = (dest, t) => { tone(dest, t, "sine", 400, 0.06, 0.05, 0.45, 370); tone(dest, t + 0.75, "sine", 410, 0.05, 0.04, 0.25, 395); tone(dest, t + 1.1, "sine", 400, 0.06, 0.05, 0.7, 360); };
  const horn = (dest, t) => { const f = filt(dest, "lowpass", 1800, 0.7); [[392, 0.18], [523, 0.18], [659, 0.18], [784, 0.4], [659, 0.16], [784, 0.7]].reduce((tt, [n, d]) => { tone(f, tt, "sawtooth", n, 0.02, 0.07, d); return tt + d + 0.03; }, t); };
  // a continuous murmur (a crowd, a room) or breeze; returns a stopper
  function murmur(dest, level, bands = [350, 700, 1150]) {
    const nodes = [];
    for (const b of bands) {
      const g = gainAt(dest, level * 0.5), lfo = ac.createOscillator(), lg = ac.createGain();
      lfo.frequency.value = 0.25 + Math.random() * 0.6; lg.gain.value = level * 0.4; lfo.connect(lg); lg.connect(g.gain); lfo.start();
      nodes.push(lfo, noise(filt(g, "bandpass", b, 1.6), now()));
    }
    return () => nodes.forEach((n) => { try { n.stop(); } catch (e) {} });
  }
  function breeze(dest, level) {
    const g = gainAt(dest, level), lfo = ac.createOscillator(), lg = ac.createGain(); lfo.frequency.value = 0.07; lg.gain.value = level * 0.6; lfo.connect(lg); lg.connect(g.gain); lfo.start();
    const n = noise(filt(g, "lowpass", 420, 0.5), now()); return () => { lfo.stop(); n.stop(); };
  }
  // the auctioneer, in the browser's own voice
  let voice = null;
  function speak(text, rate = 1.3) {
    if (!("speechSynthesis" in window)) return;
    try {
      if (!voice) { const vs = speechSynthesis.getVoices(); voice = vs.find((v) => /en-GB/i.test(v.lang) && /male|daniel|arthur|george/i.test(v.name)) || vs.find((v) => /en-GB/i.test(v.lang)) || vs.find((v) => /^en/i.test(v.lang)) || null; }
      const u = new SpeechSynthesisUtterance(text); if (voice) u.voice = voice; u.rate = rate; u.pitch = 0.85; u.volume = 0.5; speechSynthesis.speak(u);
    } catch (e) {}
  }
  const LOTS = ["Lot forty-two. A bay colt, out of a winning mare.", "Lot fifty-seven. A strong chestnut filly.", "Lot sixty-three. A good-looking grey colt.", "Lot seventy-one. A dark bay filly, a full sister to a winner."];
  // a soundscape: a fading-in bus, a few continuous layers and events scheduled a little ahead; stop() fades it all out
  function runScene(id) {
    const bus = gainAt(out, 0); bus.gain.setValueAtTime(0.0001, now()); bus.gain.exponentialRampToValueAtTime(1, now() + 0.8);
    const stops = [], timers = [];
    const every = (min, max, fn, first = 0) => { const go = () => { if (!S.on) return; fn(now() + 0.05); timers.push(setTimeout(go, (min + Math.random() * (max - min)) * 1000)); }; timers.push(setTimeout(go, first * 1000)); };
    if (id === "tatts-ring") {
      stops.push(murmur(bus, 0.12));
      every(3, 6, (t) => { const p = Math.random() - 0.5; for (let i = 0; i < 4; i++) clip(bus, t + i * 0.32, 0.12, p); });
      every(10, 16, (t) => whinny(bus, t, 600, 1.1, 0.06), 6);
    } else if (id === "tatts") {
      stops.push(murmur(bus, 0.18));
      let lot = 0;
      every(17, 20, (t) => {
        const name = LOTS[lot++ % LOTS.length], price = [40, 55, 70, 85][lot % 4];
        speak(`${name} Who'll start me? ${price} thousand. ${price + 5}. ${price + 10} thousand I'm bid. At the back, ${price + 15}. All done? ${price + 15} thousand guineas.`);
        timers.push(setTimeout(() => S.on && gavel(bus, now() + 0.02), 12500));
      }, 0.4);
      every(2.5, 5, (t) => { const p = Math.random() - 0.5; for (let i = 0; i < 4; i++) clip(bus, t + i * 0.32, 0.16, p); });
      every(9, 15, (t) => whinny(bus, t, 600, 1.1, 0.08), 6);
    } else if (id === "warren") {
      stops.push(breeze(bus, 0.12));
      let dir = 1; every(6.5, 8.5, (t) => { gallop(bus, t, 5.5, 3, dir); dir = -dir; });
      every(4, 9, (t) => snort(bus, t), 3); every(3, 7, (t) => chirp(bus, t, Math.random() * 1.6 - 0.8), 1);
    } else if (id === "stables") {
      stops.push(murmur(bus, 0.04, [600]));
      every(1.6, 2.6, (t) => scrape(bus, t), 0.2);
      every(5, 9, (t) => clank(bus, t), 2.5);
      every(2.5, 5, (t) => { const p = Math.random() - 0.5; clip(bus, t, 0.2, p); clip(bus, t + 0.25, 0.18, p); }, 1);
      every(7, 12, (t) => whinny(bus, t, 620, 1.2, 0.1), 4); every(5, 9, (t) => snort(bus, t), 3);
    } else if (id === "stud") {
      stops.push(breeze(bus, 0.12));
      every(4, 7, (t) => whinny(bus, t, 980, 0.85, 0.09), 0.6);
      every(8, 13, (t) => whinny(bus, t, 420, 0.7, 0.07), 3);
      every(1.5, 4, (t) => chirp(bus, t, Math.random() * 1.6 - 0.8));
      every(6, 10, (t) => { for (let i = 0; i < 8; i++) thud(bus, t + i * 0.26 + (i % 2) * 0.05, 0.12, 0.3); }, 5);
    } else if (id === "palace") {
      stops.push(murmur(bus, 0.035, [500]));
      every(16, 16, (t) => { [659, 523, 587, 392].forEach((f, i) => bell(bus, t + i * 0.9, f, 0.12)); }, 0.3);
      every(1, 1, (t) => tick(bus, t), 0.5);
    } else if (id === "jockey") {
      stops.push(murmur(bus, 0.09, [300, 550, 900]));
      every(2, 5, (t) => ping(bus, t), 1); every(1, 1, (t) => tick(bus, t), 0.2);
    } else if (id === "races") {
      const g = gainAt(bus, 0); g.gain.setValueAtTime(0.0001, now()); g.gain.exponentialRampToValueAtTime(1, now() + 3);
      stops.push(murmur(g, 0.3, [400, 800, 1300, 2000]));
      every(12, 12, (t) => horn(bus, t), 0.5);
      every(9, 12, (t) => gallop(bus, t, 4, 6, 1), 4);
    }
    return { stop() {
      timers.forEach(clearTimeout); try { speechSynthesis.cancel(); } catch (e) {}
      bus.gain.cancelScheduledValues(now()); bus.gain.setValueAtTime(bus.gain.value, now()); bus.gain.exponentialRampToValueAtTime(0.0001, now() + 0.7);
      setTimeout(() => { stops.forEach((f) => f()); bus.disconnect(); }, 900);
    } };
  }
  // always there while sound is on: the breeze, birds by day, an owl at night
  function runBed() {
    const bus = gainAt(out, 0.7), stop = breeze(bus, 0.06), timers = [];
    const loop = () => { if (!S.on) return; const h = hourNow(), t = now() + 0.05;
      if (h > 4.8 && h < 20) chirp(bus, t, Math.random() * 1.8 - 0.9); else if (Math.random() < 0.35) owl(bus, t);
      timers.push(setTimeout(loop, (3 + Math.random() * 6) * 1000)); };
    loop();
    return { stop() { timers.forEach(clearTimeout); stop(); bus.disconnect(); } };
  }
  S.set = (on) => {
    S.on = on;
    if (on) { if (!ac) init(); ac.resume(); bed = runBed(); const id = sceneId; sceneId = null; S.place(id); }
    else { if (scene) scene.stop(); if (bed) bed.stop(); scene = bed = null; try { speechSynthesis.cancel(); } catch (e) {} setTimeout(() => ac && !S.on && ac.suspend(), 1000); }
  };
  S.place = (id) => {
    if (id === sceneId && scene) return;
    sceneId = id;
    if (!S.on) return;
    if (scene) { scene.stop(); scene = null; }
    if (id) scene = runScene(id);
  };
  S.caws = () => { if (!ac || !S.on) return; for (let i = 0; i < 4; i++) caw(out, now() + 0.3 + i * (0.35 + Math.random() * 0.5), Math.random() * 1.4 - 0.7); };
  // the game's own moments
  S.gavel = () => { if (ac && S.on) gavel(out, now() + 0.02); };
  S.hooves = (n = 4) => { if (ac && S.on) gallop(out, now() + 0.05, 3.5, n, 1); };
  S.horn = () => { if (ac && S.on) horn(out, now() + 0.05); };
  S.whinny = () => { if (ac && S.on) whinny(out, now() + 0.05, 640, 1.2, 0.12); };
  S.chime = () => { if (ac && S.on) [784, 659, 988].forEach((f, i) => bell(out, now() + 0.05 + i * 0.32, f, 0.09)); };
  S.cheer = (secs = 4) => {
    if (!ac || !S.on) return;
    const g = gainAt(out, 0); g.gain.setValueAtTime(0.0001, now()); g.gain.exponentialRampToValueAtTime(1, now() + 0.6);
    g.gain.setValueAtTime(1, now() + secs - 1.2); g.gain.exponentialRampToValueAtTime(0.0001, now() + secs);
    const stop = murmur(g, 0.5, [500, 900, 1500, 2300]); setTimeout(() => { stop(); g.disconnect(); }, secs * 1000 + 200);
  };
  return S;
})();
// sound follows the place you're in (an open sheet), else the one under the pointer, else the one chosen
let inPlace = null;
const placeSound = () => Sound.place(inPlace || hovered || chosen);

// ---------------------------------------------------------------- the banner avenue: silks flown along the road to the races
// assets/banners.json (tools/banners.py): banners on the north verge of the road above the National Stud, which runs
// off the board towards To the Races. Each flag is the silks' body colours and pattern laid flat, drawn like the
// owner's reference (ink outline, a ragged fly, three tabs on the pole, a white pole with a spear tip).
const BAN = { x: 870, y: 236, w: 500, h: 200, k: 2 };                 // the canvas covers this part of the board
const banC = document.getElementById("banners"), bx = banC.getContext("2d");
banC.width = BAN.w * BAN.k; banC.height = BAN.h * BAN.k;
Object.assign(banC.style, { left: BAN.x + "px", top: BAN.y + "px", width: BAN.w + "px", height: BAN.h + "px" });
const AVENUE = ["aga-khan", "cheveley-park", "qatar", "alcohol-free", "liberty-lane", "circus-maximus", "ballydoyle-orange", "judmonte", "black-white", "shadwell", "desert-crown", "night-of-thunder"];
let BANNERS = [], banPole = 36, banW = 22;
const INKB = "#2a2520";
function silkFlag(def, palette, W, H, seed) {
  let s0 = seed * 9973 + 7; const r = () => ((s0 = (s0 * 16807) % 2147483647) / 2147483647);
  const K = 4, m = 3, c = document.createElement("canvas"); c.width = (W + m * 2) * K; c.height = (H + m * 2) * K;
  const g = c.getContext("2d"); g.scale(K, K); g.translate(m, m); g.lineJoin = "round"; g.lineCap = "round";
  const soft = (name) => { const h = palette[name] || "#888888", n = parseInt(h.slice(1), 16), base = [232, 220, 186];
    let v = [n >> 16, (n >> 8) & 255, n & 255]; const grey = (v[0] + v[1] + v[2]) / 3;
    v = v.map((x, i) => Math.round((x * 0.86 + grey * 0.14) * 0.86 + base[i] * 0.12));     // a touch less saturated, warmed towards the board's paper
    return `rgb(${v.join(",")})`; };
  const c1 = soft(def.body.colour), c2 = soft(def.body.colour2 || def.body.colour);
  // the cloth: wavering top and bottom edges, a ragged fly
  const pts = [];
  for (let i = 0; i <= 6; i++) pts.push([W * i / 6, (r() - 0.5) * 0.5]);
  for (let i = 1; i <= 7; i++) pts.push([W - (i % 2 ? 0.2 + r() * 0.5 : r() * 0.2), H * i / 8]);
  pts.push([W, H]);
  for (let i = 6; i >= 0; i--) pts.push([W * i / 6, H + (r() - 0.5) * 0.5]);
  const cloth = new Path2D(); pts.forEach(([x, y], i) => (i ? cloth.lineTo(x, y) : cloth.moveTo(x, y))); cloth.closePath();
  g.save(); g.clip(cloth);
  g.fillStyle = c1; g.fillRect(-1, -1, W + 2, H + 2);
  g.fillStyle = c2; g.strokeStyle = c2;
  switch (def.body.pattern) {
    case "hooped band": g.fillRect(-1, H * 0.36, W + 2, H * 0.28); break;
    case "hoops": for (let i = 1; i < 5; i += 2) g.fillRect(-1, i * H / 5, W + 2, H / 5); break;
    case "epaulets": g.fillRect(-1, -1, W + 2, H * 0.27); break;
    case "chevron": g.lineWidth = H * 0.22; g.beginPath(); g.moveTo(-1, H * 0.05); g.lineTo(W / 2, H * 0.72); g.lineTo(W + 1, H * 0.05); g.stroke(); break;
    case "sash": g.lineWidth = H * 0.26; g.beginPath(); g.moveTo(-1, -1); g.lineTo(W + 1, H + 1); g.stroke(); break;
    case "crossbelts": g.lineWidth = H * 0.2; g.beginPath(); g.moveTo(-1, -1); g.lineTo(W + 1, H + 1); g.moveTo(-1, H + 1); g.lineTo(W + 1, -1); g.stroke(); break;
    case "three spots": for (const [x, y] of [[0.28, 0.3], [0.72, 0.3], [0.5, 0.72]]) { g.beginPath(); g.arc(W * x, H * y, H * 0.16, 0, 6.283); g.fill(); } break;
    case "disc": g.beginPath(); g.arc(W / 2, H / 2, H * 0.3, 0, 6.283); g.fill(); break;
    case "diamond": g.beginPath(); g.moveTo(W / 2, H * 0.12); g.lineTo(W * 0.78, H / 2); g.lineTo(W / 2, H * 0.88); g.lineTo(W * 0.22, H / 2); g.closePath(); g.fill(); break;
    case "seams": g.lineWidth = 0.9; g.beginPath(); g.moveTo(W / 3, -1); g.lineTo(W / 3, H + 1); g.moveTo(W * 2 / 3, -1); g.lineTo(W * 2 / 3, H + 1); g.stroke(); break;
  }
  // painted cloth: a few soft vertical folds, light from the upper left, darker edges and the board's grain
  for (let i = 0; i < 4; i++) {
    const x = W * (0.15 + i * 0.24 + (r() - 0.5) * 0.08), w = W * (0.08 + r() * 0.08), gr = g.createLinearGradient(x - w, 0, x + w, 0);
    gr.addColorStop(0, "rgba(40,28,14,0)"); gr.addColorStop(0.5, `rgba(40,28,14,${(0.1 + r() * 0.08).toFixed(2)})`); gr.addColorStop(1, "rgba(40,28,14,0)");
    g.fillStyle = gr; g.fillRect(x - w, -1, w * 2, H + 2);
    const hl = g.createLinearGradient(x - w * 2, 0, x - w * 0.6, 0);
    hl.addColorStop(0, "rgba(255,248,226,0)"); hl.addColorStop(0.6, "rgba(255,248,226,.14)"); hl.addColorStop(1, "rgba(255,248,226,0)");
    g.fillStyle = hl; g.fillRect(x - w * 2, -1, w * 1.4, H + 2);
  }
  const lit = g.createLinearGradient(0, 0, W * 0.4, H); lit.addColorStop(0, "rgba(255,246,220,.16)"); lit.addColorStop(1, "rgba(255,246,220,0)");
  g.fillStyle = lit; g.fillRect(-1, -1, W + 2, H + 2);
  const dk = g.createLinearGradient(0, H * 0.55, 0, H); dk.addColorStop(0, "rgba(40,26,12,0)"); dk.addColorStop(1, "rgba(40,26,12,.18)");
  g.fillStyle = dk; g.fillRect(-1, -1, W + 2, H + 2);
  for (let i = 0; i < W * H * 1.4; i++) {
    g.fillStyle = r() < 0.5 ? `rgba(30,20,10,${(r() * 0.12).toFixed(3)})` : `rgba(255,248,230,${(r() * 0.1).toFixed(3)})`;
    g.fillRect(r() * W, r() * H, 0.35 + r() * 0.5, 0.25 + r() * 0.3);
  }
  g.restore();
  g.save(); g.clip(cloth); g.strokeStyle = "rgba(40,26,12,.28)"; g.lineWidth = 0.9; g.stroke(cloth); g.restore();
  // the sleeve the cloth is sewn into, round the pole
  g.fillStyle = c1; g.fillRect(-0.9, -0.2, 1.6, H + 0.2); g.fillStyle = "rgba(40,26,12,.25)"; g.fillRect(-0.9, -0.2, 1.6, H + 0.2);
  c.m = m; c.K = K; c.W = W; c.H = H;
  return c;
}
let racesHot = 0;
function drawBanners(t, dt) {
  if (!BANNERS.length) return;
  const want = hovered === "races" || chosen === "races" ? 1 : 0; racesHot += (want - racesHot) * Math.min(1, dt * 3);
  const k = BAN.k; bx.setTransform(1, 0, 0, 1, 0, 0); bx.clearRect(0, 0, banC.width, banC.height);
  bx.setTransform(k, 0, 0, k, -BAN.x * k, -BAN.y * k); bx.lineJoin = "round";
  const amp = 1.1 + racesHot * 1.3, speed = 4.2 + racesHot * 3.5;
  for (const b of BANNERS) {
    const top = b.y - banPole;
    // the shadow of pole and flag, thrown down and to the right across the grass as the board's own shadows fall
    bx.save(); bx.globalAlpha = 0.22; bx.fillStyle = "#2c2414";
    bx.beginPath(); bx.moveTo(b.x - 0.6, b.y); bx.lineTo(b.x + 13, b.y + 7.5); bx.lineTo(b.x + 14, b.y + 6.2); bx.lineTo(b.x + 0.6, b.y - 0.6); bx.fill();
    bx.beginPath(); bx.moveTo(b.x + 9, b.y + 5.2); bx.lineTo(b.x + 9 + banW * 0.95, b.y + 6.8); bx.lineTo(b.x + 13 + banW * 0.95, b.y + 9.8); bx.lineTo(b.x + 13, b.y + 8.3); bx.closePath(); bx.fill();
    bx.restore();
    const pg = bx.createLinearGradient(b.x - 0.7, 0, b.x + 0.7, 0); pg.addColorStop(0, "#eee6d2"); pg.addColorStop(0.5, "#d6cbb2"); pg.addColorStop(1, "#8d8068");
    bx.fillStyle = pg; bx.fillRect(b.x - 0.65, top, 1.3, banPole);
    const fg = bx.createRadialGradient(b.x - 0.4, top - 1.6, 0.1, b.x, top - 1.2, 1.4); fg.addColorStop(0, "#f3dc94"); fg.addColorStop(1, "#8a6a2c");
    bx.fillStyle = fg; bx.beginPath(); bx.arc(b.x, top - 1.1, 1.15, 0, 6.283); bx.fill();
    // the flag, in slices that ripple more towards the fly
    const f = b.flag, K = f.K, m = f.m, N = 12, sw = (f.W + m) * K / N, fx = b.x - m + 0.2, fy = top + 1.6 - m;
    for (let i = 0; i < N; i++) {
      const sx = m * K * 0 + i * sw, u = Math.max(0, (i * sw / K - m) / f.W), ph = t * speed - u * 3.2 + b.ph;
      const dy = Math.sin(ph) * amp * u, shade = Math.cos(ph) * u;
      bx.drawImage(f, sx, 0, sw + 1, f.height, fx + sx / K, fy + dy, (sw + 1) / K, f.height / K);
      if (Math.abs(shade) > 0.04) { bx.globalCompositeOperation = "source-atop";
        bx.fillStyle = shade > 0 ? `rgba(36,24,10,${(0.24 * shade).toFixed(3)})` : `rgba(255,246,222,${(-0.14 * shade).toFixed(3)})`;
        bx.fillRect(fx + sx / K, fy + dy, sw / K + 0.05, f.height / K); bx.globalCompositeOperation = "source-over"; }
    }
  }
}
// your own colours fly on the last banner before To the Races
let ownSilk = null, silkDefs = null;
function flyOwn(id) {
  ownSilk = id;
  if (!silkDefs || !BANNERS.length || !silkDefs.byId[id]) return;
  const i = BANNERS.length - 1;
  BANNERS[i].flag = silkFlag(silkDefs.byId[id], silkDefs.palette, banW, Math.round(banW * 0.72), 99);
}
Promise.all([fetch(BASE + "banners.json").then((r) => r.json()), fetch(BASE + "silks.json").then((r) => r.json())]).then(([ban, silks]) => {
  banPole = ban.pole; banW = ban.flag;
  const byId = Object.fromEntries(silks.silks.map((s) => [s.id, s]));
  silkDefs = { byId, palette: silks.palette };
  BANNERS = ban.banners.map(([x, y], i) => ({ x, y, ph: i * 0.9, flag: silkFlag(byId[AVENUE[i % AVENUE.length]], silks.palette, banW, Math.round(banW * 0.72), i + 1) }));
  if (ownSilk) flyOwn(ownSilk);
  // the avenue lights up like the places, and picks To the Races
  const tops = BANNERS.map((b) => [b.x - 6, b.y - banPole - 9]), feet = BANNERS.map((b) => [b.x - 6, b.y + 9]).reverse();
  const end = BANNERS[BANNERS.length - 1], first = BANNERS[0];
  const poly = [[first.x - 14, first.y - 10], ...tops, [end.x + banW + 14, end.y - banPole - 9], [end.x + banW + 14, end.y + 4], ...feet, [first.x - 14, first.y + 9]];
  const d = smoothPath(poly);
  const gEl = document.createElementNS(svgNS, "g"); gEl.setAttribute("class", "site " + ((API.states && "st-" + (API.states.races || "open")) || "")); gEl.id = "site-races";
  gEl.innerHTML = `<path class="wash" d="${d}"/><path class="halo" d="${d}"/><path class="hit" d="${d}"/>`;
  gEl.addEventListener("pointerenter", () => hover("races", true)); gEl.addEventListener("pointerleave", () => hover("races", false));
  gEl.addEventListener("click", () => choose(chosen === "races" ? null : "races"));
  glow.insertBefore(gEl, glow.querySelector(".trail"));
  if (chosen === "races") gEl.classList.add("hot");
}).catch((e) => console.warn("banners", e));
const racesBtn = $id("races");
racesBtn.addEventListener("mouseenter", () => hover("races", true)); racesBtn.addEventListener("mouseleave", () => hover("races", false));
racesBtn.addEventListener("focus", () => hover("races", true)); racesBtn.addEventListener("blur", () => hover("races", false));
stage.appendChild(racesBtn); racesBtn.style.left = RACES_AT[0] + "px"; racesBtn.style.top = RACES_AT[1] + "px";

// ---------------------------------------------------------------- the loop
// While a sheet covers the board it holds still (see frame()).
const frameHooks = [];
let last = performance.now(), clockT = 0, skyT = 0;
function frame(now) {
  const raw = Math.min((now - last) / 1000, 0.1);
  if (LITE && (API.covered || document.hidden)) { last = now; requestAnimationFrame(frame); return; }   // a phone's sheet fills the screen
  if (document.body.classList.contains("watching")) { last = now; requestAnimationFrame(frame); return; }   // a race is on over everything
  if (LITE && now - last < 31) { requestAnimationFrame(frame); return; }
  last = now;
  // a sheet is open over the board (the programme, the stud, the sales...): the board holds still behind it, as a
  // still picture, instead of ticking over at a few frames a second (owner, 7 Nov: the moving map was wasted there)
  if (API.covered) { last = now; requestAnimationFrame(frame); return; }
  const dt = raw;
  clockT += dt; const t = clockT;
  if (!API.holdDay) stepDay(dt); else stepDay(0);
  stepSmoke(dt); drawFx(t, dt); drawBanners(t, dt);
  skyT += dt; if (skyT > 1 / 15) { drawSky(skyT); drawMist(skyT); drawLamps(t); skyT = 0; }
  for (const h of frameHooks) { try { h(t, dt); } catch (e) { console.warn(e); } }
  requestAnimationFrame(frame);
}

// ---------------------------------------------------------------- what the game and js/life.js can reach
const API = window.BOARD = {
  MW, MH, REDUCED, ROAD, PLACES, RACES, placeOf, medalAt, routeFor, join, rev,
  get scale() { return scale; }, view, stage, holder,
  inHours, hourNow,
  setHour: (h) => { const t = h >= 5.5 && h < 21.5 ? (h - 5.5) / 16 * 0.86 : 0.86 + (((h - 21.5 + 24) % 24) / 8) * 0.14; dayT = t % 1; },
  holdDay: false, covered: false, blocked: false, states: {},
  setStates, choose, hover, trail, clearTrail, leanTo, panTo, paintPic, fit,
  get chosen() { return chosen; },
  addFrame: (f) => frameHooks.push(f), onFit: (f) => { fitHooks.push(f); f(scale); },
  Sound, setInPlace: (id) => { inPlace = id; placeSound(); },
  flyOwn,
  cardFor: null, onEnter: null, onChoose: null,
};
window.__setHour = API.setHour;
fit(); drawSky(0); requestAnimationFrame(frame);
})();
