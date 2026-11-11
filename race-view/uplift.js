// Thoroughbred race view: the V2 look (11 Nov 2026). Loaded only with ?uplift=... on the address; without it the race
// view is exactly as before. Everything here is PART OF THE 3D SCENE: the light, the shadows, the ground's shading, the
// sky dome, real planting. No picture filter and no extra full-screen pass; it moves with the cameras like the rest.
//
// The big change: the world is RELIT. Blender's baked light is kept only as soft "how open to the sky is this spot"
// shading; the sun itself is worked out here, with real cast shadows from the stand, the site pieces and the trees
// (two shadow pictures taken once from the sun as the view opens, then only looked up: nothing extra is drawn each
// frame). So the sun can stand anywhere, and a "look" is just a short list of numbers: where the sun is, its colour,
// the sky, the haze. Same course, same models, any time of day or weather.
//
//   ?uplift=afternoon   (or 1) Royal afternoon: fresh blue sky, a clear warm sun, lilac shade
//   ?uplift=golden      Golden hour: a low sun raking along the stand, long shadows across the turf
//   ?uplift=storm       Storm light: the stand and the turf lit against a dark slate sky, sun patches drifting through
//   ?uplift=mist        Misty morning: silver light, the far side fading into layers of haze
//   &upoff=a,b,...      leave parts out: heath, plants, clouds (their shadows), sky, relight, crowd, turf
//   &cloudAt=x,z        slide the cloud shadows (metres), for composing a still
import * as THREE from "three";

const q = new URLSearchParams(location.search);
const OFF = (q.get("upoff") || "").split(",");
export const has = (k) => !OFF.includes(k);

// A look: all the light there is. Colours of light are linear; sky and haze colours are as they should appear.
//   sun: from the course towards the sun (x east, y up, z south; the stand faces -z)
//   sunCol: the sun's light on a surface facing it; ambSky / ambGnd: the sky's light from above, the ground's from below
//   gndSun / gndShade: what the (unlit) ground's own colours are multiplied by in the sun and in shadow
//   litTint / shadeTint: a last warm / cool push on the sunlit and shaded sides of things; rim: a thread of sunlight
//   round the edges of figures against the light
//   haze: amount (0..1), starts at (m), builds over (m), how much thicker and warmer towards the sun
const LOOKSET = {
  afternoon: {
    label: "Royal afternoon", sun: [-110, 104.5, -49.5],
    sunCol: [1.12, 1.03, 0.88], ambSky: [0.33, 0.38, 0.56], ambGnd: [0.36, 0.33, 0.27],
    gndSun: [1.03, 1.02, 0.97], gndShade: [0.5, 0.54, 0.76], litTint: [1.06, 1.03, 0.95], shadeTint: [0.86, 0.89, 1.06], rim: 0.22,
    sky: { horizon: "#f6ecdb", mid: "#bfdaf0", top: "#6ea4dc", glow: [1.0, 0.84, 0.62], cover: 0.53, edge: "#ffffff", base: "#b9c3de", thick: 0.5 },
    haze: [0.3, 120, 900, 0.5], hazeCol: "#d7dce8", hazeSun: "#f2e9da", exposure: 1.0, clouds: 0.9, catcher: ["#2a2f52", 0.46],
    crowdShade: [0.46, 0.47, 0.66],
  },
  golden: {
    label: "Golden hour", sun: [-1, 0.24, -0.22],
    sunCol: [1.9, 1.18, 0.56], ambSky: [0.25, 0.3, 0.52], ambGnd: [0.42, 0.3, 0.2],
    gndSun: [1.2, 1.04, 0.7], gndShade: [0.3, 0.36, 0.68], litTint: [1.1, 1.0, 0.86], shadeTint: [0.78, 0.84, 1.12], rim: 0.9,
    sky: { horizon: "#ffd9a8", mid: "#f3c9c0", top: "#7f9bd2", glow: [1.0, 0.72, 0.38], cover: 0.56, edge: "#ffe2c2", base: "#b79bbd", thick: 0.6 },
    haze: [0.34, 70, 600, 1.4], hazeCol: "#cbbfd2", hazeSun: "#ffd29a", exposure: 1.0, clouds: 0.0, catcher: ["#2b2452", 0.6],
    crowdShade: [0.38, 0.38, 0.62],
  },
  storm: {
    label: "Storm light", sun: [-0.85, 0.45, -0.35],
    sunCol: [1.5, 1.34, 1.05], ambSky: [0.2, 0.24, 0.34], ambGnd: [0.26, 0.27, 0.22],
    gndSun: [1.12, 1.1, 0.92], gndShade: [0.4, 0.44, 0.58], litTint: [1.06, 1.04, 0.96], shadeTint: [0.84, 0.88, 1.04], rim: 0.35,
    sky: { horizon: "#c9cfd6", mid: "#69758e", top: "#3b4560", glow: [1.0, 0.9, 0.7], cover: 0.38, edge: "#aab3c4", base: "#353d52", thick: 1.0 },
    haze: [0.36, 90, 700, 0.6], hazeCol: "#8e97aa", hazeSun: "#d6d3c8", exposure: 1.0, clouds: 1.0, cloudCover: 0.46, catcher: ["#1e2440", 0.55],
    crowdShade: [0.42, 0.44, 0.6],
  },
  mist: {
    label: "Misty morning", sun: [0.8, 0.3, -0.5],
    sunCol: [0.8, 0.72, 0.6], ambSky: [0.5, 0.52, 0.57], ambGnd: [0.4, 0.4, 0.37],
    gndSun: [1.0, 0.98, 0.93], gndShade: [0.7, 0.73, 0.82], litTint: [1.04, 1.02, 0.97], shadeTint: [0.93, 0.95, 1.03], rim: 0.5,
    sky: { horizon: "#ece6dc", mid: "#dfe2e6", top: "#b9c6d6", glow: [1.0, 0.86, 0.66], cover: 0.75, edge: "#f4f1ec", base: "#d2d6dc", thick: 0.3 },
    haze: [0.92, 15, 170, 0.6], hazeTop: 0.35, hazeCol: "#dcdcdc", hazeSun: "#f6e3c4", exposure: 1.0, clouds: 0.0, catcher: ["#3a4058", 0.3],
    crowdShade: [0.62, 0.63, 0.74],
  },
};
// The soft look (owner's choices in the landscape workshop, 11 Nov 2026; see claude/landscape-workshop-handover.md):
// a low warm sun and a lot of soft sky light, a clear sky graded from straw at the horizon to pale teal overhead, a light
// straw haze; the ground one soft brushed surface (a fine grain, and a nap of soft light and dark clouds like brushed
// suede); the trees graded dark at the foot to light at the crown, paler and flatter with distance. No bushes.
LOOKSET.soft = {
  label: "Soft afternoon", brushed: 0.32, trees: true, sun: [-0.25, 0.55, -0.85],
  sunCol: [1.2, 1.08, 0.82], ambSky: [0.52, 0.56, 0.5], ambGnd: [0.44, 0.41, 0.31],
  gndSun: [1.04, 1.02, 0.94], gndShade: [0.6, 0.67, 0.64], litTint: [1.04, 1.02, 0.96], shadeTint: [0.92, 0.96, 0.98], rim: 0.12,
  sky: { horizon: "#efecc6", mid: "#dde5cb", top: "#b4d4cc", glow: [0.5, 0.45, 0.3], cover: 2, edge: "#ffffff", base: "#ffffff", thick: 0 },
  haze: [0.6, 70, 520, 0.15], hazeTop: 0.8, hazeCol: "#efecc6", hazeSun: "#f3edc6", exposure: 1.0, clouds: 0.0, catcher: ["#3a4a40", 0.36],
  crowdShade: [0.6, 0.64, 0.62],
};
// The course as a model on a table: the same world under a warm lamp, cut to a board with a painted edge, standing on
// a wooden table with the game's own cards beside it. For the moments either side of a race (the board comes alive,
// the camera dives in; afterwards it lifts back out to the table and the cards).
LOOKSET.table = {
  label: "The board on the table", table: true, sun: [0.5, 0.8, -0.42],
  sunCol: [1.3, 1.12, 0.86], ambSky: [0.4, 0.37, 0.36], ambGnd: [0.34, 0.29, 0.22],
  gndSun: [1.06, 1.02, 0.92], gndShade: [0.46, 0.47, 0.6], litTint: [1.06, 1.02, 0.94], shadeTint: [0.88, 0.89, 1.02], rim: 0.2,
  sky: { room: true, horizon: "#4a372a", mid: "#241b15", top: "#120e0b", glow: [0.5, 0.36, 0.2], cover: 2, edge: "#000000", base: "#000000", thick: 0 },
  haze: [0.0, 100, 900, 0], hazeCol: "#2b211a", hazeSun: "#2b211a", exposure: 1.0, clouds: 0.0, catcher: ["#2a2a40", 0.5],
  crowdShade: [0.5, 0.5, 0.62], heather: 0.15,
  props: { cards: [-200, -590, 4.04], cover: [-640, -110, 4.35], board: [1380, -1420, 3.0] },   // [x, z, turn]
};
const LOOK_ID = LOOKSET[q.get("uplift")] ? q.get("uplift") : "afternoon";
const LOOK = LOOKSET[LOOK_ID];
export const lookId = LOOK_ID, looks = Object.fromEntries(Object.entries(LOOKSET).map(([k, v]) => [k, v.label]));

const M = 3;                       // metres per pixel of the site map
const RIDE = 5;                    // the mown verge beside the rail, metres
const LOW = 24;                    // within this of the rail only low planting (the tracking car films from 12 m inside it)
const v3 = (a) => new THREE.Vector3(...a), disp = (hex) => { const c = new THREE.Color(hex).convertLinearToSRGB(); return new THREE.Vector3(c.r, c.g, c.b); };
const U = {
  upTime: { value: 0 }, upSite: { value: null }, upNoise: { value: null }, upCrowd: { value: null },
  upArea: { value: new THREE.Vector4() }, upCrowdArea: { value: new THREE.Vector4(0, 0, -1, -1) }, upOff: { value: new THREE.Vector2() },
  upSun: { value: v3(LOOK.sun).normalize() }, upSunCol: { value: v3(LOOK.sunCol) }, upAmbSky: { value: v3(LOOK.ambSky) }, upAmbGnd: { value: v3(LOOK.ambGnd) },
  upGndSun: { value: v3(LOOK.gndSun) }, upGndShade: { value: v3(LOOK.gndShade) }, upLitTint: { value: v3(LOOK.litTint) }, upShadeTint: { value: v3(LOOK.shadeTint) },
  upCrowdShade: { value: v3(LOOK.crowdShade) }, upRim: { value: LOOK.rim }, upCloudK: { value: has("clouds") ? LOOK.clouds : 0 }, upCloudCover: { value: LOOK.cloudCover || 0.49 },
  upHaze: { value: new THREE.Vector4(...LOOK.haze) }, upHazeTop: { value: LOOK.hazeTop ?? 0.85 }, upHazeCol: { value: disp(LOOK.hazeCol) }, upHorizon: { value: disp(LOOK.sky.horizon) }, upHazeSun: { value: disp(LOOK.hazeSun) },
  upSh1: { value: null }, upSh2: { value: null }, upShM1: { value: new THREE.Matrix4() }, upShM2: { value: new THREE.Matrix4() },
  upShT: { value: new THREE.Vector4(1, 1, 0.001, 0.001) },     // texel size of each shadow picture, then each one's depth allowance
};
let BOARD = null;                  // the table look: the board's edges [x0, z0, x1, z1], and the planes that cut the ground to it
let S = null;                      // { x0, z0, W, H, data } the site map; N = { size, data } the noise
let N = null, CTX = null;

