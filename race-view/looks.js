// Graphic style options for the race view (?look=model | diorama | faceted). Without ?look the race view is
// exactly as before: every hook below does nothing.
//
// Each look restyles four things, from the owner's precedent images (6 Nov 2026):
//   structures (the stand and site pieces: surface pattern and finish), the crowd (palette and a painted
//   figure shading), trees (shape and colour), and the ground (grass texture), plus a finishing pass
//   (crease shadows, depth of field, haze, colour grade, grain).
//   model    "Model maker": faceted foam trees on brass pins, flocked grass, painted card buildings,
//            enamel-painted figures, a soft studio light and a shallow miniature focus (precedents 4 and 5).
//   diorama  "Sunlit diorama": pastel plaster washes, warm sun-bleached grade, mossy tufted trees, pastel
//            crowd, strong tilt-shift (precedents 1 and 2).
//   faceted  "Faceted parkland": low-poly faceted trees and spires with a few copper beeches, stone coursing
//            and slate on the buildings, faceted turf, deep layered haze (precedents 2 and 3).
// All of it is shaders and generated shapes in the browser: no new downloads. Portable later as material
// settings (Godot/Unreal) and as Blender-built tree masters.
import * as THREE from "three";
import { mergeGeometries, mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";

const P = new URLSearchParams(location.search);
const ID = ["model", "diorama", "faceted"].includes(P.get("look")) ? P.get("look") : null;

const LOOKS = {
  model: {
    label: "Model maker",
    sky: ["#eef0ea", "#dfe8ec", "#c3d8e6", "#a9c6de"], fog: [0.86, 0.88, 0.86], clouds: 0.4,
    sunCol: [1.0, 0.95, 0.88], sun: 4.2, hemi: ["#cfe0ec", "#8a9a6a", 2.8],
    trees: { kind: "foam", palette: ["#4f8a3c", "#6fa443", "#9dbd45", "#7aa98f", "#3f7340", "#aac550", "#86b49a", "#5d9447"], trunk: "pin", stipple: 0.10 },
    ground: { kind: "flock", tint: [0.97, 1.0, 0.9], amt: 1 },
    build: { kind: "card", amt: 1 },
    crowd: {
      suits: ["#2d3a52", "#3a4a3e", "#5a4a3a", "#6e6a62", "#26282e", "#8a7a5e", "#40506a", "#5b3a3a"],
      dresses: ["#d9a0a8", "#9cc6d0", "#e8d48a", "#a8c88a", "#e6dcc6", "#c9a0d0", "#e3a27a", "#7fa8c9", "#f0e4d0", "#b8d8b0"],
      hats_gent: ["#1c1c20", "#1c1c20", "#d8c89a", "#1c1c20", "#4a3a2a"], hats_lady: ["#f0ead8", "#d8c89a", "#d9a0a8", "#9cc6d0", "#2a2a2e", "#e8d48a"],
      foot: 0.72, flat: 0.35,
    },
    post: { ao: 0.75, aoR: 1.4, aperture: 0.55, maxBlur: 9, tilt: 0.0, haze: [0.86, 0.88, 0.86], hazeK: [300, 2500, 0.15],
      lift: [0.015, 0.015, 0.012], gain: [1.0, 1.0, 0.98], gamma: 1.0, sat: 1.05, shadowTint: [0.97, 0.99, 1.02], highTint: [1.02, 1.0, 0.97], grain: 0.025, vignette: 0.10 },
  },
  diorama: {
    label: "Sunlit diorama",
    sky: ["#f4e2cf", "#e9d6c8", "#bcd0dc", "#8fb3cf"], fog: [0.93, 0.85, 0.78], clouds: 0.7,
    sunCol: [1.0, 0.86, 0.68], sun: 5.4, hemi: ["#d9c4c8", "#8a7a48", 2.2],
    trees: { kind: "moss", palette: ["#7f9a52", "#98a85e", "#6c8a4c", "#a8a868", "#8aa06a", "#5f7e48", "#b0aa70"], trunk: "keep", stipple: 0.16 },
    ground: { kind: "mottle", tint: [1.06, 1.0, 0.86], amt: 1 },
    build: { kind: "plaster", amt: 1 },
    crowd: {
      suits: ["#e6dcc6", "#c8bca4", "#9aa4b0", "#6a7480", "#b09a7a", "#3a3e48", "#8a6a5a", "#d8cfbd"],
      dresses: ["#f0b8b0", "#f4d4a0", "#b8dcc8", "#a8c8e0", "#d8b8e0", "#f8e8d0", "#e8a088", "#c8d8a0", "#f0c8d8", "#a0c8c0"],
      hats_gent: ["#e8dcc0", "#d8c08a", "#2a2a2e", "#e8dcc0", "#b89a6a"], hats_lady: ["#fff4e4", "#f0b8b0", "#e8d8a8", "#b8dcc8", "#a8c8e0", "#d8c08a"],
      foot: 0.78, flat: 0.25,
    },
    post: { ao: 0.6, aoR: 1.6, aperture: 0.9, maxBlur: 12, tilt: 0.55, haze: [0.95, 0.84, 0.76], hazeK: [220, 2500, 0.22],
      lift: [0.04, 0.025, 0.035], gain: [1.03, 0.99, 0.93], gamma: 0.95, sat: 0.92, shadowTint: [1.02, 0.95, 1.04], highTint: [1.04, 1.0, 0.92], grain: 0.03, vignette: 0.14 },
  },
  faceted: {
    label: "Faceted parkland",
    sky: ["#d8ddd0", "#c4d2cc", "#9fbcc4", "#7ca2b4"], fog: [0.72, 0.78, 0.72], clouds: 0.5,
    sunCol: [1.0, 0.9, 0.78], sun: 4.8, hemi: ["#a8c4c8", "#55683e", 2.4],
    trees: { kind: "facet", palette: ["#6f8a5a", "#88a06a", "#5a7650", "#9aae78", "#7a9468", "#a6b886", "#647e56"], copper: ["#9a5a48", "#b06a50", "#8a4e44"], copperShare: 0.12, trunk: "keep", stipple: 0.0 },
    ground: { kind: "facets", tint: [0.98, 1.02, 0.97], amt: 1 },
    build: { kind: "masonry", amt: 1 },
    crowd: {
      suits: ["#2a2c31", "#30353f", "#3b3e44", "#4a4c50", "#2a3140", "#57544f", "#6a665f", "#3d4038", "#5a3a34"],
      dresses: ["#c99aa6", "#9bb4c6", "#ddd2b8", "#a8605a", "#7f9a78", "#cdb46e", "#e6e0d2", "#8e7aa6", "#c98a6c", "#4f6f92", "#b84a3a"],
      hats_gent: ["#1c1c20", "#1c1c20", "#1c1c20", "#5a5248"], hats_lady: ["#e8e2d4", "#232327", "#c99aa6", "#bfa36c", "#9bb4c6", "#a8402e"],
      foot: 0.65, flat: 0.15,
    },
    post: { ao: 0.9, aoR: 1.2, aperture: 0.25, maxBlur: 6, tilt: 0.0, haze: [0.70, 0.77, 0.74], hazeK: [120, 2000, 0.38],
      lift: [0.015, 0.02, 0.02], gain: [1.0, 1.01, 1.0], gamma: 1.0, sat: 0.95, shadowTint: [0.95, 1.0, 1.03], highTint: [1.03, 1.0, 0.95], grain: 0.02, vignette: 0.16 },
  },
};
export const LOOK = ID ? LOOKS[ID] : null;
export const lookId = ID;

// ---------- Shader helpers (world position, noise, line patterns) ----------
const NOISE = `
  float lkH(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float lkH3(vec3 p) { return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
  float lkN(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(lkH(i), lkH(i + vec2(1, 0)), f.x), mix(lkH(i + vec2(0, 1)), lkH(i + vec2(1, 1)), f.x), f.y); }
  float lkN3(vec3 p) { vec3 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    float a = mix(mix(lkH3(i), lkH3(i + vec3(1,0,0)), f.x), mix(lkH3(i + vec3(0,1,0)), lkH3(i + vec3(1,1,0)), f.x), f.y);
    float b = mix(mix(lkH3(i + vec3(0,0,1)), lkH3(i + vec3(1,0,1)), f.x), mix(lkH3(i + vec3(0,1,1)), lkH3(i + vec3(1,1,1)), f.x), f.y);
    return mix(a, b, f.z); }
  float lkFbm(vec2 p) { return 0.5 * lkN(p) + 0.3 * lkN(p * 2.07 + 5.1) + 0.2 * lkN(p * 4.13 + 1.7); }
  // detail that fades out before it can shimmer: k = how many cycles a pixel spans
  float lkFade(float k) { return 1.0 - smoothstep(0.25, 0.7, k); }
  float lkFine(vec2 p) { vec2 w = fwidth(p); return mix(0.5, lkN(p), lkFade(max(w.x, w.y))); }
  float lkFine3(vec3 p) { vec3 w = fwidth(p); return mix(0.5, lkN3(p), lkFade(max(w.x, max(w.y, w.z)))); }
  // a thin line every period (1 on the line), faded out when too fine to draw
  float lkLine(float x, float period, float width) {
    float u = x / period, d = abs(fract(u + 0.5) - 0.5), px = fwidth(u);
    return (1.0 - smoothstep(width - px, width + px, d)) * lkFade(px * 1.5);
  }
  vec2 lkCell(vec2 p) { vec2 i = floor(p), f = fract(p); float best = 9.0; vec2 id = i;
    for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) { vec2 g = vec2(x, y), o = vec2(lkH(i + g), lkH(i + g + 7.3));
      float d = length(g + o - f); if (d < best) { best = d; id = i + g; } }
    return id; }
`;
function patch(mat, key, frag, uniforms = {}) {
  const prev = mat.onBeforeCompile, prevKey = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, r) => {
    if (prev) prev.call(mat, sh, r);
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vLkW;")
      .replace("#include <project_vertex>", `#include <project_vertex>
        { vec4 lkW = vec4(transformed, 1.0);
          #ifdef USE_BATCHING
            lkW = batchingMatrix * lkW;
          #endif
          #ifdef USE_INSTANCING
            lkW = instanceMatrix * lkW;
          #endif
          vLkW = (modelMatrix * lkW).xyz; }`);
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vLkW;\n" + NOISE + Object.keys(uniforms).map((k) => `uniform ${uniforms[k].type || "float"} ${k};`).join("\n"))
      .replace("#include <color_fragment>", `#include <color_fragment>
        { vec3 wp = vLkW; vec3 wn = normalize(cross(dFdx(vLkW), dFdy(vLkW))); if (wn.y < 0.0 && abs(wn.y) > 0.9) wn = -wn;
          ${frag} }`);
  };
  mat.customProgramCacheKey = () => (prevKey ? prevKey.call(mat) : "") + "|look-" + ID + "-" + key;
  mat.needsUpdate = true;
  return mat;
}
const v3 = (a) => `vec3(${a.map((x) => x.toFixed(4)).join(",")})`;

