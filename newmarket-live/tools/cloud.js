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
