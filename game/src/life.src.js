// =====================================================================================================================
// Life on the Newmarket board (from newmarket-live/): strings walking out, lots on the gallops, horseboxes on the
// roads, horses and lads in the yards, drawn in 3D in the board's own projection so they sit in the picture at its scale.
// Needs three.js; if it can't load, the board (js/board.js) still works without them.
// Also the game's processions: the yearlings led to Tattersalls, your new string walking to your yard, the horseboxes
// leaving for the races (window.LIFE.procession).
// =====================================================================================================================
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";

const B = window.BOARD;
const { MW, MH, REDUCED, ROAD, inHours, join, rev } = B;
let renderer = null, lost = false;
const RB = [632, 294];                                             // the roundabout at the top of the High Street
// ---------------------------------------------------------------- the moving things, drawn in the board's own projection
// world: x = board x, z = board y (both pixels), y = height in pixels. The board is drawn as if from the south with
// heights straight up the page, so a point lands on the board at (x, z - y). Nearer the viewer = further south, higher.
const canvas = document.getElementById("life");
const scene = new THREE.Scene();
const cam = new THREE.Camera();
cam.matrixAutoUpdate = false; cam.matrixWorldAutoUpdate = false;
cam.projectionMatrix.set(2 / MW, 0, 0, -1,
                         0, 2 / MH, -2 / MH, 1,
                         0, -0.0015, -0.0015, 0.9,
                         0, 0, 0, 1);
cam.projectionMatrixInverse.copy(cam.projectionMatrix).invert();
scene.add(new THREE.HemisphereLight(0xfff4dc, 0x7d7458, 1.5));
const sun = new THREE.DirectionalLight(0xfff0d0, 1.7); sun.position.set(-0.7, 1.1, -0.5); scene.add(sun);

// assets/occlusion.png (tools/occlusion.py): for each board pixel showing a building or tree, the board y of its foot.
// A fragment of a horse, person or horsebox is dropped where something standing further south is drawn over it.
const OCC = { occ: { value: null }, uRes: { value: new THREE.Vector2(MW, MH) } };
function occluded(mat, ground) {
  const prev = mat.onBeforeCompile;
  mat.onBeforeCompile = (sh, r) => {
    if (prev) prev(sh, r);
    Object.assign(sh.uniforms, OCC, { uGround: ground });
    sh.fragmentShader = sh.fragmentShader.replace("#include <common>", "#include <common>\nuniform sampler2D occ; uniform vec2 uRes; uniform float uGround;")
      .replace("#include <clipping_planes_fragment>", `#include <clipping_planes_fragment>
        { vec2 uvb = vec2(gl_FragCoord.x / uRes.x, 1.0 - gl_FragCoord.y / uRes.y);
          vec4 o = texture2D(occ, uvb); float foot = o.r * 65280.0 + o.g * 255.0 - 1.0;
          if (foot > 0.0 && foot > uGround + 6.0) discard; }`);
  };
  const key = mat.customProgramCacheKey ? mat.customProgramCacheKey() : "";
  mat.customProgramCacheKey = () => key + "-occ";
}
const shadowTex = (() => { const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
  const r = g.createRadialGradient(32, 32, 0, 32, 32, 32); r.addColorStop(0, "rgba(30,26,12,.55)"); r.addColorStop(1, "rgba(30,26,12,0)");
  g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const shadowGeo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
function addShadow(obj, len, wid) {
  const mat = new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false }); occluded(mat, obj.userData.ground);
  const s = new THREE.Mesh(shadowGeo, mat); s.scale.set(len, 1, wid); s.renderOrder = -1; scene.add(s); obj.userData.shadow = s; return s; }

