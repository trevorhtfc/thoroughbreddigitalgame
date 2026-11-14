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
// The roundabout has a monument on its island, so nothing goes straight over the middle: every route that reaches it
// is taken round the island instead, clockwise as traffic goes, from the road it came in by to the road it leaves by.
const RING = { x: 632, z: 292, rx: 19, rz: 13 };
function roundabout(pts) {
  const rad = (q) => Math.hypot((q[0] - RING.x) / RING.rx, (q[1] - RING.z) / RING.rz);
  const i = pts.findIndex((q) => rad(q) < 2.1); if (i <= 0) return pts;
  let j = i; while (j + 1 < pts.length && rad(pts[j + 1]) < 2.1) j++;
  if (j >= pts.length - 1) return pts;
  const ang = (q) => Math.atan2((q[1] - RING.z) / RING.rz, (q[0] - RING.x) / RING.rx);
  let a = ang(pts[i - 1]), b = ang(pts[j + 1]); while (b <= a + 0.5) b += 6.2832;
  const trim = Math.min(0.7, (b - a) * 0.3); a += trim; b -= trim;   // it joins the ring a little way round, and peels off before its road
  const n = Math.max(1, Math.ceil((b - a) / 0.4)), arc = [];
  for (let k = 0; k <= n; k++) { const t = a + (b - a) * k / n; arc.push([RING.x + RING.rx * Math.cos(t), RING.z + RING.rz * Math.sin(t)]); }
  return [...pts.slice(0, i), ...arc, ...pts.slice(j + 1)];
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
  // from the National Stud, down Bury Road, round by Exeter Road and out along the Avenue beside the Gallops (it used to
  // cut across the Gallops themselves, through the lots at work there: AVENUE_W is filled in below, from the van routes)
  { route: join([[905, 262], [874, 247], [847, 228], [818, 208], [790, 194]], [[780, 198], [740, 222], [700, 250], [660, 280], RB], [[630, 262], [629, 236]], ROAD.exeter.slice(1),
      [[250, 298], [215, 305]]), n: 6, silk: "ballydoyle-navy", start: 0, avenue: true },
  // from Tattersalls, up Kingston Road, down the High Street, out along Station Road onto Warren Hill
  { route: join([[752, 517], [729, 520], [702, 535], [671, 548], [640, 556], [606, 563], [574, 562]], [[590, 530], [605, 495], [618, 460], [626, 420], [629, 380], [630, 340], RB],
      ROAD.highSt.slice(1), ROAD.station.slice(1), [[215, 348], [170, 335], [120, 322], [70, 310], [-20, 292]]), n: 6, silk: "godolphin", start: 30 },
  // from the stables, past the Jockey Club, up the Shied and across the top of Warren Hill
  { route: join([[722, 721], [659, 722], [636, 726], [616, 734], [598, 736], [583, 733], [531, 743], [496, 758], [468, 787], [448, 800]], ROAD.shied.slice(1),
      [[304, 597], [241, 574], [191, 532], [130, 490], [101, 457], [54, 413], [25, 398], [-20, 392]]), n: 7, silk: "judmonte", start: 62 },
];
// the horseboxes' routes: the roads, slid onto the middle of the painted road (tools/snap_van_routes.py)
// VAN_ROUTES (made by tools/snap_van_routes.py: do not edit by hand)
const VAN_ROUTES = {
  oldStnFordham: [[1465.1,743.7],[1451.1,746.4],[1441.5,746.5],[1413.2,736.4],[1189.0,642.8],[1140.6,624.1],[1060.3,582.3],[987.6,539.4],[956.7,522.9],[920.2,501.4],[836.6,436.8],[799.6,410.8],[779.1,393.1],[745.3,366.5],[719.1,340.8],[677.6,315.7],[656.2,295.1],[650.8,292.0],[644.9,291.1],[632.0,294.0],[633.1,279.8],[629.8,256.0],[629.8,226.0],[628.0,187.0],[621.0,144.9],[626.2,106.0],[626.6,34.0],[630.0,-14.0]],
  nmktFordham: [[98.4,1071.2],[115.7,1066.1],[151.9,1061.6],[169.4,1057.4],[212.0,1043.3],[247.9,1026.8],[286.7,1014.8],[300.9,1007.7],[313.2,997.9],[334.6,976.8],[363.5,943.8],[370.7,938.5],[386.6,929.7],[394.2,923.6],[399.9,915.9],[445.7,840.6],[450.6,828.2],[452.2,819.2],[451.0,809.9],[448.0,800.0],[467.7,787.9],[475.4,776.8],[486.4,751.2],[495.6,725.9],[507.0,682.6],[511.7,675.0],[526.9,655.9],[548.0,618.0],[562.5,587.2],[573.7,555.9],[590.4,527.6],[604.4,488.0],[609.8,477.3],[623.0,456.0],[628.6,438.7],[637.8,375.2],[639.2,354.2],[637.1,333.2],[630.4,309.0],[630.2,303.1],[633.1,279.8],[629.8,256.0],[628.4,193.0],[626.7,175.0],[621.9,153.9],[621.0,144.9],[626.2,106.0],[626.6,34.0],[630.0,-14.0]],
  buryAvenue: [[1119.4,-17.4],[1107.7,-12.0],[1099.9,-7.2],[1062.6,26.7],[1028.6,46.9],[979.6,82.8],[929.5,115.4],[840.7,165.4],[806.5,188.8],[739.6,228.9],[710.4,249.7],[669.9,275.4],[661.8,279.5],[641.2,285.5],[634.9,290.6],[626.0,301.0],[619.0,306.5],[597.4,316.9],[526.1,361.4],[496.4,375.9],[459.4,402.3],[437.4,419.7],[429.5,424.4],[420.9,427.2],[408.0,426.2],[388.3,421.8],[335.1,393.9],[263.3,352.1],[252.2,341.9],[225.7,333.5],[197.4,316.6],[165.6,299.9],[133.5,278.1],[101.4,261.8],[49.0,232.5],[-1.9,200.8],[-17.4,185.4]],
  toTheRaces: [[722.0,721.0],[659.0,722.0],[636.0,726.0],[616.0,734.0],[598.0,736.0],[583.0,733.0],[531.0,743.0],[496.0,758.0],[490.6,740.0],[499.1,714.6],[504.1,691.1],[507.0,682.6],[511.7,675.0],[526.9,655.9],[549.4,615.3],[562.5,587.2],[573.7,555.9],[591.6,524.8],[605.7,485.3],[624.3,453.2],[629.7,432.8],[637.8,375.2],[639.2,354.2],[637.1,333.2],[630.4,309.0],[630.2,303.1],[633.1,279.8],[629.8,256.0],[628.4,193.0],[626.7,175.0],[621.9,153.9],[621.0,144.9],[626.2,106.0],[626.6,34.0],[630.0,-14.0]],
};
// /VAN_ROUTES
// One way round (owner, 14 Nov: "some of the vans are still hitting buildings, horses or each other"): every road has one
// direction, the one the strings already walk it in, so nothing meets head on. In by Old Station Road, Newmarket Road
// and Bury Road; out up Fordham Road, or down the High Street and Station Road to the Avenue.
const VANS = [VAN_ROUTES.oldStnFordham, VAN_ROUTES.nmktFordham, VAN_ROUTES.buryAvenue];
const AVENUE_W = VAN_ROUTES.buryAvenue.filter(([x, z]) => x < 204 && z < 310);   // the Avenue, from Exeter Road's end to the board's edge
for (const s of STRINGS) { if (s.avenue) s.route = s.route.concat(AVENUE_W); s.route = roundabout(s.route); }
// The Gallops: the lots come in over the board's edge, gallop up the field, wheel round at the top and come back out
// along the hedge, so nothing appears or fades in the middle of the heath.
const GALLOPS = [[-20, 178], [60, 171], [130, 162], [200, 150], [270, 137], [340, 123], [410, 109], [480, 96], [530, 88], [553, 76], [550, 62], [530, 55],
  [480, 60], [410, 74], [340, 88], [270, 102], [200, 116], [130, 129], [60, 142], [-20, 156]];
