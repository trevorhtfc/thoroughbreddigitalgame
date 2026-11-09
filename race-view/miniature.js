// The "miniature" look test (owner, 9 Nov 2026): what makes the AI-restyled stills of the Rowley Mile read as a
// photograph of a model, tried in the real race view one effect at a time. Only with ?mini=1; without it nothing here
// runs and the race view is exactly as before. Not part of the game (not staged, not loaded by game mode).
//
// The owner's concept stills against our renders of the same views showed six differences, each a switch here:
//   light    warm light and a sky that warms to cream at the horizon (the biggest one)
//   haze     distant things fade into warm air
//   shadows  short soft shadows (a higher sun, soft edges, lighter shade) instead of long crisp ones
//   contact  soft darkening where things meet (under the rail, at the foot of walls, between people)
//   tilt     tilt-shift: sharp across a band, blurred above and below, like a macro lens on a model
//   grade    one warm colour family: a little less saturated, lifted shadows, warm highlights
//   crowd    the crowd in muted model-railway colours (camel, cream, pale blue, mustard), fewer black top hats
//            (most of the toppers become grey morning dress), darker at the feet
//   turf     a duller sage turf with a fine grain and gentler mowing stripes
// The trees are left as they are (owner: keep the leafy trees).
//
// Everything switches live: the picture is drawn into an off-screen image and finished by one full-screen pass, as
// the earlier look tests did (looks.js), keeping the game's own storybook grade underneath, so "all off" is the game.
import * as THREE from "three";

const P = new URLSearchParams(location.search);
export const ON = P.has("mini");

// Uniforms the material patches read (so the crowd and turf switch without rebuilding anything).
export const U = { turf: { value: 1 }, crowd: { value: 1 } };