// ---------- Noise: one small tileable image, read at several sizes (in the shaders and here, so both agree) ----------
function makeNoise(size = 256) {
  const data = new Uint8Array(size * size * 4);
  const lattice = (period, seed) => {
    const g = new Float32Array(period * period);
    let s = seed >>> 0;
    for (let i = 0; i < g.length; i++) { s = (s * 1664525 + 1013904223) >>> 0; g[i] = s / 4294967296; }
    return (u, v) => {                                   // u, v in 0..1, wraps
      const x = u * period, y = v * period, i = Math.floor(x), j = Math.floor(y);
      let a = x - i, b = y - j; a = a * a * (3 - 2 * a); b = b * b * (3 - 2 * b);
      const i0 = ((i % period) + period) % period, i1 = (i0 + 1) % period, j0 = ((j % period) + period) % period, j1 = (j0 + 1) % period;
      return (g[j0 * period + i0] * (1 - a) + g[j0 * period + i1] * a) * (1 - b) + (g[j1 * period + i0] * (1 - a) + g[j1 * period + i1] * a) * b;
    };
  };
  const ch = [
    [[4, 0.6, 11], [8, 0.28, 12], [16, 0.12, 13]],       // r: big soft shapes
    [[4, 0.55, 21], [8, 0.3, 22], [16, 0.15, 23]],       // g: another set
    [[16, 0.5, 31], [32, 0.3, 32], [64, 0.2, 33]],       // b: fine
    [[6, 0.55, 41], [12, 0.3, 42], [24, 0.15, 43]],      // a: middling
  ].map((oct) => oct.map(([p, w, s]) => [lattice(p, s), w]));
  for (let j = 0; j < size; j++) for (let i = 0; i < size; i++) {
    const u = (i + 0.5) / size, v = (j + 0.5) / size;
    for (let c = 0; c < 4; c++) {
      let x = 0; for (const [f, w] of ch[c]) x += f(u, v) * w;
      data[(j * size + i) * 4 + c] = Math.max(0, Math.min(255, Math.round((0.5 + (x - 0.5) * 1.7) * 255)));   // stretched to use the range
    }
  }
  return { size, data };
}
function noiseAt(c, u, v) {                              // as the shader's texture2D(upNoise, uv)[c], 0..1
  const n = N.size, x = u * n - 0.5, y = v * n - 0.5, i = Math.floor(x), j = Math.floor(y), a = x - i, b = y - j;
  const at = (ii, jj) => N.data[((((jj % n) + n) % n) * n + (((ii % n) + n) % n)) * 4 + c] / 255;
  return (at(i, j) * (1 - a) + at(i + 1, j) * a) * (1 - b) + (at(i, j + 1) * (1 - a) + at(i + 1, j + 1) * a) * b;
}

// ---------- The site map: for every 3 m of the site, how far it is from the turf, and whether it is infield heath ----------
function makeSite(COURSE, dressing) {
  const surf = COURSE.track.surface, ring = surf[0];
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
  for (const [x, z] of ring) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z); }
  x0 -= 120; x1 += 120; z0 -= 120; z1 += 120;
  const W = Math.ceil((x1 - x0) / M), H = Math.ceil((z1 - z0) / M);
  const raster = (draw) => {
    const c = document.createElement("canvas"); c.width = W; c.height = H;
    const g = c.getContext("2d", { willReadFrequently: true });
    g.fillStyle = "#000"; g.fillRect(0, 0, W, H); g.fillStyle = "#fff"; g.strokeStyle = "#fff";
    draw(g, (poly) => { poly.forEach(([x, z], i) => (i ? g.lineTo((x - x0) / M, (z - z0) / M) : g.moveTo((x - x0) / M, (z - z0) / M))); g.closePath(); });
    const d = g.getImageData(0, 0, W, H).data, out = new Uint8Array(W * H);
    for (let i = 0; i < W * H; i++) out[i] = d[i * 4] > 127 ? 1 : 0;
    return out;
  };
  const turf = raster((g, path) => { g.beginPath(); for (const r of surf) path(r); g.fill("evenodd"); });
  const infield = raster((g, path) => { g.beginPath(); for (const r of surf.slice(1)) path(r); g.fill(); });
  // the festival inside the home straight keeps its own ground: 32 m round every piece that stands there
  const festival = raster((g) => { for (const p of (dressing && dressing.pieces) || []) { g.beginPath(); g.arc((p.x - x0) / M, (p.z - z0) / M, 32 / M, 0, Math.PI * 2); g.fill(); } });
  // distance from the turf (two sweeps, 3-4 chamfer: within a few per cent of true)
  const BIG = 1e6, d = new Float32Array(W * H);
  for (let i = 0; i < W * H; i++) d[i] = turf[i] ? 0 : BIG;
  const pass = (dir) => {
    const [ja, jb, js, ia, ib, is] = dir > 0 ? [0, H, 1, 0, W, 1] : [H - 1, -1, -1, W - 1, -1, -1];
    for (let j = ja; j !== jb; j += js) for (let i = ia; i !== ib; i += is) {
      const k = j * W + i; let v = d[k];
      const jj = j - js, ii = i - is;
      if (ii >= 0 && ii < W) v = Math.min(v, d[j * W + ii] + 3);
      if (jj >= 0 && jj < H) {
        v = Math.min(v, d[jj * W + i] + 3);
        if (ii >= 0 && ii < W) v = Math.min(v, d[jj * W + ii] + 4);
        const i2 = i + is; if (i2 >= 0 && i2 < W) v = Math.min(v, d[jj * W + i2] + 4);
      }
      d[k] = v;
    }
  };
  pass(1); pass(-1);
  // and, on the turf, how far from the infield (the inside rail): the worn strip the field runs along
  const turfD = d.slice();
  for (let i = 0; i < W * H; i++) d[i] = infield[i] ? 0 : BIG;
  pass(1); pass(-1);
  const inner = d.slice(); d.set(turfD);
  // heath = infield, off the festival; its edge softened over a few metres
  const heath = new Float32Array(W * H);
  const zone = COURSE.zones && COURSE.zones.grandstand;
  for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
    const k = j * W + i, x = x0 + (i + 0.5) * M, z = z0 + (j + 0.5) * M;
    const stands = zone && x > zone.from - 40 && x < zone.to && z > 0 && z < zone.farEdge + 30;
    heath[k] = (infield[k] || (LOOK.table && !turf[k] && !stands)) && !festival[k] ? 1 : 0;
  }
  const blur = (src) => {
    const t = new Float32Array(W * H), o = new Float32Array(W * H), R = 3;
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) { let s = 0, n = 0; for (let k = -R; k <= R; k++) { const ii = i + k; if (ii >= 0 && ii < W) { s += src[j * W + ii]; n++; } } t[j * W + i] = s / n; }
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) { let s = 0, n = 0; for (let k = -R; k <= R; k++) { const jj = j + k; if (jj >= 0 && jj < H) { s += t[jj * W + i]; n++; } } o[j * W + i] = s / n; }
    return o;
  };
  const soft = blur(heath);
  const data = new Uint8Array(W * H * 4);
  for (let i = 0; i < W * H; i++) {
    data[i * 4] = Math.min(255, Math.round((d[i] / 3) * M / 64 * 255));       // r: metres from the turf / 64
    data[i * 4 + 1] = Math.round(soft[i] * 255);                              // g: heath
    data[i * 4 + 2] = turf[i] * 255;                                          // b: on the turf
    data[i * 4 + 3] = Math.min(255, Math.round((inner[i] / 3) * M / 32 * 255));   // a: metres from the infield / 32
  }
  return { x0, z0, x1: x0 + W * M, z1: z0 + H * M, W, H, data };
}
function siteAt(x, z) {                                   // { dist (m), heath 0..1 }, as the shader reads the map
  const fx = (x - S.x0) / M - 0.5, fz = (z - S.z0) / M - 0.5, i = Math.max(0, Math.min(S.W - 2, Math.floor(fx))), j = Math.max(0, Math.min(S.H - 2, Math.floor(fz)));
  const a = Math.max(0, Math.min(1, fx - i)), b = Math.max(0, Math.min(1, fz - j));
  const at = (c, ii, jj) => S.data[(jj * S.W + ii) * 4 + c] / 255;
  const lerp = (c) => (at(c, i, j) * (1 - a) + at(c, i + 1, j) * a) * (1 - b) + (at(c, i, j + 1) * (1 - a) + at(c, i + 1, j + 1) * a) * b;
  return { dist: lerp(0) * 64, heath: lerp(1) };
}
// the same reads the ground shader makes, so the planting sits where the ground is painted for it
const ROT = [0.8, -0.6, 0.6, 0.8];
const fields = (x, z) => {
  const n1 = noiseAt(1, x / 520, z / 520), n2 = noiseAt(3, x / 230 + 0.17, z / 230 + 0.17);
  const rx = (ROT[0] * x + ROT[2] * z) / 61, rz = (ROT[1] * x + ROT[3] * z) / 61, n3 = noiseAt(2, rx, rz);
  const path = Math.abs(noiseAt(0, x / 700 + 0.5, z / 700 + 0.5) - 0.5);
  return { n1, n2, n3, heather: n2 * 0.75 + n3 * 0.25, path };
};

