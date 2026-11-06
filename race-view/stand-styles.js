// Grandstand style tests (?stand=pastel|brick, with &v=1..3 for the variant; ?stand=debug colours each material).
// Without ?stand the stand is exactly as before. Restyles only the main stand: its colours by material and by
// module (each stretch of the stand its own building), its surface (clay plaster or stylised brick and stone),
// how the baked sunlight sits on it (warm sun, tinted shade), and drawn line work along its edges.
//   pastel: the pastel diorama street (precedent 1): a row of plaster buildings, each its own colour, white trims,
//           dark bronze ironwork, deep violet glass, soft terracotta roofs.
//   brick:  the brick harbour town (precedent 2): big stylised brick, grey stone base, cream trim, terracotta tile
//           roofs, black ironwork, crisp ink line work.
import * as THREE from "three";
import { LineSegments2 } from "three/addons/lines/LineSegments2.js";
import { LineSegmentsGeometry } from "three/addons/lines/LineSegmentsGeometry.js";
import { LineMaterial } from "three/addons/lines/LineMaterial.js";

const P = new URLSearchParams(location.search);
const ID = ["pastel", "brick", "debug"].includes(P.get("stand")) ? P.get("stand") : null;
const VN = Math.max(1, Math.min(3, Number(P.get("v") || 1)));
export const standId = ID;

// Variants: what each tests is in its label.
const OPTIONS = {
  pastel: [
    { label: "Pastel row · clay · no line work",
      row: ["#e3968b", "#eeae78", "#ecc95f", "#f0dcbc", "#8fbea4", "#dd826b", "#9fc8d6"], trim: "#fbf6ec", trimMix: 0.5, podiumDark: 0.8, exposure: 0.72,
      roof: "#d79c80", iron: "#5b4636", glass: "#4b4862", door: "#4f8a86", gilt: "#d9b26a", steps: "#e9dcc6",
      surface: "clay", lines: null, sun: [1.08, 1.0, 0.9], shade: [0.86, 0.8, 0.98], contrast: 0.25 },
    { label: "Pastel row · clay · soft coloured line work",
      row: ["#e3968b", "#eeae78", "#ecc95f", "#f0dcbc", "#8fbea4", "#dd826b", "#9fc8d6"], trim: "#fbf6ec", trimMix: 0.5, podiumDark: 0.8, exposure: 0.72,
      roof: "#d79c80", iron: "#5b4636", glass: "#4b4862", door: "#4f8a86", gilt: "#d9b26a", steps: "#e9dcc6",
      surface: "clay", lines: { mode: "tone", k: 0.45, width: 0.1 }, sun: [1.08, 1.0, 0.9], shade: [0.86, 0.8, 0.98], contrast: 0.25 },
    { label: "Sorbet · bolder colour · white line work",
      row: ["#ec6a5e", "#f39a45", "#f2c84a", "#45ab9c", "#9c7fcc", "#ec7c98", "#5fa8d3"], trim: "#ffffff", trimMix: 0.38, podiumDark: 0.75, exposure: 0.7,
      roof: "#e7d2bd", iron: "#2e4b52", glass: "#3e3a5c", door: "#2f6f8a", gilt: "#e3b45a", steps: "#f0e2cc",
      surface: "clay", lines: { mode: "colour", colour: "#fffaf0", width: 0.08 }, sun: [1.1, 1.0, 0.86], shade: [0.84, 0.82, 1.02], contrast: 0.35 },
  ],
  brick: [
    { label: "Red brick · stone base · ink line work",
      brick: "#b8573f", mortar: "#e2d6c4", stone: "#b9b4aa", trim: "#efe6d2", roof: "#c9683e", roofKind: "tile",
      iron: "#24262a", glass: "#34404c", door: "#2f4a3a", gilt: "#c8a052", steps: "#bdb6aa",
      surface: "brick", exposure: 0.74, lines: { mode: "colour", colour: "#2a211c", width: 0.07 }, sun: [1.14, 1.0, 0.84], shade: [0.8, 0.88, 1.06], contrast: 0.5 },
    { label: "Red brick · stone base · no line work",
      brick: "#b8573f", mortar: "#e2d6c4", stone: "#b9b4aa", trim: "#efe6d2", roof: "#c9683e", roofKind: "tile",
      iron: "#24262a", glass: "#34404c", door: "#2f4a3a", gilt: "#c8a052", steps: "#bdb6aa",
      surface: "brick", exposure: 0.74, lines: null, sun: [1.14, 1.0, 0.84], shade: [0.8, 0.88, 1.06], contrast: 0.5 },
    { label: "Mixed terrace · red and white brick · racing-green trim · ink line work",
      row: ["#b8573f", "#cfccc2", "#a9503a", "#d9d4c6", "#c0664a"], brick: "#b8573f", mortar: "#ece3d2", stone: "#9d988e", trim: "#2f5a45", roof: "#c9683e", roofKind: "tile",
      iron: "#e9e2d2", glass: "#2c3640", door: "#e9e2d2", gilt: "#c8a052", steps: "#bdb6aa",
      surface: "brick", exposure: 0.74, lines: { mode: "colour", colour: "#231c18", width: 0.07 }, sun: [1.14, 1.0, 0.84], shade: [0.8, 0.88, 1.06], contrast: 0.5 },
  ],
};
const O = ID && ID !== "debug" ? OPTIONS[ID][VN - 1] : null;
export const standLabel = O ? O.label : ID === "debug" ? "Materials" : null;