// ---- routes: the owner's red (strings), blue (horseboxes) and pink (yards and paddocks) lines, kept to the roads
const P = (pts, closed = false) => { const c = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, 0, z)), closed, "centripetal"); c.L = c.getLength(); return c; };
const STRINGS = [
  // from the National Stud, down Bury Road, round by Exeter Road and out across the Gallops
  { route: join([[905, 262], [874, 247], [847, 228], [818, 208], [790, 194]], [[780, 198], [740, 222], [700, 250], [660, 280], RB], [[630, 262], [629, 236]], ROAD.exeter.slice(1),
      [[270, 282], [230, 258], [190, 236], [150, 214], [110, 195], [70, 180], [30, 166], [-20, 152]]), n: 6, silk: "ballydoyle-navy", start: 0 },
  // from Tattersalls, up Kingston Road, down the High Street, out along Station Road onto Warren Hill
  { route: join([[752, 517], [729, 520], [702, 535], [671, 548], [640, 556], [606, 563], [574, 562]], [[590, 530], [605, 495], [618, 460], [626, 420], [629, 380], [630, 340], RB],
      ROAD.highSt.slice(1), ROAD.station.slice(1), [[215, 348], [170, 335], [120, 322], [70, 310], [-20, 292]]), n: 6, silk: "godolphin", start: 30 },
  // from the stables, past the Jockey Club, up the Shied and across the top of Warren Hill
  { route: join([[722, 721], [659, 722], [636, 726], [616, 734], [598, 736], [583, 733], [531, 743], [496, 758], [468, 787], [448, 800]], ROAD.shied.slice(1),
      [[304, 597], [241, 574], [191, 532], [130, 490], [101, 457], [54, 413], [25, 398], [-20, 392]]), n: 7, silk: "judmonte", start: 62 },
];
const VANS = [join(ROAD.fordham, ROAD.oldStn), join(rev(ROAD.nmkt), rev(ROAD.kingston), ROAD.bury), join(ROAD.fordham, ROAD.kingston, ROAD.nmkt)];
const GALLOPS = [[-20, 190], [60, 178], [130, 165], [200, 150], [270, 135], [340, 118], [410, 104], [480, 92], [536, 84]];
const WARREN = [[262, 448], [205, 428], [152, 407], [110, 390], [60, 377], [10, 366], [-20, 360]];
const LONER = [[135, 786], [164, 783], [197, 760], [225, 743], [258, 726], [274, 734], [279, 769], [295, 803], [317, 850], [315, 877], [306, 889], [285, 903],
  [256, 910], [188, 917], [177, 927], [101, 957], [63, 983], [20, 1005], [-20, 1022]];
const PADDOCK = [
  { pts: [[1022, 129], [1075, 93], [1105, 82], [1129, 78], [1159, 79], [1190, 87], [1227, 106], [1254, 127]], coat: 2 },
  { pts: [[1315, 209], [1282, 246], [1266, 256], [1248, 259], [1234, 254], [1220, 242], [1205, 217], [1196, 193]], coat: 0 },
  { pts: [[1027, 423], [1140, 392], [1257, 361]], coat: 3 },
];
const YARD_TRIPS = [                                               // led out of one stable and into another
  [[962, 870], [925, 866], [890, 864], [850, 866], [815, 870], [785, 878], [756, 892]],
  [[790, 905], [805, 925], [830, 938], [860, 943], [900, 940], [940, 932], [985, 922], [1030, 905], [1068, 886]],
];
const PEOPLE_TRIPS = [
  [[830, 848], [870, 842], [905, 846]], [[1050, 892], [1020, 912], [995, 928]], [[1256, 833], [1280, 836], [1302, 840]],
  [[1392, 876], [1385, 898], [1378, 918]], [[760, 905], [778, 922], [800, 936]], [[1205, 845], [1222, 858], [1236, 866]],
];

