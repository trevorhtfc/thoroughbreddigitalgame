<script type="module">
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";

const REDUCED = matchMedia("(prefers-reduced-motion: reduce)").matches;
const MW = 1448, MH = 1086;                                        // the board, in its own pixels; everything below is in these

// ---------------------------------------------------------------- the places
// Each lit outline is the owner's own line (markup/sites-markup.jpg, traced by markup/extract.py).
const SITES = %%SITES%%;
const ICONS = { gavel: `%%ICON:gavel%%`, temple: `%%ICON:greek-temple%%`, stable: `%%ICON:stable%%`, head: `%%ICON:horse-head%%` };
const PLACES = [
  { id: "warren", name: "Warren Hill<br>Gallops", at: [165, 487], icon: "horse", title: "Warren Hill", cta: "Go to the Gallops",
    text: "Work your string up the famous hill gallops.", pic: [170, 410, 360] },
  { id: "palace", name: "Palace House", at: [436, 676], icon: "temple", title: "Palace House", cta: "Visit Palace House",
    text: "The National Horseracing Museum: your trophies and racing history.", pic: [440, 615, 240] },
  { id: "jockey", name: "The Jockey Club", at: [660, 682], icon: "jc", title: "The Jockey Club", cta: "Enter the Rooms",
    text: "Race entries, the fixture list and the rules of racing.", pic: [662, 640, 230] },
  { id: "tatts", name: "Tattersalls", at: [946, 750], icon: "gavel", title: "Tattersalls", cta: "Enter Auction",
    text: "Historic bloodstock auctions and sales.", pic: [915, 690, 420] },
  { id: "stables", name: "Stables", at: [963, 909], icon: "stable", title: "Your Stables", cta: "Visit Stables",
    text: "Your string: training, wellbeing and race entries.", pic: [930, 880, 500] },
  { id: "stud", name: "National Stud", at: [1344, 493], icon: "head", title: "National Stud", cta: "Visit the Stud",
    text: "Stallions, mares and foals: plan your matings.", pic: [1170, 500, 440] },
];
const stage = document.getElementById("stage"), glow = document.getElementById("glow"), card = document.getElementById("card");
const svgNS = "http://www.w3.org/2000/svg";
const smoothPath = (pts) => {                                      // a closed curve through the outline's points
  const n = pts.length, p = (i) => pts[(i + n) % n];
  let d = `M${p(0)[0]},${p(0)[1]}`;
  for (let i = 0; i < n; i++) {
    const a = p(i - 1), b = p(i), c = p(i + 1), e = p(i + 2);
    d += `C${(b[0] + (c[0] - a[0]) / 6).toFixed(1)},${(b[1] + (c[1] - a[1]) / 6).toFixed(1)} ${(c[0] - (e[0] - b[0]) / 6).toFixed(1)},${(c[1] - (e[1] - b[1]) / 6).toFixed(1)} ${c[0]},${c[1]}`;
  }
  return d + "Z";
};
for (const p of PLACES) {
  const site = SITES.find((s) => s.id === p.id);
  if (site) {
    const d = smoothPath(site.poly);
    const g = document.createElementNS(svgNS, "g"); g.setAttribute("class", "site"); g.id = "site-" + p.id;
    g.innerHTML = `<path class="wash" d="${d}"/><path class="halo" d="${d}"/><path class="rim" d="${d}"/><path class="line" d="${d}"/><path class="spark" d="${d}" pathLength="548"/><path class="hit" d="${d}"/>`;
    g.addEventListener("pointerenter", () => hover(p.id, true)); g.addEventListener("pointerleave", () => hover(p.id, false));
    g.addEventListener("click", () => choose(p.id));
    glow.appendChild(g);
  }
  const b = document.createElement("button");
  b.className = "loc"; b.type = "button"; b.dataset.id = p.id; b.style.left = p.at[0] + "px"; b.style.top = (p.at[1] - 16) + "px";
  const icon = p.icon === "jc" ? `<span class="jc">JC</span>` : p.icon === "horse" ? `<span class="hz"></span>` : `<svg viewBox="0 0 512 512">${ICONS[p.icon]}</svg>`;
  b.innerHTML = `<span class="medal">${icon}</span><span class="pill">${p.name}</span><span class="ring"></span>`;
  b.setAttribute("aria-label", p.title);
  b.addEventListener("mouseenter", () => hover(p.id, true)); b.addEventListener("mouseleave", () => hover(p.id, false));
  b.addEventListener("focus", () => hover(p.id, true)); b.addEventListener("blur", () => hover(p.id, false));
  b.addEventListener("click", () => choose(p.id));
  stage.appendChild(b);
}
let chosen = null;
const siteEl = (id) => document.getElementById("site-" + id);
function hover(id, on) {
  if (id === chosen) return;
  siteEl(id)?.classList.toggle("hot", on);
  stage.querySelector(`.loc[data-id="${id}"]`).classList.toggle("lit", on);
}
function choose(id) {
  chosen = id;
  for (const p of PLACES) {
    siteEl(p.id)?.classList.toggle("hot", p.id === id);
    stage.querySelector(`.loc[data-id="${p.id}"]`).classList.toggle("on", p.id === id);
  }
  if (!id) { card.hidden = true; return; }
  const p = PLACES.find((q) => q.id === id);
  document.getElementById("cardTitle").textContent = p.title;
  document.getElementById("cardText").textContent = p.text;
  document.getElementById("cardCta").textContent = p.cta;
  document.getElementById("cardSoon").hidden = true;
  const pic = document.getElementById("cardPic"), w = pic.clientWidth || 296, h = pic.clientHeight || 170, k = w / p.pic[2];
  pic.style.backgroundSize = `${MW * k}px ${MH * k}px`;
  pic.style.backgroundPosition = `${-(p.pic[0] * k - w / 2)}px ${-(p.pic[1] * k - h / 2)}px`;
  pic.setAttribute("aria-label", p.title + " on the board");
  card.hidden = false;
}
document.getElementById("cardClose").addEventListener("click", () => choose(null));
document.getElementById("cardGo").addEventListener("click", () => { document.getElementById("cardSoon").hidden = false; });
addEventListener("keydown", (e) => { if (e.key === "Escape") choose(null); });