// ---------- Sky, light and haze ----------
export function setupScene({ scene, hemi, sun, cloudMat, haze }) {
  if (!ID) return;
  const L = LOOK;
  const sky = scene.userData.sky.material.uniforms;
  ["c0", "c1", "c2", "c3"].forEach((k, i) => sky[k].value.set(L.sky[i]));
  scene.fog.color.setRGB(...L.fog, THREE.LinearSRGBColorSpace);
  if (haze) haze.setRGB(...L.fog, THREE.LinearSRGBColorSpace);
  sun.color.setRGB(...L.sunCol, THREE.LinearSRGBColorSpace); sun.intensity = L.sun;
  hemi.color.set(L.hemi[0]); hemi.groundColor.set(L.hemi[1]); hemi.intensity = L.hemi[2];
  if (cloudMat) { cloudMat.opacity = L.clouds; cloudMat.transparent = L.clouds < 1; }
  document.documentElement.classList.remove("story");
  document.documentElement.classList.add("look-" + ID);
}

// ---------- Ground ----------
export function patchGround(mat, which) {
  if (!ID) return mat;
  const G = LOOK.ground, t = v3(G.tint);
  const code = {
    // model flock: a fine speckle of flock fibres over soft broad patches, a cooler fresher green
    flock: `float sp = lkFine(wp.xz * 7.0) * 0.6 + lkFine(wp.xz * 19.0) * 0.4;
            float cl = lkFine(wp.xz * 1.3), pa = lkFbm(wp.xz / 7.0);
            vec3 g = diffuseColor.rgb; g = mix(vec3(dot(g, vec3(0.3, 0.59, 0.11))), g, 0.82);
            diffuseColor.rgb = g * ${t} * (0.9 + 0.2 * sp) * (0.9 + 0.2 * cl) * (0.93 + 0.14 * pa);`,
    // diorama: sun-bleached mottling, yellower in the light patches, with a soft tuft texture
    mottle: `float pa = lkFbm(wp.xz / 9.0), tu = lkFine(wp.xz * 3.0);
             vec3 warm = diffuseColor.rgb * ${t} * vec3(1.08, 1.03, 0.8);
             diffuseColor.rgb = mix(diffuseColor.rgb * ${t}, warm, smoothstep(0.3, 0.7, pa)) * (0.9 + 0.2 * tu) * (0.92 + 0.16 * lkFine(wp.xz * 0.7));`,
    // faceted: the turf broken into big flat-shaded cells, like a low-poly terrain, two greens
    facets: `vec2 id = lkCell(wp.xz / 11.0); float h = lkH(id);
             diffuseColor.rgb *= ${t} * (0.9 + 0.2 * h) * mix(vec3(1.0), vec3(0.97, 1.03, 0.94), step(0.6, h));
             diffuseColor.rgb *= 0.97 + 0.06 * lkFine(wp.xz * 4.0);`,
  }[G.kind];
  return patch(mat, "ground-" + which, code);
}

