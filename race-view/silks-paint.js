/* Silks painted in the browser, for colours a player makes themselves (owner, 13 Nov 2026: "let's make all new players
   make their own colours", from the base templates: 25 jackets, 12 sleeves, 10 caps, each with a colour and a second
   colour from a fixed palette).

   The pattern rules below are tools/silks/make_silks.py's, line for line (body_mask, sleeve_mask, cap_mask), so a
   player's silks follow exactly the same rules as the 54 ready-made ones. KEEP THE TWO IN STEP: a pattern changed
   there must be changed here.

   A set of colours ("spec"): { body: { p, a, b }, sleeves: { p, a, b }, cap: { p, a, b } }
       p: the pattern's name (as in silks.json), a: its colour, b: its second colour (hex).

   SilksPaint.texture(spec, size, "v2" | "v1")  the 3D jockey's texture, as a canvas (layouts: make_silks_v2.py, make_silks.py)
   SilksPaint.icon(spec, width)                 the menu picture, in the owner's diagram layout: the strip on the left is
                                                the sleeves, the half circle at the top the cap, the rest the body
   SilksPaint.encode(spec) / decode(text)       a short text for a set of colours (saving, the leaderboard)
   Loaded as a plain script by the game (index.html) and by the race view (final-furlong.html). */
