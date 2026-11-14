// The three hands for the style frames (see style-frames.html). Each is a short list of settings (palette, light,
// how round or how faceted things are) and one 'build' that puts the scene together from the kit's plain blocks.
// The layout is the same in all three: the horses run towards -x on a 20 m track (z 0 to 20), the inside rail and the
// camera on the -z side, the lawn and the stand beyond the outer rail from z 20.

// ---------- pieces shared by more than one hand ----------
function rails(K, c, o = {}) {
  for (const z of [0.3, 19.7]) {
    K.box(160, 0.24, 0.24, c.rail, 0, 1.1, z, { r: o.r ?? 0.1 });
    for (let x = -80; x <= 80; x += 2.6) K.cyl(0.085, 0.085, 1.1, c.rail, x, 0, z + (z < 10 ? -0.02 : 0.02), { seg: 8 });
  }
  // the winning post: a white pole with a red disc, on the inside rail
  K.cyl(0.12, 0.12, 5.2, c.rail, 0, 0, -0.7, { seg: 10 });
  K.put(new K.THREE.CylinderGeometry(0.85, 0.85, 0.16, 28), c.post || "#d1483c", 0, 5.3, -0.7, { rot: [Math.PI / 2, 0, 0] });
  K.put(new K.THREE.CylinderGeometry(0.5, 0.5, 0.18, 28), c.rail, 0, 5.3, -0.7, { rot: [Math.PI / 2, 0, 0] });
}
function ground(K, c, o = {}) {
  const T = K.THREE, flatMat = (col, map) => new T.MeshStandardMaterial({ color: map ? "#ffffff" : col, map: map || null, roughness: 1, metalness: 0 });
  const plane = (w, d, col, x, y, z, map) => { const m = K.put(new T.PlaneGeometry(w, d).rotateX(-Math.PI / 2), flatMat(col, map), x, y, z, { cast: false }); return m; };
  plane(900, 900, c.lawn, 0, 0, 0);
  const st = K.stripes(c.turf[0], c.turf[1], 2); st.wrapS = st.wrapT = T.RepeatWrapping; st.repeat.set(160 / (o.band || 11), 1);
  plane(160 * 2, 20, null, 0, 0.02, 10, st);
  if (c.path) plane(320, o.pathDepth || 3.4, c.path, 0, 0.025, o.pathZ || 25.6);
}
function clock(K, r, x, y, z, c) {
  const face = K.canvas(256, 256, (g, w) => {
    g.fillStyle = c.face; g.beginPath(); g.arc(w / 2, w / 2, w / 2, 0, 7); g.fill();
    g.strokeStyle = c.ink; g.lineCap = "round";
    for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; g.lineWidth = i % 3 ? 5 : 11; g.beginPath(); g.moveTo(w / 2 + Math.sin(a) * w * 0.36, w / 2 - Math.cos(a) * w * 0.36); g.lineTo(w / 2 + Math.sin(a) * w * 0.43, w / 2 - Math.cos(a) * w * 0.43); g.stroke(); }
    g.lineWidth = 13; g.beginPath(); g.moveTo(w / 2, w / 2); g.lineTo(w / 2 + w * 0.2, w / 2 - w * 0.13); g.stroke();      // ten past two
    g.lineWidth = 9; g.beginPath(); g.moveTo(w / 2, w / 2); g.lineTo(w / 2 + w * 0.3, w / 2 + w * 0.17); g.stroke();
    g.fillStyle = c.ink; g.beginPath(); g.arc(w / 2, w / 2, 10, 0, 7); g.fill();
  });
  const T = K.THREE;
  K.put(new T.CylinderGeometry(r * 1.14, r * 1.14, 0.36, 40), c.rim, x, y, z + 0.1, { rot: [Math.PI / 2, 0, 0] });
  K.put(new T.CircleGeometry(r, 40), new T.MeshStandardMaterial({ map: face, roughness: 0.9 }), x, y, z - 0.1, { rot: [0, Math.PI, 0], cast: false });
}
function flag(K, x, y, z, h, col, pole = "#f6f1e6") {
  K.cyl(0.07, 0.07, h, pole, x, y, z, { seg: 8 });
  K.box(1.9, 1.1, 0.07, col, x + 1.0, y + h - 1.2, z, { r: 0 });
  K.ball(0.14, "#d9b24c", x, y + h + 0.1, z);
}

function cloud(K, x, y, z, s, col = "#ffffff") {
  K.group(() => { for (const [dx, dy, r] of [[0, 0, 1], [-1.2, -0.25, 0.72], [1.25, -0.2, 0.8], [2.3, -0.4, 0.5], [-2.1, -0.45, 0.45]]) K.ball(r * s, col, dx * s, dy * s, 0, { cast: false }); }, x, y, z);
}