// ---------- Settings ----------
const DEFAULTS = { light: 1, haze: 1, shadows: 1, contact: 1, tilt: 1, grade: 1, crowd: 1, turf: 1, tiltAmt: 0.6, tiltBand: 0.5, hazeAmt: 0.3, contactAmt: 0.6 };
export const S = { ...DEFAULTS };
// read from the page's address (#m=...), so a setting can be passed on and comes back after a reload
function readHash() {
  const m = /[#&]m=([^&]*)/.exec(location.hash);
  if (!m) return;
  for (const kv of decodeURIComponent(m[1]).split(",")) {
    const [k, v] = kv.split(":");
    if (k in S && Number.isFinite(+v)) S[k] = +v;
  }
}
function writeHash() {
  const s = Object.keys(S).map((k) => k + ":" + +(+S[k]).toFixed(2)).join(",");
  history.replaceState(null, "", location.pathname + location.search + "#m=" + s);
}
readHash();

// ---------- Values for "on" (worked out against the owner's concept stills) ----------
const lin = (hex) => new THREE.Color(hex);    // THREE.Color from a hex string is converted to linear already
const WARM = {
  sky: [lin("#ffdcc8"), lin("#bcc4ec"), lin("#7e9de0"), lin("#7698dc")],   // cream at the horizon, then lilac, then soft blue
  sun: new THREE.Color().setRGB(1.0, 0.9, 0.78, THREE.LinearSRGBColorSpace), sunI: 4.2,
  hemiSky: new THREE.Color("#c9cfe2"), hemiGround: new THREE.Color("#b5a98f"), hemiI: 2.5,
  fog: new THREE.Color().setRGB(0.84, 0.85, 0.9, THREE.LinearSRGBColorSpace),   // pale, a touch lilac, as the far distance in the concept
  cloud: 1,
};
const SOFT = { up: 2.1, radius: 7, type: THREE.PCFShadowMap, hemiBoost: 1.12 };   // sun about twice as high: shadows half as long
const GRADE_ON = { expo: 1.25, curve: 0.18, lift: [0.01, 0.008, 0.016], gain: [1.0, 1.0, 1.0], gamma: 1.0, sat: 1.12, shadowTint: [0.99, 0.98, 1.03], highTint: [1.012, 1.0, 0.985], vignette: 0.1, grain: 0.01 };
const GRADE_OFF = { expo: 1, curve: 0, lift: [0, 0, 0], gain: [1, 1, 1], gamma: 1, sat: 1, shadowTint: [1, 1, 1], highTint: [1, 1, 1], vignette: 0, grain: 0 };

// The crowd's model-railway palette (owner's concept: camel, cream, pale blue, mustard; black only as accents).
export const CROWD_MINI = {
  clothes: ["#c8a97e", "#e6dcc6", "#8fa8c4", "#d4b25e", "#3f4c6e", "#d8b0a6", "#5f8a8c", "#efe6d2", "#a8866a", "#b8c4d2", "#c97a5a", "#7d8a72", "#a796c0", "#e3c87e", "#46546e", "#b45a4c"],
  hats: ["#efe6d2", "#d8c08a", "#c8a97e", "#e6dcc6", "#9fb4c8", "#d9a0a8", "#3a3a40"],
  accent: ["#e6a89b", "#9cbf98", "#e8d08a", "#a3bcd8", "#c2b0d8", "#f2ece0", "#c96f5f"],
  // morning dress for the top-hat figures: most in dove and mid grey, about one in four still in black
  tails: ["#8e9096", "#a3a5aa", "#7a7c82", "#b4b2ac", "#6e7076", "#9a958c", "#2a2b30", "#24262b"],
  tophat: ["#9a9ca2", "#aeb0b4", "#86888e", "#9a9ca2", "#bdbab2", "#2a2a2e", "#26262a"],
};

// ---------- Material patches ----------
// The turf: duller sage, a fine grain and soft broad patches (only the colour; the mown stripes are softened below).
export function patchTurf(mat) {
  if (!ON) return mat;
  const prev = mat.onBeforeCompile, prevKey = mat.customProgramCacheKey;
  mat.onBeforeCompile = (sh, r) => {
    if (prev) prev.call(mat, sh, r);
    sh.uniforms.uMiniTurf = U.turf;
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec2 vMiW;")
      .replace("#include <fog_vertex>", "#include <fog_vertex>\n{ vMiW = (modelMatrix * vec4(transformed, 1.0)).xz; }");
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", `#include <common>
        uniform float uMiniTurf; varying vec2 vMiW;
        float miH(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
        float miN(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
          return mix(mix(miH(i), miH(i + vec2(1, 0)), f.x), mix(miH(i + vec2(0, 1)), miH(i + vec2(1, 1)), f.x), f.y); }
        float miFine(vec2 p) { vec2 w = fwidth(p); return mix(0.5, miN(p), 1.0 - smoothstep(0.25, 0.7, max(w.x, w.y))); }`)
      .replace("#include <dithering_fragment>", `#include <dithering_fragment>
        if (uMiniTurf > 0.0) {
          vec3 g = gl_FragColor.rgb; float l = dot(g, vec3(0.3, 0.59, 0.11));
          vec3 sage = mix(vec3(l), g, 0.9) * vec3(0.98, 1.02, 0.95);
          sage *= (0.95 + 0.1 * (0.6 * miFine(vMiW * 9.0) + 0.4 * miFine(vMiW * 23.0))) * (0.96 + 0.08 * miN(vMiW / 9.0));
          gl_FragColor.rgb = mix(g, sage, uMiniTurf);
        }`);
  };
  mat.customProgramCacheKey = () => (prevKey ? prevKey.call(mat) : "") + "|mini-turf";
  mat.needsUpdate = true;
  return mat;
}
// The crowd: a little darker at the feet (as if stood in the grass) and a touch flatter, like painted figures.
export function patchCrowd(sh) {
  if (!ON) return;
  sh.uniforms.uMiniCrowd = U.crowd;
  sh.vertexShader = sh.vertexShader.replace("#include <common>", "#include <common>\nvarying float vMiH;")
    .replace("#include <begin_vertex>", "#include <begin_vertex>\nvMiH = position.y;");
  sh.fragmentShader = sh.fragmentShader.replace("#include <common>", "#include <common>\nuniform float uMiniCrowd; varying float vMiH;")
    .replace("#include <color_fragment>", `#include <color_fragment>
      diffuseColor.rgb *= mix(1.0, mix(0.72, 1.0, smoothstep(0.0, 1.0, vMiH)), uMiniCrowd);`)
    .replace("#include <opaque_fragment>", `outgoingLight = mix(outgoingLight, diffuseColor.rgb * 0.92, 0.25 * uMiniCrowd);
      #include <opaque_fragment>`);
}

// ---------- The finishing pass ----------
let post = null;
function makePost(renderer) {
  const depth = new THREE.DepthTexture(1, 1, THREE.UnsignedInt248Type);
  depth.format = THREE.DepthStencilFormat;
  // smoothed edges as the game's own picture has them (the game asks the browser for them on the screen; drawn into an
  // off-screen picture they must be asked for here, or every rail, roof line and figure comes out jagged)
  const rt = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: C.samples(), depthBuffer: true, stencilBuffer: true, depthTexture: depth });
  const mat = new THREE.ShaderMaterial({
    uniforms: {
      tColor: { value: rt.texture }, tDepth: { value: depth }, res: { value: new THREE.Vector2(1, 1) },
      near: { value: 0.5 }, far: { value: 4000 }, tanHalf: { value: 0.4 }, scale: { value: 1 }, seed: { value: 0 },
      tilt: { value: new THREE.Vector3(0, 0.5, 10) }, aoK: { value: new THREE.Vector2(0, 1.2) },
      hazeCol: { value: WARM.fog.clone() }, hazeK: { value: new THREE.Vector3(150, 1500, 0) },
      lift: { value: new THREE.Vector3() }, gain: { value: new THREE.Vector3(1, 1, 1) }, gammaV: { value: 1 }, sat: { value: 1 },
      shadowTint: { value: new THREE.Vector3(1, 1, 1) }, highTint: { value: new THREE.Vector3(1, 1, 1) }, vignette: { value: 0 }, grain: { value: 0 }, expo: { value: 1 }, curve: { value: 0 },
    },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `
      #include <packing>
      uniform sampler2D tColor, tDepth; uniform vec2 res, aoK;
      uniform float near, far, tanHalf, scale, seed, gammaV, sat, vignette, grain, expo, curve;
      uniform vec3 tilt, hazeCol, hazeK, lift, gain, shadowTint, highTint;
      varying vec2 vUv;
      float vz(vec2 uv) { return -perspectiveDepthToViewZ(texture2D(tDepth, uv).x, near, far); }
      float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      // tilt-shift: how blurred (pixels) a point is, by its height in the picture: sharp across a band
      // (tilt.y = where the band sits, 0 bottom, 1 top), blurring towards the top and the bottom
      float coc(vec2 uv) {
        float d = abs(uv.y - tilt.y);
        return tilt.x * smoothstep(0.07, 0.48, d) * tilt.z * scale;
      }
      void main() {
        float zc = vz(vUv);
        bool sky = texture2D(tDepth, vUv).x > 0.99999;
        vec3 c = texture2D(tColor, vUv).rgb;
        float cc = coc(vUv);
        if (cc > 0.6) {
          vec3 acc = c; float ws = 1.0; float j = hash(vUv * res + seed) * 6.283;
          for (int i = 0; i < 24; i++) {
            float fi = float(i) + 0.5, r = sqrt(fi / 24.0), a = fi * 2.39996 + j;
            vec2 o = vec2(cos(a), sin(a)) * r * cc / res;
            // a sharp thing in front is not smeared over what's behind it: take a sample only if it is
            // at least as blurred as the radius it is taken from
            float w = clamp(coc(vUv + o) / max(r * cc, 0.5), 0.0, 1.0);
            acc += texture2D(tColor, vUv + o).rgb * w; ws += w;
          }
          c = acc / ws;
        }
        // contact shading: where both sides of a pixel are nearer than it (under eaves, at the foot of a wall or
        // the rail, between people) it is in a fold and gets darker; flat ground and walls are left alone
        if (aoK.x > 0.0 && !sky) {
          float rpx = clamp(aoK.y * res.y / (2.0 * tanHalf * zc), 1.5, 40.0 * scale), occ = 0.0, j = hash(vUv * res) * 6.283;
          for (int i = 0; i < 10; i++) {
            float fi = float(i) + 0.5, r = sqrt(fi / 10.0), a = fi * 2.39996 + j;
            vec2 o = vec2(cos(a), sin(a)) * r * rpx / res;
            float d = zc - 0.5 * (vz(vUv + o) + vz(vUv - o));
            occ += clamp(d / aoK.y, 0.0, 1.0) * (1.0 - smoothstep(aoK.y * 2.0, aoK.y * 5.0, d));
          }
          c *= 1.0 - aoK.x * clamp(occ / 10.0 * 1.7, 0.0, 0.75);
        }
        // haze: things further off sink into the warm air (the sky is left alone)
        if (!sky) c = mix(c, hazeCol, hazeK.z * smoothstep(hazeK.x, hazeK.y, zc));
        // the game's own tone mapping and storybook grade (the same steps every other material takes on screen)
        c = toneMapping(c * expo);
        gl_FragColor = vec4(c, 1.0);
        #include <colorspace_fragment>
        c = gl_FragColor.rgb;
        // the miniature grade: saturation, lift and gain, gamma, warm highlights and soft violet shadows
        float l = dot(c, vec3(0.299, 0.587, 0.114));
        c = mix(vec3(l), c, sat);
        c = mix(c, c * c * (3.0 - 2.0 * c), curve);          // a gentle S-curve: a little more sparkle
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

// ---------- Live state ----------
let C = null;          // the race view's parts, from init()
let BASE = null;       // the race view's own values, to go back to when a switch is off

export function init(ctx) {
  if (!ON) return;
  C = ctx;
  const sk = C.scene.userData.sky.material.uniforms;
  BASE = {
    sky: ["c0", "c1", "c2", "c3"].map((k) => sk[k].value.clone()),
    sun: C.sun.color.clone(), sunI: C.sun.intensity,
    hemiSky: C.hemi.color.clone(), hemiGround: C.hemi.groundColor.clone(), hemiI: C.hemi.intensity,
    fog: C.scene.fog ? C.scene.fog.color.clone() : null,
    sunOffset: C.sunOffset.clone(), radius: C.sun.shadow.radius,
    cloud: C.scene.userData.cloudMat ? C.scene.userData.cloudMat.color.clone() : null,
  };
  apply();
  buildPanel();
}

// the storybook grade re-colours the haze each time it's switched: take that as the game's own, keep ours on top
export function afterGrade() { if (C && C.scene.fog) { BASE.fog = C.scene.fog.color.clone(); applyLight(); } }

function applyLight() {
  const on = !!S.light, sk = C.scene.userData.sky.material.uniforms;
  ["c0", "c1", "c2", "c3"].forEach((k, i) => sk[k].value.copy(on ? WARM.sky[i] : BASE.sky[i]));
  C.sun.color.copy(on ? WARM.sun : BASE.sun);
  C.sun.intensity = on ? WARM.sunI : BASE.sunI;
  C.hemi.color.copy(on ? WARM.hemiSky : BASE.hemiSky);
  C.hemi.groundColor.copy(on ? WARM.hemiGround : BASE.hemiGround);
  C.hemi.intensity = (on ? WARM.hemiI : BASE.hemiI) * (S.shadows ? SOFT.hemiBoost : 1);
  if (C.scene.fog && BASE.fog) C.scene.fog.color.copy(on || S.haze ? WARM.fog : BASE.fog);
}
function applyShadows() {
  const on = !!S.shadows;
  C.sunOffset.copy(BASE.sunOffset);
  if (on) { C.sunOffset.y *= SOFT.up; }
  C.sun.shadow.radius = on ? SOFT.radius : BASE.radius;
  // soft edges need the plain filtered kind of shadow (the "soft" kind ignores the radius); every material
  // is rebuilt for the change, a moment's pause
  const type = on ? SOFT.type : C.shadowType();
  if (type !== C.renderer.shadowMap.type) { C.renderer.shadowMap.type = type; C.recompile(); }
  C.sun.shadow.needsUpdate = true;
}
// Where the shadows fall. The game only shades shadows in a box round the field (90 m across) and only onto the
// turf right round the runners (the ground is painted, not lit), so buildings and people cast nothing on the lawns.
// With soft shadows on, the box and the ground that takes shadows follow the view instead: about 300 m across,
// round what the camera is looking at (or round the field in the race), so the stands and crowd sit on their
// shadows. Off: exactly the game's.
const GAME_BOX = 45, _v = new THREE.Vector3(), _d = new THREE.Vector3();
export function afterSun(sunAt, cam, focus) {
  const cat = C.catcher(), sc = C.sun.shadow.camera;
  const half = S.shadows ? 150 : GAME_BOX;
  if (S.shadows) {
    // centre: where the view looks, on the ground, no further than 220 m out
    if (VIEWS[view]) {
      _d.copy(focus).sub(cam.position); _d.y = 0;
      const L = Math.min(_d.length(), 250);
      _v.copy(cam.position).addScaledVector(_d.normalize(), L); _v.y = 0;
    } else _v.copy(sunAt);
    C.sun.position.copy(_v).add(C.sunOffset); C.sun.target.position.copy(_v);
    if (cat) { cat.position.set(_v.x, 0.03, _v.z); cat.rotation.y = 0; cat.scale.set(2 * half / 120, 1, 2 * half / 44); cat.material.opacity = 0.42; cat.material.color.set("#2a2838"); }
  } else if (cat) { cat.scale.set(1, 1, 1); cat.material.opacity = 0.38; cat.material.color.set("#1d2c14"); }
  if (sc.right !== half) { Object.assign(sc, { left: -half, right: half, top: half, bottom: -half }); sc.updateProjectionMatrix(); }
}
function applyTurf() {
  U.turf.value = S.turf ? 1 : 0;
  for (const u of C.lanes()) u.value.w = u.base * (S.turf ? 0.8 : 1);
}
function applyCrowd() {
  U.crowd.value = S.crowd ? 1 : 0;
  C.crowdPalette(!!S.crowd);
}
function apply() {
  applyLight(); applyShadows(); applyTurf(); applyCrowd();
  writeHash();
  C.redraw();
}

// Draw a frame through the finishing pass. focus/auto as looks.js (unused for now: the blur is by height in the picture).
const _sz = new THREE.Vector2();
let fogBase = null;
export function render(renderer, scene, camera) {
  if (!post) post = makePost(renderer);
  renderer.getDrawingBufferSize(_sz);
  if (post.rt.samples !== C.samples()) { post.rt.dispose(); post.rt.samples = C.samples(); }
  if (post.rt.width !== _sz.x || post.rt.height !== _sz.y) post.rt.setSize(_sz.x, _sz.y);
  const u = post.mat.uniforms;
  u.res.value.copy(_sz); u.near.value = camera.near; u.far.value = camera.far;
  u.tanHalf.value = Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2);
  u.scale.value = _sz.y / 720; u.seed.value = (u.seed.value + 1) % 97;
  u.tilt.value.set(S.tilt ? S.tiltAmt : 0, S.tiltBand, 14);
  u.aoK.value.set(S.contact ? S.contactAmt : 0, 1.0);
  // a long lens looks a long way through thin air: stretch the haze with it, so the subject keeps its colour
  const lens = THREE.MathUtils.clamp(40 / camera.fov, 1, 8);
  if (scene.fog) {
    if (!fogBase) fogBase = [scene.fog.near, scene.fog.far];
    scene.fog.near = fogBase[0] * lens; scene.fog.far = fogBase[1] * lens;
  }
  u.hazeK.value.set(450 * lens, 2600 * lens, S.haze ? S.hazeAmt : 0);
  u.hazeCol.value.copy(WARM.fog);
  const G = S.grade ? GRADE_ON : GRADE_OFF;
  u.lift.value.set(...G.lift); u.gain.value.set(...G.gain); u.gammaV.value = G.gamma; u.sat.value = G.sat;
  u.shadowTint.value.set(...G.shadowTint); u.highTint.value.set(...G.highTint); u.vignette.value = G.vignette; u.grain.value = G.grain; u.expo.value = G.expo; u.curve.value = G.curve;
  renderer.setRenderTarget(post.rt);
  renderer.render(scene, camera);
  renderer.setRenderTarget(null);
  renderer.render(post.scene, post.cam);
}

// ---------- Views: the same eyes as the Blender preview stills (tools/blender/preview_rowley_stands.py) ----------
// course (x, z, height) from and to, Blender lens (mm, 36 mm sensor across)
const VIEWS = {
  race:     null,                                                    // the TV director, as in the game
  post:     [[70, 8, 8], [-60, 70, 12], 24, "From the winning post"],
  across:   [[30, -3, 6], [30, 125, 22], 20, "Across from the far side"],
  aerial:   [[110, -230, 190], [110, 70, 0], 26, "From above"],
  festival: [[470, -3, 6], [470, 70, 6], 22, "Festival up the course"],
  upcourse: [[-55, 14, 24], [700, 0, 0], 30, "Up the course"],
  farside:  [[60, 75, 22], [60, -45, 0], 24, "From the stands to the far side"],
  balloons: [[300, 8, 5], [345, 46, 5.5], 30, "The balloon pods"],
};
let view = P.get("view") && VIEWS[P.get("view")] !== undefined ? P.get("view") : "post";
let orbit = null;      // a nudge from dragging on the picture: [yaw, pitch] in radians
export function camera(cam, focus) {
  if (!ON || !VIEWS[view]) return false;
  const [f, t, lens] = VIEWS[view];
  cam.position.set(f[0], f[2], f[1]);
  const at = new THREE.Vector3(t[0], t[2], t[1]);
  if (orbit) {
    const d = at.clone().sub(cam.position), r = d.length();
    const yaw = Math.atan2(d.x, d.z) + orbit[0], pitch = THREE.MathUtils.clamp(Math.asin(d.y / r) + orbit[1], -1.5, 1.2);
    at.copy(cam.position).add(new THREE.Vector3(Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(yaw) * Math.cos(pitch)).multiplyScalar(r));
  }
  cam.lookAt(at);
  const hfov = 2 * Math.atan(18 / lens);
  cam.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(hfov / 2) / cam.aspect));
  cam.updateProjectionMatrix();
  focus.copy(at);
  return true;
}
export function fixedView() { return ON && !!VIEWS[view]; }

// ---------- The panel ----------
const SWITCHES = [
  ["light", "Warm light and sky", "the biggest change: warm sun, cream horizon, softer blue"],
  ["haze", "Haze", "distant things fade into warm air"],
  ["shadows", "Soft, short shadows", "a higher sun, soft edges, lighter shade"],
  ["contact", "Contact shading", "soft darkening where things meet"],
  ["tilt", "Tilt-shift blur", "sharp band, blurred top and bottom"],
  ["grade", "Colour grade", "one warm colour family"],
  ["crowd", "Crowd colours", "muted model-railway palette, grey toppers"],
  ["turf", "Softer turf", "duller sage, fine grain, gentler stripes"],
];
const SLIDERS = [
  ["tiltAmt", "Blur strength", 0, 1, "tilt"], ["tiltBand", "Sharp band height", 0.2, 0.8, "tilt"],
  ["hazeAmt", "Haze strength", 0, 1, "haze"], ["contactAmt", "Contact strength", 0, 1, "contact"],
];
let saved = null;      // the switches before "Before" was pressed
function buildPanel() {
  const css = document.createElement("style");
  css.textContent = `
    .mini { position: fixed; top: calc(env(safe-area-inset-top, 0px) + 12px); right: max(12px, env(safe-area-inset-right, 0px)); z-index: 50;
      width: 270px; max-width: calc(100vw - 24px); max-height: calc(100vh - 24px); overflow: auto;
      background: #f4ead2; color: #183f2a; border: 1px solid #b8954a; border-radius: 3px; font: 13px "Jost", "Helvetica Neue", Arial, sans-serif;
      box-shadow: 0 0 0 3px #f4ead2, 0 0 0 4px #b8954a, 0 8px 22px rgba(20,30,20,.3); padding: 10px 12px 12px; }
    .mini h2 { margin: 0 0 2px; font: 600 1.05rem "Cormorant SC", "Times New Roman", serif; letter-spacing: .08em; color: #1f5a38; }
    .mini p.sub { margin: 0 0 8px; font-size: .74rem; color: #4f5d4a; }
    .mini .row { display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0; }
    .mini button { font: 500 .78rem "Jost", Arial, sans-serif; color: #183f2a; background: transparent; cursor: pointer;
      border: 1px solid rgba(31,90,56,.35); border-radius: 3px; padding: 4px 8px; }
    .mini button[aria-pressed="true"] { background: #1f5a38; color: #f4ead2; border-color: #1f5a38; }
    .mini label.sw { display: grid; grid-template-columns: 18px 1fr; gap: 0 6px; align-items: start; padding: 4px 0; border-top: 1px solid rgba(184,149,74,.35); cursor: pointer; }
    .mini label.sw input { margin: 2px 0 0; accent-color: #1f5a38; }
    .mini label.sw b { font-weight: 500; }
    .mini label.sw small { grid-column: 2; color: #4f5d4a; font-size: .7rem; }
    .mini label.sl { display: grid; grid-template-columns: 1fr 110px; align-items: center; gap: 6px; font-size: .74rem; color: #4f5d4a; padding: 2px 0 2px 24px; }
    .mini label.sl input { width: 100%; accent-color: #1f5a38; }
    .mini select { font: .8rem "Jost", Arial, sans-serif; width: 100%; padding: 3px; border: 1px solid rgba(31,90,56,.35); border-radius: 3px; background: #fbf7ec; color: #183f2a; }
    .mini .hint { font-size: .7rem; color: #4f5d4a; margin: 6px 0 0; }
    .mini-hidden .mini, .mini-hidden .plate, .mini-hidden .bar, .mini-hidden .dock, .mini-hidden #call, .mini-hidden .call { display: none !important; }
    .mini-tab { position: fixed; right: 12px; bottom: 12px; z-index: 51; display: none; font: 500 .78rem "Jost", Arial, sans-serif;
      background: #f4ead2; color: #183f2a; border: 1px solid #b8954a; border-radius: 3px; padding: 5px 9px; cursor: pointer; opacity: .8; }
    .mini-hidden .mini-tab { display: block; }
    @media (max-width: 640px) { .mini { top: auto; bottom: 12px; width: auto; left: 12px; max-height: 46vh; } }`;
  document.head.append(css);
  const el = document.createElement("div");
  el.className = "mini";
  el.innerHTML = `<h2>Miniature look test</h2><p class="sub">Each switch is one of the differences from the concept stills.</p>
    <select id="miView" aria-label="View"></select>
    <div class="row"><button id="miAll">All on</button><button id="miNone">All off</button><button id="miBefore" title="Hold to see the game as it is (or press B)">Hold: before</button><button id="miHide" title="H">Hide panels</button></div>
    <div id="miSw"></div>
    <div class="row"><button id="miReset">Reset sliders</button></div>
    <p class="hint">Drag on the picture to look around a view. B: before/after. H: hide panels. The address keeps your settings.</p>`;
  document.body.append(el);
  const tab = document.createElement("button"); tab.className = "mini-tab"; tab.textContent = "Show panels"; document.body.append(tab);
  tab.onclick = () => document.documentElement.classList.remove("mini-hidden");

  const sel = el.querySelector("#miView");
  for (const [id, v] of Object.entries(VIEWS)) sel.add(new Option(v ? v[3] : "The race (TV director)", id));
  sel.value = view;
  sel.onchange = () => { view = sel.value; orbit = null; const p = new URLSearchParams(location.search); p.set("view", view); history.replaceState(null, "", location.pathname + "?" + p + location.hash); C.redraw(); };

  const box = el.querySelector("#miSw"), inputs = {};
  for (const [k, label, note] of SWITCHES) {
    const lab = document.createElement("label"); lab.className = "sw";
    lab.innerHTML = `<input type="checkbox"><span><b>${label}</b></span><small>${note}</small>`;
    const inp = lab.querySelector("input"); inp.checked = !!S[k]; inputs[k] = inp;
    inp.onchange = () => { S[k] = inp.checked ? 1 : 0; saved = null; apply(); };
    box.append(lab);
    for (const [sk, sl, lo, hi, owner] of SLIDERS.filter((s) => s[4] === k)) {
      const r = document.createElement("label"); r.className = "sl";
      r.innerHTML = `<span>${sl}</span><input type="range" min="${lo}" max="${hi}" step="0.01">`;
      const ri = r.querySelector("input"); ri.value = S[sk]; inputs[sk] = ri;
      ri.oninput = () => { S[sk] = +ri.value; writeHash(); C.redraw(); };
      box.append(r);
    }
  }
  const sync = () => { for (const k in inputs) { if (inputs[k].type === "checkbox") inputs[k].checked = !!S[k]; else inputs[k].value = S[k]; } };
  const setAll = (v) => { for (const [k] of SWITCHES) S[k] = v; saved = null; sync(); apply(); };
  el.querySelector("#miAll").onclick = () => setAll(1);
  el.querySelector("#miNone").onclick = () => setAll(0);
  el.querySelector("#miReset").onclick = () => { for (const [k] of SLIDERS) S[k] = DEFAULTS[k]; sync(); writeHash(); C.redraw(); };
  // before/after: hold the button (or B) to see the game as it is, let go for the test
  const before = (down) => {
    if (down && !saved) { saved = Object.fromEntries(SWITCHES.map(([k]) => [k, S[k]])); for (const [k] of SWITCHES) S[k] = 0; apply(); }
    else if (!down && saved) { Object.assign(S, saved); saved = null; apply(); }
    el.querySelector("#miBefore").setAttribute("aria-pressed", down);
  };
  const bb = el.querySelector("#miBefore");
  bb.onpointerdown = (e) => { e.preventDefault(); before(true); };
  for (const ev of ["pointerup", "pointerleave", "pointercancel"]) bb.addEventListener(ev, () => before(false));
  const hide = () => document.documentElement.classList.toggle("mini-hidden");
  el.querySelector("#miHide").onclick = hide;
  addEventListener("keydown", (e) => {
    if (e.target.closest && e.target.closest("input, select, textarea")) return;
    if (e.key === "b" || e.key === "B") { if (!e.repeat) before(true); }
    else if (e.key === "h" || e.key === "H") hide();
  });
  addEventListener("keyup", (e) => { if (e.key === "b" || e.key === "B") before(false); });
  // drag on the picture to look round from the view's eye
  const canvas = C.renderer.domElement;
  let drag = null;
  canvas.addEventListener("pointerdown", (e) => { if (!VIEWS[view]) return; drag = [e.clientX, e.clientY, ...(orbit || [0, 0])]; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    orbit = [drag[2] - (e.clientX - drag[0]) * 0.003, drag[3] - (e.clientY - drag[1]) * 0.003];
    C.redraw();
  });
  canvas.addEventListener("pointerup", () => (drag = null));
  // checking aid: set switches from a script (headless stills)
  window.__mini = { S, apply: (o) => { Object.assign(S, o); sync(); apply(); }, view: (v) => { sel.value = v; sel.onchange(); } };
}