// ---------- Structures (baked stand, site pieces, finish line) ----------
export function patchBaked(mat, name, key) {
  if (!ID) return mat;
  if (key === "ground") return patchGround(mat, "baked");
  if (/glass|digit|clock_face/.test(name)) return mat;
  const kind = LOOK.build.kind;
  const wall = /gs_wall|gs_podium|gs_steps|fl_board|sp_board|gs_trim|sp_trim|fl_trim/.test(name);
  const roof = /roof/.test(name), timber = /timber|seat/.test(name), canvas = /canvas|stripe|flag/.test(name), leaf = /leaf|hedge|flower/.test(name);
  let code = "";
  if (leaf) code = `diffuseColor.rgb *= 0.88 + 0.24 * lkFine3(wp * 3.0);`;
  else if (kind === "card") {
    // painted card and gesso: an even matte speckle on everything, faint scored lines at each storey and bay
    code = `float sp = lkFine3(wp * 9.0);
      diffuseColor.rgb *= 0.965 + 0.06 * sp;
      ${wall ? `float hz = abs(wn.x) > abs(wn.z) ? wp.z : wp.x; float ln = max(lkLine(wp.y, 3.5, 0.012), lkLine(hz, 3.5, 0.008)) * step(abs(wn.y), 0.4);
      diffuseColor.rgb *= 1.0 - 0.18 * ln;` : ""}
      ${roof ? `diffuseColor.rgb *= vec3(0.98, 1.0, 1.03);` : ""}`;
  } else if (kind === "plaster") {
    // pastel lime-washes: each stretch of stand a slightly different wash (cream, blush, butter, mint),
    // soft weathering, and slate courses on the roofs
    code = `${wall ? `float bay = floor((abs(wn.x) > abs(wn.z) ? wp.z : wp.x) / 24.5); float hb = lkH(vec2(bay, 3.0));
      vec3 wash = hb < 0.3 ? vec3(1.04, 0.95, 0.90) : hb < 0.55 ? vec3(1.04, 1.0, 0.86) : hb < 0.75 ? vec3(0.95, 1.02, 0.96) : vec3(1.02, 0.99, 0.95);
      diffuseColor.rgb *= mix(vec3(1.0), wash, step(abs(wn.y), 0.5));` : ""}
      diffuseColor.rgb *= 0.95 + 0.1 * lkFbm(wp.xz / 3.0 + wp.y / 2.0) + 0.04 * (lkFine3(wp * 6.0) - 0.5);
      ${roof ? `diffuseColor.rgb *= vec3(1.03, 0.97, 0.95) * (1.0 - 0.14 * lkLine(wp.y, 0.3, 0.05));` : ""}`;
  } else if (kind === "masonry") {
    // ashlar stone coursing on the walls (rusticated larger blocks on the podium), slate on the roofs,
    // boarding on timber, a weave on canvas: each block its own tone
    const course = /podium/.test(name) ? "0.7" : "0.45", block = /podium/.test(name) ? "1.6" : "0.95";
    code = `${wall ? `if (abs(wn.y) < 0.4) { float hz = abs(wn.x) > abs(wn.z) ? wp.z : wp.x; float row = floor(wp.y / ${course});
        float hh = hz + mod(row, 2.0) * ${block} * 0.5; float ln = max(lkLine(wp.y, ${course}, 0.05), lkLine(hh, ${block}, 0.025));
        float tone = lkH(vec2(row, floor(hh / ${block}))); vec2 fw = fwidth(vec2(wp.y / ${course}, hh / ${block}));
        diffuseColor.rgb *= mix(1.0, 0.95 + 0.08 * tone, lkFade(max(fw.x, fw.y))) * (1.0 - 0.22 * ln); }` : ""}
      ${roof ? `{ float ln = max(lkLine(wp.y, 0.22, 0.07), lkLine(wp.x + wp.z + floor(wp.y / 0.22) * 0.25, 0.5, 0.03) * 0.6);
        diffuseColor.rgb *= vec3(0.96, 0.98, 1.03) * (1.0 - 0.2 * ln) * (0.95 + 0.1 * lkH(floor(vec2(wp.x + wp.z, wp.y) / vec2(0.5, 0.22)))); }` : ""}
      ${timber ? `diffuseColor.rgb *= 1.0 - 0.18 * lkLine(wp.y, 0.18, 0.06);` : ""}
      ${canvas ? `diffuseColor.rgb *= 0.97 + 0.05 * lkFine3(wp * 14.0);` : ""}
      diffuseColor.rgb *= 0.97 + 0.06 * lkFine3(wp * 2.5);`;
  }
  return code ? patch(mat, "build-" + name, code) : mat;
}