// ================= 1. TOY-TOWN CLAY =================
// After the pastel street: few, fat, rounded shapes; every edge soft; openings deep; details oversized; a short
// palette used in blocks (Ascot's cream and racing green, with blush and mustard as the accents); soft low sun.
const TOY = {
  label: "Toy-town clay", round: 0.16, bevel: 0.12, seg: 24,
  sun: [-0.78, 0.56, -0.42], sunCol: "#ffecd0", sunPow: 3.2, soft: 6, skyLight: "#cfe0ff", groundLight: "#ecd9b4", fill: 1.25,
  sky: ["#86b9e6", "#bfdcf0", "#f3ead8", "#f3ead8"], fog: ["#e8eef0", 150, 520], ao: 1, aoRadius: 1.8, exposure: 1.02,
  horse: { rough: 0.78 }, horseScale: 1.6,
  horses: [[-10, 7.6, ["#b5622f", "#6b3a1c"], "ballydoyle-navy", 2, 0.05], [-3.5, 12.6, ["#7a4a2a", "#1d1714"], "alcohol-free", 1, 0.21], [3.5, 6.4, ["#c2c0b8", "#7c7973"], "aga-khan", 3, 0.34]],
  build(K) {
    const c = { cream: "#f4e6cb", white: "#fbf6ec", green: "#2f6b4f", sage: "#8db79c", blush: "#eda492", mustard: "#e6b84a", dark: "#27463b", glass: "#3b5566",
                rail: "#fbf8f0", lawn: "#d3e6b0", turf: ["#a4d58c", "#94ca7e"], path: "#f3e2c2", trunk: "#a8765a", leaf: ["#5d9c72", "#7db384", "#4c8a66"] };
    ground(K, c); rails(K, c);
    const T = K.THREE;
    // a wing of the stand: an arcade of fat arches, a balcony on fat balusters, tall windows under striped awnings, a hipped roof
    const wing = (x0, len, accent) => K.group(() => {
      const bays = Math.round(len / 4), pitch = len / bays;
      K.box(len + 1.2, 0.9, 13.5, c.white, len / 2, 0, 6.4, { r: 0.2 });                      // the plinth
      for (let s = 0; s < 3; s++) K.box(len + 1.2, 0.3, 0.8, c.white, len / 2, s * 0.3, -0.75 - (2 - s) * 0.8 + 0.4, { r: 0.1 });   // steps down to the lawn
      K.box(len, 8.4, 7.8, c.dark, len / 2, 0.9, 8.3, { r: 0 });                              // the body behind (seen only as the dark of the openings)
      K.wall(len, 4.3, 1.0, c.cream, 0, 0.9, 1.6, Array.from({ length: bays }, (_, i) => ({ x: (i + 0.5) * pitch, w: 2.7, h: 3.5, arch: true })));
      for (let i = 0; i < bays; i++) K.box(1.5, 2.5, 0.25, [c.blush, c.sage, c.mustard][(i + accent) % 3], (i + 0.5) * pitch, 0.9, 4.3, { r: 0.12 });   // doors, deep in the arcade
      K.box(len + 0.9, 0.42, 4.4, c.white, len / 2, 5.2, 2.2, { r: 0.18 });                   // the balcony
      for (let x = 0.35; x < len + 0.3; x += 0.62) K.cyl(0.13, 0.17, 0.8, c.white, x - 0.1, 5.62, 0.3, { seg: 10 });
      K.box(len + 0.9, 0.22, 0.4, c.white, len / 2, 6.42, 0.3, { r: 0.1 });
      K.wall(len, 4.0, 0.8, c.cream, 0, 5.62, 3.6, Array.from({ length: bays }, (_, i) => ({ x: (i + 0.5) * pitch, w: 1.7, y0: 0.2, h: 3.1, arch: true })));
      const aw = new T.MeshStandardMaterial({ map: K.stripes(accent % 2 ? "#eda492" : "#2f6b4f", "#fbf6ec", 6), roughness: 0.95 });
      for (let i = 0; i < bays; i++) if ((i + accent) % 2 === 0) K.put(new T.BoxGeometry(2.3, 0.12, 1.5), aw, (i + 0.5) * pitch, 9.05, 3.0, { rot: [0.5, 0, 0] });
      K.box(len + 1.1, 0.55, 11.6, c.white, len / 2, 9.62, 7.4, { r: 0.2 });                  // the cornice
      K.hip(len + 0.7, 11.2, 3.4, c.sage, len / 2, 10.17, 7.4);
      for (const fx of [5.6, len - 5.6]) { K.ball(0.42, c.mustard, fx, 13.75, 7.4); K.cyl(0.14, 0.2, 0.5, c.white, fx, 13.2, 7.4, { seg: 10 }); }
    }, x0, 0, 27);
    wing(-29.3, 24, 0); wing(3.3, 24, 1);
    // the clock tower: stubby and soft, a big clock, an arched belfry, a green cap with a gilt ball and a flag
    K.group(() => {
      K.box(9, 5.2, 9.6, c.white, 0, 0, 5.6, { r: 0.3 });
      K.box(2.9, 3.9, 0.5, c.dark, 0, 0, 0.95, { r: 0.25 }); K.cyl(1.45, 1.45, 0.5, c.dark, 0, 3.9, 0.95, { rot: [Math.PI / 2, 0, 0], seg: 28 }).position.y = 3.9;   // the doorway
      K.box(1.9, 3.0, 0.3, c.green, 0, 0, 1.3, { r: 0.12 });
      K.box(7.4, 13.6, 7.4, c.cream, 0, 5.2, 5.6, { r: 0.35 });
      K.box(8.2, 0.6, 8.2, c.white, 0, 11.4, 5.6, { r: 0.22 });
      clock(K, 2.3, 0, 15.2, 1.85, { face: "#fbf6ec", ink: "#27463b", rim: c.green });
      K.box(8.4, 0.7, 8.4, c.white, 0, 18.8, 5.6, { r: 0.25 });
      K.box(6.4, 3.6, 6.4, c.cream, 0, 19.5, 5.6, { r: 0.3 });
      for (const dx of [-1.55, 1.55]) { K.box(1.5, 2.1, 0.5, c.dark, dx, 19.9, 2.5, { r: 0.2 }); K.cyl(0.75, 0.75, 0.5, c.dark, dx, 21.75, 2.5, { rot: [Math.PI / 2, 0, 0], seg: 20 }); }
      for (const dz of [-1.55, 1.55]) { K.box(0.5, 2.1, 1.5, c.dark, -3.1, 19.9, 5.6 + dz, { r: 0.2 }); K.cyl(0.75, 0.75, 0.5, c.dark, -3.1, 21.75, 5.6 + dz, { rot: [0, 0, Math.PI / 2], seg: 20 }); }
      K.box(7.4, 0.6, 7.4, c.white, 0, 23.1, 5.6, { r: 0.22 });
      K.put(new T.ConeGeometry(4.9, 4.6, 4), K.mat(c.green, { flat: true }), 0, 26.0, 5.6, { rot: [0, Math.PI / 4, 0] });
      K.ball(0.5, c.mustard, 0, 28.6, 5.6); flag(K, 0, 28.9, 5.6, 4.2, c.blush);
    }, -1, 0, 26);
    flag(K, -17.3, 13.6, 34.4, 4.6, c.mustard); flag(K, 15.3, 13.6, 34.4, 4.6, c.green);
    // trees: a short trunk and a handful of soft balls
    const tree = (x, z, s = 1) => K.group(() => {
      K.cyl(0.42 * s, 0.6 * s, 4.2 * s, c.trunk, 0, 0, 0, { seg: 10 });
      const n = 5 + Math.floor(K.rnd() * 3);
      for (let i = 0; i < n; i++) { const a = (i / n) * 6.28 + K.rnd(), r = (2.3 + K.rnd() * 1.2) * s, d = i ? 2.4 * s : 0; K.ball(r, c.leaf[i % 3], Math.cos(a) * d, (5.6 + (i ? K.rnd() * 2.2 : 2.6)) * s, Math.sin(a) * d); }
    }, x, 0, z);
    for (let i = 0; i < 9; i++) tree(-58 + i * 14.5 + K.rnd() * 4, 49 + K.rnd() * 7, 1.25 + K.rnd() * 0.5);
    tree(-41, 31, 1.15); tree(-49, 38, 1.4); tree(45, 30, 1.2); tree(53, 37, 1.45);
    tree(-47, -12, 0.95); tree(40, -15, 1.05); tree(-58, -22, 1.2);
    // lamps along the path, and a few clay clouds
    for (let x = -30; x <= 38; x += 12) if (Math.abs(x + 1) > 6) { K.cyl(0.1, 0.14, 3.4, c.green, x + 4, 0, 24.3, { seg: 10 }); K.ball(0.42, "#fff6dc", x + 4, 3.75, 24.3, { emit: "#ffe9b0" }); K.cyl(0.3, 0.2, 0.18, c.green, x + 4, 4.1, 24.3, { seg: 12 }); }
    cloud(K, -70, 46, 170, 9); cloud(K, 30, 58, 200, 12); cloud(K, 95, 40, 150, 8);
    // clipped balls in tubs along the path, and a hedge with flowers on the inside of the course
    for (let x = -34; x <= 38; x += 8) if (Math.abs(x + 1) > 6) { K.box(0.9, 0.7, 0.9, c.white, x, 0, 24.2, { r: 0.12 }); K.cyl(0.08, 0.08, 0.9, c.trunk, x, 0.7, 24.2, { seg: 8 }); K.ball(0.75, c.leaf[2], x, 2.15, 24.2); }
    K.box(150, 0.9, 1.3, c.leaf[2], 0, 0, -3.6, { r: 0.35 });
    for (let x = -70; x < 70; x += 0.9) K.ball(0.2 + K.rnd() * 0.12, K.pick([c.blush, c.mustard, c.white, "#c9a3d6"]), x + K.rnd() * 0.5, 0.25, -4.9 - K.rnd() * 0.9);
    // people: peg figures, big and few, in blocks of colour
    const coats = ["#3b4d78", "#9a9ea8", "#3b4d78", "#c9a877", "#4f7a66"], frocks = [c.blush, c.mustard, "#a9c7e6", "#f4e6cb", "#c9a3d6", c.sage], skins = ["#efc6a4", "#e2b48e", "#b98562"];
    const person = (x, y, z, lady = K.rnd() < 0.45) => K.group(() => {
      const s = K.pick(skins);
      if (lady) { K.cone(0.56, 1.35, K.pick(frocks), 0, 0, 0, { seg: 16 }); K.ball(0.23, s, 0, 1.5, 0); K.cyl(0.5, 0.5, 0.07, K.pick(["#fbf6ec", c.blush, c.mustard]), 0, 1.68, 0, { seg: 18 }); K.cyl(0.2, 0.22, 0.16, "#fbf6ec", 0, 1.74, 0, { seg: 14 }); }
      else { const col = K.pick(coats); K.cyl(0.27, 0.36, 1.3, col, 0, 0, 0, { seg: 14 }); K.ball(0.23, s, 0, 1.52, 0); K.cyl(0.33, 0.33, 0.06, col === "#8d919b" ? "#8d919b" : "#2f3138", 0, 1.7, 0, { seg: 16 }); K.cyl(0.2, 0.21, 0.38, col === "#8d919b" ? "#8d919b" : "#2f3138", 0, 1.74, 0, { seg: 14 }); }
    }, x, y, z).scale.setScalar(1.3);
    for (let x = -30; x <= 36; x += 2.1 + K.rnd() * 2.4) if (Math.abs(x + 1) > 5.5) person(x, 0, 21.2 + K.rnd() * 1.4);          // at the rail
    for (let x = -27; x <= 35; x += 3.2 + K.rnd() * 3) if (Math.abs(x + 1) > 6) person(x, 5.62, 28.4 + K.rnd() * 0.8);          // on the balcony
    for (let x = -26; x <= 34; x += 5 + K.rnd() * 4) if (Math.abs(x + 1) > 6.5) person(x, 0.9, 27.6);                     // under the arches
  },
};