export function init(ctx) {
  CTX = ctx;
  N = makeNoise();
  const nt = new THREE.DataTexture(N.data, N.size, N.size, THREE.RGBAFormat);
  nt.wrapS = nt.wrapT = THREE.RepeatWrapping; nt.magFilter = THREE.LinearFilter; nt.minFilter = THREE.LinearMipmapLinearFilter;
  nt.generateMipmaps = true; nt.anisotropy = 8; nt.colorSpace = THREE.NoColorSpace; nt.needsUpdate = true;
  U.upNoise.value = nt;
  const off = (q.get("cloudAt") || "").split(",").map(Number);
  if (off.length === 2 && off.every(Number.isFinite)) U.upOff.value.set(off[0], off[1]);
  if (LOOK.table) {
    // The board follows the course: the round course and the stands, with a margin, as one many-sided shape (the
    // straight mile runs off its edge, as on the printed board). Worked out as the tightest outline round them.
    const pts = ctx.COURSE.track.surface[0].filter(([x]) => x < 900).concat([[-290, 215], [900, 215], [900, -40]]);
    const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const sorted = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]), lo = [], hi = [];
    for (const p of sorted) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p); }
    for (const p of sorted.slice().reverse()) { while (hi.length >= 2 && cross(hi[hi.length - 2], hi[hi.length - 1], p) <= 0) hi.pop(); hi.push(p); }
    let hull = lo.slice(0, -1).concat(hi.slice(0, -1));
    // fewer, longer sides: drop corners that barely turn
    for (let again = true; again && hull.length > 5;) {
      again = false;
      for (let i = 0; i < hull.length; i++) {
        const a = hull[(i + hull.length - 1) % hull.length], b = hull[i], c = hull[(i + 1) % hull.length];
        const turn = Math.abs(cross(a, b, c)) / (Math.hypot(b[0] - a[0], b[1] - a[1]) * Math.hypot(c[0] - b[0], c[1] - b[1]) || 1);
        if (turn < 0.2 || Math.hypot(c[0] - b[0], c[1] - b[1]) < 90) { hull.splice(i, 1); again = true; break; }
      }
    }
    // push every side out by d metres: the corners are where neighbouring sides, moved out, meet
    const grow = (poly, d) => {
      const n = poly.length, lines = poly.map((a, i) => { const b = poly[(i + 1) % n], L = Math.hypot(b[0] - a[0], b[1] - a[1]), nx = (b[1] - a[1]) / L, nz = -(b[0] - a[0]) / L; return [a[0] + nx * d, a[1] + nz * d, b[0] - a[0], b[1] - a[1]]; });
      return lines.map((l, i) => { const m = lines[(i + n - 1) % n], den = m[2] * l[3] - m[3] * l[2], t = ((l[0] - m[0]) * l[3] - (l[1] - m[1]) * l[2]) / den; return [m[0] + m[2] * t, m[1] + m[3] * t]; });
    };
    const edge = grow(hull, 125), n = edge.length;
    const planes = edge.map((a, i) => { const b = edge[(i + 1) % n], L = Math.hypot(b[0] - a[0], b[1] - a[1]), nx = -(b[1] - a[1]) / L, nz = (b[0] - a[0]) / L; return new THREE.Plane(new THREE.Vector3(nx, 0, nz), -(nx * a[0] + nz * a[1])); });
    BOARD = { edge, planes, grow, inside: (x, z, m = 0) => planes.every((p) => p.normal.x * x + p.normal.z * z + p.constant > m) };
    ctx.renderer.localClippingEnabled = true;
  }
  if (has("relight")) {
    // the sun stands where the look says: the view's own sun (the horses', crowd's and trees' light, and the field's
    // moving shadows) follows; the sky's light and the ground's bounce take the look's colours
    ctx.sunOffset.copy(U.upSun.value).multiplyScalar(160);
    const sc = v3(LOOK.sunCol), sp = Math.max(sc.x, sc.y, sc.z);
    ctx.sun.color.setRGB(sc.x / sp, sc.y / sp, sc.z / sp); ctx.sun.intensity = Math.PI * sp;
    const ak = v3(LOOK.ambSky), ap = Math.max(ak.x, ak.y, ak.z), ag = v3(LOOK.ambGnd);
    ctx.hemi.color.setRGB(ak.x / ap, ak.y / ap, ak.z / ap); ctx.hemi.groundColor.setRGB(ag.x / ap, ag.y / ap, ag.z / ap); ctx.hemi.intensity = Math.PI * ap;
    ctx.renderer.toneMappingExposure *= LOOK.exposure;
  }
  // things this file doesn't shade keep the view's plain haze: give it the look's strength and reach
  THREE.ShaderChunk.fog_fragment = `#ifdef USE_FOG
    float fogFactor = ${LOOK.haze[0].toFixed(3)} * (1.0 - exp(-max(vFogDepth - fogNear, 0.0) / fogFar));
    gl_FragColor.rgb = mix(gl_FragColor.rgb, fogColor, fogFactor);
  #endif`;
  if (ctx.scene.fog) { ctx.scene.fog.near = LOOK.haze[1]; ctx.scene.fog.far = LOOK.haze[2]; }
  if (has("sky")) newSky(ctx);
  console.log("uplift look:", LOOK_ID, OFF.filter(Boolean).length ? "without " + OFF.join(",") : "");
}
// the site map needs to know where the festival's pieces stand, so it is made once the course's files are in
function site(dressing) {
  S = makeSite(CTX.COURSE, dressing);
  const st = new THREE.DataTexture(S.data, S.W, S.H, THREE.RGBAFormat);
  st.magFilter = st.minFilter = THREE.LinearFilter; st.colorSpace = THREE.NoColorSpace; st.needsUpdate = true;
  U.upSite.value = st; U.upArea.value.set(S.x0, S.z0, S.x1, S.z1);
}
// A galloping horse leans into a turn: the tighter the turn and the faster it goes, the more (a little more than
// life, so it reads from a TV camera). turn: how fast the course's direction changes here, radians a metre.
export const lean = (turn, v) => THREE.MathUtils.clamp(Math.atan((v * v * turn) / 9.81) * LEAN, -0.3, 0.3);
const LEAN = Number(q.get("lean") ?? 1.7);
const _hz = new THREE.Color();
export function update(t, camera) {
  U.upTime.value = t;
  // a long lens looks through a lot of air: thin the haze for it, or the far rail washes out (as the view's own haze does)
  if (camera) U.upHaze.value.x = LOOK.haze[0] * THREE.MathUtils.clamp(camera.fov / 26, 0.28, 1);
  // things this file doesn't shade (the turf thrown up by hooves) take the view's own haze: keep its colour the look's
  if (CTX.scene.fog) { const h = U.upHazeCol.value; CTX.scene.fog.color.setRGB(h.x, h.y, h.z, THREE.LinearSRGBColorSpace); }
}

