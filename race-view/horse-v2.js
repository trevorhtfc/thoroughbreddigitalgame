// The v2 racehorse for the web race view: loading, colouring, detail levels, the gallop and the jockey's
// riding. Built by tools/blender/build_racehorse_v2.py (see assets/models/racehorse_v2_rig.json) and
// packaged by tools/web/package_racehorse_v2.py. Final Furlong uses it with ?horse=v2; v1 is untouched.
//
// Everything the horse and jockey do is driven by the race timeline's speed and effort, or is cosmetic
// per runner (chosen once from its seed): the view still only plays a race back.
import * as THREE from "three";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";

const STRIDE_SPEED = 14.6;        // m/s at which one stride clip matches the ground at scale 3
const SCALE = 3;
const V1 = "assets/model/racehorse-3d-model-clone1-";        // v2 reuses v1's normal and roughness maps
// The jockey's face is the original model's painting (owner's reference). Each jockey's skin tone is that
// painting multiplied by one of these (linear light; [1, 1, 1] = exactly as painted). Goggles stay dark.
const SKIN = [[1.22, 1.17, 1.12], [1.1, 1.06, 1.03], [1, 1, 1], [1, 1, 1], [0.84, 0.78, 0.72], [0.6, 0.53, 0.46], [0.4, 0.34, 0.28]];
const VARIETY = ["jky_crouch_low", "jky_crouch_high", "jky_elbows_out", "jky_hands_long", "horse_head_high", "horse_head_low", "horse_tail_high",
  "jky_look_left", "jky_look_right", "jky_stand"];
const MOMENTS = ["jky_look_left", "jky_look_right", "jky_stand"];   // not part of how he sits: they come and go (a look round, pulling up)

function seeded(seed) {
  let s = (seed * 2654435761) >>> 0 || 1;
  return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
}

// Load once: the model (three detail levels), its clips (variety poses made additive) and the shared maps.
export async function loadHorse(loadModel, dir = "assets/model-v2", tex) {
  const gltf = await loadModel(dir, "racehorse_v2");
  const load = tex || ((url, srgb) => { const t = new THREE.TextureLoader().load(url); t.flipY = false; if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t; });
  const maps = {
    base: load(dir + "/racehorse_v2-basecolor.jpg", true),          // v1's grey texture with the face painted back
    normal: load(V1 + "normal.jpg", false), rm: load(V1 + "rm.jpg", false),
    shade: load(dir + "/racehorse_v2-silks-shading.png", true),     // the helmet's light and shade, in the silks layout
  };
  maps.base.anisotropy = 4; maps.shade.wrapS = THREE.RepeatWrapping;
  const clips = {};
  for (const c of gltf.animations) {
    clips[c.name] = VARIETY.includes(c.name) ? THREE.AnimationUtils.makeClipAdditive(c.clone(), 0) : c;
  }
  return { gltf, clips, maps };
}

const NO_SHEEN = new URLSearchParams(globalThis.location ? location.search : "").has("oldcoat");   // checking aid: the coat as it was lit before
export const debug = { zones: false };     // checking aid: main zones (coat red, points green, face blue), silks as their uv

const silkCache = new Map();
// silk: one of the ready-made sets (its texture is a file), or colours a player made themselves (silk.spec:
// painted here by silks-paint.js, in the same layout)
function silkTexture(silk, load) {
  const own = silk.spec && globalThis.SilksPaint ? silk.spec : null, id = own ? "own:" + globalThis.SilksPaint.encode(own) : silk.id;
  if (!silkCache.has(id)) {
    let t;
    if (own) { t = new THREE.CanvasTexture(globalThis.SilksPaint.texture(own, 1024, "v2")); t.flipY = false; t.colorSpace = THREE.SRGBColorSpace; }
    else t = load(`assets/silks-3d-v2/${id}.png`, true);
    t.wrapS = THREE.RepeatWrapping; t.anisotropy = 8;
    silkCache.set(id, t);
  }
  return silkCache.get(id);
}