// ================= 2. FACETED, IN THE PINES =================
// After the tree house in the misty forest: every surface a flat facet; two families of colour only (sage and teal
// greens against one warm red timber), everything else cream; ranks of tall firs fading into a pale mist.
const FACET = {
  label: "Faceted, in the pines", flat: true, round: 0, bevel: 0, seg: 6,
  sun: [0.55, 0.62, -0.56], sunCol: "#fff2cc", sunPow: 2.7, soft: 3, skyLight: "#dbe8cc", groundLight: "#a9b890", fill: 1.55,
  sky: ["#cddcae", "#dfe4b8", "#e6e6c0", "#e6e6c0"], fog: ["#e2e5ba", 42, 205], ao: 0.85, aoRadius: 1.4, exposure: 1.0,
  horse: { rough: 0.95, dark: "#3a3f40", light: "#efe6c8", skin: "#d9a98a" }, horseScale: 1.6,
  horses: [[-10, 7.6, ["#b4634c", "#6e3b33"], "ballydoyle-orange", 2, 0.05], [-3.5, 12.6, ["#4a4446", "#2a2729"], "aga-khan", 1, 0.21], [3.5, 6.4, ["#d3d2c2", "#8b8a80"], "ballydoyle-pink", 3, 0.34]],
  build(K) {
    const c = { wood: "#c66d5b", woodDark: "#9c5046", roof: "#84453f", cream: "#efe6c8", teal: "#2d5754", olive: "#c9b458",
                rail: "#f1ebd0", lawn: "#b9cf98", turf: ["#8dba88", "#81ae7d"], path: "#e2d9a8", post: "#c66d5b", trunk: "#7d5448",
                fir: ["#5f9a86", "#7fb08f", "#4f8577", "#96bb95", "#6aa58f"], salmon: "#d98a70" };
    ground(K, c); rails(K, c, { r: 0 });
    const T = K.THREE;
    // an open timber stand: stepped terraces under a slatted roof on posts, a plank rail in front
    const stand = (x0, len) => K.group(() => {
      K.box(len, 1.1, 11, c.woodDark, len / 2, 0, 6.5);
      for (let i = 0; i < 5; i++) K.box(len, 0.62, 1.7, i % 2 ? c.woodDark : c.wood, len / 2, 1.1 + i * 0.62, 2.2 + i * 1.7);
      K.box(len, 9.4, 0.5, c.wood, len / 2, 1.1, 11.6);                                    // the plank back wall
      for (let x = 1; x < len; x += 1.3) K.box(0.08, 9.4, 0.08, c.woodDark, x, 1.1, 11.3);
      for (let x = 0.3; x <= len; x += (len - 0.6) / Math.round(len / 5)) {                 // posts and braces
        K.box(0.5, 8.4, 0.5, c.woodDark, x, 1.1, 1.2);
        K.box(0.32, 3.2, 0.32, c.woodDark, x + 1.05, 6.9, 1.2, { rot: [0, 0, 0.75] }); K.box(0.32, 3.2, 0.32, c.woodDark, x - 1.05, 6.9, 1.2, { rot: [0, 0, -0.75] });
      }
      K.box(len + 0.8, 0.5, 0.6, c.woodDark, len / 2, 9.5, 1.2);
      for (let x = 0.4; x < len; x += 1.0) K.box(0.14, 1.0, 0.14, c.cream, x, 1.1, 0.5);    // the front rail: pickets and a top board
      K.box(len, 0.2, 0.3, c.cream, len / 2, 2.1, 0.5);
      const run = 12.6, a = 0.2;                                                            // one slatted slope, falling to the back
      K.box(len + 2.4, 0.4, run, c.roof, len / 2, 10.2, 6.2, { rot: [-a, 0, 0] });
      for (let x = -0.6; x < len + 1.2; x += 1.5) K.box(0.22, 0.2, run + 0.2, c.woodDark, x, 10.55, 6.2, { rot: [-a, 0, 0] });
      for (let x = 2; x < len; x += 6) { K.box(0.1, 2.6, 0.1, c.cream, x, 11.4, 0.6); K.put(new T.ConeGeometry(0.75, 1.9, 3), K.mat(x % 12 < 6 ? c.salmon : c.olive), x + 0.95, 13.0, 0.6, { rot: [0, 0, -Math.PI / 2] }); }
    }, x0, 0, 27);
    stand(-30.5, 24); stand(4.5, 24);
    // the tower: a tapering timber frame, a cabin with the clock, a steep roof, a long pennant
    K.group(() => {
      K.put(new T.CylinderGeometry(3.1, 4.6, 17, 4), K.mat(c.wood), 0, 8.5, 5.6, { rot: [0, Math.PI / 4, 0] });
      for (const y of [4.5, 9, 13.5]) K.put(new T.CylinderGeometry(3.45 + (17 - y) * 0.09, 3.6 + (17 - y) * 0.09, 0.45, 4), K.mat(c.woodDark), 0, y, 5.6, { rot: [0, Math.PI / 4, 0] });
      K.box(1.7, 3.2, 0.3, c.teal, 0, 0, 2.2);
      K.box(8.6, 0.5, 8.6, c.woodDark, 0, 17, 5.6);
      for (let i = -4; i <= 4; i++) { K.box(0.14, 1.1, 0.14, c.cream, i * 1.0, 17.5, 1.5); K.box(0.14, 1.1, 0.14, c.cream, -4.1, 17.5, 5.6 + i * 1.0); }
      K.box(8.6, 0.18, 0.26, c.cream, 0, 18.6, 1.5); K.box(0.26, 0.18, 8.6, c.cream, -4.1, 18.6, 5.6);
      K.box(6.2, 6.4, 6.2, c.wood, 0, 17.5, 5.6);
      clock(K, 2.1, 0, 20.9, 2.42, { face: "#efe6c8", ink: "#2d5754", rim: c.woodDark });
      K.put(new T.ConeGeometry(5.6, 6.5, 4), K.mat(c.roof), 0, 27.1, 5.6, { rot: [0, Math.PI / 4, 0] });
      K.box(0.14, 5, 0.14, c.cream, 0, 30, 5.6); K.put(new T.ConeGeometry(0.9, 3.4, 3), K.mat(c.salmon), 1.7, 34.1, 5.6, { rot: [0, 0, -Math.PI / 2] });
    }, -1, 0, 26);
    // firs: stacked six-sided skirts, in ranks that fade into the mist; one in seven is the timber's red
    const fir = (x, z, h, col) => K.group(() => {
      K.cyl(h * 0.018, h * 0.03, h * 0.3, c.trunk, 0, 0, 0, { seg: 5 });
      const n = 5; for (let i = 0; i < n; i++) K.cone(h * (0.2 - i * 0.03), h * 0.27, col, 0, h * (0.14 + i * 0.165), 0, { seg: 7, rot: [0, i * 0.6, 0] });
    }, x, 0, z);
    for (let r = 0; r < 8; r++) for (let x = -120 - r * 6; x < 120 + r * 6; x += 6.5 + K.rnd() * 5) {
      if (r === 0 && x > -36 && x < 34) continue;
      fir(x + K.rnd() * 3, 44 + r * 11 + K.rnd() * 6, 17 + K.rnd() * 13 + r * 1.5, K.rnd() < 0.14 ? c.salmon : K.pick(c.fir));
    }
    for (const [x, z, h] of [[-46, 29, 21], [-53, 36, 26], [-41, 37, 17], [44, 30, 22], [51, 37, 27], [39, 38, 18], [-60, 24, 15], [58, 26, 16]]) fir(x, z, h, K.pick(c.fir));
    for (const [x, z, h] of [[-52, -9, 13], [-61, -16, 19], [46, -12, 15], [57, -19, 20], [-44, -20, 11]]) fir(x, z, h, K.pick(c.fir));
    // low faceted bushes inside the rail
    for (let x = -72; x < 72; x += 2.6 + K.rnd() * 3) K.put(new T.IcosahedronGeometry(0.8 + K.rnd() * 0.7, 0), K.mat(K.rnd() < 0.2 ? c.salmon : K.pick(c.fir)), x, 0.5, -4 - K.rnd() * 2.6, { rot: [K.rnd(), K.rnd(), 0], scale: [1.25, 0.8, 1.1] });
    // people: a six-sided cone and a faceted head, in the scene's own four colours
    const wear = [c.cream, c.salmon, c.teal, c.olive, c.cream, c.teal];
    const person = (x, y, z) => K.group(() => {
      const col = K.pick(wear); K.cone(0.5, 1.5, col, 0, 0, 0, { seg: 6, rot: [0, K.rnd(), 0] });
      K.put(new T.IcosahedronGeometry(0.27, 0), K.mat("#e0b494"), 0, 1.62, 0);
      if (K.rnd() < 0.55) K.cone(0.3, 0.42, col === c.teal ? c.cream : c.teal, 0, 1.78, 0, { seg: 6 });
    }, x, y, z).scale.setScalar(1.3);
    for (let x = -30; x <= 28; x += 2.2 + K.rnd() * 2.6) if (Math.abs(x + 1) > 5.5) person(x, 0, 21.3 + K.rnd() * 1.6);
    for (let i = 0; i < 5; i++) for (let x = -29; x <= 27; x += 2.4 + K.rnd() * 3.4) if (Math.abs(x + 1) > 5.2 && K.rnd() < 0.75) person(x, 1.1 + (i + 1) * 0.62, 29.2 + i * 1.7);
  },
};

