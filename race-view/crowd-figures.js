// Crowd figure options, for review: today's four figures (0) and six new figure sets (1-6), loaded the same
// way and drawn with one material, so the crowd review and the line-up page can show any of them.
//   1 Refined skittle, 2 Fashion plate, 4 Low-poly faceted, 5 Soft painterly, 6 Lowry: meshes from
//     tools/blender/build_crowd_figure_sets.py (crowd_set_<n>), one mesh per figure, tint slots by material.
//   3 Painted cut-outs: cards that turn to face the camera, painted into an atlas by
//     tools/web/build_crowd_cutouts.py (crowd_cutouts.png).
// Every person carries six colours, one per slot (instanced attributes aC0..aC5):
//   0 coat or dress, 1 skin, 2 hat, 3 trim (trousers, waistcoat, lapels, sash, hat band), 4 hair,
//   5 for the cut-outs only: which painted figure (atlas column, row).
import * as THREE from "three";
import { mergeGeometries, mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";
import { SimplifyModifier } from "three/addons/modifiers/SimplifyModifier.js";

export const FIGURE_SETS = {
  0: { name: "Today", file: "crowd_people", line: "Today's simple figures: a cone or column, a ball head and a hat." },
  1: { name: "Refined skittle", file: "crowd_set_1", line: "Today's language with shoulders, a waist, a flared dress, trousered legs and crisper hats." },
  2: { name: "Fashion plate", file: "crowd_set_2", line: "Tall, slender Edwardian figures: tail coats and waistcoats, cinched long dresses, wide hats." },
  3: { name: "Painted cut-outs", cutout: true, line: "Flat painted figures on cards that turn to face the camera." },
  4: { name: "Low-poly faceted", file: "crowd_set_4", flat: true, line: "Flat-shaded planes: arms, a hand on a hip or a race card, lapels, hair." },
  5: { name: "Soft painterly", file: "crowd_set_5", paint: true, line: "Rounded, lumpy masses with dabs of hat and colour, a brushed finish." },
  6: { name: "Lowry", file: "crowd_set_6", flat: true, line: "Thin, angular, slightly hunched figures on stick legs." },
  // a closer look at 1 and 3 (shown to the owner as 1B, 1C, 3B and 3C)
  7: { name: "Skittle, dressed up", short: "1B", file: "crowd_set_7", line: "Set 1 with Edwardian touches: coat-tails, waistcoats, taller top hats, wider brims, hair up." },
  8: { name: "Skittle with arms", short: "1C", file: "crowd_set_8", line: "1B with simple arms and hands: at the sides, on a hip, holding a race card or a bag." },
  9: { name: "Cut-outs, clean poster", short: "3B", cutout: true, atlas: "crowd_cutouts_clean", line: "The same drawings in a poster finish: two flat tones per shape, no brush." },
  10: { name: "Cut-outs, inked", short: "3C", cutout: true, atlas: "crowd_cutouts_ink", line: "The same drawings with a dark ink outline, like a storybook." },
};
export const SLOTS = 6;
const PART_OF = (name) => (/clothes|main/.test(name) ? 0 : /skin/.test(name) ? 1 : /hat/.test(name) ? 2 : /trim/.test(name) ? 3 : /hair/.test(name) ? 4 : 0);

// Colours for the two new slots (the rest come from the crowd palette).
export const EXTRA_PALETTE = {
  trim_gent: ["#7b7f86", "#8d8f92", "#5d6168", "#a6a39a", "#cfc5ae", "#3a3d44", "#6d6f73", "#b9b2a0"],   // trousers and waistcoats
  trim_lady: ["#f7f3ea", "#2a2a2e", "#e2577a", "#6fb0dd", "#f3cf55", "#ffffff", "#c9606f", "#7cc0a0", "#b48ad6"],   // sashes, bands, flowers
  hair: ["#3b2a1e", "#5a3e2b", "#2a211c", "#7a5636", "#b08a5a", "#d8c08a", "#8a8580", "#1e1a18"],
};

function meshesOf(obj) { const out = []; obj.updateMatrixWorld(true); obj.traverse((o) => { if (o.isMesh) out.push(o); }); return out; }

// Load a figure set: a list of figures, each with a near and a far (lighter) geometry, its parts told apart by aPart.
export async function loadFigureSet(id, { loadModel, dir, texLoader }) {
  const S = FIGURE_SETS[id] || FIGURE_SETS[0];
  if (S.cutout) {
    const A = S.atlas || "crowd_cutouts";
    const info = await fetch(`${dir}/${A}.json`).then((r) => r.json());
    const atlas = await new Promise((res, rej) => texLoader.load(`${dir}/${A}.png`, res, undefined, rej));
    atlas.anisotropy = 4;
    atlas.generateMipmaps = true; atlas.minFilter = THREE.LinearMipmapLinearFilter;
    const [w, h] = info.card;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.Float32BufferAttribute([-w / 2, 0, 0, w / 2, 0, 0, w / 2, h, 0, -w / 2, h, 0], 3));
    g.setAttribute("normal", new THREE.Float32BufferAttribute([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1], 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute([0, 0, 1, 0, 1, 1, 0, 1], 2));
    g.setAttribute("aPart", new THREE.Float32BufferAttribute([0, 0, 0, 0], 1));
    g.setIndex([0, 1, 2, 0, 2, 3]);
    return { id, set: S, cutout: true, info, atlas, figures: [{ name: "cutout", lady: null, near: g, far: g, tris: 2 }] };
  }
  const gltf = await loadModel(dir, S.file);
  const roots = id === 0 ? ["person_gent_tophat", "person_gent", "person_lady", "person_lady_b"].map((n) => gltf.scene.getObjectByName(n)).filter(Boolean)
                         : gltf.scene.children.slice().sort((a, b) => a.name.localeCompare(b.name));
  const tag = (g, k) => { g.setAttribute("aPart", new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count).fill(k), 1)); return g; };
  const figures = roots.map((fig) => {
    const parts = meshesOf(fig).map((p) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", p.geometry.attributes.position);
      g.setAttribute("normal", p.geometry.attributes.normal);
      g.setIndex(p.geometry.index);
      return [g, PART_OF(p.material.name)];
    });
    const near = mergeGeometries(parts.map(([g, k]) => tag(g.clone(), k)));
    // the light figure for far off: about a third of the triangles (as the race view does today)
    const far = mergeGeometries(parts.map(([g, k]) => {
      const w0 = g.clone(); w0.deleteAttribute("normal");
      const w = mergeVertices(w0);
      const sg = new SimplifyModifier().modify(w, Math.floor(w.attributes.position.count * 0.65));
      sg.computeVertexNormals();
      return tag(sg.index ? sg.toNonIndexed() : sg, k);
    }).map((g) => (g.index ? g.toNonIndexed() : g)));
    const tris = (g) => (g.index ? g.index.count : g.attributes.position.count) / 3;
    return { name: fig.name, lady: /lady/.test(fig.name), near, far, tris: tris(near), farTris: tris(far) };
  });
  return { id, set: S, cutout: false, figures };
}