// Main material: the neutral grey texture, multiplied by the coat and points colours inside their zones; the
// jockey's face keeps its painting (B zone), shifted to his skin tone. The zones are vertex colours (R coat,
// G points, B face), so each colour stops exactly at its edge.
function mainMaterial(src, maps, u) {
  const m = src.clone();
  // Nothing on a horse is metal bar the bit and irons, and the model's metal map called patches of the dock, the
  // quarters and the saddle cloth metal, which caught the sun as grey-white flares. So: no metal, and the roughness
  // map kept, a touch smoother, for the soft sheen of a groomed coat.
  m.map = maps.base; m.normalMap = maps.normal; m.roughnessMap = maps.rm; m.metalnessMap = NO_SHEEN ? maps.rm : null;
  m.color.set("#ffffff"); m.metalness = NO_SHEEN ? 1 : 0; m.roughness = NO_SHEEN ? 1 : 0.9; m.vertexColors = true;
  m.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, u);
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nuniform vec3 coatCol; uniform vec3 pointsCol; uniform vec3 skinTone;")
      .replace("#include <color_fragment>", `
        {
          vec3 zm = vColor.rgb;
          vec3 tex = diffuseColor.rgb;
          float l = dot(tex, vec3(0.2126, 0.7152, 0.0722));
          vec3 c = vec3(l);
          vec3 coat = coatCol * clamp(mix(1.0, l / 0.56, 0.65), 0.3, 1.25);
          vec3 pts = pointsCol * mix(0.75, 1.2, smoothstep(0.0, 0.035, l));
          float hk = zm.r + zm.g;                       // coat and points share the blend at the mane's edge,
          vec3 hc = (coat * zm.r + pts * zm.g) / max(hk, 1e-4);   // with none of the grey texture showing through
          c = mix(c, hc, clamp(hk, 0.0, 1.0)); c = mix(c, tex * skinTone, zm.b);${debug.zones ? "\n          c = zm;" : ""}
          diffuseColor.rgb = c;
        }`);
  };
  m.customProgramCacheKey = () => "horse-v2-main" + (debug.zones ? "-zones" : "");
  return m;
}
// Silks: the owner's silks texture, times the fabric creases (vertex colours, jacket and sleeves) and the
// helmet's light and shade (one shared map in the silks layout, white everywhere but the helmet).
function silksMaterial(src, map, shade) {
  const m = src.clone();
  m.map = map; m.color.set("#ffffff"); m.roughness = 0.62; m.metalness = 0; m.vertexColors = true;
  m.onBeforeCompile = (shader) => {
    shader.uniforms.shadeMap = { value: shade };
    shader.fragmentShader = shader.fragmentShader
      .replace("#include <common>", "#include <common>\nuniform sampler2D shadeMap;")
      .replace("#include <map_fragment>", "#include <map_fragment>\ndiffuseColor.rgb *= texture2D(shadeMap, vMapUv).r;" +
        (debug.zones ? "\ndiffuseColor.rgb = vec3(fract(vMapUv), 0.0);" : ""));
  };
  m.customProgramCacheKey = () => "horse-v2-silks" + (debug.zones ? "-zones" : "");
  return m;
}