// ---- horses, horseboxes and people
const movers = [];
let horseProto = null, peopleProto = null, silkList = [], maskTex = null, clipsByName = {}, horseScale = 1, personScale = 1;
const silkTex = new Map(), texLoader = new THREE.TextureLoader();
function silkTexture(id) { if (!silkTex.has(id)) { const t = texLoader.load(`assets/silks-3d/${id}.png`); t.flipY = false; t.colorSpace = THREE.SRGBColorSpace; silkTex.set(id, t); } return silkTex.get(id); }
const COATS = [["#6e4026", "#1d1714"], ["#4a2e1c", "#17110d"], ["#9a4f28", "#5f2e14"], ["#2b2523", "#141110"], ["#8f8d88", "#5d5b56"], ["#7a4a2a", "#1d1714"]];
let nHorse = 0;
function makeHorse({ silk: silkId, rider = true, coat: coatIx } = {}) {
  const k = nHorse++, obj = SkeletonUtils.clone(horseProto.scene); obj.scale.setScalar(horseScale);
  const coat = COATS[(coatIx ?? k) % COATS.length], silk = silkList.find((s) => s.id === silkId) || silkList[(k * 7 + 3) % silkList.length];
  const u = { mask: { value: maskTex }, coatCol: { value: new THREE.Color(coat[0]) }, pointsCol: { value: new THREE.Color(coat[1]) }, silkCol: { value: new THREE.Color(silk.colour) }, uRider: { value: rider ? 1 : 0 } };
  const mats = [], ground = { value: 0 }; obj.userData.ground = ground;
  obj.traverse((o) => {
    if (!o.isMesh) return; o.frustumCulled = false; o.material = o.material.clone(); o.material.transparent = true; mats.push(o.material);
    if (o.material.name === "silks") { o.material.map = silkTexture(silk.id); occluded(o.material, ground); if (!rider) o.visible = false; return; }
    o.material.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, u);
      sh.vertexShader = sh.vertexShader.replace("#include <common>", "#include <common>\nvarying vec3 vBind;").replace("#include <begin_vertex>", "#include <begin_vertex>\nvBind = position;");
      sh.fragmentShader = sh.fragmentShader.replace("#include <common>", "#include <common>\nuniform sampler2D mask; uniform vec3 coatCol; uniform vec3 pointsCol; uniform vec3 silkCol; uniform float uRider; varying vec3 vBind;")
        .replace("#include <clipping_planes_fragment>", "#include <clipping_planes_fragment>\n if (uRider < 0.5 && vBind.y > 0.445 && vBind.x > -0.08 && vBind.x < 0.27) discard;")
        .replace("#include <map_fragment>", `#include <map_fragment>
          { vec3 m = texture2D(mask, vMapUv).rgb; float l = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722)); diffuseColor.rgb = vec3(l);
            diffuseColor.rgb = mix(diffuseColor.rgb, coatCol * clamp(mix(1.0, l / 0.56, 0.65), 0.3, 1.25), m.r);
            diffuseColor.rgb = mix(diffuseColor.rgb, pointsCol * mix(0.75, 1.2, smoothstep(0.0, 0.035, l)), m.g);
            diffuseColor.rgb = mix(diffuseColor.rgb, silkCol * clamp(mix(1.0, l / 0.72, 0.6), 0.4, 1.15), m.b); }`);
    };
    o.material.customProgramCacheKey = () => "horse-tint";
    occluded(o.material, ground);
  });
  const mixer = new THREE.AnimationMixer(obj), act = {};
  for (const n of ["walk", "gallop", "ride_quiet", "ride_push"]) { act[n] = mixer.clipAction(clipsByName[n]); act[n].play(); act[n].setEffectiveWeight(0); }
  mixer.setTime(Math.random() * 2);
  scene.add(obj); addShadow(obj, 17, 7);
  return { obj, mixer, act, mats, gait: null, horse: true };
}
function setGait(h, gait, speed) {
  if (h.gait !== gait) {
    h.gait = gait;
    const w = { walk: [1, 0], stand: [1, 0], gallop: [0, 1] }[gait];
    h.act.walk.setEffectiveWeight(w[0]); h.act.ride_quiet.setEffectiveWeight(w[0]); h.act.gallop.setEffectiveWeight(w[1]); h.act.ride_push.setEffectiveWeight(w[1]);
  }
  const ts = gait === "stand" ? 0 : gait === "gallop" ? speed / 62 : speed / 14;
  for (const a of Object.values(h.act)) a.timeScale = gait === "stand" ? 0 : THREE.MathUtils.clamp(ts, 0.4, 1.8);
}
const CLOTHES = [0x2f3a4a, 0x5b3a2e, 0x3d4a3a, 0x6a5a48, 0x2b2b2b, 0x7a6a50, 0x4a3426, 0x405a6e];
let nPerson = 0;
function makePerson() {
  const k = nPerson++, f = peopleProto[k % 2].clone();          // stable lads: the two gents, no top hats
  const mats = [], ground = { value: 0 };
  f.traverse((o) => { if (!o.isMesh) return; const n = o.material.name;
    o.material = new THREE.MeshLambertMaterial({ color: n === "crowd_skin" ? 0xd9b090 : n === "crowd_hat" ? 0x3a3128 : CLOTHES[(k * 3) % CLOTHES.length], transparent: true });
    occluded(o.material, ground); mats.push(o.material); });
  f.position.set(0, 0, 0); f.scale.setScalar(personScale);
  const g = new THREE.Group(); g.userData.ground = ground; g.add(f); scene.add(g); addShadow(g, 7, 4);
  return { obj: g, mats, person: true };
}
const VAN_COLS = [0x3a4a3a, 0x36404e, 0x5a2a2c, 0x2e3a30, 0x463c30, 0x2a3442];
function makeVan(k) {
  const g = new THREE.Group(), col = VAN_COLS[k % VAN_COLS.length], ground = { value: 0 }; g.userData.ground = ground;
  const body = new THREE.MeshLambertMaterial({ color: col, transparent: true }), roof = new THREE.MeshLambertMaterial({ color: new THREE.Color(col).lerp(new THREE.Color(0x8a8270), 0.45), transparent: true });
  const dark = new THREE.MeshLambertMaterial({ color: 0x1b1a18, transparent: true }), glass = new THREE.MeshLambertMaterial({ color: 0x9fb2b8, transparent: true });
  const box = new THREE.Mesh(new THREE.BoxGeometry(16, 7.4, 8.6), body); box.position.set(-3.5, 5.6, 0);
  const lid = new THREE.Mesh(new THREE.BoxGeometry(16.4, 0.7, 9), roof); lid.position.set(-3.5, 9.6, 0);
  const cab = new THREE.Mesh(new THREE.BoxGeometry(6, 6.6, 8.2), body); cab.position.set(8.2, 5, 0);
  const win = new THREE.Mesh(new THREE.BoxGeometry(0.6, 2.6, 7.2), glass); win.position.set(11.25, 6.4, 0);
  g.add(box, lid, cab, win);
  for (const mt of [body, roof, dark, glass]) occluded(mt, ground);
  for (const [x, z] of [[-8, 4.4], [-8, -4.4], [8, 4.4], [8, -4.4], [-1, 4.4], [-1, -4.4]]) {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 1.4, 12).rotateX(Math.PI / 2), dark); w.position.set(x, 2.1, z); g.add(w);
  }
  g.scale.setScalar(0.95); scene.add(g); addShadow(g, 28, 12);
  return { obj: g, mats: [body, roof, dark, glass], keepLeft: 6, van: true };
}
const tmpN = new THREE.Vector3();
function place(m, p, dir, alpha, t = 0) {
  m.obj.position.copy(p);
  if (dir) {
    m.obj.rotation.y = Math.atan2(-dir.z, dir.x);                 // the models face +x
    if (m.keepLeft) { tmpN.set(dir.z, 0, -dir.x).normalize().multiplyScalar(m.keepLeft); m.obj.position.add(tmpN); }   // drive on the left
  }
  if (m.person && !REDUCED) m.obj.position.y = Math.abs(Math.sin(t * 7)) * 0.6;
  if (m.obj.userData.ground) m.obj.userData.ground.value = m.obj.position.z;
  if (dir) { m.dir = m.dir || new THREE.Vector3(); m.dir.copy(dir).setY(0).normalize(); }
  const s = m.obj.userData.shadow; s.position.set(m.obj.position.x + 2, 0.05, m.obj.position.z + 1.5); s.rotation.y = m.obj.rotation.y;
  m.obj.visible = s.visible = alpha > 0.01;
  for (const mt of m.mats) mt.opacity = alpha;
  s.material.opacity = alpha;
  if (m.lead) {                                                    // the lad at the horse's near side, a step ahead
    const d = dir ? dir.clone().normalize() : new THREE.Vector3(1, 0, 0);
    const q = p.clone().add(new THREE.Vector3(d.z, 0, -d.x).multiplyScalar(-6)).add(d.clone().multiplyScalar(4));
    place(m.lead, q, d, alpha, t);
  }
}
// a journey: legs along routes (or pauses); it repeats after a rest. Fades in and out where it starts and ends in the open.
function journey(m, legs, { start = 0, rest = 8, fadeIn = true, fadeOut = true, hours = null } = {}) {
  const ls = legs.map((l) => ({ ...l, dur: l.pause ?? l.curve.L / l.speed })), total = ls.reduce((a, l) => a + l.dur, 0);
  let last = null, lastDir = null, clock = -start;
  movers.push({ m, step(t, dt) {
    // between runs, wait for the right time of day (the strings go out in the morning; nobody works at night)
    const idle = clock < 0 || clock % (total + rest) > total;
    if (idle && hours && !inHours(hours)) { place(m, m.obj.position, null, 0, t); return; }
    if (!(m.van && blocked(m))) clock += dt;
    if (clock < 0) { place(m, m.obj.position, null, 0, t); return; }
    const tau = clock % (total + rest);
    if (tau > total) { place(m, m.obj.position, null, 0, t); return; }
    let acc = 0;
    for (const l of ls) {
      if (tau <= acc + l.dur) {
        const a = Math.min(fadeIn ? Math.min(1, tau / 1.2) : 1, fadeOut ? Math.min(1, (total - tau) / 1.2) : 1);
        if (l.pause != null) { if (m.act) setGait(m, "stand", 0); if (last) place(m, last, lastDir, a, t); return; }
        const u = (tau - acc) / l.dur, p = l.curve.getPointAt(u), d = l.curve.getTangentAt(u);
        if (m.act) setGait(m, l.gait, l.speed);
        last = p; lastDir = d; place(m, p, d, a, t); return;
      }
      acc += l.dur;
    }
  } });
}
// a horsebox waits while anyone on foot or hoof is just ahead of it in its lane
const tmpV = new THREE.Vector3();
function blocked(van) {
  if (!van.dir || !van.obj.visible) return false;
  for (const mv of movers) {
    const o = mv.m; if (o === van || o.van || !o.obj.visible) continue;
    tmpV.subVectors(o.obj.position, van.obj.position).setY(0);
    const along = tmpV.dot(van.dir), side = Math.abs(tmpV.x * van.dir.z - tmpV.z * van.dir.x);
    if (along > 2 && along < 40 && side < 10) return true;
  }
  return false;
}
function circuit(m, curve, speed, phase, gait = "walk", hours = null) {
  movers.push({ m, step(t) {
    if (hours && !inHours(hours)) { place(m, m.obj.position, null, 0, t); return; }
    const u = ((phase + t * speed / curve.L) % 1 + 1) % 1;
    if (m.act) setGait(m, gait, speed);
    place(m, curve.getPointAt(u), curve.getTangentAt(u), 1, t);
  } });
}
const oval = (cx, cz, rx, rz, turn = 0, n = 24) => { const c = Math.cos(turn), s = Math.sin(turn);
  return Array.from({ length: n }, (_, i) => { const a = i / n * 6.283, x = rx * Math.cos(a), z = rz * Math.sin(a); return [cx + x * c - z * s, cz + x * s + z * c]; }); };