const lin = (h) => new THREE.Color(h);   // three converts hex (sRGB) to linear
const v3 = (c) => `vec3(${c.r.toFixed(4)}, ${c.g.toFixed(4)}, ${c.b.toFixed(4)})`;
const roleOf = (name) =>
  /gs_wall/.test(name) ? "wall" : /gs_podium/.test(name) ? "podium" : /gs_trim/.test(name) ? "trim" : /gs_roof/.test(name) ? "roof"
  : /gs_iron/.test(name) ? "iron" : /gs_glass/.test(name) ? "glass" : /gs_door/.test(name) ? "door" : /gs_gilt/.test(name) ? "gilt"
  : /gs_steps/.test(name) ? "steps" : "other";

// The stand's modules (courses/ascot.json -> grandstand.modules): a run of the same module is one "building".
let rowTex = null, buildings = [];
export function setModules(modules) {
  if (!O || !O.row || !modules) return;
  const X0 = -130, X1 = 430, N = 1024;
  const groups = [];
  for (const m of modules.slice().sort((a, b) => b.xEast - a.xEast)) {
    const g = groups[groups.length - 1];
    if (g && g.module === m.module) g.xWest = m.xWest; else groups.push({ module: m.module, xEast: m.xEast, xWest: m.xWest });
  }
  // neighbours never share a colour; the clock tower block keeps the palette's cream
  let last = -1;
  groups.forEach((g, i) => {
    let k = g.module === "clock_centre" ? 3 : (i * 3 + (g.module.length % 4)) % O.row.length;
    if (k === last) k = (k + 1) % O.row.length;
    g.colour = O.row[k]; last = k;
  });
  buildings = groups;
  const data = new Uint8Array(N * 4), c = new THREE.Color();
  for (let i = 0; i < N; i++) {
    const x = X0 + (i + 0.5) * (X1 - X0) / N;
    const g = groups.find((q) => x <= q.xEast && x >= q.xWest) || groups[x > 0 ? 0 : groups.length - 1];
    c.set(g.colour);
    const s = c.getHexString();
    data.set([parseInt(s.slice(0, 2), 16), parseInt(s.slice(2, 4), 16), parseInt(s.slice(4, 6), 16), 255], i * 4);
  }
  rowTex = new THREE.DataTexture(data, N, 1);
  rowTex.colorSpace = THREE.SRGBColorSpace; rowTex.magFilter = rowTex.minFilter = THREE.NearestFilter; rowTex.needsUpdate = true;
  rowTex.userData = { X0, X1 };
}
const rowColourAt = (x) => { const g = buildings.find((q) => x <= q.xEast && x >= q.xWest); return new THREE.Color(g ? g.colour : O.row[0]); };

const NOISE = `
  float sH(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float sN(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(sH(i), sH(i + vec2(1, 0)), f.x), mix(sH(i + vec2(0, 1)), sH(i + vec2(1, 1)), f.x), f.y); }
  float sFade(float k) { return 1.0 - smoothstep(0.3, 0.8, k); }
  float sLine(float x, float period, float width) {
    float u = x / period, d = abs(fract(u + 0.5) - 0.5), px = fwidth(u);
    return (1.0 - smoothstep(width - px, width + px, d)) * sFade(px * 1.4);
  }
`;
const DEBUG = { wall: "#e05050", podium: "#a03030", trim: "#f0f0f0", roof: "#3070e0", iron: "#202020", glass: "#30c0e0", door: "#30a040", gilt: "#e0c020", steps: "#e090e0", other: "#ff8000" };