(function (root) {
  "use strict";
  // The palette: read from the owner's 54 silks graphics (the ten most used, plus green and orange)
  const PALETTE = [
    ["White", "#f1f6f6"], ["Royal blue", "#2454a4"], ["Black", "#1c1c1c"], ["Navy", "#343d54"], ["Yellow", "#f4e93e"], ["Red", "#ec2d24"],
    ["Pink", "#eca4c4"], ["Ice blue", "#b5e4f3"], ["Purple", "#4c246c"], ["Turquoise", "#64c4ac"], ["Green", "#3c9444"], ["Orange", "#f3a43d"],
  ];
  // The templates, numbered as on the owner's sheets, then the extra patterns that are not on them
  const JACKETS = [["plain", "Plain"], ["strip", "Strip"], ["braces", "Braces"], ["belt", "Belt"], ["hoops", "Hooped"], ["chevron", "Chevron"],
    ["chevrons", "Chevrons"], ["seams", "Seams"], ["crossbelts", "Cross belts"], ["cross of lorraine", "Cross of Lorraine"], ["check", "Checks"],
    ["diamond", "Diamond"], ["diamonds", "Diamonds"], ["quartered", "Quartered"], ["epaulets", "Epaulettes"], ["star", "Star"], ["stars", "Stars"],
    ["spots", "Spots"], ["stripes", "Stripes"], ["disc", "Disc"], ["diabolo", "Diabolo"], ["inverted triangle", "Inverted triangle"],
    ["large spots", "Large spots"], ["triple diamond", "Triple diamond"], ["hollow box", "Hollow box"],
    ["sash", "Sash"], ["halved", "Halved"], ["inverted chevron", "Inverted chevron"], ["panel", "Panel"], ["three spots", "Three spots"]];
  const SLEEVES = [["plain", "Plain"], ["armlets", "Armlet"], ["hoops", "Hooped"], ["stripes", "Striped"], ["chevrons", "Chevrons"], ["seams", "Seams"],
    ["stars", "Stars"], ["spots", "Spots"], ["halved", "Halved"], ["diabolo", "Diabolo"], ["diamonds", "Diamonds"], ["check", "Check"], ["cuffs", "Cuffs"]];
  const CAPS = [["plain", "Plain"], ["hooped", "Hooped"], ["striped", "Striped"], ["check", "Check"], ["spots", "Spots"], ["quartered", "Quartered"],
    ["star", "Star"], ["diamond", "Diamond"], ["stars", "Stars"], ["diamonds", "Diamonds"], ["halved", "Halved"], ["four spots", "Four spots"], ["peak", "Peak"]];

  const PI = Math.PI, abs = Math.abs, floor = Math.floor, hypot = Math.hypot, min = Math.min, max = Math.max;
  const mod = (a, n) => ((a % n) + n) % n;
  const odd = x => mod(floor(x), 2) === 1;
  const clip = (x, a, b) => x < a ? a : x > b ? b : x;
  function spots(x, y, r) { const row = floor(y), xs = x + 0.5 * mod(row, 2); return hypot(xs - floor(xs) - 0.5, y - row - 0.5) < r; }
  function star(px, py, r) {
    const k = mod(Math.atan2(px, py), 2 * PI / 5) - PI / 5, inner = 0.42;
    return hypot(px, py) < max(r * (inner + (1 - inner) * Math.pow(abs(k) / (PI / 5), 1.6)), r * inner);
  }
  // a brick grid of unit cells: each point's place in its own cell
  function cellX(x, y) { const xs = x + 0.5 * mod(floor(y), 2); return xs - floor(xs) - 0.5; }
  function cellY(y) { return y - floor(y) - 0.5; }

  // ---------------- the rules: true where the second colour goes ----------------
  // L runs across the body from the jockey's right side (-1) to his left (+1), the same front and back; h from the
  // waist (0) to the collar (1); Y is h in half-widths from mid-body (asp: how tall the body is drawn).
  function bodyMask(p, u, h, asp) {
    let a = mod(u - 0.25, 1); if (a > 0.5) a -= 1;
    const L = abs(a) <= 0.25 ? a / 0.25 : Math.sign(a) * (0.5 - abs(a)) / 0.25, Y = (h - 0.5) * asp;
    switch (p || "plain") {
      case "plain": return false;
      case "hoops": return odd(h * 8);
      case "hooped band": case "belt": return h > 0.42 && h < 0.62;
      case "stripes": return odd(u * 24);
      case "sash": return abs(L - (2 * h - 1)) < 0.34;
      case "crossbelts": return abs(L - (2 * h - 1)) < 0.26 || abs(L + (2 * h - 1)) < 0.26;
      case "chevron": return abs(h - (0.25 + 0.78 * abs(L))) < 0.15;
      case "inverted chevron": return abs(h - (0.95 - 0.7 * abs(L))) < 0.15;
      case "chevrons": return odd((h - 0.6 * abs(L)) * 5);
      case "braces": return abs(abs(L) - 0.5) < 0.12;
      case "halved": return L > 0;
      case "quartered": return (L > 0) !== (h > 0.5);
      case "spots": return spots(u * 4 * 2.6, (Y + 10) * 2.6, 0.27);
      case "large spots": return spots(u * 4 * 1.25, (Y + 10) * 1.25, 0.3);
      case "three spots": return hypot(L - 0.68, Y - 0.95) < 0.42 || hypot(L, Y) < 0.42 || hypot(L + 0.68, Y + 0.95) < 0.42;
      case "disc": return hypot(L, Y) < 0.62;
      case "star": return star(L, Y, 0.75);
      case "diamond": return abs(L) * 1.3 + abs(Y) < 0.85;
      case "epaulets": { const band = abs(abs(L) - 0.6); return band < 0.22 && h > 0.45 + 0.8 * band; }
      case "panel": return abs(L) < 0.45 && h > 0.12 && h < 0.88;
      case "seams": return abs(abs(L) - 1) < 0.07 || h > 0.95;
      case "check": return mod(floor(u * 16) + floor(h * 6), 2) === 1;
      case "strip": return abs(L) < 0.24;
      case "cross of lorraine": return (abs(L) < 0.13 && abs(Y) < 0.82) || (abs(Y - 0.36) < 0.1 && abs(L) < 0.36) || (abs(Y + 0.06) < 0.1 && abs(L) < 0.56);
      case "diamonds": { const P = u * 12, Q = Y * 1.9; return mod(floor(P + Q) + floor(P - Q), 2) === 1; }
      case "stars": { const x = u * 4 * 1.5, y = (Y + 10) * 1.5; return star(cellX(x, y), cellY(y), 0.4); }
      case "diabolo": return abs(L) < abs(2 * h - 1) * 0.98;
      case "inverted triangle": return Y < 0.72 && Y > -0.5 && abs(L) < (Y + 0.5) * 0.6;
      case "triple diamond": return min(abs(L + 0.64), abs(L), abs(L - 0.64)) * 3.0 + abs(Y - 0.1) * 1.9 < 0.92;
      case "hollow box": { const m = max(abs(L) * 1.15, abs(Y - 0.05)); return m > 0.36 && m < 0.62; }
    }
    return false;
  }
  // u: round the arm (0 the outside); t: shoulder (0) to cuff (1)
  function sleeveMask(p, u, t, asp) {
    const X = mod(u + 0.5, 1) - 0.5;
    switch (p || "plain") {
      case "plain": return false;
      case "hoops": return odd(t * 7);
      case "stripes": return odd(u * 8);
      case "halved": return t > 0.5;
      case "chevrons": return odd(t * 5 + abs(X) * 2.0);
      case "armlets": return t > 0.45 && t < 0.6;
      case "cuffs": return t > 0.84;
      case "spots": return spots(u * 6, t * 6 * asp, 0.27);
      case "diabolo": return abs(X) < 0.12 + 0.2 * abs(t - 0.5);
      case "seams": return abs(mod(u + 0.25, 0.5) - 0.25) < 0.03;
      case "stars": return star(X, (t - 0.2) * asp, 0.15) || star(X, (t - 0.5) * asp, 0.15) || star(X, (t - 0.8) * asp, 0.15);
      case "diamonds": return abs(X) * 3.4 + abs(mod(t * 4, 1) - 0.5) * 2.0 < 1.0;
      case "check": return mod(floor(u * 6) + floor(t * 6 * asp), 2) === 1;
    }
    return false;
  }
  // u: round the crown (.5 the peak, .75 the jockey's left); v: the top (0) to the rim (1)
  function capMask(p, u, v) {
    switch (p || "plain") {
      case "plain": return false;
      case "quartered": return odd(mod(u + 0.125, 1) * 4);
      case "halved": return u > 0.5;
      case "striped": return odd(u * 12);
      case "hooped": return odd(v * 5);
      case "spots": return spots(u * 8, v * 2.2, 0.27);
      case "four spots": { const X = (u - 0.5) * 3.2, Yc = (0.5 - v) * 1.1; return hypot(abs(X) - 0.2, abs(Yc) - 0.17) < 0.13; }
      case "star": return star((u - 0.5) * 3.2, (0.55 - v) * 1.1, 0.42);
      case "diamond": return abs(u - 0.5) * 3.2 + abs(v - 0.5) * 1.3 < 0.45;
      case "peak": return v > 0.85 && abs(u - 0.5) < 0.18;
      case "check": return mod(floor(u * 8) + floor(v * 3), 2) === 1;
      case "stars": { const a1 = mod(u * 6, 1) - 0.5, a2 = mod(u * 3 + 0.5, 1) - 0.5;
        return star(a1 * 2 * PI * 0.72 / 6 * 3.2, (v - 0.72) * 3.2, 0.42) || star(a2 * 2 * PI * 0.36 / 3 * 3.2, (v - 0.36) * 3.2, 0.42); }
      case "diamonds": { const P = u * 8, Q = v * 2.5; return mod(floor(P + Q) + floor(P - Q), 2) === 1; }
    }
    return false;
  }

  // ---------------- painting ----------------
  const rgb = hex => { const n = parseInt(String(hex).replace("#", ""), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; };
  function parts(spec) {
    const f = z => ({ p: z.p || "plain", a: rgb(z.a), b: rgb(z.b || z.a) });
    return { body: f(spec.body), sleeves: f(spec.sleeves || spec.body), cap: f(spec.cap || spec.body) };
  }
  function canvasOf(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
  function fillPixels(w, h, at) {
    const c = canvasOf(w, h), g = c.getContext("2d"), im = g.createImageData(w, h), d = im.data;
    for (let y = 0, k = 0; y < h; y++) for (let x = 0; x < w; x++, k += 4) { const q = at((x + 0.5) / w, (y + 0.5) / h); d[k] = q[0]; d[k + 1] = q[1]; d[k + 2] = q[2]; d[k + 3] = 255; }
    g.putImageData(im, 0, 0); return c;
  }
  // The 3D jockey's texture. v2 (the race view's jockey; layout in tools/silks/make_silks_v2.py): the body across the
  // top (y 0 to .47, waist to collar), the sleeves under it, the cap a disc. v1 (the board's little horses; layout in
  // make_silks.py): rows, the body, the left sleeve, the right sleeve, the cap.
  function texture(spec, size, layout) {
    const P = parts(spec), S = size || 1024;
    if (layout === "v1") return fillPixels(S, S, (U, V) => {
      if (V < 0.50) return bodyMask(P.body.p, U, V / 0.50, 1.9) ? P.body.b : P.body.a;
      if (V < 0.52) return P.body.a;
      if (V < 0.70) return sleeveMask(P.sleeves.p, U, (V - 0.52) / 0.18, 1.0) ? P.sleeves.b : P.sleeves.a;
      if (V < 0.72) return P.sleeves.a;
      if (V < 0.90) return sleeveMask(P.sleeves.p, U, (V - 0.72) / 0.18, 1.0) ? P.sleeves.b : P.sleeves.a;
      if (V < 0.92) return P.sleeves.a;
      return capMask(P.cap.p, U, (V - 0.92) / 0.08) ? P.cap.b : P.cap.a;
    });
    const SL = [[0.04, 0.53, 0.26, 0.43], [0.37, 0.53, 0.26, 0.43]], CX = 0.82, CY = 0.745, R = 0.155;
    return fillPixels(S, S, (X, Y) => {
      const dx = X - CX, dy = Y - CY, rr = hypot(dx, dy) / R;
      if (rr < 1.12) return capMask(P.cap.p, mod(Math.atan2(dx, dy) / (2 * PI) + 0.5, 1), clip(rr, 0, 1)) ? P.cap.b : P.cap.a;
      for (const [x0, y0, w, h] of SL)
        if (X > x0 - 0.03 && X < x0 + w + 0.03 && Y > y0 - 0.03 && Y < y0 + h + 0.03)
          return sleeveMask(P.sleeves.p, mod((X - x0) / w, 1), clip((Y - y0) / h, 0, 1), 1.0) ? P.sleeves.b : P.sleeves.a;
      if (Y < 0.50) return bodyMask(P.body.p, mod(X, 1), clip(Y / 0.47, 0, 1), 1.9) ? P.body.b : P.body.a;
      return P.body.a;
    });
  }
  // The menu picture, in the owner's diagram layout (his 54 are 140 x 198): the sleeves a strip down the left, the cap
  // a half circle hanging from the top edge, the body the rest, its pattern centred in it. Drawn at twice the size
  // and brought down, so edges are smooth.
  const ICON = { ratio: 198 / 140, strip: 0.245, capX: 0.395, capR: 0.335 };
  function icon(spec, width) {
    const P = parts(spec), W = width || 140, H = Math.round(W * ICON.ratio), K = 2, asp = ICON.ratio;   // asp: the picture's height in widths
    const shade = (c, k) => [c[0] * k, c[1] * k, c[2] * k];
    const bodyHalf = (1 - ICON.strip) / 2, bodyMid = ICON.strip + bodyHalf, line = 0.007;
    const big = fillPixels(W * K, H * K, (X, Yn) => {
      const y = Yn * asp;                                           // down the picture, in widths
      const dx = (X - ICON.capX) / ICON.capR, dy = y / ICON.capR, rr = hypot(dx, dy);
      if (rr < 1) {
        const u = 0.5 + 0.25 * clip(dx, -1, 1), v = clip(dy, 0, 1);
        let on;
        if (P.cap.p === "quartered") on = odd((dx + 1) * 2);          // seen from the front: four upright panels
        else if (P.cap.p === "halved") on = dx > 0;
        else if (P.cap.p === "stars") on = star(cellX(dx * 2.2 + 0.5, dy * 2.2), cellY(dy * 2.2), 0.4);
        else if (P.cap.p === "diamonds") { const p = dx * 2.6, q = dy * 2.6; on = mod(floor(p + q) + floor(p - q), 2) === 1; }
        else if (P.cap.p === "peak") on = dy > 0.8;
        else on = capMask(P.cap.p, u, v);
        const c = on ? P.cap.b : P.cap.a;
        return rr > 1 - 0.022 ? shade(c, 0.86) : c;                 // the cap's edge, a shade darker
      }
      if (X < ICON.strip) {
        const u = mod((X / ICON.strip - 0.5) * 0.5, 1), t = Yn;      // patterns centred in the strip
        const c = sleeveMask(P.sleeves.p, u, t, 2.9) ? P.sleeves.b : P.sleeves.a;
        return X > ICON.strip - line ? shade(c, 0.86) : c;           // the seam between sleeve and body
      }
      const L = (X - bodyMid) / bodyHalf, h = 1 - Yn;
      return bodyMask(P.body.p, 0.25 + 0.25 * clip(L, -1, 1), h, asp / bodyHalf) ? P.body.b : P.body.a;
    });
    const c = canvasOf(W, H), g = c.getContext("2d"); g.imageSmoothingEnabled = true; g.imageSmoothingQuality = "high";
    g.drawImage(big, 0, 0, W, H); return c;
  }

  // ---------------- saving ----------------
  const names = list => list.map(x => x[0]);
  const hexOk = h => typeof h === "string" && /^#[0-9a-f]{6}$/i.test(h);
  function valid(spec) {
    const ok = (z, list) => z && names(list).includes(z.p || "plain") && hexOk(z.a) && hexOk(z.b || z.a);
    return !!spec && ok(spec.body, JACKETS) && ok(spec.sleeves, SLEEVES) && ok(spec.cap, CAPS);
  }
  // "j5.1.4-s2.1.4-c0.4.4": each part's pattern number, colour and second colour, by their place in the lists above
  function encode(spec) {
    const ci = h => Math.max(0, PALETTE.findIndex(c => c[1].toLowerCase() === String(h).toLowerCase()));
    const f = (k, z, list) => k + Math.max(0, names(list).indexOf(z.p || "plain")) + "." + ci(z.a) + "." + ci(z.b || z.a);
    return [f("j", spec.body, JACKETS), f("s", spec.sleeves, SLEEVES), f("c", spec.cap, CAPS)].join("-");
  }
  function decode(text) {
    const m = /^j(\d+)\.(\d+)\.(\d+)-s(\d+)\.(\d+)\.(\d+)-c(\d+)\.(\d+)\.(\d+)$/.exec(String(text || "")); if (!m) return null;
    const n = m.slice(1).map(Number), col = i => (PALETTE[i] || PALETTE[0])[1], f = (list, i) => ({ p: (list[n[i]] || list[0])[0], a: col(n[i + 1]), b: col(n[i + 2]) });
    return { body: f(JACKETS, 0), sleeves: f(SLEEVES, 3), cap: f(CAPS, 6) };
  }
  // a set to start from: two colours that go together, plain sleeves and cap as likely as not
  function random(rnd) {
    rnd = rnd || Math.random;
    const pick = list => list[floor(rnd() * list.length)], a = pick(PALETTE)[1]; let b = pick(PALETTE)[1]; while (b === a) b = pick(PALETTE)[1];
    const plainish = (list) => rnd() < 0.5 ? "plain" : pick(list)[0];
    return { body: { p: pick(JACKETS.slice(0, 25))[0], a, b }, sleeves: { p: plainish(SLEEVES), a: rnd() < 0.6 ? a : b, b: rnd() < 0.6 ? b : a }, cap: { p: plainish(CAPS), a: rnd() < 0.5 ? a : b, b: rnd() < 0.5 ? b : a } };
  }
  // "Royal blue, yellow chevron, yellow sleeves, royal blue cap with a yellow star": how racing describes colours
  function describe(spec) {
    const nm = h => { const c = PALETTE.find(x => x[1].toLowerCase() === String(h).toLowerCase()); return c ? c[0].toLowerCase() : "coloured"; };
    const label = (list, p) => ((list.find(x => x[0] === p) || list[0])[1]).toLowerCase();
    const part = (z, list, noun) => { const p = z.p || "plain", plain = p === "plain" || (z.b || z.a) === z.a;
      return plain ? `${nm(z.a)}${noun ? " " + noun : ""}` : `${nm(z.a)}${noun ? " " + noun : ""}, ${nm(z.b)} ${label(list, p)}`; };
    const t = [part(spec.body, JACKETS, ""), part(spec.sleeves, SLEEVES, "sleeves"), part(spec.cap, CAPS, "cap")].join("; ");
    return t.charAt(0).toUpperCase() + t.slice(1);
  }

  root.SilksPaint = { PALETTE, JACKETS, SLEEVES, CAPS, bodyMask, sleeveMask, capMask, texture, icon, valid, encode, decode, random, describe };
})(typeof window !== "undefined" ? window : globalThis);