async function loadModel(dir, name, images) {
  const text = (f) => fetch(`${dir}/${f}`).then((r) => { if (!r.ok) throw new Error(f + " " + r.status); return r.text(); });
  let json = await text(`${name}.json`);
  // the board's horses are 20 pixels long: they take small copies of the race view's 2048-pixel textures
  if (images) { const j = JSON.parse(json); (j.images || []).forEach((im) => { if (images[im.uri]) im.uri = images[im.uri]; }); json = JSON.stringify(j); }
  const b64 = (await text(`${name}-geometry.txt`)).trim();
  const raw = atob(b64), bin = new Uint8Array(raw.length); for (let i = 0; i < raw.length; i++) bin[i] = raw.charCodeAt(i);
  const pad = (n) => (n + 3) & ~3, jb = new TextEncoder().encode(json), jl = pad(jb.length), bl = pad(bin.length);
  const glb = new Uint8Array(28 + jl + bl), dv = new DataView(glb.buffer);
  dv.setUint32(0, 0x46546c67, true); dv.setUint32(4, 2, true); dv.setUint32(8, glb.length, true);
  dv.setUint32(12, jl, true); dv.setUint32(16, 0x4e4f534a, true); glb.fill(0x20, 20, 20 + jl); glb.set(jb, 20);
  dv.setUint32(20 + jl, bl, true); dv.setUint32(24 + jl, 0x004e4942, true); glb.set(bin, 28 + jl);
  return new Promise((res, rej) => new GLTFLoader().parse(glb.buffer, dir + "/", res, rej));
}