// Restyle one of the stand's baked materials (material colour x Blender's baked light).
export function patchStand(mat, name) {
  if (!ID) return mat;
  const role = roleOf(name);
  if (ID === "debug") { mat.color.set(DEBUG[role]); return mat; }
  const uniforms = { rowTex: { value: rowTex || new THREE.DataTexture(new Uint8Array([255, 255, 255, 255]), 1, 1) }, rowSpan: { value: new THREE.Vector2(-130, 430) } };
  let colour;
  const base = (h) => `diffuseColor.rgb = ${v3(lin(h))};`;
  const row = `vec3 rowC = texture2D(rowTex, vec2((wp.x - rowSpan.x) / (rowSpan.y - rowSpan.x), 0.5)).rgb;`;
  if (O.surface === "clay") {
    // plaster like coloured clay: each building its own colour, a soft uneven wash and a fine grain
    const wash = `diffuseColor.rgb *= (0.95 + 0.1 * sN(wp.xz / 4.0 + wp.y / 3.0)) * (0.975 + 0.05 * sN(wp.xy * 9.0 + wp.zy * 9.0));`;
    colour = {
      wall: `${row} diffuseColor.rgb = rowC; ${wash}`,
      podium: `${row} diffuseColor.rgb = rowC * ${O.podiumDark.toFixed(3)}; diffuseColor.rgb *= 1.0 - 0.12 * sLine(wp.y, 0.7, 0.04) * step(abs(wn.y), 0.4); ${wash}`,
      trim: `${row} diffuseColor.rgb = mix(rowC, ${v3(lin(O.trim))}, ${O.trimMix.toFixed(2)}); ${wash}`,
      roof: `${base(O.roof)} diffuseColor.rgb *= 1.0 - 0.1 * sLine(wp.y, 0.3, 0.06); ${wash}`,
      iron: base(O.iron), glass: base(O.glass), door: base(O.door), gilt: base(O.gilt), steps: `${base(O.steps)} ${wash}`, other: "",
    }[role];
  } else {
    // stylised brick: big bricks (0.28 m courses, 0.75 m long) each its own tone, a few darker burnt ones,
    // pale mortar; a grey stone base in large blocks; tiles or slates in rows on the roofs
    const brick = `
      if (abs(wn.y) < 0.45) {
        float hz = abs(wn.x) > abs(wn.z) ? wp.z : wp.x, row = floor(wp.y / 0.28), hh = hz + mod(row, 2.0) * 0.375;
        float h = sH(vec2(row, floor(hh / 0.75)));
        vec2 fw = fwidth(vec2(wp.y / 0.28, hh / 0.75)); float near = sFade(max(fw.x, fw.y) * 0.7);
        ${O.row ? row + " vec3 bc = rowC;" : `vec3 bc = ${v3(lin(O.brick))};`}
        vec3 b = bc * mix(1.0, (0.8 + 0.34 * h) * (h > 0.92 ? 0.72 : 1.0), near);
        ${O.band ? `float band = step(mod(wp.y, 3.5), 0.56); b = mix(b, ${v3(lin(O.band))} * mix(1.0, 0.85 + 0.3 * h, near), band);` : ""}
        float ln = max(sLine(wp.y, 0.28, 0.07), sLine(hh, 0.75, 0.035));
        diffuseColor.rgb = mix(b, ${v3(lin(O.mortar))}, ln * 0.85);
      } else { diffuseColor.rgb = ${v3(lin(O.brick))} * 0.95; }`;
    const stone = (c) => `
      { float hz = abs(wn.x) > abs(wn.z) ? wp.z : wp.x, row = floor(wp.y / 0.62), hh = hz + mod(row, 2.0) * 0.8;
        float h = sH(vec2(row, floor(hh / 1.6))); vec2 fw = fwidth(vec2(wp.y / 0.62, hh / 1.6));
        diffuseColor.rgb = ${v3(lin(c))} * mix(1.0, 0.9 + 0.18 * h, sFade(max(fw.x, fw.y)));
        diffuseColor.rgb *= 1.0 - 0.3 * max(sLine(wp.y, 0.62, 0.05), sLine(hh, 1.6, 0.025)) * step(abs(wn.y), 0.45); }`;
    const roof = O.roofKind === "tile"
      ? `{ float r = floor(wp.y / 0.24), along = (abs(wn.x) > abs(wn.z) ? wp.z : wp.x) + mod(r, 2.0) * 0.16; float h = sH(vec2(r, floor(along / 0.32)));
          diffuseColor.rgb = ${v3(lin(O.roof))} * (0.86 + 0.26 * h) * (1.0 - 0.32 * sLine(wp.y, 0.24, 0.12)) * (1.0 - 0.15 * sLine(along, 0.32, 0.05)); }`
      : `{ float r = floor(wp.y / 0.2), along = (abs(wn.x) > abs(wn.z) ? wp.z : wp.x) + mod(r, 2.0) * 0.25; float h = sH(vec2(r, floor(along / 0.5)));
          diffuseColor.rgb = ${v3(lin(O.roof))} * (0.88 + 0.22 * h) * (1.0 - 0.28 * sLine(wp.y, 0.2, 0.1)); }`;
    colour = {
      wall: brick, podium: stone(O.stone), trim: `${base(O.trim)} diffuseColor.rgb *= 0.97 + 0.06 * sN(wp.xy * 3.0 + wp.zy * 3.0);`,
      roof, iron: base(O.iron), glass: base(O.glass), door: base(O.door), gilt: base(O.gilt), steps: stone(O.steps), other: "",
    }[role];
  }
  const sun = new THREE.Vector3(...O.sun), shade = new THREE.Vector3(...O.shade);
  Object.assign(uniforms, { sunTint: { value: sun }, shadeTint: { value: shade }, lightK: { value: new THREE.Vector3(0.35, 1.15, O.contrast) } });
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vSW;")
      .replace("#include <project_vertex>", "#include <project_vertex>\nvSW = (modelMatrix * vec4(transformed, 1.0)).xyz;");
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vSW; uniform sampler2D rowTex; uniform vec2 rowSpan; uniform vec3 sunTint, shadeTint, lightK;\n" + NOISE)
      .replace("#include <color_fragment>", `#include <color_fragment>
        { vec3 wp = vSW; vec3 wn = normalize(cross(dFdx(vSW), dFdy(vSW))); ${colour} }`)
      // the baked light: warmer where the sun falls, tinted shade, a little more contrast between them
      .replace("#include <aomap_fragment>", `{
          vec3 L = reflectedLight.indirectDiffuse; float l = dot(L, vec3(0.3, 0.59, 0.11));
          float k = smoothstep(lightK.x, lightK.y, l);
          reflectedLight.indirectDiffuse = L * mix(shadeTint, sunTint, k) * (1.0 + lightK.z * (k - 0.5)) * ${(O.exposure || 1).toFixed(3)} * ${role === "glass" ? "0.55" : "1.0"};
        }
        #include <aomap_fragment>`);
  };
  mat.customProgramCacheKey = () => "stand-" + ID + VN + "-" + role;
  if (O.lines) { mat.polygonOffset = true; mat.polygonOffsetFactor = 1; mat.polygonOffsetUnits = 1; }
  mat.color.set("#ffffff");
  // the stand shows its colours as painted: no film-style tone mapping squeezing pastels to white (the exposure
  // above keeps the sunlit walls just under full brightness instead)
  mat.toneMapped = false;
  return mat;
}