// ---------------------------------------------------------------- fit the board to the window
const view = document.getElementById("view"), holder = document.getElementById("holder");
let scale = 1, renderer = null;
function fit() {
  const W = view.clientWidth, H = view.clientHeight;
  const portrait = W / H < 1.05;
  scale = portrait ? H / MH : Math.min(W / MW, H / MH);
  view.classList.toggle("pan", portrait);
  holder.style.width = MW * scale + "px"; holder.style.height = MH * scale + "px";
  stage.style.transform = `scale(${scale})`;
  if (portrait) view.scrollLeft = 900 * scale - W / 2;           // start on Tattersalls and the stables
  if (renderer) { renderer.setPixelRatio(Math.min(scale * devicePixelRatio, 2.5)); renderer.setSize(MW, MH, false); }
  if (chosen) choose(chosen);
}
addEventListener("resize", fit);

// ---------------------------------------------------------------- the sky: cloud shadows over the board, wisps drifting along the top
const clouds = document.getElementById("clouds"), cx2 = clouds.getContext("2d");
const wisps = document.getElementById("wisps"), wx2 = wisps.getContext("2d");
const Q = 4;                                                       // both are drawn at a quarter size and stretched
const PUFFS = Array.from({ length: 5 }, (_, i) => ({ x: (i * 0.27 % 1) * 1800 - 180, y: 150 + (i * 0.61 % 1) * 850, r: 190 + (i * 0.37 % 1) * 200 }));
// hand-drawn clouds drifting along the top (the owner's white lines): drawn once each as a little illustration
// (a cream body, a shaded underside, an ink outline and a few curls), then slid across
function cloudSprite(seed, w, h) {
  const rnd = (k) => { const x = Math.sin(seed * 91.7 + k * 12.9) * 43758.5; return x - Math.floor(x); };
  const pad = 14, c = document.createElement("canvas"); c.width = w + pad * 2; c.height = h + pad * 2; const g = c.getContext("2d");
  const n = 6 + Math.floor(rnd(1) * 3), lobes = [];
  for (let i = 0; i < n; i++) {
    const u = i / (n - 1), top = Math.sin(u * Math.PI);
    lobes.push([pad + w * (0.1 + u * 0.8), pad + h * (0.78 - top * (0.38 + rnd(i + 3) * 0.18)), h * (0.24 + top * 0.2 + rnd(i + 9) * 0.08)]);
  }
  lobes.push([pad + w * 0.5, pad + h * 0.75, h * 0.28], [pad + w * 0.28, pad + h * 0.8, h * 0.22], [pad + w * 0.72, pad + h * 0.8, h * 0.22]);
  const blob = (grow) => { g.beginPath(); for (const [x, y, r] of lobes) { g.moveTo(x + r + grow, y); g.arc(x, y, r + grow, 0, 6.283); } };
  g.fillStyle = "rgba(120,96,64,.55)"; blob(1.6); g.fill();                                   // the ink outline, as a rim behind
  const body = g.createLinearGradient(0, pad, 0, pad + h); body.addColorStop(0, "#fffdf4"); body.addColorStop(.55, "#f6efdc"); body.addColorStop(1, "#d9cdb2");
  g.fillStyle = body; blob(0); g.fill();
  g.globalCompositeOperation = "source-atop";                                                // a flat, shaded underside
  g.fillStyle = "rgba(170,150,115,.35)"; g.fillRect(0, pad + h * 0.8, c.width, h);
  g.globalCompositeOperation = "source-over";
  g.strokeStyle = "rgba(130,105,70,.45)"; g.lineWidth = 1.2; g.lineCap = "round";            // a few curls, as an engraver would
  for (let i = 1; i < n - 1; i += 2) { const [x, y, r] = lobes[i]; g.beginPath(); g.arc(x, y + r * 0.15, r * 0.62, Math.PI * 1.05, Math.PI * 1.55); g.stroke(); }
  return c;
}
const BANKS = [
  { x: 120, y: -26, sprite: cloudSprite(1, 230, 92), speed: 7 }, { x: 560, y: -14, sprite: cloudSprite(2, 150, 64), speed: 9 },
  { x: 860, y: -30, sprite: cloudSprite(3, 270, 104), speed: 6 }, { x: 1300, y: 2, sprite: cloudSprite(4, 140, 58), speed: 8.5 },
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
    const w = b.sprite.width, h = b.sprite.height;
    if (!REDUCED) b.x += b.speed * dt;
    if (b.x > MW + 20) b.x = -w - 20;
    wx2.globalAlpha = 0.9; wx2.drawImage(b.sprite, b.x, b.y); wx2.globalAlpha = 1;
    // its shadow on the ground, below and to the right
    const sx = (b.x + w * 0.5 + 70) / Q, sy = (b.y + h * 0.6 + 150) / Q, r = w * 0.42 / Q, sg = cx2.createRadialGradient(sx, sy, 0, sx, sy, r);
    sg.addColorStop(0, "rgba(60,70,50,.13)"); sg.addColorStop(1, "rgba(60,70,50,0)");
    cx2.fillStyle = sg; cx2.beginPath(); cx2.ellipse(sx, sy, r, r * 0.45, 0, 0, 6.283); cx2.fill();
  }
}

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