// ---------- Shaders ----------
function chain(mat, key, fn) {
  const prev = mat.onBeforeCompile, prevKey = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, r) => { if (prev) prev.call(mat, sh, r); fn(sh); };
  mat.customProgramCacheKey = () => (prevKey ? prevKey.call(mat) : "") + "|up:" + key;
  mat.userData.up = key;
  return mat;
}
const COMMON = `
uniform sampler2D upSite, upNoise, upCrowd, upSh1, upSh2;
uniform mat4 upShM1, upShM2;
uniform vec4 upArea, upCrowdArea, upHaze, upShT;
uniform vec3 upHorizon, upSun, upSunCol, upAmbSky, upAmbGnd, upGndSun, upGndShade, upLitTint, upShadeTint, upCrowdShade, upHazeCol, upHazeSun;
uniform vec2 upOff; uniform float upTime, upCloudK, upCloudCover, upRim, upHazeTop;
varying vec3 vUpP; varying vec3 vUpN; varying float vUpH;
const vec3 UPLUM = vec3(0.3, 0.59, 0.11);
// soft cloud shadows: big shapes a few hundred metres across, drifting with a light wind; 0 in the sun, 1 in shade
float upCloud(vec2 w) {
  vec2 p = w + upOff + upTime * vec2(4.6, 1.9);
  float a = texture2D(upNoise, p / 1500.0).r, b = texture2D(upNoise, p / 620.0 + 0.31).g;
  return smoothstep(upCloudCover, upCloudCover + 0.11, a * 0.6 + b * 0.4) * upCloudK;
}
// Is the sun on this point? The two shadow pictures (the home straight, sharp; the whole course, softer), each read
// nine times round the point so shadows have a soft edge. 1 in the sun, 0 in shadow.
float upMapVis(sampler2D m, mat4 M, vec3 p, float tx, float bias) {
  vec4 c = M * vec4(p, 1.0); vec3 s = c.xyz * 0.5 + 0.5;
  if (s.x < 0.004 || s.x > 0.996 || s.y < 0.004 || s.y > 0.996 || s.z > 1.0) return -1.0;
  float lit = 0.0;
  for (int j = -1; j <= 1; j++) for (int i = -1; i <= 1; i++) lit += step(s.z - bias, texture2D(m, s.xy + vec2(float(i), float(j)) * tx * 1.4).r);
  return lit / 9.0;
}
float upVis(vec3 p, vec3 n) {
  vec3 o = p + n * 0.3 + upSun * 0.3;
  float a = upMapVis(upSh1, upShM1, o, upShT.x, upShT.z);
  if (a < 0.0) { a = upMapVis(upSh2, upShM2, o + n * 0.5 + upSun * 0.5, upShT.y, upShT.w); if (a < 0.0) a = 1.0; }
  return a * (1.0 - upCloud(p.xz));
}
// The haze, in place of the view's plain one: it builds with distance, and towards the sun it is thicker and takes
// the sun's colour, so the far side of the course sits back in layers.
vec3 upHazed(vec3 col, float depth) {
  vec3 vd = normalize(vUpP - cameraPosition);
  float s = pow(max(dot(vd, upSun), 0.0), 3.0);
  float f = upHaze.x * (1.0 - exp(-max(depth - upHaze.y, 0.0) / upHaze.z)) * (1.0 + upHaze.w * s);
  f *= mix(1.0, upHazeTop, smoothstep(0.0, 45.0, vUpP.y));          // mist lies low: roofs and tree tops stand clear of it
  col = mix(col, mix(upHazeCol, upHazeSun, s), min(f, 0.96));
  return mix(col, upHorizon, smoothstep(1300.0, 3600.0, depth) * step(0.001, upHaze.x));   // the far ground meets the sky's own horizon
}
`;
const HAZE = `#ifdef USE_FOG
  gl_FragColor.rgb = upHazed(gl_FragColor.rgb, vFogDepth);
#endif`;
const f3 = (c) => `vec3(${c.map((v) => v.toFixed(4)).join(", ")})`;
const lin = (hex) => { const c = new THREE.Color(hex); return [c.r, c.g, c.b]; };
// The ground. which: "turf" (the course's turf beyond the baked ground), "far" (plain grass), "baked" (the baked ground).
// The ground is drawn in its own colours (no lamp on it), so here it is told where the sun reaches it.
export function patchGround(mat, which) {
  const nap = LOOK.brushed || 0;
  const heath = has("heath") && which !== "turf" && !nap, turf = has("turf") && which !== "far" && !nap, crowd = has("crowd"), relight = has("relight");
  const lawn = (CTX.lawn || [0.5988, 0.7357, 0.4041]);
  const body = `
  { vec2 w = vUpP.xz;
    vec4 sm = texture2D(upSite, (w - upArea.xy) / (upArea.zw - upArea.xy));
    float dist = sm.r * 64.0, off = 1.0 - sm.b;
    float n1 = texture2D(upNoise, w / 520.0).g;
    float n3 = texture2D(upNoise, mat2(0.8, -0.6, 0.6, 0.8) * w / 61.0).b;
    ${relight && which === "baked" ? `
    { // the bake painted soft shadows on this ground for the sun it was baked under: lift them out (the dark at the
      // very foot of things stays), so the look's own sun can lay its shadows
      float bl = dot(diffuseColor.rgb, UPLUM), ref = mix(0.5, 0.17, sm.b);
      diffuseColor.rgb *= clamp(ref / max(bl, 0.04), 1.0, 1.9); }` : ""}
    ${heath ? `
    float n2 = texture2D(upNoise, w / 230.0 + 0.17).a, n4 = texture2D(upNoise, w / 13.0).b;
    float lum = ${which === "baked" ? "clamp(dot(diffuseColor.rgb, UPLUM) / 0.58, 0.0, 1.1)" : "1.0"};
    // the mown verge beside the rail, cut in bands along it; its edge wanders a little
    float ride = 1.0 - smoothstep(${(RIDE - 0.4).toFixed(1)}, ${(RIDE + 0.4).toFixed(1)}, dist + (n3 - 0.5) * 1.6);
    vec3 lawn = ${f3(lawn)} * (1.0 + 0.055 * cos(dist * 3.14159 / 2.5));
    // rough grass in two greens, dappled; straw where it has dried; a blush of heather here and there
    vec3 rough = mix(${f3(lin("#6c8a39"))}, ${f3(lin("#98ab52"))}, smoothstep(0.3, 0.7, n3)) * (0.88 + 0.24 * n4);
    rough = mix(rough, ${f3(lin("#c4b96c"))}, 0.65 * smoothstep(0.55, 0.72, n1 * 0.55 + n4 * 0.45));
    float hz = smoothstep(0.58, 0.66, n2 * 0.75 + n3 * 0.25);
    vec3 heathC = mix(rough, ${f3(lin("#94779f"))}, ${(LOOK.heather ?? 0.5).toFixed(2)} * hz * smoothstep(0.35, 0.6, n4));
    // mown paths winding through it
    float pth = 1.0 - smoothstep(0.011, 0.017, abs(texture2D(upNoise, w / 700.0 + 0.5).r - 0.5));
    heathC = mix(heathC, lawn * 1.03, pth);
    diffuseColor.rgb = mix(diffuseColor.rgb, mix(heathC, lawn, ride) * lum, sm.g * step(0.5, off));
    // the foot of the rail: a little shade where the turf meets the ground beside it
    diffuseColor.rgb *= 1.0 - 0.13 * step(0.5, off) * (1.0 - smoothstep(0.0, 1.8, dist));` : ""}
    ${turf ? `{ float onT = ${which === "turf" ? "1.0" : "sm.b"};
      diffuseColor.rgb *= 1.0 + onT * (0.09 * n1 - 0.045);       // nothing big is one flat colour
      // where the field runs, a few metres off the inside rail, the turf is a shade paler and drier
      float inD = sm.a * 32.0, worn = onT * smoothstep(0.3, 1.6, inD) * (1.0 - smoothstep(3.0, 7.5, inD + (n3 - 0.5) * 3.0));
      diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(1.16, 1.07, 0.86), worn * 0.55);
      // and it is cut up by hooves: small dark prints, thickest on that strip, a scatter across the rest
      float print = smoothstep(0.8, 0.87, texture2D(upNoise, w / 6.0 + 0.4).b) * onT * (0.08 + 0.92 * worn);
      diffuseColor.rgb *= 1.0 - 0.22 * print;
      // mown grass answers the light: looking towards the sun it glows paler and warmer, looking away it is deeper
      // and cooler; and it lightens into the distance, as the blades hide the earth between them
      vec3 V = normalize(vec3(cameraPosition.x - w.x, cameraPosition.y, cameraPosition.z - w.y));
      float back = dot(normalize(-V.xz + 1e-5), normalize(upSun.xz)) * 0.5 + 0.5, graze = pow(1.0 - clamp(V.y, 0.0, 1.0), 2.0);
      diffuseColor.rgb *= mix(vec3(1.0), mix(vec3(0.93, 0.965, 1.0), vec3(1.10, 1.07, 0.90), back) * (1.0 + 0.12 * graze), onT * 0.85); }` : ""}
    ${nap ? `{ // the brushed ground: one soft surface. A fine grain; and a nap, the pile lying this way and that after a hand has
      // brushed it: broad soft clouds with wispy edges, finer clouds inside them, faint strokes along the brushing.
      // On the mown turf the same, much quieter, so the lanes still show.
      float onT = ${which === "turf" ? "1.0" : which === "far" ? "0.0" : "sm.b"};
      // its colours: the turf a soft sage (keeping its mown lanes and the bake's shading); the rough ground inside the
      // course a paler sage drifting to straw
      float lum0 = dot(diffuseColor.rgb, UPLUM);
      diffuseColor.rgb = mix(diffuseColor.rgb, ${f3(lin("#8fad79"))} * (lum0 / 0.33), 0.8 * onT);
      ${which === "turf" ? "" : `float hm = sm.g * step(0.5, off);
      vec3 rough = mix(${f3(lin("#a3bb8a"))}, ${f3(lin("#b9c694"))}, smoothstep(0.3, 0.7, n1));
      diffuseColor.rgb = mix(diffuseColor.rgb, rough * clamp(lum0 / ${which === "baked" ? "0.5" : "0.33"}, 0.6, 1.12), hm);`}
      vec2 wv = w + (texture2D(upNoise, w / 400.0).rg - 0.5) * 28.0;
      float a = texture2D(upNoise, wv / 42.0).r, b = texture2D(upNoise, wv / 13.0 + 0.3).g;
      float st = texture2D(upNoise, vec2(wv.x * 0.25, wv.y * 1.5) / 9.0).a;
      float g1 = texture2D(upNoise, w / 11.0).b, g2 = texture2D(upNoise, w / 3.6 + 0.6).b;
      float k = ${nap.toFixed(3)} * mix(0.8, 0.45, onT), gk = mix(1.0, 0.5, onT);
      float tone = mix(1.0 - k, 1.0 + k * 0.8, smoothstep(0.34, 0.66, a));
      tone *= 1.0 + k * 0.45 * (smoothstep(0.3, 0.7, b) * 2.0 - 1.0);
      tone *= 1.0 + k * 0.25 * (smoothstep(0.3, 0.7, st) * 2.0 - 1.0);
      tone *= 1.0 + gk * (0.08 * (smoothstep(0.3, 0.7, g1) * 2.0 - 1.0) + 0.06 * (smoothstep(0.3, 0.7, g2) * 2.0 - 1.0));
      diffuseColor.rgb *= tone; }` : ""}
    ${relight ? `float upV = upVis(vec3(w.x, vUpP.y, w.y), vec3(0.0, 1.0, 0.0));` : `float upV = 1.0 - upCloud(w);`}
    ${crowd ? `{ vec2 cu = (w - upCrowdArea.xy) / (upCrowdArea.zw - upCrowdArea.xy);        // the people's shadows
      if (cu.x > 0.0 && cu.x < 1.0 && cu.y > 0.0 && cu.y < 1.0) { vec4 cs = texture2D(upCrowd, cu);
        diffuseColor.rgb *= mix(vec3(1.0), upCrowdShade, max(min(cs.r, 1.0) * 0.85 * upV, cs.g * 0.5)); } }` : ""}
    diffuseColor.rgb *= mix(upGndShade, upGndSun, upV);
    ${q.get("updebug") === "vis" ? "diffuseColor.rgb = vec3(upV);" : ""}
  }`;
  if (BOARD) mat.clippingPlanes = BOARD.planes;              // the table look: the ground stops at the board's edge
  return chain(mat, "ground-" + which + LOOK_ID + OFF.join(""), (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace("#include <common>", "#include <common>\nvarying vec3 vUpP; varying vec3 vUpN; varying float vUpH;")
      .replace("#include <fog_vertex>", "#include <fog_vertex>\n{ vUpP = (modelMatrix * vec4(transformed, 1.0)).xyz; vUpN = vec3(0.0, 1.0, 0.0); vUpH = 0.0; }");
    sh.fragmentShader = sh.fragmentShader.replace("#include <common>", "#include <common>\n" + COMMON)
      .replace("#include <color_fragment>", "#include <color_fragment>\n" + body)
      .replace("#include <fog_fragment>", HAZE);
  });
}
// Things lit by the view's own lamps (trees, hedge, boards, crowd, rails, horses): the sun reaches them only where the
// shadow pictures say it does (so the stand's shadow falls across the crowd, and trees shade each other), their sunlit
// and shaded sides take different colours, and a thread of sunlight runs round their edges against the light.
const TONE_LIT = `
  { vec3 upNv = normalize(normal), upNw = normalize(transpose(mat3(viewMatrix)) * upNv);
    float upV = upVis(vUpP, upNw);
    outgoingLight -= reflectedLight.directDiffuse * (1.0 - upV);
    float upD = dot(reflectedLight.directDiffuse, UPLUM) * upV, upI = dot(reflectedLight.indirectDiffuse, UPLUM);
    float upLit = smoothstep(0.08, 0.5, upD / (upD + upI + 1e-4));
    outgoingLight *= mix(upShadeTint, upLitTint, upLit);
    float upRimK = pow(1.0 - max(dot(upNv, normalize(vViewPosition)), 0.0), 3.0) * smoothstep(-0.35, 0.45, dot(upNw, upSun)) * upV;
    outgoingLight += diffuseColor.rgb * upSunCol * upRimK * upRim; }`;
// Baked scenery (the stand, the site pieces, the finish): Blender's light is kept only as how open each spot is to
// the sky (deep under a balcony: dark; out in the open: full), and the sun is worked out afresh: its angle on each
// wall, with a clean step from shade into light, and its cast shadows. Walls darken a little where they meet the ground.
const TONE_BAKED = `
  { float upL = dot(reflectedLight.indirectDiffuse, UPLUM);
    float upOpen = min(upL / (1.0 + upL / 0.45) / 0.27, 1.1);
    vec3 upN = normalize(vUpN); if (!gl_FrontFacing) upN = -upN;
    float upNL = dot(upN, upSun);
    float upV = upNL > 0.0 ? upVis(vUpP, upN) : 0.0;
    float upLit = smoothstep(0.0, 0.28, upNL) * (0.78 + 0.22 * upNL) * upV;
    vec3 upAmb = mix(upAmbGnd, upAmbSky, upN.y * 0.5 + 0.5) * upOpen;
    reflectedLight.indirectDiffuse = (upAmb * mix(upShadeTint, vec3(1.0), upLit) + upSunCol * upLit * mix(0.75, 1.0, min(upOpen, 1.0))) * mix(0.84, 1.0, smoothstep(0.0, 2.6, vUpP.y)); }`;