// ---------- Hedges and foliage that keep their models ----------
export function patchFoliage(mat, which) {
  if (!ID) return mat;
  const s = LOOK.trees.stipple;
  const code = LOOK.trees.kind === "facet"
    ? `diffuseColor.rgb *= 0.97 + 0.06 * lkFine3(wp * 1.5);`
    : `diffuseColor.rgb *= ${(1 - s).toFixed(3)} + ${(2 * s).toFixed(3)} * (0.6 * lkFine3(wp * 2.2) + 0.4 * lkFine3(wp * 6.0));`;
  return patch(mat, "foliage-" + which, code);
}

// ---------- Trees ----------
function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
// a jittered, flat-faceted blob filling a box (centre c, half sizes h); taper > 0 makes an egg pointed at the top
function blob(detail, jitter, rnd, taper = 0) {
  let g = new THREE.IcosahedronGeometry(1, detail);
  g.deleteAttribute("normal"); g.deleteAttribute("uv");
  g = mergeVertices(g);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i), k = 1 + (rnd() - 0.5) * 2 * jitter, t = 1 - taper * Math.max(0, y) + 0.12 * taper * Math.min(0, y);
    p.setXYZ(i, x * k * t, y * k, z * k * t);
  }
  return g;
}
function fit(g, box, pad = 1) {
  g.computeBoundingBox();
  const b = g.boundingBox, s = new THREE.Vector3(), c = new THREE.Vector3(), bs = new THREE.Vector3(), bc = new THREE.Vector3();
  box.getSize(s); box.getCenter(c); b.getSize(bs); b.getCenter(bc);
  g.translate(-bc.x, -bc.y, -bc.z).scale(s.x / bs.x * pad, s.y / bs.y * pad, s.z / bs.z * pad).translate(c.x, c.y, c.z);
  return g;
}
// vertex colours: darker underneath, lighter on top (multiplied by each tree's own colour)
function shade(g, lo = 0.62, hi = 1.12) {
  g = g.index ? g.toNonIndexed() : g;
  g.computeVertexNormals();
  g.computeBoundingBox();
  const b = g.boundingBox, p = g.attributes.position, col = new Float32Array(p.count * 3);
  for (let i = 0; i < p.count; i++) { const k = lo + (hi - lo) * Math.pow((p.getY(i) - b.min.y) / (b.max.y - b.min.y || 1), 0.8); col.set([k, k, k], i * 3); }
  g.setAttribute("color", new THREE.Float32BufferAttribute(col, 3));
  return g;
}
const crownCache = new Map();
// The replacement for one tree part, or null to keep the original. name like "oak_a_crown_far", "poplar_a_trunk".
export function treeGeometry(name, orig) {
  if (!ID) return null;
  const kind = LOOK.trees.kind;
  if (kind === "moss") return null;
  if (crownCache.has(name)) return crownCache.get(name);
  orig.computeBoundingBox();
  const box = orig.boundingBox.clone();
  const poplar = name.startsWith("poplar"), bush = name.startsWith("bush"), trunk = name.endsWith("_trunk");
  const rnd = rng([...name].reduce((a, ch) => a * 31 + ch.charCodeAt(0), 7));
  let g = null;
  if (trunk) {
    if (LOOK.trees.trunk !== "pin") { crownCache.set(name, null); return null; }
    // a thin brass pin from the ground up into the crown
    const h = box.max.y * 1.05;
    g = new THREE.CylinderGeometry(0.11, 0.11, h, 5, 1, true).translate((box.min.x + box.max.x) / 2, h / 2, (box.min.z + box.max.z) / 2);
    g = shade(g, 0.85, 1.0);
    const c = g.attributes.color; for (let i = 0; i < c.count; i++) c.setXYZ(i, 0.56 * c.getX(i), 0.42 * c.getX(i), 0.22 * c.getX(i));
    g.userData.plain = true;
  } else if (kind === "foam") {
    if (poplar) {
      // a tall bevelled column of foam, as precedent 4
      let c = new THREE.CylinderGeometry(0.8, 1, 1, 6, 3);
      c.deleteAttribute("normal"); c.deleteAttribute("uv"); c = mergeVertices(c);
      const p = c.attributes.position;
      for (let i = 0; i < p.count; i++) { const y = p.getY(i), k = 1 + (rnd() - 0.5) * 0.18, cap = y > 0.49 ? 0.75 : y < -0.49 ? 0.85 : 1; p.setXYZ(i, p.getX(i) * k * cap, y + (Math.abs(y) > 0.49 ? Math.sign(y) * 0.08 : 0), p.getZ(i) * k * cap); }
      g = fit(c, box, 0.92);
    } else {
      // one faceted egg of foam per crown, pointed at the top, as precedent 5
      g = fit(blob(1, 0.1, rnd, 0.32), box, bush ? 0.95 : 0.9);
    }
    g = shade(g, 0.72, 1.08);
  } else if (kind === "facet") {
    if (poplar) {
      // a stacked low-poly spire (precedent 3)
      const s = new THREE.Vector3(); box.getSize(s);
      const parts = [];
      for (let k = 0; k < 4; k++) {
        const r = 0.5 * (1 - k * 0.2), h = 0.42;
        parts.push(new THREE.ConeGeometry(r, h, 7, 1).translate(0, k * 0.22 + h / 2, 0).rotateY(rnd() * 3));
      }
      g = fit(mergeGeometries(parts.map((q) => { q.deleteAttribute("uv"); return q.index ? q.toNonIndexed() : q; })), box, 1.0);
    } else {
      // a cluster of faceted crowns (precedent 3's big tree)
      const parts = [], n = bush ? 3 : 5;
      for (let k = 0; k < n; k++) {
        const a = (k / n) * Math.PI * 2 + rnd(), r = k === 0 ? 0 : 0.42, up = k === 0 ? 0.25 : (rnd() - 0.3) * 0.4;
        const b = blob(1, 0.16, rnd, 0.1), sc = k === 0 ? 0.62 : 0.45 + rnd() * 0.12;
        b.scale(sc, sc, sc).translate(Math.cos(a) * r, up, Math.sin(a) * r);
        parts.push(b.toNonIndexed());
      }
      g = fit(mergeGeometries(parts), box, 1.0);
    }
    g = shade(g, 0.6, 1.1);
  }
  crownCache.set(name, g);
  return g;
}
const treeMats = new Map();
export function treeMaterial(base, name) {
  if (!ID) return base;
  const plain = /_trunk/.test(name) && LOOK.trees.trunk === "pin";
  const k = plain ? "pin" : "tree";
  if (!treeMats.has(k)) {
    const m = plain ? new THREE.MeshLambertMaterial({ vertexColors: true }) : base.clone();
    if (LOOK.trees.kind !== "moss") m.flatShading = true;
    if (!plain) patchFoliage(m, "tree");
    treeMats.set(k, m);
  }
  return treeMats.get(k);
}
// each tree's own colour (multiplied with its vertex colours); trunks stay as they are
const _c = new THREE.Color();
export function treeColour(name, t, i) {
  if (!ID || /_trunk/.test(name)) return null;
  const T = LOOK.trees;
  const h = Math.abs(Math.sin((t.x * 12.9898 + t.z * 78.233) * 0.01) * 43758.5453) % 1;
  const h2 = Math.abs(Math.sin((t.x * 39.3468 + t.z * 11.135) * 0.01) * 23421.631) % 1;
  if (T.copper && h2 < T.copperShare) _c.set(T.copper[Math.floor(h * T.copper.length)]);
  else _c.set(T.palette[Math.floor(h * T.palette.length)]);
  if (T.kind === "moss") {
    // the original leafy trees carry their own green: nudge them towards a sun-bleached olive and straw
    const tint = new THREE.Color(_c).multiplyScalar(1 / 0.5);
    return tint.lerp(new THREE.Color(1, 1, 1), 0.5);
  }
  // the new shapes are grey vertex colours: the palette colour (to linear) is the tree's colour, lifted a touch
  return _c.clone().multiplyScalar(1.35);
}