async function startLife() {
  // phones and tablets: a smaller picture and no antialiasing, so the board stays well inside a phone's memory
  // (a full-size, antialiased picture at a phone's pixel density runs to hundreds of megabytes)
  const phone = matchMedia("(pointer: coarse)").matches || Math.min(screen.width, screen.height) < 700;
  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: !phone, premultipliedAlpha: true, powerPreference: phone ? "low-power" : "default" });
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.setClearColor(0x000000, 0);
  canvas.addEventListener("webglcontextlost", (e) => { e.preventDefault(); lost = true; canvas.style.display = "none"; });
  B.onFit((scale) => { renderer.setPixelRatio(Math.min(scale * devicePixelRatio, phone ? 1.25 : 2)); renderer.setSize(MW, MH, false); renderer.getDrawingBufferSize(OCC.uRes.value); });
  const SMALL = { "racehorse-3d-model-clone1-basecolor.jpg": "../board-model/racehorse-basecolor-512.jpg", "racehorse-3d-model-clone1-normal.jpg": "../board-model/racehorse-normal-512.jpg", "racehorse-3d-model-clone1-rm.jpg": "../board-model/racehorse-rm-512.jpg" };
  const [g, ppl, cat] = await Promise.all([loadModel("assets/model", "racehorse", SMALL), loadModel("assets/architecture", "crowd_people"), fetch("assets/silks-catalogue.json").then((r) => r.json())]);
  horseProto = g; peopleProto = ppl.scene.children.slice(0, 2); silkList = cat.silks;
  for (const a of g.animations) clipsByName[a.name] = a;
  maskTex = texLoader.load("assets/tint-mask.png"); maskTex.flipY = false; maskTex.colorSpace = THREE.NoColorSpace;
  const occ = await new Promise((res, rej) => texLoader.load("assets/newmarket/occlusion.png", res, undefined, rej));
  occ.flipY = false; occ.colorSpace = THREE.NoColorSpace; occ.minFilter = occ.magFilter = THREE.NearestFilter; occ.generateMipmaps = false; occ.needsUpdate = true;
  OCC.occ.value = occ;
  const size = new THREE.Box3().setFromObject(g.scene).getSize(new THREE.Vector3());
  horseScale = 20 / Math.max(size.x, size.z);                      // a horse on the board is about 20 pixels nose to tail
  personScale = 12 / 1.8;                                          // and a person about 12 pixels tall

  // strings walking out to the heath, off the left edge, then round again
  for (const s of STRINGS) { const c = P(s.route); for (let i = 0; i < s.n; i++) { const h = makeHorse({ silk: s.silk }); h.keepLeft = 4; journey(h, [{ curve: c, speed: 15, gait: "walk" }], { start: s.start + i * 1.7, rest: 26, hours: [5.8, 11.5] }); } }
  // the Gallops and Warren Hill: lots working in a line
  const gal = P(GALLOPS), war = P(WARREN), lone = P(LONER);
  // morning is the busy time on the gallops: two more lots on each, and the afternoon lots are smaller
  for (let lot = 0; lot < 3; lot++) {
    const n = lot === 2 ? 3 : 5, hours = lot === 2 ? [6, 17] : [6, 11.5];
    for (let i = 0; i < n; i++) journey(makeHorse(), [{ curve: P(GALLOPS.map(([x, z]) => [x, z + (i % 2) * 8 + lot * 3])), speed: 70 - i, gait: "gallop" }], { start: 4 + lot * 9 + i * 1.1, rest: 24, hours });
  }
  for (let lot = 0; lot < 3; lot++) {
    const n = lot === 2 ? 3 : 4, hours = lot === 2 ? [6, 17] : [6, 11.5];
    for (let i = 0; i < n; i++) journey(makeHorse(), [{ curve: P(WARREN.map(([x, z]) => [x, z + (i % 2) * 7 + lot * 3])), speed: 54, gait: "gallop" }], { start: 14 + lot * 8 + i * 1.0, rest: 22, hours });
  }
  journey(makeHorse(), [{ curve: lone, speed: 46, gait: "gallop" }], { start: 9, rest: 16, hours: [6, 19] });
  // horseboxes in from the top and the bottom of the board, out along Bury Road and Old Station Road
  VANS.forEach((r, i) => journey(makeVan(i), [{ curve: P(r), speed: 26 + (i % 3) * 4 }], { start: i * 16 + 4, rest: 14 + i * 5, hours: [6.5, 21] }));
  // the paddocks: loose horses wandering along, a rest, and back
  for (const pd of PADDOCK) { const c = P(pd.pts), b = P(rev(pd.pts));
    journey(makeHorse({ rider: false, coat: pd.coat }), [{ curve: c, speed: 6, gait: "walk" }, { pause: 7 }, { curve: b, speed: 6, gait: "walk" }, { pause: 9 }], { start: Math.random() * 20, rest: 0, fadeIn: false, fadeOut: false }); }
  journey(makeHorse({ rider: false, coat: 4 }), [{ curve: P([[1333, 431], [1390, 452], [1466, 482]]), speed: 7, gait: "walk" }], { start: 5, rest: 12 });
  // the yards: horses led from one stable to another, a horse ridden round the lunge ring, people about
  YARD_TRIPS.forEach((tr, i) => { const h = makeHorse({ rider: false }); h.lead = makePerson();
    journey(h, [{ curve: P(tr), speed: 9, gait: "walk" }], { start: 3 + i * 14, rest: 10 + i * 4, hours: [6, 20] }); });
  circuit(makeHorse(), P([[1281, 847], [1241, 870], [1242, 883], [1260, 908], [1346, 896], [1370, 887], [1345, 852], [1305, 843]], true), 13, 0, "walk", [7, 19]);
  const parade = P(oval(1168, 752, 53, 26, 0.26), true);
  for (let i = 0; i < 3; i++) { const h = makeHorse({ rider: false }); h.lead = makePerson(); circuit(h, parade, 9, i / 3, "walk", [8, 18]); }
  PEOPLE_TRIPS.forEach((tr, i) => journey(makePerson(), [{ curve: P(tr), speed: 7, gait: "walk" }, { pause: 3 }, { curve: P(rev(tr)), speed: 7, gait: "walk" }], { start: i * 2.3, rest: 4 + i, fadeIn: false, fadeOut: false, hours: [5.5, 21] }));

  window.__lifeReady = true;
  // a check hook: stand a horse at a board point (it shows whether buildings in front of it hide it)
  window.__probe = (x, y) => { const h = makeHorse(); setGait(h, "walk", 5); place(h, new THREE.Vector3(x, 0, y), new THREE.Vector3(1, 0, 0), 1, 0); h.mixer.update(0.1); };
}