const WARREN = [[262, 448], [205, 428], [152, 407], [110, 390], [60, 377], [10, 366], [-20, 360]];
const LONER = [[135, 786], [164, 783], [197, 760], [225, 743], [258, 726], [274, 734], [279, 769], [295, 803], [317, 850], [315, 877], [306, 889], [285, 903],
  [256, 910], [188, 917], [177, 927], [101, 957], [63, 983], [20, 1005], [-20, 1022]];
const PADDOCK = [                                                   // w: how far the way back lies from the way out
  { pts: [[1022, 129], [1075, 93], [1105, 82], [1129, 78], [1159, 79], [1190, 87], [1227, 106], [1254, 127]], coat: 2, w: 14 },
  { pts: [[1315, 209], [1282, 246], [1266, 256], [1248, 259], [1234, 254], [1220, 242], [1205, 217], [1196, 193]], coat: 0, w: -11 },
  { pts: [[1027, 423], [1140, 392], [1257, 361]], coat: 3, w: 9 },
];
// Where the painted horses stood (they are painted out of the game's board: newmarket-live/tools/clean_board.py --game),
// moving ones go round instead. [centre x, z, half length, half width, turn, how many, kind], kind: loose, ridden or led.
const ROUNDS = [
  [800, 96, 60, 22, 0.05, 3, "loose"], [852, 100, 38, 24, -0.2, 2, "loose"], [905, 180, 36, 15, 0.35, 2, "loose"],   // the paddocks by Bury Road
  [1270, 188, 62, 20, 0.33, 2, "ridden"], [1222, 301, 30, 9, 0, 1, "loose"],                                            // the Stud's paddocks
  [985, 449, 42, 9, -0.35, 2, "loose"], [1305, 447, 34, 12, 0.1, 1, "loose"], [1292, 576, 30, 10, 0, 1, "ridden"],
  [215, 712, 70, 24, -0.2, 1, "ridden"],                                                                               // the hack below Palace House
  [838, 575, 26, 9, 0.35, 2, "led"], [858, 722, 30, 13, -0.2, 1, "ridden"],                                             // Tattersalls: the yard and the lawn
  [860, 868, 85, 11, -0.2, 2, "led"],                                                                                  // round the stable yard
];
const PATH_WEST = [[776, 612], [769, 634], [763, 656], [757, 680]];   // the sandy path west of Tattersalls: a horse led up and down
// a there-and-back line made into a round, so a horse never turns on the spot (w: how far apart the two sides are)
const loopOf = (pts, w = 12) => pts.concat(rev(pts).map(([x, z]) => [x, z + w]));
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
  return { obj: g, mats: [body, roof, dark, glass], keepLeft: 1, van: true, rank: k };   // down the middle: the roads are one way
}
const tmpN = new THREE.Vector3(), tmpS = new THREE.Vector3(), tmpD = new THREE.Vector3(), tmpQ = new THREE.Vector3();
function place(m, p, dir, alpha, t = 0) {
  m.obj.position.copy(p);
  if (dir) {
    m.obj.rotation.y = Math.atan2(-dir.z, dir.x);                 // the models face +x
    if (m.keepLeft) { tmpN.set(dir.z, 0, -dir.x).normalize().multiplyScalar(m.keepLeft); m.obj.position.add(tmpN); }   // on the left of the road
  }
  if (m.person && !REDUCED) m.obj.position.y = Math.abs(Math.sin(t * 7)) * 0.6;
  if (m.obj.userData.ground) m.obj.userData.ground.value = m.obj.position.z;
  if (dir) { m.dir = m.dir || new THREE.Vector3(); m.dir.copy(dir).setY(0).normalize(); }
  const s = m.obj.userData.shadow; s.position.set(m.obj.position.x + 2, 0.05, m.obj.position.z + 1.5); s.rotation.y = m.obj.rotation.y;
  m.obj.visible = s.visible = alpha > 0.01;
  for (const mt of m.mats) mt.opacity = alpha;
  s.material.opacity = alpha;
  if (m.lead) {
    // The lad walks at the horse's shoulder on whichever side is nearer the viewer. The board is drawn from the south
    // with heights going straight up the page, so a lad on the far side was drawn standing on the horse's back
    // (owner, 14 Nov: "these people standing on horses?"). When the horse turns he crosses in front of its nose.
    const d = tmpD.copy(m.dir || tmpD.set(1, 0, 0)), side = tmpS.set(d.z, 0, -d.x);
    if (side.z < 0) side.negate();                                 // the side nearer the viewer
    const flip = m.sideWas && m.sideWas.dot(side) < 0 && Math.abs(side.z) < 0.25;
    if (flip) side.negate();                                       // heading nearly north or south: he stays where he is
    m.sideWas = (m.sideWas || new THREE.Vector3()).copy(side);
    m.sideNow = m.sideNow ? m.sideNow.lerp(side, 0.06) : side.clone();
    const k = Math.min(1, m.sideNow.length());                     // less than 1 while he is crossing over
    const q = tmpQ.copy(m.obj.position).setY(0).addScaledVector(m.sideNow, 6.5).addScaledVector(d, 5 + (1 - k) * 9);
    place(m.lead, q, d, alpha, t);
  }
}
const hide = (m, t) => { m.path = null; m.spd = 0; place(m, m.obj.position, null, 0, t); };
// a journey: legs along routes (or pauses); it repeats after a rest. Fades in and out where it starts and ends in the open.
// road: it uses the roads, so the horseboxes look out for it. group: a string, which halts together.
function journey(m, legs, { start = 0, rest = 8, fadeIn = true, fadeOut = true, hours = null, road = false, group = null } = {}) {
  const ls = legs.map((l) => ({ ...l, dur: l.pause ?? l.curve.L / l.speed })), total = ls.reduce((a, l) => a + l.dur, 0);
  let last = null, lastDir = null, clock = -start;
  if (road) ROADIES.push(m);
  if (group) group.members.push(m);
  movers.push({ m, step(t, dt) {
    // between runs, wait for the right time of the morning (the strings go out at sunrise)
    const idle = clock < 0 || clock % (total + rest) > total;
    if (idle && hours && !inHours(hours)) { hide(m, t); return; }
    if (m.van) { m.go = ease(m.go ?? 1, rightOfWay(m), dt * 2.5); clock += dt * m.go; }
    else if (!(group && group.hold)) clock += dt;
    if (clock < 0) { hide(m, t); return; }
    const tau = clock % (total + rest);
    if (tau > total) { hide(m, t); return; }
    let acc = 0;
    for (const l of ls) {
      if (tau <= acc + l.dur) {
        const a = Math.min(fadeIn ? Math.min(1, tau / 1.2) : 1, fadeOut ? Math.min(1, (total - tau) / 1.2) : 1);
        if (l.pause != null) { if (m.act) setGait(m, "stand", 0); if (last) place(m, last, lastDir, a, t); return; }
        const u = (tau - acc) / l.dur, p = l.curve.getPointAt(u), d = l.curve.getTangentAt(u);
        const held = group && group.hold;
        if (m.act) setGait(m, held ? "stand" : l.gait, l.speed);
        m.path = m.path || {}; m.path.curve = l.curve; m.path.s = u * l.curve.L; m.cruise = l.speed; m.spd = held ? 0 : l.speed * (m.van ? m.go : 1);
        last = p; lastDir = d; place(m, p, d, a, t); return;
      }
      acc += l.dur;
    }
  } });
}
const ease = (v, to, step) => v + Math.max(-step, Math.min(step, to - v));