// ---------- Crowd ----------
export function crowdPalette(p) {
  if (!ID) return p;
  return { ...p, ...LOOK.crowd };
}
export function patchCrowd(sh) {
  if (!ID) return;
  const C = LOOK.crowd;
  // painted-figure shading: a little darker towards the feet (as if standing in the grass), and flatter light
  sh.vertexShader = sh.vertexShader.replace("#include <common>", "#include <common>\nvarying float vLkH;")
    .replace("#include <begin_vertex>", "#include <begin_vertex>\nvLkH = position.y;");
  sh.fragmentShader = sh.fragmentShader.replace("#include <common>", "#include <common>\nvarying float vLkH;")
    .replace("#include <color_fragment>", `#include <color_fragment>
      diffuseColor.rgb *= mix(${C.foot.toFixed(3)}, 1.0, smoothstep(0.0, 1.1, vLkH));`)
    .replace("#include <opaque_fragment>", `outgoingLight = mix(outgoingLight, diffuseColor.rgb * 0.95, ${C.flat.toFixed(3)});
      #include <opaque_fragment>`);
}

// ---------- The finishing pass ----------
let post = null;
function makePost(renderer) {
  const Q = LOOK.post;
  const rt = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: renderer.capabilities.isWebGL2 ? 4 : 0, depthTexture: new THREE.DepthTexture(1, 1) });
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      tColor: { value: rt.texture }, tDepth: { value: rt.depthTexture }, res: { value: new THREE.Vector2(1, 1) },
      near: { value: 0.5 }, far: { value: 4000 }, tanHalf: { value: 0.4 }, focusZ: { value: 50 },
      aperture: { value: Q.aperture }, maxBlur: { value: Q.maxBlur }, tilt: { value: Q.tilt }, aoK: { value: new THREE.Vector2(Q.ao, Q.aoR) },
      hazeCol: { value: new THREE.Color().setRGB(...Q.haze, THREE.LinearSRGBColorSpace) }, hazeK: { value: new THREE.Vector3(...Q.hazeK) },
      lift: { value: new THREE.Vector3(...Q.lift) }, gain: { value: new THREE.Vector3(...Q.gain) }, gammaV: { value: Q.gamma }, sat: { value: Q.sat },
      shadowTint: { value: new THREE.Vector3(...Q.shadowTint) }, highTint: { value: new THREE.Vector3(...Q.highTint) },
      grain: { value: Q.grain }, vignette: { value: Q.vignette }, seed: { value: 0 }, scale: { value: 1 },
    },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `
      #include <packing>
      uniform sampler2D tColor, tDepth; uniform vec2 res, aoK;
      uniform float near, far, tanHalf, focusZ, aperture, maxBlur, tilt, gammaV, sat, grain, vignette, seed, scale;
      uniform vec3 hazeCol, hazeK, lift, gain, shadowTint, highTint;
      varying vec2 vUv;
      float vz(vec2 uv) { return -perspectiveDepthToViewZ(texture2D(tDepth, uv).x, near, far); }
      float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      // how blurred a point at view depth z is (pixels): a shallow, miniature focus around the camera's subject,
      // plus an optional tilt-shift band (sharp across the middle of the picture)
      float fz;
      float coc(float z, vec2 uv) {
        float d = aperture * abs(1.0 - fz / max(z, 0.01));
        float t = tilt * smoothstep(0.12, 0.5, abs(uv.y - 0.5));
        return clamp(max(d, t), 0.0, 1.0) * maxBlur * scale;
      }
      void main() {
        float zc = vz(vUv);
        fz = focusZ > 0.0 ? focusZ : min(min(vz(vec2(0.5, 0.5)), vz(vec2(0.5, 0.42))), min(vz(vec2(0.42, 0.5)), vz(vec2(0.58, 0.5))));
        bool sky = texture2D(tDepth, vUv).x > 0.99999;
        float cc = coc(sky ? far : zc, vUv);
        vec3 c = texture2D(tColor, vUv).rgb;
        if (cc > 0.6) {
          vec3 acc = c; float ws = 1.0;
          for (int i = 0; i < 20; i++) {
            float fi = float(i) + 0.5, r = sqrt(fi / 20.0), a = fi * 2.39996;
            vec2 o = vec2(cos(a), sin(a)) * r * cc / res;
            float zt = vz(vUv + o);
            float w = zt >= zc - 1.0 ? 1.0 : clamp(coc(zt, vUv + o) / max(r * cc, 0.5), 0.0, 1.0);
            acc += texture2D(tColor, vUv + o).rgb * w; ws += w;
          }
          c = acc / ws;
        }
        // crease shadows: where both sides of a pixel are nearer than it (under eaves, between people, at the
        // foot of a wall), it is in a fold and gets darker; flat ground and walls are left alone
        if (aoK.x > 0.0 && !sky) {
          float rpx = clamp(aoK.y * res.y / (2.0 * tanHalf * zc), 1.5, 36.0 * scale), occ = 0.0, j = hash(vUv * res) * 6.283;
          for (int i = 0; i < 8; i++) {
            float fi = float(i) + 0.5, r = sqrt(fi / 8.0), a = fi * 2.39996 + j;
            vec2 o = vec2(cos(a), sin(a)) * r * rpx / res;
            float d = zc - 0.5 * (vz(vUv + o) + vz(vUv - o));
            occ += clamp(d / aoK.y, 0.0, 1.0) * (1.0 - smoothstep(aoK.y * 2.0, aoK.y * 5.0, d));
          }
          c *= 1.0 - aoK.x * clamp(occ / 8.0 * 1.6, 0.0, 0.8);
        }
        // layered haze: things further off sink into the air colour (sky left alone)
        if (!sky) c = mix(c, hazeCol, hazeK.z * smoothstep(hazeK.x, hazeK.y, zc));
        c = toneMapping(c);
        c = sRGBTransferOETF(vec4(c, 1.0)).rgb;
        // grade: saturation, lift and gain, gamma, split toning
        float l = dot(c, vec3(0.299, 0.587, 0.114));
        c = mix(vec3(l), c, sat);
        c = c * gain + lift * (1.0 - c);
        c = pow(max(c, 0.0), vec3(gammaV));
        c *= mix(shadowTint, highTint, smoothstep(0.1, 0.8, l));
        c += (hash(vUv * res + seed) - 0.5) * grain;
        float v = length((vUv - 0.5) * vec2(1.0, 0.85));
        c *= mix(1.0, 1.0 - vignette, smoothstep(0.35, 0.85, v));
        gl_FragColor = vec4(c, 1.0);
      }`,
    depthTest: false, depthWrite: false,
  });
  const ps = new THREE.Scene(); ps.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat));
  return { rt, mat, scene: ps, cam: new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1) };
}
// Draw a frame: through the finishing pass for a look, straight to the screen otherwise.
const _sz = new THREE.Vector2();
let fogBase = null;
export function render(renderer, scene, camera, focus, auto = false) {
  if (!ID) { renderer.render(scene, camera); return; }
  if (!post) post = makePost(renderer);
  renderer.getDrawingBufferSize(_sz);
  if (post.rt.width !== _sz.x || post.rt.height !== _sz.y) post.rt.setSize(_sz.x, _sz.y);
  const u = post.mat.uniforms;
  u.res.value.copy(_sz); u.near.value = camera.near; u.far.value = camera.far;
  u.tanHalf.value = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  u.focusZ.value = focus && !auto ? Math.max(2, camera.position.distanceTo(focus)) : -1;   // -1: focus on what's in the middle of the picture
  u.scale.value = _sz.y / 720; u.seed.value = (u.seed.value + 1) % 97;
  // long lens: the TV cameras look 300-800 m down the course through a narrow lens, and a haze measured from the
  // camera fogged the whole picture; on a narrow lens the air is thinned so the subject keeps its colour
  const lens = THREE.MathUtils.clamp(40 / camera.fov, 1, 8);
  if (scene.fog) {
    if (!fogBase) fogBase = [scene.fog.near, scene.fog.far];
    scene.fog.near = fogBase[0] * lens; scene.fog.far = fogBase[1] * lens;
  }
  u.hazeK.value.set(LOOK.post.hazeK[0] * lens, LOOK.post.hazeK[1] * lens, LOOK.post.hazeK[2]);
  renderer.setRenderTarget(post.rt);
  renderer.render(scene, camera);
  renderer.setRenderTarget(null);
  renderer.render(post.scene, post.cam);
}