const shadowTex = (() => { const c = document.createElement("canvas"); c.width = c.height = 64; const g = c.getContext("2d");
  const r = g.createRadialGradient(32, 32, 0, 32, 32, 32); r.addColorStop(0, "rgba(30,26,12,.55)"); r.addColorStop(1, "rgba(30,26,12,0)");
  g.fillStyle = r; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
const shadowGeo = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
function addShadow(obj, len, wid) { const s = new THREE.Mesh(shadowGeo, new THREE.MeshBasicMaterial({ map: shadowTex, transparent: true, depthWrite: false })); s.scale.set(len, 1, wid); s.renderOrder = -1; scene.add(s); obj.userData.shadow = s; return s; }

// ---- routes: the owner's red (strings), blue (horseboxes) and pink (yards and paddocks) lines, kept to the roads
const P = (pts, closed = false) => { const c = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, 0, z)), closed, "centripetal"); c.L = c.getLength(); return c; };
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
};
const rev = (a) => a.slice().reverse();
const join = (...parts) => parts.reduce((acc, p) => acc.concat(acc.length ? p.slice(1) : p), []);
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
const VANS = [
  join(ROAD.fordham, ROAD.oldStn), join(rev(ROAD.nmkt), rev(ROAD.kingston), ROAD.bury), join(ROAD.fordham, ROAD.kingston, ROAD.nmkt),
  join(rev(ROAD.nmkt), rev(ROAD.kingston), ROAD.oldStn), join(ROAD.fordham, ROAD.bury),
];
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
  [[957, 852], [922, 839], [895, 833], [846, 832], [820, 837], [792, 847], [747, 874]],
  [[796, 900], [807, 924], [829, 943], [852, 951], [888, 951], [926, 943], [973, 926], [1023, 902], [1073, 873]],
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
  const mats = [];
  obj.traverse((o) => {
    if (!o.isMesh) return; o.frustumCulled = false; o.material = o.material.clone(); o.material.transparent = true; mats.push(o.material);
    if (o.material.name === "silks") { o.material.map = silkTexture(silk.id); if (!rider) o.visible = false; return; }
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
  });
  const mixer = new THREE.AnimationMixer(obj), act = {};
  for (const n of ["walk", "gallop", "ride_quiet", "ride_push"]) { act[n] = mixer.clipAction(clipsByName[n]); act[n].play(); act[n].setEffectiveWeight(0); }
  mixer.setTime(Math.random() * 2);
  scene.add(obj); addShadow(obj, 17, 7);
  return { obj, mixer, act, mats, gait: null };
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
  const mats = [];
  f.traverse((o) => { if (!o.isMesh) return; const n = o.material.name;
    o.material = new THREE.MeshLambertMaterial({ color: n === "crowd_skin" ? 0xd9b090 : n === "crowd_hat" ? 0x3a3128 : CLOTHES[(k * 3) % CLOTHES.length], transparent: true }); mats.push(o.material); });
  f.position.set(0, 0, 0); f.scale.setScalar(personScale);
  const g = new THREE.Group(); g.add(f); scene.add(g); addShadow(g, 7, 4);
  return { obj: g, mats, person: true };
}
const VAN_COLS = [0x3a4a3a, 0x36404e, 0x5a2a2c, 0x2e3a30, 0x463c30, 0x2a3442];
function makeVan(k) {
  const g = new THREE.Group(), col = VAN_COLS[k % VAN_COLS.length];
  const body = new THREE.MeshLambertMaterial({ color: col, transparent: true }), roof = new THREE.MeshLambertMaterial({ color: new THREE.Color(col).lerp(new THREE.Color(0x8a8270), 0.45), transparent: true });
  const dark = new THREE.MeshLambertMaterial({ color: 0x1b1a18, transparent: true }), glass = new THREE.MeshLambertMaterial({ color: 0x9fb2b8, transparent: true });
  const box = new THREE.Mesh(new THREE.BoxGeometry(16, 7.4, 8.6), body); box.position.set(-3.5, 5.6, 0);
  const lid = new THREE.Mesh(new THREE.BoxGeometry(16.4, 0.7, 9), roof); lid.position.set(-3.5, 9.6, 0);
  const cab = new THREE.Mesh(new THREE.BoxGeometry(6, 6.6, 8.2), body); cab.position.set(8.2, 5, 0);
  const win = new THREE.Mesh(new THREE.BoxGeometry(0.6, 2.6, 7.2), glass); win.position.set(11.25, 6.4, 0);
  g.add(box, lid, cab, win);
  for (const [x, z] of [[-8, 4.4], [-8, -4.4], [8, 4.4], [8, -4.4], [-1, 4.4], [-1, -4.4]]) {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(2.1, 2.1, 1.4, 12).rotateX(Math.PI / 2), dark); w.position.set(x, 2.1, z); g.add(w);
  }
  g.scale.setScalar(0.95); scene.add(g); addShadow(g, 28, 12);
  return { obj: g, mats: [body, roof, dark, glass], keepLeft: 5 };
}
const tmpN = new THREE.Vector3();
function place(m, p, dir, alpha, t = 0) {
  m.obj.position.copy(p);
  if (dir) {
    m.obj.rotation.y = Math.atan2(-dir.z, dir.x);                 // the models face +x
    if (m.keepLeft) { tmpN.set(dir.z, 0, -dir.x).normalize().multiplyScalar(m.keepLeft); m.obj.position.add(tmpN); }   // drive on the left
  }
  if (m.person && !REDUCED) m.obj.position.y = Math.abs(Math.sin(t * 7)) * 0.6;
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
function journey(m, legs, { start = 0, rest = 8, fadeIn = true, fadeOut = true } = {}) {
  const ls = legs.map((l) => ({ ...l, dur: l.pause ?? l.curve.L / l.speed })), total = ls.reduce((a, l) => a + l.dur, 0);
  let last = null, lastDir = null;
  movers.push({ m, step(t) {
    let tau = (t - start) % (total + rest); if (tau < 0) tau += total + rest;
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
function circuit(m, curve, speed, phase, gait = "walk") {
  movers.push({ m, step(t) {
    const u = ((phase + t * speed / curve.L) % 1 + 1) % 1;
    if (m.act) setGait(m, gait, speed);
    place(m, curve.getPointAt(u), curve.getTangentAt(u), 1, t);
  } });
}
const oval = (cx, cz, rx, rz, turn = 0, n = 24) => { const c = Math.cos(turn), s = Math.sin(turn);
  return Array.from({ length: n }, (_, i) => { const a = i / n * 6.283, x = rx * Math.cos(a), z = rz * Math.sin(a); return [cx + x * c - z * s, cz + x * s + z * c]; }); };

async function loadModel(dir, name) {
  const text = (f) => fetch(`${dir}/${f}`).then((r) => { if (!r.ok) throw new Error(f + " " + r.status); return r.text(); });
  const json = await text(`${name}.json`), b64 = (await text(`${name}-geometry.txt`)).trim();
  const raw = atob(b64), bin = new Uint8Array(raw.length); for (let i = 0; i < raw.length; i++) bin[i] = raw.charCodeAt(i);
  const pad = (n) => (n + 3) & ~3, jb = new TextEncoder().encode(json), jl = pad(jb.length), bl = pad(bin.length);
  const glb = new Uint8Array(28 + jl + bl), dv = new DataView(glb.buffer);
  dv.setUint32(0, 0x46546c67, true); dv.setUint32(4, 2, true); dv.setUint32(8, glb.length, true);
  dv.setUint32(12, jl, true); dv.setUint32(16, 0x4e4f534a, true); glb.fill(0x20, 20, 20 + jl); glb.set(jb, 20);
  dv.setUint32(20 + jl, bl, true); dv.setUint32(24 + jl, 0x004e4942, true); glb.set(bin, 28 + jl);
  return new Promise((res, rej) => new GLTFLoader().parse(glb.buffer, dir + "/", res, rej));
}

async function startLife() {
  renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, premultipliedAlpha: true });
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.setClearColor(0x000000, 0);
  fit();
  const [g, ppl, cat] = await Promise.all([loadModel("assets/model", "racehorse"), loadModel("assets/people", "crowd_people"), fetch("assets/silks-catalogue.json").then((r) => r.json())]);
  horseProto = g; peopleProto = ppl.scene.children.slice(0, 2); silkList = cat.silks;
  for (const a of g.animations) clipsByName[a.name] = a;
  maskTex = texLoader.load("assets/tint-mask.png"); maskTex.flipY = false; maskTex.colorSpace = THREE.NoColorSpace;
  const size = new THREE.Box3().setFromObject(g.scene).getSize(new THREE.Vector3());
  horseScale = 20 / Math.max(size.x, size.z);                      // a horse on the board is about 20 pixels nose to tail
  personScale = 12 / 1.8;                                          // and a person about 12 pixels tall

  // strings walking out to the heath, off the left edge, then round again
  for (const s of STRINGS) { const c = P(s.route); for (let i = 0; i < s.n; i++) journey(makeHorse({ silk: s.silk }), [{ curve: c, speed: 15, gait: "walk" }], { start: s.start + i * 1.7, rest: 26 }); }
  // the Gallops and Warren Hill: lots working in a line
  const gal = P(GALLOPS), war = P(WARREN), lone = P(LONER);
  for (let i = 0; i < 5; i++) journey(makeHorse(), [{ curve: P(GALLOPS.map(([x, z]) => [x, z + (i % 2) * 8])), speed: 70 - i, gait: "gallop" }], { start: 4 + i * 1.1, rest: 24 });
  for (let i = 0; i < 4; i++) journey(makeHorse(), [{ curve: P(WARREN.map(([x, z]) => [x, z + (i % 2) * 7])), speed: 54, gait: "gallop" }], { start: 14 + i * 1.0, rest: 22 });
  journey(makeHorse(), [{ curve: lone, speed: 46, gait: "gallop" }], { start: 9, rest: 16 });
  // horseboxes in from the top and the bottom of the board, out along Bury Road and Old Station Road
  VANS.forEach((r, i) => journey(makeVan(i), [{ curve: P(r), speed: 26 + (i % 3) * 4 }], { start: i * 11 - 30, rest: 6 + i * 3 }));
  // the paddocks: loose horses wandering along, a rest, and back
  for (const pd of PADDOCK) { const c = P(pd.pts), b = P(rev(pd.pts));
    journey(makeHorse({ rider: false, coat: pd.coat }), [{ curve: c, speed: 6, gait: "walk" }, { pause: 7 }, { curve: b, speed: 6, gait: "walk" }, { pause: 9 }], { start: Math.random() * 20, rest: 0, fadeIn: false, fadeOut: false }); }
  journey(makeHorse({ rider: false, coat: 4 }), [{ curve: P([[1333, 431], [1390, 452], [1466, 482]]), speed: 7, gait: "walk" }], { start: 5, rest: 12 });
  // the yards: horses led from one stable to another, a horse ridden round the lunge ring, people about
  YARD_TRIPS.forEach((tr, i) => { const h = makeHorse({ rider: false }); h.lead = makePerson();
    journey(h, [{ curve: P(tr), speed: 9, gait: "walk" }], { start: 3 + i * 14, rest: 10 + i * 4 }); });
  circuit(makeHorse(), P([[1281, 847], [1241, 870], [1242, 883], [1260, 908], [1346, 896], [1370, 887], [1345, 852], [1305, 843]], true), 13, 0);
  const parade = P(oval(1168, 752, 53, 26, 0.26), true);
  for (let i = 0; i < 3; i++) { const h = makeHorse({ rider: false }); h.lead = makePerson(); circuit(h, parade, 9, i / 3); }
  PEOPLE_TRIPS.forEach((tr, i) => journey(makePerson(), [{ curve: P(tr), speed: 7, gait: "walk" }, { pause: 3 }, { curve: P(rev(tr)), speed: 7, gait: "walk" }], { start: i * 2.3, rest: 4 + i, fadeIn: false, fadeOut: false }));

  window.__ready = true;
}

if (location.hash === "#routes") {                                  // a check view: every route drawn over the board
  const line = (pts, col, closed) => { const e = document.createElementNS(svgNS, closed ? "polygon" : "polyline"); e.setAttribute("points", pts.map((q) => q.join(",")).join(" "));
    e.setAttribute("fill", "none"); e.setAttribute("stroke", col); e.setAttribute("stroke-width", "2.5"); e.style.pointerEvents = "none"; glow.appendChild(e); };
  Object.values(ROAD).forEach((r) => line(r, "#1060ff"));
  STRINGS.forEach((s) => line(s.route, "#e0102a")); [GALLOPS, WARREN, LONER].forEach((r) => line(r, "#00a040"));
  [...PADDOCK.map((p) => p.pts), ...YARD_TRIPS, ...PEOPLE_TRIPS].forEach((r) => line(r, "#ff30d0"));
  line(oval(1168, 752, 53, 26, 0.26), "#ff8000", true);
  setTimeout(() => document.querySelectorAll("#glow .site").forEach((z) => z.classList.add("hot")), 50);
}

const clock = new THREE.Clock();
let skyT = 0;
function frame() {
  const dt = Math.min(clock.getDelta(), 0.1), t = clock.elapsedTime;
  skyT += dt; if (skyT > 1 / 15) { drawSky(skyT); skyT = 0; }
  if (renderer) {
    for (const mv of movers) { mv.step(t); if (mv.m.mixer && mv.m.obj.visible) mv.m.mixer.update(dt); }
    renderer.render(scene, cam);
  }
  requestAnimationFrame(frame);
}
fit(); drawSky(0); frame();
window.__state = () => ({ movers: movers.length, scale, scroll: view.scrollLeft, w: view.clientWidth });
window.__choose = choose;
window.__hover = hover;
startLife().catch((e) => { console.warn("Newmarket life didn't start", e); });
</script>