// A person's colours, from the crowd palette P (suits, dresses, skin, hats_gent, hats_lady).
export function lookFor(lady, P, pick) {
  return [
    pick(lady ? P.dresses : P.suits), pick(P.skin), pick(lady ? P.hats_lady : P.hats_gent),
    pick(lady ? EXTRA_PALETTE.trim_lady : EXTRA_PALETTE.trim_gent), pick(EXTRA_PALETTE.hair),
  ];
}

// The crowd's gentle life, in the vertex shader (nothing per person is sent each frame): a slow sway, never
// in step with the neighbours; and as the leader comes by, those near the rail rock on their toes, lean in
// towards the track, and some raise their hats (the hat is its own part, so it can lift). The cut-outs sway
// and rock but can't lift a painted hat.
//   opts: uniforms (uTime, uLeader), clip (discard below this height), set (from loadFigureSet)
export function crowdMaterial({ uniforms, clip = -100, set = null }) {
  const S = set ? set.set : {};
  const cut = !!(set && set.cutout);
  const mat = new THREE.MeshLambertMaterial({ color: "#ffffff", flatShading: !!S.flat });
  if (cut) mat.side = THREE.DoubleSide;
  const extraU = cut ? { uAtlas: { value: set.atlas }, uGrid: { value: new THREE.Vector2(set.info.cols, set.info.rows) } } : {};
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms, extraU);
    let vs = sh.vertexShader.replace("#include <common>", `#include <common>
        attribute float aPart; attribute vec3 aC0; attribute vec3 aC1; attribute vec3 aC2; attribute vec3 aC3; attribute vec3 aC4; attribute vec3 aC5;
        uniform float uTime; uniform vec2 uLeader; uniform vec2 uGrid;
        varying vec3 vC0; varying vec3 vC1; varying vec3 vC2; varying vec3 vC3; varying vec3 vC4; varying float vPart; varying float vWy;
        varying vec3 vObj; varying vec2 vCut;`);
    if (cut) {
      // the card turns about its upright axis to face the camera; lit as if it faced up and a little towards us
      vs = vs.replace("#include <beginnormal_vertex>", `
        vec3 cIp = vec3(instanceMatrix[3][0], instanceMatrix[3][1], instanceMatrix[3][2]);
        vec3 cTo = cameraPosition - cIp; cTo.y = 0.0;
        vec3 cFwd = normalize(cTo + vec3(1e-4, 0.0, 0.0));
        vec3 cRight = vec3(cFwd.z, 0.0, -cFwd.x);
        vec3 objectNormal = normalize(vec3(0.0, 1.0, 0.0) + 0.6 * cFwd);`)
        .replace("#include <begin_vertex>", `vec3 transformed = cRight * position.x + vec3(0.0, position.y, 0.0);
        vec2 cUv = mix(vec2(0.02, 0.004), vec2(0.98, 0.996), uv);      // kept off the cell's edges, so neighbours don't bleed in
        vCut = vec2((aC5.x + cUv.x) / (2.0 * uGrid.x), 1.0 - (aC5.y + 1.0 - cUv.y) / uGrid.y);
        #include <begin_vertex_life>`);
    } else {
      vs = vs.replace("#include <begin_vertex>", "#include <begin_vertex>\n#include <begin_vertex_life>");
    }
    vs = vs.replace("#include <begin_vertex_life>", `
        vC0 = aC0; vC1 = aC1; vC2 = aC2; vC3 = aC3; vC4 = aC4; vPart = aPart; vObj = position;
        {
          vec3 ip = vec3(instanceMatrix[3][0], instanceMatrix[3][1], instanceMatrix[3][2]);
          float seed = fract(sin(dot(ip.xz, vec2(12.9898, 78.233))) * 43758.5453);
          float h = transformed.y;
          float sway = 0.018 * sin(uTime * (0.6 + 0.5 * seed) + seed * 6.2832);
          float ex = smoothstep(75.0, 15.0, abs(ip.x - uLeader.x)) * smoothstep(55.0, 18.0, abs(ip.z - uLeader.y)) * step(0.2, seed);
          float bob = ex * 0.06 * max(0.0, sin(uTime * (6.0 + 3.0 * seed) + seed * 40.0));
          transformed.x += (sway + ex * 0.025 * sin(uTime * 2.7 + seed * 9.0)) * h;
          transformed.z -= ex * 0.05 * h;
          transformed.y += bob;
          if (aPart > 1.5 && aPart < 2.5 && seed > 0.62) transformed.y += ex * 0.2 * smoothstep(0.35, 0.9, 0.5 + 0.5 * sin(uTime * 2.1 + seed * 31.0));
        }
        vWy = (modelMatrix * instanceMatrix * vec4(transformed, 1.0)).y;`);
    sh.vertexShader = vs;
    let colour;
    if (cut) {
      colour = `
        vec4 cA = texture2D(uAtlas, vCut), cB = texture2D(uAtlas, vCut + vec2(0.5, 0.0));
        vec2 cPx = vCut * vec2(2.0 * uGrid.x * 128.0, uGrid.y * 256.0);
        float cLod = log2(max(max(length(dFdx(cPx)), length(dFdy(cPx))), 1e-3));
        float cA_ = cA.a * (1.0 + 0.35 * max(cLod, 0.0));          // keep thin figures from fading out far off
        if (cA_ < 0.5) discard;
        float cov = max(cA.a, 1e-3);
        float wT = cA.g / cov, wH = cA.b / cov, wS = cB.r / cov, wR = cB.g / cov, wW = cB.b / cov;
        float wM = clamp(1.0 - wT - wH - wS - wR - wW, 0.0, 1.0);
        vec3 pc = wM * vC0 + wS * vC1 + wH * vC2 + wT * vC3 + wR * vC4 + wW * vec3(0.92, 0.9, 0.84);
        diffuseColor.rgb *= pc * (cA.r / cov) * 1.08;`;
    } else {
      colour = `
        vec3 pc = vPart < 0.5 ? vC0 : vPart < 1.5 ? vC1 : vPart < 2.5 ? vC2 : vPart < 3.5 ? vC3 : vC4;
        ${S.paint ? `
        // a brushed finish: soft blotches of lighter and darker paint, in the figure's own space
        vec3 q = vObj * vec3(11.0, 7.0, 11.0);
        vec3 qi = floor(q), qf = fract(q); qf = qf * qf * (3.0 - 2.0 * qf);
        float hsh000 = fract(sin(dot(qi, vec3(12.99, 78.23, 37.71))) * 43758.55), hsh100 = fract(sin(dot(qi + vec3(1,0,0), vec3(12.99, 78.23, 37.71))) * 43758.55);
        float hsh010 = fract(sin(dot(qi + vec3(0,1,0), vec3(12.99, 78.23, 37.71))) * 43758.55), hsh110 = fract(sin(dot(qi + vec3(1,1,0), vec3(12.99, 78.23, 37.71))) * 43758.55);
        float hsh001 = fract(sin(dot(qi + vec3(0,0,1), vec3(12.99, 78.23, 37.71))) * 43758.55), hsh101 = fract(sin(dot(qi + vec3(1,0,1), vec3(12.99, 78.23, 37.71))) * 43758.55);
        float hsh011 = fract(sin(dot(qi + vec3(0,1,1), vec3(12.99, 78.23, 37.71))) * 43758.55), hsh111 = fract(sin(dot(qi + vec3(1,1,1), vec3(12.99, 78.23, 37.71))) * 43758.55);
        float nz = mix(mix(mix(hsh000, hsh100, qf.x), mix(hsh010, hsh110, qf.x), qf.y), mix(mix(hsh001, hsh101, qf.x), mix(hsh011, hsh111, qf.x), qf.y), qf.z);
        pc *= 0.86 + 0.28 * nz;
        pc = mix(pc, vec3(dot(pc, vec3(0.3, 0.55, 0.15))), -0.12);   // a touch richer
        ` : ""}
        diffuseColor.rgb *= pc;`;
    }
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", `#include <common>
        varying vec3 vC0; varying vec3 vC1; varying vec3 vC2; varying vec3 vC3; varying vec3 vC4; varying float vPart; varying float vWy;
        varying vec3 vObj; varying vec2 vCut; uniform sampler2D uAtlas; uniform vec2 uGrid;`)
      .replace("#include <clipping_planes_fragment>", `#include <clipping_planes_fragment>\nif (vWy < ${clip.toFixed(3)}) discard;`)
      .replace("#include <color_fragment>", "#include <color_fragment>\n" + colour);
  };
  mat.customProgramCacheKey = () => "crowd-life-" + (set ? set.id : "x") + "-" + clip.toFixed(3);
  return mat;
}