const TONE_CROWD = `
  { outgoingLight *= mix(0.7, 1.06, smoothstep(0.0, 1.55, vUpH));              // darker towards the feet: the mass has a base
    #ifdef USE_FOG
    float upFar = smoothstep(70.0, 330.0, vFogDepth);                            // far off the speckle calms into a mass
    outgoingLight = mix(outgoingLight, vec3(dot(outgoingLight, UPLUM)) * vec3(1.0, 0.985, 0.97), 0.4 * upFar);
    #endif
  }`;
// The trees of the soft look ("C and F" in the workshop): each graded up its height, dark at the foot of the crown to
// light at the top, keeping a little of its own leaf-to-leaf tone; then, further off, paler and flatter, in layers.
const TREE_COL = `
  { if (diffuseColor.g > diffuseColor.r * 0.75) {                                  // leaves (the poplars' yellow tips too), not bark
      float upT = smoothstep(2.4, 12.6, vUpH);
      vec3 upG = mix(${f3(lin("#3d6e58"))}, ${f3(lin("#62996a"))}, smoothstep(0.0, 0.5, upT)); upG = mix(upG, ${f3(lin("#a6cb92"))}, smoothstep(0.5, 1.0, upT));
      diffuseColor.rgb = upG * 0.97 * clamp(dot(diffuseColor.rgb, UPLUM) / 0.27, 0.6, 1.35); } }`;
// Their form (owner, 11 Nov: "the trees in the 3d look flat again"): under this look's soft light every side of a crown
// was nearly the same tone. Each lobe is modelled again: fuller and warmer on the side towards the sun, deeper and
// cooler away from it, darker underneath where it hangs over the lobe below. Only far off do they ease into flat tones.
const TREE_FAR = `
  { vec3 upTn = normalize(transpose(mat3(viewMatrix)) * normalize(normal));
    float upSide = smoothstep(-0.5, 0.8, dot(upTn, upSun)), upUnder = smoothstep(-0.95, 0.45, upTn.y);
    vec3 upForm = mix(vec3(0.6, 0.67, 0.7), vec3(1.12, 1.08, 0.98), upSide) * mix(0.72, 1.0, upUnder);
    #ifdef USE_FOG
    float upFarT = smoothstep(260.0, 900.0, vFogDepth);
    outgoingLight *= mix(upForm, vec3(0.92), 0.55 * upFarT);
    outgoingLight = mix(outgoingLight, ${f3(lin("#bfd0b4"))} * (0.62 + 0.38 * smoothstep(2.4, 10.6, vUpH)), 0.4 * upFarT);
    #else
    outgoingLight *= upForm;
    #endif
  }`;
export function patchLit(mat, kind = "") {
  if (mat.userData.up) return mat;
  const relight = has("relight"), crowd = kind === "crowd" && has("crowd"), tree = kind === "tree" && LOOK.trees;
  const baked = mat.isMeshBasicMaterial;                       // baked scenery: unlit colour x Blender's light
  return chain(mat, "lit" + kind + LOOK_ID + OFF.join(""), (sh) => {
    Object.assign(sh.uniforms, U);
    sh.vertexShader = sh.vertexShader.replace("#include <common>", "#include <common>\nvarying vec3 vUpP; varying vec3 vUpN; varying float vUpH; varying float vUpR;")
      .replace("#include <begin_vertex>", `#include <begin_vertex>
      vUpR = 0.5;
      ${tree ? `#ifdef USE_INSTANCING
        vUpR = fract(sin(dot(instanceMatrix[3].xz, vec2(12.9898, 78.233))) * 43758.5453);
        transformed.y *= mix(0.8, 1.3, fract(vUpR * 7.31 + 0.17));
      #endif` : ""}`)
      .replace("#include <fog_vertex>", `#include <fog_vertex>
      { vUpP = transpose(mat3(viewMatrix)) * (mvPosition.xyz - viewMatrix[3].xyz); vUpH = position.y;
        vec3 upn = normal;
        #ifdef USE_BATCHING
          upn = mat3(batchingMatrix) * upn;
        #endif
        #ifdef USE_INSTANCING
          upn = mat3(instanceMatrix) * upn;
        #endif
        vUpN = mat3(modelMatrix) * upn; }`);
    let f = sh.fragmentShader.replace("#include <common>", "#include <common>\n" + COMMON).replace("#include <fog_fragment>", HAZE);
    if (relight && baked && mat.lightMap) f = f.replace("reflectedLight.indirectDiffuse *= diffuseColor.rgb;", TONE_BAKED + "\n reflectedLight.indirectDiffuse *= diffuseColor.rgb;");
    if (!baked && tree) f = f.replace("#include <common>", "#include <common>\nvarying float vUpR;").replace("#include <color_fragment>", "#include <color_fragment>\n" + TREE_COL);
    if (!baked) f = f.replace("#include <opaque_fragment>", (relight ? TONE_LIT : "") + (crowd ? TONE_CROWD : "") + (tree ? TREE_FAR : "") + "\n#include <opaque_fragment>");
    sh.fragmentShader = f;
  });
}

// ---------- The trees' broken tops ----------
// Owner, 11 Nov, with a television still of Ascot's real trees: "thin them out a bit at upper levels... they're so
// flumpy at the moment... keep a visual block beyond the track... at upper levels more fragmented and varied to allow
// sky in". So in this look a tree is built in two storeys. Its own crown is pressed down into a broad low mass (with
// the belts' understorey, the solid block). Above it stands a "top" of separate boughs with air between them. There
// are a dozen tops, made here once; each tree takes one, turned its own way, and the trees also differ in height (in
// the shader), so the top line of a belt is broken and the sky comes through it.
export function treeShape(t) { if (LOOK.trees && !t.scrub && !t.topped) { t.topped = true; t.sy = (t.sy || 1) * 0.68; } }
let TOPS = null;
// A top: six to nine boughs, each a loose bunch of flat sprays of leaf (a spray is a small lens-shaped piece, eight
// faces, lying nearly level and tilted its own way). Boughs are large and spread out low down, small and gathered
// in towards the leader; sprays overlap raggedly, so a bough has a broken edge and chinks of sky inside it.
// (Two earlier tries: holes cut in the big crowns in the shader read as torn paper; whole small bush crowns floated
// like balloons.)
function makeTops(light) {                       // light: for trees far from the action, half as many sprays, each a little larger
  let seed = 4711; const rnd = (a = 0, b = 1) => a + (b - a) * ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
  const tops = [], F = [[0, 2, 4], [2, 1, 4], [1, 3, 4], [3, 0, 4], [2, 0, 5], [1, 2, 5], [3, 1, 5], [0, 3, 5]];
  for (let v = 0; v < 12; v++) {
    const pos = [], nor = [], col = [];
    const n = 6 + Math.floor(rnd(0, 3.99)), tall = rnd() < 0.35 ? rnd(1.1, 1.35) : rnd(0.8, 1.05), ring = 5;
    for (let k = -ring; k < n; k++) {
      // the first few boughs sit round the shoulder of the low mass and break its rounded outline; the rest climb
      const f = k < 0 ? 0 : k / (n - 1), a = k * 2.39996 + rnd(-0.5, 0.5);
      const h = k < 0 ? rnd(4.6, 6.2) : 5.9 + 5.6 * Math.pow(f, 0.85) * tall + rnd(-0.4, 0.4), r = k < 0 ? rnd(2.8, 4.4) : Math.pow(1 - f, 0.7) * rnd(1.2, 3.6);
      const bx = Math.cos(a) * r, bz = Math.sin(a) * r, size = (k < 0 ? 0.8 : 1.0 - 0.5 * f) * rnd(0.85, 1.2) * (light ? 1.3 : 1), sprays = Math.round((k < 0 ? 6 : 11 - 5 * f) * rnd(0.8, 1.2) * (light ? 0.5 : 1));
      for (let j = 0; j < sprays; j++) {
        // a spray: where in the bough, how big, which way it lies
        const sa = rnd(0, 6.283), sr = Math.sqrt(rnd()) * 1.9 * size, cx = bx + Math.cos(sa) * sr, cz = bz + Math.sin(sa) * sr, cy = h + rnd(-0.9, 0.9) * size - 0.12 * sr * sr;
        const L = rnd(0.65, 1.45) * size, Wd = L * rnd(0.5, 0.8), T = rnd(0.16, 0.34) * size, yaw = rnd(0, 6.283), tilt = rnd(-0.55, 0.55), roll = rnd(-0.4, 0.4), tone = rnd(0.82, 1.16);
        const cyw = Math.cos(yaw), syw = Math.sin(yaw), ct = Math.cos(tilt), st = Math.sin(tilt), cr = Math.cos(roll), sr2 = Math.sin(roll);
        const turn = (x, y, z) => { const y1 = y * ct - z * st, z1 = y * st + z * ct; const x2 = x * cr - y1 * sr2, y2 = x * sr2 + y1 * cr; return [cx + x2 * cyw + z1 * syw, cy + y2, cz - x2 * syw + z1 * cyw]; };
        const j_ = () => rnd(0.75, 1.25);
        const V = [turn(-L * j_(), rnd(-0.1, 0.1), rnd(-0.2, 0.2)), turn(L * j_(), rnd(-0.1, 0.1), rnd(-0.2, 0.2)), turn(rnd(-0.2, 0.2), rnd(-0.1, 0.1), -Wd * j_()), turn(rnd(-0.2, 0.2), rnd(-0.1, 0.1), Wd * j_()), turn(0, T, 0), turn(0, -T * 0.7, 0)];
        for (const [i0, i1, i2] of F) {
          const A = V[i0], B = V[i1], C = V[i2];
          let nx = (B[1] - A[1]) * (C[2] - A[2]) - (B[2] - A[2]) * (C[1] - A[1]), ny = (B[2] - A[2]) * (C[0] - A[0]) - (B[0] - A[0]) * (C[2] - A[2]), nz = (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]);
          const nl = Math.hypot(nx, ny, nz) || 1; nx /= nl; ny /= nl; nz /= nl;
          for (const P of [A, B, C]) {
            // its light and shade: half its own facet, half as if it lay on a rounded bough (soft, not glittery)
            let ox = P[0] - bx, oy = P[1] - (h - 1.2 * size), oz = P[2] - bz; const ol = Math.hypot(ox, oy, oz) || 1;
            let mx = nx * 0.5 + ox / ol * 0.5, my = ny * 0.5 + oy / ol * 0.5, mz = nz * 0.5 + oz / ol * 0.5; const ml = Math.hypot(mx, my, mz) || 1;
            pos.push(P[0], P[1], P[2]); nor.push(mx / ml, my / ml, mz / ml);
            const under = P === V[5] ? 0.72 : 1.0, t = tone * under; col.push(0.17 * t, 0.34 * t, 0.12 * t);
          }
        }
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3)); geo.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3)); geo.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
    tops.push(geo);
  }
  return tops;
}
export function treeTops({ trees, scene, LAYERS, groundY, material, isNear }) {
  if (!LOOK.trees || !has("tops") || !trees.length) return;
  TOPS = TOPS || [makeTops(false), makeTops(true)];
  const hash = (t, k) => { const x = Math.sin(t.x * 12.9898 * k + t.z * 78.233) * 43758.5453; return x - Math.floor(x); };
  const K = TOPS[0].length, by = [...TOPS[0], ...TOPS[1]].map(() => []);
  for (const t of trees) by[(isNear && isNear(t.x, t.z) ? 0 : K) + Math.floor(hash(t, 1.7) * K) % K].push(t);
  const m4 = new THREE.Matrix4(), qt = new THREE.Quaternion(), sc = new THREE.Vector3(), p = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  by.forEach((ts, v) => {
    if (!ts.length) return;
    const inst = new THREE.InstancedMesh(TOPS[v < K ? 0 : 1][v % K], material, ts.length);
    ts.forEach((t, i) => { qt.setFromAxisAngle(up, hash(t, 3.1) * 6.283); const s = t.s * (0.92 + 0.2 * hash(t, 5.3)); inst.setMatrixAt(i, m4.compose(p.set(t.x, groundY(t.x, t.z) + (t.dy || 0), t.z), qt, sc.set(s, s, s))); });
    inst.computeBoundingSphere(); scene.add(inst); LAYERS.trees.push(inst);
  });
}