// ================= 3. THE BRICK TOWN =================
// After the harbour town: brick laid in visible courses, stone bands, small white-framed windows in a grid, stepped
// gables and tiled roofs, black ironwork, round lamps; a slate sky with a low warm sun, so the red glows.
const BRICK = {
  label: "The brick town", round: 0, bevel: 0.05, seg: 20,
  sun: [-0.8, 0.42, -0.42], sunCol: "#ffe0b8", sunPow: 3.1, soft: 4, skyLight: "#a9b9cc", groundLight: "#8c7a6c", fill: 1.3,
  sky: ["#56676c", "#6f8084", "#93a09b", "#b3b8ad"], fog: ["#8f9c9a", 130, 480], ao: 1, aoRadius: 1.5, exposure: 1.0,
  horse: { rough: 0.8 }, horseScale: 1.6,
  horses: [[-10, 7.6, ["#b5622f", "#6b3a1c"], "ballydoyle-navy", 2, 0.05], [-3.5, 12.6, ["#5a3a26", "#1d1714"], "alcohol-free", 1, 0.21], [3.5, 6.4, ["#c9c7bd", "#7c7973"], "ballydoyle-orange", 3, 0.34]],
  build(K) {
    const T = K.THREE;
    const c = { brick: "#c9685a", stone: "#dedbd0", pale: "#cfd1ca", tile: "#dc9662", tileGreen: "#aab586", iron: "#2b2c30", glass: "#34424c", frame: "#f6f3e8",
                rail: "#f2efe6", lawn: "#a9b78e", turf: ["#8cb57a", "#80aa6f"], path: "#c3c0b4", leaf: ["#5f8f6a", "#6f9c74"], trunk: "#6b5248", post: "#d96654" };
    const course = K.blocks(1.0, 0.5, 0.07, 0.9), tiles = K.blocks(0.5, 0.4, 0.1, 0.8), paving = K.blocks(1.6, 0.8, 0.06, 0.92);
    const brick = K.mat(c.brick, { map: course }), stone = K.mat(c.stone, { map: course }), pale = K.mat(c.pale, { map: course });
    const tile = K.mat(c.tile, { map: tiles, flat: true }), tileG = K.mat(c.tileGreen, { map: tiles, flat: true });
    ground(K, c); rails(K, c, { r: 0 });
    K.put(new T.PlaneGeometry(200, 7.4).rotateX(-Math.PI / 2), (() => { const m = K.mat(c.path, { map: paving }); return m; })(), 0, 0.03, 23.7, { cast: false }).geometry.attributes.uv.array.set([0, 7.4, 200, 7.4, 0, 0, 200, 0]);
    const railing = (x0, x1, y, z) => { K.box(x1 - x0, 0.09, 0.09, c.iron, (x0 + x1) / 2, y + 1.0, z); K.box(x1 - x0, 0.06, 0.06, c.iron, (x0 + x1) / 2, y + 0.5, z); for (let x = x0; x <= x1 + 0.01; x += 1.25) K.box(0.08, 1.05, 0.08, c.iron, x, y, z); };
    const lamp = (x, y, z) => { K.cyl(0.07, 0.1, 2.6, c.iron, x, y, z, { seg: 8 }); K.ball(0.34, "#fff3c8", x, y + 2.85, z, { emit: "#ffd98a" }); };
    const window_ = (x, y, z, w, h) => { K.box(w + 0.36, h + 0.36, 0.12, c.frame, x, y - 0.18, z + 0.34); K.box(w - 0.1, h - 0.1, 0.1, c.glass, x, y + 0.05, z + 0.26); K.box(0.07, h, 0.06, c.frame, x, y, z + 0.2); K.box(w, 0.07, 0.06, c.frame, x, y + h / 2 - 0.03, z + 0.2); };
    // a wing: a stone base, a brick arcade, two floors of small windows, a tiled roof between stepped gables
    const wing = (x0, len, mat, roofMat) => K.group(() => {
      const bays = Math.round(len / 4), pitch = len / bays, H = 11.6;
      K.tbox(len + 0.8, 1.0, 12.4, stone, len / 2, 0, 7.6);
      K.box(len - 0.4, H, 9, "#22272b", len / 2, 1.0, 8.2);
      const holes = [];
      for (let i = 0; i < bays; i++) { holes.push({ x: (i + 0.5) * pitch, w: 2.6, h: 3.5, arch: true }); for (const y of [5.2, 8.4]) for (const dx of [-0.85, 0.85]) holes.push({ x: (i + 0.5) * pitch + dx, w: 0.95, y0: y, h: 1.45 }); }
      K.wall(len, H, 0.9, mat, 0, 1.0, 2.0, holes);
      for (let i = 0; i < bays; i++) for (const y of [5.2, 8.4]) for (const dx of [-0.85, 0.85]) window_((i + 0.5) * pitch + dx, 1.0 + y, 2.0, 0.95, 1.45);
      K.tbox(len + 0.3, 0.36, 1.2, stone, len / 2, 5.3, 2.4); K.tbox(len + 0.5, 0.5, 1.4, stone, len / 2, 12.3, 2.5);
      for (let i = 0; i < bays; i++) K.box(1.5, 2.6, 0.2, i % 2 ? c.tileGreen : "#3f5a52", (i + 0.5) * pitch, 1.0, 4.4);
      K.roof2(len - 0.6, 10.4, 4.6, roofMat, len / 2, 12.8, 7.6);
      // stepped gables at both ends
      const st = [[0, 0], [10.6, 0], [10.6, 0.9], [9.2, 0.9], [9.2, 2.1], [7.8, 2.1], [7.8, 3.3], [6.4, 3.3], [6.4, 4.6], [5.9, 4.6], [5.9, 5.6], [4.7, 5.6], [4.7, 4.6], [4.2, 4.6], [4.2, 3.3], [2.8, 3.3], [2.8, 2.1], [1.4, 2.1], [1.4, 0.9], [0, 0.9]];
      for (const gx of [0.9, len]) K.put(new T.ExtrudeGeometry(new T.Shape(st.map(([a, b]) => new T.Vector2(a, b))), { depth: 0.9, bevelEnabled: false }), mat, gx, 12.7, 2.3, { rot: [0, -Math.PI / 2, 0] });
      for (const cx of [len * 0.3, len * 0.7]) { K.tbox(1.3, 3.4, 1.3, mat, cx, 15.2, 9.6); K.tbox(1.6, 0.3, 1.6, stone, cx, 18.6, 9.6); }
      railing(-0.2, len + 0.2, 1.0, 0.7);
      for (let s2 = 0; s2 < 3; s2++) K.tbox(5, 0.34, 0.8, stone, len / 2, s2 * 0.33, 0.9 - (2 - s2) * 0.8);
    }, x0, 0, 27);
    wing(-29.2, 24, brick, tile); wing(3.2, 24, pale, tile);
    // the tower: eight-sided brick with stone bands, a big clock, an open stage, a tiled spire with a gilt ball
    K.group(() => {
      const oct = (r0, r1, h, m, y) => K.put(new T.CylinderGeometry(r0, r1, h, 8), m, 0, y + h / 2, 5.6, { rot: [0, Math.PI / 8, 0] });
      const bm = K.mat(c.brick, { map: (() => { const t = K.blocks(1.0, 0.5, 0.07, 0.9); t.repeat.set(13.5, 10.5); return t; })() });
      oct(4.7, 4.9, 1.2, K.mat(c.stone), 0); oct(4.3, 4.3, 21, bm, 1.2);
      for (const y of [7, 13.6, 21.6]) oct(4.55, 4.55, 0.5, K.mat(c.stone), y);
      K.box(2.4, 3.1, 0.4, "#22272b", 0, 1.2, 1.5); K.cyl(1.2, 1.2, 0.4, "#22272b", 0, 4.1, 1.5, { rot: [Math.PI / 2, 0, 0] });
      clock(K, 2.3, 0, 17.6, 1.55, { face: "#f6f3e8", ink: "#2b2c30", rim: c.iron });
      for (const y of [9.6]) window_(0, y, 1.35, 1.1, 1.7);
      oct(4.9, 4.9, 0.6, K.mat(c.stone), 22.2);
      for (let i = 0; i < 8; i++) { const a = (i / 8) * Math.PI * 2; K.box(0.5, 3.2, 0.5, c.stone, Math.sin(a) * 3.6, 22.8, 5.6 + Math.cos(a) * 3.6); }
      oct(4.5, 4.5, 0.5, K.mat(c.stone), 26);
      K.put(new T.ConeGeometry(4.9, 8.2, 8), tileG, 0, 30.6, 5.6, { rot: [0, Math.PI / 8, 0] });
      K.ball(0.55, "#d9b24c", 0, 35.0, 5.6); K.box(0.1, 2.4, 0.1, c.iron, 0, 35.3, 5.6);
    }, -1, 0, 26);
    // the town behind: plain houses with tiled gables, stepping back into the haze
    for (let r = 0; r < 3; r++) for (let x = -92; x < 92;) {
      const w = 7 + K.rnd() * 7, h = 7 + K.rnd() * 9 + r * 2, d = 9, z = 52 + r * 15 + K.rnd() * 4;
      if (r > 0 || x + w < -34 || x > 32) { K.tbox(w, h, d, K.rnd() < 0.3 ? brick : K.rnd() < 0.5 ? stone : pale, x + w / 2, 0, z); K.roof2(w + 0.3, d, 3 + K.rnd() * 1.5, K.rnd() < 0.8 ? tile : tileG, x + w / 2, h, z); }
      x += w + 0.5 + (K.rnd() < 0.25 ? 4 : 0);
    }
    // clipped balls in stone tubs, lamps, and a few round trees
    for (let x = -34; x <= 36; x += 7) if (Math.abs(x + 1) > 6) { K.tbox(1.0, 0.8, 1.0, stone, x, 0, 25.2); K.ball(0.85, c.leaf[0], x, 1.55, 25.2); }
    for (let x = -38; x <= 40; x += 13) lamp(x, 0, 20.9);
    railing(-80, 80, 0, 20.6);
    const tree = (x, z, s) => { K.cyl(0.35 * s, 0.5 * s, 3.6 * s, c.trunk, x, 0, z, { seg: 8 }); K.ball(3.3 * s, c.leaf[0], x, 6 * s, z); K.ball(2.4 * s, c.leaf[1], x + 1.9 * s, 7.2 * s, z - 0.6 * s); };
    tree(-42, 33, 1.2); tree(-50, 40, 1.5); tree(43, 32, 1.25); tree(51, 39, 1.5); tree(-48, -13, 1.0); tree(42, -15, 1.1);
    K.tbox(170, 0.8, 1.2, stone, 0, 0, -3.4);
    // the canal inside the course, behind a stone quay
    K.put(new T.PlaneGeometry(260, 60).rotateX(-Math.PI / 2), new T.MeshStandardMaterial({ color: "#5d7f88", roughness: 0.25, metalness: 0 }), 0, 0.04, -34.2, { cast: false });
    for (let x = -60; x <= 60; x += 12) if (x < -34 || x > 2) lamp(x + 5, 0.8, -3.4);
    // people: turned tokens in muted colours
    const wear = ["#3d4a63", "#8f949c", "#b8574a", "#d9c59a", "#4f6b5e", "#2f3136", "#c98f5a"];
    const person = (x, y, z) => K.group(() => { const col = K.pick(wear); K.cyl(0.2, 0.38, 1.25, col, 0, 0, 0, { seg: 12 }); K.ball(0.24, "#e2b995", 0, 1.45, 0); if (K.rnd() < 0.5) { K.cyl(0.3, 0.3, 0.06, "#2f3136", 0, 1.62, 0, { seg: 12 }); K.cyl(0.18, 0.19, 0.3, "#2f3136", 0, 1.66, 0, { seg: 12 }); } }, x, y, z).scale.setScalar(1.25);
    for (let x = -30; x <= 30; x += 1.9 + K.rnd() * 2.2) if (Math.abs(x + 1) > 5.5) person(x, 0, 21.6 + K.rnd() * 1.8);
    for (let x = -27; x <= 26; x += 3 + K.rnd() * 3) if (Math.abs(x + 1) > 6) person(x, 1.0, 28.2);
  },
};

export const STYLES = { toy: TOY, facet: FACET, brick: BRICK };