// Line work: the stand's edges drawn as lines (creases sharper than 28 degrees), in world units so they thin
// out with distance like a pen drawing, not a fixed-width outline.
const lineMats = [];
export function addStandLines(scene, meshes) {
  if (!O || !O.lines) return;
  const L = O.lines;
  for (const m of meshes) {
    const role = roleOf(m.material.name || "");
    if (["glass", "iron", "gilt", "other"].includes(role)) continue;
    const edges = new THREE.EdgesGeometry(m.geometry, 28);
    const g = new LineSegmentsGeometry().fromEdgesGeometry(edges);
    let mat;
    if (L.mode === "tone") {
      // each line a darker shade of the surface it belongs to (its building's colour on the walls)
      const pos = edges.attributes.position, cols = new Float32Array(pos.count * 3), v = new THREE.Vector3(), c = new THREE.Color();
      const fixed = { trim: O.trim, roof: O.roof, door: O.door, steps: O.steps }[role];
      for (let i = 0; i < pos.count; i += 2) {
        v.fromBufferAttribute(pos, i).add(new THREE.Vector3().fromBufferAttribute(pos, i + 1)).multiplyScalar(0.5).applyMatrix4(m.matrixWorld);
        c.set(fixed || rowColourAt(v.x)).multiplyScalar(L.k);
        cols.set([c.r, c.g, c.b, c.r, c.g, c.b], i * 3);
      }
      g.setColors(cols);
      mat = new LineMaterial({ linewidth: L.width, worldUnits: true, vertexColors: true });
    } else {
      mat = new LineMaterial({ color: L.colour, linewidth: L.width, worldUnits: true });
    }
    mat.fog = true;
    lineMats.push(mat);
    const line = new LineSegments2(g, mat);
    line.matrixAutoUpdate = false; line.matrix.copy(m.matrixWorld);
    scene.add(line);
  }
  const res = () => lineMats.forEach((lm) => lm.resolution.set(innerWidth * devicePixelRatio, innerHeight * devicePixelRatio));
  res(); addEventListener("resize", res);
}