// ---------- Sky and clouds ----------
// One dome. The sky's colours run from the horizon up; a soft glow and a small bright disc where the sun is; and a
// layer of cloud painted on it in perspective, so the clouds get smaller and closer together towards the horizon and
// drift with the wind: bright at their thin edges, shaded in their thick middles, as clouds are from below.
function newSky({ scene }) {
  const old = scene.userData.sky, K = LOOK.sky, c = (hex) => new THREE.Color(hex);
  const mat = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, fog: false, toneMapped: false,
    stencilWrite: old.material.stencilWrite, stencilRef: 0, stencilFunc: THREE.EqualStencilFunc, stencilZPass: THREE.KeepStencilOp,
    uniforms: { c0: { value: c(K.horizon) }, c1: { value: c(K.mid) }, c2: { value: c(K.top) }, glow: { value: v3(K.glow) }, sunDir: U.upSun,
                cEdge: { value: c(K.edge) }, cBase: { value: c(K.base) }, cover: { value: K.cover }, thick: { value: K.thick },
                upNoise: U.upNoise, upTime: U.upTime },
    vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
    fragmentShader: `uniform vec3 c0, c1, c2, glow, sunDir, cEdge, cBase; uniform float cover, thick, upTime; uniform sampler2D upNoise; varying vec3 vP;
      void main(){
        vec3 d = normalize(vP); float h = max(d.y, 0.0);
        vec3 c = mix(c0, c1, smoothstep(0.0, 0.2, h)); c = mix(c, c2, smoothstep(0.12, 0.8, h));
        float s = max(dot(d, sunDir), 0.0);
        ${K.room ? "gl_FragColor = vec4(c + glow * 0.25 * pow(s, 3.0), 1.0);\n#include <colorspace_fragment>\nreturn;" : ""}
        c += glow * (0.1 * pow(s, 5.0) + 0.32 * pow(s, 60.0));
        // the cloud layer, a flat sheet high overhead seen in perspective
        vec2 p = d.xz / (h + 0.09) * vec2(0.035, 0.07) + upTime * vec2(0.0006, 0.00025);
        float n = texture2D(upNoise, p).r * 0.68 + texture2D(upNoise, p * 2.3 + 0.37).g * 0.32;
        float a = smoothstep(cover, cover + 0.05, n) * smoothstep(0.015, 0.11, h);
        vec3 cl = mix(cEdge, cBase, smoothstep(0.0, 0.22, n - cover) * thick);
        cl += glow * 0.35 * pow(s, 4.0) * (1.0 - smoothstep(0.0, 0.2, n - cover));          // lit edges near the sun
        cl = mix(c0, cl, smoothstep(0.02, 0.16, h));                                            // sinking into the horizon
        c = mix(c, cl, a);
        c += glow * 1.4 * smoothstep(0.9992, 0.99975, s) * (1.0 - a * 0.85);                  // the sun itself
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`,
  });
  old.material = mat;
  const was = scene.userData.cloudMat;                     // the solid cloud shapes give way to the painted layer
  scene.traverse((o) => { if (o.isMesh && o.material === was) o.visible = false; });
}

// ---------- Planting on the heath ----------
// A bush as a model maker's clump foliage: three or four soft lobes grown together, smooth, carrying its own light
// and shade (darker at the foot and in the folds). About 150 triangles. base/tip: its colours low down and on top.
function clump(seed, base, tip, squash = 0.85) {
  let s = seed * 7919 + 13; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  const lobes = [];
  for (let k = 0, n = 3 + (seed % 2); k < n; k++) {
    const a = (k / n) * Math.PI * 2 + rnd() * 1.2, d = k === 0 ? 0 : 0.42 + rnd() * 0.22, r = k === 0 ? 0.62 + rnd() * 0.12 : 0.4 + rnd() * 0.2;
    lobes.push([Math.cos(a) * d, r * 0.5, Math.sin(a) * d, r]);
  }
  const pos = [], nor = [], col = [], A = new THREE.Color(base), B = new THREE.Color(tip), c = new THREE.Color();
  const src = new THREE.IcosahedronGeometry(1, 1).attributes.position;
  lobes.forEach(([cx, cy, cz, r], li) => {
    for (let f = 0; f < src.count; f += 3) {
      if (Math.max(src.getY(f), src.getY(f + 1), src.getY(f + 2)) < -0.45) continue;        // the underside is never seen
      for (let k = 0; k < 3; k++) {
        const nx = src.getX(f + k), ny = src.getY(f + k), nz = src.getZ(f + k);
        const x = cx + nx * r, y = Math.max(0, cy + ny * r) * squash, z = cz + nz * r;
        // shade: the foot, and wherever another lobe crowds this point
        let fold = 1;
        lobes.forEach(([ox, oy, oz, orr], lj) => { if (lj !== li) fold = Math.min(fold, THREE.MathUtils.smoothstep(Math.hypot(x - ox, y / squash - oy, z - oz) / orr, 0.85, 1.5)); });
        const h = THREE.MathUtils.smoothstep(y, 0.05, 0.75);
        c.copy(A).lerp(B, h * h).multiplyScalar((0.62 + 0.38 * h) * (0.7 + 0.3 * fold));
        pos.push(x, y, z); nor.push(nx, ny + 0.35, nz); col.push(c.r, c.g, c.b);
      }
    }
  });
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3)); g.normalizeNormals();
  g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  g.computeBoundingSphere();
  return g;
}
export function plant({ scene, LAYERS, instanceTrees, sunOffset, dressing }) {
  site(dressing);
  if (!has("plants") || !has("heath") || LOOK.brushed) return;
  let s = 20261111; const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  // sizes in metres: w = across (a radius of about half that), h = how tall against its width
  const kinds = {
    heather: { geos: [1, 2].map((k) => clump(k, "#6a5a70", "#c3a6c6", 0.7)), w: [0.9, 1.7], tints: ["#ffffff", "#f2e2f4", "#e2cfe0", "#ffeef8"] },
    gorse:   { geos: [3, 4].map((k) => clump(k, "#3c5a2b", "#d0b23e", 1.0)), w: [1.3, 2.4], tints: ["#ffffff", "#f4f0d2", "#dfecd0"] },
    green:   { geos: [5, 6, 7].map((k) => clump(k, "#44612c", "#9db45a", 0.8)), w: [0.8, 1.9], tints: ["#ffffff", "#eaf0d0", "#d4e6cc", "#f4eccb", "#cfe0d4"] },
  };
  const CELL = 160, cells = new Map(), STEP = 5.5;
  const put = (kind, x, z) => {
    const K = kinds[kind], w = K.w[0] + rnd() * (K.w[1] - K.w[0]), v = Math.floor(rnd() * K.geos.length);
    const key = kind + v + ":" + Math.floor(x / CELL) + ":" + Math.floor(z / CELL);
    if (!cells.has(key)) cells.set(key, { geo: K.geos[v], list: [] });
    cells.get(key).list.push([x, z, w, 0.85 + rnd() * 0.35, rnd() * Math.PI * 2, K.tints[Math.floor(rnd() * K.tints.length)]]);
  };
  // bushes come in twos and threes, the way they grow
  const group = (kind, x, z) => { put(kind, x, z); for (let k = 0, n = Math.floor(rnd() * 3); k < n; k++) put(kind, x + (rnd() - 0.5) * 3.4, z + (rnd() - 0.5) * 3.4); };
  for (let z = S.z0; z < S.z1; z += STEP) for (let x = S.x0; x < S.x1; x += STEP) {
    const px = x + (rnd() - 0.5) * STEP, pz = z + (rnd() - 0.5) * STEP, site = siteAt(px, pz);
    if (site.heath < 0.75 || site.dist < RIDE + 2) continue;
    const low = site.dist < LOW;
    const f = fields(px, pz);
    if (f.path < 0.024) continue;                           // the mown paths stay clear
    // thickest in a border 7 to 35 m inside the rail, where the cameras look; thinner out on the open heath
    const r = rnd() / (site.dist < 35 ? 3.2 : 1), hz = THREE.MathUtils.smoothstep(f.heather, 0.58, 0.66);
    const gz = THREE.MathUtils.smoothstep(noiseAt(0, px / 310 + 0.7, pz / 310 + 0.2) * 0.7 + f.n3 * 0.3, 0.56, 0.68);
    if (hz > 0.3 && r < 0.22 * hz) group(rnd() < 0.4 ? "heather" : rnd() < 0.25 && !low ? "gorse" : "green", px, pz);
    else if (gz > 0.3 && r < 0.2 * gz) group(low ? "green" : "gorse", px, pz);
    else if (r < 0.05) group(rnd() < 0.12 ? "heather" : !low && rnd() < 0.25 ? "gorse" : "green", px, pz);
  }
  const mat = patchLit(new THREE.MeshLambertMaterial({ vertexColors: true }));
  const m4 = new THREE.Matrix4(), qt = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), p = new THREE.Vector3(), sc = new THREE.Vector3(), col = new THREE.Color();
  let n = 0;
  for (const { geo, list } of cells.values()) {
    const inst = new THREE.InstancedMesh(geo, mat, list.length);
    list.forEach(([x, z, w, tall, turn, tint], i) => {
      inst.setMatrixAt(i, m4.compose(p.set(x, 0, z), qt.setFromAxisAngle(up, turn), sc.set(w, w * tall, w)));
      inst.setColorAt(i, col.set(tint));
    });
    inst.computeBoundingSphere(); scene.add(inst); LAYERS.trees.push(inst); n += list.length;
  }
  // a few clusters of small trees (hawthorn-sized: nothing tall in the middle of the course)
  const small = [], names = ["oak_a", "oak_b", "oak_c", "wide_a", "wide_b"];
  for (let tries = 0, made = 0; tries < 4000 && made < 26; tries++) {
    const x = S.x0 + rnd() * (S.x1 - S.x0), z = S.z0 + rnd() * (S.z1 - S.z0), site = siteAt(x, z);
    if (site.heath < 0.9 || site.dist < 45 || fields(x, z).path < 0.03) continue;
    if (small.some((t) => Math.hypot(t.x - x, t.z - z) < 70)) continue;
    made++;
    for (let k = 0, c = 2 + Math.floor(rnd() * 4); k < c; k++) {
      const tx = x + (rnd() - 0.5) * 16, tz = z + (rnd() - 0.5) * 12, sz = 0.36 + rnd() * 0.24;
      small.push({ x: tx, z: tz, s: sz, tree: names[Math.floor(rnd() * names.length)], turn: rnd() * 360, sy: 0.9 + rnd() * 0.2 });
    }
  }
  if (instanceTrees && small.length) instanceTrees(small);
  console.log("uplift planting:", n, "shrubs,", small.length, "small trees");
}