if (location.hash === "#routes") {
  const glow = document.getElementById("glow"), svgNS = "http://www.w3.org/2000/svg";                                  // a check view: every route drawn over the board
  const line = (pts, col, closed) => { const e = document.createElementNS(svgNS, closed ? "polygon" : "polyline"); e.setAttribute("points", pts.map((q) => q.join(",")).join(" "));
    e.setAttribute("fill", "none"); e.setAttribute("stroke", col); e.setAttribute("stroke-width", "2.5"); e.style.pointerEvents = "none"; glow.appendChild(e); };
  Object.values(ROAD).forEach((r) => line(r, "#1060ff"));
  STRINGS.forEach((s) => line(s.route, "#e0102a")); [GALLOPS, WARREN, LONER].forEach((r) => line(r, "#00a040"));
  [...PADDOCK.map((p) => p.pts), ...YARD_TRIPS, ...PEOPLE_TRIPS].forEach((r) => line(r, "#ff30d0"));
  line(oval(1168, 752, 53, 26, 0.26), "#ff8000", true);
  for (const k of ["jockey>stud", "stud>tatts", "tatts>stables", "stables>warren", "warren>jockey", "jockey>races", "races>palace"]) line(B.routeFor(...k.split(">")), "#ffd24a");
  setTimeout(() => document.querySelectorAll("#glow .site").forEach((z) => z.classList.add("hot")), 50);
}
// ---------------------------------------------------------------- the game's processions: one journey each, then gone
const PROC = {
  // the yearlings out of the mares nobody bred, led from the National Stud along Old Station Road into Tattersalls
  yearlings: { route: () => B.routeFor("stud", "tatts"), n: 4, gap: 2.4, speed: 16, make: (i) => { const h = makeHorse({ rider: false, coat: i + 1 }); h.lead = makePerson(); return h; } },
  // your string, out of the yard in your colours: past the Jockey Club and up the Shied onto Warren Hill (the owner's route)
  gallops: { route: () => STRINGS[2].route, n: 5, gap: 1.8, speed: 16, make: (i, o) => makeHorse({ silk: o.silk }) },
  // the horseboxes away to the races: Kingston Road, then off the top of the board up Fordham Road
  boxes: { route: () => join([[722, 721], [659, 722], [636, 726], [616, 734], [598, 736], [583, 733], [531, 743], [496, 758], [468, 787], [448, 800]], rev(ROAD.kingston), rev(ROAD.fordham)), n: 3, gap: 2.6, speed: 70, make: (i) => makeVan(i) },
};
const shots = [];
function procession(kind, opts = {}) {
  const P0 = PROC[kind]; if (!P0 || !horseProto) return 0;
  const curve = P(P0.route()), dur = curve.L / P0.speed;
  for (let i = 0; i < P0.n; i++) {
    const m = P0.make(i, opts); if (m.act) setGait(m, "walk", P0.speed); if (m.van) m.keepLeft = 6; else m.keepLeft = 3;
    shots.push({ m, curve, speed: P0.speed, t: -i * P0.gap, dur, gait: P0.speed > 26 && m.act ? "gallop" : "walk" });
  }
  return (dur + P0.n * P0.gap) * 1000;
}
function stepShots(t, dt) {
  for (let k = shots.length - 1; k >= 0; k--) {
    const s = shots[k]; s.t += dt;
    if (s.t < 0) { place(s.m, s.m.obj.position, null, 0, t); continue; }
    if (s.t > s.dur) { place(s.m, s.m.obj.position, null, 0, t); s.m.obj.visible = false; shots.splice(k, 1); continue; }
    const u = s.t / s.dur, a = Math.min(1, s.t / 1.0, (s.dur - s.t) / 1.0);
    if (s.m.act) setGait(s.m, s.gait, s.speed);
    place(s.m, s.curve.getPointAt(u), s.curve.getTangentAt(u), a, t);
    if (s.m.mixer) s.m.mixer.update(dt);
  }
}
window.LIFE = { procession, __advance: (secs) => { stepShots(0, secs); return shots.map((s) => [Math.round(s.m.obj.position.x), Math.round(s.m.obj.position.z), s.m.obj.visible]); } };   // __advance: a checking aid
B.addFrame((t, dt) => {
  if (!renderer || lost) return;
  // nothing to draw while the board is out of sight: at Ascot, or under a sheet on a phone (where the sheet fills the screen)
  if (document.body.classList.contains("at-ascot") || (B.covered && innerWidth <= 760)) return;
  for (const mv of movers) { mv.step(t, dt); if (mv.m.mixer && mv.m.obj.visible) mv.m.mixer.update(dt); }
  stepShots(t, dt);
  renderer.render(scene, cam);
});
// ?nolife=1 leaves the board without its 3D life (for checking the game quickly on a machine without a graphics chip)
if (!new URLSearchParams(location.search).has("nolife")) startLife().catch((e) => { console.warn("Newmarket life didn't start", e); });