// One runner: { obj, update(dt, speed, effort, camera), setTime(t), level }
export function makeRunner(proto, { coat, silk, seed = 1, texLoader, castShadow = true, skin }) {
  const rnd = seeded(seed + 17);
  const obj = SkeletonUtils.clone(proto.gltf.scene);
  obj.scale.setScalar(SCALE);
  const load = texLoader || ((url, srgb) => { const t = new THREE.TextureLoader().load(url); t.flipY = false; if (srgb) t.colorSpace = THREE.SRGBColorSpace; return t; });
  const u = {
    coatCol: { value: new THREE.Color(coat.body) }, pointsCol: { value: new THREE.Color(coat.points) },
    skinTone: { value: new THREE.Vector3(...SKIN[(() => { const k = Math.floor(rnd() * SKIN.length); return skin == null ? k : skin; })()]) },
  };
  const mats = new Map();
  const levels = [[], [], []];
  const sized = [];
  obj.traverse((o) => {
    if (!o.isSkinnedMesh) return;
    o.castShadow = castShadow; o.frustumCulled = false;
    const src = o.material;
    if (!mats.has(src.name)) mats.set(src.name, src.name.includes("silks") ? silksMaterial(src, silkTexture(silk, load), proto.maps.shade) : mainMaterial(src, proto.maps, u));
    o.material = mats.get(src.name);
    sized.push(o);
  });
  // group the meshes into the three detail levels, by triangle count (biggest = close)
  const count = (o) => (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3;
  const total = new Map();
  sized.forEach((o) => { const k = o.parent && o.parent.isGroup && o.parent !== obj ? o.parent.uuid : o.uuid; total.set(k, (total.get(k) || 0) + count(o)); });
  const rank = [...total.entries()].sort((a, b) => b[1] - a[1]).map(([k]) => k);
  sized.forEach((o) => { const k = o.parent && o.parent.isGroup && o.parent !== obj ? o.parent.uuid : o.uuid; levels[Math.min(2, rank.indexOf(k))].push(o); });

  const mixer = new THREE.AnimationMixer(obj);
  const actions = {};
  for (const [name, clip] of Object.entries(proto.clips)) {
    const a = mixer.clipAction(clip);
    if (VARIETY.includes(name)) { a.blendMode = THREE.AdditiveAnimationBlendMode; a.play(); a.paused = true; a.time = clip.duration; a.setEffectiveWeight(0); }
    else a.play();
    actions[name] = a;
  }
  // cosmetic variety, chosen once: how he sits, how she carries her head and tail, stride rhythm, timing
  const crouch = rnd() * 2 - 1, head = rnd() * 2 - 1;
  const look = {
    jky_crouch_low: Math.max(0, crouch) * 0.9, jky_crouch_high: Math.max(0, -crouch) * 0.7,
    jky_elbows_out: rnd() * 0.9, jky_hands_long: rnd() * 0.8,
    horse_head_high: Math.max(0, head) * 0.9, horse_head_low: Math.max(0, -head) * 0.9, horse_tail_high: rnd() * 0.8,
  };
  for (const [k, w] of Object.entries(look)) actions[k] && actions[k].setEffectiveWeight(w);
  // a look round for dangers now and then while he is sitting quietly: some jockeys often, some hardly ever,
  // each with a side he favours. Cosmetic: from his seed and his own clock, never from the race.
  const glance = { every: 5 + rnd() * 14, left: 0.25 + rnd() * 0.5, next: 2 + rnd() * 12, t: 0, side: null, w: 0 };
  let stand = 0;
  const cadence = 0.955 + rnd() * 0.09;                       // a touch quicker or slower in the stride
  const lag = rnd() * 0.04;                                  // the jockey's push a little before or after the stride
  const vigour = 0.85 + rnd() * 0.3;                         // how hard he rides for the same effort
  const RIDE = ["ride_quiet", "ride_push", "ride_drive", "ride_whip"];
  let effort = 0, horseEffort = 0, level = 1;
  const setLevel = (k) => { level = k; levels.forEach((L, i) => L.forEach((o) => (o.visible = i === k))); };
  setLevel(1);
  const _v = new THREE.Vector3();
  return {
    obj, mixer, actions, look: Object.assign({ cadence, lag, vigour }, look), kind: "v2",
    get level() { return level; },
    setTime(t) {
      for (const [n, a] of Object.entries(actions)) if (!VARIETY.includes(n)) a.time = (t + (RIDE.includes(n) ? lag : 0)) % a.getClip().duration;
    },
    // speed m/s, effort 0..3 from the race timeline (0 quiet, 1 push, 2 drive, 3 whip); ease 0..1: pulling up
    // after the line (he stands in his irons)
    update(dt, v, eff, camera, step = dt, ease = 0) {
      effort += (Math.min(3, eff) * (eff > 0.05 ? vigour : 1) - effort) * Math.min(1, dt * 2.2);
      horseEffort += (effort - horseEffort) * Math.min(1, dt * 1.5);   // the horse answers a beat later
      const e = THREE.MathUtils.clamp(effort, 0, 3);
      const set = (n, w) => actions[n] && actions[n].setEffectiveWeight(w);
      set("ride_quiet", Math.max(0, 1 - e)); set("ride_push", Math.max(0, 1 - Math.abs(e - 1)));
      set("ride_drive", Math.max(0, 1 - Math.abs(e - 2))); set("ride_whip", THREE.MathUtils.clamp(e - 2, 0, 1));
      const w = 1 - THREE.MathUtils.smoothstep(v, 0.3, 4.5);             // standing in the stalls: the walk, nearly still
      const d = Math.min(1, horseEffort / 2) * 0.85;
      set("walk", w); set("gallop_v2", (1 - d) * (1 - w)); set("gallop_v2_drive", d * (1 - w));
      // moments: standing in the irons as he pulls up; a look round while he sits quietly
      stand += (THREE.MathUtils.clamp(ease, 0, 1) * (1 - w) - stand) * Math.min(1, dt * 1.6);
      set("jky_stand", stand);
      if (step > 0 && dt < 1) {
        glance.t += step;
        if (glance.side === null && glance.t > glance.next && e < 0.6 && w < 0.05 && stand < 0.1) { glance.side = rnd() < glance.left ? "jky_look_left" : "jky_look_right"; glance.t = 0; }
        if (glance.side !== null) {
          const u = glance.t / 1.5;                                          // round, hold, back: a second and a half
          glance.w = e > 1.2 ? glance.w * Math.max(0, 1 - dt * 6) : THREE.MathUtils.smoothstep(u, 0, 0.3) * (1 - THREE.MathUtils.smoothstep(u, 0.62, 1));
          set(glance.side, glance.w);
          if (u >= 1 || (e > 1.2 && glance.w < 0.01)) { set(glance.side, 0); glance.side = null; glance.t = 0; glance.next = glance.every * (0.5 + rnd()); }
        }
      }
      mixer.timeScale = v < 0.3 ? 0.06 : THREE.MathUtils.clamp((v / STRIDE_SPEED) * cadence, 0.3, 1.45);
      mixer.update(step);
      if (camera) {                                                          // on its own (the studio): detail by size on screen
        const frac = this.screenFrac(camera);
        const want = frac > (level === 0 ? 0.17 : 0.21) ? 0 : frac < (level === 2 ? 0.075 : 0.06) ? 2 : 1;
        if (want !== level) setLevel(want);
      }
    },
    // how much of the screen's height the horse and jockey fill (about 2 m tall)
    screenFrac(camera) {
      obj.getWorldPosition(_v);
      const dist = Math.max(0.1, _v.distanceTo(camera.position));
      return 2.0 / (2 * dist * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2));
    },
    setLevel,
    hold(name, weight) { if (MOMENTS.includes(name) && actions[name]) { actions[name].setEffectiveWeight(weight); mixer.update(0); } },   // checking aid: a moment held in a still
  };
}

// For a field: detail levels by size on screen, with at most 'close' runners at the close level (the
// biggest on screen), so a telephoto shot of a big field never draws every horse at full detail.
// Far: smaller than about 6% of the screen's height. Close: bigger than about a fifth.
// 'far' moves the far level's threshold (the Lightest quality uses the far horse for more of the field).
export function chooseLevels(list, camera, { close = 4, far = 0.06 } = {}) {
  const sized = list.map((r, i) => [r.screenFrac(camera), i]).sort((a, b) => b[0] - a[0]);
  sized.forEach(([f, i], k) => {
    const r = list[i], cur = r.level;
    let lv = f < (cur === 2 ? far * 1.25 : far) ? 2 : 1;
    if (k < close && f > (cur === 0 ? 0.17 : 0.21)) lv = 0;
    if (lv !== cur) r.setLevel(lv);
  });
}