// The people's shadows, painted once into one image laid over the ground (40 cm a pixel): a soft shadow falling away
// from the sun from each person standing on the ground, and a darker touch at the feet. One lookup in the ground's
// shader; no extra shapes to draw.
function crowdShadows(figs, share, sunOffset) {
  const pts = [];
  for (const F of figs) for (const c of F.cells) {
    const take = Math.round(c.count * share);
    for (let i = c.start; i < c.start + take; i++) if (F.mats[16 * i + 13] < 0.4) pts.push(F.mats[16 * i + 12], F.mats[16 * i + 14]);
  }
  if (!pts.length) return;
  let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
  for (let i = 0; i < pts.length; i += 2) { x0 = Math.min(x0, pts[i]); x1 = Math.max(x1, pts[i]); z0 = Math.min(z0, pts[i + 1]); z1 = Math.max(z1, pts[i + 1]); }
  x0 -= 6; x1 += 6; z0 -= 6; z1 += 6;
  const R = Math.max(0.4, (x1 - x0) / 4096, (z1 - z0) / 4096);
  const c = document.createElement("canvas"); c.width = Math.ceil((x1 - x0) / R); c.height = Math.ceil((z1 - z0) / R);
  const g = c.getContext("2d"); g.fillStyle = "#000"; g.fillRect(0, 0, c.width, c.height);
  const sp = document.createElement("canvas"); sp.width = sp.height = 32;
  const sg = sp.getContext("2d"), gr = sg.createRadialGradient(16, 16, 1, 16, 16, 15.5);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.5, "rgba(255,255,255,0.7)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  sg.fillStyle = gr; sg.fillRect(0, 0, 32, 32);
  const tint = (col) => { const t = document.createElement("canvas"); t.width = t.height = 32; const tg = t.getContext("2d"); tg.drawImage(sp, 0, 0); tg.globalCompositeOperation = "source-in"; tg.fillStyle = col; tg.fillRect(0, 0, 32, 32); return t; };
  const spR = tint("#ff0000"), spG = tint("#00ff00");
  g.globalCompositeOperation = "lighter";
  const flat = new THREE.Vector2(-sunOffset.x, -sunOffset.z).normalize(), ang = Math.atan2(flat.y, flat.x);
  const L = Math.min(1.7 * Math.hypot(sunOffset.x, sunOffset.z) / Math.max(sunOffset.y, 1), 9) + 0.5;      // a person's shadow, metres
  for (let i = 0; i < pts.length; i += 2) {
    g.setTransform(1, 0, 0, 1, (pts[i] - x0) / R, (pts[i + 1] - z0) / R); g.rotate(ang);
    g.globalAlpha = 0.5; g.drawImage(spR, -0.3 / R, -0.32 / R, L / R, 0.64 / R);        // red: the cast shadow
    g.globalAlpha = 0.45; g.drawImage(spG, -0.36 / R, -0.36 / R, 0.72 / R, 0.72 / R);     // green: the dark touch at the feet
  }
  const t = new THREE.CanvasTexture(c); t.flipY = false; t.colorSpace = THREE.NoColorSpace; t.anisotropy = 4;
  U.upCrowd.value = t; U.upCrowdArea.value.set(x0, z0, x0 + c.width * R, z0 + c.height * R);
  console.log("uplift crowd shadows:", pts.length / 2, "people,", c.width, "x", c.height);
}

// ---------- The shadow pictures ----------
// Taken once, from the sun: how far the sun's light gets before it meets the stand, a site piece, a tree or a bush.
// Two of them: the home straight in detail, and the whole course more coarsely. After this nothing is drawn for
// shadows on the scenery: each surface just looks up whether the sun reaches it.
function shadowPictures({ renderer, scene, LAYERS, quality }) {
  const LAYER = 5, dir = U.upSun.value;
  for (const key of ["trees", "buildings"]) for (const root of LAYERS[key]) root.traverse((o) => {
    if (o.isMesh && o.material && !o.material.transparent) o.layers.enable(LAYER);
  });
  const depthMat = new THREE.MeshBasicMaterial({ colorWrite: false, side: THREE.DoubleSide });
  const v = new THREE.Vector3();
  const take = (size, [x0, z0, x1, z1], top) => {
    const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 10), C = new THREE.Vector3((x0 + x1) / 2, 0, (z0 + z1) / 2);
    cam.position.copy(C).addScaledVector(dir, 3000); cam.lookAt(C); cam.updateMatrixWorld(true);
    const inv = cam.matrixWorld.clone().invert();
    let l = Infinity, r = -Infinity, b = Infinity, t = -Infinity, n = Infinity, f = -Infinity;
    for (const x of [x0, x1]) for (const y of [0, top]) for (const z of [z0, z1]) {
      v.set(x, y, z).applyMatrix4(inv); l = Math.min(l, v.x); r = Math.max(r, v.x); b = Math.min(b, v.y); t = Math.max(t, v.y); n = Math.min(n, -v.z); f = Math.max(f, -v.z);
    }
    Object.assign(cam, { left: l, right: r, bottom: b, top: t, near: Math.max(1, n - 700), far: f + 4 }); cam.updateProjectionMatrix();
    cam.layers.set(LAYER);
    const dt = new THREE.DepthTexture(size, size, THREE.UnsignedIntType); dt.minFilter = dt.magFilter = THREE.NearestFilter;
    const rt = new THREE.WebGLRenderTarget(size, size, { depthBuffer: true, depthTexture: dt, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });
    const om = scene.overrideMaterial, was = renderer.getRenderTarget(), auto = renderer.shadowMap.autoUpdate;
    scene.overrideMaterial = depthMat; renderer.shadowMap.autoUpdate = false;
    renderer.setRenderTarget(rt); renderer.clear(); renderer.render(scene, cam); renderer.setRenderTarget(was);
    scene.overrideMaterial = om; renderer.shadowMap.autoUpdate = auto; renderer.shadowMap.needsUpdate = true;
    return { tex: dt, M: new THREE.Matrix4().multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse), allow: 0.2 / (cam.far - cam.near) };
  };
  const big = quality === "high" ? 4096 : 2048, wide = BOARD ? big : 2048;
  const a = take(big, [-330, -175, 790, 180], 60), b = take(wide, [S.x0, S.z0, BOARD ? 1000 : S.x1, BOARD ? 260 : S.z1], 45);
  U.upSh1.value = a.tex; U.upShM1.value.copy(a.M); U.upSh2.value = b.tex; U.upShM2.value.copy(b.M);
  U.upShT.value.set(1 / big, 1 / wide, a.allow, b.allow);
}

// ---------- Once the scene is built ----------
export function afterBuild({ scene, LAYERS, shadowCatcher, crowd, crowdShare = 1, sunOffset, renderer, quality }) {
  if (!S) site(null);
  if (has("crowd") && crowd) crowdShadows(crowd, crowdShare, sunOffset);
  if (has("relight")) {
    if (shadowCatcher) { shadowCatcher.material.color.set(LOOK.catcher[0]); shadowCatcher.material.opacity = LOOK.catcher[1]; }
    // the trees' painted-on shadows go (the real ones take over); the dark touch round each trunk stays
    for (const o of LAYERS.trees) if (o.isInstancedMesh && o.material.transparent && o.material.map && o.material.isMeshBasicMaterial) {
      const half = o.count / 2, m = new THREE.Matrix4().makeScale(0, 0, 0);
      for (let i = 0; i < half; i++) o.setMatrixAt(i, m);
      o.instanceMatrix.needsUpdate = true; o.material.color.set(LOOK.catcher[0]);
    }
    if (BOARD) {                                             // everything stops at the board's edge
      scene.traverse((o) => { if (o.isMesh && o !== scene.userData.sky) for (const m of Array.isArray(o.material) ? o.material : [o.material]) if (m && !m.isShaderMaterial) { m.clippingPlanes = BOARD.planes; m.needsUpdate = true; } });
      buildTable({ scene, LAYERS });
    }
    shadowPictures({ renderer, scene, LAYERS, quality });
  }
  const seen = new Set();
  // the trees themselves, not the boards and hedge that share their layer
  const isTree = (o) => { const m = Array.isArray(o.material) ? o.material[0] : o.material; return !!(o.isInstancedMesh && m && m.vertexColors && !m.map); };
  const visit = (o, kind) => {
    const mats = Array.isArray(o.material) ? o.material : [o.material];
    for (const m of mats) {
      if (!m || seen.has(m)) continue; seen.add(m);
      if (m.transparent || m.userData.up || !(m.isMeshLambertMaterial || m.isMeshStandardMaterial || m.isMeshBasicMaterial)) continue;
      patchLit(m, kind); m.needsUpdate = true;
    }
  };
  for (const key of ["trees", "rails", "buildings", "crowd", "stalls", "horses"]) for (const root of LAYERS[key]) root.traverse((o) => { if (o.isMesh) visit(o, key === "crowd" ? "crowd" : key === "trees" && isTree(o) ? "tree" : ""); });
}