// ---- right of way (owner, 14 Nov: "some of the vans are still hitting buildings, horses or each other")
// Everything on the roads is in ROADIES. A horsebox looks a few seconds down its own route, and at where everything
// near it will be by then: if it would come up against a horse, a lad or another horsebox ahead of it, it eases off
// and waits, and falls in behind a string going its way. Only one horsebox is on the roundabout at a time.
const ROADIES = [], GROUPS = [];
const ZONE = { x: 632, z: 292, rx: 52, rz: 40 };                   // the roundabout and the mouths of its roads
let zoneOwner = null;
const inZone = (q) => Math.hypot((q.x - ZONE.x) / ZONE.rx, (q.z - ZONE.z) / ZONE.rz) < 1;
const A0 = new THREE.Vector3(), A1 = new THREE.Vector3(), B0 = new THREE.Vector3(), tmpV = new THREE.Vector3();
// where a thing will be in tau seconds, going at v: along its route if it has one
function ahead(m, tau, v, out) {
  if (m.path && m.path.curve) return m.path.curve.getPointAt(Math.min(1, Math.max(0, (m.path.s + v * tau) / m.path.curve.L)), out);
  out.copy(m.obj.position); if (m.dir) out.addScaledVector(m.dir, v * tau); return out;
}
// how many seconds until a, driving on, comes up against b ahead of it (Infinity if it won't in the next three)
function meets(a, b) {
  tmpV.subVectors(b.obj.position, a.obj.position).setY(0);
  if (tmpV.length() > 170) return Infinity;
  if (a.dir && b.dir && a.dir.dot(b.dir) > 0.3 && tmpV.dot(a.dir) < 0) return Infinity;   // it is behind, going my way: its look-out, not mine
  const gap = b.van ? 34 : 24, vb = b.spd || 0;
  for (let tau = 0; tau <= 3.01; tau += 0.5) {
    ahead(a, tau, a.cruise, A0); ahead(b, tau, vb, B0); B0.y = A0.y = 0;
    if (A0.distanceTo(B0) >= gap) continue;
    ahead(a, tau + 0.3, a.cruise, A1); A1.y = 0;
    if (A1.sub(A0).dot(B0.sub(A0)) >= 0) return tau;               // and ahead of me when I get there
  }
  return Infinity;
}
// 1 = drive on, 0 = wait, and in between as something ahead gets nearer
function rightOfWay(van) {
  if (!van.path || !van.obj.visible) { if (zoneOwner === van) zoneOwner = null; return 1; }
  ahead(van, 0, 0, A0); const inNow = inZone(A0); ahead(van, 1.4, van.cruise, A1); const wants = inNow || inZone(A1);
  if (zoneOwner === van && !wants) zoneOwner = null;
  if (wants && !zoneOwner) zoneOwner = van;
  if (wants && zoneOwner !== van && !inNow) return 0;
  let first = Infinity;
  for (const o of ROADIES) {
    if (o === van || !o.obj.visible) continue;
    const tau = meets(van, o);
    if (tau === Infinity) continue;
    if (o.van && van.rank < o.rank && meets(o, van) < Infinity) continue;   // each would wait for the other: the first of them goes
    if (tau < first) first = tau;
  }
  return first >= 3 ? 1 : first <= 1 ? 0 : (first - 1) / 2;
}
// a string halts, all together, rather than walk into the back of a horsebox standing in its way
function holdGroups() {
  for (const g of GROUPS) {
    g.hold = false;
    for (const h of g.members) {
      if (!h.obj.visible || !h.dir) continue;
      for (const o of ROADIES) {
        if (!o.van || !o.obj.visible) continue;
        tmpV.subVectors(o.obj.position, h.obj.position).setY(0);
        const along = tmpV.dot(h.dir), side = Math.abs(tmpV.x * h.dir.z - tmpV.z * h.dir.x);
        if (along > 4 && along < 30 && side < 9) { g.hold = true; break; }
      }
      if (g.hold) break;
    }
  }
}
const newGroup = () => { const g = { members: [], hold: false }; GROUPS.push(g); return g; };
function circuit(m, curve, speed, phase, gait = "walk") {
  movers.push({ m, step(t) {
    const u = ((phase + t * speed / curve.L) % 1 + 1) % 1, d = curve.getTangentAt(u);
    if (speed < 0) d.negate();                                     // going round the other way
    if (m.act) setGait(m, gait, Math.abs(speed));
    place(m, curve.getPointAt(u), d, 1, t);
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

  // a phone gets a lighter board: fewer of the horses that are always in sight, and smaller lots on the gallops
  const few = phone;
  // strings walking out to the heath, off the left edge, then round again
  for (const s of STRINGS) { const c = P(s.route), g = newGroup(); for (let i = 0; i < s.n; i++) { const h = makeHorse({ silk: s.silk }); h.keepLeft = 4; journey(h, [{ curve: c, speed: 15, gait: "walk" }], { start: s.start + i * 1.7, rest: 20, hours: [5.75, 11.5], road: true, group: g }); } }
  // The Gallops and Warren Hill: lots working in pairs. A first lot is out in the half light; once it has brightened
  // up a little the heath fills (owner, 14 Nov: "increase the horses on the gallops once it's brightened up a tad").
  const lone = P(LONER), BRIGHT = 6.4;
  const galLots = few ? 3 : 4, galN = few ? 4 : 5, galLen = P(GALLOPS).L / 66;
  for (let lot = 0; lot < galLots; lot++)
    for (let i = 0; i < galN; i++) journey(makeHorse(), [{ curve: P(GALLOPS.map(([x, z], k) => (i % 2 ? (k < 9 ? [x, z - 7] : k < 12 ? [x - 7, z] : [x, z + 7]) : [x, z]))), speed: 66 - (i >> 1), gait: "gallop" }],
      { start: 3 + lot * (galLen + 7) / galLots + (i >> 1) * 0.9, rest: 7, hours: [lot ? BRIGHT : 5.8, 11.5] });
  const warLots = few ? 3 : 4, warN = few ? 3 : 4, warLen = P(WARREN).L / 54;
  for (let lot = 0; lot < warLots; lot++)
    for (let i = 0; i < warN; i++) journey(makeHorse(), [{ curve: P(WARREN.map(([x, z]) => [x, z + (i % 2) * 7 + (lot % 2) * 3])), speed: 54, gait: "gallop" }],
      { start: 6 + lot * (warLen + 9) / warLots + (i >> 1) * 0.9, rest: 9, hours: [lot ? BRIGHT : 5.9, 11.5] });
  journey(makeHorse(), [{ curve: lone, speed: 46, gait: "gallop" }], { start: 9, rest: 12, hours: [6, 11.5] });
  // horseboxes: in by Old Station Road, Newmarket Road and Bury Road, out up Fordham Road and along the Avenue
  VANS.forEach((r, i) => journey(makeVan(i), [{ curve: P(roundabout(r)), speed: 28 }], { start: i * 16 + 4, rest: 12 + i * 5, hours: [6.2, 11.5], road: true }));
  // The paddocks and yards. Nothing stands still (owner, 14 Nov: "there shouldn't really be any still horses"): the
  // loose horses amble round and round their paddocks, the led and ridden ones go round the yards and the lawns.
  let nRound = 0;
  const round = (curve, kind, speed, phase, coat, back) => {
    const h = makeHorse({ rider: kind === "ridden", coat }); if (kind === "led") h.lead = makePerson();
    circuit(h, curve, back ? -speed : speed, phase, "walk");
  };
  for (const pd of PADDOCK) round(P(loopOf(pd.pts, pd.w ?? 12), true), "loose", 6.5, Math.random(), pd.coat);
  journey(makeHorse({ rider: false, coat: 4 }), [{ curve: P([[1333, 431], [1390, 452], [1466, 482]]), speed: 7, gait: "walk" }], { start: 5, rest: 6 });
  for (const [cx, cz, rx, rz, turn, n, kind] of ROUNDS) {
    const c = P(oval(cx, cz, rx, rz, turn), true), back = nRound++ % 2 === 1, k = few ? Math.ceil(n / 2) : n;
    for (let i = 0; i < k; i++) round(c, kind, kind === "loose" ? 6 + (i % 2) : kind === "led" ? 9 : 11, i / k + 0.13 * nRound, nRound + i * 2, back);
  }
  round(P(loopOf(PATH_WEST, 9), true), "led", 8, 0.2, 2);
  // the yards: horses led from one stable to another, horses ridden round the ring, people about
  YARD_TRIPS.forEach((tr, i) => { const h = makeHorse({ rider: false }); h.lead = makePerson();
    journey(h, [{ curve: P(tr), speed: 9, gait: "walk" }], { start: 3 + i * 9, rest: 3 + i * 2 }); });
  const ring = P([[1281, 847], [1241, 870], [1242, 883], [1260, 908], [1346, 896], [1370, 887], [1345, 852], [1305, 843]], true);
  for (let i = 0; i < 2; i++) circuit(makeHorse(), ring, 13, i / 2, "walk");
  const parade = P(oval(1168, 752, 53, 26, 0.26), true);
  for (let i = 0; i < 3; i++) { const h = makeHorse({ rider: false }); h.lead = makePerson(); circuit(h, parade, 9, i / 3, "walk"); }
  PEOPLE_TRIPS.forEach((tr, i) => journey(makePerson(), [{ curve: P(tr), speed: 7, gait: "walk" }, { pause: 3 }, { curve: P(rev(tr)), speed: 7, gait: "walk" }], { start: i * 2.3, rest: 4 + i, fadeIn: false, fadeOut: false }));

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
  for (const [cx, cz, rx, rz, turn] of ROUNDS) line(oval(cx, cz, rx, rz, turn), "#ff8000", true);
  PADDOCK.forEach((pd) => line(loopOf(pd.pts, pd.w), "#ff8000", true)); line(loopOf(PATH_WEST, 9), "#ff8000", true);
  VANS.forEach((r) => line(roundabout(r), "#00e0ff"));
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
  boxes: { route: () => VAN_ROUTES.toTheRaces, n: 3, gap: 2.6, speed: 70, make: (i) => makeVan(i) },
};
const shots = [];
const LITE = document.documentElement.classList.contains("lite");
let tick = 0;
function procession(kind, opts = {}) {
  const P0 = PROC[kind]; if (!P0 || !horseProto) return 0;
  const curve = P(roundabout(P0.route())), dur = curve.L / P0.speed;
  for (let i = 0; i < P0.n; i++) {
    const m = P0.make(i, opts); if (m.act) setGait(m, "walk", P0.speed); if (m.van) { m.keepLeft = 1; m.rank = 10 + i; } else m.keepLeft = 3;
    m.path = { curve, s: 0 }; m.cruise = P0.speed; ROADIES.push(m);                // on the roads: the horseboxes look out for it
    shots.push({ m, curve, speed: P0.speed, t: -i * P0.gap, dur, gait: P0.speed > 26 && m.act ? "gallop" : "walk" });
  }
  return (dur + P0.n * P0.gap) * 1000;
}
function stepShots(t, dt) {
  for (let k = shots.length - 1; k >= 0; k--) {
    const s = shots[k], m = s.m;
    if (m.van && s.t >= 0) { m.go = ease(m.go ?? 1, rightOfWay(m), dt * 2.5); s.t += dt * m.go; } else s.t += dt;
    if (s.t < 0) { place(m, m.obj.position, null, 0, t); m.spd = 0; continue; }
    if (s.t > s.dur) { place(m, m.obj.position, null, 0, t); m.obj.visible = false; shots.splice(k, 1); const r = ROADIES.indexOf(m); if (r >= 0) ROADIES.splice(r, 1); if (zoneOwner === m) zoneOwner = null; continue; }
    const u = s.t / s.dur, a = Math.min(1, s.t / 1.0, (s.dur - s.t) / 1.0);
    if (m.act) setGait(m, s.gait, s.speed);
    m.path.s = u * s.curve.L; m.spd = s.speed * (m.van ? m.go : 1);
    place(m, s.curve.getPointAt(u), s.curve.getTangentAt(u), a, t);
    if (m.mixer) m.mixer.update(dt);
  }
}
// __advance, __state and noDraw are checking aids: __state lists everything that moves (kind, where, which way, in sight)
window.LIFE = { procession, noDraw: false,
  __advance: (secs) => { stepShots(0, secs); return shots.map((s) => [Math.round(s.m.obj.position.x), Math.round(s.m.obj.position.z), s.m.obj.visible]); },
  __state: () => [...movers.map((mv) => mv.m), ...shots.map((s) => s.m)].flatMap((m) => [m, m.lead].filter(Boolean)).map((m) => ({ kind: m.van ? "van" : m.person ? "person" : "horse", road: ROADIES.includes(m), x: +m.obj.position.x.toFixed(1), z: +m.obj.position.z.toFixed(1),
    dx: m.dir ? +m.dir.x.toFixed(3) : 0, dz: m.dir ? +m.dir.z.toFixed(3) : 0, seen: m.obj.visible, spd: m.spd || 0, gait: m.gait || "" })) };
B.addFrame((t, dt) => {
  if (!renderer || lost) return;
  // nothing to draw while the board is out of sight: at Ascot, or under a sheet on a phone (where the sheet fills the screen)
  if (document.body.classList.contains("at-ascot") || B.covered) return;   // still behind a sheet, like the board
  holdGroups();
  // on a phone each horse's legs are worked out every other frame (half of them one frame, half the next): at 20 pixels
  // long nobody can tell, and it pays for the extra horses now on the board
  tick++;
  for (let i = 0; i < movers.length; i++) {
    const mv = movers[i], m = mv.m; mv.step(t, dt);
    if (!m.mixer) continue;
    if (!m.obj.visible) { m.owed = 0; continue; }
    m.owed = (m.owed || 0) + dt;
    if (!LITE || ((tick + i) & 1) === 0) { m.mixer.update(m.owed); m.owed = 0; }
  }
  stepShots(t, dt);
  if (!window.LIFE.noDraw) renderer.render(scene, cam);
});
// ?nolife=1 leaves the board without its 3D life (for checking the game quickly on a machine without a graphics chip)
if (!new URLSearchParams(location.search).has("nolife")) startLife().catch((e) => { console.warn("Newmarket life didn't start", e); });