// ---------- The board on the table ----------
function buildTable({ scene, LAYERS }) {
  const T = 46, RIM = 40;                                  // the board: 46 m thick at the course's scale, a 40 m printed border
  // nothing stands beyond the board's edge
  const m4 = new THREE.Matrix4(), zero = new THREE.Matrix4().makeScale(0, 0, 0);
  for (const o of LAYERS.trees.concat(LAYERS.rails)) if (o.isInstancedMesh) {
    for (let i = 0; i < o.count; i++) { o.getMatrixAt(i, m4); const e = m4.elements; if (!BOARD.inside(e[12], e[14], 10)) o.setMatrixAt(i, zero); }
    o.instanceMatrix.needsUpdate = true; o.computeBoundingSphere();
  }
  const g = new THREE.Group(); scene.add(g);
  const canvas = (w, h, draw) => { const c = document.createElement("canvas"); c.width = w; c.height = h; draw(c.getContext("2d"), w, h); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const inner = BOARD.edge, outer = BOARD.grow(inner, RIM), n = inner.length, sun = U.upSun.value;
  const quad = (pts, uv, mat, order = 0) => {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(pts.flat(), 3)); geo.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2)); geo.setIndex([0, 1, 2, 0, 2, 3]);
    const m = new THREE.Mesh(geo, mat); m.renderOrder = order; g.add(m); return m;
  };
  // the printed border round the scenery: cream card, a racing-green line, a fine gold one
  const rimMat = new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, map: canvas(64, 256, (c, w, h) => {
    c.fillStyle = "#efe7d3"; c.fillRect(0, 0, w, h);
    c.fillStyle = "#1f4a3a"; c.fillRect(0, h * 0.06, w, h * 0.1); c.fillStyle = "#b99a4e"; c.fillRect(0, h * 0.2, w, h * 0.025);
  }) });
  // the board's sides: layered card on a wooden base, the course's name on a brass plate on the two longest sides
  const sideTex = (plate) => canvas(2048, 128, (c, w, h) => {
    c.fillStyle = "#e9dfc8"; c.fillRect(0, 0, w, h);
    c.fillStyle = "#1f4a3a"; c.fillRect(0, 0, w, h * 0.16); c.fillStyle = "#b99a4e"; c.fillRect(0, h * 0.2, w, h * 0.035);
    c.fillStyle = "#6b4b2e"; c.fillRect(0, h * 0.78, w, h * 0.22); c.fillStyle = "rgba(0,0,0,0.18)"; c.fillRect(0, h * 0.76, w, h * 0.03);
    if (plate) {
      const pw = w * plate, ph = h * 0.46, px = (w - pw) / 2, py = h * 0.27;
      c.fillStyle = "#c9ad63"; c.fillRect(px, py, pw, ph); c.strokeStyle = "#8a7335"; c.lineWidth = 3; c.strokeRect(px + 4, py + 4, pw - 8, ph - 8);
      c.save(); c.translate(w / 2, py + ph / 2 + 2); c.scale(pw / 520, 1); c.fillStyle = "#2a2417"; c.font = "600 36px Georgia, serif"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText("THOROUGHBRED  ·  ASCOT", 0, 0); c.restore();
    }
  });
  const lens = outer.map((a, i) => { const b = outer[(i + 1) % n]; return Math.hypot(b[0] - a[0], b[1] - a[1]); });
  const longest = lens.map((L, i) => [L, i]).sort((a, b) => b[0] - a[0]).slice(0, 2).map((v) => v[1]);
  for (let i = 0; i < n; i++) {
    const a = inner[i], b = inner[(i + 1) % n], A = outer[i], B = outer[(i + 1) % n];
    quad([[a[0], 0.03, a[1]], [b[0], 0.03, b[1]], [B[0], 0.03, B[1]], [A[0], 0.03, A[1]]], [0, 1, 1, 1, 1, 0, 0, 0], rimMat);
    // the side under it, facing out: lit by how squarely it faces the lamp
    const L = lens[i], ox = (B[1] - A[1]) / L, oz = -(B[0] - A[0]) / L, lit = 0.52 + 0.46 * Math.max(0, (ox * sun.x + oz * sun.z) / Math.hypot(sun.x, sun.z));
    quad([[B[0], 0, B[1]], [A[0], 0, A[1]], [A[0], -T, A[1]], [B[0], -T, B[1]]], [0, 1, 1, 1, 1, 0, 0, 0],
      new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, map: sideTex(longest.includes(i) ? Math.min(0.5, 260 / L) : 0), color: new THREE.Color(lit, lit, lit) }));
  }
  // the table: oak boards under the lamp's pool of light
  let cx = 0, cz = 0; for (const [x, z] of outer) { cx += x / n; cz += z / n; }
  const table = new THREE.Mesh(new THREE.PlaneGeometry(16000, 16000).rotateX(-Math.PI / 2), new THREE.ShaderMaterial({
    toneMapped: false, fog: false,
    uniforms: { upNoise: U.upNoise, lamp: { value: new THREE.Vector2(cx - 250, cz - 350) } },
    vertexShader: "varying vec2 vW; void main(){ vec4 wp = modelMatrix * vec4(position, 1.0); vW = wp.xz; gl_Position = projectionMatrix * viewMatrix * wp; }",
    fragmentShader: `uniform sampler2D upNoise; uniform vec2 lamp; varying vec2 vW;
      void main(){
        vec2 w = mat2(0.94, 0.34, -0.34, 0.94) * vW;                              // the boards run a little askew to the model
        float plank = floor(w.y / 290.0), h = fract(sin(plank * 91.7) * 43758.5);
        vec2 gp = vec2(w.x + h * 3000.0, w.y);
        float grain = texture2D(upNoise, vec2(gp.x / 2600.0, gp.y / 190.0)).b * 0.6 + texture2D(upNoise, vec2(gp.x / 900.0, gp.y / 45.0) + h).b * 0.4;
        vec3 c = mix(vec3(0.42, 0.26, 0.14), vec3(0.64, 0.43, 0.25), grain) * (0.86 + 0.24 * h);
        float gap = min(fract(w.y / 290.0), 1.0 - fract(w.y / 290.0)) * 290.0;
        c *= 0.6 + 0.4 * smoothstep(0.0, 5.0, gap);
        c *= mix(0.16, 1.1, 1.0 - smoothstep(700.0, 3300.0, distance(vW, lamp)));     // the lamp's pool, falling away into the room
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
      }`,
  }));
  table.position.y = -T; g.add(table);
  // the board's soft shadow on the table, away from the lamp
  {
    let x0 = Infinity, x1 = -Infinity, z0 = Infinity, z1 = -Infinity;
    for (const [x, z] of outer) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); z0 = Math.min(z0, z); z1 = Math.max(z1, z); }
    const pad = 340, w = x1 - x0 + pad * 2, d = z1 - z0 + pad * 2, k = 512 / Math.max(w, d);
    const tex = canvas(Math.ceil(w * k), Math.ceil(d * k), (c) => {
      c.shadowColor = "#000"; c.shadowBlur = 130 * k; c.fillStyle = "#000"; c.beginPath();
      BOARD.grow(outer, 30).forEach(([x, z], i) => { const px = (x - x0 + pad) * k, py = (z - z0 + pad) * k; i ? c.lineTo(px, py) : c.moveTo(px, py); }); c.closePath(); c.fill(); c.fill();
    });
    tex.flipY = false;
    const cast = T / Math.max(sun.y, 0.2) * 0.9;
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: tex, color: "#000000", transparent: true, opacity: 0.62, depthWrite: false }));
    // (the plane's picture runs +x east, and with flipY off its first row is its north edge)
    m.geometry.attributes.uv.array.set([0, 0, 1, 0, 0, 1, 1, 1]); m.geometry.attributes.uv.needsUpdate = true;
    m.position.set((x0 + x1) / 2 - sun.x * cast, -T + 0.3, (z0 + z1) / 2 - sun.z * cast); m.renderOrder = 1; g.add(m);
  }
  // the game's own cards, box lid and the Newmarket board laid out beside it
  const SOFT = canvas(128, 128, (c, w, h) => { c.clearRect(0, 0, w, h); c.shadowColor = "#000"; c.shadowBlur = 14; c.fillStyle = "#000"; c.fillRect(16, 16, w - 32, h - 32); });
  const loader = new THREE.TextureLoader(), img = (f) => new Promise((res) => loader.load("assets/table/" + f, (t) => res(t.image), undefined, () => res(null)));
  const lay = (tex, w, h, x, z, turn, lift = 1.5) => {
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(w * 1.14, h * 1.14).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: SOFT, color: "#000000", transparent: true, opacity: 0.55, depthWrite: false }));
    shadow.position.set(x - sun.x * 16, -T + 0.5 + lift * 0.1, z - sun.z * 16); shadow.rotation.y = turn; shadow.renderOrder = 2; g.add(shadow);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: tex, transparent: true, alphaTest: 0.5 }));
    m.position.set(x, -T + lift, z); m.rotation.y = turn; m.renderOrder = 3; g.add(m);
  };
  // where things lie is given in the table look's own terms: across (to the camera's right) and towards the camera
  const P = LOOK.props || {};
  Promise.all(["base.webp", "p01.webp", "p04.webp", "p07.webp", "p10.webp", "cover.jpg", "newmarket-board.webp"].map(img)).then(([base, a, b, c2, d2, cover, nm]) => {
    if (!base) return;
    const card = (portrait) => canvas(750, 1125, (c, w, h) => { c.clearRect(0, 0, w, h); c.drawImage(base, 0, 0, w, h); if (portrait) c.drawImage(portrait, 26, 96, 360, 540); });
    const [kx, kz, kt] = P.cards || [cx, cz - 900, Math.PI];
    [a, b, c2, d2].forEach((pt, i) => { const u = (i - 1.5) * 190, cs = Math.cos(kt), sn = Math.sin(kt); lay(card(pt), 230, 345, kx + u * cs, kz - u * sn + Math.abs(i - 1.5) * 14, kt + (i - 1.5) * -0.12, 1.5 + i * 0.7); });
    if (cover && P.cover) lay(canvas(904, 720, (c, w, h) => c.drawImage(cover, 0, 0, w, h)), 640, 510, ...P.cover, 2);
    if (nm && P.board) lay(canvas(1448, 1086, (c, w, h) => c.drawImage(nm, 0, 0, w, h)), 1500, 1125, ...P.board, 2);
  });
}
